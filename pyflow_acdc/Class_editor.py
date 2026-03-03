"""
Created on Fri Dec 15 15:24:42 2023

@author: BernardoCastro
"""

import pandas as pd
import numpy as np
import sys
import yaml
import re
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from shapely.wkt import loads

from .Classes import*
from .Results_class import*

from pathlib import Path    
    
"""
"""

__all__ = [
    # Add grid Elements
    'add_AC_node',
    'add_DC_node',
    'add_line_AC',
    'add_line_DC',
    'add_ACDC_converter',
    'add_DCDC_converter',
    'add_gen',
    'add_gen_DC',
    'add_extgrid',
    'add_RenSource',
    'add_generators',
    'add_cable_option',
    'add_line_sizing',
    
    # Add Zones
    'add_RenSource_zone',
    'add_price_zone',
    'add_MTDC_price_zone',
    'add_offshore_price_zone',
    
    # Add Time Series
    'add_TimeSeries',
    
    #Add investment series
    'add_inv_series',
    'add_gen_mix_limits',
    'create_gen_limit_csv_template',
    'create_inv_csv_template',
    
    # Line Modifications
    'change_line_AC_to_expandable',
    'change_line_AC_to_reconducting',
    'change_line_AC_to_tap_transformer',
    
    # Zone Assignments
    'assign_RenToZone',
    'assign_nodeToPrice_Zone',
    'assign_ConvToPrice_Zone',
    'assign_lineToCable_options',
    
    # Parameter Calculations
    'Cable_parameters',
    'Converter_parameters',
    
    # Utility Functions
    'pol2cart',
    'cart2pol',
    'pol2cartz',
    'cartz2pol',

    # Analysis
    'analyse_grid',
    'grid_state',
    'import_orbit_cables',
    'current_fuel_type_distribution'
]

def pol2cart(r, theta):
    x = r*np.cos(theta)
    y = r*np.sin(theta)
    return x, y


def pol2cartz(r, theta):
    x = r*np.cos(theta)
    y = r*np.sin(theta)
    z = x+1j*y
    return z


def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return rho, theta


def cartz2pol(z):
    r = np.abs(z)
    theta = np.angle(z)
    return r, theta



def Converter_parameters(S_base, kV_base, T_R_Ohm, T_X_mH, PR_R_Ohm, PR_X_mH, Filter_uF, f=50):

    Z_base = kV_base**2/S_base  # kv^2/MVA
    Y_base = 1/Z_base

    F = Filter_uF*10**(-6)
    PR_X_H = PR_X_mH/1000
    T_X_H = T_X_mH/1000

    B    = 2*f*F*np.pi
    T_X  = 2*f*T_X_H*np.pi
    PR_X = 2*f*PR_X_H*np.pi

    T_R_pu = T_R_Ohm/Z_base
    T_X_pu = T_X/Z_base
    PR_R_pu = PR_R_Ohm/Z_base
    PR_X_pu = PR_X/Z_base
    Filter_pu = B/Y_base

    return [T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu]


def Cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km, N_cables=1, f=50):

    Z_base = kV_base**2/S_base  # kv^2/MVA
    Y_base = 1/Z_base

    if L_mH == 0:
        N_cables = 1
        MVA_rating = N_cables*A_rating*kV_base/(1000)
        #IN DC N cables is always 1 as the varible is used directly in the formulation
    else:
        MVA_rating = N_cables*A_rating*kV_base*np.sqrt(3)/(1000)

    C = C_uF*(10**(-6))
    L = L_mH/1000
    G = G_uS*(10**(-6))

    R_AC = R*km

    B = 2*f*C*np.pi*km
    X = 2*f*L*np.pi*km

    Z = R_AC+X*1j
    Y = G+B*1j

    # Zc=np.sqrt(Z/Y)
    # theta_Z=np.sqrt(Z*Y)

    Z_pi = Z
    Y_pi = Y

    # Z_pi=Zc*np.sinh(theta_Z)
    # Y_pi = 2*np.tanh(theta_Z/2)/Zc

    R_1 = np.real(Z_pi)
    X_1 = np.imag(Z_pi)
    G_1 = np.real(Y_pi)
    B_1 = np.imag(Y_pi)

    Req = R_1/N_cables
    Xeq = X_1/N_cables
    Geq = G_1*N_cables
    Beq = B_1*N_cables

    Rpu = Req/Z_base
    Xpu = Xeq/Z_base
    Gpu = Geq/Y_base
    Bpu = Beq/Y_base

    return [Rpu, Xpu, Gpu, Bpu, MVA_rating]

"Add main components"

def add_AC_node(grid, kV_base,node_type='PQ',Voltage_0=1.01, theta_0=0.01, Power_Gained=0, Reactive_Gained=0, Power_load=0, Reactive_load=0, name=None, Umin=0.9, Umax=1.1,Gs= 0,Bs=0,x_coord=None,y_coord=None,geometry=None):
    node = Node_AC( node_type, Voltage_0, theta_0,kV_base, Power_Gained, Reactive_Gained, Power_load, Reactive_load, name, Umin, Umax,Gs,Bs,x_coord,y_coord)
    if geometry is not None:
       if isinstance(geometry, str): 
            geometry = loads(geometry)  
       node.geometry = geometry
       node.x_coord = geometry.x
       node.y_coord = geometry.y
    
    grid.nodes_AC.append(node)
    
    return node

def add_DC_node(grid,kV_base,node_type='P', Voltage_0=1.01, Power_Gained=0, Power_load=0, name=None,Umin=0.95, Umax=1.05,x_coord=None,y_coord=None,geometry=None):  
    node = Node_DC(node_type, kV_base, Voltage_0, Power_Gained, Power_load, name,Umin, Umax,x_coord,y_coord)
    grid.nodes_DC.append(node)
    if geometry is not None:
       if isinstance(geometry, str): 
            geometry = loads(geometry)  
       node.geometry = geometry
       node.x_coord = geometry.x
       node.y_coord = geometry.y
       
       
    return node
    
def add_line_AC(grid, fromNode, toNode,MVA_rating=None, r=0, x=0, b=0, g=0,R_Ohm_km=None,L_mH_km=None, C_uF_km=0, G_uS_km=0, A_rating=None ,m=1, shift=0, name=None,tap_changer=False,Expandable=False,N_cables=1,Length_km=1,geometry=None,data_in='pu',Cable_type:str ='Custom',update_grid=True):
    
    if isinstance(fromNode, str):
        fromNode = next((node for node in grid.nodes_AC if node.name == fromNode), None)
    if isinstance(toNode, str):
        toNode = next((node for node in grid.nodes_AC if node.name == toNode), None)
    
    kV_base=toNode.kV_base
    if L_mH_km is not None:
        data_in = 'Real'
    if data_in == 'Ohm':
        Z_base = kV_base**2/grid.S_base
        
        Resistance_pu = r / Z_base if r!=0 else 0.00001
        Reactance_pu  = x  / Z_base if x!=0  else 0.00001
        Conductance_pu = g*Z_base
        Susceptance_pu = b*Z_base
    elif data_in== 'Real' and Cable_type == 'Custom': 
       [Resistance_pu, Reactance_pu, Conductance_pu, Susceptance_pu, MVA_rating] = Cable_parameters(grid.S_base, R_Ohm_km, L_mH_km, C_uF_km, G_uS_km, A_rating, kV_base, Length_km,N_cables=N_cables)
    else:
        Resistance_pu = r if r!=0 else 0.00001
        Reactance_pu  = x if x!=0  else 0.00001
        Conductance_pu = g
        Susceptance_pu = b
    
    
    if tap_changer:
        line = TF_Line_AC(fromNode, toNode, Resistance_pu,Reactance_pu, Conductance_pu, Susceptance_pu, MVA_rating, kV_base,m, shift, name)
        grid.lines_AC_tf.append(line)
        if update_grid:
            grid.Update_Graph_AC()
    elif Expandable:
        line = Exp_Line_AC(fromNode, toNode, Resistance_pu,Reactance_pu, Conductance_pu, Susceptance_pu, MVA_rating,Length_km,m, shift,N_cables, name,S_base=grid.S_base,Cable_type=Cable_type)
        grid.lines_AC_exp.append(line)
        if update_grid:
            grid.Update_Graph_AC()
        
    else:    
        line = Line_AC(fromNode, toNode, Resistance_pu,Reactance_pu, Conductance_pu, Susceptance_pu, MVA_rating,Length_km,m, shift,N_cables, name,S_base=grid.S_base,Cable_type=Cable_type)
        
        grid.lines_AC.append(line)
        if update_grid: 
            grid.create_Ybus_AC()
            grid.Update_Graph_AC()
        
    if geometry is not None:
       if isinstance(geometry, str): 
            geometry = loads(geometry)  
       line.geometry = geometry
    
    return line

