#!/bin/bash

# Ultra-Performance Setup Script
# ==============================

echo "🚀 MVP Hyper-Core Setup"
echo "======================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "✓ Python version: $python_version"

# Install minimal required dependencies
echo ""
echo "📦 Installing minimal dependencies..."
echo "-----------------------------------"

# Core requirement
pip install pymupdf --upgrade

# Optional performance boosters
echo ""
echo "📦 Installing optional performance boosters..."
pip install xxhash numba

# System optimizations
echo ""
echo "⚙️  System Optimizations"
echo "----------------------"

# Check if running as root for system optimizations
if [ "$EUID" -eq 0 ]; then 
    # Increase file descriptor limits
    echo "fs.file-max = 2097152" >> /etc/sysctl.conf
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    sysctl -p
    echo "✓ File descriptor limits increased"
    
    # CPU performance mode
    if command -v cpupower &> /dev/null; then
        cpupower frequency-set -g performance
        echo "✓ CPU set to performance mode"
    fi
else
    echo "⚠️  Run as root for system optimizations"
    echo "   sudo ./setup.sh"
fi

# Create ramdisk for ultra-fast I/O (optional)
echo ""
echo "💾 Optional: Create RAM disk for testing"
echo "---------------------------------------"
echo "To create a 1GB RAM disk:"
echo "  sudo mkdir -p /mnt/ramdisk"
echo "  sudo mount -t tmpfs -o size=1G tmpfs /mnt/ramdisk"
echo "  cp your_test_files.pdf /mnt/ramdisk/"
echo ""

# Test installation
echo "🧪 Testing installation..."
echo "------------------------"
python3 -c "import fitz; print(f'✓ PyMuPDF version: {fitz.version}')"

# Check for optional accelerators
python3 -c "import xxhash; print('✓ xxhash installed')" 2>/dev/null || echo "  ⚠️  xxhash not installed (optional)"
python3 -c "import numba; print('✓ numba installed')" 2>/dev/null || echo "  ⚠️  numba not installed (optional)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🏃 Quick start:"
echo "  ./mvp-hyper-core.py your_file.pdf"
echo "  ./benchmark.py --num-files 10"
echo ""
echo "🎯 Target: 1,000+ pages/second"