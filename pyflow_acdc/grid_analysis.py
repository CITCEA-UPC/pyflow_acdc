"""
Analysis and utility helpers for pyflow_acdc grids.
"""

import numpy as np
import pandas as pd

from .constants import SQRT_3


__all__ = [
    "pol2cart",
    "pol2cartz",
    "cart2pol",
    "cartz2pol",
    "converter_parameters",
    "cable_parameters",
    "get_gen_p_min_eff",
    "grid_state",
    "analyse_grid",
    "current_fuel_type_distribution",
]


def pol2cart(r, theta):
    """Convert polar coordinates to Cartesian.

    Parameters
    ----------
    r : float
        Radius.
    theta : float
        Angle in radians.

    Returns
    -------
    tuple
        ``(x, y)``.
    """
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y


def pol2cartz(r, theta):
    """Convert polar coordinates to a complex number.

    Parameters
    ----------
    r : float
        Radius.
    theta : float
        Angle in radians.

    Returns
    -------
    complex
        ``x + j y``.
    """
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = x + 1j * y
    return z


def cart2pol(x, y):
    """Convert Cartesian coordinates to polar.

    Parameters
    ----------
    x, y : float
        Cartesian components.

    Returns
    -------
    tuple
        ``(rho, theta)`` with ``theta`` in radians.
    """
    rho = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return rho, theta


def cartz2pol(z):
    """Convert a complex number to polar coordinates.

    Parameters
    ----------
    z : complex
        Complex value ``x + j y``.

    Returns
    -------
    tuple
        ``(r, theta)`` with ``theta`` in radians.
    """
    r = np.abs(z)
    theta = np.angle(z)
    return r, theta


def converter_parameters(S_base, kV_base, T_R_Ohm, T_X_mH, PR_R_Ohm, PR_X_mH, Filter_uF, f=50):
    """Convert converter transformer/reactor/filter data to per-unit values.

    Parameters
    ----------
    S_base : float
        System power base in MVA.
    kV_base : float
        Voltage base in kV.
    T_R_Ohm, T_X_mH : float
        Transformer resistance (ohm) and inductance (mH).
    PR_R_Ohm, PR_X_mH : float
        Phase-reactor resistance (ohm) and inductance (mH).
    Filter_uF : float
        Filter capacitance in microfarad.
    f : float, optional
        System frequency in Hz (default 50).

    Returns
    -------
    list
        ``[T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu]`` in per unit.
    """
    Z_base = kV_base**2 / S_base  # kv^2/MVA
    Y_base = 1 / Z_base

    F = Filter_uF * 10 ** (-6)
    PR_X_H = PR_X_mH / 1000
    T_X_H = T_X_mH / 1000

    B = 2 * f * F * np.pi
    T_X = 2 * f * T_X_H * np.pi
    PR_X = 2 * f * PR_X_H * np.pi

    T_R_pu = T_R_Ohm / Z_base
    T_X_pu = T_X / Z_base
    PR_R_pu = PR_R_Ohm / Z_base
    PR_X_pu = PR_X / Z_base
    Filter_pu = B / Y_base

    return [T_R_pu, T_X_pu, PR_R_pu, PR_X_pu, Filter_pu]


def cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km, N_cables=1, f=50):
    """Convert cable data to per-unit equivalent parameters and rating.

    For DC cables (``L_mH == 0``) ``N_cables`` is forced to 1 and a 2-conductor
    MVA rating is used; otherwise a 3-phase (``sqrt(3)``) rating is used.

    Parameters
    ----------
    S_base : float
        System power base in MVA.
    R : float
        Series resistance per km (ohm/km).
    L_mH, C_uF, G_uS : float
        Per-km inductance (mH), capacitance (microF), and shunt conductance
        (microS).
    A_rating : float
        Current rating in A.
    kV_base : float
        Voltage base in kV.
    km : float
        Cable length in km.
    N_cables : int, optional
        Number of parallel cables (default 1).
    f : float, optional
        System frequency in Hz (default 50).

    Returns
    -------
    list
        ``[Rpu, Xpu, Gpu, Bpu, MVA_rating]`` (per-unit parameters + MVA rating).
    """
    Z_base = kV_base**2 / S_base  # kv^2/MVA
    Y_base = 1 / Z_base

    if L_mH == 0:
        N_cables = 1
        MVA_rating = N_cables * A_rating * kV_base / (1000)
        # IN DC N cables is always 1 as the varible is used directly in the formulation
    else:
        MVA_rating = N_cables * A_rating * kV_base * SQRT_3 / (1000)

    C = C_uF * (10 ** (-6))
    L = L_mH / 1000
    G = G_uS * (10 ** (-6))

    R_AC = R * km

    B = 2 * f * C * np.pi * km
    X = 2 * f * L * np.pi * km

    Z = R_AC + X * 1j
    Y = G + B * 1j

    Z_pi = Z
    Y_pi = Y

    R_1 = np.real(Z_pi)
    X_1 = np.imag(Z_pi)
    G_1 = np.real(Y_pi)
    B_1 = np.imag(Y_pi)

    Req = R_1 / N_cables
    Xeq = X_1 / N_cables
    Geq = G_1 * N_cables
    Beq = B_1 * N_cables

    Rpu = Req / Z_base
    Xpu = Xeq / Z_base
    Gpu = Geq / Y_base
    Bpu = Beq / Y_base

    return [Rpu, Xpu, Gpu, Bpu, MVA_rating]


