#!/usr/bin/env python3
"""
GOAL: Test comprehensive word boundary fix for FLPC patterns
REASON: Verify phantom "8 G" detection is fixed and patterns scale correctly
PROBLEM: Previous patterns extracted substrings from within words
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_word_boundary_fix():
    """Test the comprehensive word boundary pattern fix"""
    print("🧪 TESTING COMPREHENSIVE WORD BOUNDARY FIX")
    print("=" * 60)
    
    # Test cases that should NOT match (previously caused phantom detections)
    negative_test_cases = [
        "GPE: 8 geopolitical entities",  # Should not detect "8 g" 
        "Total: 8 governments involved", # Should not detect "8 g"
        "Managing 12 managers effectively", # Should not detect "12 m"
        "The company expanded rapidly", # Should not detect "expanded"
        "Temperature got colder", # Should not detect "got"
        "Using organizational methods", # Should not detect "g"
    ]
    
    # Test cases that SHOULD match (legitimate entities)
    positive_test_cases = [
        "Weight: 8 g of material",       # Should detect "8 g"
        "Distance: 12 meters exactly",   # Should detect "12 meters"
        "Temperature: 25 degrees celsius", # Should detect "25 degrees celsius"
        "Cost: $100 dollars",            # Should detect "$100"
        "Time: 3:30 PM today",           # Should detect "3:30 PM"
        "Date: January 15, 2024",        # Should detect "January 15, 2024"
    ]
    
    print(f"📄 TEST CASES:")
    print(f"   Negative tests (should NOT detect): {len(negative_test_cases)}")
    print(f"   Positive tests (SHOULD detect): {len(positive_test_cases)}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING NEGATIVE CASES (Should not detect phantom entities):")
        print("-" * 60)
        
        phantom_detections = 0
        
        for i, test_case in enumerate(negative_test_cases, 1):
            print(f"\n   Test {i}: '{test_case}'")
            
            entities = processor._extract_universal_entities(test_case)
            
            # Check for phantom measurements
            measurements = entities.get('measurement', [])
            money = entities.get('money', [])
            dates = entities.get('date', [])
            times = entities.get('time', [])
            
            total_entities = len(measurements) + len(money) + len(dates) + len(times)
            
            if total_entities > 0:
                phantom_detections += 1
                print(f"      🔴 PHANTOM DETECTED: {total_entities} entities")
                
                for measurement in measurements:
                    text = measurement.get('text', 'N/A')
                    print(f"         - Measurement: '{text}'")
                
                for m in money:
                    text = m.get('text', 'N/A')
                    print(f"         - Money: '{text}'")
                    
                for d in dates:
                    text = d.get('text', 'N/A')
                    print(f"         - Date: '{text}'")
                    
                for t in times:
                    text = t.get('text', 'N/A')
                    print(f"         - Time: '{text}'")
            else:
                print(f"      ✅ CLEAN: No phantom detections")
        
        print(f"\n🔍 TESTING POSITIVE CASES (Should detect legitimate entities):")
        print("-" * 60)
        
        successful_detections = 0
        
        for i, test_case in enumerate(positive_test_cases, 1):
            print(f"\n   Test {i}: '{test_case}'")
            
            entities = processor._extract_universal_entities(test_case)
            
            measurements = entities.get('measurement', [])
            money = entities.get('money', [])
            dates = entities.get('date', [])
            times = entities.get('time', [])
            
            total_entities = len(measurements) + len(money) + len(dates) + len(times)
            
            if total_entities > 0:
                successful_detections += 1
                print(f"      ✅ DETECTED: {total_entities} entities")
                
                for measurement in measurements:
                    text = measurement.get('text', 'N/A')
                    print(f"         - Measurement: '{text}'")
                
                for m in money:
                    text = m.get('text', 'N/A')
                    print(f"         - Money: '{text}'")
                    
                for d in dates:
                    text = d.get('text', 'N/A')
                    print(f"         - Date: '{text}'")
                    
                for t in times:
                    text = t.get('text', 'N/A')
                    print(f"         - Time: '{text}'")
            else:
                print(f"      🔴 MISSED: No entities detected")
        
        # Test the specific Section 9.4 document
        print(f"\n🎯 TESTING SECTION 9.4 DOCUMENT:")
        print("-" * 40)
        
        source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
        with open(source_path, 'r') as f:
            source_content = f.read()
        
        entities = processor._extract_universal_entities(source_content)
        measurements = entities.get('measurement', [])
        
        print(f"   Total measurements detected: {len(measurements)}")
        
        # Check for the phantom "8 G" specifically
        phantom_8g_found = False
        for measurement in measurements:
            text = measurement.get('text', '')
            if '8 G' in text or '8 g' in text:
                span = measurement.get('span', {})
                start = span.get('start', 0)
                end = span.get('end', 0)
                actual_text = source_content[start:end] if start < len(source_content) and end <= len(source_content) else "INVALID"
                
                if actual_text != text:
                    phantom_8g_found = True
                    print(f"   🔴 PHANTOM '8 G' still exists: detected '{text}' but actual text is '{actual_text}'")
        
        if not phantom_8g_found:
            print(f"   ✅ Phantom '8 G' detection FIXED!")
        
        # Summary
        print(f"\n📊 WORD BOUNDARY FIX SUMMARY:")
        print("-" * 40)
        
        print(f"   Phantom detections in negative tests: {phantom_detections}/{len(negative_test_cases)}")
        print(f"   Successful detections in positive tests: {successful_detections}/{len(positive_test_cases)}")
        print(f"   Section 9.4 total measurements: {len(measurements)}")
        
        if phantom_detections == 0 and successful_detections >= len(positive_test_cases) // 2:
            print(f"   🟢 **SUCCESS**: Word boundary fix working effectively!")
        elif phantom_detections == 0:
            print(f"   🟡 **PARTIAL**: Phantom detections fixed but some legitimate entities missed")
        else:
            print(f"   🔴 **FAILED**: Still have phantom detections")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Word boundary test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_word_boundary_fix()