#!/usr/bin/env python3
"""
Standalone Semantic Extraction Test
===================================
Direct test of semantic fact extraction from markdown files
Eliminates pipeline complexity to debug knowledge extraction
"""

import sys
import json
from pathlib import Path
import yaml

# Add current directory to path for imports
sys.path.append('.')

from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor

def parse_markdown_yaml(markdown_content: str):
    """Parse YAML front matter from markdown content"""
    if markdown_content.strip().startswith('---'):
        parts = markdown_content.split('---', 2)
        if len(parts) >= 3:
            try:
                yaml_content = parts[1].strip()
                markdown_text = parts[2].strip()
                yaml_data = yaml.safe_load(yaml_content)
                return yaml_data or {}, markdown_text
            except yaml.YAMLError as e:
                print(f"❌ YAML parsing error: {e}")
                return {}, markdown_content
    
    print("⚠️  No YAML front matter found")
    return {}, markdown_content

def test_semantic_extraction(markdown_file_path: str):
    """Test semantic extraction on a single markdown file"""
    print(f"🧪 STANDALONE SEMANTIC EXTRACTION TEST")
    print(f"📄 Testing file: {markdown_file_path}")
    print("=" * 80)
    
    # Read the markdown file
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"📊 File size: {len(markdown_content)} characters")
    
    # Parse YAML and markdown sections
    yaml_data, markdown_text = parse_markdown_yaml(markdown_content)
    print(f"📄 YAML data keys: {list(yaml_data.keys())}")
    print(f"📝 Markdown text: {len(markdown_text)} characters")
    
    # Extract classification entities
    classification = yaml_data.get('classification', {})
    entities_section = classification.get('entities', {})
    global_entities = entities_section.get('global_entities', {})
    domain_entities = entities_section.get('domain_entities', {})
    
    print(f"\n🔍 ENTITY ANALYSIS:")
    print(f"   📊 Global entity types: {list(global_entities.keys())}")
    print(f"   🎯 Domain entity types: {list(domain_entities.keys())}")
    
    # Count entities
    global_count = 0
    for entity_type, entities in global_entities.items():
        if isinstance(entities, list):
            count = len(entities)
            global_count += count
            print(f"      - global_{entity_type}: {count} entities")
    
    domain_count = 0  
    for entity_type, entities in domain_entities.items():
        if isinstance(entities, list):
            count = len(entities)
            domain_count += count
            print(f"      - domain_{entity_type}: {count} entities")
    
    print(f"   📈 Total entities: {global_count + domain_count} ({global_count} global + {domain_count} domain)")
    
    # Test semantic fact extraction
    print(f"\n🧠 SEMANTIC FACT EXTRACTION:")
    try:
        extractor = SemanticFactExtractor()
        
        # Use the new parallel processing method
        semantic_facts = extractor.extract_semantic_facts_from_classification(
            classification_data=classification,
            markdown_content=markdown_text
        )
        
        print(f"✅ Semantic extraction completed!")
        print(f"📊 Semantic facts structure: {list(semantic_facts.keys())}")
        
        semantic_summary = semantic_facts.get('semantic_summary', {})
        total_facts = semantic_summary.get('total_facts', 0)
        fact_types = semantic_summary.get('fact_types', {})
        
        print(f"📈 Total semantic facts: {total_facts}")
        print(f"📋 Fact type breakdown:")
        for fact_type, count in fact_types.items():
            print(f"      - {fact_type}: {count} facts")
        
        # Generate JSON knowledge file for testing
        file_stem = Path(markdown_file_path).stem
        json_output_path = f"{file_stem}_knowledge_test.json"
        
        knowledge_data = {
            'test_info': {
                'source_file': markdown_file_path,
                'test_timestamp': semantic_summary.get('timestamp', ''),
                'extraction_engine': semantic_summary.get('extraction_engine', '')
            },
            'entity_summary': {
                'global_entities_count': global_count,
                'domain_entities_count': domain_count,
                'total_entities': global_count + domain_count
            },
            'semantic_facts': semantic_facts.get('semantic_facts', {}),
            'normalized_entities': semantic_facts.get('normalized_entities', {}),
            'semantic_summary': semantic_summary
        }
        
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Generated test JSON: {json_output_path}")
        print(f"✅ Test completed successfully!")
        
        return semantic_facts
        
    except Exception as e:
        print(f"❌ Semantic extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with the OSHA stairways document
    test_file = "/home/corey/projects/docling/output/fusion/3124-stairways-and-ladders.md"
    
    print("🧪 STANDALONE SEMANTIC EXTRACTION TEST")
    print("=" * 80)
    
    result = test_semantic_extraction(test_file)
    
    if result:
        print(f"\n🎉 SUCCESS: Extracted {result.get('semantic_summary', {}).get('total_facts', 0)} semantic facts")
    else:
        print(f"\n❌ FAILED: Could not extract semantic facts")