Results
=======

The Results class provides methods for analyzing and displaying power flow,
optimization, TEP, multi-period, clustering, and Pyomo solve summaries. Results
are printed in the terminal with the use of prettytable.

Construct a :class:`~pyflow_acdc.Results` instance with the solved grid, then
call a printer on that instance — for example::

   import pyflow_acdc as pyf

   grid, _ = pyf.cases["PEI_grid"]()
   pyf.power_flow(grid)
   res = pyf.Results(grid)
   res.all()

Bundled case factories often return ``(grid, res)`` with ``res`` already bound
to the grid. Use :meth:`~pyflow_acdc.Results.options` on ``res`` to list methods
available for the current grid state.

Class Reference
---------------

.. autoclass:: pyflow_acdc.Results
   :no-members:

Class Methods
-------------

Options
^^^^^^^


.. automethod:: pyflow_acdc.Results.options

   Prints a list of all available results methods.

All
^^^

.. automethod:: pyflow_acdc.Results.all

   On a :class:`~pyflow_acdc.Results` instance (``res = pyf.Results(grid)``),
   prints every section that applies to ``res.Grid``. Includes:

   - :ref:`AC power flow <res_ac_powerflow>`
   - :ref:`AC voltages <res_ac_voltage>`
   - :ref:`AC line currents and power flows <res_ac_lines_current>`
   - :ref:`DC bus data <res_dc_bus>`
   - :ref:`DC line currents and power flows <res_dc_lines_current>`
   - :ref:`Converter data <res_converter>`
   - :ref:`Slack bus information <res_slack_all>`
   - :ref:`Power losses <res_power_loss>`

   When ``res.Grid._last_pyomo_model_results_table`` is set (after a Pyomo solve),
   ``res.all()`` prints the :ref:`Pyomo solve summary <res_pyomo_model_results>`
   block first.

   When ``res.Grid.Clustering_information`` is non-empty:

   - :ref:`Clustering summary <res_clustering_results>`

   When optimization has run (``res.Grid.OPF_run`` or ``res.Grid.socp_run``):

   - :ref:`External generator data <res_ext_gen>`
   - :ref:`Renewable energy sources <res_ext_ren>`
   - :ref:`Objective function <res_objective>` (skipped during TEP / MP TEP)
   - :ref:`Price zone optimization <res_price_zone>`

   When expandable AC lines are present:

   - :ref:`AC expansion line flows <res_ac_exp_lines_power>`

   When DC/DC converters exist:

   - :ref:`DC converter summary <res_dc_converter>`

   When static TEP has run (``res.Grid.TEP_run``):

   - :ref:`Transmission expansion <res_TEP_N>`
   - :ref:`Normalized transmission expansion <res_TEP_norm>` (single-state TEP), or
     :ref:`Multi-scenario TEP tables <res_tep_multi_scenario_res>` and
     :ref:`NPV-normalized MS objective <res_tep_ts_norm>` when
     ``res.Grid.TEP_multiScenario_res`` is set

   When multi-period TEP has run (``res.Grid.MP_TEP_run``):

   - :ref:`MP expansion tables <res_mp_tep_results>`
   - :ref:`MP objective by period <res_mp_tep_obj_res>`
   - :ref:`MP fuel-type mix <res_mp_tep_fuel_type_distribution>`

   When MP+MS TEP has run (``res.Grid.MP_MS_TEP_run``):

   - :ref:`MP+MS expansion tables <res_mp_ms_tep_results>`
   - :ref:`MP+MS objectives <res_mp_ms_tep_obj_res>` (plus the MP tables above)

   When sequential STEP has run (``res.Grid.Seq_STEP_run``):

   - :ref:`Sequential STEP results <res_seq_step_results>`
   - :ref:`Sequential STEP objectives <res_seq_step_obj_res>`
   - :ref:`Sequential STEP fuel-type mix <res_seq_step_fuel_type_distribution>`

   When sequential MS STEP has run (``res.Grid.Seq_MS_STEP_run``):

   - :ref:`Sequential MS STEP results <res_seq_ms_step_results>`
   - :ref:`Sequential MS STEP objectives <res_seq_ms_step_obj_res>`
   - :ref:`Sequential MS STEP fuel-type mix <res_seq_ms_step_fuel_type_distribution>`

   For other clustering detail tables (:ref:`representatives <res_cluster_representatives>`,
   :ref:`technique <res_clustering_technique>`,
   :ref:`time-series statistics <res_clustering_time_series_statistics>`) or
   sequential Pyomo summaries (:meth:`~pyflow_acdc.Results.pyomo_model_results_sequential`),
   call the method on ``res`` directly or use :meth:`~pyflow_acdc.Results.options`.