def change_line_AC_to_expandable(grid, line_name,update_grid=True):
    l = None
    for line_to_process in grid.lines_AC:
        if line_name == line_to_process.name:
            l = line_to_process
            break
            
    if l is not None:    
        grid.lines_AC.remove(l)
        l.remove()
        line_vars = {
            'fromNode': l.fromNode,
            'toNode': l.toNode,
            'r': l.R,
            'x': l.X,
            'g': l.G,
            'b': l.B,
            'MVA_rating': l.MVA_rating,
            'Length_km': l.Length_km,
            'm': l.m,
            'shift': l.shift,
            'N_cables': l.N_cables,
            'name': l.name,
            'geometry': l.geometry,
            'S_base': l.S_base,
            'Cable_type': l.Cable_type
        }
        expandable_line = Exp_Line_AC(**line_vars)
        grid.lines_AC_exp.append(expandable_line)
        if update_grid:
            grid.Update_Graph_AC()

    # Reassign line numbers to ensure continuity
    for i, line in enumerate(grid.lines_AC):
        line.lineNumber = i 
    
    for i, line in enumerate(grid.lines_AC_exp):
        line.lineNumber = i 
    if update_grid:
        grid.create_Ybus_AC()
    return expandable_line    

def change_line_AC_to_reconducting(grid, line_name, r_new,x_new,g_new,b_new,MVA_rating_new,Life_time,base_cost,update_grid=True):
    l = None
    for line_to_process in grid.lines_AC:
        if line_name == line_to_process.name:
            l = line_to_process
            break
            
    if l is not None:    
        grid.lines_AC.remove(l)
        l.remove()
        line_vars = {
            'fromNode': l.fromNode,
            'toNode': l.toNode,
            'r': l.R,
            'x': l.X,
            'g': l.G,
            'b': l.B,
            'MVA_rating': l.MVA_rating,
            'Length_km': l.Length_km,
            'm': l.m,
            'shift': l.shift,
            'N_cables': l.N_cables,
            'name': l.name,
            'geometry': l.geometry,
            'S_base': l.S_base,
            'Cable_type': l.Cable_type
        }
        rec_line = rec_Line_AC(r_new,x_new,g_new,b_new,MVA_rating_new,Life_time,base_cost,**line_vars)
        grid.lines_AC_rec.append(rec_line)
        if update_grid:
            grid.Update_Graph_AC()

    # Reassign line numbers to ensure continuity
    for i, line in enumerate(grid.lines_AC):
        line.lineNumber = i 
    
    for i, line in enumerate(grid.lines_AC_rec):
        line.lineNumber = i 
    if update_grid:
        grid.create_Ybus_AC()    
    return rec_line  

def change_line_AC_to_tap_transformer(grid, line_name):
    l = None
    for line_to_process in grid.lines_AC:
        if line_name == line_to_process.name:
            l  = line_to_process
            break
    if l is not None:    
            grid.lines_AC.remove(l)
            l.remove()
            line_vars=line_vars = {
            'fromNode': l.fromNode,
            'toNode': l.toNode,
            'Resistance': l.R,
            'Reactance': l.X,
            'Conductance': l.G,
            'Susceptance': l.B,
            'MVA_rating': l.MVA_rating,
            'Length_km': l.Length_km,
            'm': l.m,
            'shift': l.shift,
            'N_cables': l.N_cables,
            'name': l.name,
            'geometry': l.geometry,
            'S_base': l.S_base,
            'Cable_type': l.Cable_type
        }
            trafo = TF_Line_AC(**line_vars)
            grid.lines_AC_tf.append(trafo)
    else:
        print(f"Line {line_name} not found.")
        return
    # Reassign line numbers to ensure continuity in grid.lines_AC
    for i, line in enumerate(grid.lines_AC):
        line.lineNumber = i 
    grid.create_Ybus_AC()
    s=1    

def add_line_sizing(grid, fromNode, toNode,cable_types: list=[], active_config: int = 0,Length_km=1.0,S_base=100,name=None,cable_option=None,update_grid=True,geometry=None):       
    if isinstance(fromNode, str):
        fromNode = next((node for node in grid.nodes_AC if node.name == fromNode), None)
    if isinstance(toNode, str):
        toNode = next((node for node in grid.nodes_AC if node.name == toNode), None)
    
    line = Size_selection(fromNode, toNode,cable_types, active_config,Length_km,S_base,name)
    grid.lines_AC_ct.append(line)
    if cable_option is not None:
        assign_lineToCable_options(grid,line.name,cable_option)
    if update_grid:
        grid.create_Ybus_AC()
        grid.Update_Graph_AC() 
    if geometry is not None:
       if isinstance(geometry, str): 
            geometry = loads(geometry)  
       line.geometry = geometry
    return line

def add_line_DC(grid, fromNode, toNode, r=0.001, MW_rating=9999,Length_km=1,R_Ohm_km=None,A_rating=None,polarity='m', name=None,geometry=None,Cable_type:str ='Custom',data_in='pu',update_grid=True):
    
    if isinstance(fromNode, str):
        fromNode = next((node for node in grid.nodes_DC if node.name == fromNode), None)
    if isinstance(toNode, str):
        toNode = next((node for node in grid.nodes_DC if node.name == toNode), None)
    
    kV_base=toNode.kV_base
    if data_in == 'Ohm':
        Z_base = kV_base**2/grid.S_base
        
        Resistance_pu = r / Z_base if r!=0 else 0.00001

    elif data_in== 'Real' or R_Ohm_km is not None: 
        if A_rating is None:
            A_rating = MW_rating*1000/kV_base     
        [Resistance_pu, _, _, _, MW_rating] = Cable_parameters(grid.S_base, R_Ohm_km, 0, 0, 0, A_rating, kV_base, Length_km,N_cables=1)
    else:
        Resistance_pu = r if r!=0 else 0.00001
      
    if isinstance(polarity, int):
        if polarity == 1:
            polarity = 'm'
        elif polarity == 2:
            polarity = 'b'
        else:
            print(f"Invalid polarity value: {polarity}")
            return
    line = Line_DC(fromNode, toNode, Resistance_pu, MW_rating,Length_km, polarity, name,Cable_type=Cable_type)
    grid.lines_DC.append(line)
    
    if geometry is not None:
       if isinstance(geometry, str): 
            geometry = loads(geometry)  
       line.geometry = geometry
    if update_grid:
        grid.create_Ybus_DC()
        grid.Update_Graph_DC()
    return line

def add_ACDC_converter(grid,AC_node , DC_node , AC_type='PV', DC_type=None, P_AC_MW=0, Q_AC_MVA=0, P_DC_MW=0, Transformer_resistance=0, Transformer_reactance=0, Phase_Reactor_R=0, Phase_Reactor_X=0, Filter=0, Droop=0, kV_base=None, MVA_max= None,nConvP=1,polarity =1 ,lossa=1.103,lossb= 0.887,losscrect=2.885,losscinv=4.371,Arm_R=None,Ucmin= 0.85, Ucmax= 1.2, name=None,geometry=None):
    if isinstance(DC_node, str):
        DC_node = next((node for node in grid.nodes_DC if node.name == DC_node), None)
    if isinstance(AC_node, str):
        AC_node = next((node for node in grid.nodes_AC if node.name == AC_node), None)
    
    
    
    
    if MVA_max is None:
        MVA_max= grid.S_base*100
    if kV_base is None:
        kV_base = AC_node.kV_base
    if DC_type is None:
        DC_type = DC_node.type
        
    P_DC = P_DC_MW/grid.S_base
    P_AC = P_AC_MW/grid.S_base
    Q_AC = Q_AC_MVA/grid.S_base
    # if Filter !=0 and Phase_Reactor_R==0 and  Phase_Reactor_X!=0:
    #     print(f'Please fill out phase reactor values, converter {name} not added')
    #     return
    if Arm_R is not None:
        ra  = Arm_R*conv.basekA_DC**2/grid.S_base
    else:
        ra = 0.001

    conv = AC_DC_converter(AC_type, DC_type, AC_node, DC_node, P_AC, Q_AC, P_DC, Transformer_resistance, Transformer_reactance, Phase_Reactor_R, Phase_Reactor_X, Filter, Droop, kV_base, MVA_max,nConvP,polarity ,lossa,lossb,losscrect,losscinv,Ucmin, Ucmax, ra, grid.S_base, name)
    if geometry is not None:
        if isinstance(geometry, str): 
             geometry = loads(geometry)  
        conv.geometry = geometry    
   
    conv.basekA  = grid.S_base/(np.sqrt(3)*conv.AC_kV_base)
    conv.basekA_DC = grid.S_base/(conv.DC_kV_base)
    conv.a_conv  = conv.a_conv_og/grid.S_base
    conv.b_conv  = conv.b_conv_og*conv.basekA/grid.S_base
    conv.c_inver = conv.c_inver_og*conv.basekA**2/grid.S_base
    conv.c_rect  = conv.c_rect_og*conv.basekA**2/grid.S_base     
    
    
    
    
    grid.Converters_ACDC.append(conv)
    return conv

def add_DCDC_converter(grid,fromNode , toNode ,P_MW=None,Pset=None,R_Ohm=None, r=0.0001, MW_rating=99999,name=None,geometry=None):
    if isinstance(fromNode, str):
        fromNode = next((node for node in grid.nodes_DC if node.name == fromNode), None)
    if isinstance(toNode, str):
        toNode = next((node for node in grid.nodes_DC if node.name == toNode), None)
    
    if R_Ohm is not None:
        Z_base = toNode.kV_base**2/grid.S_base
        r = R_Ohm/Z_base
    if P_MW is not None:
        Pset = P_MW/grid.S_base
    if Pset is None:
        Pset = MW_rating/(2*grid.S_base)
    
    conv = DCDC_converter(fromNode , toNode , Pset, r, MW_rating,name,geometry)
    grid.Converters_DCDC.append(conv)
    return conv

