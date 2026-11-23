"""Myopic linear TS OPF (Phase 4) — build_only smoke tests."""

import pandas as pd

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_pyomo


def _attach_load_ts(grid, node, n=4):
    factors = [0.95 + 0.02 * (i % 3) for i in range(n)]
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": factors}),
        associated=node,
        TS_type="Load",
    )


def test_ts_acdc_l_opf_ac_build_only():
    require_pyomo()
    grid, _ = pyf.cases["case39"]()
    _attach_load_ts(grid, "30", n=4)
    timing = pyf.ts_acdc_l_opf(
        grid,
        start=1,
        end=4,
        ObjRule={"Energy_cost": 1},
        export_to_grid=False,
        build_only=True,
    )
    assert timing["Create"] >= 0
    assert timing["Solve model Avg"] == 0.0
    assert grid.Time_series_ran is True
    assert "grid_loading" in grid.time_series_results
    assert len(grid.time_series_results["grid_loading"]) == 4


def test_ts_acdc_l_opf_hybrid_build_only():
    require_pyomo()
    grid, _ = pyf.cases["case39_acdc"]()
    _attach_load_ts(grid, "30", n=4)
    timing = pyf.ts_acdc_l_opf(
        grid,
        start=1,
        end=4,
        ObjRule={"Energy_cost": 1},
        export_to_grid=False,
        build_only=True,
    )
    assert grid.DCmode and grid.ACmode
    assert timing["Create"] >= 0
    assert timing["Solve model Avg"] == 0.0
    assert "converter_p_ac" in grid.time_series_results
    assert len(grid.time_series_results["converter_p_ac"]) == 4


def test_ts_acdc_l_opf_storage_carry_build_only():
    """BESS SoC rows are written when ESS is present (initializer carry)."""
    require_pyomo()
    grid, _ = pyf.cases["case39"]()
    pyf.add_storage(
        grid,
        "30",
        E_max_MWh=50.0,
        P_charge_MW=20.0,
        P_discharge_MW=20.0,
        eta_charge=0.9,
        eta_discharge=0.9,
        soc_initial=0.5,
    )
    _attach_load_ts(grid, "30", n=3)
    pyf.ts_acdc_l_opf(
        grid,
        start=1,
        end=3,
        ObjRule={"Energy_cost": 1},
        export_to_grid=False,
        build_only=True,
    )
    assert "storage_soc" in grid.time_series_results
    assert len(grid.time_series_results["storage_soc"]) == 3
