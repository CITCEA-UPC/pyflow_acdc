import os
import pandas as pd
import pyomo.environ as pyo
from .grid_analysis import analyse_grid, current_fuel_type_distribution
from .grid_modifications import add_inv_series, add_gen_mix_limits
from .ACDC_Static_TEP import transmission_expansion
from .ACDC_MultiPeriod_TEP import (
    _fill_investment_decisions,
    _validate_grid_for_MP_TEP,
    _update_grid_investment_period,
    _calculate_decomision_period,
    _deactivate_non_pre_existing_loads
)
from .Graph_and_plot import save_network_svg


def export_results_to_csv(run_results, export_dir, file_name="sequential_step_results.csv"):
    """Persist sequential STEP results dict as a pandas CSV."""
    out_path = os.path.join(export_dir, file_name)
    df = pd.DataFrame.from_dict(run_results, orient="index")
    df.index.name = "run_key"
    df = df.reset_index()
    df.to_csv(out_path, index=False)


def _iter_dynamic_elements_typed(grid):
    for gen in grid.Generators:
        yield str(gen.name), gen, "np_gen", "Generator"
    for ren in grid.RenSources:
        yield str(ren.name), ren, "np_rsgen", "Renewable Source"
    for line in grid.lines_AC_exp:
        yield str(line.name), line, "np_line", "AC Line"
    for line in grid.lines_DC:
        yield str(line.name), line, "np_line", "DC Line"
    for conv in grid.Converters_ACDC:
        yield str(conv.name), conv, "np_conv", "ACDC Conv"


def _max_attr_from_np_attr(np_attr):
    if np_attr == "np_gen":
        return "np_gen_max"
    if np_attr == "np_rsgen":
        return "np_rsgen_max"
    if np_attr == "np_line":
        return "np_line_max"
    if np_attr == "np_conv":
        return "np_conv_max"
    raise ValueError(f"Unsupported dynamic np attribute: {np_attr}")


def _iter_dynamic_elements(grid):
    for name, el, np_attr, _ in _iter_dynamic_elements_typed(grid):
        yield name, el, np_attr


def _round_dynamic_np_to_nearest_integer(grid):
    for _, el, np_attr in _iter_dynamic_elements(grid):
        value = float(getattr(el, np_attr))
        setattr(el, np_attr, float(int(round(value))))


def _snapshot_dynamic_counts(grid):
    snap = {}
    for name, el, np_attr in _iter_dynamic_elements(grid):
        snap[name] = float(getattr(el, np_attr))
    return snap


def _series_value_for_run(series, run_idx, label):
    if isinstance(series, (list, tuple)):
        if len(series) == 0:
            raise ValueError(f"{label} has no values.")
        if len(series) == 1:
            return float(series[0])
        if run_idx >= len(series):
            raise ValueError(f"{label} has length {len(series)}, cannot access run {run_idx}.")
        return float(series[run_idx])
    return float(series)


def _series_has_positive(series):
    if isinstance(series, (list, tuple)):
        return any(float(v) > 0 for v in series)
    return float(series) > 0


def _apply_decommission_for_run(grid, linked_decommission_schedule, run_idx):
    linked_now = dict(linked_decommission_schedule.pop(int(run_idx), {}))
    planned_now = {}
    for name, el, _ in _iter_dynamic_elements(grid):
        inv = el.investment_decisions
        if "planned_decomision" in inv:
            planned_now[name] = _series_value_for_run(
                inv["planned_decomision"], run_idx, f"{name}:planned_decomision"
            )

    by_name = {name: (el, np_attr) for name, el, np_attr in _iter_dynamic_elements(grid)}
    applied = {}

    names_to_apply = set(planned_now.keys()) | set(linked_now.keys())
    for name in names_to_apply:
        el, np_attr = by_name.get(name, (None, None))
        if el is None:
            raise ValueError(f"Decommission references unknown element '{name}'")

        total_decommission = float(linked_now.get(name, 0.0)) + float(planned_now.get(name, 0.0))
        if total_decommission < 0:
            raise ValueError(f"Negative total decommission for '{name}': {total_decommission}")

        current_stock = float(getattr(el, np_attr))
        if total_decommission > current_stock + 1e-9:
            raise ValueError(
                f"Decommission exceeds current stock for '{name}': "
                f"requested={total_decommission} > current={current_stock}"
            )
        setattr(el, np_attr, current_stock - total_decommission)
        #print(f"Base np for optimal solution {current_stock - total_decommission} of {name}")
        applied[name] = total_decommission

    return linked_now, planned_now, applied


