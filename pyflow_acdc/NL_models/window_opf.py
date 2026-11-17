# -*- coding: utf-8 -*-
"""Coupled window NL OPF with BESS and electrolyser (frame blocks + parent links)."""

import math
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from ..ACDC_OPF import (
    calculate_objective,
    fx_conv,
    obj_w_rule,
    opf_obj,
    translate_pyf_opf,
)
from .ACDC_OPF_NL_model import export_acdc_nl_model_to_pyflow_acdc, opf_create_nl_model_acdc
from ..constants import AcDcSide
from ..grid_analysis import analyse_grid
from ..pyomo_model_solve import (
    build_only_solver_stats,
    pyomo_model_solve,
    reset_to_initialize,
)
from ..Time_series import (
    _calculate_line_loading_from_model,
    _modify_parameters,
    update_grid_data,
)

__all__ = ['window_nl_opf', 'rolling_window_nl_opf']


def _sum_frame_objectives(model, frames):
    total = 0
    for t in frames:
        total += model.frame_model[t].obj.expr
        model.frame_model[t].obj.deactivate()
    return total


def _soc_delta_expr(eta_charge, eta_discharge, E_max, dt_hours, S_base, block, s):
    scale = dt_hours[s] * S_base[s] / E_max[s]
    return scale * (
        eta_charge[s] * block.P_storage_charge[s]
        - block.P_storage_discharge[s] / eta_discharge[s]
    )


def window_soc_constraints(model, grid, storage_info, frames, *, enforce_final=True):
    """Parent-level SoC chain across ``frame_model`` blocks.

    ``soc_initial`` / ``soc_final`` are mutable ``Param``s so rolling can
    ``set_value`` without rebuilding constraints.
    """
    ordered = list(frames)
    _lim, storage_soc, storage_phys, lista_storage = storage_info
    soc_min_st, soc_max_st, soc_initial, _soc_ref, soc_final = storage_soc
    eta_charge, eta_discharge, E_max_st, dt_hours_st, S_base_st, _conn = storage_phys
    if not lista_storage:
        raise ValueError("storage_info is empty but grid.ESS is True")

    model.soc_initial = pyo.Param(
        lista_storage,
        mutable=True,
        initialize={s: float(soc_initial[s]) for s in lista_storage},
    )
    model.soc_final = pyo.Param(
        lista_storage,
        mutable=True,
        initialize={
            s: (
                float(soc_final[s])
                if soc_final[s] is not None
                else float(soc_initial[s])
            )
            for s in lista_storage
        },
    )

    model.window_soc_constraint = pyo.ConstraintList()

    for i, t in enumerate(ordered):
        block = model.frame_model[t]
        for s in lista_storage:
            delta = _soc_delta_expr(
                eta_charge, eta_discharge, E_max_st, dt_hours_st, S_base_st,
                block, s)
            if i == 0:
                model.window_soc_constraint.add(
                    block.SoC[s] == model.soc_initial[s] + delta)
            else:
                t_prev = ordered[i - 1]
                model.window_soc_constraint.add(
                    block.SoC[s] == model.frame_model[t_prev].SoC[s] + delta)

    if enforce_final and ordered:
        t_last = ordered[-1]
        for s in lista_storage:
            if soc_final[s] is not None:
                model.window_soc_constraint.add(
                    model.frame_model[t_last].SoC[s] == model.soc_final[s])


def window_h2_constraints(
    model,
    grid,
    hydrogen_info,
    frames,
    *,
    enforce_final=True,
    final_frames=None,
    final_scale=None,
):
    """Parent-level H₂ mass chain across ``frame_model`` blocks.

    ``h2_mass_initial`` and per-pin ``h2_mass_final_target`` are mutable
    ``Param``s (rolling keeps initial at 0; targets fixed for a given structure).

    * One terminal frame (default / single pin): ``mass_H2[t] == scale ·
      H2_mass_final`` (optional ``final_scale``).
    * Several pins (future sight: end of commit and end of foresight): each
      segment must produce ``>= scale · H2_mass_final`` (incremental; default
      scale ``1``). Tank ub stays ``scale₀ · H2_mass_max`` through the first
      pin, then ``(Σ scales) · H2_mass_max``.
    """
    ordered = list(frames)
    hydrogen_lim, hydrogen_state, hydrogen_phys, lista_electrolyser = hydrogen_info
    _Pmin, _Pmax, _Qmin, _Qmax, H2_mass_max = hydrogen_lim
    H2_mass_initial, H2_mass_final = hydrogen_state
    b_h, c_h, S_base_el, dt_hours_el, _connected = hydrogen_phys
    if not lista_electrolyser:
        raise ValueError("hydrogen_info is empty but grid.H2 is True")
    el_ids = lista_electrolyser
    el_name = {el.electrolyserNumber: el.name for el in grid.electrolysers}

    model.h2_mass_initial = pyo.Param(
        el_ids,
        mutable=True,
        initialize={e: float(H2_mass_initial[e]) for e in el_ids},
    )

    model.window_h2_constraint = pyo.ConstraintList()

    for i, t in enumerate(ordered):
        block = model.frame_model[t]
        for e in el_ids:
            h_prod = (
                b_h[e] * block.P_electrolyser[e] * S_base_el[e] * dt_hours_el[e]
                + c_h[e])
            if i == 0:
                model.window_h2_constraint.add(
                    block.mass_H2[e] == model.h2_mass_initial[e] + h_prod)
            else:
                t_prev = ordered[i - 1]
                model.window_h2_constraint.add(
                    block.mass_H2[e] == model.frame_model[t_prev].mass_H2[e] + h_prod)

    if not enforce_final or not ordered:
        return

    if final_frames is None:
        term_frames = [ordered[-1]]
    else:
        term_frames = list(final_frames)
        if not term_frames:
            raise ValueError("final_frames is empty")
        ordered_set = set(ordered)
        for t in term_frames:
            if t not in ordered_set:
                raise ValueError(
                    f"h2 final frame={t} is not in solved frames "
                    f"{ordered[0]}…{ordered[-1]}"
                )

    if final_scale is not None:
        for t in term_frames:
            if t not in final_scale:
                raise ValueError(
                    f"final_scale missing frame={t}; have {sorted(final_scale)}"
                )

    pin_scales = [
        1.0 if final_scale is None else float(final_scale[t_term])
        for t_term in term_frames
    ]
    for scale in pin_scales:
        if scale < 0:
            raise ValueError(f"H₂ final_scale values must be >= 0, got {scale}")

    els_with_final = [e for e in el_ids if H2_mass_final[e] is not None]
    if not els_with_final:
        return

    for e in els_with_final:
        if H2_mass_final[e] > H2_mass_max[e]:
            raise ValueError(
                f"H2_mass_final={H2_mass_final[e]} exceeds "
                f"H2_mass_max={H2_mass_max[e]} on {el_name[e]!r}"
            )

    incremental = len(term_frames) > 1
    if incremental:
        first_pin = term_frames[0]
        first_scale = pin_scales[0]
        total_scale = sum(pin_scales)
        for t in ordered:
            ub_scale = first_scale if t <= first_pin else total_scale
            for e in els_with_final:
                model.frame_model[t].mass_H2[e].setub(ub_scale * H2_mass_max[e])

        pin_index = [(t_term, e) for t_term in term_frames for e in els_with_final]
        pin_init = {
            (t_term, e): float(H2_mass_final[e]) * pin_scales[i]
            for i, t_term in enumerate(term_frames)
            for e in els_with_final
        }
        model.h2_mass_final_target = pyo.Param(
            pin_index, mutable=True, initialize=pin_init
        )
        for i, t_term in enumerate(term_frames):
            for e in els_with_final:
                mass_end = model.frame_model[t_term].mass_H2[e]
                if i == 0:
                    mass_start = model.h2_mass_initial[e]
                else:
                    mass_start = model.frame_model[term_frames[i - 1]].mass_H2[e]
                model.window_h2_constraint.add(
                    mass_end - mass_start
                    >= model.h2_mass_final_target[t_term, e]
                )
        return

    # Single pin: mass[t] == scale * H2_mass_final
    pin_index = []
    pin_init = {}
    for t_term, scale in zip(term_frames, pin_scales):
        for e in els_with_final:
            target = scale * H2_mass_final[e]
            if target > H2_mass_max[e]:
                raise ValueError(
                    f"H₂ final target {target} kg (scale={scale} × "
                    f"H2_mass_final={H2_mass_final[e]}) exceeds "
                    f"H2_mass_max={H2_mass_max[e]} on {el_name[e]!r}"
                )
            pin_index.append((t_term, e))
            pin_init[(t_term, e)] = float(target)

    model.h2_mass_final_target = pyo.Param(
        pin_index, mutable=True, initialize=pin_init
    )
    for t_term, e in pin_index:
        model.window_h2_constraint.add(
            model.frame_model[t_term].mass_H2[e]
            == model.h2_mass_final_target[t_term, e]
        )


