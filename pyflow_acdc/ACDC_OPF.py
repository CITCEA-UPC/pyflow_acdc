"""
Created on Thu Feb 15 13:24:05 2024

@author: BernardoCastro
"""
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pyomo.environ as pyo
import warnings

from .NL_models.ACDC_OPF_NL_model import opf_create_nl_model_acdc, export_acdc_nl_model_to_pyflow_acdc
from .L_models.AC_OPF_L_model import opf_create_l_model_acdc, export_acdc_l_model_to_pyflow_acdc
from .grid_analysis import analyse_grid
from .constants import NodeType, ConverterDCType, ConverterOpfFxType, ObjComponent, default_obj_weights, AcDcSide
from .pyomo_model_solve import (
    build_only_solver_stats,
    export_solver_progress_to_excel,
    pyomo_model_solve,
    reset_to_initialize,
)

__all__ = [
    'translate_pyf_opf',
    'optimal_l_pf',
    'optimal_pf',
    'pyomo_model_solve',
    'opf_update_param',
    'opf_obj',
    'opf_obj_l',
    'check_linear_opf_weights',
    'opf_line_res',
    'opf_price_price_zone',
    'opf_step_results',
    'opf_step_results_l',
    'fx_conv',
    'export_solver_progress_to_excel',
    'reset_to_initialize',
]

def pack_variables(*args):
    return args


def obj_w_rule(grid,ObjRule):
    weights_def = default_obj_weights()

    # If user provides specific weights, merge them with the default
    if ObjRule is not None:
       for key in ObjRule:
           if key in weights_def:
               weights_def[key]['w'] = ObjRule[key]

    Price_Zones = False
    if  weights_def[ObjComponent.PZ_COST_OF_GENERATION]['w']!=0 :
        Price_Zones=True
    if  weights_def[ObjComponent.CURTAILMENT_RED]['w']!=0 :
        grid.CurtCost=True

    return weights_def, Price_Zones



def optimal_l_pf(grid,ObjRule=None,Price_Zones=False,solver='glpk',tee=False,callback=False,obj_scaling=1.0,build_only=False):
    """Build and solve the linearised AC(/DC) OPF for ``grid``.

    Constructs the linearised Pyomo model (AC Bθ; when ``grid.DCmode``, also
    linearized DC PF and thin LP converters), minimises the weighted objective,
    solves it, and exports the solution back onto ``grid``. Supported objective
    components are generator ``Energy_cost`` and (when electrolysers exist)
    ``H2_sale``. ``SoC_deviation`` is quadratic and raises if weighted.
    Other non-zero weights trigger a warning.

    When ``grid.ESS`` / ``grid.H2``, BESS (P-only) and electrolysers are included.

    Parameters
    ----------
    grid : Grid
        Network to optimise (mutated in place).
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    Price_Zones : bool, optional
        Enable price-zone pricing (resolved from the objective rule).
    solver : str, optional
        Pyomo solver name.
    tee : bool, optional
        Stream raw solver output.
    callback : bool, optional
        Enable the solver-progress callback.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    build_only : bool, optional
        Build the Pyomo model, skip the solver, and export initializer values
        onto ``grid`` so :class:`~pyflow_acdc.Results_class.Results` can run
        without an LP solver.

    Returns
    -------
    tuple
        ``(model, model_res, timing_info, solver_stats)``.

    Examples
    --------
    >>> pyf.optimal_l_pf(
    ...     grid, ObjRule=None, Price_Zones=False, solver='glpk', tee=False)
    """
    grid.reset_run_flags()
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule)

    check_linear_opf_weights(weights_def)

    model = pyo.ConcreteModel()
    model.name="""AC 'DC linear' OPF"""


    t1 = time.perf_counter()

    opf_create_l_model_acdc(model,grid)

    t2 = time.perf_counter()
    t_modelcreate = t2-t1

    """
    """



    obj_rule= opf_obj_l(model,grid,weights_def)

    if obj_scaling != 1.0:
        obj_rule = obj_rule / obj_scaling
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.obj_scaling = obj_scaling


    """
    """
    if grid.DCmode and any(conv.OPF_fx for conv in grid.Converters_ACDC):
        fx_conv(model, grid)

    t3 = time.perf_counter()
    if build_only:
        model_res, solver_stats = build_only_solver_stats(solver, model)
    else:
        model_res,solver_stats = pyomo_model_solve(model,grid,solver,tee,callback=callback)

    t1 = time.perf_counter()
    export_acdc_l_model_to_pyflow_acdc(model, grid)

    for obj in weights_def:
        weights_def[obj]['v']=calculate_objective(grid,obj)

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

