# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2026

@author: BernardoCastro
OR-Tools (linear_solver) version of AC OPF Linear Model for Cable Size Selection.
Only considers CT lines (no expansion or reconductoring).
"""

import numpy as np
import time

__all__ = ['Optimal_L_CSS_ortools']

from .ACDC_OPF import obj_w_rule, calculate_objective
from .grid_analysis import analyse_grid
from .constants import HOURS_PER_YEAR, DEFAULT_DISCOUNT_RATE, DEFAULT_TIME_LIMIT

try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_LP_AVAILABLE = True
except ImportError:
    ORTOOLS_LP_AVAILABLE = False


# ── Main entry point ────────────────────────────────────────────────────────

def Optimal_L_CSS_ortools(grid, OPEX=True, NPV=True, n_years=25, Hy=HOURS_PER_YEAR,
                          discount_rate=DEFAULT_DISCOUNT_RATE, tee=False, time_limit=DEFAULT_TIME_LIMIT):
    """Main function to create and solve OR-Tools linear_solver model.

    Equivalent to ``Optimal_L_CSS_gurobi`` but uses the open-source
    ``ortools.linear_solver`` back-end (CBC by default).
    Only CT lines are considered (no expansion / reconductoring).
    """
    if not ORTOOLS_LP_AVAILABLE:
        raise ImportError(
            "OR-Tools is not installed. Install with: pip install ortools"
        )

    analyse_grid(grid)
    if not grid.CT_AC:
        raise ValueError("No conductor size selection connections found in the grid")

    # Create solver – CBC is bundled with OR-Tools, no extra install needed
    solver = pywraplp.Solver.CreateSolver('CBC')
    if solver is None:
        raise RuntimeError("Could not create CBC solver via OR-Tools")

    t1 = time.perf_counter()
    gen_vars, ac_vars = OPF_create_LModel_AC_ortools(solver, grid)
    t2 = time.perf_counter()
    t_modelcreate = t2 - t1

    # Objective
    set_objective_ortools(solver, grid, gen_vars, ac_vars, OPEX, NPV,
                          n_years, Hy, discount_rate)

    # Solver parameters
    solver.SetTimeLimit(int(time_limit * 1000))  # ms
    if tee:
        solver.EnableOutput()

    t3 = time.perf_counter()
    model_res, solver_stats = solve_ortools_model(solver, grid, tee)
    t4 = time.perf_counter()

    # Export results to grid
    ExportACDC_Lmodel_toPyflowACDC_ortools(solver, grid, gen_vars, ac_vars,
                                            tee=tee)

    if OPEX:
        obj = {'Energy_cost': 1}
    else:
        obj = None

    weights_def, _ = obj_w_rule(grid, obj, True)
    present_value = Hy * (1 - (1 + discount_rate) ** -n_years) / discount_rate
    for obj_key in weights_def:
        weights_def[obj_key]['v'] = calculate_objective(grid, obj_key, True)
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

        model_res = {
            'status': status_str,
            'objective_value': obj_val,
            'solver_time': solve_time,
            'Solver': [{'Status': 'ok' if status in (
                pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else status_str}],
        }
        solver_stats = {
            'time': solve_time,
            'status': status_str,
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
            'Solver': [{'Status': 'error'}],
        }
        solver_stats = {
            'time': None,
            'status': 'error',
            'error_message': str(e),
            'feasible_solutions': [],
        }

    return model_res, solver_stats


# ── Model creation ──────────────────────────────────────────────────────────

def OPF_create_LModel_AC_ortools(solver, grid):
    """Build the linear AC OPF model inside *solver*."""
    from .ACDC_OPF import Translate_pyf_OPF

    opf_data = Translate_pyf_OPF(grid, False)
    AC_info = opf_data['AC_info']
    gen_info = opf_data['gen_info']

    gen_vars = Generation_variables_ortools(solver, grid, gen_info)
    ac_vars = AC_variables_ortools(solver, grid, AC_info)
    AC_constraints_ortools(solver, grid, AC_info, gen_info, gen_vars, ac_vars)

    return gen_vars, ac_vars


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

    # AC generators
    variables['PGi_gen'] = {}
    for g in lista_gen:
        gen = grid.Generators[g]
        p_lb = gen.Min_pow_gen * gen.np_gen
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
            -np.pi / 2, np.pi / 2, f'theta_AC_{node}')

    # ── Nodal power variables ────────────────────────────────────────────
    ac_vars['PGi_opt'] = {}
    for node in lista_nodos_AC:
        min_gen = sum(g.Min_pow_gen for g in grid.nodes_AC[node].connected_gen
                      if g.Min_pow_gen < 0)
        max_gen = sum(g.Max_pow_gen for g in grid.nodes_AC[node].connected_gen)
        ac_vars['PGi_opt'][node] = solver.NumVar(min_gen, max_gen,
                                                  f'PGi_opt_{node}')

    ac_vars['PGi_ren'] = {}
    for node in lista_nodos_AC:
        max_ren = sum(rs.PGi_ren for rs in grid.nodes_AC[node].connected_RenSource)
        ac_vars['PGi_ren'][node] = solver.NumVar(0, max_ren, f'PGi_ren_{node}')

    # ── CT power injection aggregates per node ───────────────────────────
    ac_vars['Pto_CT'] = {}
    ac_vars['Pfrom_CT'] = {}
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        max_ct_power = sum(
            max(S_lineACct_lim[line.lineNumber, ct] for ct in cab_types_set)
            for line in nAC.connected_toCTLine + nAC.connected_fromCTLine)
        ac_vars['Pto_CT'][node] = solver.NumVar(-max_ct_power, max_ct_power,
                                                 f'Pto_CT_{node}')
        ac_vars['Pfrom_CT'][node] = solver.NumVar(-max_ct_power, max_ct_power,
                                                   f'Pfrom_CT_{node}')

    # ── Standard AC line flows ───────────────────────────────────────────
    ac_vars['PAC_to'] = {}
    ac_vars['PAC_from'] = {}
    for line in lista_lineas_AC:
        lim = S_lineAC_limit[line]
        ac_vars['PAC_to'][line] = solver.NumVar(-lim, lim, f'PAC_to_{line}')
        ac_vars['PAC_from'][line] = solver.NumVar(-lim, lim, f'PAC_from_{line}')

    # ── Network flow (integer) for topology enforcement ──────────────────
    max_flow = grid.max_turbines_per_string
    ac_vars['network_flow'] = {}
    ac_vars['node_net_flow'] = {}
    for line in lista_lineas_AC_ct:
        ac_vars['network_flow'][line] = solver.IntVar(-max_flow, max_flow,
                                                       f'network_flow_{line}')
    for node in lista_nodos_AC:
        ac_vars['node_net_flow'][node] = solver.IntVar(
            -len(lista_nodos_AC), 1, f'node_net_flow_{node}')

    # ── CT line power flows per cable type + McCormick helpers ───────────
    ac_vars['ct_PAC_to'] = {}
    ac_vars['ct_PAC_from'] = {}
    ac_vars['z_to'] = {}
    ac_vars['z_from'] = {}
    for line in lista_lineas_AC_ct:
        max_min = max(S_lineACct_lim[line, ct] for ct in cab_types_set)
        for ct in cab_types_set:
            ac_vars['ct_PAC_to'][line, ct] = solver.NumVar(
                -max_min, max_min, f'ct_PAC_to_{line}_{ct}')
            ac_vars['ct_PAC_from'][line, ct] = solver.NumVar(
                -max_min, max_min, f'ct_PAC_from_{line}_{ct}')
            ac_vars['z_to'][line, ct] = solver.NumVar(
                -max_min, max_min, f'z_to_{line}_{ct}')
            ac_vars['z_from'][line, ct] = solver.NumVar(
                -max_min, max_min, f'z_from_{line}_{ct}')

    return ac_vars


# ── Constraints ─────────────────────────────────────────────────────────────

def AC_constraints_ortools(solver, grid, AC_info, gen_info, gen_vars, ac_vars):
    """Add all constraints to the OR-Tools model."""
    AC_Lists, AC_nodes_info, AC_lines_info, EXP_info, REC_info, CT_info = AC_info
    lista_nodos_AC, lista_lineas_AC, lista_lineas_AC_tf, AC_slack, AC_PV = AC_Lists
    lista_lineas_AC_ct, S_lineACct_lim, cab_types_set, allowed_types = CT_info

    gen_AC_info, _, gen_rs_info = gen_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info

    max_cable_limits = {
        line: max(S_lineACct_lim[line, ct] for ct in cab_types_set)
        for line in lista_lineas_AC_ct}

    # ── Nodal balance ────────────────────────────────────────────────────
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]

        # Power balance: Pto_CT + Pfrom_CT == PGi_ren + PGi_opt
        solver.Add(
            ac_vars['Pto_CT'][node] + ac_vars['Pfrom_CT'][node]
            == ac_vars['PGi_ren'][node] + ac_vars['PGi_opt'][node],
            f'power_balance_{node}')

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
        B = np.imag(l.Ybus_branch[0, 1])

        solver.Add(
            ac_vars['PAC_to'][line]
            == -B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f]),
            f'power_flow_to_{line}')
        solver.Add(
            ac_vars['PAC_from'][line]
            == -B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t]),
            f'power_flow_from_{line}')

    # ── Cable-type selection constraints ─────────────────────────────────
    # Global limit on number of distinct cable types
    solver.Add(
        sum(ac_vars['ct_types'][ct] for ct in cab_types_set)
        <= grid.cab_types_allowed,
        'CT_limit_rule')

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

    # At most one cable type per line
    for line in lista_lineas_AC_ct:
        solver.Add(
            sum(ac_vars['ct_branch'][line, ct] for ct in cab_types_set) <= 1,
            f'ct_Array_cable_type_rule_{line}')

    # Node connection limits
    for node in lista_nodos_AC:
        nAC = grid.nodes_AC[node]
        if hasattr(nAC, 'ct_limit'):
            connections = sum(
                ac_vars['ct_branch'][line.lineNumber, ct]
                for line in nAC.connected_toCTLine + nAC.connected_fromCTLine
                for ct in cab_types_set)
            solver.Add(connections >= 1, f'ct_node_min_rule_{node}')
            solver.Add(connections <= nAC.ct_limit,
                        f'ct_node_limit_rule_{node}')

    # Crossing constraints
    for ct_crossing in grid.crossing_groups:
        solver.Add(
            sum(ac_vars['ct_branch'][line, ct]
                for line in grid.crossing_groups[ct_crossing]
                for ct in cab_types_set) <= 1,
            f'ct_crossings_rule_{ct_crossing}')

    # ── McCormick envelope + power-flow linking for CT lines ─────────────
    for line in lista_lineas_AC_ct:
        l = grid.lines_AC_ct[line]
        M = max_cable_limits[line] * 1.1

        for ct in cab_types_set:
            f = l.fromNode.nodeNumber
            t = l.toNode.nodeNumber
            B = np.imag(l.Ybus_list[ct][0, 1])
            M_angle = B * 3.1416

            # Power-flow linking (big-M on angle diff)
            solver.Add(
                ac_vars['ct_PAC_to'][line, ct]
                + B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f])
                <= M_angle * (1 - ac_vars['ct_branch'][line, ct]),
                f'ct_pf_to_lower_{line}_{ct}')
            solver.Add(
                ac_vars['ct_PAC_to'][line, ct]
                + B * (ac_vars['theta_AC'][t] - ac_vars['theta_AC'][f])
                >= -M_angle * (1 - ac_vars['ct_branch'][line, ct]),
                f'ct_pf_to_upper_{line}_{ct}')
            solver.Add(
                ac_vars['ct_PAC_from'][line, ct]
                + B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t])
                <= M_angle * (1 - ac_vars['ct_branch'][line, ct]),
                f'ct_pf_from_lower_{line}_{ct}')
            solver.Add(
                ac_vars['ct_PAC_from'][line, ct]
                + B * (ac_vars['theta_AC'][f] - ac_vars['theta_AC'][t])
                >= -M_angle * (1 - ac_vars['ct_branch'][line, ct]),
                f'ct_pf_from_upper_{line}_{ct}')

            # McCormick envelopes for z_to = ct_branch * ct_PAC_to
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

    # ── Network flow constraints (topology enforcement) ──────────────────
    _add_network_flow_constraints_ortools(solver, grid, ac_vars,
                                          lista_nodos_AC,
                                          lista_lineas_AC_ct,
                                          cab_types_set)


def _add_network_flow_constraints_ortools(solver, grid, ac_vars,
                                           lista_nodos_AC,
                                           lista_lineas_AC_ct,
                                           cab_types_set):
    """Network-flow constraints ensuring a connected spanning forest."""
    max_flow = grid.max_turbines_per_string

    source_nodes = [n for n in lista_nodos_AC
                    if grid.nodes_AC[n].connected_RenSource]
    sink_nodes = [n for n in lista_nodos_AC
                  if grid.nodes_AC[n].connected_gen]

    if not source_nodes:
        raise ValueError("No renewable source nodes found!")
    if not sink_nodes:
        raise ValueError("No generator nodes found!")

    # Spanning tree: exactly (N - sinks) connections
    total_connections = sum(ac_vars['ct_branch'][line, ct]
                            for line in lista_lineas_AC_ct
                            for ct in cab_types_set)
    solver.Add(total_connections == len(lista_nodos_AC) - len(sink_nodes),
               'spanning_tree_connections')

    # Flow conservation per node
    for node in lista_nodos_AC:
        net_flow = 0
        for line in lista_lineas_AC_ct:
            line_obj = grid.lines_AC_ct[line]
            if line_obj.fromNode.nodeNumber == node:
                net_flow += ac_vars['network_flow'][line]
            elif line_obj.toNode.nodeNumber == node:
                net_flow -= ac_vars['network_flow'][line]
        solver.Add(ac_vars['node_net_flow'][node] == net_flow,
                    f'flow_conservation_{node}')

    # Source nodes: net flow out = 1
    for node in source_nodes:
        solver.Add(ac_vars['node_net_flow'][node] == 1,
                    f'source_node_{node}')

    # Sink nodes absorb all source flow
    solver.Add(
        sum(ac_vars['node_net_flow'][node] for node in sink_nodes)
        == -len(source_nodes),
        'total_sink_absorption')

    # Intermediate nodes: conservation
    for node in lista_nodos_AC:
        if node not in source_nodes and node not in sink_nodes:
            solver.Add(ac_vars['node_net_flow'][node] == 0,
                        f'intermediate_node_{node}')

    # Link flow to investment
    for line in lista_lineas_AC_ct:
        branch_sum = sum(ac_vars['ct_branch'][line, ct]
                         for ct in cab_types_set)
        solver.Add(
            ac_vars['network_flow'][line] <= max_flow * branch_sum,
            f'flow_investment_link_upper_{line}')
        solver.Add(
            ac_vars['network_flow'][line] >= -max_flow * branch_sum,
            f'flow_investment_link_lower_{line}')


# ── Objective ───────────────────────────────────────────────────────────────

def set_objective_ortools(solver, grid, gen_vars, ac_vars, OPEX=True,
                          NPV=True, n_years=25, Hy=HOURS_PER_YEAR, discount_rate=DEFAULT_DISCOUNT_RATE):
    """Set the minimisation objective (investment + operational cost)."""
    cab_types_set = list(range(len(grid.Cable_options[0]._cable_types)))

    objective = solver.Objective()
    objective.SetMinimization()

    # Investment cost
    for line in grid.lines_AC_ct:
        l = line.lineNumber
        if line.array_opf:
            for ct in cab_types_set:
                cost = line.base_cost[ct]
                if not NPV:
                    cost /= line.life_time_hours
                objective.SetCoefficient(ac_vars['ct_branch'][l, ct], cost)

    # Operational cost (energy cost via generator linear factor)
    if OPEX:
        present_value = 1.0
        if NPV:
            present_value = Hy * (1 - (1 + discount_rate) ** -n_years) / discount_rate

        for g in range(grid.n_gen):
            gen = grid.Generators[g]
            objective.SetCoefficient(gen_vars['PGi_gen'][g],
                                     gen.lf * present_value)


# ── Export results back to grid ─────────────────────────────────────────────

def ExportACDC_Lmodel_toPyflowACDC_ortools(solver, grid, gen_vars, ac_vars,
                                             tee=True):
    """Write solver results into the pyflow_acdc grid object.

    Must be called *after* ``solve_ortools_model`` – solution values are
    cached and accessible via ``.solution_value()`` without re-solving.
    """
    cab_types_set = list(range(len(grid.Cable_options[0]._cable_types)))
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
            ac_vars['ct_branch'][line.lineNumber, ct].solution_value() >= 0.9
            for ct in cab_types_set]
        if any(ct_selected):
            line.active_config = np.where(ct_selected)[0][0]
            ct = cab_types_set[line.active_config]
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
        line.network_flow = abs(
            ac_vars['network_flow'][line.lineNumber].solution_value())

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

    # Fix oversizing if solver hit time limit
    if solver.wall_time() >= solver.time_limit() * 0.99:
        try:
            from .AC_OPF_L_model import (analyze_oversizing_issues_grid,
                                          apply_oversizing_fixes_grid)
            oversizing_type1, oversizing_type2 = analyze_oversizing_issues_grid(
                grid, tee=tee)
            apply_oversizing_fixes_grid(grid, oversizing_type1,
                                        oversizing_type2, tee=tee)
        except ImportError:
            pass
