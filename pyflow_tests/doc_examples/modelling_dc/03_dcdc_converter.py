"""Docs: api\\modelling_dc.rst — DCDC converter"""
import pyflow_acdc as pyf
# Create an AC node
pyf.initialize_pyflowacdc()
grid = pyf.Grid(S_base=100)
node1 = pyf.Node_DC('Slack', 1, 0,0,525,name='Bus1')
node2 = pyf.Node_DC('P', 1, 0,0,525,name='Bus2')
conv = pyf.add_DCDC_converter(grid,node1 , node2 ,Pset=0.1, r=0.0001, MW_rating=99999,name='DCDC1')