.. automethod:: pyflow_acdc.Results.all_ac

   Displays results for AC grid only:
   
   - :ref:`AC power flow <res_ac_powerflow>`
   - :ref:`AC voltages <res_ac_voltage>`
   - :ref:`AC line currents and power flows <res_ac_lines_current>`
   - :ref:`AC slack bus info <res_ac_slack>`
   - :ref:`AC power losses <res_ac_power_loss>`

.. automethod:: pyflow_acdc.Results.all_dc

   Displays results for DC grid only:
   
   - :ref:`DC bus data <res_dc_bus>`
   - :ref:`DC line currents and power flows <res_dc_lines_current>`
   - :ref:`DC slack bus info <res_dc_slack>`
   - :ref:`DC power losses <res_dc_power_loss>`

.. _res_slack_all:
.. automethod:: pyflow_acdc.Results.slack_all

   Displays slack bus information for both AC and DC grids.


AC Specific Results
^^^^^^^^^^^^^^^^^^^	
By running the following code, the results will be printed in the terminal. 

.. literalinclude:: ../../pyflow_tests/doc_examples/results/01_ac_specific_results.py
   :language: python
   :lines: 2-



.. _res_ac_powerflow:

.. automethod:: pyflow_acdc.Results.ac_powerflow

   Displays AC power flow, split into differnet asynchronous grids. Results include:
   
   - Power generation
   - Reactive power generation  
   - Power load
   - Reactive power load
   - Real power by converter (if hybrid grid)
   - Reactive power by converter (if hybrid grid)
   - Power injected
   - Reactive power injected

   Example output::
   
      Results AC power

      Grid AC 1
      +------+----------------+---------------------+-----------------+----------------------+-------------------------+-------------------------------+----------------------+---------------------------+
      | Node | Power Gen (MW) | Reactive Gen (MVAR) | Power Load (MW) | Reactive Load (MVAR) | Power converters DC(MW) | Reactive converters DC (MVAR) | Power injected  (MW) | Reactive injected  (MVAR) |
      +------+----------------+---------------------+-----------------+----------------------+-------------------------+-------------------------------+----------------------+---------------------------+
      |  1   |    133.619     |        84.328       |       0.0       |         0.0          |           0.0           |               0               |       133.619        |           84.328          |
      |  2   |      40.0      |       -32.844       |       20.0      |         10.0         |          -60.0          |             -40.0             |        -40.0         |          -82.844          |
      |  3   |      0.0       |         -0.0        |       45.0      |         15.0         |          20.774         |             7.131             |       -24.226        |           -7.869          |
      |  4   |      0.0       |          0          |       40.0      |         5.0          |           0.0           |               0               |        -40.0         |            -5.0           |
      |  5   |      0.0       |          0          |       60.0      |         10.0         |           35.0          |              5.0              |        -25.0         |            -5.0           |
      +------+----------------+---------------------+-----------------+----------------------+-------------------------+-------------------------------+----------------------+---------------------------+
      

.. _res_ac_voltage:
.. automethod:: pyflow_acdc.Results.ac_voltage

   Displays AC voltage results including:
   
   - Voltage magnitude
   - Voltage angle

   Example output::

      Results AC bus voltage

      Grid AC 1
      +-----+--------------+---------------------+
      | Bus | Voltage (pu) | Voltage angle (deg) |
      +-----+--------------+---------------------+
      |  1  |     1.06     |         0.0         |
      |  2  |     1.0      |        -2.383       |
      |  3  |     1.0      |        -3.895       |
      |  4  |    0.996     |        -4.261       |
      |  5  |    0.991     |        -4.149       |
      +-----+--------------+---------------------+