def optimal_pf(grid,ObjRule=None,PV_set=False,Price_Zones=False,limit_flow_rate=True,solver='ipopt',tee=False,callback=False,obj_scaling=1.0,build_only=False,export_if_feasible=False):
    """Build and solve the non-linear AC/DC OPF for ``grid``.

    Constructs the full non-linear Pyomo model (AC/DC physics, converters,
    optional price zones), minimises the weighted objective, solves it, and
    exports the solution back onto ``grid``.

    Parameters
    ----------
    grid : Grid
        Network to optimise (mutated in place).
    ObjRule : dict or None, optional
        Objective-component weights; ``None`` uses the grid defaults.
    PV_set : bool, optional
        Fix PV-bus setpoints instead of optimising them.
    Price_Zones : bool, optional
        Enable price-zone pricing (resolved from the objective rule).
    limit_flow_rate : bool, optional
        Enforce line thermal/flow-rate limits.
    solver : str, optional
        Pyomo solver name.
    tee : bool, optional
        Stream raw solver output.
    callback : bool, optional
        Enable the solver-progress callback.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    build_only : bool, optional
        Build the Pyomo model, skip the solver, and export initializer values
        onto ``grid`` so :class:`~pyflow_acdc.Results_class.Results` can run.
    export_if_feasible : bool, optional
        If True, export the solution onto ``grid`` only when a feasible
        solution was found (or ``build_only``). Default False keeps the usual
        always-export behaviour for user-facing OPF calls.

    Returns
    -------
    tuple
        ``(model, model_res, timing_info, solver_stats)``.

    Examples
    --------
    >>> model, model_res, timing_info, solver_stats = pyf.optimal_pf(
    ...     grid, ObjRule=None, PV_set=False, solver='ipopt')
    """
    grid.reset_run_flags()
    analyse_grid(grid)

    weights_def, Price_Zones = obj_w_rule(grid,ObjRule)

    model = pyo.ConcreteModel()
    model.name="AC/DC hybrid OPF"


    t1 = time.perf_counter()

    opf_create_nl_model_acdc(model,grid,PV_set,Price_Zones,limit_flow_rate=limit_flow_rate)

    t2 = time.perf_counter()
    t_modelcreate = t2-t1

    """
    """



    obj_rule= opf_obj(model,grid,weights_def)

    if obj_scaling != 1.0:
        obj_rule = obj_rule / obj_scaling
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.obj_scaling = obj_scaling
    """
    """

    if grid.nn_DC!=0:

        if any(conv.OPF_fx for conv in grid.Converters_ACDC):
                    fx_conv(model, grid)

    if build_only:
        model_res, solver_stats = build_only_solver_stats(solver, model)
    else:
        model_res, solver_stats = pyomo_model_solve(model, grid, solver, tee, callback=callback)

    solution_found = bool(solver_stats and solver_stats.get("solution_found", False))
    do_export = build_only or (not export_if_feasible) or solution_found

    t1 = time.perf_counter()
    if do_export:
        export_acdc_nl_model_to_pyflow_acdc(model, grid, Price_Zones)

        for obj in weights_def:
            weights_def[obj]['v']=calculate_objective(grid,obj)

        grid.OPF_run=True
        grid.OPF_obj=weights_def
    t2 = time.perf_counter()
    t_modelexport = t2-t1


    timing_info = {
        "create": t_modelcreate,
        "solve": solver_stats["time"],
        "export": t_modelexport,
    }
    return model, model_res, timing_info, solver_stats


def fx_conv(model,grid):
    def fx_PDC(model,conv):
        element = grid.Converters_ACDC[conv]
        if element.OPF_fx and element.OPF_fx_type == ConverterOpfFxType.PDC:
            return model.P_conv_DC[element.Node_DC.nodeNumber] == element.P_DC
        return pyo.Constraint.Skip

    def fx_PAC(model,conv):
        element = grid.Converters_ACDC[conv]
        if element.OPF_fx and element.OPF_fx_type in (
                ConverterOpfFxType.PQ, ConverterOpfFxType.PV):
            return model.P_conv_s_AC[conv] == element.P_AC
        return pyo.Constraint.Skip

    def fx_QAC(model,conv):
        element = grid.Converters_ACDC[conv]
        if not hasattr(model, 'Q_conv_s_AC'):
            return pyo.Constraint.Skip
        if element.OPF_fx and element.OPF_fx_type == ConverterOpfFxType.PQ:
            return model.Q_conv_s_AC[conv] == element.Q_AC
        return pyo.Constraint.Skip

    model.Conv_fx_pdc = pyo.Constraint(model.conv, rule=fx_PDC)
    model.Conv_fx_pac = pyo.Constraint(model.conv, rule=fx_PAC)
    model.Conv_fx_qac = pyo.Constraint(model.conv, rule=fx_QAC)



