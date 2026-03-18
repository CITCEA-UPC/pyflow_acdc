import pyflow_acdc as pyf
import pandas as pd

"""
This case has been modified to include Transmision expansion costs for work

Bernardo Castro Valerio, Marc Cheah-Mane, Vinicius A. Lacerda, Pieter Gebraad, Oriol Gomis-Bellmunt,
Transmission expansion planning for hybrid AC/DC grids using a mixed-integer non-linear programming approach,
International Journal of Electrical Power & Energy Systems,
Volume 174,
2026,
111459,
ISSN 0142-0615,
https://doi.org/10.1016/j.ijepes.2025.111459.

TEP information obtained from:

TNEP of meshed HVDC grids: 'AC', 'DC' and convex formulations
Jay Dave (jay.dave@kuleuven.be), Hakan Ergun , Ting An , Jingjing Lu , and Dirk Van Hertem
https://doi.org/10.1049/iet-gtd.2019.0383



"""
def case118_TEP_DC(exp='All',N_b=0,N_i=1,N_max=1):    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.51, 'Reactive_load': 0.27, 'Node_id': '1.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.09, 'Node_id': '2.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.1, 'Node_id': '3.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.12, 'Node_id': '4.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.4, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.52, 'Reactive_load': 0.22, 'Node_id': '6.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.19, 'Reactive_load': 0.02, 'Node_id': '7.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.0, 'Node_id': '8.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '9.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '10.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.7, 'Reactive_load': 0.23, 'Node_id': '11.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.47, 'Reactive_load': 0.1, 'Node_id': '12.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.16, 'Node_id': '13.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.14, 'Reactive_load': 0.01, 'Node_id': '14.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.9, 'Reactive_load': 0.3, 'Node_id': '15.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.25, 'Reactive_load': 0.1, 'Node_id': '16.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.11, 'Reactive_load': 0.03, 'Node_id': '17.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.6, 'Reactive_load': 0.34, 'Node_id': '18.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.962, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.45, 'Reactive_load': 0.25, 'Node_id': '19.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.03, 'Node_id': '20.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.14, 'Reactive_load': 0.08, 'Node_id': '21.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.1, 'Reactive_load': 0.05, 'Node_id': '22.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.07, 'Reactive_load': 0.03, 'Node_id': '23.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.992, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.13, 'Reactive_load': 0.0, 'Node_id': '24.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '25.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '26.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.968, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.71, 'Reactive_load': 0.13, 'Node_id': '27.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.07, 'Node_id': '28.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.24, 'Reactive_load': 0.04, 'Node_id': '29.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '30.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.967, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.43, 'Reactive_load': 0.27, 'Node_id': '31.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.963, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.59, 'Reactive_load': 0.23, 'Node_id': '32.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.09, 'Node_id': '33.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.984, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.59, 'Reactive_load': 0.26, 'Node_id': '34.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.14, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.33, 'Reactive_load': 0.09, 'Node_id': '35.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.31, 'Reactive_load': 0.17, 'Node_id': '36.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '37.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.25, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '38.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.27, 'Reactive_load': 0.11, 'Node_id': '39.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.66, 'Reactive_load': 0.23, 'Node_id': '40.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.37, 'Reactive_load': 0.1, 'Node_id': '41.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.96, 'Reactive_load': 0.23, 'Node_id': '42.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.07, 'Node_id': '43.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.16, 'Reactive_load': 0.08, 'Node_id': '44.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.53, 'Reactive_load': 0.22, 'Node_id': '45.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.1, 'Node_id': '46.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.0, 'Node_id': '47.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.11, 'Node_id': '48.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.15, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.87, 'Reactive_load': 0.3, 'Node_id': '49.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.04, 'Node_id': '50.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.17, 'Reactive_load': 0.08, 'Node_id': '51.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.18, 'Reactive_load': 0.05, 'Node_id': '52.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.11, 'Node_id': '53.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.13, 'Reactive_load': 0.32, 'Node_id': '54.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.63, 'Reactive_load': 0.22, 'Node_id': '55.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.954, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.84, 'Reactive_load': 0.18, 'Node_id': '56.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '57.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '58.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.77, 'Reactive_load': 1.13, 'Node_id': '59.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.78, 'Reactive_load': 0.03, 'Node_id': '60.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.995, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '61.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.77, 'Reactive_load': 0.14, 'Node_id': '62.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '63.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '64.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '65.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.18, 'Node_id': '66.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.28, 'Reactive_load': 0.07, 'Node_id': '67.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '68.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'Slack', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '69.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.984, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.66, 'Reactive_load': 0.2, 'Node_id': '70.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '71.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.0, 'Node_id': '72.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.991, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '73.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.958, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.27, 'Node_id': '74.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.12, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.47, 'Reactive_load': 0.11, 'Node_id': '75.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.943, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.36, 'Node_id': '76.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.006, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.61, 'Reactive_load': 0.28, 'Node_id': '77.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.71, 'Reactive_load': 0.26, 'Node_id': '78.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.32, 'Node_id': '79.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.04, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.3, 'Reactive_load': 0.26, 'Node_id': '80.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '81.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.54, 'Reactive_load': 0.27, 'Node_id': '82.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.1, 'Node_id': '83.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.11, 'Reactive_load': 0.07, 'Node_id': '84.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.24, 'Reactive_load': 0.15, 'Node_id': '85.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.21, 'Reactive_load': 0.1, 'Node_id': '86.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 161.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '87.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.48, 'Reactive_load': 0.1, 'Node_id': '88.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '89.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.63, 'Reactive_load': 0.42, 'Node_id': '90.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.1, 'Reactive_load': 0.0, 'Node_id': '91.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.65, 'Reactive_load': 0.1, 'Node_id': '92.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.12, 'Reactive_load': 0.07, 'Node_id': '93.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.3, 'Reactive_load': 0.16, 'Node_id': '94.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.42, 'Reactive_load': 0.31, 'Node_id': '95.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.38, 'Reactive_load': 0.15, 'Node_id': '96.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.15, 'Reactive_load': 0.09, 'Node_id': '97.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.34, 'Reactive_load': 0.08, 'Node_id': '98.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.42, 'Reactive_load': 0.0, 'Node_id': '99.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.37, 'Reactive_load': 0.18, 'Node_id': '100.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.22, 'Reactive_load': 0.15, 'Node_id': '101.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.05, 'Reactive_load': 0.03, 'Node_id': '102.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.23, 'Reactive_load': 0.16, 'Node_id': '103.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.971, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.38, 'Reactive_load': 0.25, 'Node_id': '104.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.965, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.31, 'Reactive_load': 0.26, 'Node_id': '105.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.43, 'Reactive_load': 0.16, 'Node_id': '106.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.5, 'Reactive_load': 0.12, 'Node_id': '107.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.02, 'Reactive_load': 0.01, 'Node_id': '108.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '109.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.39, 'Reactive_load': 0.3, 'Node_id': '110.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '111.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.975, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.68, 'Reactive_load': 0.13, 'Node_id': '112.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 0.993, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '113.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '114.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.22, 'Reactive_load': 0.07, 'Node_id': '115.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.84, 'Reactive_load': 0.0, 'Node_id': '116.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.2, 'Reactive_load': 0.08, 'Node_id': '117.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.33, 'Reactive_load': 0.15, 'Node_id': '118.0', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None, 'geometry': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.0303, 'x': 0.0999, 'g': 0, 'b': 0.0254, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '1', 'geometry': None},
        {'fromNode': '1.0', 'toNode': '3.0', 'r': 0.0129, 'x': 0.0424, 'g': 0, 'b': 0.01082, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '2', 'geometry': None},
        {'fromNode': '4.0', 'toNode': '5.0', 'r': 0.00176, 'x': 0.00798, 'g': 0, 'b': 0.0021, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '3', 'geometry': None},
        {'fromNode': '3.0', 'toNode': '5.0', 'r': 0.0241, 'x': 0.108, 'g': 0, 'b': 0.0284, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '4', 'geometry': None},
        {'fromNode': '5.0', 'toNode': '6.0', 'r': 0.0119, 'x': 0.054, 'g': 0, 'b': 0.01426, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '5', 'geometry': None},
        {'fromNode': '6.0', 'toNode': '7.0', 'r': 0.00459, 'x': 0.0208, 'g': 0, 'b': 0.0055, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '6', 'geometry': None},
        {'fromNode': '8.0', 'toNode': '9.0', 'r': 0.00244, 'x': 0.0305, 'g': 0, 'b': 1.162, 'MVA_rating': 711.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '7', 'geometry': None},
        {'fromNode': '8.0', 'toNode': '5.0', 'r': 0.0, 'x': 0.0267, 'g': 0, 'b': 0.0, 'MVA_rating': 1099.0, 'kV_base': 138.0, 'm': 0.985, 'shift': 0.0, 'Line_id': '8', 'geometry': None},
        {'fromNode': '9.0', 'toNode': '10.0', 'r': 0.00258, 'x': 0.0322, 'g': 0, 'b': 1.23, 'MVA_rating': 710.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '9', 'geometry': None},
        {'fromNode': '4.0', 'toNode': '11.0', 'r': 0.0209, 'x': 0.0688, 'g': 0, 'b': 0.01748, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '10', 'geometry': None},
        {'fromNode': '5.0', 'toNode': '11.0', 'r': 0.0203, 'x': 0.0682, 'g': 0, 'b': 0.01738, 'MVA_rating': 152.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '11', 'geometry': None},
        {'fromNode': '11.0', 'toNode': '12.0', 'r': 0.00595, 'x': 0.0196, 'g': 0, 'b': 0.00502, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '12', 'geometry': None},
        {'fromNode': '2.0', 'toNode': '12.0', 'r': 0.0187, 'x': 0.0616, 'g': 0, 'b': 0.01572, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '13', 'geometry': None},
        {'fromNode': '3.0', 'toNode': '12.0', 'r': 0.0484, 'x': 0.16, 'g': 0, 'b': 0.0406, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '14', 'geometry': None},
        {'fromNode': '7.0', 'toNode': '12.0', 'r': 0.00862, 'x': 0.034, 'g': 0, 'b': 0.00874, 'MVA_rating': 164.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '15', 'geometry': None},
        {'fromNode': '11.0', 'toNode': '13.0', 'r': 0.02225, 'x': 0.0731, 'g': 0, 'b': 0.01876, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '16', 'geometry': None},
        {'fromNode': '12.0', 'toNode': '14.0', 'r': 0.0215, 'x': 0.0707, 'g': 0, 'b': 0.01816, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '17', 'geometry': None},
        {'fromNode': '13.0', 'toNode': '15.0', 'r': 0.0744, 'x': 0.2444, 'g': 0, 'b': 0.06268, 'MVA_rating': 115.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '18', 'geometry': None},
        {'fromNode': '14.0', 'toNode': '15.0', 'r': 0.0595, 'x': 0.195, 'g': 0, 'b': 0.0502, 'MVA_rating': 144.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '19', 'geometry': None},
        {'fromNode': '12.0', 'toNode': '16.0', 'r': 0.0212, 'x': 0.0834, 'g': 0, 'b': 0.0214, 'MVA_rating': 164.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '20', 'geometry': None},
        {'fromNode': '15.0', 'toNode': '17.0', 'r': 0.0132, 'x': 0.0437, 'g': 0, 'b': 0.0444, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '21', 'geometry': None},
        {'fromNode': '16.0', 'toNode': '17.0', 'r': 0.0454, 'x': 0.1801, 'g': 0, 'b': 0.0466, 'MVA_rating': 158.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '22', 'geometry': None},
        {'fromNode': '17.0', 'toNode': '18.0', 'r': 0.0123, 'x': 0.0505, 'g': 0, 'b': 0.01298, 'MVA_rating': 167.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '23', 'geometry': None},
        {'fromNode': '18.0', 'toNode': '19.0', 'r': 0.01119, 'x': 0.0493, 'g': 0, 'b': 0.01142, 'MVA_rating': 173.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '24', 'geometry': None},
        {'fromNode': '19.0', 'toNode': '20.0', 'r': 0.0252, 'x': 0.117, 'g': 0, 'b': 0.0298, 'MVA_rating': 178.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '25', 'geometry': None},
        {'fromNode': '15.0', 'toNode': '19.0', 'r': 0.012, 'x': 0.0394, 'g': 0, 'b': 0.0101, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '26', 'geometry': None},
        {'fromNode': '20.0', 'toNode': '21.0', 'r': 0.0183, 'x': 0.0849, 'g': 0, 'b': 0.0216, 'MVA_rating': 177.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '27', 'geometry': None},
        {'fromNode': '21.0', 'toNode': '22.0', 'r': 0.0209, 'x': 0.097, 'g': 0, 'b': 0.0246, 'MVA_rating': 178.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '28', 'geometry': None},
        {'fromNode': '22.0', 'toNode': '23.0', 'r': 0.0342, 'x': 0.159, 'g': 0, 'b': 0.0404, 'MVA_rating': 178.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '29', 'geometry': None},
        {'fromNode': '23.0', 'toNode': '24.0', 'r': 0.0135, 'x': 0.0492, 'g': 0, 'b': 0.0498, 'MVA_rating': 158.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '30', 'geometry': None},
        {'fromNode': '23.0', 'toNode': '25.0', 'r': 0.0156, 'x': 0.08, 'g': 0, 'b': 0.0864, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '31', 'geometry': None},
        {'fromNode': '26.0', 'toNode': '25.0', 'r': 0.0, 'x': 0.0382, 'g': 0, 'b': 0.0, 'MVA_rating': 768.0, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '32', 'geometry': None},
        {'fromNode': '25.0', 'toNode': '27.0', 'r': 0.0318, 'x': 0.163, 'g': 0, 'b': 0.1764, 'MVA_rating': 177.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '33', 'geometry': None},
        {'fromNode': '27.0', 'toNode': '28.0', 'r': 0.01913, 'x': 0.0855, 'g': 0, 'b': 0.0216, 'MVA_rating': 174.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '34', 'geometry': None},
        {'fromNode': '28.0', 'toNode': '29.0', 'r': 0.0237, 'x': 0.0943, 'g': 0, 'b': 0.0238, 'MVA_rating': 165.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '35', 'geometry': None},
        {'fromNode': '30.0', 'toNode': '17.0', 'r': 0.0, 'x': 0.0388, 'g': 0, 'b': 0.0, 'MVA_rating': 756.0, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '36', 'geometry': None},
        {'fromNode': '8.0', 'toNode': '30.0', 'r': 0.00431, 'x': 0.0504, 'g': 0, 'b': 0.514, 'MVA_rating': 580.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '37', 'geometry': None},
        {'fromNode': '26.0', 'toNode': '30.0', 'r': 0.00799, 'x': 0.086, 'g': 0, 'b': 0.908, 'MVA_rating': 340.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '38', 'geometry': None},
        {'fromNode': '17.0', 'toNode': '31.0', 'r': 0.0474, 'x': 0.1563, 'g': 0, 'b': 0.0399, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '39', 'geometry': None},
        {'fromNode': '29.0', 'toNode': '31.0', 'r': 0.0108, 'x': 0.0331, 'g': 0, 'b': 0.0083, 'MVA_rating': 146.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '40', 'geometry': None},
        {'fromNode': '23.0', 'toNode': '32.0', 'r': 0.0317, 'x': 0.1153, 'g': 0, 'b': 0.1173, 'MVA_rating': 158.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '41', 'geometry': None},
        {'fromNode': '31.0', 'toNode': '32.0', 'r': 0.0298, 'x': 0.0985, 'g': 0, 'b': 0.0251, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '42', 'geometry': None},
        {'fromNode': '27.0', 'toNode': '32.0', 'r': 0.0229, 'x': 0.0755, 'g': 0, 'b': 0.01926, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '43', 'geometry': None},
        {'fromNode': '15.0', 'toNode': '33.0', 'r': 0.038, 'x': 0.1244, 'g': 0, 'b': 0.03194, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '44', 'geometry': None},
        {'fromNode': '19.0', 'toNode': '34.0', 'r': 0.0752, 'x': 0.247, 'g': 0, 'b': 0.0632, 'MVA_rating': 114.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '45', 'geometry': None},
        {'fromNode': '35.0', 'toNode': '36.0', 'r': 0.00224, 'x': 0.0102, 'g': 0, 'b': 0.00268, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '46', 'geometry': None},
        {'fromNode': '35.0', 'toNode': '37.0', 'r': 0.011, 'x': 0.0497, 'g': 0, 'b': 0.01318, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '47', 'geometry': None},
        {'fromNode': '33.0', 'toNode': '37.0', 'r': 0.0415, 'x': 0.142, 'g': 0, 'b': 0.0366, 'MVA_rating': 154.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '48', 'geometry': None},
        {'fromNode': '34.0', 'toNode': '36.0', 'r': 0.00871, 'x': 0.0268, 'g': 0, 'b': 0.00568, 'MVA_rating': 146.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '49', 'geometry': None},
        {'fromNode': '34.0', 'toNode': '37.0', 'r': 0.00256, 'x': 0.0094, 'g': 0, 'b': 0.00984, 'MVA_rating': 159.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '50', 'geometry': None},
        {'fromNode': '38.0', 'toNode': '37.0', 'r': 0.0, 'x': 0.0375, 'g': 0, 'b': 0.0, 'MVA_rating': 783.0, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '51', 'geometry': None},
        {'fromNode': '37.0', 'toNode': '39.0', 'r': 0.0321, 'x': 0.106, 'g': 0, 'b': 0.027, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '52', 'geometry': None},
        {'fromNode': '37.0', 'toNode': '40.0', 'r': 0.0593, 'x': 0.168, 'g': 0, 'b': 0.042, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '53', 'geometry': None},
        {'fromNode': '30.0', 'toNode': '38.0', 'r': 0.00464, 'x': 0.054, 'g': 0, 'b': 0.422, 'MVA_rating': 542.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '54', 'geometry': None},
        {'fromNode': '39.0', 'toNode': '40.0', 'r': 0.0184, 'x': 0.0605, 'g': 0, 'b': 0.01552, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '55', 'geometry': None},
        {'fromNode': '40.0', 'toNode': '41.0', 'r': 0.0145, 'x': 0.0487, 'g': 0, 'b': 0.01222, 'MVA_rating': 152.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '56', 'geometry': None},
        {'fromNode': '40.0', 'toNode': '42.0', 'r': 0.0555, 'x': 0.183, 'g': 0, 'b': 0.0466, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '57', 'geometry': None},
        {'fromNode': '41.0', 'toNode': '42.0', 'r': 0.041, 'x': 0.135, 'g': 0, 'b': 0.0344, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '58', 'geometry': None},
        {'fromNode': '43.0', 'toNode': '44.0', 'r': 0.0608, 'x': 0.2454, 'g': 0, 'b': 0.06068, 'MVA_rating': 117.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '59', 'geometry': None},
        {'fromNode': '34.0', 'toNode': '43.0', 'r': 0.0413, 'x': 0.1681, 'g': 0, 'b': 0.04226, 'MVA_rating': 167.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '60', 'geometry': None},
        {'fromNode': '44.0', 'toNode': '45.0', 'r': 0.0224, 'x': 0.0901, 'g': 0, 'b': 0.0224, 'MVA_rating': 166.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '61', 'geometry': None},
        {'fromNode': '45.0', 'toNode': '46.0', 'r': 0.04, 'x': 0.1356, 'g': 0, 'b': 0.0332, 'MVA_rating': 153.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '62', 'geometry': None},
        {'fromNode': '46.0', 'toNode': '47.0', 'r': 0.038, 'x': 0.127, 'g': 0, 'b': 0.0316, 'MVA_rating': 152.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '63', 'geometry': None},
        {'fromNode': '46.0', 'toNode': '48.0', 'r': 0.0601, 'x': 0.189, 'g': 0, 'b': 0.0472, 'MVA_rating': 148.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '64', 'geometry': None},
        {'fromNode': '47.0', 'toNode': '49.0', 'r': 0.0191, 'x': 0.0625, 'g': 0, 'b': 0.01604, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '65', 'geometry': None},
        {'fromNode': '42.0', 'toNode': '49.0', 'r': 0.0715, 'x': 0.323, 'g': 0, 'b': 0.086, 'MVA_rating': 89.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '66', 'geometry': None},
        {'fromNode': '42.0', 'toNode': '49.0', 'r': 0.0715, 'x': 0.323, 'g': 0, 'b': 0.086, 'MVA_rating': 89.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '67', 'geometry': None},
        {'fromNode': '45.0', 'toNode': '49.0', 'r': 0.0684, 'x': 0.186, 'g': 0, 'b': 0.0444, 'MVA_rating': 138.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '68', 'geometry': None},
        {'fromNode': '48.0', 'toNode': '49.0', 'r': 0.0179, 'x': 0.0505, 'g': 0, 'b': 0.01258, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '69', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '50.0', 'r': 0.0267, 'x': 0.0752, 'g': 0, 'b': 0.01874, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '70', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '51.0', 'r': 0.0486, 'x': 0.137, 'g': 0, 'b': 0.0342, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '71', 'geometry': None},
        {'fromNode': '51.0', 'toNode': '52.0', 'r': 0.0203, 'x': 0.0588, 'g': 0, 'b': 0.01396, 'MVA_rating': 142.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '72', 'geometry': None},
        {'fromNode': '52.0', 'toNode': '53.0', 'r': 0.0405, 'x': 0.1635, 'g': 0, 'b': 0.04058, 'MVA_rating': 166.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '73', 'geometry': None},
        {'fromNode': '53.0', 'toNode': '54.0', 'r': 0.0263, 'x': 0.122, 'g': 0, 'b': 0.031, 'MVA_rating': 177.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '74', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '54.0', 'r': 0.073, 'x': 0.289, 'g': 0, 'b': 0.0738, 'MVA_rating': 99.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '75', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '54.0', 'r': 0.0869, 'x': 0.291, 'g': 0, 'b': 0.073, 'MVA_rating': 97.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '76', 'geometry': None},
        {'fromNode': '54.0', 'toNode': '55.0', 'r': 0.0169, 'x': 0.0707, 'g': 0, 'b': 0.0202, 'MVA_rating': 169.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '77', 'geometry': None},
        {'fromNode': '54.0', 'toNode': '56.0', 'r': 0.00275, 'x': 0.00955, 'g': 0, 'b': 0.00732, 'MVA_rating': 155.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '78', 'geometry': None},
        {'fromNode': '55.0', 'toNode': '56.0', 'r': 0.00488, 'x': 0.0151, 'g': 0, 'b': 0.00374, 'MVA_rating': 146.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '79', 'geometry': None},
        {'fromNode': '56.0', 'toNode': '57.0', 'r': 0.0343, 'x': 0.0966, 'g': 0, 'b': 0.0242, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '80', 'geometry': None},
        {'fromNode': '50.0', 'toNode': '57.0', 'r': 0.0474, 'x': 0.134, 'g': 0, 'b': 0.0332, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '81', 'geometry': None},
        {'fromNode': '56.0', 'toNode': '58.0', 'r': 0.0343, 'x': 0.0966, 'g': 0, 'b': 0.0242, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '82', 'geometry': None},
        {'fromNode': '51.0', 'toNode': '58.0', 'r': 0.0255, 'x': 0.0719, 'g': 0, 'b': 0.01788, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '83', 'geometry': None},
        {'fromNode': '54.0', 'toNode': '59.0', 'r': 0.0503, 'x': 0.2293, 'g': 0, 'b': 0.0598, 'MVA_rating': 125.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '84', 'geometry': None},
        {'fromNode': '56.0', 'toNode': '59.0', 'r': 0.0825, 'x': 0.251, 'g': 0, 'b': 0.0569, 'MVA_rating': 112.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '85', 'geometry': None},
        {'fromNode': '56.0', 'toNode': '59.0', 'r': 0.0803, 'x': 0.239, 'g': 0, 'b': 0.0536, 'MVA_rating': 117.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '86', 'geometry': None},
        {'fromNode': '55.0', 'toNode': '59.0', 'r': 0.04739, 'x': 0.2158, 'g': 0, 'b': 0.05646, 'MVA_rating': 133.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '87', 'geometry': None},
        {'fromNode': '59.0', 'toNode': '60.0', 'r': 0.0317, 'x': 0.145, 'g': 0, 'b': 0.0376, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '88', 'geometry': None},
        {'fromNode': '59.0', 'toNode': '61.0', 'r': 0.0328, 'x': 0.15, 'g': 0, 'b': 0.0388, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '89', 'geometry': None},
        {'fromNode': '60.0', 'toNode': '61.0', 'r': 0.00264, 'x': 0.0135, 'g': 0, 'b': 0.01456, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '90', 'geometry': None},
        {'fromNode': '60.0', 'toNode': '62.0', 'r': 0.0123, 'x': 0.0561, 'g': 0, 'b': 0.01468, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '91', 'geometry': None},
        {'fromNode': '61.0', 'toNode': '62.0', 'r': 0.00824, 'x': 0.0376, 'g': 0, 'b': 0.0098, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '92', 'geometry': None},
        {'fromNode': '63.0', 'toNode': '59.0', 'r': 0.0, 'x': 0.0386, 'g': 0, 'b': 0.0, 'MVA_rating': 760.0, 'kV_base': 138.0, 'm': 0.96, 'shift': 0.0, 'Line_id': '93', 'geometry': None},
        {'fromNode': '63.0', 'toNode': '64.0', 'r': 0.00172, 'x': 0.02, 'g': 0, 'b': 0.216, 'MVA_rating': 687.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '94', 'geometry': None},
        {'fromNode': '64.0', 'toNode': '61.0', 'r': 0.0, 'x': 0.0268, 'g': 0, 'b': 0.0, 'MVA_rating': 1095.0, 'kV_base': 138.0, 'm': 0.985, 'shift': 0.0, 'Line_id': '95', 'geometry': None},
        {'fromNode': '38.0', 'toNode': '65.0', 'r': 0.00901, 'x': 0.0986, 'g': 0, 'b': 1.046, 'MVA_rating': 297.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '96', 'geometry': None},
        {'fromNode': '64.0', 'toNode': '65.0', 'r': 0.00269, 'x': 0.0302, 'g': 0, 'b': 0.38, 'MVA_rating': 675.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '97', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '66.0', 'r': 0.018, 'x': 0.0919, 'g': 0, 'b': 0.0248, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '98', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '66.0', 'r': 0.018, 'x': 0.0919, 'g': 0, 'b': 0.0248, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '99', 'geometry': None},
        {'fromNode': '62.0', 'toNode': '66.0', 'r': 0.0482, 'x': 0.218, 'g': 0, 'b': 0.0578, 'MVA_rating': 132.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '100', 'geometry': None},
        {'fromNode': '62.0', 'toNode': '67.0', 'r': 0.0258, 'x': 0.117, 'g': 0, 'b': 0.031, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '101', 'geometry': None},
        {'fromNode': '65.0', 'toNode': '66.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 793.0, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '102', 'geometry': None},
        {'fromNode': '66.0', 'toNode': '67.0', 'r': 0.0224, 'x': 0.1015, 'g': 0, 'b': 0.02682, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '103', 'geometry': None},
        {'fromNode': '65.0', 'toNode': '68.0', 'r': 0.00138, 'x': 0.016, 'g': 0, 'b': 0.638, 'MVA_rating': 686.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '104', 'geometry': None},
        {'fromNode': '47.0', 'toNode': '69.0', 'r': 0.0844, 'x': 0.2778, 'g': 0, 'b': 0.07092, 'MVA_rating': 102.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '105', 'geometry': None},
        {'fromNode': '49.0', 'toNode': '69.0', 'r': 0.0985, 'x': 0.324, 'g': 0, 'b': 0.0828, 'MVA_rating': 87.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '106', 'geometry': None},
        {'fromNode': '68.0', 'toNode': '69.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 793.0, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '107', 'geometry': None},
        {'fromNode': '69.0', 'toNode': '70.0', 'r': 0.03, 'x': 0.127, 'g': 0, 'b': 0.122, 'MVA_rating': 170.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '108', 'geometry': None},
        {'fromNode': '24.0', 'toNode': '70.0', 'r': 0.00221, 'x': 0.4115, 'g': 0, 'b': 0.10198, 'MVA_rating': 72.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '109', 'geometry': None},
        {'fromNode': '70.0', 'toNode': '71.0', 'r': 0.00882, 'x': 0.0355, 'g': 0, 'b': 0.00878, 'MVA_rating': 166.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '110', 'geometry': None},
        {'fromNode': '24.0', 'toNode': '72.0', 'r': 0.0488, 'x': 0.196, 'g': 0, 'b': 0.0488, 'MVA_rating': 146.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '111', 'geometry': None},
        {'fromNode': '71.0', 'toNode': '72.0', 'r': 0.0446, 'x': 0.18, 'g': 0, 'b': 0.04444, 'MVA_rating': 159.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '112', 'geometry': None},
        {'fromNode': '71.0', 'toNode': '73.0', 'r': 0.00866, 'x': 0.0454, 'g': 0, 'b': 0.01178, 'MVA_rating': 188.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '113', 'geometry': None},
        {'fromNode': '70.0', 'toNode': '74.0', 'r': 0.0401, 'x': 0.1323, 'g': 0, 'b': 0.03368, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '114', 'geometry': None},
        {'fromNode': '70.0', 'toNode': '75.0', 'r': 0.0428, 'x': 0.141, 'g': 0, 'b': 0.036, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '115', 'geometry': None},
        {'fromNode': '69.0', 'toNode': '75.0', 'r': 0.0405, 'x': 0.122, 'g': 0, 'b': 0.124, 'MVA_rating': 145.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '116', 'geometry': None},
        {'fromNode': '74.0', 'toNode': '75.0', 'r': 0.0123, 'x': 0.0406, 'g': 0, 'b': 0.01034, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '117', 'geometry': None},
        {'fromNode': '76.0', 'toNode': '77.0', 'r': 0.0444, 'x': 0.148, 'g': 0, 'b': 0.0368, 'MVA_rating': 152.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '118', 'geometry': None},
        {'fromNode': '69.0', 'toNode': '77.0', 'r': 0.0309, 'x': 0.101, 'g': 0, 'b': 0.1038, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '119', 'geometry': None},
        {'fromNode': '75.0', 'toNode': '77.0', 'r': 0.0601, 'x': 0.1999, 'g': 0, 'b': 0.04978, 'MVA_rating': 141.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '120', 'geometry': None},
        {'fromNode': '77.0', 'toNode': '78.0', 'r': 0.00376, 'x': 0.0124, 'g': 0, 'b': 0.01264, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '121', 'geometry': None},
        {'fromNode': '78.0', 'toNode': '79.0', 'r': 0.00546, 'x': 0.0244, 'g': 0, 'b': 0.00648, 'MVA_rating': 174.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '122', 'geometry': None},
        {'fromNode': '77.0', 'toNode': '80.0', 'r': 0.017, 'x': 0.0485, 'g': 0, 'b': 0.0472, 'MVA_rating': 141.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '123', 'geometry': None},
        {'fromNode': '77.0', 'toNode': '80.0', 'r': 0.0294, 'x': 0.105, 'g': 0, 'b': 0.0228, 'MVA_rating': 157.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '124', 'geometry': None},
        {'fromNode': '79.0', 'toNode': '80.0', 'r': 0.0156, 'x': 0.0704, 'g': 0, 'b': 0.0187, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '125', 'geometry': None},
        {'fromNode': '68.0', 'toNode': '81.0', 'r': 0.00175, 'x': 0.0202, 'g': 0, 'b': 0.808, 'MVA_rating': 684.0, 'kV_base': 345.0, 'm': 1, 'shift': 0, 'Line_id': '126', 'geometry': None},
        {'fromNode': '81.0', 'toNode': '80.0', 'r': 0.0, 'x': 0.037, 'g': 0, 'b': 0.0, 'MVA_rating': 793.0, 'kV_base': 138.0, 'm': 0.935, 'shift': 0.0, 'Line_id': '127', 'geometry': None},
        {'fromNode': '77.0', 'toNode': '82.0', 'r': 0.0298, 'x': 0.0853, 'g': 0, 'b': 0.08174, 'MVA_rating': 141.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '128', 'geometry': None},
        {'fromNode': '82.0', 'toNode': '83.0', 'r': 0.0112, 'x': 0.03665, 'g': 0, 'b': 0.03796, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '129', 'geometry': None},
        {'fromNode': '83.0', 'toNode': '84.0', 'r': 0.0625, 'x': 0.132, 'g': 0, 'b': 0.0258, 'MVA_rating': 122.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '130', 'geometry': None},
        {'fromNode': '83.0', 'toNode': '85.0', 'r': 0.043, 'x': 0.148, 'g': 0, 'b': 0.0348, 'MVA_rating': 154.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '131', 'geometry': None},
        {'fromNode': '84.0', 'toNode': '85.0', 'r': 0.0302, 'x': 0.0641, 'g': 0, 'b': 0.01234, 'MVA_rating': 122.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '132', 'geometry': None},
        {'fromNode': '85.0', 'toNode': '86.0', 'r': 0.035, 'x': 0.123, 'g': 0, 'b': 0.0276, 'MVA_rating': 156.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '133', 'geometry': None},
        {'fromNode': '86.0', 'toNode': '87.0', 'r': 0.02828, 'x': 0.2074, 'g': 0, 'b': 0.0445, 'MVA_rating': 141.0, 'kV_base': 161.0, 'm': 1.0, 'shift': 0.0, 'Line_id': '134', 'geometry': None},
        {'fromNode': '85.0', 'toNode': '88.0', 'r': 0.02, 'x': 0.102, 'g': 0, 'b': 0.0276, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '135', 'geometry': None},
        {'fromNode': '85.0', 'toNode': '89.0', 'r': 0.0239, 'x': 0.173, 'g': 0, 'b': 0.047, 'MVA_rating': 168.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '136', 'geometry': None},
        {'fromNode': '88.0', 'toNode': '89.0', 'r': 0.0139, 'x': 0.0712, 'g': 0, 'b': 0.01934, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '137', 'geometry': None},
        {'fromNode': '89.0', 'toNode': '90.0', 'r': 0.0518, 'x': 0.188, 'g': 0, 'b': 0.0528, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '138', 'geometry': None},
        {'fromNode': '89.0', 'toNode': '90.0', 'r': 0.0238, 'x': 0.0997, 'g': 0, 'b': 0.106, 'MVA_rating': 169.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '139', 'geometry': None},
        {'fromNode': '90.0', 'toNode': '91.0', 'r': 0.0254, 'x': 0.0836, 'g': 0, 'b': 0.0214, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '140', 'geometry': None},
        {'fromNode': '89.0', 'toNode': '92.0', 'r': 0.0099, 'x': 0.0505, 'g': 0, 'b': 0.0548, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '141', 'geometry': None},
        {'fromNode': '89.0', 'toNode': '92.0', 'r': 0.0393, 'x': 0.1581, 'g': 0, 'b': 0.0414, 'MVA_rating': 166.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '142', 'geometry': None},
        {'fromNode': '91.0', 'toNode': '92.0', 'r': 0.0387, 'x': 0.1272, 'g': 0, 'b': 0.03268, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '143', 'geometry': None},
        {'fromNode': '92.0', 'toNode': '93.0', 'r': 0.0258, 'x': 0.0848, 'g': 0, 'b': 0.0218, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '144', 'geometry': None},
        {'fromNode': '92.0', 'toNode': '94.0', 'r': 0.0481, 'x': 0.158, 'g': 0, 'b': 0.0406, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '145', 'geometry': None},
        {'fromNode': '93.0', 'toNode': '94.0', 'r': 0.0223, 'x': 0.0732, 'g': 0, 'b': 0.01876, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '146', 'geometry': None},
        {'fromNode': '94.0', 'toNode': '95.0', 'r': 0.0132, 'x': 0.0434, 'g': 0, 'b': 0.0111, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '147', 'geometry': None},
        {'fromNode': '80.0', 'toNode': '96.0', 'r': 0.0356, 'x': 0.182, 'g': 0, 'b': 0.0494, 'MVA_rating': 159.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '148', 'geometry': None},
        {'fromNode': '82.0', 'toNode': '96.0', 'r': 0.0162, 'x': 0.053, 'g': 0, 'b': 0.0544, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '149', 'geometry': None},
        {'fromNode': '94.0', 'toNode': '96.0', 'r': 0.0269, 'x': 0.0869, 'g': 0, 'b': 0.023, 'MVA_rating': 149.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '150', 'geometry': None},
        {'fromNode': '80.0', 'toNode': '97.0', 'r': 0.0183, 'x': 0.0934, 'g': 0, 'b': 0.0254, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '151', 'geometry': None},
        {'fromNode': '80.0', 'toNode': '98.0', 'r': 0.0238, 'x': 0.108, 'g': 0, 'b': 0.0286, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '152', 'geometry': None},
        {'fromNode': '80.0', 'toNode': '99.0', 'r': 0.0454, 'x': 0.206, 'g': 0, 'b': 0.0546, 'MVA_rating': 140.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '153', 'geometry': None},
        {'fromNode': '92.0', 'toNode': '100.0', 'r': 0.0648, 'x': 0.295, 'g': 0, 'b': 0.0472, 'MVA_rating': 98.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '154', 'geometry': None},
        {'fromNode': '94.0', 'toNode': '100.0', 'r': 0.0178, 'x': 0.058, 'g': 0, 'b': 0.0604, 'MVA_rating': 150.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '155', 'geometry': None},
        {'fromNode': '95.0', 'toNode': '96.0', 'r': 0.0171, 'x': 0.0547, 'g': 0, 'b': 0.01474, 'MVA_rating': 149.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '156', 'geometry': None},
        {'fromNode': '96.0', 'toNode': '97.0', 'r': 0.0173, 'x': 0.0885, 'g': 0, 'b': 0.024, 'MVA_rating': 186.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '157', 'geometry': None},
        {'fromNode': '98.0', 'toNode': '100.0', 'r': 0.0397, 'x': 0.179, 'g': 0, 'b': 0.0476, 'MVA_rating': 160.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '158', 'geometry': None},
        {'fromNode': '99.0', 'toNode': '100.0', 'r': 0.018, 'x': 0.0813, 'g': 0, 'b': 0.0216, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '159', 'geometry': None},
        {'fromNode': '100.0', 'toNode': '101.0', 'r': 0.0277, 'x': 0.1262, 'g': 0, 'b': 0.0328, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '160', 'geometry': None},
        {'fromNode': '92.0', 'toNode': '102.0', 'r': 0.0123, 'x': 0.0559, 'g': 0, 'b': 0.01464, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '161', 'geometry': None},
        {'fromNode': '101.0', 'toNode': '102.0', 'r': 0.0246, 'x': 0.112, 'g': 0, 'b': 0.0294, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '162', 'geometry': None},
        {'fromNode': '100.0', 'toNode': '103.0', 'r': 0.016, 'x': 0.0525, 'g': 0, 'b': 0.0536, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '163', 'geometry': None},
        {'fromNode': '100.0', 'toNode': '104.0', 'r': 0.0451, 'x': 0.204, 'g': 0, 'b': 0.0541, 'MVA_rating': 141.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '164', 'geometry': None},
        {'fromNode': '103.0', 'toNode': '104.0', 'r': 0.0466, 'x': 0.1584, 'g': 0, 'b': 0.0407, 'MVA_rating': 153.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '165', 'geometry': None},
        {'fromNode': '103.0', 'toNode': '105.0', 'r': 0.0535, 'x': 0.1625, 'g': 0, 'b': 0.0408, 'MVA_rating': 145.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '166', 'geometry': None},
        {'fromNode': '100.0', 'toNode': '106.0', 'r': 0.0605, 'x': 0.229, 'g': 0, 'b': 0.062, 'MVA_rating': 124.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '167', 'geometry': None},
        {'fromNode': '104.0', 'toNode': '105.0', 'r': 0.00994, 'x': 0.0378, 'g': 0, 'b': 0.00986, 'MVA_rating': 161.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '168', 'geometry': None},
        {'fromNode': '105.0', 'toNode': '106.0', 'r': 0.014, 'x': 0.0547, 'g': 0, 'b': 0.01434, 'MVA_rating': 164.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '169', 'geometry': None},
        {'fromNode': '105.0', 'toNode': '107.0', 'r': 0.053, 'x': 0.183, 'g': 0, 'b': 0.0472, 'MVA_rating': 154.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '170', 'geometry': None},
        {'fromNode': '105.0', 'toNode': '108.0', 'r': 0.0261, 'x': 0.0703, 'g': 0, 'b': 0.01844, 'MVA_rating': 137.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '171', 'geometry': None},
        {'fromNode': '106.0', 'toNode': '107.0', 'r': 0.053, 'x': 0.183, 'g': 0, 'b': 0.0472, 'MVA_rating': 154.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '172', 'geometry': None},
        {'fromNode': '108.0', 'toNode': '109.0', 'r': 0.0105, 'x': 0.0288, 'g': 0, 'b': 0.0076, 'MVA_rating': 138.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '173', 'geometry': None},
        {'fromNode': '103.0', 'toNode': '110.0', 'r': 0.03906, 'x': 0.1813, 'g': 0, 'b': 0.0461, 'MVA_rating': 159.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '174', 'geometry': None},
        {'fromNode': '109.0', 'toNode': '110.0', 'r': 0.0278, 'x': 0.0762, 'g': 0, 'b': 0.0202, 'MVA_rating': 138.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '175', 'geometry': None},
        {'fromNode': '110.0', 'toNode': '111.0', 'r': 0.022, 'x': 0.0755, 'g': 0, 'b': 0.02, 'MVA_rating': 154.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '176', 'geometry': None},
        {'fromNode': '110.0', 'toNode': '112.0', 'r': 0.0247, 'x': 0.064, 'g': 0, 'b': 0.062, 'MVA_rating': 135.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '177', 'geometry': None},
        {'fromNode': '17.0', 'toNode': '113.0', 'r': 0.00913, 'x': 0.0301, 'g': 0, 'b': 0.00768, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '178', 'geometry': None},
        {'fromNode': '32.0', 'toNode': '113.0', 'r': 0.0615, 'x': 0.203, 'g': 0, 'b': 0.0518, 'MVA_rating': 139.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '179', 'geometry': None},
        {'fromNode': '32.0', 'toNode': '114.0', 'r': 0.0135, 'x': 0.0612, 'g': 0, 'b': 0.01628, 'MVA_rating': 176.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '180', 'geometry': None},
        {'fromNode': '27.0', 'toNode': '115.0', 'r': 0.0164, 'x': 0.0741, 'g': 0, 'b': 0.01972, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '181', 'geometry': None},
        {'fromNode': '114.0', 'toNode': '115.0', 'r': 0.0023, 'x': 0.0104, 'g': 0, 'b': 0.00276, 'MVA_rating': 175.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '182', 'geometry': None},
        {'fromNode': '68.0', 'toNode': '116.0', 'r': 0.00034, 'x': 0.00405, 'g': 0, 'b': 0.164, 'MVA_rating': 7218.0, 'kV_base': 138.0, 'm': 1.0, 'shift': 0.0, 'Line_id': '183', 'geometry': None},
        {'fromNode': '12.0', 'toNode': '117.0', 'r': 0.0329, 'x': 0.14, 'g': 0, 'b': 0.0358, 'MVA_rating': 170.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '184', 'geometry': None},
        {'fromNode': '75.0', 'toNode': '118.0', 'r': 0.0145, 'x': 0.0481, 'g': 0, 'b': 0.01198, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '185', 'geometry': None},
        {'fromNode': '76.0', 'toNode': '118.0', 'r': 0.0164, 'x': 0.0544, 'g': 0, 'b': 0.01356, 'MVA_rating': 151.0, 'kV_base': 138.0, 'm': 1, 'shift': 0, 'Line_id': '186', 'geometry': None}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC_data = [
        {'Node_id': '1', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '2', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '3', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '4', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '5', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '6', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '7', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '8', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '9', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '10', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '11', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '12', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '13', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '14', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '15', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '16', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '17', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '18', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '19', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '20', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '21', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '22', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '23', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '24', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '25', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '26', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '27', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '28', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '29', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '30', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '31', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '32', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9},
        {'Node_id': '33', 'kV_base': 345, 'Umax': 1.1, 'Umin': 0.9}
    ]

    nodes_DC = pd.DataFrame(nodes_DC_data)

    lines_DC_data = [
        {'fromNode': '1', 'toNode': '2', 'r': 0.0303, 'MVA_rating': 151.0, 'Line_id': 'DC_1','Mono_Bi_polar':'sm', 'cost': 3.03},
        {'fromNode': '1', 'toNode': '3', 'r': 0.0129, 'MVA_rating': 151.0, 'Line_id': 'DC_2','Mono_Bi_polar':'sm', 'cost': 1.29},
        {'fromNode': '3', 'toNode': '5', 'r': 0.00176, 'MVA_rating': 176.0, 'Line_id': 'DC_3','Mono_Bi_polar':'sm', 'cost': 0.18},
        {'fromNode': '3', 'toNode': '5', 'r': 0.0241, 'MVA_rating': 175.0, 'Line_id': 'DC_4','Mono_Bi_polar':'sm', 'cost': 2.41},
        {'fromNode': '5', 'toNode': '6', 'r': 0.0119, 'MVA_rating': 176.0, 'Line_id': 'DC_5','Mono_Bi_polar':'sm', 'cost': 1.19},
        {'fromNode': '6', 'toNode': '7', 'r': 0.00459, 'MVA_rating': 176.0, 'Line_id': 'DC_6','Mono_Bi_polar':'sm', 'cost': 0.46},
        {'fromNode': '8', 'toNode': '9', 'r': 0.00244, 'MVA_rating': 711.0, 'Line_id': 'DC_7','Mono_Bi_polar':'sm', 'cost': 0.24},
        {'fromNode': '8', 'toNode': '5', 'r': 0.000001, 'MVA_rating': 1099.0, 'Line_id': 'DC_8','Mono_Bi_polar':'sm', 'cost': 0.00},
        {'fromNode': '9', 'toNode': '10', 'r': 0.00258, 'MVA_rating': 710.0, 'Line_id': 'DC_9','Mono_Bi_polar':'sm', 'cost': 0.26},
        {'fromNode': '4', 'toNode': '11', 'r': 0.0209, 'MVA_rating': 151.0, 'Line_id': 'DC_10','Mono_Bi_polar':'sm', 'cost': 2.09},
        {'fromNode': '11', 'toNode': '12', 'r': 0.00595, 'MVA_rating': 151.0, 'Line_id': 'DC_11','Mono_Bi_polar':'sm', 'cost': 0.60},
        {'fromNode': '2', 'toNode': '12', 'r': 0.0187, 'MVA_rating': 151.0, 'Line_id': 'DC_12','Mono_Bi_polar':'sm', 'cost': 1.87},
        {'fromNode': '3', 'toNode': '12', 'r': 0.0484, 'MVA_rating': 151.0, 'Line_id': 'DC_13','Mono_Bi_polar':'sm', 'cost': 4.84},
        {'fromNode': '7', 'toNode': '12', 'r': 0.00862, 'MVA_rating': 164.0, 'Line_id': 'DC_14','Mono_Bi_polar':'sm', 'cost': 0.86},
        {'fromNode': '11', 'toNode': '13', 'r': 0.02225, 'MVA_rating': 151.0, 'Line_id': 'DC_15','Mono_Bi_polar':'sm', 'cost': 2.23},
        {'fromNode': '12', 'toNode': '14', 'r': 0.0215, 'MVA_rating': 151.0, 'Line_id': 'DC_16','Mono_Bi_polar':'sm', 'cost': 2.15},
        {'fromNode': '13', 'toNode': '15', 'r': 0.0744, 'MVA_rating': 115.0, 'Line_id': 'DC_17','Mono_Bi_polar':'sm', 'cost': 7.44},
        {'fromNode': '12', 'toNode': '15', 'r': 0.0595, 'MVA_rating': 144.0, 'Line_id': 'DC_18','Mono_Bi_polar':'sm', 'cost': 5.95},
        {'fromNode': '12', 'toNode': '16', 'r': 0.0212, 'MVA_rating': 164.0, 'Line_id': 'DC_19','Mono_Bi_polar':'sm', 'cost': 2.12},
        {'fromNode': '15', 'toNode': '17', 'r': 0.0132, 'MVA_rating': 151.0, 'Line_id': 'DC_20','Mono_Bi_polar':'sm', 'cost': 1.32},
        {'fromNode': '16', 'toNode': '17', 'r': 0.0454, 'MVA_rating': 158.0, 'Line_id': 'DC_21','Mono_Bi_polar':'sm', 'cost': 4.54},
        {'fromNode': '17', 'toNode': '18', 'r': 0.0123, 'MVA_rating': 167.0, 'Line_id': 'DC_22','Mono_Bi_polar':'sm', 'cost': 1.23},
        {'fromNode': '18', 'toNode': '19', 'r': 0.01119, 'MVA_rating': 173.0, 'Line_id': 'DC_23','Mono_Bi_polar':'sm', 'cost': 1.12},
        {'fromNode': '19', 'toNode': '20', 'r': 0.0252, 'MVA_rating': 178.0, 'Line_id': 'DC_24','Mono_Bi_polar':'sm', 'cost': 2.52},
        {'fromNode': '15', 'toNode': '19', 'r': 0.012, 'MVA_rating': 151.0, 'Line_id': 'DC_25','Mono_Bi_polar':'sm', 'cost': 1.20},
        {'fromNode': '20', 'toNode': '21', 'r': 0.0183, 'MVA_rating': 177.0, 'Line_id': 'DC_26','Mono_Bi_polar':'sm', 'cost': 1.83},
        {'fromNode': '21', 'toNode': '22', 'r': 0.0209, 'MVA_rating': 178.0, 'Line_id': 'DC_27','Mono_Bi_polar':'sm', 'cost': 2.09},
        {'fromNode': '22', 'toNode': '23', 'r': 0.0342, 'MVA_rating': 178.0, 'Line_id': 'DC_28','Mono_Bi_polar':'sm', 'cost': 3.42},
        {'fromNode': '23', 'toNode': '24', 'r': 0.0135, 'MVA_rating': 158.0, 'Line_id': 'DC_29','Mono_Bi_polar':'sm', 'cost': 1.35},
        {'fromNode': '23', 'toNode': '25', 'r': 0.0156, 'MVA_rating': 186.0, 'Line_id': 'DC_30','Mono_Bi_polar':'sm', 'cost': 1.56},
        {'fromNode': '26', 'toNode': '25', 'r': 0.000001, 'MVA_rating': 768.0, 'Line_id': 'DC_31','Mono_Bi_polar':'sm', 'cost': 0.00},
        {'fromNode': '25', 'toNode': '27', 'r': 0.0318, 'MVA_rating': 177.0, 'Line_id': 'DC_32','Mono_Bi_polar':'sm', 'cost': 3.18},
        {'fromNode': '27', 'toNode': '28', 'r': 0.01913, 'MVA_rating': 174.0, 'Line_id': 'DC_33','Mono_Bi_polar':'sm', 'cost': 1.91},
        {'fromNode': '28', 'toNode': '29', 'r': 0.0237, 'MVA_rating': 165.0, 'Line_id': 'DC_34','Mono_Bi_polar':'sm', 'cost': 2.37},
        {'fromNode': '30', 'toNode': '17', 'r': 0.00431, 'MVA_rating': 580.0, 'Line_id': 'DC_35','Mono_Bi_polar':'sm', 'cost': 0.43},
        {'fromNode': '26', 'toNode': '30', 'r': 0.00799, 'MVA_rating': 340.0, 'Line_id': 'DC_36','Mono_Bi_polar':'sm', 'cost': 0.80},
        {'fromNode': '17', 'toNode': '31', 'r': 0.0474, 'MVA_rating': 151.0, 'Line_id': 'DC_37','Mono_Bi_polar':'sm', 'cost': 4.74},
        {'fromNode': '29', 'toNode': '31', 'r': 0.0108, 'MVA_rating': 146.0, 'Line_id': 'DC_38','Mono_Bi_polar':'sm', 'cost': 1.08},
        {'fromNode': '23', 'toNode': '32', 'r': 0.0317, 'MVA_rating': 158.0, 'Line_id': 'DC_39','Mono_Bi_polar':'sm', 'cost': 3.17},
        {'fromNode': '31', 'toNode': '32', 'r': 0.0298, 'MVA_rating': 151.0, 'Line_id': 'DC_40','Mono_Bi_polar':'sm', 'cost': 2.98},
        {'fromNode': '27', 'toNode': '32', 'r': 0.0229, 'MVA_rating': 151.0, 'Line_id': 'DC_41','Mono_Bi_polar':'sm', 'cost': 2.29},
        {'fromNode': '15', 'toNode': '33', 'r': 0.038, 'MVA_rating': 150.0, 'Line_id': 'DC_42','Mono_Bi_polar':'sm', 'cost': 3.80}
    ]
    lines_DC = pd.DataFrame(lines_DC_data)

    Converters_ACDC_data = [
        {'Conv_id':'Conv_1','DC_node':'1','AC_node':'1.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_2','DC_node':'2','AC_node':'2.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},  
        {'Conv_id':'Conv_3','DC_node':'3','AC_node':'3.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_4','DC_node':'4','AC_node':'4.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_5','DC_node':'5','AC_node':'5.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_6','DC_node':'6','AC_node':'6.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_7','DC_node':'7','AC_node':'7.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_8','DC_node':'8','AC_node':'8.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_9','DC_node':'9','AC_node':'9.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_10','DC_node':'10','AC_node':'10.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_11','DC_node':'11','AC_node':'11.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_12','DC_node':'12','AC_node':'12.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_13','DC_node':'13','AC_node':'13.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_14','DC_node':'14','AC_node':'14.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_15','DC_node':'15','AC_node':'15.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_16','DC_node':'16','AC_node':'16.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_17','DC_node':'17','AC_node':'17.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_18','DC_node':'18','AC_node':'18.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_19','DC_node':'19','AC_node':'19.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_20','DC_node':'20','AC_node':'20.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_21','DC_node':'21','AC_node':'21.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_22','DC_node':'22','AC_node':'22.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_23','DC_node':'23','AC_node':'23.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_24','DC_node':'24','AC_node':'24.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_25','DC_node':'25','AC_node':'25.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_26','DC_node':'26','AC_node':'26.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_27','DC_node':'27','AC_node':'27.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_28','DC_node':'28','AC_node':'28.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_29','DC_node':'29','AC_node':'29.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_30','DC_node':'30','AC_node':'30.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_31','DC_node':'31','AC_node':'31.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_32','DC_node':'32','AC_node':'32.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100},
        {'Conv_id':'Conv_33','DC_node':'33','AC_node':'33.0','T_r':0.01,'T_x':0.01,'Filter_b':0.01,'PR_r':0.01,'PR_x':0.01,'reactor':1,'basekVac':345,'Ucmax':1.1,'Ucmin':0.9,'lossa':1.1033,'lossb':0.887,'losscrect':2.885,'losscinv':2.885,'MVA_rating':100}
    ]

    Converters_ACDC = pd.DataFrame(Converters_ACDC_data)
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='pu')
    grid.name = 'case118_TEP'
    
    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    
    
    
    # Add Generators
    pyf.add_gen(grid, '1.0', '1', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-5.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '4.0', '2', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '6.0', '3', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-13.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '8.0', '4', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '10.0', '5', lf=20.0, qf=0.0222222222, MWmax=550.0, MWmin=0.0, MVArmax=200.0, MVArmin=-147.0, PsetMW=450.0, QsetMVA=0.0)
    pyf.add_gen(grid, '12.0', '6', lf=20.0, qf=0.117647059, MWmax=185.0, MWmin=0.0, MVArmax=120.0, MVArmin=-35.0, PsetMW=85.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15.0', '7', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=30.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '18.0', '8', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-16.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '19.0', '9', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '24.0', '10', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '25.0', '11', lf=20.0, qf=0.0454545455, MWmax=320.0, MWmin=0.0, MVArmax=140.0, MVArmin=-47.0, PsetMW=220.00000000000003, QsetMVA=0.0)
    pyf.add_gen(grid, '26.0', '12', lf=20.0, qf=0.0318471338, MWmax=413.99999999999994, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=314.0, QsetMVA=0.0)
    pyf.add_gen(grid, '27.0', '13', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '31.0', '14', lf=20.0, qf=1.42857143, MWmax=107.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=7.000000000000001, QsetMVA=0.0)
    pyf.add_gen(grid, '32.0', '15', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=42.0, MVArmin=-14.000000000000002, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '34.0', '16', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '36.0', '17', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '40.0', '18', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '42.0', '19', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '46.0', '20', lf=20.0, qf=0.526315789, MWmax=119.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=19.0, QsetMVA=0.0)
    pyf.add_gen(grid, '49.0', '21', lf=20.0, qf=0.0490196078, MWmax=304.0, MWmin=0.0, MVArmax=210.0, MVArmin=-85.0, PsetMW=204.0, QsetMVA=0.0)
    pyf.add_gen(grid, '54.0', '22', lf=20.0, qf=0.208333333, MWmax=148.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=48.0, QsetMVA=0.0)
    pyf.add_gen(grid, '55.0', '23', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '56.0', '24', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '59.0', '25', lf=20.0, qf=0.064516129, MWmax=254.99999999999997, MWmin=0.0, MVArmax=180.0, MVArmin=-60.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '61.0', '26', lf=20.0, qf=0.0625, MWmax=260.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=160.0, QsetMVA=0.0)
    pyf.add_gen(grid, '62.0', '27', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=20.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '65.0', '28', lf=20.0, qf=0.0255754476, MWmax=491.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=391.0, QsetMVA=0.0)
    pyf.add_gen(grid, '66.0', '29', lf=20.0, qf=0.0255102041, MWmax=492.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=392.0, QsetMVA=0.0)
    pyf.add_gen(grid, '69.0', '30', lf=20.0, qf=0.0193648335, MWmax=805.1999999999999, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=516.4, QsetMVA=0.0)
    pyf.add_gen(grid, '70.0', '31', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=32.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '72.0', '32', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '73.0', '33', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '74.0', '34', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-6.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '76.0', '35', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '77.0', '36', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=70.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '80.0', '37', lf=20.0, qf=0.0209643606, MWmax=577.0, MWmin=0.0, MVArmax=280.0, MVArmin=-165.0, PsetMW=476.99999999999994, QsetMVA=0.0)
    pyf.add_gen(grid, '85.0', '38', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '87.0', '39', lf=20.0, qf=2.5, MWmax=104.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=4.0, QsetMVA=0.0)
    pyf.add_gen(grid, '89.0', '40', lf=20.0, qf=0.0164744646, MWmax=707.0, MWmin=0.0, MVArmax=300.0, MVArmin=-210.0, PsetMW=607.0, QsetMVA=0.0)
    pyf.add_gen(grid, '90.0', '41', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '91.0', '42', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '92.0', '43', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-3.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '99.0', '44', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '100.0', '45', lf=20.0, qf=0.0396825397, MWmax=352.0, MWmin=0.0, MVArmax=155.0, MVArmin=-50.0, PsetMW=252.0, QsetMVA=0.0)
    pyf.add_gen(grid, '103.0', '46', lf=20.0, qf=0.25, MWmax=140.0, MWmin=0.0, MVArmax=40.0, MVArmin=-15.0, PsetMW=40.0, QsetMVA=0.0)
    pyf.add_gen(grid, '104.0', '47', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '105.0', '48', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '107.0', '49', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-200.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '110.0', '50', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '111.0', '51', lf=20.0, qf=0.277777778, MWmax=136.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=36.0, QsetMVA=0.0)
    pyf.add_gen(grid, '112.0', '52', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '113.0', '53', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '116.0', '54', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=0.0, QsetMVA=0.0)
    
    
    # Expand Elements
    
    lines_DC.set_index('Line_id', inplace=True)
    Conv_cost = 0.001 #million EUR
    if exp == 'All':
        for line in list(grid.lines_DC):  # Create a copy of the list
            name = line.name
            line_cost = lines_DC.loc[name,'cost']/4*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
        for conv in list(grid.Converters_ACDC):
            name = conv.name
            conv_cost = Conv_cost*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max*3,base_cost=conv_cost)
    else:
        for line in list(grid.lines_DC):  # Create a copy of the list
            name = line.name
            if name not in exp:
                continue
            line_cost = lines_DC.loc[name,'cost']/4*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
        for conv in list(grid.Converters_ACDC):  
            name = conv.name
            if name not in exp:
                continue
            conv_cost = Conv_cost*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max*3,base_cost=conv_cost)


    # Return the grid
    return grid,res
