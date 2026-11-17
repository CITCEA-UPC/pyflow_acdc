"""
Sparse SOCP model builder for pyflow_acdc.

Constructs the CVXPY variables, SOC constraints, nodal balances, thermal
limits, and converter coupling for an AC/DC grid SOCP relaxation following
Useche-Arteaga et al. (SEGAN 2026).

Structure mirrors ACDC_OPF_NL_model.py:
  build_socp_data        – extract topology/data from Grid → SimpleNamespace
  socp_model             – top-level orchestrator on prepared SOCP data
    generator_variables  – PGi_gen, QGi_gen
    storage_variables    – P_charge/P_discharge, Q, SoC (continuous by default)
    hydrogen_variables   – P_electrolyser, Q, mass_H2 (linear)
    ac_variables         – h_AC, w_AC
    ac_constraints       – voltage bounds, SOC lifts, nodal balance, thermals
    dc_variables         – h_DC, w_DC, P_DC
    dc_constraints       – voltage bounds, SOC lifts, nodal balance, thermals
    converter_variables  – Ss, Ploss
    converter_constraints– power balance, loss model, rating

Design rules (locked):
  L3  – CVXPY only (no Pyomo)
  L8  – Converter AC-side RL branches ignored in Ybus
  L11 – Balance uses conj(S) == flow_k
  L13 – Converter loss: Ploss = a + b * t, t >= |Re(Ss)| (paper affine; DCP)
  L14 – DC polarity: pol = cn_pol
  L15 – AC and DC thermal limits are mandatory
  L19 – Sparse edge sets only; no dense mode
  L20 – All quantities in grid pu
"""

import numpy as np
from types import SimpleNamespace

from ..constants import AcDcSide

try:
    import cvxpy as cp
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "cvxpy is required for the SOCP stack.  "
        "Install it with: pip install pyflow_acdc[SOCP]"
    ) from exc

