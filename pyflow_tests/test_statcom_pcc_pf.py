# -*- coding: utf-8 -*-
"""STATCOM sizing with a PCC power-factor limit in multi_scenario_TEP."""

import numpy as np
import pyomo.environ as pyo
import pytest
import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_ipopt


def _grid(mode):
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 220, name="sub")
    pyf.add_AC_node(grid, 220, name="pcc")
    rs = pyf.add_RenSource(grid, "sub", base_MW=300, Qrel=0, min_gamma=1)
    # Rough p.u. cable on 100 MVA with a lot of charging
    pyf.add_line_AC(grid, "sub", "pcc", r=0.002, x=0.02, b=0.8, MVA_rating=400)
    _, zg, _ = pyf.add_grid_thevenin(grid, "pcc", SCR=10, XR=10, P_rated_MW=300, power_factor=0.95, power_factor_mode=mode)
    statcom = pyf.add_statcom(grid, "pcc", Q_max_MVAr=200, installation_cost=20)
    pyf.add_TimeSeries(grid, np.array([1.0, 0.5, 0.0]), associated=rs.name, TS_type="WPP", name="wind")
    pyf.add_TimeSeries(grid, np.array([0.3, 0.5, 0.2]), associated="TEP_w", TS_type="TEP_w", name="TEP_w")
    return grid, zg, statcom


@pytest.mark.parametrize("mode", ["band", "per_bin"])
def test_statcom_meets_pcc_power_factor(mode):
    require_ipopt()
    grid, zg, statcom = _grid(mode)
    model, *_ = pyf.multi_scenario_TEP(grid, ObjRule={"AC_losses": 1}, solver="ipopt")

    np_gen = pyo.value(model.np_gen[statcom.genNumber])
    assert 0 < np_gen <= 1
    tan_phi = np.tan(np.arccos(0.95))
    for t in model.scenario_frames:
        block = model.scenario_model[t]
        p = pyo.value(block.PAC_from[zg.lineNumber])
        q = pyo.value(block.QAC_from[zg.lineNumber])
        # P_rated 3 p.u., P_floor 10 % of it
        cap = tan_phi * (3.0 if mode == "band" else p + 0.3)
        assert abs(q) <= cap + 1e-6
        assert abs(pyo.value(block.QGi_gen[statcom.genNumber])) <= 2.0 * np_gen + 1e-6