.. _res_ac_lines_current:
.. automethod:: pyflow_acdc.Results.ac_lines_current

   Displays AC line current results including:
   
   - Current magnitude
   - Line loading percentage
   - Line capacity
   - Line polarity

   Example output::

      Results AC Lines Currents
      Grid AC 1
      +------+----------+--------+-------------+-----------+-----------+----------------+
      | Line | From bus | To bus | I from (kA) | I to (kA) | Loading % | Capacity [MVA] |
      +------+----------+--------+-------------+-----------+-----------+----------------+
      |  1   |    1     |   2    |    0.192    |   0.198   |   81.019  |      150       |
      |  2   |    1     |   3    |    0.059    |   0.063   |   37.561  |      100       |
      |  3   |    2     |   3    |    0.024    |   0.022   |   14.637  |      100       |
      |  4   |    2     |   4    |     0.03    |   0.029   |   17.841  |      100       |
      |  5   |    2     |   5    |    0.042    |   0.042   |   25.395  |      100       |
      |  6   |    3     |   4    |    0.039    |    0.04   |   23.932  |      100       |
      |  7   |    4     |   5    |     0.0     |   0.008   |   4.648   |      100       |
      +------+----------+--------+-------------+-----------+-----------+----------------+

.. _res_ac_lines_power:
.. automethod:: pyflow_acdc.Results.ac_lines_power

   Displays AC line power flow results including:
   
   - Power flow from sending end
   - Power flow to receiving end  
   - Power losses

   Example output::

      Results AC Lines power
      Grid AC 1
      +------+----------+--------+-------------+---------------+-----------+-----------+-----------------+---------------+
      | Line | From bus | To bus | P from (MW) | Q from (MVAR) | P to (MW) | Q to (MW) | Power loss (MW) | Q loss (MVAR) |
      +------+----------+--------+-------------+---------------+-----------+-----------+-----------------+---------------+
      |  1   |    1     |   2    |    98.365   |     71.369    |  -95.648  |   -69.59  |      2.717      |     1.779     |
      |  2   |    1     |   3    |    35.254   |     12.96     |  -34.192  |  -15.083  |      1.062      |     -2.123    |
      |  3   |    2     |   3    |    13.248   |     -6.223    |  -13.132  |   2.571   |      0.116      |     -3.652    |
      |  4   |    2     |   4    |    17.072   |     -5.181    |  -16.891  |    1.74   |      0.181      |     -3.441    |
      |  5   |    2     |   5    |    25.328   |     -1.85     |  -25.071  |   -0.352  |      0.257      |     -2.202    |
      |  6   |    3     |   4    |    23.098   |     4.643     |  -23.042  |   -6.465  |      0.057      |     -1.822    |
      |  7   |    4     |   5    |    -0.067   |     -0.275    |   0.071   |   -4.648  |      0.004      |     -4.922    |
      +------+----------+--------+-------------+---------------+-----------+-----------+-----------------+---------------+

.. _res_ac_slack:
.. automethod:: pyflow_acdc.Results.slack_ac

   Displays slack bus information for AC grid.

   Example output::

      Slack nodes
      +-----------+------------+
      |    Grid   | Slack node |
      +-----------+------------+
      | AC Grid 1 |     1      |
      +-----------+------------+


.. _res_ac_power_loss:
.. automethod:: pyflow_acdc.Results.power_loss_ac

   Displays power loss information for AC grid.   

   Example output::

      Power loss AC
      +------------+-----------------+
      |    Grid    | Power Loss (MW) |
      +------------+-----------------+
      | AC Grid 1  |      4.393      |
      | Total loss |      4.393      |
      +------------+-----------------+


DC Specific Results
^^^^^^^^^^^^^^^^^^^

.. _res_dc_bus:

