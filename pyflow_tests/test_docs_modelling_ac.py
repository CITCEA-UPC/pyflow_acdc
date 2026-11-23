"""Run all examples in doc_examples/modelling_ac/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "modelling_ac"


def test_docs_modelling_ac():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
