import numpy as np
import pyomo.environ as pyo
import pandas as pd
import time
import math
from concurrent.futures import ThreadPoolExecutor
import os

from .ACDC_OPF_NL_model import OPF_create_NLModel_ACDC,TEP_variables,ExportACDC_NLmodel_toPyflowACDC
from .ACDC_OPF import pyomo_model_solve,OPF_obj,obj_w_rule,calculate_objective,calculate_objective_from_model,Optimal_PF
from .ACDC_Static_TEP import get_TEP_variables,_initialize_MS_STEP_sets_model,create_scenarios
from .Class_editor import analyse_grid, current_fuel_type_distribution
from .Time_series import _modify_parameters
from .Graph_and_plot import save_network_svg, create_geometries
from .Results_class import Results



__all__ = [
    'multi_period_transmission_expansion',
    'multi_period_MS_TEP',
    'save_MP_TEP_period_svgs',
    'export_and_save_inv_period_svgs',
    'run_opf_for_investment_period',
    'run_opf_for_all_investment_periods',
]

def pack_variables(*args):
    return args

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
            if element.NUmConvP_opf:
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

    # Normalize object-owned investment decisions.
    for element in _iter_elements():
        for key, values in list(element.investment_decisions.items()):
            element.investment_decisions[key] = _normalize(
                values,
                f"{element.name}:{key}"
            )
    return target_len

def _update_grid_investment_period(grid, i,PZ=False):
    idx = i
    if PZ:
        for price_zone in grid.Price_Zones:
            inv = price_zone.investment_decisions
            price_zone.PLi_inv_factor = inv['Load'][idx]
            price_zone.elasticity = inv['elasticity'][idx]
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
            return model.inv_model[i].NumConvP[c] == model.ConvMP[c, i]
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
                return model.ConvMP[c,i] == model.installed_Conv[c,i] + model.NumConvP_base[c]
            else:
                return model.ConvMP[c,i] == model.installed_Conv[c,i] + model.ConvMP[c,i-1] - model.decomision_Conv[c,i]
        model.MP_Conv_installed_constraint = pyo.Constraint(model.conv, model.inv_periods, rule=MP_Conv_installed)

def _MP_GEN_balance_constraints(model, grid):
    # Same logic as static GEN balance, indexed by investment period.
    if all(v == 1 for v in grid.generation_type_limits.values()):
        return

    gen_type_limits = {k.lower(): v for k, v in grid.generation_type_limits.items()}
    model.gen_types = pyo.Set(initialize=list(gen_type_limits.keys()))
    model.gen_type_limits = pyo.Param(model.gen_types, initialize=gen_type_limits)

    def normalize_type(type_name):
        return type_name.lower() if type_name else None

    def gen_type_max_capacity_rule(model, gen_type, i):
        gen_capacity = 0
        for gen in grid.Generators:
            if normalize_type(gen.gen_type) != gen_type:
                continue
            g = gen.genNumber
            if grid.GPR:
                gen_capacity += gen.Max_pow_gen * model.np_gen[g, i]
            else:
                gen_capacity += gen.Max_pow_gen * gen.np_gen

        ren_capacity = 0
        for rs in grid.RenSources:
            if normalize_type(rs.rs_type) != gen_type:
                continue
            r = rs.rsNumber
            if grid.rs_GPR:
                ren_capacity += rs.PGi_ren_base * model.np_rsgen[r, i]
            else:
                ren_capacity += rs.PGi_ren_base * rs.np_rsgen

        return gen_capacity + ren_capacity

    model.gen_type_max_capacity = pyo.Expression(model.gen_types, model.inv_periods, rule=gen_type_max_capacity_rule)

    def total_max_capacity_rule(model, i):
        return sum(model.gen_type_max_capacity[gt, i] for gt in model.gen_types)

    model.total_max_capacity = pyo.Expression(model.inv_periods, rule=total_max_capacity_rule)

    def gen_type_balance_rule(model, gen_type, i):
        return model.gen_type_max_capacity[gen_type, i] <= model.total_max_capacity[i] * model.gen_type_limits[gen_type]

    model.gen_type_balance_constraint = pyo.Constraint(model.gen_types, model.inv_periods, rule=gen_type_balance_rule)


