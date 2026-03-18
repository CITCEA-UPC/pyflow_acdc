

import pyflow_acdc as pyf
import pandas as pd


def Borssele_3_and_4():    
    
    S_base=100
    WACC=0.06
    FLH = 4500
    
    if FLH:
        gamma_limit = 0.95
    else: 
        gamma_limit = 1

    LCoE = 79
    
    Turbine = 9.5
    Nc = 3

    # DataFrame Code:
    nodes_AC_data = [
        {'Node_id': 'T1', 'kV_base': 66.0, 'x_coord': 3.007097, 'y_coord': 51.602446, 'geometry': 'POINT (3.007097 51.602446)'},
        {'Node_id': 'T2', 'kV_base': 66.0, 'x_coord': 2.987324, 'y_coord': 51.615206, 'geometry': 'POINT (2.987324 51.615206)'},
        {'Node_id': 'T3', 'kV_base': 66.0, 'x_coord': 3.009493, 'y_coord': 51.62557, 'geometry': 'POINT (3.009493 51.62557)'},
        {'Node_id': 'T4', 'kV_base': 66.0, 'x_coord': 2.966396, 'y_coord': 51.627465, 'geometry': 'POINT (2.966396 51.627465)'},
        {'Node_id': 'T5', 'kV_base': 66.0, 'x_coord': 2.988121, 'y_coord': 51.633521, 'geometry': 'POINT (2.988121 51.633521)'},
        {'Node_id': 'T6', 'kV_base': 66.0, 'x_coord': 2.947505, 'y_coord': 51.639599, 'geometry': 'POINT (2.947505 51.639599)'},
        {'Node_id': 'T7', 'kV_base': 66.0, 'x_coord': 3.014262, 'y_coord': 51.638311, 'geometry': 'POINT (3.014262 51.638311)'},
        {'Node_id': 'T8', 'kV_base': 66.0, 'x_coord': 3.01723, 'y_coord': 51.649834, 'geometry': 'POINT (3.01723 51.649834)'},
        {'Node_id': 'T9', 'kV_base': 66.0, 'x_coord': 2.925951, 'y_coord': 51.651387, 'geometry': 'POINT (2.925951 51.651387)'},
        {'Node_id': 'T10', 'kV_base': 66.0, 'x_coord': 2.992081, 'y_coord': 51.654673, 'geometry': 'POINT (2.992081 51.654673)'},
        {'Node_id': 'T11', 'kV_base': 66.0, 'x_coord': 2.954194, 'y_coord': 51.655288, 'geometry': 'POINT (2.954194 51.655288)'},
        {'Node_id': 'T12', 'kV_base': 66.0, 'x_coord': 2.968419, 'y_coord': 51.645259, 'geometry': 'POINT (2.968419 51.645259)'},
        {'Node_id': 'T13', 'kV_base': 66.0, 'x_coord': 3.021282, 'y_coord': 51.662531, 'geometry': 'POINT (3.021282 51.662531)'},
        {'Node_id': 'T14', 'kV_base': 66.0, 'x_coord': 3.003126, 'y_coord': 51.668719, 'geometry': 'POINT (3.003126 51.668719)'},
        {'Node_id': 'T15', 'kV_base': 66.0, 'x_coord': 2.923419, 'y_coord': 51.668251, 'geometry': 'POINT (2.923419 51.668251)'},
        {'Node_id': 'T16', 'kV_base': 66.0, 'x_coord': 2.977256, 'y_coord': 51.669803, 'geometry': 'POINT (2.977256 51.669803)'},
        {'Node_id': 'T17', 'kV_base': 66.0, 'x_coord': 2.94787, 'y_coord': 51.669998, 'geometry': 'POINT (2.94787 51.669998)'},
        {'Node_id': 'T18', 'kV_base': 66.0, 'x_coord': 2.902233, 'y_coord': 51.666771, 'geometry': 'POINT (2.902233 51.666771)'},
        {'Node_id': 'T19', 'kV_base': 66.0, 'x_coord': 3.024409, 'y_coord': 51.676416, 'geometry': 'POINT (3.024409 51.676416)'},
        {'Node_id': 'T20', 'kV_base': 66.0, 'x_coord': 2.899931, 'y_coord': 51.680383, 'geometry': 'POINT (2.899931 51.680383)'},
        {'Node_id': 'T21', 'kV_base': 66.0, 'x_coord': 2.877646, 'y_coord': 51.68158, 'geometry': 'POINT (2.877646 51.68158)'},
        {'Node_id': 'T22', 'kV_base': 66.0, 'x_coord': 2.994969, 'y_coord': 51.682673, 'geometry': 'POINT (2.994969 51.682673)'},
        {'Node_id': 'T23', 'kV_base': 66.0, 'x_coord': 2.920427, 'y_coord': 51.683076, 'geometry': 'POINT (2.920427 51.683076)'},
        {'Node_id': 'T24', 'kV_base': 66.0, 'x_coord': 2.944118, 'y_coord': 51.68559, 'geometry': 'POINT (2.944118 51.68559)'},
        {'Node_id': 'T25', 'kV_base': 66.0, 'x_coord': 2.969605, 'y_coord': 51.687657, 'geometry': 'POINT (2.969605 51.687657)'},
        {'Node_id': 'T26', 'kV_base': 66.0, 'x_coord': 2.859919, 'y_coord': 51.692221, 'geometry': 'POINT (2.859919 51.692221)'},
        {'Node_id': 'T27', 'kV_base': 66.0, 'x_coord': 3.028902, 'y_coord': 51.689155, 'geometry': 'POINT (3.028902 51.689155)'},
        {'Node_id': 'T28', 'kV_base': 66.0, 'x_coord': 2.941023, 'y_coord': 51.697938, 'geometry': 'POINT (2.941023 51.697938)'},
        {'Node_id': 'T29', 'kV_base': 66.0, 'x_coord': 2.897664, 'y_coord': 51.697077, 'geometry': 'POINT (2.897664 51.697077)'},
        {'Node_id': 'T30', 'kV_base': 66.0, 'x_coord': 2.920267, 'y_coord': 51.697092, 'geometry': 'POINT (2.920267 51.697092)'},
        {'Node_id': 'T31', 'kV_base': 66.0, 'x_coord': 2.985911, 'y_coord': 51.700867, 'geometry': 'POINT (2.985911 51.700867)'},
        {'Node_id': 'T32', 'kV_base': 66.0, 'x_coord': 2.870323, 'y_coord': 51.703651, 'geometry': 'POINT (2.870323 51.703651)'},
        {'Node_id': 'T33', 'kV_base': 66.0, 'x_coord': 2.840065, 'y_coord': 51.702932, 'geometry': 'POINT (2.840065 51.702932)'},
        {'Node_id': 'T34', 'kV_base': 66.0, 'x_coord': 2.96142, 'y_coord': 51.699809, 'geometry': 'POINT (2.96142 51.699809)'},
        {'Node_id': 'T35', 'kV_base': 66.0, 'x_coord': 3.007886, 'y_coord': 51.694397, 'geometry': 'POINT (3.007886 51.694397)'},
        {'Node_id': 'T36', 'kV_base': 66.0, 'x_coord': 3.010118, 'y_coord': 51.707698, 'geometry': 'POINT (3.010118 51.707698)'},
        {'Node_id': 'T37', 'kV_base': 66.0, 'x_coord': 2.823655, 'y_coord': 51.713217, 'geometry': 'POINT (2.823655 51.713217)'},
        {'Node_id': 'T38', 'kV_base': 66.0, 'x_coord': 2.958572, 'y_coord': 51.711054, 'geometry': 'POINT (2.958572 51.711054)'},
        {'Node_id': 'T39', 'kV_base': 66.0, 'x_coord': 2.938783, 'y_coord': 51.71142, 'geometry': 'POINT (2.938783 51.71142)'},
        {'Node_id': 'T40', 'kV_base': 66.0, 'x_coord': 2.997697, 'y_coord': 51.711581, 'geometry': 'POINT (2.997697 51.711581)'},
        {'Node_id': 'T41', 'kV_base': 66.0, 'x_coord': 2.915604, 'y_coord': 51.711596, 'geometry': 'POINT (2.915604 51.711596)'},
        {'Node_id': 'T42', 'kV_base': 66.0, 'x_coord': 2.882555, 'y_coord': 51.72191, 'geometry': 'POINT (2.882555 51.72191)'},
        {'Node_id': 'T43', 'kV_base': 66.0, 'x_coord': 2.967202, 'y_coord': 51.719691, 'geometry': 'POINT (2.967202 51.719691)'},
        {'Node_id': 'T44', 'kV_base': 66.0, 'x_coord': 2.953799, 'y_coord': 51.723273, 'geometry': 'POINT (2.953799 51.723273)'},
        {'Node_id': 'T45', 'kV_base': 66.0, 'x_coord': 2.832289, 'y_coord': 51.726207, 'geometry': 'POINT (2.832289 51.726207)'},
        {'Node_id': 'T46', 'kV_base': 66.0, 'x_coord': 2.808741, 'y_coord': 51.722059, 'geometry': 'POINT (2.808741 51.722059)'},
        {'Node_id': 'T47', 'kV_base': 66.0, 'x_coord': 2.980445, 'y_coord': 51.716319, 'geometry': 'POINT (2.980445 51.716319)'},
        {'Node_id': 'T48', 'kV_base': 66.0, 'x_coord': 2.852339, 'y_coord': 51.717042, 'geometry': 'POINT (2.852339 51.717042)'},
        {'Node_id': 'T49', 'kV_base': 66.0, 'x_coord': 2.855984, 'y_coord': 51.729624, 'geometry': 'POINT (2.855984 51.729624)'},
        {'Node_id': 'T50', 'kV_base': 66.0, 'x_coord': 2.88688, 'y_coord': 51.734446, 'geometry': 'POINT (2.88688 51.734446)'},
        {'Node_id': 'T51', 'kV_base': 66.0, 'x_coord': 2.790784, 'y_coord': 51.733372, 'geometry': 'POINT (2.790784 51.733372)'},
        {'Node_id': 'T52', 'kV_base': 66.0, 'x_coord': 2.941396, 'y_coord': 51.731212, 'geometry': 'POINT (2.941396 51.731212)'},
        {'Node_id': 'T53', 'kV_base': 66.0, 'x_coord': 2.814668, 'y_coord': 51.738987, 'geometry': 'POINT (2.814668 51.738987)'},
        {'Node_id': 'T54', 'kV_base': 66.0, 'x_coord': 2.774673, 'y_coord': 51.742822, 'geometry': 'POINT (2.774673 51.742822)'},
        {'Node_id': 'T55', 'kV_base': 66.0, 'x_coord': 2.839391, 'y_coord': 51.742907, 'geometry': 'POINT (2.839391 51.742907)'},
        {'Node_id': 'T56', 'kV_base': 66.0, 'x_coord': 2.923457, 'y_coord': 51.740068, 'geometry': 'POINT (2.923457 51.740068)'},
        {'Node_id': 'T57', 'kV_base': 66.0, 'x_coord': 2.903306, 'y_coord': 51.74419, 'geometry': 'POINT (2.903306 51.74419)'},
        {'Node_id': 'T58', 'kV_base': 66.0, 'x_coord': 2.793707, 'y_coord': 51.745827, 'geometry': 'POINT (2.793707 51.745827)'},
        {'Node_id': 'T59', 'kV_base': 66.0, 'x_coord': 2.883644, 'y_coord': 51.748885, 'geometry': 'POINT (2.883644 51.748885)'},
        {'Node_id': 'T60', 'kV_base': 66.0, 'x_coord': 2.832472, 'y_coord': 51.753998, 'geometry': 'POINT (2.832472 51.753998)'},
        {'Node_id': 'T61', 'kV_base': 66.0, 'x_coord': 2.867363, 'y_coord': 51.752713, 'geometry': 'POINT (2.867363 51.752713)'},
        {'Node_id': 'T62', 'kV_base': 66.0, 'x_coord': 2.949325, 'y_coord': 51.749786, 'geometry': 'POINT (2.949325 51.749786)'},
        {'Node_id': 'T63', 'kV_base': 66.0, 'x_coord': 2.814039, 'y_coord': 51.749819, 'geometry': 'POINT (2.814039 51.749819)'},
        {'Node_id': 'T64', 'kV_base': 66.0, 'x_coord': 2.853196, 'y_coord': 51.757803, 'geometry': 'POINT (2.853196 51.757803)'},
        {'Node_id': 'T65', 'kV_base': 66.0, 'x_coord': 2.90934, 'y_coord': 51.760226, 'geometry': 'POINT (2.90934 51.760226)'},
        {'Node_id': 'T66', 'kV_base': 66.0, 'x_coord': 2.932399, 'y_coord': 51.760751, 'geometry': 'POINT (2.932399 51.760751)'},
        {'Node_id': 'T67', 'kV_base': 66.0, 'x_coord': 2.964024, 'y_coord': 51.761786, 'geometry': 'POINT (2.964024 51.761786)'},
        {'Node_id': 'T68', 'kV_base': 66.0, 'x_coord': 2.888408, 'y_coord': 51.765241, 'geometry': 'POINT (2.888408 51.765241)'},
        {'Node_id': 'T69', 'kV_base': 66.0, 'x_coord': 2.904759, 'y_coord': 51.767756, 'geometry': 'POINT (2.904759 51.767756)'},
        {'Node_id': 'T70', 'kV_base': 66.0, 'x_coord': 2.924369, 'y_coord': 51.772109, 'geometry': 'POINT (2.924369 51.772109)'},
        {'Node_id': 'T71', 'kV_base': 66.0, 'x_coord': 2.943299, 'y_coord': 51.776236, 'geometry': 'POINT (2.943299 51.776236)'},
        {'Node_id': 'T72', 'kV_base': 66.0, 'x_coord': 2.960263, 'y_coord': 51.779028, 'geometry': 'POINT (2.960263 51.779028)'},
        {'Node_id': 'T73', 'kV_base': 66.0, 'x_coord': 2.980483, 'y_coord': 51.783041, 'geometry': 'POINT (2.980483 51.783041)'},
        {'Node_id': 'T74', 'kV_base': 66.0, 'x_coord': 2.997089, 'y_coord': 51.786548, 'geometry': 'POINT (2.997089 51.786548)'},
        {'Node_id': 'T75', 'kV_base': 66.0, 'x_coord': 2.912034, 'y_coord': 51.726384, 'geometry': 'POINT (2.912034 51.726384)'},
        {'Node_id': 'T76', 'kV_base': 66.0, 'x_coord': 3.007781, 'y_coord': 51.613971, 'geometry': 'POINT (3.007781 51.613971)'},
        {'Node_id': 'T77', 'kV_base': 66.0, 'x_coord': 3.033326, 'y_coord': 51.70142, 'geometry': 'POINT (3.033326 51.70142)'},
        {'Node_id': 'T78', 'kV_base': 66.0, 'x_coord': 2.893243, 'y_coord': 51.711019, 'geometry': 'POINT (2.893243 51.711019)'},
        {'Node_id': 'T79', 'kV_base': 66.0, 'x_coord': 2.977348, 'y_coord': 51.77225, 'geometry': 'POINT (2.977348 51.77225)'},
        {'Node_id': 'OS1', 'kV_base': 66.0, 'x_coord': 2.964587, 'y_coord': 51.729038, 'geometry': 'POINT (2.964587 51.729038)'}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'Line_id': 'AC529', 'fromNode': 'T60', 'toNode': 'T63','active_config' :0 , 'Length_km': 1.41, 'geometry': 'LINESTRING (2.814039 51.749819, 2.832472 51.753998)'},
        {'Line_id': 'AC530', 'fromNode': 'T60', 'toNode': 'T64','active_config' :0 , 'Length_km': 1.55, 'geometry': 'LINESTRING (2.832472 51.753998, 2.853196 51.757803)'},
        {'Line_id': 'AC531', 'fromNode': 'T61', 'toNode': 'T64','active_config' :0 , 'Length_km': 1.19, 'geometry': 'LINESTRING (2.853196 51.757803, 2.867363 51.752713)'},
        {'Line_id': 'AC532', 'fromNode': 'T59', 'toNode': 'T61','active_config' :1 , 'Length_km': 1.26, 'geometry': 'LINESTRING (2.867363 51.752713, 2.883644 51.748885)'},
        {'Line_id': 'AC533', 'fromNode': 'T57', 'toNode': 'T59','active_config' :3 , 'Length_km': 1.52, 'geometry': 'LINESTRING (2.883644 51.748885, 2.903306 51.74419)'},
        {'Line_id': 'AC534', 'fromNode': 'T56', 'toNode': 'T57','active_config' :5 , 'Length_km': 1.53, 'geometry': 'LINESTRING (2.903306 51.74419, 2.923457 51.740068)'},
        {'Line_id': 'AC535', 'fromNode': 'T56', 'toNode': 'OS1','active_config' :6 , 'Length_km': 3.15, 'geometry': 'LINESTRING (2.964587 51.729038, 2.923457 51.740068)'},
        {'Line_id': 'AC536', 'fromNode': 'T54', 'toNode': 'T58','active_config' :0 , 'Length_km': 1.42, 'geometry': 'LINESTRING (2.774673 51.742822, 2.793707 51.745827)'},
        {'Line_id': 'AC537', 'fromNode': 'T53', 'toNode': 'T58','active_config' :0 , 'Length_km': 1.69, 'geometry': 'LINESTRING (2.793707 51.745827, 2.814668 51.738987)'},
        {'Line_id': 'AC538', 'fromNode': 'T53', 'toNode': 'T55','active_config' :0 , 'Length_km': 1.82, 'geometry': 'LINESTRING (2.814668 51.738987, 2.839391 51.742907)'},
        {'Line_id': 'AC539', 'fromNode': 'T49', 'toNode': 'T55','active_config' :1 , 'Length_km': 1.93, 'geometry': 'LINESTRING (2.839391 51.742907, 2.855984 51.729624)'},
        {'Line_id': 'AC540', 'fromNode': 'T49', 'toNode': 'T50','active_config' :3 , 'Length_km': 2.26, 'geometry': 'LINESTRING (2.855984 51.729624, 2.88688 51.734446)'},
        {'Line_id': 'AC541', 'fromNode': 'T50', 'toNode': 'OS1','active_config' :5 , 'Length_km': 5.68, 'geometry': 'LINESTRING (2.88688 51.734446, 2.922548 51.739092, 2.964587 51.729038)'},
        {'Line_id': 'AC542', 'fromNode': 'T46', 'toNode': 'T51','active_config' :0 , 'Length_km': 1.83, 'geometry': 'LINESTRING (2.790784 51.733372, 2.808741 51.722059)'},
        {'Line_id': 'AC543', 'fromNode': 'T45', 'toNode': 'T46','active_config' :0 , 'Length_km': 1.75, 'geometry': 'LINESTRING (2.808741 51.722059, 2.832289 51.726207)'},
        {'Line_id': 'AC544', 'fromNode': 'T45', 'toNode': 'T48','active_config' :0 , 'Length_km': 1.78, 'geometry': 'LINESTRING (2.832289 51.726207, 2.852339 51.717042)'},
        {'Line_id': 'AC545', 'fromNode': 'T42', 'toNode': 'T48','active_config' :1 , 'Length_km': 2.22, 'geometry': 'LINESTRING (2.852339 51.717042, 2.882555 51.72191)'},
        {'Line_id': 'AC546', 'fromNode': 'T42', 'toNode': 'T78','active_config' :3 , 'Length_km': 1.48, 'geometry': 'LINESTRING (2.882555 51.72191, 2.893243 51.711019)'},
        {'Line_id': 'AC547', 'fromNode': 'T75', 'toNode': 'T78','active_config' :5 , 'Length_km': 2.21, 'geometry': 'LINESTRING (2.893243 51.711019, 2.912034 51.726384)'},
        {'Line_id': 'AC548', 'fromNode': 'T52', 'toNode': 'T75','active_config' :6 , 'Length_km': 2.16, 'geometry': 'LINESTRING (2.912034 51.726384, 2.941396 51.731212)'},
        {'Line_id': 'AC549', 'fromNode': 'T52', 'toNode': 'OS1','active_config' :8   , 'Length_km': 1.68, 'geometry': 'LINESTRING (2.941396 51.731212, 2.964587 51.729038)'},
        {'Line_id': 'AC550', 'fromNode': 'T33', 'toNode': 'T37','active_config' :0   , 'Length_km': 1.67, 'geometry': 'LINESTRING (2.823655 51.713217, 2.840065 51.702932)'},
        {'Line_id': 'AC551', 'fromNode': 'T32', 'toNode': 'T33','active_config' :0   , 'Length_km': 2.16, 'geometry': 'LINESTRING (2.840065 51.702932, 2.870323 51.703651)'},
        {'Line_id': 'AC552', 'fromNode': 'T26', 'toNode': 'T32','active_config' :0   , 'Length_km': 1.53, 'geometry': 'LINESTRING (2.870323 51.703651, 2.859919 51.692221)'},
        {'Line_id': 'AC553', 'fromNode': 'T21', 'toNode': 'T26','active_config' :1   , 'Length_km': 1.76, 'geometry': 'LINESTRING (2.859919 51.692221, 2.877646 51.68158)'},
        {'Line_id': 'AC554', 'fromNode': 'T21', 'toNode': 'T29','active_config' :3   , 'Length_km': 2.27, 'geometry': 'LINESTRING (2.877646 51.68158, 2.897664 51.697077)'},
        {'Line_id': 'AC555', 'fromNode': 'T29', 'toNode': 'T41','active_config' :5   , 'Length_km': 2.1, 'geometry': 'LINESTRING (2.897664 51.697077, 2.915604 51.711596)'},
        {'Line_id': 'AC556', 'fromNode': 'T41', 'toNode': 'OS1','active_config' :6   , 'Length_km': 4.31, 'geometry': 'LINESTRING (2.915604 51.711596, 2.939512 51.728713, 2.964587 51.729038)'},
        {'Line_id': 'AC557', 'fromNode': 'T15', 'toNode': 'T18','active_config' :0   , 'Length_km': 1.53, 'geometry': 'LINESTRING (2.923419 51.668251, 2.902233 51.666771)'},
        {'Line_id': 'AC558', 'fromNode': 'T18', 'toNode': 'T20','active_config' :0   , 'Length_km': 1.58, 'geometry': 'LINESTRING (2.902233 51.666771, 2.899931 51.680383)'},
        {'Line_id': 'AC559', 'fromNode': 'T20', 'toNode': 'T23','active_config' :0   , 'Length_km': 1.5, 'geometry': 'LINESTRING (2.899931 51.680383, 2.920427 51.683076)'},
        {'Line_id': 'AC560', 'fromNode': 'T23', 'toNode': 'T30','active_config' :1   , 'Length_km': 1.62, 'geometry': 'LINESTRING (2.920427 51.683076, 2.920267 51.697092)'},
        {'Line_id': 'AC561', 'fromNode': 'T30', 'toNode': 'T39','active_config' :3   , 'Length_km': 2.1, 'geometry': 'LINESTRING (2.920267 51.697092, 2.938783 51.71142)'},
        {'Line_id': 'AC562', 'fromNode': 'T39', 'toNode': 'T44','active_config' :5   , 'Length_km': 1.74, 'geometry': 'LINESTRING (2.938783 51.71142, 2.953799 51.723273)'},
        {'Line_id': 'AC563', 'fromNode': 'T44', 'toNode': 'OS1','active_config' :6   , 'Length_km': 1.04, 'geometry': 'LINESTRING (2.953799 51.723273, 2.964587 51.729038)'},
        {'Line_id': 'AC564', 'fromNode': 'T25', 'toNode': 'OS1','active_config' :5   , 'Length_km': 5.51, 'geometry': 'LINESTRING (2.964587 51.729038, 2.965216 51.712033, 2.983959 51.699837, 2.969605 51.687657)'},
        {'Line_id': 'AC565', 'fromNode': 'T16', 'toNode': 'T25','active_config' :3   , 'Length_km': 2.11, 'geometry': 'LINESTRING (2.969605 51.687657, 2.977256 51.669803)'},
        {'Line_id': 'AC566', 'fromNode': 'T10', 'toNode': 'T16','active_config' :1   , 'Length_km': 2.02, 'geometry': 'LINESTRING (2.977256 51.669803, 2.992081 51.654673)'},
        {'Line_id': 'AC567', 'fromNode': 'T5', 'toNode': 'T10','active_config' : 0  , 'Length_km': 2.43, 'geometry': 'LINESTRING (2.992081 51.654673, 2.988121 51.633521)'},
        {'Line_id': 'AC568', 'fromNode': 'T4', 'toNode': 'T5','active_config' :  0 , 'Length_km': 1.71, 'geometry': 'LINESTRING (2.988121 51.633521, 2.966396 51.627465)'},
        {'Line_id': 'AC569', 'fromNode': 'T6', 'toNode': 'T9','active_config' :  0 , 'Length_km': 2.04, 'geometry': 'LINESTRING (2.925951 51.651387, 2.947505 51.639599)'},
        {'Line_id': 'AC570', 'fromNode': 'T6', 'toNode': 'T12','active_config' :  0 , 'Length_km': 1.63, 'geometry': 'LINESTRING (2.947505 51.639599, 2.968419 51.645259)'},
        {'Line_id': 'AC571', 'fromNode': 'T11', 'toNode': 'T12','active_config' : 0  , 'Length_km': 1.54, 'geometry': 'LINESTRING (2.968419 51.645259, 2.954194 51.655288)'},
        {'Line_id': 'AC572', 'fromNode': 'T11', 'toNode': 'T17','active_config' : 1  , 'Length_km': 1.76, 'geometry': 'LINESTRING (2.954194 51.655288, 2.94787 51.669998)'},
        {'Line_id': 'AC573', 'fromNode': 'T17', 'toNode': 'T24','active_config' : 3  , 'Length_km': 1.82, 'geometry': 'LINESTRING (2.94787 51.669998, 2.944118 51.68559)'},
        {'Line_id': 'AC574', 'fromNode': 'T24', 'toNode': 'T28','active_config' : 5  , 'Length_km': 1.45, 'geometry': 'LINESTRING (2.944118 51.68559, 2.941023 51.697938)'},
        {'Line_id': 'AC575', 'fromNode': 'T34', 'toNode': 'T38','active_config' : 0  , 'Length_km': 1.33, 'geometry': 'LINESTRING (2.96142 51.699809, 2.958572 51.711054)'},
        {'Line_id': 'AC576', 'fromNode': 'T38', 'toNode': 'OS1','active_config' : 0  , 'Length_km': 2.11, 'geometry': 'LINESTRING (2.964587 51.729038, 2.958572 51.711054)'},
        {'Line_id': 'AC577', 'fromNode': 'T2', 'toNode': 'T4','active_config' :  0 , 'Length_km': 2.05, 'geometry': 'LINESTRING (2.987324 51.615206, 2.966396 51.627465)'},
        {'Line_id': 'AC578', 'fromNode': 'T1', 'toNode': 'T76','active_config' :  0 , 'Length_km': 1.34, 'geometry': 'LINESTRING (3.007097 51.602446, 3.007781 51.613971)'},
        {'Line_id': 'AC579', 'fromNode': 'T3', 'toNode': 'T76','active_config' :  0 , 'Length_km': 1.36, 'geometry': 'LINESTRING (3.007781 51.613971, 3.009493 51.62557)'},
        {'Line_id': 'AC580', 'fromNode': 'T3', 'toNode': 'T7','active_config' :  0 , 'Length_km': 1.51, 'geometry': 'LINESTRING (3.009493 51.62557, 3.014262 51.638311)'},
        {'Line_id': 'AC581', 'fromNode': 'T7', 'toNode': 'T14','active_config' :  1 , 'Length_km': 3.52, 'geometry': 'LINESTRING (3.014262 51.638311, 3.003126 51.668719)'},
        {'Line_id': 'AC582', 'fromNode': 'T14', 'toNode': 'T22','active_config' : 3  , 'Length_km': 1.69, 'geometry': 'LINESTRING (3.003126 51.668719, 2.994969 51.682673)'},
        {'Line_id': 'AC583', 'fromNode': 'T22', 'toNode': 'T31','active_config' :  5 , 'Length_km': 2.17, 'geometry': 'LINESTRING (2.994969 51.682673, 2.985911 51.700867)'},
        {'Line_id': 'AC584', 'fromNode': 'T31', 'toNode': 'OS1','active_config' :  6 , 'Length_km': 3.82, 'geometry': 'LINESTRING (2.985911 51.700867, 2.965741 51.712132, 2.964587 51.729038)'},
        {'Line_id': 'AC585', 'fromNode': 'T43', 'toNode': 'OS1','active_config' :  8 , 'Length_km': 1.12, 'geometry': 'LINESTRING (2.964587 51.729038, 2.967202 51.719691)'},
        {'Line_id': 'AC586', 'fromNode': 'T43', 'toNode': 'T47','active_config' :  6 , 'Length_km': 1.05, 'geometry': 'LINESTRING (2.967202 51.719691, 2.980445 51.716319)'},
        {'Line_id': 'AC587', 'fromNode': 'T35', 'toNode': 'T47','active_config' :  5 , 'Length_km': 3.64, 'geometry': 'LINESTRING (2.980445 51.716319, 2.977416 51.708082, 2.987771 51.700895, 3.007886 51.694397)'},
        {'Line_id': 'AC588', 'fromNode': 'T35', 'toNode': 'T77','active_config' :  3 , 'Length_km': 1.98, 'geometry': 'LINESTRING (3.007886 51.694397, 3.033326 51.70142)'},
        {'Line_id': 'AC589', 'fromNode': 'T27', 'toNode': 'T77','active_config' :  1 , 'Length_km': 1.45, 'geometry': 'LINESTRING (3.033326 51.70142, 3.028902 51.689155)'},
        {'Line_id': 'AC590', 'fromNode': 'T19', 'toNode': 'T27','active_config' :  0 , 'Length_km': 1.5, 'geometry': 'LINESTRING (3.028902 51.689155, 3.024409 51.676416)'},
        {'Line_id': 'AC591', 'fromNode': 'T13', 'toNode': 'T19','active_config' :  0 , 'Length_km': 1.62, 'geometry': 'LINESTRING (3.024409 51.676416, 3.021282 51.662531)'},
        {'Line_id': 'AC592', 'fromNode': 'T8', 'toNode': 'T13','active_config' :   0, 'Length_km': 1.5, 'geometry': 'LINESTRING (3.021282 51.662531, 3.01723 51.649834)'},
        {'Line_id': 'AC593', 'fromNode': 'T36', 'toNode': 'T40','active_config' :  0 , 'Length_km': 1.02, 'geometry': 'LINESTRING (3.010118 51.707698, 2.997697 51.711581)'},
        {'Line_id': 'AC594', 'fromNode': 'T40', 'toNode': 'OS1','active_config' :  0 , 'Length_km': 3.33, 'geometry': 'LINESTRING (2.997697 51.711581, 2.968203 51.720244, 2.964587 51.729038)'},
        {'Line_id': 'AC595', 'fromNode': 'T68', 'toNode': 'T69','active_config' :  0 , 'Length_km': 1.23, 'geometry': 'LINESTRING (2.888408 51.765241, 2.904759 51.767756)'},
        {'Line_id': 'AC596', 'fromNode': 'T65', 'toNode': 'T69','active_config' :  0 , 'Length_km': 0.96, 'geometry': 'LINESTRING (2.904759 51.767756, 2.90934 51.760226)'},
        {'Line_id': 'AC597', 'fromNode': 'T65', 'toNode': 'T66','active_config' :  0 , 'Length_km': 1.65, 'geometry': 'LINESTRING (2.90934 51.760226, 2.932399 51.760751)'},
        {'Line_id': 'AC598', 'fromNode': 'T62', 'toNode': 'T66','active_config' :  1 , 'Length_km': 1.75, 'geometry': 'LINESTRING (2.932399 51.760751, 2.949325 51.749786)'},
        {'Line_id': 'AC599', 'fromNode': 'T67', 'toNode': 'T79','active_config' :  5 , 'Length_km': 1.55, 'geometry': 'LINESTRING (2.964024 51.761786, 2.977348 51.77225)'},
        {'Line_id': 'AC600', 'fromNode': 'T74', 'toNode': 'T79','active_config' :  3 , 'Length_km': 2.16, 'geometry': 'LINESTRING (2.977348 51.77225, 2.997089 51.786548)'},
        {'Line_id': 'AC601', 'fromNode': 'T73', 'toNode': 'T74','active_config' :  1 , 'Length_km': 1.27, 'geometry': 'LINESTRING (2.997089 51.786548, 2.980483 51.783041)'},
        {'Line_id': 'AC602', 'fromNode': 'T72', 'toNode': 'T73','active_config' :  0 , 'Length_km': 1.52, 'geometry': 'LINESTRING (2.980483 51.783041, 2.960263 51.779028)'},
        {'Line_id': 'AC603', 'fromNode': 'T71', 'toNode': 'T72','active_config' :  0 , 'Length_km': 1.27, 'geometry': 'LINESTRING (2.960263 51.779028, 2.943299 51.776236)'},
        {'Line_id': 'AC604', 'fromNode': 'T70', 'toNode': 'T71','active_config' :  0 , 'Length_km': 1.45, 'geometry': 'LINESTRING (2.943299 51.776236, 2.924369 51.772109)'},
        {'Line_id': 'AC605', 'fromNode': 'T67', 'toNode': 'OS1','active_config' : 6  , 'Length_km': 4.56, 'geometry': 'LINESTRING (2.964024 51.761786, 2.951258 51.750284, 2.968983 51.740439, 2.964587 51.729038)'},
        {'Line_id': 'AC606', 'fromNode': 'T62', 'toNode': 'OS1','active_config' :  3 , 'Length_km': 2.92, 'geometry': 'LINESTRING (2.949325 51.749786, 2.966737 51.740109, 2.964587 51.729038)'},
        {'Line_id': 'AC607', 'fromNode': 'T28', 'toNode': 'OS1','active_config' :  6 , 'Length_km': 3.89, 'geometry': 'LINESTRING (2.964587 51.729038, 2.941023 51.697938)'}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC = None

    lines_DC = None

    Converters_ACDC = None

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, data_in='pu')
    grid.name = 'Borssele_3&4'
    
    

    # Add Renewable Sources
    pyf.add_RenSource(grid, 'T1', Turbine, ren_source_name='T1', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T2', Turbine, ren_source_name='T2', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T3', Turbine, ren_source_name='T3', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T4', Turbine, ren_source_name='T4', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T5', Turbine, ren_source_name='T5', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T6', Turbine, ren_source_name='T6', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T7', Turbine, ren_source_name='T7', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T8', Turbine, ren_source_name='T8', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T9', Turbine, ren_source_name='T9', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T10', Turbine, ren_source_name='T10', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T11', Turbine, ren_source_name='T11', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T12', Turbine, ren_source_name='T12', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T13', Turbine, ren_source_name='T13', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T14', Turbine, ren_source_name='T14', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T15', Turbine, ren_source_name='T15', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T16', Turbine, ren_source_name='T16', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T17', Turbine, ren_source_name='T17', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T18', Turbine, ren_source_name='T18', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T19', Turbine, ren_source_name='T19', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T20', Turbine, ren_source_name='T20', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T21', Turbine, ren_source_name='T21', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T22', Turbine, ren_source_name='T22', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T23', Turbine, ren_source_name='T23', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T24', Turbine, ren_source_name='T24', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T25', Turbine, ren_source_name='T25', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T26', Turbine, ren_source_name='T26', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T27', Turbine, ren_source_name='T27', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T28', Turbine, ren_source_name='T28', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T29', Turbine, ren_source_name='T29', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T30', Turbine, ren_source_name='T30', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T31', Turbine, ren_source_name='T31', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T32', Turbine, ren_source_name='T32', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T33', Turbine, ren_source_name='T33', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T34', Turbine, ren_source_name='T34', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T35', Turbine, ren_source_name='T35', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T36', Turbine, ren_source_name='T36', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T37', Turbine, ren_source_name='T37', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T38', Turbine, ren_source_name='T38', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T39', Turbine, ren_source_name='T39', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T40', Turbine, ren_source_name='T40', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T41', Turbine, ren_source_name='T41', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T42', Turbine, ren_source_name='T42', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T43', Turbine, ren_source_name='T43', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T44', Turbine, ren_source_name='T44', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T45', Turbine, ren_source_name='T45', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T46', Turbine, ren_source_name='T46', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T47', Turbine, ren_source_name='T47', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T48', Turbine, ren_source_name='T48', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T49', Turbine, ren_source_name='T49', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T50', Turbine, ren_source_name='T50', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T51', Turbine, ren_source_name='T51', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T52', Turbine, ren_source_name='T52', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T53', Turbine, ren_source_name='T53', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T54', Turbine, ren_source_name='T54', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T55', Turbine, ren_source_name='T55', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T56', Turbine, ren_source_name='T56', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T57', Turbine, ren_source_name='T57', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T58', Turbine, ren_source_name='T58', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T59', Turbine, ren_source_name='T59', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T60', Turbine, ren_source_name='T60', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T61', Turbine, ren_source_name='T61', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T62', Turbine, ren_source_name='T62', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T63', Turbine, ren_source_name='T63', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T64', Turbine, ren_source_name='T64', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T65', Turbine, ren_source_name='T65', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T66', Turbine, ren_source_name='T66', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T67', Turbine, ren_source_name='T67', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T68', Turbine, ren_source_name='T68', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T69', Turbine, ren_source_name='T69', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T70', Turbine, ren_source_name='T70', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T71', Turbine, ren_source_name='T71', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T72', Turbine, ren_source_name='T72', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T73', Turbine, ren_source_name='T73', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T74', Turbine, ren_source_name='T74', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T75', Turbine, ren_source_name='T75', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T76', Turbine, ren_source_name='T76', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T77', Turbine, ren_source_name='T77', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T78', Turbine, ren_source_name='T78', min_gamma=gamma_limit,Qrel=0.3)
    pyf.add_RenSource(grid, 'T79', Turbine, ren_source_name='T79', min_gamma=gamma_limit,Qrel=0.3)


    candidate_cables = ['ABB_XLPE_Cu_66kV_sub_95mm2',
                        'ABB_XLPE_Cu_66kV_sub_120mm2',
                        'ABB_XLPE_Cu_66kV_sub_150mm2',
                        'ABB_XLPE_Cu_66kV_sub_185mm2',
                        'ABB_XLPE_Cu_66kV_sub_240mm2',
                        'ABB_XLPE_Cu_66kV_sub_300mm2',
                        'ABB_XLPE_Cu_66kV_sub_400mm2',
                        'ABB_XLPE_Cu_66kV_sub_500mm2',
                        'ABB_XLPE_Cu_66kV_sub_630mm2',
                        'ABB_XLPE_Cu_66kV_sub_800mm2',
                        'ABB_XLPE_Cu_66kV_sub_1000mm2']

    cable_option = pyf.add_cable_option(grid,candidate_cables,'PEI')

    for link in lines_AC_data:
        pyf.add_line_sizing(grid,link['fromNode'],link['toNode'],cable_option=cable_option.name,active_config=link['active_config'],Length_km=link['Length_km'],name=link['Line_id'],update_grid=False,geometry=link['geometry'])

    pyf.add_extgrid(grid, 'OS1',lf=LCoE)

    grid.cab_types_allowed = Nc

    grid.create_Ybus_AC()
    grid.Update_Graph_AC()
    
    # Return the grid
    return grid,res
