#!/usr/bin/env python3
"""
Test pyahocorasick capabilities beyond simple dictionary lookup
Explore regex support, pattern matching, and extraction features
"""

import ahocorasick
import re
import time
import glob
import os

class PyAhoCorasickCapabilityTest:
    """Test advanced pyahocorasick features for entity extraction"""
    
    def __init__(self):
        self.test_text = """
        John Smith works at OSHA. Contact him at john.smith@dol.gov or (202) 693-1999.
        The regulation CFR 1926.95 requires $50,000 in safety equipment by March 15, 2024.
        Mary Johnson from EPA in Washington, DC reported 25 violations costing $1.2 million.
        Dr. Williams at CDC found 300 workers exposed to asbestos on January 1st, 2023.
        """

    def test_basic_dictionary_lookup(self):
        """Test basic dictionary functionality"""
        print("1. BASIC DICTIONARY LOOKUP")
        print("-" * 40)
        
        automaton = ahocorasick.Automaton()
        
        # Add terms
        terms = ["OSHA", "EPA", "CDC", "John Smith", "Mary Johnson", "Dr. Williams"]
        for term in terms:
            automaton.add_word(term, term)
        
        automaton.make_automaton()
        
        matches = []
        for end_index, term in automaton.iter(self.test_text):
            start_index = end_index - len(term) + 1
            matches.append((term, start_index, end_index + 1))
        
        print(f"Found {len(matches)} matches:")
        for term, start, end in matches:
            print(f"  • '{term}' at position {start}-{end}")
        print()

    def test_case_insensitive_matching(self):
        """Test case insensitive matching"""
        print("2. CASE INSENSITIVE MATCHING")
        print("-" * 40)
        
        automaton = ahocorasick.Automaton()
        
        # Add lowercase terms but search mixed case text
        terms = ["osha", "epa", "cdc", "washington"]
        for term in terms:
            automaton.add_word(term, term.upper())
        
        automaton.make_automaton()
        
        # Search in lowercase version of text
        matches = list(automaton.iter(self.test_text.lower()))
        
        print(f"Found {len(matches)} case-insensitive matches:")
        for end_index, term in matches:
            start_index = end_index - len(term.lower()) + 1
            original_text = self.test_text[start_index:end_index + 1]
            print(f"  • Found '{term}' as '{original_text}'")
        print()

    def test_overlapping_matches(self):
        """Test how pyahocorasick handles overlapping matches"""
        print("3. OVERLAPPING MATCHES")
        print("-" * 40)
        
        automaton = ahocorasick.Automaton()
        
        # Add overlapping terms
        terms = ["John", "John Smith", "Smith", "Dr.", "Dr. Williams", "Williams"]
        for term in terms:
            automaton.add_word(term, term)
        
        automaton.make_automaton()
        
        matches = list(automaton.iter(self.test_text))
        print(f"Found {len(matches)} matches (including overlaps):")
        for end_index, term in matches:
            start_index = end_index - len(term) + 1
            print(f"  • '{term}' at position {start_index}-{end_index + 1}")
        print()

    def test_pattern_simulation(self):
        """Test simulating regex patterns with multiple dictionary entries"""
        print("4. PATTERN SIMULATION (Email-like)")
        print("-" * 40)
        
        automaton = ahocorasick.Automaton()
        
        # Simulate email patterns by adding common email domains
        email_domains = [
            "@dol.gov", "@osha.gov", "@epa.gov", "@cdc.gov", "@hhs.gov",
            "@gmail.com", "@outlook.com", "@company.com"
        ]
        
        for domain in email_domains:
            automaton.add_word(domain, f"EMAIL_DOMAIN{domain}")
        
        automaton.make_automaton()
        
        matches = list(automaton.iter(self.test_text))
        print(f"Found {len(matches)} potential email domains:")
        for end_index, term in matches:
            start_index = end_index - len(term.replace("EMAIL_DOMAIN", "")) + 1
            # Look backwards for potential email prefix
            context_start = max(0, start_index - 20)
            context = self.test_text[context_start:end_index + 1]
            print(f"  • {term}: ...{context}")
        print()

    def test_regex_comparison(self):
        """Compare pyahocorasick vs regex for pattern matching"""
        print("5. REGEX VS PYAHOCORASICK COMPARISON")
        print("-" * 40)
        
        # Test documents
        doc_pattern = "../output/pipeline/1-markdown/*.md"
        test_files = glob.glob(doc_pattern)[:5]
        
        if not test_files:
            print("No test files found")
            return
        
        # Load test content
        all_content = ""
        for file_path in test_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"
        
        print(f"Testing on {len(all_content)} characters from {len(test_files)} files")
        
        # Regex approach for money patterns
        money_regex = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?'
        
        start_time = time.time()
        regex_matches = re.findall(money_regex, all_content, re.IGNORECASE)
        regex_time = time.time() - start_time
        
        # pyahocorasick approach (simulating money with common patterns)
        automaton = ahocorasick.Automaton()
        money_patterns = [
            "$1", "$5", "$10", "$25", "$50", "$100", "$500", "$1,000", "$5,000", 
            "$10,000", "$50,000", "$100,000", "$500,000", "$1,000,000",
            "million", "billion", "thousand"
        ]
        
        for pattern in money_patterns:
            automaton.add_word(pattern, f"MONEY:{pattern}")
        
        automaton.make_automaton()
        
        start_time = time.time()
        aho_matches = list(automaton.iter(all_content))
        aho_time = time.time() - start_time
        
        print(f"\nMONEY PATTERN EXTRACTION:")
        print(f"  Regex: {len(regex_matches)} matches in {regex_time:.4f}s")
        print(f"  pyahocorasick: {len(aho_matches)} matches in {aho_time:.4f}s")
        print(f"  Speed ratio: {regex_time/aho_time:.1f}x faster" if aho_time > 0 else "")
        
        print(f"\nSample regex matches:")
        for match in regex_matches[:5]:
            print(f"    • {match}")
        
        print(f"\nSample pyahocorasick matches:")
        for end_index, term in aho_matches[:5]:
            start_index = end_index - len(term.replace("MONEY:", "")) + 1
            context_start = max(0, start_index - 10)
            context_end = min(len(all_content), end_index + 10)
            context = all_content[context_start:context_end].replace('\n', ' ')
            print(f"    • {term}: ...{context}...")
        print()

    def test_extraction_with_context(self):
        """Test extracting entities with surrounding context"""
        print("6. CONTEXT-AWARE EXTRACTION")
        print("-" * 40)
        
        automaton = ahocorasick.Automaton()
        
        # Add entities we want to extract
        entities = {
            "OSHA": "ORGANIZATION",
            "EPA": "ORGANIZATION", 
            "CDC": "ORGANIZATION",
            "CFR 1926.95": "REGULATION",
            "March 15, 2024": "DATE",
            "January 1st, 2023": "DATE"
        }
        
        for term, entity_type in entities.items():
            automaton.add_word(term, (entity_type, term))
        
        automaton.make_automaton()
        
        extractions = []
        for end_index, (entity_type, term) in automaton.iter(self.test_text):
            start_index = end_index - len(term) + 1
            
            # Extract surrounding context
            context_start = max(0, start_index - 30)
            context_end = min(len(self.test_text), end_index + 30)
            context = self.test_text[context_start:context_end].strip().replace('\n', ' ')
            
            extractions.append({
                'entity': term,
                'type': entity_type,
                'position': (start_index, end_index + 1),
                'context': context
            })
        
        print(f"Extracted {len(extractions)} entities with context:")
        for extraction in extractions:
            print(f"  • {extraction['type']}: '{extraction['entity']}'")
            print(f"    Context: ...{extraction['context']}...")
            print()

    def run_all_tests(self):
        """Run all capability tests"""
        print("PYAHOCORASICK CAPABILITY ANALYSIS")
        print("=" * 60)
        print("Testing advanced features beyond basic dictionary lookup")
        print()
        
        self.test_basic_dictionary_lookup()
        self.test_case_insensitive_matching()
        self.test_overlapping_matches()
        self.test_pattern_simulation()
        self.test_regex_comparison()
        self.test_extraction_with_context()
        
        print("=" * 60)
        print("CONCLUSION:")
        print("pyahocorasick is NOT a regex engine, but it can:")
        print("• Very fast exact string matching (faster than grep)")
        print("• Handle thousands of search terms simultaneously")  
        print("• Case-insensitive matching")
        print("• Extract context around matches")
        print("• Simulate simple patterns with multiple dictionary entries")
        print()
        print("LIMITATIONS:")
        print("• No true regex support")
        print("• Cannot recognize new patterns (only predefined strings)")
        print("• Cannot extract dynamic content like 'any date' or 'any money amount'")
        print()
        print("BEST USE CASE:")
        print("• Known entity dictionaries (organizations, standards, chemicals)")
        print("• Combined with regex for dynamic patterns (dates, money, phone numbers)")


def main():
    """Run pyahocorasick capability tests"""
    tester = PyAhoCorasickCapabilityTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()