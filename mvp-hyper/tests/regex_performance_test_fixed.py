#!/usr/bin/env python3
"""
Regex Performance Comparison Test - Fixed Version
================================================
Compare Python re, Hyperscan, and FLPC for entity extraction performance.
"""

import re
import time
import random
import string
from typing import List, Dict, Tuple
import statistics

# Test if high-performance libraries are available
try:
    import hyperscan
    HYPERSCAN_AVAILABLE = True
except ImportError:
    HYPERSCAN_AVAILABLE = False
    print("⚠️  Hyperscan not available. Install with: pip install hyperscan")

try:
    import flpc
    FLPC_AVAILABLE = True
except ImportError:
    FLPC_AVAILABLE = False
    print("⚠️  FLPC not available. Install with: pip install flpc")


class TestDataGenerator:
    """Generate realistic test data with embedded entities."""
    
    def __init__(self):
        self.entity_templates = {
            'MONEY': ['$1,234.56', '$500,000', '$25M', '$2.5 billion', '$750'],
            'DATE': ['March 15, 2024', '2024-03-15', '12/25/2023', 'Jan 1, 2025'],
            'EMAIL': ['test@company.com', 'admin@example.org', 'user123@domain.net'],
            'PHONE': ['(555) 123-4567', '555-123-4567', '1-800-555-0199'],
            'PERCENT': ['95%', '87.5%', '12.34%', '100%'],
            'TIME': ['2:30 PM', '14:30', '9:45 AM', '23:59'],
            'URL': ['https://example.com', 'http://test.org/path', 'www.site.net'],
            'VERSION': ['v1.2.3', '2.1.0', 'version 3.4.5'],
            'MEASUREMENT': ['25 kg', '100 feet', '50.5 cm', '3.2 meters'],
            'RANGE': ['25-30', '10 to 15', '100-200'],
            'REGULATION': ['29 CFR 1926.95', '40 CFR 261.1', '21 CFR 210.3']
        }
    
    def generate_text(self, size_kb: int = 10, entity_density: float = 0.1) -> str:
        """Generate text of specified size with embedded entities."""
        # Base text generation
        words = []
        target_chars = size_kb * 1024
        
        # Common words for realistic text
        common_words = [
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'safety',
            'work', 'workers', 'company', 'policy', 'training', 'equipment',
            'management', 'compliance', 'regulation', 'standard', 'procedure'
        ]
        
        current_chars = 0
        while current_chars < target_chars:
            # Add regular words
            if random.random() > entity_density:
                word = random.choice(common_words)
            else:
                # Add entities
                entity_type = random.choice(list(self.entity_templates.keys()))
                word = random.choice(self.entity_templates[entity_type])
            
            words.append(word)
            current_chars += len(word) + 1  # +1 for space
            
            # Add punctuation occasionally
            if random.random() < 0.1:
                words.append(random.choice(['.', ',', '!', '?', ';']))
        
        return ' '.join(words)


