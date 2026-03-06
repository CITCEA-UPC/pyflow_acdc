from pymoo.core.problem import ElementwiseProblem
import numpy as np
import pyomo.environ as pyo
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import time
import matplotlib.pyplot as plt
from .ACDC_OPF_NL_model import analyse_grid,ExportACDC_NLmodel_toPyflowACDC
from .ACDC_OPF import pyomo_model_solve,OPF_obj,obj_w_rule,calculate_objective
from .grid_analysis import analyse_grid

__all__ = [
    'transmission_expansion_pymoo'
]


    

class TEPOuterProblem(ElementwiseProblem):
    def __init__(self, grid, weights_def, n_years, Hy, r, pv_set=False, pz=False, time_limit=60,objective_type='sum'):
        if objective_type == 'sum':
            n_obj = 1
        elif objective_type == 'pareto':
            n_obj = 2
        else:
            raise ValueError("optimization_type must be 'sum' or 'pareto'")
        
        self.objective_type = objective_type
        t1=time.perf_counter()
        analyse_grid(grid)
        self.grid = grid
        self._store_TEP_flags()
        n_var, xl, xu, vtype, self.bound_names = self._create_pymoo_bounds()
         
        super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu, vtype=vtype)  # mix with bools if needed
        
        self.weights_def = weights_def
        self.present_value = Hy * (1 - (1 + r) ** -n_years) / r
        self.pv_set = pv_set
        self.pz = pz
        self.time_limit = time_limit
        self.pyomo_runs = 0
        self.pyomo_feasible_solutions = 0
        self.pyomo_time = 0


        self.model = self._build_model()  # built once with TEP=False
        self.t_modelcreate = time.perf_counter() - t1

    def _create_pymoo_bounds(self):
        """Create bounds and variable types for pymoo based on original TEP flags"""
        bounds = []
        xl = []  # lower bounds
        xu = []  # upper bounds
        vtype = []  # variable types
        self.idx_to_object = {}  # NEW: mapping from pymoo index to object info
        idx = 0
        
        # AC expansions (integer variables)
        for l in self.grid.lines_AC_exp:
            if self.original_np_line_opf.get(l.lineNumber, False):
                xl.append(l.np_line)  # minimum: current value
                xu.append(l.np_line_max)  # maximum: max allowed
                vtype.append(int)
                bounds.append(f"AC_exp_{l.lineNumber}")
                self.idx_to_object[idx] = (l.lineNumber, "np_line_AC")
                idx += 1
        
        # DC lines (integer variables)
        for l in self.grid.lines_DC:
            if self.original_np_line_opf_DC.get(l.lineNumber, False):  # Check current flag (should be True for DC lines)
                xl.append(l.np_line)
                xu.append(l.np_line_max)
                vtype.append(int)
                bounds.append(f"DC_line_{l.lineNumber}")
                self.idx_to_object[idx] = (l.lineNumber, "np_line_DC")
                idx += 1
        # Converters (integer variables)
        for c in self.grid.Converters_ACDC:
            if self.original_np_conv_opf.get(c.ConvNumber, False):
                xl.append(c.np_conv)
                xu.append(c.np_conv_max)
                vtype.append(int)
                bounds.append(f"Conv_{c.ConvNumber}")
                self.idx_to_object[idx] = (c.ConvNumber, "np_conv_ACDC")
                idx += 1
        # AC repurposing (binary variables)
        for l in self.grid.lines_AC_rec:
            if self.original_rec_line_opf.get(l.lineNumber, False):
                xl.append(0)
                xu.append(1)
                vtype.append(int)  # pymoo uses int for binary
                bounds.append(f"AC_rec_{l.lineNumber}")
                self.idx_to_object[idx] = (l.lineNumber, "rec_line_AC")
                idx += 1
        # Array cable type (integer variables: -1 to max_cable_type)
        for l in self.grid.lines_AC_ct:
            if self.original_array_opf.get(l.lineNumber, False):
                if self.grid.Array_opf: 
                    xl.append(-1)  # -1 means no cable
                    self.idx_to_object[idx] = (l.lineNumber, "Array_ct_AC")
                elif l.active_config < 0:
                    continue
                else:
                    xl.append(0)
                    self.idx_to_object[idx] = (l.lineNumber, "CSS_AC")
                xu.append(len(l._cable_types) - 1)  # max cable type index
                vtype.append(int)
                bounds.append(f"Array_ct_{l.lineNumber}")
                
                idx += 1
        # AC generators (if GPR is enabled)
        if self.grid.GPR:
            for g in self.grid.Generators:
                if self.original_np_gen_opf.get(g.genNumber, False):
                    xl.append(g.np_gen)
                    xu.append(g.np_gen_max)
                    vtype.append(int)
                    bounds.append(f"Gen_{g.genNumber}")
                    self.idx_to_object[idx] = (g.genNumber, "ac_gen")
                    idx += 1
        # DC generators (if GPR is enabled)
        if self.grid.GPR:
            for g in self.grid.Generators_DC:
                if self.original_np_gen_opf_DC.get(g.genNumber_DC, False):
                    xl.append(g.np_gen)
                    xu.append(g.np_gen_max)
                    vtype.append(int)
                    bounds.append(f"Gen_DC_{g.genNumber_DC}")
                    self.idx_to_object[idx] = (g.genNumber_DC, "dc_gen")
                    idx += 1
        return len(xl), xl, xu, vtype, bounds 


    def _store_TEP_flags(self):
        # Store original True values in dictionaries
        self.original_np_gen_opf = {}
        self.original_np_gen_opf_DC = {}

        self.original_np_line_opf = {}
        self.original_rec_line_opf = {}
        self.original_array_opf = {}

        self.original_np_line_opf_DC = {}
        self.original_np_conv_opf = {}
        
        for g in self.grid.Generators:
            self.original_np_gen_opf[g.genNumber] = g.np_gen_opf
            g.np_gen_opf = False
        
        # AC expansions
        for l in self.grid.lines_AC_exp:
            self.original_np_line_opf[l.lineNumber] = l.np_line_opf
            l.np_line_opf = False
        
        # AC repurposing
        for l in self.grid.lines_AC_rec:
            self.original_rec_line_opf[l.lineNumber] = l.rec_line_opf
            l.rec_line_opf = False
        
        # Array cable type
        for l in self.grid.lines_AC_ct:
            self.original_array_opf[l.lineNumber] = l.array_opf
            l.array_opf = False
        

        for g in self.grid.Generators_DC:
            self.original_np_gen_opf_DC[g.genNumber_DC] = g.np_gen_opf
            g.np_gen_opf = False

        for l in self.grid.lines_DC:
            self.original_np_line_opf_DC[l.lineNumber] = l.np_line_opf
            l.np_line_opf = False
    
        # Converters
        for c in self.grid.Converters_ACDC:
            self.original_np_conv_opf[c.ConvNumber] = c.np_conv_opf
            c.np_conv_opf = False

    def _restore_TEP_flags(self):
        for g in self.grid.Generators:
            g.np_gen_opf = self.original_np_gen_opf[g.genNumber]

        for l in self.grid.lines_AC_exp:
            l.np_line_opf = self.original_np_line_opf[l.lineNumber]
        for l in self.grid.lines_AC_rec:
            l.rec_line_opf = self.original_rec_line_opf[l.lineNumber]
        for l in self.grid.lines_AC_ct:
            l.array_opf = self.original_array_opf[l.lineNumber]

        for l in self.grid.lines_DC:
            l.np_line_opf = self.original_np_line_opf_DC[l.lineNumber]
       

        for c in self.grid.Converters_ACDC:
            c.np_conv_opf = self.original_np_conv_opf[c.ConvNumber]
    
    def _build_model(self):
        model = pyo.ConcreteModel()
        model.name = "TEP pymoo OPF"
        
        # Import the OPF builder
        from .ACDC_OPF_NL_model import OPF_create_NLModel_ACDC
        
        # Build with TEP=False so investments are Params
        OPF_create_NLModel_ACDC(model, self.grid, PV_set=self.pv_set, 
                               Price_Zones=self.pz, TEP=False)
        
        obj_OPF = OPF_obj(model,self.grid,self.weights_def)
    
        model.obj = pyo.Objective(rule=obj_OPF, sense=pyo.minimize)
        return model

    

    def _capex_from_model(self,NPV=True):
        capex = 0.0
        def Gen_investments():
            np_gen_TEP = {k: np.float64(pyo.value(v)) for k, v in self.model.np_gen.items()}
            Gen_Inv = 0
            if hasattr(self.model, 'gen_AC') and hasattr(self.model, 'np_gen'):
                for g in self.model.gen_AC:
                    gen = self.grid.Generators[g]
                    if self.original_np_gen_opf.get(g, False):
                        Gen_Inv += (np_gen_TEP[g] - gen.np_gen) * gen.base_cost
            return Gen_Inv

        def AC_Line_investments():
            AC_Inv_lines = 0
            lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in self.model.NumLinesACP.items()}
            if hasattr(self.model, 'lines_AC_exp') and hasattr(self.model, 'NumLinesACP'):
                for l in self.model.lines_AC_exp:
                    line = self.grid.lines_AC_exp[l]
                    if self.original_np_line_opf.get(l, False):
                        if NPV:
                            AC_Inv_lines += (lines_AC_TEP[l] - line.np_line) * line.base_cost
                        else:
                            AC_Inv_lines += (lines_AC_TEP[l] - line.np_line) * line.base_cost / line.life_time_hours
            return AC_Inv_lines
        
        def Repurposing_investments():
            Rep_Inv_lines = 0
            lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in self.model.rec_branch.items()}
            if hasattr(self.model, 'lines_AC_rec') and hasattr(self.model, 'rec_branch'):
                for l in self.model.lines_AC_rec:
                    line = self.grid.lines_AC_rec[l]
                    if self.original_rec_line_opf.get(l, False):
                        if NPV:
                            Rep_Inv_lines += lines_AC_REP[l] * line.base_cost
                        else:
                            Rep_Inv_lines += lines_AC_REP[l] * line.base_cost / line.life_time_hours
            return Rep_Inv_lines
        
        def Cables_investments():
            lines_DC_TEP = {k: np.float64(pyo.value(v)) for k, v in self.model.NumLinesDCP.items()}
            Inv_lines = 0
            if hasattr(self.model, 'lines_DC') and hasattr(self.model, 'NumLinesDCP'):
                for l in self.model.lines_DC:
                    line = self.grid.lines_DC[l]
                    if self.original_np_line_opf_DC.get(l, False):
                        if NPV:
                            Inv_lines += (lines_DC_TEP[l] - line.np_line) * line.base_cost
                        else:
                            Inv_lines += (lines_DC_TEP[l] - line.np_line) * line.base_cost / line.life_time_hours
            return Inv_lines

        def Array_investments():
            Inv_array = 0
            lines_AC_CT = {k: {ct: np.float64(pyo.value(self.model.ct_branch[k, ct])) for ct in self.model.ct_set} for k in self.model.lines_AC_ct}
            if hasattr(self.model, 'lines_AC_ct') and hasattr(self.model, 'ct_branch'):
                for l in self.model.lines_AC_ct:
                    line = self.grid.lines_AC_ct[l]
                    if self.original_array_opf.get(l, False):
                        if NPV:
                            for ct in self.model.ct_set:
                                Inv_array += lines_AC_CT[l, ct] * line.base_cost[ct]
                        else:
                            for ct in self.model.ct_set:
                                Inv_array += lines_AC_CT[l, ct] * line.base_cost[ct] / line.life_time_hours
            return Inv_array
            
        def Converter_investments():
            Inv_conv = 0
            np_conv_TEP = {k: np.float64(pyo.value(v)) for k, v in self.model.np_conv.items()}
            if hasattr(self.model, 'conv') and hasattr(self.model, 'np_conv'):
                for cn in self.model.conv:
                    conv = self.grid.Converters_ACDC[cn]
                    if self.original_np_conv_opf.get(cn, False):
                        if NPV:
                            Inv_conv += (np_conv_TEP[cn] - conv.np_conv) * conv.base_cost
                        else:
                            Inv_conv += (np_conv_TEP[cn] - conv.np_conv) * conv.base_cost / conv.life_time_hours
            return Inv_conv
        def DC_Gen_investments():
            Inv_gen = 0
            np_gen_TEP = {k: np.float64(pyo.value(v)) for k, v in self.model.np_gen_DC.items()}
            if hasattr(self.model, 'gen_DC') and hasattr(self.model, 'np_gen_DC'):
                for g in self.model.gen_DC:
                    gen = self.grid.Generators_DC[g]
                    if self.original_np_gen_opf_DC.get(g, False):
                        Inv_gen += (np_gen_TEP[g] - gen.np_gen) * gen.base_cost
            return Inv_gen

        if self.grid.GPR:
            capex += Gen_investments()      
            capex += DC_Gen_investments()
        if self.grid.TEP_AC:
            capex += AC_Line_investments()     
        if self.grid.REC_AC:
            capex += Repurposing_investments()        
        if self.grid.CT_AC:
            capex += Cables_investments()       
        if self.grid.Array_opf:
            capex += Array_investments()       
        if self.grid.ACmode and self.grid.DCmode:
            capex += Converter_investments()
        
        return capex

    def _update_model_from_vector(self, x):
        for idx, value in enumerate(x):
            obj_id, obj_type = self.idx_to_object[idx]
            
            if obj_type == 'np_line_AC':
                self.model.NumLinesACP[obj_id].set_value(int(value))
            elif obj_type == 'np_line_DC':
                self.model.NumLinesDCP[obj_id].set_value(int(value))
            elif obj_type == 'np_conv_ACDC':
                self.model.np_conv[obj_id].set_value(int(value))
            elif obj_type == 'rec_line_AC':
                self.model.rec_branch[obj_id].set_value(bool(value))
            elif obj_type == 'CSS_AC':
                # Set one-hot encoding for cable type
                for ct in self.model.ct_set:
                    self.model.ct_branch[obj_id, ct].set_value(1 if ct == int(value) else 0)
            elif obj_type == 'Array_ct_AC':
                if int(value) == -1:
                    # No cable type selected - set all to 0 
                    for ct in self.model.ct_set:
                        self.model.ct_branch[obj_id, ct].set_value(0)
                else:
                    # Cable type selected - one-hot encoding
                    for ct in self.model.ct_set:
                        self.model.ct_branch[obj_id, ct].set_value(1 if ct == int(value) else 0)

            elif obj_type == 'ac_gen':
                self.model.np_gen[obj_id].set_value(int(value))
            elif obj_type == 'dc_gen':
                self.model.np_gen_DC[obj_id].set_value(int(value))
        
    
    def _evaluate(self, x, out, *args, **kwargs):
        try:
            # Suppress Pyomo logging warnings
            import logging
            pyomo_logger = logging.getLogger('pyomo')
            original_level = pyomo_logger.level
            pyomo_logger.setLevel(logging.ERROR) 
            # Refresh Pyomo Params instead of rebuilding
            self._update_model_from_vector(x)
            self.pyomo_runs += 1
            
            results, stats = pyomo_model_solve(self.model, self.grid, solver='ipopt', tee=False, time_limit=self.time_limit, suppress_warnings=True)
            self.pyomo_time += stats['time']
            if results is None:
                out["F"] = 1e24
                return
            
            capex = self._capex_from_model()
            opex = pyo.value(self.model.obj)
            if results.solver.termination_condition == pyo.TerminationCondition.optimal or results.solver.termination_condition == pyo.TerminationCondition.feasible:
                self.pyomo_feasible_solutions += 1

            opex  = self.present_value * opex
            if results.solver.termination_condition == pyo.TerminationCondition.infeasible:
                capex = 1e12
                opex = 1e12
            if self.objective_type == 'sum':
                out["F"] = capex +  opex
            elif self.objective_type == 'pareto':
                out["F"] = [capex,  opex]
            
            
        except Exception:
            if self.objective_type == 'sum':
                out["F"] = 1e12
            else:
                out["F"] = [1e12, 1e12]
            

    def export_solution_to_grid(self, x,grid):
        """Export the best pymoo solution back to the grid object"""
        
        # Update model with the solution
        self._update_model_from_vector(x)
        results, stats = pyomo_model_solve(self.model, grid, solver='ipopt', tee=False, time_limit=self.time_limit, suppress_warnings=True)
            

        # Get price zones info (you might need to pass this from __init__)
        PZ = getattr(self, 'pz', False)
        # Restore original TEP flags
        self._restore_TEP_flags()
        # Export the solved model to grid
        ExportACDC_NLmodel_toPyflowACDC(self.model, grid, PZ, TEP=True)
            
        
        
        

