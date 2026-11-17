# -*- coding: utf-8 -*-

import pyflow_acdc as pyf
from pathlib import Path
import tempfile

from pyflow_tests._test_solver_deps import pyomo_missing_for_run_test, require_pyomo


def matlab_loader(output_dir):

    current_file = Path(__file__).resolve()
    path = str(current_file.parent)

    data = f'{path}/case39_acdc_var.mat'

    [grid,res]=pyf.create_grid_from_mat(data)

    pyf.save_grid_to_file(grid, "case39", folder_name=str(output_dir))


    obj = {'Energy_cost'  : 1}
    nac=grid.nn_AC

    print(nac)


    model, model_res,timing_info, solver_stats = pyf.optimal_pf(grid,ObjRule=obj)

    res.all()

    print(timing_info)
    print(model_res)
    model.obj.display()


def run_test(output_dir=None):
    """Test MATLAB file loading functionality."""
    if pyomo_missing_for_run_test():
        return

    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="pyflow_matlab_loader_") as tmpdir:
            matlab_loader(tmpdir)
    else:
        matlab_loader(output_dir)


def test_case6_acdc_tnep_var_mat_loads():
    """``case6_acdc_tnep_var.mat`` loads ``ne_branch`` expandable AC lines via :func:`create_grid_from_mat`."""
    mat = Path(__file__).resolve().parent / 'case6_acdc_tnep_var.mat'
    grid, _res = pyf.create_grid_from_mat(str(mat))
    assert grid.nn_AC == 6
    assert grid.nn_DC == 6
    assert len(grid.lines_AC) == 6
    assert len(grid.lines_AC_exp) == 1
    line = grid.lines_AC_exp[0]
    assert line.name == '5_6_100.0'
    assert line.base_cost == 2.0
    assert line.np_line == 0
    assert line.np_line_b == 0
    assert line.np_line_max == 3
    assert len(grid.lines_DC) == 6
    assert all(l.np_line_opf for l in grid.lines_DC)
    assert len(grid.Converters_ACDC) == 6
    assert all(c.np_conv_opf for c in grid.Converters_ACDC)


def test_matlab_loader(tmp_path):
    """Pytest entrypoint for MATLAB loader test."""
    require_pyomo()
    matlab_loader(tmp_path)


if __name__ == "__main__":
    run_test()
