# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

> This changelog was introduced during a maintenance/hardening effort; entries
> for releases prior to its creation are not reconstructed here. The current
> packaged version is **0.7.0**.

## [Unreleased]

### Added
- **SOCP CCP runners (Phase 10):** ``socp_ccp_optimise`` and
  ``socp_ccp_window_optimisation`` apply truncated-normal quantiles to wind
  caps (``P_ren``) and nodal prices before a single SOCP solve (Paper A §4).
  ``apply_ccp_quantiles`` is exported for inspection / reuse. Price CCP applies
  when ``Energy_cost`` has non-zero weight in ``weights_def``.
- **SOCP ``Energy_cost``:** matches Pyomo ``formula_Energy_cost`` — generator
  quadratic costs, per-renewable ``qf``/``lf`` on availability profiles, and
  heat-pump ``P_shed``/``Q_shed`` quadratic/linear shed costs when weighted.

## [0.7.0]

CVXPY sparse SOCP scaffolding (convex AC/DC stack).

### Added
- **SOCP / MI-SOCP stack (CVXPY)**: optional ``[SOCP]`` extra (``cvxpy`` +
  ``clarabel``). Builders in ``convex_model/`` (``build_socp_data``,
  ``socp_model``); runners in ``ACDC_convex`` (``socp_optimise``,
  ``soc_window_optimisation``, ``translate_pyf_socp``). ``T``-indexed
  variables for window / inventory coupling. Architecture documents the stack
  next to NL / L OPF. CCP and MI exclusivity still deferred.
- **SOCP BESS + H₂**: continuous ``P_charge``/``P_discharge``
  (no exclusivity binaries), AC S-circle / DC ``|P_net|``, SoC chain across
  ``T``; electrolyser P (+ AC Q) and linear mass balance. Wired into AC/DC
  nodal injection, ``H2_sale`` / ``SoC_deviation`` objectives, and export.
- **SOCP heat pumps**: ``socp_optimise`` / ``soc_window_optimisation`` accept
  ``grid.HP``. ``build_socp_data`` packs ``hp_data`` / ``hp_by_ac_node``;
  ``heat_pump_variables`` / ``heat_pump_constraints`` use ``P_shed`` /
  ``Q_shed`` actuators with ``P_hp = P_ref - P_shed``, ``Q_hp = Q_ref - Q_shed``,
  symmetric ``Q_shed`` bounds from ``Max_S * Q_shed_lim_frac``, and the
  cumulative ``E_heat_pump`` chain across ``T``. AC-only load injection;
  ``translate_pyf_socp`` reads ``hp_P_ref`` / ``hp_Q_ref`` / ``hp_E_min`` /
  ``hp_E_max`` profiles from ``grid.Time_series``; results exported to
  ``grid.socp_results`` and heat-pump elements.
- **SOCP docs / Results / CI**: usage + API pages; NL/L/SOCP modelling
  sections; ``grid.socp_run`` reporting in ``Results.all``; smoke tests in
  ``test_socp.py``; open-source Clarabel in ``[SOCP]`` / ``All`` so CI does
  not need MOSEK.

### Changed
- **SOCP converter loss**: Paper affine form via DCP epigraph
  ``t ≥ |Re(Ss)|``, ``Ploss = a_conv + b_conv · t`` (replaces non-DCP
  ``Ploss = a + c_rect·|Ss|²`` equality).

## [0.6.12]

Controllable heat pumps (NL + linear P-only twin).

### Added
- **Controllable heat pumps**: ``HeatPump`` class, ``add_heat_pump``, and NL OPF
  when ``grid.HP`` (AC-only planning-oriented flexible load: baseline
  ``P_ref``/``Q_ref``, served ``P_hp``/``Q_hp`` via ``P_shed``/``Q_shed``,
  cumulative ``E_heat_pump`` in kWh). Myopic carry in ``ts_acdc_opf``; parent
  energy chain in ``window_nl_opf`` (``window_heat_pump_constraints``). Results
  ``ext_heat_pump`` / ``heat_pump_window``. TS types ``hp_P_ref``, ``hp_Q_ref``,
  ``hp_E_min``, ``hp_E_max``. Linear twin (P-only): ``optimal_l_pf`` /
  ``ts_acdc_l_opf`` / ``window_l_opf`` with ``Q_hp`` fixed at 0. Docs
  ``api/modelling_flexible_assets`` (heat-pump section) and ``api/grid_mod``;
  plan ``plans/heat_pump_plan.md``; tests ``test_heat_pump_opf.py``.
