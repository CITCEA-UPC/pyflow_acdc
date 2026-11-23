"""
OR-Tools (linear_solver) linear AC OPF model for cable size selection (CSS).

Selects cable types on CT lines with a fixed inter-array topology
(``line.active_config >= 0`` set beforehand, typically by ``MIP_path_graph``).
Does not choose routes, spanning trees, or node connection counts — those
belong to the path MIP in ``Array_OPT``.

Uses CBC via ``ortools.linear_solver`` (no Pyomo/Gurobi license required).
"""

import time

import numpy as np

__all__ = ['optimal_l_css_ortools']

from ..ACDC_OPF import calculate_objective, obj_w_rule
from ..constants import (
    CT_SELECTION_THRESHOLD,
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_TIME_LIMIT,
    HOURS_PER_YEAR,
    ORTOOLS_LINEAR_SOLVERS,
    ObjComponent,
    present_value_factor,
)
from ..grid_analysis import analyse_grid, get_gen_p_min_eff

try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_LP_AVAILABLE = True
except ImportError:
    ORTOOLS_LP_AVAILABLE = False


# ── Main entry point ────────────────────────────────────────────────────────

def optimal_l_css_ortools(grid, ObjRule=None, NPV=True, n_years=25, Hy=HOURS_PER_YEAR,
                          discount_rate=DEFAULT_DISCOUNT_RATE, tee=False,
                          time_limit=DEFAULT_TIME_LIMIT, solver_name=None):
    """Build and solve the linear CSS model with OR-Tools ``linear_solver``.

    Cable size selection only: one cable type per active CT line, with optional
    discounted array-loss OPEX. The inter-array route must already be fixed on
    ``grid`` (e.g. after ``MIP_path_graph``); this function does not optimize
    topology.

    Parameters
    ----------
    grid : Grid
        Network with ``CT_AC`` and candidate cable options (mutated in place).
    ObjRule : dict or None, optional
        Objective-component weights for OPEX (e.g. ``{'Array_losses': 1}``).
    NPV : bool, optional
        Discount OPEX with ``present_value_factor`` over ``n_years``.
    n_years, Hy, discount_rate : optional
        Planning horizon and economics for NPV OPEX.
    tee : bool, optional
        Stream solver log output.
    time_limit : float, optional
        Solver time limit in seconds.
    solver_name : str or None, optional
        OR-Tools MILP backend (e.g. ``'GUROBI'``, ``'SCIP'``, ``'CBC'``).
        ``None`` tries :data:`~pyflow_acdc.constants.ORTOOLS_LINEAR_SOLVERS` in order.

    Returns
    -------
    tuple
        ``(solver, model_res, timing_info, solver_stats)``.
    """
    if not ORTOOLS_LP_AVAILABLE:
        raise ImportError(
            "OR-Tools is not installed. Install with: pip install ortools"
        )

    analyse_grid(grid)
    if not grid.CT_AC:
        raise ValueError("No conductor size selection connections found in the grid")

    weights_def, _ = obj_w_rule(grid, ObjRule)

    model_res = None
    solver_stats = None
    solver = None
    gen_vars = None
    ac_vars = None
    used_solver = None
    t_modelcreate = 0.0
    t3 = time.perf_counter()

    for try_name in ((solver_name,) if solver_name else ORTOOLS_LINEAR_SOLVERS):
        solver = pywraplp.Solver.CreateSolver(try_name)
        if solver is None:
            continue
        used_solver = try_name
        t1 = time.perf_counter()
        gen_vars, ac_vars, gen_info, AC_info = opf_create_l_model_ac_ortools(solver, grid)
        t2 = time.perf_counter()
        t_modelcreate = t2 - t1

        set_objective_ortools(solver, grid, gen_vars, ac_vars, gen_info, AC_info,
                              weights_def, NPV, n_years, Hy, discount_rate)

        solver.SetTimeLimit(int(time_limit * 1000))
        if tee:
            solver.EnableOutput()

        model_res, solver_stats = solve_ortools_model(solver, grid, tee)
        if solver_stats.get('solution_found'):
            break

    t4 = time.perf_counter()
    if solver is None or model_res is None:
        tried = (solver_name,) if solver_name else ORTOOLS_LINEAR_SOLVERS
        raise RuntimeError(
            f"Could not create any OR-Tools MILP solver (tried: {', '.join(tried)})"
        )

    solver_stats['css_solver'] = used_solver

    model_res['gen_vars'] = gen_vars
    model_res['ac_vars'] = ac_vars

    if solver_stats.get('solution_found'):
        export_acdc_l_model_to_pyflow_acdc_ortools(solver, grid, gen_vars, ac_vars,
                                                tee=tee, time_limit=time_limit)

    present_value = present_value_factor(Hy, discount_rate, n_years)
    for obj_key in weights_def:
        weights_def[obj_key]['v'] = calculate_objective(grid, obj_key)
        weights_def[obj_key]['NPV'] = weights_def[obj_key]['v'] * present_value
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

    return solver, model_res, timing_info, solver_stats


