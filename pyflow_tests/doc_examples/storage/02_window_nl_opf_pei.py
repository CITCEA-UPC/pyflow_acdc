"""PEI 24 h coupled window NL OPF with BESS and electrolyser (build-only)."""

import pyflow_acdc as pyf

grid, _ = pyf.cases["PEI_grid"](
    include_countries=["GB", "DK"],
    storage=True,
    hydrogen=True,
    data="season_comparison",
)
n_hours = len(grid.Time_series[0].data)
pyf.window_nl_opf(
    grid,
    start=0,
    end=n_hours - 1,
    ObjRule={"Energy_cost": 1},
    build_only=True,
)
