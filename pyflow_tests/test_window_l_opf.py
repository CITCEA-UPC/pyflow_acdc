"""Linear AC window / rolling window OPF (build_only)."""

import pandas as pd

import pyflow_acdc as pyf


def _grid_l_window(n_frames=10):
    grid, _ = pyf.cases["case39"]()
    pyf.add_storage(
        grid,
        "30",
        E_max_MWh=100.0,
        P_charge_MW=33.0,
        P_discharge_MW=33.0,
        eta_charge=0.85,
        eta_discharge=0.90,
        soc_initial=0.5,
        soc_final=0.5,
    )
    pyf.add_electrolyser(
        grid,
        "30",
        P_max_MW=50.0,
        P_min_MW=5.0,
        b_h=16.0,
        c_h=0.0,
        H2_mass_max_kg=1e6,
        H2_mass_initial_kg=0.0,
        H2_mass_final_kg=100.0,
        h2_price=2.0,
        electrolyser_name="el1",
    )
    factors = [0.9 + 0.02 * (i % 5) for i in range(n_frames)]
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": factors}),
        associated="30",
        TS_type="Load",
    )
    return grid


def test_window_l_opf_build_only():
    grid = _grid_l_window(8)
    model, _, timing, stats = pyf.window_l_opf(
        grid,
        start=0,
        end=7,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert stats["termination_condition"] == "build_only"
    assert timing["create"] >= 0
    assert hasattr(model, "window_soc_constraint")
    assert hasattr(model, "window_h2_constraint")
    assert "storage_soc" in grid.window_opf_results
    assert "hydrogen_mass_H2" in grid.window_opf_results
    # P-only linear: Q column is zeros, not NL Q_storage
    q = grid.window_opf_results["storage_Q"]
    assert (q.drop(columns=["frame"]) == 0).all().all()


def test_window_l_opf_hybrid_build_only():
    """Hybrid AC/DC linear window OPF builds (Phase 3)."""
    grid, _ = pyf.cases["case39_acdc"]()
    pyf.add_storage(
        grid, "30", E_max_MWh=10.0, P_charge_MW=5.0, P_discharge_MW=5.0,
        eta_charge=0.9, eta_discharge=0.9, soc_initial=0.5, soc_final=0.5,
    )
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": [0.95, 1.0, 1.05, 0.98]}),
        associated="30",
        TS_type="Load",
    )
    model, _, timing, stats = pyf.window_l_opf(
        grid,
        start=0,
        end=3,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert grid.DCmode and grid.ACmode
    assert stats["termination_condition"] == "build_only"
    assert timing["create"] >= 0
    assert hasattr(model, "window_soc_constraint")
    assert hasattr(model.frame_model[0], "V_DC")
    assert hasattr(model.frame_model[0], "PDC_from")
    assert "storage_soc" in grid.window_opf_results


def test_rolling_window_l_opf_hybrid_future_sight_build_only():
    """Hybrid rolling linear window with foresight half (Phase 3)."""
    grid, _ = pyf.cases["case39_acdc"]()
    pyf.add_storage(
        grid, "30", E_max_MWh=10.0, P_charge_MW=5.0, P_discharge_MW=5.0,
        eta_charge=0.9, eta_discharge=0.9, soc_initial=0.5, soc_final=0.5,
    )
    factors = [0.9 + 0.02 * (i % 5) for i in range(10)]
    pyf.add_TimeSeries(
        grid, pd.DataFrame({"load": factors}), associated="30", TS_type="Load",
    )
    _, _, _, stats = pyf.rolling_window_l_opf(
        grid,
        start=1,
        end=10,
        window_size=4,
        future_sight=0.5,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert grid.DCmode and grid.ACmode
    assert grid.rolling_window_opf_run is True
    assert grid.rolling_window_info.get("linear") is True
    assert stats[0]["future_sight"] == 0.5
    assert stats[0]["foresight_steps"] == 2


def test_rolling_window_l_opf_every_m_build_only():
    grid = _grid_l_window(10)
    _, _, timing, stats = pyf.rolling_window_l_opf(
        grid,
        start=1,
        end=10,
        window_size=4,
        soc_final_mode="every_m",
        soc_final_every_m=2,
        ObjRule={"Energy_cost": 1, "H2_sale": 1},
        build_only=True,
    )
    assert grid.rolling_window_opf_run is True
    assert grid.rolling_window_info.get("linear") is True
    assert timing["windows"] == 3
    assert stats[0]["force_soc"] is False
    assert stats[1]["force_soc"] is True
    assert stats[2]["force_soc"] is True


def test_rolling_window_l_opf_future_sight_half_build_only():
    grid = _grid_l_window(10)
    _, _, _, stats = pyf.rolling_window_l_opf(
        grid,
        start=1,
        end=10,
        window_size=4,
        future_sight=0.5,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert stats[0]["future_sight"] == 0.5
    assert stats[0]["foresight_steps"] == 2
    assert stats[0]["solve"] == (0, 5)
    assert stats[0]["h2_final_frames"] == [3, 5]
    assert stats[0]["h2_final_scale"] == {3: 1.0, 5: 0.5}
    assert stats[-1]["future_sight"] == 0.0
