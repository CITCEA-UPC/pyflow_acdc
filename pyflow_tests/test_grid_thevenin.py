"""Tests for ``add_grid_thevenin``."""

import numpy as np
import pytest

import pyflow_acdc as pyf
from pyflow_acdc.constants import NodeType


def test_add_grid_thevenin_two_bus():
    """PCC injecting P behind Zg: pyflow PF matches a direct fixed-point solve."""
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 220, node_type="Slack", name="pcc")
    pyf.add_RenSource(grid, "pcc", base_MW=300, Qrel=0)
    source, line, _ = pyf.add_grid_thevenin(grid, "pcc", SCR=5, XR=10, P_rated_MW=300)

    pcc = grid.nodes_AC[grid.nodes_dict_AC["pcc"]]
    assert pcc.type == NodeType.PQ
    assert source.type == NodeType.SLACK
    assert [n.name for n in grid.slack_nodes] == [source.name]
    assert abs(complex(line.r, line.x)) == pytest.approx(100 / (5 * 300))
    assert line.x / line.r == pytest.approx(10)

    pyf.ac_power_flow(grid)

    # v_pcc = 1 + zg * conj(s / v_pcc), s = 3 p.u. injected at the PCC
    zg = complex(line.r, line.x)
    v = 1 + 0j
    for _ in range(100):
        v = 1 + zg * np.conj(3.0 / v)
    assert pcc.V == pytest.approx(abs(v), abs=1e-8)
    assert pcc.theta == pytest.approx(np.angle(v), abs=1e-8)


def test_add_grid_thevenin_rejects_ext_grid_node():
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 220, node_type="Slack", name="pcc")
    pyf.add_extgrid(grid, "pcc")
    with pytest.raises(ValueError):
        pyf.add_grid_thevenin(grid, "pcc", SCR=5, XR=10, P_rated_MW=300)
