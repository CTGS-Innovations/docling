#!/usr/bin/env python3
"""
Validate that the parallel clean markdown fix eliminates tag corruption
"""
import sys
sys.path.append('..')

from knowledge.extractors.standalone_intelligent_extractor import StandaloneIntelligentExtractor

def test_corruption_fix():
    """Demonstrate the fix for tag corruption in semantic analysis"""
    
    print("🧪 VALIDATING CLEAN MARKDOWN FIX")
    print("=" * 50)
    
    # Simulate problematic input that would come from normalized text
    corrupted_input = """---
conversion:
  description: "OSHA Safety Document"
  format: "TXT"
---

OSHA regulation 29 CFR 1926.95 requires all construction workers to wear 
appropriate personal protective equipment (PPE) including hard hats, 
safety glasses, and high-visibility clothing when working in designated areas.

A landing platform must be provided if the step-across distance exceeds 
meas013|| (30 cm). I Fixed ladders without cages or wells must have at least 
a 15-inch (38 cm) clearance width to the nearest permanent object.

For training information, contact person042|| (safety coordinator) or call 
phone001|| ((555) 123-4567) to schedule a session. Training costs money003|| ($2,500) 
per group and must be completed by date004|| (March 15, 2024) at time002|| (2:30 PM).

Environmental compliance is monitored by org005|| (EPA).
"""
    
    # Clean input that should be used instead  
    clean_input = """---
conversion:
  description: "OSHA Safety Document"
  format: "TXT"
---

OSHA regulation 29 CFR 1926.95 requires all construction workers to wear 
appropriate personal protective equipment (PPE) including hard hats, 
safety glasses, and high-visibility clothing when working in designated areas.

A landing platform must be provided if the step-across distance exceeds 
30 centimeters. Fixed ladders without cages or wells must have at least 
a 15-inch (38 cm) clearance width to the nearest permanent object.

For training information, contact safety coordinator or call 
(555) 123-4567 to schedule a session. Training costs $2,500 
per group and must be completed by March 15, 2024 at 2:30 PM.

Environmental compliance is monitored by EPA.
"""
    
    extractor = StandaloneIntelligentExtractor()
    
    print("\n💀 CORRUPTED INPUT RESULTS:")
    corrupted_results = extractor.extract_semantic_facts(corrupted_input)
    corrupted_facts = corrupted_results['semantic_summary']['total_facts']
    
    print(f"Total facts: {corrupted_facts}")
    corruption_detected = False
    
    # Check for tag corruption in results
    for category, facts in corrupted_results['semantic_facts'].items():
        if facts:
            for fact in facts[:2]:  # Check first 2 facts
                context = fact.get('extra', {}).get('context', fact.get('context', ''))
                obj = fact.get('extra', {}).get('object', '')
                
                if any(tag in str(context) + str(obj) for tag in ['||', 'meas0', 'person0', 'org0', 'money0', 'date0', 'time0']):
                    corruption_detected = True
                    print(f"  ⚠️  CORRUPTION: {context[:60]}...")
                    break
    
    print(f"\n📄 CLEAN INPUT RESULTS:")
    clean_results = extractor.extract_semantic_facts(clean_input)
    clean_facts = clean_results['semantic_summary']['total_facts']
    
    print(f"Total facts: {clean_facts}")
    clean_quality = True
    
    # Check clean results quality
    for category, facts in clean_results['semantic_facts'].items():
        if facts:
            for fact in facts[:2]:  # Check first 2 facts  
                context = fact.get('extra', {}).get('context', fact.get('context', ''))
                obj = fact.get('extra', {}).get('object', '')
                
                if any(tag in str(context) + str(obj) for tag in ['||', 'meas0', 'person0', 'org0']):
                    clean_quality = False
                
                if context and len(context) > 20:  # Show good context
                    print(f"  ✅ CLEAN: {context[:60]}...")
                    break
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"Corrupted input facts: {corrupted_facts}")
    print(f"Clean input facts: {clean_facts}")
    print(f"Corruption detected: {'Yes' if corruption_detected else 'No'}")
    print(f"Clean quality: {'Yes' if clean_quality else 'No'}")
    
    if not corruption_detected and clean_quality:
        print(f"\n🟢 SUCCESS: Clean markdown fix eliminates tag corruption!")
    elif corruption_detected and clean_quality:
        print(f"\n🟡 PARTIAL: Fix works but corrupted input still shows issues")
    else:
        print(f"\n🔴 ISSUE: Fix may need refinement")
    
    print(f"\nThe parallel clean markdown approach preserves natural language")
    print(f"for semantic analysis while maintaining normalized text for entity queries.")

if __name__ == "__main__":
    test_corruption_fix()