"""Domain constants used across the pyflow_acdc package."""

from enum import Enum


# ── String enums ────────────────────────────────────────────────────────

class NodeType(str, Enum):
    SLACK = 'Slack'
    PV = 'PV'
    PQ = 'PQ'

class ConverterDCType(str, Enum):
    P = 'P'
    PAC = 'PAC'
    SLACK = 'Slack'
    DROOP = 'Droop'

class DataInput(str, Enum):
    REAL = 'Real'
    PU = 'pu'
    OHM = 'Ohm'

class Polarity(str, Enum):
    MONOPOLAR = 'm'
    BIPOLAR = 'b'
    SYMMETRIC_MONOPOLAR = 'sm'

class PowerLossModel(str, Enum):
    QUADRATIC = 'quadratic'
    MMC = 'MMC'

class CableType(str, Enum):
    """Cable catalogue selection for AC/DC lines.

    Only the ``CUSTOM`` sentinel is listed here: it means “use explicit R/X
    (or ``Cable_parameters`` from ``grid_analysis``), not a row from the
    bundled cable database”.

    All other ``Cable_type`` values are **arbitrary strings** that must match
    the index of the YAML/DataFrame cable library (e.g. ``'NKT …'``). Do not
    add one enum member per catalogue entry.
    """
    CUSTOM = 'Custom'

class ConverterOpfFxType(str, Enum):
    """How converter AC quantities are fixed in OPF (see AC_DC_converter in Classes)."""
    PDC = 'PDC'
    PQ = 'PQ'
    PV = 'PV'
    NONE = 'None'
    Q = 'Q'


class AcDcSide(str, Enum):
    """Which subsystem a generator / renewable source is attached to."""
    AC = 'AC'
    DC = 'DC'


class PriceZoneCategory(str, Enum):
    """Price-zone kind in export/import dicts and `generate_add_price_zone_code`."""
    MAIN = 'main'
    OFFSHORE = 'offshore'
    MTDC = 'MTDC'


class ObjComponent(str, Enum):
    """OPF objective components (keys of the `ObjRule` / `weights_def` dict).

    Values are the public string keys users pass via ``ObjRule`` (e.g.
    ``Optimal_PF(grid, ObjRule={'Energy_cost': 1})``). Being a ``str`` Enum,
    members compare and hash equal to their string value, so they can be used
    interchangeably as dict keys/lookups while giving fail-fast typo protection
    on comparisons.
    """
    EXT_GEN = 'Ext_Gen'
    ENERGY_COST = 'Energy_cost'
    CURTAILMENT_RED = 'Curtailment_Red'
    AC_LOSSES = 'AC_losses'
    DC_LOSSES = 'DC_losses'
    CONVERTER_LOSSES = 'Converter_Losses'
    GENERAL_LOSSES = 'General_Losses'
    ARRAY_LOSSES = 'Array_losses'
    PZ_COST_OF_GENERATION = 'PZ_cost_of_generation'
    RENEWABLE_PROFIT = 'Renewable_profit'
    GEN_SET_DEV = 'Gen_set_dev'
    H2_SALE = 'H2_sale'
    SOC_DEVIATION = 'SoC_deviation'


class CssMode(str, Enum):
    """Cable-string-sizing solve mode in `Array_OPT` (`NL` argument).

    ``NL=False`` selects the linear model; ``NL=True`` is normalized to
    ``OPF``. Only the non-linear string values are enumerated here.
    """
    OPF = 'OPF'
    PF = 'PF'


class MIPBackend(str, Enum):
    """Solver backend for the array-MIP path problem in `Array_OPT`."""
    PYOMO = 'pyomo'
    ORTOOLS = 'ortools'


# OR-Tools ``linear_solver`` backends (CSS MILP and optional Pyomo path-MIP fallback).
ORTOOLS_LINEAR_SOLVERS = ('GUROBI', 'SCIP', 'CBC')
PYOMO_LINEAR_SOLVERS = ('gurobi', 'highs', 'appsi_highs', 'cbc', 'glpk')

class PricingStrategy(str, Enum):
    """How an `MTDCPrice_Zone` derives its price from linked price zones."""
    MIN = 'min'
    MAX = 'max'
    AVG = 'avg'


class LinkCost(str, Enum):
    """How a generator links its OPF cost coeffs to the host bus.

    ``NONE``
        Gen keeps its own ``qf`` / ``lf`` (default). Used by ``Energy_cost``
        when costs are independent of nodal / zonal prices.
    ``QUADRATIC``
        ``gen.qf`` / ``gen.lf`` track ``node.qf`` / ``node.lf`` (from zone
        ``a`` / ``b`` when the bus is in a price zone).
    ``LINEAR``
        ``gen.lf`` tracks ``node.price`` (from zone ``price`` when linked).
    """
    NONE = 'none'
    QUADRATIC = 'quadratic'
    LINEAR = 'linear'


