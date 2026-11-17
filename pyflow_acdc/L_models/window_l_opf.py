# -*- coding: utf-8 -*-
"""Coupled linear AC(/DC) window OPF (frame blocks + parent SoC / H₂ / HP links).

Linear counterpart of :mod:`pyflow_acdc.NL_models.window_opf`. Uses
:func:`~pyflow_acdc.L_models.AC_OPF_L_model.opf_create_l_model_acdc` per frame
(BESS / HP P-only; hybrid via ``grid.ACmode`` / ``grid.DCmode``).
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone

import pyomo.environ as pyo

from ..ACDC_OPF import (
    calculate_objective,
    check_linear_opf_weights,
    fx_conv,
    obj_w_rule,
    opf_obj_l,
    translate_pyf_opf,
)
from ..grid_analysis import analyse_grid
from ..NL_models.window_opf import (
    _concat_rolling_results,
    _carry_state_from_results,
    _electrolysers_to_empty_after_rolling_commit,
    _empty_h2_tank,
    _rolling_commit_windows,
    _rolling_h2_empty_targets,
    _set_window_state_params,
    _slice_window_results,
    _snapshot_var_values,
    _sum_frame_objectives,
    _ts_inclusive_0based,
    export_window_opf_results,
    window_h2_constraints,
    window_heat_pump_constraints,
    window_soc_constraints,
)
from ..pyomo_model_solve import (
    build_only_solver_stats,
    pyomo_model_solve,
    reset_to_initialize,
)
from ..Time_series import _modify_parameters_l, update_grid_data
from .AC_OPF_L_model import export_acdc_l_model_to_pyflow_acdc, opf_create_l_model_acdc

__all__ = ['window_l_opf', 'rolling_window_l_opf']


def _create_l_frame_blocks(model, grid, frames, price_zones, weights_def, ts_base):
    base_model = pyo.ConcreteModel()
    opf_create_l_model_acdc(base_model, grid, TEP=False, window_block=True)

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
        _modify_parameters_l(grid, model.frame_model[i], price_zones, window_block=True)
        obj_rule = opf_obj_l(model.frame_model[i], grid, weights_def)
        model.frame_model[i].obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
        if grid.DCmode and any(conv.OPF_fx for conv in grid.Converters_ACDC):
            fx_conv(model.frame_model[i], grid)

    return storage_info, hydrogen_info, heat_pump_info


def _update_l_window_frame_params(model, grid, frames, ts_base, price_zones):
    for i in frames:
        abs_t = ts_base + i
        for ts in grid.Time_series:
            update_grid_data(grid, ts, abs_t, price_zone_restrictions=price_zones)
        _modify_parameters_l(grid, model.frame_model[i], price_zones, window_block=True)


def window_l_opf(
    grid,
    start=0,
    end=23,
    ObjRule=None,
    solver='glpk',
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
    """Build and solve a coupled linear AC(/DC) OPF over frames ``start…end``.

    Inclusive **0-based** absolute TS indices (same as
    :func:`~pyflow_acdc.window_nl_opf`). Hybrid via ``grid.ACmode`` /
    ``grid.DCmode``. BESS and heat pumps are P-only; no Q / S-circle.

    Rolling may pass ``_reuse`` and ``warm_start_mode`` ``'roll'`` / ``'hard'``.
    """
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")

    grid.reset_run_flags()
    analyse_grid(grid)

    if not grid.ESS and not grid.H2 and not grid.HP:
        raise ValueError(
            "window_l_opf requires at least one storage, electrolyser, "
            "or heat-pump element"
        )
    if not grid.Time_series:
        raise ValueError("window_l_opf requires grid.Time_series")

    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if end < start:
        raise ValueError(f"end ({end}) must be >= start ({start})")

    ts_len = len(grid.Time_series[0].data)
    if end >= ts_len:
        raise ValueError(
            f"end={end} out of range for Time_series length {ts_len} (0-based)"
        )

    weights_def, price_zones = obj_w_rule(grid, ObjRule)
    check_linear_opf_weights(weights_def)

    ts_base = start
    n_local = end - start + 1
    frames = list(range(n_local))

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
        model.name = f"Window L OPF [n={n_local}]"
        model.frames = pyo.Set(initialize=frames)
        model.frame_model = pyo.Block(model.frames)

        t1 = time.perf_counter()
        storage_info, hydrogen_info, heat_pump_info = _create_l_frame_blocks(
            model, grid, frames, price_zones, weights_def, ts_base
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
        _update_l_window_frame_params(model, grid, frames, ts_base, price_zones)
        _set_window_state_params(model, grid)
        t_modelupdate = time.perf_counter() - t1

    if build_only:
        model_res, solver_stats = build_only_solver_stats(solver, model)
        export_results = True
    else:
        model_res, solver_stats = pyomo_model_solve(
            model, grid, solver, tee, callback=callback)
        export_results = (
            model_res is not None and solver_stats.get('solution_found') is not False
        )
        if (
            not export_results
            and _reuse is not None
            and struct_key in _reuse
        ):
            entry = _reuse[struct_key]
            retry_mode = 'roll' if warm_start_mode == 'hard' else 'hard'
            if retry_mode == 'hard':
                reset_to_initialize(model, entry['initial_values'])
            _update_l_window_frame_params(model, grid, frames, ts_base, price_zones)
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
        _modify_parameters_l(
            grid, model.frame_model[last_local], price_zones, window_block=True)
        export_acdc_l_model_to_pyflow_acdc(model.frame_model[last_local], grid)

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


def rolling_window_l_opf(
    grid,
    start=1,
    end=None,
    window_size=24,
    soc_final_mode='every_m',
    soc_final_every_m=1,
    future_sight=0.0,
    ObjRule=None,
    solver='glpk',
    tee=False,
    callback=False,
    obj_scaling=1.0,
    build_only=False,
    print_step=False,
    warm_start_mode='roll',
):
    """Chain :func:`window_l_opf` over a TS horizon (linear AC(/DC) hybrid).

    Same indexing and ``future_sight`` semantics as
    :func:`~pyflow_acdc.rolling_window_nl_opf` (1-based inclusive ``start`` /
    ``end``).
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
    if not grid.ESS and not grid.H2 and not grid.HP:
        raise ValueError(
            "rolling_window_l_opf requires at least one storage, electrolyser, "
            "or heat-pump element"
        )
    if not grid.Time_series:
        raise ValueError("rolling_window_l_opf requires grid.Time_series")

    ts_len = len(grid.Time_series[0].data)
    idx0, idx1 = _ts_inclusive_0based(start, end, ts_len)
    commits = _rolling_commit_windows(idx0, idx1, window_size)
    n_win = len(commits)

    storage = list(grid.storage_elements)
    electrolysers = list(grid.electrolysers)
    orig_soc_final = {st.name: st.soc_final for st in storage}
    enforce_h2_mass = any(el.H2_mass_final is not None for el in electrolysers)
    h2_empty_targets = _rolling_h2_empty_targets(electrolysers)

    if grid.ESS and any(v is None for v in orig_soc_final.values()):
        missing = [n for n, v in orig_soc_final.items() if v is None]
        raise ValueError(
            "rolling_window_l_opf requires soc_final on all storage elements; "
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
                force_soc = True
            else:
                force_soc = ((k + 1) % soc_final_every_m == 0) or is_last
            h2_frames = None
            h2_scale = None

        if print_step:
            step_msg = (
                f"[{wall_start}] Rolling L-window {k + 1}/{n_win} "
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
        model, model_res, timing_info, solver_stats = window_l_opf(
            grid,
            start=solve_start,
            end=solve_end,
            ObjRule=ObjRule,
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
                f"Rolling L-window {k + 1}/{n_win} (frames {c_start}–{c_end}) "
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
        'linear': True,
    }
    timing_acc['windows'] = n_win
    timing_acc['frames'] = idx1 - idx0 + 1
    timing_acc['total_wall'] = time.perf_counter() - t_roll0
    timing_acc['wall_start'] = roll_wall_start
    timing_acc['wall_end'] = datetime.now(timezone.utc).isoformat()
    return None, None, timing_acc, window_stats
