# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 15:13:24 2025

@author: BernardoCastro
"""
import pyflow_acdc as pyf
import pyomo.environ as pyo
from pathlib import Path
import time

cases = {
    'arcadis_ost'
}

current_file = Path(__file__).resolve()
path = str(current_file.parent)
ct= 3
LCoE = 91

MIP_solver = 'gurobi'
tl = 300
NL = False
tee = False
fs = False
obj = {'Energy_cost': 1}
FLH = 8760
WACC = 0.02

def run_case(case,MIP_solver='gurobi'):
    start_time = time.perf_counter()
    touple = pyf.Grid_creator.load_pickle(f'{path}/wfarms/{case}.pkl.gz')
    array_graph,Data,cable_types,final_polygon =touple

    
    grid, res = pyf.Create_grid_from_turbine_graph(array_graph,Data,cable_types=cable_types,cable_types_allowed=ct,curtailment_allowed=0 ,LCoE=LCoE,MIP_time=tl,name=case)
    #model, model_results , timing_info, solver_stats= pyf.Optimal_L_CSS_gurobi(grid,OPEX=True,NPV=True,n_years=25,Hy=FLH,discount_rate=WACC,tee=False,time_limit=tl)
    

    model, summary_results , timing_info, solver_stats,best_i= pyf.sequential_CSS(grid,NPV=True,n_years=25,Hy=FLH,discount_rate=WACC,ObjRule=obj,MIP_solver=MIP_solver,CSS_L_solver='gurobi',CSS_NL_solver='bonmin',max_iter= None,time_limit=tl,NL=NL,tee=tee,fs=fs)
    lines_active_config = {line.lineNumber: line.active_config for line in grid.lines_AC_ct}
    
    i = len(summary_results['iteration'])
    obj_value = pyo.value(model[1].obj)
    cable_length = summary_results['cable_length'][best_i]
    path_time = timing_info['Paths']
    css_time = timing_info['CSS']
    crossing = len(Data['crossing_pairs'])    
        
    total_time = time.perf_counter() - start_time
    
    #pyf.plot_folium(grid,name=f'{case}',show=True,polygon=final_polygon)
    return i, total_time, array_graph.number_of_edges(), array_graph.number_of_nodes()-len(Data['turbine']),len(Data['turbine']),obj_value,path_time,css_time,summary_results,crossing,cable_length

def run_test():
    """Test CIGRE B4 optimal power flow."""
    try:
        import dill
    except ImportError:
        print("dill is not installed (required to load pickle files)...")
        return
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    try:
        import pyomo.environ as pyo
        solver = pyo.SolverFactory('gurobi')
        if not solver.available():
            raise ImportError("Gurobi solver not available")
    except (ImportError, Exception):
        print("Gurobi solver is not available.")
        MIP_solver = 'glpk'
    for case in cases:
        i, total_time, edges, subsations, turbines,obj_value,path_time,css_time,summary_results,crossing,cable_length = run_case(case,MIP_solver)
        print(f'{case}- iterations {i}, total time {total_time}, edges {edges}, subsations {subsations}, turbines {turbines}, obj_value {obj_value}, path_time {path_time}, css_time {css_time},  crossing {crossing}, cable_length {cable_length}')
    
if __name__ == "__main__":
    run_test()