"""Docs: api\\plotting.rst — Full grid visualization as a network graph"""
import pyflow_acdc as pyf

grid,res = pyf.cases['case24_3zones_acdc']()
#show is set to False for testing suit, change it to True to see the plot
pyf.plot_graph(grid,show=False)

