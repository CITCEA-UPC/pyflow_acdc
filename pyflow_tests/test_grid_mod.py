"""Tests for ``grid_modifications``: build-from-empty, CSV templates, cable DB."""

from pathlib import Path

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_acdc.Classes import Cable_options, Line_AC, Line_DC

DUMMY_CABLE_KEY = "PYTEST_DUMMY_AC_CABLE_XYZ"
ORBIT_CABLE_PREFIX = "PYTEST_ORBIT"


def _snapshot_cable_databases():
    Line_AC.load_cable_database()
    Line_DC.load_cable_database()
    Cable_options.load_cable_database()
    return (
        Line_AC._cable_database.copy(),
        Line_DC._cable_database.copy(),
        Cable_options._cable_database.copy()
        if Cable_options._cable_database is not None
        else None,
    )


def _restore_cable_databases(snap):
    ac, dc, co = snap
    Line_AC._cable_database = ac
    Line_DC._cable_database = dc
    Cable_options._cable_database = co


def test_empty_grid_add_elements_price_zones_and_line_types():
    """Build a hybrid grid from empty via grid_modifications API."""
    grid, _ = pyf.create_grid_from_data(100)
    assert len(grid.nodes_AC) == 0

    pyf.add_AC_node(
        grid,
        138,
        node_type="Slack",
        name="n1",
        geometry="POINT (0 0)",
        x_coord=0,
        y_coord=0,
    )
    pyf.add_AC_node(grid, 138, name="n2", geometry="POINT (1 0)")
    pyf.add_AC_node(grid, 138, name="n3", geometry="POINT (2 0)")
    pyf.add_DC_node(grid, 320, node_type="P", name="d1", geometry="POINT (1 1)")
    pyf.add_DC_node(grid, 320, node_type="Slack", name="d2", geometry="POINT (2 1)")

    pyf.add_line_AC(
        grid,
        "n1",
        "n2",
        r=0.02,
        x=0.06,
        b=0.06,
        MVA_rating=150,
        name="l12",
        geometry="LINESTRING (0 0, 1 0)",
    )
    pyf.add_line_AC(
        grid,
        "n2",
        "n3",
        r=0.04,
        x=0.12,
        b=0.03,
        MVA_rating=100,
        name="l23_exp",
        Expandable=True,
        geometry="LINESTRING (1 0, 2 0)",
    )
    pyf.add_line_AC(
        grid,
        "n1",
        "n3",
        r=0.01,
        x=0.03,
        b=0.02,
        MVA_rating=80,
        name="l13_tf",
        tap_changer=True,
        m=1.02,
        shift=0.05,
    )
    pyf.add_line_AC(
        grid,
        "n2",
        "n3",
        r=0.05,
        x=0.15,
        b=0.03,
        MVA_rating=90,
        name="l23_rec",
    )
    pyf.add_line_DC(
        grid,
        "d1",
        "d2",
        r=0.01,
        MW_rating=500,
        name="dc12",
        geometry="LINESTRING (1 1, 2 1)",
    )

    conv = pyf.add_ACDC_converter(
        grid,
        "n2",
        "d1",
        MVA_max=500,
        name="conv_n2_d1",
        geometry="POINT (1 0.5)",
    )
    pyf.add_DCDC_converter(grid, "d1", "d2", MW_rating=200, name="dcdc_12")

    pyf.add_gen(grid, "n1", gen_name="g1", MWmax=100, np_gen=1)
    gdc = pyf.add_gen_DC(grid, "d1", gen_name="gdc1", MWmax=80, np_gen=1)
    assert gdc._node.name == "d1"
    assert gdc in grid.Generators_DC
    assert gdc.name == "gdc1"
    pyf.add_RenSource(grid, "n3", base_MW=50, ren_source_name="wind1", np_rsgen=1)
    pyf.add_RenSource_zone(grid, "offshore_wind")

    onshore = pyf.add_price_zone(grid, "Z_on", price=45.0)
    offshore = pyf.add_offshore_price_zone(grid, onshore, "o_Z_on")
    pyf.add_MTDC_price_zone(grid, "mtdc_agg", linked_price_zones=["Z_on"])

    pyf.assign_nodeToPrice_Zone(grid, "n2", "Z_on", ACDC="AC")
    pyf.assign_nodeToPrice_Zone(grid, "d2", onshore, ACDC="DC")
    pyf.assign_ConvToPrice_Zone(grid, conv, onshore)

    pyf.Line_AC.load_cable_database()
    cable_types = ["NREL_66kV_185mm2", "NREL_66kV_630mm2"]
    cable_opt = pyf.add_cable_option(grid, cable_types=cable_types, name="pytest_opt")
    pyf.add_line_sizing(
        grid,
        "n2",
        "n3",
        cable_types=cable_types,
        name="ct_n2_n3",
        cable_option=cable_opt.name,
        geometry="LINESTRING (1 0, 2 0)",
    )

    pyf.change_line_AC_to_expandable(grid, "l12")
    pyf.change_line_AC_to_reconducting(
        grid,
        "l23_rec",
        r_new=0.008,
        x_new=0.02,
        g_new=0.0,
        b_new=0.015,
        MVA_rating_new=120,
        Life_time=30,
        base_cost=1e6,
    )
    pyf.add_line_AC(
        grid,
        "n1",
        "n2",
        r=0.03,
        x=0.09,
        b=0.04,
        MVA_rating=100,
        name="l12_tf_src",
    )
    pyf.change_line_AC_to_tap_transformer(grid, "l12_tf_src")

    assert len(grid.nodes_AC) == 3
    assert len(grid.nodes_DC) == 2
    assert len(grid.lines_AC_exp) >= 2
    assert len(grid.lines_AC_tf) >= 1
    assert len(grid.lines_AC_rec) >= 1
    assert len(grid.lines_AC_ct) >= 1
    assert len(grid.Converters_ACDC) == 1
    assert len(grid.Converters_DCDC) == 1
    assert len(grid.Price_Zones) == 3
    assert offshore.name == "o_Z_on"
    assert any(n.PZ == "Z_on" for n in grid.nodes_AC)
    assert conv in onshore.ConvACDC
    assert grid.Graph_AC is not None

    # link_cost cascade: a→qf, b→lf (quadratic); price→lf (linear); default none
    n2 = next(n for n in grid.nodes_AC if n.name == "n2")
    pyf.add_extgrid(grid, "n2", link_cost="quadratic")
    ext = next(g for g in grid.Generators if getattr(g, "is_ext_grid", False))
    assert n2.qf == pytest.approx(0.0)
    assert ext.qf == pytest.approx(0.0)
    assert ext.link_cost == "quadratic"
    onshore.b = 55.0
    assert n2.lf == pytest.approx(55.0)
    assert ext.lf == pytest.approx(55.0)
    assert ext.qf == pytest.approx(0.0)
    onshore.a_base = 0.02
    assert n2.qf == pytest.approx(0.02)
    assert ext.qf == pytest.approx(0.02)
    assert ext.lf == pytest.approx(55.0)
    onshore.price = 99.0
    assert n2.price == pytest.approx(99.0)
    assert ext.lf == pytest.approx(55.0)  # quadratic ignores node.price


