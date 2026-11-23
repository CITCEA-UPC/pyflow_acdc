"""Tests for ``change_S_base``: per-unit rescaling and PF equivalence across bases."""

import numpy as np

import pyflow_acdc as pyf
from pyflow_acdc.constants import DEFAULT_TOLERANCE

# PF input tolerance (per unit on current S_base). Library applies
# effective_tol = pf_tol * grid.tol_scaler with tol_scaler = S_base_ref / S_base
# so MW-normalized stopping is ~pf_tol * S_base_ref after a base change.
S_BASE_TEST_PF_TOL = DEFAULT_TOLERANCE  # 1e-10

# Max allowed MW drift when comparing line-flow results across change_S_base.
# ``S_BASE_PF_DRIFT_TOL`` is per-unit at ``S_base_ref``; MW atol = tol * S_base_ref.
S_BASE_PF_DRIFT_TOL = 1e-5

assert S_BASE_TEST_PF_TOL < S_BASE_PF_DRIFT_TOL


def _all_ac_lines(grid):
    return (
        grid.lines_AC + grid.lines_AC_exp + grid.lines_AC_rec
        + grid.lines_AC_tf + grid.lines_AC_ct
    )


def _snapshot_ac_pf_mw(grid):
    """AC line apparent power magnitudes in MW."""
    return np.array([
        max(abs(line.fromS), abs(line.toS)) * grid.S_base
        for line in _all_ac_lines(grid)
    ])


def _snapshot_dc_pf_mw(grid):
    """DC line power magnitudes in MW."""
    return np.array([
        max(abs(line.fromP), abs(line.toP)) * grid.S_base for line in grid.lines_DC
    ])


def _assert_pf_similar_after_s_base_change(
    grid, s_new, before, *, pf_tol=S_BASE_TEST_PF_TOL,
):
    """PF at ``s_new`` should match pre-change snapshot within drift tolerance (MW).

    PF uses ``pf_tol``; after ``change_S_base`` the solver sees
    ``effective_tol = pf_tol * S_base_ref / s_new`` (same MW scale).
    """
    s_base_ref = grid.S_base_ref
    rate = s_base_ref / s_new
    pyf.change_S_base(grid, s_new)
    assert grid.S_base == s_new
    assert grid.S_base_ref == s_base_ref
    assert grid.tol_scaler == rate

    pyf.power_flow(grid, tol_lim=pf_tol)

    atol_mw = S_BASE_PF_DRIFT_TOL * s_base_ref

    if before.get("ac_mva") is not None:
        after = _snapshot_ac_pf_mw(grid)
        assert np.allclose(before["ac_mva"], after, rtol=0, atol=atol_mw)
    if before.get("dc_mw") is not None:
        after = _snapshot_dc_pf_mw(grid)
        assert np.allclose(before["dc_mw"], after, rtol=0, atol=atol_mw)


def _assert_s_base_change_pf_independent_of_prior_pf(
    grid_factory, s_new, *, pf_tol=S_BASE_TEST_PF_TOL,
):
    """``change_S_base`` + PF should match whether PF ran at the old base first."""
    grid_after, _ = grid_factory()
    pyf.power_flow(grid_after, tol_lim=pf_tol)
    pyf.change_S_base(grid_after, s_new)
    pyf.power_flow(grid_after, tol_lim=pf_tol)

    grid_fresh, _ = grid_factory()
    pyf.change_S_base(grid_fresh, s_new)
    pyf.power_flow(grid_fresh, tol_lim=pf_tol)

    s_base_ref = grid_after.S_base_ref
    atol_mw = S_BASE_PF_DRIFT_TOL * s_base_ref

    if grid_after.nn_AC > 0:
        assert np.allclose(
            _snapshot_ac_pf_mw(grid_after),
            _snapshot_ac_pf_mw(grid_fresh),
            rtol=0,
            atol=atol_mw,
        )
    if grid_after.nn_DC > 0:
        assert np.allclose(
            _snapshot_dc_pf_mw(grid_after),
            _snapshot_dc_pf_mw(grid_fresh),
            rtol=0,
            atol=atol_mw,
        )


