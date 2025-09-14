#!/bin/bash
# MVP Hyper Pipeline Runner - Orchestrates the existing working sidecars
# =====================================================================

# Configuration
INPUT_DIR="${1:-~/projects/docling/cli/data}"
OUTPUT_BASE="${2:-output}"
CONFIG="${3:-mvp-hyper-config.yaml}"

echo "🚀 MVP Hyper Pipeline - Sidecar Orchestration"
echo "============================================="
echo "📂 Input: $INPUT_DIR"
echo "📂 Output: $OUTPUT_BASE"
echo ""

# Step 1: Convert to Markdown (if needed)
echo "📝 Step 1: Converting documents to markdown..."
MARKDOWN_OUTPUT="$OUTPUT_BASE/1-markdown"
mkdir -p "$MARKDOWN_OUTPUT"

# Use the EXISTING working mvp-hyper-core
python mvp-hyper-core.py "$INPUT_DIR" --output "$MARKDOWN_OUTPUT" --config "$CONFIG"

echo "✅ Markdown conversion complete"
echo ""

# Step 2: Tier 1 - Document Classification (Sidecar)
echo "🏷️ Step 2: Adding Tier 1 classification..."
TIER1_OUTPUT="$OUTPUT_BASE/2-tier1-classified"
mkdir -p "$TIER1_OUTPUT"

# Copy markdown files and add classification
for file in "$MARKDOWN_OUTPUT"/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        
        # Read content
        content=$(<"$file")
        
        # Run simple classification (CPU-only, fast)
        # This could call a simple Python classifier or use grep counts
        technical_count=$(echo "$content" | grep -io -E "algorithm|function|system|database|api|code" | wc -l)
        safety_count=$(echo "$content" | grep -io -E "safety|hazard|risk|osha|emergency|protection" | wc -l)
        business_count=$(echo "$content" | grep -io -E "business|company|market|customer|strategy|management" | wc -l)
        research_count=$(echo "$content" | grep -io -E "research|study|hypothesis|analysis|experiment|data" | wc -l)
        
        # Determine primary type
        max_count=$technical_count
        doc_type="technical"
        
        if [ $safety_count -gt $max_count ]; then
            max_count=$safety_count
            doc_type="safety"
        fi
        
        if [ $business_count -gt $max_count ]; then
            max_count=$business_count
            doc_type="business"
        fi
        
        if [ $research_count -gt $max_count ]; then
            max_count=$research_count
            doc_type="research"
        fi
        
        # Add classification to front matter
        echo "---" > "$TIER1_OUTPUT/$filename"
        echo "document_type: $doc_type" >> "$TIER1_OUTPUT/$filename"
        echo "classification_time: $(date +%s.%N)" >> "$TIER1_OUTPUT/$filename"
        echo "---" >> "$TIER1_OUTPUT/$filename"
        echo "" >> "$TIER1_OUTPUT/$filename"
        echo "$content" >> "$TIER1_OUTPUT/$filename"
    fi
done

echo "✅ Tier 1 classification complete"
echo ""

# Step 3: Tier 2 - Enhanced Tagging (Using existing mvp-hyper-tagger)
echo "🔖 Step 3: Adding Tier 2 domain-specific tags..."
TIER2_OUTPUT="$OUTPUT_BASE/3-tier2-tagged"
mkdir -p "$TIER2_OUTPUT"

# Use the EXISTING working mvp-hyper-tagger as a sidecar
python mvp-hyper-core.py "$TIER1_OUTPUT" --output "$TIER2_OUTPUT" --enable-tagging --config "$CONFIG"

echo "✅ Tier 2 tagging complete"
echo ""

# Step 4: Tier 3 - Semantic Extraction (Using existing mvp-hyper-semantic)
echo "🧠 Step 4: Extracting semantic facts..."
SEMANTIC_OUTPUT="$OUTPUT_BASE/4-semantic-facts"
mkdir -p "$SEMANTIC_OUTPUT"

# Use the EXISTING working mvp-hyper-semantic
python mvp-hyper-semantic.py "$TIER2_OUTPUT" --output "$SEMANTIC_OUTPUT"

echo "✅ Semantic extraction complete"
echo ""

echo "🎉 Pipeline Complete!"
echo "📊 Results:"
echo "  - Markdown files: $MARKDOWN_OUTPUT"
echo "  - Tier 1 classified: $TIER1_OUTPUT"
echo "  - Tier 2 tagged: $TIER2_OUTPUT"
echo "  - Semantic facts: $SEMANTIC_OUTPUT"