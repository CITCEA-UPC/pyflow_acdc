# -*- coding: utf-8 -*-
"""build_only tests for linear static rs_GPR and linear multi-period TEP."""

import importlib.util
import sys
from pathlib import Path

import pyomo.environ as pyo
import pyflow_acdc as pyf

from pyflow_tests._test_solver_deps import require_pyomo


def _load_case24_mp_module():
    case_path = Path(pyf.__file__).resolve().parent / "example_grids" / "TEP" / "case24_MP.py"
    module_name = "TEP__case24_MP"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, case_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case24_mp_grid_with_csvs():
    mod = _load_case24_mp_module()
    grid, res = mod.case24_MP()
    inv_csv = mod._resolve_example_path("case24_MP_TEP_inv_series_10.csv")
    mix_csv = mod._resolve_example_path("case24_MP_TEP_gen_mix_limits.csv")
    pyf.add_inv_series(grid, inv_csv)
    pyf.add_gen_mix_limits(grid, mix_csv)
    return grid, res, mod


def test_linear_static_tep_rs_gpr_build_only():
    require_pyomo()

    grid, _, mod = _case24_mp_grid_with_csvs()
    assert any(rs.np_rsgen_opf for rs in grid.RenSources)

    model, model_results, timing_info, solver_stats = pyf.linear_transmission_expansion(
        grid,
        n_years=mod.DEFAULT_N_YEARS,
        ObjRule=mod.DEFAULT_OBJ_RULE,
        solver="gurobi",
        build_only=True,
    )

    assert isinstance(model.np_rsgen, pyo.Var)
    assert hasattr(model, "np_rsgen_install")
    assert hasattr(model, "np_rsgen_base")
    assert model_results is None
    assert solver_stats["termination_condition"] == "build_only"
    assert timing_info["create"] >= 0


def test_linear_multi_period_transmission_expansion_build_only():
    require_pyomo()

    grid, _, mod = _case24_mp_grid_with_csvs()
    model, model_results, timing_info, solver_stats = pyf.linear_multi_period_transmission_expansion(
        grid,
        n_years=mod.DEFAULT_N_YEARS,
        Hy=8760,
        discount_rate=0.02,
        ObjRule=mod.DEFAULT_OBJ_RULE,
        solver="gurobi",
        tee=False,
        obj_scaling=1e9,
        build_only=True,
    )

    assert hasattr(model, "inv_periods")
    assert len(model.inv_periods) >= 1
    assert hasattr(model, "np_rsgen")
    assert hasattr(model, "ACLinesMP")
    assert isinstance(model.inv_model[0].np_rsgen, pyo.Var)
    assert model_results is None
    assert timing_info["create"] >= 0
    assert timing_info["solve"] == 0.0
    assert timing_info["export"] >= 0
    assert solver_stats["termination_condition"] == "build_only"
    assert solver_stats["solution_found"] is False
    assert hasattr(grid, "MP_TEP_obj_res")
    assert grid.DCmode is False