class PythonReExtractor:
    """Entity extraction using Python's built-in re module."""
    
    def __init__(self):
        self.patterns = {
            'MONEY': re.compile(
                r'\$[\d,]+(?:\.?\d{0,2})?(?:\s*(?:million|billion|thousand|M|B|K))?'
                r'|[\d,]+(?:\.?\d{0,2})?\s*(?:dollars?|USD|EUR|GBP|pounds?|euros?)',
                re.IGNORECASE
            ),
            'DATE': re.compile(
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)'
                r'\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}'
                r'|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
                r'|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                re.IGNORECASE
            ),
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'PHONE': re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
                r'|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
            ),
            'PERCENT': re.compile(r'\b\d{1,3}(?:\.\d{1,2})?%'),
            'TIME': re.compile(
                r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?\b'
                r'|\b\d{1,2}\s*(?:AM|PM|am|pm)\b',
                re.IGNORECASE
            ),
            'URL': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            'VERSION': re.compile(r'\bv?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?'),
            'MEASUREMENT': re.compile(
                r'\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)',
                re.IGNORECASE
            ),
            'RANGE': re.compile(r'\b\d+\s*-\s*\d+\b|\b\d+\s*to\s*\d+\b', re.IGNORECASE),
            'REGULATION': re.compile(r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?(?:\([a-z]\))?', re.IGNORECASE),
        }
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using Python re."""
        results = {}
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                results[entity_type] = matches
        return results


class HyperscanExtractor:
    """Entity extraction using Intel Hyperscan."""
    
    def __init__(self):
        if not HYPERSCAN_AVAILABLE:
            raise ImportError("Hyperscan not available")
            
        # Pattern definitions for Hyperscan
        patterns = [
            b'\\$[\\d,]+(?:\\.?\\d{0,2})?',  # MONEY
            b'\\b\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}',  # DATE
            b'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}',  # EMAIL
            b'\\(?[0-9]{3}\\)?[-\\.\\s]?[0-9]{3}[-\\.\\s]?[0-9]{4}',  # PHONE
            b'\\d{1,3}(?:\\.\\d{1,2})?%',  # PERCENT
            b'\\d{1,2}:\\d{2}(?::\\d{2})?',  # TIME
            b'https?://[^\\s<>"{}|\\\\^`\\[\\]]+',  # URL
            b'v?\\d+\\.\\d+(?:\\.\\d+)?',  # VERSION
            b'\\d+(?:\\.\\d+)?\\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm)',  # MEASUREMENT
            b'\\d+\\s*-\\s*\\d+',  # RANGE
            b'\\d{1,2}\\s*CFR\\s*\\d{3,4}(?:\\.\\d+)?',  # REGULATION
        ]
        
        self.entity_names = [
            'MONEY', 'DATE', 'EMAIL', 'PHONE', 'PERCENT', 
            'TIME', 'URL', 'VERSION', 'MEASUREMENT', 'RANGE', 'REGULATION'
        ]
        
        # Compile database
        self.db = hyperscan.Database()
        ids = list(range(len(patterns)))
        self.db.compile(
            expressions=patterns, 
            ids=ids
        )
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using Hyperscan."""
        results = {name: [] for name in self.entity_names}
        
        def on_match(id: int, start: int, end: int, flags: int, context=None):
            entity_name = self.entity_names[id]
            match_text = text[start:end]
            results[entity_name].append(match_text)
        
        self.db.scan(text.encode('utf-8'), match_event_handler=on_match)
        
        # Remove empty results
        return {k: v for k, v in results.items() if v}


