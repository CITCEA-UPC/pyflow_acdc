# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:25:02 2024

@author: BernardoCastro
Gurobi version of AC OPF Linear Model
"""

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import time
from .Graph_and_plot import save_network_svg
from .constants import HOURS_PER_YEAR, DEFAULT_DISCOUNT_RATE, DEFAULT_TIME_LIMIT, present_value_factor

__all__ = ['Optimal_L_CSS_gurobi']

from .ACDC_OPF import  obj_w_rule, calculate_objective
from .grid_analysis import analyse_grid

def print_gurobi_model(model, gen_vars=None, ac_vars=None, detailed=True):
    """
    Print Gurobi model information similar to Pyomo's pprint()
    
    Args:
        model: Gurobi model object
        gen_vars: Generation variables dictionary (optional)
        ac_vars: AC variables dictionary (optional)
        detailed: If True, print detailed variable and constraint information
    """
    print("=" * 80)
    print("GUROBI MODEL SUMMARY")
    print("=" * 80)
    
    # Basic model info
    print(f"Model Name: {model.ModelName}")
    print(f"Number of Variables: {model.NumVars}")
    print(f"Number of Constraints: {model.NumConstrs}")
    print(f"Number of Binary Variables: {model.NumBinVars}")
    print(f"Number of Integer Variables: {model.NumIntVars}")
    print(f"Model Status: {model.status}")
    
    if model.status == GRB.OPTIMAL:
        print(f"Objective Value: {model.objVal:.6f}")
    
    print("\n" + "=" * 80)
    print("VARIABLES SUMMARY")
    print("=" * 80)
    
    # Print variable information
    if gen_vars and ac_vars:
        print("\nGeneration Variables:")
        for var_type, var_dict in gen_vars.items():
            print(f"  {var_type}: {len(var_dict)} variables")
            if detailed and var_dict:
                for key, var in var_dict.items():  # Show ALL variables
                    print(f"    {var.VarName}: [{var.LB:.2f}, {var.UB:.2f}]")
        
        print("\nAC Variables:")
        for var_type, var_dict in ac_vars.items():
            print(f"  {var_type}: {len(var_dict)} variables")
            if detailed and var_dict:
                for key, var in var_dict.items():  # Show ALL variables
                    print(f"    {var.VarName}: [{var.LB:.2f}, {var.UB:.2f}]")
    
    print("\n" + "=" * 80)
    print("CONSTRAINTS SUMMARY")
    print("=" * 80)
    
    # Print constraint information
    if detailed:
        print("\nALL CONSTRAINTS:")
        for i, constr in enumerate(model.getConstrs()):
            # Get the constraint expression
            row = model.getRow(constr)
            expr_str = ""
            for j in range(row.size()):
                var = row.getVar(j)
                coeff = row.getCoeff(j)
                if coeff != 0:
                    if coeff > 0 and expr_str:
                        expr_str += " + "
                    elif coeff < 0:
                        expr_str += " - " if expr_str else "-"
                    expr_str += f"{abs(coeff)}*{var.VarName}"
            
            # Add RHS to the expression
            if constr.RHS != 0:
                if constr.RHS > 0:
                    expr_str += f" + {constr.RHS}"
                else:
                    expr_str += f" - {abs(constr.RHS)}"
            
            print(f"  {i+1}: {constr.ConstrName}: {expr_str} {constr.Sense} 0")
    else:
        print(f"Total Constraints: {model.NumConstrs}")
    
    print("\n" + "=" * 80)
    print("SOLVER STATISTICS")
    print("=" * 80)
    
    # Print solver statistics
    if hasattr(model, 'Runtime'):
        print(f"Solve Time: {model.Runtime:.4f} seconds")
    if hasattr(model, 'BarrierIterCount'):
        print(f"Barrier Iterations: {model.BarrierIterCount}")
    if hasattr(model, 'NodeCount'):
        print(f"Nodes Explored: {model.NodeCount}")
    if hasattr(model, 'IterCount'):
        print(f"Simplex Iterations: {model.IterCount}")
    
    print("=" * 80)


def add_pprint_to_model(model, gen_vars=None, ac_vars=None):
    """
    Add a pprint method to the Gurobi model object for easy access
    """
    def pprint(detailed=True):
        print_gurobi_model(model, gen_vars, ac_vars, detailed)
    
    # Store the pprint function in the model's _pprint attribute
    # We'll use a try-except to handle the case where we can't add attributes
    try:
        model._pprint = pprint
    except AttributeError:
        # If we can't add attributes, we'll just return the function
        pass
    return model


def debug_infeasibility(model, gen_vars=None, ac_vars=None):
    """
    Debug infeasibility by computing IIS and showing problematic constraints
    """
    print("=" * 80)
    print("INFEASIBILITY DEBUGGING")
    print("=" * 80)
    
    if model.status == GRB.INFEASIBLE:
        print("Model is infeasible. Computing IIS (Irreducible Infeasible Subsystem)...")
        
        # Compute IIS
        model.computeIIS()
        
        # Get IIS constraints
        iis_constrs = [c for c in model.getConstrs() if c.IISConstr]
        iis_vars = [v for v in model.getVars() if v.IISLB or v.IISUB]
        
        print(f"\nFound {len(iis_constrs)} constraints in IIS:")
        for constr in iis_constrs:
            print(f"  - {constr.ConstrName}: {constr.Sense} {constr.RHS}")
        
        print(f"\nFound {len(iis_vars)} variables with bounds in IIS:")
        for var in iis_vars:
            if var.IISLB:
                print(f"  - {var.VarName}: LB = {var.LB}")
            if var.IISUB:
                print(f"  - {var.VarName}: UB = {var.UB}")
        
        # Show some variable bounds that might be problematic
        if gen_vars and ac_vars:
            print("\nChecking variable bounds:")
            
            print("\nGeneration Variables:")
            for var_type, var_dict in gen_vars.items():
                for key, var in var_dict.items():
                    if var.LB == var.UB and var.LB != 0:
                        print(f"  {var.VarName}: Fixed at {var.LB}")
                    elif var.LB > var.UB:
                        print(f"  {var.VarName}: LB ({var.LB}) > UB ({var.UB}) - INVALID!")
            
            print("\nAC Variables:")
            for var_type, var_dict in ac_vars.items():
                for key, var in var_dict.items():
                    if var.LB == var.UB and var.LB != 0:
                        print(f"  {var.VarName}: Fixed at {var.LB}")
                    elif var.LB > var.UB:
                        print(f"  {var.VarName}: LB ({var.LB}) > UB ({var.UB}) - INVALID!")
    
    elif model.status == GRB.UNBOUNDED:
        print("Model is unbounded. Check for missing constraints or incorrect bounds.")
    
    else:
        print(f"Model status: {model.status}")
    
    print("=" * 80)


def Optimal_L_CSS_gurobi(grid, OPEX=True, NPV=True, n_years=25, Hy=HOURS_PER_YEAR, discount_rate=DEFAULT_DISCOUNT_RATE,tee=False,time_limit=DEFAULT_TIME_LIMIT):
    """Main function to create and solve Gurobi model"""
    
    analyse_grid(grid)
    if not grid.CT_AC:
        raise ValueError("No conductor size selection connections found in the grid")
    
    # Create model
    model = gp.Model("ACDC_OPF")
    
          
    t1 = time.perf_counter()
    model, gen_vars, ac_vars = OPF_create_LModel_AC_gurobi(model,grid)
    t2 = time.perf_counter()  
    t_modelcreate = t2 - t1
    
    # Add pprint method to model for easy inspection
    add_pprint_to_model(model, gen_vars, ac_vars)
    
    # Set objective function for Gurobi model
    set_objective(model, grid,gen_vars,ac_vars,OPEX,NPV, n_years, Hy, discount_rate)
    
    model.setParam('OutputFlag', 1 if tee else 0)  
     # Use more primal heuristics
    model.setParam("TimeLimit", time_limit)        # Cap at 10 mins
    #model.setParam("MIPGap", 0.01)          # Stop if within 1% of best
    #model.setParam("MIPFocus", 1)           # Bias toward feasibility
   # model.setParam("Heuristics", 0.9)       # Find feasible layouts fast
 
    #model.setParam("DisplayInterval", 5)    # Optional: watch progress closely
    t3 = time.perf_counter()
    model_res, solver_stats = solve_gurobi_model(model, grid)
    t4 = time.perf_counter()
    
    # Export results
    ExportACDC_Lmodel_toPyflowACDC_gurobi(model, grid,gen_vars,ac_vars, tee=tee)
    
    if OPEX:
        obj = {'Energy_cost': 1}
    else:
        obj = None

    weights_def, _ = obj_w_rule(grid, obj, True)
    # Calculate objective values
    present_value = present_value_factor(Hy, discount_rate, n_years)
    for obj in weights_def:
        weights_def[obj]['v']=calculate_objective(grid,obj,True)
        weights_def[obj]['NPV']=weights_def[obj]['v']*present_value
    t5 = time.perf_counter()  
    t_modelexport = t5 - t4
    
    grid.OPF_run = True 
    grid.OPF_obj = weights_def
    grid.TEP_run = True
    timing_info = {
        "create": t_modelcreate,
        "solve": solver_stats['time'] if solver_stats['time'] is not None else t4 - t3,
        "export": t_modelexport,
    }
    
    return model, model_res, timing_info, solver_stats


def solve_gurobi_model(model, grid):
    """Solve Gurobi model and return results"""
    
    try:
      
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            model_res = {
                'status': 'optimal',
                'objective_value': model.objVal,
                'solver_time': model.Runtime,
                'iterations': getattr(model, 'BarrierIterCount', None),
                'nodes': getattr(model, 'NodeCount', None)
            }
        elif model.status == GRB.INFEASIBLE:
            model_res = {
                'status': 'infeasible',
                'objective_value': None,
                'solver_time': model.Runtime
            }
        elif model.status == GRB.UNBOUNDED:
            model_res = {
                'status': 'unbounded',
                'objective_value': None,
                'solver_time': model.Runtime
            }
        else:
            model_res = {
                'status': f'other_{model.status}',
                'objective_value': None,
                'solver_time': model.Runtime
            }
        
        solver_stats = {
            'time': model.Runtime,
            'status': model.status,
            'iterations': getattr(model, 'BarrierIterCount', None),
            'nodes': getattr(model, 'NodeCount', None)
        }
        
    except Exception as e:
        model_res = {
            'status': 'error',
            'error_message': str(e),
            'objective_value': None,
            'solver_time': None
        }
        solver_stats = {
            'time': None,
            'status': 'error',
            'error_message': str(e)
        }
    
    return model_res, solver_stats


def OPF_create_LModel_AC_gurobi(model,grid):
    """Create Gurobi model for AC DC OPF"""
    from .ACDC_OPF import Translate_pyf_OPF 
   
    
    # Get problem data
    opf_data = Translate_pyf_OPF(grid,False)
    AC_info = opf_data['AC_info']
    gen_info = opf_data['gen_info']
    
    
    # Create variables
    gen_vars = Generation_variables_gurobi(model, grid, gen_info)
    ac_vars = AC_variables_gurobi(model, grid, AC_info)
     # Suppress output during constraint building
    AC_constraints_gurobi(model, grid, AC_info, gen_info, gen_vars, ac_vars)
  
    return model, gen_vars, ac_vars


def Generation_variables_gurobi(model, grid, gen_info):
    """Convert generation variables to Gurobi"""
    gen_AC_info, _, gen_rs_info = gen_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info
    lf, qf, fc, np_gen, lista_gen = gen_AC_info
    
    # Create a dictionary to store variables
    variables = {}
    
    # Renewable sources
    variables['gamma'] = {}
    
    for rs in lista_rs:
        ren_source = grid.RenSources[rs]
        
        # Curtailment factor
        if ren_source.curtailable:
            lb, ub = ren_source.min_gamma, 1.0
        else:
            lb, ub = 1.0, 1.0
        variables['gamma'][rs] = model.addVar(lb=lb, ub=ub, name=f"gamma_{rs}")
        # Set initial value to 1 to match Pyomo
        variables['gamma'][rs].start = 1
    

    # AC Generators
    variables['PGi_gen'] = {}
    variables['lf'] = {}
    for g in lista_gen:
        gen = grid.Generators[g]

        # Power bounds
        p_lb = gen.Min_pow_gen * gen.np_gen
        p_ub = gen.Max_pow_gen * gen.np_gen
        
        variables['PGi_gen'][g] = model.addVar(lb=p_lb, ub=p_ub, name=f"PGi_gen_{g}")
      
    return variables


def AC_variables_gurobi(model, grid, AC_info):
    """Convert AC variables to Gurobi"""
    AC_Lists, AC_nodes_info, AC_lines_info, EXP_info, REC_info, CT_info = AC_info
    
    lista_nodos_AC, lista_lineas_AC, lista_lineas_AC_tf, AC_slack, AC_PV = AC_Lists
    u_min_ac, u_max_ac, V_ini_AC, Theta_ini, P_know, Q_know, price = AC_nodes_info
    S_lineAC_limit, S_lineACtf_limit, m_tf_og = AC_lines_info

    lista_lineas_AC_exp, S_lineACexp_limit, NP_lineAC = EXP_info
    lista_lineas_AC_rec, S_lineACrec_lim, S_lineACrec_lim_new, grid.REC_AC_act = REC_info
    lista_lineas_AC_ct, S_lineACct_lim, cab_types_set, allowed_types = CT_info
    ct_ini = {}
    for l in grid.lines_AC_ct:
        for ct in range(len(l._cable_types)):
            ct_ini[l.lineNumber, ct] = 1 if ct == l.active_config else 0  
    ac_vars = {}
    
    ac_vars['ct_types'] = {}
    # Find which cable types are used in the initial guess
    used_cable_types = set()
    for l in grid.lines_AC_ct:
        if l.active_config >= 0:  # If line has an active configuration
            used_cable_types.add(l.active_config)
    
    for ct in cab_types_set:
        ac_vars['ct_types'][ct] = model.addVar(
            vtype=GRB.BINARY,
            name=f"ct_types_{ct}"
        )
        # Set start value to 1 if this cable type is used in the initial guess
        #ac_vars['ct_types'][ct].start = 1 if ct in used_cable_types else 0
    
    ac_vars['ct_branch'] = {}
    for line in lista_lineas_AC_ct:
        for ct in cab_types_set:
            ac_vars['ct_branch'][line, ct] = model.addVar(
                vtype=GRB.BINARY,
                name=f"ct_branch_{line}_{ct}",
            )
            # Don't set start values - let Gurobi find its own feasible starting point
            #ac_vars['ct_branch'][line, ct].start = ct_ini[line, ct]
    
    # Voltage angles with tighter bounds
    ac_vars['theta_AC'] = {}
    for node in lista_nodos_AC:
        ac_vars['theta_AC'][node] = model.addVar(
            lb=-np.pi/2, ub=np.pi/2,  
            name=f"theta_AC_{node}",
        )
        # Don't set start values for voltage angles - let Gurobi find its own feasible starting point
        # ac_vars['theta_AC'][node].start = Theta_ini[node] if Theta_ini[node] is not None else 0.0

    
    # Power generation variables with better bounds
    ac_vars['PGi_opt'] = {}
    for node in lista_nodos_AC:
        min_gen = sum(gen.Min_pow_gen for gen in grid.nodes_AC[node].connected_gen if gen.Min_pow_gen < 0)
        max_gen = sum(gen.Max_pow_gen for gen in grid.nodes_AC[node].connected_gen)
        ac_vars['PGi_opt'][node] = model.addVar(
            lb=min_gen, ub=max_gen,
            name=f"PGi_opt_{node}"
        )

    
    # Renewable power variables
    ac_vars['PGi_ren'] = {}
    for node in lista_nodos_AC:
        max_ren = sum(rs.PGi_ren for rs in grid.nodes_AC[node].connected_RenSource)
        ac_vars['PGi_ren'][node] = model.addVar(
            lb=0, ub=max_ren,
            name=f"PGi_ren_{node}"
        )
    
    # Power injection variables
    ac_vars['Pto_CT'] = {}
    ac_vars['Pfrom_CT'] = {}
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        max_ct_power = sum(max(S_lineACct_lim[line.lineNumber, ct] for ct in cab_types_set) 
                          for line in nAC.connected_toCTLine + nAC.connected_fromCTLine)
        
        ac_vars['Pto_CT'][node] = model.addVar(
            lb=-max_ct_power, ub=max_ct_power,
            name=f"Pto_CT_{node}"
        )
        
        ac_vars['Pfrom_CT'][node] = model.addVar(
            lb=-max_ct_power, ub=max_ct_power,
            name=f"Pfrom_CT_{node}"
        )
    
    # Standard AC line power flows
    ac_vars['PAC_to'] = {}
    ac_vars['PAC_from'] = {}
    for line in lista_lineas_AC:
       
        ac_vars['PAC_to'][line] = model.addVar(
            lb=-S_lineAC_limit[line], ub=S_lineAC_limit[line],
            name=f"PAC_to_{line}"
        )
        
        ac_vars['PAC_from'][line] = model.addVar(
            lb=-S_lineAC_limit[line], ub=S_lineAC_limit[line],
            name=f"PAC_from_{line}"
        )
    
    # Network flow variables for MIP integration
    ac_vars['network_flow'] = {}
    ac_vars['node_net_flow'] = {}
    
    # Calculate max flow for bounds
    max_flow = grid.max_turbines_per_string
    for line in lista_lineas_AC_ct:
        ac_vars['network_flow'][line] = model.addVar(
            lb=-max_flow, ub=max_flow,
            name=f"network_flow_{line}"
        )
    
    for node in lista_nodos_AC:
        ac_vars['node_net_flow'][node] = model.addVar(
            lb=-len(lista_nodos_AC), ub=1,  # Allow negative values for sink nodes
            name=f"node_net_flow_{node}"
        )
    
    # Cable type variables
    
    ac_vars['ct_PAC_to'] = {}
    ac_vars['ct_PAC_from'] = {}
    ac_vars['z_to'] = {}
    ac_vars['z_from'] = {}
    
    for line in lista_lineas_AC_ct:
        max_min = max(S_lineACct_lim[line,ct] for ct in cab_types_set)
        for ct in cab_types_set:
            
            
            ac_vars['ct_PAC_to'][line, ct] = model.addVar(
                lb=-max_min, ub=max_min,
                name=f"ct_PAC_to_{line}_{ct}"
            )
            
            ac_vars['ct_PAC_from'][line, ct] = model.addVar(
                lb=-max_min, ub=max_min,
                name=f"ct_PAC_from_{line}_{ct}"
            )
            
            ac_vars['z_to'][line, ct] = model.addVar(
                lb=-max_min, ub=max_min,
                name=f"z_to_{line}_{ct}"
            )
            
            ac_vars['z_from'][line, ct] = model.addVar(
                lb=-max_min, ub=max_min,
                name=f"z_from_{line}_{ct}"
            )
    
    return ac_vars


def AC_constraints_gurobi(model, grid, AC_info, gen_info, gen_vars, ac_vars):
    """Convert AC constraints to Gurobi"""
    AC_Lists, AC_nodes_info, AC_lines_info, EXP_info, REC_info, CT_info = AC_info
    lista_nodos_AC, lista_lineas_AC, lista_lineas_AC_tf, AC_slack, AC_PV = AC_Lists
    
    lista_lineas_AC_ct, S_lineACct_lim, cab_types_set, allowed_types = CT_info

    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info

    
    max_cable_limits = {line: max(S_lineACct_lim[line, ct] for ct in cab_types_set) 
                       for line in lista_lineas_AC_ct}

    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        
        # Add investment-related power flows
        power_sum = ac_vars['Pto_CT'][node] + ac_vars['Pfrom_CT'][node]
        
        # Power balance constraint
        model.addConstr(
            power_sum == ac_vars['PGi_ren'][node] + ac_vars['PGi_opt'][node],
            name=f"power_balance_{node}"
        )
    
        gen_power = sum(gen_vars['PGi_gen'][gen.genNumber] for gen in nAC.connected_gen)
        model.addConstr(
            ac_vars['PGi_opt'][node] == gen_power,
            name=f"gen_power_{node}"
        )
        

        ren_power = sum(P_renSource[rs.rsNumber] * gen_vars['gamma'][rs.rsNumber] * np_rsgen[rs.rsNumber]
                       for rs in nAC.connected_RenSource)
        model.addConstr(
            ac_vars['PGi_ren'][node] == ren_power,
            name=f"ren_power_{node}"
        )
    
        to_ct_sum = sum(ac_vars['z_to'][line.lineNumber, ct] 
                       for line in nAC.connected_toCTLine for ct in cab_types_set)
        model.addConstr(
            ac_vars['Pto_CT'][node] == to_ct_sum,
            name=f"to_ct_{node}"
        )
        
        from_ct_sum = sum(ac_vars['z_from'][line.lineNumber, ct] 
                         for line in nAC.connected_fromCTLine for ct in cab_types_set)
        model.addConstr(
            ac_vars['Pfrom_CT'][node] == from_ct_sum,
            name=f"from_ct_{node}"
        )

    
    # Line flow constraints
    for line in lista_lineas_AC:
        l = grid.lines_AC[line]
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        
        # Power flow equations (DC approximation)
        B = np.imag(l.Ybus_branch[0, 1])
        
        model.addConstr(
            ac_vars['PAC_to'][line] == -B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]),
            name=f"power_flow_to_{line}"
        )
        
        model.addConstr(
            ac_vars['PAC_from'][line] == -B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]),
            name=f"power_flow_from_{line}"
        )
    
    # Slack node angle constraint - fix slack node angle to 0
    #for slack_node in AC_slack:
    #    model.addConstr(
    #        ac_vars['theta_AC'][slack_node] == 0,
    #        name=f"slack_angle_{slack_node}"
    #    )
    
    # Cable type constraints
    model.addConstr(
        sum(ac_vars['ct_types'][ct] for ct in cab_types_set) <= grid.cab_types_allowed,
        name="CT_limit_rule"
    )
    
    # Cable types upper bound - if cable type is selected, it must be used
    for ct in cab_types_set:
        model.addConstr(
            sum(ac_vars['ct_branch'][line, ct] for line in lista_lineas_AC_ct) <= len(lista_lineas_AC_ct) * ac_vars['ct_types'][ct],
            name=f"ct_types_upper_bound_{ct}"
        )
    
    # Cable types lower bound - if cable type is used, it must be selected
    for ct in cab_types_set:
        model.addConstr(
            ac_vars['ct_types'][ct] <= sum(ac_vars['ct_branch'][line, ct] for line in lista_lineas_AC_ct),
            name=f"ct_types_lower_bound_{ct}"
        )
    
    # Array cable type rule - at most one cable type per line (for array mode)
    for line in lista_lineas_AC_ct:
        model.addConstr(
            sum(ac_vars['ct_branch'][line, ct] for ct in cab_types_set) <= 1,
            name=f"ct_Array_cable_type_rule_{line}"
        )
   
    # Node limit rule - limit cable types per node
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if hasattr(nAC, 'ct_limit'):
            connections = sum(ac_vars['ct_branch'][line.lineNumber, ct] 
                            for line in nAC.connected_toCTLine + nAC.connected_fromCTLine 
                            for ct in cab_types_set)
            model.addConstr(
                connections >= 1,
                name=f"ct_node_min_rule_{node}"
            )
            
            model.addConstr(
                connections <= nAC.ct_limit,
                name=f"ct_node_limit_rule_{node}"
            )
   
    # Crossings rule - limit cable types in crossing groups   
    for ct_crossing in grid.crossing_groups:
        model.addConstr(
            sum(ac_vars['ct_branch'][line, ct] for line in grid.crossing_groups[ct_crossing] for ct in cab_types_set) <= 1,
            name=f"ct_crossings_rule_{ct_crossing}"
        )

    # McCormick envelope constraints for z variables
    for line in lista_lineas_AC_ct:
        l = grid.lines_AC_ct[line]
        M = max_cable_limits[line] * 1.1  # Pre-calculated
        
        for ct in cab_types_set:
            f = l.fromNode.nodeNumber
            t = l.toNode.nodeNumber
            B = np.imag(l.Ybus_list[ct][0, 1])
            M_angle= B*3.1416
            # Power flow constraints
            model.addConstr(
                ac_vars['ct_PAC_to'][line, ct] + B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]) <= M_angle*(1-ac_vars['ct_branch'][line, ct]),
                name=f"ct_power_flow_to_lower_{line}_{ct}"
            )

            model.addConstr(
                ac_vars['ct_PAC_to'][line, ct] + B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]) >= -M_angle*(1-ac_vars['ct_branch'][line, ct]),
                name=f"ct_power_flow_to_upper_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['ct_PAC_from'][line, ct] + B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]) <= M_angle*(1-ac_vars['ct_branch'][line, ct]),
                name=f"ct_power_flow_from_lower_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['ct_PAC_from'][line, ct] + B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]) >= -M_angle*(1-ac_vars['ct_branch'][line, ct]),
                name=f"ct_power_flow_from_upper_{line}_{ct}"
            )
            # McCormick envelopes for z_to
            model.addConstr(
                ac_vars['z_to'][line, ct] <= ac_vars['ct_PAC_to'][line, ct] + (1 - ac_vars['ct_branch'][line, ct]) * (2*M),
                name=f"z_to_ub_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_to'][line, ct] >= ac_vars['ct_PAC_to'][line, ct] - (1 - ac_vars['ct_branch'][line, ct]) * (2*M),
                name=f"z_to_lb_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_to'][line, ct] <= S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                name=f"z_to_branch_ub_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_to'][line, ct] >= -S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                name=f"z_to_branch_lb_{line}_{ct}"
            )
            
            # McCormick envelopes for z_from
            model.addConstr(
                ac_vars['z_from'][line, ct] <= ac_vars['ct_PAC_from'][line, ct] + (1 - ac_vars['ct_branch'][line, ct]) * (2*M),
                name=f"z_from_ub_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_from'][line, ct] >= ac_vars['ct_PAC_from'][line, ct] - (1 - ac_vars['ct_branch'][line, ct]) * (2*M),
                name=f"z_from_lb_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_from'][line, ct] <= S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                name=f"z_from_branch_ub_{line}_{ct}"
            )
            
            model.addConstr(
                ac_vars['z_from'][line, ct] >= -S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                name=f"z_from_branch_lb_{line}_{ct}"
            )
         
    # Network flow constraints for MIP integration
    add_network_flow_constraints(model, grid, ac_vars, lista_nodos_AC, lista_lineas_AC_ct, cab_types_set            )


def add_network_flow_constraints(model, grid, ac_vars, lista_nodos_AC, lista_lineas_AC_ct, cab_types_set):
    """Add network flow constraints from MIP problem to ensure flow feasibility"""
    max_flow = grid.max_turbines_per_string
    # Find source and sink nodes
    source_nodes = []
    sink_nodes = []
    
    
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if nAC.connected_RenSource:  # Node has renewable resources (source)
            source_nodes.append(node)
        if nAC.connected_gen:  # Node has generator (sink)
            sink_nodes.append(node)
            
    total_connections = sum(ac_vars['ct_branch'][line, ct] for line in lista_lineas_AC_ct for ct in cab_types_set)
    

    model.addConstr(
        total_connections == len(lista_nodos_AC) - len(sink_nodes),
        name="spanning_tree_connections")
    if not source_nodes:
        raise ValueError("No renewable source nodes found!")
    if not sink_nodes:
        raise ValueError("No generator nodes found!")
    
    # Flow conservation for all nodes
    for node in lista_nodos_AC:
        # Calculate net flow out of this node
        net_flow = 0
        
        for line in lista_lineas_AC_ct:
            line_obj = grid.lines_AC_ct[line]
            from_node = line_obj.fromNode.nodeNumber
            to_node = line_obj.toNode.nodeNumber
            
            if from_node == node:
                # Flow leaving this node (positive)
                net_flow += ac_vars['network_flow'][line]
            elif to_node == node:
                # Flow entering this node (negative, so we add it to net_flow)
                net_flow -= ac_vars['network_flow'][line]
        
        # Set the net flow out of this node
        model.addConstr(
            ac_vars['node_net_flow'][node] == net_flow,
            name=f"flow_conservation_{node}"
        )
    
    # Source nodes: net flow out = 1 (supply)
    for node in source_nodes:
        model.addConstr(
            ac_vars['node_net_flow'][node] == 1,
            name=f"source_node_{node}"
        )
    
    # Sink nodes: total net flow out = -num_sources (demand)
    model.addConstr(
        sum(ac_vars['node_net_flow'][node] for node in sink_nodes) == -len(source_nodes),
        name="total_sink_absorption"
    )
    
    # Intermediate nodes: net flow = 0 (conservation)
    for node in lista_nodos_AC:
        if node not in source_nodes and node not in sink_nodes:
            model.addConstr(
                ac_vars['node_net_flow'][node] == 0,
                name=f"intermediate_node_{node}"
            )
    
    # Link flow to investment: can only use lines we invest in
    
    for line in lista_lineas_AC_ct:
        # Flow must be zero if line not invested
        model.addConstr(
            ac_vars['network_flow'][line] <= max_flow * sum(ac_vars['ct_branch'][line, ct] for ct in cab_types_set),
            name=f"flow_investment_link_upper_{line}"
        )
        model.addConstr(
            ac_vars['network_flow'][line] >= -max_flow * sum(ac_vars['ct_branch'][line, ct] for ct in cab_types_set),
            name=f"flow_investment_link_lower_{line}"
        )


def set_objective(model, grid, gen_vars, ac_vars, OPEX=True, NPV=True, n_years=25, Hy=HOURS_PER_YEAR, discount_rate=DEFAULT_DISCOUNT_RATE):
    """Set objective function for Gurobi model"""
    cab_types_set = list(range(0,len(grid.Cable_options[0]._cable_types)))
    # Investment costs
    investment_cost = 0
    
    for line in grid.lines_AC_ct:
        l = line.lineNumber
        if line.array_opf:
            if NPV:
                for ct in cab_types_set:
                    investment_cost += ac_vars['ct_branch'][l, ct] * line.base_cost[ct]
            else:
                for ct in cab_types_set:
                    investment_cost += ac_vars['ct_branch'][l, ct] * line.base_cost[ct] / line.life_time_hours
    
    # Operational costs
    operational_cost = 0
    if OPEX:
        lista_gen = list(range(0, grid.n_gen))
        for g in lista_gen:
            gen = grid.Generators[g]
            operational_cost += gen.lf * gen_vars['PGi_gen'][g]
    
    if NPV:
        present_value = present_value_factor(Hy, discount_rate, n_years)
        operational_cost *= present_value
    
    # Total objective
    total_cost = investment_cost + operational_cost
    model.setObjective(total_cost, GRB.MINIMIZE)


def ExportACDC_Lmodel_toPyflowACDC_gurobi(model, grid,gen_vars,ac_vars, tee=True):
    """Export Gurobi results back to grid object"""
    
    if model.status not in [GRB.OPTIMAL, GRB.SUBOPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        # Print model information to help debug infeasibility
        #print_gurobi_model(model, gen_vars, ac_vars, detailed=True)
        debug_infeasibility(model, gen_vars, ac_vars)
        raise RuntimeError(f"Cannot export results: status {model.status}, solutions: {model.SolCount}")
    
    if model.status == GRB.TIME_LIMIT:
        if tee:
            print("Time limit reached. Exporting results anyway. Cleaning intermidate results")
    
    cab_types_set = list(range(0,len(grid.Cable_options[0]._cable_types)))
    grid.OPF_run = True

    # Generation 
    for g in grid.Generators:
        g.PGen = gen_vars['PGi_gen'][g.genNumber].X
        g.QGen = 0.0 
    
    # Renewable sources
    for rs in grid.RenSources:
        rs.gamma = gen_vars['gamma'][rs.rsNumber].X
        rs.QGi_ren = 0.0 

    # AC bus
    grid.V_AC = np.ones(grid.nn_AC)
    grid.Theta_V_AC = np.zeros(grid.nn_AC)

    for node in grid.nodes_AC:
        nAC = node.nodeNumber
        node.V = 1.0  
        node.theta = ac_vars['theta_AC'][nAC].X
        
        node.PGi_opt = ac_vars['PGi_opt'][nAC].X
        node.QGi_opt = 0.0 
        node.PGi_ren = ac_vars['PGi_ren'][nAC].X
        node.QGi_ren = 0.0  
        
        grid.Theta_V_AC[nAC] = node.theta

    # Power injections
    B = np.imag(grid.Ybus_AC)
    Theta = grid.Theta_V_AC
    Theta_diff = Theta[:, None] - Theta
    Pf_DC = (-B * Theta_diff).sum(axis=1)
    
    for node in grid.nodes_AC:
        i = node.nodeNumber
        node.P_INJ = Pf_DC[i]
        node.Q_INJ = 0.0
    
    for line in grid.lines_AC_ct:
        ct_selected = [ac_vars['ct_branch'][line.lineNumber, ct].X >= 0.9 for ct in cab_types_set]
        if any(ct_selected):
            line.active_config = np.where(ct_selected)[0][0]
            ct = list(cab_types_set)[line.active_config]
            line.fromS = ac_vars['ct_PAC_from'][line.lineNumber, ct].X + 1j*0
            line.toS = ac_vars['ct_PAC_to'][line.lineNumber, ct].X + 1j*0
        else:
            line.active_config = -1
            line.fromS = 0 + 1j*0
            line.toS = 0 + 1j*0
        line.loss = 0
        line.P_loss = 0
        
        # Export network flow value to grid
        line.network_flow = abs(ac_vars['network_flow'][line.lineNumber].X)

    # Standard AC lines
    Theta = grid.Theta_V_AC
    for line in grid.lines_AC:
        i = line.fromNode.nodeNumber
        j = line.toNode.nodeNumber
        
        B = -np.imag(line.Ybus_branch[0, 1])
        P_ij = B * (Theta[i] - Theta[j])
        P_ji = B * (Theta[j] - Theta[i])

        line.fromP = P_ij
        line.toP = P_ji
        line.toS = P_ji + 1j*0
        line.fromS = P_ij + 1j*0
        line.P_loss = 0
        line.loss = 0
        line.i_from = abs(P_ij)
        line.i_to = abs(P_ji)
    
    # After export is complete, analyze and fix oversizing issues if time limit was reached
    if model.status == GRB.TIME_LIMIT:  # or check for time limit in Pyomo
        from .AC_OPF_L_model import analyze_oversizing_issues_grid, apply_oversizing_fixes_grid
        oversizing_type1, oversizing_type2 = analyze_oversizing_issues_grid(grid, tee=tee)
        apply_oversizing_fixes_grid(grid, oversizing_type1, oversizing_type2, tee=tee)



def create_master_problem_gurobi(grid, crossings=False, max_flow=None):
    master = gp.Model("Master")
    if max_flow is None:
        max_flow = len(grid.nodes_AC) - 1
    lista_lineas_AC_ct = list(range(0, len(grid.lines_AC_ct)))
    lista_nodos_AC = list(range(0, len(grid.nodes_AC)))
    
    # Binary variables: one per line (used or not)
    line_vars = {}
    
    for line in lista_lineas_AC_ct:
        line_vars[line] = master.addVar(
            vtype=GRB.BINARY,
            name=f"line_used_{line}"
        )

    
    # Objective: minimize total cable length
    investment_cost = 0
    for line in grid.lines_AC_ct:
        l = line.lineNumber
        line_cost = line.Length_km
        investment_cost += line_vars[l] * line_cost
          
    
    # Spanning tree constraint: exactly numNodes-numSinkNodes connections (multiple trees for multiple substations)
    total_connections = sum(line_vars[line] for line in lista_lineas_AC_ct)
    master.addConstr(
        total_connections == len(lista_nodos_AC) - len(sink_nodes),
        name="spanning_tree_connections"
    )
    
  
    # Find sink nodes (nodes with generators) and source nodes (nodes with renewable resources)
    sink_nodes = []
    source_nodes = []
    
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if nAC.connected_gen:  # Node has generator (sink)
            sink_nodes.append(node)
        if nAC.connected_RenSource:  # Node has renewable resources (source)
            source_nodes.append(node)
    
    if not sink_nodes:
        raise ValueError("No generator nodes found!")
      # Constrain connections for source nodes (renewable nodes)
    for node in source_nodes:
        # Count how many lines are connected to this source node
        node_connections = sum(line_vars[line] 
                              for line in lista_lineas_AC_ct
                              if (grid.lines_AC_ct[line].fromNode.nodeNumber == node or 
                                  grid.lines_AC_ct[line].toNode.nodeNumber == node))
        
        # Limit to node.ct_limit
        nAC = grid.nodes_AC[node]
        master.addConstr(
            node_connections <= nAC.ct_limit,
            name=f"source_connections_limit_{node}"
        )
 
    # Flow variables (integer - can carry flow in either direction)
    flow_vars = {}
    node_flow_vars = {}
    
    for line in lista_lineas_AC_ct:
        # Signed flow variable: positive = flow from fromNode to toNode, negative = reverse
        flow_vars[line] = master.addVar(
            vtype=GRB.INTEGER,
            lb=-max_flow,
            ub=max_flow,
            name=f"flow_{line}"
        )
    
    for node in lista_nodos_AC:
        # Net flow out of each node
        node_flow_vars[node] = master.addVar(
            vtype=GRB.INTEGER,
            name=f"node_flow_{node}"
        )
        
        # Calculate net flow out of this node
        net_flow = 0
        
        for line in lista_lineas_AC_ct:
            line_obj = grid.lines_AC_ct[line]
            from_node = line_obj.fromNode.nodeNumber
            to_node = line_obj.toNode.nodeNumber
            
            if from_node == node:
                # Flow leaving this node (positive)
                net_flow += flow_vars[line]
            elif to_node == node:
                # Flow entering this node (negative, so we add it to flow_out)
                net_flow -= flow_vars[line]
        
        # Set the net flow out of this node
        master.addConstr(
            node_flow_vars[node] == net_flow,
            name=f"flow_conservation_{node}"
        )
    
    # Source nodes: net flow out = 1 (supply)
    for node in source_nodes:
        master.addConstr(
            node_flow_vars[node] == 1,
            name=f"source_node_{node}"
        )
    
    # Sink nodes: total net flow out = -num_sources (demand)
    master.addConstr(
        sum(node_flow_vars[node] for node in sink_nodes) == -len(source_nodes),
        name="total_sink_absorption"
    )
    
    # Intermediate nodes: net flow = 0 (conservation)
    for node in lista_nodos_AC:
        if node not in source_nodes and node not in sink_nodes:
            master.addConstr(
                node_flow_vars[node] == 0,
                name=f"intermediate_node_{node}"
            )
    
    # Link flow to investment: can only use lines we invest in
    for line in lista_lineas_AC_ct:
        # Flow must be zero if line not invested
        master.addConstr(
            flow_vars[line] <= max_flow * line_vars[line],
            name=f"flow_investment_link_upper_{line}"
        )
        master.addConstr(
            flow_vars[line] >= -max_flow * line_vars[line],
            name=f"flow_investment_link_lower_{line}"
        )
    
    # Add crossing constraints if grid has crossing groups
    if hasattr(grid, 'crossing_groups') and grid.crossing_groups:
        for group_idx, group in enumerate(grid.crossing_groups):
            # Constraint: for each crossing group, only one line can be active
            # Sum of all line_vars in this crossing group must be <= 1
            crossing_sum = sum(line_vars[line] for line in lista_lineas_AC_ct 
                              if grid.lines_AC_ct[line].lineNumber in group)
            master.addConstr(
                crossing_sum <= 1,
                name=f"crossing_constraint_{group_idx}"
            )

    master.setObjective(investment_cost, GRB.MINIMIZE)
    master.update()
    return master, line_vars, flow_vars, node_flow_vars


def test_master_problem_gurobi(grid, crossings=False, max_flow=None):
    """Simple test for master problem"""
    print("Testing Master Problem...")
    
    # Create and solve master problem
    master, line_vars, flow_vars,node_flow_vars = create_master_problem_gurobi(grid, crossings, max_flow)
    
    # Try to solve (should be feasible)
    master.setParam('OutputFlag', 1)  # Show output for debugging
    master.optimize()
    
    if master.status == GRB.OPTIMAL:
        print(f"✓ Master problem is feasible!")
        print(f"  Objective: {master.objVal:.2f}")
        print(f"  Variables: {master.NumVars}")
        print(f"  Constraints: {master.NumConstrs}")
        
        # Count and display investments
        investments = 0
        print("\n=== NETWORK FLOW ANALYSIS ===")
        print("Invested lines and their flows:")
        for line in range(len(grid.lines_AC_ct)):
            if line_vars[line].X > 0.8:
                investments += 1
                line_obj = grid.lines_AC_ct[line]
                flow_value = flow_vars[line].X
                print(f"  Line {line}: {line_obj.fromNode.nodeNumber} -> {line_obj.toNode.nodeNumber}, Flow: {flow_value}")
        
        print("\nNode flows:")
        for node in range(len(grid.nodes_AC)):
            node_flow = node_flow_vars[node].X
            node_type = ""
            if node in [n for n in range(len(grid.nodes_AC)) if grid.nodes_AC[n].connected_RenSource]:
                node_type = " (SOURCE)"
            elif node in [n for n in range(len(grid.nodes_AC)) if grid.nodes_AC[n].connected_gen]:
                node_type = " (SINK)"
            else:
                node_type = " (INTERMEDIATE)"
            print(f"  Node {node}: Net flow = {node_flow}{node_type}")
        
        # Set active configurations
        # Get the last available cable type index
        last_cable_type_index = len(grid.Cable_options[0]._cable_types) - 1
        for line in range(len(grid.lines_AC_ct)):
            ct_line = grid.lines_AC_ct[line]
            if line_vars[line].X > 0.5:
                ct_line.active_config = last_cable_type_index
            else:
                ct_line.active_config = -1
        
        print(f"\n=== SUMMARY ===")
        print(f"  Total investments: {investments}")
        print(f"  Expected (numNodes-1): {len(grid.nodes_AC) - 1}")
        
        # Verify flow conservation
        source_nodes = [n for n in range(len(grid.nodes_AC)) if grid.nodes_AC[n].connected_RenSource]
        sink_nodes = [n for n in range(len(grid.nodes_AC)) if grid.nodes_AC[n].connected_gen]
        total_source_flow = sum(node_flow_vars[node].X for node in source_nodes)
        total_sink_flow = sum(node_flow_vars[node].X for node in sink_nodes)
        print(f"  Total source flow: {total_source_flow}")
        print(f"  Total sink flow: {total_sink_flow}")
        print(f"  Flow conservation check: {total_source_flow + total_sink_flow == 0}")
        
        save_network_svg(grid, name='grid_network_investments')
        return True
    
        
    else:
        print(f"✗ Master problem failed: status {master.status}")
        return False