def _MP_TEP_variables(model,grid):
    
    tep_vars = get_TEP_variables(grid)
    np_gen_max_install={}
    for gen in grid.Generators:
        max_inv = _inv_decision(gen, 'max_inv')
        np_gen_max_install[gen.genNumber] = max(max_inv) if len(max_inv) > 0 else gen.np_gen_max
    np_rsgen_max_install={}
    for rs in grid.RenSources:
        max_inv = _inv_decision(rs, 'max_inv')
        np_rsgen_max_install[rs.rsNumber] = max(max_inv) if len(max_inv) > 0 else rs.np_rsgen_max

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

    if grid.rs_GPR:
        np_rsgen = tep_vars['ren_sources']['np_rsgen']
        np_rsgen_max = tep_vars['ren_sources']['np_rsgen_max']

        model.np_rsgen_base = pyo.Param(model.ren_sources,initialize=np_rsgen)
        
        def np_rsgen_bounds(model,rs,i):
            return (0,np_rsgen_max[rs])
        def np_rsgen_bounds_install(model,rs,i):
            return (0,np_rsgen_max_install[rs])
        def np_rsgen_bounds_install_opt(model,rs,i):
            ren_source = grid.RenSources[rs]
            if ren_source.np_rsgen_opf:
                return (-model.planned_installation_rsgen[rs, i], np_rsgen_max_install[rs])
            else:
                return (0,0)  
        def np_rsgen_i(model, rs, i):
            return np_rsgen[rs]
        model.np_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.NonNegativeIntegers,bounds=np_rsgen_bounds,initialize=np_rsgen_i)
        model.installed_rsgen = pyo.Var(model.ren_sources,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0,bounds=np_rsgen_bounds_install)
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
            return (0,np_gen_max_install[g])
        def np_gen_bounds_install_opt(model,g,i):
            gen = grid.Generators[g]
            if gen.np_gen_opf:
                return (-model.planned_installation_gen[g, i], np_gen_max_install[g])
            else:
                return (0,0)
        def np_gen_i(model, g, i):
            return np_gen[g]
        model.np_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.NonNegativeIntegers,bounds=np_gen_bounds,initialize=np_gen_i)
        model.installed_gen = pyo.Var(model.gen_AC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0,bounds=np_gen_bounds_install)
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
                return (0,NP_lineAC_max[l])
            def MP_AC_line_bounds_install_opt(model,l,i):
                line = grid.lines_AC_exp[l]
                if line.np_line_opf:
                    return (-model.planned_installation_ACline[l, i], NP_lineAC_max[l])
                else:
                    return (0,0)
            def NP_lineAC_i(model, l, i):
                return NP_lineAC[l]
            model.ACLinesMP = pyo.Var(model.lines_AC_exp,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_AC_line_bounds,initialize=NP_lineAC_i)
            model.installed_ACline = pyo.Var(model.lines_AC_exp,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0,bounds=MP_AC_line_bounds_install)
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
            return (0,NP_lineDC_max[l])
        def MP_DC_line_bounds_install_opt(model,l,i):
            line = grid.lines_DC[l]
            if line.np_line_opf:
                return (-model.planned_installation_DCline[l, i], NP_lineDC_max[l])
            else:
                return (0,0)
        def NP_lineDC_i(model, l, i):
            return NP_lineDC[l]
        model.DCLinesMP = pyo.Var(model.lines_DC,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_DC_line_bounds,initialize=NP_lineDC_i)
        model.installed_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0,bounds=MP_DC_line_bounds_install)
        model.planned_installation_DCline = pyo.Param(model.lines_DC,model.inv_periods,initialize=planned_installation_DCline_init)
        model.opt_installation_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.Integers,initialize=0,bounds=MP_DC_line_bounds_install_opt)
        model.decomision_DCline = pyo.Var(model.lines_DC,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)

    if grid.ACmode and grid.DCmode:
        NumConvP = tep_vars['converters']['NumConvP']
        NumConvP_max = tep_vars['converters']['NumConvP_max']
        model.NumConvP_base  =pyo.Param(model.conv,initialize=NumConvP)
        def MP_Conv_bounds(model,c,i):
            return (0,NumConvP_max[c])
        def MP_Conv_bounds_install(model,c,i):
            return (0,NumConvP_max[c])
        def MP_Conv_bounds_install_opt(model,c,i):
            conv = grid.Converters_ACDC[c]
            if conv.NUmConvP_opf:
                return (-model.planned_installation_Conv[c, i], NumConvP_max[c])
            else:
                return (0,0)
        def NumConvP_i(model, c, i):
            return NumConvP[c]
        model.ConvMP = pyo.Var(model.conv,model.inv_periods, within=pyo.NonNegativeIntegers,bounds=MP_Conv_bounds,initialize=NumConvP_i)
        model.installed_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0,bounds=MP_Conv_bounds_install)
        model.planned_installation_Conv = pyo.Param(model.conv,model.inv_periods,initialize=planned_installation_Conv_init)
        model.opt_installation_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.Integers,initialize=0,bounds=MP_Conv_bounds_install_opt)
        model.decomision_Conv = pyo.Var(model.conv,model.inv_periods,within=pyo.NonNegativeIntegers,initialize=0)
        
