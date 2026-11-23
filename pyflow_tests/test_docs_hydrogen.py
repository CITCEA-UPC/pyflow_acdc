"""Run hydrogen doc examples in doc_examples/hydrogen/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "hydrogen"


def test_docs_hydrogen():
    run_test()


def run_test():
    run_doc_examples(FOLDER, skip_on_import_error=True)
    print(f"OK {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
