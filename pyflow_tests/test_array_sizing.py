import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo, tep_solver


def array_sizing(combinations):
    WACC = 0.06
    FLH = 4500
    solver = tep_solver()

    for combo in combinations:
        print(f'Starting analysis with opt_type={combo["opt_type"]}, Nc={combo["Nc"]}')
        print('--------------------------------------------------------------')
        opt_type = combo['opt_type']
        Nc = combo['Nc']

        if opt_type == 'W' or opt_type == 'FLH':
            gamma_limit = 0.9
        elif opt_type == 'OPF':
            gamma_limit = 0
        else:
            gamma_limit = 1

        grid, res = pyf.cases['array_sizing_pei'](gamma_limit=gamma_limit)

        obj = {'Energy_cost': 1}
        grid.cab_types_allowed = Nc

        if opt_type == 'OPF':
            model, timing_info, model_res, solver_stats = pyf.optimal_pf(grid, ObjRule=obj)
            res.all()
            res.tep_n()
            res.obj_res()
        elif opt_type == 'FLH':
            model, model_results, timing_info, solver_stats = pyf.transmission_expansion(
                grid, NPV=True, Hy=FLH, discount_rate=WACC, ObjRule=obj, tee=True, solver=solver
            )
            res.tep_n()
            res.tep_norm()
            model.obj.display()
        else:
            model, model_results, timing_info, solver_stats = pyf.transmission_expansion(
                grid, NPV=True, discount_rate=WACC, solver=solver
            )
            res.all()

        print(timing_info)


@pytest.mark.slow
def test_array_sizing():
    require_pyomo()
    combinations = [
        {'opt_type': 'FLH', 'Nc': 1},
        {'opt_type': 'FLH', 'Nc': 2},
        {'opt_type': 'FLH', 'Nc': 3},
        {'opt_type': 'FLH', 'Nc': 4},
    ]
    array_sizing(combinations)


def run_test():
    """Test array sizing functionality."""
    if pyomo_missing_for_run_test():
        return
    test_array_sizing()


if __name__ == "__main__":
    run_test()
