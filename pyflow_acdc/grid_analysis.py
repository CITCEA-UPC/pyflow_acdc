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
    "Converter_parameters",
    "Cable_parameters",
    "grid_state",
    "analyse_grid",
    "current_fuel_type_distribution",
]


def pol2cart(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y


def pol2cartz(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = x + 1j * y
    return z


def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return rho, theta


def cartz2pol(z):
    r = np.abs(z)
    theta = np.angle(z)
    return r, theta


def Converter_parameters(S_base, kV_base, T_R_Ohm, T_X_mH, PR_R_Ohm, PR_X_mH, Filter_uF, f=50):
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


def Cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km, N_cables=1, f=50):
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


def grid_state(grid):
    Total_load = 0
    min_generation = 0
    max_generation = 0
    for node in grid.nodes_AC:
        Total_load += node.PLi
    for node in grid.nodes_DC:
        Total_load += node.PLi
    for gen in grid.Generators:
        if getattr(gen, 'is_ext_grid', False):
            if getattr(gen, 'allow_sell', True):
                min_eff = -(gen.Max_pow_gen * gen.np_gen - gen.p_load_eff)
            else:
                min_eff = 0
        else:
            min_eff = gen.Min_pow_gen * gen.np_gen
        min_generation += min_eff if not gen.activate_gen_opf else 0
        max_generation += gen.Max_pow_gen * gen.np_gen

    for ren in grid.RenSources:
        min_generation += ren.PGi_ren * ren.min_gamma
        max_generation += ren.PGi_ren
    return Total_load, min_generation, max_generation


def analyse_grid(grid):
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

    return grid.ACmode, grid.DCmode, [grid.TEP_AC, grid.TAP_tf, grid.REC_AC, grid.CT_AC], [grid.CFC, grid.CDC], grid.GPR


def current_fuel_type_distribution(grid, output="df"):
    """
    Build current generation-type distribution summary.

    The summary follows Static TEP style normalization (lowercase types) and
    includes both conventional generators and renewable sources.
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