__all__ = [
    "build_socp_data",
    "socp_model",
    "generator_variables",
    "generator_constraints",
    "storage_variables",
    "storage_constraints",
    "hydrogen_variables",
    "hydrogen_constraints",
    "heat_pump_variables",
    "heat_pump_constraints",
    "ac_variables",
    "ac_constraints",
    "dc_variables",
    "dc_constraints",
    "converter_variables",
    "converter_constraints",
]


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def build_socp_data(grid):
    """Extract all SOCP-relevant data from *grid* into a SimpleNamespace.

    Parameters
    ----------
    grid : Grid
        An analysed pyflow_acdc grid (``analyse_grid`` must have been called).

    Returns
    -------
    SimpleNamespace
        All power / admittance values are in grid pu.
    """
    Sbase = grid.S_base

    # ------------------------------------------------------------------ AC --
    N_AC = grid.nn_AC
    Ybus_AC = np.array(grid.Ybus_AC, dtype=complex)  # (N_AC, N_AC)

    E_AC = set()
    for k in range(N_AC):
        for m in range(k + 1, N_AC):
            if abs(Ybus_AC[k, m]) > 1e-12:
                E_AC.add((k, m))

    V_min_AC = np.array([n.Umin if hasattr(n, 'Umin') and n.Umin is not None else 0.9
                         for n in grid.nodes_AC])
    V_max_AC = np.array([n.Umax if hasattr(n, 'Umax') and n.Umax is not None else 1.1
                         for n in grid.nodes_AC])

    ac_slack = [n.nodeNumber for n in grid.nodes_AC
                if str(n.type).lower() in ('slack', 'nodetype.slack')]

    ac_line_limits = {}
    for line in grid.lines_AC:
        k = line.fromNode.nodeNumber
        m = line.toNode.nodeNumber
        rating_pu = line.MVA_rating / Sbase if line.MVA_rating and line.MVA_rating > 0 else None
        edge = (min(k, m), max(k, m))
        if rating_pu is not None:
            if edge not in ac_line_limits or rating_pu < ac_line_limits[edge]:
                ac_line_limits[edge] = rating_pu

    # ------------------------------------------------------------------ DC --
    N_DC = grid.nn_DC
    Ybus_DC = np.array(grid.Ybus_DC, dtype=float)  # (N_DC, N_DC)

    E_DC = set()
    for k in range(N_DC):
        for m in range(k + 1, N_DC):
            if abs(Ybus_DC[k, m]) > 1e-12:
                E_DC.add((k, m))

    V_min_DC = np.array([n.Umin if hasattr(n, 'Umin') and n.Umin is not None else 0.9
                         for n in grid.nodes_DC])
    V_max_DC = np.array([n.Umax if hasattr(n, 'Umax') and n.Umax is not None else 1.1
                         for n in grid.nodes_DC])

    dc_slack = [n.nodeNumber for n in grid.nodes_DC
                if str(n.type).lower() in ('slack', 'nodetype.slack')]

    dc_line_limits = {}
    for line in grid.lines_DC:
        k = line.fromNode.nodeNumber
        m = line.toNode.nodeNumber
        rating_pu = line.MW_rating / Sbase if line.MW_rating and line.MW_rating > 0 else None
        edge = (min(k, m), max(k, m))
        if rating_pu is not None:
            if edge not in dc_line_limits or rating_pu < dc_line_limits[edge]:
                dc_line_limits[edge] = rating_pu * getattr(line, 'np_line', 1)

    # -------------------------------------------------------------- converters
    conv_data = []
    for conv in grid.Converters_ACDC:
        np_c = conv.np_conv if hasattr(conv, 'np_conv') and conv.np_conv > 0 else 1
        conv_data.append({
            'idx':  conv.ConvNumber,
            'nAC':  conv.Node_AC.nodeNumber,
            'nDC':  conv.Node_DC.nodeNumber,
            'pol':  abs(conv.cn_pol) if hasattr(conv, 'cn_pol') else 1,
            'a':    conv.a_conv,
            'b':    conv.b_conv,
            'Smax': conv.MVA_max * np_c / Sbase,
        })

    conv_ac_nodes = {cd['nAC'] for cd in conv_data}

    # --------------------------------------------------------- bus role maps
    gen_data_AC = []
    ren_nodes_AC = {}

    for gen in grid.Generators:
        np_gen = getattr(gen, 'np_gen', 1)
        if getattr(gen, 'is_ext_grid', False):
            if not getattr(gen, 'allow_sell', True):
                p_min = 0.0
            else:
                p_min = -(gen.Max_pow_gen * np_gen - gen.p_load_eff)
        else:
            p_min = gen.Min_pow_gen * np_gen
        p_max = gen.Max_pow_gen * np_gen
        q_min = gen.Min_pow_genR * np_gen
        q_max = gen.Max_pow_genR * np_gen
        p_ini = min(max(gen.Pset * np_gen, p_min), p_max)
        q_ini = min(max(gen.Qset * np_gen, q_min), q_max)
        gen_data_AC.append({
            'idx': gen.genNumber,
            'node': gen._node.nodeNumber,
            'is_ext_grid': getattr(gen, 'is_ext_grid', False),
            'link_cost': gen.link_cost,
            'p_min': p_min,
            'p_max': p_max,
            'q_min': q_min,
            'q_max': q_max,
            'p_ini': p_ini,
            'q_ini': q_ini,
            'qf': gen.qf,
            'lf': gen.lf,
            'fc': gen.fc,
            'np_gen': np_gen,
            'max_s': gen.Max_S * np_gen if gen.Max_S is not None else None,
        })

    nodes_ac = {n.name: n for n in grid.nodes_AC}
    ren_data = []
    for rs in grid.RenSources:
        node = nodes_ac.get(rs.Node)
        if node is None:
            raise ValueError(f"RenSource {rs.name!r} Node={rs.Node!r} not found in grid.nodes_AC")
        ren_nodes_AC[node.nodeNumber] = (
            rs.PGi_ren_base * rs.PRGi_available * getattr(rs, 'np_rsgen', 1),
            0.0,
        )  # Q=0 (L12)
        ren_data.append({
            'idx': rs.rsNumber,
            'node': node.nodeNumber,
            'p_base': rs.PGi_ren_base,
            'qf': rs.qf,
            'lf': rs.lf,
            'np_rsgen': getattr(rs, 'np_rsgen', 1),
        })

    # --------------------------------------------------------------- storage
    # Separate continuous charge/discharge powers; optional MI exclusivity via
    # bess_mi_exclusivity on the prepared SOCP data.
    storage_data = []
    storage_by_ac_node = {}
    storage_by_dc_node = {}
    for s in grid.storage_elements:
        node_num = s._node.nodeNumber
        entry = {
            'idx': s.storageNumber,
            'node': node_num,
            'connected': s.connected,
            'P_charge_max': s.P_charge_max,
            'P_discharge_max': s.P_discharge_max,
            'P_max': s.P_max,
            'S_max': s.S_max if s.connected == AcDcSide.AC else 0.0,
            'eta_charge': s.eta_charge,
            'eta_discharge': s.eta_discharge,
            'E_max': s.E_max,
            'dt_hours': s.dt_hours,
            'S_base': s.S_base,
            'soc_min': s.soc_min,
            'soc_max': s.soc_max,
            'soc_initial': s.soc_initial,
            'soc_final': s.soc_final,
            'soc_ref': s.soc_ref,
        }
        storage_data.append(entry)
        if s.connected == AcDcSide.AC:
            storage_by_ac_node.setdefault(node_num, []).append(len(storage_data) - 1)
        else:
            storage_by_dc_node.setdefault(node_num, []).append(len(storage_data) - 1)

    # ------------------------------------------------------------- electrolyser
    h2_data = []
    h2_by_ac_node = {}
    h2_by_dc_node = {}
    for el in grid.electrolysers:
        node_num = el._node.nodeNumber
        entry = {
            'idx': el.electrolyserNumber,
            'node': node_num,
            'connected': el.connected,
            'P_min': el.P_min,
            'P_max': el.P_max,
            'Q_min': el.Q_min if el.connected == AcDcSide.AC else 0.0,
            'Q_max': el.Q_max if el.connected == AcDcSide.AC else 0.0,
            'H2_mass_max': el.H2_mass_max,
            'H2_mass_initial': el.H2_mass_initial,
            'H2_mass_final': el.H2_mass_final,
            'b_h': el.b_h,
            'c_h': el.c_h,
            'S_base': el.S_base,
            'dt_hours': el.dt_hours,
            'h2_price': float(el.h2_price),
        }
        h2_data.append(entry)
        if el.connected == AcDcSide.AC:
            h2_by_ac_node.setdefault(node_num, []).append(len(h2_data) - 1)
        else:
            h2_by_dc_node.setdefault(node_num, []).append(len(h2_data) - 1)

    # ------------------------------------------------------------- heat pumps
    # AC-only controllable load with cumulative energy state (NL/SOCP twin).
    hp_data = []
    hp_by_ac_node = {}
    for hp in grid.heat_pumps:
        node_num = hp._node.nodeNumber
        entry = {
            'idx': hp.heatPumpNumber,
            'node': node_num,
            'P_ref': hp.P_ref,
            'Q_ref': hp.Q_ref,
            'P_unit_max': hp.P_unit_max,
            'np_hp': hp.np_hp,
            'Max_S': hp.Max_S,
            'Q_min': hp.Q_min,
            'Q_max': hp.Q_max,
            'Q_lim_shed': hp.Q_lim_shed,
            'E_min': hp.E_min,
            'E_max': hp.E_max,
            'E_state': hp.E_state,
            'dt_hours': hp.dt_hours,
            'S_base': hp.S_base,
            'qf': hp.qf,
            'lf': hp.lf,
            'qf_q': hp.qf_q,
            'lf_q': hp.lf_q,
        }
        hp_data.append(entry)
        hp_by_ac_node.setdefault(node_num, []).append(len(hp_data) - 1)

    # DC node polarity from converters (L14); conflict → hard error
    dc_pol = {}
    for cd in conv_data:
        k = cd['nDC']
        if k in dc_pol and dc_pol[k] != cd['pol']:
            raise ValueError(
                f"Conflicting converter polarity at DC node {k}: "
                f"{dc_pol[k]} vs {cd['pol']}"
            )
        dc_pol[k] = cd['pol']

    return SimpleNamespace(
        N_AC=N_AC, Ybus_AC=Ybus_AC, E_AC=E_AC,
        V_min_AC=V_min_AC, V_max_AC=V_max_AC, ac_slack=ac_slack,
        ac_line_limits=ac_line_limits,
        N_DC=N_DC, Ybus_DC=Ybus_DC, E_DC=E_DC,
        V_min_DC=V_min_DC, V_max_DC=V_max_DC, dc_slack=dc_slack,
        dc_line_limits=dc_line_limits,
        conv_data=conv_data, conv_ac_nodes=conv_ac_nodes, dc_pol=dc_pol,
        gen_data_AC=gen_data_AC, ren_nodes_AC=ren_nodes_AC, ren_data=ren_data,
        storage_data=storage_data,
        storage_by_ac_node=storage_by_ac_node,
        storage_by_dc_node=storage_by_dc_node,
        h2_data=h2_data,
        h2_by_ac_node=h2_by_ac_node,
        h2_by_dc_node=h2_by_dc_node,
        hp_data=hp_data,
        hp_by_ac_node=hp_by_ac_node,
        Sbase=Sbase,
    )


