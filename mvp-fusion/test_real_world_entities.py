#!/usr/bin/env python3
"""
Real World Entity Metadata Testing
==================================

Test enhanced entity extraction on realistic business/government content
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from enhanced_entity_metadata_extractor import EnhancedEntityExtractor

def test_government_document():
    """Test with government document style content"""
    
    text = """
    DEPARTMENT OF LABOR NOTICE
    
    The Occupational Safety and Health Administration (OSHA) and the Environmental
    Protection Agency (EPA) announce new joint regulations affecting workplace safety
    in California, Texas, Florida, and New York. The Department of Homeland Security
    (DHS) will coordinate with the Federal Bureau of Investigation (FBI) and Central
    Intelligence Agency (CIA) on implementation.
    
    Regional offices in Los Angeles, Houston, Miami, Chicago, and Boston will handle
    coordination. The United Nations Environmental Programme and NATO standards will
    be incorporated. International cooperation with Canada, Mexico, the United Kingdom,
    and European Union representatives is expected.
    
    Geographic coverage includes the Rocky Mountains region, Great Lakes area, 
    Mississippi River basin, Appalachian Mountains, Pacific Coast, Atlantic Ocean
    coastal zones, Gulf of Mexico regions, and Yellowstone National Park boundaries.
    """
    
    print("🧪 Testing Government Document Content")
    print("=" * 60)
    
    extractor = EnhancedEntityExtractor()
    entities = extractor.extract_entities_with_metadata(text)
    
    extractor.print_structured_summary(entities)
    print(f"\n📋 Found {len(entities)} entities with subcategory metadata")
    
    return entities

def test_business_document():
    """Test with business document style content"""
    
    text = """
    CORPORATE EXPANSION REPORT
    
    Our analysis covers operations across North America, including major markets
    in California, Texas, New York, Illinois, and Florida. European expansion
    targets include Germany, France, United Kingdom, Italy, and Spain.
    
    Key metropolitan areas include New York City, Los Angeles, Chicago, Houston,
    Philadelphia, Phoenix, San Antonio, San Diego, Dallas, and San Jose.
    
    Supply chain routes utilize the Pacific Ocean shipping lanes, Atlantic Ocean
    corridors, Mississippi River transport, Great Lakes shipping, and Rocky Mountains
    overland routes. Strategic locations near Lake Superior, Lake Michigan, 
    Colorado River, Columbia River, and Amazon River provide logistics advantages.
    
    Protected environmental areas including Yellowstone National Park, Grand Canyon
    National Park, Yosemite National Park, and Everglades National Park may impact
    development plans in the western United States regions.
    """
    
    print("\n🏢 Testing Business Document Content")
    print("=" * 60)
    
    extractor = EnhancedEntityExtractor()
    entities = extractor.extract_entities_with_metadata(text)
    
    extractor.print_structured_summary(entities)
    print(f"\n📋 Found {len(entities)} entities with subcategory metadata")
    
    return entities

def analyze_coverage_gaps(entities_list):
    """Analyze coverage and identify potential gaps"""
    
    print("\n🔍 Coverage Analysis")
    print("=" * 40)
    
    all_entities = []
    for entities in entities_list:
        all_entities.extend(entities)
    
    # Count by type and subcategory
    gpe_subcategories = set()
    loc_subcategories = set()
    
    for entity in all_entities:
        if entity.entity_type == "GPE":
            gpe_subcategories.add(entity.subcategory)
        elif entity.entity_type == "LOC":
            loc_subcategories.add(entity.subcategory)
    
    print(f"📊 GPE subcategories covered: {len(gpe_subcategories)}")
    for subcat in sorted(gpe_subcategories):
        count = sum(1 for e in all_entities if e.entity_type == "GPE" and e.subcategory == subcat)
        print(f"   - {subcat}: {count} entities")
    
    print(f"\n🌍 LOC subcategories covered: {len(loc_subcategories)}")
    for subcat in sorted(loc_subcategories):
        count = sum(1 for e in all_entities if e.entity_type == "LOC" and e.subcategory == subcat)
        print(f"   - {subcat}: {count} entities")
    
    # Check for overlaps (same entity detected in multiple subcategories)
    entity_texts = {}
    for entity in all_entities:
        text = entity.text.lower()
        if text not in entity_texts:
            entity_texts[text] = []
        entity_texts[text].append(f"{entity.entity_type}:{entity.subcategory}")
    
    overlaps = {text: cats for text, cats in entity_texts.items() if len(cats) > 1}
    
    if overlaps:
        print(f"\n⚠️ Entity Overlaps Found ({len(overlaps)} entities):")
        for text, categories in overlaps.items():
            print(f"   '{text}' → {', '.join(categories)}")
    else:
        print(f"\n✅ No overlapping entity classifications detected")

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    print("🟡 **WAITING**: Running comprehensive entity metadata tests...")
    
    # Test different document types
    gov_entities = test_government_document()
    biz_entities = test_business_document()
    
    # Analyze overall coverage
    analyze_coverage_gaps([gov_entities, biz_entities])
    
    print(f"\n🟢 **SUCCESS**: Comprehensive testing completed")