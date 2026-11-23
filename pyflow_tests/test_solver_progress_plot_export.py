"""Plot/export smoke tests for solver progress using committed stats fixtures.

Parser coverage lives in :mod:`pyflow_tests.test_pyomo_model_solve`.
HiGHS is live-tested in CI (no log fixture). Gurobi has no log parser.
"""

from pathlib import Path

import pandas as pd
import pytest

from pyflow_acdc.Graph_and_plot import plot_model_feasibility
from pyflow_acdc.pyomo_model_solve import export_solver_progress_to_excel
from pyflow_tests._solver_stats_fixtures import (
    STATS_JSON_FIXTURES,
    load_solver_stats_fixture,
    solver_stats_from_log,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "solver_logs"


@pytest.mark.parametrize("stats_name", STATS_JSON_FIXTURES)
def test_solver_stats_json_matches_log(stats_name):
    log_name = stats_name.replace(".stats.json", ".log")
    log_path = FIXTURES / log_name
    assert log_path.is_file(), f"Missing log fixture: {log_path}"

    from pyflow_tests._solver_stats_fixtures import LOG_TO_STATS

    solver, kwargs = LOG_TO_STATS[log_name]
    built = solver_stats_from_log(log_path, solver, **kwargs)
    loaded = load_solver_stats_fixture(stats_name)

    assert loaded["solver"] == built["solver"]
    assert loaded["feasible_solutions"] == built["feasible_solutions"]
    assert loaded["all_solutions"] == built["all_solutions"]
    assert loaded["bound_solutions"] == built["bound_solutions"]


def test_plot_model_feasibility_ipopt_all_and_feasible(tmp_path):
    stats = load_solver_stats_fixture("ipopt_optimal.stats.json")
    assert stats["all_solutions"]

    all_png = tmp_path / "ipopt_all.png"
    plot_model_feasibility(
        stats,
        sol="all",
        show=False,
        save_path=str(all_png),
    )
    assert all_png.is_file() and all_png.stat().st_size > 0

    norm_png = tmp_path / "ipopt_all_norm.png"
    plot_model_feasibility(
        stats,
        sol="all",
        normalize=True,
        show=False,
        save_path=str(norm_png),
    )
    assert norm_png.is_file() and norm_png.stat().st_size > 0

    feas_png = tmp_path / "ipopt_feasible.png"
    plot_model_feasibility(
        stats,
        sol="feasible",
        show=False,
        save_path=str(feas_png),
    )
    assert feas_png.is_file() and feas_png.stat().st_size > 0


def test_export_solver_progress_ipopt_kkt_columns(tmp_path):
    stats = load_solver_stats_fixture("ipopt_optimal.stats.json")
    xlsx = export_solver_progress_to_excel(stats, str(tmp_path / "ipopt_progress"))
    df = pd.read_excel(xlsx)

    assert "inf_pr_all" in df.columns
    assert "inf_du_all" in df.columns
    assert "kkt_inf_du_feasible" in df.columns
    assert df["inf_pr_all"].notna().any()
    assert df["kkt_inf_du_feasible"].notna().any()


def test_export_solver_progress_bonmin_mip_columns(tmp_path):
    stats = load_solver_stats_fixture("bonmin_bb_sample.stats.json")
    xlsx = export_solver_progress_to_excel(stats, str(tmp_path / "bonmin_progress"))
    df = pd.read_excel(xlsx)

    assert df["time_feasible"].notna().any()
    assert df["obj_feasible"].notna().any()
    assert df["is_feasible_all"].notna().any()


def run_test():
    pytest.main([__file__, "-q"])


if __name__ == "__main__":
    run_test()
