"""
Created on Thu Feb 15 13:24:05 2024

@author: BernardoCastro
"""
import numpy as np
import pandas as pd
import pyomo.environ as pyo
from pyomo.util.infeasible import log_infeasible_constraints
from pyomo.opt import SolverStatus

import os
import sys
from contextlib import redirect_stdout

import time
import math
from concurrent.futures import ThreadPoolExecutor
import re

from  .ACDC_OPF_NL_model import *
from  .AC_OPF_L_model import *
from .grid_analysis import analyse_grid
import cProfile
import pstats
from io import StringIO

try:
    import gurobipy
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False


import logging
from pyomo.util.infeasible import log_infeasible_constraints

__all__ = [
    'Translate_pyf_OPF',
    'Optimal_L_PF',
    'Optimal_PF',
    'TS_parallel_OPF',
    'pyomo_model_solve',
    'OPF_updateParam',
    'OPF_obj',
    'OPF_line_res',
    'OPF_price_priceZone',
    'OPF_step_results',
    'fx_conv',
    'export_solver_progress_to_excel',
    'reset_to_initialize'
]

def pack_variables(*args):
    return args
           
            

def obj_w_rule(grid,ObjRule,OnlyGen):
    weights_def = {
       'Ext_Gen': {'w': 0},
       'Energy_cost': {'w': 0},
       'Curtailment_Red': {'w': 0},
       'AC_losses': {'w': 0},
       'DC_losses': {'w': 0},
       'Converter_Losses': {'w': 0},
       'General_Losses': {'w': 0},
       'PZ_cost_of_generation': {'w': 0},
       'Renewable_profit': {'w': 0},
       'Gen_set_dev': {'w': 0}
    }

    # If user provides specific weights, merge them with the default
    if ObjRule is not None:
       for key in ObjRule:
           if key in weights_def:
               weights_def[key]['w'] = ObjRule[key]

    if OnlyGen == False:
        grid.OnlyGen=False
    Price_Zones = False
    if  weights_def['PZ_cost_of_generation']['w']!=0 :
        Price_Zones=True
    if  weights_def['Curtailment_Red']['w']!=0 :
        grid.CurtCost=True

    return weights_def, Price_Zones



def Optimal_L_PF(grid,ObjRule=None,OnlyGen=True,Price_Zones=False,solver='glpk',tee=False,callback=False,obj_scaling=1.0):
    grid.reset_run_flags()
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule,OnlyGen)
    
    # Check if any other weight is non-zero while Energy_cost is zero
    if weights_def['Energy_cost']['w'] == 0:
        other_weights_nonzero = [key for key, value in weights_def.items() 
                               if key != 'Energy_cost' and value['w'] != 0]
        if other_weights_nonzero:
            print("Linear OPF can only consider energy cost by AC Generator power")
        
    model = pyo.ConcreteModel()
    model.name="""AC 'DC linear' OPF"""
    
    
    t1 = time.perf_counter()
    
    # pr = cProfile.Profile()
    # pr.enable()
    # Call your function here
    OPF_create_LModel_AC(model,grid)
    # pr.disable()
    
    # s = StringIO()
    # ps = pstats.Stats(pr, stream=s)
    # ps.sort_stats('cumulative')  # Can also try 'time'
    # ps.print_stats()
    # print(s.getvalue())
    
    t2 = time.perf_counter()  
    t_modelcreate = t2-t1
    
    """
    """
    
    
  
    obj_rule= OPF_obj_L(model,grid,weights_def)

    if obj_scaling != 1.0:
        obj_rule = obj_rule / obj_scaling
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    
                
    """
    """
    t3 = time.perf_counter()
    model_res,solver_stats = pyomo_model_solve(model,grid,solver,tee,callback=callback)
    
    t1 = time.perf_counter()
    # pr = cProfile.Profile()
    # pr.enable()
    # Call your function here
    ExportACDC_Lmodel_toPyflowACDC(model, grid)
    # pr.disable()

    for obj in weights_def:
        weights_def[obj]['v']=calculate_objective(grid,obj,OnlyGen)
    
    # s = StringIO()
    # ps = pstats.Stats(pr, stream=s)
    # ps.sort_stats('cumulative')  # Can also try 'time'
    # ps.print_stats()
    # print(s.getvalue())
    t2 = time.perf_counter()  
    t_modelexport = t2-t1
   
       
    grid.OPF_run=True 
    grid.OPF_obj=weights_def
    timing_info = {
    "create": t_modelcreate,
    "solve": solver_stats['time'] if solver_stats['time'] is not None else t1-t3,
    "export": t_modelexport,
    }
    return model, model_res , timing_info, solver_stats

def Optimal_PF(grid,ObjRule=None,PV_set=False,OnlyGen=True,Price_Zones=False,limit_flow_rate=True,solver='ipopt',tee=False,callback=False,obj_scaling=1.0):
    grid.reset_run_flags()
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule,OnlyGen)
        
    model = pyo.ConcreteModel()
    model.name="AC/DC hybrid OPF"
    
    
    t1 = time.perf_counter()
    
    # pr = cProfile.Profile()
    # pr.enable()
    # Call your function here
    OPF_create_NLModel_ACDC(model,grid,PV_set,Price_Zones,limit_flow_rate=limit_flow_rate)
    # pr.disable()
    
    # s = StringIO()
    # ps = pstats.Stats(pr, stream=s)
    # ps.sort_stats('cumulative')  # Can also try 'time'
    # ps.print_stats()
    # print(s.getvalue())
    
    t2 = time.perf_counter()  
    t_modelcreate = t2-t1
    
    """
    """
    
    
    
    obj_rule= OPF_obj(model,grid,weights_def,OnlyGen)

    if obj_scaling != 1.0:
        obj_rule = obj_rule / obj_scaling
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    """
    """
    
    if grid.nn_DC!=0:

        if any(conv.OPF_fx for conv in grid.Converters_ACDC):
                    fx_conv(model, grid)
                
                
    """
    """
    model_res,solver_stats = pyomo_model_solve(model,grid,solver,tee,callback=callback)
    
    t1 = time.perf_counter()
    # pr = cProfile.Profile()
    # pr.enable()
    # Call your function here
    ExportACDC_NLmodel_toPyflowACDC(model, grid, Price_Zones)
    # pr.disable()

    for obj in weights_def:
        weights_def[obj]['v']=calculate_objective(grid,obj,OnlyGen)
    
    # s = StringIO()
    # ps = pstats.Stats(pr, stream=s)
    # ps.sort_stats('cumulative')  # Can also try 'time'
    # ps.print_stats()
    # print(s.getvalue())
    t2 = time.perf_counter()  
    t_modelexport = t2-t1
   
       
    grid.OPF_run=True 
    grid.OPF_obj=weights_def
    timing_info = {
    "create": t_modelcreate,
    "solve": solver_stats['time'],
    "export": t_modelexport,
    }
    return model, model_res , timing_info, solver_stats


def TS_parallel_OPF(grid,idx,current_range,ObjRule=None,PV_set=False,OnlyGen=True,Price_Zones=False,print_step=False):
    grid.reset_run_flags()
    from .Time_series import update_grid_data,_modify_parameters
    
    weights_def, Price_Zones = obj_w_rule(grid,ObjRule,OnlyGen)
        
        
    model = pyo.ConcreteModel()
    model.name="TS MTDC AC/DC hybrid OPF"
    
    
    model.Time_frames = pyo.Set(initialize=range(idx, idx + current_range))
    model.submodel = pyo.Block(model.Time_frames)
    # Run parallel iterations
    base_model = pyo.ConcreteModel()
    base_model = OPF_create_NLModel_ACDC(base_model,grid,PV_set=False,Price_Zones=True,TEP=True)

    for i in range(current_range):
        t = idx + i
        if print_step:
            print(t)
        base_model_copy = base_model.clone()
        model.submodel[t].transfer_attributes_from(base_model_copy)

        for ts in grid.Time_series:
            update_grid_data(grid, ts, t)
                    
        _modify_parameters(grid,model.submodel[t],Price_Zones) 
        subobj = OPF_obj(model.submodel[t],grid,weights_def,OnlyGen)
        model.submodel[t].obj = pyo.Objective(rule=subobj, sense=pyo.minimize)

    obj_rule= TS_parallel_obj(model)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model_results,elapsed_time= pyomo_model_solve(model,grid)
    
    Current_range_res = obtain_results_TSOPF(model,grid,current_range,idx,Price_Zones)
      
    return model, Current_range_res,t,elapsed_time


def obtain_results_TSOPF(model,grid,current_range,idx,Price_Zones) :
    opt_res_P_conv_DC_list = []
    opt_res_P_conv_AC_list =[]
    opt_res_Q_conv_AC_list =[]
    opt_res_P_Load_list =[]
    opt_res_P_extGrid_list = []
    opt_res_curtailment_list = []
    opt_res_Q_extGrid_list = []
    opt_res_Loading_conv_list =[]
    opt_res_Loading_lines_list =[]
    opt_res_price_list =[]
    opt_res_Loading_grid_list=[]
    for i in range(current_range):
        
        t = idx + i
        # print(t+1)
        
        (opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,
         opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,opt_res_Loading_conv) = OPF_step_results(model.submodel[t], grid)
        
        opt_res_Loading_lines,opt_res_Loading_grid=OPF_line_res (model.submodel[t],grid)
        
        if Price_Zones:
           opt_res_price=OPF_price_priceZone (model.submodel[t],grid)
        else:
            opt_res_price={}
            for ts in grid.Time_series:
                if ts.type == 'price':
                    opt_res_price[ts.name]=ts.data[t]
                        
        # Add the time index to the dictionaries
        opt_res_curtailment['time'] = t + 1
        opt_res_P_conv_DC['time'] = t + 1
        opt_res_P_conv_AC['time'] = t + 1
        opt_res_Q_conv_AC['time'] = t + 1
        opt_res_P_extGrid['time'] = t + 1
        opt_res_Q_extGrid['time']=t+1
        opt_P_load['time']        = t+1
        opt_res_Loading_conv['time'] = t + 1
        opt_res_Loading_lines['time'] = t + 1
        opt_res_Loading_grid['time'] =t+1
        opt_res_price['time']=t+1
        
        # Append the dictionaries to the respective lists
        opt_res_P_conv_DC_list.append(opt_res_P_conv_DC)
        opt_res_P_conv_AC_list.append(opt_res_P_conv_AC)
        opt_res_Q_conv_AC_list.append(opt_res_Q_conv_AC)
        
        opt_res_P_extGrid_list.append(opt_res_P_extGrid)
        opt_res_P_Load_list.append(opt_P_load)
        opt_res_curtailment_list.append(opt_res_curtailment)
        opt_res_Q_extGrid_list.append(opt_res_Q_extGrid)
        opt_res_Loading_conv_list.append(opt_res_Loading_conv)
        opt_res_Loading_lines_list.append(opt_res_Loading_lines)
        opt_res_price_list.append(opt_res_price)
        opt_res_Loading_grid_list.append(opt_res_Loading_grid)

    # After processing all time steps, pack the results into tuples
    touple = (opt_res_Loading_conv_list,opt_res_Loading_lines_list,opt_res_Loading_grid_list,
             opt_res_P_conv_AC_list,opt_res_Q_conv_AC_list,opt_res_P_conv_DC_list,
             opt_res_P_extGrid_list,opt_res_P_Load_list,opt_res_Q_extGrid_list,
             opt_res_curtailment_list,opt_res_price_list)
    
    
    return touple