def test_case24_mp_csv_templates(tmp_path):
    """case24_MP grid should yield gen-mix and investment CSV templates."""
    grid, _ = pyf.cases["case24_MP"]()
    assert len(grid.Generators) > 0 or len(grid.RenSources) > 0

    gen_path = pyf.create_gen_limit_csv_template(
        grid, file_path=tmp_path / "gen_mix_limits.csv"
    )
    inv_path = pyf.create_inv_csv_template(
        grid, file_path=tmp_path / "inv_series.csv"
    )

    gen_df = pd.read_csv(gen_path, header=None)
    inv_df = pd.read_csv(inv_path, header=None)
    assert gen_df.shape[0] >= 2
    assert gen_df.shape[1] >= 1
    assert inv_df.shape[0] >= 2
    assert inv_df.shape[1] >= 1


def test_cable_database_expand_and_orbit_import_do_not_persist():
    """expand_cable_database and import_orbit_cables (GitHub fetch) do not persist."""
    snap = _snapshot_cable_databases()
    ac_count_before = len(Line_AC._cable_database)
    try:
        assert DUMMY_CABLE_KEY not in Line_AC._cable_database.index

        dummy_cable = {
            DUMMY_CABLE_KEY: {
                "R_Ohm_km": 0.1,
                "L_mH_km": 0.4,
                "C_uF_km": 0.2,
                "G_uS_km": 0.0,
                "A_rating": 500,
                "Nominal_voltage_kV": 33,
                "MVA_rating": 30.0,
                "conductor_size": 185,
                "Type": "AC",
                "Reference": "pytest",
            }
        }
        pyf.expand_cable_database(dummy_cable, format="yaml")
        assert DUMMY_CABLE_KEY in Line_AC._cable_database.index
        assert len(Line_AC._cable_database) == ac_count_before + 1

        ac_indices_before_orbit = set(Line_AC._cable_database.index)
        out = pyf.import_orbit_cables(name_prefix=ORBIT_CABLE_PREFIX, default_type="AC")
        assert len(out) > 0
        assert all(str(name).startswith(f"{ORBIT_CABLE_PREFIX}_") for name in out.index)
        orbit_names = [
            name
            for name in Line_AC._cable_database.index
            if str(name).startswith(f"{ORBIT_CABLE_PREFIX}_")
            and name not in ac_indices_before_orbit
        ]
        assert len(orbit_names) > 0
    finally:
        _restore_cable_databases(snap)

    assert DUMMY_CABLE_KEY not in Line_AC._cable_database.index
    assert not any(
        str(name).startswith(f"{ORBIT_CABLE_PREFIX}_")
        for name in Line_AC._cable_database.index
    )
    assert len(Line_AC._cable_database) == ac_count_before


