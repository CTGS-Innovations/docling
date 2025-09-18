#!/usr/bin/env python3
"""
Entity Extraction Validation Test Script
Tests the MVP-Fusion pipeline against a document with known entity counts
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Expected entity counts from our test document
EXPECTED_COUNTS = {
    "core_8": {
        "person": 25,
        "org": 30,
        "loc": 20,
        "gpe": 8,
        "date": 15,
        "time": 8,
        "money": 20,
        "percent": 15
    },
    "additional": {
        "phone": 10,
        "regulation": 10,
        "url": 5,
        "measurement": 20
    },
    "relationships": {
        "reports_to": 1,
        "oversees": 1,
        "collaborates": 1,
        "coordinates": 1,
        "partners": 1
    },
    "rules": {
        "compliance_rules": 5,
        "financial_rules": 5
    }
}

def load_extraction_results(json_file: Path) -> Dict:
    """Load the JSON extraction results"""
    with open(json_file, 'r') as f:
        return json.load(f)

def validate_core_8_entities(results: Dict) -> Dict[str, Any]:
    """Validate Core 8 entity extraction"""
    validation_results = {}
    semantic_facts = results.get("semantic_facts", {})
    
    # Check each Core 8 entity type
    entity_mapping = {
        "person": "global_person",
        "org": "global_org", 
        "loc": "global_loc",
        "gpe": "global_gpe",
        "date": "global_date",
        "time": "global_time",
        "money": "global_money",
        "percent": "global_percent"
    }
    
    for entity_type, json_key in entity_mapping.items():
        expected = EXPECTED_COUNTS["core_8"][entity_type]
        found = len(semantic_facts.get(json_key, []))
        
        validation_results[entity_type] = {
            "expected": expected,
            "found": found,
            "accuracy": (found / expected * 100) if expected > 0 else 0,
            "status": "✅" if found == expected else "❌",
            "difference": found - expected
        }
        
    return validation_results

def validate_additional_entities(results: Dict) -> Dict[str, Any]:
    """Validate additional entity types"""
    validation_results = {}
    semantic_facts = results.get("semantic_facts", {})
    
    # Map additional entity types
    entity_mapping = {
        "phone": "global_phone",
        "regulation": "global_regulation",
        "url": "global_url",
        "measurement": "global_measurement"
    }
    
    for entity_type, json_key in entity_mapping.items():
        expected = EXPECTED_COUNTS["additional"][entity_type]
        found = len(semantic_facts.get(json_key, []))
        
        validation_results[entity_type] = {
            "expected": expected,
            "found": found,
            "accuracy": (found / expected * 100) if expected > 0 else 0,
            "status": "✅" if found == expected else "❌",
            "difference": found - expected
        }
        
    return validation_results

def validate_enrichment(results: Dict) -> Dict[str, Any]:
    """Validate entity enrichment (roles, organizations, context)"""
    validation_results = {
        "persons_with_roles": 0,
        "persons_with_orgs": 0,
        "enriched_locations": 0,
        "enriched_orgs": 0
    }
    
    # Check enrichment in domain entities
    enrichment_data = results.get("enrichment", {})
    domain_entities = enrichment_data.get("domain_entities", {})
    
    # Check people enrichment
    people = domain_entities.get("people", [])
    for person in people:
        if person.get("role"):
            validation_results["persons_with_roles"] += 1
        if person.get("organization"):
            validation_results["persons_with_orgs"] += 1
    
    # Check other enrichments
    validation_results["enriched_locations"] = len(domain_entities.get("locations", []))
    validation_results["enriched_orgs"] = len(domain_entities.get("organizations", []))
    
    return validation_results

def analyze_specific_cases(results: Dict) -> Dict[str, List[str]]:
    """Analyze specific challenging cases"""
    analysis = {
        "challenging_names_found": [],
        "single_names_found": [],
        "abbreviations_found": [],
        "multi_word_orgs_found": [],
        "regulation_patterns_found": []
    }
    
    semantic_facts = results.get("semantic_facts", {})
    
    # Check for challenging person names
    challenging_names = ["Xi Zhang", "José García-López", "Priya Patel", "François Dubois", 
                        "Yuki Tanaka", "Ahmed Al-Rashid", "Olga Volkov", "João Silva Santos"]
    
    persons = semantic_facts.get("global_person", [])
    for person in persons:
        name = person.get("raw_text", "")
        if name in challenging_names:
            analysis["challenging_names_found"].append(name)
        if " " not in name and len(name) > 2:  # Single names
            analysis["single_names_found"].append(name)
    
    # Check organizations
    orgs = semantic_facts.get("global_org", [])
    for org in orgs:
        name = org.get("raw_text", "")
        if len(name) <= 5 and name.isupper():  # Abbreviations
            analysis["abbreviations_found"].append(name)
        if len(name.split()) > 3:  # Multi-word organizations
            analysis["multi_word_orgs_found"].append(name)
    
    # Check regulations
    regulations = semantic_facts.get("global_regulation", [])
    for reg in regulations:
        pattern = reg.get("raw_text", "")
        analysis["regulation_patterns_found"].append(pattern)
    
    return analysis

def print_validation_report(json_file: Path):
    """Generate and print comprehensive validation report"""
    results = load_extraction_results(json_file)
    
    print("=" * 80)
    print("ENTITY EXTRACTION VALIDATION REPORT")
    print("=" * 80)
    print(f"Test Document: ENTITY_EXTRACTION_TEST_DOCUMENT.md")
    print(f"Results File: {json_file}")
    print("=" * 80)
    
    # Core 8 Validation
    print("\n📊 CORE 8 ENTITY VALIDATION")
    print("-" * 40)
    core_8_results = validate_core_8_entities(results)
    
    total_expected = 0
    total_found = 0
    
    for entity_type, stats in core_8_results.items():
        print(f"{stats['status']} {entity_type.upper():15} Expected: {stats['expected']:3} | Found: {stats['found']:3} | Accuracy: {stats['accuracy']:6.1f}% | Diff: {stats['difference']:+3}")
        total_expected += stats['expected']
        total_found += stats['found']
    
    overall_accuracy = (total_found / total_expected * 100) if total_expected > 0 else 0
    print(f"\n📈 Overall Core 8 Accuracy: {overall_accuracy:.1f}% ({total_found}/{total_expected})")
    
    # Additional Entities Validation
    print("\n📋 ADDITIONAL ENTITY VALIDATION")
    print("-" * 40)
    additional_results = validate_additional_entities(results)
    
    for entity_type, stats in additional_results.items():
        print(f"{stats['status']} {entity_type.upper():15} Expected: {stats['expected']:3} | Found: {stats['found']:3} | Accuracy: {stats['accuracy']:6.1f}% | Diff: {stats['difference']:+3}")
    
    # Enrichment Validation
    print("\n🔍 ENRICHMENT VALIDATION")
    print("-" * 40)
    enrichment_results = validate_enrichment(results)
    for key, value in enrichment_results.items():
        print(f"{key:25}: {value}")
    
    # Specific Cases Analysis
    print("\n🎯 SPECIFIC CASES ANALYSIS")
    print("-" * 40)
    specific_cases = analyze_specific_cases(results)
    for case_type, found_items in specific_cases.items():
        print(f"\n{case_type}:")
        if found_items:
            for item in found_items[:5]:  # Show first 5
                print(f"  • {item}")
            if len(found_items) > 5:
                print(f"  ... and {len(found_items) - 5} more")
        else:
            print("  None found")
    
    # Performance Metrics
    print("\n⚡ PERFORMANCE METRICS")
    print("-" * 40)
    if "entity_summary" in results:
        summary = results["entity_summary"]
        print(f"Total Entities Found: {summary.get('total_entities', 'N/A')}")
        print(f"Global Entities: {summary.get('global_entities_count', 'N/A')}")
        print(f"Domain Entities: {summary.get('domain_entities_count', 'N/A')}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    
    issues = []
    if core_8_results["person"]["found"] < core_8_results["person"]["expected"]:
        issues.append(f"• Person detection needs improvement (missing {core_8_results['person']['expected'] - core_8_results['person']['found']} persons)")
    if core_8_results["org"]["found"] < core_8_results["org"]["expected"]:
        issues.append(f"• Organization detection needs improvement (missing {core_8_results['org']['expected'] - core_8_results['org']['found']} orgs)")
    if len(specific_cases["challenging_names_found"]) < 8:
        issues.append("• Challenging name detection needs enhancement")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ All entity types meeting expected thresholds!")
    
    print("\n" + "=" * 80)
    print("END OF VALIDATION REPORT")
    print("=" * 80)

if __name__ == "__main__":
    # Default path to the JSON output
    json_file = Path("../output/fusion/ENTITY_EXTRACTION_TEST_DOCUMENT.json")
    
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
    
    if not json_file.exists():
        print(f"❌ Error: Results file not found: {json_file}")
        print("\nFirst run the extraction:")
        print("  python fusion_cli.py --file ~/projects/docling/cli/data_complex/ENTITY_EXTRACTION_TEST_DOCUMENT.md")
        sys.exit(1)
    
    print_validation_report(json_file)