# ---------------------------------------------------------------------------
# Generator variables
# ---------------------------------------------------------------------------

def generator_variables(d, T):
    """Declare AC generator decision variables."""
    n_gen = len(d.gen_data_AC)
    p_ini = np.array([g['p_ini'] for g in d.gen_data_AC], dtype=float)
    q_ini = np.array([g['q_ini'] for g in d.gen_data_AC], dtype=float)

    PGi_gen = cp.Variable((n_gen, T), name="PGi_gen")
    QGi_gen = cp.Variable((n_gen, T), name="QGi_gen")

    return SimpleNamespace(PGi_gen=PGi_gen, QGi_gen=QGi_gen, p_ini=p_ini, q_ini=q_ini)


# ---------------------------------------------------------------------------
# Generator constraints
# ---------------------------------------------------------------------------

def generator_constraints(d, gen_vars):
    """Build AC generator bounds and capability constraints."""
    constrs = []
    T = d.T
    for gi, gd in enumerate(d.gen_data_AC):
        p_min = gd['p_min']
        p_max = gd['p_max']
        if gd['is_ext_grid'] and gd['node'] in d.P_ext_bounds:
            p_min, p_max = d.P_ext_bounds[gd['node']]
        constrs += [
            gen_vars.PGi_gen[gi, :] >= p_min,
            gen_vars.PGi_gen[gi, :] <= p_max,
            gen_vars.QGi_gen[gi, :] >= gd['q_min'],
            gen_vars.QGi_gen[gi, :] <= gd['q_max'],
        ]
        if gd['max_s'] is not None:
            for t in range(T):
                constrs += [
                    cp.norm(cp.vstack([gen_vars.PGi_gen[gi, t], gen_vars.QGi_gen[gi, t]])) <= gd['max_s']
                ]
    return constrs


# ---------------------------------------------------------------------------
# Storage variables / constraints (continuous overlap or optional MI exclusivity)
# ---------------------------------------------------------------------------

