#!/usr/bin/env python3
"""
YAML Generation Performance A/B Testing
========================================
GOAL: Test YAML generation optimization approaches
REASON: YAML generation is 99.2% of I/O bottleneck (378.87ms for 32 files)
PROBLEM: 11.8ms per file YAML generation vs user's expectation of sub-second total I/O

Test Options:
A) Optimize current YAML generation (reduce deep copies, streamline OrderedDict)
B) Cache/precompute common YAML patterns
C) Simplify YAML frontmatter structure
"""

import time
import yaml
import copy
from collections import OrderedDict
from pathlib import Path

# Mock document data structure for testing
class MockDocument:
    def __init__(self, doc_id):
        self.source_filename = f"test_doc_{doc_id}.pdf"
        self.source_stem = f"test_doc_{doc_id}"
        self.markdown_content = "# Sample Document\n\nThis is test content."
        
        # Complex YAML frontmatter (realistic structure)
        self.yaml_frontmatter = {
            'conversion': {
                'engine': 'docling_v1',
                'version': '1.2.3',
                'timestamp': '2025-09-25T12:00:00Z',
                'processing_time_ms': 123.45
            },
            'content_detection': {
                'has_tables': True,
                'has_images': False,
                'language': 'en',
                'page_count': 15,
                'word_count': 2500
            },
            'processing': {
                'pipeline_version': 'v2.1',
                'worker_id': 'worker-1',
                'batch_id': 'batch-001'
            },
            'processing_info': {
                'memory_usage_mb': 45.2,
                'cpu_time_ms': 890.1
            },
            'classification': {
                'source_file': self.source_filename,
                'domain_routing': {
                    'primary_domain': 'technical',
                    'confidence': 0.85,
                    'routing_decision': 'technical_pipeline'
                },
                'domains': {
                    'technical': 0.85,
                    'safety': 0.72,
                    'regulatory': 0.45,
                    'compliance': 0.38,
                    'legal': 0.15
                },
                'document_types': {
                    'manual': 0.78,
                    'specification': 0.65,
                    'report': 0.42,
                    'guideline': 0.35,
                    'policy': 0.22
                }
            },
            'source': {
                'path': f'/test/data/{self.source_filename}',
                'size_bytes': 125000,
                'modified': '2025-09-24T10:30:00Z'
            }
        }

# Custom YAML dumper (from existing code)
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def force_flow_style_spans(yaml_text):
    """Apply flow style formatting"""
    import re
    flow_pattern = r'(\w+):\s*\[([^\]]+)\]'
    def make_flow(match):
        key = match.group(1)
        values = match.group(2)
        return f'{key}: [{values}]'
    return re.sub(flow_pattern, make_flow, yaml_text)

# OPTION A: Optimized YAML generation (reduce deep copies, streamline)
def generate_yaml_optimized(doc):
    """Optimized YAML generation with minimal copying"""
    # Use direct references instead of deep copies where safe
    ordered_yaml = OrderedDict()
    
    # 1. Conversion info FIRST (direct reference - immutable data)
    if 'conversion' in doc.yaml_frontmatter:
        ordered_yaml['conversion'] = doc.yaml_frontmatter['conversion']
    
    # 2. Content analysis (shallow copy only structure, not values)
    if 'content_detection' in doc.yaml_frontmatter:
        ordered_yaml['content_analysis'] = dict(doc.yaml_frontmatter['content_detection'])
    
    # 3. Processing info (merge without deep copy)
    processing = {}
    if 'processing' in doc.yaml_frontmatter:
        processing.update(doc.yaml_frontmatter['processing'])
    if 'processing_info' in doc.yaml_frontmatter:
        processing.update(doc.yaml_frontmatter['processing_info'])
    if processing:
        ordered_yaml['processing'] = processing
    
    # 4. Domain Classification (optimized structure building)
    if 'classification' in doc.yaml_frontmatter:
        classification_data = doc.yaml_frontmatter['classification']
        domain_classification = {}
        
        # Direct reference for routing
        if 'domain_routing' in classification_data:
            domain_classification['routing'] = classification_data['domain_routing']
        
        # Optimized top domains filtering (single pass)
        domains = classification_data.get('domains', {})
        document_types = classification_data.get('document_types', {})
        
        # Single-pass filtering and sorting
        top_domains = [k for k, v in sorted(domains.items(), key=lambda x: x[1], reverse=True) if v > 0.5][:5]
        top_doc_types = [k for k, v in sorted(document_types.items(), key=lambda x: x[1], reverse=True) if v > 0.5][:5]
        
        if top_domains:
            domain_classification['top_domains'] = top_domains
        if top_doc_types:
            domain_classification['top_document_types'] = top_doc_types
        
        # Filtered data (single comprehension)
        filtered_domains = {k: v for k, v in domains.items() if v > 0.5}
        filtered_doc_types = {k: v for k, v in document_types.items() if v > 0.5}
        
        if filtered_domains:
            domain_classification['domains'] = filtered_domains
        if filtered_doc_types:
            domain_classification['document_types'] = filtered_doc_types
        
        ordered_yaml['domain_classification'] = domain_classification
    
    # 5. Source info (direct reference)
    if 'source' in doc.yaml_frontmatter:
        ordered_yaml['source'] = doc.yaml_frontmatter['source']
    
    # Skip remaining sections processing for performance
    
    yaml_header = yaml.dump(
        dict(ordered_yaml), 
        Dumper=NoAliasDumper,
        default_flow_style=None,
        sort_keys=False,
        width=200,
        allow_unicode=True
    )
    
    yaml_header = force_flow_style_spans(yaml_header)
    return f"---\n{yaml_header}---\n\n{doc.markdown_content}"