# ── Solver wrapper ──────────────────────────────────────────────────────────

def solve_ortools_model(solver, grid, tee=False):
    """Solve the model and return results + stats."""
    t_start = time.perf_counter()
    try:
        status = solver.Solve()
        solve_time = time.perf_counter() - t_start

        status_map = {
            pywraplp.Solver.OPTIMAL: 'optimal',
            pywraplp.Solver.FEASIBLE: 'feasible',
            pywraplp.Solver.INFEASIBLE: 'infeasible',
            pywraplp.Solver.UNBOUNDED: 'unbounded',
            pywraplp.Solver.NOT_SOLVED: 'not_solved',
            pywraplp.Solver.ABNORMAL: 'abnormal',
        }
        status_str = status_map.get(status, f'other_{status}')

        obj_val = solver.Objective().Value() if status in (
            pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else None

        solution_found = status in (
            pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)

        model_res = {
            'status': status_str,
            'objective_value': obj_val,
            'solver_time': solve_time,
            'solution_found': solution_found,
            'Solver': [{'Status': 'ok' if solution_found else status_str}],
        }
        solver_stats = {
            'time': solve_time,
            'status': status_str,
            'termination_condition': status_str,
            'solution_found': solution_found,
            'iterations': solver.iterations(),
            'nodes': solver.nodes(),
            'feasible_solutions': [],
        }
    except Exception as e:
        model_res = {
            'status': 'error',
            'error_message': str(e),
            'objective_value': None,
            'solver_time': None,
            'solution_found': False,
            'Solver': [{'Status': 'error'}],
        }
        solver_stats = {
            'time': None,
            'status': 'error',
            'termination_condition': 'error',
            'solution_found': False,
            'error_message': str(e),
            'feasible_solutions': [],
        }

    return model_res, solver_stats


# ── Model creation ──────────────────────────────────────────────────────────

def opf_create_l_model_ac_ortools(solver, grid):
    """Build the linear AC OPF model inside *solver*."""
    from ..ACDC_OPF import translate_pyf_opf

    opf_data = translate_pyf_opf(grid, False)
    AC_info = opf_data['AC_info']
    gen_info = opf_data['gen_info']

    gen_vars = Generation_variables_ortools(solver, grid, gen_info)
    ac_vars = AC_variables_ortools(solver, grid, AC_info)
    AC_constraints_ortools(solver, grid, AC_info, gen_info, gen_vars, ac_vars)

    return gen_vars, ac_vars, gen_info, AC_info


# ── Variables ───────────────────────────────────────────────────────────────

def Generation_variables_ortools(solver, grid, gen_info):
    """Create generation decision variables."""

    gen_AC_info, _, gen_rs_info = gen_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info
    lf, qf, fc, np_gen, lista_gen = gen_AC_info

    variables = {}

    # Renewable curtailment factor
    variables['gamma'] = {}
    for rs in lista_rs:
        ren_source = grid.RenSources[rs]
        if ren_source.curtailable:
            lb, ub = ren_source.min_gamma, 1.0
        else:
            lb, ub = 1.0, 1.0
        variables['gamma'][rs] = solver.NumVar(lb, ub, f'gamma_{rs}')

    # AC generators (same bounds as Pyomo P_Gen_bounds / get_gen_p_min_eff)
    variables['PGi_gen'] = {}
    for g in lista_gen:
        gen = grid.Generators[g]
        p_lb = get_gen_p_min_eff(gen, gen.np_gen)
        p_ub = gen.Max_pow_gen * gen.np_gen
        variables['PGi_gen'][g] = solver.NumVar(p_lb, p_ub, f'PGi_gen_{g}')

    return variables


def AC_variables_ortools(solver, grid, AC_info):
    """Create AC network decision variables."""
    AC_Lists, AC_nodes_info, AC_lines_info, EXP_info, REC_info, CT_info = AC_info
    lista_nodos_AC, lista_lineas_AC, lista_lineas_AC_tf, AC_slack, AC_PV = AC_Lists
    S_lineAC_limit = AC_lines_info[0]

    lista_lineas_AC_ct, S_lineACct_lim, cab_types_set, allowed_types = CT_info

    ac_vars = {}
    infinity = solver.infinity()

    # ── Cable-type binary variables ──────────────────────────────────────
    ac_vars['ct_types'] = {}
    for ct in cab_types_set:
        ac_vars['ct_types'][ct] = solver.BoolVar(f'ct_types_{ct}')

    ac_vars['ct_branch'] = {}
    for line in lista_lineas_AC_ct:
        for ct in cab_types_set:
            ac_vars['ct_branch'][line, ct] = solver.BoolVar(
                f'ct_branch_{line}_{ct}')

    # ── Voltage angles ───────────────────────────────────────────────────
    ac_vars['theta_AC'] = {}
    for node in lista_nodos_AC:
        ac_vars['theta_AC'][node] = solver.NumVar(
            -1.6, 1.6, f'theta_AC_{node}')

    # ── Nodal power variables (match Pyomo None, None where unbounded) ───
    ac_vars['PGi_opt'] = {}
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if nAC.connected_gen:
            ac_vars['PGi_opt'][node] = solver.NumVar(
                -infinity, infinity, f'PGi_opt_{node}')
        else:
            ac_vars['PGi_opt'][node] = solver.NumVar(0, 0, f'PGi_opt_{node}')

    ac_vars['PGi_ren'] = {}
    for node in lista_nodos_AC:
        if grid.nodes_AC[node].connected_RenSource:
            ac_vars['PGi_ren'][node] = solver.NumVar(
                -infinity, infinity, f'PGi_ren_{node}')
        else:
            ac_vars['PGi_ren'][node] = solver.NumVar(0, 0, f'PGi_ren_{node}')

    # ── CT power injection aggregates per node ───────────────────────────
    ac_vars['Pto_CT'] = {}
    ac_vars['Pfrom_CT'] = {}
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if nAC.connected_toCTLine or nAC.connected_fromCTLine:
            ac_vars['Pto_CT'][node] = solver.NumVar(
                -infinity, infinity, f'Pto_CT_{node}')
            ac_vars['Pfrom_CT'][node] = solver.NumVar(
                -infinity, infinity, f'Pfrom_CT_{node}')
        else:
            ac_vars['Pto_CT'][node] = solver.NumVar(0, 0, f'Pto_CT_{node}')
            ac_vars['Pfrom_CT'][node] = solver.NumVar(0, 0, f'Pfrom_CT_{node}')

    # ── Standard AC line flows ───────────────────────────────────────────
    ac_vars['PAC_to'] = {}
    ac_vars['PAC_from'] = {}
    for line in lista_lineas_AC:
        lim = S_lineAC_limit[line]
        ac_vars['PAC_to'][line] = solver.NumVar(-lim, lim, f'PAC_to_{line}')
        ac_vars['PAC_from'][line] = solver.NumVar(-lim, lim, f'PAC_from_{line}')

    # ── CT line power flows per cable type + McCormick helpers ───────────
    ac_vars['ct_PAC_to'] = {}
    ac_vars['ct_PAC_from'] = {}
    ac_vars['z_to'] = {}
    ac_vars['z_from'] = {}
    for line in lista_lineas_AC_ct:
        l = grid.lines_AC_ct[line]
        line_max = max(S_lineACct_lim[line, ct] for ct in cab_types_set)
        for ct in cab_types_set:
            # ct_PAC: unbounded like Pyomo (limits enter via McCormick on z only)
            ac_vars['ct_PAC_to'][line, ct] = solver.NumVar(
                -infinity, infinity, f'ct_PAC_to_{line}_{ct}')
            ac_vars['ct_PAC_from'][line, ct] = solver.NumVar(
                -infinity, infinity, f'ct_PAC_from_{line}_{ct}')
            if l.active_config < 0:
                z_lb, z_ub = 0.0, 0.0
            else:
                z_lb, z_ub = -line_max, line_max
            ac_vars['z_to'][line, ct] = solver.NumVar(
                z_lb, z_ub, f'z_to_{line}_{ct}')
            ac_vars['z_from'][line, ct] = solver.NumVar(
                z_lb, z_ub, f'z_from_{line}_{ct}')

    return ac_vars


# ── Constraints ─────────────────────────────────────────────────────────────

def AC_constraints_ortools(solver, grid, AC_info, gen_info, gen_vars, ac_vars):
    """Add all constraints to the OR-Tools model."""
    AC_Lists, AC_nodes_info, AC_lines_info, EXP_info, REC_info, CT_info = AC_info
    lista_nodos_AC, lista_lineas_AC, lista_lineas_AC_tf, AC_slack, AC_PV = AC_Lists
    lista_lineas_AC_ct, S_lineACct_lim, cab_types_set, allowed_types = CT_info

    gen_AC_info, _, gen_rs_info = gen_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info
    _, _, _, _, P_know, _, _ = AC_nodes_info

    max_cable_limits = {
        line: max(S_lineACct_lim[line, ct] for ct in cab_types_set)
        for line in lista_lineas_AC_ct}

    Ybus = grid.Ybus_AC

    # ── Slack reference bus ──────────────────────────────────────────────
    for node in AC_slack:
        solver.Add(ac_vars['theta_AC'][node] == 0, f'AC_theta_slack_{node}')

    # ── Nodal balance (Ybus DC + known injections + CT aggregates) ───────
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]

        p_sum = sum(
            -np.imag(Ybus[node, k]) * (ac_vars['theta_AC'][node] - ac_vars['theta_AC'][k])
            for k in lista_nodos_AC if Ybus[node, k] != 0)
        p_rhs = (P_know[node]
                 + ac_vars['PGi_ren'][node]
                 + ac_vars['PGi_opt'][node])
        p_rhs += ac_vars['Pto_CT'][node] + ac_vars['Pfrom_CT'][node]
        solver.Add(p_sum == p_rhs, f'power_balance_{node}')

        # Generator power link
        gen_power = sum(gen_vars['PGi_gen'][g.genNumber]
                        for g in nAC.connected_gen)
        solver.Add(ac_vars['PGi_opt'][node] == gen_power,
                    f'gen_power_{node}')

        # Renewable power link
        ren_power = sum(P_renSource[rs.rsNumber]
                        * gen_vars['gamma'][rs.rsNumber]
                        * np_rsgen[rs.rsNumber]
                        for rs in nAC.connected_RenSource)
        solver.Add(ac_vars['PGi_ren'][node] == ren_power,
                    f'ren_power_{node}')

        # CT injection sums
        to_ct_sum = sum(ac_vars['z_to'][line.lineNumber, ct]
                        for line in nAC.connected_toCTLine
                        for ct in cab_types_set)
        solver.Add(ac_vars['Pto_CT'][node] == to_ct_sum,
                    f'to_ct_{node}')

        from_ct_sum = sum(ac_vars['z_from'][line.lineNumber, ct]
                          for line in nAC.connected_fromCTLine
                          for ct in cab_types_set)
        solver.Add(ac_vars['Pfrom_CT'][node] == from_ct_sum,
                    f'from_ct_{node}')

    # ── Standard AC line flow (DC power-flow approximation) ─────────────
    for line in lista_lineas_AC:
        l = grid.lines_AC[line]
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        B_to = np.imag(l.Ybus_branch[1, 0])
        B_from = np.imag(l.Ybus_branch[0, 1])

        solver.Add(
            ac_vars['PAC_to'][line]
            == -B_to * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]),
            f'power_flow_to_{line}')
        solver.Add(
            ac_vars['PAC_from'][line]
            == -B_from * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]),
            f'power_flow_from_{line}')

    # ── Cable-type selection constraints ─────────────────────────────────
    # Global limit on number of distinct cable types
    solver.Add(
        sum(ac_vars['ct_types'][ct] for ct in cab_types_set)
        <= grid.cab_types_allowed,
        'CT_limit_rule')
    solver.Add(
        sum(ac_vars['ct_types'][ct] for ct in cab_types_set) >= 1,
        'CT_limit_lower_rule')

    # Upper bound: type selected only if at least one line uses it
    for ct in cab_types_set:
        solver.Add(
            sum(ac_vars['ct_branch'][line, ct] for line in lista_lineas_AC_ct)
            <= len(lista_lineas_AC_ct) * ac_vars['ct_types'][ct],
            f'ct_types_upper_bound_{ct}')

    # Lower bound: if any line uses this type, type must be selected
    for ct in cab_types_set:
        solver.Add(
            ac_vars['ct_types'][ct]
            <= sum(ac_vars['ct_branch'][line, ct] for line in lista_lineas_AC_ct),
            f'ct_types_lower_bound_{ct}')

    # Exactly one cable type per active CT line (fixed topology from route MIP)
    for line in lista_lineas_AC_ct:
        ct_vars = sum(ac_vars['ct_branch'][line, ct] for ct in cab_types_set)
        l = grid.lines_AC_ct[line]
        if l.active_config >= 0:
            solver.Add(ct_vars == 1, f'ct_cable_type_rule_{line}')
        else:
            solver.Add(ct_vars == 0, f'ct_cable_type_rule_{line}')

    # ── DC power-flow equality + McCormick envelopes for CT lines ────────
    for line in lista_lineas_AC_ct:
        l = grid.lines_AC_ct[line]
        M = max_cable_limits[line] * 1.1
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber

        if l.active_config < 0:
            for ct in cab_types_set:
                solver.Add(ac_vars['ct_PAC_to'][line, ct] == 0,
                           f'ct_pf_to_zero_{line}_{ct}')
                solver.Add(ac_vars['ct_PAC_from'][line, ct] == 0,
                           f'ct_pf_from_zero_{line}_{ct}')
        else:
            for ct in cab_types_set:
                B_to = np.imag(l.Ybus_list[ct][1, 0])
                B_from = np.imag(l.Ybus_list[ct][0, 1])
                solver.Add(
                    ac_vars['ct_PAC_to'][line, ct]
                    == -B_to * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]),
                    f'ct_pf_to_{line}_{ct}')
                solver.Add(
                    ac_vars['ct_PAC_from'][line, ct]
                    == -B_from * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]),
                    f'ct_pf_from_{line}_{ct}')

        for ct in cab_types_set:
            solver.Add(
                ac_vars['z_to'][line, ct]
                <= ac_vars['ct_PAC_to'][line, ct]
                + (1 - ac_vars['ct_branch'][line, ct]) * (2 * M),
                f'z_to_ub_{line}_{ct}')
            solver.Add(
                ac_vars['z_to'][line, ct]
                >= ac_vars['ct_PAC_to'][line, ct]
                - (1 - ac_vars['ct_branch'][line, ct]) * (2 * M),
                f'z_to_lb_{line}_{ct}')
            solver.Add(
                ac_vars['z_to'][line, ct]
                <= S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                f'z_to_branch_ub_{line}_{ct}')
            solver.Add(
                ac_vars['z_to'][line, ct]
                >= -S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                f'z_to_branch_lb_{line}_{ct}')

            # McCormick envelopes for z_from = ct_branch * ct_PAC_from
            solver.Add(
                ac_vars['z_from'][line, ct]
                <= ac_vars['ct_PAC_from'][line, ct]
                + (1 - ac_vars['ct_branch'][line, ct]) * (2 * M),
                f'z_from_ub_{line}_{ct}')
            solver.Add(
                ac_vars['z_from'][line, ct]
                >= ac_vars['ct_PAC_from'][line, ct]
                - (1 - ac_vars['ct_branch'][line, ct]) * (2 * M),
                f'z_from_lb_{line}_{ct}')
            solver.Add(
                ac_vars['z_from'][line, ct]
                <= S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                f'z_from_branch_ub_{line}_{ct}')
            solver.Add(
                ac_vars['z_from'][line, ct]
                >= -S_lineACct_lim[line, ct] * ac_vars['ct_branch'][line, ct],
                f'z_from_branch_lb_{line}_{ct}')


