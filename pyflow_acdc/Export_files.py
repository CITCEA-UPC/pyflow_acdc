# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 18:23:52 2024

@author: BernardoCastro
"""

import numpy as np
import pandas as pd
import os
from .Classes import MTDCPrice_Zone, OffshorePrice_Zone

import os
import pickle
import gzip

try:
    import dill  # optional fallback
    _dill = dill
except Exception:
    _dill = None

__all__ = [
    'save_grid_to_file',
    'save_grid_to_matlab',
    'save_pickle'

]

def generate_dataframe_code_from_dict(data_list, var_name):
    """
    Generate Python code to recreate a DataFrame from an input dictionary.
    
    :param data_dict: Dictionary with column names as keys and lists as values.
    :param var_name: The desired variable name for the DataFrame.
    :return: Python code to recreate the DataFrame.
    """
    
    if not data_list:
        return f"{var_name} = None\n"
    
    data_repr = f"{var_name}_data = [\n"
    for i, data in enumerate(data_list):
        data_repr += f"        {data},\n" if i < len(data_list) - 1 else f"        {data}\n"
    data_repr += "    ]\n"
    
    # Create DataFrame from list of dictionaries
    df_creation_code = f"    {var_name} = pd.DataFrame({var_name}_data)\n"
    
    # Return the complete code
    return data_repr + df_creation_code
    
def generate_add_price_zone_code(price_zone_data):
    """
    Generates Python code with a for loop to call `add_price_zone` for each set of arguments
    in the list `price_zone_data`.
    
    :param price_zone_data: List of dictionaries with arguments for add_price_zone.
    :return: Python code as a string to call add_price_zone for each set of arguments.
    """
    
    code = ""
    
    if not price_zone_data:
        return code
  
    # Loop through each entry in the data list and generate the corresponding function call
    for zone in price_zone_data:
        if zone["type"]=="main":        
            code += f"    pyf.add_price_zone(grid,'{zone['name']}',{zone['price']},import_pu_L={zone['import_pu_L']},export_pu_G={zone['export_pu_G']},a={zone['a']},b={zone['b']},c={zone['c']},import_expand_pu={zone['import_expand_pu']})\n"
    for zone in price_zone_data:
        if zone["type"]== "offshore":
            code += f"    pyf.add_offshore_price_zone(grid,'{zone['main_price_zone']}','{zone['name']}')\n"
    for zone in price_zone_data:
        if zone["type"]== "MTDC":
            code += f"    pyf.add_MTDC_price_zone(grid, '{zone['name']}',linked_price_zones={zone['linked_price_zones']},pricing_strategy={zone['pricing_strategy']})\n"        
    
   
    return code

def generate_add_gen_code(gens,S_base):
    """
    Generate Python code with a for loop to call `add_gen` for each generator in the list `gens`.
    
    :param gens: List of dictionaries, where each dictionary contains the arguments for add_gen.
    :return: Python code as a string to call add_gen for each generator.
    """

    code = ""
    if not gens:
        return code
    
    # Loop through each generator in the list and generate the corresponding function call
    for gen in gens:
        # Start building the add_gen function call
        code += f"    pyf.add_gen(grid, '{gen['node']}', '{gen['name']}', "
        
        # Dynamically handle parameters
        if gen['price_zone_link'] != False:
            code += f"price_zone_link={gen['price_zone_link']}, "
        code += f"np_gen={gen['np_gen']}, "
        code += f"fc={gen['fc']},lf={gen['lf']}, qf={gen['qf']}, "
        code += f"MWmax={gen['Max_pow_gen']*S_base}, MWmin={gen['Min_pow_gen']*S_base}, "
        code += f"MVArmax={gen['Max_pow_genR']*S_base}, MVArmin={gen['Min_pow_genR']*S_base}, "
        code += f"PsetMW={gen['Pset']*S_base}, QsetMVA={gen['Qset']*S_base})\n"

    
    return code

def generate_add_ren_source_zone_code(ren_source_zones):
    """
    Generate Python code with a for loop to call `add_RenSource_zone` for each renewable source zone in the list `ren_source_zones`.

    :param ren_source_zones: List of dictionaries, where each dictionary contains the arguments for add_RenSource_zone.
    :return: Python code as a string to call add_RenSource_zone for each renewable source zone.
    """
    
    code = ""
    
    if not ren_source_zones:
        return code
    
    for zone in ren_source_zones:
        # Start building the add_RenSource_zone function call
        code += f"    pyf.add_RenSource_zone(grid,'{zone['name']}')\n"
    
    return code

def generate_add_ren_source_code(ren_sources,S_base):
    """
    Generate Python code with a for loop to call `add_RenSource` for each renewable source in the list `ren_sources`.

    :param ren_sources: List of dictionaries, where each dictionary contains the arguments for add_RenSource.
    :return: Python code as a string to call add_RenSource for each renewable source.
    """
    
    
    
    code = ""
    
    if not ren_sources:
        return code
    
    for ren_source in ren_sources:
        # Start building the add_RenSource function call
        code += f"    pyf.add_RenSource(grid, '{ren_source['node_name']}', {ren_source['base']*S_base}, "
        
        # Dynamically handle optional parameters
        code += f"ren_source_name='{ren_source['ren_source_name']}', " if ren_source['ren_source_name'] else ""
        code += f"available={ren_source['available']}, "
        code += f"zone='{ren_source['zone']}', " if ren_source['zone'] else ""
        code += f"price_zone='{ren_source['price_zone']}', " if ren_source['price_zone'] else ""
        code += f"Offshore={ren_source['Offshore']}, "
        code += f"MTDC={ren_source['MTDC']})\n"
    
    return code

def create_dictionaries(grid):
    data = {
        "S_base": grid.S_base,
        "nodes_AC": [],
        "lines_AC": [],
        "nodes_DC": [],
        "lines_DC": [],
        "Converters_ACDC": [],
        "Price_Zone": [],
        "RenSource_zone": [],
        "Generators": [],
        "RenSources": [],
    }
    
    # AC Nodes
    if grid.nodes_AC:
        for node in getattr(grid, "nodes_AC", []):
            if node:
                data["nodes_AC"].append({
                    "Node_id": node.name,
                    "type": node.type,
                    "Voltage_0": float(node.V_ini),
                    "theta_0": float(node.theta_ini),
                    "kV_base": float(node.kV_base),
                    "Power_Gained": float(node.PGi),
                    "Reactive_Gained": float(node.QGi),
                    "Power_load": float(node.PLi),
                    "Reactive_load": float(node.QLi),
                    "Umin": float(node.Umin),
                    "Umax": float(node.Umax),
                    "Gs": float(np.real(node.Reactor)),
                    "Bs": float(np.imag(node.Reactor)),
                    "x_coord": float(node.x_coord) if node.x_coord is not None else None,
                    "y_coord": float(node.y_coord) if node.y_coord is not None else None,
                    "PZ": node.PZ,
                    "geometry": node.geometry.wkt if node.geometry is not None else None
                })

    # AC Lines
    if grid.lines_AC:
        for line in getattr(grid, "lines_AC", []):
            if line:
                data["lines_AC"].append({
                    "Line_id": line.name,
                    "fromNode": line.fromNode.name,
                    "toNode": line.toNode.name,
                    "r": float(line.R),
                    "x": float(line.X),
                    "g": float(line.G),
                    "b": float(line.B),
                    "MVA_rating": float(line.MVA_rating),
                    "m": float(line.m),
                    "shift": float(line.shift),
                    "Length_km": float(line.Length_km),
                    "geometry": line.geometry.wkt if line.geometry is not None else None
                })

    # DC Nodes
    if grid.nodes_DC:
        for node in getattr(grid, "nodes_DC", []):
            if node:
                data["nodes_DC"].append({
                    "type": node.type,
                    "Voltage_0": float(node.V_ini),
                    "Power_Gained": float(node.PGi),
                    "Power_load": float(node.PLi),
                    "kV_base": float(node.kV_base),
                    "Node_id": node.name,
                    "Umin": float(node.Umin),
                    "Umax": float(node.Umax),
                    "x_coord": float(node.x_coord) if node.x_coord is not None else None,
                    "y_coord": float(node.y_coord) if node.y_coord is not None else None,
                    "PZ": node.PZ,
                    "geometry": node.geometry.wkt if node.geometry is not None else None
                })

    # DC Lines
    if grid.lines_DC:
        for line in getattr(grid, "lines_DC", []):
            if line:
                if line.pol   == 1:
                    pol = 'm'
                else:
                    pol = 'b'
            
                data["lines_DC"].append({
                    "fromNode":   line.fromNode.name,
                    "toNode":     line.toNode.name,
                    "r": float(line.R),
                    "MW_rating":  float(line.MW_rating),
                    "kV_base":    float(line.kV_base),
                    "Length_km":         float(line.Length_km),
                    "Mono_Bi_polar":   pol,
                    "Line_id":       line.name,     
                    "geometry": line.geometry.wkt if line.geometry is not None else None
                })

    # Converters
    if grid.Converters_ACDC:
        for conv in getattr(grid, "Converters_ACDC", []):
            if conv:
                data["Converters_ACDC"].append({
                    "AC_type": conv.AC_type,
                    "DC_type": conv.type,
                    "AC_node": conv.Node_AC.name,
                    "DC_node": conv.Node_DC.name,
                    "P_AC": float(conv.P_AC),
                    "Q_AC": float(conv.Q_AC),
                    "P_DC": float(conv.P_DC),
                    "T_r": float(conv.R_t * conv.cn_pol),
                    "T_x": float(conv.X_t * conv.cn_pol),
                    "PR_r": float(conv.PR_R * conv.cn_pol),
                    "PR_x": float(conv.PR_X * conv.cn_pol),
                    "Filter": float(conv.Bf / conv.cn_pol),
                    "Droop": float(conv.Droop_rate),
                    "AC_kV_base": float(conv.AC_kV_base),
                    "MVA_rating": float(conv.MVA_max / conv.cn_pol),
                    "Nconverter": float(conv._np_conv),
                    "pol": float(conv.cn_pol),
                    "Conv_id": conv.name,
                    "lossa": float(conv.a_conv_og / conv.cn_pol),
                    "lossb": float(conv.b_conv_og),
                    "losscrect": float(conv.c_rect_og * conv.cn_pol),
                    "losscinv": float(conv.c_inver_og * conv.cn_pol),
                    "Ucmin": float(conv.Ucmin),
                    "Ucmax": float(conv.Ucmax),
                    "geometry": conv.geometry.wkt if conv.geometry is not None else None        
                })
    
    # Step 1: Define sets for the MTDC price_zones and linked price_zones
    if grid.Price_Zones:
        for price_zone in getattr(grid, "Price_Zones", []):
            if price_zone:
                if isinstance(price_zone, MTDCPrice_Zone):
                    data["Price_Zone"].append({
                        "name": price_zone.name,
                        "linked_price_zones": price_zone.linked_price_zones,
                        "pricing_strategy": price_zone.pricing_strategy,
                        "type":'MTDC',
                    })
                elif isinstance(price_zone, OffshorePrice_Zone):
                    data["Price_Zone"].append({
                        "main_price_zone": price_zone.main_price_zone.name,
                        "name": price_zone.name,
                        "type":'offshore', 
                    })
                else:
                    data["Price_Zone"].append({
                        "name":        price_zone.name,
                        "price":       price_zone._price,
                        "import_pu_L": price_zone.import_pu_L,
                        "export_pu_G": price_zone.export_pu_G,
                        "a":           price_zone.a,
                        "b":           price_zone.b,
                        "c":           price_zone.c,
                        "import_expand_pu": price_zone.import_expand,
                        "type":'main',
                    })

    # RenSource Zones
    if grid.RenSource_zones:
        for ren_zone in getattr(grid, "RenSource_zones", []):
            if ren_zone:
                data["RenSource_zone"].append({
                    "name": ren_zone.name,
                })

    # Generators
    if grid.Generators:
        for gen in getattr(grid, "Generators", []):
            if gen:
                data["Generators"].append({
                    "name": gen.name,
                    "node": gen.Node_AC,
                    "Max_pow_gen":  gen.Max_pow_gen,
                    "Min_pow_gen":  gen.Min_pow_gen,
                    "Max_pow_genR": gen.Max_pow_genR,
                    "Min_pow_genR": gen.Min_pow_genR,
                    "np_gen": gen.np_gen,
                    "qf": gen.qf,
                    "lf":  gen.lf,
                    "fc": gen.fc,
                    "Pset": gen.Pset,
                    "Qset": gen.Qset,
                    "S_rated": gen.Max_S,
                    "price_zone_link" :gen.price_zone_link,
                })

    # RenSources
    if grid.RenSources:
        for ren_source in getattr(grid, "RenSources", []):
            if ren_source:
                        
                data["RenSources"].append({
                    "ren_source_name" : ren_source.name,
                    "node_name": ren_source.Node,
                    "base": ren_source.PGi_ren_base,
                    "available": ren_source._PRGi_available,
                    "zone":       getattr(ren_source, "zone", None),
                    "price_zone": getattr(ren_source, "price_zone", None),
                    "Offshore":   getattr(ren_source, "Offshore", False),
                    "MTDC":       getattr(ren_source, "MTDC", None),
                })

    return data






def generate_loading_code(grid,file_name):
    
    data_dict=create_dictionaries(grid)
    # Generate the code
    nodes_AC_code = generate_dataframe_code_from_dict(data_dict["nodes_AC"], "nodes_AC")
    lines_AC_code = generate_dataframe_code_from_dict(data_dict["lines_AC"], "lines_AC")
    nodes_DC_code = generate_dataframe_code_from_dict(data_dict["nodes_DC"], "nodes_DC")
    lines_DC_code = generate_dataframe_code_from_dict(data_dict["lines_DC"], "lines_DC")
    Converters_ACDC_code = generate_dataframe_code_from_dict(data_dict["Converters_ACDC"], "Converters_ACDC")
    
    
    pz_code = generate_add_price_zone_code(data_dict["Price_Zone"])
    gen_code = generate_add_gen_code(data_dict["Generators"],data_dict['S_base'])
    
    
    rz_code = generate_add_ren_source_zone_code(data_dict["RenSource_zone"])
    rens_code = generate_add_ren_source_code(data_dict["RenSources"],data_dict['S_base'])
    
    
    main_code = f"""

