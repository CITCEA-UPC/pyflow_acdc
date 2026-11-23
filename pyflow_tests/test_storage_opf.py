"""Snapshot NL OPF with AC and DC BESS (Phase 2). Myopic TS + soft soc_ref (Phase 8)."""

import pandas as pd
import pytest

import pyflow_acdc as pyf
from pyflow_acdc.constants import ObjComponent
from pyflow_tests._test_solver_deps import require_pyomo


def _grid_with_storage():
    grid, _ = pyf.cases["case39_acdc"]()
    pyf.add_storage(
        grid,
        "30",
        E_max_MWh=100.0,
        P_charge_MW=33.0,
        P_discharge_MW=33.0,
        eta_charge=0.85,
        eta_discharge=0.90,
        soc_initial=0.5,
        soc_final=0.5,
    )
    dc_node = next(n for n in grid.nodes_DC if n.name == "1")
    pyf.add_storage(
        grid,
        dc_node,
        E_max_MWh=50.0,
        P_charge_MW=10.0,
        P_discharge_MW=10.0,
        eta_charge=0.9,
        eta_discharge=0.95,
        soc_initial=0.5,
    )
    return grid


def _attach_min_time_series(grid, n_frames=5):
    pattern = [1.0, 0.88, 0.76, 0.92, 1.05]
    factors = [pattern[i % len(pattern)] for i in range(n_frames)]
    pyf.add_TimeSeries(
        grid,
        pd.DataFrame({"load": factors}),
        associated="30",
        TS_type="Load",
    )


def _grid_with_storage_and_ts(n_frames=5):
    grid = _grid_with_storage()
    _attach_min_time_series(grid, n_frames=n_frames)
    return grid


def test_storage_nl_model_builds():
    require_pyomo()
    grid = _grid_with_storage()
    pyf.analyse_grid(grid)
    assert grid.ESS is True

    model, _, _, _ = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    assert hasattr(model, "storage")
    assert hasattr(model, "P_storage_charge")
    assert hasattr(model, "Q_storage")
    assert hasattr(model, "S_storage_AC_limit_constraint")
    assert hasattr(model, "P_storage_DC_net_upper_constraint")
    assert hasattr(model, "Gen_Pstorage_constraint")
    assert hasattr(model, "Gen_Pstorage_DC_constraint")
    assert len(model.storage) == 2


def test_ext_storage_reporting():
    require_pyomo()
    grid = _grid_with_storage()
    pyf.optimal_pf(grid, ObjRule={"Energy_cost": 1}, build_only=True)

    res = pyf.Results(grid)
    df = res.ext_storage(print_table=False)

    assert "Ext_storage" in res.tables
    assert len(df) == 3  # AC + DC + Total
    assert set(df.loc[df["Name"] != "Total", "Side"]) == {"AC", "DC"}
    assert "P charge (MW)" in df.columns
    assert "SoC (pu)" in df.columns
    ac_row = df[df["Side"] == "AC"].iloc[0]
    dc_row = df[df["Side"] == "DC"].iloc[0]
    assert ac_row["Q (MVAR)"] != "----"
    assert dc_row["Q (MVAR)"] == "----"


def test_storage_opf_solves_when_ipopt_available():
    require_pyomo()
    if not pyf.is_pyomo_solver_available("ipopt"):
        return

    grid = _grid_with_storage()
    model, model_res, _, solver_stats = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
        tee=False,
    )
    assert model_res is not None
    assert solver_stats.get("solution_found") is not False

    ac_storage = next(s for s in grid.storage_elements if s.connected.value == "AC")
    dc_storage = next(s for s in grid.storage_elements if s.connected.value == "DC")
    tol = 1e-5
    assert ac_storage.soc_min - tol <= ac_storage.SoC <= ac_storage.soc_max + tol
    assert dc_storage.soc_min - tol <= dc_storage.SoC <= dc_storage.soc_max + tol
    assert -tol <= ac_storage.P_charge <= ac_storage.P_charge_max + tol
    assert -tol <= ac_storage.P_discharge <= ac_storage.P_discharge_max + tol
    assert -tol <= dc_storage.P_charge <= dc_storage.P_charge_max + tol
    assert -tol <= dc_storage.P_discharge <= dc_storage.P_discharge_max + tol
    assert hasattr(ac_storage, "Q")
    assert model.obj is not None


def test_window_nl_opf_requires_time_series():
    require_pyomo()
    grid = _grid_with_storage()
    with pytest.raises(ValueError, match="Time_series"):
        pyf.window_nl_opf(grid, start=0, end=1, build_only=True)


