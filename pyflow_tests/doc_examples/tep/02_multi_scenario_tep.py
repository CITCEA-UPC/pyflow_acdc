"""Docs: usage_tep.rst — Multi-scenario TEP"""

import pyflow_acdc as pyf
from pyflow_tests.test_constants import north_sea_ms_clustering_options

build_only = True

grid, res = pyf.cases["NS_MTDC_2025"](years_data="23,24", expandable="step", online=False)


model, model_results, timing_info, solver_stats, ts_results = pyf.multi_scenario_TEP(

    grid,

    ObjRule={"PZ_cost_of_generation": 1},

    clustering_options=north_sea_ms_clustering_options(),

    solver="ipopt",

    tee=True,

    obj_scaling=1e6,

    build_only=build_only,

)