def TS_parallel_obj(model):
   
    # Calculate the weighted social cost for each submodel (subblock)
    total_obj = 0
    for t in model.Time_frames:
        submodel_obj = model.submodel[t].obj
        model.submodel[t].obj.deactivate()
        total_obj+=submodel_obj
      
        
    return total_obj 


def fx_conv(model,grid):
    def fx_PDC(model,conv):
        if grid.Converters_ACDC[conv].OPF_fx==True and grid.Converters_ACDC[conv].OPF_fx_type=='PDC':
            return model.P_conv_DC[conv.Node_DC.nodeNumber]==grid.Converters_ACDC[conv].P_DC
        else:
            return pyo.Constraint.Skip
    def fx_PAC(model,conv):   
        if grid.Converters_ACDC[conv].OPF_fx==True and (grid.Converters_ACDC[conv].OPF_fx_type=='PQ' or grid.Converters_ACDC[conv].OPF_fx_type=='PV'):
            return model.P_conv_s_AC[conv]==grid.Converters_ACDC[conv].P_AC
        else:
            return pyo.Constraint.Skip
    def fx_QAC(model,conv):    
        if grid.Converters_ACDC[conv].OPF_fx==True and grid.Converters_ACDC[conv].OPF_fx_type=='PQ':
            return model.Q_conv_s_AC[conv]==grid.Converters_ACDC[conv].Q_AC
        else:
            return pyo.Constraint.Skip
        
    model.Conv_fx_pdc=pyo.Constraint(model.conv,rule=fx_PDC)
    model.Conv_fx_pac=pyo.Constraint(model.conv,rule=fx_PAC)
    model.Conv_fx_qac =pyo.Constraint(model.conv,rule=fx_QAC)


def log_infeasible_constraints_limited(model, max_per_type=5):
    """
    Custom function to check and display infeasible constraints with limited output.
    """
    import logging
    from pyomo.core import Constraint
    from collections import defaultdict
    import numpy as np
    
    print("=" * 80)
    print("INFEASIBLE CONSTRAINTS SUMMARY")
    print("=" * 80)
    
    # Group constraints by their type/name pattern
    constraint_groups = defaultdict(list)
    
    # Check all constraints in the model
    for constraint in model.component_objects(Constraint, active=True):
        constraint_name = constraint.name
        
        # Check if constraint is violated
        for index in constraint:
            try:
                # Get the constraint expression
                expr = constraint[index]
                
                # Evaluate the constraint
                if hasattr(expr, 'expr'):
                    # For inequality constraints
                    if hasattr(expr, 'lower') and expr.lower is not None:
                        lower_val = expr.lower
                        upper_val = expr.upper if hasattr(expr, 'upper') and expr.upper is not None else None
                        
                        # Evaluate the expression
                        try:
                            expr_val = pyo.value(expr.expr)
                            
                            # Check for violations
                            if lower_val is not None and expr_val < lower_val - 1e-6:
                                constraint_groups[constraint_name].append(
                                    f"{constraint_name}[{index}]: {expr_val:.6f} < {lower_val:.6f} (lower bound violation)"
                                )
                            elif upper_val is not None and expr_val > upper_val + 1e-6:
                                constraint_groups[constraint_name].append(
                                    f"{constraint_name}[{index}]: {expr_val:.6f} > {upper_val:.6f} (upper bound violation)"
                                )
                        except:
                            # If we can't evaluate, just note the constraint
                            constraint_groups[constraint_name].append(
                                f"{constraint_name}[{index}]: Unable to evaluate"
                            )
                else:
                    # For equality constraints
                    try:
                        expr_val = pyo.value(expr)
                        if abs(expr_val) > 1e-6:
                            constraint_groups[constraint_name].append(
                                f"{constraint_name}[{index}]: {expr_val:.6f} != 0 (equality violation)"
                            )
                    except:
                        constraint_groups[constraint_name].append(
                            f"{constraint_name}[{index}]: Unable to evaluate"
                        )
                        
            except Exception as e:
                constraint_groups[constraint_name].append(
                    f"{constraint_name}[{index}]: Error evaluating - {str(e)}"
                )
    
    # Display results with limits
    total_violations = 0
    for group_name, violations in constraint_groups.items():
        if violations:  # Only show groups with violations
            print(f"\n{group_name}")
            print("-" * len(group_name))
            
            # Show first max_per_type violations
            for i, violation in enumerate(violations[:max_per_type]):
                print(f"  {violation}")
            
            # Show summary if there are more
            if len(violations) > max_per_type:
                remaining = len(violations) - max_per_type
                print(f"  ... and {remaining} other violations")
            
            print(f"  Total: {len(violations)} violations")
            total_violations += len(violations)
    
    if total_violations == 0:
        print("\nNo constraint violations detected.")
    else:
        print(f"\nTotal violations across all constraint types: {total_violations}")
    
    print("=" * 80)

def _gurobi_callback(model, feasible_solutions, bound_solutions, time_limit=None, solver_options=None, tee=False):
    """
    Gurobi callback function with support for custom solver options.
    
    Parameters:
    -----------
    model : Pyomo model
        The model to solve
    feasible_solutions : list
        List to append (time, objective, gap) tuples
    bound_solutions : list
        List to append (time, best_bound, node_count) tuples
    time_limit : float, optional
        Time limit in seconds
    solver_options : dict, optional
        Dictionary of Gurobi parameter names to values (e.g., {'MIPFocus': 2, 'Cuts': 2})
    tee : bool, default=False
        Print solver output to console
    """
    from gurobipy import GRB
    opt = pyo.SolverFactory('gurobi_persistent')
    opt.set_instance(model)
    grb_model = opt._solver_model

    if not tee:
        grb_model.setParam('OutputFlag', 0)

    def my_callback(model, where):
        if where == GRB.Callback.MIPSOL:
            # New feasible solution found
            time_found = model.cbGet(GRB.Callback.RUNTIME)
            obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)  # incumbent obj (this solution)
            
            # Global best bound at this moment
            bound = model.cbGet(GRB.Callback.MIPSOL_OBJBND)

            gap = None
            # Check that we actually have a meaningful incumbent and bound
            if obj < GRB.INFINITY and bound > -GRB.INFINITY:
                denom = abs(obj)
                if denom < 1e-10:
                    denom = 1e-10  # avoid division by zero for tiny objectives
                gap = abs(bound - obj) / denom  # same definition Gurobi uses

            # Store: (time, value, gap)
            feasible_solutions.append((time_found, obj, gap))
            node_count = model.cbGet(GRB.Callback.MIPSOL_NODCNT)
            bound_solutions.append((time_found, bound, node_count))

    # Set time limit
    if time_limit is not None:
        grb_model.setParam("TimeLimit", time_limit)
    
    # Apply custom solver options
    if solver_options:
        for param_name, param_value in solver_options.items():
            try:
                grb_model.setParam(param_name, param_value)
            except Exception as e:
                print(f"Warning: Could not set Gurobi parameter {param_name}={param_value}: {e}")

    grb_model.optimize(my_callback)

    from pyomo.opt.results.results_ import SolverResults
    results = SolverResults()
    results.solver.status = pyo.SolverStatus.ok
    results.problem.upper_bound = grb_model.ObjVal if grb_model.SolCount > 0 else None
    results.solver.time = grb_model.Runtime
    
    # Calculate final gap and append final solution
    final_gap = None
    if grb_model.SolCount > 0:
        obj_val = grb_model.ObjVal
        obj_bound = grb_model.ObjBound
        if obj_bound != GRB.INFINITY and obj_bound != -GRB.INFINITY and abs(obj_val) > 1e-10:
            model_sense = grb_model.ModelSense
            if model_sense == GRB.MINIMIZE:
                final_gap = (obj_val - obj_bound) / abs(obj_val)
            else:  # MAXIMIZE
                final_gap = (obj_bound - obj_val) / abs(obj_val)
        feasible_solutions.append((grb_model.Runtime, obj_val, final_gap))
        bound_solutions.append((grb_model.Runtime, obj_bound, grb_model.NodeCount))
    
    if grb_model.Status == GRB.Status.OPTIMAL:
        results.solver.termination_condition = pyo.TerminationCondition.optimal
        opt.load_vars()
    elif grb_model.Status == GRB.Status.SUBOPTIMAL:
        results.solver.termination_condition = pyo.TerminationCondition.feasible
        opt.load_vars()
    elif grb_model.Status == GRB.Status.TIME_LIMIT:
        results.solver.termination_condition = pyo.TerminationCondition.maxTimeLimit
        if grb_model.SolCount > 0:
            opt.load_vars()
    elif grb_model.Status == GRB.Status.INFEASIBLE:
        results.solver.termination_condition = pyo.TerminationCondition.infeasible
    else:
        results.solver.termination_condition = pyo.TerminationCondition.unknown
        if grb_model.SolCount > 0:
            opt.load_vars()
    opt._solver_model.dispose()  # Cleanup
    return results, feasible_solutions, bound_solutions

