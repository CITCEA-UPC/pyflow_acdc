# -*- coding: utf-8 -*-
"""Sparse SOCP smoke and parity checks."""

import pandas as pd
import pytest
import pyflow_acdc as pyf

from pyflow_tests._test_solver_deps import require_ipopt, require_socp, socp_solver

SOCP_ENERGY = {"Energy_cost": {"w": 1}}
SOCP_ENERGY_H2 = {"Energy_cost": {"w": 1}, "H2_sale": {"w": 1}}


def _case39_socp_grid():
    return pyf.cases["case39_acdc"]()[0]


def _case39_socp_grid_with_flex_and_ts(n_frames=3):
    grid = _case39_socp_grid()
    pyf.add_storage(
        grid,
        "30",
        E_max_MWh=100.0,
        P_charge_MW=33.0,
        P_discharge_MW=33.0,
        eta_charge=0.85,
        eta_discharge=0.90,
        soc_initial=0.5,
    )
    pyf.add_electrolyser(
        grid,
        "30",
        P_max_MW=20.0,
        P_min_MW=0.0,
        b_h=0.02,
        c_h=0.0,
        H2_mass_max_kg=1000.0,
        H2_mass_initial_kg=0.0,
        h2_price=2.0,
    )
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": [1.0, 0.92, 1.05][:n_frames]}),
        associated="30",
        TS_type="Load",
    )
    return grid


def test_socp_builds_case39_acdc():
    require_socp()
    grid = _case39_socp_grid()
    problem, variables, timing, stats = pyf.socp_optimise(
        grid,
        build_only=True,
        weights_def=SOCP_ENERGY,
    )

    assert problem is not None
    assert variables.ac is not None
    assert variables.dc is not None
    assert variables.conv is not None
    assert stats["n_vars"] > 0
    assert stats["n_constr"] > 0
    assert timing["build"] >= 0


def test_socp_solves_case39_acdc():
    require_socp()
    grid = _case39_socp_grid()
    _, _, _, stats = pyf.socp_optimise(
        grid,
        solver=socp_solver(),
        weights_def=SOCP_ENERGY,
    )

    assert stats["status"] in ("optimal", "optimal_inaccurate")
    assert stats["solver"] == socp_solver()
    assert grid.socp_run is True
    assert grid.nodes_AC[0].V_AC is not None
    assert grid.Converters_ACDC[0].P_loss >= 0


def test_soc_window_optimisation_solves_case39_with_bess_h2():
    require_socp()
    grid = _case39_socp_grid_with_flex_and_ts()
    _, variables, _, stats = pyf.soc_window_optimisation(
        grid,
        frame_ids=[0, 1, 2],
        solver=socp_solver(),
        weights_def=SOCP_ENERGY_H2,
    )

    assert stats["status"] in ("optimal", "optimal_inaccurate")
    assert variables.storage is not None
    assert variables.hydrogen is not None
    assert grid.storage_elements[0].SoC is not None
    assert grid.electrolysers[0].mass_H2 >= 0


def test_socp_builds_with_bess_mi_exclusivity():
    require_socp()
    grid = _case39_socp_grid_with_flex_and_ts(n_frames=1)
    _, variables, _, stats = pyf.socp_optimise(
        grid,
        build_only=True,
        bess_mi_exclusivity=True,
        weights_def=SOCP_ENERGY,
    )

    assert variables.storage is not None
    assert variables.storage.y_charge is not None
    assert variables.storage.y_discharge is not None
    assert stats["n_vars"] > 0


def test_socp_ccp_builds_case39_acdc():
    require_socp()
    grid = _case39_socp_grid()
    problem, variables, _, stats = pyf.socp_ccp_optimise(
        grid,
        confidence_level=0.95,
        build_only=True,
        weights_def=SOCP_ENERGY,
    )

    assert problem is not None
    assert variables.ac is not None
    assert stats["n_vars"] > 0


def test_apply_ccp_quantiles_tightens_wind_cap():
    require_socp()
    from pyflow_acdc.ACDC_convex import apply_ccp_quantiles, translate_pyf_socp

    grid = _case39_socp_grid()
    pyf.add_RenSource(grid, "30", base_MW=100.0, available=0.5)
    pyf.analyse_grid(grid)
    socp_data = translate_pyf_socp(grid, frame_ids=[0])
    node = next(iter(socp_data.P_ren))
    p_before = float(socp_data.P_ren[node][0])

    apply_ccp_quantiles(socp_data, grid, confidence_level=0.95)
    p_after = float(socp_data.P_ren[node][0])

    assert p_after < p_before


def test_socp_builds_with_energy_cost_pricing():
    require_socp()
    grid = _case39_socp_grid()
    grid.nodes_AC[0].price = 50.0
    problem, _, _, stats = pyf.socp_optimise(
        grid,
        build_only=True,
        weights_def=SOCP_ENERGY,
    )
    assert problem is not None
    assert stats["n_vars"] > 0


def test_apply_ccp_quantiles_skips_price_without_energy_cost_weight():
    require_socp()
    from pyflow_acdc.ACDC_convex import apply_ccp_quantiles, translate_pyf_socp

    grid = _case39_socp_grid()
    grid.nodes_AC[0].price = 100.0
    pyf.analyse_grid(grid)
    socp_data = translate_pyf_socp(grid, frame_ids=[0])
    before = socp_data.prices[0][0]
    apply_ccp_quantiles(
        socp_data,
        grid,
        confidence_level=0.95,
        weights_def={"AC_losses": {"w": 1}},
    )
    assert socp_data.prices[0][0] == before