def multi_period_transmission_expansion(
    grid,
    inv_periods=[],
    n_years=10,
    Hy=8760,
    discount_rate=0.02,
    ObjRule=None,
    solver='bonmin',
    time_limit=99999,
    tee=False,
    callback=False,
    solver_options=None,
    obj_scaling=1.0,
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

    grid.GPR = True if any(any(x != 0 for x in _inv_decision(gen, 'planned_installation')) for gen in grid.Generators) else grid.GPR
    grid.rs_GPR = True if any(any(x != 0 for x in _inv_decision(ren_source, 'planned_installation')) for ren_source in grid.RenSources) else grid.rs_GPR
    
    for gen in grid.Generators:
        gen.np_gen_mp = gen.np_gen_opf or any(x != 0 for x in _inv_decision(gen, 'planned_installation'))
    for rs in grid.RenSources:
        rs.np_rsgen_mp = rs.np_rsgen_opf or any(x != 0 for x in _inv_decision(rs, 'planned_installation'))
    
    t1=time.time()

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

        _update_grid_investment_period(grid, i,PZ)

        _modify_parameters(grid,model.inv_model[i],PZ)

        
        obj_OPF = OPF_obj(model.inv_model[i],grid,weights_def,True)
    
        obj_OPF *=present_value_opf
        
        model.inv_model[i].obj = pyo.Objective(rule=obj_OPF, sense=pyo.minimize)

    _initialize_DTEP_sets_model(model,grid)
    _MP_TEP_variables(model,grid)
    _MP_TEP_constraints(model,grid)
    _MP_GEN_balance_constraints(model,grid)
    _MP_TEP_capex_budget_constraint(model,grid,capex_budget=capex_budget)
    

    net_cost = _MP_TEP_obj(model,grid,n_years,discount_rate)
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
    
    MINLP = False
    if solver != 'ipopt':
        MINLP = True
    
    export_MP_TEP_results_toPyflowACDC(model,grid,Price_Zones=PZ,MINLP=MINLP)
    _save_inv_models(model,grid)
    t4 = time.time()

    inv_objs, inv_opf_objs = calculate_DTEP_objective_from_model(model,grid,weights_def,n_years,discount_rate,multi_scenario=False)
    
    # Build list of rows then create DataFrame once to avoid concat-on-empty FutureWarning
    obj_rows = []
    for i in model.inv_periods:
        present_value_tep = 1/(1+discount_rate)**(i*n_years)
        
        opf_obj = inv_opf_objs[i][0]  # Get first element from the list
        npv_opf_obj = opf_obj*present_value_opf
        inv_obj = inv_objs[i]
        step_obj = inv_obj + npv_opf_obj
        npv_step_obj = step_obj*present_value_tep
        obj_rows.append({
            'Investment_Period': i+1,
            'OPF_Objective': opf_obj,
            'NPV_OPF_Objective': npv_opf_obj,
            'TEP_Objective': inv_obj,
            'STEP_Objective': step_obj,
            'NPV_STEP_Objective': npv_step_obj
        })
    obj_res = pd.DataFrame(obj_rows, columns=['Investment_Period', 'OPF_Objective',
                                              'NPV_OPF_Objective','TEP_Objective',
                                              'STEP_Objective','NPV_STEP_Objective'])
    grid.MP_TEP_obj_res = obj_res
    timing_info = {
    "create": t2-t1,
    "solve": solver_stats['time'],
    "export": t4-t3,
    }

    
    
    return model, model_results ,timing_info, solver_stats
    
def _initialize_DTEP_sets_model(model,grid):    

    if grid.DCmode:
        model.lines_DC = pyo.Set(initialize=list(range(0, grid.nl_DC)))
    if grid.ACmode and grid.DCmode:
        model.conv = pyo.Set(initialize=list(range(0, grid.nconv)))
    if grid.TEP_AC:
        model.lines_AC_exp = pyo.Set(initialize=list(range(0,grid.nle_AC)))
    if grid.GPR:
        model.gen_AC = pyo.Set(initialize=list(range(0,grid.n_gen)))
    if grid.rs_GPR:
        model.ren_sources = pyo.Set(initialize=list(range(0,grid.n_ren)))

def _inv_model_obj(model,grid,i):
    inv_gen= 0
    AC_Inv_lines=0
    DC_Inv_lines=0
    Conv_Inv=0
    inv_rs=0
    if grid.rs_GPR:
        for rs in model.ren_sources:
            ren_source = grid.RenSources[rs]
            inv_rs+=model.installed_rsgen[rs,i]*ren_source.base_cost
    else:
        inv_rs=0

    if grid.GPR:
        
        for g in model.gen_AC:
            gen = grid.Generators[g]
            inv_gen+=model.installed_gen[g,i]*gen.base_cost
    else:
        inv_gen=0


    if grid.ACmode:
        if grid.TEP_AC:
            for l in model.lines_AC_exp:
                line = grid.lines_AC_exp[l]
                AC_Inv_lines+=model.installed_ACline[l,i]*line.base_cost
            
    if grid.DCmode:
        for l in model.lines_DC:
            line = grid.lines_DC[l]
            DC_Inv_lines+=model.installed_DCline[l,i]*line.base_cost
        
    if grid.ACmode and grid.DCmode:
        for c in model.conv:
            conv = grid.Converters_ACDC[c]
            Conv_Inv+=model.installed_Conv[c,i]*conv.base_cost
        

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

def _MP_TEP_obj(model,grid,n_years,discount_rate):
    
    net_cost = 0

    for i in model.inv_periods:
        inv_cost = _inv_model_obj(model,grid,i)
        instance_cost = model.inv_model[i].obj.expr + inv_cost
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

def export_MP_TEP_results_toPyflowACDC(model,grid,Price_Zones=False,MINLP=False):
    

    grid.MP_TEP_run=True
    
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
                if i == 0:
                    cost = (n_val - pyo.value(model.np_gen_base[g])) * gen.base_cost
                else:
                    cost = (n_val - gen_mp_values[g, i-1]) * gen.base_cost
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
                if i == 0:
                    cost = (n_val - pyo.value(model.np_rsgen_base[rs])) * ren_source.base_cost
                else:
                    cost = (n_val - rs_mp_values[rs, i-1]) * ren_source.base_cost
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
                    if i == 0:
                        cost = (n_val - pyo.value(model.NumLinesACP_base[l])) * line.base_cost
                    else:
                        cost = (n_val - ac_lines_mp_values[l, i-1]) * line.base_cost
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
                    if i == 0:
                        cost = (n_val - pyo.value(model.NumLinesDCP_base[l])) * line.base_cost
                    else:
                        cost = (n_val - dc_lines_mp_values[l, i-1]) * line.base_cost
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
            row['Pre Existing'] = pyo.value(model.NumConvP_base[c])
            total_cost = 0
            for i in range(n_periods):
                n_val = acdc_conv_mp_values[c, i]   
                if i == 0:
                    cost = (n_val - pyo.value(model.NumConvP_base[c])) * conv.base_cost
                else:
                    cost = (n_val - acdc_conv_mp_values[c, i-1]) * conv.base_cost
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
    fuel_type_dist_by_period = {}
    for i in model.inv_periods:
        _set_grid_to_dynamic_state(grid, i)
        fuel_type_dist_by_period[int(i) + 1] = current_fuel_type_distribution(grid, output='df')

    grid.MP_TEP_fuel_type_distribution = fuel_type_dist_by_period

    last_i = max(model.inv_periods)
    _set_grid_to_dynamic_state(grid, last_i)
     
    ExportACDC_NLmodel_toPyflowACDC(model.inv_model[last_i],grid,Price_Zones,TEP=True)

    grid.MP_TEP_results = df  

def multi_period_MS_TEP(grid, NPV=True, n_years=10, Hy=8760, 
                       discount_rate=0.02, clustering_options=None, ObjRule=None, 
                       solver='bonmin', obj_scaling=1.0):
    """
    Multi-period Transmission Expansion Planning with time series clustering.
    Hierarchical model structure:
    - Level 1: Investment periods
    - Level 2: Time frames/scenarios for each investment period
    """
    # 1. Initial analysis and setup
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid, ObjRule, True)

    # 2. Set grid parameters
    grid.TEP_n_years = n_years
    grid.TEP_discount_rate = discount_rate
    n_periods = _fill_investment_decisions(grid)

    # 3. Handle time series clustering
    try:
        from .Time_series_clustering import cluster_analysis
        n_clusters,clustering = cluster_analysis(grid,clustering_options)
    except:
        n_clusters = len(grid.Time_series[0].data)
        clustering = False

    # 4. Create model sets
    t1 = time.time()
    model = pyo.ConcreteModel()
    model.name = "MP TEP MS MTDC AC/DC hybrid OPF"
    
    # Investment periods
    model.inv_periods = pyo.Set(initialize=list(range(0, n_periods)))
    
    # Create hierarchical model structure
    model.inv_model = pyo.Block(model.inv_periods)  # Level 1: Investment periods
    for i in model.inv_periods:
        # Time frames for each investment period
        model.inv_model[i].scenario_frames = pyo.Set(initialize=range(1, n_clusters + 1))
        model.inv_model[i].scenario_model = pyo.Block(model.inv_model[i].scenario_frames)  # Level 2: Time frames

    # 5. Create base model and clone for each period/time frame
    base_model = pyo.ConcreteModel()
    OPF_create_NLModel_ACDC(base_model, grid, PV_set=False, Price_Zones=Price_Zones, TEP=True)

    create_scenarios(model.inv_model[i],grid,Price_Zones,weights_def,n_clusters,clustering,NPV,n_years,discount_rate,Hy)

    _initialize_MS_STEP_sets_model(model,grid)
    _MP_TEP_variables(model,grid)
    _MP_GEN_balance_constraints(model,grid)

    
    net_cost = _MP_TEP_obj(model,grid,n_years,discount_rate)
    if obj_scaling != 1.0:
        net_cost = net_cost / obj_scaling
    model.obj = pyo.Objective(rule=net_cost, sense=pyo.minimize)
    model.obj_scaling = obj_scaling


    # 10. Solve the model
    t2 = time.time()
    model_results, solver_stats = pyomo_model_solve(model, grid, solver)
    t3 = time.time()

    # 11. Export results
    MINLP = False
    if solver != 'ipopt':
        MINLP = True
    TEP_TS_res = export_MP_TEP_results_toPyflowACDC(model, grid,Price_Zones,MINLP)
    t4 = time.time()

    timing_info = {
        "create": t2-t1,
        "solve": solver_stats['time'],
        "export": t4-t3,
    }

    return model, model_results, timing_info, solver_stats, TEP_TS_res  


