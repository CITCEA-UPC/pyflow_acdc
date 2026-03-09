import time
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import numpy as np
import math
import pyomo.environ as pyo
import pandas as pd
import sys
try:
    import gurobipy
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from .ACDC_OPF_NL_model import OPF_create_NLModel_ACDC,TEP_variables
from .AC_OPF_L_model import OPF_create_LModel_AC,ExportACDC_Lmodel_toPyflowACDC
from .ACDC_OPF import pyomo_model_solve,OPF_obj,OPF_obj_L,obj_w_rule,ExportACDC_NLmodel_toPyflowACDC,calculate_objective,reset_to_initialize
from .ACDC_Static_TEP import transmission_expansion, linear_transmission_expansion

from .Graph_and_plot import save_network_svg


__all__ = [
    'sequential_CSS',
    'min_sub_connections',
    'MIP_path_graph',
    'simple_CSS',
    'simple_assign_cable_types'
]


@dataclass
class MIPConfig:
    """
    Lightweight container for MIP / path-graph options.

    This lets us avoid threading a long list of flags between
    sequential_CSS, min_sub_connections and MIP_path_graph,
    while keeping the public function signatures unchanged.
    """
    solver_name: str = 'glpk'
    backend: str = 'pyomo'
    crossings: bool = False
    tee: bool = False
    callback: bool = False
    MIP_gap: float | None = None
    min_turbines_per_string: bool | int = False
    fixed_substation_connections: int | None = None
    t_MW: float | None = None


def sequential_CSS(grid,NPV=True,LCoE=None,n_years=25,Hy=8760,discount_rate=0.02,ObjRule=None,max_turbines_per_string=None,limit_crossings=True,sub_min_connections=True,
                   MIP_solver='glpk',CSS_L_solver='glpk',CSS_NL_solver='bonmin',svg=None,max_iter=None,time_limit=300,NL=False,tee=False,fs=False,save_path=None,
                   MIP_gap=0.01,backend='pyomo',min_turbines_per_string=False,fixed_substation_connections=None,max_ns=None):
    
    if LCoE is not None:
        grid.LCoE = LCoE
    # Determine save directory: create "sequential_CSS" folder
    if save_path is not None and os.path.isdir(save_path):
        # If save_path is provided and is a directory, create "sequential_CSS" inside it
        save_dir = os.path.join(save_path, 'sequential_CSS')
    else:
        # If save_path is None or not a directory, create "sequential_CSS" in current working directory
        save_dir = 'sequential_CSS'
    if MIP_solver == 'ortools':
        backend = 'ortools'
    # Create the directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    

    staring_cables = grid.Cable_options[0].cable_types
    new_cables = staring_cables.copy()
  
    results = []
    tot_timing_info = {}
    i = 0
    seq_path_time = 0
    seq_css_time = 0
    weights_def, PZ = obj_w_rule(grid,ObjRule,True)
    t0 = time.perf_counter()
    t_MW = grid.RenSources[0].PGi_ren_base*grid.S_base
    #print(f'DEBUG: t_MW {t_MW}')
    #print(f'DEBUG: starting max flow {max_flow}')

    if max_iter is None:
        max_iter = len(grid.Cable_options[0].cable_types)
    og_cable_types = grid.Cable_options[0].cable_types.copy()
    
    MIP_time = grid.MIP_time
    if max_turbines_per_string is not None:
        max_flow = max_turbines_per_string
    else:
        max_flow = grid.max_turbines_per_string

    flag = True

    # Bundle MIP / path-graph options in a small config object so that
    # we don't have to pass a long list of flags through every call.
    mip_cfg = MIPConfig(
        solver_name=MIP_solver,
        backend=backend,
        crossings=limit_crossings,
        tee=tee,
        callback=fs,
        MIP_gap=MIP_gap,
        min_turbines_per_string=min_turbines_per_string,
        fixed_substation_connections=fixed_substation_connections,
        t_MW=t_MW,
    )

    if tee:
        print(f'Starting sequential CSS for {grid.name}')

    while flag:
        timing_info = {}
        
        t1 = time.perf_counter()
        if sub_min_connections:
            if tee and i==0:
                print(f'Using min sub connections iterationfor sequential CSS')
            # Use the shared MIPConfig for internal calls
            flag, high_flow,model_MIP,feasible_solutions_MIP ,ns, sub_iter , path_time = min_sub_connections(
                grid, max_flow, mip_cfg=mip_cfg, max_ns=max_ns
            )
        else:
            if tee and i==0:
                print(f'Using user defined substation limit path graph for sequential CSS')
            flag, high_flow,model_MIP,feasible_solutions_MIP = MIP_path_graph(
                grid, max_flow, mip_cfg=mip_cfg,sub_k_max=max_ns
            )
            sub_iter = 1
        
        t2 = time.perf_counter()
        if tee:     
            print(f'Iteration {i} MIP finished in {t2 - t1} seconds')
        timing_info['Paths'] = t2 - t1
        seq_path_time += t2 - t1

        if not flag:
            if i == 0:
                # If MIP fails on first iteration, return None
                if tee:
                    print(f'MIP failed on first iteration, returning None')
                return None, None, None, None,i
            else:
                # If MIP fails on later iterations, break the loop
                if tee:
                    print(f'MIP failed on iteration {i}, breaking loop')
                break
        # Handle both Pyomo model and OR-Tools MockModel
        if hasattr(model_MIP, 'objective'):
            # Pyomo model
            MIP_obj_value = pyo.value(model_MIP.objective)
        elif hasattr(model_MIP, 'objective_value'):
            # OR-Tools MockModel – already unscaled in MockModel.__init__
            MIP_obj_value = model_MIP.objective_value
        else:
            raise AttributeError("model_MIP must have either 'objective' (Pyomo) or 'objective_value' (OR-Tools) attribute")
        if  high_flow < max_flow:
            
            max_power_per_string = t_MW*high_flow 
            first_index_to_comply = next((i for i, rating in enumerate(grid.Cable_options[0].MVA_ratings) if rating >= max_power_per_string), len(grid.Cable_options[0].MVA_ratings) - 1)
            for line in grid.lines_AC_ct:
                if line.active_config > 0:
                    line.active_config = first_index_to_comply

            grid.Cable_options[0].cable_types = grid.Cable_options[0]._cable_types[:first_index_to_comply + 1]
           
            grid.max_turbines_per_string = high_flow
        iter_cab_available= grid.Cable_options[0].cable_types.copy()
        if tee:
            print(f'DEBUG: Iteration {i} iter_cab_available: {iter_cab_available}')
        
        t3 = time.perf_counter()
        #print(f'DEBUG: Iteration {i}')
        if NL == 'OPF':
            from .Graph_and_plot import save_network_svg
            intermediate_dir = os.path.join(save_dir, 'intermediate_networks')
            os.makedirs(intermediate_dir, exist_ok=True)
            save_network_svg(grid, name=f'{intermediate_dir}/{svg}_{i}_preCSS', width=1000, height=1000, journal=True,square_ratio=True, legend=True)
        
        # OPF uses NL solver; False and PF both use linear CSS
        css_NL = (NL == 'OPF')
        model, model_results, timing_info_CSS, solver_stats = simple_CSS(grid,NPV,n_years,Hy,discount_rate,ObjRule,CSS_L_solver,CSS_NL_solver,time_limit,css_NL,tee,fs=fs)
        css_status_ok = model_results is not None and model_results['Solver'][0]['Status'] == 'ok'
        css_solution_found = solver_stats.get('solution_found', False) if solver_stats else False
        css_ok = css_status_ok or css_solution_found
        feasible_solutions_CSS = solver_stats.get('feasible_solutions', []) if solver_stats else []
        t4 = time.perf_counter()
        if tee:
            print(f'Iteration {i} CSS finished in {t4 - t3} seconds')
            if not css_status_ok and css_solution_found:
                tc = solver_stats.get('termination_condition', 'unknown') if solver_stats else 'unknown'
                print(f'  Warning: solver status not ok (termination: {tc}), but feasible solution found — using it')
        timing_info['CSS'] = t4 - t3
        seq_css_time += t4 - t3
        if svg is not None:
            if tee:
                print(f'Iteration {i} saving SVG')
            from .Graph_and_plot import save_network_svg
            CSS_solver = CSS_NL_solver if NL == 'OPF' else CSS_L_solver
            # Save SVG in the sequential_CSS folder
            intermediate_dir = os.path.join(save_dir, 'intermediate_networks')
            if not os.path.exists(intermediate_dir):
                os.makedirs(intermediate_dir)
            save_network_svg(grid, name=f'{intermediate_dir}/{svg}_{i}_{CSS_solver}', width=1000, height=1000, journal=True,square_ratio=True, legend=True)
        
        if css_ok:
            obj_value = pyo.value(model.obj)
        else:
            if tee:
                print(f'Iteration {i} CSS solver status not ok and no feasible solution found, skipping to next cable combo')
            obj_value = None

        
        
        #print('DEBUG: Iteration',i)

        used_cable_types = []
        used_cable_names = []
        
        # Analyze which cable types were used in the optimization
        if css_ok:
            # Get the cable types that were actually used
           
            for ct in model.ct_set:
                if pyo.value(model.ct_types[ct]) > 0.5:  # Binary variable > 0.5 means it was selected
                    used_cable_types.append(ct)
                    used_cable_names.append(grid.Cable_options[0].cable_types[ct])
            #print(f'DEBUG: Used cable types: {used_cable_types}')
            
            if used_cable_types:
                # Find the largest cable type that was used
                largest_used_index = max(used_cable_types)
              
                new_cables = new_cables[:largest_used_index]
                
            else:
                # No cable types were used, remove the largest one
                new_cables.pop()
               
        else:
            # Optimization failed, remove the largest cable type
            new_cables.pop()
           
        
       
        
        # Check if it's Pyomo or OR-Tools MockModel
        if hasattr(model_MIP, 'line_used') and hasattr(model_MIP, 'lines'):
            # Pyomo model
            cable_length = pyo.value(sum(model_MIP.line_used[line] * grid.lines_AC_ct[line].Length_km for line in model_MIP.lines))
            weighted_length = pyo.value(sum(model_MIP.line_used[line] * grid.lines_AC_ct[line].trench_lenght_km for line in model_MIP.lines))
        elif hasattr(model_MIP, 'line_used_vals'):
            # OR-Tools MockModel
            cable_length = sum(model_MIP.line_used_vals[line] * grid.lines_AC_ct[line].Length_km for line in model_MIP.line_used_vals.keys())
            weighted_length = sum(model_MIP.line_used_vals[line] * grid.lines_AC_ct[line].trench_lenght_km for line in model_MIP.line_used_vals.keys())

        else:
            raise AttributeError("model_MIP must have either Pyomo attributes ('line_used', 'lines') or OR-Tools attribute ('line_used_vals')")
        
        t5 = time.perf_counter()
        timing_info['processing'] = (t5 - t1)-(timing_info['Paths']+timing_info['CSS'])
        # Compute cable cost matching TEP_obj Array_investments()
        
               
        present_value_factor = Hy * (1 - (1 + discount_rate) ** -n_years) / discount_rate

        if obj_value is None:
            cable_cost = None
            loss_cost = None
            loss_MW = None
            opt_obj = None
            total_cost = None
        else:
            if NL == 'OPF':
                # OPF: losses from NL solver export
                loss_MW = sum(line.P_loss for line in grid.lines_AC_ct) * grid.S_base
                loss_cost = loss_MW * present_value_factor*grid.LCoE
                cable_cost = 0
                for line in grid.lines_AC_ct:
                    if line.active_config >= 0:
                        cable_cost += line.base_cost[line.active_config]
                opt_obj = MIP_obj_value + cable_cost + loss_cost
            elif NL == 'PF':
                # PF: post-processing power flow for losses, not in opt_obj
                from .ACDC_PF import Power_flow
                Power_flow(grid)
                loss_MW = sum(line.P_loss for line in grid.lines_AC_ct) * grid.S_base
                loss_cost = loss_MW * present_value_factor*grid.LCoE
                cable_cost = obj_value
                opt_obj = cable_cost + MIP_obj_value
            else:
                # Linear: no losses
                cable_cost = obj_value
                loss_cost = 0
                loss_MW = 0
                opt_obj = cable_cost + MIP_obj_value
            total_cost = MIP_obj_value + cable_cost + loss_cost
        # Create a dictionary for this iteration's results
        iteration_result = {
            'cable_length': cable_length,
            'weighted_length': weighted_length,
            'installation_cost': MIP_obj_value,
            'loss_MW': loss_MW,
            'cable_cost': cable_cost,
            'loss_cost': loss_cost,
            'total_cost': total_cost,  # Save the objective value
            'opt_obj': opt_obj,
            'cable_options': iter_cab_available,  # Save a copy of the cable list
            'cables_used': used_cable_names,
            'model_results': model_results,
            'solver_stats': solver_stats,
            'timing_info': timing_info,
            'MIP_model': model_MIP,
            'CSS_model': model,
            'sub_iter': sub_iter,
            'i': i,
            'css_ok': css_ok,
            'feasible_solutions_MIP': feasible_solutions_MIP,
            'feasible_solutions_CSS': feasible_solutions_CSS
        }
        results.append(iteration_result)  # Add to the results list   
        
        if i > 0 and opt_obj is not None and results[i-1]['opt_obj'] is not None:
            if opt_obj > results[i-1]['opt_obj']:
                if tee:
                    print(f'Iteration {i} objective value increased, breaking loop')
                break
        i += 1
        if i > max_iter:
            if tee:
                print(f'Iteration {i} max iterations reached, breaking loop')
            break
        # Update grid with new cable set
        if len(new_cables) > 0:
            grid.Cable_options[0].cable_types = new_cables
            
            # Recalculate max_flow based on current cable set
            max_cable_capacity = max(grid.Cable_options[0].MVA_ratings)
            max_flow = int(max_cable_capacity / t_MW)
            if tee:
                print(f'Iteration {i} max flow updated to {max_flow}')
        else:
            if tee:
                print(f'Iteration {i} no more cable types available, breaking loop')
            break
        if tee:
            print(f'Iteration {i} finished updating grid with new cable set')
    if tee:
        print(f'Sequential CSS finished in {time.perf_counter() - t0} seconds')
    # After the while loop ends, create summary from all iterations
    summary_results = {
        'cable_length': [result['cable_length'] for result in results],
        'weighted_length': [result['weighted_length'] for result in results],
        'loss_MW': [result['loss_MW'] for result in results],
        'installation_cost': [result['installation_cost'] for result in results],
        'cable_cost':    [result['cable_cost'] for result in results],
        'loss_cost':     [result['loss_cost'] for result in results],
        'total_cost':   [result['total_cost'] for result in results],
        'opt_obj':      [result['opt_obj'] for result in results],
        'cable_options': [result['cable_options'] for result in results],
        'cables_used':  [result['cables_used'] for result in results],
        'timing_info':  [result['timing_info'] for result in results],
        'solver_status':[result['model_results']['Solver'][0]['Status'] if result['model_results'] is not None else 'failed' for result in results],
        'iteration':    [result['i'] for result in results],
        'sub_iter':     [result['sub_iter'] for result in results],
        'feasible_solutions_MIP': [result['feasible_solutions_MIP'] for result in results],
        'feasible_solutions_CSS': [result['feasible_solutions_CSS'] for result in results]
    }

    # Find best result (only among iterations where optimization succeeded)
    valid_results = [r for r in results if r['opt_obj'] is not None]
    if len(valid_results) > 1:
        best_result = min(valid_results, key=lambda x: x['opt_obj'])
    elif len(valid_results) == 1:
        best_result = valid_results[0]
    else:
        best_result = results[0]  # All failed, return first
    

    if fs:
        feasible_solutions_MIP = [result['feasible_solutions_MIP'] for result in results]
        feasible_solutions_CSS = [result['feasible_solutions_CSS'] for result in results]
        # Save feasible solutions plot in the sequential_CSS folder
        feasible_sol_gap_path = os.path.join(save_dir, f'feasible_solutions_{grid.name}_gap.png')
        feasible_sol_obj_path = os.path.join(save_dir, f'feasible_solutions_{grid.name}_obj.png')
        _plot_feasible_solutions_subplots(
            feasible_solutions_MIP,
            feasible_solutions_CSS,
            show=False,
            save_path=feasible_sol_obj_path,
            type='obj'
        )
        _plot_feasible_solutions_subplots(
            feasible_solutions_MIP,
            feasible_solutions_CSS,
            show=False,
            save_path=feasible_sol_gap_path,
            type='gap'
        )
        # Export feasible solutions to Excel/CSV
        feasible_sol_excel_path = os.path.join(save_dir, f'feasible_solutions_{grid.name}.csv')
        _export_feasible_solutions_to_excel(
            feasible_solutions_MIP,
            feasible_solutions_CSS,
            save_path=feasible_sol_excel_path
        )

    
    

    model = best_result['CSS_model']
    model_MIP = best_result['MIP_model']
    model_results = best_result['model_results']
    tot_timing_info['Paths'] = seq_path_time
    tot_timing_info['CSS'] = seq_css_time
    solver_stats = best_result['solver_stats']
    best_i = best_result['i']

    t5 = time.perf_counter()

    # Restore original cable types BEFORE exporting results, so that
    # Ybus_list has all entries and active_config is not silently clamped
    # to a shorter list (which would cause wrong Ybus and wrong P_INJ).
    grid.Cable_options[0].cable_types = og_cable_types

    # Rebuild active_config from per-line selections (robust, no reliance on global state)
    used_types = set()
    for line in grid.lines_AC_ct:
        if line.active_config >= 0:
            used_types.add(line.active_config)
    grid.Cable_options[0].active_config = [1 if k in used_types else 0 for k in range(len(og_cable_types))]

    if NL == 'OPF':
        ExportACDC_NLmodel_toPyflowACDC(model, grid, PZ, TEP=True)
    else:
        ExportACDC_Lmodel_toPyflowACDC(model, grid, solver_results=model_results, tee=tee)


    present_value = Hy*(1 - (1 + discount_rate) ** -n_years) / discount_rate
    for obj in weights_def:
        weights_def[obj]['v']=calculate_objective(grid,obj,True)
        weights_def[obj]['NPV']=weights_def[obj]['v']*present_value

    grid.TEP_run=True
    grid.OPF_obj = weights_def

    t_modelexport = time.perf_counter() - t5
    tot_timing_info['export'] = t_modelexport
    tot_timing_info['sequential'] = t5 - t0

    models = (model_MIP,model)
    return models, summary_results , tot_timing_info, solver_stats,best_i
    


