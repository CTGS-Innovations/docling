#!/usr/bin/env python3
"""
Test Integrated Person Extraction System
========================================
Quick test to verify the conservative person extractor integration with semantic fact extraction.
"""

import sys
from pathlib import Path
import yaml

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from utils.logging_config import setup_logging, get_fusion_logger
from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor

def test_integrated_person_extraction():
    """Test the integrated conservative person extraction system"""
    
    # Setup logging
    setup_logging(verbosity=2)
    logger = get_fusion_logger(__name__)
    
    logger.stage("🧪 Testing Integrated Conservative Person Extraction")
    
    # Load config
    config_path = Path("config/config.yaml")
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    # Initialize semantic extractor with config
    extractor = SemanticFactExtractor(config)
    
    # Test text with various person scenarios
    test_text = """---
classification:
  universal_entities:
    person:
      - value: "Dr. Smith"
        span: {start: 0, end: 9}
        type: "person"
      - value: "Ford"
        span: {start: 50, end: 54}
        type: "person"
      - value: "John Doe"
        span: {start: 100, end: 108}
        type: "person"
      - value: "Apple"
        span: {start: 150, end: 155}
        type: "person"
    organization:
      - value: "OSHA"
        span: {start: 200, end: 204}
        type: "organization"
---

# Test Document

Dr. Smith announced new safety regulations yesterday. Ford Motor Company 
released a statement. John Doe, CEO of TechCorp, spoke at the conference.
Apple Inc. reported quarterly earnings. OSHA requires compliance with 
all safety standards.

The researcher, Professor Jane Wilson, published findings on workplace 
safety. Microsoft CEO Satya Nadella discussed technology trends. Walt Disney
founded Disney Studios in 1923. Tim Cook, Apple's CEO, presented the 
new iPhone models.
"""

    logger.stage("📝 Extracting semantic facts from test document...")
    
    # Extract semantic facts (includes conservative person validation)
    results = extractor.extract_semantic_facts(test_text)
    
    # Display results
    logger.stage("\n📊 EXTRACTION RESULTS:")
    
    # Show semantic summary
    summary = results.get('semantic_summary', {})
    logger.stage(f"   Total facts: {summary.get('total_facts', 0)}")
    logger.stage(f"   Fact types: {summary.get('fact_types', {})}")
    
    # Show conservative person facts specifically
    semantic_facts = results.get('semantic_facts', {})
    if 'conservative_persons' in semantic_facts:
        persons = semantic_facts['conservative_persons']
        logger.stage(f"\n👥 CONSERVATIVE PERSON FACTS ({len(persons)}):")
        
        for i, person in enumerate(persons, 1):
            logger.stage(f"   {i}. {person.get('person_name', 'Unknown')}")
            logger.stage(f"      Confidence: {person.get('confidence', 0):.3f}")
            logger.stage(f"      Role: {person.get('role_context', 'None')}")
            logger.stage(f"      Organization: {person.get('organization_affiliation', 'None')}")
            logger.stage(f"      Evidence: {person.get('validation_evidence', [])}")
            logger.stage(f"      Ambiguity Score: {person.get('ambiguity_score', 0):.3f}")
    else:
        logger.stage("\n👥 No conservative person facts extracted")
    
    # Show person-related facts from YAML promotion
    yaml_person_types = [k for k in semantic_facts.keys() if 'person' in k.lower()]
    if yaml_person_types:
        logger.stage(f"\n📋 YAML PERSON FACTS:")
        for fact_type in yaml_person_types:
            facts = semantic_facts[fact_type]
            logger.stage(f"   {fact_type}: {len(facts)} facts")
            
            for i, fact in enumerate(facts[:3], 1):  # Show first 3
                logger.stage(f"      {i}. {fact.get('person_name', fact.get('canonical_name', 'Unknown'))}")
                logger.stage(f"         Validation: {fact.get('conservative_validation', 'N/A')}")
                logger.stage(f"         Confidence: {fact.get('confidence', 0):.3f}")
                if fact.get('validation_failure_reason'):
                    logger.stage(f"         Failure: {fact.get('validation_failure_reason')}")
    
    # Show normalized entities
    normalized = results.get('normalized_entities', {})
    if normalized:
        logger.stage(f"\n🔄 NORMALIZED ENTITIES ({len(normalized)}):")
        for entity, info in list(normalized.items())[:5]:  # Show first 5
            logger.stage(f"   {entity}: {info.get('canonical_name', 'Unknown')}")
    
    return results

def test_person_extractor_standalone():
    """Test the person extractor independently"""
    logger = get_fusion_logger(__name__)
    
    logger.stage("\n🔬 Testing Standalone Person Extractor")
    
    try:
        from utils.person_entity_extractor import PersonEntityExtractor
        
        # Initialize with sample data
        extractor = PersonEntityExtractor(min_confidence=0.7)
        
        # Add sample names for testing
        extractor.first_names = {'john', 'jane', 'tim', 'walt', 'satya'}
        extractor.last_names = {'doe', 'smith', 'cook', 'disney', 'nadella'}
        extractor.organizations = {'apple', 'microsoft', 'ford', 'disney'}
        
        test_text = """
        Dr. Smith announced new findings. Ford reported earnings.
        John Doe, CEO of TechCorp, spoke yesterday. Apple released
        new products. Tim Cook presented at the conference.
        Walt Disney founded Disney Studios. Satya Nadella discussed AI.
        """
        
        persons = extractor.extract_persons(test_text)
        
        logger.stage(f"   Found {len(persons)} persons:")
        for person in persons:
            logger.stage(f"      {person['text']} (confidence: {person['confidence']:.3f})")
            logger.stage(f"         Evidence: {person.get('evidence', [])}")
        
        return persons
        
    except ImportError as e:
        logger.logger.error(f"❌ Person extractor not available: {e}")
        return []

if __name__ == "__main__":
    print("="*60)
    print("INTEGRATED PERSON EXTRACTION TEST")
    print("="*60)
    
    # Test standalone person extractor
    standalone_results = test_person_extractor_standalone()
    
    # Test integrated system
    integrated_results = test_integrated_person_extraction()
    
    print("\n" + "="*60)
    print("✅ Test completed! Check the logs above for results.")
    print("="*60)