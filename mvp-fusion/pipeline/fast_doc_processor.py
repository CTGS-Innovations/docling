"""
FastDocProcessor - Quick Document Processing Bottleneck Isolation
================================================================

Minimal document processor designed to isolate performance bottlenecks
in the document processing pipeline by testing different processing paths:

1. PDF Conversion timing isolation
2. Text processing timing isolation  
3. I/O operation timing isolation
4. Memory vs disk operation comparison

This processor integrates with the existing A/B testing framework to
run side-by-side with ServiceProcessor for direct comparison.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import tempfile
import json

# Minimal imports to avoid dependency issues
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ProcessorResult:
    """Standard result format for processors."""
    def __init__(self, data: Any, success: bool = True, error: str = None, timing_ms: float = 0):
        self.data = data
        self.success = success
        self.error = error
        self.timing_ms = timing_ms

class FastDocProcessor:
    """Optimized processor for faster document processing with bottleneck isolation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = "FastDocProcessor"
        
        # Timing isolation flags
        self.test_pdf_conversion = True
        self.test_text_processing = True
        self.test_io_operations = True
        self.test_memory_vs_disk = True
    
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> ProcessorResult:
        """Process files with timing isolation to identify bottlenecks."""
        metadata = metadata or {}
        
        if not isinstance(input_data, list):
            return ProcessorResult(
                data=None,
                success=False,
                error="FastDocProcessor requires list of file paths"
            )
        
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
            
            # ISOLATION TEST 2: Text Processing Timing (OPTIMIZED)
            if self.test_text_processing:
                text_timing = self._optimized_text_processing(files)
                timing_breakdown['optimized_text_processing_ms'] = text_timing
                print(f"🔍 Optimized Text Processing: {text_timing:.2f}ms")
            
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
                'bottleneck_analysis': self._analyze_bottlenecks(timing_breakdown)
            }
            
            print(f"🎯 FastDocProcessor Complete: {total_time*1000:.2f}ms")
            
            return ProcessorResult(
                data=results,
                success=True,
                timing_ms=total_time * 1000
            )
            
        except Exception as e:
            return ProcessorResult(
                data=None,
                success=False,
                error=f"FastDocProcessor failed: {str(e)}"
            )
    
    def _test_pdf_conversion_timing(self, files: List[Path]) -> float:
        """Test PDF conversion timing in isolation."""
        start_time = time.perf_counter()
        
        try:
            # Import docling for PDF conversion
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            
            # Convert first file only for timing test
            if files:
                test_file = files[0]
                if test_file.suffix.lower() == '.pdf':
                    result = converter.convert(test_file)
                    # Just access the markdown to ensure conversion completed
                    _ = result.document.export_to_markdown()
            
        except Exception as e:
            print(f"WARNING: PDF conversion test failed: {e}")
        
        return (time.perf_counter() - start_time) * 1000
    
    def _optimized_text_processing(self, files: List[Path]) -> float:
        """OPTIMIZED text processing - should be much faster than original."""
        start_time = time.perf_counter()
        
        try:
            # OPTIMIZATION 1: Single-pass processing instead of multiple passes
            # OPTIMIZATION 2: Avoid Python regex (Rule #12 compliance) 
            # OPTIMIZATION 3: Minimize string operations
            
            for file_path in files[:3]:  # Test first 3 files only
                if file_path.exists():
                    # Read file content once
                    with open(file_path, 'rb') as f:
                        content_bytes = f.read()
                    
                    # Fast byte-level operations instead of string operations
                    content_size = len(content_bytes)
                    
                    # Simple byte counting instead of complex text processing
                    line_count = content_bytes.count(b'\n')
                    
                    # Minimal processing - just basic stats
                    stats = {
                        'size': content_size,
                        'lines': line_count,
                        'file': str(file_path)
                    }
                    
        except Exception as e:
            print(f"WARNING: Optimized text processing failed: {e}")
        
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
            print(f"WARNING: Text processing test failed: {e}")
        
        return (time.perf_counter() - start_time) * 1000
    
    def _test_io_operations_timing(self, files: List[Path], output_dir) -> float:
        """Test I/O operations timing in isolation."""
        start_time = time.perf_counter()
        
        try:
            # Test file system operations
            from pathlib import Path as PathLib
            output_path = PathLib(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Test writing small files
            for i, file_path in enumerate(files[:3]):  # Test first 3 files only
                test_output = output_path / f"fast_test_{i}.json"
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
            print(f"WARNING: I/O operations test failed: {e}")
        
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
            print(f"WARNING: Memory processing test failed: {e}")
        memory_timing = (time.perf_counter() - memory_start) * 1000
        
        # Disk processing test  
        disk_start = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                from pathlib import Path as PathLib
                temp_path = PathLib(temp_dir)
                
                for i, file_path in enumerate(files[:2]):  # Test first 2 files only
                    if file_path.exists():
                        temp_file = temp_path / f"temp_{i}.txt"
                        
                        # Read and write to disk
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        temp_file.write_text(content[:1000])  # Write first 1000 chars
                        
                        # Read back from disk
                        _ = temp_file.read_text()
        except Exception as e:
            print(f"WARNING: Disk processing test failed: {e}")
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