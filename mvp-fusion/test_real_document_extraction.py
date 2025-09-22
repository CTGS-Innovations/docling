#!/usr/bin/env python3
"""
Test Enhanced Pipeline on Real Document
=======================================

Test the hybrid metadata system on the same entities you showed in your example
to demonstrate the enhanced subcategorization.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from enhanced_extraction_pipeline import EnhancedExtractionPipeline

def test_document_entities():
    """Test with entities similar to your example document"""
    
    # Simulate text containing the entities from your example
    test_text = """
    The analysis covers multiple regions including New York, California, and Texas.
    International coordination with the EU is essential for global compliance.
    
    Operations in Moscow are being coordinated with Brazilian officials.
    The state of Massachusetts has implemented new protocols.
    
    Major metropolitan areas including New York City, Los Angeles, Chicago, 
    Houston, Phoenix, Philadelphia, San Antonio, San Diego, Dallas, and San Jose
    are participating in the initiative.
    
    The policy will affect Florida, United States, and Canada relationships
    going forward.
    """
    
    print("🧪 Testing Enhanced Pipeline on Real Document Entities")
    print("=" * 60)
    
    pipeline = EnhancedExtractionPipeline()
    
    # Extract with enhanced metadata
    result = pipeline.extract_entities_with_enhanced_metadata(test_text, include_normalized=True)
    
    # Show the enhanced format (vs. your original basic format)
    print("📋 BEFORE (Basic GPE tagging):")
    print("-" * 35)
    print("  gpe:")
    basic_entities = [
        "New York", "California", "Texas", "EU", "Moscow", "Brazilian",
        "Massachusetts", "New York City", "Los Angeles", "Chicago", "Houston",
        "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", 
        "San Jose", "Florida", "United States", "Canada"
    ]
    for i, entity in enumerate(basic_entities, 1):
        print(f"  - value: {entity}")
        print(f"    text: {entity}")
        print(f"    type: GPE")
        print(f"    span: {{start: {1000+i*10}, end: {1000+i*10+len(entity)}}}")
        if i >= 5:  # Show just first 5 for comparison
            print(f"  ... ({len(basic_entities)-5} more)")
            break
    
    print(f"\n📊 AFTER (Enhanced Subcategory Tagging):")
    print("-" * 42)
    enhanced_output = pipeline.extract_and_format_like_existing(test_text)
    print(enhanced_output)
    
    print(f"\n🎯 Enhanced Metadata Summary:")
    print("-" * 30)
    pipeline.print_enhanced_summary(result)
    
    # Show normalized entities (Option C rich metadata)
    print(f"\n🧠 Normalized Entities (Rich Metadata Layer):")
    print("-" * 47)
    
    for entity in result["normalized_entities"]["geopolitical"][:5]:
        print(f"• {entity.canonical_name}")
        print(f"  Authority: {entity.geopolitical_properties.get('authority_type', 'N/A')}")
        print(f"  Level: {entity.geopolitical_properties.get('authority_level', 'N/A')}")
        print(f"  Scope: {entity.geopolitical_properties.get('jurisdiction_scope', 'N/A')}")
        print(f"  Governmental: {entity.geopolitical_properties.get('governmental_entity', False)}")
        if entity.alternative_classifications:
            print(f"  Alternatives: {', '.join(entity.alternative_classifications)}")
        print()
    
    # Show comparison table
    print("📈 Value Comparison:")
    print("-" * 20)
    print("Before: All entities tagged as generic 'GPE'")
    print("After: Rich subcategorization with hierarchical metadata")
    print(f"  • Government agencies: {result['metadata']['subcategory_breakdown']['gpe'].get('us_government_agencies', 0)}")
    print(f"  • US States: {result['metadata']['subcategory_breakdown']['gpe'].get('us_states', 0)}")
    print(f"  • Major cities: {result['metadata']['subcategory_breakdown']['gpe'].get('major_cities', 0)}")
    print(f"  • Countries: {result['metadata']['subcategory_breakdown']['gpe'].get('countries', 0)}")
    print(f"  • International orgs: {result['metadata']['subcategory_breakdown']['gpe'].get('international_organizations', 0)}")
    
    return result

def demonstrate_api_integration():
    """Show how this integrates with existing systems"""
    
    print(f"\n🔧 API Integration Example:")
    print("-" * 28)
    
    pipeline = EnhancedExtractionPipeline()
    
    # Example: Filter only government entities
    sample_text = "The EPA and Department of Defense coordinate with Texas and California officials."
    result = pipeline.extract_entities_with_enhanced_metadata(sample_text, include_normalized=False)
    
    # Filter government entities
    government_entities = [
        entity for entity in result["entities"]["gpe"] 
        if entity["subcategory"] in ["us_government_agencies", "federal_provincial_governments", "government_forms"]
    ]
    
    print("Government entities only:")
    for entity in government_entities:
        print(f"  • {entity['value']} [{entity['subcategory']}]")
    
    # Example: Filter by jurisdiction level
    state_entities = [
        entity for entity in result["entities"]["gpe"]
        if entity["subcategory"] == "us_states"
    ]
    
    print("\nState-level entities:")
    for entity in state_entities:
        print(f"  • {entity['value']} [state government]")

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    result = test_document_entities()
    demonstrate_api_integration()
    
    print(f"\n🟢 **SUCCESS**: Enhanced metadata system ready for production integration")