Time Series Modifications
=========================

These functions are used to modify and simplify the use of time series data.

Functions are found in `pyflow_acdc.grid_modifications`.

Renewable Source Zone
---------------------

Renewable Source Zone is an object designed to unify multiple renewable sources sharing the same time series data. For instance, if multiple wind turbines generate identical power output, they can be grouped into a single wind power plant zone.


Add Renewable Source Zone
^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_RenSource_zone(grid, name)

   Adds a renewable source zone to the grid.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid to modify
      * - ``name``
        - str
        - Zone name
      * - Returns
        - Ren_source_zone
        - Created renewable zone

   **Example**

   .. code-block:: python

       zone = pyf.add_RenSource_zone(grid, "WindZone1")


Assign Renewable to Zone
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: assign_RenToZone(grid, ren_source_name, new_zone_name)

   Assigns a renewable source to a zone.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid containing source
      * - ``ren_source_name``
        - str
        - Name of renewable source
      * - ``new_zone_name``
        - str
        - Name of target zone

   **Example**

   This example shows how to assign two renewable sources to the same zone. Each renewable source has a base power of 22 MW. You can either create the renewbale sources and then the zones to assign them to or create the zone first and then add the renewable sources to it.
   
   .. code-block:: python

       grid = pyf.Grid(100)

       node = pyf.add_AC_node(grid,66, name="node1")
       node2 = pyf.add_AC_node(grid,66, name="node2")



       pyf.add_RenSource(grid, 'node1', 22, ren_source_name='wind1')
       pyf.add_RenSource(grid, 'node2', 22, ren_source_name='wind2')

       zone = pyf.add_RenSource_zone(grid, "WindZone1")

       pyf.assign_RenToZone(grid, "wind1", "WindZone1")
       pyf.assign_RenToZone(grid, "wind2", "WindZone1")

   Or you can create the zone first and then add the renewable sources to it. The assigment of zones will be called when adding the renewable sources.
  
   .. code-block:: python

       grid = pyf.Grid(100)

       node = pyf.add_AC_node(grid,66, name="node1")
       node2 = pyf.add_AC_node(grid,66, name="node2")

       pyf.add_RenSource_zone(grid, "WindZone1")

       pyf.add_RenSource(grid, 'node1', 22, ren_source_name='wind1', zone="WindZone1")
       pyf.add_RenSource(grid, 'node2', 22, ren_source_name='wind2', zone="WindZone1")


Price Zone
----------

Price zones function also like renewable sources zone when dealing with time series data. As they allow to group multiple nodes and generators with the same price data. Check the :ref:`price_zones`  and :ref:`price_zone_assignments` for more information.



Time Series data
----------------

Add Time Series
^^^^^^^^^^^^^^^

Time series data can be added to the grid by using the :py:func:`add_TimeSeries` function. This function allows to add time series data to a specific component. Time series data is imported from csv files.



.. py:function:: add_TimeSeries(grid, Time_Series_data, associated=None, TS_type=None)

   Adds time series data to grid components.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid to modify
      * - ``Time_Series_data``
        - DataFrame
        - Time series data
      * - ``associated``
        - str
        - Object name
      * - ``TS_type``
        - str
        - Time series type
      

Accepted types
^^^^^^^^^^^^^^

The time series update will depend on which type it can be associated to, this is why it is important to have different names for each object even if they are in different classes. The following types are accepted:

.. list-table::
  :widths: 10 50 20 30
  :header-rows: 1

  * - Type
    - Description
    - Object Associated
    - Affected object variable
  * - 'Load'
    - Load time series
    - :py:class:`Price_Zone`, :py:class:`Node_AC`, :py:class:`Node_DC`
    - obj.PLi_factor
  * - 'price'
    - Price time series
    - :py:class:`Price_Zone`, :py:class:`Node_AC`,  :py:class:`Node_DC`
    - obj.price
  * - 'WPP', 'OWPP', 'SF', 'REN'
    - Per unit power available of base power
    - :py:class:`Ren_source_zone`, :py:class:`Ren_Source`
    - obj.PRGi_available

