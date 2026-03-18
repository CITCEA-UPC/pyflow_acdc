

import pyflow_acdc as pyf
import pandas as pd
"""
Converted to PyFlowACDC format from
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%                                                                  %%%%%
%%%%    IEEE PES Power Grid Library - Optimal Power Flow - v21.07     %%%%%
%%%%          (https://github.com/power-grid-lib/pglib-opf)           %%%%%
%%%%               Benchmark Group - Typical Operations               %%%%%
%%%%                         29 - July - 2021                         %%%%%
%%%%                                                                  %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   Power flow data for the IEEE RELIABILITY TEST SYSTEM 1979.
%
%   IEEE Reliability Test System Task Force of the Applications of
%   Probability Methods Subcommittee, "IEEE reliability test system,"
%   IEEE Transactions on Power Apparatus and Systems, Vol. 98, No. 6,
%   Nov./Dec. 1979, pp. 2047-2054.
%
%   Cost data is from Web site run by Georgia Tech Power Systems Control
%   and Automation Laboratory:
%       http://pscal.ece.gatech.edu/testsys/index.html
%
%   Matpower case file data provided by Bruce Wollenberg.
%
%   Copyright (c) 1979 The Institute of Electrical and Electronics Engineers (IEEE)
%   Licensed under the Creative Commons Attribution 4.0
%   International license, http://creativecommons.org/licenses/by/4.0/
%
%   Contact M.E. Brennan (me.brennan@ieee.org) for inquries on further reuse of
%   this dataset.
%

generator cost c(0) modified to 0

"""

