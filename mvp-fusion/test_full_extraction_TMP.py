#!/usr/bin/env python3
"""Test comprehensive entity extraction on full OSHA document"""

import sys
sys.path.insert(0, 'knowledge/extractors')
from comprehensive_entity_extractor import ComprehensiveEntityExtractor

# Read the full OSHA document
with open('/home/corey/projects/docling/output/fusion/3124-stairways-and-ladders.md', 'r') as f:
    content = f.read()

# Extract just the document content (after the YAML headers)
content_start = content.find('# 3124-stairways-and-ladders.pdf')
if content_start != -1:
    osha_content = content[content_start:]
else:
    osha_content = content

print(f'Document length: {len(osha_content)} characters')
print(f'Processing with FLPC Rust regex...')

# Extract comprehensive entities
extractor = ComprehensiveEntityExtractor()
results = extractor.extract_all_entities(osha_content)

print('\n=== COMPREHENSIVE ENTITY EXTRACTION FROM FULL OSHA DOCUMENT ===')
print(f'Total entities extracted: {results["summary"]["total_entities"]}')
print(f'Entity breakdown: {results["summary"]["entity_types"]}')

# Show financial entities
financial_items = results["entities"]["financial"]
print(f'\n💰 FINANCIAL DATA ({len(financial_items)} items):')
for item in financial_items[:5]:  # Show first 5
    print(f'   {item["amount"]} ({item["currency"]}) = ${item["normalized"]:,.2f}')

# Show percentages  
percentage_items = results["entities"]["percentages"]
print(f'\n📊 PERCENTAGES ({len(percentage_items)} items):')
for item in percentage_items:
    trend_text = f' {item["trend"]}' if item["trend"] else ''
    print(f'   {item["value"]}% of {item["subject"]}{trend_text}')

# Show measurements
measurement_items = results["entities"]["measurements"]
print(f'\n📏 MEASUREMENTS ({len(measurement_items)} items):')
for item in measurement_items[:10]:  # Show first 10
    pair_info = f' (paired with {item["pair"]})' if item['pair'] else ''
    print(f'   {item["value"]} {item["unit"]} ({item["category"]}){pair_info}')

# Show organizations
org_items = results["entities"]["organizations"]
print(f'\n🏢 ORGANIZATIONS ({len(org_items)} items):')
for item in org_items:
    acronym_info = f' ({item["acronym"]})' if item['acronym'] else ''
    print(f'   {item["name"]} [{item["type"]}]{acronym_info}')

# Show regulations
reg_items = results["entities"]["regulations"]
print(f'\n📜 REGULATIONS ({len(reg_items)} items):')
for item in reg_items:
    print(f'   {item["id"]} ({item["type"]})')

print(f'\n✅ Complete entity extraction using 100% FLPC Rust regex!')
print(f'🚀 Engine: {results["summary"]["extraction_engine"]}')
print(f'⏰ Processed at: {results["summary"]["timestamp"]}')