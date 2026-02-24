from scipy.io import loadmat
import pandas as pd
import numpy as np
import copy
import networkx as nx
from shapely.geometry import Polygon, Point
from shapely.wkt import loads

from .Results_class import*
from .Classes import*
from .Class_editor import Cable_parameters, Converter_parameters, add_gen

import pickle
import gzip

try:
    import dill  # optional fallback
    _dill = dill
except Exception:
    _dill = None


__all__ = [ # Grid Creation and Import
    'Create_grid_from_data',
    'Create_grid_from_mat',
    'Create_grid_from_turbine_graph',
    'Extend_grid_from_data',
    'initialize_pyflowacdc',
    'Create_grid_from_pickle'
]

def initialize_pyflowacdc():
    Node_AC.reset_class()
    Line_AC.reset_class()
    Size_selection.reset_class()
    TF_Line_AC.reset_class()
    
    Node_DC.reset_class()
    Line_DC.reset_class()
    DCDC_converter.reset_class()

    AC_DC_converter.reset_class()

    TimeSeries.reset_class()
    investment_periods.reset_class()
      
    Ren_source_zone.reset_class()
    Price_Zone.reset_class()
  
    Gen_AC.reset_class()
    Ren_Source.reset_class()
    
    
def Create_grid_from_data(S_base, AC_node_data=None, AC_line_data=None, DC_node_data=None, DC_line_data=None, Converter_data=None, data_in='Real'):
    
    if isinstance(AC_node_data, str):
        AC_node_data = pd.read_csv(AC_node_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(AC_line_data, str):
        AC_line_data = pd.read_csv(AC_line_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(DC_node_data, str):
        DC_node_data = pd.read_csv(DC_node_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(DC_line_data, str):
        DC_line_data = pd.read_csv(DC_line_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(Converter_data, str):
        Converter_data = pd.read_csv(Converter_data, delimiter=",", quotechar="'", encoding="utf-8")

    initialize_pyflowacdc()
    
    AC_nodes = process_AC_node(S_base, data_in, AC_node_data) if AC_node_data is not None else None
    AC_nodes_list = list(AC_nodes.values()) if AC_nodes is not None else []
    
    DC_nodes = process_DC_node(S_base, data_in, DC_node_data) if DC_node_data is not None else None
    DC_nodes_list = list(DC_nodes.values()) if DC_nodes is not None else []
    
    AC_lines = process_AC_line(S_base, data_in, AC_line_data, AC_nodes) if AC_line_data is not None else None
    AC_lines_list = list(AC_lines.values()) if AC_lines is not None else []
        
    DC_lines = process_DC_line(S_base, data_in, DC_line_data, DC_nodes) if DC_line_data is not None else None
    DC_lines_list = list(DC_lines.values()) if DC_lines is not None else []
    
    ACDC_convs = process_ACDC_converters(S_base, data_in, Converter_data, AC_nodes, DC_nodes) if Converter_data is not None else None
    Convertor_list = list(ACDC_convs.values()) if ACDC_convs is not None else []
        
        
    G = Grid(S_base, AC_nodes_list, AC_lines_list, nodes_DC=DC_nodes_list,
             lines_DC=DC_lines_list, Converters=Convertor_list)
    res = Results(G, decimals=3)

    return [G, res]

def Extend_grid_from_data(grid, AC_node_data=None, AC_line_data=None, DC_node_data=None, DC_line_data=None, Converter_data=None, data_in='Real'):
    

    if isinstance(AC_node_data, str):
        AC_node_data = pd.read_csv(AC_node_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(AC_line_data, str):
        AC_line_data = pd.read_csv(AC_line_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(DC_node_data, str):
        DC_node_data = pd.read_csv(DC_node_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(DC_line_data, str):
        DC_line_data = pd.read_csv(DC_line_data, delimiter=",", quotechar="'", encoding="utf-8")
    if isinstance(Converter_data, str):
        Converter_data = pd.read_csv(Converter_data, delimiter=",", quotechar="'", encoding="utf-8")
        
    S_base= grid.S_base
    
    AC_nodes = process_AC_node(S_base, data_in, AC_node_data) if AC_node_data is not None else None
    AC_nodes_list = list(AC_nodes.values()) if AC_nodes is not None else []
    grid.extend_nodes_AC(AC_nodes_list)
    
    DC_nodes = process_DC_node(S_base, data_in, DC_node_data) if DC_node_data is not None else None
    DC_nodes_list = list(DC_nodes.values()) if DC_nodes is not None else []
    grid.extend_nodes_DC(DC_nodes_list)
    
    AC_lines = process_AC_line(S_base, data_in, AC_line_data, grid=grid) if AC_line_data is not None else None
    AC_lines_list = list(AC_lines.values()) if AC_lines is not None else []
    
    DC_lines = process_DC_line(S_base, data_in, DC_line_data, grid=grid) if DC_line_data is not None else None
    DC_lines_list = list(DC_lines.values()) if DC_lines is not None else []
    
    ACDC_convs = process_ACDC_converters(S_base, data_in, Converter_data, grid=grid) if Converter_data is not None else None
    Convertor_list = list(ACDC_convs.values()) if ACDC_convs is not None else []

    
    grid.lines_AC.extend(AC_lines_list)
    grid.lines_DC.extend(DC_lines_list)
    grid.Converters_ACDC.extend(Convertor_list)
    
    grid.create_Ybus_AC()
    grid.create_Ybus_DC()
    
    
    if grid.nodes_AC: 
        grid.Update_Graph_AC()
        grid.Update_PQ_AC()
    if grid.nodes_DC: 
        grid.Update_Graph_DC()
        grid.Update_P_DC()
        
    return grid


    
def process_AC_node(S_base,data_in,AC_node_data):
    if data_in == 'pu':
        "AC nodes data sorting in pu"
        AC_node_data = AC_node_data.set_index('Node_id')
        AC_nodes = {}
        for index, row in AC_node_data.iterrows():
            var_name = index
            element_type = AC_node_data.at[index, 'type']               if 'type'            in AC_node_data.columns else 'PQ'

            kV_base       = AC_node_data.at[index, 'kV_base']
            Voltage_0 = AC_node_data.at[index, 'Voltage_0']             if 'Voltage_0'       in AC_node_data.columns else 1.01
            theta_0 = AC_node_data.at[index, 'theta_0']                 if 'theta_0'         in AC_node_data.columns else 0.01
            Power_Gained    = AC_node_data.at[index, 'Power_Gained']    if 'Power_Gained'    in AC_node_data.columns else 0
            Reactive_Gained = AC_node_data.at[index, 'Reactive_Gained'] if 'Reactive_Gained' in AC_node_data.columns else 0
            Power_load      = AC_node_data.at[index, 'Power_load']      if 'Power_load'      in AC_node_data.columns else 0
            Reactive_load   = AC_node_data.at[index, 'Reactive_load']   if 'Reactive_load'   in AC_node_data.columns else 0
            Umin            = AC_node_data.at[index, 'Umin']            if 'Umin'            in AC_node_data.columns else 0.9
            Umax            = AC_node_data.at[index, 'Umax']            if 'Umax'            in AC_node_data.columns else 1.1
            x_coord         = AC_node_data.at[index, 'x_coord']         if 'x_coord'         in AC_node_data.columns else None
            y_coord         = AC_node_data.at[index, 'y_coord']         if 'y_coord'         in AC_node_data.columns else None
            Bs              = AC_node_data.at[index, 'Bs']              if 'Bs'              in AC_node_data.columns else 0
            Gs              = AC_node_data.at[index, 'Gs']              if 'Gs'              in AC_node_data.columns else 0
            
            geometry        = AC_node_data.at[index, 'geometry']        if 'geometry'         in AC_node_data.columns else None



            AC_nodes[var_name] = Node_AC(element_type, Voltage_0, theta_0,kV_base, Power_Gained,
                                         Reactive_Gained, Power_load, Reactive_load, name=str(var_name),Umin=Umin,Umax=Umax,Gs=Gs,Bs=Bs,x_coord=x_coord,y_coord=y_coord)
            if geometry is not None:
               if isinstance(geometry, str): 
                    geometry = loads(geometry)  
               AC_nodes[var_name].geometry = geometry
               AC_nodes[var_name].x_coord = geometry.x
               AC_nodes[var_name].y_coord = geometry.y
        
    else:
        "AC nodes data sorting in real"
        AC_node_data = AC_node_data.set_index('Node_id')
        AC_nodes = {}
        for index, row in AC_node_data.iterrows():
            
            var_name = index
            element_type = AC_node_data.at[index, 'type']               if 'type'            in AC_node_data.columns else 'PQ'
            kV_base = AC_node_data.at[index, 'kV_base']
            
            Voltage_0 = AC_node_data.at[index, 'Voltage_0']             if 'Voltage_0'       in AC_node_data.columns else 1.01
            theta_0 = AC_node_data.at[index, 'theta_0']                 if 'theta_0'         in AC_node_data.columns else 0.01
            Power_Gained    = AC_node_data.at[index, 'Power_Gained']    if 'Power_Gained'    in AC_node_data.columns else 0
            Reactive_Gained = AC_node_data.at[index, 'Reactive_Gained'] if 'Reactive_Gained' in AC_node_data.columns else 0
            Power_load      = AC_node_data.at[index, 'Power_load']      if 'Power_load'      in AC_node_data.columns else 0
            Reactive_load   = AC_node_data.at[index, 'Reactive_load']   if 'Reactive_load'   in AC_node_data.columns else 0
            Umin            = AC_node_data.at[index, 'Umin']            if 'Umin'            in AC_node_data.columns else 0.9
            Umax            = AC_node_data.at[index, 'Umax']            if 'Umax'            in AC_node_data.columns else 1.1
            x_coord         = AC_node_data.at[index, 'x_coord']         if 'x_coord'         in AC_node_data.columns else None
            y_coord         = AC_node_data.at[index, 'y_coord']         if 'y_coord'         in AC_node_data.columns else None
            Bs              = AC_node_data.at[index, 'Bs']              if 'Bs'              in AC_node_data.columns else 0
            Gs              = AC_node_data.at[index, 'Gs']              if 'Gs'              in AC_node_data.columns else 0
            
            geometry        = AC_node_data.at[index, 'geometry']        if 'geometry'         in AC_node_data.columns else None
            
            Bs/=S_base
            Gs/=S_base
            Power_Gained    /=S_base
            Reactive_Gained /=S_base
            Power_load      /=S_base
            Reactive_load   /=S_base

            AC_nodes[var_name] = Node_AC(element_type, Voltage_0, theta_0,kV_base, Power_Gained,
                                         Reactive_Gained, Power_load, Reactive_load, name=str(var_name),Umin=Umin,Umax=Umax,Gs=Gs,Bs=Bs,x_coord=x_coord,y_coord=y_coord)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                AC_nodes[var_name].geometry = geometry
                AC_nodes[var_name].x_coord = geometry.x
                AC_nodes[var_name].y_coord = geometry.y
    return AC_nodes
    
def process_AC_line(S_base,data_in,AC_line_data,AC_nodes=None,grid=None):
    AC_line_data = AC_line_data.set_index('Line_id') if 'Line_id' in AC_line_data.columns else AC_line_data.set_index('transformer_id')
     
    AC_lines = {}
    
    if data_in == 'pu':
      
        for index, row in AC_line_data.iterrows():
            var_name = index
            if AC_nodes is not None:
                fromNode     = AC_nodes[AC_line_data.at[index, 'fromNode']] 
                toNode       = AC_nodes[AC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'toNode']]]  

            Resistance   = AC_line_data.at[index, 'r']   if 'r'  in AC_line_data.columns else  0.00001
            Reactance    = AC_line_data.at[index, 'x']    if 'x'  in AC_line_data.columns else   0.00001
            Conductance  = AC_line_data.at[index, 'g']  if 'g'  in AC_line_data.columns else 0
            Susceptance  = AC_line_data.at[index, 'b']  if 'b'  in AC_line_data.columns else 0
            MVA_rating   = AC_line_data.at[index, 'MVA_rating']   if 'MVA_rating'   in AC_line_data.columns else S_base*1.05
            km           = AC_line_data.at[index, 'Length_km']    if 'Length_km'    in AC_line_data.columns else 1
            kV_base      = toNode.kV_base 
            m            = AC_line_data.at[index, 'm']            if 'm'            in AC_line_data.columns else 1
            shift        = AC_line_data.at[index, 'shift']        if 'shift'        in AC_line_data.columns else 0

            geometry        = AC_line_data.at[index, 'geometry']  if 'geometry'     in AC_line_data.columns else None
            if 'is_transformer' in AC_line_data.columns:
                isTF = AC_line_data.at[index, 'is_transformer'] == 1
            elif 'transformer_id' in AC_line_data.columns:
                isTF = True
            else:
                isTF = False 
            AC_lines[var_name] = Line_AC(fromNode, toNode, Resistance,
                                         Reactance, Conductance, Susceptance, MVA_rating,km,m,shift ,name=str(var_name),S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                AC_lines[var_name].geometry = geometry
            if isTF:
                AC_lines[var_name].isTF= True
    
    elif data_in == 'Ohm':
      
        for index, row in AC_line_data.iterrows():
            var_name = index
            if AC_nodes is not None:
                fromNode     = AC_nodes[AC_line_data.at[index, 'fromNode']] 
                toNode       = AC_nodes[AC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'toNode']]]  

            Resistance   = AC_line_data.at[index, 'R']   if 'R'   in AC_line_data.columns else None
            Reactance    = AC_line_data.at[index, 'X']   if 'X'   in AC_line_data.columns else None
            Conductance  = AC_line_data.at[index, 'G']   if 'G'   in AC_line_data.columns else 0
            Susceptance  = AC_line_data.at[index, 'B']   if 'B'   in AC_line_data.columns else 0
            MVA_rating   = AC_line_data.at[index, 'MVA_rating']   if 'MVA_rating'   in AC_line_data.columns else 99999
            A_rating       = AC_line_data.at[index, 'A_rating']   if 'A_rating'   in AC_line_data.columns else None
            
            km           = AC_line_data.at[index, 'Length_km']    if 'Length_km'    in AC_line_data.columns else 1
            kV_base      = toNode.kV_base 
            m            = AC_line_data.at[index, 'm']            if 'm'            in AC_line_data.columns else 1
            shift        = AC_line_data.at[index, 'shift']        if 'shift'        in AC_line_data.columns else 0

            geometry        = AC_line_data.at[index, 'geometry']  if 'geometry'     in AC_line_data.columns else None
            if 'is_transformer' in AC_line_data.columns:
                isTF = AC_line_data.at[index, 'is_transformer'] == 1
            elif 'transformer_id' in AC_line_data.columns:
                isTF = True
            else:
                isTF = False
            
            if A_rating is not None:
                N_cables = AC_line_data.at[index, 'N_cables']  if 'N_cables'   in AC_line_data.columns else 1
                MVA_rating = N_cables*A_rating*kV_base*np.sqrt(3)/(1000)


            Z_base = kV_base**2/S_base
            
            Resistance = Resistance / Z_base if Resistance else 0.0001
            Reactance  = Reactance  / Z_base if Reactance  else 0.0001
            Conductance *= Z_base
            Susceptance *= Z_base
            
            
            AC_lines[var_name] = Line_AC(fromNode, toNode, Resistance,
                                         Reactance, Conductance, Susceptance, MVA_rating,km,m,shift ,name=str(var_name),S_base=S_base)
            
            
            
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                AC_lines[var_name].geometry = geometry
            if isTF:
                AC_lines[var_name].isTF= True
    else:
        
        for index, row in AC_line_data.iterrows():
            var_name = index
            
            if AC_nodes is not None:
                fromNode     = AC_nodes[AC_line_data.at[index, 'fromNode']] 
                toNode       = AC_nodes[AC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_AC[grid.nodes_dict_AC[AC_line_data.at[index, 'toNode']]]  
            
            R = AC_line_data.at[index, 'R_Ohm_km']
            L_mH = AC_line_data.at[index, 'L_mH_km']       
            C_uF = AC_line_data.at[index, 'C_uF_km']       if 'C_uF_km'    in AC_line_data.columns else 0
            G_uS = AC_line_data.at[index, 'G_uS_km']       if 'G_uS_km'    in AC_line_data.columns else 0
            A_rating = AC_line_data.at[index, 'A_rating']   if 'A_rating'   in AC_line_data.columns else 9999
            # kV_base = AC_line_data.at[index, 'kV_base']
            kV_base= toNode.kV_base 
            #print(AC_line_data['Length_km'].dtype)
            km = AC_line_data.at[index, 'Length_km']      if 'Length_km'   in AC_line_data.columns else 1
            #print(type(km))
            N_cables = AC_line_data.at[index, 'N_cables']  if 'N_cables'   in AC_line_data.columns else 1
            m    = AC_line_data.at[index, 'm']             if 'm'            in AC_line_data.columns else 1
            shift= AC_line_data.at[index, 'shift']         if 'shift'        in AC_line_data.columns else 0
           
            if 'is_transformer' in AC_line_data.columns:
                isTF = AC_line_data.at[index, 'is_transformer'] == 1
            elif 'transformer_id' in AC_line_data.columns:
                isTF = True
            else:
                isTF = False    
            [Resistance, Reactance, Conductance, Susceptance, MVA_rating] = Cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km,N_cables=N_cables)
            
            geometry        = AC_line_data.at[index, 'geometry']  if 'geometry'     in AC_line_data.columns else None
           
            AC_lines[var_name] = Line_AC(fromNode, toNode, Resistance,
                                         Reactance, Conductance, Susceptance, MVA_rating, km,m,shift,name=str(var_name),S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                AC_lines[var_name].geometry = geometry
            if isTF:
                AC_lines[var_name].isTF= True
    return AC_lines

def process_DC_node(S_base,data_in,DC_node_data):
    if data_in == 'pu':
        DC_node_data = DC_node_data.set_index('Node_id')

        "DC nodes data sorting"
        DC_nodes = {}
        for index, row in DC_node_data.iterrows():

            var_name = index
            node_type = DC_node_data.at[index, 'type']              if 'type'          in DC_node_data.columns else 'P'

            Voltage_0     = DC_node_data.at[index, 'Voltage_0']     if 'Voltage_0'     in DC_node_data.columns else 1.01
            Power_Gained  = DC_node_data.at[index, 'Power_Gained']  if 'Power_Gained'  in DC_node_data.columns else 0
            Power_load    = DC_node_data.at[index, 'Power_Load']    if 'Power_Load'    in DC_node_data.columns else 0
            kV_base       = DC_node_data.at[index, 'kV_base']  
            Umin          = DC_node_data.at[index, 'Umin']          if 'Umin'          in DC_node_data.columns else 0.95
            Umax          = DC_node_data.at[index, 'Umax']          if 'Umax'          in DC_node_data.columns else 1.05
            x_coord       = DC_node_data.at[index, 'x_coord']       if 'x_coord'       in DC_node_data.columns else None
            y_coord       = DC_node_data.at[index, 'y_coord']       if 'y_coord'       in DC_node_data.columns else None
            
            geometry      = DC_node_data.at[index, 'geometry']        if 'geometry'    in DC_node_data.columns else None
                
            DC_nodes[var_name] = Node_DC(node_type,kV_base, Voltage_0, Power_Gained, Power_load, name=str(var_name),Umin=Umin,Umax=Umax,x_coord=x_coord,y_coord=y_coord)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                DC_nodes[var_name].geometry = geometry
    else:
        DC_node_data = DC_node_data.set_index('Node_id')

        "DC nodes data sorting"
        DC_nodes = {}
        for index, row in DC_node_data.iterrows():

            var_name = index 
            node_type = DC_node_data.at[index, 'type']              if 'type'          in DC_node_data.columns else 'P'
            
            Voltage_0     = DC_node_data.at[index, 'Voltage_0']     if 'Power_Gained'  in DC_node_data.columns else 1.01
            Power_Gained  = DC_node_data.at[index, 'Power_Gained']  if 'Power_Gained'  in DC_node_data.columns else 0
            Power_load    = DC_node_data.at[index, 'Power_Load']    if 'Power_Load'    in DC_node_data.columns else 0
            kV_base       = DC_node_data.at[index, 'kV_base']  
            Umin          = DC_node_data.at[index, 'Umin']          if 'Umin'          in DC_node_data.columns else 0.95
            Umax          = DC_node_data.at[index, 'Umax']          if 'Umax'          in DC_node_data.columns else 1.05
            x_coord       = DC_node_data.at[index, 'x_coord']       if 'x_coord'       in DC_node_data.columns else None
            y_coord       = DC_node_data.at[index, 'y_coord']       if 'y_coord'       in DC_node_data.columns else None

            Power_Gained = Power_Gained/S_base
            Power_load = Power_load/S_base
            
            geometry      = DC_node_data.at[index, 'geometry']        if 'geometry'    in DC_node_data.columns else None
            
            DC_nodes[var_name] = Node_DC(node_type,kV_base, Voltage_0, Power_Gained, Power_load, name=str(var_name),Umin=Umin,Umax=Umax,x_coord=x_coord,y_coord=y_coord)
            
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                DC_nodes[var_name].geometry = geometry
            
    return DC_nodes

def process_DC_line(S_base,data_in,DC_line_data,DC_nodes=None,grid=None):
    if data_in == 'pu':
        DC_nodes_list = list(DC_nodes.values())

        DC_line_data = DC_line_data.set_index('Line_id')
        DC_lines = {}
        for index, row in DC_line_data.iterrows():
            var_name = index
            
            if DC_nodes is not None:
                fromNode     = DC_nodes[DC_line_data.at[index, 'fromNode']] 
                toNode       = DC_nodes[DC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'toNode']]]  
            
            
            Resistance    = DC_line_data.at[index, 'r']    if 'r'  in DC_line_data.columns else 0.0001
            MW_rating     = DC_line_data.at[index, 'MW_rating']      if 'MW_rating'     in DC_line_data.columns else 99999
            kV_base       = toNode.kV_base 
            pol           = DC_line_data.at[index, 'Mono_Bi_polar']  if 'Mono_Bi_polar' in DC_line_data.columns else 'm'
            km            = DC_line_data.at[index, 'Length_km']        if 'Length_km' in DC_line_data.columns else 1
            N_cables      = DC_line_data.at[index, 'N_cables']   if 'N_cables' in DC_line_data.columns else 1
            
            
            geometry      = DC_line_data.at[index, 'geometry']        if 'geometry'    in DC_line_data.columns else None
            DC_lines[var_name] = Line_DC(fromNode, toNode, Resistance, MW_rating, km, pol,name=str(var_name),N_cables=N_cables,S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                DC_lines[var_name].geometry = geometry
    
    elif data_in == 'Ohm':
        DC_nodes_list = list(DC_nodes.values())

        DC_line_data = DC_line_data.set_index('Line_id')
        DC_lines = {}
        for index, row in DC_line_data.iterrows():
            var_name = index
            
            if DC_nodes is not None:
                fromNode     = DC_nodes[DC_line_data.at[index, 'fromNode']] 
                toNode       = DC_nodes[DC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'toNode']]]  
            
            
            
            MW_rating     = DC_line_data.at[index, 'MW_rating']      if 'MW_rating'     in DC_line_data.columns else 99999
            kV_base       = toNode.kV_base 
            pol           = DC_line_data.at[index, 'Mono_Bi_polar']  if 'Mono_Bi_polar' in DC_line_data.columns else 'm'
            km            = DC_line_data.at[index, 'Length_km']      if 'Length_km' in DC_line_data.columns else 1
            N_cables      = DC_line_data.at[index, 'N_cables']       if 'N_cables' in DC_line_data.columns else 1
            Resistance    = DC_line_data.at[index, 'R']              if 'R'  in DC_line_data.columns else 0.0095*km
            
            
            Z_base = kV_base**2/S_base
            Resistance = Resistance / Z_base if Resistance else 0.00001
          
            
            
            geometry      = DC_line_data.at[index, 'geometry']        if 'geometry'    in DC_line_data.columns else None
            DC_lines[var_name] = Line_DC(fromNode, toNode, Resistance, MW_rating, km, pol,name=str(var_name),N_cables=N_cables,S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                DC_lines[var_name].geometry = geometry
    
    else:
        DC_line_data = DC_line_data.set_index('Line_id')
        DC_lines = {}
        for index, row in DC_line_data.iterrows():
            var_name = index

            if DC_nodes is not None:
                fromNode     = DC_nodes[DC_line_data.at[index, 'fromNode']] 
                toNode       = DC_nodes[DC_line_data.at[index, 'toNode']]
            else:
                fromNode = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'fromNode']]] 
                toNode   = grid.nodes_DC[grid.nodes_dict_DC[DC_line_data.at[index, 'toNode']]]  
            
            R = DC_line_data.at[index, 'R_Ohm_km']  if 'R_Ohm_km' in DC_line_data.columns else 0.0095
            A_rating = DC_line_data.at[index, 'A_rating']  if 'A_rating' in DC_line_data.columns else 9999
            kV_base = toNode.kV_base 
            pol  = DC_line_data.at[index, 'Mono_Bi_polar']  if 'Mono_Bi_polar' in DC_line_data.columns else 'm'
            km = DC_line_data.at[index, 'Length_km']        if 'Length_km' in DC_line_data.columns else 1
            N_cables = DC_line_data.at[index, 'N_cables']   if 'N_cables' in DC_line_data.columns else 1
            L_mH = 0
            C_uF = 0
            G_uS = 0
            [Resistance, _, _, _, MW_rating] = Cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km, N_cables=1)
            
            if pol == 'm':
                pol_val = 1
            elif pol == 'b' or pol == 'sm':
                pol_val = 2
            else:
                pol_val = 1
            MW_rating=MW_rating*pol_val
            geometry      = DC_line_data.at[index, 'geometry']        if 'geometry'    in DC_line_data.columns else None
            
            DC_lines[var_name] = Line_DC(fromNode, toNode, Resistance, MW_rating, km, pol,name=str(var_name),N_cables=N_cables,S_base=S_base)
            
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                DC_lines[var_name].geometry = geometry
            
    return DC_lines

