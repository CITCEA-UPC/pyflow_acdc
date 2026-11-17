.. pyflow acdc documentation master file, created by
   sphinx-quickstart on Thu Feb 27 09:19:48 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. themed-figure:: pyflowacdc_logo
   :align: right
   :width: 300px

pyflow-acdc
===========

Welcome to the pyflow-acdc documentation!

This is a python-based tool for the design and analysis of hybrid AC/DC grids

pyflow-acdc is a program worked on by `ADOreD Project <https://www.msca-adored.eu/>`_ by `CITCEA-UPC <https://www.linkedin.com/company/citcea>`_ in collaboration with `Youwind <https://youwindrenewables.com/>`_.

.. figure:: images/logos/ADOreD_logo_colours.png
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
   api/cable_database
   api/grid_analysis
   api/results

.. toctree::
   :maxdepth: 3
   :caption: Power Flow Analysis:

   api/pf
   api/opf
   api/socp
   api/L_models

.. toctree::
   :maxdepth: 3  
   :caption: Time Series & Analysis:

   api/ts_mod
   api/clustering
   api/ts
   api/window
   api/market_coef

.. toctree::
   :maxdepth: 3
   :caption: Transmission Expansion Planning:

   api/tep
   api/sequential_step
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

.. toctree::
   :maxdepth: 1
   :caption: Development:

   architecture
   testing
   api/constants
   api/solver_utils
   api/windfarm_loader

Quick Start
-----------

Basic installation::

    pip install pyflow-acdc

.. literalinclude:: ../pyflow_tests/doc_examples/index/basic_usage.py
   :language: python
   :lines: 2-

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`