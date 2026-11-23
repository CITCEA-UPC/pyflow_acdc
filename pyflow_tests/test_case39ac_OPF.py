import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def case39ac_OPF():
    grid, res = pyf.cases['case39']()
    obj = {'Energy_cost': 1}
    pyf.optimal_pf(grid, ObjRule=obj)
    res.all()


def test_case39ac_opf():
    require_pyomo()
    case39ac_OPF()


def run_test():
    """Test case39 AC optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    case39ac_OPF()


if __name__ == "__main__":
    run_test()
