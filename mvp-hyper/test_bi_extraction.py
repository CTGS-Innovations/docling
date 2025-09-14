#!/usr/bin/env python3
"""
Test Business Intelligence Entity Extraction Pipeline
====================================================
Tests the enhanced tagger and semantic layer with business intelligence
content to verify opportunity discovery capabilities.
"""

import sys
import json
from pathlib import Path
import importlib.util
import sys

# Import modules with hyphens in filename
spec_tagger = importlib.util.spec_from_file_location("mvp_hyper_tagger", "mvp-hyper-tagger.py")
mvp_hyper_tagger = importlib.util.module_from_spec(spec_tagger)
spec_tagger.loader.exec_module(mvp_hyper_tagger)

spec_semantic = importlib.util.spec_from_file_location("mvp_hyper_semantic", "mvp-hyper-semantic.py")
mvp_hyper_semantic = importlib.util.module_from_spec(spec_semantic)
spec_semantic.loader.exec_module(mvp_hyper_semantic)

MVPHyperTagger = mvp_hyper_tagger.MVPHyperTagger
MVPHyperSemanticExtractor = mvp_hyper_semantic.MVPHyperSemanticExtractor

# Test document with rich business intelligence content
TEST_CONTENT = """---
Test Business Intelligence Document
====================================

Acme Corp, a leading technology company founded by John Smith, recently announced 
a $50 million Series B funding round led by Venture Capital Partners. The company 
struggles with manual data processing workflows that are time-consuming and costly, 
creating a significant bottleneck in their operations.

CEO Sarah Johnson reported that the market for automated workflow solutions is 
estimated to be worth $2.5 billion and growing at 25% annually. The company's 
breakthrough approach to AI-driven process automation represents a novel solution 
that addresses the gap in enterprise workflow optimization.

Contact: info@acmecorp.com or call (555) 123-4567
Website: https://www.acmecorp.com
Location: San Francisco, California

Competitors like TechFlow Inc. and DataStream Corporation have established 
dominant market positions, but Acme's partnership with Microsoft Corporation 
provides strategic advantages in the competitive landscape.

The innovation in machine learning algorithms has potential for revolutionary 
changes in how businesses approach workflow management, with early-stage companies 
raising significant venture capital investment rounds.

Key challenges include difficulty in integrating legacy systems, expensive 
maintenance costs, and barriers to user adoption among enterprise clients.
---"""

