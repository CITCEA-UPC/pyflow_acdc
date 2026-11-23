"""PEI: solve each season window, attach season-compare, open Dash.

Heavy: four 24 h IPOPT windows. Docs CI does not execute this file; it is the
literalinclude for ``docs/usage_window_opf.rst``. Run interactively, or use
``my_tests/pei_window_nl_opf_bess_h2.py --compare-seasons --dash``.
"""

import pyflow_acdc as pyf
from pyflow_acdc.example_grids.PF._pei_bess_data import (
    PEI_OBJ_RULE,
    PEI_SEASONS,
)

if not pyf.is_pyomo_solver_available("ipopt"):
    raise SystemExit(0)

season_results = {}
grid = None
for season in PEI_SEASONS:
    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
        seasons=(season,),
    )
    n_hours = len(grid.Time_series[0].data)
    pyf.window_nl_opf(
        grid,
        start=0,
        end=n_hours - 1,
        ObjRule=PEI_OBJ_RULE,
        solver="ipopt",
    )
    season_results[season] = grid.window_opf_results

pyf.attach_season_window_compare(grid, season_results)
grid.name = "PEI BESS H2"
# Interactive browser: pyf.run_dash(grid)
app = pyf.create_season_compare_dash_app(grid)
assert app.layout is not None
