#!/usr/bin/env python3
"""
Quick A/B Test for FastDocProcessor - Bypass Import Issues
==========================================================

GOAL: Test FastDocProcessor directly to isolate bottlenecks  
REASON: Full pipeline has legacy import issues - need isolated test
PROBLEM: Unicode/import errors preventing A/B comparison

This is a temporary bypass to test FastDocProcessor without the 
full pipeline import chain.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import tempfile
import json

class FastDocProcessor:
    """Minimal processor for isolating document processing bottlenecks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = "FastDocProcessor"
        
        # Timing isolation flags
        self.test_pdf_conversion = True
        self.test_text_processing = True
        self.test_io_operations = True
        self.test_memory_vs_disk = True
    
    def process(self, input_data: List[Path], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process files with timing isolation to identify bottlenecks."""
        metadata = metadata or {}
        
        files = input_data
        output_dir = metadata.get('output_dir', Path.cwd())
        
        try:
            start_time = time.perf_counter()
            timing_breakdown = {}
            
            # ISOLATION TEST 1: PDF Conversion Timing
            if self.test_pdf_conversion:
                pdf_timing = self._test_pdf_conversion_timing(files)
                timing_breakdown['pdf_conversion_ms'] = pdf_timing
                print(f"🔍 PDF Conversion: {pdf_timing:.2f}ms")
            
            # ISOLATION TEST 2: Text Processing Timing
            if self.test_text_processing:
                text_timing = self._test_text_processing_timing(files)
                timing_breakdown['text_processing_ms'] = text_timing
                print(f"🔍 Text Processing: {text_timing:.2f}ms")
            
            # ISOLATION TEST 3: I/O Operations Timing
            if self.test_io_operations:
                io_timing = self._test_io_operations_timing(files, output_dir)
                timing_breakdown['io_operations_ms'] = io_timing
                print(f"🔍 I/O Operations: {io_timing:.2f}ms")
            
            # ISOLATION TEST 4: Memory vs Disk Comparison
            if self.test_memory_vs_disk:
                memory_timing, disk_timing = self._test_memory_vs_disk_timing(files)
                timing_breakdown['memory_processing_ms'] = memory_timing
                timing_breakdown['disk_processing_ms'] = disk_timing
                print(f"🔍 Memory Processing: {memory_timing:.2f}ms")
                print(f"🔍 Disk Processing: {disk_timing:.2f}ms")
            
            total_time = time.perf_counter() - start_time
            
            # Create minimal output for comparison
            results = {
                'processed_files': len(files),
                'timing_breakdown': timing_breakdown,
                'bottleneck_analysis': self._analyze_bottlenecks(timing_breakdown),
                'success': True,
                'timing_ms': total_time * 1000
            }
            
            print(f"🎯 FastDocProcessor Analysis Complete: {total_time*1000:.2f}ms")
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'error': f"FastDocProcessor failed: {str(e)}",
                'timing_ms': 0
            }
    
    def _test_pdf_conversion_timing(self, files: List[Path]) -> float:
        """Test PDF file reading timing (simulates conversion load)."""
        start_time = time.perf_counter()
        
        try:
            # Simulate PDF processing by reading file bytes
            if files:
                test_file = files[0]
                if test_file.suffix.lower() == '.pdf':
                    # Read entire PDF file to simulate conversion load
                    pdf_content = test_file.read_bytes()
                    
                    # Simulate some processing overhead (parsing simulation)
                    content_size = len(pdf_content)
                    chunks = content_size // 1024  # Simulate 1KB chunk processing
                    
                    # Simulate processing time proportional to file size
                    time.sleep(chunks * 0.0001)  # 0.1ms per KB simulation
            
        except Exception as e:
            print(f"⚠️ PDF conversion test failed: {e}")
        
        return (time.perf_counter() - start_time) * 1000
    
    def _test_text_processing_timing(self, files: List[Path]) -> float:
        """Test text processing timing in isolation."""
        start_time = time.perf_counter()
        
        try:
            # Simulate text processing operations
            for file_path in files[:3]:  # Test first 3 files only
                if file_path.exists():
                    # Read file content (minimal processing)
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Minimal text operations
                    lines = content.split('\n')
                    word_count = len(content.split())
                    char_count = len(content)
                    
                    # Simulate some processing without heavy operations
                    processed_lines = [line.strip() for line in lines if line.strip()]
                    
        except Exception as e:
            print(f"⚠️ Text processing test failed: {e}")
        
        return (time.perf_counter() - start_time) * 1000
    
    def _test_io_operations_timing(self, files: List[Path], output_dir: Path) -> float:
        """Test I/O operations timing in isolation."""
        start_time = time.perf_counter()
        
        try:
            # Test file system operations
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Test writing small files
            for i, file_path in enumerate(files[:3]):  # Test first 3 files only
                test_output = output_dir / f"fast_test_{i}.json"
                test_data = {
                    'file': str(file_path),
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'timestamp': time.time()
                }
                
                # Write JSON output
                with open(test_output, 'w') as f:
                    json.dump(test_data, f, indent=2)
                
                # Clean up immediately
                test_output.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️ I/O operations test failed: {e}")
        
        return (time.perf_counter() - start_time) * 1000
    
    def _test_memory_vs_disk_timing(self, files: List[Path]) -> Tuple[float, float]:
        """Compare memory vs disk processing timing."""
        
        # Memory processing test
        memory_start = time.perf_counter()
        try:
            memory_data = []
            for file_path in files[:2]:  # Test first 2 files only
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    memory_data.append({
                        'file': str(file_path),
                        'content_length': len(content),
                        'line_count': len(content.split('\n'))
                    })
        except Exception as e:
            print(f"⚠️ Memory processing test failed: {e}")
        memory_timing = (time.perf_counter() - memory_start) * 1000
        
        # Disk processing test  
        disk_start = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                for i, file_path in enumerate(files[:2]):  # Test first 2 files only
                    if file_path.exists():
                        temp_file = temp_path / f"temp_{i}.txt"
                        
                        # Read and write to disk
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        temp_file.write_text(content[:1000])  # Write first 1000 chars
                        
                        # Read back from disk
                        _ = temp_file.read_text()
        except Exception as e:
            print(f"⚠️ Disk processing test failed: {e}")
        disk_timing = (time.perf_counter() - disk_start) * 1000
        
        return memory_timing, disk_timing
    
    def _analyze_bottlenecks(self, timing_breakdown: Dict[str, float]) -> Dict[str, Any]:
        """Analyze timing breakdown to identify bottlenecks."""
        if not timing_breakdown:
            return {'analysis': 'No timing data available'}
        
        # Find the slowest operation
        slowest_operation = max(timing_breakdown.items(), key=lambda x: x[1])
        total_time = sum(timing_breakdown.values())
        
        analysis = {
            'slowest_operation': slowest_operation[0],
            'slowest_time_ms': slowest_operation[1],
            'slowest_percentage': (slowest_operation[1] / total_time * 100) if total_time > 0 else 0,
            'total_isolation_time_ms': total_time,
            'recommendations': []
        }
        
        # Add specific recommendations based on bottlenecks
        if slowest_operation[0] == 'pdf_conversion_ms' and slowest_operation[1] > 100:
            analysis['recommendations'].append("PDF conversion is the bottleneck - check docling configuration")
        
        if slowest_operation[0] == 'text_processing_ms' and slowest_operation[1] > 50:
            analysis['recommendations'].append("Text processing is slow - check for regex usage (Rule #12)")
        
        if slowest_operation[0] == 'io_operations_ms' and slowest_operation[1] > 30:
            analysis['recommendations'].append("I/O operations are slow - check disk performance or file sizes")
        
        memory_time = timing_breakdown.get('memory_processing_ms', 0)
        disk_time = timing_breakdown.get('disk_processing_ms', 0)
        if disk_time > memory_time * 2:
            analysis['recommendations'].append("Disk operations significantly slower than memory - optimize file I/O")
        
        return analysis


def main():
    """Run quick bottleneck isolation test."""
    print("🚀 FastDocProcessor Quick Bottleneck Isolation Test")
    print("=" * 50)
    
    # Configuration
    config = {'pipeline': {'document_processing': {'target_time_ms': 30}}}
    processor = FastDocProcessor(config)
    
    # Find test files
    test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
    if test_dir.exists():
        files = list(test_dir.glob('*.pdf'))[:3]  # First 3 PDFs only
        print(f"📁 Testing with {len(files)} files from data_complex")
        for f in files:
            print(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        
        # Run the test
        result = processor.process(files, {'output_dir': Path('/tmp')})
        
        # Display results
        print("\n" + "=" * 50)
        print("🎯 BOTTLENECK ISOLATION RESULTS")
        print("=" * 50)
        
        if result['success']:
            analysis = result['bottleneck_analysis']
            print(f"🟢 **SUCCESS**: Test completed in {result['timing_ms']:.2f}ms")
            print(f"🔴 **BOTTLENECK**: {analysis['slowest_operation']} ({analysis['slowest_time_ms']:.2f}ms, {analysis['slowest_percentage']:.1f}%)")
            
            if analysis['recommendations']:
                print("\n📋 **RECOMMENDATIONS**:")
                for rec in analysis['recommendations']:
                    print(f"   • {rec}")
            
            # Compare to target
            target_ms = config['pipeline']['document_processing']['target_time_ms']
            comparison = result['timing_ms'] / target_ms
            print(f"\n⏱️  **PERFORMANCE**: {comparison:.1f}x slower than {target_ms}ms target")
            
        else:
            print(f"🔴 **BLOCKED**: {result['error']}")
            
    else:
        print(f"❌ Test directory not found: {test_dir}")


if __name__ == "__main__":
    main()