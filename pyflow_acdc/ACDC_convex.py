"""
pyflow_acdc SOCP optimisation entry point.

Public API
----------
socp_optimise(grid, ...)   – mirror of optimal_pf for the CVXPY SOCP stack.

Design rules (locked):
  L2  – case-agnostic: works on any pyflow Grid
  L4  – files: convex_model/convex_model.py (build) + this file (run)
  L5  – entry point: socp_optimise (British spelling)
  L16 – objective: min Σ Re(S_export)·price  (≡ max revenue)
  L20 – grid pu throughout; € only at objective scaling
"""

import time
import warnings
from types import SimpleNamespace

import numpy as np

from .constants import (
    LinkCost,
    ObjComponent,
    TSType,
    TS_RENEWABLE_TYPES,
    default_obj_weights,
)
from .grid_analysis import analyse_grid
from .solver_utils import (
    resolve_socp_solver,
)

try:
    import cvxpy as cp
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "cvxpy is required for the SOCP stack.  "
        "Install it with: pip install pyflow_acdc[SOCP]"
    ) from exc

from scipy.stats import truncnorm

from .convex_model.convex_model import build_socp_data, socp_model

__all__ = [
    "socp_optimise",
    "soc_window_optimisation",
    "socp_ccp_optimise",
    "socp_ccp_window_optimisation",
    "translate_pyf_socp",
    "apply_ccp_quantiles",
]


def _rs_node_number(grid, rs):
    """Resolve RenSource host AC node number from ``rs.Node`` name."""
    nodes = getattr(grid, 'nodes_AC_dict', None)
    if nodes is None:
        nodes = {n.name: n for n in grid.nodes_AC}
    node = nodes.get(rs.Node)
    if node is None:
        raise ValueError(f"RenSource {rs.name!r} Node={rs.Node!r} not found in grid.nodes_AC")
    return node.nodeNumber


def _ts_type(ts):
    """Normalize TimeSeries.type to a comparable value."""
    typ = ts.type
    return typ.value if hasattr(typ, 'value') else typ


# ---------------------------------------------------------------------------
# Translate  Grid  →  SOCP inputs
# ---------------------------------------------------------------------------