def opf_update_param(model,grid):

    for n in grid.nodes_AC:
        model.P_Gain_known_AC[n.nodeNumber] = n.PGi
        model.P_Load_known_AC[n.nodeNumber] = n.PLi
        model.Q_known_AC[n.nodeNumber] = n.QGi-n.QLi
        model.price[n.nodeNumber] = n.price

    for n in grid.nodes_DC:
        model.P_known_DC[n.nodeNumber] = n.P_DC


    return model

def opf_obj_l(model,grid,ObjRule):
    """Linear OPF objective: Energy_cost and optional H2_sale."""
    total = 0

    if ObjRule[ObjComponent.ENERGY_COST]['w'] != 0:
        if grid.ACmode:
            total += sum(
                (
                    model.PGi_gen[gen.genNumber] * grid.S_base * model.lf[gen.genNumber]
                    + model.np_gen[gen.genNumber] * gen.fc
                )
                for gen in grid.Generators
            )
            if grid.RenSources:
                total += sum(
                    model.np_rsgen[rs] * (
                        model.P_renSource[rs] * model.gamma[rs] * grid.S_base
                        * grid.RenSources[rs].lf
                    )
                    for rs in model.ren_sources
                )
        if grid.DCmode and grid.Generators_DC:
            total += sum(
                (
                    model.PGi_gen_DC[gen.genNumber_DC]
                    * grid.S_base
                    * model.lf_dc[gen.genNumber_DC]
                    + model.np_gen_DC[gen.genNumber_DC] * gen.fc
                )
                for gen in grid.Generators_DC
            )

    if ObjRule[ObjComponent.H2_SALE]['w'] != 0:
        if not grid.H2:
            raise ValueError(
                "H2_sale weight > 0 requires grid.H2 / electrolysers in linear OPF")
        # Minimise -price·Δm  ≡  maximise H₂ sale revenue (EUR for Δm in kg).
        total += sum(
            -float(el.h2_price) * (
                el.b_h * model.P_electrolyser[el.electrolyserNumber]
                * el.S_base * el.dt_hours
                + el.c_h
            )
            for el in grid.electrolysers
        )

    return total


def check_linear_opf_weights(weights_def):
    """Validate ObjRule weights for linear OPF / linear window drivers.

    Raises if ``SoC_deviation`` is weighted (quadratic). Warns on other
    non-zero weights outside ``Energy_cost`` / ``H2_sale`` (they are ignored
    by :func:`opf_obj_l`).
    """
    if weights_def[ObjComponent.SOC_DEVIATION]['w'] != 0:
        raise ValueError(
            "SoC_deviation is quadratic and is not supported in linear OPF"
        )
    supported_l = {ObjComponent.ENERGY_COST, ObjComponent.H2_SALE}
    other_weights_nonzero = [
        key for key, value in weights_def.items()
        if key not in supported_l and value['w'] != 0
    ]
    if other_weights_nonzero:
        warnings.warn(
            "Linear OPF only supports Energy_cost and H2_sale; "
            f"ignoring non-zero weights for {other_weights_nonzero}"
        )


def opf_obj_l_array_losses(model, grid, ObjRule):
    """Linear array-loss OPEX term (matches :func:`opf_obj` ``formula_Array_losses``)."""
    if ObjRule[ObjComponent.ARRAY_LOSSES]['w'] == 0:
        return 0
    ren_injected = 0
    if grid.RenSources:
        ren_injected = sum(
            model.P_renSource[rs] * model.np_rsgen[rs]
            for rs in model.ren_sources)
    substations_extracted = sum(
        model.PGi_opt[node]
        for node in model.nodes_AC
        if grid.nodes_AC[node].type == NodeType.SLACK)
    return (ren_injected + substations_extracted) * grid.LCoE * grid.S_base


