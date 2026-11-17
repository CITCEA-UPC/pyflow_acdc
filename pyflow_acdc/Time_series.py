# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 15:38:12 2024

@author: BernardoCastro
"""

import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from scipy import stats as st

import time

from .grid_analysis import analyse_grid, grid_state, get_gen_p_min_eff
from .ACDC_PF import ac_power_flow, dc_power_flow, acdc_sequential
from .constants import (
    DEFAULT_TOLERANCE,
    DEFAULT_PF_MAX_ITER,
    BINARY_THRESHOLD,
    HOURS_PER_YEAR,
    NodeType,
    ConverterDCType,
    ObjComponent,
    default_obj_weights,
    TSType,
    TS_RENEWABLE_TYPES,
    TS_CONV_PF_TYPES,
    TS_STORAGE_PF_TYPES,
    TS_H2_PF_TYPES,
    TS_PF_TYPES,
    AcDcSide,
)


# Base __all__ with functions that don't require OPF
__all__ = ['time_series_pf',
           'ts_acdc_pf',
           'ts_ac_pf',
           'ts_dc_pf',
           'time_series_statistics',
           'update_grid_data',
           'update_grid_for_pf']

try:
    import pyomo.environ as pyo
    from .NL_models.ACDC_OPF_NL_model import (
        opf_create_nl_model_acdc,
        export_acdc_nl_model_to_pyflow_acdc)

    from .ACDC_OPF import (
        pyomo_model_solve,
        opf_obj,
        opf_obj_l,
        opf_step_results,
        opf_step_results_l,
        pack_variables,
        translate_pyf_opf,
        reset_to_initialize,
        calculate_objective,
        check_linear_opf_weights,
        fx_conv,
        obj_w_rule,
    )
    from .L_models.AC_OPF_L_model import (
        opf_create_l_model_acdc,
        export_acdc_l_model_to_pyflow_acdc,
    )
    pyomo_imp= True
    # Add OPF-dependent functions to __all__ only if pyomo is available
    __all__.extend(['ts_acdc_opf', 'ts_acdc_l_opf', 'results_ts_opf'])

except ImportError:
    pyomo_imp= False


def _to_dataframe(data):
    return pd.DataFrame(data).set_index('time')


def _find_value_from_cdf(cdf, x):
    for i in range(len(cdf)):
        if cdf[i] >= x:
            return i
    return None

def time_series_pf(grid):
    """Run PF over attached time series (auto-dispatch).

    Calls :func:`ts_dc_pf`, :func:`ts_ac_pf`, or :func:`ts_acdc_pf` depending on
    whether ``grid`` is DC-only, AC-only, or hybrid.

    Parameters
    ----------
    grid : Grid
        Grid with ``Time_series`` data attached.

    Returns
    -------
    None
        Populates ``grid.time_series_results`` by the dispatched
        function (:func:`ts_ac_pf`, :func:`ts_dc_pf`, or :func:`ts_acdc_pf`).

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> pyf.time_series_pf(grid)
    """
    analyse_grid(grid)
    if grid.ACmode and grid.DCmode:
        ts_acdc_pf(grid)
    elif grid.ACmode:
        ts_ac_pf(grid)
    elif grid.DCmode:
        ts_dc_pf(grid)

def combine_TS(ts_list, rep_year=False):
    """Combines multiple time series while maintaining the order of the input list.

    Args:
        ts_list: List of pandas DataFrames to combine, each with index 1-8760
        rep_year: If True, averages data hour by hour across years

    Returns:
        DataFrame containing combined or averaged time series data
    """
    # Concatenate DataFrames in order
    # save first 2 rows
    first_two_rows = [df.iloc[:2] for df in ts_list]
    # just save 1 data frame
    first_two_rows = first_two_rows[0]
    # ignore first two rows
    ts_list = [df.iloc[2:] for df in ts_list]
    # reset index
    ts_list = [df.reset_index(drop=True) for df in ts_list]
    combined_df = pd.concat(ts_list, axis=0, ignore_index=True)
    combined_df = pd.concat([first_two_rows, combined_df], axis=0, ignore_index=True)
    if rep_year:
        # Standardize all dataframes to 8760 hours
        processed_dfs = []
        for df in ts_list:
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # 'coerce' will convert invalid values to NaN
            if len(df) > HOURS_PER_YEAR:
                # remove 29th feb
                df = df.drop(df.index[1416:1440])
                df = df.reset_index(drop=True)
            elif len(df) < HOURS_PER_YEAR:
                df = df.reindex(range(HOURS_PER_YEAR), method='ffill')
            processed_dfs.append(df)

        # Calculate element-wise average across all dataframes
        new_df = pd.concat(processed_dfs).groupby(level=0).mean()
        return new_df, combined_df

    return combined_df

def update_grid_data(grid, ts, idx, price_zone_restrictions=False, use_clusters=False, n_clusters=None):
    """Apply one time-series sample to mutable grid fields before PF/OPF/TEP.

    Reads ``ts.data[idx]`` (or ``ts.data_clustered[n_clusters][idx]`` when
    ``use_clusters=True``) and updates linked grid objects according to
    ``ts.type`` (see :class:`~pyflow_acdc.constants.TSType`).

    Parameters
    ----------
    grid : Grid
        Grid whose attached price zones, nodes, and renewable objects are
        updated in place.
    ts : TimeSeries
        Series to apply. ``ts.element_name`` is matched against price-zone
        names, AC/DC node names, renewable-source names, or renewable-zone
        names depending on type.
    idx : int
        Index into ``ts.data`` or the clustered array for the current step.
    price_zone_restrictions : bool, optional
        When ``True``, also update price-zone restriction coefficients and
        limits for types ``a_CG``, ``b_CG``, ``c_CG``, ``PGL_min``, and
        ``PGL_max`` (in addition to the updates below).
    use_clusters : bool, optional
        Read from ``ts.data_clustered[n_clusters]`` instead of ``ts.data``.
    n_clusters : int, optional
        Cluster count key into ``ts.data_clustered``. Required when
        ``use_clusters=True``.

    Notes
    -----
    **``price``** — sets ``price`` on the matching price zone and on AC/DC
    nodes named ``ts.element_name``.

    **``Load``** — sets ``PLi_factor`` on the matching price zone and nodes.

    **Renewable types** (``WPP``, ``SPP``, etc.) — sets ``PRGi_available`` on
    the matching renewable zone and renewable source.

    Used internally by :func:`~pyflow_acdc.ts_acdc_pf`, :func:`~pyflow_acdc.ts_acdc_opf`,
    and TEP scenario-frame updates. Call directly when building custom
    time-step loops.

    Converter / BESS / H₂ PF setpoint series (``conv_P_DC``, ``storage_P``,
    ``h2_P``, etc.) are not handled here — use :func:`update_grid_for_pf`
    after any Droop/P ``P_DC`` reset so prescribed setpoints win.

    Heat-pump series (``hp_P_ref``, ``hp_Q_ref``, ``hp_E_min``, ``hp_E_max``)
    remain here (like ``h2_price``): they update element attributes for OPF and
    for PF nodal loads (``P_ref`` / ``Q_ref`` via :meth:`Grid.update_pq_ac`).
    """
    typ = ts.type
    if typ in TS_PF_TYPES:
        return

    if use_clusters:
        ts_data = ts.data_clustered[n_clusters]
    else:
        ts_data = ts.data
    # Pre-build dictionaries for fast lookups if not already present
    if not hasattr(grid, 'Price_Zones_dict'):
        grid.Price_Zones_dict = {pz.name: pz for pz in grid.Price_Zones}
    if not hasattr(grid, 'nodes_AC_dict'):
        grid.nodes_AC_dict = {node.name: node for node in grid.nodes_AC}
    if not hasattr(grid, 'nodes_DC_dict'):
        grid.nodes_DC_dict = {node.name: node for node in grid.nodes_DC}
    if not hasattr(grid, 'RenSource_zones_dict'):
        grid.RenSource_zones_dict = {zone.name: zone for zone in grid.RenSource_zones}
    if not hasattr(grid, 'RenSources_dict'):
        grid.RenSources_dict = {rs.name: rs for rs in grid.RenSources}

    if price_zone_restrictions:
        # Using dictionaries to directly access the Price Zone objects
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            if typ == TSType.A_CG:
                price_zone.a_base = ts_data[idx]
            elif typ == TSType.B_CG:
                price_zone.b = ts_data[idx]
            elif typ == TSType.C_CG:
                price_zone.c = ts_data[idx]
            elif typ == TSType.PGL_MIN:
                price_zone.PGL_min_base = ts_data[idx]
            elif typ == TSType.PGL_MAX:
                price_zone.PGL_max = ts_data[idx]
    elif typ in (TSType.A_CG, TSType.B_CG):
        # Cost-curve coeffs update zones (→ nodes → linked gens) without PZ-cost mode.
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            if typ == TSType.A_CG:
                price_zone.a_base = ts_data[idx]
            else:
                price_zone.b = ts_data[idx]

    if typ == TSType.PRICE:
        # Directly access price zone and nodes using dictionaries
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            price_zone.price = ts_data[idx]

        node = grid.nodes_AC_dict.get(ts.element_name, None)
        if node:
            node.price = ts_data[idx]

        node_dc = grid.nodes_DC_dict.get(ts.element_name, None)
        if node_dc:
            node_dc.price = ts_data[idx]

    elif typ == TSType.LOAD:
        # Directly access price zone and nodes using dictionaries
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            price_zone.PLi_factor = ts_data[idx]

        node = grid.nodes_AC_dict.get(ts.element_name, None)
        if node:
            node.PLi_factor = ts_data[idx]

        node_dc = grid.nodes_DC_dict.get(ts.element_name, None)
        if node_dc:
            node_dc.PLi_factor = ts_data[idx]

    elif typ in TS_RENEWABLE_TYPES:
        # Directly access RenSource_zones and RenSources using dictionaries
        zone = grid.RenSource_zones_dict.get(ts.element_name, None)
        if zone:
            zone.PRGi_available = ts_data[idx]

        rs = grid.RenSources_dict.get(ts.element_name, None)
        if rs:
            rs.PRGi_available = ts_data[idx]

    elif typ == TSType.H2_PRICE:
        if not hasattr(grid, 'electrolysers_dict'):
            grid.electrolysers_dict = {el.name: el for el in grid.electrolysers}
        el = grid.electrolysers_dict.get(ts.element_name, None)
        if el is None:
            raise ValueError(
                f"H2_PRICE time series element_name={ts.element_name!r} "
                f"does not match any electrolyser"
            )
        el.h2_price = ts_data[idx]

    elif typ in (TSType.HP_P_REF, TSType.HP_Q_REF, TSType.HP_E_MIN, TSType.HP_E_MAX):
        grid.heat_pumps_dict = {hp.name: hp for hp in grid.heat_pumps}
        hp = grid.heat_pumps_dict.get(ts.element_name, None)
        if hp is None:
            raise ValueError(
                f"{typ} time series element_name={ts.element_name!r} "
                f"does not match any heat pump"
            )
        if typ == TSType.HP_P_REF:
            hp.P_ref = float(ts_data[idx])
        elif typ == TSType.HP_Q_REF:
            hp.Q_ref = float(ts_data[idx])
        elif typ == TSType.HP_E_MIN:
            hp.E_min = float(ts_data[idx])
        else:
            hp.E_max = float(ts_data[idx])
        if hp.E_min > hp.E_max:
            raise ValueError(
                f"Heat pump {hp.name!r}: E_min ({hp.E_min}) > E_max ({hp.E_max}) "
                f"after applying {typ} at idx={idx}"
            )


def update_grid_for_pf(grid, ts, idx, use_clusters=False, n_clusters=None):
    """Apply one PF-setpoint time-series sample when ``ts`` is a PF setpoint type.

    Always safe to call for every attached series: non-PF types are ignored
    (no-op). PF types update known setpoints only (converters, BESS, H₂).

    Unlike :func:`update_grid_data` (loads, renewables, prices including
    ``h2_price``, and heat-pump ``hp_P_ref`` / ``hp_Q_ref`` / energy bounds),
    this only updates prescribed PF setpoints. Values are in
    **per-unit** on ``grid.S_base``.

    Accepted labels are listed in ``TS_PF_TYPES`` / ``TSType`` (see
    ``constants``). Converter ``P_DC`` / ``P_AC`` / ``Q_AC`` require matching
    DC ``type`` / ``AC_type``; ``storage_Q`` / ``h2_Q`` require AC connection.

    Heat-pump baselines are **not** PF setpoint types: keep them on
    :func:`update_grid_data`; PF nodal injection uses ``P_ref`` / ``Q_ref``.

    Parameters
    ----------
    grid : Grid
        Grid to update in place.
    ts : TimeSeries
        Any series; only PF setpoint types (``conv_*``, ``storage_*``,
        ``h2_P`` / ``h2_Q``) cause updates.
    idx : int
        Index into ``ts.data`` (or clustered data).
    use_clusters : bool, optional
        Read from ``ts.data_clustered[n_clusters]`` instead of ``ts.data``.
    n_clusters : int, optional
        Cluster count key when ``use_clusters=True``.

    Raises
    ------
    ValueError
        If ``ts`` is a PF setpoint type but the element name is unknown, or
        that setpoint is not valid for the element's control / connection side.
    """
    typ = ts.type
    if typ not in TS_PF_TYPES:
        return

    if use_clusters:
        ts_data = ts.data_clustered[n_clusters]
    else:
        ts_data = ts.data
    value = float(ts_data[idx])

    if typ in TS_CONV_PF_TYPES:
        if not hasattr(grid, 'Converters_ACDC_dict'):
            grid.Converters_ACDC_dict = {c.name: c for c in grid.Converters_ACDC}

        conv = grid.Converters_ACDC_dict.get(ts.element_name, None)
        if conv is None:
            raise ValueError(
                f"{typ} time series element_name={ts.element_name!r} "
                f"does not match any ACDC converter"
            )

        if typ == TSType.CONV_P_DC:
            if conv.type not in (ConverterDCType.P, ConverterDCType.DROOP):
                raise ValueError(
                    f"Converter {conv.name!r} (DC type={conv.type!r}, AC type="
                    f"{conv.AC_type!r}) does not have known PF setpoint P_DC"
                )
            conv.P_DC = value
            conv.Node_DC.Pconv = value
        elif typ == TSType.CONV_P_AC:
            if conv.type != ConverterDCType.PAC:
                raise ValueError(
                    f"Converter {conv.name!r} (DC type={conv.type!r}, AC type="
                    f"{conv.AC_type!r}) does not have known PF setpoint P_AC"
                )
            conv.P_AC = value
            conv.Node_AC.P_s = value
        elif typ == TSType.CONV_Q_AC:
            if conv.AC_type != NodeType.PQ:
                raise ValueError(
                    f"Converter {conv.name!r} (DC type={conv.type!r}, AC type="
                    f"{conv.AC_type!r}) does not have known PF setpoint Q_AC"
                )
            conv.Q_AC = value
        return

    if typ in TS_STORAGE_PF_TYPES:
        if not hasattr(grid, 'storage_elements_dict'):
            grid.storage_elements_dict = {
                s.name: s for s in grid.storage_elements
            }
        storage = grid.storage_elements_dict.get(ts.element_name, None)
        if storage is None:
            raise ValueError(
                f"{typ} time series element_name={ts.element_name!r} "
                f"does not match any storage element"
            )
        if typ == TSType.STORAGE_P:
            if value >= 0.0:
                storage.P_discharge = value
                storage.P_charge = 0.0
            else:
                storage.P_charge = -value
                storage.P_discharge = 0.0
        elif typ == TSType.STORAGE_Q:
            if storage.connected != AcDcSide.AC:
                raise ValueError(
                    f"Storage {storage.name!r} (connected={storage.connected!r}) "
                    f"does not have known PF setpoint Q"
                )
            storage.Q = value
        return

    if typ in TS_H2_PF_TYPES:
        if not hasattr(grid, 'electrolysers_dict'):
            grid.electrolysers_dict = {el.name: el for el in grid.electrolysers}
        el = grid.electrolysers_dict.get(ts.element_name, None)
        if el is None:
            raise ValueError(
                f"{typ} time series element_name={ts.element_name!r} "
                f"does not match any electrolyser"
            )
        if typ == TSType.H2_P:
            el.P_electrolyser = value
        elif typ == TSType.H2_Q:
            if el.connected != AcDcSide.AC:
                raise ValueError(
                    f"Electrolyser {el.name!r} (connected={el.connected!r}) "
                    f"does not have known PF setpoint Q"
                )
            el.Q_electrolyser = value
        return


def _converter_names_with_pf_ts(grid, ts_type):
    """Return converter names that have an attached PF setpoint series of ``ts_type``."""
    return {
        ts.element_name
        for ts in grid.Time_series
        if ts.type == ts_type
    }


def _apply_droop_p_dc_baseline(grid):
    """Restore Droop/P ``P_DC`` from ``Pconv_save`` when no ``conv_P_DC`` TS exists.

    Converters with a ``conv_P_DC`` series are left alone here; ``update_grid_for_pf``
    applies that series. Without a series, reset to the hour-0 reference so the
    previous PF solve does not leave a polluted droop/P setpoint.
    """
    ts_p_dc = _converter_names_with_pf_ts(grid, TSType.CONV_P_DC)
    for conv in grid.Converters_ACDC:
        if conv.type not in (ConverterDCType.DROOP, ConverterDCType.P):
            continue
        if conv.name in ts_p_dc:
            continue
        p_dc = grid.Pconv_save[conv.ConvNumber]
        conv.P_DC = p_dc
        conv.Node_DC.Pconv = p_dc


def _update_ac_nodes(grid, idx):
    row_data = {'time': idx+1}
    for node in grid.nodes_AC:
        if node.type == NodeType.SLACK:
            PGi = node.gen_P_injection().item()
            QGi = node.gen_Q_injection()
            if node.S_rating !=0:
                loading = np.sqrt(PGi**2 + QGi**2) / node.S_rating
            else:
                loading = 0
            row_data.update({
                f'Pg_{node.name}': PGi,
                f'Qg_{node.name}': QGi,
                f'Loading_{node.name}': loading
            })
    return row_data

def _update_converters(grid, idx):
    row_data = {'time': idx+1}
    for conv in grid.Converters_ACDC:
        S_AC = np.sqrt(conv.P_AC**2 + conv.Q_AC**2)
        P_DC = conv.P_DC
        row_data.update({
            f'Loading_{conv.name}': np.maximum(S_AC, np.abs(P_DC)) * grid.S_base / conv.MVA_max,
            f'{conv.name}_P_DC': P_DC
        })
    return row_data

def _obtain_line_power_from_grid(grid,idx):
    loadS_AC = np.zeros(grid.Num_Grids_AC) if grid.ACmode else np.zeros(0)
    loadP_DC = np.zeros(grid.Num_Grids_DC) if grid.DCmode else np.zeros(0)
    line_data = {'time': idx+1}

    if grid.ACmode:
        for line in (
            grid.lines_AC
            + grid.lines_AC_exp
            + grid.lines_AC_rec
            + grid.lines_AC_tf
            + grid.lines_AC_ct
        ):
            active_config = getattr(line, 'active_config', None)
            if active_config is not None and active_config < 0:
                continue
            G = grid.Graph_line_to_Grid_index_AC[line]
            load = line.apparent_MVA
            loadS_AC[G] += load
            line_data[f'AC_Load_{line.name}'] = line.loading
            line_data[f'AC_to_{line.name}']   = np.real(line.toS) * grid.S_base

    if grid.DCmode:
        for line in grid.lines_DC:
            G = grid.Graph_line_to_Grid_index_DC[line]
            load = line.power_MW
            loadP_DC[G] += load
            line_data[f'DC_Load_{line.name}'] = line.loading
            line_data[f'DC_to_{line.name}']   = line.toP * grid.S_base

    return line_data, loadS_AC, loadP_DC

def _calculate_line_loading_from_model(grid,model,idx):
    loadS_AC = np.zeros(grid.Num_Grids_AC)
    loadP_DC = np.zeros(grid.Num_Grids_DC)
    line_data = {'time': idx+1}



    if grid.ACmode:
        keys = sorted(model.PAC_from.keys())

        PAC_from = np.array([np.float64(pyo.value(model.PAC_from[k])) for k in keys])
        PAC_to = np.array([np.float64(pyo.value(model.PAC_to[k])) for k in keys])
        if hasattr(model, 'QAC_from'):
            QAC_from = np.array([np.float64(pyo.value(model.QAC_from[k])) for k in keys])
            QAC_to = np.array([np.float64(pyo.value(model.QAC_to[k])) for k in keys])
        else:
            # Linear AC OPF has P-only line flows (no Q).
            QAC_from = np.zeros_like(PAC_from)
            QAC_to = np.zeros_like(PAC_to)

        S_from   =np.sqrt(PAC_from**2+QAC_from**2)
        S_to     =np.sqrt(PAC_to**2+QAC_to**2)

        for line in grid.lines_AC:
            G = grid.Graph_line_to_Grid_index_AC[line]
            load = max(abs(S_from[line.lineNumber]), abs(S_to[line.lineNumber]))
            loadS_AC[G] += load
            line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.capacity_MVA
            line_data[f'AC_to_{line.name}']   = PAC_to[line.lineNumber]   * grid.S_base

        if grid.TEP_AC:
            lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}
            lines_AC_TEP_fromP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_from.items()}
            lines_AC_TEP_toP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_to.items()}
            lines_AC_TEP_fromQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_from.items()}
            lines_AC_TEP_toQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_to.items()}
            lines_AC_TEP_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_line_loss.items()}
            for line in grid.lines_AC_exp:
                G = grid.Graph_line_to_Grid_index_AC[line]
                l = line.lineNumber
                n_lines_ac = lines_AC_TEP[l]
                line.P_loss = lines_AC_TEP_P_loss[l] * n_lines_ac
                ac_from = (lines_AC_TEP_fromP[l] + 1j*lines_AC_TEP_fromQ[l]) * n_lines_ac
                ac_to = (lines_AC_TEP_toP[l] + 1j*lines_AC_TEP_toQ[l]) * n_lines_ac
                line_data[f'AC_to_{line.name}'] = ac_to
                load = max(abs(ac_from), abs(ac_to))
                loadS_AC[G] += load
                line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.capacity_MVA if line.capacity_MVA > 0 else 0
        if grid.REC_AC:
            lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in model.rec_branch.items()}
            lines_AC_REC_fromP = {k: {state: np.float64(pyo.value(model.rec_PAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toP = {k: {state: np.float64(pyo.value(model.rec_PAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_fromQ = {k: {state: np.float64(pyo.value(model.rec_QAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toQ = {k: {state: np.float64(pyo.value(model.rec_QAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.rec_PAC_line_loss.items()}

            for line in grid.lines_AC_rec:
                G = grid.Graph_line_to_Grid_index_AC[line]
                l = line.lineNumber
                line.rec_branch = True if lines_AC_REP[l] >= BINARY_THRESHOLD else False
                line.P_loss = lines_AC_REC_P_loss[l]
                state = 1 if line.rec_branch else 0
                ac_from = (lines_AC_REC_fromP[l][state] + 1j*lines_AC_REC_fromQ[l][state])
                ac_to = (lines_AC_REC_toP[l][state] + 1j*lines_AC_REC_toQ[l][state])
                line_data[f'AC_to_{line.name}'] = ac_to
                load = max(abs(ac_from), abs(ac_to))
                loadS_AC[G] += load
                if state == 1:
                    line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.MVA_rating_new
                else:
                    line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.MVA_rating


    if grid.DCmode:

        PDC_from = {k: np.float64(pyo.value(v)) for k, v in model.PDC_from.items()}
        PDC_to   = {k: np.float64(pyo.value(v)) for k, v in model.PDC_to.items()}
        n_lines_dc = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesDCP.items()}
        for line in grid.lines_DC:
            G = grid.Graph_line_to_Grid_index_DC[line]
            load = max(abs(PDC_from[line.lineNumber]), abs(PDC_to[line.lineNumber])) * n_lines_dc[line.lineNumber]
            loadP_DC[G] += load
            line_data[f'DC_Load_{line.name}'] = load * grid.S_base / line.capacity_MW if line.capacity_MW > 0 else 0
            line_data[f'DC_to_{line.name}'] = (
                PDC_to[line.lineNumber] * grid.S_base * n_lines_dc[line.lineNumber]
            )

    return line_data, loadS_AC, loadP_DC

def _calculate_grid_loading(grid, loadS_AC, loadP_DC,idx):
    grid_data_loading = {'time': idx+1}
    total_loading = 0
    total_rating = 0
    if grid.ACmode:
        total_rating += sum(grid.rating_grid_AC)
    if grid.DCmode:
        total_rating += sum(grid.rating_grid_DC)
    if grid.ACmode:
        for g in range(grid.Num_Grids_AC):
            loading = loadS_AC[g] * grid.S_base
            total_loading += loading
            grid_data_loading[f'Loading_Grid_AC_{g+1}'] = 0 if grid.rating_grid_AC[g] == 0 else loading / grid.rating_grid_AC[g]

    if grid.DCmode:
        for g in range(grid.Num_Grids_DC):
            loading = loadP_DC[g] * grid.S_base
            total_loading += loading
            grid_data_loading[f'Loading_Grid_DC_{g+1}'] = loading / grid.rating_grid_DC[g]

    grid_data_loading['Total'] = 0 if total_rating == 0 else total_loading /total_rating
    return grid_data_loading

def _calculate_price_zone_price(grid,idx):
    price_zone_price = {'time': idx+1}
    for m in grid.Price_Zones:
         price_zone_price[m.name]=m.price

    return price_zone_price

def _calculate_price_zone_price_from_model(grid,model,idx):
    price_zone_price = {'time': idx+1}
    prices    = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_price.items()}
    for m in grid.Price_Zones:
         price_zone_price[m.name]=prices[m.price_zone_num]

    return price_zone_price


def _calculate_pz_social_cost_kEUR_from_model(grid, model, idx):
    """Per price zone social cost of generation in k€ (model SocialCost / 1000), aligned with MS export."""
    row = {'time': idx + 1}
    if not getattr(grid, 'Price_Zones', None) or not hasattr(model, 'SocialCost'):
        return row
    for m in grid.Price_Zones:
        n_m = m.price_zone_num
        sc = np.float64(pyo.value(model.SocialCost[n_m]))
        row[m.name] = np.round(sc / 1000.0, decimals=4)
    return row


def _calculate_pz_p_known_mw_from_model(grid, model, idx):
    """
    Per price zone: sum of model P_known (pu) on zone nodes × S_base → MW.
    Same definition as MS export ``PZ_load`` / ``get_price_zone_data`` row_data_load.
    """
    row = {'time': idx + 1}
    if not getattr(grid, 'Price_Zones', None) or not hasattr(model, 'P_known_AC'):
        return row
    for m in grid.Price_Zones:
        load_pu = 0.0
        for node in m.nodes_AC:
            load_pu += pyo.value(model.P_known_AC[node.nodeNumber])
        if grid.DCmode and hasattr(model, 'P_known_DC'):
            for node in m.nodes_DC:
                load_pu += pyo.value(model.P_known_DC[node.nodeNumber])
        row[m.name] = np.round(load_pu * grid.S_base, decimals=2)
    return row


def _calculate_net_price_zone_power_from_model(grid, model, idx):
    net_price_zone_power = {'time': idx + 1}
    if hasattr(model, 'PN'):
        pn_values = {k: np.float64(pyo.value(v)) for k, v in model.PN.items()}
        for m in grid.Price_Zones:
            if m.price_zone_num in pn_values:
                net_price_zone_power[m.name] = pn_values[m.price_zone_num] * grid.S_base
        return net_price_zone_power

    if not getattr(grid, 'Price_Zones', None):
        return net_price_zone_power

    for m in grid.Price_Zones:
        pm_pu = 0.0
        for node in m.nodes_AC:
            n = node.nodeNumber
            if hasattr(model, 'P_known_AC'):
                pm_pu += pyo.value(model.P_known_AC[n])
            if hasattr(model, 'PGi_ren'):
                pm_pu += pyo.value(model.PGi_ren[n])
            if hasattr(model, 'PGi_opt'):
                pm_pu += pyo.value(model.PGi_opt[n])
        for node in m.nodes_DC:
            n = node.nodeNumber
            if hasattr(model, 'P_known_DC'):
                pm_pu += pyo.value(model.P_known_DC[n])
            if hasattr(model, 'PGi_ren_DC'):
                pm_pu += pyo.value(model.PGi_ren_DC[n])
        net_price_zone_power[m.name] = pm_pu * grid.S_base
    return net_price_zone_power
def _calculate_res_available_from_model(grid, model, idx):
    res_available = {'time': idx + 1}
    if hasattr(model, 'ren_sources'):
        res_available_values = {k: np.float64(pyo.value(v)) for k, v in model.P_renSource.items()}
        np_rsgen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_rsgen.items()}
        for rs in grid.RenSources:
            res_available[rs.name] = res_available_values[rs.rsNumber] * np_rsgen_values[rs.rsNumber] * grid.S_base
    return res_available

def _calculate_pn_min_max_from_model(grid, model, idx):
    """
    Compute PN lower/upper bounds (MW) from the model's PN bounds.

    In Pyomo these are the price-zone power bounds: model.PGL_min / model.PGL_max.
    They bound model.PN with: PGL_min <= PN <= PGL_max.
    """
    pn_min = {'time': idx + 1}
    pn_max = {'time': idx + 1}
    a = {'time': idx + 1}
    b = {'time': idx + 1}
    if hasattr(model, 'PGL_min') and hasattr(model, 'PGL_max'):
        pgl_min_values = {k: np.float64(pyo.value(v)) for k, v in model.PGL_min.items()}
        pgl_max_values = {k: np.float64(pyo.value(v)) for k, v in model.PGL_max.items()}
        a_values = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_a.items()}
        b_values = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_b.items()}
        for m in grid.Price_Zones:
            # model.PGL_min/max are indexed by price_zone_num
            if m.price_zone_num in pgl_min_values:
                pn_min[m.name] = pgl_min_values[m.price_zone_num] * grid.S_base
            if m.price_zone_num in pgl_max_values:
                pn_max[m.name] = pgl_max_values[m.price_zone_num] * grid.S_base
            if m.price_zone_num in a_values:
                a[m.name] = a_values[m.price_zone_num]
            if m.price_zone_num in b_values:
                b[m.name] = b_values[m.price_zone_num]
    return pn_min, pn_max, a, b


def ts_acdc_pf(grid, start=1, end=None,print_step=False,tol_lim=DEFAULT_TOLERANCE, maxIter=DEFAULT_PF_MAX_ITER):
    """Run sequential AC/DC power flow over a time-series window.

    Updates grid data each hour, runs :func:`~pyflow_acdc.acdc_sequential`, and
    stores results in ``grid.time_series_results``.

    Parameters
    ----------
    grid : Grid
        Hybrid AC/DC grid with ``Time_series`` data attached.
    start : int, optional
        First hour (1-based).
    end : int, optional
        Last hour (inclusive); defaults to the series length.
    print_step : bool, optional
        Print the current hour index while running.
    tol_lim : float, optional
        Power-flow tolerance.
    maxIter : int, optional
        Maximum power-flow iterations per hour.

    Returns
    -------
    None
        Populates ``grid.time_series_results`` with:

        - ``PF_results``: node voltages and power flows
        - ``ac_loading``: AC line loading percentages
        - ``dc_loading``: DC line loading percentages
        - ``ac_MW_to``: AC line active power flows
        - ``dc_MW_to``: DC line active power flows
        - ``converter_loading``: converter loading percentages
        - ``grid_loading``: overall grid loading

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> pyf.ts_acdc_pf(grid, start=1, end=24)
    """
    idx = start-1
    TS_len = len(grid.Time_series[0].data)
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)

    Time_series_res = []
    Time_series_line_res = []
    Time_series_conv_res = []
    Time_series_grid_loading = []
    analyse_grid(grid)
    # saving droop configuration to reset each time, if not it takes power set from previous point.
    grid.Pconv_save = np.zeros(grid.nconv)
    for conv in grid.Converters_ACDC:
        grid.Pconv_save[conv.ConvNumber] = conv.P_DC

    while idx < max_time:
        # Droop/P: either hour-0 Pconv_save (no TS) or conv_P_DC via update_grid_for_pf.
        if grid.ACmode and grid.DCmode:
            _apply_droop_p_dc_baseline(grid)

        for ts in grid.Time_series:
            if ts.type in TS_PF_TYPES:
                update_grid_for_pf(grid, ts, idx)
            else:
                update_grid_data(grid, ts, idx)

        if grid.ACmode and grid.DCmode:
            acdc_sequential(grid,QLimit=False)
        elif grid.ACmode:
            t,tol,_hist=ac_power_flow(grid,tol_lim, maxIter)
        elif grid.DCmode:
            t,tol,_hist=dc_power_flow(grid,tol_lim, maxIter)

        with ThreadPoolExecutor() as executor:
            # Submit the functions to the executor
            future_row_data = executor.submit(_update_ac_nodes, grid, idx)
            future_line_data = executor.submit(_obtain_line_power_from_grid, grid, idx)
            if grid.ACmode and grid.DCmode:
                future_conv_data = executor.submit(_update_converters, grid, idx)
                conv_data = future_conv_data.result()
            else:
                conv_data = None
            # Wait for the results
            row_data = future_row_data.result()
            line_data, loadS_AC, loadP_DC = future_line_data.result()

        grid_data_loading = _calculate_grid_loading(grid, loadS_AC, loadP_DC,idx)
        row_data['time'] = idx+1
        Time_series_res.append(row_data)
        if conv_data is not None:
            conv_data['time'] = idx+1
            Time_series_conv_res.append(conv_data)
        line_data['time'] = idx+1
        Time_series_line_res.append(line_data)
        grid_data_loading['time'] = idx+1
        Time_series_grid_loading.append(grid_data_loading)


        if print_step:
            print(idx+1)
        idx += 1

    # Create the DataFrame from the list of rows
    grid.time_series_results['PF_results']   = _to_dataframe(Time_series_res)
    line_data_df = _to_dataframe(Time_series_line_res)
    # Split line time-series into explicit loading and MW-to datasets
    ac_loading = line_data_df.filter(like='AC_Load_', axis=1)
    dc_loading = line_data_df.filter(like='DC_Load_', axis=1)
    ac_mw_to = line_data_df.filter(like='AC_to_', axis=1)
    dc_mw_to = line_data_df.filter(like='DC_to_', axis=1)

    # Remove prefixes from column names for both DataFrames
    ac_loading.columns = ac_loading.columns.str.replace('AC_Load_', '', regex=False)
    dc_loading.columns = dc_loading.columns.str.replace('DC_Load_', '', regex=False)
    ac_mw_to.columns = ac_mw_to.columns.str.replace('AC_to_', '', regex=False)
    dc_mw_to.columns = dc_mw_to.columns.str.replace('DC_to_', '', regex=False)

    grid.time_series_results['ac_loading'] = ac_loading
    grid.time_series_results['dc_loading'] = dc_loading
    grid.time_series_results['ac_MW_to'] = ac_mw_to
    grid.time_series_results['dc_MW_to'] = dc_mw_to

    if grid.ACmode and grid.DCmode:
        grid.time_series_results['converter_loading'] = _to_dataframe(Time_series_conv_res)
    grid.time_series_results['grid_loading'] = _to_dataframe(Time_series_grid_loading)

    grid.Time_series_ran = True


def ts_ac_pf(grid, start=1, end=None, print_step=False, tol_lim=DEFAULT_TOLERANCE, maxIter=DEFAULT_PF_MAX_ITER):
    """Run AC-only power flow over a time-series window.

    Parameters
    ----------
    grid : Grid
        AC grid with ``Time_series`` data attached.
    start : int, optional
        First hour (1-based).
    end : int, optional
        Last hour (inclusive); defaults to the series length.
    print_step : bool, optional
        Print the current hour index while running.
    tol_lim : float, optional
        Power-flow tolerance.
    maxIter : int, optional
        Maximum power-flow iterations per hour.

    Returns
    -------
    None
        Populates ``grid.time_series_results`` with:

        - ``PF_results``: node voltages and power flows
        - ``ac_loading``: AC line loading percentages
        - ``ac_MW_to``: AC line active power flows
        - ``grid_loading``: overall grid loading

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> pyf.ts_ac_pf(grid, start=1, end=24)
    """
    idx = start-1
    TS_len = len(grid.Time_series[0].data)
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)

    Time_series_res = []
    Time_series_line_res = []
    Time_series_grid_loading = []
    analyse_grid(grid)

    while idx < max_time:
        for ts in grid.Time_series:
            if ts.type in TS_PF_TYPES:
                update_grid_for_pf(grid, ts, idx)
            else:
                update_grid_data(grid, ts, idx)
        ac_power_flow(grid, tol_lim, maxIter)

        with ThreadPoolExecutor() as executor:
            future_row_data = executor.submit(_update_ac_nodes, grid, idx)
            future_line_data = executor.submit(_obtain_line_power_from_grid, grid, idx)
            row_data = future_row_data.result()
            line_data, loadS_AC, loadP_DC = future_line_data.result()

        grid_data_loading = _calculate_grid_loading(grid, loadS_AC, loadP_DC, idx)
        row_data['time'] = idx+1
        Time_series_res.append(row_data)
        line_data['time'] = idx+1
        Time_series_line_res.append(line_data)
        grid_data_loading['time'] = idx+1
        Time_series_grid_loading.append(grid_data_loading)

        if print_step:
            print(idx+1)
        idx += 1

    grid.time_series_results['PF_results'] = _to_dataframe(Time_series_res)
    line_data_df = _to_dataframe(Time_series_line_res)
    ac_loading = line_data_df.filter(like='AC_Load_', axis=1)
    ac_mw_to = line_data_df.filter(like='AC_to_', axis=1)
    ac_loading.columns = ac_loading.columns.str.replace('AC_Load_', '', regex=False)
    ac_mw_to.columns = ac_mw_to.columns.str.replace('AC_to_', '', regex=False)
    grid.time_series_results['ac_loading'] = ac_loading
    grid.time_series_results['ac_MW_to'] = ac_mw_to
    grid.time_series_results['grid_loading'] = _to_dataframe(Time_series_grid_loading)

    grid.Time_series_ran = True


def ts_dc_pf(grid, start=1, end=None, print_step=False, tol_lim=DEFAULT_TOLERANCE, maxIter=DEFAULT_PF_MAX_ITER):
    """Run DC-only power flow over a time-series window.

    Parameters
    ----------
    grid : Grid
        DC grid with ``Time_series`` data attached.
    start : int, optional
        First hour (1-based).
    end : int, optional
        Last hour (inclusive); defaults to the series length.
    print_step : bool, optional
        Print the current hour index while running.
    tol_lim : float, optional
        Power-flow tolerance.
    maxIter : int, optional
        Maximum power-flow iterations per hour.

    Returns
    -------
    None
        Populates ``grid.time_series_results`` with:

        - ``PF_results``: node voltages and power flows
        - ``dc_loading``: DC line loading percentages
        - ``dc_MW_to``: DC line active power flows
        - ``grid_loading``: overall grid loading

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> pyf.ts_dc_pf(grid, start=1, end=24)
    """
    idx = start-1
    TS_len = len(grid.Time_series[0].data)
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)

    Time_series_res = []
    Time_series_line_res = []
    Time_series_grid_loading = []
    analyse_grid(grid)

    while idx < max_time:
        for ts in grid.Time_series:
            if ts.type in TS_PF_TYPES:
                update_grid_for_pf(grid, ts, idx)
            else:
                update_grid_data(grid, ts, idx)
        dc_power_flow(grid, tol_lim, maxIter)

        with ThreadPoolExecutor() as executor:
            future_row_data = executor.submit(_update_ac_nodes, grid, idx)
            future_line_data = executor.submit(_obtain_line_power_from_grid, grid, idx)
            row_data = future_row_data.result()
            line_data, loadS_AC, loadP_DC = future_line_data.result()

        grid_data_loading = _calculate_grid_loading(grid, loadS_AC, loadP_DC, idx)
        row_data['time'] = idx+1
        Time_series_res.append(row_data)
        line_data['time'] = idx+1
        Time_series_line_res.append(line_data)
        grid_data_loading['time'] = idx+1
        Time_series_grid_loading.append(grid_data_loading)

        if print_step:
            print(idx+1)
        idx += 1

    grid.time_series_results['PF_results'] = _to_dataframe(Time_series_res)
    line_data_df = _to_dataframe(Time_series_line_res)
    dc_loading = line_data_df.filter(like='DC_Load_', axis=1)
    dc_mw_to = line_data_df.filter(like='DC_to_', axis=1)
    dc_loading.columns = dc_loading.columns.str.replace('DC_Load_', '', regex=False)
    dc_mw_to.columns = dc_mw_to.columns.str.replace('DC_to_', '', regex=False)
    grid.time_series_results['dc_loading'] = dc_loading
    grid.time_series_results['dc_MW_to'] = dc_mw_to
    grid.time_series_results['grid_loading'] = _to_dataframe(Time_series_grid_loading)

    grid.Time_series_ran = True


def _modify_parameters_l(grid, model, Price_Zones=False, window_block=False):
    """Update mutable Params on a linear OPF model from current grid TS state."""
    opf_data = translate_pyf_opf(grid, Price_Zones=Price_Zones)
    AC_info = opf_data['AC_info']
    DC_info = opf_data['DC_info']
    gen_info = opf_data['gen_info']
    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    lf, _, _, _, _ = gen_AC_info
    P_renSource, _, _ = gen_rs_info

    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)

    if grid.ACmode:
        _, AC_nodes_info, _, _, _, _ = AC_info
        _, _, _, _, P_know, _, _ = AC_nodes_info
        for idx, val in P_know.items():
            model.P_known_AC[idx].set_value(val)
        for idx, val in lf.items():
            model.lf[idx].set_value(val)
        for gen in grid.Generators:
            if not getattr(gen, 'is_ext_grid', False):
                continue
            g = gen.genNumber
            np_gen_value = pyo.value(model.np_gen[g])
            pmax_eff = gen.Max_pow_gen * np_gen_value
            pmin_eff = get_gen_p_min_eff(gen, np_gen_value)
            model.PGi_gen[g].setlb(pmin_eff)
            model.PGi_gen[g].setub(pmax_eff)

    if grid.DCmode:
        _, DC_nodes_info, _, _ = DC_info
        _, _, _, P_known_DC, _ = DC_nodes_info
        for idx, val in P_known_DC.items():
            model.P_known_DC[idx].set_value(val)
        if grid.Generators_DC:
            lf_DC, _, _, _, _ = gen_DC_info
            for idx, val in lf_DC.items():
                model.lf_dc[idx].set_value(val)

    if grid.ESS:
        for storage in grid.storage_elements:
            s = storage.storageNumber
            if not window_block:
                model.SoC_prev[s].set_value(float(storage.soc_initial))
            model.soc_ref[s].set_value(float(storage.soc_ref))

    if grid.H2 and not window_block:
        for el in grid.electrolysers:
            model.mass_H2_prev[el.electrolyserNumber].set_value(
                float(el.H2_mass_initial)
            )

    if grid.HP:
        for hp in grid.heat_pumps:
            h = hp.heatPumpNumber
            if not window_block:
                model.E_heat_pump_prev[h].set_value(float(hp.E_state))
            model.hp_p_ref[h].set_value(float(hp.P_ref))
            model.hp_e_min[h].set_value(float(hp.E_min))
            model.hp_e_max[h].set_value(float(hp.E_max))


def _modify_parameters(grid,model,Price_Zones,window_block=False):
    opf_data = translate_pyf_opf(grid,Price_Zones=Price_Zones)
    AC_info = opf_data['AC_info']
    DC_info = opf_data['DC_info']
    Price_Zone_info = opf_data['Price_Zone_info']
    gen_info = opf_data['gen_info']
    ACmode = grid.ACmode
    DCmode = grid.DCmode
    AC_Lists, AC_nodes_info, AC_lines_info,EXP_info,REP_info,CT_info = AC_info

    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    lf,qf,fc,np_gen,lista_gen = gen_AC_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info

    _,_,_,_, P_know,Q_know,price = AC_nodes_info
    if DCmode:
        DC_Lists,DC_nodes_info,_,_ = DC_info
        lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC = gen_DC_info
        _, _ ,_,P_known_DC,price_dc  = DC_nodes_info

    _,Price_Zone_lim = Price_Zone_info

    price_zone_as,price_zone_bs,PGL_min, PGL_max = Price_Zone_lim

    if Price_Zones:
        for idx, val in price_zone_as.items():
            model.price_zone_a[idx].set_value(val)
        for idx, val in price_zone_bs.items():
            model.price_zone_b[idx].set_value(val)
        for idx, val in PGL_min.items():
            model.PGL_min[idx].set_value(val)
        for idx, val in PGL_max.items():
            model.PGL_max[idx].set_value(val)
    else:
        if ACmode:
            for idx, val in price.items():
                model.price[idx].set_value(val)
            for idx, val in lf.items():
                model.lf[idx].set_value(val)
        if DCmode:
            for idx, val in price_dc.items():
                 model.price_dc[idx].set_value(val)
            for idx, val in lf_DC.items():
                model.lf_dc[idx].set_value(val)

    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)

    if ACmode:
        for idx, val in P_know.items():
            model.P_known_AC[idx].set_value(val)
        for idx, val in Q_know.items():
            model.Q_known_AC[idx].set_value(val)
        if hasattr(model, 'P_load_eff'):
            for gen in grid.Generators:
                model.P_load_eff[gen.genNumber].set_value(gen.p_load_eff)
        # Keep ext-grid generator bounds synchronized with scenario/investment load factors
        # when the OPF model is reused across time steps.
        if hasattr(model, 'PGi_gen') and not hasattr(model, 'PGi_lower_bound'):
            for gen in grid.Generators:
                if not getattr(gen, 'is_ext_grid', False):
                    continue
                g = gen.genNumber
                np_gen_value = pyo.value(model.np_gen[g]) if hasattr(model, 'np_gen') else gen.np_gen
                pmax_eff = gen.Max_pow_gen * np_gen_value
                pmin_eff = get_gen_p_min_eff(gen, np_gen_value)
                model.PGi_gen[g].setlb(pmin_eff)
                model.PGi_gen[g].setub(pmax_eff)

    if DCmode:
        for idx, val in P_known_DC.items():
            model.P_known_DC[idx].set_value(val)
    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)

    if grid.ESS:
        for storage in grid.storage_elements:
            s = storage.storageNumber
            if not window_block:
                model.SoC_prev[s].set_value(float(storage.soc_initial))
            model.soc_ref[s].set_value(float(storage.soc_ref))

    if grid.H2 and not window_block:
            for el in grid.electrolysers:
                model.mass_H2_prev[el.electrolyserNumber].set_value(
                    float(el.H2_mass_initial)
                )

    if grid.HP:
        for hp in grid.heat_pumps:
            h = hp.heatPumpNumber
            if not window_block:
                model.E_heat_pump_prev[h].set_value(float(hp.E_state))
            model.hp_p_ref[h].set_value(float(hp.P_ref))
            model.hp_q_ref[h].set_value(float(hp.Q_ref))
            model.hp_e_min[h].set_value(float(hp.E_min))
            model.hp_e_max[h].set_value(float(hp.E_max))


def _carry_storage_h2_state_from_model(grid, model):
    """Write solved SoC / H₂ / HP state onto elements and set next-hour initials."""
    if grid.ESS:
        for storage in grid.storage_elements:
            s = storage.storageNumber
            soc = float(pyo.value(model.SoC[s]))
            model.SoC_prev[s].set_value(soc)
            storage.P_charge = float(pyo.value(model.P_storage_charge[s]))
            storage.P_discharge = float(pyo.value(model.P_storage_discharge[s]))
            storage.Q = float(pyo.value(model.Q_storage[s]))
            storage.SoC = soc
            storage.soc_initial = soc

    if grid.H2:
        for el in grid.electrolysers:
            e = el.electrolyserNumber
            mass = float(pyo.value(model.mass_H2[e]))
            el.mass_H2 = mass
            el.H2_mass_initial = mass
            model.mass_H2_prev[e].set_value(mass)
            el.P_electrolyser = float(pyo.value(model.P_electrolyser[e]))

    if grid.HP:
        for hp in grid.heat_pumps:
            h = hp.heatPumpNumber
            e_state = float(pyo.value(model.E_heat_pump[h]))
            hp.P_shed = float(pyo.value(model.P_shed[h]))
            hp.E_state = e_state
            hp.P_hp = float(pyo.value(model.P_heat_pump[h]))
            if hasattr(model, "Q_shed"):
                hp.Q_shed = float(pyo.value(model.Q_shed[h]))
            if hasattr(model, "Q_heat_pump"):
                hp.Q_hp = float(pyo.value(model.Q_heat_pump[h]))
            model.E_heat_pump_prev[h].set_value(e_state)


def _maybe_empty_h2_after_myopic_step(grid, model, hour_1based):
    """Out-of-opt tank empty after a myopic hour (``empty_tank_cycle``).

    ``None`` → never empty. Positive ``N`` → empty when ``hour_1based % N == 0``.
    Caller must only invoke when ``grid.H2`` is true.
    """
    for el in grid.electrolysers:
        n = el.empty_tank_cycle
        if n is None:
            continue
        if hour_1based % n != 0:
            continue
        el.empty_tank()
        model.mass_H2_prev[el.electrolyserNumber].set_value(0.0)


def _ts_storage_soc_row(grid, time_1based):
    row = {'time': time_1based}
    for storage in grid.storage_elements:
        row[storage.name] = np.float64(storage.SoC)
    return row


def _ts_storage_power_row(grid, time_1based):
    """Net injection MW (discharge − charge) per storage element."""
    row = {'time': time_1based}
    for storage in grid.storage_elements:
        row[storage.name] = np.float64(
            (storage.P_discharge - storage.P_charge) * storage.S_base
        )
    return row


def _ts_heat_pump_power_row(grid, time_1based):
    row = {'time': time_1based}
    for hp in grid.heat_pumps:
        row[hp.name] = np.float64(hp.P_hp * hp.np_hp * hp.S_base)
    return row


def _ts_heat_pump_energy_row(grid, time_1based):
    row = {'time': time_1based}
    for hp in grid.heat_pumps:
        row[hp.name] = np.float64(hp.E_state)
    return row


def ts_acdc_opf(
    grid,
    start=1,
    end=None,
    ObjRule=None,
    price_zone_restrictions=False,
    expand=False,
    print_step=False,
    limit_flow_rate=True,
    use_clusters=False,
    n_clusters=None,
    solver='ipopt',
    obj_scaling=1.0,
    warm_start_mode='roll',
    export_to_grid=True,
    build_only=False,
):
    """Run sequential AC/DC OPF over a time-series window.

    Parameters
    ----------
    grid : Grid
        Hybrid AC/DC grid with ``Time_series`` data attached.
    start : int, optional
        First hour (1-based).
    end : int, optional
        Last hour (inclusive); defaults to the series length.
    ObjRule : dict, optional
        Objective-component weights; see :ref:`Objective Functions <obj_functions>`.
    price_zone_restrictions : bool, optional
        Add price-zone restrictions to the model [1]_.
    expand : bool, optional
        Enable price-zone import expansion.
    print_step : bool, optional
        Print the current hour index while running.
    limit_flow_rate : bool, optional
        Enforce line thermal/flow-rate limits in the OPF model.
    use_clusters : bool, optional
        Use clustered time-series data instead of hourly data.
    n_clusters : int, optional
        Cluster count to use when ``use_clusters`` is True.
    solver : str, optional
        Pyomo solver name.
    obj_scaling : float, optional
        Divide the objective by this factor for numerical conditioning.
    warm_start_mode : {'roll', 'hard'}, optional
        Warm-start strategy between hours.
    export_to_grid : bool, optional
        Export the final model state back onto ``grid``.
    build_only : bool, optional
        If ``True``, build and update the Pyomo model each hour but skip the
        solver. Post-processing (including
        :func:`_calculate_line_loading_from_model`) still runs using the
        model's current variable values (typically the initializer).

    Returns
    -------
    dict
        Timing information with keys ``Create``, ``Update model Avg``,
        ``Solve model Avg``, and ``Export``.

        Also populates ``grid.time_series_results`` with:

        - ``converter_p_dc``: converter active power on the DC side
        - ``converter_q_ac``: converter reactive power on the AC side
        - ``converter_p_ac``: converter active power on the AC side
        - ``converter_loading``: converter loading percentages
        - ``real_load_opf``: real load per node
        - ``real_power_opf``: real power per generator
        - ``reactive_power_opf``: reactive power per generator
        - ``curtailment``: curtailment values
        - ``grid_loading``: loading by unsynchronised grids
        - ``prices_by_zone``: prices by price zone
        - ``PZ_cost_of_generation``: price-zone generation cost
        - ``PZ_load``: price-zone load
        - ``net_price_zone_power``: net price-zone power
        - ``PZ_lb``, ``PZ_ub``: price-zone power bounds
        - ``a``, ``b``: price-zone cost coefficients
        - ``res_available``: available renewable energy
        - ``ac_loading``, ``dc_loading``: line loading percentages
        - ``ac_MW_to``, ``dc_MW_to``: line active power flows
        - ``storage_soc``: BESS SoC [pu] per element (when ``grid.ESS``)
        - ``storage_power``: BESS net injection [MW] per element (when ``grid.ESS``)
    """
    idx = start-1
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")
    TS_len = len(grid.Time_series[0].data)
    total_solve_time  = 0
    total_update_time = 0
    count = 0
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)

    Time_series_voltages = []
    Time_series_line_res = []
    Time_series_conv_res = []
    Time_series_grid_loading = []

    Time_series_Opt_res_P_conv_AC = []
    Time_series_Opt_res_Q_conv_AC = []
    Time_series_Opt_res_P_conv_DC = []
    Time_series_Opt_res_P_Load    = []
    Time_series_Opt_res_P_extGrid = []
    Time_series_Opt_res_Q_extGrid =[]
    Time_series_Opt_curtailment   =[]

    Time_series_price = []
    Time_series_PZ_cost_kEUR = []
    Time_series_PZ_load = []
    Time_series_net_price_zone_power = []
    Time_series_PN_min = []
    Time_series_PN_max = []
    Time_series_a = []
    Time_series_b = []
    Time_series_res_available = []
    Time_series_storage_soc = []
    Time_series_storage_power = []
    Time_series_heat_pump_power = []
    Time_series_heat_pump_energy = []

    weights_def = default_obj_weights()

    # If user provides specific weights, merge them with the default
    if ObjRule is not None:
       for key in ObjRule:
           if key in weights_def:
               weights_def[key]['w'] = ObjRule[key]

    PV_set=False
    if  weights_def[ObjComponent.PZ_COST_OF_GENERATION]['w']!=0 :
        price_zone_restrictions=True
    if  weights_def[ObjComponent.CURTAILMENT_RED]['w']!=0 :
        grid.CurtCost=True


    def _snapshot_initial_values(model_obj):
        values = {}
        for var_obj in model_obj.component_objects(pyo.Var, active=True):
            values[var_obj.name] = {index: var_obj[index].value for index in var_obj}
        return values

    def _build_ts_model():
        model_obj = pyo.ConcreteModel()
        model_obj.name = "TS AC/DC hybrid OPF"

        opf_create_nl_model_acdc(model_obj,grid,PV_set,price_zone_restrictions,limit_flow_rate=limit_flow_rate)

        obj_rule_local = opf_obj(model_obj,grid,weights_def)
        if obj_scaling != 1.0:
            obj_rule_local = obj_rule_local / obj_scaling
        model_obj.obj = pyo.Objective(rule=obj_rule_local, sense=pyo.minimize)
        model_obj.obj_scaling = obj_scaling
        return model_obj

    analyse_grid(grid)
    t1 = time.perf_counter()
    model = _build_ts_model()
    t2 = time.perf_counter()
    t_modelcreate = t2 - t1
    initial_values = _snapshot_initial_values(model)
    t_minus_1_values = None

    if expand:
        for price_zone in grid.Price_Zones:
            price_zone.expand_import = True

    infeasible= 0
    inf_list=[]
    if not use_clusters:
        n_clusters = 1
    else:
        available_clusters = list(grid.Time_series[0].data_clustered.keys())
        if len(available_clusters) == 0:
            use_clusters = False
            n_clusters = None
            print("No clusters available")
            print("Please run clustering first,running full Time series")
        elif n_clusters is not None:
            if n_clusters not in available_clusters:
                raise ValueError(f"Invalid cluster number {n_clusters}. Available clusters: {available_clusters}")
        elif len(available_clusters) == 1:
            n_clusters = available_clusters[0]
        else:
            raise ValueError(f"Multiple clusters available: {available_clusters}. Pass n_clusters= to select one.")
        max_time  = len(grid.Time_series[0].data_clustered[n_clusters])

    while idx < max_time:
        for ts in grid.Time_series:
            update_grid_data(grid,ts, idx,price_zone_restrictions,use_clusters=use_clusters,n_clusters=n_clusters)
        Total_load, min_generation, max_generation = grid_state(grid)

        if Total_load < min_generation or Total_load > max_generation:
            print(f"Total load {Total_load} is out of bounds {min_generation} and {max_generation}")
            inf_list.append(idx+1)
            idx += 1
            infeasible += 1

            continue
        t1= time.perf_counter()
        if warm_start_mode == 'hard':
            reset_to_initialize(model, initial_values)

        _modify_parameters(grid,model,price_zone_restrictions)
        t2= time.perf_counter()
        t_modelupdate = t2-t1

        if build_only:
            t_modelsolve = 0.0
        else:
            results, solver_stats = pyomo_model_solve(model,grid,solver,suppress_warnings=True)
            termination_condition = str((solver_stats or {}).get('termination_condition') or '').lower()
            solution_found = bool((solver_stats or {}).get('solution_found', False))
            if (results is None) or (not solution_found):
                # Retry with opposite initialization strategy for this timestep.
                retry_mode = 'roll' if warm_start_mode == 'hard' else 'hard'
                if print_step:
                    print(f"{idx+1} Failed with {warm_start_mode}")
                retry_model = _build_ts_model()
                if retry_mode == 'hard':
                    reset_to_initialize(retry_model, initial_values)
                elif t_minus_1_values is not None:
                    reset_to_initialize(retry_model, t_minus_1_values)
                _modify_parameters(grid,retry_model,price_zone_restrictions)
                retry_results, retry_stats = pyomo_model_solve(retry_model,grid,solver,suppress_warnings=True)
                retry_solution_found = bool((retry_stats or {}).get('solution_found', False))
                if retry_results is not None and retry_solution_found:
                    model = retry_model
                    results, solver_stats = retry_results, retry_stats
                    if print_step:
                        print(f"{idx+1} Passed with {retry_mode} returning to {warm_start_mode}")
                else:
                    infeasible += 1
                    inf_list.append(idx+1)
                    if print_step:
                        reason = str((retry_stats or {}).get('termination_condition') or termination_condition or 'solver error').lower()
                        print(f"{idx+1} Failed with {retry_mode}")
                        print(f"{idx+1} skipped ({reason})")
                    idx += 1
                    continue
            t_modelsolve = (solver_stats or {}).get('time')
            if t_modelsolve is None:
                t_modelsolve = 0.0

        total_update_time+= t_modelupdate
        total_solve_time += t_modelsolve

        count += 1
        [opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,opt_res_Loading_conv] = opf_step_results(model,grid)


        opt_res_curtailment['time'] = idx+1
        opt_res_P_conv_AC['time'] = idx+1
        opt_res_Q_conv_AC['time'] = idx+1
        opt_res_P_conv_DC['time'] = idx+1
        opt_P_load['time']        = idx+1
        opt_res_P_extGrid['time'] = idx+1
        opt_res_Q_extGrid['time'] = idx+1
        opt_res_Loading_conv['time'] = idx+1


        line_data, loadS_AC, loadP_DC = _calculate_line_loading_from_model( grid, model,idx)


        grid_data_loading = _calculate_grid_loading(grid, loadS_AC, loadP_DC,idx)

        if price_zone_restrictions:
            price_zone_price = _calculate_price_zone_price_from_model(grid,model,idx)
        else:
            price_zone_price = _calculate_price_zone_price(grid,idx)
        net_price_zone_power = _calculate_net_price_zone_power_from_model(grid, model, idx)

        pz_cost_kEUR = _calculate_pz_social_cost_kEUR_from_model(grid, model, idx)
        pz_load_mw = _calculate_pz_p_known_mw_from_model(grid, model, idx)

        pn_min, pn_max, a, b = _calculate_pn_min_max_from_model(grid, model, idx)

        res_available = _calculate_res_available_from_model(grid, model, idx)

        Time_series_price.append(price_zone_price)
        Time_series_PZ_cost_kEUR.append(pz_cost_kEUR)
        Time_series_PZ_load.append(pz_load_mw)
        Time_series_net_price_zone_power.append(net_price_zone_power)
        Time_series_PN_min.append(pn_min)
        Time_series_PN_max.append(pn_max)
        Time_series_a.append(a)
        Time_series_b.append(b)
        Time_series_res_available.append(res_available)
        Time_series_conv_res.append(opt_res_Loading_conv)
        Time_series_line_res.append(line_data)
        Time_series_grid_loading.append(grid_data_loading)


        Time_series_Opt_res_P_conv_AC.append(opt_res_P_conv_AC)
        Time_series_Opt_res_Q_conv_AC.append(opt_res_Q_conv_AC)
        Time_series_Opt_res_P_conv_DC.append(opt_res_P_conv_DC)
        Time_series_Opt_res_P_Load.append(opt_P_load)
        Time_series_Opt_res_P_extGrid.append(opt_res_P_extGrid)
        Time_series_Opt_res_Q_extGrid.append(opt_res_Q_extGrid)
        Time_series_Opt_curtailment.append(opt_res_curtailment)

        if grid.ESS or grid.H2 or grid.HP:
            _carry_storage_h2_state_from_model(grid, model)
            if grid.H2:
                _maybe_empty_h2_after_myopic_step(grid, model, idx + 1)
        if grid.ESS:
            Time_series_storage_soc.append(_ts_storage_soc_row(grid, idx + 1))
            Time_series_storage_power.append(_ts_storage_power_row(grid, idx + 1))
        if grid.HP:
            Time_series_heat_pump_power.append(_ts_heat_pump_power_row(grid, idx + 1))
            Time_series_heat_pump_energy.append(_ts_heat_pump_energy_row(grid, idx + 1))

        t_minus_1_values = _snapshot_initial_values(model)

        if print_step:
            print(idx+1)
        idx += 1


    if export_to_grid:
        t1 = time.perf_counter()
        export_acdc_nl_model_to_pyflow_acdc(model, grid, price_zone_restrictions)
        for obj in weights_def:
            weights_def[obj]['v'] = calculate_objective(grid, obj)
        t2 = time.perf_counter()
        t_modelexport = t2 - t1
    else:
        t_modelexport = 0.0

    # Persist timestep indices that failed / were skipped during the TS loop.
    # These are 1-based indices (matching the public TS time step numbering).
    grid.ts_infeasible_indices = sorted(set(inf_list))
    ts_results = pack_variables(Time_series_conv_res,Time_series_line_res,Time_series_grid_loading,
                            Time_series_Opt_res_P_conv_AC,Time_series_Opt_res_Q_conv_AC,Time_series_Opt_res_P_conv_DC,
                            Time_series_Opt_res_P_extGrid,Time_series_Opt_res_Q_extGrid,Time_series_Opt_curtailment,
                            Time_series_Opt_res_P_Load,Time_series_price,Time_series_PZ_cost_kEUR,Time_series_PZ_load,Time_series_net_price_zone_power,
                            Time_series_PN_min,Time_series_PN_max,Time_series_a,Time_series_b,Time_series_res_available,
                            Time_series_storage_soc, Time_series_storage_power,
                            Time_series_heat_pump_power, Time_series_heat_pump_energy)

    av_t_modelsolve = total_solve_time / count if count else 0.0
    av_t_modelupdate=total_update_time / count if count else 0.0

    # Always persist time-series result frames for plotting/reporting.
    # export_to_grid only controls whether final model state is written back to grid objects.
    _save_TS_to_grid(grid, ts_results, infeasible)
    grid.OPF_obj = weights_def
    grid.OPF_run = True
    grid.Time_series_ran = True




    timing_info = {
    "Create": t_modelcreate,
    "Update model Avg": av_t_modelupdate,
    "Solve model Avg": av_t_modelsolve,
    "Export": t_modelexport,
    }

    return timing_info


def ts_acdc_l_opf(
    grid,
    start=1,
    end=None,
    ObjRule=None,
    print_step=False,
    solver='glpk',
    obj_scaling=1.0,
    warm_start_mode='roll',
    export_to_grid=True,
    build_only=False,
):
    """Run sequential linear AC(/DC) OPF over a time-series window.

    Myopic twin of :func:`ts_acdc_opf` using
    :func:`~pyflow_acdc.L_models.AC_OPF_L_model.opf_create_l_model_acdc`.
    Supports ``Energy_cost`` / ``H2_sale`` only (same as snapshot linear OPF).
    Carries BESS SoC / H₂ mass / HP energy between hours when ``grid.ESS`` /
    ``grid.H2`` / ``grid.HP``. Hybrid via ``grid.ACmode`` / ``grid.DCmode``;
    ``fx_conv`` when converters have ``OPF_fx``. ``SoC_deviation`` is rejected
    (quadratic). Heat pumps are P-only in the linear stack (no Q model objects).

    Parameters
    ----------
    grid : Grid
        Network with ``Time_series`` attached.
    start, end : int, optional
        Inclusive **1-based** hour indices (same as :func:`ts_acdc_opf`).
    ObjRule : dict or None, optional
        Objective weights; linear path accepts ``Energy_cost`` / ``H2_sale``.
    print_step : bool, optional
        Print the current hour index while running.
    solver : str, optional
        Pyomo LP solver name.
    obj_scaling : float, optional
        Divide the objective by this factor.
    warm_start_mode : {'roll', 'hard'}, optional
        Variable warm-start policy between hours.
    export_to_grid : bool, optional
        Export the last solved model state onto ``grid``.
    build_only : bool, optional
        Build / update only (no solve); still writes TS result frames.

    Returns
    -------
    dict
        Timing keys ``Create``, ``Update model Avg``, ``Solve model Avg``,
        ``Export``.
    """
    if not pyomo_imp:
        raise ImportError("ts_acdc_l_opf requires Pyomo")

    idx = start - 1
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")
    TS_len = len(grid.Time_series[0].data)
    total_solve_time = 0
    total_update_time = 0
    count = 0
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)

    Time_series_line_res = []
    Time_series_conv_res = []
    Time_series_grid_loading = []
    Time_series_Opt_res_P_conv_AC = []
    Time_series_Opt_res_Q_conv_AC = []
    Time_series_Opt_res_P_conv_DC = []
    Time_series_Opt_res_P_Load = []
    Time_series_Opt_res_P_extGrid = []
    Time_series_Opt_res_Q_extGrid = []
    Time_series_Opt_curtailment = []
    Time_series_price = []
    Time_series_PZ_cost_kEUR = []
    Time_series_PZ_load = []
    Time_series_net_price_zone_power = []
    Time_series_PN_min = []
    Time_series_PN_max = []
    Time_series_a = []
    Time_series_b = []
    Time_series_res_available = []
    Time_series_storage_soc = []
    Time_series_storage_power = []
    Time_series_heat_pump_power = []
    Time_series_heat_pump_energy = []

    analyse_grid(grid)
    weights_def, price_zones = obj_w_rule(grid, ObjRule)
    check_linear_opf_weights(weights_def)

    def _snapshot_initial_values(model_obj):
        values = {}
        for var_obj in model_obj.component_objects(pyo.Var, active=True):
            values[var_obj.name] = {
                index: var_obj[index].value for index in var_obj}
        return values

    def _build_ts_l_model():
        model_obj = pyo.ConcreteModel()
        model_obj.name = "TS AC/DC linear OPF"
        opf_create_l_model_acdc(model_obj, grid, TEP=False, window_block=False)
        obj_rule_local = opf_obj_l(model_obj, grid, weights_def)
        if obj_scaling != 1.0:
            obj_rule_local = obj_rule_local / obj_scaling
        model_obj.obj = pyo.Objective(rule=obj_rule_local, sense=pyo.minimize)
        model_obj.obj_scaling = obj_scaling
        if grid.DCmode and any(conv.OPF_fx for conv in grid.Converters_ACDC):
            fx_conv(model_obj, grid)
        return model_obj

    t1 = time.perf_counter()
    model = _build_ts_l_model()
    t2 = time.perf_counter()
    t_modelcreate = t2 - t1
    initial_values = _snapshot_initial_values(model)
    t_minus_1_values = None

    infeasible = 0
    inf_list = []

    while idx < max_time:
        for ts in grid.Time_series:
            update_grid_data(grid, ts, idx, price_zones)
        Total_load, min_generation, max_generation = grid_state(grid)

        if Total_load < min_generation or Total_load > max_generation:
            print(
                f"Total load {Total_load} is out of bounds "
                f"{min_generation} and {max_generation}")
            inf_list.append(idx + 1)
            idx += 1
            infeasible += 1
            continue

        t1 = time.perf_counter()
        if warm_start_mode == 'hard':
            reset_to_initialize(model, initial_values)
        _modify_parameters_l(grid, model, price_zones, window_block=False)
        t2 = time.perf_counter()
        t_modelupdate = t2 - t1

        if build_only:
            t_modelsolve = 0.0
        else:
            results, solver_stats = pyomo_model_solve(
                model, grid, solver, suppress_warnings=True)
            solution_found = bool(
                (solver_stats or {}).get('solution_found', False))
            if (results is None) or (not solution_found):
                retry_mode = 'roll' if warm_start_mode == 'hard' else 'hard'
                if print_step:
                    print(f"{idx+1} Failed with {warm_start_mode}")
                retry_model = _build_ts_l_model()
                if retry_mode == 'hard':
                    reset_to_initialize(retry_model, initial_values)
                elif t_minus_1_values is not None:
                    reset_to_initialize(retry_model, t_minus_1_values)
                _modify_parameters_l(
                    grid, retry_model, price_zones, window_block=False)
                retry_results, retry_stats = pyomo_model_solve(
                    retry_model, grid, solver, suppress_warnings=True)
                retry_solution_found = bool(
                    (retry_stats or {}).get('solution_found', False))
                if retry_results is not None and retry_solution_found:
                    model = retry_model
                    results, solver_stats = retry_results, retry_stats
                    if print_step:
                        print(
                            f"{idx+1} Passed with {retry_mode} "
                            f"returning to {warm_start_mode}")
                else:
                    infeasible += 1
                    inf_list.append(idx + 1)
                    if print_step:
                        print(f"{idx+1} Failed with {retry_mode}")
                    idx += 1
                    continue
            t_modelsolve = (solver_stats or {}).get('time')
            if t_modelsolve is None:
                t_modelsolve = 0.0

        total_update_time += t_modelupdate
        total_solve_time += t_modelsolve
        count += 1

        (
            opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,
            opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,
            opt_res_Loading_conv,
        ) = opf_step_results_l(model, grid)

        opt_res_curtailment['time'] = idx + 1
        opt_res_P_conv_AC['time'] = idx + 1
        opt_res_Q_conv_AC['time'] = idx + 1
        opt_res_P_conv_DC['time'] = idx + 1
        opt_P_load['time'] = idx + 1
        opt_res_P_extGrid['time'] = idx + 1
        opt_res_Q_extGrid['time'] = idx + 1
        opt_res_Loading_conv['time'] = idx + 1

        line_data, loadS_AC, loadP_DC = _calculate_line_loading_from_model(
            grid, model, idx)
        grid_data_loading = _calculate_grid_loading(
            grid, loadS_AC, loadP_DC, idx)
        price_zone_price = _calculate_price_zone_price(grid, idx)
        net_price_zone_power = _calculate_net_price_zone_power_from_model(
            grid, model, idx)
        pz_cost_kEUR = _calculate_pz_social_cost_kEUR_from_model(
            grid, model, idx)
        pz_load_mw = _calculate_pz_p_known_mw_from_model(grid, model, idx)
        pn_min, pn_max, a, b = _calculate_pn_min_max_from_model(
            grid, model, idx)
        res_available = _calculate_res_available_from_model(grid, model, idx)

        Time_series_price.append(price_zone_price)
        Time_series_PZ_cost_kEUR.append(pz_cost_kEUR)
        Time_series_PZ_load.append(pz_load_mw)
        Time_series_net_price_zone_power.append(net_price_zone_power)
        Time_series_PN_min.append(pn_min)
        Time_series_PN_max.append(pn_max)
        Time_series_a.append(a)
        Time_series_b.append(b)
        Time_series_res_available.append(res_available)
        Time_series_conv_res.append(opt_res_Loading_conv)
        Time_series_line_res.append(line_data)
        Time_series_grid_loading.append(grid_data_loading)
        Time_series_Opt_res_P_conv_AC.append(opt_res_P_conv_AC)
        Time_series_Opt_res_Q_conv_AC.append(opt_res_Q_conv_AC)
        Time_series_Opt_res_P_conv_DC.append(opt_res_P_conv_DC)
        Time_series_Opt_res_P_Load.append(opt_P_load)
        Time_series_Opt_res_P_extGrid.append(opt_res_P_extGrid)
        Time_series_Opt_res_Q_extGrid.append(opt_res_Q_extGrid)
        Time_series_Opt_curtailment.append(opt_res_curtailment)

        if grid.ESS or grid.H2 or grid.HP:
            _carry_storage_h2_state_from_model(grid, model)
            if grid.H2:
                _maybe_empty_h2_after_myopic_step(grid, model, idx + 1)
        if grid.ESS:
            Time_series_storage_soc.append(_ts_storage_soc_row(grid, idx + 1))
            Time_series_storage_power.append(
                _ts_storage_power_row(grid, idx + 1))
        if grid.HP:
            Time_series_heat_pump_power.append(
                _ts_heat_pump_power_row(grid, idx + 1))
            Time_series_heat_pump_energy.append(
                _ts_heat_pump_energy_row(grid, idx + 1))

        t_minus_1_values = _snapshot_initial_values(model)
        if print_step:
            print(idx + 1)
        idx += 1

    if export_to_grid:
        t1 = time.perf_counter()
        export_acdc_l_model_to_pyflow_acdc(model, grid)
        for obj in weights_def:
            weights_def[obj]['v'] = calculate_objective(grid, obj)
        t2 = time.perf_counter()
        t_modelexport = t2 - t1
    else:
        t_modelexport = 0.0

    grid.ts_infeasible_indices = sorted(set(inf_list))
    ts_results = pack_variables(
        Time_series_conv_res, Time_series_line_res, Time_series_grid_loading,
        Time_series_Opt_res_P_conv_AC, Time_series_Opt_res_Q_conv_AC,
        Time_series_Opt_res_P_conv_DC,
        Time_series_Opt_res_P_extGrid, Time_series_Opt_res_Q_extGrid,
        Time_series_Opt_curtailment,
        Time_series_Opt_res_P_Load, Time_series_price,
        Time_series_PZ_cost_kEUR, Time_series_PZ_load,
        Time_series_net_price_zone_power,
        Time_series_PN_min, Time_series_PN_max, Time_series_a, Time_series_b,
        Time_series_res_available,
        Time_series_storage_soc, Time_series_storage_power,
        Time_series_heat_pump_power, Time_series_heat_pump_energy,
    )

    av_t_modelsolve = total_solve_time / count if count else 0.0
    av_t_modelupdate = total_update_time / count if count else 0.0
    _save_TS_to_grid(grid, ts_results, infeasible)
    grid.OPF_obj = weights_def
    grid.OPF_run = True
    grid.Time_series_ran = True

    return {
        "Create": t_modelcreate,
        "Update model Avg": av_t_modelupdate,
        "Solve model Avg": av_t_modelsolve,
        "Export": t_modelexport,
    }


def _save_TS_to_grid (grid,ts_results,infeasible):
    # Create the DataFrame from the list of rows
    (Time_series_conv_res,Time_series_line_res,Time_series_grid_loading,
    Time_series_Opt_res_P_conv_AC,Time_series_Opt_res_Q_conv_AC,Time_series_Opt_res_P_conv_DC,
    Time_series_Opt_res_P_extGrid,Time_series_Opt_res_Q_extGrid,Time_series_Opt_curtailment,
    Time_series_Opt_res_P_Load,Time_series_price,Time_series_PZ_cost_kEUR,Time_series_PZ_load,Time_series_net_price_zone_power,
    Time_series_PN_min,Time_series_PN_max,Time_series_a,Time_series_b,Time_series_res_available,
    Time_series_storage_soc, Time_series_storage_power,
    Time_series_heat_pump_power, Time_series_heat_pump_energy)= ts_results

    grid.time_series_results['converter_p_dc'] = _to_dataframe(Time_series_Opt_res_P_conv_DC)
    grid.time_series_results['converter_q_ac'] = _to_dataframe(Time_series_Opt_res_Q_conv_AC)
    grid.time_series_results['converter_p_ac'] = _to_dataframe(Time_series_Opt_res_P_conv_AC)
    grid.time_series_results['converter_loading'] = _to_dataframe(Time_series_conv_res)

    grid.time_series_results['real_load_opf'] = _to_dataframe(Time_series_Opt_res_P_Load)
    grid.time_series_results['real_power_opf'] = _to_dataframe(Time_series_Opt_res_P_extGrid)
    grid.time_series_results['reactive_power_opf'] = _to_dataframe(Time_series_Opt_res_Q_extGrid)

    grid.time_series_results['curtailment'] = _to_dataframe(Time_series_Opt_curtailment)

    line_data_df = _to_dataframe(Time_series_line_res)
    grid.time_series_results['grid_loading'] = _to_dataframe(Time_series_grid_loading)

    grid.time_series_results['prices_by_zone'] = _to_dataframe(Time_series_price)
    grid.time_series_results['PZ_cost_of_generation'] = _to_dataframe(Time_series_PZ_cost_kEUR)
    grid.time_series_results['PZ_load'] = _to_dataframe(Time_series_PZ_load)
    grid.time_series_results['net_price_zone_power'] = _to_dataframe(Time_series_net_price_zone_power)
    grid.time_series_results['PZ_lb'] = _to_dataframe(Time_series_PN_min)
    grid.time_series_results['PZ_ub'] = _to_dataframe(Time_series_PN_max)
    grid.time_series_results['a'] = _to_dataframe(Time_series_a)
    grid.time_series_results['b'] = _to_dataframe(Time_series_b)
    grid.time_series_results['res_available'] = _to_dataframe(Time_series_res_available)
    if Time_series_storage_soc:
        grid.time_series_results['storage_soc'] = _to_dataframe(Time_series_storage_soc)
    if Time_series_storage_power:
        grid.time_series_results['storage_power'] = _to_dataframe(Time_series_storage_power)
    if Time_series_heat_pump_power:
        grid.time_series_results['heat_pump_p'] = _to_dataframe(Time_series_heat_pump_power)
    if Time_series_heat_pump_energy:
        grid.time_series_results['heat_pump_energy_state'] = _to_dataframe(Time_series_heat_pump_energy)
    # Split line time-series into explicit loading and MW-to datasets
    ac_loading = line_data_df.filter(like='AC_Load_', axis=1)
    dc_loading = line_data_df.filter(like='DC_Load_', axis=1)
    ac_mw_to = line_data_df.filter(like='AC_to_', axis=1)
    dc_mw_to = line_data_df.filter(like='DC_to_', axis=1)

    # Remove prefixes from column names for both DataFrames
    ac_loading.columns = ac_loading.columns.str.replace('AC_Load_', '', regex=False)
    dc_loading.columns = dc_loading.columns.str.replace('DC_Load_', '', regex=False)
    ac_mw_to.columns = ac_mw_to.columns.str.replace('AC_to_', '', regex=False)
    dc_mw_to.columns = dc_mw_to.columns.str.replace('DC_to_', '', regex=False)

    grid.time_series_results['ac_loading'] = ac_loading
    grid.time_series_results['dc_loading'] = dc_loading
    grid.time_series_results['ac_MW_to'] = ac_mw_to
    grid.time_series_results['dc_MW_to'] = dc_mw_to


    for line in (grid.lines_AC + grid.lines_AC_tf + grid.lines_AC_rec + grid.lines_AC_exp):
        col = line.name
        if col in ac_loading:
            max_frac = float(ac_loading[col].max())
            avg_frac = float(ac_loading[col].mean())
            setattr(line, 'ts_max_loading', max_frac*100)
            setattr(line, 'ts_avg_loading', avg_frac*100)    # fraction of rating (0..)


    # DC lines
    for line in grid.lines_DC:
        col = line.name
        if col in dc_loading:
            max_frac = float(dc_loading[col].max())
            avg_frac = float(dc_loading[col].mean())
            setattr(line, 'ts_max_loading', max_frac*100)
            setattr(line, 'ts_avg_loading', avg_frac*100)


    grouped_columns_load = {}
    grouped_columns = {}
    # Group columns based on prefix in external generation data

    for col in grid.time_series_results['real_load_opf'].columns:
         prefix = ''.join(filter(str.isalpha, col))
         if prefix not in grouped_columns_load:
             grouped_columns_load[prefix] = []
         grouped_columns_load[prefix].append(col)
    Ext_Load_joined = pd.DataFrame()
    for prefix, cols in grouped_columns_load.items():
         Ext_Load_joined[f'{prefix}'] =grid.time_series_results['real_load_opf'][cols].sum(axis=1)
    Ext_Load_joined['Total']=grid.time_series_results['real_load_opf'].sum(axis=1)

    for col in grid.time_series_results['real_power_opf'].columns:
         if 'RenSource' in col:
            prefix = 'RenSource'  # Group all RenSource together
         else:
            prefix = ''.join(filter(str.isalpha, col))
         if prefix not in grouped_columns:
             grouped_columns[prefix] = []
         grouped_columns[prefix].append(col)
    Ext_Gen_joined = pd.DataFrame()
     # Aggregate columns with the same prefix for external generation
    for prefix, cols in grouped_columns.items():
         Ext_Gen_joined[f'{prefix}'] =grid.time_series_results['real_power_opf'][cols].sum(axis=1)


    if 'RenSource' in Ext_Gen_joined.columns:
        Ext_Gen_joined  = Ext_Gen_joined[[col for col in Ext_Gen_joined.columns if col != 'RenSource'] + ['RenSource']]
    grid.ts_infeasible_count = infeasible
    grid.time_series_results['real_load_by_zone']  = Ext_Load_joined
    # Track the *model* P_known_AC sign convention aggregated by price zone.
    # In opf_step_results: opt_P_load = -P_known_AC, so real_load_by_zone is the sign-flipped view.
    grid.time_series_results['real_load_known_by_zone'] = -Ext_Load_joined
    grid.time_series_results['real_power_by_zone'] = Ext_Gen_joined
    grid.time_series_results['reactive_power_opf'].columns = grid.time_series_results['reactive_power_opf'].columns.str.replace('Reactor_' , '',regex=False)
    grid.time_series_results['real_power_opf'].columns = grid.time_series_results['real_power_opf'].columns.str.replace('RenSource_','', regex=False)

def time_series_statistics(grid, curtail=0.99,over_loading=0.9):

    a = grid.Time_series

    static = []  # Initialize stats as an empty DataFrame

    for ts in a:
            # Calculate statistics for each time series
            mean = np.mean(ts.data)  # Calculate mean
            median = np.median(ts.data)  # Calculate median
            maxim = np.max(ts.data)  # Calculate maximum
            minim = np.min(ts.data)  # Calculate minimum
            mode, count = st.mode(np.round(ts.data, decimals=3))
            iqr = st.iqr(ts.data)

            sorted_data = np.sort(ts.data)
            cumulative_prob = np.linspace(0, 1, len(sorted_data))

            i = _find_value_from_cdf(cumulative_prob, curtail)
            name=ts.name
            if 'loading' in name:
                n = sum(1 for num in ts.data if num > over_loading)
            else:
                n = sum(1 for num in ts.data if num > over_loading * maxim)

            # Create a dictionary to store the statistics
            stats_dict = {
                'Element': name,
                'Mean': mean,
                'Median': median,
                'Maximum': maxim,
                'Minimum': minim,
                'Mode3dec': mode,
                'Mode_count': count,
                'IQR': iqr,
                f'{curtail*100}%': sorted_data[i].item(),
                f'Number above {over_loading*100}%': n,
               }

            # Convert the dictionary to a DataFrame and append it to the stats DataFrame
            static.append(stats_dict)

    if grid.Time_series_ran == True:
        # Create a new dictionary with marked DataFrames
        marked_time_series_results = {
            'PF_results': grid.time_series_results['PF_results'].add_suffix('_PF'),
            'ac_loading': grid.time_series_results['ac_loading'].add_suffix('_ACloading'),
            'dc_loading': grid.time_series_results['dc_loading'].add_suffix('_DCloading'),
            'grid_loading': grid.time_series_results['grid_loading'].add_suffix('_gridloading'),
            'ac_MW_to': grid.time_series_results['ac_MW_to'].add_suffix('_ACMWto'),
            'dc_MW_to': grid.time_series_results['dc_MW_to'].add_suffix('_DCMWto'),
            'converter_p_dc': grid.time_series_results['converter_p_dc'].add_suffix('_convP_DC'),
            'converter_q_ac': grid.time_series_results['converter_q_ac'].add_suffix('_convQ_AC'),
            'converter_p_ac': grid.time_series_results['converter_p_ac'].add_suffix('_convP_AC'),
            'real_load_by_zone': grid.time_series_results['real_load_by_zone'].add_suffix('_PL_OPF'),
            'real_load_known_by_zone': grid.time_series_results['real_load_known_by_zone'].add_suffix('_PL_Pknown'),
            'real_power_opf': grid.time_series_results['real_power_opf'].add_suffix('_P_OPF'),
            'reactive_power_opf': grid.time_series_results['reactive_power_opf'].add_suffix('_Q_OPF'),
            'curtailment': grid.time_series_results['curtailment'].add_suffix('_curtail'),
            'converter_loading': grid.time_series_results['converter_loading'].add_suffix('_convloading'),
            'real_power_by_zone': grid.time_series_results['real_power_by_zone'].add_suffix('_zoneP'),
            'prices_by_zone': grid.time_series_results['prices_by_zone'].add_suffix('_price'),
            'PZ_cost_of_generation': grid.time_series_results.get('PZ_cost_of_generation', pd.DataFrame()).add_suffix('_PZcost'),
            'PZ_load': grid.time_series_results.get('PZ_load', pd.DataFrame()).add_suffix('_PZload'),
            'net_price_zone_power': grid.time_series_results['net_price_zone_power'].add_suffix('_netPZ'),
            'a': grid.time_series_results['a'].add_suffix('_a'),
            'b': grid.time_series_results['b'].add_suffix('_b'),
        }

        # Merge non-empty DataFrames
        merged_df = pd.concat([df for df in marked_time_series_results.values() if not df.empty], axis=1)

        for col in merged_df:
            # Calculate statistics for each column in merged_df
            mean = merged_df[col].mean()  # Calculate mean
            median = merged_df[col].median()  # Calculate median
            maxim = merged_df[col].max()  # Calculate maximum
            minim = merged_df[col].min()  # Calculate minimum
            mode, count = st.mode(merged_df[col].round(3))
            iqr = st.iqr(merged_df[col])

            sorted_data = np.sort(merged_df[col])
            cumulative_prob = np.linspace(0, 1, len(sorted_data))

            i = _find_value_from_cdf(cumulative_prob, curtail)


            if 'loading' in col:
                n = sum(1 for num in merged_df[col] if num > over_loading)
            else:
                n = sum(1 for num in merged_df[col] if num > over_loading*maxim)

            # Create a dictionary to store the statistics
            stats_dict = {
                'Element': col,
                'Mean': mean,
                'Median': median,
                'Maximum': maxim,
                'Minimum': minim,
                'Mode3dec': mode,
                'Mode_count': count,
                'IQR': iqr,
                f'{curtail*100}%': sorted_data[i].item(),
               f'Number above {over_loading*100}%': n
            }

            # Convert the dictionary to a DataFrame and append it to the stats DataFrame
            static.append(stats_dict)

    # Reset index of the stats DataFrame
    stats = pd.DataFrame(static)
    stats.set_index('Element', inplace=True)
    grid.Stats = stats

    return stats

def results_ts_opf(grid,excel_file_path,grid_names=None,stats=None,times=None):
    """Export time-series OPF results to an Excel workbook.

    Parameters
    ----------
    grid : Grid
        Grid with ``time_series_results`` populated by :func:`ts_acdc_opf`.
    excel_file_path : str
        Output ``.xlsx`` path (``.xlsx`` is appended if missing).
    grid_names : dict, optional
        Rename columns in the ``grid_loading`` sheet.
    stats : DataFrame, optional
        Statistics table written to the ``stats`` sheet.
    times : dict, optional
        Timing metrics written to the ``Time`` sheet.

    Notes
    -----
    Writes one sheet per result table, including AC/DC line loading, flows,
    converter powers, OPF dispatch, curtailment, price-zone data, and optional
    ``stats`` / ``Time`` sheets.

    Examples
    --------
    >>> pyf.results_ts_opf(grid, "results", stats=stats_df)
    """

    if not excel_file_path.endswith('.xlsx'):
        excel_file_path = f'{excel_file_path}.xlsx'

    if grid_names is not None:
        grid.time_series_results['grid_loading'] =grid.time_series_results['grid_loading'].rename(columns=grid_names)


    with pd.ExcelWriter(excel_file_path) as writer:
        # Write each DataFrame to a separate sheet
        if times is not None:
            times_df = pd.DataFrame(list(times.items()), columns=['Metric', 'Time (s)'])
            row_space = pd.DataFrame({'Metric': [''], 'Time (s)': ['']})
            row_infeasible = pd.DataFrame({'Metric': ['Infeasible'], 'Time (s)': [grid.ts_infeasible_count]})
            times_df = pd.concat([times_df, row_space, row_infeasible], ignore_index=True)
            times_df.to_excel(writer, sheet_name='Time', index=False)

        (grid.time_series_results['ac_loading']* 100).to_excel(writer, sheet_name='AC line loading', index=True)
        (grid.time_series_results['dc_loading']* 100).to_excel(writer, sheet_name='DC line loading', index=True)
        grid.time_series_results['ac_MW_to'].to_excel(writer, sheet_name='AC MW to', index=True)
        grid.time_series_results['dc_MW_to'].to_excel(writer, sheet_name='DC MW to', index=True)
        (grid.time_series_results['grid_loading']* 100).to_excel(writer, sheet_name='Grid loading', index=True)

        (grid.time_series_results['converter_p_dc']*grid.S_base).to_excel(writer, sheet_name='Converter P DC', index=True)
        (grid.time_series_results['converter_q_ac']*grid.S_base).to_excel(writer, sheet_name='Converter Q AC', index=True)
        (grid.time_series_results['converter_p_ac']*grid.S_base).to_excel(writer, sheet_name='Converter P AC', index=True)
        (grid.time_series_results['real_load_by_zone']*grid.S_base).to_excel(writer, sheet_name='Real Load', index=True)
        (grid.time_series_results['real_load_known_by_zone']*grid.S_base).to_excel(writer, sheet_name='Known Load', index=True)
        (grid.time_series_results['real_power_opf']*grid.S_base).to_excel(writer, sheet_name='Real power OPF', index=True)
        (grid.time_series_results['reactive_power_opf']*grid.S_base).to_excel(writer, sheet_name='Reactive OPF', index=True)
        (grid.time_series_results['curtailment']* 100).to_excel(writer, sheet_name='Curtailment', index=True)

        (grid.time_series_results['converter_loading']*100).to_excel(writer, sheet_name='Converter loading', index=True)
        (grid.time_series_results['real_power_by_zone']*grid.S_base).to_excel(writer, sheet_name='Real power by zone', index=True)
        grid.time_series_results['net_price_zone_power'].to_excel(writer, sheet_name='Net price zone power', index=True)
        grid.time_series_results['prices_by_zone'].to_excel(writer, sheet_name='Prices by zone', index=True)
        grid.time_series_results['PZ_cost_of_generation'].to_excel(
            writer, sheet_name='PZ cost of generation', index=True
        )
        grid.time_series_results['PZ_load'].to_excel(writer, sheet_name='PZ_load', index=True)
        grid.time_series_results['a'].to_excel(writer, sheet_name='a', index=True)
        grid.time_series_results['b'].to_excel(writer, sheet_name='b', index=True)
        grid.time_series_results['PZ_lb'].to_excel(writer, sheet_name='PZ_lb', index=True)
        grid.time_series_results['PZ_ub'].to_excel(writer, sheet_name='PZ_ub', index=True)
        grid.time_series_results['res_available'].to_excel(writer, sheet_name='res_available', index=True)
        if stats is not None:
            stats.to_excel(writer, sheet_name='stats', index=True)




