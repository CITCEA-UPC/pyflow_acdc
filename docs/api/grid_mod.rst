Grid Modifications
==================

This module provides functions for modifying existing grids by adding components and zones.

Functions are found in `pyflow_acdc.grid_modifications`.

Add Grid Components
-------------------

Add AC Node
^^^^^^^^^^^^	

.. py:function:: add_AC_node(grid, kV_base, node_type='PQ', Voltage_0=1.01, theta_0=0.01, Power_Gained=0, Reactive_Gained=0, Power_load=0, Reactive_load=0, name=None, Umin=0.9, Umax=1.1, Gs=0, Bs=0, x_coord=None, y_coord=None, geometry=None)

   Adds an AC node to the grid.

   .. list-table::
      :widths: 20 10 50 10 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Units
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``kV_base``
        - float
        - Base voltage
        - Required
        - kV
      * - ``node_type``
        - str
        - Node type ('PQ', 'PV', or 'Slack')
        - 'PQ'
        - -
      * - ``Voltage_0``
        - float
        - Initial voltage magnitude in p.u.
        - 1.01
        - p.u.
      * - ``theta_0``
        - float
        - Initial voltage angle
        - 0.01
        - rad
      * - ``Power_Gained``
        - float
        - Active power generation
        - 0
        - p.u.
      * - ``Reactive_Gained``
        - float
        - Reactive power generation
        - 0
        - p.u.
      * - ``Power_load``
        - float
        - Active power load
        - 0
        - p.u.
      * - ``Reactive_load``
        - float
        - Reactive power load
        - 0
        - p.u.
      * - ``name``
        - str
        - Node name
        - None
        - -
      * - ``Umin``
        - float
        - Minimum voltage magnitude
        - 0.9
        - p.u.
      * - ``Umax``
        - float
        - Maximum voltage magnitude
        - 1.1
        - p.u.
      * - ``Gs``
        - float
        - Shunt conductance
        - 0
        - p.u.
      * - ``Bs``
        - float
        - Shunt susceptance
        - 0
        - p.u.
      * - ``x_coord``
        - float
        - X coordinate for plotting
        - None
        - -
      * - ``y_coord``
        - float
        - Y coordinate for plotting
        - None
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -
  

   **Example**

   .. code-block:: python

       node = pyf.add_AC_node(grid, kV_base=400, name='bus1', node_type='PQ')

       #OR

       node1 = pyf.Node_AC('PQ', 1, 0,66, Power_Gained=0.5, name='Bus1')

       grid.nodes_AC.append(node1)


Add AC Line
^^^^^^^^^^^^

