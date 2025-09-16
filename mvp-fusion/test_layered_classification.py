#!/usr/bin/env python3
"""
Test script for Layered Classification Architecture
==================================================
Demonstrates 5-layer progressive intelligence system with early termination.
"""

import time
import yaml
from pathlib import Path
from pipeline.fusion_pipeline import FusionPipeline

def test_layered_classification():
    """Test the new layered classification system"""
    
    print("🏗️  Testing Layered Classification Architecture")
    print("=" * 60)
    
    # Load configuration
    config_path = Path("config/full_test.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create pipeline
    pipeline = FusionPipeline(config)
    
    # Test documents with different characteristics
    test_documents = [
        {
            'name': 'Safety Document (High confidence expected)',
            'content': """
            OSHA Safety Guidelines for Construction Sites
            
            This document outlines safety requirements for construction workers.
            All personnel must wear hard hats, safety goggles, and protective gloves.
            
            Fall hazards are present when working above 6 feet.
            Workers must use safety harnesses when working on scaffolds.
            
            OSHA regulations 29 CFR 1926.95 require head protection.
            Safety equipment must be inspected daily.
            
            Common injuries include fractures, cuts, and bruises.
            Report all accidents to the safety coordinator immediately.
            
            Contact: Safety Office at (555) 123-4567
            """,
            'filename': 'osha_safety_guidelines.pdf'
        },
        {
            'name': 'Financial Document (Mixed domains)',
            'content': """
            Quarterly Financial Report - Q3 2024
            
            Revenue: $2,500,000
            Expenses: $1,800,000
            Net profit: $700,000
            
            Investment in safety equipment: $150,000
            Compliance training costs: $45,000
            
            SEC filing deadline: December 15, 2024
            Contact CFO at (555) 987-6543
            
            Reference: SEC regulation 10-K filing requirements
            """,
            'filename': 'quarterly_financial_report.pdf'
        },
        {
            'name': 'Low-Content Document (Expected early termination)',
            'content': """
            Brief Note
            
            This is a very short document with minimal content.
            No clear domain indicators.
            """,
            'filename': 'brief_note.pdf'
        },
        {
            'name': 'Medical Document (Deep domain analysis expected)',
            'content': """
            Patient Medical Report
            
            Patient: John Doe
            Date: October 15, 2024
            
            Diagnosis: Hypertension and diabetes
            
            Medical procedures performed:
            - Blood pressure examination
            - Glucose tolerance test
            - Cardiac evaluation
            
            Medications prescribed:
            - Lisinopril for hypertension
            - Metformin for diabetes management
            
            Follow-up surgery scheduled for November 20, 2024.
            
            Contact physician at (555) 456-7890
            Insurance claim: $3,200.00
            """,
            'filename': 'patient_medical_report.pdf'
        }
    ]
    
    # Process each test document
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 Test {i}: {doc['name']}")
        print("-" * 50)
        
        start_time = time.perf_counter()
        
        # Run layered classification
        classification_result = pipeline._generate_classification_data(
            doc['content'], doc['filename']
        )
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Display results
        print(f"⏱️  Total processing time: {processing_time:.2f}ms")
        print(f"🏗️  Layers processed: {', '.join(classification_result.get('layers_processed', []))}")
        
        if classification_result.get('early_termination'):
            print(f"⚡ Early termination: {classification_result.get('termination_reason')}")
        
        # Show layer timings
        layer_timings = classification_result.get('layer_timings_ms', {})
        print(f"\n📊 Layer Performance:")
        for layer, timing in layer_timings.items():
            print(f"   {layer}: {timing:.2f}ms")
        
        # Show domain classification
        domains = classification_result.get('domains', {})
        if domains:
            print(f"\n🎯 Domain Classification:")
            for domain, confidence in list(domains.items())[:3]:  # Top 3
                print(f"   {domain}: {confidence}%")
        
        # Show primary domain info
        primary_domain = classification_result.get('primary_domain')
        primary_confidence = classification_result.get('primary_domain_confidence', 0)
        if primary_domain:
            print(f"\n🎯 Primary Domain: {primary_domain} ({primary_confidence}% confidence)")
        
        # Show entity extraction results
        universal_entities = classification_result.get('universal_entities', {})
        total_entities = classification_result.get('total_entities_found', 0)
        if total_entities > 0:
            print(f"\n🔍 Entities Found ({total_entities} total):")
            for entity_type, entities in universal_entities.items():
                if entities:
                    print(f"   {entity_type}: {len(entities)} items")
        
        # Show deep domain entities if processed
        deep_entities = classification_result.get('deep_domain_entities', {})
        if deep_entities:
            print(f"\n🎯 Deep Domain Entities:")
            for entity_type, entities in deep_entities.items():
                if entities:
                    print(f"   {entity_type}: {entities[:3]}...")  # Show first 3
        
        # Performance assessment
        if processing_time < 50:
            print(f"✅ Performance: EXCELLENT ({processing_time:.1f}ms < 50ms target)")
        elif processing_time < 100:
            print(f"⚠️  Performance: GOOD ({processing_time:.1f}ms)")
        else:
            print(f"❌ Performance: NEEDS OPTIMIZATION ({processing_time:.1f}ms > 100ms)")
    
    print(f"\n🎯 LAYERED CLASSIFICATION TEST COMPLETE")
    print("=" * 60)
    print("🏗️  Architecture Benefits:")
    print("   📊 Progressive intelligence building (5 layers)")
    print("   ⚡ Early termination for low-confidence documents") 
    print("   🎯 Deep domain analysis only when justified")
    print("   🔄 Enrichment integrated (no duplicate processing)")
    print("   ⚡ Performance-optimized with clear targets")

if __name__ == "__main__":
    test_layered_classification()