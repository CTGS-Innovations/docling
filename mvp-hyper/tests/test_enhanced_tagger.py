#!/usr/bin/env python3
"""Test the enhanced tagger on a single document."""

import sys
import importlib.util
from pathlib import Path

# Load the tagger module
import os
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level from tests/
spec = importlib.util.spec_from_file_location("mvp_hyper_tagger", os.path.join(current_dir, "core", "mvp-hyper-tagger.py"))
mvp_hyper_tagger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mvp_hyper_tagger)

MVPHyperTagger = mvp_hyper_tagger.MVPHyperTagger

def test_single_document(file_path: str):
    """Test enhanced tagger on a single document."""
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    # Read content
    content = path.read_text(encoding='utf-8')
    
    # Create tagger
    tagger = MVPHyperTagger(cache_enabled=False)
    
    # Tag document
    print(f"🏷️  Tagging {path.name}...")
    tags = tagger.tag_document(path, content)
    
    # Print results
    print("\n" + "="*60)
    print("ENHANCED TAGGER RESULTS")
    print("="*60)
    print(f"Document Types: {tags.document_types}")
    print(f"Domains: {tags.domains}")
    print(f"Keywords: {', '.join(tags.keywords[:10])}")
    print(f"Entities: {', '.join(tags.entities[:5])}")
    print(f"Topics: {', '.join(tags.topics)}")
    print(f"Technical Score: {tags.technical_score}")
    print(f"Confidence: {tags.confidence:.2f}")
    print(f"Processing Time: {tags.processing_time:.3f}s")
    print()
    
    # Enhanced fields
    if tags.measurements:
        print("MEASUREMENTS:")
        for measure_type, values in tags.measurements.items():
            print(f"  {measure_type}: {values}")
        print()
    
    if tags.time_references:
        print("TIME REFERENCES:")
        for time_type, values in tags.time_references.items():
            print(f"  {time_type}: {values}")
        print()
    
    if tags.regulatory_framework:
        print("REGULATORY FRAMEWORK:")
        for reg_type, values in tags.regulatory_framework.items():
            print(f"  {reg_type}: {values}")
        print()
    
    if tags.logical_structures:
        print("LOGICAL STRUCTURES:")
        for logic_type, values in tags.logical_structures.items():
            print(f"  {logic_type}: {values[:2]}")  # Show first 2
        print()
    
    if tags.stakeholder_roles:
        print(f"STAKEHOLDER ROLES: {', '.join(tags.stakeholder_roles)}")
        print()
    
    if tags.priority_fact_spans:
        print(f"PRIORITY FACT SPANS: {len(tags.priority_fact_spans)} high-value spans identified")
        for i, span in enumerate(tags.priority_fact_spans[:3]):  # Show first 3
            print(f"  {i+1}. {span['type']}: {span.get('preview', 'N/A')}")
        print()
    
    # Show enhanced markdown output
    print("ENHANCED MARKDOWN HEADER:")
    print("-" * 40)
    print(tagger.format_tags_as_markdown(tags))
    
    return tags

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_enhanced_tagger.py <file_path>")
        sys.exit(1)
    
    test_single_document(sys.argv[1])