.. py:function:: add_line_AC(grid, fromNode, toNode,MVA_rating=None, r=0, x=0, b=0, g=0,R_Ohm_km=None,L_mH_km=None, C_uF_km=0, G_uS_km=0, A_rating=None ,m=1, shift=0, name=None,tap_changer=False,Expandable=False,N_cables=1,Length_km=1,geometry=None,data_in='pu',Cable_type:str ='Custom',update_grid=True):
    
   Adds an AC line to the grid.

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``fromNode``
        - Node_AC
        - Source node
        - Required
        - -
      * - ``toNode``
        - Node_AC
        - Destination node
        - Required
        - -
      * - ``m``
        - float
        - Transformer ratio
        - 1
        - -
      * - ``shift``
        - float
        - Phase shift angle
        - 0
        - radians
      * - ``tap_changer``
        - bool
        - If True, creates tap changer transformer
        - False
        - -
      * - ``Expandable``
        - bool
        - If True, creates expandable line
        - False
        - -
      * - ``N_cables``
        - int
        - Number of parallel cables
        - 1
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -  
      * - ``data_in``
        - str
        - Input format ('pu', 'Ohm', 'Real')
        - 'pu'
        - -
      
   For lines with data_in = 'pu':

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``r, x, b, g``
        - float
        - Line parameters in p.u.
        - 0
        - p.u.
      * - ``MVA_rating``
        - float
        - Line rating in MVA
        - Required
        - MVA  

   For lines with data_in = 'Ohm':

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``r, x, b, g``
        - float
        - Line parameters in Ω
        - 0
        - Ω
      * - ``MVA_rating``
        - float
        - Line rating in MVA
        - Required
        - MVA

   For lines with data_in = 'Real':

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``R_Ohm_km``
        - float
        - Resistance 
        - Required
        - Ω/km
      * - ``L_mH_km``
        - float
        - Inductance 
        - Required
        - mH/km
      * - ``C_uF_km``
        - float
        - Capacitance 
        - 0
        - μF/km
      * - ``G_uS_km``
        - float
        - Conductance 
        - 0
        - μS/km
      * - ``A_rating``
        - float
        - Current rating 
        - Required
        - A
      * - ``Length_km``
        - float
        - Line length
        - 1
        - km
   
   For pre defined cable types database

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``Cable_type``
        - str
        - Cable specification name
        - Required
        - -
      * - ``Length_km`` 
        - float
        - Line length
        - 1
        - km    

   **Example**

   .. code-block:: python

       import pyflow_acdc as pyf
       #Create nodes
       node1 = pyf.Node_AC('PQ', 1, 0,66, Power_Gained=0.5, name='Bus1')
       node2 = pyf.Node_AC('Slack', 1, 0,66,name='Bus2')

       #Create grid
       grid = pyf.Grid(100,nodes_AC=[node1,node2])

       #For data_in = 'pu' 
       line_pu = pyf.add_line_AC(grid, node1, node2, r=0.029, x=0.0032,b=0.0022, Length_km=10,MVA_rating=50)

       #For data_in = 'Ohm'
       line_ohm = pyf.add_line_AC(grid, node1, node2, r=1.2632, x=0.1393,b=0.0000505, Length_km=10,MVA_rating=50, data_in='Ohm')

       #For data_in = 'Real'
       line_real = pyf.add_line_AC(grid, node1, node2, R_Ohm_km=0.128, L_mH_km=0.443,C_uF_km=0.163, G_uS_km=0.0, Length_km=10, A_rating=445,data_in='Real')

       #For pre defined cable types database
       line_db = pyf.add_line_AC(grid, node1, node2, Cable_type='NREL_XLPE_185mm_66kV',Length_km=10)

Line sizing
^^^^^^^^^^^

Add Cable Options
~~~~~~~~~~~~~~~~~

.. py:function:: add_cable_option(grid, cable_types: list,name=None)

   Adds a cable option to the grid. This is a list that will link different line sizing options to one singular cable type list, so that only a set maximum number of different ones are used.

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description 
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``cable_types``
        - list
        - List of cable types
        - Required
        - -
      * - ``name``
        - str
        - Name of the cable option
        - None
        - -

   **Example**

   .. code-block:: python

        cable_option = pyf.add_cable_option(grid,[
        'ABB_Cu_XLPE_95mm2_66kV', #0
        'ABB_Cu_XLPE_120mm2_66kV', #1
        'ABB_Cu_XLPE_150mm2_66kV', #2
        'ABB_Cu_XLPE_185mm2_66kV', #3
        'ABB_Cu_XLPE_240mm2_66kV', #4
        'ABB_Cu_XLPE_300mm2_66kV', #5
        'ABB_Cu_XLPE_400mm2_66kV', #6
        'ABB_Cu_XLPE_500mm2_66kV', #7
        'ABB_Cu_XLPE_630mm2_66kV', #8
        'ABB_Cu_XLPE_800mm2_66kV', #9
        'ABB_Cu_XLPE_1000mm2_66kV'] )#10

        grid.cab_types_allowed = 3 

Add Line sizing
~~~~~~~~~~~~~~~

