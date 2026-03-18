

import pyflow_acdc as pyf
import pandas as pd
"""
Converted to PyFlowACDC format from

%case 5 nodes    Power flow data for 5 bus, 2 generator case.
%   Please see 'help caseformat' for details on the case file format.
%
%   case file can be used together with dc case files "case5_stagg_....m"
%
%   Network data from ...
%   G.W. Stagg, A.H. El-Abiad, "Computer methods in power system analysis",
%   McGraw-Hill, 1968.
%
%   MATPOWER case file data provided by Jef Beerten.

%dc case 3 nodes    dc power flow data for 3 node system
%
%   3 node system (constant voltage and power controlled) can be used 
%   together with ac case files 'case5_stagg.m' and 'case'3_inf.m'
%   
%   Network data based on ...
%   J. Beerten, D. Van Hertem, R. Belmans, "VSC MTDC systems with a 
%   distributed DC voltage control – a power flow approach", in IEEE 
%   Powertech2011, Trondheim, Norway, Jun 2011.
%
%   MATACDC case file data provided by Jef Beerten.


"""

def Stagg5MATACDC():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'Slack', 'Voltage_0': 1.06, 'theta_0': 0.0, 'kV_base': 345, 'Power_Gained': 0.0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '1', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.1, 'kV_base': 345, 'Power_Gained': 0.4, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.1, 'Node_id': '2', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.1, 'kV_base': 345, 'Power_Gained': 0.0, 'Reactive_Gained': 0, 'Power_load': 0.45, 'Reactive_load': 0.15, 'Node_id': '3', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.1, 'kV_base': 345, 'Power_Gained': 0.0, 'Reactive_Gained': 0, 'Power_load': 0.4, 'Reactive_load': 0.05, 'Node_id': '4', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.1, 'kV_base': 345, 'Power_Gained': 0.0, 'Reactive_Gained': 0, 'Power_load': 0.6, 'Reactive_load': 0.1, 'Node_id': '5', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1', 'toNode': '2', 'r': 0.02, 'x': 0.06, 'g': 0, 'b': 0.06, 'MVA_rating': 150, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '1'},
        {'fromNode': '1', 'toNode': '3', 'r': 0.08, 'x': 0.24, 'g': 0, 'b': 0.05, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '2'},
        {'fromNode': '2', 'toNode': '3', 'r': 0.06, 'x': 0.18, 'g': 0, 'b': 0.04, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '3'},
        {'fromNode': '2', 'toNode': '4', 'r': 0.06, 'x': 0.18, 'g': 0, 'b': 0.04, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '4'},
        {'fromNode': '2', 'toNode': '5', 'r': 0.04, 'x': 0.12, 'g': 0, 'b': 0.03, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '5'},
        {'fromNode': '3', 'toNode': '4', 'r': 0.01, 'x': 0.03, 'g': 0, 'b': 0.02, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '6'},
        {'fromNode': '4', 'toNode': '5', 'r': 0.08, 'x': 0.24, 'g': 0, 'b': 0.05, 'MVA_rating': 100, 'kV_base': 345, 'm': 1, 'shift': 0, 'Line_id': '7'}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC_data = [
        {'type': 'PAC', 'Voltage_0': 1, 'Power_Gained': 0, 'Power_load': 0, 'kV_base': 345, 'Node_id': '1', 'Umin': 0.95, 'Umax': 1.05, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Slack', 'Voltage_0': 1, 'Power_Gained': 0, 'Power_load': 0, 'kV_base': 345, 'Node_id': '2', 'Umin': 0.95, 'Umax': 1.05, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PAC', 'Voltage_0': 1, 'Power_Gained': 0, 'Power_load': 0, 'kV_base': 345, 'Node_id': '3', 'Umin': 0.95, 'Umax': 1.05, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_DC = pd.DataFrame(nodes_DC_data)

    lines_DC_data = [
        {'fromNode': '1', 'toNode': '2', 'r': 0.052, 'MW_rating': 100, 'kV_base': 345, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Line_id': '1'},
        {'fromNode': '2', 'toNode': '3', 'r': 0.052, 'MW_rating': 100, 'kV_base': 345, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Line_id': '2'},
        {'fromNode': '1', 'toNode': '3', 'r': 0.073, 'MW_rating': 100, 'kV_base': 345, 'Length_km': 1, 'Mono_Bi_polar': 'sm', 'Line_id': '3'}
    ]
    lines_DC = pd.DataFrame(lines_DC_data)

    Converters_ACDC_data = [
        {'AC_type': 'PQ', 'DC_type': 'PAC', 'AC_node': '2', 'DC_node': '1', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': 0, 'T_r': 0.0015, 'T_x': 0.121, 'PR_r': 0.0001, 'PR_x': 0.16428, 'Filter_b': 0.0887, 'Droop': 0, 'AC_kV_base': 345, 'MVA_rating': 120.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '1', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2},
        {'AC_type': 'PV', 'DC_type': 'Slack', 'AC_node': '3', 'DC_node': '2', 'P_AC': 0.0, 'Q_AC': 0.0, 'P_DC': 0, 'T_r': 0.0015, 'T_x': 0.121, 'PR_r': 0.0001, 'PR_x': 0.16428, 'Filter_b': 0.0887, 'Droop': 0, 'AC_kV_base': 345, 'MVA_rating': 120.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '2', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2},
        {'AC_type': 'PQ', 'DC_type': 'PAC', 'AC_node': '5', 'DC_node': '3', 'P_AC': 0.35, 'Q_AC': 0.05, 'P_DC': 0, 'T_r': 0.0015, 'T_x': 0.121, 'PR_r': 0.0001, 'PR_x': 0.16428, 'Filter_b': 0.0887, 'Droop': 0, 'AC_kV_base': 345, 'MVA_rating': 120.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '3', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 4.371, 'Ucmin': 0.9, 'Ucmax': 1.2}
    ]
    Converters_ACDC = pd.DataFrame(Converters_ACDC_data)

    gen_data = [
        {'Gen': '1','Node': '1', 'PsetMW': 0,'QsetMVA': 0,'MWmax': 250,'MWmin': 10,'MVARmax': 500,'MVARmin': -500},
        {'Gen': '2','Node': '2', 'PsetMW': 40,'QsetMVA': 0,'MWmax': 300,'MWmin': 10,'MVARmax': 300,'MVARmin': -300}
    ]
    gen = pd.DataFrame(gen_data)


    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'Stagg 5-bus System ACDC'
    pyf.add_generators(grid,gen)
    
    # Return the grid
    return grid,res