def save_MP_TEP_period_svgs(grid, name_prefix='grid_MP_TEP', journal=True, legend=True, square_ratio=False, poly=None, linestrings=None):
    
    periods = grid.TEP_n_periods
   
    for i in range(periods):
            # From DataFrame by names
        _set_grid_to_dynamic_state(grid, i) 

        try:
            create_geometries(grid)
        except Exception:
            pass

        save_network_svg(
            grid,
            name=f"{name_prefix}_P{i}",
            journal=journal,
            legend=legend,
            square_ratio=square_ratio,
            poly=poly,
            linestrings=linestrings
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
    plot_folium={}
):
    """
    Apply a dynamic investment state, run OPF, and optionally export Results.All to Excel.

    This uses the same period-state loader as MP-TEP result post-processing:
    `_set_grid_to_dynamic_state(grid, investment_period)`.
    """
    period_idx = int(investment_period)
    export_location = export_location or 'MP_investment_periods'
    n_periods = int(getattr(grid, 'TEP_n_periods', 0) or 0)
    if n_periods > 0 and (period_idx < 0 or period_idx >= n_periods):
        raise ValueError(
            f"investment_period={period_idx} out of range [0, {n_periods - 1}]"
        )

    _set_grid_to_dynamic_state(grid, period_idx)

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
        res.All(**all_kwargs)

    if plot_folium:
        try:
            from .Mapping import plot_folium as plot_folium_fn
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
    plot_folium=None,
):
    """
    Run OPF for every dynamic investment period and export one Excel per period.

    Default file naming:
    - `<grid.name>_res_invperiod_0_results.xlsx`
    - `<grid.name>_res_invperiod_1_results.xlsx`
    - ...
    """
    n_periods = grid.TEP_n_periods


    prefix = file_name_prefix or f"{grid.name}_res_invperiod"
    period_results = {}

    for i in range(n_periods):
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
            plot_folium=plot_folium
        )
        period_results[i] = {
            'model': run_out[0],
            'model_res': run_out[1],
            'timing_info': run_out[2],
            'solver_stats': run_out[3],
            'results_obj': run_out[4],
        }

    

    return period_results

