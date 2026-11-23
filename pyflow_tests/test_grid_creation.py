"""Grid creation tests: manual build, ``grid_creator`` import/extend/sub-grid."""

import copy
import gzip
import pickle
from pathlib import Path

import pandas as pd

import pyflow_acdc as pyf
from pyflow_acdc.grid_creator import create_sub_grid

ARRAY_BUNDLE_PATH = Path(__file__).resolve().parent / "alpha_ventus_flat.pkl.gz"
_STAGG5_DATA = Path(__file__).resolve().parents[1] / "examples" / "Stagg5MATACDC"


def _load_array_bundle(path=ARRAY_BUNDLE_PATH):
    if not path.is_file():
        raise FileNotFoundError(
            f"Array graph bundle not found: {path} "
            "(run Graph_Creation/saving_farms.py to generate alpha_ventus_flat.pkl.gz)"
        )
    with gzip.open(path, "rb") as f:
        bundle = pickle.load(f)
    if not isinstance(bundle, (tuple, list)) or len(bundle) != 3:
        raise TypeError(
            f"Expected (array_graph, Data, cable_types) tuple, got {type(bundle).__name__}"
        )
    return bundle


def _bundle_to_extend_tables(array_graph, Data):
    """Build AC node and line DataFrames from an array graph bundle for ``extend_grid_from_data``."""
    sub_key = (
        "offshore_substation"
        if "offshore_substation" in Data
        else "transformer_station"
    )
    node_rows = []
    for i, attrs in array_graph.nodes(data=True):
        point_type = attrs.get("point_type")
        if point_type == "access_point":
            continue
        if point_type == "turbine":
            src = Data["turbine"].loc[attrs["original_idx"]]
        elif point_type == "substation":
            src = Data[sub_key].loc[attrs["original_idx"]]
        else:
            continue
        node_rows.append({
            "Node_id": str(i),
            "geometry": src["geometry"],
            "kV_base": float(src["kV_rating"]),
        })
    nodes = pd.DataFrame(node_rows)

    line_rows = []
    for line_id, (u, v, attrs) in enumerate(array_graph.edges(data=True)):
        u_type = array_graph.nodes[u].get("point_type")
        v_type = array_graph.nodes[v].get("point_type")
        if u_type == "access_point" or v_type == "access_point":
            continue
        line_rows.append({
            "Line_id": f"AC{line_id}",
            "fromNode": str(u),
            "toNode": str(v),
            "R_Ohm_km": 0.1,
            "L_mH_km": 0.4,
            "C_uF_km": 0.2,
            "A_rating": 500.0,
            "Length_km": attrs["length"] / 1000.0,
            "geometry": attrs.get("geometry"),
        })
    lines = pd.DataFrame(line_rows)
    return nodes, lines


def _read_stagg5_csv(name):
    df = pd.read_csv(
        _STAGG5_DATA / name,
        delimiter=",",
        quotechar="'",
        encoding="utf-8",
    )
    for col in ("Node_id", "fromNode", "toNode", "AC_node", "DC_node"):
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def test_manual_grid_creation_and_power_flow():
    """Build a small hybrid grid from element classes and run power flow."""
    pyf.initialize_pyflowacdc()

    S_base = 100

    AC_node_1 = pyf.Node_AC(node_type='Slack', Voltage_0=1.06, theta_0=0, kV_base=345)
    AC_node_2 = pyf.Node_AC(node_type='PV', Voltage_0=1, theta_0=0.1, kV_base=345,Power_Gained=0.4,Power_load=0.2,Reactive_load=0.1)
    AC_node_3 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.45,Reactive_load=0.15)
    AC_node_4 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.4,Reactive_load=0.05)
    AC_node_5 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.6,Reactive_load=0.1)

    AC_line_1 = pyf.Line_AC(AC_node_1, AC_node_2,r=0.02,x=0.06,b=0.06,MVA_rating=150)
    AC_line_2 = pyf.Line_AC(AC_node_1, AC_node_3,r=0.08,x=0.24,b=0.05,MVA_rating=100)
    AC_line_3 = pyf.Line_AC(AC_node_2, AC_node_3,r=0.06,x=0.18,b=0.04,MVA_rating=100)
    AC_line_4 = pyf.Line_AC(AC_node_2, AC_node_4,r=0.06,x=0.18,b=0.04,MVA_rating=100)
    AC_line_5 = pyf.Line_AC(AC_node_2, AC_node_5,r=0.04,x=0.12,b=0.03,MVA_rating=100)
    AC_line_6 = pyf.Line_AC(AC_node_3, AC_node_4,r=0.01,x=0.03,b=0.02,MVA_rating=100)
    AC_line_7 = pyf.Line_AC(AC_node_4, AC_node_5,r=0.08,x=0.24,b=0.05,MVA_rating=100)

    DC_node_1 = pyf.Node_DC(node_type='P', Voltage_0=1,kV_base=345)
    DC_node_2 = pyf.Node_DC(node_type='Slack', Voltage_0=1,kV_base=345)
    DC_node_3 = pyf.Node_DC(node_type='P', Voltage_0=1,kV_base=345)

    DC_line_1 = pyf.Line_DC(DC_node_1, DC_node_2,r=0.052,MW_rating=100,polarity='sm')
    DC_line_2 = pyf.Line_DC(DC_node_2, DC_node_3,r=0.052,MW_rating=100,polarity='sm')
    DC_line_3 = pyf.Line_DC(DC_node_1, DC_node_3,r=0.073,MW_rating=100,polarity='sm')

    Converter_1 = pyf.AC_DC_converter('PQ', 'PAC'  , AC_node_2, DC_node_1, P_AC=-0.6, Q_AC=-0.4, P_DC=0, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)
    Converter_2 = pyf.AC_DC_converter('PV', 'Slack', AC_node_3, DC_node_2, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)
    Converter_3 = pyf.AC_DC_converter('PQ', 'PAC'  , AC_node_5, DC_node_3, P_AC=0.35, Q_AC=0.05, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)

    AC_nodes = [AC_node_1, AC_node_2, AC_node_3, AC_node_4, AC_node_5]
    DC_nodes = [DC_node_1, DC_node_2, DC_node_3]
    AC_lines = [AC_line_1, AC_line_2, AC_line_3, AC_line_4, AC_line_5, AC_line_6, AC_line_7]
    DC_lines = [DC_line_1, DC_line_2, DC_line_3]
    Converters = [Converter_1, Converter_2, Converter_3]

    grid = pyf.Grid(S_base, AC_nodes, AC_lines, Converters, DC_nodes, DC_lines)
    res = pyf.Results(grid, decimals=3)

    pyf.power_flow(grid)
    res.all()


