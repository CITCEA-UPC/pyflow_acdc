Optimal Power Flow Module
=========================

This module provides functions for AC/DC hybrid optimal power flow analysis [1]_.

functions are found in pyflow_acdc.ACDC_OPF and pyflow_acdc.ACDC_OPF_NL_model

AC/DC Hybrid Optimal Power Flow
-------------------------------

Running the OPF
^^^^^^^^^^^^^^^^

This function runs the AC/DC hybrid optimal power flow calculation. It creates the :ref:`model <model_creation>`, chooses an :ref:`objective function <obj_functions>`, and :ref:`solves <model_solving>` the model.

.. py:function::  Optimal_PF(grid, ObjRule=None, PV_set=False, OnlyGen=True, Price_Zones=False)

   Performs AC/DC hybrid optimal power flow calculation.

   .. list-table::
      :widths: 20 10 50 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid to optimize
        - Required
      * - ``ObjRule``
        - dict
        - Objective function weights
        - None
      * - ``PV_set``
        - bool
        - Sets PV and Slack voltage as fixed variables
        - False
      * - ``OnlyGen``
        - bool
        - Only generators are considered in the cost function
        - True
      * - ``Price_Zones``
        - bool
        - Enable price zone constraints
        - False
  
   **Example**

   .. code-block:: python

      model, model_res , timing_info, solver_stats =pyf.Optimal_PF(grid, ObjRule=None, PV_set=False, OnlyGen=True, Price_Zones=False)

.. _model_creation:

Creating the OPF model
^^^^^^^^^^^^^^^^^^^^^^


.. function:: OPF_create_NLModel_ACDC(model, grid, PV_set, Price_Zones, TEP=False, limit_flow_rate=True)

   Creates the OPF model.

   .. list-table::
      :widths: 20 10 50 
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``model``
        - Model
        - Model to create
      * - ``grid``
        - Grid
        - Grid to optimize    
      * - ``PV_set``
        - bool
        - Sets PV and Slack voltage as fixed variables
      * - ``Price_Zones``
        - bool
        - Enable price zone constraints
      * - ``TEP``
        - bool
        - Enable TEP investment variables (lines/generators)
      * - ``limit_flow_rate``
        - bool
        - Enable flow rate limits

   **Variables**


   The optimization model includes variables for:

   - AC node voltages and angles
   - DC node voltages 
   - Generator active/reactive power
   - Renewable generation and curtailment
   - Line flows
   - Converter power flows
   - Price zone variables

   **Constraints**


   The model enforces constraints for:

   - :ref:`AC power flow equations <AC_node_modelling>`
   - :ref:`DC power flow equations <DC_node_modelling>`
   - :ref:`Generator limits <Generator_modelling>`
   - :ref:`AC branch thermal limits <AC_branch_modelling>`
   - :ref:`DC branch thermal limits <DC_line_modelling>`
   - Voltage and angle limits
   - :ref:`Converter operation limits <ACDC_converter_modelling>`
   - :ref:`Price zone balancing <Price_zone_modelling>`

   For more details on the constraints, please refer to the :ref:`System Modelling <modelling>` page.

   **Example**

   .. code-block:: python

      from pyflow_acdc.ACDC_OPF_NL_model import OPF_create_NLModel_ACDC
      model = OPF_create_NLModel_ACDC(model, grid, PV_set=False, Price_Zones=False)

.. _obj_functions:

Objective Functions
^^^^^^^^^^^^^^^^^^^^

The user can define the objective by setting the weight of each sub objective. The objective function is defined as:

