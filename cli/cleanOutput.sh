#!/bin/bash

# Clean Output Script - Remove all work from output folders
# This script cleans up all generated output files from testing and processing

echo "🧹 Cleaning output directories..."

# Clean test extracted images
if [ -d "tests/extracted_images" ]; then
    echo "📁 Cleaning tests/extracted_images..."
    rm -rf tests/extracted_images/*.png
    rm -rf tests/extracted_images/*.json
    echo "   ✅ Cleaned extracted images"
fi

# Clean main output directory if it exists
if [ -d "output" ]; then
    echo "📁 Cleaning output directory..."
    rm -rf output/*
    echo "   ✅ Cleaned output directory"
fi

# Clean VLM processing logs
if [ -f "vlm_processing.log" ]; then
    echo "📄 Removing VLM processing log..."
    rm -f vlm_processing.log
    echo "   ✅ Removed VLM log"
fi

# Clean any .md output files in current directory
echo "📄 Cleaning markdown output files..."
rm -f *.md 2>/dev/null || true
echo "   ✅ Cleaned markdown files"

# Clean any JSON output files in current directory
echo "📄 Cleaning JSON output files..."
rm -f *_output.json 2>/dev/null || true
rm -f *_results.json 2>/dev/null || true
echo "   ✅ Cleaned JSON files"

# Clean docling cache if needed
if [ -d ".docling-cache" ]; then
    echo "📁 Cleaning docling cache..."
    rm -rf .docling-cache/*
    echo "   ✅ Cleaned docling cache"
fi

# Clean temp directories
if [ -d "temp" ]; then
    echo "📁 Cleaning temp directory..."
    rm -rf temp/*
    echo "   ✅ Cleaned temp directory"
fi

echo ""
echo "✅ Output cleanup complete!"
echo ""
echo "Directories cleaned:"
echo "  • tests/extracted_images/"
echo "  • output/"
echo "  • .docling-cache/"
echo "  • temp/"
echo ""
echo "Files cleaned:"
echo "  • *.md (output markdowns)"
echo "  • *_output.json, *_results.json"
echo "  • vlm_processing.log"