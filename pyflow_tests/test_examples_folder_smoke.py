# -*- coding: utf-8 -*-
"""
Smoke tests for the top-level examples/ folder.
"""

import os
import runpy
from types import SimpleNamespace
from pathlib import Path

import pandas as pd
import pytest
import pyflow_acdc as pyf


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE_PICKLES = sorted(EXAMPLES_DIR.glob("*.pkl.gz"))
EXAMPLE_SCRIPTS = sorted(EXAMPLES_DIR.glob("*.py"))


@pytest.mark.parametrize("pickle_file", EXAMPLE_PICKLES, ids=lambda p: p.stem)
def test_examples_pickle_loads_grid_and_results(pickle_file):
    """Each packaged example pickle should load into (grid, results)."""
    grid, res = pyf.Create_grid_from_pickle(str(pickle_file), use_dill=True)

    assert grid is not None
    assert res is not None
    assert hasattr(grid, "nodes_AC")
    assert hasattr(grid, "nodes_DC")
    assert len(grid.nodes_AC) + len(grid.nodes_DC) > 0


def test_cigreb4_csv_inputs_build_grid():
    """The CIGRE B4 example CSV set should build a grid."""
    base = EXAMPLES_DIR / "CigreB4"
    ac_node_data = pd.read_csv(base / "CigreB4_AC_node_data.csv")
    dc_node_data = pd.read_csv(base / "CigreB4_DC_node_data.csv")
    ac_line_data = pd.read_csv(base / "CigreB4_AC_line_data.csv")
    dc_line_data = pd.read_csv(base / "CigreB4_DC_line_data.csv")
    converter_data = pd.read_csv(base / "CigreB4_Converter_data.csv")

    grid, res = pyf.Create_grid_from_data(
        100,
        ac_node_data,
        ac_line_data,
        dc_node_data,
        dc_line_data,
        converter_data,
    )

    assert grid is not None
    assert res is not None
    assert len(grid.nodes_AC) > 0


def test_matacdc_real_csv_inputs_build_grid():
    """The MATACDC Real CSV set should build a grid."""
    base = EXAMPLES_DIR / "Stagg5MATACDC"
    ac_node_data = pd.read_csv(base / "MATACDC_AC_node_data_Real.csv")
    dc_node_data = pd.read_csv(base / "MATACDC_DC_node_data_Real.csv")
    ac_line_data = pd.read_csv(base / "MATACDC_AC_line_data_Real.csv")
    dc_line_data = pd.read_csv(base / "MATACDC_DC_line_data_Real.csv")
    converter_data = pd.read_csv(base / "MATACDC_Converter_data_Real.csv")

    grid, res = pyf.Create_grid_from_data(
        100,
        ac_node_data,
        ac_line_data,
        dc_node_data,
        dc_line_data,
        converter_data,
        data_in="Real",
    )

    assert grid is not None
    assert res is not None
    assert len(grid.nodes_AC) > 0


@pytest.mark.parametrize("script_file", EXAMPLE_SCRIPTS, ids=lambda p: p.stem)
def test_examples_scripts_run(script_file, monkeypatch):
    """Run each examples/*.py script with minimal stubs for heavy optional steps."""
    if script_file.name == "__init__.py":
        pytest.skip("__init__ module is not a runnable example script")

    # Keep examples runnable without external solvers in CI.
    if script_file.name == "CrigeB4_OPF_Main.py":
        monkeypatch.setattr(
            pyf,
            "Optimal_PF",
            lambda *args, **kwargs: (
                SimpleNamespace(),
                None,
                {"create": 0.0, "solve": 0.0, "export": 0.0},
                {"time": 0.0},
            ),
        )

    # Display formatting can rely on solved states; avoid coupling smoke tests
    # to full result table generation.
    monkeypatch.setattr(pyf.Results, "All", lambda self, *args, **kwargs: None)

    # Avoid optional plotting side-effects during script smoke runs.
    monkeypatch.setattr(pyf, "plot_folium", lambda *args, **kwargs: None)

    # Example scripts use relative data paths from examples/ as working directory.
    prev_cwd = os.getcwd()
    try:
        os.chdir(str(EXAMPLES_DIR))
        runpy.run_path(str(script_file), run_name="__main__")
    finally:
        os.chdir(prev_cwd)


def run_test():
    """Run examples-folder smoke tests from script entrypoint."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("✓ Examples folder smoke tests passed")
    else:
        print("✗ Examples folder smoke tests failed")


if __name__ == "__main__":
    run_test()
