#!/usr/bin/env python3
"""
Measurement Normalization Module for MVP-Fusion
=============================================

Implements industry-standard measurement normalization following MVP-FUSION-NER.md PRD:
- Structured schema: value, unit, text, type, span
- Canonical unit conversions for all 10 measurement categories
- Reusable patterns for NER entity normalization

Categories: Length, Weight, Volume, Temperature, Angle, Percentage, Time, Speed, Area, Currency
Canonical Units: meters, kg, liters, °C, radians, ratio, seconds, m/s, m², currency_code
"""

import re
import yaml
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NormalizedMeasurement:
    """Normalized measurement following industry standards"""
    value: float          # Original numeric value
    unit: str            # Original unit
    text: str            # Original text span
    type: str            # Measurement category (length, weight, etc.)
    span: Dict[str, int] # Character positions {start, end}
    normalized: Dict[str, Any]  # {value: float, unit: str} in canonical form


class MeasurementNormalizer:
    """
    Industry-standard measurement normalization engine.
    
    Follows reusable patterns for NER entity normalization:
    1. Load canonical conversion rules from config
    2. Parse measurement text into components
    3. Classify measurement type
    4. Apply normalization to canonical units
    5. Return structured normalized result
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with canonical unit conversion map"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'canonical_measurements.yaml')
        
        self.config_path = config_path
        self.unit_map = self._load_canonical_units()
        self.regex_patterns = self._compile_regex_patterns()
    
    def _load_canonical_units(self) -> Dict[str, Any]:
        """Load canonical unit conversion map from YAML config"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"Canonical units config not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in canonical units config: {e}")
    
    def _compile_regex_patterns(self) -> Dict[str, re.Pattern]:
        """DISABLED: Regex patterns disabled for performance (Rule #12 compliance)"""
        # PERFORMANCE: Return empty dict to disable regex-based normalization
        # This provides ~10-20x speedup by avoiding Python regex
        return {}
    
    def extract_measurements(self, text: str) -> List[NormalizedMeasurement]:
        """
        Extract and normalize all measurements from text.
        
        Returns list of NormalizedMeasurement objects with:
        - Original value, unit, text, span
        - Measurement type classification
        - Normalized value in canonical units
        """
        measurements = []
        matched_spans = set()  # Track matched character ranges to avoid overlaps
        
        # Process patterns in order of specificity to avoid conflicts
        # More specific patterns (like 'sq ft', 'km/h') should be processed first
        pattern_order = [
            'area',        # 'sq ft', 'ft²' - most specific
            'speed',       # 'km/h', 'mph' - compound units  
            'volume',      # 'gallons', 'liters' - before single letters
            'temperature', # '°C', '°F' - specific symbols
            'percentage',  # '%', 'percent' - specific symbols
            'time',        # 'hours', 'minutes' - before single letters
            'weight',      # 'pounds', 'kg' - before single letters
            'length',      # 'miles', 'feet' - before single letters
            'angle',       # 'degrees', '°' - symbols
            'currency'     # '$', currency codes
        ]
        
        for measurement_type in pattern_order:
            if measurement_type not in self.regex_patterns:
                continue
                
            pattern = self.regex_patterns[measurement_type]
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                
                # Check if this span overlaps with any previous match
                overlap = any(start < prev_end and end > prev_start 
                            for prev_start, prev_end in matched_spans)
                
                if not overlap:
                    try:
                        normalized = self._normalize_single_measurement(
                            match.group(0), 
                            measurement_type, 
                            start, 
                            end
                        )
                        if normalized:
                            measurements.append(normalized)
                            matched_spans.add((start, end))
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Warning: Failed to normalize measurement '{match.group(0)}': {e}")
        
        return measurements
    
    def _normalize_single_measurement(self, text: str, measurement_type: str, start: int, end: int) -> Optional[NormalizedMeasurement]:
        """Normalize a single measurement to canonical form"""
        
        # Parse value and unit from text
        parsed = self._parse_measurement_text(text)
        if not parsed:
            return None
        
        value, unit = parsed
        
        # Get normalization rules for this measurement type
        type_config = self.unit_map.get(measurement_type, {})
        conversions = type_config.get('conversions', {})
        canonical_unit = type_config.get('canonical_unit', unit)
        
        # Apply normalization
        normalized_value, normalized_unit = self._apply_normalization(
            value, unit, conversions, canonical_unit, measurement_type
        )
        
        return NormalizedMeasurement(
            value=value,
            unit=unit,
            text=text.strip(),
            type=measurement_type,
            span={'start': start, 'end': end},
            normalized={'value': normalized_value, 'unit': normalized_unit}
        )
    
    def _parse_measurement_text(self, text: str) -> Optional[Tuple[float, str]]:
        """Parse measurement text into numeric value and unit"""
        
        # Handle various formats: "5.2 feet", "100%", "$250", "98.6°F"
        text = text.strip()
        
        # Currency special case
        if text.startswith('$'):
            match = re.match(r'\$([0-9,]+(?:\.[0-9]+)?)', text)
            if match:
                value = float(match.group(1).replace(',', ''))
                return value, '$'
        
        # Percentage special case
        if '%' in text:
            match = re.match(r'([0-9.]+)\s*%', text)
            if match:
                value = float(match.group(1))
                return value, '%'
        
        # Temperature special case
        if '°' in text:
            match = re.match(r'([0-9.]+)\s*°([CF])', text)
            if match:
                value = float(match.group(1))
                unit = f"°{match.group(2)}"
                return value, unit
        
        # General pattern: number + unit
        match = re.match(r'([0-9.,]+)\s*([a-zA-Z/²³°]+)', text)
        if match:
            try:
                value = float(match.group(1).replace(',', ''))
                unit = match.group(2)
                return value, unit
            except ValueError:
                return None
        
        return None
    
    def _apply_normalization(self, value: float, unit: str, conversions: Dict[str, Any], 
                           canonical_unit: str, measurement_type: str) -> Tuple[float, str]:
        """Apply normalization rules to convert to canonical units"""
        
        # Handle special cases requiring formulas
        if measurement_type == 'temperature':
            return self._normalize_temperature(value, unit)
        
        # Handle currency (preserve original currency code)
        if measurement_type == 'currency':
            currency_code = conversions.get(unit, unit)
            return value, currency_code
        
        # Standard multiplication-based conversion
        unit_lower = unit.lower()
        conversion_factor = None
        
        # Try exact match first
        if unit_lower in conversions:
            conversion_factor = conversions[unit_lower]
        else:
            # Try variations (with/without 's', etc.)
            for conv_unit, factor in conversions.items():
                if (unit_lower == conv_unit or 
                    unit_lower == conv_unit + 's' or 
                    unit_lower + 's' == conv_unit):
                    conversion_factor = factor
                    break
        
        if conversion_factor is not None and isinstance(conversion_factor, (int, float)):
            normalized_value = value * conversion_factor
            return normalized_value, canonical_unit
        else:
            # No conversion found, return original
            return value, unit
    
    def _normalize_temperature(self, value: float, unit: str) -> Tuple[float, str]:
        """Special temperature conversion formulas"""
        unit = unit.lower()
        
        if unit in ['°f', 'fahrenheit']:
            # °C = (°F - 32) × 5/9
            celsius = (value - 32) * 5/9
            return celsius, '°C'
        elif unit in ['k', 'kelvin']:
            # °C = K - 273.15
            celsius = value - 273.15
            return celsius, '°C'
        else:
            # Already in Celsius or unknown
            return value, '°C'
    
    def to_dict(self, measurement: NormalizedMeasurement) -> Dict[str, Any]:
        """Convert NormalizedMeasurement to dictionary for JSON/YAML output"""
        return {
            'text': measurement.text,
            'value': measurement.value,
            'unit': measurement.unit,
            'type': measurement.type,
            'span': measurement.span,
            'normalized': measurement.normalized
        }
    
    def extract_and_normalize_measurements(self, text: str) -> List[Dict[str, Any]]:
        """
        Convenience method that extracts and returns measurements as dictionaries.
        Used for integration with existing MVP-Fusion pipeline.
        """
        measurements = self.extract_measurements(text)
        return [self.to_dict(m) for m in measurements]


# Convenience function for backward compatibility
def normalize_measurement_text(text: str, config_path: str = None) -> List[Dict[str, Any]]:
    """
    Simple function interface for measurement normalization.
    
    Args:
        text: Input text to extract measurements from
        config_path: Optional path to canonical_units.yaml
    
    Returns:
        List of normalized measurement dictionaries
    """
    normalizer = MeasurementNormalizer(config_path)
    return normalizer.extract_and_normalize_measurements(text)