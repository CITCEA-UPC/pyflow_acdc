"""
Created on Thu Oct 10 14:58:18 2024

@author: BernardoCastro
"""

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from ..ACDC_OPF import (
    calculate_objective,
    calculate_objective_from_model,
    export_acdc_nl_model_to_pyflow_acdc,
    obj_w_rule,
    opf_obj,
    reset_to_initialize,
)
from ..constants import (
    BINARY_THRESHOLD,
    DEFAULT_DISCOUNT_RATE,
    HOURS_PER_YEAR,
    TS_RENEWABLE_TYPES,
    TSType,
    present_value_factor,
)
from ..Graph_and_plot import save_network_svg
from ..grid_analysis import analyse_grid
from ..pyomo_model_solve import build_only_solver_stats, pyomo_model_solve
from .ACDC_OPF_NL_model import TEP_variables, opf_create_nl_model_acdc

__all__ = [
    'update_grid_scenario_frame',
    'transmission_expansion',
    'multi_scenario_TEP',
    'identify_standalone_rs_conv_pairs',
    'export_TEP_multiScenario_results_to_excel',
    'alpha_pareto',
    'rate_sensitivity',
    'kappa_sensitivity',
    'comprehensive_sensitivity_analysis'
]

def identify_standalone_rs_conv_pairs(grid, ren_source_ids=None, conv_ids=None):
    """
    Identify standalone AC-node pairs with exactly one RS and one converter.

    Optional filters:
    - ren_source_ids: iterable of allowed RS indices (rsNumber)
    - conv_ids: iterable of allowed converter indices (ConvNumber)
    """
    if not (grid.ACmode and grid.DCmode):
        return []

    allowed_rs = None if ren_source_ids is None else set(ren_source_ids)
    allowed_conv = None if conv_ids is None else set(conv_ids)
    standalone_pairs = []

    for node in grid.nodes_AC:
        if not node.stand_alone:
            continue
        if len(node.connected_RenSource) != 1:
            continue
        if len(node.connected_conv) != 1:
            continue

        ren_source = node.connected_RenSource[0]
        conv_idx = next(iter(node.connected_conv))
        rs_idx = ren_source.rsNumber

        if allowed_rs is not None and rs_idx not in allowed_rs:
            continue
        if allowed_conv is not None and conv_idx not in allowed_conv:
            continue
        if not ren_source.np_rsgen_opf:
            continue
        if not grid.Converters_ACDC[conv_idx].np_conv_opf:
            continue

        standalone_pairs.append((rs_idx, conv_idx))

    return standalone_pairs


def update_grid_scenario_frame(grid,ts,t,n_clusters,clustering):
    idx=t-1
    typ = ts.type

    if clustering:
        ts_data = ts.data_clustered[n_clusters]
    else:
        ts_data = ts.data

    if typ == TSType.A_CG:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.a_base = ts_data[idx]
                break
    elif typ == TSType.B_CG:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.b = ts_data[idx]
                break
    elif typ == TSType.C_CG:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.c = ts_data[idx]
                break
    elif typ == TSType.PGL_MIN:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.PGL_min_base= ts_data[idx]
                break
    elif typ == TSType.PGL_MAX:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.PGL_max= ts_data[idx]
                break
    if typ == TSType.PRICE:
        for price_zone in grid.Price_Zones:
            if ts.element_name == price_zone.name:
                price_zone.price = ts_data[idx]
                break  # Stop after assigning to the correct price_zone
        for node in grid.nodes_AC:
            if ts.element_name == node.name:
                node.price = ts_data[idx]
                break  # Stop after assigning to the correct node

    elif typ == TSType.LOAD:
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

    elif typ in TS_RENEWABLE_TYPES:
        for zone in grid.RenSource_zones:
            if ts.element_name == zone.name:
                zone.PRGi_available = ts_data[idx]
                # print(ts_data[idx])
                break  # Stop after assigning to the correct zone
        for rs in grid.RenSources:
            if ts.element_name == rs.name:
                rs.PRGi_available = ts_data[idx]
                break  # Stop after assigning to the correct node

