Export Files Module
====================

This module provides functions for exporting grid data to various file formats.

Functions are found in `pyflow_acdc.Export_files` and `pyflow_acdc.ACDC_OPF`.

Grid Data Export
----------------

.. py:function:: save_grid_to_file(grid, file_name, folder_name=None):

   Exports grid data to a Python file. The file can be used to load the grid data into the model. Files in the example_grids folder are examples of the files that can be generated. Any file added to this folder will be automatically loaded when the pyflow_acdc package is imported.

MATLAB Export
--------------

save_grid_to_matlab
^^^^^^^^^^^^^^^^^^^

.. py:function:: save_grid_to_matlab(grid, file_name, folder_name=None, dcpol=2)

   Exports grid to MATLAB format. It is important to note, that for MATACDC format, only one polarity can be chosen for all DC grids.

   .. list-table::
      :widths: 20 10 50 20
      :header-rows: 1

      * - Parameter
        - Type
        - Description
        - Default
      * - ``grid``
        - Grid
        - Grid to export
        - Required
      * - ``file_name``
        - str
        - Output filename
        - Required
      * - ``folder_name``
        - str
        - Output folder
        - None
      * - ``dcpol``
        - int
        - DC polarity
        - 2

Pickle Export
-------------

.. py:function:: save_pickle(grid, path, compress=True, use_dill=False)

   Serializes a grid object to pickle/dill for later reload with
   :py:func:`Create_grid_from_pickle`.

Solver Progress Export
----------------------

.. py:function:: export_solver_progress_to_excel(solver_stats, save_path)

   Exports solver callback/progress records to an Excel file.

   
