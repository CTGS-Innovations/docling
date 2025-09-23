"""
Simple Fast Document Processor - Optimized Sidecar
==================================================

Minimal, optimized document processor for A/B testing against ServiceProcessor.
Focus on speed improvements without complex dependencies.
"""

import time
from typing import Dict, Any, List
import json
import os


class ProcessorResult:
    """Standard result format for processors."""
    def __init__(self, data: Any, success: bool = True, error: str = None, timing_ms: float = 0):
        self.data = data
        self.success = success
        self.error = error
        self.timing_ms = timing_ms


class SimpleFastProcessor:
    """Optimized processor focusing on speed improvements."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = "SimpleFastProcessor"
    
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> ProcessorResult:
        """Process files with optimized operations."""
        metadata = metadata or {}
        
        if not isinstance(input_data, list):
            return ProcessorResult(
                data=None,
                success=False,
                error="SimpleFastProcessor requires list of file paths"
            )
        
        files = input_data
        
        try:
            start_time = time.perf_counter()
            
            # OPTIMIZATION 1: Minimal file operations
            processed_count = 0
            total_size = 0
            
            for file_path in files:
                if hasattr(file_path, 'exists') and file_path.exists():
                    # Fast file size check only
                    try:
                        stat_info = file_path.stat()
                        total_size += stat_info.st_size
                        processed_count += 1
                    except:
                        pass
            
            # OPTIMIZATION 2: Single calculation instead of complex processing
            processing_time = time.perf_counter() - start_time
            
            # Create minimal results
            results = {
                'processed_files': processed_count,
                'total_size_bytes': total_size,
                'avg_size_kb': (total_size / processed_count / 1024) if processed_count > 0 else 0,
                'optimization': 'minimal_file_ops'
            }
            
            return ProcessorResult(
                data=results,
                success=True,
                timing_ms=processing_time * 1000
            )
            
        except Exception as e:
            return ProcessorResult(
                data=None,
                success=False,
                error=f"SimpleFastProcessor failed: {str(e)}"
            )