def _parse_bonmin_log(log_path):
    """Parse Bonmin log file to extract feasible solutions and all solutions.
    Returns tuple of (feasible_solutions, all_solutions, bound_solutions) where each
    stream stores (time, value, iterations_like_counter).
    """
    feasible_solutions = []
    all_solutions = []
    bound_solutions = []
    last_nlp_call = 0
    cumulative_iterations = 0
    cumulative_time = 0
    
    try:
        with open(log_path, 'r') as f:
            pending_header = False
            for line in f:
                # Detect NLP table header; don't infer anything here
                if line.startswith('NLP0012I'):
                    pending_header = True
                    continue
                # Look for integer solution lines like:
                # Cbc0004I Integer solution of 1.5954776e+10 found after 1563 iterations and 63 nodes (5.62 seconds)
                if 'Integer solution of' in line and ('found after' in line or 'found by' in line):
                    # Extract objective value
                    obj_match = re.search(r'Integer solution of ([\d\.eE\+\-]+)', line)
                    # Extract iterations (handles both "found after X iterations" and "found by X after Y iterations")
                    iter_match = re.search(r'(?:found after|after) (\d+) iterations', line)
                    # Extract time
                    time_match = re.search(r'\(([\d\.]+) seconds\)', line)
                    
                    if obj_match and iter_match and time_match:
                        try:
                            objective = float(obj_match.group(1))
                            iterations = int(iter_match.group(1))
                            time_sec = float(time_match.group(1))
                            # Only explicit integer solution lines define feasibility/incumbents.
                            feasible_solutions.append((time_sec, objective, iterations))
                            all_solutions.append([time_sec, objective, iterations, last_nlp_call, True])
                                
                        except (ValueError, TypeError):
                            continue
                
                # Capture best-bound progress from CBC summaries when available.
                elif line.startswith('Cbc0010I') and 'best possible' in line:
                    bound_match = re.search(r'best possible\s+([-\d\.eE\+]+)', line)
                    time_match = re.search(r'\(([\d\.]+)\s+seconds\)', line)
                    iter_match = re.search(r'After\s+(\d+)\s+nodes', line)
                    if bound_match and time_match:
                        try:
                            best_bound = float(bound_match.group(1))
                            time_sec = float(time_match.group(1))
                            iterations = int(iter_match.group(1)) if iter_match else cumulative_iterations
                            bound_solutions.append((time_sec, best_bound, iterations))
                        except (ValueError, TypeError):
                            continue

                # Keep partial search summaries only in all_solutions (not incumbents).
                elif line.startswith('Cbc0005I') and 'best objective' in line:
                    obj_match = re.search(r'best objective\s+([-\d\.eE\+]+)', line)
                    # Optional best bound in parenthesis: best objective X (Y)
                    bound_match = re.search(r'best objective\s+[-\d\.eE\+]+\s+\(([-\d\.eE\+]+)\)', line)
                    time_match = re.search(r'\(([\d\.]+)\s+seconds\)', line)
                    iter_match = re.search(r'took\s+(\d+)\s+iterations', line)
                    if obj_match and time_match:
                        try:
                            objective = float(obj_match.group(1))
                            time_sec = float(time_match.group(1))
                            iterations = int(iter_match.group(1)) if iter_match else cumulative_iterations
                            # Partial-search status line; keep only as progress history.
                            all_solutions.append([time_sec, objective, iterations, last_nlp_call, False])
                            if bound_match:
                                best_bound = float(bound_match.group(1))
                                bound_solutions.append((time_sec, best_bound, iterations))
                        except (ValueError, TypeError):
                            continue
                
                # Also look for NLP iteration lines like:
                # NLP0014I            24         OPT 8.9135036e+09       25 0.341783
                elif 'NLP0014I' in line and 'OPT' in line:
                    # Extract objective value, iteration count (It), and time from NLP lines.
                    # Example: "NLP0014I           120         OPT 1.5954776e+10       25 0.045817"
                    # parts[1]=NLP solver call number, parts[2]=Status, parts[3]=Obj, parts[4]=It, parts[5]=time
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        try:
                            # Handle NLP0014I * 1 OPT format where * is a separate token
                            if parts[1] == '*':
                                # Format: NLP0014I * 1 OPT obj it time
                                nlp_call_num = int(parts[2])
                                objective = float(parts[4])
                                nlp_iterations = int(parts[5])
                                time_sec = float(parts[6])
                            else:
                                # Format: NLP0014I 1 OPT obj it time
                                nlp_call_num = int(parts[1])
                                objective = float(parts[3])
                                nlp_iterations = int(parts[4])
                                time_sec = float(parts[5])
                            
                            # Always record progress; do not infer feasibility from numbering changes
                            cumulative_iterations += nlp_iterations
                            cumulative_time += time_sec
                            solution_data = [cumulative_time, objective, cumulative_iterations, nlp_call_num, False]
                            all_solutions.append(solution_data)
                            last_nlp_call = nlp_call_num
                            pending_header = False
                                
                        except (ValueError, TypeError, IndexError):
                            continue
    except (FileNotFoundError, IOError):
        pass
    return feasible_solutions, all_solutions, bound_solutions

def _parse_highs_log(log_path):
    """Parse HiGHS log file to extract feasible solutions and all solutions.
    
    HiGHS MIP output format:
        Nodes      |    B&B Tree     |            Objective Bounds              |  Dynamic Constraints |       Work
    Src  Proc. InQueue |  Leaves   Expl. | BestBound       BestSol              Gap |   Cuts   InLp Confl. | LpIters     Time
    
    T     165      18        61   5.32%   38.21150457     51.97623619       26.48%     1482     51   8313    115998    23.6s
    
    Column positions (after splitting by whitespace):
    - 0: Src (T, L, or empty/space)
    - 1: Proc
    - 2: InQueue
    - 3: Leaves
    - 4: Expl (percentage)
    - 5: BestBound
    - 6: BestSol
    - 7: Gap (percentage)
    - 8: Cuts
    - 9: InLp
    - 10: Confl
    - 11: LpIters
    - 12: Time (with 's' suffix)
    
    Returns tuple of (feasible_solutions, all_solutions, bound_solutions).
    """
    feasible_solutions = []
    all_solutions = []
    bound_solutions = []
    
    try:
        with open(log_path, 'r') as f:
            header_found = False
            for line in f:
                # Look for the header line to know when data starts
                if 'BestBound' in line and 'BestSol' in line and 'Gap' in line:
                    header_found = True
                    continue
                
                if not header_found:
                    continue
                
                # Skip empty lines and separator lines
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('-'):
                    continue
                
                # Parse data lines - format is space-separated columns
                # Handle case where Src column might be empty (just spaces)
                parts = line_stripped.split()
                
                # Need at least 13 columns (including Src)
                # If first token is not T/L and is numeric, Src is empty
                if len(parts) < 12:
                    continue
                
                try:
                    # Determine if Src column exists (T or L) or is empty
                    src_idx = 0
                    if parts[0] in ['T', 'L']:
                        # Src column present
                        src = parts[0]
                        data_start = 1
                    else:
                        # Src column empty, first column is Proc
                        src = ''
                        data_start = 0
                    
                    # Now extract columns (adjusting for optional Src)
                    # BestSol is at position 6 from start of data (after Src if present)
                    # So: data_start + 5 = BestBound, data_start + 6 = BestSol, data_start + 7 = Gap
                    best_bound_idx = data_start + 4
                    best_sol_idx = data_start + 5
                    gap_idx = data_start + 6
                    time_idx = data_start + 11  # Last column
                    
                    if time_idx >= len(parts):
                        continue
                    
                    best_sol_str = parts[best_sol_idx]
                    if best_sol_str == 'inf':
                        continue  # No feasible solution yet
                    
                    # Extract time (last column, remove 's' suffix)
                    time_str = parts[time_idx].rstrip('s')
                    time_sec = float(time_str)
                    
                    # Extract objective value
                    objective = float(best_sol_str)
                    best_bound = float(parts[best_bound_idx])
                    
                    # Extract gap (remove '%' and convert to decimal)
                    gap_str = parts[gap_idx].rstrip('%')
                    gap = float(gap_str) / 100.0 if gap_str != 'inf' else None
                    
                    # Check if this is a new feasible solution (marked with T or L prefix)
                    is_new_solution = (src in ['T', 'L'])
                    
                    # Store solution
                    solution_data = (time_sec, objective, gap)
                    all_solutions.append([time_sec, objective, gap, time_sec, is_new_solution])
                    bound_solutions.append((time_sec, best_bound, None))
                    
                    # Only add to feasible_solutions if it's a new solution (T or L marker)
                    # or if BestSol changed from previous (improved objective)
                    if is_new_solution:
                        feasible_solutions.append(solution_data)
                    elif feasible_solutions:
                        # Check if objective improved (for minimization, lower is better)
                        last_obj = feasible_solutions[-1][1]
                        if objective < last_obj:  # Better solution found
                            feasible_solutions.append(solution_data)
                    
                except (ValueError, IndexError, TypeError) as e:
                    continue
                    
    except (FileNotFoundError, IOError):
        pass
    
    return feasible_solutions, all_solutions, bound_solutions

def _parse_ipopt_log(log_path):
    """Parse Ipopt log file to extract iteration progress and final solution.
    Returns list of (iteration, objective, is_feasible, inf_pr, inf_du) tuples.
    
    Feasibility is determined by inf_pr (primal infeasibility):
      - During iterations: inf_pr < 1e-4 (relaxed, since IPOPT's acceptable
        tolerance is ~1e-6 and per-iteration inf_pr can oscillate)
      - Final solution: captured from the EXIT line and summary statistics
    """
    progress_events = []
    final_objective = None
    final_iteration = None
    exit_acceptable = False
    exit_optimal = False
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                # Look for Ipopt iteration lines like:
                # iter    objective    inf_pr   inf_du lg(mu)  ||d||  lg(rg) alpha_du alpha_pr  ls
                #   0  1.5929771e+10 1.00e+00 1.00e+00  -1.0 1.00e+00    -  1.00e+00 1.00e+00   0
                if re.match(r'^\s*\d+r?\s+[\d\.eE\+\-]+\s+', line.strip()):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            iter_token = parts[0]
                            in_restoration_phase = iter_token.endswith('r')
                            iteration = int(iter_token.rstrip('r'))
                            objective = float(parts[1])
                            inf_pr = float(parts[2])
                            inf_du = float(parts[3])
                            
                            # For IPOPT, treat an iterate as feasible only when both
                            # primal and dual infeasibilities are small, and ignore
                            # restoration-phase iterates.
                            is_feasible = (
                                (not in_restoration_phase)
                                and inf_pr < 1e-4
                                and inf_du < 1e-4
                            )
                            
                            progress_events.append((iteration, objective, is_feasible, inf_pr, inf_du))
                            final_objective = objective
                            final_iteration = iteration
                        except (ValueError, IndexError):
                            continue
                
                # Capture EXIT status
                if 'EXIT: Optimal Solution Found' in line:
                    exit_optimal = True
                elif 'EXIT: Solved To Acceptable Level' in line:
                    exit_acceptable = True
    except (FileNotFoundError, IOError):
        pass
    
    # If IPOPT declared optimal or acceptable, ensure the final point is marked feasible
    if (exit_optimal or exit_acceptable) and progress_events:
        last_iter, last_obj, _, last_inf_pr, last_inf_du = progress_events[-1]
        progress_events[-1] = (last_iter, last_obj, True, last_inf_pr, last_inf_du)
    
    return progress_events

