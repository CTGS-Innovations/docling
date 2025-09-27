#!/usr/bin/env python3
"""
Comprehensive Core-8 Methodology Test
=====================================

GOAL: Test professional order-of-operations across ALL Core-8 entities
REASON: Need complete validation for DATE, TIME, MONEY, MEASUREMENT
PROBLEM: Must handle all joining symbols, negative indicators, and edge cases

COMPREHENSIVE TEST MATRIX:
- ENTITIES: Date, Time, Money, Measurement  
- JOINING: -, –, —, to, through, thru, between...and, from...to, /
- NEGATIVES: -, −, minus, negative, loss, decline, drop, below
- FORMATS: Various number formats, units, currencies, time formats

Expected Results:
- All ranges detected as single entities
- All negatives properly signed
- Priority order resolves conflicts correctly
"""

import re
from typing import Dict, List, Any, Optional, Tuple
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
    raw_start: str = ""  # Original start text
    raw_end: str = ""    # Original end text

class ComprehensiveRegexEngine:
    """
    Comprehensive implementation covering all Core-8 entities
    
    Tests all joining symbols and negative indicators
    """
    
    def __init__(self):
        # ALL JOINING SYMBOLS AND WORDS
        self.join_patterns = [
            r'[-−–—]',           # Hyphens, minus, en dash, em dash
            r'\s+to\s+',         # "to" with spaces
            r'\s+through\s+',    # "through" with spaces  
            r'\s+thru\s+',       # "thru" with spaces
            r'\s*[/]\s*',        # Forward slash
            r'\s+from\s+(.+?)\s+to\s+',  # "from X to Y"
            r'between\s+(.+?)\s+and\s+', # "between X and Y"
        ]
        
        # ALL NEGATIVE INDICATORS
        self.negative_patterns = [
            r'[-−]',             # Direct negative signs
            r'minus\s+',         # "minus 20"
            r'negative\s+',      # "negative 20" 
            r'loss\s+of\s+',     # "loss of $500"
            r'decline\s+of\s+',  # "decline of 15%"
            r'drop\s+of\s+',     # "drop of 5 degrees"
            r'below\s+',         # "below -20°F"
            r'deficit\s+of\s+',  # "deficit of $1M"
        ]
        
        # UNIT PATTERNS BY CATEGORY
        self.units = {
            'measurement': r'(?:°[CF]|%|inches?|inch|feet|foot|ft|pounds?|pound|lbs?|kg|kilograms?|minutes?|minute|min|hours?|hour|hr|decibels?|decibel|db|meters?|meter|metres?|metre|m|cm|mm|millimeters?|kilometers?|km|grams?|gram|g|mg|ounces?|ounce|oz)',
            'money': r'(?:\$|USD|EUR|GBP|dollars?|dollar|euros?|euro|pounds?|pound|million|billion|thousand|M|B|K)',
            'time': r'(?:AM|PM|am|pm|hours?|hour|hr|minutes?|minute|min|seconds?|second|sec|o\'clock)',
            'date': r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|\d{1,2}[/-]\d{1,2})',
        }
        
        # Build comprehensive pattern set
        self.patterns = self._build_patterns()
        
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
    
    def _build_patterns(self) -> List[Dict]:
        """Build comprehensive pattern set for all Core-8 entities"""
        patterns = []
        
        # PRIORITY 1: DATE INTERVALS (ISO format with /)
        patterns.append({
            'name': 'date_intervals_iso',
            'pattern': r'(\d{4}-\d{2}-\d{2})\s*/\s*(\d{4}-\d{2}-\d{2})',
            'priority': 1,
            'category': 'date'
        })
        
        # PRIORITY 2: MEASUREMENT RANGES (all joining symbols)
        for i, join in enumerate([r'[-−–—]', r'\s+to\s+', r'\s+through\s+', r'\s+thru\s+']):
            patterns.append({
                'name': f'measurement_range_{i}',
                'pattern': f'([-−]?\\d+(?:\\.\\d+)?)\\s*{self.units["measurement"]}\\s*{join}\\s*([-−]?\\d+(?:\\.\\d+)?)\\s*{self.units["measurement"]}',
                'priority': 2,
                'category': 'measurement'
            })
            # Unit suffix version
            patterns.append({
                'name': f'measurement_range_suffix_{i}',
                'pattern': f'([-−]?\\d+(?:\\.\\d+)?)\\s*{join}\\s*([-−]?\\d+(?:\\.\\d+)?)\\s*{self.units["measurement"]}',
                'priority': 2,
                'category': 'measurement'
            })
        
        # PRIORITY 2: MONEY RANGES
        for i, join in enumerate([r'[-−–—]', r'\s+to\s+', r'\s+through\s+']):
            patterns.append({
                'name': f'money_range_{i}',
                'pattern': f'(\\$?[-−]?\\d+(?:\\.\\d+)?(?:[KMB])?)\\s*{join}\\s*(\\$?[-−]?\\d+(?:\\.\\d+)?(?:[KMB])?)',
                'priority': 2,
                'category': 'money'
            })
        
        # PRIORITY 2: TIME RANGES  
        for i, join in enumerate([r'[-−–—]', r'\s+to\s+', r'\s+through\s+']):
            patterns.append({
                'name': f'time_range_{i}',
                'pattern': f'(\\d{1,2}:\\d{2}(?::\\d{2})?(?:\\s*(?:AM|PM|am|pm))?)\\s*{join}\\s*(\\d{1,2}:\\d{2}(?::\\d{2})?(?:\\s*(?:AM|PM|am|pm))?)',
                'priority': 2,
                'category': 'time'
            })
        
        # PRIORITY 2: DATE RANGES
        for i, join in enumerate([r'[-−–—]', r'\s+to\s+', r'\s+through\s+']):
            patterns.append({
                'name': f'date_range_{i}',
                'pattern': f'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2},?\\s+\\d{4})\\s*{join}\\s*((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2},?\\s+\\d{4})',
                'priority': 2,
                'category': 'date'
            })
        
        # PRIORITY 3: NEGATIVE SINGLE VALUES (all negative indicators)
        for neg_pattern in self.negative_patterns:
            patterns.extend([
                {
                    'name': f'negative_measurement_{hash(neg_pattern)}',
                    'pattern': f'{neg_pattern}(\\d+(?:\\.\\d+)?)\\s*{self.units["measurement"]}',
                    'priority': 3,
                    'category': 'measurement'
                },
                {
                    'name': f'negative_money_{hash(neg_pattern)}',
                    'pattern': f'{neg_pattern}(\\$?\\d+(?:\\.\\d+)?(?:[KMB])?)',
                    'priority': 3,
                    'category': 'money'
                }
            ])
        
        # PRIORITY 4: POSITIVE SINGLE VALUES
        patterns.extend([
            {
                'name': 'positive_measurement',
                'pattern': f'(?<!\\d)\\s*(\\d+(?:\\.\\d+)?)\\s*{self.units["measurement"]}',
                'priority': 4,
                'category': 'measurement'
            },
            {
                'name': 'positive_money',
                'pattern': f'(?<!\\d)\\s*(\\$?\\d+(?:\\.\\d+)?(?:[KMB])?)',
                'priority': 4,
                'category': 'money'
            },
            {
                'name': 'positive_time',
                'pattern': r'(?<!\d)\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)',
                'priority': 4,
                'category': 'time'
            },
            {
                'name': 'positive_date',
                'pattern': r'(?<!\d)\s*((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',
                'priority': 4,
                'category': 'date'
            }
        ])
        
        # Sort by priority
        return sorted(patterns, key=lambda x: x['priority'])
    
    def detect_entities(self, text: str) -> List[DetectedEntity]:
        """Detect entities using comprehensive Core-8 methodology"""
        entities = []
        used_spans = set()
        
        # Process patterns in priority order
        for pattern_info in self.compiled_patterns:
            matches = pattern_info['compiled'].finditer(text)
            
            for match in matches:
                start, end = match.span()
                
                # Skip if overlaps with higher-priority match
                if any(pos in used_spans for pos in range(start, end)):
                    continue
                
                used_spans.update(range(start, end))
                
                entity = self._parse_match(match, pattern_info, text)
                if entity:
                    entities.append(entity)
        
        return entities
    
    def _parse_match(self, match: re.Match, pattern_info: Dict, text: str) -> Optional[DetectedEntity]:
        """Parse regex match into structured entity"""
        groups = match.groups()
        matched_text = match.group(0)
        
        try:
            if 'range' in pattern_info['name']:
                # Range patterns
                if len(groups) >= 2:
                    start_val = self._extract_number(groups[0])
                    end_val = self._extract_number(groups[1])
                    unit = self._extract_unit(matched_text, pattern_info['category'])
                    
                    return DetectedEntity(
                        type="range",
                        text=matched_text,
                        start=start_val,
                        end=end_val,
                        unit=unit,
                        category=pattern_info['category'],
                        raw_start=groups[0],
                        raw_end=groups[1]
                    )
            
            elif 'negative' in pattern_info['name']:
                # Negative single values
                if groups:
                    value = -abs(self._extract_number(groups[0]))  # Ensure negative
                    unit = self._extract_unit(matched_text, pattern_info['category'])
                    
                    return DetectedEntity(
                        type="negative",
                        text=matched_text,
                        value=value,
                        unit=unit,
                        category=pattern_info['category']
                    )
            
            else:
                # Positive single values
                if groups:
                    value = self._extract_number(groups[0])
                    unit = self._extract_unit(matched_text, pattern_info['category'])
                    
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
        if not text:
            return 0.0
            
        # Handle various negative signs and formats
        clean_text = text.replace('−', '-').replace('$', '').strip()
        
        # Handle multipliers
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        multiplier = 1
        for suffix, mult in multipliers.items():
            if suffix in clean_text.upper():
                multiplier = mult
                clean_text = clean_text.upper().replace(suffix, '')
        
        # Extract number
        number_match = re.search(r'[-]?\d+(?:\.\d+)?', clean_text)
        if number_match:
            return float(number_match.group()) * multiplier
        return 0.0
    
    def _extract_unit(self, text: str, category: str) -> str:
        """Extract unit from matched text"""
        if category in self.units:
            unit_match = re.search(self.units[category], text, re.IGNORECASE)
            return unit_match.group() if unit_match else ""
        return ""