def process_ACDC_converters(S_base,data_in,Converter_data,AC_nodes=None,DC_nodes=None,grid=None):
    if data_in == 'pu':
        Converter_data = Converter_data.set_index('Conv_id')
        "Convertor data sorting"
        Converters = {}
        for index, row in Converter_data.iterrows():
            var_name        = index
            if AC_nodes is not None and DC_nodes is not None:
                AC_node         = AC_nodes[Converter_data.at[index, 'AC_node']]         
                DC_node         = DC_nodes[Converter_data.at[index, 'DC_node']] 
            else:
                AC_node     = grid.nodes_DC[grid.nodes_dict_AC[Converter_data.at[index, 'AC_node']]] 
                DC_node     = grid.nodes_DC[grid.nodes_dict_DC[Converter_data.at[index, 'DC_node']]]  
            AC_type         = Converter_data.at[index, 'AC_type']        if 'AC_type'        in Converter_data.columns else AC_node.type
            DC_type         = Converter_data.at[index, 'DC_type']        if 'DC_type'        in Converter_data.columns else DC_node.type
            P_AC            = Converter_data.at[index, 'P_AC']           if 'P_AC'           in Converter_data.columns else 0
            Q_AC            = Converter_data.at[index, 'Q_AC']           if 'Q_AC'           in Converter_data.columns else 0
            P_DC            = Converter_data.at[index, 'P_DC']           if 'P_DC'           in Converter_data.columns else 0
            T_R_pu          = Converter_data.at[index, 'T_r']            if 'T_r'            in Converter_data.columns else 0
            T_X_pu          = Converter_data.at[index, 'T_x']            if 'T_x'            in Converter_data.columns else 0
            PR_R_pu         = Converter_data.at[index, 'PR_r']           if 'PR_r'           in Converter_data.columns else 0
            PR_X_pu         = Converter_data.at[index, 'PR_x']           if 'PR_x'           in Converter_data.columns else 0   
            Filter_pu       = Converter_data.at[index, 'Filter_b']       if 'Filter_b'       in Converter_data.columns else 0
            Droop           = Converter_data.at[index, 'Droop']          if 'Droop'          in Converter_data.columns else 0
            kV_base         = Converter_data.at[index, 'AC_kV_base']     if 'AC_kV_base'     in Converter_data.columns else AC_node.kV_base
            MVA_max         = Converter_data.at[index, 'MVA_rating']     if 'MVA_rating'     in Converter_data.columns else 99999
            Ucmin           = Converter_data.at[index, 'Ucmin']          if 'Ucmin'          in Converter_data.columns else 0.85
            Ucmax           = Converter_data.at[index, 'Ucmax']          if 'Ucmax'          in Converter_data.columns else 1.2
            n               = Converter_data.at[index, 'Nconverter']     if 'Nconverter'     in Converter_data.columns else 1
            pol             = Converter_data.at[index, 'pol']            if 'pol'            in Converter_data.columns else 1
            LossA           = Converter_data.at[index, 'lossa']          if 'lossa'          in Converter_data.columns else 1.103
            LossB           = Converter_data.at[index, 'lossb']          if 'lossb'          in Converter_data.columns else 0.887
            LossCrec        = Converter_data.at[index, 'losscrect']      if 'losscrect'      in Converter_data.columns else 2.885
            LossCinv        = Converter_data.at[index, 'losscinv']       if 'losscinv'       in Converter_data.columns else 4.371
            arm_res         = Converter_data.at[index, 'A_r']            if 'A_r'            in Converter_data.columns else 0.001

            geometry      = Converter_data.at[index, 'geometry']         if 'geometry'    in Converter_data.columns else None
                     
            Converters[var_name] = AC_DC_converter(AC_type, DC_type, AC_node, DC_node, P_AC, Q_AC, P_DC, T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu, Droop, kV_base, 
                    MVA_max=MVA_max,nConvP=n,polarity=pol,Ucmin=Ucmin,Ucmax=Ucmax,lossa=LossA,lossb=LossB,losscrect=LossCrec ,losscinv=LossCinv ,arm_res=arm_res, 
                    name=str(var_name),S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                Converters[var_name].geometry = geometry    
    elif data_in == 'Ohm':
        Converter_data = Converter_data.set_index('Conv_id')
        "Convertor data sorting"
        Converters = {}
        for index, row in Converter_data.iterrows():
            var_name        = index
            if AC_nodes is not None and DC_nodes is not None:
                AC_node         = AC_nodes[Converter_data.at[index, 'AC_node']]         
                DC_node         = DC_nodes[Converter_data.at[index, 'DC_node']] 
            else:
                AC_node     = grid.nodes_DC[grid.nodes_dict_AC[Converter_data.at[index, 'AC_node']]] 
                DC_node     = grid.nodes_DC[grid.nodes_dict_DC[Converter_data.at[index, 'DC_node']]]  
            AC_type         = Converter_data.at[index, 'AC_type']        if 'AC_type'        in Converter_data.columns else AC_node.type
            DC_type         = Converter_data.at[index, 'DC_type']        if 'DC_type'        in Converter_data.columns else DC_node.type
            P_AC            = Converter_data.at[index, 'P_MW_AC']           if 'P_MW_AC'           in Converter_data.columns else 0
            Q_AC            = Converter_data.at[index, 'Q_MVA_AC']           if 'Q_MVA_AC'           in Converter_data.columns else 0
            P_DC            = Converter_data.at[index, 'P_MW_DC']           if 'P_MW_DC'           in Converter_data.columns else 0
            Transformer_R   = Converter_data.at[index, 'T_R']            if 'T_R'            in Converter_data.columns else 0
            Transformer_X   = Converter_data.at[index, 'T_X']            if 'T_X'            in Converter_data.columns else 0
            Phase_Reactor_R = Converter_data.at[index, 'PR_R']           if 'PR_R'           in Converter_data.columns else 0
            Phase_Reactor_X = Converter_data.at[index, 'PR_X']           if 'PR_X'           in Converter_data.columns else 0   
            Filter          = Converter_data.at[index, 'Filter_B']         if 'Filter_B'         in Converter_data.columns else 0
            Droop           = Converter_data.at[index, 'Droop']          if 'Droop'          in Converter_data.columns else 0
            kV_base         = Converter_data.at[index, 'AC_kV_base']     if 'AC_kV_base'     in Converter_data.columns else AC_node.kV_base
            MVA_max         = Converter_data.at[index, 'MVA_rating']     if 'MVA_rating'     in Converter_data.columns else 99999
            Ucmin           = Converter_data.at[index, 'Ucmin']          if 'Ucmin'          in Converter_data.columns else 0.85
            Ucmax           = Converter_data.at[index, 'Ucmax']          if 'Ucmax'          in Converter_data.columns else 1.2
            n               = Converter_data.at[index, 'Nconverter']     if 'Nconverter'     in Converter_data.columns else 1
            pol             = Converter_data.at[index, 'pol']            if 'pol'            in Converter_data.columns else 1
          
            LossA           = Converter_data.at[index, 'lossa']          if 'lossa'          in Converter_data.columns else 1.103
            LossB           = Converter_data.at[index, 'lossb']          if 'lossb'          in Converter_data.columns else 0.887
            LossCrec        = Converter_data.at[index, 'losscrect']      if 'losscrect'      in Converter_data.columns else 2.885
            LossCinv        = Converter_data.at[index, 'losscinv']       if 'losscinv'       in Converter_data.columns else 4.371

            arm_res_Ohm         = Converter_data.at[index, 'A_R']            if 'A_R'            in Converter_data.columns else None

            geometry      = Converter_data.at[index, 'geometry']         if 'geometry'    in Converter_data.columns else None

            P_AC = P_AC/S_base
            Q_AC = Q_AC/S_base
            P_DC = P_DC/S_base

            if arm_res_Ohm is not None:
                basekA_DC = S_base/(DC_node.kV_base)
                arm_res = arm_res_Ohm*basekA_DC**2/S_base
            else:
                arm_res = 0.001


            Z_base = kV_base**2/S_base
            T_R_pu = Transformer_R/Z_base
            T_X_pu = Transformer_X/Z_base
            PR_R_pu = Phase_Reactor_R/Z_base
            PR_X_pu = Phase_Reactor_X/Z_base
            Filter_pu = Filter*Z_base

            Converters[var_name] = AC_DC_converter(AC_type, DC_type, AC_node, DC_node, P_AC, Q_AC, P_DC, T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu, Droop, kV_base,
             MVA_max=MVA_max,nConvP=n,polarity=pol,Ucmin=Ucmin,Ucmax=Ucmax,lossa=LossA,lossb=LossB,losscrect=LossCrec ,losscinv=LossCinv,arm_res=arm_res, name=str(var_name),S_base=S_base)
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                Converters[var_name].geometry = geometry
    else:
        Converter_data = Converter_data.set_index('Conv_id')
        "Convertor data sorting"
        Converters = {}
        for index, row in Converter_data.iterrows():
            var_name         = index
            if AC_nodes is not None and DC_nodes is not None:
                AC_node         = AC_nodes[Converter_data.at[index, 'AC_node']]         
                DC_node         = DC_nodes[Converter_data.at[index, 'DC_node']] 
            else:
                AC_node     = grid.nodes_AC[grid.nodes_dict_AC[Converter_data.at[index, 'AC_node']]] 
                DC_node     = grid.nodes_DC[grid.nodes_dict_DC[Converter_data.at[index, 'DC_node']]]  
            AC_type         = Converter_data.at[index, 'AC_type']        if 'AC_type'        in Converter_data.columns else AC_node.type
            DC_type         = Converter_data.at[index, 'DC_type']        if 'DC_type'        in Converter_data.columns else DC_node.type
            P_AC             = Converter_data.at[index, 'P_MW_AC']       if 'P_MW_AC'        in Converter_data.columns else 0
            Q_AC             = Converter_data.at[index, 'Q_MVA_AC']          if 'Q_MVA_AC'           in Converter_data.columns else 0
            P_DC             = Converter_data.at[index, 'P_MW_DC']       if 'P_MW_DC'        in Converter_data.columns else 0
            Transformer_R    = Converter_data.at[index, 'T_R_Ohm']       if 'T_R_Ohm'        in Converter_data.columns else 0
            Transformer_X    = Converter_data.at[index, 'T_X_mH']        if 'T_X_mH'         in Converter_data.columns else 0
            Phase_Reactor_R  = Converter_data.at[index, 'PR_R_Ohm']      if 'PR_R_Ohm'       in Converter_data.columns else 0
            Phase_Reactor_X  = Converter_data.at[index, 'PR_X_mH']       if 'PR_X_mH'        in Converter_data.columns else 0
            Filter           = Converter_data.at[index, 'Filter_uF']     if 'Filter_uF'      in Converter_data.columns else 0
            Droop            = Converter_data.at[index, 'Droop']         if 'Droop'          in Converter_data.columns else 0
            kV_base          = Converter_data.at[index, 'AC_kV_base']    if 'AC_kV_base'     in Converter_data.columns else AC_node.kV_base
            MVA_rating       = Converter_data.at[index, 'MVA_rating']    if 'MVA_rating'     in Converter_data.columns else 99999
            Ucmin           = Converter_data.at[index, 'Ucmin']          if 'Ucmin'          in Converter_data.columns else 0.85
            Ucmax           = Converter_data.at[index, 'Ucmax']          if 'Ucmax'          in Converter_data.columns else 1.2
            n               = Converter_data.at[index, 'Nconverter']     if 'Nconverter'     in Converter_data.columns else 1
            pol             = Converter_data.at[index, 'pol']            if 'pol'     in Converter_data.columns else 1
            
            LossA           = Converter_data.at[index, 'lossa']          if 'lossa'          in Converter_data.columns else 1.103
            LossB           = Converter_data.at[index, 'lossb']          if 'lossb'          in Converter_data.columns else 0.887
            LossCrec        = Converter_data.at[index, 'losscrect']      if 'losscrect'      in Converter_data.columns else 2.885
            LossCinv        = Converter_data.at[index, 'losscinv']       if 'losscinv'       in Converter_data.columns else 4.371
            arm_res_Ohm         = Converter_data.at[index, 'A_R']            if 'A_R'            in Converter_data.columns else 0

            if arm_res_Ohm is not None:
                basekA_DC = S_base/(DC_node.kV_base)
                arm_res = arm_res_Ohm*basekA_DC**2/S_base
            else:
                arm_res = 0.001


            [T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu] = Converter_parameters(S_base, kV_base, Transformer_R, Transformer_X, Phase_Reactor_R, Phase_Reactor_X, Filter)

            geometry      = Converter_data.at[index, 'geometry']         if 'geometry'    in Converter_data.columns else None

            MVA_max = MVA_rating
            P_AC = P_AC/S_base
            Q_AC = Q_AC/S_base
            P_DC = P_DC/S_base
            
           
            Converters[var_name] = AC_DC_converter(AC_type, DC_type, AC_node, DC_node, P_AC, Q_AC,
                                                   P_DC, T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu, Droop, kV_base, MVA_max=MVA_max,nConvP=n,polarity=pol,Ucmin=Ucmin,Ucmax=Ucmax ,
                                                   lossa=LossA,lossb=LossB,losscrect=LossCrec ,losscinv=LossCinv,arm_res=arm_res, name=str(var_name),S_base=S_base)
        
            if geometry is not None:
                if isinstance(geometry, str): 
                     geometry = loads(geometry)  
                Converters[var_name].geometry = geometry 
   
    for strg in Converters:
        conv = Converters[strg]
        conv.basekA  = S_base/(np.sqrt(3)*conv.AC_kV_base)
        conv.a_conv  = conv.a_conv_og/S_base
        conv.b_conv  = conv.b_conv_og*conv.basekA/S_base
        conv.c_inver = conv.c_inver_og*conv.basekA**2/S_base
        conv.c_rect  = conv.c_rect_og*conv.basekA**2/S_base            
    

       
        
    return    Converters


def Create_grid_from_turbine_graph(array_graph,Data,S_base=100,cable_types=[],cable_database=None,cable_types_allowed=3,curtailment_allowed=0.05,max_turbines_per_string= None,LCoE=1,trenching_cost=1,MIP_time=None,name=None):
    from .Class_editor import add_AC_node, add_line_sizing, add_RenSource, add_extGrid, add_cable_option
    from .Classes import Cable_options, Line_AC, Line_DC

    turbines_df = Data["turbine"]
    substations_df = Data["offshore_substation"] if 'offshore_substation' in Data else Data['transformer_station']
    

    initialize_pyflowacdc()
    grid = Grid(S_base)
    if name is not None:
        grid.name = name
    res = Results(grid)

    # Handle cable_types and cable_database:
    # - If cable_database is provided: load it for all classes, extract cable_types from index if empty
    # - If cable_types is provided (no cable_database): use with default pyflow database
    # - If both empty: don't create cable_option
    
    if cable_database is not None:
        # User provided custom database - use it for all classes
        Cable_options.load_cable_database(cable_database=cable_database)
        Line_AC.load_cable_database(cable_database=cable_database)
        Line_DC.load_cable_database(cable_database=cable_database)
        
        # Extract cable types from database index if not provided
        if len(cable_types) == 0:
            cable_types = list(cable_database.index)
        
        cable_option = add_cable_option(grid, cable_types, cable_database=cable_database)
    elif len(cable_types) == 0:
        # No database and no cable_types - don't create cable_option
        cable_option = None
    else:
        # cable_types provided - use default pyflow database (lazy loaded when needed)
        cable_option = add_cable_option(grid, cable_types)
    t_MW = turbines_df.iloc[0].MW_rating
    if max_turbines_per_string is not None:
        
        max_power_per_string = t_MW*max_turbines_per_string 
        first_index_to_comply = next((i for i, rating in enumerate(cable_option.MVA_ratings) if rating >= max_power_per_string), len(cable_option.MVA_ratings) - 1)
        cable_option._cable_types = cable_option._cable_types[:first_index_to_comply + 1]
        cable_option.MVA_ratings = cable_option.MVA_ratings[:first_index_to_comply + 1]

    else:
    
        max_cable_capacity = max(cable_option.MVA_ratings)
        max_turbines_per_string = int(max_cable_capacity / t_MW)
        # Store it in the grid for later use
        grid.max_turbines_per_string = max_turbines_per_string
        
    
    for i, attrs in array_graph.nodes(data=True):
        if attrs['point_type'] == 'access_point':
            continue  # Skip access_point nodes - they're routing points, not AC nodes
        elif attrs['point_type'] == 'turbine':
            kV=   turbines_df.loc[attrs['original_idx']].kV_rating
            geo = turbines_df.loc[attrs['original_idx']].geometry
        else: 
            kV=   substations_df.loc[attrs['original_idx']].kV_rating
            geo = substations_df.loc[attrs['original_idx']].geometry

        node = add_AC_node(grid, kV, node_type='PQ',geometry=geo,name=str(i))

        if attrs['point_type'] == 'turbine':
            add_RenSource(grid,node,turbines_df.loc[attrs['original_idx']].MW_rating,ren_type='Wind',min_gamma=1-curtailment_allowed,Qrel=0)
            node.ct_limit = turbines_df.loc[attrs['original_idx']].connections
            
        if attrs['point_type'] == 'substation':
            add_extGrid(grid,node,MVAmax=99999,Allow_sell=True,lf=LCoE)
            node.ct_limit = substations_df.loc[attrs['original_idx']].connections
            node.type = 'Slack'
            node.V_ini = 1
            node.theta_ini = 0
            if 'turbine_limit' in substations_df.columns:
                node.pu_power_limit = substations_df.loc[attrs['original_idx']].turbine_limit
    # First pass: add all lines
    line_objects = {}  # Dictionary to store line objects by their name
    
    for u,v, attrs in array_graph.edges(data=True):
        # Ensure substations are always toNode so positive flow goes towards them
        # Note: In the graph, substation-turbine edges always have substation as u (from add_substation_paths_to_graph)
        u_is_substation = array_graph.nodes[u].get('point_type') == 'substation'
        v_is_substation = array_graph.nodes[v].get('point_type') == 'substation'
        
        u_is_access_point = array_graph.nodes[u].get('point_type') == 'access_point'
        v_is_access_point = array_graph.nodes[v].get('point_type') == 'access_point'
        # If u is substation and v is not, swap them (substation becomes toNode)
        # This is the common case for substation-turbine edges
        # If both or neither are substations, keep original order
        if u_is_access_point or v_is_access_point:
            continue
        if u_is_substation and not v_is_substation:
            fromnode = str(v)
            tonode = str(u)
            name= f'{str(v)}_{str(u)}'
            geo = attrs['geometry'].reverse()
        else:
            fromnode = str(u)
            tonode = str(v)
            name= f'{str(u)}_{str(v)}'
            geo = attrs['geometry']

        l = attrs['length']/1000
        w_l = attrs['weight']/1000
        
        line_obj = add_line_sizing(grid,fromnode,tonode,cable_option=cable_option.name,active_config=0,Length_km=l,name=name,geometry=geo,update_grid=False)
        
        line_obj.installation_cost_per_km = trenching_cost
        line_obj.trench_lenght_km = w_l
        # Store the line object using original graph edge key format for crossing_pairs lookup
        # crossing_pairs uses _generate_edge_key which creates f"{str(u)}_{str(v)}" (original graph order)
        original_edge_key = f'{str(u)}_{str(v)}'
        line_objects[original_edge_key] = line_obj
    
    # Add the complete crossing groups as line numbers to the grid
    grid.crossing_groups = []

    
    if 'crossing_pairs' in Data and Data['crossing_pairs']:
        limit_crossings=True
        for crossing_group in Data['crossing_pairs']:
            line_numbers_group = []
            for edge_key in crossing_group:
                if edge_key in line_objects:
                    line_numbers_group.append(line_objects[edge_key].lineNumber)
            if len(line_numbers_group) > 1:  # Only add groups with more than one line
                grid.crossing_groups.append(line_numbers_group)
    
        
    grid.Update_Graph_AC()
    grid.create_Ybus_AC()
    grid.Array_opf = True  
    grid.cab_types_allowed = cable_types_allowed
    grid.max_turbines_per_string = max_turbines_per_string
    
    grid.MIP_time = MIP_time
    
    # Enable crossings if there are crossing groups
    
    
    return grid, res

def Create_grid_from_mat(matfile):
    if not matfile.endswith('.mat'):
        matfile = matfile + '.mat'
    
    initialize_pyflowacdc()

    data = loadmat(matfile)

    bus_columns = ['bus_i', 'type', 'Pd', 'Qd', 'Gs', 'Bs', 'area', 'Vm', 'Va', 'baseKV', 'zone', 'Vmax', 'Vmin']
    branch_columns = ['fbus', 'tbus', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC', 'ratio', 'angle', 'status', 'angmin', 'angmax']
    gen_columns = ['bus', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status', 'Pmax', 'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min', 'Qc2max', 'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf']

    gencost_columns = ['2', 'startup', 'shutdown', 'n', 'c(n-1)','c(n-2)' ,'c0']

    busdc_columns = ['busdc_i',  'grid', 'Pdc', 'Vdc', 'basekVdc', 'Vdcmax', 'Vdcmin', 'Cdc']
    converter_columns = ['busdc_i', 'busac_i', 'type_dc', 'type_ac', 'P_g', 'Q_g', 'islcc', 'Vtar', 'rtf', 'xtf', 'transformer', 'tm', 'bf', 'filter', 'rc', 'xc', 'reactor', 'basekVac', 'Vmmax', 'Vmmin', 'Imax', 'status', 'LossA', 'LossB', 'LossCrec', 'LossCinv', 'droop', 'Pdcset', 'Vdcset', 'dVdcset', 'Pacmax', 'Pacmin', 'Qacmax', 'Qacmin']
    branch_DC = ['fbusdc', 'tbusdc', 'r', 'l', 'c', 'rateA', 'rateB', 'rateC', 'status']
    
    candidate_ac_branch = ['f_bus',	't_bus','br_r'	,'br_x'	,'br_b'	,'rate_a'	,'rate_b',	'rate_c',	'tap',	'shift',	'br_status',	'angmin'	,'angmax'	,'construction_cost']
    candidate_dc_bus = ['busdc_i' , 'grid' , 'Pdc' , 'Vdc' , 'basekVdc' , 'Vdcmax' , 'Vdcmin' , 'Cdc']
    candidate_dc_branch = ['fbusdc' , 'tbusdc' , 'r' , 'l' , 'c' , 'rateA' , 'rateB' , 'rateC' , 'status' , 'cost']
    candidate_conv = ['busdc_i' , 'busac_i' , 'type_dc' , 'type_ac' , 'P_g' , 'Q_g' , 'islcc' , 'Vtar' , 'rtf' , 'xtf' , 'transformer' , 'tm' , 'bf' , 'filter' , 'rc' , 'xc' , 'reactor' , 'basekVac' , 'Vmmax' , 'Vmmin' , 'Imax' , 'status' , 'LossA' , 'LossB' , 'LossCrec' , 'LossCinv' , 'droop' , 'Pdcset' , 'Vdcset' , 'dVdcset' , 'Pacmax' , 'Pacmin' , 'Qacmax' , 'Qacmin' , 'cost']

    S_base = data['baseMVA'][0, 0]
    
    dcpol = data['dcpol'][0, 0] if 'dcpol' in data else 2
    
    
    
    if 'bus' in data:
        num_data_columns = len(data['bus'][0])
        if num_data_columns > len(bus_columns):
            # Add extra column names if needed
            extra_columns = [f"extra_column_{i}" for i in range(num_data_columns - len(bus_columns))]
            bus_columns = bus_columns + extra_columns
        else:
            # Use only the required number of columns from bus_columns
            bus_columns = bus_columns[:num_data_columns]
        AC_node_data = pd.DataFrame(data['bus'], columns=bus_columns)  
    else:
        AC_node_data = None
    
    if 'branch' in data:
        num_data_columns = len(data['branch'][0])
        if num_data_columns > len(branch_columns):
            # Add extra column names if needed
            extra_columns = [f"extra_column_{i}" for i in range(num_data_columns - len(branch_columns))]
            branch_columns = branch_columns + extra_columns
        else:
            # Use only the required number of columns from bus_columns
            branch_columns = branch_columns[:num_data_columns]
        AC_line_data = pd.DataFrame(data['branch'], columns=branch_columns)  
    else:
        AC_line_data = None
    
    if 'ne_branch'in data:
        EXP_line_data = pd.DataFrame(data['ne_branch'], columns=candidate_ac_branch) 
    else:
        EXP_line_data = None

    if 'gen' in data:
        num_data_columns = len(data['gen'][0])
        if num_data_columns > len(gen_columns):
            # Add extra column names if needed
            extra_columns = [f"extra_column_{i}" for i in range(num_data_columns - len(gen_columns))]
            gen_columns = gen_columns + extra_columns
        else:
            # Use only the required number of columns from gen_columns
            gen_columns = gen_columns[:num_data_columns]
        Gen_data = pd.DataFrame(data['gen'], columns=gen_columns)  
    else:
        Gen_data = None
    
    
    # Gen_data = pd.DataFrame(data['gen'], columns=gen_columns)             if 'gen' in data else None    
    if 'gencost' in data:
        num_cols = data['gencost'].shape[1]
        first_model = int(data['gencost'][0, 0]) if data['gencost'].shape[0] > 0 else 2
        if first_model == 1:
            # Piecewise linear: model, startup, shutdown, n, (x1, y1), (x2, y2), ...
            gencost_columns = ['model', 'startup', 'shutdown', 'n']
            num_pairs = (num_cols - 4) // 2
            for i in range(1, num_pairs + 1):
                gencost_columns.extend([f'x{i}', f'y{i}'])
            # If there are any remaining columns (in case of odd number), add generic names
            if len(gencost_columns) < num_cols:
                gencost_columns += [f'extra_{i}' for i in range(len(gencost_columns)+1, num_cols+1)]
        else:
            # Polynomial: use the default columns, but trim or extend as needed
            default_poly_cols = ['model', 'startup', 'shutdown', 'n', 'c(n-1)', 'c(n-2)', 'c0']
            if num_cols > len(default_poly_cols):
                # Add extra columns if needed
                default_poly_cols += [f'extra_{i}' for i in range(len(default_poly_cols)+1, num_cols+1)]
            gencost_columns = default_poly_cols[:num_cols]
        Gen_data_cost = pd.DataFrame(data['gencost'], columns=gencost_columns)
    else:
        Gen_data_cost = None

    if 'busdc' in data:
        num_data_columns = len(data['busdc'][0])
        if num_data_columns > len(busdc_columns):
            # Add extra column names if needed
            extra_columns = [f"extra_column_{i}" for i in range(num_data_columns - len(busdc_columns))]
            busdc_columns = busdc_columns + extra_columns
        else:
            # Use only the required number of columns from gen_columns
            busdc_columns = busdc_columns[:num_data_columns]
        DC_node_data = pd.DataFrame(data['busdc'], columns=busdc_columns)  
    else:
        DC_node_data = None

    if 'busdc_ne' in data:
        num_data_columns = len(data['busdc_ne'][0])
        if num_data_columns > len(candidate_dc_bus):
            # Add extra column names if needed
            extra_columns = [f"extra_column_{i}" for i in range(num_data_columns - len(candidate_dc_bus))]
            candidate_dc_bus = candidate_dc_bus + extra_columns 
        DC_exp_node_data = pd.DataFrame(data['busdc_ne'], columns=candidate_dc_bus)   
    else:
        DC_exp_node_data = None

    # Safe concatenation of DC_node_data and DC_exp_node_data
    if DC_node_data is not None and DC_exp_node_data is not None:
        DC_node_data = pd.concat([DC_node_data, DC_exp_node_data])
    elif DC_node_data is None and DC_exp_node_data is not None:
        DC_node_data = DC_exp_node_data
    elif DC_node_data is not None and DC_exp_node_data is None:
        pass  # DC_node_data remains unchanged
    else:
        DC_node_data = None  # Both are None

    DC_line_data=pd.DataFrame(data['branchdc'], columns=branch_DC) if 'branchdc' in data else None
    if DC_line_data is not None:
        DC_line_data['cost'] = -1  # Add cost column with default value -1 for non expandable lines
    
    DC_exp_line_data=pd.DataFrame(data['branchdc_ne'], columns=candidate_dc_branch) if 'branchdc_ne' in data else None
    

    # Safe concatenation of DC_line_data and DC_exp_line_data
    if DC_line_data is not None and DC_exp_line_data is not None:
        DC_line_data = pd.concat([DC_line_data, DC_exp_line_data])
    elif DC_line_data is None and DC_exp_line_data is not None:
        DC_line_data = DC_exp_line_data
    elif DC_line_data is not None and DC_exp_line_data is None:
        pass  # DC_line_data remains unchanged
    else:
        DC_line_data = None  # Both are None

        
    Converter_data=pd.DataFrame(data['convdc'], columns=converter_columns) if 'convdc' in data else None
    if Converter_data is not None:
        Converter_data['cost'] = -1  #
    Conv_exp_data=pd.DataFrame(data['convdc_ne'], columns=candidate_conv) if 'convdc_ne' in data else None

    # Safe concatenation of Converter_data and Conv_exp_data
    if Converter_data is not None and Conv_exp_data is not None:
        Converter_data = pd.concat([Converter_data, Conv_exp_data])
    elif Converter_data is None and Conv_exp_data is not None:
        Converter_data = Conv_exp_data
    elif Converter_data is not None and Conv_exp_data is None:
        pass  # Converter_data remains unchanged
    else:
        Converter_data = None  # Both are None


    if AC_node_data is None:
        AC_nodes_list = None
        AC_lines_list = None
    else:
        "AC nodes data sorting"
        AC_node_data = AC_node_data.set_index('bus_i')
        AC_nodes = {}
        for index, row in AC_node_data.iterrows():
            var_name = index
            
            mat_type=AC_node_data.at[index, 'type']
            if mat_type == 1:
                element_type = 'PQ'
            elif mat_type == 2:
                element_type = 'PV'
            elif mat_type == 3:
                element_type = 'Slack'
             
            Gs = AC_node_data.at[index, 'Gs']/S_base
            Bs = AC_node_data.at[index, 'Bs']/S_base
          
            kV_base         = AC_node_data.at[index, 'baseKV']
            
            theta_0         = np.radians(AC_node_data.at[index, 'Va'])     
            
            
            Voltage_0 = Gen_data.loc[Gen_data['bus'] == index, 'Vg'].iloc[0] if Gen_data is not None and (Gen_data['bus'] == index).any() else 1.01
            
            Power_Gained = (Gen_data[Gen_data['bus'] == index]['Pg'].values[0] / S_base 
                if Gen_data is not None and not Gen_data[Gen_data['bus'] == index].empty 
                and Gen_data[Gen_data['bus'] == index]['status'].values[0] != 0 else 0)
            Reactive_Gained  = (Gen_data[Gen_data['bus'] == index]['Qg'].values[0] / S_base 
                if Gen_data is not None and not Gen_data[Gen_data['bus'] == index].empty 
                and Gen_data[Gen_data['bus'] == index]['status'].values[0] != 0 else 0)
            
            Power_load      = AC_node_data.at[index, 'Pd']/S_base   
            Reactive_load   = AC_node_data.at[index, 'Qd']/S_base
            Umin            = AC_node_data.at[index, 'Vmin']           
            Umax            = AC_node_data.at[index, 'Vmax']        
            x_coord         = AC_node_data.at[index, 'x_coord']         if 'x_coord'         in AC_node_data.columns else None
            y_coord         = AC_node_data.at[index, 'y_coord']         if 'y_coord'         in AC_node_data.columns else None
            

            AC_nodes[var_name] = Node_AC(element_type, Voltage_0, theta_0,kV_base, Power_Gained,
                                         Reactive_Gained, Power_load, Reactive_load, name=str(var_name),Umin=Umin,Umax=Umax,Gs=Gs,Bs=Bs,x_coord=x_coord,y_coord=y_coord)
        AC_nodes_list = list(AC_nodes.values())

        
        AC_lines = {}
        for index, row in AC_line_data.iterrows():
          if AC_line_data.at[index, 'status'] !=0:    
            var_name = f"L_AC_{index+1}"
            

            fromNode     = AC_line_data.at[index, 'fbus']
            toNode       = AC_line_data.at[index, 'tbus']
            r   = AC_line_data.at[index, 'r']
            x    = AC_line_data.at[index, 'x']    
            g  = 0
            b  = AC_line_data.at[index, 'b']  
            
            
            kV_base      = AC_nodes[toNode].kV_base 
            if AC_line_data.at[index, 'rateA'] == 0:
                MVA_rating=9999
            else:
                MVA_rating   = AC_line_data.at[index, 'rateA']
            if AC_line_data.at[index, 'ratio']== 0:
                m=1
                shift=0
            else:
                m            = AC_line_data.at[index, 'ratio']  
                shift        = np.radians(AC_line_data.at[index, 'angle'])

            km=1
            
            AC_lines[var_name] = Line_AC(AC_nodes[fromNode], AC_nodes[toNode], r,
                                         x, g, b, MVA_rating,km,m,shift ,name=str(var_name),S_base=S_base)
        AC_lines_list = list(AC_lines.values())

    if DC_node_data is None:

        DC_nodes_list = None
        DC_lines_list = None

    else:
        DC_node_data = DC_node_data.set_index('busdc_i')

        "DC nodes data sorting"
        DC_nodes = {} 
        for index, row in DC_node_data.iterrows():

            var_name = index
            node_type = 'P'

            Voltage_0     = DC_node_data.at[index, 'Vdc'] 
            Power_Gained  = 0
            Power_load    = DC_node_data.at[index, 'Pdc']/S_base   
            kV_base       = DC_node_data.at[index, 'basekVdc']  
            Umin          = DC_node_data.at[index, 'Vdcmin']         
            Umax          = DC_node_data.at[index, 'Vdcmax']       
            x_coord       = DC_node_data.at[index, 'x_coord']       if 'x_coord'       in DC_node_data.columns else None
            y_coord       = DC_node_data.at[index, 'y_coord']       if 'y_coord'       in DC_node_data.columns else None
            
            
            DC_nodes[var_name] = Node_DC(
                node_type,kV_base, Voltage_0, Power_Gained, Power_load ,name=str(var_name),Umin=Umin,Umax=Umax,x_coord=x_coord,y_coord=y_coord)
        DC_nodes_list = list(DC_nodes.values())

        # DC_line_data = DC_line_data.set_index('Line_id')
        DC_lines = {}
        for index, row in DC_line_data.iterrows():
           if DC_line_data.at[index, 'status'] !=0:    
            

            fromNode      = DC_line_data.at[index, 'fbusdc']
            toNode        = DC_line_data.at[index, 'tbusdc']

            

            Resistance    = DC_line_data.at[index, 'r']
            MW_rating     = DC_line_data.at[index, 'rateA']    
            kV_base       = DC_nodes[toNode].kV_base 
            
            var_name = f'L_DC_{index+1}'
            
            if dcpol == 2:
                pol = 'sm'
            else:
                pol = 'm'
            DC_lines[var_name] = Line_DC(DC_nodes[fromNode], DC_nodes[toNode], Resistance, MW_rating, polarity=pol, name=str(var_name),S_base=S_base)

            if DC_line_data.at[index, 'cost'] >= 0:
                DC_lines[var_name].np_line_opf = True
                DC_lines[var_name].np_line   = 0
                DC_lines[var_name].np_line_b = 0
                DC_lines[var_name].np_line_i = 0
                DC_lines[var_name].np_line_max = 3
                DC_lines[var_name].base_cost = DC_line_data.at[index, 'cost']

        DC_lines_list = list(DC_lines.values())

    if Converter_data is None:
        Convertor_list = None
    else:
        # Converter_data = Converter_data.set_index('Conv_id')
        "Convertor data sorting"
        Converters = {}
        for index, row in Converter_data.iterrows():
          if Converter_data.at[index, 'status'] !=0:   
            var_name  = f"Conv_{index+1}"
            
            type_ac = Converter_data.at[index, 'type_ac']   
            if type_ac == 1:
                AC_type = 'PQ'
            elif type_ac == 2:
                AC_type = 'PV'
          
            type_dc= Converter_data.at[index, 'type_dc']     
            if type_dc == 1:
                 DC_type = 'P'
            elif type_dc == 2:
                DC_type = 'Slack'
            elif type_dc == 3:
                DC_type = 'Droop'
             
            
                       
            DC_node         = Converter_data.at[index, 'busdc_i']   
            AC_node         = Converter_data.at[index, 'busac_i']            
            P_AC            = Converter_data.at[index, 'P_g']/S_base      
            Q_AC            = Converter_data.at[index, 'Q_g']/S_base         
            P_DC            = Converter_data.at[index, 'Pdcset']/S_base         
            Transformer_R   = Converter_data.at[index, 'rtf']          
            Transformer_X   = Converter_data.at[index, 'xtf']           
            Phase_Reactor_R = Converter_data.at[index, 'rc']           
            Phase_Reactor_X = Converter_data.at[index, 'xc']      
            Filter          = Converter_data.at[index, 'bf']      
            Droop           = Converter_data.at[index, 'droop']        
            kV_base         = Converter_data.at[index, 'basekVac']    
            
            P_max  = Converter_data.at[index, 'Pacmax']
            P_min  = Converter_data.at[index, 'Pacmin']
            Q_max  = Converter_data.at[index, 'Qacmax']
            Q_min  = Converter_data.at[index, 'Qacmin']
            
            maxP = max(abs(P_max),abs(P_min))
            maxQ = max(abs(Q_max),abs(Q_min))
            
            MVA_max         = max(maxP,maxQ)
            Ucmin           = Converter_data.at[index, 'Vmmin']        
            Ucmax           = Converter_data.at[index, 'Vmmax']        
            n               = 1
            pol             = 1
            
            LossA           = Converter_data.at[index, 'LossA']
            LossB           = Converter_data.at[index, 'LossB']
            LossCrec        = Converter_data.at[index, 'LossCrec']
            LossCinv        = Converter_data.at[index, 'LossCinv']
        
            Converters[var_name] = AC_DC_converter(AC_type, DC_type, AC_nodes[AC_node], DC_nodes[DC_node], P_AC, Q_AC, P_DC, Transformer_R, Transformer_X, Phase_Reactor_R, Phase_Reactor_X, Filter, Droop, kV_base, 
            MVA_max=MVA_max,nConvP=n,polarity=pol,Ucmin=Ucmin,Ucmax=Ucmax,lossa=LossA,lossb=LossB,losscrect=LossCrec ,losscinv=LossCinv ,name=str(var_name),S_base=S_base)

            if Converter_data.at[index, 'cost'] >= 0:
                Converters[var_name].NUmConvP_opf = True
                Converters[var_name].NumConvP   = 0
                Converters[var_name].NumConvP_b = 0
                Converters[var_name].NumConvP_i = 0
                Converters[var_name].NumConvP_max = 1
                Converters[var_name].base_cost = Converter_data.at[index, 'cost']
        Convertor_list = list(Converters.values())



    G = Grid(S_base, AC_nodes_list, AC_lines_list, nodes_DC=DC_nodes_list,
             lines_DC=DC_lines_list, Converters=Convertor_list)
    res = Results(G, decimals=3)
    
    if EXP_line_data is not None:
        
        for index, row in EXP_line_data.iterrows():  
              
            fromNode     = EXP_line_data.at[index, 'f_bus']
            toNode       = EXP_line_data.at[index, 't_bus']
            r   = EXP_line_data.at[index, 'br_r']
            x    = EXP_line_data.at[index, 'br_x']    
            g  = 0
            b  = EXP_line_data.at[index, 'br_b']  
            
            
            
            kV_base      = AC_nodes[toNode].kV_base 
            MVA_rating   = EXP_line_data.at[index, 'rate_a']
           
            var_name =  f'{AC_nodes[fromNode].name}_{AC_nodes[toNode].name}_{MVA_rating}'

            if EXP_line_data.at[index, 'tap']== 0:
                m=1
                shift=0
            else:
                m            = EXP_line_data.at[index, 'tap']  
                shift        = np.radians(EXP_line_data.at[index, 'shift'])

            km=1
            
            line = Exp_Line_AC(AC_nodes[fromNode], AC_nodes[toNode], r,
                                         x, g, b, MVA_rating,km,m,shift ,name=str(var_name),S_base=S_base)
    
            line.base_cost = EXP_line_data.at[index, 'construction_cost']  
            line.lineNumber = index
            line.np_line = 0
            line.np_line_b = 0
            line.np_line_i = 1
            line.np_line_max = 3
            G.lines_AC_exp.append(line)
        G.Update_Graph_AC()

    if Gen_data is not None:        
        for index, row in Gen_data.iterrows():
            
            var_name = index+1 
            node_name = str(Gen_data.at[index, 'bus'])
            
            MWmax  = Gen_data.at[index, 'Pmax']
            MWmin   = Gen_data.at[index, 'Pmin']
            MVArmin = Gen_data.at[index, 'Qmin']
            MVArmax = Gen_data.at[index, 'Qmax']
            
            
            
            
            PsetMW = Gen_data.at[index,'Pg']
            QsetMVA = Gen_data.at[index,'Qg']


            if first_model == 1:
                # Extract x/y pairs from the row
                n_points = int(Gen_data_cost.at[index, 'n'])
                x_vals = []
                y_vals = []
                for i in range(1, n_points + 1):
                    x_col = f'x{i}'
                    y_col = f'y{i}'
                    if x_col in Gen_data_cost.columns and y_col in Gen_data_cost.columns:
                        x_vals.append(Gen_data_cost.at[index, x_col])
                        y_vals.append(Gen_data_cost.at[index, y_col])
                # Fit quadratic: y = a*x^2 + b*x + c
                if len(x_vals) >= 3:
                    a, b, c = np.polyfit(x_vals, y_vals, 2)
                    qf = a
                    lf = b
                    cf = c
                elif len(x_vals) == 2:
                    b, c = np.polyfit(x_vals, y_vals, 1)
                    qf = 0
                    lf = b
                    cf = c
                else:
                    qf, lf, cf = 0, 0, 0
            else:
                qf = Gen_data_cost.at[index, 'c(n-1)']
                lf = Gen_data_cost.at[index, 'c(n-2)']   
                cf = Gen_data_cost.at[index, 'c0']
            
            price_zone_link = False
            
            if Gen_data.at[index, 'status'] == 0:
                np_gen = 0
            else:
                np_gen = 1

            gen = add_gen(G, node_name,var_name, price_zone_link,lf,qf,cf,MWmax,MWmin,MVArmin,MVArmax,PsetMW,QsetMVA) 
            gen.np_gen = np_gen
    
    return [G, res]


def Create_grid_from_pickle(path,use_dill=True):
    initialize_pyflowacdc()

    grid = load_pickle(path,use_dill)

    # Class-level cable databases are not persisted by pickle; reload them.
    Line_AC._cable_database = None
    Line_AC.load_cable_database()
    Cable_options._cable_database = None
    Cable_options.load_cable_database()
    Line_DC._cable_database = None
    Line_DC.load_cable_database()

    res = Results(grid, decimals=3)
    return [grid, res]

def load_pickle(path, use_dill=False):
    opener = gzip.open if path.endswith(".gz") else open
    # Try pickle first, fall back to dill if it fails (for files saved with dill)
    if not use_dill:
        try:
            with opener(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            if _dill is not None:
                with opener(path, "rb") as f:
                    return _dill.load(f)
            raise
    else:
        lib = _dill if _dill is not None else pickle
        with opener(path, "rb") as f:
            return lib.load(f)

def change_S_base(grid,Sbase_new):
    
    Sbase_old = grid.S_base
    rate = Sbase_old/Sbase_new
    for line in grid.lines_AC:
        line.S_base = Sbase_new
    for line in grid.lines_DC:
        line.S_base = Sbase_new
    for conv in grid.Converters:
        conv.S_base = Sbase_new
    for node in grid.nodes_AC:
        node.PGi *= rate 
        node.PLi *= rate 
        node.QGi *= rate 
        node.QLi *= rate 
    
    for gen in grid.Generators:
        gen.PGen *= rate
        gen.Pset *= rate
        gen.QGen *= rate
        gen.Qset *= rate
    grid.Update_PQ_AC()
    grid.create_Ybus_AC()
    grid.S_base=Sbase_new
    
    return grid


def create_sub_grid(grid,Area=None, Area_name = None,polygon_coords=None):
        
        ac_nodes_list=[]
        dc_nodes_list=[]
        opz=None
        if Area is not None:
            if isinstance(Area, list):
                for a in Area:
                    ac_nodes_list.extend(a.nodes_AC)
                    dc_nodes_list.extend(a.nodes_DC)
            else:   
                ac_nodes_list = Area.nodes_AC
                dc_nodes_list = Area.nodes_DC
        elif Area_name is not None:
            if isinstance(Area_name, list):
                for a_name in Area_name:
                    for Area in grid.Price_Zones:
                        if Area.name == a_name:
                            ac_nodes_list.extend(Area.nodes_AC)
                            dc_nodes_list.extend(Area.nodes_DC)
                    
                        if Area.name == f'o{a_name}':
                            ac_nodes_list.extend(Area.nodes_AC)
                            dc_nodes_list.extend(Area.nodes_DC)                    
            
            else:
                for Area in grid.Price_Zones:
                    if Area.name == Area_name:
                        ac_nodes_list.extend(Area.nodes_AC)
                        dc_nodes_list.extend(Area.nodes_DC)
                
                    if Area.name == f'o{Area_name}':
                        ac_nodes_list.extend(Area.nodes_AC)
                        dc_nodes_list.extend(Area.nodes_DC)
                    
                    
        elif polygon_coords is not None:
            polygon_shape = Polygon(polygon_coords)
            for node in grid.nodes_AC:
                node_point = Point(node.x_coord, node.y_coord)
                if polygon_shape.contains(node_point):
                    ac_nodes_list.append(node)
            for node in grid.nodes_DC:
                node_point = Point(node.x_coord, node.y_coord)
                if polygon_shape.contains(node_point):
                    dc_nodes_list.append(node)
            
            
        else:
            print("No area provided to create sub grid")
            return grid
        
        
        for node in ac_nodes_list:
            # Check for converters connected to the node
            if hasattr(node, 'connected_conv') and node.connected_conv:
                # Access the converter objects from grid.Converters_ACDC using the index
                for conv_index in node.connected_conv:
                    converter = grid.Converters_ACDC[conv_index]
                    dc_nodes_list.append(converter.Node_DC)
        
        ac_node_names = {node.name for node in ac_nodes_list}
        dc_node_names = {node.name for node in dc_nodes_list}
        
        G_AC_new = nx.MultiGraph()
        
        nodes_AC1 =[]
        
        # Iterate through the node list and combine ego graphs
        for node in ac_nodes_list:
            # Generate an ego graph for the current node
            Gn = nx.ego_graph(grid.Graph_AC, node, radius=1)
            
            # Combine the current ego graph with Gnew
            G_AC_new = nx.compose(G_AC_new, Gn)
        
            if node.stand_alone:
                nodes_AC1.append(node)
        
        
        G_DC_new = nx.Graph()

        # Iterate through the node list and combine ego graphs
        for node in dc_nodes_list:
            # Generate an ego graph for the current node
            Gn = nx.ego_graph(grid.Graph_DC, node, radius=1)
            
            # Combine the current ego graph with Gnew
            G_DC_new = nx.compose(G_DC_new, Gn)
        
        
        edge_list = list(G_AC_new.edges(data=True))
        

        # Extract the list of line objects from the edge list
        line_objects_AC = [data['line'] for _, _, data in edge_list if 'line' in data]
        
        line_objects_AC = copy.deepcopy(line_objects_AC)
    
        nodes_AC = copy.deepcopy(nodes_AC1)
        
        for line in line_objects_AC:
            nodes_AC.append(line.toNode)
            nodes_AC.append(line.fromNode)
        
        nodes_AC = list(set(nodes_AC))
        
        new_ac_node_names = {node.name for node in nodes_AC}
        new_only_names = new_ac_node_names - ac_node_names
        
        if polygon_coords is not None:
            ac_nodes_outside = {node for node in nodes_AC if node.name in new_only_names}
            lines_ac_outside=[]
            for line in line_objects_AC:
                if line.toNode in ac_nodes_outside or line.fromNode in ac_nodes_outside:
          
                    if line.toNode not in ac_nodes_outside:
                        node = line.toNode
                    elif line.fromNode not in ac_nodes_outside:
                        node =  line.fromNode
                    
                    Max_pow_gen= line.MVA_rating/grid.S_base
                    Min_pow_gen= 0
                    Min_pow_genR= -line.MVA_rating/grid.S_base
                    Max_pow_genR= line.MVA_rating/grid.S_base
                    gen = Gen_AC(line.name, node,Max_pow_gen,Min_pow_gen,Max_pow_genR,Min_pow_genR,S_rated=Max_pow_gen/grid.S_base)
                    
                    gen.price_zone_link=True
                    gen.lf= node.price
                    
                    node.PLi_base += line.MVA_rating/grid.S_base
                    node.update_PLi()
                    lines_ac_outside.append(line)
                        
            nodes_AC = [node for node in nodes_AC if node not in ac_nodes_outside]
            line_objects_AC = [line for line in line_objects_AC if line not in lines_ac_outside]
        
        
        
        lines_AC = []
        lines_AC_exp = []
        lines_AC_tf = []
        
        # Sort the lines into the appropriate lists
        for line in line_objects_AC:
            if "Line_AC" in str(type(line)):  # Check if it's a regular AC line
                lines_AC.append(line)
            elif "Exp_Line_AC" in str(type(line)):  # Check if it's an expanded AC line
                lines_AC_exp.append(line)
            elif "TF_Line_AC" in str(type(line)):  # Check if it's a transformer line (adjust type as needed)
                lines_AC_tf.append(line)
        
        
        
        edge_list_DC = list(G_DC_new.edges(data=True))
        # Extract the list of line objects from the edge list
        line_objects_DC = [data['line'] for _, _, data in edge_list_DC if 'line' in data]
        lines_DC  = copy.deepcopy(line_objects_DC)
        
        nodes_DC = []
        for line in lines_DC:
            nodes_DC.append(line.toNode)
            nodes_DC.append(line.fromNode)
        nodes_DC = list(set(nodes_DC))
       
        new_dc_node_names = {node.name for node in nodes_DC}
        new_dc_only_names = new_dc_node_names - dc_node_names
       
        
        REN_sources_list = []
        Gens_list = []
        Conv_list = []
        
        # Iterate through nodes in nodes_AC_new
        for node in nodes_AC:
            # Check for renewable sources connected to the node
            if hasattr(node, 'connected_RenSource') and node.RenSource:
                REN_sources_list.extend(node.connected_RenSource)  # Add connected REN sources
                 
            # Check for generators connected to the node
            if hasattr(node, 'connected_gen') and node.connected_gen:
                Gens_list.extend(node.connected_gen)  # Add connected generators
            
            # Check for converters connected to the node
            if hasattr(node, 'connected_conv') and node.connected_conv:
                # Access the converter objects from grid.Converters_ACDC using the index
                for conv_index in node.connected_conv:
                    converter = grid.Converters_ACDC[conv_index]
                    Conv_list.append(converter)  # Add connected converter object
                    

        Conv_list = list(set(Conv_list))
        
        
        Conv_list = copy.deepcopy(Conv_list)
        for conv in Conv_list:
            nc = conv.ConvNumber
            nAC = grid.Converters_ACDC[nc].Node_AC.nodeNumber
            nDC = grid.Converters_ACDC[nc].Node_DC.nodeNumber
            conv.Node_AC = next((node for node in nodes_AC if node.nodeNumber == nAC), None)
            conv.Node_DC = next((node for node in nodes_DC if node.nodeNumber == nDC), None)
        
        
        for node in nodes_DC:
            # Check for renewable sources connected to the node
            if hasattr(node, 'connected_RenSource') and node.connected_RenSource:
                REN_sources_list.extend(node.connected_RenSource)  # Add connected REN sources
            
        
        # Remove duplicates if necessary
        REN_sources_list = list(set(REN_sources_list))
        Gens_list = list(set(Gens_list))
        Conv_list = list(set(Conv_list))
        
        for node in nodes_AC:
            node.connected_conv = set() 
        
        
        for i, line in enumerate(lines_AC):
            line.lineNumber = i
        for i, line in enumerate(lines_AC_exp):
            line.lineNumber = i 
        for i, line in enumerate(lines_AC_tf):
            line.lineNumber = i     
        for i, line in enumerate(lines_DC):
            line.lineNumber = i 
        for i, node in enumerate(nodes_AC):
            node.nodeNumber = i 
        for i, node in enumerate(nodes_DC):
            node.nodeNumber = i
        for i, conv in enumerate(Conv_list):
            conv.ConvNumber = i 
            conv.Node_AC.connected_conv.add(i)
        for i, rs in enumerate(REN_sources_list):
            rs.rsNumber = i 
        for i, g in enumerate(Gens_list):
            g.genNumber = i 
        
        
        sub_grid = Grid(grid.S_base, nodes_AC, lines_AC, nodes_DC=nodes_DC,
                 lines_DC=lines_DC, Converters=Conv_list)
        res = Results(sub_grid, decimals=3)
         
    
        pz_names = {node.PZ for node in nodes_AC} | {node.PZ for node in nodes_DC} 
        copy_PZ = copy.deepcopy(grid.Price_Zones)
        copy_PZ = [pz for pz in copy_PZ if pz.name in pz_names]
    
        
        for i, pz in enumerate(copy_PZ):
            pz.price_zone_num = i 
            pz.nodes_AC = []
            pz.nodes_DC = []
        sub_grid.Price_Zones=copy_PZ
        
        pz_dict = {}
        for pz in copy_PZ:
            for node in nodes_AC:
                if node.PZ == pz.name:
                    sub_grid.Price_Zones[pz.price_zone_num].nodes_AC.append(node)
            for node in nodes_DC:
                if node.PZ == pz.name:
                    sub_grid.Price_Zones[pz.price_zone_num].nodes_DC.append(node)
            
            # Add the PZ to the dictionary with price_zone_num
            pz_dict[pz.name] = pz.price_zone_num
       
        sub_grid.Price_Zones_dic= pz_dict
             
        rz_names = {rs.Ren_source_zone for rs in REN_sources_list} 
        copy_RZ = copy.deepcopy(grid.RenSource_zones)
        copy_RZ = [rz for rz in copy_RZ if rz.name in rz_names]
    
        for i, rz in enumerate(copy_RZ):
            rz.ren_source_num = i 
            rz.RenSources = []
           
        sub_grid.RenSource_zones=copy_RZ
        
        rz_dict = {}
        for rz in copy_RZ:
            for rs in REN_sources_list:
                if rs.Ren_source_zone == pz.name:
                    sub_grid.RenSource_zones[rs.ren_source_num].RenSources.append(rs)
            
            # Add the PZ to the dictionary with price_zone_num
            rz_dict[rz.name] = rz.ren_source_num
       
        sub_grid.RenSources_zones_dic= rz_dict
        
        
        
        sub_grid.RenSources = REN_sources_list
        sub_grid.Generators = Gens_list
        return [sub_grid, res]
    
    