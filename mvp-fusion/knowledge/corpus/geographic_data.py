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
import csv
from typing import Set, Optional, Dict, Any
from pathlib import Path


class ReferenceData:
    """Centralized reference data with performant O(1) lookups"""
    
    def __init__(self):
        self._base_path = Path(__file__).parent / "foundation_data"
        self._csv_path = Path(__file__).parent / "temp_data" / "agency_codes.csv"
        
        # Geographic data
        self.us_states: Set[str] = self._load_set("us_states.txt")
        self.countries: Set[str] = self._load_set("countries.txt")  
        self.major_cities: Set[str] = self._load_set("major_cities.txt")
        
        # Organization data
        self.unicorn_companies: Set[str] = self._load_set("unicorn_companies.txt")
        self.investors: Set[str] = self._load_set("investors.txt")
        
        # Enhanced government entity data
        self.government_agencies: Set[str] = set()
        self.government_abbreviations: Set[str] = set()
        self.government_enrichment: Dict[str, Dict[str, Any]] = {}
        self._load_government_enrichment()
        
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
    
    def _load_government_enrichment(self):
        """Load government entity enrichment data from CSV with proper subtier handling"""
        if not self._csv_path.exists():
            print(f"Warning: Government enrichment CSV not found at {self._csv_path}")
            return
        
        try:
            with open(self._csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    agency_name = row.get('AGENCY NAME', '').strip()
                    agency_abbrev = row.get('AGENCY ABBREVIATION', '').strip()
                    subtier_name = row.get('SUBTIER NAME', '').strip()
                    subtier_abbrev = row.get('SUBTIER ABBREVIATION', '').strip()
                    website = row.get('WEBSITE', '').strip()
                    mission = row.get('MISSION', '').strip()
                    
                    # FIXED: Create separate entries for agency and subtier entities
                    
                    # 1. Index main agency if it has a name
                    if agency_name:
                        enrichment_data = {
                            'formal_name': agency_name,
                            'abbreviation': agency_abbrev,
                            'website': website,
                            'mission': mission,
                            'entity_type': 'government_entity',
                            'subtier': None  # This is the main agency
                        }
                        
                        key_name = agency_name.lower()
                        self.government_agencies.add(key_name)
                        self.government_enrichment[key_name] = enrichment_data
                        
                        if agency_abbrev:
                            key_abbrev = agency_abbrev.lower()
                            self.government_abbreviations.add(key_abbrev)
                            self.government_enrichment[key_abbrev] = enrichment_data
                    
                    # 2. FIXED: Index subtier as separate entity with its own formal name
                    if subtier_name and subtier_name != agency_name:
                        # Create proper enrichment data for subtier agency
                        subtier_enrichment = {
                            'formal_name': subtier_name,  # Use subtier name as formal name
                            'abbreviation': subtier_abbrev,  # Use subtier abbreviation if available
                            'website': website,
                            'mission': mission,
                            'entity_type': 'government_entity',
                            'parent_agency': agency_name,  # Track parent department
                            'subtier': subtier_name
                        }
                        
                        # Index subtier by its full name
                        key_subtier = subtier_name.lower()
                        self.government_agencies.add(key_subtier)
                        self.government_enrichment[key_subtier] = subtier_enrichment
                        
                        # Index subtier by its abbreviation if available
                        if subtier_abbrev:
                            key_subtier_abbrev = subtier_abbrev.lower()
                            self.government_abbreviations.add(key_subtier_abbrev)
                            self.government_enrichment[key_subtier_abbrev] = subtier_enrichment
                        
                        # FIXED: Infer common abbreviations for well-known agencies
                        subtier_lower = subtier_name.lower()
                        inferred_abbrev = None
                        
                        if 'centers for disease control' in subtier_lower:
                            inferred_abbrev = 'cdc'
                        elif 'occupational safety and health administration' in subtier_lower:
                            inferred_abbrev = 'osha'
                        elif 'food and drug administration' in subtier_lower:
                            inferred_abbrev = 'fda'
                        elif 'environmental protection agency' in subtier_lower:
                            inferred_abbrev = 'epa'
                        
                        if inferred_abbrev:
                            self.government_abbreviations.add(inferred_abbrev)
                            self.government_enrichment[inferred_abbrev] = subtier_enrichment
                            # Update the abbreviation in the enrichment data
                            subtier_enrichment['abbreviation'] = inferred_abbrev.upper()
                            
        except Exception as e:
            print(f"Warning: Error loading government enrichment data: {e}")
    
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
        
        Returns: 'unicorn_company', 'investor', 'government_entity', 'company', or 'organization'
        """
        # High-value unicorn companies
        if org_name in self.unicorn_companies:
            return 'unicorn_company'
        
        # Investment firms and VCs
        if org_name in self.investors:
            return 'investor'
        
        # Enhanced government entity detection (CSV-based)
        org_lower = org_name.lower()
        if org_lower in self.government_agencies or org_lower in self.government_abbreviations:
            return 'government_entity'
        
        # Fallback: Government agencies (pattern matching)
        gov_indicators = {'Department', 'Agency', 'Administration', 'Commission', 'Bureau'}
        if any(indicator in org_name for indicator in gov_indicators):
            return 'government_entity'
        
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
    
    def get_government_enrichment(self, org_name: str) -> Optional[Dict[str, Any]]:
        """
        Get rich metadata for government entities
        
        Returns enrichment data including formal_name, abbreviation, website, mission
        Only returns data if entity is classified as government_entity
        """
        org_lower = org_name.lower()
        return self.government_enrichment.get(org_lower)
    
    def is_government_entity(self, org_name: str) -> bool:
        """Check if organization is a government entity with enrichment data"""
        org_lower = org_name.lower()
        return (org_lower in self.government_agencies or 
                org_lower in self.government_abbreviations)


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