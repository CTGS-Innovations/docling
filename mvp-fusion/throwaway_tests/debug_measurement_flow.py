#!/usr/bin/env python3
"""
GOAL: Debug measurement flow from FLPC extraction to normalization
REASON: FLPC detects measurements but they're not appearing in final output
PROBLEM: Need to trace where measurements are being lost in the pipeline
"""

import yaml
import time
from fusion.flpc_engine import FLPCEngine

# Test text from the document
test_text = """
Fall protection required above 6 feet in construction.
Guardrails must be 42 inches high.
Toe boards minimum 4 inches high.
Safety nets within 30 feet.
Noise exposure limit 90 decibels for 8 hours.
Weight capacity 250 pounds per person.
Temperature range -20°F to 120°F.
Response time 15 minutes maximum.
Storage height limit 15 feet maximum.
"""

print("🔍 DEBUGGING MEASUREMENT FLOW")
print("=" * 50)

# Step 1: Test FLPC extraction
print("1️⃣ FLPC EXTRACTION:")
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

flpc_engine = FLPCEngine(config)
flpc_results = flpc_engine.extract_entities(test_text)
flpc_measurements = flpc_results.get('entities', {}).get('MEASUREMENT', [])

print(f"   FLPC found {len(flpc_measurements)} measurements:")
for i, m in enumerate(flpc_measurements, 1):
    print(f"   {i}. {repr(m)}")

print()

# Step 2: Test entity conversion (simulate service processor)
print("2️⃣ ENTITY CONVERSION:")
def convert_flpc_entities(flpc_matches, entity_type):
    """Simulate service processor conversion"""
    entities = []
    for match in flpc_matches:
        if isinstance(match, dict):
            entity = {
                'value': match.get('text', ''),
                'text': match.get('text', ''),
                'type': entity_type,
                'span': {
                    'start': match.get('start', 0),
                    'end': match.get('end', 0)
                }
            }
            entities.append(entity)
        elif isinstance(match, str):
            entity = {
                'value': match,
                'text': match,
                'type': entity_type,
                'span': {'start': 0, 'end': len(match)}
            }
            entities.append(entity)
    return entities

converted_measurements = convert_flpc_entities(flpc_measurements, 'MEASUREMENT')
print(f"   Converted {len(converted_measurements)} measurements:")
for i, m in enumerate(converted_measurements, 1):
    print(f"   {i}. {m}")

print()

# Step 3: Test what goes to normalization
print("3️⃣ ENTITIES SENT TO NORMALIZATION:")
entities = {'measurement': converted_measurements}
print(f"   entities['measurement'] has {len(entities['measurement'])} items")

print()
print("🔬 CONCLUSION:")
if len(flpc_measurements) > 0:
    print("✅ FLPC is detecting measurements correctly")
if len(converted_measurements) > 0:
    print("✅ Entity conversion is working correctly")
if len(entities['measurement']) > 0:
    print("✅ Measurements are being sent to normalization")
    print("🔴 ISSUE: Problem must be IN the normalization phase")
else:
    print("❌ Measurements are being lost before normalization")