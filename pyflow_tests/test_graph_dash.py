"""Graph_Dash unit tests with synthetic time-series results (no OPF solve, no server)."""

import pandas as pd
import plotly.graph_objects as go
import pytest

import pyflow_acdc as pyf
from pyflow_tests._test_solver_deps import dash_missing_for_run_test, require_dash


def _dash_installed():
    try:
        __import__("dash")
    except ImportError:
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _dash_installed(),
    reason="dash is not installed",
)

if _dash_installed():
    from pyflow_acdc.Graph_Dash import (
        _MP_PLOT_CHOICES,
        attach_season_window_compare,
        available_dash_families,
        available_family_aggregations,
        build_season_window_compare,
        create_dash_app,
        create_mp_ts_dash,
        create_season_compare_dash_app,
        create_window_dash_app,
        plot_season_family_dash,
        plot_TS_res_dash,
        plot_TS_res_from_ts,
        plot_window_res_dash,
        resolve_family_df,
        run_dash,
    )
else:
    _MP_PLOT_CHOICES = []


def _synthetic_ts_results(n=6):
    """Minimal ``time_series_results`` dict covering all Dash plot types."""
    idx = pd.RangeIndex(0, n)
    return {
        "curtailment": pd.DataFrame({"rs1": [0.1, 0.2, 0.15, 0.05, 0.0, 0.1]}, index=idx),
        "net_price_zone_power": pd.DataFrame(
            {"pz1": [10.0] * n, "o_aux": [0.0] * n}, index=idx
        ),
        "grid_loading": pd.DataFrame({"load": [0.5, 0.6, 0.55, 0.7, 0.65, 0.6]}, index=idx),
        "real_load_opf": pd.DataFrame({"n1": [-0.2, -0.25, -0.22, -0.3, -0.28, -0.26]}, index=idx),
        "real_load_known_by_zone": pd.DataFrame({"z1": [0.3] * n}, index=idx),
        "PN_min": pd.DataFrame({"pz1": [1.0, 2.0, 1.5, 2.5, 2.0, 1.8]}, index=idx),
        "PN_max": pd.DataFrame({"pz1": [5.0, 6.0, 5.5, 7.0, 6.5, 6.0]}, index=idx),
        "real_power_opf": pd.DataFrame({"g1": [0.4, 0.5, 0.45, 0.55, 0.5, 0.48]}, index=idx),
        "real_power_by_zone": pd.DataFrame({"z1": [0.4, 0.5, 0.45, 0.55, 0.5, 0.48]}, index=idx),
        "prices_by_zone": pd.DataFrame(
            {"pz1": [50.0, 55.0, 52.0, 58.0, 54.0, 51.0], "o_hidden": [0.0] * n},
            index=idx,
        ),
        "ac_loading": pd.DataFrame({"l1": [0.6, 0.7, 0.65, 0.75, 0.7, 0.68]}, index=idx),
        "dc_loading": pd.DataFrame({"l2": [0.5, 0.55, 0.52, 0.6, 0.58, 0.56]}, index=idx),
        "converter_loading": pd.DataFrame({"c1": [0.8, 0.85, 0.82, 0.9, 0.88, 0.86]}, index=idx),
    }


def _grid_with_ts_results():
    grid = pyf.Grid(S_base=100)
    grid.name = "dash_test"
    grid.time_series_results = _synthetic_ts_results()
    grid.Time_series_ran = True
    return grid


def _ts_inv_snapshot():
    return {"time_series_results": _synthetic_ts_results(), "S_base": 100.0}


