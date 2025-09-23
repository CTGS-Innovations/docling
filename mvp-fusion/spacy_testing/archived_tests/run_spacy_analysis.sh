#!/bin/bash
# Run spaCy Complete Analysis Script
# This will analyze ENTITY_EXTRACTION_TXT_DOCUMENT.md and generate all outputs

echo "🚀 Starting spaCy Complete Analysis..."
echo "=================================="
echo ""

# Navigate to mvp-fusion directory
cd /home/corey/projects/docling/mvp-fusion

# Activate the virtual environment
source .venv-clean/bin/activate

# Run the analysis
python spacy_test_outputs/complete_spacy_analysis_TMP.py

echo ""
echo "✅ Analysis complete! Check the output files:"
echo "   - raw_entities.yaml/json"
echo "   - normalized_entities.yaml/json"  
echo "   - semantic_rules.yaml/json"
echo "   - relationships.yaml/json"
echo "   - linguistics.yaml/json"
echo "   - performance.yaml/json"
echo "   - complete_results.json"
echo "   - analysis_report.md"