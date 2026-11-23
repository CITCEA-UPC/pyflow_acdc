"""Round-trip tests for ``save_grid_to_file``."""

import enum
import importlib.util

import pytest

import pyflow_acdc as pyf
from pyflow_acdc.Export_files import create_dictionaries


def _load_saved_grid(py_path, factory_name):
    spec = importlib.util.spec_from_file_location(factory_name, py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    factory = getattr(module, factory_name)
    return factory()


def _normalize_export_value(value):
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _normalize_export_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_export_value(v) for v in value]
    if hasattr(value, "name") and hasattr(value, "price"):
        return value.name
    return value


def _sort_export_rows(rows, key):
    return sorted(rows, key=lambda row: row[key])


def _export_snapshot(grid):
    data = create_dictionaries(grid)
    return {
        "S_base": data["S_base"],
        "nodes_AC": _sort_export_rows(data["nodes_AC"], "Node_id") if data["nodes_AC"] else [],
        "lines_AC": _sort_export_rows(data["lines_AC"], "Line_id") if data["lines_AC"] else [],
        "nodes_DC": _sort_export_rows(data["nodes_DC"], "Node_id") if data["nodes_DC"] else [],
        "lines_DC": _sort_export_rows(data["lines_DC"], "Line_id") if data["lines_DC"] else [],
        "Converters_ACDC": _sort_export_rows(data["Converters_ACDC"], "Conv_id") if data["Converters_ACDC"] else [],
        "Price_Zone": _sort_export_rows(data["Price_Zone"], "name") if data["Price_Zone"] else [],
        "RenSource_zone": _sort_export_rows(data["RenSource_zone"], "name") if data["RenSource_zone"] else [],
        "Generators": _sort_export_rows(data["Generators"], "name") if data["Generators"] else [],
        "Generators_DC": _sort_export_rows(data["Generators_DC"], "name") if data["Generators_DC"] else [],
        "RenSources": _sort_export_rows(data["RenSources"], "ren_source_name") if data["RenSources"] else [],
    }


def _assert_row_equal(row_a, row_b):
    assert row_a.keys() == row_b.keys()
    for key in row_a:
        val_a = _normalize_export_value(row_a[key])
        val_b = _normalize_export_value(row_b[key])
        if isinstance(val_a, (float, int)) and isinstance(val_b, (float, int)):
            assert float(val_a) == pytest.approx(float(val_b), rel=0, abs=1e-9)
        else:
            assert val_a == val_b


def _assert_grid_export_equivalent(grid_a, grid_b):
    snap_a = _export_snapshot(grid_a)
    snap_b = _export_snapshot(grid_b)
    assert snap_a.keys() == snap_b.keys()
    for section in snap_a:
        if section == "S_base":
            assert snap_a[section] == snap_b[section]
            continue
        assert len(snap_a[section]) == len(snap_b[section])
        for row_a, row_b in zip(snap_a[section], snap_b[section]):
            _assert_row_equal(row_a, row_b)


def _round_trip_grid(grid_orig, file_name, tmp_path):
    pyf.save_grid_to_file(grid_orig, file_name, folder_name=str(tmp_path))
    saved_py = tmp_path / f"{file_name}.py"
    assert saved_py.is_file()

    grid_reload, res_reload = _load_saved_grid(saved_py, file_name)

    assert grid_reload.name == file_name
    assert res_reload is not None
    _assert_grid_export_equivalent(grid_orig, grid_reload)


def _round_trip_case(case_name, tmp_path):
    grid_orig, _res_orig = pyf.cases[case_name]()
    _round_trip_grid(grid_orig, f"{case_name.lower()}_export", tmp_path)


@pytest.mark.parametrize(
    "case_name",
    ["NS_MTDC", "Stagg5MATACDC", "DC_OPF_simple"],
)
def test_save_and_reload_example_case(case_name, tmp_path):
    """Export bundled cases to .py loaders and reload equivalent grid data."""
    _round_trip_case(case_name, tmp_path)


def _build_extended_feature_grid():
    grid_orig, res_orig = pyf.cases["Stagg5MATACDC"]()
    pyf.add_extgrid(
        grid_orig,
        "1",
        gen_name="ext_main",
        lf=12.0,
        qf=0.001,
        MVAmax=600,
        P_load_MW=10,
        Allow_sell=False,
    )
    pyf.add_gen(
        grid_orig,
        "4",
        "gen_solar",
        fuel_type="Solar",
        installation_cost=1_000_000,
        MWmax=50,
        Smax=60,
        fc=5,
        np_gen=2,
    )
    pyf.add_RenSource(
        grid_orig,
        "5",
        80,
        ren_source_name="wind5",
        ren_type="Wind",
        min_gamma=0.2,
        np_rsgen=2,
        Qrel=0.3,
        available=0.95,
    )
    return grid_orig, res_orig


def test_save_and_reload_extended_features(tmp_path):
    """Round-trip grid with external grid, gen extras, and RenSource extras."""
    grid_orig, _res_orig = _build_extended_feature_grid()
    _round_trip_grid(grid_orig, "stagg5_extended_export", tmp_path)


def run_test():
    """Script entrypoint using a temporary directory."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(prefix="pyflow_save_grid_") as tmpdir:
        path = Path(tmpdir)
        for case in ("NS_MTDC", "Stagg5MATACDC", "DC_OPF_simple"):
            _round_trip_case(case, path)
        grid_orig, _ = _build_extended_feature_grid()
        _round_trip_grid(grid_orig, "stagg5_extended_export", path)
    print("✓ save_grid_to_file round-trip passed")


if __name__ == "__main__":
    run_test()