def _apply_generation_type_limits_from_run(grid, run_idx):
    if run_idx < 0:
        raise ValueError(f"run_idx must be >= 0, got {run_idx}")

    for gen_type, series in dict(grid.generation_type_limits).items():
        if isinstance(series, list):
            if run_idx >= len(series):
                raise ValueError(
                    f"generation_type_limits['{gen_type}'] has length {len(series)}; "
                    f"cannot access run index {run_idx}"
                )
            value = float(series[run_idx])
        else:
            value = float(series)
        grid.current_generation_type_limits[gen_type] = value


def _apply_sequential_run_np_caps(grid, run_idx, absolute_np_max_by_name):
    for name, el, np_attr in _iter_dynamic_elements(grid):
        max_attr = _max_attr_from_np_attr(np_attr)
        if not hasattr(el, max_attr):
            continue

        current_stock = float(getattr(el, np_attr))
        absolute_max = float(absolute_np_max_by_name.get(name, getattr(el, max_attr)))

        max_inv_series = el.investment_decisions.get("max_inv") if isinstance(el.investment_decisions, dict) else None
        if max_inv_series is None:
            setattr(el, max_attr, absolute_max)
            continue

        install_max = _series_value_for_run(max_inv_series, run_idx, f"{name}:max_inv")
        run_max = min(current_stock + install_max, absolute_max)
        setattr(el, max_attr, run_max)


def _restore_absolute_np_caps(element_meta, absolute_np_max_by_name):
    for name, meta in element_meta.items():
        el = meta["element"]
        np_attr = meta["np_attr"]
        max_attr = _max_attr_from_np_attr(np_attr)
        if hasattr(el, max_attr) and name in absolute_np_max_by_name:
            setattr(el, max_attr, float(absolute_np_max_by_name[name]))


def _register_future_aged_decommission(grid, run_idx, n_years, decommission_applied_by_name, np_before_by_name, schedule):
    run_idx = int(run_idx)
    for name, el, np_attr in _iter_dynamic_elements(grid):
        np_before = float(np_before_by_name[name])
        np_after = float(getattr(el, np_attr))
        decomm_now = float(decommission_applied_by_name.get(name, 0.0))

        added_now = np_after - (np_before - decomm_now)
        if added_now <= 1e-9:
            continue

        decomision_period = int(el.decomision_period)
        future_idx = run_idx + decomision_period
        bucket = schedule.setdefault(future_idx, {})
        bucket[name] = bucket.get(name, 0.0) + float(added_now)


