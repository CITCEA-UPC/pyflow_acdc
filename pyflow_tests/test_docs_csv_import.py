"""Run all examples in doc_examples/csv_import/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "csv_import"


def test_docs_csv_import():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
