#!/usr/bin/env python3
"""Simple test runner for the refactored components."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print("STDOUT:", result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all tests and checks."""
    print("DocTR Process - Refactored Components Test Suite")
    
    all_passed = True
    
    # Run ruff linting
    if not run_command(["python", "-m", "ruff", "check", "src/"], "Ruff linting"):
        all_passed = False
    
    # Run ruff formatting check
    if not run_command(["python", "-m", "ruff", "format", "--check", "src/"], "Ruff formatting"):
        all_passed = False
    
    # Run pytest on new tests
    test_files = [
        "tests/test_io.py",
        "tests/test_extract.py", 
        "tests/test_parse.py",
        "tests/test_refactor_smoke.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            if not run_command(["python", "-m", "pytest", test_file, "-v"], f"Tests: {test_file}"):
                all_passed = False
    
    # Run smoke test
    if not run_command(["python", "-m", "pytest", "tests/test_smoke.py", "-v"], "Original smoke tests"):
        all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests and checks PASSED!")
        return 0
    else:
        print("💥 Some tests or checks FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())