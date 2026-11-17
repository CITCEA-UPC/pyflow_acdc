"""Probe installed Pyomo solvers, CVXPY solvers, and OR-Tools backends."""

import logging
import warnings

DEFAULT_PYOMO_SOLVERS = [
    "cbc",
    "glpk",
    "highs",
    "appsi_highs",
    "gurobi",
    "cplex",
    "scip",
    "ipopt",
    "bonmin",
    "appsi_maingo",
]

DEFAULT_ORTOOLS_BACKENDS = [
    "GLOP",
    "CP_SAT",
    "SAT",
    "BOP",
    "CBC",
    "CLP",
    "SCIP",
    "GUROBI",
    "CPLEX",
    "XPRESS",
    "GLPK",
]

DEFAULT_SOCP_SOLVERS = [
    "MOSEK",
    "GUROBI",
    "SCIP",
    "CLARABEL",
    "SCS",
]

# Subset of ``DEFAULT_SOCP_SOLVERS`` that support SOCP + boolean variables.
SOCP_MI_CAPABLE_SOLVERS = frozenset({"MOSEK", "GUROBI", "SCIP"})


def _normalize_solver_names(pyomo_solvers=None):
    alias_map = {"maingo": "appsi_maingo"}
    requested = pyomo_solvers if pyomo_solvers is not None else DEFAULT_PYOMO_SOLVERS
    normalized = []
    seen = set()

    for solver_name in requested:
        name = str(solver_name).strip().lower()
        name = alias_map.get(name, name)
        if name and name not in seen:
            normalized.append(name)
            seen.add(name)
    return normalized


def check_pyomo_solvers(pyomo_solvers=None, verbose=True):
    """
    Check availability of Pyomo solvers.
    """
    solvers_to_check = _normalize_solver_names(pyomo_solvers)
    pyomo_available = []
    pyomo_errors = {}

    if verbose:
        print("")
        print("=== checking pyomo solvers ===")
        print("")

    try:
        import pyomo.environ as pyo
    except ImportError as exc:
        pyomo_errors["pyomo"] = (
            "Pyomo is not installed. Install pyflow_acdc[OPF] or install pyomo directly."
        )
        pyomo_errors["pyomo_import"] = str(exc)
        return {
            "pyomo_available": pyomo_available,
            "pyomo_errors": pyomo_errors,
        }

    for solver in solvers_to_check:
        if verbose:
            print(f"checking {solver}")
        try:
            if not verbose:
                pyomo_opt_logger = logging.getLogger("pyomo.opt")
                previous_level = pyomo_opt_logger.level
                pyomo_opt_logger.setLevel(logging.ERROR)
            else:
                previous_level = None
            try:
                available = pyo.SolverFactory(solver).available(False)
            finally:
                if previous_level is not None:
                    pyomo_opt_logger.setLevel(previous_level)
            if available:
                pyomo_available.append(solver)
            else:
                pyomo_errors[solver] = f"Solver ({solver}) not available"
        except Exception as exc:
            pyomo_errors[solver] = str(exc)

    return {
        "pyomo_available": pyomo_available,
        "pyomo_errors": pyomo_errors,
    }


def is_pyomo_solver_available(solver_name):
    """Return ``True`` if a Pyomo solver is installed and available.

    Uses ``SolverFactory(...).available(False)`` so missing executables are
    detected without raising (unlike ``available()`` with no argument).
    """
    name = _normalize_solver_names([solver_name])[0]
    result = check_pyomo_solvers([name], verbose=False)
    return name in result["pyomo_available"]


def pyomo_solver_factory_name(solver_name):
    """Return the Pyomo ``SolverFactory`` name (after alias normalization)."""
    return _normalize_solver_names([solver_name])[0]


def resolve_pyomo_linear_solver(candidates=None):
    """First available MIP/CSS-L Pyomo solver from ``candidates``."""
    if candidates is None:
        from .constants import PYOMO_LINEAR_SOLVERS
        candidates = PYOMO_LINEAR_SOLVERS
    for name in candidates:
        if is_pyomo_solver_available(name):
            return name
    return None


def cvxpy_available():
    """Return ``True`` when CVXPY can be imported."""
    try:
        __import__("cvxpy")
    except Exception:
        return False
    return True


