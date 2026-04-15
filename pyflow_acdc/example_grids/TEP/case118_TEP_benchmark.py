import pyflow_acdc as pyf
import pandas as pd
from pathlib import Path
"""

This case is built uppon the data of 

H. Barrios, A. Roehder, H. Natemeyer and A. Schnettler, "A benchmark case for network expansion methods," 2015 IEEE Eindhoven PowerTech, Eindhoven, Netherlands, 2015, pp. 1-6, doi: 10.1109/PTC.2015.7232601. keywords: {Load modeling;Time series analysis;Biological system modeling;Load flow;Generators;Poles and towers;Wind;Power system planning;Power system economics;RES integration;hybrid AC/DC Systems},

and used in the following paper:

Bernardo Castro Valerio, Marc Cheah-Mane, Vinicius A. Lacerda, Pieter Gebraad, Oriol Gomis-Bellmunt,
Transmission expansion planning for hybrid AC/DC grids using a mixed-integer non-linear programming approach,
International Journal of Electrical Power & Energy Systems,
Volume 174,
2026,
111459,
ISSN 0142-0615,
https://doi.org/10.1016/j.ijepes.2025.111459.

"""
current_file = Path(__file__).resolve()
path = str(current_file.parent)
def case_118_TEP_benchmark(exp_220=None,exp_380=None,slack=1,curtailment_allowed=1,load_factor=1,export_capacity=15000,Gen_Pmin=True,DC=False,DC_exp=False):    
    exp_tf=False
    if exp_380 or exp_220:
        exp_tf =True
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
    {'Node_id': '1', 'Voltage_0': 0.955, 'theta_0': 0.0, 'y_coord': 52.25122049, 'x_coord': 8.070045459, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 294.5, 'Reactive_load': 41.41},
    {'Node_id': '2', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.29693228, 'x_coord': 8.353353937, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 290.83, 'Reactive_load': 40.89},
    {'Node_id': '3', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 51.88264645, 'x_coord': 8.719361326, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 309.16, 'Reactive_load': 43.47},
    {'Node_id': '4', 'Voltage_0': 0.998, 'theta_0': 0.0, 'y_coord': 51.88264645, 'x_coord': 8.719361326, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 639.0, 'Reactive_load': 89.84},
    {'Node_id': '5', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 51.91011822, 'x_coord': 9.3203, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 330.49, 'Reactive_load': 46.47},
    {'Node_id': '6', 'Voltage_0': 0.99, 'theta_0': 0.0, 'y_coord': 51.98980717, 'x_coord': 9.2579, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 263.41, 'Reactive_load': 37.03},
    {'Node_id': '7', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.10915302, 'x_coord': 9.335118766, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 290.35, 'Reactive_load': 40.82},
    {'Node_id': '8', 'Voltage_0': 1.015, 'theta_0': 0.0, 'y_coord': 51.91011822, 'x_coord': 9.3203, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 697.27, 'Reactive_load': 98.04},
    {'Node_id': '9', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 51.75226522, 'x_coord': 9.584495906, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 726.31, 'Reactive_load': 102.12},
    {'Node_id': '10', 'Voltage_0': 1.05, 'theta_0': 0.0, 'y_coord': 51.58135481, 'x_coord': 9.899495962, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_0', 'Power_load': 0.0, 'Reactive_load': 0.0},
    {'Node_id': '11', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.10708672, 'x_coord': 8.752474415, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 333.34, 'Reactive_load': 46.87},
    {'Node_id': '12', 'Voltage_0': 0.99, 'theta_0': 0.0, 'y_coord': 52.33814691, 'x_coord': 8.693179477, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 305.05, 'Reactive_load': 42.89},
    {'Node_id': '13', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.36536775, 'x_coord': 8.94369911, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 297.4, 'Reactive_load': 41.81},
    {'Node_id': '14', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.4127104, 'x_coord': 8.834679312, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 255.24, 'Reactive_load': 35.89},
    {'Node_id': '15', 'Voltage_0': 0.97, 'theta_0': 0.0, 'y_coord': 52.48212518, 'x_coord': 8.947082275, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 214.59, 'Reactive_load': 30.17},
    {'Node_id': '16', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.30160221, 'x_coord': 9.1937, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 262.1, 'Reactive_load': 36.85},
    {'Node_id': '17', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.36250318, 'x_coord': 9.660452363, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 238.96, 'Reactive_load': 33.6},
    {'Node_id': '18', 'Voltage_0': 0.973, 'theta_0': 0.0, 'y_coord': 52.603019, 'x_coord': 9.395527054, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 289.75, 'Reactive_load': 40.74},
    {'Node_id': '19', 'Voltage_0': 0.962, 'theta_0': 0.0, 'y_coord': 52.46354164, 'x_coord': 9.422562808, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 295.6, 'Reactive_load': 41.56},
    {'Node_id': '20', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.4889931, 'x_coord': 9.7537, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 319.51, 'Reactive_load': 44.92},
    {'Node_id': '21', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.44547418, 'x_coord': 10.1409, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 261.75, 'Reactive_load': 36.8},
    {'Node_id': '22', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.48601236, 'x_coord': 10.3261, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 312.25, 'Reactive_load': 43.9},
    {'Node_id': '23', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.4817812, 'x_coord': 10.56375888, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 291.33, 'Reactive_load': 40.96},
    {'Node_id': '24', 'Voltage_0': 0.992, 'theta_0': 0.0, 'y_coord': 52.72032345, 'x_coord': 10.62566641, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 522.11, 'Reactive_load': 73.41},
    {'Node_id': '25', 'Voltage_0': 1.05, 'theta_0': 0.0, 'y_coord': 52.4645323, 'x_coord': 10.82763329, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 311.65, 'Reactive_load': 43.82},
    {'Node_id': '26', 'Voltage_0': 1.015, 'theta_0': 0.0, 'y_coord': 52.4645323, 'x_coord': 10.82763329, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 580.93, 'Reactive_load': 81.68},
    {'Node_id': '27', 'Voltage_0': 0.968, 'theta_0': 0.0, 'y_coord': 52.15812588, 'x_coord': 10.4746, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 282.46, 'Reactive_load': 39.71},
    {'Node_id': '28', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.12980798, 'x_coord': 10.0871, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 343.56, 'Reactive_load': 48.31},
    {'Node_id': '29', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.15017967, 'x_coord': 9.947763763, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 226.88, 'Reactive_load': 31.9},
    {'Node_id': '30', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.36250318, 'x_coord': 9.660452363, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 559.66, 'Reactive_load': 78.69},
    {'Node_id': '31', 'Voltage_0': 0.967, 'theta_0': 0.0, 'y_coord': 52.20512352, 'x_coord': 9.8317, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 217.29, 'Reactive_load': 30.55},
    {'Node_id': '32', 'Voltage_0': 0.963, 'theta_0': 0.0, 'y_coord': 52.29461116, 'x_coord': 10.35529966, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 291.78, 'Reactive_load': 41.02},
    {'Node_id': '33', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.64052451, 'x_coord': 9.204042675, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 294.28, 'Reactive_load': 41.38},
    {'Node_id': '34', 'Voltage_0': 0.984, 'theta_0': 0.0, 'y_coord': 52.57707379, 'x_coord': 9.455461122, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 302.38, 'Reactive_load': 42.51},
    {'Node_id': '35', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.603019, 'x_coord': 9.648223, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 531.74, 'Reactive_load': 74.76},
    {'Node_id': '36', 'Voltage_0': 0.98, 'theta_0': 0.0, 'y_coord': 52.603019, 'x_coord': 9.648223, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 266.21, 'Reactive_load': 37.43},
    {'Node_id': '37', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.8200495, 'x_coord': 9.3515, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 299.69, 'Reactive_load': 42.14},
    {'Node_id': '38', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.8200495, 'x_coord': 9.3515, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 672.57, 'Reactive_load': 94.56},
    {'Node_id': '39', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.91600975, 'x_coord': 8.85290958, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 197.47, 'Reactive_load': 27.76},
    {'Node_id': '40', 'Voltage_0': 0.97, 'theta_0': 0.0, 'y_coord': 53.047357, 'x_coord': 8.820570864, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 183.09, 'Reactive_load': 25.74},
    {'Node_id': '41', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.1957868, 'x_coord': 8.650382229, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 198.86, 'Reactive_load': 27.96},
    {'Node_id': '42', 'Voltage_0': 0.985, 'theta_0': 0.0, 'y_coord': 53.34993112, 'x_coord': 8.828200519, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 193.86, 'Reactive_load': 27.26},
    {'Node_id': '43', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.71017268, 'x_coord': 9.5906, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 147.53, 'Reactive_load': 20.74},
    {'Node_id': '44', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.12009845, 'x_coord': 9.5, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 159.77, 'Reactive_load': 22.46},
    {'Node_id': '45', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.1107593, 'x_coord': 9.6928, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 150.54, 'Reactive_load': 21.17},
    {'Node_id': '46', 'Voltage_0': 1.005, 'theta_0': 0.0, 'y_coord': 53.00365653, 'x_coord': 9.8929, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 143.45, 'Reactive_load': 20.17},
    {'Node_id': '47', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.1963017, 'x_coord': 9.9092, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 145.75, 'Reactive_load': 20.49},
    {'Node_id': '48', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.1963017, 'x_coord': 9.9092, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 176.78, 'Reactive_load': 24.86},
    {'Node_id': '49', 'Voltage_0': 1.025, 'theta_0': 0.0, 'y_coord': 53.64921827, 'x_coord': 9.908277084, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 139.41, 'Reactive_load': 19.6},
    {'Node_id': '50', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.68529409, 'x_coord': 9.666176658, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 130.97, 'Reactive_load': 18.41},
    {'Node_id': '51', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.68529409, 'x_coord': 9.666176658, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 193.21, 'Reactive_load': 27.17},
    {'Node_id': '52', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.48807929, 'x_coord': 9.156115867, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_3', 'Power_load': 135.97, 'Reactive_load': 19.12},
    {'Node_id': '53', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.55070175, 'x_coord': 8.602444441, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 189.32, 'Reactive_load': 26.62},
    {'Node_id': '54', 'Voltage_0': 0.955, 'theta_0': 0.0, 'y_coord': 53.72032928, 'x_coord': 8.661483164, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 147.92, 'Reactive_load': 20.8},
    {'Node_id': '55', 'Voltage_0': 0.952, 'theta_0': 0.0, 'y_coord': 54.06079759, 'x_coord': 8.932421156, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 179.27, 'Reactive_load': 25.2},
    {'Node_id': '56', 'Voltage_0': 0.954, 'theta_0': 0.0, 'y_coord': 53.89887566, 'x_coord': 9.17539155, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 152.22, 'Reactive_load': 21.4},
    {'Node_id': '57', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.76070699, 'x_coord': 9.446, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 157.71, 'Reactive_load': 22.17},
    {'Node_id': '58', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.7982989, 'x_coord': 9.430750891, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 184.1, 'Reactive_load': 25.88},
    {'Node_id': '59', 'Voltage_0': 0.985, 'theta_0': 0.0, 'y_coord': 53.96741859, 'x_coord': 9.597318868, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 169.51, 'Reactive_load': 23.83},
    {'Node_id': '60', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 54.07872993, 'x_coord': 9.986062373, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 128.33, 'Reactive_load': 18.04},
    {'Node_id': '61', 'Voltage_0': 0.995, 'theta_0': 0.0, 'y_coord': 53.96906214, 'x_coord': 10.46359245, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 146.54, 'Reactive_load': 20.6},
    {'Node_id': '62', 'Voltage_0': 0.998, 'theta_0': 0.0, 'y_coord': 54.049762, 'x_coord': 10.25340208, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 129.88, 'Reactive_load': 18.26},
    {'Node_id': '63', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.96741859, 'x_coord': 9.597318868, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 196.7, 'Reactive_load': 27.66},
    {'Node_id': '64', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.96906214, 'x_coord': 10.46359245, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 176.75, 'Reactive_load': 24.85},
    {'Node_id': '65', 'Voltage_0': 1.005, 'theta_0': 0.0, 'y_coord': 53.59950335, 'x_coord': 10.12614877, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 192.01, 'Reactive_load': 27.0},
    {'Node_id': '66', 'Voltage_0': 1.05, 'theta_0': 0.0, 'y_coord': 53.59950335, 'x_coord': 10.12614877, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 141.22, 'Reactive_load': 19.86},
    {'Node_id': '67', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.81882499, 'x_coord': 10.2492, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_5', 'Power_load': 134.45, 'Reactive_load': 18.9},
    {'Node_id': '68', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.46673479, 'x_coord': 10.4895, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 161.66, 'Reactive_load': 22.73},
    {'Node_id': '69', 'Voltage_0': 1.035, 'theta_0': 0.0, 'y_coord': 53.46673479, 'x_coord': 10.4895, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 161.14, 'Reactive_load': 22.66},
    {'Node_id': '70', 'Voltage_0': 0.984, 'theta_0': 0.0, 'y_coord': 52.89277731, 'x_coord': 10.8752, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 244.47, 'Reactive_load': 34.37},
    {'Node_id': '71', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.84481988, 'x_coord': 10.67287728, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 249.02, 'Reactive_load': 35.01},
    {'Node_id': '72', 'Voltage_0': 0.98, 'theta_0': 0.0, 'y_coord': 52.77514085, 'x_coord': 10.5411, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 193.7, 'Reactive_load': 27.23},
    {'Node_id': '73', 'Voltage_0': 0.991, 'theta_0': 0.0, 'y_coord': 52.90609082, 'x_coord': 10.461, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 202.79, 'Reactive_load': 28.51},
    {'Node_id': '74', 'Voltage_0': 0.958, 'theta_0': 0.0, 'y_coord': 52.89277731, 'x_coord': 10.8752, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 145.42, 'Reactive_load': 20.45},
    {'Node_id': '75', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.95348282, 'x_coord': 11.2095, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 153.68, 'Reactive_load': 21.61},
    {'Node_id': '76', 'Voltage_0': 0.943, 'theta_0': 0.0, 'y_coord': 53.19401013, 'x_coord': 11.04104, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 138.51, 'Reactive_load': 19.47},
    {'Node_id': '77', 'Voltage_0': 1.006, 'theta_0': 0.0, 'y_coord': 53.189049, 'x_coord': 11.3791, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 123.24, 'Reactive_load': 17.33},
    {'Node_id': '78', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.41248263, 'x_coord': 11.1017, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 202.98, 'Reactive_load': 28.54},
    {'Node_id': '79', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.6, 'x_coord': 10.8471, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_10', 'Power_load': 133.83, 'Reactive_load': 18.82},
    {'Node_id': '80', 'Voltage_0': 1.04, 'theta_0': 0.0, 'y_coord': 53.7, 'x_coord': 11.37326028, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_10', 'Power_load': 123.5, 'Reactive_load': 17.36},
    {'Node_id': '81', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.7, 'x_coord': 11.37326028, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_10', 'Power_load': 252.09, 'Reactive_load': 35.44},
    {'Node_id': '82', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.1987855, 'x_coord': 12.0, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 148.96, 'Reactive_load': 20.94},
    {'Node_id': '83', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.99812261, 'x_coord': 12.0104, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 158.68, 'Reactive_load': 22.31},
    {'Node_id': '84', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.99812261, 'x_coord': 12.0104, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 228.02, 'Reactive_load': 32.06},
    {'Node_id': '85', 'Voltage_0': 0.985, 'theta_0': 0.0, 'y_coord': 52.9405948, 'x_coord': 12.39144981, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 126.82, 'Reactive_load': 17.83},
    {'Node_id': '86', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.92460105, 'x_coord': 12.63412798, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 158.82, 'Reactive_load': 22.33},
    {'Node_id': '87', 'Voltage_0': 1.015, 'theta_0': 0.0, 'y_coord': 52.90846656, 'x_coord': 12.79269494, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 160.17, 'Reactive_load': 22.52},
    {'Node_id': '88', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.14766093, 'x_coord': 12.45752234, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 153.79, 'Reactive_load': 21.62},
    {'Node_id': '89', 'Voltage_0': 1.005, 'theta_0': 0.0, 'y_coord': 53.19714732, 'x_coord': 13.1920365, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 154.93, 'Reactive_load': 21.78},
    {'Node_id': '90', 'Voltage_0': 0.985, 'theta_0': 0.0, 'y_coord': 53.19714732, 'x_coord': 13.1920365, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 272.97, 'Reactive_load': 38.38},
    {'Node_id': '91', 'Voltage_0': 0.98, 'theta_0': 0.0, 'y_coord': 53.56, 'x_coord': 12.666644, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 298.45, 'Reactive_load': 41.96},
    {'Node_id': '92', 'Voltage_0': 0.99, 'theta_0': 0.0, 'y_coord': 53.56, 'x_coord': 12.666644, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 139.56, 'Reactive_load': 19.62},
    {'Node_id': '93', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.49227081, 'x_coord': 12.24302265, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 140.37, 'Reactive_load': 19.74},
    {'Node_id': '94', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.54988673, 'x_coord': 12.09361533, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 163.58, 'Reactive_load': 23.0},
    {'Node_id': '95', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.42669678, 'x_coord': 12.0788, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 178.24, 'Reactive_load': 25.06},
    {'Node_id': '96', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.3338041, 'x_coord': 11.9039, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 146.63, 'Reactive_load': 20.62},
    {'Node_id': '97', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.47488147, 'x_coord': 11.6184, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_2', 'Power_load': 144.82, 'Reactive_load': 20.36},
    {'Node_id': '98', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.70407892, 'x_coord': 11.8287, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_10', 'Power_load': 158.74, 'Reactive_load': 22.32},
    {'Node_id': '99', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.74282447, 'x_coord': 11.9966, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 168.88, 'Reactive_load': 23.74},
    {'Node_id': '100', 'Voltage_0': 1.017, 'theta_0': 0.0, 'y_coord': 53.76865477, 'x_coord': 12.28705505, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 167.28, 'Reactive_load': 23.52},
    {'Node_id': '101', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.65738539, 'x_coord': 12.5321, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 156.64, 'Reactive_load': 22.02},
    {'Node_id': '102', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.56131536, 'x_coord': 12.512, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 142.84, 'Reactive_load': 20.08},
    {'Node_id': '103', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.76090568, 'x_coord': 12.58100965, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 162.12, 'Reactive_load': 22.79},
    {'Node_id': '104', 'Voltage_0': 0.971, 'theta_0': 0.0, 'y_coord': 54.0497212, 'x_coord': 12.5405391, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 151.31, 'Reactive_load': 21.27},
    {'Node_id': '105', 'Voltage_0': 0.965, 'theta_0': 0.0, 'y_coord': 54.0497212, 'x_coord': 12.5405391, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 231.77, 'Reactive_load': 32.59},
    {'Node_id': '106', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 54.09291807, 'x_coord': 12.13061866, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 131.04, 'Reactive_load': 18.42},
    {'Node_id': '107', 'Voltage_0': 0.952, 'theta_0': 0.0, 'y_coord': 54.33778772, 'x_coord': 12.69307448, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 154.67, 'Reactive_load': 21.75},
    {'Node_id': '108', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 54.0, 'x_coord': 12.76124013, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 172.19, 'Reactive_load': 24.21},
    {'Node_id': '109', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.98782005, 'x_coord': 13.03042139, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 144.97, 'Reactive_load': 20.38},
    {'Node_id': '110', 'Voltage_0': 0.973, 'theta_0': 0.0, 'y_coord': 54.0522274, 'x_coord': 13.24390719, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_9', 'Power_load': 142.99, 'Reactive_load': 20.1},
    {'Node_id': '111', 'Voltage_0': 0.98, 'theta_0': 0.0, 'y_coord': 53.59372993, 'x_coord': 13.19865011, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_1', 'Power_load': 0.0, 'Reactive_load': 0.0},
    {'Node_id': '112', 'Voltage_0': 0.975, 'theta_0': 0.0, 'y_coord': 54.36631804, 'x_coord': 13.44314915, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_1', 'Power_load': 0.0, 'Reactive_load': 0.0},
    {'Node_id': '113', 'Voltage_0': 0.993, 'theta_0': 0.0, 'y_coord': 52.26603138, 'x_coord': 9.7162, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 149.46, 'Reactive_load': 21.01},
    {'Node_id': '114', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.274939, 'x_coord': 10.514143, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 169.61, 'Reactive_load': 23.85},
    {'Node_id': '115', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.274939, 'x_coord': 10.514143, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 185.73, 'Reactive_load': 26.11},
    {'Node_id': '116', 'Voltage_0': 1.005, 'theta_0': 0.0, 'y_coord': 53.19401013, 'x_coord': 11.04104, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 205.4, 'Reactive_load': 28.88},
    {'Node_id': '117', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 52.50293267, 'x_coord': 8.340377708, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_14', 'Power_load': 193.31, 'Reactive_load': 27.18},
    {'Node_id': '118', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.06913042, 'x_coord': 11.204, 'kV_base': 220.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_4', 'Power_load': 146.9, 'Reactive_load': 20.65},
    {'Node_id': '119', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 54.33, 'x_coord': 8.66, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_0', 'Power_load': 0.0, 'Reactive_load': 0.0},
    {'Node_id': '120', 'Voltage_0': 1.01, 'theta_0': 0.0, 'y_coord': 53.14, 'x_coord': 13.44, 'kV_base': 380.0, 'Umin': 0.9, 'Umax': 1.1, 'price_zone': 'R_0', 'Power_load': 0.0, 'Reactive_load': 0.0}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
    {'Line_id': 'L_1', 'fromNode': '1', 'toNode': '2', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1528', 'X [mOhm]': '9062.3', 'C [nF]': '325.05', 'MVA_rating': 491.56, 'Length_km': 27.91, 'is_transformer': 0.0, 'R': 1.528, 'X': 9.0623, 'B': 0.000102117, 'N_b': 1.0},
    {'Line_id': 'L_2', 'fromNode': '3', 'toNode': '5', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3169.27', 'X [mOhm]': '18041.67', 'C [nF]': '847.86', 'MVA_rating': 491.56, 'Length_km': 57.89, 'is_transformer': 0.0, 'R': 3.16927, 'X': 18.04167, 'B': 0.000266363, 'N_b': 1.0},
    {'Line_id': 'L_3', 'fromNode': '6', 'toNode': '7', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1094.76', 'X [mOhm]': '6492.84', 'C [nF]': '232.89', 'MVA_rating': 491.56, 'Length_km': 20.0, 'is_transformer': 0.0, 'R': 1.09476, 'X': 6.49284, 'B': 7.31646e-05, 'N_b': 1.0},
    {'Line_id': 'L_4', 'fromNode': '8', 'toNode': '9', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '967.79', 'X [mOhm]': '9161.16', 'C [nF]': '518.11', 'MVA_rating': 1790.25, 'Length_km': 35.35, 'is_transformer': 0.0, 'R': 0.96779, 'X': 9.16116, 'B': 0.000162769, 'N_b': 1.0},
    {'Line_id': 'T_5', 'fromNode': '8', 'toNode': '5', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_6', 'fromNode': '9', 'toNode': '10', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1106.21', 'X [mOhm]': '10471.39', 'C [nF]': '592.21', 'MVA_rating': 1790.25, 'Length_km': 40.41, 'is_transformer': 0.0, 'R': 1.10621, 'X': 10.47139, 'B': 0.000186048, 'N_b': 1.0},
    {'Line_id': 'L_7', 'fromNode': '5', 'toNode': '11', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3419.45', 'X [mOhm]': '19821.32', 'C [nF]': '710.36', 'MVA_rating': 491.56, 'Length_km': 62.46, 'is_transformer': 0.0, 'R': 3.41945, 'X': 19.82132, 'B': 0.000223166, 'N_b': 1.0},
    {'Line_id': 'L_8', 'fromNode': '11', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1993.53', 'X [mOhm]': '11555.79', 'C [nF]': '414.14', 'MVA_rating': 491.56, 'Length_km': 36.41, 'is_transformer': 0.0, 'R': 1.99353, 'X': 11.55579, 'B': 0.000130106, 'N_b': 1.0},
    {'Line_id': 'L_9', 'fromNode': '3', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3884.69', 'X [mOhm]': '23039.4', 'C [nF]': '826.38', 'MVA_rating': 491.56, 'Length_km': 70.95, 'is_transformer': 0.0, 'R': 3.88469, 'X': 23.0394, 'B': 0.000259615, 'N_b': 1.0},
    {'Line_id': 'L_10', 'fromNode': '11', 'toNode': '13', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2417.06', 'X [mOhm]': '14010.82', 'C [nF]': '502.13', 'MVA_rating': 491.56, 'Length_km': 44.15, 'is_transformer': 0.0, 'R': 2.41706, 'X': 14.01082, 'B': 0.000157749, 'N_b': 1.0},
    {'Line_id': 'L_11', 'fromNode': '12', 'toNode': '14', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '972.6', 'X [mOhm]': '5791.55', 'C [nF]': '211.29', 'MVA_rating': 491.56, 'Length_km': 17.76, 'is_transformer': 0.0, 'R': 0.9726, 'X': 5.79155, 'B': 6.63787e-05, 'N_b': 1.0},
    {'Line_id': 'L_12', 'fromNode': '13', 'toNode': '15', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '995.29', 'X [mOhm]': '5902.88', 'C [nF]': '211.73', 'MVA_rating': 491.56, 'Length_km': 18.18, 'is_transformer': 0.0, 'R': 0.99529, 'X': 5.90288, 'B': 6.65169e-05, 'N_b': 1.0},
    {'Line_id': 'L_13', 'fromNode': '14', 'toNode': '15', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '831.24', 'X [mOhm]': '4949.83', 'C [nF]': '180.58', 'MVA_rating': 491.56, 'Length_km': 15.18, 'is_transformer': 0.0, 'R': 0.83124, 'X': 4.94983, 'B': 5.67309e-05, 'N_b': 1.0},
    {'Line_id': 'L_14', 'fromNode': '12', 'toNode': '16', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2626.12', 'X [mOhm]': '15222.69', 'C [nF]': '545.56', 'MVA_rating': 491.56, 'Length_km': 47.97, 'is_transformer': 0.0, 'R': 2.62612, 'X': 15.22269, 'B': 0.000171393, 'N_b': 1.0},
    {'Line_id': 'L_15', 'fromNode': '15', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3845.48', 'X [mOhm]': '22806.84', 'C [nF]': '818.04', 'MVA_rating': 491.56, 'Length_km': 70.24, 'is_transformer': 0.0, 'R': 3.84548, 'X': 22.80684, 'B': 0.000256995, 'N_b': 1.0},
    {'Line_id': 'L_16', 'fromNode': '16', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2485.79', 'X [mOhm]': '14742.78', 'C [nF]': '528.8', 'MVA_rating': 491.56, 'Length_km': 45.4, 'is_transformer': 0.0, 'R': 2.48579, 'X': 14.74278, 'B': 0.000166127, 'N_b': 1.0},
    {'Line_id': 'L_17', 'fromNode': '18', 'toNode': '19', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1197.01', 'X [mOhm]': '7099.27', 'C [nF]': '254.64', 'MVA_rating': 491.56, 'Length_km': 21.86, 'is_transformer': 0.0, 'R': 1.19701, 'X': 7.09927, 'B': 7.99975e-05, 'N_b': 1.0},
    {'Line_id': 'L_18', 'fromNode': '19', 'toNode': '20', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1732.67', 'X [mOhm]': '10276.18', 'C [nF]': '368.59', 'MVA_rating': 491.56, 'Length_km': 31.65, 'is_transformer': 0.0, 'R': 1.73267, 'X': 10.27618, 'B': 0.000115796, 'N_b': 1.0},
    {'Line_id': 'L_19', 'fromNode': '15', 'toNode': '19', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2473.64', 'X [mOhm]': '14670.72', 'C [nF]': '526.21', 'MVA_rating': 491.56, 'Length_km': 45.18, 'is_transformer': 0.0, 'R': 2.47364, 'X': 14.67072, 'B': 0.000165314, 'N_b': 1.0},
    {'Line_id': 'L_20', 'fromNode': '21', 'toNode': '22', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1021.85', 'X [mOhm]': '6060.4', 'C [nF]': '217.38', 'MVA_rating': 491.56, 'Length_km': 18.66, 'is_transformer': 0.0, 'R': 1.02185, 'X': 6.0604, 'B': 6.82919e-05, 'N_b': 1.0},
    {'Line_id': 'L_21', 'fromNode': '22', 'toNode': '23', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1234.08', 'X [mOhm]': '7319.1', 'C [nF]': '262.52', 'MVA_rating': 491.56, 'Length_km': 22.54, 'is_transformer': 0.0, 'R': 1.23408, 'X': 7.3191, 'B': 8.24731e-05, 'N_b': 1.0},
    {'Line_id': 'L_22', 'fromNode': '23', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1377.82', 'X [mOhm]': '8204.55', 'C [nF]': '299.32', 'MVA_rating': 491.56, 'Length_km': 25.17, 'is_transformer': 0.0, 'R': 1.37782, 'X': 8.20455, 'B': 9.40342e-05, 'N_b': 1.0},
    {'Line_id': 'T_23', 'fromNode': '26', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_24', 'fromNode': '25', 'toNode': '27', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3194.38', 'X [mOhm]': '18945.3', 'C [nF]': '679.53', 'MVA_rating': 491.56, 'Length_km': 58.34, 'is_transformer': 0.0, 'R': 3.19438, 'X': 18.9453, 'B': 0.000213481, 'N_b': 1.0},
    {'Line_id': 'L_25', 'fromNode': '27', 'toNode': '28', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2041.12', 'X [mOhm]': '12105.49', 'C [nF]': '434.2', 'MVA_rating': 491.56, 'Length_km': 37.28, 'is_transformer': 0.0, 'R': 2.04112, 'X': 12.10549, 'B': 0.000136408, 'N_b': 1.0},
    {'Line_id': 'T_26', 'fromNode': '30', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_27', 'fromNode': '17', 'toNode': '31', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1611.36', 'X [mOhm]': '9556.71', 'C [nF]': '342.78', 'MVA_rating': 491.56, 'Length_km': 29.43, 'is_transformer': 0.0, 'R': 1.61136, 'X': 9.55671, 'B': 0.000107688, 'N_b': 1.0},
    {'Line_id': 'L_28', 'fromNode': '29', 'toNode': '31', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '766.33', 'X [mOhm]': '4544.99', 'C [nF]': '163.02', 'MVA_rating': 491.56, 'Length_km': 14.0, 'is_transformer': 0.0, 'R': 0.76633, 'X': 4.54499, 'B': 5.12142e-05, 'N_b': 1.0},
    {'Line_id': 'L_29', 'fromNode': '31', 'toNode': '32', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2836.6', 'X [mOhm]': '16442.73', 'C [nF]': '589.28', 'MVA_rating': 491.56, 'Length_km': 51.81, 'is_transformer': 0.0, 'R': 2.8366, 'X': 16.44273, 'B': 0.000185128, 'N_b': 1.0},
    {'Line_id': 'L_30', 'fromNode': '15', 'toNode': '33', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1896.11', 'X [mOhm]': '11290.8', 'C [nF]': '411.91', 'MVA_rating': 491.56, 'Length_km': 34.63, 'is_transformer': 0.0, 'R': 1.89611, 'X': 11.2908, 'B': 0.000129405, 'N_b': 1.0},
    {'Line_id': 'L_31', 'fromNode': '19', 'toNode': '34', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '982.57', 'X [mOhm]': '6038.43', 'C [nF]': '226.31', 'MVA_rating': 491.56, 'Length_km': 17.95, 'is_transformer': 0.0, 'R': 0.98257, 'X': 6.03843, 'B': 7.10974e-05, 'N_b': 1.0},
    {'Line_id': 'T_32', 'fromNode': '35', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_33', 'fromNode': '33', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1708.94', 'X [mOhm]': '10176.24', 'C [nF]': '371.25', 'MVA_rating': 491.56, 'Length_km': 31.21, 'is_transformer': 0.0, 'R': 1.70894, 'X': 10.17624, 'B': 0.000116632, 'N_b': 1.0},
    {'Line_id': 'L_34', 'fromNode': '34', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1022.3', 'X [mOhm]': '6282.61', 'C [nF]': '235.46', 'MVA_rating': 491.56, 'Length_km': 18.67, 'is_transformer': 0.0, 'R': 1.0223, 'X': 6.28261, 'B': 7.39719e-05, 'N_b': 1.0},
    {'Line_id': 'T_35', 'fromNode': '38', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_36', 'fromNode': '30', 'toNode': '38', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2107.52', 'X [mOhm]': '19387.7', 'C [nF]': '1095.2', 'MVA_rating': 1790.25, 'Length_km': 76.99, 'is_transformer': 0.0, 'R': 2.10752, 'X': 19.3877, 'B': 0.000344067, 'N_b': 1.0},
    {'Line_id': 'L_37', 'fromNode': '39', 'toNode': '40', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '565.86', 'X [mOhm]': '5382.49', 'C [nF]': '310.9', 'MVA_rating': 1790.25, 'Length_km': 20.67, 'is_transformer': 0.0, 'R': 0.56586, 'X': 5.38249, 'B': 9.76721e-05, 'N_b': 1.0},
    {'Line_id': 'L_38', 'fromNode': '40', 'toNode': '41', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '767.82', 'X [mOhm]': '7303.56', 'C [nF]': '421.86', 'MVA_rating': 1790.25, 'Length_km': 28.05, 'is_transformer': 0.0, 'R': 0.76782, 'X': 7.30356, 'B': 0.000132531, 'N_b': 1.0},
    {'Line_id': 'L_39', 'fromNode': '41', 'toNode': '42', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '798.03', 'X [mOhm]': '7554.22', 'C [nF]': '427.23', 'MVA_rating': 1790.25, 'Length_km': 29.15, 'is_transformer': 0.0, 'R': 0.79803, 'X': 7.55422, 'B': 0.000134218, 'N_b': 1.0},
    {'Line_id': 'L_40', 'fromNode': '34', 'toNode': '43', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1332.41', 'X [mOhm]': '7723.52', 'C [nF]': '276.8', 'MVA_rating': 491.56, 'Length_km': 24.34, 'is_transformer': 0.0, 'R': 1.33241, 'X': 7.72352, 'B': 8.69593e-05, 'N_b': 1.0},
    {'Line_id': 'L_41', 'fromNode': '44', 'toNode': '45', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '989.49', 'X [mOhm]': '5735.74', 'C [nF]': '205.56', 'MVA_rating': 491.56, 'Length_km': 18.07, 'is_transformer': 0.0, 'R': 0.98949, 'X': 5.73574, 'B': 6.45786e-05, 'N_b': 1.0},
    {'Line_id': 'L_42', 'fromNode': '45', 'toNode': '46', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1372.57', 'X [mOhm]': '7956.29', 'C [nF]': '285.14', 'MVA_rating': 491.56, 'Length_km': 25.07, 'is_transformer': 0.0, 'R': 1.37257, 'X': 7.95629, 'B': 8.95794e-05, 'N_b': 1.0},
    {'Line_id': 'L_43', 'fromNode': '47', 'toNode': '49', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3860.25', 'X [mOhm]': '22376.48', 'C [nF]': '801.94', 'MVA_rating': 491.56, 'Length_km': 70.51, 'is_transformer': 0.0, 'R': 3.86025, 'X': 22.37648, 'B': 0.000251937, 'N_b': 1.0},
    {'Line_id': 'L_44', 'fromNode': '45', 'toNode': '49', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4718.27', 'X [mOhm]': '27350.09', 'C [nF]': '980.18', 'MVA_rating': 491.56, 'Length_km': 86.18, 'is_transformer': 0.0, 'R': 4.71827, 'X': 27.35009, 'B': 0.000307933, 'N_b': 1.0},
    {'Line_id': 'L_45', 'fromNode': '56', 'toNode': '57', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1799.92', 'X [mOhm]': '10674.99', 'C [nF]': '382.89', 'MVA_rating': 491.56, 'Length_km': 32.88, 'is_transformer': 0.0, 'R': 1.79992, 'X': 10.67499, 'B': 0.000120288, 'N_b': 1.0},
    {'Line_id': 'L_46', 'fromNode': '50', 'toNode': '57', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1282.97', 'X [mOhm]': '7609.08', 'C [nF]': '272.92', 'MVA_rating': 491.56, 'Length_km': 23.43, 'is_transformer': 0.0, 'R': 1.28297, 'X': 7.60908, 'B': 8.57403e-05, 'N_b': 1.0},
    {'Line_id': 'L_47', 'fromNode': '56', 'toNode': '59', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2196.26', 'X [mOhm]': '13025.63', 'C [nF]': '467.21', 'MVA_rating': 491.56, 'Length_km': 40.11, 'is_transformer': 0.0, 'R': 2.19626, 'X': 13.02563, 'B': 0.000146778, 'N_b': 1.0},
    {'Line_id': 'L_48', 'fromNode': '59', 'toNode': '60', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2165.32', 'X [mOhm]': '12551.59', 'C [nF]': '449.83', 'MVA_rating': 491.56, 'Length_km': 39.55, 'is_transformer': 0.0, 'R': 2.16532, 'X': 12.55159, 'B': 0.000141318, 'N_b': 1.0},
    {'Line_id': 'L_49', 'fromNode': '60', 'toNode': '62', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1359.84', 'X [mOhm]': '7882.48', 'C [nF]': '282.5', 'MVA_rating': 491.56, 'Length_km': 24.84, 'is_transformer': 0.0, 'R': 1.35984, 'X': 7.88248, 'B': 8.875e-05, 'N_b': 1.0},
    {'Line_id': 'L_50', 'fromNode': '61', 'toNode': '62', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1257.53', 'X [mOhm]': '7289.47', 'C [nF]': '261.24', 'MVA_rating': 491.56, 'Length_km': 22.97, 'is_transformer': 0.0, 'R': 1.25753, 'X': 7.28947, 'B': 8.2071e-05, 'N_b': 1.0},
    {'Line_id': 'T_51', 'fromNode': '63', 'toNode': '59', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_52', 'fromNode': '63', 'toNode': '64', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2171.56', 'X [mOhm]': '19976.78', 'C [nF]': '1128.47', 'MVA_rating': 1790.25, 'Length_km': 79.33, 'is_transformer': 0.0, 'R': 2.17156, 'X': 19.97678, 'B': 0.000354519, 'N_b': 1.0},
    {'Line_id': 'T_53', 'fromNode': '64', 'toNode': '61', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_54', 'fromNode': '38', 'toNode': '65', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3865.47', 'X [mOhm]': '35559.52', 'C [nF]': '2008.73', 'MVA_rating': 1790.25, 'Length_km': 141.2, 'is_transformer': 0.0, 'R': 3.86547, 'X': 35.55952, 'B': 0.000631061, 'N_b': 1.0},
    {'Line_id': 'L_55', 'fromNode': '64', 'toNode': '65', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1789.45', 'X [mOhm]': '16461.66', 'C [nF]': '929.91', 'MVA_rating': 1790.25, 'Length_km': 65.37, 'is_transformer': 0.0, 'R': 1.78945, 'X': 16.46166, 'B': 0.00029214, 'N_b': 1.0},
    {'Line_id': 'L_56', 'fromNode': '49', 'toNode': '66', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1180.01', 'X [mOhm]': '6998.42', 'C [nF]': '251.02', 'MVA_rating': 491.56, 'Length_km': 21.55, 'is_transformer': 0.0, 'R': 1.18001, 'X': 6.99842, 'B': 7.88603e-05, 'N_b': 2.0},
    {'Line_id': 'L_57', 'fromNode': '49', 'toNode': '66', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1180.01', 'X [mOhm]': '6998.42', 'C [nF]': '251.02', 'MVA_rating': 491.56, 'Length_km': 21.55, 'is_transformer': 0.0, 'R': 1.18001, 'X': 6.99842, 'B': 7.88603e-05, 'N_b': -1.0},
    {'Line_id': 'L_58', 'fromNode': '62', 'toNode': '67', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1968.41', 'X [mOhm]': '11410.16', 'C [nF]': '408.92', 'MVA_rating': 491.56, 'Length_km': 35.95, 'is_transformer': 0.0, 'R': 1.96841, 'X': 11.41016, 'B': 0.000128466, 'N_b': 1.0},
    {'Line_id': 'T_59', 'fromNode': '65', 'toNode': '66', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_60', 'fromNode': '66', 'toNode': '67', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1969.67', 'X [mOhm]': '11417.48', 'C [nF]': '409.18', 'MVA_rating': 491.56, 'Length_km': 35.98, 'is_transformer': 0.0, 'R': 1.96967, 'X': 11.41748, 'B': 0.000128548, 'N_b': 1.0},
    {'Line_id': 'L_61', 'fromNode': '65', 'toNode': '68', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1080.34', 'X [mOhm]': '10226.5', 'C [nF]': '578.36', 'MVA_rating': 1790.25, 'Length_km': 39.46, 'is_transformer': 0.0, 'R': 1.08034, 'X': 10.2265, 'B': 0.000181697, 'N_b': 1.0},
    {'Line_id': 'L_62', 'fromNode': '47', 'toNode': '69', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3746.54', 'X [mOhm]': '22217.02', 'C [nF]': '828.07', 'MVA_rating': 491.56, 'Length_km': 68.43, 'is_transformer': 0.0, 'R': 3.74654, 'X': 22.21702, 'B': 0.000260146, 'N_b': 1.0},
    {'Line_id': 'L_63', 'fromNode': '49', 'toNode': '69', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3328.35', 'X [mOhm]': '19739.83', 'C [nF]': '708.03', 'MVA_rating': 491.56, 'Length_km': 60.79, 'is_transformer': 0.0, 'R': 3.32835, 'X': 19.73983, 'B': 0.000222434, 'N_b': 1.0},
    {'Line_id': 'T_64', 'fromNode': '68', 'toNode': '69', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_65', 'fromNode': '24', 'toNode': '70', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '976.39', 'X [mOhm]': '8982.1', 'C [nF]': '507.39', 'MVA_rating': 1790.25, 'Length_km': 35.67, 'is_transformer': 0.0, 'R': 0.97639, 'X': 8.9821, 'B': 0.000159401, 'N_b': 1.0},
    {'Line_id': 'L_66', 'fromNode': '70', 'toNode': '71', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '559.15', 'X [mOhm]': '5143.8', 'C [nF]': '290.57', 'MVA_rating': 1790.25, 'Length_km': 20.43, 'is_transformer': 0.0, 'R': 0.55915, 'X': 5.1438, 'B': 9.12853e-05, 'N_b': 1.0},
    {'Line_id': 'L_67', 'fromNode': '24', 'toNode': '72', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '319.63', 'X [mOhm]': '3025.6', 'C [nF]': '171.11', 'MVA_rating': 1790.25, 'Length_km': 11.68, 'is_transformer': 0.0, 'R': 0.31963, 'X': 3.0256, 'B': 5.37558e-05, 'N_b': 1.0},
    {'Line_id': 'L_68', 'fromNode': '71', 'toNode': '72', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '451', 'X [mOhm]': '4148.86', 'C [nF]': '234.37', 'MVA_rating': 1790.25, 'Length_km': 16.47, 'is_transformer': 0.0, 'R': 0.451, 'X': 4.14886, 'B': 7.36295e-05, 'N_b': 1.0},
    {'Line_id': 'L_69', 'fromNode': '71', 'toNode': '73', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '604.28', 'X [mOhm]': '5558.97', 'C [nF]': '314.02', 'MVA_rating': 1790.25, 'Length_km': 22.07, 'is_transformer': 0.0, 'R': 0.60428, 'X': 5.55897, 'B': 9.86523e-05, 'N_b': 1.0},
    {'Line_id': 'T_70', 'fromNode': '70', 'toNode': '74', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_71', 'fromNode': '74', 'toNode': '75', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1794.01', 'X [mOhm]': '10639.96', 'C [nF]': '381.64', 'MVA_rating': 491.56, 'Length_km': 32.77, 'is_transformer': 0.0, 'R': 1.79401, 'X': 10.63996, 'B': 0.000119896, 'N_b': 1.0},
    {'Line_id': 'L_72', 'fromNode': '76', 'toNode': '77', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1726.83', 'X [mOhm]': '10241.54', 'C [nF]': '367.35', 'MVA_rating': 491.56, 'Length_km': 31.54, 'is_transformer': 0.0, 'R': 1.72683, 'X': 10.24154, 'B': 0.000115406, 'N_b': 1.0},
    {'Line_id': 'L_73', 'fromNode': '75', 'toNode': '77', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2187.54', 'X [mOhm]': '12680.4', 'C [nF]': '454.45', 'MVA_rating': 491.56, 'Length_km': 39.96, 'is_transformer': 0.0, 'R': 2.18754, 'X': 12.6804, 'B': 0.00014277, 'N_b': 1.0},
    {'Line_id': 'L_74', 'fromNode': '79', 'toNode': '80', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2791.34', 'X [mOhm]': '16554.94', 'C [nF]': '593.8', 'MVA_rating': 491.56, 'Length_km': 50.98, 'is_transformer': 0.0, 'R': 2.79134, 'X': 16.55494, 'B': 0.000186548, 'N_b': 1.0},
    {'Line_id': 'T_75', 'fromNode': '81', 'toNode': '80', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_76', 'fromNode': '77', 'toNode': '82', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3171.55', 'X [mOhm]': '18809.9', 'C [nF]': '674.68', 'MVA_rating': 491.56, 'Length_km': 57.93, 'is_transformer': 0.0, 'R': 3.17155, 'X': 18.8099, 'B': 0.000211957, 'N_b': 1.0},
    {'Line_id': 'L_77', 'fromNode': '82', 'toNode': '83', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1711.1', 'X [mOhm]': '10148.2', 'C [nF]': '364', 'MVA_rating': 491.56, 'Length_km': 31.25, 'is_transformer': 0.0, 'R': 1.7111, 'X': 10.1482, 'B': 0.000114354, 'N_b': 1.0},
    {'Line_id': 'L_78', 'fromNode': '85', 'toNode': '86', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1254.15', 'X [mOhm]': '7438.12', 'C [nF]': '266.79', 'MVA_rating': 491.56, 'Length_km': 22.91, 'is_transformer': 0.0, 'R': 1.25415, 'X': 7.43812, 'B': 8.38146e-05, 'N_b': 1.0},
    {'Line_id': 'L_79', 'fromNode': '86', 'toNode': '87', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '826.43', 'X [mOhm]': '4901.43', 'C [nF]': '175.81', 'MVA_rating': 491.56, 'Length_km': 15.09, 'is_transformer': 0.0, 'R': 0.82643, 'X': 4.90143, 'B': 5.52323e-05, 'N_b': 1.0},
    {'Line_id': 'L_80', 'fromNode': '85', 'toNode': '88', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1797.02', 'X [mOhm]': '10416.7', 'C [nF]': '373.32', 'MVA_rating': 491.56, 'Length_km': 32.82, 'is_transformer': 0.0, 'R': 1.79702, 'X': 10.4167, 'B': 0.000117282, 'N_b': 1.0},
    {'Line_id': 'L_81', 'fromNode': '88', 'toNode': '89', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3776.11', 'X [mOhm]': '21888.75', 'C [nF]': '784.46', 'MVA_rating': 491.56, 'Length_km': 68.97, 'is_transformer': 0.0, 'R': 3.77611, 'X': 21.88875, 'B': 0.000246445, 'N_b': 1.0},
    {'Line_id': 'L_82', 'fromNode': '89', 'toNode': '92', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4086.51', 'X [mOhm]': '24233.08', 'C [nF]': '903.22', 'MVA_rating': 491.56, 'Length_km': 74.64, 'is_transformer': 0.0, 'R': 4.08651, 'X': 24.23308, 'B': 0.000283755, 'N_b': 1.0},
    {'Line_id': 'T_83', 'fromNode': '91', 'toNode': '92', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_84', 'fromNode': '92', 'toNode': '93', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2222.59', 'X [mOhm]': '12883.55', 'C [nF]': '461.73', 'MVA_rating': 491.56, 'Length_km': 40.6, 'is_transformer': 0.0, 'R': 2.22259, 'X': 12.88355, 'B': 0.000145057, 'N_b': 1.0},
    {'Line_id': 'L_85', 'fromNode': '93', 'toNode': '94', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '902.39', 'X [mOhm]': '5230.84', 'C [nF]': '187.46', 'MVA_rating': 491.56, 'Length_km': 16.48, 'is_transformer': 0.0, 'R': 0.90239, 'X': 5.23084, 'B': 5.88923e-05, 'N_b': 1.0},
    {'Line_id': 'L_86', 'fromNode': '82', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1250.71', 'X [mOhm]': '7447.62', 'C [nF]': '271.71', 'MVA_rating': 491.56, 'Length_km': 22.84, 'is_transformer': 0.0, 'R': 1.25071, 'X': 7.44762, 'B': 8.53602e-05, 'N_b': 1.0},
    {'Line_id': 'L_87', 'fromNode': '80', 'toNode': '97', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2284.64', 'X [mOhm]': '13243.23', 'C [nF]': '474.62', 'MVA_rating': 491.56, 'Length_km': 41.73, 'is_transformer': 0.0, 'R': 2.28464, 'X': 13.24323, 'B': 0.000149106, 'N_b': 1.0},
    {'Line_id': 'L_88', 'fromNode': '80', 'toNode': '98', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2298.2', 'X [mOhm]': '13630.2', 'C [nF]': '488.89', 'MVA_rating': 491.56, 'Length_km': 41.98, 'is_transformer': 0.0, 'R': 2.2982, 'X': 13.6302, 'B': 0.000153589, 'N_b': 1.0},
    {'Line_id': 'L_89', 'fromNode': '94', 'toNode': '100', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2105.04', 'X [mOhm]': '12484.59', 'C [nF]': '447.8', 'MVA_rating': 491.56, 'Length_km': 38.45, 'is_transformer': 0.0, 'R': 2.10504, 'X': 12.48459, 'B': 0.000140681, 'N_b': 1.0},
    {'Line_id': 'L_90', 'fromNode': '96', 'toNode': '97', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1884.21', 'X [mOhm]': '10922.07', 'C [nF]': '391.43', 'MVA_rating': 491.56, 'Length_km': 34.41, 'is_transformer': 0.0, 'R': 1.88421, 'X': 10.92207, 'B': 0.000122971, 'N_b': 1.0},
    {'Line_id': 'L_91', 'fromNode': '99', 'toNode': '100', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1480.09', 'X [mOhm]': '8778.18', 'C [nF]': '314.86', 'MVA_rating': 491.56, 'Length_km': 27.03, 'is_transformer': 0.0, 'R': 1.48009, 'X': 8.77818, 'B': 9.89162e-05, 'N_b': 1.0},
    {'Line_id': 'L_92', 'fromNode': '100', 'toNode': '101', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1557.96', 'X [mOhm]': '9030.91', 'C [nF]': '323.65', 'MVA_rating': 491.56, 'Length_km': 28.46, 'is_transformer': 0.0, 'R': 1.55796, 'X': 9.03091, 'B': 0.000101678, 'N_b': 1.0},
    {'Line_id': 'L_93', 'fromNode': '92', 'toNode': '102', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '782.96', 'X [mOhm]': '4662.32', 'C [nF]': '170.09', 'MVA_rating': 491.56, 'Length_km': 14.3, 'is_transformer': 0.0, 'R': 0.78296, 'X': 4.66232, 'B': 5.34353e-05, 'N_b': 1.0},
    {'Line_id': 'L_94', 'fromNode': '101', 'toNode': '102', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '825.1', 'X [mOhm]': '4893.51', 'C [nF]': '175.52', 'MVA_rating': 491.56, 'Length_km': 15.07, 'is_transformer': 0.0, 'R': 0.8251, 'X': 4.89351, 'B': 5.51412e-05, 'N_b': 1.0},
    {'Line_id': 'L_95', 'fromNode': '100', 'toNode': '103', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1482.42', 'X [mOhm]': '8791.96', 'C [nF]': '315.35', 'MVA_rating': 491.56, 'Length_km': 27.08, 'is_transformer': 0.0, 'R': 1.48242, 'X': 8.79196, 'B': 9.90701e-05, 'N_b': 1.0},
    {'Line_id': 'L_96', 'fromNode': '103', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2469.97', 'X [mOhm]': '14317.54', 'C [nF]': '513.12', 'MVA_rating': 491.56, 'Length_km': 45.11, 'is_transformer': 0.0, 'R': 2.46997, 'X': 14.31754, 'B': 0.000161201, 'N_b': 1.0},
    {'Line_id': 'L_97', 'fromNode': '100', 'toNode': '106', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2873.05', 'X [mOhm]': '16654.02', 'C [nF]': '596.85', 'MVA_rating': 491.56, 'Length_km': 52.48, 'is_transformer': 0.0, 'R': 2.87305, 'X': 16.65402, 'B': 0.000187506, 'N_b': 1.0},
    {'Line_id': 'T_98', 'fromNode': '104', 'toNode': '105', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_99', 'fromNode': '106', 'toNode': '107', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3494.76', 'X [mOhm]': '20257.88', 'C [nF]': '726.01', 'MVA_rating': 491.56, 'Length_km': 63.83, 'is_transformer': 0.0, 'R': 3.49476, 'X': 20.25788, 'B': 0.000228083, 'N_b': 1.0},
    {'Line_id': 'L_100', 'fromNode': '108', 'toNode': '109', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1352.72', 'X [mOhm]': '8022.71', 'C [nF]': '287.76', 'MVA_rating': 491.56, 'Length_km': 24.71, 'is_transformer': 0.0, 'R': 1.35272, 'X': 8.02271, 'B': 9.04025e-05, 'N_b': 1.0},
    {'Line_id': 'L_101', 'fromNode': '103', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4152.48', 'X [mOhm]': '24627.62', 'C [nF]': '883.35', 'MVA_rating': 491.56, 'Length_km': 75.84, 'is_transformer': 0.0, 'R': 4.15248, 'X': 24.62762, 'B': 0.000277513, 'N_b': 1.0},
    {'Line_id': 'L_102', 'fromNode': '109', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1201.71', 'X [mOhm]': '7127.1', 'C [nF]': '255.64', 'MVA_rating': 491.56, 'Length_km': 21.95, 'is_transformer': 0.0, 'R': 1.20171, 'X': 7.1271, 'B': 8.03117e-05, 'N_b': 1.0},
    {'Line_id': 'L_103', 'fromNode': '110', 'toNode': '111', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3914.44', 'X [mOhm]': '23309.44', 'C [nF]': '850.38', 'MVA_rating': 491.56, 'Length_km': 71.5, 'is_transformer': 0.0, 'R': 3.91444, 'X': 23.30944, 'B': 0.000267155, 'N_b': 1.0},
    {'Line_id': 'L_104', 'fromNode': '110', 'toNode': '112', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2855.3', 'X [mOhm]': '17002.53', 'C [nF]': '620.29', 'MVA_rating': 491.56, 'Length_km': 52.15, 'is_transformer': 0.0, 'R': 2.8553, 'X': 17.00253, 'B': 0.00019487, 'N_b': 1.0},
    {'Line_id': 'L_105', 'fromNode': '17', 'toNode': '113', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '872.04', 'X [mOhm]': '5054.88', 'C [nF]': '181.16', 'MVA_rating': 491.56, 'Length_km': 15.93, 'is_transformer': 0.0, 'R': 0.87204, 'X': 5.05488, 'B': 5.69131e-05, 'N_b': 1.0},
    {'Line_id': 'L_106', 'fromNode': '32', 'toNode': '113', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3341.41', 'X [mOhm]': '19368.95', 'C [nF]': '694.15', 'MVA_rating': 491.56, 'Length_km': 61.03, 'is_transformer': 0.0, 'R': 3.34141, 'X': 19.36895, 'B': 0.000218074, 'N_b': 1.0},
    {'Line_id': 'L_107', 'fromNode': '32', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '844.99', 'X [mOhm]': '5192.94', 'C [nF]': '194.62', 'MVA_rating': 491.56, 'Length_km': 15.43, 'is_transformer': 0.0, 'R': 0.84499, 'X': 5.19294, 'B': 6.11417e-05, 'N_b': 1.0},
    {'Line_id': 'T_108', 'fromNode': '114', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_109', 'fromNode': '68', 'toNode': '116', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1822.37', 'X [mOhm]': '17250.6', 'C [nF]': '975.61', 'MVA_rating': 1790.25, 'Length_km': 66.57, 'is_transformer': 0.0, 'R': 1.82237, 'X': 17.2506, 'B': 0.000306497, 'N_b': 1.0},
    {'Line_id': 'L_110', 'fromNode': '12', 'toNode': '117', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2309.87', 'X [mOhm]': '13699.4', 'C [nF]': '491.37', 'MVA_rating': 491.56, 'Length_km': 42.19, 'is_transformer': 0.0, 'R': 2.30987, 'X': 13.6994, 'B': 0.000154368, 'N_b': 1.0},
    {'Line_id': 'L_111', 'fromNode': '75', 'toNode': '118', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '986.08', 'X [mOhm]': '5715.94', 'C [nF]': '204.85', 'MVA_rating': 491.56, 'Length_km': 18.01, 'is_transformer': 0.0, 'R': 0.98608, 'X': 5.71594, 'B': 6.43555e-05, 'N_b': 1.0},
    {'Line_id': 'L_112', 'fromNode': '76', 'toNode': '118', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1351.77', 'X [mOhm]': '7835.75', 'C [nF]': '280.82', 'MVA_rating': 491.56, 'Length_km': 24.69, 'is_transformer': 0.0, 'R': 1.35177, 'X': 7.83575, 'B': 8.82222e-05, 'N_b': 1.0},
    {'Line_id': 'L_113', 'fromNode': '68', 'toNode': '70', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2636.85', 'X [mOhm]': '24257.08', 'C [nF]': '1370.27', 'MVA_rating': 1790.25, 'Length_km': 96.32, 'is_transformer': 0.0, 'R': 2.63685, 'X': 24.25708, 'B': 0.000430483, 'N_b': 1.0},
    {'Line_id': 'L_114', 'fromNode': '24', 'toNode': '26', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1208.97', 'X [mOhm]': '11444.19', 'C [nF]': '647.23', 'MVA_rating': 1790.25, 'Length_km': 44.16, 'is_transformer': 0.0, 'R': 1.20897, 'X': 11.44419, 'B': 0.000203333, 'N_b': 1.0},
    {'Line_id': 'L_115', 'fromNode': '8', 'toNode': '4', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1584.64', 'X [mOhm]': '15076.7', 'C [nF]': '865.1', 'MVA_rating': 1790.25, 'Length_km': 57.89, 'is_transformer': 0.0, 'R': 1.58464, 'X': 15.0767, 'B': 0.000271779, 'N_b': 1.0},
    {'Line_id': 'L_116', 'fromNode': '4', 'toNode': '38', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4320.36', 'X [mOhm]': '39744.21', 'C [nF]': '2245.12', 'MVA_rating': 1790.25, 'Length_km': 157.82, 'is_transformer': 0.0, 'R': 4.32036, 'X': 39.74421, 'B': 0.000705325, 'N_b': 1.0},
    {'Line_id': 'L_117', 'fromNode': '42', 'toNode': '65', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3459.56', 'X [mOhm]': '31825.49', 'C [nF]': '1797.8', 'MVA_rating': 1790.25, 'Length_km': 126.38, 'is_transformer': 0.0, 'R': 3.45956, 'X': 31.82549, 'B': 0.000564796, 'N_b': 1.0},
    {'Line_id': 'L_118', 'fromNode': '42', 'toNode': '55', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3040.78', 'X [mOhm]': '27972.95', 'C [nF]': '1580.17', 'MVA_rating': 1790.25, 'Length_km': 111.08, 'is_transformer': 0.0, 'R': 3.04078, 'X': 27.97295, 'B': 0.000496425, 'N_b': 1.0},
    {'Line_id': 'L_119', 'fromNode': '55', 'toNode': '63', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1711.81', 'X [mOhm]': '15747.41', 'C [nF]': '889.56', 'MVA_rating': 1790.25, 'Length_km': 62.53, 'is_transformer': 0.0, 'R': 1.71181, 'X': 15.74741, 'B': 0.000279464, 'N_b': 1.0},
    {'Line_id': 'L_120', 'fromNode': '116', 'toNode': '78', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '943.76', 'X [mOhm]': '8933.66', 'C [nF]': '505.25', 'MVA_rating': 1790.25, 'Length_km': 34.48, 'is_transformer': 0.0, 'R': 0.94376, 'X': 8.93366, 'B': 0.000158729, 'N_b': 1.0},
    {'Line_id': 'L_121', 'fromNode': '78', 'toNode': '81', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1404.94', 'X [mOhm]': '13299.26', 'C [nF]': '752.14', 'MVA_rating': 1790.25, 'Length_km': 51.32, 'is_transformer': 0.0, 'R': 1.40494, 'X': 13.29926, 'B': 0.000236292, 'N_b': 1.0},
    {'Line_id': 'L_122', 'fromNode': '116', 'toNode': '70', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1352.21', 'X [mOhm]': '12800.05', 'C [nF]': '723.91', 'MVA_rating': 1790.25, 'Length_km': 49.4, 'is_transformer': 0.0, 'R': 1.35221, 'X': 12.80005, 'B': 0.000227423, 'N_b': 1.0},
    {'Line_id': 'L_123', 'fromNode': '65', 'toNode': '48', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1804.52', 'X [mOhm]': '16600.31', 'C [nF]': '937.74', 'MVA_rating': 1790.25, 'Length_km': 65.92, 'is_transformer': 0.0, 'R': 1.80452, 'X': 16.60031, 'B': 0.0002946, 'N_b': 1.0},
    {'Line_id': 'L_124', 'fromNode': '48', 'toNode': '73', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1878.16', 'X [mOhm]': '17277.74', 'C [nF]': '976.01', 'MVA_rating': 1790.25, 'Length_km': 68.61, 'is_transformer': 0.0, 'R': 1.87816, 'X': 17.27774, 'B': 0.000306623, 'N_b': 1.0},
    {'Line_id': 'L_125', 'fromNode': '26', 'toNode': '48', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3913.59', 'X [mOhm]': '36002.19', 'C [nF]': '2033.74', 'MVA_rating': 1790.25, 'Length_km': 142.96, 'is_transformer': 0.0, 'R': 3.91359, 'X': 36.00219, 'B': 0.000638918, 'N_b': 1.0},
    {'Line_id': 'L_126', 'fromNode': '68', 'toNode': '48', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1873.27', 'X [mOhm]': '17735.44', 'C [nF]': '990.84', 'MVA_rating': 1790.25, 'Length_km': 68.43, 'is_transformer': 0.0, 'R': 1.87327, 'X': 17.73544, 'B': 0.000311282, 'N_b': 1.0},
    {'Line_id': 'L_127', 'fromNode': '65', 'toNode': '39', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4361.06', 'X [mOhm]': '40118.62', 'C [nF]': '2266.27', 'MVA_rating': 1790.25, 'Length_km': 159.31, 'is_transformer': 0.0, 'R': 4.36106, 'X': 40.11862, 'B': 0.00071197, 'N_b': 1.0},
    {'Line_id': 'L_128', 'fromNode': '42', 'toNode': '63', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3270.6', 'X [mOhm]': '30087.15', 'C [nF]': '1699.6', 'MVA_rating': 1790.25, 'Length_km': 119.47, 'is_transformer': 0.0, 'R': 3.2706, 'X': 30.08715, 'B': 0.000533945, 'N_b': 1.0},
    {'Line_id': 'L_129', 'fromNode': '81', 'toNode': '84', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3401.96', 'X [mOhm]': '31295.63', 'C [nF]': '1767.87', 'MVA_rating': 1790.25, 'Length_km': 124.27, 'is_transformer': 0.0, 'R': 3.40196, 'X': 31.29563, 'B': 0.000555393, 'N_b': 1.0},
    {'Line_id': 'L_130', 'fromNode': '116', 'toNode': '84', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2617.22', 'X [mOhm]': '24076.54', 'C [nF]': '1360.07', 'MVA_rating': 1790.25, 'Length_km': 95.61, 'is_transformer': 0.0, 'R': 2.61722, 'X': 24.07654, 'B': 0.000427279, 'N_b': 1.0},
    {'Line_id': 'L_131', 'fromNode': '84', 'toNode': '90', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3140.3', 'X [mOhm]': '28888.53', 'C [nF]': '1631.89', 'MVA_rating': 1790.25, 'Length_km': 114.71, 'is_transformer': 0.0, 'R': 3.1403, 'X': 28.88853, 'B': 0.000512673, 'N_b': 1.0},
    {'Line_id': 'L_132', 'fromNode': '90', 'toNode': '81', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '5088.91', 'X [mOhm]': '46814.33', 'C [nF]': '2644.51', 'MVA_rating': 1790.25, 'Length_km': 185.9, 'is_transformer': 0.0, 'R': 5.08891, 'X': 46.81433, 'B': 0.000830797, 'N_b': 1.0},
    {'Line_id': 'L_133', 'fromNode': '27', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1016.8', 'X [mOhm]': '5894', 'C [nF]': '211.23', 'MVA_rating': 491.56, 'Length_km': 18.57, 'is_transformer': 0.0, 'R': 1.0168, 'X': 5.894, 'B': 6.63599e-05, 'N_b': 1.0},
    {'Line_id': 'L_134', 'fromNode': '26', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1148.1', 'X [mOhm]': '10920.83', 'C [nF]': '630.8', 'MVA_rating': 1790.25, 'Length_km': 41.94, 'is_transformer': 0.0, 'R': 1.1481, 'X': 10.92083, 'B': 0.000198172, 'N_b': 1.0},
    {'Line_id': 'L_135', 'fromNode': '37', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2401.89', 'X [mOhm]': '14243.25', 'C [nF]': '530.87', 'MVA_rating': 491.56, 'Length_km': 43.87, 'is_transformer': 0.0, 'R': 2.40189, 'X': 14.24325, 'B': 0.000166778, 'N_b': 1.0},
    {'Line_id': 'L_136', 'fromNode': '30', 'toNode': '35', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1025.46', 'X [mOhm]': '9433.5', 'C [nF]': '532.89', 'MVA_rating': 1790.25, 'Length_km': 37.46, 'is_transformer': 0.0, 'R': 1.02546, 'X': 9.4335, 'B': 0.000167412, 'N_b': 1.0},
    {'Line_id': 'L_137', 'fromNode': '26', 'toNode': '35', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3113.75', 'X [mOhm]': '28644.29', 'C [nF]': '1618.1', 'MVA_rating': 1790.25, 'Length_km': 113.74, 'is_transformer': 0.0, 'R': 3.11375, 'X': 28.64429, 'B': 0.000508341, 'N_b': 1.0},
    {'Line_id': 'L_138', 'fromNode': '35', 'toNode': '38', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1200.95', 'X [mOhm]': '11370.13', 'C [nF]': '635.22', 'MVA_rating': 1790.25, 'Length_km': 43.87, 'is_transformer': 0.0, 'R': 1.20095, 'X': 11.37013, 'B': 0.00019956, 'N_b': 1.0},
    {'Line_id': 'L_139', 'fromNode': '8', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3491.01', 'X [mOhm]': '33206.74', 'C [nF]': '1918.05', 'MVA_rating': 1790.25, 'Length_km': 127.53, 'is_transformer': 0.0, 'R': 3.49101, 'X': 33.20674, 'B': 0.000602573, 'N_b': 1.0},
    {'Line_id': 'L_140', 'fromNode': '90', 'toNode': '91', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2043.26', 'X [mOhm]': '19344.82', 'C [nF]': '1080.75', 'MVA_rating': 1790.25, 'Length_km': 74.64, 'is_transformer': 0.0, 'R': 2.04326, 'X': 19.34482, 'B': 0.000339528, 'N_b': 1.0},
    {'Line_id': 'L_141', 'fromNode': '81', 'toNode': '91', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3322.45', 'X [mOhm]': '30564.13', 'C [nF]': '1726.55', 'MVA_rating': 1790.25, 'Length_km': 121.37, 'is_transformer': 0.0, 'R': 3.32245, 'X': 30.56413, 'B': 0.000542412, 'N_b': 1.0},
    {'Line_id': 'L_142', 'fromNode': '107', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2570.33', 'X [mOhm]': '15244.17', 'C [nF]': '546.78', 'MVA_rating': 491.56, 'Length_km': 46.95, 'is_transformer': 0.0, 'R': 2.57033, 'X': 15.24417, 'B': 0.000171776, 'N_b': 1.0},
    {'Line_id': 'L_143', 'fromNode': '106', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2082.87', 'X [mOhm]': '12073.65', 'C [nF]': '432.7', 'MVA_rating': 491.56, 'Length_km': 38.04, 'is_transformer': 0.0, 'R': 2.08287, 'X': 12.07365, 'B': 0.000135937, 'N_b': 1.0},
    {'Line_id': 'L_144', 'fromNode': '108', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1183.47', 'X [mOhm]': '7018.95', 'C [nF]': '251.76', 'MVA_rating': 491.56, 'Length_km': 21.62, 'is_transformer': 0.0, 'R': 1.18347, 'X': 7.01895, 'B': 7.90927e-05, 'N_b': 1.0},
    {'Line_id': 'L_145', 'fromNode': '81', 'toNode': '105', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3289.58', 'X [mOhm]': '30261.76', 'C [nF]': '1709.47', 'MVA_rating': 1790.25, 'Length_km': 120.17, 'is_transformer': 0.0, 'R': 3.28958, 'X': 30.26176, 'B': 0.000537046, 'N_b': 1.0},
    {'Line_id': 'L_146', 'fromNode': '91', 'toNode': '105', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2110.96', 'X [mOhm]': '19419.31', 'C [nF]': '1096.98', 'MVA_rating': 1790.25, 'Length_km': 77.11, 'is_transformer': 0.0, 'R': 2.11096, 'X': 19.41931, 'B': 0.000344626, 'N_b': 1.0},
    {'Line_id': 'L_147', 'fromNode': '90', 'toNode': '105', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3988.96', 'X [mOhm]': '36695.61', 'C [nF]': '2072.91', 'MVA_rating': 1790.25, 'Length_km': 145.72, 'is_transformer': 0.0, 'R': 3.98896, 'X': 36.69561, 'B': 0.000651224, 'N_b': 1.0},
    {'Line_id': 'L_148', 'fromNode': '38', 'toNode': '39', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1346.23', 'X [mOhm]': '12805.47', 'C [nF]': '739.66', 'MVA_rating': 1790.25, 'Length_km': 49.18, 'is_transformer': 0.0, 'R': 1.34623, 'X': 12.80547, 'B': 0.000232371, 'N_b': 1.0},
    {'Line_id': 'L_149', 'fromNode': '54', 'toNode': '52', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3189.94', 'X [mOhm]': '18918.97', 'C [nF]': '678.59', 'MVA_rating': 491.56, 'Length_km': 58.26, 'is_transformer': 0.0, 'R': 3.18994, 'X': 18.91897, 'B': 0.000213185, 'N_b': 1.0},
    {'Line_id': 'L_150', 'fromNode': '41', 'toNode': '53', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1517.39', 'X [mOhm]': '13958.89', 'C [nF]': '788.53', 'MVA_rating': 1790.25, 'Length_km': 55.43, 'is_transformer': 0.0, 'R': 1.51739, 'X': 13.95889, 'B': 0.000247724, 'N_b': 1.0},
    {'Line_id': 'L_151', 'fromNode': '53', 'toNode': '55', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2327', 'X [mOhm]': '21406.73', 'C [nF]': '1209.25', 'MVA_rating': 1790.25, 'Length_km': 85.0, 'is_transformer': 0.0, 'R': 2.327, 'X': 21.40673, 'B': 0.000379897, 'N_b': 1.0},
    {'Line_id': 'L_152', 'fromNode': '99', 'toNode': '98', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '908.83', 'X [mOhm]': '5390.13', 'C [nF]': '193.33', 'MVA_rating': 491.56, 'Length_km': 16.6, 'is_transformer': 0.0, 'R': 0.90883, 'X': 5.39013, 'B': 6.07364e-05, 'N_b': 1.0},
    {'Line_id': 'L_153', 'fromNode': '52', 'toNode': '50', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3079.72', 'X [mOhm]': '17852.02', 'C [nF]': '639.79', 'MVA_rating': 491.56, 'Length_km': 56.25, 'is_transformer': 0.0, 'R': 3.07972, 'X': 17.85202, 'B': 0.000200996, 'N_b': 1.0},
    {'Line_id': 'L_154', 'fromNode': '63', 'toNode': '58', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '833.36', 'X [mOhm]': '7666.3', 'C [nF]': '433.06', 'MVA_rating': 1790.25, 'Length_km': 30.44, 'is_transformer': 0.0, 'R': 0.83336, 'X': 7.6663, 'B': 0.00013605, 'N_b': 1.0},
    {'Line_id': 'L_155', 'fromNode': '58', 'toNode': '51', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '764.19', 'X [mOhm]': '7030.04', 'C [nF]': '397.12', 'MVA_rating': 1790.25, 'Length_km': 27.92, 'is_transformer': 0.0, 'R': 0.76419, 'X': 7.03004, 'B': 0.000124759, 'N_b': 1.0},
    {'Line_id': 'L_156', 'fromNode': '51', 'toNode': '64', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2342.04', 'X [mOhm]': '21545.09', 'C [nF]': '1217.07', 'MVA_rating': 1790.25, 'Length_km': 85.55, 'is_transformer': 0.0, 'R': 2.34204, 'X': 21.54509, 'B': 0.000382354, 'N_b': 1.0},
    {'Line_id': 'L_157', 'fromNode': '5', 'toNode': '7', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1698.17', 'X [mOhm]': '10071.55', 'C [nF]': '361.25', 'MVA_rating': 491.56, 'Length_km': 31.02, 'is_transformer': 0.0, 'R': 1.69817, 'X': 10.07155, 'B': 0.00011349, 'N_b': 1.0},
    {'Line_id': 'L_158', 'fromNode': '48', 'toNode': '72', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2418.54', 'X [mOhm]': '22248.79', 'C [nF]': '1256.82', 'MVA_rating': 1790.25, 'Length_km': 88.35, 'is_transformer': 0.0, 'R': 2.41854, 'X': 22.24879, 'B': 0.000394842, 'N_b': 1.0},
    {'Line_id': 'L_159', 'fromNode': '72', 'toNode': '24', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '319.63', 'X [mOhm]': '3025.6', 'C [nF]': '171.11', 'MVA_rating': 1790.25, 'Length_km': 11.68, 'is_transformer': 0.0, 'R': 0.31963, 'X': 3.0256, 'B': 5.37558e-05, 'N_b': 1.0},
    {'Line_id': 'L_160', 'fromNode': '13', 'toNode': '16', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1410.92', 'X [mOhm]': '8178.57', 'C [nF]': '293.11', 'MVA_rating': 491.56, 'Length_km': 25.77, 'is_transformer': 0.0, 'R': 1.41092, 'X': 8.17857, 'B': 9.20832e-05, 'N_b': 1.0},
    {'Line_id': 'L_161', 'fromNode': '42', 'toNode': '51', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2559.43', 'X [mOhm]': '23544.89', 'C [nF]': '1330.03', 'MVA_rating': 1790.25, 'Length_km': 93.5, 'is_transformer': 0.0, 'R': 2.55943, 'X': 23.54489, 'B': 0.000417841, 'N_b': 1.0},
    {'Line_id': 'L_162', 'fromNode': '51', 'toNode': '65', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1218.2', 'X [mOhm]': '11206.56', 'C [nF]': '633.05', 'MVA_rating': 1790.25, 'Length_km': 44.5, 'is_transformer': 0.0, 'R': 1.2182, 'X': 11.20656, 'B': 0.000198879, 'N_b': 1.0},
    {'Line_id': 'L_163', 'fromNode': '50', 'toNode': '49', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1260.61', 'X [mOhm]': '7307.29', 'C [nF]': '261.88', 'MVA_rating': 491.56, 'Length_km': 23.02, 'is_transformer': 0.0, 'R': 1.26061, 'X': 7.30729, 'B': 8.2272e-05, 'N_b': 1.0},
    {'Line_id': 'L_164', 'fromNode': '52', 'toNode': '44', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3592.22', 'X [mOhm]': '20822.82', 'C [nF]': '746.26', 'MVA_rating': 491.56, 'Length_km': 65.61, 'is_transformer': 0.0, 'R': 3.59222, 'X': 20.82282, 'B': 0.000234444, 'N_b': 1.0},
    {'Line_id': 'L_165', 'fromNode': '8', 'toNode': '9', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '967.79', 'X [mOhm]': '9161.16', 'C [nF]': '518.11', 'MVA_rating': 1790.25, 'Length_km': 35.35, 'is_transformer': 0.0, 'R': 0.96779, 'X': 9.16116, 'B': 0.000162769, 'N_b': 1.0},
    {'Line_id': 'L_166', 'fromNode': '6', 'toNode': '16', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2678.59', 'X [mOhm]': '15886.22', 'C [nF]': '569.81', 'MVA_rating': 491.56, 'Length_km': 48.92, 'is_transformer': 0.0, 'R': 2.67859, 'X': 15.88622, 'B': 0.000179011, 'N_b': 1.0},
    {'Line_id': 'L_167', 'fromNode': '1', 'toNode': '2', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1528', 'X [mOhm]': '9062.3', 'C [nF]': '325.05', 'MVA_rating': 491.56, 'Length_km': 27.91, 'is_transformer': 0.0, 'R': 1.528, 'X': 9.0623, 'B': 0.000102117, 'N_b': 1.0},
    {'Line_id': 'L_168', 'fromNode': '117', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2309.87', 'X [mOhm]': '13699.4', 'C [nF]': '491.37', 'MVA_rating': 491.56, 'Length_km': 42.19, 'is_transformer': 0.0, 'R': 2.30987, 'X': 13.6994, 'B': 0.000154368, 'N_b': 1.0},
    {'Line_id': 'L_169', 'fromNode': '18', 'toNode': '19', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1197.01', 'X [mOhm]': '7099.27', 'C [nF]': '254.64', 'MVA_rating': 491.56, 'Length_km': 21.86, 'is_transformer': 0.0, 'R': 1.19701, 'X': 7.09927, 'B': 7.99975e-05, 'N_b': 1.0},
    {'Line_id': 'L_170', 'fromNode': '20', 'toNode': '19', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1732.67', 'X [mOhm]': '10276.18', 'C [nF]': '368.59', 'MVA_rating': 491.56, 'Length_km': 31.65, 'is_transformer': 0.0, 'R': 1.73267, 'X': 10.27618, 'B': 0.000115796, 'N_b': 1.0},
    {'Line_id': 'L_171', 'fromNode': '21', 'toNode': '32', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1702.39', 'X [mOhm]': '10096.55', 'C [nF]': '362.15', 'MVA_rating': 491.56, 'Length_km': 31.09, 'is_transformer': 0.0, 'R': 1.70239, 'X': 10.09655, 'B': 0.000113773, 'N_b': 1.0},
    {'Line_id': 'L_172', 'fromNode': '28', 'toNode': '29', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '749.25', 'X [mOhm]': '4443.68', 'C [nF]': '159.39', 'MVA_rating': 491.56, 'Length_km': 13.68, 'is_transformer': 0.0, 'R': 0.74925, 'X': 4.44368, 'B': 5.00738e-05, 'N_b': 1.0},
    {'Line_id': 'L_173', 'fromNode': '54', 'toNode': '52', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3189.94', 'X [mOhm]': '18918.97', 'C [nF]': '678.59', 'MVA_rating': 491.56, 'Length_km': 58.26, 'is_transformer': 0.0, 'R': 3.18994, 'X': 18.91897, 'B': 0.000213185, 'N_b': 1.0},
    {'Line_id': 'L_174', 'fromNode': '79', 'toNode': '80', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2791.34', 'X [mOhm]': '16554.94', 'C [nF]': '593.8', 'MVA_rating': 491.56, 'Length_km': 50.98, 'is_transformer': 0.0, 'R': 2.79134, 'X': 16.55494, 'B': 0.000186548, 'N_b': 1.0},
    {'Line_id': 'L_175', 'fromNode': '87', 'toNode': '86', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '826.43', 'X [mOhm]': '4901.43', 'C [nF]': '175.81', 'MVA_rating': 491.56, 'Length_km': 15.09, 'is_transformer': 0.0, 'R': 0.82643, 'X': 4.90143, 'B': 5.52323e-05, 'N_b': 1.0},
    {'Line_id': 'L_176', 'fromNode': '86', 'toNode': '85', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1254.15', 'X [mOhm]': '7438.12', 'C [nF]': '266.79', 'MVA_rating': 491.56, 'Length_km': 22.91, 'is_transformer': 0.0, 'R': 1.25415, 'X': 7.43812, 'B': 8.38146e-05, 'N_b': 1.0},
    {'Line_id': 'L_177', 'fromNode': '111', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3914.44', 'X [mOhm]': '23488.42', 'C [nF]': '897.25', 'MVA_rating': 491.56, 'Length_km': 71.5, 'is_transformer': 0.0, 'R': 3.91444, 'X': 23.48842, 'B': 0.000281879, 'N_b': 1.0},
    {'Line_id': 'L_178', 'fromNode': '112', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2855.3', 'X [mOhm]': '17133.08', 'C [nF]': '654.48', 'MVA_rating': 491.56, 'Length_km': 52.15, 'is_transformer': 0.0, 'R': 2.8553, 'X': 17.13308, 'B': 0.000205611, 'N_b': 1.0},
    {'Line_id': 'T_179', 'fromNode': '89', 'toNode': '90', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_180', 'fromNode': '76', 'toNode': '116', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_181', 'fromNode': '83', 'toNode': '84', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_182', 'fromNode': '47', 'toNode': '48', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_183', 'fromNode': '50', 'toNode': '51', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_184', 'fromNode': '3', 'toNode': '4', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_185', 'fromNode': '6', 'toNode': '7', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1094.76', 'X [mOhm]': '6492.84', 'C [nF]': '232.89', 'MVA_rating': 491.56, 'Length_km': 20.0, 'is_transformer': 0.0, 'R': 1.09476, 'X': 6.49284, 'B': 7.31646e-05, 'N_b': 1.0},
    {'Line_id': 'L_186', 'fromNode': '15', 'toNode': '19', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2473.64', 'X [mOhm]': '14670.72', 'C [nF]': '526.21', 'MVA_rating': 491.56, 'Length_km': 45.18, 'is_transformer': 0.0, 'R': 2.47364, 'X': 14.67072, 'B': 0.000165314, 'N_b': 1.0},
    {'Line_id': 'L_187', 'fromNode': '24', 'toNode': '26', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1208.97', 'X [mOhm]': '11444.19', 'C [nF]': '647.23', 'MVA_rating': 1790.25, 'Length_km': 44.16, 'is_transformer': 0.0, 'R': 1.20897, 'X': 11.44419, 'B': 0.000203333, 'N_b': 1.0},
    {'Line_id': 'L_188', 'fromNode': '84', 'toNode': '26', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3806.08', 'X [mOhm]': '36028.52', 'C [nF]': '2037.6', 'MVA_rating': 1790.25, 'Length_km': 139.03, 'is_transformer': 0.0, 'R': 3.80608, 'X': 36.02852, 'B': 0.000640131, 'N_b': 1.0},
    {'Line_id': 'L_189', 'fromNode': '37', 'toNode': '43', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1548.39', 'X [mOhm]': '8975.44', 'C [nF]': '321.67', 'MVA_rating': 491.56, 'Length_km': 28.28, 'is_transformer': 0.0, 'R': 1.54839, 'X': 8.97544, 'B': 0.000101056, 'N_b': 1.0},
    {'Line_id': 'T_190', 'fromNode': '8', 'toNode': '5', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_191', 'fromNode': '2', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1805.01', 'X [mOhm]': '10705.21', 'C [nF]': '383.98', 'MVA_rating': 491.56, 'Length_km': 32.97, 'is_transformer': 0.0, 'R': 1.80501, 'X': 10.70521, 'B': 0.000120631, 'N_b': 1.0},
    {'Line_id': 'L_192', 'fromNode': '3', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3884.69', 'X [mOhm]': '23039.4', 'C [nF]': '826.38', 'MVA_rating': 491.56, 'Length_km': 70.95, 'is_transformer': 0.0, 'R': 3.88469, 'X': 23.0394, 'B': 0.000259615, 'N_b': 1.0},
    {'Line_id': 'L_193', 'fromNode': '13', 'toNode': '15', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '995.29', 'X [mOhm]': '5902.88', 'C [nF]': '211.73', 'MVA_rating': 491.56, 'Length_km': 18.18, 'is_transformer': 0.0, 'R': 0.99529, 'X': 5.90288, 'B': 6.65169e-05, 'N_b': 1.0},
    {'Line_id': 'L_194', 'fromNode': '14', 'toNode': '15', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '831.24', 'X [mOhm]': '4987.84', 'C [nF]': '190.53', 'MVA_rating': 491.56, 'Length_km': 15.18, 'is_transformer': 0.0, 'R': 0.83124, 'X': 4.98784, 'B': 5.98568e-05, 'N_b': 1.0},
    {'Line_id': 'L_195', 'fromNode': '15', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3845.48', 'X [mOhm]': '22806.84', 'C [nF]': '818.04', 'MVA_rating': 491.56, 'Length_km': 70.24, 'is_transformer': 0.0, 'R': 3.84548, 'X': 22.80684, 'B': 0.000256995, 'N_b': 1.0},
    {'Line_id': 'L_196', 'fromNode': '16', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2485.79', 'X [mOhm]': '14742.78', 'C [nF]': '528.8', 'MVA_rating': 491.56, 'Length_km': 45.4, 'is_transformer': 0.0, 'R': 2.48579, 'X': 14.74278, 'B': 0.000166127, 'N_b': 1.0},
    {'Line_id': 'L_197', 'fromNode': '23', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1377.82', 'X [mOhm]': '8267.54', 'C [nF]': '315.82', 'MVA_rating': 491.56, 'Length_km': 25.17, 'is_transformer': 0.0, 'R': 1.37782, 'X': 8.26754, 'B': 9.92178e-05, 'N_b': 1.0},
    {'Line_id': 'T_198', 'fromNode': '26', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_199', 'fromNode': '30', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_200', 'fromNode': '17', 'toNode': '31', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1611.36', 'X [mOhm]': '9556.71', 'C [nF]': '342.78', 'MVA_rating': 491.56, 'Length_km': 29.43, 'is_transformer': 0.0, 'R': 1.61136, 'X': 9.55671, 'B': 0.000107688, 'N_b': 1.0},
    {'Line_id': 'L_201', 'fromNode': '29', 'toNode': '31', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '766.33', 'X [mOhm]': '4544.99', 'C [nF]': '163.02', 'MVA_rating': 491.56, 'Length_km': 14.0, 'is_transformer': 0.0, 'R': 0.76633, 'X': 4.54499, 'B': 5.12142e-05, 'N_b': 1.0},
    {'Line_id': 'L_202', 'fromNode': '15', 'toNode': '33', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1896.11', 'X [mOhm]': '11377.49', 'C [nF]': '434.62', 'MVA_rating': 491.56, 'Length_km': 34.63, 'is_transformer': 0.0, 'R': 1.89611, 'X': 11.37749, 'B': 0.00013654, 'N_b': 1.0},
    {'Line_id': 'L_203', 'fromNode': '19', 'toNode': '34', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '982.57', 'X [mOhm]': '6038.43', 'C [nF]': '226.31', 'MVA_rating': 491.56, 'Length_km': 17.95, 'is_transformer': 0.0, 'R': 0.98257, 'X': 6.03843, 'B': 7.10974e-05, 'N_b': 1.0},
    {'Line_id': 'L_204', 'fromNode': '33', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1708.94', 'X [mOhm]': '10254.38', 'C [nF]': '391.71', 'MVA_rating': 491.56, 'Length_km': 31.21, 'is_transformer': 0.0, 'R': 1.70894, 'X': 10.25438, 'B': 0.000123059, 'N_b': 1.0},
    {'Line_id': 'L_205', 'fromNode': '34', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1022.3', 'X [mOhm]': '6282.61', 'C [nF]': '235.46', 'MVA_rating': 491.56, 'Length_km': 18.67, 'is_transformer': 0.0, 'R': 1.0223, 'X': 6.28261, 'B': 7.39719e-05, 'N_b': 1.0},
    {'Line_id': 'T_206', 'fromNode': '38', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_207', 'fromNode': '39', 'toNode': '40', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '565.86', 'X [mOhm]': '5433.34', 'C [nF]': '333.06', 'MVA_rating': 1790.25, 'Length_km': 20.67, 'is_transformer': 0.0, 'R': 0.56586, 'X': 5.43334, 'B': 0.000104634, 'N_b': 1.0},
    {'Line_id': 'L_208', 'fromNode': '56', 'toNode': '57', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1799.92', 'X [mOhm]': '10674.99', 'C [nF]': '382.89', 'MVA_rating': 491.56, 'Length_km': 32.88, 'is_transformer': 0.0, 'R': 1.79992, 'X': 10.67499, 'B': 0.000120288, 'N_b': 1.0},
    {'Line_id': 'L_209', 'fromNode': '49', 'toNode': '69', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3328.35', 'X [mOhm]': '19739.83', 'C [nF]': '708.03', 'MVA_rating': 491.56, 'Length_km': 60.79, 'is_transformer': 0.0, 'R': 3.32835, 'X': 19.73983, 'B': 0.000222434, 'N_b': 1.0},
    {'Line_id': 'L_210', 'fromNode': '74', 'toNode': '75', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1794.01', 'X [mOhm]': '10639.96', 'C [nF]': '381.64', 'MVA_rating': 491.56, 'Length_km': 32.77, 'is_transformer': 0.0, 'R': 1.79401, 'X': 10.63996, 'B': 0.000119896, 'N_b': 1.0},
    {'Line_id': 'L_211', 'fromNode': '76', 'toNode': '77', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1726.83', 'X [mOhm]': '10241.54', 'C [nF]': '367.35', 'MVA_rating': 491.56, 'Length_km': 31.54, 'is_transformer': 0.0, 'R': 1.72683, 'X': 10.24154, 'B': 0.000115406, 'N_b': 1.0},
    {'Line_id': 'L_212', 'fromNode': '77', 'toNode': '82', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3171.55', 'X [mOhm]': '18809.9', 'C [nF]': '674.68', 'MVA_rating': 491.56, 'Length_km': 57.93, 'is_transformer': 0.0, 'R': 3.17155, 'X': 18.8099, 'B': 0.000211957, 'N_b': 1.0},
    {'Line_id': 'L_213', 'fromNode': '82', 'toNode': '83', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1711.1', 'X [mOhm]': '10148.2', 'C [nF]': '364', 'MVA_rating': 491.56, 'Length_km': 31.25, 'is_transformer': 0.0, 'R': 1.7111, 'X': 10.1482, 'B': 0.000114354, 'N_b': 1.0},
    {'Line_id': 'L_214', 'fromNode': '83', 'toNode': '85', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2016.43', 'X [mOhm]': '12007.31', 'C [nF]': '438.05', 'MVA_rating': 491.56, 'Length_km': 36.83, 'is_transformer': 0.0, 'R': 2.01643, 'X': 12.00731, 'B': 0.000137617, 'N_b': 1.0},
    {'Line_id': 'L_215', 'fromNode': '94', 'toNode': '95', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1052.64', 'X [mOhm]': '6268.21', 'C [nF]': '228.68', 'MVA_rating': 491.56, 'Length_km': 19.23, 'is_transformer': 0.0, 'R': 1.05264, 'X': 6.26821, 'B': 7.18419e-05, 'N_b': 1.0},
    {'Line_id': 'L_216', 'fromNode': '82', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1250.71', 'X [mOhm]': '7504.81', 'C [nF]': '286.68', 'MVA_rating': 491.56, 'Length_km': 22.84, 'is_transformer': 0.0, 'R': 1.25071, 'X': 7.50481, 'B': 9.00632e-05, 'N_b': 1.0},
    {'Line_id': 'L_217', 'fromNode': '80', 'toNode': '98', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2298.2', 'X [mOhm]': '13630.2', 'C [nF]': '488.89', 'MVA_rating': 491.56, 'Length_km': 41.98, 'is_transformer': 0.0, 'R': 2.2982, 'X': 13.6302, 'B': 0.000153589, 'N_b': 1.0},
    {'Line_id': 'L_218', 'fromNode': '94', 'toNode': '100', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2105.04', 'X [mOhm]': '12484.59', 'C [nF]': '447.8', 'MVA_rating': 491.56, 'Length_km': 38.45, 'is_transformer': 0.0, 'R': 2.10504, 'X': 12.48459, 'B': 0.000140681, 'N_b': 1.0},
    {'Line_id': 'L_219', 'fromNode': '95', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1190.59', 'X [mOhm]': '7089.66', 'C [nF]': '258.65', 'MVA_rating': 491.56, 'Length_km': 21.75, 'is_transformer': 0.0, 'R': 1.19059, 'X': 7.08966, 'B': 8.12573e-05, 'N_b': 1.0},
    {'Line_id': 'L_220', 'fromNode': '100', 'toNode': '103', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1482.42', 'X [mOhm]': '8791.96', 'C [nF]': '315.35', 'MVA_rating': 491.56, 'Length_km': 27.08, 'is_transformer': 0.0, 'R': 1.48242, 'X': 8.79196, 'B': 9.90701e-05, 'N_b': 1.0},
    {'Line_id': 'L_221', 'fromNode': '108', 'toNode': '109', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1352.72', 'X [mOhm]': '8022.71', 'C [nF]': '287.76', 'MVA_rating': 491.56, 'Length_km': 24.71, 'is_transformer': 0.0, 'R': 1.35272, 'X': 8.02271, 'B': 9.04025e-05, 'N_b': 1.0},
    {'Line_id': 'L_222', 'fromNode': '103', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4152.48', 'X [mOhm]': '24627.62', 'C [nF]': '883.35', 'MVA_rating': 491.56, 'Length_km': 75.84, 'is_transformer': 0.0, 'R': 4.15248, 'X': 24.62762, 'B': 0.000277513, 'N_b': 1.0},
    {'Line_id': 'L_223', 'fromNode': '109', 'toNode': '110', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1201.71', 'X [mOhm]': '7127.1', 'C [nF]': '255.64', 'MVA_rating': 491.56, 'Length_km': 21.95, 'is_transformer': 0.0, 'R': 1.20171, 'X': 7.1271, 'B': 8.03117e-05, 'N_b': 1.0},
    {'Line_id': 'L_224', 'fromNode': '32', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '844.99', 'X [mOhm]': '5192.94', 'C [nF]': '194.62', 'MVA_rating': 491.56, 'Length_km': 15.43, 'is_transformer': 0.0, 'R': 0.84499, 'X': 5.19294, 'B': 6.11417e-05, 'N_b': 1.0},
    {'Line_id': 'T_225', 'fromNode': '114', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_226', 'fromNode': '107', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2570.33', 'X [mOhm]': '15244.17', 'C [nF]': '546.78', 'MVA_rating': 491.56, 'Length_km': 46.95, 'is_transformer': 0.0, 'R': 2.57033, 'X': 15.24417, 'B': 0.000171776, 'N_b': 1.0},
    {'Line_id': 'L_227', 'fromNode': '38', 'toNode': '39', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1346.23', 'X [mOhm]': '12926.43', 'C [nF]': '792.38', 'MVA_rating': 1790.25, 'Length_km': 49.18, 'is_transformer': 0.0, 'R': 1.34623, 'X': 12.92643, 'B': 0.000248934, 'N_b': 1.0},
    {'Line_id': 'L_228', 'fromNode': '5', 'toNode': '7', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1698.17', 'X [mOhm]': '10071.55', 'C [nF]': '361.25', 'MVA_rating': 491.56, 'Length_km': 31.02, 'is_transformer': 0.0, 'R': 1.69817, 'X': 10.07155, 'B': 0.00011349, 'N_b': 1.0},
    {'Line_id': 'L_229', 'fromNode': '2', 'toNode': '12', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1805.01', 'X [mOhm]': '10705.21', 'C [nF]': '383.98', 'MVA_rating': 491.56, 'Length_km': 32.97, 'is_transformer': 0.0, 'R': 1.80501, 'X': 10.70521, 'B': 0.000120631, 'N_b': 1.0},
    {'Line_id': 'L_230', 'fromNode': '21', 'toNode': '32', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1702.39', 'X [mOhm]': '10096.55', 'C [nF]': '362.15', 'MVA_rating': 491.56, 'Length_km': 31.09, 'is_transformer': 0.0, 'R': 1.70239, 'X': 10.09655, 'B': 0.000113773, 'N_b': 1.0},
    {'Line_id': 'T_231', 'fromNode': '3', 'toNode': '4', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_232', 'fromNode': '110', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3519.43', 'X [mOhm]': '20400.86', 'C [nF]': '731.13', 'MVA_rating': 491.56, 'Length_km': 64.28, 'is_transformer': 0.0, 'R': 3.51943, 'X': 20.40086, 'B': 0.000229691, 'N_b': 1.0},
    {'Line_id': 'L_233', 'fromNode': '2', 'toNode': '3', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4017.66', 'X [mOhm]': '23288.93', 'C [nF]': '834.64', 'MVA_rating': 491.56, 'Length_km': 73.38, 'is_transformer': 0.0, 'R': 4.01766, 'X': 23.28893, 'B': 0.00026221, 'N_b': 1.0},
    {'Line_id': 'T_234', 'fromNode': '74', 'toNode': '70', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_235', 'fromNode': '47', 'toNode': '48', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_236', 'fromNode': '37', 'toNode': '33', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1708.94', 'X [mOhm]': '9732.98', 'C [nF]': '407.92', 'MVA_rating': 491.56, 'Length_km': 31.21, 'is_transformer': 0.0, 'R': 1.70894, 'X': 9.73298, 'B': 0.000128152, 'N_b': 1.0},
    {'Line_id': 'L_237', 'fromNode': '3', 'toNode': '1', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '4630.57', 'X [mOhm]': '26841.74', 'C [nF]': '961.96', 'MVA_rating': 491.56, 'Length_km': 84.58, 'is_transformer': 0.0, 'R': 4.63057, 'X': 26.84174, 'B': 0.000302209, 'N_b': 1.0},
    {'Line_id': 'L_238', 'fromNode': '110', 'toNode': '107', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3669.78', 'X [mOhm]': '21272.37', 'C [nF]': '762.37', 'MVA_rating': 491.56, 'Length_km': 67.03, 'is_transformer': 0.0, 'R': 3.66978, 'X': 21.27237, 'B': 0.000239506, 'N_b': 1.0},
    {'Line_id': 'L_239', 'fromNode': '84', 'toNode': '26', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3806.08', 'X [mOhm]': '36028.52', 'C [nF]': '2037.6', 'MVA_rating': 1790.25, 'Length_km': 139.03, 'is_transformer': 0.0, 'R': 3.80608, 'X': 36.02852, 'B': 0.000640131, 'N_b': 1.0},
    {'Line_id': 'L_240', 'fromNode': '103', 'toNode': '101', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '916.16', 'X [mOhm]': '5433.59', 'C [nF]': '194.89', 'MVA_rating': 491.56, 'Length_km': 16.73, 'is_transformer': 0.0, 'R': 0.91616, 'X': 5.43359, 'B': 6.12265e-05, 'N_b': 2.0},
    {'Line_id': 'L_241', 'fromNode': '103', 'toNode': '101', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '916.16', 'X [mOhm]': '5433.59', 'C [nF]': '194.89', 'MVA_rating': 491.56, 'Length_km': 16.73, 'is_transformer': 0.0, 'R': 0.91616, 'X': 5.43359, 'B': 6.12265e-05, 'N_b': -1.0},
    {'Line_id': 'T_242', 'fromNode': '3', 'toNode': '4', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_243', 'fromNode': '5', 'toNode': '8', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_244', 'fromNode': '30', 'toNode': '17', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_245', 'fromNode': '35', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_246', 'fromNode': '38', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_247', 'fromNode': '115', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_248', 'fromNode': '26', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_249', 'fromNode': '59', 'toNode': '63', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_250', 'fromNode': '64', 'toNode': '61', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_251', 'fromNode': '51', 'toNode': '50', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_252', 'fromNode': '65', 'toNode': '66', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_253', 'fromNode': '68', 'toNode': '69', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_254', 'fromNode': '48', 'toNode': '47', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_255', 'fromNode': '70', 'toNode': '74', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_256', 'fromNode': '116', 'toNode': '76', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_257', 'fromNode': '81', 'toNode': '80', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_258', 'fromNode': '105', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_259', 'fromNode': '91', 'toNode': '92', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_260', 'fromNode': '90', 'toNode': '89', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_261', 'fromNode': '83', 'toNode': '84', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '6.05', 'X [mOhm]': '9680', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.00605, 'X': 9.68, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'L_262', 'fromNode': '110', 'toNode': '112', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2855.3', 'X [mOhm]': '16261.92', 'C [nF]': '681.55', 'MVA_rating': 491.56, 'Length_km': 52.15, 'is_transformer': 0.0, 'R': 2.8553, 'X': 16.26192, 'B': 0.000214115, 'N_b': 1.0},
    {'Line_id': 'L_263', 'fromNode': '110', 'toNode': '111', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3914.44', 'X [mOhm]': '22294.11', 'C [nF]': '934.37', 'MVA_rating': 491.56, 'Length_km': 71.5, 'is_transformer': 0.0, 'R': 3.91444, 'X': 22.29411, 'B': 0.000293541, 'N_b': 1.0},
    {'Line_id': 'L_264', 'fromNode': '32', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '844.99', 'X [mOhm]': '4864.11', 'C [nF]': '221.16', 'MVA_rating': 491.56, 'Length_km': 15.43, 'is_transformer': 0.0, 'R': 0.84499, 'X': 4.86411, 'B': 6.94795e-05, 'N_b': 2.0},
    {'Line_id': 'L_265', 'fromNode': '32', 'toNode': '114', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '844.99', 'X [mOhm]': '4864.11', 'C [nF]': '221.16', 'MVA_rating': 491.56, 'Length_km': 15.43, 'is_transformer': 0.0, 'R': 0.84499, 'X': 4.86411, 'B': 6.94795e-05, 'N_b': -1.0},
    {'Line_id': 'L_266', 'fromNode': '34', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1022.3', 'X [mOhm]': '5884.77', 'C [nF]': '267.57', 'MVA_rating': 491.56, 'Length_km': 18.67, 'is_transformer': 0.0, 'R': 1.0223, 'X': 5.88477, 'B': 8.40596e-05, 'N_b': 2.0},
    {'Line_id': 'L_267', 'fromNode': '34', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1022.3', 'X [mOhm]': '5884.77', 'C [nF]': '267.57', 'MVA_rating': 491.56, 'Length_km': 18.67, 'is_transformer': 0.0, 'R': 1.0223, 'X': 5.88477, 'B': 8.40596e-05, 'N_b': -1.0},
    {'Line_id': 'L_268', 'fromNode': '94', 'toNode': '95', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1052.64', 'X [mOhm]': '6316.33', 'C [nF]': '241.28', 'MVA_rating': 491.56, 'Length_km': 19.23, 'is_transformer': 0.0, 'R': 1.05264, 'X': 6.31633, 'B': 7.58003e-05, 'N_b': 1.0},
    {'Line_id': 'L_269', 'fromNode': '46', 'toNode': '47', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1644.05', 'X [mOhm]': '9750.56', 'C [nF]': '349.74', 'MVA_rating': 491.56, 'Length_km': 30.03, 'is_transformer': 0.0, 'R': 1.64405, 'X': 9.75056, 'B': 0.000109874, 'N_b': 1.0},
    {'Line_id': 'L_270', 'fromNode': '19', 'toNode': '34', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '982.57', 'X [mOhm]': '5656.06', 'C [nF]': '257.17', 'MVA_rating': 491.56, 'Length_km': 17.95, 'is_transformer': 0.0, 'R': 0.98257, 'X': 5.65606, 'B': 8.07923e-05, 'N_b': 1.0},
    {'Line_id': 'L_271', 'fromNode': '101', 'toNode': '102', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '825.1', 'X [mOhm]': '4893.51', 'C [nF]': '175.52', 'MVA_rating': 491.56, 'Length_km': 15.07, 'is_transformer': 0.0, 'R': 0.8251, 'X': 4.89351, 'B': 5.51412e-05, 'N_b': 1.0},
    {'Line_id': 'L_272', 'fromNode': '92', 'toNode': '102', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '782.96', 'X [mOhm]': '4698.12', 'C [nF]': '179.47', 'MVA_rating': 491.56, 'Length_km': 14.3, 'is_transformer': 0.0, 'R': 0.78296, 'X': 4.69812, 'B': 5.63822e-05, 'N_b': 1.0},
    {'Line_id': 'L_273', 'fromNode': '94', 'toNode': '95', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1052.64', 'X [mOhm]': '5995.17', 'C [nF]': '251.26', 'MVA_rating': 491.56, 'Length_km': 19.23, 'is_transformer': 0.0, 'R': 1.05264, 'X': 5.99517, 'B': 7.89357e-05, 'N_b': 1.0},
    {'Line_id': 'L_274', 'fromNode': '82', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1250.71', 'X [mOhm]': '7123.21', 'C [nF]': '298.54', 'MVA_rating': 491.56, 'Length_km': 22.84, 'is_transformer': 0.0, 'R': 1.25071, 'X': 7.12321, 'B': 9.37891e-05, 'N_b': 1.0},
    {'Line_id': 'L_275', 'fromNode': '46', 'toNode': '47', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1644.05', 'X [mOhm]': '9750.56', 'C [nF]': '349.74', 'MVA_rating': 491.56, 'Length_km': 30.03, 'is_transformer': 0.0, 'R': 1.64405, 'X': 9.75056, 'B': 0.000109874, 'N_b': 1.0},
    {'Line_id': 'L_276', 'fromNode': '19', 'toNode': '34', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '982.57', 'X [mOhm]': '5656.06', 'C [nF]': '257.17', 'MVA_rating': 491.56, 'Length_km': 17.95, 'is_transformer': 0.0, 'R': 0.98257, 'X': 5.65606, 'B': 8.07923e-05, 'N_b': 1.0},
    {'Line_id': 'L_277', 'fromNode': '50', 'toNode': '57', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1282.97', 'X [mOhm]': '7609.08', 'C [nF]': '272.92', 'MVA_rating': 491.56, 'Length_km': 23.43, 'is_transformer': 0.0, 'R': 1.28297, 'X': 7.60908, 'B': 8.57403e-05, 'N_b': 1.0},
    {'Line_id': 'L_278', 'fromNode': '56', 'toNode': '59', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2196.26', 'X [mOhm]': '13025.63', 'C [nF]': '467.21', 'MVA_rating': 491.56, 'Length_km': 40.11, 'is_transformer': 0.0, 'R': 2.19626, 'X': 13.02563, 'B': 0.000146778, 'N_b': 1.0},
    {'Line_id': 'L_279', 'fromNode': '83', 'toNode': '85', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2016.43', 'X [mOhm]': '12099.5', 'C [nF]': '462.2', 'MVA_rating': 491.56, 'Length_km': 36.83, 'is_transformer': 0.0, 'R': 2.01643, 'X': 12.0995, 'B': 0.000145204, 'N_b': 1.0},
    {'Line_id': 'L_280', 'fromNode': '95', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1190.59', 'X [mOhm]': '7144.09', 'C [nF]': '272.9', 'MVA_rating': 491.56, 'Length_km': 21.75, 'is_transformer': 0.0, 'R': 1.19059, 'X': 7.14409, 'B': 8.57341e-05, 'N_b': 1.0},
    {'Line_id': 'L_281', 'fromNode': '83', 'toNode': '85', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2016.43', 'X [mOhm]': '11484.28', 'C [nF]': '481.32', 'MVA_rating': 491.56, 'Length_km': 36.83, 'is_transformer': 0.0, 'R': 2.01643, 'X': 11.48428, 'B': 0.000151211, 'N_b': 1.0},
    {'Line_id': 'L_282', 'fromNode': '95', 'toNode': '96', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1190.59', 'X [mOhm]': '6780.84', 'C [nF]': '284.19', 'MVA_rating': 491.56, 'Length_km': 21.75, 'is_transformer': 0.0, 'R': 1.19059, 'X': 6.78084, 'B': 8.92809e-05, 'N_b': 1.0},
    {'Line_id': 'L_283', 'fromNode': '12', 'toNode': '14', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '972.6', 'X [mOhm]': '5836.02', 'C [nF]': '222.93', 'MVA_rating': 491.56, 'Length_km': 17.76, 'is_transformer': 0.0, 'R': 0.9726, 'X': 5.83602, 'B': 7.00355e-05, 'N_b': 1.0},
    {'Line_id': 'L_284', 'fromNode': '26', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1148.1', 'X [mOhm]': '11023.99', 'C [nF]': '675.76', 'MVA_rating': 1790.25, 'Length_km': 41.94, 'is_transformer': 0.0, 'R': 1.1481, 'X': 11.02399, 'B': 0.000212296, 'N_b': 1.0},
    {'Line_id': 'L_285', 'fromNode': '41', 'toNode': '42', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '798.03', 'X [mOhm]': '7554.22', 'C [nF]': '427.23', 'MVA_rating': 1790.25, 'Length_km': 29.15, 'is_transformer': 0.0, 'R': 0.79803, 'X': 7.55422, 'B': 0.000134218, 'N_b': 1.0},
    {'Line_id': 'L_286', 'fromNode': '116', 'toNode': '78', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '943.76', 'X [mOhm]': '8933.66', 'C [nF]': '505.25', 'MVA_rating': 1790.25, 'Length_km': 34.48, 'is_transformer': 0.0, 'R': 0.94376, 'X': 8.93366, 'B': 0.000158729, 'N_b': 1.0},
    {'Line_id': 'L_287', 'fromNode': '40', 'toNode': '41', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '767.82', 'X [mOhm]': '7372.55', 'C [nF]': '451.93', 'MVA_rating': 1790.25, 'Length_km': 28.05, 'is_transformer': 0.0, 'R': 0.76782, 'X': 7.37255, 'B': 0.000141978, 'N_b': 1.0},
    {'Line_id': 'L_288', 'fromNode': '27', 'toNode': '28', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2041.12', 'X [mOhm]': '12105.49', 'C [nF]': '434.2', 'MVA_rating': 491.56, 'Length_km': 37.28, 'is_transformer': 0.0, 'R': 2.04112, 'X': 12.10549, 'B': 0.000136408, 'N_b': 1.0},
    {'Line_id': 'L_289', 'fromNode': '22', 'toNode': '23', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1234.08', 'X [mOhm]': '7319.1', 'C [nF]': '262.52', 'MVA_rating': 491.56, 'Length_km': 22.54, 'is_transformer': 0.0, 'R': 1.23408, 'X': 7.3191, 'B': 8.24731e-05, 'N_b': 1.0},
    {'Line_id': 'L_290', 'fromNode': '116', 'toNode': '70', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1352.21', 'X [mOhm]': '12800.05', 'C [nF]': '723.91', 'MVA_rating': 1790.25, 'Length_km': 49.4, 'is_transformer': 0.0, 'R': 1.35221, 'X': 12.80005, 'B': 0.000227423, 'N_b': 1.0},
    {'Line_id': 'L_291', 'fromNode': '116', 'toNode': '68', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1822.37', 'X [mOhm]': '17250.6', 'C [nF]': '975.61', 'MVA_rating': 1790.25, 'Length_km': 66.57, 'is_transformer': 0.0, 'R': 1.82237, 'X': 17.2506, 'B': 0.000306497, 'N_b': 1.0},
    {'Line_id': 'L_292', 'fromNode': '78', 'toNode': '81', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1404.94', 'X [mOhm]': '13299.26', 'C [nF]': '752.14', 'MVA_rating': 1790.25, 'Length_km': 51.32, 'is_transformer': 0.0, 'R': 1.40494, 'X': 13.29926, 'B': 0.000236292, 'N_b': 1.0},
    {'Line_id': 'L_293', 'fromNode': '65', 'toNode': '68', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1080.34', 'X [mOhm]': '10226.5', 'C [nF]': '578.36', 'MVA_rating': 1790.25, 'Length_km': 39.46, 'is_transformer': 0.0, 'R': 1.08034, 'X': 10.2265, 'B': 0.000181697, 'N_b': 1.0},
    {'Line_id': 'L_294', 'fromNode': '23', 'toNode': '25', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1377.82', 'X [mOhm]': '7847.17', 'C [nF]': '328.88', 'MVA_rating': 491.56, 'Length_km': 25.17, 'is_transformer': 0.0, 'R': 1.37782, 'X': 7.84717, 'B': 0.000103321, 'N_b': 1.0},
    {'Line_id': 'L_295', 'fromNode': '25', 'toNode': '27', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3194.38', 'X [mOhm]': '18945.3', 'C [nF]': '679.53', 'MVA_rating': 491.56, 'Length_km': 58.34, 'is_transformer': 0.0, 'R': 3.19438, 'X': 18.9453, 'B': 0.000213481, 'N_b': 1.0},
    {'Line_id': 'L_296', 'fromNode': '26', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1148.1', 'X [mOhm]': '10323', 'C [nF]': '710.67', 'MVA_rating': 1790.25, 'Length_km': 41.94, 'is_transformer': 0.0, 'R': 1.1481, 'X': 10.323, 'B': 0.000223264, 'N_b': 1.0},
    {'Line_id': 'L_297', 'fromNode': '4', 'toNode': '8', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1584.64', 'X [mOhm]': '15221.58', 'C [nF]': '903.24', 'MVA_rating': 1790.25, 'Length_km': 57.89, 'is_transformer': 0.0, 'R': 1.58464, 'X': 15.22158, 'B': 0.000283761, 'N_b': 1.0},
    {'Line_id': 'L_298', 'fromNode': '8', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3491.01', 'X [mOhm]': '33520.41', 'C [nF]': '2054.76', 'MVA_rating': 1790.25, 'Length_km': 127.53, 'is_transformer': 0.0, 'R': 3.49101, 'X': 33.52041, 'B': 0.000645522, 'N_b': 1.0},
    {'Line_id': 'L_299', 'fromNode': '99', 'toNode': '100', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1480.09', 'X [mOhm]': '8778.18', 'C [nF]': '314.86', 'MVA_rating': 491.56, 'Length_km': 27.03, 'is_transformer': 0.0, 'R': 1.48009, 'X': 8.77818, 'B': 9.89162e-05, 'N_b': 1.0},
    {'Line_id': 'L_300', 'fromNode': '40', 'toNode': '39', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '565.86', 'X [mOhm]': '5087.84', 'C [nF]': '350.26', 'MVA_rating': 1790.25, 'Length_km': 20.67, 'is_transformer': 0.0, 'R': 0.56586, 'X': 5.08784, 'B': 0.000110037, 'N_b': 1.0},
    {'Line_id': 'L_301', 'fromNode': '38', 'toNode': '39', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1346.23', 'X [mOhm]': '12104.46', 'C [nF]': '833.31', 'MVA_rating': 1790.25, 'Length_km': 49.18, 'is_transformer': 0.0, 'R': 1.34623, 'X': 12.10446, 'B': 0.000261792, 'N_b': 1.0},
    {'Line_id': 'L_302', 'fromNode': '98', 'toNode': '99', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '908.83', 'X [mOhm]': '5390.13', 'C [nF]': '193.33', 'MVA_rating': 491.56, 'Length_km': 16.6, 'is_transformer': 0.0, 'R': 0.90883, 'X': 5.39013, 'B': 6.07364e-05, 'N_b': 1.0},
    {'Line_id': 'L_303', 'fromNode': '40', 'toNode': '41', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '767.82', 'X [mOhm]': '6903.74', 'C [nF]': '475.27', 'MVA_rating': 1790.25, 'Length_km': 28.05, 'is_transformer': 0.0, 'R': 0.76782, 'X': 6.90374, 'B': 0.00014931, 'N_b': 1.0},
    {'Line_id': 'L_304', 'fromNode': '92', 'toNode': '102', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '782.96', 'X [mOhm]': '4459.23', 'C [nF]': '186.89', 'MVA_rating': 491.56, 'Length_km': 14.3, 'is_transformer': 0.0, 'R': 0.78296, 'X': 4.45923, 'B': 5.87132e-05, 'N_b': 1.0},
    {'Line_id': 'L_305', 'fromNode': '55', 'toNode': '119', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1333.18', 'X [mOhm]': '12619.98', 'C [nF]': '713.73', 'MVA_rating': 1790.25, 'Length_km': 48.7, 'is_transformer': 0.0, 'R': 1.33318, 'X': 12.61998, 'B': 0.000224225, 'N_b': 2.0},
    {'Line_id': 'L_306', 'fromNode': '55', 'toNode': '119', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1333.18', 'X [mOhm]': '12619.98', 'C [nF]': '713.73', 'MVA_rating': 1790.25, 'Length_km': 48.7, 'is_transformer': 0.0, 'R': 1.33318, 'X': 12.61998, 'B': 0.000224225, 'N_b': -1.0},
    {'Line_id': 'L_307', 'fromNode': '90', 'toNode': '120', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '678.66', 'X [mOhm]': '6424.2', 'C [nF]': '363.32', 'MVA_rating': 1790.25, 'Length_km': 24.79, 'is_transformer': 0.0, 'R': 0.67866, 'X': 6.4242, 'B': 0.00011414, 'N_b': 2.0},
    {'Line_id': 'L_308', 'fromNode': '90', 'toNode': '120', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '678.66', 'X [mOhm]': '6424.2', 'C [nF]': '363.32', 'MVA_rating': 1790.25, 'Length_km': 24.79, 'is_transformer': 0.0, 'R': 0.67866, 'X': 6.4242, 'B': 0.00011414, 'N_b': -1.0},
    {'Line_id': 'L_309', 'fromNode': '9', 'toNode': '10', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1106.21', 'X [mOhm]': '10471.39', 'C [nF]': '592.21', 'MVA_rating': 1790.25, 'Length_km': 40.41, 'is_transformer': 0.0, 'R': 1.10621, 'X': 10.47139, 'B': 0.000186048, 'N_b': 1.0},
    {'Line_id': 'L_310', 'fromNode': '54', 'toNode': '56', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3000.79', 'X [mOhm]': '17797.13', 'C [nF]': '638.35', 'MVA_rating': 491.56, 'Length_km': 54.81, 'is_transformer': 0.0, 'R': 3.00079, 'X': 17.79713, 'B': 0.000200544, 'N_b': 2.0},
    {'Line_id': 'L_311', 'fromNode': '54', 'toNode': '56', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3000.79', 'X [mOhm]': '17797.13', 'C [nF]': '638.35', 'MVA_rating': 491.56, 'Length_km': 54.81, 'is_transformer': 0.0, 'R': 3.00079, 'X': 17.79713, 'B': 0.000200544, 'N_b': -1.0},
    {'Line_id': 'L_312', 'fromNode': '14', 'toNode': '15', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '831.24', 'X [mOhm]': '4734.22', 'C [nF]': '198.42', 'MVA_rating': 491.56, 'Length_km': 15.18, 'is_transformer': 0.0, 'R': 0.83124, 'X': 4.73422, 'B': 6.23355e-05, 'N_b': 1.0},
    {'Line_id': 'L_313', 'fromNode': '6', 'toNode': '16', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '2678.59', 'X [mOhm]': '15886.22', 'C [nF]': '569.81', 'MVA_rating': 491.56, 'Length_km': 48.92, 'is_transformer': 0.0, 'R': 2.67859, 'X': 15.88622, 'B': 0.000179011, 'N_b': 1.0},
    {'Line_id': 'L_314', 'fromNode': '28', 'toNode': '29', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '749.25', 'X [mOhm]': '4443.68', 'C [nF]': '159.39', 'MVA_rating': 491.56, 'Length_km': 13.68, 'is_transformer': 0.0, 'R': 0.74925, 'X': 4.44368, 'B': 5.00738e-05, 'N_b': 1.0},
    {'Line_id': 'L_315', 'fromNode': '108', 'toNode': '104', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1183.47', 'X [mOhm]': '7018.95', 'C [nF]': '251.76', 'MVA_rating': 491.56, 'Length_km': 21.62, 'is_transformer': 0.0, 'R': 1.18347, 'X': 7.01895, 'B': 7.90927e-05, 'N_b': 1.0},
    {'Line_id': 'L_316', 'fromNode': '15', 'toNode': '33', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1896.11', 'X [mOhm]': '10798.98', 'C [nF]': '452.59', 'MVA_rating': 491.56, 'Length_km': 34.63, 'is_transformer': 0.0, 'R': 1.89611, 'X': 10.79898, 'B': 0.000142185, 'N_b': 1.0},
    {'Line_id': 'L_317', 'fromNode': '21', 'toNode': '22', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '1021.85', 'X [mOhm]': '6060.4', 'C [nF]': '217.38', 'MVA_rating': 491.56, 'Length_km': 18.66, 'is_transformer': 0.0, 'R': 1.02185, 'X': 6.0604, 'B': 6.82919e-05, 'N_b': 1.0},
    {'Line_id': 'L_318', 'fromNode': '12', 'toNode': '14', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '972.6', 'X [mOhm]': '5539.28', 'C [nF]': '232.16', 'MVA_rating': 491.56, 'Length_km': 17.76, 'is_transformer': 0.0, 'R': 0.9726, 'X': 5.53928, 'B': 7.29352e-05, 'N_b': 1.0},
    {'Line_id': 'L_319', 'fromNode': '8', 'toNode': '115', 'Branchtype (Line=1;Transformer=2)': '1', 'R [mOhm]': '3491.01', 'X [mOhm]': '31388.92', 'C [nF]': '2160.91', 'MVA_rating': 1790.25, 'Length_km': 127.53, 'is_transformer': 0.0, 'R': 3.49101, 'X': 31.38892, 'B': 0.00067887, 'N_b': 1.0},
    {'Line_id': 'T_320', 'fromNode': '35', 'toNode': '36', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0},
    {'Line_id': 'T_321', 'fromNode': '38', 'toNode': '37', 'Branchtype (Line=1;Transformer=2)': '2', 'R [mOhm]': '18.05', 'X [mOhm]': '28879.99', 'C [nF]': '0', 'MVA_rating': 800.0, 'Length_km': 0.0, 'is_transformer': 1.0, 'R': 0.01805, 'X': 28.87999, 'B': 0.0, 'N_b': 1.0}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)




    gen_data=[
    {'Gen_name': 'Gen_1', 'node': '115', 'MWmax': 400.0, 'MWmin': 168.0, 'MVARmax': 200.0, 'MVARmin': -200.0, 'Fueltype': 'Gas', 'Linear factor': 121.56, 'CO2-Coefficient [t CO2/MWh_electric]': 0.74, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_2', 'node': '12', 'MWmax': 600.0, 'MWmin': 297.0, 'MVARmax': 300.0, 'MVARmin': -300.0, 'Fueltype': 'CCGT', 'Linear factor': 80.25, 'CO2-Coefficient [t CO2/MWh_electric]': 0.49, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_3', 'node': '38', 'MWmax': 1500.0, 'MWmin': 623.0, 'MVARmax': 750.0, 'MVARmin': -750.0, 'Fueltype': 'Hard Coal', 'Linear factor': 47.42, 'CO2-Coefficient [t CO2/MWh_electric]': 0.8, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_4', 'node': '35', 'MWmax': 1600.0, 'MWmin': 843.0, 'MVARmax': 800.0, 'MVARmin': -800.0, 'Fueltype': 'Lignite', 'Linear factor': 36.05, 'CO2-Coefficient [t CO2/MWh_electric]': 1.1, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_5', 'node': '19', 'MWmax': 800.0, 'MWmin': 389.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 76.86, 'CO2-Coefficient [t CO2/MWh_electric]': 0.47, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_6', 'node': '72', 'MWmax': 1400.0, 'MWmin': 566.0, 'MVARmax': 700.0, 'MVARmin': -700.0, 'Fueltype': 'Hard Coal', 'Linear factor': 46.72, 'CO2-Coefficient [t CO2/MWh_electric]': 0.79, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_7', 'node': '26', 'MWmax': 1600.0, 'MWmin': 870.0, 'MVARmax': 800.0, 'MVARmin': -800.0, 'Fueltype': 'Lignite', 'Linear factor': 37.28, 'CO2-Coefficient [t CO2/MWh_electric]': 1.14, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_8', 'node': '22', 'MWmax': 400.0, 'MWmin': 177.0, 'MVARmax': 200.0, 'MVARmin': -200.0, 'Fueltype': 'Gas', 'Linear factor': 129.22, 'CO2-Coefficient [t CO2/MWh_electric]': 0.79, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_9', 'node': '27', 'MWmax': 600.0, 'MWmin': 282.0, 'MVARmax': 300.0, 'MVARmin': -300.0, 'Fueltype': 'CCGT', 'Linear factor': 65.64, 'CO2-Coefficient [t CO2/MWh_electric]': 0.4, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_10', 'node': '30', 'MWmax': 1300.0, 'MWmin': 551.0, 'MVARmax': 650.0, 'MVARmin': -650.0, 'Fueltype': 'Hard Coal', 'Linear factor': 48.19, 'CO2-Coefficient [t CO2/MWh_electric]': 0.82, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_11', 'node': '8', 'MWmax': 700.0, 'MWmin': 299.0, 'MVARmax': 350.0, 'MVARmin': -350.0, 'Fueltype': 'Hard Coal', 'Linear factor': 48.53, 'CO2-Coefficient [t CO2/MWh_electric]': 0.82, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_12', 'node': '34', 'MWmax': 800.0, 'MWmin': 378.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 66.57, 'CO2-Coefficient [t CO2/MWh_electric]': 0.41, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_13', 'node': '37', 'MWmax': 800.0, 'MWmin': 395.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 79.66, 'CO2-Coefficient [t CO2/MWh_electric]': 0.49, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_14', 'node': '42', 'MWmax': 1000.0, 'MWmin': 488.0, 'MVARmax': 500.0, 'MVARmin': -500.0, 'Fueltype': 'CCGT', 'Linear factor': 77.41, 'CO2-Coefficient [t CO2/MWh_electric]': 0.47, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_15', 'node': '70', 'MWmax': 400.0, 'MWmin': 170.0, 'MVARmax': 200.0, 'MVARmin': -200.0, 'Fueltype': 'Gas', 'Linear factor': 123.39, 'CO2-Coefficient [t CO2/MWh_electric]': 0.75, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_16', 'node': '78', 'MWmax': 700.0, 'MWmin': 345.0, 'MVARmax': 350.0, 'MVARmin': -350.0, 'Fueltype': 'CCGT', 'Linear factor': 79.09, 'CO2-Coefficient [t CO2/MWh_electric]': 0.48, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_17', 'node': '76', 'MWmax': 400.0, 'MWmin': 174.0, 'MVARmax': 200.0, 'MVARmin': -200.0, 'Fueltype': 'Gas', 'Linear factor': 126.23, 'CO2-Coefficient [t CO2/MWh_electric]': 0.77, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_18', 'node': '68', 'MWmax': 1600.0, 'MWmin': 674.0, 'MVARmax': 800.0, 'MVARmin': -800.0, 'Fueltype': 'Hard Coal', 'Linear factor': 47.85, 'CO2-Coefficient [t CO2/MWh_electric]': 0.81, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_19', 'node': '85', 'MWmax': 800.0, 'MWmin': 382.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 70.58, 'CO2-Coefficient [t CO2/MWh_electric]': 0.43, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_20', 'node': '84', 'MWmax': 1500.0, 'MWmin': 634.0, 'MVARmax': 750.0, 'MVARmin': -750.0, 'Fueltype': 'Hard Coal', 'Linear factor': 48.02, 'CO2-Coefficient [t CO2/MWh_electric]': 0.81, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_21', 'node': '48', 'MWmax': 1600.0, 'MWmin': 861.0, 'MVARmax': 800.0, 'MVARmin': -800.0, 'Fueltype': 'Lignite', 'Linear factor': 37.06, 'CO2-Coefficient [t CO2/MWh_electric]': 1.13, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_22', 'node': '92', 'MWmax': 400.0, 'MWmin': 169.0, 'MVARmax': 200.0, 'MVARmin': -200.0, 'Fueltype': 'Gas', 'Linear factor': 122.47, 'CO2-Coefficient [t CO2/MWh_electric]': 0.75, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_23', 'node': '31', 'MWmax': 800.0, 'MWmin': 393.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 78.52, 'CO2-Coefficient [t CO2/MWh_electric]': 0.48, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_24', 'node': '81', 'MWmax': 1500.0, 'MWmin': 619.0, 'MVARmax': 750.0, 'MVARmin': -750.0, 'Fueltype': 'Hard Coal', 'Linear factor': 47.24, 'CO2-Coefficient [t CO2/MWh_electric]': 0.8, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_25', 'node': '4', 'MWmax': 1600.0, 'MWmin': 834.0, 'MVARmax': 800.0, 'MVARmin': -800.0, 'Fueltype': 'Lignite', 'Linear factor': 35.46, 'CO2-Coefficient [t CO2/MWh_electric]': 1.08, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_26', 'node': '69', 'MWmax': 800.0, 'MWmin': 392.0, 'MVARmax': 400.0, 'MVARmin': -400.0, 'Fueltype': 'CCGT', 'Linear factor': 77.96, 'CO2-Coefficient [t CO2/MWh_electric]': 0.48, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_27', 'node': '26', 'MWmax': 780.0, 'MWmin': 329.0, 'MVARmax': 390.0, 'MVARmin': -390.0, 'Fueltype': 'CCGT', 'Linear factor': 54.25, 'CO2-Coefficient [t CO2/MWh_electric]': 0.33, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_28', 'node': '91', 'MWmax': 780.0, 'MWmin': 326.0, 'MVARmax': 390.0, 'MVARmin': -390.0, 'Fueltype': 'CCGT', 'Linear factor': 54.16, 'CO2-Coefficient [t CO2/MWh_electric]': 0.33, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_29', 'node': '91', 'MWmax': 750.0, 'MWmin': 312.0, 'MVARmax': 375.0, 'MVARmin': -375.0, 'Fueltype': 'CCGT', 'Linear factor': 54.07, 'CO2-Coefficient [t CO2/MWh_electric]': 0.33, 'Ren_zone': 'Gen'},
    {'Gen_name': 'Gen_30', 'node': '112', 'MWmax': 874.0, 'MWmin': 0.0, 'MVARmax': 437.0, 'MVARmin': -437.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_1'},
    {'Gen_name': 'Gen_31', 'node': '111', 'MWmax': 966.0, 'MWmin': 0.0, 'MVARmax': 483.0, 'MVARmin': -483.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_1'},
    {'Gen_name': 'Gen_32', 'node': '105', 'MWmax': 901.6, 'MWmin': 0.0, 'MVARmax': 450.8, 'MVARmin': -450.8, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_33', 'node': '116', 'MWmax': 869.4, 'MWmin': 0.0, 'MVARmax': 434.7, 'MVARmin': -434.7, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_3'},
    {'Gen_name': 'Gen_34', 'node': '73', 'MWmax': 798.1, 'MWmin': 0.0, 'MVARmax': 399.05, 'MVARmin': -399.05, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_3'},
    {'Gen_name': 'Gen_35', 'node': '24', 'MWmax': 483.0, 'MWmin': 0.0, 'MVARmax': 241.5, 'MVARmin': -241.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_3'},
    {'Gen_name': 'Gen_36', 'node': '110', 'MWmax': 524.4, 'MWmin': 0.0, 'MVARmax': 262.2, 'MVARmin': -262.2, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_37', 'node': '87', 'MWmax': 547.4, 'MWmin': 0.0, 'MVARmax': 273.7, 'MVARmin': -273.7, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_38', 'node': '103', 'MWmax': 529.0, 'MWmin': 0.0, 'MVARmax': 264.5, 'MVARmin': -264.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_39', 'node': '90', 'MWmax': 805.0, 'MWmin': 0.0, 'MVARmax': 402.5, 'MVARmin': -402.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_40', 'node': '96', 'MWmax': 460.0, 'MWmin': 0.0, 'MVARmax': 230.0, 'MVARmin': -230.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_41', 'node': '104', 'MWmax': 621.0, 'MWmin': 0.0, 'MVARmax': 310.5, 'MVARmin': -310.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_42', 'node': '53', 'MWmax': 644.0, 'MWmin': 0.0, 'MVARmax': 322.0, 'MVARmin': -322.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_5'},
    {'Gen_name': 'Gen_43', 'node': '11', 'MWmax': 575.0, 'MWmin': 0.0, 'MVARmax': 287.5, 'MVARmin': -287.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_44', 'node': '67', 'MWmax': 506.0, 'MWmin': 0.0, 'MVARmax': 253.0, 'MVARmin': -253.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_5'},
    {'Gen_name': 'Gen_45', 'node': '28', 'MWmax': 276.0, 'MWmin': 0.0, 'MVARmax': 138.0, 'MVARmin': -138.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_46', 'node': '15', 'MWmax': 690.0, 'MWmin': 0.0, 'MVARmax': 345.0, 'MVARmin': -345.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_47', 'node': '75', 'MWmax': 345.0, 'MWmin': 0.0, 'MVARmax': 172.5, 'MVARmin': -172.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_3'},
    {'Gen_name': 'Gen_48', 'node': '107', 'MWmax': 345.0, 'MWmin': 0.0, 'MVARmax': 172.5, 'MVARmin': -172.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_49', 'node': '106', 'MWmax': 506.0, 'MWmin': 0.0, 'MVARmax': 253.0, 'MVARmin': -253.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_50', 'node': '98', 'MWmax': 460.0, 'MWmin': 0.0, 'MVARmax': 230.0, 'MVARmin': -230.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_7'},
    {'Gen_name': 'Gen_51', 'node': '52', 'MWmax': 598.0, 'MWmin': 0.0, 'MVARmax': 299.0, 'MVARmin': -299.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_8'},
    {'Gen_name': 'Gen_52', 'node': '58', 'MWmax': 667.0, 'MWmin': 0.0, 'MVARmax': 333.5, 'MVARmin': -333.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_5'},
    {'Gen_name': 'Gen_53', 'node': '82', 'MWmax': 575.0, 'MWmin': 0.0, 'MVARmax': 287.5, 'MVARmin': -287.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_54', 'node': '81', 'MWmax': 625.6, 'MWmin': 0.0, 'MVARmax': 312.8, 'MVARmin': -312.8, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_7'},
    {'Gen_name': 'Gen_55', 'node': '7', 'MWmax': 713.0, 'MWmin': 0.0, 'MVARmax': 356.5, 'MVARmin': -356.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_56', 'node': '63', 'MWmax': 644.0, 'MWmin': 0.0, 'MVARmax': 322.0, 'MVARmin': -322.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_5'},
    {'Gen_name': 'Gen_57', 'node': '19', 'MWmax': 460.0, 'MWmin': 0.0, 'MVARmax': 230.0, 'MVARmin': -230.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_58', 'node': '100', 'MWmax': 678.5, 'MWmin': 0.0, 'MVARmax': 339.25, 'MVARmin': -339.25, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_59', 'node': '93', 'MWmax': 345.0, 'MWmin': 0.0, 'MVARmax': 172.5, 'MVARmin': -172.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_60', 'node': '84', 'MWmax': 644.0, 'MWmin': 0.0, 'MVARmax': 322.0, 'MVARmin': -322.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_61', 'node': '95', 'MWmax': 253.0, 'MWmin': 0.0, 'MVARmax': 126.5, 'MVARmin': -126.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_62', 'node': '88', 'MWmax': 207.0, 'MWmin': 0.0, 'MVARmax': 103.5, 'MVARmin': -103.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_63', 'node': '101', 'MWmax': 299.0, 'MWmin': 0.0, 'MVARmax': 149.5, 'MVARmin': -149.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_64', 'node': '60', 'MWmax': 322.0, 'MWmin': 0.0, 'MVARmax': 161.0, 'MVARmin': -161.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_5'},
    {'Gen_name': 'Gen_65', 'node': '91', 'MWmax': 667.0, 'MWmin': 0.0, 'MVARmax': 333.5, 'MVARmin': -333.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_2'},
    {'Gen_name': 'Gen_66', 'node': '79', 'MWmax': 368.0, 'MWmin': 0.0, 'MVARmax': 184.0, 'MVARmin': -184.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_7'},
    {'Gen_name': 'Gen_67', 'node': '85', 'MWmax': 259.9, 'MWmin': 0.0, 'MVARmax': 129.95, 'MVARmin': -129.95, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_68', 'node': '97', 'MWmax': 287.5, 'MWmin': 0.0, 'MVARmax': 143.75, 'MVARmin': -143.75, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_69', 'node': '117', 'MWmax': 207.0, 'MWmin': 0.0, 'MVARmax': 103.5, 'MVARmin': -103.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_70', 'node': '1', 'MWmax': 299.0, 'MWmin': 0.0, 'MVARmax': 149.5, 'MVARmin': -149.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_71', 'node': '113', 'MWmax': 253.0, 'MWmin': 0.0, 'MVARmax': 126.5, 'MVARmin': -126.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_6'},
    {'Gen_name': 'Gen_72', 'node': '97', 'MWmax': 345.0, 'MWmin': 0.0, 'MVARmax': 172.5, 'MVARmin': -172.5, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_4'},
    {'Gen_name': 'Gen_73', 'node': '44', 'MWmax': 138.0, 'MWmin': 0.0, 'MVARmax': 69.0, 'MVARmin': -69.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_8'},
    {'Gen_name': 'Gen_74', 'node': '41', 'MWmax': 322.0, 'MWmin': 0.0, 'MVARmax': 161.0, 'MVARmin': -161.0, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_8'},
    {'Gen_name': 'Gen_75', 'node': '39', 'MWmax': 124.2, 'MWmin': 0.0, 'MVARmax': 62.1, 'MVARmin': -62.1, 'Fueltype': 'Wind', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Wind_8'},
    {'Gen_name': 'Gen_76', 'node': '40', 'MWmax': 900.0, 'MWmin': 0.0, 'MVARmax': 450.0, 'MVARmin': -450.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_77', 'node': '55', 'MWmax': 890.0, 'MWmin': 0.0, 'MVARmax': 445.0, 'MVARmin': -445.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_78', 'node': '56', 'MWmax': 700.0, 'MWmin': 0.0, 'MVARmax': 350.0, 'MVARmin': -350.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_79', 'node': '46', 'MWmax': 600.0, 'MWmin': 0.0, 'MVARmax': 300.0, 'MVARmin': -300.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_80', 'node': '54', 'MWmax': 840.0, 'MWmin': 0.0, 'MVARmax': 420.0, 'MVARmin': -420.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_81', 'node': '66', 'MWmax': 760.0, 'MWmin': 0.0, 'MVARmax': 380.0, 'MVARmin': -380.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_82', 'node': '65', 'MWmax': 860.0, 'MWmin': 0.0, 'MVARmax': 430.0, 'MVARmin': -430.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_83', 'node': '49', 'MWmax': 630.0, 'MWmin': 0.0, 'MVARmax': 315.0, 'MVARmin': -315.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_84', 'node': '61', 'MWmax': 690.0, 'MWmin': 0.0, 'MVARmax': 345.0, 'MVARmin': -345.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_85', 'node': '62', 'MWmax': 565.0, 'MWmin': 0.0, 'MVARmax': 282.5, 'MVARmin': -282.5, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_86', 'node': '16', 'MWmax': 620.0, 'MWmin': 0.0, 'MVARmax': 310.0, 'MVARmin': -310.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_87', 'node': '71', 'MWmax': 750.0, 'MWmin': 0.0, 'MVARmax': 375.0, 'MVARmin': -375.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_88', 'node': '94', 'MWmax': 470.0, 'MWmin': 0.0, 'MVARmax': 235.0, 'MVARmin': -235.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_89', 'node': '58', 'MWmax': 820.0, 'MWmin': 0.0, 'MVARmax': 410.0, 'MVARmin': -410.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_90', 'node': '41', 'MWmax': 760.0, 'MWmin': 0.0, 'MVARmax': 380.0, 'MVARmin': -380.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_91', 'node': '40', 'MWmax': 590.0, 'MWmin': 0.0, 'MVARmax': 295.0, 'MVARmin': -295.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_92', 'node': '39', 'MWmax': 680.0, 'MWmin': 0.0, 'MVARmax': 340.0, 'MVARmin': -340.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_93', 'node': '60', 'MWmax': 380.0, 'MWmin': 0.0, 'MVARmax': 190.0, 'MVARmin': -190.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_94', 'node': '44', 'MWmax': 250.0, 'MWmin': 0.0, 'MVARmax': 125.0, 'MVARmin': -125.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_95', 'node': '45', 'MWmax': 260.0, 'MWmin': 0.0, 'MVARmax': 130.0, 'MVARmin': -130.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_96', 'node': '52', 'MWmax': 290.0, 'MWmin': 0.0, 'MVARmax': 145.0, 'MVARmin': -145.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_97', 'node': '42', 'MWmax': 860.0, 'MWmin': 0.0, 'MVARmax': 430.0, 'MVARmin': -430.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_98', 'node': '53', 'MWmax': 860.0, 'MWmin': 0.0, 'MVARmax': 430.0, 'MVARmin': -430.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_99', 'node': '73', 'MWmax': 770.0, 'MWmin': 0.0, 'MVARmax': 385.0, 'MVARmin': -385.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_100', 'node': '96', 'MWmax': 870.0, 'MWmin': 0.0, 'MVARmax': 435.0, 'MVARmin': -435.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_101', 'node': '2', 'MWmax': 730.0, 'MWmin': 0.0, 'MVARmax': 365.0, 'MVARmin': -365.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_102', 'node': '32', 'MWmax': 700.0, 'MWmin': 0.0, 'MVARmax': 350.0, 'MVARmin': -350.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_103', 'node': '20', 'MWmax': 650.0, 'MWmin': 0.0, 'MVARmax': 325.0, 'MVARmin': -325.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_104', 'node': '51', 'MWmax': 790.0, 'MWmin': 0.0, 'MVARmax': 395.0, 'MVARmin': -395.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_105', 'node': '99', 'MWmax': 390.0, 'MWmin': 0.0, 'MVARmax': 195.0, 'MVARmin': -195.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_106', 'node': '100', 'MWmax': 370.0, 'MWmin': 0.0, 'MVARmax': 185.0, 'MVARmin': -185.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_107', 'node': '106', 'MWmax': 520.0, 'MWmin': 0.0, 'MVARmax': 260.0, 'MVARmin': -260.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_108', 'node': '63', 'MWmax': 690.0, 'MWmin': 0.0, 'MVARmax': 345.0, 'MVARmin': -345.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_109', 'node': '64', 'MWmax': 530.0, 'MWmin': 0.0, 'MVARmax': 265.0, 'MVARmin': -265.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'},
    {'Gen_name': 'Gen_110', 'node': '48', 'MWmax': 228.0, 'MWmin': 0.0, 'MVARmax': 114.0, 'MVARmin': -114.0, 'Fueltype': 'Solar', 'Linear factor': 0.0, 'CO2-Coefficient [t CO2/MWh_electric]': 0.0, 'Ren_zone': 'Solar_1'}
    ]
    gen_AC=pd.DataFrame(gen_data)
    
    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    if DC:
        nodes_DC_data=[
        {'Node_id': '80_dc','kV_base':400, 'x_coord': 11.3733, 'y_coord': 53.7},
        {'Node_id': '69_dc','kV_base':400, 'x_coord': 10.4895, 'y_coord': 53.4667},
        {'Node_id': '110_dc','kV_base':400, 'x_coord': 13.2439, 'y_coord': 54.0522},
        {'Node_id': '83_dc','kV_base':400, 'x_coord': 12.0104, 'y_coord': 52.9981},
        {'Node_id': '25_dc','kV_base':400, 'x_coord': 10.8276, 'y_coord': 52.4645},
        {'Node_id': '37_dc','kV_base':400, 'x_coord': 9.3515, 'y_coord': 52.82},
        {'Node_id': '55_dc','kV_base':400, 'x_coord': 8.9324, 'y_coord': 54.0608},
        {'Node_id': '10_dc','kV_base':400, 'x_coord': 9.8995, 'y_coord': 51.5814}
        ]
        nodes_DC =pd.DataFrame(nodes_DC_data)

        lines_DC_data =[
        {'Line_id': 'L_DC1', 'fromNode': '69_dc', 'toNode': '80_dc', 'R': 0.823585732, 'MW_rating': 2000.0, 'Length_km': 63.8438552},
        {'Line_id': 'L_DC2', 'fromNode': '25_dc', 'toNode': '69_dc', 'R': 1.466952158, 'MW_rating': 2000.0, 'Length_km': 113.7172216},
        {'Line_id': 'L_DC3', 'fromNode': '37_dc', 'toNode': '69_dc', 'R': 1.348723978, 'MW_rating': 2000.0, 'Length_km': 104.5522464},
        {'Line_id': 'L_DC4', 'fromNode': '80_dc', 'toNode': '110_dc', 'R': 1.660552942, 'MW_rating': 2000.0, 'Length_km': 128.7250342},
        {'Line_id': 'L_DC5', 'fromNode': '55_dc', 'toNode': '80_dc', 'R': 2.127629027, 'MW_rating': 2000.0, 'Length_km': 164.9324827},
        {'Line_id': 'L_DC6', 'fromNode': '69_dc', 'toNode': '83_dc', 'R': 1.468650729, 'MW_rating': 2000.0, 'Length_km': 113.8488937},
        {'Line_id': 'L_DC7', 'fromNode': '10_dc', 'toNode': '25_dc', 'R': 1.508624433, 'MW_rating': 2000.0, 'Length_km': 116.9476304},
        {'Line_id': 'L_DC8', 'fromNode': '83_dc', 'toNode': '110_dc', 'R': 1.841831153, 'MW_rating': 2000.0, 'Length_km': 142.7776088},
        {'Line_id': 'L_DC9', 'fromNode': '37_dc', 'toNode': '55_dc', 'R': 1.815403575, 'MW_rating': 2000.0, 'Length_km': 140.7289593},
        {'Line_id': 'L_DC10', 'fromNode': '10_dc', 'toNode': '37_dc', 'R': 1.840945618, 'MW_rating': 2000.0, 'Length_km': 142.7089627}
        ]
        lines_DC = pd.DataFrame(lines_DC_data)

        conv_data =[
        {'Conv_id': 'C_80','AC_node': '80', 'DC_node': '80_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_69','AC_node': '69', 'DC_node': '69_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_110','AC_node': '110', 'DC_node': '110_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_83','AC_node': '83', 'DC_node': '83_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_25','AC_node': '25', 'DC_node': '25_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_37','AC_node': '37', 'DC_node': '37_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_55','AC_node': '55', 'DC_node': '55_dc', 'MVA_rating': 2000.0},
        {'Conv_id': 'C_10','AC_node': '10', 'DC_node': '10_dc', 'MVA_rating': 2000.0}
        ]
        Converters_ACDC = pd.DataFrame(conv_data)

    if not Gen_Pmin:
        gen_AC['MWmin']*=0
        
    if curtailment_allowed == 0:
        mask = gen_AC['Ren_zone'] != 'Gen'
        gen_AC.loc[mask, 'MVARmax'] *= 0
        gen_AC.loc[mask, 'MVARmin'] *= 0
    nodes_AC['Power_load']  *= load_factor
    nodes_AC['Reactive_load']  *= load_factor
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='Ohm')
    grid.name = 'case118_TEP'
    
    
    grid._nodes_AC[slack-1].type = 'Slack'
    
    pyf.add_price_zone(grid,'R_0' ,1)
    pyf.add_price_zone(grid,'R_1' ,1)
    pyf.add_price_zone(grid,'R_2' ,1)
    pyf.add_price_zone(grid,'R_3' ,1)
    pyf.add_price_zone(grid,'R_4' ,1)
    pyf.add_price_zone(grid,'R_5' ,1)
    pyf.add_price_zone(grid,'R_9' ,1)
    pyf.add_price_zone(grid,'R_10' ,1)
    pyf.add_price_zone(grid,'R_14' ,1)
    
    pyf.add_RenSource_zone(grid, 'Wind_1')
    pyf.add_RenSource_zone(grid, 'Wind_2')
    pyf.add_RenSource_zone(grid, 'Wind_3')
    pyf.add_RenSource_zone(grid, 'Wind_4')
    pyf.add_RenSource_zone(grid, 'Wind_5')
    pyf.add_RenSource_zone(grid, 'Wind_6')
    pyf.add_RenSource_zone(grid, 'Wind_7')
    pyf.add_RenSource_zone(grid, 'Wind_8')
    
    pyf.add_RenSource_zone(grid, 'Solar_1')
 

    for index, row in nodes_AC.iterrows():
        node_name=nodes_AC.at[index,'Node_id']
        price_zone=nodes_AC.at[index,'price_zone']
        ACDC='AC'
        pyf.assign_nodeToPrice_Zone(grid,node_name, price_zone,ACDC)     
    pyf.add_generators(grid,gen_AC,curtailment_allowed)    
    
    avg_w_price = sum(gen.lf*gen.Max_pow_gen for gen in grid.Generators)/sum(gen.Max_pow_gen for gen in grid.Generators)
    price_alpha = 0.75
    range_price = price_alpha*max(gen.lf for gen in grid.Generators)+(1-price_alpha)*min(gen.lf for gen in grid.Generators)
 
    
    pyf.add_extgrid(grid,'10','Ext_10',lf=0,MVAmax=export_capacity/3,MWmax=0) 
    pyf.add_extgrid(grid, '119','Ext_119',lf=0,MVAmax=export_capacity/3,MWmax=0)  
    pyf.add_extgrid(grid, '120','Ext_120',lf=0,MVAmax=export_capacity/3,MWmax=0) 
    pyf.create_geometries_from_coords(grid)
    rec_exp_info=[
        {'kV': 220, 'rec_cost': 275000, 'rec_Rating':  900, 'exp_cost':  700000},
        {'kV': 380, 'rec_cost': 550000, 'rec_Rating': 2369, 'exp_cost':1400000},
        {'kV': 'Transformer', 'rec_cost': None, 'rec_Rating': None,   'exp_cost': 8800000},
        {'kv': 'DC_line' ,  'rec_cost': None, 'rec_Rating': None,   'exp_cost': 1400000},
        {'kv': 'Conv' ,  'rec_cost': None, 'rec_Rating': None,   'exp_cost': 130000}
        ]
    upgradable_data=[]
    exp_elements =[]    
    if exp_tf:
        
        # Expand Elements
       
        lines_AC.set_index('Line_id', inplace=True)
        
        for line in list(grid.lines_AC):  # Create a copy of the list
            name = line.name  
            # if name in {'L_6','L_305','L_306','L_307','L_308','L_309'}: #not expand export lines
            #     continue
            N_b = lines_AC.loc[name,'N_b']
            
            N_max =N_b*3
            N_i = N_max
            if not line.isTf:
                if  line.kV_base == 220:
                    if exp_220== 'Reconducting':
                        if N_b==-1 or N_b ==2:
                            continue
                        row={'Line_id': name, 'r_new': line.R, 'x_new': line.X, 'b_new': line.B, 'MVA_rating_new': 900, 'base_cost':275000*line.Length_km}
                        upgradable_data.append(row)
                    elif exp_220 == 'Expandable':
                        if N_b == -1:
                            grid.lines_AC.remove(line)
                            line.remove()
                            continue
                        exp_row= {'name':name,'N_b':N_b,'N_i':N_i,'N_max':N_max,'Life_time':25,'base_cost':700000*line.Length_km}
                        exp_elements.append(exp_row)
                elif line.kV_base == 380:
                    if exp_380== 'Reconducting':
                        if N_b==-1 or N_b ==2:
                            continue
                        row={'Line_id': name, 'r_new': line.R, 'x_new': line.X, 'b_new': line.B, 'MVA_rating_new': 2369, 'base_cost':550000*line.Length_km}
                        upgradable_data.append(row)
                    elif exp_380 == 'Expandable':
                        if N_b == -1:
                            grid.lines_AC.remove(line)
                            line.remove()
                            continue
                        exp_row= {'name':name,'N_b':N_b,'N_i':N_i,'N_max':N_max,'Life_time':25,'base_cost':1400000*line.Length_km}
                        exp_elements.append(exp_row)
            else:
                N_max= 5
                exp_row= {'name':name,'N_b':N_b,'N_i':N_i,'N_max':N_max,'Life_time':25,'base_cost':8800000}
                exp_elements.append(exp_row)
            
                
                                    
    if DC_exp:                
        lines_DC.set_index('Line_id', inplace=True)
        
        for line in list(grid.lines_DC):  # Create a copy of the list
            name = line.name    
            N_b = 0
            N_i=1
            N_max =2
            exp_row= {'name':name,'N_b':N_b,'N_i':N_i,'N_max':N_max,'Life_time':25,'base_cost':1400000*line.Length_km}
            exp_elements.append(exp_row)
        for conv in list(grid.Converters_ACDC):  # Create a copy of the list
            name = conv.name
            N_b = 0
            N_i=1
            N_max =2
            exp_row= {'name':name,'N_b':N_b,'N_i':N_i,'N_max':N_max,'Life_time':25,'base_cost':130000*conv.MVA_max}
            exp_elements.append(exp_row)
        
    exp_elements = pd.DataFrame(exp_elements)
    upgradable_data = pd.DataFrame(upgradable_data)
    if not exp_elements.empty:
        pyf.expand_elements_from_pd(grid,exp_elements)
    if not upgradable_data.empty:
        pyf.repurpose_element_from_pd(grid,upgradable_data)

    TS_wl= pd.read_csv(f'{path}/118_benchmark_wl.csv')
    pyf.add_TimeSeries(grid,TS_wl)
    
    # Return the grid
    return grid,res
