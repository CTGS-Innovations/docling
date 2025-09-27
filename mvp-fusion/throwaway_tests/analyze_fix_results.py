#!/usr/bin/env python3
"""
GOAL: Compare measurement detection before vs after pipeline fix
REASON: Need to verify our fix improved measurement detection in production document
PROBLEM: Need to show quantitative improvement from pipeline fixes
"""

import re

def analyze_fix_results():
    """Analyze measurement detection improvement after pipeline fix"""
    print("📊 MEASUREMENT DETECTION ANALYSIS - AFTER FIX")
    print("=" * 60)
    
    # Read the newly processed document
    with open('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md', 'r') as f:
        new_content = f.read()
    
    # Find measurement section
    measurement_section_start = new_content.find('### 9.4 Measurements (20 measurements)')
    measurement_section_end = new_content.find('### ', measurement_section_start + 1)
    if measurement_section_end == -1:
        measurement_section_end = new_content.find('---', measurement_section_start)
    
    if measurement_section_start != -1:
        measurement_section = new_content[measurement_section_start:measurement_section_end]
        
        # Count tagged measurements (||value||id|| format)
        tagged_pattern = r'\|\|[^|]+\|\|[^|]+\|\|'
        tagged_matches = re.findall(tagged_pattern, measurement_section)
        print(f'✅ TAGGED measurements: {len(tagged_matches)}')
        
        # Show first 10 tagged measurements
        for i, match in enumerate(tagged_matches[:10], 1):
            print(f'   {i}. {match}')
        
        print()
        
        # Look for measurement patterns that should be tagged
        measurement_patterns = [
            r'\b\d+(?:\.\d+)?\s*(?:feet|ft|inches?|inch|cm|mm|meters?|metres?)',
            r'\b\d+(?:\.\d+)?\s*(?:pounds?|lbs?|kg)',
            r'\b\d+(?:\.\d+)?\s*(?:decibels?|dB)',
            r'\b\d+(?:\.\d+)?\s*(?:minutes?|hours?)',
            r'\b\d+(?:\.\d+)?°[FC]'
        ]
        
        all_measurements = []
        for pattern in measurement_patterns:
            matches = re.findall(pattern, measurement_section, re.IGNORECASE)
            all_measurements.extend(matches)
        
        print(f'🔍 POTENTIAL measurements found: {len(all_measurements)}')
        
        # Calculate success rate
        if len(all_measurements) > 0:
            success_rate = (len(tagged_matches) / len(all_measurements)) * 100
            print(f'📈 TAGGING SUCCESS RATE: {success_rate:.1f}%')
            
            # Compare to previous 13.9% rate
            previous_rate = 13.9
            improvement = success_rate - previous_rate
            
            print(f'📊 COMPARISON TO PREVIOUS:')
            print(f'   Previous rate: {previous_rate}%')
            print(f'   Current rate:  {success_rate:.1f}%')
            print(f'   Improvement:   +{improvement:.1f} percentage points')
            
            if success_rate > 50:
                print(f'🟢 **SUCCESS**: Significant improvement in measurement tagging!')
            elif success_rate > 20:
                print(f'🟡 **PARTIAL**: Some improvement but more work needed')
            else:
                print(f'🔴 **FAILED**: Tagging rate still too low')
        
        # Check specific test case
        print()
        print(f'🎯 SPECIFIC TEST: "30-37 inches"')
        if '30-37 inches' in measurement_section:
            print(f'✅ Found "30-37 inches" in section')
            
            # Check if it has entity tags
            range_context_start = measurement_section.find('30-37 inches') - 50
            range_context_end = measurement_section.find('30-37 inches') + 100
            range_context = measurement_section[max(0, range_context_start):range_context_end]
            
            tagged_in_context = re.findall(tagged_pattern, range_context)
            if tagged_in_context:
                print(f'🟢 **SUCCESS**: "30-37 inches" area has entity tags:')
                for tag in tagged_in_context:
                    print(f'   {tag}')
            else:
                print(f'🔴 **FAILED**: "30-37 inches" still not tagged')
                print(f'Context: {range_context}')
        else:
            print(f'❌ "30-37 inches" not found in measurement section')
        
        # Show the measurement section for direct inspection
        print()
        print(f'📋 MEASUREMENT SECTION PREVIEW:')
        print('-' * 40)
        lines = measurement_section.split('\n')
        for i, line in enumerate(lines[:15], 1):  # Show first 15 lines
            print(f'   {i:2d}. {line}')
    
    else:
        print('❌ Measurement section not found in document')

if __name__ == "__main__":
    analyze_fix_results()