def min_sub_connections(grid, max_flow=None, solver_name='glpk', crossings=True, tee=False, max_ns=None,
                        callback=False, MIP_gap=None, backend='pyomo',
                        min_turbines_per_string=False, mip_cfg: MIPConfig | None = None,t_MW=None):
    # If a MIPConfig is provided, let it override the individual flags.
    if mip_cfg is not None:
        solver_name = mip_cfg.solver_name
        crossings = mip_cfg.crossings
        tee = mip_cfg.tee
        callback = mip_cfg.callback
        backend = mip_cfg.backend
        # Allow explicit function arguments to override the config where given
        if MIP_gap is None:
            MIP_gap = mip_cfg.MIP_gap
        if min_turbines_per_string is False and mip_cfg.min_turbines_per_string is not False:
            min_turbines_per_string = mip_cfg.min_turbines_per_string
        if t_MW is None:
            t_MW = mip_cfg.t_MW

    tn = grid.n_ren
    sn = grid.nn_AC - grid.n_ren

    ns = math.ceil(tn/(sn* max_flow))
    
    # If the minimum required ns already exceeds max_ns, the problem is infeasible
    if max_ns is not None and ns > max_ns:
        if tee:
            print(f'Infeasible: minimum ns={ns} exceeds max_ns={max_ns}')
        return False, None, None, None, ns, 0, 0.0

    flag=False
    i =0
    max_iters = 1 if ns is None else 10
    if tee:
        print(f'Starting min sub connections for {grid.name}')
    while not flag and i<max_iters:
        if tee:
            print(f'Iteration sub-{i} starting min sub connections')
            if min_turbines_per_string:
                min_t_s = math.floor(tn / (sn * ns))   
            else:
                min_t_s = min_turbines_per_string
            print(f'Connecting {tn} turbines to {sn} substations')    
            print(f'max connection to substations: {ns}, max turbines per connection: {max_flow}, min turbines per string: {min_t_s}')
        for node in grid.nodes_AC:
            if node.type == 'Slack':
                node.ct_limit = ns

        t0 = time.perf_counter()
        # Use MIP_path_graph with the same configuration; pass mip_cfg so
        # internal routing/solver options remain consistent.
        flag, high_flow,model_MIP,feasible_solutions_MIP = MIP_path_graph(
            grid,
            max_flow,
            solver_name,
            crossings,
            tee,
            callback,
            MIP_gap,
            backend,
            min_turbines_per_string=min_turbines_per_string,
            min_sub_connections=True,
            sub_k_max=ns,
            mip_cfg=mip_cfg,
        )
        t1 = time.perf_counter()
        path_time = t1 - t0
        i+=1
        if not flag:
            if ns is not None:
                if max_ns is not None and ns >= max_ns:
                    if tee:
                        print(f'Iteration sub-{i} ns increased to {ns} (max_ns reached), breaking loop')
                    break
                ns+=1
                
            if tee:
                print(f'Iteration sub-{i} ns increased to {ns}')

    if tee:
        print(f'Min sub connections finished in {time.perf_counter() - t0} seconds')
        print(f'Final ns: {ns}')
    return flag, high_flow,model_MIP,feasible_solutions_MIP ,ns, i , path_time