def translate_pyf_socp(grid, gamma=1.0, frame_ids=None, P_ext_bounds=None):
    """Prepare SOCP data from *grid* and ``grid.Time_series``.

    Elements do not hold TS arrays; they only link by name. Profiles are read
    from ``grid.Time_series`` (same pattern as window OPF / ``update_grid_data``).

    Parameters
    ----------
    grid : Grid
        Analysed pyflow_acdc grid.
    gamma : float
        Renewable curtailment parameter (L12).  ``1.0`` = no curtailment.
    frame_ids : sequence or None
        Absolute indices into each ``TimeSeries.data``.  If ``None`` and the
        grid has time series, uses the full horizon ``0…len-1``.  If ``None``
        and there are no time series, uses a single static frame.
    P_ext_bounds : dict or None
        Optional ``{node: (P_min, P_max)}`` overrides for ext-grid generators.

    Returns
    -------
    SimpleNamespace
        Static SOCP data plus ``T``, ``frame_ids``, ``P_ren``, ``prices``,
        ``h2_prices``, and ``P_ext_bounds``.
    """
    socp_data = build_socp_data(grid)

    series = list(grid.Time_series)
    if frame_ids is None:
        if series:
            T = len(series[0].data)
            frame_ids = list(range(T))
        else:
            T = 1
            frame_ids = [0]
    else:
        frame_ids = list(frame_ids)
        T = len(frame_ids)
        if T < 1:
            raise ValueError("frame_ids must contain at least one frame")

    if series:
        lengths = {len(ts.data) for ts in series}
        if len(lengths) != 1:
            raise ValueError(f"All Time_series must share the same length; got {sorted(lengths)}")
        ts_len = lengths.pop()
        for abs_t in frame_ids:
            if abs_t < 0 or abs_t >= ts_len:
                raise ValueError(f"frame_id={abs_t} out of range for Time_series length {ts_len}")

    nodes_ac = {n.name: n for n in grid.nodes_AC}
    grid.nodes_AC_dict = nodes_ac
    rs_by_name = {rs.name: rs for rs in grid.RenSources}
    zones_by_name = {z.name: z for z in getattr(grid, 'RenSource_zones', []) or []}
    pz_by_name = {pz.name: pz for pz in getattr(grid, 'Price_Zones', []) or []}

    # ---- renewable injections: node → array(T) ----------------------------
    # Start from current/static availability, then overwrite from TS profiles.
    avail = {rs.name: np.full(T, float(rs.PRGi_available), dtype=float) for rs in grid.RenSources}

    for ts in series:
        typ = _ts_type(ts)
        if typ not in TS_RENEWABLE_TYPES:
            continue
        data = np.asarray(ts.data, dtype=float)
        profile = np.array([data[abs_t] for abs_t in frame_ids], dtype=float)

        rs = rs_by_name.get(ts.element_name)
        if rs is not None:
            avail[rs.name] = profile
            continue
        zone = zones_by_name.get(ts.element_name)
        if zone is not None:
            for linked in zone.RenSources:
                if linked.PGRi_linked:
                    avail[linked.name] = profile

    P_ren_out = {}
    ren_P_source = {}
    rs_by_number = {rs.rsNumber: rs for rs in grid.RenSources}
    for ri, rd in enumerate(socp_data.ren_data):
        rs = rs_by_number[rd['idx']]
        ren_P_source[ri] = avail[rs.name] * rd['p_base']
    for rs in grid.RenSources:
        n = _rs_node_number(grid, rs)
        scale = rs.PGi_ren_base * getattr(rs, 'np_rsgen', 1) * gamma
        inj = avail[rs.name] * scale
        if n in P_ren_out:
            P_ren_out[n] = P_ren_out[n] + inj
        else:
            P_ren_out[n] = inj

    # ---- prices: node → array(T) ------------------------------------------
    prices_out = {}
    # Static fallback from current price-zone / node prices
    for n in grid.nodes_AC:
        prices_out[n.nodeNumber] = np.full(T, float(getattr(n, 'price', 0.0)), dtype=float)

    for ts in series:
        typ = _ts_type(ts)
        if typ != TSType.PRICE:
            continue
        data = np.asarray(ts.data, dtype=float)
        profile = np.array([data[abs_t] for abs_t in frame_ids], dtype=float)

        pz = pz_by_name.get(ts.element_name)
        if pz is not None:
            for n_ac in getattr(pz, 'nodes_AC', []) or []:
                node_num = n_ac.nodeNumber if hasattr(n_ac, 'nodeNumber') else nodes_ac[n_ac].nodeNumber
                prices_out[node_num] = profile.copy()

        node = nodes_ac.get(ts.element_name)
        if node is not None:
            prices_out[node.nodeNumber] = profile.copy()

    # ---- H₂ sale prices: electrolyser index → array(T) --------------------
    el_by_name = {el.name: el for el in grid.electrolysers}
    h2_prices = {
        ei: np.full(T, float(ed['h2_price']), dtype=float)
        for ei, ed in enumerate(socp_data.h2_data)
    }
    for ts in series:
        typ = _ts_type(ts)
        if typ != TSType.H2_PRICE:
            continue
        data = np.asarray(ts.data, dtype=float)
        profile = np.array([data[abs_t] for abs_t in frame_ids], dtype=float)
        el = el_by_name.get(ts.element_name)
        if el is None:
            raise ValueError(
                f"H2_PRICE time series element_name={ts.element_name!r} "
                f"does not match any electrolyser"
            )
        for ei, ed in enumerate(socp_data.h2_data):
            if ed['idx'] == el.electrolyserNumber:
                h2_prices[ei] = profile.copy()
                break
        else:
            raise ValueError(
                f"Electrolyser {el.name!r} not found in h2_data"
            )

    # ---- heat-pump refs / energy bounds: hp index → array(T) --------------
    # Static scalars from build_socp_data, overridden per-frame by TS profiles.
    hp_by_name = {hp.name: hp for hp in grid.heat_pumps}
    hp_idx_by_number = {hd['idx']: hi for hi, hd in enumerate(socp_data.hp_data)}
    hp_P_ref = {hi: np.full(T, hd['P_ref'], dtype=float) for hi, hd in enumerate(socp_data.hp_data)}
    hp_Q_ref = {hi: np.full(T, hd['Q_ref'], dtype=float) for hi, hd in enumerate(socp_data.hp_data)}
    hp_E_min = {hi: np.full(T, hd['E_min'], dtype=float) for hi, hd in enumerate(socp_data.hp_data)}
    hp_E_max = {hi: np.full(T, hd['E_max'], dtype=float) for hi, hd in enumerate(socp_data.hp_data)}

    _hp_ts_targets = {
        TSType.HP_P_REF: hp_P_ref,
        TSType.HP_Q_REF: hp_Q_ref,
        TSType.HP_E_MIN: hp_E_min,
        TSType.HP_E_MAX: hp_E_max,
    }
    for ts in series:
        typ = _ts_type(ts)
        target = next((store for k, store in _hp_ts_targets.items() if typ == k), None)
        if target is None:
            continue
        hp = hp_by_name.get(ts.element_name)
        if hp is None:
            raise ValueError(
                f"Heat-pump time series element_name={ts.element_name!r} "
                f"does not match any heat pump"
            )
        hi = hp_idx_by_number.get(hp.heatPumpNumber)
        if hi is None:
            raise ValueError(f"Heat pump {hp.name!r} not found in hp_data")
        data = np.asarray(ts.data, dtype=float)
        target[hi] = np.array([data[abs_t] for abs_t in frame_ids], dtype=float)

    return SimpleNamespace(
        **vars(socp_data),
        T=T,
        frame_ids=frame_ids,
        P_ren=P_ren_out,
        ren_P_source=ren_P_source,
        ren_gamma=gamma,
        prices=prices_out,
        h2_prices=h2_prices,
        hp_P_ref=hp_P_ref,
        hp_Q_ref=hp_Q_ref,
        hp_E_min=hp_E_min,
        hp_E_max=hp_E_max,
        P_ext_bounds=P_ext_bounds or {},
    )


