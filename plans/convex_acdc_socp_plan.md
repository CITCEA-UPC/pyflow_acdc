# Convex AC/DC SOCP plan for pyflow_acdc

**Repository:** In-repo links target the [`mario_integration`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration) branch ([`plans/`](https://github.com/CITCEA-UPC/pyflow_acdc/tree/mario_integration/plans)).

Living implementation plan for **sparse second-order cone programming (SOCP)**,
**mixed-integer SOCP (MI-SOCP)**, and **chance-constrained programming (CCP)** from
Mario Useche-Arteaga et al. (SEGAN 2026 energy-hub paper).

Publication-grounded reference material is in §1–§5 and §7–§10. **Implementation
status (what is coded vs not)** is consolidated in **§0.4** — read that first.
Locked owner decisions: **§0.0** (L1–L28). Do not re-litigate L/Q locks without an
explicit change.

**Next work:** Phase **11** — ``socp_robust_*`` robust box + C&CG runners (§0.4 / §5.5).

**Primary reference (Paper A — sparse SOCP + CCP)**

M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Efficient AC/DC energy hubs operation using sparse SOCP relaxation
and chance-constrained optimization*, Sustainable Energy, Grids and Networks **46**, 102217
(2026). https://doi.org/10.1016/j.segan.2026.102217

**Companion reference (Paper R — robust MI-SOCP)**

M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Robust Optimal Operation of AC/DC Offshore Energy Hubs: Addressing
Wind Uncertainty with Mixed-Integer Second-Order Cone Programming*, manuscript (R3
revision, under review). Workspace copy:
`citcea_extras_pyflow/scop/Manuscript_Source_RO_ACDC_ENERGY_ISLANDS_R3 (1).pdf`.
Same PEI hub as Paper A, but **dense** SOCP with the VSC converter transformer/filter
impedance folded into the AC ``Ybus``, **MI-BESS** mutually-exclusive charge/discharge
binaries, and **robust box-uncertainty** on wind (worst-case via Column-and-Constraint
Generation) — not the truncated-normal CCP of Paper A. Paper R cites Paper A as its
sparse follow-up (its ref [33]). Summarised in §1.5; formulation in §5.4 / §5.5.

**Related pyflow_acdc assets**

| Document | Link |
|----------|------|
| BESS / H₂ operation (NLP, shipped) | [bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) |
| BESS sizing (separate build) | [bess_sizing_ramp_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_sizing_ramp_plan.md) |
| Architecture map | [docs/architecture.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/docs/architecture.md) |
| Example PEI grid (optional later) | [`PEI_grid.py`](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/pyflow_acdc/example_grids/PF/PEI_grid.py) |
| PEI window OPF tests (NLP peer) | [`test_pei_window_nl_opf_bess_h2.py`](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/pyflow_tests/test_pei_window_nl_opf_bess_h2.py) |

Local PDF (user-provided): `efficient.pdf` (2026).

Mario reference (workspace): `mario_implementation/scop/ACDC_PE_Simplified_Efficient_SOCP_Multiperiodo.py`
(+ local Autumn price CSVs; `wpp_forecast.csv` may still be needed for smoke runs).

---

## 0. Scope of this plan

### 0.0 Locked owner decisions

| ID | Decision |
|----|----------|
| L1 | **Scope:** sparse SOCP core (Paper A) + **optional MI-BESS exclusivity** (Phase 9, Paper R Eqs. 56–59) + **both** uncertainty methodologies as separate public runners — chance constraints (Paper A §4, Phase 10) and robust box + C&CG (Paper R §3.3, Phase 11). **Converter-in-``Ybus`` (option A)** still deferred (L8). ADN / other robust EMP papers **out of scope**. |
| L2 | Stack is **case-agnostic**: `socp_optimise(grid, …)` must load **any** pyflow `Grid` (+ time series / options). Do not design the API or builder around a single validation case. Case-specific regression (PEI tables, etc.) is deferred. |
| L3 | Modeling language is **CVXPY**, not Pyomo. |
| L4 | Files: **`convex_model.py`** (CVXPY build) + **`ACDC_convex.py`** (pyflow call layer). |
| L5 | Public entry point: **`socp_optimise`** (British spelling). |
| L6 | Optional dependency extra: **`[SOCP]`** in `pyproject.toml` (`cvxpy` + chosen solvers). Guarded import in `__init__.py`, same pattern as `[OPF]`. |
| L7 | Reference script: `mario_implementation/scop/ACDC_PE_Simplified_Efficient_SOCP_Multiperiodo.py` (sparse multiperiod). Align formulation with this + paper; case data stays outside the API. |
| L8 | **Ybus for SOCP (v1 = option B):** use existing AC Ybus / `Line_AC` topology. **Ignore** converter AC-side RL branches in the SOCP graph. Converters enter only as **AC↔DC power + loss + rating**. Later **option A:** a `CONVEX_Ybus` that adds AC nodes for converter elements. |
| L9 | Included AC series elements share one Ybus (lines / trafos / cables as line-class topology). |
| L10 | Bus roles from pyflow types: gen / export (ext-grid) / converter AC / zero-injection — generalise Mario’s hard-coded node lists. |
| L11 | Nodal balance uses **`conj(S) == flow`** (Mario: simpler conj-on-V bookkeeping). |
| L12 | Renewables v1: **`gamma` as parameter**, start with `gamma = 1` (P fixed to forecast×gamma, Q = 0). |
| L13 | Converter loss v1: **`Ploss = a + b·t`**, **`t ≥ |Re(Ss)|`** (Paper A affine `a+b·ℜ{s^c}`; bidirectional via abs; DCP). Uses ``a_conv`` / ``b_conv``. Defer NL ``c_rect·I²`` and Mario per-conv ± without abs. |
| L14 | DC polarity: **`pol = pcn`** as in Mario. |
| L15 | **AC and DC thermal / rating limits are mandatory** (Paper A Eqs. 4–7 → SOCP 40–43). Mario’s script omitted AC limits — **do not** omit them in pyflow. |
| L16 | Exports = ext-grid **negative** injections (pyflow). Paper/Mario revenue form: **`min Σ Re(S_export)·price`**. **Superseded for default runner by L27** (`Energy_cost`); `Ext_Gen` weight still available for priced-export style. |
| L17 | Mario Autumn price CSVs are **demo only**, not a canonical paper-table target. |
| L18 | **BESS default = G6 continuous** (NL twin): separate ``P_charge``/``P_discharge``, no exclusivity binaries, ``T``-indexed SoC. **Optional MI exclusivity (Phase 9):** runner kwarg ``bess_mi_exclusivity=False`` (default) on ``socp_optimise`` / ``soc_window_optimisation`` (and on chance/robust runners when they land). When ``True``: Paper R / Paper A MI block (Eqs. 20–23 / 56–59) — binaries ``y^c``/``y^d`` gate charge/discharge; ``y^c+y^d≤1``; SoC chain and S-circle unchanged; **MI-capable conic solver preferred** (MOSEK / Gurobi / SCIP); **warn** if only CLARABEL/SCS available or explicitly chosen. |
| L19 | **Sparse only — GREEN LIGHT.** Ship sparse edge-set SOCP exclusively. Do **not** plan or implement a dense SOCP path (paper Table 2 comparison is optional later research, not a product requirement). |
| L20 | Model is **grid pu only**; € scaling only in objective / reporting via `S_base`. |
| L21 | **One CVXPY model with `(…, T)` indexing**, not Pyomo-style per-frame submodels. Single-period = `T=1`; window = ordered `frame_ids` with `T = len(frame_ids)`. |
| L22 | Internal builder name: **`socp_model(grid, d)`**. Public runners — **deterministic:** **`socp_optimise`** + **`soc_window_optimisation`** (optional ``bess_mi_exclusivity``, L18); **chance-constrained (Phase 10):** **`socp_ccp_optimise`** + **`socp_ccp_window_optimisation`**; **robust box (Phase 11):** **`socp_robust_optimise`** + **`socp_robust_window_optimisation`**. All share one builder; uncertainty layers differ (§5.5). |
| L23 | Builder consumes a **prepared SOCP data object** only (no ad hoc `P_ren` / `P_ext_bounds` kwargs on the builder). Translation owns `T`, `frame_ids`, profiles. |
| L24 | **AC generators (incl. ext-grids) are decision variables** (`PGi_gen`, `QGi_gen`) with OPF-NL-style bounds. Ext-grids are **not** a separate asset class — same gen family, different limits / sell logic. |
| L25 | **Renewables stay separate** from gens: availability from TS → fixed (parameter) injection v1 (`gamma` param, L12). |
| L26 | Time series come from **`grid.Time_series`** (`type` + `element_name` + `data`). Elements do **not** hold arrays (only `TS_dict` links). `grid.Time_series` is always present (`[]` if empty) — access directly, no soft `getattr`. |
| L27 | Objective uses NLP **`ObjComponent` / `weights_def` / `default_obj_weights()`**. Supported v1: `Energy_cost`, `Ext_Gen`, `AC_losses`, `DC_losses`, `Converter_Losses`. Unsupported active weights → **hard `NotImplementedError`**. Default = `Energy_cost` w=1. |
| L28 | Flags **`grid.ACmode` / `grid.DCmode`** (from `analyse_grid`) gate DC / converter blocks. Converters require **both** AC and DC modes plus `conv_data`. |

### 0.1 Problem class (Paper A)

| Aspect | Paper A (SEGAN 2026) |
|--------|----------------------|
| System | Hybrid **AC/DC energy hub** (offshore island in the paper; any Grid in pyflow) |
| Objective | Paper: maximize **export revenue** (Eq. 1 / 37). pyflow v1 default: NLP-style **`Energy_cost`** (L27); priced export via `Ext_Gen` / L16 |
| Network | AC collection + HVDC + converters + export links |
| Assets (paper) | Wind, BESS (MI), H₂, CCP |
| Assets (pyflow v1) | Gens as vars (L24), wind/`gamma` (L12/L25), converters, AC/DC + limits, **BESS G6 + linear H₂** (L18); **optional MI exclusivity Phase 9**. Heat pumps **Phase 8 done** (Q-18 **A**). |
| Convex core | **Sparse SOCP** only (L19) |
| Uncertainty | **Phase 10** chance constraints (Paper A); **Phase 11** robust box + C&CG (Paper R); separate public runners (Q-27) |
| Time | Multi-period when TS present |

SOCP lifting: `h_k = |v_k|²`, sparse complex `w_km` (Mario), rotated SOC inequality.

### 0.2 In scope / out of scope

| In scope (product) | Out of scope |
|--------------------|--------------|
| Deterministic sparse SOCP (Phases 0–8 — **done**, §0.4) | Modifying `ACDC_OPF_NL_model.py` / `window_opf.py` in place |
| Optional MI-BESS, chance, robust runners (Phases 9–11 — **todo**, §0.4) | BESS sizing; TEP investment; dense SOCP (L19) |
| Any analysed `Grid` + `grid.Time_series` (L2) | ADN EMP papers; case-specific API design |
| Optional PEI / paper-table parity later (L2) | Pyomo port of SOCP stack |

### 0.3 Distinction from existing pyflow_acdc stacks

| Stack | Formulation | Relation to this plan |
|-------|-------------|----------------------|
| `optimal_pf` + `ACDC_OPF_NL_model.py` | **Nonlinear** polar OPF (`V`, `θ`) | Optional “exact” baseline later |
| `window_nl_opf` | Coupled multi-hour **NLP** on full grid + BESS + H₂ | Operational peer (Pyomo/IPOPT) |
| `soc_window_optimisation` | Coupled multi-hour **SOCP** (`T`-indexed CVXPY) + BESS/H₂ chain | This plan (L22) |
| `bess_sizing.py` (planned) | Plant-level POI NLP | Separate problem class |

**This plan adds a dedicated CVXPY SOCP / MI-SOCP stack** with its own model builder and
runner — not a patch to the shipped NLP builders.

### 0.4 Implementation status

Single source of truth for **what logic is in the tree** vs **what is still planned**.
Subsystem detail and equations remain in §5; paper background in §1.

#### Already done — logic implemented

Phases **0–4**, **6–9**, and **10** (chance-constrained runners).

| Area | Logic in code | Where |
|------|---------------|-------|
| **Stack** | `[SOCP]` extra; guarded exports; `build_socp_data`, `socp_model`, `translate_pyf_socp` | `pyproject.toml`, `__init__.py`, `convex_model.py`, `ACDC_convex.py` |
| **Runners** | `socp_optimise`, `soc_window_optimisation`; one `(…, T)` model; `grid.socp_run`, `grid.socp_results` | `ACDC_convex.py`, `Results_class.py` |
| **Sparse SOCP kernel** | Edge sets `E_AC`/`E_DC`; complex `w` + real DC lifts; rotated SOC; `conj(S)==flow` AC balance; DC balance + `pol=pcn` | `convex_model.py` |
| **Thermals** | AC + DC line rating limits (L15) | `ac_constraints`, `dc_constraints` |
| **Converters** | `Re(Ss)+Pdc+Ploss=0`; DCP loss `Ploss=a+b·t`, `t≥|Re(Ss)|`; `‖Ss‖≤Smax`; option B (no conv in Ybus, L8) | `converter_*` |
| **Gens / wind** | `PGi_gen`/`QGi_gen`; ren injection from `grid.Time_series` + `gamma` param | `generator_*`, `translate_pyf_socp` |
| **BESS (G6)** | Continuous `P_charge`/`P_discharge`, SoC chain, AC S-circle / DC `\|P_net\|`; AC+DC nodes | `storage_*` |
| **BESS (MI opt-in)** | ``bess_mi_exclusivity=True``: ``y_charge``/``y_discharge`` gate charge/discharge; ``y_c+y_d≤1`` (Paper R 56–59) | `storage_*`, `ACDC_convex.py` |
| **H₂ (linear)** | `P_electrolyser`, optional AC `Q`; mass chain `h=b_h·P·S_base·dt+c_h`; optional `H2_mass_final` | `hydrogen_*` |
| **Heat pumps** | NL Q twin (Q-18 **A**): `P`/`Q`/`E` chain; TS profiles; AC load injection | `heat_pump_*`, `translate_pyf_socp` |
| **Objective** | `ObjComponent` weights: `Energy_cost`, `Ext_Gen`, `AC_losses`, `DC_losses`, `Converter_Losses`, `H2_sale`, `SoC_deviation` | `ACDC_convex._build_objective` |
| **Chance (CCP)** | ``socp_ccp_optimise`` / ``socp_ccp_window_optimisation``; ``apply_ccp_quantiles`` on ``P_ren`` + prices | `ACDC_convex.py` |
| **Solver / CI** | `resolve_socp_solver` (MOSEK → CLARABEL → SCS); smoke tests build + solve | `solver_utils.py`, `test_socp.py` |
| **Docs** | Usage/API/modelling NL+L+SOCP pages; architecture pointer | `docs/`, `ARCHITECTURE.md` |

**Call flow (implemented):**

```
analyse_grid → translate_pyf_socp → socp_model → _build_objective → solve → _export_to_grid
```

#### Still to do — logic not yet implemented

| Priority | Phase | Logic to add | Entry / trigger | Detail |
|----------|-------|--------------|-----------------|--------|
| **1 — next** | **11** | Robust box uncertainty + C&CG loop | ``socp_robust_optimise``, ``socp_robust_window_optimisation`` | §5.5 family B; Paper R §3.3 |
| **2 — later** | — | Converter AC RL in Ybus | ``CONVEX_Ybus`` / L8 option A | Not started |
| **Optional** | — | PEI / paper-table parity; H₂ mandatory daily quota; NLP cross-benchmark | Tests / fixtures (L2) | §1.6, Q-16, Q-19 |

**Explicit non-goals (unchanged):** dense SOCP; in-place NLP builder edits; BESS sizing.

**Files (implemented vs todo):**

| File | Status |
|------|--------|
| `convex_model/convex_model.py` | **Done** — Phase 9 adds MI gating in `storage_*` |
| `ACDC_convex.py` | **Done** — Phase 9 kwarg; **Phase 10** chance runners; Phases 11 new runners |
| `solver_utils.py` | **Done** — Phase 9 MI backend selection |
| `test_socp.py` | **Done** — extend for MI / chance / robust smokes |

---

## 1. Paper summary — SEGAN 2026: sparse SOCP + CCP for AC/DC energy hubs

### 1.1 Problem class

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

### 1.2 Conventional dense SOCP (§2.2)

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

### 1.3 Sparse SOCP (§3) — key contribution

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

### 1.4 Chance-constrained programming (§4)

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

### 1.5 Companion paper (Paper R) — robust MI-SOCP with box uncertainty

Paper R is a **separate** Useche-Arteaga et al. manuscript (R3 revision) on the same
PEI hub. It shares the SOCP AC/DC core with Paper A but differs on three axes that map
directly onto pyflow's currently-deferred items:

| Axis | Paper A (sparse + CCP) | Paper R (robust MI-SOCP) |
|------|------------------------|--------------------------|
| Sparsity | Sparse edge-set ``w`` | **Dense** all-pairs ``w`` (defers sparse to Paper A / its ref [33]) |
| Converter embedding | Power + loss + rating; converter AC RL not in Ybus | **Transformer / filter / impedance folded into AC ``Ybus``** (pyflow "option A") |
| BESS | Continuous (no binaries) | **MI exclusivity**: binaries ``y^c``/``y^d`` |
| Uncertainty | Chance constraints, truncated-normal quantiles | **Robust box set** + worst-case via **C&CG** decomposition |

**Three stated innovations:** (1) SOCP relaxation of AC/DC power flow with converter
losses; (2) finite-horizon MI model for BESS + H₂ with mutually-exclusive
charge/discharge; (3) robust worst-case handling of wind availability.

**Deterministic MI-SOCP (Paper R Eqs. 39–65).** Objective ``max Σ_{t,i} C_{i,t}·p_exp``
(39). AC balance ``(s_k − d_k)* = Σ_m y_km w_km`` (40); DC balance
``p_dc,k = ρ Σ_m y_dc,km (u_dc,k − w_dc,km)`` (41). SOC lifts (42–43):
``‖[2 w_km ; u_k − u_m]‖ ≤ u_k + u_m`` (AC), analogous DC. AC thermals (44–45):
``(y_s,km + y_sh,km) u_k − y_s,km w_km ≤ s_km^max`` (both ends). DC thermals (46–47):
``ρ y_dc,km (u_dc,k − w_dc,km) ≤ p_km^max``. Converter loss (48)
``p_loss,k = a_c,k + b_c,k · p_c,k`` (affine in real power, single-sign — pyflow keeps
its bidirectional ``|Re|`` epigraph); rating ``‖s_c,k‖ ≤ s_c,k^max`` (49–50); balance
``p_dc,k = −Re{s_c,k} − p_loss,k`` (51). Wind cap ``p_w,k ≤ G_k,t · P_rated`` (52).

**BESS with MI exclusivity (Eqs. 53–61).**
``SoE_k,t = SoE_k,t−1 + η_c p^c_k,t − p^d_k,t / η_d`` (53); ``SoE_min ≤ SoE ≤ SoE_max``
(54); fixed initial/final ``SoE_ti = E_0, SoE_tf = E_f`` (55); ``0 ≤ p^c ≤ p^{c,max} y^c``
(56); ``0 ≤ p^d ≤ p^{d,max} y^d`` (57); ``y^c + y^d ≤ 1`` (58); ``y^c, y^d ∈ {0,1}``
(59); ``s^b = (p^d − p^c) + j q^b`` (60); ``‖s^b‖ ≤ s^max_b`` (61). BESS is complex
**demand** in the nodal balance.

**Green H₂ with daily quota (Eqs. 62–65).** ``M_k,t = M_k,t−1 + h_k,t`` (62);
``h_k,t = b_h p_e,k,t + c_h`` (63); ``p_e,min ≤ p_e ≤ p_e,max`` (64); fixed daily quota via
``M_ti = M, M_tf = M̄`` (65). Case study uses electrolyser min power 22.5 MW to avoid
energy-intensive restarts.

**Robust box uncertainty (Eqs. 68–71).** Wind availability
``G_k,t = Ĝ_k,t + G̃_k,t (z^+_k,t − z^−_k,t)`` with ``z^+ + z^− ≤ 1`` binaries, deviation
``G̃ = γ Ĝ`` (± percentage), bounded ``G ∈ [Ĝ − G̃, Ĝ + G̃]``. Robust counterpart
``min_x max_{β∈B} (−z)`` solved by **Column-and-Constraint Generation** (Master ↔
adversarial Subproblem, Algorithm 1) rather than a single-shot solve. Box set chosen for
tractability over Γ-robustness / Wasserstein-DRO.

**Validation / scale (reference figures).** Objective within **0.0002 %** of NLP; AC
voltage error ≤ 0.0023 %, DC ≤ 0.0003 %. 24-h robust case: 48 binaries + 3,528
continuous vars, MOSEK, ~4.17 s, 0 % gap. Economic benefit: deterministic 2,715,900 €;
±5 % → −5.07 %; ±10 % → −10.14 %. Solved in YALMIP (MATLAB) with MOSEK / Gurobi.

### 1.6 Paper case-study anchors (reference only — not v1 design drivers)

Paper configurations used in publication (for later optional parity checks / Mario
alignment). **Do not** hard-wire the API or builder to these cases (see L2).

| Configuration | Nodes | Paper purpose |
|---------------|-------|---------------|
| Simplified (Fig. 2) | 12 AC, 4 DC | Dense vs sparse vs NLP benchmark |
| Full PEI (Fig. 6) | 172 AC, 4 DC | Scalability + BESS + H₂ deterministic |
| CCP full PEI | 172 AC, 4 DC | γ = 0.7, 0.8, 0.9 scenarios |

Deterministic full-system revenue reference in paper: **7,112,732 €** / 24 h (§5.2).

---

## 2. What pyflow_acdc already has

### 2.1 Shipped — nonlinear operational stack (overlap with Paper A assets)

| Layer | Location | Paper A mapping | Gap |
|-------|----------|-----------------|-----|
| `Grid`, `Ybus_AC`, `Ybus_DC` | `Classes.py`, `analyse_grid` | Admittance for sparse edge construction | ✅ |
| Polar NL OPF (`V`, `θ`) | `ACDC_OPF_NL_model.py` | NLP baseline | Different formulation — not rectangular SOC lift |
| `Storage` + `storage_*` | `Classes.py`, NL model | Eqs. 17–25 | **No** charge/discharge binaries; overlap allowed (G6) |
| `Electrolyser` + `hydrogen_*` | `Classes.py`, NL model | Eqs. 13–16 | Linear H₂ map exists; daily quota constraint not verified |
| `Ren_Source` | `Classes.py` | Wind dispatch `p^w` | Curtailment via `gamma`; no CCP layer |
| `Price_Zone` / export gens | NL model | Export revenue objective | Quadratic zone costs — not Paper A linear `C·p_exp` |
| `window_nl_opf` | `window_opf.py` | Multi-period coupled NLP | IPOPT/Pyomo path; no SOCP |
| Example grids | `example_grids/` | Optional later checks | Not required for API design |

### 2.2 SOCP stack vs NLP stack

| Subject | NLP stack (shipped) | SOCP stack — see **§0.4** |
|---------|-------------------|---------------------------|
| Model builder | `ACDC_OPF_NL_model.py` (Pyomo) | `convex_model.py` (CVXPY) — **done** |
| Runners | `optimal_pf`, `window_nl_opf` | `socp_optimise`, `soc_window_optimisation` — **done** |
| MI-BESS exclusivity | G6 continuous (overlap allowed) | ``bess_mi_exclusivity=True`` — **done** (Phase 9) |
| Chance / robust uncertainty | — | Phase 10–11 runners — **todo** |
| Optional extra | `[OPF]` | `[SOCP]` — **done** |

---

## 3. Architecture: `convex_model.py` + `ACDC_convex.py` (CVXPY)

**Locked (L3–L6):** implement Mario's SOCP methodologies as **new, self-contained modules**
using **CVXPY**. Do **not** modify `ACDC_OPF_NL_model.py`, TEP builders, or `window_opf.py`
internals.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  EXISTING (unchanged)              │  NEW SOCP stack                           │
│  ACDC_OPF_NL_model (polar NLP)     │  convex_model.py — CVXPY SOCP/MI-SOCP    │
│  optimal_pf / window_nl_opf        │  ACDC_convex.py — socp_optimise /          │
│  IPOPT / [OPF]=pyomo               │  soc_window_optimisation + I/O             │
│                                    │  solve via CVXPY backends ([SOCP] extra)    │
└──────────────────────────────────────────────────────────────────────────────┘
         │                                      │
         │  optional benchmark / cross-check    │
         └──────────────────────────────────────┘
              same Grid in, compare objectives & voltages vs NLP (later)
```

### 3.1 Module split

| File | Responsibility | Analogue in codebase |
|------|----------------|----------------------|
| **`convex_model.py`** | `build_socp_data` + `socp_model`: edge sets, `h`/`w`, SOC, AC/DC balance, **AC+DC thermals**, converters, gens; later BESS/H₂/CCP | `ACDC_OPF_NL_model.py` |
| **`ACDC_convex.py`** | `translate_pyf_socp`; public **`socp_optimise`** + **`soc_window_optimisation`** (landed; **Phase 9** ``bess_mi_exclusivity``); **`socp_ccp_*`** (Phase 10); **`socp_robust_*`** (Phase 11); weighted objective; solve; export | `ACDC_OPF.py` |

Rationale for **two files**:

1. Even without BESS/H₂, AC + DC + converter + thermals + gens warrants **build** vs **run** split.
2. Mirrors existing `ACDC_OPF.py` / `ACDC_OPF_NL_model.py` split.
3. Keeps CVXPY optional: `ACDC_convex` / `__init__` can fail cleanly when `[SOCP]` is missing.
4. **One** `socp_model` with `(…, T)` indexing (L21); runners only differ in how `frame_ids` / `T` are prepared.

### 3.2 Public API

| Item | Locked / status |
|------|-----------------|
| Entry points (deterministic) | **`socp_optimise`** (single / `T=1`) + **`soc_window_optimisation`** (multiperiod) — **landed**; optional ``bess_mi_exclusivity`` (Phase 9, L18) |
| Entry points (chance-constrained) | **`socp_ccp_optimise`** + **`socp_ccp_window_optimisation`** — **Phase 10** (Paper A CCP) |
| Entry points (robust box) | **`socp_robust_optimise`** + **`socp_robust_window_optimisation`** — **Phase 11** (Paper R + C&CG) |
| Translate | **`translate_pyf_socp`** — shared by all runners (Q-7 locked) |
| Uncertainty config | Per-runner kwargs; **distinct names** for the two γ notions: `confidence_level` (CCP) vs `wind_deviation_fraction` (robust box). Missing required inputs → **hard error** (no silent fallback to deterministic). |
| Case binding | **None** — any analysed `Grid` with required assets/params |
| Builder | Internal **`socp_model(grid, d)`** only — prepared data object (L23) |

**Runner family (L22 / Q-27 locked):**

| Runner | Uncertainty | Solve | Paper |
|--------|-------------|-------|-------|
| `socp_optimise` / `soc_window_optimisation` | none | single SOCP | — (landed) |
| `socp_ccp_optimise` / `socp_ccp_window_optimisation` | truncated-normal quantiles on wind + price | single SOCP | Paper A §4 (Phase 10) |
| `socp_robust_optimise` / `socp_robust_window_optimisation` | box on wind availability ``G`` | C&CG loop (master ↔ subproblem) | Paper R §3.3 (Phase 11) |

All six call the same `build_socp_data` / `socp_model` core; chance and robust runners
add pre/post layers in `ACDC_convex.py` (quantile tightening vs outer C&CG orchestration).
Guarded export in `__init__.py` when `[SOCP]` is installed.

### 3.3 Optional dependency `[SOCP]`

Mirror `[OPF] = ["pyomo"]` in `pyproject.toml`:

```toml
SOCP = ["cvxpy"]   # solvers TBD (e.g. mosek); may also document [Gurobi]
```

- Guarded import in `__init__.py`: export `socp_optimise`, `soc_window_optimisation`,
  `translate_pyf_socp` when CVXPY is available (**landed**).
- Folded into `[All]` (**landed** as `cvxpy` alone).
- Solvers packaged inside `[SOCP]` vs documented separately: **open** (U-S1).

### 3.4 What stays outside the SOCP build

| Module | Policy |
|--------|--------|
| `ACDC_OPF_NL_model.py` | Unchanged — NLP remains default “exact physics” path |
| `ACDC_Static_TEP.py`, `ACDC_MultiPeriod_TEP.py` | Unchanged |
| `bess_sizing.py` | Sibling plan — no overlap |
| `window_opf.py` | Optional downstream benchmark only |
| `pyomo_model_solve.py` | **Not** used by this stack (CVXPY solve path) |

### 3.5 Rationale

1. SOCP is a **different mathematical object** from polar NLP — own builder, not a branch
   inside `ACDC_OPF_NL_model.py`.
2. Paper A reference stack is **CVXPY+MOSEK** — matching that avoids a double port
   (paper → Pyomo).
3. Conic solvers are not the IPOPT-centric `[OPF]` default — `[SOCP]` isolates optional
   dependency and licensing.
4. Sparse formulation is an **implementation strategy** inside `convex_model.py`, not a
   change to `Grid` topology storage.
5. Case-agnostic API (L2) keeps the stack reusable beyond PEI.

---

## 4. pyflow_acdc mapping: Classes → Model → Problem → Solution

### 4.1 Classes (`Classes.py`, `grid_modifications.py`, `constants.py`)

**Role:** parameters, topology, and post-solve results. SOCP **decision structure** lives in
CVXPY variables, not on element classes, until owner decides otherwise.

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

**Proposed class-layer actions (owner review)**

| ID | Action | Notes |
|----|--------|-------|
| C3 | Uncertainty kwargs on chance/robust runners only | `confidence_level`, wind/price error params (chance); `wind_deviation_fraction`, `ccg_tol` (robust). Keeps `Grid` free of stale flags. |
| C4 | **Do not** replace `Storage` with MI logic globally | Binaries only in SOCP BESS block |
| C5 | `grid.socp_run` flag (or sibling) | Results routing, like `window_opf_run` / `opf_run` |

### 4.2 Model (`convex_model.py`)

**Role:** CVXPY variables, SOC constraints, subsystem blocks. **Not** in NL or L builders.

#### 4.2.1 SOC kernel

```
convex_model.py
├── build_edge_sets(grid) → E_AC, E_DC from sparsity (k < m)
├── soc_lift_ac(...)     → h_k,t, w_km,t complex (Mario), SOC (55)
├── soc_lift_dc(...)     → h^dc, w^dc real, SOC (57)
├── linear_ac_balance(...)   → Eq. (54); conj(S)==flow (L11); bus roles (L10)
├── linear_dc_balance(...)   → Eq. (56); pol=pcn (L14)
├── thermal_limits_ac(...)   → Eqs. (40)–(43) **required** (L15)
├── thermal_limits_dc(...)   → DC rating limits (Mario + paper)
├── converter_acdc(...)      → Re(Ss)+Pdc+Ploss=0; Ploss=a+b·t, t≥|Re(Ss)| (L13); ‖Ss‖≤Smax
└── voltage_bounds_on_h(...) → Eqs. (46)–(47)
```

| Aspect | NL model (`ACDC_OPF_NL_model`) | SOCP model (`convex_model`) |
|--------|----------------------------------|-----------------------------|
| Language | Pyomo | **CVXPY** |
| Voltage representation | `V_AC`, `theta_AC` (polar) | `h_k`, sparse complex `w_km` |
| AC balance | `cos/sin` of angle differences | Linear in `w`, `h` with Ybus; `conj(S)` |
| DC balance | Polar / simplified | Lift → linear in `w^dc`, `h^dc`; `pol=pcn` |
| Line limits | Nonlinear branch flow | **AC + DC** SOCP-reformulated (L15) |
| Converter AC branches | Explicit in NL model | **Ignored in v1** (L8 option B) |
| Relaxation gap | — | SOC inequality ≤ tightness vs NLP |

#### 4.2.2 Paper A extensions

| Block | Eqs. | v1 status |
|-------|------|-----------|
| VSC-HVDC interface | (10)–(12) | **In** — power+loss only; no conv AC Ybus (L8/L13) |
| **AC thermal limits** | (40)–(43) | **In** — mandatory (L15); missing in Mario script |
| DC thermal limits | Mario + paper | **In** |
| Export revenue objective | (37) | Available via `Ext_Gen` / L16; **default runner uses `Energy_cost` (L27)** |
| Wind / renewables | (26) + gamma | **In** — `gamma` param, start at 1 (L12); TS from `grid.Time_series` (L26) |
| AC gens / ext-grids | — | **In** — decision vars `PGi_gen`/`QGi_gen` (L24) |
| BESS G6 (continuous) | (17)–(25) without MI | **Done** — `storage_*`; MI exclusivity Phase 9 |
| H₂ subsystem | (13)–(16) | **Done** — `hydrogen_*` (continuous linear) |
| **CCP layer** | (70)–(72) | **Phase 10** — `socp_ccp_*` runners |

**Sparse only — GREEN LIGHT (L19).** No dense SOCP mode in the product plan.

#### 4.2.3 CVXPY / solver note

Paper A uses **CVXPY+MOSEK**. pyflow NLP OPF remains Pyomo. This stack solves through
CVXPY’s solver interface (`problem.solve(solver=…)`). Target solver package list inside
`[SOCP]` is **open** (U-S1).

### 4.3 Problem (`ACDC_convex.py`)

**Role:** assemble full problem from any `Grid` + time series + uncertainty options; call
CVXPY solve; export.

| Runner concern | Direction |
|----------------|-----------|
| Horizon | `T` + ordered `frame_ids` from `translate_pyf_socp` (L21/L23) |
| Input TS | From **`grid.Time_series`** only (L26): renewables, prices; loads TBD |
| Mode switch | **Three runner families** (deterministic / chance / robust) — not one function with a mode enum (Q-27) |
| Objective | Weighted `ObjComponent` (L27); default `Energy_cost`; Mario L16 via `Ext_Gen` |
| Output | `grid.socp_results`; element updates via `_export_to_grid` |

**Relationship to `window_nl_opf`:**

| Feature | `window_nl_opf` | `soc_window_optimisation` (v1) |
|---------|-----------------|--------------------------------|
| Coupling | Multi-hour SoC / H₂ links | Multi-period network (`T`); no BESS/H₂ yet |
| Physics | Polar NLP | Sparse SOCP + AC/DC thermals |
| BESS exclusivity | No (G6) | Optional via ``bess_mi_exclusivity`` (Phase 9) |
| Uncertainty | None in deterministic v1 | **`socp_ccp_*`** (Phase 10) / **`socp_robust_*`** (Phase 11) |
| Solver | IPOPT (Pyomo) | CVXPY + conic solver |
| Single-period sibling | `optimal_pf` | `socp_optimise` (`T=1`) |

**Landed:** both runners share one `socp_model` (not a thin wrapper around independent per-frame solves).

### 4.4 Solution (`Results_class.py`, export, tests)

| Output | Paper reference | pyflow destination (TBD) |
|--------|-----------------|--------------------------|
| Total revenue | Tables 3–4 | `Results` summary method |
| Nodal `h_k` → voltage magnitude | Table 3 voltage check | `sqrt(h_k)` vs `V_AC` from NLP |
| Export powers | Fig. 8 | Time series export |
| BESS SoC / power | Fig. 9 | Storage results tables |
| H₂ production | Fig. 10 | Electrolyser results |
| CCP revenue sensitivity | Table 4 | Scenario comparison table |
| Solve stats (vars, constraints, time) | Table 2 | CVXPY / solver stats helper |

**Validation strategy:** deferred per L2. Prefer generic smoke tests (build + optional solve
on any small Grid) before paper-table reproduction. When Mario’s code/logs arrive, add
optional parity checks.

---

## 5. Subject-focused breakdown

Status key: **Done** = logic in tree (§0.4); **Next** / **Planned** = §0.4 still-to-do.

### 5.1 Sparse SOCP relaxation (Paper A §3) — **Done**

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | Nothing mandatory — `Ybus` sparsity from existing `analyse_grid` | `grid_analysis.py` read-only |
| **Model** | `E_AC`, `E_DC`; upper-triangular `w`; Hermitian conjugate in balance (Eq. 54); SOC on edges only (Eq. 55) | `convex_model.py` |
| **Problem** | Sparse edge sets only (L19); no `formulation='dense'` | `ACDC_convex.py` |
| **Solution** | Report variable/constraint counts; wall time | solver stats helper |

### 5.2 AC / DC thermal limits (Paper A Eqs. 40–43) — **Done**

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Classes** | Line ratings from existing `Line_AC` / `Line_DC` | Grid |
| **Model** | SOCP reformulation of AC apparent/active limits; DC rating as in Mario + paper | `convex_model.py` |
| **Problem** | Always on unless explicitly disabled (fail-hard default: on) | `ACDC_convex.py` |
| **Note** | Mario script has DC limits only — pyflow **must** add AC (L15) |

### 5.3 Converter AC↔DC — **Done**

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Model** | `Re(Ss)+Pdc+Ploss=0`; `Ploss=a+b·t`, `t≥|Re(Ss)|` (L13); `‖Ss‖≤Smax`; no conv AC Ybus (L8) | `convex_model.py` |
| **Classes** | `a_conv`, `b_conv`, polarity `pcn` | Existing converter attrs |

### 5.4 MI-SOCP BESS — optional exclusivity — **Done (Phase 9)**

**Owner decision (Q-15):** MI charge/discharge exclusivity is the **largest BESS gap**
vs Paper R (Eqs. 56–59). Implement as an **opt-in runner flag** on the existing
deterministic SOCP path — **not** a separate public function family (unlike
chance/robust in §5.5).

**Default (``bess_mi_exclusivity=False``):** shipped G6 continuous block — separate
``P_charge``/``P_discharge``, overlap allowed, continuous SOCP solver (CLARABEL OK).

**When ``bess_mi_exclusivity=True``:** add Paper R / Paper A MI block on top of the
same SoC chain and S-circle (Eqs. 53–54, 60–61 unchanged):

```text
0 ≤ p^c_k,t ≤ p^{c,max}_k · y^c_k,t          # charge gated by binary
0 ≤ p^d_k,t ≤ p^{d,max}_k · y^d_k,t          # discharge gated by binary
y^c_k,t + y^d_k,t ≤ 1                         # mutually exclusive
y^c_k,t, y^d_k,t ∈ {0,1}
```

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **API** | ``bess_mi_exclusivity: bool = False`` on ``socp_optimise`` and ``soc_window_optimisation``; propagate through ``socp_model`` / ``storage_constraints``. Same flag on ``socp_ccp_*`` / ``socp_robust_*`` when those land. | `ACDC_convex.py` |
| **Model** | When flag set: ``cp.Variable(boolean=True)`` ``y^c``/``y^d`` per storage×``T``; replace direct ``P_charge``/``P_discharge`` upper bounds with gated bounds; keep SoC chain and AC/DC rating constraints unchanged. | `convex_model.py` (`storage_variables`, `storage_constraints`) |
| **Solver** | ``resolve_socp_solver`` prefers MI-capable backend (MOSEK / Gurobi / SCIP) when flag is ``True``; **warn** if a non-MI solver is resolved or passed explicitly. | `solver_utils.py` |
| **Tests** | Continuous default smoke unchanged; optional MI smoke (skip if no MI solver in CI). | `test_socp.py` |
| **Docs** | SOCP modelling page: G6 default vs MI opt-in; Paper R parity note. | `modelling_flexible_assets.rst` |

**Exit criterion (Phase 9):** ``socp_optimise(..., bess_mi_exclusivity=True)`` builds and
solves on ``case39_acdc`` with one BESS when an MI solver is available; default path
unchanged.

**Note:** MI flag changes solver contract for that run only (U-D6/U-S1). Independent of
Phase 10–11 uncertainty runners — any combination (continuous + chance, MI + robust, …)
is valid if the solver supports it.

### 5.5 Wind uncertainty — **Planned (Phase 10 + 11)**

**Owner decision (Q-27):** implement **both** Paper A chance constraints and Paper R
robust box uncertainty as **separate public runner families** (L22), not a single
`socp_optimise(..., mode=…)` switch. Shared deterministic core; different pre/post
layers and solve orchestration.

#### Runner family A — chance constraints (Paper A §4) — **Done (Phase 10)**

Per-node truncated-normal quantiles tighten wind and price caps before a **single** SOCP
solve:

```text
p^w_k,t ≤ p̂^w_k,t + Q_{1−confidence_level}(ε_w)
C_k,t   ≤ Ĉ_k,t   + Q_{1−confidence_level}(ε_c)
```

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Translate** | Optional wind/price forecast-error params; precompute quantiles per ``(k,t)`` | `translate_pyf_socp` or chance-runner prep |
| **Model** | Quantile-shifted RHS on renewable caps and price terms in objective/bounds | `convex_model.py` or data object fields |
| **Runners** | **`socp_ccp_optimise`**, **`socp_ccp_window_optimisation`** — same export path as deterministic | `ACDC_convex.py` |
| **Config** | `confidence_level` (Paper A γ); wind/price error σ and truncated-normal bounds | runner kwargs |
| **Solver** | Continuous SOCP — CLARABEL/MOSEK/SCS still OK | existing `resolve_socp_solver` |
| **Tests** | Build + solve smoke; optional PEI revenue sensitivity vs Paper A Table 4 | `test_socp.py` |

Conservative bias; ignores spatial correlation (Paper A Remark 1).

#### Runner family B — robust box + C&CG (Paper R §3.3) — **Phase 11**

Box uncertainty on wind availability; worst-case dispatch via **Column-and-Constraint
Generation**:

```text
G_k,t = Ĝ_k,t + G̃_k,t (z^+_k,t − z^−_k,t),   z^+ + z^− ≤ 1
G̃_k,t = wind_deviation_fraction · Ĝ_k,t
G_k,t ∈ [Ĝ_k,t − G̃_k,t, Ĝ_k,t + G̃_k,t]
min_x max_{β∈B} (−z)   solved by Master ↔ Subproblem loop (Algorithm 1)
```

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Orchestration** | Outer C&CG loop: solve master MI-SOCP at β* → adversarial subproblem for worst β → update bounds until ``UB − LB ≤ ccg_tol`` | `ACDC_convex.py` (new module or `_robust_ccg_*` helpers) |
| **Model** | Box-set vars on ``G``; master uses same `socp_model` with worst-case availability injected | `convex_model.py` + robust prep |
| **Runners** | **`socp_robust_optimise`**, **`socp_robust_window_optimisation`** | `ACDC_convex.py` |
| **Config** | `wind_deviation_fraction` (Paper R γ — **not** the same as `confidence_level`); `ccg_tol` | runner kwargs |
| **Solver** | MI-capable conic solver if ``bess_mi_exclusivity=True`` on same run; continuous robust-only may use iteration wrapper only | `solver_utils.py` |
| **Tests** | C&CG convergence smoke; optional ±5 % / ±10 % scenarios vs Paper R Table 7 | `test_socp.py` |

Implement **Phase 10 before Phase 11** — chance is a thin layer on the existing
single-shot path; robust adds outer-loop complexity. **Phase 9 (MI-BESS) is independent**
and should land first (see §5.4).

#### Shared rules (both families)

- Fail fast if required uncertainty inputs are missing (no silent fallback to deterministic).
- Use **`confidence_level`** and **`wind_deviation_fraction`** in the public API — never
  overload a single ``gamma`` kwarg across runners.
- Export and `grid.socp_results` shape match deterministic runners; document which
  uncertainty assumption was used in run metadata / stats dict.

### 5.6 Hydrogen subsystem — **Done** (continuous linear)

| Layer | What to implement | Where |
|-------|-------------------|-------|
| **Model** | Linear mass balance / optional `H2_mass_final`; AC Q bounds | `convex_model.py` (landed continuous) |

### 5.7 Heat pumps — **Done** (Phase 8; Q-18 **A** NL Q twin)

Implemented in `heat_pump_variables` / `heat_pump_constraints`, `hp_data`,
`translate_pyf_socp` HP profiles, `_export_to_grid`. Full HP physics lock:
[`heat_pump_plan.md`](heat_pump_plan.md). Smoke: `test_socp.py` heat-pump cases.

---

## 6. Phased roadmap

Mirror of **§0.4** for phase numbering. **Done** = phases 0–4, 6–8. **Todo** = 9–11.

| Phase | Goal | Status |
|-------|------|--------|
| **0–4** | Stack, sparse SOCP, runners, smoke | **Done** |
| **5** | CCP slot | Superseded → Phase 10 |
| **6** | BESS G6 + H₂ linear | **Done** |
| **7** | Docs, Results, CI | **Done** |
| **8** | Heat pumps (Q-18 **A**) | **Done** |
| **9** | Optional MI-BESS (``bess_mi_exclusivity``) | **Done** — §5.4 |
| **10** | ``socp_ccp_*`` (Paper A CCP) | **Done** — §5.5 |
| **11** | ``socp_robust_*`` (Paper R box + C&CG) | **Next** — §5.5 |

---

## 7. Queries before / during implementation

Owner-locked items (**L1–L28**) are answered. Remaining opens below.

### 7.1 Architecture and API

| Q-ID | Question | Status |
|------|----------|--------|
| Q-1 | Paper A only? | **Locked L1** |
| Q-5 | Two-file split? | **Locked L4** |
| Q-6 | Public entry `socp_optimise`? | **Locked L5** (+ window L22); optional ``bess_mi_exclusivity`` (Phase 9); **Phase 10–11** add `socp_ccp_*` / `socp_robust_*` (Q-27) |
| Q-7 | Dedicated `translate_pyf_socp` vs fork `translate_pyf_opf`? | **Locked** — dedicated `translate_pyf_socp` (L23/L26) |
| Q-8 | Multi-period: standalone vs `window_*`? | **Locked L21/L22** — one `socp_model(…, T)`; `socp_optimise` + `soc_window_optimisation` |
| Q-9 | `w_{km}` complex vs Re/Im? | **Locked** — complex dict like Mario |

### 7.2 Solver and dependencies

| Q-ID | Question | Status |
|------|----------|--------|
| Q-10 | Solvers inside `[SOCP]` (MOSEK vs docs-only)? | **Resolved** — default preference `MOSEK → CLARABEL → SCS`; docs explain fallback |
| Q-11 | CI without commercial license? | **Resolved** — `[SOCP]` includes open-source Clarabel; tests skip if no conic solver; MOSEK never required |
| Q-12 | MIP gap (BESS) | **Open for Phase 9** — expose solver MIP gap when ``bess_mi_exclusivity=True`` |
| Q-13 | CVXPY solve path (not Pyomo) | **Locked L3** |

### 7.3 Formulation (mostly locked from Mario Q&A)

| Q-ID | Question | Status |
|------|----------|--------|
| Q-14 | Linear priced exports vs `Price_Zone` quadratic? | **L16 paper form**; default objective **L27 `Energy_cost`** |
| Q-15 | BESS MI exclusivity? | **Locked Phase 9** — optional ``bess_mi_exclusivity=False`` (default G6); ``True`` → Paper R Eqs. 56–59 (L18) |
| Q-16 | H₂ daily quota? | **Deferred** |
| Q-17 | CCP quantiles? | **Locked Phase 10** — `socp_ccp_*` runners; truncated-normal precompute per ``(k,t)`` |
| Q-18 | SOCP heat pumps: NL Q twin (**A**) vs L P-only (**B**)? | **Locked A** — NL Q twin (§5.7 / Phase 8) |
| Q-19 | Paper parity tolerances | **Open** / deferred with L2 |
| Q-27 | Wind uncertainty: one method or both? | **Locked** — **both**, as separate runner families: `socp_ccp_*` (Phase 10) + `socp_robust_*` (Phase 11); not a single `mode=` kwarg (L22) |
| Q-28 | Adopt Paper R beyond robust box (MI-BESS, converter-in-``Ybus``)? | **Partial** — **MI-BESS opt-in Phase 9** (L18); robust box Phase 11; converter-in-``Ybus`` (L8 option A) still deferred |

### 7.4 Data and reference

| Q-ID | Question | Status |
|------|----------|--------|
| Q-20 | Case-specific PEI fixtures | **Deferred L2** |
| Q-21 / Q-22 | Mario script | **Have** scop script (L7); still useful: `wpp_forecast.csv`, solve logs |
| Q-24 | CCP / chance-runner tests | **Phase 10** — `confidence_level` scenario smoke |

### 7.5 Governance / product

| Q-ID | Question | Status |
|------|----------|--------|
| Q-2 | Complement NLP (not replace)? | **Open** (default: complement) |
| Q-25 | Sign-off on port | Mario / CITCEA |
| Q-26 | `Results` section name | **Resolved** — reuse existing Results tables when `grid.socp_run`; full `T` arrays on `grid.socp_results` |

### 7.6 Where to start

See **§0.4 Still to do**. Next gate: Phase **10** (``socp_ccp_*``).

---

## 8. Uncertainties (Paper A / CVXPY only)

### 8.1 Architecture and scope

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-A3 | **Horizon wrapper** | **Resolved L21/L22** — one `socp_model` with `T`; `socp_optimise` + `soc_window_optimisation` |
| U-A4 | **Translate packing** | **Resolved** — dedicated `translate_pyf_socp` (L23/L26); does not fork `translate_pyf_opf` |
| U-A5 | **`w_{km}` representation** | **Locked** — complex (Mario) |
| U-A6 | **Export / gen objective** | **L16** paper revenue form available; **default = L27 `Energy_cost`** |
| U-A7 | **Licensing** — which solvers ship in `[SOCP]` vs docs-only | CI and install story |
| U-A8 | **AC thermal form** — exact Paper A (40–43) vs pyflow rating fields mapping | L15 requires AC limits; expression detail open |

### 8.2 Mathematical formulation

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-M1 | **SOC relaxation tightness** — gap vs polar NLP | When to warn users |
| U-M2 | **Paper A Eq. (3) DC balance** vs pyflow `Ybus_DC` | Sign of `ρ`, grounding |
| U-M3 | **Converter embedding** | **Locked L8** — v1 option B (power+loss only; no conv AC Ybus) |
| U-M4 | **Line limits (40–43)** — map paper form → pyflow `Line_AC` ratings | **Required** (L15); expression detail = U-A8 |
| U-M5 | **BESS Eq. (17) time units** — paper minute-scale vs `Storage.dt_hours` | SoC scaling |
| U-M6 | **H₂ daily quota** — hard vs soft / optional | §5.2.4 policy |
| U-M7 | **CCP truncated-normal quantiles** — analytic vs lookup | Precompute per `(k,t)` |
| U-M8 | **Spatial wind correlation** — node-wise CCP ignores correlation (Remark 1) | Document conservative bias? |

### 8.3 Units and grid mapping

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-U1 | **Physical vs pu** | **Locked L20** — model in grid pu |
| U-U2 | **`h_k` / `h^dc`** — pu² vs kV² | Eq. (47) bounds |
| U-U5 | **Export link modeling** | **Locked L16** — ext-grid negative injections |

### 8.4 Data and reproducibility

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-D3 | **CCP forecast errors** — σ = 10 %; truncation | Quantitative CCP |
| U-D5 | **Acceptance tolerances** if paper parity is pursued later | Optional exit gates |
| U-D6 | **Public CI without MOSEK** | Test design |
| U-G2 / U-G4 | **Reference logs / CVXPY code** from Mario | Avoid re-derivation (L7) |

### 8.5 Solver, numerics, and performance

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-S1 | **Primary conic MIP solver** for `[SOCP]` | Extra contents |
| U-S2 | **MI-SOCP scale** (large N × T) | Memory / time |
| U-S4 | **MIP gap** for BESS binaries | Optimality vs speed |
| U-S5 | **Warm-start from NLP** (`h ← V²`) | Heuristic only |

### 8.6 Class model and integration

| ID | Uncertainty | Why it matters |
|----|-------------|----------------|
| U-C2 | **`grid.socp_run` vs reuse `opf_run`** | `Results.all()` routing |
| U-C3 | **Coexistence with G6** in NL — SOCP path stricter | User docs |
| U-C4 | **Dash / plotting** — new SOCP views or reuse NL | Later scope |
| U-G1 | **Formulation sign-off** — Mario on CVXPY port | Before claiming paper parity |

### 8.7 Suggested resolution order

1. ~~Phases 0–9 (deterministic SOCP + optional MI-BESS).~~ **Done** — §0.4.
2. **Phase 10:** ``socp_ccp_*`` (§5.5).
3. **Phase 11:** ``socp_robust_*`` (§5.5).
4. Later: ``CONVEX_Ybus`` (L8 option A); optional PEI parity (L2).

---

## 9. File touch list

| File | Action / status |
|------|-----------------|
| **`pyflow_acdc/convex_model/convex_model.py`** | **Landed** — `build_socp_data`, `socp_model`, subsystem vars/constraints; **Phase 9:** MI gating in `storage_variables`/`storage_constraints` |
| **`pyflow_acdc/ACDC_convex.py`** | **Landed** — deterministic runners; **Phase 9:** ``bess_mi_exclusivity``; **Phase 10–11:** `socp_ccp_*`, `socp_robust_*` |
| `solver_utils.py` | **Landed** — `resolve_socp_solver` / `cvxpy_available`; **Phase 9:** MI backend when ``bess_mi_exclusivity=True`` |
| `__init__.py` | **Landed** — guarded export of deterministic runners + translate; extend for chance/robust when landed |
| `pyproject.toml` | **Landed** — `SOCP = ["cvxpy", "clarabel"]`; folded into `All` |
| `Classes.py` | **Landed** — `socp_run` cleared in `reset_run_flags` |
| `constants.py` | Optional: SOCP / CCP mode enums |
| `Results_class.py` | **Landed** — `socp_run` gates same flex/gen sections as `OPF_run`; `T` arrays on `grid.socp_results` |
| `docs/usage_socp.rst`, `docs/api/socp.rst`, modelling pages | **Done** — public SOCP usage + API + NL/L/SOCP; **Phase 9:** G6 vs MI note in `modelling_flexible_assets.rst` |
| `pyflow_tests/test_socp.py` | **Done** — build / solve / window / PEI / optional NLP compare; **Phase 9:** optional MI smoke (skip without MI solver) |

**Do not modify (v1)**

| File | Reason |
|------|--------|
| `ACDC_OPF_NL_model.py` | NLP stack remains canonical operational path |
| `ACDC_Static_TEP.py`, `ACDC_MultiPeriod_TEP.py` | Unrelated planning class |
| `window_opf.py` | Optional benchmark peer only |
| `pyomo_model_solve.py` | Wrong stack for CVXPY |
| `bess_sizing.py` (planned) | Sibling sizing problem |

---

## 10. References

### Primary

M. Useche-Arteaga et al., *Efficient AC/DC energy hubs operation using sparse SOCP
relaxation and chance-constrained optimization*, Sustainable Energy, Grids and Networks
**46**, 102217 (2026). https://doi.org/10.1016/j.segan.2026.102217

### Companion robust MI-SOCP paper (Paper R)

M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Robust Optimal Operation of AC/DC Offshore Energy Hubs: Addressing
Wind Uncertainty with Mixed-Integer Second-Order Cone Programming*, manuscript (R3
revision, under review). Workspace copy:
`citcea_extras_pyflow/scop/Manuscript_Source_RO_ACDC_ENERGY_ISLANDS_R3 (1).pdf`. Provides
the concrete formulations for MI-BESS exclusivity (§5.4), robust box uncertainty + C&CG
(§5.5), and converter-in-``Ybus`` embedding (option A). Summarised in §1.5.

### Related pyflow / predecessor NLP paper

M. Useche-Arteaga et al., *Optimizing the operation of energy islands with predictive
nonlinear programming* (PEI case study), Wind Energy Sci. **11**, 349–372 (2026).
Implemented in [bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) (`window_nl_opf`).

### Convex optimization background

A. Garces, *Mathematical Programming for Power Systems Operation* (Wiley, 2022) — SOC
lift background.

S. H. Low, Convex relaxation of optimal power flow, IEEE Trans. Control Netw. Syst. **1**(1)
(2014).

### pyflow_acdc siblings

[bess_integration_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_integration_plan.md) — operational NLP BESS + H₂.

[bess_sizing_ramp_plan.md](https://github.com/CITCEA-UPC/pyflow_acdc/blob/mario_integration/plans/bess_sizing_ramp_plan.md) — plant-level BESS sizing (separate build).
