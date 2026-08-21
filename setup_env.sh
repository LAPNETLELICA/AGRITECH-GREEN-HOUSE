#!/usr/bin/env bash
# Script to set up local simulation environment for Person A MicroPython project

set -e

echo "============================================================"
echo " Setting up AGRITECH GREENHOUSE - Person A Local Simulation"
echo "============================================================"

# Ensure script is run from project root
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$ROOT_DIR"

# Make simulation script executable
chmod +x sim/run_simulation.py

echo "[1/3] Verifying Python installation..."
python3 --version

echo "[2/3] Running Automated Unit Tests..."
python3 -m unittest tests/test_firmware.py -v

echo "[3/3] Environment Ready!"
echo ""
echo "To launch the interactive Person A Local Simulation Environment, run:"
echo "  python3 sim/run_simulation.py"
echo "============================================================"
