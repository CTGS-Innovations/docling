#!/bin/bash

# Docling Performance Benchmark Runner
# Optimized for 80% GPU/CPU utilization with comprehensive logging

set -e  # Exit on any error

echo "🚀 DOCLING ULTRA-FAST PERFORMANCE BENCHMARK"
echo "=============================================="
echo "Timestamp: $(date)"
echo "Target: 80% GPU/CPU utilization for maximum throughput"
echo "Hardware: RTX 3090 GPU acceleration"
echo ""

# Check if we're in the correct directory
if [ ! -d "./data" ]; then
    echo "❌ Error: Please run this script from the /cli directory"
    echo "   Expected: /home/corey/projects/docling/cli/"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected"
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

# Verify docling is installed
if ! command -v docling &> /dev/null; then
    echo "❌ Error: docling not found in PATH"
    echo "   Please ensure docling is installed in the virtual environment"
    exit 1
fi

# Check GPU availability
echo "🔍 Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "✅ GPU detected and ready"
else
    echo "⚠️  No GPU detected - will use CPU only"
fi

echo ""
echo "📊 Starting performance benchmark..."
echo "📝 Live progress will be logged to benchmark.log"
echo "📁 Results will be saved to timestamped run directory"
echo ""

# Run the performance benchmark
python3 performance_benchmark.py

# Check if benchmark completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Benchmark completed successfully!"
    echo ""
    echo "📊 Results available in:"
    echo "   📂 ./output/latest/          (symlink to latest run)"
    echo "   📄 ./output/latest/PERFORMANCE_REPORT.md"
    echo "   📊 ./output/latest/performance_results.json"
    echo "   📝 ./output/latest/benchmark.log"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Review the performance report"
    echo "   2. Analyze GPU utilization efficiency"
    echo "   3. Optimize configurations for production"
    
    # Show quick summary if report exists
    if [ -f "./output/latest/PERFORMANCE_REPORT.md" ]; then
        echo ""
        echo "📋 Quick Summary:"
        grep -E "Overall Throughput|Enterprise Capacity|GPU" ./output/latest/PERFORMANCE_REPORT.md | head -3
    fi
else
    echo ""
    echo "❌ Benchmark failed!"
    echo "📝 Check benchmark.log for detailed error information"
    exit 1
fi