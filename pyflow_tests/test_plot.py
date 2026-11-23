from pathlib import Path

import pytest
import pyflow_acdc as pyf
from pyflow_acdc.Graph_and_plot import update_hovertexts
from pyflow_acdc.windfarm_loader import load_case_grid_and_geo
from pyflow_tests.test_constants import CABLE_TYPES_OFF66, MORAY_EAST_CABLE_DECISIONS


def _get_plot_context(grid):
    polygon = getattr(grid, "dev_polygon", None)
    exclusion_zones = getattr(grid, "exclusion_zones", None)
    export_cables = getattr(grid, "export_cables", None)

    if isinstance(polygon, list):
        try:
            from shapely.ops import unary_union
            polygon = unary_union(polygon) if polygon else None
        except Exception:
            polygon = polygon[0] if polygon else None

    if isinstance(exclusion_zones, list):
        try:
            from shapely.ops import unary_union
            exclusion_zones = unary_union(exclusion_zones) if exclusion_zones else None
        except Exception:
            exclusion_zones = exclusion_zones[0] if exclusion_zones else None

    if polygon is not None and exclusion_zones is not None:
        try:
            polygon = polygon.difference(exclusion_zones)
        except Exception:
            pass
    return polygon, export_cables


def _assign_manual_cables(grid):
    # Same cable assignment approach used in Graph_Creation/WES_ComparisonNL_L.py.
    grid.cab_types_allowed = len(CABLE_TYPES_OFF66)
    cable_index = {name: idx for idx, name in enumerate(CABLE_TYPES_OFF66)}
    for line in grid.lines_AC_ct:
        line.cable_types = list(CABLE_TYPES_OFF66)
        line.active_config = cable_index.get(MORAY_EAST_CABLE_DECISIONS.get(str(line.name), ""), -1)


def _load_moray_grid():
    return load_case_grid_and_geo("moray_east", source_tag="gebco")


def _build_tf_ct_grid():
    """Minimal grid with transformer and cable-type AC lines."""
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, 138, node_type="Slack", name="n1", x_coord=0, y_coord=0)
    pyf.add_AC_node(grid, 138, name="n2", x_coord=1, y_coord=0)
    pyf.add_AC_node(grid, 138, name="n3", x_coord=2, y_coord=0)

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

    pyf.Line_AC.load_cable_database()
    cable_types = ["NREL_66kV_185mm2", "NREL_66kV_630mm2"]
    cable_opt = pyf.add_cable_option(grid, cable_types=cable_types, name="pytest_hover_opt")
    pyf.add_line_sizing(
        grid,
        "n2",
        "n3",
        cable_types=cable_types,
        name="ct_n2_n3",
        cable_option=cable_opt.name,
    )
    return grid


def _assert_hovertext_modes(grid, element_getter, required_by_mode):
    for mode, fragments in required_by_mode.items():
        update_hovertexts(grid, mode)
        element = element_getter(grid)
        assert element.hover_text, f"Missing hover_text for {mode}"
        for fragment in fragments:
            assert fragment in element.hover_text, f"{mode}: expected {fragment!r} in hover_text"


def test_moray_east_assign_and_plot_outputs(tmp_path):
    pytest.importorskip("folium")
    pytest.importorskip("branca")
    pytest.importorskip("svgwrite")

    grid, _res = _load_moray_grid()
    _assign_manual_cables(grid)

    assert any(line.active_config >= 0 for line in grid.lines_AC_ct), "No cable type was assigned."

    final_polygon, export_cables = _get_plot_context(grid)
    svg_prefix = tmp_path / "moray_east_manual_network"
    html_3d_path = tmp_path / "moray_east_manual_3d.html"
    folium_prefix = tmp_path / "moray_east_manual_map"

    pyf.save_network_svg(
        grid,
        name=str(svg_prefix),
        width=1000,
        height=1000,
        journal=True,
        legend=False,
        square_ratio=True,
        poly=final_polygon,
        linestrings=export_cables,
    )
    pyf.plot_3D(grid, show=False, save_path=str(html_3d_path))
    pyf.plot_folium(
        grid,
        name=str(folium_prefix),
        show=False,
        polygon=final_polygon,
        linestrings=export_cables,
        clustering=False,
    )

    assert Path(f"{svg_prefix}.svg").exists(), "SVG export was not created."
    assert html_3d_path.exists(), "3D HTML export was not created."
    assert Path(f"{folium_prefix}.html").exists(), "Folium HTML export was not created."


def test_hovertexts_exp_tf_and_ct():
    """Hover text for expandable, transformer, and cable-type AC lines."""
    grid_tep, _ = pyf.cases["case24_TEP"]()
    assert len(grid_tep.lines_AC_exp) > 0
    _assert_hovertext_modes(
        grid_tep,
        lambda g: g.lines_AC_exp[0],
        {
            "data": ["Line:", "Number of lines", "Installation cost"],
            "inPu": ["Loading", "Number of lines"],
            "Real": ["MVA", "Number of lines"],
        },
    )

    grid = _build_tf_ct_grid()
    _assert_hovertext_modes(
        grid,
        lambda g: g.lines_AC_tf[0],
        {
            "data": ["Transformer:", "Tap:", "Shift:", "Rating"],
            "inPu": ["Transformer:", "Tap:", "Loading"],
            "Real": ["Transformer:", "Tap:", "MVA"],
        },
    )
    _assert_hovertext_modes(
        grid,
        lambda g: g.lines_AC_ct[0],
        {
            "data": ["Cable type line:", "Installation cost"],
            "inPu": ["Cable type line:", "Cable type:"],
            "Real": ["MVA", "Cable type:"],
        },
    )


def test_ns_mtdc_generates_hovertexts():
    grid, _res = pyf.cases['NS_MTDC']()

    # Exercise hovertext generation paths on a representative built-in grid.
    update_hovertexts(grid, "data")
    update_hovertexts(grid, "inPu")
    update_hovertexts(grid, "Real")

    assert len(grid.nodes_AC) > 0, "NS_MTDC did not provide AC nodes."
    assert hasattr(grid.nodes_AC[0], "hover_text") and grid.nodes_AC[0].hover_text

    if getattr(grid, "lines_AC", []):
        assert hasattr(grid.lines_AC[0], "hover_text") and grid.lines_AC[0].hover_text
    if getattr(grid, "lines_DC", []):
        assert hasattr(grid.lines_DC[0], "hover_text") and grid.lines_DC[0].hover_text
    if getattr(grid, "Converters_ACDC", []):
        assert hasattr(grid.Converters_ACDC[0], "hover_text") and grid.Converters_ACDC[0].hover_text


def run_test():
    """Run plotting tests from the legacy run_tests.py harness."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("tests_plot passed")
    else:
        print("tests_plot failed")


if __name__ == "__main__":
    run_test()