The following parameters are only available for price zones [1]_.

.. list-table::
  :widths: 10 50 20 30
  :header-rows: 1   

  * - Type
    - Description
    - Object Associated
    - Affected object variable
  * - 'a_CG'
    - Quadratic factor of cost of generation
    - :py:class:`Price_Zone`
    - obj.a_CG
  * - 'b_CG'
    - Linear factor of cost of generation
    - :py:class:`Price_Zone`
    - obj.b_CG
  * - 'c_CG'
    - Constant factor of cost of generation
    - :py:class:`Price_Zone`
    - obj.c_CG
  * - 'PGL_min'
    - Minimum value of P_N for the price zone
    - :py:class:`Price_Zone`
    - obj.PGL_min
  * - 'PGL_max'
    - Maximum value of P_N for the price zone
    - :py:class:`Price_Zone`
    - obj.PGL_max

Data format
^^^^^^^^^^^^

Data format depends on the selection of ``associated`` and ``TS_type``. The value in ``associated`` is the name of the object which it refers to, this can be a node, a renewable source, a price zone or a renewable source zone.

For a dataset of length n, the CSV will follow this format: Position 0 is treated as the column name when imported into pandas. The first line should contain only headers and no data. Then there are cases where:

**associated  and TS_type assigned by user**

.. list-table::
   :class: columns-2
   :widths: 100 100
  
   * - .. list-table::
         :widths: 10 10 
         :header-rows: 1   
         :align: left

         * - position
           - value
         * - 0
           - time series name
         * - 1
           - start of the data
         * - n
           - end of the data

     - .. list-table::
         :widths: 10 10 10 10
         :header-rows: 1   
         :align: right

         * - 0
           - Load_n1
           - Load_n2
           - price_n1
         * - 1
           - 0.95
           - 0.55
           - 20
         * - 2
           - 0.75
           - 0.95
           - 30
         * - 3
           - 0.84
           - 0.72
           - 30

.. code-block:: python

    n1_load_data = pd.DataFrame({"Load_n1": [0.95, 0.75, 0.84]})
    n2_load_data = pd.DataFrame({"Load_n2": [0.55, 0.95, 0.72]})
    price_data   = pd.DataFrame({"price_n1": [20, 30, 40]})

    pyf.add_TimeSeries(grid, n1_load_data,associated="node1", TS_type="Load")
    pyf.add_TimeSeries(grid, n2_load_data,associated="node2", TS_type="Load")
    pyf.add_TimeSeries(grid, price_data,associated="node1", TS_type="price")

**only associated assigned by user**

.. list-table::
   :class: columns-2
   :widths: 100 100
  
   * - .. list-table::
         :widths: 10 10 
         :header-rows: 1   

         * - position
           - value
         * - 0
           - time series name
         * - 1
           - TS_type
         * - 2
           - start of the data
         * - n+1
           - end of the data

     - .. list-table::
         :widths: 10 10 10 10
         :header-rows: 1   
         :align: right

         * - 0
           - Load_n1
           - Load_n2
           - price_n1
         * - 1
           - Load
           - Load
           - price
         * - 2
           - 0.95
           - 0.55
           - 20
         * - 3
           - 0.75
           - 0.95
           - 30
         * - 4
           - 0.84
           - 0.72
           - 40

.. code-block:: python

    n1_data = pd.DataFrame({"Load_n1": ['Load', 0.95, 0.75, 0.84],
                            "price_n1": ['price', 20, 30, 40]})
    n2_data = pd.DataFrame({"Load_n2": ['Load', 0.55, 0.95, 0.72]})
    pyf.add_TimeSeries(grid, n1_data,associated="node1")
    pyf.add_TimeSeries(grid, n2_data,associated="node2")

**only TS_type assigned by user**

