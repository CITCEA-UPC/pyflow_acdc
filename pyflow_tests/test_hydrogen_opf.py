"""Snapshot and window NL OPF with electrolyser (Phase 5)."""

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_pyomo


def _grid_with_electrolyser():
    grid, _ = pyf.cases["case39_acdc"]()
    pyf.add_electrolyser(
        grid,
        "30",
        P_max_MW=150.0,
        P_min_MW=22.5,
        b_h=16.0585,
        c_h=8.2195,
        H2_mass_max_kg=43448.0,
        H2_mass_initial_kg=0.0,
    )
    return grid


def _grid_with_storage_and_electrolyser_ts(n_frames=5):
    grid, _ = pyf.cases["case39_acdc"]()
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
        P_max_MW=150.0,
        P_min_MW=22.5,
        b_h=16.0585,
        c_h=8.2195,
        H2_mass_max_kg=43448.0,
        H2_mass_initial_kg=0.0,
        H2_mass_final_kg=1000.0,
    )
    dc_node = next(n for n in grid.nodes_DC if n.name == "1")
    pyf.add_electrolyser(
        grid,
        dc_node,
        P_max_MW=50.0,
        P_min_MW=7.5,
        b_h=16.0585,
        c_h=8.2195,
        H2_mass_max_kg=10000.0,
        H2_mass_initial_kg=0.0,
    )
    pattern = [1.0, 0.88, 0.76, 0.92, 1.05]
    factors = [pattern[i % len(pattern)] for i in range(n_frames)]
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": factors}),
        associated="30",
        TS_type="Load",
    )
    return grid


def test_hydrogen_nl_model_builds():
    require_pyomo()
    grid = _grid_with_electrolyser()
    pyf.analyse_grid(grid)
    assert grid.H2 is True

    model, _, _, _ = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    assert hasattr(model, "electrolyser")
    assert hasattr(model, "P_electrolyser")
    assert hasattr(model, "Q_electrolyser")
    assert hasattr(model, "mass_H2")
    assert hasattr(model, "hydrogen_mass_h2_balance_constraint")
    assert hasattr(model, "Gen_Pelectrolyser_constraint")
    assert hasattr(model, "Gen_Qelectrolyser_constraint")
    assert len(model.electrolyser) == 1


def test_ext_electrolyser_reporting():
    require_pyomo()
    grid = _grid_with_electrolyser()
    pyf.optimal_pf(grid, ObjRule={"Energy_cost": 1}, build_only=True)

    res = pyf.Results(grid)
    df = res.ext_electrolyser(print_table=False)

    assert "Ext_electrolyser" in res.tables
    assert len(df) == 2  # element + Total
    assert "mass_H2 (kg)" in df.columns
    assert "Q (MVAR)" in df.columns


def test_window_nl_opf_h2_builds_multi_frame_model():
    require_pyomo()
    grid = _grid_with_storage_and_electrolyser_ts()
    model, _, _, _ = pyf.window_nl_opf(
        grid,
        start=0,
        end=4,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    assert hasattr(model, "window_h2_constraint")
    assert len(model.window_h2_constraint) >= 2
    block = model.frame_model[0]
    assert hasattr(block, "mass_H2")
    assert hasattr(block, "electrolyser")
    assert len(block.electrolyser) == 2
    assert not hasattr(block, "mass_H2_prev")
    assert "hydrogen_mass_H2" in grid.window_opf_results
    assert "hydrogen_P_e" in grid.window_opf_results


def test_hydrogen_window_reporting():
    require_pyomo()
    grid = _grid_with_storage_and_electrolyser_ts()
    pyf.window_nl_opf(grid, start=0, end=4, ObjRule={"Energy_cost": 1}, build_only=True)

    res = pyf.Results(grid)
    m_df, pe_df = res.hydrogen_window(print_table=False)

    assert "Hydrogen_window_mass_H2" in res.tables
    assert "Hydrogen_window_P_e" in res.tables
    # mass includes leading initial row at frame start-1; P_e is solve frames only
    assert len(m_df) == 6
    assert list(m_df["frame"]) == [-1, 0, 1, 2, 3, 4]
    assert len(pe_df) == 5
    assert list(pe_df["frame"]) == [0, 1, 2, 3, 4]


def test_window_nl_opf_electrolyser_only_requires_time_series():
    require_pyomo()
    grid = _grid_with_electrolyser()
    with pytest.raises(ValueError, match="Time_series"):
        pyf.window_nl_opf(grid, start=0, end=1, build_only=True)


def test_empty_tank_cycle_validation_and_myopic_helper():
    from pyflow_acdc.Time_series import _maybe_empty_h2_after_myopic_step

    grid = _grid_with_electrolyser()
    pyf.analyse_grid(grid)
    el = grid.electrolysers[0]
    assert el.empty_tank_cycle is None
    assert grid.H2 is True

    with pytest.raises(ValueError, match="empty_tank_cycle"):
        pyf.add_electrolyser(
            grid,
            "30",
            P_max_MW=10.0,
            P_min_MW=0.0,
            b_h=1.0,
            c_h=0.0,
            H2_mass_max_kg=100.0,
            empty_tank_cycle=0,
        )

    el.empty_tank_cycle = 2
    el.mass_H2 = 12.0
    el.H2_mass_initial = 12.0

    class _Param:
        def __init__(self):
            self.value = 12.0

        def set_value(self, v):
            self.value = float(v)

    class _FakeModel:
        def __init__(self):
            self.mass_H2_prev = {el.electrolyserNumber: _Param()}

    model = _FakeModel()
    _maybe_empty_h2_after_myopic_step(grid, model, 1)
    assert el.mass_H2 == pytest.approx(12.0)
    _maybe_empty_h2_after_myopic_step(grid, model, 2)
    assert el.mass_H2 == pytest.approx(0.0)
    assert el.H2_mass_initial == pytest.approx(0.0)
    assert model.mass_H2_prev[el.electrolyserNumber].value == pytest.approx(0.0)


def test_rolling_empty_tank_cycle_boundary_selection():
    from pyflow_acdc.NL_models.window_opf import (
        _electrolysers_to_empty_after_rolling_commit,
        _rolling_h2_empty_targets,
    )

    grid = _grid_with_electrolyser()
    el_none = grid.electrolysers[0]
    el_n = pyf.add_electrolyser(
        grid,
        "30",
        P_max_MW=10.0,
        P_min_MW=0.0,
        b_h=1.0,
        c_h=0.0,
        H2_mass_max_kg=100.0,
        electrolyser_name="el_cycle48",
        empty_tank_cycle=48,
    )
    els = [el_none, el_n]
    targets = _rolling_h2_empty_targets(els)

    # Window ends at hour 24: None empties; N=48 does not.
    to_empty = _electrolysers_to_empty_after_rolling_commit(els, 24, targets)
    assert el_none in to_empty
    assert el_n not in to_empty

    # Window ends at hour 48: both empty; next target for N becomes 96.
    to_empty = _electrolysers_to_empty_after_rolling_commit(els, 48, targets)
    assert el_none in to_empty
    assert el_n in to_empty
    assert targets[el_n.electrolyserNumber] == 96


def run_test():
    test_hydrogen_nl_model_builds()
    test_ext_electrolyser_reporting()
    test_window_nl_opf_h2_builds_multi_frame_model()
    test_hydrogen_window_reporting()
    test_window_nl_opf_electrolyser_only_requires_time_series()
    test_empty_tank_cycle_validation_and_myopic_helper()
    test_rolling_empty_tank_cycle_boundary_selection()
    print("OK test_hydrogen_opf")


if __name__ == "__main__":
    run_test()
