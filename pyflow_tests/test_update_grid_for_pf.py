"""Tests for update_grid_for_pf converter / BESS / H₂ setpoint wiring."""

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_acdc.Classes import TimeSeries
from pyflow_acdc.constants import AcDcSide, ConverterDCType, NodeType, TSType


def _pu_ts(values, column_name):
    return pd.DataFrame({column_name: values})


def test_update_grid_for_pf_sets_known_p_dc_and_rejects_unknown():
    grid, _ = pyf.cases["CigreB4_ACDC"]()
    conv = next(
        c for c in grid.Converters_ACDC
        if c.type in (ConverterDCType.P, ConverterDCType.DROOP)
    )
    series = _pu_ts([0.1, 0.2, 0.3], "p_dc")
    pyf.add_TimeSeries(
        grid,
        series,
        associated=conv.name,
        TS_type=TSType.CONV_P_DC,
    )
    ts = grid.Time_series[-1]

    pyf.update_grid_for_pf(grid, ts, 1)
    assert conv.P_DC == pytest.approx(0.2)
    assert conv.Node_DC.Pconv == pytest.approx(0.2)

    if conv.type != ConverterDCType.PAC:
        bad = TimeSeries(
            TSType.CONV_P_AC.value,
            conv.name,
            series["p_dc"].to_numpy(),
            name="bad_pac",
        )
        with pytest.raises(ValueError, match="P_AC"):
            pyf.update_grid_for_pf(grid, bad, 0)


def test_update_grid_for_pf_sets_q_ac_for_pq():
    grid, _ = pyf.cases["CigreB4_ACDC"]()
    conv = next(c for c in grid.Converters_ACDC if c.AC_type == NodeType.PQ)
    series = _pu_ts([-0.05, -0.1], "q_ac")
    pyf.add_TimeSeries(
        grid,
        series,
        associated=conv.name,
        TS_type="conv_Q_AC",
    )
    ts = grid.Time_series[-1]
    pyf.update_grid_for_pf(grid, ts, 1)
    assert conv.Q_AC == pytest.approx(-0.1)


def _grid_with_ac_dc_storage_and_h2():
    grid, _ = pyf.cases["case39_acdc"]()
    pyf.add_storage(
        grid,
        "30",
        E_max_MWh=100.0,
        P_charge_MW=33.0,
        P_discharge_MW=33.0,
        eta_charge=0.85,
        eta_discharge=0.90,
        storage_name="bess_ac",
    )
    dc_node = next(n for n in grid.nodes_DC if n.name == "1")
    pyf.add_storage(
        grid,
        dc_node,
        E_max_MWh=50.0,
        P_charge_MW=10.0,
        P_discharge_MW=10.0,
        eta_charge=0.9,
        eta_discharge=0.95,
        storage_name="bess_dc",
    )
    pyf.add_electrolyser(
        grid,
        "30",
        P_max_MW=150.0,
        P_min_MW=0.0,
        b_h=16.0,
        c_h=8.0,
        H2_mass_max_kg=1000.0,
        electrolyser_name="el_ac",
    )
    pyf.add_electrolyser(
        grid,
        dc_node,
        P_max_MW=50.0,
        P_min_MW=0.0,
        b_h=16.0,
        c_h=8.0,
        H2_mass_max_kg=500.0,
        electrolyser_name="el_dc",
    )
    return grid