def get_gen_p_min_eff(gen, np_gen_value, p_load_eff_value=None):
    """Effective lower active-power bound (pu) for a generator at ``np_gen_value`` parallel units."""
    if not getattr(gen, 'is_ext_grid', False):
        return gen.Min_pow_gen * np_gen_value
    if not getattr(gen, 'allow_sell', True):
        return 0
    pmax_eff = gen.Max_pow_gen * np_gen_value
    if pmax_eff == 0:
        return gen.Min_pow_gen * np_gen_value
    p_load_eff = gen.p_load_eff if p_load_eff_value is None else p_load_eff_value
    return -(pmax_eff - p_load_eff)


def grid_state(grid):
    """Return aggregate load and generation bounds for the current grid.

    Parameters
    ----------
    grid : Grid
        Network to summarise.

    Returns
    -------
    tuple
        ``(total_load, min_generation, max_generation)`` in per unit.
    """
    Total_load = 0
    min_generation = 0
    max_generation = 0
    for node in grid.nodes_AC:
        Total_load += node.PLi
    for node in grid.nodes_DC:
        Total_load += node.PLi
    for gen in grid.Generators:
        min_eff = get_gen_p_min_eff(gen, gen.np_gen)
        min_generation += min_eff if not gen.activate_gen_opf else 0
        max_generation += gen.Max_pow_gen * gen.np_gen

    for ren in grid.RenSources:
        min_generation += ren.PGi_ren * ren.min_gamma
        max_generation += ren.PGi_ren
    return Total_load, min_generation, max_generation


def analyse_grid(grid):
    """Detect enabled grid features and store boolean flags on ``grid``.

    Sets ``ACmode``, ``DCmode``, ``TEP_AC``, ``REC_AC``, ``TAP_tf``, ``CT_AC``,
    ``CFC``, ``CDC``, ``GPR``, ``rs_GPR``, ``act_gen``, ``ESS``, ``H2``, and ``HP``.
    Called at the start of power-flow, OPF, and TEP entry points.

    Parameters
    ----------
    grid : Grid
        Network to analyse (mutated in place).

    Returns
    -------
    tuple
        ``(ACmode, DCmode, [TEP_AC, TAP_tf, REC_AC, CT_AC], [CFC, CDC], GPR)``.
    """
    def _has_positive_planned_install(element):
        planned = getattr(element, "planned_installation", 0)
        if isinstance(planned, np.ndarray):
            return bool(np.any(planned > 0))
        if isinstance(planned, (list, tuple)):
            return any(float(v) > 0 for v in planned)
        try:
            return float(planned) > 0
        except (TypeError, ValueError):
            return False

    # Perform the analysis and store directly on grid
    grid.ACmode = grid.nn_AC != 0  # AC nodes present
    grid.DCmode = grid.nn_DC != 0  # DC nodes present
    grid.TEP_AC = grid.nle_AC != 0  # AC expansion lines present
    grid.REC_AC = grid.nlr_AC != 0  # AC reconductoring lines present
    grid.TAP_tf = grid.nttf != 0  # AC transformer lines present
    grid.CT_AC = grid.nct_AC != 0  # AC conductor size selection lines present
    grid.CFC = grid.ncfc_DC != 0  # DC variable voltage converter lines present
    grid.CDC = grid.ncdc_DC != 0  # DC-DC converter lines present
    grid.GPR = any(
        gen.np_gen_opf or _has_positive_planned_install(gen)
        for gen in grid.Generators
    )
    grid.rs_GPR = any(
        rs.np_rsgen_opf or _has_positive_planned_install(rs)
        for rs in grid.RenSources
    )
    grid.act_gen = any(gen.activate_gen_opf for gen in grid.Generators)
    grid.ESS = bool(grid.storage_elements)
    grid.H2 = bool(grid.electrolysers)
    grid.HP = bool(grid.heat_pumps)

    return grid.ACmode, grid.DCmode, [grid.TEP_AC, grid.TAP_tf, grid.REC_AC, grid.CT_AC], [grid.CFC, grid.CDC], grid.GPR


