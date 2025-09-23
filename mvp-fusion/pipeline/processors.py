"""
Pipeline Processor Implementations
==================================

Clean processor implementations that wrap existing processors and provide
a standardized interface for the pipeline architecture.

This module provides:
- ServiceProcessorWrapper - wraps the existing ServiceProcessor
- FusionProcessorWrapper - wraps the existing FusionPipeline  
- AbstractProcessor - base class for all processors
- ProcessorFactory - creates processors by name

Design goals:
- Standardized interface for all processors
- Performance monitoring and timing
- Configuration-based processor selection
- A/B testing capability
- Easy to add new processors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from pathlib import Path
import time

class ProcessorResult:
    """Standard result format for all processors."""
    
    def __init__(self, data: Any, success: bool = True, error: str = None, timing_ms: float = 0):
        self.data = data
        self.success = success
        self.error = error
        self.timing_ms = timing_ms
        self.metadata = {}

class AbstractProcessor(ABC):
    """Base class for all pipeline processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> ProcessorResult:
        """Process input data and return standardized result."""
        pass
    
    def get_processor_name(self) -> str:
        """Get the processor name for logging and identification."""
        return self.name

class ServiceProcessorWrapper(AbstractProcessor):
    """Wrapper for the existing ServiceProcessor."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Import and initialize the actual ServiceProcessor
        try:
            from pipeline.legacy.service_processor import ServiceProcessor
            max_workers = config.get('max_workers', 8)
            self.processor = ServiceProcessor(config, max_workers)
            self.name = "ServiceProcessor"
        except ImportError as e:
            raise RuntimeError(f"Failed to import ServiceProcessor: {e}")
    
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> ProcessorResult:
        """Process files using ServiceProcessor."""
        metadata = metadata or {}
        
        try:
            start_time = time.perf_counter()
            
            # ServiceProcessor expects list of file paths and output directory
            if isinstance(input_data, list):
                files = input_data
                output_dir = metadata.get('output_dir', Path.cwd())
                
                # Call the ServiceProcessor
                results, timing = self.processor.process_files_service(files, output_dir)
                
                processing_time = time.perf_counter() - start_time
                
                return ProcessorResult(
                    data=results,
                    success=True,
                    timing_ms=processing_time * 1000
                )
            else:
                return ProcessorResult(
                    data=None,
                    success=False,
                    error="ServiceProcessor requires list of file paths"
                )
                
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            return ProcessorResult(
                data=None,
                success=False,
                error=str(e),
                timing_ms=processing_time * 1000
            )

class FusionProcessorWrapper(AbstractProcessor):
    """Wrapper for the existing FusionPipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Import and initialize the actual FusionPipeline
        try:
            from pipeline.legacy.fusion_pipeline import FusionPipeline
            self.processor = FusionPipeline(config)
            self.name = "FusionPipeline"
        except ImportError as e:
            raise RuntimeError(f"Failed to import FusionPipeline: {e}")
    
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> ProcessorResult:
        """Process files using FusionPipeline."""
        metadata = metadata or {}
        
        try:
            start_time = time.perf_counter()
            
            # FusionPipeline expects extractor, files, output_dir, max_workers
            if isinstance(input_data, list):
                files = input_data
                output_dir = metadata.get('output_dir', Path.cwd())
                max_workers = metadata.get('max_workers', 8)
                
                # Create a minimal extractor for FusionPipeline
                # This is a simplified approach - in practice you'd pass the real extractor
                from extraction import create_extractor
                extractor = create_extractor('highspeed_markdown_general', self.config)
                
                # Call the FusionPipeline
                results, timing = self.processor.process_files(extractor, files, output_dir, max_workers)
                
                processing_time = time.perf_counter() - start_time
                
                return ProcessorResult(
                    data=results,
                    success=True,
                    timing_ms=processing_time * 1000
                )
            else:
                return ProcessorResult(
                    data=None,
                    success=False,
                    error="FusionPipeline requires list of file paths"
                )
                
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            return ProcessorResult(
                data=None,
                success=False,
                error=str(e),
                timing_ms=processing_time * 1000
            )

class ProcessorFactory:
    """Factory for creating processors by name."""
    
    _processors = {
        'service_processor': ServiceProcessorWrapper,
        'fusion_pipeline': FusionProcessorWrapper,
        'fast_doc_processor': None,  # Lazy loaded
        'simple_fast_processor': None,  # Lazy loaded
        'optimized_doc_processor': None,  # Lazy loaded
    }
    
    @classmethod
    def create(cls, processor_name: str, config: Dict[str, Any]) -> AbstractProcessor:
        """Create a processor by name."""
        if processor_name not in cls._processors:
            available = list(cls._processors.keys())
            raise ValueError(f"Unknown processor '{processor_name}'. Available: {available}")
        
        # Lazy load processors to avoid circular imports
        if processor_name == 'fast_doc_processor' and cls._processors[processor_name] is None:
            from pipeline.fast_doc_processor import FastDocProcessor
            cls._processors[processor_name] = FastDocProcessor
        elif processor_name == 'simple_fast_processor' and cls._processors[processor_name] is None:
            from pipeline.simple_fast_processor import SimpleFastProcessor
            cls._processors[processor_name] = SimpleFastProcessor
        elif processor_name == 'optimized_doc_processor' and cls._processors[processor_name] is None:
            from pipeline.optimized_doc_processor import OptimizedDocProcessorWrapper
            cls._processors[processor_name] = OptimizedDocProcessorWrapper
        
        processor_class = cls._processors[processor_name]
        return processor_class(config)
    
    @classmethod
    def register(cls, name: str, processor_class: type):
        """Register a new processor type."""
        if not issubclass(processor_class, AbstractProcessor):
            raise ValueError("Processor must inherit from AbstractProcessor")
        cls._processors[name] = processor_class
    
    @classmethod
    def get_available_processors(cls) -> List[str]:
        """Get list of available processor names."""
        return list(cls._processors.keys())