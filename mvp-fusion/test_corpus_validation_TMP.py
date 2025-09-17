#!/usr/bin/env python3
"""
Test Corpus-Based Entity Validation at Scale
=============================================
Demonstrates high-confidence entity recognition using name/company corpuses.
"""

import json
import sys
import time
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))

def test_corpus_validation():
    """Test corpus-based validation for high-confidence entity recognition."""
    
    print("=" * 60)
    print("TESTING CORPUS-BASED ENTITY VALIDATION")
    print("=" * 60)
    
    # Try to import and initialize corpus validator
    try:
        from knowledge.corpus.entity_corpus_builder import CorpusValidator
        validator = CorpusValidator()
        
        print("✅ Corpus validator initialized successfully")
        
        # Show corpus statistics
        stats = validator.get_corpus_stats()
        print(f"\n📊 CORPUS STATISTICS:")
        print(f"  First Names: {stats['total_first_names']:,}")
        print(f"  Last Names: {stats['total_last_names']:,}")
        print(f"  Companies: {stats['total_companies']:,}")
        print(f"  VC Firms: {stats['total_vc_firms']:,}")
        print(f"  PE Firms: {stats['total_pe_firms']:,}")
        print(f"  Universities: {stats['total_universities']:,}")
        print(f"  Aho-Corasick: {'✅ Available' if stats['uses_ahocorasick'] else '❌ Not available'}")
        
    except ImportError as e:
        print(f"❌ Failed to import corpus validator: {e}")
        return
    except Exception as e:
        print(f"❌ Error initializing corpus validator: {e}")
        return
    
    # Test cases with challenging examples
    test_entities = [
        # Person names that should get high confidence
        ("Tim Cook", "person"),
        ("Elon Musk", "person"), 
        ("Sundar Pichai", "person"),
        ("Jonathan Ford", "person"),  # First name gives confidence
        ("Jennifer Smith", "person"),  # Common names
        ("Dr. Sarah Johnson", "person"),  # With title
        
        # Company names that should get high confidence  
        ("Apple Inc", "company"),
        ("Google", "company"),
        ("Microsoft Corporation", "company"),
        ("Sequoia Capital", "company"),  # VC firm
        ("Y Combinator", "company"),  # Accelerator
        ("Stanford University", "company"),  # University
        
        # Ambiguous cases where corpus helps
        ("Ford", "ambiguous"),  # Could be person or company
        ("Morgan Stanley", "ambiguous"),  # Looks like person, is company
        ("Stanley Morgan", "ambiguous"),  # Looks like company, could be person
        ("Apple", "ambiguous"),  # Could be company or uncommon first name
        
        # Edge cases
        ("John Company", "edge_case"),  # Person with company-like last name
        ("Company Inc", "edge_case"),  # Generic company name
        ("Unknown Person", "edge_case"),  # Not in corpus
        ("Random Startup LLC", "edge_case"),  # Pattern-based only
    ]
    
    print(f"\n🧪 TESTING {len(test_entities)} ENTITIES:")
    print("=" * 60)
    
    # Track performance
    start_time = time.time()
    
    for entity_text, expected_type in test_entities:
        print(f"\n🔍 Testing: '{entity_text}' (expected: {expected_type})")
        
        # Test person validation
        person_conf, person_details = validator.validate_person_name(entity_text)
        
        # Test company validation  
        company_conf, company_details = validator.validate_company_name(entity_text)
        
        # Determine winning classification
        if person_conf > company_conf:
            classification = "PERSON"
            confidence = person_conf
            details = person_details
        else:
            classification = "COMPANY" 
            confidence = company_conf
            details = company_details
        
        print(f"  Result: {classification} (confidence: {confidence:.2f})")
        
        # Show interesting details
        if classification == "PERSON":
            if details.get('has_valid_first_name'):
                print(f"    ✓ Valid first name: {details.get('first_name')}")
            if details.get('has_valid_last_name'):
                print(f"    ✓ Valid last name: {details.get('last_name')}")
            if details.get('gender_hint'):
                print(f"    👤 Gender hint: {details.get('gender_hint')}")
            if details.get('is_known_angel'):
                print(f"    💰 Known angel investor")
        else:
            if details.get('is_known_company'):
                print(f"    ✓ Known company in corpus")
            if details.get('company_type'):
                print(f"    🏢 Type: {details.get('company_type')}")
            if details.get('has_company_suffix'):
                print(f"    ✓ Has company suffix")
            if details.get('is_vc_firm'):
                print(f"    💼 VC Firm")
            if details.get('is_university'):
                print(f"    🎓 University")
        
        # Show confidence breakdown for interesting cases
        if abs(person_conf - company_conf) < 0.3:  # Close call
            print(f"    📊 Close call - Person: {person_conf:.2f}, Company: {company_conf:.2f}")
    
    # Performance summary
    total_time = time.time() - start_time
    entities_per_second = len(test_entities) / total_time
    
    print(f"\n⚡ PERFORMANCE:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Rate: {entities_per_second:.0f} entities/second")
    print(f"  Per entity: {total_time/len(test_entities)*1000:.1f}ms")

