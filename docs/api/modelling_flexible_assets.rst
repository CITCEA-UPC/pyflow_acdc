Flexible assets modelling
=========================

Operation-oriented battery energy storage (BESS), green-hydrogen electrolysers,
and controllable heat pumps for hybrid AC/DC grids.

BESS and electrolyser formulations follow Useche-Arteaga et al. (2026)
[#useche2026]_ (§3.3–§3.4). Heat pumps follow the planning-oriented controllable
load model of Montalà-Palau et al. (2026) [#montala2026]_ (§4.1). See
:doc:`../citing`.

Elements attach with :func:`~pyflow_acdc.add_storage` /
:func:`~pyflow_acdc.add_electrolyser` /
:func:`~pyflow_acdc.add_heat_pump` (:doc:`grid_mod`). Coupled multi-hour
runs: :doc:`window` / :doc:`../usage_window_opf`. Myopic sequential hours:
:func:`~pyflow_acdc.ts_acdc_opf` (:doc:`ts`).

.. _Storage_modelling:

Battery energy storage system
-----------------------------

Energy islands can improve flexibility by integrating storage to manage wind
intermittency, grid constraints, and curtailment. Conventional BESS with power
converters regulate active and (on AC) reactive power. The energy storage
system follows the linear model of Pozo (2022) as used in [#useche2026]_
Eqs. (24)–(31).

Paper energy-balance form (SoE :math:`e_t`, charging / discharging
:math:`P_t^{c}`, :math:`P_t^{d}`, efficiencies :math:`\eta_c`, :math:`\eta_d`):

.. math::
    :label: eq:bess_soe

    \begin{align}
        e_{t} &= e_{t-1} + \eta_c P_{t}^{c} - \frac{1}{\eta_d} P_{t}^{d}
            & \qquad \forall t \in \mathcal{T} \\
        e_{t}^{\mathrm{ini}} &= E_{0}, \quad
        e_{t}^{\mathrm{fin}} = E_{f} & \\
        e^{\min} &\leq e_{t} \leq e^{\max}
            & \qquad \forall t \in \mathcal{T} \\
        0 &\leq P_{t}^{c} \leq P^{c,\max},\quad
        0 \leq P_{t}^{d} \leq P^{d,\max}
            & \qquad \forall t \in \mathcal{T}
    \end{align}

On AC buses the converter capability curve limits apparent power
(:math:`s_{t}^{b}` net injection, rating :math:`s_{b}^{\max}`):

.. math::
    :label: eq:bess_s_circle

    \begin{align}
        s_{t}^{b} &= \bigl(P_{t}^{d} - P_{t}^{c}\bigr) + j\, q_{t}^{b}
            & \qquad \forall t \in \mathcal{T} \\
        \|s_{t}^{b}\| &\leq s_{b}^{\max}
            & \qquad \forall t \in \mathcal{T}
    \end{align}

**pyflow-acdc implementation.** SoC is stored in **pu** (fraction of
:attr:`~pyflow_acdc.Storage.E_max` in MWh). Charge/discharge decision variables
are in **pu** of ``S_base``. The discrete SoC update implemented in
:mod:`~pyflow_acdc.NL_models.ACDC_OPF_NL_model` is:

.. math::
    :label: eq:bess_soc_pyflow

    \mathrm{SoC}_{t}
    =
    \mathrm{SoC}_{t-1}
    +
    \frac{\Delta t\, S_{\mathrm{base}}}{E_{\max}}
    \Bigl(
        \eta_c P_{t}^{c} - \frac{P_{t}^{d}}{\eta_d}
    \Bigr)

with bounds ``soc_min`` / ``soc_max``, optional window terminal ``soc_final``,
and AC S-circle / DC net-:math:`P` limits. **Sign convention:** net active
power injected into the bus is ``P_discharge - P_charge``.

Linear model
^^^^^^^^^^^^

In the linear OPF stack the same SoC update is used, with a net active-power
limit and no reactive storage power:

.. math::
    :label: eq:bess_l

    \begin{align}
        \mathrm{SoC}_{t}
        &=
        \mathrm{SoC}_{t-1}
        +
        \frac{\Delta t\, S_{\mathrm{base}}}{E_{\max}}
        \Bigl(
            \eta_c P_{t}^{c} - \frac{P_{t}^{d}}{\eta_d}
        \Bigr) \\
        |P_{t}^{d}-P_{t}^{c}| &\leq P^{\max}
    \end{align}

SOCP model
^^^^^^^^^^

In the sparse SOCP stack the same SoC update is used. On AC buses the rating is
an apparent-power limit; on DC buses it is a net active-power limit:

.. math::
    :label: eq:bess_socp

    \begin{align}
        \mathrm{SoC}_{t}
        &=
        \mathrm{SoC}_{t-1}
        +
        \frac{\Delta t\, S_{\mathrm{base}}}{E_{\max}}
        \Bigl(
            \eta_c P_{t}^{c} - \frac{P_{t}^{d}}{\eta_d}
        \Bigr) \\
        \bigl\|(P_{t}^{d}-P_{t}^{c})+j\,q_{t}^{b}\bigr\|
        &\leq s_{b}^{\max}
          \qquad \text{(AC)} \\
        |P_{t}^{d}-P_{t}^{c}|
        &\leq P^{\max}
          \qquad \text{(DC)}
    \end{align}

Optional **mutually exclusive** charge/discharge (Paper R MI-BESS) is available
via ``bess_mi_exclusivity=True`` on :func:`~pyflow_acdc.socp_optimise` /
:func:`~pyflow_acdc.soc_window_optimisation``. Default is G6 continuous (overlap
allowed). MI mode prefers an MI-capable conic solver (MOSEK, GUROBI, or SCIP)
and warns if a non-MI backend is selected.

* :attr:`~pyflow_acdc.Node_AC.connected_storage` /
  :attr:`~pyflow_acdc.Node_DC.connected_storage` /
  :attr:`~pyflow_acdc.Grid.storage_elements`
* ``analyse_grid`` sets ``grid.ESS`` when storage is present
* Results: ``Results.ext_storage`` / ``Results.storage_window``

Class Reference: :class:`pyflow_acdc.Classes.Storage`

.. autoclass:: pyflow_acdc.Storage
   :no-members:

Add with :func:`~pyflow_acdc.add_storage`.

Example:

.. literalinclude:: ../../pyflow_tests/doc_examples/storage/01_add_storage.py
   :language: python
   :lines: 2-

.. _Electrolyser_modelling:

Green hydrogen / electrolyser
-----------------------------

Hydrogen production is inherently nonlinear (voltage–current density,
temperature, degradation). pyflow-acdc uses the **linear** production model of
[#useche2026]_ Eqs. (32)–(36): inventory :math:`M_t`, production
:math:`h_t`, electrolyser demand :math:`P_{t}^{e}`, slope / intercept
:math:`b_h`, :math:`c_h`:

.. math::
    :label: eq:h2_inventory

    \begin{align}
        M_{t} &= M_{t-1} + h_{t}
            & \qquad \forall t \in \mathcal{T} \\
        h_{t} &= b_{h}\, P_{t}^{e} + c_{h}
            & \qquad \forall t \in \mathcal{T} \\
        M_{t_{i}} &= M^{\mathrm{ini}},\quad
        M_{t_{f}} = M^{\mathrm{fin}} & \\
        0 &\leq M_{t} \leq \overline{M}
            & \qquad \forall t \in \mathcal{T}
    \end{align}

**pyflow-acdc implementation.** Inventory ``mass_H2`` is in **kg**. Active
power ``P_electrolyser`` is a **load** (subtracted from nodal injection).
Production each frame uses ``c_h`` every hour:

.. math::
    :label: eq:h2_pyflow

    h = b_{h}\, P_{e}\, S_{\mathrm{base}}\, \Delta t + c_{h},
    \qquad
    M_{t} = M_{t-1} + h

On **AC**, optional reactive compensation via ``Q_min_MVAR`` / ``Q_max_MVAR``
(generation convention). On **DC**, ``Q`` is fixed at zero.

``empty_tank_cycle`` (``None`` or ``N >= 1``) controls **out-of-opt** tank
resets between solves (not a Pyomo constraint) — see :doc:`../usage_window_opf`
and :func:`~pyflow_acdc.ts_acdc_opf`. Optional ``H2_mass_final`` is enforced in
coupled window / rolling OPF when set. Economics use ``h2_price`` with
``ObjRule['H2_sale']``.

Linear model
^^^^^^^^^^^^

In the linear OPF stack the same inventory update is used with electrolyser
active power only:

.. math::
    :label: eq:h2_l

    h = b_{h}\, P_{e}\, S_{\mathrm{base}}\, \Delta t + c_{h},
    \qquad
    M_{t} = M_{t-1} + h

SOCP model
^^^^^^^^^^

In the sparse SOCP stack the same inventory update is used. On AC buses,
optional reactive compensation is available through ``Q_min_MVAR`` /
``Q_max_MVAR``; on DC buses reactive power is zero.

* :attr:`~pyflow_acdc.Node_AC.connected_electrolyser` /
  :attr:`~pyflow_acdc.Node_DC.connected_electrolyser` /
  :attr:`~pyflow_acdc.Grid.electrolysers`
* ``analyse_grid`` sets ``grid.H2`` when electrolysers are present
* Results: ``Results.ext_electrolyser`` / ``Results.hydrogen_window``

Class Reference: :class:`pyflow_acdc.Classes.Electrolyser`

.. autoclass:: pyflow_acdc.Electrolyser
   :no-members:

Add with :func:`~pyflow_acdc.add_electrolyser`.

Example:

.. literalinclude:: ../../pyflow_tests/doc_examples/hydrogen/01_add_electrolyser.py
   :language: python
   :lines: 2-

.. _Heat_pump_modelling:

Controllable heat pumps
-----------------------

Local energy communities can provide flexibility through heat pumps (HPs)
operated as controllable electrical loads. In the planning-oriented model of
[#montala2026]_, HP active and reactive powers are decomposed into a baseline
(reference) demand and a flexibility activation, subject to converter-style
instantaneous bounds and cumulative energy (comfort) envelopes.

Paper form (controllable load :math:`d \in \mathcal{D}`, reference
:math:`p^{*}_{d,t}`, :math:`q^{*}_{d,t}`, served demand :math:`p_{d,t}`,
:math:`q_{d,t}`, cumulative electrical energy :math:`e_{d,t}` in kWh):

.. math::
    :label: eq:hp_bounds

    \begin{align}
        \underline{p}_{d,t} &\leq p_{d,t} \leq \overline{p}_{d,t}
            & \qquad \forall d \in \mathcal{D} \\
        \underline{q}_{d,t} &\leq q_{d,t} \leq \overline{q}_{d,t}
            & \qquad \forall d \in \mathcal{D} \\
        \frac{\underline{e}_{d,t} - e_{d,t}}{\Delta t}
            &\leq p_{d,t} \leq
            \frac{\overline{e}_{d,t} - e_{d,t}}{\Delta t}
            & \qquad \forall d \in \mathcal{D}
    \end{align}

Energy evolves sequentially as
:math:`e_{d,t+1} = e_{d,t} + p_{d,t}\,\Delta t` (with :math:`e_{d,0} = 0` in
the paper's planning setup). Admissible envelopes
:math:`(\underline{p},\overline{p})`, :math:`(\underline{q},\overline{q})`,
and :math:`(\underline{e},\overline{e})` encode thermal comfort / hot-water
limits derived offline from building simulations; pyflow-acdc does **not**
embed a thermal model.

**pyflow-acdc implementation.** Per-unit baseline demand is stored as
``P_ref`` / ``Q_ref`` in **pu** on ``S_base``; parallel units use ``np_hp``
(same pattern as ``np_gen`` / ``np_rsgen`` on :class:`~pyflow_acdc.Gen_AC` /
:class:`~pyflow_acdc.Ren_Source`). Aggregate served power is

.. math::
    :label: eq:hp_pyflow_served

    P_{\mathrm{hp}} = n_{\mathrm{hp}}\,(P_{\mathrm{ref}} - P_{\mathrm{shed}}), \qquad
    Q_{\mathrm{hp}} = n_{\mathrm{hp}}\,(Q_{\mathrm{ref}} - Q_{\mathrm{shed}})

Per-unit apparent-power rating ``Max_S`` [pu] defaults to ``P_unit_max``;
override with ``add_heat_pump(..., S_rated_MVAR=)``. Fixed per-unit bounds on
served reactive power ``Q_{\mathrm{ref}} - Q_{\mathrm{shed}}`` are set at
creation via ``add_heat_pump(..., Q_min_MVAR=, Q_max_MVAR=)``; when omitted
they default to ``\pm S_{\mathrm{rated}}``. Reactive shedding is bounded
separately by ``\pm Q_{\mathrm{lim}}^{\mathrm{shed}}`` with
``Q_{\mathrm{lim}}^{\mathrm{shed}} = S_{\mathrm{rated}} \cdot q_{\mathrm{shed,lim,frac}}``.
Neither limit has time-series types. Per-unit injection is also limited by
``S_{\mathrm{rated}}`` on
``(P_{\mathrm{ref}} - P_{\mathrm{shed}})^2 + (Q_{\mathrm{ref}} - Q_{\mathrm{shed}})^2 \leq S_{\mathrm{rated}}^2``.

Non-linear model
^^^^^^^^^^^^^^^^

Decision variables: ``P_shed``, ``Q_shed``, ``P_heat_pump``, ``Q_heat_pump``, ``E_heat_pump``.
Per-unit links: ``P_heat_pump = P_ref - P_shed``, ``Q_heat_pump = Q_ref - Q_shed``
(``Q_heat_pump`` bounded by ``Q_min`` / ``Q_max``).
Nodal totals: ``np_hp * P_heat_pump``, ``np_hp * Q_heat_pump``.

Instantaneous bounds (every frame, including window blocks):

.. math::
    :label: eq:hp_pyflow_p_shed

    0 \leq P_{\mathrm{shed}} \leq P_{\mathrm{unit}}^{\max}

.. math::
    :label: eq:hp_pyflow_q_shed

    -Q_{\mathrm{lim}}^{\mathrm{shed}} \leq Q_{\mathrm{shed}} \leq Q_{\mathrm{lim}}^{\mathrm{shed}},
    \qquad
    Q_{\mathrm{lim}}^{\mathrm{shed}} = S_{\mathrm{rated}} \cdot q_{\mathrm{shed,lim,frac}}

.. math::
    :label: eq:hp_pyflow_q_injected

    Q_{\min} \leq Q_{\mathrm{hp}} \leq Q_{\max},
    \qquad
    Q_{\mathrm{hp}} = Q_{\mathrm{ref}} - Q_{\mathrm{shed}}

.. math::
    :label: eq:hp_pyflow_s_rating

    (P_{\mathrm{ref}} - P_{\mathrm{shed}})^{2}
    + Q_{\mathrm{hp}}^{2}
    \leq S_{\mathrm{rated}}^{2}

.. math::
    :label: eq:hp_pyflow_e

    E_{\min} \leq E \leq E_{\max}

Energy balance and :math:`E_{t-1}`-linked active shedding (snapshot / myopic /
in-block only; skipped when ``window_block=True`` — parent window owns the
chain):

.. math::
    :label: eq:hp_energy_pyflow

    E_{t}
    =
    E_{t-1}
    +
    n_{\mathrm{hp}}\, P_{\mathrm{hp}}\, S_{\mathrm{base}}\, \Delta t

.. math::
    :label: eq:hp_p_shed_energy

    \frac{E_{\min}}{ \Delta t} - \frac{E_{t-1}}{ \Delta t}
    \leq
    P_{\mathrm{shed}}
    \leq
    \frac{E_{\max}}{ \Delta t} - \frac{E_{t-1}}{ \Delta t}

``Energy_cost`` penalises shed directly (MW/MVAR via ``S_base``):

.. math::
    :label: eq:hp_energy_cost

    P_{\mathrm{shed}}^{2}\, S_{\mathrm{base}}^{2}\, q_f
    + P_{\mathrm{shed}}\, S_{\mathrm{base}}\, \ell_f
    + Q_{\mathrm{shed}}^{2}\, S_{\mathrm{base}}^{2}\, q_{f,Q}
    + Q_{\mathrm{shed}}\, S_{\mathrm{base}}\, \ell_{f,Q}

Coefficients are set on ``add_heat_pump`` (``quadratic_cost_factor`` /
``linear_cost_factor`` and Q twins; default ``0``). Nodal injection subtracts
``np_hp * P_heat_pump`` / ``np_hp * Q_heat_pump`` from the AC balance (load sign).

Window OPF owns the energy chain across frames
(:func:`~pyflow_acdc.NL_models.window_opf.window_heat_pump_constraints`).

**Power flow.** Unlike BESS / H₂ PF setpoint series (``storage_P``, ``h2_P``,
… via :func:`~pyflow_acdc.update_grid_for_pf`), heat-pump baselines stay on
:func:`~pyflow_acdc.update_grid_data` (``hp_P_ref``, ``hp_Q_ref``,
``hp_E_min``, ``hp_E_max``). In AC power flow,
:meth:`~pyflow_acdc.Grid.update_pq_ac` treats ``P_ref * np_hp`` /
``Q_ref * np_hp`` as known nodal loads (same sign convention as NL OPF).

Linear model
^^^^^^^^^^^^

Same ``P_shed`` / ``E_heat_pump`` chain as the non-linear model. Reactive
power is not part of the linear stack (no ``Q_shed`` / ``Q_heat_pump`` vars,
no Q nodal injection).

.. math::
    :label: eq:hp_l

    \begin{align}
        0 &\leq P_{\mathrm{shed}} \leq n_{\mathrm{hp}}\, P_{\mathrm{unit}}^{\max} \\
        \frac{E_{\min}}{ \Delta t} - \frac{E_{t-1}}{ \Delta t}
        &\leq P_{\mathrm{shed}}
        \leq \frac{E_{\max}}{ \Delta t} - \frac{E_{t-1}}{ \Delta t} \\
        E_{t}
        &=
        E_{t-1}
        +
        P_{\mathrm{hp}}\, S_{\mathrm{base}}\, \Delta t,
        \qquad
        P_{\mathrm{hp}} = n_{\mathrm{hp}}\,(P_{\mathrm{ref}} - P_{\mathrm{shed}})
    \end{align}

Only active ``P_shed`` shed costs enter ``Energy_cost`` in the linear stack
(same ``qf`` / ``lf`` scaling as NL).

SOCP model
^^^^^^^^^^

Same per-unit decision structure as the non-linear model: ``P_shed``,
``Q_shed``, ``P_heat_pump``, ``Q_heat_pump``, ``E_heat_pump`` with links
``P_heat_pump = P_ref - P_shed``, ``Q_heat_pump = Q_ref - Q_shed``,
``Q_shed`` bounded by ``± Q_lim_shed``, ``Q_heat_pump`` by ``Q_min``/``Q_max``,
and per-unit apparent-power limit
``\|P_heat_pump, Q_heat_pump\|_2 \leq Max_S`` (SOCP circle). Nodal injection
uses ``np_hp * P_heat_pump`` and ``np_hp * Q_heat_pump``. Active shed cap is
per-unit ``P_unit_max``. Energy balance uses aggregate electrical input
``np_hp * P_heat_pump * S_base * Δt`` (same as :eq:`eq:hp_energy_pyflow`).

``Energy_cost`` penalises ``P_shed`` / ``Q_shed`` directly (MW/MVAR via
``S_base``; same formula as :eq:`eq:hp_energy_cost`). Time-varying references
and energy envelopes are read from ``grid.Time_series`` (``hp_P_ref``,
``hp_Q_ref``, ``hp_E_min``, ``hp_E_max``) by
:func:`~pyflow_acdc.translate_pyf_socp`.

* :attr:`~pyflow_acdc.Node_AC.connected_heat_pumps` /
  :attr:`~pyflow_acdc.Grid.heat_pumps`
* ``analyse_grid`` sets ``grid.HP`` when heat pumps are present
* Results: ``Results.ext_heat_pump`` / ``Results.heat_pump_window``

Class Reference: :class:`pyflow_acdc.Classes.HeatPump`

.. autoclass:: pyflow_acdc.HeatPump
   :no-members:

Add with :func:`~pyflow_acdc.add_heat_pump`. Snapshot inputs are scalars for
one-step OPF; for multi-hour studies attach time series to the heat-pump name
(``P_ref`` / ``Q_ref`` in pu, energy bounds in kWh):

.. code-block:: python

    import pyflow_acdc as pyf

    hp = pyf.add_heat_pump(
        grid,
        "bus1",
        P_ref_MW=0.08,
        Q_ref_MVAR=-0.02,
        np_hp=2,
        P_unit_max_MW=1.76 / 1000,
        E_min_kWh=-5.0,
        E_max_kWh=5.0,
        E_state_initial_kWh=0.0,
        quadratic_cost_factor=50.0,
        linear_cost_factor=0.0,
    )
    pyf.add_TimeSeries(grid, df_p_ref, associated=hp.name, TS_type="hp_P_ref")
    pyf.add_TimeSeries(grid, df_q_ref, associated=hp.name, TS_type="hp_Q_ref")
    pyf.add_TimeSeries(grid, df_e_min, associated=hp.name, TS_type="hp_E_min")
    pyf.add_TimeSeries(grid, df_e_max, associated=hp.name, TS_type="hp_E_max")

**References**

.. [#useche2026] M. Useche-Arteaga, P. Gebraad, V. Lacerda, M. Cheah-Mane, and O. Gomis-Bellmunt: *Optimizing the operation of energy islands with predictive nonlinear programming -- a case study based on the Princess Elisabeth Energy Island*, Wind Energy Science, 11(2), 349--372, 2026, https://doi.org/10.5194/wes-11-349-2026

.. [#montala2026] M. Montalà-Palau, J. J. Markus, M. Kazemi, M. Cheah-Mañé,
   C. Papadimitriou, and O. Gomis-Bellmunt: *Enhancing Distribution System
   Resilience through Energy Communities*, CIRED 2026 Brussels Workshop,
   Paper 1361, 2026.
