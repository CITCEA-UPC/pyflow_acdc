"""Run doc examples in doc_examples/tep_pymoo/."""

from pyflow_tests._test_solver_deps import (
    pymoo_tep_missing_for_run_test,
    require_tep_pymoo,
)
from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "tep_pymoo"


def test_docs_tep_pymoo():
    require_tep_pymoo()
    run_test()


def run_test():
    if pymoo_tep_missing_for_run_test():
        return
    run_doc_examples(FOLDER, skip_on_import_error=True)
    print(f"OK {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
