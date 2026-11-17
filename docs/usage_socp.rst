Sparse SOCP
===========

Requires ``pip install pyflow-acdc[SOCP]`` (includes ``cvxpy`` and open-source
``clarabel``). By default, :func:`~pyflow_acdc.socp_optimise` prefers
``MOSEK`` when it is installed, then falls back to ``CLARABEL`` and ``SCS``.

This stack is the CVXPY sparse SOCP path for hybrid AC/DC grids. It mirrors the
public NL OPF surface with:

- :func:`~pyflow_acdc.socp_optimise` for single-period runs
- :func:`~pyflow_acdc.soc_window_optimisation` for explicit multiperiod windows
- :func:`~pyflow_acdc.translate_pyf_socp` for the prepared SOCP input object

Component formulations (Non-linear / Linear / SOCP) live on the system modelling
pages: :doc:`api/modelling_ac`, :doc:`api/modelling_dc`,
:doc:`api/modelling_acdc_converter`, and :doc:`api/modelling_flexible_assets`.
For the runner API, see :doc:`api/socp`.

.. _usage_socp:

Workflow
--------

Start from an analysed or analysable grid, then call the SOCP runner. The
quickest workspace check is ``build_only=True`` to confirm model assembly
without solving.

**Quick example**

.. literalinclude:: ../pyflow_tests/doc_examples/usage/socp_quick.py
   :language: python
   :lines: 1-

After a successful solve, element attributes are updated and
``grid.socp_run`` is set. Call :meth:`~pyflow_acdc.Results.all` for the usual
network / asset tables. Full multiperiod arrays are also stored on
``grid.socp_results``.

Solver notes
------------

- ``solver=None`` prefers ``MOSEK`` if available, then ``CLARABEL``, then
  ``SCS``. Commercial MOSEK is never required for CI or local smoke tests.
- Use ``build_only=True`` when you only want model size / assembly stats.
- Use ``solver_opts`` to pass backend-specific options to CVXPY.

Window runs
-----------

Use :func:`~pyflow_acdc.soc_window_optimisation` when profiles live in
``grid.Time_series`` and you want a coupled ``T``-period network solve. Pass
``frame_ids`` to select a subset; otherwise the full horizon is used.

Related guides
--------------

- :doc:`usage_opf` for the nonlinear Pyomo/IPOPT OPF stack
- :doc:`usage_window_opf` for the nonlinear rolling/coupled window workflows
- :doc:`api/L_models` for the LP linearization path
- :doc:`api/socp` for the SOCP runner API
- :doc:`api/modelling_flexible_assets` for BESS / H₂ / heat-pump formulations