.. py:function:: add_line_sizing(grid, fromNode, toNode, cable_types: list=[], active_config: int = 0,Length_km=1.0,S_base=100,name=None,cable_option=None,update_grid=True,geometry=None)

   Adds a line sizing to the grid.

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``fromNode``
        - Node_AC
        - Source node
        - Required
        - -
      * - ``toNode``
        - Node_AC
        - Destination node
        - Required
        - -
      * - ``cable_types`` 
        - list
        - List of cable types
        - Required
        - -
      * - ``active_config``
        - int
        - Active configuration
        - First of the list
        - -
      * - ``Length_km``
        - float
        - Line length
        - 1
        - km
      * - ``S_base``
        - float
        - Base power
        - 100
        - MVA
      * - ``name``
        - str
        - Name of the line sizing
        - None
        - -
      * - ``cable_option``
        - str
        - Cable option
        -   
        - -
      * - ``update_grid``
        - bool
        - Update the grid
        - True
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -



Add DC Node
^^^^^^^^^^^^

.. py:function:: add_DC_node(grid, kV_base, node_type='P', Voltage_0=1.01, Power_Gained=0, Power_load=0, name=None, Umin=0.95, Umax=1.05, x_coord=None, y_coord=None, geometry=None)

   Adds a DC node to the grid.

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``kV_base``
        - float
        - Base voltage
        - Required
        - kV
      * - ``node_type``
        - str
        - Node type ('P', 'Slack', or 'Droop')
        - 'P'
        - -
      * - ``Voltage_0``
        - float
        - Initial voltage magnitude
        - 1.01
        - p.u.
      * - ``Power_Gained``
        - float
        - Power generation
        - 0
        - p.u.
      * - ``Power_load``
        - float
        - Power load
        - 0
        - p.u.
      * - ``name``
        - str
        - Node name
        - None
        - -
      * - ``Umin``
        - float
        - Minimum voltage magnitude
        - 0.95
        - p.u.
      * - ``Umax``
        - float
        - Maximum voltage magnitude
        - 1.05
        - p.u.
      * - ``x_coord``
        - float
        - X coordinate for plotting
        - None
        - -
      * - ``y_coord``
        - float
        - Y coordinate for plotting
        - None
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -
   

   **Example**

   .. code-block:: python

       import pyflow_acdc as pyf
       #Create grid
       grid = pyf.Grid(100)

       #Create DC node  
       node = pyf.add_DC_node(grid, kV_base=525, name='dc_bus1')  

       #OR

       node1 = pyf.Node_DC('P', 1, 0,0,525,name='Bus1')

       grid.nodes_DC.append(node1)


Add DC Line
^^^^^^^^^^^^

.. py:function:: add_line_DC(grid, fromNode, toNode, r=0.001, MW_rating=9999,Length_km=1,R_Ohm_km=None,A_rating=None,polarity='m', name=None,geometry=None,Cable_type:str ='Custom',data_in='pu',update_grid=True):
    
   Adds a DC line to the grid.

   .. list-table::
      :widths: 15 10 50 10 15
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``fromNode``
        - Node_DC
        - Source node
        - Required
        - -
      * - ``toNode``
        - Node_DC
        - Destination node
        - Required
        - -
      * - ``r``
        - float
        - Line resistance
        - 0.001
        - p.u.
      * - ``MW_rating``
        - float
        - Power rating
        - 9999
        - MW
      * - ``Length_km``
        - float
        - Line length
        - 1
        - km
      * - ``R_Ohm_km``
        - float
        - Line resistance in ohms per kilometer
        - None
        - Ω/km
      * - ``A_rating``
        - float
        - Line rating
        - None
        - A
      * - ``polarity``
        - str
        - 'm' for asymmetric monopolar, 'sm' for symmetric monopolar, 'b' for bipolar
        - 'm'
        - -
      * - ``name``
        - str
        - Line name
        - None
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -
      * - ``Cable_type``
        - str
        - Cable specification name
        - 'Custom'
        - -
      * - ``data_in``
        - str
        - Input data format ('pu' or 'Ohm')
        - 'pu'
        - -
      * - ``update_grid``
        - bool
        - Whether to update the grid after adding the line
        - True
        - -

   **Example**

   .. code-block:: python

      import pyflow_acdc as pyf
      #Create grid
      grid = pyf.Grid(100)

      #Create nodes
      node1 = pyf.add_DC_node(grid, 525)
      node2 = pyf.add_DC_node(grid, 525)

      line = pyf.add_line_DC(grid, node1, node2, Resistance_pu=0.0000318, MW_rating=1000, polarity='b', Length_km=10)

      #OR
      node3 = pyf.add_DC_node(grid, 525)
      node4 = pyf.add_DC_node(grid, 525) 

      line_db = pyf.add_line_DC(grid, node3, node4, Cable_type='NREL_HVDC_2500mm_525kV', polarity='b', Length_km=10)

