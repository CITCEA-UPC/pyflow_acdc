"""Docs: index.rst — Basic usage"""
import pyflow_acdc as pyf

#Use pre saved grids to familiarize yourself with the package
[grid,res]=pyf.cases['PEI_grid']()
pyf.acdc_sequential(grid,QLimit=False)
res.all()