# ---------------------------------------------------------------------------
# Build objective
# ---------------------------------------------------------------------------

def _default_socp_obj_weights():
    """Return SOCP default objective weights matching current v1 behavior."""
    weights = default_obj_weights()
    weights[ObjComponent.ENERGY_COST.value]['w'] = 1
    return weights


def _sum_ac_losses_expr(ac, d):
    """Return total AC active losses across all sparse AC edges."""
    terms = []
    for t in range(d.T):
        for (k, m) in d.E_AC:
            w_km_t = ac.w_AC[(k, m)][t]
            s_km = cp.conj(d.Ybus_AC[k, m]) * (ac.h_AC[k, t] - w_km_t)
            s_mk = cp.conj(d.Ybus_AC[m, k]) * (ac.h_AC[m, t] - cp.conj(w_km_t))
            terms.append(cp.real(s_km + s_mk))
    return sum(terms) if terms else 0


def _sum_dc_losses_expr(dc, d):
    """Return total DC active losses across all sparse DC edges."""
    if dc is None:
        return 0

    terms = []
    for t in range(d.T):
        for (k, m) in d.E_DC:
            w_km_t = dc.w_DC[(k, m)][t]
            p_km = (dc.h_DC[k, t] - w_km_t) * d.Ybus_DC[k, m]
            p_mk = (dc.h_DC[m, t] - w_km_t) * d.Ybus_DC[m, k]
            terms.append(p_km + p_mk)
    return sum(terms) if terms else 0