def get_TEP_variables(grid):

    np_conv, np_conv_model_first_guess, np_conv_max = {}, {}, {}
    np_conv_planned_install = {}
    S_limit_conv={}
    P_lineDC_limit ={}
    NP_lineDC, NP_lineDC_model_first_guess, NP_lineDC_max = {}, {}, {}
    NP_lineDC_planned_install = {}
    NP_lineAC, NP_lineAC_model_first_guess, NP_lineAC_max = {}, {}, {}
    NP_lineAC_planned_install = {}
    Line_length ={}
    REC_branch ={}


    for l in grid.lines_AC_rec:
        REC_branch[l.lineNumber] = 0 if not l.rec_branch  else 1

    def _init_with_planned(base, n_max, planned_install, active):
        if not active:
            return base
        # Model first guess: start from current stock + planned additions, capped by max.
        return max(base, min(base + planned_install, n_max))

    for l in grid.lines_AC_exp:
        planned_install = getattr(l, 'planned_installation', 0)
        NP_lineAC[l.lineNumber]     = l.np_line
        NP_lineAC_model_first_guess[l.lineNumber] = _init_with_planned(
            l.np_line, l.np_line_max, planned_install, l.np_line_opf
        )
        NP_lineAC_max[l.lineNumber]   = l.np_line_max
        NP_lineAC_planned_install[l.lineNumber] = planned_install

    ct_ini = {}
    for l in grid.lines_AC_ct:
        for ct in range(len(l._cable_types)):
            ct_ini[l.lineNumber, ct] = 1 if ct == l.active_config else 0

    for conv in grid.Converters_ACDC:
        planned_install = getattr(conv, 'planned_installation', 0)
        np_conv [conv.ConvNumber]  = conv.np_conv
        np_conv_model_first_guess[conv.ConvNumber] = _init_with_planned(
            conv.np_conv, conv.np_conv_max, planned_install, conv.np_conv_opf
        )
        np_conv_max[conv.ConvNumber] = conv.np_conv_max
        np_conv_planned_install[conv.ConvNumber] = planned_install
        S_limit_conv[conv.ConvNumber] = conv.MVA_max/grid.S_base
    for l in grid.lines_DC:
        planned_install = getattr(l, 'planned_installation', 0)
        P_lineDC_limit[l.lineNumber]  = l.MW_rating/grid.S_base
        NP_lineDC[l.lineNumber]     = l.np_line
        NP_lineDC_model_first_guess[l.lineNumber] = _init_with_planned(
            l.np_line, l.np_line_max, planned_install, l.np_line_opf
        )
        NP_lineDC_max[l.lineNumber]   = l.np_line_max
        NP_lineDC_planned_install[l.lineNumber] = planned_install
        Line_length[l.lineNumber]     = l.Length_km

    np_gen={}
    np_gen_model_first_guess={}
    np_gen_max={}
    np_gen_planned_install = {}
    for gen in grid.Generators:
        planned_install = getattr(gen, 'planned_installation', 0)
        np_gen_max[gen.genNumber] = gen.np_gen_max
        np_gen[gen.genNumber] = gen.np_gen
        np_gen_model_first_guess[gen.genNumber] = _init_with_planned(
            gen.np_gen, gen.np_gen_max, planned_install, gen.np_gen_opf
        )
        np_gen_planned_install[gen.genNumber] = planned_install

    np_gen_DC={}
    np_gen_DC_model_first_guess={}
    np_gen_max_DC={}
    np_gen_DC_planned_install = {}
    for gen in grid.Generators_DC:
        planned_install = getattr(gen, 'planned_installation', 0)
        np_gen_max_DC[gen.genNumber_DC] = gen.np_gen_max
        np_gen_DC[gen.genNumber_DC] = gen.np_gen
        np_gen_DC_model_first_guess[gen.genNumber_DC] = _init_with_planned(
            gen.np_gen, gen.np_gen_max, planned_install, gen.np_gen_opf
        )
        np_gen_DC_planned_install[gen.genNumber_DC] = planned_install

    np_rsgen={}
    np_rsgen_model_first_guess={}
    np_rsgen_max={}
    np_rsgen_planned_install = {}
    for rs in grid.RenSources:
        planned_install = getattr(rs, 'planned_installation', 0)
        np_rsgen[rs.rsNumber] = rs.np_rsgen
        np_rsgen_max[rs.rsNumber] = rs.np_rsgen_max
        np_rsgen_model_first_guess[rs.rsNumber] = _init_with_planned(
            rs.np_rsgen, rs.np_rsgen_max, planned_install, rs.np_rsgen_opf
        )
        np_rsgen_planned_install[rs.rsNumber] = planned_install

    # Return as dictionary for easier extension and maintenance
    return {
        'converters': {
            'np_conv': np_conv,
            'np_conv_model_first_guess': np_conv_model_first_guess,
            'np_conv_max': np_conv_max,
            'np_conv_planned_install': np_conv_planned_install,
            'S_limit_conv': S_limit_conv
        },
        'dc_lines': {
            'P_lineDC_limit': P_lineDC_limit,
            'NP_lineDC': NP_lineDC,
            'NP_lineDC_model_first_guess': NP_lineDC_model_first_guess,
            'NP_lineDC_max': NP_lineDC_max,
            'NP_lineDC_planned_install': NP_lineDC_planned_install,
            'Line_length': Line_length
        },
        'ac_lines': {
            'NP_lineAC': NP_lineAC,
            'NP_lineAC_model_first_guess': NP_lineAC_model_first_guess,
            'NP_lineAC_max': NP_lineAC_max,
            'NP_lineAC_planned_install': NP_lineAC_planned_install,
            'Line_length': Line_length,
            'REC_branch': REC_branch,
            'ct_ini': ct_ini
        },
        'generators': {
            'np_gen': np_gen,
            'np_gen_model_first_guess': np_gen_model_first_guess,
            'np_gen_planned_install': np_gen_planned_install,
            'np_gen_max': np_gen_max,
            'np_gen_DC': np_gen_DC,
            'np_gen_DC_model_first_guess': np_gen_DC_model_first_guess,
            'np_gen_DC_planned_install': np_gen_DC_planned_install,
            'np_gen_max_DC': np_gen_max_DC
        },
        'ren_sources': {
            'np_rsgen': np_rsgen,
            'np_rsgen_model_first_guess': np_rsgen_model_first_guess,
            'np_rsgen_planned_install': np_rsgen_planned_install,
            'np_rsgen_max': np_rsgen_max
        }
    }