def simple_assign_cable_types(grid, model, t_MW=None):
    """Assign the smallest sufficient cable type to each active branch.

    For every line activated by the MIP solution (``line_used > 0.5``),
    compute the MW flow as ``abs(line_flow) * t_MW`` and pick the first
    cable type whose MVA rating can carry it.  Inactive lines get
    ``active_config = -1``.
    """
    import pyomo.environ as pyo
    if t_MW is None:
        t_MW = grid.RenSources[0].PGi_ren_base*grid.S_base
    cable_options = grid.Cable_options[0]
    ratings = cable_options.MVA_ratings

    for line in model.lines:
        ct_line = grid.lines_AC_ct[line]

        if pyo.value(model.line_used[line]) < 0.5:
            ct_line.active_config = -1
            continue

        mw_flow = abs(pyo.value(model.line_flow[line])) * t_MW

        selected = next(
            (i for i, r in enumerate(ratings) if r >= mw_flow),
            len(ratings) - 1,
        )
        ct_line.active_config = selected


def MIP_path_graph(grid, max_flow=None, solver_name='glpk', crossings=False, tee=False,
                   callback=False, MIP_gap=None, backend='pyomo',
                   enable_cable_types=False, t_MW=None, cab_types_allowed=None,
                   min_turbines_per_string=False, fixed_substation_connections=None,
                   min_sub_connections=False, sub_k_max=None,
                   mip_cfg: MIPConfig | None = None,
                   flow_dir_tightening='auto',
                   solver_options_override: dict | None = None):
    """
    Solve the master MIP problem and track feasible solutions over time.
    
    Parameters:
    -----------
    backend : str, optional
        Backend to use: 'pyomo' (default) or 'ortools'
        - 'pyomo': Uses Pyomo with external solver (GLPK, Gurobi, etc.)
        - 'ortools': Uses OR-Tools CP-SAT solver (built-in, faster)
    enable_cable_types : bool
        If True, enable individual cable type selection per line
    t_MW : float
        Turbine MW rating (needed to calculate flow capacity from MVA ratings)
    cab_types_allowed : int, optional
        Maximum number of cable types that can be used (linking constraint)
    
    Returns:
    --------
    success : bool
        True if solution found, False otherwise
    high_flow : float or None
        Maximum flow value in solution
    model : Pyomo model or MockModel
        Solved model object
    feasible_solutions : list
        List of (time, objective_value, gap) tuples if callback=True
    """
    # If a MIPConfig is provided, prefer its values unless explicitly overridden
    if mip_cfg is not None:
        solver_name = mip_cfg.solver_name
        backend = mip_cfg.backend
        crossings = mip_cfg.crossings
        tee = mip_cfg.tee
        callback = mip_cfg.callback
        if MIP_gap is None:
            MIP_gap = mip_cfg.MIP_gap
        if min_turbines_per_string is False and mip_cfg.min_turbines_per_string is not False:
            min_turbines_per_string = mip_cfg.min_turbines_per_string
        if fixed_substation_connections is None and mip_cfg.fixed_substation_connections is not None:
            fixed_substation_connections = mip_cfg.fixed_substation_connections
        if t_MW is None:
            t_MW = mip_cfg.t_MW
    if t_MW is None:
        t_MW = grid.RenSources[0].PGi_ren_base*grid.S_base
    # Route to appropriate backend
    if backend.lower() == 'ortools':
        if not ORTOOLS_AVAILABLE:
            raise ImportError(
                "OR-Tools is not installed. Please install it with: pip install ortools\n"
                "Alternatively, use backend='pyomo' (default) which uses Pyomo with external solvers."
            )
        return MIP_path_graph_ortools(grid, max_flow=max_flow, crossings=crossings, 
                                      tee=tee, callback=callback, MIP_gap=MIP_gap,
                                      enable_cable_types=enable_cable_types,
                                      t_MW=t_MW,
                                      cab_types_allowed=cab_types_allowed,
                                      min_turbines_per_string=min_turbines_per_string,
                                      fixed_substation_connections=fixed_substation_connections,
                                      min_sub_connections=min_sub_connections,
                                      sub_k_max=sub_k_max)
    elif backend.lower() != 'pyomo':
        raise ValueError(f"Unknown backend: {backend}. Must be 'pyomo' or 'ortools'")
    
    # Original Pyomo implementation
    model = _create_master_problem_pyomo(grid, crossings, max_flow, 
                                         enable_cable_types=enable_cable_types,
                                         t_MW=t_MW,
                                         cab_types_allowed=cab_types_allowed,
                                         min_turbines_per_string=min_turbines_per_string,
                                         fixed_substation_connections=fixed_substation_connections,
                                         min_sub_connections=min_sub_connections,
                                         sub_k_max=sub_k_max,
                                         flow_dir_tightening=flow_dir_tightening)
    # Build solver options based on solver and grid attributes
    solver_options = {}
    time_limit = getattr(grid, "MIP_time", None)
    
    if solver_name == 'gurobi':
        mip_focus = getattr(grid, "MIP_focus", 2)
        solver_options = {
            'MIPFocus': mip_focus,
            'Cuts': 2,
            'Heuristics': 0.05,
            'Presolve': 2,
        }
        if MIP_gap is not None:
            solver_options['MIPGap'] = MIP_gap
    elif solver_name == 'cbc':
        if MIP_gap is not None:
            solver_options['ratioGap'] = MIP_gap
    elif solver_name == 'highs':
        if MIP_gap is not None:
            solver_options['mip_rel_gap'] = MIP_gap
    
    if solver_options_override is not None:
        solver_options.update(solver_options_override)
    
    # Use pyomo_model_solve to handle all solver logic
    results, solver_stats = pyomo_model_solve(
        model,
        grid=None,  # Not needed for MIP
        solver=solver_name,
        tee=tee,
        time_limit=time_limit,
        callback=callback,
        solver_options=solver_options if solver_options else None,
        objective_name='objective',  # MIP model uses 'objective'
        suppress_warnings=True  # Suppress warnings for MIP failures
    )
    
    # Extract results
    feasible_solutions = solver_stats['feasible_solutions'] if solver_stats else []
    feasible_solution_found = solver_stats['solution_found'] if solver_stats else False
    high_flow = None

    # === Post-solve handling ===
    if feasible_solution_found:
        flows = [abs(pyo.value(model.line_flow[line])) for line in model.lines]
        high_flow = max(flows) if flows else 0
        
        # Assign cable types to lines
        for line in model.lines:
            ct_line = grid.lines_AC_ct[line]
            line_used = pyo.value(model.line_used[line]) > 0.5
            
            if not line_used:
                ct_line.active_config = -1
            elif enable_cable_types and hasattr(model, 'ct_branch'):
                # Read selected cable type from ct_branch
                selected_ct = None
                for ct in model.ct_set:
                    if pyo.value(model.ct_branch[line, ct]) > 0.5:
                        selected_ct = ct
                        break
                if selected_ct is not None:
                    ct_line.active_config = selected_ct
                else:
                    # Fallback: use last cable type if no selection found
                    last_cable_type_index = len(grid.Cable_options[0]._cable_types) - 1
                    ct_line.active_config = last_cable_type_index
            else:
                # No cable type selection: calculate minimum required cable type if t_MW is available
                if t_MW is not None:
                    # Calculate MW flow for this line: flow in turbines * MW per turbine
                    flow_turbines = abs(pyo.value(model.line_flow[line]))
                    mw_flow = flow_turbines * t_MW
                    
                    # Find minimum cable type that can handle this MW flow
                    cable_options = grid.Cable_options[0]
                    selected_ct = None
                    # Cable types are sorted by capacity (smallest to largest)
                    for ct_idx in range(len(cable_options._cable_types)):
                        mva_rating = cable_options.MVA_ratings[ct_idx]
                        if mva_rating >= mw_flow:
                            selected_ct = ct_idx
                            break
                    
                    # If no cable type can handle the flow, use the largest one
                    if selected_ct is None:
                        selected_ct = len(cable_options._cable_types) - 1
                    
                    ct_line.active_config = selected_ct
                else:
                    # Fallback: use last cable type as default
                    last_cable_type_index = len(grid.Cable_options[0]._cable_types) - 1 if grid.Cable_options and len(grid.Cable_options) > 0 else -1
                    ct_line.active_config = last_cable_type_index

        model._solver_stats = solver_stats
        return True, high_flow, model, feasible_solutions

    else:
        print("✗ MIP model failed")
        return False, None, None, feasible_solutions

