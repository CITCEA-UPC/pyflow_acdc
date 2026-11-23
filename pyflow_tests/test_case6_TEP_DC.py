import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo, tep_solver


def case6_TEP_DC():
    grid, res = pyf.cases['case6_TEP_DC']()
    model, model_results, timing_info, solver_stats = pyf.transmission_expansion(
        grid, NPV=True, solver=tep_solver()
    )
    print(timing_info)


def test_case6_tep_dc():
    require_pyomo()
    case6_TEP_DC()


def run_test():
    """Test case6 DC transmission expansion planning."""
    if pyomo_missing_for_run_test():
        return
    case6_TEP_DC()


if __name__ == "__main__":
    run_test()
