"""Run all examples in doc_examples/results/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "results"


def test_docs_results():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
