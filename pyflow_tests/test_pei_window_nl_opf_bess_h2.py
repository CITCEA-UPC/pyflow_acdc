"""Phase 6: PEI 24 h window_nl_opf with coupled BESS and electrolyser.

Uses the full ``PEI_grid`` with BE, UK, and DK export links. Validates model
assembly, Table 1 asset parameters, and (when IPOPT is available) a coupled solve.
"""

import pytest

import pyflow_acdc as pyf
from pyflow_acdc.example_grids.PF._pei_bess_data import (
    BESS_E_MAX_MWH,
    BESS_P_NOM_MW,
    EXPORT_NODE_TO_ZONE,
    EXPORT_PRICE_NODES,
    EXPORT_PRICE_ZONES,
    H2_MASS_FINAL_KG,
    HUB_NODE,
    PEI_OBJ_RULE,
    PEI_SEASONS,
    load_pei_export_prices,
    load_pei_power_matrix,
)
from pyflow_tests._test_solver_deps import require_pyomo


def test_pei_power_matrix_available():
    assert load_pei_power_matrix().shape == (160, 24)
    assert load_pei_power_matrix(seasons=PEI_SEASONS).shape == (160, 96)


def test_pei_export_prices_available():
    prices = load_pei_export_prices()
    assert set(prices) == set(EXPORT_PRICE_ZONES)
    for zone, series in prices.items():
        assert series.shape == (24,), zone

    prices_all = load_pei_export_prices(seasons=PEI_SEASONS)
    for zone, series in prices_all.items():
        assert series.shape == (96,), zone

    by_node = load_pei_export_prices(by_zone=False)
    assert set(by_node) == set(EXPORT_PRICE_NODES)


def test_pei_bess_h2_grid_assets():
    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
        attach_wind=False,
    )
    pyf.analyse_grid(grid)

    assert grid.ESS is True
    assert grid.H2 is True
    assert len(grid.storage_elements) == 1
    assert len(grid.electrolysers) == 1
    assert {pz.name for pz in grid.Price_Zones} >= set(EXPORT_PRICE_ZONES)
    price_ts = {
        ts.element_name
        for ts in grid.Time_series
        if ts.type == "b_CG"
    }
    for zone_name in EXPORT_PRICE_ZONES:
        assert zone_name in price_ts
    for node_name, zone_name in EXPORT_NODE_TO_ZONE.items():
        node = next(n for n in grid.nodes_AC if n.name == node_name)
        assert node.PZ == zone_name
        assert node.qf == 0
        ext = next(
            g for g in grid.Generators
            if getattr(g, "is_ext_grid", False) and g._node.name == node_name
        )
        assert ext.link_cost == "quadratic"
        assert ext.qf == 0
    bess = grid.storage_elements[0]
    assert bess.Node == HUB_NODE
    assert bess.E_max == pytest.approx(BESS_E_MAX_MWH)
    assert bess.P_charge_max * grid.S_base == pytest.approx(BESS_P_NOM_MW)
    assert bess.P_discharge_max * grid.S_base == pytest.approx(BESS_P_NOM_MW)
    assert grid.electrolysers[0].Node == HUB_NODE
    assert grid.electrolysers[0].H2_mass_final == pytest.approx(
        H2_MASS_FINAL_KG, rel=1e-6
    )


def test_pei_window_nl_opf_bess_h2_builds():
    require_pyomo()
    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
    )
    assert len(grid.Time_series) == 163

    n_hours = len(grid.Time_series[0].data)
    model, _, _, _ = pyf.window_nl_opf(
        grid,
        start=0,
        end=n_hours - 1,
        ObjRule=PEI_OBJ_RULE,
        build_only=True,
    )

    assert hasattr(model, "window_soc_constraint")
    assert hasattr(model, "window_h2_constraint")
    assert len(model.frames) == n_hours

    block0 = model.frame_model[0]
    assert hasattr(block0, "storage")
    assert hasattr(block0, "electrolyser")
    assert len(block0.storage) == 1
    assert len(block0.electrolyser) == 1


@pytest.mark.slow
def test_pei_window_nl_opf_bess_h2_solves_when_ipopt_available():
    require_pyomo()
    if not pyf.is_pyomo_solver_available("ipopt"):
        pytest.skip("IPOPT not available")

    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
    )
    n_hours = len(grid.Time_series[0].data)
    model, _, _, stats = pyf.window_nl_opf(
        grid,
        start=0,
        end=n_hours - 1,
        ObjRule=PEI_OBJ_RULE,
        solver="ipopt",
        tee=False,
    )

    assert stats is not None
    assert hasattr(model, "obj")
