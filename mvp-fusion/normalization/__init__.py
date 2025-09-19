#!/usr/bin/env python3
"""
MVP-Fusion Normalization Module
==============================

Centralized normalization strategy for all NER entities following industry standards.

Design Pattern: Efficiency and Easy Maintenance
- Single source of truth for normalization rules
- Reusable patterns across all entity types  
- FLPC-optimized for high performance (2000+ pages/sec)
- Industry-standard schemas and canonical units

Components:
- canonical_units.yaml: Industry-standard unit conversion map
- measurement_normalizer.py: Measurement normalization engine
- entity_normalizers/: Future entity-specific normalizers

Usage:
    from normalization import MeasurementNormalizer
    
    normalizer = MeasurementNormalizer()
    measurements = normalizer.extract_measurements(text)
"""

from .measurement_normalizer import MeasurementNormalizer, normalize_measurement_text

__all__ = [
    'MeasurementNormalizer',
    'normalize_measurement_text'
]

__version__ = '1.0.0'
__author__ = 'MVP-Fusion Team'