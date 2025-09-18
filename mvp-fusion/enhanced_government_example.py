"""
EXAMPLE: Enhanced Government Entity Recognition
Shows how CSV integration would work in geographic_data.py
"""

import csv
from typing import Set, Dict, Optional
from pathlib import Path

class EnhancedReferenceData:
    """Example of how geographic_data.py would be enhanced"""
    
    def __init__(self):
        self._base_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        self._csv_path = Path(__file__).parent / "knowledge/corpus/temp_data/agency_codes.csv"
        
        # Current data (unchanged)
        self.us_states: Set[str] = self._load_set("us_states.txt")
        self.countries: Set[str] = self._load_set("countries.txt")
        self.major_cities: Set[str] = self._load_set("major_cities.txt")
        self.unicorn_companies: Set[str] = self._load_set("unicorn_companies.txt")
        self.investors: Set[str] = self._load_set("investors.txt")
        
        # NEW: Enhanced government data from CSV
        self.government_agencies: Set[str] = set()
        self.government_abbreviations: Set[str] = set()
        self.government_aliases: Dict[str, str] = {}
        self._load_government_data()
    
    def _load_set(self, filename: str) -> Set[str]:
        """Load text file into set (unchanged from current)"""
        file_path = self._base_path / filename
        if not file_path.exists():
            return set()
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}
    
    def _load_government_data(self):
        """NEW: Load government data from CSV"""
        if not self._csv_path.exists():
            print(f"Warning: {self._csv_path} not found")
            return
            
        with open(self._csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                agency_name = row.get('AGENCY NAME', '').strip()
                agency_abbrev = row.get('AGENCY ABBREVIATION', '').strip()
                subtier_name = row.get('SUBTIER NAME', '').strip()
                
                # Add full agency names
                if agency_name:
                    self.government_agencies.add(agency_name.lower())
                    
                # Add subtier organizations 
                if subtier_name and subtier_name != agency_name:
                    self.government_agencies.add(subtier_name.lower())
                
                # Add abbreviations and create aliases
                if agency_abbrev and agency_name:
                    self.government_abbreviations.add(agency_abbrev.lower())
                    self.government_aliases[agency_abbrev.lower()] = agency_name
    
    def classify_organization(self, org_name: str) -> str:
        """
        ENHANCED: Government detection with CSV data
        Returns: 'unicorn_company', 'investor', 'government', 'company', or 'organization'
        """
        org_lower = org_name.lower()
        
        # High-value unicorn companies (unchanged)
        if org_name in self.unicorn_companies:
            return 'unicorn_company'
        
        # Investment firms and VCs (unchanged)
        if org_name in self.investors:
            return 'investor'
        
        # NEW: Precise government detection from CSV
        if org_lower in self.government_agencies or org_lower in self.government_abbreviations:
            return 'government'
        
        # Fallback: Government agencies (pattern matching - unchanged)
        gov_indicators = {'Department', 'Agency', 'Administration', 'Commission', 'Bureau'}
        if any(indicator in org_name for indicator in gov_indicators):
            return 'government'
        
        # Corporate suffixes (unchanged)
        corp_suffixes = {'Inc', 'LLC', 'Corp', 'Corporation', 'Company', 'Ltd', 'Limited'}
        if any(suffix in org_name for suffix in corp_suffixes):
            return 'company'
        
        return 'organization'
    
    def resolve_government_alias(self, name: str) -> Optional[str]:
        """NEW: Resolve abbreviation to full name"""
        return self.government_aliases.get(name.lower())
    
    def is_government_agency(self, org_name: str) -> bool:
        """NEW: Precise government agency detection"""
        org_lower = org_name.lower()
        return (org_lower in self.government_agencies or 
                org_lower in self.government_abbreviations)

# DEMONSTRATION
if __name__ == "__main__":
    print("🚀 ENHANCED GOVERNMENT ENTITY RECOGNITION DEMO")
    print("=" * 60)
    
    # This would replace the current ReferenceData class
    ref = EnhancedReferenceData()
    
    print(f"📊 DATA LOADED:")
    print(f"  Government Agencies: {len(ref.government_agencies)}")
    print(f"  Government Abbreviations: {len(ref.government_abbreviations)}")
    print(f"  Alias Mappings: {len(ref.government_aliases)}")
    
    print(f"\n🔍 CLASSIFICATION EXAMPLES:")
    test_cases = [
        "GAO",
        "FDA", 
        "Library of Congress",
        "NASA",
        "Sequoia Capital",  # Should be investor
        "SpaceX",           # Should be unicorn_company
        "Microsoft Corp",   # Should be company
        "Random Org"        # Should be organization
    ]
    
    for entity in test_cases:
        classification = ref.classify_organization(entity)
        alias = ref.resolve_government_alias(entity)
        
        result = f"{entity:<20} → {classification}"
        if alias:
            result += f" (full name: {alias})"
            
        print(f"  {result}")