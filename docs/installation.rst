Installation
============

Requirements
------------
* Python 3.10+
* Dependencies:
    * numpy
    * pandas
    * networkx
    * matplotlib
    * scipy
    * prettytable
    * plotly
    * geopandas
    * pyyaml
    * shapely
    * svgwrite
    * kmedoids
    * scikit-learn
    * openpyxl
    * dill
    * xlsxwriter
    * utm

* Optional dependencies:
    * Mapping:
        * folium
        * branca
    * Optimal power flow:  
        * pyomo
    * Dash:
        * dash
    * Array optimization:
        * ortools
        * pyomo
    * TEP (pymoo wrapper):
        * pymoo
        * pyomo
    * Gurobi:
        * gurobipy
    * Plot export:
        * kaleido



Install from PyPI
-----------------
::

    pip install pyflow-acdc


Install from source
-------------------
::

    git clone https://github.com/CITCEA-UPC/pyflow_acdc.git
    cd pyflow_acdc
    pip install -e .



Making Changes
--------------

1. Create a new branch for your changes::

    git checkout -b new-branch-name
    git push origin new-branch-name

2. To push your changes to the remote repository::

    git add .
    git commit -m "Description of your changes"
    git pull origin new-branch-name
    git push origin new-branch-name

3. To pull the latest changes from the remote repository::

    git pull origin main

.. note::
    To merge your changes into the main branch please contact the repository owner.

Additional Dependencies
------------------------

Install optional dependency groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Install with pip extras as defined in ``pyproject.toml``::

    pip install pyflow-acdc[mapping]
    pip install pyflow-acdc[OPF]
    pip install pyflow-acdc[Dash]
    pip install pyflow-acdc[Array_OPT]
    pip install pyflow-acdc[TEP_pymoo]
    pip install pyflow-acdc[Gurobi]
    pip install pyflow-acdc[plotting]
    pip install pyflow-acdc[All]

Solver installation notes
^^^^^^^^^^^^^^^^^^^^^^^^^
Some solvers are external to Python wheels and must be installed separately.

For IPOPT (commonly used with OPF)::

    conda install -c conda-forge ipopt

For Bonmin (typically used for MINLP TEP, Linux recommended)::

    sudo apt update
    sudo apt install coinor-libbonmin-dev
    conda install -c conda-forge coin-or-bonmin

**Note:** bonmin and ipopt are only available through conda-forge, not pip. Make sure you have conda installed on your Linux system.