.. automethod:: pyflow_acdc.Results.dc_bus

   Displays DC bus results including:
   
   - Power generation
   - Power load
   - Converter power
   - Power injection
   - Voltage   

   Example output::

      Results DC

      Grid DC 1
      +------+----------------+-----------------+---------------------------+---------------------+--------------+
      | Node | Power Gen (MW) | Power Load (MW) | Power Converter ACDC (MW) | Power injected (MW) | Voltage (pu) |
      +------+----------------+-----------------+---------------------------+---------------------+--------------+
      |  1   |       0        |        0        |           58.652          |        58.652       |    1.008     |
      |  2   |       0        |        0        |           -21.92          |        -21.92       |     1.0      |
      |  3   |       0        |        0        |          -36.191          |       -36.191       |    0.998     |
      +------+----------------+-----------------+---------------------------+---------------------+--------------+

.. _res_dc_lines_current:
.. automethod:: pyflow_acdc.Results.dc_lines_current

   Displays DC line current results including:
   
   - Current magnitude
   - Line loading percentage
   - Line capacity
   - Line polarity

   Example output::

      Results DC Lines current
      Grid DC 1
      +------+----------+--------+--------+-----------+---------------+------------------------------------+
      | Line | From bus | To bus | I (kA) | Loading % | Capacity [kA] | Polarity                           |
      +------+----------+--------+--------+-----------+---------------+------------------------------------+
      |  1   |    1     |   2    | 0.044  |   30.681  |     0.145     | Monopolar (symmetrically grounded) |
      |  2   |    2     |   3    | 0.012  |   8.519   |     0.145     | Monopolar (symmetrically grounded) |
      |  3   |    1     |   3    |  0.04  |   27.971  |     0.145     | Monopolar (symmetrically grounded) |
      +------+----------+--------+--------+-----------+---------------+------------------------------------+


.. _res_dc_lines_power:
.. automethod:: pyflow_acdc.Results.dc_lines_power

   Displays DC line power flow results including:
   
   - Power flow from sending end
   - Power flow to receiving end  
   - Power losses

   Example output::

      Results DC Lines power
      Grid DC 1
      +------+----------+--------+-------------+-----------+-----------------+---------------+
      | Line | From bus | To bus | P from (MW) | P to (MW) | Power loss (MW) | Capacity [MW] |
      +------+----------+--------+-------------+-----------+-----------------+---------------+
      |  1   |    1     |   2    |    30.681   |   -30.44  |      0.241      |      100      |
      |  2   |    2     |   3    |    8.519    |    -8.5   |      0.019      |      100      |
      |  3   |    1     |   3    |    27.971   |   -27.69  |      0.281      |      100      |
      +------+----------+--------+-------------+-----------+-----------------+---------------+


.. _res_dc_slack:
.. automethod:: pyflow_acdc.Results.slack_dc

   Displays slack bus information for DC grid.

   Example output::

      Slack nodes
      +-----------+------------+
      |    Grid   | Slack node |
      +-----------+------------+
      | AC Grid 1 |     1      |
      | DC Grid 1 |     2      |
      +-----------+------------+


.. _res_dc_power_loss:
.. automethod:: pyflow_acdc.Results.power_loss_dc

   Displays power loss information for DC grid.

   Example output::

      Power loss DC
      +------------+-----------------+
      |    Grid    | Power Loss (MW) |
      +------------+-----------------+
      | DC Grid 1  |      0.541      |
      | Total loss |      0.541      |
      +------------+-----------------+

Optimization Results
^^^^^^^^^^^^^^^^^^^^^