"Zones"

def add_cable_option(grid, cable_types: list = None, name=None, cable_database=None):
    """Add cable option to grid.
    
    Parameters
    ----------
    grid : grid
        The grid object
    cable_types : list, optional
        List of cable type names. If None, creates empty cable option.
    name : str, optional
        Name for the cable option
    cable_database : pd.DataFrame, optional
        Custom cable database DataFrame. If provided, uses this instead of loading from YAML.
        If None and cable_type_ini == "pyflow_acdc", loads from YAML database.
    """
    cable_option = Cable_options(cable_types, name, cable_database=cable_database)
    grid.Cable_options.append(cable_option)
    return cable_option


def add_RenSource_zone(grid,name):
        
    RSZ = Ren_source_zone(name)
    grid.RenSource_zones.append(RSZ)
    grid.RenSource_zones_dic[name]=RSZ.ren_source_num
    
    return RSZ


def add_price_zone(grid,name,price,import_pu_L=1,export_pu_G=1,a=0,b=1,c=0,import_expand_pu=0,elasticity=1):

    if b==1:
        b= price
    
    M = Price_Zone(price,import_pu_L,export_pu_G,a,b,c,import_expand_pu,elasticity,grid.S_base,name)
    grid.Price_Zones.append(M)
    grid.Price_Zones_dic[name]=M.price_zone_num
    
    return M

def add_MTDC_price_zone(grid, name,  linked_price_zones=None,pricing_strategy='avg'):
    # Initialize the MTDC price_zone and link it to the given price_zones
    mtdc_price_zone = MTDCPrice_Zone(name=name, linked_price_zones=linked_price_zones, pricing_strategy=pricing_strategy)
    grid.Price_Zones.append(mtdc_price_zone)
    
    return mtdc_price_zone


def add_offshore_price_zone(grid,main_price_zone,name):
    if isinstance(main_price_zone, str):
        main_price_zone = next((M for M in grid.Price_Zones if main_price_zone == M.name), None)

    oprice_zone = OffshorePrice_Zone(name=name, price=main_price_zone.price, main_price_zone=main_price_zone)
    grid.Price_Zones.append(oprice_zone)
    
    return oprice_zone

"Components for optimal power flow"

def add_generators(grid,Gen_csv,curtailmet_allowed=1):
    if isinstance(Gen_csv, pd.DataFrame):
        Gen_data = Gen_csv
    else:
        Gen_data = pd.read_csv(Gen_csv)
    if 'Gen' in Gen_data.columns:
        Gen_data = Gen_data.set_index('Gen')
    
    
    for index, row in Gen_data.iterrows():
        var_name = Gen_data.at[index, 'Gen_name'] if 'Gen_name' in Gen_data.columns else index
        if 'Node' in Gen_data.columns:
            node_name = str(Gen_data.at[index, 'Node'])
        elif 'node' in Gen_data.columns:
            node_name = str(Gen_data.at[index, 'node'])
        else:
            raise ValueError(f"No 'Node' or 'node' column found in Gen_data for index {index}")
        
        MWmax = Gen_data.at[index, 'MWmax'] if 'MWmax' in Gen_data.columns else None
        MWmin = Gen_data.at[index, 'MWmin'] if 'MWmin' in Gen_data.columns else 0
        MVArmin = Gen_data.at[index, 'MVARmin'] if 'MVARmin' in Gen_data.columns else None
        MVArmax = Gen_data.at[index, 'MVARmax'] if 'MVARmax' in Gen_data.columns else None
        
        PsetMW = Gen_data.at[index, 'PsetMW']  if 'PsetMW'  in Gen_data.columns else 0
        QsetMVA= Gen_data.at[index, 'QsetMVA'] if 'QsetMVA' in Gen_data.columns else 0
        lf = Gen_data.at[index, 'Linear factor']    if 'Linear factor' in Gen_data.columns else 0
        qf = Gen_data.at[index, 'Quadratic factor'] if 'Quadratic factor' in Gen_data.columns else 0
        fc = Gen_data.at[index, 'Fixed cost'] if 'Fixed cost' in Gen_data.columns else 0
        geo  = Gen_data.at[index, 'geometry'] if 'geometry' in Gen_data.columns else None
        Ren_zone = Gen_data.at[index, 'Ren_zone'] if 'Ren_zone' in Gen_data.columns else None
        price_zone_link = False
        
        fuel_type = Gen_data.at[index, 'Fueltype']    if 'Fueltype' in Gen_data.columns else 'Other'
        if fuel_type.lower() in grid.renewable_types:
            add_RenSource(grid,node_name, MWmax,ren_source_name=var_name ,geometry=geo,ren_type=fuel_type,Qmin=MVArmin,Qmax=MVArmax,min_gamma=(1-curtailmet_allowed),zone=Ren_zone)
        else:
            if MVArmax is None:
                MVArmax = 9999
            if MVArmin is None:
                MVArmin = -9999
            add_gen(grid, node_name,var_name, price_zone_link,lf,qf,fc,MWmax,MWmin,MVArmin,MVArmax,PsetMW,QsetMVA,fuel_type=fuel_type,geometry=geo)  
        
def add_gen(grid, node_name,gen_name=None, price_zone_link=False,lf=0,qf=0,fc=0,MWmax=99999,MWmin=0,MVArmin=None,MVArmax=None,PsetMW=0,QsetMVA=0,Smax=None,fuel_type='Other',geometry= None,installation_cost:float=0,np_gen:int=1):
    
    if MVArmax is None:
        MVArmax=MWmax
    if MVArmin is None:
        MVArmin=-MVArmax
    if Smax is not None:
        Smax/=grid.S_base
    Max_pow_gen=MWmax/grid.S_base
 
    Max_pow_genR=MVArmax/grid.S_base
    Min_pow_genR=MVArmin/grid.S_base
    Min_pow_gen=MWmin/grid.S_base
    Pset=PsetMW/grid.S_base
    Qset=QsetMVA/grid.S_base
    found=False    
    for node in grid.nodes_AC:
   
        if node_name == node.name:
             gen = Gen_AC(
                 gen_name, node, Max_pow_gen, Min_pow_gen, Max_pow_genR, Min_pow_genR,
                 qf, lf, fc, Pset, Qset, Smax,
                 gen_type=fuel_type, installation_cost=installation_cost, S_base=grid.S_base
             )
             node.PGi = 0
             node.QGi = 0
             available_types = getattr(grid, 'gen_ac_types', ['other'])
             gen_type_lookup = {str(t).lower(): str(t) for t in available_types}
             normalized_fuel = str(fuel_type).lower()
             if normalized_fuel == 'gas':
                 normalized_fuel = 'natural gas'
             gen.gen_type = gen_type_lookup.get(normalized_fuel, gen_type_lookup.get('other', 'other'))
             gen.np_gen = np_gen
             if geometry is not None:
                 if isinstance(geometry, str): 
                      geometry = loads(geometry)  
                 gen.geometry= geometry
             found = True
             break

    if not found:
            print('Node does not exist')
            sys.exit()
    gen.price_zone_link=price_zone_link
    
    if price_zone_link:
        
        gen.qf= 0
        gen.lf= node.price
    grid.Generators.append(gen)
    
    return gen
            
def add_gen_DC(grid, node_name,gen_name=None, price_zone_link=False,lf=0,qf=0,fc=0,MWmax=99999,MWmin=0,PsetMW=0,fuel_type='Other',geometry= None,installation_cost:float=0,np_gen:int=1):
    
    Max_pow_gen=MWmax/grid.S_base
    Min_pow_gen=MWmin/grid.S_base
    Pset=PsetMW/grid.S_base
    
    found=False    
    for node in grid.nodes_DC:
   
        if node_name == node.name:
             gen = Gen_DC(
                 gen_name, node, Max_pow_gen, Min_pow_gen, qf, lf, fc, Pset,
                 gen_type=fuel_type, installation_cost=installation_cost, S_base=grid.S_base
             )
             node.PGi = 0
             available_types = getattr(grid, 'gen_dc_types', ['other'])
             gen_type_lookup = {str(t).lower(): str(t) for t in available_types}
             normalized_fuel = str(fuel_type).lower()
             if normalized_fuel == 'gas':
                 normalized_fuel = 'natural gas'
             gen.gen_type = gen_type_lookup.get(normalized_fuel, gen_type_lookup.get('other', 'other'))
             gen.np_gen = np_gen
             if geometry is not None:
                 if isinstance(geometry, str): 
                      geometry = loads(geometry)  
                 gen.geometry= geometry
             found = True
             break

    if not found:
            print('Node does not exist')
            sys.exit()
    gen.price_zone_link=price_zone_link
    
    if price_zone_link:
        
        gen.qf= 0
        gen.lf= node.price
    grid.Generators_DC.append(gen)
    
    return gen


