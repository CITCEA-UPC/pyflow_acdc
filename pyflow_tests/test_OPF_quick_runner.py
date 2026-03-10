"""
Pytest wrapper for script-style OPF/TEP/LOPF tests.

These files are full tests but are not pytest-auto-collected by filename
pattern, so this wrapper executes their run_test() entrypoints in fake-solve
mode to validate loading and model creation in quick runs.
"""

import importlib

import pytest
from pyflow_tests._quick_fake_solve import quick_fake_solve_context


FULL_OPF_TEP_CASE_MODULES = [
    # OPF
    "pyflow_tests.DC_OPF",
    "pyflow_tests.CigreB4_OPF",
    "pyflow_tests.case39ac_OPF",
    "pyflow_tests.case39acdc_OPF",
    "pyflow_tests.case24_3zones_acdc_OPF",
    "pyflow_tests.case24_OPF",
    # LOPF
    "pyflow_tests.case39ac_LOPF",
    # TEP / related expansion
    "pyflow_tests.case6_TEP_DC",
    "pyflow_tests.case24_TEP",
    "pyflow_tests.case24_REC",
    "pyflow_tests.array_sizing",
]


@pytest.mark.parametrize("module_name", FULL_OPF_TEP_CASE_MODULES)
def test_opf_tep_lopf_run_test_entrypoints_quick_fake_solve(module_name, monkeypatch):
    pytest.importorskip("pyomo")
    import pyomo.environ as pyo

    class _AlwaysAvailableSolver:
        def available(self):
            return True

    # Keep in-file dependency guards from short-circuiting quick fake runs.
    monkeypatch.setattr(pyo, "SolverFactory", lambda *args, **kwargs: _AlwaysAvailableSolver())

    module = importlib.import_module(module_name)
    assert hasattr(module, "run_test"), f"{module_name} does not expose run_test()"

    # Validate load + model-build paths without requiring actual solver binaries.
    with quick_fake_solve_context(opf=True, tep=True):
        module.run_test()


def run_test():
    """Run this pytest wrapper from run_tests.py contract."""
    exit_code = pytest.main([__file__, "-q"])
    if exit_code == 0:
        print("OPF/TEP/LOPF quick wrapper passed")
    else:
        print("OPF/TEP/LOPF quick wrapper failed")


if __name__ == "__main__":
    run_test()