# ── Objective ───────────────────────────────────────────────────────────────

def set_objective_ortools(solver, grid, gen_vars, ac_vars, gen_info, AC_info,
                          weights_def, NPV=True, n_years=25, Hy=HOURS_PER_YEAR,
                          discount_rate=DEFAULT_DISCOUNT_RATE):
    """Set the minimisation objective (investment + array-loss OPEX)."""
    AC_Lists, *_ = AC_info
    _, _, _, AC_slack, _ = AC_Lists

    objective = solver.Objective()
    objective.SetMinimization()

    # Investment cost
    for (l, ct), ct_branch_var in ac_vars['ct_branch'].items():
        line = grid.lines_AC_ct[l]
        if line.array_opf:
            cost = line.base_cost[ct]
            if not NPV:
                cost /= line.life_time_hours
            objective.SetCoefficient(ct_branch_var, cost)

    # Array-loss OPEX: (ren_injected + slack_extraction) * LCoE * S_base
    # Slack PGi_opt is negative on export, so input + output = losses.
    if weights_def[ObjComponent.ARRAY_LOSSES]['w'] != 0:
        present_value = 1.0
        if NPV:
            present_value = present_value_factor(Hy, discount_rate, n_years)
        coef = (grid.LCoE * grid.S_base * present_value
                * weights_def[ObjComponent.ARRAY_LOSSES]['w'])
        _, _, gen_rs_info = gen_info
        P_renSource, np_rsgen, lista_rs = gen_rs_info
        ren_injected = sum(
            P_renSource[rs] * np_rsgen[rs] for rs in lista_rs)
        objective.SetOffset(ren_injected * coef)
        for node in AC_slack:
            objective.SetCoefficient(ac_vars['PGi_opt'][node], coef)