def _build_objective(variables, d, grid, weights_def=None):
    """Construct the weighted SOCP objective using NLP OPF component names.

    Supported v1 components:
    - ``Energy_cost``       : generator quadratic costs; gens with
      ``link_cost=LINEAR`` use ``d.prices[node,t]`` for the linear term;
      renewable ``qf``/``lf`` on per-source availability profiles; heat-pump
      shed quadratic/linear costs on ``P_shed``/``Q_shed``
    - ``Ext_Gen``           : total external-grid active power
    - ``AC_losses``         : AC branch active losses
    - ``DC_losses``         : DC branch active losses
    - ``Converter_Losses``  : converter losses
    - ``H2_sale``           : −price · Δm (maximise H₂ revenue)
    - ``SoC_deviation``     : quadratic SoC tracking vs ``soc_ref``

    Any active unsupported component raises ``NotImplementedError``.
    """
    if weights_def is None:
        weights_def = _default_socp_obj_weights()

    ac = variables.ac
    gen = variables.gen
    dc = variables.dc
    conv = variables.conv
    st = variables.storage
    h2 = variables.hydrogen
    hp = variables.heat_pump
    terms = []
    np_den_eps = 1e-3

    for component, cfg in weights_def.items():
        weight = cfg.get('w', 0)
        if weight == 0:
            continue

        if component == ObjComponent.ENERGY_COST.value:
            if gen is not None:
                for gi, gd in enumerate(d.gen_data_AC):
                    node = gd['node']
                    for t in range(d.T):
                        p_mw = gen.PGi_gen[gi, t] * d.Sbase
                        if gd['link_cost'] == LinkCost.LINEAR:
                            lf_t = float(d.prices[node][t])
                        else:
                            lf_t = gd['lf']
                        terms.append(
                            weight * (
                                (p_mw ** 2) * gd['qf'] / (gd['np_gen'] + np_den_eps)
                                + p_mw * lf_t
                                + gd['np_gen'] * gd['fc']
                            )
                        )
            if grid.DCmode and grid.Generators_DC:
                raise NotImplementedError(
                    "SOCP Energy_cost does not yet include DC generator costs."
                )
            ren_gamma = getattr(d, 'ren_gamma', 1.0)
            for ri, rd in enumerate(getattr(d, 'ren_data', ())):
                p_src = d.ren_P_source[ri]
                for t in range(d.T):
                    p_mw = float(p_src[t]) * ren_gamma * d.Sbase
                    terms.append(
                        weight * rd['np_rsgen'] * (
                            (p_mw ** 2) * rd['qf'] + p_mw * rd['lf']
                        )
                    )
            if hp is not None:
                for hi, hd in enumerate(d.hp_data):
                    for t in range(d.T):
                        p_mw = hp.P_shed[hi, t] * d.Sbase
                        q_mvar = hp.Q_shed[hi, t] * d.Sbase
                        terms.append(
                            weight * (
                                (p_mw ** 2) * hd['qf'] + p_mw * hd['lf']
                                + (q_mvar ** 2) * hd['qf_q'] + q_mvar * hd['lf_q']
                            )
                        )
        elif component == ObjComponent.EXT_GEN.value:
            if gen is None:
                continue
            for gi, gd in enumerate(d.gen_data_AC):
                if gd['is_ext_grid']:
                    terms.append(weight * cp.sum(gen.PGi_gen[gi, :]) * d.Sbase)
        elif component == ObjComponent.AC_LOSSES.value:
            terms.append(weight * _sum_ac_losses_expr(ac, d) * grid.LCoE * d.Sbase)
        elif component == ObjComponent.DC_LOSSES.value:
            terms.append(weight * _sum_dc_losses_expr(dc, d) * grid.LCoE * d.Sbase)
        elif component == ObjComponent.CONVERTER_LOSSES.value:
            if conv is None:
                continue
            terms.append(weight * cp.sum(conv.Ploss) * grid.LCoE * d.Sbase)
        elif component == ObjComponent.H2_SALE.value:
            if h2 is None:
                raise ValueError("H2_sale weight > 0 requires grid.H2 / electrolysers")
            for ei, ed in enumerate(d.h2_data):
                for t in range(d.T):
                    h_prod = (
                        ed['b_h'] * h2.P_electrolyser[ei, t] * ed['S_base'] * ed['dt_hours']
                        + ed['c_h']
                    )
                    price_t = float(d.h2_prices[ei][t])
                    terms.append(weight * (-price_t * h_prod))
        elif component == ObjComponent.SOC_DEVIATION.value:
            if st is None:
                raise ValueError("SoC_deviation weight > 0 requires grid.ESS / storage")
            for si, sd in enumerate(d.storage_data):
                for t in range(d.T):
                    terms.append(weight * (st.SoC[si, t] - sd['soc_ref']) ** 2)
        else:
            raise NotImplementedError(
                f"SOCP objective component '{component}' is not implemented."
            )

    if not terms:
        warnings.warn(
            "socp_optimise: objective is zero — no active supported components.",
            stacklevel=3,
        )
        return cp.Minimize(0)

    return cp.Minimize(sum(terms))


# ---------------------------------------------------------------------------
# Export solution back to Grid
# ---------------------------------------------------------------------------

