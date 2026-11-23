"""Run all examples in doc_examples/ts/."""

from pyflow_tests._test_solver_deps import (
    pyomo_missing_for_run_test,
    require_pyomo,
)
from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "ts"


def test_docs_ts():
    require_pyomo()
    run_test()


def run_test():
    if pyomo_missing_for_run_test():
        return
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
