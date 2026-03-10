

import pyflow_acdc as pyf
import pandas as pd


def case39():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'Node_id': '1.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.23625827443204947, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.976, 'Reactive_load': 0.442, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '2.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.17078512035543097, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '3.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.21426332103915155, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 3.22, 'Reactive_load': 0.024, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '4.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.2203780820735137, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 5.0, 'Reactive_load': 1.84, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '5.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.19534316654936965, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '6.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.1816596281341014, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '7.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.2226276718529942, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.338, 'Reactive_load': 0.84, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '8.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.23275438633233067, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 5.22, 'Reactive_load': 1.766, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '9.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.24746049570304987, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.065, 'Reactive_load': -0.6659999999999999, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '10.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.14260867151889167, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '11.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.1559794870747753, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '12.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.15705910062616918, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.08529999999999999, 'Reactive_load': 0.88, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '13.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.15585663160339816, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '14.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.18701717807248577, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '15.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.19801456750247215, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 3.2, 'Reactive_load': 1.53, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '16.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.17511495759838802, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 3.29, 'Reactive_load': 0.32299999999999995, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '17.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.19401840928722838, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '18.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.20919809629718367, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 1.58, 'Reactive_load': 0.3, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '19.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.09442358487791794, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '20.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.11905202020058953, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 6.8, 'Reactive_load': 1.03, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '21.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.1331467372436766, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.74, 'Reactive_load': 1.15, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '22.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.05555592274075265, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '23.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.059014404354651544, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.475, 'Reactive_load': 0.846, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '24.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.17302772707257427, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 3.0860000000000003, 'Reactive_load': -0.922, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '25.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.14607071360446466, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.24, 'Reactive_load': 0.47200000000000003, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '26.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.16473760685714817, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 1.39, 'Reactive_load': 0.17, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '27.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.19830696251205876, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.81, 'Reactive_load': 0.755, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '28.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.10346938728089702, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.06, 'Reactive_load': 0.276, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '29.0', 'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': -0.05532473991869198, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 2.835, 'Reactive_load': 0.26899999999999996, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '30.0', 'type': 'PV', 'Voltage_0': 1.0499, 'theta_0': -0.12863904920461205, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '31.0', 'type': 'Slack', 'Voltage_0': 0.982, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.092, 'Reactive_load': 0.046, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '32.0', 'type': 'PV', 'Voltage_0': 0.9841, 'theta_0': -0.003288853063897563, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '33.0', 'type': 'PV', 'Voltage_0': 0.9972, 'theta_0': -0.00337153018322916, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '34.0', 'type': 'PV', 'Voltage_0': 1.0123, 'theta_0': -0.028468397041837387, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '35.0', 'type': 'PV', 'Voltage_0': 1.0494, 'theta_0': 0.03100589458939765, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '36.0', 'type': 'PV', 'Voltage_0': 1.0636, 'theta_0': 0.07798894504925487, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '37.0', 'type': 'PV', 'Voltage_0': 1.0275, 'theta_0': -0.027626795785867218, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '38.0', 'type': 'PV', 'Voltage_0': 1.0265, 'theta_0': 0.06794248604491286, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'Node_id': '39.0', 'type': 'PV', 'Voltage_0': 1.03, 'theta_0': -0.2536880748202609, 'kV_base': 345.0, 'Power_Gained': 0.0, 'Reactive_Gained': 0.0, 'Power_load': 11.04, 'Reactive_load': 2.5, 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'Line_id': 'L_AC_1', 'fromNode': '1.0', 'toNode': '2.0', 'r': 0.0035, 'x': 0.0411, 'g': 0.0, 'b': 0.6987, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_2', 'fromNode': '1.0', 'toNode': '39.0', 'r': 0.001, 'x': 0.025, 'g': 0.0, 'b': 0.75, 'MVA_rating': 1000.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_3', 'fromNode': '2.0', 'toNode': '3.0', 'r': 0.0013, 'x': 0.0151, 'g': 0.0, 'b': 0.2572, 'MVA_rating': 500.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_4', 'fromNode': '2.0', 'toNode': '25.0', 'r': 0.007, 'x': 0.0086, 'g': 0.0, 'b': 0.146, 'MVA_rating': 500.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_5', 'fromNode': '2.0', 'toNode': '30.0', 'r': 0.0, 'x': 0.0181, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.025, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_6', 'fromNode': '3.0', 'toNode': '4.0', 'r': 0.0013, 'x': 0.0213, 'g': 0.0, 'b': 0.2214, 'MVA_rating': 500.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_7', 'fromNode': '3.0', 'toNode': '18.0', 'r': 0.0011, 'x': 0.0133, 'g': 0.0, 'b': 0.2138, 'MVA_rating': 500.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_8', 'fromNode': '4.0', 'toNode': '5.0', 'r': 0.0008, 'x': 0.0128, 'g': 0.0, 'b': 0.1342, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_9', 'fromNode': '4.0', 'toNode': '14.0', 'r': 0.0008, 'x': 0.0129, 'g': 0.0, 'b': 0.1382, 'MVA_rating': 500.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_10', 'fromNode': '5.0', 'toNode': '6.0', 'r': 0.0002, 'x': 0.0026, 'g': 0.0, 'b': 0.0434, 'MVA_rating': 1200.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_11', 'fromNode': '5.0', 'toNode': '8.0', 'r': 0.0008, 'x': 0.0112, 'g': 0.0, 'b': 0.1476, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_12', 'fromNode': '6.0', 'toNode': '7.0', 'r': 0.0006, 'x': 0.0092, 'g': 0.0, 'b': 0.113, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_13', 'fromNode': '6.0', 'toNode': '11.0', 'r': 0.0007, 'x': 0.0082, 'g': 0.0, 'b': 0.1389, 'MVA_rating': 480.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_14', 'fromNode': '6.0', 'toNode': '31.0', 'r': 0.0, 'x': 0.025, 'g': 0.0, 'b': 0.0, 'MVA_rating': 1800.0, 'm': 1.07, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_15', 'fromNode': '7.0', 'toNode': '8.0', 'r': 0.0004, 'x': 0.0046, 'g': 0.0, 'b': 0.078, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_16', 'fromNode': '8.0', 'toNode': '9.0', 'r': 0.0023, 'x': 0.0363, 'g': 0.0, 'b': 0.3804, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_17', 'fromNode': '9.0', 'toNode': '39.0', 'r': 0.001, 'x': 0.025, 'g': 0.0, 'b': 1.2, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_18', 'fromNode': '10.0', 'toNode': '11.0', 'r': 0.0004, 'x': 0.0043, 'g': 0.0, 'b': 0.0729, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_19', 'fromNode': '10.0', 'toNode': '13.0', 'r': 0.0004, 'x': 0.0043, 'g': 0.0, 'b': 0.0729, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_20', 'fromNode': '10.0', 'toNode': '32.0', 'r': 0.0, 'x': 0.02, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.07, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_21', 'fromNode': '12.0', 'toNode': '11.0', 'r': 0.0016, 'x': 0.0435, 'g': 0.0, 'b': 0.0, 'MVA_rating': 500.0, 'm': 1.006, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_22', 'fromNode': '12.0', 'toNode': '13.0', 'r': 0.0016, 'x': 0.0435, 'g': 0.0, 'b': 0.0, 'MVA_rating': 500.0, 'm': 1.006, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_23', 'fromNode': '13.0', 'toNode': '14.0', 'r': 0.0009, 'x': 0.0101, 'g': 0.0, 'b': 0.1723, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_24', 'fromNode': '14.0', 'toNode': '15.0', 'r': 0.0018, 'x': 0.0217, 'g': 0.0, 'b': 0.366, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_25', 'fromNode': '15.0', 'toNode': '16.0', 'r': 0.0009, 'x': 0.0094, 'g': 0.0, 'b': 0.171, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_26', 'fromNode': '16.0', 'toNode': '17.0', 'r': 0.0007, 'x': 0.0089, 'g': 0.0, 'b': 0.1342, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_27', 'fromNode': '16.0', 'toNode': '19.0', 'r': 0.0016, 'x': 0.0195, 'g': 0.0, 'b': 0.304, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_28', 'fromNode': '16.0', 'toNode': '21.0', 'r': 0.0008, 'x': 0.0135, 'g': 0.0, 'b': 0.2548, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_29', 'fromNode': '16.0', 'toNode': '24.0', 'r': 0.0003, 'x': 0.0059, 'g': 0.0, 'b': 0.068, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_30', 'fromNode': '17.0', 'toNode': '18.0', 'r': 0.0007, 'x': 0.0082, 'g': 0.0, 'b': 0.1319, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_31', 'fromNode': '17.0', 'toNode': '27.0', 'r': 0.0013, 'x': 0.0173, 'g': 0.0, 'b': 0.3216, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_32', 'fromNode': '19.0', 'toNode': '20.0', 'r': 0.0007, 'x': 0.0138, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.06, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_33', 'fromNode': '19.0', 'toNode': '33.0', 'r': 0.0007, 'x': 0.0142, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.07, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_34', 'fromNode': '20.0', 'toNode': '34.0', 'r': 0.0009, 'x': 0.018, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.009, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_35', 'fromNode': '21.0', 'toNode': '22.0', 'r': 0.0008, 'x': 0.014, 'g': 0.0, 'b': 0.2565, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_36', 'fromNode': '22.0', 'toNode': '23.0', 'r': 0.0006, 'x': 0.0096, 'g': 0.0, 'b': 0.1846, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_37', 'fromNode': '22.0', 'toNode': '35.0', 'r': 0.0, 'x': 0.0143, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.025, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_38', 'fromNode': '23.0', 'toNode': '24.0', 'r': 0.0022, 'x': 0.035, 'g': 0.0, 'b': 0.361, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_39', 'fromNode': '23.0', 'toNode': '36.0', 'r': 0.0005, 'x': 0.0272, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_40', 'fromNode': '25.0', 'toNode': '26.0', 'r': 0.0032, 'x': 0.0323, 'g': 0.0, 'b': 0.531, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_41', 'fromNode': '25.0', 'toNode': '37.0', 'r': 0.0006, 'x': 0.0232, 'g': 0.0, 'b': 0.0, 'MVA_rating': 900.0, 'm': 1.025, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_42', 'fromNode': '26.0', 'toNode': '27.0', 'r': 0.0014, 'x': 0.0147, 'g': 0.0, 'b': 0.2396, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_43', 'fromNode': '26.0', 'toNode': '28.0', 'r': 0.0043, 'x': 0.0474, 'g': 0.0, 'b': 0.7802, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_44', 'fromNode': '26.0', 'toNode': '29.0', 'r': 0.0057, 'x': 0.0625, 'g': 0.0, 'b': 1.029, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_45', 'fromNode': '28.0', 'toNode': '29.0', 'r': 0.0014, 'x': 0.0151, 'g': 0.0, 'b': 0.249, 'MVA_rating': 600.0, 'm': 1.0, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None},
        {'Line_id': 'L_AC_46', 'fromNode': '29.0', 'toNode': '38.0', 'r': 0.0008, 'x': 0.0156, 'g': 0.0, 'b': 0.0, 'MVA_rating': 1200.0, 'm': 1.025, 'shift': 0.0, 'Length_km': 1.0, 'geometry': None}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC_data = [
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '1.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '2.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '3.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '4.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '5.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '6.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '7.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '8.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '9.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0.0, 'Power_load': 0.0, 'kV_base': 345.0, 'Node_id': '10.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None}
    ]
    nodes_DC = pd.DataFrame(nodes_DC_data)

    lines_DC_data = [
        {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_1', 'geometry': None},
        {'fromNode': '2.0', 'toNode': '3.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_2', 'geometry': None},
        {'fromNode': '1.0', 'toNode': '4.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_3', 'geometry': None},
        {'fromNode': '2.0', 'toNode': '4.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_4', 'geometry': None},
        {'fromNode': '2.0', 'toNode': '4.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_5', 'geometry': None},
        {'fromNode': '1.0', 'toNode': '5.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_6', 'geometry': None},
        {'fromNode': '5.0', 'toNode': '6.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_7', 'geometry': None},
        {'fromNode': '5.0', 'toNode': '7.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_8', 'geometry': None},
        {'fromNode': '7.0', 'toNode': '4.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_9', 'geometry': None},
        {'fromNode': '4.0', 'toNode': '8.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_10', 'geometry': None},
        {'fromNode': '8.0', 'toNode': '9.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_11', 'geometry': None},
        {'fromNode': '8.0', 'toNode': '10.0', 'r': 0.01, 'MW_rating': 100.0, 'kV_base': 345.0, 'Length_km': 1.0, 'Mono_Bi_polar': 'b', 'Line_id': 'L_DC_12', 'geometry': None}
    ]
    lines_DC = pd.DataFrame(lines_DC_data)

    Converters_ACDC_data = [
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '2.0', 'DC_node': '1.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_1', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '9.0', 'DC_node': '2.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_2', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '10.0', 'DC_node': '3.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_3', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '18.0', 'DC_node': '4.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_4', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '26.0', 'DC_node': '5.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_5', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '29.0', 'DC_node': '6.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_6', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '24.0', 'DC_node': '7.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_7', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '14.0', 'DC_node': '8.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_8', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '23.0', 'DC_node': '9.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_9', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None},
        {'AC_type': 'PQ', 'DC_type': 'P', 'AC_node': '13.0', 'DC_node': '10.0', 'P_AC': -0.6, 'Q_AC': -0.4, 'P_DC': -0.586274, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter': 0.01, 'Droop': 0.005, 'AC_kV_base': 345.0, 'MVA_rating': 100.0, 'Nconverter': 1.0, 'pol': 1.0, 'Conv_id': 'Conv_10', 'lossa': 1.1033, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1, 'geometry': None}
    ]
    Converters_ACDC = pd.DataFrame(Converters_ACDC_data)

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='pu')
    grid.name = 'case39'
    
    # Add Generators
    pyf.add_gen(grid, '30.0', '1', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=1040.0, MWmin=0.0, MVArmax=400.0, MVArmin=140.0, PsetMW=250.0, QsetMVA=161.762)
    pyf.add_gen(grid, '31.0', '2', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=646.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=677.871, QsetMVA=221.574)
    pyf.add_gen(grid, '32.0', '3', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=725.0, MWmin=0.0, MVArmax=300.0, MVArmin=150.0, PsetMW=650.0, QsetMVA=206.96500000000003)
    pyf.add_gen(grid, '33.0', '4', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=652.0, MWmin=0.0, MVArmax=250.0, MVArmin=0.0, PsetMW=632.0, QsetMVA=108.29300000000002)
    pyf.add_gen(grid, '34.0', '5', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=508.0, MWmin=0.0, MVArmax=167.0, MVArmin=0.0, PsetMW=508.0, QsetMVA=166.688)
    pyf.add_gen(grid, '35.0', '6', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=687.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=650.0, QsetMVA=210.661)
    pyf.add_gen(grid, '36.0', '7', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=580.0, MWmin=0.0, MVArmax=240.0, MVArmin=0.0, PsetMW=560.0, QsetMVA=100.16500000000002)
    pyf.add_gen(grid, '37.0', '8', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=564.0, MWmin=0.0, MVArmax=250.0, MVArmin=0.0, PsetMW=540.0, QsetMVA=-1.36945)
    pyf.add_gen(grid, '38.0', '9', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=865.0, MWmin=0.0, MVArmax=300.0, MVArmin=-150.0, PsetMW=830.0000000000001, QsetMVA=21.7327)
    pyf.add_gen(grid, '39.0', '10', np_gen=1, fc=0.2,lf=0.3, qf=0.01, MWmax=1100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=1000.0, QsetMVA=78.4674)
    
    
    # Add Renewable Source Zones

    
    # Add Renewable Sources

    
    # Return the grid
    return grid,res
