#!/usr/bin/env bash
set -euo pipefail

echo "=== FaceProof API Build ==="

# Install Python dependencies
pip install -r requirements.txt

# Pre-download InsightFace model so it's available at runtime
python -c "
import insightface
import os
model_dir = os.path.expanduser('~/.insightface/models')
os.makedirs(model_dir, exist_ok=True)
print('Pre-downloading InsightFace buffalo_l model...')
app = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print('Model ready.')
" || echo "WARNING: Model pre-download failed, will try at runtime"

# Install Solidity compiler for py-solc-x
python -c "from solcx import install_solc; install_solc('0.8.24')" || true

echo "=== Build complete ==="
