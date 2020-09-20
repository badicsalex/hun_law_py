#!/usr/bin/bash
set -euo pipefail

./run_static_analysis.sh

echo "Running all tests"
pytest --workers auto