def _cols_for_plot_choice(plotting_choice, ts):
    if plotting_choice in (
        "Power Generation by generator",
        "Power Generation by generator area chart",
    ):
        return list(ts["real_power_opf"].columns)
    if plotting_choice in (
        "Power Generation by price zone",
        "Power Generation by price zone area chart",
    ):
        return list(ts["real_power_by_zone"].columns)
    if plotting_choice in ("Market Prices", "PN"):
        return ["pz1"]
    if plotting_choice == "PN_min":
        return list(ts["PN_min"].columns)
    if plotting_choice == "PN_max":
        return list(ts["PN_max"].columns)
    if plotting_choice == "Grid loading":
        return list(ts["grid_loading"].columns)
    if plotting_choice == "Real load":
        return list(ts["real_load_opf"].columns)
    if plotting_choice == "Known load by zone":
        return list(ts["real_load_known_by_zone"].columns)
    if plotting_choice == "AC line loading":
        return list(ts["ac_loading"].columns)
    if plotting_choice == "DC line loading":
        return list(ts["dc_loading"].columns)
    if plotting_choice == "AC/DC Converters":
        return list(ts["converter_loading"].columns)
    if plotting_choice == "Curtailment":
        return list(ts["curtailment"].columns)
    return []


@pytest.mark.parametrize("plotting_choice", _MP_PLOT_CHOICES)
def test_plot_TS_res_from_ts_all_choices(plotting_choice):
    ts = _synthetic_ts_results()
    cols = _cols_for_plot_choice(plotting_choice, ts)

    fig = plot_TS_res_from_ts(
        ts,
        S_base=100.0,
        plotting_choice=plotting_choice,
        selected_rows=cols,
        x_limits=(0, 5),
        y_limits=(0, 100),
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_plot_TS_res_from_ts_empty_and_unknown():
    ts = _synthetic_ts_results()
    empty_fig = plot_TS_res_from_ts(
        ts, 100.0, "unknown plot", selected_rows=[],
    )
    assert isinstance(empty_fig, go.Figure)
    assert len(empty_fig.data) == 0

    missing_pn = dict(ts)
    missing_pn.pop("net_price_zone_power")
    fig = plot_TS_res_from_ts(
        missing_pn, 100.0, "PN", selected_rows=["pz1"],
    )
    assert len(fig.data) == 0


def test_plot_TS_res_dash_wraps_grid():
    grid = _grid_with_ts_results()
    fig = plot_TS_res_dash(
        grid,
        "Power Generation by generator",
        selected_rows=["g1"],
        x_limits=(0, 5),
        y_limits=(0, 50),
    )
    assert len(fig.data) == 1


def _all_components(component, out=None):
    """Yield every component object in a Dash layout tree."""
    if out is None:
        out = []
    if component is None:
        return out
    out.append(component)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            _all_components(child, out)
    elif children is not None:
        _all_components(children, out)
    return out


def _layout_ids(component, found=None):
    """Collect component ids (str or dict) from a Dash layout tree."""
    if found is None:
        found = set()
    if component is None:
        return found
    cid = getattr(component, "id", None)
    if cid is not None:
        if isinstance(cid, dict):
            found.add((cid.get("type"), cid.get("index")))
        else:
            found.add(cid)
    children = getattr(component, "children", None)
    if children is None:
        return found
    if isinstance(children, (list, tuple)):
        for child in children:
            _layout_ids(child, found)
    else:
        _layout_ids(children, found)
    return found


def test_family_source_ts_generators():
    """Families generalized to TS: only Generators maps (real_power_opf × S_base)."""
    grid = _grid_with_ts_results()
    ts = grid.time_series_results
    assert available_dash_families(grid, ts, source="ts") == ["Generators"]

    # No topology generators on the synthetic grid → entity/total fallback.
    df, ylabel = resolve_family_df(ts, grid, "Generators", "total", source="ts")
    assert df is not None and not df.empty
    assert list(df.columns) == ["total"]
    # total == sum over gen columns × S_base (single col g1 here)
    assert list(df["total"]) == list(ts["real_power_opf"]["g1"] * grid.S_base)

    ent, _ = resolve_family_df(ts, grid, "Generators", "gen", source="ts")
    assert list(ent.columns) == ["g1"]
    # Window-only families do not resolve for ts.
    assert "Storage" not in available_dash_families(grid, ts, source="ts")


def test_power_family_overview():
    """Power family: one series per input class; gens split AC/DC."""
    grid = _grid_with_window_results()
    res = grid.window_opf_results
    families = available_dash_families(grid, res, source="window")
    assert families[0] == "Power"
    assert "Curtailment" in families
    assert available_family_aggregations(grid, "Power", res) == ["source"]

    df_c, ylabel_c = resolve_family_df(
        res, grid, "Curtailment", "ren_source", source="window"
    )
    assert ylabel_c == "Curtailment %"
    assert list(df_c["rs1"]) == [0.0, 10.0, 5.0]

    # MW-weighted total uses ren_available (pre-curtail).
    # rs1: curt=[0, 0.5, 1.0], avail=[90, 10, 40]
    # rs2: curt=[0, 0, 0],     avail=[10, 10, 10]
    # f0: 0%; f1: (5+0)/20=25%; f2: (40+0)/50=80%
    weighted_res = {
        "curtailment": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [0.0, 0.5, 1.0], "rs2": [0.0, 0.0, 0.0]}
        ),
        "ren_available": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [90.0, 10.0, 40.0], "rs2": [10.0, 10.0, 10.0]}
        ),
        "ren_power": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [90.0, 5.0, 0.0], "rs2": [10.0, 10.0, 10.0]}
        ),
    }
    bare = pyf.Grid(S_base=100)
    df_w, _ = resolve_family_df(
        weighted_res, bare, "Curtailment", "total", source="window"
    )
    assert list(df_w["total"]) == pytest.approx([0.0, 25.0, 80.0])

    df, ylabel = resolve_family_df(res, grid, "Power", "source", source="window")
    assert ylabel == "Power (MW)"
    assert set(df.columns) == {
        "Total ren", "Total gen_AC", "Total gen_DC", "Total H2", "Total BESS",
    }
    assert list(df["Total ren"]) == [5.0, 8.0, 6.0]
    assert list(df["Total gen_AC"]) == [10.0, 20.0, 15.0]
    assert list(df["Total gen_DC"]) == [3.0, 4.0, 5.0]
    assert list(df["Total H2"]) == [22.5, 22.5, 22.5]
    assert list(df["Total BESS"]) == [5.0, 10.0, 0.0]

    # Hard error when gen_power exists but topology names do not match.
    bare = pyf.Grid(S_base=100)
    bare.window_opf_results = {
        "gen_power": pd.DataFrame({"frame": [0, 1], "orphan": [1.0, 2.0]}),
    }
    with pytest.raises(ValueError, match="none match"):
        resolve_family_df(bare.window_opf_results, bare, "Power", "source", source="window")

    # TS source has no Power overview (window-only composite).
    assert "Power" not in available_dash_families(
        _grid_with_ts_results(), _synthetic_ts_results(), source="ts"
    )


