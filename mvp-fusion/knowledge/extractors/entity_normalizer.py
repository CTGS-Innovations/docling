#!/usr/bin/env python3
"""
Entity Normalization Engine for MVP-Fusion
==========================================
Normalizes extracted entities into structured, analysis-ready formats.

Supported Entity Types:
- MONEY: Currency detection, amount parsing, standard formatting
- PHONE: Country codes, area codes, formatting, type detection
- MEASUREMENT: Unit conversion, metric equivalents, categorization
- REGULATION: Agency parsing, structural breakdown
- DATE: ISO formatting, component extraction
- TIME: 12/24 hour conversion, minute calculations
- EMAIL: Domain extraction, validation
- TEMPERATURE: Unit conversion (F/C/K)
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """
    Centralized entity normalization engine.
    Provides structured data while preserving original text.
    """
    
    def __init__(self):
        # Currency symbols to codes
        self.currency_map = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            '₹': 'INR', '₽': 'RUB', '¢': 'USD', 'USD': 'USD'
        }
        
        # Amount multipliers
        self.amount_multipliers = {
            'thousand': 1000, 'k': 1000, 'K': 1000,
            'million': 1000000, 'm': 1000000, 'M': 1000000,
            'billion': 1000000000, 'b': 1000000000, 'B': 1000000000,
            'trillion': 1000000000000, 't': 1000000000000, 'T': 1000000000000
        }
        
        # Unit conversions (to metric)
        self.length_conversions = {
            'feet': 0.3048, 'foot': 0.3048, 'ft': 0.3048,
            'inches': 0.0254, 'inch': 0.0254, 'in': 0.0254,
            'meters': 1.0, 'meter': 1.0, 'm': 1.0,
            'cm': 0.01, 'centimeters': 0.01,
            'mm': 0.001, 'millimeters': 0.001,
            'yards': 0.9144, 'yard': 0.9144, 'yd': 0.9144
        }
        
        self.weight_conversions = {
            'pounds': 0.453592, 'pound': 0.453592, 'lbs': 0.453592, 'lb': 0.453592,
            'kg': 1.0, 'kilograms': 1.0, 'kilogram': 1.0,
            'grams': 0.001, 'gram': 0.001, 'g': 0.001,
            'ounces': 0.0283495, 'ounce': 0.0283495, 'oz': 0.0283495
        }
        
        # Regulation agencies
        self.regulation_agencies = {
            '29 CFR': 'OSHA', '40 CFR': 'EPA', '49 CFR': 'DOT',
            '21 CFR': 'FDA', 'ISO': 'ISO', 'ANSI': 'ANSI', 'NFPA': 'NFPA'
        }
    
    def normalize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single entity based on its type.
        
        Args:
            entity: Original entity with 'type', 'value', 'text' fields
            
        Returns:
            Enhanced entity with 'normalized' field added
        """
        entity_type = entity.get('type', '').upper()
        normalized = {}
        
        try:
            if entity_type == 'MONEY':
                normalized = self._normalize_money(entity['value'])
            elif entity_type == 'PHONE':
                normalized = self._normalize_phone(entity['value'])
            elif entity_type == 'MEASUREMENT':
                normalized = self._normalize_measurement(entity['value'])
            elif entity_type == 'REGULATION':
                normalized = self._normalize_regulation(entity['value'])
            elif entity_type == 'DATE':
                normalized = self._normalize_date(entity['value'])
            elif entity_type == 'TIME':
                normalized = self._normalize_time(entity['value'])
            elif entity_type == 'EMAIL':
                normalized = self._normalize_email(entity['value'])
            elif entity_type == 'PERCENT':
                normalized = self._normalize_percent(entity['value'])
        except Exception as e:
            logger.debug(f"Normalization failed for {entity_type} '{entity['value']}': {e}")
            normalized = {'error': str(e)}
        
        # Add normalized data to entity (preserve original)
        if normalized:
            entity['normalized'] = normalized
        
        return entity
    
    def _normalize_money(self, value: str) -> Dict[str, Any]:
        """Normalize money amounts with currency detection and parsing."""
        # Extract currency symbol
        currency = 'USD'  # default
        for symbol, code in self.currency_map.items():
            if symbol in value:
                currency = code
                break
        
        # Extract numeric amount
        amount_text = re.sub(r'[^\d.,kmbtKMBT\s]', '', value).strip()
        
        # Parse amount with multipliers
        amount = 0
        try:
            # Handle formats like "2.5 million", "100k", etc.
            parts = amount_text.lower().split()
            base_amount = float(parts[0].replace(',', ''))
            
            multiplier = 1
            if len(parts) > 1:
                multiplier_text = parts[1]
                multiplier = self.amount_multipliers.get(multiplier_text, 1)
            elif parts[0][-1].lower() in 'kmbt':
                multiplier_char = parts[0][-1].lower()
                base_amount = float(parts[0][:-1].replace(',', ''))
                multiplier = self.amount_multipliers.get(multiplier_char, 1)
            
            amount = base_amount * multiplier
        except (ValueError, IndexError):
            # Fallback to simple numeric extraction
            numbers = re.findall(r'[\d,]+\.?\d*', value)
            if numbers:
                amount = float(numbers[0].replace(',', ''))
        
        return {
            'amount': amount,
            'currency': currency,
            'formatted': f"{currency_symbol}{amount:,.0f}" if amount >= 1 else f"{currency_symbol}{amount:.2f}",
            'raw_amount': amount_text
        } if (currency_symbol := next((k for k, v in self.currency_map.items() if v == currency), '$')) else {}
    
    def _normalize_phone(self, value: str) -> Dict[str, Any]:
        """Normalize phone numbers with formatting and type detection."""
        # Extract digits only
        digits = re.sub(r'[^\d]', '', value)
        
        # Determine format and parse components
        country_code = None
        area_code = None
        number = None
        phone_type = 'unknown'
        
        if len(digits) == 10:
            # US/Canada format without country code
            country_code = '1'
            area_code = digits[:3]
            number = digits[3:]
        elif len(digits) == 11 and digits[0] == '1':
            # US/Canada format with country code
            country_code = '1'
            area_code = digits[1:4]
            number = digits[4:]
        elif len(digits) >= 10:
            # International format (assume first 1-3 digits are country code)
            if digits.startswith('1'):
                country_code = '1'
                area_code = digits[1:4]
                number = digits[4:]
            else:
                country_code = digits[:2] if len(digits) > 10 else digits[:1]
                remaining = digits[len(country_code):]
                area_code = remaining[:3] if len(remaining) >= 6 else None
                number = remaining[3:] if area_code else remaining
        
        # Detect phone type
        if area_code:
            if area_code.startswith('8'):
                phone_type = 'toll_free'
            elif area_code in ['800', '888', '877', '866', '855', '844', '833', '822']:
                phone_type = 'toll_free'
            else:
                phone_type = 'standard'
        
        # Format variants
        formatted_us = f"({area_code}) {number[:3]}-{number[3:]}" if area_code and len(number) >= 7 else value
        formatted_international = f"+{country_code}-{area_code}-{number}" if all([country_code, area_code, number]) else value
        
        return {
            'country_code': country_code,
            'area_code': area_code,
            'number': number,
            'type': phone_type,
            'formatted_us': formatted_us,
            'formatted_international': formatted_international,
            'digits_only': digits
        }
    
    def _normalize_measurement(self, value: str) -> Dict[str, Any]:
        """Normalize measurements with unit conversion and categorization."""
        # Extract numeric value and unit
        match = re.match(r'([\d.,]+)\s*([a-zA-Z°]+)', value.strip())
        if not match:
            return {'error': 'Could not parse measurement'}
        
        numeric_part = float(match.group(1).replace(',', ''))
        unit = match.group(2).lower()
        
        # Determine category and convert to metric
        category = 'unknown'
        metric_value = numeric_part
        metric_unit = unit
        
        if unit in self.length_conversions:
            category = 'length'
            metric_value = numeric_part * self.length_conversions[unit]
            metric_unit = 'meters'
        elif unit in self.weight_conversions:
            category = 'weight'
            metric_value = numeric_part * self.weight_conversions[unit]
            metric_unit = 'kg'
        elif unit in ['°f', 'fahrenheit']:
            category = 'temperature'
            metric_value = (numeric_part - 32) * 5/9
            metric_unit = '°c'
        elif unit in ['°c', 'celsius']:
            category = 'temperature'
            metric_value = numeric_part
            metric_unit = '°c'
        elif unit in ['decibels', 'db']:
            category = 'sound'
            metric_value = numeric_part
            metric_unit = 'db'
        
        return {
            'value': numeric_part,
            'unit': match.group(2),
            'category': category,
            'metric_value': round(metric_value, 3),
            'metric_unit': metric_unit,
            'formatted_metric': f"{metric_value:.1f} {metric_unit}" if category != 'unknown' else value
        }
    
    def _normalize_regulation(self, value: str) -> Dict[str, Any]:
        """Normalize regulation references with agency and structural parsing."""
        # Common regulation patterns
        cfr_match = re.match(r'(\d+)\s+CFR\s+(\d+)\.?(\d+)?', value, re.IGNORECASE)
        iso_match = re.match(r'ISO\s+(\d+):?(\d+)?', value, re.IGNORECASE)
        ansi_match = re.match(r'ANSI\s+([\w.-]+)', value, re.IGNORECASE)
        
        if cfr_match:
            title = cfr_match.group(1)
            part = cfr_match.group(2)
            section = cfr_match.group(3)
            agency_key = f"{title} CFR"
            agency = self.regulation_agencies.get(agency_key, 'Federal')
            
            return {
                'type': 'CFR',
                'agency': agency,
                'title': title,
                'part': part,
                'section': section,
                'formatted': f"{title} CFR {part}" + (f".{section}" if section else "")
            }
        elif iso_match:
            standard = iso_match.group(1)
            year = iso_match.group(2)
            return {
                'type': 'ISO',
                'agency': 'ISO',
                'standard': standard,
                'year': year,
                'formatted': f"ISO {standard}" + (f":{year}" if year else "")
            }
        elif ansi_match:
            standard = ansi_match.group(1)
            return {
                'type': 'ANSI',
                'agency': 'ANSI',
                'standard': standard,
                'formatted': f"ANSI {standard}"
            }
        
        return {'type': 'unknown', 'formatted': value}
    
    def _normalize_date(self, value: str) -> Dict[str, Any]:
        """Normalize dates to ISO format with component extraction."""
        try:
            # Try to parse various date formats
            for fmt in ['%B %d, %Y', '%b %d, %Y', '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    return {
                        'iso': dt.strftime('%Y-%m-%d'),
                        'year': dt.year,
                        'month': dt.month,
                        'day': dt.day,
                        'formatted': dt.strftime('%B %d, %Y'),
                        'day_of_week': dt.strftime('%A')
                    }
                except ValueError:
                    continue
        except Exception:
            pass
        
        return {'error': 'Could not parse date', 'original': value}
    
    def _normalize_time(self, value: str) -> Dict[str, Any]:
        """Normalize times to 24-hour format with calculations."""
        try:
            # Parse 12-hour format
            time_match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', value.strip(), re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                period = time_match.group(3)
                
                # Convert to 24-hour
                hour_24 = hour
                if period:
                    if period.upper() == 'PM' and hour != 12:
                        hour_24 += 12
                    elif period.upper() == 'AM' and hour == 12:
                        hour_24 = 0
                
                # Calculate minutes since midnight
                minutes_since_midnight = hour_24 * 60 + minute
                
                return {
                    'hour_12': f"{hour}:{minute:02d} {period}" if period else f"{hour}:{minute:02d}",
                    'hour_24': f"{hour_24:02d}:{minute:02d}",
                    'hour': hour_24,
                    'minute': minute,
                    'minutes_since_midnight': minutes_since_midnight
                }
        except Exception:
            pass
        
        return {'error': 'Could not parse time', 'original': value}
    
    def _normalize_email(self, value: str) -> Dict[str, Any]:
        """Normalize email addresses with domain extraction."""
        email_pattern = r'^([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'
        match = re.match(email_pattern, value.strip())
        
        if match:
            username = match.group(1)
            domain = match.group(2)
            domain_parts = domain.split('.')
            tld = domain_parts[-1] if domain_parts else ''
            
            return {
                'username': username,
                'domain': domain,
                'tld': tld.upper(),
                'is_valid': True,
                'formatted': value.lower()
            }
        
        return {'is_valid': False, 'error': 'Invalid email format'}
    
    def _normalize_percent(self, value: str) -> Dict[str, Any]:
        """Normalize percentage values."""
        try:
            # Extract numeric value
            numeric = float(re.sub(r'[^\d.]', '', value))
            return {
                'value': numeric,
                'decimal': numeric / 100,
                'formatted': f"{numeric}%",
                'category': 'percentage'
            }
        except ValueError:
            return {'error': 'Could not parse percentage'}


# Convenience function for single entity normalization
def normalize_entity(entity: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single entity."""
    normalizer = EntityNormalizer()
    return normalizer.normalize_entity(entity)


# Convenience function for bulk normalization
def normalize_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of entities."""
    normalizer = EntityNormalizer()
    return [normalizer.normalize_entity(entity) for entity in entities]