def test_business_intelligence_pipeline():
    """Test the complete BI extraction pipeline."""
    
    print("🔧 Testing Business Intelligence Extraction Pipeline")
    print("=" * 60)
    
    # Initialize components
    tagger = MVPHyperTagger(cache_enabled=False)
    semantic_extractor = MVPHyperSemanticExtractor()
    
    # Step 1: Test enhanced tagger with BI extraction
    print("📊 Step 1: Testing Enhanced Tagger...")
    test_file = Path("test_bi_document.md")
    
    tags = tagger.tag_document(test_file, TEST_CONTENT)
    
    print(f"Document Types: {tags.document_types}")
    print(f"Confidence: {tags.confidence}")
    print(f"Processing Time: {tags.processing_time:.4f}s")
    
    # Check universal entities
    if tags.universal_entities:
        print("\n🎯 Universal Entities:")
        for entity_type, entities in tags.universal_entities.items():
            print(f"  {entity_type}: {entities}")
    else:
        print("\n⚠️  No universal entities extracted!")
    
    # Check business intelligence extractions
    print(f"\n💡 Pain Points: {tags.pain_points}")
    print(f"📈 Market Opportunities: {tags.market_opportunities}")  
    print(f"🚀 Innovation Signals: {tags.innovation_signals}")
    print(f"🏢 Competitive Intelligence: {tags.competitive_intelligence}")
    
    # Step 2: Test semantic extraction with tagger metadata
    print(f"\n📋 Step 2: Testing Semantic Extraction with BI metadata...")
    
    # Convert tags to front matter format for semantic processing
    front_matter_content = f"""---
document_types: {tags.document_types}
domains: {tags.domains}
keywords: {', '.join(tags.keywords)}
entities: {', '.join(tags.entities)}
universal_entities:
"""
    
    # Add universal entities if available
    if tags.universal_entities:
        for entity_type, entity_list in tags.universal_entities.items():
            front_matter_content += f"  {entity_type}: [{', '.join(entity_list)}]\n"
    
    # Add BI fields  
    if tags.pain_points:
        front_matter_content += f"pain_points: [{', '.join(tags.pain_points)}]\n"
    if tags.market_opportunities:
        front_matter_content += f"market_opportunities: [{', '.join(tags.market_opportunities)}]\n"
    if tags.innovation_signals:
        front_matter_content += f"innovation_signals: [{', '.join(tags.innovation_signals)}]\n"
    if tags.competitive_intelligence:
        front_matter_content += f"competitive_intelligence: [{', '.join(tags.competitive_intelligence)}]\n"
    
    front_matter_content += "---\n\n" + TEST_CONTENT.split('---', 2)[2]
    
    # Extract semantic metadata
    semantic_results = semantic_extractor.extract_semantic_metadata(
        test_file, front_matter_content
    )
    
    print(f"✅ Semantic extraction completed in {semantic_results.processing_time:.4f}s")
    print(f"📝 Total facts extracted: {len(semantic_results.facts)}")
    
    # Analyze business intelligence facts
    bi_facts = [f for f in semantic_results.facts if f.fact_type == 'business_intelligence']
    print(f"🎯 Business Intelligence facts: {len(bi_facts)}")
    
    if bi_facts:
        print("\n🔍 Business Intelligence Facts:")
        for fact in bi_facts:
            print(f"  - {fact.subject} {fact.predicate} {fact.object[:60]}{'...' if len(fact.object) > 60 else ''}")
            print(f"    Category: {fact.attributes.get('bi_category', 'unknown')} | Confidence: {fact.confidence}")
    
    # Analyze entity classification
    entity_facts = [f for f in semantic_results.facts if f.fact_type == 'entity_identification']
    print(f"\n👥 Entity identification facts: {len(entity_facts)}")
    
    if entity_facts:
        print("\n🏷️  Classified Entities:")
        for fact in entity_facts:
            entity_type = fact.attributes.get('entity_type', 'UNKNOWN')
            source = fact.attributes.get('source', 'unknown')
            print(f"  - {fact.subject} → {entity_type} (from {source}, confidence: {fact.confidence})")
    
    # Performance summary
    total_time = tags.processing_time + semantic_results.processing_time
    content_length = len(TEST_CONTENT)
    pages_per_sec = (content_length / 2000) / total_time if total_time > 0 else 0  # Assume 2000 chars per page
    
    print(f"\n⚡ Performance Summary:")
    print(f"  Total processing time: {total_time:.4f}s")
    print(f"  Content length: {content_length} chars")
    print(f"  Estimated pages/sec: {pages_per_sec:.1f}")
    
    return {
        'tags': tags,
        'semantic_results': semantic_results,
        'performance': {
            'total_time': total_time,
            'pages_per_sec': pages_per_sec
        }
    }

if __name__ == "__main__":
    try:
        results = test_business_intelligence_pipeline()
        print(f"\n✅ Business Intelligence extraction pipeline test completed successfully!")
        
        # Summary of key metrics
        tags = results['tags']
        semantic = results['semantic_results']
        
        print(f"\n📊 Key Metrics:")
        print(f"  - Universal entities extracted: {len(tags.universal_entities) if tags.universal_entities else 0}")
        print(f"  - Pain points identified: {len(tags.pain_points) if tags.pain_points else 0}")
        print(f"  - Market opportunities found: {len(tags.market_opportunities) if tags.market_opportunities else 0}")
        print(f"  - Innovation signals detected: {len(tags.innovation_signals) if tags.innovation_signals else 0}")
        print(f"  - Competitive intel gathered: {len(tags.competitive_intelligence) if tags.competitive_intelligence else 0}")
        print(f"  - Total semantic facts: {len(semantic.facts)}")
        print(f"  - Processing speed: {results['performance']['pages_per_sec']:.1f} pages/sec")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)