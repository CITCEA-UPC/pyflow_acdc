"""Parser tests for :mod:`pyflow_acdc.pyomo_model_solve` using committed log fixtures."""

from pathlib import Path

import pytest

from pyflow_acdc.pyomo_model_solve import (
    _parse_bonmin_log,
    _parse_highs_log,
    _parse_ipopt_log,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "solver_logs"


@pytest.mark.parametrize(
    "fixture_name,parser,kwargs,expect_feasible,expect_all,expect_bounds",
    [
        (
            "ipopt_optimal.log",
            _parse_ipopt_log,
            {},
            1,
            None,
            None,
        ),
        (
            "highs_mip_sample.log",
            _parse_highs_log,
            {},
            1,
            2,
            2,
        ),
        (
            "bonmin_bb_sample.log",
            _parse_bonmin_log,
            {"bonmin_algorithm": "B-BB"},
            1,
            2,
            None,
        ),
        (
            "bonmin_hyb_sample.log",
            _parse_bonmin_log,
            {"bonmin_algorithm": "B-Hyb"},
            1,
            2,
            None,
        ),
    ],
)
def test_parse_solver_log_fixture(
    fixture_name, parser, kwargs, expect_feasible, expect_all, expect_bounds
):
    log_path = FIXTURES / fixture_name
    assert log_path.is_file(), f"Missing fixture: {log_path}"
    result = parser(str(log_path), **kwargs)
    if parser is _parse_ipopt_log:
        events = result
        assert len(events) >= expect_feasible
        assert events[-1][2] is True
        return
    feasible, all_solutions, bound_solutions = result
    assert len(feasible) >= expect_feasible
    if expect_all is not None:
        assert len(all_solutions) >= expect_all
    if expect_bounds is not None:
        assert len(bound_solutions) >= expect_bounds


def test_parse_bonmin_log_missing_file_returns_empty():
    feasible, all_solutions, bound_solutions = _parse_bonmin_log(
        str(FIXTURES / "does_not_exist.log")
    )
    assert feasible == []
    assert all_solutions == []
    assert bound_solutions == []


def test_parse_ipopt_log_missing_file_returns_empty():
    assert _parse_ipopt_log(str(FIXTURES / "does_not_exist.log")) == []


def test_parse_highs_log_missing_file_returns_empty():
    feasible, all_solutions, bound_solutions = _parse_highs_log(
        str(FIXTURES / "does_not_exist.log")
    )
    assert feasible == []
    assert all_solutions == []
    assert bound_solutions == []


def test_parse_ipopt_log_acceptable_exit_and_restoration(tmp_path):
    log_path = tmp_path / "ipopt.log"
    log_path.write_text(
        "   0  1.0000000e+03 1.00e+00 1.00e+00  -1.0 1.00e+00    -  1.00e+00 1.00e+00   0\n"
        "  10r 9.5000000e+02 1.00e-02 1.00e-02  -3.0 1.00e-01    -  1.00e+00 1.00e+00   1\n"
        "  12  9.0000000e+02 1.00e-05 1.00e-05  -5.0 1.00e-02    -  1.00e+00 1.00e+00   1\n"
        "EXIT: Solved To Acceptable Level\n",
        encoding="utf-8",
    )
    events = _parse_ipopt_log(str(log_path))
    assert len(events) == 3
    assert events[0][2] is False
    assert events[1][2] is False  # restoration-phase iterate
    assert events[-1][2] is True


def test_parse_bonmin_log_cbc0005_partial_search():
    """Uses committed OA-run log only for the Cbc0005I partial-search line shape."""
    log_path = FIXTURES / "bonmin_oa_sample.log"
    assert log_path.is_file(), f"Missing fixture: {log_path}"
    feasible, all_solutions, bound_solutions = _parse_bonmin_log(
        str(log_path),
        bonmin_algorithm="B-BB",
    )
    partial = [row for row in all_solutions if row[4] is False and row[1] == 1e50]
    assert partial
    assert partial[0][0] == 300.73
    assert partial[0][2] == 5104


def test_parse_bonmin_hyb_cbc0010_incumbent(tmp_path):
    log_path = tmp_path / "bonmin.log"
    log_path.write_text(
        "Cbc0010I After 120 nodes, 1.50e+10 best solution, best possible 1.40e+10 (12.34 seconds)\n",
        encoding="utf-8",
    )
    feasible, all_solutions, bound_solutions = _parse_bonmin_log(
        str(log_path),
        bonmin_algorithm="B-Hyb",
    )
    assert len(all_solutions) == 1
    assert all_solutions[0][4] is True
    assert feasible == [(12.34, 1.50e10, 120)]
    assert bound_solutions == [(12.34, 1.40e10, 120)]


def test_parse_bonmin_log_nlp_star_format(tmp_path):
    log_path = tmp_path / "bonmin.log"
    log_path.write_text(
        "NLP0012I\n"
        "NLP0014I * 1 OPT 1.5954776e+10       25 0.045817\n",
        encoding="utf-8",
    )
    feasible, all_solutions, bound_solutions = _parse_bonmin_log(
        str(log_path),
        bonmin_algorithm="B-BB",
    )
    assert feasible == []
    assert len(all_solutions) == 1
    assert all_solutions[0][1] == 1.5954776e10
    assert all_solutions[0][3] == 1
    assert bound_solutions == []


def run_test():
    pytest.main([__file__, "-q"])


if __name__ == "__main__":
    run_test()
