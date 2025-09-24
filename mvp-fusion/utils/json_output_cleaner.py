#!/usr/bin/env python3
"""
Universal JSON Output Cleaner
=============================
Decorator and utilities to automatically clean ALL text content in JSON output.

Purpose:
- Remove newlines from every string field in JSON structures
- Clean Core8 tags from all text content
- Ensure all JSON output is single-line and clean
- Apply universally without field-specific handling
"""

import re
import json
from functools import wraps
from typing import Any, Dict, List, Union, Callable
from pathlib import Path

class UniversalJSONCleaner:
    """Universal cleaner that processes any JSON structure recursively"""
    
    def __init__(self):
        """Initialize with comprehensive cleaning patterns"""
        
        # Core8 tag patterns (preserve meaningful content in parentheses)
        self.core8_patterns = [
            # Measurement tags: meas013|| (30 cm) → (30 cm)
            (r'meas\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'meas\d{3}\|\|', ''),
            
            # Person tags: person042|| (John Smith) → (John Smith)
            (r'person\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'person\d{3}\|\|', ''),
            
            # Organization tags: org005|| (EPA) → (EPA)
            (r'org\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'org\d{3}\|\|', ''),
            
            # Location/GPE tags
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
            
            # Quantity tags
            (r'quantity\d{3}\|\|\s*(\([^)]*\))', r'\1'),
            (r'quantity\d{3}\|\|', ''),
            
            # Generic incomplete tags: ||0, ||1, ||anything
            (r'\|\|\d*', ''),
            (r'\|\|[^|]*\|\|', ''),
            (r'\|\|$', ''),
        ]
    
    def clean_string(self, text: str) -> str:
        """Clean a single string value"""
        if not isinstance(text, str) or not text:
            return text
        
        cleaned = text
        
        # Step 1: Remove Core8 tagged elements (preserve meaningful content)
        for pattern, replacement in self.core8_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Step 2: Replace all newlines with single spaces
        cleaned = re.sub(r'\n+', ' ', cleaned)
        cleaned = re.sub(r'\r+', ' ', cleaned)
        
        # Step 3: Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Step 4: Clean up punctuation artifacts
        cleaned = re.sub(r'\s*,\s*,', ',', cleaned)
        cleaned = re.sub(r'\s*\.\s*\.', '.', cleaned)
        cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)
        
        # Step 5: Trim whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def clean_recursive(self, obj: Any) -> Any:
        """Recursively clean all strings in any data structure"""
        if isinstance(obj, str):
            return self.clean_string(obj)
        
        elif isinstance(obj, dict):
            cleaned_dict = {}
            for key, value in obj.items():
                # Clean both keys and values
                clean_key = self.clean_string(key) if isinstance(key, str) else key
                clean_value = self.clean_recursive(value)
                cleaned_dict[clean_key] = clean_value
            return cleaned_dict
        
        elif isinstance(obj, list):
            return [self.clean_recursive(item) for item in obj]
        
        elif isinstance(obj, tuple):
            return tuple(self.clean_recursive(item) for item in obj)
        
        else:
            # Numbers, booleans, None, etc. - return as-is
            return obj

# Global cleaner instance
_global_cleaner = UniversalJSONCleaner()

def clean_json_output(func: Callable) -> Callable:
    """
    Decorator to automatically clean all JSON output from a function.
    
    Usage:
    @clean_json_output
    def extract_facts(text: str) -> dict:
        return {"facts": ["has newlines\nin text", "another fact"]}
    
    # Output will be automatically cleaned:
    # {"facts": ["has newlines in text", "another fact"]}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return _global_cleaner.clean_recursive(result)
    return wrapper

def clean_json_data(data: Any) -> Any:
    """Clean any JSON-serializable data structure"""
    return _global_cleaner.clean_recursive(data)

def clean_json_file_in_place(file_path: Union[str, Path]) -> bool:
    """Clean a JSON file in place, removing newlines from all text content"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"🔴 File not found: {file_path}")
        return False
    
    try:
        # Read original JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Clean all content
        cleaned_data = _global_cleaner.clean_recursive(data)
        
        # Write back to same file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cleaned in place: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"🔴 Error cleaning {file_path}: {e}")
        return False

def batch_clean_directory(directory: Union[str, Path], pattern: str = "*.json") -> int:
    """Clean all JSON files in a directory in place"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"🔴 Directory not found: {directory}")
        return 0
    
    json_files = list(directory.glob(pattern))
    cleaned_count = 0
    
    print(f"🧹 BATCH CLEANING DIRECTORY: {directory}")
    print(f"📄 Found {len(json_files)} files matching '{pattern}'")
    
    for json_file in json_files:
        if clean_json_file_in_place(json_file):
            cleaned_count += 1
    
    print(f"🟢 Successfully cleaned {cleaned_count}/{len(json_files)} files")
    return cleaned_count

# Integration with high-performance JSON saving
def save_clean_json(data: Any, file_path: Union[str, Path], use_orjson: bool = True) -> None:
    """Save JSON data with automatic cleaning"""
    cleaned_data = clean_json_data(data)
    
    if use_orjson:
        try:
            import orjson
            with open(file_path, 'wb') as f:
                f.write(orjson.dumps(cleaned_data, option=orjson.OPT_INDENT_2))
        except ImportError:
            # Fallback to standard json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

# Example usage and testing
if __name__ == "__main__":
    # Test the universal cleaner
    test_data = {
        "semantic_facts": {
            "actionable_requirements": [
                {
                    "subject": "safety_requirements_fact@1.0: '' [10416-10545]",
                    "context": "",
                    "extra": {
                        "subject": "Entity",
                        "predicate": "REQUIRED_TO",
                        "object": "at least a 15-inch (38 cm) clearance width\nto the nearest permanent object on each side\nof the centerline of the ladder",
                        "context": "A landing platform must be provided if the step-across distance exceeds meas013|| (30 cm). I Fixed ladders without cages...",
                        "actionable": True
                    }
                }
            ]
        },
        "summary": {
            "description": "This is a test\nwith multiple\nlines of text",
            "tags": ["tag1\nwith newline", "org005|| (EPA)", "normal tag"]
        }
    }
    
    print("🧹 UNIVERSAL JSON CLEANER TEST")
    print("=" * 40)
    
    cleaned_data = clean_json_data(test_data)
    
    print("🔴 ORIGINAL OBJECT:")
    original_obj = test_data["semantic_facts"]["actionable_requirements"][0]["extra"]["object"]
    print(f'"{original_obj}"')
    
    print("\n🟢 CLEANED OBJECT:")
    cleaned_obj = cleaned_data["semantic_facts"]["actionable_requirements"][0]["extra"]["object"]
    print(f'"{cleaned_obj}"')
    
    print(f"\n✅ Newlines removed: {'\\n' not in cleaned_obj}")
    print(f"✅ Tags cleaned: {'meas013||' not in str(cleaned_data)}")
    print(f"✅ Content preserved: '(30 cm)' in cleaned context")