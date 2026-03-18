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
def case118_TEP(exp='All',N_b=1,N_i=1,N_max=5,kappa=0.5):    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.51, 'Reactive_load': 0.27, 'Node_id': '1', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.2, 'Reactive_load': 0.09, 'Node_id': '2', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.39, 'Reactive_load': 0.1, 'Node_id': '3', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.39, 'Reactive_load': 0.12, 'Node_id': '4', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.4},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.52, 'Reactive_load': 0.22, 'Node_id': '6', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.19, 'Reactive_load': 0.02, 'Node_id': '7', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.28, 'Reactive_load': 0.0, 'Node_id': '8', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '9', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '10', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.7, 'Reactive_load': 0.23, 'Node_id': '11', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.47, 'Reactive_load': 0.1, 'Node_id': '12', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.34, 'Reactive_load': 0.16, 'Node_id': '13', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.14, 'Reactive_load': 0.01, 'Node_id': '14', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.9, 'Reactive_load': 0.3, 'Node_id': '15', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.25, 'Reactive_load': 0.1, 'Node_id': '16', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.11, 'Reactive_load': 0.03, 'Node_id': '17', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.6, 'Reactive_load': 0.34, 'Node_id': '18', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.962, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.45, 'Reactive_load': 0.25, 'Node_id': '19', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.18, 'Reactive_load': 0.03, 'Node_id': '20', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.14, 'Reactive_load': 0.08, 'Node_id': '21', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.1, 'Reactive_load': 0.05, 'Node_id': '22', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.07, 'Reactive_load': 0.03, 'Node_id': '23', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.992, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.13, 'Reactive_load': 0.0, 'Node_id': '24', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '25', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '26', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.968, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.71, 'Reactive_load': 0.13, 'Node_id': '27', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.17, 'Reactive_load': 0.07, 'Node_id': '28', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.24, 'Reactive_load': 0.04, 'Node_id': '29', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '30', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.967, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.43, 'Reactive_load': 0.27, 'Node_id': '31', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.963, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.59, 'Reactive_load': 0.23, 'Node_id': '32', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.23, 'Reactive_load': 0.09, 'Node_id': '33', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.984, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.59, 'Reactive_load': 0.26, 'Node_id': '34', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.14},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.33, 'Reactive_load': 0.09, 'Node_id': '35', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.31, 'Reactive_load': 0.17, 'Node_id': '36', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '37', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': -0.25},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '38', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.27, 'Reactive_load': 0.11, 'Node_id': '39', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.97, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.66, 'Reactive_load': 0.23, 'Node_id': '40', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.37, 'Reactive_load': 0.1, 'Node_id': '41', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.96, 'Reactive_load': 0.23, 'Node_id': '42', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.18, 'Reactive_load': 0.07, 'Node_id': '43', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.16, 'Reactive_load': 0.08, 'Node_id': '44', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.53, 'Reactive_load': 0.22, 'Node_id': '45', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.28, 'Reactive_load': 0.1, 'Node_id': '46', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.34, 'Reactive_load': 0.0, 'Node_id': '47', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.2, 'Reactive_load': 0.11, 'Node_id': '48', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.15},
        {'type': 'PV', 'Voltage_0': 1.025, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.87, 'Reactive_load': 0.3, 'Node_id': '49', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.17, 'Reactive_load': 0.04, 'Node_id': '50', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.17, 'Reactive_load': 0.08, 'Node_id': '51', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.18, 'Reactive_load': 0.05, 'Node_id': '52', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.23, 'Reactive_load': 0.11, 'Node_id': '53', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.955, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 1.13, 'Reactive_load': 0.32, 'Node_id': '54', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.63, 'Reactive_load': 0.22, 'Node_id': '55', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.954, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.84, 'Reactive_load': 0.18, 'Node_id': '56', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '57', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.12, 'Reactive_load': 0.03, 'Node_id': '58', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 2.77, 'Reactive_load': 1.13, 'Node_id': '59', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.78, 'Reactive_load': 0.03, 'Node_id': '60', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.995, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '61', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.998, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.77, 'Reactive_load': 0.14, 'Node_id': '62', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '63', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '64', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '65', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.05, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.39, 'Reactive_load': 0.18, 'Node_id': '66', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.28, 'Reactive_load': 0.07, 'Node_id': '67', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '68', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'Slack', 'Voltage_0': 1.035, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '69', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.984, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.66, 'Reactive_load': 0.2, 'Node_id': '70', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '71', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.12, 'Reactive_load': 0.0, 'Node_id': '72', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.991, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '73', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.958, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.68, 'Reactive_load': 0.27, 'Node_id': '74', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.12},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.47, 'Reactive_load': 0.11, 'Node_id': '75', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.943, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.68, 'Reactive_load': 0.36, 'Node_id': '76', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.006, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.61, 'Reactive_load': 0.28, 'Node_id': '77', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.71, 'Reactive_load': 0.26, 'Node_id': '78', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.39, 'Reactive_load': 0.32, 'Node_id': '79', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2},
        {'type': 'PV', 'Voltage_0': 1.04, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 1.3, 'Reactive_load': 0.26, 'Node_id': '80', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 345.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '81', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.54, 'Reactive_load': 0.27, 'Node_id': '82', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.2, 'Reactive_load': 0.1, 'Node_id': '83', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.1},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.11, 'Reactive_load': 0.07, 'Node_id': '84', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.24, 'Reactive_load': 0.15, 'Node_id': '85', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.21, 'Reactive_load': 0.1, 'Node_id': '86', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.015, 'theta_0': 0.0, 'kV_base': 161.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '87', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.48, 'Reactive_load': 0.1, 'Node_id': '88', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '89', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.985, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 1.63, 'Reactive_load': 0.42, 'Node_id': '90', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.1, 'Reactive_load': 0.0, 'Node_id': '91', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.99, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.65, 'Reactive_load': 0.1, 'Node_id': '92', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.12, 'Reactive_load': 0.07, 'Node_id': '93', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.3, 'Reactive_load': 0.16, 'Node_id': '94', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.42, 'Reactive_load': 0.31, 'Node_id': '95', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.38, 'Reactive_load': 0.15, 'Node_id': '96', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.15, 'Reactive_load': 0.09, 'Node_id': '97', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.34, 'Reactive_load': 0.08, 'Node_id': '98', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.42, 'Reactive_load': 0.0, 'Node_id': '99', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.017, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.37, 'Reactive_load': 0.18, 'Node_id': '100', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.22, 'Reactive_load': 0.15, 'Node_id': '101', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.05, 'Reactive_load': 0.03, 'Node_id': '102', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.23, 'Reactive_load': 0.16, 'Node_id': '103', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.971, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.38, 'Reactive_load': 0.25, 'Node_id': '104', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.965, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.31, 'Reactive_load': 0.26, 'Node_id': '105', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.2},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.43, 'Reactive_load': 0.16, 'Node_id': '106', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.952, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.5, 'Reactive_load': 0.12, 'Node_id': '107', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.02, 'Reactive_load': 0.01, 'Node_id': '108', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '109', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.973, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.39, 'Reactive_load': 0.3, 'Node_id': '110', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.06},
        {'type': 'PV', 'Voltage_0': 0.98, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '111', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.975, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.68, 'Reactive_load': 0.13, 'Node_id': '112', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 0.993, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.06, 'Reactive_load': 0.0, 'Node_id': '113', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.08, 'Reactive_load': 0.03, 'Node_id': '114', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.22, 'Reactive_load': 0.07, 'Node_id': '115', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PV', 'Voltage_0': 1.005, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 1.84, 'Reactive_load': 0.0, 'Node_id': '116', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.2, 'Reactive_load': 0.08, 'Node_id': '117', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0},
        {'type': 'PQ', 'Voltage_0': 1.01, 'theta_0': 0.0, 'kV_base': 138.0,  'Power_load': 0.33, 'Reactive_load': 0.15, 'Node_id': '118', 'Umin': 0.94, 'Umax': 1.06, 'Gs': 0.0, 'Bs': 0.0}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
    {'Line_id': 'L_1', 'fromNode': '1', 'toNode': '2', 'r': 0.0303, 'x': 0.0999, 'b': 0.0254, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.88},
    {'Line_id': 'L_2', 'fromNode': '1', 'toNode': '3', 'r': 0.0129, 'x': 0.0424, 'b': 0.01082, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.35},
    {'Line_id': 'L_3', 'fromNode': '4', 'toNode': '5', 'r': 0.00176, 'x': 0.00798, 'b': 0.0021, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.72},
    {'Line_id': 'L_4', 'fromNode': '3', 'toNode': '5', 'r': 0.0241, 'x': 0.108, 'b': 0.0284, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.68},
    {'Line_id': 'L_5', 'fromNode': '5', 'toNode': '6', 'r': 0.0119, 'x': 0.054, 'b': 0.01426, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.87},
    {'Line_id': 'L_6', 'fromNode': '6', 'toNode': '7', 'r': 0.00459, 'x': 0.0208, 'b': 0.0055, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.87},
    {'Line_id': 'L_7', 'fromNode': '8', 'toNode': '9', 'r': 0.00244, 'x': 0.0305, 'b': 1.162, 'MVA_rating': 711.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.88},
    {'Line_id': 'L_8', 'fromNode': '8', 'toNode': '5', 'r': 0.0, 'x': 0.0267, 'b': 0.0, 'MVA_rating': 1099.0, 'm': 0.985, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_9', 'fromNode': '9', 'toNode': '10', 'r': 0.00258, 'x': 0.0322, 'b': 1.23, 'MVA_rating': 710.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.47},
    {'Line_id': 'L_10', 'fromNode': '4', 'toNode': '11', 'r': 0.0209, 'x': 0.0688, 'b': 0.01748, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.43},
    {'Line_id': 'L_11', 'fromNode': '5', 'toNode': '11', 'r': 0.0203, 'x': 0.0682, 'b': 0.01738, 'MVA_rating': 152.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.41},
    {'Line_id': 'L_12', 'fromNode': '11', 'toNode': '12', 'r': 0.00595, 'x': 0.0196, 'b': 0.00502, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.55},
    {'Line_id': 'L_13', 'fromNode': '2', 'toNode': '12', 'r': 0.0187, 'x': 0.0616, 'b': 0.01572, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.86},
    {'Line_id': 'L_14', 'fromNode': '3', 'toNode': '12', 'r': 0.0484, 'x': 0.16, 'b': 0.0406, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.62},
    {'Line_id': 'L_15', 'fromNode': '7', 'toNode': '12', 'r': 0.00862, 'x': 0.034, 'b': 0.00874, 'MVA_rating': 164.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.88},
    {'Line_id': 'L_16', 'fromNode': '11', 'toNode': '13', 'r': 0.02225, 'x': 0.0731, 'b': 0.01876, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.77},
    {'Line_id': 'L_17', 'fromNode': '12', 'toNode': '14', 'r': 0.0215, 'x': 0.0707, 'b': 0.01816, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.58},
    {'Line_id': 'L_18', 'fromNode': '13', 'toNode': '15', 'r': 0.0744, 'x': 0.2444, 'b': 0.06268, 'MVA_rating': 115.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.69},
    {'Line_id': 'L_19', 'fromNode': '14', 'toNode': '15', 'r': 0.0595, 'x': 0.195, 'b': 0.0502, 'MVA_rating': 144.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.68},
    {'Line_id': 'L_20', 'fromNode': '12', 'toNode': '16', 'r': 0.0212, 'x': 0.0834, 'b': 0.0214, 'MVA_rating': 164.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.06},
    {'Line_id': 'L_21', 'fromNode': '15', 'toNode': '17', 'r': 0.0132, 'x': 0.0437, 'b': 0.0444, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.45},
    {'Line_id': 'L_22', 'fromNode': '16', 'toNode': '17', 'r': 0.0454, 'x': 0.1801, 'b': 0.0466, 'MVA_rating': 158.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_23', 'fromNode': '17', 'toNode': '18', 'r': 0.0123, 'x': 0.0505, 'b': 0.01298, 'MVA_rating': 167.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.34},
    {'Line_id': 'L_24', 'fromNode': '18', 'toNode': '19', 'r': 0.01119, 'x': 0.0493, 'b': 0.01142, 'MVA_rating': 173.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.37},
    {'Line_id': 'L_25', 'fromNode': '19', 'toNode': '20', 'r': 0.0252, 'x': 0.117, 'b': 0.0298, 'MVA_rating': 178.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.65},
    {'Line_id': 'L_26', 'fromNode': '15', 'toNode': '19', 'r': 0.012, 'x': 0.0394, 'b': 0.0101, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.11},
    {'Line_id': 'L_27', 'fromNode': '20', 'toNode': '21', 'r': 0.0183, 'x': 0.0849, 'b': 0.0216, 'MVA_rating': 177.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.69},
    {'Line_id': 'L_28', 'fromNode': '21', 'toNode': '22', 'r': 0.0209, 'x': 0.097, 'b': 0.0246, 'MVA_rating': 178.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.83},
    {'Line_id': 'L_29', 'fromNode': '22', 'toNode': '23', 'r': 0.0342, 'x': 0.159, 'b': 0.0404, 'MVA_rating': 178.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.47},
    {'Line_id': 'L_30', 'fromNode': '23', 'toNode': '24', 'r': 0.0135, 'x': 0.0492, 'b': 0.0498, 'MVA_rating': 158.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.03},
    {'Line_id': 'L_31', 'fromNode': '23', 'toNode': '25', 'r': 0.0156, 'x': 0.08, 'b': 0.0864, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.58},
    {'Line_id': 'L_32', 'fromNode': '26', 'toNode': '25', 'r': 0.0, 'x': 0.0382, 'b': 0.0, 'MVA_rating': 768.0, 'm': 0.96, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_33', 'fromNode': '25', 'toNode': '27', 'r': 0.0318, 'x': 0.163, 'b': 0.1764, 'MVA_rating': 177.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.7},
    {'Line_id': 'L_34', 'fromNode': '27', 'toNode': '28', 'r': 0.01913, 'x': 0.0855, 'b': 0.0216, 'MVA_rating': 174.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.62},
    {'Line_id': 'L_35', 'fromNode': '28', 'toNode': '29', 'r': 0.0237, 'x': 0.0943, 'b': 0.0238, 'MVA_rating': 165.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.02},
    {'Line_id': 'L_36', 'fromNode': '30', 'toNode': '17', 'r': 0.0, 'x': 0.0388, 'b': 0.0, 'MVA_rating': 756.0, 'm': 0.96, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_37', 'fromNode': '8', 'toNode': '30', 'r': 0.00431, 'x': 0.0504, 'b': 0.514, 'MVA_rating': 580.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_38', 'fromNode': '26', 'toNode': '30', 'r': 0.00799, 'x': 0.086, 'b': 0.908, 'MVA_rating': 340.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.68},
    {'Line_id': 'L_39', 'fromNode': '17', 'toNode': '31', 'r': 0.0474, 'x': 0.1563, 'b': 0.0399, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.33},
    {'Line_id': 'L_40', 'fromNode': '29', 'toNode': '31', 'r': 0.0108, 'x': 0.0331, 'b': 0.0083, 'MVA_rating': 146.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.54},
    {'Line_id': 'L_41', 'fromNode': '23', 'toNode': '32', 'r': 0.0317, 'x': 0.1153, 'b': 0.1173, 'MVA_rating': 158.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.45},
    {'Line_id': 'L_42', 'fromNode': '31', 'toNode': '32', 'r': 0.0298, 'x': 0.0985, 'b': 0.0251, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.77},
    {'Line_id': 'L_43', 'fromNode': '27', 'toNode': '32', 'r': 0.0229, 'x': 0.0755, 'b': 0.01926, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.96},
    {'Line_id': 'L_44', 'fromNode': '15', 'toNode': '33', 'r': 0.038, 'x': 0.1244, 'b': 0.03194, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.76},
    {'Line_id': 'L_45', 'fromNode': '19', 'toNode': '34', 'r': 0.0752, 'x': 0.247, 'b': 0.0632, 'MVA_rating': 114.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.72},
    {'Line_id': 'L_46', 'fromNode': '35', 'toNode': '36', 'r': 0.00224, 'x': 0.0102, 'b': 0.00268, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.92},
    {'Line_id': 'L_47', 'fromNode': '35', 'toNode': '37', 'r': 0.011, 'x': 0.0497, 'b': 0.01318, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.45},
    {'Line_id': 'L_48', 'fromNode': '33', 'toNode': '37', 'r': 0.0415, 'x': 0.142, 'b': 0.0366, 'MVA_rating': 154.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.39},
    {'Line_id': 'L_49', 'fromNode': '34', 'toNode': '36', 'r': 0.00871, 'x': 0.0268, 'b': 0.00568, 'MVA_rating': 146.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.06},
    {'Line_id': 'L_50', 'fromNode': '34', 'toNode': '37', 'r': 0.00256, 'x': 0.0094, 'b': 0.00984, 'MVA_rating': 159.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.77},
    {'Line_id': 'L_51', 'fromNode': '38', 'toNode': '37', 'r': 0.0, 'x': 0.0375, 'b': 0.0, 'MVA_rating': 783.0, 'm': 0.935, 'shift': 0.0, 'Cost MEUR': 14.68},
    {'Line_id': 'L_52', 'fromNode': '37', 'toNode': '39', 'r': 0.0321, 'x': 0.106, 'b': 0.027, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.36},
    {'Line_id': 'L_53', 'fromNode': '37', 'toNode': '40', 'r': 0.0593, 'x': 0.168, 'b': 0.042, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.47},
    {'Line_id': 'L_54', 'fromNode': '30', 'toNode': '38', 'r': 0.00464, 'x': 0.054, 'b': 0.422, 'MVA_rating': 542.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.69},
    {'Line_id': 'L_55', 'fromNode': '39', 'toNode': '40', 'r': 0.0184, 'x': 0.0605, 'b': 0.01552, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.77},
    {'Line_id': 'L_56', 'fromNode': '40', 'toNode': '41', 'r': 0.0145, 'x': 0.0487, 'b': 0.01222, 'MVA_rating': 152.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.86},
    {'Line_id': 'L_57', 'fromNode': '40', 'toNode': '42', 'r': 0.0555, 'x': 0.183, 'b': 0.0466, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.44},
    {'Line_id': 'L_58', 'fromNode': '41', 'toNode': '42', 'r': 0.041, 'x': 0.135, 'b': 0.0344, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.65},
    {'Line_id': 'L_59', 'fromNode': '43', 'toNode': '44', 'r': 0.0608, 'x': 0.2454, 'b': 0.06068, 'MVA_rating': 117.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.79},
    {'Line_id': 'L_60', 'fromNode': '34', 'toNode': '43', 'r': 0.0413, 'x': 0.1681, 'b': 0.04226, 'MVA_rating': 167.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.45},
    {'Line_id': 'L_61', 'fromNode': '44', 'toNode': '45', 'r': 0.0224, 'x': 0.0901, 'b': 0.0224, 'MVA_rating': 166.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.71},
    {'Line_id': 'L_62', 'fromNode': '45', 'toNode': '46', 'r': 0.04, 'x': 0.1356, 'b': 0.0332, 'MVA_rating': 153.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.82},
    {'Line_id': 'L_63', 'fromNode': '46', 'toNode': '47', 'r': 0.038, 'x': 0.127, 'b': 0.0316, 'MVA_rating': 152.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.07},
    {'Line_id': 'L_64', 'fromNode': '46', 'toNode': '48', 'r': 0.0601, 'x': 0.189, 'b': 0.0472, 'MVA_rating': 148.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.68},
    {'Line_id': 'L_65', 'fromNode': '47', 'toNode': '49', 'r': 0.0191, 'x': 0.0625, 'b': 0.01604, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.9},
    {'Line_id': 'L_66', 'fromNode': '42', 'toNode': '49', 'r': 0.0715, 'x': 0.323, 'b': 0.086, 'MVA_rating': 89.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.72},
    {'Line_id': 'L_67', 'fromNode': '42', 'toNode': '49', 'r': 0.0715, 'x': 0.323, 'b': 0.086, 'MVA_rating': 89.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.72},
    {'Line_id': 'L_68', 'fromNode': '45', 'toNode': '49', 'r': 0.0684, 'x': 0.186, 'b': 0.0444, 'MVA_rating': 138.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 13.67},
    {'Line_id': 'L_69', 'fromNode': '48', 'toNode': '49', 'r': 0.0179, 'x': 0.0505, 'b': 0.01258, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.75},
    {'Line_id': 'L_70', 'fromNode': '49', 'toNode': '50', 'r': 0.0267, 'x': 0.0752, 'b': 0.01874, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.59},
    {'Line_id': 'L_71', 'fromNode': '49', 'toNode': '51', 'r': 0.0486, 'x': 0.137, 'b': 0.0342, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.18},
    {'Line_id': 'L_72', 'fromNode': '51', 'toNode': '52', 'r': 0.0203, 'x': 0.0588, 'b': 0.01396, 'MVA_rating': 142.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.42},
    {'Line_id': 'L_73', 'fromNode': '52', 'toNode': '53', 'r': 0.0405, 'x': 0.1635, 'b': 0.04058, 'MVA_rating': 166.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 13.98},
    {'Line_id': 'L_74', 'fromNode': '53', 'toNode': '54', 'r': 0.0263, 'x': 0.122, 'b': 0.031, 'MVA_rating': 177.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.05},
    {'Line_id': 'L_75', 'fromNode': '49', 'toNode': '54', 'r': 0.073, 'x': 0.289, 'b': 0.0738, 'MVA_rating': 99.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.75},
    {'Line_id': 'L_76', 'fromNode': '49', 'toNode': '54', 'r': 0.0869, 'x': 0.291, 'b': 0.073, 'MVA_rating': 97.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.73},
    {'Line_id': 'L_77', 'fromNode': '54', 'toNode': '55', 'r': 0.0169, 'x': 0.0707, 'b': 0.0202, 'MVA_rating': 169.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.14},
    {'Line_id': 'L_78', 'fromNode': '54', 'toNode': '56', 'r': 0.00275, 'x': 0.00955, 'b': 0.00732, 'MVA_rating': 155.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.77},
    {'Line_id': 'L_79', 'fromNode': '55', 'toNode': '56', 'r': 0.00488, 'x': 0.0151, 'b': 0.00374, 'MVA_rating': 146.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.16},
    {'Line_id': 'L_80', 'fromNode': '56', 'toNode': '57', 'r': 0.0343, 'x': 0.0966, 'b': 0.0242, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.18},
    {'Line_id': 'L_81', 'fromNode': '50', 'toNode': '57', 'r': 0.0474, 'x': 0.134, 'b': 0.0332, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.95},
    {'Line_id': 'L_82', 'fromNode': '56', 'toNode': '58', 'r': 0.0343, 'x': 0.0966, 'b': 0.0242, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.18},
    {'Line_id': 'L_83', 'fromNode': '51', 'toNode': '58', 'r': 0.0255, 'x': 0.0719, 'b': 0.01788, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.34},
    {'Line_id': 'L_84', 'fromNode': '54', 'toNode': '59', 'r': 0.0503, 'x': 0.2293, 'b': 0.0598, 'MVA_rating': 125.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_85', 'fromNode': '56', 'toNode': '59', 'r': 0.0825, 'x': 0.251, 'b': 0.0569, 'MVA_rating': 112.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.8},
    {'Line_id': 'L_86', 'fromNode': '56', 'toNode': '59', 'r': 0.0803, 'x': 0.239, 'b': 0.0536, 'MVA_rating': 117.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.75},
    {'Line_id': 'L_87', 'fromNode': '55', 'toNode': '59', 'r': 0.04739, 'x': 0.2158, 'b': 0.05646, 'MVA_rating': 133.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.69},
    {'Line_id': 'L_88', 'fromNode': '59', 'toNode': '60', 'r': 0.0317, 'x': 0.145, 'b': 0.0376, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 13.06},
    {'Line_id': 'L_89', 'fromNode': '59', 'toNode': '61', 'r': 0.0328, 'x': 0.15, 'b': 0.0388, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 13.51},
    {'Line_id': 'L_90', 'fromNode': '60', 'toNode': '61', 'r': 0.00264, 'x': 0.0135, 'b': 0.01456, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 1.28},
    {'Line_id': 'L_91', 'fromNode': '60', 'toNode': '62', 'r': 0.0123, 'x': 0.0561, 'b': 0.01468, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.05},
    {'Line_id': 'L_92', 'fromNode': '61', 'toNode': '62', 'r': 0.00824, 'x': 0.0376, 'b': 0.0098, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.39},
    {'Line_id': 'L_93', 'fromNode': '63', 'toNode': '59', 'r': 0.0, 'x': 0.0386, 'b': 0.0, 'MVA_rating': 760.0, 'm': 0.96, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_94', 'fromNode': '63', 'toNode': '64', 'r': 0.00172, 'x': 0.02, 'b': 0.216, 'MVA_rating': 687.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.9},
    {'Line_id': 'L_95', 'fromNode': '64', 'toNode': '61', 'r': 0.0, 'x': 0.0268, 'b': 0.0, 'MVA_rating': 1095.0, 'm': 0.985, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_96', 'fromNode': '38', 'toNode': '65', 'r': 0.00901, 'x': 0.0986, 'b': 1.046, 'MVA_rating': 297.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.7},
    {'Line_id': 'L_97', 'fromNode': '64', 'toNode': '65', 'r': 0.00269, 'x': 0.0302, 'b': 0.38, 'MVA_rating': 675.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.23},
    {'Line_id': 'L_98', 'fromNode': '49', 'toNode': '66', 'r': 0.018, 'x': 0.0919, 'b': 0.0248, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.71},
    {'Line_id': 'L_99', 'fromNode': '49', 'toNode': '66', 'r': 0.018, 'x': 0.0919, 'b': 0.0248, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.71},
    {'Line_id': 'L_100', 'fromNode': '62', 'toNode': '66', 'r': 0.0482, 'x': 0.218, 'b': 0.0578, 'MVA_rating': 132.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_101', 'fromNode': '62', 'toNode': '67', 'r': 0.0258, 'x': 0.117, 'b': 0.031, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.54},
    {'Line_id': 'L_102', 'fromNode': '65', 'toNode': '66', 'r': 0.0, 'x': 0.037, 'b': 0.0, 'MVA_rating': 793.0, 'm': 0.935, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_103', 'fromNode': '66', 'toNode': '67', 'r': 0.0224, 'x': 0.1015, 'b': 0.02682, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.15},
    {'Line_id': 'L_104', 'fromNode': '65', 'toNode': '68', 'r': 0.00138, 'x': 0.016, 'b': 0.638, 'MVA_rating': 686.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.51},
    {'Line_id': 'L_105', 'fromNode': '47', 'toNode': '69', 'r': 0.0844, 'x': 0.2778, 'b': 0.07092, 'MVA_rating': 102.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.81},
    {'Line_id': 'L_106', 'fromNode': '49', 'toNode': '69', 'r': 0.0985, 'x': 0.324, 'b': 0.0828, 'MVA_rating': 87.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.73},
    {'Line_id': 'L_107', 'fromNode': '68', 'toNode': '69', 'r': 0.0, 'x': 0.037, 'b': 0.0, 'MVA_rating': 793.0, 'm': 0.935, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_108', 'fromNode': '69', 'toNode': '70', 'r': 0.03, 'x': 0.127, 'b': 0.122, 'MVA_rating': 170.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.09},
    {'Line_id': 'L_109', 'fromNode': '24', 'toNode': '70', 'r': 0.00221, 'x': 0.4115, 'b': 0.10198, 'MVA_rating': 72.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.81},
    {'Line_id': 'L_110', 'fromNode': '70', 'toNode': '71', 'r': 0.00882, 'x': 0.0355, 'b': 0.00878, 'MVA_rating': 166.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.04},
    {'Line_id': 'L_111', 'fromNode': '24', 'toNode': '72', 'r': 0.0488, 'x': 0.196, 'b': 0.0488, 'MVA_rating': 146.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_112', 'fromNode': '71', 'toNode': '72', 'r': 0.0446, 'x': 0.18, 'b': 0.04444, 'MVA_rating': 159.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_113', 'fromNode': '71', 'toNode': '73', 'r': 0.00866, 'x': 0.0454, 'b': 0.01178, 'MVA_rating': 188.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.34},
    {'Line_id': 'L_114', 'fromNode': '70', 'toNode': '74', 'r': 0.0401, 'x': 0.1323, 'b': 0.03368, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.44},
    {'Line_id': 'L_115', 'fromNode': '70', 'toNode': '75', 'r': 0.0428, 'x': 0.141, 'b': 0.036, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.13},
    {'Line_id': 'L_116', 'fromNode': '69', 'toNode': '75', 'r': 0.0405, 'x': 0.122, 'b': 0.124, 'MVA_rating': 145.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.32},
    {'Line_id': 'L_117', 'fromNode': '74', 'toNode': '75', 'r': 0.0123, 'x': 0.0406, 'b': 0.01034, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.2},
    {'Line_id': 'L_118', 'fromNode': '76', 'toNode': '77', 'r': 0.0444, 'x': 0.148, 'b': 0.0368, 'MVA_rating': 152.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.74},
    {'Line_id': 'L_119', 'fromNode': '69', 'toNode': '77', 'r': 0.0309, 'x': 0.101, 'b': 0.1038, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.92},
    {'Line_id': 'L_120', 'fromNode': '75', 'toNode': '77', 'r': 0.0601, 'x': 0.1999, 'b': 0.04978, 'MVA_rating': 141.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.72},
    {'Line_id': 'L_121', 'fromNode': '77', 'toNode': '78', 'r': 0.00376, 'x': 0.0124, 'b': 0.01264, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.98},
    {'Line_id': 'L_122', 'fromNode': '78', 'toNode': '79', 'r': 0.00546, 'x': 0.0244, 'b': 0.00648, 'MVA_rating': 174.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.18},
    {'Line_id': 'L_123', 'fromNode': '77', 'toNode': '80', 'r': 0.017, 'x': 0.0485, 'b': 0.0472, 'MVA_rating': 141.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.62},
    {'Line_id': 'L_124', 'fromNode': '77', 'toNode': '80', 'r': 0.0294, 'x': 0.105, 'b': 0.0228, 'MVA_rating': 157.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.56},
    {'Line_id': 'L_125', 'fromNode': '79', 'toNode': '80', 'r': 0.0156, 'x': 0.0704, 'b': 0.0187, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.31},
    {'Line_id': 'L_126', 'fromNode': '68', 'toNode': '81', 'r': 0.00175, 'x': 0.0202, 'b': 0.808, 'MVA_rating': 684.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.93},
    {'Line_id': 'L_127', 'fromNode': '81', 'toNode': '80', 'r': 0.0, 'x': 0.037, 'b': 0.0, 'MVA_rating': 793.0, 'm': 0.935, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_128', 'fromNode': '77', 'toNode': '82', 'r': 0.0298, 'x': 0.0853, 'b': 0.08174, 'MVA_rating': 141.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.37},
    {'Line_id': 'L_129', 'fromNode': '82', 'toNode': '83', 'r': 0.0112, 'x': 0.03665, 'b': 0.03796, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.87},
    {'Line_id': 'L_130', 'fromNode': '83', 'toNode': '84', 'r': 0.0625, 'x': 0.132, 'b': 0.0258, 'MVA_rating': 122.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.91},
    {'Line_id': 'L_131', 'fromNode': '83', 'toNode': '85', 'r': 0.043, 'x': 0.148, 'b': 0.0348, 'MVA_rating': 154.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.87},
    {'Line_id': 'L_132', 'fromNode': '84', 'toNode': '85', 'r': 0.0302, 'x': 0.0641, 'b': 0.01234, 'MVA_rating': 122.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.32},
    {'Line_id': 'L_133', 'fromNode': '85', 'toNode': '86', 'r': 0.035, 'x': 0.123, 'b': 0.0276, 'MVA_rating': 156.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.97},
    {'Line_id': 'L_134', 'fromNode': '86', 'toNode': '87', 'r': 0.02828, 'x': 0.2074, 'b': 0.0445, 'MVA_rating': 141.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.76},
    {'Line_id': 'L_135', 'fromNode': '85', 'toNode': '88', 'r': 0.02, 'x': 0.102, 'b': 0.0276, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.67},
    {'Line_id': 'L_136', 'fromNode': '85', 'toNode': '89', 'r': 0.0239, 'x': 0.173, 'b': 0.047, 'MVA_rating': 168.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_137', 'fromNode': '88', 'toNode': '89', 'r': 0.0139, 'x': 0.0712, 'b': 0.01934, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.75},
    {'Line_id': 'L_138', 'fromNode': '89', 'toNode': '90', 'r': 0.0518, 'x': 0.188, 'b': 0.0528, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.72},
    {'Line_id': 'L_139', 'fromNode': '89', 'toNode': '90', 'r': 0.0238, 'x': 0.0997, 'b': 0.106, 'MVA_rating': 169.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.66},
    {'Line_id': 'L_140', 'fromNode': '90', 'toNode': '91', 'r': 0.0254, 'x': 0.0836, 'b': 0.0214, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.6},
    {'Line_id': 'L_141', 'fromNode': '89', 'toNode': '92', 'r': 0.0099, 'x': 0.0505, 'b': 0.0548, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.79},
    {'Line_id': 'L_142', 'fromNode': '89', 'toNode': '92', 'r': 0.0393, 'x': 0.1581, 'b': 0.0414, 'MVA_rating': 166.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 13.52},
    {'Line_id': 'L_143', 'fromNode': '91', 'toNode': '92', 'r': 0.0387, 'x': 0.1272, 'b': 0.03268, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.04},
    {'Line_id': 'L_144', 'fromNode': '92', 'toNode': '93', 'r': 0.0258, 'x': 0.0848, 'b': 0.0218, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.69},
    {'Line_id': 'L_145', 'fromNode': '92', 'toNode': '94', 'r': 0.0481, 'x': 0.158, 'b': 0.0406, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.47},
    {'Line_id': 'L_146', 'fromNode': '93', 'toNode': '94', 'r': 0.0223, 'x': 0.0732, 'b': 0.01876, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.78},
    {'Line_id': 'L_147', 'fromNode': '94', 'toNode': '95', 'r': 0.0132, 'x': 0.0434, 'b': 0.0111, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.42},
    {'Line_id': 'L_148', 'fromNode': '80', 'toNode': '96', 'r': 0.0356, 'x': 0.182, 'b': 0.0494, 'MVA_rating': 159.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_149', 'fromNode': '82', 'toNode': '96', 'r': 0.0162, 'x': 0.053, 'b': 0.0544, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.16},
    {'Line_id': 'L_150', 'fromNode': '94', 'toNode': '96', 'r': 0.0269, 'x': 0.0869, 'b': 0.023, 'MVA_rating': 149.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.78},
    {'Line_id': 'L_151', 'fromNode': '80', 'toNode': '97', 'r': 0.0183, 'x': 0.0934, 'b': 0.0254, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.85},
    {'Line_id': 'L_152', 'fromNode': '80', 'toNode': '98', 'r': 0.0238, 'x': 0.108, 'b': 0.0286, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 9.73},
    {'Line_id': 'L_153', 'fromNode': '80', 'toNode': '99', 'r': 0.0454, 'x': 0.206, 'b': 0.0546, 'MVA_rating': 140.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.77},
    {'Line_id': 'L_154', 'fromNode': '92', 'toNode': '100', 'r': 0.0648, 'x': 0.295, 'b': 0.0472, 'MVA_rating': 98.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.8},
    {'Line_id': 'L_155', 'fromNode': '94', 'toNode': '100', 'r': 0.0178, 'x': 0.058, 'b': 0.0604, 'MVA_rating': 150.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.55},
    {'Line_id': 'L_156', 'fromNode': '95', 'toNode': '96', 'r': 0.0171, 'x': 0.0547, 'b': 0.01474, 'MVA_rating': 149.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.27},
    {'Line_id': 'L_157', 'fromNode': '96', 'toNode': '97', 'r': 0.0173, 'x': 0.0885, 'b': 0.024, 'MVA_rating': 186.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 8.39},
    {'Line_id': 'L_158', 'fromNode': '98', 'toNode': '100', 'r': 0.0397, 'x': 0.179, 'b': 0.0476, 'MVA_rating': 160.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_159', 'fromNode': '99', 'toNode': '100', 'r': 0.018, 'x': 0.0813, 'b': 0.0216, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 7.29},
    {'Line_id': 'L_160', 'fromNode': '100', 'toNode': '101', 'r': 0.0277, 'x': 0.1262, 'b': 0.0328, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 11.37},
    {'Line_id': 'L_161', 'fromNode': '92', 'toNode': '102', 'r': 0.0123, 'x': 0.0559, 'b': 0.01464, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.04},
    {'Line_id': 'L_162', 'fromNode': '101', 'toNode': '102', 'r': 0.0246, 'x': 0.112, 'b': 0.0294, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 10.09},
    {'Line_id': 'L_163', 'fromNode': '100', 'toNode': '103', 'r': 0.016, 'x': 0.0525, 'b': 0.0536, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.14},
    {'Line_id': 'L_164', 'fromNode': '100', 'toNode': '104', 'r': 0.0451, 'x': 0.204, 'b': 0.0541, 'MVA_rating': 141.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.73},
    {'Line_id': 'L_165', 'fromNode': '103', 'toNode': '104', 'r': 0.0466, 'x': 0.1584, 'b': 0.0407, 'MVA_rating': 153.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.63},
    {'Line_id': 'L_166', 'fromNode': '103', 'toNode': '105', 'r': 0.0535, 'x': 0.1625, 'b': 0.0408, 'MVA_rating': 145.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.4},
    {'Line_id': 'L_167', 'fromNode': '100', 'toNode': '106', 'r': 0.0605, 'x': 0.229, 'b': 0.062, 'MVA_rating': 124.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.69},
    {'Line_id': 'L_168', 'fromNode': '104', 'toNode': '105', 'r': 0.00994, 'x': 0.0378, 'b': 0.00986, 'MVA_rating': 161.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.15},
    {'Line_id': 'L_169', 'fromNode': '105', 'toNode': '106', 'r': 0.014, 'x': 0.0547, 'b': 0.01434, 'MVA_rating': 164.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.63},
    {'Line_id': 'L_170', 'fromNode': '105', 'toNode': '107', 'r': 0.053, 'x': 0.183, 'b': 0.0472, 'MVA_rating': 154.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_171', 'fromNode': '105', 'toNode': '108', 'r': 0.0261, 'x': 0.0703, 'b': 0.01844, 'MVA_rating': 137.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.14},
    {'Line_id': 'L_172', 'fromNode': '106', 'toNode': '107', 'r': 0.053, 'x': 0.183, 'b': 0.0472, 'MVA_rating': 154.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_173', 'fromNode': '108', 'toNode': '109', 'r': 0.0105, 'x': 0.0288, 'b': 0.0076, 'MVA_rating': 138.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.12},
    {'Line_id': 'L_174', 'fromNode': '103', 'toNode': '110', 'r': 0.03906, 'x': 0.1813, 'b': 0.0461, 'MVA_rating': 159.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_175', 'fromNode': '109', 'toNode': '110', 'r': 0.0278, 'x': 0.0762, 'b': 0.0202, 'MVA_rating': 138.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.6},
    {'Line_id': 'L_176', 'fromNode': '110', 'toNode': '111', 'r': 0.022, 'x': 0.0755, 'b': 0.02, 'MVA_rating': 154.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.06},
    {'Line_id': 'L_177', 'fromNode': '110', 'toNode': '112', 'r': 0.0247, 'x': 0.064, 'b': 0.062, 'MVA_rating': 135.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.63},
    {'Line_id': 'L_178', 'fromNode': '17', 'toNode': '113', 'r': 0.00913, 'x': 0.0301, 'b': 0.00768, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 2.37},
    {'Line_id': 'L_179', 'fromNode': '32', 'toNode': '113', 'r': 0.0615, 'x': 0.203, 'b': 0.0518, 'MVA_rating': 139.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.74},
    {'Line_id': 'L_180', 'fromNode': '32', 'toNode': '114', 'r': 0.0135, 'x': 0.0612, 'b': 0.01628, 'MVA_rating': 176.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 5.52},
    {'Line_id': 'L_181', 'fromNode': '27', 'toNode': '115', 'r': 0.0164, 'x': 0.0741, 'b': 0.01972, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 6.64},
    {'Line_id': 'L_182', 'fromNode': '114', 'toNode': '115', 'r': 0.0023, 'x': 0.0104, 'b': 0.00276, 'MVA_rating': 175.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 0.93},
    {'Line_id': 'L_183', 'fromNode': '68', 'toNode': '116', 'r': 0.00034, 'x': 0.00405, 'b': 0.164, 'MVA_rating': 7218.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 14.67},
    {'Line_id': 'L_184', 'fromNode': '12', 'toNode': '117', 'r': 0.0329, 'x': 0.14, 'b': 0.0358, 'MVA_rating': 170.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 12.22},
    {'Line_id': 'L_185', 'fromNode': '75', 'toNode': '118', 'r': 0.0145, 'x': 0.0481, 'b': 0.01198, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 3.79},
    {'Line_id': 'L_186', 'fromNode': '76', 'toNode': '118', 'r': 0.0164, 'x': 0.0544, 'b': 0.01356, 'MVA_rating': 151.0, 'm': 1.0, 'shift': 0.0, 'Cost MEUR': 4.29}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)


    lines_AC['Cost MEUR'] = lines_AC['Cost MEUR'] * kappa/0.5

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='pu')
    grid.name = 'case118_TEP'
    

    
    # Add Generators
    pyf.add_gen(grid, '1', '1', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-5.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '4', '2', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '6', '3', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-13.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '8', '4', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '10', '5', lf=20.0, qf=0.0222222222, MWmax=550.0, MWmin=0.0, MVArmax=200.0, MVArmin=-147.0, PsetMW=450.0, QsetMVA=0.0)
    pyf.add_gen(grid, '12', '6', lf=20.0, qf=0.117647059, MWmax=185.0, MWmin=0.0, MVArmax=120.0, MVArmin=-35.0, PsetMW=85.0, QsetMVA=0.0)
    pyf.add_gen(grid, '15', '7', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=30.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '18', '8', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=50.0, MVArmin=-16.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '19', '9', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '24', '10', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '25', '11', lf=20.0, qf=0.0454545455, MWmax=320.0, MWmin=0.0, MVArmax=140.0, MVArmin=-47.0, PsetMW=220.00000000000003, QsetMVA=0.0)
    pyf.add_gen(grid, '26', '12', lf=20.0, qf=0.0318471338, MWmax=413.99999999999994, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=314.0, QsetMVA=0.0)
    pyf.add_gen(grid, '27', '13', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '31', '14', lf=20.0, qf=1.42857143, MWmax=107.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=7.000000000000001, QsetMVA=0.0)
    pyf.add_gen(grid, '32', '15', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=42.0, MVArmin=-14.000000000000002, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '34', '16', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '36', '17', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=24.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '40', '18', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '42', '19', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '46', '20', lf=20.0, qf=0.526315789, MWmax=119.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=19.0, QsetMVA=0.0)
    pyf.add_gen(grid, '49', '21', lf=20.0, qf=0.0490196078, MWmax=304.0, MWmin=0.0, MVArmax=210.0, MVArmin=-85.0, PsetMW=204.0, QsetMVA=0.0)
    pyf.add_gen(grid, '54', '22', lf=20.0, qf=0.208333333, MWmax=148.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=48.0, QsetMVA=0.0)
    pyf.add_gen(grid, '55', '23', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '56', '24', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=15.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '59', '25', lf=20.0, qf=0.064516129, MWmax=254.99999999999997, MWmin=0.0, MVArmax=180.0, MVArmin=-60.0, PsetMW=155.0, QsetMVA=0.0)
    pyf.add_gen(grid, '61', '26', lf=20.0, qf=0.0625, MWmax=260.0, MWmin=0.0, MVArmax=300.0, MVArmin=-100.0, PsetMW=160.0, QsetMVA=0.0)
    pyf.add_gen(grid, '62', '27', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=20.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '65', '28', lf=20.0, qf=0.0255754476, MWmax=491.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=391.0, QsetMVA=0.0)
    pyf.add_gen(grid, '66', '29', lf=20.0, qf=0.0255102041, MWmax=492.0, MWmin=0.0, MVArmax=200.0, MVArmin=-67.0, PsetMW=392.0, QsetMVA=0.0)
    pyf.add_gen(grid, '69', '30', lf=20.0, qf=0.0193648335, MWmax=805.1999999999999, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=516.4, QsetMVA=0.0)
    pyf.add_gen(grid, '70', '31', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=32.0, MVArmin=-10.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '72', '32', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '73', '33', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '74', '34', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-6.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '76', '35', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '77', '36', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=70.0, MVArmin=-20.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '80', '37', lf=20.0, qf=0.0209643606, MWmax=577.0, MWmin=0.0, MVArmax=280.0, MVArmin=-165.0, PsetMW=476.99999999999994, QsetMVA=0.0)
    pyf.add_gen(grid, '85', '38', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '87', '39', lf=20.0, qf=2.5, MWmax=104.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=4.0, QsetMVA=0.0)
    pyf.add_gen(grid, '89', '40', lf=20.0, qf=0.0164744646, MWmax=707.0, MWmin=0.0, MVArmax=300.0, MVArmin=-210.0, PsetMW=607.0, QsetMVA=0.0)
    pyf.add_gen(grid, '90', '41', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '91', '42', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '92', '43', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=9.0, MVArmin=-3.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '99', '44', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=100.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '100', '45', lf=20.0, qf=0.0396825397, MWmax=352.0, MWmin=0.0, MVArmax=155.0, MVArmin=-50.0, PsetMW=252.0, QsetMVA=0.0)
    pyf.add_gen(grid, '103', '46', lf=20.0, qf=0.25, MWmax=140.0, MWmin=0.0, MVArmax=40.0, MVArmin=-15.0, PsetMW=40.0, QsetMVA=0.0)
    pyf.add_gen(grid, '104', '47', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '105', '48', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '107', '49', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-200.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '110', '50', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=23.0, MVArmin=-8.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '111', '51', lf=20.0, qf=0.277777778, MWmax=136.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=36.0, QsetMVA=0.0)
    pyf.add_gen(grid, '112', '52', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '113', '53', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=200.0, MVArmin=-100.0, PsetMW=0.0, QsetMVA=0.0)
    pyf.add_gen(grid, '116', '54', lf=40.0, qf=0.01, MWmax=100.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-1000.0, PsetMW=0.0, QsetMVA=0.0)
    
    
    # Expand Elements

    lines_AC.set_index('Line_id', inplace=True)
    if exp == 'All':
        for line in list(grid.lines_AC):  # Create a copy of the list
            name = line.name
            line_cost = lines_AC.loc[name,'Cost MEUR']*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)
    else:
        for line in list(grid.lines_AC):  
            name = line.name
            if name not in exp:
                continue
            line_cost = lines_AC.loc[name,'Cost MEUR']*10**6
            pyf.Expand_element(grid,name,N_b=N_b,N_i=N_i,N_max=N_max,base_cost=line_cost)


    # Return the grid
    return grid,res