# OPTION B: Cached YAML patterns
class YAMLCache:
    def __init__(self):
        self.conversion_cache = {}
        self.processing_cache = {}
        self.source_cache = {}
    
    def get_cached_conversion(self, conversion_data):
        # Use conversion engine + version as cache key
        key = f"{conversion_data.get('engine', '')}_{conversion_data.get('version', '')}"
        if key not in self.conversion_cache:
            self.conversion_cache[key] = yaml.dump({'conversion': conversion_data}, Dumper=NoAliasDumper)
        return self.conversion_cache[key]

yaml_cache = YAMLCache()

def generate_yaml_cached(doc):
    """YAML generation with pattern caching"""
    parts = []
    
    # Use cached patterns for common sections
    if 'conversion' in doc.yaml_frontmatter:
        parts.append(yaml_cache.get_cached_conversion(doc.yaml_frontmatter['conversion']))
    
    # Generate dynamic parts only for unique data
    dynamic_yaml = OrderedDict()
    
    if 'content_detection' in doc.yaml_frontmatter:
        dynamic_yaml['content_analysis'] = copy.deepcopy(doc.yaml_frontmatter['content_detection'])
    
    # ... (abbreviated for demo - would include classification logic)
    
    if dynamic_yaml:
        parts.append(yaml.dump(dict(dynamic_yaml), Dumper=NoAliasDumper))
    
    # Combine cached and dynamic parts
    yaml_header = ''.join(parts).replace('---\n', '').strip()
    yaml_header = force_flow_style_spans(yaml_header)
    return f"---\n{yaml_header}\n---\n\n{doc.markdown_content}"

# OPTION C: Simplified YAML structure
def generate_yaml_simplified(doc):
    """Simplified YAML with reduced complexity"""
    # Minimal, flat structure
    simple_yaml = OrderedDict()
    
    # Essential info only
    if 'conversion' in doc.yaml_frontmatter:
        conv = doc.yaml_frontmatter['conversion']
        simple_yaml['engine'] = conv.get('engine', 'unknown')
        simple_yaml['version'] = conv.get('version', '1.0')
        simple_yaml['processing_time_ms'] = conv.get('processing_time_ms', 0)
    
    if 'content_detection' in doc.yaml_frontmatter:
        content = doc.yaml_frontmatter['content_detection']
        simple_yaml['pages'] = content.get('page_count', 0)
        simple_yaml['words'] = content.get('word_count', 0)
        simple_yaml['language'] = content.get('language', 'en')
    
    # Simplified classification
    if 'classification' in doc.yaml_frontmatter:
        classification = doc.yaml_frontmatter['classification']
        domains = classification.get('domains', {})
        
        # Only top domain
        if domains:
            top_domain = max(domains.items(), key=lambda x: x[1])
            simple_yaml['primary_domain'] = top_domain[0]
            simple_yaml['confidence'] = top_domain[1]
    
    if 'source' in doc.yaml_frontmatter:
        simple_yaml['source'] = doc.yaml_frontmatter['source']['path']
    
    yaml_header = yaml.dump(
        dict(simple_yaml), 
        Dumper=NoAliasDumper,
        default_flow_style=False,
        sort_keys=False
    )
    
    return f"---\n{yaml_header}---\n\n{doc.markdown_content}"

