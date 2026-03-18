

import pyflow_acdc as pyf
import pandas as pd
"""
Converted to PyFlowACDC format from

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%                                                                  			 	  %%%%%
%%%%    IEEE PES Power Grid Library - Optimal Power Flow with HVDC Lines - v23.09     %%%%%
%%%%          (https://github.com/power-grid-lib/pglib-opf-hvdc)      				  %%%%%
%%%%               Benchmark Group - Typical Operations               				  %%%%%
%%%%                         23 - August - 2023                       				  %%%%%
%%%%                                                                  				  %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   AC/DC grid OPF test case based on:
%   Sass, F., Sennewald, T., Marten, A.-K. and Westermann, D. (2017), 
%   Mixed AC high-voltage direct current benchmark test system for security constrained optimal power flow calculation. 
%   IET Gener. Transm. Distrib., 11: 447-455. https://doi.org/10.1049/iet-gtd.2016.0993
%
%   Copyright (c) 2023 by Hakan Ergun, Vaishally Bhardwaj ({hakan.ergun, vaishally.bhardwaj}@kuleuven.be)
%   Licensed under the Creative Commons Attribution 4.0
%   International license, http://creativecommons.org/licenses/by/4.0/
%
"""

def pglib_opf_hvdc_case67():    
    
    S_base=100
    
    # DataFrame Code:
    nodes_AC_data = [
        {'type': 'Slack', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '1.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '2.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '3.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '4.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0526, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '5.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.91, 'Reactive_load': 0.76, 'Node_id': '6.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '7.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.87, 'Reactive_load': 0.73, 'Node_id': '8.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.86, 'Reactive_load': 0.74, 'Node_id': '9.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '10.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.71, 'Reactive_load': 0.55, 'Node_id': '11.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.71, 'Reactive_load': 0.87, 'Node_id': '12.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '13.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.99, 'Reactive_load': 0.6, 'Node_id': '14.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.13, 'Reactive_load': 0.525, 'Node_id': '15.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.38, 'Reactive_load': 0.07, 'Node_id': '16.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.75, 'Reactive_load': 1.06, 'Node_id': '17.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '18.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.65, 'Reactive_load': 0.46, 'Node_id': '19.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.78, 'Reactive_load': 0.825, 'Node_id': '20.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '21.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.3, 'Reactive_load': 0.07, 'Node_id': '22.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '23.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.32, 'Reactive_load': 0.07, 'Node_id': '24.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '25.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.95, 'Reactive_load': 0.89, 'Node_id': '26.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '27.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 6.65, 'Reactive_load': 0.99, 'Node_id': '28.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '29.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 2.66, 'Reactive_load': 1.0, 'Node_id': '30.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 8.45, 'Reactive_load': 1.19, 'Node_id': '31.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.32, 'Reactive_load': 1.37, 'Node_id': '32.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '33.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 5.4, 'Reactive_load': 1.58, 'Node_id': '34.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.6, 'Reactive_load': 0.97, 'Node_id': '35.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '36.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.51, 'Reactive_load': 1.9, 'Node_id': '37.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.5, 'Reactive_load': 0.0, 'Node_id': '38.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 6.29, 'Reactive_load': 0.87, 'Node_id': '39.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '40.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '41.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 8.59, 'Reactive_load': 1.8, 'Node_id': '42.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '43.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.74, 'Reactive_load': 0.92, 'Node_id': '44.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 6.68, 'Reactive_load': 1.09, 'Node_id': '45.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 6.14, 'Reactive_load': 0.95, 'Node_id': '46.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.81, 'Reactive_load': 0.0, 'Node_id': '47.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '48.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '49.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '50.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 4.3, 'Reactive_load': 1.23, 'Node_id': '51.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.09, 'Reactive_load': 1.02, 'Node_id': '52.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.0, 'Reactive_load': 0.3, 'Node_id': '53.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '54.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.03, 'Reactive_load': 1.1, 'Node_id': '55.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '56.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '57.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.24, 'Reactive_load': 1.57, 'Node_id': '58.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '59.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.15, 'Reactive_load': 0.42, 'Node_id': '60.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 1.87, 'Reactive_load': 0.75, 'Node_id': '61.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.19, 'Reactive_load': 0.95, 'Node_id': '62.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '63.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '64.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PQ', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 3.15, 'Reactive_load': 0.97, 'Node_id': '65.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'PV', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '66.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Slack', 'Voltage_0': 1.0, 'theta_0': 0.0, 'kV_base': 380.0, 'Power_Gained': 0, 'Reactive_Gained': 0, 'Power_load': 0.0, 'Reactive_load': 0.0, 'Node_id': '67.0', 'Umin': 0.9, 'Umax': 1.1, 'Gs': 0.0, 'Bs': 0.0, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_AC = pd.DataFrame(nodes_AC_data)

    lines_AC_data = [
        {'fromNode': '1.0', 'toNode': '5.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '1'},
        {'fromNode': '1.0', 'toNode': '7.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '2'},
        {'fromNode': '1.0', 'toNode': '8.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '3'},
        {'fromNode': '1.0', 'toNode': '14.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '4'},
        {'fromNode': '2.0', 'toNode': '3.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '5'},
        {'fromNode': '2.0', 'toNode': '9.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '6'},
        {'fromNode': '2.0', 'toNode': '12.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '7'},
        {'fromNode': '3.0', 'toNode': '4.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '8'},
        {'fromNode': '3.0', 'toNode': '10.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '9'},
        {'fromNode': '3.0', 'toNode': '12.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '10'},
        {'fromNode': '3.0', 'toNode': '9.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '11'},
        {'fromNode': '4.0', 'toNode': '14.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '12'},
        {'fromNode': '4.0', 'toNode': '19.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '13'},
        {'fromNode': '5.0', 'toNode': '6.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '14'},
        {'fromNode': '5.0', 'toNode': '7.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '15'},
        {'fromNode': '5.0', 'toNode': '8.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '16'},
        {'fromNode': '6.0', 'toNode': '7.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '17'},
        {'fromNode': '7.0', 'toNode': '15.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '18'},
        {'fromNode': '7.0', 'toNode': '16.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '19'},
        {'fromNode': '8.0', 'toNode': '9.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '20'},
        {'fromNode': '10.0', 'toNode': '11.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '21'},
        {'fromNode': '10.0', 'toNode': '22.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '22'},
        {'fromNode': '11.0', 'toNode': '12.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '23'},
        {'fromNode': '11.0', 'toNode': '13.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '24'},
        {'fromNode': '12.0', 'toNode': '13.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '25'},
        {'fromNode': '13.0', 'toNode': '53.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '26'},
        {'fromNode': '14.0', 'toNode': '15.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '27'},
        {'fromNode': '14.0', 'toNode': '18.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '28'},
        {'fromNode': '16.0', 'toNode': '17.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '29'},
        {'fromNode': '16.0', 'toNode': '18.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '30'},
        {'fromNode': '17.0', 'toNode': '24.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '31'},
        {'fromNode': '18.0', 'toNode': '24.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '32'},
        {'fromNode': '19.0', 'toNode': '20.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '33'},
        {'fromNode': '19.0', 'toNode': '23.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '34'},
        {'fromNode': '20.0', 'toNode': '21.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '35'},
        {'fromNode': '21.0', 'toNode': '25.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '36'},
        {'fromNode': '21.0', 'toNode': '22.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '37'},
        {'fromNode': '21.0', 'toNode': '23.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '38'},
        {'fromNode': '22.0', 'toNode': '25.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '39'},
        {'fromNode': '18.0', 'toNode': '20.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '40'},
        {'fromNode': '24.0', 'toNode': '49.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '41'},
        {'fromNode': '25.0', 'toNode': '43.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '42'},
        {'fromNode': '26.0', 'toNode': '27.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '43'},
        {'fromNode': '26.0', 'toNode': '31.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '44'},
        {'fromNode': '26.0', 'toNode': '40.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '45'},
        {'fromNode': '27.0', 'toNode': '28.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '46'},
        {'fromNode': '28.0', 'toNode': '35.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '47'},
        {'fromNode': '28.0', 'toNode': '37.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '48'},
        {'fromNode': '29.0', 'toNode': '39.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '49'},
        {'fromNode': '29.0', 'toNode': '44.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '50'},
        {'fromNode': '30.0', 'toNode': '31.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '51'},
        {'fromNode': '31.0', 'toNode': '27.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '52'},
        {'fromNode': '30.0', 'toNode': '26.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '53'},
        {'fromNode': '32.0', 'toNode': '40.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '54'},
        {'fromNode': '41.0', 'toNode': '40.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '55'},
        {'fromNode': '43.0', 'toNode': '44.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '56'},
        {'fromNode': '33.0', 'toNode': '51.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '57'},
        {'fromNode': '33.0', 'toNode': '34.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '58'},
        {'fromNode': '34.0', 'toNode': '51.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '59'},
        {'fromNode': '35.0', 'toNode': '33.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '60'},
        {'fromNode': '35.0', 'toNode': '36.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '61'},
        {'fromNode': '35.0', 'toNode': '47.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '62'},
        {'fromNode': '29.0', 'toNode': '35.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '63'},
        {'fromNode': '36.0', 'toNode': '37.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '64'},
        {'fromNode': '36.0', 'toNode': '38.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '65'},
        {'fromNode': '37.0', 'toNode': '38.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '66'},
        {'fromNode': '39.0', 'toNode': '40.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '67'},
        {'fromNode': '39.0', 'toNode': '43.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '68'},
        {'fromNode': '41.0', 'toNode': '42.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '69'},
        {'fromNode': '42.0', 'toNode': '43.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '70'},
        {'fromNode': '42.0', 'toNode': '49.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '71'},
        {'fromNode': '43.0', 'toNode': '49.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '72'},
        {'fromNode': '44.0', 'toNode': '45.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '73'},
        {'fromNode': '44.0', 'toNode': '48.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '74'},
        {'fromNode': '45.0', 'toNode': '46.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '75'},
        {'fromNode': '45.0', 'toNode': '50.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '76'},
        {'fromNode': '47.0', 'toNode': '48.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '77'},
        {'fromNode': '46.0', 'toNode': '48.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '78'},
        {'fromNode': '47.0', 'toNode': '50.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '79'},
        {'fromNode': '47.0', 'toNode': '51.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '80'},
        {'fromNode': '47.0', 'toNode': '59.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '81'},
        {'fromNode': '52.0', 'toNode': '53.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '82'},
        {'fromNode': '52.0', 'toNode': '54.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '83'},
        {'fromNode': '63.0', 'toNode': '55.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '84'},
        {'fromNode': '22.0', 'toNode': '56.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '85'},
        {'fromNode': '54.0', 'toNode': '65.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '86'},
        {'fromNode': '55.0', 'toNode': '57.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '87'},
        {'fromNode': '58.0', 'toNode': '61.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '88'},
        {'fromNode': '56.0', 'toNode': '59.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '89'},
        {'fromNode': '57.0', 'toNode': '58.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '90'},
        {'fromNode': '56.0', 'toNode': '58.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '91'},
        {'fromNode': '58.0', 'toNode': '60.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '92'},
        {'fromNode': '62.0', 'toNode': '66.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '93'},
        {'fromNode': '61.0', 'toNode': '62.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '94'},
        {'fromNode': '52.0', 'toNode': '64.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '95'},
        {'fromNode': '62.0', 'toNode': '63.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '96'},
        {'fromNode': '59.0', 'toNode': '60.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '97'},
        {'fromNode': '63.0', 'toNode': '57.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '98'},
        {'fromNode': '65.0', 'toNode': '66.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '99'},
        {'fromNode': '66.0', 'toNode': '54.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '100'},
        {'fromNode': '66.0', 'toNode': '64.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '101'},
        {'fromNode': '30.0', 'toNode': '32.0', 'r': 0.00207756, 'x': 0.01800554, 'g': 0, 'b': 0.61242207, 'MVA_rating': 900.0, 'kV_base': 380.0, 'm': 1, 'shift': 0, 'Line_id': '102'}
    ]
    lines_AC = pd.DataFrame(lines_AC_data)

    nodes_DC_data = [
        {'type': 'Slack', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '1.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '2.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '3.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '4.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '5.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '6.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '7.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'Droop', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '8.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None},
        {'type': 'P', 'Voltage_0': 1.0, 'Power_Gained': 0, 'Power_load': 0.0, 'kV_base': 500.0, 'Node_id': '9.0', 'Umin': 0.9, 'Umax': 1.1, 'x_coord': None, 'y_coord': None, 'PZ': None}
    ]
    nodes_DC = pd.DataFrame(nodes_DC_data)

    lines_DC_data = [
        {'fromNode': '1.0', 'toNode': '2.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '1'},
        {'fromNode': '3.0', 'toNode': '4.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '2'},
        {'fromNode': '4.0', 'toNode': '5.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '3'},
        {'fromNode': '6.0', 'toNode': '7.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '4'},
        {'fromNode': '1.0', 'toNode': '3.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '5'},
        {'fromNode': '2.0', 'toNode': '8.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '6'},
        {'fromNode': '8.0', 'toNode': '5.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '7'},
        {'fromNode': '4.0', 'toNode': '6.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '8'},
        {'fromNode': '2.0', 'toNode': '4.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '9'},
        {'fromNode': '5.0', 'toNode': '7.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '10'},
        {'fromNode': '3.0', 'toNode': '9.0', 'r': 0.0012, 'MW_rating': 1575.0, 'kV_base': 500.0, 'Length_km': 1, 'Mono_Bi_polar': 'b', 'Line_id': '11'}
    ]
    lines_DC = pd.DataFrame(lines_DC_data)

    Converters_ACDC_data = [
        {'AC_type': 'PQ', 'DC_type': 'Slack', 'AC_node': '7.0', 'DC_node': '1.0', 'P_AC': -5.775, 'Q_AC': 0.0, 'P_DC': -4.659871, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '1', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '40.0', 'DC_node': '2.0', 'P_AC': 10.0, 'Q_AC': 0.0, 'P_DC': 5.0, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '2', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '3.0', 'DC_node': '3.0', 'P_AC': -5.5, 'Q_AC': 0.0, 'P_DC': -5.171051, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '3', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '23.0', 'DC_node': '4.0', 'P_AC': -6.0, 'Q_AC': 0.0, 'P_DC': -5.608855, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '4', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '48.0', 'DC_node': '5.0', 'P_AC': 10.0, 'Q_AC': 0.0, 'P_DC': 11.038969999999999, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '5', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '54.0', 'DC_node': '6.0', 'P_AC': 0.5, 'Q_AC': 0.0, 'P_DC': 0.5131034, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '6', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '57.0', 'DC_node': '7.0', 'P_AC': -5.5, 'Q_AC': 0.0, 'P_DC': -5.1646220000000005, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '7', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PQ', 'DC_type': 'Droop', 'AC_node': '27.0', 'DC_node': '8.0', 'P_AC': 10.0, 'Q_AC': 0.0, 'P_DC': 11.11644, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 2000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '8', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1},
        {'AC_type': 'PV', 'DC_type': 'P', 'AC_node': '67.0', 'DC_node': '9.0', 'P_AC': -8.0, 'Q_AC': 0.0, 'P_DC': -7.313881, 'T_r': 0.01, 'T_x': 0.01, 'PR_r': 0.01, 'PR_x': 0.01, 'Filter_b': 0.01, 'Droop': 0.005, 'AC_kV_base': 500.0, 'MVA_rating': 1000.0, 'Nconverter': 1, 'pol': 1, 'Conv_id': '9', 'lossa': 1.103, 'lossb': 0.887, 'losscrect': 2.885, 'losscinv': 2.885, 'Ucmin': 0.9, 'Ucmax': 1.1}
    ]
    Converters_ACDC = pd.DataFrame(Converters_ACDC_data)

    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in = 'pu')
    grid.name = 'IEEE 67-bus System HVDC'
    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    
    for index, row in nodes_DC.iterrows():
        node_name = nodes_DC.at[index, 'Node_id']
        price_zone = nodes_DC.at[index, 'PZ']
        ACDC = 'DC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    
    # Add Generators
    pyf.add_gen(grid, '1.0', '1', price_zone_link=False, lf=10, qf=0, MWmax=1000.0, MWmin=0.0, MVArmax=1000.0, MVArmin=-500.0, PsetMW=700.0, QsetMVA=23.0)
    pyf.add_gen(grid, '2.0', '2', price_zone_link=False, lf=10, qf=0, MWmax=1500.0, MWmin=0.0, MVArmax=0.0, MVArmin=0.0, PsetMW=1500.0, QsetMVA=100.0)
    pyf.add_gen(grid, '4.0', '3', price_zone_link=False, lf=10, qf=0, MWmax=560.0, MWmin=0.0, MVArmax=350.0, MVArmin=-350.0, PsetMW=523.0, QsetMVA=140.0)
    pyf.add_gen(grid, '5.0', '4', price_zone_link=False, lf=10, qf=0, MWmax=1200.0, MWmin=0.0, MVArmax=0.0, MVArmin=0.0, PsetMW=1200.0, QsetMVA=100.0)
    pyf.add_gen(grid, '10.0', '5', price_zone_link=False, lf=10, qf=0, MWmax=560.0, MWmin=0.0, MVArmax=350.0, MVArmin=-350.0, PsetMW=436.00000000000006, QsetMVA=105.0)
    pyf.add_gen(grid, '13.0', '6', price_zone_link=False, lf=10, qf=0, MWmax=630.0, MWmin=0.0, MVArmax=300.0, MVArmin=-300.0, PsetMW=541.0, QsetMVA=117.0)
    pyf.add_gen(grid, '18.0', '7', price_zone_link=False, lf=10, qf=0, MWmax=720.0, MWmin=0.0, MVArmax=400.0, MVArmin=-400.0, PsetMW=681.0, QsetMVA=-35.0)
    pyf.add_gen(grid, '25.0', '8', price_zone_link=False, lf=10, qf=0, MWmax=560.0, MWmin=0.0, MVArmax=250.0, MVArmin=-250.0, PsetMW=469.00000000000006, QsetMVA=59.0)
    pyf.add_gen(grid, '29.0', '9', price_zone_link=False, lf=10, qf=0, MWmax=630.0, MWmin=0.0, MVArmax=350.0, MVArmin=-350.0, PsetMW=500.0, QsetMVA=101.0)
    pyf.add_gen(grid, '33.0', '10', price_zone_link=False, lf=10, qf=0, MWmax=850.0, MWmin=0.0, MVArmax=500.0, MVArmin=-500.0, PsetMW=496.0, QsetMVA=306.0)
    pyf.add_gen(grid, '36.0', '11', price_zone_link=False, lf=10, qf=0, MWmax=720.0, MWmin=0.0, MVArmax=400.0, MVArmin=-400.0, PsetMW=512.0, QsetMVA=249.00000000000003)
    pyf.add_gen(grid, '41.0', '12', price_zone_link=False, lf=10, qf=0, MWmax=850.0, MWmin=0.0, MVArmax=450.0, MVArmin=-450.0, PsetMW=350.0, QsetMVA=238.0)
    pyf.add_gen(grid, '43.0', '13', price_zone_link=False, lf=10, qf=0, MWmax=720.0, MWmin=0.0, MVArmax=500.0, MVArmin=-250.0, PsetMW=574.0, QsetMVA=223.0)
    pyf.add_gen(grid, '50.0', '14', price_zone_link=False, lf=10, qf=0, MWmax=720.0, MWmin=0.0, MVArmax=400.0, MVArmin=-400.0, PsetMW=581.0, QsetMVA=150.0)
    pyf.add_gen(grid, '56.0', '15', price_zone_link=False, lf=10, qf=0, MWmax=560.0, MWmin=0.0, MVArmax=250.0, MVArmin=-250.0, PsetMW=496.0, QsetMVA=56.00000000000001)
    pyf.add_gen(grid, '59.0', '16', price_zone_link=False, lf=10, qf=0, MWmax=720.0, MWmin=0.0, MVArmax=350.0, MVArmin=-350.0, PsetMW=430.99999999999994, QsetMVA=206.0)
    pyf.add_gen(grid, '63.0', '17', price_zone_link=False, lf=10, qf=0, MWmax=520.0, MWmin=0.0, MVArmax=250.0, MVArmin=-300.0, PsetMW=488.0, QsetMVA=152.0)
    pyf.add_gen(grid, '64.0', '18', price_zone_link=False, lf=10, qf=0, MWmax=560.0, MWmin=0.0, MVArmax=250.0, MVArmin=-400.0, PsetMW=300.0, QsetMVA=61.0)
    pyf.add_gen(grid, '66.0', '19', price_zone_link=False, lf=10, qf=0, MWmax=630.0, MWmin=0.0, MVArmax=300.0, MVArmin=-400.0, PsetMW=537.0, QsetMVA=143.0)
    pyf.add_gen(grid, '67.0', '20', price_zone_link=False, lf=10, qf=0, MWmax=800.0, MWmin=0.0, MVArmax=0.0, MVArmin=0.0, PsetMW=800.0, QsetMVA=0.0)
    
    
    # Add Renewable Source Zones

    
    # Add Renewable Sources

    
    # Return the grid
    return grid,res
