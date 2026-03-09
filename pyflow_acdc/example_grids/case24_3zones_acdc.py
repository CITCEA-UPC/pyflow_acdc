

import pyflow_acdc as pyf
import pandas as pd

"""
Converted to PyFlowACDC format from
%CASE24_IEEE_RTS1996_3zones  Power flow data for system based on the
%IEEE RELIABILITY TEST SYSTEM.
%   Please see CASEFORMAT for details on the case file format.
%
%   This system data is based on the MATPOWER case file CASE24_IEEE_RTS
%   which is based on the IEEE RELIABILITY TEST SYSTEM
%
%   The data has been adopted to corresponding with the
%   IEEE Two Area RTS-96 data from...
%   IEEE Reliability Test System Task Force of Applications of
%   Probability Methods Subcommittee, "IEEE reliability test system-96,"
%   IEEE Transactions on Power Systems, Vol. 14, No. 3, Aug. 1999,
%   pp. 1010-1020.
%
%   The IEEE Two Area RTS-96 network has been extended and now includes 3
%   asynchronous zones (node numbers 1xx, 2xx and 3xx).
%   Data on zone 1 and 2 taken from the IEEE Two Area RTS-96 with following
%   adaptations:
%   - nodes renumbered according to IEEE Two Area RTS-96 data
%   - gen U100 at node 107 disabled (commented)
%   - gen U76 at node 201 disabled (commented)
%   - slack node zone 2: node 213
%   - lines 107-203, 113-215, 123-217 removed (commented)
%   Data on zone 3 added:
%   - nodes 301 and 302
%   - gen at node 302
%   - line 301-302
%
%   MATPOWER case file data provided by Bruce Wollenberg
%   (MATPOWER file case24_ieee_rts.m) and adapted for use with MatACDC
%   by Jef Beerten.

generator C(0) modified to 0


This grid has been modified to include Transmision expansion costs, as well as additional DC lines by Bernardo Castro Valerio (2025)

"""

