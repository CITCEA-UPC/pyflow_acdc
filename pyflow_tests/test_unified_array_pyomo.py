"""Unified MIP path graph on alpha_ventus (Pyomo backend)."""
import time

import pyomo.environ as pyo

import pyflow_acdc as pyf
from pyflow_acdc.Array_OPT import _create_master_problem_pyomo
from pyflow_acdc.constants import MIPBackend
from pyflow_acdc.solver_utils import is_pyomo_solver_available
from pyflow_tests._test_solver_deps import (
    pyomo_missing_for_run_test,
    require_pyomo,
)

ARRAY_CASE = "alpha_ventus"
CT = 3
TEE = False
FS = True
MIP_SOLVER = "highs"


def run_case(mip_solver=MIP_SOLVER, build_only=False):
    start_time = time.perf_counter()
    grid, res = pyf.cases[ARRAY_CASE](cab_types_allowed=CT)
    t_mw = grid.RenSources[0].PGi_ren_base * grid.S_base
    crossing = len(getattr(grid, "crossing_groups", []))
    edges = len(getattr(grid, "lines_AC_ct", []))
    turbines = len(getattr(grid, "RenSources", []))
    substations = sum(
        1 for n in getattr(grid, "nodes_AC", []) if getattr(n, "type", None) == "Slack"
    )

    if build_only:
        _create_master_problem_pyomo(
            grid,
            crossings=True,
            max_flow=None,
            enable_cable_types=True,
            t_MW=t_mw,
            cab_types_allowed=CT,
        )
        total_time = time.perf_counter() - start_time
        return (
            "build_only",
            total_time,
            edges,
            substations,
            turbines,
            crossing,
            None,
            None,
            None,
            0,
        )

    if mip_solver is None:
        mip_solver = MIP_SOLVER

    flag, high_flow, model, feasible_solutions = pyf.MIP_path_graph(
        grid,
        max_flow=None,
        solver_name=mip_solver,
        crossings=True,
        tee=TEE,
        callback=FS,
        MIP_gap=None,
        backend=MIPBackend.PYOMO.value,
        enable_cable_types=True,
        t_MW=t_mw,
        cab_types_allowed=CT,
    )
    total_time = time.perf_counter() - start_time

    obj_value = None
    cable_length = None
    if flag and model is not None:
        obj_value = pyo.value(model.objective)
        cable_length = pyo.value(
            sum(
                model.line_used[line] * grid.lines_AC_ct[line].Length_km
                for line in model.lines
            )
        )

    return (
        "solve",
        total_time,
        edges,
        substations,
        turbines,
        crossing,
        high_flow,
        obj_value,
        cable_length,
        len(feasible_solutions or []),
    )


def _print_result(mip_solver, result):
    (
        mode,
        total_time,
        edges,
        substations,
        turbines,
        crossing,
        high_flow,
        obj_value,
        cable_length,
        n_feasible_solutions,
    ) = result
    if mode == "build_only":
        print(
            f"{ARRAY_CASE} [unified pyomo build_only]- mode {mode}, "
            f"total time {total_time}, edges {edges}, subsations {substations}, "
            f"turbines {turbines}, crossing {crossing}"
        )
        return
    print(
        f"{ARRAY_CASE} [unified pyomo {mip_solver}]- mode {mode}, "
        f"total time {total_time}, edges {edges}, subsations {substations}, "
        f"turbines {turbines}, high_flow {high_flow}, obj_value {obj_value}, "
        f"cable_length {cable_length}, crossing {crossing}, "
        f"n_feasible_solutions {n_feasible_solutions}"
    )


def test_unified_array_pyomo_alpha_ventus():
    require_pyomo()
    build_only = not is_pyomo_solver_available(MIP_SOLVER)
    result = run_case(build_only=build_only)
    _print_result(MIP_SOLVER, result)
    if build_only:
        assert result[0] == "build_only"
    else:
        assert result[0] == "solve"
        assert result[7] is not None
        assert result[9] >= 0


def run_test():
    if pyomo_missing_for_run_test():
        return
    build_only = not is_pyomo_solver_available(MIP_SOLVER)
    result = run_case(build_only=build_only)
    _print_result(MIP_SOLVER, result)


if __name__ == "__main__":
    run_test()
