#!/bin/bash
# Compress the "fusion" folder using multiple methods and compare sizes

INPUT_DIR="fusion"
OUTPUT_DIR="compressed_outputs"

# Make sure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "Compressing folder: $INPUT_DIR"
echo "Outputs will be stored in: $OUTPUT_DIR"
echo

# Tar + gzip
tar -czf "$OUTPUT_DIR/fusion.tar.gz" "$INPUT_DIR"

# Tar + bzip2
tar -cjf "$OUTPUT_DIR/fusion.tar.bz2" "$INPUT_DIR"

# Tar + xz
tar -cJf "$OUTPUT_DIR/fusion.tar.xz" "$INPUT_DIR"

# Tar + zstd (if installed)
if command -v zstd >/dev/null 2>&1; then
    tar -cf - "$INPUT_DIR" | zstd -q -o "$OUTPUT_DIR/fusion.tar.zst"
else
    echo "zstd not installed, skipping .zst compression"
fi

echo
echo "Compression complete. File sizes:"
ls -lh "$OUTPUT_DIR"