class DataExportType(str, Enum):
    """How :class:`~pyflow_acdc.Results_class.Results` writes tables to disk.

    ``XLSX`` is accepted as an alias of ``EXCEL`` (same workbook export path).
    """
    CSV = 'csv'
    EXCEL = 'excel'
    XLSX = 'xlsx'


def coerce_data_export_type(value):
    """Return a :class:`DataExportType`; map ``xlsx`` → ``EXCEL``.

    Parameters
    ----------
    value : DataExportType or str
        Export-type flag from Results / callers.

    Returns
    -------
    DataExportType
        Canonical member (``XLSX`` is returned as ``EXCEL``).

    Raises
    ------
    ValueError
        If ``value`` is not a known export type.
    TypeError
        If ``value`` is neither ``str`` nor :class:`DataExportType`.
    """
    if isinstance(value, DataExportType):
        return DataExportType.EXCEL if value is DataExportType.XLSX else value
    if not isinstance(value, str):
        raise TypeError(
            f"export_type must be str or DataExportType, got {type(value).__name__}"
        )
    key = value.strip().lower()
    try:
        member = DataExportType(key)
    except ValueError as exc:
        allowed = ', '.join(repr(m.value) for m in DataExportType)
        raise ValueError(
            f"Unknown export_type {value!r}; expected one of: {allowed}"
        ) from exc
    return DataExportType.EXCEL if member is DataExportType.XLSX else member


class TSType(str, Enum):
    """`TimeSeries.type` labels recognised by the TS dispatch logic.

    These are the built-in time-series categories matched in
    `Time_series.update_grid_data`, `grid_modifications.time_series_dict`
    and `ACDC_Static_TEP`. ``ts.type`` is user-set, so unknown labels simply
    match no branch (unchanged behaviour); this enum only centralises the
    labels the package itself acts on.
    """
    A_CG = 'a_CG'
    B_CG = 'b_CG'
    C_CG = 'c_CG'
    PGL_MIN = 'PGL_min'
    PGL_MAX = 'PGL_max'
    PRICE = 'price'
    H2_PRICE = 'h2_price'
    HP_P_REF = 'hp_P_ref'
    HP_Q_REF = 'hp_Q_ref'
    HP_E_MIN = 'hp_E_min'
    HP_E_MAX = 'hp_E_max'
    LOAD = 'Load'
    # PF setpoint series for ACDC converters (see update_grid_for_pf)
    CONV_P_DC = 'conv_P_DC'
    CONV_P_AC = 'conv_P_AC'
    CONV_Q_AC = 'conv_Q_AC'
    # PF setpoint series for BESS (net P; Q on AC only)
    STORAGE_P = 'storage_P'
    STORAGE_Q = 'storage_Q'
    # PF setpoint series for electrolyser (P load; Q on AC only)
    H2_P = 'h2_P'
    H2_Q = 'h2_Q'
    # Renewable availability series (see TS_RENEWABLE_TYPES)
    WPP = 'WPP'
    OWPP = 'OWPP'
    SF = 'SF'
    REN = 'REN'
    SOLAR = 'Solar'


# Renewable-availability TS labels handled together as one group.
TS_RENEWABLE_TYPES = (TSType.WPP, TSType.OWPP, TSType.SF, TSType.REN, TSType.SOLAR)

# Converter PF setpoint TS labels (update_grid_for_pf).
TS_CONV_PF_TYPES = (TSType.CONV_P_DC, TSType.CONV_P_AC, TSType.CONV_Q_AC)

# BESS PF setpoint TS labels (net active; reactive on AC only).
TS_STORAGE_PF_TYPES = (TSType.STORAGE_P, TSType.STORAGE_Q)

# Electrolyser PF setpoint TS labels (active load; reactive on AC only).
TS_H2_PF_TYPES = (TSType.H2_P, TSType.H2_Q)

# All PF setpoint TS labels dispatched via update_grid_for_pf.
TS_PF_TYPES = TS_CONV_PF_TYPES + TS_STORAGE_PF_TYPES + TS_H2_PF_TYPES


# Default fuel / technology labels for Grid.gen_ac_types (ENTSO-E-like; grids may extend).
DEFAULT_GENERATION_TYPES = (
    'nuclear',
    'hard coal',
    'hydro',
    'oil',
    'lignite',
    'natural gas',
    'solid biomass',
    'other',
    'waste',
    'biogas',
    'geothermal',
    'ccgt',
    'diesel',
    'shunt reactor',
)

DEFAULT_RENEWABLE_TYPES = (
    'wind',
    'solar',
    'offshore wind',
    'onshore wind',
)

