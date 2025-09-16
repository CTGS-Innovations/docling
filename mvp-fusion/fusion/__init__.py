"""
MVP-Fusion Engine Module
========================

High-performance text processing engines optimized for speed:
- Aho-Corasick automaton for keyword matching (50M+ chars/sec)
- FLPC Rust regex engine for complex patterns (69M chars/sec)
- Smart pattern routing and vectorized operations
"""

from .fusion_engine import FusionEngine
from .ac_automaton import AhoCorasickEngine
from .flpc_engine import FLPCEngine
from .pattern_router import PatternRouter
from .batch_processor import BatchProcessor

__all__ = [
    "FusionEngine",
    "AhoCorasickEngine", 
    "FLPCEngine",
    "PatternRouter",
    "BatchProcessor"
]