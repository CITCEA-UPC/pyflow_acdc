"""Tests for ``Line_AC.line_model`` (nominal vs hyperbolic π from per-km data)."""

import cmath
import math

import pytest

import pyflow_acdc as pyf
from pyflow_acdc.constants import LineModel

R_OHM_KM, L_MH_KM, C_UF_KM = 0.022, 0.35, 0.221
KV, KM, N = 275.0, 100.0, 2
F = 50.0
A_RATING = 730.0


def _grid_with_line(line_model, f=F):
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, KV, node_type="Slack", name="a")
    pyf.add_AC_node(grid, KV, name="b")
    line = pyf.add_line_AC(grid, "a", "b", R_Ohm_km=R_OHM_KM, L_mH_km=L_MH_KM, C_uF_km=C_UF_KM, A_rating=A_RATING,
                           N_cables=N, Length_km=KM, line_model=line_model, f=f)
    return grid, line


def _hyperbolic_pu(f=F):
    w = 2 * math.pi * f
    z = complex(R_OHM_KM, w * L_MH_KM * 1e-3)
    y = complex(0.0, w * C_UF_KM * 1e-6)
    z_c = cmath.sqrt(z / y)
    theta = cmath.sqrt(z * y) * KM
    z_pi = z_c * cmath.sinh(theta) / N
    y_pi = 2 * cmath.tanh(theta / 2) / z_c * N
    z_base = KV**2 / 100
    return z_pi / z_base, y_pi * z_base


def test_hyperbolic_matches_long_line_formula():
    _, line = _grid_with_line(LineModel.HYPERBOLIC_PI_MODEL)
    z_pu, y_pu = _hyperbolic_pu()
    assert complex(line.r, line.x) == pytest.approx(z_pu, rel=1e-9)
    assert complex(line.g, line.b) == pytest.approx(y_pu, rel=1e-9)


def test_setter_switches_and_restores_nominal():
    _, line = _grid_with_line(LineModel.PI_MODEL)
    nominal = (line.r, line.x, line.g, line.b)
    line.line_model = LineModel.HYPERBOLIC_PI_MODEL
    assert (line.r, line.x, line.g, line.b) != pytest.approx(nominal)
    line.line_model = "pi"
    assert (line.r, line.x, line.g, line.b) == pytest.approx(nominal)


def test_frequency_is_used():
    _, line = _grid_with_line(LineModel.HYPERBOLIC_PI_MODEL, f=60.0)
    z_pu, _ = _hyperbolic_pu(f=60.0)
    assert complex(line.r, line.x) == pytest.approx(z_pu, rel=1e-9)


def test_setter_needs_per_km_data():
    grid, _ = pyf.create_grid_from_data(100)
    pyf.add_AC_node(grid, KV, node_type="Slack", name="a")
    pyf.add_AC_node(grid, KV, name="b")
    line = pyf.add_line_AC(grid, "a", "b", r=0.01, x=0.1, b=0.5, MVA_rating=300)
    with pytest.raises(ValueError):
        line.line_model = LineModel.HYPERBOLIC_PI_MODEL
