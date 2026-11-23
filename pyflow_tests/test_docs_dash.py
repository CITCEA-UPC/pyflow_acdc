"""Run all examples in doc_examples/dash/."""

from pyflow_tests._test_solver_deps import (
    dash_missing_for_run_test,
    require_dash,
)
from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "dash"


def test_docs_dash():
    require_dash()
    run_test()


def run_test():
    if dash_missing_for_run_test():
        return
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