def opf_obj(model,grid,weights_def):
    """Build the weighted OPF objective from component weights.

    Parameters
    ----------
    model : pyomo.ConcreteModel
        OPF model returned by :func:`~pyflow_acdc.NL_models.ACDC_OPF_NL_model.opf_create_nl_model_acdc`.
    grid : Grid
        Network being optimised.
    weights_def : dict
        Mapping of objective component names to ``{'w': weight}`` entries.

    Returns
    -------
    pyomo expression
        Weighted sum of the active sub-objectives.


    """
    np_den_eps = 1e-5

    def np_den(np_comp, g):
        # Offset only when the count can reach 0: a parameter at 0, or a variable with lower bound 0.
        np_g = np_comp[g]
        if np_comp.ctype is pyo.Var:
            np_min = np_g.lb
            if np_min is None:
                raise ValueError(f"{np_g.name} has no lower bound")
        elif np_comp.ctype is pyo.Param:
            np_min = pyo.value(np_g)
        else:
            raise TypeError(f"{np_comp.name} must be a Var or Param, got {np_comp.ctype}")
        return np_g + np_den_eps if np_min == 0 else np_g

    def formula_Min_Ext_Gen():
        if weights_def[ObjComponent.EXT_GEN]['w']==0:
            return 0
        return sum((model.PGi_opt[node]*grid.S_base) for node in model.nodes_AC)

    def formula_Energy_cost():
        if weights_def[ObjComponent.ENERGY_COST]['w']==0:
            return 0

        AC= 0
        DC= 0
        if grid.ACmode:
            if grid.act_gen:
                AC= sum((((model.PGi_gen[gen.genNumber]*grid.S_base)**2*gen.qf/np_den(model.np_gen, gen.genNumber)+model.PGi_gen[gen.genNumber]*grid.S_base*model.lf[gen.genNumber]+model.np_gen[gen.genNumber]*gen.fc)*model.gen_active[gen.genNumber]) for gen in grid.Generators)
            else:
                AC= sum(((model.PGi_gen[gen.genNumber]*grid.S_base)**2*gen.qf/np_den(model.np_gen, gen.genNumber)+model.PGi_gen[gen.genNumber]*grid.S_base*model.lf[gen.genNumber]+model.np_gen[gen.genNumber]*gen.fc) for gen in grid.Generators)
        if grid.DCmode:
            DC= sum(((model.PGi_gen_DC[gen.genNumber_DC]*grid.S_base)**2*gen.qf/np_den(model.np_gen_DC, gen.genNumber_DC)+model.PGi_gen_DC[gen.genNumber_DC]*grid.S_base*model.lf_dc[gen.genNumber_DC]+model.np_gen_DC[gen.genNumber_DC]*gen.fc) for gen in grid.Generators_DC)

        REN = 0
        if grid.RenSources:
            REN = sum(
                model.np_rsgen[rs] * (
                    (model.P_renSource[rs] * model.gamma[rs] * grid.S_base) ** 2
                    * grid.RenSources[rs].qf
                    + model.P_renSource[rs] * model.gamma[rs] * grid.S_base
                    * grid.RenSources[rs].lf
                )
                for rs in model.ren_sources
            )
        return AC + DC + REN
    def formula_AC_losses():
        if weights_def[ObjComponent.AC_LOSSES]['w']==0:
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
        if weights_def[ObjComponent.DC_LOSSES]['w']==0:
            return 0
        loss = sum(model.PDC_line_loss[line] for line in model.lines_DC)
        if grid.CDC:
            loss += sum(model.CDC_loss[conv] for conv in model.DCDC_conv)
        return loss*grid.LCoE

    def formula_Converter_Losses():
        if weights_def[ObjComponent.CONVERTER_LOSSES]['w']==0:
            return 0
        return sum(model.P_conv_loss[conv]+model.P_AC_loss_conv[conv] for conv in model.conv)*grid.LCoE

    def formula_General_Losses():
        if weights_def[ObjComponent.GENERAL_LOSSES]['w']==0:
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

    def formula_Array_losses():
        if weights_def[ObjComponent.ARRAY_LOSSES]['w'] == 0:
            return 0
        ren_injected = 0
        if grid.RenSources != []:
            ren_injected = sum(model.P_renSource[rs] *model.np_rsgen[rs] for rs in model.ren_sources)
        substations_extracted = sum(
            model.PGi_opt[node]
            for node in model.nodes_AC
            if grid.nodes_AC[node].type == NodeType.SLACK
        )
        return (ren_injected + substations_extracted) * grid.LCoE * grid.S_base

    def formula_curtailment_red():
        if weights_def[ObjComponent.CURTAILMENT_RED]['w']==0:
            return 0
        ac_curt=0
        dc_curt=0
        if grid.ACmode:
            ac_curt= sum((1-model.gamma[rs])*model.P_renSource[rs]*model.price[grid.rs2node['AC'].get(rs, 0)*model.np_rsgen[rs]]*rs.sigma for rs in model.ren_sources)*grid.S_base
        if grid.DCmode:
            dc_curt= sum((1-model.gamma[rs])*model.P_renSource[rs]*model.price_DC[grid.rs2node['DC'].get(rs, 0)*model.np_rsgen[rs]]*rs.sigma for rs in model.ren_sources)*grid.S_base
        return ac_curt+dc_curt
    def formula_CG():
       if weights_def[ObjComponent.PZ_COST_OF_GENERATION]['w']==0:
           return 0
       return sum(model.SocialCost[price_zone] for price_zone in model.M)

    def formula_Offshoreprofit():
        from .Classes import OffshorePrice_Zone
        if weights_def[ObjComponent.RENEWABLE_PROFIT]['w']==0:
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
        if weights_def[ObjComponent.GEN_SET_DEV]['w']==0:
            return 0
        return sum((model.PGi_gen[gen.genNumber]-gen.Pset*gen.np_gen)**2 for gen in grid.Generators)

    def formula_H2_sale():
        if weights_def[ObjComponent.H2_SALE]['w'] == 0:
            return 0
        if not grid.H2:
            raise ValueError("H2_sale weight > 0 requires grid.H2 / electrolysers")
        # Minimise -price·Δm  ≡  maximise H₂ sale revenue (EUR for Δm in kg).
        # h2_price defaults to 0 → term is zero until set or driven by H2_PRICE TS.
        return sum(
            -float(el.h2_price) * (
                el.b_h * model.P_electrolyser[el.electrolyserNumber] * el.S_base * el.dt_hours
                + el.c_h
            )
            for el in grid.electrolysers
        )

    def formula_SoC_deviation():
        if weights_def[ObjComponent.SOC_DEVIATION]['w'] == 0:
            return 0
        if not grid.ESS:
            raise ValueError("SoC_deviation weight > 0 requires grid.ESS / storage")
        total = 0
        for st in grid.storage_elements:
            s = st.storageNumber
            total += (model.SoC[s] - model.soc_ref[s]) ** 2
        return total

    s=1
    for key, entry in weights_def.items():
        if key == ObjComponent.EXT_GEN:
            entry['f'] = formula_Min_Ext_Gen()
        elif key == ObjComponent.ENERGY_COST:
            entry['f'] = formula_Energy_cost()
        elif key == ObjComponent.AC_LOSSES:
            entry['f'] = formula_AC_losses()
        elif key == ObjComponent.DC_LOSSES:
            entry['f'] = formula_DC_losses()
        elif key == ObjComponent.CONVERTER_LOSSES:
            entry['f'] = formula_Converter_Losses()
        elif key == ObjComponent.GENERAL_LOSSES:
            entry['f'] = formula_General_Losses()
        elif key == ObjComponent.ARRAY_LOSSES:
            entry['f'] = formula_Array_losses()
        elif key == ObjComponent.CURTAILMENT_RED:
            entry ['f'] = formula_curtailment_red()
        elif key == ObjComponent.PZ_COST_OF_GENERATION:
            entry['f']  =formula_CG()
        elif key == ObjComponent.RENEWABLE_PROFIT:
            entry['f']  =formula_Offshoreprofit()
        elif key == ObjComponent.GEN_SET_DEV:
            entry['f']  =formula_Gen_set_dev()
        elif key == ObjComponent.H2_SALE:
            entry['f'] = formula_H2_sale()
        elif key == ObjComponent.SOC_DEVIATION:
            entry['f'] = formula_SoC_deviation()
    s=1
    total_weight = sum(entry['w'] for entry in weights_def.values())
    if total_weight== 0:
        weighted_sum=0
    else:
        weighted_sum = sum(entry['w'] / total_weight * entry['f'] for entry in weights_def.values())


    return weighted_sum