.. function:: OPF_obj(model,grid,ObjRule,OnlyGen,OnlyAC=False)

  This function creates a weighted sum of the different sub objectives.

  .. math::
    \min \frac{\sum_{i \in O} \left( w_i \cdot f_i \right)}{\sum_{i \in O} w_i}

  where :math:`f_i` is the sub objective and :math:`w_i` is the weight.

  The following table shows the pre-built objective functions as defined in [1]_ :


  .. list-table::
    :widths: 20 40 40
    :header-rows: 1

    * - Weight
      - Description
      - Formula
    * - ``Ext_Gen``
      - External generation minimization or maximum export
      - :math:`\sum_{g \in G} \cdot P_{g}`
    * - ``Energy_cost``
      - Energy cost
      - :math:`\sum_{g \in \mathcal{G}_{ac}} \left(P_{g}^2 \cdot \alpha_g + P_{g} \cdot \beta_g  \right)`
    * - ``Curtailment_Red``
      - Renewable curtailment reduction
      - :math:`\sum_{rg \in  \mathcal{RG}_{ac}}\left((1-\gamma_rg)P_{rg}\cdot \rho_{rg} \sigma_{rg}\right)`
    * - ``AC_losses``
      - AC transmission losses
      - :math:`\sum_{j \in \mathcal{B}_{ac}}  \left( P_{j,\text{from}} +P_{j,\text{to}} \right)`
    * - ``DC_losses``
      - DC transmission losses
      - :math:`\sum_{e \in \mathcal{B}_{dc}} \left( P_{e,\text{from}} +P_{e,\text{to}} \right)`
    * - ``Converter_Losses``
      - Converter losses
      - :math:`\sum_{cn \in \mathcal{C}_{n}} \left( P_{loss_{cn}} + |\left(P_{c_{cn}}-P_{s_{cn}}\right)| \right)`
    * - ``General_Losses``
      - Generation minus demand
      - :math:`\left(\sum_{g \in \mathcal{G}} P_{g}+\sum_{rg \in \mathcal{RG}} P_{rg}*\gamma_{rg}- \sum_{l \in \mathcal{L}} P_{L} \right)`

  The following table shows the pre-built objective functions as defined in [2]_:

  .. list-table::
    :widths: 20 40 40
    :header-rows: 1

    * - Weight
      - Description
      - Formula 
    * - ``PZ_cost_of_generation``
      - Price zone generation cost
      - :math:`\sum_{m \in \mathcal{M}} CG(P_N)_m`

  The following table shows the pre-built objective functions in development:

  .. list-table::
    :widths: 20 40 40
    :header-rows: 1

    * - Weight
      - Description
      - Formula
    * - ``Renewable_profit``
      - Renewable generation profit
      - :math:`- \left(\sum_{rg \in \mathcal{RG}} P_{rg}*\gamma_{rg} + \sum_{cn \in \mathcal{C}} \left(P_{loss,cn} + P_{AC,loss,cn}\right)\right)`
    * - ``Gen_set_dev``
      - Generator setpoint deviation
      - :math:`\sum_{g \in G}  \left(P_g -P_{g,set}\right)^2`
      

  **Example**

  .. code-block:: python

      weights_def = {
      'Ext_Gen': {'w': 0},
      'Energy_cost': {'w': 0},
      'Curtailment_Red': {'w': 0},
      'AC_losses': {'w': 0},
      'DC_losses': {'w': 0},
      'Converter_Losses': {'w': 0},
      'PZ_cost_of_generation': {'w': 0},
      'Renewable_profit': {'w': 0},
      'Gen_set_dev': {'w': 0}
      }
      
.. _model_solving:

Solvers
^^^^^^^

The OPF module supports pyomo solvers.

To see the available solvers, use the following command:

.. code-block:: bash

  pyomo help --solvers

Tested with:

- IPOPT
- Bonmin

.. function::  pyomo_model_solve(model,grid,solver = 'ipopt')

   Solves the OPF model using the specified solver.

   :param model: The optimization model
   :param grid: The grid to optimize
   :param solver: The solver to use

   **Example**

   .. code-block:: python

        results, solver_stats =pyf.pyomo_model_solve(model,grid)

Result Translation Helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: OPF_line_res(model, grid)

   Extracts AC/DC line OPF results from a solved model into pandas-friendly structures.

.. py:function:: OPF_price_priceZone(model, grid)

   Extracts price-zone results from a solved OPF model.

.. py:function:: Translate_pyf_OPF(grid, Price_Zones=False)

   Translates solved OPF variables into `grid` result containers for plotting/export.


**References**

.. [1] B.C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
       "An optimal power flow tool for AC/DC systems, applied to the analysis of the
       North Sea Grid for offshore wind integration" in IEEE Transactions on Power
       Systems, doi: 10.1109/TPWRS.2023.3533889.

.. [2] B. C. Valerio, V. A. Lacerda, M. Cheah-Mañe, P. Gebraad, and O. Gomis-Bellmunt,
       "Optimizing offshore wind integration through multi-terminal DC grids: a market-based
       OPF framework for the North Sea interconnectors," IET Conference Proceedings, vol. 2025,
       no. 6, pp. 150–155, 2025. doi: 10.1049/icp.2025.1198