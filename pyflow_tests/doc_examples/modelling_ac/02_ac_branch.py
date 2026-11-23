"""Docs: api\\modelling_ac.rst — AC branch"""
import pyflow_acdc as pyf

# Create an AC node
pyf.initialize_pyflowacdc()
node1 = pyf.Node_AC('PQ', 1, 0,66, Power_Gained=0.5, name='Bus1')
node2 = pyf.Node_AC('Slack', 1, 0,66,name='Bus2')
# In pu
line_1 = pyf.Line_AC(node1, node2, r=0.01, x=0.1, g=0, b=0, MVA_rating=100, N_cables=1, name='Line1')
# Or by cable type in database
line_2 = pyf.Line_AC(node1, node2, S_base=100, Length_km=100, Cable_type='NREL_66kV_630mm2')
