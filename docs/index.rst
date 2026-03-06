.. pyflow acdc documentation master file, created by
   sphinx-quickstart on Thu Feb 27 09:19:48 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. figure:: images/logo_dark.svg
   :align: right
   :width: 300px

PyFlow ACDC
===========

Welcome to PyFlow ACDC's documentation!

This is a  python-based tool for the design and analysis of hybrid AC/DC grids

PyFlow ACDC is a program worked on by `ADOreD Project <https://www.msca-adored.eu/>`_.

.. figure:: images/ADOreD_logo_colours.png
   :align: right
   :width: 250px


This project has received funding from the European Union’s  Horizon Europe 
Research and Innovation programme under the Marie Skłodowska-Curie grant 
agreement No 101073554.

This documentation is under active development if any questions arise please contact the authors.

.. toctree::
   :maxdepth: 2
   :caption: Introduction:

   installation
   usage
   citing

API Documentation
^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 3
   :caption: Grid Management:

   api/modelling
   api/grid
   api/csv_import
   api/grid_mod
   api/grid_analysis
   api/results

.. toctree::
   :maxdepth: 3
   :caption: Power Flow Analysis:

   api/pf
   api/opf
   api/L_opf

.. toctree::
   :maxdepth: 3  
   :caption: Time Series & Analysis:

   api/ts_mod
   api/ts
   api/market_coef

.. toctree::
   :maxdepth: 3
   :caption: Transmission Expansion Planning:

   api/tep
   api/tep_pymoo
   api/tep_dynamic
   api/wf_array

.. toctree::
   :maxdepth: 3
   :caption: Visualization & Export:

   api/plotting
   api/dash
   api/folium
   api/export_files

Quick Start
-----------

Basic installation::

    pip install pyflow-acdc

Basic usage::

   import pyflow_acdc as pyf

   #Use pre saved grids to familiarize yourself with the package
   [grid,res]=pyf.PEI_grid()

   pyf.ACDC_sequential(grid,QLimit=False)

   
   res.All()
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`