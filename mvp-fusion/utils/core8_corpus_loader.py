#!/usr/bin/env python3
"""
Core-8 Entity Corpus Loader
============================
Loads all corpus files organized by the Core-8 entity categories.
Includes subfolder support for GPE and LOC.
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import ahocorasick


class Core8CorpusLoader:
    """Loads corpus files organized by Core-8 entity categories"""
    
    # Core-8 entity categories with their corpus file mappings
    CORE8_MAPPINGS = {
        'PERSON': {
            'files': [
                'first_names_2025_09_18.txt',
                'last_names_2025_09_18.txt'
            ],
            'subfolders': []
        },
        'ORG': {
            'files': [
                'organizations_2025_09_18.txt',
                'unicorn_companies_2025_09_18.txt',
                'investors_2025_09_18.txt'
            ],
            'subfolders': []
        },
        'GPE': {
            'files': [
                'geopolitical_entities_2025_09_18.txt'
            ],
            'subfolders': ['gpe']  # Load all files from gpe subfolder
        },
        'LOC': {
            'files': [],
            'subfolders': ['loc']  # Load all files from loc subfolder
        },
        'DATE': {
            'files': [],  # Handled by patterns, not corpus
            'subfolders': []
        },
        'TIME': {
            'files': [],  # Handled by patterns, not corpus
            'subfolders': []
        },
        'MONEY': {
            'files': [],  # Handled by patterns, not corpus
            'subfolders': []
        },
        'MEASUREMENT': {
            'files': [],  # Handled by patterns, not corpus
            'subfolders': []
        }
    }
    
    def __init__(self, corpus_dir: Path = None, verbose: bool = False):
        """Initialize the Core-8 corpus loader
        
        Args:
            corpus_dir: Path to corpus directory
            verbose: If True, show detailed file loading. If False, show only summary.
        """
        if corpus_dir is None:
            corpus_dir = Path("/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data")
        
        self.corpus_dir = corpus_dir
        self.verbose = verbose
        self.automatons: Dict[str, ahocorasick.Automaton] = {}
        self.corpus_data: Dict[str, Set[str]] = {}
        self.subcategory_data: Dict[str, Dict[str, Set[str]]] = {}  # Track subcategories
        self.load_stats: Dict[str, Dict] = {}
        
        # Initialize all Core-8 automatons
        self._initialize_core8_automatons()
    
    def _load_corpus_file(self, file_path: Path) -> Set[str]:
        """Load a single corpus file"""
        data = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip comments
                        data.add(line.lower())
        except Exception as e:
            print(f"      ⚠️  Error loading {file_path.name}: {e}")
        
        return data
    
    def _load_subfolder(self, subfolder: str) -> Dict[str, Set[str]]:
        """Load all .txt files from a subfolder with subcategory tracking"""
        data_by_subcategory = {}
        subfolder_path = self.corpus_dir / subfolder
        
        if subfolder_path.exists() and subfolder_path.is_dir():
            for txt_file in subfolder_path.glob("*.txt"):
                if txt_file.name != "README.md":
                    file_data = self._load_corpus_file(txt_file)
                    if len(file_data) > 0:
                        # Extract subcategory from filename (remove date suffix and .txt)
                        subcategory = txt_file.stem.split('_2025_')[0]  
                        data_by_subcategory[subcategory] = file_data
                        if self.verbose:
                            print(f"      📄 {txt_file.name:<40} {len(file_data):>7,} patterns")
        
        return data_by_subcategory
    
    def get_subcategory(self, entity_type: str, entity_text: str) -> Optional[str]:
        """Get the subcategory for a specific entity"""
        if entity_type in self.subcategory_data:
            entity_lower = entity_text.lower()
            for subcategory, entities in self.subcategory_data[entity_type].items():
                if entity_lower in entities:
                    return subcategory
        return None
    
    def _initialize_core8_automatons(self):
        """Initialize all Core-8 entity automatons"""
        total_start = time.perf_counter()
        
        if self.verbose:
            print("\n🎯 CORE-8 ENTITY CORPUS INITIALIZATION")
            print("=" * 70)
        
        total_patterns = 0
        total_files = 0
        
        for entity_type, mapping in self.CORE8_MAPPINGS.items():
            entity_start = time.perf_counter()
            entity_data = set()
            entity_files = 0
            
            if self.verbose:
                print(f"\n📊 {entity_type} Entity:")
                print("-" * 60)
            
            # Load direct files
            for filename in mapping['files']:
                file_path = self.corpus_dir / filename
                if file_path.exists():
                    file_data = self._load_corpus_file(file_path)
                    entity_data.update(file_data)
                    entity_files += 1
                    if self.verbose:
                        print(f"   📄 {filename:<40} {len(file_data):>7,} patterns")
            
            # Load subfolders with subcategory tracking
            for subfolder in mapping['subfolders']:
                subfolder_path = self.corpus_dir / subfolder
                if subfolder_path.exists():
                    if self.verbose:
                        print(f"   📂 Loading {subfolder}/ subfolder:")
                    subfolder_data_by_category = self._load_subfolder(subfolder)
                    
                    # Store subcategory data for metadata
                    if entity_type not in self.subcategory_data:
                        self.subcategory_data[entity_type] = {}
                    self.subcategory_data[entity_type].update(subfolder_data_by_category)
                    
                    # Combine all subcategory data for the main automaton
                    for subcategory, subcat_data in subfolder_data_by_category.items():
                        entity_data.update(subcat_data)
                    
                    entity_files += len(list(subfolder_path.glob("*.txt")))
                    total_subfolder_patterns = sum(len(data) for data in subfolder_data_by_category.values())
                    if self.verbose:
                        print(f"      └─ Total from {subfolder}/: {total_subfolder_patterns:,} patterns")
            
            # Build automaton if we have data
            if len(entity_data) > 0:
                automaton_start = time.perf_counter()
                automaton = ahocorasick.Automaton()
                
                for pattern in entity_data:
                    automaton.add_word(pattern, (entity_type, pattern))
                
                automaton.make_automaton()
                build_time = (time.perf_counter() - automaton_start) * 1000
                
                self.automatons[entity_type] = automaton
                self.corpus_data[entity_type] = entity_data
                
                entity_time = (time.perf_counter() - entity_start) * 1000
                total_patterns += len(entity_data)
                total_files += entity_files
                
                self.load_stats[entity_type] = {
                    'patterns': len(entity_data),
                    'files': entity_files,
                    'build_time_ms': build_time,
                    'total_time_ms': entity_time
                }
                
                if self.verbose:
                    print(f"   ✅ Total: {len(entity_data):,} unique patterns loaded")
            else:
                if self.verbose:
                    if entity_type not in ['DATE', 'TIME', 'MONEY', 'MEASUREMENT']:
                        print(f"   ⚠️  No corpus data loaded")
                    else:
                        print(f"   ℹ️  Pattern-based entity (no corpus needed)")
        
        # Total initialization time
        total_time = (time.perf_counter() - total_start) * 1000
        
        # Always show the summary (this is the only output in non-verbose mode)
        print("\n" + "=" * 70)
        print("📈 CORE-8 INITIALIZATION SUMMARY")
        print("-" * 70)
        print(f"{'Entity':<15} {'Patterns':<15} {'Engine':<25}")
        print("-" * 70)
        
        for entity_type in self.CORE8_MAPPINGS.keys():
            if entity_type in self.load_stats:
                stats = self.load_stats[entity_type]
                print(f"{entity_type:<15} {stats['patterns']:>14,} {'Aho-Corasick ✅':<25}")
            else:
                if entity_type in ['DATE', 'TIME', 'MONEY', 'MEASUREMENT']:
                    print(f"{entity_type:<15} {'FLPC Compiled':>14} {'FLPC Engine ✅':<25}")
                else:
                    print(f"{entity_type:<15} {0:>14} {'Not Loaded ⚠️':<25}")
        
        print("-" * 70)
        print(f"{'TOTAL':<15} {total_patterns:>14,} {f'{total_time:.1f}ms':<25}")
        print("=" * 70)
    
    def search(self, text: str, entity_type: str = None) -> Dict[str, List[Dict]]:
        """
        Search for patterns in text using Core-8 automatons
        
        Args:
            text: Text to search in
            entity_type: Specific entity type to search for (None = all)
        
        Returns:
            Dictionary of entity_type -> list of matches
        """
        results = {}
        
        # Determine which automatons to use
        if entity_type and entity_type in self.automatons:
            search_automatons = {entity_type: self.automatons[entity_type]}
        else:
            search_automatons = self.automatons
        
        # Search with each automaton
        for ent_type, automaton in search_automatons.items():
            matches = []
            
            for end_pos, (match_type, match_text) in automaton.iter(text.lower()):
                start_pos = end_pos - len(match_text) + 1
                matches.append({
                    'text': text[start_pos:end_pos + 1],  # Original case
                    'type': match_type,
                    'start': start_pos,
                    'end': end_pos + 1,
                    'canonical': match_text
                })
            
            if matches:
                results[ent_type] = matches
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about loaded corpus"""
        return {
            'corpus_directory': str(self.corpus_dir),
            'total_automatons': len(self.automatons),
            'total_patterns': sum(len(data) for data in self.corpus_data.values()),
            'entity_types': list(self.automatons.keys()),
            'load_statistics': self.load_stats,
            'corpus_sizes': {
                name: len(data) for name, data in self.corpus_data.items()
            }
        }


def test_core8_loader():
    """Test the Core-8 corpus loader"""
    print("🚀 Testing Core-8 Entity Corpus Loader")
    print("=" * 70)
    
    # Initialize the loader (this will load all corpus files)
    loader = Core8CorpusLoader()
    
    # Test searching
    test_text = "John Smith from Microsoft visited the Grand Canyon in Arizona last January."
    
    print("\n🔍 Testing Entity Search:")
    print(f"Text: \"{test_text}\"")
    print()
    
    # Search for all entities
    all_results = loader.search(test_text)
    
    for entity_type, matches in all_results.items():
        print(f"\n{entity_type} matches: {len(matches)}")
        # Show first 5 matches for each type
        for match in matches[:5]:
            print(f"   - \"{match['text']}\" at {match['start']}-{match['end']}")
        if len(matches) > 5:
            print(f"   ... and {len(matches) - 5} more")
    
    print("\n✅ Core-8 loader test complete!")


if __name__ == "__main__":
    test_core8_loader()