def test_create_dash_app_layout():
    app = create_dash_app(_grid_with_ts_results())
    assert app.layout is not None
    ids = _layout_ids(app.layout)
    for required in ("sidebar", "content", "plot-panels", "add-plot", "toggle-sidebar", "view-mode"):
        assert required in ids
    # full-width logo image present in sidebar
    imgs = [c for c in _all_components(app.layout) if getattr(c, "src", None)]
    assert imgs
    assert imgs[0].style.get("width") == "100%"



def test_create_mp_ts_dash_layout_and_errors():
    ts_inv = {"base": _ts_inv_snapshot(), 1: _ts_inv_snapshot()}
    app = create_mp_ts_dash(ts_inv, grid_name="MP test")
    assert app.layout is not None
    ids = _layout_ids(app.layout)
    for required in ("sidebar", "content", "plot-panels", "add-plot", "toggle-sidebar",
                     "mp-mode", "mp-compare-layout"):
        assert required in ids

    with pytest.raises(ValueError, match="ts_inv is empty"):
        create_mp_ts_dash({})
    with pytest.raises(ValueError, match="no period keys"):
        create_mp_ts_dash({"bad": 1})


def test_run_dash_routing_errors():
    grid = pyf.Grid(S_base=100)
    with pytest.raises(ValueError, match="run_dash \\(auto\\)"):
        run_dash(grid)

    grid.dash_mode = "mp_ts"
    with pytest.raises(ValueError, match="dash_mode=mp_ts"):
        run_dash(grid)

    grid.dash_mode = "window"
    with pytest.raises(ValueError, match="dash_mode=window"):
        run_dash(grid)

    grid.dash_mode = "rolling"
    with pytest.raises(ValueError, match="dash_mode=rolling"):
        run_dash(grid)