def window_heat_pump_constraints(model, grid, heat_pump_info, frames):
    """Parent-level cumulative HP energy-state chain across ``frame_model`` blocks."""
    ordered = list(frames)
    hp_ids, heat_pump_by_number = heat_pump_info
    if not hp_ids:
        return

    model.hp_energy_initial = pyo.Param(
        hp_ids,
        mutable=True,
        initialize={h: float(heat_pump_by_number[h].E_state) for h in hp_ids},
    )
    model.window_heat_pump_constraint = pyo.ConstraintList()

    for i, t in enumerate(ordered):
        block = model.frame_model[t]
        for h, hp in heat_pump_by_number.items():
            delta = block.P_heat_pump[h] * hp.np_hp * hp.S_base * hp.dt_hours
            if i == 0:
                model.window_heat_pump_constraint.add(
                    block.E_heat_pump[h] == model.hp_energy_initial[h] + delta
                )
            else:
                t_prev = ordered[i - 1]
                model.window_heat_pump_constraint.add(
                    block.E_heat_pump[h] == model.frame_model[t_prev].E_heat_pump[h] + delta
                )


def _snapshot_var_values(model_obj):
    values = {}
    for var_obj in model_obj.component_objects(pyo.Var, active=True):
        values[var_obj.name] = {index: var_obj[index].value for index in var_obj}
    return values


def _create_frame_blocks(
    model,
    grid,
    frames,
    pv_set,
    price_zones,
    limit_flow_rate,
    weights_def,
    ts_base,
):
    base_model = pyo.ConcreteModel()
    opf_create_nl_model_acdc(
        base_model,
        grid,
        PV_set=pv_set,
        Price_Zones=price_zones,
        limit_flow_rate=limit_flow_rate,
        window_block=True,
    )

    opf_data = translate_pyf_opf(grid, Price_Zones=price_zones)
    storage_info = opf_data['storage_info']
    hydrogen_info = opf_data['hydrogen_info']
    heat_pump_info = opf_data['heat_pump_info']

    for i in frames:
        base_copy = base_model.clone()
        model.frame_model[i].transfer_attributes_from(base_copy)
        abs_t = ts_base + i
        for ts in grid.Time_series:
            update_grid_data(grid, ts, abs_t, price_zone_restrictions=price_zones)
        _modify_parameters(grid, model.frame_model[i], price_zones, window_block=True)
        obj_rule = opf_obj(model.frame_model[i], grid, weights_def)
        model.frame_model[i].obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
        if grid.nn_DC != 0 and any(conv.OPF_fx for conv in grid.Converters_ACDC):
            fx_conv(model.frame_model[i], grid)

    return storage_info, hydrogen_info, heat_pump_info


def _update_window_frame_params(model, grid, frames, ts_base, price_zones):
    """Reload TS into each local frame block (``_modify_parameters`` like ``ts_acdc_opf``)."""
    for i in frames:
        abs_t = ts_base + i
        for ts in grid.Time_series:
            update_grid_data(grid, ts, abs_t, price_zone_restrictions=price_zones)
        _modify_parameters(grid, model.frame_model[i], price_zones, window_block=True)


def _set_window_state_params(model, grid):
    """Push current SoC / H₂ initials into mutable window Params."""
    if grid.ESS:
        for st in grid.storage_elements:
            model.soc_initial[st.storageNumber].set_value(float(st.soc_initial))
    if grid.H2:
        for el in grid.electrolysers:
            model.h2_mass_initial[el.electrolyserNumber].set_value(
                float(el.H2_mass_initial)
            )
    if hasattr(model, 'hp_energy_initial'):
        for hp in grid.heat_pumps:
            model.hp_energy_initial[hp.heatPumpNumber].set_value(float(hp.E_state))