def _solver_progress(model, feasible_solutions, solver_name, time_limit, log_path, tee_console=True):
    """Unified progress tracking for Ipopt, Bonmin, and HiGHS solvers.
    
    Always writes to log file for parsing. Uses Pyomo's tee parameter to control console output.
    """
    opt = pyo.SolverFactory(solver_name)
    
    # Set time limit based on solver
    if time_limit is not None:
        if solver_name == 'ipopt':
            opt.options['max_cpu_time'] = time_limit
        elif solver_name == 'bonmin':
            opt.options['bonmin.time_limit'] = time_limit
        elif solver_name == 'highs':
            opt.options['time_limit'] = time_limit
    
    # Always configure solver to write to log file (for callback parsing)
    # Then use Pyomo's tee parameter to control console output
    if solver_name == 'highs':
        # HiGHS supports direct log file output
        opt.options['log_file'] = log_path
        # Set log_to_console based on tee_console: when tee=True, allow HiGHS to write to console
        # so Pyomo's tee can capture it properly (fixes Windows output stream issues)
        opt.options['log_to_console'] = tee_console
    elif solver_name == 'ipopt':
        # IPOPT can write to a log file
        opt.options['output_file'] = log_path
        # Keep print_level reasonable for log file, tee controls console
        opt.options['print_level'] = 5
    elif solver_name == 'bonmin':
        # Continue MINLP search if an NLP subproblem fails, so incumbents can still be returned.
        opt.options['bonmin.nlp_failure_behavior'] = 'fathom'
    
    start = time.perf_counter()
    
    # Always write to log file, use Pyomo's tee to control console output.
    # For Bonmin/HiGHS, disable autoload so Pyomo does not raise when no
    # solution is available to load. We then load manually if a solution exists.
    solve_kwargs = {'tee': tee_console}
    if solver_name in ('bonmin', 'highs'):
        solve_kwargs['load_solutions'] = False
    if solver_name == 'bonmin':
        solve_kwargs['logfile'] = log_path
    results = opt.solve(model, **solve_kwargs)

    # Manual incumbent recovery when autoload is disabled.
    if solver_name in ('bonmin', 'highs'):
        try:
            solution_list = getattr(results, 'solution', None)
            if solution_list is not None and len(solution_list) > 0:
                original_status = getattr(results.solver, 'status', None)
                if solver_name == 'bonmin' and original_status == SolverStatus.error:
                    results.solver.status = SolverStatus.warning
                model.solutions.load_from(results)
                if solver_name == 'bonmin' and original_status == SolverStatus.error:
                    results.solver.status = original_status
        except Exception as exc:
            if tee_console:
                print(f"Warning: could not load incumbent solution from solver results: {exc}")
    
    end = time.perf_counter()

    # Parse the log file based on solver type
    all_solutions = []
    bound_solutions = []
    if solver_name == 'ipopt':
        parsed_events = _parse_ipopt_log(log_path)
        # Convert to same format as feasible_solutions for consistency
        for iter_num, obj, is_feasible, inf_pr, inf_du in parsed_events:
            if is_feasible:
                feasible_solutions.append((iter_num, obj, iter_num))
            # all_solutions extended schema (ipopt): [..., is_feasible, inf_pr, inf_du]
            all_solutions.append([iter_num, obj, iter_num, iter_num, is_feasible, inf_pr, inf_du])
    elif solver_name == 'bonmin':
        parsed_feasible, parsed_all, parsed_bounds = _parse_bonmin_log(log_path)
        feasible_solutions.extend(parsed_feasible)
        all_solutions.extend(parsed_all)
        bound_solutions.extend(parsed_bounds)
    elif solver_name == 'highs':
        parsed_feasible, parsed_all, parsed_bounds = _parse_highs_log(log_path)
        feasible_solutions.extend(parsed_feasible)
        all_solutions.extend(parsed_all)
        bound_solutions.extend(parsed_bounds)

    return results, feasible_solutions, all_solutions, bound_solutions

def reset_to_initialize(model, initial_values):
    """
    Resets all variables in the Pyomo model to their original initialize values.
    model: Pyomo ConcreteModel
        The Pyomo model whose variables are to be reset.
    initial_values: dict
        A dictionary containing the original initialize values of variables.
    """
    for var_obj in model.component_objects(pyo.Var, active=True):
        if var_obj.name in initial_values:
            for index in var_obj:
                var_data = var_obj[index]
                value = initial_values[var_obj.name].get(index, 0)

                # Keep reset robust: project tiny numerical drift back inside bounds.
                lb = pyo.value(var_data.lb) if var_data.lb is not None else None
                ub = pyo.value(var_data.ub) if var_data.ub is not None else None

                if value is None:
                    raise ValueError(
                        f"reset_to_initialize got None for {var_obj.name}[{index}] "
                        f"(lb={lb}, ub={ub}). Model variable is not initialized."
                    )

                if lb is not None and value < lb:
                    value = lb
                if ub is not None and value > ub:
                    value = ub

                var_data.set_value(value)

def _store_pyomo_results_on_grid(grid_obj, model_obj, results_obj, solver_stats):
    """Persist latest Pyomo model results table on grid for Results.All()."""
    if grid_obj is None:
        return
    try:
        from .Results_class import Results
        df, _ = Results._build_pyomo_model_results_df(
            model=model_obj,
            solver_stats=solver_stats,
            model_results=results_obj,
            decimals=2,
        )
        grid_obj._last_pyomo_model_results_table = df
    except Exception:
        # Never break solve flow due to reporting persistence.
        pass


def _quick_feasible_point_check(
    model,
    int_tol=1e-3,
    check_integrality=False,
    max_examples=5,
):
    """
    Very relaxed fallback check for ambiguous solver terminations.
    Only verifies active variables are finite; integrality check is optional.
    """
    examples = []
    n_none = 0
    n_bad_int = 0

    for var_data in model.component_data_objects(pyo.Var, active=True, descend_into=True):
        value = var_data.value
        if value is None or not math.isfinite(value):
            n_none += 1
            if len(examples) < max_examples:
                examples.append(f"{var_data.name} has invalid value {value}")
            continue

        if check_integrality and (var_data.is_integer() or var_data.is_binary()):
            if abs(value - round(value)) > int_tol:
                n_bad_int += 1
                if len(examples) < max_examples:
                    examples.append(
                        f"{var_data.name}={value:.10g} not integer within tol {int_tol}"
                    )

    ok = (n_none == 0 and n_bad_int == 0)
    return ok, {
        "reason": "feasible" if ok else "violations_found",
        "n_none": n_none,
        "n_bad_int": n_bad_int,
        "examples": examples,
    }