def test_update_grid_for_pf_storage_net_p_and_q():
    grid = _grid_with_ac_dc_storage_and_h2()
    ac_st = next(s for s in grid.storage_elements if s.name == "bess_ac")
    dc_st = next(s for s in grid.storage_elements if s.name == "bess_dc")

    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.05, -0.02], "p"),
        associated="bess_ac",
        TS_type=TSType.STORAGE_P,
    )
    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.01, -0.03], "q"),
        associated="bess_ac",
        TS_type=TSType.STORAGE_Q,
    )
    ts_p = next(ts for ts in grid.Time_series if ts.type == TSType.STORAGE_P)
    ts_q = next(ts for ts in grid.Time_series if ts.type == TSType.STORAGE_Q)

    pyf.update_grid_for_pf(grid, ts_p, 0)
    assert ac_st.P_discharge == pytest.approx(0.05)
    assert ac_st.P_charge == pytest.approx(0.0)
    assert ac_st.net_P_pu == pytest.approx(0.05)

    pyf.update_grid_for_pf(grid, ts_p, 1)
    assert ac_st.P_charge == pytest.approx(0.02)
    assert ac_st.P_discharge == pytest.approx(0.0)
    assert ac_st.net_P_pu == pytest.approx(-0.02)

    pyf.update_grid_for_pf(grid, ts_q, 1)
    assert ac_st.Q == pytest.approx(-0.03)

    bad_q = TimeSeries(
        TSType.STORAGE_Q.value,
        "bess_dc",
        [0.01, 0.02],
        name="bad_dc_q",
    )
    with pytest.raises(ValueError, match="Q"):
        pyf.update_grid_for_pf(grid, bad_q, 0)

    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.04], "p_dc"),
        associated="bess_dc",
        TS_type=TSType.STORAGE_P,
    )
    ts_dc = next(
        ts for ts in grid.Time_series
        if ts.type == TSType.STORAGE_P and ts.element_name == "bess_dc"
    )
    pyf.update_grid_for_pf(grid, ts_dc, 0)
    assert dc_st.net_P_pu == pytest.approx(0.04)
    assert dc_st.connected == AcDcSide.DC


def test_update_grid_for_pf_h2_p_and_q():
    grid = _grid_with_ac_dc_storage_and_h2()
    el_ac = next(e for e in grid.electrolysers if e.name == "el_ac")
    el_dc = next(e for e in grid.electrolysers if e.name == "el_dc")

    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.12, 0.08], "p"),
        associated="el_ac",
        TS_type=TSType.H2_P,
    )
    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.0, -0.01], "q"),
        associated="el_ac",
        TS_type=TSType.H2_Q,
    )
    ts_p = next(ts for ts in grid.Time_series if ts.type == TSType.H2_P)
    ts_q = next(ts for ts in grid.Time_series if ts.type == TSType.H2_Q)

    pyf.update_grid_for_pf(grid, ts_p, 0)
    assert el_ac.P_electrolyser == pytest.approx(0.12)
    pyf.update_grid_for_pf(grid, ts_q, 1)
    assert el_ac.Q_electrolyser == pytest.approx(-0.01)

    bad_q = TimeSeries(
        TSType.H2_Q.value,
        "el_dc",
        [0.01],
        name="bad_el_dc_q",
    )
    with pytest.raises(ValueError, match="Q"):
        pyf.update_grid_for_pf(grid, bad_q, 0)

    pyf.add_TimeSeries(
        grid,
        _pu_ts([0.05], "p_dc"),
        associated="el_dc",
        TS_type=TSType.H2_P,
    )
    ts_dc = next(
        ts for ts in grid.Time_series
        if ts.type == TSType.H2_P and ts.element_name == "el_dc"
    )
    pyf.update_grid_for_pf(grid, ts_dc, 0)
    assert el_dc.P_electrolyser == pytest.approx(0.05)
    assert el_dc.connected == AcDcSide.DC


def test_h2_price_remains_normal_ts_not_pf():
    """h2_price is update_grid_data territory, not update_grid_for_pf."""
    grid = _grid_with_ac_dc_storage_and_h2()
    el = next(e for e in grid.electrolysers if e.name == "el_ac")
    pyf.add_TimeSeries(
        grid,
        _pu_ts([10.0, 20.0], "price"),
        associated="el_ac",
        TS_type=TSType.H2_PRICE,
    )
    ts = grid.Time_series[-1]
    assert ts.type == TSType.H2_PRICE

    before = el.h2_price
    pyf.update_grid_for_pf(grid, ts, 1)
    assert el.h2_price == before

    pyf.update_grid_data(grid, ts, 1)
    assert el.h2_price == pytest.approx(20.0)