# ── Export results back to grid ─────────────────────────────────────────────

def export_acdc_l_model_to_pyflow_acdc_ortools(solver, grid, gen_vars, ac_vars,
                                             tee=True, time_limit=None):
    """Write solver results into the pyflow_acdc grid object.

    Must be called *after* ``solve_ortools_model`` – solution values are
    cached and accessible via ``.solution_value()`` without re-solving.
    """
    cab_types_set = sorted({ct for (_, ct) in ac_vars['ct_branch']})
    grid.OPF_run = True

    # Generation
    for g in grid.Generators:
        g.PGen = gen_vars['PGi_gen'][g.genNumber].solution_value()
        g.QGen = 0.0

    # Renewable sources
    for rs in grid.RenSources:
        rs.gamma = gen_vars['gamma'][rs.rsNumber].solution_value()
        rs.QGi_ren = 0.0

    # AC bus
    grid.V_AC = np.ones(grid.nn_AC)
    grid.Theta_V_AC = np.zeros(grid.nn_AC)

    for node in grid.nodes_AC:
        nAC = node.nodeNumber
        node.V = 1.0
        node.theta = ac_vars['theta_AC'][nAC].solution_value()
        node.PGi_opt = ac_vars['PGi_opt'][nAC].solution_value()
        node.QGi_opt = 0.0
        node.PGi_ren = ac_vars['PGi_ren'][nAC].solution_value()
        node.QGi_ren = 0.0
        grid.Theta_V_AC[nAC] = node.theta

    # Power injections (DC power-flow)
    B = np.imag(grid.Ybus_AC)
    Theta = grid.Theta_V_AC
    Theta_diff = Theta[:, None] - Theta
    Pf_DC = (-B * Theta_diff).sum(axis=1)

    for node in grid.nodes_AC:
        i = node.nodeNumber
        node.P_INJ = Pf_DC[i]
        node.Q_INJ = 0.0

    # CT lines
    for line in grid.lines_AC_ct:
        ct_selected = [
            ac_vars['ct_branch'][line.lineNumber, ct].solution_value()
            >= CT_SELECTION_THRESHOLD
            for ct in cab_types_set]
        if any(ct_selected):
            sel_i = int(np.where(ct_selected)[0][0])
            line.active_config = cab_types_set[sel_i]
            ct = cab_types_set[sel_i]
            line.fromS = (ac_vars['ct_PAC_from'][line.lineNumber, ct]
                          .solution_value() + 1j * 0)
            line.toS = (ac_vars['ct_PAC_to'][line.lineNumber, ct]
                        .solution_value() + 1j * 0)
        else:
            line.active_config = -1
            line.fromS = 0 + 1j * 0
            line.toS = 0 + 1j * 0
        line.loss = 0
        line.P_loss = 0
        line.network_flow = 0.0

    grid.Cable_options[0].active_config = {
        ct: ac_vars['ct_types'][ct].solution_value()
        for ct in ac_vars['ct_types']
    }

    # Standard AC lines
    Theta = grid.Theta_V_AC
    for line in grid.lines_AC:
        i = line.fromNode.nodeNumber
        j = line.toNode.nodeNumber
        B_val = -np.imag(line.Ybus_branch[0, 1])
        P_ij = B_val * (Theta[i] - Theta[j])
        P_ji = B_val * (Theta[j] - Theta[i])
        line.fromP = P_ij
        line.toP = P_ji
        line.toS = P_ji + 1j * 0
        line.fromS = P_ij + 1j * 0
        line.P_loss = 0
        line.loss = 0
        line.i_from = abs(P_ij)
        line.i_to = abs(P_ji)

    # Fix oversizing if solver hit time limit (wall_time is milliseconds)
    if (time_limit is not None
            and solver.wall_time() >= int(time_limit * 1000 * 0.99)):
        try:
            from .AC_OPF_L_model import analyze_oversizing_issues_grid, apply_oversizing_fixes_grid
            oversizing_type1, oversizing_type2 = analyze_oversizing_issues_grid(
                grid, tee=tee)
            apply_oversizing_fixes_grid(grid, oversizing_type1,
                                        oversizing_type2, tee=tee)
        except ImportError:
            pass
