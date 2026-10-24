Linear Models (OPF and TEP)
===========================

Linearised AC(/DC) counterparts of the :doc:`OPF <opf>` and :doc:`TEP <tep>`
modules. [1]_ They trade full AC (and nonlinear DC/converter) accuracy for
speed and LP/MILP-solvability, making them suitable for fast studies, large
sweeps, and the Pyomo backend of :func:`~pyflow_acdc.wind_farm_CSS`.

Component formulations (Non-linear vs Linear) are documented on the system
modelling pages: :doc:`modelling_ac`, :doc:`modelling_dc`,
:doc:`modelling_acdc_converter`, and :doc:`modelling_storage_hydrogen`.

Model construction lives in ``pyflow_acdc.L_models.AC_OPF_L_model``; operational
drivers are :func:`~pyflow_acdc.optimal_l_pf`,
:func:`~pyflow_acdc.window_l_opf` / :func:`~pyflow_acdc.rolling_window_l_opf`,
and myopic :func:`~pyflow_acdc.ts_acdc_l_opf` (:doc:`ts`). TEP drivers
(:func:`~pyflow_acdc.linear_transmission_expansion`,
:func:`~pyflow_acdc.linear_multi_period_transmission_expansion`) live in
``pyflow_acdc.L_models.ACDC_L_TEP`` (**AC-only** investment layer for now;
hybrid ``TEP=True`` raises). Drivers accept ``build_only=True`` to build and
export initializer values without a solver.

Linearised AC(/DC) Optimal Power Flow
-------------------------------------

Sets up and solves the linearised OPF: it creates the
:ref:`linear model <L_model_creation>`, minimises the weighted objective, solves
with a Pyomo LP solver, and exports the solution back to the ``grid``. Supported
objective terms are generator ``Energy_cost`` and optional ``H2_sale``.
When ``grid.ESS`` / ``grid.H2``, BESS (P-only) and electrolysers are included.
Hybrid grids use ``grid.ACmode`` / ``grid.DCmode``: AC Bθ plus linearized DC
flows and thin converters; ``fx_conv`` PDC/PQ/PV apply (Q fix skipped — no
``Q_conv_s_AC``). ``SoC_deviation`` is not supported (quadratic).

.. autofunction:: pyflow_acdc.optimal_l_pf

   Example on ``case24_OPF`` (AC-only LP; solved with the first available LP
   solver from ``PYOMO_LINEAR_SOLVERS``, otherwise ``build_only``):

   .. literalinclude:: ../../pyflow_tests/doc_examples/L_models/03_linear_opf.py
      :language: python
      :lines: 2-

   Hybrid AC/DC on ``case39_acdc``:

   .. literalinclude:: ../../pyflow_tests/doc_examples/L_models/05_hybrid_linear_opf.py
      :language: python
      :lines: 2-

Linear coupled window
---------------------

Multi-hour linear OPF with linked BESS SoC and H₂ inventory (same indexing as
the nonlinear window). Lives in ``pyflow_acdc.L_models.window_l_opf``.
Accepts AC-only and hybrid grids; BESS remains P-only. See also
:doc:`../usage_window_opf`.

.. autofunction:: pyflow_acdc.window_l_opf

.. autofunction:: pyflow_acdc.rolling_window_l_opf

   ``future_sight`` in ``[0, 1]`` matches
   :func:`~pyflow_acdc.rolling_window_nl_opf` (ceil steps; proportional H₂ on
   the foresight segment).

Linear Transmission Expansion Planning
--------------------------------------

Linear (MILP) counterpart of :func:`~pyflow_acdc.transmission_expansion`: combines
the TEP investment cost with the linear OPF operating cost (discounted to present
value when ``NPV`` is set) and solves the MILP. Supports line expansion,
reconductoring (REC), and conductor-size selection (CT). This is also the Pyomo
backend for :func:`~pyflow_acdc.wind_farm_CSS` when ``CSS_L_solver`` is a Pyomo
LP/MIP solver (not ``'ortools'``).

.. autofunction:: pyflow_acdc.linear_transmission_expansion

   Example on ``case118_TEP`` (MILP; solved with the first available MIP solver
   from ``PYOMO_LINEAR_SOLVERS``, otherwise ``build_only``). See
   :doc:`../usage_tep` for grid setup.

   .. literalinclude:: ../../pyflow_tests/doc_examples/L_models/01_linear_transmission_expansion.py
      :language: python
      :lines: 2-

   Reconductoring (REC) variant on ``case24_REC`` (see :doc:`../usage_tep` for how
   reconductoring candidates store two admittance sets per element):

   .. literalinclude:: ../../pyflow_tests/doc_examples/L_models/02_linear_reconductoring.py
      :language: python
      :lines: 2-

