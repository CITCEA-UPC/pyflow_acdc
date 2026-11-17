Coupled window NL OPF
=====================

Multi-hour nonlinear OPF with **coupled** BESS SoC and (when present) H₂
inventory across frames — unlike myopic :func:`~pyflow_acdc.ts_acdc_opf`,
which solves hour-by-hour.

API reference: :doc:`api/window`. Element models:
:doc:`api/modelling_flexible_assets`. Dash: :doc:`api/dash`.

Requires ``ipopt`` and ``pip install "pyflow-acdc[OPF]"`` (add ``Dash`` for
interactive plots).

Workflow
--------

1. Build or load a grid with time series
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start from a case that already has ``Time_series``, or attach series with
:func:`~pyflow_acdc.add_TimeSeries` (:doc:`api/ts_mod`).

Princess Elisabeth Island (PEI) seasonal data lives under
``examples/PEI_BESS/<Season>/`` (local checkout, else GitHub ``main``)::

    https://raw.githubusercontent.com/CITCEA-UPC/pyflow_acdc/main/examples/PEI_BESS/

Load with case flags ``storage``, ``hydrogen``, and
``data='season_comparison'`` / ``'full'``.

2. Add BESS and/or electrolysers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Attach operation-only storage and hydrogen with
:func:`~pyflow_acdc.add_storage` / :func:`~pyflow_acdc.add_electrolyser`
(or enable them on the PEI case). Modelling details:
:doc:`api/modelling_flexible_assets`.

``window_nl_opf`` requires ``grid.ESS`` or ``grid.H2`` (and time series).

3. Choose an objective
^^^^^^^^^^^^^^^^^^^^^^

Pass ``ObjRule`` keys from :ref:`obj_functions` (e.g. ``Energy_cost``,
``H2_sale``). Soft ``SoC_deviation`` is mainly for myopic TS, not coupled
windows (coupled runs use hard ``soc_initial`` / ``soc_final``).

4. Run a single coupled window
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``start`` / ``end`` are **0-based inclusive** frame indices::

    grid, _ = pyf.cases["PEI_grid"](
        include_countries=["GB", "DK"],
        storage=True,
        hydrogen=True,
        data="season_comparison",
        seasons=("Autumn",),
    )
    pyf.window_nl_opf(
        grid,
        start=0,
        end=23,
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
    )
    pyf.run_dash(grid)

Build-only smoke (no solve):

.. literalinclude:: ../pyflow_tests/doc_examples/storage/02_window_nl_opf_pei.py
   :language: python
   :lines: 2-

5. Or run a rolling horizon
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``start`` / ``end`` are **1-based inclusive** (same as ``ts_acdc_opf``).
SoC carries between commits. H₂ tank empties follow each electrolyser's
``empty_tank_cycle``:

- ``None`` → empty at every commit window boundary
- ``N`` → empty at the first commit end hour ``>= k·N``

Optional ``H2_mass_final`` is enforced on the terminal frame of each
coupled solve when set.

**Foresight** (``future_sight`` in ``[0, 1]``, default ``0``):

- ``0`` — commit-only solves; terminal SoC follows ``soc_final_mode='every_m'``
  / ``soc_final_every_m``.
- ``(0, 1]`` — each commit (except the last) is solved together with
  ``ceil(future_sight · window_size)`` foresight hours into the next commit
  (clamped to remaining series). SoC final is enforced at the foresight end;
  only the commit frames are kept. With a mass target, the commit must produce
  ``≥ H2_mass_final`` and the foresight segment
  ``≥ future_sight · H2_mass_final`` (raw fraction).

::

    pyf.rolling_window_nl_opf(
        grid,
        start=1,
        end=48,
        window_size=24,
        future_sight=0.5,  # half-window foresight; use 1.0 for a full next window
        ObjRule={"Energy_cost": 1},
        solver="ipopt",
    )

6. Season-compare + Dash (PEI)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Solve each season as its own 24 h window, attach compare tables, then open
the season-compare dashboard.

Docs CI only smoke-loads the seasonal CSVs (four IPOPT windows are too heavy).
Interactively prefer ``pyf.run_dash(grid)`` over ``create_season_compare_dash_app``.

.. literalinclude:: ../pyflow_tests/doc_examples/window_opf/01_pei_season_compare_dash.py
   :language: python
   :lines: 9-

Once running, open http://127.0.0.1:8050/ .

.. themed-figure:: pei_season_compare_dash
   :width: 100%
   :alt: PEI BESS H2 season-compare Dash

   Season-compare Dash: Power (source) and SoC across Spring–Winter (split layout).

Related: myopic TS
------------------

Sequential :func:`~pyflow_acdc.ts_acdc_opf` carries SoC / H₂ hour-to-hour
without a coupled horizon. Use ``ObjRule['SoC_deviation']`` /
``ObjRule['H2_sale']`` there — see :doc:`api/ts` and :ref:`obj_functions`.

Linear twin: :func:`~pyflow_acdc.ts_acdc_l_opf` (``Energy_cost`` /
``H2_sale`` only; same SoC / H₂ carry).

Related: linear AC(/DC) window
------------------------------

:func:`~pyflow_acdc.window_l_opf` / :func:`~pyflow_acdc.rolling_window_l_opf`
mirror the coupled / rolling API with the linearised AC(/DC) model (BESS
P-only; hybrid via ``grid.ACmode`` / ``grid.DCmode``). Same ``future_sight``
semantics. LP — not SOCP. See :doc:`api/L_models`.
