import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import lopf_solver, pyomo_missing_for_run_test, require_pyomo


def case39ac_LOPF():
    grid, res = pyf.cases['case39']()
    obj = {'Energy_cost': 1}
    model, model_res, timing_info, solver_stats = pyf.optimal_l_pf(
        grid, ObjRule=obj, solver=lopf_solver()
    )
    res.all()
    model.obj.display()
    model.obj.pprint()


def test_case39ac_lopf():
    require_pyomo()
    case39ac_LOPF()


def run_test():
    """Test case39 AC linear optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    case39ac_LOPF()


if __name__ == "__main__":
    run_test()