def export_window_opf_results(model, grid, frames, ts_base=0):
    """Build per-frame storage trajectories from solved frame blocks.

    ``frames`` are **local** model indices ``0…n-1``. Result ``frame`` columns
    use absolute TS indices ``ts_base + local``. ``storage_soc`` includes a
    leading row at ``ts_base - 1`` with each element's ``soc_initial``.
    """
    ordered = list(frames)

    def _abs_frame(local_t):
        return ts_base + local_t

    rows_soc = []
    rows_pc = []
    rows_pd = []
    rows_p = []
    rows_q = []

    if ordered and grid.storage_elements:
        row0 = {'frame': _abs_frame(ordered[0]) - 1}
        for storage in grid.storage_elements:
            row0[storage.name] = np.float64(storage.soc_initial)
        rows_soc.append(row0)

    for t in ordered:
        block = model.frame_model[t]
        abs_t = _abs_frame(t)
        row_soc = {'frame': abs_t}
        row_pc = {'frame': abs_t}
        row_pd = {'frame': abs_t}
        row_p = {'frame': abs_t}
        row_q = {'frame': abs_t}
        for storage in grid.storage_elements:
            name = storage.name
            s = storage.storageNumber
            row_soc[name] = np.float64(pyo.value(block.SoC[s]))
            pc = np.float64(pyo.value(block.P_storage_charge[s])) * grid.S_base
            pd_ = np.float64(pyo.value(block.P_storage_discharge[s])) * grid.S_base
            if storage.connected == AcDcSide.AC:
                row_q[name] = (
                    np.float64(pyo.value(block.Q_storage[s])) * grid.S_base
                )
            else:
                row_q[name] = np.nan
            row_pc[name] = pc
            row_pd[name] = pd_
            row_p[name] = pd_ - pc
        rows_soc.append(row_soc)
        rows_pc.append(row_pc)
        rows_pd.append(row_pd)
        rows_p.append(row_p)
        rows_q.append(row_q)

    summary_rows = []
    for storage in grid.storage_elements:
        pc_col = [row[storage.name] for row in rows_pc]
        pd_col = [row[storage.name] for row in rows_pd]
        energy_in = sum(pc_col) * storage.dt_hours
        energy_out = sum(pd_col) * storage.dt_hours
        rt_eff = energy_out / energy_in if energy_in > 0 else np.nan
        summary_rows.append({
            'Name': storage.name,
            'Side': storage.connected.value,
            'Energy charged (MWh)': energy_in,
            'Energy discharged (MWh)': energy_out,
            'Round-trip efficiency': rt_eff,
        })

    results = {
        'storage_soc': pd.DataFrame(rows_soc),
        'storage_power': pd.DataFrame(rows_p),
        'storage_Q': pd.DataFrame(rows_q),
        'storage_summary': pd.DataFrame(summary_rows),
        'total_objective': np.float64(pyo.value(model.obj)),
    }

    if grid.electrolysers:
        rows_m = []
        rows_pe = []
        if ordered:
            row_m0 = {'frame': _abs_frame(ordered[0]) - 1}
            for el in grid.electrolysers:
                row_m0[el.name] = np.float64(el.H2_mass_initial)
            rows_m.append(row_m0)
        for t in ordered:
            block = model.frame_model[t]
            abs_t = _abs_frame(t)
            row_m = {'frame': abs_t}
            row_pe = {'frame': abs_t}
            for el in grid.electrolysers:
                e = el.electrolyserNumber
                row_m[el.name] = np.float64(pyo.value(block.mass_H2[e]))
                row_pe[el.name] = np.float64(pyo.value(block.P_electrolyser[e])) * grid.S_base
            rows_m.append(row_m)
            rows_pe.append(row_pe)
        results['hydrogen_mass_H2'] = pd.DataFrame(rows_m)
        results['hydrogen_P_e'] = pd.DataFrame(rows_pe)

    if grid.heat_pumps:
        rows_hp_p = []
        rows_hp_q = []
        rows_hp_e = []
        if ordered:
            row_e0 = {'frame': _abs_frame(ordered[0]) - 1}
            for hp in grid.heat_pumps:
                row_e0[hp.name] = np.float64(hp.E_state)
            rows_hp_e.append(row_e0)
        for t in ordered:
            block = model.frame_model[t]
            abs_t = _abs_frame(t)
            row_p = {'frame': abs_t}
            row_q = {'frame': abs_t}
            row_e = {'frame': abs_t}
            for hp in grid.heat_pumps:
                h = hp.heatPumpNumber
                row_p[hp.name] = np.float64(pyo.value(block.P_heat_pump[h])) * hp.np_hp * grid.S_base
                if hasattr(block, "Q_heat_pump"):
                    row_q[hp.name] = (
                        np.float64(pyo.value(block.Q_heat_pump[h])) * hp.np_hp * grid.S_base
                    )
                else:
                    row_q[hp.name] = 0.0
                row_e[hp.name] = np.float64(pyo.value(block.E_heat_pump[h]))
            rows_hp_p.append(row_p)
            rows_hp_q.append(row_q)
            rows_hp_e.append(row_e)
        results['heat_pump_P'] = pd.DataFrame(rows_hp_p)
        results['heat_pump_Q'] = pd.DataFrame(rows_hp_q)
        results['heat_pump_energy_state'] = pd.DataFrame(rows_hp_e)

    if ordered and (grid.Generators or grid.Generators_DC):
        rows_gp = []
        rows_gprice = []
        for t in ordered:
            block = model.frame_model[t]
            abs_t = _abs_frame(t)
            row_gp = {'frame': abs_t}
            row_gprice = {'frame': abs_t}
            for gen in grid.Generators:
                g = gen.genNumber
                p = np.float64(pyo.value(block.PGi_gen[g]))
                if grid.act_gen:
                    p *= np.float64(pyo.value(block.gen_active[g]))
                row_gp[gen.name] = p * grid.S_base
                if hasattr(block, 'lf'):
                    row_gprice[gen.name] = np.float64(pyo.value(block.lf[g]))
                else:
                    row_gprice[gen.name] = np.nan
            for gen in grid.Generators_DC:
                g = gen.genNumber_DC
                row_gp[gen.name] = (
                    np.float64(pyo.value(block.PGi_gen_DC[g])) * grid.S_base
                )
                if hasattr(block, 'lf_dc'):
                    row_gprice[gen.name] = np.float64(pyo.value(block.lf_dc[g]))
                else:
                    row_gprice[gen.name] = np.nan
            rows_gp.append(row_gp)
            rows_gprice.append(row_gprice)
        results['gen_power'] = pd.DataFrame(rows_gp)
        results['gen_price'] = pd.DataFrame(rows_gprice)

    if ordered and grid.RenSources:
        nodes_ac = {n.name: n for n in grid.nodes_AC}
        nodes_dc = {n.name: n for n in grid.nodes_DC}
        rows_rp = []
        rows_ravail = []
        rows_rprice = []
        rows_curt = []
        for t in ordered:
            block = model.frame_model[t]
            abs_t = _abs_frame(t)
            row_rp = {'frame': abs_t}
            row_ravail = {'frame': abs_t}
            row_rprice = {'frame': abs_t}
            row_c = {'frame': abs_t}
            for rs in grid.RenSources:
                r = rs.rsNumber
                p_ren = np.float64(pyo.value(block.P_renSource[r]))
                gamma = np.float64(pyo.value(block.gamma[r]))
                np_rs = np.float64(pyo.value(block.np_rsgen[r]))
                available_pu = p_ren * np_rs
                row_ravail[rs.name] = available_pu * grid.S_base
                row_rp[rs.name] = available_pu * gamma * grid.S_base
                if np_rs <= 0:
                    row_c[rs.name] = 0.0
                else:
                    row_c[rs.name] = 1.0 - gamma
                if rs.connected in (AcDcSide.AC, 'AC'):
                    node = nodes_ac.get(rs.Node)
                    if node is not None and hasattr(block, 'price'):
                        row_rprice[rs.name] = np.float64(
                            pyo.value(block.price[node.nodeNumber])
                        )
                    else:
                        row_rprice[rs.name] = np.nan
                else:
                    node = nodes_dc.get(rs.Node)
                    if node is not None and hasattr(block, 'price_dc'):
                        row_rprice[rs.name] = np.float64(
                            pyo.value(block.price_dc[node.nodeNumber])
                        )
                    else:
                        row_rprice[rs.name] = np.nan
            rows_rp.append(row_rp)
            rows_ravail.append(row_ravail)
            rows_rprice.append(row_rprice)
            rows_curt.append(row_c)
        results['ren_power'] = pd.DataFrame(rows_rp)
        results['ren_available'] = pd.DataFrame(rows_ravail)
        results['ren_price'] = pd.DataFrame(rows_rprice)
        results['curtailment'] = pd.DataFrame(rows_curt)

    if ordered and (grid.ACmode or grid.DCmode):
        rows_ac = []
        rows_dc = []
        for t in ordered:
            block = model.frame_model[t]
            abs_t = _abs_frame(t)
            line_data, _, _ = _calculate_line_loading_from_model(grid, block, abs_t)
            row_ac = {'frame': abs_t}
            row_dc = {'frame': abs_t}
            for key, val in line_data.items():
                if key.startswith('AC_Load_'):
                    row_ac[key[len('AC_Load_'):]] = val
                elif key.startswith('DC_Load_'):
                    row_dc[key[len('DC_Load_'):]] = val
            rows_ac.append(row_ac)
            rows_dc.append(row_dc)
        if grid.ACmode and grid.lines_AC:
            results['ac_loading'] = pd.DataFrame(rows_ac)
        if grid.DCmode and grid.lines_DC:
            results['dc_loading'] = pd.DataFrame(rows_dc)

    if (
        ordered
        and grid.ACmode
        and grid.DCmode
        and grid.Converters_ACDC
    ):
        # NL has Q_conv_s_AC / P_conv_c_AC / P_conv_loss; linear has P-only Ps.
        linear_conv = not hasattr(model.frame_model[ordered[0]], 'Q_conv_s_AC')
        rows_conv = []
        for t in ordered:
            block = model.frame_model[t]
            row_conv = {'frame': _abs_frame(t)}
            p_s = {
                k: np.float64(pyo.value(v))
                for k, v in block.P_conv_s_AC.items()
            }
            if linear_conv:
                for conv in grid.Converters_ACDC:
                    n = conv.ConvNumber
                    ps = p_s[n]
                    loss_pu = float(conv.a_conv) + float(conv.b_conv) * ps
                    p_ac = ps * conv.np_conv
                    p_dc = -(p_ac + loss_pu * conv.np_conv)
                    if conv.np_conv == 0:
                        row_conv[conv.name] = 0.0
                    else:
                        row_conv[conv.name] = (
                            max(abs(p_ac), abs(p_dc)) * grid.S_base
                            / (conv.MVA_max * conv.np_conv)
                        )
            else:
                q_s = {
                    k: np.float64(pyo.value(v))
                    for k, v in block.Q_conv_s_AC.items()
                }
                p_c = {
                    k: np.float64(pyo.value(v))
                    for k, v in block.P_conv_c_AC.items()
                }
                p_loss = {
                    k: np.float64(pyo.value(v))
                    for k, v in block.P_conv_loss.items()
                }
                for conv in grid.Converters_ACDC:
                    n = conv.ConvNumber
                    p_ac = p_s[n] * conv.np_conv
                    q_ac = q_s[n] * conv.np_conv
                    p_dc = -(p_c[n] + p_loss[n]) * conv.np_conv
                    if conv.np_conv == 0:
                        row_conv[conv.name] = 0.0
                    else:
                        s_ac = np.sqrt(p_ac**2 + q_ac**2)
                        row_conv[conv.name] = (
                            max(s_ac, abs(p_dc)) * grid.S_base
                            / (conv.MVA_max * conv.np_conv)
                        )
            rows_conv.append(row_conv)
        results['converter_loading'] = pd.DataFrame(rows_conv)

    return results


