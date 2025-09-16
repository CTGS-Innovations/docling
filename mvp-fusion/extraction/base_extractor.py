#!/usr/bin/env python3
"""
Base extractor interface for document processing methodologies.
Defines the contract for all extraction engines as sidecar components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Union
from pathlib import Path
import time


class ExtractionResult:
    """Standard result format for all extractors"""
    
    def __init__(self, success: bool, file_path: str, pages: int = 0, 
                 output_path: str = None, error: str = None, **kwargs):
        self.success = success
        self.file_path = file_path
        self.pages = pages
        self.output_path = output_path
        self.error = error
        self.metadata = kwargs
        self.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization"""
        return {
            'success': self.success,
            'file': self.file_path,
            'pages': self.pages,
            'output': self.output_path,
            'error': self.error,
            'timestamp': self.timestamp,
            **self.metadata
        }


class BaseExtractor(ABC):
    """
    Abstract base class for all document extraction engines.
    
    Each extractor implements a specific methodology for document processing:
    - Production: High-speed, lightweight extraction for bulk processing
    - Precision: High-accuracy extraction with advanced parsing
    - Specialized: Domain-specific extraction (scientific, legal, etc.)
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.performance_metrics = {
            'total_files': 0,
            'total_pages': 0,
            'total_time': 0.0,
            'successful_extractions': 0,
            'total_input_bytes': 0,
            'total_output_bytes': 0
        }
    
    @abstractmethod
    def extract_single(self, file_path: Union[str, Path], output_dir: Union[str, Path], 
                      **kwargs) -> ExtractionResult:
        """
        Extract content from a single document.
        
        Args:
            file_path: Path to input document
            output_dir: Directory to save output
            **kwargs: Extractor-specific parameters
            
        Returns:
            ExtractionResult with processing outcome
        """
        pass
    
    @abstractmethod
    def extract_batch(self, file_paths: List[Union[str, Path]], 
                     output_dir: Union[str, Path], 
                     max_workers: int = None, **kwargs) -> tuple[List[ExtractionResult], float]:
        """
        Extract content from multiple documents efficiently.
        
        Args:
            file_paths: List of input document paths
            output_dir: Directory to save outputs
            max_workers: Maximum parallel workers
            **kwargs: Extractor-specific parameters
            
        Returns:
            Tuple of (results_list, total_processing_time)
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats (e.g., ['pdf', 'docx'])"""
        pass
    
    @abstractmethod
    def get_output_formats(self) -> List[str]:
        """Return list of supported output formats (e.g., ['markdown', 'json'])"""
        pass
    
    def can_process(self, file_path: Union[str, Path]) -> bool:
        """Check if this extractor can process the given file"""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower().lstrip('.')
        return file_ext in self.get_supported_formats()
    
    def update_metrics(self, results: List[ExtractionResult], processing_time: float):
        """Update performance metrics"""
        successful = [r for r in results if r.success]
        self.performance_metrics['total_files'] += len(results)
        self.performance_metrics['total_pages'] += sum(r.pages for r in successful)
        self.performance_metrics['total_time'] += processing_time
        self.performance_metrics['successful_extractions'] += len(successful)
        
        # Add input/output file sizes (get for free from file system)
        for result in successful:
            try:
                # Input file size
                input_size = Path(result.file_path).stat().st_size
                self.performance_metrics['total_input_bytes'] += input_size
                
                # Output file size (if available)
                if hasattr(result, 'output_path') and result.output_path:
                    try:
                        output_size = Path(result.output_path).stat().st_size
                        self.performance_metrics['total_output_bytes'] += output_size
                    except:
                        pass
            except:
                pass  # Skip if file size unavailable
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = self.performance_metrics.copy()
        if metrics['total_time'] > 0:
            metrics['pages_per_second'] = metrics['total_pages'] / metrics['total_time']
            metrics['files_per_second'] = metrics['total_files'] / metrics['total_time']
            metrics['input_mb_per_sec'] = (metrics['total_input_bytes'] / 1024 / 1024) / metrics['total_time']
            metrics['success_rate'] = metrics['successful_extractions'] / metrics['total_files']
            
            # Compression ratio
            if metrics['total_output_bytes'] > 0:
                metrics['compression_ratio'] = metrics['total_input_bytes'] / metrics['total_output_bytes']
            else:
                metrics['compression_ratio'] = 0
        else:
            metrics['pages_per_second'] = 0
            metrics['files_per_second'] = 0
            metrics['input_mb_per_sec'] = 0
            metrics['success_rate'] = 0
            metrics['compression_ratio'] = 0
        
        return metrics
    
    def reset_metrics(self):
        """Reset performance tracking"""
        self.performance_metrics = {
            'total_files': 0,
            'total_pages': 0,
            'total_time': 0.0,
            'successful_extractions': 0
        }
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"