import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def DC_OPF():
    grid, res = pyf.cases['DC_OPF_simple']()
    obj = {'Energy_cost': 1}
    model, model_res, timing_info, solver_stats = pyf.optimal_pf(grid, ObjRule=obj)
    res.all()
    print(model_res)
    print(timing_info)
    model.obj.display()


def test_dc_opf():
    require_pyomo()
    DC_OPF()


def run_test():
    """Test DC optimal power flow."""
    if pyomo_missing_for_run_test():
        return
    DC_OPF()


if __name__ == "__main__":
    run_test()