def window_nl_opf(
    grid,
    start=0,
    end=23,
    ObjRule=None,
    PV_set=False,
    limit_flow_rate=True,
    solver='ipopt',
    tee=False,
    callback=False,
    obj_scaling=1.0,
    build_only=False,
    enforce_soc_final=True,
    enforce_h2_final=True,
    h2_final_frames=None,
    h2_final_scale=None,
    *,
    _reuse=None,
    warm_start_mode='roll',
):
    """Build and solve a coupled NL OPF over frames ``start…end`` (0-based, inclusive).

    Internally the Pyomo model uses **local** frame indices ``0…n-1``; ``start``
    is the absolute TS base. Result tables still use absolute TS frame numbers.

    Rolling may pass ``_reuse`` (cache dict) and ``warm_start_mode`` ``'roll'`` /
    ``'hard'`` (same meaning as :func:`~pyflow_acdc.ts_acdc_opf`).

    Parameters
    ----------
    start, end : int, optional
        Inclusive 0-based absolute TS frame indices.
    warm_start_mode : {'roll', 'hard'}, optional
        When reusing a cached model: ``roll`` keeps the previous solution;
        ``hard`` resets variables to the post-build initializer.
    _reuse : dict or None, optional
        Internal rolling cache ``{structure_key: cache_entry}``.
    """
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")

    grid.reset_run_flags()
    analyse_grid(grid)

    if not grid.ESS and not grid.H2 and not grid.HP:
        raise ValueError(
            "window_nl_opf requires at least one storage, electrolyser, or heat-pump element")

    if not grid.Time_series:
        raise ValueError("window_nl_opf requires grid.Time_series")

    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if end < start:
        raise ValueError(f"end ({end}) must be >= start ({start})")

    ts_len = len(grid.Time_series[0].data)
    if end >= ts_len:
        raise ValueError(
            f"end={end} out of range for Time_series length {ts_len} (0-based)")

    weights_def, price_zones = obj_w_rule(grid, ObjRule)
    ts_base = start
    n_local = end - start + 1
    frames = list(range(n_local))

    # Absolute → local for H₂ pins
    h2_frames_local = None
    h2_scale_local = None
    if h2_final_frames is not None:
        h2_frames_local = [t - ts_base for t in h2_final_frames]
        for t_loc in h2_frames_local:
            if t_loc < 0 or t_loc >= n_local:
                raise ValueError(
                    f"h2_final_frames absolute values must lie in [{start}, {end}]"
                )
        if h2_final_scale is not None:
            h2_scale_local = {
                t - ts_base: scale for t, scale in h2_final_scale.items()
            }

    struct_key = (
        n_local,
        bool(enforce_soc_final),
        bool(enforce_h2_final),
        tuple(h2_frames_local) if h2_frames_local is not None else None,
        tuple(sorted((h2_scale_local or {}).items())),
    )

    cache_entry = None if _reuse is None else _reuse.get(struct_key)
    t_modelcreate = 0.0
    t_modelupdate = 0.0

    if cache_entry is None:
        model = pyo.ConcreteModel()
        model.name = f"Window NL OPF [n={n_local}]"
        model.frames = pyo.Set(initialize=frames)
        model.frame_model = pyo.Block(model.frames)

        t1 = time.perf_counter()
        storage_info, hydrogen_info, heat_pump_info = _create_frame_blocks(
            model,
            grid,
            frames,
            PV_set,
            price_zones,
            limit_flow_rate,
            weights_def,
            ts_base,
        )
        if grid.ESS:
            window_soc_constraints(
                model, grid, storage_info, frames,
                enforce_final=enforce_soc_final,
            )
        if grid.H2:
            window_h2_constraints(
                model, grid, hydrogen_info, frames,
                enforce_final=enforce_h2_final,
                final_frames=h2_frames_local,
                final_scale=h2_scale_local,
            )
        if grid.HP:
            window_heat_pump_constraints(model, grid, heat_pump_info, frames)
        obj_total = _sum_frame_objectives(model, frames)
        if obj_scaling != 1.0:
            obj_total = obj_total / obj_scaling
        model.obj = pyo.Objective(rule=obj_total, sense=pyo.minimize)
        model.obj_scaling = obj_scaling
        t_modelcreate = time.perf_counter() - t1
        initial_values = _snapshot_var_values(model)
        if _reuse is not None:
            _reuse[struct_key] = {
                'model': model,
                'initial_values': initial_values,
                'storage_info': storage_info,
                'hydrogen_info': hydrogen_info,
                'heat_pump_info': heat_pump_info,
                'price_zones': price_zones,
                'weights_def': weights_def,
            }
    else:
        model = cache_entry['model']
        storage_info = cache_entry['storage_info']
        hydrogen_info = cache_entry['hydrogen_info']
        heat_pump_info = cache_entry.get('heat_pump_info')
        price_zones = cache_entry['price_zones']
        weights_def = cache_entry['weights_def']
        t1 = time.perf_counter()
        if warm_start_mode == 'hard':
            reset_to_initialize(model, cache_entry['initial_values'])
        _update_window_frame_params(model, grid, frames, ts_base, price_zones)
        _set_window_state_params(model, grid)
        t_modelupdate = time.perf_counter() - t1

    if build_only:
        model_res, solver_stats = build_only_solver_stats(solver, model)
        export_results = True
    else:
        model_res, solver_stats = pyomo_model_solve(
            model, grid, solver, tee, callback=callback)
        export_results = (
            model_res is not None and solver_stats.get('solution_found') is not False)

        # Retry opposite warm-start like ts_acdc_opf when a cached model exists.
        if (
            not export_results
            and _reuse is not None
            and struct_key in _reuse
        ):
            entry = _reuse[struct_key]
            retry_mode = 'roll' if warm_start_mode == 'hard' else 'hard'
            if retry_mode == 'hard':
                reset_to_initialize(model, entry['initial_values'])
            _update_window_frame_params(model, grid, frames, ts_base, price_zones)
            _set_window_state_params(model, grid)
            model_res, solver_stats = pyomo_model_solve(
                model, grid, solver, tee, callback=callback)
            export_results = (
                model_res is not None
                and solver_stats.get('solution_found') is not False
            )

    t3 = time.perf_counter()
    if export_results:
        grid.window_opf_results = export_window_opf_results(
            model, grid, frames, ts_base=ts_base
        )
        last_local = frames[-1]
        last_abs = ts_base + last_local
        for ts in grid.Time_series:
            update_grid_data(grid, ts, last_abs, price_zone_restrictions=price_zones)
        _modify_parameters(grid, model.frame_model[last_local], price_zones, window_block=True)
        export_acdc_nl_model_to_pyflow_acdc(
            model.frame_model[last_local], grid, price_zones)

    for obj in weights_def:
        weights_def[obj]['v'] = calculate_objective(grid, obj)

    t4 = time.perf_counter()

    grid.window_opf_run = True
    grid.OPF_run = True
    grid.OPF_obj = weights_def

    timing_info = {
        'create': t_modelcreate,
        'update': t_modelupdate,
        'solve': solver_stats['time'] if solver_stats.get('time') is not None else t4 - t3,
        'export': t4 - t3,
    }
    return model, model_res, timing_info, solver_stats