def _export_to_grid(grid, variables, socp_data):
    """Write SOCP solution values back onto Grid elements.

    Only scalar (T=1) or the first time step is used for static grid attrs;
    full time-series are stored on ``grid.socp_results``.
    """
    ac   = variables.ac
    gen  = variables.gen
    dc   = variables.dc
    conv = variables.conv
    st   = variables.storage
    h2   = variables.hydrogen
    hp   = variables.heat_pump

    # Voltage magnitudes → AC nodes
    if ac.h_AC.value is not None:
        for n in grid.nodes_AC:
            n.V_AC = float(np.sqrt(np.clip(ac.h_AC.value[n.nodeNumber, 0], 0, None)))

    # Voltage magnitudes → DC nodes
    if dc is not None and dc.h_DC.value is not None:
        for n in grid.nodes_DC:
            n.V_DC = float(np.sqrt(np.clip(dc.h_DC.value[n.nodeNumber, 0], 0, None)))

    # Generator results
    if gen is not None and gen.PGi_gen.value is not None:
        for gi, gd in enumerate(socp_data.gen_data_AC):
            g_obj = grid.Generators[gd['idx']]
            g_obj.PGen = float(gen.PGi_gen.value[gi, 0])
            g_obj.QGen = float(gen.QGi_gen.value[gi, 0])

    # Converter results
    if conv is not None and conv.Ss.value is not None:
        for ci, cd in enumerate(socp_data.conv_data):
            c_obj = grid.Converters_ACDC[ci]
            c_obj.P_AC   = float(np.real(conv.Ss.value[ci, 0]))
            c_obj.Q_AC   = float(np.imag(conv.Ss.value[ci, 0]))
            c_obj.P_loss = float(conv.Ploss.value[ci, 0]) if conv.Ploss.value is not None else 0.0
            if dc is not None and dc.P_DC.value is not None:
                c_obj.P_DC = float(dc.P_DC.value[cd['nDC'], 0])

    # BESS results (last time step for SoC / operating point for t=0 attrs)
    if st is not None and st.P_charge.value is not None:
        t_last = socp_data.T - 1
        for si, sd in enumerate(socp_data.storage_data):
            s_obj = grid.storage_elements[si]
            if s_obj.storageNumber != sd['idx']:
                raise ValueError(
                    f"storage_data index mismatch: expected storageNumber "
                    f"{sd['idx']}, got {s_obj.storageNumber}"
                )
            s_obj.P_charge = float(st.P_charge.value[si, 0])
            s_obj.P_discharge = float(st.P_discharge.value[si, 0])
            s_obj.Q = float(st.Q_storage.value[si, 0])
            s_obj.SoC = float(st.SoC.value[si, t_last])

    # H₂ results
    if h2 is not None and h2.P_electrolyser.value is not None:
        t_last = socp_data.T - 1
        for ei, ed in enumerate(socp_data.h2_data):
            el = grid.electrolysers[ei]
            if el.electrolyserNumber != ed['idx']:
                raise ValueError(
                    f"h2_data index mismatch: expected electrolyserNumber "
                    f"{ed['idx']}, got {el.electrolyserNumber}"
                )
            el.P_electrolyser = float(h2.P_electrolyser.value[ei, 0])
            el.Q_electrolyser = float(h2.Q_electrolyser.value[ei, 0])
            el.mass_H2 = float(h2.mass_H2.value[ei, t_last])

    # Heat-pump results
    if hp is not None and hp.P_shed.value is not None:
        t_last = socp_data.T - 1
        for hi, hd in enumerate(socp_data.hp_data):
            h_obj = grid.heat_pumps[hi]
            if h_obj.heatPumpNumber != hd['idx']:
                raise ValueError(
                    f"hp_data index mismatch: expected heatPumpNumber "
                    f"{hd['idx']}, got {h_obj.heatPumpNumber}"
                )
            h_obj.P_shed = float(hp.P_shed.value[hi, 0])
            h_obj.Q_shed = float(hp.Q_shed.value[hi, 0])
            h_obj.P_hp = float(hp.P_heat_pump.value[hi, 0])
            h_obj.Q_hp = float(hp.Q_heat_pump.value[hi, 0])
            h_obj.E_state = float(hp.E_heat_pump.value[hi, t_last])

    hp_P_served = None
    hp_Q_served = None
    if hp is not None and hp.P_shed.value is not None:
        hp_P_served = hp.P_heat_pump.value
        hp_Q_served = hp.Q_heat_pump.value

    # Store full time-series for post-processing
    grid.socp_results = SimpleNamespace(
        h_AC  = ac.h_AC.value,
        w_AC  = {e: v.value for e, v in ac.w_AC.items()},
        PGi_gen = gen.PGi_gen.value if gen is not None else None,
        QGi_gen = gen.QGi_gen.value if gen is not None else None,
        h_DC  = dc.h_DC.value  if dc   is not None else None,
        P_DC  = dc.P_DC.value  if dc   is not None else None,
        Ss    = conv.Ss.value  if conv is not None else None,
        Ploss = conv.Ploss.value if conv is not None else None,
        P_storage_charge = st.P_charge.value if st is not None else None,
        P_storage_discharge = st.P_discharge.value if st is not None else None,
        Q_storage = st.Q_storage.value if st is not None else None,
        SoC = st.SoC.value if st is not None else None,
        P_electrolyser = h2.P_electrolyser.value if h2 is not None else None,
        Q_electrolyser = h2.Q_electrolyser.value if h2 is not None else None,
        mass_H2 = h2.mass_H2.value if h2 is not None else None,
        P_heat_pump = hp_P_served,
        Q_heat_pump = hp_Q_served,
        P_shed = hp.P_shed.value if hp is not None else None,
        Q_shed = hp.Q_shed.value if hp is not None else None,
        E_heat_pump = hp.E_heat_pump.value if hp is not None else None,
        T     = socp_data.T,
        frame_ids = socp_data.frame_ids,
    )

    grid.socp_run = True


# ---------------------------------------------------------------------------
# Chance-constrained prep (Paper A §4)
# ---------------------------------------------------------------------------

