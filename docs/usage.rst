Usage Guide
===========

This package was designed to facilitate the management of node and branch data in Excel, allowing users to easily convert the data into CSV format for seamless import into Python for calculations. For a detailed guide on this process, I highly recommend referring to :ref:`csv_import`.

Alternatively, you can also construct your grid directly in Python. Below is the fundamental approach to creating a grid.

The Python blocks in **Creating a grid**, **Adding components**, and **Running a power flow** are included from ``pyflow_tests/doc_examples/usage/`` and executed by ``test_docs_usage.py``.

Creating a Grid
---------------
This is the basic way to create a grid. This grid is the same as running MATACDC case5_stagg and case5_stagg_MTDC [1]_.

.. themed-figure:: stagg5
   :alt: Case 5 Stagg
   :align: center

   Case 5 Stagg Grid


.. literalinclude:: ../pyflow_tests/doc_examples/usage/creating_grid.py
   :language: python
   :lines: 2-

Adding Components
-----------------

Grids can also be built in the opposite order, creating the core grid first, then adding elements.

.. literalinclude:: ../pyflow_tests/doc_examples/usage/add_components.py
   :language: python
   :lines: 2-

Running a Power Flow
--------------------
Examples of running a power flow...

.. literalinclude:: ../pyflow_tests/doc_examples/usage/power_flow.py
   :language: python
   :lines: 2-

Available test cases
--------------------

Bundled example grids
^^^^^^^^^^^^^^^^^^^^^

Preloaded grids live under ``pyflow_acdc/example_grids/`` and are registered on
``pyf.cases`` when you ``import pyflow_acdc as pyf``. Each factory returns
``(grid, results)`` — for example ``grid, res = pyf.cases["PEI_grid"]()``.

Factories are grouped by folder: ``PF/``, ``OPF/``, ``TEP/``, ``Wind_Array/``.
Keyword arguments depend on the case. ``NS_MTDC_2025`` accepts ``years_data``
(such as ``"23,24"``), ``expandable="mp"`` or ``"step"``, and ``online=True``
for GitHub raw URLs under ``examples/North_Sea_grid_data/``. For ``NS_MTDC``,
attach the same folder's time-series CSVs with :func:`~pyflow_acdc.add_TimeSeries`
after loading the grid (see :doc:`usage_tep`).

**Power Flow** (``pyflow_acdc/example_grids/PF/``):

* ``pyf.cases['CigreB4_ACDC']()``
* ``pyf.cases['PEI_grid']()``

**Optimal Power Flow** (``pyflow_acdc/example_grids/OPF/``):

* ``pyf.cases['case118']()``
* ``pyf.cases['case1888rte']()``
* ``pyf.cases['case3120sp_acdc']()``
* ``pyf.cases['case_ACTIVSg2000']()``
* ``pyf.cases['NS_MTDC']()`` — North Sea MTDC with an alternate HVDC
  configuration; use with online time-series CSVs from
  ``examples/North_Sea_grid_data/`` (not bundled in the factory)
* ``pyf.cases['NS_SI']()``
* ``pyf.cases['NS_SII']()``
* ``pyf.cases['pglib_opf_case14_ieee']()``
* ``pyf.cases['pglib_opf_case24_ieee_rts']()``
* ``pyf.cases['pglib_opf_case300_ieee']()``
* ``pyf.cases['pglib_opf_case588_sdet_acdc']()``
* ``pyf.cases['pglib_opf_case5_pjm']()``
* ``pyf.cases['pglib_opf_hvdc_case67']()``
* ``pyf.cases['Stagg5MATACDC']()``
* ``pyf.cases['case24_OPF']()`` — IEEE RTS-24 with expandable lines and
  multi-unit generators (distinct from ``pglib_opf_case24_ieee_rts``)
* ``pyf.cases['DC_OPF_simple']()`` — 3-bus DC OPF tutorial grid

**Transmission Expansion Planning** (``pyflow_acdc/example_grids/TEP/``):

* ``pyf.cases['case24_MP']()``
* ``pyf.cases['case24_TEP']()`` — RTS-24 static TEP with expandable AC lines
* ``pyf.cases['case24_REC']()`` — RTS-24 line repurposing (upgrades)
* ``pyf.cases['case6_TEP_DC']()`` — 6-bus AC/DC TEP with expandable DC lines
* ``pyf.cases['case118_TEP']()``
* ``pyf.cases['case118_TEP_DC']()``
* ``pyf.cases['case24_3zones_acdc']()``
* ``pyf.cases['case39']()``
* ``pyf.cases['case39_acdc']()``
* ``pyf.cases['case118_TEP_benchmark']()``
* ``pyf.cases['case_ACTIVSg500']()``
* ``pyf.cases['Texas7k_20210804']()``
* ``pyf.cases['NS_MTDC_2025']()`` — North Sea MTDC for TEP (different HVDC
  layout, bundled TS load, expansion tables); CSVs in
  ``examples/North_Sea_grid_data/`` (``expandable="mp"`` or ``"step"``)

**Wind Array** (``pyflow_acdc/example_grids/Wind_Array/``):

* ``pyf.cases['alpha_ventus']()``
* ``pyf.cases['anholt']()``
* ``pyf.cases['barrow']()``
* ``pyf.cases['Borssele_3_and_4']()``
* ``pyf.cases['moray_east']()``
* ``pyf.cases['nordsee_one']()``
* ``pyf.cases['westermost_rough']()``
* ``pyf.cases['array_sizing_pei'](gamma_limit=0.9)`` — 8-turbine string array
  with cable options for CSS/TEP array-sizing studies

Workflow guides
---------------

.. toctree::
   :maxdepth: 1

   usage_opf
   usage_socp
   usage_tep
   usage_mp_tep
   usage_window_opf
   usage_wf_array

**References**

.. [1] J. Beerten and R. Belmans, "MatACDC - an open source software tool for steady-state analysis and operation of HVDC grids," 11th IET International Conference on AC and DC Power Transmission, Birmingham, 2015, pp. 1-9, doi: 10.1049/cp.2015.0061. keywords: {Steady-state analysis;HVDC grids;AC/DC systems;power flow modelling},
