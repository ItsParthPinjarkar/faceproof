#!/usr/bin/env bash
set -euo pipefail

echo "=== FaceProof API Build ==="

pip install -r requirements.txt

python -c "from solcx import install_solc; install_solc('0.8.24')" || true

echo "=== Build complete ==="
