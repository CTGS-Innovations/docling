#!/usr/bin/env python3
"""
JSON Performance Testing: orjson vs ujson vs standard json

Tests performance on actual semantic fact extraction data to determine
best high-performance JSON library for MVP-Fusion pipeline.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any

# Test imports for available libraries
LIBRARIES = {}

# Standard library (baseline)
LIBRARIES['json'] = json

# Test orjson (Rust-based, claimed 6x faster)
try:
    import orjson
    LIBRARIES['orjson'] = orjson
    print("✅ orjson available (Rust-based)")
except ImportError:
    print("❌ orjson not available - install with: pip install orjson")

# Test ujson (C-based, claimed 3x faster)
try:
    import ujson
    LIBRARIES['ujson'] = ujson
    print("✅ ujson available (C-based)")
except ImportError:
    print("❌ ujson not available - install with: pip install ujson")

def load_test_data() -> Dict[str, Any]:
    """Load actual semantic extraction data for testing"""
    test_file = Path('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_TXT_DOCUMENT.json')
    
    if not test_file.exists():
        # Create sample large data if file doesn't exist
        print("⚠️  Test file not found, creating sample data...")
        return create_large_sample_data()
    
    with open(test_file, 'r') as f:
        return json.load(f)

def create_large_sample_data() -> Dict[str, Any]:
    """Create large sample data similar to semantic extraction output"""
    sample_fact = {
        "fact_type": "MeasurementContextFact",
        "confidence": 0.6,
        "span": {"start": 0, "end": 10},
        "raw_text": "100 meters",
        "canonical_name": "100 meters",
        "context_summary": "The measurement context provides detailed information about the extracted value including units, precision, and surrounding textual context that helps validate the extraction accuracy.",
        "extraction_layer": "intelligent_analysis",
        "frequency_score": 1
    }
    
    # Create large dataset (simulate 1000 facts)
    large_data = {
        "semantic_facts": {
            "measurement": [sample_fact.copy() for _ in range(500)],
            "requirements": [sample_fact.copy() for _ in range(300)],
            "action_facts": [sample_fact.copy() for _ in range(200)]
        },
        "normalized_entities": {},
        "semantic_summary": {
            "total_facts": 1000,
            "fact_types": {"measurement": 500, "requirements": 300, "action_facts": 200},
            "extraction_engine": "Enhanced FLPC + Aho-Corasick + SPO Hybrid",
            "performance_model": "O(n) Linear Semantic Extraction"
        }
    }
    
    return large_data

def benchmark_serialization(data: Dict[str, Any], library_name: str, library) -> Dict[str, float]:
    """Benchmark JSON serialization performance"""
    results = {}
    
    if library_name == 'orjson':
        # orjson uses different API
        def serialize_pretty():
            return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode('utf-8')
        
        def serialize_compact():
            return orjson.dumps(data).decode('utf-8')
    
    elif library_name == 'ujson':
        def serialize_pretty():
            return ujson.dumps(data, indent=2, ensure_ascii=False)
        
        def serialize_compact():
            return ujson.dumps(data, ensure_ascii=False)
    
    else:  # standard json
        def serialize_pretty():
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        def serialize_compact():
            return json.dumps(data, ensure_ascii=False)
    
    # Benchmark pretty printing (what you want for readable output)
    print(f"  Testing {library_name} pretty printing...")
    start_time = time.perf_counter()
    for _ in range(10):  # 10 iterations for average
        pretty_json = serialize_pretty()
    pretty_time = (time.perf_counter() - start_time) * 1000 / 10  # ms per operation
    results['pretty_serialize_ms'] = pretty_time
    results['pretty_size_bytes'] = len(pretty_json.encode('utf-8'))
    
    # Benchmark compact serialization
    print(f"  Testing {library_name} compact serialization...")
    start_time = time.perf_counter()
    for _ in range(10):
        compact_json = serialize_compact()
    compact_time = (time.perf_counter() - start_time) * 1000 / 10
    results['compact_serialize_ms'] = compact_time
    results['compact_size_bytes'] = len(compact_json.encode('utf-8'))
    
    return results

def benchmark_deserialization(json_str: str, library_name: str, library) -> float:
    """Benchmark JSON deserialization performance"""
    if library_name == 'orjson':
        def deserialize():
            return orjson.loads(json_str.encode('utf-8'))
    elif library_name == 'ujson':
        def deserialize():
            return ujson.loads(json_str)
    else:
        def deserialize():
            return json.loads(json_str)
    
    print(f"  Testing {library_name} deserialization...")
    start_time = time.perf_counter()
    for _ in range(10):
        data = deserialize()
    return (time.perf_counter() - start_time) * 1000 / 10  # ms per operation

def create_horizontal_compact_formatter(library_name: str, library) -> callable:
    """Create compact horizontal formatter function for the library"""
    
    def format_horizontal_compact(data: Dict[str, Any]) -> str:
        """Format JSON in horizontal compact style"""
        # Transform data to more compact representation
        compact_data = data.copy()
        
        if 'semantic_facts' in compact_data:
            for category, facts in compact_data['semantic_facts'].items():
                if isinstance(facts, list) and len(facts) > 0:
                    # Make each fact more compact
                    compact_facts = []
                    for fact in facts[:20]:  # Limit for testing
                        compact_fact = {
                            'type': fact.get('fact_type', ''),
                            'conf': fact.get('confidence', 0),
                            'span': fact.get('span', {}),
                            'text': fact.get('raw_text', fact.get('canonical_name', '')),
                            'context': (fact.get('context_summary', '')[:100] + '...') if len(fact.get('context_summary', '')) > 100 else fact.get('context_summary', '')
                        }
                        compact_facts.append(compact_fact)
                    compact_data['semantic_facts'][category] = compact_facts
        
        # Serialize with minimal formatting for horizontal layout
        if library_name == 'orjson':
            return orjson.dumps(compact_data, option=orjson.OPT_INDENT_2).decode('utf-8')
        elif library_name == 'ujson':
            return ujson.dumps(compact_data, indent=1, ensure_ascii=False)
        else:
            return json.dumps(compact_data, indent=1, separators=(',', ':'), ensure_ascii=False)
    
    return format_horizontal_compact

def main():
    """Run comprehensive JSON performance tests"""
    print("JSON Performance Testing for MVP-Fusion")
    print("=" * 50)
    print("Testing with actual semantic extraction data...\n")
    
    # Load test data
    test_data = load_test_data()
    data_size = sys.getsizeof(str(test_data))
    fact_count = 0
    if 'semantic_facts' in test_data:
        fact_count = sum(len(facts) for facts in test_data['semantic_facts'].values() 
                        if isinstance(facts, list))
    
    print(f"📊 Test Data: {data_size:,} bytes, {fact_count} facts\n")
    
    # Test each available library
    results = {}
    json_samples = {}
    
    for lib_name, lib in LIBRARIES.items():
        print(f"🧪 Testing {lib_name}...")
        try:
            # Serialization tests
            serialize_results = benchmark_serialization(test_data, lib_name, lib)
            
            # Create sample JSON for deserialization test
            if lib_name == 'orjson':
                sample_json = orjson.dumps(test_data).decode('utf-8')
            elif lib_name == 'ujson':
                sample_json = ujson.dumps(test_data)
            else:
                sample_json = json.dumps(test_data)
            
            # Deserialization test
            deserialize_ms = benchmark_deserialization(sample_json, lib_name, lib)
            
            # Horizontal compact formatting test
            formatter = create_horizontal_compact_formatter(lib_name, lib)
            start_time = time.perf_counter()
            compact_horizontal = formatter(test_data)
            format_time = (time.perf_counter() - start_time) * 1000
            
            # Store results
            results[lib_name] = {
                **serialize_results,
                'deserialize_ms': deserialize_ms,
                'horizontal_format_ms': format_time,
                'horizontal_size_bytes': len(compact_horizontal.encode('utf-8'))
            }
            
            json_samples[lib_name] = compact_horizontal[:300] + "..." if len(compact_horizontal) > 300 else compact_horizontal
            
            print(f"  ✅ {lib_name} complete\n")
            
        except Exception as e:
            print(f"  ❌ {lib_name} failed: {e}\n")
            results[lib_name] = None
    
    # Display results
    print("📈 PERFORMANCE RESULTS")
    print("=" * 50)
    
    # Find baseline (standard json)
    baseline = results.get('json', {})
    baseline_pretty = baseline.get('pretty_serialize_ms', 1)
    baseline_deserialize = baseline.get('deserialize_ms', 1)
    baseline_horizontal = baseline.get('horizontal_format_ms', 1)
    
    print(f"{'Library':<12} {'Pretty':<12} {'Compact':<12} {'Deserial':<12} {'Horizontal':<12} {'Speed vs json'}")
    print("-" * 80)
    
    for lib_name, data in results.items():
        if data:
            pretty_ms = data['pretty_serialize_ms']
            compact_ms = data['compact_serialize_ms'] 
            deserial_ms = data['deserialize_ms']
            horizontal_ms = data['horizontal_format_ms']
            
            # Calculate speedup vs baseline
            pretty_speedup = baseline_pretty / pretty_ms if pretty_ms > 0 else 0
            deserial_speedup = baseline_deserialize / deserial_ms if deserial_ms > 0 else 0
            horizontal_speedup = baseline_horizontal / horizontal_ms if horizontal_ms > 0 else 0
            
            print(f"{lib_name:<12} {pretty_ms:>8.1f}ms  {compact_ms:>8.1f}ms  {deserial_ms:>8.1f}ms  {horizontal_ms:>8.1f}ms  {pretty_speedup:.1f}x / {deserial_speedup:.1f}x")
    
    # Show format comparison
    print(f"\n📋 HORIZONTAL FORMAT SAMPLES")
    print("=" * 50)
    for lib_name, sample in json_samples.items():
        print(f"\n{lib_name}:")
        print(sample)
    
    # Recommendations
    print(f"\n🚀 RECOMMENDATIONS FOR MVP-FUSION")
    print("=" * 50)
    
    if 'orjson' in results and results['orjson']:
        orjson_data = results['orjson']
        json_data = results['json']
        speedup = json_data['pretty_serialize_ms'] / orjson_data['pretty_serialize_ms']
        print(f"✅ PRIMARY: Use orjson - {speedup:.1f}x faster for your use case")
        print(f"   • Pretty printing: {orjson_data['pretty_serialize_ms']:.1f}ms")
        print(f"   • Horizontal formatting: {orjson_data['horizontal_format_ms']:.1f}ms")
        print(f"   • Install: pip install orjson")
    
    if 'ujson' in results and results['ujson']:
        ujson_data = results['ujson']
        json_data = results['json']
        speedup = json_data['pretty_serialize_ms'] / ujson_data['pretty_serialize_ms']
        print(f"✅ SECONDARY: Use ujson - {speedup:.1f}x faster, drop-in replacement")
    
    print(f"\n💡 Implementation: Replace json.dumps() with orjson.dumps() in:")
    print(f"   • service_processor.py:1649 (semantic JSON output)")
    print(f"   • fusion_pipeline.py:612 (knowledge data export)")
    print(f"   • All performance-critical JSON serialization")

if __name__ == "__main__":
    main()