def _TEP_install_variables(model, grid, initiate_max=False):
    tep_vars = get_TEP_variables(grid)

    np_conv = tep_vars['converters']['np_conv']
    np_conv_max = tep_vars['converters']['np_conv_max']
    np_conv_planned_install = tep_vars['converters']['np_conv_planned_install']

    NP_lineDC = tep_vars['dc_lines']['NP_lineDC']
    NP_lineDC_max = tep_vars['dc_lines']['NP_lineDC_max']
    NP_lineDC_planned_install = tep_vars['dc_lines']['NP_lineDC_planned_install']

    NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
    NP_lineAC_max = tep_vars['ac_lines']['NP_lineAC_max']
    NP_lineAC_planned_install = tep_vars['ac_lines']['NP_lineAC_planned_install']

    np_gen = tep_vars['generators']['np_gen']
    np_gen_max = tep_vars['generators']['np_gen_max']
    np_gen_DC = tep_vars['generators']['np_gen_DC']
    np_gen_max_DC = tep_vars['generators']['np_gen_max_DC']
    np_gen_planned_install = tep_vars['generators']['np_gen_planned_install']
    np_gen_DC_planned_install = tep_vars['generators']['np_gen_DC_planned_install']

    np_rsgen = tep_vars['ren_sources']['np_rsgen']
    np_rsgen_max = tep_vars['ren_sources']['np_rsgen_max']
    np_rsgen_planned_install = tep_vars['ren_sources']['np_rsgen_planned_install']

    def min_install_opt(element, planned, max_opt):
        allows_decrease = element.allow_planned_decrease
        return -min(planned, max_opt) if allows_decrease else 0

    def init_install_from_bounds(bounds_fn, idx):
        lb, ub = bounds_fn(model, idx)
        return ub if initiate_max else 0

    if grid.rs_GPR:
        def np_rsgen_install_opt_bounds(model, rs):
            ren_source = grid.RenSources[rs]
            if not ren_source.np_rsgen_opf:
                return (0, 0)
            max_opt = np_rsgen_max[rs] - np_rsgen[rs] - np_rsgen_planned_install[rs]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(ren_source, np_rsgen_planned_install[rs], max_opt), max_opt)

        model.np_rsgen_planned_install = pyo.Param(model.ren_sources, initialize=np_rsgen_planned_install)
        model.np_rsgen_install_opt = pyo.Var(
            model.ren_sources,
            within=pyo.Integers,
            bounds=np_rsgen_install_opt_bounds,
            initialize=lambda m, rs: init_install_from_bounds(np_rsgen_install_opt_bounds, rs),
        )
        model.np_rsgen_install = pyo.Expression(
            model.ren_sources,
            rule=lambda m, rs: m.np_rsgen_planned_install[rs] + m.np_rsgen_install_opt[rs],
        )

    if grid.ACmode and grid.GPR:
        def np_gen_install_opt_bounds(model, g):
            gen = grid.Generators[g]
            if not gen.np_gen_opf:
                return (0, 0)
            max_opt = np_gen_max[g] - np_gen[g] - np_gen_planned_install[g]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(gen, np_gen_planned_install[g], max_opt), max_opt)

        model.np_gen_planned_install = pyo.Param(model.gen_AC, initialize=np_gen_planned_install)
        model.np_gen_install_opt = pyo.Var(
            model.gen_AC,
            within=pyo.Integers,
            bounds=np_gen_install_opt_bounds,
            initialize=lambda m, g: init_install_from_bounds(np_gen_install_opt_bounds, g),
        )
        model.np_gen_install = pyo.Expression(
            model.gen_AC,
            rule=lambda m, g: m.np_gen_planned_install[g] + m.np_gen_install_opt[g],
        )

    if grid.ACmode and grid.TEP_AC:
        def NPline_install_opt_bounds_AC(model, line):
            element = grid.lines_AC_exp[line]
            if not element.np_line_opf:
                return (0, 0)
            max_opt = NP_lineAC_max[line] - NP_lineAC[line] - NP_lineAC_planned_install[line]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(element, NP_lineAC_planned_install[line], max_opt), max_opt)

        model.NumLinesACP_planned_install = pyo.Param(model.lines_AC_exp, initialize=NP_lineAC_planned_install)
        model.NumLinesACP_install_opt = pyo.Var(
            model.lines_AC_exp,
            within=pyo.Integers,
            bounds=NPline_install_opt_bounds_AC,
            initialize=lambda m, line: init_install_from_bounds(NPline_install_opt_bounds_AC, line),
        )
        model.NumLinesACP_install = pyo.Expression(
            model.lines_AC_exp,
            rule=lambda m, line: m.NumLinesACP_planned_install[line] + m.NumLinesACP_install_opt[line],
        )

    if grid.DCmode and grid.GPR:
        def np_gen_install_opt_bounds_DC(model, g):
            gen = grid.Generators_DC[g]
            if not gen.np_gen_opf:
                return (0, 0)
            max_opt = np_gen_max_DC[g] - np_gen_DC[g] - np_gen_DC_planned_install[g]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(gen, np_gen_DC_planned_install[g], max_opt), max_opt)

        model.np_gen_DC_planned_install = pyo.Param(model.gen_DC, initialize=np_gen_DC_planned_install)
        model.np_gen_DC_install_opt = pyo.Var(
            model.gen_DC,
            within=pyo.Integers,
            bounds=np_gen_install_opt_bounds_DC,
            initialize=lambda m, g: init_install_from_bounds(np_gen_install_opt_bounds_DC, g),
        )
        model.np_gen_DC_install = pyo.Expression(
            model.gen_DC,
            rule=lambda m, g: m.np_gen_DC_planned_install[g] + m.np_gen_DC_install_opt[g],
        )

    if grid.DCmode:
        def NPline_install_opt_bounds(model, line):
            element = grid.lines_DC[line]
            if not element.np_line_opf:
                return (0, 0)
            max_opt = NP_lineDC_max[line] - NP_lineDC[line] - NP_lineDC_planned_install[line]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(element, NP_lineDC_planned_install[line], max_opt), max_opt)

        model.NumLinesDCP_planned_install = pyo.Param(model.lines_DC, initialize=NP_lineDC_planned_install)
        model.NumLinesDCP_install_opt = pyo.Var(
            model.lines_DC,
            within=pyo.Integers,
            bounds=NPline_install_opt_bounds,
            initialize=lambda m, line: init_install_from_bounds(NPline_install_opt_bounds, line),
        )
        model.NumLinesDCP_install = pyo.Expression(
            model.lines_DC,
            rule=lambda m, line: m.NumLinesDCP_planned_install[line] + m.NumLinesDCP_install_opt[line],
        )

    if grid.ACmode and grid.DCmode:
        def NPconv_install_opt_bounds(model, conv):
            element = grid.Converters_ACDC[conv]
            if not element.np_conv_opf:
                return (0, 0)
            max_opt = np_conv_max[conv] - np_conv[conv] - np_conv_planned_install[conv]
            if max_opt < 0:
                max_opt = 0
            return (min_install_opt(element, np_conv_planned_install[conv], max_opt), max_opt)

        model.np_conv_planned_install = pyo.Param(model.conv, initialize=np_conv_planned_install)
        model.np_conv_install_opt = pyo.Var(
            model.conv,
            within=pyo.Integers,
            bounds=NPconv_install_opt_bounds,
            initialize=lambda m, conv: init_install_from_bounds(NPconv_install_opt_bounds, conv),
        )
        model.np_conv_install = pyo.Expression(
            model.conv,
            rule=lambda m, conv: m.np_conv_planned_install[conv] + m.np_conv_install_opt[conv],
        )


