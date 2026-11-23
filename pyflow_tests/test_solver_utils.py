"""Unit tests for pyflow_acdc.solver_utils (mocked solvers; no binaries required)."""

import builtins
import sys

import pytest

import pyflow_acdc.solver_utils as su


class _MockPyomoSolver:
    def __init__(self, available):
        self._available = available

    def available(self, quiet=False):
        return self._available


def _patch_pyomo_solver_factory(monkeypatch, factory_fn):
    import pyomo.environ as pyo

    monkeypatch.setattr(pyo, "SolverFactory", factory_fn)


def test_check_pyomo_solvers_normalizes_maingo_alias(monkeypatch):
    seen = []

    def factory(name):
        seen.append(name)
        return _MockPyomoSolver(True)

    _patch_pyomo_solver_factory(monkeypatch, factory)
    result = su.check_pyomo_solvers(["maingo"], verbose=False)

    assert seen == ["appsi_maingo"]
    assert "appsi_maingo" in result["pyomo_available"]


def test_check_pyomo_solvers_available_unavailable_and_error(monkeypatch):
    def factory(name):
        if name == "ipopt":
            return _MockPyomoSolver(True)
        if name == "glpk":
            return _MockPyomoSolver(False)
        raise RuntimeError(f"no factory for {name}")

    _patch_pyomo_solver_factory(monkeypatch, factory)
    result = su.check_pyomo_solvers(["ipopt", "glpk", "broken"], verbose=False)

    assert result["pyomo_available"] == ["ipopt"]
    assert "glpk" in result["pyomo_errors"]
    assert "broken" in result["pyomo_errors"]


def test_check_pyomo_solvers_pyomo_import_error(monkeypatch):
    real_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pyomo.environ" or (name == "pyomo" and "environ" in fromlist):
            raise ImportError("no pyomo")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    result = su.check_pyomo_solvers(["ipopt"], verbose=False)

    assert result["pyomo_available"] == []
    assert "pyomo" in result["pyomo_errors"]
    assert "pyomo_import" in result["pyomo_errors"]


def test_check_pyomo_solvers_verbose_prints(capsys, monkeypatch):
    _patch_pyomo_solver_factory(monkeypatch, lambda name: _MockPyomoSolver(True))
    su.check_pyomo_solvers(["ipopt"], verbose=True)
    out = capsys.readouterr().out
    assert "checking pyomo solvers" in out
    assert "checking ipopt" in out


def test_is_pyomo_solver_available(monkeypatch):
    _patch_pyomo_solver_factory(monkeypatch, lambda name: _MockPyomoSolver(name == "ipopt"))
    assert su.is_pyomo_solver_available("ipopt") is True
    assert su.is_pyomo_solver_available("glpk") is False


def test_check_ortools_backends_import_error(monkeypatch):
    real_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("ortools"):
            raise ImportError("no ortools")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    result = su.check_ortools_backends(verbose=False)

    assert result["ortools_installed"] is False
    assert result["ortools_available"] == []
    assert result["ortools_error"] is None


def test_check_ortools_backends_create_solver(monkeypatch):
    class _FakeSolver:
        pass

    class _FakeSolverFactory:
        @staticmethod
        def CreateSolver(backend):
            if backend == "GLOP":
                return _FakeSolver()
            return None

    class _FakePywraplp:
        Solver = _FakeSolverFactory

    fake_linear = type(sys)("ortools.linear_solver")
    fake_linear.pywraplp = _FakePywraplp
    monkeypatch.setitem(sys.modules, "ortools.linear_solver", fake_linear)

    result = su.check_ortools_backends(verbose=False)
    assert result["ortools_installed"] is True
    assert "GLOP" in result["ortools_available"]


def test_check_available_solvers_without_ortools(monkeypatch):
    _patch_pyomo_solver_factory(monkeypatch, lambda name: _MockPyomoSolver(True))
    result = su.check_available_solvers(pyomo_solvers=["ipopt"], include_ortools=False, verbose=False)

    assert "ipopt" in result["pyomo_available"]
    assert result["ortools_installed"] is None
    assert result["ortools_available"] == []


def test_format_solver_report_includes_sections(monkeypatch):
    _patch_pyomo_solver_factory(monkeypatch, lambda name: _MockPyomoSolver(name == "appsi_maingo"))

    class _FakeSolver:
        pass

    class _FakeSolverFactory:
        @staticmethod
        def CreateSolver(backend):
            return _FakeSolver() if backend == "GLOP" else None

    class _FakePywraplp:
        Solver = _FakeSolverFactory

    fake_linear = type(sys)("ortools.linear_solver")
    fake_linear.pywraplp = _FakePywraplp
    monkeypatch.setitem(sys.modules, "ortools.linear_solver", fake_linear)

    result = su.check_available_solvers(pyomo_solvers=["appsi_maingo"], verbose=False)
    report = su._format_solver_report(result)

    assert "pyflow-acdc solver availability" in report.lower()
    assert "MAiNGO note" in report
    assert "appsi_maingo" in report
    assert "OR-Tools installed: Yes" in report
    assert "GLOP" in report


def run_test():
    pytest.main([__file__, "-q"])


if __name__ == "__main__":
    run_test()
