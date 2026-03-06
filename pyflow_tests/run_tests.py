import sys
from pathlib import Path
import importlib.util
from io import StringIO
import contextlib
from typing import Dict, List
import warnings
import re
import time

# Configuration
TEST_DIR = Path(__file__).parent

# List of test cases to run (in order)
ALL_CASES = [
    # Documentation tests
    'test_docs_basic_grid_creation.py',
    'test_docs_add_components.py',
    'test_docs_power_flow.py',
    'test_docs_opf_quick.py',
    'test_docs_opf_detailed.py',
    
    #Power Flow
    'grid_creation.py',
    'CigreB4_PF.py',

    #OPF
    'DC_OPF.py',
    'CigreB4_OPF.py',
    'case39ac_OPF.py',
    'case39acdc_OPF.py',
    'case24_3zones_acdc_OPF.py',
   
    #loading matlab files
    'matlab_loader.py',
    #folium
    'folium_test.py',
    
    #Transmission Expansion
    'case24_OPF.py',
    #DC
    'case6_TEP_DC.py',
    #AC
    'case24_TEP.py',
    #REC
    'case24_REC.py',
    #CT
    'array_sizing.py',
    #time series and dash
    'ts_dash.py',
    #wind farm array
    'sequential_array.py',
    'sequential_array_ortools.py'
]

# Quick tests (basic functionality only)
QUICK_CASES = [
    'test_docs_basic_grid_creation.py',
    'test_docs_add_components.py',
    'test_docs_power_flow.py',
    'grid_creation.py',
    'CigreB4_PF.py',
    'matlab_loader.py',
]

TEP_CASES = [
    'case24_OPF.py',
    'case6_TEP_DC.py',
    'case24_TEP.py',
    'case24_REC.py',
    'array_sizing.py',
]

def run_test_case(case: str, show_output: bool = False) -> tuple[bool, str, List[str]]:
    
    """Run a test case and return (success, error_message, warnings)."""
    if show_output:
        print(f"\nRunning test case: {case}")
        print("-" * 70)
    
    # Load the module
    module_path = TEST_DIR / case
    spec = importlib.util.spec_from_file_location(case[:-3], module_path)
    if spec is None or spec.loader is None:
        error_msg = f"Error: Could not load module {case}"
        print(error_msg)
        return False, error_msg, []
        
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
                    captured_warnings.append(line.strip())
            
            stdout_content = stdout_capture.getvalue()
            if 'is not installed' in stdout_content or 'not available' in stdout_content:
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
    
    # Choose which tests to run
    if quick_mode:
        CASES = QUICK_CASES
        print("Running quick tests (basic functionality only)")
    
    elif tep_mode:
        CASES = TEP_CASES
        print("Running TEP tests")
    else:
        CASES = ALL_CASES
        print("Running all tests")
    
    print(f"Running {len(CASES)} test cases")
    if show_output:
        print("Showing full output for each test case")
    print("-" * 70)
    
    results: Dict[str, tuple[bool, str, List[str]]] = {}
    
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