Linear Multi-Period Transmission Expansion
------------------------------------------

Linear (MILP) counterpart of :func:`~pyflow_acdc.multi_period_transmission_expansion`
for **AC-only** grids. Lives in ``pyflow_acdc.L_models.ACDC_L_TEP``; default solver is
Gurobi. See :doc:`../usage_mp_tep` for the nonlinear multi-period workflow and CSV
setup; the linear driver reuses the same investment series.

.. autofunction:: pyflow_acdc.linear_multi_period_transmission_expansion

   Example on ``case24_MP`` (``build_only`` when Gurobi is unavailable):

   .. literalinclude:: ../../pyflow_tests/doc_examples/L_models/04_linear_mp_tep_case24.py
      :language: python
      :lines: 2-

.. _L_model_creation:

Creating the Linear model
-------------------------

.. autofunction:: pyflow_acdc.L_models.AC_OPF_L_model.opf_create_l_model_acdc

**Variables**

The linear model includes variables for (gated by ``grid.ACmode`` /
``grid.DCmode``):

- AC node angles; AC generator / renewable active power; AC line P flows
- When ``DCmode``: DC voltages, linearized DC line flows, thin converter
  ``P_conv_s_AC`` / DC converter injections
- Optional BESS charge / discharge / SoC (when ``grid.ESS``; P-only, no Q)
- Optional electrolyser power / H₂ mass (when ``grid.H2``; no Q)

**Constraints**

The model enforces constraints for:

- AC nodal active power balance (linearized), including storage injection and
  electrolyser load when present
- When ``DCmode``: linearized DC nodal balance and ``PDC_from`` / ``PDC_to``;
  converter ``np·Ps + P_DC + np·(a + b·Ps) = 0``
- Generator / renewable aggregation at nodes
- Optional storage SoC balance and ``|P_net| ≤ P_max``
- Optional electrolyser mass balance
- AC branch linearized power flow equations
- Thermal limits (including linear big-M formulations for REC/CT states)
- Slack angle constraints
- Optional array network-flow conservation and investment-linking
- Optional investment bounds for generators and lines (if ``TEP=True``;
  AC-only — hybrid TEP not wired yet)

TEP/REC/CT Parameters and Variables
-----------------------------------

When ``TEP=True``, :func:`~pyflow_acdc.L_models.AC_OPF_L_model.opf_create_l_model_acdc` adds
the investment layer used by :func:`~pyflow_acdc.linear_transmission_expansion`
and :func:`~pyflow_acdc.wind_farm_CSS`.

.. autofunction:: pyflow_acdc.L_models.AC_OPF_L_model.TEP_parameters

   Sets parameters for TEP/REC/CT decisions (e.g., base multiplicities, initial configs, limits).

.. autofunction:: pyflow_acdc.L_models.AC_OPF_L_model.TEP_variables

   Adds investment variables:

   - Generator multiplicities (optional integer bounded by capability)
   - AC expansion line multiplicities (integer)
   - Reconductoring branch selection (binary)
   - Cable-type selection (binary per type and line)
   - Optional type-usage flags and array flow variables

Linearization of investment couplings
-------------------------------------

Coupling the investment decisions to the network flows produces **bilinear**
terms (decision variable :math:`\times` flow variable). Left as-is these make the
"linear" model non-convex and unsolvable by LP/MIP solvers such as GLPK, CBC, or
HiGHS. Each coupling is therefore reformulated exactly into mixed-integer linear
constraints. The building block is the standard big-M / McCormick envelope, which
is **exact for a binary** multiplied by a bounded continuous variable.

