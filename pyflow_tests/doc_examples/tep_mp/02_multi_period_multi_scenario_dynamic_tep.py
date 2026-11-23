"""Docs: usage_mp_tep.rst, api/tep_dynamic.rst — Multi-period Multi-scenario Dynamic TEP"""

import pyflow_acdc as pyf
from pyflow_tests.test_constants import north_sea_ms_clustering_options

build_only = True

grid, res = pyf.cases["NS_MTDC_2025"](years_data="23,24", expandable="mp", online=True)

mp_load_series = list(grid.Price_Zones[0].investment_decisions["Load"])

model, model_results, timing_info, solver_stats, ts_results = pyf.multi_period_MS_TEP(
    grid,
    inv_periods=mp_load_series,
    ObjRule={"PZ_cost_of_generation": 1},
    clustering_options=north_sea_ms_clustering_options(),
    solver="ipopt",
    tee=True,
    build_only=build_only,
)