def MIP_path_graph_ortools(grid, max_flow=None, crossings=False, tee=False, callback=False, MIP_gap=None, enable_cable_types=False, t_MW=None, cab_types_allowed=None, min_turbines_per_string=False, fixed_substation_connections=None,min_sub_connections=False,sub_k_max=None, flow_dir_tightening='auto'):
    """Solve the master MIP problem using OR-Tools CP-SAT solver."""
    if not ORTOOLS_AVAILABLE:
        raise ImportError(
            "OR-Tools is not installed. Please install it with: pip install ortools"
        )
    length_scale = 1000
    from ortools.sat.python import cp_model
    
    # Create model (calculation will be done inside _create_master_problem_ortools)
    model, vars_dict = _create_master_problem_ortools(grid, crossings, max_flow, min_turbines_per_string, length_scale, 
                                                       enable_cable_types, t_MW, cab_types_allowed, fixed_substation_connections,min_sub_connections,sub_k_max,
                                                       flow_dir_tightening=flow_dir_tightening)
    
    feasible_solutions = []
    feasible_solution_found = False
    high_flow = None
    
    # Create solver
    solver = cp_model.CpSolver()
    
    # Set solver parameters
    if tee:
        solver.parameters.log_search_progress = True
    
    # Set time limit if specified
    if hasattr(grid, "MIP_time") and grid.MIP_time is not None:
        solver.parameters.max_time_in_seconds = grid.MIP_time
    
    # Set MIP gap if specified (CP-SAT uses relative gap)
    if MIP_gap is not None:
        solver.parameters.relative_gap_limit = MIP_gap
    
    # Callback for tracking feasible solutions (if requested)
    if callback:
        class SolutionCallback(cp_model.CpSolverSolutionCallback):
            def __init__(self, vars_dict, feasible_solutions):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.vars_dict = vars_dict
                self.feasible_solutions = feasible_solutions
                self.solution_count = 0
            
            def on_solution_callback(self):
                self.solution_count += 1
                runtime = self.WallTime()
                objective = self.ObjectiveValue()
                
                # Try to get bound if available (CP-SAT may not provide in callback)
                try:
                    bound = self.BestObjectiveBound()
                except:
                    bound = None
                
                # Calculate relative gap
                relgap = None
                if bound is not None and objective is not None and abs(objective) > 1e-10:
                    relgap = 1.0 - bound / objective
                
                # Store as tuple for compatibility: (time, objective, gap)
                self.feasible_solutions.append((runtime, objective, relgap))
        
        callback_obj = SolutionCallback(vars_dict, feasible_solutions)
        status = solver.Solve(model, callback_obj)
    else:
        status = solver.Solve(model)
    
    # Check solution status
    if status == cp_model.OPTIMAL:
        feasible_solution_found = True
    elif status == cp_model.FEASIBLE:
        feasible_solution_found = True
    elif status == cp_model.INFEASIBLE:
        feasible_solution_found = False
    elif status == cp_model.MODEL_INVALID:
        feasible_solution_found = False
    else:
        # TIMEOUT or other status - check if we have a solution by checking objective value
        # CP-SAT returns a very large value if no solution found
        try:
            obj_val = solver.ObjectiveValue()
            # If objective is reasonable (not infinity), we have a solution
            feasible_solution_found = obj_val < 1e20
        except:
            feasible_solution_found = False
    
    # Post-solve handling
    if feasible_solution_found:
        # Extract solution values
        line_used_vals = {}
        line_flow_vals = {}
        
        for l in vars_dict["line_used"]:
            line_used_vals[l] = solver.Value(vars_dict["line_used"][l])
            line_flow_vals[l] = solver.Value(vars_dict["line_flow"][l])
        
        # Calculate high flow
        flows = [abs(line_flow_vals[l]) for l in line_flow_vals]
        high_flow = max(flows) if flows else 0
        
        # Update grid with solution
        for l in line_used_vals:
            ct_line = grid.lines_AC_ct[l]
            if line_used_vals[l] > 0:
                if enable_cable_types and "ct_branch" in vars_dict:
                    # Read selected cable type from ct_branch
                    selected_ct = None
                    for ct in vars_dict["ct_set"]:
                        if solver.Value(vars_dict["ct_branch"][(l, ct)]) > 0:
                            selected_ct = ct
                            break
                    if selected_ct is not None:
                        ct_line.active_config = selected_ct
                    else:
                        # Fallback: use last cable type if no selection found
                        last_cable_type_index = len(grid.Cable_options[0]._cable_types) - 1
                        ct_line.active_config = last_cable_type_index
                else:
                    # Calculate MW flow for this line
                    flow_turbines = abs(line_flow_vals[l])
                    
                    if t_MW is not None:
                        # Calculate MW flow: flow in turbines * MW per turbine
                        mw_flow = flow_turbines * t_MW
                        
                        # Find minimum cable type that can handle this MW flow
                        cable_options = grid.Cable_options[0]
                        selected_ct = None
                        
                        # Cable types are sorted by capacity (smallest to largest)
                        for ct_idx in range(len(cable_options._cable_types)):
                            mva_rating = cable_options.MVA_ratings[ct_idx]
                            if mva_rating >= mw_flow:
                                selected_ct = ct_idx
                                break
                        
                        # If no cable type can handle the flow, use the largest one
                        if selected_ct is None:
                            selected_ct = len(cable_options._cable_types) - 1
                        
                        ct_line.active_config = selected_ct
                    
                    else:
                        # Fallback: use last cable type if t_MW not available
                        last_cable_type_index = len(grid.Cable_options[0]._cable_types) - 1 if grid.Cable_options and len(grid.Cable_options) > 0 else -1
                        ct_line.active_config = last_cable_type_index
            else:
                ct_line.active_config = -1
        
        # Create SolutionInfo for final solution
        objective = solver.ObjectiveValue()
        runtime = solver.WallTime()
        
        # Get bound if available
        try:
            bound = solver.BestObjectiveBound()
        except:
            bound = None
        
        # Calculate relative gap
        relgap = None
        if bound is not None and objective is not None and abs(objective) > 1e-10:
            relgap = 1.0 - bound / objective
        elif status == cp_model.OPTIMAL:
            relgap = 0.0  # Optimal means gap is 0
        
        # Get termination status name
        termination_map = {
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE',
            cp_model.MODEL_INVALID: 'MODEL_INVALID',
            cp_model.UNKNOWN: 'UNKNOWN'
        }
        termination = termination_map.get(status, 'UNKNOWN')
    
        # Add final solution to feasible_solutions if callback was used
        if callback:
            # Store as tuple for compatibility: (time, objective, gap)
            feasible_solutions.append((runtime, objective, relgap))
        
        # Create a mock model-like object for compatibility with Pyomo version
        class MockModel:
            def __init__(self, vars_dict, line_used_vals, line_flow_vals, objective_value, length_scale):
                self.vars_dict = vars_dict
                self.line_used_vals = line_used_vals
                self.line_flow_vals = line_flow_vals
                self.objective_value = objective_value / length_scale
                self.length_scale = length_scale
             
        
        mock_model = MockModel(vars_dict, line_used_vals, line_flow_vals, objective, length_scale)
        
        return True, high_flow, mock_model, feasible_solutions
    else:
        print("✗ MIP model failed (OR-Tools)")
        return False, None, None, feasible_solutions


def _prepare_capacity_and_min_turbines(grid, max_flow=None, min_turbines_per_string=False,
                                       enable_cable_types=False, t_MW=None, num_nodes=None,
                                       fixed_substation_connections=None,min_sub_connections=False,sub_k_max=None):
    """
    Helper function to prepare capacity calculations and min_turbines_per_string.
    
    This function extracts common logic for:
    - Calculating cable type flow capacities
    - Determining max_ct_flow (max cable capacity or max_flow)
    - Calculating min_turbines_per_string based on grid topology
    - Performing feasibility checks
    - Handling fixed_substation_connections
    
    Parameters:
    -----------
    grid : Grid object
        The grid to analyze
    max_flow : int, optional
        Maximum flow per connection. If None, defaults to num_nodes - 1
    min_turbines_per_string : bool or int, optional
        Minimum turbines per string constraint (default: False):
        - False: Set to 1 (minimum constraint)
        - True: Calculate automatically based on grid topology
        - int: Use the specified value directly
    enable_cable_types : bool, optional
        If True, enable cable type capacity calculations
    t_MW : float, optional
        Turbine MW rating (needed when enable_cable_types=True)
    num_nodes : int, optional
        Number of nodes in the grid. If None, uses len(grid.nodes_AC)
    fixed_substation_connections : int, optional
        If provided, sets ct_limit for all slack nodes and performs feasibility check
    
    Returns:
    --------
    min_turbines_per_string : int
        The calculated or provided min_turbines_per_string value
    max_ct_flow : int
        The capacity to use for calculations (max cable capacity or max_flow)
    ct_flow_capacity : dict
        Dictionary mapping cable type indices to flow capacities (empty if not enabled)
    nT : int
        Number of turbines (non-sink nodes)
    nS : int
        Number of substations (sink nodes)
    """
    # Validate inputs
    ct_flow_capacity = {}
    if enable_cable_types:
        if grid.Cable_options is None or len(grid.Cable_options) == 0:
            raise ValueError("enable_cable_types=True but no Cable_options found in grid")
        if t_MW is None:
            raise ValueError("t_MW must be provided when enable_cable_types=True")
        
        # Calculate flow capacity for each cable type (in turbine units)
        # Flow capacity = int(MVA_rating / t_MW)
        ct_set_temp = list(range(len(grid.Cable_options[0]._cable_types)))
        for ct in ct_set_temp:
            mva_rating = grid.Cable_options[0].MVA_ratings[ct]
            ct_flow_capacity[ct] = int(mva_rating / t_MW)
    
    if enable_cable_types and ct_flow_capacity:
        max_ct_flow = max(ct_flow_capacity.values())
        min_ct_flow = min(ct_flow_capacity.values())
    else:
        max_ct_flow = max_flow
        min_ct_flow = max_flow

    if min_turbines_per_string is True:
        if max_ct_flow is None:
            raise ValueError("max_flow must be provided when min_turbines_per_string=True")
    
    # Set default max_flow
    if num_nodes is None:
        num_nodes = len(grid.nodes_AC)
    if max_flow is None:
        max_flow = num_nodes - 1
    
    # Initialize cable type capacities (if enabled) - needed for capacity calculation
    
    
    
    
    # Calculate nT and nS
    nT = len([n for n in grid.nodes_AC if n not in grid.slack_nodes])
    nS = len(grid.slack_nodes)
    
    # Handle min_turbines_per_string: can be bool or int, default is False
    if min_turbines_per_string is False:
        min_turbines_per_string = 1
    elif min_turbines_per_string is True:
        if min_sub_connections is False:
            # Calculate using formula - use max_ct_flow instead of max_flow
            min_s_connections = math.ceil(nT / (nS * min_ct_flow))
            min_turbines_per_string = math.floor(nT / (nS * min_s_connections))
        else:
            max_s_connections = sub_k_max
            min_turbines_per_string = math.floor(nT / (nS * max_s_connections))   
    # If it's an int, validate and correct if needed
    elif isinstance(min_turbines_per_string, int):
        # If provided value is greater than capacity, recalculate
        if min_turbines_per_string > max_ct_flow:
            print(f"min_turbines_per_string {min_turbines_per_string} must be less than capacity {max_ct_flow}")
            min_s_connections = math.ceil(nT / (nS * max_ct_flow))
            min_turbines_per_string = math.floor(nT / (nS * min_s_connections))
    
    # Get slack nodes (handle both direct access and getattr for compatibility)
    if hasattr(grid, 'slack_nodes'):
        slack_nodes = grid.slack_nodes
    else:
        slack_nodes = [n for n in grid.nodes_AC if getattr(n, "type", None) == "Slack"]
    
    # Feasibility check: only valid if ALL substations have ct_limit defined
    # If any substation has ct_limit = None, it has unlimited connections, so check is invalid
    slack_nodes_with_limit = [node for node in slack_nodes 
                              if getattr(node, "ct_limit", None) is not None]
    all_slack_have_limit = len(slack_nodes_with_limit) == len(slack_nodes) if slack_nodes else False
    
    if all_slack_have_limit and len(slack_nodes_with_limit) > 0:
        # All substations have an explicit connection limit -> we can perform
        # a meaningful global feasibility check.

        # Two necessary conditions for feasibility:
        #   1) Minimum-turbines constraint must not exceed the number of turbines:
        #        min_turbines_per_string * min_s_conn <= nT
        #   2) Total capacity must be able to host all turbines:
        #        max_ct_flow * max_s_conn >= nT
        max_s_conn = sum(getattr(node, "ct_limit") for node in slack_nodes_with_limit)
        min_s_conn = math.ceil(nT / (nS * min_ct_flow))

        # Condition 1: lower bound from min_turbines_per_string
        min_required_turbines = min_turbines_per_string * min_s_conn
        if min_required_turbines > nT:
            raise ValueError(
                f"Not feasible to connect {nT} turbines with {nS} substations, "
                f"{min_s_conn} total connections, and minimum "
                f"{min_turbines_per_string} turbines per connection. "
                f"Minimum required: {min_required_turbines} > {nT} turbines. "
                f"Decrease min_turbines_per_string or increase connections."
            )

        # Condition 2: upper bound from connection capacity
        max_total_capacity = max_ct_flow * max_s_conn
        if max_total_capacity < nT:
            raise ValueError(
                f"Not feasible to connect {nT} turbines with {nS} substations, "
                f"{max_s_conn} total connections, and maximum "
                f"{max_ct_flow} turbines per connection. "
                f"Total capacity: {max_total_capacity} < {nT} turbines. "
                f"Increase connections or cable capacity."
            )
    
    # Handle fixed_substation_connections
    if fixed_substation_connections is not None:
        # Recalculate min_turbines_per_string based on fixed connections
        min_turbines_per_string = math.floor(nT / (nS * fixed_substation_connections))
        
        # Set ct_limit for all slack nodes
        for node in slack_nodes:
            node.ct_limit = fixed_substation_connections
        
        # Feasibility check: total maximum capacity must be >= number of turbines
        # Each substation has fixed_substation_connections connections
        total_max_capacity = max_ct_flow * fixed_substation_connections * nS
        if total_max_capacity < nT:
            raise ValueError(
                f"Not feasible to connect {nT} turbines with {nS} substations, "
                f"{fixed_substation_connections} connections per substation, "
                f"and max flow of {max_ct_flow} per connection. "
                f"Total capacity: {total_max_capacity} < {nT} turbines"
            )
    
    return min_turbines_per_string, max_ct_flow, ct_flow_capacity, nT, nS


