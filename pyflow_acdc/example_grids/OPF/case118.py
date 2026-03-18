

import pyflow_acdc as pyf
import pandas as pd

"""
Converted to PyFlowACDC format from

function mpc = case118
%CASE118    Power flow data for IEEE 118 bus test case.
%   Please see CASEFORMAT for details on the case file format.
%   This data was converted from IEEE Common Data Format
%   (ieee118cdf.txt) on 15-Oct-2014 by cdf2matp, rev. 2393
%   See end of file for warnings generated during conversion.
%
%   Converted from IEEE CDF file from:
%       https://labs.ece.uw.edu/pstca/
%   With baseKV data take from the PSAP format file from the same site,
%   added manually on 10-Mar-2006.
%   Branches 86--87, 68--116 changed from transmission lines (tap ratio = 0)
%   to transformers (tap ratio = 1) for consistency with bus base voltages
%   on 2019-02-15.
% 
%   08/25/93 UW ARCHIVE           100.0  1961 W IEEE 118 Bus Test Case

%   MATPOWER
"""

def case118():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.18622663118779495, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.51, 'Reactive_load': 0.27, 'Node_id': '1.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.971, 'theta_0': 0.19582594207376378, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.09, 'Node_id': '2.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.968, 'theta_0': 0.20176006153054452, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.1, 'Node_id': '3.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.26668630970473356, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.12, 'Node_id': '4.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.002, 'theta_0': 0.27454029133870805, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.4, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.22689280275926285, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.52, 'Reactive_load': 0.22, 'Node_id': '6.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.989, 'theta_0': 0.2192133540504878, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.19, 'Reactive_load': 0.02, 'Node_id': '7.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.36250488563922223, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.0, 'Node_id': '8.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.043, 'theta_0': 0.48904125640881113, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '9.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.6215117466351807, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '10.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.985, 'theta_0': 0.22200588085367873, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.7, 'Reactive_load': 0.23, 'Node_id': '11.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.2129301687433082, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.47, 'Reactive_load': 0.1, 'Node_id': '12.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.968, 'theta_0': 0.1980948701013564, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.16, 'Node_id': '13.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.984, 'theta_0': 0.2007128639793479, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.14, 'Reactive_load': 0.01, 'Node_id': '14.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.19600047499896323, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.9, 'Reactive_load': 0.3, 'Node_id': '15.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.984, 'theta_0': 0.20786871391252465, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.25, 'Reactive_load': 0.1, 'Node_id': '16.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.995, 'theta_0': 0.2398082392240209, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.11, 'Reactive_load': 0.03, 'Node_id': '17.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.2012364627549462, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.6, 'Reactive_load': 0.34, 'Node_id': '18.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.963, 'theta_0': 0.19285888234537343, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.45, 'Reactive_load': 0.25, 'Node_id': '19.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.958, 'theta_0': 0.20821777976292352, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.03, 'Node_id': '20.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.959, 'theta_0': 0.23596851486963336, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.14, 'Reactive_load': 0.08, 'Node_id': '21.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.97, 'theta_0': 0.28064894372068816, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.1, 'Reactive_load': 0.05, 'Node_id': '22.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.3665191429188092, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.07, 'Reactive_load': 0.03, 'Node_id': '23.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.992, 'theta_0': 0.36459928074161546, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.13, 'Reactive_load': 0.0, 'Node_id': '24.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.4874704600820162, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '25.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.5185373207675154, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '26.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.968, 'theta_0': 0.26790804018112957, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.71, 'Reactive_load': 0.13, 'Node_id': '27.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.962, 'theta_0': 0.23771384412162766, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.07, 'Node_id': '28.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.963, 'theta_0': 0.22043508452688385, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.24, 'Reactive_load': 0.04, 'Node_id': '29.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.968, 'theta_0': 0.3279473664497345, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '30.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.967, 'theta_0': 0.22252947962927702, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.43, 'Reactive_load': 0.27, 'Node_id': '31.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.964, 'theta_0': 0.2583087292951608, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.59, 'Reactive_load': 0.23, 'Node_id': '32.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.972, 'theta_0': 0.18552849948699723, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.09, 'Node_id': '33.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.986, 'theta_0': 0.19722220547535926, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.59, 'Reactive_load': 0.26, 'Node_id': '34.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.14, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.981, 'theta_0': 0.1897172896917836, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.33, 'Reactive_load': 0.09, 'Node_id': '35.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.1897172896917836, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.31, 'Reactive_load': 0.17, 'Node_id': '36.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.992, 'theta_0': 0.20542525295973257, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '37.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.25, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.962, 'theta_0': 0.29513517651224114, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '38.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.97, 'theta_0': 0.1467821900927231, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.27, 'Reactive_load': 0.11, 'Node_id': '39.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.1282817000215832, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.66, 'Reactive_load': 0.23, 'Node_id': '40.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.967, 'theta_0': 0.1207767842380076, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.37, 'Reactive_load': 0.1, 'Node_id': '41.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.1488765851951163, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.96, 'Reactive_load': 0.23, 'Node_id': '42.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.978, 'theta_0': 0.19687313962496036, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.07, 'Node_id': '43.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.985, 'theta_0': 0.24120450262561635, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.16, 'Reactive_load': 0.08, 'Node_id': '44.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.987, 'theta_0': 0.27349309378751147, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.53, 'Reactive_load': 0.22, 'Node_id': '45.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.3227113786937515, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.1, 'Node_id': '46.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.017, 'theta_0': 0.36180675393842454, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.0, 'Node_id': '47.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.021, 'theta_0': 0.3478441199224699, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.11, 'Node_id': '48.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.15, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.3654719453676126, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.87, 'Reactive_load': 0.3, 'Node_id': '49.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.001, 'theta_0': 0.32986722862692824, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.04, 'Node_id': '50.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.967, 'theta_0': 0.2841396022246769, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.08, 'Node_id': '51.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.957, 'theta_0': 0.2673844414055313, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.05, 'Node_id': '52.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.946, 'theta_0': 0.2504547476611863, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.11, 'Node_id': '53.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.26633724385433466, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.13, 'Reactive_load': 0.32, 'Node_id': '54.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.26127578902355114, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.63, 'Reactive_load': 0.22, 'Node_id': '55.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.954, 'theta_0': 0.2645919146023404, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.84, 'Reactive_load': 0.18, 'Node_id': '56.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.971, 'theta_0': 0.2855358656262723, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '57.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.959, 'theta_0': 0.2707005669843205, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '58.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.33807027611130164, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.77, 'Reactive_load': 1.13, 'Node_id': '59.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.993, 'theta_0': 0.40404372183668724, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.78, 'Reactive_load': 0.03, 'Node_id': '60.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.995, 'theta_0': 0.4195771521794368, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '61.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.4089306437422714, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.77, 'Reactive_load': 0.14, 'Node_id': '62.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.969, 'theta_0': 0.39706240482870997, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '63.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.984, 'theta_0': 0.4279547325890096, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '64.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.48258353817643207, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '65.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.4796164784480418, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.18, 'Node_id': '66.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.02, 'theta_0': 0.43353978619539146, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.07, 'Node_id': '67.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.003, 'theta_0': 0.4808382089244378, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '68.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Slack', 'Voltage_0': 1.035, 'theta_0': 0.5235987755982988, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '69.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.984, 'theta_0': 0.39409534510031957, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.66, 'Reactive_load': 0.2, 'Node_id': '70.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.987, 'theta_0': 0.386590429316744, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '71.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.36617007706841037, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.0, 'Node_id': '72.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.991, 'theta_0': 0.38292523788755595, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '73.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.958, 'theta_0': 0.37768925013157295, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.27, 'Node_id': '74.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.12, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.967, 'theta_0': 0.3998549316319009, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.47, 'Reactive_load': 0.11, 'Node_id': '75.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.943, 'theta_0': 0.37995817815916555, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.36, 'Node_id': '76.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.006, 'theta_0': 0.4663519761328848, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.61, 'Reactive_load': 0.28, 'Node_id': '77.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.003, 'theta_0': 0.4611159883769019, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.71, 'Reactive_load': 0.26, 'Node_id': '78.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.009, 'theta_0': 0.4663519761328848, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.32, 'Node_id': '79.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.04, 'theta_0': 0.5054473513775578, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.3, 'Reactive_load': 0.26, 'Node_id': '80.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.997, 'theta_0': 0.4904375198104066, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '81.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.989, 'theta_0': 0.4754276882432553, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.54, 'Reactive_load': 0.27, 'Node_id': '82.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.985, 'theta_0': 0.4960225734167885, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.1, 'Node_id': '83.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.98, 'theta_0': 0.540179403492245, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.11, 'Reactive_load': 0.07, 'Node_id': '84.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.5674065398233565, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.24, 'Reactive_load': 0.15, 'Node_id': '85.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.987, 'theta_0': 0.5434955290710343, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.21, 'Reactive_load': 0.1, 'Node_id': '86.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.5480333851262195, 'kV_base': 161.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '87.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.987, 'theta_0': 0.6220353454107791, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.48, 'Reactive_load': 0.1, 'Node_id': '88.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.6927211801165494, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '89.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.5810201079889122, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.63, 'Reactive_load': 0.42, 'Node_id': '90.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.5813691738393112, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.1, 'Reactive_load': 0.0, 'Node_id': '91.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.993, 'theta_0': 0.5899212871740833, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.65, 'Reactive_load': 0.1, 'Node_id': '92.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.987, 'theta_0': 0.537386876689054, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.07, 'Node_id': '93.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.991, 'theta_0': 0.49986229777117597, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.3, 'Reactive_load': 0.16, 'Node_id': '94.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.981, 'theta_0': 0.482932604026831, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.42, 'Reactive_load': 0.31, 'Node_id': '95.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.993, 'theta_0': 0.4801400772236401, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.38, 'Reactive_load': 0.15, 'Node_id': '96.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.011, 'theta_0': 0.48659779545601906, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.15, 'Reactive_load': 0.09, 'Node_id': '97.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.024, 'theta_0': 0.4782202150464463, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.08, 'Node_id': '98.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.4719370297392667, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.42, 'Reactive_load': 0.0, 'Node_id': '99.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.4892157893340106, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.37, 'Reactive_load': 0.18, 'Node_id': '100.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.993, 'theta_0': 0.516791991515521, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.22, 'Reactive_load': 0.15, 'Node_id': '101.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.991, 'theta_0': 0.5637413483941683, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.05, 'Reactive_load': 0.03, 'Node_id': '102.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.001, 'theta_0': 0.4265584691874142, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.16, 'Node_id': '103.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.971, 'theta_0': 0.3785619147575701, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.38, 'Reactive_load': 0.25, 'Node_id': '104.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.965, 'theta_0': 0.35901422713523357, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.31, 'Reactive_load': 0.26, 'Node_id': '105.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.962, 'theta_0': 0.3546509040052478, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.43, 'Reactive_load': 0.16, 'Node_id': '106.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.305956217874606, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.5, 'Reactive_load': 0.12, 'Node_id': '107.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.967, 'theta_0': 0.33824480903650106, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.02, 'Reactive_load': 0.01, 'Node_id': '108.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.967, 'theta_0': 0.33039082740252657, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '109.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.3157300616857742, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.3, 'Node_id': '110.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.34452799434368064, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '111.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.975, 'theta_0': 0.26162485487395, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.13, 'Node_id': '112.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 0.993, 'theta_0': 0.2398082392240209, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '113.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.96, 'theta_0': 0.25237460983838006, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '114.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.96, 'theta_0': 0.25237460983838006, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.22, 'Reactive_load': 0.07, 'Node_id': '115.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.4733332931408622, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.84, 'Reactive_load': 0.0, 'Node_id': '116.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.974, 'theta_0': 0.18622663118779495, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.08, 'Node_id': '117.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 0.949, 'theta_0': 0.38257617203715705, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.33, 'Reactive_load': 0.15, 'Node_id': '118.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.0303, 'x': 0.0999, 'g': 0, 'b': 0.0254, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '1'},
        {'fromNode': '1.0', 'toNode': '3.0', 'r': 0.0129, 'x': 0.0424, 'g': 0, 'b': 0.01082, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '2'},
        {'fromNode': '4.0', 'toNode': '5.0', 'r': 0.00176, 'x': 0.00798, 'g': 0, 'b': 0.0021, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '3'},
        {'fromNode': '3.0', 'toNode': '5.0', 'r': 0.0241, 'x': 0.108, 'g': 0, 'b': 0.0284, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '4'},
        {'fromNode': '5.0', 'toNode': '6.0', 'r': 0.0119, 'x': 0.054, 'g': 0, 'b': 0.01426, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '5'},
        {'fromNode': '6.0', 'toNode': '7.0', 'r': 0.00459, 'x': 0.0208, 'g': 0, 'b': 0.0055, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '6'},
        {'fromNode': '8.0', 'toNode': '9.0', 'r': 0.00244, 'x': 0.0305, 'g': 0, 'b': 1.162, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '7'},
        {'fromNode': '8.0', 'toNode': '5.0', 'r': 0.0, 'x': 0.0267, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.985, 'shift': 0.0, 'Line_id': '8'},
        {'fromNode': '9.0', 'toNode': '10.0', 'r': 0.00258, 'x': 0.0322, 'g': 0, 'b': 1.23, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '9'},
        {'fromNode': '4.0', 'toNode': '11.0', 'r': 0.0209, 'x': 0.0688, 'g': 0, 'b': 0.01748, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '10'},
        {'fromNode': '5.0', 'toNode': '11.0', 'r': 0.0203, 'x': 0.0682, 'g': 0, 'b': 0.01738, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '11'},
        {'fromNode': '11.0', 'toNode': '12.0', 'r': 0.00595, 'x': 0.0196, 'g': 0, 'b': 0.00502, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '12'},
        {'fromNode': '2.0', 'toNode': '12.0', 'r': 0.0187, 'x': 0.0616, 'g': 0, 'b': 0.01572, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '13'},
        {'fromNode': '3.0', 'toNode': '12.0', 'r': 0.0484, 'x': 0.16, 'g': 0, 'b': 0.0406, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '14'},
        {'fromNode': '7.0', 'toNode': '12.0', 'r': 0.00862, 'x': 0.034, 'g': 0, 'b': 0.00874, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '15'},
        {'fromNode': '11.0', 'toNode': '13.0', 'r': 0.02225, 'x': 0.0731, 'g': 0, 'b': 0.01876, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '16'},
        {'fromNode': '12.0', 'toNode': '14.0', 'r': 0.0215, 'x': 0.0707, 'g': 0, 'b': 0.01816, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '17'},
        {'fromNode': '13.0', 'toNode': '15.0', 'r': 0.0744, 'x': 0.2444, 'g': 0, 'b': 0.06268, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '18'},
        {'fromNode': '14.0', 'toNode': '15.0', 'r': 0.0595, 'x': 0.195, 'g': 0, 'b': 0.0502, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '19'},
        {'fromNode': '12.0', 'toNode': '16.0', 'r': 0.0212, 'x': 0.0834, 'g': 0, 'b': 0.0214, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '20'},
        {'fromNode': '15.0', 'toNode': '17.0', 'r': 0.0132, 'x': 0.0437, 'g': 0, 'b': 0.0444, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '21'},
        {'fromNode': '16.0', 'toNode': '17.0', 'r': 0.0454, 'x': 0.1801, 'g': 0, 'b': 0.0466, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '22'},
        {'fromNode': '17.0', 'toNode': '18.0', 'r': 0.0123, 'x': 0.0505, 'g': 0, 'b': 0.01298, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '23'},
        {'fromNode': '18.0', 'toNode': '19.0', 'r': 0.01119, 'x': 0.0493, 'g': 0, 'b': 0.01142, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '24'},
        {'fromNode': '19.0', 'toNode': '20.0', 'r': 0.0252, 'x': 0.117, 'g': 0, 'b': 0.0298, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '25'},
        {'fromNode': '15.0', 'toNode': '19.0', 'r': 0.012, 'x': 0.0394, 'g': 0, 'b': 0.0101, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '26'},
        {'fromNode': '20.0', 'toNode': '21.0', 'r': 0.0183, 'x': 0.0849, 'g': 0, 'b': 0.0216, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '27'},
        {'fromNode': '21.0', 'toNode': '22.0', 'r': 0.0209, 'x': 0.097, 'g': 0, 'b': 0.0246, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '28'},
        {'fromNode': '22.0', 'toNode': '23.0', 'r': 0.0342, 'x': 0.159, 'g': 0, 'b': 0.0404, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '29'},
        {'fromNode': '23.0', 'toNode': '24.0', 'r': 0.0135, 'x': 0.0492, 'g': 0, 'b': 0.0498, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '30'},
        {'fromNode': '23.0', 'toNode': '25.0', 'r': 0.0156, 'x': 0.08, 'g': 0, 'b': 0.0864, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '31'},
        {'fromNode': '26.0', 'toNode': '25.0', 'r': 0.0, 'x': 0.0382, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '32'},
        {'fromNode': '25.0', 'toNode': '27.0', 'r': 0.0318, 'x': 0.163, 'g': 0, 'b': 0.1764, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '33'},
        {'fromNode': '27.0', 'toNode': '28.0', 'r': 0.01913, 'x': 0.0855, 'g': 0, 'b': 0.0216, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '34'},
        {'fromNode': '28.0', 'toNode': '29.0', 'r': 0.0237, 'x': 0.0943, 'g': 0, 'b': 0.0238, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '35'},
        {'fromNode': '30.0', 'toNode': '17.0', 'r': 0.0, 'x': 0.0388, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '36'},
        {'fromNode': '8.0', 'toNode': '30.0', 'r': 0.00431, 'x': 0.0504, 'g': 0, 'b': 0.514, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '37'},
        {'fromNode': '26.0', 'toNode': '30.0', 'r': 0.00799, 'x': 0.086, 'g': 0, 'b': 0.908, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '38'},
        {'fromNode': '17.0', 'toNode': '31.0', 'r': 0.0474, 'x': 0.1563, 'g': 0, 'b': 0.0399, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '39'},
        {'fromNode': '29.0', 'toNode': '31.0', 'r': 0.0108, 'x': 0.0331, 'g': 0, 'b': 0.0083, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '40'},
        {'fromNode': '23.0', 'toNode': '32.0', 'r': 0.0317, 'x': 0.1153, 'g': 0, 'b': 0.1173, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '41'},
        {'fromNode': '31.0', 'toNode': '32.0', 'r': 0.0298, 'x': 0.0985, 'g': 0, 'b': 0.0251, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '42'},
        {'fromNode': '27.0', 'toNode': '32.0', 'r': 0.0229, 'x': 0.0755, 'g': 0, 'b': 0.01926, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '43'},
        {'fromNode': '15.0', 'toNode': '33.0', 'r': 0.038, 'x': 0.1244, 'g': 0, 'b': 0.03194, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '44'},
        {'fromNode': '19.0', 'toNode': '34.0', 'r': 0.0752, 'x': 0.247, 'g': 0, 'b': 0.0632, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '45'},
        {'fromNode': '35.0', 'toNode': '36.0', 'r': 0.00224, 'x': 0.0102, 'g': 0, 'b': 0.00268, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '46'},
        {'fromNode': '35.0', 'toNode': '37.0', 'r': 0.011, 'x': 0.0497, 'g': 0, 'b': 0.01318, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '47'},
        {'fromNode': '33.0', 'toNode': '37.0', 'r': 0.0415, 'x': 0.142, 'g': 0, 'b': 0.0366, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '48'},
        {'fromNode': '34.0', 'toNode': '36.0', 'r': 0.00871, 'x': 0.0268, 'g': 0, 'b': 0.00568, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '49'},
        {'fromNode': '34.0', 'toNode': '37.0', 'r': 0.00256, 'x': 0.0094, 'g': 0, 'b': 0.00984, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '50'},
        {'fromNode': '38.0', 'toNode': '37.0', 'r': 0.0, 'x': 0.0375, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '51'},
        {'fromNode': '37.0', 'toNode': '39.0', 'r': 0.0321, 'x': 0.106, 'g': 0, 'b': 0.027, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '52'},
        {'fromNode': '37.0', 'toNode': '40.0', 'r': 0.0593, 'x': 0.168, 'g': 0, 'b': 0.042, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '53'},
        {'fromNode': '30.0', 'toNode': '38.0', 'r': 0.00464, 'x': 0.054, 'g': 0, 'b': 0.422, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '54'},
        {'fromNode': '39.0', 'toNode': '40.0', 'r': 0.0184, 'x': 0.0605, 'g': 0, 'b': 0.01552, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '55'},
        {'fromNode': '40.0', 'toNode': '41.0', 'r': 0.0145, 'x': 0.0487, 'g': 0, 'b': 0.01222, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '56'},
        {'fromNode': '40.0', 'toNode': '42.0', 'r': 0.0555, 'x': 0.183, 'g': 0, 'b': 0.0466, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '57'},
        {'fromNode': '41.0', 'toNode': '42.0', 'r': 0.041, 'x': 0.135, 'g': 0, 'b': 0.0344, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '58'},
        {'fromNode': '43.0', 'toNode': '44.0', 'r': 0.0608, 'x': 0.2454, 'g': 0, 'b': 0.06068, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '59'},
        {'fromNode': '34.0', 'toNode': '43.0', 'r': 0.0413, 'x': 0.1681, 'g': 0, 'b': 0.04226, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '60'},
        {'fromNode': '44.0', 'toNode': '45.0', 'r': 0.0224, 'x': 0.0901, 'g': 0, 'b': 0.0224, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '61'},
        {'fromNode': '45.0', 'toNode': '46.0', 'r': 0.04, 'x': 0.1356, 'g': 0, 'b': 0.0332, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '62'},
        {'fromNode': '46.0', 'toNode': '47.0', 'r': 0.038, 'x': 0.127, 'g': 0, 'b': 0.0316, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '63'},
        {'fromNode': '46.0', 'toNode': '48.0', 'r': 0.0601, 'x': 0.189, 'g': 0, 'b': 0.0472, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '64'},
        {'fromNode': '47.0', 'toNode': '49.0', 'r': 0.0191, 'x': 0.0625, 'g': 0, 'b': 0.01604, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '65'},
        {'fromNode': '42.0', 'toNode': '49.0', 'r': 0.0715, 'x': 0.323, 'g': 0, 'b': 0.086, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '66'},
        {'fromNode': '42.0', 'toNode': '49.0', 'r': 0.0715, 'x': 0.323, 'g': 0, 'b': 0.086, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '67'},
        {'fromNode': '45.0', 'toNode': '49.0', 'r': 0.0684, 'x': 0.186, 'g': 0, 'b': 0.0444, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '68'},
        {'fromNode': '48.0', 'toNode': '49.0', 'r': 0.0179, 'x': 0.0505, 'g': 0, 'b': 0.01258, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '69'},
        {'fromNode': '49.0', 'toNode': '50.0', 'r': 0.0267, 'x': 0.0752, 'g': 0, 'b': 0.01874, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '70'},
        {'fromNode': '49.0', 'toNode': '51.0', 'r': 0.0486, 'x': 0.137, 'g': 0, 'b': 0.0342, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '71'},
        {'fromNode': '51.0', 'toNode': '52.0', 'r': 0.0203, 'x': 0.0588, 'g': 0, 'b': 0.01396, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '72'},
        {'fromNode': '52.0', 'toNode': '53.0', 'r': 0.0405, 'x': 0.1635, 'g': 0, 'b': 0.04058, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '73'},
        {'fromNode': '53.0', 'toNode': '54.0', 'r': 0.0263, 'x': 0.122, 'g': 0, 'b': 0.031, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '74'},
        {'fromNode': '49.0', 'toNode': '54.0', 'r': 0.073, 'x': 0.289, 'g': 0, 'b': 0.0738, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '75'},
        {'fromNode': '49.0', 'toNode': '54.0', 'r': 0.0869, 'x': 0.291, 'g': 0, 'b': 0.073, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '76'},
        {'fromNode': '54.0', 'toNode': '55.0', 'r': 0.0169, 'x': 0.0707, 'g': 0, 'b': 0.0202, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '77'},
        {'fromNode': '54.0', 'toNode': '56.0', 'r': 0.00275, 'x': 0.00955, 'g': 0, 'b': 0.00732, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '78'},
        {'fromNode': '55.0', 'toNode': '56.0', 'r': 0.00488, 'x': 0.0151, 'g': 0, 'b': 0.00374, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '79'},
        {'fromNode': '56.0', 'toNode': '57.0', 'r': 0.0343, 'x': 0.0966, 'g': 0, 'b': 0.0242, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '80'},
        {'fromNode': '50.0', 'toNode': '57.0', 'r': 0.0474, 'x': 0.134, 'g': 0, 'b': 0.0332, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '81'},
        {'fromNode': '56.0', 'toNode': '58.0', 'r': 0.0343, 'x': 0.0966, 'g': 0, 'b': 0.0242, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '82'},
        {'fromNode': '51.0', 'toNode': '58.0', 'r': 0.0255, 'x': 0.0719, 'g': 0, 'b': 0.01788, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '83'},
        {'fromNode': '54.0', 'toNode': '59.0', 'r': 0.0503, 'x': 0.2293, 'g': 0, 'b': 0.0598, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '84'},
        {'fromNode': '56.0', 'toNode': '59.0', 'r': 0.0825, 'x': 0.251, 'g': 0, 'b': 0.0569, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '85'},
        {'fromNode': '56.0', 'toNode': '59.0', 'r': 0.0803, 'x': 0.239, 'g': 0, 'b': 0.0536, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '86'},
        {'fromNode': '55.0', 'toNode': '59.0', 'r': 0.04739, 'x': 0.2158, 'g': 0, 'b': 0.05646, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '87'},
        {'fromNode': '59.0', 'toNode': '60.0', 'r': 0.0317, 'x': 0.145, 'g': 0, 'b': 0.0376, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '88'},
        {'fromNode': '59.0', 'toNode': '61.0', 'r': 0.0328, 'x': 0.15, 'g': 0, 'b': 0.0388, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '89'},
        {'fromNode': '60.0', 'toNode': '61.0', 'r': 0.00264, 'x': 0.0135, 'g': 0, 'b': 0.01456, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '90'},
        {'fromNode': '60.0', 'toNode': '62.0', 'r': 0.0123, 'x': 0.0561, 'g': 0, 'b': 0.01468, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '91'},
        {'fromNode': '61.0', 'toNode': '62.0', 'r': 0.00824, 'x': 0.0376, 'g': 0, 'b': 0.0098, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '92'},
        {'fromNode': '63.0', 'toNode': '59.0', 'r': 0.0, 'x': 0.0386, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '93'},
        {'fromNode': '63.0', 'toNode': '64.0', 'r': 0.00172, 'x': 0.02, 'g': 0, 'b': 0.216, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '94'},
        {'fromNode': '64.0', 'toNode': '61.0', 'r': 0.0, 'x': 0.0268, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.985, 'shift': 0.0, 'Line_id': '95'},
        {'fromNode': '38.0', 'toNode': '65.0', 'r': 0.00901, 'x': 0.0986, 'g': 0, 'b': 1.046, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '96'},
        {'fromNode': '64.0', 'toNode': '65.0', 'r': 0.00269, 'x': 0.0302, 'g': 0, 'b': 0.38, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '97'},
        {'fromNode': '49.0', 'toNode': '66.0', 'r': 0.018, 'x': 0.0919, 'g': 0, 'b': 0.0248, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '98'},
        {'fromNode': '49.0', 'toNode': '66.0', 'r': 0.018, 'x': 0.0919, 'g': 0, 'b': 0.0248, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '99'},
        {'fromNode': '62.0', 'toNode': '66.0', 'r': 0.0482, 'x': 0.218, 'g': 0, 'b': 0.0578, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '100'},
        {'fromNode': '62.0', 'toNode': '67.0', 'r': 0.0258, 'x': 0.117, 'g': 0, 'b': 0.031, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '101'},
        {'fromNode': '65.0', 'toNode': '66.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '102'},
        {'fromNode': '66.0', 'toNode': '67.0', 'r': 0.0224, 'x': 0.1015, 'g': 0, 'b': 0.02682, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '103'},
        {'fromNode': '65.0', 'toNode': '68.0', 'r': 0.00138, 'x': 0.016, 'g': 0, 'b': 0.638, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '104'},
        {'fromNode': '47.0', 'toNode': '69.0', 'r': 0.0844, 'x': 0.2778, 'g': 0, 'b': 0.07092, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '105'},
        {'fromNode': '49.0', 'toNode': '69.0', 'r': 0.0985, 'x': 0.324, 'g': 0, 'b': 0.0828, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '106'},
        {'fromNode': '68.0', 'toNode': '69.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '107'},
        {'fromNode': '69.0', 'toNode': '70.0', 'r': 0.03, 'x': 0.127, 'g': 0, 'b': 0.122, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '108'},
        {'fromNode': '24.0', 'toNode': '70.0', 'r': 0.00221, 'x': 0.4115, 'g': 0, 'b': 0.10198, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '109'},
        {'fromNode': '70.0', 'toNode': '71.0', 'r': 0.00882, 'x': 0.0355, 'g': 0, 'b': 0.00878, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '110'},
        {'fromNode': '24.0', 'toNode': '72.0', 'r': 0.0488, 'x': 0.196, 'g': 0, 'b': 0.0488, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '111'},
        {'fromNode': '71.0', 'toNode': '72.0', 'r': 0.0446, 'x': 0.18, 'g': 0, 'b': 0.04444, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '112'},
        {'fromNode': '71.0', 'toNode': '73.0', 'r': 0.00866, 'x': 0.0454, 'g': 0, 'b': 0.01178, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '113'},
        {'fromNode': '70.0', 'toNode': '74.0', 'r': 0.0401, 'x': 0.1323, 'g': 0, 'b': 0.03368, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '114'},
        {'fromNode': '70.0', 'toNode': '75.0', 'r': 0.0428, 'x': 0.141, 'g': 0, 'b': 0.036, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '115'},
        {'fromNode': '69.0', 'toNode': '75.0', 'r': 0.0405, 'x': 0.122, 'g': 0, 'b': 0.124, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '116'},
        {'fromNode': '74.0', 'toNode': '75.0', 'r': 0.0123, 'x': 0.0406, 'g': 0, 'b': 0.01034, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '117'},
        {'fromNode': '76.0', 'toNode': '77.0', 'r': 0.0444, 'x': 0.148, 'g': 0, 'b': 0.0368, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '118'},
        {'fromNode': '69.0', 'toNode': '77.0', 'r': 0.0309, 'x': 0.101, 'g': 0, 'b': 0.1038, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '119'},
        {'fromNode': '75.0', 'toNode': '77.0', 'r': 0.0601, 'x': 0.1999, 'g': 0, 'b': 0.04978, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '120'},
        {'fromNode': '77.0', 'toNode': '78.0', 'r': 0.00376, 'x': 0.0124, 'g': 0, 'b': 0.01264, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '121'},
        {'fromNode': '78.0', 'toNode': '79.0', 'r': 0.00546, 'x': 0.0244, 'g': 0, 'b': 0.00648, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '122'},
        {'fromNode': '77.0', 'toNode': '80.0', 'r': 0.017, 'x': 0.0485, 'g': 0, 'b': 0.0472, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '123'},
        {'fromNode': '77.0', 'toNode': '80.0', 'r': 0.0294, 'x': 0.105, 'g': 0, 'b': 0.0228, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '124'},
        {'fromNode': '79.0', 'toNode': '80.0', 'r': 0.0156, 'x': 0.0704, 'g': 0, 'b': 0.0187, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '125'},
        {'fromNode': '68.0', 'toNode': '81.0', 'r': 0.00175, 'x': 0.0202, 'g': 0, 'b': 0.808, 'MVA_rating': 9999, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '126'},
        {'fromNode': '81.0', 'toNode': '80.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '127'},
        {'fromNode': '77.0', 'toNode': '82.0', 'r': 0.0298, 'x': 0.0853, 'g': 0, 'b': 0.08174, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '128'},
        {'fromNode': '82.0', 'toNode': '83.0', 'r': 0.0112, 'x': 0.03665, 'g': 0, 'b': 0.03796, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '129'},
        {'fromNode': '83.0', 'toNode': '84.0', 'r': 0.0625, 'x': 0.132, 'g': 0, 'b': 0.0258, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '130'},
        {'fromNode': '83.0', 'toNode': '85.0', 'r': 0.043, 'x': 0.148, 'g': 0, 'b': 0.0348, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '131'},
        {'fromNode': '84.0', 'toNode': '85.0', 'r': 0.0302, 'x': 0.0641, 'g': 0, 'b': 0.01234, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '132'},
        {'fromNode': '85.0', 'toNode': '86.0', 'r': 0.035, 'x': 0.123, 'g': 0, 'b': 0.0276, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '133'},
        {'fromNode': '86.0', 'toNode': '87.0', 'r': 0.02828, 'x': 0.2074, 'g': 0, 'b': 0.0445, 'MVA_rating': 9999, 'kV_base': 161.0, 'm': 1.0, 'shift': 0.0, 'Line_id': '134'},
        {'fromNode': '85.0', 'toNode': '88.0', 'r': 0.02, 'x': 0.102, 'g': 0, 'b': 0.0276, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '135'},
        {'fromNode': '85.0', 'toNode': '89.0', 'r': 0.0239, 'x': 0.173, 'g': 0, 'b': 0.047, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '136'},
        {'fromNode': '88.0', 'toNode': '89.0', 'r': 0.0139, 'x': 0.0712, 'g': 0, 'b': 0.01934, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '137'},
        {'fromNode': '89.0', 'toNode': '90.0', 'r': 0.0518, 'x': 0.188, 'g': 0, 'b': 0.0528, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '138'},
        {'fromNode': '89.0', 'toNode': '90.0', 'r': 0.0238, 'x': 0.0997, 'g': 0, 'b': 0.106, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '139'},
        {'fromNode': '90.0', 'toNode': '91.0', 'r': 0.0254, 'x': 0.0836, 'g': 0, 'b': 0.0214, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '140'},
        {'fromNode': '89.0', 'toNode': '92.0', 'r': 0.0099, 'x': 0.0505, 'g': 0, 'b': 0.0548, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '141'},
        {'fromNode': '89.0', 'toNode': '92.0', 'r': 0.0393, 'x': 0.1581, 'g': 0, 'b': 0.0414, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '142'},
        {'fromNode': '91.0', 'toNode': '92.0', 'r': 0.0387, 'x': 0.1272, 'g': 0, 'b': 0.03268, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '143'},
        {'fromNode': '92.0', 'toNode': '93.0', 'r': 0.0258, 'x': 0.0848, 'g': 0, 'b': 0.0218, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '144'},
        {'fromNode': '92.0', 'toNode': '94.0', 'r': 0.0481, 'x': 0.158, 'g': 0, 'b': 0.0406, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '145'},
        {'fromNode': '93.0', 'toNode': '94.0', 'r': 0.0223, 'x': 0.0732, 'g': 0, 'b': 0.01876, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '146'},
        {'fromNode': '94.0', 'toNode': '95.0', 'r': 0.0132, 'x': 0.0434, 'g': 0, 'b': 0.0111, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '147'},
        {'fromNode': '80.0', 'toNode': '96.0', 'r': 0.0356, 'x': 0.182, 'g': 0, 'b': 0.0494, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '148'},
        {'fromNode': '82.0', 'toNode': '96.0', 'r': 0.0162, 'x': 0.053, 'g': 0, 'b': 0.0544, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '149'},
        {'fromNode': '94.0', 'toNode': '96.0', 'r': 0.0269, 'x': 0.0869, 'g': 0, 'b': 0.023, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '150'},
        {'fromNode': '80.0', 'toNode': '97.0', 'r': 0.0183, 'x': 0.0934, 'g': 0, 'b': 0.0254, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '151'},
        {'fromNode': '80.0', 'toNode': '98.0', 'r': 0.0238, 'x': 0.108, 'g': 0, 'b': 0.0286, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '152'},
        {'fromNode': '80.0', 'toNode': '99.0', 'r': 0.0454, 'x': 0.206, 'g': 0, 'b': 0.0546, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '153'},
        {'fromNode': '92.0', 'toNode': '100.0', 'r': 0.0648, 'x': 0.295, 'g': 0, 'b': 0.0472, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '154'},
        {'fromNode': '94.0', 'toNode': '100.0', 'r': 0.0178, 'x': 0.058, 'g': 0, 'b': 0.0604, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '155'},
        {'fromNode': '95.0', 'toNode': '96.0', 'r': 0.0171, 'x': 0.0547, 'g': 0, 'b': 0.01474, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '156'},
        {'fromNode': '96.0', 'toNode': '97.0', 'r': 0.0173, 'x': 0.0885, 'g': 0, 'b': 0.024, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '157'},
        {'fromNode': '98.0', 'toNode': '100.0', 'r': 0.0397, 'x': 0.179, 'g': 0, 'b': 0.0476, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '158'},
        {'fromNode': '99.0', 'toNode': '100.0', 'r': 0.018, 'x': 0.0813, 'g': 0, 'b': 0.0216, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '159'},
        {'fromNode': '100.0', 'toNode': '101.0', 'r': 0.0277, 'x': 0.1262, 'g': 0, 'b': 0.0328, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '160'},
        {'fromNode': '92.0', 'toNode': '102.0', 'r': 0.0123, 'x': 0.0559, 'g': 0, 'b': 0.01464, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '161'},
        {'fromNode': '101.0', 'toNode': '102.0', 'r': 0.0246, 'x': 0.112, 'g': 0, 'b': 0.0294, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '162'},
        {'fromNode': '100.0', 'toNode': '103.0', 'r': 0.016, 'x': 0.0525, 'g': 0, 'b': 0.0536, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '163'},
        {'fromNode': '100.0', 'toNode': '104.0', 'r': 0.0451, 'x': 0.204, 'g': 0, 'b': 0.0541, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '164'},
        {'fromNode': '103.0', 'toNode': '104.0', 'r': 0.0466, 'x': 0.1584, 'g': 0, 'b': 0.0407, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '165'},
        {'fromNode': '103.0', 'toNode': '105.0', 'r': 0.0535, 'x': 0.1625, 'g': 0, 'b': 0.0408, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '166'},
        {'fromNode': '100.0', 'toNode': '106.0', 'r': 0.0605, 'x': 0.229, 'g': 0, 'b': 0.062, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '167'},
        {'fromNode': '104.0', 'toNode': '105.0', 'r': 0.00994, 'x': 0.0378, 'g': 0, 'b': 0.00986, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '168'},
        {'fromNode': '105.0', 'toNode': '106.0', 'r': 0.014, 'x': 0.0547, 'g': 0, 'b': 0.01434, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '169'},
        {'fromNode': '105.0', 'toNode': '107.0', 'r': 0.053, 'x': 0.183, 'g': 0, 'b': 0.0472, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '170'},
        {'fromNode': '105.0', 'toNode': '108.0', 'r': 0.0261, 'x': 0.0703, 'g': 0, 'b': 0.01844, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '171'},
        {'fromNode': '106.0', 'toNode': '107.0', 'r': 0.053, 'x': 0.183, 'g': 0, 'b': 0.0472, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '172'},
        {'fromNode': '108.0', 'toNode': '109.0', 'r': 0.0105, 'x': 0.0288, 'g': 0, 'b': 0.0076, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '173'},
        {'fromNode': '103.0', 'toNode': '110.0', 'r': 0.03906, 'x': 0.1813, 'g': 0, 'b': 0.0461, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '174'},
        {'fromNode': '109.0', 'toNode': '110.0', 'r': 0.0278, 'x': 0.0762, 'g': 0, 'b': 0.0202, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '175'},
        {'fromNode': '110.0', 'toNode': '111.0', 'r': 0.022, 'x': 0.0755, 'g': 0, 'b': 0.02, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '176'},
        {'fromNode': '110.0', 'toNode': '112.0', 'r': 0.0247, 'x': 0.064, 'g': 0, 'b': 0.062, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '177'},
        {'fromNode': '17.0', 'toNode': '113.0', 'r': 0.00913, 'x': 0.0301, 'g': 0, 'b': 0.00768, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '178'},
        {'fromNode': '32.0', 'toNode': '113.0', 'r': 0.0615, 'x': 0.203, 'g': 0, 'b': 0.0518, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '179'},
        {'fromNode': '32.0', 'toNode': '114.0', 'r': 0.0135, 'x': 0.0612, 'g': 0, 'b': 0.01628, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '180'},
        {'fromNode': '27.0', 'toNode': '115.0', 'r': 0.0164, 'x': 0.0741, 'g': 0, 'b': 0.01972, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '181'},
        {'fromNode': '114.0', 'toNode': '115.0', 'r': 0.0023, 'x': 0.0104, 'g': 0, 'b': 0.00276, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '182'},
        {'fromNode': '68.0', 'toNode': '116.0', 'r': 0.00034, 'x': 0.00405, 'g': 0, 'b': 0.164, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1.0, 'shift': 0.0, 'Line_id': '183'},
        {'fromNode': '12.0', 'toNode': '117.0', 'r': 0.0329, 'x': 0.14, 'g': 0, 'b': 0.0358, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '184'},
        {'fromNode': '75.0', 'toNode': '118.0', 'r': 0.0145, 'x': 0.0481, 'g': 0, 'b': 0.01198, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '185'},
        {'fromNode': '76.0', 'toNode': '118.0', 'r': 0.0164, 'x': 0.0544, 'g': 0, 'b': 0.01356, 'MVA_rating': 9999, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '186'}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'case118'
    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    
    # Add Generators
    pyf.add_gen(grid, '1.0', '1', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-5.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '4.0', '2', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '6.0', '3', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-13.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '8.0', '4', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '10.0', '5', price_zone_link=False, lf=20.0, qf=0.0222222222, MWmax=550.0, MWmin=0.0, MVArmax=200.0, MVArmin=-147.0, PsetMW=450.0, QsetMVA=0.0)
    pyf.add_gen(grid, '12.0', '6', price_zone_link=False, lf=20.0, qf=0.117647059, MWmax=185.0, MWmin=0.0, MVArmax=120.0, MVArmin=-35.0, PsetMW=85.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15.0', '7', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=30.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '18.0', '8', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-16.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '19.0', '9', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '24.0', '10', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '25.0', '11', price_zone_link=False, lf=20.0, qf=0.0454545455, MWmax=320.0, MWmin=0.0, MVArmax=140.0, MVArmin=-47.0, PsetMW=220.00000000000003, QsetMVA=0.0)
    pyf.add_gen(grid, '26.0', '12', price_zone_link=False, lf=20.0, qf=0.0318471338, MWmax=413.99999999999994, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=314.0, QsetMVA=0.0)
    pyf.add_gen(grid, '27.0', '13', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '31.0', '14', price_zone_link=False, lf=20.0, qf=1.42857143, MWmax=107.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=7.000000000000001, QsetMVA=0.0)
    pyf.add_gen(grid, '32.0', '15', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=42.0, MVArmin=-14.000000000000002, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '34.0', '16', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '36.0', '17', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '40.0', '18', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '42.0', '19', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '46.0', '20', price_zone_link=False, lf=20.0, qf=0.526315789, MWmax=119.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=19.0, QsetMVA=0.0)
    pyf.add_gen(grid, '49.0', '21', price_zone_link=False, lf=20.0, qf=0.0490196078, MWmax=304.0, MWmin=0.0, MVArmax=210.0, MVArmin=-85.0, PsetMW=204.0, QsetMVA=0.0)
    pyf.add_gen(grid, '54.0', '22', price_zone_link=False, lf=20.0, qf=0.208333333, MWmax=148.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=48.0, QsetMVA=0.0)
    pyf.add_gen(grid, '55.0', '23', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '56.0', '24', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '59.0', '25', price_zone_link=False, lf=20.0, qf=0.064516129, MWmax=254.99999999999997, MWmin=0.0, MVArmax=180.0, MVArmin=-60.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '61.0', '26', price_zone_link=False, lf=20.0, qf=0.0625, MWmax=260.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=160.0, QsetMVA=0.0)
    pyf.add_gen(grid, '62.0', '27', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=20.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '65.0', '28', price_zone_link=False, lf=20.0, qf=0.0255754476, MWmax=491.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=391.0, QsetMVA=0.0)
    pyf.add_gen(grid, '66.0', '29', price_zone_link=False, lf=20.0, qf=0.0255102041, MWmax=492.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=392.0, QsetMVA=0.0)
    pyf.add_gen(grid, '69.0', '30', price_zone_link=False, lf=20.0, qf=0.0193648335, MWmax=805.1999999999999, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=516.4, QsetMVA=0.0)
    pyf.add_gen(grid, '70.0', '31', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=32.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '72.0', '32', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '73.0', '33', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '74.0', '34', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-6.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '76.0', '35', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '77.0', '36', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=70.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '80.0', '37', price_zone_link=False, lf=20.0, qf=0.0209643606, MWmax=577.0, MWmin=0.0, MVArmax=280.0, MVArmin=-165.0, PsetMW=476.99999999999994, QsetMVA=0.0)
    pyf.add_gen(grid, '85.0', '38', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '87.0', '39', price_zone_link=False, lf=20.0, qf=2.5, MWmax=104.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=4.0, QsetMVA=0.0)
    pyf.add_gen(grid, '89.0', '40', price_zone_link=False, lf=20.0, qf=0.0164744646, MWmax=707.0, MWmin=0.0, MVArmax=300.0, MVArmin=-210.0, PsetMW=607.0, QsetMVA=0.0)
    pyf.add_gen(grid, '90.0', '41', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '91.0', '42', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '92.0', '43', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-3.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '99.0', '44', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '100.0', '45', price_zone_link=False, lf=20.0, qf=0.0396825397, MWmax=352.0, MWmin=0.0, MVArmax=155.0, MVArmin=-50.0, PsetMW=252.0, QsetMVA=0.0)
    pyf.add_gen(grid, '103.0', '46', price_zone_link=False, lf=20.0, qf=0.25, MWmax=140.0, MWmin=0.0, MVArmax=40.0, MVArmin=-15.0, PsetMW=40.0, QsetMVA=0.0)
    pyf.add_gen(grid, '104.0', '47', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '105.0', '48', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '107.0', '49', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-200.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '110.0', '50', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '111.0', '51', price_zone_link=False, lf=20.0, qf=0.277777778, MWmax=136.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=36.0, QsetMVA=0.0)
    pyf.add_gen(grid, '112.0', '52', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '113.0', '53', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '116.0', '54', price_zone_link=False, lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=0.0, QsetMVA=0.0)
    
    
    # Add Renewable Source Zones

    
    # Add Renewable Sources

    
    # Return the grid
    return grid,res
