#!/usr/bin/env python3
"""
Enhanced Classification Benchmark
=================================
Test spaCy NLP + Universal Entity Extraction performance with complex markdown documents
"""

import time
import psutil
import statistics
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime
import sys
from dataclasses import dataclass

# Try importing spaCy - install if needed
try:
    import spacy
    from spacy import displacy
    HAS_SPACY = True
except ImportError:
    print("⚠️  spaCy not installed. Run: pip install spacy")
    print("⚠️  Also run: python -m spacy download en_core_web_sm")
    HAS_SPACY = False


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    configuration: str
    pages_per_sec: float
    processing_time: float
    total_pages: int
    entities_found: int
    patterns_matched: int
    memory_usage_mb: float
    accuracy_score: float = 0.0


class EnhancedClassificationBenchmark:
    """Benchmark suite for enhanced classification with spaCy NLP and universal entity extraction."""
    
    def __init__(self, markdown_dir: Path = None):
        self.markdown_dir = markdown_dir or Path("/home/corey/projects/docling/mvp-hyper/output/pipeline/1-markdown")
        self.results = []
        
        # Initialize spaCy models for testing
        self.spacy_models = {}
        if HAS_SPACY:
            self._init_spacy_models()
        
        # Universal structural patterns from FutureState.md
        self.structural_patterns = {
            'requirements': re.compile(r'\b(must|shall|required to|should|will|cannot|may not)\s+([^.!?]{15,100})', re.IGNORECASE),
            'conditionals': re.compile(r'\b(if|when|unless|provided that|in case)\s+([^,]{10,60})', re.IGNORECASE), 
            'measurements': re.compile(r'(\d+(?:\.\d+)?)\s*(percent|%|dollars?|\$|hours?|days?|years?|times?)', re.IGNORECASE),
            'headers': re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE),
            'lists': re.compile(r'^\s*[-*•]\s+(.+)$', re.MULTILINE),
            'authorities': re.compile(r'\b(CFR|USC|ISO|ANSI|NFPA|OSHA)\s+\d+(?:[-.]?\d+)*', re.IGNORECASE),
            'references': re.compile(r'\b(?:see|refer to|according to|pursuant to)\s+([^.]{10,50})', re.IGNORECASE),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_numbers': re.compile(r'\b(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'),
        }
        
    def _init_spacy_models(self):
        """Initialize different spaCy model configurations for testing."""
        try:
            # Full pipeline model
            self.spacy_models['full'] = spacy.load("en_core_web_sm")
            
            # NER-only model (optimized for speed)
            nlp_ner_only = spacy.load("en_core_web_sm")
            nlp_ner_only.disable_pipes(["parser", "tagger", "lemmatizer", "attribute_ruler"])
            self.spacy_models['ner_only'] = nlp_ner_only
            
            # Minimum model (just tokenizer + NER)
            nlp_minimal = spacy.load("en_core_web_sm")
            nlp_minimal.disable_pipes(["parser", "tagger", "lemmatizer", "attribute_ruler", "tok2vec"])
            self.spacy_models['minimal'] = nlp_minimal
            
            print("✅ spaCy models initialized successfully")
            
        except OSError as e:
            print(f"❌ Could not load spaCy model: {e}")
            print("   Run: python -m spacy download en_core_web_sm")
            self.spacy_models = {}
    
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
    
    def extract_spacy_entities(self, content: str, model_name: str = 'ner_only') -> Dict[str, List[str]]:
        """Extract entities using spaCy NLP."""
        if not HAS_SPACY or model_name not in self.spacy_models:
            return {}
        
        nlp = self.spacy_models[model_name]
        
        # Process in chunks for large documents
        chunk_size = 10000
        entities = {
            'persons': set(),
            'organizations': set(),
            'locations': set(),
            'money': set(),
            'dates': set(),
            'quantities': set()
        }
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            doc = nlp(chunk)
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    entities['persons'].add(ent.text.strip())
                elif ent.label_ == "ORG":
                    entities['organizations'].add(ent.text.strip())
                elif ent.label_ in ["GPE", "LOC"]:
                    entities['locations'].add(ent.text.strip())
                elif ent.label_ == "MONEY":
                    entities['money'].add(ent.text.strip())
                elif ent.label_ == "DATE":
                    entities['dates'].add(ent.text.strip())
                elif ent.label_ in ["CARDINAL", "QUANTITY"]:
                    entities['quantities'].add(ent.text.strip())
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in entities.items()}
    
    def extract_structural_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract structural patterns using regex."""
        patterns_found = {}
        
        for pattern_name, pattern_regex in self.structural_patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                # Handle different match group structures
                if pattern_name in ['requirements', 'conditionals', 'references']:
                    patterns_found[pattern_name] = [f"{m[0]} {m[1]}" for m in matches if len(m) > 1]
                else:
                    patterns_found[pattern_name] = [m if isinstance(m, str) else ' '.join(m) for m in matches]
        
        return patterns_found
    
    def run_classification_benchmark(self, documents: List[Tuple[Path, str, int]], 
                                   config_name: str, spacy_model: str = 'ner_only',
                                   enable_patterns: bool = True) -> BenchmarkResult:
        """Run benchmark with specific configuration."""
        print(f"\n🧪 Testing: {config_name}")
        print("─" * 40)
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        total_entities = 0
        total_patterns = 0
        total_pages = sum(doc[2] for doc in documents)
        
        for file_path, content, pages in documents:
            # Extract spaCy entities
            if HAS_SPACY and spacy_model in self.spacy_models:
                entities = self.extract_spacy_entities(content, spacy_model)
                total_entities += sum(len(entity_list) for entity_list in entities.values())
            
            # Extract structural patterns
            if enable_patterns:
                patterns = self.extract_structural_patterns(content)
                total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        processing_time = end_time - start_time
        pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
        memory_used = end_memory - start_memory
        
        result = BenchmarkResult(
            configuration=config_name,
            pages_per_sec=pages_per_sec,
            processing_time=processing_time,
            total_pages=total_pages,
            entities_found=total_entities,
            patterns_matched=total_patterns,
            memory_usage_mb=memory_used
        )
        
        # Display results
        status = "✅" if pages_per_sec >= 1000 else "⚠️" if pages_per_sec >= 500 else "❌"
        print(f"{status} Performance: {pages_per_sec:.1f} pages/sec")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Entities found: {total_entities}")
        print(f"   Patterns matched: {total_patterns}")
        print(f"   Memory used: {memory_used:.1f} MB")
        
        return result
    
    def run_full_benchmark(self, document_limit: int = 20):
        """Run comprehensive benchmark with different configurations."""
        print("🚀 ENHANCED CLASSIFICATION BENCHMARK")
        print("=" * 60)
        print(f"Target: 1,000+ pages/second with enhanced features")
        print(f"CPUs: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print(f"spaCy Available: {HAS_SPACY}")
        print("=" * 60)
        
        # Load test documents
        documents = self.load_test_documents(document_limit)
        if not documents:
            print("❌ No documents to test with")
            return
        
        # Test configurations
        test_configs = []
        
        if HAS_SPACY:
            # spaCy model variations
            test_configs.extend([
                ("spaCy Full Pipeline + Patterns", "full", True),
                ("spaCy NER-Only + Patterns", "ner_only", True),
                ("spaCy Minimal + Patterns", "minimal", True),
                ("spaCy NER-Only (No Patterns)", "ner_only", False),
            ])
        
        # Baseline configurations
        test_configs.extend([
            ("Regex Patterns Only", None, True),
            ("No Enhancement (Baseline)", None, False),
        ])
        
        # Run benchmarks
        for config_name, spacy_model, enable_patterns in test_configs:
            try:
                result = self.run_classification_benchmark(
                    documents, config_name, spacy_model, enable_patterns
                )
                self.results.append(result)
            except Exception as e:
                print(f"❌ {config_name} failed: {e}")
        
        # Summary results
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print benchmark summary."""
        if not self.results:
            return
            
        print("\n📊 BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"{'Configuration':<35} {'Pages/Sec':<12} {'Entities':<10} {'Patterns':<10} {'Memory':<10}")
        print("─" * 80)
        
        for result in sorted(self.results, key=lambda x: x.pages_per_sec, reverse=True):
            status = "🟢" if result.pages_per_sec >= 1000 else "🟡" if result.pages_per_sec >= 500 else "🔴"
            print(f"{result.configuration:<35} {result.pages_per_sec:>8.1f} {status}   "
                  f"{result.entities_found:>7}   {result.patterns_matched:>7}   "
                  f"{result.memory_usage_mb:>6.1f}MB")
        
        # Best performer
        best = max(self.results, key=lambda x: x.pages_per_sec)
        print(f"\n🏆 Best Performance: {best.configuration} at {best.pages_per_sec:.1f} pages/sec")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        viable_configs = [r for r in self.results if r.pages_per_sec >= 1000]
        if viable_configs:
            best_viable = max(viable_configs, key=lambda x: x.entities_found + x.patterns_matched)
            print(f"   ✅ Use: {best_viable.configuration}")
            print(f"   ✅ Expected performance: {best_viable.pages_per_sec:.1f} pages/sec")
            print(f"   ✅ Entity extraction: {best_viable.entities_found} entities found")
        else:
            print("   ⚠️  No configuration meets 1000+ pages/sec target")
            print("   ⚠️  Consider: Document sampling, hybrid processing, or reduced features")
    
    def save_results(self):
        """Save benchmark results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"/home/corey/projects/docling/mvp-hyper/benchmarks/enhanced_classification_results_{timestamp}.json")
        
        results_data = {
            'timestamp': timestamp,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'spacy_available': HAS_SPACY
            },
            'results': [
                {
                    'configuration': r.configuration,
                    'pages_per_sec': r.pages_per_sec,
                    'processing_time': r.processing_time,
                    'total_pages': r.total_pages,
                    'entities_found': r.entities_found,
                    'patterns_matched': r.patterns_matched,
                    'memory_usage_mb': r.memory_usage_mb,
                    'accuracy_score': r.accuracy_score
                }
                for r in self.results
            ]
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\n💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Run the enhanced classification benchmark."""
    if len(sys.argv) > 1:
        document_limit = int(sys.argv[1])
    else:
        document_limit = 20
        
    benchmark = EnhancedClassificationBenchmark()
    benchmark.run_full_benchmark(document_limit)


if __name__ == "__main__":
    main()