- ``Ren_Source.quadratic_cost_factor`` / ``linear_cost_factor`` (``qf`` / ``lf``);
  ``add_RenSource(..., quadratic_cost_factor=, linear_cost_factor=)``.

### Changed
- **Heat pumps**: optimize explicit ``P_shed`` / ``Q_shed`` with
  ``P_hp = P_ref - P_shed``, ``Q_hp = Q_ref - Q_shed``; reactive
  ``Q_shed`` bounds ``-Q_lim_shed <= Q_shed <= Q_lim_shed`` with
  ``Q_lim_shed = Max_S * Q_shed_lim_frac`` (``Max_S`` in pu, default
  ``n_units * P_unit_max``; ``add_heat_pump(..., S_rated_MVAR=)``;
  ``Q_shed_lim_frac`` default ``1``).
  ``Energy_cost`` penalizes shed vars directly (Montse shedding-sgen pattern):
  ``P_shed²·qf + P_shed·lf`` and
  ``Q_shed²·qf_q + Q_shed·lf_q`` (MW/MVAR via ``S_base``); cost kwargs on
  ``add_heat_pump`` default ``0``.
- **Window / TS parameter updates**: ``_modify_parameters`` /
  ``_modify_parameters_l`` and myopic carry include heat-pump ``E_heat_pump_prev``
  / refs when ``grid.HP``;
  ``window_block=True`` skips rewriting ``E_heat_pump_prev`` (parent window owns
  the energy chain).
- **`Energy_cost`**: removed ``OnlyGen`` flag from OPF runners and ``grid.OnlyGen``;
  renewable sources use per-element ``qf`` / ``lf`` on ``Ren_Source`` (default ``0``),
  with the same MW-scaled quadratic form as generators; converter
  ``P_conv·price`` and nodal ``PGi_ren·price`` terms removed from ``Energy_cost``.

## [0.6.11]

### Added
- **Export-only external grids**: with ``Allow_sell=True`` and ``MWmax=0``,
  ``MWmin`` sets the active-power export lower bound (e.g. ``MWmin=-MVAmax``).
  ``get_gen_p_min_eff`` lives in ``grid_analysis`` and is used consistently
  across NL/L OPF, time-series bound updates, and ``grid_state``.

## [0.6.10]

### Fixed
- **case118 TEP benchmark export interfaces**: ``add_extgrid`` at nodes 10/119/120
  no longer pass ``MWmax=0``; ``MVAmax=export_capacity/3`` now sets the active-power
  limit so TS OPF ``grid_state`` bounds and external-grid export capacity match the
  benchmark.

## [0.6.9]

### Fixed
- **Pip example data paths**: ``case118_TEP_benchmark``, ``case24_MP``,
  ``NS_MTDC_2025``, and PEI BESS loaders now resolve CSVs from the git-checkout
  ``examples/`` tree and ``{sys.prefix}/examples/...`` (pip ``data-files``),
  with GitHub raw fallback when local copies are missing. Shared helper:
  ``example_grids/_example_data_paths.py``. Fixes ``FileNotFoundError`` after
  ``pip install pyflow_acdc`` for benchmark and multi-period example cases.
