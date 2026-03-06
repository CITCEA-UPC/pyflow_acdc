Wind Farm Array Sizing Module
=============================

This module provides functions for wind farm array sizing based on [1]_.




Sequential Cable Sizing (CSS)
-----------------------------

.. function:: sequential_CSS(grid, NPV=True, n_years=25, Hy=8760, discount_rate=0.02, ObjRule=None, max_turbines_per_string=None, limit_crossings=True, MIP_solver='glpk', CSS_L_solver='gurobi', CSS_NL_solver='bonmin', svg=None, max_iter=None, time_limit=300, NL=False, tee=False, fs=False)

   Iteratively alternates between a path selection MIP and a linear/nonlinear OPF-based cable type selection to converge to an efficient array layout. Returns models, a summary of iterations, timing info, solver stats, and the best iteration index.

   .. list-table::
      :widths: 22 10 48 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid with candidate array lines and cable options
        - Required
      * - ``max_turbines_per_string``
        - int
        - Optional cap on per-string turbines (sets MIP flow bound)
        - None
      * - ``limit_crossings``
        - bool
        - Enforce one-active-per-crossing-group
        - True
      * - ``MIP_solver``
        - str
        - Solver for path MIP (e.g., ``glpk``/``gurobi``)
        - 'glpk'
      * - ``CSS_L_solver``
        - str
        - Solver for linear OPF step
        - 'gurobi'
      * - ``CSS_NL_solver``
        - str
        - Solver for nonlinear OPF step (if ``NL=True``)
        - 'bonmin'
      * - ``time_limit``
        - int
        - Solver time limit in seconds
        - 300
      * - ``NL``
        - bool
        - Use nonlinear OPF instead of linear in CSS
        - False

   **Example**

   .. code-block:: python

      import pyflow_acdc as pyf

      grid,res = pyf.barrow()
      print('grid loaded')
      pyf.sequential_CSS(grid,NPV=True,max_turbines_per_string=None,MIP_solver='gurobi',CSS_L_solver='gurobi',max_iter=None,time_limit=300,tee=True)
          

      res.All()


MIP Path Selection (Array)
--------------------------

.. function:: MIP_path_graph(grid, max_flow=None, solver_name='glpk', crossings=False, tee=False, callback=False)

   Solves a master MIP to select array connection paths minimizing total cable length, with optional crossing constraints and Gurobi callback to record feasible solutions over time. Activates cable types on candidate lines upon success.

   .. list-table::
      :widths: 22 10 48 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid with candidate array lines
        - Required
      * - ``max_flow``
        - int
        - Per-line absolute flow bound (≈ turbines per string)
        - ``|nodes|-1``
      * - ``solver_name``
        - str
        - 'glpk' or 'gurobi' (callback supported with Gurobi)
        - 'glpk'
      * - ``crossings``
        - bool
        - Enforce one-active-per-crossing-group
        - False
      * - ``callback``
        - bool
        - Enable Gurobi MIPSOL callback to track (time, objective)
        - False

   **Returns**

   - ``flag`` (bool): feasible solution found
   - ``high_flow`` (int|None): maximum absolute line flow
   - ``model``: Pyomo model
   - ``feasible_solutions``: list of ``(time, objective)`` pairs (if callback)

   **Example**

   .. code-block:: python

      import pyflow_acdc as pyf

      grid,res = pyf.anholt()
      
      flag, high_flow,model_MIP,feasible_solutions_MIP = pyf.MIP_path_graph(grid, max_flow=10, 
                                                                            solver_name='gurobi', 
                                                                            crossings=True, tee=True,callback=True)
      pyf.ACDC_TEP.plot_feasible_solutions(
                      feasible_solutions_MIP,
                      'MIP',
                      show=True)

Simplified CSS Workflow
-----------------------

.. py:function:: simple_CSS(grid, NPV=True, n_years=25, Hy=8760, discount_rate=0.02, ObjRule=None, CSS_L_solver='gurobi', CSS_NL_solver='bonmin', time_limit=1200, NL=False, tee=False, export=True, fs=False)

   Runs a simplified sequential cable sizing workflow with reduced setup.

.. py:function:: simple_assign_cable_types(grid, model, t_MW=None)

   Assigns cable types from an optimized model back into the grid.

Linear CSS Solvers
------------------

.. py:function:: Optimal_L_CSS_gurobi(grid, OPEX=True, NPV=True, n_years=25, Hy=8760, discount_rate=0.02, tee=False, time_limit=300)

   Solves the linear CSS formulation with Gurobi.

.. py:function:: Optimal_L_CSS_ortools(grid, OPEX=True, NPV=True, n_years=25, Hy=8760, discount_rate=0.02, tee=False, time_limit=300)

   Solves the linear CSS formulation with OR-Tools.

**References**
^^^^^^^^^^^^^^

.. [1] B.C. Valerio, P. Gebraad, M. Cheah-Mane, V. A. Lacerda and O. Gomis-Bellmunt,
       "Strategies for wind park inter array optimisation through Mixed Integer Linear Programming"