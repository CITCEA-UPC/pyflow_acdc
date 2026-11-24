"""multi_scenario_opf: weighted OPF over scenario frames with fixed installed amounts."""

import numpy as np
import pyomo.environ as pyo
import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_ipopt


def _grid(power_factor=None, statcom_mvar=50):
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 220, name="sub")
    pyf.add_AC_node(grid, 220, name="pcc")
    rs = pyf.add_RenSource(grid, "sub", base_MW=300, Qrel=0, min_gamma=1)
    pyf.add_line_AC(grid, "sub", "pcc", r=0.002, x=0.02, b=0.2, MVA_rating=400)
    pyf.add_grid_thevenin(grid, "pcc", SCR=10, XR=10, P_rated_MW=300, power_factor=power_factor)
    statcom = pyf.add_statcom(grid, "pcc", Q_max_MVAr=statcom_mvar)
    statcom.np_gen, statcom.np_gen_opf = 1, False  # installed, not sized
    pyf.add_TimeSeries(grid, np.array([1.0, 0.2]), associated=rs.name, TS_type="WPP", name="wind")
    return grid, statcom


def test_frame_weights():
    grid, _ = _grid()
    model, *_ = pyf.multi_scenario_opf(grid, ObjRule={"AC_losses": 1}, build_only=True, scenario_weights=[0.3, 0.7])
    assert [pyo.value(model.weights[t]) for t in model.scenario_frames] == pytest.approx([0.3, 0.7])


def test_scenario_weights_length_must_match_frames():
    grid, _ = _grid()
    with pytest.raises(ValueError):
        pyf.multi_scenario_opf(grid, ObjRule={"AC_losses": 1}, build_only=True, scenario_weights=[1.0])


def test_fixed_statcom_q_within_rating():
    require_ipopt()
    grid, statcom = _grid()
    model, _, _, stats = pyf.multi_scenario_opf(grid, ObjRule={"AC_losses": 1}, scenario_weights=[0.3, 0.7])
    assert stats["solution_found"]
    for t in model.scenario_frames:
        q = pyo.value(model.scenario_model[t].QGi_gen[statcom.genNumber]) * grid.S_base
        assert -50 - 1e-6 <= q <= 50 + 1e-6


def test_unreachable_power_factor_has_no_solution():
    require_ipopt()
    grid, _ = _grid(power_factor=0.999999, statcom_mvar=1)
    _, _, _, stats = pyf.multi_scenario_opf(grid, ObjRule={"AC_losses": 1}, scenario_weights=[0.3, 0.7])
    assert not stats["solution_found"]