def test_change_S_base_rescales_pu_preserves_mw():
    """``change_S_base`` updates all elements and keeps physical MW/MVA unchanged."""
    pyf.initialize_pyflowacdc()
    grid, _ = pyf.cases["Stagg5MATACDC"]()

    S_old = grid.S_base
    S_new = 250
    rate = S_old / S_new

    ac_load_mw = {n.name: n.PLi * S_old for n in grid.nodes_AC if n.PLi}
    ac_gen_mw = {n.name: n.PGi * S_old for n in grid.nodes_AC if n.PGi}
    conv_p_mw = {c.name: c.P_AC * S_old for c in grid.Converters_ACDC}
    conv_q_mvar = {c.name: c.Q_AC * S_old for c in grid.Converters_ACDC}
    gen_p_mw = {g.name: g.PGen * S_old for g in grid.Generators}
    line_mva = {line.name: line.MVA_rating for line in _all_ac_lines(grid)}
    dc_mw_rating = {line.name: line.MW_rating for line in grid.lines_DC}

    pyf.change_S_base(grid, S_new)

    assert grid.S_base == S_new
    assert all(line.S_base == S_new for line in _all_ac_lines(grid))
    assert all(line.S_base == S_new for line in grid.lines_DC)
    assert all(conv.S_base == S_new for conv in grid.Converters_ACDC)
    assert all(gen.S_base == S_new for gen in grid.Generators)

    for name, mw in ac_load_mw.items():
        node = next(n for n in grid.nodes_AC if n.name == name)
        assert abs(node.PLi * S_new - mw) < 1e-9
        assert abs(node.PLi - mw / S_new) < 1e-9
        assert abs(node.PLi - (mw / S_old) * rate) < 1e-9

    for name, mw in ac_gen_mw.items():
        node = next(n for n in grid.nodes_AC if n.name == name)
        assert abs(node.PGi * S_new - mw) < 1e-9

    for name, mw in conv_p_mw.items():
        conv = next(c for c in grid.Converters_ACDC if c.name == name)
        assert abs(conv.P_AC * S_new - mw) < 1e-9

    for name, mvar in conv_q_mvar.items():
        conv = next(c for c in grid.Converters_ACDC if c.name == name)
        assert abs(conv.Q_AC * S_new - mvar) < 1e-9

    for name, mw in gen_p_mw.items():
        gen = next(g for g in grid.Generators if g.name == name)
        assert abs(gen.PGen * S_new - mw) < 1e-9

    for name, mva in line_mva.items():
        line = next(ln for ln in _all_ac_lines(grid) if ln.name == name)
        assert line.MVA_rating == mva

    for name, mw in dc_mw_rating.items():
        line = next(ln for ln in grid.lines_DC if ln.name == name)
        assert line.MW_rating == mw


# ── AC S_base PF regression (case24): A / B / C ─────────────────────────────
# A: two fresh loads, PF@100 vs change+PF@200 (equivalent-base gold standard).
# B: same grid PF@100 vs PF@200 after change (stale solve state).
# C: PF→change→PF vs change→PF on fresh loads (path at new base).


def test_case24_ac_s_base_pf_A_fresh_grids_equivalent_base():
    """A: fresh grid PF@100 vs fresh grid change_S_base(200)+PF — line MW."""
    pyf.initialize_pyflowacdc()
    s_base_ref = 100
    s_new = 200
    atol_mw = S_BASE_PF_DRIFT_TOL * s_base_ref

    grid100, res100 = pyf.cases["case24_OPF"]()
    pyf.power_flow(grid100, tol_lim=S_BASE_TEST_PF_TOL)
    res100.all()
    mw100 = _snapshot_ac_pf_mw(grid100)

    grid200, res200 = pyf.cases["case24_OPF"]()
    pyf.change_S_base(grid200, s_new)
    assert grid200.S_base == s_new
    assert grid200.tol_scaler == s_base_ref / s_new
    pyf.power_flow(grid200, tol_lim=S_BASE_TEST_PF_TOL)
    res200.all()
    mw200 = _snapshot_ac_pf_mw(grid200)

    assert np.allclose(mw100, mw200, rtol=0, atol=atol_mw)


def test_case24_ac_s_base_pf_B_same_grid_after_change():
    """B: same grid — line MW at 100 vs after change_S_base(200) + PF."""
    pyf.initialize_pyflowacdc()
    grid, _ = pyf.cases["case24_OPF"]()
    assert grid.S_base_ref == 100
    assert grid.tol_scaler == 1.0

    pyf.power_flow(grid, tol_lim=S_BASE_TEST_PF_TOL)
    before = {"ac_mva": _snapshot_ac_pf_mw(grid)}
    _assert_pf_similar_after_s_base_change(grid, 200, before)


def test_case24_ac_s_base_pf_C_path_independent():
    """C: PF@200 should not depend on whether PF ran at S_base=100 first."""
    pyf.initialize_pyflowacdc()
    _assert_s_base_change_pf_independent_of_prior_pf(pyf.cases["case24_OPF"], 200)


# ── DC S_base PF regression (DC_OPF_simple): A / B / C ──────────────────────
# A: two fresh loads, PF@100 vs change+PF@200 (equivalent-base gold standard).
# B: same grid PF@100 vs PF@200 after change (stale solve state).
# C: PF→change→PF vs change→PF on fresh loads (path at new base).