.. list-table::
   :class: columns-2
   :widths: 100 100
  
   * - .. list-table::
         :widths: 10 10 
         :header-rows: 1   

         * - position
           - value
         * - 0
           - time series name
         * - 1
           - Object name
         * - 2
           - start of the data
         * - n+1
           - end of the data

     - .. list-table::
         :widths: 10 10 10 10
         :header-rows: 1   
         :align: right

         * - 0
           - Load_n1
           - Load_n2
           - price_n1
         * - 1
           - node1
           - node2
           - node1
         * - 2
           - 0.95
           - 0.55
           - 20
         * - 3
           - 0.75
           - 0.95
           - 30
         * - 4
           - 0.84
           - 0.72
           - 40

.. code-block:: python

    load_data  = pd.DataFrame({"Load_n1": ['node1', 0.95, 0.75, 0.84],
                               "Load_n2": ['node2', 0.55, 0.95, 0.72]})
    price_data = pd.DataFrame({"price_n1": ['node1', 20, 30, 40]})
    pyf.add_TimeSeries(grid, load_data, TS_type="Load")    
    pyf.add_TimeSeries(grid, price_data, TS_type="price")

**associated = None and TS_type = None**

.. list-table::
   :class: columns-2
   :widths: 100 100
  
   * - .. list-table::
         :widths: 10 10 
         :header-rows: 1   

         * - position
           - value
         * - 0
           - time series name
         * - 1
           - Object name
         * - 2
           - TS type
         * - 3
           - start of the data
         * - n+2
           - end of the data

     - .. list-table::
         :widths: 10 10 10 10
         :header-rows: 1   
         :align: right

         * - 0
           - Load_n1
           - Load_n2
           - price_n1
         * - 1
           - node1
           - node2
           - node1
         * - 2
           - Load
           - Load
           - price
         * - 3
           - 0.95
           - 0.75
           - 20
         * - 4
           - 0.75
           - 0.84
           - 30
         * - 5
           - 0.84
           - 0.72
           - 40

.. code-block:: python

    load_data = pd.DataFrame({"Load_n1": ['node1', 'Load', 0.95, 0.75, 0.84],
                              "Load_n2": ['node2', 'Load', 0.55, 0.95, 0.72],
                              "price_n1":['node1', 'price', 20, 30, 40]})
    pyf.add_TimeSeries(grid, load_data)   




Time-Series Clustering
----------------------

These functions are found in `pyflow_acdc.Time_series_clustering`.

.. py:function:: identify_correlations(grid, time_series=[], correlation_threshold=0, cv_threshold=0, central_market=[], print_details=False, correlation_decisions=[])

   Detects highly correlated time-series and builds reduction decisions.

.. py:function:: cluster_TS(grid, n_clusters, time_series=[], central_market=[], algorithm='Kmeans', cv_threshold=0, correlation_threshold=0.8, print_details=False, correlation_decisions=[], critical_idx=[], base_critical_ratio=0.5, scaler_type='robust', **kwargs)

   Clusters time-series profiles into representative operating states.

.. py:function:: run_clustering_analysis_and_plot(grid, algorithms=['kmeans', 'kmedoids', 'ward', 'pam_hierarchical'], n_clusters_list=DEFAULT_CLUSTER_NUMBERS, path='clustering_results', time_series=[], print_details=False, ts_options=[None, 0, 0.8], correlation_decisions=[True, '2', True], plotting_options=[None, 'svg'], identifier=None)

   Runs clustering sweeps and exports comparison plots/artifacts.

.. py:function:: cluster_analysis(grid, clustering_options)

   Applies clustering configuration and returns representative scenarios for TS/TEP workflows.

**References**

.. [1] B. C. Valerio, V. A. Lacerda, M. Cheah-Mañe, P. Gebraad, and O. Gomis-Bellmunt,
       "Optimizing offshore wind integration through multi-terminal DC grids: a market-based
       OPF framework for the North Sea interconnectors," IET Conference Proceedings, vol. 2025,
       no. 6, pp. 150–155, 2025. doi: 10.1049/icp.2025.1198