

import pyflow_acdc as pyf
import pandas as pd

"""
Converted to PyFlowACDC format from

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%                                                                  %%%%%
%%%%    IEEE PES Power Grid Library - Optimal Power Flow - v23.07     %%%%%
%%%%          (https://github.com/power-grid-lib/pglib-opf)           %%%%%
%%%%               Benchmark Group - Typical Operations               %%%%%
%%%%                         23 - July - 2023                         %%%%%
%%%%                                                                  %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   CASE5  Power flow data for modified 5 bus, 5 gen case based on PJM 5-bus system
%   Please see CASEFORMAT for details on the case file format.
%
%   Based on data from ...
%     F.Li and R.Bo, "Small Test Systems for Power System Economic Studies",
%     Proceedings of the 2010 IEEE Power & Energy Society General Meeting
%
%   Created by Rui Bo in 2006, modified in 2010, 2014.
%
%   Copyright (c) 2010 by The Institute of Electrical and Electronics Engineers (IEEE)
%   Licensed under the Creative Commons Attribution 4.0
%   International license, http://creativecommons.org/licenses/by/4.0/
%
%   Contact M.E. Brennan (me.brennan@ieee.org) for inquries on further reuse of
%   this dataset.
%
"""

def pglib_opf_case5_pjm():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '1.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.0, 'Reactive_load': 0.9861, 'Node_id': '2.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.0, 'Reactive_load': 0.9861, 'Node_id': '3.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Slack', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.0, 'Reactive_load': 1.3147, 'Node_id': '4.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.00281, 'x': 0.0281, 'g': 0, 'b': 0.00712, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '1'},
        {'fromNode': '1.0', 'toNode': '4.0', 'r': 0.00304, 'x': 0.0304, 'g': 0, 'b': 0.00658, 'MVA_rating': 426.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '2'},
        {'fromNode': '1.0', 'toNode': '5.0', 'r': 0.00064, 'x': 0.0064, 'g': 0, 'b': 0.03126, 'MVA_rating': 426.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '3'},
        {'fromNode': '2.0', 'toNode': '3.0', 'r': 0.00108, 'x': 0.0108, 'g': 0, 'b': 0.01852, 'MVA_rating': 426.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '4'},
        {'fromNode': '3.0', 'toNode': '4.0', 'r': 0.00297, 'x': 0.0297, 'g': 0, 'b': 0.00674, 'MVA_rating': 426.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '5'},
        {'fromNode': '4.0', 'toNode': '5.0', 'r': 0.00297, 'x': 0.0297, 'g': 0, 'b': 0.00674, 'MVA_rating': 240.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '6'}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'PJM 5-bus System'

    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    
    # Add Generators
    pyf.add_gen(grid, '1.0', '1', price_zone_link=False, lf=14, qf=0, MWmax=40.0, MWmin=0.0, MVArmax=30.0, MVArmin=-30.0, PsetMW=20.0, QsetMVA=0.0)
    pyf.add_gen(grid, '1.0', '2', price_zone_link=False, lf=15, qf=0, MWmax=170.0, MWmin=0.0, MVArmax=127.49999999999999, MVArmin=-127.49999999999999, PsetMW=85.0, QsetMVA=0.0)
    pyf.add_gen(grid, '3.0', '3', price_zone_link=False, lf=30, qf=0, MWmax=520.0, MWmin=0.0, MVArmax=390.0, MVArmin=-390.0, PsetMW=260.0, QsetMVA=0.0)
    pyf.add_gen(grid, '4.0', '4', price_zone_link=False, lf=40, qf=0, MWmax=200.0, MWmin=0.0, MVArmax=150.0, MVArmin=-150.0, PsetMW=100.0, QsetMVA=0.0)
    pyf.add_gen(grid, '5.0', '5', price_zone_link=False, lf=10, qf=0, MWmax=600.0, MWmin=0.0, MVArmax=450.0, MVArmin=-450.0, PsetMW=300.0, QsetMVA=0.0)
    
    
    # Add Renewable Source Zones

    
    # Add Renewable Sources

    
    # Return the grid
    return grid,res
