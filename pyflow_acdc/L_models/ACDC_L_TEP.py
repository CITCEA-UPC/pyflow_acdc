"""Linear (MILP) static and multi-period transmission-expansion drivers."""

import time

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from ..ACDC_OPF import (
    calculate_objective,
    obj_w_rule,
    opf_obj_l,
    opf_obj_l_array_losses,
    translate_pyf_opf,
)
from ..constants import (
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_TIME_LIMIT,
    HOURS_PER_YEAR,
    present_value_factor,
)
from ..grid_analysis import analyse_grid, current_fuel_type_distribution
from ..NL_models.ACDC_Static_TEP import _TEP_install_constraints, _TEP_install_variables, tep_obj
from ..pyomo_model_solve import build_only_solver_stats, pyomo_model_solve
from .AC_OPF_L_model import export_acdc_l_model_to_pyflow_acdc, opf_create_l_model_acdc

__all__ = [
    'linear_transmission_expansion',
    'linear_multi_period_transmission_expansion',
]


def _modify_parameters_l(grid, model, Price_Zones):
    """Update mutable linear-OPF params for the current investment period.

    Linear models have ``P_known_AC`` / ``P_renSource`` / prices but no
    ``Q_known_AC``.
    """
    if Price_Zones:
        raise ValueError(
            "linear_multi_period_transmission_expansion does not support Price_Zones."
        )

    opf_data = translate_pyf_opf(grid, Price_Zones=False)
    AC_info = opf_data['AC_info']
    gen_info = opf_data['gen_info']
    gen_AC_info, _, gen_rs_info = gen_info
    lf, _, _, _, _ = gen_AC_info
    P_renSource, _, _ = gen_rs_info
    _, AC_nodes_info, _, _, _, _ = AC_info
    _, _, _, _, P_know, _, _ = AC_nodes_info

    for idx, val in lf.items():
        model.lf[idx].set_value(val)
    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)
    for idx, val in P_know.items():
        model.P_known_AC[idx].set_value(val)
    if hasattr(model, 'P_load_eff'):
        for gen in grid.Generators:
            model.P_load_eff[gen.genNumber].set_value(gen.p_load_eff)


def _calculate_l_mptep_objective_from_model(model, grid, weights_def):
    from ..NL_models.ACDC_MultiPeriod_TEP import _inv_model_obj

    inv_objs = {}
    inv_opf_objs = {}
    for i in model.inv_periods:
        period = model.inv_model[i]
        opf_expr = opf_obj_l(period, grid, weights_def) + opf_obj_l_array_losses(
            period, grid, weights_def
        )
        inv_opf_objs[i] = [pyo.value(opf_expr)]
        inv_objs[i] = pyo.value(_inv_model_obj(model, grid, i))
    return inv_objs, inv_opf_objs


