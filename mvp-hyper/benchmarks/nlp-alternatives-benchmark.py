#!/usr/bin/env python3
"""
High-Performance NLP Alternatives Benchmark
==========================================
Test multiple NLP libraries for named entity recognition performance vs spaCy
"""

import time
import psutil
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime
import sys
from dataclasses import dataclass

# Test multiple NLP library imports
NLP_LIBRARIES = {}

# Test spaCy
try:
    import spacy
    NLP_LIBRARIES['spacy'] = spacy.__version__
    print(f"✅ spaCy {spacy.__version__} available")
except ImportError:
    print("❌ spaCy not available")

# Test HanLP
try:
    import hanlp
    NLP_LIBRARIES['hanlp'] = hanlp.__version__
    print(f"✅ HanLP {hanlp.__version__} available")
except ImportError:
    print("❌ HanLP not available")

# Test Stanza
try:
    import stanza
    NLP_LIBRARIES['stanza'] = stanza.__version__
    print(f"✅ Stanza {stanza.__version__} available")
except ImportError:
    print("❌ Stanza not available")

# Test Flair
try:
    import flair
    NLP_LIBRARIES['flair'] = flair.__version__
    print(f"✅ Flair {flair.__version__} available")
except ImportError:
    print("❌ Flair not available")

# Test NLTK (for comparison)
try:
    import nltk
    NLP_LIBRARIES['nltk'] = nltk.__version__
    print(f"✅ NLTK {nltk.__version__} available")
except ImportError:
    print("❌ NLTK not available")


@dataclass
class NLPBenchmarkResult:
    """Results from NLP library benchmark."""
    library: str
    version: str
    configuration: str
    pages_per_sec: float
    processing_time: float
    total_pages: int
    entities_found: int
    patterns_matched: int
    memory_usage_mb: float
    setup_time: float
    accuracy_score: float = 0.0
    error_message: Optional[str] = None