def storage_variables(d, T):
    """Declare BESS charge/discharge, Q (AC), SoC over ``T``.

    By default, ``P_charge`` and ``P_discharge`` are separate non-negative
    continuous variables, so both may be positive in the same period (no
    charge/discharge exclusivity).

    When ``d.bess_mi_exclusivity`` is True, also declares binary mode
    variables ``y_charge`` and ``y_discharge`` that gate charge and discharge
    power; constraints in :func:`storage_constraints` then forbid simultaneous
    charge and discharge.
    """
    n_st = len(d.storage_data)
    if n_st == 0:
        raise ValueError("storage_variables called with empty storage_data")

    P_charge = cp.Variable((n_st, T), nonneg=True, name="P_storage_charge")
    P_discharge = cp.Variable((n_st, T), nonneg=True, name="P_storage_discharge")
    Q_storage = cp.Variable((n_st, T), name="Q_storage")
    SoC = cp.Variable((n_st, T), name="SoC")

    mi = bool(getattr(d, "bess_mi_exclusivity", False))
    y_charge = y_discharge = None
    if mi:
        y_charge = cp.Variable((n_st, T), boolean=True, name="y_storage_charge")
        y_discharge = cp.Variable((n_st, T), boolean=True, name="y_storage_discharge")

    return SimpleNamespace(
        P_charge=P_charge,
        P_discharge=P_discharge,
        Q_storage=Q_storage,
        SoC=SoC,
        y_charge=y_charge,
        y_discharge=y_discharge,
    )


def storage_constraints(d, st_vars):
    """SoC dynamics, charge/discharge limits, and apparent-power limits.

    **Continuous mode** (``bess_mi_exclusivity=False``, default): bounds
    ``P_charge`` and ``P_discharge`` independently. Both can be non-zero in
    the same period — a convex relaxation that allows overlapping charge and
    discharge.

    **MI exclusivity mode** (``bess_mi_exclusivity=True``): charge and
    discharge are gated by binary mode variables so
    ``P_charge <= P_charge_max * y_charge``,
    ``P_discharge <= P_discharge_max * y_discharge``, and
    ``y_charge + y_discharge <= 1`` (at most one direction active per period).

    AC-connected storage uses the S-circle on net power and ``Q``; DC-connected
    storage bounds ``|P_discharge - P_charge|``.
    """
    constrs = []
    T = d.T
    Pc = st_vars.P_charge
    Pd = st_vars.P_discharge
    Qs = st_vars.Q_storage
    SoC = st_vars.SoC
    mi = bool(getattr(d, "bess_mi_exclusivity", False))
    y_c = st_vars.y_charge
    y_d = st_vars.y_discharge
    if mi and (y_c is None or y_d is None):
        raise ValueError(
            "bess_mi_exclusivity=True requires storage y_charge/y_discharge variables"
        )

    for si, sd in enumerate(d.storage_data):
        if mi:
            constrs += [
                Pc[si, :] <= sd['P_charge_max'] * y_c[si, :],
                Pd[si, :] <= sd['P_discharge_max'] * y_d[si, :],
                y_c[si, :] + y_d[si, :] <= 1,
            ]
        else:
            constrs += [
                Pc[si, :] <= sd['P_charge_max'],
                Pd[si, :] <= sd['P_discharge_max'],
            ]
        constrs += [
            SoC[si, :] >= sd['soc_min'],
            SoC[si, :] <= sd['soc_max'],
        ]
        if sd['connected'] == AcDcSide.DC:
            constrs += [Qs[si, :] == 0]
        else:
            constrs += [
                Qs[si, :] >= -sd['S_max'],
                Qs[si, :] <= sd['S_max'],
            ]

        scale = sd['dt_hours'] * sd['S_base'] / sd['E_max']
        for t in range(T):
            soc_prev = sd['soc_initial'] if t == 0 else SoC[si, t - 1]
            constrs += [
                SoC[si, t] == soc_prev + scale * (
                    sd['eta_charge'] * Pc[si, t]
                    - Pd[si, t] / sd['eta_discharge']
                )
            ]
            p_net = Pd[si, t] - Pc[si, t]
            if sd['connected'] == AcDcSide.AC:
                constrs += [
                    cp.norm(cp.vstack([p_net, Qs[si, t]])) <= sd['S_max']
                ]
            else:
                constrs += [
                    p_net <= sd['P_max'],
                    -p_net <= sd['P_max'],
                ]

        if sd['soc_final'] is not None:
            constrs += [SoC[si, T - 1] == sd['soc_final']]

    return constrs


# ---------------------------------------------------------------------------
# Hydrogen variables / constraints (linear, paper Eqs. 13–16)
# ---------------------------------------------------------------------------

def hydrogen_variables(d, T):
    """Declare electrolyser P, optional AC Q, and H₂ mass inventory."""
    n_el = len(d.h2_data)
    if n_el == 0:
        raise ValueError("hydrogen_variables called with empty h2_data")

    P_electrolyser = cp.Variable((n_el, T), name="P_electrolyser")
    Q_electrolyser = cp.Variable((n_el, T), name="Q_electrolyser")
    mass_H2 = cp.Variable((n_el, T), nonneg=True, name="mass_H2")

    return SimpleNamespace(
        P_electrolyser=P_electrolyser,
        Q_electrolyser=Q_electrolyser,
        mass_H2=mass_H2,
    )