.. _res_ext_gen:
.. automethod:: pyflow_acdc.Results.ext_gen

   Displays external generator results including:
   
   - Generator
   - Power (MW)
   - Price (€/MWh)
   - Loading (%)
   - Cost (€)

   Example output::

      External Generation optimization
      +-----------+------+------------+-----------------------+-------------------------+--------------------+-----------+---------+
      | Generator | Node | Power (MW) | Reactive power (MVAR) | Quadratic Price €/MWh^2 | Linear Price €/MWh | Loading % | Cost k€ |
      +-----------+------+------------+-----------------------+-------------------------+--------------------+-----------+---------+
      |     1     | 30.0 |  673.041   |         140.0         |           0.01          |        0.3         |   61.695  |   5.0   |
      |     2     | 31.0 |   646.0    |         300.0         |           0.01          |        0.3         |   100.0   |   4.0   |
      |     3     | 32.0 |  672.666   |        285.674        |           0.01          |        0.3         |   93.143  |   5.0   |
      +-----------+------+------------+-----------------------+-------------------------+--------------------+-----------+---------+

.. _res_ext_ren:
.. automethod:: pyflow_acdc.Results.ext_ren

   Displays renewable sources results including:
   
   - Base power (MW)
   - Curtailment (%)
   - Power injected (MW)
   - Reactive power injected (MVAR)

   Example output::

      Renewable energy sources
      +-------+-----------------+---------------+---------------------+--------------------------------+-------------+---------+-----------------------+
      |  Bus  | Base Power (MW) | Curtailment % | Power Injected (MW) | Reactive Power Injected (MVAR) | Price €/MWh | Cost k€ | Curtailment Cost [k€] |
      +-------+-----------------+---------------+---------------------+--------------------------------+-------------+---------+-----------------------+
      |   T1  |       9.5       |     0.152     |        9.486        |             -0.524             |      0      |    0    |           0           |
      |   T2  |       9.5       |     0.154     |        9.485        |             -0.527             |      0      |    0    |           0           |
      |   T3  |       9.5       |     0.156     |        9.485        |             -0.53              |      0      |    0    |           0           |
      |   T4  |       9.5       |     0.159     |        9.485        |             -0.535             |      0      |    0    |           0           |
      |   T5  |       9.5       |     1.095     |        9.396        |             1.402              |      0      |    0    |           0           |
      |   T6  |       9.5       |     1.091     |        9.396        |              1.4               |      0      |    0    |           0           |
      |   T7  |       9.5       |     1.088     |        9.397        |             1.398              |      0      |    0    |           0           |
      |   T8  |       9.5       |     1.085     |        9.397        |             1.396              |      0      |    0    |           0           |
      | Total |       76.0      |     0.623     |        75.527       |                                |             |    0    |           0           |
      +-------+-----------------+---------------+---------------------+--------------------------------+-------------+---------+-----------------------+

.. _res_objective:
.. automethod:: pyflow_acdc.Results.obj_res

   Displays function value for all optimization functions.

   Example output::
      
      Objective function value
      +-----------------------+--------+------------------+------------------+
      |       Objective       | Weight |      Value       |  Weighted Value  |
      +-----------------------+--------+------------------+------------------+
      |        Ext_Gen        |  0.00  |    15 143.85     |       0.00       |
      |      Energy_cost      |  0.00  |    172 036.78    |       0.00       |
      |    Curtailment_Red    |  0.00  |     5 851.94     |       0.00       |
      |       AC_losses       |  0.00  |      47.55       |       0.00       |
      |       DC_losses       |  0.00  |      49.34       |       0.00       |
      |    Converter_Losses   |  0.00  |      156.38      |       0.00       |
      |     General_Losses    |  0.00  |      253.27      |       0.00       |
      | PZ_cost_of_generation |  1.00  | 2 266 461 478.61 | 2 266 461 478.61 |
      |    Renewable_profit   |  0.00  |       0.00       |       0.00       |
      |      Gen_set_dev      |  0.00  |     2 089.86     |       0.00       |
      +-----------------------+--------+------------------+------------------+

Price Zone optimization
^^^^^^^^^^^^^^^^^^^^^^^^