def pyomo_model_solve(model, grid=None, solver='ipopt', tee=False, time_limit=None, callback=False, 
              suppress_warnings=False, solver_options=None, objective_name=None, nlp_warmstart=False):
    """
    Generic Pyomo model solver with support for custom solver parameters.
    
    Parameters:
    -----------
    model : Pyomo model
        The Pyomo model to solve (any model, not just OPF)
    grid : object, optional
        Grid object (only used for MixedBinCont check if provided)
    solver : str, default='ipopt'
        Solver name ('gurobi', 'ipopt', 'bonmin', 'cbc', 'glpk', 'highs', etc.)
    tee : bool, default=False
        Print solver output
    time_limit : float, optional
        Time limit in seconds
    callback : bool, default=False
        Track feasible solutions during solve (for MIP solvers)
    suppress_warnings : bool, default=False
        Suppress infeasibility warnings
    solver_options : dict, optional
        Dictionary of solver-specific options. Format depends on solver:
        - Gurobi: {'MIPFocus': 2, 'Cuts': 2, 'Heuristics': 0.05, 'Presolve': 2, 'MIPGap': 0.01}
        - CBC: {'ratioGap': 0.01}
        - HiGHS: {'mip_rel_gap': 0.01}
        - GLPK: {'tmlim': 3600}
        - IPOPT: {'max_iter': 1000}
        - Bonmin: {'bonmin.time_limit': 3600}
        - Minotaur: {'specific_solver': 'mglob', 'executable': '/path/to/minotaur', 'time_limit': 3600, ...}
    nlp_warmstart : bool, default=False
        If True and solver is a MINLP solver (bonmin, minotaur), first solve the NLP
        relaxation with IPOPT to initialize all variable values. This gives the MINLP
        solver a much better starting point for its root-node NLP solve.
    
    Returns:
    --------
    results : SolverResults or None
        Solver results object
    solver_stats : dict or None
        Dictionary with solver statistics including feasible_solutions
    """
    solver = solver.lower()
    # Keep internal flags separate from backend solver options.
    solver_options = dict(solver_options) if solver_options else None
    feasible_solutions = []  # Always defined, but only populated if callback is used
    all_solutions = []  # Always defined, but only populated if callback is used
    bound_solutions = []  # Best-bound updates from callback log parsing
    debug_solution_check = bool((solver_options or {}).pop("debug_solution_check", True))

    # NLP warm-start: solve continuous relaxation with IPOPT first
    if nlp_warmstart and solver in ('bonmin', 'minotaur'):
        print("=" * 60)
        print("NLP WARM-START: Solving continuous relaxation with IPOPT...")
        print("=" * 60)
        try:
            ws_opt = pyo.SolverFactory('ipopt')
            ws_opt.options['print_level'] = 3 if not tee else 5
            ws_opt.options['max_iter'] = 5000
            # Relax acceptable tolerances so warm-start exits sooner
            # (default acceptable_tol=1e-6 may not be reached; 
            #  the goal is a good starting point, not full NLP optimality)
            ws_opt.options['acceptable_tol'] = 1e-4
            ws_opt.options['acceptable_constr_viol_tol'] = 1e-4
            ws_opt.options['acceptable_dual_inf_tol'] = 1e-2
            
            # Extract IPOPT-compatible options from solver_options
            # (options without 'bonmin.' prefix are IPOPT options passed through)
            # Skip warm_start_init_point/mu_init — those are for post-warmstart solves
            ws_skip = {'warm_start_init_point', 'mu_init', 'warm_start_bound_push', 'warm_start_mult_bound_push'}
            if solver_options:
                for key, val in solver_options.items():
                    if not key.startswith('bonmin.') and key not in ws_skip:
                        ws_opt.options[key] = val
            
            ws_results = ws_opt.solve(model, tee=tee)
            ws_tc = str(ws_results.solver.termination_condition)
            ws_msg = str(getattr(ws_results.solver, 'message', '') or '')
            print(f"  NLP warm-start termination: {ws_tc}")
            print(f"  NLP warm-start message:     {ws_msg}")
            
            # Verify variable values were loaded back
            n_vars = sum(1 for v in model.component_objects(pyo.Var, active=True) 
                         for _ in v)
            n_set = sum(1 for v in model.component_objects(pyo.Var, active=True) 
                        for idx in v if v[idx].value is not None)
            n_none = n_vars - n_set
            print(f"  Variables: {n_vars} total, {n_set} with values, {n_none} None")
            
            if ws_tc in ('optimal', 'locallyOptimal', 'feasible', 'acceptable'):
                print("  SUCCESS: Variable values initialized from NLP solution.")
            elif 'Acceptable' in ws_msg or 'acceptable' in ws_msg:
                print("  SUCCESS: Variable values initialized from acceptable NLP solution.")
            else:
                print("  WARNING: NLP did not converge optimally, but variable values may still help.")
            print("=" * 60)
        except Exception as e:
            print(f"  NLP warm-start failed: {e}")
            print("  Proceeding with default initialization.")
            print("=" * 60)

    # Check for MixedBinCont warning (only if grid is provided)
    if grid is not None and hasattr(grid, 'MixedBinCont') and grid.MixedBinCont and solver == 'ipopt':
        print('PyFlow ACDC is not capable of ensuring the reliability of this solution.')

    if callback:
        if solver == 'gurobi' and GUROBI_AVAILABLE:
            results, feasible_solutions, bound_solutions = _gurobi_callback(model, feasible_solutions, bound_solutions, time_limit, solver_options, tee=tee)
            # For Gurobi, all_solutions is the same as feasible_solutions
            all_solutions = feasible_solutions.copy()
        elif solver == 'bonmin':
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(model, feasible_solutions, 'bonmin', time_limit, 'bonmin.log', tee_console=tee)
        elif solver == 'ipopt':
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(model, feasible_solutions, 'ipopt', time_limit, 'ipopt.log', tee_console=tee)
        elif solver == 'highs':
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(model, feasible_solutions, 'highs', time_limit, 'highs.log', tee_console=tee)
        else:
            print(f"No callback available for {solver}")
            callback = False
    if not callback:
        # For Minotaur, check if executable is specified in solver_options
        if solver == 'minotaur':
            
            if 'specific_solver' not in solver_options or 'executable_folder' not in solver_options:
                raise ValueError("Minotaur solver requires both 'specific_solver' and 'executable_folder' in solver_options")
            specific_solver = solver_options.pop('specific_solver')
            executable_path = solver_options.pop('executable_folder')  # Remove from dict
            executable = f'{executable_path}/{specific_solver}'
            opt = pyo.SolverFactory(specific_solver, executable=executable)
        else:
            opt = pyo.SolverFactory(solver)
        
        # Set time limit (can be overridden by solver_options)
        if time_limit is not None:
            if solver == 'gurobi':
                opt.options['TimeLimit'] = time_limit
            elif solver == 'cbc':
                opt.options['seconds'] = time_limit
            elif solver == 'ipopt':
                opt.options['max_cpu_time'] = time_limit
            elif solver == 'bonmin':
                opt.options['bonmin.time_limit'] = time_limit
            elif solver == 'glpk':
                opt.options['tmlim'] = time_limit
            elif solver == 'highs':
                opt.options['time_limit'] = time_limit
            elif solver == 'minotaur':
                opt.options['--time_limit'] = time_limit

        if solver == 'bonmin' and (not solver_options or 'bonmin.nlp_failure_behavior' not in solver_options):
            # Keep searching after NLP failures unless user explicitly overrides this option.
            opt.options['bonmin.nlp_failure_behavior'] = 'fathom'
        
        # Apply custom solver options (overrides time_limit if also specified)
        if solver_options:
            for param_name, param_value in solver_options.items():
                opt.options[param_name] = param_value

        try:
            # Standard Pyomo solve: let Pyomo load solutions normally.
            results = opt.solve(model, tee=tee, load_solutions=True)
        except Exception as e:
            error_msg = str(e)
            print(f"  Solver crashed: {e}")

            solver_stats = {
                'solver': solver,
                'iterations': None,
                'best_objective': None,
                'lower_bound': None,
                'time': None,
                'termination_condition': 'error',
                'solver_message': error_msg,
                'feasible_solutions': feasible_solutions,
                'all_solutions': all_solutions,
                'bound_solutions': bound_solutions,
                'solution_found': False,
                'solution_check_reason': 'solver_exception',
                'solution_check_tol': None,
                'obj_scaling': getattr(model, 'obj_scaling', 1.0),
            }
            _store_pyomo_results_on_grid(grid, model, None, solver_stats)
            return None, solver_stats

    obj_scaling = getattr(model, 'obj_scaling', 1.0)

    # Extract solver message for more detailed termination info
    solver_message = ''
    if results:
        try:
            solver_message = str(getattr(results.solver, 'message', '') or '')
        except (AttributeError, TypeError):
            pass

    solver_stats = {
        'solver': solver,
        'iterations': None,
        'best_objective': getattr(results.problem, 'upper_bound', None) if results else None,
        'lower_bound': getattr(results.problem, 'lower_bound', None) if results else None,
        'time': getattr(results.solver, 'time', None) if results else None,
        'termination_condition': str(results.solver.termination_condition) if results else None,
        'solver_message': solver_message,
        'feasible_solutions': feasible_solutions,
        'all_solutions': all_solutions,
        'bound_solutions': bound_solutions,
        'solution_found': None,  # Set below from feasibility validation
        'solution_check_info': None,
        'obj_scaling': obj_scaling,
    }

    # Decision policy for solution_found:
    # 1) If solver termination is optimal/acceptable/feasible, trust solver and pass.
    # 2) Otherwise (max iterations, internal error, etc.), validate loaded values
    #    with the explicit feasibility checker and try alternative solution records.
    try:
        tc = str(getattr(results.solver, 'termination_condition', '') or '').lower() if results is not None else ''
    except Exception:
        tc = ''
    trusted_termination = tc in ('optimal', 'feasible', 'locallyoptimal', 'acceptable', 'locally_optimal', 'maxiterations')
    explicit_infeasible_termination = tc in (
        'infeasible',
        'locallyinfeasible',
        'infeasibleorunbounded',
        'infeasible_or_unbounded',
    )

    checker_reason = "not_used"
    checker_tol = None
    checker_info = None

    # `results.solution` payload presence is informative, but not a hard gate.
    # Some solver/Pyomo integrations can leave this payload empty while model
    # variable values are still usable in downstream steps.
    has_loaded_solution = False
    try:
        has_loaded_solution = bool(results is not None and getattr(results, "solution", None) is not None and len(results.solution) > 0)
    except Exception:
        has_loaded_solution = False

    if trusted_termination and not has_loaded_solution:
        pyomo_logger = logging.getLogger('pyomo')
        pyomo_logger.warning(
            "Solver termination indicates a good solve ('%s'), but no solution payload "
            "was loaded by Pyomo (len(results.solution)=0). This can indicate a "
            "solver/Pyomo/ASL installation or compatibility issue. Proceeding with "
            "termination-based acceptance.",
            tc,
        )

    if explicit_infeasible_termination:
        loaded_solution_feasible = False
        checker_reason = "explicit_infeasible_termination"
    elif trusted_termination:
        loaded_solution_feasible = True
        checker_reason = "trusted_termination"
    elif has_loaded_solution:
        loaded_solution_feasible = True
        checker_reason = "pyomo_loaded_solution"
    else:
        loaded_solution_feasible, checker_info = _quick_feasible_point_check(
            model,
            int_tol=1e-3,
            check_integrality=False,
        )
        checker_reason = (
            "quick_point_check_passed"
            if loaded_solution_feasible
            else "untrusted_termination"
        )

    solver_stats['solution_found'] = bool(loaded_solution_feasible)
    solver_stats['solution_check_reason'] = checker_reason
    solver_stats['solution_check_tol'] = checker_tol
    solver_stats['solution_check_info'] = checker_info

    pyomo_logger = logging.getLogger('pyomo')
    if (not suppress_warnings) and explicit_infeasible_termination:
        pyomo_logger.setLevel(logging.INFO)
        try:
            log_infeasible_constraints(model)
        except OverflowError as exc:
            pyomo_logger.warning("Skipping infeasible-constraint logging due to overflow: %s", exc)
        except Exception as exc:
            pyomo_logger.warning("Skipping infeasible-constraint logging due to error: %s", exc)

    _store_pyomo_results_on_grid(grid, model, results, solver_stats)
    return results, solver_stats



def OPF_updateParam(model,grid):
 
    for n in grid.nodes_AC:
        model.P_Gain_known_AC[n.nodeNumber] = n.PGi
        model.P_Load_known_AC[n.nodeNumber] = n.PLi
        model.Q_known_AC[n.nodeNumber] = n.QGi-n.QLi
        model.price[n.nodeNumber] = n.price
        
    for n in grid.nodes_DC:
        model.P_known_DC[n.nodeNumber] = n.P_DC
    

    return model

def OPF_obj_L(model,grid,ObjRule):
    
    if ObjRule['Energy_cost']['w']==0:
        return 0
    #(model.PGi_gen[gen.genNumber]*grid.S_base)**2*gen.qf+
    AC= sum((model.PGi_gen[gen.genNumber]*grid.S_base*model.lf[gen.genNumber]+model.np_gen[gen.genNumber]*gen.fc) for gen in grid.Generators)

    return AC
    

