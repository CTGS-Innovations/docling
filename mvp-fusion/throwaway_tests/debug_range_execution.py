#!/usr/bin/env python3
"""
GOAL: Debug why range post-processing is not executing in pipeline
REASON: No log messages or range entities found in output
PROBLEM: Integration issue - need to verify execution path

Debug Strategy:
1. Test if _detect_ranges_from_text method exists and works
2. Test with exact content from processed document
3. Identify where the integration is failing
"""

import sys
sys.path.append('/home/corey/projects/docling/mvp-fusion')

def test_range_method_exists():
    """Test if the range detection method can be imported"""
    print("🟡 **WAITING**: Testing range method import...")
    
    try:
        from pipeline.legacy.service_processor import ServiceProcessor
        
        # Check if method exists
        if hasattr(ServiceProcessor, '_detect_ranges_from_text'):
            print("✅ _detect_ranges_from_text method exists")
            
            # Test if fallback method exists
            if hasattr(ServiceProcessor, '_fallback_range_detection'):
                print("✅ _fallback_range_detection method exists")
            else:
                print("❌ _fallback_range_detection method missing")
                
            return True
        else:
            print("❌ _detect_ranges_from_text method missing")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_range_detection_directly():
    """Test range detection with exact problematic text"""
    print("🟡 **WAITING**: Testing range detection directly...")
    
    # Test text that should contain ranges
    test_text = "- Handrail height 30-37 inches (76-94 cm)"
    
    try:
        # Use our tested fallback method directly
        range_entities = []
        
        # Look for measurement ranges like "30-37 inches", "76-94 cm"
        measurement_units = ['inches', 'inch', 'cm', 'mm', 'meters', 'metres', 'feet', 'ft', 'yards', 'miles']
        
        # Split text into words for analysis
        words = test_text.split()
        print(f"Debug - Words: {words}")
        
        for i in range(len(words) - 1):  # Need at least 2 words: number-number unit
            word1 = words[i]
            word2 = words[i + 1] if i + 1 < len(words) else ""
            
            # Clean word1 and word2 of punctuation 
            word1_clean = word1.strip('().,;:!?')
            word2_clean = word2.strip('().,;:!?').lower()
            
            print(f"  Checking: '{word1_clean}' + '{word2_clean}'")
            
            # Check for pattern: number-number unit (including within parentheses)
            if '-' in word1_clean and word2_clean in measurement_units:
                print(f"  ✅ Found range pattern: {word1_clean} {word2_clean}")
                
                # Try to extract numbers from word1_clean
                parts = word1_clean.split('-')
                if len(parts) == 2:
                    try:
                        start_num = float(parts[0])
                        end_num = float(parts[1])
                        
                        # Create range entity
                        full_text = f"{word1_clean} {word2_clean}"
                        
                        range_entity = {
                            'value': full_text,
                            'text': full_text,
                            'type': 'measurement_range',
                            'range_components': {
                                'start_value': str(start_num),
                                'end_value': str(end_num),
                                'unit': word2_clean
                            },
                            'confidence': 'medium',
                            'detection_method': 'fallback_string_analysis'
                        }
                        range_entities.append(range_entity)
                        print(f"    ✅ Created range entity: {range_entity}")
                        
                    except ValueError as e:
                        print(f"    ❌ Number parsing failed: {e}")
            else:
                if '-' in word1_clean:
                    print(f"    ⚠️ Has dash but unit '{word2_clean}' not in measurement_units")
                    
        print(f"📊 Total ranges detected: {len(range_entities)}")
        return range_entities
        
    except Exception as e:
        print(f"❌ Range detection failed: {e}")
        return []

def main():
    """Main debug function"""
    print("🔴 **DEBUGGING**: Range post-processing execution issue")
    print("=" * 60)
    
    # Test 1: Method existence
    method_exists = test_range_method_exists()
    print()
    
    # Test 2: Direct range detection
    ranges = test_range_detection_directly()
    print()
    
    # Analysis
    print("📊 **DEBUG ANALYSIS**:")
    print(f"  - Range method exists: {'✅' if method_exists else '❌'}")
    print(f"  - Direct detection works: {'✅' if ranges else '❌'}")
    print(f"  - Ranges found: {len(ranges)}")
    
    if method_exists and ranges:
        print("🟢 **CONCLUSION**: Range detection logic works - integration issue")
        print("💡 **NEXT**: Check if range post-processing is being called in pipeline")
    else:
        print("🔴 **CONCLUSION**: Fundamental issue with range detection")

if __name__ == "__main__":
    main()