# Architecture

This page describes what each module in `pyflow_acdc` owns, and how the
layers depend on one another. It is a developer-oriented map, not an API
reference (see the API pages for signatures).

## Layering overview

`Classes` holds the **objects** (`Grid` and element instances). Everything
below that in the map is a **worker module**: public functions (and a few
orchestration helpers) that read/write those objects. They are not subclasses
of `Classes`.

```
[data]     constants  →  Classes          (Grid + element objects)

[build]    grid_creator / grid_modifications / grid_analysis
             (construct / mutate Grid; analyse topology)

[workers]  operate on a Grid (and related objects):
             ACDC_PF                              power flow
             pyomo_model_solve                    generic Pyomo solve
             ACDC_OPF (+ NL_models / L_models)    optimal power flow
             Static / STEP / MP TEP (+ pymoo, L)   transmission expansion
             Array_OPT                            wind-array route / CSS
             Time_series(_clustering)             time-series studies
             Results / Export / Graph_* / Mapping output
```

Lower layers never import from higher layers. `constants` is a leaf module
(no intra-package imports). Workers depend on `Classes` (and usually on
`grid_analysis` / `constants`); they do not form an inheritance tree off
`Classes`.

## Core model and construction

- **`constants.py`** — Single source of truth for domain constants and
  string enums (`NodeType`, `ConverterDCType`, `DataInput`, `Polarity`,
  `PowerLossModel`, `CableType`, `ConverterOpfFxType`, `AcDcSide`,
  `PriceZoneCategory`, `ObjComponent`, `CssMode`, `MIPBackend`,
  `PricingStrategy`, `LinkCost`, `DataExportType`, `TSType`), default
  tuples, tolerances/iteration caps, and shared helpers
  (`present_value_factor`, `default_obj_weights`). Owns: magic-value/string
  centralisation. Does not own: any grid logic.
- **`Classes.py`** — The data model: `Grid` plus element classes
  (`Node_AC/DC`, `Line_AC/DC` and AC line subclasses, `TF_Line_AC`,
  `AC_DC_converter`, `DCDC_converter`, `Gen_AC/DC`, `Storage` (AC or DC via
  `connected`), `Electrolyser`, `HeatPump` (AC flexible load), `Ren_Source`,
  `Price_Zone` and subclasses, `TimeSeries`, `Cable_options` / sizing helpers).
  Owns per-object state and derived electrical quantities (e.g. `Ybus`).
- **`grid_creator.py`** — Build a `Grid` from data tables, MATPOWER `.mat`
  files, pickles, or a turbine graph. Owns import/parsing.
- **`grid_modifications.py`** — Add or mutate elements after creation
  (`add_*`, including `add_storage` / `add_electrolyser` / `add_heat_pump`,
  line-type conversions, time/investment series wiring).
- **`grid_analysis.py`** — Topology/analysis utilities: `analyse_grid`,
  coordinate transforms (`pol2cart`/`cart2pol`/…), `Cable_parameters`,
  `Converter_parameters`, fuel-mix distribution.

## Analysis engines

- **`ACDC_PF.py`** — Power flow: `power_flow`, `ac_power_flow`,
  `dc_power_flow`, `acdc_sequential` (deprecated mixed-case aliases live in
  `depreciation_methods`). Pure Numpy; no Pyomo. Known P/Q folds in BESS /
  electrolyser operating fields when set.
- **`ACDC_OPF.py`** — OPF orchestration: `optimal_pf` / `optimal_l_pf`,
  objective assembly (`obj_w_rule`, `opf_obj` / `opf_obj_l`), `fx_conv`,
  result translation back onto the `Grid` (`translate_pyf_opf`,
  `opf_line_res`, `opf_step_results_l`, …). Calls `pyomo_model_solve` for
  the actual solve.
- **`pyomo_model_solve.py`** — Generic Pyomo solve layer shared by OPF, TEP,
  array, and time-series drivers: `pyomo_model_solve`, solver log parsers,
  feasibility checks, `reset_to_initialize`, `export_solver_progress_to_excel`.
  Distinct from `solver_utils.py` (environment probe only).
- **`NL_models/`** — Nonlinear model builders and drivers:
  `ACDC_OPF_NL_model` (full AC/DC Pyomo model, converters, price zones, TEP
  variables, BESS / H₂ / heat pumps), and `window_opf` (coupled / rolling
  multi-hour NL OPF with SoC / H₂ / HP parent links). TEP drivers in this
  package are listed under Planning below.