.. _res_price_zone:
.. automethod:: pyflow_acdc.Results.price_zone

   Displays price zone results

   Example output::

      Price_Zone
      +------------+--------------------------+-----------------+-----------+-------------+-------------+---------------+
      | Price_Zone | Renewable Generation(MW) | Generation (MW) | Load (MW) | Import (MW) | Export (MW) | Price (€/MWh) |
      +------------+--------------------------+-----------------+-----------+-------------+-------------+---------------+
      |     BE     |            0             |     2430.355    |  3028.613 |   598.258   |      0      |     18.45     |
      |     DE     |            0             |     7182.182    |  8215.099 |   1032.917  |      0      |      0.0      |
      |     DK     |            0             |     183.954     |  840.161  |   656.207   |      0      |      3.93     |
      |     GB     |            0             |     3880.814    |  5992.166 |   2111.353  |      0      |      24.8     |
      |     NL     |            0             |     1139.034    |  2380.084 |   1241.049  |      0      |     24.71     |
      |     NO     |            0             |     327.514     |  812.459  |   484.945   |      0      |      6.36     |
      |    MTDC    |            0             |        0        |     0     |      0      |      0      |       1       |
      |    o_BE    |          31.268          |       0.0       |    0.0    |      0      |    31.268   |     18.45     |
      |    o_DE    |         2050.71          |       0.0       |    0.0    |      0      |   2050.71   |      0.0      |
      |    o_DK    |         3082.808         |       0.0       |    0.0    |      0      |   3082.808  |      3.93     |
      |    o_NL    |         775.306          |       0.0       |    0.0    |      0      |   775.306   |     24.71     |
      |    o_NO    |         498.419          |       0.0       |    0.0    |      0      |   498.419   |      6.36     |
      +------------+--------------------------+-----------------+-----------+-------------+-------------+---------------+
      +------------+------------------+-------------------------+-----------------------+----------------------+-----------------+
      | Price_Zone | Social Cost [k€] | Renewable Gen Cost [k€] | Curtailment Cost [k€] | Generation Cost [k€] | Total Cost [k€] |
      +------------+------------------+-------------------------+-----------------------+----------------------+-----------------+
      |     BE     |     -38.712      |           0.0           |           0           |        44.845        |      6.133      |
      |     DE     |     -88.381      |           0.0           |           0           |         0.0          |     -88.381     |
      |     DK     |      -6.845      |           0.0           |           0           |        0.723         |      -6.123     |
      |     GB     |     -94.419      |           0.0           |           0           |        96.239        |      1.819      |
      |     NL     |     -99.751      |           0.0           |           0           |        28.148        |     -71.602     |
      |     NO     |      -3.909      |           0.0           |           0           |        2.082         |      -1.826     |
      |    MTDC    |       0.0        |           0.0           |           0           |         0.0          |       0.0       |
      |    o_BE    |       0.0        |          0.577          |           0           |         0.0          |      0.577      |
      |    o_DE    |       0.0        |           0.0           |           0           |         0.0          |       0.0       |
      |    o_DK    |       0.0        |          12.109         |           0           |         0.0          |      12.109     |
      |    o_NL    |       0.0        |          19.16          |           0           |         0.0          |      19.16      |
      |    o_NO    |       0.0        |          3.169          |           0           |         0.0          |      3.169      |
      |   Total    |     -332.017     |          35.015         |           0           |       172.037        |     -124.966    |
      +------------+------------------+-------------------------+-----------------------+----------------------+-----------------+

Treansmission expansion
^^^^^^^^^^^^^^^^^^^^^^^^

.. _res_TEP_N:
.. automethod:: pyflow_acdc.Results.tep_n

   Displays transmission expansion results 
   
   Example output::

      Transmission Expansion Problem
      +---------+---------+---------+-------------+---------+-----------------------------+--------------------+
      | Element |   Type  | Initial | Optimized N | Maximum | Optimized Power Rating [MW] | Expansion Cost [€] |
      +---------+---------+---------+-------------+---------+-----------------------------+--------------------+
      |   2-6   | AC Line |    0    |     1.0     |    5    |             120             |       30.00        |
      |   3-5   | AC Line |    1    |     3.0     |    5    |             360             |       40.00        |
      |   4-6   | AC Line |    0    |     2.0     |    5    |             240             |       60.00        |
      |  Total  |         |         |             |         |                             |       130.00       |
      +---------+---------+---------+-------------+---------+-----------------------------+--------------------+

