# Convex AC/DC SOCP plan for pyflow_acdc

**Repository:** In-repo links target the [`mario_integration`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration) branch ([`plans/`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration/plans)).

Living implementation plan for **sparse second-order cone programming (SOCP)**, **mixed-integer
SOCP (MI-SOCP)**, **chance-constrained programming (CCP)**, and **robust convex optimization**
methodologies from Mario Useche-Arteaga et al.

This plan is **publication-grounded only**. It does **not** prescribe owner implementation
details, solver choices, Pyomo constraint syntax, or API names beyond what the papers and
existing pyflow_acdc architecture require. Owner code and business logic should be waited
for before coding.

**Primary references**

1. M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Efficient AC/DC energy hubs operation using sparse SOCP relaxation
and chance-constrained optimization*, Sustainable Energy, Grids and Networks **46**, 102217
(2026). https://doi.org/10.1016/j.segan.2026.102217

2. M. Useche-Arteaga, W. Gil-González, O. Gomis-Bellmunt, M. Cheah-Mane, and V. Lacerda,
   *Robust energy management in active distribution networks using mixed-integer convex
   optimization*, Electr. Power Syst. Res. **241**, 111367 (2025).
   https://doi.org/10.1016/j.epsr.2024.111367

**Related pyflow_acdc assets**

| Document | Link |
|----------|------|
| BESS / H₂ operation (NLP, shipped) | [bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) |
| BESS sizing (separate build) | [bess_sizing_ramp_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_sizing_ramp_plan.md) |
| Architecture map | [docs/architecture.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/architecture.md) |
| PEI validation grid | [`PEI_grid.py`](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/pyflow_acdc/example_grids/PF/PEI_grid.py) |
| PEI window OPF tests | [`test_pei_window_nl_opf_bess_h2.py`](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/pyflow_tests/test_pei_window_nl_opf_bess_h2.py) |

Local PDFs (user-provided): `efficient.pdf` (2026), `1-s2.0-S0378779624012537-main.pdf` (2025).

---

## 0. Scope of this plan

### 0.1 Two related but distinct problem classes

| Aspect | Paper A (SEGAN 2026) | Paper B (EPSR 2025) |
|--------|----------------------|---------------------|
| System | Hybrid **AC/DC energy hub** (offshore island) | **Active distribution network** (IEEE 33-bus class) |
| Objective | Maximize **export revenue** (Eq. 1 / 37) | Minimize **generation cost** (Eq. 1 / 19) |
| Network | AC collection + HVDC + converters + export links | Radial / meshed **AC distribution** only |
| Assets | Wind, BESS (MI), H₂ electrolyser + storage | DG (wind/PV), fixed-step **capacitor banks** (integer), **CRPD** (TSC/D-STATCOM) |
| Convex core | Dense SOCP → **sparse SOCP** (§3) | MI-SOC relaxation (§3) |
| Uncertainty | **CCP** — wind + electricity price (§4) | **Robust** worst-case — demand + RES (§3.1) |
| Time | Multi-period (24 h in case study) | Single snapshot (24 h profiles in results) |
| Validation | PEI simplified (12 AC / 4 DC) + full (172 AC / 4 DC) | Modified IEEE 33-bus |

Both papers share the **same SOCP lifting** (`h_k = |v_k|²`, `w_km = v_k v_m*`, rotated SOC
inequality Eq. 18/30/31) but target different grids, objectives, discrete devices, and
uncertainty frameworks.

### 0.2 In scope (papers)

| In scope | Out of scope (this plan) |
|----------|--------------------------|
| SOCP / MI-SOCP relaxation of AC (and AC/DC) power flow | Modifying `ACDC_OPF_NL_model.py` in place |
| Sparse edge-set formulation (Paper A §3, Algorithm 1) | BESS **sizing** economics (`bess_sizing_ramp_plan.md`) |
| CCP for wind + price (Paper A §4) | Static / MP TEP investment variables |
| Robust MI-SOC for ADN EMP (Paper B §3.1) | Static / MP TEP investment variables |
| BESS charge/discharge **exclusivity** binaries (Paper A Eqs. 20–23) | SDP relaxations (Paper B cites [22] for comparison only) |
| H₂ mass balance + quota (Paper A Eqs. 13–16) | Metaheuristic ORPD from literature |
| Optional comparison vs existing NLP (`optimal_pf`, `window_nl_opf`) | Owner-specific YALMIP / CVXPY port (papers use MATLAB/Python externally) |

### 0.3 Distinction from existing pyflow_acdc stacks

| Stack | Formulation | Relation to this plan |
|-------|-------------|----------------------|
| `optimal_pf` + `ACDC_OPF_NL_model.py` | **Nonlinear** polar OPF (`V`, `θ`) | Reference “exact” baseline for Paper A validation (Table 3) |
| `window_nl_opf` | Coupled multi-hour **NLP** on full grid + BESS + H₂ | Operational peer; PEI tests already exist |
| `bess_sizing.py` (planned) | Plant-level POI NLP | Separate problem class ([bess_sizing_ramp_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_sizing_ramp_plan.md)) |

**This plan adds a dedicated SOCP / MI-SOCP stack** with its own model builder and runner —
not a patch to the shipped NLP builders.

---

## 1. Paper summaries

### 1.1 Paper A — SEGAN 2026: sparse SOCP + CCP for AC/DC energy hubs

#### 1.1.1 Problem class

Mixed-integer **nonlinear** operation model (Eqs. 1–26) for hybrid AC/DC hub:

- **Objective (Eq. 1):** `max Σ_{t,i} C_{i,t} · p_exp_{i,t}` — revenue from exports to
  onshore countries.
- **Continuous vars:** AC complex voltages `v_{k,t}`, DC voltages `v^dc_{k,t}`, complex
  injections `s_{k,t}`, BESS charge/discharge, H₂ inventory, wind dispatch `p^w_{k,t}`, …
