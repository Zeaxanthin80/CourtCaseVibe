#!/usr/bin/env python
"""
Test runner for CourtCaseVibe tests
"""
import unittest
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests and return the result"""
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # Discover and run the tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(test_dir), pattern="test_*.py")
    
    # Run the tests with a text test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if successful, 1 if there were failures or errors
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
