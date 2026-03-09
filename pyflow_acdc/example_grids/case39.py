

import pyflow_acdc as pyf
import pandas as pd
"""
Converted to PyFlowACDC format from

%CASE39 Power flow data for 39 bus New England system.
%   Please see CASEFORMAT for details on the case file format.
%
%   Data taken from [1] with the following modifications/additions:
%
%       - renumbered gen buses consecutively (as in [2] and [4])
%       - added Pmin = 0 for all gens
%       - added Qmin, Qmax for gens at 31 & 39 (copied from gen at 35)
%       - added Vg based on V in bus data (missing for bus 39)
%       - added Vg, Pg, Pd, Qd at bus 39 from [2] (same in [4])
%       - added Pmax at bus 39: Pmax = Pg + 100
%       - added line flow limits and area data from [4]
%       - added voltage limits, Vmax = 1.06, Vmin = 0.94
%       - added identical quadratic generator costs
%       - increased Pmax for gen at bus 34 from 308 to 508
%         (assumed typo in [1], makes initial solved case feasible)
%       - re-solved power flow
% 
%   Notes:
%       - Bus 39, its generator and 2 connecting lines were added
%         (by authors of [1]) to represent the interconnection with
%         the rest of the eastern interconnect, and did not include
%         Vg, Pg, Qg, Pd, Qd, Pmin, Pmax, Qmin or Qmax.
%       - As the swing bus, bus 31 did not include and Q limits.
%       - The voltages, etc in [1] appear to be quite close to the
%         power flow solution of the case before adding bus 39 with
%         it's generator and connecting branches, though the solution
%         is not exact.
%       - Explicit voltage setpoints for gen buses are not given, so
%         they are taken from the bus data, however this results in two
%         binding Q limits at buses 34 & 37, so the corresponding
%         voltages have probably deviated from their original setpoints.
%       - The generator locations and types are as follows:
%           1   30      hydro
%           2   31      nuke01
%           3   32      nuke02
%           4   33      fossil02
%           5   34      fossil01
%           6   35      nuke03
%           7   36      fossil04
%           8   37      nuke04
%           9   38      nuke05
%           10  39      interconnection to rest of US/Canada
%
%   This is a solved power flow case, but it includes the following
%   violations:
%       - Pmax violated at bus 31: Pg = 677.87, Pmax = 646
%       - Qmin violated at bus 37: Qg = -1.37,  Qmin = 0
%
%   References:
%   [1] G. W. Bills, et.al., "On-Line Stability Analysis Study"
%       RP90-1 Report for the Edison Electric Institute, October 12, 1970,
%       pp. 1-20 - 1-35.
%       prepared by E. M. Gulachenski - New England Electric System
%                   J. M. Undrill     - General Electric Co.
%       "generally representative of the New England 345 KV system, but is
%        not an exact or complete model of any past, present or projected
%        configuration of the actual New England 345 KV system.
%   [2] M. A. Pai, Energy Function Analysis for Power System Stability,
%       Kluwer Academic Publishers, Boston, 1989.
%       (references [3] as source of data)
%   [3] Athay, T.; Podmore, R.; Virmani, S., "A Practical Method for the
%       Direct Analysis of Transient Stability," IEEE Transactions on Power
%       Apparatus and Systems , vol.PAS-98, no.2, pp.573-584, March 1979.
%       URL: https://doi.org/10.1109/TPAS.1979.319407
%       (references [1] as source of data)
%   [4] Data included with TC Calculator at http://www.pserc.cornell.edu/tcc/
%       for 39-bus system.

%   MATPOWER

"""

