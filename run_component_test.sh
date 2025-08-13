#!/bin/bash

# Set PYTHONPATH to include the project root and all submodules
export PYTHONPATH="$(pwd):$(pwd)/EventBusClient:$(pwd)/libs:$(pwd)/testconfig"
# echo "PYTHONPATH is set to: $PYTHONPATH"
python --version

python test/component_test.py "$@"