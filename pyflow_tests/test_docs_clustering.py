"""Run all examples in doc_examples/clustering/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "clustering"


def test_docs_clustering():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