def hydrogen_constraints(d, h2_vars):
    """Electrolyser bounds and H₂ mass balance chain."""
    constrs = []
    T = d.T
    Pel = h2_vars.P_electrolyser
    Qel = h2_vars.Q_electrolyser
    mass = h2_vars.mass_H2

    for ei, ed in enumerate(d.h2_data):
        constrs += [
            Pel[ei, :] >= ed['P_min'],
            Pel[ei, :] <= ed['P_max'],
            mass[ei, :] <= ed['H2_mass_max'],
        ]
        if ed['connected'] == AcDcSide.DC:
            constrs += [Qel[ei, :] == 0]
        else:
            constrs += [
                Qel[ei, :] >= ed['Q_min'],
                Qel[ei, :] <= ed['Q_max'],
            ]

        for t in range(T):
            mass_prev = ed['H2_mass_initial'] if t == 0 else mass[ei, t - 1]
            h_prod = (
                ed['b_h'] * Pel[ei, t] * ed['S_base'] * ed['dt_hours']
                + ed['c_h']
            )
            constrs += [mass[ei, t] == mass_prev + h_prod]

        if ed['H2_mass_final'] is not None:
            constrs += [mass[ei, T - 1] == ed['H2_mass_final']]

    return constrs


# ---------------------------------------------------------------------------
# Heat-pump variables / constraints (NL twin: per-unit P/Q + SOCP S circle)
# ---------------------------------------------------------------------------

def heat_pump_variables(d, T):
    """Declare P/Q shed actuators, served P/Q, and cumulative energy over ``T``."""
    n_hp = len(d.hp_data)
    if n_hp == 0:
        raise ValueError("heat_pump_variables called with empty hp_data")

    P_shed = cp.Variable((n_hp, T), nonneg=True, name="P_shed")
    Q_shed = cp.Variable((n_hp, T), name="Q_shed")
    P_heat_pump = cp.Variable((n_hp, T), name="P_heat_pump")
    Q_heat_pump = cp.Variable((n_hp, T), name="Q_heat_pump")
    E_heat_pump = cp.Variable((n_hp, T), name="E_heat_pump")

    return SimpleNamespace(
        P_shed=P_shed,
        Q_shed=Q_shed,
        P_heat_pump=P_heat_pump,
        Q_heat_pump=Q_heat_pump,
        E_heat_pump=E_heat_pump,
    )


def heat_pump_constraints(d, hp_vars):
    """P/Q shed bounds, served-power links, S rating, and energy chain (NL twin).

    Per-unit ``P_heat_pump`` / ``Q_heat_pump`` with nodal totals scaled by
    ``np_hp`` in :func:`ac_constraints`. Refs and energy envelopes are
    time-varying (from ``translate_pyf_socp``).
    """
    constrs = []
    T = d.T
    P_shed = hp_vars.P_shed
    Q_shed = hp_vars.Q_shed
    P_hp = hp_vars.P_heat_pump
    Q_hp = hp_vars.Q_heat_pump
    E = hp_vars.E_heat_pump

    for hi, hd in enumerate(d.hp_data):
        p_ref = d.hp_P_ref[hi]
        q_ref = d.hp_Q_ref[hi]
        e_min = d.hp_E_min[hi]
        e_max = d.hp_E_max[hi]
        p_cap = hd['P_unit_max']
        q_lim = hd['Q_lim_shed']
        q_min = hd['Q_min']
        q_max = hd['Q_max']
        max_s = hd['Max_S']
        np_hp = float(hd['np_hp'])
        dt = hd['dt_hours']
        scale = hd['S_base'] * dt

        for t in range(T):
            e_prev = hd['E_state'] if t == 0 else E[hi, t - 1]
            p_ref_t = p_ref[t]
            q_ref_t = q_ref[t]
            constrs += [
                P_shed[hi, t] >= 0,
                P_shed[hi, t] <= p_cap,
                Q_shed[hi, t] >= -q_lim,
                Q_shed[hi, t] <= q_lim,
                P_hp[hi, t] == p_ref_t - P_shed[hi, t],
                Q_hp[hi, t] == q_ref_t - Q_shed[hi, t],
                Q_hp[hi, t] >= q_min,
                Q_hp[hi, t] <= q_max,
                cp.norm(cp.vstack([P_hp[hi, t], Q_hp[hi, t]])) <= max_s,
                E[hi, t] >= e_min[t],
                E[hi, t] <= e_max[t],
                E[hi, t] == e_prev + P_hp[hi, t] * np_hp * scale,
                P_shed[hi, t] >= e_min[t] / dt - e_prev / dt,
                P_shed[hi, t] <= e_max[t] / dt - e_prev / dt,
            ]

    return constrs


# ---------------------------------------------------------------------------
# AC variables
# ---------------------------------------------------------------------------