def _grid_with_window_results():
    grid = pyf.Grid(S_base=100)
    grid.name = "window_dash_test"
    pyf.add_AC_node(grid, 220, name="n1")
    pyf.add_DC_node(grid, 320, name="ndc1")
    pyf.add_extgrid(grid, "n1", gen_name="g1")
    pyf.add_gen_DC(grid, "ndc1", gen_name="gdc1")
    grid.window_opf_run = True
    grid.window_opf_results = {
        "storage_soc": pd.DataFrame(
            {"frame": [-1, 0, 1, 2], "st1": [0.5, 0.45, 0.5, 0.55]}
        ),
        "storage_power": pd.DataFrame(
            {"frame": [0, 1, 2], "st1": [5.0, 10.0, 0.0]}
        ),
        "hydrogen_mass_H2": pd.DataFrame(
            {"frame": [-1, 0, 1, 2], "el1": [0.0, 10.0, 20.0, 30.0]}
        ),
        "hydrogen_P_e": pd.DataFrame(
            {"frame": [0, 1, 2], "el1": [22.5, 22.5, 22.5]}
        ),
        "gen_power": pd.DataFrame(
            {"frame": [0, 1, 2], "g1": [10.0, 20.0, 15.0], "gdc1": [3.0, 4.0, 5.0]}
        ),
        "gen_price": pd.DataFrame(
            {"frame": [0, 1, 2], "g1": [40.0, 50.0, 45.0]}
        ),
        "ren_power": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [5.0, 8.0, 6.0]}
        ),
        "ren_available": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [5.0, 8.0 / 0.9, 6.0 / 0.95]}
        ),
        "ren_price": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [0.0, 0.0, 0.0]}
        ),
        "curtailment": pd.DataFrame(
            {"frame": [0, 1, 2], "rs1": [0.0, 0.1, 0.05]}
        ),
        "ac_loading": pd.DataFrame(
            {"frame": [0, 1, 2], "l1": [0.2, 0.3, 0.25]}
        ),
        "dc_loading": pd.DataFrame(
            {"frame": [0, 1, 2], "ldc1": [0.1, 0.15, 0.12]}
        ),
        "converter_loading": pd.DataFrame(
            {"frame": [0, 1, 2], "c1": [0.4, 0.5, 0.45]}
        ),
        "total_objective": 0.0,
    }
    return grid


def test_create_window_dash_app_layout_and_plot():
    grid = _grid_with_window_results()
    app = create_window_dash_app(grid)
    assert app.layout is not None

    fig = plot_window_res_dash(grid, "Storage SoC", ["st1"])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert list(fig.data[0].x) == [-1, 0, 1, 2]
    assert list(fig.data[0].y) == [0.5, 0.45, 0.5, 0.55]

    overview = plot_window_res_dash(
        grid,
        "Total power",
        ["Total ren", "Total gen", "Total H2", "Total BESS"],
    )
    assert len(overview.data) == 4
    assert {t.name for t in overview.data} == {
        "Total ren", "Total gen", "Total H2", "Total BESS",
    }

    with pytest.raises(ValueError, match="window_opf"):
        create_window_dash_app(pyf.Grid(S_base=100))