Add AC/DC Converter
^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_ACDC_converter(grid, AC_node, DC_node, AC_type='PV', DC_type=None, P_AC_MW=0, Q_AC_MVA=0, P_DC_MW=0, Transformer_resistance=0, Transformer_reactance=0, Phase_Reactor_R=0, Phase_Reactor_X=0, Filter=0, Droop=0, kV_base=None, MVA_max=None, nConvP=1, polarity=1, lossa=1.103, lossb=0.887, losscrect=2.885, losscinv=4.371, Ucmin=0.85, Ucmax=1.2, name=None, geometry=None)

   Adds an AC/DC converter to the grid.

   .. list-table::
      :widths: 15 10 50 15 10
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
        - Unit
      * - ``grid``
        - Grid
        - Grid to modify
        - Required
        - -
      * - ``AC_node``
        - Node_AC
        - AC side node
        - Required
        - -
      * - ``DC_node``
        - Node_DC
        - DC side node
        - Required
        - -
      * - ``AC_type``
        - str
        - AC control type ('PV', 'PQ', 'Slack')
        - 'PV'
        - -
      * - ``DC_type``
        - str
        - DC control type ('P', 'Slack', 'Droop')
        - None
        - -
      * - ``P_AC_MW``
        - float
        - AC active power setpoint
        - 0
        - MW
      * - ``Q_AC_MVA``
        - float
        - AC reactive power setpoint
        - 0
        - MVAr
      * - ``P_DC_MW``
        - float
        - DC power setpoint
        - 0
        - MW
      * - ``Transformer_resistance``
        - float
        - Transformer resistance
        - 0
        - pu
      * - ``Transformer_reactance``
        - float
        - Transformer reactance
        - 0
        - pu
      * - ``Phase_Reactor_R``
        - float
        - Phase reactor resistance
        - 0
        - pu
      * - ``Phase_Reactor_X``
        - float
        - Phase reactor reactance
        - 0
        - pu
      * - ``Filter``
        - float
        - Filter susceptance
        - 0
        - pu
      * - ``Droop``
        - float
        - Droop constant
        - 0
        - pu
      * - ``kV_base``
        - float
        - AC side base voltage
        - None
        - kV
      * - ``MVA_max``
        - float
        - Converter rating
        - None
        - MVA
      * - ``nConvP``
        - int
        - Number of parallel converters
        - 1
        - -
      * - ``geometry``
        - Geometry
        - Shapely geometry object
        - None
        - -
      * - Returns
        - AC_DC_converter
        - Created converter
        - -
        - -

   For Power Flow AC side control type:   

   .. list-table::
      :widths: 10 10 80
      :header-rows: 1

      * - ``AC_type``
        - ``DC_type``
        - Additional requiered Values
      * - Slack
        - PAC
        - None
      * - PQ
        - PAC
        - ``Q_AC_MVA``
      * - PV
        - PAC
        - ``P_AC_MW``

   For Power Flow DC side control type:  

   .. list-table::
      :widths: 10 10 80
      :header-rows: 1

      * - ``DC_type``
        - ``AC_type``
        - Requiered Values
      * - P
        - PQ, PV
        - ``P_DC_MW``
      * - Droop
        - PQ, PV
        - ``P_DC_MW`` , ``Droop``

**Example**

.. code-block:: python

    conv = pyf.add_ACDC_converter(grid, ac_node, dc_node, MVA_max=1000)

Add Generator
^^^^^^^^^^^^^^

