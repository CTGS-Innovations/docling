#!/usr/bin/env python3
"""
High-Performance NLP Benchmark Script
Tests deterministic automata libraries for 1000+ pages/sec entity extraction

Libraries tested:
- pyahocorasick: Aho-Corasick trie for dictionary lookups
- hyperscan: SIMD-optimized multi-regex engine
- marisa-trie: Memory-mapped static tries
- flashtext: Lightweight keyword extractor
- blingfire: Fast finite-state tokenizer
- ripgrep: External sidecar binary performance test

Target: 1000+ pages/sec for OSHA document entity extraction
"""

import time
import json
import psutil
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import tempfile
import re

# Import all high-performance libraries
try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False

try:
    import hyperscan
    HYPERSCAN_AVAILABLE = True
except ImportError:
    HYPERSCAN_AVAILABLE = False

try:
    import marisa_trie
    MARISA_AVAILABLE = True
except ImportError:
    MARISA_AVAILABLE = False

try:
    import flashtext
    FLASHTEXT_AVAILABLE = True
except ImportError:
    FLASHTEXT_AVAILABLE = False

try:
    import blingfire as bf
    BLINGFIRE_AVAILABLE = True
except ImportError:
    BLINGFIRE_AVAILABLE = False


class HighPerformanceNLPBenchmark:
    """Benchmark high-performance NLP alternatives for entity extraction"""
    
    def __init__(self, test_docs_dir: str = "../output/pipeline/1-markdown"):
        self.test_docs_dir = test_docs_dir
        self.results = []
        
        # OSHA-specific entity dictionaries
        self.osha_standards = [
            "CFR 1926.95", "OSHA 3162", "ISO 9001", "ANSI Z87.1", "CFR 1910.132",
            "OSHA 3162-01R", "ANSI Z359.1", "CFR 1926.502", "OSHA 1926.451",
            "ISO 45001", "NFPA 70E", "CFR 1910.147", "OSHA 3071", "ANSI B11.0",
            "CFR 1926.1053", "OSHA 3990", "ANSI A10.8", "CFR 1910.1200"
        ]
        
        self.organizations = [
            "Occupational Safety and Health Administration", "Department of Labor",
            "OSHA", "EPA", "CDC", "NIOSH", "Bureau of Labor Statistics",
            "National Institute for Occupational Safety and Health",
            "Environmental Protection Agency", "Centers for Disease Control",
            "Occupational Safety and Health Review Commission", "MSHA",
            "Mine Safety and Health Administration", "CPSC"
        ]
        
        self.chemicals = [
            "asbestos", "benzene", "lead", "silica", "formaldehyde", "toluene",
            "xylene", "methylene chloride", "vinyl chloride", "chromium",
            "cadmium", "beryllium", "arsenic", "mercury", "hexavalent chromium",
            "crystalline silica", "respirable crystalline silica"
        ]
        
        self.requirement_patterns = [
            r"\b(must|shall|required to|mandated to|obligated to)\s+\w+",
            r"\b(compliance with|conform to|accordance with)\s+[\w\s]+",
            r"\b(prohibited|forbidden|not permitted|restricted)\s+\w+",
            r"\b(ensure|provide|maintain|establish)\s+[\w\s]+",
            r"\b(training|certification|qualification)\s+required"
        ]
        
        self.measurement_patterns = [
            r"\d+\s*(percent|%|percentage)",
            r"\d+\s*(hours?|hrs?|minutes?|mins?|seconds?|secs?)",
            r"\d+\s*(days?|weeks?|months?|years?)",
            r"\$[\d,]+(?:\.\d{2})?",
            r"\d+\s*(feet|ft|inches?|in|yards?|yd)",
            r"\d+\s*(pounds?|lbs?|tons?|ounces?|oz)"
        ]
        
        self.contact_patterns = [
            r"\b[\w.-]+@[\w.-]+\.\w+\b",
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\b\d{3}-\d{3}-\d{4}\b"
        ]

    def get_test_documents(self) -> List[Tuple[str, str]]:
        """Load test documents and return (filename, content) pairs"""
        docs = []
        doc_pattern = os.path.join(self.test_docs_dir, "*.md")
        
        for file_path in glob.glob(doc_pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    docs.append((filename, content))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return docs

    def measure_performance(self, func, *args, **kwargs) -> Tuple[Any, float, float]:
        """Measure function performance and memory usage"""
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = mem_after - mem_before
        
        return result, end_time - start_time, memory_used

    def benchmark_pyahocorasick(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark pyahocorasick for dictionary-based entity extraction"""
        if not AHOCORASICK_AVAILABLE:
            return {"error": "pyahocorasick not available"}
        
        # Build Aho-Corasick automaton
        def build_automaton():
            automaton = ahocorasick.Automaton()
            
            # Add all entity dictionaries
            entities = []
            entities.extend([(term, 'OSHA_STANDARD') for term in self.osha_standards])
            entities.extend([(term, 'ORGANIZATION') for term in self.organizations])
            entities.extend([(term, 'CHEMICAL') for term in self.chemicals])
            
            for term, entity_type in entities:
                automaton.add_word(term, (entity_type, term))
            
            automaton.make_automaton()
            return automaton
        
        # Build automaton and measure setup time
        automaton, setup_time, setup_memory = self.measure_performance(build_automaton)
        
        # Process documents
        def process_documents():
            total_entities = 0
            for filename, content in documents:
                matches = list(automaton.iter(content))
                total_entities += len(matches)
            return total_entities
        
        entities_found, processing_time, memory_used = self.measure_performance(process_documents)
        
        pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
        
        return {
            "library": "pyahocorasick",
            "version": ahocorasick.__version__ if hasattr(ahocorasick, '__version__') else "unknown",
            "configuration": "OSHA dictionaries (standards, orgs, chemicals)",
            "pages_per_sec": pages_per_sec,
            "processing_time": processing_time,
            "setup_time": setup_time,
            "total_pages": len(documents),
            "entities_found": entities_found,
            "memory_usage_mb": memory_used,
            "setup_memory_mb": setup_memory,
            "error_message": None
        }

    def benchmark_hyperscan(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark hyperscan for pattern-based entity extraction"""
        if not HYPERSCAN_AVAILABLE:
            return {"error": "hyperscan not available"}
        
        try:
            # Compile all patterns into hyperscan database
            def build_database():
                all_patterns = []
                all_patterns.extend(self.requirement_patterns)
                all_patterns.extend(self.measurement_patterns)
                all_patterns.extend(self.contact_patterns)
                
                patterns = []
                flags = []
                ids = []
                
                for i, pattern in enumerate(all_patterns):
                    patterns.append(pattern.encode('utf-8'))
                    flags.append(hyperscan.HS_FLAG_CASELESS)
                    ids.append(i)
                
                db = hyperscan.compile_multi(patterns, flags=flags, ids=ids)
                return db, len(all_patterns)
            
            database_info, setup_time, setup_memory = self.measure_performance(build_database)
            database, pattern_count = database_info
            
            # Process documents
            def process_documents():
                total_matches = 0
                
                def on_match(match_id, start, end, flags, context):
                    nonlocal total_matches
                    total_matches += 1
                
                for filename, content in documents:
                    hyperscan.scan(database, content.encode('utf-8'), on_match)
                
                return total_matches
            
            matches_found, processing_time, memory_used = self.measure_performance(process_documents)
            
            pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
            
            return {
                "library": "hyperscan",
                "version": "0.7.23",  # Known version from our installation
                "configuration": f"Multi-regex compilation ({pattern_count} patterns)",
                "pages_per_sec": pages_per_sec,
                "processing_time": processing_time,
                "setup_time": setup_time,
                "total_pages": len(documents),
                "entities_found": matches_found,
                "memory_usage_mb": memory_used,
                "setup_memory_mb": setup_memory,
                "pattern_count": pattern_count,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "library": "hyperscan",
                "error_message": str(e),
                "pages_per_sec": 0,
                "processing_time": 0,
                "entities_found": 0
            }

    def benchmark_marisa_trie(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark marisa-trie for memory-efficient dictionary lookups"""
        if not MARISA_AVAILABLE:
            return {"error": "marisa-trie not available"}
        
        try:
            # Build marisa trie
            def build_trie():
                all_terms = []
                all_terms.extend(self.osha_standards)
                all_terms.extend(self.organizations)
                all_terms.extend(self.chemicals)
                
                trie = marisa_trie.Trie(all_terms)
                return trie, len(all_terms)
            
            trie_info, setup_time, setup_memory = self.measure_performance(build_trie)
            trie, term_count = trie_info
            
            # Process documents
            def process_documents():
                total_matches = 0
                for filename, content in documents:
                    # Simple word tokenization for trie lookup
                    words = re.findall(r'\b\w+\b', content.lower())
                    for word in words:
                        if word in trie:
                            total_matches += 1
                return total_matches
            
            matches_found, processing_time, memory_used = self.measure_performance(process_documents)
            
            pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
            
            return {
                "library": "marisa-trie",
                "version": "1.3.1",  # Known version
                "configuration": f"Static trie ({term_count} terms)",
                "pages_per_sec": pages_per_sec,
                "processing_time": processing_time,
                "setup_time": setup_time,
                "total_pages": len(documents),
                "entities_found": matches_found,
                "memory_usage_mb": memory_used,
                "setup_memory_mb": setup_memory,
                "term_count": term_count,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "library": "marisa-trie",
                "error_message": str(e),
                "pages_per_sec": 0,
                "processing_time": 0,
                "entities_found": 0
            }

    def benchmark_flashtext(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark flashtext for lightweight keyword extraction"""
        if not FLASHTEXT_AVAILABLE:
            return {"error": "flashtext not available"}
        
        try:
            # Build flashtext processor
            def build_processor():
                processor = flashtext.KeywordProcessor(case_sensitive=False)
                
                # Add all keywords
                for term in self.osha_standards:
                    processor.add_keyword(term, ('OSHA_STANDARD', term))
                for term in self.organizations:
                    processor.add_keyword(term, ('ORGANIZATION', term))
                for term in self.chemicals:
                    processor.add_keyword(term, ('CHEMICAL', term))
                
                return processor, len(self.osha_standards + self.organizations + self.chemicals)
            
            processor_info, setup_time, setup_memory = self.measure_performance(build_processor)
            processor, keyword_count = processor_info
            
            # Process documents
            def process_documents():
                total_matches = 0
                for filename, content in documents:
                    keywords_found = processor.extract_keywords(content)
                    total_matches += len(keywords_found)
                return total_matches
            
            matches_found, processing_time, memory_used = self.measure_performance(process_documents)
            
            pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
            
            return {
                "library": "flashtext",
                "version": "2.7",  # Known version
                "configuration": f"Keyword processor ({keyword_count} keywords)",
                "pages_per_sec": pages_per_sec,
                "processing_time": processing_time,
                "setup_time": setup_time,
                "total_pages": len(documents),
                "entities_found": matches_found,
                "memory_usage_mb": memory_used,
                "setup_memory_mb": setup_memory,
                "keyword_count": keyword_count,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "library": "flashtext",
                "error_message": str(e),
                "pages_per_sec": 0,
                "processing_time": 0,
                "entities_found": 0
            }

    def benchmark_blingfire(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark blingfire for fast tokenization and sentence segmentation"""
        if not BLINGFIRE_AVAILABLE:
            return {"error": "blingfire not available"}
        
        try:
            # Process documents with blingfire tokenization
            def process_documents():
                total_tokens = 0
                total_sentences = 0
                
                for filename, content in documents:
                    # Tokenize text
                    tokens = bf.text_to_words(content).split()
                    total_tokens += len(tokens)
                    
                    # Segment sentences
                    sentences = bf.text_to_sentences(content).split('\n')
                    total_sentences += len([s for s in sentences if s.strip()])
                
                return total_tokens, total_sentences
            
            result, processing_time, memory_used = self.measure_performance(process_documents)
            total_tokens, total_sentences = result
            
            pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
            
            return {
                "library": "blingfire",
                "version": "0.1.8",  # Known version
                "configuration": "Fast tokenization + sentence segmentation",
                "pages_per_sec": pages_per_sec,
                "processing_time": processing_time,
                "setup_time": 0.0,  # No setup required
                "total_pages": len(documents),
                "tokens_found": total_tokens,
                "sentences_found": total_sentences,
                "memory_usage_mb": memory_used,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "library": "blingfire",
                "error_message": str(e),
                "pages_per_sec": 0,
                "processing_time": 0,
                "tokens_found": 0
            }

    def benchmark_ripgrep_sidecar(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark ripgrep as external sidecar for maximum performance"""
        try:
            # Check if ripgrep is available
            result = subprocess.run(['rg', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {"error": "ripgrep not available"}
            
            # Create temporary files for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write test documents to temporary files
                doc_files = []
                for i, (filename, content) in enumerate(documents):
                    temp_file = os.path.join(temp_dir, f"doc_{i}.md")
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    doc_files.append(temp_file)
                
                # Create patterns file
                patterns_file = os.path.join(temp_dir, "patterns.txt")
                with open(patterns_file, 'w', encoding='utf-8') as f:
                    # Add all entity terms for fixed-string search
                    for term in self.osha_standards + self.organizations + self.chemicals:
                        f.write(f"{term}\n")
                
                # Measure ripgrep performance
                def run_ripgrep():
                    cmd = [
                        'rg', 
                        '--fixed-strings',
                        '--file', patterns_file,
                        '--count',
                        '--json'
                    ] + doc_files
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    # Count total matches from JSON output
                    total_matches = 0
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get('type') == 'match':
                                    total_matches += 1
                            except:
                                pass
                    
                    return total_matches
                
                matches_found, processing_time, memory_used = self.measure_performance(run_ripgrep)
                
                pages_per_sec = len(documents) / processing_time if processing_time > 0 else 0
                
                return {
                    "library": "ripgrep_sidecar",
                    "version": result.stdout.strip().split('\n')[0] if result.stdout else "unknown",
                    "configuration": "Fixed-strings + JSON output",
                    "pages_per_sec": pages_per_sec,
                    "processing_time": processing_time,
                    "setup_time": 0.0,  # File I/O time included in processing
                    "total_pages": len(documents),
                    "entities_found": matches_found,
                    "memory_usage_mb": memory_used,
                    "error_message": None
                }
                
        except Exception as e:
            return {
                "library": "ripgrep_sidecar",
                "error_message": str(e),
                "pages_per_sec": 0,
                "processing_time": 0,
                "entities_found": 0
            }

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all available benchmarks and return results"""
        print("High-Performance NLP Benchmark Starting...")
        print("=" * 60)
        
        # Load test documents
        documents = self.get_test_documents()
        if not documents:
            print(f"No test documents found in {self.test_docs_dir}")
            return {"error": "No test documents found"}
        
        print(f"Loaded {len(documents)} test documents")
        print(f"Average document size: {sum(len(content) for _, content in documents) / len(documents):.0f} characters")
        print()
        
        # System info
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "available_libraries": {
                "pyahocorasick": AHOCORASICK_AVAILABLE,
                "hyperscan": HYPERSCAN_AVAILABLE,
                "marisa_trie": MARISA_AVAILABLE,
                "flashtext": FLASHTEXT_AVAILABLE,
                "blingfire": BLINGFIRE_AVAILABLE
            }
        }
        
        # Run benchmarks
        benchmarks = [
            ("pyahocorasick", self.benchmark_pyahocorasick),
            ("hyperscan", self.benchmark_hyperscan),
            ("marisa-trie", self.benchmark_marisa_trie),
            ("flashtext", self.benchmark_flashtext),
            ("blingfire", self.benchmark_blingfire),
            ("ripgrep", self.benchmark_ripgrep_sidecar)
        ]
        
        results = []
        for name, benchmark_func in benchmarks:
            print(f"Testing {name}...")
            result = benchmark_func(documents)
            results.append(result)
            
            if "error" in result:
                print(f"  ❌ {result['error']}")
            else:
                pages_sec = result.get('pages_per_sec', 0)
                entities = result.get('entities_found', result.get('tokens_found', 0))
                memory = result.get('memory_usage_mb', 0)
                
                # Check if we hit our target
                target_met = "🎯" if pages_sec >= 1000 else "📈" if pages_sec >= 500 else "⚠️"
                
                print(f"  {target_met} {pages_sec:.1f} pages/sec, {entities} entities, {memory:.1f}MB")
            print()
        
        return {
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "focus": "High-performance deterministic automata comparison",
            "target_performance": "1000+ pages/sec",
            "system_info": system_info,
            "total_documents": len(documents),
            "results": results
        }

    def save_results(self, results: Dict[str, Any]) -> str:
        """Save benchmark results to JSON file"""
        timestamp = results["timestamp"]
        filename = f"high_performance_nlp_results_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        return filepath


def main():
    """Run high-performance NLP benchmarks"""
    benchmark = HighPerformanceNLPBenchmark()
    results = benchmark.run_all_benchmarks()
    
    if "error" not in results:
        filepath = benchmark.save_results(results)
        print("=" * 60)
        print("BENCHMARK COMPLETE")
        print(f"Results saved to: {filepath}")
        print()
        
        # Summary of results
        print("PERFORMANCE SUMMARY:")
        print("-" * 40)
        successful_results = [r for r in results["results"] if "error" not in r]
        
        if successful_results:
            # Sort by pages per second
            sorted_results = sorted(successful_results, key=lambda x: x.get('pages_per_sec', 0), reverse=True)
            
            for result in sorted_results:
                pages_sec = result.get('pages_per_sec', 0)
                library = result.get('library', 'unknown')
                target_status = "✅ TARGET MET" if pages_sec >= 1000 else "🔄 IMPROVING" if pages_sec >= 500 else "❌ INSUFFICIENT"
                
                print(f"{library:>15}: {pages_sec:>8.1f} pages/sec {target_status}")
        
        print()
        print("Next steps: Analyze results and select optimal library combination")
    else:
        print(f"Benchmark failed: {results['error']}")


if __name__ == "__main__":
    main()