def transmission_expansion_pymoo(grid,NPV=True,n_years=25,Hy=8760,discount_rate=0.02,ObjRule=None,solver='GA',time_limit=300,tee=False,n_gen=10):
    
            
    analyse_grid(grid)
    
    weights_def, PZ = obj_w_rule(grid,ObjRule,True)
    # Create problem
    if solver == 'GA':
        algorithm = GA(pop_size=50)
        objective_type = 'sum'
    elif solver == 'NSGA2':
        algorithm = NSGA2(pop_size=50)
        objective_type = 'pareto'
    else:
        raise ValueError("solver must be 'GA' or 'NSGA2'")

    problem = TEPOuterProblem(grid, weights_def, n_years=n_years, Hy=Hy, r=discount_rate,objective_type=objective_type)

    # Run optimization
    
    
    res = minimize(problem, algorithm, 
                  ('n_gen', n_gen), ('f_tol', 1e-6),
                  save_history=True,
                  verbose=tee)
  
    if objective_type == 'sum':
        return _handle_single_objective_result(res, problem, grid)
    else:
        return _handle_pareto_result(res, problem, grid,pareto_result='balanced')

def _handle_single_objective_result(res, problem, grid):
    """Handle single-objective optimization results"""
    # Export best solution to grid
    # Export best solution to grid
    t1 = time.perf_counter()
    best_solution = res.X  # Best decision vector
    
    problem.export_solution_to_grid(best_solution,grid)
    for obj in problem.weights_def:
        problem.weights_def[obj]['v']=calculate_objective(grid,obj,True)
        problem.weights_def[obj]['NPV']=problem.weights_def[obj]['v']*problem.present_value
    grid.TEP_run=True
    grid.OPF_obj = problem.weights_def
    t2 = time.perf_counter() 

    t_modelexport = t2-t1

    


    # Now grid contains the optimized solution
    print(f"Best objective: {res.F[0]}")
    print(f"Grid now has optimized investments")

    

    print(f"Number of Pyomo runs: {problem.pyomo_runs}")
    print(f"Pyomo time: {problem.pyomo_time}")
    print(f"mean Pyomo time: {problem.pyomo_time / problem.pyomo_runs}")
    val = [e.opt.get("F")[0] for e in res.history]
    plt.plot(np.arange(len(val)), val)
    plt.show()
    timing_info = {
        "create": problem.t_modelcreate,  # Model creation time (negligible for pymoo)
        "solve": res.exec_time,  # Optimization time
        "export": t_modelexport,  # Export time (negligible)
    }
    
    solver_stats = {
        'iterations': len(val),
        'best_objective': res.F[0],
        'time': res.exec_time,
        'termination_condition': 'optimal',
        'feasible_solutions': []
    }
    # Return same format as original: model, results, timing_info, solver_stats
    return problem, res, timing_info, solver_stats

