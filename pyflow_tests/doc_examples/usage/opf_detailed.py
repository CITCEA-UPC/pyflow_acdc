"""Usage guide: Detailed OPF example (``docs/usage.rst``)."""
import pandas as pd

import pyflow_acdc as pyf

build_only = not pyf.is_pyomo_solver_available("ipopt")

S_base = 100

nodes_AC_data = [
    {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '1.0'},
    {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.0, 'Reactive_load': 0.9861, 'Node_id': '2.0'},
    {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.0, 'Reactive_load': 0.9861, 'Node_id': '3.0'},
    {'type': 'Slack', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.0, 'Reactive_load': 1.3147, 'Node_id': '4.0'},
    {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5.0'},
]
nodes_AC = pd.DataFrame(nodes_AC_data)

lines_AC_data = [
    {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.00281, 'x': 0.0281, 'g': 0, 'b': 0.00712, 'MVA_rating': 400.0, 'kV_base': 230.0, 'Line_id': '1'},
    {'fromNode': '1.0', 'toNode': '4.0', 'r': 0.00304, 'x': 0.0304, 'g': 0, 'b': 0.00658, 'MVA_rating': 426.0, 'kV_base': 230.0, 'Line_id': '2'},
    {'fromNode': '1.0', 'toNode': '5.0', 'r': 0.00064, 'x': 0.0064, 'g': 0, 'b': 0.03126, 'MVA_rating': 426.0, 'kV_base': 230.0, 'Line_id': '3'},
    {'fromNode': '2.0', 'toNode': '3.0', 'r': 0.00108, 'x': 0.0108, 'g': 0, 'b': 0.01852, 'MVA_rating': 426.0, 'kV_base': 230.0, 'Line_id': '4'},
    {'fromNode': '3.0', 'toNode': '4.0', 'r': 0.00297, 'x': 0.0297, 'g': 0, 'b': 0.00674, 'MVA_rating': 426.0, 'kV_base': 230.0, 'Line_id': '5'},
    {'fromNode': '4.0', 'toNode': '5.0', 'r': 0.00297, 'x': 0.0297, 'g': 0, 'b': 0.00674, 'MVA_rating': 240.0, 'kV_base': 230.0, 'Line_id': '6'},
]
lines_AC = pd.DataFrame(lines_AC_data)

[grid, res] = pyf.create_grid_from_data(S_base, nodes_AC, lines_AC, data_in='pu')

pyf.add_gen(grid, '1.0', '1', lf=14, qf=0, MWmax=40.0, MWmin=0.0, MVArmax=30.0, MVArmin=-30.0, PsetMW=20.0, QsetMVA=0.0)
pyf.add_gen(grid, '1.0', '2', lf=15, qf=0, MWmax=170.0, MWmin=0.0, MVArmax=127.5, MVArmin=-127.5, PsetMW=85.0, QsetMVA=0.0)
pyf.add_gen(grid, '3.0', '3', lf=30, qf=0, MWmax=520.0, MWmin=0.0, MVArmax=390.0, MVArmin=-390.0, PsetMW=260.0, QsetMVA=0.0)
pyf.add_gen(grid, '4.0', '4', lf=40, qf=0, MWmax=200.0, MWmin=0.0, MVArmax=150.0, MVArmin=-150.0, PsetMW=100.0, QsetMVA=0.0)
pyf.add_gen(grid, '5.0', '5', lf=10, qf=0, MWmax=600.0, MWmin=0.0, MVArmax=450.0, MVArmin=-450.0, PsetMW=300.0, QsetMVA=0.0)

obj = {'Energy_cost': 1}

model, timing_info, model_res, solver_stats = pyf.optimal_pf(
    grid,
    ObjRule=obj,
    build_only=build_only,
)

res.all()
print('------')
