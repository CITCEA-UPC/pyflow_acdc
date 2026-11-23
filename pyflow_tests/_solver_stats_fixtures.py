"""Build and load committed ``solver_stats`` JSON fixtures from solver log parsers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyflow_acdc.pyomo_model_solve import (
    _parse_bonmin_log,
    _parse_highs_log,
    _parse_ipopt_log,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "solver_logs"

LOG_TO_STATS: dict[str, tuple[str, dict[str, Any]]] = {
    "ipopt_optimal.log": ("ipopt", {}),
    "bonmin_bb_sample.log": ("bonmin", {"bonmin_algorithm": "B-BB"}),
    "bonmin_hyb_sample.log": ("bonmin", {"bonmin_algorithm": "B-Hyb"}),
    "highs_mip_sample.log": ("highs", {}),
}

# Logs with committed JSON used by plot/export tests (parser-only coverage stays elsewhere).
STATS_JSON_FIXTURES = (
    "ipopt_optimal.stats.json",
    "bonmin_bb_sample.stats.json",
)


def stats_json_path_for_log(log_name: str) -> Path:
    return FIXTURES_DIR / log_name.replace(".log", ".stats.json")


def _stats_to_jsonable(stats: dict) -> dict:
    out: dict[str, Any] = {"solver": stats["solver"]}
    for key in ("feasible_solutions", "all_solutions", "bound_solutions"):
        seq = stats.get(key, []) or []
        out[key] = [list(item) if not isinstance(item, list) else item for item in seq]
    return out


def _stats_from_jsonable(data: dict) -> dict:
    return {
        "solver": data.get("solver"),
        "feasible_solutions": [tuple(x) for x in data.get("feasible_solutions", [])],
        "all_solutions": [list(x) for x in data.get("all_solutions", [])],
        "bound_solutions": [tuple(x) for x in data.get("bound_solutions", [])],
    }


def solver_stats_from_log(log_path, solver: str, *, bonmin_algorithm: str = "B-BB") -> dict:
    """Mirror :func:`pyflow_acdc.pyomo_model_solve._solver_progress` post-parse assembly."""
    log_path = str(log_path)
    solver = solver.lower()
    feasible_solutions: list[tuple] = []
    all_solutions: list = []
    bound_solutions: list[tuple] = []

    if solver == "ipopt":
        for iter_num, obj, is_feasible, inf_pr, inf_du in _parse_ipopt_log(log_path):
            if is_feasible:
                feasible_solutions.append((iter_num, obj, iter_num))
            all_solutions.append(
                [iter_num, obj, iter_num, iter_num, is_feasible, inf_pr, inf_du]
            )
    elif solver == "bonmin":
        feasible_solutions, all_solutions, bound_solutions = _parse_bonmin_log(
            log_path,
            bonmin_algorithm=bonmin_algorithm,
        )
    elif solver == "highs":
        feasible_solutions, all_solutions, bound_solutions = _parse_highs_log(log_path)
    else:
        raise ValueError(f"Unsupported solver for log parsing: {solver}")

    return {
        "solver": solver,
        "feasible_solutions": feasible_solutions,
        "all_solutions": all_solutions,
        "bound_solutions": bound_solutions,
    }


def write_solver_stats_json(log_path: Path, solver: str, **kwargs) -> Path:
    stats = solver_stats_from_log(log_path, solver, **kwargs)
    out = stats_json_path_for_log(log_path.name)
    out.write_text(
        json.dumps(_stats_to_jsonable(stats), indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def refresh_solver_stats_json_for_log(log_name: str) -> Path | None:
    if log_name not in LOG_TO_STATS:
        return None
    log_path = FIXTURES_DIR / log_name
    if not log_path.is_file():
        raise FileNotFoundError(log_path)
    solver, kwargs = LOG_TO_STATS[log_name]
    return write_solver_stats_json(log_path, solver, **kwargs)


def load_solver_stats_fixture(name: str) -> dict:
    """Load committed ``*.stats.json`` or build from the paired ``*.log`` fixture."""
    if name.endswith(".stats.json"):
        json_path = FIXTURES_DIR / name
        log_name = name.replace(".stats.json", ".log")
    else:
        log_name = name if name.endswith(".log") else f"{name}.log"
        json_path = stats_json_path_for_log(log_name)

    if json_path.is_file():
        return _stats_from_jsonable(json.loads(json_path.read_text(encoding="utf-8")))

    if log_name not in LOG_TO_STATS:
        raise FileNotFoundError(f"No solver_stats fixture for {name}")

    log_path = FIXTURES_DIR / log_name
    if not log_path.is_file():
        raise FileNotFoundError(log_path)

    solver, kwargs = LOG_TO_STATS[log_name]
    return solver_stats_from_log(log_path, solver, **kwargs)