def _ts_inclusive_0based(start, end, ts_len):
    """Convert TS-style 1-based inclusive ``start``/``end`` to 0-based inclusive."""
    if start < 1:
        raise ValueError(f"start must be >= 1 (1-based, like ts_acdc_opf), got {start}")
    idx0 = start - 1
    if end is None:
        end = ts_len
    max_time = min(ts_len, end)
    if max_time <= idx0:
        raise ValueError(
            f"Empty horizon: start={start}, end={end}, Time_series length={ts_len}"
        )
    return idx0, max_time - 1


def _rolling_commit_windows(idx0, idx1, window_size):
    """Return list of (commit_start, commit_end) 0-based inclusive pairs."""
    if window_size < 1:
        raise ValueError(f"window_size must be >= 1, got {window_size}")
    windows = []
    t = idx0
    while t <= idx1:
        w_end = min(t + window_size - 1, idx1)
        windows.append((t, w_end))
        t = w_end + 1
    return windows


def _slice_window_results(results, keep_frames, *, include_initial_row, initial_frame):
    """Keep rows whose ``frame`` is in ``keep_frames`` (plus optional initial row)."""
    keep = set(keep_frames)
    out = {}
    for key, df in results.items():
        if not isinstance(df, pd.DataFrame) or 'frame' not in getattr(df, 'columns', []):
            out[key] = df
            continue
        mask = df['frame'].isin(keep)
        if include_initial_row:
            mask = mask | (df['frame'] == initial_frame)
        out[key] = df.loc[mask].copy()
    return out