def translate_pyf_opf(grid,Price_Zones=False):
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

    nn_st = 0
    P_charge_max, P_discharge_max, P_max_st, S_max_st = {}, {}, {}, {}
    soc_min_st, soc_max_st, soc_initial, soc_ref, soc_final = {}, {}, {}, {}, {}
    eta_charge, eta_discharge, E_max_st, dt_hours_st, S_base_st = {}, {}, {}, {}, {}
    connected_st = {}
    for s in grid.storage_elements:
        nn_st += 1
        n = s.storageNumber
        P_charge_max[n] = s.P_charge_max
        P_discharge_max[n] = s.P_discharge_max
        P_max_st[n] = s.P_max
        S_max_st[n] = s.S_max if s.connected == AcDcSide.AC else 0.0
        soc_min_st[n] = s.soc_min
        soc_max_st[n] = s.soc_max
        soc_initial[n] = s.soc_initial
        soc_ref[n] = s.soc_ref
        soc_final[n] = s.soc_final
        eta_charge[n] = s.eta_charge
        eta_discharge[n] = s.eta_discharge
        E_max_st[n] = s.E_max
        dt_hours_st[n] = s.dt_hours
        S_base_st[n] = s.S_base
        connected_st[n] = s.connected
    lista_storage = list(range(0, nn_st))
    storage_lim = pack_variables(P_charge_max, P_discharge_max, P_max_st, S_max_st)
    storage_soc = pack_variables(
        soc_min_st, soc_max_st, soc_initial, soc_ref, soc_final)
    storage_phys = pack_variables(
        eta_charge, eta_discharge, E_max_st, dt_hours_st, S_base_st, connected_st)
    storage_info = pack_variables(storage_lim, storage_soc, storage_phys, lista_storage)

    nn_el = 0
    P_min_el, P_max_el, Q_min_el, Q_max_el, H2_mass_max = {}, {}, {}, {}, {}
    H2_mass_initial, H2_mass_final = {}, {}
    b_h, c_h, S_base_el, dt_hours_el, connected_el = {}, {}, {}, {}, {}
    for el in grid.electrolysers:
        nn_el += 1
        e = el.electrolyserNumber
        P_min_el[e] = el.P_min
        P_max_el[e] = el.P_max
        Q_min_el[e] = el.Q_min if el.connected == AcDcSide.AC else 0.0
        Q_max_el[e] = el.Q_max if el.connected == AcDcSide.AC else 0.0
        H2_mass_max[e] = el.H2_mass_max
        H2_mass_initial[e] = el.H2_mass_initial
        H2_mass_final[e] = el.H2_mass_final
        b_h[e] = el.b_h
        c_h[e] = el.c_h
        S_base_el[e] = el.S_base
        dt_hours_el[e] = el.dt_hours
        connected_el[e] = el.connected
    lista_electrolyser = list(range(0, nn_el))
    hydrogen_lim = pack_variables(
        P_min_el, P_max_el, Q_min_el, Q_max_el, H2_mass_max)
    hydrogen_state = pack_variables(H2_mass_initial, H2_mass_final)
    hydrogen_phys = pack_variables(
        b_h, c_h, S_base_el, dt_hours_el, connected_el)
    hydrogen_info = pack_variables(
        hydrogen_lim, hydrogen_state, hydrogen_phys, lista_electrolyser)

    "Price zone info"

    price_zone_prices, price_zone_as, price_zone_bs, PGL_min, PGL_max =  {}, {}, {}, {}, {}
    nn_M, lista_M = 0, []
    node2price_zone = {'DC': {}, 'AC': {}}
    price_zone2node = {'DC': {}, 'AC': {}}
    if Price_Zones:
        for m in grid.Price_Zones:

            nn_M += 1
            price_zone_prices[m.price_zone_num] = m.price
            price_zone_as[m.price_zone_num] = m.a
            price_zone_bs[m.price_zone_num] = m.b
            if ACmode:
                price_zone2node['AC'][m.price_zone_num] = []
                for n in m.nodes_AC:
                    price_zone2node['AC'][m.price_zone_num].append(n.nodeNumber)
                    node2price_zone['AC'][n.nodeNumber] = m.price_zone_num

            if DCmode:
                price_zone2node['DC'][m.price_zone_num] = []
                for n in m.nodes_DC:
                    price_zone2node['DC'][m.price_zone_num].append(n.nodeNumber)
                    node2price_zone['DC'][n.nodeNumber] = m.price_zone_num
            pgl_min_val = float(getattr(m, 'PGL_min', -np.inf))
            pgl_max_val = float(getattr(m, 'PGL_max', np.inf))
            if not np.isfinite(pgl_min_val):
                pgl_min_val = float(m.min_PGL_min)
            if not np.isfinite(pgl_max_val):
                pgl_max_val = float(m.max_PGL_max)

            PGL_min[m.price_zone_num] = pgl_min_val
            PGL_max[m.price_zone_num] = pgl_max_val
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

            if n.type == NodeType.SLACK:
                AC_slack.append(n.nodeNumber)
            elif n.type == NodeType.PV:
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
            if n.type == ConverterDCType.SLACK:
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
        'gen_info': gen_info,
        'storage_info': storage_info,
        'hydrogen_info': hydrogen_info,
    }