def test_rolling_window_dash_controls_and_frame_limits():
    from pyflow_acdc.Graph_Dash import (
        _rolling_frame_limits,
        create_rolling_dash_app,
    )

    info = {
        "window_size": 24,
        "n_windows": 3,
        "commits": [(0, 23), (24, 47), (48, 71)],
    }
    assert _rolling_frame_limits(info, 1, 3) is None
    assert _rolling_frame_limits(info, 1, 1) == (0, 23)
    assert _rolling_frame_limits(info, 2, 1) == (24, 47)
    assert _rolling_frame_limits(info, 2, 2) == (24, 71)

    grid = _grid_with_window_results()
    grid.rolling_window_opf_run = True
    grid.rolling_window_info = info
    app = create_rolling_dash_app(grid)
    assert app.layout is not None
    ids = _layout_ids(app.layout)
    assert "roll-panel-configs" in ids

    with pytest.raises(ValueError, match="rolling"):
        create_rolling_dash_app(pyf.Grid(S_base=100))


def _synthetic_window_opf_results(*, ren, gen, h2, bess, soc=None, h2_mass=None, gen_price=None):
    """Minimal window_opf_results for season-compare totals (3 frames)."""
    frames = [0, 1, 2]
    out = {
        "ren_power": pd.DataFrame({"frame": frames, "rs1": ren}),
        "gen_power": pd.DataFrame({"frame": frames, "g1": gen}),
        "hydrogen_P_e": pd.DataFrame({"frame": frames, "el1": h2}),
        "storage_power": pd.DataFrame({"frame": frames, "st1": bess}),
    }
    if soc is not None:
        out["storage_soc"] = pd.DataFrame(
            {"frame": [-1, 0, 1, 2], "st1": soc}
        )
    if h2_mass is not None:
        out["hydrogen_mass_H2"] = pd.DataFrame(
            {"frame": [-1, 0, 1, 2], "el1": h2_mass}
        )
    if gen_price is not None:
        out["gen_price"] = pd.DataFrame({"frame": frames, "g1": gen_price})
    return out


def _grid_with_season_compare():
    season_map = {
        "Autumn": _synthetic_window_opf_results(
            ren=[5.0, 8.0, 6.0],
            gen=[10.0, 20.0, 15.0],
            h2=[22.5, 22.5, 22.5],
            bess=[5.0, 10.0, 0.0],
            soc=[0.5, 0.45, 0.5, 0.55],
            h2_mass=[0.0, 10.0, 20.0, 30.0],
            gen_price=[40.0, 50.0, 45.0],
        ),
        "Winter": _synthetic_window_opf_results(
            ren=[7.0, 9.0, 4.0],
            gen=[12.0, 18.0, 14.0],
            h2=[20.0, 21.0, 19.0],
            bess=[-5.0, 0.0, 8.0],
            soc=[0.5, 0.4, 0.35, 0.4],
            h2_mass=[0.0, 8.0, 16.0, 24.0],
            gen_price=[60.0, 55.0, 50.0],
        ),
    }
    grid = pyf.Grid(S_base=100)
    grid.name = "season_compare_test"
    pyf.add_AC_node(grid, 220, name="n1")
    pyf.add_extgrid(grid, "n1", gen_name="g1")
    attach_season_window_compare(grid, season_map)
    return grid


def test_build_season_window_compare_totals():
    autumn = _synthetic_window_opf_results(
        ren=[5.0, 8.0, 6.0],
        gen=[10.0, 20.0, 15.0],
        h2=[22.5, 22.5, 22.5],
        bess=[5.0, 10.0, 0.0],
        soc=[0.5, 0.45, 0.5, 0.55],
        h2_mass=[0.0, 10.0, 20.0, 30.0],
    )
    winter = _synthetic_window_opf_results(
        ren=[7.0, 9.0, 4.0],
        gen=[12.0, 18.0, 14.0],
        h2=[20.0, 21.0, 19.0],
        bess=[-5.0, 0.0, 8.0],
        soc=[0.5, 0.4, 0.35, 0.4],
        h2_mass=[0.0, 8.0, 16.0, 24.0],
    )
    compare, ylabels = build_season_window_compare(
        {"Autumn": autumn, "Winter": winter}
    )
    assert set(compare) >= {"Total ren", "Total gen", "Total H2", "Total BESS", "SoC", "H2 mass"}
    assert list(compare["Total ren"].columns) == ["Autumn", "Winter"]
    assert list(compare["Total ren"]["Autumn"]) == [5.0, 8.0, 6.0]
    assert list(compare["Total ren"]["Winter"]) == [7.0, 9.0, 4.0]
    assert list(compare["Total BESS"]["Winter"]) == [-5.0, 0.0, 8.0]
    assert list(compare["SoC"]["Autumn"]) == [0.5, 0.45, 0.5, 0.55]
    assert ylabels["SoC"] == "SoC"
    assert ylabels["H2 mass"] == "H₂ mass (kg)"