.. py:function:: add_gen(grid, node_name, gen_name=None, price_zone_link=False, lf=0, qf=0, MWmax=99999, MWmin=0, MVArmin=None, MVArmax=None, PsetMW=0, QsetMVA=0, Smax=None, fuel_type='Other', geometry=None)

   Adds a generator to the grid.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid to modify
      * - ``node_name``
        - str
        - Name of node to connect to
      * - ``gen_name``
        - str
        - Generator name
      * - ``MWmax``
        - float
        - Maximum active power
      * - ``MWmin``
        - float
        - Minimum active power
      * - ``MVArmin``
        - float
        - Minimum reactive power
      * - ``MVArmax``
        - float
        - Maximum reactive power
      * - ``fuel_type``
        - str
        - Generator fuel type
      * - Returns
        - Gen_AC
        - Created generator

   **Example**

   .. code-block:: python

       gen = pyf.add_gen(grid, "bus1", MWmax=500, fuel_type="Natural Gas")

Add Renewable Source
^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_RenSource(grid, node_name, base, ren_source_name=None, available=1, zone=None, price_zone=None, Offshore=False, MTDC=None, geometry=None, ren_type='Wind')

   Adds a renewable energy source to the grid.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid to modify
      * - ``node_name``
        - str
        - Name of node to connect to
      * - ``base``
        - float
        - Base power in MW
      * - ``ren_type``
        - str
        - Type ('Wind', 'Solar')
      * - ``zone``
        - str
        - Renewable zone name
      * - ``price_zone``
        - str
        - Price zone name
      * - Returns
        - Ren_Source
        - Created renewable source

   **Example**

   .. code-block:: python

       source = pyf.add_RenSource(grid, "bus1", 100, ren_type="Wind")


.. _price_zones:

Add Price Zone
^^^^^^^^^^^^^^	

.. py:function:: add_price_zone(grid, name, price, import_pu_L=1, export_pu_G=1, a=0, b=1, c=0, import_expand_pu=0)

   Adds a price zone to the grid.

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
      * - ``price``
        - float
        - Base price
      * - ``import_pu_L``
        - float
        - Import limit p.u.
      * - ``export_pu_G``
        - float
        - Export limit p.u.
      * - Returns
        - Price_Zone
        - Created price zone

   **Example**

   .. code-block:: python

       zone = pyf.add_price_zone(grid, "Zone1", price=50)


.. _price_zone_assignments:



Add DCDC Converter
^^^^^^^^^^^^^^^^^^

.. py:function:: add_DCDC_converter(grid, fromNode, toNode, P_MW=None, Pset=None, R_Ohm=None, r=0.0001, MW_rating=99999, name=None, geometry=None)

   Adds a DC/DC converter between two DC nodes.

Add DC Generator
^^^^^^^^^^^^^^^^

.. py:function:: add_gen_DC(grid, node_name, gen_name=None, price_zone_link=False, lf=0, qf=0, fc=0, MWmax=99999, MWmin=0, PsetMW=0, fuel_type='Other', geometry=None, installation_cost=0, np_gen=1)

   Adds a generator connected to a DC node.

Add External Grid
^^^^^^^^^^^^^^^^^

.. py:function:: add_extgrid(grid, node, gen_name=None, price_zone_link=False, lf=0, qf=0, MVAmax=99999, MWmax=None, MVArmin=None, MVArmax=None, Allow_sell=True, P_load_MW=0)

   Adds an external grid equivalent as a generator-like source.

Bulk Add Generators
^^^^^^^^^^^^^^^^^^^

.. py:function:: add_generators(grid, Gen_csv, curtailmet_allowed=1)

   Adds multiple generators from tabular input.

Add Renewable Source Zone
^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_RenSource_zone(grid, name)
   :no-index:

   Adds a renewable source zone object.

   See also :doc:`ts_mod`.

Add MTDC Price Zone
^^^^^^^^^^^^^^^^^^^

.. py:function:: add_MTDC_price_zone(grid, name, linked_price_zones=None, pricing_strategy='avg')

   Adds an MTDC price zone linked to existing price zones.

Add Offshore Price Zone
^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_offshore_price_zone(grid, main_price_zone, name)

   Adds an offshore price zone linked to a main/onshore price zone.

