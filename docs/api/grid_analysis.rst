Grid Analysis
=============

This module provides utility and grid-analysis helpers used by power-flow and
optimization workflows.

Functions are found in `pyflow_acdc.grid_analysis`.

Coordinate Conversion Utilities
-------------------------------

.. py:function:: pol2cart(r, theta)

   Converts polar coordinates to Cartesian coordinates.

.. py:function:: cart2pol(x, y)

   Converts Cartesian coordinates to polar coordinates.

.. py:function:: pol2cartz(r, theta)

   Converts polar coordinates to a complex number.

.. py:function:: cartz2pol(z)

   Converts a complex number to polar coordinates.

Electrical Parameter Utilities
------------------------------

.. py:function:: Cable_parameters(S_base, R, L_mH, C_uF, G_uS, A_rating, kV_base, km, N_cables=1, f=50)

   Converts cable data to per-unit equivalent parameters and rating.

.. py:function:: Converter_parameters(S_base, kV_base, T_R_Ohm, T_X_mH, PR_R_Ohm, PR_X_mH, Filter_uF, f=50)

   Converts converter transformer/reactor/filter data to per-unit values.

Grid State and Analysis
-----------------------

.. py:function:: grid_state(grid)

   Returns aggregate load and generation bounds for the current grid.

.. py:function:: analyse_grid(grid)

   Detects enabled grid features (AC/DC presence, TEP flags, converter modes,
   generator activation) and stores them in the grid object.

.. py:function:: current_fuel_type_distribution(grid, output='df')

   Returns the current generation mix summary by type.

   - ``output='df'`` returns a pandas DataFrame
   - ``output='dict'`` returns a dictionary
