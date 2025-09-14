#!/bin/bash

# Clean Output Script
# ==================
# Cleans all files in the output directory before each run

echo "🧹 Cleaning output directory..."

OUTPUT_DIR="./output"

if [ -d "$OUTPUT_DIR" ]; then
    # Count files before cleaning
    FILE_COUNT=$(find "$OUTPUT_DIR" -type f | wc -l)
    
    if [ "$FILE_COUNT" -gt 0 ]; then
        echo "   Removing $FILE_COUNT files from $OUTPUT_DIR/"
        rm -rf "$OUTPUT_DIR"/*
        echo "   ✅ Output directory cleaned"
    else
        echo "   ✅ Output directory already empty"
    fi
else
    echo "   📁 Creating output directory"
    mkdir -p "$OUTPUT_DIR"
    echo "   ✅ Output directory created"
fi

echo "   Ready for new processing run!"
echo ""