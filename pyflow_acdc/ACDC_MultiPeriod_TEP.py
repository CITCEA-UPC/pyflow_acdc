import numpy as np
import pyomo.environ as pyo
import pandas as pd
import time
import math
from concurrent.futures import ThreadPoolExecutor
import os
import copy

from .ACDC_OPF_NL_model import OPF_create_NLModel_ACDC,TEP_variables,ExportACDC_NLmodel_toPyflowACDC
from .ACDC_OPF import pyomo_model_solve,OPF_obj,obj_w_rule,calculate_objective,calculate_objective_from_model,Optimal_PF
from .ACDC_Static_TEP import (
    get_TEP_variables,
    _initialize_MS_STEP_sets_model,
    update_grid_scenario_frame,
    ExportACDC_TEP_MS_toPyflowACDC,
)
from .grid_analysis import analyse_grid, current_fuel_type_distribution
from .Time_series import _modify_parameters, TS_ACDC_OPF, results_TS_OPF
from .Graph_and_plot import save_network_svg, create_geometries
from .Results_class import Results



__all__ = [
    'multi_period_transmission_expansion',
    'multi_period_MS_TEP',
    'save_MP_TEP_period_svgs',
    'export_and_save_inv_period_svgs',
    'run_opf_for_investment_period',
    'run_ts_opf_for_investment_period',
    'run_opf_for_all_investment_periods',
]

def pack_variables(*args):
    return args


def _snapshot_ts_results(grid):
    """Deep-copy TS DataFrames from grid after TS_ACDC_OPF (for Dash / comparisons)."""
    return {
        'time_series_results': copy.deepcopy(grid.time_series_results),
        'S_base': float(getattr(grid, 'S_base', 100.0)),
    }

def _inv_decision(element, key):
    return element.investment_decisions[key]

def _fill_investment_decisions(grid):
    """
    Harmonize all MP investment arrays to one period length.

    Rules:
    - If one or more series have length > 1, they must all have the same length.
    - Length-1 series are treated as defaults and broadcast to the target length.
    - Empty series are invalid and raise an error.
    """
    
    def _iter_elements():
        for element in grid.Price_Zones:
            yield element
        for element in grid.nodes_AC:
            yield element
        for element in grid.nodes_DC:
            yield element
        for element in grid.Generators:
            if element.np_gen_opf:
                yield element
        for element in grid.RenSources:
            if element.np_rsgen_opf:
                yield element
        for element in grid.lines_AC_exp:
            if element.np_line_opf:
                yield element
        for element in grid.lines_DC:
            if element.np_line_opf:
                yield element
        for element in grid.Converters_ACDC:
            if element.np_conv_opf:
                yield element

    def _as_list(values):
        if values is None:
            return None
        return np.atleast_1d(values).tolist()

    def _series_length(values):
        values_list = _as_list(values)
        if values_list is None:
            return 0
        return len(values_list)

    # Collect all non-default lengths (>1) to determine target period length.
    lengths_gt1 = []
    for element in _iter_elements():
        for values in element.investment_decisions.values():
            length = _series_length(values)
            if length > 1:
                lengths_gt1.append(length)

    unique_lengths = sorted(set(lengths_gt1))
    if len(unique_lengths) > 1:
        raise ValueError(
            f"Inconsistent investment period lengths found: {unique_lengths}. "
            "Only length-1 defaults may differ; all other lengths must match."
        )
    target_len = unique_lengths[0] if unique_lengths else 1

    def _normalize(values, context):
        values_list = _as_list(values)
        if values_list is None:
            return None
        if len(values_list) == 0:
            raise ValueError(f"{context} has no period values")
        if len(values_list) == 1 and target_len > 1:
            return [values_list[0]] * target_len
        if len(values_list) != target_len:
            raise ValueError(
                f"{context} has length {len(values_list)} but expected {target_len}. "
                "Only length-1 defaults are auto-expanded."
            )
        return values_list

    def _dynamic_max_cap(element):
        if hasattr(element, "np_gen_max"):
            return float(element.np_gen_max)
        if hasattr(element, "np_rsgen_max"):
            return float(element.np_rsgen_max)
        if hasattr(element, "np_line_max"):
            return float(element.np_line_max)
        if hasattr(element, "np_conv_max"):
            return float(element.np_conv_max)
        return None

    # Normalize object-owned investment decisions.
    for element in _iter_elements():
        for key, values in list(element.investment_decisions.items()):
            element.investment_decisions[key] = _normalize(
                values,
                f"{element.name}:{key}"
            )

        # Keep per-period investment caps consistent with static max stock.
        cap = _dynamic_max_cap(element)
        if cap is not None:
            max_inv = [float(v) for v in element.investment_decisions["max_inv"]]
            element.investment_decisions["max_inv"] = [min(v, cap) for v in max_inv]
    return target_len

def _update_grid_investment_period(grid, i):
    idx = i

    def _inv_at(inv, key, period_idx, fallback):
        series = inv.get(key)
        if isinstance(series, (list, tuple)) and period_idx < len(series):
            return series[period_idx]
        return fallback

    for price_zone in grid.Price_Zones:
        inv = price_zone.investment_decisions
        price_zone.PLi_inv_factor = inv['Load'][idx]
        price_zone.curvature_factor = inv['curvature_factor'][idx]
        price_zone.import_expand = inv['import_expand'][idx]

    for node in grid.nodes_AC:
        if node.PLi_linked == True:
            continue
        inv = node.investment_decisions
        node.PLi_inv_factor = inv['Load'][idx]

    for node in grid.nodes_DC:
        if node.PLi_linked == True:
            continue
        inv = node.investment_decisions
        node.PLi_inv_factor = inv['Load'][idx]

    for element in grid.Generators + grid.RenSources + grid.lines_AC_exp + grid.lines_DC + grid.Converters_ACDC:
        inv = element.investment_decisions
        element.lamda_capex = _inv_at(inv, 'lamda_capex', idx, element.lamda_capex)


def _MP_TEP_constraints(model,grid):
    if grid.rs_GPR:
        def MP_rsgen_link(model,rs,i):
            return model.inv_model[i].np_rsgen[rs] == model.np_rsgen[rs,i]
        model.MP_rsgen_link_constraint = pyo.Constraint(model.ren_sources,model.inv_periods,rule=MP_rsgen_link)

        def MP_rsgen_decomision(model,rs,i):
            ren_source = grid.RenSources[rs]
            planned_decomision = _inv_decision(ren_source, 'planned_decomision')[i]
            decomision_period = ren_source.decomision_period
            if i < decomision_period:
                return model.decomision_rsgen[rs,i] == planned_decomision
            else:
                return model.decomision_rsgen[rs,i] == planned_decomision + model.installed_rsgen[rs,i-decomision_period]
        model.MP_rsgen_decomision_constraint = pyo.Constraint(model.ren_sources,model.inv_periods,rule=MP_rsgen_decomision)

        def MP_rsgen_installation(model,rs,i):
            return model.installed_rsgen[rs,i] == model.planned_installation_rsgen[rs,i]+model.opt_installation_rsgen[rs,i]
        model.MP_rsgen_installation_constraint = pyo.Constraint(model.ren_sources,model.inv_periods,rule=MP_rsgen_installation)

        def MP_rsgen_installed(model,rs,i):
            if i == 0:
                return model.np_rsgen[rs,i] == model.installed_rsgen[rs,i]+model.np_rsgen_base[rs]
            else:
                return model.np_rsgen[rs,i] == model.installed_rsgen[rs,i]+model.np_rsgen[rs,i-1]-model.decomision_rsgen[rs,i]
        model.MP_rsgen_installed_constraint = pyo.Constraint(model.ren_sources,model.inv_periods,rule=MP_rsgen_installed)

    if grid.GPR:
        def MP_gen_link(model,g,i):
            return model.inv_model[i].np_gen[g] == model.np_gen[g,i]
        model.MP_gen_link_constraint = pyo.Constraint(model.gen_AC,model.inv_periods,rule=MP_gen_link)

        def MP_gen_decomision(model,g,i):
            gen = grid.Generators[g]
            planned_decomision = _inv_decision(gen, 'planned_decomision')[i]
            decomision_period = gen.decomision_period
            if i < decomision_period:
                return model.decomision_gen[g,i] == planned_decomision
            else:
                return model.decomision_gen[g,i] == planned_decomision + model.installed_gen[g,i-decomision_period]
        model.MP_gen_decomision_constraint = pyo.Constraint(model.gen_AC,model.inv_periods,rule=MP_gen_decomision)

        def MP_gen_installation(model,g,i):
            return model.installed_gen[g,i] == model.planned_installation_gen[g,i]+model.opt_installation_gen[g,i]
        model.MP_gen_installation_constraint = pyo.Constraint(model.gen_AC,model.inv_periods,rule=MP_gen_installation)

        def MP_gen_installed(model,g,i):
            if i == 0:
                return model.np_gen[g,i] == model.installed_gen[g,i]+model.np_gen_base[g]
            else:
                return model.np_gen[g,i] == model.installed_gen[g,i]+model.np_gen[g,i-1]-model.decomision_gen[g,i]
            
        model.MP_gen_installed_constraint = pyo.Constraint(model.gen_AC,model.inv_periods,rule=MP_gen_installed)

    if grid.ACmode:
        if grid.TEP_AC:
            def MP_AC_line_link(model, l, i):
                return model.inv_model[i].NumLinesACP[l] == model.ACLinesMP[l, i]
            model.MP_AC_line_link_constraint = pyo.Constraint(model.lines_AC_exp, model.inv_periods, rule=MP_AC_line_link)

            def MP_AC_line_decomision(model, l, i):
                line = grid.lines_AC_exp[l]
                planned_decomision = _inv_decision(line, 'planned_decomision')[i]
                decomision_period = line.decomision_period
                if i < decomision_period:
                    return model.decomision_ACline[l,i] == planned_decomision
                else:
                    return model.decomision_ACline[l,i] == planned_decomision + model.installed_ACline[l,i-decomision_period]
            model.MP_AC_line_decomision_constraint = pyo.Constraint(model.lines_AC_exp, model.inv_periods, rule=MP_AC_line_decomision)

            def MP_AC_line_installation(model, l, i):
                return model.installed_ACline[l,i] == model.planned_installation_ACline[l,i] + model.opt_installation_ACline[l,i]
            model.MP_AC_line_installation_constraint = pyo.Constraint(model.lines_AC_exp, model.inv_periods, rule=MP_AC_line_installation)

            def MP_AC_line_installed(model, l, i):
                if i == 0:
                    return model.ACLinesMP[l,i] == model.installed_ACline[l,i] + model.NumLinesACP_base[l]
                else:
                    return model.ACLinesMP[l,i] == model.installed_ACline[l,i] + model.ACLinesMP[l,i-1] - model.decomision_ACline[l,i]
            model.MP_AC_line_installed_constraint = pyo.Constraint(model.lines_AC_exp, model.inv_periods, rule=MP_AC_line_installed)

    if grid.DCmode:
        def MP_DC_line_link(model, l, i):
            return model.inv_model[i].NumLinesDCP[l] == model.DCLinesMP[l, i]
        model.MP_DC_line_link_constraint = pyo.Constraint(model.lines_DC, model.inv_periods, rule=MP_DC_line_link)

        def MP_DC_line_decomision(model, l, i):
            line = grid.lines_DC[l]
            planned_decomision = _inv_decision(line, 'planned_decomision')[i]
            decomision_period = line.decomision_period
            if i < decomision_period:
                return model.decomision_DCline[l,i] == planned_decomision
            else:
                return model.decomision_DCline[l,i] == planned_decomision + model.installed_DCline[l,i-decomision_period]
        model.MP_DC_line_decomision_constraint = pyo.Constraint(model.lines_DC, model.inv_periods, rule=MP_DC_line_decomision)

        def MP_DC_line_installation(model, l, i):
            return model.installed_DCline[l,i] == model.planned_installation_DCline[l,i] + model.opt_installation_DCline[l,i]
        model.MP_DC_line_installation_constraint = pyo.Constraint(model.lines_DC, model.inv_periods, rule=MP_DC_line_installation)

        def MP_DC_line_installed(model, l, i):
            if i == 0:
                return model.DCLinesMP[l,i] == model.installed_DCline[l,i] + model.NumLinesDCP_base[l]
            else:
                return model.DCLinesMP[l,i] == model.installed_DCline[l,i] + model.DCLinesMP[l,i-1] - model.decomision_DCline[l,i]
        model.MP_DC_line_installed_constraint = pyo.Constraint(model.lines_DC, model.inv_periods, rule=MP_DC_line_installed)

    if grid.ACmode and grid.DCmode:
        def MP_Conv_link(model, c, i):
            return model.inv_model[i].np_conv[c] == model.ConvMP[c, i]
        model.MP_Conv_link_constraint = pyo.Constraint(model.conv, model.inv_periods, rule=MP_Conv_link)

        def MP_Conv_decomision(model, c, i):
            conv = grid.Converters_ACDC[c]
            planned_decomision = _inv_decision(conv, 'planned_decomision')[i]
            decomision_period = conv.decomision_period
            if i < decomision_period:
                return model.decomision_Conv[c,i] == planned_decomision
            else:
                return model.decomision_Conv[c,i] == planned_decomision + model.installed_Conv[c,i-decomision_period]
        model.MP_Conv_decomision_constraint = pyo.Constraint(model.conv, model.inv_periods, rule=MP_Conv_decomision)

        def MP_Conv_installation(model, c, i):
            return model.installed_Conv[c,i] == model.planned_installation_Conv[c,i] + model.opt_installation_Conv[c,i]
        model.MP_Conv_installation_constraint = pyo.Constraint(model.conv, model.inv_periods, rule=MP_Conv_installation)

        def MP_Conv_installed(model, c, i):
            if i == 0:
                return model.ConvMP[c,i] == model.installed_Conv[c,i] + model.np_conv_base[c]
            else:
                return model.ConvMP[c,i] == model.installed_Conv[c,i] + model.ConvMP[c,i-1] - model.decomision_Conv[c,i]
        model.MP_Conv_installed_constraint = pyo.Constraint(model.conv, model.inv_periods, rule=MP_Conv_installed)

