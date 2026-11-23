"""Fast multi-period TEP tests on the case24_MP example grid."""

import importlib.util
import sys
from pathlib import Path

import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_pyomo, tep_solver


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


def test_case24_mp_case_is_registered():
    assert "case24_MP" in pyf.cases
    grid, res = pyf.cases["case24_MP"]()
    assert len(grid.nodes_AC) == 32
    assert res is not None


def test_case24_mp_investment_csvs_resolve():
    mod = _load_case24_mp_module()
    inv_path = mod._resolve_example_path("case24_MP_TEP_inv_series_10.csv")
    mix_path = mod._resolve_example_path("case24_MP_TEP_gen_mix_limits.csv")
    assert Path(inv_path).is_file()
    assert Path(mix_path).is_file()


def test_case24_mp_grid_ready_for_multperiod():
    grid, _, mod = _case24_mp_grid_with_csvs()
    assert mod.DEFAULT_OBJ_RULE == {"Energy_cost": 1}
    assert len(grid.lines_AC_exp) > 0
    assert any(hasattr(el, "investment_decisions") for el in grid.Generators)


def test_case24_multi_period_transmission_expansion_build_only():
    require_pyomo()

    grid, _, mod = _case24_mp_grid_with_csvs()
    model, model_results, timing_info, solver_stats = pyf.multi_period_transmission_expansion(
        grid,
        n_years=mod.DEFAULT_N_YEARS,
        Hy=8760,
        discount_rate=0.02,
        ObjRule=mod.DEFAULT_OBJ_RULE,
        solver=tep_solver(),
        tee=False,
        obj_scaling=1e9,
        build_only=True,
    )

    assert hasattr(model, "inv_periods")
    assert len(model.inv_periods) >= 1
    assert model_results is None
    assert timing_info["create"] >= 0
    assert timing_info["solve"] == 0.0
    assert timing_info["export"] >= 0
    assert solver_stats["termination_condition"] == "build_only"
    assert solver_stats["solution_found"] is False
    assert hasattr(grid, "MP_TEP_obj_res")


def test_case24_sequential_step_orchestration_fake_solve(monkeypatch):
    require_pyomo()

    solve_calls = []

    def _fake_solve(*args, **kwargs):
        solve_calls.append(1)
        return None, {
            "solution_found": False,
            "termination_condition": "unknown",
            "solver_message": "mocked in test",
            "time": 0.0,
        }

    monkeypatch.setattr("pyflow_acdc.NL_models.ACDC_Static_TEP.pyomo_model_solve", _fake_solve)

    grid, _, mod = _case24_mp_grid_with_csvs()
    inv_csv = mod._resolve_example_path("case24_MP_TEP_inv_series_10.csv")
    mix_csv = mod._resolve_example_path("case24_MP_TEP_gen_mix_limits.csv")

    pyf.sequential_STEP(
        grid=grid,
        inv_data=inv_csv,
        mix_data=mix_csv,
        n_years=mod.DEFAULT_N_YEARS,
        Hy=8760,
        discount_rate=0.02,
        ObjRule=mod.DEFAULT_OBJ_RULE,
        solver=tep_solver(),
        tee=False,
        obj_scaling=1e9,
        save_svgs=False,
        export_steps=False,
    )

    assert len(solve_calls) == 1
    assert grid.Seq_STEP_run_aborted is True
    assert "no feasible solution" in grid.Seq_STEP_run_abort_reason


def test_case24_sequential_step_build_only():
    """build_only: build period 1, extract init values, do not build period 2+."""
    require_pyomo()

    grid, res, mod = _case24_mp_grid_with_csvs()
    inv_csv = mod._resolve_example_path("case24_MP_TEP_inv_series_10.csv")
    mix_csv = mod._resolve_example_path("case24_MP_TEP_gen_mix_limits.csv")

    run_results = pyf.sequential_STEP(
        grid=grid,
        inv_data=inv_csv,
        mix_data=mix_csv,
        n_years=mod.DEFAULT_N_YEARS,
        Hy=8760,
        discount_rate=0.02,
        ObjRule=mod.DEFAULT_OBJ_RULE,
        solver=tep_solver(),
        tee=False,
        obj_scaling=1e9,
        save_svgs=False,
        export_steps=False,
        build_only=True,
    )

    assert grid.Seq_STEP_run_aborted is False
    assert grid.Seq_STEP_run_abort_reason is None
    assert 0 in run_results
    assert 1 not in run_results

    stats = run_results[0]["solver_stats"]
    assert stats["termination_condition"] == "build_only"
    assert stats["solution_found"] is False
    assert run_results[0]["timing_info"]["solve"] == 0.0
    assert run_results[0]["model"] is not None

    assert grid.Seq_STEP_run is True
    assert grid.Seq_STEP_obj_res is not None
    assert len(grid.Seq_STEP_obj_res) == 1

    df = res.pyomo_model_results_sequential(run_results, print_table=False)
    assert df is not None
    assert "Pyomo_Model_Results" in res.tables


def run_test():
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("✓ case24 MP multi-period tests passed")
    else:
        print("✗ case24 MP multi-period tests failed")


if __name__ == "__main__":
    run_test()
