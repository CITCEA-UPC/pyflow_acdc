"""Docs: api\\plotting.rst — Saving the Network Graph"""
import pyflow_acdc as pyf

grid,res = pyf.cases['NS_MTDC']()
pyf.save_network_svg(grid)
