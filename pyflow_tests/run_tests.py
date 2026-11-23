import sys
from pathlib import Path
import importlib.util
from io import StringIO
import contextlib
from typing import Dict, List, Tuple
import time

from pyflow_tests.test_constants import (
    ALL_CASES,
    DOCS_CASES,
    IGNORED_WARNING_SNIPPETS,
    OPF_CASES,
    QUICK_CASES,
    TEP_CASES,
)

# Configuration
TEST_DIR = Path(__file__).parent

def run_test_case(case: str, show_output: bool = False) -> Tuple[bool, str, List[str], float]:

    """Run a test case and return (success, error_message, warnings, elapsed_time)."""
    if show_output:
        print(f"\nRunning test case: {case}")
        print("-" * 70)

    # Load the module
    module_path = TEST_DIR / case
    spec = importlib.util.spec_from_file_location(case[:-3], module_path)
    if spec is None or spec.loader is None:
        error_msg = f"Error: Could not load module {case}"
        print(error_msg)
        return False, error_msg, [], 0

    module = importlib.util.module_from_spec(spec)

    # Capture warnings
    captured_warnings = []

    try:
        if show_output:
            # Run the module directly to see all output
            spec.loader.exec_module(module)
            # Call the standardized test function
            start_time = time.perf_counter()
            module.run_test()
            elapsed_time = time.perf_counter() - start_time
        else:
            # Capture stdout to check for warning messages
            stdout_capture = StringIO()
            with contextlib.redirect_stdout(stdout_capture):
                spec.loader.exec_module(module)
                # Call the standardized test function
                start_time = time.perf_counter()
                module.run_test()
                elapsed_time = time.perf_counter() - start_time

            # Check stdout for explicit warning messages
            for line in stdout_capture.getvalue().split('\n'):
                if 'Warning' in line or 'warning' in line:
                    stripped = line.strip()
                    if any(snippet in stripped for snippet in IGNORED_WARNING_SNIPPETS):
                        continue
                    captured_warnings.append(stripped)

            stdout_content = stdout_capture.getvalue()
            doc_examples_passed = " doc examples passed" in stdout_content
            if not doc_examples_passed and (
                "is not installed" in stdout_content or "Skipped:" in stdout_content
            ):
                return False, "Dependency not available", captured_warnings, 0

        return True, "", captured_warnings, elapsed_time
    except Exception as e:
        error_msg = f"Error running {case}: {str(e)}"
        print(error_msg)
        return False, error_msg, captured_warnings, 0
    finally:
        if show_output:
            print("-" * 70)

def main():
    # Check command line arguments
    args = sys.argv[1:]
    show_output = "--show-output" in args
    quick_mode = "--quick" in args
    tep_mode = "--tep" in args
    opf_mode = "--opf" in args

    docs_mode = "--docs" in args

    # Choose which tests to run
    if quick_mode:
        CASES = QUICK_CASES
        print("Running quick tests (basic functionality only)")
    elif docs_mode:
        CASES = DOCS_CASES
        print("Running documentation example tests")
    elif tep_mode:
        CASES = TEP_CASES
        print("Running TEP tests")
    elif opf_mode:
        CASES = OPF_CASES
        print("Running OPF tests (solver-dependent)")
    else:
        CASES = ALL_CASES
        print("Running all tests")

    print(f"Running {len(CASES)} test cases")
    if show_output:
        print("Showing full output for each test case")
    print("-" * 70)

    results: Dict[str, Tuple[bool, str, List[str], float]] = {}

    for case in CASES:
        success, error_msg, warnings, elapsed_time = run_test_case(case, show_output)
        results[case] = (success, error_msg, warnings, elapsed_time)
        if not show_output:
            status = "✓ Passed" if success else "✗ Failed"
            if error_msg == "Dependency not available":
                status = "~ Skipped"
            print(f"{status} - {case} - {elapsed_time:.2f}s")
            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(f"  {warning}")

    print("-" * 70)

    # Print summary
    success_count = sum(1 for result in results.values() if result[0])
    print(f"Summary: {success_count}/{len(CASES)} tests passed")

    # Print detailed error report if any tests failed
    failed_tests = [(case, error, warnings, elapsed_time) for case, (success, error, warnings, elapsed_time) in results.items() if not success]
    if failed_tests:
        print("\nFailed Tests:")
        for case, error, warnings, elapsed_time in failed_tests:
            if error == "Dependency not available":
                continue
            print(f"\n{case}:")
            print(f"  {error}")
            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(f"  {warning}")
        print('------')
        print('Skipped tests:')
        for case, error, warnings, elapsed_time in failed_tests:
            if error != "Dependency not available":
                continue
            print(f"\n{case}:  {error}")
            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(f"  {warning}")

if __name__ == "__main__":
    main()