def sequential_STEP(
    grid,
    inv_data=None,
    mix_data=None,
    n_years=10,
    Hy=8760,
    discount_rate=0.02,
    ObjRule=None,
    solver="bonmin",
    time_limit=None,
    tee=False,
    callback=False,
    solver_options=None,
    obj_scaling=1.0,
    export_dir=None,
    svg_prefix="sequential_STEP",
    save_svgs=False,
    export_steps=False
):
    """
    Sequentially solve static transmission expansion one investment period at a time.

    The run sequence emulates MP behavior by applying period-k:
    - load multiplier
    - planned + aged decommission
    - generation-mix limit
    and then solving `transmission_expansion()` on the updated grid state.
    """
    
    grid.reset_run_flags()
    analyse_grid(grid)

    if inv_data is not None:
        add_inv_series(grid, inv_data)
    if mix_data is not None:
        add_gen_mix_limits(grid, mix_data)

    for gen in grid.Generators:
        planned_positive = _series_has_positive(gen.investment_decisions.get("planned_installation", 0.0))
        gen.np_gen_opf = bool(gen.np_gen_opf or planned_positive)
        gen.np_gen_mp = False
    for rs in grid.RenSources:
        planned_positive = _series_has_positive(rs.investment_decisions.get("planned_installation", 0.0))
        rs.np_rsgen_opf = bool(rs.np_rsgen_opf or planned_positive)
        rs.np_rsgen_mp = False

    n_runs = _fill_investment_decisions(grid)
    _validate_grid_for_MP_TEP(grid)
    if n_runs <= 0:
        raise ValueError("No investment periods found in grid investment decisions.")

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate = discount_rate
    grid.TEP_n_periods = n_runs

    grid.GPR = any(gen.np_gen_opf for gen in grid.Generators)
    grid.rs_GPR = any(rs.np_rsgen_opf for rs in grid.RenSources)

    for element in grid.Generators + grid.lines_AC_exp + grid.lines_DC + grid.Converters_ACDC + grid.RenSources:
        _calculate_decomision_period(element, n_years)

    if export_dir is not None:
        os.makedirs(export_dir, exist_ok=True)

    aged_decommission_schedule = {}
    run_results = {}
    pre_existing_by_name = _snapshot_dynamic_counts(grid)
    absolute_np_max_by_name = {}
    element_meta = {}
    report_rows = {}
    for name, el, np_attr, type_name in _iter_dynamic_elements_typed(grid):
        max_attr = _max_attr_from_np_attr(np_attr)
        absolute_np_max_by_name[name] = float(getattr(el, max_attr, getattr(el, np_attr)))
        element_meta[name] = {"element": el, "np_attr": np_attr, "type": type_name}
        report_rows[name] = {
            "Element": name,
            "Type": type_name,
            "Pre Existing": pre_existing_by_name.get(name, 0.0),
        }

    _deactivate_non_pre_existing_loads(grid)
    fuel_type_dist_by_period = {0: current_fuel_type_distribution(grid, output="df")}
    obj_rows = []
    aborted = False
    abort_reason = None

    for k in range(n_runs):
        np_before = _snapshot_dynamic_counts(grid)

        _update_grid_investment_period(grid, k)
        load_multiplier = None

        linked_now, planned_now, applied_decommission = _apply_decommission_for_run(
            grid, aged_decommission_schedule, k
        )
        _apply_sequential_run_np_caps(grid, k, absolute_np_max_by_name)
        _apply_generation_type_limits_from_run(grid, k)
        _round_dynamic_np_to_nearest_integer(grid)

        model, model_res, timing_info, solver_stats = transmission_expansion(
            grid,
            NPV=True,
            n_years=n_years,
            Hy=Hy,
            discount_rate=discount_rate,
            ObjRule=ObjRule,
            solver=solver,
            time_limit=time_limit,
            tee=tee,
            callback=callback,
            solver_options=solver_options,
            obj_scaling=obj_scaling,
        )
        if export_steps:
            from .Results_class import Results
            res = Results(grid)
            res.pyomo_model_results(model, solver_stats=solver_stats, model_results=model_res, print_table=False)
            res.All(export_location=export_dir, export_type="excel", file_name=f"sequential_STEP_{k+1}.xlsx",print_table=False)
        _round_dynamic_np_to_nearest_integer(grid)
        has_feasible_solution = bool(
            solver_stats
            and (
                solver_stats.get("solution_found", False)
                or len(solver_stats.get("feasible_solutions", []) or []) > 0
            )
        )
        if not has_feasible_solution:
            aborted = True
            termination = solver_stats.get("termination_condition", "unknown") if solver_stats else "unknown"
            abort_reason = f"run {k + 1} has no feasible solution (termination={termination})"
            if tee:
                print(f"Sequential STEP aborted at run {k + 1}: no solution found (termination={termination})")
            break

        _register_future_aged_decommission(
            grid=grid,
            run_idx=k,
            n_years=n_years,
            decommission_applied_by_name=applied_decommission,
            np_before_by_name=np_before,
            schedule=aged_decommission_schedule,
        )

        if save_svgs and export_dir is not None:
            save_network_svg(grid, name=os.path.join(export_dir, f"{svg_prefix}_{k+1}"))

        run_results[k] = {
            "run": k + 1,
            "csv_row_index": k + 2,
            "load_multiplier": load_multiplier,
            "model": model,
            "model_res": model_res,
            "timing_info": timing_info,
            "solver_stats": solver_stats,
            "decommission_applied": applied_decommission,
            "linked_decommission_requested": linked_now,
            "planned_decommission_requested": planned_now,
            "linked_decommission_requested_total": float(sum(linked_now.values())) if linked_now else 0.0,
            "linked_decommission_applied_total": float(sum(linked_now.values())) if linked_now else 0.0,
        }

        period = k + 1
        np_after = _snapshot_dynamic_counts(grid)
        for name, row in report_rows.items():
            decommissioned = float(applied_decommission.get(name, 0.0))
            installed = float(np_after[name]) - (float(np_before[name]) - decommissioned)
            if abs(installed) <= 1e-9:
                installed = 0.0
            active = float(np_after[name])
            base_cost = float(getattr(element_meta[name]["element"], "base_cost", 0.0) or 0.0)
            cost = installed * base_cost

            row[f"Decommissioned_{period}"] = decommissioned
            row[f"Installed_{period}"] = installed
            row[f"Active_{period}"] = active
            row[f"Cost_{period}"] = cost

        fuel_type_dist_by_period[period] = current_fuel_type_distribution(grid, output="df")

        opf_obj = sum(float(x.get("v", 0.0)) for x in grid.OPF_obj.values())
        npv_opf_obj = sum(float(x.get("NPV", 0.0)) for x in grid.OPF_obj.values())

        tep_obj = float(pyo.value(model.obj) * getattr(model, "obj_scaling", 1.0))
        present_value_tep = 1 / (1 + discount_rate) ** (k * n_years)
        obj_rows.append(
            {
                "Investment_Period": period,
                "OPF_Objective": opf_obj,
                "NPV_OPF_Objective": npv_opf_obj,
                "TEP_Objective": tep_obj,
                "STEP_Objective": tep_obj,
                "NPV_STEP_Objective": tep_obj * present_value_tep,
                "STEP_Objective_Economic": tep_obj,
                "NPV_STEP_Objective_Economic": tep_obj * present_value_tep,
            }
        )

        if export_dir is not None:
            export_results_to_csv(run_results, export_dir)

    seq_results_df = pd.DataFrame(list(report_rows.values()))
    if not seq_results_df.empty:
        cost_cols = [f"Cost_{i+1}" for i in range(n_runs) if f"Cost_{i+1}" in seq_results_df.columns]
        seq_results_df["Total_Cost"] = seq_results_df[cost_cols].sum(axis=1) if cost_cols else 0.0

        total_row = {}
        for col in seq_results_df.columns:
            if col == "Element":
                total_row[col] = "Total cost"
            elif "Cost" in col:
                total_row[col] = seq_results_df[col].sum()
            else:
                total_row[col] = ""
        seq_results_df = pd.concat([seq_results_df, pd.DataFrame([total_row])], ignore_index=True)

    grid.sequential_STEP_run_results = run_results
    grid.Seq_STEP_run = True
    grid.Seq_STEP_results = seq_results_df
    grid.Seq_STEP_obj_res = pd.DataFrame(
        obj_rows,
        columns=[
            "Investment_Period",
            "OPF_Objective",
            "NPV_OPF_Objective",
            "TEP_Objective",
            "STEP_Objective",
            "NPV_STEP_Objective",
            "STEP_Objective_Economic",
            "NPV_STEP_Objective_Economic",
        ],
    )
    grid.Seq_STEP_fuel_type_distribution = fuel_type_dist_by_period

    _restore_absolute_np_caps(element_meta, absolute_np_max_by_name)
    return run_results