def opf_line_res (model,grid):
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


def opf_price_price_zone (model,grid):
    opt_res_Loading_pz = {}
    for pz in grid.Price_Zones:
        m= pz.price_zone_num
        price = pyo.value(model.price_zone_price[m])
        opt_res_Loading_pz[pz.name]=price


    return opt_res_Loading_pz

def opf_step_results(model,grid):
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
            if element.np_rsgen >0 :
                opt_res_curtailment [name] = 1-gamma
            else:
                opt_res_curtailment [name] = 0
            # Renewable "multiplicity" is captured by model.np_rsgen in the OPF constraints.
            # For time-series export we must include it as well, otherwise RenSource_* columns
            # represent only one unit instead of the total installed multiplicity.
            rs_multiplicity = np.float64(pyo.value(model.np_rsgen[element.rsNumber]))
            opt_res_P_extGrid[f'RenSource_{name}'] = Pren_values[element.rsNumber] * gamma * rs_multiplicity
            opt_res_Q_extGrid[f'RenSource_{name}'] = Qren_values[element.rsNumber] * rs_multiplicity

    # Combine Generators and Renewable Sources into one iterable
    elements = grid.Generators + grid.RenSources

    # Parallelize processing
    with ThreadPoolExecutor() as executor:
        executor.map(process_element, elements)


    return (opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,
                opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,
                opt_res_Loading_conv)