def case24_3zones_acdc(TEP=False,exp='All',N_b=1,N_i=1,N_max=3,kappa=0.5):    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
    {'Node_id': '101', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.08, 'Reactive_load': 0.22, 'Bs': 0.0, 'x_coord': 26.194, 'y_coord': 0.869, 'PZ': '100'},
    {'Node_id': '102', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.97, 'Reactive_load': 0.2, 'Bs': 0.0, 'x_coord': 52.652, 'y_coord': 0.869, 'PZ': '100'},
    {'Node_id': '103', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.8, 'Reactive_load': 0.37, 'Bs': 0.0, 'x_coord': 18.256, 'y_coord': 28.65, 'PZ': '100'},
    {'Node_id': '104', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.74, 'Reactive_load': 0.15, 'Bs': 0.0, 'x_coord': 36.777, 'y_coord': 10.999, 'PZ': '100'},
    {'Node_id': '105', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.71, 'Reactive_load': 0.14, 'Bs': 0.0, 'x_coord': 50.271, 'y_coord': 10.999, 'PZ': '100'},
    {'Node_id': '106', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.36, 'Reactive_load': 0.28, 'Bs': 0.01, 'x_coord': 76.906, 'y_coord': 29.092, 'PZ': '100'},
    {'Node_id': '107', 'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.25, 'Reactive_load': 0.25, 'Bs': 0.0, 'x_coord': 69.321, 'y_coord': 0.869, 'PZ': '100'},
    {'Node_id': '108', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.71, 'Reactive_load': 0.35, 'Bs': 0.0, 'x_coord': 76.906, 'y_coord': 10.999, 'PZ': '100'},
    {'Node_id': '109', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.75, 'Reactive_load': 0.36, 'Bs': 0.0, 'x_coord': 40.847, 'y_coord': 28.65, 'PZ': '100'},
    {'Node_id': '110', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.95, 'Reactive_load': 0.4, 'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 28.65, 'PZ': '100'},
    {'Node_id': '111', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 40.847, 'y_coord': 39.035, 'PZ': '100'},
    {'Node_id': '112', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 39.035, 'PZ': '100'},
    {'Node_id': '113', 'type': 'Slack', 'Voltage_0': 1.02, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 2.65, 'Reactive_load': 0.54, 'Bs': 0.0, 'x_coord': 69.857, 'y_coord': 58.555, 'PZ': '100'},
    {'Node_id': '114', 'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.94, 'Reactive_load': 0.39, 'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 59.519, 'PZ': '100'},
    {'Node_id': '115', 'type': 'PV', 'Voltage_0': 1.014, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.17, 'Reactive_load': 0.64, 'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 59.076, 'PZ': '100'},
    {'Node_id': '116', 'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.0, 'Reactive_load': 0.2, 'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 68.791, 'PZ': '100'},
    {'Node_id': '117', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 3.81, 'y_coord': 87.209, 'PZ': '100'},
    {'Node_id': '118', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.33, 'Reactive_load': 0.68, 'Bs': 0.0, 'x_coord': 15.027, 'y_coord': 91.75, 'PZ': '100'},
    {'Node_id': '119', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.81, 'Reactive_load': 0.37, 'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 68.791, 'PZ': '100'},
    {'Node_id': '120', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.28, 'Reactive_load': 0.26, 'Bs': 0.0, 'x_coord': 51.126, 'y_coord': 68.791, 'PZ': '100'},
    {'Node_id': '121', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 34.497, 'y_coord': 91.75, 'PZ': '100'},
    {'Node_id': '122', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 62.808, 'y_coord': 91.75, 'PZ': '100'},
    {'Node_id': '123', 'type': 'PQ', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 62.484, 'y_coord': 78.201, 'PZ': '100'},
    {'Node_id': '124', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 18.256, 'y_coord': 39.035, 'PZ': '100'},
    {'Node_id': '201', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.08, 'Reactive_load': 0.22, 'Bs': 0.0, 'x_coord': 116.194, 'y_coord': 0.869, 'PZ': '200'},
    {'Node_id': '202', 'type': 'PV', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.97, 'Reactive_load': 0.2, 'Bs': 0.0, 'x_coord': 142.652, 'y_coord': 0.869, 'PZ': '200'},
    {'Node_id': '203', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.8, 'Reactive_load': 0.37, 'Bs': 0.0, 'x_coord': 108.256, 'y_coord': 28.65, 'PZ': '200'},
    {'Node_id': '204', 'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.74, 'Reactive_load': 0.15, 'Bs': 0.0, 'x_coord': 126.777, 'y_coord': 10.999, 'PZ': '200'},
    {'Node_id': '205', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 0.71, 'Reactive_load': 0.14, 'Bs': 0.0, 'x_coord': 140.271, 'y_coord': 10.999, 'PZ': '200'},
    {'Node_id': '206', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.36, 'Reactive_load': 0.28, 'Bs': 0.01, 'x_coord': 166.906, 'y_coord': 29.092, 'PZ': '200'},
    {'Node_id': '207', 'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.25, 'Reactive_load': 0.25, 'Bs': 0.0, 'x_coord': 159.321, 'y_coord': 0.869, 'PZ': '200'},
    {'Node_id': '208', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.71, 'Reactive_load': 0.35, 'Bs': 0.0, 'x_coord': 166.906, 'y_coord': 10.999, 'PZ': '200'},
    {'Node_id': '209', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.75, 'Reactive_load': 0.36, 'Bs': 0.0, 'x_coord': 130.847, 'y_coord': 28.65, 'PZ': '200'},
    {'Node_id': '210', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_load': 1.95, 'Reactive_load': 0.4, 'Bs': 0.0, 'x_coord': 152.808, 'y_coord': 28.65, 'PZ': '200'},
    {'Node_id': '211', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 130.847, 'y_coord': 39.035, 'PZ': '200'},
    {'Node_id': '212', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 152.808, 'y_coord': 39.035, 'PZ': '200'},
    {'Node_id': '213', 'type': 'Slack', 'Voltage_0': 1.02, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 2.65, 'Reactive_load': 0.54, 'Bs': 0.0, 'x_coord': 159.857, 'y_coord': 58.555, 'PZ': '200'},
    {'Node_id': '214', 'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.94, 'Reactive_load': 0.39, 'Bs': 0.0, 'x_coord': 124.497, 'y_coord': 59.519, 'PZ': '200'},
    {'Node_id': '215', 'type': 'PV', 'Voltage_0': 1.014, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.17, 'Reactive_load': 0.64, 'Bs': 0.0, 'x_coord': 105.027, 'y_coord': 59.076, 'PZ': '200'},
    {'Node_id': '216', 'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.0, 'Reactive_load': 0.2, 'Bs': 0.0, 'x_coord': 105.027, 'y_coord': 68.791, 'PZ': '200'},
    {'Node_id': '217', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 93.81, 'y_coord': 87.209, 'PZ': '200'},
    {'Node_id': '218', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 3.33, 'Reactive_load': 0.68, 'Bs': 0.0, 'x_coord': 105.027, 'y_coord': 91.75, 'PZ': '200'},
    {'Node_id': '219', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.81, 'Reactive_load': 0.37, 'Bs': 0.0, 'x_coord': 124.497, 'y_coord': 68.791, 'PZ': '200'},
    {'Node_id': '220', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 1.28, 'Reactive_load': 0.26, 'Bs': 0.0, 'x_coord': 141.126, 'y_coord': 68.791, 'PZ': '200'},
    {'Node_id': '221', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 124.497, 'y_coord': 91.75, 'PZ': '200'},
    {'Node_id': '222', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 152.808, 'y_coord': 91.75, 'PZ': '200'},
    {'Node_id': '223', 'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 152.484, 'y_coord': 78.201, 'PZ': '200'},
    {'Node_id': '224', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 108.256, 'y_coord': 39.035, 'PZ': '200'},
    {'Node_id': '301', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 93.81, 'y_coord': 27.092, 'PZ': '300'},
    {'Node_id': '302', 'type': 'Slack', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 230.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Bs': 0.0, 'x_coord': 93.81, 'y_coord': 22.092, 'PZ': '300'}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'Line_id': 'L_AC_1', 'fromNode': '101', 'toNode': '102', 'r': 0.003, 'x': 0.014, 'b': 0.461, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_2', 'fromNode': '101', 'toNode': '103', 'r': 0.055, 'x': 0.211, 'b': 0.057, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_3', 'fromNode': '101', 'toNode': '105', 'r': 0.022, 'x': 0.085, 'b': 0.023, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_4', 'fromNode': '102', 'toNode': '104', 'r': 0.033, 'x': 0.127, 'b': 0.034, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_5', 'fromNode': '102', 'toNode': '106', 'r': 0.05, 'x': 0.192, 'b': 0.052, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_6', 'fromNode': '103', 'toNode': '109', 'r': 0.031, 'x': 0.119, 'b': 0.032, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_7', 'fromNode': '103', 'toNode': '124', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_8', 'fromNode': '104', 'toNode': '109', 'r': 0.027, 'x': 0.104, 'b': 0.028, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_9', 'fromNode': '105', 'toNode': '110', 'r': 0.022, 'x': 0.088, 'b': 0.024, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_10', 'fromNode': '106', 'toNode': '110', 'r': 0.014, 'x': 0.061, 'b': 2.459, 'MVA_rating': 400.0, 'm': 1.0},
        {'Line_id': 'L_AC_11', 'fromNode': '107', 'toNode': '108', 'r': 0.016, 'x': 0.061, 'b': 0.017, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_12', 'fromNode': '108', 'toNode': '109', 'r': 0.043, 'x': 0.165, 'b': 0.045, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_13', 'fromNode': '108', 'toNode': '110', 'r': 0.043, 'x': 0.165, 'b': 0.045, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_14', 'fromNode': '109', 'toNode': '111', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.03},
        {'Line_id': 'L_AC_15', 'fromNode': '109', 'toNode': '112', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.03},
        {'Line_id': 'L_AC_16', 'fromNode': '110', 'toNode': '111', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_17', 'fromNode': '110', 'toNode': '112', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_18', 'fromNode': '111', 'toNode': '113', 'r': 0.006, 'x': 0.048, 'b': 0.1, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_19', 'fromNode': '111', 'toNode': '114', 'r': 0.005, 'x': 0.042, 'b': 0.088, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_20', 'fromNode': '112', 'toNode': '113', 'r': 0.006, 'x': 0.048, 'b': 0.1, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_21', 'fromNode': '112', 'toNode': '123', 'r': 0.012, 'x': 0.097, 'b': 0.203, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_22', 'fromNode': '113', 'toNode': '123', 'r': 0.011, 'x': 0.087, 'b': 0.182, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_23', 'fromNode': '114', 'toNode': '116', 'r': 0.005, 'x': 0.059, 'b': 0.082, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_24', 'fromNode': '115', 'toNode': '116', 'r': 0.002, 'x': 0.017, 'b': 0.036, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_25', 'fromNode': '115', 'toNode': '121', 'r': 0.006, 'x': 0.049, 'b': 0.103, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_26', 'fromNode': '115', 'toNode': '121', 'r': 0.006, 'x': 0.049, 'b': 0.103, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_27', 'fromNode': '115', 'toNode': '124', 'r': 0.007, 'x': 0.052, 'b': 0.109, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_28', 'fromNode': '116', 'toNode': '117', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_29', 'fromNode': '116', 'toNode': '119', 'r': 0.003, 'x': 0.023, 'b': 0.049, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_30', 'fromNode': '117', 'toNode': '118', 'r': 0.002, 'x': 0.014, 'b': 0.03, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_31', 'fromNode': '117', 'toNode': '122', 'r': 0.014, 'x': 0.105, 'b': 0.221, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_32', 'fromNode': '118', 'toNode': '121', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_33', 'fromNode': '118', 'toNode': '121', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_34', 'fromNode': '119', 'toNode': '120', 'r': 0.005, 'x': 0.04, 'b': 0.083, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_35', 'fromNode': '119', 'toNode': '120', 'r': 0.005, 'x': 0.04, 'b': 0.083, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_36', 'fromNode': '120', 'toNode': '123', 'r': 0.003, 'x': 0.022, 'b': 0.046, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_37', 'fromNode': '120', 'toNode': '123', 'r': 0.003, 'x': 0.022, 'b': 0.046, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_38', 'fromNode': '121', 'toNode': '122', 'r': 0.009, 'x': 0.068, 'b': 0.142, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_39', 'fromNode': '201', 'toNode': '202', 'r': 0.003, 'x': 0.014, 'b': 0.461, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_40', 'fromNode': '201', 'toNode': '203', 'r': 0.055, 'x': 0.211, 'b': 0.057, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_41', 'fromNode': '201', 'toNode': '205', 'r': 0.022, 'x': 0.085, 'b': 0.023, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_42', 'fromNode': '202', 'toNode': '204', 'r': 0.033, 'x': 0.127, 'b': 0.034, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_43', 'fromNode': '202', 'toNode': '206', 'r': 0.05, 'x': 0.192, 'b': 0.052, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_44', 'fromNode': '203', 'toNode': '209', 'r': 0.031, 'x': 0.119, 'b': 0.032, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_45', 'fromNode': '203', 'toNode': '224', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_46', 'fromNode': '204', 'toNode': '209', 'r': 0.027, 'x': 0.104, 'b': 0.028, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_47', 'fromNode': '205', 'toNode': '210', 'r': 0.022, 'x': 0.088, 'b': 0.024, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_48', 'fromNode': '206', 'toNode': '210', 'r': 0.014, 'x': 0.061, 'b': 2.459, 'MVA_rating': 400.0, 'm': 1.0},
        {'Line_id': 'L_AC_49', 'fromNode': '207', 'toNode': '208', 'r': 0.016, 'x': 0.061, 'b': 0.017, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_50', 'fromNode': '208', 'toNode': '209', 'r': 0.043, 'x': 0.165, 'b': 0.045, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_51', 'fromNode': '208', 'toNode': '210', 'r': 0.043, 'x': 0.165, 'b': 0.045, 'MVA_rating': 175.0, 'm': 1.0},
        {'Line_id': 'L_AC_52', 'fromNode': '209', 'toNode': '211', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.03},
        {'Line_id': 'L_AC_53', 'fromNode': '209', 'toNode': '212', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.03},
        {'Line_id': 'L_AC_54', 'fromNode': '210', 'toNode': '211', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_55', 'fromNode': '210', 'toNode': '212', 'r': 0.002, 'x': 0.084, 'b': 0.0, 'MVA_rating': 400.0, 'm': 1.015},
        {'Line_id': 'L_AC_56', 'fromNode': '211', 'toNode': '213', 'r': 0.006, 'x': 0.048, 'b': 0.1, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_57', 'fromNode': '211', 'toNode': '214', 'r': 0.005, 'x': 0.042, 'b': 0.088, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_58', 'fromNode': '212', 'toNode': '213', 'r': 0.006, 'x': 0.048, 'b': 0.1, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_59', 'fromNode': '212', 'toNode': '223', 'r': 0.012, 'x': 0.097, 'b': 0.203, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_60', 'fromNode': '213', 'toNode': '223', 'r': 0.011, 'x': 0.087, 'b': 0.182, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_61', 'fromNode': '214', 'toNode': '216', 'r': 0.005, 'x': 0.059, 'b': 0.082, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_62', 'fromNode': '215', 'toNode': '216', 'r': 0.002, 'x': 0.017, 'b': 0.036, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_63', 'fromNode': '215', 'toNode': '221', 'r': 0.006, 'x': 0.049, 'b': 0.103, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_64', 'fromNode': '215', 'toNode': '221', 'r': 0.006, 'x': 0.049, 'b': 0.103, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_65', 'fromNode': '215', 'toNode': '224', 'r': 0.007, 'x': 0.052, 'b': 0.109, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_66', 'fromNode': '216', 'toNode': '217', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_67', 'fromNode': '216', 'toNode': '219', 'r': 0.003, 'x': 0.023, 'b': 0.049, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_68', 'fromNode': '217', 'toNode': '218', 'r': 0.002, 'x': 0.014, 'b': 0.03, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_69', 'fromNode': '217', 'toNode': '222', 'r': 0.014, 'x': 0.105, 'b': 0.221, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_70', 'fromNode': '218', 'toNode': '221', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_71', 'fromNode': '218', 'toNode': '221', 'r': 0.003, 'x': 0.026, 'b': 0.055, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_72', 'fromNode': '219', 'toNode': '220', 'r': 0.005, 'x': 0.04, 'b': 0.083, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_73', 'fromNode': '219', 'toNode': '220', 'r': 0.005, 'x': 0.04, 'b': 0.083, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_74', 'fromNode': '220', 'toNode': '223', 'r': 0.003, 'x': 0.022, 'b': 0.046, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_75', 'fromNode': '220', 'toNode': '223', 'r': 0.003, 'x': 0.022, 'b': 0.046, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_76', 'fromNode': '221', 'toNode': '222', 'r': 0.009, 'x': 0.068, 'b': 0.142, 'MVA_rating': 500.0, 'm': 1.0},
        {'Line_id': 'L_AC_77', 'fromNode': '301', 'toNode': '302', 'r': 0.0, 'x': 0.001, 'b': 0.0, 'MVA_rating': 500.0, 'm': 1.0}
    ]
    

    
    nodes_DC_data = [
    {'type': 'Slack', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 150.0, 'Node_id': '1'},
    {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 150.0, 'Node_id': '2'},
    {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 150.0, 'Node_id': '3'},
    {'type': 'Slack', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 300.0, 'Node_id': '4'},
    {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 300.0, 'Node_id': '5'},
    {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 300.0, 'Node_id': '6'},
    {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 300.0, 'Node_id': '7'}
    ]

    Converters_ACDC_data = [
    {'Conv_id': 'Conv_1', 'AC_type': 'PQ', 'DC_type': 'Slack', 'AC_node': '107', 'DC_node': '1', 'P_AC': 0.0, 'Q_AC': 0.5, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.09, 'AC_kV_base': 138.0, 'MVA_rating': 200.0, 'Nconverter': 1.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_2', 'AC_type': 'PV', 'DC_type': 'P', 'AC_node': '204', 'DC_node': '2', 'P_AC': 0.753, 'Q_AC': -0.5, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.09, 'AC_kV_base': 138.0, 'MVA_rating': 200.0, 'Nconverter': 1.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_3', 'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '301', 'DC_node': '3', 'P_AC': -1.419, 'Q_AC': 1.3, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.09, 'AC_kV_base': 138.0, 'MVA_rating': 200.0, 'Nconverter': 2.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_4', 'AC_type': 'PQ', 'DC_type': 'Slack', 'AC_node': '113', 'DC_node': '4', 'P_AC': 1.315, 'Q_AC': 0.759, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.0, 'AC_kV_base': 345.0, 'MVA_rating': 200.0, 'Nconverter': 2.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 1.8, 'losscrect': 11.88, 'losscinv': 18.0, 'Ucmin': 0.5, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_5', 'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '123', 'DC_node': '5', 'P_AC': -0.617, 'Q_AC': 0.0, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.0, 'AC_kV_base': 345.0, 'MVA_rating': 200.0, 'Nconverter': 1.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 1.8, 'losscrect': 11.88, 'losscinv': 18.0, 'Ucmin': 0.5, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_6', 'AC_type': 'PV', 'DC_type': 'P', 'AC_node': '215', 'DC_node': '6', 'P_AC': -1.234, 'Q_AC': -0.1, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.0, 'AC_kV_base': 345.0, 'MVA_rating': 200.0, 'Nconverter': 2.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 1.8, 'losscrect': 11.88, 'losscinv': 18.0, 'Ucmin': 0.5, 'Ucmax': 1.2, 'Cost MEUR': 26.0},
    {'Conv_id': 'Conv_7', 'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '217', 'DC_node': '7', 'P_AC': 0.5, 'Q_AC': 0.2, 'T_r': 0.001, 'T_x': 0.1, 'PR_r': 0.0001, 'PR_x': 0.16, 'Filter_b': 0.0, 'AC_kV_base': 345.0, 'MVA_rating': 200.0, 'Nconverter': 1.0, 'pol': 1.0, 'lossa': 1.103, 'lossb': 1.8, 'losscrect': 11.88, 'losscinv': 18.0, 'Ucmin': 0.5, 'Ucmax': 1.2, 'Cost MEUR': 26.0}
    ]
    
    lines_DC_data = [
    {'Line_id': 'L_DC_1', 'fromNode': '1', 'toNode': '3', 'r': 0.0352, 'MW_rating': 100, 'kV_base': 150.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 1.76},
    {'Line_id': 'L_DC_2', 'fromNode': '2', 'toNode': '3', 'r': 0.0352, 'MW_rating': 100, 'kV_base': 150.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 1.76},
    {'Line_id': 'L_DC_3', 'fromNode': '4', 'toNode': '5', 'r': 0.0828, 'MW_rating': 100, 'kV_base': 300.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 4.14},
    {'Line_id': 'L_DC_4', 'fromNode': '4', 'toNode': '7', 'r': 0.0704, 'MW_rating': 100, 'kV_base': 300.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 3.52},
    {'Line_id': 'L_DC_5', 'fromNode': '4', 'toNode': '6', 'r': 0.0718, 'MW_rating': 100, 'kV_base': 300.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 3.59},
    {'Line_id': 'L_DC_6', 'fromNode': '5', 'toNode': '7', 'r': 0.076, 'MW_rating': 100, 'kV_base': 300.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 3.8},
    {'Line_id': 'L_DC_7', 'fromNode': '6', 'toNode': '7', 'r': 0.0248, 'MW_rating': 100, 'kV_base': 300.0, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Cost MEUR': 1.24}
    ]
    
    if TEP:
        nodes_DC_data[3]['type']= 'P'
        Converters_ACDC_data[3]['DC_type']= 'P'
        # Update MVA rating for line 301-302 (index 76)
        lines_AC_data[76]['MVA_rating']= 800
        lines_DC_data_extra =   [
        {'Line_id': 'L_DC_8', 'fromNode': '3', 'toNode': '6', 'r': 0.0684, 'MW_rating': 100.0, 'kV_base': 300.0, 'Length_km': '1', 'Mono_Bi_polar': 'sm', 'Cost MEUR': 3.42},
        {'Line_id': 'L_DC_9', 'fromNode': '3', 'toNode': '4', 'r': 0.0684, 'MW_rating': 100.0, 'kV_base': 300.0, 'Length_km': '1', 'Mono_Bi_polar': 'sm', 'Cost MEUR': 3.42}
        ]
        
        lines_DC_data.extend(lines_DC_data_extra)

    lines_AC = pd.DataFrame(lines_AC_data)    
    nodes_DC = pd.DataFrame(nodes_DC_data)
    lines_DC = pd.DataFrame(lines_DC_data)
    
    
    Converters_ACDC = pd.DataFrame(Converters_ACDC_data)

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'case24_3zones_acdc_TEP'

    pyf.add_price_zone(grid, '100', 1)
    pyf.add_price_zone(grid, '200', 1)
    pyf.add_price_zone(grid, '300', 1)

    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
            
    # Add Generators
    pyf.add_gen(grid, '101', '1', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '101', '2', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '101', '3', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=14.099999999999998)
    pyf.add_gen(grid, '101', '4', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=14.099999999999998)
    pyf.add_gen(grid, '102', '5', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '102', '6', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '102', '7', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=7.000000000000001)
    pyf.add_gen(grid, '102', '8', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=7.000000000000001)
    pyf.add_gen(grid, '107', '9', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=17.2)
    pyf.add_gen(grid, '107', '10', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=17.2)
    pyf.add_gen(grid, '113', '11', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '113', '12', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '113', '13', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '114', '14', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=0.0, MWmin=0.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=0.0, QsetMVA=13.699999999999998)
    pyf.add_gen(grid, '115', '15', np_gen=1, fc=0.0,lf=0.0, qf=0.0, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '115', '16', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '115', '17', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '115', '18', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '115', '19', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '115', '20', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.05)
    pyf.add_gen(grid, '116', '21', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=25.22)
    pyf.add_gen(grid, '118', '22', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=137.4)
    pyf.add_gen(grid, '121', '23', np_gen=1, fc=395.3749,lf=4.4231, qf=0.000213, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=108.2)
    pyf.add_gen(grid, '122', '24', np_gen=1, fc=395.3749,lf=4.4231, qf=0.000213, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '122', '25', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '122', '26', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '122', '27', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '122', '28', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '122', '29', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '123', '30', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=31.790000000000003)
    pyf.add_gen(grid, '123', '31', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=31.790000000000003)
    pyf.add_gen(grid, '123', '32', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=350.0, MWmin=140.0, MVArmax=150.0, MVArmin=-25.0, PsetMW=350.0, QsetMVA=71.78)
    pyf.add_gen(grid, '201', '33', np_gen=1, fc=665.1094,lf=11.8495, qf=0.004895, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '201', '34', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '201', '35', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=14.099999999999998)
    pyf.add_gen(grid, '202', '36', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '202', '37', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=20.0, MWmin=16.0, MVArmax=10.0, MVArmin=0.0, PsetMW=10.0, QsetMVA=0.0)
    pyf.add_gen(grid, '202', '38', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=7.000000000000001)
    pyf.add_gen(grid, '202', '39', np_gen=1, fc=400.6849,lf=130.0, qf=0.0, MWmax=76.0, MWmin=15.2, MVArmax=30.0, MVArmin=-25.0, PsetMW=76.0, QsetMVA=7.000000000000001)
    pyf.add_gen(grid, '207', '40', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=17.2)
    pyf.add_gen(grid, '207', '41', np_gen=1, fc=212.3076,lf=16.0811, qf=0.014142, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=17.2)
    pyf.add_gen(grid, '207', '42', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=100.0, MWmin=25.0, MVArmax=60.0, MVArmin=0.0, PsetMW=80.0, QsetMVA=17.2)
    pyf.add_gen(grid, '213', '43', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '213', '44', np_gen=1, fc=781.521,lf=43.6615, qf=0.052672, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '213', '45', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=197.0, MWmin=69.0, MVArmax=80.0, MVArmin=0.0, PsetMW=95.1, QsetMVA=40.7)
    pyf.add_gen(grid, '214', '46', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=0.0, MWmin=0.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=0.0, QsetMVA=13.68)
    pyf.add_gen(grid, '215', '47', np_gen=1, fc=832.7575,lf=48.5804, qf=0.00717, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '215', '48', np_gen=1, fc=0.0,lf=0.0, qf=0.0, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '215', '49', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '215', '50', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '215', '51', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=12.0, MWmin=2.4, MVArmax=6.0, MVArmin=0.0, PsetMW=12.0, QsetMVA=0.0)
    pyf.add_gen(grid, '215', '52', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=0.048)
    pyf.add_gen(grid, '216', '53', np_gen=1, fc=86.3852,lf=56.564, qf=0.328412, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=25.22)
    pyf.add_gen(grid, '218', '54', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=137.4)
    pyf.add_gen(grid, '221', '55', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=400.0, MWmin=100.0, MVArmax=200.0, MVArmin=-50.0, PsetMW=400.0, QsetMVA=108.2)
    pyf.add_gen(grid, '222', '56', np_gen=1, fc=395.3749,lf=4.4231, qf=0.000213, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '222', '57', np_gen=1, fc=395.3749,lf=4.4231, qf=0.000213, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '222', '58', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '222', '59', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '222', '60', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '222', '61', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=50.0, MWmin=10.0, MVArmax=16.0, MVArmin=-10.0, PsetMW=50.0, QsetMVA=-4.96)
    pyf.add_gen(grid, '223', '62', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=31.790000000000003)
    pyf.add_gen(grid, '223', '63', np_gen=1, fc=0.001,lf=0.001, qf=0.0, MWmax=155.0, MWmin=54.29999999999999, MVArmax=80.0, MVArmin=-50.0, PsetMW=155.0, QsetMVA=31.790000000000003)
    pyf.add_gen(grid, '223', '64', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=350.0, MWmin=140.0, MVArmax=150.0, MVArmin=-25.0, PsetMW=350.0, QsetMVA=71.78)
    if TEP:
        pyf.add_gen(grid, '302', '65', np_gen=1, fc=382.2391,lf=0, qf=0, MWmax=700.0, MWmin=100.0, MVArmax=300.0, MVArmin=-50.0, PsetMW=300.0, QsetMVA=20.0)
    else:
        pyf.add_gen(grid, '302', '65', np_gen=1, fc=382.2391,lf=12.3883, qf=0.008342, MWmax=350.0, MWmin=140.0, MVArmax=150.0, MVArmin=-25.0, PsetMW=150.0, QsetMVA=10.0)
    
    
    if TEP==True:

        lines_AC['Cost MEUR'] = lines_AC['Cost MEUR'] * kappa/0.5
        lines_DC['Cost MEUR'] = lines_DC['Cost MEUR'] * kappa/0.5
        Converters_ACDC['Cost MEUR'] = Converters_ACDC['Cost MEUR'] * kappa/0.5
        lines_DC.set_index('Line_id', inplace=True)
        Converters_ACDC.set_index('Conv_id', inplace=True)
        if exp == 'All':
            for line in list(grid.lines_DC):  # Create a copy of the list
                name = line.name
                line_cost = lines_DC.loc[name,'Cost MEUR']*10**6
                pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
            for conv in list(grid.Converters_ACDC):  # Create a copy of the list
                name = conv.name
                conv_cost = Converters_ACDC.loc[name,'Cost MEUR']*10**6
                pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=conv_cost)    
        else:
            for line in list(grid.lines_DC):  
                name = line.name
                if name not in exp:
                    continue
                line_cost = lines_DC.loc[name,'Cost MEUR']*10**6
                pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
            for conv in list(grid.Converters_ACDC):  
                name = conv.name
                if name not in exp:
                    continue
                conv_cost = Converters_ACDC.loc[name,'Cost MEUR']*10**6
                pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=conv_cost)
                
                
                
    return grid,res