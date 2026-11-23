import time
import pyflow_acdc as pyf


S_base=100 #MVA


[grid,res]=pyf.cases['PEI_grid']()

pyf.plot_folium(grid)
"""
Sequential algorithm 

"""

time,tol,ps_iterations = pyf.acdc_sequential(grid,QLimit=False)




res.all()
print ('------')
print(f'Time elapsed : {time}')