def _TEP_install_constraints(model, grid):
    if grid.rs_GPR:
        def np_rsgen_total_balance_rule(model, rs):
            return model.np_rsgen[rs] == model.np_rsgen_base[rs] + model.np_rsgen_install[rs]

        model.np_rsgen_total_balance = pyo.Constraint(model.ren_sources, rule=np_rsgen_total_balance_rule)

    if grid.ACmode and grid.GPR:
        def np_gen_total_balance_rule(model, g):
            return model.np_gen[g] == model.np_gen_base[g] + model.np_gen_install[g]

        model.np_gen_total_balance = pyo.Constraint(model.gen_AC, rule=np_gen_total_balance_rule)

    if grid.ACmode and grid.TEP_AC:
        def NPlineAC_total_balance_rule(model, line):
            return model.NumLinesACP[line] == model.NumLinesACP_base[line] + model.NumLinesACP_install[line]

        model.NPlineAC_total_balance = pyo.Constraint(model.lines_AC_exp, rule=NPlineAC_total_balance_rule)

    if grid.DCmode and grid.GPR:
        def np_gen_DC_total_balance_rule(model, g):
            return model.np_gen_DC[g] == model.np_gen_DC_base[g] + model.np_gen_DC_install[g]

        model.np_gen_DC_total_balance = pyo.Constraint(model.gen_DC, rule=np_gen_DC_total_balance_rule)

    if grid.DCmode:
        def NPline_total_balance_rule(model, line):
            return model.NumLinesDCP[line] == model.NumLinesDCP_base[line] + model.NumLinesDCP_install[line]

        model.NPline_total_balance = pyo.Constraint(model.lines_DC, rule=NPline_total_balance_rule)

    if grid.ACmode and grid.DCmode:
        def np_conv_total_balance_rule(model, conv):
            return model.np_conv[conv] == model.np_conv_base[conv] + model.np_conv_install[conv]

        model.np_conv_total_balance = pyo.Constraint(model.conv, rule=np_conv_total_balance_rule)


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
        if element.np_conv_opf:
            return model.np_conv[conv] ==model.scenario_model[t].np_conv[conv]
        else:
            return pyo.Constraint.Skip

    def NP_gen_AC_link(model,g,t):
        gen = grid.Generators[g]
        if gen.np_gen_opf:
            return model.np_gen[g] == model.scenario_model[t].np_gen[g]
        else:
            return pyo.Constraint.Skip

    def NP_gen_DC_link(model,g,t):
        gen = grid.Generators_DC[g]
        if gen.np_gen_opf:
            return model.np_gen_DC[g] == model.scenario_model[t].np_gen_DC[g]
        else:
            return pyo.Constraint.Skip

    def NP_rsgen_link(model,rs,t):
        source = grid.RenSources[rs]
        if source.np_rsgen_opf:
            return model.np_rsgen[rs] == model.scenario_model[t].np_rsgen[rs]
        else:
            return pyo.Constraint.Skip

    if grid.TEP_AC:
        model.NP_ACline_link_constraint = pyo.Constraint(model.lines_AC_exp,model.scenario_frames, rule=NP_ACline_link)

    if grid.DCmode:
        model.NP_line_link_constraint = pyo.Constraint(model.lines_DC,model.scenario_frames, rule=NP_line_link)
    if grid.ACmode and grid.DCmode:
        model.NP_conv_link_constraint = pyo.Constraint(model.conv,model.scenario_frames, rule=NP_conv_link)
    if grid.ACmode and grid.GPR:
        model.NP_gen_AC_link_constraint = pyo.Constraint(model.gen_AC, model.scenario_frames, rule=NP_gen_AC_link)
    if grid.DCmode and grid.GPR:
        model.NP_gen_DC_link_constraint = pyo.Constraint(model.gen_DC, model.scenario_frames, rule=NP_gen_DC_link)
    if grid.rs_GPR:
        model.NP_rsgen_link_constraint = pyo.Constraint(model.ren_sources, model.scenario_frames, rule=NP_rsgen_link)

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

def _prepare_TEP_model(
    grid,
    NPV,
    n_years,
    Hy,
    discount_rate,
    ObjRule,
    PV_set=False,
    initiate_max=False,
):

    analyse_grid(grid)

    weights_def, PZ = obj_w_rule(grid,ObjRule)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate

    model = pyo.ConcreteModel()
    model.name = "TEP MTDC AC/DC hybrid OPF"

    opf_create_nl_model_acdc(model,grid,PV_set=PV_set,Price_Zones=PZ,TEP=True)
    _TEP_install_variables(model, grid, initiate_max=initiate_max)
    _TEP_install_constraints(model, grid)

    limits_map = getattr(grid, "current_generation_type_limits", {}) or {}
    if any(float(v) != 1.0 for v in limits_map.values()):
        GEN_balance_constraints(model, grid)


    obj_TEP = tep_obj(model,grid,NPV)
    obj_OPF = opf_obj(model,grid,weights_def)


    return model, obj_TEP, obj_OPF,weights_def,PZ


def GEN_balance_constraints(model,grid):

    if all(v == 1 for v in grid.current_generation_type_limits.values()):
        return  # All limits are 1, no constraints needed

    gen_type_limits = {k.lower(): v for k, v in grid.current_generation_type_limits.items()}
    model.gen_types = pyo.Set(initialize=list(gen_type_limits.keys()))
    model.gen_type_limits = pyo.Param(model.gen_types,initialize=gen_type_limits)

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

