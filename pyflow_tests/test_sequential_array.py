"""Sequential CSS on alpha_ventus (linear and PF loss post-processing)."""
import time
from pathlib import Path

import pyomo.environ as pyo

import pyflow_acdc as pyf
from pyflow_acdc.constants import CssMode
from pyflow_tests._test_solver_deps import (
    mip_solvers,
    pyomo_mip_css_solvers_missing_for_run_test,
    pyomo_missing_for_run_test,
    require_pyomo,
    require_pyomo_mip_css_solvers,
    tep_solver,
)

ARRAY_CASE = "alpha_ventus"
CT = 3
TL = 600
TEE = False
FS = True
FLH = 8760
WACC = 0.02
L_OPEX = True


def _feasible_solution_plots(save_path):
    plot_dir = Path(save_path) / "sequential_CSS"
    gap_plots = list(plot_dir.glob("feasible_solutions_*_gap.png"))
    obj_plots = list(plot_dir.glob("feasible_solutions_*_obj.png"))
    if len(gap_plots) != 1 or len(obj_plots) != 1:
        raise AssertionError(
            f"expected one gap and one obj feasible-solution plot in {plot_dir}, "
            f"got gap={gap_plots}, obj={obj_plots}"
        )
    return gap_plots[0], obj_plots[0]


def _format_result(nl_label, result):
    (
        i,
        total_time,
        edges,
        substations,
        turbines,
        obj_value,
        path_time,
        css_time,
        crossing,
        cable_length,
    ) = result
    return (
        f"{ARRAY_CASE} [{nl_label}] - iterations {i}, total time {total_time}, "
        f"edges {edges}, subsations {substations}, turbines {turbines}, "
        f"obj_value {obj_value}, path_time {path_time}, css_time {css_time}, "
        f"crossing {crossing}, cable_length {cable_length}"
    )


def run_case(mip_solver=None, css_l_solver=None, *, nl=False, save_path=None):
    if mip_solver is None or css_l_solver is None:
        mip_solver, css_l_solver = mip_solvers()

    start_time = time.perf_counter()
    grid, res = pyf.cases[ARRAY_CASE](cab_types_allowed=CT)

    model, summary_results, timing_info, solver_stats, best_i = pyf.sequential_CSS(
        grid,
        NPV=True,
        n_years=25,
        Hy=FLH,
        discount_rate=WACC,
        L_OPEX=L_OPEX,
        MIP_solver=mip_solver,
        CSS_L_solver=css_l_solver,
        CSS_NL_solver=tep_solver(),
        max_iter=None,
        time_limit=TL,
        NL=nl,
        tee=TEE,
        fs=FS,
        save_path=save_path,
    )
    i = len(summary_results["iteration"])
    obj_value = pyo.value(model[1].obj)
    cable_length = summary_results["cable_length"][best_i]
    path_time = timing_info["Paths"]
    css_time = timing_info["CSS"]
    crossing = len(getattr(grid, "crossing_groups", []))
    edges = len(getattr(grid, "lines_AC_ct", []))
    turbines = len(getattr(grid, "RenSources", []))
    substations = sum(
        1 for n in getattr(grid, "nodes_AC", []) if getattr(n, "type", None) == "Slack"
    )
    total_time = time.perf_counter() - start_time

    return (
        i,
        total_time,
        edges,
        substations,
        turbines,
        obj_value,
        path_time,
        css_time,
        crossing,
        cable_length,
    )


def test_sequential_array_alpha_ventus_linear(tmp_path):
    require_pyomo()
    require_pyomo_mip_css_solvers()
    mip_solver, css_solver = mip_solvers()
    result = run_case(mip_solver, css_solver, nl=False, save_path=tmp_path)
    print(_format_result("linear", result))
    _feasible_solution_plots(tmp_path)


def test_sequential_array_alpha_ventus_pf(tmp_path):
    require_pyomo()
    require_pyomo_mip_css_solvers()
    mip_solver, css_solver = mip_solvers()
    result = run_case(mip_solver, css_solver, nl=CssMode.PF, save_path=tmp_path)
    print(_format_result("PF", result))
    _feasible_solution_plots(tmp_path)


def run_test():
    if pyomo_missing_for_run_test():
        return
    if pyomo_mip_css_solvers_missing_for_run_test():
        return
    mip_solver, css_solver = mip_solvers()
    save_path = Path("sequential_CSS_test_output")
    save_path.mkdir(exist_ok=True)
    for nl, label in ((False, "linear"), (CssMode.PF, "PF")):
        result = run_case(mip_solver, css_solver, nl=nl, save_path=save_path)
        print(_format_result(label, result))
    _feasible_solution_plots(save_path)

if __name__ == "__main__":
    run_test()
