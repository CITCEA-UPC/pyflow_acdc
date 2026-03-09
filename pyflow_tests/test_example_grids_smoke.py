# -*- coding: utf-8 -*-
"""
Smoke tests for example_grids factory functions.
"""

import importlib.util
import inspect
from pathlib import Path

import pytest
import pyflow_acdc as pyf


EXAMPLE_GRIDS_DIR = Path(pyf.__file__).resolve().parent / "example_grids"
EXAMPLE_GRID_FILES = sorted(EXAMPLE_GRIDS_DIR.glob("*.py"))


def _load_module_from_path(file_path):
    module_name = f"_example_grid_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pick_factory(module, stem):
    candidates = [
        fn
        for _, fn in inspect.getmembers(module, inspect.isfunction)
        if not fn.__name__.startswith("_") and fn.__module__ == module.__name__
    ]
    if not candidates:
        raise AssertionError(f"No public factory function found in {module.__name__}")

    for fn in candidates:
        if fn.__name__ == stem:
            return fn
    return candidates[0]


@pytest.mark.parametrize("example_file", EXAMPLE_GRID_FILES, ids=lambda p: p.stem)
def test_example_grid_factory_loads_grid_and_results(example_file):
    """Load each example grid module and verify it returns grid/results."""
    module = _load_module_from_path(example_file)
    factory = _pick_factory(module, example_file.stem)
    result = factory()

    assert isinstance(result, (list, tuple))
    assert len(result) >= 2
    grid, res = result[0], result[1]
    assert grid is not None
    assert res is not None
    assert hasattr(grid, "nodes_AC")
    assert hasattr(grid, "nodes_DC")
    assert len(grid.nodes_AC) > 0


def run_test():
    """Run example_grids smoke test from script entrypoint."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("✓ Example grids smoke test passed")
    else:
        print("✗ Example grids smoke test failed")


if __name__ == "__main__":
    run_test()