import pyflow_acdc as pyf
import pandas as pd


def {file_name}():    
    
    S_base={data_dict['S_base']}
    
    # DataFrame Code:
    {nodes_AC_code}
    {lines_AC_code}
    {nodes_DC_code}
    {lines_DC_code}
    {Converters_ACDC_code}
    
    # Create the grid
    [grid, res] = pyf.Create_grid_from_data(S_base, nodes_AC, lines_AC, nodes_DC, lines_DC, Converters_ACDC, data_in='pu')
    grid.name = '{file_name}'
    """
    
    if pz_code:
        main_code += f"""    
    
    # Add Price Zones:
{pz_code}
    

    """
    
    # If nodes_AC code exists, add the code for assigning price zones to nodes_AC
        if data_dict["nodes_AC"]:
            main_code += f"""
    # Assign Price Zones to Nodes
    for index, row in nodes_AC.iterrows():
        node_name = nodes_AC.at[index, 'Node_id']
        price_zone = nodes_AC.at[index, 'PZ']
        ACDC = 'AC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    """
    
    # If nodes_DC code exists, add the code for assigning price zones to nodes_DC
        if data_dict["nodes_DC"]:
            main_code += f"""
    for index, row in nodes_DC.iterrows():
        node_name = nodes_DC.at[index, 'Node_id']
        price_zone = nodes_DC.at[index, 'PZ']
        ACDC = 'DC'
        if price_zone is not None:
            pyf.assign_nodeToPrice_Zone(grid, node_name, price_zone,ACDC)
    """
    
    
    main_code+=f"""
    # Add Generators
{gen_code}    
    
    # Add Renewable Source Zones
{rz_code}
    
    # Add Renewable Sources
{rens_code}
    
    # Return the grid
    return grid,res
"""

   
    return main_code
    
    