def current_fuel_type_distribution(grid, output="df"):
    """Summarise installed capacity by generation type (Static TEP style).

    Parameters
    ----------
    grid : Grid
        Network whose generators and renewable sources are counted.
    output : str, optional
        ``'df'`` for a :class:`pandas.DataFrame`, ``'dict'`` for a nested dict.

    Returns
    -------
    pandas.DataFrame or dict
        Rows per fuel/technology plus ``'All'`` and system-load summary.
    """

    def _norm(t):
        return str(t).lower() if t else None

    type_capacity = {}
    type_units = {}
    type_limits = {_norm(k): v for k, v in grid.current_generation_type_limits.items()}

    for gen in getattr(grid, "Generators", []):
        gt = _norm(getattr(gen, "gen_type", None))
        if gt is None:
            continue
        units = float(getattr(gen, "np_gen", 1.0))
        cap = float(getattr(gen, "Max_pow_gen", 0.0)) * units
        type_units[gt] = type_units.get(gt, 0.0) + units
        type_capacity[gt] = type_capacity.get(gt, 0.0) + cap

    for rs in getattr(grid, "RenSources", []):
        rt = _norm(getattr(rs, "rs_type", None))
        if rt is None:
            continue
        units = float(getattr(rs, "np_rsgen", 1.0))
        cap = float(getattr(rs, "PGi_ren_base", 0.0)) * units
        type_units[rt] = type_units.get(rt, 0.0) + units
        type_capacity[rt] = type_capacity.get(rt, 0.0) + cap

    total_cap = sum(type_capacity.values())
    total_units = sum(type_units.values())
    load_nodes_count = sum(1 for node in grid.nodes_AC if node.PLi != 0.0) + sum(1 for node in grid.nodes_DC if node.PLi != 0.0)

    total_system_load = (
        sum((node.PLi_base + node._PLi_extgrid) * node.PLi_inv_factor for node in grid.nodes_AC)
        + sum(node.PLi_base * node.PLi_inv_factor for node in grid.nodes_DC)
    )
    load_pct_of_total_cap = round((total_system_load / total_cap) * 100.0, 2) if total_cap > 0 else 0.0

    rows = []
    for typ in sorted(type_capacity):
        cap = type_capacity[typ]
        units = type_units.get(typ, 0.0)
        pct = round((cap / total_cap * 100.0), 2) if total_cap > 0 else 0.0
        limit = type_limits.get(typ)
        rows.append(
            {
                "Type": typ,
                "number of gen": units,
                "total install cap": cap,
                "percentage": pct,
                "current limit": round(float(limit) * 100.0, 2) if limit is not None else None,
            }
        )

    rows.append(
        {
            "Type": "All",
            "number of gen": total_units,
            "total install cap": total_cap,
            "percentage": 100.0 if total_cap > 0 else 0.0,
            "current limit": None,
        }
    )
    rows.append(
        {
            "Type": "System load (all nodes)",
            "number of gen": load_nodes_count,
            "total install cap": total_system_load,
            "percentage": load_pct_of_total_cap,
            "current limit": None,
        }
    )

    if output == "df":
        return pd.DataFrame(rows, columns=["Type", "number of gen", "total install cap", "percentage", "current limit"])
    if output == "dict":
        return {
            row["Type"]: {
                "number of gen": row["number of gen"],
                "total install cap": row["total install cap"],
                "percentage": row["percentage"],
                "current limit": row["current limit"],
            }
            for row in rows
        }
    raise ValueError("output must be either 'df' or 'dict'")