def case39(TEP=False,exp='All',N_b=1,N_i=1,N_max=5,Increase=1,kappa=0.5):       
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
    {'Node_id': '1', 'type': 'PQ', 'Voltage_0': 1.0393836, 'theta_0': -0.236258274, 'kV_base': 345.0, 'Power_load': 0.976, 'Reactive_load': 0.442, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 48.252033, 'y_coord': -0.63953},
    {'Node_id': '2', 'type': 'PQ', 'Voltage_0': 1.0484941, 'theta_0': -0.17078512, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 55.92495, 'y_coord': 4.916718},
    {'Node_id': '3', 'type': 'PQ', 'Voltage_0': 1.0307077, 'theta_0': -0.214263321, 'kV_base': 345.0, 'Power_load': 3.22, 'Reactive_load': 0.024, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 62.804115, 'y_coord': -6.72495},
    {'Node_id': '4', 'type': 'PQ', 'Voltage_0': 1.00446, 'theta_0': -0.220378082, 'kV_base': 345.0, 'Power_load': 5.0, 'Reactive_load': 1.84, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 62.804115, 'y_coord': -32.9187},
    {'Node_id': '5', 'type': 'PQ', 'Voltage_0': 1.0060063, 'theta_0': -0.195343167, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 58.041615, 'y_coord': -43.50203},
    {'Node_id': '6', 'type': 'PQ', 'Voltage_0': 1.0082256, 'theta_0': -0.181659628, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 70.741615, 'y_coord': -49.05827},
    {'Node_id': '7', 'type': 'PQ', 'Voltage_0': 0.99839728, 'theta_0': -0.222627672, 'kV_base': 345.0, 'Power_load': 2.338, 'Reactive_load': 0.84, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 62.804115, 'y_coord': -55.14369},
    {'Node_id': '8', 'type': 'PQ', 'Voltage_0': 0.99787232, 'theta_0': -0.232754386, 'kV_base': 345.0, 'Power_load': 5.22, 'Reactive_load': 1.766, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 54.866615, 'y_coord': -68.10828},
    {'Node_id': '9', 'type': 'PQ', 'Voltage_0': 1.038332, 'theta_0': -0.247460496, 'kV_base': 345.0, 'Power_load': 0.065, 'Reactive_load': -0.666, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 48.252033, 'y_coord': -49.05827},
    {'Node_id': '10', 'type': 'PQ', 'Voltage_0': 1.0178431, 'theta_0': -0.142608672, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 91.379112, 'y_coord': -62.28745},
    {'Node_id': '11', 'type': 'PQ', 'Voltage_0': 1.0133858, 'theta_0': -0.155979487, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 81.324951, 'y_coord': -55.14369},
    {'Node_id': '12', 'type': 'PQ', 'Voltage_0': 1.000815, 'theta_0': -0.157059101, 'kV_base': 345.0, 'Power_load': 0.0853, 'Reactive_load': 0.88, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 91.379112, 'y_coord': -49.05827},
    {'Node_id': '13', 'type': 'PQ', 'Voltage_0': 1.014923, 'theta_0': -0.155856632, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 98.522865, 'y_coord': -43.50203},
    {'Node_id': '14', 'type': 'PQ', 'Voltage_0': 1.012319, 'theta_0': -0.187017178, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 103.02078, 'y_coord': -32.9187},
    {'Node_id': '15', 'type': 'PQ', 'Voltage_0': 1.0161854, 'theta_0': -0.198014568, 'kV_base': 345.0, 'Power_load': 3.2, 'Reactive_load': 1.53, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 107.5187, 'y_coord': -19.16036},
    {'Node_id': '16', 'type': 'PQ', 'Voltage_0': 1.0325203, 'theta_0': -0.175114958, 'kV_base': 345.0, 'Power_load': 3.29, 'Reactive_load': 0.323, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 113.07495, 'y_coord': -13.8687},
    {'Node_id': '17', 'type': 'PQ', 'Voltage_0': 1.0342365, 'theta_0': -0.194018409, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 113.07495, 'y_coord': -6.72495},
    {'Node_id': '18', 'type': 'PQ', 'Voltage_0': 1.0315726, 'theta_0': -0.209198096, 'kV_base': 345.0, 'Power_load': 1.58, 'Reactive_load': 0.3, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 91.379112, 'y_coord': -6.72495},
    {'Node_id': '19', 'type': 'PQ', 'Voltage_0': 1.0501068, 'theta_0': -0.094423585, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 119.16036, 'y_coord': -51.70412},
    {'Node_id': '20', 'type': 'PQ', 'Voltage_0': 0.99101054, 'theta_0': -0.11905202, 'kV_base': 345.0, 'Power_load': 6.8, 'Reactive_load': 1.03, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 113.07495, 'y_coord': -55.14369},
    {'Node_id': '21', 'type': 'PQ', 'Voltage_0': 1.0323192, 'theta_0': -0.133146737, 'kV_base': 345.0, 'Power_load': 2.74, 'Reactive_load': 1.15, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 146.94162, 'y_coord': -13.8687},
    {'Node_id': '22', 'type': 'PQ', 'Voltage_0': 1.0501427, 'theta_0': -0.055555923, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 144.29578, 'y_coord': -55.14369},
    {'Node_id': '23', 'type': 'PQ', 'Voltage_0': 1.0451451, 'theta_0': -0.059014404, 'kV_base': 345.0, 'Power_load': 2.475, 'Reactive_load': 0.846, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 130.80203, 'y_coord': -43.50203},
    {'Node_id': '24', 'type': 'PQ', 'Voltage_0': 1.038001, 'theta_0': -0.173027727, 'kV_base': 345.0, 'Power_load': 3.086, 'Reactive_load': -0.922, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 120.74786, 'y_coord': -32.9187},
    {'Node_id': '25', 'type': 'PQ', 'Voltage_0': 1.0576827, 'theta_0': -0.146070714, 'kV_base': 345.0, 'Power_load': 2.24, 'Reactive_load': 0.472, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 67.8312, 'y_coord': 12.32505},
    {'Node_id': '26', 'type': 'PQ', 'Voltage_0': 1.0525613, 'theta_0': -0.164737607, 'kV_base': 345.0, 'Power_load': 1.39, 'Reactive_load': 0.17, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 107.5187, 'y_coord': 12.32505},
    {'Node_id': '27', 'type': 'PQ', 'Voltage_0': 1.0383449, 'theta_0': -0.198306963, 'kV_base': 345.0, 'Power_load': 2.81, 'Reactive_load': 0.755, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 113.07495, 'y_coord': 4.916718},
    {'Node_id': '28', 'type': 'PQ', 'Voltage_0': 1.0503737, 'theta_0': -0.103469387, 'kV_base': 345.0, 'Power_load': 2.06, 'Reactive_load': 0.276, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 130.00829, 'y_coord': 12.32505},
    {'Node_id': '29', 'type': 'PQ', 'Voltage_0': 1.0501149, 'theta_0': -0.05532474, 'kV_base': 345.0, 'Power_load': 2.835, 'Reactive_load': 0.269, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 146.94162, 'y_coord': 12.32505},
    {'Node_id': '30', 'type': 'PV', 'Voltage_0': 1.0499, 'theta_0': -0.128639049, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 48.252033, 'y_coord': 16.558388},
    {'Node_id': '31', 'type': 'Slack', 'Voltage_0': 0.982, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_load': 0.092, 'Reactive_load': 0.046, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 75.7687, 'y_coord': -68.10828},
    {'Node_id': '32', 'type': 'PV', 'Voltage_0': 0.9841, 'theta_0': -0.003288853, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 91.379112, 'y_coord': -68.10828},
    {'Node_id': '33', 'type': 'PV', 'Voltage_0': 0.9972, 'theta_0': -0.00337153, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 123.92287, 'y_coord': -68.10828},
    {'Node_id': '34', 'type': 'PV', 'Voltage_0': 1.0123, 'theta_0': -0.028468397, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 113.07495, 'y_coord': -68.10828},
    {'Node_id': '35', 'type': 'PV', 'Voltage_0': 1.0494, 'theta_0': 0.031005895, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 144.29578, 'y_coord': -68.10828},
    {'Node_id': '36', 'type': 'PV', 'Voltage_0': 1.0636, 'theta_0': 0.077988945, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 138.47495, 'y_coord': -32.9187},
    {'Node_id': '37', 'type': 'PV', 'Voltage_0': 1.0275, 'theta_0': -0.027626796, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 67.8312, 'y_coord': 16.558388},
    {'Node_id': '38', 'type': 'PV', 'Voltage_0': 1.0265, 'theta_0': 0.067942486, 'kV_base': 345.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 146.94162, 'y_coord': -0.63953},
    {'Node_id': '39', 'type': 'PV', 'Voltage_0': 1.03, 'theta_0': -0.253688075, 'kV_base': 345.0, 'Power_load': 11.04, 'Reactive_load': 2.5, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': 48.252033, 'y_coord': -13.8687}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
    {'Line_id': 'L_AC1', 'fromNode': '1', 'toNode': '2', 'r': 0.0035, 'x': 0.0411, 'g': 0.0, 'b': 0.6987, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.37},
    {'Line_id': 'L_AC2', 'fromNode': '1', 'toNode': '39', 'r': 0.001, 'x': 0.025, 'g': 0.0, 'b': 0.75, 'MVA_rating': 1000.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.51},
    {'Line_id': 'L_AC3', 'fromNode': '2', 'toNode': '3', 'r': 0.0013, 'x': 0.0151, 'g': 0.0, 'b': 0.2572, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.79},
    {'Line_id': 'L_AC4', 'fromNode': '2', 'toNode': '25', 'r': 0.007, 'x': 0.0086, 'g': 0.0, 'b': 0.146, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.77},
    {'Line_id': 'L_AC5', 'fromNode': '2', 'toNode': '30', 'r': 0.0, 'x': 0.0181, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.025, 'shift': 0.0, 'Cost MEUR': 8.15},
    {'Line_id': 'L_AC6', 'fromNode': '3', 'toNode': '4', 'r': 0.0013, 'x': 0.0213, 'g': 0.0, 'b': 0.2214, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.33},
    {'Line_id': 'L_AC7', 'fromNode': '3', 'toNode': '18', 'r': 0.0011, 'x': 0.0133, 'g': 0.0, 'b': 0.2138, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.34},
    {'Line_id': 'L_AC8', 'fromNode': '4', 'toNode': '5', 'r': 0.0008, 'x': 0.0128, 'g': 0.0, 'b': 0.1342, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.85},
    {'Line_id': 'L_AC9', 'fromNode': '4', 'toNode': '14', 'r': 0.0008, 'x': 0.0129, 'g': 0.0, 'b': 0.1382, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.23},
    {'Line_id': 'L_AC10', 'fromNode': '5', 'toNode': '6', 'r': 0.0002, 'x': 0.0026, 'g': 0.0, 'b': 0.0434, 'MVA_rating': 1200.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.56},
    {'Line_id': 'L_AC11', 'fromNode': '5', 'toNode': '8', 'r': 0.0008, 'x': 0.0112, 'g': 0.0, 'b': 0.1476, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.05},
    {'Line_id': 'L_AC12', 'fromNode': '6', 'toNode': '7', 'r': 0.0006, 'x': 0.0092, 'g': 0.0, 'b': 0.113, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.15},
    {'Line_id': 'L_AC13', 'fromNode': '6', 'toNode': '11', 'r': 0.0007, 'x': 0.0082, 'g': 0.0, 'b': 0.1389, 'MVA_rating': 480.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.98},
    {'Line_id': 'L_AC14', 'fromNode': '6', 'toNode': '31', 'r': 0.0, 'x': 0.025, 'g': 0.0, 'b': 0.0, 'MVA_rating': 1800.0, 'kV_base': 345.0, 'm': 1.07, 'shift': 0.0, 'Cost MEUR': 22.5},
    {'Line_id': 'L_AC15', 'fromNode': '7', 'toNode': '8', 'r': 0.0004, 'x': 0.0046, 'g': 0.0, 'b': 0.078, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.08},
    {'Line_id': 'L_AC16', 'fromNode': '8', 'toNode': '9', 'r': 0.0023, 'x': 0.0363, 'g': 0.0, 'b': 0.3804, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 16.37},
    {'Line_id': 'L_AC17', 'fromNode': '9', 'toNode': '39', 'r': 0.001, 'x': 0.025, 'g': 0.0, 'b': 1.2, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.26},
    {'Line_id': 'L_AC18', 'fromNode': '10', 'toNode': '11', 'r': 0.0004, 'x': 0.0043, 'g': 0.0, 'b': 0.0729, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.3},
    {'Line_id': 'L_AC19', 'fromNode': '10', 'toNode': '13', 'r': 0.0004, 'x': 0.0043, 'g': 0.0, 'b': 0.0729, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.3},
    {'Line_id': 'L_AC20', 'fromNode': '10', 'toNode': '32', 'r': 0.0, 'x': 0.02, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.07, 'shift': 0.0, 'Cost MEUR': 9.0},
    {'Line_id': 'L_AC21', 'fromNode': '12', 'toNode': '11', 'r': 0.0016, 'x': 0.0435, 'g': 0.0, 'b': 0.0, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.006, 'shift': 0.0, 'Cost MEUR': 10.88},
    {'Line_id': 'L_AC22', 'fromNode': '12', 'toNode': '13', 'r': 0.0016, 'x': 0.0435, 'g': 0.0, 'b': 0.0, 'MVA_rating': 500.0, 'kV_base': 345.0, 'm': 1.006, 'shift': 0.0, 'Cost MEUR': 10.88},
    {'Line_id': 'L_AC23', 'fromNode': '13', 'toNode': '14', 'r': 0.0009, 'x': 0.0101, 'g': 0.0, 'b': 0.1723, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.04},
    {'Line_id': 'L_AC24', 'fromNode': '14', 'toNode': '15', 'r': 0.0018, 'x': 0.0217, 'g': 0.0, 'b': 0.366, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.53},
    {'Line_id': 'L_AC25', 'fromNode': '15', 'toNode': '16', 'r': 0.0009, 'x': 0.0094, 'g': 0.0, 'b': 0.171, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.83},
    {'Line_id': 'L_AC26', 'fromNode': '16', 'toNode': '17', 'r': 0.0007, 'x': 0.0089, 'g': 0.0, 'b': 0.1342, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.68},
    {'Line_id': 'L_AC27', 'fromNode': '16', 'toNode': '19', 'r': 0.0016, 'x': 0.0195, 'g': 0.0, 'b': 0.304, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.87},
    {'Line_id': 'L_AC28', 'fromNode': '16', 'toNode': '21', 'r': 0.0008, 'x': 0.0135, 'g': 0.0, 'b': 0.2548, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.06},
    {'Line_id': 'L_AC29', 'fromNode': '16', 'toNode': '24', 'r': 0.0003, 'x': 0.0059, 'g': 0.0, 'b': 0.068, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.77},
    {'Line_id': 'L_AC30', 'fromNode': '17', 'toNode': '18', 'r': 0.0007, 'x': 0.0082, 'g': 0.0, 'b': 0.1319, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.47},
    {'Line_id': 'L_AC31', 'fromNode': '17', 'toNode': '27', 'r': 0.0013, 'x': 0.0173, 'g': 0.0, 'b': 0.3216, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.2},
    {'Line_id': 'L_AC32', 'fromNode': '19', 'toNode': '20', 'r': 0.0007, 'x': 0.0138, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.06, 'shift': 0.0, 'Cost MEUR': 6.22},
    {'Line_id': 'L_AC33', 'fromNode': '19', 'toNode': '33', 'r': 0.0007, 'x': 0.0142, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.07, 'shift': 0.0, 'Cost MEUR': 6.4},
    {'Line_id': 'L_AC34', 'fromNode': '20', 'toNode': '34', 'r': 0.0009, 'x': 0.018, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.009, 'shift': 0.0, 'Cost MEUR': 8.11},
    {'Line_id': 'L_AC35', 'fromNode': '21', 'toNode': '22', 'r': 0.0008, 'x': 0.014, 'g': 0.0, 'b': 0.2565, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.31},
    {'Line_id': 'L_AC36', 'fromNode': '22', 'toNode': '23', 'r': 0.0006, 'x': 0.0096, 'g': 0.0, 'b': 0.1846, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.89},
    {'Line_id': 'L_AC37', 'fromNode': '22', 'toNode': '35', 'r': 0.0, 'x': 0.0143, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.025, 'shift': 0.0, 'Cost MEUR': 6.44},
    {'Line_id': 'L_AC38', 'fromNode': '23', 'toNode': '24', 'r': 0.0022, 'x': 0.035, 'g': 0.0, 'b': 0.361, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.52},
    {'Line_id': 'L_AC39', 'fromNode': '23', 'toNode': '36', 'r': 0.0005, 'x': 0.0272, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.24},
    {'Line_id': 'L_AC40', 'fromNode': '25', 'toNode': '26', 'r': 0.0032, 'x': 0.0323, 'g': 0.0, 'b': 0.531, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.74},
    {'Line_id': 'L_AC41', 'fromNode': '25', 'toNode': '37', 'r': 0.0006, 'x': 0.0232, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'kV_base': 345.0, 'm': 1.025, 'shift': 0.0, 'Cost MEUR': 10.44},
    {'Line_id': 'L_AC42', 'fromNode': '26', 'toNode': '27', 'r': 0.0014, 'x': 0.0147, 'g': 0.0, 'b': 0.2396, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.43},
    {'Line_id': 'L_AC43', 'fromNode': '26', 'toNode': '28', 'r': 0.0043, 'x': 0.0474, 'g': 0.0, 'b': 0.7802, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.28},
    {'Line_id': 'L_AC44', 'fromNode': '26', 'toNode': '29', 'r': 0.0057, 'x': 0.0625, 'g': 0.0, 'b': 1.029, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 18.83},
    {'Line_id': 'L_AC45', 'fromNode': '28', 'toNode': '29', 'r': 0.0014, 'x': 0.0151, 'g': 0.0, 'b': 0.249, 'MVA_rating': 600.0, 'kV_base': 345.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.55},
    {'Line_id': 'L_AC46', 'fromNode': '29', 'toNode': '38', 'r': 0.0008, 'x': 0.0156, 'g': 0.0, 'b': 0.0, 'MVA_rating': 1200.0, 'kV_base': 345.0, 'm': 1.025, 'shift': 0.0, 'Cost MEUR': 9.37}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    lines_AC['Cost MEUR'] = lines_AC['Cost MEUR'] * kappa/0.5

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'case39'
    # Assign Price Zones to Nodes
   
    
    # Add Generators
    pyf.add_gen(grid, '30', '1', price_zone_link=False, lf=0.3, qf=0.01, MWmax=1040.0, MWmin=0.0, MVArmax=400.0, MVArmin=140.0, PsetMW=250.0, QsetMVA=161.762)
    pyf.add_gen(grid, '31', '2', price_zone_link=False, lf=0.3, qf=0.01, MWmax=646.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=677.871, QsetMVA=221.574)
    pyf.add_gen(grid, '32', '3', price_zone_link=False, lf=0.3, qf=0.01, MWmax=725.0, MWmin=0.0, MVArmax=300.0, MVArmin=150.0, PsetMW=650.0, QsetMVA=206.96500000000003)
    pyf.add_gen(grid, '33', '4', price_zone_link=False, lf=0.3, qf=0.01, MWmax=652.0, MWmin=0.0, MVArmax=250.0, MVArmin=0.0, PsetMW=632.0, QsetMVA=108.29300000000002)
    pyf.add_gen(grid, '34', '5', price_zone_link=False, lf=0.3, qf=0.01, MWmax=508.0, MWmin=0.0, MVArmax=167.0, MVArmin=0.0, PsetMW=508.0, QsetMVA=166.688)
    pyf.add_gen(grid, '35', '6', price_zone_link=False, lf=0.3, qf=0.01, MWmax=687.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=650.0, QsetMVA=210.661)
    pyf.add_gen(grid, '36', '7', price_zone_link=False, lf=0.3, qf=0.01, MWmax=580.0, MWmin=0.0, MVArmax=240.0, MVArmin=0.0, PsetMW=560.0, QsetMVA=100.16500000000002)
    pyf.add_gen(grid, '37', '8', price_zone_link=False, lf=0.3, qf=0.01, MWmax=564.0, MWmin=0.0, MVArmax=250.0, MVArmin=0.0, PsetMW=540.0, QsetMVA=-1.36945)
    pyf.add_gen(grid, '38', '9', price_zone_link=False, lf=0.3, qf=0.01, MWmax=865.0, MWmin=0.0, MVArmax=300.0, MVArmin=-150.0, PsetMW=830.0000000000001, QsetMVA=21.7327)
    pyf.add_gen(grid, '39', '10', price_zone_link=False, lf=0.3, qf=0.01, MWmax=1100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=1000.0, QsetMVA=78.4674)
    
    
    if TEP==True:
        lines_AC.set_index('Line_id', inplace=True)
        
    
        for node in grid.nodes_AC:
            node.PLi_factor = Increase

        for gen in grid.Generators:
            gen.np_gen = Increase
            
            
        if exp == 'All':
            for line in list(grid.lines_AC):  # Create a copy of the list
                name = line.name
                line_cost = lines_AC.loc[name,'Cost MEUR']*10**6
                pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
        
                
            
    
    # Return the grid
    return grid,res
