"""
MVP-Fusion: High-Performance Document Processing Pipeline
========================================================

A ground-up rewrite of document processing optimized for extreme performance.
Targets 20-250x performance improvements through fusion of:

- Aho-Corasick automaton for keyword matching (50M+ chars/sec)
- FLPC Rust regex engine for complex patterns (69M chars/sec) 
- Zero-copy memory operations
- Vectorized parallel processing
- Smart pattern routing

Performance Targets:
- Conservative: 4,000+ pages/sec (20x improvement)
- Aggressive: 10,000+ pages/sec (50x improvement)
- Extreme: 50,000+ pages/sec (250x improvement)
"""

__version__ = "1.0.0"
__author__ = "MVP-Fusion Team"
__description__ = "High-Performance Document Processing Pipeline"

# Core imports
from .fusion import FusionEngine
from .pipeline import FusionPipeline
from .performance import FusionMetrics

__all__ = [
    "FusionEngine",
    "FusionPipeline", 
    "FusionMetrics"
]