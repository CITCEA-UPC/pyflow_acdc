Mapping
=======



For this module, you need to have the optional dependendency pyflow_acdc[mapping] installed.

Interactive map
---------------

.. py:function:: plot_folium(grid, text='inPu', name='grid_map',tiles="CartoDB Positron",polygon=None,ant_path='None',clustering=True,coloring=None)
   
   Creates an interactive map visualization using Folium.

   .. list-table::
      :widths: 20 10 50 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid to visualize
        - Required
      * - ``text``
        - str
        - Hover text format ('data','inPu' or 'abs')
        - 'inPu'
      * - ``name``
        - str
        - Output file name
        - 'grid_map'
      * - ``tiles``
        - str
        - "OpenStreetMap","CartoDB Positron","Cartodb dark_matter" or None
        - "CartoDB Positron"
      * - ``ant_path``
        - str
        - Animated paths
        - 'ALl', 'Reduced' or 'None'
      * - ``clustering``
        - bool
        - Enable marker clustering
        - True

   **Features**:

   - Interactive map with zoom/pan
   - Voltage level filtering
   - Component type layers:

     - MVAC Lines (<110kV)
     - HVAC Lines (<300kV)
     - EHVAC Lines (<500kV)
     - UHVAC Lines
     - DC Lines
     - Converters
     - Transformers
     - Generators by type
   - Marker clustering for generators
   - Hover information for components
   - Optional animated power flows:

     - 'All', all lines higher than 110kV
     - 'Reduced', only HVDC lines
     - 'None', no animated power flows

   **Example**

   .. code-block:: python

       import pyflow_acdc as pyf

       grid,res = pyf.NS_MTDC()

       pyf.Optimal_PF(grid)

       pyf.plot_folium(grid)

   .. figure:: ../images/north_sea_folium.svg
      :alt: Example of the Folium map.
      :align: center
      :width: 80%

   **Example with animated power flows**

   .. code-block:: python

       import pyflow_acdc as pyf

       grid,res = pyf.NS_MTDC()

       pyf.Optimal_PF(grid)

       pyf.plot_folium(grid,ant_path='All')
