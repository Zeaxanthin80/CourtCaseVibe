#!/bin/bash
# Script to run tests with proper Python path

# Get the absolute path to the backend directory
BACKEND_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Add backend directory to PYTHONPATH
export PYTHONPATH=$BACKEND_DIR:$PYTHONPATH

# Run the tests
python tests/run_tests.py

