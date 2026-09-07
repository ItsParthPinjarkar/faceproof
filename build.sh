#!/usr/bin/env bash
set -euo pipefail

echo "=== FaceProof API Build ==="

# Install Python dependencies
pip install -r requirements.txt

# Install Solidity compiler for py-solc-x
python -c "from solcx import install_solc; install_solc('0.8.24')" || true

echo "=== Build complete ==="
