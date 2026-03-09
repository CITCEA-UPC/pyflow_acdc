# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:05:19 2024

@author: BernardoCastro
"""

import time
import pandas as pd
import pyflow_acdc as pyf

start_time = time.perf_counter()
S_base=100 #MVA

ext='Real'

AC_node_data   = pd.read_csv(f'Stagg5MATACDC/MATACDC_AC_node_data_{ext}.csv')
DC_node_data   = pd.read_csv(f'Stagg5MATACDC/MATACDC_DC_node_data_{ext}.csv')
AC_line_data   = pd.read_csv(f'Stagg5MATACDC/MATACDC_AC_line_data_{ext}.csv')
DC_line_data   = pd.read_csv(f'Stagg5MATACDC/MATACDC_DC_line_data_{ext}.csv')
Converter_data = pd.read_csv(f'Stagg5MATACDC/MATACDC_Converter_data_{ext}.csv')



[grid,res]=pyf.Create_grid_from_data(S_base, AC_node_data, AC_line_data,DC_node_data, DC_line_data, Converter_data,data_in = ext)

"""
# Sequential algorithm 

# """

pf_time,tol,ps_iterations = pyf.ACDC_sequential(grid,QLimit=False)




end_time = time.perf_counter()
elapsed_time = end_time - start_time
res.All()
print ('------')
print(f'Time elapsed : {elapsed_time}')
