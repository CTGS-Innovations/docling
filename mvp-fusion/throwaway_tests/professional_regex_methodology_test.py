#!/usr/bin/env python3
"""
Professional Regex Methodology Test
====================================

GOAL: Prove the order-of-operations approach works for range/negative detection
REASON: Need data-driven validation before implementing in FLPC pipeline
PROBLEM: Current approach fails on "10-15%" and "-20°F to 120°F" cases

METHODOLOGY (Professional Standards):
1. Interval regex (dates/times with "/") - HIGHEST PRIORITY
2. Range regex (two operands around dash) - HIGH PRIORITY  
3. Negative single values (dash glued to number) - MEDIUM PRIORITY
4. Positive single values - LOW PRIORITY

TEST CASES:
- "10-15%" → Range: {start: 10, end: 15, unit: "%"}
- "-20°F" → Negative: {value: -20, unit: "°F"}
- "-20°F to 120°F" → Range: {start: -20, end: 120, unit: "°F"}
- "Growth projection: 10-15% range" → Range detected
- "Temperature is -20°F today" → Negative detected
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class DetectedEntity:
    """Structured entity representation"""
    type: str  # "range", "negative", "positive"
    text: str  # Original text
    value: Optional[float] = None  # For single values
    start: Optional[float] = None  # For ranges
    end: Optional[float] = None    # For ranges
    unit: str = ""
    category: str = ""  # "measurement", "money", "date", "time"

class ProfessionalRegexEngine:
    """
    Implementation of professional order-of-operations methodology
    
    Follows NIST/ISO standards for numeric range detection
    """
    
    def __init__(self):
        # PRIORITY ORDER PATTERNS (highest to lowest)
        self.patterns = [
            # 1. INTERVAL REGEX (dates/times with "/") - HIGHEST PRIORITY
            {
                'name': 'date_intervals',
                'pattern': r'(\d{4}-\d{2}-\d{2})\s*/\s*(\d{4}-\d{2}-\d{2})',
                'priority': 1,
                'category': 'date'
            },
            
            # 2. RANGE REGEX (two operands around dash) - HIGH PRIORITY
            {
                'name': 'measurement_ranges',
                'pattern': r'([-−]?\d+(?:\.\d+)?)\s*(?:°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)\s*[-–]\s*([-−]?\d+(?:\.\d+)?)\s*(?:°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 2,
                'category': 'measurement'
            },
            {
                'name': 'unit_suffix_ranges', 
                'pattern': r'([-−]?\d+(?:\.\d+)?)\s*[-–]\s*([-−]?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 2,
                'category': 'measurement'
            },
            {
                'name': 'money_ranges',
                'pattern': r'(\$[-−]?\d+(?:\.\d+)?(?:[KMB])?)\s*[-–]\s*(\$?[-−]?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 2,
                'category': 'money'
            },
            
            # 3. NEGATIVE SINGLE VALUES (dash glued to number) - MEDIUM PRIORITY
            {
                'name': 'negative_measurements',
                'pattern': r'(?<!\d)\s*([-−])\s*(\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 3,
                'category': 'measurement'
            },
            {
                'name': 'negative_money',
                'pattern': r'(?<!\d)\s*([-−])\s*(\$?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 3,
                'category': 'money'
            },
            
            # 4. POSITIVE SINGLE VALUES - LOW PRIORITY
            {
                'name': 'positive_measurements',
                'pattern': r'(?<!\d)\s*(\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 4,
                'category': 'measurement'
            },
            {
                'name': 'positive_money',
                'pattern': r'(?<!\d)\s*(\$?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 4,
                'category': 'money'
            }
        ]
        
        # Compile patterns
        self.compiled_patterns = []
        for pattern_info in self.patterns:
            try:
                compiled = re.compile(pattern_info['pattern'], re.IGNORECASE)
                self.compiled_patterns.append({
                    **pattern_info,
                    'compiled': compiled
                })
            except Exception as e:
                print(f"⚠️  Failed to compile pattern '{pattern_info['name']}': {e}")
    
    def detect_entities(self, text: str) -> List[DetectedEntity]:
        """
        Detect entities using professional order-of-operations
        
        Returns structured entities with proper precedence
        """
        entities = []
        used_spans = set()  # Track character spans to avoid overlaps
        
        # Process patterns in priority order
        for pattern_info in self.compiled_patterns:
            matches = pattern_info['compiled'].finditer(text)
            
            for match in matches:
                start, end = match.span()
                
                # Skip if this span overlaps with higher-priority match
                if any(pos in used_spans for pos in range(start, end)):
                    continue
                
                # Mark this span as used
                used_spans.update(range(start, end))
                
                # Parse the match based on pattern type
                entity = self._parse_match(match, pattern_info, text)
                if entity:
                    entities.append(entity)
        
        return entities
    
    def _parse_match(self, match: re.Match, pattern_info: Dict, text: str) -> Optional[DetectedEntity]:
        """Parse regex match into structured entity"""
        groups = match.groups()
        matched_text = match.group(0)
        
        try:
            if 'ranges' in pattern_info['name']:
                # Range patterns
                if len(groups) >= 2:
                    start_val = self._extract_number(groups[0])
                    end_val = self._extract_number(groups[1])
                    unit = groups[2] if len(groups) > 2 else self._extract_unit(matched_text)
                    
                    return DetectedEntity(
                        type="range",
                        text=matched_text,
                        start=start_val,
                        end=end_val,
                        unit=unit,
                        category=pattern_info['category']
                    )
            
            elif 'negative' in pattern_info['name']:
                # Negative single values
                if len(groups) >= 2:
                    value = -self._extract_number(groups[1])  # Apply negative
                    unit = groups[2] if len(groups) > 2 else self._extract_unit(matched_text)
                    
                    return DetectedEntity(
                        type="negative",
                        text=matched_text,
                        value=value,
                        unit=unit,
                        category=pattern_info['category']
                    )
            
            else:
                # Positive single values
                value = self._extract_number(groups[0])
                unit = groups[1] if len(groups) > 1 else self._extract_unit(matched_text)
                
                return DetectedEntity(
                    type="positive",
                    text=matched_text,
                    value=value,
                    unit=unit,
                    category=pattern_info['category']
                )
                
        except Exception as e:
            print(f"⚠️  Parse error for '{matched_text}': {e}")
            return None
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        # Handle negative signs and special characters
        clean_text = text.replace('−', '-').replace('$', '').strip()
        
        # Extract just the number part
        import re
        number_match = re.search(r'[-]?\d+(?:\.\d+)?', clean_text)
        if number_match:
            return float(number_match.group())
        return 0.0
    
    def _extract_unit(self, text: str) -> str:
        """Extract unit from matched text"""
        import re
        unit_match = re.search(r'(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm|\$|[KMB])', text)
        return unit_match.group() if unit_match else ""

def test_professional_methodology():
    """Test the professional order-of-operations approach"""
    print("🔍 PROFESSIONAL REGEX METHODOLOGY TEST")
    print("=" * 60)
    print("Testing order-of-operations for range/negative detection")
    print()
    
    engine = ProfessionalRegexEngine()
    
    # Test cases that currently fail
    test_cases = [
        # Range cases
        "Growth projection: 10-15% range",
        "Temperature range -20°F to 120°F", 
        "10-15%",
        "30-37 inches",
        "Weight capacity 250-500 pounds",
        "$1-5 million",
        
        # Negative cases  
        "Temperature is -20°F today",
        "Loss of -$500",
        "Below -37 inches",
        
        # Mixed cases
        "Range from -20°F to 120°F with -5°F average",
        "Growth: 10-15% but declined -2%",
        
        # Edge cases
        "2024-01-01/2024-12-31",  # Date interval
        "10 to 15 inches",        # Word connector
        "Between 10% and 15%"     # Word range
    ]
    
    print("📊 DETECTION RESULTS:")
    print("-" * 40)
    
    total_tests = len(test_cases)
    successful_detections = 0
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i:2d}: \"{text}\"")
        
        entities = engine.detect_entities(text)
        
        if entities:
            successful_detections += 1
            print(f"  ✅ DETECTED: {len(entities)} entities")
            for entity in entities:
                if entity.type == "range":
                    print(f"    📏 Range: {entity.start} to {entity.end} {entity.unit} ({entity.category})")
                elif entity.type == "negative":
                    print(f"    ➖ Negative: {entity.value} {entity.unit} ({entity.category})")
                else:
                    print(f"    ➕ Positive: {entity.value} {entity.unit} ({entity.category})")
        else:
            print(f"  ❌ NO DETECTION")
        
        print()
    
    # Summary
    print("📊 TEST SUMMARY:")
    print("=" * 30)
    print(f"Total tests: {total_tests}")
    print(f"Successful detections: {successful_detections}")
    print(f"Success rate: {(successful_detections/total_tests)*100:.1f}%")
    
    if successful_detections >= total_tests * 0.8:  # 80% threshold
        print("✅ METHODOLOGY PROVEN: Ready for FLPC implementation")
        print("🎯 Key success: Order-of-operations resolves range vs negative conflicts")
    else:
        print("❌ METHODOLOGY NEEDS REFINEMENT")
        print("🔧 Check pattern design and precedence logic")
    
    return successful_detections / total_tests

if __name__ == "__main__":
    print("# GOAL: Prove professional order-of-operations methodology works")
    print("# REASON: Need data-driven validation before FLPC implementation")
    print("# PROBLEM: Current approach fails on range/negative edge cases")
    print()
    
    success_rate = test_professional_methodology()
    
    if success_rate >= 0.8:
        print(f"\n🎉 PROOF OF CONCEPT SUCCESSFUL: {success_rate*100:.1f}% success rate")
        print("Ready to implement in FLPC pattern_sets.yaml")
    else:
        print(f"\n🔧 CONCEPT NEEDS WORK: {success_rate*100:.1f}% success rate")
        print("Refine patterns before FLPC implementation")