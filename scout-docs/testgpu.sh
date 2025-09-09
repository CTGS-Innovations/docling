#!/bin/bash

echo "🖥️  Testing GPU Access in Docker..."
echo "=================================="
echo ""

echo "Test 1: Basic nvidia-smi in Docker"
echo "-----------------------------------"
if docker run --rm --gpus all ubuntu:22.04 nvidia-smi; then
    echo "✅ nvidia-smi works in Docker"
else
    echo "❌ nvidia-smi failed in Docker"
    exit 1
fi

echo ""
echo "Test 2: PyTorch CUDA Detection"
echo "------------------------------"
if docker run --rm --gpus all python:3.11-slim bash -c '
pip install torch --index-url https://download.pytorch.org/whl/cu121 > /dev/null 2>&1
python -c "
import torch
print(\"CUDA available:\", torch.cuda.is_available())
print(\"GPU count:\", torch.cuda.device_count())
if torch.cuda.is_available():
    print(\"GPU name:\", torch.cuda.get_device_name(0))
else:
    print(\"GPU name: None\")
"'; then
    echo "✅ PyTorch CUDA detection successful"
else
    echo "❌ PyTorch CUDA detection failed"
fi

echo ""
echo "Test 3: Check Docker GPU Configuration"
echo "-------------------------------------"
echo "Docker runtimes:"
docker info | grep -i runtime
echo ""
echo "NVIDIA runtime available:"
docker info | grep -i nvidia || echo "No NVIDIA runtime detected"

echo ""
echo "🎯 GPU Test Complete!"
echo "If all tests pass, GPU is working properly in Docker."