- **Binary vars:** BESS mode `y^c_{k,t}`, `y^d_{k,t}` — no simultaneous charge/discharge
  (Eqs. 22–23).

Subsystems in the MINLP:

| Block | Eqs. | Notes |
|-------|------|-------|
| AC nodal balance | (2) | Bilinear `v* Y v` |
| DC nodal balance | (3) | Bilinear DC voltage products |
| AC / DC thermal limits | (4)–(7) | Apparent / active power on lines |
| Voltage bounds | (8)–(9) | AC magnitude, DC voltage |
| VSC-HVDC losses + rating | (10)–(12) | Affine loss `a + b·ℜ{s^c}` |
| H₂ production + storage | (13)–(16) | Linear electrolyser map; mass balance |
| BESS SoC + exclusivity | (17)–(25) | MI coupling; reactive `q` on BESS |
| Wind cap | (26) | `p^w ≤ P_rated` |

#### 1.1.2 Conventional dense SOCP (§2.2)

Lift bilinear voltage products via:

- `h_{k,t} = |v_{k,t}|²` (Eq. 27)
- `w_{km,t} = v*_{k,t} v_{m,t}` (Eq. 28) — defined for **all node pairs** in dense form
- `h^dc_{k,t}`, `w^dc_{km,t}` for DC (Eqs. 33–34)

Rotated SOC relaxation (Eq. 31 / 44–45):

```
‖ [2 w_{km}; h_k − h_m] ‖₂ ≤ h_k + h_m
```

Linearized balances (Eqs. 32, 36, 38–39). Line limits reformulated in `h`, `w` (Eqs. 40–43).
Voltage bounds on `h` (Eqs. 46–47). Remaining blocks unchanged → **MI-SOCP** (Eqs. 37–48).

**Complexity:** O(N²) auxiliary variables per period — prohibitive at PEI scale (§2.2: ~90k
scalar vars for one period at 172 nodes).

#### 1.1.3 Sparse SOCP (§3) — key contribution

Exploit topology:

- Edge sets `E_AC = {(k,m) | branch exists, k < m}`, `E_DC` analogously.
- Hermitian symmetry (AC): `w_{mk} = w*_{km}` — optimize upper triangle only.
- Symmetry (DC): `w^dc_{mk} = w^dc_{km}`.

Sparse balance (Eq. 54) uses diagonal admittance + off-diagonal `w` or `w*` by index order.
SOC constraints only on `(k,m) ∈ E` (Eqs. 55, 57). **Mathematically equivalent** to dense
SOCP; fewer variables/constraints.

Reported gains (Table 2, simplified PEI 12 AC / 4 DC, 24 h):

| Metric | Reduction vs dense SOCP |
|--------|-------------------------|
| Variables | 79.2 % |
| Constraints | 56.2 % |
| Solve time | 86.3 % |

Accuracy vs NLP: objective gap < 0.001 % (Table 3).

#### 1.1.4 Chance-constrained programming (§4)

Individual chance constraints at confidence `γ`:

```
Pr(g(x, ξ) ≤ 0) ≥ γ  →  g(x) ≤ Q_{1−γ}(ξ)     (Eqs. 58–60)
```

**Wind (Eqs. 61–65):** `p^w_{k,t} ≤ p^p_{w,k,t} + Q_{1−γ}(ε_w)` with truncated normal
forecast error (σ = 10 % of forecast; bounded by turbine rating).

**Price (Eqs. 66–69):** `C_{k,t} ≤ C^p_{k,t} + Q_{1−γ}(ε_c)` — conservative revenue valuation;
truncated normal (±3σ).

Combined deterministic sparse SOCP (Eqs. 70–72) + remaining physics.

Revenue impact vs deterministic: 1.2 %–17 % reduction depending on γ and scenario
(Table 4). Wind uncertainty dominates price uncertainty.

#### 1.1.5 Case study anchors (validation targets)

| Configuration | Nodes | Purpose |
|---------------|-------|---------|
| Simplified (Fig. 2) | 12 AC, 4 DC | Dense vs sparse vs NLP benchmark |
| Full PEI (Fig. 6) | 172 AC, 4 DC | Scalability + BESS + H₂ deterministic |
| CCP full PEI | 172 AC, 4 DC | γ = 0.7, 0.8, 0.9 scenarios |

Deterministic full-system revenue reference: **7,112,732 €** / 24 h (§5.2).

---

### 1.2 Paper B — EPSR 2025: robust MI-SOC for active distribution EMP

#### 1.2.1 Problem class

**Energy management problem (EMP)** on an active distribution network:

- **Objective (Eq. 1 / 19):** `min ℜ{ C_G s_G + Σ_k C_{DG,k} s_k }` — minimize real
  generation cost (losses + DG dispatch).
- **Exact MINLP (§2):** nonlinear rectangular power balance (Eq. 2), integer capacitor
  steps `ξ_k`, continuous CRPD reactive `q^crpd_k`, DG active/reactive capability.

#### 1.2.2 Device taxonomy (not in pyflow_acdc today)

| Device | Paper set | Model role |
|--------|-----------|------------|
| Fixed-step capacitor bank | `S_CB`, integer `ξ_k` | Discrete reactive injection `ξ_k q^c_k` in balance (Eq. 2) |
| CRPD (TSC / D-STATCOM) | `S_crpd` | Continuous `q^crpd_k`, ‖q‖ ≤ q^nom (Eq. 6 / 30) |
| Distributed generator | `S_DG` | Complex `s_k`, ‖s‖ ≤ s^max (Eq. 7 / 23); reactive support |
| Slack substation | bus 0 | `v_0 = v_slack` (Eq. 4 / 20) |

#### 1.2.3 MI-SOC relaxation (§3)

Same lifting as Paper A:

- `w_{km} = v*_k v_m`, `h_k = ‖v_k‖²`
- SOC inequality (Eq. 18 / 22)
- Linearized balance (Eq. 27)
- Thermal limit (Eq. 24) on `h`, `w`
- Integer capacitor constraints (Eqs. 31–32)

#### 1.2.4 Uncertainty — robust worst-case (§2.2.6, §3.1)

Box uncertainty sets (±10 % in case study):

- DG active: `P^p_k ∈ [P^p_k − P̂^p_k, P^p_k + P̂^p_k]` (Eqs. 8–9 / 25–26)
- Demand: real and imag parts boxed separately (Eqs. 10–11 / 28–29)

Reformulated via robust counterpart (Eqs. 33–37, Löfberg [38]): **convex** worst-case
schedule. Worst-case generation cost +13 % vs deterministic (Table 3).

#### 1.2.5 Validation anchors

- Modified **IEEE 33-bus** with wind, PV, capacitor banks, CRPD.
- MATPOWER + SDP cross-check: ~0.002 % cost error vs SOC (Table 4).
- Voltage error vs MATPOWER < 0.0001 % (Fig. 9).
- Deterministic: **35 %+** active energy loss reduction vs base scenario; **2 %** cost reduction.

---

## 2. What pyflow_acdc already has

### 2.1 Shipped — nonlinear operational stack (Paper A overlap)

| Layer | Location | Paper A mapping | Gap |
|-------|----------|-----------------|-----|
| `Grid`, `Ybus_AC`, `Ybus_DC` | `Classes.py`, `analyse_grid` | Admittance for sparse edge construction | ✅ |
| Polar NL OPF (`V`, `θ`) | `ACDC_OPF_NL_model.py` | NLP baseline (Table 3) | Different formulation — not rectangular SOC lift |
| `Storage` + `storage_*` | `Classes.py`, NL model | Eqs. 17–25 | **No** charge/discharge binaries; overlap allowed (G6) |
| `Electrolyser` + `hydrogen_*` | `Classes.py`, NL model | Eqs. 13–16 | Linear H₂ map exists; daily quota constraint not verified |
| `Ren_Source` | `Classes.py` | Wind dispatch `p^w` | Curtailment via `gamma`; no CCP layer |
| `Price_Zone` / export gens | NL model, PEI grid | Export revenue objective | Quadratic zone costs — not Paper A linear `C·p_exp` |
| `window_nl_opf` | `window_opf.py` | Multi-period coupled NLP | IPOPT path; no SOCP |
| PEI fixtures | `PEI_grid.py`, `_pei_bess_data.py` | Fig. 6 validation | ✅ starting point |

### 2.2 Not shipped — this plan's subjects

| Subject | Paper | pyflow status |
|---------|-------|---------------|
| SOCP / MI-SOCP model builder | A, B | **None** |
| Sparse edge-set `E_AC`, `E_DC` | A | **None** |
| Rectangular complex `w_{km}` SOC constraints | A, B | **None** (NL uses polar) |
| CCP quantile constraints | A | **None** |
| Robust box uncertainty counterpart | B | **None** |
| Capacitor banks (integer steps) | B | **None** |
| CRPD / D-STATCOM / TSC devices | B | **None** |
| MOSEK / conic solver integration path | A (CVXPY+MOSEK) | **None** in OPF stack |
| `convex_ACDC.py` / `convex_model.py` | This plan | **None** |

---

## 3. Architecture decision: standalone `convex_model.py` + `convex_ACDC.py`

**Locked:** implement Mario's convex methodologies as **new, self-contained modules**. Do
**not** modify `ACDC_OPF_NL_model.py`, TEP builders, or `window_opf.py` internals.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  EXISTING (unchanged)              │  NEW convex stack                         │
│  ACDC_OPF_NL_model (polar NLP)     │  convex_model.py — Pyomo SOCP/MI-SOCP    │
│  optimal_pf / window_nl_opf        │  convex_ACDC.py — runners + translate     │
│  IPOPT                             │    solve via conic-capable solver         │
└──────────────────────────────────────────────────────────────────────────────┘
         │                                      │
         │  benchmark / cross-check (Paper A)   │
         └──────────────────────────────────────┘
              same Grid in, compare objectives & voltages vs NLP