def _set_grid_to_dynamic_state(grid, investment_period):    
    for line in grid.lines_AC_exp:
        line.np_line = line.investment_decisions['np_dynamic'][investment_period]
    for line in grid.lines_DC:
        line.np_line = line.investment_decisions['np_dynamic'][investment_period]
    for conv in grid.Converters_ACDC:
        conv.NumConvP = conv.investment_decisions['np_dynamic'][investment_period]
    for rs in grid.RenSources:
        rs.np_rsgen = rs.investment_decisions['np_dynamic'][investment_period]
    for gen in grid.Generators:
        gen.np_gen = gen.investment_decisions['np_dynamic'][investment_period]

def _calculate_decomision_period(element,n_years):

    element.decomision_period = math.ceil(element.life_time/n_years)

def calculate_DTEP_objective_from_model(model,grid,weights_def,n_years,discount_rate,multi_scenario=False):
    inv_objs = {}
    inv_opf_objs = {}
    for i in model.inv_periods:    
        opf_objs = []
        if multi_scenario:
            for t in model.scenario_frames:
                opf_obj = calculate_objective_from_model(model.inv_model[i].scenario_model[t],grid,weights_def,True)
                opf_objs.append(opf_obj)
        else:
            opf_objs = [calculate_objective_from_model(model.inv_model[i],grid,weights_def,True)]

        tep_obj = _inv_model_obj(model,grid,i)  
        tep_obj_value = pyo.value(tep_obj)
        inv_objs[i] = tep_obj_value
        inv_opf_objs[i] = opf_objs
    return inv_objs, inv_opf_objs