def _truncated_normal_quantile(confidence_level, sigma, lower, upper):
    """Left-tail quantile of N(0, σ²) truncated to ``[lower, upper]``."""
    if sigma <= 0 or lower >= upper:
        return 0.0
    q = 1.0 - confidence_level
    a = lower / sigma
    b = upper / sigma
    return float(truncnorm.ppf(q, a, b, loc=0.0, scale=sigma))


def _ren_rated_pu_by_node(grid, gamma=1.0):
    """Max renewable active power [pu] per AC node at availability 1."""
    nodes = {n.name: n for n in grid.nodes_AC}
    rated = {}
    for rs in grid.RenSources:
        node = nodes.get(rs.Node)
        if node is None:
            continue
        k = node.nodeNumber
        cap = rs.PGi_ren_base * getattr(rs, 'np_rsgen', 1) * gamma
        rated[k] = rated.get(k, 0.0) + cap
    return rated


def apply_ccp_quantiles(
    socp_data,
    grid,
    confidence_level,
    *,
    gamma=1.0,
    wind_error_sigma_frac=0.10,
    price_error_sigma_frac=0.10,
    price_error_sigma_bounds=3.0,
    weights_def=None,
):
    """Tighten wind caps and nodal prices using truncated-normal quantiles.

    Implements Paper A Eqs. 61–69 in place on ``socp_data.P_ren`` and
    ``socp_data.prices`` before :func:`socp_model` is called.

    Wind quantiles apply whenever ``P_ren`` is present. Price quantiles apply
    when ``Energy_cost`` has non-zero weight in ``weights_def`` (same rule as
    the objective using ``socp_data.prices``).

    Wind: ``p^w ≤ p̂ + Q_{1−confidence_level}(ε_w)`` with
    ``σ_w = wind_error_sigma_frac · |p̂|``, error truncated to keep
    injection in ``[0, P_rated]``.

    Price: ``C ≤ Ĉ + Q_{1−confidence_level}(ε_c)`` with
    ``σ_c = price_error_sigma_frac · |Ĉ|``, error truncated to
    ``± price_error_sigma_bounds · σ_c``.
    """
    if not (0.0 < confidence_level < 1.0):
        raise ValueError(
            f"confidence_level must be in (0, 1); got {confidence_level!r}"
        )
    if wind_error_sigma_frac < 0:
        raise ValueError("wind_error_sigma_frac must be non-negative")
    if price_error_sigma_frac < 0:
        raise ValueError("price_error_sigma_frac must be non-negative")
    if price_error_sigma_bounds <= 0:
        raise ValueError("price_error_sigma_bounds must be positive")

    rated_by_node = _ren_rated_pu_by_node(grid, gamma=gamma)
    if weights_def is None:
        weights_def = _default_socp_obj_weights()
    apply_price_ccp = (
        weights_def.get(ObjComponent.ENERGY_COST.value, {}).get('w', 0) != 0
    )

    for k, profile in socp_data.P_ren.items():
        p_rated = rated_by_node.get(k, float(np.max(profile)) if len(profile) else 0.0)
        new_profile = np.asarray(profile, dtype=float).copy()
        for t, p_hat in enumerate(new_profile):
            sigma = wind_error_sigma_frac * abs(p_hat)
            lower = -p_hat
            upper = max(p_rated - p_hat, lower)
            q_err = _truncated_normal_quantile(confidence_level, sigma, lower, upper)
            cap = p_rated if p_rated > 0 else max(p_hat, 0.0)
            new_profile[t] = np.clip(p_hat + q_err, 0.0, cap)
        socp_data.P_ren[k] = new_profile

    if apply_price_ccp:
        for k, profile in socp_data.prices.items():
            new_profile = np.asarray(profile, dtype=float).copy()
            for t, c_hat in enumerate(new_profile):
                sigma_c = price_error_sigma_frac * abs(c_hat)
                if sigma_c <= 0:
                    continue
                span = price_error_sigma_bounds * sigma_c
                q_err = _truncated_normal_quantile(
                    confidence_level, sigma_c, -span, span,
                )
                new_profile[t] = c_hat + q_err
            socp_data.prices[k] = new_profile

    socp_data.confidence_level = confidence_level


