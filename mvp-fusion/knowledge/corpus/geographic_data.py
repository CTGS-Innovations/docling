"""
Centralized Reference Data System
=================================

High-performance lookup system using sets for O(1) lookups.
Replaces hardcoded lists scattered across extractors.

Includes:
- Geographic data (countries, states, cities)
- Organization data (companies, investors)

Usage:
    from knowledge.corpus.geographic_data import ReferenceData
    
    ref = ReferenceData()
    location_type = ref.classify_location("Texas")     # returns "state"
    org_type = ref.classify_organization("SpaceX")     # returns "unicorn_company"
    is_investor = ref.is_investor("Sequoia Capital")   # returns True
"""

import os
from typing import Set, Optional
from pathlib import Path


class ReferenceData:
    """Centralized reference data with performant O(1) lookups"""
    
    def __init__(self):
        self._base_path = Path(__file__).parent / "foundation_data"
        
        # Geographic data
        self.us_states: Set[str] = self._load_set("us_states.txt")
        self.countries: Set[str] = self._load_set("countries.txt")  
        self.major_cities: Set[str] = self._load_set("major_cities.txt")
        
        # Organization data
        self.unicorn_companies: Set[str] = self._load_set("unicorn_companies.txt")
        self.investors: Set[str] = self._load_set("investors.txt")
        
        # Combined lookup sets
        self.address_indicators = {
            'Street', 'St', 'Avenue', 'Ave', 'Road', 'Rd', 
            'Boulevard', 'Blvd', 'Drive', 'Dr', 'Lane', 'Ln'
        }
    
    def _load_set(self, filename: str) -> Set[str]:
        """Load text file into set for O(1) lookups"""
        file_path = self._base_path / filename
        
        if not file_path.exists():
            print(f"Warning: {filename} not found at {file_path}")
            return set()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}
    
    def classify_location(self, location: str) -> str:
        """
        Classify location type with high performance O(1) lookups
        
        Returns: 'address', 'country', 'state', 'city', or 'location'
        """
        # Address indicators
        if any(indicator in location for indicator in self.address_indicators):
            return 'address'
        
        # Countries (highest specificity)
        if location in self.countries:
            return 'country'
        
        # US States  
        if location in self.us_states:
            return 'state'
        
        # Major cities (only if in our verified list)
        if location in self.major_cities:
            return 'city'
        
        # NO fallback classification - only classify what we can verify
        # This prevents false positives like people names being classified as cities
        return 'location'
    
    def is_us_state(self, location: str) -> bool:
        """Check if location is a US state - O(1) lookup"""
        return location in self.us_states
    
    def is_country(self, location: str) -> bool:
        """Check if location is a country - O(1) lookup"""
        return location in self.countries
    
    def is_major_city(self, location: str) -> bool:
        """Check if location is a major city - O(1) lookup"""
        return location in self.major_cities
    
    # Organization classification methods
    def classify_organization(self, org_name: str) -> str:
        """
        Classify organization type with O(1) lookups
        
        Returns: 'unicorn_company', 'investor', 'government', 'company', or 'organization'
        """
        # High-value unicorn companies
        if org_name in self.unicorn_companies:
            return 'unicorn_company'
        
        # Investment firms and VCs
        if org_name in self.investors:
            return 'investor'
        
        # Government agencies (common patterns)
        gov_indicators = {'Department', 'Agency', 'Administration', 'Commission', 'Bureau'}
        if any(indicator in org_name for indicator in gov_indicators):
            return 'government'
        
        # Corporate suffixes
        corp_suffixes = {'Inc', 'LLC', 'Corp', 'Corporation', 'Company', 'Ltd', 'Limited'}
        if any(suffix in org_name for suffix in corp_suffixes):
            return 'company'
        
        return 'organization'
    
    def is_unicorn_company(self, org_name: str) -> bool:
        """Check if organization is a unicorn startup - O(1) lookup"""
        return org_name in self.unicorn_companies
    
    def is_investor(self, org_name: str) -> bool:
        """Check if organization is an investor/VC - O(1) lookup"""
        return org_name in self.investors


# Maintain backward compatibility
GeographicData = ReferenceData

# Singleton instance for efficient reuse
_reference_data = None

def get_geographic_data() -> ReferenceData:
    """Get singleton ReferenceData instance (backward compatible name)"""
    global _reference_data
    if _reference_data is None:
        _reference_data = ReferenceData()
    return _reference_data

def get_reference_data() -> ReferenceData:
    """Get singleton ReferenceData instance"""
    return get_geographic_data()