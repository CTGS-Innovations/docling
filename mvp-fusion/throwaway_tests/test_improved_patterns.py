#!/usr/bin/env python3
"""
Test improved FLPC patterns for money, percentage, and measurement ranges
========================================================================

GOAL: Verify that improved patterns correctly handle ranges and complex formats
REASON: Updated pattern_sets.yaml with new patterns that should capture ranges
PROBLEM: Need to validate the new patterns work as expected
"""

import re
import yaml
from pathlib import Path

def test_improved_patterns():
    """Test the improved FLPC patterns from pattern_sets.yaml"""
    
    # Load patterns from actual config file
    config_file = Path("/home/corey/projects/docling/mvp-fusion/config/pattern_sets.yaml")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    patterns = config['flpc_regex_patterns']['universal_entities']
    
    # Test cases from real documents
    test_cases = {
        'money': [
            # Should work - simple money
            "$58.51",
            "$55.7B", 
            "$52.3B",
            "$21 billion",
            "$25B",
            
            # Should now work - money ranges
            "60 to 70 billion dollars",
            "$10M to $20M",
            "$1.5 billion to $2.3 billion",
            "$500K-$1M",
        ],
        
        'percent': [
            # Should work - simple percentages
            "5%",
            "12.5%",
            "85%",
            
            # Should now work - percentage ranges
            "60% to 70%",
            "15-20%",
            "5% - 15%",
        ],
        
        'measurement': [
            # Should work - simple measurements
            "28 G",
            "15 L", 
            "5m",
            
            # Should now work - measurement ranges  
            "10-15 kg",
            "5 to 10 feet",
            "100g to 200g"
        ]
    }
    
    print("🧪 Testing Improved FLPC Patterns")
    print("=" * 60)
    
    for pattern_name in ['money', 'percent', 'measurement']:
        if pattern_name not in patterns:
            print(f"❌ Pattern '{pattern_name}' not found in config")
            continue
            
        pattern_info = patterns[pattern_name]
        pattern_str = pattern_info['pattern']
        
        print(f"\n📊 {pattern_name.upper()} Pattern (Improved):")
        print(f"   Description: {pattern_info['description']}")
        print(f"   Priority: {pattern_info['priority']}")
        
        pattern = re.compile(pattern_str)
        total_cases = len(test_cases[pattern_name])
        matches_found = 0
        
        for test_case in test_cases[pattern_name]:
            matches = pattern.findall(test_case)
            if matches:
                matches_found += 1
                print(f"   ✅ '{test_case}' -> {matches}")
            else:
                print(f"   ❌ '{test_case}' -> NO MATCH")
        
        success_rate = (matches_found / total_cases) * 100
        print(f"   📈 Success rate: {matches_found}/{total_cases} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print(f"   🟢 **SUCCESS**: Excellent pattern coverage")
        elif success_rate >= 70:
            print(f"   🟡 **PARTIAL**: Good pattern coverage, minor improvements needed")
        else:
            print(f"   🔴 **NEEDS WORK**: Pattern requires significant improvement")

if __name__ == "__main__":
    test_improved_patterns()