- **Wheel packaging**: include ``example_grids/PF/CigreB4/*.csv`` so
  ``CigreB4_ACDC`` works after ``pip install`` (CSVs live beside the case, not
  under top-level ``examples/``).
- **CI package check**: load ``case118_TEP_benchmark``, ``case24_MP``,
  ``CigreB4_ACDC``, and ``NS_MTDC_2025`` (``online=False``) from the installed
  wheel to catch missing example data in distributions.

## [0.6.8]

### Fixed
- **Sequential STEP results export**: removed redundant ``run_results["_meta"]``
  (abort status stays on ``grid.Seq_*_aborted`` / ``abort_reason``), so
  ``pyomo_model_results_sequential`` no longer hits mixed str/int key sorting.

## [0.6.7]

### Fixed
- **Wheel packaging**: ship ``pyflow_acdc.NL_models`` and ``pyflow_acdc.L_models``
  subpackages (setuptools ``packages.find``). ``0.6.6`` omitted them, so OPF /
  TEP / STEP imports failed with ``No module named 'pyflow_acdc.NL_models'``.
- **CI package check**: install the built wheel with pyomo and assert NL/L
  subpackages plus TEP/STEP public attributes are importable (top-level
  ``import pyflow_acdc`` alone no longer counts as success).

## [0.6.6]

### Fixed
- **Expandable setup always available**: moved ``expand_elements_from_pd``,
  ``expand_element``, ``repurpose_element_from_pd``, ``update_attributes``, and
  ``base_cost_calculation`` from OPF-gated ``ACDC_Static_TEP`` into
  ``grid_modifications``, so example cases that mark elements expandable no
  longer fail with ``AttributeError`` when the soft-fail OPF import path does
  not attach TEP symbols.

## [0.6.5]

### Added
- **Sequential STEP** ``build_only``: skips the period-1 solve, extracts init
  values as usual, then stops before building later periods.
- **North Sea example data**: ``clusters_kmeans_medoids_k24.json`` for 2023+2024
  MS TEP (alongside existing k4).

## [0.6.4]

Linear twin of the 0.6.3 BESS / H₂ operational surface, plus hybrid AC/DC LP
and related packaging / docs / tooling.

### Added
- **Linear AC(/DC) hybrid OPF stack (LP)**: ``optimal_l_pf``,
  ``window_l_opf`` / ``rolling_window_l_opf``, and myopic ``ts_acdc_l_opf``
  mirror the NL operational surface on AC-only and hybrid grids
  (``ACmode`` / ``DCmode``). Builder ``opf_create_l_model_acdc`` adds
  linearized DC PF at ``V_ini``, thin converter link
  ``np·Ps + P_DC + np·(a + b·Ps) = 0``, and ``fx_conv`` PDC/PQ/PV (Q fix
  skipped when the linear model has no ``Q_conv_s_AC``). BESS is P-only
  (``Q_storage`` fixed at 0); electrolyser is P + mass inventory.
  ``SoC_deviation`` stays rejected (quadratic). Hybrid ``TEP=True`` still
  raises. Docs: ``api/L_models``, ``api/ts``, ``usage_window_opf``,
  ``architecture``; example ``doc_examples/L_models/05_hybrid_linear_opf.py``.
- **Dash**: restyled interactive dashboard (``run_dash``, assets, season-compare
  via ``create_season_compare_dash_app``); PEI season-compare doc example and
  screenshot. Family mode adds ``Curtailment`` (``window_opf_results`` /
  rolling; node/zone/total is MW-weighted
  ``Σ(curt·ren_available)/Σ(ren_available)`` from exported pre-curtail
  available MW, so ``curt=0`` and ``curt=1`` both work; shown as %). Add plot
  preserves per-panel family / aggregation / elements.
- **Window results**: ``ren_available`` (pre-curtail renewable MW) exported
  alongside ``ren_power`` / ``curtailment`` for weighted curtailment plots.
- **CI**: Codecov upload on push/PR to ``main`` (``coverage`` job in
  ``pr-tests.yml``; set ``CODECOV_TOKEN`` in repository secrets). Coverage
  reports and the README badge are maintained on Codecov.
- **`pyomo_model_solve.py`**: extracted generic Pyomo solve layer from
  `ACDC_OPF.py` (`pyomo_model_solve`, log parsers, feasibility checks,
  `reset_to_initialize`, `export_solver_progress_to_excel`). `ACDC_OPF` re-exports
  for backward compatibility.
- **Tests**: `test_solver_utils.py` (mocked Pyomo/OR-Tools solver probes),
  `test_opf_result_helpers.py` (OPF result helpers after Ipopt solve),
  `test_market_coeff.py`, clustering doc examples (`test_docs_clustering`),
  `test_graph_dash.py` (synthetic TS + Dash callback unit tests).
- **`ipopt_available` / `require_ipopt`** helpers in `pyflow_tests/_test_solver_deps.py`.
- **Generator cost linking**: ``LinkCost`` (``none`` / ``quadratic`` /
  ``linear``) and ``link_cost`` on ``add_gen`` / ``add_gen_DC`` / ``add_extgrid``
  so OPF cost coeffs can track nodal / price-zone prices.

### Removed
- **`TEST_COVERAGE.md`**: removed in favor of Codecov-only coverage tracking.
- **``price_link``**: removed from ``Gen_AC`` / ``Gen_DC`` and ``add_gen`` /
  ``add_gen_DC`` / ``add_extgrid``. Use ``link_cost='linear'`` instead. Legacy
  pickles are still migrated by ``_migrate_legacy_gen_link_cost``.

### Changed
- **Rename**: ``opf_create_l_model_ac`` → ``opf_create_l_model_acdc`` (same
  module; aligns with NL ``opf_create_nl_model_acdc`` naming).
- **Linear hybrid OPF (LP)**: ``opf_create_l_model_acdc`` follows
  ``ACmode`` / ``DCmode``; linearized DC ``V(V−V)G`` / ``PDC_from`` /
  ``PDC_to`` at ``V_ini``; thin converter loss ``a + b·Ps``; ``fx_conv`` on
  snapshot / window / TS linear drivers; window and ``ts_acdc_l_opf`` accept
  hybrid grids. Richer converter LP / S-limit outer approx deferred. Hybrid
  ``TEP=True`` still raises until TEP hooks are wired.
- **Pickle load migration**: ``_migrate_legacy_grid_attrs`` backfills node
  ``_price`` / ``_qf`` / ``_lf`` and gen ``link_cost`` (from legacy ``price`` /
  ``price_link``) so pre-property wind-farm pickles load cleanly.
- **Power flow API**: ``power_flow`` / ``ac_power_flow`` / ``dc_power_flow``
  return ``(elapsed, tol, tol_history)``; sequential tracker adds per-outer
  Newton histories (``ac_pf_iter_tolerances`` / ``dc_pf_iter_tolerances``).
- **Price-zone ↔ node linking** and generator cost sync improved in
  ``grid_modifications`` / ``Classes``.
- **`dill`** is a required base dependency; removed optional-import fallbacks in
  `grid_creator` / `Export_files` and `require_dill` test skips.
- **`Market_Coeff`**: module and public-function docstrings; expanded
  `docs/api/market_coef.rst` (EPEX CSV schema, workflow, ENTSO-E layout).
  `clean_entsoe_data` now returns the output Excel path.
- Docs and user-facing strings: **pyflow-acdc** / **pyflow_acdc** naming
  (replacing mixed ``PyFlow-ACDC`` / ``PyFlow ACDC`` variants).
- Citation / docs: README and ``docs/citing.rst`` aligned; root
  ``ARCHITECTURE.md`` included from ``docs/architecture.md``.

## [0.6.3]

BESS and green-hydrogen integration in the **nonlinear** OPF / window / TS stack.

### Added
- **Battery storage (BESS)**: ``Storage`` class, ``add_storage``, and NL OPF
  SoC dynamics / S-circle on AC or DC buses when ``grid.ESS``. Snapshot
  results via ``Results.ext_storage``; docs ``usage_storage`` / ``api/storage``.
- **Green hydrogen**: ``Electrolyser`` class, ``add_electrolyser``, and NL OPF
  inventory when ``grid.H2``. Snapshot results via ``Results.ext_electrolyser``;
  docs ``usage_hydrogen`` / ``api/hydrogen``.
- **Coupled window NL OPF** (``window_opf.py``): ``window_nl_opf`` solves a
  multi-hour nonlinear OPF with linked BESS SoC and H₂ inventory across frames;
  ``rolling_window_nl_opf`` chains windows with state carry-over; export helpers
  ``export_window_opf_results`` / ``results_window_opf``. Results tables
  ``storage_window`` / ``hydrogen_window``.
- **Myopic time-series OPF** with BESS / H₂: ``ts_acdc_opf`` carries SoC
  hour-to-hour; optional ``ObjRule['SoC_deviation']`` soft SoC reference;
  H₂ inventory carries within ``H2_mass_max`` with out-of-opt
  ``empty_tank_cycle`` empties (``None`` = never; ``N`` = every ``N`` hours);
  ``ObjRule['H2_sale']`` / ``TSType.H2_PRICE`` for sale economics. Window /
  rolling keep hard SoC ini/final and optional ``H2_mass_final``.
- **Objective / TS constants**: ``ObjComponent.H2_SALE``,
  ``ObjComponent.SOC_DEVIATION``, ``TSType.H2_PRICE``.
- **PEI example**: ``PEI_grid`` flags ``storage`` / ``hydrogen`` / seasonal
  data; ``examples/PEI_BESS``; tests for storage, hydrogen, window, and rolling
  OPF.
- **TS PF setpoints**: ``update_grid_for_pf`` applies prescribed PF setpoints
  from time series in pu: ACDC converters (``conv_P_DC``, ``conv_P_AC``,
  ``conv_Q_AC``), BESS (``storage_P`` net injection, ``storage_Q`` on AC), and
  electrolyser (``h2_P`` load, ``h2_Q`` on AC). Safe to call for every series
  (non-PF types no-op). ``h2_price`` stays a normal TS via ``update_grid_data``.
  Accepted labels live in ``TS_PF_TYPES`` / ``TSType``; converter fields must
  match DC ``type`` / ``AC_type``, and ``storage_Q`` / ``h2_Q`` require AC
  (fail-fast on mismatch). ``ts_acdc_pf`` / ``ts_ac_pf`` / ``ts_dc_pf``
  dispatch ``TS_PF_TYPES`` → ``update_grid_for_pf``, else → ``update_grid_data``.
  Droop/P converters without a ``conv_P_DC`` series restore ``P_DC`` from
  ``Pconv_save`` in ``ts_acdc_pf``.

### Changed
- **Rolling foresight**: ``rolling_window_nl_opf`` takes ``future_sight`` in
  ``[0, 1]`` (default ``0``) instead of ``soc_final_mode='future_sight'``.
  Steps are ``ceil(future_sight · window_size)`` (clamped to remaining hours);
  SoC final is enforced at the foresight end; with ``H2_mass_final``, the
  foresight segment requires ``≥ future_sight · H2_mass_final`` (raw fraction).
  Docs: ``usage_window_opf`` / ``api/window``.
- **Power flow known injections**: ``update_pq_ac`` / ``update_p_dc`` fold BESS
  and H₂ operating fields into the PF known P/Q (same signs as NL OPF). Storage
  contributes ``net_P_pu = P_discharge - P_charge`` (AC also ``Q``); electrolyser
  ``P_electrolyser`` is a known load (AC also ``Q_electrolyser`` as injection).
  Defaults remain zero until set / after OPF export.
- **Window OPF parameter updates**: ``_modify_parameters(..., window_block=True)``
  skips rewriting ``SoC_prev`` / ``mass_H2_prev`` so frame-to-frame inventory
  links are not overwritten by ``soc_initial`` / ``H2_mass_initial``.

## [0.6.2] - 2026-07-29

### Added
- **Linear multi-period TEP** (`ACDC_L_TEP.linear_multi_period_transmission_expansion`):
  MILP counterpart of multi-period TEP (AC-only; default solver Gurobi), with
  shared investment/decommission handling and `MP_TEP_obj_res` / `MP_TEP_results`
  export. Doc example
  `pyflow_tests/doc_examples/L_models/04_linear_mp_tep_case24.py` (``build_only=True``)
  and `pyflow_tests/test_linear_mp_tep.py`.
- **NL OPF post-process** for linear MP-TEP: optional ``post_process_nl_opf`` /
  ``nl_solver`` re-solves a single-state NL OPF per investment period after a
  successful MILP. Results go to ``grid.MP_TEP_nl_obj_res`` (same column schema
  as linear ``MP_TEP_obj_res``); NL always uses ``obj_scaling=1.0``. Failed period
  NL solves soft-fail with NaNs and do not block the run. When post-processing,
  NL calls ``optimal_pf(..., export_if_feasible=True)`` so an infeasible NL does
  **not** export onto the grid (normal user OPF still always exports).
- **Period SVGs** for linear MP-TEP: ``save_period_svgs`` / ``period_svg_prefix``
  write one SVG per period from the assigned investment state (``np_*``, loads),
  independent of NL OPF success.
- **Results**: ``mp_tep_nl_obj_res`` table / Excel sheet ``MP_TEP_nl_obj_res``.
- **`optimal_pf`**: optional ``export_if_feasible`` (default ``False``) to skip
  grid export when no feasible solution was found.

### Changed
- Linear static TEP helpers consolidated under ``ACDC_L_TEP.py`` (linear MP driver
  lives there alongside static linear TEP).
- ``log_infeasible_constraints_limited`` prints Pyomo-style
  ``INFO: CONSTR ... =/= 0.0`` lines (avoids ``NumericConstant`` formatting
  crashes when dumping infeasible NL OPFs).

## [0.6.1] - 2026-07-21

### Added
- **Linear models docs**: `docs/api/L_models.rst` and doc examples for linear
  transmission expansion, reconductoring, and linear OPF (`L_models/01`–`03`).

### Changed
- Linear OPF / TEP model improvements (`AC_OPF_L_model.py`) and related API/doc
  wiring (`usage_tep.rst`, TEP doc examples).

## [0.6.0] - 2026-06-16

### Added
- **Sequential STEP** (`ACDC_sequential_STEP.py`): `sequential_STEP` and
  `sequential_MS_STEP` run static transmission expansion sequentially across
  time frames (single- and multi-scenario), tracking per-element installation
  (`np_gen`/`np_rsgen`/`np_line`/`np_conv`) over the horizon; `export_results_to_csv`
  persists the run results.
- **Solver utilities** (`solver_utils.py`): `check_available_solvers` detects which
  Pyomo solvers and OR-Tools backends are actually installed.
- **Multi-period TEP — time-series OPF per investment period**:
  `run_ts_opf_for_investment_period` (alongside the existing
  `run_opf_for_investment_period`).
- **Dash / interactive visualization** (`Graph_Dash.py`): `run_ts_dash`,
  `run_mp_ts_dash`, `create_mp_ts_dash`, `plot_TS_res_from_ts`, `plot_TS_res_dash`
  for time-series and multi-period result exploration.
- **Folium map plotting**: `plot_folium` and `plot_folium_network` for geographic
  network rendering.
- **Clustering**: `load_precomputed_clusters_to_grid` plus forced-cluster support
  and correlation-identification improvements in `Time_series_clustering.py`.
- **Example grids reorganized** into `PF/`, `OPF/`, `TEP/`, and `Wind_Array/`
  subfolders; the case loader now walks these folders (qualified module names).
  New cases: `case1888rte`, `case3120sp_acdc` (OPF) and `CigreB4_ACDC` (PF). Added
  `Moray_East` wind-farm data; removed the obsolete `generate_grids.py`.
- **Tests**: fast fake-solve harness (`_quick_fake_solve.py`,
  `test_OPF_quick_runner.py`) and plotting tests (`test_plot.py`).
- `CONTRIBUTING.md`, `CHANGELOG.md`, and `ARCHITECTURE.md` (docs include via
  `docs/architecture.md`).
- Centralised string-as-enum constants in `pyflow_acdc/constants.py`:
  `ObjComponent`, `CssMode`, `MIPBackend`, `PricingStrategy`, `TSType`
  (plus the `TS_RENEWABLE_TYPES` group), and a `default_obj_weights()` factory.
- `__all__` is now defined on every module, making the public surface explicit.
- `pyflow_acdc/depreciation_methods.py`: deprecated mixed-case aliases (both
  module-level functions and `Results` methods) that forward to the snake_case
  implementations and emit `DeprecationWarning`.
- `pyproject.toml`: `keywords`, a `Homepage` URL, and `pytest-cov` in the
  `[tests]` extra.
- `ts_ac_pf` and `ts_dc_pf`: AC-only and DC-only time-series power-flow
  helpers (mirroring `ts_acdc_pf`), exported at the top level.

### Changed
- **`pyomo_model_solve` reworked**: supports solver options and callbacks, a
  robust retry path, constraint-tightening/feasibility handling for hard
  multi-period runs, and richer solver-statistics reporting.
- **Multi-period TEP substantially extended** (`ACDC_MultiPeriod_TEP.py`):
  installation ranges over planned values, decommissioning periods, time-series
  net-power reporting, and per-investment-period result exports / SVG output.
- **PGL min/max physical constraints** added for renewable/load power bounds in
  the OPF/TEP formulations.
- **Array optimization** (`Array_OPT.py`): added an array-loss objective term and
  fixed cable-sizing/CSS behavior.
- **OPF/TS multiplicity (`np`) handling aligned** across the OPF and time-series
  paths, and time-series line outputs were cleaned up for consistent reporting.
- **Mapping/Folium cleanup**: planar-layout fix and SVG export scaling.
- Objective-weight defaults are now built from a single factory instead of
  three duplicated literal dicts.
- Node active/reactive generation expressions are centralized on `Node_AC`
  (`gen_P_injection`, `gen_Q_injection`, `gen_P_total`, `gen_Q_total`,
  `gen_P_node_aggregate`), replacing duplicated formulas in `Time_series`,
  `Results_class`, and `Graph_and_plot`. The slack and PV reactive
  back-calculations (which were identical) now share `gen_Q_injection`.
  **Behavior change:** the non-OPF forward generation sums now scale per-unit
  generator/renewable output by the parallel-unit counts (`np_gen` /
  `np_rsgen`); previously these counts were ignored outside the OPF path.
- Power flow now populates per-node generation aggregates as a single source of
  truth: `Node_AC.PGi_ren`/`QGi_ren` (renewable: `Σ rs.PGi_ren*rs.gamma*rs.np_rsgen`
  active, `Σ rs.QGi_ren*rs.np_rsgen` reactive — reactive is not curtailed) and
  `Node_AC.PGi_opt`/`QGi_opt` (connected-generator dispatch: `Σ gen.PGen`/`Σ gen.QGen`).
  The known-power vectors are now `PGi + PGi_ren + PGi_opt - PLi` (and the reactive
  analog). The DC path mirrors the active side, and `Node_DC` gained `PGi_ren` /
  `PGi_opt` attributes. The converter `P_AC`/`Q_AC` back-calculation in
  `ACDC_PF.acdc_sequential` now reads these node attributes instead of recomputing
  the sums inline. **Behavior change:** for renewable sources with `np_rsgen > 1`
  the power-flow injection now includes the parallel-unit count (and the renewable
  reactive contribution, previously omitted entirely from `Q_AC`).
- `Gen_AC`/`Gen_DC` now initialize `PGen`/`QGen` as the **total** output
  (`Pset * np_gen` / `Qset * np_gen`) instead of the per-unit setpoint, making
  `PGen` consistently the total dispatch both before and after an OPF solve
  (`Pset`/`Qset` remain the per-unit inputs). The power-flow known-power vectors
  therefore use `Σ gen.PGen` / `Σ gen.QGen` directly. **Behavior change:** for
  generators with `np_gen > 1`, the power-flow injection and `PGen`-derived
  reporting (e.g. loading) now reflect the full parallel-unit output, which was
  previously omitted in the pre-OPF state.

### Removed
- `Node_AC.curtailment` (a node-level scalar that was always `1` and never
  assigned): curtailment is modeled per `Ren_Source` via `gamma`/`min_gamma`,
  and `PGi_ren` already reflects it, so the redundant factor was dropped from
  the node generation expressions.
- **Namespace narrowing:** accidentally re-exported internals (e.g.
  `pyflow_acdc.NodeType`) are no longer in the top-level namespace now that
  every module declares `__all__`. Use `pyflow_acdc.constants.<Name>` or a
  direct import. The documented `pyflow_acdc.__all__` API is unchanged.
- Docs: corrected class references (`rec_Line_AC`, `Size_selection`),
  refreshed the `Optimal_PF` signature, removed the unused `sphinx-rtd-theme`
  dependency, and updated the copyright year.
- **snake_case is now the default for the public API.** Public functions were
  renamed to snake_case (e.g. `Power_flow→power_flow`, `Create_grid_from_data→
  create_grid_from_data`, `Optimal_PF→optimal_pf`, `OPF_obj→opf_obj`,
  `Expand_element→expand_element`, `Translate_pyf_OPF→translate_pyf_opf`,
  `plot_Graph→plot_graph`, `results_TS_OPF→results_ts_opf`). The legacy
  mixed-case names remain importable as deprecated aliases (see below). The
  `grid.OPF_obj` attribute is unchanged (only the same-named function moved).
- **`Results` methods renamed to snake_case** (e.g. `res.All()→res.all()`,
  `res.AC_Powerflow()→res.ac_powerflow()`, `res.TEP_N()→res.tep_n()`). Old
  method names remain as deprecated aliases. Excel-sheet/table keys, `Grid`
  attributes, and the `Price_Zone` class are unchanged.
- **`Grid` methods renamed to snake_case** (e.g. `grid.Update_Graph_AC()→grid.update_graph_ac()`,
  `grid.Line_AC_calc()→grid.line_ac_calc()`, `grid.Check_SlacknDroop()→grid.check_slack_n_droop()`).
  Old method names remain as deprecated aliases on `Grid`.
- **Internal OPF/PF/TEP helpers renamed to snake_case** (e.g.
  `OPF_create_NLModel_ACDC→opf_create_nl_model_acdc`,
  `load_flow_AC→load_flow_ac`, `TEP_obj→tep_obj`,
  `Jacobian_conv→jacobian_conv`, `OPF_create_LModel_AC_gurobi→opf_create_l_model_ac_gurobi`).
  Submodule-only; no deprecation aliases added.
- **Multi-scenario TEP economics (`weighted_subobj`):** scenario weights `w[t]`
  carry each frame's share of the year; `Hy` (default 8760 h/y) scales per-hour
  OPF costs to annual. `create_scenarios` passes the full
  `present_value_factor(Hy, discount_rate, n_years)` (or `Hy` when `NPV=False`)
  into `weighted_subobj` — not a separate bug. Prior audit/CHANGELOG note about
  “missing `Hy`” was incorrect (looked at the helper body, not the caller).

### Fixed
- `plot_model_feasebility` renamed to `plot_model_feasibility` (public typo;
  old name kept as a deprecated alias).
- DC power-flow corrections and renewable/generator parallel-unit (`np_rsgen` /
  `np_gen`) export fixes.
- Sequential/multi-period solver robustness: `bonmin` exit handling and retry on
  solver failures during STEP/MP runs.
- `Export_files` no longer emits an unquoted `pricing_strategy=` value in
  generated loader code (which raised `NameError` when re-run).
- Removed a duplicate/unreachable `PZ_cost_of_generation` branch in
  `calculate_objective` (kept the `S_base`-scaled formula).
- Removed the invalid `Programming Language :: C` classifier from packaging
  metadata.
- `kappa_sensitivity` no longer references undefined `model.discount_rate`;
  it now uses `present_value_factor(Hy, discount_rate, n_years)` like the other
  TEP sensitivity helpers (fixes `AttributeError` at runtime).
- `Gen_set_dev` objective now compares like units: the setpoint deviation uses
  `gen.Pset * gen.np_gen` (total) instead of the per-unit `gen.Pset`, so the
  penalty is zero at the setpoint for generators with `np_gen > 1` (both the
  Pyomo objective and the post-solve `calculate_objective` path).
- `transmission_expansion_pymoo` now wires its `NPV` flag into
  `TEPOuterProblem`: when `NPV=False` the OPEX (and CAPEX) are no longer scaled
  by the present-value factor. Previously the flag was ignored and present value
  was always applied.
- `time_series_pf` no longer calls the non-existent `grid.TS_ACDC_PF` attribute
  (which raised `AttributeError` for AC/DC grids); it now routes to the
  module-level `ts_dc_pf` (DC-only), `ts_ac_pf` (AC-only), or `ts_acdc_pf`
  (sequential). Also replaced `== None` comparisons with `is None`.