Conductor-size selection (CT / CSS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Selecting one conductor type per line multiplies a binary type-selector
:math:`ct\_branch_{l,c}` by the per-type flow :math:`ct\_PAC_{l,c}`. Auxiliary
variables :math:`z\_to_{l,c}` / :math:`z\_from_{l,c}` carry the flow of the
*selected* type only, enforced by big-M envelopes:

.. math::

   -M_c\, ct\_branch_{l,c} \le z_{l,c} \le M_c\, ct\_branch_{l,c}

   ct\_PAC_{l,c} - 2M(1-ct\_branch_{l,c}) \le z_{l,c} \le ct\_PAC_{l,c} + 2M(1-ct\_branch_{l,c})

where :math:`M_c` is the per-type rating and :math:`M` a valid flow bound. The
node balance then uses the linear :math:`\sum_c z_{l,c}`.

Reconductoring (REC)
~~~~~~~~~~~~~~~~~~~~~

A reconductoring line carries the flow of exactly one of two admittance states
(``0`` = existing, ``1`` = upgraded), selected by the binary
:math:`rec\_branch_l`. The node injection would otherwise contain
:math:`rec\_PAC_{l,0}\,(1-rec\_branch_l) + rec\_PAC_{l,1}\,rec\_branch_l`
(two binary :math:`\times` continuous products). Auxiliary variables
:math:`rec\_z\_to_{l,s}` / :math:`rec\_z\_from_{l,s}` carry the active state's
flow, with an **active indicator** per state
(:math:`rec\_branch_l` for state 1, :math:`1-rec\_branch_l` for state 0) and the
same big-M envelope shape as CT. This mirrors the CT/CSS pattern and is exact
because the selector is binary.

Transmission expansion (TEP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Line expansion multiplies the **integer** line count
:math:`NumLinesACP_l` by the per-circuit flow :math:`exp\_PAC\_to_l`. A single
McCormick envelope over the integer count would only be a *relaxation* (exact
only at the count bounds), and a plain big-M on the aggregate integer product is
not exact for intermediate counts. Because parallel candidates are **identical**,
the coupling is instead split as

.. math::

   NumLinesACP_l \cdot exp\_PAC\_to_l
   = \underbrace{N^{base}_l \cdot exp\_PAC\_to_l}_{\text{linear (Param count)}}
   + \sum_{j} p\_to_{l,j}

and each optional circuit :math:`j` beyond the base is modelled with its own
build binary :math:`exp\_build_{l,j}` and flow variable :math:`p\_to_{l,j}`
(disjunctive per-circuit big-M):

.. math::

   |p_{l,j}| \le S_l\, exp\_build_{l,j} \qquad
   |p_{l,j} - exp\_PAC\_to_l| \le 2 S_l\,(1 - exp\_build_{l,j})

so a circuit carries the reference flow when built and zero otherwise. The
binaries are tied back to the reported integer count by
:math:`NumLinesACP_l = N^{base}_l + \sum_j exp\_build_{l,j}` and ordered
(:math:`exp\_build_{l,j} \ge exp\_build_{l,j+1}`) to break symmetry. Since all
active circuits carry the same reference flow, :math:`\sum_j p_{l,j}` reproduces
the integer product **exactly**, and the model remains a true MILP solvable by any
MIP solver.

Renewable unit count and curtailment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the renewable unit count :math:`n_{rg}` is an integer investment variable and
the curtailment factor :math:`\gamma_{rg}` is free, the injection
:math:`P_{rg}\,\gamma_{rg}\,n_{rg}` is bilinear. The product is replaced by
:math:`y_{rg}` with

.. math::

   \gamma_{rg}^{\min}\, n_{rg} \le y_{rg} \le n_{rg}

and :math:`P_{rg}\, y_{rg}` enters the node balance and the energy cost. Since
:math:`\gamma_{rg}` appears only in this product, every :math:`y_{rg}` in the
interval corresponds to :math:`\gamma_{rg} = y_{rg}/n_{rg} \in [\gamma_{rg}^{\min}, 1]`,
so the reformulation is **exact**.

Exporting Results
-----------------

.. autofunction:: pyflow_acdc.L_models.AC_OPF_L_model.export_acdc_l_model_to_pyflow_acdc

   Exports the Pyomo solution back to the ``grid`` (internal helper; called by
   :func:`~pyflow_acdc.optimal_l_pf`, linear window / TS drivers, and
   :func:`~pyflow_acdc.linear_transmission_expansion`):

   - Generator dispatch and renewable gamma
   - AC node angles and injections; when hybrid, DC voltages / flows and
     converter P exports
   - AC line flows and losses (linearized, zero reactive)
   - TEP/REC/CT selections and flows (including optional array network-flow)
   - Optional post-processing for time-limit cases (oversizing analysis and fixes)

Solvers
-------

The linear models are solved by LP/MIP solvers in Pyomo (see
``PYOMO_LINEAR_SOLVERS`` in :doc:`constants`). Tested with GLPK and Gurobi.

**Notes**

- Plain linear OPF is an LP. Enabling REC/CT/TEP or array-flow variables makes the
  problem a MILP; prefer a MIP-capable solver (e.g., ``gurobi``, ``highs``).

**References**

.. [1] B.C. Valerio, P. Gebraad, M. Cheah-Mane, V. A. Lacerda and O. Gomis-Bellmunt,
       "Strategies for wind park inter array optimisation through Mixed Integer Linear Programming"
