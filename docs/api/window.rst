Window Module
=============

Coupled multi-hour nonlinear OPF with shared BESS SoC and (when present) H₂
inventory across frames. Implemented in :mod:`pyflow_acdc.NL_models.window_opf`.

Workflow guide: :doc:`../usage_window_opf`. Element models:
:doc:`modelling_flexible_assets`. Objectives: :ref:`obj_functions`.
Myopic (uncoupled) sequential hours: :func:`~pyflow_acdc.ts_acdc_opf`
(:doc:`ts`).

Requires at least one storage or electrolyser (``grid.ESS`` or ``grid.H2``)
and ``grid.Time_series``.

Coupled window
--------------

.. autofunction:: pyflow_acdc.window_nl_opf

   Inclusive **0-based** ``start`` / ``end`` on the time series.
   Optional terminal pins: ``soc_final``, ``H2_mass_final`` (when set on
   elements). Results: ``grid.window_opf_results``,
   ``Results.storage_window`` / ``Results.hydrogen_window``.

Rolling window
--------------

.. autofunction:: pyflow_acdc.rolling_window_nl_opf

   Inclusive **1-based** ``start`` / ``end`` (same convention as
   :func:`~pyflow_acdc.ts_acdc_opf`). Chains :func:`~pyflow_acdc.window_nl_opf`
   with SoC carry-over; H₂ tank empties follow ``empty_tank_cycle`` between
   commits. Optional ``future_sight`` in ``[0, 1]`` extends each commit solve
   by ``ceil(future_sight · window_size)`` foresight frames (SoC final at the
   foresight end; proportional H₂ mass on the foresight segment). See
   :doc:`../usage_window_opf`.

Linear AC(/DC) window
---------------------

Linear counterparts (:func:`~pyflow_acdc.window_l_opf`,
:func:`~pyflow_acdc.rolling_window_l_opf`) live under :doc:`L_models`
(AC-only and hybrid LP; BESS P-only).
