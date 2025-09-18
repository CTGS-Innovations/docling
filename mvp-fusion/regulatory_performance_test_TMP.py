#!/usr/bin/env python3
"""
Performance Test: Basic vs Comprehensive Regulatory Patterns
=============================================================

GOAL: Test performance impact of adding 60+ regulatory patterns vs 7 basic patterns
REASON: User wants to add comprehensive legal/regulatory entity detection
PROBLEM: Need to measure if 8.5x pattern increase causes significant slowdown
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Import FLPC engine 
import sys
sys.path.append('/home/corey/projects/docling/mvp-fusion')

try:
    from fusion.flpc_engine import FLPCEngine
    import flpc
    FLPC_AVAILABLE = True
    print("✅ FLPC available for testing")
except ImportError as e:
    print(f"❌ FLPC not available: {e}")
    FLPC_AVAILABLE = False
    exit(1)

class RegulatoryPatternTester:
    def __init__(self):
        self.test_documents = []
        self.load_test_documents()
        
    def load_test_documents(self):
        """Load test documents from output/fusion directory"""
        output_dir = Path("/home/corey/projects/docling/output/fusion")
        
        for md_file in output_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                self.test_documents.append({
                    'name': md_file.name,
                    'content': content,
                    'size_chars': len(content)
                })
                print(f"📄 Loaded: {md_file.name} ({len(content):,} chars)")
            except Exception as e:
                print(f"⚠️ Failed to load {md_file.name}: {e}")
                
        print(f"✅ Loaded {len(self.test_documents)} test documents")
        
    def get_basic_patterns(self) -> Dict[str, Any]:
        """Original 7 basic regulatory patterns"""
        return {
            'regulatory_entities': {
                'regulation': {
                    'pattern': r'(?i)\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?(?:\([a-z]\))?',
                    'description': 'CFR regulation numbers',
                    'priority': 'high'
                },
                'iso_standard': {
                    'pattern': r'(?i)ISO\s*\d+(?:[-:]\d+)*',
                    'description': 'ISO standards',
                    'priority': 'medium'
                },
                'ansi_standard': {
                    'pattern': r'(?i)ANSI\s*[A-Z]*\d+(?:\.\d+)*',
                    'description': 'ANSI standards', 
                    'priority': 'medium'
                },
                'astm_standard': {
                    'pattern': r'(?i)ASTM\s*[A-Z]\d+(?:[-]\d+)*',
                    'description': 'ASTM standards',
                    'priority': 'medium'
                },
                'nfpa_standard': {
                    'pattern': r'(?i)NFPA\s*\d+',
                    'description': 'NFPA standards',
                    'priority': 'medium'
                },
                'generic_standard': {
                    'pattern': r'(?i)[A-Z]{2,4}\s*\d+(?:[-:\.]\d+)*',
                    'description': 'Generic standards',
                    'priority': 'low'
                },
                'section_ref': {
                    'pattern': r'(?i)Section\s+\d+(?:\.\d+)*',
                    'description': 'Section references',
                    'priority': 'low'
                }
            }
        }
        
    def get_comprehensive_patterns(self) -> Dict[str, Any]:
        """Comprehensive 60+ regulatory patterns"""
        return {
            'regulatory_entities': {
                # Legislation
                'constitution': {
                    'pattern': r'(?i)Constitution( of [A-Z][a-z]+)?',
                    'description': 'Constitutional references',
                    'priority': 'high'
                },
                'usc_statute': {
                    'pattern': r'(?i)\b\d+\s*U\.?S\.?C\.?\s*\d+',
                    'description': 'US Code statutes',
                    'priority': 'high'
                },
                'public_law': {
                    'pattern': r'(?i)\bPublic Law\s+\d+-\d+',
                    'description': 'Public laws',
                    'priority': 'high'
                },
                'house_bill': {
                    'pattern': r'(?i)\b(H\.R\.|S\.)\s*\d+',
                    'description': 'Congressional bills',
                    'priority': 'medium'
                },
                'amendment': {
                    'pattern': r'(?i)Amendment\s+[IVXLC]+',
                    'description': 'Constitutional amendments',
                    'priority': 'high'
                },
                
                # Federal Regulations
                'cfr_regulation': {
                    'pattern': r'(?i)\d+\s*CFR\s*\d+(?:\.\d+)*',
                    'description': 'Code of Federal Regulations',
                    'priority': 'high'
                },
                'federal_register': {
                    'pattern': r'(?i)\b[0-9]+\s*FR\s*[0-9]+',
                    'description': 'Federal Register',
                    'priority': 'medium'
                },
                'eu_regulation': {
                    'pattern': r'(?i)\bRegulation\s*\(\s*EU\s*\)\s*\d+/\d+',
                    'description': 'EU regulations',
                    'priority': 'medium'
                },
                
                # State and Local
                'state_code': {
                    'pattern': r'(?i)\b[A-Z][a-z]+\s+Code\s+§?\s*\d+',
                    'description': 'State codes',
                    'priority': 'medium'
                },
                'admin_code': {
                    'pattern': r'(?i)\b[A-Z]+\s+Admin(?:istrative)?\s+Code\s+\d+',
                    'description': 'Administrative codes',
                    'priority': 'medium'
                },
                
                # Standards Organizations
                'iso_standard': {
                    'pattern': r'(?i)ISO\s*\d+(?:[-:]\d+)*',
                    'description': 'ISO standards',
                    'priority': 'medium'
                },
                'ansi_standard': {
                    'pattern': r'(?i)ANSI\s*[A-Z]*\d+(?:\.\d+)*',
                    'description': 'ANSI standards',
                    'priority': 'medium'
                },
                'astm_standard': {
                    'pattern': r'(?i)ASTM\s*[A-Z]\d+(?:[-]\d+)*',
                    'description': 'ASTM standards',
                    'priority': 'medium'
                },
                'nfpa_standard': {
                    'pattern': r'(?i)NFPA\s*\d+',
                    'description': 'NFPA standards',
                    'priority': 'medium'
                },
                'ieee_standard': {
                    'pattern': r'(?i)IEEE\s*\d+(?:\.\d+)*',
                    'description': 'IEEE standards',
                    'priority': 'medium'
                },
                'nist_standard': {
                    'pattern': r'(?i)NIST\s*SP\s*\d{3,}-\d+',
                    'description': 'NIST special publications',
                    'priority': 'medium'
                },
                
                # Case Law
                'supreme_court_case': {
                    'pattern': r'(?i)[A-Z][a-z]+ v\. [A-Z][a-z]+',
                    'description': 'Court cases',
                    'priority': 'medium'
                },
                'federal_case': {
                    'pattern': r'(?i)\d+\s*F\.\s*\d+[a-z]*',
                    'description': 'Federal court cases',
                    'priority': 'medium'
                },
                'state_case': {
                    'pattern': r'(?i)\d+\s*[A-Z]{2,3}\s*\d+',
                    'description': 'State court cases',
                    'priority': 'low'
                },
                'icj_case': {
                    'pattern': r'(?i)ICJ\s+Case\s+\d+',
                    'description': 'International Court cases',
                    'priority': 'low'
                },
                
                # International Treaties
                'un_treaty': {
                    'pattern': r'(?i)UN Treaty Series\s*\d+',
                    'description': 'UN treaties',
                    'priority': 'medium'
                },
                'eu_directive': {
                    'pattern': r'(?i)Directive\s+\d+/\d+/(EU|EC)',
                    'description': 'EU directives',
                    'priority': 'medium'
                },
                'convention': {
                    'pattern': r'(?i)Convention on [A-Z][a-z]+',
                    'description': 'International conventions',
                    'priority': 'medium'
                },
                'bilateral_agreement': {
                    'pattern': r'(?i)Agreement between [A-Z][a-z]+ and [A-Z][a-z]+',
                    'description': 'Bilateral agreements',
                    'priority': 'low'
                },
                
                # Administrative Materials
                'executive_order': {
                    'pattern': r'(?i)Executive Order\s*\d+',
                    'description': 'Executive orders',
                    'priority': 'high'
                },
                'policy_statement': {
                    'pattern': r'(?i)Policy Statement\s+\d+',
                    'description': 'Policy statements',
                    'priority': 'medium'
                },
                'agency_memo': {
                    'pattern': r'(?i)Memorandum\s+(?:No\.)?\s*\d+',
                    'description': 'Agency memoranda',
                    'priority': 'medium'
                },
                'advisory_opinion': {
                    'pattern': r'(?i)Advisory Opinion\s+\d+',
                    'description': 'Advisory opinions',
                    'priority': 'medium'
                },
                'circular': {
                    'pattern': r'(?i)Circular\s+[A-Z0-9\-]+',
                    'description': 'Circulars',
                    'priority': 'low'
                },
                
                # Document Structure
                'title': {
                    'pattern': r'(?i)Title\s+\d+',
                    'description': 'Title references',
                    'priority': 'medium'
                },
                'chapter': {
                    'pattern': r'(?i)Chapter\s+\d+',
                    'description': 'Chapter references',
                    'priority': 'medium'
                },
                'part': {
                    'pattern': r'(?i)Part\s+\d+',
                    'description': 'Part references',
                    'priority': 'medium'
                },
                'subpart': {
                    'pattern': r'(?i)Subpart\s+[A-Z]',
                    'description': 'Subpart references',
                    'priority': 'low'
                },
                'section': {
                    'pattern': r'(?i)(Section|Sec\.)\s+\d+(?:\.\d+)*',
                    'description': 'Section references',
                    'priority': 'medium'
                },
                'appendix': {
                    'pattern': r'(?i)Appendix\s+[A-Z0-9]+',
                    'description': 'Appendix references',
                    'priority': 'low'
                },
                'annex': {
                    'pattern': r'(?i)Annex\s+[A-Z0-9]+',
                    'description': 'Annex references',
                    'priority': 'low'
                },
                
                # Compliance Frameworks
                'soc2': {
                    'pattern': r'(?i)SOC\s*2',
                    'description': 'SOC 2 compliance',
                    'priority': 'high'
                },
                'hipaa': {
                    'pattern': r'(?i)HIPAA',
                    'description': 'HIPAA compliance',
                    'priority': 'high'
                },
                'gdpr': {
                    'pattern': r'(?i)GDPR\s*(Regulation)?',
                    'description': 'GDPR compliance',
                    'priority': 'high'
                },
                'fhir': {
                    'pattern': r'(?i)FHIR\s*(?:Standard)?',
                    'description': 'FHIR standards',
                    'priority': 'medium'
                },
                'pci_dss': {
                    'pattern': r'(?i)PCI[-\s]?DSS',
                    'description': 'PCI DSS compliance',
                    'priority': 'high'
                },
                
                # Documentation
                'white_paper': {
                    'pattern': r'(?i)White Paper\s+\d+',
                    'description': 'White papers',
                    'priority': 'low'
                },
                'technical_report': {
                    'pattern': r'(?i)Technical Report\s+[A-Z0-9\-]+',
                    'description': 'Technical reports',
                    'priority': 'low'
                },
                'guidance_note': {
                    'pattern': r'(?i)Guidance Note\s+\d+',
                    'description': 'Guidance notes',
                    'priority': 'low'
                },
                'guidance_document': {
                    'pattern': r'(?i)Guidance\s+Document\s+\d+',
                    'description': 'Federal guidance documents',
                    'priority': 'medium'
                },
                'who_fao_guidelines': {
                    'pattern': r'(?i)(WHO|FAO)\s+Guidelines?',
                    'description': 'WHO/FAO guidelines',
                    'priority': 'medium'
                }
            }
        }
    
    def run_performance_test(self, patterns: Dict[str, Any], test_name: str) -> Dict[str, Any]:
        """Run performance test with given patterns"""
        print(f"\n🔬 Running {test_name}...")
        
        # Create test config
        config = {
            'engines': {'flpc_rust': {'enabled': True}},
            'patterns': patterns
        }
        
        try:
            # Initialize FLPC engine
            engine = FLPCEngine(config)
            engine.raw_patterns = patterns
            engine._compile_patterns()
            
            print(f"✅ Engine initialized with {len(patterns['regulatory_entities'])} patterns")
            
            # Performance metrics
            results = {
                'test_name': test_name,
                'pattern_count': len(patterns['regulatory_entities']),
                'document_times': [],
                'total_entities': 0,
                'total_chars': 0,
                'total_time': 0.0
            }
            
            # Test each document
            for doc in self.test_documents:
                print(f"  📄 Testing {doc['name']} ({doc['size_chars']:,} chars)...")
                
                start_time = time.perf_counter()
                
                # Extract entities
                extraction_result = engine.extract_entities(doc['content'], 'regulatory_entities')
                
                end_time = time.perf_counter()
                doc_time = end_time - start_time
                
                # Count entities found
                entities_found = sum(len(entities) for entities in extraction_result.get('entities', {}).values())
                
                results['document_times'].append(doc_time)
                results['total_entities'] += entities_found
                results['total_chars'] += doc['size_chars']
                results['total_time'] += doc_time
                
                print(f"    ⏱️ {doc_time:.4f}s, {entities_found} entities")
            
            # Calculate performance metrics
            results['avg_time_per_doc'] = statistics.mean(results['document_times'])
            results['chars_per_second'] = results['total_chars'] / results['total_time'] if results['total_time'] > 0 else 0
            results['entities_per_second'] = results['total_entities'] / results['total_time'] if results['total_time'] > 0 else 0
            
            return results
            
        except Exception as e:
            print(f"❌ Error in {test_name}: {e}")
            return {'error': str(e), 'test_name': test_name}
    
    def run_comparison(self):
        """Run both tests and compare results"""
        print("🚀 Starting Regulatory Pattern Performance Test")
        print("=" * 60)
        
        # Test basic patterns (7 patterns)
        basic_results = self.run_performance_test(self.get_basic_patterns(), "Basic Patterns (7)")
        
        # Test comprehensive patterns (40+ patterns)  
        comprehensive_results = self.run_performance_test(self.get_comprehensive_patterns(), "Comprehensive Patterns (40+)")
        
        # Compare results
        self.print_comparison(basic_results, comprehensive_results)
        
    def print_comparison(self, basic: Dict[str, Any], comprehensive: Dict[str, Any]):
        """Print detailed performance comparison"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE COMPARISON RESULTS")
        print("=" * 60)
        
        if 'error' in basic or 'error' in comprehensive:
            print("❌ Test failed:")
            if 'error' in basic:
                print(f"  Basic test error: {basic['error']}")
            if 'error' in comprehensive:
                print(f"  Comprehensive test error: {comprehensive['error']}")
            return
        
        print(f"📄 Test Documents: {len(self.test_documents)}")
        print(f"📝 Total Characters: {basic['total_chars']:,}")
        print()
        
        print("🔢 PATTERN COUNTS:")
        print(f"  Basic Patterns:        {basic['pattern_count']:2d}")
        print(f"  Comprehensive Patterns: {comprehensive['pattern_count']:2d}")
        print(f"  Increase Factor:        {comprehensive['pattern_count']/basic['pattern_count']:.1f}x")
        print()
        
        print("⏱️ PROCESSING TIME:")
        print(f"  Basic Total Time:       {basic['total_time']:.4f}s")
        print(f"  Comprehensive Time:     {comprehensive['total_time']:.4f}s")
        print(f"  Time Increase:          {comprehensive['total_time']/basic['total_time']:.2f}x")
        print()
        
        print("⚡ THROUGHPUT:")
        print(f"  Basic Chars/sec:        {basic['chars_per_second']:,.0f}")
        print(f"  Comprehensive Chars/sec: {comprehensive['chars_per_second']:,.0f}")
        print(f"  Throughput Ratio:       {basic['chars_per_second']/comprehensive['chars_per_second']:.2f}x")
        print()
        
        print("🎯 ENTITY DETECTION:")
        print(f"  Basic Entities Found:   {basic['total_entities']}")
        print(f"  Comprehensive Found:    {comprehensive['total_entities']}")
        print(f"  Entity Increase:        {comprehensive['total_entities']/max(basic['total_entities'],1):.1f}x")
        print()
        
        print("📊 PER-DOCUMENT PERFORMANCE:")
        for i, doc in enumerate(self.test_documents):
            basic_time = basic['document_times'][i]
            comp_time = comprehensive['document_times'][i]
            slowdown = comp_time / basic_time
            print(f"  {doc['name']:<25}: {basic_time:.4f}s → {comp_time:.4f}s ({slowdown:.2f}x)")
        
        print()
        
        # Performance verdict
        slowdown_factor = comprehensive['total_time'] / basic['total_time']
        if slowdown_factor < 1.5:
            verdict = "✅ NEGLIGIBLE IMPACT"
            recommendation = "Safe to implement comprehensive patterns"
        elif slowdown_factor < 2.0:
            verdict = "🟡 MODERATE IMPACT" 
            recommendation = "Consider selective pattern implementation"
        else:
            verdict = "🔴 SIGNIFICANT IMPACT"
            recommendation = "Recommend optimizing patterns before implementation"
            
        print(f"🏁 VERDICT: {verdict}")
        print(f"💡 RECOMMENDATION: {recommendation}")
        print(f"📈 Performance Impact: {slowdown_factor:.2f}x slower")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = RegulatoryPatternTester()
    tester.run_comparison()