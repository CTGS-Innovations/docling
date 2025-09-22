#!/usr/bin/env python3
"""
Comprehensive Aho-Corasick Corpus Loader
========================================
Loads all corpus files into Aho-Corasick automatons with detailed tracking
of initialization times, file sizes, and pattern counts.
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import ahocorasick


class ComprehensiveAhoCorasickLoader:
    """Loads and tracks all corpus files for Aho-Corasick pattern matching"""
    
    def __init__(self, corpus_dir: Path = None):
        """Initialize the comprehensive loader with corpus directory"""
        if corpus_dir is None:
            corpus_dir = Path("/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data")
        
        self.corpus_dir = corpus_dir
        self.automatons: Dict[str, ahocorasick.Automaton] = {}
        self.corpus_data: Dict[str, Set[str]] = {}
        self.load_times: Dict[str, float] = {}
        self.file_stats: Dict[str, Dict] = {}
        
        # Initialize all automatons
        self._initialize_all_automatons()
    
    def _load_corpus_file(self, file_path: Path) -> Tuple[Set[str], float]:
        """Load a single corpus file and return the data with timing"""
        start_time = time.perf_counter()
        
        data = set()
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data.add(line.lower())  # Normalize to lowercase
                        line_count += 1
        except Exception as e:
            print(f"   ⚠️  Error loading {file_path.name}: {e}")
            return data, 0.0
        
        load_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Store file statistics
        self.file_stats[file_path.name] = {
            'path': str(file_path),
            'size_bytes': file_path.stat().st_size,
            'size_mb': file_path.stat().st_size / (1024 * 1024),
            'line_count': line_count,
            'unique_entries': len(data),
            'load_time_ms': load_time
        }
        
        return data, load_time
    
    def _build_automaton(self, corpus_name: str, data: Set[str]) -> Tuple[ahocorasick.Automaton, float]:
        """Build an Aho-Corasick automaton from corpus data"""
        start_time = time.perf_counter()
        
        automaton = ahocorasick.Automaton()
        
        # Add all words to automaton with their type
        for word in data:
            automaton.add_word(word, (corpus_name, word))
        
        # Build the automaton (creates the trie structure)
        automaton.make_automaton()
        
        build_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        return automaton, build_time
    
    def _initialize_all_automatons(self):
        """Initialize all corpus files into Aho-Corasick automatons"""
        total_start = time.perf_counter()
        
        print("🔄 COMPREHENSIVE AHO-CORASICK INITIALIZATION")
        print("=" * 60)
        
        # Define corpus files to load with their categories
        corpus_files = {
            'person_first_names': 'first_names_2025_09_18.txt',
            'person_last_names': 'last_names_2025_09_18.txt',
            'organizations': 'organizations_2025_09_18.txt',
            'geopolitical': 'geopolitical_entities_2025_09_18.txt',
            'investors': 'investors_2025_09_18.txt',
            'unicorn_companies': 'unicorn_companies_2025_09_18.txt'
        }
        
        # Track overall stats
        total_patterns = 0
        total_load_time = 0
        total_build_time = 0
        
        for corpus_name, filename in corpus_files.items():
            file_path = self.corpus_dir / filename
            
            if not file_path.exists():
                print(f"⚠️  {corpus_name:20} - File not found: {filename}")
                continue
            
            # Load corpus file
            print(f"📂 Loading {corpus_name:20} from {filename}")
            data, load_time = self._load_corpus_file(file_path)
            total_load_time += load_time
            
            if len(data) == 0:
                print(f"   ⚠️  No data loaded from {filename}")
                continue
            
            # Build automaton
            print(f"   🔧 Building automaton with {len(data):,} patterns...")
            automaton, build_time = self._build_automaton(corpus_name, data)
            total_build_time += build_time
            
            # Store results
            self.corpus_data[corpus_name] = data
            self.automatons[corpus_name] = automaton
            self.load_times[corpus_name] = {
                'load_ms': load_time,
                'build_ms': build_time,
                'total_ms': load_time + build_time
            }
            
            total_patterns += len(data)
            
            # Report for this corpus
            stats = self.file_stats[filename]
            print(f"   ✅ Loaded: {stats['unique_entries']:,} unique entries from {stats['line_count']:,} lines")
            print(f"   📊 File size: {stats['size_mb']:.2f} MB")
            print(f"   ⏱️  Load: {load_time:.2f}ms | Build: {build_time:.2f}ms | Total: {load_time + build_time:.2f}ms")
            print()
        
        # Create combined automatons for related categories
        print("🔗 Building Combined Automatons:")
        print("-" * 40)
        
        # Combine person names
        if 'person_first_names' in self.corpus_data and 'person_last_names' in self.corpus_data:
            start_time = time.perf_counter()
            combined_names = self.corpus_data['person_first_names'] | self.corpus_data['person_last_names']
            
            combined_automaton = ahocorasick.Automaton()
            for name in self.corpus_data['person_first_names']:
                combined_automaton.add_word(name, ('first_name', name))
            for name in self.corpus_data['person_last_names']:
                combined_automaton.add_word(name, ('last_name', name))
            
            combined_automaton.make_automaton()
            combine_time = (time.perf_counter() - start_time) * 1000
            
            self.automatons['combined_person_names'] = combined_automaton
            print(f"   👥 Person Names: {len(combined_names):,} patterns in {combine_time:.2f}ms")
        
        # Combine organization-related
        org_patterns = 0
        if 'organizations' in self.corpus_data:
            org_patterns += len(self.corpus_data['organizations'])
        if 'unicorn_companies' in self.corpus_data:
            org_patterns += len(self.corpus_data['unicorn_companies'])
        if 'investors' in self.corpus_data:
            org_patterns += len(self.corpus_data['investors'])
        
        if org_patterns > 0:
            start_time = time.perf_counter()
            combined_org = ahocorasick.Automaton()
            
            for corpus_name in ['organizations', 'unicorn_companies', 'investors']:
                if corpus_name in self.corpus_data:
                    for org in self.corpus_data[corpus_name]:
                        combined_org.add_word(org, (corpus_name, org))
            
            combined_org.make_automaton()
            combine_time = (time.perf_counter() - start_time) * 1000
            
            self.automatons['combined_organizations'] = combined_org
            print(f"   🏢 Organizations: {org_patterns:,} patterns in {combine_time:.2f}ms")
        
        # Total initialization time
        total_time = (time.perf_counter() - total_start) * 1000
        
        print()
        print("=" * 60)
        print("🎯 INITIALIZATION COMPLETE")
        print(f"   📊 Total Patterns Loaded: {total_patterns:,}")
        print(f"   🗂️  Individual Automatons: {len(self.automatons)}")
        print(f"   ⏱️  File Loading: {total_load_time:.2f}ms")
        print(f"   ⏱️  Automaton Building: {total_build_time:.2f}ms")
        print(f"   ⏱️  Total Initialization: {total_time:.2f}ms")
        print()
        
        # Summary table
        print("📋 CORPUS SUMMARY:")
        print("-" * 60)
        print(f"{'Corpus':<25} {'Patterns':<12} {'Size (MB)':<12} {'Time (ms)':<12}")
        print("-" * 60)
        
        for corpus_name in corpus_files.keys():
            if corpus_name in self.corpus_data:
                filename = corpus_files[corpus_name]
                stats = self.file_stats.get(filename, {})
                timing = self.load_times.get(corpus_name, {})
                
                print(f"{corpus_name:<25} {len(self.corpus_data[corpus_name]):<12,} "
                      f"{stats.get('size_mb', 0):<12.2f} "
                      f"{timing.get('total_ms', 0):<12.2f}")
        
        print("-" * 60)
        print(f"{'TOTAL':<25} {total_patterns:<12,} "
              f"{sum(s.get('size_mb', 0) for s in self.file_stats.values()):<12.2f} "
              f"{total_time:<12.2f}")
        print("=" * 60)
    
    def search(self, text: str, automaton_name: str = 'combined_person_names') -> List[Dict]:
        """Search for patterns in text using specified automaton"""
        if automaton_name not in self.automatons:
            print(f"⚠️  Automaton '{automaton_name}' not found")
            return []
        
        automaton = self.automatons[automaton_name]
        matches = []
        
        for end_pos, (match_type, match_text) in automaton.iter(text.lower()):
            start_pos = end_pos - len(match_text) + 1
            matches.append({
                'text': text[start_pos:end_pos + 1],  # Original case from text
                'type': match_type,
                'start': start_pos,
                'end': end_pos + 1,
                'canonical': match_text
            })
        
        return matches
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about loaded corpus"""
        return {
            'corpus_directory': str(self.corpus_dir),
            'total_automatons': len(self.automatons),
            'total_patterns': sum(len(data) for data in self.corpus_data.values()),
            'corpus_categories': list(self.corpus_data.keys()),
            'file_statistics': self.file_stats,
            'load_times': self.load_times,
            'automaton_sizes': {
                name: len(self.corpus_data.get(name, set()))
                for name in self.corpus_data.keys()
            }
        }


