"""Docs: api\\plotting.rst — Time series probability"""
import pandas as pd

import pyflow_acdc as pyf
from pyflow_tests.test_constants import NS_MTDC_MARKET_PRICES_URL, NS_MTDC_WIND_LOAD_URL

[grid,results] = pyf.cases['NS_MTDC']()
start = 5750
end = 6000
obj = {'Energy_cost': 1}
TS_MK = pd.read_csv(NS_MTDC_MARKET_PRICES_URL)
pyf.add_TimeSeries(grid,TS_MK)
TS_wl = pd.read_csv(NS_MTDC_WIND_LOAD_URL)
pyf.add_TimeSeries(grid,TS_wl)
#show is set to False for testing suit, change it to True to see the plot
pyf.time_series_prob(grid, 'OWPP_BE', show=False)
pyf.time_series_prob(grid, 'BE_price', show=False)
pyf.time_series_prob(grid, 'L_BE', show=False)
