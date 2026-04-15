<img src="docs/images/logo_dark.svg" align="right" width="200px">

# PyFlow ACDC
A python-based tool for the design and analysis of hybrid AC/DC grids


PyFlow ACDC is a program worked on by ADOreD Project 

This project has received funding from the European Union’s  Horizon Europe 
Research and Innovation programme under the Marie Skłodowska-Curie grant 
agreement No 101073554.

## Important

This project is experimental and under active development. Issue reports and contributions are very welcome.


## Citation

If you use this package in your research, please cite the appropriate publication(s):

**General usage:**
```
B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt, 
"An Optimal Power Flow Tool for AC/DC Systems, Applied to the Analysis of the 
North Sea Grid for Offshore Wind Integration," in IEEE Transactions on Power Systems, 
vol. 40, no. 5, pp. 4278-4291, Sept. 2025, doi: 10.1109/TPWRS.2025.3533889.
```

**For market integration into optimal power flow:**
```
Valerio B C, Lacerda V A, Cheah-Ma˜ne M, Gebraad P and Gomis-Bellmunt O 2025
Optimizing offshore wind integration through multi-terminal dc grids: a market-based opf
framework for the north sea interconnectors IET Conference Proceedings 2025(6) 150–155
URL https://digital-library.theiet.org/doi/abs/10.1049/icp.2025.1198
```

**For transmission expansion planning:**
```
B. C. Valerio, M. Cheah-Mane, V. A. Lacerda, P. Gebraad, and O. Gomis-
Bellmunt, “Transmission expansion planning for hybrid AC/DC grids using
a mixed-integer non-linear programming approach,” International Journal of
Electrical Power & Energy Systems, vol. 174, p. 111459, 2026. [Online]. Available:
https://www.sciencedirect.com/science/article/pii/S0142061525010075 
```

**For array optimization:**
```
B. C. Valerio, P. M. Gebraad, M. Cheah-Mane, V. Lacerda, and O. Gomis-
Bellmunt, “Strategies for wind park inter-array optimisation through mixed in-
teger linear programming,” in Proceedings of the TORQUE 2026 Conference,
2026, to be published in Journal of Physics: Conference Series [under review].

```


## Installation

### Basic Installation

Install from PyPI:
```bash
pip install pyflow-acdc
```

**Requirements:** Python 3.10 or higher

### For Users
To run examples, download the folder to your repository including the csv folders.

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
pip install pyflow-acdc[Dash]         # For Dash web applications
pip install pyflow-acdc[Array_OPT]    # For array optimization (ortools, pyomo)
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

**For Array Optimization:**
```bash
pip install ortools pyomo
pip install highspy  # Optional: for HiGHS solver
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

**Test Flags:**
```bash
--quick         # Quick tests only
--tep           # TEP tests only
--opf           # OPF tests only
--show-output    # All tests with output
```
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
