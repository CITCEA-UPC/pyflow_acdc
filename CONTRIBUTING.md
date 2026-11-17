# Contributing to pyflow-acdc

Thanks for your interest in contributing! This project is experimental and
under active development — issue reports and pull requests are very welcome.

## Development setup

```bash
git clone https://github.com/CITCEA-UPC/pyflow_acdc.git
cd pyflow_acdc
pip install -e .
```

Requires **Python 3.10+**. Package version is set in `pyproject.toml`
(this branch is **0.7.0**). Install the optional extras you need (see the
README for the full list), e.g.:

```bash
pip install -e ".[OPF]"            # pyomo for optimal power flow
pip install -e ".[SOCP]"           # cvxpy for sparse SOCP
pip install -e ".[LINEAR_ARRAY]"  # ortools + highspy for array MIP/CSS
pip install -e ".[tests]"          # pytest + pytest-cov
pip install -e ".[All]"        # everything except gurobipy (needs a license)
```

Solvers such as `ipopt` / `bonmin` are not on PyPI and must come from
conda-forge — see the README "Installation" section.

## Running the tests

The test runner is exposed as a console script and as a module:

```bash
pyflow-acdc-test                 # full suite
pyflow-acdc-test --quick         # fast subset (basic functionality)
pyflow-acdc-test --opf           # solver-dependent OPF tests
pyflow-acdc-test --tep           # transmission-expansion tests
pyflow-acdc-test --show-output   # stream each case's output

# equivalently:
python -m pyflow_tests.run_tests --quick
```

Tests that require an unavailable optional dependency are reported as
**Skipped**, not failed. Please make sure `--quick` passes before opening a
PR, and run the relevant `--opf` / `--tep` subset if you touched those areas.

### Do not weaken tests to hide bugs

If a test fails because product code is wrong, **fix the product code**. Do
**not** change, stub around, skip, or delete the test just to make the suite
pass. Tests are the contract; green must mean the behaviour is correct.

Updating a test is only appropriate when the **intended behaviour** itself
changed (API redesign, new requirement) and the PR documents that change.
Adapting fixtures or assertions to paper over a bug is not allowed.

When adding a new test case, add the file to the appropriate list
(`ALL_CASES`, `QUICK_CASES`, `OPF_CASES`, `TEP_CASES`, `DOCS_CASES`) in
`pyflow_tests/test_constants.py`, and expose a top-level `run_test()` function in
the case module.

## Test coverage

CI uploads pytest coverage to [Codecov](https://codecov.io/gh/CITCEA-UPC/pyflow_acdc)
on each push/PR to `main` (`.github/workflows/pr-tests.yml`, `coverage` job).
The repository must have a `CODECOV_TOKEN` Actions secret. Per-module reports
and the README coverage badge are maintained on Codecov.

To inspect coverage locally:

```bash
pytest pyflow_tests/ --cov=pyflow_acdc --cov-report=term-missing
```

## Coding conventions

- **New code uses `snake_case`** for functions and variables. Several existing
  public names are mixed-case for backward compatibility; do not rename them
  without a deprecation alias.
- **Centralise closed-vocabulary strings** in `pyflow_acdc/constants.py` as
  `(str, Enum)` members rather than scattering string literals. Use the enum
  member in comparisons (typo-safe) and `.value` for stored attributes / dict
  keys (preserves serialization and display).
- **Prefer fail-fast over silent fallbacks**: raise clear errors on invalid
  input instead of masking problems.
- **Keep changes simple and local**; avoid introducing new helper/abstraction
  layers unless reuse clearly justifies it.
- **Optional dependencies** must be guarded with `try/except ImportError` and a
  feature flag, matching the pattern in `__init__.py`.
- **Public API**: each module defines `__all__`. If you add a public symbol,
  add it to the module's `__all__` (and to `__init__.py` if it should be part
  of the top-level `pyflow_acdc` namespace).
- **Docstrings** use the NumPy style (the docs build with
  `sphinx.ext.napoleon`): one-line purpose, then `Parameters` / `Returns` /
  `Raises` / side-effects as relevant.

See `ARCHITECTURE.md` for module responsibilities and the dependency
layering.

## Documentation

```bash
cd docs
pip install -r requirements.txt
make html      # or make.bat html on Windows
```

Output is written to `docs/_build/html/index.html`.

## Pull requests

1. Create a feature branch off `main`.
2. Keep PRs focused; describe the motivation ("why") in the description.
3. Ensure tests pass and add/adjust tests for behavioural changes. If a test
   fails due to a bug, fix the bug — never weaken the test to get green (see
   **Do not weaken tests to hide bugs** above).
4. To merge into `main`, contact the repository owner.
