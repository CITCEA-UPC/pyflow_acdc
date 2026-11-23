"""Docs: api\\modelling_dc.rst — DC line"""
import pyflow_acdc as pyf

# Create an AC node
pyf.initialize_pyflowacdc()
node1 = pyf.Node_DC('Slack', 1, 0,0,525,name='Bus1')
node2 = pyf.Node_DC('P', 1, 0,0,525,name='Bus2')
# In pu
line_1 = pyf.Line_DC(node1, node2, r=0.01, MW_rating=100, N_cables=1, name='Line1')
# Or by cable type in database
line_2 = pyf.Line_DC(node1, node2, S_base=100, Length_km=100, Cable_type='NREL_525kV_2500mm2')