def test_create_season_compare_dash_app_layout_and_plot():
    grid = _grid_with_season_compare()
    app = create_season_compare_dash_app(grid)
    assert app.layout is not None
    assert "compare-layout" in _layout_ids(app.layout)
    assert "SoC" in grid.season_window_compare
    assert "H2 mass" in grid.season_window_compare
    assert "Price: g1" in grid.season_window_compare

    with pytest.raises(ValueError, match="season_window_compare"):
        create_season_compare_dash_app(pyf.Grid(S_base=100))


def test_plot_season_family_overlay_vs_split():
    """Season compare supports Overlay (one axes) and Split (subplot per season)."""
    grid = _grid_with_season_compare()
    seasons = ["Autumn", "Winter"]

    overlay = plot_season_family_dash(
        grid, "Generators", "total", seasons, [], layout="overlay"
    )
    assert isinstance(overlay, go.Figure)
    assert len(overlay.data) == 2
    # Single axes → no second x-axis.
    assert "xaxis2" not in overlay.layout.to_plotly_json()

    split = plot_season_family_dash(
        grid, "Generators", "total", seasons, [], layout="split"
    )
    assert len(split.data) == 2
    # One subplot column per season → a second x-axis exists.
    assert "xaxis2" in split.layout.to_plotly_json()
    # Split colors align by variable: the (single) total series is the same
    # color in every season subplot.
    assert len({t.line.color for t in split.data}) == 1


def _callback_fn(app, key):
    """Return the undecorated Dash callback (Dash 3 wraps with context)."""
    return app.callback_map[key]["callback"].__wrapped__


def _find_callback_key(app, *needles):
    """Find a callback_map key that contains all needle substrings."""
    for key in app.callback_map:
        if all(n in key for n in needles):
            return key
    raise KeyError(f"No callback key matching {needles!r}; keys={list(app.callback_map)}")


def test_create_dash_app_callbacks_fire():
    """Invoke registered callbacks without starting a server (family builder, source='ts')."""
    grid = _grid_with_ts_results()
    app = create_dash_app(grid)

    toggle = _callback_fn(app, _find_callback_key(app, "sidebar.style", "content.style", "sidebar-open.data"))
    side, content, opened, label = toggle(1, 0, True)
    assert opened is False
    assert "translateX(-100%)" in side["transform"]
    assert content["marginLeft"] == "0"
    assert "Show options" in label
    side, content, opened, label = toggle(0, 0, False)
    assert opened is False

    render = _callback_fn(app, _find_callback_key(app, "panel-controls.children", "panel-graphs.children"))
    ctrls, graphs = render([0, 1], {}, "classic")
    assert len(ctrls) == 2
    assert len(graphs) == 2

    draw = _callback_fn(app, _find_callback_key(app, "plot-graph", "figure"))
    # Classic mode: use the flat TS plot-type list.
    figs, styles = draw(
        "classic",
        [], [], [],
        ["Power Generation by generator", "Market Prices"],
        [["g1"], ["pz1"]],
        [0, 0],
        [50, 100],
        0,
        5,
        360,
    )
    assert len(figs) == 2
    assert len(figs[0].data) >= 1
    assert len(figs[1].data) >= 1
    assert figs[0].layout.height == 360
    assert styles[0]["height"] == "360px"

    # Family mode: the Generators family resolves for TS (real_power_opf × S_base).
    fam_figs, _ = draw(
        "family",
        ["Generators"],
        ["total"],
        [[]],
        [], [],
        [None],
        [None],
        0,
        5,
        420,
    )
    assert len(fam_figs) == 1
    assert len(fam_figs[0].data) >= 1
    assert fam_figs[0].layout.height == 420


