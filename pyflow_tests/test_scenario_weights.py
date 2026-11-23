"""multi_scenario_TEP with scenario_weights passed directly (no clustering, no TEP_w series)."""

import numpy as np
import pyomo.environ as pyo
import pytest

import pyflow_acdc as pyf


def _grid():
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 220, name="sub")
    pyf.add_AC_node(grid, 220, name="pcc")
    rs = pyf.add_RenSource(grid, "sub", base_MW=300, Qrel=0, min_gamma=1)
    pyf.add_line_AC(grid, "sub", "pcc", r=0.002, x=0.02, b=0.2, MVA_rating=400)
    pyf.add_grid_thevenin(grid, "pcc", SCR=10, XR=10, P_rated_MW=300)
    pyf.add_statcom(grid, "pcc", Q_max_MVAr=100, installation_cost=10)
    pyf.add_TimeSeries(grid, np.array([1.0, 0.2]), associated=rs.name, TS_type="WPP", name="wind")
    return grid


def test_scenario_weights_set_frame_weights():
    model, *_ = pyf.multi_scenario_TEP(_grid(), ObjRule={"AC_losses": 1}, solver="ipopt", build_only=True, scenario_weights=[0.3, 0.7])
    assert [pyo.value(model.weights[t]) for t in model.scenario_frames] == pytest.approx([0.3, 0.7])


def test_scenario_weights_length_must_match_frames():
    with pytest.raises(ValueError):
        pyf.multi_scenario_TEP(_grid(), ObjRule={"AC_losses": 1}, solver="ipopt", build_only=True, scenario_weights=[1.0])