def opf_step_results_l(model, grid):
    """TS step reporting for linear OPF (P-only; converter Q = 0)."""
    opt_res_P_conv_DC = {}
    opt_res_P_conv_AC = {}
    opt_res_Q_conv_AC = {}
    opt_res_Loading_conv = {}
    opt_P_load = {}
    opt_res_P_extGrid = {}
    opt_res_Q_extGrid = {}
    opt_res_curtailment = {}

    if grid.ACmode and grid.DCmode:
        P_conv_s_AC_values = {
            k: np.float64(pyo.value(v)) for k, v in model.P_conv_s_AC.items()}

        def process_converter(conv):
            nconv = conv.ConvNumber
            name = conv.name
            Ps = P_conv_s_AC_values[nconv]
            loss_pu = float(conv.a_conv) + float(conv.b_conv) * Ps
            pac = Ps * conv.np_conv
            pdc = -(pac + loss_pu * conv.np_conv)
            opt_res_P_conv_AC[name] = pac
            opt_res_Q_conv_AC[name] = 0.0
            opt_res_P_conv_DC[name] = pdc
            if conv.np_conv == 0:
                opt_res_Loading_conv[name] = 0
            else:
                opt_res_Loading_conv[name] = (
                    max(abs(pac), abs(pdc)) * grid.S_base
                    / (conv.MVA_max * conv.np_conv)
                )

        with ThreadPoolExecutor() as executor:
            executor.map(process_converter, grid.Converters_ACDC)

    if grid.ACmode:
        Pload_values = {
            k: np.float64(pyo.value(v)) for k, v in model.P_known_AC.items()}
        PGen_values = {
            k: np.float64(pyo.value(v)) for k, v in model.PGi_gen.items()}
        for node in grid.nodes_AC:
            opt_P_load[node.name] = -Pload_values[node.nodeNumber]
        for gen in grid.Generators:
            opt_res_P_extGrid[gen.name] = PGen_values[gen.genNumber]
            opt_res_Q_extGrid[gen.name] = 0.0

    if grid.DCmode and grid.Generators_DC:
        PGen_DC_values = {
            k: np.float64(pyo.value(v)) for k, v in model.PGi_gen_DC.items()}
        for gen in grid.Generators_DC:
            opt_res_P_extGrid[gen.name] = PGen_DC_values[gen.genNumber_DC]
            opt_res_Q_extGrid[gen.name] = 0.0

    gamma_values = {k: np.float64(pyo.value(v)) for k, v in model.gamma.items()}
    Pren_values = {
        k: np.float64(pyo.value(v)) for k, v in model.P_renSource.items()}
    for rs in grid.RenSources:
        name = rs.name
        gamma = gamma_values[rs.rsNumber]
        opt_res_curtailment[name] = (
            1 - gamma if rs.np_rsgen > 0 else 0)
        rs_multiplicity = np.float64(pyo.value(model.np_rsgen[rs.rsNumber]))
        opt_res_P_extGrid[f'RenSource_{name}'] = (
            Pren_values[rs.rsNumber] * gamma * rs_multiplicity)
        opt_res_Q_extGrid[f'RenSource_{name}'] = 0.0

    return (
        opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,
        opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,
        opt_res_Loading_conv,
    )