def _post_process_l_mptep_with_nl_opf(
    grid,
    ObjRule,
    n_years,
    discount_rate,
    Hy,
    alpha=None,
    nl_solver='ipopt',
    tee=False,
    obj_scaling=1.0,
    save_period_svgs=False,
    period_svg_prefix='grid_L_MP_TEP',
):
    """Re-solve NL OPF per investment period; store results in ``MP_TEP_nl_obj_res``.

    Linear ``grid.MP_TEP_obj_res`` is left unchanged. The NL table uses the same
    column schema so the two Excel sheets are directly comparable.
    Failed NL OPFs do not export onto ``grid`` (``export_if_feasible=True``).
    ``optimal_pf`` clears run flags, so ``MP_TEP_run`` is restored at the end.
    """
    from ..ACDC_OPF import calculate_objective_from_model, optimal_pf
    from ..Graph_and_plot import create_geometries_from_layout, save_network_svg
    from ..NL_models.ACDC_MultiPeriod_TEP import _set_grid_to_multiperiod_state

    df_lin = grid.MP_TEP_obj_res
    if df_lin is None or df_lin.empty:
        raise ValueError("MP_TEP_obj_res is missing; cannot post-process NL OPF.")

    present_value_opf = present_value_factor(Hy, discount_rate, n_years)
    n_periods = int(grid.TEP_n_periods)
    _, PZ = obj_w_rule(grid, ObjRule)

    # NL post-process always uses obj_scaling=1 (MP scaling is for the MILP only).
    nl_obj_scaling = 1.0

    obj_rows = []
    for i in range(n_periods):
        _set_grid_to_multiperiod_state(grid, i, PZ)
        if save_period_svgs:
            create_geometries_from_layout(grid)
            save_network_svg(
                grid,
                name=f"{period_svg_prefix}_P{i}",
                journal=True,
                legend=True,
            )
        tep_obj = float(df_lin.loc[df_lin["Investment_Period"] == i + 1, "TEP_Objective"].iloc[0])
        present_value_tep = 1 / (1 + discount_rate) ** (i * n_years)
        nl_model, _, _, nl_stats = optimal_pf(
            grid,
            ObjRule=ObjRule,
            solver=nl_solver,
            tee=tee,
            obj_scaling=nl_obj_scaling,
            export_if_feasible=True,
        )
        solution_found = bool(nl_stats and nl_stats.get("solution_found", False))
        termination = nl_stats.get("termination_condition", "unknown") if nl_stats else "unknown"

        if solution_found:
            nl_opf = float(calculate_objective_from_model(nl_model, grid, grid.OPF_obj))
            npv_nl_opf = nl_opf * present_value_opf
            economic_nl_step = tep_obj + npv_nl_opf
            if alpha is None:
                nl_step = economic_nl_step
            else:
                nl_step = alpha * tep_obj + (1 - alpha) * npv_nl_opf
            npv_nl_step = nl_step * present_value_tep
            npv_nl_step_economic = economic_nl_step * present_value_tep
        else:
            if tee:
                print(
                    f"NL OPF post-process skipped for investment period {i} "
                    f"(termination={termination})."
                )
            nl_opf = np.nan
            npv_nl_opf = np.nan
            nl_step = np.nan
            npv_nl_step = np.nan
            economic_nl_step = np.nan
            npv_nl_step_economic = np.nan

        obj_rows.append({
            'Investment_Period': i + 1,
            'OPF_Objective': nl_opf,
            'NPV_OPF_Objective': npv_nl_opf,
            'TEP_Objective': tep_obj,
            'STEP_Objective': nl_step,
            'NPV_STEP_Objective': npv_nl_step,
            'STEP_Objective_Economic': economic_nl_step,
            'NPV_STEP_Objective_Economic': npv_nl_step_economic,
        })

    grid.MP_TEP_nl_obj_res = pd.DataFrame(
        obj_rows,
        columns=[
            'Investment_Period',
            'OPF_Objective',
            'NPV_OPF_Objective',
            'TEP_Objective',
            'STEP_Objective',
            'NPV_STEP_Objective',
            'STEP_Objective_Economic',
            'NPV_STEP_Objective_Economic',
        ],
    )
    grid.MP_TEP_run = True
    return grid.MP_TEP_nl_obj_res


def linear_transmission_expansion(
    grid,
    NPV=True,
    n_years=25,
    Hy=HOURS_PER_YEAR,
    discount_rate=DEFAULT_DISCOUNT_RATE,
    ObjRule=None,
    solver='gurobi',
    time_limit=DEFAULT_TIME_LIMIT,
    tee=False,
    export=True,
    fs=False,
    obj_scaling=1.0,
    build_only=False,
):
    """Build and solve the linear (MILP) static transmission-expansion problem.

    Linear counterpart of :func:`~pyflow_acdc.transmission_expansion`: combines TEP
    investment cost with the linear OPF operating cost (OPEX discounted to
    present value when ``NPV`` is set), solves the MILP, and exports the
    expansion decisions and operating point back onto ``grid``.

    Parameters
    ----------
    grid : Grid
        Network with candidate expandable elements (mutated in place).
    NPV : bool, optional
        Discount OPEX to present value over the planning horizon.
    n_years : int, optional
        Planning horizon in years.
    Hy : float, optional
        Operating hours per year used to annualise OPEX.
    discount_rate : float, optional
        Annual discount rate for the present-value factor.
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    solver : str, optional
        Pyomo MILP solver name.
    time_limit : float, optional
        Solver time limit in seconds.
    tee : bool, optional
        Stream raw solver output.
    export : bool, optional
        Write the solution back onto ``grid``.
    fs : bool, optional
        Enable the solver-progress callback.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    build_only : bool, optional
        Build the Pyomo model, skip the solver, and export initializer values
        onto ``grid`` so :class:`~pyflow_acdc.Results_class.Results` can run
        without a MILP solver.

    Returns
    -------
    tuple
        ``(model, model_results, timing_info, solver_stats)``; all ``None`` if
        the solve fails.
    """
    grid.reset_run_flags()
    analyse_grid(grid)

    weights_def, _ = obj_w_rule(grid, ObjRule)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate = discount_rate

    t1 = time.perf_counter()
    model = pyo.ConcreteModel()
    model.name = "TEP MTDC linear AC OPF"

    opf_create_l_model_acdc(model, grid, TEP=True)
    _TEP_install_variables(model, grid)
    _TEP_install_constraints(model, grid)

    obj_TEP = tep_obj(model, grid, NPV)
    obj_OPF = opf_obj_l(model, grid, weights_def) + opf_obj_l_array_losses(
        model, grid, weights_def
    )

    present_value = present_value_factor(Hy, discount_rate, n_years)
    if NPV:
        obj_OPF *= present_value

    total_cost = obj_TEP + obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    t2 = time.perf_counter()
    t_modelcreate = t2 - t1

    t3 = time.perf_counter()
    if build_only:
        model_results, solver_stats = build_only_solver_stats(solver, model)
    else:
        model_results, solver_stats = pyomo_model_solve(
            model, grid, solver, tee, time_limit, callback=fs
        )
        if model_results is None:
            return None, None, None, None

    t1 = time.perf_counter()
    if export:
        export_acdc_l_model_to_pyflow_acdc(
            model, grid, solver_results=model_results, tee=tee
        )
        for obj in weights_def:
            weights_def[obj]['v'] = calculate_objective(grid, obj)
            weights_def[obj]['NPV'] = weights_def[obj]['v'] * present_value
    t2 = time.perf_counter()

    t_modelexport = t2 - t1

    grid.TEP_run = True
    grid.OPF_obj = weights_def

    timing_info = {
        "create": t_modelcreate,
        "solve": solver_stats['time'] if solver_stats['time'] is not None else t1 - t3,
        "export": t_modelexport,
    }
    return model, model_results, timing_info, solver_stats


