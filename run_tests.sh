#!/usr/bin/bash
set -euo pipefail

echo "Checking types with mypy"
mypy .

echo "Checking other bugs with pylint"
pylint hun_law tests *.py

echo "Running all tests"
pytest --workers auto