def test_create_sub_grid_ns_mtdc_be():
    grid, _ = pyf.cases["NS_MTDC"]()
    n_ac_full = len(grid.nodes_AC)
    n_dc_full = len(grid.nodes_DC)
    assert n_ac_full > 0
    assert n_dc_full > 0

    grid_copy = copy.deepcopy(grid)
    subgrid, res = create_sub_grid(grid_copy, Area_name="BE")

    assert res is not None
    assert len(subgrid.nodes_AC) > 0
    assert len(subgrid.nodes_AC) < n_ac_full
    assert len(subgrid.nodes_DC) <= n_dc_full
    assert any(pz.name == "BE" for pz in subgrid.Price_Zones)
    assert any(node.PZ == "BE" for node in subgrid.nodes_AC)


def test_create_grid_from_turbine_graph_alpha_ventus_bundle():
    array_graph, Data, cable_types = _load_array_bundle()
    n_turbines = len(Data["turbine"])
    n_edges = array_graph.number_of_edges()
    assert n_turbines > 0
    assert n_edges > 0
    assert len(cable_types) > 0

    grid, res = pyf.create_grid_from_turbine_graph(
        array_graph,
        Data,
        cable_types=cable_types,
        name="alpha_ventus",
    )

    assert res is not None
    assert grid.Array_opf is True
    assert len(grid.nodes_AC) > 0
    assert len(grid.lines_AC_ct) > 0
    assert len(grid.RenSources) == n_turbines
    assert len(grid.Cable_options) == 1
    assert grid.crossing_groups is not None


def test_extend_grid_from_data_stagg5_partial_csv():
    """Extend an empty grid with Stagg5MATACDC CSV tables (nodes first, then rest)."""
    grid, _ = pyf.create_grid_from_data(
        100,
        AC_node_data=_read_stagg5_csv("MATACDC_AC_node_data.csv"),
        data_in="pu",
    )
    n_ac_nodes = len(grid.nodes_AC)
    assert n_ac_nodes == 5
    assert len(grid.lines_AC) == 0

    pyf.extend_grid_from_data(
        grid,
        AC_line_data=_read_stagg5_csv("MATACDC_AC_line_data.csv"),
        DC_node_data=_read_stagg5_csv("MATACDC_DC_node_data.csv"),
        DC_line_data=_read_stagg5_csv("MATACDC_DC_line_data.csv"),
        Converter_data=_read_stagg5_csv("MATACDC_Converter_data.csv"),
        data_in="pu",
    )

    assert len(grid.nodes_AC) == n_ac_nodes
    assert len(grid.lines_AC) == 7
    assert len(grid.nodes_DC) == 3
    assert len(grid.lines_DC) == 3
    assert len(grid.Converters_ACDC) == 3


def test_extend_grid_from_data_alpha_ventus_bundle():
    """Extend empty grid with Real-valued node/line tables built from array bundle."""
    array_graph, Data, _ = _load_array_bundle()
    nodes, lines = _bundle_to_extend_tables(array_graph, Data)

    grid, _ = pyf.create_grid_from_data(100)
    assert len(grid.nodes_AC) == 0
    assert len(grid.lines_AC) == 0

    pyf.extend_grid_from_data(
        grid,
        AC_node_data=nodes,
        AC_line_data=lines,
        data_in="Real",
    )

    assert len(grid.nodes_AC) == len(nodes)
    assert len(grid.lines_AC) == len(lines)
    assert len(grid.nodes_AC) > len(Data["turbine"])
    assert grid.Graph_AC is not None


def run_test():
    test_manual_grid_creation_and_power_flow()
    test_extend_grid_from_data_stagg5_partial_csv()
    test_extend_grid_from_data_alpha_ventus_bundle()
    test_create_sub_grid_ns_mtdc_be()
    test_create_grid_from_turbine_graph_alpha_ventus_bundle()
    print("✓ grid creation tests passed")


if __name__ == "__main__":
    run_test()