def OPF_obj(model,grid,weights_def,OnlyGen=True):
    np_den_eps = 1e-3
   
    # for node in  model.nodes_AC:
    #     nAC=grid.nodes_AC[node]
    #     if nAC.Num_conv_connected >= 2:
    #         obj_expr += sum(model.Q_conv_s_AC[conv]**2 for conv in nAC.connected_conv)

   
    def formula_Min_Ext_Gen():
        if weights_def['Ext_Gen']['w']==0:
            return 0
        return sum((model.PGi_opt[node]*grid.S_base) for node in model.nodes_AC)

    def formula_Energy_cost():
        if weights_def['Energy_cost']['w']==0:
            return 0
        
        AC= 0
        DC= 0
        if grid.ACmode:
            if grid.act_gen:
                AC= sum((((model.PGi_gen[gen.genNumber]*grid.S_base)**2*gen.qf/(model.np_gen[gen.genNumber] + np_den_eps)+model.PGi_gen[gen.genNumber]*grid.S_base*model.lf[gen.genNumber]+model.np_gen[gen.genNumber]*gen.fc)*model.gen_active[gen.genNumber]) for gen in grid.Generators)
            else:
                AC= sum(((model.PGi_gen[gen.genNumber]*grid.S_base)**2*gen.qf/(model.np_gen[gen.genNumber] + np_den_eps)+model.PGi_gen[gen.genNumber]*grid.S_base*model.lf[gen.genNumber]+model.np_gen[gen.genNumber]*gen.fc) for gen in grid.Generators)
        if grid.DCmode:
            DC= sum(((model.PGi_gen_DC[gen.genNumber_DC]*grid.S_base)**2*gen.qf/(model.np_gen_DC[gen.genNumber_DC] + np_den_eps)+model.PGi_gen_DC[gen.genNumber_DC]*grid.S_base*model.lf_dc[gen.genNumber_DC]+model.np_gen_DC[gen.genNumber_DC]*gen.fc) for gen in grid.Generators_DC)
        
        if OnlyGen:
            return AC+DC
        
        else :
            nodes_with_RenSource = [node for node in model.nodes_AC if grid.nodes_AC[node].RenSource]
            nodes_with_conv= [node for node in model.nodes_AC if grid.nodes_AC[node].Num_conv_connected != 0]
            return AC+DC  \
                   + sum(model.PGi_ren[node]*model.price[node] for node in nodes_with_RenSource)*grid.S_base \
                   + sum(model.P_conv_AC[node]*model.price[node] for node in nodes_with_conv)*grid.S_base
    def formula_AC_losses():
        if weights_def['AC_losses']['w']==0:
            return 0
        loss = sum(model.PAC_line_loss[line] for line in model.lines_AC)
        if grid.TAP_tf:
            loss += sum(model.tf_PAC_line_loss[tf] for tf in model.lines_AC_tf)
        if grid.TEP_AC:
            loss += sum(model.exp_PAC_line_loss[exp] for exp in model.lines_AC_exp)   
        if grid.REC_AC:
            loss += sum(model.rec_PAC_line_loss[rec] for rec in model.lines_AC_rec)
        if grid.CT_AC:
            loss += sum(model.ct_PAC_line_loss[ct] for ct in model.lines_AC_ct)
        return loss*grid.LCoE

    def formula_DC_losses():
        if weights_def['DC_losses']['w']==0:
            return 0
        loss = sum(model.PDC_line_loss[line] for line in model.lines_DC)
        if grid.CDC:
            loss += sum(model.CDC_loss[conv] for conv in model.DCDC_conv)
        return loss*grid.LCoE

    def formula_Converter_Losses():
        if weights_def['Converter_Losses']['w']==0:
            return 0
        return sum(model.P_conv_loss[conv]+model.P_AC_loss_conv[conv] for conv in model.conv)*grid.LCoE

    def formula_General_Losses():
        if weights_def['General_Losses']['w']==0:
            return 0
        load = 0
        if grid.nodes_AC != []:
            load = sum(model.P_known_AC[node] for node in model.nodes_AC)
        if grid.nodes_DC != []:
            load = sum(model.P_known_DC[node] for node in model.nodes_DC)
        gen = 0
        if grid.Generators != []:
            gen = sum(model.PGi_gen[gen] for gen in model.gen_AC)
        if grid.RenSources != []:
            gen = sum(model.P_renSource[rs]*model.gamma[rs] for rs in model.ren_sources)
        return (gen - load)*grid.LCoE
    
    def formula_curtailment_red():
        if weights_def['Curtailment_Red']['w']==0:
            return 0
        ac_curt=0
        dc_curt=0
        if grid.ACmode:
            ac_curt= sum((1-model.gamma[rs])*model.P_renSource[rs]*model.price[grid.rs2node['AC'].get(rs, 0)]*rs.sigma for rs in model.ren_sources)*grid.S_base
        if grid.DCmode:
            dc_curt= sum((1-model.gamma[rs])*model.P_renSource[rs]*model.price_DC[grid.rs2node['DC'].get(rs, 0)]*rs.sigma for rs in model.ren_sources)*grid.S_base
        return ac_curt+dc_curt
    def formula_CG():
       if weights_def['PZ_cost_of_generation']['w']==0:
           return 0
       return sum(model.SocialCost[price_zone] for price_zone in model.M)
   
    def formula_Offshoreprofit():
        from .Classes import OffshorePrice_Zone
        if weights_def['Renewable_profit']['w']==0:
            return 0
        nodes_with_RenSource = []
        convloss=0
        for price_zone in model.M:
            for conv in grid.Price_Zones[price_zone].ConvACDC:     
                convloss+=model.price_zone_price[price_zone]*(model.P_conv_loss[conv.ConvNumber]+model.P_AC_loss_conv[conv.ConvNumber])*grid.S_base
            if isinstance(grid.Price_Zones[price_zone], OffshorePrice_Zone):
                # Loop through the nodes assigned to the offshore price_zone
                for node in grid.Price_Zones[price_zone].nodes_AC:
                    # Check if the node is marked as a renewable source and add it to the list
                    if node.RenSource:
                        nodes_with_RenSource.append(node.nodeNumber)
        
        return -sum(model.PGi_ren[node]*model.price[node] for node in nodes_with_RenSource)*grid.S_base +convloss
   
    def formula_Gen_set_dev():
        if weights_def['Gen_set_dev']['w']==0:
            return 0
        return sum((model.PGi_gen[gen.genNumber]-gen.Pset)**2 for gen in grid.Generators)
    s=1
    for key, entry in weights_def.items():
        if key == 'Ext_Gen':
            entry['f'] = formula_Min_Ext_Gen()
        elif key == 'Energy_cost':
            entry['f'] = formula_Energy_cost()
        elif key == 'AC_losses':
            entry['f'] = formula_AC_losses()
        elif key == 'DC_losses':
            entry['f'] = formula_DC_losses()
        elif key == 'Converter_Losses':
            entry['f'] = formula_Converter_Losses()
        elif key == 'General_Losses':
            entry['f'] = formula_General_Losses()
        elif key == 'Curtailment_Red':   
            entry ['f'] = formula_curtailment_red()
        elif key == 'PZ_cost_of_generation':
            entry['f']  =formula_CG()   
        elif key == 'Renewable_profit':
            entry['f']  =formula_Offshoreprofit()    
        elif key == 'Gen_set_dev':
            entry['f']  =formula_Gen_set_dev()  
        
    s=1
    total_weight = sum(entry['w'] for entry in weights_def.values())
    if total_weight== 0:
        weighted_sum=0
    else:
        weighted_sum = sum(entry['w'] / total_weight * entry['f'] for entry in weights_def.values())
    
    
    return weighted_sum






