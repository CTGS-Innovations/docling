#!/usr/bin/env python3
"""
Entity Normalization Engine for MVP-Fusion Normalization Phase
==============================================================

Implements entity canonicalization and global text replacement for all 8 core entity types:
PERSON, ORGANIZATION, LOCATION, GPE, DATE, TIME, MONEY, MEASUREMENT

Core Functions:
1. Entity Canonicalization: Transform duplicates into canonical forms with unique IDs
2. Global Text Replacement: Aho-Corasick pattern replacement with ||canonical||id|| format
3. Unified Fact Set: Generate clean, AI-ready entity representations

Legacy Functions (preserved for compatibility):
- Individual entity normalization for MONEY, PHONE, MEASUREMENT, etc.

Performance Target: <50ms per document with linear O(n) complexity
Memory Target: CloudFlare Workers compatible (1GB limit)
"""

import re
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import logging

# Fast hashing for entity grouping (LSH approach)
try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

# Fuzzy matching fallback (if needed)
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Date parsing for normalization
try:
    from dateutil import parser as dateutil_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

# Aho-Corasick for global text replacement
try:
    import ahocorasick
    HAS_AHOCORASICK = True
except ImportError:
    HAS_AHOCORASICK = False

logger = logging.getLogger(__name__)


@dataclass
class NormalizedEntity:
    """Represents a canonical entity with all mentions and metadata."""
    id: str
    type: str
    normalized: str
    aliases: List[str]
    count: int
    mentions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None


@dataclass
class NormalizationResult:
    """Result of entity normalization process."""
    normalized_entities: List[NormalizedEntity]
    normalized_text: str
    statistics: Dict[str, Any]
    processing_time_ms: float


