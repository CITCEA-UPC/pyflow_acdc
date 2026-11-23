"""Run all examples in doc_examples/plotting/."""


from pyflow_tests.run_doc_examples import run_doc_examples

FOLDER = "plotting"


def test_docs_plotting():
    run_test()


def run_test():
    run_doc_examples(FOLDER, skip_on_import_error=True)
    print(f"✓ {FOLDER} doc examples passed")


if __name__ == "__main__":
    run_test()