- **`L_models/`** — Linearised (LP/MILP) model builders and drivers — **not
  SOCP**: `AC_OPF_L_model` (AC Bθ; optional hybrid DC linearization + thin
  converters; McCormick cable-type selection; BESS P-only / electrolyser P +
  mass / heat-pump P-only with `Q_heat_pump` fixed at 0), `window_l_opf`
  (coupled / rolling), and `AC_L_CSS_ortools` (array CSS). Linear TEP lives
  under Planning. Myopic linear TS lives in `Time_series.ts_acdc_l_opf`.

## Planning and sizing

Transmission expansion (grid investment):

- **`NL_models/ACDC_Static_TEP.py`** — Static (single-horizon) NL TEP.
- **`NL_models/ACDC_sequential_STEP.py`** — Sequential STEP
  (`sequential_STEP` / `sequential_MS_STEP`) across time frames.
- **`NL_models/ACDC_MultiPeriod_TEP.py`** — Multi-period (MP) NL TEP sizing /
  investment over periods.
- **`L_models/ACDC_L_TEP.py`** — Linear static and linear multi-period TEP
  (`linear_transmission_expansion`,
  `linear_multi_period_transmission_expansion`).
- **`ACDC_TEP_pymoo.py`** — STEP via pymoo outer loop
  (`transmission_expansion_pymoo`) with OPF subproblems.

Wind-array specific (not general TEP):

- **`Array_OPT.py`** — Offshore inter-array **route** MIP
  (``MIP_path_graph``, Pyomo or OR-Tools CP-SAT; optional joint cable types
  via ``enable_cable_types``) and **CSS** dispatch (``wind_farm_CSS``,
  ``sequential_CSS``). Owns spanning-tree / flow / ``ct_limit`` constraints.
  Install ``[OPF]`` for Pyomo CSS; ``[LINEAR_ARRAY]`` for OR-Tools MIP/CSS +
  HiGHS. Uses OPF / L helpers as needed. Economics use
  `constants.present_value_factor`.

## Time series

- **`Time_series.py`** — Time-series power flow / OPF drivers and result
  aggregation (`ts_acdc_opf` NL myopic; `ts_acdc_l_opf` linear myopic twin;
  shared parameter update / SoC–H₂–HP carry helpers; PF setpoint TS for
  converters / BESS / electrolyser).
- **`Time_series_clustering.py`** — Representative-period clustering of
  time-series inputs.
- **`Market_Coeff.py`** — Price-zone quadratic cost curves from EPEX order books
  and ENTSO-E day-ahead CSVs (`price_zone_coef_data`, `clean_entsoe_data`, …).

## Output and visualisation

- **`Results_class.py`** — `Results` container and reporting tables
  (including `ext_storage` / `ext_electrolyser` / `ext_heat_pump`, window
  tables).
- **`Export_files.py`** — Export a grid to runnable Python, MATLAB, or
  pickle; code generation for loaders.
- **`Graph_and_plot.py`** — Static / Plotly network and result plots.
- **`Graph_Dash.py`** — Interactive Dash applications (TS, window family /
  season-compare).
- **`Mapping.py`** — Geographic (folium) maps.

## Support

- **`example_grids/`** — Bundled case factories (`PF/`, `OPF/`, `TEP/`,
  `Wind_Array/`); exposed via `pyflow_acdc.cases`.
- **`windfarm_loader.py`** — Load a bundled wind-farm case grid plus its
  GeoJSON context.
- **`solver_utils.py`** — Detect available Pyomo solvers and OR-Tools backends
  (does not run models).
- **`depreciation_methods.py`** — Deprecated mixed-case public aliases that
  warn and forward to snake_case names.
- **`__init__.py`** — Public API surface (`__all__`), optional-dependency
  guards, and the `cases` example-grid loader.

## Conventions

- Optional dependencies are imported behind `try/except ImportError` with
  feature flags (`HAS_OPF`, `HAS_DASH`, …). New optional features follow the
  same pattern.
- Public string values that form a closed vocabulary live in `constants.py`
  as `(str, Enum)` members. Stored attributes / dict keys use `.value`
  (plain strings) to preserve serialization; comparisons use the enum member.
- See `CONTRIBUTING.md` for coding and testing expectations.