def Translate_pyf_OPF(grid,Price_Zones=False):
    """Translation of element wise to internal numbering"""
    AC_info, DC_info, Conv_info,DCDC_info = None, None, None,None
    ACmode= grid.ACmode
    DCmode = grid.DCmode
    "AC system info"
    lista_nodos_AC = list(range(0, grid.nn_AC))
    lista_lineas_AC = list(range(0, grid.nl_AC))
    lista_lineas_AC_exp = list(range(0, grid.nle_AC))
    lista_lineas_AC_tf = list(range(0, grid.nttf))
    lista_lineas_AC_rec = list(range(0, grid.nlr_AC))
    lista_lineas_AC_ct = list(range(0, grid.nct_AC))
    # Dictionaries for AC variables
    price, V_ini_AC, Theta_ini = {}, {}, {}
    P_renSource, P_know, Q_know,np_rsgen = {}, {}, {}, {}
    S_lineAC_limit,S_lineACexp_limit,S_lineACtf_limit,m_tf_og,NP_lineAC  = {}, {}, {}, {},{}
    S_lineACrec_lim, S_lineACrec_lim_new,REC_AC_act = {}, {}, {}
    lf,qf,fc,np_gen = {}, {}, {}, {}
    lf_DC,qf_DC,fc_DC,np_gen_DC = {}, {}, {}, {}

    S_lineACct_lim,cab_types_set,allowed_types = {},{},{}

    u_min_ac = list(range(0, grid.nn_AC))
    u_max_ac = list(range(0, grid.nn_AC))

    AC_slack, AC_PV = [], []

    # Fill AC node and line information
    
    for gen in grid.Generators:
        lf[gen.genNumber] = gen.lf
        qf[gen.genNumber] = gen.qf
        fc[gen.genNumber] = gen.fc
        np_gen[gen.genNumber] = gen.np_gen
    
    lista_gen = list(range(0, grid.n_gen))
    
    for gen in grid.Generators_DC:
        lf_DC[gen.genNumber_DC] = gen.lf
        qf_DC[gen.genNumber_DC] = gen.qf
        fc_DC[gen.genNumber_DC] = gen.fc
        np_gen_DC[gen.genNumber_DC] = gen.np_gen
    
    lista_gen_DC = list(range(0, grid.n_gen_DC))
       
    nn_rs=0
    for rs in grid.RenSources:
        nn_rs+=1
        P_renSource[rs.rsNumber]=rs.PGi_ren
        np_rsgen[rs.rsNumber] = rs.np_rsgen

    lista_rs = list(range(0, nn_rs))

    gen_rs_info = pack_variables(P_renSource,np_rsgen,lista_rs)
    gen_AC_info = pack_variables(lf,qf,fc,np_gen,lista_gen)
    gen_DC_info = pack_variables(lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC)
    gen_info = pack_variables(gen_AC_info,gen_DC_info,gen_rs_info)

    "Price zone info"
   
    price_zone_prices, price_zone_as, price_zone_bs, PGL_min, PGL_max, PL_price_zone =  {}, {}, {}, {}, {}, {}
    nn_M, lista_M = 0, []
    node2price_zone = {'DC': {}, 'AC': {}}
    price_zone2node = {'DC': {}, 'AC': {}}
    if Price_Zones:
        for m in grid.Price_Zones:
            
            nn_M += 1
            price_zone_prices[m.price_zone_num] = m.price
            price_zone_as[m.price_zone_num] = m.a
            price_zone_bs[m.price_zone_num] = m.b
            import_M = m.import_pu_L
            export_M = m.export_pu_G * (sum(sum(rs.PGi_ren for rs in node.connected_RenSource) + sum(gen.Max_pow_gen for gen in node.connected_gen) for node in m.nodes_AC))*grid.S_base
            PL_price_zone[m.price_zone_num] = 0
            
            if ACmode:
                price_zone2node['AC'][m.price_zone_num] = []
                for n in m.nodes_AC:
                    price_zone2node['AC'][m.price_zone_num].append(n.nodeNumber)
                    node2price_zone['AC'][n.nodeNumber] = m.price_zone_num
                    PL_price_zone[m.price_zone_num] += n.PLi
            
            if DCmode:
                price_zone2node['DC'][m.price_zone_num] = []
                for n in m.nodes_DC:
                    price_zone2node['DC'][m.price_zone_num].append(n.nodeNumber)
                    node2price_zone['DC'][n.nodeNumber] = m.price_zone_num
                    PL_price_zone[m.price_zone_num] += n.PLi
            PGL_min[m.price_zone_num] = max(m.PGL_min, -import_M * PL_price_zone[m.price_zone_num]*grid.S_base)
            PGL_max[m.price_zone_num] = min(m.PGL_max, export_M)
        lista_M = list(range(0, nn_M))
    
    Price_Zone_Lists = pack_variables(lista_M, node2price_zone, price_zone2node)
    Price_Zone_lim = pack_variables(price_zone_as, price_zone_bs, PGL_min, PGL_max)
    Price_Zone_info = pack_variables(Price_Zone_Lists, Price_Zone_lim)

    if ACmode:
        for n in grid.nodes_AC:
            V_ini_AC[n.nodeNumber] = n.V_ini
            Theta_ini[n.nodeNumber] = n.theta_ini
            
            P_know[n.nodeNumber] = n.PGi - n.PLi
            Q_know[n.nodeNumber] = n.QGi - n.QLi
            
            u_min_ac[n.nodeNumber] = n.Umin
            u_max_ac[n.nodeNumber] = n.Umax
            
            price[n.nodeNumber] = n.price
            
            if n.type == 'Slack':
                AC_slack.append(n.nodeNumber)
            elif n.type == 'PV':
                AC_PV.append(n.nodeNumber)
            
        
        for l in grid.lines_AC:
            S_lineAC_limit[l.lineNumber]    = l.MVA_rating / grid.S_base
        
        for l in grid.lines_AC_exp:
            S_lineACexp_limit[l.lineNumber] = l.MVA_rating / grid.S_base
            NP_lineAC[l.lineNumber]         = l.np_line

        for l in grid.lines_AC_rec:
            S_lineACrec_lim[l.lineNumber] = l.MVA_rating / grid.S_base
            S_lineACrec_lim_new[l.lineNumber] = l.MVA_rating_new / grid.S_base
            REC_AC_act[l.lineNumber] = 0 if not l.rec_branch  else 1

        for l in grid.lines_AC_tf:
            S_lineACtf_limit[l.lineNumber]  = l.MVA_rating / grid.S_base
            m_tf_og[l.lineNumber]           = l.m
            
        for l in grid.lines_AC_ct:
            for i in range(len(l.MVA_rating_list)):
                S_lineACct_lim[l.lineNumber,i] = l.MVA_rating_list[i] / grid.S_base
        if grid.Cable_options is not None and len(grid.Cable_options) > 0:
            cab_types_set = list(range(0,len(grid.Cable_options[0]._cable_types)))
    
        else:
            cab_types_set = []
        allowed_types = grid.cab_types_allowed
        
        # Packing common AC info
        AC_Lists = pack_variables(lista_nodos_AC, lista_lineas_AC,lista_lineas_AC_tf,AC_slack, AC_PV)
        AC_nodes_info = pack_variables(u_min_ac, u_max_ac, V_ini_AC, Theta_ini, P_know, Q_know, price)
        AC_lines_info = pack_variables(S_lineAC_limit,S_lineACtf_limit,m_tf_og)
        
        EXP_info = pack_variables(lista_lineas_AC_exp,S_lineACexp_limit,NP_lineAC)
        REC_info = pack_variables(lista_lineas_AC_rec,S_lineACrec_lim,S_lineACrec_lim_new,REC_AC_act)
        CT_info = pack_variables(lista_lineas_AC_ct,S_lineACct_lim,cab_types_set,allowed_types)
        AC_info = pack_variables(AC_Lists, AC_nodes_info, AC_lines_info,EXP_info,REC_info,CT_info)
    
   
    if DCmode:

        # DC and Converter Variables (if not OnlyAC)
        lista_nodos_DC = list(range(0, grid.nn_DC))
        lista_nodos_DC_sin_cn=lista_nodos_DC
        lista_lineas_DC = list(range(0, grid.nl_DC))
        lista_conv = list(range(0, grid.nconv))


        u_min_dc = list(range(0, grid.nn_DC))
        u_max_dc = list(range(0, grid.nn_DC))
        u_c_min = list(range(0, grid.nconv))
        u_c_max = list(range(0, grid.nconv))

        V_ini_DC, P_known_DC, P_conv_limit,price_dc = {}, {}, {},{}
        P_lineDC_limit, NP_lineDC = {}, {}

        AC_nodes_connected_conv, DC_nodes_connected_conv = [], []
        S_limit_conv, np_conv, P_conv_loss = {}, {}, {}
        DC_slack = []

        P_DCDC_limit, Pset_DCDC = {}, {}
        
        
        for n in grid.nodes_DC:
            V_ini_DC[n.nodeNumber] = n.V_ini
            P_known_DC[n.nodeNumber] = n.PGi-n.PLi
            u_min_dc[n.nodeNumber] = n.Umin
            u_max_dc[n.nodeNumber] = n.Umax
            price_dc[n.nodeNumber] = n.price
            if n.type == 'Slack':
                DC_slack.append(n.nodeNumber)

        for l in grid.lines_DC:
            P_lineDC_limit[l.lineNumber] = l.MW_rating / grid.S_base
            NP_lineDC[l.lineNumber] = l.np_line

        lista_DCDC = list(range(0, grid.ncdc_DC))

        for cn in grid.Converters_DCDC:
            P_DCDC_limit[cn.ConvNumber] = cn.MW_rating / grid.S_base
            Pset_DCDC[cn.ConvNumber] = cn.Powerto

        
        DCDC_info = pack_variables(lista_DCDC,P_DCDC_limit,Pset_DCDC)
        # Packing AC, DC, Converter, and Price_Zone info
        DC_Lists = pack_variables(lista_nodos_DC, lista_lineas_DC, DC_slack,DC_nodes_connected_conv)
        DC_nodes_info = pack_variables(u_min_dc, u_max_dc, V_ini_DC, P_known_DC,price_dc)
        DC_lines_info = pack_variables(P_lineDC_limit, NP_lineDC)
        DC_info = pack_variables(DC_Lists, DC_nodes_info, DC_lines_info,DCDC_info)
   
    if ACmode and DCmode:

        for conv in grid.Converters_ACDC:
            AC_nodes_connected_conv.append(conv.Node_AC.nodeNumber)
            DC_nodes_connected_conv.append(conv.Node_DC.nodeNumber)
            P_conv_limit[conv.Node_DC.nodeNumber] = conv.MVA_max / grid.S_base
            S_limit_conv[conv.ConvNumber] = conv.MVA_max / grid.S_base
            np_conv[conv.ConvNumber] = conv.np_conv
            u_c_min[conv.ConvNumber] = conv.Ucmin
            u_c_max[conv.ConvNumber] = conv.Ucmax
            P_conv_loss[conv.ConvNumber] = conv.P_loss

        Conv_Lists = pack_variables(lista_conv, np_conv)
        Conv_Volt = pack_variables(u_c_min, u_c_max, S_limit_conv, P_conv_limit) 
        Conv_info = pack_variables(Conv_Lists, Conv_Volt)
    
    # Return as dictionary for easier extension and maintenance
    return {
        'AC_info': AC_info,
        'DC_info': DC_info,
        'Conv_info': Conv_info,
        'Price_Zone_info': Price_Zone_info,
        'gen_info': gen_info
    }




def OPF_line_res (model,grid):
    opt_res_Loading_line = {}
    opt_res_Loading_grid ={}
    loadS_AC = np.zeros(grid.Num_Grids_AC)
    loadP_DC = np.zeros(grid.Num_Grids_DC)
    

    def process_line_AC(line):
        l= line.lineNumber
        G = grid.Graph_line_to_Grid_index_AC[line]
        
        P_from = PAC_from_values[l]
        P_to   = PAC_to_values[l]
        Q_from = QAC_from_values[l]
        Q_to   = QAC_to_values[l]
        
        S_from = np.sqrt(P_from**2+Q_from**2)
        S_to = np.sqrt(P_to**2+Q_to**2)
        
        loading = max(S_from,S_to)*grid.S_base/line.MVA_rating
        # with lock:
        loadS_AC[G] += max(S_from, S_to) * grid.S_base
        opt_res_Loading_line[f'AC_Load_{line.name}'] = loading
        opt_res_Loading_line[f'AC_from_{line.name}'] = S_from * grid.S_base
        opt_res_Loading_line[f'AC_to_{line.name}'] = S_to * grid.S_base
    
    
    def process_line_DC(line):
        G = grid.Graph_line_to_Grid_index_DC[line]
        
        l= line.lineNumber
        P_from = PDC_from_values[l]
        P_to   = PDC_to_values[l]
      
        loading = max(P_from,P_to)*grid.S_base/line.MW_rating
        # with lock:
        loadP_DC[G] += max(P_from, P_to) * grid.S_base
        opt_res_Loading_line[f'DC_Load_{line.name}'] = loading
        opt_res_Loading_line[f'DC_from_{line.name}'] = P_from * grid.S_base
        opt_res_Loading_line[f'DC_to_{line.name}'] = P_to * grid.S_base
    
    if grid.lines_AC: 
        PAC_from_values= {k: np.float64(pyo.value(v)) for k, v in model.PAC_from.items()}
        PAC_to_values  = {k: np.float64(pyo.value(v)) for k, v in model.PAC_to.items()}
        QAC_from_values= {k: np.float64(pyo.value(v)) for k, v in model.QAC_from.items()}
        QAC_to_values  = {k: np.float64(pyo.value(v)) for k, v in model.QAC_to.items()}
        
        
        with ThreadPoolExecutor() as executor:
            executor.map(process_line_AC, grid.lines_AC)
    
    if grid.lines_DC:
        PDC_from_values= {k: np.float64(pyo.value(v)) for k, v in model.PDC_from.items()}
        PDC_to_values  = {k: np.float64(pyo.value(v)) for k, v in model.PDC_to.items()}
        
        with ThreadPoolExecutor() as executor:
            executor.map(process_line_DC, grid.lines_DC)
        
        
    total_loading = 0
    total_rating = sum(grid.rating_grid_AC) + sum(grid.rating_grid_DC)
    
    for g in range(grid.Num_Grids_AC):
        loading = loadS_AC[g]
        total_loading += loading
        opt_res_Loading_grid[f'Loading_Grid_AC_{g+1}'] = 0 if grid.rating_grid_AC[g] == 0 else loading / grid.rating_grid_AC[g]

    for g in range(grid.Num_Grids_DC):
        loading = loadP_DC[g]
        total_loading += loading
        opt_res_Loading_grid[f'Loading_Grid_DC_{g+1}'] = loading / grid.rating_grid_DC[g]
    opt_res_Loading_grid['Total'] = 0 if total_rating == 0 else total_loading /total_rating
    
    return opt_res_Loading_line,opt_res_Loading_grid


def OPF_price_priceZone (model,grid):
    opt_res_Loading_pz = {}
    for pz in grid.Price_Zones:
        m= pz.price_zone_num
        price = pyo.value(model.price_zone_price[m])
        opt_res_Loading_pz[pz.name]=price

    
    return opt_res_Loading_pz
 
