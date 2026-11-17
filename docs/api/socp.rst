Sparse SOCP API
===============

This page documents the CVXPY sparse SOCP stack implemented in
``pyflow_acdc.ACDC_convex`` and ``pyflow_acdc.convex_model.convex_model``.

Reference
---------

Primary paper:

M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Efficient AC/DC energy hubs operation using sparse SOCP
relaxation and chance-constrained optimization*, Sustainable Energy, Grids and
Networks **46**, 102217 (2026).

Use this page to understand the public SOCP model and API. For the package
citation entry, see :doc:`../citing`.

Public runners
--------------

.. autofunction:: pyflow_acdc.socp_optimise

.. autofunction:: pyflow_acdc.soc_window_optimisation

.. autofunction:: pyflow_acdc.socp_ccp_optimise

.. autofunction:: pyflow_acdc.socp_ccp_window_optimisation

Input translation
-----------------

.. autofunction:: pyflow_acdc.translate_pyf_socp

.. autofunction:: pyflow_acdc.apply_ccp_quantiles

Current logic
-------------

- Sparse AC/DC SOCP relaxation with topology-based edge sets only
- AC and DC thermal limits
- Converter coupling with affine loss model
  ``Ploss = a_conv + b_conv · t``, ``t >= |Re(Ss)|``
- Optional BESS continuous charge/discharge and H2 linear inventory
- Shared objective keys with NL OPF where currently supported

The current public SOCP objective support is:

- ``Energy_cost`` — Pyomo-style generator quadratic costs; per-renewable
  ``qf``/``lf`` on availability profiles; heat-pump ``P_shed``/``Q_shed`` shed
  costs when this component is weighted
- ``Ext_Gen``
- ``AC_losses``
- ``DC_losses``
- ``Converter_Losses``
- ``H2_sale``
- ``SoC_deviation``

Unsupported active objective keys raise ``NotImplementedError``.

Model overview
--------------

The sparse SOCP stack is the CVXPY-based convex OPF path for hybrid AC/DC
grids. It supports:

- single-period runs with :func:`~pyflow_acdc.socp_optimise`
- explicit multiperiod runs with :func:`~pyflow_acdc.soc_window_optimisation`
- chance-constrained (CCP) runs with :func:`~pyflow_acdc.socp_ccp_optimise`
  and :func:`~pyflow_acdc.socp_ccp_window_optimisation` (Paper A §4)
- AC/DC network constraints on the existing grid topology
- converter coupling, renewable injections, and optional BESS / H2 operation
- the public objective keys listed above

The detailed component formulations are described on the system modelling pages:

- :doc:`modelling_ac`
- :doc:`modelling_dc`
- :doc:`modelling_acdc_converter`
- :doc:`modelling_flexible_assets`

Model shape
-----------

- ``socp_optimise`` is the single-period entry point (``T = 1``)
- ``soc_window_optimisation`` uses the same builder with ``T = len(frame_ids)``
- Grid profiles come from ``grid.Time_series`` through
  :func:`~pyflow_acdc.translate_pyf_socp`
- Solver path is CVXPY; default preference is ``MOSEK``, then ``CLARABEL``,
  then ``SCS``