```

### 3.1 Module split

| File | Responsibility | Analogue in codebase |
|------|----------------|----------------------|
| **`convex_model.py`** | Pyomo model construction: sets, `h`/`w` vars, SOC constraints, subsystem blocks (BESS MI, H₂, exports / CRPD / caps), uncertainty layers | `ACDC_OPF_NL_model.py` |
| **`convex_ACDC.py`** | `translate_pyf_convex(grid)` (or reuse patterns from `translate_pyf_opf`), horizon assembly, objective, `pyomo_model_solve`, export back to `Grid` | `ACDC_OPF.py` + `window_opf.py` |

Rationale for **two files** (vs single `bess_sizing.py`):

1. Paper A alone has AC + DC + converter + BESS + H₂ + export + CCP — model bulk warrants
   separation of **build** vs **run**.
2. Paper B shares SOC core but different assets and robust layer — shared `convex_model`
   primitives (SOC lift, sparse edges) with problem-specific extensions.
3. Mirrors existing `ACDC_OPF.py` / `ACDC_OPF_NL_model.py` split.

### 3.2 Problem modes inside `convex_ACDC.py` (owner to name)

| Mode | Paper | Problem type | Typical solver class |
|------|-------|--------------|----------------------|
| `energy_hub_socp` | A §2–3 | MI-SOCP (sparse) | MOSEK, Gurobi, CPLEX |
| `energy_hub_ccp` | A §4 | MI-SOCP + linear quantile cuts | same |
| `adn_emp_misoc` | B §3 | MI-SOCP | MOSEK, Gurobi, CPLEX |
| `adn_emp_robust` | B §3.1 | Robust MI-SOCP | conic + robust reformulation |

These are **planning labels**, not committed API names.

### 3.3 What stays outside the convex build

| Module | Policy |
|--------|--------|
| `ACDC_OPF_NL_model.py` | Unchanged — NLP remains default “exact physics” path |
| `ACDC_Static_TEP.py`, `ACDC_MultiPeriod_TEP.py` | Unchanged |
| `bess_sizing.py` | Sibling plan — no overlap |
| `Classes.py` | Optional new element types for Paper B devices; optional CCP/robust params |
| `window_opf.py` | Optional downstream benchmark only |

### 3.4 Rationale

1. SOCP is a **different mathematical object** from polar NLP — deserves its own builder,
   not a branch inside `ACDC_OPF_NL_model.py`.
2. Conic solvers (MOSEK, etc.) are not the current IPOPT-centric `[OPF]` default — isolation
   contains optional-dependency and licensing concerns.
3. Paper B devices (capacitor banks, CRPD) do not belong in offshore hub NL model.
4. Sparse formulation (Paper A) is an **implementation strategy** inside `convex_model.py`,
   not a change to `Grid` topology storage.
5. PEI + IEEE 33 validation can proceed without risking regression on shipped `window_nl_opf`.

---

## 4. pyflow_acdc mapping: Classes → Model → Problem → Solution

### 4.1 Classes (`Classes.py`, `grid_modifications.py`, `constants.py`)

**Role:** parameters, topology, and post-solve results. Convex-specific **decision structure**
lives in Pyomo, not on element classes, until owner decides otherwise.

#### 4.1.1 Paper A — energy hub assets

| Paper entity | Existing class | Gap / owner decision |
|--------------|----------------|----------------------|
| Wind `p^w_{k,t}` | `Ren_Source` + nodal `PGi_ren` in NL | CCP needs forecast `p^p`, error distribution params |
| BESS `p^c`, `p^d`, `y^c`, `y^d`, SoC | `Storage` | **Missing:** binary exclusivity; paper uses MI |
| BESS reactive `q`, ‖s^b‖ limit | `Storage.Q`, `S_max` on AC | Partially aligned |
| Electrolyser `p^e`, H₂ mass `M` | `Electrolyser`, `mass_H2` | Check min power (Eq. 15), daily quota (§5.2.4) |
| Export `p^exp` to countries | `Price_Zone` + ext grid gens | Paper uses **linear** revenue; pyflow often quadratic |
| HVDC losses `a_k`, `b_k` | `AC_DC_converter` | Verify affine loss model match (Eq. 10) |
| `ρ` (mono/bipolar DC) | `Polarity` on `Line_DC` | Map to paper `ρ` factor |
| Price / wind uncertainty | — | **Missing:** `γ`, quantile inputs, truncated-normal params |
| Edge sets `E_AC`, `E_DC` | Built from `Ybus` sparsity pattern | Runtime derived — no new class required |

#### 4.1.2 Paper B — ADN assets

| Paper entity | Existing class | Gap |
|--------------|----------------|-----|
| Capacitor bank integer steps `ξ_k` | — | **New class or grid attachment** |
| CRPD `q^crpd` | — | **New class** (`TSC`, `DSTATCOM`) |
| DG with reactive capability | `Gen_AC` / `Ren_Source` | Partial — verify `‖s‖` limit and Q bounds |
| Box uncertainty `P̂^p`, `d̂^p` | — | **Missing** robust deviation params |
| Slack `v_0` | `Node_AC` slack | ✅ |

**Proposed class-layer actions (owner review)**

| ID | Action | Notes |
|----|--------|-------|
| C1 | `CapacitorBank` (or similar) with `q_nom`, `N_steps`, node attachment | Paper B Eqs. 12–13, 31–32 |
| C2 | `CRPD` / `ReactiveCompensator` with `q_nom` | Paper B Eq. 6 |
| C3 | Uncertainty config object (CCP vs robust) | Keeps `Grid` free of stale flags |
| C4 | **Do not** replace `Storage` with MI logic globally | Binaries only in convex BESS block |
| C5 | `grid.convex_opf_run` flag (or sibling) | Results routing, like `window_opf_run` |
| C6 | `add_capacitor_bank()`, `add_crpd()` in `grid_modifications.py` | Only when Paper B scope approved |

### 4.2 Model (`convex_model.py`)

**Role:** Pyomo variables, SOC constraints, subsystem blocks. **Not** in NL or L builders.

#### 4.2.1 Shared SOC kernel (Papers A & B)

```
convex_model.py
├── build_edge_sets(grid) → E_AC, E_DC from sparsity (k < m convention)
├── soc_lift_ac(model, E_AC, T)     → h_k,t, w_km,t, constraints (31)/(55)
├── soc_lift_dc(model, E_DC, T)     → h^dc, w^dc, constraints (35)/(57)
├── linear_ac_balance(model, ...)   → Eq. (54) / (32)
├── linear_dc_balance(model, ...)   → Eq. (56) / (36)
├── thermal_limits_soc(model, ...)  → Eqs. (40)–(43) [Paper A]
└── voltage_bounds_on_h(model, ...) → Eqs. (46)–(47)
```

| Aspect | NL model (`ACDC_OPF_NL_model`) | Convex model |
|--------|----------------------------------|--------------|
| Voltage representation | `V_AC`, `theta_AC` (polar) | `h_k`, `w_km` (rectangular lift) |
| AC balance | `cos/sin` of angle differences | Linear in `w`, `h` with `Y_bus` |
| DC balance | Polar / simplified | Quadratic lift → linear in `w^dc`, `h^dc` |
| Line limits | Nonlinear branch flow | SOC-reformulated (Eq. 40) |
| Relaxation gap | — | SOC inequality ≤ tightness vs NLP |

#### 4.2.2 Paper A extensions

| Block | Eqs. | Notes |
|-------|------|-------|
| VSC-HVDC interface | (10)–(12) | Embed in DC node balance per paper |
| BESS MI | (17)–(25) | `y^c`, `y^d` binaries; differs from NL G6 |
| H₂ subsystem | (13)–(16) | Reuse equations from NL `hydrogen_*` as reference |
| Export revenue objective | (37) | Linear `C·p_exp` — may bypass `Price_Zone` quadratic |
| Wind cap | (26) | Upper bound on dispatch |
| **CCP layer** | (70)–(72) | Precomputed `Q_{1−γ}` or parametric cuts |

**Sparse vs dense:** implement sparse first (Paper A contribution); dense SOC optional for
small-network regression tests (Table 2).

#### 4.2.3 Paper B extensions

| Block | Eqs. | Notes |
|-------|------|-------|
| Capacitor integer `ξ_k` | (12), (31)–(32) | MI-SOC |
| CRPD limits | (6), (30) | Scalar or vector `q` |
| DG cost objective | (19) | Real part of complex cost — differs from Paper A |
| Line current (Eq. 5 / 24) | Distribution thermal | Uses `‖Y(v_k − v_m)‖` lift |
| **Robust layer** | (25)–(29) + §3.1 | Worst-case box — owner picks Löfberg-style reformulation |

#### 4.2.4 Pyomo / solver note (plan only)

Papers use YALMIP (B) and CVXPY+MOSEK (A). pyflow_acdc standard is **Pyomo**. SOC
constraints map to Pyomo's conic interfaces (`pyo.SOCConstraint` or solver-specific).
**Owner must confirm** target solver(s) and whether `[OPF]` extra depends on MOSEK.

### 4.3 Problem (`convex_ACDC.py`)

**Role:** assemble full problem from `Grid` + time series + uncertainty scenario; call solve;
export.

| Runner concern | Paper A | Paper B |
|----------------|---------|---------|
| Horizon | Multi-period `T` (24 h) | Single or multi-period profiles |
| Input TS | Wind forecasts (Fig. 7), prices (Fig. 5) | Load / RES profiles (Fig. 5) |
| Mode switch | deterministic / CCP wind / CCP price / both | Scenarios 1–5 (§4.1) |
| Objective | Max revenue | Min generation cost |
| Output | `p_exp`, BESS, H₂ trajectories | Losses, voltages, `ξ_k`, `q^crpd` |

**Relationship to `window_nl_opf`:**

| Feature | `window_nl_opf` | `convex_ACDC` (planned) |
|---------|-----------------|-------------------------|
| Coupling | Multi-hour SoC / H₂ links | Same time-linking needed for Paper A |
| Physics | Polar NLP | Sparse MI-SOCP |
| BESS exclusivity | No (G6) | Yes (paper MI) |
| Uncertainty | None | CCP or robust |
| Solver | IPOPT | Conic MIP |

Possible future: `window_convex_opf` as horizon wrapper — **not assumed** in v1; owner decides.

### 4.4 Solution (`Results_class.py`, export, tests)

| Output | Paper reference | pyflow destination (TBD) |
|--------|-----------------|--------------------------|
| Total revenue / cost | Tables 3–4 (A), Table 3 (B) | `Results` summary method |
| Nodal `h_k` → voltage magnitude | Table 3 voltage check | `sqrt(h_k)` vs `V_AC` from NLP |
| Export powers | Fig. 8 | Time series export |
| BESS SoC / power | Fig. 9 | Storage results tables |
| H₂ production | Fig. 10 | Electrolyser results |
| CCP revenue sensitivity | Table 4 | Scenario comparison table |
| Capacitor steps `ξ_k` | Paper B | New results section |
| Solve stats (vars, constraints, time) | Table 2 (A) | `solver_stats` pattern from `pyomo_model_solve` |

**Validation strategy (design only):**

1. **Paper A simplified grid:** reproduce Table 2 counts + Table 3 objective / voltage parity
   (NLP vs sparse SOCP).
2. **Paper A full PEI:** deterministic revenue ~7.11 M€ (order-of-magnitude; tolerances TBD).
3. **Paper A CCP:** qualitative revenue reductions per Table 4.
4. **Paper B IEEE 33:** loss reduction ~35 %+, cost −2 % deterministic; +13 % worst-case.
5. **Cross-check:** `optimal_pf` / `window_nl_opf` on same PEI case for NLP baseline.

---

## 5. Subject-focused breakdown

### 5.1 Sparse SOCP relaxation (Paper A §3)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | Nothing mandatory — `Ybus` sparsity from existing `analyse_grid` | `grid_analysis.py` read-only |
| **Model** | `E_AC`, `E_DC`; upper-triangular `w`; Hermitian conjugate in balance (Eq. 54); SOC on edges only (Eq. 55) | `convex_model.py` |
| **Problem** | Flag `formulation='sparse'|'dense'` for regression | `convex_ACDC.py` |
| **Solution** | Report variable/constraint counts vs Table 2; wall time | `solver_stats` |

### 5.2 MI-SOCP BESS operation (Paper A Eqs. 20–23)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | Optional policy attrs (`enforce_exclusive_cd`) | `Storage` or run config |
| **Model** | Binary `y^c`, `y^d`; Eqs. (20)–(23) | `convex_model.py` |
| **Problem** | MIP time limit / gap for large `T` | `convex_ACDC.py` |
| **Solution** | Compare vs NL overlapping charge/discharge (G6) | Test / report |

### 5.3 Chance-constrained wind & price (Paper A §4)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | Forecast series `p^p`, `C^p`; optional error metadata on `Time_series` | `Time_series.py` / case data |
| **Model** | Deterministic equivalents (71)–(72); truncated-normal quantiles | `convex_model.py` or preprocessed `Param` |
| **Problem** | γ sweep {0.7, 0.8, 0.9}; scenario flags wind / price / both | `convex_ACDC.py` |
| **Solution** | Table 4 style revenue comparison | `Results_class.py` |

### 5.4 Robust MI-SOC EMP (Paper B)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | `CapacitorBank`, `CRPD`; robust deviation params | `Classes.py`, `grid_modifications.py` |
| **Model** | Eqs. (19)–(32) + robust counterpart (§3.1) | `convex_model.py` |
| **Problem** | Scenarios 1–5 driver | `convex_ACDC.py` |
| **Solution** | Loss and cost tables vs MATPOWER / NLP | Tests |

### 5.5 Hydrogen subsystem (Paper A §2.1)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | `Electrolyser` linear coeffs `c_k`, `d_k`; `H2_mass_min/max` | Mostly exists — verify Eq. (14)–(16) |
| **Model** | Mass balance, min electrolyser power, optional daily quota | `convex_model.py` |
| **Problem** | 24 h coupled horizon | `convex_ACDC.py` |
| **Solution** | Fig. 10 style production profile | Results / plots |

---

## 6. Phased roadmap (design only — no coding until owner sign-off)

| Phase | Goal | Exit criterion |
|-------|------|----------------|
| **0** | Resolve architecture + solver + Paper A vs B priority | U-A*, U-S*, U-G* tentatively answered |
| **1** | `convex_model.py` SOC kernel + sparse edges on **AC-only toy** | SOC feasible; voltage within tolerance vs known solution |
| **2** | Full **AC/DC hub** deterministic MI-SOCP (Paper A §2–3) on simplified PEI | Table 3 objective gap < owner tolerance |
| **3** | Multi-period + BESS MI + H₂ on simplified grid | Figs. 8–10 qualitative match |
| **4** | Sparse scaling on full PEI (172 AC) | Solve completes; revenue ballpark §5.2 |
| **5** | CCP layer (Paper A §4) | Table 4 qualitative revenue ordering |
| **6** | Paper B IEEE 33 EMP + robust | Scenario 2–5 cost/loss trends |
| **7** | Docs, citations, `Results` hooks, CI fixtures | Doc tests with `build_only` where no MOSEK |

Phases 6–7 can be **reordered or split** if offshore hub (Paper A) is priority for pyflow's
PEI track record.

---

## 7. Queries before implementation

Explicit questions that need answers **before coding starts**. Each maps to one or more
uncertainty IDs in §8. Answers may come from pyflow owners, Mario / CITCEA authors,
reference scripts, or a validation spike — not assumed here.

### 7.1 Scope and priority

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-1 | Is **v1** scoped to **Paper A only** (PEI sparse SOCP + CCP), with Paper B (ADN EMP) deferred? | Phases 0–7 ordering | Product / pyflow owner | U-A2, U-G3 |
| Q-2 | Should the convex stack **replace**, **complement**, or **benchmark against** existing `window_nl_opf` on PEI? | API messaging, tests | pyflow owner | U-A3, U-C3 |
| Q-3 | Is a **simplified 12 AC / 4 DC** PEI case required for Table 2 regression, or is full **172 AC** the only validation target? | Example grids, Phase 1–2 | Authors / owner | U-U3 |
| Q-4 | Is **Paper B** (capacitor banks, CRPD, IEEE 33) in scope for the same release as Paper A? | `Classes.py`, Phase 6 | pyflow owner | U-A2, U-C1 |

### 7.2 Architecture and API

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-5 | Confirm **two-file split**: `convex_model.py` (build) + `convex_ACDC.py` (run) — or prefer a single module? | File layout | pyflow owner | U-A1 |
| Q-6 | One public entry point with a **mode flag** (`energy_hub_socp`, `energy_hub_ccp`, …) or separate functions per problem? | `__init__.py` export | pyflow owner | U-A1 |
| Q-7 | Reuse / fork **`translate_pyf_opf`** packing, or build a dedicated `translate_pyf_convex` from scratch? | `convex_ACDC.py` | Implementer + owner | U-A4 |
| Q-8 | Should multi-period coupling follow **`window_opf.py`** (parent SoC / H₂ links) or a standalone 24 h solve in v1? | Horizon assembly | pyflow owner | U-A3 |
| Q-9 | How should **`w_{km}`** be represented in Pyomo — complex variable, or Re/Im pair? | SOC kernel | Mario / implementer | U-A5 |

### 7.3 Solver and dependencies

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-10 | What is the **mandatory v1 solver** — MOSEK (paper default), Gurobi, CPLEX, or an open-source conic option? | `[OPF]` extras, CI | pyflow owner / infra | U-A7, U-S1 |
| Q-11 | Is a MOSEK (or commercial) license available in **CI**, or must tests use `build_only=True` only? | `pyflow_tests` | DevOps / owner | U-D6, U-S1 |
| Q-12 | Acceptable **MIP gap / time limit** for BESS charge/discharge binaries at 24 h × full PEI? | Phase 4 performance | Authors / owner | U-S2, U-S4 |
| Q-13 | Extend **`pyomo_model_solve`** for conic stats, or keep a separate solve path in `convex_ACDC.py`? | Solver layer | pyflow owner | U-S3 |

### 7.4 Formulation and physics

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-14 | Does the Paper A **export revenue** objective use **linear** `C·p_exp` (bypassing quadratic `Price_Zone`), or adapt existing price-zone machinery? | Objective assembly | Mario / owner | U-A6 |
| Q-15 | Should convex BESS enforce **MI exclusivity** (Eqs. 22–23) even though NL OPF allows overlap (G6)? | BESS block | Mario / owner | U-C3 |
| Q-16 | Is the **H₂ daily production quota** (43 448 kg in §5.2.4) a hard constraint in v1? | H₂ block | Authors | U-M6 |
| Q-17 | For CCP: are **truncated-normal quantiles** precomputed offline and passed as params, or computed inside the builder? | CCP layer | Mario / implementer | U-M7 |
| Q-18 | For Paper B robust EMP: use **YALMIP-style automatic robust counterpart** logic ported to Pyomo, or a hand-derived worst-case formulation? | Robust layer | Mario / Walter Gil-González | U-M9 |
| Q-19 | What **objective / voltage tolerance** counts as “paper parity” for Table 3 (e.g. 0.001 % on revenue)? | Phase 2 exit | Authors / owner | U-D5 |

### 7.5 Data, cases, and validation

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-20 | Is bundled **`PEI_grid.py` + `_pei_bess_data.py`** sufficient for Paper A validation, or is a new simplified case file needed? | Examples | Owner + authors | U-D1, U-U3 |
| Q-21 | Can authors share **CVXPY/MOSEK reference logs** (objective, var counts, timing) for Table 2–3 reproduction? | Validation | Mario / CITCEA | U-G2 |
| Q-22 | Is there **reference Python** (ADOreD / FAIR) beyond the published papers to align sparse SOC indexing? | Phase 1 | Authors | U-G4 |
| Q-23 | For Paper B: provide **IEEE 33-bus case data** as a pyflow example grid, or import from MATPOWER at test time? | Phase 6 | Authors / owner | U-U6 |
| Q-24 | Which **CCP confidence levels** (γ = 0.7, 0.8, 0.9) are required in v1 tests vs optional sweeps? | Phase 5 tests | Owner | U-D3 |

### 7.6 Governance

| Q-ID | Question | Blocks | Likely source | Uncertainty |
|------|----------|--------|---------------|-------------|
| Q-25 | Who **signs off** on the Pyomo port of sparse SOC + CCP before Phase 1 merge? | All phases | Mario / CITCEA | U-G1 |
| Q-26 | Should **`Results.all()`** gain a new `convex_opf()` section, or reuse existing OPF result tables? | Results / Dash | pyflow owner | U-C2, U-C4 |

### 7.7 Minimum answers to start Phase 0 skeleton

At least tentatively resolve **Q-1, Q-5, Q-10, Q-14, Q-19, Q-25** before any code is
written. **Paper-faithful PEI validation** additionally needs **Q-20, Q-21**. Paper B work
needs **Q-4, Q-18, Q-23** answered first.

---

## 8. Uncertainties blocking implementation start

Full catalog of open items. §7 distils the blocking subset into explicit queries. Owners
resolve when ready; none assume the reader already knows the answer.

### 8.1 Architecture and scope

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-A1 | **Single vs dual entry points** — one `convex_optimize(...)` with mode flag vs separate hub/ADN functions | API surface in `convex_ACDC.py` |
| U-A2 | **Paper B in v1?** — PEI focus may defer ADN EMP entirely | Scope of `Classes` / examples |
| U-A3 | **Horizon wrapper** — standalone 24 h solve vs `window_*` pattern for SoC/H₂ linking | Code reuse vs duplication |
| U-A4 | **Relationship to `translate_pyf_opf`** — fork vs shared packers for `AC_info` / `DC_info` | Maintenance burden |
| U-A5 | **Complex Pyomo variables** — implement `w_{km}` as Re/Im pair vs polar auxiliary | Eq. (54) conjugation bookkeeping |
| U-A6 | **Export objective** — bypass `Price_Zone` quadratic machinery for linear Paper A revenue | Objective assembly location |
| U-A7 | **Licensing** — MOSEK (paper default) vs open-source conic (ECOS, CLARABEL, HiGHS conic?) | CI and user install story |

### 8.2 Mathematical formulation

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-M1 | **SOC relaxation tightness** — gap vs polar NLP on meshed vs radial PEI | When to warn users |
| U-M2 | **Paper A Eq. (3) DC balance** vs pyflow `Ybus_DC` convention | Sign of `ρ`, grounding |
| U-M3 | **Converter model embedding** — nodal admittance vs separate `Converter_*` block | Match paper unified matrix |
| U-M4 | **Line limits (40)–(43)** — shunt admittance `y^sh` indexing | Thermal limit orientation `km` vs `mk` |
| U-M5 | **BESS Eq. (17) time units** — paper minute-scale; `Storage.dt_hours` in pyflow | SoC scaling in convex block |
| U-M6 | **H₂ daily quota** — hard cumulative constraint vs soft penalty | §5.2.4 policy constraint |
| U-M7 | **CCP truncated normal quantiles** — analytic formula vs lookup table | Precompute per `(k,t)` |
| U-M8 | **Spatial wind correlation** — paper Remark 1: node-wise CCP ignores correlation | Conservative bias acknowledged? |
| U-M9 | **Robust counterpart (Paper B)** — explicit Löfberg reformulation vs manual worst-case epigraph | Convexity preservation |
| U-M10 | **Paper B Eq. (2) conjugate notation** — complex balance sign convention vs pyflow NL | Power injection direction |
| U-M11 | **Integer capacitor `ξ_k` domain** — {0,…,N_steps} vs simplified binary | MI size |

### 8.3 Units, per-unit, and grid mapping

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-U1 | **Paper A physical units (W, V)** vs pyflow pu on `S_base` | All exports to `Grid` |
| U-U2 | **`h_k` definition** — paper p.u.² vs kV² on DC (`ℎ^dc` nomenclature) | Eq. (47) bounds |
| U-U3 | **PEI simplified 12-bus** — does bundled `PEI_grid` subsample or need new case file? | Table 2 reproduction |
| U-U4 | **172-turbine forecasts** — `_pei_bess_data.py` shape (160×24) vs paper 160 turbines | Wake / aggregation |
| U-U5 | **Export link modeling** — ext grid gens at BE/UK/DK vs explicit `p_exp` vars | Revenue constraint |
| U-U6 | **IEEE 33-bus case** — not in repo; create `example_grids/` case or external MATPOWER import | Paper B validation |
| U-U7 | **DG reactive limits** — circle `‖s‖ ≤ s^max` on rectangular lift | Q capability reporting |

### 8.4 Data and reproducibility

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-D1 | **Full PEI parameters** — paper cites [9] for details; alignment with `PEI_grid.py` | Parameter parity |
| U-D2 | **Price series Fig. 5** — match `_pei_bess_data` export prices | Revenue validation |
| U-D3 | **CCP forecast errors** — σ = 10 % rule; turbine rating truncation per node | Table 4 quantitative |
| U-D4 | **Paper B generation costs** — Table 2 USD/kWh values | Scenario 2 cost baseline |
| U-D5 | **Acceptance tolerances** — 0.001 % objective (A) vs 0.002 % (B) vs CI practicality | Phase exit gates |
| U-D6 | **Public CI without MOSEK** — `build_only=True` sufficient? | Test design |

### 8.5 Solver, numerics, and performance

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-S1 | **Primary conic MIP solver** — MOSEK vs Gurobi vs CPLEX availability in target env | `[OPF]` optional extra naming |
| U-S2 | **MI-SOCP at 172×24 scale** — memory / time budget | Phase 4 feasibility |
| U-S3 | **`pyomo_model_solve` extension** — conic constraint support in existing parsers | Progress logs / stats |
| U-S4 | **MIP gap for BESS binaries** — 24×2 binaries per storage unit | Optimality vs speed |
| U-S5 | **Warm-start from NLP** — initialize `h` from `V²` after `optimal_pf` | Heuristic only — not in paper |

### 8.6 Class model and integration

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-C1 | **New device classes vs attributes on `Node_AC`** | Grid mutability / export |
| U-C2 | **`grid.convex_opf_run` vs reuse `opf_run`** | `Results.all()` routing |
| U-C3 | **Coexistence with G6 (overlap allowed) in NL** — convex path stricter; document divergence | User confusion |
| U-C4 | **Dash / plotting** — new SOC-specific views or reuse NL panels | Phase 7 scope |

### 8.7 Governance

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-G1 | **Formulation owner** — Mario / CITCEA sign-off on sparse + CCP Pyomo port | Before Phase 1 |
| U-G2 | **Reference logs** — CVXPY/MOSEK benchmarks shareable for Table 2–3? | Quantitative validation |
| U-G3 | **Paper A vs B priority** for pyflow product roadmap | Phase ordering |
| U-G4 | **CVXPY reference code** — any ADOreD / FAIR scripts to align with | Avoid re-derivation errors |

### 8.8 Suggested resolution order (non-binding)

See §7.7 for the query-level minimum. Full catalog: architecture skeleton after
**U-A1, U-A5, U-S1, U-U1, U-G1**; PEI validation additionally **U-D1, U-D5, U-G2**;
Paper B after **U-A2, U-U6, U-C1**.

---

## 9. File touch list

| File | Action |
|------|--------|
| **`pyflow_acdc/convex_model.py`** | **New** — SOC/MI-SOCP builder (sparse kernel + subsystem blocks) |
| **`pyflow_acdc/convex_ACDC.py`** | **New** — runners, translate, solve, export |
| `__init__.py` | Export public entry point(s) |
| `Classes.py` | Optional: `CapacitorBank`, `CRPD`; uncertainty params |
| `grid_modifications.py` | Optional: `add_capacitor_bank`, `add_crpd` |
| `constants.py` | Optional: `ConvexFormulation`, `UncertaintyMode` enums |
| `pyomo_model_solve.py` | Optional: conic solver detection / stats |
| `solver_utils.py` | Optional: MOSEK / conic capability probe |
| `Results_class.py` | Optional: `convex_opf()` report methods |
| `example_grids/PF/` or `example_grids/OPF/` | Optional: simplified PEI 12-bus; IEEE 33 ADN |
| `docs/usage_convex.rst`, `docs/citing.rst` | User guide + citations |
| `pyflow_tests/...` | Validation vs Tables 2–4 (A), Scenarios 1–5 (B) |

**Do not modify (v1)**

| File | Reason |
|------|--------|
| `ACDC_OPF_NL_model.py` | NLP stack remains canonical operational path |
| `ACDC_Static_TEP.py`, `ACDC_MultiPeriod_TEP.py` | Unrelated planning class |
| `window_opf.py` | Optional benchmark peer only |
| `bess_sizing.py` (planned) | Sibling sizing problem |

---

## 10. References

### Primary

M. Useche-Arteaga et al., *Efficient AC/DC energy hubs operation using sparse SOCP
relaxation and chance-constrained optimization*, Sustainable Energy, Grids and Networks
**46**, 102217 (2026). https://doi.org/10.1016/j.segan.2026.102217

M. Useche-Arteaga et al., *Robust energy management in active distribution networks using
mixed-integer convex optimization*, Electr. Power Syst. Res. **241**, 111367 (2025).
https://doi.org/10.1016/j.epsr.2024.111367

### Related pyflow / predecessor NLP paper

M. Useche-Arteaga et al., *Optimizing the operation of energy islands with predictive
nonlinear programming* (PEI case study), Wind Energy Sci. **11**, 349–372 (2026).
Implemented in [bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) (`window_nl_opf`).

### Convex optimization background (cited in papers)

A. Garces, *Mathematical Programming for Power Systems Operation* (Wiley, 2022) — SOC
lift Eqs. parallel to Paper B §3.

S. H. Low, Convex relaxation of optimal power flow, IEEE Trans. Control Netw. Syst. **1**(1)
(2014).

J. Löfberg, Automatic robust convex programming, Optim. Methods Softw. **27**(1) (2012) —
robust counterpart (Paper B).

### pyflow_acdc siblings

[bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) — operational NLP BESS + H₂.

[bess_sizing_ramp_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_sizing_ramp_plan.md) — plant-level BESS sizing (separate build).
