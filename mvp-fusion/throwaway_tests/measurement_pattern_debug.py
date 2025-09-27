#!/usr/bin/env python3
"""
GOAL: Debug why FLPC measurement pattern misses 12+ out of 20 measurements
REASON: User reported only 8/20 measurements detected - need to test pattern against source text
PROBLEM: FLPC pattern not matching measurements like "6 feet", "42 inches", "4 inches", etc.
"""

import re
import sys
import os

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_measurement_patterns():
    """Test measurement pattern against all 20 measurements from source document"""
    
    # Current FLPC pattern from pattern_sets.yaml
    flpc_pattern = r'(?i)\b-?\d+(?:\.\d+)?\s*(?:mg|g|kg|µg|tons?|tonnes?|pounds?|lbs?|oz|ml|l|liters?|litres?|gal|gallons?|ft|feet|in(?:ch|ches)?|meters?|metres?|m|cm|mm|km|mi|mph|kph|km/h|m/s|fps|yd|yards?|°C|°F|degC|degF|degrees?|K|seconds?|secs?|s|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|ms|µs|ns|psi|bar|Pa|kPa|MPa|atm|torr|mmHg|J|kJ|cal|kcal|W|kW|MW|HP|BTU|eV|V|A|mA|Ω|Wh|kWh|F|H|S|C|T|B|KB|MB|GB|TB|Hz|kHz|MHz|GHz|THz|ppm|ppb|mg/L|g/L|mol/L|M|%|percent|bps|basis\s+points|m²|cm²|km²|acre|hectare|ha|N|N·m|ft·lbf|L/100km|Gy|Sv|Bq|Ci|dB|decibels?)'
    
    # Test measurements from source document (expected 20 total)
    measurements_text = """
Fall protection required above **6 feet** (1.8 meters) in construction
Guardrails must be **42 inches** (107 cm) high
Toe boards minimum **4 inches** (10 cm) high
Safety nets within **30 feet** (9.1 meters)
Ladder side rails extend **3 feet** (0.9 meters)
Stairway width minimum **22 inches** (56 cm)
Handrail height **30-37 inches** (76-94 cm)
Landing depth **30 inches** (76 cm) minimum
Riser height maximum **9.5 inches** (24 cm)
Tread depth minimum **9.5 inches** (24 cm)
Door swing clearance **20 inches** (51 cm)
Scaffold width minimum **18 inches** (46 cm)
Clearance from power lines **10 feet** (3 meters)
Excavation depth requiring protection **5 feet** (1.5 meters)
Noise exposure limit **90 decibels** for 8 hours
Weight capacity **250 pounds** (113 kg) per person
Temperature range **-20°F to 120°F** (-29°C to 49°C)
Visibility distance **500 feet** (152 meters)
Response time **15 minutes** maximum
Storage height limit **15 feet** (4.6 meters)
"""
    
    print("🔍 MEASUREMENT PATTERN DEBUG")
    print("=" * 50)
    print(f"Pattern: {flpc_pattern}")
    print("\n📊 TESTING AGAINST SOURCE TEXT:")
    print("-" * 30)
    
    # Find all matches
    matches = re.findall(flpc_pattern, measurements_text)
    print(f"✅ Total matches found: {len(matches)}")
    
    if matches:
        print("\n🎯 DETECTED MEASUREMENTS:")
        for i, match in enumerate(matches, 1):
            print(f"{i:2d}. {match}")
    
    # Manual analysis - extract all number+unit patterns manually
    print("\n🔍 MANUAL ANALYSIS - Expected measurements:")
    manual_pattern = r'(\*\*)?(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*([a-zA-Z°]+)(\*\*)?'
    manual_matches = re.findall(manual_pattern, measurements_text)
    
    expected_measurements = []
    for match in manual_matches:
        number = match[1]
        unit = match[2]
        if unit.lower() in ['feet', 'inches', 'cm', 'meters', 'kg', 'pounds', 'decibels', 'minutes', 'f', 'c']:
            expected_measurements.append(f"{number} {unit}")
    
    print(f"📋 Expected measurements ({len(expected_measurements)}):")
    for i, meas in enumerate(expected_measurements, 1):
        print(f"{i:2d}. {meas}")
    
    # Find what's missing
    detected_set = set(matches)
    expected_set = set([m.split()[1] for m in expected_measurements])  # Just units
    
    print(f"\n❌ MISSING DETECTIONS:")
    print(f"Expected units: {sorted(expected_set)}")
    print(f"Detected units: {sorted(detected_set)}")
    
    # Test specific problematic cases
    test_cases = [
        "6 feet",
        "42 inches", 
        "4 inches",
        "30 feet",
        "3 feet",
        "22 inches",
        "90 decibels",
        "250 pounds",
        "15 minutes",
        "500 feet",
        "15 feet"
    ]
    
    print(f"\n🧪 TESTING SPECIFIC CASES:")
    pattern_compiled = re.compile(flpc_pattern)
    for case in test_cases:
        match = pattern_compiled.search(case)
        status = "✅" if match else "❌"
        print(f"{status} '{case}' -> {match.group() if match else 'NO MATCH'}")

if __name__ == "__main__":
    test_measurement_patterns()