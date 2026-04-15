"""
Solver availability helper functions.
"""

DEFAULT_PYOMO_SOLVERS = [
    "cbc",
    "glpk",
    "highs",
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
            if pyo.SolverFactory(solver).available(False):
                pyomo_available.append(solver)
            else:
                pyomo_errors[solver] = f"Solver ({solver}) not available"
        except Exception as exc:
            pyomo_errors[solver] = str(exc)

    return {
        "pyomo_available": pyomo_available,
        "pyomo_errors": pyomo_errors,
    }


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
    """
    Orchestrate solver/backend checks for Pyomo and OR-Tools.
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
    lines.append("=== PyFlow-ACDC Solver Availability ===")
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
