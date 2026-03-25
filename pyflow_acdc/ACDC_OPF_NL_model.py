# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:25:02 2024

@author: BernardoCastro
"""

import pyomo.environ as pyo
import numpy as np
from concurrent.futures import ThreadPoolExecutor


__all__ = [
    'OPF_create_NLModel_ACDC',
    'ExportACDC_NLmodel_toPyflowACDC'
]


def get_gen_p_min_eff(gen, np_gen_value, p_load_eff_value=None):
    if not getattr(gen, 'is_ext_grid', False):
        return gen.Min_pow_gen * np_gen_value
    if not getattr(gen, 'allow_sell', True):
        return 0
    p_load_eff = gen.p_load_eff if p_load_eff_value is None else p_load_eff_value
    return -(gen.Max_pow_gen * np_gen_value - p_load_eff)


    

def OPF_create_NLModel_ACDC(model,grid,PV_set,Price_Zones,TEP=False,limit_flow_rate=True,robust_mode=False):
    from .ACDC_OPF import Translate_pyf_OPF 
    
    if limit_flow_rate is True:
        limit_flow_rate = 1
        
    model.robust_mode = bool(robust_mode)
    
    opf_data = Translate_pyf_OPF(grid,Price_Zones=Price_Zones)
    AC_info = opf_data['AC_info']
    DC_info = opf_data['DC_info']
    Conv_info = opf_data['Conv_info']
    Price_Zone_info = opf_data['Price_Zone_info']
    gen_info = opf_data['gen_info']
   
    Generation_variables(model,grid,gen_info,TEP)

    if grid.ACmode:
        AC_variables(model,grid,AC_info,PV_set,limit_flow_rate)

    if grid.DCmode:
        DC_variables(model,grid,DC_info,TEP,limit_flow_rate)
    
    if grid.DCmode and grid.ACmode:
        Converter_variables(model,grid,Conv_info)

    if TEP:
        TEP_variables(model,grid)
    else:
        TEP_parameters(model,grid,AC_info,DC_info,Conv_info)

    if Price_Zones:
        price_zone_variables(model,grid,Price_Zone_info,AC_info,DC_info,gen_info)
        price_zone_constraints(model,grid,Price_Zone_info)
    else:
        price_zone_parameters(model,grid,AC_info,DC_info,gen_info)

    if grid.ACmode:
        AC_constraints(model,grid,AC_info,limit_flow_rate)

    if grid.DCmode:
        DC_constraints(model,grid)
        
    if grid.DCmode and grid.ACmode:
        Converter_constraints(model,grid,Conv_info)

    

def Generation_variables(model,grid,gen_info,TEP):
    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    _,_,_,_,lista_gen = gen_AC_info
    _,_,_,_,lista_gen_DC = gen_DC_info
    P_renSource, _, lista_rs = gen_rs_info
    
    model.ren_sources= pyo.Set(initialize=lista_rs)
    model.P_renSource = pyo.Param(model.ren_sources,initialize=P_renSource,mutable=True)
    
    def gamma_bounds(model,rs):
        ren_source= grid.RenSources[rs]
        if ren_source.curtailable:
            return (ren_source.min_gamma,1)
        else:
            return (1,1)
    model.gamma = pyo.Var(model.ren_sources, bounds=gamma_bounds, initialize=1)
    
    def Qren_bounds(model,rs):
        ren_source= grid.RenSources[rs]
        if ren_source.connected == 'AC':
            return (ren_source.Qmin,ren_source.Qmax)
        else:
            return (0,0)
    
    
    model.Q_renSource = pyo.Var(model.ren_sources,bounds=Qren_bounds, initialize=0)
    
    
    def P_Gen_bounds(model, g):
        gen = grid.Generators[g]
        return (get_gen_p_min_eff(gen, gen.np_gen), gen.Max_pow_gen * gen.np_gen)
        
    def Q_Gen_bounds(model, g):
        gen = grid.Generators[g]
        return (gen.Min_pow_genR*gen.np_gen,gen.Max_pow_genR*gen.np_gen)
    
    def P_gen_ini(model,g):
        gen = grid.Generators[g]
        min_pow_gen = get_gen_p_min_eff(gen, gen.np_gen)
        ini=gen.Pset * gen.np_gen
        max_pow_gen = gen.Max_pow_gen * gen.np_gen
        if  min_pow_gen>ini:
            ini=min_pow_gen
        elif ini>max_pow_gen: 
            ini=max_pow_gen
        return (ini)
    
    def Q_gen_ini(model,g):
        gen = grid.Generators[g]
        min_pow_genR = gen.Min_pow_genR * gen.np_gen
        ini=gen.Qset * gen.np_gen
        max_pow_genR = gen.Max_pow_genR * gen.np_gen
        if min_pow_genR>ini:
            ini=min_pow_genR
        elif ini>max_pow_genR: 
            ini=max_pow_genR    
        return (ini)
    

    if grid.ACmode:
        model.gen_AC     = pyo.Set(initialize=lista_gen)
        if grid.GPR and TEP:
            p_load_eff_ini = {gen.genNumber: gen.p_load_eff for gen in grid.Generators}
            model.P_load_eff = pyo.Param(model.gen_AC, initialize=p_load_eff_ini, mutable=True)
 
            model.PGi_gen = pyo.Var(model.gen_AC, initialize=P_gen_ini)
            model.QGi_gen = pyo.Var(model.gen_AC, initialize=Q_gen_ini) 
        else:
            model.PGi_gen = pyo.Var(model.gen_AC,bounds=P_Gen_bounds, initialize=P_gen_ini)
            model.QGi_gen = pyo.Var(model.gen_AC,bounds=Q_Gen_bounds, initialize=Q_gen_ini) 
        if grid.act_gen:
            model.gen_active = pyo.Var(model.gen_AC, domain=pyo.Binary, initialize=1)
    def P_Gen_bounds_DC(model, g):
        gen = grid.Generators_DC[g]
        return (gen.Min_pow_gen*gen.np_gen,gen.Max_pow_gen*gen.np_gen)
        
    def P_gen_ini_DC(model,g):
        gen = grid.Generators_DC[g]
        min_pow_gen = gen.Min_pow_gen * gen.np_gen
        ini=gen.Pset * gen.np_gen
        max_pow_gen = gen.Max_pow_gen * gen.np_gen
        if  min_pow_gen>ini:
            ini=min_pow_gen
        elif ini>max_pow_gen: 
            ini=max_pow_gen
        return (ini)
    
    if grid.DCmode:
        model.gen_DC     = pyo.Set(initialize=lista_gen_DC)    
    
        if grid.GPR and TEP:
            model.PGi_gen_DC = pyo.Var(model.gen_DC, initialize=P_gen_ini_DC)

        else:
            model.PGi_gen_DC = pyo.Var(model.gen_DC,bounds=P_Gen_bounds_DC, initialize=P_gen_ini_DC)
           
    s=1
def AC_variables(model,grid,AC_info,PV_set,limit_flow_rate=1):

    AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info
    
    
    lista_nodos_AC, lista_lineas_AC,lista_lineas_AC_tf,AC_slack, AC_PV = AC_Lists
    u_min_ac,u_max_ac,V_ini_AC,Theta_ini, P_know,Q_know,price = AC_nodes_info
    S_lineAC_limit,S_lineACtf_limit,m_tf_og = AC_lines_info

    lista_lineas_AC_exp,S_lineACexp_limit,NP_lineAC = EXP_info
    lista_lineas_AC_rec,S_lineACrec_lim,S_lineACrec_lim_new,grid.REC_AC_act = REC_info
    lista_lineas_AC_ct,S_lineACct_lim,cab_types_set,allowed_types = CT_info

    "Model Sets"
    model.nodes_AC   = pyo.Set(initialize=lista_nodos_AC)
    model.lines_AC   = pyo.Set(initialize=lista_lineas_AC)
    
    if grid.TEP_AC:
        model.lines_AC_exp = pyo.Set(initialize=lista_lineas_AC_exp)
    if grid.TAP_tf:
        model.lines_AC_tf  = pyo.Set(initialize=lista_lineas_AC_tf) 
    if grid.REC_AC:
        model.lines_AC_rec = pyo.Set(initialize=lista_lineas_AC_rec)
    if grid.CT_AC:
        model.lines_AC_ct = pyo.Set(initialize=lista_lineas_AC_ct)
    
    
    
    model.AC_slacks  = pyo.Set(initialize=AC_slack)
    if PV_set:
        model.AC_PVs     = pyo.Set(initialize=AC_PV)
            
    "AC Variables"
    #AC nodes variables
    model.V_AC       = pyo.Var(model.nodes_AC, bounds=lambda model, node: (u_min_ac[node], u_max_ac[node]), initialize=V_ini_AC)
    model.thetha_AC  = pyo.Var(model.nodes_AC, bounds=(-1.6, 1.6), initialize=Theta_ini)

    model.P_known_AC = pyo.Param(model.nodes_AC, initialize=P_know,mutable=True)
    model.Q_known_AC = pyo.Param(model.nodes_AC, initialize=Q_know,mutable=True)
        
    def Pren_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_RenSource == []:
            return (0,0)
        else:
            return (None,None)
    
    def Qren_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_RenSource == []:
            return (0,0)
        else:
            return (None,None)
    
    model.PGi_ren = pyo.Var(model.nodes_AC, bounds=Pren_bounds,initialize=0)
    model.QGi_ren = pyo.Var(model.nodes_AC, bounds=Qren_bounds,initialize=0)
     
    
    def PGi_opt_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_gen == []:
            return (0,0)
        else:
            return (None,None)
            
    def QGi_opt_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_gen == []:
            return (0,0)
        else:
            return (None,None)
   
    
    model.PGi_opt = pyo.Var(model.nodes_AC,bounds=PGi_opt_bounds ,initialize=0)
    model.QGi_opt = pyo.Var(model.nodes_AC,bounds=QGi_opt_bounds, initialize=0)

    def make_opt_bounds(attribute_name):
        def bounds_func(model, node):
            nAC = grid.nodes_AC[node]
            connected_lines = getattr(nAC, attribute_name)
            return (0, 0) if not connected_lines else (None, None)
        return bounds_func

    # Create bounds functions dynamically
    toExp_opt_bounds    = make_opt_bounds('connected_toExpLine')
    fromExp_opt_bounds  = make_opt_bounds('connected_fromExpLine')
    toTF_opt_bounds     = make_opt_bounds('connected_toTFLine')
    fromTF_opt_bounds   = make_opt_bounds('connected_fromTFLine')
    toREC_opt_bounds    = make_opt_bounds('connected_toRepLine')
    fromREC_opt_bounds  = make_opt_bounds('connected_fromRepLine')
    toCT_opt_bounds     = make_opt_bounds('connected_toCTLine')
    fromCT_opt_bounds   = make_opt_bounds('connected_fromCTLine')

    if grid.TEP_AC:
        model.Pto_Exp  = pyo.Var(model.nodes_AC,bounds=toExp_opt_bounds ,initialize=0)
        model.Pfrom_Exp= pyo.Var(model.nodes_AC,bounds=fromExp_opt_bounds ,initialize=0)
        model.Qto_Exp  = pyo.Var(model.nodes_AC,bounds=toExp_opt_bounds ,initialize=0)
        model.Qfrom_Exp= pyo.Var(model.nodes_AC,bounds=fromExp_opt_bounds ,initialize=0)
    
    if grid.TAP_tf:
        model.Pto_TF   = pyo.Var(model.nodes_AC,bounds=toTF_opt_bounds ,initialize=0)
        model.Pfrom_TF = pyo.Var(model.nodes_AC,bounds=fromTF_opt_bounds ,initialize=0)
        model.Qto_TF   = pyo.Var(model.nodes_AC,bounds=toTF_opt_bounds ,initialize=0)
        model.Qfrom_TF = pyo.Var(model.nodes_AC,bounds=fromTF_opt_bounds ,initialize=0)
   
    if grid.REC_AC:
        model.Pto_REP   = pyo.Var(model.nodes_AC,bounds=toREC_opt_bounds ,initialize=0)
        model.Pfrom_REP = pyo.Var(model.nodes_AC,bounds=fromREC_opt_bounds ,initialize=0)
        model.Qto_REP   = pyo.Var(model.nodes_AC,bounds=toREC_opt_bounds ,initialize=0)
        model.Qfrom_REP = pyo.Var(model.nodes_AC,bounds=fromREC_opt_bounds ,initialize=0)

    if grid.CT_AC:
        model.Pto_CT   = pyo.Var(model.nodes_AC,bounds=toCT_opt_bounds ,initialize=0)
        model.Pfrom_CT = pyo.Var(model.nodes_AC,bounds=fromCT_opt_bounds ,initialize=0)
        model.Qto_CT   = pyo.Var(model.nodes_AC,bounds=toCT_opt_bounds ,initialize=0)
        model.Qfrom_CT = pyo.Var(model.nodes_AC,bounds=fromCT_opt_bounds ,initialize=0) 

    def AC_V_slack_rule(model, node):
        return model.V_AC[node] == V_ini_AC[node]

    def AC_theta_slack_rule(model, node):
        return model.thetha_AC[node] == Theta_ini[node]

    def AC_V_PV_rule(model, node):
        return model.V_AC[node] == V_ini_AC[node]

    
    model.AC_theta_slack_constraint = pyo.Constraint(model.AC_slacks, rule=AC_theta_slack_rule)
    if PV_set:
        model.AC_V_slack_constraint = pyo.Constraint(model.AC_slacks, rule=AC_V_slack_rule)
        model.AC_V_PV_constraint = pyo.Constraint(model.AC_PVs, rule=AC_V_PV_rule)
    
    #AC Lines variables
    def Sbounds_lines(model, line):
        if limit_flow_rate is False:
            return (None,None)
        
        return (-S_lineAC_limit[line]*limit_flow_rate, S_lineAC_limit[line]*limit_flow_rate)
    
    
    model.PAC_to       = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.PAC_from     = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.QAC_to       = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.QAC_from     = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.PAC_line_loss= pyo.Var(model.lines_AC, initialize=0)

    def Sbounds_lines_exp(model, line):
        if not limit_flow_rate:
            return (None,None)
        return (-S_lineACexp_limit[line], S_lineACexp_limit[line])
   
    if grid.TEP_AC:
        model.exp_PAC_to       = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_PAC_from     = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_QAC_to       = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_QAC_from     = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_PAC_line_loss= pyo.Var(model.lines_AC_exp, initialize=0)
    
    def Sbounds_lines_tf(model, line):
        if not limit_flow_rate:
            return (None,None)
        return (-S_lineACtf_limit[line], S_lineACtf_limit[line])
    def bounds_tf_tap(model, tf):
        if not limit_flow_rate:
            return (None,None)
        return (0.95*m_tf_og[tf], 1.05*m_tf_og[tf])
    
    if grid.TAP_tf:
        model.tf_PAC_to       = pyo.Var(model.lines_AC_tf, bounds=Sbounds_lines_tf, initialize=0)
        model.tf_PAC_from     = pyo.Var(model.lines_AC_tf, bounds=Sbounds_lines_tf, initialize=0)
        model.tf_QAC_to       = pyo.Var(model.lines_AC_tf, bounds=Sbounds_lines_tf, initialize=0)
        model.tf_QAC_from     = pyo.Var(model.lines_AC_tf, bounds=Sbounds_lines_tf, initialize=0)
        model.tf_m            = pyo.Var(model.lines_AC_tf, bounds=bounds_tf_tap   , initialize=m_tf_og)
                  
        model.tf_PAC_line_loss= pyo.Var(model.lines_AC_tf, initialize=0)

    def state_based_bounds(model, line, state):
            max_min = max(S_lineACrec_lim[line], S_lineACrec_lim_new[line])
            return (-max_min, max_min)
            
    if grid.REC_AC:
        # Define a set for the branch states (0=old, 1=new)
        model.branch_states = pyo.Set(initialize=[0, 1])
        
        # Single variable for all power flows with two indices
        model.rec_PAC_to   = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_PAC_from = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_QAC_to   = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_QAC_from = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_PAC_line_loss = pyo.Var(model.lines_AC_rec,initialize=0)
    
    def set_based_bounds(model, line, cab_type):
        # Check if this is a fixed route with no cable selected (inactive line)
        if grid.lines_AC_ct[line].active_config < 0:
            return (0, 0)  # Force variables to zero for inactive lines
        max_min = max(S_lineACct_lim[line,ct] for ct in cab_types_set)  # Use cab_types_set instead of model.ct_set
        return (-max_min, max_min)
       
    
    if grid.CT_AC:

        model.ct_set = pyo.Set(initialize=cab_types_set)
        model.ct_PAC_to   = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)
        model.ct_PAC_from = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)
        model.ct_QAC_to   = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)
        model.ct_QAC_from = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)
        model.ct_PAC_line_loss = pyo.Var(model.lines_AC_ct,initialize=0)
        

def AC_constraints(model,grid,AC_info,limit_flow_rate=True):
    
    
    AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info
    S_lineAC_limit,S_lineACtf_limit,m_tf_og = AC_lines_info

    lista_lineas_AC_exp,S_lineACexp_limit,NP_lineAC = EXP_info
    lista_lineas_AC_rec,S_lineACrec_lim,S_lineACrec_lim_new,grid.REC_AC_act = REC_info
    lista_lineas_AC_ct,S_lineACct_lim,cab_types_set,allowed_types = CT_info
    
    if grid.TEP_AC and model.robust_mode:
        lines_np0 = [ln for ln in lista_lineas_AC_exp if int(NP_lineAC[ln]) == 0]
        model.lines_AC_exp_np0 = pyo.Set(initialize=lines_np0)
        model.z_ACexp_active = pyo.Var(model.lines_AC_exp_np0, domain=pyo.Binary, initialize=0)
        
        def _z_link_lower_rule(m, line):
            return m.NumLinesACP[line] >= m.z_ACexp_active[line]
        
        def _z_link_upper_rule(m, line):
            ub = m.NumLinesACP[line].ub
            if ub is None:
                return pyo.Constraint.Skip
            return m.NumLinesACP[line] <= ub * m.z_ACexp_active[line]
        
        model.z_ACexp_link_lower = pyo.Constraint(model.lines_AC_exp_np0, rule=_z_link_lower_rule)
        model.z_ACexp_link_upper = pyo.Constraint(model.lines_AC_exp_np0, rule=_z_link_upper_rule)
    else:
        model.lines_AC_exp_np0 = pyo.Set(initialize=[])

    "AC equality constraints"
    # AC node constraints
    def P_AC_node_rule(model, node):
        P_sum = sum(
                model.V_AC[node] * model.V_AC[k] *
                (np.real(grid.Ybus_AC[node, k]) * pyo.cos(model.thetha_AC[node] - model.thetha_AC[k]) +
                 np.imag(grid.Ybus_AC[node, k]) * pyo.sin(model.thetha_AC[node] - model.thetha_AC[k]))
                for k in model.nodes_AC if grid.Ybus_AC[node, k] != 0   )   
        P_var = model.P_known_AC[node] + model.PGi_ren[node] + model.PGi_opt[node]
        if grid.DCmode:
            P_var += model.P_conv_AC[node]
        if grid.TEP_AC:
            P_sum += model.Pto_Exp[node]+model.Pfrom_Exp[node]
        if grid.TAP_tf:
            P_sum += model.Pto_TF[node]+model.Pfrom_TF[node]
        if grid.REC_AC:
            P_sum += model.Pto_REP[node]+model.Pfrom_REP[node]
        if grid.CT_AC:
            P_sum += model.Pto_CT[node]+model.Pfrom_CT[node]
        
        return P_sum == P_var

    def Q_AC_node_rule(model, node):

        Q_sum = sum(
            model.V_AC[node] * model.V_AC[k] *
            (np.real(grid.Ybus_AC[node, k]) * pyo.sin(model.thetha_AC[node] - model.thetha_AC[k]) -
             np.imag(grid.Ybus_AC[node, k]) * pyo.cos(model.thetha_AC[node] - model.thetha_AC[k]))
            for k in model.nodes_AC if grid.Ybus_AC[node, k] != 0)
        Q_var = model.Q_known_AC[node] + model.QGi_ren[node] + model.QGi_opt[node]
        if grid.DCmode:
            Q_var += model.Q_conv_AC[node]
        if grid.TEP_AC:
            Q_sum += model.Qto_Exp[node]+model.Qfrom_Exp[node]
        if grid.TAP_tf:
            Q_sum += model.Qto_TF[node]+model.Qfrom_TF[node]
        if grid.REC_AC:
            Q_sum += model.Qto_REP[node]+model.Qfrom_REP[node]
        if grid.CT_AC:
            Q_sum += model.Qto_CT[node]+model.Qfrom_CT[node]
        
        return Q_sum == Q_var

    model.P_AC_node_constraint = pyo.Constraint(model.nodes_AC, rule=P_AC_node_rule)
    model.Q_AC_node_constraint = pyo.Constraint(model.nodes_AC, rule=Q_AC_node_rule)
    
    # Adds all generators in the AC nodes they are connected to
    def Gen_PAC_rule(model,node):
       nAC = grid.nodes_AC[node]
       if grid.act_gen:
            P_gen = sum(model.PGi_gen[gen.genNumber]*model.gen_active[gen.genNumber] for gen in nAC.connected_gen)                  
       else:
            P_gen = sum(model.PGi_gen[gen.genNumber] for gen in nAC.connected_gen)                  
       return  model.PGi_opt[node] ==   P_gen
           
    def Gen_Q_rule(model,node):
       nAC = grid.nodes_AC[node]
       if grid.act_gen:
            Q_gen = sum(model.QGi_gen[gen.genNumber]*model.gen_active[gen.genNumber] for gen in nAC.connected_gen)                  
       else:
            Q_gen = sum(model.QGi_gen[gen.genNumber] for gen in nAC.connected_gen)                  
       return  model.QGi_opt[node] ==   Q_gen
    
    model.Gen_PAC_constraint = pyo.Constraint(model.nodes_AC, rule=Gen_PAC_rule)
    model.Gen_QAC_constraint = pyo.Constraint(model.nodes_AC, rule=Gen_Q_rule)
    
    def Gen_PREN_rule(model,node):
       nAC = grid.nodes_AC[node]
       P_gen = sum(model.P_renSource[rs.rsNumber]*model.gamma[rs.rsNumber]*model.np_rsgen[rs.rsNumber] for rs in nAC.connected_RenSource)                  
       return  model.PGi_ren[node] ==   P_gen
   
    def Gen_QREN_rule(model,node):
       nAC = grid.nodes_AC[node]
       Q_gen = sum(model.Q_renSource[rs.rsNumber]*model.np_rsgen[rs.rsNumber] for rs in nAC.connected_RenSource)                  
       return  model.QGi_ren[node] ==   Q_gen
   
    model.Gen_PREN_constraint =pyo.Constraint(model.nodes_AC, rule=Gen_PREN_rule)
    model.Gen_QREN_constraint =pyo.Constraint(model.nodes_AC, rule=Gen_QREN_rule) 
    
    
    def toPexp_rule(model,node):
       nAC = grid.nodes_AC[node]
       toPexp = sum(model.exp_PAC_to[l.lineNumber]*model.NumLinesACP[l.lineNumber] for l in nAC.connected_toExpLine)                  
       return  model.Pto_Exp[node] ==  toPexp
    def fromPexp_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromPexp = sum(model.exp_PAC_from[l.lineNumber]*model.NumLinesACP[l.lineNumber] for l in nAC.connected_fromExpLine)                
       return  model.Pfrom_Exp[node] ==   fromPexp
    
    def toQexp_rule(model,node):
       nAC = grid.nodes_AC[node]
       toQexp = sum(model.exp_QAC_to[l.lineNumber]*model.NumLinesACP[l.lineNumber] for l in nAC.connected_toExpLine)                  
       return  model.Qto_Exp[node] ==  toQexp
    
    def fromQexp_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromQexp = sum(model.exp_QAC_from[l.lineNumber]*model.NumLinesACP[l.lineNumber] for l in nAC.connected_fromExpLine)                  
       return  model.Qfrom_Exp[node] ==  fromQexp   
   
    if grid.TEP_AC:
        model.exp_Pto_constraint  = pyo.Constraint(model.nodes_AC, rule=toPexp_rule)
        model.exp_Pfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromPexp_rule)
        model.exp_Qto_constraint  = pyo.Constraint(model.nodes_AC, rule=toQexp_rule)
        model.exp_Qfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromQexp_rule)
    
    def toPtf_rule(model,node):
       nAC = grid.nodes_AC[node]
       toPtf = sum(model.tf_PAC_to[l.lineNumber] for l in nAC.connected_toTFLine)                  
       return  model.Pto_TF[node] ==   toPtf
    def fromPtf_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromPtf = sum(model.tf_PAC_from[l.lineNumber] for l in nAC.connected_fromTFLine)                
       return  model.Pfrom_TF[node] ==   fromPtf
    
    def toQtf_rule(model,node):
       nAC = grid.nodes_AC[node]
       toQtf = sum(model.tf_QAC_to[l.lineNumber] for l in nAC.connected_toTFLine)                  
       return  model.Qto_TF[node] ==   toQtf
    def fromQtf_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromQtf = sum(model.tf_QAC_from[l.lineNumber] for l in nAC.connected_fromTFLine)                  
       return  model.Qfrom_TF[node] ==  fromQtf   

    if grid.TAP_tf:
        model.Pto_TF_constraint   = pyo.Constraint(model.nodes_AC, rule=toPtf_rule)
        model.Pfrom_TF_constraint = pyo.Constraint(model.nodes_AC, rule=fromPtf_rule)
        model.Qto_TF_constraint   = pyo.Constraint(model.nodes_AC, rule=toQtf_rule)
        model.Qfrom_TF_constraint = pyo.Constraint(model.nodes_AC, rule=fromQtf_rule)
   
    def toPre_rule(model,node):
       nAC = grid.nodes_AC[node]
       toPre = sum(model.rec_PAC_to[l.lineNumber,0]*(1-model.rec_branch[l.lineNumber])+model.rec_PAC_to[l.lineNumber,1]*model.rec_branch[l.lineNumber] for l in nAC.connected_toRepLine)                  
       return  model.Pto_REP[node] ==  toPre
    def fromPre_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromPre = sum(model.rec_PAC_from[l.lineNumber,0]*(1-model.rec_branch[l.lineNumber])+model.rec_PAC_from[l.lineNumber,1]*model.rec_branch[l.lineNumber] for l in nAC.connected_fromRepLine)                
       return  model.Pfrom_REP[node] ==   fromPre
    
    def toQrec_rule(model,node):
       nAC = grid.nodes_AC[node]
       toQrep = sum(model.rec_QAC_to[l.lineNumber,0]*(1-model.rec_branch[l.lineNumber])+model.rec_QAC_to[l.lineNumber,1]*model.rec_branch[l.lineNumber] for l in nAC.connected_toRepLine)                  
       return  model.Qto_REP[node] ==  toQrep
    
    def fromQrec_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromQrep = sum(model.rec_QAC_from[l.lineNumber,0]*(1-model.rec_branch[l.lineNumber])+model.rec_QAC_from[l.lineNumber,1]*model.rec_branch[l.lineNumber] for l in nAC.connected_fromRepLine)                  
       return  model.Qfrom_REP[node] ==  fromQrep   
   
    if grid.REC_AC:
        model.rec_Pto_constraint  = pyo.Constraint(model.nodes_AC, rule=toPre_rule)
        model.rec_Pfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromPre_rule)
        model.rec_Qto_constraint  = pyo.Constraint(model.nodes_AC, rule=toQrec_rule)
        model.rec_Qfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromQrec_rule)

    def toCT_rule(model,node):
       nAC = grid.nodes_AC[node]
       toPre = 0
       for line in nAC.connected_toCTLine:
           for ct in model.ct_set:
               toPre += model.ct_PAC_to[line.lineNumber,ct]*(model.ct_branch[line.lineNumber,ct])
       return  model.Pto_CT[node] ==  toPre
    def fromCT_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromPre = 0
       for line in nAC.connected_fromCTLine:
           for ct in model.ct_set:
               fromPre += model.ct_PAC_from[line.lineNumber,ct]*(model.ct_branch[line.lineNumber,ct])
       return  model.Pfrom_CT[node] ==   fromPre
    
    def toQCT_rule(model,node):
       nAC = grid.nodes_AC[node]
       toQCT = 0
       for line in nAC.connected_toCTLine:
           for ct in model.ct_set:
               toQCT += model.ct_QAC_to[line.lineNumber,ct]*(model.ct_branch[line.lineNumber,ct])
       return  model.Qto_CT[node] ==  toQCT
    
    def fromQCT_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromQCT = 0
       for line in nAC.connected_fromCTLine:
           for ct in model.ct_set:
               fromQCT += model.ct_QAC_from[line.lineNumber,ct]*(model.ct_branch[line.lineNumber,ct])
       return  model.Qfrom_CT[node] ==  fromQCT   
   

    if grid.CT_AC:
        model.ct_Pto_constraint  = pyo.Constraint(model.nodes_AC, rule=toCT_rule)
        model.ct_Pfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromCT_rule)
        model.ct_Qto_constraint  = pyo.Constraint(model.nodes_AC, rule=toQCT_rule)
        model.ct_Qfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromQCT_rule)


    # AC line equality constraints
    def calculate_P(model, line, direction,idx=None):
        f = line.fromNode.nodeNumber
        t = line.toNode.nodeNumber
        
        if idx is None:
            Ybus = line.Ybus_branch
        elif idx == 'new':
            Ybus = line.Ybus_branch_new
        else:
            Ybus = line.Ybus_list[idx]
        
        if direction == 'to':
            Vf=model.V_AC[f]
            Vt=model.V_AC[t]
            Gtt=np.real(Ybus[1,1])
            Gtf=np.real(Ybus[1,0])
            Btf=np.imag(Ybus[1,0])
            thf=model.thetha_AC[f]
            tht=model.thetha_AC[t]
            
            P= Vt*Vt*Gtt + Vf*Vt*(Gtf*pyo.cos(tht - thf) + Btf*pyo.sin(tht - thf))
        else:  # 'from'
            Vf=model.V_AC[f]
            Vt=model.V_AC[t]
            Gff=np.real(Ybus[0,0])
            Gft=np.real(Ybus[0,1])
            Bft=np.imag(Ybus[0,1])
            thf=model.thetha_AC[f]
            tht=model.thetha_AC[t]
            
            P= Vf*Vf*Gff + Vf*Vt*(Gft*pyo.cos(thf - tht) + Bft*pyo.sin(thf - tht))
        return P

    def calculate_Q(model, line, direction,idx=None):
        f = line.fromNode.nodeNumber
        t = line.toNode.nodeNumber
        
        if idx is None:
            Ybus = line.Ybus_branch
        elif idx == 'new':
            Ybus = line.Ybus_branch_new
        else:
            Ybus = line.Ybus_list[idx]

        if direction == 'to':
            Vf=model.V_AC[f]
            Vt=model.V_AC[t]
        
            thf=model.thetha_AC[f]
            tht=model.thetha_AC[t]
            
            Btt=np.imag(Ybus[1,1])
            Gtf=np.real(Ybus[1,0])
            Btf=np.imag(Ybus[1,0])
            
            Q   = -Vt*Vt*Btt + Vf*Vt*(Gtf*pyo.sin(tht - thf) - Btf*pyo.cos(tht - thf))
        else:  # 'from'
            Vf=model.V_AC[f]
            Vt=model.V_AC[t]
            
            Bff=np.imag(Ybus[0,0])
            Gft=np.real(Ybus[0,1])
            Bft=np.imag(Ybus[0,1])
            thf=model.thetha_AC[f]
            tht=model.thetha_AC[t]
            
            Q = -Vf*Vf*Bff + Vf*Vt*(Gft*pyo.sin(thf - tht) - Bft*pyo.cos(thf - tht))
        return Q

    def P_to_AC_line(model,line):   
        l = grid.lines_AC[line]
        Pto = calculate_P(model,l,'to')
        return model.PAC_to[line] == Pto
    
    def P_from_AC_line(model,line):       
       l = grid.lines_AC[line]
       Pfrom = calculate_P(model,l,'from')
       return model.PAC_from[line] == Pfrom
    
    def Q_to_AC_line(model,line):   
        l = grid.lines_AC[line]
        Qto = calculate_Q(model,l,'to')

        return model.QAC_to[line] == Qto
    
    def Q_from_AC_line(model,line):       
       l = grid.lines_AC[line]
       Qfrom = calculate_Q(model,l,'from')
      
       return model.QAC_from[line] == Qfrom
    
    def P_loss_AC_rule(model,line):
        return model.PAC_line_loss[line]== model.PAC_to[line]+model.PAC_from[line]
    
    
    model.Pto_AC_line_constraint   = pyo.Constraint(model.lines_AC, rule=P_to_AC_line)
    model.Pfrom_AC_line_constraint = pyo.Constraint(model.lines_AC, rule=P_from_AC_line)
    model.Qto_AC_line_constraint   = pyo.Constraint(model.lines_AC, rule=Q_to_AC_line)
    model.Qfrom_AC_line_constraint = pyo.Constraint(model.lines_AC, rule=Q_from_AC_line)
    model.P_AC_loss_constraint     = pyo.Constraint(model.lines_AC, rule=P_loss_AC_rule)
    
    def P_to_AC_line_exp(model,line):   
        l = grid.lines_AC_exp[line]
        Pto = calculate_P(model,l,'to')
        if model.robust_mode and line in model.lines_AC_exp_np0:
            return pyo.Constraint.Skip
        return model.exp_PAC_to[line] == Pto
    
    def P_from_AC_line_exp(model,line):       
       l = grid.lines_AC_exp[line]
       Pfrom = calculate_P(model,l,'from')
       if model.robust_mode and line in model.lines_AC_exp_np0:
           return pyo.Constraint.Skip
       return model.exp_PAC_from[line] == Pfrom
    
    def Q_to_AC_line_exp(model,line):   
        l = grid.lines_AC_exp[line]
        Qto = calculate_Q(model,l,'to')
        if model.robust_mode and line in model.lines_AC_exp_np0:
            return pyo.Constraint.Skip
        return model.exp_QAC_to[line] == Qto
    
    def Q_from_AC_line_exp(model,line):       
       l = grid.lines_AC_exp[line]
       Qfrom = calculate_Q(model,l,'from')

       if model.robust_mode and line in model.lines_AC_exp_np0:
           return pyo.Constraint.Skip
       return model.exp_QAC_from[line] == Qfrom
    
    def P_loss_AC_rule_exp(model,line):
        if model.robust_mode and line in model.lines_AC_exp_np0:
            return pyo.Constraint.Skip
        return model.exp_PAC_line_loss[line]== model.exp_PAC_to[line]+model.exp_PAC_from[line]
    
    
    if grid.TEP_AC:
        model.exp_Pto_AC_line_constraint   = pyo.Constraint(model.lines_AC_exp, rule=P_to_AC_line_exp)
        model.exp_Pfrom_AC_line_constraint = pyo.Constraint(model.lines_AC_exp, rule=P_from_AC_line_exp)
        model.exp_Qto_AC_line_constraint   = pyo.Constraint(model.lines_AC_exp, rule=Q_to_AC_line_exp)
        model.exp_Qfrom_AC_line_constraint = pyo.Constraint(model.lines_AC_exp, rule=Q_from_AC_line_exp)
        model.exp_P_AC_loss_constraint     = pyo.Constraint(model.lines_AC_exp, rule=P_loss_AC_rule_exp)
        
        if model.robust_mode:
            u_min_ac,u_max_ac,V_ini_AC,Theta_ini, P_know,Q_know,price = AC_nodes_info
            
            def _exp_flow_limit(line):
                if limit_flow_rate is False:
                    return S_lineACexp_limit[line]
                return S_lineACexp_limit[line] * limit_flow_rate
            
            def _bigm_bounds(line_obj, direction):
                f = line_obj.fromNode.nodeNumber
                t = line_obj.toNode.nodeNumber
                Y = line_obj.Ybus_branch
                Vf_max = float(u_max_ac[f])
                Vt_max = float(u_max_ac[t])
                
                if direction == 'Pto':
                    Gtt = float(np.real(Y[1, 1]))
                    Gtf = float(np.real(Y[1, 0]))
                    Btf = float(np.imag(Y[1, 0]))
                    bound = (Vt_max ** 2) * abs(Gtt) + (Vf_max * Vt_max) * float(np.sqrt(Gtf ** 2 + Btf ** 2))
                elif direction == 'Pfrom':
                    Gff = float(np.real(Y[0, 0]))
                    Gft = float(np.real(Y[0, 1]))
                    Bft = float(np.imag(Y[0, 1]))
                    bound = (Vf_max ** 2) * abs(Gff) + (Vf_max * Vt_max) * float(np.sqrt(Gft ** 2 + Bft ** 2))
                elif direction == 'Qto':
                    Btt = float(np.imag(Y[1, 1]))
                    Gtf = float(np.real(Y[1, 0]))
                    Btf = float(np.imag(Y[1, 0]))
                    bound = (Vt_max ** 2) * abs(Btt) + (Vf_max * Vt_max) * float(np.sqrt(Gtf ** 2 + Btf ** 2))
                elif direction == 'Qfrom':
                    Bff = float(np.imag(Y[0, 0]))
                    Gft = float(np.real(Y[0, 1]))
                    Bft = float(np.imag(Y[0, 1]))
                    bound = (Vf_max ** 2) * abs(Bff) + (Vf_max * Vt_max) * float(np.sqrt(Gft ** 2 + Bft ** 2))
                else:
                    bound = 0.0
                
                s = float(_exp_flow_limit(line_obj.lineNumber))
                return s + bound
            
            def _Pto_bigm_ub(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Pto')
                Pto = calculate_P(m, l, 'to')
                return m.exp_PAC_to[line] - Pto <= M * (1 - m.z_ACexp_active[line])
            def _Pto_bigm_lb(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Pto')
                Pto = calculate_P(m, l, 'to')
                return m.exp_PAC_to[line] - Pto >= -M * (1 - m.z_ACexp_active[line])
            
            def _Pfrom_bigm_ub(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Pfrom')
                Pfrom = calculate_P(m, l, 'from')
                return m.exp_PAC_from[line] - Pfrom <= M * (1 - m.z_ACexp_active[line])
            def _Pfrom_bigm_lb(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Pfrom')
                Pfrom = calculate_P(m, l, 'from')
                return m.exp_PAC_from[line] - Pfrom >= -M * (1 - m.z_ACexp_active[line])
            
            def _Qto_bigm_ub(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Qto')
                Qto = calculate_Q(m, l, 'to')
                return m.exp_QAC_to[line] - Qto <= M * (1 - m.z_ACexp_active[line])
            def _Qto_bigm_lb(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Qto')
                Qto = calculate_Q(m, l, 'to')
                return m.exp_QAC_to[line] - Qto >= -M * (1 - m.z_ACexp_active[line])
            
            def _Qfrom_bigm_ub(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Qfrom')
                Qfrom = calculate_Q(m, l, 'from')
                return m.exp_QAC_from[line] - Qfrom <= M * (1 - m.z_ACexp_active[line])
            def _Qfrom_bigm_lb(m, line):
                l = grid.lines_AC_exp[line]
                M = _bigm_bounds(l, 'Qfrom')
                Qfrom = calculate_Q(m, l, 'from')
                return m.exp_QAC_from[line] - Qfrom >= -M * (1 - m.z_ACexp_active[line])
            
            model.exp_Pto_AC_line_bigm_ub = pyo.Constraint(model.lines_AC_exp_np0, rule=_Pto_bigm_ub)
            model.exp_Pto_AC_line_bigm_lb = pyo.Constraint(model.lines_AC_exp_np0, rule=_Pto_bigm_lb)
            model.exp_Pfrom_AC_line_bigm_ub = pyo.Constraint(model.lines_AC_exp_np0, rule=_Pfrom_bigm_ub)
            model.exp_Pfrom_AC_line_bigm_lb = pyo.Constraint(model.lines_AC_exp_np0, rule=_Pfrom_bigm_lb)
            model.exp_Qto_AC_line_bigm_ub = pyo.Constraint(model.lines_AC_exp_np0, rule=_Qto_bigm_ub)
            model.exp_Qto_AC_line_bigm_lb = pyo.Constraint(model.lines_AC_exp_np0, rule=_Qto_bigm_lb)
            model.exp_Qfrom_AC_line_bigm_ub = pyo.Constraint(model.lines_AC_exp_np0, rule=_Qfrom_bigm_ub)
            model.exp_Qfrom_AC_line_bigm_lb = pyo.Constraint(model.lines_AC_exp_np0, rule=_Qfrom_bigm_lb)

            # Gate line losses so they cannot create objective/unboundedness when the corridor is inactive.
            def _loss_U(line):
                # Losses are modeled as P_to + P_from in per-unit; each side is bounded by the S limit.
                return 2.0 * float(_exp_flow_limit(line))

            def _loss_upper(m, line):
                return m.exp_PAC_line_loss[line] <= _loss_U(line) * m.z_ACexp_active[line]

            def _loss_lower(m, line):
                return m.exp_PAC_line_loss[line] >= 0

            def _loss_link_ub(m, line):
                sumP = m.exp_PAC_to[line] + m.exp_PAC_from[line]
                return m.exp_PAC_line_loss[line] - sumP <= _loss_U(line) * (1 - m.z_ACexp_active[line])

            def _loss_link_lb(m, line):
                sumP = m.exp_PAC_to[line] + m.exp_PAC_from[line]
                return m.exp_PAC_line_loss[line] - sumP >= -_loss_U(line) * (1 - m.z_ACexp_active[line])

            model.exp_PAC_loss_gate_upper = pyo.Constraint(model.lines_AC_exp_np0, rule=_loss_upper)
            model.exp_PAC_loss_gate_lower = pyo.Constraint(model.lines_AC_exp_np0, rule=_loss_lower)
            model.exp_PAC_loss_link_ub = pyo.Constraint(model.lines_AC_exp_np0, rule=_loss_link_ub)
            model.exp_PAC_loss_link_lb = pyo.Constraint(model.lines_AC_exp_np0, rule=_loss_link_lb)
    
    def P_to_AC_line_rec(model,line,state):   
        l = grid.lines_AC_rec[line]
        if state ==  0:
            Pto = calculate_P(model,l,'to')
        else:
            Pto = calculate_P(model,l,'to',idx='new')
        return model.rec_PAC_to[line,state] == Pto
    
    def P_from_AC_line_rec(model,line,state):       
       l = grid.lines_AC_rec[line]
       if state == 0:
           Pfrom = calculate_P(model,l,'from')
       else:
           Pfrom = calculate_P(model,l,'from',idx='new')
       return model.rec_PAC_from[line,state] == Pfrom
    
    def Q_to_AC_line_rec(model,line,state):   
        l = grid.lines_AC_rec[line]
        if state == 0:
            Qto = calculate_Q(model,l,'to')
        else:
            Qto = calculate_Q(model,l,'to',idx='new')
        return model.rec_QAC_to[line,state] == Qto
    
    def Q_from_AC_line_rec(model,line,state):       
       l = grid.lines_AC_rec[line]
       if state == 0:
           Qfrom = calculate_Q(model,l,'from')
       else:
           Qfrom = calculate_Q(model,l,'from',idx='new')
       return model.rec_QAC_from[line,state] == Qfrom
   
    def P_loss_AC_rule_rec(model,line):
        return model.rec_PAC_line_loss[line]== (model.rec_PAC_to[line,0]+model.rec_PAC_from[line,0])*(1-model.rec_branch[line])+\
                                               (model.rec_PAC_to[line,1]+model.rec_PAC_from[line,1])*model.rec_branch[line]  
    
    
    if grid.REC_AC:
     
        model.rec_Pto_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=P_to_AC_line_rec)
        model.rec_Pfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=P_from_AC_line_rec)
        model.rec_Qto_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=Q_to_AC_line_rec)
        model.rec_Qfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=Q_from_AC_line_rec)
        model.rec_P_AC_loss_constraint     = pyo.Constraint(model.lines_AC_rec, rule=P_loss_AC_rule_rec)
    
    def P_to_AC_line_ct(model,line,ct):   
        l = grid.lines_AC_ct[line]
        # Check if this is a fixed route with no cable selected (inactive line)
        if l.active_config < 0:
            return model.ct_PAC_to[line,ct] == 0
        Pto = calculate_P(model,l,'to',idx=ct)
        return model.ct_PAC_to[line,ct] == Pto
    
    def P_from_AC_line_ct(model,line,ct):       
       l = grid.lines_AC_ct[line]
       # Check if this is a fixed route with no cable selected (inactive line)
       if l.active_config < 0:
           return model.ct_PAC_from[line,ct] == 0
       Pfrom = calculate_P(model,l,'from',idx=ct)
       return model.ct_PAC_from[line,ct] == Pfrom
    
    def Q_to_AC_line_ct(model,line,ct):   
        l = grid.lines_AC_ct[line]
        # Check if this is a fixed route with no cable selected (inactive line)
        if l.active_config < 0:
            return model.ct_QAC_to[line,ct] == 0
        Qto = calculate_Q(model,l,'to',idx=ct)
        return model.ct_QAC_to[line,ct] == Qto
    
    def Q_from_AC_line_ct(model,line,ct):       
       l = grid.lines_AC_ct[line]
       # Check if this is a fixed route with no cable selected (inactive line)
       if l.active_config < 0 :
           return model.ct_QAC_from[line,ct] == 0
       Qfrom = calculate_Q(model,l,'from',idx=ct)
       return model.ct_QAC_from[line,ct] == Qfrom
   
    def P_loss_AC_rule_ct(model,line):
        l = grid.lines_AC_ct[line]
        if l.active_config < 0:
            return model.ct_PAC_line_loss[line] == 0
        loss = 0
        for ct in model.ct_set:
            loss += (model.ct_PAC_to[line,ct]+model.ct_PAC_from[line,ct])*(model.ct_branch[line,ct])
        return model.ct_PAC_line_loss[line]== loss
    
    

    if grid.CT_AC:   
        model.ct_Pto_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=P_to_AC_line_ct)
        model.ct_Pfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=P_from_AC_line_ct)
        model.ct_Qto_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=Q_to_AC_line_ct)
        model.ct_Qfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=Q_from_AC_line_ct)
        model.ct_P_AC_loss_constraint     = pyo.Constraint(model.lines_AC_ct, rule=P_loss_AC_rule_ct)

        
    s=1
    def P_to_AC_line_tf(model,trafo):   
        tf = grid.lines_AC_tf[trafo]
        f = tf.fromNode.nodeNumber
        t = tf.toNode.nodeNumber
        Vf=model.V_AC[f]
        Vt=model.V_AC[t]
        
        Gtt=np.real(tf.Ybus_branch[1,1])
        Gtf=np.real(tf.Ybus_branch[1,0])
        Btf=np.imag(tf.Ybus_branch[1,0])
        
      
        thf=model.thetha_AC[f]
        tht=model.thetha_AC[t]
        
        
        Pto= Vt*Vt*Gtt+ Vf/model.tf_m[tf]*Vt*(Gtf*pyo.cos(tht - thf) + Btf*pyo.sin(tht - thf))
       
        
        return model.tf_PAC_to[trafo] == Pto
    
    def P_from_AC_line_tf(model,trafo):       
       tf = grid.lines_AC_tf[trafo]
       f = tf.fromNode.nodeNumber
       t = tf.toNode.nodeNumber
       Vf=model.V_AC[f]
       Vt=model.V_AC[t]
       Gff=np.real(tf.Ybus_branch[0,0])
       Gft=np.real(tf.Ybus_branch[0,1])
       Bft=np.imag(tf.Ybus_branch[0,1])
       
    
       thf=model.thetha_AC[f]
       tht=model.thetha_AC[t]
       
       Pfrom= Vf*Vf*Gff/model.tf_m[tf]**2 + Vf/model.tf_m[tf]*Vt*(Gft*pyo.cos(thf - tht) + Bft*pyo.sin(thf - tht))

       return model.tf_PAC_from[trafo] == Pfrom
    
    def Q_to_AC_line_tf(model,trafo):   
        tf = grid.lines_AC_tf[trafo]
        f = tf.fromNode.nodeNumber
        t = tf.toNode.nodeNumber
        Vf=model.V_AC[f]
        Vt=model.V_AC[t]
       
        thf=model.thetha_AC[f]
        tht=model.thetha_AC[t]
        
        Btt=np.imag(tf.Ybus_branch[1,1])
        Gtf=np.real(tf.Ybus_branch[1,0])
        Btf=np.imag(tf.Ybus_branch[1,0])
        
        Qto   = -Vt*Vt*Btt + Vf/model.tf_m[tf]*Vt*(Gtf*pyo.sin(tht - thf) - Btf*pyo.cos(tht - thf))
         
        
        return model.tf_QAC_to[trafo] == Qto
    
    def Q_from_AC_line_tf(model,trafo):       
       tf = grid.lines_AC_tf[trafo]
       f = tf.fromNode.nodeNumber
       t = tf.toNode.nodeNumber
       Vf=model.V_AC[f]
       Vt=model.V_AC[t]
      
       Bff=np.imag(tf.Ybus_branch[0,0])
       Gft=np.real(tf.Ybus_branch[0,1])
       Bft=np.imag(tf.Ybus_branch[0,1])
       
       thf=model.thetha_AC[f]
       tht=model.thetha_AC[t]
       

       Qfrom = -Vf*Vf*Bff/model.tf_m[tf]**2 + Vf/model.tf_m[tf]*Vt*(Gft*pyo.sin(thf - tht) - Bft*pyo.cos(thf - tht))
      

       return model.tf_QAC_from[trafo] == Qfrom
    
    def P_loss_AC_rule_tf(model,trafo):
        return model.tf_PAC_line_loss[trafo]== model.tf_PAC_to[trafo]+model.PAC_from[trafo]
    
    
    if grid.TAP_tf:
        model.tf_Pto_AC_line_constraint   = pyo.Constraint(model.lines_AC_tf, rule=P_to_AC_line_tf)
        model.tf_Pfrom_AC_line_constraint = pyo.Constraint(model.lines_AC_tf, rule=P_from_AC_line_tf)
        model.tf_Qto_AC_line_constraint   = pyo.Constraint(model.lines_AC_tf, rule=Q_to_AC_line_tf)
        model.tf_Qfrom_AC_line_constraint = pyo.Constraint(model.lines_AC_tf, rule=Q_from_AC_line_tf)
        model.tf_P_AC_loss_constraint     = pyo.Constraint(model.lines_AC_tf, rule=P_loss_AC_rule_tf)
    "AC inequality constraints"
    #AC gen inequality
    def S_gen_AC_limit_rule(model,g):
        gen = grid.Generators[g]
        if gen.Max_S is None:
            return pyo.Constraint.Skip
        else:
            return model.PGi_gen[g]**2+model.QGi_gen[g]**2 <= (gen.Max_S*model.np_gen[g])**2 
    
    model.S_gen_AC_limit_constraint   = pyo.Constraint(model.gen_AC, rule=S_gen_AC_limit_rule)
    
    # Fix gen_active to 1 for generators where activate_gen_opf is False
    if grid.act_gen:
        def gen_active_fix_rule(model, g):
            gen = grid.Generators[g]
            if not gen.activate_gen_opf:
                return model.gen_active[g] == 1
            else:
                return pyo.Constraint.Skip
        
        model.gen_active_fix_constraint = pyo.Constraint(model.gen_AC, rule=gen_active_fix_rule)
    
    #AC Ren sources inequality
    
    def S_renS_AC_limit_rule(model,rs):
        ren_source = grid.RenSources[rs]
        if ren_source.Max_S is None or ren_source.connected =='DC':
            return pyo.Constraint.Skip
        else:    
            return (model.P_renSource[rs]*model.gamma[rs])**2+model.Q_renSource[rs]**2 <= ren_source.Max_S**2 
    
    model.S_renS_AC_limit_constraint   = pyo.Constraint(model.ren_sources, rule=S_renS_AC_limit_rule)
    
    
    if limit_flow_rate is not False:
        
        #AC lines inequality
        def S_to_AC_limit_rule(model,line):
            
            return model.PAC_to[line]**2+model.QAC_to[line]**2 <= (S_lineAC_limit[line]*limit_flow_rate)**2
        def S_from_AC_limit_rule(model,line):
            
            return model.PAC_from[line]**2+model.QAC_from[line]**2 <= (S_lineAC_limit[line]*limit_flow_rate)**2
        
        
        model.S_to_AC_limit_constraint   = pyo.Constraint(model.lines_AC, rule=S_to_AC_limit_rule)
        model.S_from_AC_limit_constraint = pyo.Constraint(model.lines_AC, rule=S_from_AC_limit_rule)
        
        def S_to_AC_limit_rule_exp(model,line):
            if model.robust_mode and line in model.lines_AC_exp_np0:
                npl = model.NumLinesACP[line]
                return (
                    npl * (model.exp_PAC_to[line]**2 + model.exp_QAC_to[line]**2)
                    <= npl * (S_lineACexp_limit[line] * limit_flow_rate)**2
                )
            return model.exp_PAC_to[line]**2+model.exp_QAC_to[line]**2 <= (S_lineACexp_limit[line]*limit_flow_rate)**2
        def S_from_AC_limit_rule_exp(model,line):
            if model.robust_mode and line in model.lines_AC_exp_np0:
                npl = model.NumLinesACP[line]
                return (
                    npl * (model.exp_PAC_from[line]**2 + model.exp_QAC_from[line]**2)
                    <= npl * (S_lineACexp_limit[line] * limit_flow_rate)**2
                )
            return model.exp_PAC_from[line]**2+model.exp_QAC_from[line]**2 <= (S_lineACexp_limit[line]*limit_flow_rate)**2
        
        if grid.TEP_AC:
            model.exp_S_to_AC_limit_constraint   = pyo.Constraint(model.lines_AC_exp, rule=S_to_AC_limit_rule_exp)
            model.exp_S_from_AC_limit_constraint = pyo.Constraint(model.lines_AC_exp, rule=S_from_AC_limit_rule_exp)
        
        def S_to_AC_limit_rule_tf(model,line):
            
            return model.tf_PAC_to[line]**2+model.tf_QAC_to[line]**2 <= (S_lineACtf_limit[line]*limit_flow_rate)**2
        def S_from_AC_limit_rule_tf(model,line):
            
            return model.tf_PAC_from[line]**2+model.tf_QAC_from[line]**2 <= (S_lineACtf_limit[line]*limit_flow_rate)**2
        
        if grid.TAP_tf:
            model.tf_S_to_AC_limit_constraint   = pyo.Constraint(model.lines_AC_tf, rule=S_to_AC_limit_rule_tf)
            model.tf_S_from_AC_limit_constraint = pyo.Constraint(model.lines_AC_tf, rule=S_from_AC_limit_rule_tf)
        
        def S_to_AC_line_rule_rec(model, line, state):
            if state == 0:
                return (model.rec_PAC_to[line,0]**2+model.rec_QAC_to[line,0]**2)*(1-model.rec_branch[line]) <= (S_lineACrec_lim[line]*limit_flow_rate)**2
            else:
                return (model.rec_PAC_to[line,1]**2+model.rec_QAC_to[line,1]**2)*model.rec_branch[line] <= (S_lineACrec_lim_new[line]*limit_flow_rate)**2 
        def S_from_AC_limit_rule_rec(model,line,state):
            if state == 0:
                return (model.rec_PAC_from[line,0]**2+model.rec_QAC_from[line,0]**2)*(1-model.rec_branch[line]) <= (S_lineACrec_lim[line]*limit_flow_rate)**2
            else:
                return (model.rec_PAC_from[line,1]**2+model.rec_QAC_from[line,1]**2)*model.rec_branch[line] <= (S_lineACrec_lim_new[line]*limit_flow_rate)**2
    
        if grid.REC_AC:
            model.rec_S_to_AC_limit_constraint   = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_to_AC_line_rule_rec)
            model.rec_S_from_AC_limit_constraint = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_from_AC_limit_rule_rec)
    
    
        def S_to_AC_line_rule_ct(model, line, ct):
            return (model.ct_PAC_to[line,ct]**2+model.ct_QAC_to[line,ct]**2)*(model.ct_branch[line,ct]) <= (S_lineACct_lim[line,ct]*limit_flow_rate)**2
        def S_from_AC_limit_rule_ct(model,line,ct):
            return (model.ct_PAC_from[line,ct]**2+model.ct_QAC_from[line,ct]**2)*(model.ct_branch[line,ct]) <= (S_lineACct_lim[line,ct]*limit_flow_rate)**2
    
        

        if grid.CT_AC:
            model.ct_S_to_AC_limit_constraint   = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=S_to_AC_line_rule_ct)
            model.ct_S_from_AC_limit_constraint = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=S_from_AC_limit_rule_ct)
        
    s=1
        

def DC_variables(model,grid,DC_info,TEP=False,limit_flow_rate=1):


    DC_Lists,DC_nodes_info,DC_lines_info,DCDC_info = DC_info
        
    lista_nodos_DC, lista_lineas_DC,DC_slack ,DC_nodes_connected_conv   = DC_Lists
    u_min_dc, u_max_dc ,V_ini_DC,P_known_DC,price_dc  = DC_nodes_info
    P_lineDC_limit,NP_lineDC    = DC_lines_info

    "Model Sets"
    model.nodes_DC   = pyo.Set(initialize=lista_nodos_DC)
    model.lines_DC   = pyo.Set(initialize=lista_lineas_DC)
    model.DC_slacks  = pyo.Set(initialize=DC_slack)

    "DC variables"
    #DC nodes variables
    def DC_V_slack_rule(model, node):
        return model.V_DC[node] == V_ini_DC[node]
    def Pbounds_lines(model, line):
        if limit_flow_rate is False:
            return (None,None)
        return (-P_lineDC_limit[line]*limit_flow_rate, P_lineDC_limit[line]*limit_flow_rate)
       
    
    def P_conv_DC_node_bounds(model,node): #This limits the varable of those DC nodes that do not have a converter connected 
         if node in DC_nodes_connected_conv:
             return (None,None)
         else:
             return (0,0)
         
    def Pren_bounds_DC(model, node):
        nDC = grid.nodes_DC[node]
        if nDC.connected_RenSource == []:
            return (0,0)
        else:
            return (None,None)

    model.V_DC = pyo.Var(model.nodes_DC, bounds=lambda model, node: (u_min_dc[node], u_max_dc[node]), initialize=V_ini_DC)
    model.P_known_DC = pyo.Param(model.nodes_DC, initialize=P_known_DC,mutable=True)
    model.PGi_ren_DC = pyo.Var(model.nodes_DC, bounds=Pren_bounds_DC,initialize=0)

    def PGi_opt_bounds_DC(model, node):
        nDC = grid.nodes_DC[node]
        if nDC.connected_gen == []:
            return (0,0)
        else:
            return (None,None)
            
  
    
    model.PGi_opt_DC = pyo.Var(model.nodes_DC, bounds=PGi_opt_bounds_DC, initialize=0)

    #if not TEP:
    model.DC_V_slack_constraint = pyo.Constraint(model.DC_slacks, rule=DC_V_slack_rule)
    
    #DC Lines variables
    

    model.PDC_to       = pyo.Var(model.lines_DC,bounds=Pbounds_lines ,  initialize=0)
    model.PDC_from     = pyo.Var(model.lines_DC,bounds=Pbounds_lines , initialize=0)
    model.PDC_line_loss= pyo.Var(model.lines_DC,bounds=Pbounds_lines , initialize=0)
    
    
    model.P_conv_DC = pyo.Var(model.nodes_DC, bounds=P_conv_DC_node_bounds,initialize=0)
   
    if grid.CDC:
        lista_DCDC,P_DCDC_limit,Pset_DCDC=DCDC_info
        "Converter Variables"
        def P_DCDC_bounds(model, node):
            nDC = grid.nodes_DC[node]
            if not nDC.connected_DCDC_to and not nDC.connected_DCDC_from:
                return (0,0)
            else:
                return (None,None)

        def DCDC_opt_bounds(model,conv):
            return (-P_DCDC_limit[conv],P_DCDC_limit[conv])
        
        
        model.P_DCDC_to = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds,initialize=0)
        model.P_DCDC_from = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds,initialize=0)
        model.P_DCDC = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds,initialize=0)

        model.DCDC_conv = pyo.Set(initialize=lista_DCDC)
        model.cn_DCDC_from = pyo.Var(model.DCDC_conv, bounds=DCDC_opt_bounds,initialize=0)
        model.cn_DCDC_to = pyo.Var(model.DCDC_conv, bounds=DCDC_opt_bounds,initialize=0)
        model.CDC_loss= pyo.Var(model.DCDC_conv, initialize=0)

def DC_constraints(model,grid):
    
    
    

    "DC equality constraints"
    #DC node constraints
    
    def Gen_PREN_rule_DC(model,node):
       nDC = grid.nodes_DC[node]
       P_gen = sum(model.P_renSource[rs.rsNumber]*model.gamma[rs.rsNumber]*model.np_rsgen[rs.rsNumber] for rs in nDC.connected_RenSource)                  
       return  model.PGi_ren_DC[node] ==   P_gen
   
    def Gen_P_rule_DC(model,node):
        nDC = grid.nodes_DC[node]
        P_gen = sum(model.PGi_gen_DC[gen.genNumber_DC]*model.np_gen_DC[gen.genNumber_DC] for gen in nDC.connected_gen)                  
        return  model.PGi_opt_DC[node] ==   P_gen


    def P_DC_node_rule(model, node):
        i = node
        P_sum = 0
        for k in range(grid.nn_DC):
            Y = grid.Ybus_DC[i, k]
            if k != i:
                if Y != 0:
                    line = grid.get_lineDC_by_nodes(i, k)
                    pol = line.pol
                    G = 1/line.R
                    
                    P_sum += pol*model.V_DC[i] * (model.V_DC[i]-model.V_DC[k])*(G)*model.NumLinesDCP[line.lineNumber]

        P_var = model.P_known_DC[node]+ model.PGi_ren_DC[node]+model.PGi_opt_DC[node]
        if grid.ACmode:
            P_var += model.P_conv_DC[node]
        if grid.CDC:
            P_var += model.P_DCDC[node]
        return P_sum ==  P_var

    # def P_DC_noconv_rule(model, node):
    #     return model.P_conv_DC[node] == 0
    
    model.Gen_PREN_constraint_DC =pyo.Constraint(model.nodes_DC, rule=Gen_PREN_rule_DC)
    model.Gen_P_constraint_DC    =pyo.Constraint(model.nodes_DC, rule=Gen_P_rule_DC)
    model.P_DC_node_constraint = pyo.Constraint(model.nodes_DC, rule=P_DC_node_rule)
    
    #DC lines equality constraints
    
    def P_from_DC_line(model,line):       
        l = grid.lines_DC[line]
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        pol = l.pol
        
        Pfrom= (model.V_DC[t]-model.V_DC[f])*grid.Ybus_DC[f,t]*model.V_DC[f]*pol
        
        return model.PDC_from[line] == Pfrom
    
    def P_to_DC_line(model,line):   
        l = grid.lines_DC[line]
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        pol = l.pol

         
        Pto= (model.V_DC[f]-model.V_DC[t])*grid.Ybus_DC[t,f]*model.V_DC[t]*pol 
        
        
        return model.PDC_to[line] == Pto
    
    def P_loss_DC_line_rule(model,line):
        
        return model.PDC_line_loss[line]==(model.PDC_from[line]+ model.PDC_to[line])
    
    model.Pfrom_DC_line_constraint   = pyo.Constraint(model.lines_DC, rule=P_from_DC_line)
    model.Pto_DC_line_constraint     = pyo.Constraint(model.lines_DC, rule=P_to_DC_line)
    model.Ploss_DC_line_constraint   = pyo.Constraint(model.lines_DC, rule=P_loss_DC_line_rule)    
     
    if grid.CDC:

        def P_DCDC_rule(model,node): 
            return  model.P_DCDC[node] ==   model.P_DCDC_to[node] + model.P_DCDC_from[node]

        def P_DCDC_to_rule(model,node):
            nDC = grid.nodes_DC[node]
            P_DCDC = sum(model.cn_DCDC_to[conv] for conv in nDC.connected_DCDC_to)     
            return  model.P_DCDC_to[node] ==   P_DCDC
        
        def P_DCDC_from_rule(model,node):
            nDC = grid.nodes_DC[node]
            P_DCDC = sum(model.cn_DCDC_from[conv] for conv in nDC.connected_DCDC_from)     
            return  model.P_DCDC_from[node] ==   P_DCDC


        def DCDC_relation_rule(model,conv):  
            return  model.cn_DCDC_from[conv] + model.cn_DCDC_to[conv]+ model.CDC_loss[conv] == 0
        

        def DCDC_loss_rule(model,conv):
            cn = grid.Converters_DCDC[conv]
            nt = cn.toNode.nodeNumber
            return  model.CDC_loss[conv] == (model.cn_DCDC_to[conv]/model.V_DC[nt])**2*cn.r
        
        model.P_DCDC_rule = pyo.Constraint(model.nodes_DC, rule=P_DCDC_rule)
        model.P_DCDC_to_constraint = pyo.Constraint(model.nodes_DC, rule=P_DCDC_to_rule)
        model.P_DCDC_from_constraint = pyo.Constraint(model.nodes_DC, rule=P_DCDC_from_rule)
        model.DCDC_relation_constraint = pyo.Constraint(model.DCDC_conv, rule=DCDC_relation_rule)
        model.DCDC_loss_constraint = pyo.Constraint(model.DCDC_conv, rule=DCDC_loss_rule)
    "DC inequality constraints"
    
    #they set in the variables themselves
       

def Converter_variables(model,grid,Conv_info):
    
    Conv_Lists, Conv_Volt = Conv_info
        
    lista_conv,np_conv_i = Conv_Lists
    u_c_min,u_c_max,S_limit_conv,P_conv_limit = Conv_Volt


    "Model Sets"
    model.conv       = pyo.Set(initialize=lista_conv)

    "Converter Variables"
    def conv_opt_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if not nAC.connected_conv:
            return (0,0)
        else:
            return (None,None)
        
    model.Uc   = pyo.Var(model.conv, bounds=lambda model, conv: (u_c_min[conv], u_c_max[conv]), initialize=1) 
    model.Uf   = pyo.Var(model.conv, bounds=lambda model, conv: (u_c_min[conv], u_c_max[conv]), initialize=1) 
    model.th_c   = pyo.Var(model.conv, bounds=(-1.6, 1.6), initialize=0) 
    model.th_f   = pyo.Var(model.conv, bounds=(-1.6, 1.6), initialize=0) 
    model.P_AC_loss_conv= pyo.Var(model.conv,within=pyo.NonNegativeReals, initialize=0)
    
        
    model.P_conv_loss = pyo.Var(model.conv, initialize=0)

    model.P_conv_AC = pyo.Var(model.nodes_AC,bounds=conv_opt_bounds, initialize=0)
    model.Q_conv_AC = pyo.Var(model.nodes_AC,bounds=conv_opt_bounds, initialize=0)
    
    model.P_conv_s_AC  = pyo.Var(model.conv, initialize=0)   
    model.Q_conv_s_AC = pyo.Var(model.conv, initialize=0)

    model.P_conv_c_AC  = pyo.Var(model.conv, initialize=0.0001)   
    model.Q_conv_c_AC = pyo.Var(model.conv, initialize=0.0001)
    
    model.P_conv_c_AC_sq = pyo.Var(model.conv, bounds=(1e-100,None), initialize=0.1)   
    model.Q_conv_c_AC_sq = pyo.Var(model.conv, bounds=(1e-100,None), initialize=0.1)
    
def Converter_constraints(model,grid,Conv_info):
    Conv_Lists, Conv_Volt = Conv_info
  
    u_c_min,u_c_max,S_limit_conv,P_conv_limit = Conv_Volt
    
    "Converter equality Constraints"
    
    def Conv_Ps_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
        
       Gc  = element.Gc   
       Bc  = element.Bc   
       Gtf = element.Gtf  
       Btf = element.Btf  
       Bf  = element.Bf   
       
       if element.Bf == 0:
           Ztf = element.Ztf
           Zc = element.Zc
           Zeq = Ztf+Zc
           if Zeq == 0:
               return model.thetha_AC[nAC]==model.th_c[conv]
           Yeq = 1/Zeq
           
           Gc = np.real(Yeq)  
           Bc = np.imag(Yeq)  
           
           Ps = -model.V_AC[nAC]**2*Gc+model.V_AC[nAC]*model.Uc[conv] * \
               (Gc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv])+Bc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv]))
          

       elif element.Gtf == 0:
   
           Bcf = Bc+Bf

           Ps = -model.V_AC[nAC]**2*Gc+model.V_AC[nAC]*model.Uc[conv] * \
               (Gc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv])+Bc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv]))
          
           
       else:

           Ps = -model.V_AC[nAC]**2*Gtf+model.V_AC[nAC]*model.Uf[conv] * \
               (Gtf*pyo.cos(model.thetha_AC[nAC]-model.th_f[conv])+Btf*pyo.sin(model.thetha_AC[nAC]-model.th_f[conv]))
           
       return model.P_conv_s_AC[conv]-Ps==0
           
    def Conv_Qs_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
       
       Gc = element.Gc    
       Bc = element.Bc    
       Gtf = element.Gtf  
       Btf = element.Btf  
       Bf = element.Bf    
       
       if element.Bf == 0:
           Ztf = element.Ztf
           Zc = element.Zc
           Zeq = Ztf+Zc
           if Zeq == 0:
               return model.V_AC[nAC]==model.Uc[conv]
           Yeq = 1/Zeq

           Gc = np.real(Yeq)  
           Bc = np.imag(Yeq)  
           
           Qs = model.V_AC[nAC]**2*Bc+model.V_AC[nAC]*model.Uc[conv]*(Gc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv])-Bc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv]))

       elif element.Gtf == 0:
  
           Bcf = Bc+Bf

           Qs = model.V_AC[nAC]**2*Bcf+model.V_AC[nAC]*model.Uc[conv] * \
                (Gc*pyo.sin(model.thetha_AC[nAC]-model.th_f[conv])-Bc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv]))
         
       else:
                         
           Qs = model.V_AC[nAC]**2*Btf+model.V_AC[nAC]*model.Uf[conv] * \
               (Gtf*pyo.sin(model.thetha_AC[nAC]-model.th_f[conv])-Btf*pyo.cos(model.thetha_AC[nAC]-model.th_f[conv]))

       return model.Q_conv_s_AC[conv]-Qs==0
       
   
    

    def Conv_Pc_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
       
       Gc = element.Gc    
       Bc = element.Bc    
       Gtf = element.Gtf  
       Btf = element.Btf  
       Bf = element.Bf    
       
       if element.Bf == 0:
           Ztf = element.Ztf
           Zc = element.Zc
           Zeq = Ztf+Zc
           if Zeq == 0:
               return -model.P_conv_s_AC[conv]+model.P_conv_c_AC[conv]==0
           
           Yeq = 1/Zeq

           Gc = np.real(Yeq)  
           Bc = np.imag(Yeq)  
           
           Pc = model.Uc[conv]**2*Gc-model.V_AC[nAC]*model.Uc[conv] * \
               (Gc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv])-Bc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv]))
          

       elif element.Gtf == 0:
                    
           Bcf = Bc+Bf
        
           Pc = model.Uc[conv]**2*Gc-model.V_AC[nAC]*model.Uc[conv]*(Gc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv])-Bc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv]))
           
           
       else:
           
           Pc = model.Uc[conv]**2*Gc-model.Uf[conv]*model.Uc[conv]*(Gc*pyo.cos(model.th_f[conv]-model.th_c[conv])-Bc*pyo.sin(model.th_f[conv]-model.th_c[conv]))
           
           
       return -Pc+model.P_conv_c_AC[conv]==0
           
    def Conv_Qc_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
        
       Gc = element.Gc    
       Bc = element.Bc    
       Gtf = element.Gtf  
       Btf = element.Btf  
       Bf = element.Bf    
       
       if element.Bf == 0:
           Ztf = element.Ztf
           Zc = element.Zc
           Zeq = Ztf+Zc
           if Zeq == 0:
               return -model.Q_conv_s_AC[conv]+model.Q_conv_c_AC[conv]==0
           Yeq = 1/Zeq

           Gc = np.real(Yeq)  
           Bc = np.imag(Yeq)  
           
           
           Qc = -model.Uc[conv]**2*Bc+model.V_AC[nAC]*model.Uc[conv] * \
               (Gc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv])+Bc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv]))

       elif element.Gtf == 0:
           
           Bcf = Bc+Bf

           Qc = -model.Uc[conv]*model.Uc[conv]*Bc+model.V_AC[nAC]*model.Uc[conv] * \
               (Gc*pyo.sin(model.thetha_AC[nAC]-model.th_c[conv])+Bc*pyo.cos(model.thetha_AC[nAC]-model.th_c[conv]))
     
       else:
           
           Qc = -model.Uc[conv]*model.Uc[conv]*Bc+model.Uf[conv]*model.Uc[conv] * \
               (Gc*pyo.sin(model.th_f[conv]-model.th_c[conv])+Bc*pyo.cos(model.th_f[conv]-model.th_c[conv]))

       return -Qc+model.Q_conv_c_AC[conv]==0




    def Conv_F1_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber

            
       if element.Bf == 0 or element.Gtf == 0:
        return pyo.Constraint.Skip
           
       else:
           Gc = element.Gc    
           Bc = element.Bc    
           Gtf = element.Gtf  
           Btf = element.Btf  
           Bf = element.Bf    
                
           Psf = model.Uf[conv]*model.Uf[conv]*Gtf-model.Uf[conv]*model.V_AC[nAC] * \
               (Gtf*pyo.cos(model.thetha_AC[nAC]-model.th_f[conv])-Btf*pyo.sin(model.thetha_AC[nAC]-model.th_f[conv]))
      
           Pcf = -model.Uf[conv]*model.Uf[conv]*Gc+model.Uf[conv]*model.Uc[conv] * \
               (Gc*pyo.cos(model.th_f[conv]-model.th_c[conv])+Bc*pyo.sin(model.th_f[conv]-model.th_c[conv]))
        

           F1 = Pcf-Psf
            
       return F1==0

    def Conv_F2_rule(model,conv):
       element=grid.Converters_ACDC[conv]
       nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
       nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
       constraints = pyo.ConstraintList()
       
       if element.Bf == 0 or element.Gtf == 0:
        return pyo.Constraint.Skip
           
       else:
           
           Gc = element.Gc    
           Bc = element.Bc    
           Gtf = element.Gtf  
           Btf = element.Btf  
           Bf = element.Bf    

         
           Qsf = -model.Uf[conv]**2*Btf+model.Uf[conv]*model.V_AC[nAC] * \
               (Gtf*pyo.sin(model.thetha_AC[nAC]-model.th_f[conv])+Btf*pyo.cos(model.thetha_AC[nAC]-model.th_f[conv]))

         
           Qcf = model.Uf[conv]**2*Bc+model.Uf[conv]*model.Uc[conv] * \
               (Gc*pyo.sin(model.th_f[conv]-model.th_c[conv])-Bc*pyo.cos(model.th_f[conv]-model.th_c[conv]))

           Qf = -model.Uf[conv]*model.Uf[conv]*Bf

           

           F2 = Qcf-Qsf-Qf
           
           
            
       return F2==0

    model.Conv_Ps_constraint = pyo.Constraint(model.conv,rule=Conv_Ps_rule)
    model.Conv_Qs_constraint = pyo.Constraint(model.conv,rule=Conv_Qs_rule)
    model.Conv_Pc_constraint = pyo.Constraint(model.conv,rule=Conv_Pc_rule)
    model.Conv_Qc_constraint = pyo.Constraint(model.conv,rule=Conv_Qc_rule)
    model.Conv_F1_constraint = pyo.Constraint(model.conv,rule=Conv_F1_rule)
    model.Conv_F2_constraint = pyo.Constraint(model.conv,rule=Conv_F2_rule)
    
    # Adds all converters in the AC nodes they are connected to
    def Conv_PAC_rule(model,node):
       nAC = grid.nodes_AC[node]
       P_conv = sum(model.P_conv_s_AC[conv]*model.np_conv[conv] for conv in nAC.connected_conv)
                  
       return  model.P_conv_AC[node] ==   P_conv
           
    def Conv_Q_rule(model,node):
       nAC = grid.nodes_AC[node]
       Q_conv = sum(model.Q_conv_s_AC[conv]*model.np_conv[conv] for conv in nAC.connected_conv)
    
       return   model.Q_conv_AC[node] ==   Q_conv       
         

    # IGBTs losses
    def Conv_DC_rule(model, conv):
        nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
        nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber

        return model.P_conv_c_AC[conv]*model.np_conv[conv]+model.P_conv_DC[nDC] + model.P_conv_loss[conv]*model.np_conv[conv] == 0

    def Conv_loss_rule(model, conv):
        element=grid.Converters_ACDC[conv]
        nAC = grid.Converters_ACDC[conv].Node_AC.nodeNumber
        nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
        a = grid.Converters_ACDC[conv].a_conv 
        b = grid.Converters_ACDC[conv].b_conv
      
        if element.power_loss_model == 'MMC':
             Vdc = model.V_DC[element.Node_DC.nodeNumber]
             Pc  = model.P_conv_c_AC[conv]
             Ra  = element.ra
             
             I = (-Vdc +pyo.sqrt(Vdc**2-4*Ra*Pc/3))/(-2*Ra)

             P_loss = 3*I**2*Ra
             
        else:
            # current = pyo.sqrt(model.P_conv_c_AC_sq[conv]+model.Q_conv_c_AC_sq[conv])/(model.Uc[conv])
            currentsqr = (model.P_conv_c_AC[conv]**2+model.Q_conv_c_AC[conv]**2)/(model.Uc[conv]**2)
    
            
    
            # c_inver = (element.c_inver_og /model.np_conv[conv])*element.basekA**2/grid.S_base
            # c_rect = (element.c_rect_og   /model.np_conv[conv])*element.basekA**2/grid.S_base 
            
            c_inver=grid.Converters_ACDC[conv].c_inver 
            c_rect=grid.Converters_ACDC[conv].c_rect   
        
               
        
        
            P_loss = a  +c_rect * currentsqr
    
        
        return model.P_conv_loss[conv] == P_loss


    model.Conv_DC_constraint = pyo.Constraint(model.conv, rule=Conv_DC_rule)
    model.Conv_PAC_constraint = pyo.Constraint(model.nodes_AC, rule=Conv_PAC_rule)
    model.Conv_QAC_constraint = pyo.Constraint(model.nodes_AC, rule=Conv_Q_rule)
    model.Conv_loss_constraint = pyo.Constraint(model.conv, rule=Conv_loss_rule)
   

    "Converters inequality constraints"
    
    def Conv_ACc_Limit_rule(model, conv):
        return (model.P_conv_c_AC[conv]**2+model.Q_conv_c_AC[conv]**2) <= (S_limit_conv[conv])**2 
    
    
    def Conv_ACs_Limit_rule(model, conv):
        return (model.P_conv_s_AC[conv]**2+model.Q_conv_s_AC[conv]**2) <= (S_limit_conv[conv])**2
    
    def Conv_DC_Limit_rule(model, conv):
        nDC = grid.Converters_ACDC[conv].Node_DC.nodeNumber
        return (model.P_conv_c_AC[conv]+ model.P_conv_loss[conv])**2 <= (P_conv_limit[nDC])**2
    
    
   #AC elements losses 
    def Conv_AC_loss1(model,conv):
        return  model.P_AC_loss_conv[conv] >= model.P_conv_c_AC[conv]-model.P_conv_s_AC[conv] 
    def Conv_AC_loss2(model,conv):
        return  model.P_AC_loss_conv[conv] >= model.P_conv_s_AC[conv]-model.P_conv_c_AC[conv]
    

    model.Conv_ACc_Limit_constraint = pyo.Constraint(model.conv, rule=Conv_ACc_Limit_rule)
    model.Conv_ACs_Limit_constraint = pyo.Constraint(model.conv, rule=Conv_ACs_Limit_rule)
    model.Conv_DC_Limit_constraint = pyo.Constraint(model.conv, rule=Conv_DC_Limit_rule)
    model.Conv_AC_loss_constraint1= pyo.Constraint(model.conv,rule=Conv_AC_loss1)
    model.Conv_AC_loss_constraint2= pyo.Constraint(model.conv,rule=Conv_AC_loss2)
    
    

def price_zone_variables(model,grid,Price_Zone_info,AC_info,DC_info,gen_info):
    
    AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info
    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    lf,qf,fc,np_gen,lista_gen = gen_AC_info
    
    u_min_ac,u_max_ac,V_ini_AC,Theta_ini, P_know,Q_know,price = AC_nodes_info
    
    if grid.DCmode:
        DC_Lists,DC_nodes_info,DC_lines_info,DCDC_info = DC_info
        lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC = gen_DC_info
        u_min_dc, u_max_dc ,V_ini_DC,P_known_DC,price_dc  = DC_nodes_info

    Price_Zone_Lists,Price_Zone_lim = Price_Zone_info   
    lista_M, node2price_zone ,price_zone2node=Price_Zone_Lists
    price_zone_as,price_zone_bs,PGL_min, PGL_max = Price_Zone_lim

    "Price Zone Sets"
    model.M = pyo.Set(initialize=lista_M)


    "Price_Zone Variables"
    def Price_Zone_P_bounds(model, price_zone):
        nM = grid.Price_Zones[price_zone]
        return (nM.PGL_min,nM.PGL_max)
    
    def lf_bounds(model, g):
        gen = grid.Generators[g]
        if gen.price_zone_link:
            return (None,None)
        else:
            return (lf[g],lf[g])
    def lf_bounds_DC(model, g):
        gen = grid.Generators_DC[g]
        if gen.price_zone_link:
            return (None,None)
        else:
            return (lf_DC[g],lf_DC[g])


    model.PN = pyo.Var(model.M,bounds=Price_Zone_P_bounds,initialize=0)
    model.PGL_min= pyo.Param(model.M,initialize=PGL_min,mutable=True)
    model.PGL_max= pyo.Param(model.M,initialize=PGL_max,mutable=True)
    # model.PN_load = pyo.Var(model.M)
    if grid.ACmode:
        model.price = pyo.Var(model.nodes_AC,initialize=price)
        model.lf = pyo.Var (model.gen_AC,bounds=lf_bounds,  initialize=lf)
    if grid.DCmode:
        model.price_dc = pyo.Var(model.nodes_DC,initialize=price_dc)
        model.lf_dc = pyo.Var (model.gen_DC,bounds=lf_bounds_DC,  initialize=lf_DC)
        
    
    model.price_zone_price = pyo.Var(model.M,initialize=0)
    model.price_zone_a = pyo.Param(model.M,initialize=price_zone_as,mutable=True)
    model.price_zone_b = pyo.Param(model.M,initialize=price_zone_bs,mutable=True)
    model.SocialCost = pyo.Var(model.M,initialize=0)


def price_zone_constraints(model,grid,Price_Zone_info):

    Price_Zone_Lists,Price_Zone_lim = Price_Zone_info   
    lista_M, node2price_zone ,price_zone2node=Price_Zone_Lists
    price_zone_as,price_zone_bs,PGL_min, PGL_max = Price_Zone_lim

    "Price Zone equality constraints"
    
    def price_zone_price_formula(model,price_zone):
        from .Classes import Price_Zone
        if type(grid.Price_Zones[price_zone]) is Price_Zone:
            return model.price_zone_price[price_zone]==2*model.price_zone_a[price_zone]*model.PN[price_zone]*grid.S_base+model.price_zone_b[price_zone]
        else :
            return pyo.Constraint.Skip
    
    def node_price_set_AC(model,node):
        try: 
            price_zone=node2price_zone['AC'][node]
            return model.price_zone_price[price_zone]== model.price[node] 
        except:
            return model.price[node]==0
    def node_price_set_DC(model,node):
        try: 
            price_zone=node2price_zone['DC'][node]
            return model.price_zone_price[price_zone]== model.price_dc[node] 
        except:
            return model.price_dc[node]==0
    
    
    def P_price_zone(model,price_zone):
        Pm_AC=sum(model.P_known_AC[node]   + model.PGi_ren[node] + model.PGi_opt[node] for node in price_zone2node['AC'][price_zone])
        Pm_DC=sum(model.P_known_DC[node_DC]+ model.PGi_ren_DC[node_DC] for node_DC in price_zone2node['DC'][price_zone])
        
        return model.PN[price_zone] ==Pm_AC+Pm_DC

    def PZ_cost_of_generation(model,price_zone):
        from .Classes import Price_Zone
        if type(grid.Price_Zones[price_zone]) is Price_Zone:
            return model.SocialCost[price_zone]== model.price_zone_a[price_zone]*(model.PN[price_zone]*grid.S_base)**2+model.price_zone_b[price_zone]*(model.PN[price_zone]*grid.S_base)
        else:
            return model.SocialCost[price_zone]==0
        
    def Price_link(model,price_zone):
        from .Classes import Price_Zone
        if type(grid.Price_Zones[price_zone]) is Price_Zone:
            linked_price_zone=grid.Price_Zones[price_zone].linked_price_zone
            if linked_price_zone is not None:   
                return model.price_zone_price[price_zone] == model.price_zone_price[linked_price_zone.price_zone_num]
            else: 
                return pyo.Constraint.Skip
        else:
            return pyo.Constraint.Skip
    
    # def MTDC_price_link(model,price_zone):
    #     from PyFlow_ACDC import MTDCPrice_Zone
    #     if isinstance(grid.Price_Zones[price_zone], MTDCPrice_Zone): 
    #          pricing_strategy = grid.Price_Zones[price_zone].pricing_strategy
    #          linked_price_zones = [mkt.price_zone_num for mkt in grid.Price_Zones[price_zone].linked_price_zones]
    #          if pricing_strategy == 'min':
    #             return model.price_zone_price[price_zone] <= min(model.price_zone_price[mkt] for mkt in linked_price_zones)  # Set upper limit to the minimum of linked price_zones
    
    #          elif pricing_strategy == 'max':
    #             return model.price_zone_price[price_zone] >= max(model.price_zone_price[mkt] for mkt in linked_price_zones)  # Set lower limit to the maximum of linked price_zones
    
    #          elif pricing_strategy == 'avg':
    #             return model.price_zone_price[price_zone] == sum(model.price_zone_price[mkt] for mkt in linked_price_zones) / len(linked_price_zones)

    #          else:
    #             raise ValueError(f"Unsupported pricing strategy: {pricing_strategy}")
    #             return pyo.Constraint.Skip
    #     else:
    #         return pyo.Constraint.Skip
        
    grid.OPF_Price_Zones_constraints_used=True
    model.price_zone_gen_link = pyo.ConstraintList()
    for node in grid.nodes_AC:  # Loop through all nodes
        nAC = node.nodeNumber
        for g in node.connected_gen:  # Loop through all generators in the node
            if g.price_zone_link:
                model.price_zone_gen_link.add(model.price[nAC] == model.lf[g.genNumber])
    
        
        
    model.price_zone_price_constraint = pyo.Constraint(model.M,rule=price_zone_price_formula)
    model.price_zone_price_link_ = pyo.Constraint(model.M,rule=Price_link)
    
    model.price_zone_MTDC_link = pyo.ConstraintList()
    
    from .Classes import MTDCPrice_Zone
    # Step 1: Define sets for the MTDC price_zones and linked price_zones
    model.MTDCPrice_Zones = pyo.Set(initialize=[m for m in model.M if isinstance(grid.Price_Zones[m], MTDCPrice_Zone)])
    
    for mtdc_price_zone in model.MTDCPrice_Zones:
        linked_price_zones = [mkt.price_zone_num for mkt in grid.Price_Zones[mtdc_price_zone].linked_price_zones]
        
        if not linked_price_zones:
            break
        # Define a set of linked price_zones for each MTDC price_zone
        # model.LinkedPrice_Zones = pyo.Set(initialize=linked_price_zones)
    
        pricing_strategy = grid.Price_Zones[mtdc_price_zone].pricing_strategy
    
        if pricing_strategy == 'min':
            grid.MixedBinCont=True
            # Step 1: Create distinct binary variables for each MTDC price_zone and its linked price_zones
            model.y_min = pyo.Var(linked_price_zones, model.MTDCPrice_Zones, domain=pyo.Binary, initialize=1)

            # Step 2: Ensure MTDC price_zone price is less than or equal to all linked price_zone prices
            for mkt in linked_price_zones:
                model.price_zone_MTDC_link.add(model.price_zone_price[mtdc_price_zone] <= model.price_zone_price[mkt])

            # Step 3: Ensure that the MTDC price_zone price is equal to one of the linked price_zone prices
            model.price_zone_MTDC_link.add(sum(model.y_min[mkt, mtdc_price_zone] for mkt in linked_price_zones) == 1)

            # Step 4: Link the binary variable to the actual price_zone prices
            for mkt in linked_price_zones:
                model.price_zone_MTDC_link.add(model.price_zone_price[mtdc_price_zone] == model.price_zone_price[mkt] * model.y_min[mkt, mtdc_price_zone])

        elif pricing_strategy == 'max':
            grid.MixedBinCont=True
            # Step 2: Create binary variables indexed by both the linked price_zones and the MTDC price_zone
            model.y_max = pyo.Var(linked_price_zones, model.MTDCPrice_Zones, domain=pyo.Binary, initialize=0)
    
            # Step 3: Ensure MTDC price_zone price is greater than or equal to all linked price_zone prices
            for mkt in linked_price_zones:
                model.price_zone_MTDC_link.add(model.price_zone_price[mtdc_price_zone] >= model.price_zone_price[mkt])
    
            # Step 4: Ensure that the MTDC price_zone price is equal to one of the linked price_zone prices
            model.price_zone_MTDC_link.add(sum(model.y_max[mkt, mtdc_price_zone] for mkt in linked_price_zones) == 1)
    
            # Step 5: Link the binary variable to the actual price_zone prices
            for mkt in linked_price_zones:
                model.price_zone_MTDC_link.add(model.price_zone_price[mtdc_price_zone] == model.price_zone_price[mkt] * model.y_max[mkt, mtdc_price_zone]/sum(model.y_max[mkt, mtdc_price_zone] for mkt in linked_price_zones))
    
        elif pricing_strategy == 'avg':
            # MTDC price_zone price equals the average of linked price_zone prices
            avg_expr = sum(model.price_zone_price[mkt] for mkt in linked_price_zones) / len(linked_price_zones)
            model.price_zone_MTDC_link.add(model.price_zone_price[mtdc_price_zone] == avg_expr)
    
        else:
            raise ValueError(f"Unsupported pricing strategy: {pricing_strategy}")
                
                
    
    model.price_constraint_AC = pyo.Constraint(model.nodes_AC,rule=node_price_set_AC)
    model.price_constraint_DC = pyo.Constraint(model.nodes_DC,rule=node_price_set_DC)
    
    model.PN_constraint = pyo.Constraint(model.M,rule=P_price_zone)
    # model.PNL_constraint = pyo.Constraint(model.M,rule=P_price_zone_load)
    model.CG_constraint = pyo.Constraint(model.M,rule=PZ_cost_of_generation)
        
    "Price_Zone inequality constraints"
    
    def import_rule(model,price_zone):
        return model.PN[price_zone] >= model.PGL_min[price_zone]
    def export_rule(model,price_zone):
        return model.PN[price_zone] <= model.PGL_max[price_zone]
    
    # model.import_constraint = pyo.Constraint(model.M,rule=import_rule)
    model.export_constraint = pyo.Constraint(model.M,rule=export_rule)    

def price_zone_parameters(model,grid,AC_info,DC_info,gen_info):
    "Price Zone Parameters"
    
    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    if grid.ACmode:
        AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info
        
        lf,qf,fc,np_gen,lista_gen = gen_AC_info
        
        u_min_ac,u_max_ac,V_ini_AC,Theta_ini, P_know,Q_know,price = AC_nodes_info
        
        model.price  = pyo.Param(model.nodes_AC, initialize=price,mutable=True)
        model.lf = pyo.Param (model.gen_AC, initialize=lf, mutable=True)
        
    if grid.DCmode:
        DC_Lists,DC_nodes_info,DC_lines_info,DCDC_info = DC_info
        lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC = gen_DC_info
        u_min_dc, u_max_dc ,V_ini_DC,P_known_DC,price_dc  = DC_nodes_info

        model.price_dc  = pyo.Param(model.nodes_DC, initialize=price_dc,mutable=True)
        model.lf_dc = pyo.Param (model.gen_DC, initialize=lf_DC, mutable=True)

def TEP_parameters(model,grid,AC_info,DC_info,Conv_info):
    
    
    
    from .ACDC_Static_TEP import get_TEP_variables

    tep_vars = get_TEP_variables(grid)

    # Extract converter variables
    np_conv = tep_vars['converters']['np_conv']
    
    # Extract DC line variables
    NP_lineDC = tep_vars['dc_lines']['NP_lineDC']
    
    # Extract AC line variables
    NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
    REC_branch = tep_vars['ac_lines']['REC_branch']
    ct_ini = tep_vars['ac_lines']['ct_ini']
    
    # Extract generator variables
    np_gen = tep_vars['generators']['np_gen']
    np_gen_DC = tep_vars['generators']['np_gen_DC']
    # Extract renewable source variables
    np_rsgen = tep_vars['ren_sources']['np_rsgen']
   
    
   
    model.np_rsgen = pyo.Param(model.ren_sources,initialize=np_rsgen,mutable=True)
    if grid.ACmode:
        
        model.np_gen = pyo.Param(model.gen_AC,initialize=np_gen,mutable=True)
        
        if grid.TEP_AC:    
            model.NumLinesACP = pyo.Param(model.lines_AC_exp ,initialize=NP_lineAC,mutable=True)    

        if grid.REC_AC:
            model.rec_branch = pyo.Param(model.lines_AC_rec,initialize=REC_branch,mutable=True)
        
        if grid.CT_AC:
            model.ct_branch = pyo.Param(model.lines_AC_ct,model.ct_set,initialize=ct_ini,mutable=True)
    if grid.DCmode:
        DC_Lists,DC_nodes_info,DC_lines_info,DCDC_info = DC_info
        P_lineDC_limit,NP_lineDC    = DC_lines_info
        lista_DCDC = DCDC_info
        
        model.np_gen_DC = pyo.Param(model.gen_DC,initialize=np_gen_DC,mutable=True)
        model.NumLinesDCP = pyo.Param(model.lines_DC,initialize=NP_lineDC,mutable=True)

    if grid.ACmode and grid.DCmode:
        Conv_Lists, Conv_Volt = Conv_info
        lista_conv,np_conv = Conv_Lists

        model.np_conv = pyo.Param(model.conv,initialize=np_conv,mutable=True)


def TEP_variables(model,grid):

    from .ACDC_Static_TEP import get_TEP_variables

    tep_vars = get_TEP_variables(grid)

    # Extract converter variables
    np_conv = tep_vars['converters']['np_conv']
    np_conv_i = tep_vars['converters']['np_conv_i']
    np_conv_max = tep_vars['converters']['np_conv_max']
    S_limit_conv = tep_vars['converters']['S_limit_conv']
    
    # Extract DC line variables
    P_lineDC_limit = tep_vars['dc_lines']['P_lineDC_limit']
    NP_lineDC = tep_vars['dc_lines']['NP_lineDC']
    NP_lineDC_i = tep_vars['dc_lines']['NP_lineDC_i']
    NP_lineDC_max = tep_vars['dc_lines']['NP_lineDC_max']
    Line_length = tep_vars['dc_lines']['Line_length']
    
    # Extract AC line variables
    NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
    NP_lineAC_i = tep_vars['ac_lines']['NP_lineAC_i']
    NP_lineAC_max = tep_vars['ac_lines']['NP_lineAC_max']
    REC_branch = tep_vars['ac_lines']['REC_branch']
    ct_ini = tep_vars['ac_lines']['ct_ini']
    
    # Extract generator variables
    np_gen = tep_vars['generators']['np_gen']
    np_gen_i = tep_vars['generators']['np_gen_i']
    np_gen_max = tep_vars['generators']['np_gen_max']
    np_gen_DC = tep_vars['generators']['np_gen_DC']
    np_gen_DC_i = tep_vars['generators']['np_gen_DC_i']
    np_gen_max_DC = tep_vars['generators']['np_gen_max_DC']    

    np_rsgen = tep_vars['ren_sources']['np_rsgen']
    np_rsgen_i = tep_vars['ren_sources']['np_rsgen_i']
    np_rsgen_max = tep_vars['ren_sources']['np_rsgen_max']

    "TEP variables"

    if grid.rs_GPR:
        def np_rsgen_bounds(model,rs):
            ren_source = grid.RenSources[rs]
            if getattr(ren_source, 'np_rsgen_mp', False):
                return (0, np_rsgen_max[rs])
            elif ren_source.np_rsgen_opf:
                return (np_rsgen[rs], np_rsgen_max[rs])
            else:
                return (np_rsgen[rs], np_rsgen[rs])
        model.np_rsgen = pyo.Var(model.ren_sources,within=pyo.NonNegativeIntegers,bounds=np_rsgen_bounds,initialize=np_rsgen_i)
        model.np_rsgen_base = pyo.Param(model.ren_sources,initialize=np_rsgen)
    elif hasattr(model,'ren_sources'):
        model.np_rsgen = pyo.Param(model.ren_sources,initialize=np_rsgen)

    if grid.ACmode:
        def np_gen_bounds(model,g):
            gen = grid.Generators[g]
            if getattr(gen, 'np_gen_mp', False):
                return (0, np_gen_max[g])
            elif gen.np_gen_opf:
                return (np_gen[g], np_gen_max[g])
            else:
                return (np_gen[g], np_gen[g])
    
        if grid.GPR:

            def P_gen_lower_bound_rule(model, g):
                gen = grid.Generators[g]
                return (get_gen_p_min_eff(gen, model.np_gen[g], model.P_load_eff[g]) <= model.PGi_gen[g])

            def Q_gen_lower_bound_rule(model, g):
                gen = grid.Generators[g]
                return (gen.Min_pow_genR * model.np_gen[g] <= model.QGi_gen[g])

            def P_gen_upper_bound_rule(model, g):
                gen = grid.Generators[g]
                return (model.PGi_gen[g] <= gen.Max_pow_gen * model.np_gen[g])

            def Q_gen_upper_bound_rule(model, g):
                gen = grid.Generators[g]
                return (model.QGi_gen[g] <= gen.Max_pow_genR * model.np_gen[g])


            model.np_gen = pyo.Var(model.gen_AC,within=pyo.NonNegativeIntegers,bounds=np_gen_bounds,initialize=np_gen_i)
            model.np_gen_base = pyo.Param(model.gen_AC,initialize=np_gen)  

            model.PGi_lower_bound = pyo.Constraint(model.gen_AC,rule=P_gen_lower_bound_rule)
            model.QGi_lower_bound = pyo.Constraint(model.gen_AC,rule=Q_gen_lower_bound_rule)
            model.PGi_upper_bound = pyo.Constraint(model.gen_AC,rule=P_gen_upper_bound_rule)
            model.QGi_upper_bound = pyo.Constraint(model.gen_AC,rule=Q_gen_upper_bound_rule)


        elif hasattr(model,'gen_AC'):
            model.np_gen = pyo.Param(model.gen_AC,initialize=np_gen)
            



        if grid.TEP_AC:
            def NPline_bounds_AC(model, line):
                element=grid.lines_AC_exp[line]
                if not element.np_line_opf:
                    return (NP_lineAC[line], NP_lineAC[line])
                else:
                    return (NP_lineAC[line], NP_lineAC_max[line])
            
            model.NumLinesACP = pyo.Var(model.lines_AC_exp, within=pyo.NonNegativeIntegers,bounds=NPline_bounds_AC,initialize=NP_lineAC_i)
            model.NumLinesACP_base  =pyo.Param(model.lines_AC_exp,initialize=NP_lineAC)

        if grid.REC_AC:
            model.rec_branch = pyo.Var(model.lines_AC_rec,domain=pyo.Binary,initialize=REC_branch)

        if grid.CT_AC:
            model.ct_branch = pyo.Var(model.lines_AC_ct,model.ct_set,domain=pyo.Binary,initialize=ct_ini)
            used_cable_types = set()
            for l in grid.lines_AC_ct:
                if l.active_config >= 0:  # If line has an active configuration
                    used_cable_types.add(l.active_config)
            ct_types_ini = {ct: 1 if ct in used_cable_types else 0 for ct in model.ct_set}
            model.ct_types = pyo.Var(model.ct_set,domain=pyo.Binary,initialize=ct_types_ini)

    if grid.DCmode:
        def np_gen_bounds_DC(model,g):
            gen = grid.Generators_DC[g]
            if gen.np_gen_opf:
                return (np_gen_DC[g],np_gen_max_DC[g])
            else:
                return (np_gen_DC[g],np_gen_DC[g])
        
        if grid.GPR:

            def P_gen_DC_lower_bound_rule(model, g):
                gen = grid.Generators_DC[g]
                return (gen.Min_pow_gen * model.np_gen_DC[g] <= model.PGi_gen_DC[g])
            def P_gen_DC_upper_bound_rule(model, g):
                gen = grid.Generators_DC[g]
                return (model.PGi_gen_DC[g] <= gen.Max_pow_gen * model.np_gen_DC[g])

    

            model.np_gen_DC = pyo.Var(model.gen_DC,within=pyo.NonNegativeIntegers,bounds=np_gen_bounds_DC,initialize=np_gen_DC_i)
            model.np_gen_DC_base = pyo.Param(model.gen_DC,initialize=np_gen_DC)  

            model.PGi_lower_bound = pyo.Constraint(model.gen_DC,rule=P_gen_DC_lower_bound_rule)
            model.PGi_upper_bound = pyo.Constraint(model.gen_DC,rule=P_gen_DC_upper_bound_rule)


        elif hasattr(model,'gen_DC'):
            model.np_gen_DC = pyo.Param(model.gen_DC,initialize=np_gen_DC)
            
        def NPline_bounds(model, line):
            element=grid.lines_DC[line]
            if element.np_line_opf==False:
                return (NP_lineDC[line], NP_lineDC[line])
            else:
                return (NP_lineDC[line], NP_lineDC_max[line])
        
        model.NumLinesDCP = pyo.Var(model.lines_DC, within=pyo.NonNegativeIntegers,bounds=NPline_bounds,initialize=NP_lineDC_i)
        model.NumLinesDCP_base  =pyo.Param(model.lines_DC,initialize=NP_lineDC)
       
    if grid.ACmode and grid.DCmode:
        def NPconv_bounds(model, conv):
            element=grid.Converters_ACDC[conv]
            if element.np_conv_opf==False:
                return (np_conv[conv], np_conv[conv])
            else:
                return (np_conv[conv], np_conv_max[conv])
        
        model.np_conv = pyo.Var(model.conv, within=pyo.NonNegativeIntegers,bounds=NPconv_bounds,initialize=np_conv_i)
        model.np_conv_base  =pyo.Param(model.conv,initialize=np_conv)


def ExportACDC_NLmodel_toPyflowACDC(model,grid,Price_Zones,TEP=False):
    
    
    
    
    grid.OPF_run=True

    #Generation 
    if grid.ACmode:
        PGen_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_gen.items()}
        QGen_values  = {k: np.float64(pyo.value(v)) for k, v in model.QGi_gen.items()}
        if grid.act_gen:
            gen_active_values = {k: np.float64(pyo.value(v)) for k, v in model.gen_active.items()}
        else:
            # Use same keys as PGen_values to ensure consistency
            gen_active_values = {k: 1 for k in PGen_values.keys()}
    if grid.DCmode:
        PGen_DC_values = {k: np.float64(pyo.value(v)) for k, v in model.PGi_gen_DC.items()}
    
    gamma_values = {k: np.float64(pyo.value(v)) for k, v in model.gamma.items()}
    Qren_values  = {k: np.float64(pyo.value(v)) for k, v in model.Q_renSource.items()}
    
    def process_element(element):
        if hasattr(element, 'genNumber'):  # Generator
            element.PGen = PGen_values[element.genNumber]*gen_active_values[element.genNumber]
            element.QGen = QGen_values[element.genNumber]*gen_active_values[element.genNumber]
            element.gen_active = gen_active_values[element.genNumber]
        elif hasattr(element, 'genNumber_DC'):  # Generator
            element.PGen = PGen_DC_values[element.genNumber_DC]
        elif hasattr(element, 'rsNumber'):  # Renewable Source
            element.gamma = gamma_values[element.rsNumber]
            element.QGi_ren  = Qren_values[element.rsNumber]

    # Combine Generators and Renewable Sources into one iterable
    elements = grid.Generators + grid.RenSources + grid.Generators_DC
    
    # Parallelize processing    
    with ThreadPoolExecutor() as executor:
        executor.map(process_element, elements)
        
    if Price_Zones:
        # Parallelize price zone processing
        pz_price = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_price.items()}
        pz_PN    = {k: np.float64(pyo.value(v)*grid.S_base) for k, v in model.PN.items()}


        def process_price_zone(m):
            nM = m.price_zone_num
            m.price = pz_price[nM]
            m.PN    = pz_PN[nM]
        with ThreadPoolExecutor() as executor:
            executor.map(process_price_zone, grid.Price_Zones)


    
    #AC bus
    if grid.ACmode:
            
        grid.V_AC = np.zeros(grid.nn_AC)
        grid.Theta_V_AC = np.zeros(grid.nn_AC)

        V_AC_values     = {k: np.float64(pyo.value(v)) for k, v in model.V_AC.items()}
        theta_AC_values = {k: np.float64(pyo.value(v)) for k, v in model.thetha_AC.items()}
        PGi_opt_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_opt.items()}
        QGi_opt_values  = {k: np.float64(pyo.value(v)) for k, v in model.QGi_opt.items()}
        PGi_ren_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_ren.items()}
        QGi_ren_values  = {k: np.float64(pyo.value(v)) for k, v in model.QGi_ren.items()}
        if  grid.DCmode:
            P_conv_AC_values= {k: np.float64(pyo.value(v)) for k, v in model.P_conv_AC.items()}
            Q_conv_AC_values= {k: np.float64(pyo.value(v)) for k, v in model.Q_conv_AC.items()}

        # Parallelize node processing
        def process_node_AC(node):
            nAC = node.nodeNumber
            node.V = V_AC_values[nAC]
            node.theta = theta_AC_values[nAC]
            
            node.PGi_opt = PGi_opt_values[nAC]
            node.QGi_opt = QGi_opt_values[nAC]
            node.PGi_ren = PGi_ren_values[nAC]
            node.QGi_ren = QGi_ren_values[nAC]
            
            if grid.DCmode:
                node.P_s = P_conv_AC_values[nAC]
                node.Q_s = Q_conv_AC_values[nAC]
            
            grid.V_AC[nAC] = node.V
            grid.Theta_V_AC[nAC] = node.theta
            
            
        with ThreadPoolExecutor() as executor:
            executor.map(process_node_AC, grid.nodes_AC)
        
        if grid.GPR:
            np_gen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_gen.items()}
            for gen in grid.Generators:
                gen.np_gen = np_gen_values[gen.genNumber]

        if grid.rs_GPR:
            np_rsgen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_rsgen.items()}
            for rs in grid.RenSources:
                rs.np_rsgen = np_rsgen_values[rs.rsNumber]
        
        if grid.TEP_AC:
            lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}
            lines_AC_TEP_fromP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_from.items()}
            lines_AC_TEP_toP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_to.items()}
            lines_AC_TEP_fromQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_from.items()}
            lines_AC_TEP_toQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_to.items()}
            lines_AC_TEP_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_line_loss.items()}

            def process_line_AC_TEP(line):
                l = line.lineNumber
                line.np_line = lines_AC_TEP[l]
                line.P_loss = lines_AC_TEP_P_loss[l]*lines_AC_TEP[l]
                line.fromS = (lines_AC_TEP_fromP[l] + 1j*lines_AC_TEP_fromQ[l])*lines_AC_TEP[l]
                line.toS = (lines_AC_TEP_toP[l] + 1j*lines_AC_TEP_toQ[l])*lines_AC_TEP[l]
                line.loss = line.fromS + line.toS

            with ThreadPoolExecutor() as executor:
                executor.map(process_line_AC_TEP, grid.lines_AC_exp)

        if grid.REC_AC:
            lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in model.rec_branch.items()}
            lines_AC_REC_fromP = {k: {state: np.float64(pyo.value(model.rec_PAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toP = {k: {state: np.float64(pyo.value(model.rec_PAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_fromQ = {k: {state: np.float64(pyo.value(model.rec_QAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toQ = {k: {state: np.float64(pyo.value(model.rec_QAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.rec_PAC_line_loss.items()}
            
            
            def process_line_AC_REP(line):
                l = line.lineNumber
                line.rec_branch = True if lines_AC_REP[l] >= 0.99999 else False
                line.P_loss = lines_AC_REC_P_loss[l]
                state = 1 if line.rec_branch else 0
                line.fromS = (lines_AC_REC_fromP[l][state] + 1j*lines_AC_REC_fromQ[l][state])
                line.toS = (lines_AC_REC_toP[l][state] + 1j*lines_AC_REC_toQ[l][state])
                line.loss = line.fromS + line.toS

            with ThreadPoolExecutor() as executor:
                executor.map(process_line_AC_REP, grid.lines_AC_rec)    

        if grid.CT_AC:   
            lines_AC_CT = {k: {ct: np.float64(pyo.value(model.ct_branch[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
            lines_AC_CT_fromP = {k: {ct: np.float64(pyo.value(model.ct_PAC_from[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
            lines_AC_CT_toP = {k: {ct: np.float64(pyo.value(model.ct_PAC_to[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
            lines_AC_CT_fromQ = {k: {ct: np.float64(pyo.value(model.ct_QAC_from[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
            lines_AC_CT_toQ = {k: {ct: np.float64(pyo.value(model.ct_QAC_to[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
            lines_AC_CT_loss = {k: np.float64(pyo.value(v)) for k, v in model.ct_PAC_line_loss.items()}
            
            def process_line_AC_CT(line):
                l = line.lineNumber
                ct_selected = [lines_AC_CT[l][ct] >= 0.90  for ct in model.ct_set]
                if any(ct_selected):
                    line.active_config = np.where(ct_selected)[0][0]
                    ct = list(model.ct_set)[line.active_config]
                    Pfrom = lines_AC_CT_fromP[l][ct]
                    Pto   = lines_AC_CT_toP[l][ct]
                    Qfrom = lines_AC_CT_fromQ[l][ct]
                    Qto   = lines_AC_CT_toQ[l][ct]
                else:
                    line.active_config = -1
                    Pfrom = 0
                    Pto   = 0
                    Qfrom = 0
                    Qto   = 0
                
                
                
                line.fromS = (Pfrom + 1j*Qfrom)
                line.toS = (Pto + 1j*Qto)
                line.loss = line.fromS + line.toS
                line.P_loss = lines_AC_CT_loss[l]

            with ThreadPoolExecutor() as executor:
                executor.map(process_line_AC_CT, grid.lines_AC_ct)

        

        if grid.TAP_tf:
            tf_PAC_to_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_PAC_to.items()}
            tf_PAC_from_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_PAC_from.items()}
            tf_QAC_to_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_QAC_to.items()}
            tf_QAC_from_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_QAC_from.items()}
            tf_m_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_m.items()}
            tf_loss_values = {k: np.float64(pyo.value(v)) for k, v in model.tf_PAC_line_loss.items()}
            
            def process_line_AC_tf(tf):
                tfN = tf.trafNumber
                tf.P_loss = tf_loss_values[tfN]
                tf.fromS = tf_PAC_from_values[tfN] + 1j*tf_QAC_from_values[tfN]
                tf.toS = tf_PAC_to_values[tfN] + 1j*tf_QAC_to_values[tfN]
                tf.m = tf_m_values[tfN]
                tf.loss = tf.fromS + tf.toS

            with ThreadPoolExecutor() as executor:
                executor.map(process_line_AC_tf, grid.lines_AC_tf)
        
        grid.create_Ybus_AC()
    
        Pf = np.zeros((grid.nn_AC, 1))
        Qf = np.zeros((grid.nn_AC, 1))
        

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
                    
        grid.Line_AC_calc() 
        
    if grid.DCmode:
        
        # DC nodes
        grid.V_DC = np.zeros(grid.nn_DC)  
        V_DC_values       = {k: np.float64(pyo.value(v)) for k, v in model.V_DC.items()}
        if grid.ACmode:
            P_conv_DC_values  = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_DC.items()}
        if grid.CDC:
            P_DCDC_values  = {k: np.float64(pyo.value(v)) for k, v in model.P_DCDC.items()}
        # Parallelize DC node processing
        def process_node_DC(node):
            nDC = node.nodeNumber
            node.V        = V_DC_values[nDC]
            
            
            grid.V_DC[nDC]= node.V

            if grid.ACmode:
                node.Pconv    = P_conv_DC_values[nDC]
            if grid.CDC:
                node.PconvDC  = P_DCDC_values[nDC]

            node.P_INJ    = node.PGi - node.PLi + node.Pconv + node.PconvDC
        with ThreadPoolExecutor() as executor:
            executor.map(process_node_DC, grid.nodes_DC)

        if TEP:
            lines_DC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesDCP.items()}

            def process_line_DC_TEP(line):
                l = line.lineNumber
                line.np_line = lines_DC_TEP[l]

            with ThreadPoolExecutor() as executor:
                executor.map(process_line_DC_TEP, grid.lines_DC)

        
        if grid.CDC:
            P_DCDC_to_values = {k: np.float64(pyo.value(v)) for k, v in model.cn_DCDC_to.items()}
            P_DCDC_from_values = {k: np.float64(pyo.value(v)) for k, v in model.cn_DCDC_from.items()}
            P_DCDC_loss_values = {k: np.float64(pyo.value(v)) for k, v in model.CDC_loss.items()}

            def process_conv_DCDC(conv):
                conv.Powerto = P_DCDC_to_values[conv.ConvNumber]
                conv.Powerfrom = P_DCDC_from_values[conv.ConvNumber]
                conv.loss = P_DCDC_loss_values[conv.ConvNumber]
            with ThreadPoolExecutor() as executor:
                executor.map(process_conv_DCDC, grid.Converters_DCDC)

        grid.Line_DC_calc()

    if grid.ACmode and grid.DCmode:
        # converters
        P_conv_DC_conv_values= {k: np.float64(pyo.value(v)) for k, v in model.P_conv_DC.items()}
        P_conv_s_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_s_AC.items()}
        Q_conv_s_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.Q_conv_s_AC.items()}
        P_conv_c_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_c_AC.items()}
        Q_conv_c_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.Q_conv_c_AC.items()}
        P_conv_loss_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_loss.items()}
        Uc_values            = {k: np.float64(pyo.value(v)) for k, v in model.Uc.items()}
        Uf_values            = {k: np.float64(pyo.value(v)) for k, v in model.Uf.items()}
        nconv_TEP            = {k: np.float64(pyo.value(v)) for k, v in model.np_conv.items()}

        # Parallelize converter processing
        def process_converter(conv):
            nconv = conv.ConvNumber
            if TEP:
                conv.np_conv = nconv_TEP[nconv]
            conv.P_AC      = P_conv_s_AC_values[nconv] * conv.np_conv
            conv.Q_AC      = Q_conv_s_AC_values[nconv] * conv.np_conv
            conv.Pc        = P_conv_c_AC_values[nconv] * conv.np_conv
            conv.Qc        = Q_conv_c_AC_values[nconv] * conv.np_conv
            conv.P_loss    = P_conv_loss_values[nconv] * conv.np_conv
            conv.P_DC      = -(conv.Pc + conv.P_loss)
            conv.P_loss_tf = abs(conv.P_AC - conv.Pc)
            conv.U_c       = Uc_values[nconv]
            conv.U_f       = Uf_values[nconv]
            conv.U_s       = V_AC_values[conv.Node_AC.nodeNumber]
            conv.th_c      = Uc_values[nconv]
            conv.th_f      = Uf_values[nconv]
            conv.th_s      = theta_AC_values[conv.Node_AC.nodeNumber]
            

        with ThreadPoolExecutor() as executor:
            executor.map(process_converter, grid.Converters_ACDC)
            
    
        

    