"""
Smoke tests for the top-level examples/ folder.
"""

import os
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import require_mapping

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE_SCRIPTS = sorted(
    p for p in EXAMPLES_DIR.glob("*.py") if p.name != "__init__.py"
)

# Only this script calls pyf.plot_folium (needs [mapping] extra).
FOLIUM_SCRIPT = "Princess_Elisabeth.py"


@pytest.mark.parametrize("script_file", EXAMPLE_SCRIPTS, ids=lambda p: p.stem)
def test_examples_scripts_run(script_file, monkeypatch):
    """Run each examples/*.py script with minimal stubs for heavy optional steps."""
    if script_file.name == FOLIUM_SCRIPT:
        require_mapping()

    # Keep examples runnable without external solvers in CI.
    if script_file.name == "CrigeB4_OPF_Main.py":
        monkeypatch.setattr(
            pyf,
            "optimal_pf",
            lambda *args, **kwargs: (
                SimpleNamespace(),
                None,
                {"create": 0.0, "solve": 0.0, "export": 0.0},
                {"time": 0.0},
            ),
        )

    # Display formatting can rely on solved states; avoid coupling smoke tests
    # to full result table generation.
    monkeypatch.setattr(pyf.Results, "all", lambda self, *args, **kwargs: None)

    # Stub folium if present; raising=False when [mapping] is not installed.
    monkeypatch.setattr(
        pyf, "plot_folium", lambda *args, **kwargs: None, raising=False
    )

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
