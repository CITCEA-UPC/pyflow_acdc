"""Docs: api\\modelling_ac.rst — AC node"""
import pyflow_acdc as pyf

# Create an AC node
pyf.initialize_pyflowacdc()
node = pyf.Node_AC('PQ', 1, 0,66, Power_Gained=0, Reactive_Gained=0, Power_load=100, Reactive_load=50, name='Bus1', Umin=0.9, Umax=1.1,Gs=0,Bs=0)
