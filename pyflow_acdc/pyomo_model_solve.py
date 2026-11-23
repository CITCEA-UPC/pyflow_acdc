"""Generic Pyomo model solve: callbacks, log parsers, feasibility checks, progress export."""

import logging
import math
import re
import warnings

import pandas as pd
import pyomo.environ as pyo
from pyomo.opt import SolverStatus
from pyomo.util.infeasible import log_infeasible_constraints

try:
    import gurobipy  # noqa: F401
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False

from .solver_utils import pyomo_solver_factory_name

logger = logging.getLogger(__name__)

__all__ = [
    "pyomo_model_solve",
    "build_only_solver_stats",
    "reset_to_initialize",
    "export_solver_progress_to_excel",
    "log_infeasible_constraints_limited",
]


def build_only_solver_stats(solver=None, model=None):
    """Return ``(None, solver_stats)`` matching :func:`pyomo_model_solve` for ``build_only``."""
    return None, {
        "solver": solver,
        "iterations": None,
        "best_objective": None,
        "lower_bound": None,
        "time": 0.0,
        "termination_condition": "build_only",
        "solver_status": None,
        "solver_message": "build_only=True: model built and solve skipped.",
        "feasible_solutions": [],
        "all_solutions": [],
        "bound_solutions": [],
        "solution_found": False,
        "solution_check_info": None,
        "solution_check_reason": "build_only",
        "solution_check_tol": None,
        "obj_scaling": getattr(model, "obj_scaling", 1.0) if model is not None else 1.0,
    }

def log_infeasible_constraints_limited(model, max_per_type=5, tol=1e-6):
    """Print violated constraints in Pyomo-style ``INFO: CONSTR ... =/= 0.0`` form."""
    from collections import defaultdict

    from pyomo.core import Constraint

    def _as_float(val):
        if val is None:
            return None
        return float(pyo.value(val))

    print("=" * 80)
    print("INFEASIBLE CONSTRAINTS SUMMARY")
    print("=" * 80)

    constraint_groups = defaultdict(list)

    for constraint in model.component_objects(Constraint, active=True):
        constraint_name = constraint.name
        for index in constraint:
            try:
                con = constraint[index]
                body = _as_float(con.body)
                lower = _as_float(con.lower)
                upper = _as_float(con.upper)
                label = f"{constraint_name}[{index}]"

                if con.equality:
                    rhs = lower if lower is not None else 0.0
                    residual = body - rhs
                    if abs(residual) > tol:
                        constraint_groups[constraint_name].append(
                            f"INFO: CONSTR {label}: {residual} =/= 0.0"
                        )
                else:
                    if lower is not None and body < lower - tol:
                        constraint_groups[constraint_name].append(
                            f"INFO: CONSTR {label}: {body} </= {lower}"
                        )
                    if upper is not None and body > upper + tol:
                        constraint_groups[constraint_name].append(
                            f"INFO: CONSTR {label}: {body} >/= {upper}"
                        )
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                constraint_groups[constraint_name].append(
                    f"INFO: CONSTR {constraint_name}[{index}]: Unable to evaluate ({e})"
                )

    total_violations = 0
    for group_name, violations in constraint_groups.items():
        if not violations:
            continue
        print(f"\n{group_name}")
        print("-" * len(group_name))
        for violation in violations[:max_per_type]:
            print(f"  {violation}")
        if len(violations) > max_per_type:
            print(f"  ... and {len(violations) - max_per_type} other violations")
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
                logger.warning(f"Could not set Gurobi parameter {param_name}={param_value}: {e}")

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