def _MP_GEN_balance_constraints(model, grid):
    # Same logic as static GEN balance, indexed by investment period.
    n_periods = len(list(model.inv_periods))
    gen_type_limits = {}
    for k, v in grid.generation_type_limits.items():
        key = k.lower()
        if isinstance(v, (list, tuple, np.ndarray)):
            vals = [float(x) for x in v]
            if len(vals) == 1 and n_periods > 1:
                vals = vals * n_periods
            elif len(vals) != n_periods:
                raise ValueError(
                    f"generation_type_limits['{k}'] has length {len(vals)} but expected {n_periods}"
                )
        else:
            vals = [float(v)] * n_periods
        gen_type_limits[key] = vals

    if all(all(x == 1 for x in vals) for vals in gen_type_limits.values()):
        return

    model.gen_types = pyo.Set(initialize=list(gen_type_limits.keys()))
    model.gen_type_limits = pyo.Param(
        model.gen_types,
        model.inv_periods,
        initialize=lambda m, gt, i: gen_type_limits[gt][int(i)],
    )

    def normalize_type(type_name):
        return type_name.lower() if type_name else None

    def gen_type_max_capacity_rule(model, gen_type, i):
        gen_capacity = 0
        for gen in grid.Generators:
            if normalize_type(gen.gen_type) != gen_type:
                continue
            g = gen.genNumber
            if grid.GPR and g in model.gen_AC:
                gen_capacity += gen.Max_pow_gen * model.np_gen[g, i]
            else:
                gen_capacity += gen.Max_pow_gen * gen.np_gen

        ren_capacity = 0
        for rs in grid.RenSources:
            if normalize_type(rs.rs_type) != gen_type:
                continue
            r = rs.rsNumber
            if grid.rs_GPR and r in model.ren_sources:
                ren_capacity += rs.PGi_ren_base * model.np_rsgen[r, i]
            else:
                ren_capacity += rs.PGi_ren_base * rs.np_rsgen

        return gen_capacity + ren_capacity

    model.gen_type_max_capacity = pyo.Expression(model.gen_types, model.inv_periods, rule=gen_type_max_capacity_rule)

    def total_max_capacity_rule(model, i):
        return sum(model.gen_type_max_capacity[gt, i] for gt in model.gen_types)

    model.total_max_capacity = pyo.Expression(model.inv_periods, rule=total_max_capacity_rule)

    def gen_type_balance_rule(model, gen_type, i):
        return model.gen_type_max_capacity[gen_type, i] <= model.total_max_capacity[i] * model.gen_type_limits[gen_type, i]

    model.gen_type_balance_constraint = pyo.Constraint(model.gen_types, model.inv_periods, rule=gen_type_balance_rule)


def _MP_TEP_variables(model, grid):
    
    tep_vars = get_TEP_variables(grid)
    gen_set = list(model.gen_AC) if hasattr(model, "gen_AC") else []
    rs_set = list(model.ren_sources) if hasattr(model, "ren_sources") else []
    ac_line_set = list(model.lines_AC_exp) if hasattr(model, "lines_AC_exp") else []
    dc_line_set = list(model.lines_DC) if hasattr(model, "lines_DC") else []
    conv_set = list(model.conv) if hasattr(model, "conv") else []

    np_gen_max_install={}
    for g in gen_set:
        vals = _inv_decision(grid.Generators[g], 'max_inv')
        for i in model.inv_periods:
            np_gen_max_install[(g, i)] = vals[i]
    np_rsgen_max_install={}
    for r in rs_set:
        vals = _inv_decision(grid.RenSources[r], 'max_inv')
        for i in model.inv_periods:
            np_rsgen_max_install[(r, i)] = vals[i]
    np_acline_max_install = {}
    for l in ac_line_set:
        vals = _inv_decision(grid.lines_AC_exp[l], 'max_inv')
        for i in model.inv_periods:
            np_acline_max_install[(l, i)] = vals[i]
    np_dcline_max_install = {}
    for l in dc_line_set:
        vals = _inv_decision(grid.lines_DC[l], 'max_inv')
        for i in model.inv_periods:
            np_dcline_max_install[(l, i)] = vals[i]
    np_conv_max_install = {}
    for c in conv_set:
        vals = _inv_decision(grid.Converters_ACDC[c], 'max_inv')
        for i in model.inv_periods:
            np_conv_max_install[(c, i)] = vals[i]

    def planned_installation_rsgen_init(model, rs, i):
        return _inv_decision(grid.RenSources[rs], 'planned_installation')[i]
    def planned_installation_gen_init(model, g, i):
        return _inv_decision(grid.Generators[g], 'planned_installation')[i]
    def planned_installation_ACline_init(model, l, i):
        return _inv_decision(grid.lines_AC_exp[l], 'planned_installation')[i]
    def planned_installation_DCline_init(model, l, i):
        return _inv_decision(grid.lines_DC[l], 'planned_installation')[i]
    def planned_installation_Conv_init(model, c, i):
        return _inv_decision(grid.Converters_ACDC[c], 'planned_installation')[i]

    def min_install_opt(element, planned, max_install):
        allows_decrease = element.allow_planned_decrease
        return -min(planned, max_install) if allows_decrease else 0

    if grid.rs_GPR:
        np_rsgen = tep_vars['ren_sources']['np_rsgen']
        np_rsgen_max = tep_vars['ren_sources']['np_rsgen_max']

        model.np_rsgen_base = pyo.Param(model.ren_sources,initialize=np_rsgen)
        
        def np_rsgen_bounds(model,rs,i):
            return (0,np_rsgen_max[rs])
        def np_rsgen_bounds_install(model,rs,i):
            planned = planned_installation_rsgen_init(model, rs, i)
            max_install = np_rsgen_max_install[(rs, i)]
            return (max(0.0, planned - max_install), planned + max_install)
        def np_rsgen_bounds_install_opt(model,rs,i):
            ren_source = grid.RenSources[rs]
            if ren_source.np_rsgen_opf:
                planned = planned_installation_rsgen_init(model, rs, i)
                max_install = np_rsgen_max_install[(rs, i)]
                return (min_install_opt(ren_source, planned, max_install), max_install)
            else:
                return (0,0)  
        def np_rsgen_i(model, rs, i):
            return np_rsgen[rs]
        model.np_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.NonNegativeIntegers,bounds=np_rsgen_bounds,initialize=np_rsgen_i)
        model.installed_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=planned_installation_rsgen_init,bounds=np_rsgen_bounds_install)
        model.planned_installation_rsgen = pyo.Param(model.ren_sources,model.inv_periods,initialize=planned_installation_rsgen_init)
        model.opt_installation_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.Integers,initialize=0,bounds=np_rsgen_bounds_install_opt)
        
        model.decomision_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)
    
    if grid.GPR:
        np_gen = tep_vars['generators']['np_gen']
        np_gen_max = tep_vars['generators']['np_gen_max']

        model.np_gen_base = pyo.Param(model.gen_AC,initialize=np_gen)
        
        def np_gen_bounds(model,g,i):
            return (0,np_gen_max[g])

        def np_gen_bounds_install(model,g,i):
            planned = planned_installation_gen_init(model, g, i)
            max_install = np_gen_max_install[(g, i)]
            return (max(0.0, planned - max_install), planned + max_install)
        def np_gen_bounds_install_opt(model,g,i):
            gen = grid.Generators[g]
            if gen.np_gen_opf:
                planned = planned_installation_gen_init(model, g, i)
                max_install = np_gen_max_install[(g, i)]
                return (min_install_opt(gen, planned, max_install), max_install)
            else:
                return (0,0)
        def np_gen_i(model, g, i):
            return np_gen[g]
        model.np_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.NonNegativeIntegers,bounds=np_gen_bounds,initialize=np_gen_i)
        model.installed_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=planned_installation_gen_init,bounds=np_gen_bounds_install)
        model.planned_installation_gen = pyo.Param(model.gen_AC,model.inv_periods,initialize=planned_installation_gen_init)
        model.opt_installation_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.Integers,initialize=0,bounds=np_gen_bounds_install_opt)
        
        model.decomision_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)

    if grid.ACmode:
        NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
        NP_lineAC_max = tep_vars['ac_lines']['NP_lineAC_max']
        if grid.TEP_AC:
            model.NumLinesACP_base  =pyo.Param(model.lines_AC_exp,initialize=NP_lineAC)
            def MP_AC_line_bounds(model,l,i):
                return (0,NP_lineAC_max[l])
            def MP_AC_line_bounds_install(model,l,i):
                planned = planned_installation_ACline_init(model, l, i)
                max_install = np_acline_max_install[(l, i)]
                return (max(0.0, planned - max_install), planned + max_install)
            def MP_AC_line_bounds_install_opt(model,l,i):
                line = grid.lines_AC_exp[l]
                if line.np_line_opf:
                    planned = planned_installation_ACline_init(model, l, i)
                    max_install = np_acline_max_install[(l, i)]
                    return (min_install_opt(line, planned, max_install), max_install)
                else:
                    return (0,0)
            def NP_lineAC_i(model, l, i):
                return NP_lineAC[l]
            model.ACLinesMP = pyo.Var(model.lines_AC_exp,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_AC_line_bounds,initialize=NP_lineAC_i)
            model.installed_ACline = pyo.Var(model.lines_AC_exp,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=planned_installation_ACline_init,bounds=MP_AC_line_bounds_install)
            model.planned_installation_ACline = pyo.Param(model.lines_AC_exp,model.inv_periods,initialize=planned_installation_ACline_init)
            model.opt_installation_ACline = pyo.Var(model.lines_AC_exp,model.inv_periods,within=pyo.Integers,initialize=0,bounds=MP_AC_line_bounds_install_opt)
            model.decomision_ACline = pyo.Var(model.lines_AC_exp,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)
    if grid.DCmode:
        NP_lineDC = tep_vars['dc_lines']['NP_lineDC']
        NP_lineDC_max = tep_vars['dc_lines']['NP_lineDC_max']
        
        model.NumLinesDCP_base  =pyo.Param(model.lines_DC,initialize=NP_lineDC)
        def MP_DC_line_bounds(model,l,i):
            return (0,NP_lineDC_max[l])
        def MP_DC_line_bounds_install(model,l,i):
            planned = planned_installation_DCline_init(model, l, i)
            max_install = np_dcline_max_install[(l, i)]
            return (max(0.0, planned - max_install), planned + max_install)
        def MP_DC_line_bounds_install_opt(model,l,i):
            line = grid.lines_DC[l]
            if line.np_line_opf:
                planned = planned_installation_DCline_init(model, l, i)
                max_install = np_dcline_max_install[(l, i)]
                return (min_install_opt(line, planned, max_install), max_install)
            else:
                return (0,0)
        def NP_lineDC_i(model, l, i):
            return NP_lineDC[l]
        model.DCLinesMP = pyo.Var(model.lines_DC,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_DC_line_bounds,initialize=NP_lineDC_i)
        model.installed_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=planned_installation_DCline_init,bounds=MP_DC_line_bounds_install)
        model.planned_installation_DCline = pyo.Param(model.lines_DC,model.inv_periods,initialize=planned_installation_DCline_init)
        model.opt_installation_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.Integers,initialize=0,bounds=MP_DC_line_bounds_install_opt)
        model.decomision_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)

    if grid.ACmode and grid.DCmode:
        np_conv = tep_vars['converters']['np_conv']
        np_conv_max = tep_vars['converters']['np_conv_max']
        model.np_conv_base  =pyo.Param(model.conv,initialize=np_conv)
        def MP_Conv_bounds(model,c,i):
            return (0,np_conv_max[c])
        def MP_Conv_bounds_install(model,c,i):
            planned = planned_installation_Conv_init(model, c, i)
            max_install = np_conv_max_install[(c, i)]
            return (max(0.0, planned - max_install), planned + max_install)
        def MP_Conv_bounds_install_opt(model,c,i):
            conv = grid.Converters_ACDC[c]
            if conv.np_conv_opf:
                planned = planned_installation_Conv_init(model, c, i)
                max_install = np_conv_max_install[(c, i)]
                return (min_install_opt(conv, planned, max_install), max_install)
            else:
                return (0,0)
        def np_conv_i(model, c, i):
            return np_conv[c]
        model.ConvMP = pyo.Var(model.conv,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_Conv_bounds,initialize=np_conv_i)
        model.installed_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=planned_installation_Conv_init,bounds=MP_Conv_bounds_install)
        model.planned_installation_Conv = pyo.Param(model.conv,model.inv_periods,initialize=planned_installation_Conv_init)
        model.opt_installation_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.Integers,initialize=0,bounds=MP_Conv_bounds_install_opt)
        model.decomision_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)