# Default Gen_AC / Gen_DC / add_gen fuel_type (capital O; normalized to lowercase in lookups).
DEFAULT_GEN_TYPE = 'Other'


# ── General ──────────────────────────────────────────────────────────────
""" Classes, grid_creator, grid_modifications, Results_class, grid_analysis """
import math
SQRT_3 = math.sqrt(3)

""" Classes, Time_series, Results_class, AC_L_CSS_*, ACDC_Static_TEP,
    ACDC_MultiPeriod_TEP, Array_OPT, ACDC_TEP_pymoo """
HOURS_PER_YEAR = 8760

# ── Economics (TEP / planning) ───────────────────────────────────────────
""" Classes, ACDC_Static_TEP, ACDC_MultiPeriod_TEP, Array_OPT """
DEFAULT_N_YEARS = 25

""" Classes, AC_L_CSS_*, ACDC_Static_TEP, ACDC_MultiPeriod_TEP,
    Array_OPT, ACDC_TEP_pymoo """
DEFAULT_DISCOUNT_RATE = 0.02

# ── Solver defaults ──────────────────────────────────────────────────────
""" AC_L_CSS_*, ACDC_Static_TEP, Array_OPT, ACDC_TEP_pymoo """
DEFAULT_TIME_LIMIT = 300

# ── Power-flow tolerances ────────────────────────────────────────────────
""" ACDC_PF (Power_flow, AC_PowerFlow, DC_PowerFlow), Time_series (TS_ACDC_PF),
    ACDC_OPF_NL_model, Array_OPT, ACDC_OPF, Results_class """
DEFAULT_TOLERANCE = 1e-10

""" ACDC_PF (ACDC_sequential outer loop), ACDC_OPF """
PF_OUTER_TOLERANCE = 1e-4

""" ACDC_PF (:func:`power_flow` hybrid path): outer sequential tol = inner * factor """
PF_SEQ_TOL_FACTOR = 1e4

""" ACDC_PF (load_flow_dc, load_flow_ac, acdc_sequential internal_tol),
    ACDC_MultiPeriod_TEP """
PF_INNER_TOLERANCE = PF_OUTER_TOLERANCE / PF_SEQ_TOL_FACTOR

""" ACDC_PF (flow_conv — converter inner iterations) """
CONV_TOLERANCE = PF_OUTER_TOLERANCE / PF_SEQ_TOL_FACTOR**2

# ── Iteration caps ───────────────────────────────────────────────────────
""" ACDC_PF, Time_series """
DEFAULT_PF_MAX_ITER = 100

""" ACDC_PF (flow_conv) """
DEFAULT_CONV_MAX_ITER = 20

""" Time_series_clustering """
DEFAULT_CLUSTERING_MAX_ITER = 300

# ── Voltage limits (per-unit) ────────────────────────────────────────────
""" Classes (Node_DC), grid_creator, grid_modifications """
DEFAULT_V_MIN_DC = 0.95
DEFAULT_V_MAX_DC = 1.05

# ── Placeholders / thresholds ────────────────────────────────────────────
""" grid_creator, grid_modifications, Time_series, ACDC_OPF_NL_model,
    ACDC_Static_TEP, ACDC_MultiPeriod_TEP, AC_OPF_L_model """
MAX_RATING_PLACEHOLDER = 99999

""" ACDC_OPF_NL_model, ACDC_Static_TEP, AC_OPF_L_model """
CT_SELECTION_THRESHOLD = 0.90

""" Time_series, ACDC_OPF_NL_model, ACDC_Static_TEP, AC_OPF_L_model
    (binary variable rounding: >= threshold → treat as 1) """
BINARY_THRESHOLD = 0.99999


# ── OPF objective defaults ───────────────────────────────────────────────

def default_obj_weights():
    """Return a fresh OPF objective-weights dict with every component at ``w=0``.

    Single source of truth for the ``weights_def`` / ``Grid.OPF_obj`` layout
    (used by ``obj_w_rule``, ``Grid.__init__`` and ``TS_ACDC_OPF``). A new dict
    with fresh inner dicts is built on every call so each caller can mutate its
    own copy. Key order follows ``ObjComponent`` declaration order; keys are
    plain strings (``.value``) so existing serialization/display is unchanged.
    """
    return {component.value: {'w': 0} for component in ObjComponent}


# ── Shared economics helpers ────────────────────────────────────────────

def present_value_factor(Hy=HOURS_PER_YEAR, discount_rate=DEFAULT_DISCOUNT_RATE, n_years=25):
    """Annuity factor scaled by hours-per-year.

    Returns  Hy * (1 - (1 + r)^{-n}) / r  which converts a per-hour
    operational cost into its net-present-value over *n_years* at a
    constant annual *discount_rate*.
    """
    return Hy * (1 - (1 + discount_rate) ** -n_years) / discount_rate
