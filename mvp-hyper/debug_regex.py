#!/usr/bin/env python3
"""Debug regex patterns in config file."""

import yaml
import re

# Load config and test each pattern
with open('pipeline-config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print("Testing universal entity patterns...")

patterns = config['pipeline']['tier2_pretagger']['universal_entities']

for entity_type, pattern_str in patterns.items():
    print(f"\nTesting {entity_type}:")
    print(f"Pattern: {pattern_str}")
    print(f"Length: {len(pattern_str)}")
    try:
        compiled = re.compile(pattern_str, re.I)
        print("✅ Pattern compiles successfully")
    except re.error as e:
        print(f"❌ Regex error: {e}")
        print(f"Error at position: {getattr(e, 'pos', 'unknown')}")