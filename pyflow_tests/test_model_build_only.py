# -*- coding: utf-8 -*-
"""
Build-only tests for heavy optimization modules.
"""

from types import SimpleNamespace

import pytest
import pyflow_acdc as pyf

from pyflow_acdc.ACDC_MultiPeriod_TEP import multi_period_transmission_expansion
from pyflow_acdc.ACDC_Static_TEP import _prepare_TEP_model, transmission_expansion
from pyflow_acdc.Array_OPT import _create_master_problem_pyomo


def _tiny_array_grid():
    """Create a minimal synthetic grid accepted by Array_OPT MIP builder."""
    sink = SimpleNamespace(
        nodeNumber=0,
        type="Slack",
        connected_gen=True,
        connected_RenSource=False,
        ct_limit=3,
        pu_power_limit=None,
    )
    src_1 = SimpleNamespace(
        nodeNumber=1,
        type="PQ",
        connected_gen=False,
        connected_RenSource=True,
        ct_limit=None,
        pu_power_limit=None,
    )
    src_2 = SimpleNamespace(
        nodeNumber=2,
        type="PQ",
        connected_gen=False,
        connected_RenSource=True,
        ct_limit=None,
        pu_power_limit=None,
    )

    line_1 = SimpleNamespace(fromNode=src_1, toNode=sink, installation_cost=1.0)
    line_2 = SimpleNamespace(fromNode=src_2, toNode=sink, installation_cost=1.0)

    return SimpleNamespace(
        nodes_AC=[sink, src_1, src_2],
        slack_nodes=[sink],
        lines_AC_ct=[line_1, line_2],
        crossing_groups=[],
        Cable_options=None,
    )


def test_static_tep_model_builds_without_solving():
    pytest.importorskip("pyomo")

    grid, _ = pyf.cases['case39'](TEP=True)
    model, obj_tep, obj_opf, _, _ = _prepare_TEP_model(
        grid,
        NPV=True,
        n_years=5,
        Hy=8760,
        discount_rate=0.02,
        ObjRule={"Energy_cost": 1},
        PV_set=False,
    )

    assert model.name == "TEP MTDC AC/DC hybrid OPF"
    assert obj_tep is not None
    assert obj_opf is not None


def test_array_opt_master_problem_builds_without_solving():
    pytest.importorskip("pyomo")

    grid = _tiny_array_grid()
    model = _create_master_problem_pyomo(
        grid,
        crossings=False,
        max_flow=2,
        enable_cable_types=False,
    )

    assert len(model.lines) == 2
    assert len(model.nodes) == 3
    assert hasattr(model, "objective")
    assert hasattr(model, "spanning_tree")


def test_mp_tep_build_phase_runs_without_real_solver(monkeypatch):
    pytest.importorskip("pyomo")

    def _fake_solve(*args, **kwargs):
        return None, {
            "solution_found": False,
            "termination_condition": "unknown",
            "solver_message": "mocked in test",
            "time": 0.0,
        }

    monkeypatch.setattr("pyflow_acdc.ACDC_MultiPeriod_TEP.pyomo_model_solve", _fake_solve)

    grid, _ = pyf.cases['case39'](TEP=True)
    model, model_results, timing_info, solver_stats = multi_period_transmission_expansion(
        grid,
        inv_periods=[1.0, 1.05],
        n_years=2,
        Hy=8760,
        discount_rate=0.02,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
        tee=False,
    )

    assert hasattr(model, "inv_periods")
    assert len(model.inv_periods) >= 1
    assert model_results is None
    assert timing_info["create"] >= 0
    assert solver_stats["solution_found"] is False


def test_static_tep_transmission_expansion_obj_scaling_branch(monkeypatch):
    pytest.importorskip("pyomo")

    def _fake_solve(*args, **kwargs):
        return None, {
            "solution_found": False,
            "termination_condition": "unknown",
            "solver_message": "mocked in test",
            "time": 0.0,
        }

    monkeypatch.setattr("pyflow_acdc.ACDC_Static_TEP.pyomo_model_solve", _fake_solve)

    grid, _ = pyf.cases['case39'](TEP=True)
    model, model_results, timing_info, solver_stats = transmission_expansion(
        grid,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
        export=False,
        obj_scaling=10.0,
    )

    assert hasattr(model, "obj")
    assert model.obj_scaling == 10.0
    assert model_results is None
    assert timing_info["create"] >= 0
    assert solver_stats["solution_found"] is False


def test_static_tep_transmission_expansion_alpha_branch(monkeypatch):
    pytest.importorskip("pyomo")

    def _fake_solve(*args, **kwargs):
        return None, {
            "solution_found": False,
            "termination_condition": "unknown",
            "solver_message": "mocked in test",
            "time": 0.0,
        }

    monkeypatch.setattr("pyflow_acdc.ACDC_Static_TEP.pyomo_model_solve", _fake_solve)

    grid, _ = pyf.cases['case39'](TEP=True)
    model, model_results, timing_info, solver_stats = transmission_expansion(
        grid,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
        export=False,
        alpha=0.5,
    )

    assert hasattr(model, "obj")
    assert model_results is None
    assert timing_info["create"] >= 0
    assert solver_stats["solution_found"] is False


def run_test():
    """Run this module with pytest and print a docs-style status line."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("✓ Model build-only tests passed")
    else:
        print("✗ Model build-only tests failed")


if __name__ == "__main__":
    run_test()