def calculate_objective(grid,obj):

    if obj ==ObjComponent.EXT_GEN:
        return sum((node.PGi_opt*grid.S_base) for node in grid.nodes_AC)

    if obj ==ObjComponent.ENERGY_COST:
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
        REN = 0
        if grid.RenSources:
            REN = sum(
                rs.np_rsgen * (
                    (rs.PGi_ren * rs.gamma * grid.S_base) ** 2 * rs.qf
                    + rs.PGi_ren * rs.gamma * grid.S_base * rs.lf
                )
                for rs in grid.RenSources
            )
        return AC + DC + REN




    if obj ==ObjComponent.AC_LOSSES:
        return (sum(line.P_loss for line in grid.lines_AC)+
                sum(tf.P_loss for tf in grid.lines_AC_tf)+
                sum(line.P_loss for line in grid.lines_AC_exp)+
                sum(line.P_loss for line in grid.lines_AC_rec)+
                sum(line.P_loss for line in grid.lines_AC_ct))*grid.S_base*grid.LCoE

    if obj ==ObjComponent.DC_LOSSES:
        return (sum(line.loss for line in grid.lines_DC)+
                sum(conv.loss for conv in grid.Converters_DCDC))*grid.S_base*grid.LCoE

    if obj ==ObjComponent.CONVERTER_LOSSES:
        return sum(conv.P_loss for conv in grid.Converters_ACDC)*grid.S_base*grid.LCoE

    if obj ==ObjComponent.GENERAL_LOSSES:
        return (sum(line.P_loss for line in grid.lines_AC) +
                sum(tf.P_loss for tf in grid.lines_AC_tf) +
                sum(line.P_loss for line in grid.lines_AC_exp) +
                sum(line.loss for line in grid.lines_DC) +
                sum(conv.P_loss for conv in grid.Converters_ACDC))*grid.S_base*grid.LCoE

    if obj == ObjComponent.ARRAY_LOSSES:
        ren_injected = sum(rs.PGi_ren * rs.gamma * rs.np_rsgen for rs in grid.RenSources) * grid.S_base
        substations_extracted = sum(
            node.PGi_opt * grid.S_base
            for node in grid.nodes_AC
            if node.type == NodeType.SLACK
        )
        return (ren_injected - substations_extracted) * grid.LCoE

    if obj ==ObjComponent.CURTAILMENT_RED:
        ac_curt=0
        dc_curt=0
        if grid.ACmode:
            ac_curt= sum((1-rs.gamma)*rs.PGi_ren*grid.nodes_AC[grid.rs2node['AC'].get(rs, 0)].price*rs.np_rsgen*rs.sigma for rs in grid.RenSources)*grid.S_base
        if  grid.DCmode:
            dc_curt= sum((1-rs.gamma)*rs.PGi_ren*grid.nodes_DC[grid.rs2node['DC'].get(rs, 0)].price*rs.np_rsgen*rs.sigma for rs in grid.RenSources)*grid.S_base
        return ac_curt+dc_curt
    if obj ==ObjComponent.PZ_COST_OF_GENERATION:
       return sum(pz.a*(pz.PN*grid.S_base)**2+pz.b*(pz.PN*grid.S_base) for pz in grid.Price_Zones)


    if obj==ObjComponent.GEN_SET_DEV:
        return sum((gen.PGen-gen.Pset*gen.np_gen)**2 for gen in grid.Generators)

    if obj == ObjComponent.H2_SALE:
        if not grid.H2:
            return 0
        total = 0.0
        for el in grid.electrolysers:
            h_prod = el.b_h * el.P_electrolyser * el.S_base * el.dt_hours + el.c_h
            total += -float(el.h2_price) * h_prod
        return total

    if obj == ObjComponent.SOC_DEVIATION:
        if not grid.ESS:
            return 0
        return sum((st.SoC - st.soc_ref) ** 2 for st in grid.storage_elements)

    return 0

def calculate_objective_from_model(model, grid, weights_def):
    """
    Calculate weighted objective value directly from a solved Pyomo model.
    Uses opf_obj() to build the expression, then evaluates it once.

    Args:
        model: Solved Pyomo model
        grid: Grid object (needed for generator properties and grid structure)
        weights_def: Objective weights (same format as opf_obj)

    Returns:
        Weighted sum of objectives (float)
    """
    # Build the objective expression (Pyomo expression)
    obj = opf_obj(model, grid, weights_def)
    # Evaluate it once
    obj_value = pyo.value(obj)
    return obj_value
