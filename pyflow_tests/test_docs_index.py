"""Run all examples in doc_examples/index/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "index"


def test_docs_index():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