def _create_master_problem_pyomo(grid,crossings=True, max_flow=None, 
                                  enable_cable_types=False, 
                                  t_MW=None,
                                  cab_types_allowed=None,
                                  min_turbines_per_string=False,
                                  fixed_substation_connections=None,
                                  min_sub_connections=False,
                                  sub_k_max=None,
                                  flow_dir_tightening='auto'):
        """Create master problem using Pyomo
        
        Parameters:
        -----------
        enable_cable_types : bool
            If True, enable individual cable type selection per line
        t_MW : float
            Turbine MW rating (needed to calculate flow capacity from MVA ratings)
        cab_types_allowed : int, optional
            Maximum number of cable types that can be used (linking constraint)
        min_turbines_per_string : bool or int, optional
            Minimum turbines per string constraint (default: False):
            - False: Set to 1 (minimum constraint)
            - True: Calculate automatically based on grid topology
            - int: Use the specified value directly
        flow_dir_tightening : bool or 'auto'
            Add auxiliary line_flow_dir binary + big-M constraints that tighten
            the LP relaxation.  'auto' (default) enables when the number of
            crossing groups >= 3000.
        """
        if flow_dir_tightening == 'auto':
            n_crossings = len(grid.crossing_groups) if hasattr(grid, 'crossing_groups') and grid.crossing_groups else 0
            flow_dir_tightening = n_crossings >= 3000
        min_turbines_per_string, max_ct_flow, ct_flow_capacity, nT, nS = _prepare_capacity_and_min_turbines(
            grid, max_flow=max_flow, min_turbines_per_string=min_turbines_per_string,
            enable_cable_types=enable_cable_types, t_MW=t_MW, num_nodes=len(grid.nodes_AC),
            fixed_substation_connections=fixed_substation_connections, 
            min_sub_connections=min_sub_connections,
            sub_k_max=sub_k_max
        )
        
        model = pyo.ConcreteModel()
        model.lines = pyo.Set(initialize=range(len(grid.lines_AC_ct)))
        model.nodes = pyo.Set(initialize=range(len(grid.nodes_AC)))
        
        sink_nodes = []
        source_nodes = []
        for node in model.nodes:
            nAC = grid.nodes_AC[node]
            if nAC.connected_gen:
                sink_nodes.append(node)
            if nAC.connected_RenSource:
                source_nodes.append(node)
        
        if not sink_nodes:
            raise ValueError("No generator nodes found!")
        
        model.source_nodes = pyo.Set(initialize=source_nodes)
        model.sink_nodes = pyo.Set(initialize=sink_nodes)
        
        model.line_used = pyo.Var(model.lines, domain=pyo.Binary)
        if enable_cable_types:
            if grid.Cable_options is None or len(grid.Cable_options) == 0:
                raise ValueError("enable_cable_types=True but no Cable_options found in grid")
            if t_MW is None:
                raise ValueError("t_MW must be provided when enable_cable_types=True")
            
            # Cable type set
            model.ct_set = pyo.Set(initialize=range(len(grid.Cable_options[0]._cable_types)))
            
            # Calculate flow capacity for each cable type (in turbine units)
            # Flow capacity = int(MVA_rating / t_MW)
            ct_flow_capacity = {}
            for ct in model.ct_set:
                mva_rating = grid.Cable_options[0].MVA_ratings[ct]
                ct_flow_capacity[ct] = int(mva_rating / t_MW)
            model.ct_flow_capacity = pyo.Param(model.ct_set, initialize=ct_flow_capacity)
            
            model.ct_branch = pyo.Var(model.lines, model.ct_set, domain=pyo.Binary)
            model.ct_types = pyo.Var(model.ct_set, domain=pyo.Binary)
        
        def line_flow_bounds(model, line):
            line_obj = grid.lines_AC_ct[line]
            from_node = line_obj.fromNode
            to_node = line_obj.toNode
            from_is_slack = from_node.type == 'Slack'
            to_is_slack = to_node.type == 'Slack'
            
            if enable_cable_types:
                if to_is_slack and not from_is_slack:
                    return (0, max_ct_flow)
                elif from_is_slack and not to_is_slack:
                    return (-max_ct_flow, 0)
                else:
                    return (-(max_ct_flow - 1), max_ct_flow - 1)
            else:
                if to_is_slack and not from_is_slack:
                    return (0, max_flow)
                elif from_is_slack and not to_is_slack:
                    return (-max_flow, 0)
                else:
                    # If line connects PQ-PQ (turbine-turbine) or both slack: use reduced capacity
                    return (-(max_flow - 1), max_flow - 1)
        
        # Flow variables (integer - can carry flow in either direction)
        model.line_flow = pyo.Var(model.lines, domain=pyo.Integers, bounds=line_flow_bounds)

        def _node_flow_expr(model, node):
            nf = 0
            for line in model.lines:
                line_obj = grid.lines_AC_ct[line]
                if line_obj.fromNode.nodeNumber == node:
                    nf += model.line_flow[line]
                elif line_obj.toNode.nodeNumber == node:
                    nf -= model.line_flow[line]
            return nf
        model.node_flow = pyo.Expression(model.nodes, rule=_node_flow_expr)
        # Objective: minimize total cable length (+ optional investment cost)
        def objective_rule(model):
            installation_cost = sum(model.line_used[line] * grid.lines_AC_ct[line].installation_cost  for line in model.lines)
            if enable_cable_types:
                # Add cable type investment costs
                cable_type_cost = 0
                for line in model.lines:
                    line_obj = grid.lines_AC_ct[line]
                    for ct in model.ct_set:
                        cable_type_cost += model.ct_branch[line, ct] * line_obj.base_cost[ct]
                return installation_cost + cable_type_cost
            else:
                return installation_cost
        
        model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
        
        # Spanning tree constraint: exactly numNodes-1 connections
        def spanning_tree_rule(model):
            return sum(model.line_used[line] for line in model.lines) == len(model.nodes) - len(model.sink_nodes)
     
        
        model.spanning_tree = pyo.Constraint(rule=spanning_tree_rule)
        
        # Constrain connections 
        def connections_rule(model, node):
            if  grid.nodes_AC[node].ct_limit is None:
                    return pyo.Constraint.Skip
            else:
                node_connections = sum(model.line_used[line] 
                                     for line in model.lines
                                     if (grid.lines_AC_ct[line].fromNode.nodeNumber == node or 
                                         grid.lines_AC_ct[line].toNode.nodeNumber == node))
                return node_connections <= grid.nodes_AC[node].ct_limit
                
        nT= len(model.nodes) - len(model.sink_nodes)
        nS = len(model.sink_nodes)

        def connections_rule_lower(model, node):
            node_connections = sum(model.line_used[line] 
                            for line in model.lines
                            if (grid.lines_AC_ct[line].fromNode.nodeNumber == node or 
                                grid.lines_AC_ct[line].toNode.nodeNumber == node))
        
            # If node is a sink (substation), calculate minimum connections needed
            if node in model.sink_nodes:
                # Calculate minimum connections per sink based on capacity
                # Formula: ceil((non_sink_nodes) / (total_sink_capacity))
                if fixed_substation_connections is not None:
                    min_connections = fixed_substation_connections
                
                elif enable_cable_types:
                    min_connections = math.ceil(nT/(nS*max_ct_flow))
                    
                else:
                    min_connections = math.ceil(nT/(nS*max_flow))
                return node_connections >= min_connections
            else:
                # For non-sink nodes, minimum is 1
                return node_connections >= 1

        model.connections_rule = pyo.Constraint(model.nodes, rule=connections_rule)
        model.connect_lower = pyo.Constraint(model.nodes, rule= connections_rule_lower)




        def source_node_rule(model, node):
            return model.node_flow[node] == 1
            
        model.source_node = pyo.Constraint(model.source_nodes, rule=source_node_rule)

     
        def sink_absorption_rule(model):
            return sum(model.node_flow[n] for n in model.sink_nodes) == -len(model.source_nodes)
        model.total_sink_absorption = pyo.Constraint(rule=sink_absorption_rule)
        
        def sink_power_limit_rule(model, node):
            pu_limit = grid.nodes_AC[node].pu_power_limit
            # Check for None, NaN, or non-finite values
            if pu_limit is None:
                return pyo.Constraint.Skip
            # Check if it's a number and if it's finite (not NaN, not inf)
            if isinstance(pu_limit, (int, float)) and (math.isnan(pu_limit) or not math.isfinite(pu_limit)):
                return pyo.Constraint.Skip
            return model.node_flow[node] >= -pu_limit
        
        # Only create constraint if at least one node has a valid (non-None, finite) pu_power_limit
        def is_valid_pu_limit(node):
            pu_limit = grid.nodes_AC[node].pu_power_limit
            if pu_limit is None:
                return False
            if isinstance(pu_limit, (int, float)):
                return not (math.isnan(pu_limit) or not math.isfinite(pu_limit))
            return True
        
        if any(is_valid_pu_limit(node) for node in model.sink_nodes):
            model.sink_power_limit = pyo.Constraint(model.sink_nodes, rule=sink_power_limit_rule)

        # Intermediate nodes: net flow = 0 (conservation)
        def intermediate_node_rule(model, node):
            if node not in model.source_nodes and node not in model.sink_nodes:
                return model.node_flow[node] == 0
            else:
                return pyo.Constraint.Skip
        
        model.intermediate_node = pyo.Constraint(model.nodes, rule=intermediate_node_rule)
        
        # Link flow to investment: can only use lines we invest in
        if enable_cable_types:
            # Flow capacity linked to selected cable type
            def flow_capacity_upper_rule(model, line):
                # Flow <= sum(flow_capacity[ct] * ct_branch[line, ct])
                return model.line_flow[line] <= sum(model.ct_flow_capacity[ct] * model.ct_branch[line, ct] 
                                                   for ct in model.ct_set)
            
            def flow_capacity_lower_rule(model, line):
                # Flow >= -sum(flow_capacity[line, ct] * ct_branch[line, ct])
                return model.line_flow[line] >= -sum(model.ct_flow_capacity[ct] * model.ct_branch[line, ct] 
                                                    for ct in model.ct_set)
            
            # Cable type selection: each used line must have exactly one cable type
            # CONSTRAINT LINKING line_used and ct_branch:
            # sum(ct_branch[line, ct]) == line_used[line]
            # - If line_used[line] = 1: exactly one ct_branch[line, ct] = 1 (one cable type selected)
            # - If line_used[line] = 0: all ct_branch[line, ct] = 0 (no cable type selected)
            def cable_type_selection_rule(model, line):
                return sum(model.ct_branch[line, ct] for ct in model.ct_set) == model.line_used[line]
            
            model.flow_capacity_upper = pyo.Constraint(model.lines, rule=flow_capacity_upper_rule)
            model.flow_capacity_lower = pyo.Constraint(model.lines, rule=flow_capacity_lower_rule)
            model.cable_type_selection = pyo.Constraint(model.lines, rule=cable_type_selection_rule)
            
            # Link ct_types to ct_branch using homogeneity constraint from image formulation
            # Constraint: sum(ct_branch[line, ct]) - (NN-1) * ct_types[ct] <= 0
            # Which is: sum(ct_branch[line, ct]) <= (NN-1) * ct_types[ct]
            # Where NN-1 = len(nodes) - len(sink_nodes) (spanning tree has exactly this many lines)
            # This constraint enforces BOTH directions:
            # - If ct_types[ct] = 0: then sum(ct_branch) <= 0, so no lines use ct
            # - If sum(ct_branch) > 0 (any line uses ct): then ct_types[ct] must be 1
            #   (because if ct_types[ct] = 0, we'd have sum(ct_branch) <= 0, contradiction)
            # So the lower bound constraint is NOT needed - homogeneity constraint is sufficient!
            NN_minus_1 = len(model.nodes) - len(model.sink_nodes)  # Number of lines in spanning tree
            
            def ct_types_homogeneity_rule(model, ct):
                # Image formulation: sum X_i,j,k - (NN-1) * Z_k <= 0
                return sum(model.ct_branch[line, ct] for line in model.lines) - NN_minus_1 * model.ct_types[ct] <= 0
            
            model.ct_types_homogeneity = pyo.Constraint(model.ct_set, rule=ct_types_homogeneity_rule)
            
            # Optional: Limit total cable types used (linking constraint)
            if cab_types_allowed is not None:
                def ct_limit_rule(model):
                    return sum(model.ct_types[ct] for ct in model.ct_set) <= cab_types_allowed
                model.ct_limit = pyo.Constraint(rule=ct_limit_rule)
        else:
            # Original flow constraints (no cable type selection)
            def flow_investment_rule(model, line):
                return model.line_flow[line] <= max_flow * model.line_used[line]

            def flow_investment_rule_2(model, line):
                return model.line_flow[line] >= -max_flow * model.line_used[line]
            
            model.flow_investment_link = pyo.Constraint(model.lines, rule=flow_investment_rule)
            model.flow_investment_link_2 = pyo.Constraint(model.lines, rule=flow_investment_rule_2)

        # line_flow_dir: auxiliary binary for flow direction.
        # Theoretically redundant (spanning tree implies nonzero flow on every
        # bridge), but these big-M constraints tighten the LP relaxation
        # dramatically and are essential for solver performance.
        if flow_dir_tightening:
            model.line_flow_dir = pyo.Var(model.lines, domain=pyo.Binary)

            def flow_nonzero_positive(model, line):
                line_obj = grid.lines_AC_ct[line]
                to_is_slack = line_obj.toNode.type == 'Slack'
                min_flow = min_turbines_per_string if to_is_slack else 1
                if enable_cable_types:
                    M = max_ct_flow + 1
                else:
                    M = max_flow + 1
                return model.line_flow[line] >= min_flow - M * (1 - model.line_used[line]) - M * (1 - model.line_flow_dir[line])

            def flow_nonzero_negative(model, line):
                line_obj = grid.lines_AC_ct[line]
                from_is_slack = line_obj.fromNode.type == 'Slack'
                min_flow = min_turbines_per_string if from_is_slack else 1
                if enable_cable_types:
                    M = max_ct_flow + 1
                else:
                    M = max_flow + 1
                return model.line_flow[line] <= -min_flow + M * (1 - model.line_used[line]) + M * model.line_flow_dir[line]

            def flow_dir_active(model, line):
                return model.line_flow_dir[line] <= model.line_used[line]

            model.flow_nonzero_pos = pyo.Constraint(model.lines, rule=flow_nonzero_positive)
            model.flow_nonzero_neg = pyo.Constraint(model.lines, rule=flow_nonzero_negative)
            model.flow_dir_active = pyo.Constraint(model.lines, rule=flow_dir_active)



        # Add crossing constraints if crossings=True
        if crossings and hasattr(grid, 'crossing_groups') and grid.crossing_groups:
            # Create a set for crossing groups
            model.crossing_groups = pyo.Set(initialize=range(len(grid.crossing_groups)))
            
            # Constraint: for each crossing group, only one line can be active
            def crossing_constraint_rule(model, group_idx):
                group = grid.crossing_groups[group_idx]
                # Sum of all line_used variables in this crossing group must be <= 1
                return sum(model.line_used[line] for line in model.lines 
                          if grid.lines_AC_ct[line].lineNumber in group) <= 1
            
            model.crossing_constraints = pyo.Constraint(model.crossing_groups, rule=crossing_constraint_rule)
            
        return model
    




