Time Series Module
==================

This module provides functions for time series analysis of power flows and optimal power flow.

functions are found in pyflow_acdc.Time_series


Sequential AC/DC Time Series Power Flow
---------------------------------------

General time series
^^^^^^^^^^^^^^^^^^^

.. autofunction:: pyflow_acdc.time_series_pf

   Dispatches to the AC-only, DC-only, or AC/DC routine below depending on
   ``grid``.

AC
""""

.. autofunction:: pyflow_acdc.ts_ac_pf

DC
""""

.. autofunction:: pyflow_acdc.ts_dc_pf

AC/DC
"""""

.. autofunction:: pyflow_acdc.ts_acdc_pf

Grid Data Update Helper
^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pyflow_acdc.update_grid_data

   Applies one hourly (or clustered) time-series sample onto the ``Grid`` before
   PF/OPF/TEP routines run. Matching is by ``TimeSeries.element_name`` and
   ``TimeSeries.type``:

   - ``price`` → node and price-zone ``price``
   - ``Load`` → ``PLi_factor`` on nodes and price zones
   - renewable types → ``PRGi_available`` on sources/zones
   - with ``price_zone_restrictions=True`` → ``a_CG``, ``b_CG``, ``c_CG``,
     ``PGL_min``, ``PGL_max`` on price zones

   Set ``use_clusters=True`` and pass ``n_clusters`` when TEP/OPF should read
   from ``ts.data_clustered`` instead of the full hourly ``ts.data``.

Optimal Power Flow Time Series
------------------------------

Nonlinear (myopic)
^^^^^^^^^^^^^^^^^^
.. autofunction:: pyflow_acdc.ts_acdc_opf

   Objective rule (``ObjRule``) — see :ref:`Objective Functions <obj_functions>`.
   ``price_zone_restrictions`` adds price-zone restrictions to the model [1]_.

   With BESS (``grid.ESS``): SoC is carried hour-to-hour; optional soft reference
   via ``ObjRule['SoC_deviation']``.
   With H₂ (``grid.H2``): inventory carries within ``H2_mass_max``;
   ``empty_tank_cycle`` empties between solves; economics via
   ``ObjRule['H2_sale']``.
   Element models: :doc:`modelling_flexible_assets`.
   Coupled multi-hour inventory / terminal mass:
   :doc:`window` (API) and :doc:`../usage_window_opf` (workflow).


   **Example**

.. literalinclude:: ../../pyflow_tests/doc_examples/ts/02_cross_sectional_time_series.py
   :language: python
   :lines: 2-

Linear (myopic)
^^^^^^^^^^^^^^^
.. autofunction:: pyflow_acdc.ts_acdc_l_opf

   Myopic twin of :func:`~pyflow_acdc.ts_acdc_opf` using
   :func:`~pyflow_acdc.optimal_l_pf`'s builder
   (``opf_create_l_model_acdc``). Supports ``Energy_cost`` / ``H2_sale`` only;
   ``SoC_deviation`` is rejected. Carries BESS SoC / H₂ mass and
   ``empty_tank_cycle`` the same way. AC-only and hybrid grids. See
   :doc:`L_models`.



Data handling
-------------

Statistical Analysis
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pyflow_acdc.time_series_statistics

   Calculates for each time series:

   - Mean
   - Median
   - Maximum/Minimum
   - Mode
   - IQR
   - Percentiles

Results Export
^^^^^^^^^^^^^^

.. autofunction:: pyflow_acdc.results_ts_opf

**References**

.. [1] B. C. Valerio, V. A. Lacerda, M. Cheah-Mañe, P. Gebraad, and O. Gomis-Bellmunt,
       "Optimizing offshore wind integration through multi-terminal DC grids: a market-based
       OPF framework for the North Sea interconnectors," IET Conference Proceedings, vol. 2025,
       no. 6, pp. 150–155, 2025. doi: 10.1049/icp.2025.1198

