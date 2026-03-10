from pathlib import Path

import pytest
import pyflow_acdc as pyf
from pyflow_acdc.windfarm_loader import load_case_grid_and_geo


MORAY_EAST_CABLE_DECISIONS = {
    "45_46": "MOF_240",
    "43_46": "MOF_240",
    "42_43": "MOF_240",
    "41_42": "MOF_240",
    "40_41": "MOF_630",
    "36_40": "MOF_630",
    "36_100": "MOF_630",
    "38_44": "MOF_240",
    "38_39": "MOF_240",
    "35_39": "MOF_240",
    "33_35": "MOF_240",
    "33_34": "MOF_630",
    "34_100": "MOF_630",
    "27_31": "MOF_240",
    "26_27": "MOF_240",
    "25_26": "MOF_240",
    "24_25": "MOF_240",
    "23_24": "MOF_630",
    "23_32": "MOF_630",
    "32_100": "MOF_630",
    "57_58": "MOF_240",
    "56_57": "MOF_240",
    "55_56": "MOF_240",
    "54_55": "MOF_240",
    "53_54": "MOF_630",
    "37_53": "MOF_630",
    "37_100": "MOF_630",
    "47_67": "MOF_240",
    "47_48": "MOF_240",
    "48_49": "MOF_240",
    "49_50": "MOF_240",
    "50_51": "MOF_630",
    "51_52": "MOF_630",
    "52_100": "MOF_630",
    "70_71": "MOF_240",
    "69_70": "MOF_240",
    "69_73": "MOF_240",
    "72_73": "MOF_240",
    "68_72": "MOF_630",
    "66_68": "MOF_630",
    "62_66": "MOF_630",
    "62_102": "MOF_630",
    "96_99": "MOF_240",
    "95_96": "MOF_240",
    "87_95": "MOF_240",
    "86_87": "MOF_240",
    "63_86": "MOF_630",
    "63_64": "MOF_630",
    "64_65": "MOF_630",
    "65_102": "MOF_630",
    "97_98": "MOF_240",
    "93_97": "MOF_240",
    "93_94": "MOF_240",
    "91_94": "MOF_240",
    "85_91": "MOF_630",
    "78_85": "MOF_630",
    "78_102": "MOF_630",
    "82_88": "MOF_240",
    "88_92": "MOF_240",
    "89_92": "MOF_240",
    "89_90": "MOF_240",
    "77_90": "MOF_630",
    "77_102": "MOF_630",
    "28_29": "MOF_240",
    "29_30": "MOF_240",
    "30_60": "MOF_240",
    "60_102": "MOF_240",
    "83_84": "MOF_240",
    "79_84": "MOF_240",
    "76_79": "MOF_240",
    "61_76": "MOF_240",
    "13_61": "MOF_630",
    "13_16": "MOF_630",
    "16_101": "MOF_630",
    "74_81": "MOF_240",
    "80_81": "MOF_240",
    "75_80": "MOF_240",
    "59_75": "MOF_240",
    "12_59": "MOF_630",
    "11_12": "MOF_630",
    "11_101": "MOF_630",
    "2_3": "MOF_240",
    "1_2": "MOF_240",
    "0_1": "MOF_240",
    "0_6": "MOF_240",
    "5_6": "MOF_630",
    "4_5": "MOF_630",
    "4_101": "MOF_630",
    "14_15": "MOF_240",
    "7_15": "MOF_240",
    "7_8": "MOF_240",
    "8_9": "MOF_240",
    "9_10": "MOF_630",
    "10_101": "MOF_630",
    "21_22": "MOF_240",
    "20_21": "MOF_240",
    "19_20": "MOF_240",
    "18_19": "MOF_240",
    "17_18": "MOF_630",
    "17_101": "MOF_630",
}

CABLE_TYPES_OFF66 = [
    "MOF_240",
    "MOF_300",
    "MOF_630",
    "MOF_800",
]


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
    cable_index = {name: idx for idx, name in enumerate(CABLE_TYPES_OFF66)}
    for line in grid.lines_AC_ct:
        line.active_config = cable_index.get(MORAY_EAST_CABLE_DECISIONS.get(str(line.name), ""), -1)


def _load_moray_grid():
    return load_case_grid_and_geo("Moray_East", source_tag="gebco")


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


def run_test():
    """Run plotting tests from the legacy run_tests.py harness."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("tests_plot passed")
    else:
        print("tests_plot failed")


if __name__ == "__main__":
    run_test()