def test_window_nl_opf_builds_multi_frame_model():
    require_pyomo()
    grid = _grid_with_storage_and_ts()
    model, _, _, _ = pyf.window_nl_opf(
        grid,
        start=0,
        end=4,
        ObjRule={"Energy_cost": 1},
        build_only=True,
    )

    assert hasattr(model, "frame_model")
    assert hasattr(model, "window_soc_constraint")
    assert len(model.frames) == 5
    for t in model.frames:
        block = model.frame_model[t]
        assert hasattr(block, "SoC")
        assert not hasattr(block, "SoC_prev")
        assert not hasattr(block, "storage_soc_balance_constraint")
    assert len(model.window_soc_constraint) >= 2
    assert "storage_soc" in grid.window_opf_results
    assert grid.window_opf_run is True


def test_storage_window_reporting():
    require_pyomo()
    grid = _grid_with_storage_and_ts()
    pyf.window_nl_opf(grid, start=0, end=4, ObjRule={"Energy_cost": 1}, build_only=True)

    res = pyf.Results(grid)
    soc_df, summary_df = res.storage_window(print_table=False)

    assert "Storage_window_soc" in res.tables
    assert "Storage_window_power" in res.tables
    assert len(soc_df) == 6  # frames -1…4 (leading soc_initial row)
    assert len(summary_df) == 2


def test_storage_soc_ref_defaults_to_soc_initial():
    grid = _grid_with_storage()
    for st in grid.storage_elements:
        assert st.soc_ref == st.soc_initial


def test_storage_soc_ref_param_and_soc_deviation_obj():
    require_pyomo()
    grid = _grid_with_storage()
    pyf.analyse_grid(grid)
    model, _, _, _ = pyf.optimal_pf(
        grid,
        ObjRule={"Energy_cost": 1, "SoC_deviation": 1},
        build_only=True,
    )
    assert hasattr(model, "soc_ref")
    assert not hasattr(model, "soc_ref_DC")
    ac_id = next(
        s.storageNumber
        for s in grid.storage_elements
        if s.connected.value == "AC"
    )
    assert model.soc_ref[ac_id].value == pytest.approx(0.5)
    from pyflow_acdc.constants import default_obj_weights
    assert ObjComponent.SOC_DEVIATION in default_obj_weights()


def test_ts_acdc_opf_carries_soc_when_ipopt_available():
    require_pyomo()
    if not pyf.is_pyomo_solver_available("ipopt"):
        return

    grid = _grid_with_storage_and_ts(n_frames=4)
    pyf.ts_acdc_opf(
        grid,
        start=1,
        end=4,
        ObjRule={"Energy_cost": 1, "SoC_deviation": 10},
        solver="ipopt",
    )
    assert "storage_soc" in grid.time_series_results
    assert "storage_power" in grid.time_series_results
    soc_df = grid.time_series_results["storage_soc"]
    assert len(soc_df) == 4
    ac = next(s for s in grid.storage_elements if s.connected.value == "AC")
    assert ac.soc_initial == pytest.approx(float(soc_df[ac.name].iloc[-1]), abs=1e-6)
    assert ac.soc_min - 1e-5 <= float(soc_df[ac.name].min())
    assert float(soc_df[ac.name].max()) <= ac.soc_max + 1e-5


def run_test():
    test_storage_nl_model_builds()
    test_ext_storage_reporting()
    test_storage_opf_solves_when_ipopt_available()
    test_storage_soc_ref_defaults_to_soc_initial()
    test_storage_soc_ref_param_and_soc_deviation_obj()
    test_window_nl_opf_requires_time_series()
    test_window_nl_opf_builds_multi_frame_model()
    test_storage_window_reporting()
    test_ts_acdc_opf_carries_soc_when_ipopt_available()
    print("OK test_storage_opf")


def _print_results_demo():
    require_pyomo()
    opf_kwargs = {"ObjRule": {"Energy_cost": 1}}
    if pyf.is_pyomo_solver_available("ipopt"):
        opf_kwargs["solver"] = "ipopt"
    else:
        opf_kwargs["build_only"] = True

    print("\n=== Snapshot NL OPF — ext_storage ===")
    grid = _grid_with_storage()
    pyf.optimal_pf(grid, **opf_kwargs)
    pyf.Results(grid).ext_storage(print_table=True)

    print("\n=== Window NL OPF — storage_window + ext_storage (last frame) ===")
    grid = _grid_with_storage_and_ts()
    pyf.window_nl_opf(grid, start=0, end=4, **opf_kwargs)
    res = pyf.Results(grid)
    res.storage_window(print_table=True)
    res.ext_storage(print_table=True)


if __name__ == "__main__":
    run_test()
    _print_results_demo()