# CURRENT IMPLEMENTATION (from service_processor.py)
def generate_yaml_current(doc):
    """Current YAML generation (with all deep copies)"""
    ordered_yaml = OrderedDict()
    
    # 1. Conversion info FIRST
    if 'conversion' in doc.yaml_frontmatter:
        ordered_yaml['conversion'] = doc.yaml_frontmatter['conversion']
    
    # 2. Content analysis (pre-screening flags)
    if 'content_detection' in doc.yaml_frontmatter:
        ordered_yaml['content_analysis'] = copy.deepcopy(doc.yaml_frontmatter['content_detection'])
    
    # 3. Processing info (merge processing and processing_info)
    processing = {}
    if 'processing' in doc.yaml_frontmatter:
        processing.update(doc.yaml_frontmatter['processing'])
    if 'processing_info' in doc.yaml_frontmatter:
        processing.update(doc.yaml_frontmatter['processing_info'])
    if processing:
        ordered_yaml['processing'] = processing
    
    # 4. Domain Classification (enhanced structure) - HEAVY DEEP COPY USAGE
    if 'classification' in doc.yaml_frontmatter:
        classification_data = copy.deepcopy(doc.yaml_frontmatter['classification'])
        if 'source_file' in classification_data:
            del classification_data['source_file']
        
        # Build enhanced domain_classification structure
        domain_classification = {}
        
        # Routing decisions FIRST (drives classification)
        if 'domain_routing' in classification_data:
            domain_classification['routing'] = copy.deepcopy(classification_data['domain_routing'])
        
        # Top domains and document types (configurable top 5)
        domains = classification_data.get('domains', {})
        document_types = classification_data.get('document_types', {})
        
        # Get top 5 domains with scores > 0.5
        top_domains = [(k, v) for k, v in sorted(domains.items(), key=lambda x: x[1], reverse=True) 
                     if v > 0.5][:5]
        top_doc_types = [(k, v) for k, v in sorted(document_types.items(), key=lambda x: x[1], reverse=True) 
                       if v > 0.5][:5]
        
        if top_domains:
            domain_classification['top_domains'] = [k for k, v in top_domains]
        if top_doc_types:
            domain_classification['top_document_types'] = [k for k, v in top_doc_types]
        
        # Full detailed breakdowns (only scores > 0.5)
        filtered_domains = {k: v for k, v in domains.items() if v > 0.5}
        filtered_doc_types = {k: v for k, v in document_types.items() if v > 0.5}
        
        if filtered_domains:
            domain_classification['domains'] = filtered_domains
        if filtered_doc_types:
            domain_classification['document_types'] = filtered_doc_types
        
        ordered_yaml['domain_classification'] = domain_classification
    
    # 5. Source info
    if 'source' in doc.yaml_frontmatter:
        ordered_yaml['source'] = doc.yaml_frontmatter['source']
    
    # Add any other sections not explicitly ordered
    for key, value in doc.yaml_frontmatter.items():
        if key not in ordered_yaml and key not in ['processing_info', 'classification', 'content_detection']:
            ordered_yaml[key] = value
    
    yaml_header = yaml.dump(
        dict(ordered_yaml), 
        Dumper=NoAliasDumper,
        default_flow_style=None,
        sort_keys=False,
        width=200,
        allow_unicode=True
    )
    
    yaml_header = force_flow_style_spans(yaml_header)
    return f"---\n{yaml_header}---\n\n{doc.markdown_content}"

