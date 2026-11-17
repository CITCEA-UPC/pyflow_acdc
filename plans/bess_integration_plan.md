# BESS integration plan for pyflow_acdc

**Repository:** In-repo links target the [`mario_integration`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration) branch ([`plans/`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration/plans)).

Implementation plan for adding Battery Energy Storage Systems (BESS) and green
hydrogen to pyflow_acdc (NL OPF primary; linear AC OPF operation in Phase 9), based on:

- Mario Useche-Arteaga et al., *Wind Energ. Sci.* 11, 349–372 (2026) — §3.3 BESS model
- Reference script: `mario_implementation/18414805/OPF_ACDC_Energy_Islands.py`

## Documentation (GitHub / Read the Docs)

| Document | GitHub (`mario_integration`) | Read the Docs |
|----------|------------------------------|---------------|
| User guide (BESS) | [docs/usage_storage.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_storage.rst) | [usage_storage](https://pyflow-acdc.readthedocs.io/en/latest/usage_storage.html) |
| User guide (H₂) | [docs/usage_hydrogen.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_hydrogen.rst) | [usage_hydrogen](https://pyflow-acdc.readthedocs.io/en/latest/usage_hydrogen.html) |
| Window / rolling | [docs/usage_window_opf.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_window_opf.rst) | [usage_window_opf](https://pyflow-acdc.readthedocs.io/en/latest/usage_window_opf.html) |
| Linear OPF API | [docs/api/L_models.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/api/L_models.rst) | [api/L_models](https://pyflow-acdc.readthedocs.io/en/latest/api/L_models.html) |
| API reference | [docs/api/storage.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/api/storage.rst) | [api/storage](https://pyflow-acdc.readthedocs.io/en/latest/api/storage.html) |
| This plan | [plans/bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) | — |
| Sibling plans | [plans/](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration/plans) | — |

---

## 1. Decisions (resolved gaps)

| ID | Topic | Decision |
|----|--------|----------|
| G1 | Scope | **Phases 0–8 done** (BESS, H₂, PEI window, rolling, myopic TS). **Phase 9** — linear AC OPF operation (`optimal_l_pf`) for AC-connected BESS / H₂. **Docs:** concurrent track. **TEP sizing** remains out of scope. |
| G2 | OPF modes | **NL OPF** is primary (full AC/DC, Q, S-circle). **Linear AC OPF** (`optimal_l_pf`) supports BESS (P-only) + electrolyser inventory / `H2_sale` on **AC-only** grids; raises if `grid.DCmode`; `SoC_deviation` rejected (quadratic). **No TEP sizing.** |
| G3 | Multi-hour optimization | **Coupled horizon** in a new top-level script `window_opf.py`; BESS constraints live **inside the NL model** (not a post-processing layer) |
| G4 | Time series (`ts_acdc_opf`) | **Phase 8** — **myopic / forward-only** SoC: one snapshot NL OPF per hour with `SoC_prev` carry. Soft **`soc_ref`** (class attr + mutable Param, init = `soc_initial`) via quadratic `SoC_deviation` in `ObjRule`. **H₂:** inventory carries within `H2_mass_max`; out-of-opt **`empty_tank_cycle`** empties (`None` = never empty in myopic; `N` = empty every `N` hours). Sale economics via `H2_sale` / `H2_PRICE`. Window/rolling: `None` empties every window boundary; `N` empties at commit ends `≥ k·N`. Hard `H2_mass_final` remains window/rolling only. Not equivalent to `window_nl_opf`. |
| G5 | SoC units | **SoC in pu** in the Pyomo model; physical capacity via class attribute **`E_max` [MWh]** (enables future degradation modelling on `E_max`) |
| G6 | Simultaneous charge/discharge | Keep Mario/paper formulation (separate `P_charge` / `P_discharge` vars, no exclusivity binary). Optimizer should cancel overlap in practice. **Add code comment: revisit later** if artefacts appear |
| G7 | Apparent-power limit | **Per element**, side-dependent (mirrors `Ren_Source`): AC — `(P_dis − P_ch)² + Q² ≤ S_max²`; DC — active power only, `|P_dis − P_ch| ≤ P_max` (no `Q`, no S-circle) |
| G8 | Validation | **Phase 6** — single 24 h PEI `window_nl_opf` vs Mario paper/script (BESS + H₂ + exports + revenue) |
| G9 | PEI hub node | Mario uses index `0` (offshore hub). In `PEI_grid.py` the equivalent bus is **`PE_Island`** (220 kV PV hub). Confirm index mapping during validation setup |
| G10 | Public API | **`add_storage(grid, node, ...)`** in `grid_modifications.py` |
| G11 | Economics | **Operation only** — no CAPEX / investment variables |

### Phase 4 implementation (locked)

| ID | Topic | Decision |
|----|--------|----------|
| P4-1 | SoC coupling | **Parent `window_soc_links` only** — chain SoC across `hour_model[t]`; each block keeps **power limits only** (charge/discharge bounds, AC S-circle, DC `P_max`). |
| P4-1a | `window_block=True` | **Skip** in-block use of `soc_initial` / `SoC_prev ← soc_initial` and **`storage_soc_balance`** (parent owns dynamics). **Remove** `storage_soc_final_*` in blocks. Standalone `optimal_pf` (no flag) keeps Phase 2 snapshot behaviour including `soc_initial` / optional `soc_final`. |
| P4-1b | Energy state (future) | Comment in code/plan: parent links may later use **actual energy** [MWh] (or `SoC × E_max_eff`) instead of pu SoC, to support **capacity degradation** / time-varying `E_max`. Phase 4 v1 stays **pu SoC** links. |
| P4-2 | Builder API | **`opf_create_nl_model_acdc(..., window_block=True)`** — snapshot builder with block-specific SoC omissions; **`window_opf.py`** assembles blocks + parent links + objective. |
| P4-3 | Objective | **No new objective terms in Phase 4** — `model.obj = sum_t opf_obj(hour_model[t], …)` using existing per-block operational objectives only. Soft SoC reference (`SoC_deviation`) arrives in **Phase 8** for **`ts_acdc_opf`** only; window keeps hard ini/final SoC. |
| P4-4 | Hour indexing | **Python convention:** block indices `t ∈ {0, …, T−1}` aligned with `Time_series` row indexing (0-based). |
| P4-5 | Block build | **Clone structure** (cf. `multi_scenario_TEP`: build template once, `clone()` per hour, patch mutable params). |
| P4-6 | Window scope (v1) | **Single coupled window per call** (e.g. one 24 h solve). **Rolling / sliding window** → **Phase 7**, after Phase 6 validation. |

### Architecture principle

Hooks mirror **`Gen_AC` / `Gen_DC` / `Ren_Source`**:

- `Storage_AC` / `Storage_DC` classes (`storageNumber` / `storageNumber_DC`)
- `Node_AC.connected_storage` and `Node_DC.connected_storage`
- `Grid.storage_elements` (both sides in one list, like `RenSources`)
- Nodal aggregation: `PGi_storage` / `QGi_storage` (AC) and `PGi_storage_DC` (DC only)
- `connected` flag (`AcDcSide.AC` / `AcDcSide.DC`) — same branching pattern as `Ren_Source.connected` in the NL model

### Run modes (by design)

```
┌─────────────────────────────────────────────────────────────────┐
│  window_opf.py            Coupled multi-hour NLP (paper-faithful) │
│  window_nl_opf()            Parent SoC (+ H₂) links               │
│  rolling_window_nl_opf()    Chained windows (Phase 7)             │
├─────────────────────────────────────────────────────────────────┤
│  ts_acdc_opf (Phase 8)    Myopic / forward-only hours (G4)        │
│  ─────────────────        SoC_prev ← previous SoC* each hour      │
│                           Soft soc_ref via ObjRule SoC_deviation  │
│                           H₂: inventory + empty_tank_cycle        │
├─────────────────────────────────────────────────────────────────┤
│  optimal_l_pf (Phase 9)   Linear AC OPF — AC BESS P-only + AC H₂ │
│  ─────────────────        Energy_cost + H2_sale; no SoC_deviation │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical model (NL)

Reference: paper Eqs. (24)–(31), Mario script lines 584–605 (AC hub BESS only).

### 2.1 Shared (AC and DC)

**Variables (pu on `grid.S_base`, per element `s`, per time `t` when window OPF)**

| Symbol | Pyomo name (proposed) | AC | DC |
|--------|----------------------|----|----|
| `P^c_{s,t}` | `P_storage_charge[...]` | ✓ | ✓ |
| `P^d_{s,t}` | `P_storage_discharge[...]` | ✓ | ✓ |
| `Q^b_{s,t}` | `Q_storage[...]` | ✓ | — |
| `e_{s,t}` | `SoC[...]` | ✓ | ✓ |

**Parameters (class attributes)**

| Symbol | `Storage_AC` | `Storage_DC` |
|--------|--------------|--------------|
| `E_max` [MWh] | ✓ | ✓ |
| `η_c`, `η_d` | ✓ | ✓ |
| `soc_min`, `soc_max`, `soc_initial`, `soc_final`, `soc_ref` | ✓ | ✓ |
| `P_charge_max`, `P_discharge_max` [pu] | ✓ | ✓ |
| `S_max` [pu] | apparent-power rating | — |
| `P_max` [pu] | — | max active-power rating |
| `Δt` | `dt_hours` | `dt_hours` |

**SoC dynamics** (same both sides):

```
SoC[s,t] = SoC[s,t-1] + (dt / E_max[s]) * (eta_c * P_charge[s,t] - P_discharge[s,t] / eta_d)
```

Plus terminal SoC (horizon modes), bounds on SoC, and separate charge/discharge power bounds (G6 note unchanged).

**Soft SoC reference (Phase 8 — myopic `ts_acdc_opf`)** — secondary objective term, not a hard constraint:

```
J_SoC_dev = w * Σ_s (SoC[s] - soc_ref[s])**2
```

- **Quadratic only** — absolute deviation is avoided (Pyomo / IPOPT handle abs poorly).
- ``soc_ref`` is a **class attribute** (fixed scalar, init = ``soc_initial``) and a **mutable Param** in the NL model so a future per-frame / TS update path is possible without rebuilding the model.
- ``w`` uses the **existing ``ObjRule`` weighting** mechanism (same as ``Energy_cost``, ``H2_sale``, …). Scaling semantics may be revised later.
- Active when ``ObjRule['SoC_deviation']`` weight ``> 0``. Entices return toward ``soc_ref`` after discharge under myopic foresight.
- **Window modes** keep hard ``soc_initial`` / ``soc_final`` constraints; soft ``SoC_deviation`` is **not** part of Phase 8 window policy.

**Net active injection** (generation convention):

```
P_storage_net[s,t] = P_discharge[s,t] - P_charge[s,t]
```

### 2.2 AC vs DC power limits — mirror `Ren_Source`

Today in `ACDC_OPF_NL_model.py`, renewables branch on `ren_source.connected`:

```python
# Q bounds: AC only (DC → (0, 0))
# S-circle: S_renS_AC_limit_rule skips when connected == 'DC' or Max_S is None
#   (P*gamma)^2 + Q^2 <= Max_S^2   # AC only
# DC nodal sum → PGi_ren_DC[node]; no QGi_ren on DC
```

Storage should follow the **same split**:

| Aspect | AC (`Storage_AC`) | DC (`Storage_DC`) |
|--------|-------------------|-------------------|
| Reactive var `Q` | `Q_storage[s]` with free bounds (or ±`S_max`) | **None** — do not create `Q_storage` for DC indices |
| Converter / S-limit | Paper Eq. (30)–(31): `(P_d − P_c)² + Q² ≤ S_max²` per element | **No S-circle.** Net active limit: `|P_d − P_c| ≤ P_max` (equivalently two linear bounds, or rely on `P_charge_max` / `P_discharge_max` if `P_max = max(...)` ) |
| Nodal P aggregation | `PGi_storage[node]` = Σ `P_storage_net` over `node.connected_storage` (AC elements only) | `PGi_storage_DC[node]` = Σ `P_storage_net` (DC elements only) — parallel to `PGi_ren` / `PGi_ren_DC` |
| Nodal Q aggregation | `QGi_storage[node]` = Σ `Q_storage` → added to `Q_AC_node_rule` | **Skip** — no term in DC balance |
| Pyomo sets | `model.storage_AC` indexed by `storageNumber` | `model.storage_DC` indexed by `storageNumber_DC` |
| Export | write `P_charge`, `P_discharge`, `Q`, `SoC` on element | write `P_charge`, `P_discharge`, `SoC` only |

**AC apparent-power constraint** (element-level, not nodal — G7):

```
(P_discharge[s,t] - P_charge[s,t])**2 + Q_storage[s,t]**2 <= S_max[s]**2
```

**DC active-power constraint** (element-level):

```
P_discharge[s,t] - P_charge[s,t] <= P_max[s]
P_charge[s,t] - P_discharge[s,t] <= P_max[s]
```

(or `Constraint.Skip` if `P_max` already equals separate charge/discharge caps and bounds are sufficient — prefer explicit `P_max` rule for parity with class `loading` and future asymmetric ratings)

**Reference mapping in existing code**

| Ren_Source pattern | Storage equivalent (Phase 2) |
|--------------------|------------------------------|
| `S_renS_AC_limit_rule` | `S_storage_AC_limit_rule` on `model.storage_AC` |
| `Qren_bounds` → AC only | `Q_storage` vars / bounds on AC set only |
| `PGi_ren` + `Gen_PREN_rule` (AC nodes) | `PGi_storage` + `Gen_Pstorage_AC_rule` |
| `PGi_ren_DC` + `Gen_PREN_rule` (DC nodes) | `PGi_storage_DC` + `Gen_Pstorage_DC_rule` |
| `P_AC_node_rule`: `P_var += …` | `P_var += PGi_storage[node]` |
| `P_DC_node_rule`: `P_var += …` | `P_var += PGi_storage_DC[node]` |
| `Q_AC_node_rule`: `Q_var += …` | `Q_var += QGi_storage[node]` |

Mario PEI case remains **AC-only** (`Storage_AC` on `PE_Island`); DC storage is for general hybrid grids.

### 2.3 Nodal balance (summary)

AC (`P_AC_node_rule` / `Q_AC_node_rule`):

```
P_var += PGi_storage[node,t]
Q_var += QGi_storage[node,t]
```

DC (`P_DC_node_rule`):

```
P_var += PGi_storage_DC[node,t]
```

### 2.4 Green hydrogen / electrolyser (paper §3.4 — **Phase 5**)

Reference: paper Eqs. (32)–(36); Mario script lines 608–630, hub nodal balance line 658; Table 1 (PEI parameters).

**Variables (per electrolyser element `e`, frame `t` when window OPF)**

| Symbol | Pyomo name (proposed) | Unit / base |
|--------|----------------------|-------------|
| `P^e_{e,t}` | `P_electrolyser[e]` | pu on `grid.S_base` (active **load**) |
| `M_{e,t}` | `M_H2[e]` | cumulative H₂ inventory **[kg]** (paper `M_t`) |
| `h_{e,t}` | (auxiliary or inline) | H₂ produced in frame **[kg]** |

**Parameters (class attributes — PEI values from paper Table 1 / Mario)**

| Symbol | `Electrolyser_AC` attr | Mario / paper |
|--------|------------------------|---------------|
| `P^e_max` | `P_max` [pu] | 150 MW → pu via `S_base` |
| `P^e_min` | `P_min` [pu] | 22.5 MW (15 % of nominal) |
| `b_h` | `b_h` [kg/MWh] | 16.0585 (Mario) / 16.058 (Table 1) |
| `c_h` | `c_h` [kg] | 8.2195 (Mario) / 8.219 (Table 1) |
| `M_max` | `M_max` [kg] | 43 448 (Table 1) or `P_max_MW * 24 / eta_MWh_per_kg` with `ne = 58e-3` MWh/kg (Mario) |
| `M_initial`, `M_final` | `M_initial`, `M_final` [kg] | Mario: `MH2_ini=0`, `MH2_fin=0.7·P_h·24/ne` |
| `Δt` | `dt_hours` | 1 h (default; same as BESS frames) |

**Dynamics** (paper Eqs. 32–33):

```
h[e,t] = b_h[e] · P_e[e,t] · S_base · dt_hours + c_h[e]     # every frame (paper Eq. 32–33)
M[e,t] = M[e,t−1] + h[e,t]   (t = 0: M[e,−1] ≡ H2_mass_initial)
```

Paper and reference script both include **`c_h` in every hourly increment** (not only at `t = 0`). The script `OPF_ACDC_Energy_Islands.py` lines 626–630:

```python
if t == 0:
    MH[t] == b_h * Pe[t] * (Sbase*1e-6) + c_h
else:
    MH[t] == MH[t-1] + b_h * Pe[t] * (Sbase*1e-6) + c_h
```

*(An older plan note incorrectly showed `c_h` omitted in the `else` branch — that was a documentation error.)*

**Bounds & terminal** (paper Eqs. 34–36):

```
0 ≤ M[e,t] ≤ M_max[e]
M[e, t_last] = M_final[e]   (when set — parent link in window_nl_opf only)
P_min[e] ≤ P_e[e,t] ≤ P_max[e]
```

**Nodal balance (AC hub — load convention)**

At the connected AC node (Mario node `0` / pyflow `PE_Island`):

```
P_var[node] -= P_electrolyser[e]    # alongside BESS ±P and wind ±P
```

No reactive power term (electrolyser is active load only).

**Run modes (mirror BESS)**

| Mode | Inventory dynamics | Terminal `M_final` |
|------|-------------------|---------------------|
| Snapshot `optimal_pf` (1 frame) | Single-step from `M_initial` | **No** (same policy as snapshot BESS: no terminal SoC) |
| `window_nl_opf` | Parent `window_h2_links` across `frame_model[t]` | **Yes** @ last frame when set |

## 3. Implementation phases

> **Numbering note:** Former **Phase 5** (BESS-only Mario validation) was **deleted** and folded into **Phase 6** (full coupled BESS + H₂ + exports). Phases **0–8** are the original NL track; **Phase 9** adds linear AC OPF operation. **TEP sizing** remains out of scope. **Documentation** is a **concurrent** track at the end of §3 — update docs with each phase, not as a blocking gate.

### Phase 0 — Design freeze

**Goal:** Lock interfaces before coding.

**Tasks**

- [x] Confirm `PE_Island` as Mario hub mapping for validation (G9)
- [x] Fix sign convention docstring on `Storage_AC` (discharge = positive injection)
- [x] Define `dt_hours` default (= 1) on `Storage_AC`; window length remains a `window_opf` argument

**Deliverable:** This document approved; no open blocking questions.

---

### Phase 1 — Storage classes and grid hooks ✅

**Files:** `Classes.py`, `grid_modifications.py`, `grid_analysis.py`, `__init__.py`

#### 1.1 `Storage_AC` / `Storage_DC` (`Classes.py`)

Mirror `Gen_AC` / `Gen_DC` + `Ren_Source` connectivity:

```python
class Storage_AC:
    storageNumber, connected = AcDcSide.AC
    # S_max, Q, Node_AC, ...

class Storage_DC:
    storageNumber_DC, connected = AcDcSide.DC
    # P_max (no Q), Node_DC, ...
```

- `node.connected_storage.append(self)` on AC or DC host
- `reset_class()` for tests
- `S_base` setter rescales pu ratings

#### 1.2 `Grid` hooks

```python
self.storage_elements = []  # both Storage_AC and Storage_DC
```

- Property `nstorage`
- TS result keys: `storage_soc`, `storage_p_charge`, `storage_p_discharge`, `storage_q` (Q columns N/A or zero for DC in export)

#### 1.3 `Node_AC` / `Node_DC`

```python
self.connected_storage = []
```

#### 1.4 `add_storage()` (`grid_modifications.py`)

- `_look_up_node(..., ac_or_dc="any")` → `Storage_AC` or `Storage_DC`
- AC: `S_max_MVA` → apparent-power rating
- DC: `S_max_MVA` interpreted as **max active power MW** → `P_max`

#### 1.5 `analyse_grid`

- `grid.ESS = bool(grid.storage_elements)`

**Exit criteria:** Grid with `add_storage` builds; element appears on correct node; no OPF yet. ✅ Done (Phase 1)

---

### Phase 2 — NL model: BESS in `ACDC_OPF_NL_model.py`

**Goal:** BESS variables and constraints inside the existing NL builder (snapshot / single hour). **Branch AC/DC like `Ren_Source`** (§2.2 mathematical split).

#### 2.1 Snapshot mode — single hour ✅

When `grid.storage_elements` non-empty:

**Sets**

- `model.storage_AC` ← `[s.storageNumber for s in grid.storage_elements if s.connected == AcDcSide.AC]`
- `model.storage_DC` ← `[s.storageNumber_DC for s in grid.storage_elements if s.connected == AcDcSide.DC]`

**Variables**

| Var | Index | AC | DC |
|-----|-------|----|----|
| `P_storage_charge` | element id | ✓ | ✓ |
| `P_storage_discharge` | element id | ✓ | ✓ |
| `Q_storage` | `storageNumber` | ✓ | — |
| `SoC` | element id | ✓ | ✓ |
| `SoC_prev` | Param, mutable | ✓ | ✓ |

**Element constraints**

- SoC balance (one step), SoC bounds, charge/discharge bounds — both sides
- **AC:** `S_storage_AC_limit_rule` — `(P_d - P_c)² + Q² ≤ S_max²` (cf. `S_renS_AC_limit_rule`)
- **DC:** `P_storage_DC_net_limit_rule` — `|P_d - P_c| ≤ P_max` (cf. ren DC skipping S-circle; active limits only)
- G6 comment on charge/discharge overlap at both constraint sites

**Nodal aggregation** (cf. `Gen_PREN_rule` / `Gen_PREN_rule` on DC)

- AC: `PGi_storage[node]`, `QGi_storage[node]` from `node.connected_storage` (filter AC elements)
- DC: `PGi_storage_DC[node]` from DC-connected storage only

**Balance hooks**

- `P_AC_node_rule` / `Q_AC_node_rule`: add `PGi_storage`, `QGi_storage`
- `P_DC_node_rule`: add `PGi_storage_DC`

Gate entire block on `grid.ESS` (same as checking `RenSources` before building ren sets).

#### 2.2 Export (`export_acdc_nl_model_to_pyflow_acdc`) ✅

Map solved values back to each element:

| Field | `Storage_AC` | `Storage_DC` |
|-------|--------------|--------------|
| `P_charge`, `P_discharge`, `SoC` | ✓ | ✓ |
| `Q` | ✓ | — (leave unset / 0) |

Loop `grid.storage_elements` and branch on `connected` (same pattern as ren export at ~line 2259).

**Exit criteria:** Single-hour OPF with AC and DC storage on a hybrid toy grid; AC S-circle and DC P-only limits satisfied; export to `storage_elements`. ✅ Done (Phase 2)

---

### Phase 3 — `Results_class.py`

**Goal:** Reporting consistent with `ext_gen` / `ext_ren`.

#### 3.1 `ext_storage(print_table=True)`

Snapshot table per element:

| Column | Unit |
|--------|------|
| Name, Node, Side (AC/DC) | — |
| P charge / P discharge | MW |
| Q | MVAr (AC only; omit or “—” for DC) |
| SoC | pu (and MWh = SoC × E_max) |
| Loading | % (`S_max` AC / `P_max` DC) |

#### 3.2 `storage_window(print_table=True)` (window OPF)

- Hourly SoC, P_charge, P_discharge, Q per element
- Summary: energy charged/discharged [MWh], round-trip efficiency

#### 3.3 Wire into `Results.all()`

```python
if self.Grid.storage_elements:
    self.ext_storage(print_table=print_table)
if getattr(self.Grid, "window_opf_run", False):
    self.storage_window(print_table=print_table)
```

#### 3.4 Excel / CSV

- Add sheets to existing export paths when `save_res=True`

**Exit criteria:** `Results(grid).all()` prints storage table after OPF. ✅ Done (Phase 3.1)

---

### Phase 4 — Coupled horizon: time-indexed NL model + `window_opf.py`

**Goal:** Paper-faithful multi-hour NLP — extend the NL builder with a time index **and** add a separate top-level runner (not inside `ts_acdc_opf`).

> Snapshot BESS (Phase 2) stays the default for `optimal_pf`. Phase 4 adds `horizon=T` and `window_opf.py` together.

#### 4.1 Coupled window model — hour blocks + parent SoC links

**Pattern:** mirror `multi_scenario_TEP` (`model.hour_model[t] = pyo.Block(...)`) — **not** a full `(node, t)` re-index of the NL model.

```
model
├── hour_model[t]     ← opf_create_nl_model_acdc(..., window_block=True), t ∈ [0, T−1]
│   └── snapshot NL OPF + storage power limits (no in-block SoC boundaries)
└── window_soc_links  ← parent level only (P4-1)
    ├── t = 0:        anchor from soc_initial (+ dynamics using hour 0 dispatch)
    ├── t = 1…T−1:    SoC[s,t] = SoC[s,t−1] + Δt/E_max · (η_c P_c − P_d/η_d)
    └── t = T−1:      SoC[s,T−1] = soc_final[s]  (when set)
    # Future (P4-1b): link actual energy [MWh] or SoC×E_max_eff for degradation
    # Future: window_dc_ramp_links — same parent pattern (not Phase 4 v1):
    #   |P_line[t] − P_line[t−1]| ≤ ramp_max[line] · Δt  on selected DC lines
```

**Per-block vs parent (P4-1, P4-1a)**

| In each `hour_model[t]` (`window_block=True`) | At parent only |
|-----------------------------------------------|----------------|
| `P_charge`, `P_discharge`, `Q`, `SoC` vars + bounds | `soc_initial` @ **t = 0** |
| AC S-circle, DC `P_max`, charge/discharge caps | SoC chain @ **t = 1…T−1** |
| **Skip** `SoC_prev ← soc_initial` and **`storage_soc_balance`** | `soc_final` @ **t = T−1** (when set) |
| **Omit** `storage_soc_final_*` | |

Standalone `optimal_pf` (no `window_block`) unchanged: `SoC_prev = soc_initial`, one-step balance, optional `storage_soc_final_*`.

**Build (P4-2, P4-5)**

1. Build one template snapshot via `opf_create_nl_model_acdc(..., window_block=True)`.
2. For each `t`: `clone()` → `hour_model[t]`, patch hourly params from `Time_series` (cf. `_modify_parameters`).
3. Add parent `window_soc_constraints` + `sum_t` objective (P4-3).

Reference: `ACDC_Static_TEP.multi_scenario_TEP` + `MS_TEP_constraints`.

> **Future — same hour-block / parent-link pattern:** **DC line ramp-rate limits** between consecutive hours, e.g. on `hour_model[t].PDC_to[line]` / `PDC_from[line]`:
>
> `|P_line[t] − P_line[t−1]| ≤ ramp_max[line] · Δt_hours` (pu or MW rating on the line class).
>
> Defer until after BESS window OPF is stable; requires `ramp_max` (or similar) on `Line_DC` / grid data.

#### 4.2 Runner — `window_opf.py` (single window, v1)

**New file:** `pyflow_acdc/window_opf.py`

```python
def window_opf(
    grid,
    start=0,
    end=23,
    ObjRule=None,
    solver="ipopt",
    tee=False,
    ...
):
    """
    Build one coupled NL model over hours start…end (0-based, inclusive).
    Phase 4 v1: single window per call (e.g. 24 h). Rolling windows → **Phase 7**.
    Updates ren availability and prices per hour from grid.Time_series.
    Solves once; exports trajectory to grid + storage_elements.
    Sets grid.window_opf_run = True.
    """
```

**Responsibilities**

1. `analyse_grid(grid)`
2. Apply hourly data from `Time_series` into each block (cf. `update_grid_scenario_frame` + `_modify_parameters`)
3. Clone template → `model.hour_model[t]` for `t ∈ range(start, end + 1)` with `window_block=True`
4. Add parent `window_soc_constraints` (P4-1)
5. `model.obj = sum_t opf_obj(hour_model[t], …)` — **no new objective terms** (P4-3)
6. `pyomo_model_solve`
7. Window export → `grid.window_opf_results` DataFrames

**Grid flag:** `grid.window_opf_run = True` (set in `reset_run_flags` companion or window entry)

**Export in `__init__.py`:** `from .window_opf import window_opf`

**Exit criteria:** One coupled 24 h window on PEI completes; SoC obeys terminal constraint.

---

### Phase 5 — Green hydrogen / electrolyser (NL + `window_nl_opf`)

**Goal:** Paper-faithful **linear electrolyser + H₂ inventory** model (§3.4, Eqs. 32–36), co-optimized with BESS and AC/DC OPF on the PEI hub — same element / nodal / window patterns as BESS.

**References**

- Paper: `mario_implementation/wes-11-349-2026.pdf` — §3.4, Table 1, §4.2–4.3 (parameter identification)
- Code: `mario_implementation/18414805/OPF_ACDC_Energy_Islands.py` — lines 608–630 (constraints), 658 (hub `P` balance: `-Pe`)

#### 5.0 Decisions (to lock before coding)

| ID | Topic | Proposal |
|----|--------|----------|
| H5-1 | Side | **Single `Electrolyser` class** (like `Ren_Source`): `connected` AC/DC. AC: optional reactive compensation (`Q_min_MVAR` / `Q_max_MVAR`). DC: `Q` fixed at 0. ✅ Locked |
| H5-2 | State unit | **`mass_H2`** [kg] on element and Pyomo var (not pu). Class caps: `H2_mass_max`, `H2_mass_initial`, `H2_mass_final`. ✅ Locked |
| H5-3 | `c_h` term | **Locked — paper + reference script:** `h = b_h·P·S_base·dt + c_h` **every frame** (Eqs. 32–33). ✅ |
| H5-4 | Economics | **Operation only** — no electrolyser CAPEX (G11). |
| H5-5 | Horizon | **`window_nl_opf` only** for multi-frame inventory + `H2_mass_final`; snapshot OPF = one frame, no terminal `H2_mass_final`. |
| H5-6 | `window_block` | Reuse BESS pattern: omit in-block `mass_H2` chain / `H2_mass_final` in snapshot blocks; parent `window_h2_constraints` in `window_nl_opf`. |
| H5-7 | Grid flag | **`grid.H2`** via `analyse_grid` when `electrolysers` non-empty. ✅ Locked |
| H5-8 | API | **`add_electrolyser(..., H2_mass_max_kg, H2_mass_initial_kg, H2_mass_final_kg, Q_min_MVAR, Q_max_MVAR)`** — AC or DC node. ✅ Locked |

#### 5.1 Classes & grid hooks

**New:** `Electrolyser` in `Classes.py` (AC or DC via ``connected``)

- `electrolyserNumber`, `Node` / `Node_AC` or `Node_DC`, `connected`
- `P_max`, `P_min` [pu], `b_h` [kg/MWh], `c_h` [kg], `M_max`, `M_initial`, `M_final` [kg], `dt_hours`, `S_base`
- Post-solve attrs: `P_electrolyser`, `M_H2`, `h_produced` (optional)

**Grid / nodes**

- `Grid.electrolysers` (list)
- `Node_AC.connected_electrolyser` (list)
- `analyse_grid`: set `grid.H2 = bool(grid.electrolysers)` (name TBD at implementation)

#### 5.2 Snapshot NL model (`ACDC_OPF_NL_model.py`)

Gate on `grid.H2` (when implemented).

- `hydrogen_variables` / `hydrogen_constraints` (mirror `storage_*`)
- Vars: `P_electrolyser`, `M_H2` with bounds
- Snapshot: one-step inventory from `M_initial` (Param `M_H2_prev` or inline), **no** terminal `M_final`
- Nodal: `PGi_electrolyser` or subtract `P_electrolyser` in `P_AC_node_rule` for connected node
- Export in `export_acdc_nl_model_to_pyflow_acdc`

#### 5.3 Results

- `Results.ext_electrolyser()` — snapshot table: Name, Node, P (MW), M_H2 (kg), loading %
- `Results.hydrogen_window()` — per-frame `M_H2`, `P_electrolyser` (mirror `storage_window`)
- Wire into `Results.all()` when `window_nl_opf_run` / `grid.H2`

#### 5.4 Coupled window (`window_nl_opf.py`)

Extend existing frame-block assembly:

1. `opf_create_nl_model_acdc(..., window_block=True)` also skips in-block H₂ balance / `M_final` (extend P4-1a or add `H5-6` flag).
2. Parent **`window_h2_constraints`** — same pattern as `window_soc_constraints`:

```
t = 0:     mass[t] = H2_mass_initial + h(P_e[t])   (h includes c_h)
t > 0:     mass[t] = mass[t−1] + h(P_e[t])
t = T−1:   mass[t] = H2_mass_final   (when set)
```

3. Objective unchanged (P4-3) — revenue-only; H₂ quota enforced via `M_final`, not a separate cost term.
4. Export trajectories → `grid.window_opf_results['hydrogen_M_H2']`, `['hydrogen_P_e']`, etc.

**Exit criteria (Phase 5 v1):** `add_electrolyser` + NL constraints + `window_nl_opf` parent H₂ links + results tables. **No Mario comparison yet** — that is **Phase 6**. Doc updates → **Concurrent — Documentation** (below). ✅ Done (code + `test_hydrogen_opf.py`).

---

### Phase 6 — PEI validation vs Mario paper (G8) — **all together**

**Goal:** One coupled **24 h** `window_nl_opf` on the Princess Elisabeth test system reproducing the Mario paper / reference script — **BESS + hydrogen + exports + revenue** in a single run, not separate BESS-only and H₂-only checks.

**Prerequisites:** Phase 4 (`window_nl_opf`) ✅; **Phase 5** (electrolyser) for full paper parity. A **BESS-only** subset test may land early while Phase 5 is in progress; **Phase 6 exit** requires the **full** coupled case.

**Ordering vs Phase 7:** Fixed-window Mario validation (**Phase 6**) **before** rolling horizon (**Phase 7**). Mario is a single 24 h coupled solve; rolling has no paper reference and adds boundary/carry-over complexity — validate the core window first.

**Note:** This subsumes the deleted old **Phase 5** (BESS-only Mario check).

**References**

- Paper: `mario_implementation/wes-11-349-2026.pdf` — §3.3–3.5, §4.1, Table 1, case study §5.2
- Script: `mario_implementation/18414805/OPF_ACDC_Energy_Islands.py`
- Data: `power_matrix.csv`, `BE_Price.csv`, `GB_Price.csv`, `DK_Price.csv`
- pyflow grid: `PEI_grid()` — hub **`PE_Island`** (G9; Mario node `0`)

**Files:** `pyflow_tests/test_pei_window_nl_opf_bess_h2.py`,
`example_grids/PF/_pei_bess_data.py`, and/or
`pyflow_tests/doc_examples/storage/02_window_nl_opf_pei.py`

#### 6.1 Grid & asset setup

1. `PEI_grid()` — harmonize **`S_base = 3500` MVA** with Mario (`Sbase = 3500e6`); document any remaining base / per-unit mismatch.
2. **`add_storage(grid, 'PE_Island', ...)`** — Mario / Table 1 BESS:
   - `P_nom = 0.33` pu, `η_c = 0.85`, `η_d = 0.9`
   - `soc_initial = 0.5`, `soc_final = 0.5` (window terminal @ last frame only)
   - `soc_min = 0.1`, `soc_max = 1.0`
3. **`add_electrolyser(grid, 'PE_Island', ...)`** — Mario / Table 1 H₂:
   - `P_max = 150` MW, `P_min = 22.5` MW
   - `b_h = 16.0585` kg/MWh, `c_h = 8.2195` kg
   - `M_final` per Mario `MH2_fin = 0.7 · P_h · 24 / ne`, `ne = 58e-3` MWh/kg
4. Attach wind **`Time_series`** from `power_matrix.csv` (turbine-level → pyflow mapping per PEI layout).
5. Attach hourly **export prices** (BE, GB, DK) from Mario CSVs.
6. **`window_nl_opf(grid, start=0, end=23)`** — 0-based, 24 frames; revenue objective (paper Eq. 37 / Mario `obj_rule`).

#### 6.2 Quantities to compare (single checklist)

| Quantity | Mario source (script) | Match expectation |
|----------|----------------------|-------------------|
| `P_charge[t]`, `P_discharge[t]`, `Q[t]`, `SoC[t]` | `Pb_c`, `Pb_d`, `Qb`, `SoC` (~807–814) | Document Δ; tighten after `S_base` alignment |
| `P_electrolyser[t]`, `M_H2[t]` | `Pe_values`, `MH2` (~810–813) | Same |
| Export `P` to BE / GB / DK | `P_CA`, `P_CB`, `P_CC` (~817–819) | Qualitative → numeric as grid converges |
| Total revenue / objective | `benefit_total` (~869–878) | Qualitative first; explain converter / export sign conventions |
| Terminal SoC / `M_final` | `SoC_fin`, `MH2_fin` constraints | Hard constraints in both models |

#### 6.3 Known alignment items (document in test docstring)

- `S_base` (3500 MVA vs pyflow PEI default)
- Slack / PV hub specification (`PE_Island`)
- HVDC converter loss coefficients (`a`, `b`, `c` in Mario)
- Export power sign convention (Mario objective uses exported power formulation)
- Hybrid pyflow PEI topology vs Mario’s aggregated node numbering

#### 6.4 Exit criteria

- One **24 h coupled** run completes with BESS **and** electrolyser on `PE_Island`.
- Validation test committed; all §6.2 rows reported with tolerances or explained deltas.
- `storage/02_window_nl_opf_pei.py` literalinclude example runs in CI (see **Concurrent — Documentation**).

---

### Phase 7 — Rolling / sliding window ✅

**Status:** Implemented as `rolling_window_nl_opf` in `window_opf.py` (1-based `start`/`end`, SoC carry, `soc_final_mode`).

**Goal (met):** Advance over a long `Time_series` — carry `soc_initial` / H₂ state from the previous window’s terminal state.

**Exit criteria:** Multi-day `Time_series` solved as chained windows; terminal SoC / H₂ inventory carried between windows; doc example in **Concurrent — Documentation**.

---

### Phase 8 — Myopic / forward-only time series + soft `soc_ref` (G4) ✅

**When:** After Phase 7 rolling window is in use; independent of hard `soc_final` window policy.

**Problem:** Under pure energy-cost myopic OPF, a BESS can discharge in a high-price hour and then **stay empty** (no foresight of future need / no incentive to recharge). Coupled `window_nl_opf` / rolling already prevent that via horizon coupling and/or hard `soc_final`. Phase 8 adds the **causal TS** path with a **soft SoC reference** so sequential hours remain useful.

**Goal:** Forward-only BESS in `ts_acdc_opf`: each hour is one snapshot NL OPF; SoC carries hour→hour; a secondary objective penalizes deviation from `soc_ref`.

#### 8.1 Locked decisions (Phase 8 v1)

| ID | Topic | Decision |
|----|--------|----------|
| P8-1 | Foresight | **Myopic only** — one hour per solve; `SoC_prev` ← previous hour’s solved SoC. **H₂ inventory carries** (see P8-9) |
| P8-2 | Soft reference | New class attribute **`soc_ref`** [pu] on `Storage`. **Init = `soc_initial`**. In the NL model: **mutable `Param`** (scalar for now; mutable so a future per-frame / TS `soc_ref` is possible) |
| P8-3 | Penalty form | **Quadratic only** `(SoC − soc_ref)²`. No absolute-value form (Pyomo / IPOPT do not handle abs well) |
| P8-4 | Objective API | New `ObjComponent` **`SoC_deviation`**. Active when `ObjRule['SoC_deviation']['w'] > 0`. Explicit opt-in (no silent auto-enable when ESS present) |
| P8-5 | Weighting | **Same `ObjRule` weighting mechanism** as existing objective terms (`Energy_cost`, `H2_sale`, …). Global weight only in v1 (no per-element `soc_ref_weight`). Scaling may be revised later |
| P8-6 | Hard terminal SoC | **`ts_acdc_opf`:** no hard `soc_final` — soft `soc_ref` only. **`window_nl_opf` / rolling:** keep hard **`soc_initial` + `soc_final`** constraints (unchanged); soft SoC not part of window Phase 8 |
| P8-7 | Scope | **`ts_acdc_opf` for now** (penalty lives in snapshot `opf_obj` because TS calls snapshot OPF each hour). Window paths do not adopt soft SoC in v1 |
| P8-8 | Equivalence | Document clearly: myopic + `SoC_deviation` ≠ global `window_nl_opf` optimum |
| P8-9 | H₂ tank / empties | Keep **`H2_mass_max`**. Attribute **`empty_tank_cycle`** (`None` or int `N≥1`): empties are **out-of-opt** (between solves), never in-model constraints. **Myopic:** `None` → never empty (carry until max binds); `N` → empty after every `N` solved hours. **Rolling:** `None` → empty every window boundary; `N` → empty at first commit end hour `≥ k·N`. `H2_mass_final` stays window/rolling only. Sale via `H2_sale`. |
#### 8.2 Implementation tasks

- [x] `Classes.py` / `add_storage`: `soc_ref` attribute, init = `soc_initial`
- [x] `constants.py`: `ObjComponent.SOC_DEVIATION = 'SoC_deviation'`
- [x] `ACDC_OPF.py` `opf_obj`: `w * Σ (SoC − soc_ref)²` via existing ObjRule weight path
- [x] `ACDC_OPF_NL_model.py`: `soc_ref` / `soc_ref_DC` as **mutable Param**; wire into objective; snapshot SoC balance already exists
- [x] `Time_series.py` `ts_acdc_opf`: after each successful hour, write `st.soc_initial` / `SoC_prev` from solved `SoC`
- [x] `Electrolyser.empty_tank_cycle` + myopic / rolling out-of-opt empties (P8-9)
- [x] Results: record per-hour SoC / charge / discharge in TS results (reuse or extend existing TS export patterns)
- [x] Tests: small grid — SoC carry + `SoC_deviation`; H₂ empty-cycle helpers
- [x] Docs: `usage_storage.rst` / `usage_hydrogen.rst` / `api/hydrogen.rst` / `api/ts.rst` — myopic SoC + H₂ tank / empties

#### 8.3 Exit criteria

- `ts_acdc_opf` on a grid with `grid.ESS` carries SoC across hours without NaNs / reset bugs
- `ObjRule={'Energy_cost': 1, 'SoC_deviation': w}` runs; SoC trajectory visibly pulled toward `soc_ref` for `w` large enough
- Window modes still use hard `soc_initial` / `soc_final` only (no soft SoC dependency)
- Doc example + unit test committed; roadmap line in `usage_storage.rst` marks Phase 8 done when shipped

---

### Phase 9 — Linear AC OPF (`optimal_l_pf`) ✅

**When:** After Phases 0–8 (element API + NL model stable). Beyond original G2 (NL-only); kept as operation-only (no TEP sizing).

**Goal:** Include **AC-connected** BESS and electrolysers in the linear (DC-style) AC OPF for fast LP studies.

#### 9.1 Locked decisions

| ID | Topic | Decision |
|----|--------|----------|
| P9-1 | Side | **AC-only grids**; raise if `grid.DCmode` |
| P9-2 | BESS | Charge / discharge / SoC + `|P_net| ≤ S_max`; **no Q**, no S-circle |
| P9-3 | H₂ | `P_electrolyser` + mass balance; **no Q**; optional `H2_sale` in `opf_obj_l` |
| P9-4 | `SoC_deviation` | **Reject** if weight > 0 (quadratic; not LP-safe) |
| P9-5 | Export | Write storage / electrolyser setpoints; `Q = 0` |

**Files:** `AC_OPF_L_model.py`, `ACDC_OPF.py` (`opf_obj_l` / `optimal_l_pf`), `test_linear_opf_bess_h2.py`, docs `api/L_models`, `usage_storage` / `usage_hydrogen`.

**Exit criteria:** `build_only` + optional LP solve tests; docs note linear vs NL. ✅ Done

---

### Concurrent — Documentation (ongoing; not a blocking phase)

**Goal:** Keep user-facing docs and citations aligned with each implementation phase — update **with every change**, not as a final gate.

**When:** Start after Phase 4 (API stable). Extend on Phase 5 (H₂), Phase 6 (PEI example), Phase 7 (rolling), etc.

#### D.1 API reference

**New file:** `docs/api/storage.rst` ✅

- `.. autoclass:: pyflow_acdc.Storage_AC`
- `.. autofunction:: pyflow_acdc.add_storage`
- `.. autofunction:: pyflow_acdc.window_nl_opf`
- BESS constraint summary (SoC dynamics, S-circle) with cross-ref to usage page
- Sign convention table (charge / discharge / injection)
- **Phase 5:** add `docs/api/hydrogen.rst` — `Electrolyser_AC`, `add_electrolyser`

**Update:** `docs/api/grid_mod.rst` — link to `storage.rst` ✅

**Update:** `docs/api/opf.rst` — NL OPF supports `storage_elements`; coupled multi-hour runs use `window_nl_opf`

**Update:** `docs/api/L_models.rst` — Phase 9 linear AC BESS / H₂ ✅

#### D.2 Usage guide

**New file:** `docs/usage_storage.rst` ✅

Sections:

1. **Overview** — coupled / rolling / myopic TS / linear OPF ✅
2. **Adding a BESS** — `add_storage` workflow on any AC/DC node ✅
3. **Running `window_nl_opf`** — see `usage_window_opf.rst` ✅
4. **Results** — `Results.ext_storage`, `Results.storage_window` ✅
5. **PEI example** — hub bus `PE_Island`; literalinclude `storage/02_window_nl_opf_pei.py` ✅
6. **Modelling note** — Useche-Arteaga et al. (2026) §3.3 ✅
7. **H₂** — `usage_hydrogen.rst` (§3.4) ✅
8. **Myopic TS** — soft `soc_ref` (`ObjRule['SoC_deviation']`) ✅
9. **Linear OPF** — cross-link `api/L_models` / `optimal_l_pf` (Phase 9) ✅

**Literalinclude examples** (under `pyflow_tests/doc_examples/`):

- `storage/01_add_storage.py` ✅
- `storage/02_window_nl_opf_pei.py` — PEI window (build-only) ✅
- `window_opf/01_pei_season_compare_dash.py` — season-compare + Dash ✅

**Update:** `docs/index.rst`, `docs/usage.rst` ✅

#### D.3 Citing

**Update:** `docs/citing.rst` — *For BESS / energy-island operation* ✅ (H₂ covered via same paper §3.4)

#### D.4 Doc tests

**New:** `pyflow_tests/test_docs_storage.py` ✅

**Exit criteria (rolling checklist, not a single gate):**

- [x] `usage_storage.rst` and `api/storage.rst` build in Sphinx without warnings
- [x] Mario paper cited in `citing.rst`, usage page, and plan §7
- [x] Doc examples execute in CI (`test_docs_storage.py`)
- [x] Cross-links between plan and docs on GitHub / Read the Docs
- [x] H₂ API + usage pages (Phase 5)
- [x] PEI validation literalinclude (Phase 6) — `usage_window_opf` + `storage/02_…`
- [x] Rolling-window usage note (Phase 7) — `usage_window_opf` / storage / hydrogen
- [x] Myopic TS + `soc_ref` / `SoC_deviation` (Phase 8)
- [x] H₂ `empty_tank_cycle` docs (P8-9)
- [x] Linear AC OPF BESS / H₂ docs (Phase 9) — `api/L_models`, usage pages

---

## 4. File touch list (summary)

| File | Changes |
|------|---------|
| `Classes.py` | `Storage_AC`, `Storage_DC`, `Grid.storage_elements`, `Node_AC/DC.connected_storage` |
| `grid_modifications.py` | `add_storage()` |
| `grid_analysis.py` | `ESS` flag |
| `ACDC_OPF_NL_model.py` | Snapshot storage (Phase 2 ✅); `window_block=True` skips in-block SoC boundaries (P4-1a) |
| `window_opf.py` | **`window_nl_opf`** — frame blocks, parent SoC links ✅; **Phase 5** parent H₂ links ✅ |
| `Classes.py` (Phase 5) | `Electrolyser_AC`, `Grid.electrolysers`, `Node_AC.connected_electrolyser` ✅ |
| `grid_modifications.py` (Phase 5) | `add_electrolyser()` ✅ |
| `grid_analysis.py` (Phase 5) | `H2` flag ✅ |
| `ACDC_OPF_NL_model.py` (Phase 5) | `hydrogen_variables` / `hydrogen_constraints`, nodal load hook, export ✅ |
| `Results_class.py` (Phase 5) | `ext_electrolyser()`, `hydrogen_window()` ✅ |
| `ACDC_OPF.py` | `storage_info` in `translate_pyf_opf`; pass horizon if needed |
| `Results_class.py` | `ext_storage()`, `storage_window()` |
| `Time_series.py` | **Phase 8** — myopic SoC carry + soft `soc_ref`; H₂ inventory + `empty_tank_cycle` |
| `AC_OPF_L_model.py` | **Phase 9** — AC BESS / H₂ vars, P balance, export ✅ |
| `ACDC_OPF.py` | **Phase 9** — `opf_obj_l` (`Energy_cost` + `H2_sale`); `SoC_deviation` reject ✅ |
| `__init__.py` | Export new symbols |
| `pyflow_tests/...` | PEI / H₂ / rolling / `test_linear_opf_bess_h2.py` ✅ |
| `docs/api/storage.rst` | `Storage`, `add_storage`, window API + linear note ✅ |
| `docs/usage_storage.rst` | Usage guide + Mario modelling note + plan link ✅ |
| `docs/api/L_models.rst` | Linear OPF BESS / H₂ ✅ |
| `docs/citing.rst` | BibTeX + citation for Useche-Arteaga et al. (2026) |
| `docs/index.rst`, `docs/usage.rst` | Toctree / catalogue links |
| `pyflow_tests/doc_examples/storage/` | Literalinclude examples |
| `pyflow_tests/test_docs_storage.py` | Doc example smoke tests |

---

## 5. Other considerations

### Nonlinearities

- S-circle (AC) and AC power flow → **IPOPT** only; DC storage adds linear `P_max` bounds only
- SoC dynamics are linear in pu when `E_max` is fixed
- Linear OPF (Phase 9): AC BESS uses `|P_net| ≤ S_max` (no Q); H₂ and SoC dynamics stay LP-compatible; `SoC_deviation` excluded

### Code conventions

- No `getattr` on Pyomo model objects (workspace rule)
- Fail fast on missing / invalid storage parameters
- Prefer explicit model attribute access

### Future: degradation

- `E_max` on `Storage_AC` is the degradation hook (e.g. `E_max_eff = E_max * health_factor`)
- SoC stays in pu; MWh state = `SoC * E_max_eff`

### Future: exclusivity (G6 revisit)

If simultaneous charge/discharge appears in results:

- Option A: post-solve assertion / warning
- Option B: complementarity or small penalty
- Option C: single net power variable with sign (changes model structure)

---

## 6. Suggested implementation order

1. Phase 0 — design freeze ✅  
2. Phase 1 — class + `add_storage` ✅  
3. Phase 2 — snapshot NL model ✅  
4. Phase 3 — `Results.ext_storage` + `storage_window` ✅  
5. Phase 4 — `window_nl_opf` + `window_block` ✅  
6. Phase 5 — hydrogen / electrolyser ✅  
7. Phase 6 — Mario PEI validation (BESS + H₂ + exports) ✅ / in use  
8. Phase 7 — rolling window ✅  
9. Phase 8 — myopic TS + soft `soc_ref` (`SoC_deviation`) + H₂ `empty_tank_cycle` ✅  
10. **Phase 9 — linear AC OPF (`optimal_l_pf`) AC BESS / H₂** ✅  

**Concurrent (throughout):** Documentation — update RST, examples, and citations with each phase above.

---

## 7. References

### Primary reference (BESS / energy-island operation)

M. Useche-Arteaga, P. Gebraad, V. A. Lacerda, M. Cheah-Mane, and O. Gomis-Bellmunt, *Optimizing the operation of energy islands with predictive nonlinear programming – a case study based on the Princess Elisabeth Energy Island*, Wind Energ. Sci., 11, 349–372, 2026, https://doi.org/10.5194/wes-11-349-2026.

- BESS model: paper §3.3 (Eqs. 24–31) — implemented as `Storage_AC` / `Storage_DC` + NL constraints ✅
- Hydrogen model: paper §3.4 (Eqs. 32–36) — **Phase 5** (`Electrolyser_AC`, `add_electrolyser`)
- Coupled multi-hour operation: paper §3.5–3.6 — implemented via **`window_nl_opf`** (`window_opf.py`) ✅
- Local PDF: `mario_implementation/wes-11-349-2026.pdf`
- Reference implementation: `mario_implementation/18414805/OPF_ACDC_Energy_Islands.py` (BESS ~584–605, H₂ ~608–630, hub balance ~658)

### pyflow_acdc assets

- PEI grid — [`PEI_grid.py`](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/pyflow_acdc/example_grids/PF/PEI_grid.py) (hub: **`PE_Island`**)
- User guide — [docs/usage_storage.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_storage.rst) · [Read the Docs](https://pyflow-acdc.readthedocs.io/en/latest/usage_storage.html)
- H₂ guide — [docs/usage_hydrogen.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_hydrogen.rst) · [Read the Docs](https://pyflow-acdc.readthedocs.io/en/latest/usage_hydrogen.html)
- Window / rolling — [docs/usage_window_opf.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/usage_window_opf.rst) · [Read the Docs](https://pyflow-acdc.readthedocs.io/en/latest/usage_window_opf.html)
- Linear OPF — [docs/api/L_models.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/api/L_models.rst) · [Read the Docs](https://pyflow-acdc.readthedocs.io/en/latest/api/L_models.html)
- API — [docs/api/storage.rst](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/api/storage.rst) · [Read the Docs](https://pyflow-acdc.readthedocs.io/en/latest/api/storage.html)
- Integration plan — [plans/bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md)
- Sibling plans — [plans/](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration/plans)