def _create_master_problem_ortools(grid, crossings=True, max_flow=None, min_turbines_per_string=False, length_scale=1000,
                                   enable_cable_types=False, t_MW=None, cab_types_allowed=None, fixed_substation_connections=None,min_sub_connections=False,sub_k_max=None,
                                   flow_dir_tightening='auto'):
    """
    OR-Tools version of _create_master_problem_pyomo(grid, crossings=True, max_flow=None)

    Returns:
        model: cp_model.CpModel
        vars_dict: {
            "line_used": {line: BoolVar},
            "line_flow": {line: IntVar},
            "source_nodes": list[int],
            "sink_nodes": list[int],
        }
    """
    if not ORTOOLS_AVAILABLE:
        raise ImportError(
            "OR-Tools is not installed. Please install it with: pip install ortools"
        )
    
    if flow_dir_tightening == 'auto':
        n_crossings = len(grid.crossing_groups) if hasattr(grid, 'crossing_groups') and grid.crossing_groups else 0
        flow_dir_tightening = n_crossings >= 3000

    from ortools.sat.python import cp_model

    model = cp_model.CpModel()

    # --------------------
    # Basic sets and parameters
    # --------------------
    num_lines = len(grid.lines_AC_ct)
    num_nodes = len(grid.nodes_AC)

    lines = range(num_lines)
    nodes = range(num_nodes)

    # Use helper function to prepare capacity and min_turbines_per_string
    # This also handles feasibility checks and fixed_substation_connections
    min_turbines_per_string, max_ct_flow, ct_flow_capacity, nT, nS = _prepare_capacity_and_min_turbines(
        grid, max_flow=max_flow, min_turbines_per_string=min_turbines_per_string,
        enable_cable_types=enable_cable_types, t_MW=t_MW, num_nodes=num_nodes,
        fixed_substation_connections=fixed_substation_connections
    )
    
    # Update max_flow for consistency (used later in the function)
    if max_flow is None:
        max_flow = num_nodes - 1

    # Identify sources (renewables) and sinks (generators / substations)
    source_nodes = []
    sink_nodes = []

    for n in nodes:
        nAC = grid.nodes_AC[n]
        if getattr(nAC, "connected_gen", False):
            sink_nodes.append(n)
        if getattr(nAC, "connected_RenSource", False):
            source_nodes.append(n)

    if not sink_nodes:
        raise ValueError("No generator nodes found!")

    source_nodes_set = set(source_nodes)
    sink_nodes_set = set(sink_nodes)

    # Non-sink nodes count (recalculate based on sink_nodes for consistency)
    nT = num_nodes - len(sink_nodes)
    nS = len(sink_nodes)

    # Minimum connections for sink nodes (same formula as Pyomo version)
    # If fixed_substation_connections is set, use that; otherwise calculate based on capacity
    if fixed_substation_connections is not None:
        min_connections_per_sink = fixed_substation_connections
    else:
        # Calculate based on capacity - use max_ct_flow (already calculated above)
        if nS > 0:
            min_connections_per_sink = math.ceil(nT / (nS * max_ct_flow))
        else:
            raise ValueError("No substations found!")

    # --------------------
    # Precompute line incidence and bounds
    # --------------------
    incident_lines = {n: [] for n in nodes}
    line_from = {}
    line_to = {}
    line_lb = {}
    line_ub = {}

    for l in lines:
        line_obj = grid.lines_AC_ct[l]
        from_node = line_obj.fromNode
        to_node = line_obj.toNode

        from_idx = from_node.nodeNumber
        to_idx = to_node.nodeNumber

        line_from[l] = from_idx
        line_to[l] = to_idx

        incident_lines[from_idx].append(l)
        incident_lines[to_idx].append(l)

        # Bounds depend on slack nodes (substations)
        # Note: substations are always toNode, so to_is_slack is true for substation-turbine edges
        # Bounds allow 0 (when line not used) and constraints enforce min_turbines_per_string when used
        from_is_slack = getattr(from_node, "type", None) == "Slack"
        to_is_slack = getattr(to_node, "type", None) == "Slack"

        if to_is_slack and not from_is_slack:
            lb, ub = 0, max_flow  # Allow 0 when line_used=0, constraint enforces min when used
        elif from_is_slack and not to_is_slack:
            lb, ub = -max_flow, 0  # Allow 0 when line_used=0, constraint enforces min when used
        else:
            # If line connects PQ-PQ (turbine-turbine) or both slack: use reduced capacity
            lb, ub = -(max_flow - 1), (max_flow - 1)

        line_lb[l] = lb
        line_ub[l] = ub

    # --------------------
    # Cable type selection (if enabled)
    # --------------------
    ct_set = []
    ct_branch = {}
    ct_types = {}
    
    if enable_cable_types:
        # Cable type set (capacities already calculated above)
        ct_set = list(range(len(grid.Cable_options[0]._cable_types)))
        
        # Update bounds to use max_ct_flow (already calculated, same as max cable type capacity)
        for l in lines:
            line_obj = grid.lines_AC_ct[l]
            from_node = line_obj.fromNode
            to_node = line_obj.toNode
            from_is_slack = getattr(from_node, "type", None) == "Slack"
            to_is_slack = getattr(to_node, "type", None) == "Slack"
            
            if to_is_slack and not from_is_slack:
                line_lb[l], line_ub[l] = 0, max_ct_flow
            elif from_is_slack and not to_is_slack:
                line_lb[l], line_ub[l] = -max_ct_flow, 0
            else:
                line_lb[l], line_ub[l] = -(max_ct_flow - 1), (max_ct_flow - 1)
    
    # --------------------
    # Variables
    # --------------------
    # Binary: line_used[l] = 1 if line is active
    line_used = {
        l: model.NewBoolVar(f"line_used[{l}]")
        for l in lines
    }

    # line_flow_dir: auxiliary binary — tightens LP relaxation (see Pyomo model)
    if flow_dir_tightening:
        line_flow_dir = {
            l: model.NewBoolVar(f"line_flow_dir[{l}]")
            for l in lines
        }

    # Integer flow on each line (can be negative)
    line_flow = {
        l: model.NewIntVar(line_lb[l], line_ub[l], f"line_flow[{l}]")
        for l in lines
    }
    
    # Cable type selection variables (if enabled)
    if enable_cable_types:
        # ct_branch[line, ct] = 1 if cable type ct selected for line
        for l in lines:
            for ct in ct_set:
                ct_branch[(l, ct)] = model.NewBoolVar(f"ct_branch[{l},{ct}]")
        
        # Global cable type indicator: ct_types[ct] = 1 if cable type ct is used anywhere
        for ct in ct_set:
            ct_types[ct] = model.NewBoolVar(f"ct_types[{ct}]")

    # node_flow replaced with inline expressions (no variable needed)
    # Build net-flow expression per node for reuse in constraints
    node_flow_expr = {}
    for n in nodes:
        terms = []
        for l in incident_lines[n]:
            if line_from[l] == n:
                terms.append(line_flow[l])
            elif line_to[l] == n:
                terms.append(-line_flow[l])
        node_flow_expr[n] = sum(terms) if terms else 0

    # --------------------
    # Objective: minimize total cable length (+ optional cable type investment cost)
    # CP-SAT needs integer coefficients: we scale Length_km by length_scale.
    # Using math.ceil to round up to nearest meter integer (conservative approach).
    # Effective objective = sum(line_used[l] * Length_km[l]) up to a constant factor.
    # --------------------
    coeffs = []
    for l in lines:
        # Use installation_cost (= cost_per_km * trench_length_km) to match Pyomo objective
        install_cost = grid.lines_AC_ct[l].installation_cost
        coeff = math.ceil(install_cost * length_scale)
        coeffs.append(coeff)

    if enable_cable_types:
        # Add cable type investment costs
        cable_type_cost_terms = []
        for l in lines:
            line_obj = grid.lines_AC_ct[l]
            for ct in ct_set:
                base_cost = line_obj.base_cost[ct] if hasattr(line_obj, 'base_cost') and ct < len(line_obj.base_cost) else 0
                cost_coeff = math.ceil(base_cost * length_scale)
                cable_type_cost_terms.append(cost_coeff * ct_branch[(l, ct)])
        
        model.Minimize(
            sum(coeffs[l] * line_used[l] for l in lines) + 
            sum(cable_type_cost_terms)
        )
    else:
        model.Minimize(sum(coeffs[l] * line_used[l] for l in lines))

    # --------------------
    # Spanning tree constraint:
    #   sum(line_used) == num_nodes - num_sink_nodes
    # (same as original)
    # --------------------
    model.Add(sum(line_used[l] for l in lines) == num_nodes - len(sink_nodes))

    # --------------------
    # Connection constraints
    # --------------------
    # Upper bound: ct_limit per node if given
    for n in nodes:
        nAC = grid.nodes_AC[n]
        ct_limit = getattr(nAC, "ct_limit", None)
        if ct_limit is not None:
            model.Add(
                sum(line_used[l] for l in incident_lines[n]) <= ct_limit
            )

    # Lower bound:
    # - For sinks: >= min_connections_per_sink
    # - For non-sinks: >= 1
    for n in nodes:
        deg = sum(line_used[l] for l in incident_lines[n])

        if n in sink_nodes_set:
            if min_connections_per_sink > 0:
                model.Add(deg >= min_connections_per_sink)
        else:
            model.Add(deg >= 1)

    # --------------------
    # Flow constraints using inline expressions (no node_flow variable)
    # --------------------
    for n in source_nodes:
        model.Add(node_flow_expr[n] == 1)

    for n in nodes:
        if n not in source_nodes_set and n not in sink_nodes_set:
            model.Add(node_flow_expr[n] == 0)

    if sink_nodes:
        model.Add(
            sum(node_flow_expr[n] for n in sink_nodes) == -len(source_nodes)
        )

    # --------------------
    # Link flow to investment: |line_flow| <= capacity * line_used
    # If cable types enabled, use selected cable type capacity
    # --------------------
    if enable_cable_types:
        # Flow capacity linked to selected cable type
        for l in lines:
            # Flow <= sum(flow_capacity[ct] * ct_branch[line, ct])
            model.Add(
                line_flow[l] <= sum(ct_flow_capacity[ct] * ct_branch[(l, ct)] for ct in ct_set)
            )
            # Flow >= -sum(flow_capacity[ct] * ct_branch[line, ct])
            model.Add(
                line_flow[l] >= -sum(ct_flow_capacity[ct] * ct_branch[(l, ct)] for ct in ct_set)
            )
        
        # Cable type selection: each used line must have exactly one cable type
        # sum(ct_branch[line, ct]) == line_used[line]
        for l in lines:
            model.Add(
                sum(ct_branch[(l, ct)] for ct in ct_set) == line_used[l]
            )
        
        # Homogeneity constraint: link ct_types to ct_branch
        # sum(ct_branch[line, ct]) <= (NN-1) * ct_types[ct]
        NN_minus_1 = num_nodes - len(sink_nodes)
        for ct in ct_set:
            model.Add(
                sum(ct_branch[(l, ct)] for l in lines) <= NN_minus_1 * ct_types[ct]
            )
        
        # Optional: Limit total cable types used
        if cab_types_allowed is not None:
            model.Add(
                sum(ct_types[ct] for ct in ct_set) <= cab_types_allowed
            )
    else:
        # Original flow constraints (no cable type selection)
        for l in lines:
            model.Add(line_flow[l] <= max_flow * line_used[l])
            model.Add(line_flow[l] >= -max_flow * line_used[l])

    # line_flow_dir constraints: tighten LP relaxation (essential for performance)
    if flow_dir_tightening:
        if enable_cable_types:
            M = max(ct_flow_capacity.values()) + 1 if ct_flow_capacity else max_flow + 1
        else:
            M = max_flow + 1

        for l in lines:
            line_obj = grid.lines_AC_ct[l]
            to_is_slack = getattr(line_obj.toNode, "type", None) == "Slack"
            min_flow = min_turbines_per_string if to_is_slack else 1
            model.Add(line_flow[l] >= (min_flow - 2*M) + M*line_flow_dir[l] + M*line_used[l])

        for l in lines:
            line_obj = grid.lines_AC_ct[l]
            from_is_slack = getattr(line_obj.fromNode, "type", None) == "Slack"
            min_flow = min_turbines_per_string if from_is_slack else 1
            model.Add(line_flow[l] <= (-min_flow + M) - M*line_used[l] + M*line_flow_dir[l])

        for l in lines:
            model.Add(line_flow_dir[l] <= line_used[l])

    # --------------------
    # Crossing constraints: at most one line per crossing group
    # --------------------
    if crossings and hasattr(grid, "crossing_groups") and grid.crossing_groups:
        # Map lineNumber -> index
        line_number_to_idx = {
            grid.lines_AC_ct[l].lineNumber: l
            for l in lines
        }

        for group_idx, group in enumerate(grid.crossing_groups):
            # group is a collection of lineNumbers
            line_indices = [
                line_number_to_idx[ln]
                for ln in group
                if ln in line_number_to_idx
            ]
            if line_indices:
                model.Add(
                    sum(line_used[l] for l in line_indices) <= 1
                )

    # --------------------
    # Return model + handy variable dict
    # --------------------
    vars_dict = {
        "line_used": line_used,
        "line_flow": line_flow,
        "source_nodes": source_nodes,
        "sink_nodes": sink_nodes,
    }
    if flow_dir_tightening:
        vars_dict["line_flow_dir"] = line_flow_dir
    
    if enable_cable_types:
        vars_dict["ct_branch"] = ct_branch
        vars_dict["ct_types"] = ct_types
        vars_dict["ct_set"] = ct_set
        vars_dict["ct_flow_capacity"] = ct_flow_capacity

    return model, vars_dict