def _execute_socp(
    grid,
    socp_data,
    *,
    weights_def,
    solver,
    solver_opts,
    build_only,
    verbose,
    bess_mi_exclusivity,
    t0,
    t1,
    runner_name="socp_optimise",
):
    """Build, optionally solve, and export a prepared SOCP."""
    socp_data.bess_mi_exclusivity = bess_mi_exclusivity

    constraints, variables = socp_model(grid, socp_data)

    objective = _build_objective(
        variables,
        socp_data,
        grid,
        weights_def=weights_def,
    )
    problem = cp.Problem(objective, constraints)

    t2 = time.perf_counter()

    solver_stats = {
        'status': None,
        'value': None,
        'time': 0.0,
        'n_vars': problem.variables().__len__(),
        'n_constr': len(problem.constraints),
    }

    if build_only:
        timing_info = {'translate': t1 - t0, 'build': t2 - t1, 'solve': 0.0}
        return problem, variables, timing_info, solver_stats

    solve_kwargs = {'verbose': verbose}
    chosen_solver = resolve_socp_solver(
        mi_required=bess_mi_exclusivity and bool(socp_data.storage_data),
        solver=solver,
    )
    if chosen_solver is not None:
        solve_kwargs['solver'] = chosen_solver
    if solver_opts:
        solve_kwargs.update(solver_opts)

    t3 = time.perf_counter()
    problem.solve(**solve_kwargs)
    t4 = time.perf_counter()

    solver_stats['status'] = problem.status
    solver_stats['value'] = problem.value
    solver_stats['time'] = t4 - t3
    solver_stats['solver'] = chosen_solver

    if problem.status not in ('optimal', 'optimal_inaccurate'):
        warnings.warn(
            f"{runner_name}: solver returned status '{problem.status}'.",
            stacklevel=2,
        )
    else:
        _export_to_grid(grid, variables, socp_data)

    timing_info = {
        'translate': t1 - t0,
        'build': t2 - t1,
        'solve': t4 - t3,
    }

    return problem, variables, timing_info, solver_stats


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def socp_optimise(
    grid,
    gamma=1.0,
    frame_id=0,
    P_ext_bounds=None,
    weights_def=None,
    solver=None,
    solver_opts=None,
    build_only=False,
    verbose=False,
    bess_mi_exclusivity=False,
):
    """Build and solve the sparse AC/DC SOCP for *grid* (single period).

    Parameters
    ----------
    grid : Grid
        pyflow_acdc grid (will be analysed if not already).
    gamma : float
        Renewable curtailment parameter (L12).  ``1.0`` = full dispatch.
    frame_id : int
        Absolute index into ``grid.Time_series`` data when series are present.
        Ignored for static (no-TS) grids.
    P_ext_bounds : dict or None
        ``{node_AC: (P_min_pu, P_max_pu)}`` for export buses.
    weights_def : dict or None
        Objective-component weights using the same public keys as NLP OPF
        (for example ``Energy_cost`` or ``AC_losses``). If ``None``, defaults to
        ``{'Energy_cost': {'w': 1}}``.
    solver : str or None
        CVXPY solver name, e.g. ``'MOSEK'``, ``'GUROBI'``, ``'CLARABEL'``.
        If ``None``, picks the first installed solver from the default SOCP
        list (MOSEK, GUROBI, SCIP, CLARABEL, SCS). When
        ``bess_mi_exclusivity=True``, an MI-capable solver (MOSEK, GUROBI, or
        SCIP) is preferred; a non-MI choice emits a warning but is not blocked.
    solver_opts : dict or None
        Keyword options forwarded to ``problem.solve()``.
    build_only : bool
        If ``True``, build the problem but do not solve.  Useful for
        inspecting model size or CI without a commercial solver.
    verbose : bool
        Stream solver output.
    bess_mi_exclusivity : bool
        If ``True``, add MI charge/discharge exclusivity binaries on BESS
        (Paper R Eqs. 56–59). Default ``False`` keeps G6 continuous overlap.

    Returns
    -------
    tuple
        ``(problem, variables, timing_info, solver_stats)``.
    """
    analyse_grid(grid)
    grid.reset_run_flags()

    t0 = time.perf_counter()

    socp_data = translate_pyf_socp(
        grid,
        gamma=gamma,
        frame_ids=[frame_id],
        P_ext_bounds=P_ext_bounds,
    )
    socp_data.bess_mi_exclusivity = bess_mi_exclusivity

    t1 = time.perf_counter()

    return _execute_socp(
        grid,
        socp_data,
        weights_def=weights_def,
        solver=solver,
        solver_opts=solver_opts,
        build_only=build_only,
        verbose=verbose,
        bess_mi_exclusivity=bess_mi_exclusivity,
        t0=t0,
        t1=t1,
        runner_name="socp_optimise",
    )


