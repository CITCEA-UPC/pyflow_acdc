Optimal Power Flow Module
=========================

This module provides functions for AC/DC hybrid optimal power flow analysis [1]_.

functions are found in ``pyflow_acdc.ACDC_OPF``, ``pyflow_acdc.pyomo_model_solve``,
and ``pyflow_acdc.NL_models.ACDC_OPF_NL_model``

AC/DC Hybrid Optimal Power Flow
-------------------------------

Running the OPF
^^^^^^^^^^^^^^^^

This function runs the AC/DC hybrid optimal power flow calculation. It creates the :ref:`model <model_creation>`, chooses an :ref:`objective function <obj_functions>`, and :ref:`solves <model_solving>` the model.

For step-by-step examples (grid setup, generators, and calling ``optimal_pf``), see :ref:`Running an Optimal Power Flow <usage_opf>`.

.. autofunction:: pyflow_acdc.optimal_pf

.. autofunction:: pyflow_acdc.multi_scenario_opf

   One OPF per scenario frame, weighted by ``scenario_weights``, solved as one model with every
   installed amount fixed. Use it to score fixed designs (e.g. reactive compensation sizes) over
   operating states. Per-frame values are read from ``model.scenario_model[t]``.

.. _model_creation:

Creating the OPF model
^^^^^^^^^^^^^^^^^^^^^^


.. autofunction:: pyflow_acdc.NL_models.ACDC_OPF_NL_model.opf_create_nl_model_acdc

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
- :ref:`BESS SoC and power limits <Storage_modelling>` (when ``grid.ESS``)
- :ref:`Electrolyser power and H₂ inventory <Electrolyser_modelling>` (when ``grid.H2``)

For more details on the constraints, please refer to the :ref:`System Modelling <modelling>` page.

.. _obj_functions:

Objective Functions
^^^^^^^^^^^^^^^^^^^^

The user can define the objective by setting the weight of each sub objective. The objective function is defined as:

.. autofunction:: pyflow_acdc.opf_obj

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
    * - ``Array_losses``
      - Offshore array injection and slack extraction losses
      - :math:`\left(\sum_{rg \in \mathcal{RG}} P_{rg}\, n_{rg} + \sum_{n \in \mathcal{N}_{slack}} P_{g,opt,n}\right) \cdot \mathrm{LCoE} \cdot S_{base}`

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

  Pass these names exactly as ``ObjRule`` keys (e.g. ``{"PZ_cost_of_generation": 1}``).
 
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
    * - ``SoC_deviation``
      - Soft BESS SoC reference toward ``soc_ref`` (defaults to ``soc_initial``). Useful in myopic :func:`~pyflow_acdc.ts_acdc_opf` so storage is not emptied under pure ``Energy_cost``. Requires ``grid.ESS``. Quadratic — not supported in linear OPF. See :ref:`Storage_modelling`.
      - :math:`\sum_{s} \bigl(\mathrm{SoC}_{s} - soc_{ref,s}\bigr)^{2}`
    * - ``H2_sale``
      - Hydrogen sale revenue (minimise negative revenue ≡ maximise sales). Uses each electrolyser ``h2_price`` (EUR/kg; static or ``H2_PRICE`` series). Requires ``grid.H2``. Supported in NL and linear OPF. See :ref:`Electrolyser_modelling`.
      - :math:`-\sum_{e} price_{H2,e}\,\bigl(b_{h,e}\, P_{e}\, S_{\mathrm{base}}\,\Delta t + c_{h,e}\bigr)`

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

.. autofunction:: pyflow_acdc.pyomo_model_solve

Result Translation Helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pyflow_acdc.opf_line_res

.. autofunction:: pyflow_acdc.opf_price_price_zone

.. autofunction:: pyflow_acdc.translate_pyf_opf


**References**

.. [1] B.C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
       "An optimal power flow tool for AC/DC systems, applied to the analysis of the
       North Sea Grid for offshore wind integration" in IEEE Transactions on Power
       Systems, doi: 10.1109/TPWRS.2023.3533889.

.. [2] B. C. Valerio, V. A. Lacerda, M. Cheah-Mañe, P. Gebraad, and O. Gomis-Bellmunt,
       "Optimizing offshore wind integration through multi-terminal DC grids: a market-based
       OPF framework for the North Sea interconnectors," IET Conference Proceedings, vol. 2025,
       no. 6, pp. 150–155, 2025. doi: 10.1049/icp.2025.1198