def ac_variables(d, T):
    """Declare AC SOCP variables.

    Returns
    -------
    SimpleNamespace
        ``h_AC`` – voltage magnitude squared (N_AC × T)
        ``w_AC`` – sparse cross-product dict (k,m) → (T,) complex
    """
    h_AC = cp.Variable((d.N_AC, T), nonneg=True, name="h_AC")
    w_AC = {e: cp.Variable(T, complex=True, name=f"w_AC_{e[0]}_{e[1]}")
            for e in d.E_AC}

    return SimpleNamespace(h_AC=h_AC, w_AC=w_AC)


# ---------------------------------------------------------------------------
# AC constraints
# ---------------------------------------------------------------------------

def ac_constraints(d, grid, ac_vars, gen_vars, conv_vars, st_vars=None, h2_vars=None, hp_vars=None):
    """Build AC constraints: voltage bounds, SOC lifts, nodal balance, thermals.

    Parameters
    ----------
    d : SimpleNamespace
        Output of :func:`build_socp_data`.
    grid : Grid
        Live grid (used for ACmode flag).
    ac_vars : SimpleNamespace
        Output of :func:`ac_variables`.
    conv_vars : SimpleNamespace or None
        Output of :func:`converter_variables`, or ``None`` if no converters.
    st_vars : SimpleNamespace or None
        Output of :func:`storage_variables`, or ``None`` if no BESS.
    h2_vars : SimpleNamespace or None
        Output of :func:`hydrogen_variables`, or ``None`` if no H₂.
    hp_vars : SimpleNamespace or None
        Output of :func:`heat_pump_variables`, or ``None`` if no heat pumps.
    Returns
    -------
    list
        CVXPY constraints.
    """
    h_AC  = ac_vars.h_AC
    w_AC  = ac_vars.w_AC
    Ss    = conv_vars.Ss if conv_vars is not None else None
    T = d.T

    constrs = []

    for t in range(T):
        # voltage magnitude bounds
        constrs += [h_AC[:, t] >= d.V_min_AC ** 2,
                    h_AC[:, t] <= d.V_max_AC ** 2]

        # slack bus fixed at 1 pu²
        for k in d.ac_slack:
            constrs += [h_AC[k, t] == 1.0]

        # SOC lifts on sparse edges (L19)
        for (k, m) in d.E_AC:
            w_km = w_AC[(k, m)][t]
            constrs += [
                cp.SOC(
                    h_AC[k, t] + h_AC[m, t],
                    cp.vstack([
                        2 * cp.real(w_km),
                        2 * cp.imag(w_km),
                        h_AC[k, t] - h_AC[m, t],
                    ])
                )
            ]

        # nodal power balance: conj(S_k) == flow_k (L11)
        for k in range(d.N_AC):
            flow_k = d.Ybus_AC[k, k] * h_AC[k, t]
            for m in range(d.N_AC):
                if m == k or abs(d.Ybus_AC[k, m]) < 1e-12:
                    continue
                w_km_t = w_AC[(k, m)][t] if (k, m) in w_AC else cp.conj(w_AC[(m, k)][t])
                flow_k = flow_k + d.Ybus_AC[k, m] * w_km_t

            S_k = _ac_node_injection(k, t, d, gen_vars, Ss, st_vars, h2_vars, hp_vars)
            constrs += [flow_k == 0] if S_k is None else [cp.conj(S_k) == flow_k]

        # thermal limits (L15)
        for (k, m), rating_pu in d.ac_line_limits.items():
            w_km_t = w_AC[(k, m)][t] if (k, m) in w_AC else cp.conj(w_AC[(m, k)][t])
            S_km_from = cp.conj(d.Ybus_AC[k, m]) * (h_AC[k, t] - w_km_t)
            S_km_to   = cp.conj(d.Ybus_AC[m, k]) * (h_AC[m, t] - cp.conj(w_km_t))
            constrs += [cp.norm(cp.vstack([cp.real(S_km_from), cp.imag(S_km_from)])) <= rating_pu,
                        cp.norm(cp.vstack([cp.real(S_km_to),   cp.imag(S_km_to)]))   <= rating_pu]

    return constrs


# ---------------------------------------------------------------------------
# DC variables
# ---------------------------------------------------------------------------

def dc_variables(d, T):
    """Declare DC SOCP variables.

    Returns
    -------
    SimpleNamespace
        ``h_DC`` – voltage squared (N_DC × T)
        ``w_DC`` – sparse cross-product dict (k,m) → (T,) real
        ``P_DC``  – nodal active injection (N_DC × T)
    """
    h_DC = cp.Variable((d.N_DC, T), nonneg=True, name="h_DC")
    w_DC = {e: cp.Variable(T, nonneg=True, name=f"w_DC_{e[0]}_{e[1]}")
            for e in d.E_DC}
    P_DC = cp.Variable((d.N_DC, T), name="P_DC")

    return SimpleNamespace(h_DC=h_DC, w_DC=w_DC, P_DC=P_DC)


# ---------------------------------------------------------------------------
# DC constraints
# ---------------------------------------------------------------------------