def _validate_grid_for_MP_TEP(grid):
    """
    Fast pre-solve validation for MP TEP inputs.

    Current checks:
    - planned_decomision[p] >= 0 for all periods
    - sum(planned_decomision) <= pre-existing stock
    - cumulative planned_decomision[t] <= stock[t] where
      stock[t] = pre-existing + cumulative planned_installation[t]
    """
    def _as_float_series(values, label, name, key):
        series = np.array(values, dtype=float).reshape(-1)
        if series.size == 0:
            raise ValueError(f"{label} '{name}' has empty {key} series")
        return series

    def _validate_element_planned_decomision(element, base_count, label):
        inv = element.investment_decisions
        name = element.name
        required_keys = ('planned_installation', 'planned_decomision', 'max_inv', 'np_dynamic')
        for key in required_keys:
            if key not in inv:
                raise ValueError(f"{label} '{name}' is missing investment_decisions['{key}']")

        series = {
            key: _as_float_series(inv[key], label, name, key)
            for key in required_keys
        }
        lengths = {arr.size for arr in series.values()}
        if len(lengths) != 1:
            raise ValueError(
                f"{label} '{name}' has mismatched investment series lengths: "
                f"planned_installation={series['planned_installation'].size}, "
                f"planned_decomision={series['planned_decomision'].size}, "
                f"max_inv={series['max_inv'].size}, np_dynamic={series['np_dynamic'].size}"
            )
        planned_installation = series['planned_installation']
        planned_decomision = series['planned_decomision']

        if np.any(planned_installation < 0):
            bad_idx = np.where(planned_installation < 0)[0][0]
            bad_val = float(planned_installation[bad_idx])
            raise ValueError(
                f"{label} '{name}' has negative planned_installation at period {int(bad_idx)}: {bad_val}"
            )

        if np.any(planned_decomision < 0):
            bad_idx = np.where(planned_decomision < 0)[0][0]
            bad_val = float(planned_decomision[bad_idx])
            raise ValueError(
                f"{label} '{name}' has negative planned_decomision at period {int(bad_idx)}: {bad_val}"
            )

        if np.any(series['max_inv'] < 0):
            bad_idx = np.where(series['max_inv'] < 0)[0][0]
            bad_val = float(series['max_inv'][bad_idx])
            raise ValueError(
                f"{label} '{name}' has negative max_inv at period {int(bad_idx)}: {bad_val}"
            )

        if np.any(series['np_dynamic'] < 0):
            bad_idx = np.where(series['np_dynamic'] < 0)[0][0]
            bad_val = float(series['np_dynamic'][bad_idx])
            raise ValueError(
                f"{label} '{name}' has negative np_dynamic at period {int(bad_idx)}: {bad_val}"
            )

        base_count = float(base_count)
        if base_count < 0:
            raise ValueError(f"{label} '{name}' has negative base count: {base_count}")
        total_decom = float(np.sum(planned_decomision))
        if total_decom > base_count + 1e-9:
            raise ValueError(
                f"{label} '{name}' violates baseline decommission check: "
                f"sum(planned_decomision)={total_decom} > base_count={base_count}"
            )

        cum_decom = np.cumsum(planned_decomision)
        cum_install = np.cumsum(planned_installation)
        available_stock = base_count + cum_install
        bad = np.where(cum_decom > available_stock + 1e-9)[0]
        if bad.size > 0:
            t = int(bad[0])
            raise ValueError(
                f"{label} '{name}' violates stock-aware decommission check at period {t}: "
                f"cum_decom={float(cum_decom[t])} > available={float(available_stock[t])}"
            )

    def _validate_static_parameters(element, base_count, max_count, label):
        name = element.name

        life_time = float(element.life_time)
        if life_time <= 0:
            raise ValueError(f"{label} '{name}' has non-positive life_time: {life_time}")

        base_cost = float(element.base_cost)
        if base_cost < 0:
            raise ValueError(f"{label} '{name}' has negative base_cost: {base_cost}")

        base_count = float(base_count)
        max_count = float(max_count)
        if max_count < 0:
            raise ValueError(f"{label} '{name}' has negative max count: {max_count}")
        if base_count > max_count + 1e-9:
            raise ValueError(
                f"{label} '{name}' has base count greater than max count: "
                f"base_count={base_count} > max_count={max_count}"
            )

    element_groups = [
        (grid.Generators, lambda e: e.np_gen_opf, lambda e: e.np_gen, lambda e: e.np_gen_max, "Generator"),
        (grid.RenSources, lambda e: e.np_rsgen_opf, lambda e: e.np_rsgen, lambda e: e.np_rsgen_max, "RenSource"),
        (grid.lines_AC_exp, lambda e: e.np_line_opf, lambda e: e.np_line, lambda e: e.np_line_max, "AC line"),
        (grid.lines_DC, lambda e: e.np_line_opf, lambda e: e.np_line, lambda e: e.np_line_max, "DC line"),
        (grid.Converters_ACDC, lambda e: e.np_conv_opf, lambda e: e.np_conv, lambda e: e.np_conv_max, "Converter"),
    ]
    for elements, is_active, base_count, max_count, label in element_groups:
        for element in elements:
            if is_active(element):
                _validate_static_parameters(element, base_count(element), max_count(element), label)
                _validate_element_planned_decomision(element, base_count(element), label)