def save_pickle(grid, path, compress=True, use_dill=False):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    lib = _dill if (use_dill and _dill is not None) else pickle
    protocol = pickle.HIGHEST_PROTOCOL

    if compress:
        with gzip.open(path, "wb") as f:
            lib.dump(grid, f, protocol=protocol)
    else:
        with open(path, "wb") as f:
            lib.dump(grid, f, protocol=protocol)



def save_grid_to_file(grid, file_name,folder_name=None):
    """
    Save the generated main code to a .py file.

    :param main_code: The code to save to the file.
    :param file_name: The name of the file where the code will be saved.
    """
    
    main_code= generate_loading_code(grid,file_name)
   
    if folder_name is not None:
        # Ensure the folder path exists
        os.makedirs(folder_name, exist_ok=True)  # Create folder if it doesn't exist
        
        # Save the file in the specified folder
        file_path = os.path.join(folder_name, f'{file_name}.py')
    else:
        # Save the file in the current directory
        file_path = f'{file_name}.py'
    
    # Write the main code to the file
    with open(file_path, 'w') as file:
        file.write(main_code)



def gather_grid_data(grid):
    node_ac_data = []

    for node in grid.nodes_AC:
        if node.type == 'PQ':
            tp=1
        elif node.type =='PV':
            tp=2
        else:
            tp=3
        node_ac_data.append({
            "bus_i": node.nodeNumber+1,
            "type": tp,
            "Pd": node.PLi*grid.S_base,
            "Qd": node.QLi*grid.S_base,
            "Gs": np.real(node.Reactor)*grid.S_base,
            "Bs": np.imag(node.Reactor)*grid.S_base,
            "area": grid.Graph_node_to_Grid_index_AC[node.nodeNumber]+1,
            "Vm": node.V_ini,
            "Va": node.theta_ini,
            "baseKV": node.kV_base,
            "zone": grid.Graph_node_to_Grid_index_AC[node.nodeNumber]+1,
            "Vmax": node.Umax,
            "Vmin": node.Umin
        })  
        
    line_ac_data = []

    for line in grid.lines_AC:
        line_ac_data.append({
            "fbus": line.fromNode.nodeNumber+1,
            "tbus": line.toNode.nodeNumber+1,
            "r": line.R,
            "x": line.X,
            "b": line.B,
            "rateA": np.round(line.MVA_rating,0),
            "rateB": np.round(line.MVA_rating,0),
            "rateC": np.round(line.MVA_rating,0),
            "ratio": line.m     if line.m !=1 and line.shift !=0  else 0,
            "angle": line.shift if line.m !=1 and line.shift !=0  else 0,
            "status": 1,
            "angmin": -360,
            "angmax": 360
        })
    
    node_dc_data = []
    
    if grid.nodes_DC is not None:    
        for node in grid.nodes_DC:
            node_dc_data.append({
                "busdc_i": node.nodeNumber+1,
                "grid": grid.Graph_node_to_Grid_index_DC[node.nodeNumber]+1,
                "Pdc": node.PLi*grid.S_base,
                "Vdc": node.V_ini,
                "basekVdc": node.kV_base,
                "Vdcmax": node.Umax,
                "Vdcmin": node.Umin,
                "Cdc": 0
            })
        
        
    line_dc_data = []
    if grid.lines_DC is not None:   
        for line in grid.lines_DC:
            pol = line.pol
            
            line_dc_data.append({
                "fbusdc": line.fromNode.nodeNumber+1,
                "tbusdc": line.toNode.nodeNumber+1,
                "r": line.R,
                "l": 0,
                "c": 0,
                "rateA": np.round(line.MW_rating,0),
                "rateB": np.round(line.MW_rating,0),
                "rateC": np.round(line.MW_rating,0),
                "status": 1
            })
    
    conv_data = []
    if grid.Converters_ACDC is not None:   
        for conv in grid.Converters_ACDC:
            if conv.AC_type == 'PQ':
                tpac=1
            elif conv.AC_type =='PV':
                tpac=2
            else:
                tpac=1
            
            if conv.type == 'P' or conv.type == 'PAC':
                tpdc=1
            elif conv.type =='Slack':
                tpdc=2
            else: 
                tpdc=3
            
            
            conv_data.append({
                "busdc_i": conv.Node_DC.nodeNumber+1,
                "busac_i": conv.Node_AC.nodeNumber+1,
                "type_dc": tpdc,
                "type_ac": tpac,
                "P_g": conv.P_AC,
                "Q_g": conv.P_DC,
                "islcc": 0, 
                "Vtar": 1,
                "rtf": conv.R_t/conv.np_conv,
                "xtf": conv.X_t/conv.np_conv,
                "transformer": 1 if conv.R_t != 0 else 0,
                "tm": 1,
                "bf": conv.Bf*conv.np_conv,
                "filter": 1 if conv.Bf != 0 else 0,
                "rc": conv.PR_R/conv.np_conv,
                "xc": conv.PR_X/conv.np_conv,
                "reactor": 0,
                "basekVac": conv.AC_kV_base,
                "Vmmax": conv.Ucmax,
                "Vmmin": conv.Ucmin,
                "Imax": 1.1,
                "status": 1,
                "LossA": conv.a_conv_og*conv.np_conv,
                "LossB": conv.b_conv_og,
                "LossCrec": conv.c_rect_og/conv.np_conv,
                "LossCinv": conv.c_rect_og/conv.np_conv,
                "droop": conv.Droop_rate,
                "Pdcset": conv.P_DC,
                "Vdcset": conv.Node_DC.V,
                "dVdcset": 0,
                "Pacmax": conv.MVA_max,
                "Pacmin": -conv.MVA_max,
                "Qacmax": conv.MVA_max,
                "Qacmin": -conv.MVA_max
            })
        
    gen_data = []

    for gen in grid.Generators:
        gen_data.append({
            "bus": gen.Node_AC.nodeNumber+1,
            "Pg": gen.Pset,
            "Qg": gen.Qset,
            "Qmax": gen.Max_pow_genR*grid.S_base,
            "Qmin": gen.Min_pow_genR*grid.S_base,
            "Vg": gen.Node_AC.V,
            "mBase": grid.S_base,
            "status": 1,
            "Pmax": gen.Max_pow_gen*grid.S_base,
            "Pmin": gen.Min_pow_gen*grid.S_base,
            "Pc1": 0,
            "Pc2": 0,
            "Qc1min": 0,
            "Qc1max": 0,
            "Qc2min": 0,
            "Qc2max": 0,
            "ramp_agc": 0,
            "ramp_10": 0,
            "ramp_30": 0,
            "ramp_q": 0,
            "apf": 0
        }) 
    
    if grid.RenSources is not None:    
        for gen in grid.RenSources:
            if gen.connected =='DC':
                continue
            gen_data.append({
                "bus": gen.Node.nodeNumber+1,
                "Pg": gen.PGi_ren,
                "Qg": 0,
                "Qmax": gen.Qmax,
                "Qmin": gen.Qmin,
                "Vg": gen.Node.V,
                "mBase": grid.S_base,
                "status": 1,
                "Pmax": gen.PGi_ren*grid.S_base,
                "Pmin": gen.PGi_ren*gen.min_gamma*grid.S_base,
                "Pc1": 0,
                "Pc2": 0,
                "Qc1min": 0,
                "Qc1max": 0,
                "Qc2min": 0,
                "Qc2max": 0,
                "ramp_agc": 0,
                "ramp_10": 0,
                "ramp_30": 0,
                "ramp_q": 0,
                "apf": 0
            })
        
    gen_cost_data = []

    for gen in grid.Generators:
        gen_cost_data.append({
            "type": 2,
            "n":3,
            "startup": 0,
            "shutdown": 0,
            "c(n-1)": gen.qf,  # Coefficient of the highest power term
            "c(n-2)": gen.lf,  # Coefficient of the second highest power term
            "c0": 0         # Constant cost term
        }) 
    if grid.RenSources is not None:        
        for gen in grid.RenSources:
            if gen.connected =='DC':
                continue
            gen_cost_data.append({
                "type": 2,
                "n":3,
                "startup": 0,
                "shutdown":0,
                "c(n-1)": 0,  # Coefficient of the highest power term
                "c(n-2)": 0,  # Coefficient of the second highest power term
                "c0": 0         # Constant cost term
            })  
    base=grid.S_base
    grid_data = [base,node_ac_data,line_ac_data,node_dc_data,line_dc_data,conv_data,gen_data,gen_cost_data]    
    return grid_data
        
        
