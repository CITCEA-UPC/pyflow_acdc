"""Time-series power flow and build-only TS-OPF smoke tests."""

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo

TS_FACTORS = [1.0, 0.9, 0.8, 0.9, 1.0]
N_STEPS = len(TS_FACTORS)


def _factor_ts(values, column_name):
    return pd.DataFrame({column_name: values})


def _attach_load_ts(grid, node_name, column_name=None):
    column_name = column_name or f"load_{node_name}"
    pyf.add_TimeSeries(
        grid,
        _factor_ts(TS_FACTORS, column_name),
        associated=node_name,
        TS_type="Load",
    )


def _assert_ts_pf_results(grid, *, expect_ac=False, expect_dc=False, expect_conv=False):
    assert grid.Time_series_ran is True
    pf = grid.time_series_results["PF_results"]
    assert len(pf) == N_STEPS
    assert pf.index.tolist() == list(range(1, N_STEPS + 1))

    if expect_ac:
        ac_loading = grid.time_series_results["ac_loading"]
        assert len(ac_loading) == N_STEPS
        assert not ac_loading.isna().any().any()

    if expect_dc:
        dc_loading = grid.time_series_results["dc_loading"]
        assert len(dc_loading) == N_STEPS
        assert not dc_loading.isna().any().any()

    if expect_conv:
        conv_loading = grid.time_series_results["converter_loading"]
        assert len(conv_loading) == N_STEPS
        assert not conv_loading.isna().any().any()


def _assert_ts_opf_build_only_results(grid, *, start=1, n_steps=N_STEPS, expect_tep=False, expect_rec=False):
    assert grid.Time_series_ran is True
    assert grid.OPF_run is True
    expected_index = list(range(start, start + n_steps))

    ac_loading = grid.time_series_results["ac_loading"]
    assert len(ac_loading) == n_steps
    assert ac_loading.index.tolist() == expected_index
    assert len(ac_loading.columns) > 0
    assert not ac_loading.isna().any().any()

    grid_loading = grid.time_series_results["grid_loading"]
    assert len(grid_loading) == n_steps
    assert "Total" in grid_loading.columns

    if expect_tep:
        assert grid.TEP_AC
        assert len(grid.lines_AC_exp) > 0
    if expect_rec:
        assert grid.REC_AC
        assert len(grid.lines_AC_rec) > 0


def _run_ts_opf_build_only(grid, *, start=1, end=None):
    if end is None:
        end = start + N_STEPS - 1
    timing = pyf.ts_acdc_opf(
        grid,
        start=start,
        end=end,
        ObjRule={"Energy_cost": 1},
        export_to_grid=False,
        build_only=True,
    )
    assert timing["Create"] >= 0
    assert timing["Solve model Avg"] == 0.0
    return timing


def test_time_series_pf_stagg5_acdc_load():
    """Hybrid MATACDC case 5: load-factor time series via ``ts_acdc_pf`` dispatch."""
    grid, _res = pyf.cases["Stagg5MATACDC"]()
    load_node = "4"
    _attach_load_ts(grid, load_node)

    pyf.time_series_pf(grid)

    node = grid.nodes_AC_dict[load_node]
    assert node.PLi_factor == pytest.approx(TS_FACTORS[-1])
    _assert_ts_pf_results(grid, expect_ac=True, expect_dc=True, expect_conv=True)


def test_time_series_pf_case24_ac_load():
    """IEEE RTS-24 (``case24_OPF``): pure AC load-factor time series."""
    grid, _res = pyf.cases["case24_OPF"]()
    load_node = "4"
    _attach_load_ts(grid, load_node)

    pyf.time_series_pf(grid)

    node = grid.nodes_AC_dict[load_node]
    assert node.PLi_factor == pytest.approx(TS_FACTORS[-1])
    _assert_ts_pf_results(grid, expect_ac=True)


def test_time_series_pf_dc_opf_simple_load():
    """Small DC grid (``DC_OPF_simple``): DC load-factor time series."""
    grid, _res = pyf.cases["DC_OPF_simple"]()
    load_node = "Node_2"
    _attach_load_ts(grid, load_node, column_name="load_n2")

    pyf.time_series_pf(grid)

    node = grid.nodes_DC_dict[load_node]
    assert node.PLi_factor == pytest.approx(TS_FACTORS[-1])
    _assert_ts_pf_results(grid, expect_dc=True)


def test_ts_opf_build_only_case24_tep():
    """RTS-24 TEP grid: 5-step TS-OPF build-only exercises expansion line loading."""
    require_pyomo()

    grid, _res = pyf.cases["case24_TEP"]()
    _attach_load_ts(grid, "4")

    _run_ts_opf_build_only(grid)
    _assert_ts_opf_build_only_results(grid, expect_tep=True)


def test_ts_opf_build_only_case24_rec():
    """RTS-24 reconductoring grid: 5-step TS-OPF build-only exercises REC line loading."""
    require_pyomo()

    grid, _res = pyf.cases["case24_REC"]()
    _attach_load_ts(grid, "4")

    _run_ts_opf_build_only(grid)
    _assert_ts_opf_build_only_results(grid, expect_rec=True)


def test_ts_opf_build_only_case118_benchmark():
    """118-bus TEP+REC benchmark: 5-step TS-OPF build-only with bundled wind/load series."""
    require_pyomo()

    grid, _res = pyf.cases["case118_TEP_benchmark"](
        exp_220="Expandable",
        exp_380="Reconducting",
    )

    _run_ts_opf_build_only(grid, start=2000, end=2004)
    _assert_ts_opf_build_only_results(
        grid, start=2000, n_steps=5, expect_tep=True, expect_rec=True
    )


def run_test():
    """Script entrypoint for ``pyflow-acdc-test``."""
    test_time_series_pf_stagg5_acdc_load()
    test_time_series_pf_case24_ac_load()
    test_time_series_pf_dc_opf_simple_load()
    if not pyomo_missing_for_run_test():
        test_ts_opf_build_only_case24_tep()
        test_ts_opf_build_only_case24_rec()
        test_ts_opf_build_only_case118_benchmark()
    print("✓ Time-series PF tests passed")


if __name__ == "__main__":
    run_test()
