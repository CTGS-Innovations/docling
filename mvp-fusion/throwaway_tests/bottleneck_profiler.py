#!/usr/bin/env python3
"""
Comprehensive Bottleneck Profiler
==================================
GOAL: Identify the 549ms mystery overhead in pipeline processing
REASON: User has 41.8% unaccounted time - something is consuming CPU cycles
PROBLEM: Need to find the hidden bottleneck before architectural changes

Focus areas:
1. CPU pinning and context switching
2. I/O batching and caching opportunities  
3. YAML generation optimization
4. Memory allocation/garbage collection overhead
"""

import time
import psutil
import threading
import os
import gc
import sys
from pathlib import Path
import cProfile
import pstats
import io
from contextlib import contextmanager

class BottleneckProfiler:
    def __init__(self):
        self.timings = {}
        self.memory_samples = []
        self.cpu_samples = []
        self.gc_events = []
        self.context_switches = []
        
    @contextmanager
    def profile_section(self, section_name):
        """Profile a specific section of code"""
        # Get initial metrics
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent(interval=None)
        start_ctx_switches = psutil.Process().num_ctx_switches()
        
        # Enable garbage collection tracking
        gc.set_debug(gc.DEBUG_STATS)
        gc_before = gc.get_count()
        
        try:
            yield
        finally:
            # Get final metrics
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent(interval=None)
            end_ctx_switches = psutil.Process().num_ctx_switches()
            
            gc_after = gc.get_count()
            gc.set_debug(0)
            
            # Calculate differences
            duration_ms = (end_time - start_time) * 1000
            memory_delta = end_memory - start_memory
            ctx_switch_delta = (end_ctx_switches.voluntary - start_ctx_switches.voluntary,
                              end_ctx_switches.involuntary - start_ctx_switches.involuntary)
            
            # Store results
            self.timings[section_name] = {
                'duration_ms': duration_ms,
                'memory_delta_mb': memory_delta,
                'cpu_before': start_cpu,
                'cpu_after': end_cpu,
                'ctx_switches_voluntary': ctx_switch_delta[0],
                'ctx_switches_involuntary': ctx_switch_delta[1],
                'gc_collections': [gc_after[i] - gc_before[i] for i in range(3)]
            }

    def profile_function_calls(self, func, *args, **kwargs):
        """Profile function call patterns"""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Capture profiling results
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('tottime')
        ps.print_stats(20)  # Top 20 time-consuming functions
        
        profile_output = s.getvalue()
        return result, profile_output

    def get_cpu_affinity_info(self):
        """Get CPU affinity and core information"""
        process = psutil.Process()
        return {
            'cpu_affinity': process.cpu_affinity(),
            'cpu_count': psutil.cpu_count(),
            'current_cpu': psutil.Process().cpu_num() if hasattr(psutil.Process(), 'cpu_num') else 'unknown'
        }

    def test_cpu_pinning_impact(self):
        """Test impact of CPU pinning on performance"""
        print("🔍 Testing CPU Pinning Impact")
        
        # Test 1: No CPU pinning (default)
        start_time = time.perf_counter()
        self._cpu_intensive_work(duration=0.5)  # 500ms work
        no_pinning_time = (time.perf_counter() - start_time) * 1000
        
        # Test 2: Pin to CPU 0
        try:
            psutil.Process().cpu_affinity([0])
            start_time = time.perf_counter()
            self._cpu_intensive_work(duration=0.5)  # 500ms work
            cpu0_pinning_time = (time.perf_counter() - start_time) * 1000
        except:
            cpu0_pinning_time = "Failed to pin to CPU 0"
        
        # Test 3: Pin to CPU 1 (if available)
        try:
            if psutil.cpu_count() > 1:
                psutil.Process().cpu_affinity([1])
                start_time = time.perf_counter()
                self._cpu_intensive_work(duration=0.5)  # 500ms work
                cpu1_pinning_time = (time.perf_counter() - start_time) * 1000
            else:
                cpu1_pinning_time = "Only 1 CPU available"
        except:
            cpu1_pinning_time = "Failed to pin to CPU 1"
        
        # Restore default affinity
        try:
            psutil.Process().cpu_affinity(list(range(psutil.cpu_count())))
        except:
            pass
        
        return {
            'no_pinning_ms': no_pinning_time,
            'cpu0_pinning_ms': cpu0_pinning_time,
            'cpu1_pinning_ms': cpu1_pinning_time
        }

    def _cpu_intensive_work(self, duration):
        """Simulate CPU-intensive work"""
        start = time.perf_counter()
        result = 0
        while time.perf_counter() - start < duration:
            for i in range(10000):
                result += i * 0.001

    def test_io_batching_opportunities(self):
        """Test I/O operations for batching potential"""
        print("💾 Testing I/O Batching Opportunities")
        
        test_dir = Path("throwaway_tests/io_test_temp")
        test_dir.mkdir(exist_ok=True)
        
        # Test 1: Individual file writes (current approach)
        num_files = 50
        file_content = "x" * 1000  # 1KB content per file
        
        with self.profile_section("individual_file_writes"):
            for i in range(num_files):
                file_path = test_dir / f"individual_{i}.txt"
                with open(file_path, 'w') as f:
                    f.write(file_content)
        
        # Test 2: Batched file writes
        batch_size = 10
        with self.profile_section("batched_file_writes"):
            for batch_start in range(0, num_files, batch_size):
                batch_files = []
                for i in range(batch_start, min(batch_start + batch_size, num_files)):
                    batch_files.append((test_dir / f"batched_{i}.txt", file_content))
                
                # Write batch
                for file_path, content in batch_files:
                    with open(file_path, 'w') as f:
                        f.write(content)
        
        # Test 3: Single bulk write operation
        with self.profile_section("bulk_file_write"):
            bulk_content = []
            for i in range(num_files):
                bulk_content.append(f"File {i}: {file_content}")
            
            bulk_file = test_dir / "bulk_output.txt"
            with open(bulk_file, 'w') as f:
                f.write('\n'.join(bulk_content))
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_yaml_caching_impact(self):
        """Test YAML generation caching strategies"""
        print("📋 Testing YAML Caching Strategies")
        
        import yaml
        from collections import OrderedDict
        
        # Sample YAML data (similar to your pipeline)
        sample_yaml_data = OrderedDict([
            ('conversion', {
                'engine': 'docling_v1',
                'version': '1.2.3',
                'timestamp': '2025-09-25T12:00:00Z',
                'processing_time_ms': 123.45
            }),
            ('content_analysis', {
                'has_tables': True,
                'has_images': False,
                'language': 'en',
                'page_count': 15,
                'word_count': 2500
            }),
            ('processing', {
                'pipeline_version': 'v2.1',
                'worker_id': 'worker-1',
                'batch_id': 'batch-001'
            }),
            ('classification', {
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
            })
        ])
        
        # Test 1: Standard YAML generation (current)
        num_documents = 100
        with self.profile_section("standard_yaml_generation"):
            for i in range(num_documents):
                # Simulate document-specific data
                doc_data = sample_yaml_data.copy()
                doc_data['source'] = {'filename': f'doc_{i}.pdf'}
                
                yaml_output = yaml.dump(dict(doc_data), default_flow_style=False)
        
        # Test 2: Template-based YAML generation
        yaml_template = yaml.dump(dict(sample_yaml_data), default_flow_style=False)
        with self.profile_section("template_yaml_generation"):
            for i in range(num_documents):
                # Use string replacement instead of full YAML generation
                doc_yaml = yaml_template.replace('doc_0.pdf', f'doc_{i}.pdf')
        
        # Test 3: Pre-compiled YAML sections
        static_sections = {}
        for key in ['conversion', 'processing']:
            static_sections[key] = yaml.dump({key: sample_yaml_data[key]}, default_flow_style=False)
        
        with self.profile_section("precompiled_yaml_sections"):
            for i in range(num_documents):
                yaml_parts = []
                
                # Use pre-compiled static sections
                yaml_parts.extend(static_sections.values())
                
                # Generate only dynamic sections
                dynamic_data = {
                    'source': {'filename': f'doc_{i}.pdf'},
                    'classification': sample_yaml_data['classification']
                }
                yaml_parts.append(yaml.dump(dynamic_data, default_flow_style=False))
                
                final_yaml = ''.join(yaml_parts)

    def test_memory_allocation_patterns(self):
        """Test memory allocation and garbage collection impact"""
        print("🧠 Testing Memory Allocation Patterns")
        
        # Test 1: Large object creation (potential GC pressure)
        with self.profile_section("large_object_creation"):
            large_objects = []
            for i in range(100):
                # Simulate large document processing data
                large_obj = {
                    'content': 'x' * 10000,  # 10KB content
                    'metadata': {'id': i, 'size': 10000},
                    'entities': [f'entity_{j}' for j in range(100)],
                    'processed_data': list(range(1000))
                }
                large_objects.append(large_obj)
        
        # Test 2: Small object creation (current approach)
        with self.profile_section("small_object_creation"):
            small_objects = []
            for i in range(100):
                small_obj = {
                    'id': i,
                    'status': 'processed',
                    'result': f'result_{i}'
                }
                small_objects.append(small_obj)
        
        # Force garbage collection and measure impact
        with self.profile_section("garbage_collection"):
            gc.collect()

    def run_comprehensive_analysis(self):
        """Run comprehensive bottleneck analysis"""
        print("🔍 COMPREHENSIVE BOTTLENECK ANALYSIS")
        print("=" * 60)
        print("🎯 Goal: Find the 549ms mystery overhead")
        print()
        
        # Get system info
        cpu_info = self.get_cpu_affinity_info()
        print(f"💻 System: {cpu_info['cpu_count']} cores, affinity: {cpu_info['cpu_affinity']}")
        print()
        
        # Test CPU pinning impact
        cpu_pinning_results = self.test_cpu_pinning_impact()
        print("📊 CPU Pinning Results:")
        for method, timing in cpu_pinning_results.items():
            print(f"   {method}: {timing}")
        print()
        
        # Test I/O batching
        self.test_io_batching_opportunities()
        
        # Test YAML caching
        self.test_yaml_caching_impact()
        
        # Test memory patterns
        self.test_memory_allocation_patterns()
        
        # Analyze results
        print("📊 BOTTLENECK ANALYSIS RESULTS")
        print("-" * 60)
        
        for section_name, metrics in self.timings.items():
            print(f"{section_name}:")
            print(f"   Duration: {metrics['duration_ms']:.2f}ms")
            print(f"   Memory Δ: {metrics['memory_delta_mb']:+.2f}MB")
            print(f"   Ctx switches: {metrics['ctx_switches_voluntary']}V, {metrics['ctx_switches_involuntary']}I")
            print(f"   GC events: {metrics['gc_collections']}")
            print()
        
        # Identify bottlenecks
        self._identify_bottlenecks()

    def _identify_bottlenecks(self):
        """Identify the primary bottlenecks from collected data"""
        print("🎯 BOTTLENECK IDENTIFICATION")
        print("=" * 60)
        
        # Sort by duration
        sorted_timings = sorted(self.timings.items(), key=lambda x: x[1]['duration_ms'], reverse=True)
        
        print("⏱️  Top Time Consumers:")
        for i, (name, metrics) in enumerate(sorted_timings[:5]):
            print(f"   {i+1}. {name}: {metrics['duration_ms']:.2f}ms")
        
        print()
        
        # Memory pressure analysis
        high_memory_operations = [
            (name, metrics) for name, metrics in self.timings.items()
            if abs(metrics['memory_delta_mb']) > 10  # >10MB change
        ]
        
        if high_memory_operations:
            print("🧠 High Memory Pressure Operations:")
            for name, metrics in high_memory_operations:
                print(f"   {name}: {metrics['memory_delta_mb']:+.2f}MB")
        
        print()
        
        # Context switching analysis
        high_context_switch_ops = [
            (name, metrics) for name, metrics in self.timings.items()
            if metrics['ctx_switches_voluntary'] > 10 or metrics['ctx_switches_involuntary'] > 5
        ]
        
        if high_context_switch_ops:
            print("🔄 High Context Switching Operations:")
            for name, metrics in high_context_switch_ops:
                v, i = metrics['ctx_switches_voluntary'], metrics['ctx_switches_involuntary']
                print(f"   {name}: {v}V, {i}I switches")
        
        print()
        
        # Recommendations
        print("💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 60)
        
        if sorted_timings:
            slowest = sorted_timings[0]
            print(f"🎯 PRIMARY TARGET: {slowest[0]} ({slowest[1]['duration_ms']:.2f}ms)")
        
        if high_memory_operations:
            print("🧠 MEMORY OPTIMIZATION: Reduce memory allocation in high-pressure operations")
        
        if high_context_switch_ops:
            print("🔄 CPU PINNING: Consider pinning processes to specific cores")
        
        # Specific recommendations based on patterns
        yaml_times = [metrics['duration_ms'] for name, metrics in self.timings.items() if 'yaml' in name.lower()]
        io_times = [metrics['duration_ms'] for name, metrics in self.timings.items() if 'file' in name.lower() or 'io' in name.lower()]
        
        if yaml_times:
            avg_yaml_time = sum(yaml_times) / len(yaml_times)
            print(f"📋 YAML OPTIMIZATION: Average {avg_yaml_time:.2f}ms - implement caching/templates")
        
        if io_times:
            avg_io_time = sum(io_times) / len(io_times)
            print(f"💾 I/O OPTIMIZATION: Average {avg_io_time:.2f}ms - implement batching")

def main():
    profiler = BottleneckProfiler()
    profiler.run_comprehensive_analysis()

if __name__ == "__main__":
    main()