def _plot_feasible_solutions(results,type='solution', plot_type='MIP', suptitle=None, show=True, save_path=None, width_mm=None):
    import matplotlib.pyplot as plt
    # local import to ensure availability regardless of module-level imports
    import os
    FS = 10
    
    # Determine which column to extract based on type parameter
    # Tuples are always (time, solution, gap)
    if type == 'gap':
        col_idx = 2  # Third column (gap)
    else:  # type == 'solution'
        col_idx = 1  # Second column (solution)
    
    # Normalize input: accept a single feasible_solutions list, a list of those,
    # a dict with key 'feasible_solutions_MIP', or a list of such dicts
    def _is_pair_list(seq):
        try:
            return isinstance(seq, (list, tuple)) and len(seq) > 0 and isinstance(seq[0], (list, tuple)) and len(seq[0]) >= 2
        except Exception:
            return False
    
    if results is None:
        normalized_results = []
    elif isinstance(results, dict) and 'feasible_solutions_MIP' in results:
        normalized_results = [results.get('feasible_solutions_MIP', [])]
    elif isinstance(results, list):
        if len(results) > 0 and isinstance(results[0], dict) and 'feasible_solutions_MIP' in results[0]:
            normalized_results = [r.get('feasible_solutions_MIP', []) for r in results]
        elif _is_pair_list(results):
            # single run provided as list of (time, obj)
            normalized_results = [results]
        else:
            # assume already in the expected list-of-runs format
            normalized_results = results
    else:
        # Fallback: treat as empty
        normalized_results = []
    
    if width_mm is not None:
        fig_w_in = width_mm / 25.4
        fig_h_in = fig_w_in 
    else:
        fig_w_in = 6.0
        fig_h_in = fig_w_in 

    fig, ax = plt.subplots(1, 1, figsize=(fig_w_in, fig_h_in), sharex=False, sharey=False, constrained_layout=True)

    # Normalize plot_type and set axis label
    ptype = (plot_type or 'MIP').upper()
    if ptype == 'CSS':
        y_axis_label = 'Objective [M€]'
    else:
        ptype = 'MIP'
        y_axis_label = 'Cable length [km]'
    
    # Update y-axis label based on type
    if type == 'gap':
        y_axis_label = 'Gap'

    # plotting logic mirroring the subplots helper
    if not normalized_results:
        ax.set_title(ptype, fontsize=FS)
        ax.set_xlabel('Time (s)', fontsize=FS)
        ax.set_ylabel(y_axis_label, fontsize=FS)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=FS)
    else:
        has_any = False
        for i, feas in enumerate(normalized_results):
            if not feas:
                continue
            has_any = True
            feas_sorted = sorted(feas, key=lambda x: x[0])
            times = []
            values = []
            for f in feas_sorted:
                # Tuples are always (time, solution, gap)
                t = f[0]
                v = f[col_idx]
                # For gap, skip None values
                if col_idx == 2 and v is None:
                    continue
                times.append(t)
                values.append(v)
            
            if not times:  # Skip if no valid data points
                continue
            
            if ptype == 'CSS' and col_idx == 1:
                values = [v / 1e6 for v in values]
            ax.plot(times, values, 'o-', label=f'i={i} (s={len(values)})', markersize=5, linewidth=2)
        ax.set_title(ptype, fontsize=FS*1.2)
        ax.set_xlabel('Time (s)', fontsize=FS*1.1)
        ax.set_ylabel(y_axis_label, fontsize=FS*1.1)
        if has_any:
            ax.legend(prop={'size': FS}, loc='upper right', frameon=False)
        ax.tick_params(labelsize=FS)
        ax.grid(True, alpha=0.3)

    if suptitle is not None:
        fig.suptitle(suptitle, fontsize=FS*1.3)
        fig.subplots_adjust(left=0.10, right=0.99, top=0.80, bottom=0.22)
    else:
        fig.subplots_adjust(left=0.08, right=0.99, top=0.98, bottom=0.18)

    if save_path is not None:
        dir_, base = os.path.split(save_path)
        root, ext = os.path.splitext(base)
        base = (root + ext.lower()).lower()
        save_path = os.path.join(dir_, base)
        if save_path.endswith('.svg'):
            fig.savefig(save_path, format='svg', bbox_inches='tight')
        else:
            fig.savefig(save_path, format='png', bbox_inches='tight')

    if show:
        plt.show()
    else:
        plt.close(fig)

