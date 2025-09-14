#!/usr/bin/env python3
"""Test the enhanced semantic extractor on a single document."""

import sys
import importlib.util
from pathlib import Path
import json

# Load the semantic extractor module
import os
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level from tests/
spec = importlib.util.spec_from_file_location("mvp_hyper_semantic", os.path.join(current_dir, "core", "mvp-hyper-semantic.py"))
mvp_hyper_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mvp_hyper_semantic)

MVPHyperSemanticExtractor = mvp_hyper_semantic.MVPHyperSemanticExtractor

def test_semantic_extraction(file_path: str):
    """Test enhanced semantic extraction on a single document."""
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    # Read content
    content = path.read_text(encoding='utf-8')
    
    # Create extractor with domain extraction enabled
    extractor = MVPHyperSemanticExtractor(
        enable_spacy=False,  # Skip for speed
        enable_domain_extraction=True
    )
    
    # Extract semantic metadata
    print(f"🧠 Extracting semantic metadata from {path.name}...")
    metadata = extractor.extract_semantic_metadata(path, content)
    
    # Print results
    print("\n" + "="*60)
    print("ENHANCED SEMANTIC EXTRACTION RESULTS")
    print("="*60)
    
    # Processing stats
    print(f"Processing Time: {metadata.processing_time:.3f}s")
    print(f"Extraction Stats: {metadata.extraction_stats}")
    print()
    
    # Existing tagger integration
    if metadata.existing_tagger_metadata:
        print("TAGGER INTEGRATION:")
        etm = metadata.existing_tagger_metadata
        print(f"  Used tagger data: Document types: {etm.document_types}")
        print(f"  Stakeholder roles: {etm.stakeholder_roles}")
        print(f"  Priority spans: {etm.priority_fact_spans}")
        print()
    
    # Two-tier results
    print("TWO-TIER EXTRACTION RESULTS:")
    if metadata.core_facts:
        print(f"  Core Facts: {len(metadata.core_facts)}")
        print("  Sample Core Facts:")
        for i, fact in enumerate(metadata.core_facts[:3]):
            enhanced = " [ENHANCED]" if fact.get('enhanced_by_tagger') else ""
            print(f"    {i+1}. {fact['type']}: {fact['subject']} -> {fact['predicate']} -> {str(fact.get('object', fact.get('value', 'N/A')))[:80]}...{enhanced}")
        print()
    
    if metadata.domain_facts:
        domain_name = metadata.domain_classification.get('domain', 'unknown')
        confidence = metadata.domain_classification.get('confidence', 0.0)
        print(f"  Domain Facts: {len(metadata.domain_facts)} (Domain: {domain_name}, Confidence: {confidence:.2f})")
        print("  Sample Domain Facts:")
        for i, fact in enumerate(metadata.domain_facts[:3]):
            print(f"    {i+1}. {fact.get('fact_type', 'unknown')}: {str(fact.get('subject', 'N/A'))} -> {str(fact.get('predicate', 'N/A'))} -> {str(fact.get('object', fact.get('value', 'N/A')))[:80]}...")
        print()
    
    # Legacy extraction for comparison
    print("LEGACY EXTRACTION (for comparison):")
    print(f"  Legacy Facts: {len(metadata.facts)}")
    print(f"  Legacy Entities: {len(metadata.entities)}")
    print("  Sample Legacy Facts:")
    for i, fact in enumerate(metadata.facts[:3]):
        print(f"    {i+1}. {fact.subject} -> {fact.predicate} -> {str(fact.value)[:80]}...")
    print()
    
    # Performance calculation
    words = len(content.split())
    pages = words // 250 or 1
    pages_per_sec = pages / metadata.processing_time if metadata.processing_time > 0 else 0
    print(f"PERFORMANCE: {pages_per_sec:.1f} pages/sec ({words} words, {pages} pages)")
    
    return metadata

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_enhanced_semantic.py <file_path>")
        sys.exit(1)
    
    test_semantic_extraction(sys.argv[1])