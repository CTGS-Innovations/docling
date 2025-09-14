#!/bin/bash

# Docker Resource-Constrained Performance Test
# ============================================
# Simulates deployment with 1 CPU core, 1GB RAM

echo "🐳 DOCKER RESOURCE-CONSTRAINED TEST"
echo "==================================="
echo "Target: 1 CPU core, 1GB RAM"
echo ""

# Clean previous output
./clean.sh

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t mvp-hyper:test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

# Run with resource constraints
echo ""
echo "🚀 Running with resource constraints:"
echo "   • CPU: 1.0 core"
echo "   • Memory: 1GB limit"
echo "   • Config: docker-config.yaml"
echo ""

# Use docker run with explicit resource limits
docker run --rm \
    --cpus="1.0" \
    --memory="1g" \
    --memory-swap="1g" \
    -v "$(pwd)/output:/app/output" \
    -v "$(pwd)/docker-config.yaml:/app/config.yaml" \
    -v "$HOME/projects/docling/cli/data:/app/data:ro" \
    -v "$HOME/projects/docling/cli/data_complex:/app/data_complex:ro" \
    -v "$HOME/projects/docling/cli/data_osha:/app/data_osha:ro" \
    mvp-hyper:test python mvp-hyper-core.py

echo ""
echo "🏁 Docker test complete!"
echo ""
echo "📊 Compare results:"
echo "  Native (current):    Your recent test results"
echo "  Docker (1 core/1GB): Results above"
echo ""
echo "📁 Output files saved to: ./output/"