def _export_feasible_solutions_to_excel(results_mip, results_css, save_path):
    """
    Export feasible solutions to separate CSV files (one for MIP, one for CSS) or Excel.
    Format: 0_t, 0_obj, 0_gap, 1_t, 1_obj, 1_gap, ...
    
    Args:
        results_mip: List of feasible solutions for MIP (each is list of (time, obj, gap) tuples)
        results_css: List of feasible solutions for CSS (each is list of (time, obj, gap) tuples)
        save_path: Base path (will create _MIP.csv and _CSS.csv, or single .xlsx file)
    """
    
    # Determine format from extension
    base_path = save_path
    if save_path.lower().endswith('.csv'):
        base_path = save_path[:-4]  # Remove .csv extension
        file_format = 'csv'
    elif save_path.lower().endswith('.xlsx'):
        file_format = 'excel'
    else:
        # Default to CSV
        file_format = 'csv'
    
    def _export_single(results, suffix, max_solutions):
        """Export a single set of results (MIP or CSS)"""
        if not results:
            return None
        
        data = {}
        max_iter = len(results)
        
        for i in range(max_iter):
            if results[i]:
                feas_sorted = sorted(results[i], key=lambda x: x[0])  # Sort by time
                # Pad to max_solutions with NaN
                times = [t for t, _, _ in feas_sorted] + [np.nan] * (max_solutions - len(feas_sorted))
                objs = [o for _, o, _ in feas_sorted] + [np.nan] * (max_solutions - len(feas_sorted))
                gaps = [g for _, _, g in feas_sorted] + [np.nan] * (max_solutions - len(feas_sorted))
                
                data[f'{i}_t'] = times[:max_solutions]
                data[f'{i}_obj'] = objs[:max_solutions]
                data[f'{i}_gap'] = gaps[:max_solutions]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        if file_format == 'csv':
            csv_path = f"{base_path}_{suffix}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Feasible solutions ({suffix}) exported to CSV: {csv_path}")
            return None
        else:
            # For Excel, return DataFrame to write to sheet
            return df
    
    # Find maximum number of feasible solutions for each type
    max_mip_solutions = max((len(feas) for feas in results_mip if feas), default=0)
    max_css_solutions = max((len(feas) for feas in results_css if feas), default=0)
    
    if max_mip_solutions == 0 and max_css_solutions == 0:
        print("Warning: No feasible solutions to export")
        return
    
    if file_format == 'csv':
        # Save separate CSV files
        if max_mip_solutions > 0:
            _export_single(results_mip, 'MIP', max_mip_solutions)
        if max_css_solutions > 0:
            _export_single(results_css, 'CSS', max_css_solutions)
    else:
        # Save to Excel with separate sheets
        excel_path = f"{base_path}.xlsx" if not base_path.endswith('.xlsx') else base_path
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            if max_mip_solutions > 0:
                df_mip = _export_single(results_mip, 'MIP', max_mip_solutions)
                if df_mip is not None:
                    df_mip.to_excel(writer, sheet_name='MIP', index=False)
            if max_css_solutions > 0:
                df_css = _export_single(results_css, 'CSS', max_css_solutions)
                if df_css is not None:
                    df_css.to_excel(writer, sheet_name='CSS', index=False)
        print(f"Feasible solutions exported to Excel: {excel_path}")


def _plot_feasible_solutions_subplots(results_mip, results_css, suptitle=None, show=True, save_path=None, width_mm=None,type='gap'):
    import matplotlib.pyplot as plt
    FS = 10
    # Maintain 40:20 aspect ratio regardless of absolute size (taller axes)
    ratio = 20.0 / 40.0
    if width_mm is not None:
        fig_w_in = width_mm / 25.4
        fig_h_in = fig_w_in * ratio
    else:
        fig_w_in = 6.0
        fig_h_in = fig_w_in * ratio
    figsize = (fig_w_in, fig_h_in)
    # Two subplots side-by-side: MIP (left), CSS (right)
    fig, axes = plt.subplots(1, 2, figsize=figsize, sharex=False, sharey=False, constrained_layout=True)

    def _plot(ax, results, title,yaxis,type):
        if not results:
            ax.set_title(title, fontsize=FS)
            ax.set_xlabel('Time (s)', fontsize=FS)
            ax.set_ylabel(yaxis, fontsize=FS)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=FS)
            return
        has_any = False
        for i, feas in enumerate(results):
            if not feas:
                continue
            has_any = True
            feas_sorted = sorted(feas, key=lambda x: x[0])
            # Unpack (time, objective, gap) tuples
            times = [t for t, _, _ in feas_sorted]
            if type == 'gap':
                # Handle None gaps - convert to percentage, use 0 if None
                gap = [(g * 100 if g is not None else 0) for _, _, g in feas_sorted]
            else:
                gap = [o for _, o, _ in feas_sorted]
                if title == 'CSS':
                    gap = [o/1e6 for o in gap]
            ax.plot(times, gap, 'o-', label=f'i={i} (s={len(gap)})', markersize=5, linewidth=2)
        ax.set_title(title, fontsize=FS*1.2)
        ax.set_xlabel('Time (s)', fontsize=FS*1.1)
        ax.set_ylabel(yaxis, fontsize=FS*1.1)
        if has_any:
            ax.legend(prop={'size': FS}, loc='upper right', frameon=False)
        ax.tick_params(labelsize=FS)
        ax.grid(True, alpha=0.3)
    
    if type == 'gap':
        _plot(axes[0], results_mip, 'MIP', 'Gap [%]',type)
        _plot(axes[1], results_css, 'CSS', 'Gap [%]',type)
    else:
        _plot(axes[0], results_mip, 'MIP', 'Cable length [km]',type)
        _plot(axes[1], results_css, 'CSS', 'Objective [M€]',type)
   

    if suptitle is not None:
        fig.suptitle(suptitle, fontsize=FS*1.3)
        fig.subplots_adjust(left=0.10, right=0.99, top=0.80, bottom=0.22, wspace=0.22)
    else:
        fig.subplots_adjust(left=0.08, right=0.99, top=0.98, bottom=0.18, wspace=0.18)

    if save_path is not None:
        dir_, base = os.path.split(save_path)
        root, ext = os.path.splitext(base)
        base = (root + ext.lower()).lower()  # lowercase name + extension
        save_path = os.path.join(dir_, base)
        
        if save_path.endswith('.svg'):
            fig.savefig(save_path, format='svg', bbox_inches='tight')
        else:
            fig.savefig(save_path, format='png', bbox_inches='tight')

    if show:
        plt.show()
    else:
        plt.close(fig)



def simple_CSS(grid,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,ObjRule=None,CSS_L_solver='gurobi',CSS_NL_solver='bonmin',time_limit=1200,NL=False,tee=False,export=True,fs=False):

    grid.Array_opf = False
    if NL:
        model, model_results , timing_info, solver_stats= transmission_expansion(grid,NPV,n_years,Hy,discount_rate,ObjRule,CSS_NL_solver,time_limit,tee,export,PV_set=True,callback=fs)
    elif CSS_L_solver == 'ortools':
        from .AC_L_CSS_ortools import Optimal_L_CSS_ortools
        OPEX = ObjRule is not None and ObjRule.get('Energy_cost', 0) != 0
        model, model_results, timing_info, solver_stats = Optimal_L_CSS_ortools(
            grid, OPEX=OPEX, NPV=NPV, n_years=n_years, Hy=Hy,
            discount_rate=discount_rate, tee=tee, time_limit=time_limit)
    else:
        model, model_results , timing_info, solver_stats= linear_transmission_expansion(grid,NPV,n_years,Hy,discount_rate,None,CSS_L_solver,time_limit,tee,export,fs)

    return model, model_results , timing_info, solver_stats