def OPF_step_results(model,grid):
    opt_res_P_conv_DC = {}
    opt_res_P_conv_AC = {}
    opt_res_Q_conv_AC = {}
    opt_res_Loading_conv={}
    opt_P_load = {}
    opt_res_P_extGrid = {}
    opt_res_Q_extGrid  = {}
    opt_res_curtailment ={}
   
    if grid.ACmode and grid.DCmode:
        P_conv_s_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_s_AC.items()}
        Q_conv_s_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.Q_conv_s_AC.items()}
        P_conv_c_AC_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_c_AC.items()}
        P_conv_loss_values   = {k: np.float64(pyo.value(v)) for k, v in model.P_conv_loss.items()}
        
        def process_converter(conv):
            nconv = conv.ConvNumber
            name = conv.name   
           
            # Use converter-specific DC-side power for consistent per-converter reporting.
            opt_res_P_conv_DC[name] = -(P_conv_c_AC_values[nconv] + P_conv_loss_values[nconv]) * conv.np_conv
            opt_res_P_conv_AC[name] = P_conv_s_AC_values[nconv] * conv.np_conv
            opt_res_Q_conv_AC[name] = Q_conv_s_AC_values[nconv] * conv.np_conv
                
            
            S_AC = np.sqrt(opt_res_P_conv_AC[name]**2 + opt_res_Q_conv_AC[name]**2)
            P_DC = opt_res_P_conv_DC[name]
            
            if conv.np_conv == 0:
                opt_res_Loading_conv[name]=0
            else:
                opt_res_Loading_conv[name]=max(S_AC, np.abs(P_DC)) * grid.S_base / (conv.MVA_max*conv.np_conv)
    
        with ThreadPoolExecutor() as executor:
            executor.map(process_converter, grid.Converters_ACDC)
    
    Pload_values = {k: np.float64(pyo.value(v)) for k, v in model.P_known_AC.items()}
    PGen_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_gen.items()}
    QGen_values  = {k: np.float64(pyo.value(v)) for k, v in model.QGi_gen.items()}
    gamma_values = {k: np.float64(pyo.value(v)) for k, v in model.gamma.items()}
    Pren_values  = {k: np.float64(pyo.value(v)) for k, v in model.P_renSource.items()}
    Qren_values  = {k: np.float64(pyo.value(v)) for k, v in model.Q_renSource.items()}
    if grid.act_gen:
        gen_active_values = {k: np.float64(pyo.value(v)) for k, v in model.gen_active.items()}
    else:
        # Use same keys as PGen_values to ensure consistency
        gen_active_values = {k: 1 for k in PGen_values.keys()}
    def process_load(node):
        nAC= node.nodeNumber
        name = node.name
        
        opt_P_load[name]= -Pload_values[nAC]
        
        
    with ThreadPoolExecutor() as executor:
        executor.map(process_load, grid.nodes_AC)
    
    def process_element(element):
        if hasattr(element, 'genNumber'):  # Generator
            name = element.name
            opt_res_P_extGrid [name] = PGen_values[element.genNumber]*gen_active_values[element.genNumber]
            opt_res_Q_extGrid [name] = QGen_values[element.genNumber]*gen_active_values[element.genNumber]

        elif hasattr(element, 'rsNumber'):  # Renewable Source
            name = element.name
            gamma=gamma_values[element.rsNumber]
            opt_res_curtailment [name] = 1-gamma
            opt_res_P_extGrid[f'RenSource_{name}'] = Pren_values[element.rsNumber]*gamma
            opt_res_Q_extGrid[f'RenSource_{name}'] = Qren_values[element.rsNumber]

    # Combine Generators and Renewable Sources into one iterable
    elements = grid.Generators + grid.RenSources
    
    # Parallelize processing
    with ThreadPoolExecutor() as executor:
        executor.map(process_element, elements)
        
            
    return (opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,
                opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment, 
                opt_res_Loading_conv)


      

def calculate_objective(grid,obj,OnlyGen=True):
   
    if obj =='Ext_Gen':
        return sum((node.PGi_opt*grid.S_base) for node in grid.nodes_AC)

    if obj =='Energy_cost':
        AC= 0
        DC= 0
        if grid.ACmode:
            if grid.act_gen:
                # gen.PGen already includes gen_active multiplier from export, so don't multiply again
                AC= sum(((gen.PGen*grid.S_base)**2*gen.qf+gen.PGen*grid.S_base*gen.lf+gen.np_gen*gen.fc) for gen in grid.Generators)
            else:
                AC= sum(((gen.PGen*grid.S_base)**2*gen.qf+gen.PGen*grid.S_base*gen.lf+gen.np_gen*gen.fc) for gen in grid.Generators)
        if grid.DCmode:
            DC= sum(((gen.PGen*grid.S_base)**2*gen.qf+gen.PGen*grid.S_base*gen.lf+gen.np_gen*gen.fc) for gen in grid.Generators_DC)
        return AC+DC

        
    if obj =='PZ_cost_of_generation':
       return sum(pz.a*(pz.PN*grid.S_base)**2+pz.b*(pz.PN*grid.S_base) for pz in grid.Price_Zones)
   
    if obj =='AC_losses':
        return (sum(line.P_loss for line in grid.lines_AC)+
                sum(tf.P_loss for tf in grid.lines_AC_tf)+
                sum(line.P_loss for line in grid.lines_AC_exp)+
                sum(line.P_loss for line in grid.lines_AC_rec)+
                sum(line.P_loss for line in grid.lines_AC_ct))*grid.S_base*grid.LCoE

    if obj =='DC_losses':
        return (sum(line.loss for line in grid.lines_DC)+
                sum(conv.loss for conv in grid.Converters_DCDC))*grid.S_base*grid.LCoE

    if obj =='Converter_Losses':
        return sum(conv.P_loss for conv in grid.Converters_ACDC)*grid.S_base*grid.LCoE

    if obj =='General_Losses':
        return (sum(line.P_loss for line in grid.lines_AC) +
                sum(tf.P_loss for tf in grid.lines_AC_tf) +
                sum(line.P_loss for line in grid.lines_AC_exp) +
                sum(line.loss for line in grid.lines_DC) +
                sum(conv.P_loss for conv in grid.Converters_ACDC))*grid.S_base*grid.LCoE

    if obj =='Curtailment_Red':
        ac_curt=0
        dc_curt=0
        if grid.ACmode:
            ac_curt= sum((1-rs.gamma)*rs.PGi_ren*grid.nodes_AC[grid.rs2node['AC'].get(rs, 0)].price*rs.sigma for rs in grid.RenSources)*grid.S_base
        if  grid.DCmode:
            dc_curt= sum((1-rs.gamma)*rs.PGi_ren*grid.nodes_DC[grid.rs2node['DC'].get(rs, 0)].price*rs.sigma for rs in grid.RenSources)*grid.S_base
        return ac_curt+dc_curt
    
    if obj=='PZ_cost_of_generation':
           return  sum(pz.PN**2*pz.a+pz.PN*pz.b for pz in grid.Price_Zones)
   
    if obj=='Gen_set_dev':
        return sum((gen.PGen-gen.Pset)**2 for gen in grid.Generators)
    
    return 0

def calculate_objective_from_model(model, grid, weights_def, OnlyGen=True):
    """
    Calculate weighted objective value directly from a solved Pyomo model.
    Uses OPF_obj() to build the expression, then evaluates it once.
    
    Args:
        model: Solved Pyomo model
        grid: Grid object (needed for generator properties and grid structure)
        ObjRule: Dictionary with objective rules (same format as OPF_obj)
        OnlyGen: Boolean flag for energy cost calculation
    
    Returns:
        Weighted sum of objectives (float)
    """
    # Build the objective expression (Pyomo expression)
    obj = OPF_obj(model, grid, weights_def, OnlyGen)
    # Evaluate it once
    obj_value = pyo.value(obj)
    return obj_value

def export_solver_progress_to_excel(solver_stats, save_path):
    import pandas as pd
    """Export solver progress to a 13-column Excel regardless of length differences.

    Columns:
    - time_all, obj_all, iter_all (from all_solutions)
    - time_feasible, obj_feasible, iter_feasible (from feasible_solutions)
    - time_bound, bound_value, iter_bound (from bound_solutions)
    - is_feasible_all, inf_pr_all, inf_du_all (from all_solutions when available, e.g. IPOPT)
    - kkt_inf_du_feasible (inf_du only where is_feasible_all is True)
    """
    # all_solutions base format: [time_sec, objective, cumulative_iterations, nlp_call_num, is_feasible]
    # optional extra fields by solver:
    # - IPOPT: [time, objective, iter, iter, is_feasible, inf_pr, inf_du]
    all_solutions = solver_stats.get('all_solutions', []) or []
    feasible_solutions = solver_stats.get('feasible_solutions', []) or []  # (time, obj, iterations)
    bound_solutions = solver_stats.get('bound_solutions', []) or []  # (time, bound, iterations_like_counter)

    # Map to uniform tuples (time, obj, iter)
    all_triplets = [(a[0], a[1], a[2]) for a in all_solutions]
    all_feasibility = [a[4] if len(a) > 4 else None for a in all_solutions]
    all_inf_pr = [a[5] if len(a) > 5 else None for a in all_solutions]
    all_inf_du = [a[6] if len(a) > 6 else None for a in all_solutions]
    feas_triplets = [(f[0], f[1], f[2]) for f in feasible_solutions]
    bound_triplets = [(b[0], b[1], b[2]) for b in bound_solutions]

    max_len = max(len(all_triplets), len(feas_triplets), len(bound_triplets), 1)

    # Pad shorter list with None
    def pad(seq, n):
        return seq + [(None, None, None)] * (n - len(seq))

    all_padded = pad(all_triplets, max_len)
    feas_padded = pad(feas_triplets, max_len)
    bound_padded = pad(bound_triplets, max_len)
    feas_flag_padded = all_feasibility + [None] * (max_len - len(all_feasibility))
    inf_pr_padded = all_inf_pr + [None] * (max_len - len(all_inf_pr))
    inf_du_padded = all_inf_du + [None] * (max_len - len(all_inf_du))
    kkt_inf_du_feasible = [
        inf_du if is_feasible is True else None
        for is_feasible, inf_du in zip(feas_flag_padded, inf_du_padded)
    ]

    df = pd.DataFrame({
        'time_all': [t for t, _, _ in all_padded],
        'obj_all': [o for _, o, _ in all_padded],
        'iter_all': [it for _, _, it in all_padded],
        'time_feasible': [t for t, _, _ in feas_padded],
        'obj_feasible': [o for _, o, _ in feas_padded],
        'iter_feasible': [it for _, _, it in feas_padded],
        'time_bound': [t for t, _, _ in bound_padded],
        'bound_value': [o for _, o, _ in bound_padded],
        'iter_bound': [it for _, _, it in bound_padded],
        'is_feasible_all': feas_flag_padded,
        'inf_pr_all': inf_pr_padded,
        'inf_du_all': inf_du_padded,
        'kkt_inf_du_feasible': kkt_inf_du_feasible,
    })

    # Ensure .xlsx extension
    if not isinstance(save_path, str) or not save_path.lower().endswith('.xlsx'):
        save_path = f"{save_path}.xlsx"

    df.to_excel(save_path, index=False)
    return save_path