def add_extgrid(grid, node, gen_name=None,price_zone_link=False,lf=0,qf=0,MVAmax=99999,MWmax=None,MVArmin=None,MVArmax=None,Allow_sell=True):
    if isinstance(node, str):
        node_name = node
        # Search in AC nodes first, then DC nodes
        node = next((n for n in grid.nodes_AC if n.name == node_name), None)
        
        if node is None:
            print(f'Node {node_name} does not exist')
            sys.exit()
    if MWmax is None:
        MWmax=MVAmax

    if MVArmin is None:
        MVArmin=-MVAmax
    if MVArmax is None:
        MVArmax=MVAmax
    
    Max_pow_gen=MWmax/grid.S_base
 
    Max_pow_genR=MVArmax/grid.S_base
    Min_pow_genR=MVArmin/grid.S_base
    if Allow_sell:
        Min_pow_gen=-MVAmax/grid.S_base
    else:
        Min_pow_gen=0
    rating = MVAmax/ grid.S_base
    gen = Gen_AC(gen_name, node,Max_pow_gen,Min_pow_gen,Max_pow_genR,Min_pow_genR,qf,lf,S_rated=rating)
    node.PGi = 0
    node.QGi = 0
    
    gen.price_zone_link=price_zone_link
    if price_zone_link:
        gen.qf= 0
        gen.lf= node.price

    # Iterate over all AC nodes to see if any is already 'Slack'
    has_slack = any(n.type == 'Slack' for n in grid.nodes_AC)
    if not has_slack:
        node.type = 'Slack'
    grid.Generators.append(gen)

def add_RenSource(grid, node, base_MW, ren_source_name=None, available=1, zone=None, price_zone=None, Offshore=False, MTDC=None, geometry=None, ren_type='Wind', min_gamma=0, Qrel=0,Qmin=None,Qmax=None):
    
    # Handle string input by finding the node
    if isinstance(node, str):
        node_name = node
        # Search in AC nodes first, then DC nodes
        node = next((n for n in grid.nodes_AC if n.name == node_name), None)
        if node is None:
            node = next((n for n in grid.nodes_DC if n.name == node_name), None)
        if node is None:
            print(f'Node {node_name} does not exist')
            sys.exit()
    
    # Set default ren_source_name if not provided
    if ren_source_name is None:
        ren_source_name = node.name
    
    # Create renewable source
    rensource = Ren_Source(ren_source_name, node, base_MW/grid.S_base,S_base=grid.S_base)    
    rensource.PRGi_available = available
    rensource.rs_type = ren_type
    rensource.min_gamma = min_gamma
    
    # Determine connection type and set appropriate attributes
    if node in grid.nodes_AC:
        rensource.connected = 'AC'
        ACDC = 'AC'
        if Qmax is not None:
            rensource.Qmax = Qmax/grid.S_base
        else:
            rensource.Qmax = base_MW*Qrel/grid.S_base
        if Qmin is not None:    
            rensource.Qmin = Qmin/grid.S_base
        else:
            rensource.Qmin = -base_MW*Qrel/grid.S_base
        grid.rs2node['AC'][rensource.rsNumber] = node.nodeNumber
    elif node in grid.nodes_DC:
        rensource.connected = 'DC'
        ACDC = 'DC'
        grid.rs2node['DC'][rensource.rsNumber] = node.nodeNumber
    else:
        print(f'Node {node.name} is not in AC or DC nodes')
        sys.exit()
    
    # Handle geometry
    if geometry is not None:
        if isinstance(geometry, str): 
            geometry = loads(geometry)  
        rensource.geometry = geometry
    
    # Add to grid
    grid.RenSources.append(rensource)
    
    # Handle zone assignment
    if zone is not None:
        rensource.zone = zone
        assign_RenToZone(grid, ren_source_name, zone)
    
    # Handle price zone assignment
    if price_zone is not None:
        rensource.price_zone = price_zone
        if MTDC is not None:
            rensource.MTDC = MTDC
            main_price_zone = next((M for M in grid.Price_Zones if price_zone == M.name), None)
            if main_price_zone is not None:
                # Find or create the MTDC price_zone
                MTDC_price_zone = next((mdc for mdc in grid.Price_Zones if MTDC == mdc.name), None)

                if MTDC_price_zone is None:
                    # Create the MTDC price_zone using the MTDCPrice_Zone class
                    MTDC_price_zone = add_MTDC_price_zone(grid, MTDC)
            
            MTDC_price_zone.add_linked_price_zone(main_price_zone)
            main_price_zone.import_expand += base_MW / grid.S_base
            assign_nodeToPrice_Zone(grid, node_name,MTDC, ACDC)
            # Additional logic for MTDC can be placed here
        elif Offshore:
            rensource.Offshore = True
            # Create an offshore price_zone by appending 'o' to the main price_zone's name
            oprice_zone_name = f'o_{price_zone}'

            # Find the main price_zone
            main_price_zone = next((M for M in grid.Price_Zones if price_zone == M.name), None)
            
            if main_price_zone is not None:
                # Find or create the offshore price_zone
                oprice_zone = next((m for m in grid.Price_Zones if m.name == oprice_zone_name), None)

                if oprice_zone is None:
                    # Create the offshore price_zone using the OffshorePrice_Zone class
                    oprice_zone = add_offshore_price_zone(grid, main_price_zone, oprice_zone_name)

                # Assign the node to the offshore price_zone
                assign_nodeToPrice_Zone(grid, node.name, oprice_zone_name, ACDC)
                # Link the offshore price_zone to the main price_zone
                main_price_zone.link_price_zone(oprice_zone)
                # Expand the import capacity in the main price_zone
                main_price_zone.import_expand += base_MW / grid.S_base
        else:
            # Assign the node to the main price_zone
            assign_nodeToPrice_Zone(grid, node.name, price_zone, ACDC)
    
    return rensource

"Time series data "


def time_series_dict(grid, ts):
    typ = ts.type
    
    if typ == 'a_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break
    elif typ == 'b_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break
    elif typ == 'c_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break
    elif typ == 'PGL_min':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break
    elif typ == 'PGL_max':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break
                
    if typ == 'price':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break  # Stop after assigning to the correct price_zone
        for node in grid.nodes_AC + grid.nodes_DC:
            if ts.element_name == node.name:
                node.TS_dict[typ] = ts.TS_num
                break  # Stop after assigning to the correct node    
    
    elif typ == 'Load':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.TS_dict[typ] = ts.TS_num
                break  # Stop after assigning to the correct price_zone
        for node in grid.nodes_AC + grid.nodes_DC:
            if ts.element_name == node.name:
                node.TS_dict[typ] = ts.TS_num
                break  # Stop after assigning to the correct node
                
    elif typ in ['WPP', 'OWPP', 'SF', 'REN', 'Solar']:
        for zone in grid.RenSource_zones:
            if ts.element_name == zone.name:
                zone.TS_dict['PRGi_available'] = ts.TS_num
                break  # Stop after assigning to the correct zone
        for rs in grid.RenSources:
            if ts.element_name == rs.name:
                rs.TS_dict['PRGi_available'] = ts.TS_num
                break  # Stop after assigning to the correct node


