#!/usr/bin/env python3
"""
GOAL: Test Stage 3 AC+FLPC hybrid range detection
REASON: Verify range flagging works for "30-37 inches" case
PROBLEM: Need to confirm range indicators get properly flagged with metadata
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_stage3_range_detection():
    """Test the new AC+FLPC hybrid range detection in Stage 3"""
    print("🧪 TESTING STAGE 3 AC+FLPC HYBRID RANGE DETECTION")
    print("=" * 60)
    
    # Test content with range measurements
    test_content = """
    The frame measures 30-37 inches in width.
    Also measures 37 inches individually.
    Temperature dropped to -15 degrees.
    Standard temp is 15 degrees.
    Cost ranges from $100 to $200.
    """
    
    print(f"📄 TEST CONTENT:")
    print(f"   Content length: {len(test_content)} chars")
    print(f"   Contains: '30-37 inches', '-15 degrees', '$100 to $200'")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        # Test Stage 3 with range detection
        print(f"\n🔍 TESTING STAGE 3 WITH RANGE DETECTION:")
        print("-" * 40)
        
        entities = processor._extract_universal_entities(test_content)
        
        # Check measurements
        measurements = entities.get('measurement', [])
        print(f"📏 MEASUREMENTS DETECTED: {len(measurements)}")
        
        for i, measurement in enumerate(measurements, 1):
            text = measurement.get('text', 'N/A')
            range_info = measurement.get('range_indicator', {})
            detected = range_info.get('detected', False)
            
            print(f"   {i}. '{text}' - Range detected: {detected}")
            
            if detected:
                range_type = range_info.get('type', 'unknown')
                context = range_info.get('context', 'unknown')
                indicator = range_info.get('indicator_text', 'N/A')
                print(f"      → Type: {range_type}, Context: {context}, Indicator: '{indicator}'")
        
        # Check money entities
        money = entities.get('money', [])
        print(f"\n💰 MONEY DETECTED: {len(money)}")
        
        for i, money_entity in enumerate(money, 1):
            text = money_entity.get('text', 'N/A')
            range_info = money_entity.get('range_indicator', {})
            detected = range_info.get('detected', False)
            
            print(f"   {i}. '{text}' - Range detected: {detected}")
            
            if detected:
                range_type = range_info.get('type', 'unknown')
                context = range_info.get('context', 'unknown')
                indicator = range_info.get('indicator_text', 'N/A')
                print(f"      → Type: {range_type}, Context: {context}, Indicator: '{indicator}'")
        
        # Check range indicators
        range_indicators = entities.get('range_indicator', [])
        print(f"\n📐 RANGE INDICATORS DETECTED: {len(range_indicators)}")
        
        for i, indicator in enumerate(range_indicators, 1):
            text = indicator.get('text', 'N/A')
            span = indicator.get('span', {})
            print(f"   {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
        
        # Verify specific test cases
        print(f"\n🎯 VERIFICATION:")
        print("-" * 40)
        
        # Look for "37 inches" with range flag
        found_range_measurement = False
        found_negative_measurement = False
        
        for measurement in measurements:
            text = measurement.get('text', '')
            range_info = measurement.get('range_indicator', {})
            
            if '37' in text and 'inch' in text.lower():
                if range_info.get('detected') and range_info.get('context') == 'range':
                    found_range_measurement = True
                    print(f"   ✅ Range measurement: '{text}' correctly flagged as range")
            
            if '15' in text and 'degree' in text.lower():
                if range_info.get('detected') and range_info.get('context') == 'negative':
                    found_negative_measurement = True
                    print(f"   ✅ Negative measurement: '{text}' correctly flagged as negative")
        
        if not found_range_measurement:
            print(f"   ❌ Range measurement '37 inches' not properly flagged")
        
        if not found_negative_measurement:
            print(f"   ❌ Negative measurement '15 degrees' not properly flagged")
        
        print(f"\n📊 STAGE 3 RANGE DETECTION SUMMARY:")
        print("-" * 40)
        
        total_entities = len(measurements) + len(money)
        flagged_entities = sum(1 for m in measurements if m.get('range_indicator', {}).get('detected', False))
        flagged_entities += sum(1 for m in money if m.get('range_indicator', {}).get('detected', False))
        
        print(f"   Total entities: {total_entities}")
        print(f"   Range-flagged entities: {flagged_entities}")
        print(f"   Range indicators detected: {len(range_indicators)}")
        
        if flagged_entities > 0:
            print(f"   🟢 **SUCCESS**: Range detection working!")
        else:
            print(f"   🔴 **FAILED**: No entities flagged with ranges")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Stage 3 test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage3_range_detection()