def dc_constraints(d, dc_vars, st_vars=None, h2_vars=None):
    """Build DC constraints: voltage bounds, SOC lifts, nodal balance, thermals.

    Converter DC nodes use ``pol * flow == P_DC + flex`` (L14). Nodes with
    BESS/H₂ but no converter use ``flow == flex`` (``pol = 1``).

    Returns
    -------
    list
        CVXPY constraints.
    """
    h_DC = dc_vars.h_DC
    w_DC = dc_vars.w_DC
    P_DC = dc_vars.P_DC
    T = d.T

    constrs = []

    dc_balance_nodes = set(d.dc_pol.keys())
    dc_balance_nodes |= set(d.storage_by_dc_node.keys())
    dc_balance_nodes |= set(d.h2_by_dc_node.keys())

    for t in range(T):
        # voltage magnitude bounds
        constrs += [h_DC[:, t] >= d.V_min_DC ** 2,
                    h_DC[:, t] <= d.V_max_DC ** 2]

        # slack bus fixed at 1 pu²
        for k in d.dc_slack:
            constrs += [h_DC[k, t] == 1.0]

        # SOC lifts on sparse edges (L19)
        for (k, m) in d.E_DC:
            w_km = w_DC[(k, m)][t]
            constrs += [
                cp.SOC(
                    h_DC[k, t] + h_DC[m, t],
                    cp.vstack([
                        2 * w_km,
                        h_DC[k, t] - h_DC[m, t],
                    ])
                )
            ]

        # nodal balance (converter + optional BESS/H₂ flex)
        for k in dc_balance_nodes:
            flow_k = d.Ybus_DC[k, k] * h_DC[k, t]
            for m in range(d.N_DC):
                if m == k or abs(d.Ybus_DC[k, m]) < 1e-12:
                    continue
                w_km_t = w_DC[(k, m)][t] if (k, m) in w_DC else w_DC[(m, k)][t]
                flow_k = flow_k + d.Ybus_DC[k, m] * w_km_t
            flex = _dc_flex_injection(k, t, d, st_vars, h2_vars)
            if k in d.dc_pol:
                constrs += [d.dc_pol[k] * flow_k == P_DC[k, t] + flex]
            else:
                constrs += [flow_k == flex]

        # thermal limits (L15)
        for (k, m), rating_pu in d.dc_line_limits.items():
            w_km_t = w_DC[(k, m)][t] if (k, m) in w_DC else w_DC[(m, k)][t]
            P_km = (h_DC[k, t] - w_km_t) * d.Ybus_DC[k, m]
            P_mk = (h_DC[m, t] - w_km_t) * d.Ybus_DC[m, k]
            constrs += [cp.abs(P_km) <= rating_pu,
                        cp.abs(P_mk) <= rating_pu]

    return constrs


# ---------------------------------------------------------------------------
# Converter variables
# ---------------------------------------------------------------------------

def converter_variables(d, T):
    """Declare VSC converter variables.

    Returns
    -------
    SimpleNamespace
        ``Ss``    – AC-side apparent power (n_conv × T) complex
        ``Ploss`` – converter losses       (n_conv × T) real
        ``t_abs`` – epigraph of ``|Re(Ss)|`` for affine loss (n_conv × T)
    """
    n_conv = len(d.conv_data)
    Ss    = cp.Variable((n_conv, T), complex=True, name="Ss")
    Ploss = cp.Variable((n_conv, T), name="Ploss")
    t_abs = cp.Variable((n_conv, T), nonneg=True, name="t_abs_Pconv")

    return SimpleNamespace(Ss=Ss, Ploss=Ploss, t_abs=t_abs)


# ---------------------------------------------------------------------------
# Converter constraints
# ---------------------------------------------------------------------------

def converter_constraints(d, conv_vars, dc_vars):
    """Build converter constraints: power balance, loss model, rating.

    Loss model (Paper A Eqs. 10–12, DCP form):
    ``t >= |Re(Ss)|``, ``Ploss == a + b * t`` with ``a_conv`` / ``b_conv``.

    Returns
    -------
    list
        CVXPY constraints.
    """
    Ss    = conv_vars.Ss
    Ploss = conv_vars.Ploss
    t_abs = conv_vars.t_abs
    P_DC  = dc_vars.P_DC
    T = d.T

    constrs = []

    for t in range(T):
        for ci, cd in enumerate(d.conv_data):
            # power balance: Re(Ss) + P_DC + Ploss = 0
            constrs += [cp.real(Ss[ci, t]) + P_DC[cd['nDC'], t] + Ploss[ci, t] == 0]

            # affine loss via |Re(Ss)| epigraph (L13 / paper b, not c_rect)
            constrs += [
                t_abs[ci, t] >= cp.abs(cp.real(Ss[ci, t])),
                Ploss[ci, t] == cd['a'] + cd['b'] * t_abs[ci, t],
            ]

            # apparent power rating
            constrs += [cp.norm(Ss[ci, t]) <= cd['Smax']]

    return constrs


# ---------------------------------------------------------------------------
# Top-level model builder
# ---------------------------------------------------------------------------