def socp_ccp_optimise(
    grid,
    confidence_level,
    gamma=1.0,
    frame_id=0,
    P_ext_bounds=None,
    weights_def=None,
    solver=None,
    solver_opts=None,
    build_only=False,
    verbose=False,
    bess_mi_exclusivity=False,
    wind_error_sigma_frac=0.10,
    price_error_sigma_frac=0.10,
    price_error_sigma_bounds=3.0,
):
    """Build and solve the CCP sparse AC/DC SOCP (single period).

    Chance-constrained programming (Paper A §4): same as
    :func:`socp_optimise`, but tightens renewable caps and nodal prices with
    truncated-normal quantiles at ``confidence_level`` before the SOCP is built.

    See :func:`socp_optimise` for remaining parameters and
    :func:`apply_ccp_quantiles` for the uncertainty model.
    """
    analyse_grid(grid)
    grid.reset_run_flags()

    t0 = time.perf_counter()
    socp_data = translate_pyf_socp(
        grid,
        gamma=gamma,
        frame_ids=[frame_id],
        P_ext_bounds=P_ext_bounds,
    )
    apply_ccp_quantiles(
        socp_data,
        grid,
        confidence_level,
        gamma=gamma,
        wind_error_sigma_frac=wind_error_sigma_frac,
        price_error_sigma_frac=price_error_sigma_frac,
        price_error_sigma_bounds=price_error_sigma_bounds,
        weights_def=weights_def,
    )
    t1 = time.perf_counter()

    return _execute_socp(
        grid,
        socp_data,
        weights_def=weights_def,
        solver=solver,
        solver_opts=solver_opts,
        build_only=build_only,
        verbose=verbose,
        bess_mi_exclusivity=bess_mi_exclusivity,
        t0=t0,
        t1=t1,
        runner_name="socp_ccp_optimise",
    )


def soc_window_optimisation(
    grid,
    gamma=1.0,
    frame_ids=None,
    P_ext_bounds=None,
    weights_def=None,
    solver=None,
    solver_opts=None,
    build_only=False,
    verbose=False,
    bess_mi_exclusivity=False,
):
    """Build and solve the multiperiod/window SOCP for *grid*.

    Profiles come from ``grid.Time_series``.  If ``frame_ids`` is ``None``,
    the full TS horizon is used.

    See :func:`socp_optimise` for ``bess_mi_exclusivity`` and solver behaviour.
    """
    analyse_grid(grid)
    grid.reset_run_flags()

    t0 = time.perf_counter()
    socp_data = translate_pyf_socp(
        grid,
        gamma=gamma,
        frame_ids=frame_ids,
        P_ext_bounds=P_ext_bounds,
    )
    socp_data.bess_mi_exclusivity = bess_mi_exclusivity
    t1 = time.perf_counter()

    return _execute_socp(
        grid,
        socp_data,
        weights_def=weights_def,
        solver=solver,
        solver_opts=solver_opts,
        build_only=build_only,
        verbose=verbose,
        bess_mi_exclusivity=bess_mi_exclusivity,
        t0=t0,
        t1=t1,
        runner_name="soc_window_optimisation",
    )


def socp_ccp_window_optimisation(
    grid,
    confidence_level,
    gamma=1.0,
    frame_ids=None,
    P_ext_bounds=None,
    weights_def=None,
    solver=None,
    solver_opts=None,
    build_only=False,
    verbose=False,
    bess_mi_exclusivity=False,
    wind_error_sigma_frac=0.10,
    price_error_sigma_frac=0.10,
    price_error_sigma_bounds=3.0,
):
    """Build and solve the CCP multiperiod SOCP for *grid*.

    Chance-constrained programming (Paper A §4): same as
    :func:`soc_window_optimisation`, but applies :func:`apply_ccp_quantiles`
    at ``confidence_level`` before building.
    """
    analyse_grid(grid)
    grid.reset_run_flags()

    t0 = time.perf_counter()
    socp_data = translate_pyf_socp(
        grid,
        gamma=gamma,
        frame_ids=frame_ids,
        P_ext_bounds=P_ext_bounds,
    )
    apply_ccp_quantiles(
        socp_data,
        grid,
        confidence_level,
        gamma=gamma,
        wind_error_sigma_frac=wind_error_sigma_frac,
        price_error_sigma_frac=price_error_sigma_frac,
        price_error_sigma_bounds=price_error_sigma_bounds,
        weights_def=weights_def,
    )
    t1 = time.perf_counter()

    return _execute_socp(
        grid,
        socp_data,
        weights_def=weights_def,
        solver=solver,
        solver_opts=solver_opts,
        build_only=build_only,
        verbose=verbose,
        bess_mi_exclusivity=bess_mi_exclusivity,
        t0=t0,
        t1=t1,
        runner_name="socp_ccp_window_optimisation",
    )
