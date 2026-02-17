# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 14:58:18 2024

@author: BernardoCastro
"""

import numpy as np
import pyomo.environ as pyo
import pandas as pd
import time
import os
from concurrent.futures import ThreadPoolExecutor

from .Class_editor import analyse_grid

from .ACDC_OPF_NL_model import OPF_create_NLModel_ACDC,TEP_variables
from .AC_OPF_L_model import OPF_create_LModel_AC,ExportACDC_Lmodel_toPyflowACDC
from .ACDC_OPF import pyomo_model_solve,OPF_obj,OPF_obj_L,obj_w_rule,ExportACDC_NLmodel_toPyflowACDC,calculate_objective,reset_to_initialize,calculate_objective_from_model

from .Graph_and_plot import save_network_svg


__all__ = [
    'update_grid_scenario_frame',
    'expand_elements_from_pd',
    'repurpose_element_from_pd',
    'update_attributes',
    'Expand_element',
    'Translate_pd_TEP',
    'transmission_expansion',
    'linear_transmission_expansion',
    'multi_scenario_TEP',
    'export_TEP_multiScenario_results_to_excel',
    'alpha_paretto',
    'rate_sensitivity',
    'kappa_sensitivity',
    'comprehensive_sensitivity_analysis'
]

def pack_variables(*args):
    return args


def update_grid_scenario_frame(grid,ts,t,n_clusters,clustering):
    idx=t-1
    typ = ts.type
    
    if clustering:
        ts_data = ts.data_clustered[n_clusters]
    else:
        ts_data = ts.data
    
    if typ == 'a_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.a_base = ts_data[idx]
                break
    elif typ == 'b_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.b = ts_data[idx]
                break
    elif typ == 'c_CG':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.c = ts_data[idx]
                break
    elif typ == 'PGL_min':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.PGL_min_base= ts_data[idx]
                break
    elif typ == 'PGL_max':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.PGL_max= ts_data[idx]
                break
    if typ == 'price':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.price = ts_data[idx]
                break  # Stop after assigning to the correct price_zone
        for node in grid.nodes_AC:
            if ts.element_name == node.name:
                node.price = ts_data[idx]
                break  # Stop after assigning to the correct node    
    
    elif typ == 'Load':
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.PLi_factor = ts_data[idx]
                break  # Stop after assigning to the correct price_zone
        for node in grid.nodes_AC:
            if ts.element_name == node.name:
                node.PLi_factor = ts_data[idx]
                break  # Stop after assigning to the correct node
        for node in grid.nodes_DC:
            if ts.element_name == node.name:
                node.PLi_factor = ts_data[idx]
                break  # Stop after assigning to the correct node

    elif typ in ['WPP', 'OWPP','SF','REN','Solar']:
        for zone in grid.RenSource_zones:
            if ts.element_name == zone.name:
                zone.PRGi_available = ts_data[idx]
                # print(ts_data[idx])
                break  # Stop after assigning to the correct zone
        for rs in grid.RenSources:
            if ts.element_name == rs.name:
                rs.PRGi_available = ts_data[idx]
                break  # Stop after assigning to the correct node

def expand_elements_from_pd(grid,exp_elements):
    """
    This function iterates over exp_elements and applies Expand_element 
    with the corresponding columns (N_i, Life_time, and base_cost) if available.
    
    Parameters:
    exp_elements: DataFrame containing element data.
    grid: The grid object to be passed to Expand_element.
    """
    
    # Helper function to get the column value if it exists
    def get_column_value(row, col_name):
        return row[col_name] if col_name in row.index else None
    
    # Apply the Expand_element function for each element in exp_elements
    exp_elements.iloc[:, 0].apply(lambda name: Expand_element(
        grid,
        name,
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'N_b'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'N_i'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'N_max'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'Life_time'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'base_cost'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'per_unit_cost'),
        get_column_value(exp_elements.loc[exp_elements[exp_elements.iloc[:, 0] == name].index[0], :], 'exp'),
        False
    ))
    grid.Update_Graph_AC()
    grid.create_Ybus_AC() 

def repurpose_element_from_pd(grid,rec_elements):
    from .Class_editor import change_line_AC_to_reconducting
    
    def get_column_value(row, col_name,default_value=None):
        return row[col_name] if col_name in row.index else default_value
    
    # Apply the Expand_element function for each element in exp_elements
    rec_elements.iloc[:, 0].apply(lambda name: change_line_AC_to_reconducting(
        grid,
        name,
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'r_new',default_value=0.001),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'x_new',default_value=0.001),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'g_new',default_value=0),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'b_new',default_value=0),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'MVA_rating_new',default_value=99999),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'Life_time',default_value=1),
        get_column_value(rec_elements.loc[rec_elements[rec_elements.iloc[:, 0] == name].index[0], :], 'base_cost',default_value=0),
        False
            
    ))
    grid.Update_Graph_AC()
    grid.create_Ybus_AC()    


def update_attributes(element, N_b,N_i, N_max, Life_time, base_cost, per_unit_cost, exp):
   """Updates the attributes of the given element if not None."""
   if N_b is not None:
       if N_i is None:
           N_i = N_b
       if hasattr(element, 'np_line'):
           element.np_line_b = N_b
           element.np_line = N_b
       if hasattr(element, 'np_line_i'):
           element.np_line_i = N_i
       if hasattr(element, 'NumConvP'):
           element.NumConvP_b = N_b  
           element.NumConvP = N_b
       if hasattr(element, 'NumConvP_i'):
           element.NumConvP_i = N_i      # Only set if it exists
       if hasattr(element, 'np_gen'):
           element.np_gen_b = N_b
           element.np_gen = N_b
       if hasattr(element, 'np_gen_i'):
           element.np_gen_i = N_i
       if hasattr(element, 'np_rsgen'):
           element.np_rsgen_b = N_b
           element.np_rsgen = N_b
       if hasattr(element, 'np_rsgen_i'):
           element.np_rsgen_i = N_i
       
   if N_max is not None:
       if hasattr(element, 'np_line_max'):
           element.np_line_max = N_max
       if hasattr(element, 'NumConvP_max'):
           element.NumConvP_max = N_max  
       if hasattr(element, 'np_gen_max'):
           element.np_gen_max = N_max     
       if hasattr(element, 'np_rsgen_max'):
           element.np_rsgen_max = N_max     
    
   if Life_time is not None:
       element.life_time = Life_time
   
   if per_unit_cost is not None:
       if hasattr(element, 'cost_perMWkm'):
           element.cost_perMWkm = per_unit_cost
       if hasattr(element, 'cost_perMVAkm'):
           element.cost_perMVAkm = per_unit_cost    
       if hasattr(element, 'cost_perMVA'):
           element.cost_perMVA = per_unit_cost
   if base_cost is not None:
       element.base_cost = base_cost
   else:
       base_cost_calculation(element)
   if exp is not None:
       element.exp = exp


def Expand_element(grid,name,N_b=None,N_i=None,N_max=None,Life_time=None,base_cost=None,per_unit_cost=None, exp=None,update_grid=True):
    
    if N_max is None:
        N_max= N_b+20
    
    for l in grid.lines_AC:
        if name == l.name:
            from .Class_editor import change_line_AC_to_expandable
            exp_l=change_line_AC_to_expandable(grid, name,update_grid)
            exp_l.np_line_opf = True
            update_attributes(exp_l, N_b,N_i, N_max,Life_time, base_cost, per_unit_cost, exp)
            continue

    for l in grid.lines_DC:
        if name == l.name:
            l.np_line_opf = True
            update_attributes(l, N_b, N_i, N_max,Life_time, base_cost, per_unit_cost, exp)
            continue
            
    for cn in grid.Converters_ACDC:
        if name == cn.name:
            cn.NUmConvP_opf = True
            update_attributes(cn, N_b, N_i, N_max, Life_time, base_cost, per_unit_cost, exp)
            continue
        
    for gen in grid.Generators:
        if name == gen.name:
            gen.np_gen_opf = True
            update_attributes(gen, N_b, N_i, N_max, Life_time, base_cost, per_unit_cost, exp)
            continue
    for rs in grid.RenSources:
        if name == rs.name:
            rs.np_rsgen_opf = True
            update_attributes(rs, N_b, N_i, N_max, Life_time, base_cost, per_unit_cost, exp)
            continue
def base_cost_calculation(element):
    from .Classes import Exp_Line_AC 
    if isinstance(element, Exp_Line_AC):
        element.base_cost= element.cost_perMVAkm*element.Length_km*element.MW_rating

    from .Classes import Line_DC 
    if isinstance(element, Line_DC):
        element.base_cost= element.cost_perMWkm*element.Length_km*element.MW_rating

    from .Classes import AC_DC_converter
    if isinstance(element, AC_DC_converter):
        element.base_cost= element.cost_perMVA*element.MVA_max
    
    from .Classes import Gen_AC
    if isinstance(element, Gen_AC):
        if element.Max_S is not None:
            element.base_cost= element.cost_perMVA*element.Max_S
        elif element.Max_pow_gen !=0:
            element.base_cost= element.cost_perMVA*element.Max_pow_gen
        else:
            element.base_cost= element.cost_perMVA*element.Max_pow_genR
    from .Classes import Ren_Source
    if isinstance(element, Ren_Source):
        element.base_cost= element.cost_perMVA*element.Max_S

def Translate_pd_TEP(grid):
    """Translation of element wise to internal numbering"""
    # Price_Zones
    price_zone2node, price_zone_prices, price_zone_as, price_zone_bs, PGL_min, PGL_max, PL_price_zone = {}, {}, {}, {}, {}, {}, {}
    nn_M, node2price_zone, lista_M = 0, {}, []
    
    for m in grid.Price_Zones:
        price_zone2node[m.price_zone_num] = []
        nn_M += 1
        price_zone_prices[m.price_zone_num] = m.price
        price_zone_as[m.price_zone_num] = m.a
        price_zone_bs[m.price_zone_num] = m.b
        PGLmin = m.PGL_min
        PGLmax = m.PGL_max
        import_M = m.import_pu_L
        export_M = m.export_pu_G * (sum(node.PGi_ren + node.Max_pow_gen for node in m.nodes_AC))
        PL_price_zone[m.price_zone_num] = 0
        for n in m.nodes_AC:
            price_zone2node[m.price_zone_num].append(n.nodeNumber)
            node2price_zone[n.nodeNumber] = m.price_zone_num
            PL_price_zone[m.price_zone_num] += n.PLi
        PGL_min[m.price_zone_num] = max(PGLmin, -import_M * PL_price_zone[m.price_zone_num])
        PGL_max[m.price_zone_num] = min(PGLmax, export_M)
    lista_M = list(range(0, nn_M))

    Price_Zone_Lists = pack_variables(lista_M, node2price_zone, price_zone2node)
    Price_Zone_lim = pack_variables(price_zone_as, price_zone_bs, PGL_min, PGL_max)

   
    Price_Zone_info = pack_variables(Price_Zone_Lists, Price_Zone_lim)

    return Price_Zone_info

def get_TEP_variables(grid):
    
    NumConvP,NumConvP_i,NumConvP_max={},{},{}
    S_limit_conv={}
    P_lineDC_limit ={}
    NP_lineDC,NP_lineDC_i,NP_lineDC_max ={},{},{}
    NP_lineAC,NP_lineAC_i,NP_lineAC_max = {},{},{}
    Line_length ={}
    REC_branch ={}


    for l in grid.lines_AC_rec:
        REC_branch[l.lineNumber] = 0 if not l.rec_branch  else 1

    for l in grid.lines_AC_exp:
        NP_lineAC[l.lineNumber]     = l.np_line
        NP_lineAC_i[l.lineNumber]   = (
            l.np_line if not l.np_line_opf 
            else max(l.np_line,min(l.np_line_i , l.np_line_max))
        )
        NP_lineAC_max[l.lineNumber]   = l.np_line_max

    ct_ini = {}
    for l in grid.lines_AC_ct:
        for ct in range(len(l._cable_types)):
            ct_ini[l.lineNumber, ct] = 1 if ct == l.active_config else 0  
             
    for conv in grid.Converters_ACDC:
        NumConvP [conv.ConvNumber]  = conv.NumConvP 
        NumConvP_i[conv.ConvNumber] = (
            conv.NumConvP if not conv.NUmConvP_opf 
            else max(conv.NumConvP,min(conv.NumConvP_i , conv.NumConvP_max))
        )
        NumConvP_max[conv.ConvNumber] = conv.NumConvP_max
        S_limit_conv[conv.ConvNumber] = conv.MVA_max/grid.S_base
    for l in grid.lines_DC:
        P_lineDC_limit[l.lineNumber]  = l.MW_rating/grid.S_base
        NP_lineDC[l.lineNumber]     = l.np_line 
        NP_lineDC_i[l.lineNumber]   = (
            l.np_line if not l.np_line_opf 
            else max(l.np_line,min(l.np_line_i , l.np_line_max))
        )
        NP_lineDC_max[l.lineNumber]   = l.np_line_max
        Line_length[l.lineNumber]     = l.Length_km
        
    np_gen={}
    np_gen_max={}
    for gen in grid.Generators:
        np_gen_max[gen.genNumber] = gen.np_gen_max
        np_gen[gen.genNumber] = gen.np_gen
    
    np_gen_DC={}
    np_gen_max_DC={}
    for gen in grid.Generators_DC:
        np_gen_max_DC[gen.genNumber_DC] = gen.np_gen_max
        np_gen_DC[gen.genNumber_DC] = gen.np_gen
    
    np_rsgen={}
    np_rsgen_max={}
    for rs in grid.RenSources:
        np_rsgen[rs.rsNumber] = rs.np_rsgen
        np_rsgen_max[rs.rsNumber] = rs.np_rsgen_max
    
    # Return as dictionary for easier extension and maintenance
    return {
        'converters': {
            'NumConvP': NumConvP,
            'NumConvP_i': NumConvP_i,
            'NumConvP_max': NumConvP_max,
            'S_limit_conv': S_limit_conv
        },
        'dc_lines': {
            'P_lineDC_limit': P_lineDC_limit,
            'NP_lineDC': NP_lineDC,
            'NP_lineDC_i': NP_lineDC_i,
            'NP_lineDC_max': NP_lineDC_max,
            'Line_length': Line_length
        },
        'ac_lines': {
            'NP_lineAC': NP_lineAC,
            'NP_lineAC_i': NP_lineAC_i,
            'NP_lineAC_max': NP_lineAC_max,
            'Line_length': Line_length,
            'REC_branch': REC_branch,
            'ct_ini': ct_ini
        },
        'generators': {
            'np_gen': np_gen,
            'np_gen_max': np_gen_max,
            'np_gen_DC': np_gen_DC,
            'np_gen_max_DC': np_gen_max_DC
        },
        'ren_sources': {
            'np_rsgen': np_rsgen,
            'np_rsgen_max': np_rsgen_max
        }
    }


def MS_TEP_constraints(model,grid):
    
    
    def NP_ACline_link(model,line,t):
        element=grid.lines_AC_exp[line]
        if element.np_line_opf:
            return model.NumLinesACP[line] ==model.scenario_model[t].NumLinesACP[line]
        else:
            return pyo.Constraint.Skip
    
    def NP_line_link(model,line,t):
        element=grid.lines_DC[line]
        if element.np_line_opf:
            return model.NumLinesDCP[line] ==model.scenario_model[t].NumLinesDCP[line]
        else:
            return pyo.Constraint.Skip
    def NP_conv_link(model,conv,t):
        element=grid.Converters_ACDC[conv]
        if element.NUmConvP_opf:
            return model.NumConvP[conv] ==model.scenario_model[t].NumConvP[conv]
        else:
            return pyo.Constraint.Skip
    if grid.TEP_AC:
        model.NP_ACline_link_constraint = pyo.Constraint(model.lines_AC_exp,model.scenario_frames, rule=NP_ACline_link)

    if grid.DCmode:
        model.NP_line_link_constraint = pyo.Constraint(model.lines_DC,model.scenario_frames, rule=NP_line_link)
    if grid.ACmode and grid.DCmode:
        model.NP_conv_link_constraint = pyo.Constraint(model.conv,model.scenario_frames, rule=NP_conv_link)
    
    def NP_ACline_rec_link(model,line,t):
        element=grid.lines_AC_rec[line]
        if element.rec_line_opf:
            return model.rec_branch[line] ==model.scenario_model[t].rec_branch[line]
        else:
            return pyo.Constraint.Skip
    if grid.REC_AC:
        model.NP_ACline_rec_link_constraint = pyo.Constraint(model.lines_AC_rec,model.scenario_frames, rule=NP_ACline_rec_link) 


    def NP_ACline_ct_link(model,line,ct,t):
        element=grid.lines_AC_ct[line]
        if element.array_opf:
            return model.ct_branch[line,ct] ==model.scenario_model[t].ct_branch[line,ct]
        else:
            return pyo.Constraint.Skip
    if grid.CT_AC:
        model.NP_ACline_ct_link_constraint = pyo.Constraint(model.lines_AC_ct,model.ct_set,model.scenario_frames, rule=NP_ACline_ct_link)

def _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule,PV_set=False):

    analyse_grid(grid)
    
    weights_def, PZ = obj_w_rule(grid,ObjRule,True)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate
   
    model = pyo.ConcreteModel()
    model.name = "TEP MTDC AC/DC hybrid OPF"

    OPF_create_NLModel_ACDC(model,grid,PV_set=PV_set,Price_Zones=PZ,TEP=True)
    

    obj_TEP = TEP_obj(model,grid,NPV)
    obj_OPF = OPF_obj(model,grid,weights_def,True)
    

    return model, obj_TEP, obj_OPF,weights_def,PZ


def GEN_balance_constraints(model,grid):
    
    if all(v == 1 for v in grid.generation_type_limits.values()):
        return  # All limits are 1, no constraints needed
    
    grid.generation_type_limits = {k.lower(): v for k, v in grid.generation_type_limits.items()}
    model.gen_types = pyo.Set(initialize=list(grid.generation_type_limits.keys()))
    model.gen_type_limits = pyo.Param(model.gen_types,initialize=grid.generation_type_limits)
    
    # Helper function to normalize type names to lowercase
    def normalize_type(type_name):
        return type_name.lower() if type_name else None
    
    # Calculate max installed capacity for each type
    def gen_type_max_capacity_rule(model, gen_type):
        # Sum generator max capacities for this type (normalize gen.gen_type to lowercase)
        gen_capacity = sum(
            gen.Max_pow_gen * model.np_gen[gen.genNumber] 
            for gen in grid.Generators 
            if normalize_type(gen.gen_type) == gen_type
        )
        
        # Sum renewable source max capacities for this type (normalize rs.rs_type to lowercase)
        ren_capacity = sum(
            rs.PGi_ren_base * model.np_rsgen[rs.rsNumber]
            for rs in grid.RenSources
            if normalize_type(rs.rs_type) == gen_type
        )
        
        return gen_capacity + ren_capacity
    
    model.gen_type_max_capacity = pyo.Expression(model.gen_types, rule=gen_type_max_capacity_rule)
    
    # Calculate total max capacity across all types
    def total_max_capacity_rule(model):
        return sum(model.gen_type_max_capacity[gt] for gt in model.gen_types)
    
    model.total_max_capacity = pyo.Expression(rule=total_max_capacity_rule)
    
    # Constraint: each type's max capacity <= total_max_capacity * type_limit
    def gen_type_balance_rule(model, gen_type):
        return model.gen_type_max_capacity[gen_type] <= model.total_max_capacity * model.gen_type_limits[gen_type]
    
    model.gen_type_balance_constraint = pyo.Constraint(model.gen_types, rule=gen_type_balance_rule)
    
def transmission_expansion(grid,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,ObjRule=None,solver='bonmin',time_limit=99999,tee=False,export=True,PV_set=False,alpha=None,callback=False,solver_options=None,obj_scaling=1.0):
    grid.reset_run_flags()
    t1 = time.perf_counter()
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule,PV_set)
    
    present_value =   Hy*(1 - (1 + discount_rate) ** -n_years) / discount_rate
    if NPV:
        obj_OPF *=present_value

    if alpha is not None:
        obj_TEP *= alpha
        obj_OPF *= (1-alpha)

    total_cost = obj_TEP + obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    t2 = time.perf_counter()  
    t_modelcreate = t2-t1
    
    # model.obj.pprint()

    model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,time_limit,callback=callback,solver_options=solver_options)
    
    t1 = time.perf_counter()
    if export:
        if grid.ACmode:
            grid.create_Ybus_AC()
        if grid.DCmode:
            grid.create_Ybus_DC()   
        ExportACDC_NLmodel_toPyflowACDC(model, grid, PZ,TEP=True)
        for obj in weights_def:
            weights_def[obj]['v']=calculate_objective(grid,obj,True)
            weights_def[obj]['NPV']=weights_def[obj]['v']*present_value
    t2 = time.perf_counter() 

    t_modelexport = t2-t1

      
    grid.TEP_run=True
    grid.OPF_obj = weights_def

    timing_info = {
    "create": t_modelcreate,
    "solve": solver_stats['time'],
    "export": t_modelexport,
    }
    return model, model_results , timing_info, solver_stats

def linear_transmission_expansion(grid,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,ObjRule=None,solver='gurobi',time_limit=300,tee=False,export=True,fs=False,obj_scaling=1.0):
    grid.reset_run_flags()
    analyse_grid(grid)
    
    weights_def, _ = obj_w_rule(grid,ObjRule,True)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate
   
    t1 = time.perf_counter()
    model = pyo.ConcreteModel()
    model.name = "TEP MTDC linear AC OPF"

    OPF_create_LModel_AC(model,grid,TEP=True)
    

    obj_TEP = TEP_obj(model,grid,NPV)
    obj_OPF = OPF_obj_L(model,grid,weights_def)
    
    present_value =   Hy*(1 - (1 + discount_rate) ** -n_years) / discount_rate
    if NPV:
        obj_OPF *=present_value
    

    total_cost = obj_TEP + obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    t2 = time.perf_counter()  
    t_modelcreate = t2-t1

   
    # model.obj.pprint()
    t3 = time.perf_counter()
    model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,time_limit,callback=fs)
    
    if model_results is None:
        return None, None, None, None

    
    t1 = time.perf_counter()
    if export:
        ExportACDC_Lmodel_toPyflowACDC(model, grid, solver_results=model_results, tee=tee)
        for obj in weights_def:
            weights_def[obj]['v']=calculate_objective(grid,obj,True)
            weights_def[obj]['NPV']=weights_def[obj]['v']*present_value
    t2 = time.perf_counter() 

    t_modelexport = t2-t1

      
    grid.TEP_run=True
    grid.OPF_obj = weights_def

    timing_info = {
    "create": t_modelcreate,
    "solve":  solver_stats['time'] if solver_stats['time'] is not None else t1-t3,
    "export": t_modelexport,
    }
    return model, model_results , timing_info, solver_stats
    


def _initialize_MS_STEP_sets_model(model,grid):    
    if grid.DCmode:
        model.lines_DC    = pyo.Set(initialize=list(range(0, grid.nl_DC)))
    if grid.ACmode and grid.DCmode:
        model.conv        = pyo.Set(initialize=list(range(0, grid.nconv)))
    if grid.TEP_AC:
        model.lines_AC_exp= pyo.Set(initialize=list(range(0,grid.nle_AC)))
    if grid.REC_AC:
        model.lines_AC_rec= pyo.Set(initialize=list(range(0,grid.nlr_AC)))
    if grid.CT_AC:
        model.lines_AC_ct = pyo.Set(initialize=list(range(0,grid.nct_AC)))
        model.ct_set = pyo.Set(initialize=list(range(0,len(grid.Cable_options[0].cable_types))))
    if grid.GPR:
        model.gen_AC = pyo.Set(initialize=list(range(0,grid.n_gen)))

def alpha_paretto(grid,steps,ObjRule,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,solver='bonmin',time_limit=99999,tee=False,save_name=None,obj_scaling=1.0):
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule)
    present_value =   Hy*(1 - (1 + discount_rate) ** -n_years) / discount_rate
    if NPV:
        obj_OPF *=present_value
    results = []
    model.alpha = pyo.Param(initialize=0,mutable=True)
    modified_obj_TEP = obj_TEP * model.alpha
    modified_obj_OPF = obj_OPF * (1-model.alpha)

    total_cost = modified_obj_TEP + modified_obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    
    # Store initial values for resetting
    
    initial_values = {}
    for var_obj in model.component_objects(pyo.Var, active=True):
        initial_values[var_obj.name] = {}
        for index in var_obj:
            initial_values[var_obj.name][index] = var_obj[index].value
    
    # Allow either an integer (count) or an iterable of alphas
    if isinstance(steps, int):
        steps_iter = np.linspace(0.0, 1.0, steps)
    else:
        steps_iter = np.asarray(steps, dtype=float).ravel()

    for a in steps_iter:
        print(f'Running alpha: {a}')
        # Reset model variables to initial values
        reset_to_initialize(model, initial_values)
        model.alpha.set_value(a)
        model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,time_limit)
        
        row = {
            'alpha': a,
            'obj_TEP': pyo.value(obj_TEP),
            'obj_OPF': pyo.value(obj_OPF),
            'Total_cost': pyo.value(model.obj) * obj_scaling,
            'Time': solver_stats.get('time', None) if solver_stats is not None else None
        }
        
        results.append(row)

        if save_name is not None:
            save_path = f'{save_name}_alpha_{a}.svg'
            if grid.TEP_AC:
                lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}
                for line in grid.lines_AC_exp:
                    l = line.lineNumber
                    line.np_line = lines_AC_TEP[l]
            for line in grid.lines_DC:
                l = line.lineNumber
                line.np_line = pyo.value(model.NumLinesDCP[l])
            for conv in grid.Converters_ACDC:
                c = conv.ConvNumber
                conv.NUmConvP = pyo.value(model.NumConvP[c])

            save_network_svg(grid,save_path)
    
    
    df = pd.DataFrame(results)
    
    # Add normalized columns
    df['norm_TEP'] = df['obj_TEP'] / df['obj_TEP'].max()
    df['norm_OPF'] = df['obj_OPF'] / df['obj_OPF'].max()
    
    
    
    return df

def rate_sensitivity(grid,steps,ObjRule,min_rate=0.0,max_rate=0.1,NPV=True,n_years=25,Hy=8760,solver='bonmin',time_limit=99999,tee=False,obj_scaling=1.0):
   
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,min_rate,ObjRule)
    
    results = []
    model.discount_rate = pyo.Param(initialize=min_rate,mutable=True)
    present_value =   Hy*(1 - (1 + model.discount_rate) ** -n_years) / model.discount_rate
    

    obj_OPF  *= present_value

    total_cost = obj_TEP + obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    
    # Store initial values for resetting
    
    initial_values = {}
    for var_obj in model.component_objects(pyo.Var, active=True):
        initial_values[var_obj.name] = {}
        for index in var_obj:
            initial_values[var_obj.name][index] = var_obj[index].value
    
    # Allow either an integer (count) or an iterable of alphas
    if isinstance(steps, int):
        steps_iter = np.linspace(min_rate, max_rate, steps)
    else:
        steps_iter = np.asarray(steps, dtype=float).ravel()

    for rate in steps_iter:
        print(f'Running rate: {rate}')
        # Reset model variables to initial values
        reset_to_initialize(model, initial_values)
        model.discount_rate.set_value(rate)
        model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,time_limit)
        
        row = {
            'rate': rate,
            'obj_TEP': pyo.value(obj_TEP),
            'obj_OPF': pyo.value(obj_OPF),
            'Total_cost': pyo.value(model.obj) * obj_scaling,
            'Time': solver_stats.get('time', None) if solver_stats is not None else None
        }
        
        results.append(row)
    
    
    df = pd.DataFrame(results)
    
    # Add normalized columns
    df['norm_TEP'] = df['obj_TEP'] / df['obj_TEP'].max()
    df['norm_OPF'] = df['obj_OPF'] / df['obj_OPF'].max()
    
    
    
    return df

def kappa_sensitivity(grid,steps,ObjRule,min_kappa=0.0,max_kappa=1.0,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,solver='bonmin',time_limit=99999,tee=False,obj_scaling=1.0):
   
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule)
    
    results = []
    model.kappa = pyo.Param(initialize=min_kappa,mutable=True)
    present_value =   Hy*(1 - (1 + model.discount_rate) ** -n_years) / model.discount_rate
    

    obj_OPF  *= present_value
    obj_TEP *= model.kappa
    total_cost = obj_TEP + obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    
    # Store initial values for resetting
    
    initial_values = {}
    for var_obj in model.component_objects(pyo.Var, active=True):
        initial_values[var_obj.name] = {}
        for index in var_obj:
            initial_values[var_obj.name][index] = var_obj[index].value
    
    # Allow either an integer (count) or an iterable of alphas
    if isinstance(steps, int):
        steps_iter = np.linspace(min_kappa, max_kappa, steps)
    else:
        steps_iter = np.asarray(steps, dtype=float).ravel()

    for kappa in steps_iter:
        print(f'Running rate: {kappa}')
        # Reset model variables to initial values
        reset_to_initialize(model, initial_values)
        model.kappa.set_value(kappa)
        model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,time_limit)
        
        row = {
            'kappa': kappa,
            'obj_TEP': pyo.value(obj_TEP),
            'obj_OPF': pyo.value(obj_OPF),
            'Total_cost': pyo.value(model.obj) * obj_scaling,
            'Time': solver_stats.get('time', None) if solver_stats is not None else None
        }
        
        results.append(row)
    
    
    df = pd.DataFrame(results)
    
    # Add normalized columns
    df['norm_TEP'] = df['obj_TEP'] / df['obj_TEP'].max()
    df['norm_OPF'] = df['obj_OPF'] / df['obj_OPF'].max()
    
    
    
    return df


def comprehensive_sensitivity_analysis(
    grid, 
    ObjRule,
    alpha_steps=None, 
    rate_steps=None, 
    kappa_steps=None,
    alpha_range=(0.0, 1.0),
    rate_range=(0.01, 0.1), 
    kappa_range=(0.0, 1.0),
    n_years=25, 
    Hy=8760, 
    discount_rate=0.02,
    solver='bonmin', 
    time_limit=99999, 
    tee=False,
    obj_scaling=1.0
):
    """
    Comprehensive sensitivity analysis combining alpha, rate, and kappa variations.
    
    Parameters:
    - alpha_steps, rate_steps, kappa_steps: Number of steps or specific values for each parameter
    - alpha_range, rate_range, kappa_range: (min, max) tuples for parameter ranges
    """
    # Prepare base model
    model, obj_TEP, obj_OPF, weights_def, PZ = _prepare_TEP_model(grid, True, n_years, Hy, discount_rate, ObjRule)
    
    # Create mutable parameters
    model.alpha = pyo.Param(initialize=0.5, mutable=True)
    model.discount_rate = pyo.Param(initialize=discount_rate, mutable=True) 
    model.kappa = pyo.Param(initialize=0.5, mutable=True)
    
    # Store initial values
    initial_values = {}
    for var_obj in model.component_objects(pyo.Var, active=True):
        initial_values[var_obj.name] = {}
        for index in var_obj:
            initial_values[var_obj.name][index] = var_obj[index].value
    
    results = []
    
    # Generate parameter ranges
    alpha_values = _generate_steps(alpha_steps, alpha_range) if alpha_steps is not None else [None]
    rate_values = _generate_steps(rate_steps, rate_range) if rate_steps is not None else [None] 
    kappa_values = _generate_steps(kappa_steps, kappa_range) if kappa_steps is not None else [None]
    # Set parameters
    
    # Calculate present value with current discount rate
    
    present_value = Hy * (1 - (1 + model.discount_rate) ** -n_years) / model.discount_rate
    
    obj_OPF  *= present_value
    obj_TEP *= model.kappa


    # Modify objectives
    modified_obj_TEP = obj_TEP * model.alpha
    modified_obj_OPF = obj_OPF * (1 - model.alpha)
    
    total_cost = modified_obj_TEP + modified_obj_OPF
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
                
    # Nested loops
    for alpha in alpha_values:
        print(f'Running alpha: {alpha}')
        for rate in rate_values:
            print(f'Running rate: {rate}')
            for kappa in kappa_values:
                print(f'Running: alpha={alpha}, rate={rate}, kappa={kappa}')
                if alpha is not None:
                    model.alpha.set_value(alpha)
                if rate is not None:
                    model.discount_rate.set_value(rate)
                if kappa is not None:
                    model.kappa.set_value(kappa)
                # Reset model
                reset_to_initialize(model, initial_values)
                
                
                # Solve
                model_results, solver_stats = pyomo_model_solve(model, grid, solver, tee, time_limit)
                
                # Store results
                row = {
                    'alpha': alpha,
                    'rate': rate, 
                    'kappa': kappa,
                    'obj_TEP': pyo.value(obj_TEP),
                    'obj_OPF': pyo.value(obj_OPF),
                    'Total_cost': pyo.value(model.obj) * obj_scaling,
                    'Time': solver_stats.get('time', None) if solver_stats is not None else None
                }
                results.append(row)
    
    df = pd.DataFrame(results)
    
    # Add normalized columns
    df['norm_TEP'] = df['obj_TEP'] / df['obj_TEP'].max()
    df['norm_OPF'] = df['obj_OPF'] / df['obj_OPF'].max()
    
    return df

def _generate_steps(steps, range_tuple):
    """Helper function to generate parameter values"""
    if isinstance(steps, int):
        return np.linspace(range_tuple[0], range_tuple[1], steps)
    else:
        return np.asarray(steps, dtype=float).ravel()   

def create_scenarios(model,grid,Price_Zones,weights_def,n_clusters,clustering,NPV,n_years,discount_rate,Hy,alpha,limit_flow_rate,obj_scaling=1.0):
       
    
    from .Time_series import  _modify_parameters    
    
    w={}

    base_model = pyo.ConcreteModel()
    OPF_create_NLModel_ACDC(base_model,grid,PV_set=False,Price_Zones=Price_Zones,TEP=True,limit_flow_rate=limit_flow_rate)
    
    
    for t in model.scenario_frames:
        if t == 1:
            s=1
        base_model_copy = base_model.clone()
        model.scenario_model[t].transfer_attributes_from(base_model_copy)
        
        for ts in grid.Time_series:
            update_grid_scenario_frame(grid,ts,t,n_clusters,clustering)
        
        # After all time series are updated, ensure a and PGL_min are recalculated
        # This is critical because a_base and PGL_min_base setters trigger calculations
        # that may use stale values if called in the wrong order
        for price_zone in grid.Price_Zones:
            price_zone.update_a()

        _modify_parameters(grid,model.scenario_model[t],Price_Zones)
        
        TEP_subObj(model.scenario_model[t],grid,weights_def)
        if clustering:
            w[t]= float(grid.Clusters[n_clusters]['Weight'][t-1])

        elif any(ts.element_name == 'TEP_w' for ts in grid.Time_series):
            w[t] = next(ts.data[t-1] for ts in grid.Time_series if ts.element_name == 'TEP_w')
        else:
            num_scenario_frames = len(model.scenario_frames)
            w[t]=1/num_scenario_frames
    
    _initialize_MS_STEP_sets_model(model,grid)
    TEP_variables(model,grid)
    
    MS_TEP_constraints(model,grid)

    
    model.weights = pyo.Param(model.scenario_frames, initialize=w)
    obj_TEP = TEP_obj(model,grid,NPV)
    obj_weighted = weighted_subobj(model,NPV,n_years,discount_rate)
    
    if alpha is None:
        total_cost = obj_TEP + Hy*obj_weighted
    else:    
        total_cost = obj_TEP*alpha + Hy*obj_weighted*(1-alpha)
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    s=1

def multi_scenario_TEP(grid,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,clustering_options=None,ObjRule=None,solver='bonmin',tee=False,callback=False,alpha=None,limit_flow_rate=True,obj_scaling=1.0):
    
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule,True)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate
    if tee:
        print('Trying clustering')
    try:
        from .Time_series_clustering import cluster_analysis
        n_clusters,clustering = cluster_analysis(grid,clustering_options)
        if ('print_details' in clustering_options and clustering_options['print_details']) or tee:
            print('Clustering done')
    except:
        n_clusters = len(grid.Time_series[0].data)
        clustering = False

    t1 = time.time()
    model = pyo.ConcreteModel()
    model.name        ="TEP TS MTDC AC/DC hybrid OPF"
    model.scenario_frames = pyo.Set(initialize=range(1, n_clusters + 1))
    
    #print(list(model.scenario_frames))
    model.scenario_model    = pyo.Block(model.scenario_frames)
    
    create_scenarios(model,grid,Price_Zones,weights_def,n_clusters,clustering,NPV,n_years,discount_rate,Hy,alpha,limit_flow_rate,obj_scaling=obj_scaling)

    t2 = time.time()  
    t_modelcreate = t2-t1
    if tee : 
        print('Model loaded') 
    model_results,solver_stats = pyomo_model_solve(model,grid,solver,tee,callback=callback)
    
    t1 = time.perf_counter()
    TEP_multiScenario_res = ExportACDC_TEP_MS_toPyflowACDC(model,grid,n_clusters,clustering,Price_Zones)   
    
    TEP_multiScenario_res['OPF_obj'] = weights_def
    
    t2 = time.perf_counter()  
    t_modelexport = t2-t1
        
    # TEP_multiScenario_res ={}
    
    grid.TEP_run=True
    grid.TEP_multiScenario_res = TEP_multiScenario_res
    grid.OPF_obj = weights_def
    
    timing_info = {
    "create": t_modelcreate,
    "solve": solver_stats['time'],
    "export": t_modelexport,
    }
    
    return model, model_results , timing_info, solver_stats , TEP_multiScenario_res


def TEP_subObj(scenario_model,grid,ObjRule):
    OnlyGen=True

    obj_rule= OPF_obj(scenario_model,grid,ObjRule,OnlyGen)
    scenario_model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    s=1
    

def TEP_obj(model,grid,NPV):
  
    def Gen_investments():
        Gen_Inv=0
        for g in model.gen_AC:
            gen = grid.Generators[g]
            if gen.np_gen_opf:
                Gen_Inv+=(model.np_gen[g]-model.np_gen_base[g])*gen.base_cost
        return Gen_Inv
    def Renewable_investments():
        Renewable_Inv=0
        for rs in model.ren_sources:
            ren_source = grid.RenSources[rs]
            if ren_source.np_rsgen_opf:
                Renewable_Inv+=(model.np_rsgen[rs]-model.np_rsgen_base[rs])*ren_source.base_cost
        return Renewable_Inv
    def AC_Line_investments():
        AC_Inv_lines=0
        for l in model.lines_AC_exp:
            line = grid.lines_AC_exp[l]
            if line.np_line_opf: 
               if NPV:
                   AC_Inv_lines+=(model.NumLinesACP[l]-model.NumLinesACP_base[l])*line.base_cost
               else: 
                   AC_Inv_lines+=(model.NumLinesACP[l]-model.NumLinesACP_base[l])*line.base_cost/line.life_time_hours
    
        return AC_Inv_lines
    
    def Repurposing_investments():
        Rep_Inv_lines=0
        for l in model.lines_AC_rec:
            line = grid.lines_AC_rec[l]
            if line.rec_line_opf:
                if NPV:
                    Rep_Inv_lines+=model.rec_branch[l]*line.base_cost
                else:
                    Rep_Inv_lines+=model.rec_branch[l]*line.base_cost/line.life_time_hours
        return Rep_Inv_lines
    
    def Cables_investments():
        Inv_lines=0
        for l in model.lines_DC:
           line= grid.lines_DC[l]
           if line.np_line_opf: 
             if NPV:
                 Inv_lines+=(model.NumLinesDCP[l]-model.NumLinesDCP_base[l])*line.base_cost
             else:
                 Inv_lines+=(model.NumLinesDCP[l]-model.NumLinesDCP_base[l])*line.base_cost/line.life_time_hours
        return Inv_lines

    def Array_investments():
        Inv_array=0
        for l in model.lines_AC_ct:
            line= grid.lines_AC_ct[l]
            if line.array_opf:
                if NPV:
                    for ct in model.ct_set:
                        Inv_array+=(model.ct_branch[l,ct])*line.base_cost[ct]
                else:
                    for ct in model.ct_set:
                        Inv_array+=(model.ct_branch[l,ct])*line.base_cost[ct]/line.life_time_hours
        
        return Inv_array
        
    
    def Converter_investments():
        Inv_conv=0
        for cn in model.conv:
            conv= grid.Converters_ACDC[cn]
            if conv.NUmConvP_opf:
               if NPV: 
                 Inv_conv+=(model.NumConvP[cn]-model.NumConvP_base[cn])*conv.base_cost
               else:
                 Inv_conv+=(model.NumConvP[cn]-model.NumConvP_base[cn])*conv.base_cost/conv.life_time_hours
        return Inv_conv
    
    if grid.GPR:
        inv_gen= Gen_investments()
    else:
        inv_gen=0
    
    if grid.rs_GPR:
        inv_rs = Renewable_investments()
    else:
        inv_rs = 0

    if grid.TEP_AC: 
        inv_line_AC = AC_Line_investments()
    else:
        inv_line_AC=0

    if grid.REC_AC:
        inv_line_AC_rec = Repurposing_investments()
    else:
        inv_line_AC_rec = 0

    def CT_limit_rule(model):
            # Upper bound: limit total cable types used
            return sum(model.ct_types[ct] for ct in model.ct_set) <= grid.cab_types_allowed
    
    def CT_limit_lower_bound_rule(model):
            # Lower bound: at least 1 cable type must be used (matching image formulation)
            return 1 <= sum(model.ct_types[ct] for ct in model.ct_set)
    def ct_cable_type_rule(model, line):
        l = grid.lines_AC_ct[line]
        if l.active_config >=0:
            return sum(model.ct_branch[line, ct] for ct in model.ct_set) == 1
        else:
            return sum(model.ct_branch[line, ct] for ct in model.ct_set) == 0
    
    
    def ct_types_upper_bound(model, ct):
        return sum(model.ct_branch[l, ct] for l in model.lines_AC_ct) <= len(model.lines_AC_ct) * model.ct_types[ct]

    def ct_types_lower_bound(model, ct):
        return model.ct_types[ct] <= sum(model.ct_branch[l, ct] for l in model.lines_AC_ct)
    if grid.CT_AC:
        
        model.ct_types_upper_bound = pyo.Constraint(model.ct_set, rule=ct_types_upper_bound)
        model.ct_types_lower_bound = pyo.Constraint(model.ct_set, rule=ct_types_lower_bound)
        model.CT_limit_constraint = pyo.Constraint(rule=CT_limit_rule)
        model.CT_limit_lower_bound_constraint = pyo.Constraint(rule=CT_limit_lower_bound_rule)
        model.ct_cable_type_constraint = pyo.Constraint(model.lines_AC_ct, rule=ct_cable_type_rule)    
        inv_array = Array_investments()
    else:
        inv_array = 0

    if grid.DCmode:
        inv_cable = Cables_investments()
    else:
        inv_cable = 0

    if grid.ACmode and grid.DCmode:
        inv_conv = Converter_investments()
    else:
        inv_conv  = 0

    return inv_gen+inv_line_AC+inv_line_AC_rec+inv_cable + inv_conv + inv_array + inv_rs

def weighted_subobj(model,NPV,n_years,discount_rate):
    # Calculate the weighted social cost for each scenario_model (subblock)
    weighted_subobj = 0
    present_value = (1 - (1 + discount_rate) ** -n_years) / discount_rate
        
    for t in model.scenario_frames:
        # Get the objective expression directly
        scenario_model_obj = model.scenario_model[t].obj.expr
        weighted_subobj += model.weights[t] * scenario_model_obj
            
        model.scenario_model[t].obj.deactivate()
    
    if NPV:
        weighted_subobj *= present_value
    
    return weighted_subobj


def get_price_zone_data(t, model, grid,n_clusters,clustering):
    row_data_price = {'Time_Frame': t}
    row_data_SC = {'Time_Frame': t}
    row_data_PN = {'Time_Frame': t}
    row_data_GEN = {'Time_Frame': t}
    # Collect price_zone data
    
    for m in grid.Price_Zones:
        nM = m.price_zone_num
        row_data_price[m.name] = np.round(np.float64(pyo.value(model.scenario_model[t].price_zone_price[nM])), decimals=2)
        
        from .Classes import Price_Zone
        from .Classes import MTDCPrice_Zone
        from .Classes import OffshorePrice_Zone
        gen=0
        for node in m.nodes_AC:
            nAC=node.nodeNumber
            PGi_ren = 0
            PGi_opt = sum(pyo.value(model.scenario_model[t].PGi_gen[gen.genNumber]) for gen in node.connected_gen)
            for rs in node.connected_RenSource:
                if rs.PGRi_linked:
                    rz = rs.Ren_source_zone
                    z  = grid.RenSource_zones[grid.RenSource_zones_dic[rz]]
                else:
                    z= rs
                try:    
                    if clustering:
                        factor = grid.Time_series[z.TS_dict['PRGi_available']].data_clustered[n_clusters][t-1]
                    else:
                        factor = grid.Time_series[z.TS_dict['PRGi_available']].data[t-1]
          
                    PGi_ren+=rs.PGi_ren_base*factor
                except KeyError:
                    PGi_ren+=rs.PGi_ren_base*rs.PRGi_available
                    print(f'Key {z} not found in Time series')   
                
                
            gen+=node.PGi +PGi_ren+PGi_opt
            
        row_data_GEN[m.name] = np.round(gen * grid.S_base, decimals=2)    

        if type(m) is Price_Zone:
            SC = np.float64(pyo.value(model.scenario_model[t].SocialCost[nM]))
            row_data_SC[m.name] = np.round(SC / 1000, decimals=2)

            PN = np.float64(pyo.value(model.scenario_model[t].PN[nM]))
            row_data_PN[m.name] = np.round(PN * grid.S_base, decimals=2)
            
            
            
            
    return row_data_price, row_data_SC, row_data_PN,row_data_GEN

def get_curtailment_data(t, model, grid,n_clusters,clustering):
    row_data_curt = {'Time_Frame': t}
    row_data_curt_per = {'Time_Frame': t}

    for rs in grid.RenSources:
        if rs.PGRi_linked:
            rz = rs.Ren_source_zone
            z  = grid.RenSource_zones[grid.RenSource_zones_dic[rz]]
        else:
            z= rs
        try:    
            if clustering:
                factor = grid.Time_series[z.TS_dict['PRGi_available']].data_clustered[n_clusters][t-1]
            else:
                factor = grid.Time_series[z.TS_dict['PRGi_available']].data[t-1]
  
            PGi_ren=rs.PGi_ren_base*factor
        except KeyError:
            PGi_ren=rs.PGi_ren_base*rs.PRGi_available
            print(f'Key {z} not found in Time series')    
         
        curt_value = np.round((1 - pyo.value(model.scenario_model[t].gamma[rs.rsNumber])) *PGi_ren* grid.S_base, decimals=2)
        row_data_curt[rs.name] = curt_value
        row_data_curt_per[rs.name] =  np.round(1 - pyo.value(model.scenario_model[t].gamma[rs.rsNumber]), decimals=2)*100

    return row_data_curt,row_data_curt_per

def get_line_data(t, model, grid):
    row_data_lines = {'Time_Frame': t}
    
    if grid.TEP_AC:
        for l in grid.lines_AC_exp:
            if l.np_line_opf:
                ln = l.lineNumber
                P_to = np.float64(pyo.value(model.scenario_model[t].exp_PAC_to[ln])) * grid.S_base
                P_from = np.float64(pyo.value(model.scenario_model[t].exp_PAC_from[ln])) * grid.S_base
                Q_to = np.float64(pyo.value(model.scenario_model[t].exp_QAC_to[ln])) * grid.S_base
                Q_from = np.float64(pyo.value(model.scenario_model[t].exp_QAC_from[ln])) * grid.S_base
                S_to = np.sqrt(P_to**2 + Q_to**2)
                S_from = np.sqrt(P_from**2 + Q_from**2)
                load = max(S_to, S_from) / l.MVA_rating * 100
                row_data_lines[l.name] = np.round(load, decimals=0).astype(int)
    if grid.REC_AC:
        for l in grid.lines_AC_rec:
            if l.rec_line_opf:
                ln = l.lineNumber
                state = 1 if pyo.value(model.rec_branch[ln]) >= 0.99999 else 0
                P_to = np.float64(pyo.value(model.scenario_model[t].rec_PAC_to[ln,state])) * grid.S_base
                P_from = np.float64(pyo.value(model.scenario_model[t].rec_PAC_from[ln,state])) * grid.S_base
                Q_to = np.float64(pyo.value(model.scenario_model[t].rec_QAC_to[ln,state])) * grid.S_base
                Q_from = np.float64(pyo.value(model.scenario_model[t].rec_QAC_from[ln,state])) * grid.S_base
                S_to = np.sqrt(P_to**2 + Q_to**2)
                S_from = np.sqrt(P_from**2 + Q_from**2)
                if state == 1:
                    load = max(S_to, S_from) / l.MVA_rating_new * 100
                else:   
                    load = max(S_to, S_from) / l.MVA_rating * 100 
                row_data_lines[l.name] = np.round(load, decimals=0).astype(int)
                
    if grid.CT_AC:
        for l in grid.lines_AC_ct:
            if l.array_opf:
                ln = l.lineNumber
                # Check if any conductor type is selected
                ct_selected = [pyo.value(model.ct_branch[ln,ct]) >= 0.99999 for ct in model.ct_set]
                if any(ct_selected):
                    active_config = np.where(ct_selected)[0][0]
                    P_to = np.float64(pyo.value(model.scenario_model[t].ct_PAC_to[ln,active_config])) * grid.S_base
                    P_from = np.float64(pyo.value(model.scenario_model[t].ct_PAC_from[ln,active_config])) * grid.S_base
                    Q_to = np.float64(pyo.value(model.scenario_model[t].ct_QAC_to[ln,active_config])) * grid.S_base
                    Q_from = np.float64(pyo.value(model.scenario_model[t].ct_QAC_from[ln,active_config])) * grid.S_base
                else:
                    active_config = -1  # or None, or handle appropriately
                    P_to = 0
                    P_from = 0
                    Q_to = 0
                    Q_from = 0
                
                S_to = np.sqrt(P_to**2 + Q_to**2)
                S_from = np.sqrt(P_from**2 + Q_from**2)
                load = max(S_to, S_from) / l.MVA_rating_list[active_config] * 100
                row_data_lines[l.name] = np.round(load, decimals=0).astype(int)
    if grid.DCmode:
        for l in grid.lines_DC:
            if l.np_line_opf:
                ln = l.lineNumber
                if l.np_line <= 0.00001:
                    row_data_lines[l.name] = np.nan
                else:
                    p_to = np.float64(pyo.value(model.scenario_model[t].PDC_to[ln])) * grid.S_base
                    p_from = np.float64(pyo.value(model.scenario_model[t].PDC_from[ln])) * grid.S_base
                    load = max(p_to, p_from) / l.MW_rating * 100
                    row_data_lines[l.name] = np.round(load, decimals=0).astype(int)

    return row_data_lines

def get_converter_data(t, model, grid):
    row_data_conv = {'Time_Frame': t}

    for conv in grid.Converters_ACDC:
        if conv.NUmConvP_opf:
            cn = conv.ConvNumber
            if conv.NumConvP <= 0.00001:
                row_data_conv[conv.name] = np.nan
            else:
                P_DC = np.float64(pyo.value(model.scenario_model[t].P_conv_DC[conv.Node_DC.nodeNumber])) * grid.S_base
                P_s  = np.float64(pyo.value(model.scenario_model[t].P_conv_s_AC[cn])) * grid.S_base
                Q_s  = np.float64(pyo.value(model.scenario_model[t].Q_conv_s_AC[cn])) * grid.S_base
                S = np.sqrt(P_s**2 + Q_s**2)
                loading = max(S, abs(P_DC)) / (conv.MVA_max * conv.NumConvP) * 100
                row_data_conv[conv.name] = np.round(loading, decimals=0)
                

    return row_data_conv

def get_weight_data(model, t):
    return pyo.value(model.weights[t])

def get_gen_data(t, model, grid):
    row_data_gen = {'Time_Frame': t}
    row_data_qgen = {'Time_Frame': t}
    for gen in grid.Generators:
            gn = gen.genNumber
            PGen = np.float64(pyo.value(model.scenario_model[t].PGi_gen[gn])) * grid.S_base
            QGen = np.float64(pyo.value(model.scenario_model[t].QGi_gen[gn])) * grid.S_base
            row_data_gen[f'G_{gen.name}'] = np.round(PGen, decimals=2)
            row_data_qgen[f'G_{gen.name}'] = np.round(QGen, decimals=2)
    for rg in grid.RenSources:
            rn = rg.rsNumber
            PGen = np.float64(pyo.value(model.scenario_model[t].P_renSource[rn]*model.scenario_model[t].gamma[rn])) * grid.S_base
            QGen = np.float64(pyo.value(model.scenario_model[t].Q_renSource[rn])) * grid.S_base
            row_data_gen[f'R_{rg.name}'] = np.round(PGen, decimals=2)
            row_data_qgen[f'R_{rg.name}'] = np.round(QGen, decimals=2)
    
    return row_data_gen,row_data_qgen



def ExportACDC_TEP_MS_toPyflowACDC(model,grid,n_clusters,clustering,Price_Zones):
    grid.V_AC =np.zeros(grid.nn_AC)
    grid.Theta_V_AC=np.zeros(grid.nn_AC)
    grid.V_DC=np.zeros(grid.nn_DC)

    grid.OPF_run=True  

   
    SW= sum(pyo.value(model.weights[t]) for t in model.scenario_frames)
    def process_ren_source(renSource):
        rs = renSource.rsNumber
        renSource.gamma =  np.float64(sum(pyo.value(model.scenario_model[t].gamma[rs]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
    
    def process_gen(gen):
        gn = gen.genNumber
        gen.PGen =  np.float64(sum(pyo.value(model.scenario_model[t].PGi_gen[gn]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        gen.QGen =  np.float64(sum(pyo.value(model.scenario_model[t].QGi_gen[gn]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
    
    
    def process_ac_node(node):
        nAC = node.nodeNumber
        node.V_AC = np.float64(sum(pyo.value(model.scenario_model[t].V_AC[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        node.theta = np.float64(sum(pyo.value(model.scenario_model[t].thetha_AC[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        if grid.DCmode:
            node.P_s = np.float64(sum(pyo.value(model.scenario_model[t].P_conv_AC[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
            node.Q_s = np.float64(sum(pyo.value(model.scenario_model[t].Q_conv_AC[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
    
        node.PGi_opt = np.float64(sum(pyo.value(model.scenario_model[t].PGi_opt[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        node.QGi_opt = np.float64(sum(pyo.value(model.scenario_model[t].QGi_opt[nAC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
    
        grid.V_AC[nAC] = node.V_AC
        grid.Theta_V_AC[nAC] = node.theta
    
    # Helper function for DC nodes
    def process_dc_node(node):
        nDC = node.nodeNumber
        node.V = np.float64(sum(pyo.value(model.scenario_model[t].V_DC[nDC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        node.P = np.float64(sum(pyo.value(model.scenario_model[t].P_conv_DC[nDC]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        node.P_INJ = node.PGi - node.PLi + node.P
        grid.V_DC[nDC] = node.V
    
    # Helper function for converters
    def process_converter(conv):
        nconv = conv.ConvNumber
        nconvp=np.float64(pyo.value(model.NumConvP[nconv]))
        conv.P_DC  = np.float64(sum(pyo.value(model.scenario_model[t].P_conv_DC[conv.Node_DC.nodeNumber])   *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.P_AC  = np.float64(sum(pyo.value(model.scenario_model[t].P_conv_s_AC[nconv]) *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.Q_AC  = np.float64(sum(pyo.value(model.scenario_model[t].Q_conv_s_AC[nconv]) *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.Pc    = np.float64(sum(pyo.value(model.scenario_model[t].P_conv_c_AC[nconv]) *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.Qc    = np.float64(sum(pyo.value(model.scenario_model[t].Q_conv_c_AC[nconv]) *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.P_loss= np.float64(sum(pyo.value(model.scenario_model[t].P_conv_loss[nconv]) *nconvp* pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.P_loss_tf = abs(conv.P_AC - conv.Pc)
        conv.U_c   = np.float64(sum(pyo.value(model.scenario_model[t].Uc[nconv])   * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.U_f   = np.float64(sum(pyo.value(model.scenario_model[t].Uf[nconv])   * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.U_s   = np.float64(sum(pyo.value(model.scenario_model[t].V_AC[nconv]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.th_c  = np.float64(sum(pyo.value(model.scenario_model[t].th_c[nconv]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.th_f  = np.float64(sum(pyo.value(model.scenario_model[t].th_f[nconv]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.th_s  = np.float64(sum(pyo.value(model.scenario_model[t].thetha_AC[nconv]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        conv.NumConvP = nconvp
    # Helper function for price_zones
    def process_price_zone(m):
        nM = m.price_zone_num
        m.price = np.float64(sum(pyo.value(model.scenario_model[t].price_zone_price[nM]) * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        s=1
        from .Classes import Price_Zone
        if type(m) is Price_Zone:
       
            if clustering:
                m.a          = np.float64(sum(grid.Time_series[m.TS_dict['a_CG']].data_clustered[n_clusters][t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
                m.b          = np.float64(sum(grid.Time_series[m.TS_dict['b_CG']].data_clustered[n_clusters][t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
                m.PLi_factor = np.float64(sum(grid.Time_series[m.TS_dict['Load']].data_clustered[n_clusters][t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        
            else:
                m.a = np.float64(sum(grid.Time_series[m.TS_dict['a_CG']].data[t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
                m.b = np.float64(sum(grid.Time_series[m.TS_dict['b_CG']].data[t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
                m.PLi_factor = np.float64(sum(grid.Time_series[m.TS_dict['Load']].data[t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
        
    
    with ThreadPoolExecutor() as executor:
        # Submit all tasks
        futures = []
        futures.extend([executor.submit(process_ac_node, node) for node in grid.nodes_AC])
        
        if grid.DCmode:
            futures.extend([executor.submit(process_dc_node, node) for node in grid.nodes_DC])
        if grid.ACmode and grid.DCmode:
            futures.extend([executor.submit(process_converter, conv) for conv in grid.Converters_ACDC])
            
        if Price_Zones:
            futures.extend([executor.submit(process_price_zone, m) for m in grid.Price_Zones])
            
        futures.extend([executor.submit(process_ren_source, m) for m in grid.RenSources])
        futures.extend([executor.submit(process_gen, m) for m in grid.Generators])
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()
    
    Pf = np.zeros((grid.nn_AC, 1))
    Qf = np.zeros((grid.nn_AC, 1))
    grid.create_Ybus_AC()
    G = np.real(grid.Ybus_AC_full)
    B = np.imag(grid.Ybus_AC_full)
    V = grid.V_AC
    Theta = grid.Theta_V_AC
    # Compute differences in voltage angles
    Theta_diff = Theta[:, None] - Theta
    
    # Calculate power flow
    Pf = (V[:, None] * V * (G * np.cos(Theta_diff) + B * np.sin(Theta_diff))).sum(axis=1)
    Qf = (V[:, None] * V * (G * np.sin(Theta_diff) - B * np.cos(Theta_diff))).sum(axis=1)
    

    for node in grid.nodes_AC:
        i = node.nodeNumber
        node.P_INJ = Pf[i]
        node.Q_INJ = Qf[i]

    if grid.TEP_AC:  
        NumLinesACP_values= {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}    
        for line in grid.lines_AC_exp:
            line.np_line=NumLinesACP_values[line.lineNumber] 
    if grid.REC_AC:
        lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in model.rec_branch.items()}
        for line in grid.lines_AC_rec:
            l = line.lineNumber
            line.rec_branch = True if lines_AC_REP[l] >= 0.99999 else False
    if grid.CT_AC:
        lines_AC_CT = {k: {ct: np.float64(pyo.value(model.ct_branch[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
        for line in grid.lines_AC_ct:
            l=line.lineNumber
            # Check if any conductor type is selected
            ct_selected = [lines_AC_CT[l][ct] >= 0.90 for ct in model.ct_set]
            if any(ct_selected):
                line.active_config = np.where(ct_selected)[0][0]
            else:
                line.active_config = -1  # or None, or handle appropriately
                # This line has no conductor type selected
    
    if grid.DCmode:
        NumLinesDCP_values= {k: np.float64(pyo.value(v)) for k, v in model.NumLinesDCP.items()}   
        for line in grid.lines_DC:
            line.np_line = NumLinesDCP_values[line.lineNumber]
    

    for z in grid.RenSource_zones:
        if clustering:
            z.PRGi_available = np.float64(sum(grid.Time_series[z.TS_dict['PRGi_available']].data_clustered[n_clusters][t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)      
        else:
            z.PRGi_available = np.float64(sum(grid.Time_series[z.TS_dict['PRGi_available']].data[t-1] * pyo.value(model.weights[t]) for t in model.scenario_frames) / SW)
           
    # Multithreading the time frame processing
    data_rows_PN = []
    data_rows_PZGEN= []
    data_rows_SC = []
    data_rows_curt = []
    data_rows_curt_per = []
    data_rows_lines = []
    data_rows_conv = []
    data_rows_price = []
    data_rows_pgen = []
    data_rows_qgen = []
    
    weights_row = []
    
    with ThreadPoolExecutor() as executor:
        futures = []
        
        for t in model.scenario_frames:
            
            futures.append(executor.submit(get_curtailment_data, t, model, grid,n_clusters,clustering))
            futures.append(executor.submit(get_line_data, t, model, grid))
            futures.append(executor.submit(get_converter_data, t, model, grid))
            futures.append(executor.submit(get_weight_data, model, t))
            futures.append(executor.submit(get_gen_data, t, model, grid))
            if Price_Zones:
                futures.append(executor.submit(get_price_zone_data, t, model, grid,n_clusters,clustering))
        # Calculate tasks per time frame
        tasks_per_frame = 5 + (1 if Price_Zones else 0)

        # Process results
        for i in range(0, len(futures), tasks_per_frame):
            curt_data, curt_data_per = futures[i].result()
            lines_data = futures[i+1].result()
            conv_data = futures[i+2].result()
            weight_data = futures[i+3].result()
            pgen_data, qgen_data = futures[i+4].result()
            
            if Price_Zones:
                price_data, SC_data, PN_data, PZ_GEN_data = futures[i+5].result()
                data_rows_price.append(price_data)
                data_rows_SC.append(SC_data)
                data_rows_PN.append(PN_data)
                data_rows_PZGEN.append(PZ_GEN_data)
            
            data_rows_curt.append(curt_data)
            data_rows_curt_per.append(curt_data_per)
            data_rows_lines.append(lines_data)
            data_rows_conv.append(conv_data)
            weights_row.append(weight_data)
            data_rows_pgen.append(pgen_data)
            data_rows_qgen.append(qgen_data)
    
    # Convert to DataFrames
    if Price_Zones:
        data_PN = pd.DataFrame(data_rows_PN)
        data_PZGEN = pd.DataFrame(data_rows_PZGEN)
        data_SC = pd.DataFrame(data_rows_SC)
        data_price = pd.DataFrame(data_rows_price)
        
        # Transpose the DataFrame to flip rows and columns
        flipped_data_PN = data_PN.set_index('Time_Frame').T 
        flipped_data_PZGEN = data_PZGEN.set_index('Time_Frame').T 
        flipped_data_SC = data_SC.set_index('Time_Frame').T 
        flipped_data_price = data_price.set_index('Time_Frame').T 
    else:
        # Create empty DataFrames with the same structure
        flipped_data_PN = pd.DataFrame()
        flipped_data_PZGEN = pd.DataFrame()
        flipped_data_SC = pd.DataFrame()
        flipped_data_price = pd.DataFrame()

    # These are always created regardless of Price_Zones
    data_curt = pd.DataFrame(data_rows_curt)
    data_curt_per = pd.DataFrame(data_rows_curt_per)
    data_lines = pd.DataFrame(data_rows_lines)
    data_conv = pd.DataFrame(data_rows_conv)
    data_pgen = pd.DataFrame(data_rows_pgen)
    data_qgen = pd.DataFrame(data_rows_qgen)

    # Transpose the remaining DataFrames
    flipped_data_curt = data_curt.set_index('Time_Frame').T 
    flipped_data_curt_per = data_curt_per.set_index('Time_Frame').T 
    flipped_data_lines = data_lines.set_index('Time_Frame').T 
    flipped_data_conv = data_conv.set_index('Time_Frame').T 
    flipped_data_pgen = data_pgen.set_index('Time_Frame').T 
    flipped_data_qgen = data_qgen.set_index('Time_Frame').T 

    # Calculate Total SC and related calculations only if Price_Zones is True
    if Price_Zones:
        # Total SC per scenario frame as numeric Series
        total_sc = flipped_data_SC.sum().astype(float).round(2)

        # Weights as numeric Series aligned with the scenario columns
        weights_series = pd.Series(
            [float(w) for w in weights_row],
            index=flipped_data_SC.columns
        )

        # Single authoritative weighted SC (per scenario frame)
        weighted_sc = (total_sc * weights_series).round(2)
        
        # Additional rows using that same weighted_sc
        additional_rows = pd.DataFrame({
            'Total SC': total_sc,
            '': [None] * len(total_sc),  # Blank row
            'Weight': weights_series,
            'Weighted SC': weighted_sc
        }).T
        
        # Combine original data with additional rows
        flipped_data_SC = pd.concat([flipped_data_SC, additional_rows])
    else:
        # Create empty DataFrame with the same structure for consistency
        flipped_data_SC = pd.DataFrame()
    
    frames = [int(t) for t in model.scenario_frames]
    weights_df = pd.DataFrame(
        [[float(pyo.value(model.weights[t])) for t in frames]],
        index=['Weight'],
        columns=frames
        )

    # Pack all variables into the final result
    TEP_multiScenario_res =     {
    'clustering': clustering,
    'n_clusters': n_clusters,
    'weights': weights_df,


    'PN': flipped_data_PN if flipped_data_PN is not None else None,
    'PZ_GEN': flipped_data_PZGEN if flipped_data_PZGEN is not None else None,
    'PZ_cost_of_generation': flipped_data_SC if flipped_data_SC is not None else None,

    'curtailment': flipped_data_curt,
    'curtailment_per': flipped_data_curt_per,
    'lines': flipped_data_lines,
    'converters': flipped_data_conv,
    'price': flipped_data_price,
    'pgen': flipped_data_pgen,
    'qgen': flipped_data_qgen,
    }
    
    
      
    grid.Line_AC_calc()
    grid.Line_DC_calc()
    
    return TEP_multiScenario_res

      

def export_TEP_multiScenario_results_to_excel(grid,export):
    
    [clustering,n_clusters,flipped_data_PN,flipped_data_PZGEN ,flipped_data_SC, flipped_data_curt,flipped_data_curt_per, flipped_data_lines,
        flipped_data_conv, flipped_data_price,flipped_data_pgen,flipped_data_qgen] = grid.TEP_multiScenario_res
           # Define the column names for the DataFrame
    columns = ["Element", "Type", "Initial", "Optimized N", "Optimized Power Rating [MW]", "Expansion Cost [k€]"]
    
    # Create an empty list to hold the data
    data = []
    
    tot = 0

    if grid.TEP_AC:
        for l in grid.lines_AC_exp:
            if l.np_line_opf:
                element = l.name
                ini = l.np_line_i
                opt = l.np_line
                pr = opt * l.MVA_rating
                cost = ((opt - ini) * l.base_cost)  / 1000
                tot += cost
                data.append([element, "AC Line", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])
    if grid.REC_AC:
        for l in grid.lines_AC_rec:
            if l.rec_line_opf:
                element = l.name
                ini = " "
                opt = l.rec_branch
                if l.rec_branch:
                    pr = l.MVA_rating_new
                    cost = l.base_cost  / 1000
                else:
                    pr = l.MVA_rating
                    cost = 0
                tot += cost
                data.append([element, "Reconducting Line", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])
    if grid.CT_AC:
        for l in grid.lines_AC_ct:
            if l.array_opf:
                element = l.name
                ini = l.ini_active_config
                opt = l.active_config
                pr = l.MVA_rating_list[opt]
                cost = l.base_cost[opt] / 1000
                tot += cost
                data.append([element, "Cable type Line", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])
                

    if grid.DCmode:
        # Loop through DC lines and add data to the list
        for l in grid.lines_DC:
            if l.np_line_opf:
                element = l.name
                ini = l.np_line_i
                opt = l.np_line
                pr = opt * l.MW_rating
                cost = ((opt - ini) * l.base_cost)  / 1000
                
                tot += cost
                data.append([element, "DC Line", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])
    
    if grid.ACmode and grid.DCmode:
        # Loop through ACDC converters and add data to the list
        for cn in grid.Converters_ACDC:
            if cn.NUmConvP_opf:
                element = cn.name
                ini = cn.NumConvP_i
                opt = cn.NumConvP
                pr = opt * cn.MVA_max
                cost = ((opt - ini) * cn.base_cost)  / 1000
                tot += cost
                
                if cn.cost_perMVA is not None:
                    unit_cost= cn.cost_perMVA
                elif cn.base_cost is not None:
                    unit_cost= cn.base_cost /cn.MVA_max
                else:
                    unit_cost = np.nan
                    
                
                data.append([element, "ACDC Conv", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])
        
    # Create a pandas DataFrame with the collected data
    df = pd.DataFrame(data, columns=columns)    
    
    
    
    

    data = {}

    # Loop through RenSourceZones
    for z in grid.RenSource_zones:
        # Extract the zone name
        zone_name = z.name
        # Access the time series data for the specific 'PGRi' from the zone's TS_dict
        if clustering:
            time_series_data = grid.Time_series[z.TS_dict['PRGi_available']].data_clustered[n_clusters]
        else:
            time_series_data = grid.Time_series[z.TS_dict['PRGi_available']].data
        
        # Append the zone name and corresponding data as a row in the data list
        data[zone_name]= time_series_data
    
    # Create a DataFrame named Availability_factors from the collected data
    Availability_factors = pd.DataFrame(data)

    data_L = {}

    # Loop through
    for z in grid.Price_Zones:
        
        # Extract the zone name
        zone_name = z.name
        # Access the time series data for the specific 'PGRi' from the zone's TS_dict
        if z.TS_dict is None or z.TS_dict.get('Load') is None:
            continue
        if clustering:
            time_series_data = grid.Time_series[z.TS_dict['Load']].data_clustered[n_clusters]
        else:
            time_series_data = grid.Time_series[z.TS_dict['Load']].data
        
        # Append the zone name and corresponding data as a row in the data list
        
        data_L[zone_name]= time_series_data 
    
    # Create a DataFrame named Availability_factors from the collected data
    Load_factors = pd.DataFrame(data)

    flipped_AV=Availability_factors.T
    flipped_LF = Load_factors.T
    
    
    if export.endswith('.xlsx'):
        export=export
    else:
        export=f'{export}.xlsx'
    with pd.ExcelWriter(export) as writer:
        df.to_excel(writer, sheet_name='TEP solution', index=True)
        flipped_data_SC.to_excel(writer, sheet_name='Social Cost k€', index=True)
        flipped_data_PN.to_excel(writer, sheet_name='Net price_zone power MW', index=True)
        flipped_data_price.to_excel(writer, sheet_name='Price_Zone Price  € per MWh', index=True)
        flipped_data_PZGEN.to_excel(writer, sheet_name='Price Zone Generation MW', index=True)
        flipped_data_pgen.to_excel(writer, sheet_name='Generation MW', index=True)
        flipped_data_qgen.to_excel(writer, sheet_name='Generation MVAR', index=True)
        flipped_data_curt.to_excel(writer, sheet_name='Curtailment MW', index=True)
        flipped_data_curt_per.to_excel(writer, sheet_name='Curtailment %', index=True)
        flipped_data_lines.to_excel(writer, sheet_name='Line loading %', index=True)
        flipped_data_conv.to_excel(writer, sheet_name='Converter loading %', index=True)
        flipped_AV.to_excel(writer, sheet_name='Availability Factors pu', index=True)
        flipped_LF.to_excel(writer, sheet_name='Load Factors  pu', index=True)

def calculate_STEP_objective_from_model(model,grid,weights_def,multi_scenario=False):

    opf_objs = []
    if multi_scenario:
        for t in model.scenario_frames:
            opf_obj = calculate_objective_from_model(model.scenario_model[t],grid,weights_def,True)
            opf_objs.append(opf_obj)
    else:
        opf_objs = [calculate_objective_from_model(model,grid,weights_def,True)]

    tep_obj = TEP_obj(model,grid,True)  
    tep_obj_value = pyo.value(tep_obj)
    return opf_objs, tep_obj_value