def _parse_bonmin_log(log_path, bonmin_algorithm='B-BB'):
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
    algorithm = str(bonmin_algorithm or 'B-BB').strip().lower().replace('_', '-')
    parse_cbc0010_incumbent = ('hyb' in algorithm)
    last_cbc0010_best_solution = None

    try:
        with open(log_path) as f:
            for line in f:
                # Detect NLP table header; don't infer anything here
                if line.startswith('NLP0012I'):
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
                    node_match = re.search(r'After\s+(\d+)\s+nodes', line)
                    # Typical Cbc0010I format in Bonmin B-Hyb:
                    # "... <best_solution> best solution, best possible <best_bound> (<time> seconds)"
                    # Keep fallback for alternate ordering if encountered.
                    best_solution_match = re.search(
                        r'([-\d\.eE\+]+)\s+best solution,\s+best possible',
                        line,
                    )
                    if best_solution_match is None:
                        best_solution_match = re.search(
                            r'best solution,\s+([-\d\.eE\+]+)\s+best possible',
                            line,
                        )
                    bound_match = re.search(r'best possible\s+([-\d\.eE\+]+)', line)
                    time_match = re.search(r'\(([\d\.]+)\s+seconds\)', line)
                    if bound_match and time_match:
                        try:
                            best_bound = float(bound_match.group(1))
                            time_sec = float(time_match.group(1))
                            iterations = int(node_match.group(1)) if node_match else cumulative_iterations
                            bound_solutions.append((time_sec, best_bound, iterations))
                            if parse_cbc0010_incumbent and best_solution_match:
                                best_solution = float(best_solution_match.group(1))
                                is_new = (
                                    last_cbc0010_best_solution is None
                                    or best_solution != last_cbc0010_best_solution
                                )
                                all_solutions.append([time_sec, best_solution, iterations, last_nlp_call, is_new])
                                if is_new:
                                    feasible_solutions.append((time_sec, best_solution, iterations))
                                last_cbc0010_best_solution = best_solution
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

                        except (ValueError, TypeError, IndexError):
                            continue
    except (OSError, FileNotFoundError):
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
        with open(log_path) as f:
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

                except (ValueError, IndexError, TypeError):
                    continue

    except (OSError, FileNotFoundError):
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
    exit_acceptable = False
    exit_optimal = False

    try:
        with open(log_path) as f:
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
                        except (ValueError, IndexError):
                            continue

                # Capture EXIT status
                if 'EXIT: Optimal Solution Found' in line:
                    exit_optimal = True
                elif 'EXIT: Solved To Acceptable Level' in line:
                    exit_acceptable = True
    except (OSError, FileNotFoundError):
        pass

    # If IPOPT declared optimal or acceptable, ensure the final point is marked feasible
    if (exit_optimal or exit_acceptable) and progress_events:
        last_iter, last_obj, _, last_inf_pr, last_inf_du = progress_events[-1]
        progress_events[-1] = (last_iter, last_obj, True, last_inf_pr, last_inf_du)

    return progress_events

