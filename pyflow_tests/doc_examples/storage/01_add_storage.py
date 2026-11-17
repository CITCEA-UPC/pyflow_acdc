"""System modelling: Adding BESS (``docs/api/modelling_flexible_assets.rst``)."""
import pyflow_acdc as pyf

pyf.initialize_pyflowacdc()

grid = pyf.Grid(S_base=100)
pyf.add_AC_node(grid, kV_base=220, node_type="PV", name="hub")
pyf.add_DC_node(grid, kV_base=320, node_type="P", name="dc_hub")

storage_ac = pyf.add_storage(
    grid,
    "hub",
    E_max_MWh=50.0,
    P_charge_MW=10.0,
    P_discharge_MW=10.0,
    eta_charge=0.85,
    eta_discharge=0.90,
    soc_min=0.1,
    soc_max=1.0,
    soc_initial=0.5,
)

storage_dc = pyf.add_storage(
    grid,
    "dc_hub",
    E_max_MWh=30.0,
    P_charge_MW=5.0,
    P_discharge_MW=5.0,
    eta_charge=0.9,
    eta_discharge=0.95,
)

assert storage_ac.Node_AC == "hub"
assert storage_dc.Node_DC == "dc_hub"
assert grid.nstorage == 2
assert len(grid.nodes_AC[0].connected_storage) == 1
assert len(grid.nodes_DC[0].connected_storage) == 1
assert hasattr(storage_ac, "S_max")
assert hasattr(storage_dc, "P_max")
assert storage_dc.Q == 0.0