class EntityNormalizer:
    """
    Enhanced entity normalization engine for MVP-Fusion pipeline.
    
    Supports both:
    1. NEW: Entity canonicalization with global text replacement (normalization phase)
    2. LEGACY: Individual entity normalization (existing functionality)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # NEW: Configuration for normalization phase
        self.config = config or {}
        self.normalization_config = self.config.get('normalization', {})
        
        # Performance settings for canonicalization
        self.fuzzy_threshold = self.normalization_config.get('fuzzy_matching_threshold', 0.85)
        self.canonical_preference = self.normalization_config.get('canonical_preference', 'longest')
        
        # Hash-based grouping settings (LSH approach)
        self.use_hash_grouping = self.normalization_config.get('use_hash_grouping', True)
        self.ngram_size = self.normalization_config.get('ngram_size', 3)
        self.hash_similarity_threshold = self.normalization_config.get('hash_similarity_threshold', 0.4)
        
        # Entity counters for unique ID generation
        self.entity_counters = {
            'PERSON': 0, 'ORG': 0, 'LOCATION': 0, 'GPE': 0,
            'DATE': 0, 'TIME': 0, 'MONEY': 0, 'MEASUREMENT': 0,
            'PHONE': 0, 'REGULATION': 0
        }
        
        # Initialize patterns for canonicalization
        self._init_canonicalization_patterns()
        
        # LEGACY: Existing currency symbols to codes
        self.currency_map = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            '₹': 'INR', '₽': 'RUB', '¢': 'USD', 'USD': 'USD'
        }
        
        # LEGACY: Amount multipliers
        self.amount_multipliers = {
            'thousand': 1000, 'k': 1000, 'K': 1000,
            'million': 1000000, 'm': 1000000, 'M': 1000000,
            'billion': 1000000000, 'b': 1000000000, 'B': 1000000000,
            'trillion': 1000000000000, 't': 1000000000000, 'T': 1000000000000
        }
        
        # LEGACY: Unit conversions (to metric)
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
        
        # LEGACY: Regulation agencies
        self.regulation_agencies = {
            '29 CFR': 'OSHA', '40 CFR': 'EPA', '49 CFR': 'DOT',
            '21 CFR': 'FDA', 'ISO': 'ISO', 'ANSI': 'ANSI', 'NFPA': 'NFPA'
        }
    
    def _init_canonicalization_patterns(self):
        """Initialize regex patterns for entity canonicalization."""
        
        # Person name patterns
        self.person_title_pattern = re.compile(r'^(Dr|Prof|Mr|Mrs|Ms|Miss|Sir|Lady|Hon)\.\s*', re.IGNORECASE)
        self.person_suffix_pattern = re.compile(r'\s+(Jr|Sr|III?|IV|V|PhD|MD|Esq)\s*$', re.IGNORECASE)
        
        # Organization patterns
        self.org_legal_suffixes = re.compile(r'\s+(Inc|Corp|LLC|Ltd|LP|LLP|Co|Company|Corporation|Incorporated)\s*$', re.IGNORECASE)
        self.org_acronym_pattern = re.compile(r'^[A-Z]{2,6}$')
        
        # Money patterns
        self.money_pattern = re.compile(r'(\$|USD|EUR|GBP|CAD|AUD)?\s*([0-9,.]+)\s*(million|billion|trillion|k|M|B|T)?\s*(dollars?|USD|EUR|GBP|CAD|AUD)?', re.IGNORECASE)
        self.money_words = {
            'thousand': 1000, 'k': 1000, 'million': 1000000, 'm': 1000000,
            'billion': 1000000000, 'b': 1000000000, 'trillion': 1000000000000, 't': 1000000000000
        }
        
        # Measurement patterns
        self.measurement_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(ft|feet|foot|in|inch|inches|cm|centimeters?|m|meters?|km|kilometers?|miles?|mi|lbs?|pounds?|kg|kilograms?|g|grams?|°F|°C|fahrenheit|celsius|%|percent|percentage)', re.IGNORECASE)
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b'),
            re.compile(r'\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b'),
            re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b', re.IGNORECASE),
            re.compile(r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', re.IGNORECASE)
        ]
        
        # Time patterns
        self.time_pattern = re.compile(r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\b')
    
    # =============================================================================
    # NEW: NORMALIZATION PHASE METHODS (Entity Canonicalization + Global Replacement)
    # =============================================================================
    
    def normalize_entities_phase(self, entities: Dict[str, List[Dict]], document_text: str) -> NormalizationResult:
        """
        NEW: Main normalization phase method for MVP-Fusion pipeline.
        
        Performs entity canonicalization and global text replacement.
        
        Args:
            entities: Raw entities from enrichment stage {type: [entity_list]}
            document_text: Original document text
            
        Returns:
            NormalizationResult with canonical entities and normalized text
        """
        start_time = time.perf_counter()
        
        # Step 1: Canonicalize entities by type
        normalized_entities = []
        replacement_map = {}  # Maps original text -> (canonical, id)
        
        for entity_type, entity_list in entities.items():
            # Normalize entity type to uppercase for consistency
            normalized_type = entity_type.upper()
            if normalized_type in self.entity_counters:
                type_entities = self._canonicalize_entity_type(normalized_type, entity_list)
                normalized_entities.extend(type_entities)
                
                # Build replacement map for this type
                for entity in type_entities:
                    for mention in entity.mentions:
                        original_text = mention['text']
                        replacement_map[original_text] = (entity.normalized, entity.id)
        
        # Step 2: Perform global text replacement using Aho-Corasick
        normalized_text = self._perform_global_replacement(document_text, replacement_map)
        
        # Step 3: Generate statistics
        processing_time = (time.perf_counter() - start_time) * 1000
        stats = self._generate_statistics(entities, normalized_entities, processing_time)
        
        return NormalizationResult(
            normalized_entities=normalized_entities,
            normalized_text=normalized_text,
            statistics=stats,
            processing_time_ms=processing_time
        )
    
    def _canonicalize_entity_type(self, entity_type: str, entity_list: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize entities of a specific type."""
        if entity_type == 'PERSON':
            return self._canonicalize_persons(entity_list)
        elif entity_type == 'ORG':
            return self._canonicalize_organizations(entity_list)
        elif entity_type == 'LOCATION':
            return self._canonicalize_locations(entity_list)
        elif entity_type == 'GPE':
            return self._canonicalize_gpes(entity_list)
        elif entity_type == 'DATE':
            return self._canonicalize_dates(entity_list)
        elif entity_type == 'TIME':
            return self._canonicalize_times(entity_list)
        elif entity_type == 'MONEY':
            return self._canonicalize_money_entities(entity_list)
        elif entity_type == 'MEASUREMENT':
            return self._canonicalize_measurements(entity_list)
        elif entity_type == 'PHONE':
            return self._canonicalize_phones(entity_list)
        elif entity_type == 'REGULATION':
            return self._canonicalize_regulations(entity_list)
        else:
            return []
    
    def _perform_global_replacement(self, text: str, replacement_map: Dict[str, Tuple[str, str]]) -> str:
        """Perform global text replacement using Aho-Corasick algorithm."""
        if not replacement_map:
            return text
            
        if HAS_AHOCORASICK:
            return self._aho_corasick_replacement(text, replacement_map)
        else:
            return self._regex_replacement(text, replacement_map)
    
    def _aho_corasick_replacement(self, text: str, replacement_map: Dict[str, Tuple[str, str]]) -> str:
        """Use Aho-Corasick for efficient global replacement."""
        # Build automaton
        automaton = ahocorasick.Automaton()
        
        for original_text, (canonical, entity_id) in replacement_map.items():
            automaton.add_word(original_text, (original_text, canonical, entity_id))
        
        automaton.make_automaton()
        
        # Find all matches and sort by position (reverse order for replacement)
        matches = []
        for end_index, (original, canonical, entity_id) in automaton.iter(text):
            start_index = end_index - len(original) + 1
            matches.append((start_index, end_index + 1, original, canonical, entity_id))
        
        # Sort by start position in reverse order
        matches.sort(key=lambda x: x[0], reverse=True)
        
        # Perform replacements from end to beginning
        result = text
        for start, end, original, canonical, entity_id in matches:
            # Verify this is a word boundary match (not part of larger word)
            if self._is_word_boundary_match(result, start, end, original):
                replacement = f"||{canonical}||{entity_id}||"
                result = result[:start] + replacement + result[end:]
        
        return result
    
    def _regex_replacement(self, text: str, replacement_map: Dict[str, Tuple[str, str]]) -> str:
        """Fallback regex-based replacement."""
        result = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_terms = sorted(replacement_map.keys(), key=len, reverse=True)
        
        for original_text in sorted_terms:
            canonical, entity_id = replacement_map[original_text]
            # Use word boundary regex for exact matches
            pattern = r'\b' + re.escape(original_text) + r'\b'
            replacement = f"||{canonical}||{entity_id}||"
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _is_word_boundary_match(self, text: str, start: int, end: int, original: str) -> bool:
        """Check if match is at word boundary."""
        # Check character before
        if start > 0 and text[start - 1].isalnum():
            return False
        
        # Check character after
        if end < len(text) and text[end].isalnum():
            return False
            
        return True
    
    # Canonicalization methods for each entity type will be added next...
    # For now, let me add placeholder methods and then implement them
    
    def _canonicalize_persons(self, persons: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize person entities with fuzzy matching and title removal."""
        if not persons:
            return []
            
        canonical_groups = []
        
        for person in persons:
            text = person.get('text', '').strip()
            if not text:
                continue
                
            # Clean the name (remove titles, normalize whitespace)
            cleaned_name = self._clean_person_name(text)
            
            # Find existing group using hash-based grouping or fuzzy matching
            group_found = False
            group_idx = -1
            
            # Try hash-based grouping first (faster)
            if HAS_XXHASH and self.use_hash_grouping and len(canonical_groups) > 0:
                fingerprint = self._generate_entity_fingerprint(cleaned_name)
                group_idx = self._find_matching_group_by_hash(fingerprint, canonical_groups)
                
                if group_idx >= 0:
                    # Add to existing group
                    canonical_groups[group_idx]['mentions'].append({
                        'text': text,
                        'span': person.get('span', {})
                    })
                    canonical_groups[group_idx]['aliases'].add(text)
                    canonical_groups[group_idx]['count'] += 1
                    group_found = True
            
            # Fallback to fuzzy matching if hash grouping fails
            elif HAS_RAPIDFUZZ and len(canonical_groups) > 0:
                group_names = [group['canonical'] for group in canonical_groups]
                best_match = process.extractOne(cleaned_name, group_names, scorer=fuzz.ratio)
                
                if best_match and best_match[1] >= (self.fuzzy_threshold * 100):
                    # Add to existing group
                    group_idx = group_names.index(best_match[0])
                    canonical_groups[group_idx]['mentions'].append({
                        'text': text,
                        'span': person.get('span', {})
                    })
                    canonical_groups[group_idx]['aliases'].add(text)
                    canonical_groups[group_idx]['count'] += 1
                    group_found = True
            
            if not group_found:
                # Create new group with hash fingerprint
                self.entity_counters['PERSON'] += 1
                fingerprint = self._generate_entity_fingerprint(cleaned_name) if HAS_XXHASH else []
                canonical_groups.append({
                    'canonical': cleaned_name,
                    'aliases': {text},
                    'mentions': [{
                        'text': text,
                        'span': person.get('span', {})
                    }],
                    'count': 1,
                    'id': f"p{self.entity_counters['PERSON']:03d}",
                    'fingerprint': fingerprint
                })
        
        # Convert to NormalizedEntity objects
        result = []
        for group in canonical_groups:
            # Choose best canonical form (longest variant)
            if self.canonical_preference == 'longest':
                canonical = max(group['aliases'], key=len)
            else:
                canonical = group['canonical']
            
            # Create proper aliases list (all variants except the canonical form)
            all_variants = group['aliases'].copy()
            aliases = list(all_variants - {canonical})
                
            result.append(NormalizedEntity(
                id=group['id'],
                type='PERSON',
                normalized=canonical,
                aliases=aliases,
                count=group['count'],
                mentions=group['mentions']
            ))
        
        return result
    
    def _clean_person_name(self, name: str) -> str:
        """Clean person name by removing titles and normalizing."""
        cleaned = name.strip()
        
        # Remove titles (Dr., Mr., etc.)
        cleaned = self.person_title_pattern.sub('', cleaned)
        
        # Remove suffixes (Jr., PhD, etc.)
        cleaned = self.person_suffix_pattern.sub('', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    # =============================================================================
    # HASH-BASED ENTITY GROUPING (LSH Approach)
    # =============================================================================
    
    def _generate_entity_fingerprint(self, text: str) -> List[int]:
        """Generate n-gram hash fingerprint for entity text using xxHash."""
        if not HAS_XXHASH:
            return []
            
        # Normalize text for fingerprinting
        normalized = self._normalize_for_hashing(text)
        
        # Generate n-grams
        ngrams = self._generate_ngrams(normalized, self.ngram_size)
        
        # Hash each n-gram
        fingerprint = []
        for ngram in ngrams:
            hash_val = xxhash.xxh64(ngram.encode('utf-8')).intdigest()
            fingerprint.append(hash_val)
        
        return sorted(fingerprint)  # Sort for consistent comparison
    
    def _normalize_for_hashing(self, text: str) -> str:
        """Normalize text for hash-based comparison."""
        # Convert to lowercase, remove spaces, special chars
        normalized = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
        return normalized
    
    def _generate_ngrams(self, text: str, n: int) -> List[str]:
        """Generate n-grams from text."""
        if len(text) < n:
            return [text]
        return [text[i:i+n] for i in range(len(text) - n + 1)]
    
    def _calculate_fingerprint_similarity(self, fp1: List[int], fp2: List[int]) -> float:
        """Calculate similarity between two fingerprints using Jaccard similarity."""
        if not fp1 or not fp2:
            return 0.0
        
        set1 = set(fp1)
        set2 = set(fp2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _find_matching_group_by_hash(self, fingerprint: List[int], canonical_groups: List[Dict]) -> int:
        """Find matching group using hash-based similarity."""
        if not HAS_XXHASH or not self.use_hash_grouping:
            return -1
            
        for i, group in enumerate(canonical_groups):
            group_fingerprint = group.get('fingerprint', [])
            similarity = self._calculate_fingerprint_similarity(fingerprint, group_fingerprint)
            
            if similarity >= self.hash_similarity_threshold:
                return i
        
        return -1
    
    def _canonicalize_organizations(self, orgs: List[Dict]) -> List[NormalizedEntity]:
        """
        STAGE 4 ENHANCEMENT: Canonicalize organizations with government entity linking.
        
        Applies Named Entity Linking (NEL) for government entities using Aho-Corasick lookup.
        Following NER/NEL standards within our existing normalization pipeline.
        """
        if not orgs:
            return []
        
        # Load government reference data for entity linking
        try:
            from knowledge.corpus.geographic_data import get_reference_data
            reference_data = get_reference_data()
        except Exception:
            reference_data = None
        
        canonical_groups = []
        for org in orgs:
            text = org.get('text', '').strip()
            if not text:
                continue
                
            self.entity_counters['ORG'] += 1
            
            # GOVERNMENT ENTITY LINKING: Apply NEL if government entity detected in Stage 3
            if org.get('is_government_entity') and reference_data:
                # Use formal name as canonical form (Named Entity Linking)
                gov_data = org.get('government_enrichment', {})
                canonical_name = gov_data.get('formal_name', text)
                abbreviation = gov_data.get('abbreviation', '')
                
                # Build aliases list with abbreviation and original text
                aliases = []
                if abbreviation and abbreviation.lower() != canonical_name.lower():
                    aliases.append(abbreviation)
                if text.lower() != canonical_name.lower():
                    aliases.append(text)
                
                canonical_groups.append({
                    'id': f"gov{self.entity_counters['ORG']:03d}",  # Special gov prefix
                    'canonical': canonical_name,
                    'aliases': aliases,
                    'mentions': [{'text': text, 'span': org.get('span', {})}],
                    'count': 1,
                    'entity_type': 'government_entity',
                    'government_enrichment': gov_data,  # Preserve enrichment data
                    'website_url': gov_data.get('website', ''),
                    'mission_statement': gov_data.get('mission', ''),
                    'enrichment_source': 'government_csv_kb'
                })
            else:
                # Standard organization canonicalization
                canonical_groups.append({
                    'id': f"org{self.entity_counters['ORG']:03d}",
                    'canonical': text,
                    'aliases': [],
                    'mentions': [{'text': text, 'span': org.get('span', {})}],
                    'count': 1
                })
        
        return [NormalizedEntity(
            id=group['id'], type=group.get('entity_type', 'ORG'), normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group  # Include all enrichment data in metadata
        ) for group in canonical_groups]
    
    def _canonicalize_locations(self, locations: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize location entities with metadata-enriched normalization."""
        if not locations:
            return []
        
        # Group locations by canonical form using metadata-informed logic
        canonical_groups = {}
        
        for loc in locations:
            text = loc.get('text', '').strip()
            if not text:
                continue
            
            # Extract subcategory metadata for enhanced canonicalization
            metadata = loc.get('metadata', {})
            subcategory = metadata.get('subcategory', '')
            
            # Apply subcategory-specific canonicalization rules
            canonical_form = self._get_canonical_location_form(text, subcategory)
            
            # Create enhanced metadata with normalization context
            enhanced_metadata = {
                'subcategory': subcategory,
                'location_type': self._classify_location_type(subcategory),
                'normalization_confidence': self._calculate_location_confidence(text, subcategory),
                'standardization_applied': canonical_form != text
            }
            
            # Add geographic hierarchy if available
            if subcategory:
                enhanced_metadata['geographic_level'] = self._get_geographic_level(subcategory)
            
            # Group by canonical form (merge variants)
            if canonical_form in canonical_groups:
                # Add to existing group
                canonical_groups[canonical_form]['mentions'].append({
                    'text': text,
                    'span': loc.get('span', {}),
                    'subcategory': subcategory
                })
                canonical_groups[canonical_form]['aliases'].add(text)
                canonical_groups[canonical_form]['count'] += 1
                
                # Update confidence if this variant is more confident
                current_confidence = canonical_groups[canonical_form]['metadata']['normalization_confidence']
                if enhanced_metadata['normalization_confidence'] > current_confidence:
                    canonical_groups[canonical_form]['metadata'] = enhanced_metadata
            else:
                # Create new canonical group
                self.entity_counters['LOCATION'] += 1
                canonical_groups[canonical_form] = {
                    'id': f"loc{self.entity_counters['LOCATION']:03d}",
                    'canonical': canonical_form,
                    'aliases': {text} if text != canonical_form else set(),
                    'mentions': [{'text': text, 'span': loc.get('span', {}), 'subcategory': subcategory}],
                    'count': 1,
                    'metadata': enhanced_metadata
                }
        
        # Convert to NormalizedEntity objects
        result = []
        for group in canonical_groups.values():
            # Convert aliases set to list
            aliases = list(group['aliases'])
            
            result.append(NormalizedEntity(
                id=group['id'],
                type='LOCATION',
                normalized=group['canonical'],
                aliases=aliases,
                count=group['count'],
                mentions=group['mentions'],
                metadata=group['metadata']
            ))
        
        return result
    
    def _canonicalize_gpes(self, gpes: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize geopolitical entities with metadata-enriched normalization."""
        if not gpes:
            return []
        
        # Group GPEs by canonical form using metadata-informed logic
        canonical_groups = {}
        
        for gpe in gpes:
            text = gpe.get('text', '').strip()
            if not text:
                continue
            
            # Extract subcategory metadata for enhanced canonicalization
            metadata = gpe.get('metadata', {})
            subcategory = metadata.get('subcategory', '')
            
            # Apply subcategory-specific canonicalization rules
            canonical_form = self._get_canonical_gpe_form(text, subcategory)
            
            # Create enhanced metadata with normalization context
            enhanced_metadata = {
                'subcategory': subcategory,
                'gpe_type': self._classify_gpe_type(subcategory),
                'political_level': self._get_political_level(subcategory),
                'normalization_confidence': self._calculate_gpe_confidence(text, subcategory),
                'standardization_applied': canonical_form != text
            }
            
            # Add ISO codes and formal names if available for high-confidence entities
            if subcategory in ['countries', 'us_states'] and enhanced_metadata['normalization_confidence'] > 0.8:
                enhanced_metadata.update(self._get_iso_standards(canonical_form, subcategory))
            
            # Group by canonical form (merge variants)
            if canonical_form in canonical_groups:
                # Add to existing group
                canonical_groups[canonical_form]['mentions'].append({
                    'text': text,
                    'span': gpe.get('span', {}),
                    'subcategory': subcategory
                })
                canonical_groups[canonical_form]['aliases'].add(text)
                canonical_groups[canonical_form]['count'] += 1
                
                # Update confidence if this variant is more confident
                current_confidence = canonical_groups[canonical_form]['metadata']['normalization_confidence']
                if enhanced_metadata['normalization_confidence'] > current_confidence:
                    canonical_groups[canonical_form]['metadata'] = enhanced_metadata
            else:
                # Create new canonical group
                self.entity_counters['GPE'] += 1
                canonical_groups[canonical_form] = {
                    'id': f"gpe{self.entity_counters['GPE']:03d}",
                    'canonical': canonical_form,
                    'aliases': {text} if text != canonical_form else set(),
                    'mentions': [{'text': text, 'span': gpe.get('span', {}), 'subcategory': subcategory}],
                    'count': 1,
                    'metadata': enhanced_metadata
                }
        
        # Convert to NormalizedEntity objects
        result = []
        for group in canonical_groups.values():
            # Convert aliases set to list
            aliases = list(group['aliases'])
            
            result.append(NormalizedEntity(
                id=group['id'],
                type='GPE',
                normalized=group['canonical'],
                aliases=aliases,
                count=group['count'],
                mentions=group['mentions'],
                metadata=group['metadata']
            ))
        
        return result
    
    def _canonicalize_dates(self, dates: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize date entities to ISO 8601 format with temporal metadata."""
        if not dates:
            return []
        
        canonical_groups = []
        for date in dates:
            text = date.get('text', '').strip()
            if not text:
                continue
                
            # Parse date to ISO 8601 format
            parsed_date = self._parse_date_to_iso(text)
            
            if parsed_date:
                # Use ISO format as canonical
                canonical = parsed_date['iso_date']
                metadata = parsed_date
            else:
                # Fallback to original text if parsing fails
                canonical = text
                metadata = {'parse_error': True, 'original_text': text}
                
            self.entity_counters['DATE'] += 1
            canonical_groups.append({
                'id': f"d{self.entity_counters['DATE']:03d}",
                'canonical': canonical,
                'aliases': [],
                'mentions': [{'text': text, 'span': date.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='DATE', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _canonicalize_times(self, times: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize time entities to 24-hour format with temporal metadata."""
        if not times:
            return []
        
        canonical_groups = []
        for time_entity in times:
            text = time_entity.get('text', '').strip()
            if not text:
                continue
                
            # Parse time to 24-hour format
            parsed_time = self._parse_time_to_24h(text)
            
            if parsed_time:
                # Use 24-hour format as canonical
                canonical = parsed_time['time_24h']
                metadata = parsed_time
            else:
                # Fallback to original text if parsing fails
                canonical = text
                metadata = {'parse_error': True, 'original_text': text}
                
            self.entity_counters['TIME'] += 1
            canonical_groups.append({
                'id': f"t{self.entity_counters['TIME']:03d}",
                'canonical': canonical,
                'aliases': [],
                'mentions': [{'text': text, 'span': time_entity.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='TIME', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _canonicalize_money_entities(self, money_entities: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize money entities to industry standard: base numeric value with metadata."""
        if not money_entities:
            return []
        
        # Currency symbol to ISO 4217 mapping
        currency_map = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR', '₽': 'RUB',
            'USD': 'USD', 'EUR': 'EUR', 'GBP': 'GBP', 'JPY': 'JPY', 'CAD': 'CAD', 'AUD': 'AUD'
        }
        
        # Magnitude multipliers for parsing
        magnitude_map = {
            'thousand': 1000, 'k': 1000,
            'million': 1000000, 'm': 1000000, 'mil': 1000000,
            'billion': 1000000000, 'b': 1000000000, 'bil': 1000000000,
            'trillion': 1000000000000, 't': 1000000000000
        }
        
        canonical_groups = []
        for money in money_entities:
            text = money.get('text', '').strip()
            if not text:
                continue
            
            # Enhanced money parsing pattern to handle "$2.5 million" format
            import re
            # Pattern: optional currency, amount, optional magnitude, optional currency word
            money_pattern = r'([€£¥₹$]?)\s*([0-9,]+\.?[0-9]*)\s*(thousand|million|billion|trillion|k|m|b|t)?\s*([A-Z]{3}|dollars?|euros?|pounds?)?'
            match = re.search(money_pattern, text, re.IGNORECASE)
            
            if match:
                symbol, amount_str, magnitude, currency_word = match.groups()
                
                # Parse base amount
                try:
                    base_value = float(amount_str.replace(',', ''))
                except ValueError:
                    base_value = 0.0
                
                # Apply magnitude multiplier
                multiplier = 1
                if magnitude:
                    multiplier = magnitude_map.get(magnitude.lower(), 1)
                
                # Calculate actual value (e.g., 2.5 * 1000000 = 2500000)
                actual_value = base_value * multiplier
                
                # Determine currency
                if currency_word and currency_word.upper() in currency_map:
                    currency = currency_word.upper()
                elif symbol:
                    currency = currency_map.get(symbol, 'USD')
                elif currency_word:
                    # Map currency words to codes
                    word_map = {'dollar': 'USD', 'dollars': 'USD', 'euro': 'EUR', 'euros': 'EUR', 
                               'pound': 'GBP', 'pounds': 'GBP'}
                    currency = word_map.get(currency_word.lower(), 'USD')
                else:
                    currency = 'USD'  # Default
                
                # Industry standard: normalized is the actual numeric value
                canonical = str(actual_value)
                
                # Create metadata with all the parsed information
                metadata = {
                    'currency': currency,
                    'original_value': base_value,
                    'magnitude': magnitude or '',
                    'multiplier': multiplier,
                    'formatted': f"{currency} {actual_value:,.2f}"
                }
            else:
                # Fallback: use original text as canonical
                canonical = text
                metadata = {'currency': 'USD', 'parse_error': True}
                
            self.entity_counters['MONEY'] += 1
            canonical_groups.append({
                'id': f"mon{self.entity_counters['MONEY']:03d}",
                'canonical': canonical,
                'aliases': [],
                'mentions': [{'text': text, 'span': money.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='MONEY', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _canonicalize_measurements(self, measurements: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize measurements to industry standard with clear bidirectional metadata."""
        if not measurements:
            return []
        
        # Comprehensive unit conversions to SI/metric base units
        unit_conversions = {
            # Length -> meters
            'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254, '"': 0.0254,
            'ft': 0.3048, 'feet': 0.3048, 'foot': 0.3048, "'": 0.3048,
            'yd': 0.9144, 'yard': 0.9144, 'yards': 0.9144,
            'mi': 1609.34, 'mile': 1609.34, 'miles': 1609.34,
            'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'meter': 1.0, 'meters': 1.0, 'km': 1000.0,
            # Weight -> kilograms
            'lb': 0.453592, 'lbs': 0.453592, 'pound': 0.453592, 'pounds': 0.453592,
            'oz': 0.0283495, 'ounce': 0.0283495, 'ounces': 0.0283495,
            'g': 0.001, 'gram': 0.001, 'grams': 0.001,
            'kg': 1.0, 'kilogram': 1.0, 'kilograms': 1.0,
            'ton': 1000.0, 'tons': 1000.0, 'metric ton': 1000.0,
            # Volume -> liters
            'gal': 3.78541, 'gallon': 3.78541, 'gallons': 3.78541,
            'qt': 0.946353, 'quart': 0.946353, 'quarts': 0.946353,
            'pt': 0.473176, 'pint': 0.473176, 'pints': 0.473176,
            'cup': 0.236588, 'cups': 0.236588,
            'fl oz': 0.0295735, 'fluid ounce': 0.0295735,
            'ml': 0.001, 'milliliter': 0.001, 'milliliters': 0.001,
            'l': 1.0, 'liter': 1.0, 'liters': 1.0,
            # Temperature - special handling needed
            '°f': 'fahrenheit', 'f': 'fahrenheit', 'fahrenheit': 'fahrenheit',
            '°c': 'celsius', 'c': 'celsius', 'celsius': 'celsius',
            'k': 'kelvin', 'kelvin': 'kelvin',
            # Time -> seconds
            'ms': 0.001, 'millisecond': 0.001, 'milliseconds': 0.001,
            's': 1.0, 'sec': 1.0, 'second': 1.0, 'seconds': 1.0,
            'min': 60.0, 'minute': 60.0, 'minutes': 60.0,
            'hr': 3600.0, 'hour': 3600.0, 'hours': 3600.0,
            'day': 86400.0, 'days': 86400.0,
            'week': 604800.0, 'weeks': 604800.0,
            'month': 2592000.0, 'months': 2592000.0,  # Approximate: 30 days
            'year': 31536000.0, 'years': 31536000.0,  # 365 days
        }
        
        # Map units to their measurement types and SI units
        measurement_types = {
            'length': {'si_unit': 'meters', 'units': ['in', 'inch', 'inches', 'ft', 'feet', 'foot', 'yd', 'yard', 'yards', 'mi', 'mile', 'miles', 'mm', 'cm', 'm', 'meter', 'meters', 'km']},
            'weight': {'si_unit': 'kilograms', 'units': ['lb', 'lbs', 'pound', 'pounds', 'oz', 'ounce', 'ounces', 'g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ton', 'tons']},
            'volume': {'si_unit': 'liters', 'units': ['gal', 'gallon', 'gallons', 'qt', 'quart', 'quarts', 'pt', 'pint', 'pints', 'cup', 'cups', 'fl oz', 'fluid ounce', 'ml', 'milliliter', 'milliliters', 'l', 'liter', 'liters']},
            'temperature': {'si_unit': 'celsius', 'units': ['°f', 'f', 'fahrenheit', '°c', 'c', 'celsius', 'k', 'kelvin']},
            'time': {'si_unit': 'seconds', 'units': ['ms', 'millisecond', 'milliseconds', 's', 'sec', 'second', 'seconds', 'min', 'minute', 'minutes', 'hr', 'hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months', 'year', 'years']},
            'percentage': {'si_unit': 'percent', 'units': ['%', 'percent', 'percentage']},
        }
        
        canonical_groups = []
        for measurement in measurements:
            text = measurement.get('text', '').strip()
            if not text:
                continue
            
            # Parse measurement: extract value and unit
            import re
            # Enhanced pattern to handle decimals, percentages, and temperature symbols
            measurement_pattern = r'([0-9,]+\.?[0-9]*)\s*([°]?)\s*([a-zA-Z%\'"]+)'
            match = re.search(measurement_pattern, text)
            
            if match:
                amount_str, degree_symbol, unit_str = match.groups()
                
                # Clean up unit string
                if degree_symbol:
                    unit_str = degree_symbol + unit_str  # Reconstruct °F or °C
                
                # Parse numeric value
                try:
                    original_value = float(amount_str.replace(',', ''))
                except ValueError:
                    original_value = 0.0
                
                # Determine measurement type
                unit_lower = unit_str.lower()
                measurement_type = 'unknown'
                for mtype, minfo in measurement_types.items():
                    if unit_lower in minfo['units']:
                        measurement_type = mtype
                        break
                
                # Special handling for percentages (keep as percentage, not ratio)
                if unit_lower in ['%', 'percent', 'percentage']:
                    si_value = original_value  # Keep as percentage
                    si_unit = 'percent'
                    canonical = str(si_value)
                # Special handling for temperature
                elif measurement_type == 'temperature':
                    if unit_lower in ['°f', 'f', 'fahrenheit']:
                        si_value = (original_value - 32) * 5/9  # Convert to Celsius
                        si_unit = 'celsius'
                    elif unit_lower in ['k', 'kelvin']:
                        si_value = original_value - 273.15  # Convert to Celsius
                        si_unit = 'celsius'
                    else:
                        si_value = original_value
                        si_unit = 'celsius'
                    canonical = str(round(si_value, 2))
                # Standard unit conversion
                elif unit_lower in unit_conversions and isinstance(unit_conversions[unit_lower], (int, float)):
                    conversion_factor = unit_conversions[unit_lower]
                    si_value = original_value * conversion_factor
                    
                    # Determine SI unit based on measurement type
                    si_unit = measurement_types.get(measurement_type, {}).get('si_unit', unit_str)
                    
                    # Round appropriately based on magnitude
                    if si_value >= 1:
                        canonical = str(round(si_value, 4))
                    else:
                        canonical = str(round(si_value, 6))
                else:
                    # No conversion available, keep original
                    si_value = original_value
                    si_unit = unit_str
                    canonical = str(original_value)
                
                # Create comprehensive metadata
                metadata = {
                    'value': original_value,           # Original numeric value
                    'unit': unit_str,                  # Original unit
                    'si_value': si_value,              # Converted SI value
                    'si_unit': si_unit,                # SI unit
                    'measurement_type': measurement_type,  # Category of measurement
                    'display_value': f"{original_value} {unit_str} ({si_value:.2f} {si_unit})" if unit_str != si_unit else f"{original_value} {unit_str}"
                }
            else:
                # Fallback for unparseable measurements
                canonical = text
                metadata = {'parse_error': True, 'original_text': text}
                
            self.entity_counters['MEASUREMENT'] += 1
            canonical_groups.append({
                'id': f"meas{self.entity_counters['MEASUREMENT']:03d}",
                'canonical': canonical,  # The normalized numeric value
                'aliases': [],
                'mentions': [{'text': text, 'span': measurement.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='MEASUREMENT', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _canonicalize_phones(self, phones: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize phone entities to E.164 international format with regional metadata."""
        if not phones:
            return []
        
        canonical_groups = []
        for phone in phones:
            text = phone.get('text', '').strip()
            if not text:
                continue
                
            # Parse phone to E.164 format
            parsed_phone = self._parse_phone_to_e164(text)
            
            if parsed_phone:
                # Use E.164 format as canonical
                canonical = parsed_phone['e164_format']
                metadata = parsed_phone
            else:
                # Fallback to original text if parsing fails
                canonical = text
                metadata = {'parse_error': True, 'original_text': text}
                
            self.entity_counters['PHONE'] = self.entity_counters.get('PHONE', 0) + 1
            canonical_groups.append({
                'id': f"ph{self.entity_counters['PHONE']:03d}",
                'canonical': canonical,
                'aliases': [],
                'mentions': [{'text': text, 'span': phone.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='PHONE', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _canonicalize_regulations(self, regulations: List[Dict]) -> List[NormalizedEntity]:
        """Canonicalize regulation entities with structured regulatory reference."""
        if not regulations:
            return []
        
        canonical_groups = []
        for regulation in regulations:
            text = regulation.get('text', '').strip()
            if not text:
                continue
                
            # Parse regulation to structured format
            parsed_regulation = self._parse_regulation_structure(text)
            
            if parsed_regulation:
                # Use structured format as canonical
                canonical = parsed_regulation['canonical_format']
                metadata = parsed_regulation
            else:
                # Fallback to original text if parsing fails
                canonical = text
                metadata = {'parse_error': True, 'original_text': text}
                
            self.entity_counters['REGULATION'] = self.entity_counters.get('REGULATION', 0) + 1
            canonical_groups.append({
                'id': f"reg{self.entity_counters['REGULATION']:03d}",
                'canonical': canonical,
                'aliases': [],
                'mentions': [{'text': text, 'span': regulation.get('span', {})}],
                'count': 1,
                'metadata': metadata
            })
        
        return [NormalizedEntity(
            id=group['id'], type='REGULATION', normalized=group['canonical'],
            aliases=group['aliases'], count=group['count'], mentions=group['mentions'],
            metadata=group.get('metadata')
        ) for group in canonical_groups]
    
    def _parse_date_to_iso(self, date_text: str) -> Dict[str, Any]:
        """Parse date text to ISO 8601 format with comprehensive metadata, including date ranges."""
        try:
            # First, check if this is a date range (e.g., "August 15-20, 2024", "October 10-12, 2024")
            range_match = re.match(r'(\w+)\s+(\d{1,2})-(\d{1,2}),?\s+(\d{4})', date_text.strip())
            if range_match:
                month_name, start_day, end_day, year = range_match.groups()
                
                # Parse the start date properly
                start_date_str = f"{month_name} {start_day}, {year}"
                try:
                    start_dt = datetime.strptime(start_date_str, '%B %d, %Y')
                    end_date_str = f"{month_name} {end_day}, {year}"
                    end_dt = datetime.strptime(end_date_str, '%B %d, %Y')
                    
                    # Return range information with the full range preserved
                    today = datetime.now()
                    relative_ref = 'future' if start_dt.date() > today.date() else ('past' if end_dt.date() < today.date() else 'present')
                    
                    return {
                        'iso_date': f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}",  # Preserve the full range
                        'start_date': start_dt.strftime('%Y-%m-%d'),
                        'end_date': end_dt.strftime('%Y-%m-%d'),
                        'date_type': 'range',
                        'duration_days': (end_dt - start_dt).days + 1,
                        'year': int(year),
                        'month': start_dt.month,
                        'month_name': month_name,
                        'start_day': int(start_day),
                        'end_day': int(end_day),
                        'relative_reference': relative_ref,
                        'formatted': date_text,  # Keep original format
                        'quarter': (start_dt.month - 1) // 3 + 1
                    }
                except ValueError:
                    pass  # Fall through to single date parsing
            
            # Original single date parsing logic
            dt = None
            
            # Use dateutil for flexible date parsing if available
            if HAS_DATEUTIL:
                try:
                    dt = dateutil_parser.parse(date_text)
                except Exception:
                    dt = None
            
            # Fallback to manual parsing
            if not dt:
                # Try common formats
                formats = [
                    '%B %d, %Y',    # January 15, 2024
                    '%b %d, %Y',    # Jan 15, 2024
                    '%m/%d/%Y',     # 01/15/2024
                    '%m-%d-%Y',     # 01-15-2024
                    '%Y-%m-%d',     # 2024-01-15
                    '%d/%m/%Y',     # 15/01/2024
                    '%d-%m-%Y',     # 15-01-2024
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_text, fmt)
                        break
                    except ValueError:
                        continue
                        
            if dt:
                # Calculate relative reference (past/present/future)
                today = datetime.now()
                if dt.date() < today.date():
                    relative_ref = 'past'
                elif dt.date() == today.date():
                    relative_ref = 'present'
                else:
                    relative_ref = 'future'
                
                # Calculate quarter
                quarter = f"Q{(dt.month - 1) // 3 + 1}"
                
                # Calculate fiscal year (assuming Oct-Sep fiscal year)
                if dt.month >= 10:
                    fiscal_year = f"FY{dt.year + 1}"
                else:
                    fiscal_year = f"FY{dt.year}"
                
                return {
                    'original_format': date_text,
                    'iso_date': dt.strftime('%Y-%m-%d'),
                    'epoch_timestamp': int(dt.timestamp()),
                    'day_of_week': dt.strftime('%A'),
                    'quarter': quarter,
                    'fiscal_year': fiscal_year,
                    'relative_reference': relative_ref,
                    'year': dt.year,
                    'month': dt.month,
                    'day': dt.day
                }
        except Exception:
            pass
            
        return None
    
    def _parse_time_to_24h(self, time_text: str) -> Dict[str, Any]:
        """Parse time text to 24-hour format with temporal metadata."""
        try:
            # Enhanced time pattern to handle various formats
            import re
            time_pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?'
            match = re.search(time_pattern, time_text)
            
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                second = int(match.group(3) or 0)
                period = match.group(4)
                
                # Convert to 24-hour format
                hour_24 = hour
                if period:
                    period_upper = period.upper()
                    if period_upper == 'PM' and hour != 12:
                        hour_24 += 12
                    elif period_upper == 'AM' and hour == 12:
                        hour_24 = 0
                
                # Calculate minutes from midnight
                minutes_from_midnight = hour_24 * 60 + minute
                
                # Determine if business hours (9 AM - 5 PM)
                business_hours = 9 <= hour_24 < 17
                
                # Detect timezone hint (basic)
                timezone = 'local'  # Could be enhanced to detect timezone from context
                
                return {
                    'original_format': time_text,
                    'time_24h': f"{hour_24:02d}:{minute:02d}:{second:02d}",
                    'time_12h': f"{hour}:{minute:02d}:{second:02d} {period}" if period else f"{hour}:{minute:02d}:{second:02d}",
                    'timezone': timezone,
                    'minutes_from_midnight': minutes_from_midnight,
                    'business_hours': business_hours,
                    'hour': hour_24,
                    'minute': minute,
                    'second': second
                }
        except Exception:
            pass
            
        return None
    
    def _parse_phone_to_e164(self, phone_text: str) -> Dict[str, Any]:
        """Parse phone text to E.164 international format with regional metadata."""
        try:
            # Extract digits only
            import re
            digits = re.sub(r'[^\d]', '', phone_text)
            
            if not digits:
                return None
                
            # Determine format and parse components
            country_code = None
            area_code = None
            local_number = None
            phone_type = 'unknown'
            
            # Handle various length patterns
            if len(digits) == 10:
                # US/Canada format without country code
                country_code = '1'
                area_code = digits[:3]
                local_number = digits[3:]
            elif len(digits) == 11 and digits[0] == '1':
                # US/Canada format with country code
                country_code = '1'
                area_code = digits[1:4]
                local_number = digits[4:]
            elif len(digits) >= 10:
                # International format (basic detection)
                if digits.startswith('1'):
                    country_code = '1'
                    if len(digits) == 11:
                        area_code = digits[1:4]
                        local_number = digits[4:]
                    else:
                        area_code = digits[1:4] if len(digits) > 10 else None
                        local_number = digits[4:] if area_code else digits[1:]
                else:
                    # Assume first 1-3 digits are country code
                    country_code = digits[:2] if len(digits) > 10 else digits[:1]
                    remaining = digits[len(country_code):]
                    area_code = remaining[:3] if len(remaining) >= 6 else None
                    local_number = remaining[3:] if area_code else remaining
            
            # Determine phone type
            if area_code:
                toll_free_codes = ['800', '888', '877', '866', '855', '844', '833', '822']
                if area_code in toll_free_codes:
                    phone_type = 'toll_free'
                elif area_code.startswith('8'):
                    phone_type = 'toll_free'
                else:
                    phone_type = 'landline'  # Could be enhanced to detect mobile vs landline
            
            # Format E.164
            e164_format = f"+{country_code}{area_code or ''}{local_number or ''}"
            
            # Format national
            if country_code == '1' and area_code and local_number and len(local_number) == 7:
                national_format = f"({area_code}) {local_number[:3]}-{local_number[3:]}"
            else:
                national_format = phone_text
            
            # Validate basic format
            is_valid = len(digits) >= 10 and len(digits) <= 15
            
            return {
                'original_format': phone_text,
                'e164_format': e164_format,
                'national_format': national_format,
                'country_code': country_code or 'US',  # Default to US
                'area_code': area_code,
                'local_number': local_number,
                'phone_type': phone_type,
                'is_valid': is_valid,
                'digits_only': digits
            }
        except Exception:
            pass
            
        return None
    
    # =============================================================================
    # METADATA-ENRICHED NORMALIZATION HELPERS FOR GPE AND LOC ENTITIES
    # =============================================================================
    
    def _get_canonical_gpe_form(self, text: str, subcategory: str) -> str:
        """Get canonical form for GPE entity based on subcategory metadata."""
        text_clean = text.strip()
        
        # US States: standardize to full names
        if subcategory == 'us_states':
            state_abbreviations = {
                'CA': 'California', 'NY': 'New York', 'TX': 'Texas', 'FL': 'Florida',
                'IL': 'Illinois', 'PA': 'Pennsylvania', 'OH': 'Ohio', 'GA': 'Georgia',
                'NC': 'North Carolina', 'MI': 'Michigan', 'NJ': 'New Jersey', 'VA': 'Virginia',
                'WA': 'Washington', 'AZ': 'Arizona', 'MA': 'Massachusetts', 'TN': 'Tennessee',
                'IN': 'Indiana', 'MO': 'Missouri', 'MD': 'Maryland', 'WI': 'Wisconsin',
                'CO': 'Colorado', 'MN': 'Minnesota', 'SC': 'South Carolina', 'AL': 'Alabama',
                'LA': 'Louisiana', 'KY': 'Kentucky', 'OR': 'Oregon', 'OK': 'Oklahoma',
                'CT': 'Connecticut', 'IA': 'Iowa', 'MS': 'Mississippi', 'AR': 'Arkansas',
                'UT': 'Utah', 'KS': 'Kansas', 'NV': 'Nevada', 'NM': 'New Mexico',
                'WV': 'West Virginia', 'NE': 'Nebraska', 'ID': 'Idaho', 'HI': 'Hawaii',
                'NH': 'New Hampshire', 'ME': 'Maine', 'MT': 'Montana', 'RI': 'Rhode Island',
                'DE': 'Delaware', 'SD': 'South Dakota', 'ND': 'North Dakota', 'AK': 'Alaska',
                'VT': 'Vermont', 'WY': 'Wyoming'
            }
            return state_abbreviations.get(text_clean.upper(), text_clean)
        
        # Countries: standardize to formal names 
        elif subcategory == 'countries':
            country_standardizations = {
                'US': 'United States', 'USA': 'United States', 'America': 'United States',
                'UK': 'United Kingdom', 'Britain': 'United Kingdom', 'England': 'United Kingdom',
                'UAE': 'United Arab Emirates', 'USSR': 'Soviet Union', 'USSR': 'Russia',
                'PRC': 'China', 'ROC': 'Taiwan'
            }
            return country_standardizations.get(text_clean, text_clean)
        
        # US Cities: keep as-is but could be enhanced with city standardization
        elif subcategory in ['major_cities', 'urban_settlements']:
            return text_clean  # Keep original form for cities
        
        # Default: use original text
        return text_clean
    
    def _get_canonical_location_form(self, text: str, subcategory: str) -> str:
        """Get canonical form for location entity based on subcategory metadata."""
        text_clean = text.strip()
        
        # Physical features: standardize common abbreviations
        if subcategory in ['mountains', 'rivers', 'lakes']:
            # Standardize directional abbreviations
            text_clean = text_clean.replace(' Mt.', ' Mountain')
            text_clean = text_clean.replace(' Mt ', ' Mountain ')
            text_clean = text_clean.replace(' R.', ' River')
            text_clean = text_clean.replace(' L.', ' Lake')
            
        # Buildings and landmarks: keep formal names
        elif subcategory in ['landmarks', 'buildings']:
            return text_clean  # Usually already in formal form
        
        return text_clean
    
    def _classify_gpe_type(self, subcategory: str) -> str:
        """Classify GPE type based on subcategory."""
        if subcategory == 'countries':
            return 'country'
        elif subcategory == 'us_states':
            return 'state' 
        elif subcategory in ['major_cities', 'urban_settlements']:
            return 'city'
        elif subcategory in ['provinces', 'territories']:
            return 'administrative_division'
        else:
            return 'geopolitical_entity'
    
    def _classify_location_type(self, subcategory: str) -> str:
        """Classify location type based on subcategory."""
        if subcategory in ['mountains', 'rivers', 'lakes']:
            return 'natural_feature'
        elif subcategory in ['landmarks', 'buildings']:
            return 'human_made_structure'
        elif subcategory in ['parks', 'forests']:
            return 'protected_area'
        else:
            return 'location'
    
    def _get_political_level(self, subcategory: str) -> str:
        """Get political/administrative level based on subcategory."""
        level_map = {
            'countries': 'national',
            'us_states': 'state',
            'provinces': 'provincial', 
            'territories': 'territorial',
            'major_cities': 'municipal',
            'urban_settlements': 'municipal'
        }
        return level_map.get(subcategory, 'unknown')
    
    def _get_geographic_level(self, subcategory: str) -> str:
        """Get geographic classification level based on subcategory."""
        level_map = {
            'mountains': 'physical_feature',
            'rivers': 'hydrographic_feature',
            'lakes': 'hydrographic_feature',
            'landmarks': 'cultural_feature',
            'buildings': 'structural_feature',
            'parks': 'conservation_area',
            'forests': 'conservation_area'
        }
        return level_map.get(subcategory, 'geographic_feature')
    
    def _calculate_gpe_confidence(self, text: str, subcategory: str) -> float:
        """Calculate normalization confidence for GPE entities based on metadata."""
        base_confidence = 0.7  # Default confidence
        
        # Higher confidence for well-known subcategories
        if subcategory in ['countries', 'us_states']:
            base_confidence = 0.9
        elif subcategory in ['major_cities']:
            base_confidence = 0.8
        elif subcategory in ['urban_settlements', 'provinces']:
            base_confidence = 0.75
        
        # Text-based confidence adjustments
        text_lower = text.lower()
        
        # Boost confidence for formal names (capital letters, proper formatting)
        if text.istitle() or text.isupper():
            base_confidence += 0.05
        
        # Reduce confidence for ambiguous short names
        if len(text) <= 2:
            base_confidence -= 0.1
        
        # Boost confidence for known patterns
        if subcategory == 'us_states' and len(text) == 2 and text.isupper():
            base_confidence += 0.1  # State abbreviations
        
        return min(1.0, max(0.1, base_confidence))
    
    def _calculate_location_confidence(self, text: str, subcategory: str) -> float:
        """Calculate normalization confidence for location entities based on metadata."""
        base_confidence = 0.7  # Default confidence
        
        # Higher confidence for physical features with clear subcategories
        if subcategory in ['mountains', 'rivers', 'lakes']:
            base_confidence = 0.85
        elif subcategory in ['landmarks', 'parks']:
            base_confidence = 0.8
        elif subcategory in ['buildings']:
            base_confidence = 0.75
        
        # Text-based confidence adjustments
        if 'Mountain' in text or 'River' in text or 'Lake' in text:
            base_confidence += 0.05  # Clear geographic indicators
        
        if len(text.split()) >= 2:
            base_confidence += 0.05  # Multi-word names typically more specific
        
        return min(1.0, max(0.1, base_confidence))
    
    def _get_iso_standards(self, canonical_form: str, subcategory: str) -> Dict[str, str]:
        """Get ISO codes and formal names for high-confidence GPE entities."""
        iso_data = {}
        
        if subcategory == 'countries':
            # Common country ISO codes (could be expanded)
            country_codes = {
                'United States': {'iso_alpha2': 'US', 'iso_alpha3': 'USA', 'iso_numeric': '840'},
                'United Kingdom': {'iso_alpha2': 'GB', 'iso_alpha3': 'GBR', 'iso_numeric': '826'},
                'Canada': {'iso_alpha2': 'CA', 'iso_alpha3': 'CAN', 'iso_numeric': '124'},
                'Germany': {'iso_alpha2': 'DE', 'iso_alpha3': 'DEU', 'iso_numeric': '276'},
                'France': {'iso_alpha2': 'FR', 'iso_alpha3': 'FRA', 'iso_numeric': '250'},
                'China': {'iso_alpha2': 'CN', 'iso_alpha3': 'CHN', 'iso_numeric': '156'},
                'Japan': {'iso_alpha2': 'JP', 'iso_alpha3': 'JPN', 'iso_numeric': '392'},
                'Australia': {'iso_alpha2': 'AU', 'iso_alpha3': 'AUS', 'iso_numeric': '036'}
            }
            iso_data.update(country_codes.get(canonical_form, {}))
        
        elif subcategory == 'us_states':
            # USPS state codes (subset - could be expanded)
            state_codes = {
                'California': {'usps_code': 'CA', 'fips_code': '06'},
                'New York': {'usps_code': 'NY', 'fips_code': '36'},
                'Texas': {'usps_code': 'TX', 'fips_code': '48'},
                'Florida': {'usps_code': 'FL', 'fips_code': '12'}
            }
            iso_data.update(state_codes.get(canonical_form, {}))
        
        return iso_data
    
    def _parse_regulation_structure(self, regulation_text: str) -> Dict[str, Any]:
        """Parse regulation text to structured regulatory reference with authority metadata."""
        try:
            import re
            
            # CFR Pattern: 29 CFR 1910.132
            cfr_match = re.match(r'(\d+)\s+CFR\s+(\d+)(?:\.(\d+))?', regulation_text, re.IGNORECASE)
            if cfr_match:
                title = cfr_match.group(1)
                part = cfr_match.group(2)
                section = cfr_match.group(3)
                
                # Map title to authority
                authority_map = {
                    '29': 'Department of Labor',
                    '40': 'Environmental Protection Agency',
                    '49': 'Department of Transportation',
                    '21': 'Food and Drug Administration'
                }
                authority = authority_map.get(title, 'Federal Government')
                
                # Subject area mapping
                subject_map = {
                    '29': 'Occupational Safety',
                    '40': 'Environmental Protection',
                    '49': 'Transportation',
                    '21': 'Food and Drug Safety'
                }
                subject_area = subject_map.get(title, 'Federal Regulation')
                
                canonical_format = f"CFR-{title}-{part}-{section}" if section else f"CFR-{title}-{part}"
                full_citation = f"{title} CFR § {part}.{section}" if section else f"{title} CFR § {part}"
                url = f"https://www.ecfr.gov/current/title-{title}/subtitle-B/chapter-XVII/part-{part}/section-{part}.{section}" if section else f"https://www.ecfr.gov/current/title-{title}/part-{part}"
                
                return {
                    'original_text': regulation_text,
                    'canonical_format': canonical_format,
                    'regulation_type': 'CFR',
                    'title': title,
                    'part': part,
                    'section': section,
                    'authority': authority,
                    'subject_area': subject_area,
                    'full_citation': full_citation,
                    'url': url
                }
            
            # ISO Pattern: ISO 9001:2015
            iso_match = re.match(r'ISO\s+(\d+)(?::(\d{4}))?', regulation_text, re.IGNORECASE)
            if iso_match:
                standard = iso_match.group(1)
                year = iso_match.group(2)
                
                canonical_format = f"ISO-{standard}-{year}" if year else f"ISO-{standard}"
                full_citation = f"ISO {standard}:{year}" if year else f"ISO {standard}"
                
                return {
                    'original_text': regulation_text,
                    'canonical_format': canonical_format,
                    'regulation_type': 'ISO',
                    'standard': standard,
                    'year': year,
                    'authority': 'International Organization for Standardization',
                    'subject_area': 'International Standards',
                    'full_citation': full_citation,
                    'url': f"https://www.iso.org/standard/{standard}.html"
                }
            
            # ANSI Pattern: ANSI Z359.11
            ansi_match = re.match(r'ANSI\s+([A-Z]?\d+(?:\.\d+)*)', regulation_text, re.IGNORECASE)
            if ansi_match:
                standard = ansi_match.group(1)
                
                canonical_format = f"ANSI-{standard}"
                full_citation = f"ANSI {standard}"
                
                return {
                    'original_text': regulation_text,
                    'canonical_format': canonical_format,
                    'regulation_type': 'ANSI',
                    'standard': standard,
                    'authority': 'American National Standards Institute',
                    'subject_area': 'American National Standards',
                    'full_citation': full_citation,
                    'url': f"https://www.ansi.org/"
                }
            
            # NFPA Pattern: NFPA 70E
            nfpa_match = re.match(r'NFPA\s+(\d+[A-Z]?)', regulation_text, re.IGNORECASE)
            if nfpa_match:
                standard = nfpa_match.group(1)
                
                canonical_format = f"NFPA-{standard}"
                full_citation = f"NFPA {standard}"
                
                return {
                    'original_text': regulation_text,
                    'canonical_format': canonical_format,
                    'regulation_type': 'NFPA',
                    'standard': standard,
                    'authority': 'National Fire Protection Association',
                    'subject_area': 'Fire Protection Standards',
                    'full_citation': full_citation,
                    'url': f"https://www.nfpa.org/"
                }
                
        except Exception:
            pass
            
        return None
    
    def _generate_statistics(self, original_entities: Dict, normalized_entities: List[NormalizedEntity], processing_time: float) -> Dict[str, Any]:
        """Generate normalization statistics."""
        stats = {
            'processing_time_ms': processing_time,
            'original_entity_count': sum(len(entities) for entities in original_entities.values()),
            'normalized_entity_count': len(normalized_entities),
            'entity_reduction_percent': 0.0,
            'entity_types_processed': len([e for e in normalized_entities if e.count > 0]),
            'canonical_forms_created': len(normalized_entities),
            'total_mentions': sum(e.count for e in normalized_entities),
            'performance_metrics': {
                'entities_per_ms': len(normalized_entities) / processing_time if processing_time > 0 else 0,
                'memory_efficient': processing_time < 50,  # Target: <50ms
                'edge_compatible': processing_time < 100   # CloudFlare limit
            }
        }
        
        # Calculate reduction percentage
        if stats['original_entity_count'] > 0:
            stats['entity_reduction_percent'] = ((stats['original_entity_count'] - stats['normalized_entity_count']) / stats['original_entity_count']) * 100
        
        return stats
    
    # =============================================================================
    # LEGACY: INDIVIDUAL ENTITY NORMALIZATION METHODS (preserved for compatibility)
    # =============================================================================
    
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
    
    def _normalize_measurement(self, value: str, span: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Normalize measurements following industry standards from MVP-FUSION-NER.md PRD.
        
        Returns structured schema: value, unit, text, type, span, normalized
        Uses canonical unit conversion map for all 10 measurement categories.
        """
        try:
            # Use the new MeasurementNormalizer for industry-standard normalization
            from normalization import MeasurementNormalizer
            
            normalizer = MeasurementNormalizer()
            measurements = normalizer.extract_measurements(value)
            
            if measurements:
                # Return the first measurement found, converted to dict
                measurement = measurements[0]
                result = normalizer.to_dict(measurement)
                
                # Override span if provided (for integration with existing pipeline)
                if span:
                    result['span'] = span
                
                # Add legacy compatibility fields
                result.update({
                    'category': result['type'],  # Legacy field name
                    'metric_value': result['normalized']['value'],
                    'metric_unit': result['normalized']['unit'],
                    'formatted_metric': f"{result['normalized']['value']:.1f} {result['normalized']['unit']}"
                })
                
                return result
            else:
                # Fallback to legacy method if new normalizer fails
                return self._normalize_measurement_legacy(value)
                
        except Exception as e:
            # Fallback to legacy method on any error
            return self._normalize_measurement_legacy(value)
    
    def _normalize_measurement_legacy(self, value: str) -> Dict[str, Any]:
        """Legacy measurement normalization (kept for fallback compatibility)."""
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