def transmission_expansion(
    grid,
    NPV=True,
    n_years=25,
    Hy=HOURS_PER_YEAR,
    discount_rate=DEFAULT_DISCOUNT_RATE,
    ObjRule=None,
    solver='bonmin',
    time_limit=None,
    tee=False,
    export=True,
    PV_set=False,
    alpha=None,
    callback=False,
    solver_options=None,
    obj_scaling=1.0,
    nlp_warmstart=False,
    initiate_max=False,
    build_only=False,
):
    """Build and solve the (non-linear) static transmission-expansion problem.

    Combines the TEP investment cost with the OPF operating cost in a single
    objective (OPEX discounted to present value when ``NPV`` is set, optionally
    weighted by ``alpha``), solves the resulting non-linear model, and exports
    the expansion decisions and operating point back onto ``grid``.

    Parameters
    ----------
    grid : Grid
        Network with candidate expandable elements (mutated in place).
    NPV : bool, optional
        Discount OPEX to present value over the planning horizon.
    n_years : int, optional
        Planning horizon in years.
    Hy : float, optional
        Operating hours per year used to annualise OPEX.
    discount_rate : float, optional
        Annual discount rate for the present-value factor.
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    solver : str, optional
        Pyomo (MINLP/NLP) solver name.
    time_limit : float or None, optional
        Solver time limit in seconds.
    tee : bool, optional
        Stream raw solver output.
    export : bool, optional
        Write the solution back onto ``grid``.
    PV_set : bool, optional
        Fix PV-bus setpoints instead of optimising them.
    alpha : float or None, optional
        Weighting between CAPEX (``alpha``) and OPEX (``1-alpha``).
    callback : bool, optional
        Enable the solver-progress callback.
    solver_options : dict or None, optional
        Extra solver options.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    nlp_warmstart : bool, optional
        Warm-start the NLP from a relaxed/previous solution.
    initiate_max : bool, optional
        Initialise expandable elements at their maximum allowed installation.
    build_only : bool, optional
        Build the Pyomo model and skip the solver call.

    Returns
    -------
    tuple
        ``(model, model_results, timing_info, solver_stats)``.
    """
    grid.reset_run_flags()
    t1 = time.perf_counter()
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(
        grid,
        NPV,
        n_years,
        Hy,
        discount_rate,
        ObjRule,
        PV_set,
        initiate_max,
    )

    present_value = present_value_factor(Hy, discount_rate, n_years)
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

    if build_only:
        model_results, solver_stats = build_only_solver_stats(solver, model)
    else:
        model_results, solver_stats = pyomo_model_solve(
            model,
            grid,
            solver,
            tee,
            time_limit,
            callback=callback,
            solver_options=solver_options,
            nlp_warmstart=nlp_warmstart,
        )

    t1 = time.perf_counter()
    if export:
        if grid.ACmode:
            grid.create_Ybus_AC()
        if grid.DCmode:
            grid.create_Ybus_DC()
        export_acdc_nl_model_to_pyflow_acdc(model, grid, PZ,TEP=True)
        for obj in weights_def:
            weights_def[obj]['v']=calculate_objective(grid,obj)
            weights_def[obj]['NPV']=weights_def[obj]['v']*present_value
    t2 = time.perf_counter()

    t_modelexport = t2-t1


    grid.TEP_run=True
    grid.OPF_obj = weights_def

    timing_info = {
        "create": t_modelcreate,
        "solve": solver_stats["time"],
        "export": t_modelexport,
    }
    return model, model_results, timing_info, solver_stats

def _initialize_MS_STEP_sets_model(model,grid):
    if grid.DCmode:
        model.lines_DC    = pyo.Set(initialize=list(range(grid.nl_DC)))
    if grid.ACmode and grid.DCmode:
        model.conv        = pyo.Set(initialize=list(range(grid.nconv)))
    if grid.TEP_AC:
        model.lines_AC_exp= pyo.Set(initialize=list(range(grid.nle_AC)))
    if grid.REC_AC:
        model.lines_AC_rec= pyo.Set(initialize=list(range(grid.nlr_AC)))
    if grid.CT_AC:
        model.lines_AC_ct = pyo.Set(initialize=list(range(grid.nct_AC)))
        model.ct_set = pyo.Set(initialize=list(range(len(grid.Cable_options[0].cable_types))))
    if grid.ACmode and grid.n_gen > 0:
        model.gen_AC = pyo.Set(initialize=list(range(grid.n_gen)))
    if grid.n_ren > 0:
        model.ren_sources = pyo.Set(initialize=list(range(grid.n_ren)))

def alpha_pareto(grid,steps,ObjRule,NPV=True,n_years=25,Hy=HOURS_PER_YEAR,discount_rate=DEFAULT_DISCOUNT_RATE,solver='bonmin',time_limit=None,tee=False,save_name=None,obj_scaling=1.0):
    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule)
    present_value = present_value_factor(Hy, discount_rate, n_years)
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
                conv.NUmConvP = pyo.value(model.np_conv[c])

            save_network_svg(grid,save_path)


    df = pd.DataFrame(results)

    # Add normalized columns
    df['norm_TEP'] = df['obj_TEP'] / df['obj_TEP'].max()
    df['norm_OPF'] = df['obj_OPF'] / df['obj_OPF'].max()



    return df

def rate_sensitivity(grid,steps,ObjRule,min_rate=0.0,max_rate=0.1,NPV=True,n_years=25,Hy=HOURS_PER_YEAR,solver='bonmin',time_limit=None,tee=False,obj_scaling=1.0):

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

def kappa_sensitivity(grid,steps,ObjRule,min_kappa=0.0,max_kappa=1.0,NPV=True,n_years=25,Hy=HOURS_PER_YEAR,discount_rate=DEFAULT_DISCOUNT_RATE,solver='bonmin',time_limit=None,tee=False,obj_scaling=1.0):

    model, obj_TEP, obj_OPF,weights_def,PZ = _prepare_TEP_model(grid,NPV,n_years,Hy,discount_rate,ObjRule)

    results = []
    model.kappa = pyo.Param(initialize=min_kappa,mutable=True)
    present_value =  present_value_factor(Hy, discount_rate, n_years)


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
    Hy=HOURS_PER_YEAR,
    discount_rate=DEFAULT_DISCOUNT_RATE,
    solver='bonmin',
    time_limit=None,
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

def _create_scenarios(
    model,
    grid,
    Price_Zones,
    weights_def,
    n_clusters,
    clustering,
    limit_flow_rate,
):
    """Build one OPF sub-model per scenario frame and return scenario weights."""
    from ..Time_series import _modify_parameters

    w = {}

    base_model = pyo.ConcreteModel()
    opf_create_nl_model_acdc(base_model, grid, PV_set=False, Price_Zones=Price_Zones, TEP=True, limit_flow_rate=limit_flow_rate)

    for t in model.scenario_frames:
        base_model_copy = base_model.clone()
        model.scenario_model[t].transfer_attributes_from(base_model_copy)

        for ts in grid.Time_series:
            update_grid_scenario_frame(grid, ts, t, n_clusters, clustering)

        _modify_parameters(grid, model.scenario_model[t], Price_Zones)

        tep_sub_obj(model.scenario_model[t], grid, weights_def)
        if clustering:
            w[t] = float(grid.Clusters[n_clusters]['Weight'][t - 1])
        elif any(ts.element_name == 'TEP_w' for ts in grid.Time_series):
            w[t] = next(ts.data[t - 1] for ts in grid.Time_series if ts.element_name == 'TEP_w')
        else:
            w[t] = 1 / len(model.scenario_frames)

    return w