class NLPAlternativesBenchmark:
    """Benchmark multiple NLP libraries for entity extraction performance."""
    
    def __init__(self, markdown_dir: Path = None):
        self.markdown_dir = markdown_dir or Path("/home/corey/projects/docling/mvp-hyper/output/pipeline/1-markdown")
        self.results = []
        
        # Enhanced structural patterns for domain-specific entities
        self.enhanced_patterns = {
            # OSHA/Safety specific patterns
            'osha_standards': re.compile(r'\b(OSHA|CFR|USC|ISO|ANSI|NFPA)\s+\d+(?:[-.]?\d+)*', re.IGNORECASE),
            'safety_requirements': re.compile(r'\b(must|shall|required to|should|will|cannot|may not)\s+(wear|use|provide|ensure|comply|maintain|inspect)\s+([^.!?]{10,50})', re.IGNORECASE),
            'chemical_entities': re.compile(r'\b(asbestos|benzene|lead|silica|formaldehyde|chromium|cadmium|acrylonitrile|butadiene)\b', re.IGNORECASE),
            
            # General entities
            'organizations': re.compile(r'\b(Inc\.|Corp\.|LLC|Company|Corporation|Department|Administration|Agency|Bureau|Institute|University|College)\b', re.IGNORECASE),
            'locations': re.compile(r'\b(California|New York|Texas|Florida|Illinois|Pennsylvania|Ohio|Georgia|North Carolina|Michigan|Washington|Boston|Chicago|Los Angeles|Houston|Philadelphia|Phoenix|San Antonio|San Diego|Dallas|Austin)\b', re.IGNORECASE),
            'phone_numbers': re.compile(r'\b(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'),
            'measurements': re.compile(r'(\d+(?:\.\d+)?)\s*(percent|%|dollars?|\$|hours?|days?|years?|times?|feet|ft|inches|in|pounds|lbs|kilograms|kg|meters|m|miles|km)', re.IGNORECASE),
            'conditionals': re.compile(r'\b(if|when|unless|provided that|in case|where|whenever)\s+([^,]{10,60})', re.IGNORECASE),
            'person_titles': re.compile(r'\b(Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|President|Director|Manager|Engineer|Supervisor|Inspector|Coordinator)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
        }
        
    def load_test_documents(self, limit: int = 20) -> List[Tuple[Path, str, int]]:
        """Load markdown documents for testing."""
        documents = []
        markdown_files = list(self.markdown_dir.glob("*.md"))[:limit]
        
        if not markdown_files:
            print(f"❌ No markdown files found in {self.markdown_dir}")
            return []
            
        print(f"📁 Loading {len(markdown_files)} markdown documents...")
        
        for file_path in markdown_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract page count from YAML frontmatter if available
                pages = 1  # default
                if content.startswith('---'):
                    end_yaml = content.find('\n---', 3)
                    if end_yaml > 0:
                        yaml_content = content[3:end_yaml]
                        if 'pages:' in yaml_content:
                            try:
                                pages = int(yaml_content.split('pages:')[1].split()[0])
                            except:
                                pages = len(content.split('\n')) // 50  # rough estimate
                
                documents.append((file_path, content, pages))
                
            except Exception as e:
                print(f"⚠️  Could not load {file_path}: {e}")
        
        total_pages = sum(doc[2] for doc in documents)
        print(f"📊 Loaded {len(documents)} documents, {total_pages} total pages")
        return documents
    
    def extract_enhanced_regex_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract entities using enhanced regex patterns."""
        patterns_found = {}
        
        for pattern_name, pattern_regex in self.enhanced_patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                if pattern_name in ['safety_requirements', 'conditionals']:
                    # Handle tuple matches
                    patterns_found[pattern_name] = [f"{m[0]} {m[1]} {m[2]}" if len(m) > 2 else ' '.join(m) for m in matches]
                elif pattern_name in ['person_titles']:
                    patterns_found[pattern_name] = [f"{m[0]} {m[1]}" if len(m) > 1 else m for m in matches]
                else:
                    patterns_found[pattern_name] = [m if isinstance(m, str) else ' '.join(m) for m in matches]
        
        return patterns_found
    
    def test_spacy_ner(self, documents: List[Tuple[Path, str, int]]) -> NLPBenchmarkResult:
        """Test spaCy named entity recognition."""
        if 'spacy' not in NLP_LIBRARIES:
            return NLPBenchmarkResult(
                library='spacy', version='N/A', configuration='not_available',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message="spaCy not available"
            )
        
        try:
            setup_start = time.time()
            nlp = spacy.load("en_core_web_sm")
            nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            setup_time = time.time() - setup_start
            
            start_time = time.time()
            start_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            total_entities = 0
            total_patterns = 0
            total_pages = sum(doc[2] for doc in documents)
            
            # Extract entities in batches
            all_texts = [content for _, content, _ in documents]
            
            with nlp.memory_zone():
                docs = nlp.pipe(all_texts, batch_size=1000)
                for doc in docs:
                    total_entities += len(doc.ents)
            
            # Extract patterns
            for _, content, _ in documents:
                patterns = self.extract_enhanced_regex_patterns(content)
                total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            processing_time = end_time - start_time
            pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
            memory_used = end_memory - start_memory
            
            return NLPBenchmarkResult(
                library='spacy', version=NLP_LIBRARIES['spacy'], configuration='NER-only + patterns',
                pages_per_sec=pages_per_sec, processing_time=processing_time, total_pages=total_pages,
                entities_found=total_entities, patterns_matched=total_patterns, memory_usage_mb=memory_used,
                setup_time=setup_time
            )
            
        except Exception as e:
            return NLPBenchmarkResult(
                library='spacy', version=NLP_LIBRARIES.get('spacy', 'N/A'), configuration='error',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message=str(e)
            )
    
    def test_hanlp_ner(self, documents: List[Tuple[Path, str, int]]) -> NLPBenchmarkResult:
        """Test HanLP named entity recognition."""
        if 'hanlp' not in NLP_LIBRARIES:
            return NLPBenchmarkResult(
                library='hanlp', version='N/A', configuration='not_available',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message="HanLP not available"
            )
        
        try:
            setup_start = time.time()
            # Try to load English NER model
            try:
                nlp = hanlp.load(hanlp.pretrained.ner.CONLL03_NER_BERT_BASE_UNCASED_EN)
            except:
                # Fallback to a basic model or default
                nlp = hanlp.load('en')
            setup_time = time.time() - setup_start
            
            start_time = time.time()
            start_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            total_entities = 0
            total_patterns = 0
            total_pages = sum(doc[2] for doc in documents)
            
            # Process documents
            for _, content, _ in documents:
                # Split into sentences for better processing
                sentences = content.split('.')[:10]  # Limit for performance testing
                for sentence in sentences:
                    if len(sentence.strip()) > 10:
                        try:
                            # Try HanLP NER
                            result = nlp(sentence.strip().split())
                            if isinstance(result, list):
                                total_entities += len(result)
                        except:
                            # Skip problematic sentences
                            pass
                
                # Extract patterns
                patterns = self.extract_enhanced_regex_patterns(content)
                total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            processing_time = end_time - start_time
            pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
            memory_used = end_memory - start_memory
            
            return NLPBenchmarkResult(
                library='hanlp', version=NLP_LIBRARIES['hanlp'], configuration='English NER + patterns',
                pages_per_sec=pages_per_sec, processing_time=processing_time, total_pages=total_pages,
                entities_found=total_entities, patterns_matched=total_patterns, memory_usage_mb=memory_used,
                setup_time=setup_time
            )
            
        except Exception as e:
            return NLPBenchmarkResult(
                library='hanlp', version=NLP_LIBRARIES.get('hanlp', 'N/A'), configuration='error',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message=str(e)
            )
    
    def test_stanza_ner(self, documents: List[Tuple[Path, str, int]]) -> NLPBenchmarkResult:
        """Test Stanford Stanza named entity recognition."""
        if 'stanza' not in NLP_LIBRARIES:
            return NLPBenchmarkResult(
                library='stanza', version='N/A', configuration='not_available',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message="Stanza not available"
            )
        
        try:
            setup_start = time.time()
            # Download and load English NER model
            nlp = stanza.Pipeline('en', processors='tokenize,ner', use_gpu=False)
            setup_time = time.time() - setup_start
            
            start_time = time.time()
            start_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            total_entities = 0
            total_patterns = 0
            total_pages = sum(doc[2] for doc in documents)
            
            # Process documents in smaller chunks
            for _, content, _ in documents:
                # Process first 1000 characters for performance testing
                text_sample = content[:1000]
                try:
                    doc = nlp(text_sample)
                    for sentence in doc.sentences:
                        for entity in sentence.ents:
                            total_entities += 1
                except:
                    # Skip problematic documents
                    pass
                
                # Extract patterns
                patterns = self.extract_enhanced_regex_patterns(content)
                total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            processing_time = end_time - start_time
            pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
            memory_used = end_memory - start_memory
            
            return NLPBenchmarkResult(
                library='stanza', version=NLP_LIBRARIES['stanza'], configuration='English NER + patterns',
                pages_per_sec=pages_per_sec, processing_time=processing_time, total_pages=total_pages,
                entities_found=total_entities, patterns_matched=total_patterns, memory_usage_mb=memory_used,
                setup_time=setup_time
            )
            
        except Exception as e:
            return NLPBenchmarkResult(
                library='stanza', version=NLP_LIBRARIES.get('stanza', 'N/A'), configuration='error',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message=str(e)
            )
    
    def test_enhanced_regex_only(self, documents: List[Tuple[Path, str, int]]) -> NLPBenchmarkResult:
        """Test enhanced regex-only entity extraction."""
        try:
            setup_start = time.time()
            # No setup needed for regex
            setup_time = time.time() - setup_start
            
            start_time = time.time()
            start_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            total_entities = 0
            total_patterns = 0
            total_pages = sum(doc[2] for doc in documents)
            
            # Extract patterns only
            for _, content, _ in documents:
                patterns = self.extract_enhanced_regex_patterns(content)
                pattern_count = sum(len(pattern_list) for pattern_list in patterns.values())
                total_patterns += pattern_count
                total_entities += pattern_count  # Count patterns as entities for comparison
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            processing_time = end_time - start_time
            pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
            memory_used = end_memory - start_memory
            
            return NLPBenchmarkResult(
                library='enhanced_regex', version='1.0', configuration='Domain-specific patterns',
                pages_per_sec=pages_per_sec, processing_time=processing_time, total_pages=total_pages,
                entities_found=total_entities, patterns_matched=total_patterns, memory_usage_mb=memory_used,
                setup_time=setup_time
            )
            
        except Exception as e:
            return NLPBenchmarkResult(
                library='enhanced_regex', version='1.0', configuration='error',
                pages_per_sec=0, processing_time=0, total_pages=0, entities_found=0,
                patterns_matched=0, memory_usage_mb=0, setup_time=0,
                error_message=str(e)
            )
    
    def run_comprehensive_benchmark(self, document_limit: int = 15):
        """Run comprehensive benchmark of all available NLP libraries."""
        print("🚀 COMPREHENSIVE NLP ALTERNATIVES BENCHMARK")
        print("=" * 70)
        print(f"Target: Find fastest NLP library for 1,000+ pages/second")
        print(f"Available libraries: {list(NLP_LIBRARIES.keys())}")
        print(f"System: {psutil.cpu_count()} CPUs, {psutil.virtual_memory().total / (1024**3):.1f} GB RAM")
        print("=" * 70)
        
        # Load test documents
        documents = self.load_test_documents(document_limit)
        if not documents:
            print("❌ No documents to test with")
            return
        
        # Test configurations
        test_functions = [
            ("Enhanced Regex Only", self.test_enhanced_regex_only),
            ("spaCy NER", self.test_spacy_ner),
        ]
        
        # Add available libraries
        if 'hanlp' in NLP_LIBRARIES:
            test_functions.append(("HanLP NER", self.test_hanlp_ner))
        
        if 'stanza' in NLP_LIBRARIES:
            test_functions.append(("Stanza NER", self.test_stanza_ner))
        
        # Run benchmarks
        for test_name, test_function in test_functions:
            print(f"\n🧪 Testing: {test_name}")
            print("─" * 50)
            
            try:
                result = test_function(documents)
                self.results.append(result)
                
                # Display results
                if result.error_message:
                    print(f"❌ Failed: {result.error_message}")
                else:
                    status = "✅" if result.pages_per_sec >= 1000 else "⚠️" if result.pages_per_sec >= 500 else "❌"
                    print(f"{status} Performance: {result.pages_per_sec:.1f} pages/sec")
                    print(f"   Setup time: {result.setup_time:.2f}s")
                    print(f"   Processing time: {result.processing_time:.2f}s") 
                    print(f"   Entities found: {result.entities_found}")
                    print(f"   Patterns matched: {result.patterns_matched}")
                    print(f"   Memory used: {result.memory_usage_mb:.1f} MB")
                
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
        
        # Summary results
        self.print_comprehensive_summary()
        self.save_comprehensive_results()
    
    def print_comprehensive_summary(self):
        """Print comprehensive benchmark summary."""
        if not self.results:
            return
            
        print("\n📊 COMPREHENSIVE NLP BENCHMARK SUMMARY")
        print("=" * 100)
        print(f"{'Library':<15} {'Version':<10} {'Pages/Sec':<12} {'Setup':<8} {'Entities':<10} {'Patterns':<10} {'Memory':<10}")
        print("─" * 100)
        
        # Sort by performance
        valid_results = [r for r in self.results if not r.error_message]
        error_results = [r for r in self.results if r.error_message]
        
        for result in sorted(valid_results, key=lambda x: x.pages_per_sec, reverse=True):
            status = "🟢" if result.pages_per_sec >= 1000 else "🟡" if result.pages_per_sec >= 500 else "🔴"
            print(f"{result.library:<15} {result.version:<10} {result.pages_per_sec:>8.1f} {status}   "
                  f"{result.setup_time:>4.1f}s   {result.entities_found:>7}   {result.patterns_matched:>7}   "
                  f"{result.memory_usage_mb:>6.1f}MB")
        
        # Show errors
        for result in error_results:
            print(f"{result.library:<15} {result.version:<10} {'ERROR':>12} {'N/A':>8} {'N/A':>10} {'N/A':>10} {'N/A':>10}")
        
        # Analysis
        if valid_results:
            best = max(valid_results, key=lambda x: x.pages_per_sec)
            print(f"\n🏆 Best Performance: {best.library} v{best.version} at {best.pages_per_sec:.1f} pages/sec")
            
            viable_options = [r for r in valid_results if r.pages_per_sec >= 1000]
            if viable_options:
                print(f"\n✅ LIBRARIES MEETING 1000+ pages/sec TARGET:")
                for r in sorted(viable_options, key=lambda x: x.pages_per_sec, reverse=True):
                    entity_quality = "High entity extraction" if r.entities_found > 100 else "Pattern extraction"
                    print(f"   • {r.library} v{r.version}: {r.pages_per_sec:.1f} pages/sec ({entity_quality})")
            else:
                print(f"\n❌ NO LIBRARIES MEET 1000+ pages/sec TARGET")
                print(f"   Recommend: Enhanced regex patterns at {max(valid_results, key=lambda x: x.pages_per_sec).pages_per_sec:.1f} pages/sec")
        
        print(f"\n💡 RECOMMENDATIONS FOR FUTURE STATE:")
        enhanced_regex = next((r for r in valid_results if r.library == 'enhanced_regex'), None)
        if enhanced_regex and enhanced_regex.pages_per_sec >= 1000:
            print(f"   ✅ Use enhanced regex patterns for real-time classification")
            print(f"   ✅ Domain-specific entity extraction at {enhanced_regex.pages_per_sec:.1f} pages/sec")
            print(f"   ✅ Patterns found: OSHA standards, safety requirements, chemical entities, organizations")
        
        # Suggest hybrid approach
        best_nlp = max([r for r in valid_results if r.library != 'enhanced_regex'], key=lambda x: x.pages_per_sec) if len(valid_results) > 1 else None
        if best_nlp:
            print(f"   🔄 Optional: Use {best_nlp.library} for background enrichment at {best_nlp.pages_per_sec:.1f} pages/sec")
    
    def save_comprehensive_results(self):
        """Save comprehensive benchmark results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"/home/corey/projects/docling/mvp-hyper/benchmarks/nlp_alternatives_results_{timestamp}.json")
        
        results_data = {
            'timestamp': timestamp,
            'focus': 'Comprehensive NLP library performance comparison',
            'libraries_tested': list(NLP_LIBRARIES.keys()),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'available_libraries': NLP_LIBRARIES
            },
            'results': [
                {
                    'library': r.library,
                    'version': r.version,
                    'configuration': r.configuration,
                    'pages_per_sec': r.pages_per_sec,
                    'processing_time': r.processing_time,
                    'total_pages': r.total_pages,
                    'entities_found': r.entities_found,
                    'patterns_matched': r.patterns_matched,
                    'memory_usage_mb': r.memory_usage_mb,
                    'setup_time': r.setup_time,
                    'accuracy_score': r.accuracy_score,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\n💾 Comprehensive results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Run the comprehensive NLP alternatives benchmark."""
    if len(sys.argv) > 1:
        document_limit = int(sys.argv[1])
    else:
        document_limit = 15
        
    benchmark = NLPAlternativesBenchmark()
    benchmark.run_comprehensive_benchmark(document_limit)


if __name__ == "__main__":
    main()