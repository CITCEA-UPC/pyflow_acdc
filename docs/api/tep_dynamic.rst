Multi period Transmission Expansion Planning Module
====================================================

This module is under development 


This module provides functions for multi-period transmission expansion planning
with investment states applied over time.

Functions are found in `pyflow_acdc.ACDC_MultiPeriod_TEP`.

Multi-period Multi-scenario Dynamic TEP
---------------------------------------

.. py:function:: multi_period_MS_TEP(grid, NPV=True, n_years=10, Hy=8760, discount_rate=0.02, clustering_options=None, ObjRule=None, solver='bonmin', obj_scaling=1.0)

   Solves dynamic transmission expansion planning across investment periods
   using clustered time frames/scenarios.

   .. list-table::
      :widths: 20 10 50 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid to analyze
        - Required
      * - ``NPV``
        - bool
        - Include NPV formulation for operational costs
        - True
      * - ``n_years``
        - int
        - Number of years for discounting
        - 10
      * - ``Hy``
        - int
        - Hours per year
        - 8760
      * - ``discount_rate``
        - float
        - Discount rate
        - 0.02
      * - ``clustering_options``
        - dict
        - Time-series clustering configuration
        - None
      * - ``ObjRule``
        - dict
        - OPF objective weights
        - None
      * - ``solver``
        - str
        - Pyomo solver name
        - 'bonmin'
      * - ``obj_scaling``
        - float
        - Objective scaling factor
        - 1.0

   **Returns**

   - Model object
   - Model results
   - Timing information dictionary
   - Solver statistics dictionary
   - Dynamic TEP time-series results

   **Example**

   .. code-block:: python

      import pyflow_acdc as pyf

      grid, res = pyf.NS_MTDC()
      obj = {'Energy_cost': 1}
      model, model_results, timing_info, solver_stats, ts_results = pyf.multi_period_MS_TEP(
          grid,
          ObjRule=obj,
          solver='bonmin'
      )

Export Dynamic Investment Period Plots
--------------------------------------

.. py:function:: export_and_save_inv_period_svgs(grid, Price_Zones=False, folder_name=None)

   Exports one SVG network plot per investment period using the solved dynamic
   investment states.

Run OPF on One Investment Period
--------------------------------

.. py:function:: run_opf_for_investment_period(grid, investment_period, ObjRule=None, solver='ipopt', tee=False, limit_flow_rate=True, obj_scaling=1.0, export_excel=True, export_location='MP_investment_periods', file_name=None, print_table=False, decimals=3, plot_folium={})

   Applies one dynamic investment-period state to the grid, runs OPF, and
   optionally exports period results to Excel and Folium map.

Run OPF on All Investment Periods
---------------------------------

.. py:function:: run_opf_for_all_investment_periods(grid, ObjRule=None, solver='ipopt', tee=False, limit_flow_rate=True, obj_scaling=1.0, export_excel=True, export_location=None, file_name_prefix=None, print_table=False, decimals=3, plot_folium=None)

   Runs OPF for every dynamic investment period and exports one result file per
   period.