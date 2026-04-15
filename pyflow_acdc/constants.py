"""Domain constants used across the pyflow_acdc package."""

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

""" ACDC_PF (load_flow_DC, load_flow_AC, ACDC_sequential internal_tol),
    ACDC_MultiPeriod_TEP """
PF_INNER_TOLERANCE = 1e-8

""" ACDC_PF (flow_conv — converter inner iterations) """
CONV_TOLERANCE = 1e-12

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
