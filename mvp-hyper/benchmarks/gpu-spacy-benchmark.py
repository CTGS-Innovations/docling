#!/usr/bin/env python3
"""
GPU spaCy Benchmark
==================
Test spaCy NER performance with GPU acceleration vs CPU
"""

import time
import psutil
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime
import sys
from dataclasses import dataclass

# Try importing required libraries
try:
    import spacy
    from thinc.api import require_gpu, prefer_gpu, require_cpu, set_gpu_allocator
    import cupy
    HAS_GPU_SUPPORT = True
    print(f"✅ GPU support available - CuPy: {cupy.__version__}")
except ImportError as e:
    print(f"❌ GPU support not available: {e}")
    HAS_GPU_SUPPORT = False


@dataclass
class GPUBenchmarkResult:
    """Results from GPU vs CPU benchmark."""
    configuration: str
    device: str  # 'GPU' or 'CPU'
    pages_per_sec: float
    processing_time: float
    total_pages: int
    entities_found: int
    patterns_matched: int
    memory_usage_mb: float
    batch_size: int
    gpu_activated: bool


class GPUSpacyBenchmark:
    """Benchmark spaCy with GPU vs CPU for NER performance."""
    
    def __init__(self, markdown_dir: Path = None):
        self.markdown_dir = markdown_dir or Path("/home/corey/projects/docling/mvp-hyper/output/pipeline/1-markdown")
        self.results = []
        
        # Structural patterns for comparison
        self.structural_patterns = {
            'requirements': re.compile(r'\b(must|shall|required to|should|will|cannot|may not)\s+([^.!?]{15,100})', re.IGNORECASE),
            'conditionals': re.compile(r'\b(if|when|unless|provided that|in case)\s+([^,]{10,60})', re.IGNORECASE), 
            'measurements': re.compile(r'(\d+(?:\.\d+)?)\s*(percent|%|dollars?|\$|hours?|days?|years?|times?)', re.IGNORECASE),
            'authorities': re.compile(r'\b(CFR|USC|ISO|ANSI|NFPA|OSHA)\s+\d+(?:[-.]?\d+)*', re.IGNORECASE),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_numbers': re.compile(r'\b(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'),
        }
        
    def setup_gpu_model(self):
        """Setup spaCy model with GPU acceleration."""
        if not HAS_GPU_SUPPORT:
            print("❌ GPU support not available")
            return None
            
        try:
            # Force GPU allocation
            print("🎮 Setting up GPU acceleration...")
            require_gpu()
            
            # Load model with GPU
            nlp = spacy.load("en_core_web_sm")
            
            # Optimize for NER only
            nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            
            # Add doc cleaner
            nlp.add_pipe("doc_cleaner", config={"attrs": {"tensor": None}})
            
            print("✅ GPU model setup successful")
            return nlp
            
        except Exception as e:
            print(f"❌ GPU model setup failed: {e}")
            return None
    
    def setup_cpu_model(self):
        """Setup spaCy model for CPU processing."""
        try:
            print("🖥️  Setting up CPU model...")
            require_cpu()
            
            # Load model
            nlp = spacy.load("en_core_web_sm")
            
            # Optimize for NER only
            nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
            
            # Add doc cleaner
            nlp.add_pipe("doc_cleaner", config={"attrs": {"tensor": None}})
            
            print("✅ CPU model setup successful")
            return nlp
            
        except Exception as e:
            print(f"❌ CPU model setup failed: {e}")
            return None
    
    def load_test_documents(self, limit: int = 15) -> List[Tuple[Path, str, int]]:
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
    
    def extract_entities_gpu_test(self, texts: List[str], nlp, batch_size: int = 2000) -> Dict[str, List[str]]:
        """Extract entities for GPU/CPU testing."""
        entities = {
            'persons': set(),
            'organizations': set(), 
            'locations': set(),
            'money': set(),
            'dates': set(),
            'quantities': set()
        }
        
        # Use memory zones for efficient processing
        with nlp.memory_zone():
            docs = nlp.pipe(texts, batch_size=batch_size)
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
        """Extract structural patterns using regex."""
        patterns_found = {}
        
        for pattern_name, pattern_regex in self.structural_patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                if pattern_name in ['requirements', 'conditionals']:
                    patterns_found[pattern_name] = [f"{m[0]} {m[1]}" for m in matches if len(m) > 1]
                else:
                    patterns_found[pattern_name] = [m if isinstance(m, str) else ' '.join(m) for m in matches]
        
        return patterns_found
    
    def run_device_benchmark(self, documents: List[Tuple[Path, str, int]], 
                           config_name: str, nlp, device: str, 
                           batch_size: int = 2000) -> GPUBenchmarkResult:
        """Run benchmark on specific device (GPU or CPU)."""
        print(f"\n🧪 Testing: {config_name} on {device}")
        print("─" * 50)
        print(f"   Device: {device}")
        print(f"   Batch size: {batch_size}")
        
        # Check if GPU is actually activated
        gpu_activated = False
        if HAS_GPU_SUPPORT:
            try:
                # Test if we can use GPU operations
                import cupy as cp
                test_array = cp.array([1, 2, 3])
                gpu_activated = True
                print(f"   GPU Status: ✅ Active")
            except:
                print(f"   GPU Status: ❌ Not active")
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        total_entities = 0
        total_patterns = 0
        total_pages = sum(doc[2] for doc in documents)
        
        # Prepare texts for batch processing
        all_texts = [content for _, content, _ in documents]
        
        # Extract spaCy entities
        if nlp is not None:
            entities = self.extract_entities_gpu_test(all_texts, nlp, batch_size)
            total_entities = sum(len(entity_list) for entity_list in entities.values())
        
        # Extract structural patterns
        for file_path, content, pages in documents:
            patterns = self.extract_structural_patterns(content)
            total_patterns += sum(len(pattern_list) for pattern_list in patterns.values())
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        processing_time = end_time - start_time
        pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
        memory_used = end_memory - start_memory
        
        result = GPUBenchmarkResult(
            configuration=config_name,
            device=device,
            pages_per_sec=pages_per_sec,
            processing_time=processing_time,
            total_pages=total_pages,
            entities_found=total_entities,
            patterns_matched=total_patterns,
            memory_usage_mb=memory_used,
            batch_size=batch_size,
            gpu_activated=gpu_activated
        )
        
        # Display results
        status = "✅" if pages_per_sec >= 1000 else "⚠️" if pages_per_sec >= 500 else "❌"
        print(f"{status} Performance: {pages_per_sec:.1f} pages/sec")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Entities found: {total_entities}")
        print(f"   Patterns matched: {total_patterns}")
        print(f"   Memory used: {memory_used:.1f} MB")
        print(f"   GPU Active: {gpu_activated}")
        
        return result
    
    def run_gpu_vs_cpu_benchmark(self, document_limit: int = 15):
        """Run comprehensive GPU vs CPU benchmark."""
        print("🚀 GPU vs CPU SPACY BENCHMARK")
        print("=" * 60)
        print(f"Target: Test if GPU can achieve 1,000+ pages/second")
        print(f"CPUs: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print(f"GPU Support: {HAS_GPU_SUPPORT}")
        print("=" * 60)
        
        # Load test documents
        documents = self.load_test_documents(document_limit)
        if not documents:
            print("❌ No documents to test with")
            return
        
        # Test configurations
        test_configs = []
        
        # GPU tests (if available)
        if HAS_GPU_SUPPORT:
            gpu_model = self.setup_gpu_model()
            if gpu_model:
                test_configs.extend([
                    ("NER-Only GPU (batch=1000)", gpu_model, "GPU", 1000),
                    ("NER-Only GPU (batch=2000)", gpu_model, "GPU", 2000),
                    ("NER-Only GPU (batch=5000)", gpu_model, "GPU", 5000),
                ])
        
        # CPU tests for comparison
        cpu_model = self.setup_cpu_model()
        if cpu_model:
            test_configs.extend([
                ("NER-Only CPU (batch=1000)", cpu_model, "CPU", 1000),
                ("NER-Only CPU (batch=2000)", cpu_model, "CPU", 2000),
                ("NER-Only CPU (batch=5000)", cpu_model, "CPU", 5000),
            ])
        
        # Baseline tests
        test_configs.extend([
            ("Regex Patterns Only", None, "CPU", 0),
        ])
        
        # Run benchmarks
        for config_name, nlp_model, device, batch_size in test_configs:
            try:
                if nlp_model is None:
                    # Handle regex-only test
                    result = self.run_device_benchmark(
                        documents, config_name, None, device, batch_size
                    )
                else:
                    result = self.run_device_benchmark(
                        documents, config_name, nlp_model, device, batch_size
                    )
                    
                self.results.append(result)
                
            except Exception as e:
                print(f"❌ {config_name} failed: {e}")
        
        # Summary results
        self.print_gpu_summary()
        self.save_gpu_results()
    
    def print_gpu_summary(self):
        """Print GPU vs CPU benchmark summary."""
        if not self.results:
            return
            
        print("\n📊 GPU vs CPU BENCHMARK SUMMARY")
        print("=" * 95)
        print(f"{'Configuration':<35} {'Device':<6} {'Pages/Sec':<12} {'Entities':<10} {'GPU':<6} {'Memory':<10}")
        print("─" * 95)
        
        for result in sorted(self.results, key=lambda x: x.pages_per_sec, reverse=True):
            status = "🟢" if result.pages_per_sec >= 1000 else "🟡" if result.pages_per_sec >= 500 else "🔴"
            gpu_status = "✅" if result.gpu_activated else "❌"
            print(f"{result.configuration:<35} {result.device:<6} {result.pages_per_sec:>8.1f} {status}   "
                  f"{result.entities_found:>7}   {gpu_status:<6}   {result.memory_usage_mb:>6.1f}MB")
        
        # GPU vs CPU comparison
        gpu_results = [r for r in self.results if r.device == "GPU" and r.entities_found > 0]
        cpu_results = [r for r in self.results if r.device == "CPU" and r.entities_found > 0]
        
        if gpu_results and cpu_results:
            best_gpu = max(gpu_results, key=lambda x: x.pages_per_sec)
            best_cpu = max(cpu_results, key=lambda x: x.pages_per_sec)
            
            print(f"\n🎮 GPU vs CPU COMPARISON:")
            print(f"   Best GPU: {best_gpu.pages_per_sec:.1f} pages/sec")
            print(f"   Best CPU: {best_cpu.pages_per_sec:.1f} pages/sec")
            
            if best_gpu.pages_per_sec > best_cpu.pages_per_sec:
                speedup = best_gpu.pages_per_sec / best_cpu.pages_per_sec
                print(f"   🚀 GPU Speedup: {speedup:.2f}x faster")
            else:
                slowdown = best_cpu.pages_per_sec / best_gpu.pages_per_sec
                print(f"   🐌 GPU Slower: {slowdown:.2f}x slower")
        
        # Target achievement
        viable_configs = [r for r in self.results if r.pages_per_sec >= 1000]
        if viable_configs:
            print(f"\n✅ CONFIGS MEETING 1000+ pages/sec TARGET:")
            for r in viable_configs:
                print(f"   • {r.configuration} ({r.device}): {r.pages_per_sec:.1f} pages/sec")
        else:
            print(f"\n❌ NO CONFIGS MEET 1000+ pages/sec TARGET")
            best_spacy = max([r for r in self.results if r.entities_found > 0], key=lambda x: x.pages_per_sec)
            print(f"   Best spaCy: {best_spacy.configuration} ({best_spacy.device}): {best_spacy.pages_per_sec:.1f} pages/sec")
    
    def save_gpu_results(self):
        """Save GPU benchmark results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"/home/corey/projects/docling/mvp-hyper/benchmarks/gpu_spacy_results_{timestamp}.json")
        
        results_data = {
            'timestamp': timestamp,
            'focus': 'GPU vs CPU spaCy performance comparison',
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'gpu_support': HAS_GPU_SUPPORT,
                'spacy_version': spacy.__version__ if 'spacy' in globals() else 'N/A'
            },
            'results': [
                {
                    'configuration': r.configuration,
                    'device': r.device,
                    'pages_per_sec': r.pages_per_sec,
                    'processing_time': r.processing_time,
                    'total_pages': r.total_pages,
                    'entities_found': r.entities_found,
                    'patterns_matched': r.patterns_matched,
                    'memory_usage_mb': r.memory_usage_mb,
                    'batch_size': r.batch_size,
                    'gpu_activated': r.gpu_activated
                }
                for r in self.results
            ]
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\n💾 GPU benchmark results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Run the GPU vs CPU spaCy benchmark."""
    if len(sys.argv) > 1:
        document_limit = int(sys.argv[1])
    else:
        document_limit = 15
        
    benchmark = GPUSpacyBenchmark()
    benchmark.run_gpu_vs_cpu_benchmark(document_limit)


if __name__ == "__main__":
    main()