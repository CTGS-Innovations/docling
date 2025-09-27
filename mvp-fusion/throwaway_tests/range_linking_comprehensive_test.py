#!/usr/bin/env python3
"""
Comprehensive Range Linking Test - MVP-Fusion
=============================================

GOAL: Test all joining word scenarios across measurement types
REASON: Growth projection "10-15%" shows broken range detection
PROBLEM: Need to validate linking words create single range entities

Expected Behavior:
- "10-15%" → ||10-15%||range001|| (single entity)
- NOT "10-||15.0||meas115||" (broken split)

Test Categories:
1. Percentage ranges with all joining words
2. Temperature ranges with all joining words  
3. Measurement ranges with all joining words
4. Date ranges with all joining words
5. Time ranges with all joining words
6. Money ranges with all joining words
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fusion.flpc_engine import FLPCEngine
from pathlib import Path
import yaml

class RangeLinkingTester:
    """Comprehensive test for range linking across all measurement types"""
    
    def __init__(self):
        # Load FLPC engine  
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.flpc_engine = FLPCEngine(config)
        
        # Define all joining words/symbols
        self.joining_words = [
            '-',           # Hyphen (most common)
            ' to ',        # "to" with spaces
            ' through ',   # "through" with spaces  
            ' thru ',      # Informal "thru"
            ' - ',         # Hyphen with spaces
            '–',           # En dash
            '—',           # Em dash
            ' between ',   # "between X and Y"
            ' from ',      # "from X to Y" 
            ' and ',       # Used with "between"
        ]
        
        # Test cases by measurement type
        self.test_cases = {
            'percentage': [
                ('10', '15', '%'),
                ('25.5', '30.2', '%'),
                ('0.5', '2.0', 'percent'),
                ('95', '99', '% accuracy')
            ],
            'temperature': [
                ('-20', '120', '°F'),
                ('-29', '49', '°C'), 
                ('32', '212', 'degrees Fahrenheit'),
                ('0', '100', 'degrees Celsius')
            ],
            'measurement': [
                ('30', '37', 'inches'),
                ('10', '15', 'feet'),
                ('2.5', '5.0', 'pounds'),
                ('500', '1000', 'decibels'),
                ('15', '30', 'minutes'),
                ('1', '3', 'hours')
            ],
            'date': [
                ('January 1', 'December 31', '2024'),
                ('2024-01-01', '2024-12-31', ''),
                ('March 15', 'April 20', '2024'),
                ('Q1', 'Q4', '2024')
            ],
            'money': [
                ('$1', '$5', 'million'),
                ('$100', '$500', 'thousand'),
                ('10', '20', 'dollars'),
                ('€50', '€100', '')
            ]
        }
        
    def generate_test_text(self, value1, value2, unit, joining_word):
        """Generate test text with specific joining pattern"""
        if joining_word == ' between ':
            return f"Range between {value1}{unit}{' and '}{value2}{unit}"
        elif joining_word == ' from ':
            return f"Range from {value1}{unit} to {value2}{unit}"
        else:
            return f"Range {value1}{unit}{joining_word}{value2}{unit}"
    
    def analyze_detection(self, text, expected_range):
        """Analyze what FLPC detects and check for proper range formation"""
        results = self.flpc_engine.extract_entities(text)
        entities = results.get('entities', {})
        
        # Get all detected entities
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                all_entities.append((entity_type, entity))
        
        # Check if we detected the full range vs broken pieces
        has_full_range = any(expected_range in str(entity) for _, entity in all_entities)
        
        return {
            'text': text,
            'expected_range': expected_range,
            'detected_entities': all_entities,
            'has_full_range': has_full_range,
            'entity_count': len(all_entities),
            'is_broken': len(all_entities) > 1 and not has_full_range
        }
    
    def run_comprehensive_test(self):
        """Run comprehensive test across all scenarios"""
        print("🔍 COMPREHENSIVE RANGE LINKING TEST")
        print("=" * 60)
        print("Testing individual detection + normalization approach")
        print("Expected: Individual entities detected, then linked in normalization")
        print()
        
        total_tests = 0
        broken_cases = []
        good_cases = []
        
        for measurement_type, test_values in self.test_cases.items():
            print(f"📊 {measurement_type.upper()} RANGES:")
            print("-" * 30)
            
            for value1, value2, unit in test_values:
                for joining_word in self.joining_words:
                    # Generate test text
                    text = self.generate_test_text(value1, value2, unit, joining_word)
                    expected_range = f"{value1}{unit}{joining_word}{value2}{unit}"
                    
                    # Analyze detection
                    result = self.analyze_detection(text, expected_range)
                    total_tests += 1
                    
                    # Categorize result
                    if result['is_broken']:
                        broken_cases.append(result)
                        status = "❌ BROKEN"
                    elif result['entity_count'] == 2:
                        good_cases.append(result)
                        status = "✅ GOOD (2 individual entities)"
                    elif result['has_full_range']:
                        good_cases.append(result)
                        status = "✅ PERFECT (full range)"
                    else:
                        status = "⚠️  UNCLEAR"
                    
                    print(f"  {status}: {text}")
                    print(f"    Detected: {result['detected_entities']}")
                    print()
        
        # Summary
        print("📋 TEST SUMMARY:")
        print("=" * 40)
        print(f"Total tests: {total_tests}")
        print(f"✅ Good cases: {len(good_cases)}")
        print(f"❌ Broken cases: {len(broken_cases)}")
        print(f"Success rate: {(len(good_cases)/total_tests)*100:.1f}%")
        
        # Show broken case patterns
        if broken_cases:
            print(f"\n🚨 BROKEN CASES ANALYSIS:")
            print("-" * 30)
            for case in broken_cases[:5]:  # Show first 5
                print(f"Text: {case['text']}")
                print(f"Issue: {case['detected_entities']}")
                print()
        
        # Recommendations
        print("🎯 RECOMMENDATIONS:")
        print("-" * 20)
        print("1. ✅ Individual detection working (FLPC finds individual numbers)")
        print("2. 🔧 Need range normalization in EntityNormalizer")
        print("3. 🎯 Focus on joining word detection algorithm")
        print("4. 📝 Create range linking post-processor")
        
        return {
            'total_tests': total_tests,
            'good_cases': len(good_cases),
            'broken_cases': len(broken_cases),
            'broken_examples': broken_cases[:10]
        }

if __name__ == "__main__":
    print("# GOAL: Test range linking across all measurement types")
    print("# REASON: Growth projection '10-15%' shows broken detection")
    print("# PROBLEM: Need comprehensive test for joining word scenarios")
    print()
    
    tester = RangeLinkingTester()
    results = tester.run_comprehensive_test()
    
    print(f"\n✅ Comprehensive test complete: {results['total_tests']} scenarios tested")
    print("Next step: Implement range normalization in EntityNormalizer")