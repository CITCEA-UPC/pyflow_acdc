# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 10:55:43 2023

@author: BernardoCastro

This grid is based on the CIGRE B4 test system. DCDC converters have been simplified to a load and a gain in respective nodes.
"""

import time
import pandas as pd
import pyflow_acdc as pyf

from pathlib import Path

def CigreB4_OPF():


    start_time = time.perf_counter()

    grid,res  = pyf.cases['CigreB4_ACDC']()
    # pyf.ACDC_sequential(grid)
    model, timing_info, model_res,solver_stats=pyf.Optimal_PF(grid)

    res.All()
    print(model_res)
    print(timing_info)
    model.obj.display()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print ('------')
    print(f'Time elapsed : {elapsed_time}')

def run_test():
    """Test CIGRE B4 optimal power flow."""
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    
    CigreB4_OPF()

if __name__ == "__main__":
    run_test()