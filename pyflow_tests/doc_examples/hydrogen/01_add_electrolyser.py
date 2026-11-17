"""System modelling: Adding an electrolyser (``docs/api/modelling_flexible_assets.rst``)."""
import pyflow_acdc as pyf

pyf.initialize_pyflowacdc()

grid = pyf.Grid(S_base=100)
pyf.add_AC_node(grid, kV_base=220, node_type="PV", name="hub")
pyf.add_DC_node(grid, kV_base=320, node_type="P", name="dc_hub")

el_ac = pyf.add_electrolyser(
    grid,
    "hub",
    P_max_MW=150.0,
    P_min_MW=22.5,
    b_h=16.0585,
    c_h=8.2195,
    H2_mass_max_kg=43448.0,
    H2_mass_initial_kg=0.0,
    Q_min_MVAR=-10.0,
    Q_max_MVAR=10.0,
)

el_dc = pyf.add_electrolyser(
    grid,
    "dc_hub",
    P_max_MW=50.0,
    P_min_MW=7.5,
    b_h=16.0585,
    c_h=8.2195,
    H2_mass_max_kg=10000.0,
    H2_mass_initial_kg=0.0,
)

assert el_ac.Node_AC == "hub"
assert el_dc.Node_DC == "dc_hub"
assert grid.nelectrolysers == 2
assert len(grid.nodes_AC[0].connected_electrolyser) == 1
assert len(grid.nodes_DC[0].connected_electrolyser) == 1
assert el_dc.Q_min == 0.0 and el_dc.Q_max == 0.0
