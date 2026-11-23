import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def case39acdc_OPF():
    grid, res = pyf.cases['case39_acdc']()
    model, model_res, timing_info, solver_stats = pyf.optimal_pf(
        grid, ObjRule={'Energy_cost': 1}
    )
    res.all()
    model.display()
    model.obj.display()
    model.obj.pprint()
    print(timing_info)


def test_case39acdc_opf():
    require_pyomo()
    case39acdc_OPF()


def run_test():
    """Test case39 AC/DC optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    case39acdc_OPF()


if __name__ == "__main__":
    run_test()
