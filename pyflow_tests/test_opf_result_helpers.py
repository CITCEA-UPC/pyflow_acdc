"""OPF post-solve result helpers (public API not called from res.all()).

Uses ``build_only`` when Ipopt is unavailable (helpers read ``pyo.value(...)``
on initializer values).
"""

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import (
    pyomo_missing_for_run_test,
    require_pyomo,
)


def _solve_case39_acdc(*, require_solution=True):
    grid, _ = pyf.cases["case39_acdc"]()
    build_only = not pyf.is_pyomo_solver_available("ipopt")
    model, model_results, _, solver_stats = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
        build_only=build_only,
    )
    if build_only:
        return grid, model
    ok = model_results is not None and solver_stats.get("solution_found") is not False
    if not ok:
        if require_solution:
            assert model_results is not None
            assert solver_stats.get("solution_found") is not False
        return None
    return grid, model


def _assert_opf_line_res(grid, model):
    line_res, grid_res = pyf.opf_line_res(model, grid)
    assert len(line_res) > 0
    assert any(key.startswith("AC_Load_") for key in line_res)
    assert "Total" in grid_res


def _assert_opf_step_results(grid, model):
    (
        conv_dc,
        _conv_ac,
        _conv_q_ac,
        p_load,
        _p_ext,
        _q_ext,
        _curtailment,
        loading_conv,
    ) = pyf.opf_step_results(model, grid)
    assert len(p_load) > 0
    assert grid.ACmode and grid.DCmode
    assert len(conv_dc) == len(grid.Converters_ACDC)
    assert len(loading_conv) == len(grid.Converters_ACDC)


def _solve_case24_3zones_price_zone(*, require_solution=True):
    grid, _ = pyf.cases["case24_3zones_acdc"]()
    assert len(grid.Price_Zones) >= 1
    build_only = not pyf.is_pyomo_solver_available("ipopt")
    model, model_results, _, solver_stats = pyf.optimal_pf(
        grid,
        ObjRule={"PZ_cost_of_generation": 1},
        solver="ipopt",
        build_only=build_only,
    )
    if build_only:
        assert hasattr(model, "price_zone_price")
        return grid, model
    ok = model_results is not None and solver_stats.get("solution_found") is not False
    if not ok:
        if require_solution:
            assert model_results is not None
            assert solver_stats.get("solution_found") is not False
        return None
    assert hasattr(model, "price_zone_price")
    return grid, model


def _assert_opf_price_zone(grid, model):
    pz_prices = pyf.opf_price_price_zone(model, grid)
    assert len(pz_prices) == len(grid.Price_Zones)
    for pz in grid.Price_Zones:
        assert pz.name in pz_prices


def test_opf_line_res_case39_acdc():
    require_pyomo()
    grid, model = _solve_case39_acdc()
    _assert_opf_line_res(grid, model)


def test_opf_step_results_case39_acdc():
    require_pyomo()
    grid, model = _solve_case39_acdc()
    _assert_opf_step_results(grid, model)


def test_opf_price_zone_case24_3zones():
    require_pyomo()
    grid, model = _solve_case24_3zones_price_zone()
    _assert_opf_price_zone(grid, model)


def run_test():
    if pyomo_missing_for_run_test():
        return

    grid, model = _solve_case39_acdc()
    _assert_opf_line_res(grid, model)
    _assert_opf_step_results(grid, model)
    _assert_opf_price_zone(*_solve_case24_3zones_price_zone())

    print("✓ OPF result helper tests passed")


if __name__ == "__main__":
    run_test()