def socp_model(grid, d):
    """Build all CVXPY SOCP variables and constraints for prepared SOCP data.

    Parameters
    ----------
    grid : Grid
        pyflow_acdc grid (``analyse_grid`` must have been called).
    d : SimpleNamespace
        Prepared SOCP data object with static grid data plus translated
        multiperiod inputs (``T``, ``frame_ids``, ``P_ren``, ``prices``,
        ``P_ext_bounds``).

    Returns
    -------
    tuple
        ``(constraints, variables)`` where *variables* is a SimpleNamespace
        holding all CVXPY variable blocks.
    """
    T = d.T

    # -- variables -----------------------------------------------------------
    gen_vars  = generator_variables(d, T) if grid.ACmode and d.gen_data_AC else None
    ac_vars   = ac_variables(d, T)
    dc_vars   = dc_variables(d, T)   if grid.DCmode             else None
    conv_vars = converter_variables(d, T) if grid.ACmode and grid.DCmode and d.conv_data else None
    st_vars   = storage_variables(d, T) if grid.ESS and d.storage_data else None
    h2_vars   = hydrogen_variables(d, T) if grid.H2 and d.h2_data else None
    hp_vars   = heat_pump_variables(d, T) if grid.HP and d.hp_data else None

    if grid.ESS and not d.storage_data:
        raise ValueError("grid.ESS is True but storage_data is empty")
    if grid.H2 and not d.h2_data:
        raise ValueError("grid.H2 is True but h2_data is empty")
    if grid.HP and not d.hp_data:
        raise ValueError("grid.HP is True but hp_data is empty")

    # -- constraints ---------------------------------------------------------
    constrs  = generator_constraints(d, gen_vars) if gen_vars is not None else []
    if st_vars is not None:
        constrs += storage_constraints(d, st_vars)
    if h2_vars is not None:
        constrs += hydrogen_constraints(d, h2_vars)
    if hp_vars is not None:
        constrs += heat_pump_constraints(d, hp_vars)
    constrs += ac_constraints(d, grid, ac_vars, gen_vars, conv_vars, st_vars, h2_vars, hp_vars)
    if grid.DCmode:
        constrs += dc_constraints(d, dc_vars, st_vars, h2_vars)
    if grid.ACmode and grid.DCmode and d.conv_data:
        constrs += converter_constraints(d, conv_vars, dc_vars)

    variables = SimpleNamespace(
        gen=gen_vars,
        ac=ac_vars,
        dc=dc_vars,
        conv=conv_vars,
        storage=st_vars,
        hydrogen=h2_vars,
        heat_pump=hp_vars,
    )

    return constrs, variables


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ac_node_injection(k, t, d, gen_vars, Ss, st_vars=None, h2_vars=None, hp_vars=None):
    """Return the net complex injection at AC node *k*, time *t*.

    Returns ``None`` for zero-injection nodes.
    """
    parts = []

    if gen_vars is not None:
        for gi, gd in enumerate(d.gen_data_AC):
            if gd['node'] == k:
                parts.append(gen_vars.PGi_gen[gi, t] + 1j * gen_vars.QGi_gen[gi, t])

    if k in d.ren_nodes_AC:
        p_t = float(d.P_ren[k][t]) if k in d.P_ren else d.ren_nodes_AC[k][0]
        parts.append(p_t + 1j * d.ren_nodes_AC[k][1])

    if Ss is not None and k in d.conv_ac_nodes:
        for ci, cd in enumerate(d.conv_data):
            if cd['nAC'] == k:
                parts.append(Ss[ci, t])

    if st_vars is not None and k in d.storage_by_ac_node:
        for si in d.storage_by_ac_node[k]:
            parts.append(
                (st_vars.P_discharge[si, t] - st_vars.P_charge[si, t])
                + 1j * st_vars.Q_storage[si, t]
            )

    if h2_vars is not None and k in d.h2_by_ac_node:
        for ei in d.h2_by_ac_node[k]:
            # P is a load; Q is reactive injection (NL sign convention)
            parts.append(
                -h2_vars.P_electrolyser[ei, t] + 1j * h2_vars.Q_electrolyser[ei, t]
            )

    if hp_vars is not None and k in d.hp_by_ac_node:
        for hi in d.hp_by_ac_node[k]:
            np_hp = float(d.hp_data[hi]['np_hp'])
            p_hp = hp_vars.P_heat_pump[hi, t] * np_hp
            q_hp = hp_vars.Q_heat_pump[hi, t] * np_hp
            parts.append(-p_hp - 1j * q_hp)

    if not parts:
        return None

    result = parts[0]
    for p in parts[1:]:
        result = result + p
    return result


def _dc_flex_injection(k, t, d, st_vars, h2_vars):
    """Net DC flexible injection at node *k*: +BESS net − electrolyser load."""
    flex = 0
    if st_vars is not None and k in d.storage_by_dc_node:
        for si in d.storage_by_dc_node[k]:
            flex = flex + (
                st_vars.P_discharge[si, t] - st_vars.P_charge[si, t]
            )
    if h2_vars is not None and k in d.h2_by_dc_node:
        for ei in d.h2_by_dc_node[k]:
            flex = flex - h2_vars.P_electrolyser[ei, t]
    return flex