Add Time Series
^^^^^^^^^^^^^^^

.. py:function:: add_TimeSeries(grid, Time_Series_data, associated=None, TS_type=None, name=None)
   :no-index:

   Adds time-series data to grid elements.

   See full data-format details in :doc:`ts_mod`.

Add Investment Series
^^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_inv_series(grid, inv_data, associated=None, inv_type=None, name=None)

   Adds dynamic investment-period series data to supported elements.

Add Generator Mix Limits
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: add_gen_mix_limits(grid, mix_data)

   Adds generation-mix constraint data for optimization workflows.

Assign Node to Price Zone
^^^^^^^^^^^^^^^^^^^^^^^^^	

.. py:function:: assign_nodeToPrice_Zone(grid, node_name, ACDC, new_price_zone_name)

   Assigns a node to a price zone.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid containing node
      * - ``node_name``
        - str
        - Name of node to assign
      * - ``ACDC``
        - str
        - 'AC' or 'DC'
      * - ``new_price_zone_name``
        - str
        - Name of target price zone

   **Example**

   .. code-block:: python

       pyf.assign_nodeToPrice_Zone(grid, "bus1", "AC", "Zone1")

Assign Converter to Price Zone
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: assign_ConvToPrice_Zone(grid, conv_name, new_price_zone_name)

   Assigns an AC/DC converter to a price zone.

Template and Import Helpers
---------------------------

.. py:function:: create_inv_csv_template(grid, file_path=None, exclude=None)

   Creates a CSV template for dynamic investment-series input.

.. py:function:: create_gen_limit_csv_template(grid, file_path=None)

   Creates a CSV template for generation mix limit input.

.. py:function:: import_orbit_cables(data=None, column_map=None, default_type='AC', name_prefix='NREL', save_yaml=False, source_url='https://github.com/NLRWindSystems/ORBIT/tree/dev/library/cables')

   Imports/normalizes ORBIT-style cable data into the cable database format.


Line Modifications
------------------

Change Line to Expandable
^^^^^^^^^^^^^^^^^^^^^^^^^    

.. py:function:: change_line_AC_to_expandable(grid, line_name)

   Converts an AC line to an expandable line.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid containing line
      * - ``line_name``
        - str
        - Name of line to convert

   **Example**

   .. code-block:: python

       pyf.change_line_AC_to_expandable(grid, "line1")

Change Line to Reconducting
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: change_line_AC_to_reconducting(grid, line_name, r_new, x_new, g_new, b_new, MVA_rating_new, Life_time, base_cost)

   Converts an AC line to a reconducting line.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid containing line
      * - ``line_name``
        - str
        - Name of line to convert
      * - ``r_new``
        - float
        - Resistance of reconducting line
      * - ``x_new``
        - float
        - Reactance of reconducting line
      * - ``g_new``
        - float
        - Conductance of reconducting line
      * - ``b_new``
        - float
        - Susceptance of reconducting line
      * - ``MVA_rating_new``
        - float
        - MVA rating of reconducting line
      * - ``Life_time``
        - float
        - Life time of reconducting line
      * - ``base_cost``
        - float
        - Base cost of reconducting line

   Internally the original line is included into the reconducting line, as a base line, ``line.rec_branch`` is set to False. When set to True, the reconducted line is active in the grid.

   **Example**

   .. code-block:: python

       pyf.change_line_AC_to_reconducting(grid, "line1", r_new=0.1, x_new=0.2, g_new=0, b_new=0.1, MVA_rating_new=100, Life_time=20, base_cost=1000000)








Change Line to Transformer
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: change_line_AC_to_tap_transformer(grid, line_name)

   Converts an AC line to a tap-changing transformer.

   .. list-table::
      :widths: 20 10 70
      :header-rows: 1

      * - Parameter
        - Type
        - Description
      * - ``grid``
        - Grid
        - Grid containing line
      * - ``line_name``
        - str
        - Name of line to convert

   **Example**

   .. code-block:: python

       pyf.change_line_AC_to_tap_transformer(grid, "line1")

