import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import (
    folium_missing_for_run_test,
    pyomo_missing_for_run_test,
    require_folium,
    require_pyomo,
)


def folium_test():
    grid, res = pyf.cases['NS_MTDC']()
    pyf.optimal_pf(grid)
    pyf.plot_folium(grid)
    print('folium test completed')


@pytest.mark.integration
def test_folium():
    require_pyomo()
    require_folium()
    folium_test()


def run_test():
    """Test folium mapping functionality."""
    if pyomo_missing_for_run_test():
        return
    if folium_missing_for_run_test():
        return
    folium_test()


if __name__ == "__main__":
    run_test()