def test_dc_opf_simple_s_base_pf_A_fresh_grids_equivalent_base():
    """A: fresh grid PF@100 vs fresh grid change_S_base(200)+PF — line MW."""
    pyf.initialize_pyflowacdc()
    s_base_ref = 100
    s_new = 200
    atol_mw = S_BASE_PF_DRIFT_TOL * s_base_ref

    grid100, _ = pyf.cases["DC_OPF_simple"]()
    assert grid100.nn_AC == 0
    assert grid100.nn_DC > 0
    pyf.power_flow(grid100, tol_lim=S_BASE_TEST_PF_TOL)
    mw100 = _snapshot_dc_pf_mw(grid100)

    grid200, _ = pyf.cases["DC_OPF_simple"]()
    pyf.change_S_base(grid200, s_new)
    assert grid200.S_base == s_new
    assert grid200.tol_scaler == s_base_ref / s_new
    pyf.power_flow(grid200, tol_lim=S_BASE_TEST_PF_TOL)
    mw200 = _snapshot_dc_pf_mw(grid200)

    assert np.allclose(mw100, mw200, rtol=0, atol=atol_mw)


def test_dc_opf_simple_s_base_pf_B_same_grid_after_change():
    """B: same grid — line MW at 100 vs after change_S_base(200) + PF."""
    pyf.initialize_pyflowacdc()
    grid, _ = pyf.cases["DC_OPF_simple"]()
    assert grid.nn_AC == 0
    assert grid.nn_DC > 0
    assert grid.S_base_ref == 100
    assert grid.tol_scaler == 1.0

    pyf.power_flow(grid, tol_lim=S_BASE_TEST_PF_TOL)
    before = {"dc_mw": _snapshot_dc_pf_mw(grid)}
    _assert_pf_similar_after_s_base_change(grid, 200, before)


def test_dc_opf_simple_s_base_pf_C_path_independent():
    """C: PF@200 should not depend on whether PF ran at S_base=100 first."""
    pyf.initialize_pyflowacdc()
    _assert_s_base_change_pf_independent_of_prior_pf(pyf.cases["DC_OPF_simple"], 200)


# ── Hybrid S_base PF regression (Stagg5): A / B / C ───────────────────────────
# A: two fresh loads, PF@100 vs change+PF@200 (equivalent-base gold standard).
# B: same grid PF@100 vs PF@200 after change (stale solve state).
# C: PF→change→PF vs change→PF on fresh loads (path at new base).


def test_stagg5_s_base_pf_A_fresh_grids_equivalent_base():
    """A: fresh grid PF@100 vs fresh grid change_S_base(200)+PF — AC/DC line MW."""
    pyf.initialize_pyflowacdc()
    s_base_ref = 100
    s_new = 200
    atol_mw = S_BASE_PF_DRIFT_TOL * s_base_ref

    grid100, _ = pyf.cases["Stagg5MATACDC"]()
    assert grid100.nn_AC > 0
    assert grid100.nn_DC > 0
    pyf.power_flow(grid100, tol_lim=S_BASE_TEST_PF_TOL)
    ac100 = _snapshot_ac_pf_mw(grid100)
    dc100 = _snapshot_dc_pf_mw(grid100)

    grid200, _ = pyf.cases["Stagg5MATACDC"]()
    pyf.change_S_base(grid200, s_new)
    assert grid200.S_base == s_new
    assert grid200.tol_scaler == s_base_ref / s_new
    pyf.power_flow(grid200, tol_lim=S_BASE_TEST_PF_TOL)
    ac200 = _snapshot_ac_pf_mw(grid200)
    dc200 = _snapshot_dc_pf_mw(grid200)

    assert np.allclose(ac100, ac200, rtol=0, atol=atol_mw)
    assert np.allclose(dc100, dc200, rtol=0, atol=atol_mw)


def test_stagg5_s_base_pf_B_same_grid_after_change():
    """B: same grid — AC/DC line MW at 100 vs after change_S_base(200) + PF."""
    pyf.initialize_pyflowacdc()
    grid, _ = pyf.cases["Stagg5MATACDC"]()
    assert grid.nn_AC > 0
    assert grid.nn_DC > 0
    assert grid.S_base_ref == 100
    assert grid.tol_scaler == 1.0

    pyf.power_flow(grid, tol_lim=S_BASE_TEST_PF_TOL)
    before = {
        "ac_mva": _snapshot_ac_pf_mw(grid),
        "dc_mw": _snapshot_dc_pf_mw(grid),
    }
    _assert_pf_similar_after_s_base_change(grid, 200, before)


def test_stagg5_s_base_pf_C_path_independent():
    """C: PF@200 should not depend on whether PF ran at S_base=100 first."""
    pyf.initialize_pyflowacdc()
    _assert_s_base_change_pf_independent_of_prior_pf(pyf.cases["Stagg5MATACDC"], 200)


def run_test():
    test_case24_ac_s_base_pf_A_fresh_grids_equivalent_base()
    test_dc_opf_simple_s_base_pf_A_fresh_grids_equivalent_base()
    test_stagg5_s_base_pf_A_fresh_grids_equivalent_base()
    print("✓ S_base change tests passed")


if __name__ == "__main__":
    run_test()
