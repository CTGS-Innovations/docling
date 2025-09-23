"""
Legacy Pipeline Processors
==========================

This module contains the existing processor implementations that are wrapped
by the clean pipeline architecture.

- ServiceProcessor - I/O + CPU worker architecture  
- FusionPipeline - In-memory pipeline with spaCy integration

These processors are maintained for backward compatibility and gradual migration
to the new clean pipeline architecture.
"""

__version__ = "1.0.0"