def resolve_socp_solver(candidates=None, mi_required=False, solver=None):
    """Return a CVXPY SOCP solver name (upper-case).

    If ``solver`` is given, return its upper-case form. Otherwise return the
    first installed solver from ``candidates`` (default
    :data:`DEFAULT_SOCP_SOLVERS`).

    When ``mi_required`` is True, prefer the first installed solver in
    :data:`SOCP_MI_CAPABLE_SOLVERS`. If none are installed, fall back to the
    first installed solver from the full list and emit a warning. An explicit
    non-MI ``solver`` with ``mi_required=True`` also emits a warning.
    """
    if not cvxpy_available():
        return None

    if solver is not None:
        chosen = str(solver).upper()
        if mi_required and chosen not in SOCP_MI_CAPABLE_SOLVERS:
            warnings.warn(
                f"solver {chosen!r} may not support SOCP with boolean variables; "
                f"bess_mi_exclusivity=True prefers "
                f"{', '.join(sorted(SOCP_MI_CAPABLE_SOLVERS))}.",
                stacklevel=2,
            )
        return chosen

    import cvxpy as cp

    candidate_names = candidates if candidates is not None else DEFAULT_SOCP_SOLVERS
    installed = set(cp.installed_solvers())
    if mi_required:
        for name in candidate_names:
            if name in installed and name in SOCP_MI_CAPABLE_SOLVERS:
                return name
    for name in candidate_names:
        if name in installed:
            if mi_required and name not in SOCP_MI_CAPABLE_SOLVERS:
                warnings.warn(
                    f"solver {name!r} may not support SOCP with boolean variables; "
                    f"bess_mi_exclusivity=True prefers "
                    f"{', '.join(sorted(SOCP_MI_CAPABLE_SOLVERS))}.",
                    stacklevel=2,
                )
            return name
    return None


def check_ortools_backends(verbose=True):
    """
    Check availability of OR-Tools linear solver backends.
    """
    if verbose:
        print("")
        print("=== checking ortools backends ===")
        print("")

    try:
        from ortools.linear_solver import pywraplp
    except ImportError:
        return {
            "ortools_installed": False,
            "ortools_available": [],
            "ortools_error": None,
        }
    except Exception as exc:
        return {
            "ortools_installed": False,
            "ortools_available": [],
            "ortools_error": str(exc),
        }

    ortools_available = []
    ortools_error = None

    for backend in DEFAULT_ORTOOLS_BACKENDS:
        if verbose:
            print(f"checking {backend}")
        try:
            solver = pywraplp.Solver.CreateSolver(backend)
            if solver is not None:
                ortools_available.append(backend)
        except Exception as exc:
            if ortools_error is None:
                ortools_error = str(exc)

    return {
        "ortools_installed": True,
        "ortools_available": ortools_available,
        "ortools_error": ortools_error,
    }


def check_available_solvers(pyomo_solvers=None, include_ortools=True, verbose=True):
    """Report which Pyomo solvers and OR-Tools backends are installed and available.

    Parameters
    ----------
    pyomo_solvers : list of str, optional
        Solver names to probe; defaults to a built-in list (cbc, glpk, ipopt,
        bonmin, gurobi, …).
    include_ortools : bool, optional
        When ``True``, also report OR-Tools LP/MIP backend availability.
    verbose : bool, optional
        Print a human-readable report to stdout.

    Returns
    -------
    dict
        Keys include ``pyomo_available``, ``pyomo_errors``, and (when
        ``include_ortools``) ``ortools_installed``, ``ortools_available``.
    """
    result = {}

    pyomo_result = check_pyomo_solvers(pyomo_solvers=pyomo_solvers, verbose=verbose)
    result.update(pyomo_result)

    if include_ortools:
        ortools_result = check_ortools_backends(verbose=verbose)
        result.update(ortools_result)
    else:
        result.update(
            {
                "ortools_installed": None,
                "ortools_available": [],
                "ortools_error": None,
            }
        )

    return result


def _format_solver_report(result):
    pyomo_available = result["pyomo_available"]
    pyomo_errors = result["pyomo_errors"]
    ortools_installed = result["ortools_installed"]
    ortools_available = result["ortools_available"]
    ortools_error = result["ortools_error"]

    lines = []
    lines.append("=== pyflow-acdc solver availability ===")
    if "appsi_maingo" in pyomo_available:
        lines.append("MAiNGO note: available via 'appsi_maingo' (alias from 'maingo').")
        lines.append("")

    lines.append("Pyomo available solvers:")
    if pyomo_available:
        lines.extend([f"  - {name}" for name in pyomo_available])
    else:
        lines.append("  <none>")

    if pyomo_errors:
        lines.append("")
        lines.append("Pyomo check errors:")
        for name in sorted(pyomo_errors):
            lines.append(f"  - {name}: {pyomo_errors[name]}")

    lines.append("")
    if ortools_installed is True:
        lines.append("OR-Tools installed: Yes")
        lines.append("OR-Tools backends:")
        if ortools_available:
            lines.extend([f"  - {name}" for name in ortools_available])
        else:
            lines.append("  <none>")
    elif ortools_installed is False:
        lines.append("OR-Tools installed: No")
    else:
        lines.append("OR-Tools installed: Unknown")

    if ortools_error:
        lines.append(f"OR-Tools error: {ortools_error}")

    return "\n".join(lines)


def cli_check_solvers():
    result = check_available_solvers(verbose=True)
    print("")
    print(_format_solver_report(result))


if __name__ == "__main__":
    cli_check_solvers()