def _handle_pareto_result(res, problem, grid,pareto_result='balanced'):
    """Handle multi-objective optimization results"""
    # Get Pareto front
    pareto_front = res.F  # Shape: (n_solutions, 2)
    pareto_solutions = res.X  # Shape: (n_solutions, n_variables)
    
    # Find different trade-off solutions
    min_capex_idx = np.argmin(pareto_front[:, 0])
    min_opex_idx = np.argmin(pareto_front[:, 1])
    balanced_idx = np.argmin(np.sum(pareto_front, axis=1))
    
    # Export balanced solution to grid (or let user choose)
    if pareto_result == 'balanced':
        chosen_solution = pareto_solutions[balanced_idx]
    elif pareto_result == 'min_capex':
        chosen_solution = pareto_solutions[min_capex_idx]
    elif pareto_result == 'min_opex':
        chosen_solution = pareto_solutions[min_opex_idx]
    else:
        raise ValueError("pareto_result must be 'balanced', 'min_capex', or 'min_opex'")
    problem.export_solution_to_grid(chosen_solution,grid)
    for obj in problem.weights_def:
        problem.weights_def[obj]['v']=calculate_objective(grid,obj,True)
        problem.weights_def[obj]['NPV']=problem.weights_def[obj]['v']*problem.present_value
    grid.TEP_run=True
    grid.OPF_obj = problem.weights_def
    # All populations' objectives across generations
    F_all = [e.pop.get("F") for e in res.history]  # list of (pop_size x n_obj)
    F_all_flat = np.vstack(F_all)               # (N_total x n_obj)
    # Remove penalized entries exactly equal to [1e12, 1e12]
    if F_all_flat.ndim == 2 and F_all_flat.shape[1] == 2:
        valid_mask = ~np.all(F_all_flat == 1e12, axis=1)
        F_all_flat = F_all_flat[valid_mask]
    capex_all = F_all_flat[:, 0] / 1000000
    opex_all = F_all_flat[:, 1] / (1000*problem.present_value)
    idx = np.argsort(pareto_front[:, 0])
    pf_sorted = pareto_front[idx]

    pareto_capex = pf_sorted[:, 0] / 1_000_000
    pareto_opex  = pf_sorted[:, 1] / (1000 * problem.present_value)

    plt.scatter(capex_all, opex_all, s=10, alpha=0.25, color='gray')
    plt.plot(pareto_capex, pareto_opex, '-o', markersize=4, linewidth=1.5, color='r')
    plt.xlabel('CAPEX (M€)')
    plt.ylabel('NPV OPEX (k€)')
    plt.title('Pareto Front')
    plt.show()
    timing_info = {
        "create": problem.t_modelcreate,
        "solve": res.exec_time,
        "export": 0,
    }
    
    solver_stats = {
        'iterations': res.algorithm.n_gen,
        'best_objective': pareto_front[balanced_idx],
        'time': res.exec_time,
        'termination_condition': 'optimal',
        'feasible_solutions': pareto_front.tolist()
    }
    
    # Add Pareto-specific information
    pareto_info = {
        'pareto_front': pareto_front,
        'pareto_solutions': pareto_solutions,
        'min_capex_solution': pareto_solutions[min_capex_idx],
        'min_opex_solution': pareto_solutions[min_opex_idx],
        'balanced_solution': pareto_solutions[balanced_idx],
        'min_capex_values': pareto_front[min_capex_idx],
        'min_opex_values': pareto_front[min_opex_idx],
        'balanced_values': pareto_front[balanced_idx]
    }
    
    return problem, pareto_info, timing_info, solver_stats


    