.. _res_TEP_norm:
.. automethod:: pyflow_acdc.Results.tep_norm

   Displays NPV objective function value for transmission expansion results

   Example output::

      +-----------------------+--------+--------+----------------+----------------+
      |       Objective       | Weight | Value  | Weighted Value |      NPV       |
      +-----------------------+--------+--------+----------------+----------------+
      |        Ext_Gen        |  0.00  | 774.55 |      0.00      | 132 468 266.42 |
      |      Energy_cost      |  0.00  |  0.00  |      0.00      |      0.00      |
      |    Curtailment_Red    |  0.00  |  0.00  |      0.00      |      0.00      |
      |       AC_losses       |  0.00  | 14.55  |      0.00      |  2 488 902.61  |
      |       DC_losses       |  0.00  |  0.00  |      0.00      |      0.00      |
      |    Converter_Losses   |  0.00  |  0.00  |      0.00      |      0.00      |
      |     General_Losses    |  0.00  | 14.55  |      0.00      |  2 488 902.61  |
      | PZ_cost_of_generation |  0.00  |  0.00  |      0.00      |      0.00      |
      |    Renewable_profit   |  0.00  |  0.00  |      0.00      |      0.00      |
      |      Gen_set_dev      |  0.00  |  3.36  |      0.00      |   575 038.66   |
      +-----------------------+--------+--------+----------------+----------------+



Pyomo solve summary
^^^^^^^^^^^^^^^^^^^

.. _res_pyomo_model_results:

.. automethod:: pyflow_acdc.Results.pyomo_model_results

   Solver status, timing, and objective breakdown after a single Pyomo solve
   (for example MP TEP or static TEP). Call as ``res.pyomo_model_results(...)``
   after ``res = pyf.Results(grid)``. ``res.all()`` prints the same table when
   ``res.Grid._last_pyomo_model_results_table`` is populated.

.. _res_pyomo_model_results_sequential:

.. automethod:: pyflow_acdc.Results.pyomo_model_results_sequential

   Per-period Pyomo summaries from :func:`~pyflow_acdc.sequential_STEP` or
   :func:`~pyflow_acdc.sequential_MS_STEP` ``run_results``.

Multi-scenario TEP results
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _res_tep_multi_scenario_res:

.. automethod:: pyflow_acdc.Results.tep_multi_scenario_res

   Per-scenario price-zone power, social cost, curtailment, line loading, and
   converter loading from ``grid.TEP_multiScenario_res``.

.. _res_tep_ts_norm:

.. automethod:: pyflow_acdc.Results.tep_ts_norm

   NPV-normalized objective components for multi-scenario TEP.

Multi-period TEP results
^^^^^^^^^^^^^^^^^^^^^^^^

.. _res_mp_tep_results:

.. automethod:: pyflow_acdc.Results.mp_tep_results

   Installed, decommissioned, active, and cost tables from ``grid.MP_TEP_results``.

.. _res_mp_tep_obj_res:

.. automethod:: pyflow_acdc.Results.mp_tep_obj_res

   Discounted operational objective by investment period (MP TEP).

.. _res_mp_tep_fuel_type_distribution:

.. automethod:: pyflow_acdc.Results.mp_tep_fuel_type_distribution

   Generation-type mix versus limits across investment periods.

.. _res_mp_ms_tep_results:

.. automethod:: pyflow_acdc.Results.mp_ms_tep_results

   Combined MP+MS expansion tables (``grid.MP_MS_TEP_results`` when present).

.. _res_mp_ms_tep_obj_res:

.. automethod:: pyflow_acdc.Results.mp_ms_tep_obj_res

   MP+MS objective breakdown by period and scenario weight.

Sequential STEP results
^^^^^^^^^^^^^^^^^^^^^^^

.. _res_seq_step_results:

.. automethod:: pyflow_acdc.Results.seq_step_results

.. _res_seq_step_obj_res:

.. automethod:: pyflow_acdc.Results.seq_step_obj_res

.. _res_seq_step_fuel_type_distribution:

.. automethod:: pyflow_acdc.Results.seq_step_fuel_type_distribution

.. _res_seq_ms_step_results:

.. automethod:: pyflow_acdc.Results.seq_ms_step_results

.. _res_seq_ms_step_obj_res:

.. automethod:: pyflow_acdc.Results.seq_ms_step_obj_res

.. _res_seq_ms_step_fuel_type_distribution:

.. automethod:: pyflow_acdc.Results.seq_ms_step_fuel_type_distribution

Clustering results
^^^^^^^^^^^^^^^^^^

.. _res_clustering_results:

.. automethod:: pyflow_acdc.Results.clustering_results

.. _res_cluster_representatives:

.. automethod:: pyflow_acdc.Results.cluster_representatives

.. _res_clustering_technique:

.. automethod:: pyflow_acdc.Results.clustering_technique

.. _res_clustering_time_series_statistics:

.. automethod:: pyflow_acdc.Results.clustering_time_series_statistics

AC expansion line flows
^^^^^^^^^^^^^^^^^^^^^^^

.. _res_ac_exp_lines_power:

.. automethod:: pyflow_acdc.Results.ac_exp_lines_power

   Power flows on expandable AC lines after TEP (non-zero ``np_line`` only).


Other Results
^^^^^^^^^^^^^^^

.. _res_converter:
.. automethod:: pyflow_acdc.Results.converter

   Displays converter results including:
   
   - AC and DC power
   - Reactive power
   - Power losses
   - Control modes
   - Loading

   Example output::

      AC DC Converters
      +-----------+---------+---------+-----------------+----------------------+-----------------+--------------+-----------------------+-----------------------+-----------------------------+
      | Converter | AC node | DC node | Power s AC (MW) | Reactive s AC (MVAR) | Power c AC (MW) | Power DC(MW) | Reactive power (MVAR) | Power loss IGBTs (MW) | Power loss AC elements (MW) |
      +-----------+---------+---------+-----------------+----------------------+-----------------+--------------+-----------------------+-----------------------+-----------------------------+
      |     1     |    2    |    1    |      -60.0      |        -40.0         |     -59.916     |    58.652    |        -32.129        |         1.264         |            0.084            |
      |     2     |    3    |    2    |      20.774     |        7.131         |      20.782     |    -21.92    |         -0.621        |         1.139         |            0.008            |
      |     3     |    5    |    3    |       35.0      |         5.0          |      35.02      |   -36.191    |         -0.269        |          1.17         |             0.02            |
      +-----------+---------+---------+-----------------+----------------------+-----------------+--------------+-----------------------+-----------------------+-----------------------------+
      +-----------+-----------------+-----------------+-----------+----------------+
      | Converter | AC control mode | DC control mode | Loading % | Capacity [MVA] |
      +-----------+-----------------+-----------------+-----------+----------------+
      |     1     |        PQ       |       PAC       |   60.093  |      120       |
      |     2     |        PV       |      Slack      |   18.303  |      120       |
      |     3     |        PQ       |       PAC       |   30.159  |      120       |
      +-----------+-----------------+-----------------+-----------+----------------+

.. _res_dc_converter:
.. automethod:: pyflow_acdc.Results.dc_converter

   DC-side converter summary when DC converters are present.


.. _res_power_loss:
.. automethod:: pyflow_acdc.Results.power_loss

   Displays power loss information for both AC and DC grids.


   Example output::

      Power loss
      +------------------+-----------------+--------+
      |       Grid       | Power Loss (MW) | Load % |
      +------------------+-----------------+--------+
      |    AC Grid 1     |      4.393      | 32.739 |
      |    DC Grid 1     |      0.541      | 22.39  |
      | AC DC Converters |      3.685      |        |
      |    Total loss    |      8.619      |        |
      |                  |                 |        |
      |    Generation    |     173.619     |        |
      |    Efficiency    |      95.0%      |        |
      +------------------+-----------------+--------+