def test_get_gen_p_min_eff_ext_grid_export_only():
    """MWmax=0 with Allow_sell uses MWmin as the export lower bound."""
    from pyflow_acdc.grid_analysis import get_gen_p_min_eff

    grid, _ = pyf.cases["Stagg5MATACDC"]()
    export_mw = 250.0
    pyf.add_extgrid(
        grid,
        "1",
        gen_name="ext_export",
        MVAmax=export_mw,
        MWmax=0,
        MWmin=-export_mw,
        Allow_sell=True,
    )
    ext = next(g for g in grid.Generators if g.name == "ext_export")

    assert get_gen_p_min_eff(ext, 1) == pytest.approx(-export_mw / grid.S_base)
    assert ext.Max_pow_gen * 1 == pytest.approx(0.0)


def test_get_gen_p_min_eff_ext_grid_bidirectional():
    """Bidirectional ext grids keep the symmetric allow_sell bound."""
    from pyflow_acdc.grid_analysis import get_gen_p_min_eff

    grid, _ = pyf.cases["Stagg5MATACDC"]()
    import_mw = 300.0
    pyf.add_extgrid(grid, "2", gen_name="ext_bidir", MVAmax=import_mw, Allow_sell=True)
    ext = next(g for g in grid.Generators if g.name == "ext_bidir")

    assert get_gen_p_min_eff(ext, 1) == pytest.approx(-import_mw / grid.S_base)


def run_test():
    import tempfile

    test_empty_grid_add_elements_price_zones_and_line_types()
    test_case24_mp_csv_templates(Path(tempfile.mkdtemp()))
    test_cable_database_expand_and_orbit_import_do_not_persist()
    print("✓ grid_mod tests passed")


if __name__ == "__main__":
    run_test()
