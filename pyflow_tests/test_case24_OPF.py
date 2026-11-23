import time

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def case24_OPF():
    t1 = time.perf_counter()
    grid, res = pyf.cases['case24_OPF']()
    obj = {'Energy_cost': 1}
    model, model_res, timing_info, solver_stats = pyf.optimal_pf(grid, ObjRule=obj)
    res.all()
    print(model_res)
    print(timing_info)
    model.obj.display()
    t2 = time.perf_counter()
    print(f'Total time :{t2 - t1}')


def test_case24_opf():
    require_pyomo()
    case24_OPF()


def run_test():
    """Test case24 optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    case24_OPF()


if __name__ == "__main__":
    run_test()