def test_apply_ccp_quantiles_applies_price_with_energy_cost_weight():
    require_socp()
    from pyflow_acdc.ACDC_convex import apply_ccp_quantiles, translate_pyf_socp

    grid = _case39_socp_grid()
    grid.nodes_AC[0].price = 100.0
    pyf.analyse_grid(grid)
    socp_data = translate_pyf_socp(grid, frame_ids=[0])
    before = socp_data.prices[0][0]
    apply_ccp_quantiles(
        socp_data,
        grid,
        confidence_level=0.95,
        weights_def=SOCP_ENERGY,
    )
    assert socp_data.prices[0][0] != before


def test_resolve_socp_solver_warns_on_non_mi_solver():
    require_socp()
    from pyflow_acdc.solver_utils import SOCP_MI_CAPABLE_SOLVERS, resolve_socp_solver

    cont = resolve_socp_solver()
    if cont is None or cont in SOCP_MI_CAPABLE_SOLVERS:
        pytest.skip("need a non-MI SOCP solver (e.g. CLARABEL or SCS only)")

    with pytest.warns(UserWarning, match="may not support SOCP with boolean"):
        resolve_socp_solver(mi_required=True, solver=cont)


def test_soc_window_optimisation_solves_with_bess_mi_exclusivity():
    from pyflow_tests._test_solver_deps import socp_mi_solver

    require_socp()
    grid = _case39_socp_grid_with_flex_and_ts()
    _, variables, _, stats = pyf.soc_window_optimisation(
        grid,
        frame_ids=[0, 1, 2],
        solver=socp_mi_solver(),
        bess_mi_exclusivity=True,
        weights_def=SOCP_ENERGY,
    )

    assert stats["status"] in ("optimal", "optimal_inaccurate")
    yc = variables.storage.y_charge.value
    yd = variables.storage.y_discharge.value
    assert yc is not None and yd is not None
    assert (yc + yd <= 1.0 + 1e-5).all()


def _case39_socp_grid_with_heat_pump(n_frames=3):
    grid = _case39_socp_grid()
    hp = pyf.add_heat_pump(
        grid,
        "30",
        P_ref_MW=0.08,
        Q_ref_MVAR=-0.02,
        np_hp=2,
        P_unit_max_MW=1.76 / 1000,
        S_rated_MVAR=0.1,
        E_min_kWh=-5.0,
        E_max_kWh=5.0,
        E_state_initial_kWh=0.0,
    )
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": [1.0, 0.92, 1.05][:n_frames]}),
        associated="30",
        TS_type="Load",
    )
    return grid, hp


def test_socp_builds_case39_acdc_with_heat_pump():
    require_socp()
    grid, _ = _case39_socp_grid_with_heat_pump()
    problem, variables, _, stats = pyf.socp_optimise(
        grid,
        build_only=True,
        weights_def=SOCP_ENERGY,
    )

    assert problem is not None
    assert variables.heat_pump is not None
    assert stats["n_vars"] > 0


def test_soc_window_optimisation_solves_case39_with_heat_pump():
    require_socp()
    grid, hp = _case39_socp_grid_with_heat_pump()
    _, variables, _, stats = pyf.soc_window_optimisation(
        grid,
        frame_ids=[0, 1, 2],
        solver=socp_solver(),
        weights_def=SOCP_ENERGY,
    )

    assert stats["status"] in ("optimal", "optimal_inaccurate")
    assert variables.heat_pump is not None

    P = grid.socp_results.P_heat_pump
    assert P is not None and P.shape == (1, 3)

    p_ref = hp.P_ref
    p_cap = hp.P_unit_max
    assert (P[0, :] <= p_ref + 1e-6).all()
    assert (P[0, :] >= p_ref - p_cap - 1e-6).all()

    Q_shed = grid.socp_results.Q_shed
    assert Q_shed is not None and Q_shed.shape == (1, 3)
    q_lim = hp.Q_lim_shed
    assert (Q_shed[0, :] <= q_lim + 1e-6).all()
    assert (Q_shed[0, :] >= -q_lim - 1e-6).all()

    Q = grid.socp_results.Q_heat_pump
    assert Q is not None and Q.shape == (1, 3)
    assert (Q[0, :] <= hp.Q_max + 1e-6).all()
    assert (Q[0, :] >= hp.Q_min - 1e-6).all()
    assert (Q[0, :] <= hp.Q_ref + q_lim + 1e-6).all()
    assert (Q[0, :] >= hp.Q_ref - q_lim - 1e-6).all()


def test_pei_soc_window_builds_short_horizon():
    require_socp()
    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
    )
    problem, variables, _, stats = pyf.soc_window_optimisation(
        grid,
        frame_ids=[0, 1, 2],
        build_only=True,
        weights_def=SOCP_ENERGY,
    )

    assert problem is not None
    assert variables.storage is not None
    assert variables.hydrogen is not None
    assert stats["n_vars"] > 0
    assert stats["n_constr"] > 0


@pytest.mark.slow
def test_socp_and_nl_case39_voltage_are_close_when_ipopt_available():
    require_socp()
    require_ipopt()

    grid_socp = _case39_socp_grid()
    grid_nl = _case39_socp_grid()

    pyf.socp_optimise(grid_socp, solver=socp_solver(), weights_def=SOCP_ENERGY)
    pyf.optimal_pf(grid_nl, ObjRule={"Energy_cost": 1}, solver="ipopt", tee=False)

    node_name = "30"
    v_socp = next(n.V_AC for n in grid_socp.nodes_AC if n.name == node_name)
    v_nl = next(n.V for n in grid_nl.nodes_AC if n.name == node_name)

    assert abs(v_socp - v_nl) < 0.08