def multi_scenario_TEP(
    grid,
    NPV=True,
    n_years=25,
    Hy=HOURS_PER_YEAR,
    discount_rate=DEFAULT_DISCOUNT_RATE,
    clustering_options=None,
    ObjRule=None,
    solver='bonmin',
    tee=False,
    callback=False,
    alpha=None,
    limit_flow_rate=True,
    obj_scaling=1.0,
    solver_options=None,
    nlp_warmstart=False,
    initiate_max=False,
    build_only=False,
):
    """Build and solve a multi-scenario (clustered) static TEP.

    Like :func:`transmission_expansion`, but the operating cost is evaluated
    over several representative scenarios (from time-series clustering) with
    weights summing to one, so a single set of expansion decisions is optimal
    across all scenarios. Exports decisions and per-scenario results onto
    ``grid``.

    Parameters
    ----------
    grid : Grid
        Network with candidate expandable elements (mutated in place).
    NPV : bool, optional
        Discount OPEX to present value over the planning horizon.
    n_years : int, optional
        Planning horizon in years.
    Hy : float, optional
        Operating hours per year used to annualise OPEX.
    discount_rate : float, optional
        Annual discount rate for the present-value factor.
    clustering_options : dict or None, optional
        Options passed to the representative-period clustering.
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    solver : str, optional
        Pyomo (MINLP/NLP) solver name.
    tee : bool, optional
        Stream raw solver output.
    callback : bool, optional
        Enable the solver-progress callback.
    alpha : float or None, optional
        Weighting between CAPEX (``alpha``) and OPEX (``1-alpha``).
    limit_flow_rate : bool, optional
        Enforce line flow-rate limits.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    solver_options : dict or None, optional
        Extra solver options.
    nlp_warmstart : bool, optional
        Warm-start the NLP from a relaxed/previous solution.
    initiate_max : bool, optional
        Initialise expandable elements at their maximum allowed installation.
    build_only : bool, optional
        Build the Pyomo model and return without solving or exporting results.

    Returns
    -------
    tuple
        ``(model, model_results, timing_info, solver_stats,
        TEP_multiScenario_res)``.
    """
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate
    if tee:
        print('Trying clustering')
    try:
        from ..Time_series_clustering import cluster_analysis
        n_clusters,clustering = cluster_analysis(grid,clustering_options)
        if (clustering_options and clustering_options.get('print_details')) or tee:
            print('Clustering done')
    except Exception:
        n_clusters = len(grid.Time_series[0].data)
        clustering = False

    t1 = time.time()
    model = pyo.ConcreteModel()
    model.name        ="TEP TS MTDC AC/DC hybrid OPF"
    model.scenario_frames = pyo.Set(initialize=range(1, n_clusters + 1))

    #print(list(model.scenario_frames))
    model.scenario_model    = pyo.Block(model.scenario_frames)

    w = _create_scenarios(
        model,
        grid,
        Price_Zones,
        weights_def,
        n_clusters,
        clustering,
        limit_flow_rate,
    )

    _initialize_MS_STEP_sets_model(model, grid)
    TEP_variables(model, grid)
    _TEP_install_variables(model, grid, initiate_max=initiate_max)
    _TEP_install_constraints(model, grid)
    MS_TEP_constraints(model, grid)

    model.weights = pyo.Param(model.scenario_frames, initialize=w)
    obj_TEP = tep_obj(model, grid, NPV)
    pv = present_value_factor(Hy, discount_rate, n_years) if NPV else 1
    obj_weighted = weighted_subobj(model, pv)

    if alpha is None:
        total_cost = obj_TEP + obj_weighted
    else:
        total_cost = obj_TEP * alpha + obj_weighted * (1 - alpha)
    if obj_scaling != 1.0:
        total_cost = total_cost / obj_scaling
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    t2 = time.time()
    t_modelcreate = t2 - t1
    if tee:
        print('Model loaded')

    if build_only:
        model_results, solver_stats = build_only_solver_stats(solver, model)
    else:
        model_results, solver_stats = pyomo_model_solve(
            model, grid, solver, tee, callback=callback,
            solver_options=solver_options, nlp_warmstart=nlp_warmstart,
        )

    t1 = time.perf_counter()
    TEP_multiScenario_res = export_acdc_tep_ms_to_pyflow_acdc(model, grid, n_clusters, clustering, Price_Zones)

    TEP_multiScenario_res['OPF_obj'] = weights_def

    t2 = time.perf_counter()
    t_modelexport = t2-t1

    # TEP_multiScenario_res ={}

    grid.TEP_run=True
    grid.TEP_multiScenario_res = TEP_multiScenario_res
    grid.OPF_obj = weights_def

    timing_info = {
        "create": t_modelcreate,
        "solve": solver_stats["time"],
        "export": t_modelexport,
    }

    return model, model_results, timing_info, solver_stats, TEP_multiScenario_res


def tep_sub_obj(scenario_model,grid,ObjRule):
    obj_rule= opf_obj(scenario_model,grid,ObjRule)
    scenario_model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)


def tep_obj(model,grid,NPV):

    def Gen_investments():
        Gen_Inv=0
        for g in model.gen_AC:
            gen = grid.Generators[g]
            if gen.np_gen_opf:
                Gen_Inv += model.np_gen_install[g] * gen.base_cost
        return Gen_Inv
    def Renewable_investments():
        Renewable_Inv=0
        for rs in model.ren_sources:
            ren_source = grid.RenSources[rs]
            if ren_source.np_rsgen_opf:
                Renewable_Inv += model.np_rsgen_install[rs] * ren_source.base_cost
        return Renewable_Inv
    def AC_Line_investments():
        AC_Inv_lines=0
        for l in model.lines_AC_exp:
            line = grid.lines_AC_exp[l]
            if line.np_line_opf:
               if NPV:
                   AC_Inv_lines += model.NumLinesACP_install[l] * line.base_cost
               else:
                   AC_Inv_lines += model.NumLinesACP_install[l] * line.base_cost / line.life_time_hours

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
                 Inv_lines+=model.NumLinesDCP_install[l]*line.base_cost
             else:
                 Inv_lines+=model.NumLinesDCP_install[l]*line.base_cost/line.life_time_hours
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
            if conv.np_conv_opf:
               if NPV:
                 Inv_conv += model.np_conv_install[cn] * conv.base_cost
               else:
                 Inv_conv += model.np_conv_install[cn] * conv.base_cost / conv.life_time_hours
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