def test_comprehensive_loader():
    """Test the comprehensive Aho-Corasick loader"""
    print("🚀 Testing Comprehensive Aho-Corasick Loader")
    print("=" * 60)
    
    # Initialize the loader (this will load all corpus files)
    loader = ComprehensiveAhoCorasickLoader()
    
    # Test searching
    test_text = "John Smith from Microsoft met with Sarah Johnson at Apple headquarters."
    
    print("\n🔍 Testing Pattern Search:")
    print(f"Text: \"{test_text}\"")
    print()
    
    # Test person name search
    if 'combined_person_names' in loader.automatons:
        person_matches = loader.search(test_text, 'combined_person_names')
        print(f"👥 Person name matches: {len(person_matches)}")
        for match in person_matches:
            print(f"   - \"{match['text']}\" ({match['type']}) at {match['start']}-{match['end']}")
    
    # Test organization search
    if 'combined_organizations' in loader.automatons:
        org_matches = loader.search(test_text, 'combined_organizations')
        print(f"🏢 Organization matches: {len(org_matches)}")
        for match in org_matches:
            print(f"   - \"{match['text']}\" ({match['type']}) at {match['start']}-{match['end']}")
    
    print("\n✅ Comprehensive loader test complete!")


if __name__ == "__main__":
    test_comprehensive_loader()