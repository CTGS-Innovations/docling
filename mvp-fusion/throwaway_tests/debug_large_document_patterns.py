#!/usr/bin/env python3
"""
GOAL: Debug why measurement patterns fail on large documents but work on small ones
REASON: 13.9% success rate on 119KB document vs 100% on 6KB document
PROBLEM: Pattern boundary issues or timeouts causing failures at scale
"""

import sys
import os
import yaml
import time

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_large_document_patterns():
    """Debug pattern performance on large vs small documents"""
    print("🔍 DEBUGGING LARGE DOCUMENT PATTERN PERFORMANCE")
    print("=" * 60)
    
    # Load the large document
    large_doc_path = '/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(large_doc_path, 'r') as f:
        large_content = f.read()
    
    # Extract just the measurement section for focused testing
    measurement_section_start = large_content.find('### 9.4 Measurements (20 measurements)')
    measurement_section_end = large_content.find('### ', measurement_section_start + 1)
    if measurement_section_end == -1:
        measurement_section_end = large_content.find('---', measurement_section_start)
    
    measurement_section = large_content[measurement_section_start:measurement_section_end]
    
    print(f"📊 DOCUMENT ANALYSIS:")
    print(f"   Large document: {len(large_content):,} chars")
    print(f"   Measurement section: {len(measurement_section):,} chars")
    print()
    
    # Load config and test patterns
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test 1: Small measurement section
    print("🧪 TEST 1: MEASUREMENT SECTION ONLY")
    print("-" * 40)
    start_time = time.perf_counter()
    results_section = flpc_engine.extract_entities(measurement_section, 'complete')
    section_time = (time.perf_counter() - start_time) * 1000
    
    section_entities = results_section.get('entities', {})
    measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(section_entities.get(mtype, []))
        measurement_count += count
        if count > 0:
            print(f"   {mtype}: {count}")
    
    range_indicators = len(section_entities.get('RANGE_INDICATOR', []))
    print(f"   RANGE_INDICATOR: {range_indicators}")
    print(f"   Total measurements: {measurement_count}")
    print(f"   Processing time: {section_time:.1f}ms")
    print()
    
    # Test 2: Full large document
    print("🧪 TEST 2: FULL LARGE DOCUMENT")
    print("-" * 40)
    start_time = time.perf_counter()
    results_full = flpc_engine.extract_entities(large_content, 'complete')
    full_time = (time.perf_counter() - start_time) * 1000
    
    full_entities = results_full.get('entities', {})
    full_measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(full_entities.get(mtype, []))
        full_measurement_count += count
        if count > 0:
            print(f"   {mtype}: {count}")
    
    full_range_indicators = len(full_entities.get('RANGE_INDICATOR', []))
    print(f"   RANGE_INDICATOR: {full_range_indicators}")
    print(f"   Total measurements: {full_measurement_count}")
    print(f"   Processing time: {full_time:.1f}ms")
    print()
    
    # Test 3: Our small test for comparison
    print("🧪 TEST 3: SMALL TEST DOCUMENT")
    print("-" * 40)
    small_test = "Safety requirements: Handrail height 30-37 inches (76-94 cm), distance between 6 to 10 feet, weight capacity between 50 and 75 pounds, response time 15-30 minutes, temperature -20°F through 120°F"
    
    start_time = time.perf_counter()
    results_small = flpc_engine.extract_entities(small_test, 'complete')
    small_time = (time.perf_counter() - start_time) * 1000
    
    small_entities = results_small.get('entities', {})
    small_measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(small_entities.get(mtype, []))
        small_measurement_count += count
        if count > 0:
            print(f"   {mtype}: {count}")
            print(f"     Content: {small_entities.get(mtype, [])}")
    
    small_range_indicators = len(small_entities.get('RANGE_INDICATOR', []))
    print(f"   RANGE_INDICATOR: {small_range_indicators}")
    print(f"     Content: {small_entities.get('RANGE_INDICATOR', [])}")
    print(f"   Total measurements: {small_measurement_count}")
    print(f"   Processing time: {small_time:.1f}ms")
    print()
    
    # Performance comparison
    print("📊 PERFORMANCE COMPARISON:")
    print("-" * 40)
    print(f"Small text ({len(small_test)} chars):")
    print(f"   Measurements: {small_measurement_count}")
    print(f"   Range indicators: {small_range_indicators}")
    print(f"   Time: {small_time:.1f}ms")
    print()
    print(f"Measurement section ({len(measurement_section)} chars):")
    print(f"   Measurements: {measurement_count}")
    print(f"   Range indicators: {range_indicators}")
    print(f"   Time: {section_time:.1f}ms")
    print()
    print(f"Full document ({len(large_content)} chars):")
    print(f"   Measurements: {full_measurement_count}")
    print(f"   Range indicators: {full_range_indicators}")
    print(f"   Time: {full_time:.1f}ms")
    print()
    
    # Check for specific test case
    print("🎯 SPECIFIC TEST: '30-37 inches'")
    print("-" * 40)
    test_cases = [small_test, measurement_section, large_content]
    test_names = ["Small test", "Measurement section", "Full document"]
    
    for test_content, test_name in zip(test_cases, test_names):
        if '30-37 inches' in test_content:
            print(f"✅ '{test_name}' contains '30-37 inches'")
            # Check if FLPC detects it
            results = flpc_engine.extract_entities(test_content, 'complete')
            entities = results.get('entities', {})
            
            # Look for any measurements containing "37" or "inches"
            found_37_inches = False
            for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
                for measurement in entities.get(mtype, []):
                    if '37' in str(measurement) and 'inch' in str(measurement):
                        found_37_inches = True
                        print(f"   🎯 Found: {measurement} in {mtype}")
            
            if not found_37_inches:
                print(f"   ❌ '30-37 inches' NOT detected by FLPC in {test_name}")
        else:
            print(f"❌ '{test_name}' does NOT contain '30-37 inches'")

if __name__ == "__main__":
    debug_large_document_patterns()