def linear_multi_period_transmission_expansion(
    grid,
    inv_periods=None,
    n_years=10,
    Hy=HOURS_PER_YEAR,
    discount_rate=DEFAULT_DISCOUNT_RATE,
    ObjRule=None,
    solver='gurobi',
    time_limit=None,
    tee=False,
    callback=False,
    solver_options=None,
    obj_scaling=1.0,
    alpha=None,
    capex_budget=None,
    build_only=False,
    n_init_install=None,
    initiate_max=None,
    post_process_nl_opf=False,
    nl_solver='ipopt',
    save_period_svgs=False,
    period_svg_prefix='grid_L_MP_TEP',
):
    """Build and solve the linear (MILP) multi-period AC transmission-expansion problem.

    Linear counterpart of :func:`~pyflow_acdc.multi_period_transmission_expansion`.
    AC-only: raises if ``grid.DCmode`` is true. Default solver is Gurobi.

    Parameters
    ----------
    grid : Grid
        AC network with candidate expandable elements (mutated in place).
    inv_periods : sequence or None, optional
        Investment-period load factors; ``None`` uses the grid's configured series.
    n_years : int, optional
        Length of each investment period in years.
    Hy : float, optional
        Operating hours per year used to annualise OPEX.
    discount_rate : float, optional
        Annual discount rate for present-value discounting.
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    solver : str, optional
        Pyomo MILP solver name (default ``'gurobi'``).
    time_limit : float or None, optional
        Solver time limit in seconds.
    tee : bool, optional
        Stream raw solver output.
    callback : bool, optional
        Enable the solver-progress callback.
    solver_options : dict or None, optional
        Extra solver options.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    alpha : float or None, optional
        Weighting between CAPEX (``alpha``) and OPEX (``1-alpha``).
    capex_budget : float or None, optional
        Optional cap on total investment cost.
    build_only : bool, optional
        Build and return the model without solving.
    n_init_install : {None, "max", "mean"}, optional
        Pre-installation level used to initialise expandable elements.
    initiate_max : bool or None, optional
        Deprecated alias for ``n_init_install`` (``True`` maps to ``"max"``).
    post_process_nl_opf : bool, optional
        After a successful MILP solve, re-solve a single-state NL OPF for each
        investment period and store results in ``grid.MP_TEP_nl_obj_res``
        (same schema as linear ``MP_TEP_obj_res`` for side-by-side comparison).
        NL post-process always uses ``obj_scaling=1.0`` (independent of the MILP
        ``obj_scaling``).
    nl_solver : str, optional
        NLP solver used when ``post_process_nl_opf`` is True (default ``'ipopt'``).
    save_period_svgs : bool, optional
        Save one SVG per investment period from the assigned investment state
        (``np_*``, loads). Independent of NL OPF success when post-processing.
    period_svg_prefix : str, optional
        Path/name prefix for period SVGs when ``save_period_svgs`` is True.

    Returns
    -------
    tuple
        ``(model, model_results, timing_info, solver_stats)``.
    """
    from ..NL_models.ACDC_MultiPeriod_TEP import (
        _calculate_decomision_period,
        _deactivate_non_pre_existing_loads,
        _fill_investment_decisions,
        _initialize_MPTEP_sets_model,
        _inv_decision,
        _MP_GEN_balance_constraints,
        _MP_TEP_capex_budget_constraint,
        _MP_TEP_constraints,
        _MP_TEP_obj,
        _MP_TEP_variables,
        _save_inv_models,
        _update_grid_investment_period,
        _validate_grid_for_MP_TEP,
        export_mp_tep_results_to_pyflow_acdc,
        save_MP_TEP_period_svgs,
    )

    if initiate_max is not None:
        if n_init_install is not None:
            raise ValueError("Provide only one of 'n_init_install' or deprecated 'initiate_max'.")
        if not isinstance(initiate_max, bool):
            raise TypeError("Deprecated 'initiate_max' must be boolean when provided.")
        n_init_install = "max" if initiate_max else None
    if n_init_install not in (None, "max", "mean"):
        raise ValueError("n_init_install must be one of: None, 'max', 'mean'.")

    grid.reset_run_flags()
    analyse_grid(grid)

    if grid.DCmode:
        raise ValueError(
            "linear_multi_period_transmission_expansion supports AC-only grids; "
            "DCmode is set."
        )

    weights_def, PZ = obj_w_rule(grid, ObjRule)
    if PZ:
        raise ValueError(
            "linear_multi_period_transmission_expansion does not support Price_Zones."
        )

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate = discount_rate

    if inv_periods:
        load_factors = np.array(inv_periods, dtype=float)
        for node in grid.nodes_AC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()
        for node in grid.nodes_DC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()

    n_periods = _fill_investment_decisions(grid)
    _validate_grid_for_MP_TEP(grid)

    grid.GPR = bool(grid.GPR) or any(
        gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
        for gen in grid.Generators
    )
    grid.rs_GPR = bool(grid.rs_GPR) or any(
        rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))
        for rs in grid.RenSources
    )

    for gen in grid.Generators:
        gen.np_gen_mp = gen.np_gen_opf or any(
            x != 0 for x in _inv_decision(gen, 'planned_installation')
        )
    for rs in grid.RenSources:
        rs.np_rsgen_mp = rs.np_rsgen_opf or any(
            x != 0 for x in _inv_decision(rs, 'planned_installation')
        )

    t1 = time.time()
    _deactivate_non_pre_existing_loads(grid)
    pre_opt_fuel_type_distribution = current_fuel_type_distribution(grid, output='df')

    model = pyo.ConcreteModel()
    model.name = "Dynamic TEP linear AC OPF"

    model.inv_periods = pyo.Set(initialize=list(range(n_periods)))
    grid.TEP_n_periods = n_periods
    model.inv_model = pyo.Block(model.inv_periods)

    base_model = pyo.ConcreteModel()
    opf_create_l_model_acdc(base_model, grid, TEP=True)

    for element in grid.Generators + grid.lines_AC_exp + grid.lines_DC + grid.Converters_ACDC + grid.RenSources:
        _calculate_decomision_period(element, n_years)

    present_value_opf = present_value_factor(Hy, discount_rate, n_years)
    for i in model.inv_periods:
        base_model_copy = base_model.clone()
        model.inv_model[i].transfer_attributes_from(base_model_copy)

        _update_grid_investment_period(grid, i)
        _modify_parameters_l(grid, model.inv_model[i], PZ)

        obj_OPF = opf_obj_l(model.inv_model[i], grid, weights_def) + opf_obj_l_array_losses(
            model.inv_model[i], grid, weights_def
        )
        obj_OPF *= present_value_opf
        model.inv_model[i].obj = pyo.Objective(rule=obj_OPF, sense=pyo.minimize)

    _initialize_MPTEP_sets_model(model, grid)
    _MP_TEP_variables(model, grid, n_init_install=n_init_install)
    _MP_TEP_constraints(model, grid)
    _MP_GEN_balance_constraints(model, grid)
    _MP_TEP_capex_budget_constraint(model, grid, capex_budget=capex_budget)

    net_cost = _MP_TEP_obj(model, grid, n_years, discount_rate, alpha=alpha)
    if obj_scaling != 1.0:
        net_cost = net_cost / obj_scaling
    model.obj = pyo.Objective(rule=net_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    t2 = time.time()

    if build_only:
        model_results, solver_stats = build_only_solver_stats(solver, model)
        t3 = t2
    else:
        model_results, solver_stats = pyomo_model_solve(
            model,
            grid,
            solver,
            time_limit=time_limit,
            tee=tee,
            callback=callback,
            solver_options=solver_options,
        )
        t3 = time.time()

        if not (solver_stats and solver_stats.get("solution_found", False)):
            termination = solver_stats.get("termination_condition", "unknown") if solver_stats else "unknown"
            solver_message = solver_stats.get("solver_message", "") if solver_stats else ""
            if tee:
                print(f"Linear MP-TEP failed: no feasible solution found (termination: {termination}).")
                if solver_message:
                    print(f"Solver message: {solver_message}")
            timing_info = {
                "create": t2 - t1,
                "solve": solver_stats["time"] if solver_stats else None,
                "export": 0.0,
            }
            return model, model_results, timing_info, solver_stats

    export_mp_tep_results_to_pyflow_acdc(
        model,
        grid,
        Price_Zones=PZ,
        MINLP=True,
        pre_opt_fuel_type_distribution=pre_opt_fuel_type_distribution,
        opf_export='l',
    )
    _save_inv_models(model, grid)
    t4 = time.time()

    inv_objs, inv_opf_objs = _calculate_l_mptep_objective_from_model(
        model, grid, weights_def
    )

    obj_rows = []
    for i in model.inv_periods:
        present_value_tep = 1 / (1 + discount_rate) ** (i * n_years)
        opf_obj_from_list = inv_opf_objs[i][0]
        npv_opf_obj = opf_obj_from_list * present_value_opf
        inv_obj_from_list = inv_objs[i]
        economic_step_obj = inv_obj_from_list + npv_opf_obj
        if alpha is None:
            step_obj = economic_step_obj
        else:
            step_obj = alpha * inv_obj_from_list + (1 - alpha) * npv_opf_obj
        npv_step_obj = step_obj * present_value_tep
        npv_economic_step_obj = economic_step_obj * present_value_tep
        obj_rows.append({
            'Investment_Period': i + 1,
            'OPF_Objective': opf_obj_from_list,
            'NPV_OPF_Objective': npv_opf_obj,
            'TEP_Objective': inv_obj_from_list,
            'STEP_Objective': step_obj,
            'NPV_STEP_Objective': npv_step_obj,
            'STEP_Objective_Economic': economic_step_obj,
            'NPV_STEP_Objective_Economic': npv_economic_step_obj,
        })
    grid.MP_TEP_obj_res = pd.DataFrame(
        obj_rows,
        columns=[
            'Investment_Period',
            'OPF_Objective',
            'NPV_OPF_Objective',
            'TEP_Objective',
            'STEP_Objective',
            'NPV_STEP_Objective',
            'STEP_Objective_Economic',
            'NPV_STEP_Objective_Economic',
        ],
    )

    solution_found = bool(solver_stats and solver_stats.get("solution_found", False))
    if post_process_nl_opf and not build_only and solution_found:
        t_pp0 = time.time()
        _post_process_l_mptep_with_nl_opf(
            grid,
            ObjRule=ObjRule,
            n_years=n_years,
            discount_rate=discount_rate,
            Hy=Hy,
            alpha=alpha,
            nl_solver=nl_solver,
            tee=tee,
            obj_scaling=obj_scaling,
            save_period_svgs=save_period_svgs,
            period_svg_prefix=period_svg_prefix,
        )
        t4 = time.time()
        timing_info = {
            "create": t2 - t1,
            "solve": solver_stats["time"],
            "export": t4 - t3,
            "nl_post_process": t4 - t_pp0,
        }
    else:
        if save_period_svgs and not build_only and solution_found:
            save_MP_TEP_period_svgs(
                grid,
                name_prefix=period_svg_prefix,
                journal=True,
                legend=True,
                Price_Zones=PZ,
            )
        timing_info = {
            "create": t2 - t1,
            "solve": solver_stats["time"],
            "export": t4 - t3,
        }

    return model, model_results, timing_info, solver_stats
