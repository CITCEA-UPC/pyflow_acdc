"""Docs: api\\ts.rst — Time series"""
import pandas as pd

import pyflow_acdc as pyf
from pyflow_tests.test_constants import NS_MTDC_MARKET_PRICES_URL, NS_MTDC_WIND_LOAD_URL

[grid,results] = pyf.cases['NS_MTDC']()
start = 5990
end = 6000
obj = {'Energy_cost': 1}
TS_MK = pd.read_csv(NS_MTDC_MARKET_PRICES_URL)
pyf.add_TimeSeries(grid,TS_MK)
TS_wl = pd.read_csv(NS_MTDC_WIND_LOAD_URL)
pyf.add_TimeSeries(grid,TS_wl)
build_only = not pyf.is_pyomo_solver_available("ipopt")
times=pyf.ts_acdc_opf(grid,start,end,ObjRule=obj,build_only=build_only)
res_dict = grid.time_series_results
