# -*- coding: utf-8 -*-
"""
Sequential array test variant using OR-Tools.
"""
import time

import pyflow_acdc as pyf
import pyomo.environ as pyo
from pyflow_acdc.windfarm_loader import load_case_grid_and_geo

cases = {
    "westermost_rough",
}

ct = 3
MIP_solver = "ortools"
tl = 300
NL = False
tee = False
fs = False
obj = {"Energy_cost": 1}
FLH = 8760
WACC = 0.02


def run_case(case, mip_solver="ortools"):
    start_time = time.perf_counter()

    grid, res = load_case_grid_and_geo(case)
    grid.cab_types_allowed = ct

    model, summary_results, timing_info, solver_stats, best_i = pyf.sequential_CSS(
        grid,
        NPV=True,
        n_years=25,
        Hy=FLH,
        discount_rate=WACC,
        ObjRule=obj,
        MIP_solver=mip_solver,
        CSS_L_solver="ortools",
        CSS_NL_solver="bonmin",
        max_iter=None,
        time_limit=tl,
        NL=NL,
        tee=tee,
        fs=fs,
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
        summary_results,
        crossing,
        cable_length,
    )


def run_test():
    try:
        from ortools.sat.python import cp_model  # noqa: F401
    except Exception:
        print("OR-Tools is not installed or unavailable.")
        return

    for case in cases:
        (
            i,
            total_time,
            edges,
            substations,
            turbines,
            obj_value,
            path_time,
            css_time,
            summary_results,
            crossing,
            cable_length,
        ) = run_case(case, MIP_solver)
        print(
            f"{case}- iterations {i}, total time {total_time}, edges {edges}, "
            f"subsations {substations}, turbines {turbines}, obj_value {obj_value}, "
            f"path_time {path_time}, css_time {css_time}, crossing {crossing}, "
            f"cable_length {cable_length}"
        )


if __name__ == "__main__":
    run_test()
