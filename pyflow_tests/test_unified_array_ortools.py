"""Unified MIP path graph on alpha_ventus (OR-Tools backend)."""
import time

import pyflow_acdc as pyf
from pyflow_acdc.constants import MIPBackend
from pyflow_tests._test_solver_deps import (
    ortools_missing_for_run_test,
    require_ortools,
)

ARRAY_CASE = "alpha_ventus"
CT = 3
MIP_SOLVER = "ortools"
TEE = False
FS = False


def run_case(mip_solver=MIP_SOLVER):
    start_time = time.perf_counter()
    grid, res = pyf.cases[ARRAY_CASE](cab_types_allowed=CT)
    t_mw = grid.RenSources[0].PGi_ren_base * grid.S_base
    crossing = len(getattr(grid, "crossing_groups", []))
    edges = len(getattr(grid, "lines_AC_ct", []))
    turbines = len(getattr(grid, "RenSources", []))
    substations = sum(
        1 for n in getattr(grid, "nodes_AC", []) if getattr(n, "type", None) == "Slack"
    )

    flag, high_flow, model, feasible_solutions = pyf.MIP_path_graph(
        grid,
        max_flow=None,
        solver_name=mip_solver,
        crossings=True,
        tee=TEE,
        callback=FS,
        MIP_gap=None,
        backend=MIPBackend.ORTOOLS.value,
        enable_cable_types=True,
        t_MW=t_mw,
        cab_types_allowed=CT,
    )
    total_time = time.perf_counter() - start_time

    obj_value = None
    cable_length = None
    if flag and model is not None:
        obj_value = model.objective_value
        cable_length = sum(
            model.line_used_vals[line] * grid.lines_AC_ct[line].Length_km
            for line in range(len(grid.lines_AC_ct))
            if model.line_used_vals[line] > 0.5
        )

    return (
        total_time,
        edges,
        substations,
        turbines,
        crossing,
        flag,
        high_flow,
        obj_value,
        cable_length,
        len(feasible_solutions or []),
    )


def test_unified_array_ortools_alpha_ventus():
    require_ortools()
    (
        total_time,
        edges,
        substations,
        turbines,
        crossing,
        flag,
        high_flow,
        obj_value,
        cable_length,
        n_feasible_solutions,
    ) = run_case()
    print(
        f"{ARRAY_CASE} [unified ortools {MIP_SOLVER}]- success {flag}, "
        f"total time {total_time}, edges {edges}, subsations {substations}, "
        f"turbines {turbines}, high_flow {high_flow}, obj_value {obj_value}, "
        f"cable_length {cable_length}, crossing {crossing}, "
        f"n_feasible_solutions {n_feasible_solutions}"
    )


def run_test():
    if ortools_missing_for_run_test():
        return
    (
        total_time,
        edges,
        substations,
        turbines,
        crossing,
        flag,
        high_flow,
        obj_value,
        cable_length,
        n_feasible_solutions,
    ) = run_case()
    print(
        f"{ARRAY_CASE} [unified ortools {MIP_SOLVER}]- success {flag}, "
        f"total time {total_time}, edges {edges}, subsations {substations}, "
        f"turbines {turbines}, high_flow {high_flow}, obj_value {obj_value}, "
        f"cable_length {cable_length}, crossing {crossing}, "
        f"n_feasible_solutions {n_feasible_solutions}"
    )


if __name__ == "__main__":
    run_test()
