#!/usr/bin/env python3
"""
Analyze High-Performance NLP Extraction Results
Compare what we're getting vs what we need for universal entity classification

Shows actual extracted entities and compares to spaCy's universal categories:
PERSON, ORG, GPE, MONEY, DATE, CARDINAL, QUANTITY
"""

import os
import glob
import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter

try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class EntityExtractionAnalyzer:
    """Analyze and compare entity extraction results"""
    
    def __init__(self, test_docs_dir: str = "../output/pipeline/1-markdown"):
        self.test_docs_dir = test_docs_dir
        
        # Our current dictionary-based entities
        self.osha_standards = [
            "CFR 1926.95", "OSHA 3162", "ISO 9001", "ANSI Z87.1", "CFR 1910.132",
            "OSHA 3162-01R", "ANSI Z359.1", "CFR 1926.502", "OSHA 1926.451",
            "ISO 45001", "NFPA 70E", "CFR 1910.147", "OSHA 3071", "ANSI B11.0"
        ]
        
        self.organizations = [
            "Occupational Safety and Health Administration", "Department of Labor",
            "OSHA", "EPA", "CDC", "NIOSH", "Bureau of Labor Statistics",
            "National Institute for Occupational Safety and Health",
            "Environmental Protection Agency", "Centers for Disease Control"
        ]
        
        self.chemicals = [
            "asbestos", "benzene", "lead", "silica", "formaldehyde", "toluene",
            "xylene", "methylene chloride", "vinyl chloride", "chromium"
        ]
        
        # Universal entity types we need to match
        self.target_entities = {
            'PERSON': 'Individual names',
            'ORG': 'Organizations and companies', 
            'GPE': 'Geopolitical entities (places)',
            'MONEY': 'Monetary values',
            'DATE': 'Date and time references',
            'CARDINAL': 'Numbers and quantities',
            'QUANTITY': 'Measurements with units'
        }

    def get_sample_documents(self, limit: int = 5) -> List[Tuple[str, str]]:
        """Get a sample of test documents for analysis"""
        docs = []
        doc_pattern = os.path.join(self.test_docs_dir, "*.md")
        
        for file_path in sorted(glob.glob(doc_pattern))[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    docs.append((filename, content))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return docs

    def extract_with_pyahocorasick(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Extract entities using pyahocorasick and show actual results"""
        if not AHOCORASICK_AVAILABLE:
            return {"error": "pyahocorasick not available"}
        
        # Build automaton
        automaton = ahocorasick.Automaton()
        
        entities = []
        entities.extend([(term, 'OSHA_STANDARD') for term in self.osha_standards])
        entities.extend([(term, 'ORGANIZATION') for term in self.organizations])
        entities.extend([(term, 'CHEMICAL') for term in self.chemicals])
        
        for term, entity_type in entities:
            automaton.add_word(term, (entity_type, term))
        
        automaton.make_automaton()
        
        # Extract entities from documents
        results = {}
        for filename, content in documents:
            matches = []
            for end_index, (entity_type, term) in automaton.iter(content):
                start_index = end_index - len(term) + 1
                context_start = max(0, start_index - 50)
                context_end = min(len(content), end_index + 50)
                context = content[context_start:context_end]
                
                matches.append({
                    'term': term,
                    'type': entity_type,
                    'start': start_index,
                    'end': end_index + 1,
                    'context': context.replace('\n', ' ').strip()
                })
            
            results[filename] = matches
        
        return results

    def extract_with_spacy(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Extract entities using spaCy for comparison"""
        if not SPACY_AVAILABLE:
            return {"error": "spaCy not available"}
        
        try:
            # Load spaCy model (NER only for speed)
            nlp = spacy.load("en_core_web_sm")
            nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            
            results = {}
            for filename, content in documents:
                # Process only first 10000 chars for speed in this analysis
                sample_content = content[:10000] if len(content) > 10000 else content
                doc = nlp(sample_content)
                
                entities = []
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG', 'GPE', 'MONEY', 'DATE', 'CARDINAL', 'QUANTITY']:
                        context_start = max(0, ent.start_char - 50)
                        context_end = min(len(sample_content), ent.end_char + 50)
                        context = sample_content[context_start:context_end]
                        
                        entities.append({
                            'term': ent.text,
                            'type': ent.label_,
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'context': context.replace('\n', ' ').strip()
                        })
                
                results[filename] = entities
            
            return results
            
        except Exception as e:
            return {"error": f"spaCy extraction failed: {str(e)}"}

    def analyze_entity_coverage(self, pyahocorasick_results: Dict, spacy_results: Dict) -> Dict[str, Any]:
        """Analyze what entity types we're missing with pyahocorasick vs spaCy"""
        
        # Count entity types from both approaches
        pyaho_types = defaultdict(int)
        spacy_types = defaultdict(int)
        
        for filename, entities in pyahocorasick_results.items():
            for entity in entities:
                pyaho_types[entity['type']] += 1
        
        for filename, entities in spacy_results.items():
            for entity in entities:
                spacy_types[entity['type']] += 1
        
        # Find unique entities that only spaCy catches
        spacy_only_entities = []
        for filename, entities in spacy_results.items():
            for entity in entities:
                if entity['type'] in ['PERSON', 'GPE', 'MONEY', 'DATE', 'CARDINAL']:
                    spacy_only_entities.append({
                        'file': filename,
                        'term': entity['term'],
                        'type': entity['type'],
                        'context': entity['context']
                    })
        
        return {
            'pyahocorasick_types': dict(pyaho_types),
            'spacy_types': dict(spacy_types),
            'missing_universal_types': {
                'PERSON': spacy_types.get('PERSON', 0),
                'GPE': spacy_types.get('GPE', 0), 
                'MONEY': spacy_types.get('MONEY', 0),
                'DATE': spacy_types.get('DATE', 0),
                'CARDINAL': spacy_types.get('CARDINAL', 0)
            },
            'spacy_unique_samples': spacy_only_entities[:20]  # Sample of what we're missing
        }

    def show_entity_examples(self, results: Dict[str, Any], title: str, max_per_type: int = 5):
        """Display entity extraction examples"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        if "error" in results:
            print(f"❌ {results['error']}")
            return
        
        # Group by entity type
        by_type = defaultdict(list)
        for filename, entities in results.items():
            for entity in entities:
                by_type[entity['type']].append({
                    'file': filename,
                    'term': entity['term'],
                    'context': entity['context']
                })
        
        for entity_type, entities in by_type.items():
            print(f"\n🏷️  {entity_type} ({len(entities)} found)")
            print("-" * 40)
            
            for i, entity in enumerate(entities[:max_per_type]):
                print(f"{i+1}. \"{entity['term']}\"")
                print(f"   📄 {entity['file']}")
                print(f"   💬 ...{entity['context']}...")
                print()
            
            if len(entities) > max_per_type:
                print(f"   ... and {len(entities) - max_per_type} more\n")

    def run_analysis(self):
        """Run complete entity extraction analysis"""
        print("Entity Extraction Analysis")
        print("=" * 60)
        print("Comparing pyahocorasick (fast) vs spaCy (universal) entity extraction")
        print()
        
        # Get sample documents
        documents = self.get_sample_documents(5)
        if not documents:
            print("❌ No test documents found")
            return
        
        print(f"📊 Analyzing {len(documents)} sample documents:")
        for filename, content in documents:
            char_count = len(content)
            word_count = len(content.split())
            print(f"  • {filename}: {char_count:,} chars, {word_count:,} words")
        print()
        
        # Extract with both approaches
        print("🔍 Extracting entities with pyahocorasick...")
        pyaho_results = self.extract_with_pyahocorasick(documents)
        
        print("🔍 Extracting entities with spaCy for comparison...")
        spacy_results = self.extract_with_spacy(documents)
        
        # Show results
        self.show_entity_examples(pyaho_results, "PYAHOCORASICK RESULTS (Current Approach)")
        self.show_entity_examples(spacy_results, "SPACY RESULTS (Universal Entities)")
        
        # Analyze coverage gaps
        if "error" not in pyaho_results and "error" not in spacy_results:
            coverage = self.analyze_entity_coverage(pyaho_results, spacy_results)
            
            print(f"\n{'='*60}")
            print("COVERAGE ANALYSIS")
            print(f"{'='*60}")
            
            print("\n📈 Entity Type Counts:")
            print(f"pyahocorasick: {coverage['pyahocorasick_types']}")
            print(f"spaCy:         {coverage['spacy_types']}")
            
            print(f"\n❗ MISSING UNIVERSAL ENTITY TYPES:")
            missing = coverage['missing_universal_types']
            for entity_type, count in missing.items():
                if count > 0:
                    print(f"  • {entity_type}: {count} entities (spaCy finds these, we don't)")
            
            print(f"\n📋 SAMPLE OF ENTITIES WE'RE MISSING:")
            for i, entity in enumerate(coverage['spacy_unique_samples'][:10]):
                print(f"{i+1}. {entity['type']}: \"{entity['term']}\"")
                print(f"   📄 {entity['file']}")
                print(f"   💬 ...{entity['context']}...")
                print()
        
        print("\n" + "="*60)
        print("CONCLUSION")
        print("="*60)
        print("pyahocorasick is FAST (1816 pages/sec) but LIMITED to our dictionaries.")
        print("spaCy is SLOW (15.5 pages/sec) but finds UNIVERSAL entity types.")
        print("\nTo get the best of both worlds, we need a HYBRID approach:")
        print("1. pyahocorasick for domain-specific entities (OSHA, chemicals)")
        print("2. Additional patterns/rules for PERSON, GPE, MONEY, DATE, CARDINAL")


def main():
    """Run entity extraction analysis"""
    analyzer = EntityExtractionAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()