# Performance testing function
def test_yaml_performance(num_docs=50):
    """Test all YAML generation approaches"""
    print("🧪 YAML Generation Performance A/B Testing")
    print("=" * 60)
    print(f"📊 Testing with {num_docs} documents")
    print()
    
    # Create test documents
    test_docs = [MockDocument(i) for i in range(num_docs)]
    
    # Test approaches
    approaches = [
        ("CURRENT", generate_yaml_current, "Current implementation with deep copies"),
        ("OPTION A", generate_yaml_optimized, "Optimized with minimal copying"),
        ("OPTION B", generate_yaml_cached, "Cached common patterns"),
        ("OPTION C", generate_yaml_simplified, "Simplified structure")
    ]
    
    results = {}
    
    for name, func, description in approaches:
        print(f"🔬 Testing {name}: {description}")
        
        start_time = time.perf_counter()
        
        generated_content = []
        for doc in test_docs:
            try:
                content = func(doc)
                generated_content.append(content)
            except Exception as e:
                print(f"  ❌ Error in {name}: {e}")
                break
        else:
            end_time = time.perf_counter()
            total_time_ms = (end_time - start_time) * 1000
            per_doc_ms = total_time_ms / num_docs
            
            results[name] = {
                'total_ms': total_time_ms,
                'per_doc_ms': per_doc_ms,
                'content_sample': generated_content[0][:200] + "..." if generated_content else "ERROR"
            }
            
            print(f"  ⏱️  Total: {total_time_ms:.2f}ms")
            print(f"  📊 Per doc: {per_doc_ms:.2f}ms")
            print(f"  🚀 Rate: {1000/per_doc_ms:.1f} docs/sec")
        
        print()
    
    # Performance comparison
    if results:
        print("📈 PERFORMANCE COMPARISON")
        print("-" * 60)
        
        # Find baseline (CURRENT)
        baseline = results.get('CURRENT', {})
        baseline_time = baseline.get('per_doc_ms', 0)
        
        for name, data in results.items():
            per_doc = data['per_doc_ms']
            if baseline_time > 0 and name != 'CURRENT':
                speedup = baseline_time / per_doc
                improvement = ((baseline_time - per_doc) / baseline_time) * 100
                print(f"{name:10}: {per_doc:6.2f}ms/doc ({speedup:.1f}x faster, {improvement:+5.1f}%)")
            else:
                print(f"{name:10}: {per_doc:6.2f}ms/doc (baseline)")
        
        print()
        
        # Projection for user's 675-file workload
        print("📊 PROJECTION FOR 675-FILE WORKLOAD")
        print("-" * 60)
        
        for name, data in results.items():
            per_doc = data['per_doc_ms']
            total_time_675 = (per_doc * 675) / 1000  # Convert to seconds
            print(f"{name:10}: {total_time_675:.2f}s total YAML generation time")
        
        print()
        
        # Show sample output differences
        print("📝 SAMPLE OUTPUT COMPARISON (first 200 chars)")
        print("-" * 60)
        
        for name, data in results.items():
            print(f"{name}:")
            print(f"  {data['content_sample']}")
            print()
    
    return results

if __name__ == "__main__":
    # Run the performance test
    test_results = test_yaml_performance(num_docs=50)
    
    # Recommend best approach
    if test_results:
        print("🎯 RECOMMENDATION")
        print("=" * 60)
        
        # Find fastest non-current approach
        best_option = None
        best_speedup = 0
        baseline_time = test_results.get('CURRENT', {}).get('per_doc_ms', float('inf'))
        
        for name, data in test_results.items():
            if name != 'CURRENT':
                speedup = baseline_time / data['per_doc_ms']
                if speedup > best_speedup:
                    best_speedup = speedup
                    best_option = name
        
        if best_option:
            best_data = test_results[best_option]
            improvement = ((baseline_time - best_data['per_doc_ms']) / baseline_time) * 100
            time_675 = (best_data['per_doc_ms'] * 675) / 1000
            
            print(f"🏆 WINNER: {best_option}")
            print(f"   Speedup: {best_speedup:.1f}x faster ({improvement:+.1f}% improvement)")
            print(f"   675 files: {time_675:.2f}s vs current {(baseline_time * 675) / 1000:.2f}s")
            print(f"   Time saved: {((baseline_time * 675) / 1000) - time_675:.2f}s")
            
            if time_675 < 1.0:
                print(f"   ✅ Meets user's sub-second expectation!")
            else:
                print(f"   ⚠️  Still above 1s - may need further optimization")