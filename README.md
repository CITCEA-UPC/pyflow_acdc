<img src="docs/images/logos/logo_dark.svg" align="right" width="200px">

# pyflow-acdc

[![PyPI version](https://img.shields.io/pypi/v/pyflow-acdc)](https://pypi.org/project/pyflow-acdc/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyflow-acdc)](https://pypi.org/project/pyflow-acdc/)
[![License](https://img.shields.io/github/license/CITCEA-UPC/pyflow_acdc)](https://github.com/CITCEA-UPC/pyflow_acdc/blob/main/LICENSE)
[![PR tests](https://github.com/CITCEA-UPC/pyflow_acdc/actions/workflows/pr-tests.yml/badge.svg)](https://github.com/CITCEA-UPC/pyflow_acdc/actions/workflows/pr-tests.yml)
[![codecov](https://codecov.io/gh/CITCEA-UPC/pyflow_acdc/graph/badge.svg)](https://codecov.io/gh/CITCEA-UPC/pyflow_acdc)
[![Documentation Status](https://readthedocs.org/projects/pyflow-acdc/badge/?version=latest)](https://pyflow-acdc.readthedocs.io/en/latest/)

A python-based tool for the design and analysis of hybrid AC/DC grids.


pyflow-acdc is a program worked on by ADOreD Project by CITCEA-UPC in collaboration with Youwind

This project has received funding from the European Union’s  Horizon Europe 
Research and Innovation programme under the Marie Skłodowska-Curie grant 
agreement No 101073554.

## Important

This project is experimental and under active development. Issue reports and contributions are very welcome.


## Citation

If you use this package in your research, please cite the publication that
matches the feature you relied on. Software citation metadata is also in
[`CITATION.cff`](CITATION.cff) (GitHub *Cite this repository*). BibTeX for
every entry is on the docs [Citing](https://pyflow-acdc.readthedocs.io/en/latest/citing.html) page.

**General framework** (general usage / AC–DC OPF tool):

```
B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
"An Optimal Power Flow Tool for AC/DC Systems, Applied to the Analysis of the
North Sea Grid for Offshore Wind Integration," in IEEE Transactions on Power
Systems, vol. 40, no. 5, pp. 4278–4291, Sept. 2025,
doi: 10.1109/TPWRS.2025.3533889.
```

**Market-based OPF** (market / price-zone integration):

```
B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
"Optimizing Offshore Wind Integration through Multi-Terminal DC Grids: A
Market-Based OPF Framework for the North Sea Interconnectors,"
IET Conference Proceedings, vol. 2025, no. 6, pp. 150–155, 2025,
doi: 10.1049/icp.2025.1198.
```

**Transmission expansion planning** (hybrid AC/DC TEP / MINLP):

```
B. C. Valerio, M. Cheah-Mane, V. A. Lacerda, P. Gebraad and O. Gomis-Bellmunt,
"Transmission expansion planning for hybrid AC/DC grids using a mixed-integer
non-linear programming approach," International Journal of Electrical Power &
Energy Systems, vol. 174, p. 111459, 2026,
doi: 10.1016/j.ijepes.2025.111459.
```

**Array optimization** (inter-array cabling / CSS / sizing):

```
Castro Valerio, B., Gebraad, P. M. O., Cheah-Mane, M., A. Lacerda, V., and
Gomis-Bellmunt, O.: A multi-stage methodology for wind park inter-array
cabling: graph preparation, layout, and sizing, Wind Energ. Sci. Discuss.
[preprint], https://doi.org/10.5194/wes-2026-53, in review, 2026.
```

**BESS / hydrogen / energy-island operation** (storage, electrolyser, window OPF):

```
M. Useche-Arteaga, P. Gebraad, V. Lacerda, M. Cheah-Mane, and O. Gomis-Bellmunt,
Optimizing the operation of energy islands with predictive nonlinear
programming -- a case study based on the Princess Elisabeth Energy Island,
Wind Energy Science, 11(2), 349–372, 2026,
doi: 10.5194/wes-11-349-2026.
```

**Heat pumps / LEC flexibility** (`HeatPump`, `add_heat_pump`):

```
M. Montalà-Palau, J. J. Markus, M. Kazemi, M. Cheah-Mañé, C. Papadimitriou,
and O. Gomis-Bellmunt, Enhancing Distribution System Resilience through Energy
Communities, CIRED 2026 Brussels Workshop, Paper 1361, 2026.
```

**Sparse SOCP / AC–DC energy hubs** (`socp_optimise`, ``[SOCP]``):

```
M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, Efficient AC/DC energy hubs operation using sparse SOCP
relaxation and chance-constrained optimization, Sustainable Energy, Grids and
Networks 46, 102217, 2026, doi: 10.1016/j.segan.2026.102217.
```

## Installation

### Basic Installation

Install from PyPI:
```bash
pip install pyflow-acdc
```

**Requirements:** Python 3.10 or higher

### Quick start

Bundled example grids are registered on ``pyf.cases`` when you import the package:

```python
import pyflow_acdc as pyf

grid, res = pyf.cases["case24_TEP"]()   # static TEP case with expandable AC lines
grid, res = pyf.cases["case39_acdc"]()  # hybrid AC/DC OPF case
```

Factories live under ``pyflow_acdc/example_grids/`` (``PF/``, ``OPF/``, ``TEP/``,
``Wind_Array/``). See the [usage guide](https://pyflow-acdc.readthedocs.io/en/latest/usage.html)
for the full case list and keyword arguments (for example ``NS_MTDC_2025``).

To load a MATPOWER / MATACDC case saved as a ``.mat`` file:

```python
grid, res = pyf.create_grid_from_mat("path/to/case.mat")
```

TEP-style ``.mat`` files may include expandable elements via keys such as
``ne_branch`` (AC), ``branchdc_ne`` / ``busdc_ne`` (DC), and ``convdc_ne``
(converters). Sample files used in tests are under ``pyflow_tests/``.

### For Users

Example grids and wind-farm data ship with the installed package. Some cases
(for example ``NS_MTDC_2025``) also use CSV time series from
``examples/North_Sea_grid_data/`` in the repository, or from GitHub when
``online=True``.

### For Developers
#### Initial Setup
1. Install Git if you haven't already:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install git
   # For Windows: Download from https://git-scm.com/download/win
   ```

2. Clone the repository:
```bash
git clone https://github.com/CITCEA-UPC/pyflow_acdc.git
cd pyflow_acdc
```

3. Install in development mode:
```bash
pip install -e .
```
This installs the package in "editable" mode, allowing you to modify the code without reinstalling.

#### Making Changes

1. Create a new branch for your changes:
```bash
git checkout -b new-branch-name
git push origin new-branch-name
```

2. To push your changes to the remote repository:
```bash
git add .
git commit -m "Description of your changes"
git pull origin new-branch-name
git push origin new-branch-name
```

3. To pull the latest changes from the remote repository:
```bash
git pull origin main
```

To merge your changes into the main branch please contact the repository owner.

### TestPyPI Publishing (Collaborators)

Any collaborator with permission to run GitHub Actions can publish a test build to
TestPyPI using the manual workflow.

1. Open the repository on GitHub.
2. Go to **Actions** -> **Publish to TestPyPI (manual)**.
3. Click **Run workflow** and confirm.

This publishes the current branch build to TestPyPI for validation without
affecting the production PyPI package.

### Optional Dependencies

You can install pyflow_acdc with optional dependencies using pip:

```bash
# Install with all optional dependencies (excludes gurobipy, which requires a license)
pip install pyflow-acdc[All]

# Or install specific optional dependency groups:
pip install pyflow-acdc[mapping]      # For mapping features (folium, branca)
pip install pyflow-acdc[OPF]          # For optimal power flow (pyomo)
pip install pyflow-acdc[SOCP]         # For sparse SOCP (cvxpy)
pip install pyflow-acdc[Dash]         # For Dash web applications
pip install pyflow-acdc[LINEAR_ARRAY]  # OR-Tools route MIP + CSS + HiGHS (ortools, highspy)
pip install pyflow-acdc[TEP_pymoo]    # For TEP with pymoo (pymoo, pyomo)
pip install pyflow-acdc[Gurobi]       # For Gurobi solver (requires license)
pip install pyflow-acdc[plotting]     # For static image export (kaleido)
```

Or install individual packages manually:

**For mapping:**
```bash
pip install folium branca
```

**For OPF:**
```bash
pip install pyomo
conda install -c conda-forge ipopt
```

**For Array Optimization (OR-Tools path):**
```bash
pip install ortools
pip install highspy  # Optional: for HiGHS solver
```

**For Array Optimization (Pyomo CSS path):**
```bash
pip install pyomo
# Optional: Gurobi for faster MIP/CSS
pip install gurobipy
```

**For TEP with pymoo:** (still in development)
```bash
pip install pymoo pyomo
```
**Note:** Both `pymoo` (for outer optimization) and `pyomo` (for inner OPF subproblems) are required.

**For static image export (plotly):**
```bash
pip install kaleido
```

pyflow_acdc has callback capabilities and has been tested with the following pyomo linked solvers:

```bash

ipopt
conda install -c conda-forge ipopt

highs
pip install highspy

gurobi (requires external licensing)
pip install gurobipy


glpk
pip install glpk

cbc
conda install -c conda-forge coincbc

bonmin
conda install -c conda-forge coin-or-bonmin



```


**Note:** `ipopt` and `bonmin` are not available on PyPI and must be installed via conda-forge.

**For Bonmin (Linux only):**
```bash
# First install system package:
sudo apt update
sudo apt install coinor-libbonmin-dev

# Then install Python interface:
conda install -c conda-forge coin-or-bonmin
```

**For Dash:**
```bash
pip install dash
```
## Test

Run the test suite:

```bash
pyflow-acdc-test
```

**Test flags** (see also `docs/testing.rst` and `CONTRIBUTING.md`):

```bash
--quick         # Fast subset (run before opening a PR)
--docs          # Documentation literalinclude examples
--tep           # TEP tests only
--opf           # OPF tests only
--show-output   # Stream each case's output
```

**Coverage**:

```bash
pip install -e ".[tests]"
pytest pyflow_tests/ --cov=pyflow_acdc --cov-report=term-missing
```

CI uploads coverage to [Codecov](https://codecov.io/gh/CITCEA-UPC/pyflow_acdc) on each
push/PR to `main` (requires the `CODECOV_TOKEN` repository secret). Reports include
``pyflow_acdc`` package code (including ``example_grids`` factories); ``pyflow_tests/``
fixtures are excluded. Per-module reports and the coverage badge are maintained there.
## Documentation
Online documentation can be found at:

https://pyflow-acdc.readthedocs.io/

To build the latest documentation of a branch, build it locally.

To build the documentation:
```bash
cd docs
pip install -r requirements.txt
make html
```

**Note:** On Windows, you may need to use `make.bat html` or install `make` (e.g., via Chocolatey or WSL).

The documentation will be available in `docs/_build/html/index.html`
