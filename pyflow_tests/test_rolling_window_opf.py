"""Rolling window NL OPF: partitioning, carry-over, SoC modes (build_only)."""

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_acdc.NL_models.window_opf import (
    _rolling_commit_windows,
    _ts_inclusive_0based,
)


def test_ts_inclusive_0based_matches_ts_acdc_opf():
    # start=1, end=24 → frames 0…23 (same as ts_acdc_opf)
    assert _ts_inclusive_0based(1, 24, 100) == (0, 23)
    assert _ts_inclusive_0based(1, None, 10) == (0, 9)
    with pytest.raises(ValueError, match="start must be >= 1"):
        _ts_inclusive_0based(0, 10, 20)


def test_rolling_commit_windows_allows_short_last():
    # N=10 frames (0…9), X=4 → 4+4+2
    assert _rolling_commit_windows(0, 9, 4) == [(0, 3), (4, 7), (8, 9)]


def _grid_rolling(n_frames=10):
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


def test_rolling_window_nl_opf_every_m_build_only():
    grid = _grid_rolling(10)
    _, _, timing, stats = pyf.rolling_window_nl_opf(
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
    assert timing["windows"] == 3
    assert timing["frames"] == 10
    assert "update" in timing
    assert len(stats) == 3
    # force on windows 2 and 3 (k=1,2 → 1-based window numbers 2 and 3); not on first
    assert stats[0]["force_soc"] is False
    assert stats[1]["force_soc"] is True
    assert stats[2]["force_soc"] is True
    soc = grid.window_opf_results["storage_soc"]
    assert set(soc["frame"]) >= {-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_rolling_window_nl_opf_future_sight_build_only():
    grid = _grid_rolling(10)
    _, _, _, stats = pyf.rolling_window_nl_opf(
        grid,
        start=1,
        end=10,
        window_size=4,
        future_sight=1.0,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    assert stats[0]["future_sight"] == 1.0
    assert stats[0]["foresight_steps"] == 4
    assert stats[0]["solve"] == (0, 7)  # commit 0–3 + next 4–7
    assert stats[0]["commit"] == (0, 3)
    assert stats[0]["h2_final_frames"] == [3, 7]
    assert stats[0]["h2_final_scale"] == {3: 1.0, 7: 1.0}
    assert stats[-1]["future_sight"] == 0.0
    assert stats[-1]["foresight_steps"] == 0
    assert stats[-1]["force_soc"] is True
    assert stats[-1]["solve"] == (8, 9)
    assert stats[-1]["h2_final_frames"] is None
    assert stats[-1]["h2_final_scale"] is None


def test_rolling_window_nl_opf_future_sight_half_build_only():
    grid = _grid_rolling(10)
    _, _, _, stats = pyf.rolling_window_nl_opf(
        grid,
        start=1,
        end=10,
        window_size=4,
        future_sight=0.5,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )
    # ceil(0.5 * 4) = 2 foresight steps
    assert stats[0]["future_sight"] == 0.5
    assert stats[0]["foresight_steps"] == 2
    assert stats[0]["solve"] == (0, 5)  # commit 0–3 + foresight 4–5
    assert stats[0]["h2_final_frames"] == [3, 5]
    assert stats[0]["h2_final_scale"] == {3: 1.0, 5: 0.5}
    assert stats[0]["force_soc"] is True


def test_rolling_rejects_old_future_sight_mode():
    grid = _grid_rolling(6)
    with pytest.raises(ValueError, match="soc_final_mode"):
        pyf.rolling_window_nl_opf(
            grid,
            start=1,
            end=6,
            window_size=3,
            soc_final_mode="future_sight",
            build_only=True,
        )


def test_rolling_requires_soc_final():
    grid = _grid_rolling(6)
    grid.storage_elements[0].soc_final = None
    with pytest.raises(ValueError, match="soc_final"):
        pyf.rolling_window_nl_opf(
            grid, start=1, end=6, window_size=3, build_only=True
        )
