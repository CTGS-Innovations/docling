#!/usr/bin/env python3
"""
Core-8 Test Matrix - Comprehensive Coverage Validation
======================================================

GOAL: Create visible test matrix for user validation of comprehensive coverage
REASON: User needs to verify test cases cover all areas properly
PROBLEM: Need transparent view of what's being tested across Core-8 entities

TEST MATRIX STRUCTURE:
- DATE: Various formats, ranges, negatives, edge cases
- TIME: 12/24 hour, ranges, AM/PM, edge cases  
- MONEY: Currencies, ranges, negatives, multipliers
- MEASUREMENT: Units, ranges, negatives, scientific notation

ORDER OF OPERATIONS: WIDEST TO NARROWEST (CORRECTED)
1. Complete entity ranges with full context
2. Complete single entities 
3. Partial entities with units
4. Bare numbers (lowest priority)
"""

from typing import Dict, List, Tuple
import json

class TestMatrixGenerator:
    """Generate comprehensive test matrix for Core-8 entities"""
    
    def __init__(self):
        self.test_matrix = self._build_comprehensive_matrix()
    
    def _build_comprehensive_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Build complete test matrix organized by entity and test type"""
        
        return {
            "DATE": {
                "ranges_full_context": [
                    "Project timeline: January 1, 2024 to December 31, 2024",
                    "Quarter spans March 15, 2024 through June 15, 2024", 
                    "Fiscal year from July 1, 2023 to June 30, 2024",
                    "Contract period: 2024-01-01 / 2024-12-31",
                    "Meeting scheduled between April 10, 2024 and April 12, 2024"
                ],
                "ranges_simple": [
                    "January 1, 2024 to December 31, 2024",
                    "March 15 - April 20, 2024",
                    "2024-01-01/2024-12-31",
                    "Jan 1 through Dec 31, 2024",
                    "Q1 2024 to Q4 2024"
                ],
                "single_dates_full": [
                    "Meeting on January 15, 2024",
                    "Deadline: December 31, 2024", 
                    "Born on 1990-05-15",
                    "Event scheduled for Mar 10, 2024",
                    "Due date is 2024/12/15"
                ],
                "single_dates_simple": [
                    "January 15, 2024",
                    "2024-01-15", 
                    "12/31/2024",
                    "Mar 10, 2024",
                    "Dec 31st, 2024"
                ],
                "relative_negative": [
                    "Delayed by -5 days",
                    "Behind schedule minus 2 weeks", 
                    "Backdated to -30 days",
                    "Historical: -100 years ago",
                    "Overdue by -7 days"
                ],
                "edge_cases": [
                    "Feb 29, 2024 (leap year)",
                    "Invalid: Feb 30, 2024",
                    "Century: January 1, 2000",
                    "Far future: 2099-12-31",
                    "Ambiguous: 01/02/03"
                ]
            },
            
            "TIME": {
                "ranges_full_context": [
                    "Office hours: 9:00 AM to 5:00 PM",
                    "Meeting scheduled from 2:30 PM through 4:30 PM",
                    "Shift runs 6:00 AM to 2:00 PM",
                    "Event timing: 14:00 - 16:00 (24-hour)",
                    "Break period between 12:00 PM and 1:00 PM"
                ],
                "ranges_simple": [
                    "9:00 AM to 5:00 PM",
                    "2:30-4:30 PM", 
                    "14:00 through 16:00",
                    "6:00 AM / 2:00 PM",
                    "12:00 - 13:00"
                ],
                "single_times_full": [
                    "Meeting at 9:00 AM",
                    "Deadline: 5:00 PM",
                    "Call scheduled for 14:30",
                    "Lunch break at 12:00 PM",
                    "Event starts 8:00 PM"
                ],
                "single_times_simple": [
                    "9:00 AM",
                    "17:30",
                    "12:00 PM",
                    "8:00 PM", 
                    "14:30"
                ],
                "relative_negative": [
                    "Running -15 minutes late",
                    "Behind by minus 30 minutes",
                    "Delayed -2 hours",
                    "Early by -10 minutes",
                    "Deficit of -45 minutes"
                ],
                "edge_cases": [
                    "Midnight: 12:00 AM",
                    "Noon: 12:00 PM", 
                    "Invalid: 25:00",
                    "Seconds: 14:30:45",
                    "Military: 0800 hours"
                ]
            },
            
            "MONEY": {
                "ranges_full_context": [
                    "Budget allocation: $1 million to $5 million",
                    "Salary range $50,000 through $75,000 annually",
                    "Investment from €100K to €500K",
                    "Revenue target: $10M - $20M",
                    "Cost estimate between $500 and $1,000"
                ],
                "ranges_simple": [
                    "$1M to $5M",
                    "$50K-$75K",
                    "€100 through €500",
                    "$10 - $20 million",
                    "£1,000 / £5,000"
                ],
                "single_amounts_full": [
                    "Price is $1,500",
                    "Budget: $2.5 million",
                    "Cost €500 thousand", 
                    "Revenue of $10M",
                    "Investment: £250K"
                ],
                "single_amounts_simple": [
                    "$1,500",
                    "$2.5M",
                    "€500K",
                    "$10 million",
                    "£250,000"
                ],
                "negative_losses": [
                    "Loss of $500,000",
                    "Deficit: -$2 million",
                    "Minus $750K",
                    "Negative cash flow -$100K",
                    "Below -$50,000"
                ],
                "edge_cases": [
                    "Free: $0",
                    "Cents: $0.99",
                    "Large: $1.5 billion", 
                    "Cryptocurrency: 0.05 BTC",
                    "Foreign: ¥10,000"
                ]
            },
            
            "MEASUREMENT": {
                "ranges_full_context": [
                    "Temperature range: -20°F to 120°F",
                    "Height requirement 5 feet through 6 feet 2 inches",
                    "Weight capacity from 250 pounds to 500 pounds",
                    "Sound level between 60 and 90 decibels",
                    "Duration: 15 minutes to 2 hours"
                ],
                "ranges_simple": [
                    "10-15%",
                    "30-37 inches",
                    "-20°F to 120°F",
                    "250-500 pounds",
                    "60 through 90 decibels"
                ],
                "single_measurements_full": [
                    "Temperature is 72°F",
                    "Height: 6 feet 2 inches",
                    "Weight limit 250 pounds",
                    "Duration of 30 minutes",
                    "Distance: 5.5 miles"
                ],
                "single_measurements_simple": [
                    "72°F",
                    "6.2 feet",
                    "250 lbs",
                    "30 minutes", 
                    "5.5 miles"
                ],
                "negative_measurements": [
                    "Below freezing: -10°F",
                    "Loss of 15%",
                    "Deficit: -50 pounds",
                    "Minus 30 minutes",
                    "Negative pressure: -5 PSI"
                ],
                "scientific_edge_cases": [
                    "Precise: 98.6°F",
                    "Scientific: 1.23e-4 meters",
                    "Zero: 0°C",
                    "Extreme: -273.15°C (absolute zero)",
                    "Large: 1,000,000 bytes"
                ]
            }
        }
    
    def print_test_matrix(self):
        """Print comprehensive test matrix for user validation"""
        print("🔍 CORE-8 COMPREHENSIVE TEST MATRIX")
        print("=" * 80)
        print("Complete test coverage for user validation")
        print()
        
        total_tests = 0
        
        for entity, test_categories in self.test_matrix.items():
            print(f"📊 {entity} ENTITY TESTS:")
            print("=" * 50)
            
            entity_total = 0
            for category, test_cases in test_categories.items():
                print(f"\n🎯 {category.upper().replace('_', ' ')}:")
                print("-" * 40)
                
                for i, test_case in enumerate(test_cases, 1):
                    print(f"  {i:2d}. {test_case}")
                    entity_total += 1
                    total_tests += 1
                
                print(f"\n     Subtotal: {len(test_cases)} tests")
            
            print(f"\n📈 {entity} TOTAL: {entity_total} tests")
            print("=" * 50)
            print()
        
        print(f"🎯 GRAND TOTAL: {total_tests} comprehensive test cases")
        print()
        
        # Test distribution analysis
        print("📊 TEST DISTRIBUTION ANALYSIS:")
        print("-" * 40)
        for entity, test_categories in self.test_matrix.items():
            entity_count = sum(len(cases) for cases in test_categories.values())
            percentage = (entity_count / total_tests) * 100
            print(f"  {entity:12s}: {entity_count:3d} tests ({percentage:5.1f}%)")
        
        print()
        print("📋 COVERAGE AREAS PER ENTITY:")
        print("-" * 40)
        for entity, test_categories in self.test_matrix.items():
            areas = list(test_categories.keys())
            print(f"  {entity:12s}: {len(areas)} areas - {', '.join(areas)}")
    
    def get_flat_test_list(self) -> List[Tuple[str, str, str]]:
        """Get flat list of all test cases for automated testing"""
        flat_tests = []
        for entity, test_categories in self.test_matrix.items():
            for category, test_cases in test_categories.items():
                for test_case in test_cases:
                    flat_tests.append((entity, category, test_case))
        return flat_tests
    
    def save_test_matrix_json(self, filename: str = "core8_test_matrix.json"):
        """Save test matrix as JSON for external validation"""
        with open(filename, 'w') as f:
            json.dump(self.test_matrix, f, indent=2)
        print(f"💾 Test matrix saved to {filename}")
    
    def validate_coverage(self) -> Dict[str, bool]:
        """Validate that all required coverage areas are present"""
        required_areas = {
            "ranges_full_context": "Full contextual ranges",
            "ranges_simple": "Simple ranges without context", 
            "single_*_full": "Single entities with context",
            "single_*_simple": "Single entities without context",
            "negative_*": "Negative/loss scenarios",
            "edge_cases": "Edge cases and error conditions"
        }
        
        coverage_check = {}
        for entity, test_categories in self.test_matrix.items():
            entity_coverage = {}
            categories = list(test_categories.keys())
            
            entity_coverage["has_ranges"] = any("range" in cat for cat in categories)
            entity_coverage["has_singles"] = any("single" in cat for cat in categories) 
            entity_coverage["has_negatives"] = any("negative" in cat for cat in categories)
            entity_coverage["has_edge_cases"] = any("edge" in cat for cat in categories)
            entity_coverage["has_context_variants"] = any("full" in cat for cat in categories)
            
            coverage_check[entity] = entity_coverage
        
        return coverage_check

def main():
    """Main function to display comprehensive test matrix"""
    print("# GOAL: Display comprehensive test matrix for user validation")
    print("# REASON: User needs to verify test coverage across all Core-8 areas")
    print("# PROBLEM: Ensure complete coverage before implementation")
    print()
    
    generator = TestMatrixGenerator()
    
    # Display full test matrix
    generator.print_test_matrix()
    
    # Validate coverage
    print("\n🔍 COVERAGE VALIDATION:")
    print("=" * 40)
    coverage = generator.validate_coverage()
    
    for entity, checks in coverage.items():
        print(f"\n{entity} Coverage:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
    
    # Save for external validation
    generator.save_test_matrix_json("throwaway_tests/core8_test_matrix.json")
    
    # Get flat list for testing
    flat_tests = generator.get_flat_test_list()
    print(f"\n📋 Ready for testing: {len(flat_tests)} individual test cases")
    
    print("\n🎯 NEXT STEPS:")
    print("1. User validates test matrix coverage")
    print("2. Implement widest-to-narrowest order of operations") 
    print("3. Run comprehensive testing with corrected priority order")
    print("4. Deploy to FLPC pattern_sets.yaml")

if __name__ == "__main__":
    main()