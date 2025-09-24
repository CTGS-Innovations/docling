#!/usr/bin/env python3
"""
Text Cleaner for JSON Knowledge Extraction
==========================================
Comprehensive cleaner to remove tagged elements, newlines, and special characters
from semantic extraction results.

Purpose:
- Remove Core8 tagged elements (meas013||, org004||, etc.)
- Replace newlines with spaces
- Clean up fragmented text and special characters
- Preserve meaningful content while ensuring clean output
"""

import re
from typing import Dict, Any, List, Union
from utils.logging_config import get_fusion_logger

logger = get_fusion_logger("text_cleaner")

class TextCleaner:
    """Comprehensive text cleaner for knowledge extraction JSON fields"""
    
    def __init__(self):
        """Initialize cleaner with patterns for Core8 tags and special characters"""
        
        # Core8 tagged element patterns - preserve meaningful content in parentheses
        self.core8_patterns = [
            # Measurement tags: meas013|| (30 cm) → (30 cm)  
            (r'meas\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'meas\d{3}\|\|', ''),  # Remove tag without parentheses
            
            # Person tags: person042|| (John Smith) → (John Smith)
            (r'person\d{3}\|\|\s*(\([^)]*\))', r'\1'), 
            (r'person\d{3}\|\|', ''),
            
            # Organization tags: org005|| (EPA) → (EPA)
            (r'org\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'org\d{3}\|\|', ''),
            
            # Location/GPE tags: gpe001|| (New York) → (New York)
            (r'(?:gpe|location)\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'(?:gpe|location)\d{3}\|\|', ''),
            
            # Financial tags: money003|| ($2,500) → ($2,500)
            (r'money\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'money\d{3}\|\|', ''),
            
            # Date tags: date004|| (March 15, 2024) → (March 15, 2024)
            (r'date\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'date\d{3}\|\|', ''),
            
            # Time tags: time002|| (2:30 PM) → (2:30 PM)
            (r'time\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'time\d{3}\|\|', ''),
            
            # Quantity tags: quantity001|| (500) → (500)
            (r'quantity\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'quantity\d{3}\|\|', ''),
            
            # Generic incomplete tags: ||0, ||1, ||anything
            (r'\|\|\d*', ''),
            (r'\|\|[^|]*\|\|', ''),  # Complete ||anything||
            (r'\|\|$', ''),          # Trailing ||
        ]
        
        print(f"🧹 Text cleaner initialized with {len(self.core8_patterns)} Core8 cleaning patterns")
    
    def clean_text_field(self, text: str) -> str:
        """Clean a single text field by removing tags, newlines, and special characters"""
        if not text or not isinstance(text, str):
            return text
        
        cleaned = text
        
        # Step 1: Remove Core8 tagged elements (preserve meaningful content in parentheses)
        for pattern, replacement in self.core8_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Step 2: Replace newlines with single spaces
        cleaned = re.sub(r'\n+', ' ', cleaned)
        
        # Step 3: Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Step 4: Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Step 5: Clean up punctuation artifacts from tag removal
        cleaned = re.sub(r'\s*,\s*,', ',', cleaned)  # Double commas
        cleaned = re.sub(r'\s*\.\s*\.', '.', cleaned)  # Double periods
        cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)  # Space before punctuation
        
        return cleaned
    
    def clean_fact(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Clean all text fields in a single fact object"""
        if not isinstance(fact, dict):
            return fact
        
        cleaned_fact = fact.copy()
        
        # Clean top-level text fields
        for field in ['context', 'subject', 'object']:
            if field in cleaned_fact:
                cleaned_fact[field] = self.clean_text_field(cleaned_fact[field])
        
        # Clean nested 'extra' fields
        if 'extra' in cleaned_fact and isinstance(cleaned_fact['extra'], dict):
            extra = cleaned_fact['extra'].copy()
            for field in ['context', 'subject', 'object', 'predicate']:
                if field in extra:
                    extra[field] = self.clean_text_field(extra[field])
            cleaned_fact['extra'] = extra
        
        return cleaned_fact
    
    def clean_semantic_facts(self, semantic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean all text fields in complete semantic facts JSON structure"""
        if not isinstance(semantic_data, dict):
            return semantic_data
        
        cleaned_data = semantic_data.copy()
        
        # Clean facts in semantic_facts section
        if 'semantic_facts' in cleaned_data and isinstance(cleaned_data['semantic_facts'], dict):
            cleaned_semantic_facts = {}
            
            for category, facts_list in cleaned_data['semantic_facts'].items():
                if isinstance(facts_list, list):
                    cleaned_facts_list = []
                    for fact in facts_list:
                        cleaned_fact = self.clean_fact(fact)
                        cleaned_facts_list.append(cleaned_fact)
                    cleaned_semantic_facts[category] = cleaned_facts_list
                else:
                    cleaned_semantic_facts[category] = facts_list
            
            cleaned_data['semantic_facts'] = cleaned_semantic_facts
        
        # Preserve other sections (semantic_summary, intelligent_extraction) as-is
        return cleaned_data
    
    def clean_json_file(self, input_path: str, output_path: str = None) -> str:
        """Clean text fields in a JSON file and save cleaned version"""
        import json
        from pathlib import Path
        
        input_path = Path(input_path)
        if not input_path.exists():
            print(f"🔴 Input file not found: {input_path}")
            return None
        
        # Read original JSON
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"🔴 Error reading JSON file {input_path}: {e}")
            return None
        
        # Clean the data
        cleaned_data = self.clean_semantic_facts(data)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        else:
            output_path = Path(output_path)
        
        # Save cleaned JSON
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            print(f"🧹 Cleaned JSON saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"🔴 Error writing cleaned JSON to {output_path}: {e}")
            return None

def clean_extraction_text(text: str) -> str:
    """Convenience function to clean a single text string"""
    cleaner = TextCleaner()
    return cleaner.clean_text_field(text)

def clean_extraction_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to clean semantic facts JSON data"""
    cleaner = TextCleaner()
    return cleaner.clean_semantic_facts(json_data)

# Example usage and testing
if __name__ == "__main__":
    # Test the cleaner
    test_text = """provided when ladders are the only\nway to enter or exit a work area where 25 or\nmore employees work or when a ladder serves\nsimultaneous two-way traff"""
    
    cleaner = TextCleaner()
    cleaned = cleaner.clean_text_field(test_text)
    
    print("🧪 TEXT CLEANER TEST")
    print("=" * 40)
    print(f"Original: {repr(test_text)}")
    print(f"Cleaned:  {repr(cleaned)}")
    print(f"\n✅ Newlines removed: {'\\n' not in cleaned}")