"""Docs: api\\modelling_dc.rst — DC node"""
import pyflow_acdc as pyf

# Create an DC node
pyf.initialize_pyflowacdc()
node = pyf.Node_DC('P', 1, 0,0,525,name='Bus1')
