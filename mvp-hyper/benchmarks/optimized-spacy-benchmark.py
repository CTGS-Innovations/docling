#!/usr/bin/env python3
"""
Optimized spaCy Benchmark
========================
Testing spaCy with ALL performance optimizations from Context7 documentation
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
    HAS_SPACY = True
except ImportError:
    print("⚠️  spaCy not installed. Run: pip install spacy")
    HAS_SPACY = False


@dataclass
class OptimizedBenchmarkResult:
    """Results from optimized spaCy benchmark."""
    configuration: str
    pages_per_sec: float
    processing_time: float
    total_pages: int
    entities_found: int
    patterns_matched: int
    memory_usage_mb: float
    batch_size: int
    n_processes: int
    disabled_components: List[str]


class OptimizedSpacyBenchmark:
    """Benchmark spaCy with all performance optimizations."""
    
    def __init__(self, markdown_dir: Path = None):
        self.markdown_dir = markdown_dir or Path("/home/corey/projects/docling/mvp-hyper/output/pipeline/1-markdown")
        self.results = []
        
        # Universal structural patterns (same as before)
        self.structural_patterns = {
            'requirements': re.compile(r'\b(must|shall|required to|should|will|cannot|may not)\s+([^.!?]{15,100})', re.IGNORECASE),
            'conditionals': re.compile(r'\b(if|when|unless|provided that|in case)\s+([^,]{10,60})', re.IGNORECASE), 
            'measurements': re.compile(r'(\d+(?:\.\d+)?)\s*(percent|%|dollars?|\$|hours?|days?|years?|times?)', re.IGNORECASE),
            'authorities': re.compile(r'\b(CFR|USC|ISO|ANSI|NFPA|OSHA)\s+\d+(?:[-.]?\d+)*', re.IGNORECASE),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_numbers': re.compile(r'\b(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'),
        }
        
    def setup_optimized_spacy_models(self):
        """Setup spaCy models with ALL performance optimizations."""
        if not HAS_SPACY:
            return {}
            
        models = {}
        
        try:
            # Enable GPU if available
            gpu_activated = spacy.prefer_gpu()
            print(f"🎮 GPU activated: {gpu_activated}")
            
            # Base model
            base_nlp = spacy.load("en_core_web_sm")
            
            # 1. MINIMAL NER-ONLY (disable everything except NER)
            nlp_minimal = spacy.load("en_core_web_sm")
            nlp_minimal.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            # Add doc cleaner to clear tensor data
            nlp_minimal.add_pipe("doc_cleaner", config={"attrs": {"tensor": None}})
            models['minimal_ner'] = nlp_minimal
            
            # 2. MEMORY OPTIMIZED (with memory zones)
            nlp_memory = spacy.load("en_core_web_sm") 
            nlp_memory.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            nlp_memory.add_pipe("doc_cleaner", config={"attrs": {"tensor": None}})
            models['memory_optimized'] = nlp_memory
            
            # 3. BATCH OPTIMIZED (will use optimized batch sizes)
            nlp_batch = spacy.load("en_core_web_sm")
            nlp_batch.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])  
            nlp_batch.add_pipe("doc_cleaner", config={"attrs": {"tensor": None}})
            models['batch_optimized'] = nlp_batch
            
            print("✅ Optimized spaCy models created successfully")
            return models
            
        except Exception as e:
            print(f"❌ Could not create optimized models: {e}")
            return {}
    
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
    
    def extract_entities_optimized(self, texts: List[str], nlp, batch_size: int = 1000, 
                                 n_processes: int = 1, use_memory_zones: bool = False) -> Dict[str, List[str]]:
        """Extract entities using optimized spaCy processing."""
        entities = {
            'persons': set(),
            'organizations': set(), 
            'locations': set(),
            'money': set(),
            'dates': set(),
            'quantities': set()
        }
        
        if use_memory_zones:
            with nlp.memory_zone():
                docs = nlp.pipe(texts, batch_size=batch_size, n_process=n_processes)
                for doc in docs:
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
        else:
            docs = nlp.pipe(texts, batch_size=batch_size, n_process=n_processes)
            for doc in docs:
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
        
        return {k: list(v) for k, v in entities.items()}
    
    def extract_structural_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract structural patterns using regex (unchanged)."""
        patterns_found = {}
        
        for pattern_name, pattern_regex in self.structural_patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                if pattern_name in ['requirements', 'conditionals']:
                    patterns_found[pattern_name] = [f"{m[0]} {m[1]}" for m in matches if len(m) > 1]
                else:
                    patterns_found[pattern_name] = [m if isinstance(m, str) else ' '.join(m) for m in matches]
        
        return patterns_found
    
    def run_optimized_benchmark(self, documents: List[Tuple[Path, str, int]], 
                               config_name: str, nlp=None, batch_size: int = 1000,
                               n_processes: int = 1, use_memory_zones: bool = False,
                               disabled_components: List[str] = None) -> OptimizedBenchmarkResult:
        """Run optimized benchmark with specific configuration."""
        print(f"\n🧪 Testing: {config_name}")
        print("─" * 50)
        print(f"   Batch size: {batch_size}")
        print(f"   Processes: {n_processes}")
        print(f"   Memory zones: {use_memory_zones}")
        print(f"   Disabled: {disabled_components or 'none'}")
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        total_entities = 0
        total_patterns = 0
        total_pages = sum(doc[2] for doc in documents)
        
        # Prepare texts for batch processing
        all_texts = [content for _, content, _ in documents]
        
        # Extract spaCy entities (optimized)
        if nlp is not None:
            entities = self.extract_entities_optimized(
                all_texts, nlp, batch_size, n_processes, use_memory_zones
            )
            total_entities = sum(len(entity_list) for entity_list in entities.values())
        
        # Extract structural patterns (unchanged)
        for file_path, content, pages in documents:
            patterns = self.extract_structural_patterns(content)
            total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        processing_time = end_time - start_time
        pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
        memory_used = end_memory - start_memory
        
        result = OptimizedBenchmarkResult(
            configuration=config_name,
            pages_per_sec=pages_per_sec,
            processing_time=processing_time,
            total_pages=total_pages,
            entities_found=total_entities,
            patterns_matched=total_patterns,
            memory_usage_mb=memory_used,
            batch_size=batch_size,
            n_processes=n_processes,
            disabled_components=disabled_components or []
        )
        
        # Display results
        status = "✅" if pages_per_sec >= 1000 else "⚠️" if pages_per_sec >= 500 else "❌"
        print(f"{status} Performance: {pages_per_sec:.1f} pages/sec")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Entities found: {total_entities}")
        print(f"   Patterns matched: {total_patterns}")
        print(f"   Memory used: {memory_used:.1f} MB")
        
        return result
    
    def run_comprehensive_benchmark(self, document_limit: int = 20):
        """Run comprehensive optimized benchmark."""
        print("🚀 OPTIMIZED SPACY BENCHMARK")
        print("=" * 60)
        print(f"Target: 1,000+ pages/second with FULL optimization")
        print(f"CPUs: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print("=" * 60)
        
        # Load test documents
        documents = self.load_test_documents(document_limit)
        if not documents:
            print("❌ No documents to test with")
            return
        
        # Setup optimized models
        models = self.setup_optimized_spacy_models()
        
        # Test configurations with performance optimizations
        test_configs = []
        
        if models:
            # Minimal NER with different batch sizes
            test_configs.extend([
                ("Minimal NER (batch=500)", models['minimal_ner'], 500, 1, False),
                ("Minimal NER (batch=1000)", models['minimal_ner'], 1000, 1, False), 
                ("Minimal NER (batch=2000)", models['minimal_ner'], 2000, 1, False),
                ("Minimal NER (batch=5000)", models['minimal_ner'], 5000, 1, False),
            ])
            
            # Memory zones optimization
            test_configs.extend([
                ("Memory Zones (batch=2000)", models['memory_optimized'], 2000, 1, True),
                ("Memory Zones (batch=5000)", models['memory_optimized'], 5000, 1, True),
            ])
            
            # Multi-processing (if safe)
            cpu_count = psutil.cpu_count()
            if cpu_count > 2:
                test_configs.extend([
                    (f"Multi-Process 2 CPUs (batch=2000)", models['batch_optimized'], 2000, 2, False),
                    (f"Multi-Process {cpu_count//2} CPUs (batch=2000)", models['batch_optimized'], 2000, cpu_count//2, False),
                ])
        
        # Baseline comparisons
        test_configs.extend([
            ("Regex Patterns Only", None, 0, 0, False),
            ("No Enhancement (Baseline)", None, 0, 0, False),
        ])
        
        # Run benchmarks
        for config_name, nlp_model, batch_size, n_processes, use_memory_zones in test_configs:
            try:
                disabled_components = ["tagger", "parser", "lemmatizer", "attribute_ruler"] if nlp_model else []
                
                if nlp_model is None:
                    # Handle regex-only and baseline tests
                    if "Regex" in config_name:
                        result = self.run_optimized_benchmark(
                            documents, config_name, None, 0, 0, False, disabled_components
                        )
                    else:  # Baseline
                        result = self.run_optimized_benchmark(
                            documents, config_name, None, 0, 0, False, []
                        )
                else:
                    result = self.run_optimized_benchmark(
                        documents, config_name, nlp_model, batch_size, n_processes, 
                        use_memory_zones, disabled_components
                    )
                    
                self.results.append(result)
                
            except Exception as e:
                print(f"❌ {config_name} failed: {e}")
        
        # Summary results
        self.print_optimized_summary()
        self.save_optimized_results()
    
    def print_optimized_summary(self):
        """Print optimized benchmark summary."""
        if not self.results:
            return
            
        print("\n📊 OPTIMIZED BENCHMARK SUMMARY")
        print("=" * 90)
        print(f"{'Configuration':<35} {'Pages/Sec':<12} {'Entities':<10} {'Patterns':<10} {'Memory':<10} {'Batch':<8}")
        print("─" * 90)
        
        for result in sorted(self.results, key=lambda x: x.pages_per_sec, reverse=True):
            status = "🟢" if result.pages_per_sec >= 1000 else "🟡" if result.pages_per_sec >= 500 else "🔴"
            batch_info = f"{result.batch_size}" if result.batch_size > 0 else "N/A"
            print(f"{result.configuration:<35} {result.pages_per_sec:>8.1f} {status}   "
                  f"{result.entities_found:>7}   {result.patterns_matched:>7}   "
                  f"{result.memory_usage_mb:>6.1f}MB   {batch_info:<6}")
        
        # Best performers
        spacy_results = [r for r in self.results if r.entities_found > 0]
        if spacy_results:
            best_spacy = max(spacy_results, key=lambda x: x.pages_per_sec)
            print(f"\n🏆 Best spaCy Performance: {best_spacy.configuration} at {best_spacy.pages_per_sec:.1f} pages/sec")
            
            viable_spacy = [r for r in spacy_results if r.pages_per_sec >= 1000]
            if viable_spacy:
                print(f"✅ VIABLE spaCy configs found: {len(viable_spacy)}")
                for r in viable_spacy:
                    print(f"   • {r.configuration}: {r.pages_per_sec:.1f} pages/sec")
            else:
                print("❌ No spaCy configuration meets 1000+ pages/sec target")
        
        print("\n💡 OPTIMIZATION INSIGHTS:")
        if spacy_results:
            batch_perf = {}
            for r in spacy_results:
                batch_perf[r.batch_size] = batch_perf.get(r.batch_size, []) + [r.pages_per_sec]
            
            for batch_size, speeds in batch_perf.items():
                avg_speed = sum(speeds) / len(speeds)
                print(f"   📦 Batch size {batch_size}: avg {avg_speed:.1f} pages/sec")
    
    def save_optimized_results(self):
        """Save optimized benchmark results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"/home/corey/projects/docling/mvp-hyper/benchmarks/optimized_spacy_results_{timestamp}.json")
        
        results_data = {
            'timestamp': timestamp,
            'optimization_focus': 'spaCy performance tuning with Context7 recommendations',
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
                    'batch_size': r.batch_size,
                    'n_processes': r.n_processes,
                    'disabled_components': r.disabled_components
                }
                for r in self.results
            ]
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\n💾 Optimized results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Run the optimized spaCy benchmark."""
    if len(sys.argv) > 1:
        document_limit = int(sys.argv[1])
    else:
        document_limit = 15
        
    benchmark = OptimizedSpacyBenchmark()
    benchmark.run_comprehensive_benchmark(document_limit)


if __name__ == "__main__":
    main()