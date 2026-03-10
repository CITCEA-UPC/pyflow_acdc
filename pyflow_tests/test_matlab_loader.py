# -*- coding: utf-8 -*-

import pyflow_acdc as pyf
from pathlib import Path
import tempfile


def matlab_loader(output_dir):

    current_file = Path(__file__).resolve()
    path = str(current_file.parent)

    data = f'{path}/case39_acdc_var.mat'

    [grid,res]=pyf.Create_grid_from_mat(data)

    pyf.save_grid_to_file(grid, "case39", folder_name=str(output_dir))


    obj = {'Energy_cost'  : 1}
    nac=grid.nn_AC

    print(nac)

        
    model, model_res,timing_info, solver_stats = pyf.Optimal_PF(grid,ObjRule=obj)

    res.All()

    print(timing_info)
    print(model_res)
    model.obj.display()


def run_test(output_dir=None):
    """Test MATLAB file loading functionality."""
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return

    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="pyflow_matlab_loader_") as tmpdir:
            matlab_loader(tmpdir)
    else:
        matlab_loader(output_dir)


def test_matlab_loader(tmp_path):
    """Pytest entrypoint for MATLAB loader test."""
    run_test(output_dir=tmp_path)


if __name__ == "__main__":
    run_test()