def _concat_rolling_results(parts):
    """Concatenate per-window result dicts (DataFrames by ``frame``)."""
    if not parts:
        raise ValueError("No window results to concatenate")
    keys = parts[0].keys()
    merged = {}
    for key in keys:
        chunks = [p[key] for p in parts if key in p]
        if not chunks:
            continue
        if all(isinstance(c, pd.DataFrame) for c in chunks):
            merged[key] = pd.concat(chunks, ignore_index=True)
        else:
            merged[key] = chunks[-1]
    return merged


def _carry_state_from_results(grid, results, commit_end):
    """Set ``soc_initial`` from results at ``commit_end`` (H₂ is not carried)."""
    if grid.ESS:
        soc = results.get('storage_soc')
        if soc is None or soc.empty:
            raise ValueError("storage_soc missing from window results for carry-over")
        row = soc.loc[soc['frame'] == commit_end]
        if row.empty:
            raise ValueError(f"No storage_soc row for commit_end frame={commit_end}")
        for st in grid.storage_elements:
            if st.name not in row.columns:
                raise ValueError(f"storage {st.name!r} missing from storage_soc")
            st.soc_initial = float(row.iloc[0][st.name])


def _empty_h2_tank(grid, electrolysers=None):
    """Reset selected (or all) H₂ tanks between solves — not an OPF constraint."""
    els = electrolysers if electrolysers is not None else grid.electrolysers
    for el in els:
        el.empty_tank()


def _rolling_h2_empty_targets(electrolysers):
    """Next 1-based hour targets for ``empty_tank_cycle`` (``None`` → always)."""
    targets = {}
    for el in electrolysers:
        n = el.empty_tank_cycle
        targets[el.electrolyserNumber] = None if n is None else int(n)
    return targets


