#!/usr/bin/env python3
"""
GOAL: Validate baseline measurement detection before range post-processing
REASON: Need to ensure individual measurements are detected properly
PROBLEM: Range post-processing only works if individual measurements are detected first

Test Strategy:
1. Use existing FLPC engine with current measurement pattern
2. Test with WIP.md case: "30 inches", "37 inches", "76 cm", "94 cm"
3. Verify pattern comprehensiveness
4. Identify gaps in measurement detection
"""

import sys
sys.path.append('/home/corey/projects/docling/mvp-fusion')

from fusion.flpc_engine import FLPCEngine
import yaml

def test_measurement_detection():
    """Test measurement detection with current patterns"""
    print("🟡 **WAITING**: Testing baseline measurement detection...")
    
    config_path = '/home/corey/projects/docling/mvp-fusion/config/pattern_sets.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    flpc_engine = FLPCEngine(config)
    
    # Test cases for individual measurements
    test_cases = [
        "30 inches",
        "37 inches", 
        "76 cm",
        "94 cm",
        "Height is 30 inches",
        "Length 76 cm exactly",
        "Handrail height 30-37 inches (76-94 cm) installed January 1, 2024 for $1,500"
    ]
    
    print("Current measurement pattern:")
    measurement_pattern = config['flpc_regex_patterns']['universal_entities']['measurement']['pattern']
    print(f"  {measurement_pattern}")
    print()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"Test {i}: {test_text}")
        
        results = flpc_engine.extract_entities(test_text)
        entities = results.get('entities', {})
        
        print(f"  Detected entities: {list(entities.keys())}")
        
        # Look for measurement entities specifically  
        measurements = entities.get('MEASUREMENT', [])  # FLPC returns uppercase keys
        if measurements:
            print(f"  📊 Measurements found: {len(measurements)}")
            for measurement in measurements:
                print(f"    - {measurement}")
        else:
            print(f"  🔴 No measurements detected")
            # Debug: show all detected entities
            for category, items in entities.items():
                if items:
                    print(f"    Debug - {category}: {items}")
        print()
    
    return config

def analyze_pattern_coverage():
    """Analyze if the current pattern covers all needed cases"""
    print("🟡 **WAITING**: Analyzing measurement pattern coverage...")
    
    current_pattern = '(?i)\\b\\d+(?:\\.\\d+)?\\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)'
    
    # Test individual components
    test_units = ['inches', 'inch', 'cm', 'mm', 'feet', 'ft', 'm', 'meters']
    test_numbers = ['30', '37', '76', '94', '30.5', '76.2']
    
    print("Pattern coverage analysis:")
    print(f"  Current pattern: {current_pattern}")
    print()
    
    print("Units coverage:")
    for unit in test_units:
        if unit in current_pattern:
            print(f"  ✅ {unit} - covered")
        else:
            print(f"  ❌ {unit} - missing")
    
    # Identify potential issues
    issues = []
    
    # Check for boundary word issues
    if '\\b' not in current_pattern:
        issues.append("No word boundaries - may match partial words")
    
    # Check for spacing flexibility
    if '\\s*' not in current_pattern:
        issues.append("No flexible spacing between number and unit")
    
    print(f"\nPotential issues: {len(issues)}")
    for issue in issues:
        print(f"  ⚠️ {issue}")
    
    return issues

def main():
    """Main validation function"""
    print("🟢 **SUCCESS**: Starting measurement baseline validation")
    print("=" * 60)
    
    # Test 1: Current measurement detection
    config = test_measurement_detection()
    
    # Test 2: Pattern coverage analysis
    issues = analyze_pattern_coverage()
    
    # Summary
    print("📊 **MEASUREMENT DETECTION ASSESSMENT**:")
    print("  - Pattern exists: ✅ YES")
    print(f"  - Potential issues: {len(issues)}")
    
    if len(issues) == 0:
        print("🟢 **SUCCESS**: Measurement detection ready for testing")
    else:
        print("🔴 **BLOCKED**: Measurement pattern needs enhancement")
        print("  Recommendation: Fix issues before range post-processing")

if __name__ == "__main__":
    main()