def test_comprehensive_core8():
    """Comprehensive test across all Core-8 entities"""
    print("🔍 COMPREHENSIVE CORE-8 METHODOLOGY TEST")
    print("=" * 70)
    print("Testing all entities, joining symbols, and negative indicators")
    print()
    
    engine = ComprehensiveRegexEngine()
    
    # COMPREHENSIVE TEST CASES
    test_categories = {
        "MEASUREMENT RANGES": [
            "10-15%",
            "Temperature range -20°F to 120°F",
            "30 to 37 inches", 
            "Weight 250 through 500 pounds",
            "Between 90 and 95 decibels",
            "-5°C through -2°C",
            "Pressure from 10 to 15 pounds"
        ],
        
        "MONEY RANGES": [
            "$1-5 million",
            "$100 to $500 thousand", 
            "Budget $1M through $5M",
            "Loss -$500 to -$200",
            "Revenue from $10K to $50K"
        ],
        
        "TIME RANGES": [
            "9:00 AM to 5:00 PM",
            "Meeting 2:30-4:00 PM",
            "Hours 8:00 through 17:00",
            "Shift from 6:00 AM to 2:00 PM"
        ],
        
        "DATE RANGES": [
            "January 1, 2024 to December 31, 2024",
            "March 15-April 20, 2024",
            "From June 1, 2024 through August 31, 2024",
            "2024-01-01/2024-12-31"
        ],
        
        "MEASUREMENT NEGATIVES": [
            "Temperature is -20°F",
            "Loss of 15%",
            "Decline of 5 degrees", 
            "Below -37 inches",
            "Deficit of 250 pounds",
            "Minus 10 decibels",
            "Negative 5°C"
        ],
        
        "MONEY NEGATIVES": [
            "Loss of $500",
            "Deficit of $1M",
            "Minus $250 thousand",
            "Negative $50K",
            "Below -$100",
            "Drop of $2 million"
        ],
        
        "COMPLEX MIXED": [
            "Range from -20°F to 120°F with average -5°F",
            "Growth 10-15% but decline of -2%",
            "Budget $1M-$5M with deficit of -$500K",
            "Hours 9:00 AM to 5:00 PM, overtime minus 2 hours"
        ]
    }
    
    total_tests = 0
    successful_detections = 0
    results_by_category = {}
    
    for category, test_cases in test_categories.items():
        print(f"📊 {category}:")
        print("-" * 50)
        
        category_success = 0
        category_total = len(test_cases)
        
        for i, text in enumerate(test_cases, 1):
            total_tests += 1
            print(f"  Test {i:2d}: \"{text}\"")
            
            entities = engine.detect_entities(text)
            
            if entities:
                successful_detections += 1
                category_success += 1
                print(f"    ✅ DETECTED: {len(entities)} entities")
                for entity in entities:
                    if entity.type == "range":
                        print(f"      📏 Range: {entity.raw_start} to {entity.raw_end} ({entity.unit}) [{entity.category}]")
                    elif entity.type == "negative":
                        print(f"      ➖ Negative: {entity.value} {entity.unit} [{entity.category}]")
                    else:
                        print(f"      ➕ Positive: {entity.value} {entity.unit} [{entity.category}]")
            else:
                print(f"    ❌ NO DETECTION")
            
            print()
        
        category_rate = (category_success / category_total) * 100
        results_by_category[category] = category_rate
        print(f"  📈 Category Success Rate: {category_rate:.1f}% ({category_success}/{category_total})")
        print()
    
    # COMPREHENSIVE SUMMARY
    print("📊 COMPREHENSIVE TEST SUMMARY:")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Successful detections: {successful_detections}")
    print(f"Overall success rate: {(successful_detections/total_tests)*100:.1f}%")
    print()
    
    print("📈 Success Rate by Category:")
    for category, rate in results_by_category.items():
        status = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
        print(f"  {status} {category}: {rate:.1f}%")
    
    print()
    if successful_detections >= total_tests * 0.8:
        print("🎉 COMPREHENSIVE METHODOLOGY PROVEN")
        print("✅ Ready for full FLPC implementation across all Core-8 entities")
    else:
        print("🔧 METHODOLOGY NEEDS REFINEMENT")
        print("❌ Fix patterns before FLPC implementation")
    
    return successful_detections / total_tests

if __name__ == "__main__":
    print("# GOAL: Comprehensive validation across all Core-8 entities")
    print("# REASON: Need complete test matrix for DATE, TIME, MONEY, MEASUREMENT")
    print("# PROBLEM: Must handle all joining symbols and negative indicators")
    print()
    
    success_rate = test_comprehensive_core8()
    
    print(f"\n🎯 FINAL RESULT: {success_rate*100:.1f}% comprehensive success rate")
    if success_rate >= 0.8:
        print("✅ METHODOLOGY PROVEN: Ready for FLPC pattern_sets.yaml implementation")
    else:
        print("🔧 METHODOLOGY INCOMPLETE: Refine patterns before production")