def add_inv_series(grid,inv_data,associated=None,inv_type=None,name=None):
    """ INFORMATION
    Supported investment-series inputs:

    - Price_Zone
      - 'Load'
      - 'elasticity'
      - 'import_expand'

    - Node_AC / Node_DC
      - 'Load'

    - Gen_AC
      - 'planned_installation'
      - 'planned_decomision'
      - 'max_inv'
      - 'np_dynamic'

    - Ren_Source
      - 'planned_installation'
      - 'planned_decomision'
      - 'max_inv'
      - 'np_dynamic'

    - Exp_Line_AC / Line_DC / AC_DC_converter
      - 'planned_installation'
      - 'planned_decomision'
      - 'max_inv'
      - 'np_dynamic'
 
    Notes:
    - inv_data must be a CSV file path.
    - CSV is read with header=None (no header row).
    - Row order in each column:
      - row 0: element (optional if 'associated' is passed)
      - row 1: inv_type (optional if 'inv_type' is passed)
      - remaining rows: period data
    - Period lengths must be consistent across all investment series in the grid.
    """
    if not isinstance(inv_data, (str, Path)):
        raise TypeError("inv_data must be a CSV file path (str or Path)")

    inv = pd.read_csv(inv_data, header=None)

    if inv.empty:
        raise ValueError("inv_data is empty")

    known_types = {
        'Load', 'elasticity', 'import_expand',
        'planned_installation', 'planned_decomision',
        'max_inv', 'np_dynamic'
    }
    # Expected period length is inferred from the first imported series
    # with more than one value. Scalar series (len=1) are always allowed.
    expected_len = None

    def _series_name(col):
        return str(col) if name is None else name

    def _to_numeric(values, inv_name):
        values = pd.Series(values).dropna()
        data = pd.to_numeric(values, errors='coerce')
        if data.isna().any():
            raise ValueError(
                f"Investment series '{inv_name}' contains non-numeric period values"
            )
        return data.to_numpy(dtype=float)

    def _associated_name(value):
        return value.name if hasattr(value, 'name') else value

    def _find_investment_element(grid_obj, elem_name):
        name = str(elem_name)
        candidates = (
            list(grid_obj.Price_Zones)
            + list(grid_obj.nodes_AC)
            + list(grid_obj.nodes_DC)
            + list(grid_obj.Generators)
            + list(grid_obj.RenSources)
            + list(grid_obj.lines_AC_exp)
            + list(grid_obj.lines_DC)
            + list(grid_obj.Converters_ACDC)
        )
        return next((el for el in candidates if str(getattr(el, 'name', '')) == name), None)

    def _is_all_load_case(elem_name, elem_type):
        return (
            str(elem_name).strip().lower() == 'all'
            and str(elem_type).strip().lower() == 'load'
        )

    def _load_targets_for_all(grid_obj):
        targets = []
        # Apply to all price zones with load investment support.
        for price_zone in list(getattr(grid_obj, 'Price_Zones', [])):
            if hasattr(price_zone, 'investment_decisions') and 'Load' in price_zone.investment_decisions:
                targets.append(price_zone)

        # Apply to independent AC/DC nodes with load investment support.
        for node in list(getattr(grid_obj, 'nodes_AC', [])) + list(getattr(grid_obj, 'nodes_DC', [])):
            if not hasattr(node, 'investment_decisions') or 'Load' not in node.investment_decisions:
                continue
            if isinstance(node, (Node_AC, Node_DC)) and getattr(node, 'PLi_linked', False):
                continue
            targets.append(node)
        return targets

    def _is_ignore_token(value):
        return str(value).strip().lower() == 'ignore'

    for col in inv.columns:
        col_values = inv[col].reset_index(drop=True)
        inv_name = _series_name(col)
        if _is_ignore_token(inv_name):
            continue
        if len(col_values) > 0 and _is_ignore_token(col_values.iloc[0]):
            continue

        # Case 1: element and type explicitly provided in function call.
        # CSV column contains only period data.
        if associated is not None and inv_type is not None:
            element_name = _associated_name(associated)
            element_type = inv_type
            data = _to_numeric(col_values, inv_name)

        # Case 2: element is provided; type is taken from row 0.
        elif associated is not None:
            if len(col_values) < 2:
                raise ValueError(
                    f"Investment series '{inv_name}' needs at least 2 rows when "
                    "'associated' is provided and 'inv_type' is not."
                )
            element_name = _associated_name(associated)
            element_type = col_values.iloc[0]
            data = _to_numeric(col_values.iloc[1:], inv_name)

        # Case 3: inv_type is provided; element is taken from row 0.
        elif inv_type is not None:
            if len(col_values) < 2:
                raise ValueError(
                    f"Investment series '{inv_name}' needs at least 2 rows when "
                    "'inv_type' is provided and 'associated' is not."
                )
            element_name = col_values.iloc[0]
            element_type = inv_type
            data = _to_numeric(col_values.iloc[1:], inv_name)

        # Case 4: both element and inv_type are read from CSV rows 0 and 1.
        else:
            if len(col_values) < 3:
                raise ValueError(
                    f"Investment series '{inv_name}' needs at least 3 rows when "
                    "'associated' and 'inv_type' are not provided"
                )
            element_name = col_values.iloc[0]
            element_type = col_values.iloc[1]
            data = _to_numeric(col_values.iloc[2:], inv_name)

        if data.size == 0:
            raise ValueError(f"Investment series '{inv_name}' has no period values")

        # Keep period length consistent inside this imported file.
        # Use the first non-scalar series as reference; scalar series are always valid.
        data_len = len(data)
        if data_len > 1 and expected_len is None:
            expected_len = data_len
        elif expected_len is not None and data_len not in (1, expected_len):
            raise ValueError(
                f"Investment series '{inv_name}' has {data_len} periods, expected {expected_len} (or 1)."
            )

        if str(element_type) not in known_types:
            print(
                f"Warning: inv_type '{element_type}' is not in documented supported types."
            )

        if _is_all_load_case(element_name, element_type):
            load_targets = _load_targets_for_all(grid)
            if not load_targets:
                raise ValueError(
                    "Investment series 'All/Load' found no matching Price_Zones or independent nodes."
                )
            load_data = np.array(data, dtype=float).tolist()
            for target in load_targets:
                target.investment_decisions['Load'] = load_data.copy()
            continue

        element = _find_investment_element(grid, element_name)
        if element is None:
            raise ValueError(
                f"Investment series '{inv_name}' references unknown element '{element_name}'"
            )
        if not hasattr(element, 'investment_decisions'):
            raise ValueError(
                f"Element '{element_name}' has no investment_decisions dictionary"
            )
        if str(element_type) not in element.investment_decisions:
            valid_keys = ", ".join(element.investment_decisions.keys())
            raise ValueError(
                f"Element '{element_name}' does not support inv_type '{element_type}'. "
                f"Valid keys: {valid_keys}"
            )

        element.investment_decisions[str(element_type)] = np.array(data, dtype=float).tolist()

def add_gen_mix_limits(grid, mix_data):
    """
    Load generation-mix limits per period from CSV and store on grid.

    Expected CSV format (header=None):
    - row 0: generation type (e.g. 'wind', 'natural gas')
    - row 1+: period limits (one value per investment period)
    - each column is one generation type series
    """
    if not isinstance(mix_data, (str, Path)):
        raise TypeError("mix_data must be a CSV file path (str or Path)")

    mix_df = pd.read_csv(mix_data, header=None)
    if mix_df.empty:
        raise ValueError("mix_data is empty")

    expected_len = None
    gen_mix_series = {}

    for col in mix_df.columns:
        col_values = mix_df[col].reset_index(drop=True)
        if len(col_values) < 2:
            raise ValueError(
                f"Generation mix column '{col}' needs at least 2 rows "
                "(gen_type + one data value)."
            )

        gen_type = str(col_values.iloc[0]).strip().lower()
        if not gen_type:
            raise ValueError(f"Generation mix column '{col}' has empty gen_type")

        values = pd.Series(col_values.iloc[1:]).dropna()
        data = pd.to_numeric(values, errors='coerce')
        if data.isna().any():
            raise ValueError(
                f"Generation mix column '{col}' ({gen_type}) contains non-numeric values"
            )
        if len(data) == 0:
            raise ValueError(
                f"Generation mix column '{col}' ({gen_type}) has no period values"
            )

        if expected_len is None:
            expected_len = len(data)
        elif len(data) != expected_len:
            raise ValueError(
                f"Generation mix type '{gen_type}' has {len(data)} periods, expected {expected_len}"
            )

        gen_mix_series[gen_type] = data.to_numpy(dtype=float).tolist()
        if gen_type not in grid.generation_types:
            grid.generation_types.append(gen_type)
        # Full per-period limits for MP model logic.
        grid.generation_type_limits[gen_type] = data.to_numpy(dtype=float).tolist()
        grid.current_generation_type_limits[gen_type] = float(data.iloc[0])

    return gen_mix_series