def weighted_subobj(model, scaling_factor):
    weighted_cost = 0
    for t in model.scenario_frames:
        weighted_cost += model.weights[t] * model.scenario_model[t].obj.expr
        model.scenario_model[t].obj.deactivate()
    return weighted_cost * scaling_factor


def get_price_zone_data(t, model, grid,n_clusters,clustering):
    row_data_price = {'Time_Frame': t}
    row_data_pz_lb = {'Time_Frame': t}
    row_data_pz_ub = {'Time_Frame': t}
    row_data_a = {'Time_Frame': t}
    row_data_b = {'Time_Frame': t}
    row_data_SC = {'Time_Frame': t}
    row_data_PN = {'Time_Frame': t}
    row_data_GEN = {'Time_Frame': t}
    # Collect price_zone data

    for m in grid.Price_Zones:
        nM = m.price_zone_num
        row_data_price[m.name] = np.round(np.float64(pyo.value(model.scenario_model[t].price_zone_price[nM])), decimals=2)

        from ..Classes import Price_Zone
        gen=0
        for node in m.nodes_AC:
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
            PN_lb = np.float64(pyo.value(model.scenario_model[t].PGL_min[nM]))
            PN_ub = np.float64(pyo.value(model.scenario_model[t].PGL_max[nM]))
            a = np.float64(pyo.value(model.scenario_model[t].price_zone_a[nM]))
            b = np.float64(pyo.value(model.scenario_model[t].price_zone_b[nM]))
            row_data_pz_lb[m.name] = np.round(PN_lb * grid.S_base, decimals=2)
            row_data_pz_ub[m.name] = np.round(PN_ub * grid.S_base, decimals=2)
            row_data_a[m.name] = a
            row_data_b[m.name] = b
            row_data_SC[m.name] = np.round(SC / 1000, decimals=2)

            PN = np.float64(pyo.value(model.scenario_model[t].PN[nM]))
            row_data_PN[m.name] = np.round(PN * grid.S_base, decimals=2)

    # PZ_load: per zone, sum of scenario model P_known on zone nodes (pu) × S_base → MW (model sign).
    row_data_load = {'Time_Frame': t}
    scen = model.scenario_model[t]
    for m in grid.Price_Zones:
        load_pu = 0.0
        for node in m.nodes_AC:
            n_ac = node.nodeNumber
            load_pu += pyo.value(scen.P_known_AC[n_ac])
        if grid.DCmode and hasattr(scen, 'P_known_DC'):
            for node in m.nodes_DC:
                n_dc = node.nodeNumber
                load_pu += pyo.value(scen.P_known_DC[n_dc])
        row_data_load[m.name] = np.round(load_pu * grid.S_base, decimals=2)

    return (
        row_data_price,
        row_data_SC,
        row_data_PN,
        row_data_GEN,
        row_data_pz_lb,
        row_data_pz_ub,
        row_data_a,
        row_data_b,
        row_data_load,
    )

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

            PGi_ren=rs.PGi_ren_base*factor*pyo.value(model.np_rsgen[rs.rsNumber])
        except KeyError:
            PGi_ren=rs.PGi_ren_base*rs.PRGi_available*pyo.value(model.np_rsgen[rs.rsNumber])
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
                n_lines_ac = np.float64(pyo.value(model.scenario_model[t].NumLinesACP[ln]))
                if n_lines_ac <= 0.01:
                    row_data_lines[l.name] = 0
                else:
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
                state = 1 if pyo.value(model.rec_branch[ln]) >= BINARY_THRESHOLD else 0
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
                ct_selected = [pyo.value(model.ct_branch[ln,ct]) >= BINARY_THRESHOLD for ct in model.ct_set]
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
                n_lines_dc = np.float64(pyo.value(model.scenario_model[t].NumLinesDCP[ln]))
                if n_lines_dc <= 0.01:
                    row_data_lines[l.name] = 0
                else:
                    p_to = np.float64(pyo.value(model.scenario_model[t].PDC_to[ln])) * grid.S_base
                    p_from = np.float64(pyo.value(model.scenario_model[t].PDC_from[ln])) * grid.S_base
                    load = max(abs(p_to), abs(p_from)) / l.MW_rating * 100
                    row_data_lines[l.name] = np.round(load, decimals=0).astype(int)

    return row_data_lines

def get_converter_data(t, model, grid):
    row_data_conv = {'Time_Frame': t}

    for conv in grid.Converters_ACDC:
        if conv.np_conv_opf:
            cn = conv.ConvNumber
            nconv = np.float64(pyo.value(model.scenario_model[t].np_conv[cn]))
            if nconv <= 0.01:
                row_data_conv[conv.name] = 0
            else:
                p_s = np.float64(pyo.value(model.scenario_model[t].P_conv_s_AC[cn])) * grid.S_base * nconv
                q_s = np.float64(pyo.value(model.scenario_model[t].Q_conv_s_AC[cn])) * grid.S_base * nconv
                p_c = np.float64(pyo.value(model.scenario_model[t].P_conv_c_AC[cn])) * grid.S_base * nconv
                p_loss = np.float64(pyo.value(model.scenario_model[t].P_conv_loss[cn])) * grid.S_base * nconv
                s_ac = np.sqrt(p_s**2 + q_s**2)
                p_dc = abs(p_c + p_loss)
                loading = max(s_ac, p_dc) / (conv.MVA_max * nconv) * 100
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
            # Renewable injections are scaled by installed units in the model equations.
            PGen = np.float64(
                pyo.value(
                    model.scenario_model[t].P_renSource[rn]
                    * model.scenario_model[t].gamma[rn]
                    * model.scenario_model[t].np_rsgen[rn]
                )
            ) * grid.S_base
            QGen = np.float64(
                pyo.value(model.scenario_model[t].Q_renSource[rn] * model.scenario_model[t].np_rsgen[rn])
            ) * grid.S_base
            row_data_gen[f'R_{rg.name}'] = np.round(PGen, decimals=2)
            row_data_qgen[f'R_{rg.name}'] = np.round(QGen, decimals=2)

    return row_data_gen,row_data_qgen