def _electrolysers_to_empty_after_rolling_commit(electrolysers, commit_end_1based, targets):
    """Return electrolysers to empty after a rolling commit ending at hour ``h``.

    ``empty_tank_cycle is None`` → every window boundary.
    Otherwise empty at the first commit boundary with ``h >= k·N`` (ceil to the
    next window end at or past each cycle multiple), then advance the target.
    """
    to_empty = []
    for el in electrolysers:
        e = el.electrolyserNumber
        next_t = targets[e]
        if next_t is None:
            to_empty.append(el)
            continue
        if commit_end_1based < next_t:
            continue
        to_empty.append(el)
        n = el.empty_tank_cycle
        targets[e] = ((commit_end_1based // n) + 1) * n
    return to_empty


def rolling_window_nl_opf(
    grid,
    start=1,
    end=None,
    window_size=24,
    soc_final_mode='every_m',
    soc_final_every_m=1,
    future_sight=0.0,
    ObjRule=None,
    PV_set=False,
    limit_flow_rate=True,
    solver='ipopt',
    tee=False,
    callback=False,
    obj_scaling=1.0,
    build_only=False,
    print_step=False,
    warm_start_mode='roll',
):
    """Solve chained ``window_nl_opf`` segments over a TS horizon (Phase 7).

    Indexing matches :func:`~pyflow_acdc.ts_acdc_opf`: ``start``/``end`` are
    **1-based inclusive**. Horizon length ``N = end - start + 1`` (clipped to
    the series). Windows have length ``window_size``; the last window may be
    shorter.

    Equal-length windows reuse one Pyomo model (local frames ``0…n-1``): TS and
    SoC/H₂ state ``Param``s are updated each roll (constraints stay put).
    ``warm_start_mode`` matches :func:`~pyflow_acdc.ts_acdc_opf` (``roll`` /
    ``hard``). Short last windows and foresight solves use separate
    cached models.

    Each window starts from the previous terminal SoC. H₂ tank empties are
    **out-of-opt** (between solves), gated by each electrolyser's
    ``empty_tank_cycle``:

    * ``None`` (default) — empty at **every** commit-window boundary (next
      window starts at ``H2_mass_initial = 0``).
    * positive ``N`` — empty at the first commit boundary whose 1-based end
      hour is ``>= k·N`` (window end at or past each cycle multiple); inventory
      otherwise carries across windows.

    Whether the goal is a mass target or sale-only does not change the empty
    policy above.

    Terminal SoC / foresight:

    * ``future_sight`` in ``(0, 1]`` — extend the solve by
      ``ceil(future_sight · window_size)`` frames into the next commit
      (clamped to remaining hours). Enforce ``soc_final`` on that foresight
      end; keep only the commit. With a mass target, commit must produce
      ``>= H2_mass_final`` and the foresight segment ``>= future_sight ·
      H2_mass_final`` (raw fraction). Last window has no foresight and still
      enforces ``soc_final``.
    * ``future_sight == 0`` — no foresight. Terminal SoC follows
      ``soc_final_mode='every_m'``: windows ``1…m-1`` run with
      ``enforce_soc_final=False``; window ``m`` (and ``2m``, …) and the last
      window use ``True``.

    H₂ mass target (``H2_mass_final``) and H₂ sale (``ObjRule['H2_sale']`` with
    ``h2_price`` / ``TSType.H2_PRICE``) are independent. With a mass target and
    no foresight, each commit regenerates ``H2_mass_final`` from the carried
    (or emptied) tank. Under foresight, tank ub stays ``H2_mass_max`` through
    end of the commit, then ``(1 + future_sight) · H2_mass_max`` for the
    foresight segment.

    Parameters
    ----------
    start, end : int, optional
        1-based inclusive hours (same as ``ts_acdc_opf``).
    window_size : int, optional
        Commit frames per window (except possibly the last).
    soc_final_mode : {'every_m'}, optional
        Terminal-SoC policy when ``future_sight == 0``.
    soc_final_every_m : int, optional
        Used when ``soc_final_mode='every_m'`` (must be >= 1).
    future_sight : float, optional
        Foresight fraction in ``[0, 1]`` (default ``0`` = off). Steps are
        ``ceil(future_sight * window_size)``.
    print_step : bool, optional
        If True, print ``Rolling window k/n (frames …)`` before each window.
    warm_start_mode : {'roll', 'hard'}, optional
        Variable warm-start between equal-structure rolls (default ``roll``).

    Returns
    -------
    tuple
        ``(None, None, timing_info, window_stats)`` where ``timing_info`` sums
        per-window create/update/solve/export and ``window_stats`` is a list of
        each window's ``solver_stats``. Results are in ``grid.window_opf_results``;
        ``grid.rolling_window_opf_run`` is True.

        ``timing_info`` sums ``create`` / ``update`` / ``solve`` / ``export`` from
        each ``window_nl_opf``, plus rolling-only ``slice`` / ``carry`` /
        ``empty_h2`` / ``concat``, and ``total_wall`` with UTC ``wall_start`` /
        ``wall_end``. Each ``window_stats[i]['timing']`` has the same per-window
        breakdown plus wall timestamps.
    """
    if soc_final_mode not in ('every_m',):
        raise ValueError(
            f"soc_final_mode must be 'every_m', got {soc_final_mode!r}"
        )
    if soc_final_every_m < 1:
        raise ValueError(f"soc_final_every_m must be >= 1, got {soc_final_every_m}")
    future_sight = float(future_sight)
    if not (0.0 <= future_sight <= 1.0):
        raise ValueError(f"future_sight must be in [0, 1], got {future_sight}")
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")

    analyse_grid(grid)
    if not grid.ESS and not grid.H2:
        raise ValueError(
            "rolling_window_nl_opf requires at least one storage or electrolyser"
        )
    if not grid.Time_series:
        raise ValueError("rolling_window_nl_opf requires grid.Time_series")

    ts_len = len(grid.Time_series[0].data)
    idx0, idx1 = _ts_inclusive_0based(start, end, ts_len)
    commits = _rolling_commit_windows(idx0, idx1, window_size)
    n_win = len(commits)

    storage = list(grid.storage_elements)
    electrolysers = list(grid.electrolysers)
    orig_soc_final = {st.name: st.soc_final for st in storage}
    enforce_h2_mass = any(
        el.H2_mass_final is not None
        for el in electrolysers
    )
    h2_empty_targets = _rolling_h2_empty_targets(electrolysers)

    if grid.ESS and any(v is None for v in orig_soc_final.values()):
        missing = [n for n, v in orig_soc_final.items() if v is None]
        raise ValueError(
            "rolling_window_nl_opf requires soc_final on all storage elements; "
            f"missing for {missing}"
        )

    result_parts = []
    window_stats = []
    timing_acc = {
        'create': 0.0,
        'update': 0.0,
        'solve': 0.0,
        'export': 0.0,
        'slice': 0.0,
        'carry': 0.0,
        'empty_h2': 0.0,
        'concat': 0.0,
    }
    model_cache = {}
    t_roll0 = time.perf_counter()
    roll_wall_start = datetime.now(timezone.utc).isoformat()

    for k, (c_start, c_end) in enumerate(commits):
        t_win0 = time.perf_counter()
        wall_start = datetime.now(timezone.utc).isoformat()
        is_last = k == n_win - 1
        available = idx1 - c_end
        foresight_steps = 0
        if future_sight > 0.0 and not is_last and available > 0:
            foresight_steps = min(
                math.ceil(future_sight * window_size),
                available,
            )
        use_foresight = foresight_steps > 0
        if use_foresight:
            foresight_end = c_end + foresight_steps
            solve_start, solve_end = c_start, foresight_end
            force_soc = True
            if enforce_h2_mass:
                h2_frames = [c_end, foresight_end]
                h2_scale = {c_end: 1.0, foresight_end: future_sight}
            else:
                h2_frames = None
                h2_scale = None
        else:
            solve_start, solve_end = c_start, c_end
            if future_sight > 0.0:
                force_soc = True  # last window (or no remaining foresight hours)
            else:
                force_soc = ((k + 1) % soc_final_every_m == 0) or is_last
            h2_frames = None  # last frame of this solve
            h2_scale = None
        if print_step:
            step_msg = (
                f"[{wall_start}] Rolling window {k + 1}/{n_win} "
                f"(frames {c_start}–{c_end})"
            )
            if use_foresight:
                step_msg += (
                    f" + future-sight {future_sight:g} "
                    f"({c_end + 1}–{foresight_end}, {foresight_steps} steps)"
                )
            print(step_msg)
        t_prepare = time.perf_counter() - t_win0

        t_opf0 = time.perf_counter()
        model, model_res, timing_info, solver_stats = window_nl_opf(
            grid,
            start=solve_start,
            end=solve_end,
            ObjRule=ObjRule,
            PV_set=PV_set,
            limit_flow_rate=limit_flow_rate,
            solver=solver,
            tee=tee,
            callback=callback,
            obj_scaling=obj_scaling,
            build_only=build_only,
            enforce_soc_final=force_soc,
            enforce_h2_final=enforce_h2_mass,
            h2_final_frames=h2_frames,
            h2_final_scale=h2_scale,
            _reuse=model_cache,
            warm_start_mode=warm_start_mode,
        )
        t_opf_wall = time.perf_counter() - t_opf0
        for key in ('create', 'update', 'solve', 'export'):
            timing_acc[key] += float(timing_info.get(key, 0.0) or 0.0)

        full = grid.window_opf_results
        if full is None:
            raise ValueError(f"Window {k} produced no window_opf_results")
        if (
            not build_only
            and solver_stats is not None
            and solver_stats.get('solution_found') is False
        ):
            raise ValueError(
                f"Rolling window {k + 1}/{n_win} (frames {c_start}–{c_end}) "
                f"did not find a solution: {solver_stats}"
            )

        t_slice0 = time.perf_counter()
        keep = list(range(c_start, c_end + 1))
        sliced = _slice_window_results(
            full,
            keep,
            include_initial_row=(k == 0),
            initial_frame=c_start - 1,
        )
        result_parts.append(sliced)
        t_slice = time.perf_counter() - t_slice0
        timing_acc['slice'] += t_slice

        t_carry = 0.0
        t_empty = 0.0
        if not is_last:
            t_c0 = time.perf_counter()
            _carry_state_from_results(grid, full, c_end)
            t_carry = time.perf_counter() - t_c0
            timing_acc['carry'] += t_carry
            # Out-of-opt tank empty (empty_tank_cycle); None → every boundary.
            t_e0 = time.perf_counter()
            to_empty = _electrolysers_to_empty_after_rolling_commit(
                electrolysers, c_end + 1, h2_empty_targets
            )
            if to_empty:
                _empty_h2_tank(grid, to_empty)
            t_empty = time.perf_counter() - t_e0
            timing_acc['empty_h2'] += t_empty

        t_win = time.perf_counter() - t_win0
        wall_end = datetime.now(timezone.utc).isoformat()
        win_timing = {
            'prepare': t_prepare,
            'create': float(timing_info.get('create', 0.0) or 0.0),
            'update': float(timing_info.get('update', 0.0) or 0.0),
            'solve': float(timing_info.get('solve', 0.0) or 0.0),
            'export': float(timing_info.get('export', 0.0) or 0.0),
            'opf_wall': t_opf_wall,
            'slice': t_slice,
            'carry': t_carry,
            'empty_h2': t_empty,
            'window_wall': t_win,
            'wall_start': wall_start,
            'wall_end': wall_end,
        }
        window_stats.append({
            'window': k,
            'commit': (c_start, c_end),
            'solve': (solve_start, solve_end),
            'force_soc': force_soc,
            'future_sight': future_sight if use_foresight else 0.0,
            'foresight_steps': foresight_steps,
            'h2_final_frames': h2_frames,
            'h2_final_scale': h2_scale,
            'warm_start_mode': warm_start_mode,
            'solver_stats': solver_stats,
            'timing': win_timing,
        })
        if print_step:
            print(
                f"  timing create={win_timing['create']:.3f}s "
                f"update={win_timing['update']:.3f}s "
                f"solve={win_timing['solve']:.3f}s "
                f"export={win_timing['export']:.3f}s "
                f"slice={win_timing['slice']:.3f}s "
                f"carry={win_timing['carry']:.3f}s "
                f"empty_h2={win_timing['empty_h2']:.3f}s "
                f"window={win_timing['window_wall']:.3f}s"
            )

    t_cat0 = time.perf_counter()
    grid.window_opf_results = _concat_rolling_results(result_parts)
    timing_acc['concat'] = time.perf_counter() - t_cat0
    grid.rolling_window_opf_run = True
    grid.window_opf_run = True
    grid.rolling_window_info = {
        'window_size': int(window_size),
        'n_windows': n_win,
        'commits': list(commits),
        'start_frame': idx0,
        'end_frame': idx1,
        'future_sight': future_sight,
    }
    timing_acc['windows'] = n_win
    timing_acc['frames'] = idx1 - idx0 + 1
    timing_acc['total_wall'] = time.perf_counter() - t_roll0
    timing_acc['wall_start'] = roll_wall_start
    timing_acc['wall_end'] = datetime.now(timezone.utc).isoformat()
    return None, None, timing_acc, window_stats


# Excel sheet names are limited to 31 characters.
_WINDOW_OPF_SHEET_NAMES = {
    'storage_soc': 'storage_soc',
    'storage_power': 'storage_power',
    'storage_Q': 'storage_Q',
    'storage_summary': 'storage_summary',
    'hydrogen_mass_H2': 'hydrogen_mass_H2',
    'hydrogen_P_e': 'hydrogen_P_e',
    'gen_power': 'gen_power',
    'gen_price': 'gen_price',
    'ren_power': 'ren_power',
    'ren_price': 'ren_price',
    'node_price': 'node_price',
    'price_zone_price': 'price_zone_price',
    'price_zone_net_power': 'price_zone_net_power',
}


def results_window_opf(grid, excel_file_path, times=None):
    """Export ``window_opf_results`` tables to an Excel workbook.

    Parameters
    ----------
    grid : Grid
        Grid with ``window_opf_results`` from ``window_nl_opf`` /
        ``rolling_window_nl_opf``.
    excel_file_path : str
        Output ``.xlsx`` path (``.xlsx`` is appended if missing).
    times : dict, optional
        Timing metrics written to the ``Time`` sheet (same idea as
        ``results_ts_opf``).

    Notes
    -----
    Writes one sheet per DataFrame in ``grid.window_opf_results``, plus a
    ``scalars`` sheet for non-DataFrame entries (e.g. ``total_objective``).
    If ``grid.rolling_window_info`` is set, also writes a ``rolling_info``
    sheet with commit ranges.
    """
    if grid.window_opf_results is None:
        raise ValueError('grid.window_opf_results is None — nothing to export')

    if not str(excel_file_path).endswith('.xlsx'):
        excel_file_path = f'{excel_file_path}.xlsx'

    results = grid.window_opf_results
    used_sheets = set()

    def _unique_sheet(name):
        base = str(name)[:31]
        sheet = base
        n = 1
        while sheet in used_sheets:
            suffix = f'_{n}'
            sheet = f'{base[: 31 - len(suffix)]}{suffix}'
            n += 1
        used_sheets.add(sheet)
        return sheet

    with pd.ExcelWriter(excel_file_path) as writer:
        if times is not None:
            times_df = pd.DataFrame(
                list(times.items()), columns=['Metric', 'Time (s)']
            )
            times_df.to_excel(writer, sheet_name=_unique_sheet('Time'), index=False)

        info = getattr(grid, 'rolling_window_info', None)
        if info is not None:
            commits = info.get('commits') or []
            info_rows = [
                {
                    'window': i,
                    'commit_start': c[0] if c else None,
                    'commit_end': c[-1] if c else None,
                    'n_commit': len(c),
                }
                for i, c in enumerate(commits)
            ]
            meta = pd.DataFrame([{
                'window_size': info.get('window_size'),
                'n_windows': info.get('n_windows'),
                'start_frame': info.get('start_frame'),
                'end_frame': info.get('end_frame'),
            }])
            meta.to_excel(writer, sheet_name=_unique_sheet('rolling_meta'), index=False)
            if info_rows:
                pd.DataFrame(info_rows).to_excel(
                    writer, sheet_name=_unique_sheet('rolling_commits'), index=False
                )

        scalar_rows = []
        for key, val in results.items():
            if isinstance(val, pd.DataFrame):
                sheet = _unique_sheet(_WINDOW_OPF_SHEET_NAMES.get(key, key))
                val.to_excel(writer, sheet_name=sheet, index=False)
            elif isinstance(val, (int, float, np.floating, np.integer)) or val is None:
                scalar_rows.append({'name': key, 'value': val})
            else:
                raise TypeError(
                    f'window_opf_results[{key!r}] has unsupported type '
                    f'{type(val)!r} for Excel export'
                )
        if scalar_rows:
            pd.DataFrame(scalar_rows).to_excel(
                writer, sheet_name=_unique_sheet('scalars'), index=False
            )

    return excel_file_path
