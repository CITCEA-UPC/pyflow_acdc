"""Run storage doc examples in doc_examples/storage/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "storage"


def test_docs_storage():
    run_test()


def run_test():
    run_doc_examples(FOLDER, skip_on_import_error=True)
    print(f"OK {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
