# Heat-pump flexible load plan for pyflow_acdc

**Repository:** In-repo links target the [`heat_pumps`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/heat_pumps) branch ([`plans/`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/heat_pumps/plans)).

Implementation plan for controllable **heat pumps** as AC flexible loads in the
nonlinear AC/DC OPF. Content was split out of `bess_integration_plan.md`; this
document is the sole plan for HP work.

**Primary reference**

M. Montalà-Palau, J. J. Markus, M. Kazemi, M. Cheah Mañé, C. Papadimitriou, and
O. Gomis-Bellmunt, *Enhancing Distribution System Resilience through Energy
Communities*, CIRED 2026 Brussels Workshop, Paper 1361, 2026.

- HP flexibility characterization: paper §3
- Planning-oriented HP + ESS resilience model: paper §4.1
- Operation-oriented FEL / reserve-envelope model: paper §4.2 (**deferred**)
- Local PDF: `citcea_extras_pyflow/heat_pumps_OPF/CIRED2026_Enhancing_Distribution_System_Resilience_through_Energy_Communities.pdf`
- Prototype: `citcea_extras_pyflow/heat_pumps_OPF/ILEC_full_code.py` (Montse)

**Related pyflow_acdc assets**

| Document | Link |
|----------|------|
| User guide | `docs/api/modelling_flexible_assets.rst` (heat-pump section) + `docs/usage_window_opf.rst` |
| API | `docs/api/grid_mod.rst` (`add_heat_pump`) + `docs/api/modelling_flexible_assets.rst` |
| BESS / H₂ operation (separate) | [bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/heat_pumps/plans/bess_integration_plan.md) |
| Tests | [pyflow_tests/test_heat_pump_opf.py](https://github.com/CITCEA-UPC/pyflow_acdc/blob/heat_pumps/pyflow_tests/test_heat_pump_opf.py) |
| Sibling plans | [plans/](https://github.com/CITCEA-UPC/pyflow_acdc/tree/heat_pumps/plans) |

---

## 0. Status

| Item | Status |
|------|--------|
| `HeatPump` class + `add_heat_pump` | Done |
| `grid.HP` / nodal hooks | Done |
| Snapshot NL OPF (`P_shed`, `Q_shed`, `E_heat_pump`) | Done |
| Myopic `ts_acdc_opf` energy-state carry | Done |
| Coupled `window_nl_opf` parent energy chain | Done |
| `Results.ext_heat_pump` / `heat_pump_window` | Done |
| Docs (`modelling_flexible_assets`, `grid_mod`) | Done |
| Tests (`test_heat_pump_opf.py`) | Done |
| TS types `hp_P_ref` / `hp_Q_ref` / `hp_E_min` / `hp_E_max` | Done |
| Operation-oriented FEL (`E_flex`, terminal neutrality) | Deferred |
| Post-solve reserve envelope (`R_up` / `R_down`) | Deferred |
| Linear OPF (`optimal_l_pf` / `ts_acdc_l_opf` / `window_l_opf`) P-only | Done |
| DC heat pumps | Out of scope (AC-only) |
| Inferred thermal / comfort model inside pyflow | Out of scope |

---

## 1. Role in the model

- Heat pumps are **controllable electrical loads** on AC buses.
- Flexibility is scheduling served demand around a **baseline** (`P_ref`, `Q_ref`) within instantaneous power bounds and a cumulative energy state tied to comfort envelopes supplied by the user.
- Planning-oriented formulation (v1, shipped): reduces / shifts electrical demand while keeping `E_state` inside `[E_min, E_max]`.
- Operation-oriented FEL + reserve reporting: paper §4.2 — **not implemented yet**.

---

## 2. Observed Montse pattern in `ILEC_full_code.py`

- Prototype keeps baseline demand as a non-controllable `load` and a controllable `"…_shedding"` `sgen` actuator.
- Admissible shedding range uses `num_con_load * 1.76 kW`, cumulative `LOAD_cap`, and time-varying `e_min` / `e_max`.
- Served power: `P_hp = P_baseline - P_shedding` (same for Q).

**pyflow v1 mapping:** optimize explicit `P_shed` / `Q_shed` with
`P_hp = P_ref - P_shed`, `Q_hp = Q_ref - Q_shed`. Shed costs in `Energy_cost`
on the shed vars (Montse shedding-sgen `cp*_loads_C` / `cq*_loads_C` pattern).

---

## 3. Shipped class and API

```python
class HeatPump:  # Classes.py
    heatPumpNumber
    connected = AcDcSide.AC
    # host Node_AC via connected_heat_pumps
```

| Attribute | Units / meaning |
|-----------|-----------------|
| `P_ref`, `Q_ref` | Baseline demand [pu on `S_base`] |
| `n_units`, `P_unit_max` | Active shed capability → `n_units * P_unit_max` [pu] |
| `Max_S` | Installed apparent-power rating [pu]; default `n_units * P_unit_max` |
| `Q_lim_shed` | `Max_S * Q_shed_lim_frac` [pu]; fixed at creation |
| `qf`, `lf`, `qf_q`, `lf_q` | `Energy_cost` coefficients on `P_shed` / `Q_shed` |
| `E_state`, `E_state_initial` | Cumulative energy state [kWh] |
| `E_min`, `E_max` | Comfort bounds on `E_state` [kWh] |
| `dt_hours` | Timestep duration [h] |
| `P_hp`, `Q_hp` | Served demand after solve [pu] |
| `P_shed`, `Q_shed` | Optimized shed after solve [pu] |

Public entry: `add_heat_pump(grid, node, *, P_ref_MW, Q_ref_MVAR=0, n_units, E_min_kWh, E_max_kWh, S_rated_MVAR=, q_shed_lim_frac=1, quadratic_cost_factor=0, …)` → appends to `grid.heat_pumps`. `analyse_grid` sets `grid.HP`.

Multi-hour overrides via `TSType`:

| `TSType` | String key | Units in series |
|----------|------------|-----------------|
| `HP_P_REF` | `hp_P_ref` | pu |
| `HP_Q_REF` | `hp_Q_ref` | pu |
| `HP_E_MIN` | `hp_E_min` | kWh |
| `HP_E_MAX` | `hp_E_max` | kWh |

---

## 4. Planning-oriented NL model (shipped)

### Snapshot / myopic (`window_block=False`)

Decision vars: `P_shed[h]`, `Q_shed[h]`, `E_heat_pump[h]`.

Expressions: `P_heat_pump = P_ref - P_shed`, `Q_heat_pump = Q_ref - Q_shed`.

Mutable params: `hp_p_ref`, `hp_q_ref`, `hp_e_min`, `hp_e_max`, `E_heat_pump_prev`.

Bounds (every frame):

```text
0 <= P_shed <= n_units * P_unit_max
-Q_lim_shed <= Q_shed <= Q_lim_shed
E_min <= E <= E_max
```

Energy balance and energy-linked P_shed bounds (skip when `window_block`):

```text
E = E_prev + P_hp * S_base * dt_hours          # E in kWh; P_hp in pu
P_shed >= E_min/dt - E_prev/dt
P_shed <= E_max/dt - E_prev/dt
```

Nodal load hook (`Gen_Pheatpump_constraint`): subtract `P_heat_pump` / `Q_heat_pump` from AC nodal injection (same load sign as electrolyser / load).

`Energy_cost`: `P_shed²·qf + P_shed·lf` and Q twin (MW/MVAR via `S_base`).

### Window (`window_nl_opf`)

- Each frame built with `window_block=True` → instantaneous P/Q/E bounds only; no in-block `E_prev` balance.
- Parent `window_heat_pump_constraints` chains `E_heat_pump` across `frame_model[t]` from `hp_energy_initial` (current `hp.E_state`).

### Time series (`ts_acdc_opf`)

- Each hour: update TS (`hp_*`), set `E_heat_pump_prev` from carried `hp.E_state`, solve, export / carry `E_state`.

### Linear OPF (P-only, shipped)

Same `P_shed` / `E_heat_pump` formulation as NL on `optimal_l_pf` / `ts_acdc_l_opf` / `window_l_opf`
(`heat_pump_variables_l` / `heat_pump_constraints_l`). Differences:

- `Q_shed` fixed at `Q_ref` (Param) → `Q_hp = 0`; no Q nodal injection.
- Only `P_shed` linear/quadratic costs in `Energy_cost`.
- Parent chain reuses `window_heat_pump_constraints`.

---

## 5. Results

| API | When |
|-----|------|
| `Results.ext_heat_pump()` | After snapshot OPF — P/Q served, shed, energy state |
| `Results.heat_pump_window()` | After `window_nl_opf` / `window_l_opf` — P/Q/E trajectories |
| `grid.time_series_results['heat_pump_p' / 'heat_pump_energy_state']` | After `ts_acdc_opf` / `ts_acdc_l_opf` |

---

## 6. File touch list (shipped)

| File | Changes |
|------|---------|
| `Classes.py` | `HeatPump`, `Grid.heat_pumps`, `Node_AC.connected_heat_pumps` |
| `grid_modifications.py` | `add_heat_pump()`, HP TS association |
| `grid_analysis.py` | `grid.HP` |
| `grid_creator.py` | init `heat_pumps` / `connected_heat_pumps` |
| `constants.py` | `TSType.HP_P_REF` / `HP_Q_REF` / `HP_E_MIN` / `HP_E_MAX` |
| `ACDC_OPF_NL_model.py` | `heat_pump_variables` / `heat_pump_constraints`, nodal hook, export |
| `ACDC_OPF.py` | `heat_pump_info` in OPF translate |
| `window_opf.py` | `window_heat_pump_constraints`, export frames |
| `Time_series.py` | HP TS update, myopic `E` carry, TS result keys |
| `AC_OPF_L_model.py` | `heat_pump_variables_l` / `heat_pump_constraints_l`, P nodal, export |
| `window_l_opf.py` | HP gate + `window_heat_pump_constraints` |
| `Time_series.py` | `_modify_parameters_l` HP params; `ts_acdc_l_opf` carry / TS keys |
| `Results_class.py` | `ext_heat_pump`, `heat_pump_window` |
| `__init__.py` | export `HeatPump`, `add_heat_pump` |
| `docs/api/modelling_flexible_assets.rst`, `docs/api/grid_mod.rst` | user + API docs |
| `pyflow_tests/test_heat_pump_opf.py` | bounds + TS + window smoke |

---

## 7. Deferred (paper §4.2 / Montse reserve)

Not in v1:

- Normalized FEL state `E_flex` with terminal neutrality `E_flex[t0] = E_flex[tn] = 0`
- Post-solve reserve envelopes `R_up` / `R_down` from power + comfort headroom

Keep planning-oriented `P_shed`/`Q_shed` model as the stable base; add FEL as a second step if needed.

---

## 8. Implementation notes (locked)

- Dedicated `HeatPump` — do not overload `Load` or `Storage`.
- Explicit baseline + envelope inputs only; no inferred house thermal dynamics.
- AC-only.
- Energy state in **kWh**; electrical powers in **pu** on grid `S_base`.
- Fail-fast on invalid `n_units`, `P_unit_max`, `dt_hours`, or `E_min > E_max` / initial outside bounds.
- No `getattr` on Pyomo model objects.