class FLPCExtractor:
    """Entity extraction using FLPC (Rust-backed)."""
    
    def __init__(self):
        if not FLPC_AVAILABLE:
            raise ImportError("FLPC not available")
            
        # FLPC uses standard patterns - mirrors re module API
        self.patterns = {
            'MONEY': flpc.compile(
                r'(?i)\$[\d,]+(?:\.?\d{0,2})?(?:\s*(?:million|billion|thousand|M|B|K))?'
                r'|[\d,]+(?:\.?\d{0,2})?\s*(?:dollars?|USD|EUR|GBP|pounds?|euros?)'
            ),
            'DATE': flpc.compile(
                r'(?i)\b(?:January|February|March|April|May|June|July|August|September|October|November|December)'
                r'\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}'
                r'|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
                r'|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}'
            ),
            'EMAIL': flpc.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'PHONE': flpc.compile(
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
                r'|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
            ),
            'PERCENT': flpc.compile(r'\b\d{1,3}(?:\.\d{1,2})?%'),
            'TIME': flpc.compile(
                r'(?i)\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?\b'
                r'|\b\d{1,2}\s*(?:AM|PM|am|pm)\b'
            ),
            'URL': flpc.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            'VERSION': flpc.compile(r'\bv?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?'),
            'MEASUREMENT': flpc.compile(
                r'(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)'
            ),
            'RANGE': flpc.compile(r'(?i)\b\d+\s*-\s*\d+\b|\b\d+\s*to\s*\d+\b'),
            'REGULATION': flpc.compile(r'(?i)\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?(?:\([a-z]\))?'),
        }
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using FLPC."""
        results = {}
        for entity_type, pattern in self.patterns.items():
            try:
                # Try different FLPC methods
                if hasattr(pattern, 'findall'):
                    matches = pattern.findall(text)
                elif hasattr(pattern, 'find_all'):
                    matches = pattern.find_all(text)
                elif hasattr(pattern, 'scan'):
                    matches = pattern.scan(text)
                else:
                    # Use flpc module-level functions
                    matches = flpc.findall(pattern, text)
                
                if matches:
                    results[entity_type] = matches
            except Exception as e:
                print(f"   FLPC error for {entity_type}: {e}")
                continue
        return results


def benchmark_extractor(extractor, test_data: List[str], name: str) -> Dict:
    """Benchmark an entity extractor."""
    print(f"\n🧪 Testing {name}...")
    
    times = []
    total_entities = 0
    
    for i, text in enumerate(test_data):
        start_time = time.time()
        results = extractor.extract(text)
        end_time = time.time()
        
        extract_time = end_time - start_time
        times.append(extract_time)
        
        entities_found = sum(len(entities) for entities in results.values())
        total_entities += entities_found
        
        if i < 3:  # Show details for first few tests
            print(f"   Test {i+1}: {extract_time*1000:.2f}ms, {entities_found} entities, {len(text)} chars")
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    
    total_chars = sum(len(text) for text in test_data)
    chars_per_sec = total_chars / sum(times)
    
    return {
        'name': name,
        'avg_time_ms': avg_time * 1000,
        'median_time_ms': median_time * 1000,
        'min_time_ms': min_time * 1000,
        'max_time_ms': max_time * 1000,
        'total_entities': total_entities,
        'chars_per_sec': chars_per_sec,
        'times': times
    }


def main():
    """Run the regex performance comparison."""
    print("🚀 Regex Performance Comparison Test")
    print("=" * 50)
    
    # Generate test data
    print("📝 Generating test data...")
    generator = TestDataGenerator()
    
    test_cases = [
        (5, 0.05, "Small, sparse"),     # 5KB, 5% entities
        (10, 0.1, "Medium, normal"),    # 10KB, 10% entities  
        (25, 0.15, "Large, dense"),     # 25KB, 15% entities
        (50, 0.2, "XL, very dense"),    # 50KB, 20% entities
    ]
    
    all_test_data = []
    for size_kb, density, description in test_cases:
        print(f"   {description}: {size_kb}KB, {density*100}% entity density")
        for _ in range(3):  # 3 samples per case
            text = generator.generate_text(size_kb, density)
            all_test_data.append(text)
    
    print(f"Generated {len(all_test_data)} test documents")
    
    # Test extractors
    extractors = []
    
    # Python re (baseline)
    extractors.append(('Python re (baseline)', PythonReExtractor()))
    
    # Hyperscan (if available)
    if HYPERSCAN_AVAILABLE:
        try:
            extractors.append(('Hyperscan (Intel)', HyperscanExtractor()))
        except Exception as e:
            print(f"⚠️  Could not initialize Hyperscan: {e}")
    
    # FLPC (if available)
    if FLPC_AVAILABLE:
        try:
            extractors.append(('FLPC (Rust)', FLPCExtractor()))
        except Exception as e:
            print(f"⚠️  Could not initialize FLPC: {e}")
    
    # Run benchmarks
    results = []
    for name, extractor in extractors:
        try:
            result = benchmark_extractor(extractor, all_test_data, name)
            results.append(result)
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")
    
    # Print results
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE RESULTS")
    print("=" * 80)
    
    if results:
        baseline = results[0]  # Python re
        
        print(f"{'Engine':<20} {'Avg Time':<12} {'Entities':<10} {'Chars/sec':<15} {'Speedup':<10}")
        print("-" * 80)
        
        for result in results:
            speedup = baseline['avg_time_ms'] / result['avg_time_ms']
            print(f"{result['name']:<20} "
                  f"{result['avg_time_ms']:.2f}ms{'':<6} "
                  f"{result['total_entities']:<10} "
                  f"{result['chars_per_sec']:,.0f}{'':<6} "
                  f"{speedup:.1f}x")
        
        print("\n📈 RECOMMENDATIONS:")
        if len(results) > 1:
            best = min(results[1:], key=lambda x: x['avg_time_ms'])
            improvement = baseline['avg_time_ms'] / best['avg_time_ms']
            print(f"🏆 Best performer: {best['name']}")
            print(f"⚡ Performance improvement: {improvement:.1f}x faster than Python re")
            print(f"🎯 In your pipeline: Could improve from 213 pages/sec to ~{213 * improvement:.0f} pages/sec")
        else:
            print("⚠️  No alternative regex engines available for comparison")
            print("   Install with: pip install hyperscan flpc")


if __name__ == "__main__":
    main()