def _solver_progress(
    model,
    feasible_solutions,
    solver_name,
    time_limit,
    log_path,
    tee_console=True,
    solver_options=None,
):
    """Unified progress tracking for Ipopt, Bonmin, and HiGHS solvers.

    Always writes to log file for parsing. Uses Pyomo's tee parameter to control console output.
    """
    opt = pyo.SolverFactory(pyomo_solver_factory_name(solver_name))

    # Set time limit based on solver
    if time_limit is not None:
        if solver_name == 'ipopt':
            opt.options['max_cpu_time'] = time_limit
        elif solver_name == 'bonmin':
            opt.options['bonmin.time_limit'] = time_limit
        elif solver_name in ('highs', 'appsi_highs'):
            opt.options['time_limit'] = time_limit

    # Always configure solver to write to log file (for callback parsing)
    # Then use Pyomo's tee parameter to control console output
    if solver_name in ('highs', 'appsi_highs'):
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

    # Apply custom solver options in callback mode as well.
    # Keep internal flags (e.g., debug_solution_check) out of backend options.
    if solver_options:
        for param_name, param_value in solver_options.items():
            if param_name == 'debug_solution_check':
                continue
            opt.options[param_name] = param_value

    # Always write to log file, use Pyomo's tee to control console output.
    # For Bonmin/HiGHS, disable autoload so Pyomo does not raise when no
    # solution is available to load. We then load manually if a solution exists.
    solve_kwargs = {'tee': tee_console}
    if solver_name in ('bonmin', 'highs', 'appsi_highs'):
        solve_kwargs['load_solutions'] = False
    if solver_name == 'bonmin':
        solve_kwargs['logfile'] = log_path
    results = opt.solve(model, **solve_kwargs)

    # Manual incumbent recovery when autoload is disabled.
    if solver_name in ('bonmin', 'highs', 'appsi_highs'):
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
                logger.warning(f"Could not load incumbent solution from solver results: {exc}")

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
        bonmin_algorithm = 'B-BB'
        if solver_options:
            bonmin_algorithm = solver_options.get('bonmin.algorithm', bonmin_algorithm)
        parsed_feasible, parsed_all, parsed_bounds = _parse_bonmin_log(
            log_path,
            bonmin_algorithm=bonmin_algorithm,
        )
        feasible_solutions.extend(parsed_feasible)
        all_solutions.extend(parsed_all)
        bound_solutions.extend(parsed_bounds)
    elif solver_name in ('highs', 'appsi_highs'):
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
    """Persist latest Pyomo model results table on grid for Results.all()."""
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

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> model = pyo.ConcreteModel()
    >>> grid = pyf.Grid(S_base=100)
    >>> opf_create_nl_model_acdc(model, grid, PV_set=False, Price_Zones=False)
    >>> results, solver_stats = pyf.pyomo_model_solve(model, grid)
    """
    solver = solver.lower()
    if solver == 'maingo':
        solver = 'appsi_maingo'
    # Keep internal flags separate from backend solver options.
    solver_options = dict(solver_options) if solver_options else None
    feasible_solutions = []  # Always defined, but only populated if callback is used
    all_solutions = []  # Always defined, but only populated if callback is used
    bound_solutions = []  # Best-bound updates from callback log parsing
    (solver_options or {}).pop("debug_solution_check", None)  # internal flag, not a solver option

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
        warnings.warn('pyflow-acdc is not capable of ensuring the reliability of this solution.')

    if callback:
        if solver == 'gurobi' and GUROBI_AVAILABLE:
            results, feasible_solutions, bound_solutions = _gurobi_callback(model, feasible_solutions, bound_solutions, time_limit, solver_options, tee=tee)
            # For Gurobi, all_solutions is the same as feasible_solutions
            all_solutions = feasible_solutions.copy()
        elif solver == 'bonmin':
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(model, feasible_solutions, 'bonmin', time_limit, 'bonmin.log', tee_console=tee, solver_options=solver_options)
        elif solver == 'ipopt':
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(model, feasible_solutions, 'ipopt', time_limit, 'ipopt.log', tee_console=tee, solver_options=solver_options)
        elif solver in ('highs', 'appsi_highs'):
            results, feasible_solutions, all_solutions, bound_solutions = _solver_progress(
                model, feasible_solutions, solver, time_limit, f'{solver}.log',
                tee_console=tee, solver_options=solver_options,
            )
        else:
            warnings.warn(f"No callback available for {solver}")
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
            opt = pyo.SolverFactory(pyomo_solver_factory_name(solver))

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
            elif solver in ('highs', 'appsi_highs'):
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
            logger.error(f"Solver crashed: {e}")

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
        'solver_status': str(getattr(results.solver, 'status', '') or '') if results else None,
        'solver_message': solver_message,
        'feasible_solutions': feasible_solutions,
        'all_solutions': all_solutions,
        'bound_solutions': bound_solutions,
        'solution_found': None,  # Set below from feasibility validation
        'solution_check_info': None,
        'obj_scaling': obj_scaling,
    }

    # Decision policy for solution_found:
    # 1) If solver termination is optimal/acceptable/feasible/maxTimeLimit, trust solver.
    # 2) User interrupt / aborted with a loaded incumbent counts as solution_found.
    # 3) Otherwise validate loaded values with the quick point check.
    try:
        tc = str(getattr(results.solver, 'termination_condition', '') or '').lower() if results is not None else ''
    except AttributeError:
        tc = ''
    solver_message_lc = solver_message.lower()
    solver_status_lc = str((solver_stats or {}).get('solver_status') or '').lower()
    solver_name_lc = str(solver).lower() if solver is not None else ''
    trusted_termination = tc in (
        'optimal',
        'feasible',
        'locallyoptimal',
        'acceptable',
        'locally_optimal',
        'maxiterations',
        'maxtimelimit',
    )
    explicit_infeasible_termination = tc in (
        'infeasible',
        'locallyinfeasible',
        'infeasibleorunbounded',
        'infeasible_or_unbounded',
    )
    # Hard-fail solver/system errors even when a partial solution payload exists.
    explicit_error_termination = tc in (
        'internalsolvererror',
        'solvererror',
        'error',
        'aborted',
        'invalidproblem',
    )
    # Guard against false positives from relaxed acceptance logic:
    # unbounded outcomes must always be rejected.
    explicit_unbounded_termination = (
        ('unbounded' in tc)
        or ('unbounded' in solver_message_lc)
        or ('continuous relaxation is unbounded' in solver_message_lc)
    )
    # Treat IPOPT maxIterations as explicit non-favorable termination.
    if solver_name_lc == 'ipopt' and tc == 'maxiterations':
        trusted_termination = False
        explicit_infeasible_termination = True

    # Ctrl-C / user abort: Gurobi often returns status aborted / tc error while
    # leaving a usable incumbent on the model. Accept that incumbent below.
    user_interrupt = (
        'terminated by the user' in solver_message_lc
        or 'interrupted by the user' in solver_message_lc
        or 'interrupted by user' in solver_message_lc
        or 'user interrupt' in solver_message_lc
        or solver_status_lc == 'aborted'
        or tc == 'aborted'
    )
    if user_interrupt:
        explicit_error_termination = False

    if (
        'aborted' in solver_message_lc
        or 'error in step computation' in solver_message_lc
        or 'error encountered in optimization' in solver_message_lc
        or 'dynamic_library_failure' in solver_message_lc
        or 'library loading failure' in solver_message_lc
        or 'cannot open shared object file' in solver_message_lc
        or 'libhsl.so' in solver_message_lc
    ):
        if not user_interrupt:
            explicit_error_termination = True

    # Some solver interfaces return termination_condition="other" for hard solver failures.
    # Promote those cases to explicit error so callers can catch them deterministically.
    if tc == 'other':
        if solver_status_lc in ('error', 'aborted') and not user_interrupt:
            explicit_error_termination = True
            solver_stats['termination_condition'] = 'error'
        elif (
            'dynamic_library_failure' in solver_message_lc
            or 'library loading failure' in solver_message_lc
            or 'cannot open shared object file' in solver_message_lc
            or 'libhsl.so' in solver_message_lc
        ):
            explicit_error_termination = True
            solver_stats['termination_condition'] = 'error'

        # If callback mode was used, analyze the last Ipopt iteration from the log
        # to measure how close we are to acceptable feasibility with default tolerances.
        if callback:
            try:
                events = _parse_ipopt_log('ipopt.log')
            except Exception:
                events = []
            if events:
                last_iter, last_obj, last_feas, last_inf_pr, last_inf_du = events[-1]
                # Align max-iteration acceptance with IPOPT acceptable tolerances when provided.
                acceptable_pr_raw = (solver_options or {}).get('acceptable_constr_viol_tol', 1e-4)
                acceptable_du_raw = (solver_options or {}).get('acceptable_dual_inf_tol', 1e-6)
                try:
                    acceptable_pr_tol = float(acceptable_pr_raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid IPOPT acceptable_constr_viol_tol: {acceptable_pr_raw!r}"
                    ) from exc
                try:
                    acceptable_du_tol = float(acceptable_du_raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid IPOPT acceptable_dual_inf_tol: {acceptable_du_raw!r}"
                    ) from exc
                within_acc_pr = bool(last_inf_pr <= acceptable_pr_tol)
                within_acc_du = bool(last_inf_du <= acceptable_du_tol)
                # If both primal and dual are within these strict tolerances,
                # pyflow-acdc takes this maxIterations point as an acceptable solution.
                if within_acc_pr and within_acc_du:
                    trusted_termination = True
                    explicit_infeasible_termination = False
                if tee and not suppress_warnings:
                    print(
                        "[pyomo_model_solve] Ipopt maxIterations: "
                        f"last_iter={last_iter}, inf_pr={last_inf_pr:.3e}, inf_du={last_inf_du:.3e}, "
                        f"within_acc_pr({acceptable_pr_tol:.3e})={within_acc_pr}, "
                        f"within_acc_du({acceptable_du_tol:.3e})={within_acc_du}"
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
    except (AttributeError, TypeError):
        has_loaded_solution = False

    # Empty results.solution is normal for some integrations (e.g. Gurobi
    # persistent callback loads vars via load_vars() without populating
    # results.solution). Warn only when the payload is missing and model
    # variables were not loaded either.
    has_model_values = has_loaded_solution
    if not has_model_values:
        has_model_values, _ = _quick_feasible_point_check(model, check_integrality=False)

    bnb_like_solvers = {"bonmin", "couenne", "scip", "cbc", "cplex", "gurobi"}
    should_warn_missing_payload = (
        not suppress_warnings
        and trusted_termination
        and not has_loaded_solution
        and not has_model_values
        and solver_name_lc in bnb_like_solvers
    )
    if should_warn_missing_payload:
        pyomo_logger = logging.getLogger('pyomo')
        pyomo_logger.warning(
            "Solver termination indicates a good solve ('%s'), but no solution payload "
            "was loaded by Pyomo (len(results.solution)=0). This can indicate a "
            "solver/Pyomo/ASL installation or compatibility issue. Proceeding with "
            "termination-based acceptance.",
            tc,
        )

    if explicit_unbounded_termination:
        loaded_solution_feasible = False
        checker_reason = "explicit_unbounded_termination"
    elif explicit_infeasible_termination:
        loaded_solution_feasible = False
        checker_reason = "explicit_infeasible_termination"
    elif explicit_error_termination:
        loaded_solution_feasible = False
        checker_reason = "explicit_error_termination"
    elif user_interrupt and (has_loaded_solution or has_model_values):
        loaded_solution_feasible = True
        checker_reason = "user_interrupt_with_incumbent"
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

    if tee and explicit_infeasible_termination:
        try:
            log_infeasible_constraints_limited(model)
        except Exception as exc:
            pyomo_logger.warning("Skipping limited infeasible-constraint logging due to error: %s", exc)

    _store_pyomo_results_on_grid(grid, model, results, solver_stats)
    return results, solver_stats
def export_solver_progress_to_excel(solver_stats, save_path):
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