def pglib_opf_case24_ieee_rts():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
    {'Node_id': '1', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.08, 'Reactive_load': 0.22, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 26.194, 'y_coord': 0.869},
    {'Node_id': '2', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.97, 'Reactive_load': 0.2, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 52.652, 'y_coord': 0.869},
    {'Node_id': '3', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.8, 'Reactive_load': 0.37, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 18.256, 'y_coord': 28.65},
    {'Node_id': '4', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.74, 'Reactive_load': 0.15, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 36.777, 'y_coord': 10.999},
    {'Node_id': '5', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.71, 'Reactive_load': 0.14, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 50.271, 'y_coord': 10.999},
    {'Node_id': '6', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.36, 'Reactive_load': 0.28, 'Umin': 0.95, 'Umax': 1.05,  'Bs': -1.0, 'x_coord': 76.906, 'y_coord': 29.092},
    {'Node_id': '7', 'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.25, 'Reactive_load': 0.25, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 69.321, 'y_coord': 0.869},
    {'Node_id': '8', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.71, 'Reactive_load': 0.35, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 76.906, 'y_coord': 10.999},
    {'Node_id': '9', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.75, 'Reactive_load': 0.36, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 40.847, 'y_coord': 28.65},
    {'Node_id': '10', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.95, 'Reactive_load': 0.4, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 28.65},
    {'Node_id': '11', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 40.847, 'y_coord': 39.035},
    {'Node_id': '12', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 39.035},
    {'Node_id': '13', 'type': 'Slack', 'Voltage_0': 1.02, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 2.65, 'Reactive_load': 0.54, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 69.857, 'y_coord': 58.555},
    {'Node_id': '14', 'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.94, 'Reactive_load': 0.39, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 59.519},
    {'Node_id': '15', 'type': 'PV', 'Voltage_0': 1.014, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.17, 'Reactive_load': 0.64, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 59.076},
    {'Node_id': '16', 'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.0, 'Reactive_load': 0.2, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 68.791},
    {'Node_id': '17', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 3.81, 'y_coord': 87.209},
    {'Node_id': '18', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.33, 'Reactive_load': 0.68, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 91.75},
    {'Node_id': '19', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.81, 'Reactive_load': 0.37, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 68.791},
    {'Node_id': '20', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.28, 'Reactive_load': 0.26, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 51.126, 'y_coord': 68.791},
    {'Node_id': '21', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 91.75},
    {'Node_id': '22', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 91.75},
    {'Node_id': '23', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 62.484, 'y_coord': 78.201},
    {'Node_id': '24', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.95, 'Umax': 1.05,  'Bs': 0.0, 'x_coord': 18.256, 'y_coord': 39.035}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1', 'toNode': '2', 'r': 0.0026, 'x': 0.0139, 'g': 0, 'b': 0.4611, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '1', 'geometry': None},
        {'fromNode': '1', 'toNode': '3', 'r': 0.0546, 'x': 0.2112, 'g': 0, 'b': 0.0572, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '2', 'geometry': None},
        {'fromNode': '1', 'toNode': '5', 'r': 0.0218, 'x': 0.0845, 'g': 0, 'b': 0.0229, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '3', 'geometry': None},
        {'fromNode': '2', 'toNode': '4', 'r': 0.0328, 'x': 0.1267, 'g': 0, 'b': 0.0343, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '4', 'geometry': None},
        {'fromNode': '2', 'toNode': '6', 'r': 0.0497, 'x': 0.192, 'g': 0, 'b': 0.052, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '5', 'geometry': None},
        {'fromNode': '3', 'toNode': '9', 'r': 0.0308, 'x': 0.119, 'g': 0, 'b': 0.0322, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '6', 'geometry': None},
        {'fromNode': '3', 'toNode': '24', 'r': 0.0023, 'x': 0.0839, 'g': 0, 'b': 0.0, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1.03, 'shift': 0.0, 'Line_id': '7', 'geometry': None},
        {'fromNode': '4', 'toNode': '9', 'r': 0.0268, 'x': 0.1037, 'g': 0, 'b': 0.0281, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '8', 'geometry': None},
        {'fromNode': '5', 'toNode': '10', 'r': 0.0228, 'x': 0.0883, 'g': 0, 'b': 0.0239, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '9', 'geometry': None},
        {'fromNode': '6', 'toNode': '10', 'r': 0.0139, 'x': 0.0605, 'g': 0, 'b': 2.459, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '10', 'geometry': None},
        {'fromNode': '7', 'toNode': '8', 'r': 0.0159, 'x': 0.0614, 'g': 0, 'b': 0.0166, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '11', 'geometry': None},
        {'fromNode': '8', 'toNode': '9', 'r': 0.0427, 'x': 0.1651, 'g': 0, 'b': 0.0447, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '12', 'geometry': None},
        {'fromNode': '8', 'toNode': '10', 'r': 0.0427, 'x': 0.1651, 'g': 0, 'b': 0.0447, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '13', 'geometry': None},
        {'fromNode': '9', 'toNode': '11', 'r': 0.0023, 'x': 0.0839, 'g': 0, 'b': 0.0, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1.03, 'shift': 0.0, 'Line_id': '14', 'geometry': None},
        {'fromNode': '9', 'toNode': '12', 'r': 0.0023, 'x': 0.0839, 'g': 0, 'b': 0.0, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1.03, 'shift': 0.0, 'Line_id': '15', 'geometry': None},
        {'fromNode': '10', 'toNode': '11', 'r': 0.0023, 'x': 0.0839, 'g': 0, 'b': 0.0, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1.02, 'shift': 0.0, 'Line_id': '16', 'geometry': None},
        {'fromNode': '10', 'toNode': '12', 'r': 0.0023, 'x': 0.0839, 'g': 0, 'b': 0.0, 'MVA_rating': 400.0, 'kV_base': 230.0, 'm': 1.02, 'shift': 0.0, 'Line_id': '17', 'geometry': None},
        {'fromNode': '11', 'toNode': '13', 'r': 0.0061, 'x': 0.0476, 'g': 0, 'b': 0.0999, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '18', 'geometry': None},
        {'fromNode': '11', 'toNode': '14', 'r': 0.0054, 'x': 0.0418, 'g': 0, 'b': 0.0879, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '19', 'geometry': None},
        {'fromNode': '12', 'toNode': '13', 'r': 0.0061, 'x': 0.0476, 'g': 0, 'b': 0.0999, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '20', 'geometry': None},
        {'fromNode': '12', 'toNode': '23', 'r': 0.0124, 'x': 0.0966, 'g': 0, 'b': 0.203, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '21', 'geometry': None},
        {'fromNode': '13', 'toNode': '23', 'r': 0.0111, 'x': 0.0865, 'g': 0, 'b': 0.1818, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '22', 'geometry': None},
        {'fromNode': '14', 'toNode': '16', 'r': 0.005, 'x': 0.0389, 'g': 0, 'b': 0.0818, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '23', 'geometry': None},
        {'fromNode': '15', 'toNode': '16', 'r': 0.0022, 'x': 0.0173, 'g': 0, 'b': 0.0364, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '24', 'geometry': None},
        {'fromNode': '15', 'toNode': '21', 'r': 0.0063, 'x': 0.049, 'g': 0, 'b': 0.103, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '25', 'geometry': None},
        {'fromNode': '15', 'toNode': '21', 'r': 0.0063, 'x': 0.049, 'g': 0, 'b': 0.103, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '26', 'geometry': None},
        {'fromNode': '15', 'toNode': '24', 'r': 0.0067, 'x': 0.0519, 'g': 0, 'b': 0.1091, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '27', 'geometry': None},
        {'fromNode': '16', 'toNode': '17', 'r': 0.0033, 'x': 0.0259, 'g': 0, 'b': 0.0545, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '28', 'geometry': None},
        {'fromNode': '16', 'toNode': '19', 'r': 0.003, 'x': 0.0231, 'g': 0, 'b': 0.0485, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '29', 'geometry': None},
        {'fromNode': '17', 'toNode': '18', 'r': 0.0018, 'x': 0.0144, 'g': 0, 'b': 0.0303, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '30', 'geometry': None},
        {'fromNode': '17', 'toNode': '22', 'r': 0.0135, 'x': 0.1053, 'g': 0, 'b': 0.2212, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '31', 'geometry': None},
        {'fromNode': '18', 'toNode': '21', 'r': 0.0033, 'x': 0.0259, 'g': 0, 'b': 0.0545, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '32', 'geometry': None},
        {'fromNode': '18', 'toNode': '21', 'r': 0.0033, 'x': 0.0259, 'g': 0, 'b': 0.0545, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '33', 'geometry': None},
        {'fromNode': '19', 'toNode': '20', 'r': 0.0051, 'x': 0.0396, 'g': 0, 'b': 0.0833, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '34', 'geometry': None},
        {'fromNode': '19', 'toNode': '20', 'r': 0.0051, 'x': 0.0396, 'g': 0, 'b': 0.0833, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '35', 'geometry': None},
        {'fromNode': '20', 'toNode': '23', 'r': 0.0028, 'x': 0.0216, 'g': 0, 'b': 0.0455, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '36', 'geometry': None},
        {'fromNode': '20', 'toNode': '23', 'r': 0.0028, 'x': 0.0216, 'g': 0, 'b': 0.0455, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '37', 'geometry': None},
        {'fromNode': '21', 'toNode': '22', 'r': 0.0087, 'x': 0.0678, 'g': 0, 'b': 0.1424, 'MVA_rating': 500.0, 'kV_base': 230.0, 'm': 1, 'shift': 0, 'Line_id': '38', 'geometry': None}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='pu')
    grid.name = 'pglib_opf_case24_ieee_rts'
    

    # Add Generators
    pyf.add_gen(grid, '1', '1', price_zone_link=False, lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '1', '2', price_zone_link=False, lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '1', '3', price_zone_link=False, lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=0.0)
    pyf.add_gen(grid, '1', '4', price_zone_link=False, lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=0.0)
    pyf.add_gen(grid, '2', '5', price_zone_link=False, lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '2', '6', price_zone_link=False, lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '2', '7', price_zone_link=False, lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=0.0)
    pyf.add_gen(grid, '2', '8', price_zone_link=False, lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=0.0)
    pyf.add_gen(grid, '7', '9', price_zone_link=False, lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=0.0)
    pyf.add_gen(grid, '7', '10', price_zone_link=False, lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=0.0)
    pyf.add_gen(grid, '7', '11', price_zone_link=False, lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=0.0)
    pyf.add_gen(grid, '13', '12', price_zone_link=False, lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=0.0)
    pyf.add_gen(grid, '13', '13', price_zone_link=False, lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=0.0)
    pyf.add_gen(grid, '13', '14', price_zone_link=False, lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=0.0)
    pyf.add_gen(grid, '14', '15', price_zone_link=False, lf=0.0, qf=0.0, MWmax=0.0, MWmin=0.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=0.0, QsetMVA=35.3)
    pyf.add_gen(grid, '15', '16', price_zone_link=False, lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '17', price_zone_link=False, lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '18', price_zone_link=False, lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '19', price_zone_link=False, lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '20', price_zone_link=False, lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '21', price_zone_link=False, lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '16', '22', price_zone_link=False, lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '18', '23', price_zone_link=False, lf=4.4231, qf=0.000213, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=0.0)
    pyf.add_gen(grid, '21', '24', price_zone_link=False, lf=4.4231, qf=0.000213, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '25', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '26', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '27', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '28', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '29', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '22', '30', price_zone_link=False, lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=0.0)
    pyf.add_gen(grid, '23', '31', price_zone_link=False, lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '23', '32', price_zone_link=False, lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '23', '33', price_zone_link=False, lf=11.8495, qf=0.004895, MWmax=350.0, MWmin=140.0, MVArmax=150.0, MVArmin=-25.0, PsetMW=350.0, QsetMVA=0.0)
    
    
    # Add Renewable Source Zones

    
    # Add Renewable Sources

    
    # Return the grid
    return grid,res

pglib_opf_case24_ieee_rts()