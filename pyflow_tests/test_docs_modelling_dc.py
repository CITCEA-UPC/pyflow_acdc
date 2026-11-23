"""Run all examples in doc_examples/modelling_dc/."""

from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "modelling_dc"


def test_docs_modelling_dc():
    run_test()


def run_test():
    run_doc_examples(FOLDER)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
