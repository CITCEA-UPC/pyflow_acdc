"""Shared dependency and solver checks for script-style case tests.

``require_*()`` — pytest entrypoints (call :func:`pytest.skip`).
``*_missing_for_run_test()`` — ``run_test()`` entrypoints (print and return ``True``).
"""

import os

import pytest

import pyflow_acdc as pyf
from pyflow_acdc.constants import ORTOOLS_LINEAR_SOLVERS, PYOMO_LINEAR_SOLVERS
from pyflow_acdc.solver_utils import cvxpy_available, resolve_socp_solver

_PYOMO_LINEAR_SKIP = (
    f"no Pyomo MIP/CSS-L solver available "
    f"(need one of: {', '.join(PYOMO_LINEAR_SOLVERS)})"
)
_ORTOOLS_LP_SKIP = (
    f"no OR-Tools linear CSS-L solver available "
    f"(need one of: {', '.join(ORTOOLS_LINEAR_SOLVERS)})"
)
_MAPPING_SKIP = "mapping extra not installed (pip install pyflow-acdc[mapping])"
_TEP_PYMOO_SKIP = "TEP_pymoo extra not installed (pip install pyflow-acdc[TEP_pymoo])"
_SOCP_SKIP = "cvxpy is not installed (pip install pyflow-acdc[SOCP])"


def _require(ok, message):
    if not ok:
        pytest.skip(message)


def _missing_for_run_test(ok, message):
    if ok:
        return False
    print(f"Skipped: {message}")
    return True


def _pyomo_available():
    try:
        __import__("pyomo")
    except Exception:
        return False
    return True


def pyomo_missing_for_run_test():
    return _missing_for_run_test(_pyomo_available(), "pyomo is not installed")


def require_pyomo():
    _require(_pyomo_available(), "pyomo is not installed")


def require_socp():
    _require(cvxpy_available() and hasattr(pyf, "socp_optimise"), _SOCP_SKIP)


def socp_solver():
    """Return preferred CVXPY conic solver for SOCP tests."""
    require_socp()
    chosen = resolve_socp_solver()
    if chosen is None:
        raise RuntimeError("no supported SOCP solver installed (need MOSEK, CLARABEL, or SCS)")
    return chosen


def socp_mi_solver():
    """Return preferred MI-capable CVXPY conic solver, or skip if none."""
    require_socp()
    from pyflow_acdc.solver_utils import SOCP_MI_CAPABLE_SOLVERS, resolve_socp_solver
    chosen = resolve_socp_solver(mi_required=True)
    if chosen is None or chosen not in SOCP_MI_CAPABLE_SOLVERS:
        pytest.skip("no MI-capable SOCP solver (need MOSEK, GUROBI, or SCIP)")
    return chosen


def ipopt_available():
    return _pyomo_available() and pyf.is_pyomo_solver_available("ipopt")


def ipopt_missing_for_run_test():
    if not _pyomo_available():
        return False
    return _missing_for_run_test(
        pyf.is_pyomo_solver_available("ipopt"), "ipopt is not installed"
    )


def require_ipopt():
    require_pyomo()
    _require(pyf.is_pyomo_solver_available("ipopt"), "ipopt is not installed")


def _folium_available():
    try:
        __import__("folium")
    except Exception:
        return False
    return True


def folium_missing_for_run_test():
    return _missing_for_run_test(_folium_available(), "folium is not installed")


def require_folium():
    _require(_folium_available(), "folium is not installed")


def _mapping_available():
    return _folium_available() and hasattr(pyf, "plot_folium")


def mapping_missing_for_run_test():
    return _missing_for_run_test(_mapping_available(), _MAPPING_SKIP)


def require_mapping():
    _require(_mapping_available(), _MAPPING_SKIP)


def _pymoo_tep_available():
    try:
        __import__("pymoo")
    except Exception:
        return False
    return hasattr(pyf, "transmission_expansion_pymoo")


def pymoo_tep_missing_for_run_test():
    return _missing_for_run_test(_pymoo_tep_available(), _TEP_PYMOO_SKIP)


def require_tep_pymoo():
    _require(_pymoo_tep_available(), _TEP_PYMOO_SKIP)


def _dash_available():
    try:
        __import__("dash")
    except Exception:
        return False
    return True


def dash_missing_for_run_test():
    return _missing_for_run_test(_dash_available(), "dash is not installed")


def require_dash():
    _require(_dash_available(), "dash is not installed")


def _ortools_available():
    try:
        from ortools.sat.python import cp_model  # noqa: F401
    except Exception:
        return False
    return True


def ortools_missing_for_run_test():
    return _missing_for_run_test(_ortools_available(), "OR-Tools is not installed")


def require_ortools():
    _require(_ortools_available(), "OR-Tools is not installed")


def _first_pyomo_linear_solver():
    from pyflow_acdc.solver_utils import resolve_pyomo_linear_solver
    return resolve_pyomo_linear_solver()


def pyomo_mip_css_solver_available():
    return _pyomo_available() and _first_pyomo_linear_solver() is not None


def require_pyomo_mip_css_solvers():
    require_pyomo()
    _require(_first_pyomo_linear_solver() is not None, _PYOMO_LINEAR_SKIP)


def pyomo_mip_css_solvers_missing_for_run_test():
    if not _pyomo_available():
        return False
    return _missing_for_run_test(
        _first_pyomo_linear_solver() is not None, _PYOMO_LINEAR_SKIP
    )


def _first_ortools_lp_solver():
    try:
        from ortools.linear_solver import pywraplp
    except Exception:
        return None
    for name in ORTOOLS_LINEAR_SOLVERS:
        if pywraplp.Solver.CreateSolver(name) is not None:
            return name
    return None


def ortools_array_stack_available():
    return _ortools_available() and _first_ortools_lp_solver() is not None


def require_ortools_array_stack():
    require_ortools()
    _require(_first_ortools_lp_solver() is not None, _ORTOOLS_LP_SKIP)


def ortools_array_stack_missing_for_run_test():
    if not _ortools_available():
        return False
    return _missing_for_run_test(
        _first_ortools_lp_solver() is not None, _ORTOOLS_LP_SKIP
    )


def tep_solver():
    """TEP solver for tests. Override with ``PYFLOW_TEP_SOLVER`` (e.g. ``bonmin``)."""
    forced = os.environ.get("PYFLOW_TEP_SOLVER", "").strip().lower()
    if forced:
        return forced
    if pyf.is_pyomo_solver_available("ipopt"):
        return "ipopt"
    if pyf.is_pyomo_solver_available("bonmin"):
        return "bonmin"
    return "ipopt"


def mip_solvers():
    """Return ``(MIP_solver, CSS_L_solver)`` for :func:`sequential_CSS`."""
    chosen = _first_pyomo_linear_solver()
    if chosen is None:
        raise RuntimeError(_PYOMO_LINEAR_SKIP)
    preferred = PYOMO_LINEAR_SOLVERS[0]
    if chosen != preferred:
        print(f"{preferred} is not available; falling back to {chosen} for MIP and CSS.")
    return chosen, chosen


def lopf_solver():
    chosen = _first_pyomo_linear_solver()
    if chosen is not None:
        return chosen
    return PYOMO_LINEAR_SOLVERS[-1]
