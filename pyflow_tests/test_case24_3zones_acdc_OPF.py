import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def case24_3zones_acdc_OPF():
    grid, res = pyf.cases['case24_3zones_acdc']()
    pyf.optimal_pf(grid)
    res.all()


def test_case24_3zones_acdc_opf():
    require_pyomo()
    case24_3zones_acdc_OPF()


def run_test():
    """Test case24 3-zones AC/DC optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    case24_3zones_acdc_OPF()


if __name__ == "__main__":
    run_test()