def export_acdc_tep_ms_to_pyflow_acdc(model,grid,n_clusters,clustering,Price_Zones,mutate_grid=True,not_transposed=False):
    grid.OPF_run=True

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
    data_rows_pz_lb = []
    data_rows_pz_ub = []
    data_rows_a = []
    data_rows_b = []
    data_rows_load = []
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
                (
                    price_data,
                    SC_data,
                    PN_data,
                    PZ_GEN_data,
                    pz_lb_data,
                    pz_ub_data,
                    a_data,
                    b_data,
                    load_data,
                ) = futures[i + 5].result()
                data_rows_price.append(price_data)
                data_rows_SC.append(SC_data)
                data_rows_PN.append(PN_data)
                data_rows_PZGEN.append(PZ_GEN_data)
                data_rows_pz_lb.append(pz_lb_data)
                data_rows_pz_ub.append(pz_ub_data)
                data_rows_a.append(a_data)
                data_rows_b.append(b_data)
                data_rows_load.append(load_data)

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
        data_pz_lb = pd.DataFrame(data_rows_pz_lb)
        data_pz_ub = pd.DataFrame(data_rows_pz_ub)
        data_a = pd.DataFrame(data_rows_a)
        data_b = pd.DataFrame(data_rows_b)
        data_load = pd.DataFrame(data_rows_load)
        # Transpose the DataFrame to flip rows and columns
        flipped_data_PN = data_PN.set_index('Time_Frame').T
        flipped_data_PZGEN = data_PZGEN.set_index('Time_Frame').T
        flipped_data_SC = data_SC.set_index('Time_Frame').T
        flipped_data_price = data_price.set_index('Time_Frame').T
        flipped_data_pz_lb = data_pz_lb.set_index('Time_Frame').T
        flipped_data_pz_ub = data_pz_ub.set_index('Time_Frame').T
        flipped_data_load = data_load.set_index('Time_Frame').T

    else:
        # Create empty DataFrames with the same structure
        flipped_data_PN = pd.DataFrame()
        flipped_data_PZGEN = pd.DataFrame()
        flipped_data_SC = pd.DataFrame()
        flipped_data_price = pd.DataFrame()
        flipped_data_pz_lb = pd.DataFrame()
        flipped_data_pz_ub = pd.DataFrame()
        flipped_data_load = pd.DataFrame()
        data_load = pd.DataFrame()
        # Read by the not_transposed export below
        data_PN = data_PZGEN = data_SC = data_price = None
        data_pz_lb = data_pz_ub = data_a = data_b = None

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
    'PZ_lb': flipped_data_pz_lb if flipped_data_pz_lb is not None else None,
    'PZ_ub': flipped_data_pz_ub if flipped_data_pz_ub is not None else None,
    'PZ_load': flipped_data_load if Price_Zones else None,

    'curtailment': flipped_data_curt,
    'curtailment_per': flipped_data_curt_per,
    'lines': flipped_data_lines,
    'converters': flipped_data_conv,
    'price': flipped_data_price,
    'pgen': flipped_data_pgen,
    'qgen': flipped_data_qgen,
    }

    if not_transposed:
        TEP_multiScenario_res =     {


        'PN': data_PN.set_index('Time_Frame') if data_PN is not None else None,
        'PZ_GEN': data_PZGEN.set_index('Time_Frame') if data_PZGEN is not None else None,
        'PZ_cost_of_generation': data_SC.set_index('Time_Frame') if data_SC is not None else None,
        'PZ_lb': data_pz_lb.set_index('Time_Frame') if data_pz_lb is not None else None,
        'PZ_ub': data_pz_ub.set_index('Time_Frame') if data_pz_ub is not None else None,
        'PZ_load': data_load.set_index('Time_Frame') if Price_Zones and data_load is not None else None,
        'a': data_a.set_index('Time_Frame') if data_a is not None else None,
        'b': data_b.set_index('Time_Frame') if data_b is not None else None,

        'curtailment': data_curt.set_index('Time_Frame'),
        'curtailment_per': data_curt_per.set_index('Time_Frame'),
        'lines': data_lines.set_index('Time_Frame'),
        'converters': data_conv.set_index('Time_Frame'),
        'price': data_price.set_index('Time_Frame'),
        }

    if mutate_grid:
        dominant_t = max(
            model.scenario_frames,
            key=lambda t: pyo.value(model.weights[t]),
        )
        export_acdc_nl_model_to_pyflow_acdc(
            model.scenario_model[dominant_t], grid, Price_Zones, TEP=True
        )
        if grid.TEP_AC:
            grid.line_ac_calc_exp()

    return TEP_multiScenario_res



def export_TEP_multiScenario_results_to_excel(grid, export):
    """Export multi-scenario TEP results to an Excel workbook.

    Writes expansion decisions, per-scenario operating results, and time-series
    tables from ``grid.TEP_multiScenario_res`` (populated by
    :func:`multi_scenario_TEP`).

    Parameters
    ----------
    grid : Grid
        Grid with multi-scenario TEP results on ``grid.TEP_multiScenario_res``.
    export : str
        Output path. ``.xlsx`` is appended when missing.

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> grid, res = pyf.cases["NS_MTDC_2025"](years_data="23,24")
    >>> pyf.multi_scenario_TEP(grid)
    >>> pyf.export_TEP_multiScenario_results_to_excel(grid, "results.xlsx")
    """

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
                ini = l.np_line_b
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
                ini = l.np_line_b
                opt = l.np_line
                pr = opt * l.MW_rating
                cost = ((opt - ini) * l.base_cost)  / 1000

                tot += cost
                data.append([element, "DC Line", ini, np.round(opt, decimals=2), np.round(pr, decimals=0).astype(int), np.round(cost, decimals=2)])

    if grid.ACmode and grid.DCmode:
        # Loop through ACDC converters and add data to the list
        for cn in grid.Converters_ACDC:
            if cn.np_conv_opf:
                element = cn.name
                ini = cn.np_conv_b
                opt = cn.np_conv
                pr = opt * cn.MVA_max
                cost = ((opt - ini) * cn.base_cost)  / 1000
                tot += cost

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


    if not export.endswith('.xlsx'):
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
            opf_obj = calculate_objective_from_model(model.scenario_model[t],grid,weights_def)
            opf_objs.append(opf_obj)
    else:
        opf_objs = [calculate_objective_from_model(model,grid,weights_def)]

    tep_obj_expr = tep_obj(model,grid,True)
    tep_obj_value = pyo.value(tep_obj_expr)
    return opf_objs, tep_obj_value