def multi_period_transmission_expansion(
    grid,
    inv_periods=[],
    n_years=10,
    Hy=8760,
    discount_rate=0.02,
    ObjRule=None,
    solver='bonmin',
    time_limit=None,
    tee=False,
    callback=False,
    solver_options=None,
    obj_scaling=1.0,
    alpha=None,
    capex_budget=None,
    nlp_warmstart=False,
):
    grid.reset_run_flags()
    analyse_grid(grid)
    weights_def, PZ = obj_w_rule(grid,ObjRule,True)

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate =discount_rate
    
    # If inv_periods is provided, set default load multipliers directly on objects.
    if inv_periods:
        load_factors = np.array(inv_periods, dtype=float)
        # Keep behavior consistent with prior shorthand by setting node loads too.
        for node in grid.nodes_AC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()

        for node in grid.nodes_DC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()
    
    n_periods = _fill_investment_decisions(grid)
    
    _validate_grid_for_MP_TEP(grid)

    grid.GPR = bool(grid.GPR) or any(
        gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
        for gen in grid.Generators
    )
    grid.rs_GPR = bool(grid.rs_GPR) or any(
        rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))
        for rs in grid.RenSources
    )
    
    for gen in grid.Generators:
        gen.np_gen_mp = gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
    for rs in grid.RenSources:
        rs.np_rsgen_mp = rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))
    
    t1=time.time()
    _deactivate_non_pre_existing_loads(grid)
    pre_opt_fuel_type_distribution = current_fuel_type_distribution(grid, output='df')

    model = pyo.ConcreteModel()
    model.name        ="Dynamic TEP MTDC AC/DC hybrid OPF"

    model.inv_periods = pyo.Set(initialize=list(range(0,n_periods)))
    grid.TEP_n_periods = n_periods
    model.inv_model = pyo.Block(model.inv_periods)

    base_model = pyo.ConcreteModel()
    OPF_create_NLModel_ACDC(base_model,grid,PV_set=False,Price_Zones=PZ,TEP=True)

    for element in grid.Generators + grid.lines_AC_exp + grid.lines_DC + grid.Converters_ACDC+grid.RenSources: 
        _calculate_decomision_period(element,n_years)
        
    present_value_opf =   Hy*(1 - (1 + discount_rate) ** -n_years) / discount_rate
    for i in model.inv_periods:
        base_model_copy = base_model.clone()
        model.inv_model[i].transfer_attributes_from(base_model_copy)

        _update_grid_investment_period(grid, i)

        _modify_parameters(grid,model.inv_model[i],PZ)

        
        obj_OPF = OPF_obj(model.inv_model[i],grid,weights_def,True)
    
        obj_OPF *=present_value_opf
        
        model.inv_model[i].obj = pyo.Objective(rule=obj_OPF, sense=pyo.minimize)

    _initialize_MPTEP_sets_model(model,grid)
    _MP_TEP_variables(model, grid)
    _MP_TEP_constraints(model,grid)
    _MP_GEN_balance_constraints(model,grid)
    _MP_TEP_capex_budget_constraint(model,grid,capex_budget=capex_budget)
    

    net_cost = _MP_TEP_obj(model,grid,n_years,discount_rate,alpha=alpha)
    if obj_scaling != 1.0:
        net_cost = net_cost / obj_scaling
    model.obj = pyo.Objective(rule=net_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    
    t2 = time.time()

    model_results,solver_stats = pyomo_model_solve(
        model, grid, solver, time_limit=time_limit, tee=tee,
        callback=callback, solver_options=solver_options, nlp_warmstart=nlp_warmstart
    )
    
    t3 = time.time()

    if not (solver_stats and solver_stats.get('solution_found', False)):
        termination = solver_stats.get('termination_condition', 'unknown') if solver_stats else 'unknown'
        solver_message = solver_stats.get('solver_message', '') if solver_stats else ''
        if tee:
            print(f"MP-TEP failed: no feasible solution found (termination: {termination}).")
            if solver_message:
                print(f"Solver message: {solver_message}")
        timing_info = {
            "create": t2 - t1,
            "solve": solver_stats['time'] if solver_stats else None,
            "export": 0.0,
        }
        return model, model_results, timing_info, solver_stats
    
    MINLP = False
    if solver != 'ipopt':
        MINLP = True
    
    export_MP_TEP_results_toPyflowACDC(
        model,
        grid,
        Price_Zones=PZ,
        MINLP=MINLP,
        pre_opt_fuel_type_distribution=pre_opt_fuel_type_distribution,
    )
    _save_inv_models(model,grid)
    t4 = time.time()

    inv_objs, inv_opf_objs = calculate_MPTEP_objective_from_model(model,grid,weights_def,n_years,discount_rate,multi_scenario=False)
    
    # Build list of rows then create DataFrame once to avoid concat-on-empty FutureWarning
    obj_rows = []
    for i in model.inv_periods:
        present_value_tep = 1/(1+discount_rate)**(i*n_years)
        
        opf_obj = inv_opf_objs[i][0]  # Get first element from the list
        npv_opf_obj = opf_obj*present_value_opf
        inv_obj = inv_objs[i]
        economic_step_obj = inv_obj + npv_opf_obj
        if alpha is None:
            step_obj = economic_step_obj
        else:
            step_obj = alpha * inv_obj + (1 - alpha) * npv_opf_obj
        npv_step_obj = step_obj*present_value_tep
        npv_economic_step_obj = economic_step_obj*present_value_tep
        obj_rows.append({
            'Investment_Period': i+1,
            'OPF_Objective': opf_obj,
            'NPV_OPF_Objective': npv_opf_obj,
            'TEP_Objective': inv_obj,
            'STEP_Objective': step_obj,
            'NPV_STEP_Objective': npv_step_obj,
            'STEP_Objective_Economic': economic_step_obj,
            'NPV_STEP_Objective_Economic': npv_economic_step_obj
        })
    obj_res = pd.DataFrame(obj_rows, columns=['Investment_Period', 'OPF_Objective',
                                              'NPV_OPF_Objective','TEP_Objective',
                                              'STEP_Objective','NPV_STEP_Objective',
                                              'STEP_Objective_Economic','NPV_STEP_Objective_Economic'])
    grid.MP_TEP_obj_res = obj_res
    timing_info = {
    "create": t2-t1,
    "solve": solver_stats['time'],
    "export": t4-t3,
    }

    
    
    return model, model_results ,timing_info, solver_stats
    
def _initialize_MPTEP_sets_model(model,grid):    

    if grid.DCmode:
        model.lines_DC = pyo.Set(
            initialize=[i for i, line in enumerate(grid.lines_DC) if line.np_line_opf]
        )
    if grid.ACmode and grid.DCmode:
        model.conv = pyo.Set(
            initialize=[i for i, conv in enumerate(grid.Converters_ACDC) if conv.np_conv_opf]
        )
    if grid.TEP_AC:
        model.lines_AC_exp = pyo.Set(
            initialize=[i for i, line in enumerate(grid.lines_AC_exp) if line.np_line_opf]
        )
    if grid.GPR:
        model.gen_AC = pyo.Set(
            initialize=[i for i, gen in enumerate(grid.Generators) if getattr(gen, "np_gen_mp", False)]
        )
    if grid.rs_GPR:
        model.ren_sources = pyo.Set(
            initialize=[i for i, rs in enumerate(grid.RenSources) if getattr(rs, "np_rsgen_mp", False)]
        )



def _period_base_cost(element, i):
    return float(element._base_cost) * (1.0 + element.investment_decisions['lamda_capex'][i])

def _inv_model_obj(model,grid,i):
    inv_gen= 0
    AC_Inv_lines=0
    DC_Inv_lines=0
    Conv_Inv=0
    inv_rs=0
    if grid.rs_GPR:
        for rs in model.ren_sources:
            ren_source = grid.RenSources[rs]
            inv_rs += model.installed_rsgen[rs, i] * _period_base_cost(ren_source, i)
    else:
        inv_rs=0

    if grid.GPR:
        
        for g in model.gen_AC:
            gen = grid.Generators[g]
            inv_gen += model.installed_gen[g, i] * _period_base_cost(gen, i)
    else:
        inv_gen=0


    if grid.ACmode:
        if grid.TEP_AC:
            for l in model.lines_AC_exp:
                line = grid.lines_AC_exp[l]
                AC_Inv_lines += model.installed_ACline[l, i] * _period_base_cost(line, i)
            
    if grid.DCmode:
        for l in model.lines_DC:
            line = grid.lines_DC[l]
            DC_Inv_lines += model.installed_DCline[l, i] * _period_base_cost(line, i)
        
    if grid.ACmode and grid.DCmode:
        for c in model.conv:
            conv = grid.Converters_ACDC[c]
            Conv_Inv += model.installed_Conv[c, i] * _period_base_cost(conv, i)
        

    inv_cost=inv_gen+AC_Inv_lines+DC_Inv_lines+Conv_Inv+inv_rs
    return inv_cost

def _MP_TEP_capex_budget_constraint(model,grid,capex_budget=None):
    # Optional period CAPEX budget (Eq. 15): Psi_x <= Psi_budget,x
    if capex_budget is None:
        capex_budget = getattr(grid, 'MP_TEP_CAPEX_budget', None)
    if capex_budget is None:
        return

    period_list = list(model.inv_periods)
    n_periods = len(period_list)

    if np.isscalar(capex_budget):
        budget_dict = {i: float(capex_budget) for i in period_list}
    elif isinstance(capex_budget, dict):
        budget_dict = {}
        for i in period_list:
            if i not in capex_budget:
                raise ValueError(f"Missing CAPEX budget for period {i}")
            budget_dict[i] = float(capex_budget[i])
    else:
        budget_arr = np.array(capex_budget, dtype=float).reshape(-1)
        if len(budget_arr) != n_periods:
            raise ValueError(
                f"CAPEX budget length ({len(budget_arr)}) does not match number of investment periods ({n_periods})"
            )
        budget_dict = {i: float(budget_arr[i]) for i in period_list}

    model.capex_budget = pyo.Param(model.inv_periods, initialize=budget_dict)

    def MP_CAPEX_budget_rule(model, i):
        return _inv_model_obj(model, grid, i) <= model.capex_budget[i]

    model.MP_CAPEX_budget_constraint = pyo.Constraint(model.inv_periods, rule=MP_CAPEX_budget_rule)

def _MP_TEP_obj(model,grid,n_years,discount_rate,alpha=None):
    if alpha is not None:
        try:
            alpha = float(alpha)
        except (TypeError, ValueError):
            raise ValueError("alpha must be None or a numeric value in [0, 1].")
        if alpha < 0.0 or alpha > 1.0:
            raise ValueError("alpha must be in [0, 1].")
    
    net_cost = 0

    for i in model.inv_periods:
        inv_cost = _inv_model_obj(model,grid,i)
        opf_cost = model.inv_model[i].obj.expr
        if alpha is None:
            instance_cost = opf_cost + inv_cost
        else:
            instance_cost = alpha * inv_cost + (1 - alpha) * opf_cost
        net_cost += instance_cost/(1+discount_rate)**(i*n_years)
        model.inv_model[i].obj.deactivate()

    return net_cost

def export_and_save_inv_period_svgs(grid,Price_Zones=False,folder_name=None):
    if folder_name is not None:
        os.makedirs(folder_name, exist_ok=True)
    if hasattr(grid, 'inv_models'):
        grid_name = grid.name
        grid_name = grid_name.replace(" ", "_")
        
        for i in grid.inv_models:
            save_path = f"{folder_name}/{grid_name}_inv_model_{i}" if folder_name else f'{grid_name}_inv_model_{i}'
            ExportACDC_NLmodel_toPyflowACDC(grid.inv_models[i],grid,Price_Zones,TEP=True)
            save_network_svg(
                grid,
                name=save_path,
                journal=True,
                legend=True,
            )

    else:
        print("No inv_models found")

def _save_inv_models(model,grid):
    grid.inv_models = {}
    for i in model.inv_periods:
        grid.inv_models[i] = model.inv_model[i]

def export_MP_TEP_results_toPyflowACDC(
    model,
    grid,
    Price_Zones=False,
    MINLP=False,
    *,
    pre_opt_fuel_type_distribution,
    export_last_opf_state=True,
    MS = False,
):
    

    grid.MP_TEP_run = (not MS)
    grid.MP_MS_TEP_run = MS
    
    n_periods = grid.TEP_n_periods
    
    rows = []
    
    if grid.GPR:
        if MINLP:
            gen_mp_values = {(g, i): round(pyo.value(model.np_gen[g, i])) for (g, i) in model.np_gen}
            gen_installed_values = {(g, i): int(round(pyo.value(model.installed_gen[g, i]))) for (g, i) in model.installed_gen}
            gen_decomision_values = {(g, i): int(round(pyo.value(model.decomision_gen[g, i]))) for (g, i) in model.decomision_gen}
        else:
            gen_mp_values = {(g, i): round(pyo.value(model.np_gen[g, i]),2) for (g, i) in model.np_gen}
            gen_installed_values = {(g, i): round(pyo.value(model.installed_gen[g, i]),2) for (g, i) in model.installed_gen}
            gen_decomision_values = {(g, i): round(pyo.value(model.decomision_gen[g, i]),2) for (g, i) in model.decomision_gen}
            
        for gen in grid.Generators:
            g = gen.genNumber
            gen.investment_decisions['np_dynamic'] = [gen_mp_values[g, i] for i in range(n_periods)]
            row = {'Element': str(gen.name)}
            row['Type'] = 'Generator'
            row['Pre Existing'] = pyo.value(model.np_gen_base[g])
            total_cost = 0
            for i in range(n_periods):
                n_val = gen_mp_values[g, i]
                cost = gen_installed_values[g, i] * _period_base_cost(gen, i)
                row[f"Decommissioned_{i+1}"] = gen_decomision_values[g, i]
                row[f"Installed_{i+1}"] = gen_installed_values[g, i]    
                row[f"Active_{i+1}"] = n_val                
                row[f"Cost_{i+1}"] = cost
                total_cost += cost
            row['Total_Cost'] = total_cost
            rows.append(row)
    if grid.rs_GPR:
        if MINLP:
            rs_mp_values = {(rs, i): round(pyo.value(model.np_rsgen[rs, i])) for (rs, i) in model.np_rsgen}
            rs_installed_values = {(rs, i): int(round(pyo.value(model.installed_rsgen[rs, i]))) for (rs, i) in model.installed_rsgen}
            rs_decomision_values = {(rs, i): int(round(pyo.value(model.decomision_rsgen[rs, i]))) for (rs, i) in model.decomision_rsgen}
        else:
            rs_mp_values = {(rs, i): round(pyo.value(model.np_rsgen[rs, i]),2) for (rs, i) in model.np_rsgen}
            rs_installed_values = {(rs, i): round(pyo.value(model.installed_rsgen[rs, i]),2) for (rs, i) in model.installed_rsgen}
            rs_decomision_values = {(rs, i): round(pyo.value(model.decomision_rsgen[rs, i]),2) for (rs, i) in model.decomision_rsgen}
            
        for ren_source in grid.RenSources:
            rs = ren_source.rsNumber
            ren_source.investment_decisions['np_dynamic'] = [rs_mp_values[rs, i] for i in range(n_periods)]
            row = {'Element': str(ren_source.name)}
            row['Type'] = 'Renewable Source'
            row['Pre Existing'] = pyo.value(model.np_rsgen_base[rs])
            total_cost = 0
            for i in range(n_periods):
                n_val = rs_mp_values[rs, i]
                cost = rs_installed_values[rs, i] * _period_base_cost(ren_source, i)
                row[f"Decommissioned_{i+1}"] = rs_decomision_values[rs, i]
                row[f"Installed_{i+1}"] = rs_installed_values[rs, i]    
                row[f"Active_{i+1}"] = n_val                
                row[f"Cost_{i+1}"] = cost
                total_cost += cost
            row['Total_Cost'] = total_cost
            rows.append(row)

    if grid.ACmode:
        if grid.TEP_AC:
            if MINLP:
                ac_lines_mp_values = {(l, i): round(pyo.value(model.ACLinesMP[l, i])) for (l, i) in model.ACLinesMP}
                ac_line_installed_values = {(l, i): int(round(pyo.value(model.installed_ACline[l, i]))) for (l, i) in model.installed_ACline}
                ac_line_decomision_values = {(l, i): int(round(pyo.value(model.decomision_ACline[l, i]))) for (l, i) in model.decomision_ACline}
            else:
                ac_lines_mp_values = {(l, i): round(pyo.value(model.ACLinesMP[l, i]),2) for (l, i) in model.ACLinesMP}
                ac_line_installed_values = {(l, i): round(pyo.value(model.installed_ACline[l, i]),2) for (l, i) in model.installed_ACline}
                ac_line_decomision_values = {(l, i): round(pyo.value(model.decomision_ACline[l, i]),2) for (l, i) in model.decomision_ACline}
            for line in grid.lines_AC_exp:
                l = line.lineNumber
                line.investment_decisions['np_dynamic'] = [ac_lines_mp_values[l, i] for i in range(n_periods)]
                row = {'Element': str(line.name)}
                row['Type'] = 'AC Line'
                row['Pre Existing'] = pyo.value(model.NumLinesACP_base[l])
                total_cost = 0
                for i in range(n_periods):
                    n_val = ac_lines_mp_values[l, i]
                    cost = ac_line_installed_values[l, i] * _period_base_cost(line, i)
                    row[f"Decommissioned_{i+1}"] = ac_line_decomision_values[l, i]
                    row[f"Installed_{i+1}"] = ac_line_installed_values[l, i]
                    row[f"Active_{i+1}"] = n_val
                    row[f"Cost_{i+1}"] = cost
                    total_cost += cost
                row['Total_Cost'] = total_cost
                rows.append(row)
        
        


    if grid.DCmode:
        if MINLP:
            dc_lines_mp_values = {(l, i): round(pyo.value(model.DCLinesMP[l, i])) for (l, i) in model.DCLinesMP}
            dc_line_installed_values = {(l, i): int(round(pyo.value(model.installed_DCline[l, i]))) for (l, i) in model.installed_DCline}
            dc_line_decomision_values = {(l, i): int(round(pyo.value(model.decomision_DCline[l, i]))) for (l, i) in model.decomision_DCline}
        else:
            dc_lines_mp_values = {(l, i): round(pyo.value(model.DCLinesMP[l, i]),2) for (l, i) in model.DCLinesMP}
            dc_line_installed_values = {(l, i): round(pyo.value(model.installed_DCline[l, i]),2) for (l, i) in model.installed_DCline}
            dc_line_decomision_values = {(l, i): round(pyo.value(model.decomision_DCline[l, i]),2) for (l, i) in model.decomision_DCline}

        for line in grid.lines_DC:  
            if line.np_line_opf:
                l = line.lineNumber
                line.investment_decisions['np_dynamic'] = [dc_lines_mp_values[l, i] for i in range(n_periods)]
                row = {'Element': str(line.name)}
                row['Type'] = 'DC Line'
                row['Pre Existing'] = pyo.value(model.NumLinesDCP_base[l])
                total_cost = 0
                for i in range(n_periods):
                    n_val = dc_lines_mp_values[l, i]
                    cost = dc_line_installed_values[l, i] * _period_base_cost(line, i)
                    row[f"Decommissioned_{i+1}"] = dc_line_decomision_values[l, i]
                    row[f"Installed_{i+1}"] = dc_line_installed_values[l, i]
                    row[f"Active_{i+1}"] = n_val
                    row[f"Cost_{i+1}"] = cost
                    total_cost += cost
                row['Total_Cost'] = total_cost
                rows.append(row)

    if grid.ACmode and grid.DCmode:
        if MINLP:
            acdc_conv_mp_values = {(c, i): round(pyo.value(model.ConvMP[c, i])) for (c, i) in model.ConvMP}
            conv_installed_values = {(c, i): int(round(pyo.value(model.installed_Conv[c, i]))) for (c, i) in model.installed_Conv}
            conv_decomision_values = {(c, i): int(round(pyo.value(model.decomision_Conv[c, i]))) for (c, i) in model.decomision_Conv}
        else:
            acdc_conv_mp_values = {(c, i): round(pyo.value(model.ConvMP[c, i]),2) for (c, i) in model.ConvMP}
            conv_installed_values = {(c, i): round(pyo.value(model.installed_Conv[c, i]),2) for (c, i) in model.installed_Conv}
            conv_decomision_values = {(c, i): round(pyo.value(model.decomision_Conv[c, i]),2) for (c, i) in model.decomision_Conv}
        for conv in grid.Converters_ACDC:
            c = conv.ConvNumber
            conv.investment_decisions['np_dynamic'] = [acdc_conv_mp_values[c, i] for i in range(n_periods)]
            row = {'Element': str(conv.name)}
            row['Type'] = 'ACDC Conv'
            row['Pre Existing'] = pyo.value(model.np_conv_base[c])
            total_cost = 0
            for i in range(n_periods):
                n_val = acdc_conv_mp_values[c, i]   
                cost = conv_installed_values[c, i] * _period_base_cost(conv, i)
                row[f"Decommissioned_{i+1}"] = conv_decomision_values[c, i]
                row[f"Installed_{i+1}"] = conv_installed_values[c, i]
                row[f"Active_{i+1}"] = n_val
                row[f"Cost_{i+1}"] = cost
                total_cost += cost
            row['Total_Cost'] = total_cost
            rows.append(row)    

    df = pd.DataFrame(rows)
    total_row = {}
    for col in df.columns:
        if col == "Element":
            total_row[col] = "Total cost"
        elif "Cost" in col:
            total_row[col] = df[col].sum()
        else:
            total_row[col] = ""
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    
    # Capture fuel-type distribution for each investment period based on solved dynamic states.
    # Key 0 stores the state before optimization.
    fuel_type_dist_by_period = {0: pre_opt_fuel_type_distribution}
    for i in model.inv_periods:
        _set_grid_to_multiperiod_state(grid, i,Price_Zones)
        
        fuel_type_dist_by_period[int(i) + 1] = current_fuel_type_distribution(grid, output='df')

    grid.MP_TEP_fuel_type_distribution = fuel_type_dist_by_period

    if export_last_opf_state:
        last_i = max(model.inv_periods)
        _set_grid_to_multiperiod_state(grid, last_i,Price_Zones)
        ExportACDC_NLmodel_toPyflowACDC(model.inv_model[last_i],grid,Price_Zones,TEP=True)

    grid.MP_TEP_results = df  


def _resolve_mp_ms_clustering(grid, clustering_options, tee=False):
    if clustering_options is None:
        if not grid.Time_series:
            raise ValueError("No time series available and clustering was not requested.")
        n_clusters = len(grid.Time_series[0].data)
        if n_clusters <= 0:
            raise ValueError("Time series is empty; cannot build scenario frames.")
        return n_clusters, False

    from .Time_series_clustering import cluster_analysis
    try:
        n_clusters, clustering = cluster_analysis(grid, clustering_options)
    except Exception as exc:
        raise RuntimeError("Clustering was requested but failed.") from exc

    if not clustering:
        raise RuntimeError("Clustering was requested but did not produce clustered scenarios.")
    if n_clusters <= 0:
        raise ValueError("Clustering returned zero scenarios.")
    if tee:
        print(f"Clustering succeeded with {n_clusters} scenarios.")
    return n_clusters, True


def _scenario_weight_for_frame(grid, t, n_clusters, clustering):
    if clustering:
        return float(grid.Clusters[n_clusters]['Weight'][t-1])
    if any(ts.element_name == 'TEP_w' for ts in grid.Time_series):
        return float(next(ts.data[t-1] for ts in grid.Time_series if ts.element_name == 'TEP_w'))
    return None


def _validate_period_scenario_updates(grid, period_idx, frame_idx, n_clusters, clustering):
    tol = 1e-8
    for pz in grid.Price_Zones:
        expected_curvature = _inv_decision(pz, 'curvature_factor')[period_idx]          
        if abs(float(pz.curvature_factor) - float(expected_curvature)) > tol:
            raise ValueError(
                f"Price zone '{pz.name}' curvature_factor mismatch at period {period_idx}, frame {frame_idx}."
            )

    for pz in grid.Price_Zones:
        expected_pli = float(pz._PLi_base) * float(pz.PLi_factor) * float(pz.PLi_inv_factor)
        if abs(float(pz.PLi) - expected_pli) > 1e-6:
            raise ValueError(
                f"Price zone '{pz.name}' load consistency mismatch at period {period_idx}, frame {frame_idx}."
            )

    for node in grid.nodes_AC:
        if node.PLi_linked:
            continue
        expected_pli = float(node._PLi_base) * float(node.PLi_factor) * float(node.PLi_inv_factor)
        if abs(float(node.PLi) - expected_pli) > 1e-6:
            raise ValueError(
                f"AC node '{node.name}' load consistency mismatch at period {period_idx}, frame {frame_idx}."
            )

    for node in grid.nodes_DC:
        if node.PLi_linked:
            continue
        expected_pli = float(node._PLi_base) * float(node.PLi_factor) * float(node.PLi_inv_factor)
        if abs(float(node.PLi) - expected_pli) > 1e-6:
            raise ValueError(
                f"DC node '{node.name}' load consistency mismatch at period {period_idx}, frame {frame_idx}."
            )


def _add_period_ms_link_constraints(period_block, grid):
    def NP_gen_link(m, gen, t):
        element = grid.Generators[gen]
        if element.np_gen_opf:
            return m.np_gen[gen] == m.scenario_model[t].np_gen[gen]
        return pyo.Constraint.Skip

    def NP_rsgen_link(m, rs, t):
        element = grid.RenSources[rs]
        if element.np_rsgen_opf:
            return m.np_rsgen[rs] == m.scenario_model[t].np_rsgen[rs]
        return pyo.Constraint.Skip

    def NP_ACline_link(m, line, t):
        element = grid.lines_AC_exp[line]
        if element.np_line_opf:
            return m.NumLinesACP[line] == m.scenario_model[t].NumLinesACP[line]
        return pyo.Constraint.Skip

    def NP_line_link(m, line, t):
        element = grid.lines_DC[line]
        if element.np_line_opf:
            return m.NumLinesDCP[line] == m.scenario_model[t].NumLinesDCP[line]
        return pyo.Constraint.Skip

    def NP_conv_link(m, conv, t):
        element = grid.Converters_ACDC[conv]
        if element.np_conv_opf:
            return m.np_conv[conv] == m.scenario_model[t].np_conv[conv]
        return pyo.Constraint.Skip

    if grid.GPR:
        period_block.NP_gen_link_constraint = pyo.Constraint(
            period_block.gen_AC, period_block.scenario_frames, rule=NP_gen_link
        )
    if grid.rs_GPR:
        period_block.NP_rsgen_link_constraint = pyo.Constraint(
            period_block.ren_sources, period_block.scenario_frames, rule=NP_rsgen_link
        )
    if grid.TEP_AC:
        period_block.NP_ACline_link_constraint = pyo.Constraint(
            period_block.lines_AC_exp, period_block.scenario_frames, rule=NP_ACline_link
        )
    if grid.DCmode:
        period_block.NP_line_link_constraint = pyo.Constraint(
            period_block.lines_DC, period_block.scenario_frames, rule=NP_line_link
        )
    if grid.ACmode and grid.DCmode:
        period_block.NP_conv_link_constraint = pyo.Constraint(
            period_block.conv, period_block.scenario_frames, rule=NP_conv_link
        )


def _build_period_scenario_block(
    model,
    grid,
    period_idx,
    base_model,
    Price_Zones,
    weights_def,
    n_clusters,
    clustering,
    n_years,
    Hy,
    discount_rate,
    NPV,
):
    period_block = model.inv_model[period_idx]
    period_block.scenario_frames = pyo.Set(initialize=range(1, n_clusters + 1))
    period_block.scenario_model = pyo.Block(period_block.scenario_frames)
    # Period block only carries shared TEP decisions; full OPF states live in scenario sub-blocks.
    _initialize_MS_STEP_sets_model(period_block, grid)
    TEP_variables(period_block, grid)

    _update_grid_investment_period(grid, period_idx)

    w = {}
    for t in period_block.scenario_frames:
        for ts in grid.Time_series:
            update_grid_scenario_frame(grid, ts, t, n_clusters, clustering)
        for price_zone in grid.Price_Zones:
            price_zone.update_a()

        _validate_period_scenario_updates(grid, period_idx, t, n_clusters, clustering)

        sc_block = period_block.scenario_model[t]
        sc_block.transfer_attributes_from(base_model.clone())
        _modify_parameters(grid, sc_block, Price_Zones)
        sc_obj = OPF_obj(sc_block, grid, weights_def, True)
        sc_block.obj = pyo.Objective(rule=sc_obj, sense=pyo.minimize)

        maybe_weight = _scenario_weight_for_frame(grid, t, n_clusters, clustering)
        if maybe_weight is None:
            maybe_weight = 1.0 / float(len(period_block.scenario_frames))
        w[t] = float(maybe_weight)

    period_block.weights = pyo.Param(period_block.scenario_frames, initialize=w)
    _add_period_ms_link_constraints(period_block, grid)

    expected_opf = sum(
        period_block.weights[t] * period_block.scenario_model[t].obj.expr
        for t in period_block.scenario_frames
    )
    for t in period_block.scenario_frames:
        period_block.scenario_model[t].obj.deactivate()

    scaling_factor = Hy
    if NPV:
        scaling_factor *= (1 - (1 + discount_rate) ** -n_years) / discount_rate
    expected_opf *= scaling_factor
    period_block.expected_opf = pyo.Expression(expr=expected_opf)
    period_block.obj = pyo.Objective(expr=period_block.expected_opf, sense=pyo.minimize)




def multi_period_MS_TEP(
    grid,
    inv_periods=[],
    NPV=True,
    n_years=10,
    Hy=8760,
    discount_rate=0.02,
    clustering_options=None,
    ObjRule=None,
    solver='bonmin',
    time_limit=None,
    tee=False,
    callback=False,
    alpha=None,
    limit_flow_rate=True,
    obj_scaling=1.0,
    solver_options=None,
    nlp_warmstart=False,
    capex_budget=None,
    save_period_svgs=True,
    period_svg_prefix='grid_MP_MS_TEP',
    period_svg_line_size_factor=1.0,
    build_only=False,
):
    grid.reset_run_flags()
    analyse_grid(grid)
    weights_def, Price_Zones = obj_w_rule(grid, ObjRule, True)

    if alpha is not None:
        try:
            alpha = float(alpha)
        except (TypeError, ValueError):
            raise ValueError("alpha must be None or a numeric value in [0, 1].")
        if alpha < 0.0 or alpha > 1.0:
            raise ValueError("alpha must be in [0, 1].")

    grid.TEP_n_years = n_years
    grid.TEP_discount_rate = discount_rate

    if inv_periods:
        load_factors = np.array(inv_periods, dtype=float)
        for node in grid.nodes_AC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()
        for node in grid.nodes_DC:
            node.investment_decisions['Load'] = load_factors.copy().tolist()

    n_periods = _fill_investment_decisions(grid)
    _validate_grid_for_MP_TEP(grid)

    grid.GPR = bool(grid.GPR) or any(
        gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
        for gen in grid.Generators
    )
    grid.rs_GPR = bool(grid.rs_GPR) or any(
        rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))
        for rs in grid.RenSources
    )
    for gen in grid.Generators:
        gen.np_gen_mp = gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
    for rs in grid.RenSources:
        rs.np_rsgen_mp = rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))

    n_clusters, clustering = _resolve_mp_ms_clustering(grid, clustering_options, tee=tee)

    t1 = time.time()
    pre_opt_fuel_type_distribution = current_fuel_type_distribution(grid, output='df')
    model = pyo.ConcreteModel()
    model.name = "MP TEP MS MTDC AC/DC hybrid OPF"
    model.inv_periods = pyo.Set(initialize=list(range(0, n_periods)))
    model.inv_model = pyo.Block(model.inv_periods)
    #model.clustering = clustering
    #model.n_clusters = n_clusters
    grid.TEP_n_periods = n_periods

    base_model = pyo.ConcreteModel()
    OPF_create_NLModel_ACDC(
        base_model, grid, PV_set=False, Price_Zones=Price_Zones, TEP=True, limit_flow_rate=limit_flow_rate
    )

    for element in grid.Generators + grid.lines_AC_exp + grid.lines_DC + grid.Converters_ACDC + grid.RenSources:
        _calculate_decomision_period(element, n_years)

    for i in model.inv_periods:
        _build_period_scenario_block(
            model,
            grid,
            i,
            base_model,
            Price_Zones,
            weights_def,
            n_clusters,
            clustering,
            n_years,
            Hy,
            discount_rate,
            NPV,
        )

    _initialize_MPTEP_sets_model(model, grid)
    _MP_TEP_variables(model, grid)
    _MP_TEP_constraints(model, grid)
    _MP_GEN_balance_constraints(model, grid)
    _MP_TEP_capex_budget_constraint(model, grid, capex_budget=capex_budget)

    net_cost = _MP_TEP_obj(model, grid, n_years, discount_rate, alpha=alpha)
    if obj_scaling != 1.0:
        net_cost = net_cost / obj_scaling
    model.obj = pyo.Objective(expr=net_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling

    if build_only:
        timing_info = {
            "create": time.time() - t1,
            "solve": None,
            "export": 0.0,
        }
        solver_stats = {
            "solver": None,
            "termination_condition": "build_only",
            "solver_message": "build_only=True: model built and solve skipped.",
            "solution_found": None,
            "time": None,
        }
        return model, None, timing_info, solver_stats, {}

    t2 = time.time()
    model_results, solver_stats = pyomo_model_solve(
        model, grid, solver, tee=tee, time_limit=time_limit, callback=callback,
        solver_options=solver_options, nlp_warmstart=nlp_warmstart
    )
    t3 = time.time()

    if not (solver_stats and solver_stats.get('solution_found', False)):
        termination = solver_stats.get('termination_condition', 'unknown') if solver_stats else 'unknown'
        solver_message = solver_stats.get('solver_message', '') if solver_stats else ''
        msg = f"MP-MS-TEP failed: no feasible solution found (termination: {termination})."
        if solver_message:
            msg = f"{msg} Solver message: {solver_message}"
        raise RuntimeError(msg)

    MINLP = solver != 'ipopt'
    export_MP_TEP_results_toPyflowACDC(
        model,
        grid,
        Price_Zones=Price_Zones,
        MINLP=MINLP,
        pre_opt_fuel_type_distribution=pre_opt_fuel_type_distribution,
        export_last_opf_state=False,
        MS=True,
    )
    _save_inv_models(model, grid)

    mp_ms_period_results = {}
    period_scenario_grid_res = {}
    obj_rows = []
    last_period = max(model.inv_periods)
    for i in model.inv_periods:
        period_block = model.inv_model[i]
        _set_grid_to_multiperiod_state(grid, i, Price_Zones)
        period_result = ExportACDC_TEP_MS_toPyflowACDC(
            period_block, grid, n_clusters, clustering, Price_Zones, mutate_grid=False
        )
        period_result['Investment_Period'] = int(i)
        mp_ms_period_results[int(i)] = period_result
        period_scenario_grid_res[int(i)] = {}
        for t in period_block.scenario_frames:
            period_scenario_grid_res[int(i)][int(t)] = {
                'weight': float(pyo.value(period_block.weights[t])),
                'opf_objective': float(calculate_objective_from_model(period_block.scenario_model[t], grid, weights_def, True)),
            }

        present_value_tep = 1 / (1 + discount_rate) ** (i * n_years)
        inv_obj = pyo.value(_inv_model_obj(model, grid, i))
        opex_obj = pyo.value(period_block.expected_opf)
        economic_step_obj = inv_obj + opex_obj
        if alpha is None:
            step_obj = economic_step_obj
        else:
            step_obj = alpha * inv_obj + (1 - alpha) * opex_obj
        obj_rows.append({
            'Investment_Period': int(i) + 1,
            'TEP_Objective': inv_obj,
            'OPEX_Objective': opex_obj,
            'STEP_Objective': step_obj,
            'NPV_STEP_Objective': step_obj * present_value_tep,
            'STEP_Objective_Economic': economic_step_obj,
            'NPV_STEP_Objective_Economic': economic_step_obj * present_value_tep,
        })

    if save_period_svgs:
        save_MP_TEP_period_svgs(
            grid,
            name_prefix=period_svg_prefix,
            journal=True,
            legend=True,
            Price_Zones=Price_Zones,
            line_size_factor=period_svg_line_size_factor,
        )
    
    _set_grid_to_multiperiod_state(grid, last_period, Price_Zones)
    ExportACDC_TEP_MS_toPyflowACDC(
        model.inv_model[last_period], grid, n_clusters, clustering, Price_Zones, mutate_grid=True
    )

    grid.MP_MS_TEP_obj_res = pd.DataFrame(obj_rows)
    grid.MP_MS_TEP_results = {
        'clustering': clustering,
        'n_clusters': n_clusters,
        'period_results': mp_ms_period_results,
        'period_scenario_grid_res': period_scenario_grid_res,
         'investment_summary': grid.MP_TEP_results,
        'objective_summary': grid.MP_MS_TEP_obj_res,
    }

    t4 = time.time()
    timing_info = {
        "create": t2 - t1,
        "solve": solver_stats['time'],
        "export": t4 - t3,
    }
    return model, model_results, timing_info, solver_stats, grid.MP_MS_TEP_results


def save_MP_TEP_period_svgs(
    grid,
    name_prefix='grid_MP_TEP',
    journal=True,
    legend=True,
    square_ratio=False,
    poly=None,
    linestrings=None,
    Price_Zones=False,
    line_size_factor=1.0,
):
    
    periods = grid.TEP_n_periods
   
    for i in range(periods):
            # From DataFrame by names
        _set_grid_to_multiperiod_state(grid, i, Price_Zones) 
        create_geometries(grid)

        save_network_svg(
            grid,
            name=f"{name_prefix}_P{i}",
            journal=journal,
            legend=legend,
            square_ratio=square_ratio,
            poly=poly,
            linestrings=linestrings,
            line_size_factor=line_size_factor,
        )

    return


def run_opf_for_investment_period(
    grid,
    investment_period,
    ObjRule=None,
    solver='ipopt',
    tee=False,
    limit_flow_rate=True,
    obj_scaling=1.0,
    export_excel=True,
    export_location='MP_investment_periods',
    file_name=None,
    print_table=False,
    decimals=3,
    plot_folium={},
    save_grid_pkl: bool = False,
):
    """
    Apply a dynamic investment state, run OPF, and optionally export Results.All to Excel.

    This uses the same period-state loader as MP-TEP result post-processing:
    `_set_grid_to_multiperiod_state(grid, investment_period)`.
    """
    period_idx = int(investment_period)
    export_location = export_location or 'MP_investment_periods'
    n_periods = int(getattr(grid, 'TEP_n_periods', 0) or 0)
    if n_periods > 0 and (period_idx < 0 or period_idx >= n_periods):
        raise ValueError(
            f"investment_period={period_idx} out of range [0, {n_periods - 1}]"
        )

    
    _, PZ = obj_w_rule(grid,ObjRule,True)
    _set_grid_to_multiperiod_state(grid, period_idx,PZ)
    model, model_res, timing_info, solver_stats = Optimal_PF(
        grid,
        ObjRule=ObjRule,
        solver=solver,
        tee=tee,
        limit_flow_rate=limit_flow_rate,
        obj_scaling=obj_scaling,
    )
    os.makedirs(export_location, exist_ok=True)
    res = Results(grid, decimals=decimals)
    if export_excel:
        all_kwargs = {
            'export_type': 'excel',
            'print_table': print_table,
            'file_name': file_name or f"{getattr(grid, 'name', 'grid')}_period_{period_idx}",
            'export_location': export_location,
        }
        res.pyomo_model_results(model, solver_stats=solver_stats, model_results=model_res, print_table=False)
        res.All(**all_kwargs)

    if save_grid_pkl:
        from .Export_files import save_pickle

        base_name = file_name or f"{getattr(grid, 'name', 'grid')}_period_{period_idx}"
        # Match Excel naming convention in Results.All():
        #   excel_path = f"{base_name}_results.xlsx"
        pkl_path = os.path.join(export_location, f"{base_name}_results.pkl")
        save_pickle(grid, pkl_path, compress=True)

    if plot_folium:
        try:
            from .Mapping import plot_folium_network as plot_folium_fn
            default_map_name = f"{grid.name}_period_{period_idx}"
            default_map_name = os.path.join(export_location, default_map_name)

            folium_kwargs = {
                'planar': False,
                'scale_gen': False,
                'plot_load': True,
                'name': default_map_name,
            }
            if isinstance(plot_folium, dict):
                folium_kwargs.update(plot_folium)

            map_name = str(folium_kwargs.get('name', default_map_name))
            export_norm = os.path.normpath(export_location)
            map_norm = os.path.normpath(map_name)
            # If relative and not already rooted under export_location, place it there.
            already_under_export = (
                map_norm == export_norm or
                map_norm.startswith(export_norm + os.sep)
            )
            if not os.path.isabs(map_name) and not already_under_export:
                map_name = os.path.join(export_location, map_name)
            folium_kwargs['name'] = map_name

            # Ensure output directory exists for custom map name paths.
            map_parent = os.path.dirname(str(folium_kwargs.get('name', "")))
            if map_parent:
                os.makedirs(map_parent, exist_ok=True)

            plot_folium_fn(grid, **folium_kwargs)
        except Exception as exc:
            print(f"Warning: folium plotting skipped ({exc})")
    return model, model_res, timing_info, solver_stats, res


def _set_grid_inv_factors_unity(grid):
    """Reset load / price-zone investment scaling to neutral (no MP growth on demand)."""
    for price_zone in grid.Price_Zones:
        price_zone.PLi_inv_factor = 1.0
        price_zone.curvature_factor = 1.0
        price_zone.import_expand = 0.0
    for node in grid.nodes_AC:
        if getattr(node, 'PLi_linked', False):
            continue
        node.PLi_inv_factor = 1.0
    for node in grid.nodes_DC:
        if getattr(node, 'PLi_linked', False):
            continue
        node.PLi_inv_factor = 1.0


def _set_grid_to_nominal_base(grid):
    """
    Set expandable assets to nominal multiplicities (``np_line_b``, ``np_conv_b``,
    ``np_gen_b``, ``np_rsgen_b``). Investment scaling on loads / price zones is
    reset to unity (``_set_grid_inv_factors_unity``).

    ``current_generation_type_limits`` is set to 1.0 for every ``generation_types``
    entry. Those limits feed TEP / reporting (e.g. ``GEN_balance_constraints``),
    not the standard TS-OPF model; keeping them neutral avoids pulling an
    arbitrary MP-period slice for a run that is meant to be a nominal hardware base.
    """
    for line in grid.lines_AC_exp:
        line.np_line = float(getattr(line, 'np_line_b', line.np_line))
    for line in grid.lines_DC:
        line.np_line = float(getattr(line, 'np_line_b', line.np_line))
    for conv in grid.Converters_ACDC:
        conv.np_conv = float(getattr(conv, 'np_conv_b', conv.np_conv))
    for rs in grid.RenSources:
        rs.np_rsgen = int(getattr(rs, 'np_rsgen_b', rs.np_rsgen))
    for gen in grid.Generators:
        gen.np_gen = int(getattr(gen, 'np_gen_b', gen.np_gen))
    _set_grid_inv_factors_unity(grid)
    for gen_type in grid.generation_types:
        grid.current_generation_type_limits[gen_type] = 1.0


def run_ts_opf_for_investment_period(
    grid,
    investment_period,
    start=1,
    end=99999,
    ObjRule=None,
    price_zone_restrictions=False,
    print_step=False,
    limit_flow_rate=True,
    use_clusters=True,
    solver='ipopt',
    obj_scaling=1.0,
    warm_start_mode='roll',
    export_to_grid=True,
    export_excel=True,
    export_location='MP_investment_periods_TS',
    file_name=None,
    plot_ts=False,
    save_grid_pkl: bool = False,
    nominal_base=False,
):
    """
    Apply a dynamic investment state for a given MP period and run TS-OPF over [start, end].

    This mirrors `run_opf_for_investment_period`, but calls `TS_ACDC_OPF`
    to perform a time-series OPF for that investment period.

    If ``nominal_base=True``, ignore ``investment_period`` and apply
    ``_set_grid_to_nominal_base`` (nominal ``np``, unity inv factors, neutral
    ``current_generation_type_limits``).
    """
    if nominal_base:
        period_tag = 'base'
        if print_step:
            print("[run_ts_opf_for_investment_period] applying state: nominal_base")
        _set_grid_to_nominal_base(grid)
    else:
        period_idx = int(investment_period)
        n_periods = int(getattr(grid, 'TEP_n_periods', 0) or 0)
        if n_periods > 0 and (period_idx < 0 or period_idx >= n_periods):
            raise ValueError(
                f"investment_period={period_idx} out of range [0, {n_periods - 1}]"
            )
        period_tag = period_idx
        if print_step:
            print(f"[run_ts_opf_for_investment_period] applying state: investment_period={period_idx}")
        _, PZ = obj_w_rule(grid, ObjRule, True)
        _set_grid_to_multiperiod_state(grid, period_idx, PZ)

    times = TS_ACDC_OPF(
        grid,
        start=start,
        end=end,
        ObjRule=ObjRule,
        price_zone_restrictions=price_zone_restrictions,
        expand=False,
        print_step=print_step,
        limit_flow_rate=limit_flow_rate,
        use_clusters=use_clusters,
        solver=solver,
        obj_scaling=obj_scaling,
        warm_start_mode=warm_start_mode,
        export_to_grid=export_to_grid,
    )

    # Export TS results to Excel, following the same naming conventions used elsewhere.
    export_location = export_location or 'MP_investment_periods_TS'
    os.makedirs(export_location, exist_ok=True)
    if nominal_base:
        base_name = file_name or f"{getattr(grid, 'name', 'grid')}_TS_base"
    else:
        base_name = file_name or f"{getattr(grid, 'name', 'grid')}_TS_period_{period_tag}"
    excel_path = os.path.join(export_location, base_name)

    if export_excel:
        results_TS_OPF(grid, excel_file_path=excel_path, times=times)

    if save_grid_pkl:
        from .Export_files import save_pickle

        pkl_path = os.path.join(export_location, f"{base_name}_results.pkl")
        save_pickle(grid, pkl_path, compress=True)

    if plot_ts:
        try:
            from .Graph_and_plot import plot_TS_res

            ts_svg_dir = os.path.join(export_location, f"ts_svg_period_{period_tag}")
            os.makedirs(ts_svg_dir, exist_ok=True)
            plot_TS_res(
                grid,
                start=start,
                end=end,
                show=False,
                path=ts_svg_dir,
                save_format='svg',
                skip_failed=True,
            )
        except Exception as exc:
            print(f"Warning: TS plotting skipped ({exc})")

    return times


def run_opf_for_all_investment_periods(
    grid,
    ObjRule=None,
    solver='ipopt',
    tee=False,
    limit_flow_rate=True,
    obj_scaling=1.0,
    export_excel=True,
    export_location=None,
    file_name_prefix=None,
    print_table=False,
    decimals=3,
    plot:bool =False,
    save_grid_pkl: bool = False,
    MS: bool = False,
    ts_start: int = 1,
    ts_end: int = 99999,
    ts_use_clusters: bool = True,
    ts_include_base_case: bool = True,
):
    """
    Run OPF for every dynamic investment period and export one Excel per period.

    Default file naming:
    - `<grid.name>_res_invperiod_0_results.xlsx`
    - `<grid.name>_res_invperiod_1_results.xlsx`
    - ...

    When ``MS=True``, each integer key ``i`` also has ``ts_results`` (snapshot of
    ``grid.time_series_results`` and ``S_base``), and ``period_results['ts_inv']``
    maps period index to that snapshot for ``create_mp_ts_dash`` / ``run_mp_ts_dash``.

    If ``ts_include_base_case`` is True (default), run a **nominal-base** TS first
    (see ``_set_grid_to_nominal_base``). Results go under ``period_results['base']``
    and ``ts_inv['base']`` for Dash comparison.
    """
    n_periods = grid.TEP_n_periods


    prefix = file_name_prefix or f"{grid.name}_res_invperiod"
    period_results = {}
    ts_export_location = export_location or 'MP_investment_periods_TS'

    if MS and ts_include_base_case:
        ts_prefix = f"{prefix}_TS"
        if tee:
            print(
                f"[run_opf_for_all_investment_periods] TS-OPF base case "
                f"(use_clusters={ts_use_clusters}, start={ts_start}, end={ts_end})"
            )
        times = run_ts_opf_for_investment_period(
            grid,
            investment_period=0,
            start=ts_start,
            end=ts_end,
            ObjRule=ObjRule,
            print_step=tee,
            use_clusters=ts_use_clusters,
            solver=solver,
            obj_scaling=obj_scaling,
            export_excel=export_excel,
            export_location=ts_export_location,
            file_name=f"{ts_prefix}_base",
            plot_ts=bool(plot),
            save_grid_pkl=save_grid_pkl,
            nominal_base=True,
        )
        ts_snap = _snapshot_ts_results(grid)
        ts_snap['times'] = times
        period_results['base'] = {
            'times': times,
            'export_location': ts_export_location,
            'ts_results': ts_snap,
        }

    for i in range(n_periods):
        if not MS:
            # Standard snapshot OPF for each investment period.
            run_out = run_opf_for_investment_period(
                grid,
                investment_period=i,
                ObjRule=ObjRule,
                solver=solver,
                tee=tee,
                limit_flow_rate=limit_flow_rate,
                obj_scaling=obj_scaling,
                export_excel=export_excel,
                export_location=export_location,
                file_name=f"{prefix}_{i}",
                print_table=print_table,
                decimals=decimals,
                plot_folium=plot,
                save_grid_pkl=save_grid_pkl,
            )
            period_results[i] = {
                'model': run_out[0],
                'model_res': run_out[1],
                'timing_info': run_out[2],
                'solver_stats': run_out[3],
                'results_obj': run_out[4],
            }
        else:
            # MS=True: run a TS-OPF for each investment period instead of a single snapshot OPF.
            # PyFlow-ACDC takes this as a time-series post-analysis on the MP solution.
            ts_prefix = f"{prefix}_TS"
            if tee:
                print(
                    f"[run_opf_for_all_investment_periods] TS-OPF investment_period={i} "
                    f"(use_clusters={ts_use_clusters}, start={ts_start}, end={ts_end})"
                )
            times = run_ts_opf_for_investment_period(
                grid,
                investment_period=i,
                start=ts_start,
                end=ts_end,
                ObjRule=ObjRule,
                print_step=tee,
                use_clusters=ts_use_clusters,
                solver=solver,
                obj_scaling=obj_scaling,
                export_excel=export_excel,
                export_location=ts_export_location,
                file_name=f"{ts_prefix}_{i}",
                plot_ts=bool(plot),
                save_grid_pkl=save_grid_pkl,
            )
            ts_snap = _snapshot_ts_results(grid)
            ts_snap['times'] = times
            period_results[i] = {
                'times': times,
                'export_location': ts_export_location,
                'ts_results': ts_snap,
            }

    if MS and period_results:
        ts_inv = {}
        if 'base' in period_results and 'ts_results' in period_results['base']:
            ts_inv['base'] = period_results['base']['ts_results']
        for k, v in period_results.items():
            if isinstance(k, int) and 'ts_results' in v:
                ts_inv[k] = v['ts_results']
        period_results['ts_inv'] = ts_inv
        grid.ts_inv = ts_inv

    return period_results


def _set_grid_to_multiperiod_state(grid, investment_period,Price_Zones=False):
    def _np_dynamic_at(inv_dict, period, fallback):
        """Return np_dynamic[period] if in range; otherwise fallback."""
        series = inv_dict["np_dynamic"]
        if period < len(series):
            return series[period]
        return fallback

    for line in grid.lines_AC_exp:
        line.np_line = _np_dynamic_at(line.investment_decisions, investment_period, line.np_line)
    for line in grid.lines_DC:
        line.np_line = _np_dynamic_at(line.investment_decisions, investment_period, line.np_line)
    for conv in grid.Converters_ACDC:
        conv.np_conv = _np_dynamic_at(conv.investment_decisions, investment_period, conv.np_conv)
    for rs in grid.RenSources:
        rs.np_rsgen = _np_dynamic_at(rs.investment_decisions, investment_period, rs.np_rsgen)
    for gen in grid.Generators:
        gen.np_gen = _np_dynamic_at(gen.investment_decisions, investment_period, gen.np_gen)
    _update_grid_investment_period(grid, investment_period)
    # Keep active single-period limits aligned with selected period.
    series_map = grid.generation_type_limits
    for gen_type, series in series_map.items():
        if isinstance(series, (list, tuple, np.ndarray)):
            if investment_period < len(series):
                grid.current_generation_type_limits[gen_type] = float(series[investment_period])
        else:
            grid.current_generation_type_limits[gen_type] = float(series)
def _calculate_decomision_period(element,n_years):

    element.decomision_period = math.ceil(element.life_time/n_years)

def calculate_MPTEP_objective_from_model(model,grid,weights_def,n_years,discount_rate,multi_scenario=False):
    inv_objs = {}
    inv_opf_objs = {}
    for i in model.inv_periods:    
        opf_objs = []
        if multi_scenario:
            period_block = model.inv_model[i]
            if not hasattr(period_block, 'scenario_frames') or not hasattr(period_block, 'scenario_model'):
                raise ValueError(f"Investment period {i} has no scenario blocks for multi-scenario objective extraction.")
            for t in period_block.scenario_frames:
                opf_obj = calculate_objective_from_model(period_block.scenario_model[t],grid,weights_def,True)
                opf_objs.append(opf_obj)
        else:
            opf_objs = [calculate_objective_from_model(model.inv_model[i],grid,weights_def,True)]

        tep_obj = _inv_model_obj(model,grid,i)  
        tep_obj_value = pyo.value(tep_obj)
        inv_objs[i] = tep_obj_value
        inv_opf_objs[i] = opf_objs
    return inv_objs, inv_opf_objs

def _deactivate_non_pre_existing_loads(grid):
    for price_zone in grid.Price_Zones:
        inv0_load = price_zone.investment_decisions["Load"][0]
        if inv0_load == 0.0:
            price_zone.PLi_inv_factor = 0.0
    for node in grid.nodes_AC:
        if node.PLi_linked:
            continue
        inv0_load = node.investment_decisions["Load"][0]
        if inv0_load == 0.0:
            node.PLi_inv_factor = 0.0
    for node in grid.nodes_DC:
        if node.PLi_linked:
            continue
        inv0_load = node.investment_decisions["Load"][0]
        if inv0_load == 0.0:
            node.PLi_inv_factor = 0.0