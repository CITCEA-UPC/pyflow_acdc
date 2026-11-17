# -*- coding: utf-8 -*-
"""Heat-pump planning-model tests."""

import pandas as pd
import pytest
import pyflow_acdc as pyf
import pyomo.environ as pyo

from pyflow_tests._test_solver_deps import require_pyomo


def _grid_with_heat_pump():
    grid, _ = pyf.cases["case39"]()
    hp = pyf.add_heat_pump(
        grid,
        "4",
        P_ref_MW=0.08,
        Q_ref_MVAR=-0.02,
        np_hp=2,
        P_unit_max_MW=1.76 / 1000,
        E_min_kWh=-5.0,
        E_max_kWh=5.0,
        E_state_initial_kWh=0.0,
    )
    return grid, hp


def _attach_ts(grid, hp, n_frames=4):
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": [1.0] * n_frames}),
        associated="4",
        TS_type="Load",
    )
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"e_min": [-5.0, -4.0, -3.0, -2.0]}),
        associated=hp.name,
        TS_type="hp_E_min",
    )
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"e_max": [5.0, 6.0, 7.0, 8.0]}),
        associated=hp.name,
        TS_type="hp_E_max",
    )


def test_heat_pump_model_builds_and_bounds_match_montse():
    require_pyomo()
    grid, hp = _grid_with_heat_pump()
    pyf.analyse_grid(grid)
    assert grid.HP is True

    model, _, _, _ = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    h = hp.heatPumpNumber
    energy_p_shed_lb = hp.E_min / hp.dt_hours - hp.E_state / hp.dt_hours
    energy_p_shed_ub = hp.E_max / hp.dt_hours - hp.E_state / hp.dt_hours
    p_shed_cap = hp.P_unit_max
    q_shed_lim = hp.Q_lim_shed
    q_injected_lb = hp.Q_min
    q_injected_ub = hp.Q_max

    assert hasattr(model, "heat_pumps")
    assert hasattr(model, "P_shed")
    assert hasattr(model, "Q_shed")
    assert hasattr(model, "Q_heat_pump")
    assert hasattr(model, "P_heat_pump")
    assert hasattr(model, "E_heat_pump")
    assert hasattr(model, "Gen_Pheatpump_constraint")
    assert model.hp_p_ref[h].value == pytest.approx(hp.P_ref)
    assert model.hp_q_ref[h].value == pytest.approx(hp.Q_ref)
    assert int(model.np_hp[h]) == hp.np_hp
    assert hp.Max_S == pytest.approx(hp.P_unit_max)
    assert hp.Q_lim_shed == pytest.approx(hp.Max_S)
    assert hp.Q_min == pytest.approx(-hp.Max_S)
    assert hp.Q_max == pytest.approx(hp.Max_S)
    assert model.hp_e_min[h].value == pytest.approx(hp.E_min)
    assert model.hp_e_max[h].value == pytest.approx(hp.E_max)
    assert pyo.value(model.heat_pump_p_shed_nonneg_constraint[h].lower) == pytest.approx(0.0)
    assert pyo.value(model.heat_pump_p_shed_cap_constraint[h].upper) == pytest.approx(p_shed_cap)
    assert model.Q_shed[h].lb == pytest.approx(-q_shed_lim)
    assert model.Q_shed[h].ub == pytest.approx(q_shed_lim)
    assert model.Q_heat_pump[h].lb == pytest.approx(q_injected_lb)
    assert model.Q_heat_pump[h].ub == pytest.approx(q_injected_ub)
    assert hasattr(model, "heat_pump_p_link_constraint")
    assert hasattr(model, "heat_pump_q_link_constraint")
    assert pyo.value(model.heat_pump_p_shed_energy_lower_constraint[h].lower) == pytest.approx(energy_p_shed_lb)
    assert pyo.value(model.heat_pump_p_shed_energy_upper_constraint[h].upper) == pytest.approx(energy_p_shed_ub)


def test_ext_heat_pump_reporting():
    require_pyomo()
    grid, _ = _grid_with_heat_pump()
    pyf.optimal_pf(grid, ObjRule={"Energy_cost": 1}, build_only=True)

    res = pyf.Results(grid)
    df = res.ext_heat_pump(print_table=False)

    assert "Ext_heat_pump" in res.tables
    assert len(df) == 2
    assert "P served (MW)" in df.columns
    assert "Energy state (kWh)" in df.columns


def test_heat_pump_ts_and_window_results_build():
    require_pyomo()
    grid, hp = _grid_with_heat_pump()
    _attach_ts(grid, hp)

    pyf.ts_acdc_opf(
        grid,
        start=1,
        end=4,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert "heat_pump_p" in grid.time_series_results
    assert "heat_pump_energy_state" in grid.time_series_results
    assert len(grid.time_series_results["heat_pump_p"]) == 4
    assert hp.E_min == pytest.approx(-2.0)
    assert hp.E_max == pytest.approx(8.0)

    pyf.window_nl_opf(
        grid,
        start=0,
        end=3,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert "heat_pump_P" in grid.window_opf_results
    assert "heat_pump_energy_state" in grid.window_opf_results

    res = pyf.Results(grid)
    p_df, e_df = res.heat_pump_window(print_table=False)
    assert len(p_df) == 4
    assert len(e_df) == 5
    assert hp.name in p_df.columns


def test_heat_pump_linear_build_only_p_only():
    require_pyomo()
    grid, hp = _grid_with_heat_pump()
    pyf.analyse_grid(grid)

    model, _, _, _ = pyf.optimal_l_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    h = hp.heatPumpNumber
    energy_p_shed_lb = hp.E_min / hp.dt_hours - hp.E_state / hp.dt_hours
    energy_p_shed_ub = hp.E_max / hp.dt_hours - hp.E_state / hp.dt_hours

    assert hasattr(model, "P_shed")
    assert hasattr(model, "P_heat_pump")
    assert hasattr(model, "E_heat_pump")
    assert hasattr(model, "Gen_Pheatpump_constraint")
    assert not hasattr(model, "Gen_Qheatpump_constraint")
    assert not hasattr(model, "Q_shed")
    assert not hasattr(model, "Q_heat_pump")
    assert not hasattr(model, "hp_q_ref")
    assert hasattr(model, "heat_pump_p_link_constraint")
    assert model.hp_p_ref[h].value == pytest.approx(hp.P_ref)
    assert pyo.value(model.heat_pump_p_shed_energy_lower_constraint[h].lower) == pytest.approx(energy_p_shed_lb)
    assert pyo.value(model.heat_pump_p_shed_energy_upper_constraint[h].upper) == pytest.approx(energy_p_shed_ub)


def test_heat_pump_linear_ts_and_window_build():
    require_pyomo()
    grid, hp = _grid_with_heat_pump()
    _attach_ts(grid, hp)

    pyf.ts_acdc_l_opf(
        grid,
        start=1,
        end=4,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert "heat_pump_p" in grid.time_series_results
    assert "heat_pump_energy_state" in grid.time_series_results
    assert len(grid.time_series_results["heat_pump_p"]) == 4

    pyf.window_l_opf(
        grid,
        start=0,
        end=3,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert "heat_pump_P" in grid.window_opf_results
    assert "heat_pump_Q" in grid.window_opf_results
    assert "heat_pump_energy_state" in grid.window_opf_results
    assert (grid.window_opf_results["heat_pump_Q"][hp.name] == 0).all()
