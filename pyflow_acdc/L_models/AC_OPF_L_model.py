# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:25:02 2024

@author: BernardoCastro
"""

import pyomo.environ as pyo
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from ..constants import CT_SELECTION_THRESHOLD, BINARY_THRESHOLD


__all__ = [
    'opf_create_l_model_acdc',
    'export_acdc_l_model_to_pyflow_acdc',
]


def opf_create_l_model_acdc(model,grid,TEP=False,window_block=False):
    """Populate ``model`` with the linearised AC(/DC) OPF formulation.

    Builds AC Bθ, linearized DC power flow, and thin LP converters according to
    ``grid.ACmode`` / ``grid.DCmode`` (same flag pattern as the NL builder).
    Mutates ``model`` in place; does not add the objective or solve.

    When ``grid.ESS`` / ``grid.H2``, also adds BESS (P-only, no Q / S-circle)
    and electrolyser inventory (P load + mass balance) on AC and/or DC.

    Parameters
    ----------
    model : pyomo.ConcreteModel
        Empty model to populate (mutated in place).
    grid : Grid
        Source of network data.
    TEP : bool, optional
        Add transmission-expansion (cable-type selection) variables.
        Hybrid ``TEP=True`` with ``grid.DCmode`` is not wired yet (raises).
    window_block : bool, optional
        If True, omit in-block SoC / H₂ ``*_prev`` balance (parent window
        links own inventory). Used by :func:`~pyflow_acdc.window_l_opf`.

    Examples
    --------
    >>> opf_create_l_model_acdc(model, grid, TEP=False)
    """
    from ..ACDC_OPF import translate_pyf_opf

    if TEP and grid.DCmode:
        raise ValueError(
            "Linear hybrid TEP (TEP=True with grid.DCmode) is not wired yet"
        )

    opf_data = translate_pyf_opf(grid)
    AC_info = opf_data['AC_info']
    DC_info = opf_data['DC_info']
    Conv_info = opf_data['Conv_info']
    gen_info = opf_data['gen_info']
    storage_info = opf_data['storage_info']
    hydrogen_info = opf_data['hydrogen_info']

    Generation_variables(model, grid, gen_info, TEP)

    if grid.ESS:
        storage_variables_l(model, grid, storage_info, window_block=window_block)
    if grid.H2:
        hydrogen_variables_l(model, grid, hydrogen_info, window_block=window_block)

    if grid.ACmode:
        AC_variables(model, grid, AC_info)

    if grid.DCmode:
        DC_variables_l(model, grid, DC_info, TEP=TEP)

    if grid.ACmode and grid.DCmode:
        Converter_variables_l(model, grid, Conv_info, TEP=TEP)

    if TEP:
        TEP_variables(model, grid)
    else:
        TEP_parameters(model, grid)

    if grid.ESS:
        storage_constraints_l(model, grid, storage_info, window_block=window_block)
    if grid.H2:
        hydrogen_constraints_l(model, grid, hydrogen_info, window_block=window_block)

    if grid.ACmode:
        AC_constraints(model, grid, AC_info)

    if grid.DCmode:
        DC_constraints_l(model, grid, DC_info, TEP=TEP)

    if grid.ACmode and grid.DCmode:
        Converter_constraints_l(model, grid, Conv_info, TEP=TEP)


def storage_variables_l(model, grid, storage_info, window_block=False):
    """BESS for linear OPF: one element set (AC/DC via ``connected``), P-only."""
    if storage_info is None:
        raise ValueError("storage_info is required when grid.ESS is True")
    storage_lim, storage_soc, storage_phys, lista_storage = storage_info
    P_charge_max, P_discharge_max, P_max_st, _S_max_st = storage_lim
    soc_min_st, soc_max_st, soc_initial, soc_ref_map, _soc_final = storage_soc
    _eta_c, _eta_d, _E_max, _dt, _S_base, _connected = storage_phys
    if not lista_storage:
        raise ValueError("storage_info is empty but grid.ESS is True")

    model.storage = pyo.Set(initialize=lista_storage)

    def P_storage_charge_bounds(model, s):
        return (0, P_charge_max[s])

    def P_storage_discharge_bounds(model, s):
        return (0, P_discharge_max[s])

    def soc_bounds(model, s):
        return (soc_min_st[s], soc_max_st[s])

    model.P_storage_charge = pyo.Var(
        model.storage, bounds=P_storage_charge_bounds, initialize=0)
    model.P_storage_discharge = pyo.Var(
        model.storage, bounds=P_storage_discharge_bounds, initialize=0)
    # Fixed at 0 (P-only linear); kept so shared window/TS paths match NL.
    model.Q_storage = pyo.Var(model.storage, bounds=(0, 0), initialize=0)
    model.SoC = pyo.Var(
        model.storage,
        bounds=soc_bounds,
        initialize={s: soc_initial[s] for s in lista_storage},
    )
    model.soc_ref = pyo.Param(
        model.storage,
        initialize={s: soc_ref_map[s] for s in lista_storage},
        mutable=True,
    )
    if not window_block:
        model.SoC_prev = pyo.Param(
            model.storage,
            initialize={s: soc_initial[s] for s in lista_storage},
            mutable=True,
        )


def storage_constraints_l(model, grid, storage_info, window_block=False):
    """BESS SoC balance and |P_net| ≤ ``P_max`` for linear OPF."""
    if storage_info is None:
        raise ValueError("storage_info is required when grid.ESS is True")
    storage_lim, _storage_soc, storage_phys, _lista = storage_info
    _Pc, _Pd, P_max_st, _S_max = storage_lim
    eta_charge, eta_discharge, E_max_st, dt_hours_st, S_base_st, _conn = storage_phys

    if not window_block:
        def soc_balance_rule(model, s):
            scale = dt_hours_st[s] * S_base_st[s] / E_max_st[s]
            return model.SoC[s] == (
                model.SoC_prev[s]
                + scale * (
                    eta_charge[s] * model.P_storage_charge[s]
                    - model.P_storage_discharge[s] / eta_discharge[s]
                )
            )

        model.storage_soc_balance_constraint = pyo.Constraint(
            model.storage, rule=soc_balance_rule)

    def P_net_upper_rule(model, s):
        return (
            model.P_storage_discharge[s] - model.P_storage_charge[s] <= P_max_st[s]
        )

    def P_net_lower_rule(model, s):
        return (
            model.P_storage_charge[s] - model.P_storage_discharge[s] <= P_max_st[s]
        )

    model.P_storage_net_upper_constraint = pyo.Constraint(
        model.storage, rule=P_net_upper_rule)
    model.P_storage_net_lower_constraint = pyo.Constraint(
        model.storage, rule=P_net_lower_rule)


def hydrogen_variables_l(model, grid, hydrogen_info, window_block=False):
    """Electrolyser for linear OPF: P load + mass inventory (no Q)."""
    if hydrogen_info is None:
        raise ValueError("hydrogen_info is required when grid.H2 is True")
    hydrogen_lim, hydrogen_state, _hydrogen_phys, lista_electrolyser = hydrogen_info
    P_min_el, P_max_el, _Q_min, _Q_max, H2_mass_max = hydrogen_lim
    H2_mass_initial, _H2_mass_final = hydrogen_state
    if not lista_electrolyser:
        raise ValueError("hydrogen_info is empty but grid.H2 is True")

    model.electrolyser = pyo.Set(initialize=lista_electrolyser)

    def P_electrolyser_bounds(model, e):
        return (P_min_el[e], P_max_el[e])

    def mass_H2_bounds(model, e):
        return (0, H2_mass_max[e])

    model.P_electrolyser = pyo.Var(
        model.electrolyser,
        bounds=P_electrolyser_bounds,
        initialize={
            e: 0.5 * (P_min_el[e] + P_max_el[e]) for e in lista_electrolyser
        },
    )
    model.mass_H2 = pyo.Var(
        model.electrolyser,
        bounds=mass_H2_bounds,
        initialize={e: H2_mass_initial[e] for e in lista_electrolyser},
    )
    if not window_block:
        model.mass_H2_prev = pyo.Param(
            model.electrolyser,
            initialize={e: H2_mass_initial[e] for e in lista_electrolyser},
            mutable=True,
        )


def hydrogen_constraints_l(model, grid, hydrogen_info, window_block=False):
    """H₂ mass balance for electrolysers in linear OPF."""
    if window_block:
        return
    if hydrogen_info is None:
        raise ValueError("hydrogen_info is required when grid.H2 is True")
    _lim, _state, hydrogen_phys, _lista = hydrogen_info
    b_h, c_h, S_base_el, dt_hours_el, _connected = hydrogen_phys

    def mass_h2_balance_rule(model, e):
        h_prod = b_h[e] * model.P_electrolyser[e] * S_base_el[e] * dt_hours_el[e] + c_h[e]
        return model.mass_H2[e] == model.mass_H2_prev[e] + h_prod

    model.mass_H2_balance_constraint = pyo.Constraint(
        model.electrolyser, rule=mass_h2_balance_rule)


def Generation_variables(model,grid,gen_info,TEP):
    from ..grid_analysis import get_gen_p_min_eff

    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    lf,qf,fc,np_gen,lista_gen = gen_AC_info
    lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC = gen_DC_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info

    model.ren_sources= pyo.Set(initialize=lista_rs)
    model.P_renSource = pyo.Param(model.ren_sources,initialize=P_renSource,mutable=True)

    def gamma_bounds(model,rs):
        ren_source= grid.RenSources[rs]
        if ren_source.curtailable:
            return (ren_source.min_gamma,1)
        else:
            return (1,1)
    model.gamma = pyo.Var(model.ren_sources, bounds=gamma_bounds, initialize=1)

    grid.GPR = False
    grid.rs_GPR = False

    if grid.ACmode and any(gen.np_gen_opf for gen in grid.Generators) and TEP:
        grid.GPR = True
    if any(rs.np_rsgen_opf for rs in grid.RenSources) and TEP:
        grid.rs_GPR = True

    def P_Gen_bounds(model, g):
        gen = grid.Generators[g]
        return (get_gen_p_min_eff(gen, gen.np_gen), gen.Max_pow_gen * gen.np_gen)

    def P_gen_ini(model,ngen):
        gen = grid.Generators[ngen]
        min_pow_gen = get_gen_p_min_eff(gen, gen.np_gen)
        ini=gen.Pset * gen.np_gen
        max_pow_gen = gen.Max_pow_gen * gen.np_gen
        if  min_pow_gen>ini:
            ini=min_pow_gen
        elif ini>max_pow_gen:
            ini=max_pow_gen
        return (ini)

    if grid.ACmode:
        model.gen_AC     = pyo.Set(initialize=lista_gen)

        if grid.GPR:
            if TEP:
                p_load_eff_ini = {gen.genNumber: gen.p_load_eff for gen in grid.Generators}
                model.P_load_eff = pyo.Param(model.gen_AC, initialize=p_load_eff_ini, mutable=True)
            model.PGi_gen = pyo.Var(model.gen_AC, initialize=P_gen_ini)
        else:
            model.PGi_gen = pyo.Var(model.gen_AC,bounds=P_Gen_bounds, initialize=P_gen_ini)

        model.lf = pyo.Param (model.gen_AC, initialize=lf, mutable=True)

    if grid.DCmode:
        def P_Gen_bounds_DC(model, g):
            gen = grid.Generators_DC[g]
            return (gen.Min_pow_gen * gen.np_gen, gen.Max_pow_gen * gen.np_gen)

        def P_gen_ini_DC(model, g):
            gen = grid.Generators_DC[g]
            min_pow_gen = gen.Min_pow_gen * gen.np_gen
            ini = gen.Pset * gen.np_gen
            max_pow_gen = gen.Max_pow_gen * gen.np_gen
            if min_pow_gen > ini:
                ini = min_pow_gen
            elif ini > max_pow_gen:
                ini = max_pow_gen
            return ini

        model.gen_DC = pyo.Set(initialize=lista_gen_DC)
        model.PGi_gen_DC = pyo.Var(
            model.gen_DC, bounds=P_Gen_bounds_DC, initialize=P_gen_ini_DC)
        model.lf_dc = pyo.Param(model.gen_DC, initialize=lf_DC, mutable=True)


def AC_variables(model,grid,AC_info):

    AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info


    lista_nodos_AC, lista_lineas_AC,lista_lineas_AC_tf,AC_slack, AC_PV = AC_Lists
    u_min_ac,u_max_ac,V_ini_AC,Theta_ini, P_know,Q_know,price = AC_nodes_info
    S_lineAC_limit,S_lineACtf_limit,m_tf_og = AC_lines_info

    lista_lineas_AC_exp,S_lineACexp_limit,NP_lineAC = EXP_info
    lista_lineas_AC_rec,S_lineACrec_lim,S_lineACrec_lim_new,grid.REC_AC_act = REC_info
    lista_lineas_AC_ct,S_lineACct_lim,cab_types_set,allowed_types = CT_info

    "Model Sets"
    model.nodes_AC   = pyo.Set(initialize=lista_nodos_AC)
    model.lines_AC   = pyo.Set(initialize=lista_lineas_AC)

    if grid.TEP_AC:
        model.lines_AC_exp = pyo.Set(initialize=lista_lineas_AC_exp)
    if grid.REC_AC:
        model.lines_AC_rec = pyo.Set(initialize=lista_lineas_AC_rec)
    if grid.CT_AC:
        model.lines_AC_ct = pyo.Set(initialize=lista_lineas_AC_ct)



    model.AC_slacks  = pyo.Set(initialize=AC_slack)


    "AC Variables"
    #AC nodes variables
    model.theta_AC  = pyo.Var(model.nodes_AC, bounds=(-1.6, 1.6), initialize=Theta_ini)

    model.P_known_AC = pyo.Param(model.nodes_AC, initialize=P_know,mutable=True)

    def Pren_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_RenSource == []:
            return (0,0)
        else:
            return (None,None)


    model.PGi_ren = pyo.Var(model.nodes_AC, bounds=Pren_bounds,initialize=0)

    def PGi_opt_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if nAC.connected_gen == []:
            return (0,0)
        else:
            return (None,None)

    model.PGi_opt = pyo.Var(model.nodes_AC,bounds=PGi_opt_bounds ,initialize=0)

    if grid.ESS:
        def Pstorage_bounds(model, node):
            nAC = grid.nodes_AC[node]
            if not nAC.connected_storage:
                return (0, 0)
            return (None, None)

        model.PGi_storage = pyo.Var(
            model.nodes_AC, bounds=Pstorage_bounds, initialize=0)

    if grid.H2:
        def Pelectrolyser_bounds(model, node):
            nAC = grid.nodes_AC[node]
            if not nAC.connected_electrolyser:
                return (0, 0)
            return (None, None)

        model.PGi_electrolyser = pyo.Var(
            model.nodes_AC, bounds=Pelectrolyser_bounds, initialize=0)

    def make_opt_bounds(attribute_name):
        def bounds_func(model, node):
            nAC = grid.nodes_AC[node]
            connected_lines = getattr(nAC, attribute_name)
            return (0, 0) if not connected_lines else (None, None)
        return bounds_func

    # Create bounds functions dynamically
    toExp_opt_bounds    = make_opt_bounds('connected_toExpLine')
    fromExp_opt_bounds  = make_opt_bounds('connected_fromExpLine')

    toREC_opt_bounds    = make_opt_bounds('connected_toRepLine')
    fromREC_opt_bounds  = make_opt_bounds('connected_fromRepLine')
    toCT_opt_bounds     = make_opt_bounds('connected_toCTLine')
    fromCT_opt_bounds   = make_opt_bounds('connected_fromCTLine')

    if grid.TEP_AC:
        model.Pto_Exp  = pyo.Var(model.nodes_AC,bounds=toExp_opt_bounds ,initialize=0)
        model.Pfrom_Exp= pyo.Var(model.nodes_AC,bounds=fromExp_opt_bounds ,initialize=0)

    if grid.REC_AC:
        model.Pto_REP   = pyo.Var(model.nodes_AC,bounds=toREC_opt_bounds ,initialize=0)
        model.Pfrom_REP = pyo.Var(model.nodes_AC,bounds=fromREC_opt_bounds ,initialize=0)

    if grid.CT_AC:
        model.Pto_CT   = pyo.Var(model.nodes_AC,bounds=toCT_opt_bounds ,initialize=0)
        model.Pfrom_CT = pyo.Var(model.nodes_AC,bounds=fromCT_opt_bounds ,initialize=0)

    def AC_theta_slack_rule(model, node):
        return model.theta_AC[node] == 0

    model.AC_theta_slack_constraint = pyo.Constraint(model.AC_slacks, rule=AC_theta_slack_rule)

    #AC Lines variables
    def Sbounds_lines(model, line):
        return (-S_lineAC_limit[line], S_lineAC_limit[line])


    model.PAC_to       = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.PAC_from     = pyo.Var(model.lines_AC, bounds=Sbounds_lines, initialize=0)
    model.PAC_line_loss= pyo.Var(model.lines_AC, initialize=0)

    def Sbounds_lines_exp(model, line):
        return (-S_lineACexp_limit[line], S_lineACexp_limit[line])

    if grid.TEP_AC:
        model.exp_PAC_to       = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_PAC_from     = pyo.Var(model.lines_AC_exp, bounds=Sbounds_lines_exp, initialize=0)
        model.exp_PAC_line_loss= pyo.Var(model.lines_AC_exp, initialize=0)


    def state_based_bounds(model, line, state):
            max_min = max(S_lineACrec_lim[line], S_lineACrec_lim_new[line])
            return (-max_min, max_min)

    if grid.REC_AC:
        # Define a set for the branch states (0=old, 1=new)
        model.branch_states = pyo.Set(initialize=[0, 1])

        # Single variable for all power flows with two indices
        model.rec_PAC_to   = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_PAC_from = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_PAC_line_loss = pyo.Var(model.lines_AC_rec,initialize=0)

        # Auxiliary (McCormick/big-M) variables carrying the flow of the active
        # branch state only: rec_z == rec_PAC when that state is active, else 0.
        # Linearises rec_PAC[state] * indicator(state active) so the node
        # injection stays linear (same pattern as the CT z_to/z_from vars).
        model.rec_z_to   = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)
        model.rec_z_from = pyo.Var(model.lines_AC_rec,model.branch_states,bounds=state_based_bounds,initialize=0)

    def set_based_bounds(model, line, cab_type):
        # Check if this is a fixed route with no cable selected
        if  grid.lines_AC_ct[line].active_config < 0:
            return (0, 0)  # Force z variables to zero

        # Original logic for variable bounds
        max_min = max(S_lineACct_lim[line,ct] for ct in cab_types_set)
        return (-max_min, max_min)


    if grid.CT_AC:

        model.ct_set = pyo.Set(initialize=cab_types_set)
        model.ct_PAC_to   = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)
        model.ct_PAC_from = pyo.Var(model.lines_AC_ct,model.ct_set,initialize=0)

        model.z_to = pyo.Var(model.lines_AC_ct, model.ct_set, bounds=set_based_bounds,initialize=0)
        model.z_from = pyo.Var(model.lines_AC_ct, model.ct_set, bounds=set_based_bounds,initialize=0)



def AC_constraints(model,grid,AC_info):


    AC_Lists,AC_nodes_info,AC_lines_info,EXP_info,REC_info,CT_info = AC_info
    S_lineAC_limit,S_lineACtf_limit,m_tf_og = AC_lines_info

    lista_lineas_AC_exp,S_lineACexp_limit,NP_lineAC = EXP_info
    lista_lineas_AC_rec,S_lineACrec_lim,S_lineACrec_lim_new,grid.REC_AC_act = REC_info
    lista_lineas_AC_ct,S_lineACct_lim,cab_types_set,allowed_types = CT_info

    "AC equality constraints"
    # AC node constraints
    def P_AC_node_rule(model, node):
        P_sum = sum(
            -np.imag(grid.Ybus_AC[node, k]) * (model.theta_AC[node] - model.theta_AC[k])
            for k in model.nodes_AC if grid.Ybus_AC[node, k] != 0
        )
        P_var = model.P_known_AC[node] + model.PGi_ren[node] + model.PGi_opt[node]
        if grid.ESS:
            P_var += model.PGi_storage[node]
        if grid.H2:
            P_var -= model.PGi_electrolyser[node]
        if grid.DCmode:
            P_var += model.P_conv_AC[node]

        if grid.TEP_AC:
            P_sum += model.Pto_Exp[node]+model.Pfrom_Exp[node]
        if grid.REC_AC:
            P_sum += model.Pto_REP[node]+model.Pfrom_REP[node]
        if grid.CT_AC:
            P_sum += model.Pto_CT[node]+model.Pfrom_CT[node]

        return P_sum == P_var


    model.P_AC_node_constraint = pyo.Constraint(model.nodes_AC, rule=P_AC_node_rule)

    # Adds all generators in the AC nodes they are connected to
    def Gen_PAC_rule(model,node):
       nAC = grid.nodes_AC[node]
       P_gen = sum(model.PGi_gen[gen.genNumber] for gen in nAC.connected_gen)
       return  model.PGi_opt[node] ==   P_gen

    model.Gen_PAC_constraint = pyo.Constraint(model.nodes_AC, rule=Gen_PAC_rule)

    if grid.ESS:
        def Gen_Pstorage_rule(model, node):
            nAC = grid.nodes_AC[node]
            p_stor = sum(
                model.P_storage_discharge[s.storageNumber]
                - model.P_storage_charge[s.storageNumber]
                for s in nAC.connected_storage
            )
            return model.PGi_storage[node] == p_stor

        model.Gen_Pstorage_constraint = pyo.Constraint(
            model.nodes_AC, rule=Gen_Pstorage_rule)

    if grid.H2:
        def Gen_Pelectrolyser_rule(model, node):
            nAC = grid.nodes_AC[node]
            p_el = sum(
                model.P_electrolyser[e.electrolyserNumber]
                for e in nAC.connected_electrolyser
            )
            return model.PGi_electrolyser[node] == p_el

        model.Gen_Pelectrolyser_constraint = pyo.Constraint(
            model.nodes_AC, rule=Gen_Pelectrolyser_rule)

    def _rs_gamma_lb(rs):
        ren_source = grid.RenSources[rs]
        if ren_source.curtailable:
            return float(ren_source.min_gamma)
        return 1.0

    def _rs_needs_y(rs):
        # gamma * np_rsgen is bilinear only when np_rsgen is a Var and gamma is free (min_gamma < 1).
        return grid.rs_GPR and _rs_gamma_lb(rs) < 1.0 - 1e-12

    y_rs_list = [rs for rs in model.ren_sources if _rs_needs_y(rs)]
    if y_rs_list:
        # y_rs replaces gamma * np_rsgen; valid only while gamma of these sources is used nowhere else.
        model.rs_y = pyo.Set(initialize=y_rs_list)
        model.y_rs = pyo.Var(model.rs_y, within=pyo.NonNegativeReals, initialize=0)

        def y_rs_lb_rule(model, rs):
            return model.y_rs[rs] >= _rs_gamma_lb(rs) * model.np_rsgen[rs]

        def y_rs_ub_rule(model, rs):
            return model.y_rs[rs] <= model.np_rsgen[rs]

        model.y_rs_lb = pyo.Constraint(model.rs_y, rule=y_rs_lb_rule)
        model.y_rs_ub = pyo.Constraint(model.rs_y, rule=y_rs_ub_rule)

    def Gen_PREN_rule(model,node):
       nAC = grid.nodes_AC[node]
       terms = []
       for rs in nAC.connected_RenSource:
           r = rs.rsNumber
           if _rs_needs_y(r):
               terms.append(model.P_renSource[r] * model.y_rs[r])
           elif grid.rs_GPR and _rs_gamma_lb(r) >= 1.0 - 1e-12:
               # gamma fixed at 1: skip the gamma product
               terms.append(model.P_renSource[r] * model.np_rsgen[r])
           else:
               terms.append(model.P_renSource[r] * model.gamma[r] * model.np_rsgen[r])
       P_gen = sum(terms)
       return  model.PGi_ren[node] ==   P_gen

    model.Gen_PREN_constraint =pyo.Constraint(model.nodes_AC, rule=Gen_PREN_rule)


    if grid.TEP_AC:
        from ..NL_models.ACDC_Static_TEP import get_TEP_variables
        _tep_vars = get_TEP_variables(grid)
        NP_lineAC_max = _tep_vars['ac_lines']['NP_lineAC_max']

        # Disjunctive per-circuit big-M linearisation of the integer x continuous
        # coupling NumLinesACP * exp_PAC_to. Parallel candidates are identical, so
        # each optional circuit j (beyond the base count) gets a build binary and
        # its own flow var that is forced to the reference flow exp_PAC_to when
        # built and to zero otherwise. Base circuits are carried linearly with the
        # (constant) base count.
        exp_K = {}
        exp_circuit_pairs = []
        for l in model.lines_AC_exp:
            element = grid.lines_AC_exp[l]
            K_l = int(round(NP_lineAC_max[l] - NP_lineAC[l])) if element.np_line_opf else 0
            if K_l < 0:
                K_l = 0
            exp_K[l] = K_l
            for j in range(1, K_l + 1):
                exp_circuit_pairs.append((l, j))

        model.exp_circuits = pyo.Set(dimen=2, initialize=exp_circuit_pairs)
        model.exp_build = pyo.Var(model.exp_circuits, domain=pyo.Binary, initialize=0)

        def exp_pcirc_bounds(model, l, j):
            return (-S_lineACexp_limit[l], S_lineACexp_limit[l])
        model.exp_p_to   = pyo.Var(model.exp_circuits, bounds=exp_pcirc_bounds, initialize=0)
        model.exp_p_from = pyo.Var(model.exp_circuits, bounds=exp_pcirc_bounds, initialize=0)

        # Symmetry breaking: build lower-indexed circuits first.
        def exp_order_rule(model, l, j):
            if (l, j + 1) in model.exp_circuits:
                return model.exp_build[l, j] >= model.exp_build[l, j + 1]
            return pyo.Constraint.Skip
        model.exp_order_con = pyo.Constraint(model.exp_circuits, rule=exp_order_rule)

        # Tie the build binaries to the integer line count.
        def exp_count_rule(model, l):
            return model.NumLinesACP[l] == NP_lineAC[l] + sum(model.exp_build[l, j] for j in range(1, exp_K[l] + 1))
        model.exp_count_con = pyo.Constraint(model.lines_AC_exp, rule=exp_count_rule)

        def exp_M(l):
            return 2.0 * S_lineACexp_limit[l]

        # Per-circuit flow: zero unless built (rating), and equal to the reference
        # flow when built (follow), enforced with big-M.
        def exp_p_to_rating_ub(model, l, j):
            return model.exp_p_to[l, j] <= S_lineACexp_limit[l] * model.exp_build[l, j]
        def exp_p_to_rating_lb(model, l, j):
            return model.exp_p_to[l, j] >= -S_lineACexp_limit[l] * model.exp_build[l, j]
        def exp_p_to_follow_ub(model, l, j):
            return model.exp_p_to[l, j] <= model.exp_PAC_to[l] + exp_M(l) * (1 - model.exp_build[l, j])
        def exp_p_to_follow_lb(model, l, j):
            return model.exp_p_to[l, j] >= model.exp_PAC_to[l] - exp_M(l) * (1 - model.exp_build[l, j])
        def exp_p_from_rating_ub(model, l, j):
            return model.exp_p_from[l, j] <= S_lineACexp_limit[l] * model.exp_build[l, j]
        def exp_p_from_rating_lb(model, l, j):
            return model.exp_p_from[l, j] >= -S_lineACexp_limit[l] * model.exp_build[l, j]
        def exp_p_from_follow_ub(model, l, j):
            return model.exp_p_from[l, j] <= model.exp_PAC_from[l] + exp_M(l) * (1 - model.exp_build[l, j])
        def exp_p_from_follow_lb(model, l, j):
            return model.exp_p_from[l, j] >= model.exp_PAC_from[l] - exp_M(l) * (1 - model.exp_build[l, j])

        model.exp_p_to_rating_ub_con   = pyo.Constraint(model.exp_circuits, rule=exp_p_to_rating_ub)
        model.exp_p_to_rating_lb_con   = pyo.Constraint(model.exp_circuits, rule=exp_p_to_rating_lb)
        model.exp_p_to_follow_ub_con   = pyo.Constraint(model.exp_circuits, rule=exp_p_to_follow_ub)
        model.exp_p_to_follow_lb_con   = pyo.Constraint(model.exp_circuits, rule=exp_p_to_follow_lb)
        model.exp_p_from_rating_ub_con = pyo.Constraint(model.exp_circuits, rule=exp_p_from_rating_ub)
        model.exp_p_from_rating_lb_con = pyo.Constraint(model.exp_circuits, rule=exp_p_from_rating_lb)
        model.exp_p_from_follow_ub_con = pyo.Constraint(model.exp_circuits, rule=exp_p_from_follow_ub)
        model.exp_p_from_follow_lb_con = pyo.Constraint(model.exp_circuits, rule=exp_p_from_follow_lb)

        def toPexp_rule(model, node):
            nAC = grid.nodes_AC[node]
            return model.Pto_Exp[node] == sum(
                NP_lineAC[l.lineNumber] * model.exp_PAC_to[l.lineNumber]
                + sum(model.exp_p_to[l.lineNumber, j] for j in range(1, exp_K[l.lineNumber] + 1))
                for l in nAC.connected_toExpLine)

        def fromPexp_rule(model, node):
            nAC = grid.nodes_AC[node]
            return model.Pfrom_Exp[node] == sum(
                NP_lineAC[l.lineNumber] * model.exp_PAC_from[l.lineNumber]
                + sum(model.exp_p_from[l.lineNumber, j] for j in range(1, exp_K[l.lineNumber] + 1))
                for l in nAC.connected_fromExpLine)

        model.exp_Pto_constraint  = pyo.Constraint(model.nodes_AC, rule=toPexp_rule)
        model.exp_Pfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromPexp_rule)


    def toPre_rule(model,node):
       nAC = grid.nodes_AC[node]
       toPre = sum(model.rec_z_to[l.lineNumber,0]+model.rec_z_to[l.lineNumber,1] for l in nAC.connected_toRepLine)
       return  model.Pto_REP[node] ==  toPre
    def fromPre_rule(model,node):
       nAC = grid.nodes_AC[node]
       fromPre = sum(model.rec_z_from[l.lineNumber,0]+model.rec_z_from[l.lineNumber,1] for l in nAC.connected_fromRepLine)
       return  model.Pfrom_REP[node] ==   fromPre


    if grid.REC_AC:
        model.rec_Pto_constraint  = pyo.Constraint(model.nodes_AC, rule=toPre_rule)
        model.rec_Pfrom_constraint= pyo.Constraint(model.nodes_AC, rule=fromPre_rule)

    # Fix the node constraints to use auxiliary variables:
    def toCT_rule_linear(model,node):
       nAC = grid.nodes_AC[node]
       toPre = 0
       for line in nAC.connected_toCTLine:
           for ct in model.ct_set:
               toPre += model.z_to[line.lineNumber,ct]  # ✅ Use z_to instead of bilinear term
       return model.Pto_CT[node] == toPre

    def fromCT_rule_linear(model,node):
       nAC = grid.nodes_AC[node]
       fromPre = 0
       for line in nAC.connected_fromCTLine:
           for ct in model.ct_set:
               fromPre += model.z_from[line.lineNumber,ct]  # ✅ Use z_from instead of bilinear term
       return model.Pfrom_CT[node] == fromPre


    def z_to_ub_rule(model, line, ct):
        M = calc_M_linear(model, line)
        return model.z_to[line, ct] <= model.ct_PAC_to[line, ct] + (1 - model.ct_branch[line, ct]) * (2*M)

    def z_to_lb_rule(model, line, ct):
        M = calc_M_linear(model, line)
        return model.z_to[line, ct] >= model.ct_PAC_to[line, ct] - (1 - model.ct_branch[line, ct]) * (2*M)

    def z_to_branch_ub_rule(model, line, ct):
        M_ct = S_lineACct_lim[line, ct]
        return model.z_to[line, ct] <= M_ct * model.ct_branch[line, ct]

    def z_to_branch_lb_rule(model, line, ct):
        M_ct = S_lineACct_lim[line, ct]
        return model.z_to[line, ct] >= -M_ct * model.ct_branch[line, ct]

    def z_from_ub_rule(model, line, ct):
        M = calc_M_linear(model, line)
        return model.z_from[line, ct] <= model.ct_PAC_from[line, ct] + (1 - model.ct_branch[line, ct]) * (2*M)

    def z_from_lb_rule(model, line, ct):
        M = calc_M_linear(model, line)
        return model.z_from[line, ct] >= model.ct_PAC_from[line, ct] - (1 - model.ct_branch[line, ct]) * (2*M)

    def z_from_branch_ub_rule(model, line, ct):
        M_ct = S_lineACct_lim[line, ct]
        return model.z_from[line, ct] <= M_ct * model.ct_branch[line, ct]

    def z_from_branch_lb_rule(model, line, ct):
        M_ct = S_lineACct_lim[line, ct]
        return model.z_from[line, ct] >= -M_ct * model.ct_branch[line, ct]

    def calc_M_linear(model, line):
        max_pow = max(S_lineACct_lim[line,ct] for ct in model.ct_set)
        return 1.1 * max_pow

    if grid.CT_AC:
        model.ct_Pto_constraint = pyo.Constraint(model.nodes_AC, rule=toCT_rule_linear)
        model.ct_Pfrom_constraint = pyo.Constraint(model.nodes_AC, rule=fromCT_rule_linear)

        # McCormick envelopes for z_to
        model.z_to_ub_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_to_ub_rule)
        model.z_to_lb_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_to_lb_rule)
        model.z_to_branch_ub_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_to_branch_ub_rule)
        model.z_to_branch_lb_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_to_branch_lb_rule)

        # McCormick envelopes for z_from
        model.z_from_ub_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_from_ub_rule)
        model.z_from_lb_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_from_lb_rule)
        model.z_from_branch_ub_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_from_branch_ub_rule)
        model.z_from_branch_lb_con = pyo.Constraint(model.lines_AC_ct, model.ct_set, rule=z_from_branch_lb_rule)

    # AC line equality constraints
    def calculate_P(model, line, direction,idx=None):
        f = line.fromNode.nodeNumber
        t = line.toNode.nodeNumber

        if idx is None:
            Ybus = line.Ybus_branch
        elif idx == 'new':
            Ybus = line.Ybus_branch_new
        else:
            Ybus = line.Ybus_list[idx]
        thf=model.theta_AC[f]
        tht=model.theta_AC[t]
        if direction == 'to':
            B = np.imag(Ybus[1,0])  # Btf
            P = -B * (tht - thf)
        else:  # 'from'
            B = np.imag(Ybus[0,1])  # Bft
            P = -B * (thf - tht)
        return P ,B


    def P_to_AC_line(model,line):
        l = grid.lines_AC[line]
        Pto,B = calculate_P(model,l,'to')
        return model.PAC_to[line] == Pto

    def P_from_AC_line(model,line):
       l = grid.lines_AC[line]
       Pfrom,B = calculate_P(model,l,'from')
       return model.PAC_from[line] == Pfrom


    model.Pto_AC_line_constraint   = pyo.Constraint(model.lines_AC, rule=P_to_AC_line)
    model.Pfrom_AC_line_constraint = pyo.Constraint(model.lines_AC, rule=P_from_AC_line)

    def P_to_AC_line_exp(model,line):
        l = grid.lines_AC_exp[line]
        Pto,B = calculate_P(model,l,'to')
        return model.exp_PAC_to[line] == Pto

    def P_from_AC_line_exp(model,line):
       l = grid.lines_AC_exp[line]
       Pfrom,B = calculate_P(model,l,'from')
       return model.exp_PAC_from[line] == Pfrom



    if grid.TEP_AC:
        model.exp_Pto_AC_line_constraint   = pyo.Constraint(model.lines_AC_exp, rule=P_to_AC_line_exp)
        model.exp_Pfrom_AC_line_constraint = pyo.Constraint(model.lines_AC_exp, rule=P_from_AC_line_exp)

    def P_to_AC_line_rec(model,line,state):
        l = grid.lines_AC_rec[line]
        if state ==  0:
            Pto,B = calculate_P(model,l,'to')
        else:
            Pto,B = calculate_P(model,l,'to',idx='new')
        return model.rec_PAC_to[line,state] == Pto

    def P_from_AC_line_rec(model,line,state):
       l = grid.lines_AC_rec[line]
       if state == 0:
           Pfrom,B = calculate_P(model,l,'from')
       else:
           Pfrom,B = calculate_P(model,l,'from',idx='new')
       return model.rec_PAC_from[line,state] == Pfrom



    if grid.REC_AC:

        model.rec_Pto_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=P_to_AC_line_rec)
        model.rec_Pfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_rec, model.branch_states, rule=P_from_AC_line_rec)

    def P_to_AC_line_ct(model,line,ct):
        l = grid.lines_AC_ct[line]
        Pto,B = calculate_P(model,l,'to',idx=ct)
        if l.active_config < 0:
            return model.ct_PAC_to[line,ct] == 0
        return model.ct_PAC_to[line,ct] == Pto

    def P_from_AC_line_ct(model,line,ct):
       l = grid.lines_AC_ct[line]
       Pfrom,B = calculate_P(model,l,'from',idx=ct)
       if l.active_config < 0:
            return model.ct_PAC_from[line,ct] == 0
       return model.ct_PAC_from[line,ct] == Pfrom

    def P_to_AC_line_ct_upper(model, line, ct):
        l = grid.lines_AC_ct[line]

        Pto,B = calculate_P(model, l, 'to', idx=ct)
        M = B * 3.1416
        return model.ct_PAC_to[line, ct] - Pto <= M * (1 - model.ct_branch[line, ct])

    def P_to_AC_line_ct_lower(model, line, ct):
        l = grid.lines_AC_ct[line]

        Pto,B = calculate_P(model, l, 'to', idx=ct)
        M = B * 3.1416
        return model.ct_PAC_to[line, ct] - Pto >= -M * (1 - model.ct_branch[line, ct])

    def P_from_AC_line_ct_upper(model, line, ct):
        l = grid.lines_AC_ct[line]

        Pfrom,B = calculate_P(model, l, 'from', idx=ct)
        M = B * 3.1416
        return model.ct_PAC_from[line, ct] - Pfrom <= M * (1 - model.ct_branch[line, ct])

    def P_from_AC_line_ct_lower(model, line, ct):
        l = grid.lines_AC_ct[line]

        Pfrom,B = calculate_P(model, l, 'from', idx=ct)
        M = B * 3.1416
        return model.ct_PAC_from[line, ct] - Pfrom >= -M * (1 - model.ct_branch[line, ct])


    if grid.CT_AC:

        model.ct_Pto_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=P_to_AC_line_ct)
        model.ct_Pfrom_AC_line_constraint = pyo.Constraint( model.lines_AC_ct, model.ct_set, rule=P_from_AC_line_ct)


    "AC inequality constraints"
    #AC gen inequality


    def calc_M_rec_linear(model, line):
        max_pow = max(S_lineACrec_lim[line], S_lineACrec_lim_new[line])
        return 1.1 * max_pow

    def S_to_AC_line_rule_rec_linear(model, line, state):
        M = calc_M_rec_linear(model, line)
        if state == 0:
            return model.rec_PAC_to[line, 0] <= S_lineACrec_lim[line] + M * model.rec_branch[line]
        else:
            return model.rec_PAC_to[line, 1] <= S_lineACrec_lim_new[line] + M * (1 - model.rec_branch[line])

    def S_to_AC_line_rule_rec_linear_neg(model, line, state):
        M = calc_M_rec_linear(model, line)
        if state == 0:
            return model.rec_PAC_to[line, 0] >= -S_lineACrec_lim[line] - M * model.rec_branch[line]
        else:
            return model.rec_PAC_to[line, 1] >= -S_lineACrec_lim_new[line] - M * (1 - model.rec_branch[line])

    def S_from_AC_limit_rule_rec_linear(model, line, state):
        M = calc_M_rec_linear(model, line)
        if state == 0:
            return model.rec_PAC_from[line, 0] <= S_lineACrec_lim[line] + M * model.rec_branch[line]
        else:
            return model.rec_PAC_from[line, 1] <= S_lineACrec_lim_new[line] + M * (1 - model.rec_branch[line])

    def S_from_AC_limit_rule_rec_linear_neg(model, line, state):
        M = calc_M_rec_linear(model, line)
        if state == 0:
            return model.rec_PAC_from[line, 0] >= -S_lineACrec_lim[line] - M * model.rec_branch[line]
        else:
            return model.rec_PAC_from[line, 1] >= -S_lineACrec_lim_new[line] - M * (1 - model.rec_branch[line])

    # McCormick/big-M envelopes tying rec_z to the flow of the active state.
    # State 1 is active when rec_branch == 1, state 0 when rec_branch == 0.
    def rec_state_active(model, line, state):
        return model.rec_branch[line] if state == 1 else (1 - model.rec_branch[line])

    def rec_state_rating(line, state):
        return S_lineACrec_lim_new[line] if state == 1 else S_lineACrec_lim[line]

    def rec_z_to_ub_rule(model, line, state):
        M = calc_M_rec_linear(model, line)
        return model.rec_z_to[line, state] <= model.rec_PAC_to[line, state] + (1 - rec_state_active(model, line, state)) * (2*M)

    def rec_z_to_lb_rule(model, line, state):
        M = calc_M_rec_linear(model, line)
        return model.rec_z_to[line, state] >= model.rec_PAC_to[line, state] - (1 - rec_state_active(model, line, state)) * (2*M)

    def rec_z_to_branch_ub_rule(model, line, state):
        return model.rec_z_to[line, state] <= rec_state_rating(line, state) * rec_state_active(model, line, state)

    def rec_z_to_branch_lb_rule(model, line, state):
        return model.rec_z_to[line, state] >= -rec_state_rating(line, state) * rec_state_active(model, line, state)

    def rec_z_from_ub_rule(model, line, state):
        M = calc_M_rec_linear(model, line)
        return model.rec_z_from[line, state] <= model.rec_PAC_from[line, state] + (1 - rec_state_active(model, line, state)) * (2*M)

    def rec_z_from_lb_rule(model, line, state):
        M = calc_M_rec_linear(model, line)
        return model.rec_z_from[line, state] >= model.rec_PAC_from[line, state] - (1 - rec_state_active(model, line, state)) * (2*M)

    def rec_z_from_branch_ub_rule(model, line, state):
        return model.rec_z_from[line, state] <= rec_state_rating(line, state) * rec_state_active(model, line, state)

    def rec_z_from_branch_lb_rule(model, line, state):
        return model.rec_z_from[line, state] >= -rec_state_rating(line, state) * rec_state_active(model, line, state)

    if grid.REC_AC:
        model.rec_S_to_AC_limit_constraint_upper = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_to_AC_line_rule_rec_linear)
        model.rec_S_to_AC_limit_constraint_lower = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_to_AC_line_rule_rec_linear_neg)
        model.rec_S_from_AC_limit_constraint_upper = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_from_AC_limit_rule_rec_linear)
        model.rec_S_from_AC_limit_constraint_lower = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=S_from_AC_limit_rule_rec_linear_neg)

        # McCormick envelopes for rec_z_to
        model.rec_z_to_ub_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_to_ub_rule)
        model.rec_z_to_lb_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_to_lb_rule)
        model.rec_z_to_branch_ub_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_to_branch_ub_rule)
        model.rec_z_to_branch_lb_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_to_branch_lb_rule)

        # McCormick envelopes for rec_z_from
        model.rec_z_from_ub_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_from_ub_rule)
        model.rec_z_from_lb_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_from_lb_rule)
        model.rec_z_from_branch_ub_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_from_branch_ub_rule)
        model.rec_z_from_branch_lb_con = pyo.Constraint(model.lines_AC_rec, model.branch_states, rule=rec_z_from_branch_lb_rule)



def DC_variables_l(model, grid, DC_info, TEP=False):
    """DC network variables for linear OPF (same shape as NL ``DC_variables``)."""
    DC_Lists, DC_nodes_info, DC_lines_info, DCDC_info = DC_info

    lista_nodos_DC, lista_lineas_DC, DC_slack, DC_nodes_connected_conv = DC_Lists
    u_min_dc, u_max_dc, V_ini_DC, P_known_DC, price_dc = DC_nodes_info
    P_lineDC_limit, NP_lineDC = DC_lines_info

    model.nodes_DC = pyo.Set(initialize=lista_nodos_DC)
    model.lines_DC = pyo.Set(initialize=lista_lineas_DC)
    model.DC_slacks = pyo.Set(initialize=DC_slack)
    # Fixed operating point for V(V-V)G linearization (H2).
    model.V_DC_ref = pyo.Param(model.nodes_DC, initialize=V_ini_DC, mutable=False)

    def DC_V_slack_rule(model, node):
        return model.V_DC[node] == V_ini_DC[node]

    def Pbounds_lines(model, line):
        if (not TEP) and grid.lines_DC[line].np_line <= 0:
            return (0, 0)
        return (-P_lineDC_limit[line], P_lineDC_limit[line])

    def P_conv_DC_node_bounds(model, node):
        if node in DC_nodes_connected_conv:
            return (None, None)
        return (0, 0)

    def Pren_bounds_DC(model, node):
        nDC = grid.nodes_DC[node]
        if not nDC.connected_RenSource:
            return (0, 0)
        return (None, None)

    model.V_DC = pyo.Var(
        model.nodes_DC,
        bounds=lambda model, node: (u_min_dc[node], u_max_dc[node]),
        initialize=V_ini_DC,
    )
    model.P_known_DC = pyo.Param(model.nodes_DC, initialize=P_known_DC, mutable=True)
    model.PGi_ren_DC = pyo.Var(model.nodes_DC, bounds=Pren_bounds_DC, initialize=0)

    if grid.ESS:
        def Pstorage_DC_bounds(model, node):
            nDC = grid.nodes_DC[node]
            if not nDC.connected_storage:
                return (0, 0)
            return (None, None)

        model.PGi_storage_DC = pyo.Var(
            model.nodes_DC, bounds=Pstorage_DC_bounds, initialize=0)

    if grid.H2:
        def Pelectrolyser_DC_bounds(model, node):
            nDC = grid.nodes_DC[node]
            if not nDC.connected_electrolyser:
                return (0, 0)
            return (None, None)

        model.PGi_electrolyser_DC = pyo.Var(
            model.nodes_DC, bounds=Pelectrolyser_DC_bounds, initialize=0)

    def PGi_opt_bounds_DC(model, node):
        nDC = grid.nodes_DC[node]
        if not nDC.connected_gen:
            return (0, 0)
        return (None, None)

    model.PGi_opt_DC = pyo.Var(model.nodes_DC, bounds=PGi_opt_bounds_DC, initialize=0)
    if DC_slack:
        model.DC_V_slack_constraint = pyo.Constraint(
            model.DC_slacks, rule=DC_V_slack_rule)

    model.PDC_to = pyo.Var(model.lines_DC, bounds=Pbounds_lines, initialize=0)
    model.PDC_from = pyo.Var(model.lines_DC, bounds=Pbounds_lines, initialize=0)
    model.PDC_line_loss = pyo.Var(model.lines_DC, bounds=Pbounds_lines, initialize=0)
    model.P_conv_DC = pyo.Var(
        model.nodes_DC, bounds=P_conv_DC_node_bounds, initialize=0)

    if grid.CDC:
        lista_DCDC, P_DCDC_limit, Pset_DCDC = DCDC_info

        def P_DCDC_bounds(model, node):
            nDC = grid.nodes_DC[node]
            if not nDC.connected_DCDC_to and not nDC.connected_DCDC_from:
                return (0, 0)
            return (None, None)

        def DCDC_opt_bounds(model, conv):
            return (-P_DCDC_limit[conv], P_DCDC_limit[conv])

        model.P_DCDC_to = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds, initialize=0)
        model.P_DCDC_from = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds, initialize=0)
        model.P_DCDC = pyo.Var(model.nodes_DC, bounds=P_DCDC_bounds, initialize=0)
        model.DCDC_conv = pyo.Set(initialize=lista_DCDC)
        model.cn_DCDC_from = pyo.Var(
            model.DCDC_conv, bounds=DCDC_opt_bounds, initialize=0)
        model.cn_DCDC_to = pyo.Var(
            model.DCDC_conv, bounds=DCDC_opt_bounds, initialize=0)
        model.CDC_loss = pyo.Var(model.DCDC_conv, initialize=0)


def DC_constraints_l(model, grid, DC_info, TEP=False):
    """Linearized DC PF: ``V_ref * (V_i - V_k) * G`` from NL ``DC_constraints``."""
    DC_Lists, DC_nodes_info, DC_lines_info, DCDC_info = DC_info
    u_min_dc, u_max_dc, V_ini_DC, P_known_DC, price_dc = DC_nodes_info

    def Gen_PREN_rule_DC(model, node):
        nDC = grid.nodes_DC[node]
        P_gen = sum(
            model.P_renSource[rs.rsNumber]
            * model.gamma[rs.rsNumber]
            * model.np_rsgen[rs.rsNumber]
            for rs in nDC.connected_RenSource
        )
        return model.PGi_ren_DC[node] == P_gen

    def Gen_P_rule_DC(model, node):
        nDC = grid.nodes_DC[node]
        P_gen = sum(
            model.PGi_gen_DC[gen.genNumber_DC] * model.np_gen_DC[gen.genNumber_DC]
            for gen in nDC.connected_gen
        )
        return model.PGi_opt_DC[node] == P_gen

    def P_DC_node_rule(model, node):
        i = node
        P_sum = 0
        for k in range(grid.nn_DC):
            Y = grid.Ybus_DC[i, k]
            if k != i and Y != 0:
                line = grid.get_lineDC_by_nodes(i, k)
                pol = line.pol
                G = 1 / line.r
                # Linearize NL: pol * V_i * (V_i - V_k) * G * NumLines
                # at V_ref,i = V_ini → pol * V_ref,i * (V_i - V_k) * G * NumLines
                P_sum += (
                    pol
                    * model.V_DC_ref[i]
                    * (model.V_DC[i] - model.V_DC[k])
                    * G
                    * model.NumLinesDCP[line.lineNumber]
                )

        P_var = (
            model.P_known_DC[node]
            + model.PGi_ren_DC[node]
            + model.PGi_opt_DC[node]
        )
        if grid.ESS:
            P_var += model.PGi_storage_DC[node]
        if grid.H2:
            P_var -= model.PGi_electrolyser_DC[node]
        if grid.ACmode:
            P_var += model.P_conv_DC[node]
        if grid.CDC:
            P_var += model.P_DCDC[node]
        return P_sum == P_var

    model.Gen_PREN_constraint_DC = pyo.Constraint(
        model.nodes_DC, rule=Gen_PREN_rule_DC)

    if grid.ESS:
        def Gen_Pstorage_DC_rule(model, node):
            nDC = grid.nodes_DC[node]
            p_stor = sum(
                model.P_storage_discharge[s.storageNumber]
                - model.P_storage_charge[s.storageNumber]
                for s in nDC.connected_storage
            )
            return model.PGi_storage_DC[node] == p_stor

        model.Gen_Pstorage_DC_constraint = pyo.Constraint(
            model.nodes_DC, rule=Gen_Pstorage_DC_rule)

    if grid.H2:
        def Gen_Pelectrolyser_DC_rule(model, node):
            nDC = grid.nodes_DC[node]
            p_el = sum(
                model.P_electrolyser[e.electrolyserNumber]
                for e in nDC.connected_electrolyser
            )
            return model.PGi_electrolyser_DC[node] == p_el

        model.Gen_Pelectrolyser_DC_constraint = pyo.Constraint(
            model.nodes_DC, rule=Gen_Pelectrolyser_DC_rule)

    model.Gen_P_constraint_DC = pyo.Constraint(model.nodes_DC, rule=Gen_P_rule_DC)
    model.P_DC_node_constraint = pyo.Constraint(model.nodes_DC, rule=P_DC_node_rule)

    def P_from_DC_line(model, line):
        l = grid.lines_DC[line]
        if (not TEP) and l.np_line <= 0:
            return pyo.Constraint.Skip
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        pol = l.pol
        G = 1 / l.r
        # NL: (V_f - V_t) * G * V_f * pol → (V_f - V_t) * G * V_ref_f * pol
        Pfrom = (model.V_DC[f] - model.V_DC[t]) * G * model.V_DC_ref[f] * pol
        return model.PDC_from[line] == Pfrom

    def P_to_DC_line(model, line):
        l = grid.lines_DC[line]
        if (not TEP) and l.np_line <= 0:
            return pyo.Constraint.Skip
        f = l.fromNode.nodeNumber
        t = l.toNode.nodeNumber
        pol = l.pol
        G = 1 / l.r
        Pto = (model.V_DC[t] - model.V_DC[f]) * G * model.V_DC_ref[t] * pol
        return model.PDC_to[line] == Pto

    def P_loss_DC_line_rule(model, line):
        if (not TEP) and grid.lines_DC[line].np_line <= 0:
            return pyo.Constraint.Skip
        return model.PDC_line_loss[line] == (
            model.PDC_from[line] + model.PDC_to[line]
        )

    model.Pfrom_DC_line_constraint = pyo.Constraint(
        model.lines_DC, rule=P_from_DC_line)
    model.Pto_DC_line_constraint = pyo.Constraint(model.lines_DC, rule=P_to_DC_line)
    model.Ploss_DC_line_constraint = pyo.Constraint(
        model.lines_DC, rule=P_loss_DC_line_rule)

    if grid.CDC:
        def P_DCDC_rule(model, node):
            return model.P_DCDC[node] == (
                model.P_DCDC_to[node] + model.P_DCDC_from[node]
            )

        def P_DCDC_to_rule(model, node):
            nDC = grid.nodes_DC[node]
            return model.P_DCDC_to[node] == sum(
                model.cn_DCDC_to[conv] for conv in nDC.connected_DCDC_to
            )

        def P_DCDC_from_rule(model, node):
            nDC = grid.nodes_DC[node]
            return model.P_DCDC_from[node] == sum(
                model.cn_DCDC_from[conv] for conv in nDC.connected_DCDC_from
            )

        def DCDC_relation_rule(model, conv):
            return (
                model.cn_DCDC_from[conv]
                + model.cn_DCDC_to[conv]
                + model.CDC_loss[conv]
                == 0
            )

        def DCDC_loss_rule(model, conv):
            # LP stage: drop NL (P/V)^2 * r quadratic loss.
            return model.CDC_loss[conv] == 0

        model.P_DCDC_rule = pyo.Constraint(model.nodes_DC, rule=P_DCDC_rule)
        model.P_DCDC_to_constraint = pyo.Constraint(
            model.nodes_DC, rule=P_DCDC_to_rule)
        model.P_DCDC_from_constraint = pyo.Constraint(
            model.nodes_DC, rule=P_DCDC_from_rule)
        model.DCDC_relation_constraint = pyo.Constraint(
            model.DCDC_conv, rule=DCDC_relation_rule)
        model.DCDC_loss_constraint = pyo.Constraint(
            model.DCDC_conv, rule=DCDC_loss_rule)


def Converter_variables_l(model, grid, Conv_info, TEP=False):
    """LP converter vars: AC-side ``P_conv_s_AC`` and nodal ``P_conv_AC`` only."""
    Conv_Lists, Conv_Volt = Conv_info
    lista_conv, np_conv = Conv_Lists
    _u_c_min, _u_c_max, S_limit_conv, _P_conv_limit = Conv_Volt

    model.conv = pyo.Set(initialize=lista_conv)

    def conv_opt_bounds(model, node):
        nAC = grid.nodes_AC[node]
        if not nAC.connected_conv:
            return (0, 0)
        return (None, None)

    def conv_power_bounds(model, conv):
        if (not TEP) and np_conv[conv] <= 0:
            return (0, 0)
        s = S_limit_conv[conv]
        return (-s, s)

    model.P_conv_AC = pyo.Var(
        model.nodes_AC, bounds=conv_opt_bounds, initialize=0)
    model.P_conv_s_AC = pyo.Var(
        model.conv, bounds=conv_power_bounds, initialize=0)


def Converter_constraints_l(model, grid, Conv_info, TEP=False):
    """One LP link: ``np·Ps + P_DC + np·(a + b·Ps) = 0``, plus AC nodal aggregate."""
    Conv_Lists, Conv_Volt = Conv_info
    lista_conv, np_conv = Conv_Lists

    def Conv_PAC_rule(model, node):
        nAC = grid.nodes_AC[node]
        return model.P_conv_AC[node] == sum(
            model.P_conv_s_AC[conv] * model.np_conv[conv]
            for conv in nAC.connected_conv
        )

    def Conv_Ps_PDC_rule(model, conv):
        element = grid.Converters_ACDC[conv]
        if (not TEP) and element.np_conv <= 0:
            return pyo.Constraint.Skip
        if element.power_loss_model == 'MMC':
            raise ValueError(
                "Linear OPF does not support MMC converter loss "
                f"(converter {conv})"
            )
        nDC = element.Node_DC.nodeNumber
        a = float(element.a_conv)
        b = float(element.b_conv)
        Ps = model.P_conv_s_AC[conv]
        # np·Ps + P_DC + np·(a + b·Ps) = 0
        return (
            model.np_conv[conv] * Ps
            + model.P_conv_DC[nDC]
            + model.np_conv[conv] * (a + b * Ps)
            == 0
        )

    model.Conv_PAC_constraint = pyo.Constraint(model.nodes_AC, rule=Conv_PAC_rule)
    model.Conv_Ps_PDC_constraint = pyo.Constraint(model.conv, rule=Conv_Ps_PDC_rule)



def TEP_parameters(model,grid):



    from ..NL_models.ACDC_Static_TEP import get_TEP_variables

    tep_vars = get_TEP_variables(grid)

    # Extract AC line variables
    NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
    REC_branch = tep_vars['ac_lines']['REC_branch']
    ct_ini = tep_vars['ac_lines']['ct_ini']

    # Extract generator variables
    np_gen = tep_vars['generators']['np_gen']
    np_gen_DC = tep_vars['generators']['np_gen_DC']
    np_rsgen = tep_vars['ren_sources']['np_rsgen']
    NP_lineDC = tep_vars['dc_lines']['NP_lineDC']
    np_conv = tep_vars['converters']['np_conv']

    model.np_rsgen = pyo.Param(model.ren_sources,initialize=np_rsgen,mutable=True)
    if grid.ACmode:
        model.np_gen = pyo.Param(model.gen_AC,initialize=np_gen)
        if grid.TEP_AC:
            model.NumLinesACP = pyo.Param(model.lines_AC_exp ,initialize=NP_lineAC)

        if grid.REC_AC:
            model.rec_branch = pyo.Param(model.lines_AC_rec,initialize=REC_branch)

        if grid.CT_AC:
            model.ct_branch = pyo.Param(model.lines_AC_ct,model.ct_set,initialize=ct_ini)

    if grid.DCmode:
        model.np_gen_DC = pyo.Param(model.gen_DC, initialize=np_gen_DC, mutable=True)
        model.NumLinesDCP = pyo.Param(model.lines_DC, initialize=NP_lineDC, mutable=True)

    if grid.ACmode and grid.DCmode:
        model.np_conv = pyo.Param(model.conv, initialize=np_conv, mutable=True)




def TEP_variables(model,grid):

    from ..NL_models.ACDC_Static_TEP import get_TEP_variables
    from ..grid_analysis import get_gen_p_min_eff

    tep_vars = get_TEP_variables(grid)


    # Extract AC line variables
    NP_lineAC = tep_vars['ac_lines']['NP_lineAC']
    NP_lineAC_model_first_guess = tep_vars['ac_lines']['NP_lineAC_model_first_guess']
    NP_lineAC_max = tep_vars['ac_lines']['NP_lineAC_max']
    REC_branch = tep_vars['ac_lines']['REC_branch']
    ct_ini = tep_vars['ac_lines']['ct_ini']

    # Extract generator variables
    np_gen = tep_vars['generators']['np_gen']
    np_gen_max = tep_vars['generators']['np_gen_max']

    np_rsgen = tep_vars['ren_sources']['np_rsgen']
    np_rsgen_model_first_guess = tep_vars['ren_sources']['np_rsgen_model_first_guess']
    np_rsgen_max = tep_vars['ren_sources']['np_rsgen_max']


    "TEP variables"

    if grid.rs_GPR:
        def np_rsgen_bounds(model,rs):
            ren_source = grid.RenSources[rs]
            if ren_source.np_rsgen_mp:
                return (0, np_rsgen_max[rs])
            elif ren_source.np_rsgen_opf:
                return (np_rsgen[rs], np_rsgen_max[rs])
            else:
                return (np_rsgen[rs], np_rsgen[rs])
        model.np_rsgen = pyo.Var(
            model.ren_sources,
            within=pyo.NonNegativeIntegers,
            bounds=np_rsgen_bounds,
            initialize=np_rsgen_model_first_guess,
        )
        model.np_rsgen_base = pyo.Param(model.ren_sources,initialize=np_rsgen)
    else:
        model.np_rsgen = pyo.Param(model.ren_sources,initialize=np_rsgen)

    def np_gen_bounds(model,gen):
        g = grid.Generators[gen]
        if g.np_gen_mp:
            return (0, np_gen_max[gen])
        elif g.np_gen_opf:
            return (np_gen[gen], np_gen_max[gen])
        else:
            return (np_gen[gen], np_gen[gen])

    if grid.GPR:

        def P_gen_lower_bound_rule(model, gen):
            g = grid.Generators[gen]
            p_load_eff = model.P_load_eff[gen]
            return (get_gen_p_min_eff(g, model.np_gen[gen], p_load_eff) <= model.PGi_gen[gen])

        def P_gen_upper_bound_rule(model, gen):
            g = grid.Generators[gen]
            return (model.PGi_gen[gen] <= g.Max_pow_gen * model.np_gen[gen])



        model.np_gen = pyo.Var(
            model.gen_AC,
            within=pyo.NonNegativeIntegers,
            bounds=np_gen_bounds,
            initialize=tep_vars['generators']['np_gen_model_first_guess'],
        )
        model.np_gen_base = pyo.Param(model.gen_AC,initialize=np_gen)

        model.PGi_lower_bound = pyo.Constraint(model.gen_AC,rule=P_gen_lower_bound_rule)
        model.PGi_upper_bound = pyo.Constraint(model.gen_AC,rule=P_gen_upper_bound_rule)


    else:
        model.np_gen = pyo.Param(model.gen_AC,initialize=np_gen)


    if grid.TEP_AC:
        def NPline_bounds_AC(model, line):
            element=grid.lines_AC_exp[line]
            if not element.np_line_opf:
                return (NP_lineAC[line], NP_lineAC[line])
            else:
                return (NP_lineAC[line], NP_lineAC_max[line])

        model.NumLinesACP = pyo.Var(model.lines_AC_exp, within=pyo.NonNegativeIntegers,bounds=NPline_bounds_AC,initialize=NP_lineAC_model_first_guess)
        model.NumLinesACP_base  =pyo.Param(model.lines_AC_exp,initialize=NP_lineAC)

    if grid.REC_AC:
        model.rec_branch = pyo.Var(model.lines_AC_rec,domain=pyo.Binary,initialize=REC_branch)

    if grid.CT_AC:
        used_cable_types = set()
        for l in grid.lines_AC_ct:
            if l.active_config >= 0:  # If line has an active configuration
                used_cable_types.add(l.active_config)
        model.ct_branch = pyo.Var(model.lines_AC_ct,model.ct_set,domain=pyo.Binary,initialize=ct_ini)
        # Initialize ct_types with 1 for used cable types, 0 otherwise
        ct_types_ini = {ct: 1 if ct in used_cable_types else 0 for ct in model.ct_set}
        model.ct_types = pyo.Var(model.ct_set,domain=pyo.Binary,initialize=ct_types_ini)


def export_acdc_l_model_to_pyflow_acdc(model,grid, solver_results=None, tee=False):
    """Export a solved linear OPF Pyomo model back onto ``grid``.

    Called by :func:`~pyflow_acdc.optimal_l_pf` after solving. Updates generator
    dispatch, AC angles, line flows, optional AC BESS / electrolyser setpoints,
    and optional TEP/REC/CT selections on ``grid``.

    Parameters
    ----------
    model : pyomo.ConcreteModel
        Solved linear OPF model.
    grid : Grid
        Network to update (mutated in place).
    solver_results : optional
        Pyomo solver results (used for time-limit post-processing).
    tee : bool, optional
        Print diagnostic output during export.

    Examples
    --------
    >>> export_acdc_l_model_to_pyflow_acdc(model, grid, solver_results=results, tee=True)
    """

    grid.OPF_run=True

    #Generation
    if grid.ACmode:
        PGen_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_gen.items()}
        QGen_values = {k: 0.0 for k in PGen_values.keys()}
        for gen in grid.Generators:
            gen.PGen = PGen_values[gen.genNumber]
            gen.QGen = QGen_values[gen.genNumber]

    if grid.DCmode:
        PGen_DC_values = {
            k: np.float64(pyo.value(v)) for k, v in model.PGi_gen_DC.items()}
        for gen in grid.Generators_DC:
            gen.PGen = PGen_DC_values[gen.genNumber_DC]

    gamma_values = {k: np.float64(pyo.value(v)) for k, v in model.gamma.items()}
    if hasattr(model, 'rs_y'):
        for rs in model.rs_y:
            n_rs = round(pyo.value(model.np_rsgen[rs]))
            # With no installed units there is nothing to curtail.
            gamma_values[rs] = np.float64(pyo.value(model.y_rs[rs]) / n_rs) if n_rs > 0 else np.float64(1.0)
    Qren_values  = {k: 0.0 for k in gamma_values.keys()}
    for rs in grid.RenSources:
        rs.gamma = gamma_values[rs.rsNumber]
        rs.QGi_ren = Qren_values[rs.rsNumber]

    if grid.ACmode:
        #AC bus
        grid.V_AC = np.ones(grid.nn_AC)
        grid.Theta_V_AC = np.zeros(grid.nn_AC)

        theta_AC_values = {k: np.float64(pyo.value(v)) for k, v in model.theta_AC.items()}
        V_AC_values     = {k: 1.0 for k in theta_AC_values.keys()}
        PGi_opt_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_opt.items()}
        QGi_opt_values  = {k: 0.0 for k in PGi_opt_values.keys()}
        PGi_ren_values  = {k: np.float64(pyo.value(v)) for k, v in model.PGi_ren.items()}
        QGi_ren_values  = {k: 0.0 for k in PGi_ren_values.keys()}

        def process_node_AC(node):
            nAC = node.nodeNumber
            node.V = V_AC_values[nAC]
            node.theta = theta_AC_values[nAC]

            node.PGi_opt = PGi_opt_values[nAC]
            node.QGi_opt = QGi_opt_values[nAC]
            node.PGi_ren = PGi_ren_values[nAC]
            node.QGi_ren = QGi_ren_values[nAC]

            grid.Theta_V_AC[nAC] = node.theta

        with ThreadPoolExecutor() as executor:
            executor.map(process_node_AC, grid.nodes_AC)

    if grid.ESS:
        P_charge = {
            k: np.float64(pyo.value(v)) for k, v in model.P_storage_charge.items()}
        P_discharge = {
            k: np.float64(pyo.value(v)) for k, v in model.P_storage_discharge.items()}
        Q_storage = {
            k: np.float64(pyo.value(v)) for k, v in model.Q_storage.items()}
        soc = {k: np.float64(pyo.value(v)) for k, v in model.SoC.items()}
        for storage in grid.storage_elements:
            s = storage.storageNumber
            storage.P_charge = P_charge[s]
            storage.P_discharge = P_discharge[s]
            storage.Q = Q_storage[s]
            storage.SoC = soc[s]

    if grid.H2:
        P_e_values = {
            k: np.float64(pyo.value(v)) for k, v in model.P_electrolyser.items()}
        mass_h2_values = {
            k: np.float64(pyo.value(v)) for k, v in model.mass_H2.items()}
        for el in grid.electrolysers:
            e = el.electrolyserNumber
            el.P_electrolyser = P_e_values[e]
            el.Q_electrolyser = 0.0
            el.mass_H2 = mass_h2_values[e]

    if grid.ACmode:
        B = np.imag(grid.Ybus_AC)
        Theta = grid.Theta_V_AC

        Theta_diff = Theta[:, None] - Theta
        Pf_AC = (-B * Theta_diff).sum(axis=1)

        for node in grid.nodes_AC:
            i = node.nodeNumber
            node.P_INJ = Pf_AC[i]
            node.Q_INJ = 0.0

    if grid.DCmode:
        grid.V_DC = np.zeros(grid.nn_DC)
        V_DC_values = {k: np.float64(pyo.value(v)) for k, v in model.V_DC.items()}
        if grid.ACmode:
            P_conv_DC_values = {
                k: np.float64(pyo.value(v)) for k, v in model.P_conv_DC.items()}
        if grid.CDC:
            P_DCDC_values = {
                k: np.float64(pyo.value(v)) for k, v in model.P_DCDC.items()}

        def process_node_DC(node):
            nDC = node.nodeNumber
            node.V = V_DC_values[nDC]
            grid.V_DC[nDC] = node.V
            if grid.ACmode:
                node.Pconv = P_conv_DC_values[nDC]
            if grid.CDC:
                node.PconvDC = P_DCDC_values[nDC]
            node.P_INJ = node.PGi - node.PLi + node.Pconv + node.PconvDC

        with ThreadPoolExecutor() as executor:
            executor.map(process_node_DC, grid.nodes_DC)

        if grid.CDC:
            P_DCDC_to_values = {
                k: np.float64(pyo.value(v)) for k, v in model.cn_DCDC_to.items()}
            P_DCDC_from_values = {
                k: np.float64(pyo.value(v)) for k, v in model.cn_DCDC_from.items()}
            P_DCDC_loss_values = {
                k: np.float64(pyo.value(v)) for k, v in model.CDC_loss.items()}
            for conv in grid.Converters_DCDC:
                conv.Powerto = P_DCDC_to_values[conv.ConvNumber]
                conv.Powerfrom = P_DCDC_from_values[conv.ConvNumber]
                conv.loss = P_DCDC_loss_values[conv.ConvNumber]

        grid.line_dc_calc()

    if grid.ACmode and grid.DCmode:
        P_conv_s_AC_values = {
            k: np.float64(pyo.value(v)) for k, v in model.P_conv_s_AC.items()}
        theta_AC_values = {
            k: np.float64(pyo.value(v)) for k, v in model.theta_AC.items()}

        for conv in grid.Converters_ACDC:
            nconv = conv.ConvNumber
            Ps = P_conv_s_AC_values[nconv]
            loss_pu = float(conv.a_conv) + float(conv.b_conv) * Ps
            conv.P_AC = Ps * conv.np_conv
            conv.Q_AC = 0.0
            conv.Pc = conv.P_AC
            conv.Qc = 0.0
            conv.P_loss = loss_pu * conv.np_conv
            conv.P_DC = -(conv.Pc + conv.P_loss)
            conv.P_loss_tf = 0.0
            conv.U_c = 1.0
            conv.U_f = 1.0
            conv.U_s = 1.0
            conv.th_c = 0.0
            conv.th_f = 0.0
            conv.th_s = theta_AC_values[conv.Node_AC.nodeNumber]

    if grid.GPR:
        np_gen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_gen.items()}
        for gen in grid.Generators:
            gen.np_gen = np_gen_values[gen.genNumber]

    if grid.rs_GPR:
        np_rsgen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_rsgen.items()}
        for rs in grid.RenSources:
            rs.np_rsgen = np_rsgen_values[rs.rsNumber]

    if grid.TEP_AC:
        lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}
        lines_AC_TEP_fromP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_from.items()}
        lines_AC_TEP_toP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_to.items()}
        lines_AC_TEP_fromQ = {k: 0.0 for k in lines_AC_TEP_fromP.keys()}
        lines_AC_TEP_toQ = {k: 0.0 for k in lines_AC_TEP_toP.keys()}
        lines_AC_TEP_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_line_loss.items()}

        def process_line_AC_TEP(line):
            l = line.lineNumber
            line.np_line = lines_AC_TEP[l]
            line.P_loss = lines_AC_TEP_P_loss[l]*lines_AC_TEP[l]
            line.fromS = (lines_AC_TEP_fromP[l] + 1j*lines_AC_TEP_fromQ[l])*lines_AC_TEP[l]
            line.toS = (lines_AC_TEP_toP[l] + 1j*lines_AC_TEP_toQ[l])*lines_AC_TEP[l]
            line.loss = line.fromS + line.toS

        with ThreadPoolExecutor() as executor:
            executor.map(process_line_AC_TEP, grid.lines_AC_exp)

    if grid.REC_AC:
        lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in model.rec_branch.items()}
        lines_AC_REC_fromP = {k: {state: np.float64(pyo.value(model.rec_PAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
        lines_AC_REC_toP = {k: {state: np.float64(pyo.value(model.rec_PAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
        lines_AC_REC_fromQ = {k: {state: 0.0 for state in model.branch_states} for k in model.lines_AC_rec}
        lines_AC_REC_toQ = {k: {state: 0.0 for state in model.branch_states} for k in model.lines_AC_rec}
        lines_AC_REC_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.rec_PAC_line_loss.items()}


        def process_line_AC_REP(line):
            l = line.lineNumber
            line.rec_branch = True if lines_AC_REP[l] >= BINARY_THRESHOLD else False
            line.P_loss = lines_AC_REC_P_loss[l]
            state = 1 if line.rec_branch else 0
            line.fromS = (lines_AC_REC_fromP[l][state] + 1j*lines_AC_REC_fromQ[l][state])
            line.toS = (lines_AC_REC_toP[l][state] + 1j*lines_AC_REC_toQ[l][state])
            line.loss = line.fromS + line.toS

        with ThreadPoolExecutor() as executor:
            executor.map(process_line_AC_REP, grid.lines_AC_rec)

    if grid.CT_AC:
        lines_AC_CT = {k: {ct: np.float64(pyo.value(model.ct_branch[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
        lines_AC_CT_fromP = {k: {ct: np.float64(pyo.value(model.ct_PAC_from[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
        lines_AC_CT_toP = {k: {ct: np.float64(pyo.value(model.ct_PAC_to[k, ct])) for ct in model.ct_set} for k in model.lines_AC_ct}
        gen_active_config = {k: np.float64(pyo.value(model.ct_types[k])) for k in model.ct_set}

        grid.Cable_options[0].active_config = gen_active_config

        def process_line_AC_CT(line):
            l = line.lineNumber
            ct_selected = [lines_AC_CT[l][ct] >= CT_SELECTION_THRESHOLD  for ct in model.ct_set]
            if any(ct_selected):
                line.active_config = np.where(ct_selected)[0][0]
                ct = list(model.ct_set)[line.active_config]
                Pfrom = lines_AC_CT_fromP[l][ct]
                Pto   = lines_AC_CT_toP[l][ct]
                Qfrom = 0.0
                Qto   = 0.0
            else:
                line.active_config = -1
                Pfrom = 0
                Pto   = 0
                Qfrom = 0
                Qto   = 0

            line.fromS = (Pfrom + 1j*Qfrom)
            line.toS = (Pto + 1j*Qto)
            line.loss = 0
            line.P_loss = 0

        with ThreadPoolExecutor() as executor:
            executor.map(process_line_AC_CT, grid.lines_AC_ct)

     # After export is complete, analyze and fix oversizing issues if time limit was reached
    if solver_results is not None:
        # Check for time limit termination in Pyomo
        termination_condition = str(solver_results.solver.termination_condition).lower()

        if 'timelimit' in termination_condition:
            if tee:
                print("Time limit reached. Analyzing potential oversizing issues...")

            # Apply oversizing analysis and fixes
            oversizing_type1, oversizing_type2 = analyze_oversizing_issues_grid(grid, tee=tee)
            apply_oversizing_fixes_grid(grid, oversizing_type1, oversizing_type2, tee=tee)
    # --- Step 1: Use voltage angles only ---
    Theta = grid.Theta_V_AC  # should be a 1D array with angle values in radians

    # --- Step 2: Iterate over lines and compute power flows ---
    for line in grid.lines_AC:
        i = line.fromNode.nodeNumber
        j = line.toNode.nodeNumber

        # Susceptance from Ybus (assuming purely imaginary admittance)
        B = -np.imag(line.Ybus_branch[0, 1])  # or [1,0] — symmetric for passive branches

        # Active power flow from i to j (DC approximation)
        P_ij = B * (Theta[i] - Theta[j])
        P_ji = B * (Theta[j] - Theta[i])

        # Store active powers
        line.fromP = P_ij
        line.toP = P_ji
        line.toS = P_ji + 1j*0
        line.fromS = P_ij + 1j*0
        # Loss is zero in DC model
        line.P_loss = 0
        line.loss = 0

        # Approximate current magnitude (linearized)
        line.i_from = abs(P_ij)  # or just set = P_ij if signed current
        line.i_to = abs(P_ji)


def analyze_oversizing_issues_grid(grid, tee=True):
    """
    Analyze potential oversizing issues due to time limits by comparing
    active configurations with network flow values.

    Args:
        grid: Grid object with exported results
        tee: Boolean to control printing output (default: True)

    Returns two types of oversizing issues:
    1. Lines with lower flow but higher active config than other lines
    2. Lines with same flow but different active configs
    """

    if tee:
        print("\n=== OVERSIZING ANALYSIS DUE TO TIME LIMIT ===")

    # Get active lines and their data
    active_lines_data = []

    for line in grid.lines_AC_ct:
        # Check if line is active (has a selected cable type)
        if  line.active_config >= 0:
            network_flow = getattr(line, 'network_flow', None)
            if network_flow is None:
                network_flow = 0.0

            active_lines_data.append({
                'line_number': line.lineNumber,
                'from_node': line.fromNode.nodeNumber,
                'to_node': line.toNode.nodeNumber,
                'active_config': line.active_config,
                'network_flow': network_flow,
                'cable_type': f"Config_{line.active_config}"
            })

    if not active_lines_data:
        if tee:
            print("No active lines found for analysis")
        return [], []

    # Sort by network flow for easier analysis
    active_lines_data.sort(key=lambda x: x['network_flow'])

    if tee:
        print(f"\nActive lines summary:")
        print(f"{'Line':<6} {'From':<6} {'To':<6} {'Flow':<8} {'Config':<8} {'Cable Type':<12}")
        print("-" * 50)
        for line_data in active_lines_data:
            print(f"{line_data['line_number']:<6} {line_data['from_node']:<6} {line_data['to_node']:<6} "
                  f"{line_data['network_flow']:<8.2f} {line_data['active_config']:<8} {line_data['cable_type']:<12}")

    # Analysis 1: Check for lines with lower flow but higher config than others
    if tee:
        print(f"\n=== ANALYSIS 1: Lower flow with higher config ===")
    oversizing_type1 = []
    oversized_lines_type1 = set()  # Track lines already identified as oversized

    for i, line1 in enumerate(active_lines_data):
        if line1['line_number'] in oversized_lines_type1:
            continue  # Skip if already identified

        best_reference = None
        max_config_difference = 0

        for j, line2 in enumerate(active_lines_data):
            if i != j:
                # Check if line1 has lower flow but higher config than line2
                if (line1['network_flow'] < line2['network_flow'] and
                    line1['active_config'] > line2['active_config']):

                    config_difference = line1['active_config'] - line2['active_config']
                    if config_difference > max_config_difference:
                        max_config_difference = config_difference
                        best_reference = line2

        # Add the biggest oversizing issue for this line
        if best_reference is not None:
            oversizing_type1.append({
                'oversized_line': line1,
                'reference_line': best_reference,
                'flow_difference': best_reference['network_flow'] - line1['network_flow'],
                'config_difference': max_config_difference
            })
            oversized_lines_type1.add(line1['line_number'])

    if oversizing_type1 and tee:
        print("Found potential oversizing issues (Type 1):")
        for issue in oversizing_type1:
            print(f"  Line {issue['oversized_line']['line_number']} (flow: {issue['oversized_line']['network_flow']:.2f}, "
                  f"config: {issue['oversized_line']['active_config']}) may be oversized compared to "
                  f"Line {issue['reference_line']['line_number']} (flow: {issue['reference_line']['network_flow']:.2f}, "
                  f"config: {issue['reference_line']['active_config']})")
            print(f"    → Line {issue['oversized_line']['line_number']} could use config {issue['reference_line']['active_config']} "
                  f"to handle flow {issue['oversized_line']['network_flow']:.2f}")
    elif tee:
        print("No Type 1 oversizing issues found")

    # Analysis 2: Check for lines with same flow but different configs
    if tee:
        print(f"\n=== ANALYSIS 2: Same flow with different configs ===")
    oversizing_type2 = []
    oversized_lines_type2 = set()  # Track lines already identified as oversized

    for i, line1 in enumerate(active_lines_data):
        if line1['line_number'] in oversized_lines_type2:
            continue  # Skip if already identified

        best_reference = None
        max_config_difference = 0

        for j, line2 in enumerate(active_lines_data):
            if i != j:
                # Check if lines have similar flow but different configs
                flow_tolerance = 0.1  # Allow small differences in flow
                if (abs(line1['network_flow'] - line2['network_flow']) <= flow_tolerance and
                    line1['active_config'] != line2['active_config']):

                    # Determine which line might be oversized (higher config = oversized)
                    if line1['active_config'] > line2['active_config']:
                        config_difference = line1['active_config'] - line2['active_config']
                        if config_difference > max_config_difference:
                            max_config_difference = config_difference
                            best_reference = line2

        # Add the biggest oversizing issue for this line
        if best_reference is not None:
            oversizing_type2.append({
                'oversized_line': line1,
                'reference_line': best_reference,
                'flow_value': (line1['network_flow'] + best_reference['network_flow']) / 2
            })
            oversized_lines_type2.add(line1['line_number'])

    if oversizing_type2 and tee:
        print("Found potential oversizing issues (Type 2):")
        for issue in oversizing_type2:
            print(f"  Line {issue['oversized_line']['line_number']} (flow: {issue['oversized_line']['network_flow']:.2f}, "
                  f"config: {issue['oversized_line']['active_config']}) may be oversized compared to "
                  f"Line {issue['reference_line']['line_number']} (flow: {issue['reference_line']['network_flow']:.2f}, "
                  f"config: {issue['reference_line']['active_config']})")
            print(f"    → Both lines handle similar flow ({issue['flow_value']:.2f}) but line {issue['oversized_line']['line_number']} "
                  f"uses higher config {issue['oversized_line']['active_config']} vs {issue['reference_line']['active_config']}")
    elif tee:
        print("No Type 2 oversizing issues found")

    # Summary
    total_issues = len(oversizing_type1) + len(oversizing_type2)
    if total_issues > 0 and tee:
        print(f"\n=== SUMMARY ===")
        print(f"Total potential oversizing issues found: {total_issues}")
        print(f"  - Type 1 (lower flow, higher config): {len(oversizing_type1)}")
        print(f"  - Type 2 (same flow, different configs): {len(oversizing_type2)}")
        print(f"\nRecommendation: Consider increasing time limit or adjusting cable type constraints")
    elif tee:
        print(f"\nNo oversizing issues detected. Solution appears consistent.")

    return oversizing_type1, oversizing_type2


def apply_oversizing_fixes_grid(grid, oversizing_type1, oversizing_type2, tee=True):
    """
    Apply fixes to the grid results based on oversizing analysis.
    Changes the active configurations of oversized lines to use lower configs.
    """
    if not oversizing_type1 and not oversizing_type2:
        if tee:
            print("No oversizing issues to fix.")
        return

    if tee:
        print("\n=== APPLYING OVERSIZING FIXES ===")

    fixes_applied = []
    fixed_lines = set()  # Track which lines have already been fixed

    # Apply Type 1 fixes (lower flow, higher config) - these take priority
    for issue in oversizing_type1:
        oversized_line_num = issue['oversized_line']['line_number']
        target_config = issue['reference_line']['active_config']

        # Find the line object
        for line in grid.lines_AC_ct:
            if line.lineNumber == oversized_line_num:
                old_config = line.active_config
                line.active_config = target_config


                fixes_applied.append({
                    'line_number': oversized_line_num,
                    'old_config': old_config,
                    'new_config': target_config,
                    'type': 'Type 1',
                    'flow': issue['oversized_line']['network_flow']
                })
                fixed_lines.add(oversized_line_num)  # Mark as fixed
                break

    # Apply Type 2 fixes (same flow, different configs) - only for lines not already fixed
    for issue in oversizing_type2:
        oversized_line_num = issue['oversized_line']['line_number']

        # Skip if this line was already fixed in Type 1
        if oversized_line_num in fixed_lines:
            continue

        target_config = issue['reference_line']['active_config']

        # Find the line object
        for line in grid.lines_AC_ct:
            if line.lineNumber == oversized_line_num:
                old_config = line.active_config
                line.active_config = target_config

                fixes_applied.append({
                    'line_number': oversized_line_num,
                    'old_config': old_config,
                    'new_config': target_config,
                    'type': 'Type 2',
                    'flow': issue['oversized_line']['network_flow']
                })
                fixed_lines.add(oversized_line_num)  # Mark as fixed
                break

    if fixes_applied and tee:
        print("Applied the following fixes:")
        print(f"{'Line':<6} {'Old Config':<12} {'New Config':<12} {'Type':<8} {'Flow':<8}")
        print("-" * 50)
        for fix in fixes_applied:
            print(f"{fix['line_number']:<6} {fix['old_config']:<12} {fix['new_config']:<12} "
                  f"{fix['type']:<8} {fix['flow']:<8.2f}")

        print(f"\nTotal fixes applied: {len(fixes_applied)}")
        print("Note: These changes may affect the objective value and solution optimality.")
        print("Note: Power flow values may need recalculation after config changes.")

    return fixes_applied
