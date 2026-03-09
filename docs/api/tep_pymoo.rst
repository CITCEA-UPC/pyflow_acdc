Pymoo Transmission Expansion Planning Module
============================================

This module is preliminar and has not been throughly tested. under development

This module provides a metaheuristic wrapper for Transmission Expansion Planning (TEP)
using `pymoo` genetic algorithms [1]_ over a fixed nonlinear AC/DC OPF model. The OPF is
built once and decision variables (AC/DC line counts, converter counts, repurposing
flags, and array cable types) are updated per candidate to evaluate CAPEX + OPEX or
their Pareto trade-off using a Pyomo-based optimization model [2]_.


Transmission Expansion (pymoo)
-------------------------------

.. function:: transmission_expansion_pymoo(grid, NPV=True, n_years=25, Hy=8760, discount_rate=0.02, ObjRule=None, solver='GA', time_limit=300, tee=False, n_gen=10)

   Runs a pymoo-based outer optimization for TEP. For single-objective, minimizes
   present value of total cost (CAPEX + NPV·OPEX). For multi-objective (``solver='NSGA2'``),
   computes the Pareto front between CAPEX and OPEX and exports the selected solution
   (balanced by default) back to the input ``grid``.

   .. list-table::
      :widths: 22 10 48 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid object with TEP flags (e.g., ``TEP_AC``, ``REC_AC``, ``CT_AC``, ``Array_opf``) and candidates
        - Required
      * - ``NPV``
        - bool
        - When True, CAPEX terms use nominal values; OPEX is multiplied by present value factor
        - True
      * - ``n_years``
        - int
        - Lifetime years for present value factor
        - 25
      * - ``Hy``
        - int
        - Hours per year used in present value computation
        - 8760
      * - ``discount_rate``
        - float
        - Discount rate used for present value
        - 0.02
      * - ``ObjRule``
        - dict|None
        - Objective weighting/selection rule passed to OPF objective builder
        - None
      * - ``solver``
        - str
        - 'GA' for single-objective sum(CAPEX+OPEX·NPV) or 'NSGA2' for Pareto
        - 'GA'
      * - ``time_limit``
        - int
        - Per-OPF solve time limit in seconds
        - 300
      * - ``tee``
        - bool
        - Verbose output from pymoo
        - False
      * - ``n_gen``
        - int
        - Number of generations for the chosen algorithm
        - 10

   **Returns**

   - If ``solver='GA'`` (single objective):
     - ``problem``: internal problem wrapper
     - ``res``: pymoo result with history
     - ``timing_info``: dict with creation, solve, and export times
     - ``solver_stats``: dict with iterations, best objective, time, termination

   - If ``solver='NSGA2'`` (multi-objective Pareto):
     - ``problem``: internal problem wrapper
     - ``pareto_info``: dict with Pareto front, solutions, and selected solutions
     - ``timing_info``: dict with creation and solve times
     - ``solver_stats``: dict with iterations, time, and feasible solutions

   **Side Effects**

   - Exports the chosen solution back into ``grid`` (sets investments and updates
     ``grid.OPF_obj`` and ``grid.TEP_run``).

   **Example**

   .. code-block:: python

      import pyflow_acdc as pyf

      grid,res = pyf.case39_acdc(TEP=True,exp='All',N_b_dc=0,N_b_ac=0,N_i=0,N_max=5,Increase=1.5)

      obj = {'Energy_cost': 1}



      model, model_results , timing_info, solver_stats= pyf.transmission_expansion_pymoo(grid,NPV=True,ObjRule=obj,solver='GA',n_gen=300,tee=True)


   

   **Notes**

   - The OPF model is built once (nonlinear ACDC OPF) and re-evaluated across candidate
     solutions by updating Pyomo Params; this avoids model rebuild overhead.
   - Decision variable bounds mirror the grid's candidate objects and their
     ``*_max`` attributes. Ensure these are set appropriately before running.
   - For Pareto runs (``solver='NSGA2'``), the function returns Pareto information and
     exports the balanced solution by default. Alternative selections can be chosen via
     ``pareto_result`` inside the returned information.

**References**
^^^^^^^^^^^^^^

.. [1] J. Blank and K. Deb, "pymoo: Multi-objective Optimization in Python," IEEE Access.
.. [2] Pyomo Optimization Modeling in Python.