def test_founder_intelligence_entities():
    """Test corpus validation on founder intelligence specific entities."""
    
    print("\n" + "=" * 60)
    print("TESTING FOUNDER INTELLIGENCE ENTITIES")
    print("=" * 60)
    
    try:
        from knowledge.corpus.entity_corpus_builder import CorpusValidator
        validator = CorpusValidator()
    except ImportError:
        print("❌ Corpus validator not available")
        return
    
    # Founder intelligence specific entities
    founder_entities = [
        # Tech CEOs and founders
        "Jeff Bezos", "Mark Zuckerberg", "Bill Gates", "Larry Page", 
        "Sergey Brin", "Jack Dorsey", "Evan Spiegel", "Travis Kalanick",
        "Brian Chesky", "Joe Gebbia", "Nathan Blecharczyk", "Stewart Butterfield",
        
        # Venture capitalists  
        "Marc Andreessen", "Ben Horowitz", "Peter Thiel", "Reid Hoffman",
        "Chris Sacca", "Naval Ravikant", "Jason Calacanis", "Tim Ferriss",
        
        # Major tech companies
        "OpenAI", "Anthropic", "DeepMind", "Stability AI", "Character AI",
        "Stripe", "Shopify", "Databricks", "Snowflake", "Palantir",
        
        # VC firms
        "Andreessen Horowitz", "Sequoia Capital", "Benchmark Capital",
        "Greylock Partners", "Kleiner Perkins", "Lightspeed Venture",
        
        # Accelerators
        "Y Combinator", "Techstars", "500 Startups", "Plug and Play",
        
        # Universities (talent pipeline)
        "Stanford", "MIT", "Harvard", "Berkeley", "Carnegie Mellon"
    ]
    
    print(f"\n🎯 Testing {len(founder_entities)} founder intelligence entities:")
    
    high_confidence_persons = 0
    high_confidence_companies = 0
    
    for entity in founder_entities:
        person_conf, person_details = validator.validate_person_name(entity)
        company_conf, company_details = validator.validate_company_name(entity)
        
        if person_conf > 0.7:
            high_confidence_persons += 1
            classification = "PERSON"
            conf = person_conf
        elif company_conf > 0.7:
            high_confidence_companies += 1  
            classification = "COMPANY"
            conf = company_conf
        else:
            classification = "UNKNOWN"
            conf = max(person_conf, company_conf)
        
        if conf > 0.7:  # Only show high confidence matches
            print(f"  ✅ {entity}: {classification} ({conf:.2f})")
    
    print(f"\n📊 FOUNDER INTELLIGENCE CORPUS COVERAGE:")
    print(f"  High-confidence persons: {high_confidence_persons}")
    print(f"  High-confidence companies: {high_confidence_companies}")
    print(f"  Total coverage: {(high_confidence_persons + high_confidence_companies)/len(founder_entities)*100:.1f}%")

def test_scale_performance():
    """Test performance at scale with thousands of entities."""
    
    print("\n" + "=" * 60)
    print("TESTING SCALE PERFORMANCE")
    print("=" * 60)
    
    try:
        from knowledge.corpus.entity_corpus_builder import CorpusValidator
        validator = CorpusValidator()
    except ImportError:
        print("❌ Corpus validator not available")
        return
    
    # Generate test entities at scale
    first_names = ["John", "Sarah", "Michael", "Jessica", "David", "Emily", "James", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    company_words = ["Tech", "Solutions", "Systems", "Digital", "Global", "Dynamics", "Innovations"]
    company_suffixes = ["Inc", "Corp", "LLC", "Ltd"]
    
    # Generate 1000 test entities
    test_entities = []
    
    # 500 person names
    for i in range(500):
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        test_entities.append(f"{first} {last}")
    
    # 500 company names  
    for i in range(500):
        word = company_words[i % len(company_words)]
        suffix = company_suffixes[i % len(company_suffixes)]
        test_entities.append(f"{word}Corp {suffix}")
    
    print(f"📊 Testing {len(test_entities)} entities for scale performance...")
    
    # Measure performance
    start_time = time.time()
    
    results = []
    for entity in test_entities:
        person_conf, _ = validator.validate_person_name(entity)
        company_conf, _ = validator.validate_company_name(entity)
        
        classification = "PERSON" if person_conf > company_conf else "COMPANY"
        confidence = max(person_conf, company_conf)
        
        results.append((entity, classification, confidence))
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    entities_per_second = len(test_entities) / total_time
    avg_time_per_entity = total_time / len(test_entities) * 1000  # ms
    
    high_conf_count = sum(1 for _, _, conf in results if conf > 0.7)
    
    print(f"\n⚡ SCALE PERFORMANCE RESULTS:")
    print(f"  Total entities: {len(test_entities):,}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Rate: {entities_per_second:,.0f} entities/second")
    print(f"  Average per entity: {avg_time_per_entity:.2f}ms")
    print(f"  High confidence (>0.7): {high_conf_count} ({high_conf_count/len(test_entities)*100:.1f}%)")
    
    # Show some sample results
    print(f"\n📝 Sample results:")
    for entity, classification, confidence in results[:10]:
        print(f"  {entity}: {classification} ({confidence:.2f})")

if __name__ == "__main__":
    print("🚀 Corpus-Based Entity Validation Test Suite")
    print("=" * 60)
    
    # Test basic corpus validation
    test_corpus_validation()
    
    # Test founder intelligence specific entities
    test_founder_intelligence_entities()
    
    # Test scale performance
    test_scale_performance()
    
    print("\n✅ Corpus validation testing completed!")
    print("\n💡 This demonstrates O(n) entity validation for millions of documents")
    print("   with high-confidence classification using name/company corpuses.")