"""
CIGRE B4 OPF test. Grid from ``pyf.cases['CigreB4_ACDC']()``.
"""
import time

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def CigreB4_OPF():
    start_time = time.perf_counter()

    grid, res = pyf.cases['CigreB4_ACDC']()
    model, timing_info, model_res, solver_stats = pyf.optimal_pf(grid)

    res.all()
    print(model_res)
    print(timing_info)
    model.obj.display()

    elapsed_time = time.perf_counter() - start_time
    print('------')
    print(f'Time elapsed : {elapsed_time}')


def test_cigreb4_opf():
    require_pyomo()
    CigreB4_OPF()


def run_test():
    """Test CIGRE B4 optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    CigreB4_OPF()


if __name__ == "__main__":
    run_test()
