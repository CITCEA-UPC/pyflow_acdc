"""Docs: api\\plotting.rst — Neighbor Graph"""
import pyflow_acdc as pyf

grid,res = pyf.cases['case24_3zones_acdc']()

pyf.plot_neighbour_graph(grid, node='111',show=False)