def create_gen_limit_csv_template(grid, file_path=None):
    """
    Create a generation-mix limit template CSV for active generation types.

    CSV layout per column (header=None expected by add_gen_mix_limits):
    - row 0: generation type
    - row 1+: period limits
    """
    if file_path is None:
        file_path = f'{grid.name}_gen_mix_limits.csv'
    path = Path(file_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    def _norm(gen_type):
        return str(gen_type).strip().lower() if gen_type is not None else None

    active_types = []
    seen_types = set()

    for gen in getattr(grid, 'Generators', []):
        gen_type = _norm(getattr(gen, 'gen_type', None))
        if not gen_type:
            continue
        units = float(getattr(gen, 'np_gen', 1.0))
        opf_active = bool(getattr(gen, 'np_gen_opf', False))
        if units <= 0 and not opf_active:
            continue
        if gen_type not in seen_types:
            seen_types.add(gen_type)
            active_types.append(gen_type)

    for ren_source in getattr(grid, 'RenSources', []):
        gen_type = _norm(getattr(ren_source, 'rs_type', None))
        if not gen_type:
            continue
        units = float(getattr(ren_source, 'np_rsgen', 1.0))
        opf_active = bool(getattr(ren_source, 'np_rsgen_opf', False))
        if units <= 0 and not opf_active:
            continue
        if gen_type not in seen_types:
            seen_types.add(gen_type)
            active_types.append(gen_type)

    if not active_types:
        raise ValueError("No active generation types were found in the provided grid.")

    # Read limits from the canonical container (can be scalar or per-period list).
    limit_series = {}
    scalar_limits_raw = getattr(grid, 'generation_type_limits', {})
    scalar_limits = {}
    if isinstance(scalar_limits_raw, dict):
        for k, v in scalar_limits_raw.items():
            kn = _norm(k)
            if not kn:
                continue
            if isinstance(v, (list, tuple, np.ndarray)):
                limit_series[kn] = list(v)
            else:
                scalar_limits[kn] = v

    max_periods = max((len(limit_series.get(gen_type, [])) for gen_type in active_types), default=0)

    if max_periods == 0:
        for element in list(getattr(grid, 'Generators', [])) + list(getattr(grid, 'RenSources', [])):
            inv_decisions = getattr(element, 'investment_decisions', {})
            if isinstance(inv_decisions, dict):
                for values in inv_decisions.values():
                    if values is not None:
                        max_periods = max(max_periods, len(values))
    if max_periods == 0:
        max_periods = 1

    columns = {}
    for col_idx, gen_type in enumerate(active_types):
        values = list(limit_series.get(gen_type, []))
        if not values:
            scalar_limit = scalar_limits.get(gen_type, 1.0)
            values = [float(scalar_limit)] * max_periods
        elif len(values) < max_periods:
            values = values + [values[-1]] * (max_periods - len(values))
        elif len(values) > max_periods:
            values = values[:max_periods]

        columns[col_idx] = [gen_type] + values

    template_df = pd.DataFrame(columns)
    template_df.to_csv(path, index=False, header=False)
    return str(path)
    
def create_inv_csv_template(grid, file_path=None, exclude=None):
    """
    Create an investment-series template CSV for the current grid.

    CSV layout per column (header=None expected by add_inv_series):
    - row 0: element name
    - row 1: inv_type
    - row 2+: current period data from investment_decisions
    """
    if file_path is None:
        file_path = f'{grid.name}_inv_series.csv'
    path = Path(file_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    exclude_keys = set(str(k) for k in (exclude or []))

    element_groups = [
        getattr(grid, 'Price_Zones', []),
        getattr(grid, 'nodes_AC', []),
        getattr(grid, 'nodes_DC', []),
        getattr(grid, 'Generators', []),
        getattr(grid, 'RenSources', []),
        getattr(grid, 'lines_AC_exp', []),
        getattr(grid, 'lines_DC', []),
        getattr(grid, 'Converters_ACDC', []),
    ]

    columns = {}
    col_idx = 0
    max_periods = 0
    for group in element_groups:
        for element in group:
            if not hasattr(element, 'investment_decisions'):
                continue
            # For nodes, only export independent load series (not price-zone-linked).
            if isinstance(element, (Node_AC, Node_DC)) and getattr(element, 'PLi_linked', True):
                continue
            # If element has an MP/TEP activation flag, only include active entries.
            if hasattr(element, 'np_line_opf') and not element.np_line_opf:
                continue
            if hasattr(element, 'np_gen_opf') and not element.np_gen_opf:
                continue
            if hasattr(element, 'np_rsgen_opf') and not element.np_rsgen_opf:
                continue
            if hasattr(element, 'np_conv_opf') and not element.np_conv_opf:
                continue
            element_name = getattr(element, 'name', None)
            if element_name is None:
                continue
            for inv_key, inv_values in element.investment_decisions.items():
                if str(inv_key) in exclude_keys:
                    continue
                values = list(inv_values) if inv_values is not None else []
                max_periods = max(max_periods, len(values))
                columns[col_idx] = [element_name, inv_key] + values
                col_idx += 1

    if not columns:
        raise ValueError(
            "No elements with investment_decisions were found in the provided grid."
        )

    # Pad columns to a common number of data rows so missing values remain visible.
    target_len = 2 + max_periods
    for col, values in columns.items():
        if len(values) < target_len:
            columns[col] = values + [""] * (target_len - len(values))

    template_df = pd.DataFrame(columns)
    template_df.to_csv(path, index=False, header=False)
    return str(path)
    
def add_TimeSeries(grid, Time_Series_data,associated=None,TS_type=None,name=None):
    # Check if Time_Series_data is a numpy array and convert to pandas DataFrame if needed
    if not isinstance(Time_Series_data, pd.DataFrame):
        TS = pd.DataFrame(Time_Series_data, columns=[name])
    else:
        TS = Time_Series_data
    Time_series = {}
    # check if there are nan values in Time series and change to 0
    TS.fillna(0, inplace=True)
    
    for col in TS.columns:
        if associated is not None and TS_type is not None:
            element_name = associated
            element_type = TS_type
            data = TS.loc[0:, col].astype(float).to_numpy()  
            name = col
            
        elif associated is not None: 
            element_name = associated
            element_type = TS.at[0, col]
            data = TS.loc[1:, col].astype(float).to_numpy()  
            name = col
        
        elif TS_type is not None:
            element_name = TS.at[0, col]
            element_type = TS_type
            data = TS.loc[1:, col].astype(float).to_numpy()   
            name = col
        
        else: 
            element_name = TS.at[0, col]
            element_type = TS.at[1, col]
            data = TS.loc[2:, col].astype(float).to_numpy()   
            name = col
            
        
        Time_serie = TimeSeries(element_type, element_name, data,name)                  
        grid.Time_series.append(Time_serie)
        grid.Time_series_dic[name]=Time_serie.TS_num
        time_series_dict(grid, Time_serie)
        
        
        
    grid.Time_series_ran = False
    s = 1


def assign_RenToZone(grid,ren_source_name,new_zone_name):
    new_zone = None
    old_zone = None
    ren_source_to_reassign = None
    
    for RenZone in grid.RenSource_zones:
        if RenZone.name == new_zone_name:
            new_zone = RenZone
            break
    if new_zone is None:
        raise ValueError(f"Zone {new_zone_name} not found.")
    
    # Remove node from its old price_zone
    for RenZone in grid.RenSource_zones:
        for ren_source in RenZone.RenSources:
            if ren_source.name == ren_source_name:
                old_zone = RenZone
                ren_source_to_reassign = ren_source
                break
        if old_zone:
            break
        
    if old_zone is not None:
        RenZone.ren_source = [ren_source for ren_source in old_zone.RenSources 
                               if ren_source.name != ren_source_name]
    
    # If the node was not found in any Renewable zone, check grid.nodes_AC
    if ren_source_to_reassign is None:
        for ren_source in grid.RenSources:
            if ren_source.name == ren_source_name:
                ren_source_to_reassign = ren_source
                break
            
    if ren_source_to_reassign is None:
        raise ValueError(f"Renewable source {ren_source_name} not found.")
    ren_source_to_reassign.PGRi_linked = True
    ren_source_to_reassign.Ren_source_zone = new_zone.name
    # Add node to the new price_zone
    if ren_source_to_reassign not in new_zone.RenSources:
        new_zone.RenSources.append(ren_source_to_reassign)
 
"Assigning components to zones"
    
def assign_nodeToPrice_Zone(grid,node_name, new_price_zone_name,ACDC='AC',link_load=True):
        """ Assign node to a new price_zone and remove it from its previous price_zone """
        new_price_zone = None
        old_price_zone = None
        node_to_reassign = None
        
        nodes_attr = 'nodes_DC' if ACDC == 'DC' else 'nodes_AC'
        
        # Find the new price_zone
        for price_zone in grid.Price_Zones:
            if price_zone.name == new_price_zone_name:
                new_price_zone = price_zone
                break

        if new_price_zone is None:
            raise ValueError(f"Price_Zone {new_price_zone_name} not found.")
        
        # Remove node from its old price_zone
        for price_zone in grid.Price_Zones:
            nodes = getattr(price_zone, nodes_attr)
            for node in nodes:
                if node.name == node_name:
                    old_price_zone = price_zone
                    node_to_reassign = node
                    break
            if old_price_zone:
                break
            
        if old_price_zone is not None:
            setattr(old_price_zone, nodes_attr, [node for node in getattr(old_price_zone, nodes_attr) if node.name != node_name])

        # If the node was not found in any price_zone, check grid.nodes_AC
        if node_to_reassign is None:
            nodes = getattr(grid, nodes_attr)
            for node in nodes:
                if node.name == node_name:
                    node_to_reassign = node
                    break
                
        if node_to_reassign is None:
            raise ValueError(f"Node {node_name} not found.")
        
        # Add node to the new price_zone
        new_price_zone_nodes = getattr(new_price_zone, nodes_attr)
        if node_to_reassign not in new_price_zone_nodes:
            new_price_zone_nodes.append(node_to_reassign)
            node_to_reassign.PZ=new_price_zone.name
            node_to_reassign.price=new_price_zone.price
            node_to_reassign.PLi_linked=link_load

def assign_ConvToPrice_Zone(grid, conv_name, new_price_zone_name):
        """ Assign node to a new price_zone and remove it from its previous price_zone """
        new_price_zone = None
        old_price_zone = None
        conv_to_reassign = None
        
        # Find the new price_zone
        for price_zone in grid.Price_Zones:
            if price_zone.name == new_price_zone_name:
                new_price_zone = price_zone
                break

        if new_price_zone is None:
            raise ValueError(f"Price_Zone {new_price_zone_name} not found.")
        
        # Remove node from its old price_zone
        for price_zone in grid.Price_Zones:
            for conv in price_zone.ConvACDC:
                if conv.name == conv_name:
                    old_price_zone = price_zone
                    conv_to_reassign = conv
                    break
            if old_price_zone:
                break
            
        if old_price_zone is not None:
            old_price_zone.ConvACDC = [conv for conv in old_price_zone.ConvACDC if conv.name != conv_name]
        
        # If the node was not found in any price_zone, check grid.nodes_AC
        if conv_to_reassign is None:
            for conv in grid.Converters_ACDC:
                if conv.name == conv_name:
                    conv_to_reassign = conv
                    break
                
        if conv_to_reassign is None:
            raise ValueError(f"Converter {conv_name} not found.")
        
        # Add node to the new price_zone
        if conv_to_reassign not in new_price_zone.ConvACDC:
            new_price_zone.ConvACDC.append(conv_to_reassign)            

def assign_lineToCable_options(grid,line_name, new_cable_option_name):
    """ Assign line to a new cable_type and remove it from its previous cable_type """
    new_cable_option = None
    old_cable_option = None
    line_to_reassign = None

    for cable_option in grid.Cable_options:
        if cable_option.name == new_cable_option_name:
            new_cable_option = cable_option
            break

    if new_cable_option is None:
        raise ValueError(f"Cable_option {new_cable_option_name} not found.")

    # Remove line from its old cable_option
    for cable_option in grid.Cable_options: 
        for line in cable_option.lines:
            if line.name == line_name:
                old_cable_option = cable_option
                line_to_reassign = line
                break
        if old_cable_option:
            break

    if old_cable_option is not None:
        old_cable_option.lines = [line for line in old_cable_option.lines if line.name != line_name]    

    if line_to_reassign is None:
        for line in grid.lines_AC_ct:
            if line.name == line_name:
                line_to_reassign = line
                break
        if line_to_reassign is None:
            raise ValueError(f"Line {line_name} not found.")

    # Add line to the new cable_option
    if line_to_reassign not in new_cable_option.lines:
        new_cable_option.lines.append(line_to_reassign) 
        line_to_reassign.cable_types = new_cable_option._cable_types





def expand_cable_database(data, format='yaml', save_yalm=False):
    """
    Expand the cable database by adding new cable specifications.
    
    Args:
        data: Either a path to YAML file, DataFrame, or dictionary with cable specifications
        format: 'yaml' or 'pandas' (default: 'yaml')
        output_path: Optional path to save the new YAML file (default: None)
        # Cable specifications

    Units:
       - Resistance: ohm/km
       - Inductance: mH/km
       - Capacitance: uF/km
       - Conductance: uS/km
       - Current rating: A
       - Power rating: MVA
       - Nominal voltage: kV
       - conductor_size: mm^2
       - Type: AC or DC

    Example YAML format:

    NEW_CABLE_TYPE:
        R_Ohm_km: 0.001
        L_mH_km: 0.001
        C_uF_km: 0.001
        G_uS_km: 0.001
        A_rating: 333
        Nominal_voltage_kV: 60
        MVA_rating: sqrt(3)*Nominal_voltage_kV*A_rating/1000
        conductor_size: 100
        Type: AC or DC
        Reference: REFERENCE
    """
    
    # Get the path to the Cable_database directory
    module_dir = Path(__file__).parent.parent
    cable_dir = module_dir / 'Cable_database'
    
    if format.lower() == 'yaml':
        if isinstance(data, (str, Path)):
            with open(data, 'r') as f:
                new_cables = yaml.safe_load(f)
        elif isinstance(data, dict):
            new_cables = data
        else:
            raise ValueError("For YAML format, data must be either a file path or dictionary")
            
    elif format.lower() == 'pandas':
        if isinstance(data, pd.DataFrame):
            new_cables = data.to_dict(orient='index')
        elif isinstance(data, (str, Path)):
            df = pd.read_csv(data)
            new_cables = df.to_dict(orient='index')
        else:
            raise ValueError("For pandas format, data must be either a DataFrame or file path")
    
   
    if save_yalm:
        # Save each cable type as a separate file
        for cable_name, cable_specs in new_cables.items():
            # Create a single-cable dictionary
            cable_data = {cable_name: cable_specs}
            
            # Create file path using cable name
            output_file = cable_dir / f"{cable_name}.yaml"
            
            # Save to YAML file
            with open(output_file, 'w') as f:
                yaml.dump(cable_data, f, sort_keys=False)
            
            print(f"Saved cable {cable_name} to {output_file}")
    
    # split ac and dc cables
    new_cables_ac = {}
    new_cables_dc = {}
    for key, value in new_cables.items():
        tval = str(value.get('Type', 'AC')).upper()
        if tval in ('HVAC', 'AC'):
            new_cables_ac[key] = value
        else:
            new_cables_dc[key] = value
    
    # Update the cable database
    if Line_DC._cable_database is None:
        Line_DC.load_cable_database()
    if Line_AC._cable_database is None:
        Line_AC.load_cable_database()
    # Add new cables to existing database
    Line_DC._cable_database = pd.concat([
        Line_DC._cable_database,
        pd.DataFrame.from_dict(new_cables_dc, orient='index')
    ])
    Line_AC._cable_database = pd.concat([
        Line_AC._cable_database,
        pd.DataFrame.from_dict(new_cables_ac, orient='index')
    ])


    print(f"Added {len(new_cables_ac)} new cables to AC and {len(new_cables_dc)} new cables to DC database")


def import_orbit_cables(
    data=None,
    column_map=None,
    default_type='AC',
    name_prefix='NREL',
    save_yaml=False,
    source_url='https://github.com/NLRWindSystems/ORBIT/tree/dev/library/cables',
):
    """
    Import ORBIT-style cable library data into pyflow cable database.

    Args:
        data: pandas DataFrame, CSV path, directory containing CSV files, or URL.
              If None, source_url is used.
        column_map: optional dict mapping pyflow field names to source columns.
                    pyflow fields:
                      ['name', 'R_Ohm_km', 'L_mH_km', 'C_uF_km', 'G_uS_km',
                       'A_rating', 'Nominal_voltage_kV', 'conductor_size',
                       'Type', 'Cost_per_km', 'Reference']
        default_type: fallback cable type when not provided ('AC' or 'DC').
        name_prefix: prefix used if a source row has no usable name.
        save_yaml: if True, also save imported entries as YAML files.
        source_url: ORBIT GitHub directory URL used when data is None.

    Returns:
        DataFrame with pyflow-standard cable schema, indexed by cable name.
    """

    def _read_text(url):
        req = Request(url, headers={'User-Agent': 'pyflow-acdc'})
        with urlopen(req) as resp:
            return resp.read().decode('utf-8')

    def _github_dir_to_rows(url):
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) < 5 or parts[2] not in ('tree', 'blob'):
            raise ValueError(
                'Expected GitHub URL like: https://github.com/<owner>/<repo>/tree/<ref>/<path>'
            )
        owner, repo = parts[0], parts[1]
        ref = parts[3]
        dir_path = '/'.join(parts[4:])
        api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={ref}'
        listing = json.loads(_read_text(api_url))
        if isinstance(listing, dict):
            listing = [listing]

        rows = []
        for item in listing:
            if item.get('type') != 'file':
                continue
            name = str(item.get('name', ''))
            dl = item.get('download_url')
            if not dl:
                continue

            if name.lower().endswith(('.yaml', '.yml')):
                y = yaml.safe_load(_read_text(dl))
                if not isinstance(y, dict):
                    continue
                # Handle nested {CableName: {...}} and flat {field: value}
                if len(y) == 1 and isinstance(next(iter(y.values())), dict):
                    cable_name = next(iter(y.keys()))
                    spec = next(iter(y.values()))
                    spec = dict(spec)
                    spec.setdefault('name', cable_name)
                    rows.append(spec)
                else:
                    rows.append(dict(y))
            elif name.lower().endswith('.csv'):
                rows.extend(pd.read_csv(dl).to_dict(orient='records'))
        return rows

    def _as_dataframe(obj):
        if obj is None:
            obj = source_url
        if isinstance(obj, pd.DataFrame):
            return obj.copy()
        if isinstance(obj, str) and obj.startswith(('http://', 'https://')):
            rows = _github_dir_to_rows(obj)
            if not rows:
                raise ValueError(f'No cable files found at URL: {obj}')
            return pd.DataFrame(rows)
        p = Path(obj)
        if p.is_dir():
            csv_files = sorted(p.glob('*.csv'))
            if not csv_files:
                raise ValueError(f'No CSV files found in directory: {p}')
            frames = [pd.read_csv(fp) for fp in csv_files]
            return pd.concat(frames, ignore_index=True)
        if p.is_file():
            return pd.read_csv(p)
        raise ValueError('data must be DataFrame, CSV file path, or directory with CSV files')

    def _slug(text):
        s = re.sub(r'[^A-Za-z0-9]+', '_', str(text)).strip('_')
        return s or 'Cable'

    def _pick_col(df, explicit, candidates, required=False):
        if explicit is not None:
            if explicit not in df.columns:
                raise KeyError(f"Mapped column '{explicit}' not found in source data")
            return explicit
        for c in candidates:
            if c in df.columns:
                return c
        if required:
            raise KeyError(f"Missing required source column. Tried: {candidates}")
        return None

    src = _as_dataframe(data)
    cmap = column_map or {}

    c_name = _pick_col(src, cmap.get('name'),
                       ['name', 'cable_name', 'Cable Name', 'id', 'ID'])
    c_r = _pick_col(src, cmap.get('R_Ohm_km'),
                    ['R_Ohm_km', 'r_ohm_km', 'resistance_ohm_km', 'ac_resistance', 'dc_resistance', 'Resistance (ohm/km)'],
                    required=True)
    c_l = _pick_col(src, cmap.get('L_mH_km'),
                    ['L_mH_km', 'l_mh_km', 'inductance_mh_km', 'Inductance (mH/km)'])
    c_c = _pick_col(src, cmap.get('C_uF_km'),
                    ['C_uF_km', 'c_uf_km', 'capacitance_uf_km', 'capacitance', 'Capacitance (uF/km)', 'Capacitance (nF/km)'])
    c_g = _pick_col(src, cmap.get('G_uS_km'),
                    ['G_uS_km', 'g_us_km', 'conductance_us_km', 'Conductance (uS/km)'])
    c_a = _pick_col(src, cmap.get('A_rating'),
                    ['A_rating', 'ampacity_a', 'ampacity', 'current_rating_a', 'current_capacity', 'Current (A)'],
                    required=True)
    c_kv = _pick_col(src, cmap.get('Nominal_voltage_kV'),
                     ['Nominal_voltage_kV', 'voltage_kv', 'rated_voltage_kv', 'rated_voltage', 'Voltage (kV)'],
                     required=True)
    c_cs = _pick_col(src, cmap.get('conductor_size'),
                     ['conductor_size', 'cross_section_mm2', 'area_mm2', 'size_mm2'])
    c_type = _pick_col(src, cmap.get('Type'),
                       ['Type', 'type', 'current_type', 'cable_type'])
    c_cost = _pick_col(src, cmap.get('Cost_per_km'),
                       ['Cost_per_km', 'cost_per_km', 'cost_eur_per_km', 'Cost (per km)'])
    c_ref = _pick_col(src, cmap.get('Reference'),
                      ['Reference', 'reference', 'source'])

    out_rows = []
    skipped_rows = 0
    for i, row in src.iterrows():
        nm = row[c_name] if c_name is not None else f'{name_prefix}_{i+1}'
        typ = row[c_type] if c_type is not None and pd.notna(row[c_type]) else default_type
        typ = str(typ).upper()
        if typ.startswith('HVAC') or typ == 'AC':
            typ = 'AC'
        elif typ.startswith('HVDC') or typ == 'DC':
            typ = 'DC'
        if typ not in ('AC', 'DC'):
            typ = default_type

        if pd.isna(row[c_kv]) or pd.isna(row[c_a]) or pd.isna(row[c_r]):
            skipped_rows += 1
            continue

        kv = float(row[c_kv])
        a_rating = float(row[c_a])
        if not np.isfinite(kv) or not np.isfinite(a_rating) or kv <= 0 or a_rating <= 0:
            skipped_rows += 1
            continue

        c_val = float(row[c_c]) if c_c is not None and pd.notna(row[c_c]) else 0.0
        # NREL/ORBIT exports often use nF/km for capacitance.
        # Convert to pyflow's expected uF/km when values look like nF/km scale.
        if c_val > 50:
            c_val = c_val / 1000.0
        size_val = float(row[c_cs]) if c_cs is not None and pd.notna(row[c_cs]) else np.nan
        name = f"{name_prefix}_{_slug(nm)}"

        out_rows.append({
            'name': name,
            'R_Ohm_km': float(row[c_r]),
            'L_mH_km': float(row[c_l]) if c_l is not None and pd.notna(row[c_l]) else 0.0,
            'C_uF_km': c_val,
            'G_uS_km': float(row[c_g]) if c_g is not None and pd.notna(row[c_g]) else 0.0,
            'A_rating': a_rating,
            'Nominal_voltage_kV': kv,
            'MVA_rating': np.sqrt(3.0) * kv * a_rating / 1000.0,
            'conductor_size': size_val,
            'Type': typ,
            'Cost_per_km': float(row[c_cost]) if c_cost is not None and pd.notna(row[c_cost]) else 1.0,
            'Reference': row[c_ref] if c_ref is not None and pd.notna(row[c_ref]) else 'ORBIT',
        })

    if not out_rows:
        raise ValueError('No valid cable rows were found after parsing ORBIT data.')

    out_df = pd.DataFrame(out_rows).set_index('name')
    out_df = out_df[~out_df.index.duplicated(keep='first')]

    expand_cable_database(out_df, format='pandas', save_yalm=save_yaml)
    if skipped_rows:
        print(f"Skipped {skipped_rows} cable rows with missing/invalid key fields.")
    return out_df


def grid_state(grid):
    Total_load = 0
    min_generation = 0
    max_generation = 0
    for node in grid.nodes_AC:
        Total_load += node.PLi
    for node in grid.nodes_DC:
        Total_load += node.PLi
    for gen in grid.Generators:
        min_generation += gen.Min_pow_gen*gen.np_gen if not gen.activate_gen_opf else 0
        max_generation += gen.Max_pow_gen*gen.np_gen 
    
    for ren in grid.RenSources:
        min_generation += ren.PGi_ren*ren.min_gamma
        max_generation += ren.PGi_ren
    return Total_load, min_generation, max_generation

def analyse_grid(grid):
    
    # Perform the analysis and store directly on grid
    grid.ACmode = grid.nn_AC != 0       #AC nodes present
    grid.DCmode = grid.nn_DC != 0       #DC nodes present
    grid.TEP_AC = grid.nle_AC != 0 #AC expansion lines present
    grid.REC_AC = grid.nlr_AC != 0 #AC reconductoring lines present
    grid.TAP_tf = grid.nttf != 0    #AC transformer lines present
    grid.CT_AC  = grid.nct_AC!= 0 #AC conductor size selection lines present
    grid.CFC = grid.ncfc_DC != 0 #DC variable voltage converter lines present
    grid.CDC = grid.ncdc_DC != 0 #DC-DC converter lines present
    grid.GPR = any(gen.np_gen_opf for gen in grid.Generators)
    grid.rs_GPR = any(rs.np_rsgen_opf for rs in grid.RenSources)
    grid.act_gen = any(gen.activate_gen_opf for gen in grid.Generators)

    return grid.ACmode, grid.DCmode, [grid.TEP_AC, grid.TAP_tf, grid.REC_AC, grid.CT_AC], [grid.CFC, grid.CDC], grid.GPR
    

def current_fuel_type_distribution(grid, output='df'):
    """
    Build current generation-type distribution summary.

    The summary follows Static TEP style normalization (lowercase types) and
    includes both conventional generators and renewable sources.

    Parameters
    ----------
    grid : grid
        Pyflow grid object.
    output : str, optional
        'df' (default) -> pandas DataFrame with columns:
        ['Type', 'number of gen', 'total install cap', 'percentage'].
        'dict' -> dict keyed by Type with the same fields.
    """
    def _norm(t):
        return str(t).lower() if t else None

    type_capacity = {}
    type_units = {}
    type_limits = {_norm(k): v for k, v in grid.current_generation_type_limits.items()}

    for gen in getattr(grid, 'Generators', []):
        gt = _norm(getattr(gen, 'gen_type', None))
        if gt is None:
            continue
        units = float(getattr(gen, 'np_gen', 1.0))
        cap = float(getattr(gen, 'Max_pow_gen', 0.0)) * units
        type_units[gt] = type_units.get(gt, 0.0) + units
        type_capacity[gt] = type_capacity.get(gt, 0.0) + cap

    for rs in getattr(grid, 'RenSources', []):
        rt = _norm(getattr(rs, 'rs_type', None))
        if rt is None:
            continue
        units = float(getattr(rs, 'np_rsgen', 1.0))
        cap = float(getattr(rs, 'PGi_ren_base', 0.0)) * units
        type_units[rt] = type_units.get(rt, 0.0) + units
        type_capacity[rt] = type_capacity.get(rt, 0.0) + cap

    total_cap = sum(type_capacity.values())
    total_units = sum(type_units.values())
    load_nodes_count = sum(1 for node in grid.nodes_AC if node.PLi != 0.0)+sum(1 for node in grid.nodes_DC if node.PLi != 0.0)
    
    total_system_load =  sum(node.PLi for node in grid.nodes_AC)+ sum(node.PLi for node in grid.nodes_DC)
    load_pct_of_total_cap = round((total_system_load / total_cap) * 100.0, 2) if total_cap > 0 else 0.0
    

    rows = []
    for typ in sorted(type_capacity):
        cap = type_capacity[typ]
        units = type_units.get(typ, 0.0)
        pct = round((cap / total_cap * 100.0), 2) if total_cap > 0 else 0.0
        limit = type_limits.get(typ)
        rows.append({
            'Type': typ,
            'number of gen': units,
            'total install cap': cap,
            'percentage': pct,
            'current limit': round(float(limit) * 100.0, 2) if limit is not None else None,
        })

    rows.append({
        'Type': 'All',
        'number of gen': total_units,
        'total install cap': total_cap,
        'percentage': 100.0 if total_cap > 0 else 0.0,
        'current limit': None,
    })
    rows.append({
        'Type': 'System load (all nodes)',
        'number of gen': load_nodes_count,
        'total install cap': total_system_load,
        'percentage': load_pct_of_total_cap,
        'current limit': None,
    })

    if output == 'df':
        return pd.DataFrame(
            rows,
            columns=['Type', 'number of gen', 'total install cap', 'percentage', 'current limit']
        )
    if output == 'dict':
        return {row['Type']: {
            'number of gen': row['number of gen'],
            'total install cap': row['total install cap'],
            'percentage': row['percentage'],
            'current limit': row['current limit'],
        } for row in rows}
    raise ValueError("output must be either 'df' or 'dict'")