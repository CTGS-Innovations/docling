"""
SPO Pattern Loader - AC Predicate Dictionary Integration

This module loads and organizes the SPO predicate dictionaries for integration
with the Aho-Corasick engine. It provides high-performance pattern loading and
categorization for the hybrid AC+FLPC SPO extraction system.

Performance Characteristics:
- Load Time: O(m) where m = number of patterns
- Memory: Shared AC automaton for all patterns
- Lookup: O(1) per pattern match
- Categories: 9 predicate categories for semantic classification
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from .spo_component_cache import PredicateCategory
except ImportError:
    # Fallback for direct execution
    from spo_component_cache import PredicateCategory

@dataclass
class SPOPattern:
    """Represents a single SPO pattern for AC engine"""
    text: str
    category: PredicateCategory
    pattern_type: str  # 'predicate', 'modifier', etc.
    confidence: float = 0.9
    metadata: Optional[Dict] = None

class SPOPatternLoader:
    """
    Loads and organizes SPO predicate patterns from foundation data
    
    Integrates with AC engine for high-performance exact pattern matching.
    Provides categorized access to predicate patterns for semantic classification.
    """
    
    def __init__(self, foundation_data_path: str = None):
        """Initialize pattern loader with foundation data path"""
        if foundation_data_path is None:
            # Default to foundation data directory
            current_dir = Path(__file__).parent
            foundation_data_path = current_dir.parent.parent / "knowledge" / "corpus" / "foundation_data" / "spo"
        
        self.foundation_path = Path(foundation_data_path)
        self.logger = logging.getLogger(__name__)
        
        # Pattern storage
        self.patterns_by_category: Dict[PredicateCategory, List[SPOPattern]] = {}
        self.all_patterns: List[SPOPattern] = []
        self.pattern_lookup: Dict[str, SPOPattern] = {}
        
        # File mapping
        self.category_files = {
            PredicateCategory.STATE: "state_predicates.txt",
            PredicateCategory.OWNERSHIP: "ownership_predicates.txt", 
            PredicateCategory.LOCATION: "location_predicates.txt",
            PredicateCategory.RELATIONSHIP: "relationship_predicates.txt",
            PredicateCategory.BUSINESS: "business_predicates.txt",
            PredicateCategory.LEGAL_REGULATORY: "legal_regulatory_predicates.txt",
            PredicateCategory.OBLIGATIONS: "obligations_compliance_predicates.txt",
            PredicateCategory.QUANTITATIVE: "quantitative_performance_predicates.txt",
            PredicateCategory.CAUSALITY: "causality_conditions_predicates.txt"
        }
        
        # Load patterns on initialization
        self._load_all_patterns()
    
    def _load_all_patterns(self) -> None:
        """Load all predicate patterns from foundation data files"""
        self.logger.info(f"Loading SPO patterns from: {self.foundation_path}")
        
        total_patterns = 0
        
        for category, filename in self.category_files.items():
            file_path = self.foundation_path / filename
            
            if not file_path.exists():
                self.logger.warning(f"Pattern file not found: {file_path}")
                continue
            
            patterns = self._load_category_patterns(file_path, category)
            self.patterns_by_category[category] = patterns
            self.all_patterns.extend(patterns)
            total_patterns += len(patterns)
            
            self.logger.debug(f"Loaded {len(patterns)} patterns for {category.value}")
        
        # Build lookup index
        for pattern in self.all_patterns:
            self.pattern_lookup[pattern.text.lower()] = pattern
        
        self.logger.info(f"Successfully loaded {total_patterns} SPO patterns across {len(self.category_files)} categories")
    
    def _load_category_patterns(self, file_path: Path, category: PredicateCategory) -> List[SPOPattern]:
        """Load patterns from a single category file"""
        patterns = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Create pattern object
                    pattern = SPOPattern(
                        text=line,
                        category=category,
                        pattern_type='predicate',
                        confidence=0.9,
                        metadata={
                            'source_file': file_path.name,
                            'line_number': line_num
                        }
                    )
                    
                    patterns.append(pattern)
        
        except Exception as e:
            self.logger.error(f"Error loading patterns from {file_path}: {e}")
            return []
        
        return patterns
    
    def get_patterns_for_ac_engine(self) -> List[Tuple[str, Dict]]:
        """
        Get patterns formatted for AC engine integration
        
        Returns:
            List of (pattern_text, metadata) tuples for AC engine
        """
        ac_patterns = []
        
        for pattern in self.all_patterns:
            metadata = {
                'category': pattern.category.value,
                'pattern_type': pattern.pattern_type,
                'confidence': pattern.confidence,
                'spo_pattern_obj': pattern  # Reference to full pattern object
            }
            
            ac_patterns.append((pattern.text, metadata))
        
        return ac_patterns
    
    def get_patterns_by_category(self, category: PredicateCategory) -> List[SPOPattern]:
        """Get all patterns for a specific category"""
        return self.patterns_by_category.get(category, [])
    
    def get_pattern_by_text(self, text: str) -> Optional[SPOPattern]:
        """Get pattern object by text (case-insensitive)"""
        return self.pattern_lookup.get(text.lower())
    
    def get_all_pattern_texts(self) -> List[str]:
        """Get list of all pattern texts for AC engine"""
        return [pattern.text for pattern in self.all_patterns]
    
    def get_category_for_text(self, text: str) -> Optional[PredicateCategory]:
        """Get category for a pattern text"""
        pattern = self.get_pattern_by_text(text)
        return pattern.category if pattern else None
    
    def get_high_frequency_patterns(self, limit: int = 100) -> List[SPOPattern]:
        """
        Get most important patterns for priority AC processing
        
        Returns the most common/important patterns for optimized AC loading.
        """
        # Priority order based on frequency and importance
        priority_categories = [
            PredicateCategory.STATE,           # is, was, are (highest frequency)
            PredicateCategory.OWNERSHIP,       # owns, controls
            PredicateCategory.LOCATION,        # located in, based in
            PredicateCategory.BUSINESS,        # founded, acquired
            PredicateCategory.RELATIONSHIP     # married to, works for
        ]
        
        high_priority_patterns = []
        
        for category in priority_categories:
            patterns = self.get_patterns_by_category(category)
            high_priority_patterns.extend(patterns[:20])  # Top 20 per category
            
            if len(high_priority_patterns) >= limit:
                break
        
        return high_priority_patterns[:limit]
    
    def get_pattern_statistics(self) -> Dict[str, any]:
        """Get statistics about loaded patterns"""
        stats = {
            'total_patterns': len(self.all_patterns),
            'categories': len(self.patterns_by_category),
            'patterns_by_category': {},
            'average_pattern_length': 0,
            'longest_pattern': "",
            'shortest_pattern': ""
        }
        
        # Category breakdown
        for category, patterns in self.patterns_by_category.items():
            stats['patterns_by_category'][category.value] = len(patterns)
        
        # Pattern length analysis
        if self.all_patterns:
            pattern_lengths = [len(p.text) for p in self.all_patterns]
            stats['average_pattern_length'] = sum(pattern_lengths) / len(pattern_lengths)
            
            longest = max(self.all_patterns, key=lambda p: len(p.text))
            shortest = min(self.all_patterns, key=lambda p: len(p.text))
            
            stats['longest_pattern'] = longest.text
            stats['shortest_pattern'] = shortest.text
        
        return stats
    
    def validate_patterns(self) -> Dict[str, List[str]]:
        """
        Validate loaded patterns for quality and consistency
        
        Returns:
            Dictionary of validation issues by category
        """
        issues = {
            'duplicates': [],
            'empty_patterns': [],
            'suspicious_patterns': [],
            'encoding_issues': []
        }
        
        seen_patterns = set()
        
        for pattern in self.all_patterns:
            # Check for duplicates
            if pattern.text.lower() in seen_patterns:
                issues['duplicates'].append(pattern.text)
            else:
                seen_patterns.add(pattern.text.lower())
            
            # Check for empty patterns
            if not pattern.text.strip():
                issues['empty_patterns'].append(f"Empty pattern in {pattern.category.value}")
            
            # Check for suspicious patterns (too short/long)
            if len(pattern.text) < 2:
                issues['suspicious_patterns'].append(f"Very short pattern: '{pattern.text}'")
            elif len(pattern.text) > 50:
                issues['suspicious_patterns'].append(f"Very long pattern: '{pattern.text[:30]}...'")
            
            # Check for encoding issues
            try:
                pattern.text.encode('utf-8')
            except UnicodeEncodeError:
                issues['encoding_issues'].append(pattern.text)
        
        return issues
    
    def export_for_ac_integration(self, output_file: str = None) -> str:
        """
        Export patterns in format suitable for AC engine integration
        
        Returns JSON string or writes to file if output_file specified.
        """
        import json
        
        export_data = {
            'metadata': {
                'total_patterns': len(self.all_patterns),
                'categories': list(self.category_files.keys()),
                'generated_by': 'SPOPatternLoader',
                'version': '1.0'
            },
            'patterns': []
        }
        
        for pattern in self.all_patterns:
            pattern_data = {
                'text': pattern.text,
                'category': pattern.category.value,
                'type': pattern.pattern_type,
                'confidence': pattern.confidence
            }
            export_data['patterns'].append(pattern_data)
        
        json_output = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            self.logger.info(f"Exported {len(self.all_patterns)} patterns to {output_file}")
        
        return json_output

# Global instance for easy access
_pattern_loader_instance = None

def get_spo_pattern_loader() -> SPOPatternLoader:
    """Get global SPO pattern loader instance (singleton)"""
    global _pattern_loader_instance
    
    if _pattern_loader_instance is None:
        _pattern_loader_instance = SPOPatternLoader()
    
    return _pattern_loader_instance

def load_spo_patterns_for_ac() -> List[Tuple[str, Dict]]:
    """Convenience function to load SPO patterns for AC engine"""
    loader = get_spo_pattern_loader()
    return loader.get_patterns_for_ac_engine()

# Testing and validation functions
if __name__ == "__main__":
    # Test pattern loading
    loader = SPOPatternLoader()
    
    print("SPO Pattern Loader Test")
    print("=" * 50)
    
    stats = loader.get_pattern_statistics()
    print(f"Total patterns loaded: {stats['total_patterns']}")
    print(f"Categories: {stats['categories']}")
    print("\nPatterns by category:")
    for category, count in stats['patterns_by_category'].items():
        print(f"  {category}: {count}")
    
    print(f"\nAverage pattern length: {stats['average_pattern_length']:.1f}")
    print(f"Longest pattern: {stats['longest_pattern']}")
    print(f"Shortest pattern: {stats['shortest_pattern']}")
    
    # Validation
    issues = loader.validate_patterns()
    print("\nValidation results:")
    for issue_type, items in issues.items():
        if items:
            print(f"  {issue_type}: {len(items)} issues")
        else:
            print(f"  {issue_type}: OK")
    
    # Test AC integration format
    ac_patterns = loader.get_patterns_for_ac_engine()
    print(f"\nGenerated {len(ac_patterns)} patterns for AC engine")
    
    # Show sample patterns
    print("\nSample patterns:")
    for i, (text, metadata) in enumerate(ac_patterns[:5]):
        print(f"  {i+1}. '{text}' ({metadata['category']})")