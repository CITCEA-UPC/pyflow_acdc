# -*- coding: utf-8 -*-
"""
This grid is based on the CIGRE B4 test system. DCDC converters have been
simplified to a load and a gain in respective nodes.
"""

import time
from pathlib import Path

import pandas as pd
import pyflow_acdc as pyf


def run_test():
    """Test CIGRE B4 power flow."""
    start_time = time.perf_counter()

    grid, res = pyf.CigreB4_ACDC()

    t = pyf.ACDC_sequential(grid, Droop_PF=True,maxIter=500)
    #model, timing_info, model_res,solver_stats=pyf.Optimal_PF(grid)

    res.All()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print ('------')
    print(f'Time elapsed : {elapsed_time}')


def test_cigreb4_pf():
    """Pytest entrypoint for CIGRE B4 power flow test."""
    run_test()


if __name__ == "__main__":
    run_test()