def test_create_mp_ts_dash_callbacks_fire():
    ts_inv = {"base": _ts_inv_snapshot(), 1: _ts_inv_snapshot(), 2: _ts_inv_snapshot()}
    app = create_mp_ts_dash(ts_inv, grid_name="MP callbacks")

    toggle_mode = _callback_fn(
        app, "..mp-compare-row.style...mp-single-row.style..",
    )
    compare_row, single_row = toggle_mode("compare")
    assert compare_row["display"] == "block"
    compare_row, single_row = toggle_mode("single")
    assert single_row["display"] == "block"

    render = _callback_fn(app, _find_callback_key(app, "panel-controls.children", "panel-graphs.children"))
    ctrls, graphs = render([0, 1])
    assert len(ctrls) == 2
    assert len(graphs) == 2

    draw = _callback_fn(app, _find_callback_key(app, "plot-graph", "figure"))
    figs, styles = draw(
        "single",
        "base",
        "base",
        "base",
        2,
        ["Power Generation by price zone"],
        [["z1"]],
        [0],
        [100],
        0,
        5,
        None,
        None,
        400,
        "split",
    )
    assert len(figs) == 1
    assert len(figs[0].data) >= 1
    assert figs[0].layout.height == 400
    assert styles[0]["height"] == "400px"

    # Compare, split (subplots): 3-column layout.
    figs_cmp, _ = draw(
        "compare",
        "base",
        "base",
        1,
        2,
        ["Power Generation by generator"],
        [["g1"]],
        [None],
        [None],
        None,
        None,
        None,
        None,
        480,
        "split",
    )
    assert len(figs_cmp) == 1
    assert len(figs_cmp[0].data) >= 1
    # make_subplots creates multiple x-axes (xaxis, xaxis2, xaxis3).
    assert "xaxis3" in figs_cmp[0].layout.to_plotly_json()

    # Compare, overlay: single axes, all period columns' traces overlaid.
    figs_ovl, _ = draw(
        "compare",
        "base",
        "base",
        1,
        2,
        ["Power Generation by generator"],
        [["g1"]],
        [None],
        [None],
        None,
        None,
        None,
        None,
        480,
        "overlay",
    )
    assert len(figs_ovl) == 1
    assert len(figs_ovl[0].data) >= 1
    # Overlay is a single subplot: no third x-axis.
    assert "xaxis3" not in figs_ovl[0].layout.to_plotly_json()
    # Trace names carry the period prefix so periods stay distinguishable.
    assert any("|" in (t.name or "") for t in figs_ovl[0].data)
    # Overlay colors encode the period: base/1/2 each get a distinct color.
    ovl_colors = [t.line.color for t in figs_ovl[0].data]
    assert len(set(ovl_colors)) == len(ovl_colors)

    figs_multi, _ = draw(
        "single",
        "base",
        "base",
        "base",
        2,
        ["Power Generation by price zone", "Curtailment"],
        [["z1"], ["rs1"]],
        [0, 0],
        [100, 100],
        0,
        5,
        None,
        None,
        480,
        "split",
    )
    assert len(figs_multi) == 2
    assert len(figs_multi[0].data) >= 1
    assert len(figs_multi[1].data) >= 1


def run_test():
    if dash_missing_for_run_test():
        return
    require_dash()
    test_plot_TS_res_from_ts_all_choices("Market Prices")
    test_plot_TS_res_from_ts_empty_and_unknown()
    test_plot_TS_res_dash_wraps_grid()
    test_create_dash_app_layout()
    test_create_mp_ts_dash_layout_and_errors()
    test_run_dash_routing_errors()
    test_create_window_dash_app_layout_and_plot()
    test_create_dash_app_callbacks_fire()
    test_create_mp_ts_dash_callbacks_fire()
    print("✓ graph_dash tests passed")


if __name__ == "__main__":
    run_test()