def save_grid_to_matlab(grid,file_name,folder_name=None,dcpol=2):
    
    base,node_ac_data,line_ac_data,node_dc_data,line_dc_data,conv_data,gen_data,gen_cost_data = gather_grid_data(grid)
    
    if folder_name is not None:
        # Ensure the folder path exists
        os.makedirs(folder_name, exist_ok=True)  # Create folder if it doesn't exist
        
        # Save the file in the specified folder
        file_path = os.path.join(folder_name, f'{file_name}.m')
    else:
        # Save the file in the current directory
        file_path = f'{file_name}.m'
    
    # Write the main code to the file
    with open(file_path, 'w') as f:
        f.write(f"function mpc = {file_name}()\n\n")
        
        # BaseMVA
        f.write("mpc.version = '2';\n\n")
        
        
        # BaseMVA
        f.write(f"mpc.baseMVA = {base};\n\n")

        # Bus data
        f.write("%% AC bus data\n")
        f.write("%    bus_i    type    Pd    Qd    Gs    Bs    area    Vm    Va    baseKV    zone    Vmax    Vmin\n")
        f.write("mpc.bus = [\n")
        for node in node_ac_data:
            f.write(f"   {node['bus_i']}     {node['type']}     {node['Pd']}     {node['Qd']}     {node['Gs']}     {node['Bs']}     {node['area']}     {node['Vm']}     {node['Va']}     {node['baseKV']}     {node['zone']}     {node['Vmax']}     {node['Vmin']};\n")
        f.write("];\n\n")

        # For AC line data
        f.write("%% AC branch data\n")
        f.write("%    fbus    tbus    r    x    b    rateA    rateB    rateC    ratio    angle    status    angmin    angmax\n")
        f.write("mpc.branch = [\n")
        for line in line_ac_data:
            f.write(f"    {line['fbus']}     {line['tbus']}     {line['r']}     {line['x']}     {line['b']}     {line['rateA']}     {line['rateB']}     {line['rateC']}     {line['ratio']}     {line['angle']}     {line['status']}     {line['angmin']}     {line['angmax']};\n")
        f.write("];\n\n")
        
        f.write("%% DC grid topology\n")
        f.write(f"mpc.dcpol = {dcpol};")
       
        
        f.write("%% DC bus data\n")
        f.write("%column_names%   busdc_i    grid    Pdc    Vdc    basekVdc    Vdcmax    Vdcmin    Cdc\n")
        f.write("mpc.busdc = [\n")
        for node in node_dc_data:
            f.write(f"    {node['busdc_i']}     {node['grid']}     {node['Pdc']}     {node['Vdc']}     {node['basekVdc']}     {node['Vdcmax']}     {node['Vdcmin']}     {node['Cdc']};\n")
        f.write("];\n\n")
        
        
        # For DC line data
        f.write("%% DC branch data\n")
        f.write("%column_names%    fbusdc    tbusdc    r    l    c    rateA    rateB    rateC    status\n")

        f.write("mpc.branchdc = [\n")
        for line in line_dc_data:
            f.write(f"    {line['fbusdc']}     {line['tbusdc']}     {line['r']}     {line['l']}     {line['c']}     {line['rateA']}     {line['rateB']}     {line['rateC']}     {line['status']};\n")
        f.write("];\n\n")
        
        # For AC/DC converter data
        f.write("%% AC/DC converter data\n")
        f.write("%column_names%    busdc_i    busac_i    type_dc    type_ac    P_g    Q_g    islcc    Vtar    rtf    xtf    transformer    tm    bf    filter    rc    xc    reactor    basekVac    Vmmax    Vmmin    Imax    status    LossA    LossB    LossCrec    LossCinv    droop    Pdcset    Vdcset    dVdcset    Pacmax    Pacmin    Qacmax    Qacmin\n")

        f.write("mpc.convdc = [\n")
        for conv in conv_data:
            f.write(f"    {conv['busdc_i']}     {conv['busac_i']}     {conv['type_dc']}     {conv['type_ac']}     {conv['P_g']}     {conv['Q_g']}     {conv['islcc']}     {conv['Vtar']}     {conv['rtf']}     {conv['xtf']}     {conv['transformer']}     {conv['tm']}     {conv['bf']}     {conv['filter']}     {conv['rc']}     {conv['xc']}     {conv['reactor']}     {conv['basekVac']}     {conv['Vmmax']}     {conv['Vmmin']}     {conv['Imax']}     {conv['status']}     {conv['LossA']}     {conv['LossB']}     {conv['LossCrec']}     {conv['LossCinv']}     {conv['droop']}     {conv['Pdcset']}     {conv['Vdcset']}     {conv['dVdcset']}     {conv['Pacmax']}     {conv['Pacmin']}     {conv['Qacmax']}     {conv['Qacmin']};\n")
        f.write("];\n\n")
        
        # For generator data
        f.write("%% Generator data\n")
        f.write("%    bus    Pg    Qg    Qmax    Qmin    Vg    mBase    status    Pmax    Pmin    Pc1    Pc2    Qc1min    Qc1max    Qc2min    Qc2max    ramp_agc    ramp_10    ramp_30    ramp_q    apf\n")

        f.write("mpc.gen = [\n")
        for gen in gen_data:
            f.write(f"    {gen['bus']}     {gen['Pg']}     {gen['Qg']}     {gen['Qmax']}     {gen['Qmin']}     {gen['Vg']}     {gen['mBase']}     {gen['status']}     {gen['Pmax']}     {gen['Pmin']}     {gen['Pc1']}     {gen['Pc2']}     {gen['Qc1min']}     {gen['Qc1max']}     {gen['Qc2min']}     {gen['Qc2max']}     {gen['ramp_agc']}     {gen['ramp_10']}     {gen['ramp_30']}     {gen['ramp_q']}     {gen['apf']};\n")
        f.write("];\n\n")
        
        # For generator cost data
        f.write("%% Generator cost data\n")
        f.write("%    2    startup    shutdown    n     c(n-1)    c(n-2)    c0\n")
        f.write("mpc.gencost = [\n")
        for gen_cost in gen_cost_data:
            f.write(f"    {gen_cost['type']}     {gen_cost['startup']}     {gen_cost['shutdown']}     {gen_cost['n']}     {gen_cost['c(n-1)']}     {gen_cost['c(n-2)']}     {gen_cost['c0']};\n")
        f.write("];\n\n")
        
        f.write("%% Adds current ratings to branch matrix\n")
        f.write("%    c_rating_a\n")
        f.write("mpc.branch_currents = [\n")
        
        for line in line_ac_data:
            f.write(f"{line['rateA']};\n")
        
        f.write("];\n")
        
 
