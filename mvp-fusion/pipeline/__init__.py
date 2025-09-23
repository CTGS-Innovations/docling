"""
MVP-Fusion Pipeline Framework
============================

Clean pipeline architecture with configurable phases and processors.

The clean pipeline design separates concerns:
- Pipeline phases (PDF conversion, document processing, classification, etc.)
- Processor implementations (ServiceProcessor, FusionPipeline, etc.)
- Legacy processors (wrapped existing implementations)

Usage:
    from pipeline import CleanFusionPipeline
    
    pipeline = CleanFusionPipeline(config)
    results, metadata = pipeline.process(files, metadata)
"""

# Import clean pipeline architecture from fusion_cli.py
# This maintains single source of truth while providing clean imports
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from fusion_cli import CleanFusionPipeline, PipelinePhase
    
    __all__ = ['CleanFusionPipeline', 'PipelinePhase']
    
except ImportError as e:
    print(f"  Pipeline framework import failed: {e}")
    __all__ = []

# Version info
__version__ = "1.0.0"
__author__ = "MVP-Fusion Team"