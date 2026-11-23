"""Docs: api\\results.rst — AC Specific Results"""
import pyflow_acdc as pyf

grid,res = pyf.cases['Stagg5MATACDC']()
pyf.acdc_sequential(grid)
res.all()
