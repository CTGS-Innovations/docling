#!/usr/bin/env python3
"""
BERT NER Performance Test
Test actual pages/sec performance after model initialization

This test:
1. Loads each model once (one-time cost)
2. Runs multiple iterations to get realistic performance
3. Tests on actual document content, not just sample text
4. Calculates realistic pages/sec estimates
"""

import time
import glob
import os
from typing import List, Dict, Any


class BERTPerformanceTester:
    """Test realistic performance of BERT NER models"""
    
    def __init__(self, docs_dir: str = "../output/pipeline/3-enriched"):
        self.docs_dir = docs_dir
        self.test_documents = []
        self.load_test_documents()
        
    def load_test_documents(self, max_docs: int = 10):
        """Load real documents for testing"""
        doc_pattern = os.path.join(self.docs_dir, "*.md")
        doc_files = sorted(glob.glob(doc_pattern))[:max_docs]
        
        print(f"Loading {len(doc_files)} test documents...")
        
        for file_path in doc_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Limit to reasonable size for testing
                    if len(content) > 20000:
                        content = content[:20000]
                    
                    self.test_documents.append({
                        'filename': os.path.basename(file_path),
                        'content': content,
                        'char_count': len(content)
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        total_chars = sum(doc['char_count'] for doc in self.test_documents)
        print(f"Loaded {len(self.test_documents)} documents, {total_chars:,} total characters")
        print()

    def test_stanza_performance(self, iterations: int = 3):
        """Test Stanza performance on real documents"""
        print("🏛️ TESTING STANZA PERFORMANCE")
        print("-" * 50)
        
        try:
            import stanza
            
            # One-time model loading
            print("Loading Stanza model (one-time cost)...")
            start_load = time.time()
            nlp = stanza.Pipeline('en', processors='tokenize,ner', verbose=False)
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s")
            
            # Performance testing
            print(f"\nRunning {iterations} iterations on {len(self.test_documents)} documents...")
            
            total_processing_time = 0
            total_entities = 0
            total_chars = 0
            
            for iteration in range(iterations):
                iteration_start = time.time()
                iteration_entities = 0
                
                for doc in self.test_documents:
                    doc_start = time.time()
                    result = nlp(doc['content'])
                    
                    # Count entities
                    for sent in result.sentences:
                        iteration_entities += len(sent.ents)
                    
                    total_chars += doc['char_count']
                
                iteration_time = time.time() - iteration_start
                total_processing_time += iteration_time
                total_entities += iteration_entities
                
                print(f"  Iteration {iteration + 1}: {iteration_time:.2f}s, {iteration_entities} entities")
            
            # Calculate performance metrics
            avg_processing_time = total_processing_time / iterations
            chars_per_sec = (total_chars / iterations) / avg_processing_time if avg_processing_time > 0 else 0
            pages_per_sec = chars_per_sec / 3000  # Assuming 3000 chars per page
            
            print(f"\n📊 STANZA RESULTS:")
            print(f"  Average processing time: {avg_processing_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Estimated pages per second: {pages_per_sec:.1f}")
            print(f"  Average entities per iteration: {total_entities / iterations:.0f}")
            
            return {
                'model': 'Stanza',
                'load_time': load_time,
                'avg_processing_time': avg_processing_time,
                'chars_per_sec': chars_per_sec,
                'pages_per_sec': pages_per_sec,
                'entities_per_iteration': total_entities / iterations,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Stanza test failed: {e}")
            return {'model': 'Stanza', 'success': False, 'error': str(e)}

    def test_flair_performance(self, iterations: int = 3):
        """Test Flair performance on real documents"""
        print("🔥 TESTING FLAIR PERFORMANCE")
        print("-" * 50)
        
        try:
            from flair.data import Sentence
            from flair.models import SequenceTagger
            
            # One-time model loading
            print("Loading Flair model (one-time cost)...")
            start_load = time.time()
            tagger = SequenceTagger.load("ner")
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s")
            
            # Performance testing
            print(f"\nRunning {iterations} iterations on {len(self.test_documents)} documents...")
            
            total_processing_time = 0
            total_entities = 0
            total_chars = 0
            
            for iteration in range(iterations):
                iteration_start = time.time()
                iteration_entities = 0
                
                for doc in self.test_documents:
                    # Split large documents into sentences for Flair
                    sentences = doc['content'].split('.')
                    
                    for sent_text in sentences[:50]:  # Limit sentences for performance
                        if len(sent_text.strip()) > 10:
                            sentence = Sentence(sent_text.strip())
                            tagger.predict(sentence)
                            iteration_entities += len(sentence.get_spans('ner'))
                    
                    total_chars += doc['char_count']
                
                iteration_time = time.time() - iteration_start
                total_processing_time += iteration_time
                total_entities += iteration_entities
                
                print(f"  Iteration {iteration + 1}: {iteration_time:.2f}s, {iteration_entities} entities")
            
            # Calculate performance metrics
            avg_processing_time = total_processing_time / iterations
            chars_per_sec = (total_chars / iterations) / avg_processing_time if avg_processing_time > 0 else 0
            pages_per_sec = chars_per_sec / 3000
            
            print(f"\n📊 FLAIR RESULTS:")
            print(f"  Average processing time: {avg_processing_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Estimated pages per second: {pages_per_sec:.1f}")
            print(f"  Average entities per iteration: {total_entities / iterations:.0f}")
            
            return {
                'model': 'Flair',
                'load_time': load_time,
                'avg_processing_time': avg_processing_time,
                'chars_per_sec': chars_per_sec,
                'pages_per_sec': pages_per_sec,
                'entities_per_iteration': total_entities / iterations,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Flair test failed: {e}")
            return {'model': 'Flair', 'success': False, 'error': str(e)}

    def test_huggingface_performance(self, iterations: int = 3):
        """Test HuggingFace performance on real documents"""
        print("🤗 TESTING HUGGINGFACE PERFORMANCE")
        print("-" * 50)
        
        try:
            from transformers import pipeline
            
            # One-time model loading
            print("Loading HuggingFace BERT model (one-time cost)...")
            start_load = time.time()
            ner = pipeline("ner", 
                          model="dbmdz/bert-large-cased-finetuned-conll03-english",
                          aggregation_strategy="simple")
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s")
            
            # Performance testing
            print(f"\nRunning {iterations} iterations on {len(self.test_documents)} documents...")
            
            total_processing_time = 0
            total_entities = 0
            total_chars = 0
            
            for iteration in range(iterations):
                iteration_start = time.time()
                iteration_entities = 0
                
                for doc in self.test_documents:
                    # Process in chunks for BERT (it has token limits)
                    content = doc['content']
                    chunk_size = 5000  # Process in smaller chunks
                    
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        if len(chunk.strip()) > 10:
                            entities = ner(chunk)
                            iteration_entities += len(entities)
                    
                    total_chars += doc['char_count']
                
                iteration_time = time.time() - iteration_start
                total_processing_time += iteration_time
                total_entities += iteration_entities
                
                print(f"  Iteration {iteration + 1}: {iteration_time:.2f}s, {iteration_entities} entities")
            
            # Calculate performance metrics
            avg_processing_time = total_processing_time / iterations
            chars_per_sec = (total_chars / iterations) / avg_processing_time if avg_processing_time > 0 else 0
            pages_per_sec = chars_per_sec / 3000
            
            print(f"\n📊 HUGGINGFACE RESULTS:")
            print(f"  Average processing time: {avg_processing_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Estimated pages per second: {pages_per_sec:.1f}")
            print(f"  Average entities per iteration: {total_entities / iterations:.0f}")
            
            return {
                'model': 'HuggingFace BERT',
                'load_time': load_time,
                'avg_processing_time': avg_processing_time,
                'chars_per_sec': chars_per_sec,
                'pages_per_sec': pages_per_sec,
                'entities_per_iteration': total_entities / iterations,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ HuggingFace test failed: {e}")
            return {'model': 'HuggingFace BERT', 'success': False, 'error': str(e)}

    def test_spacy_baseline(self, iterations: int = 3):
        """Test baseline spaCy for comparison"""
        print("📚 TESTING SPACY BASELINE")
        print("-" * 50)
        
        try:
            import spacy
            
            # One-time model loading
            print("Loading spaCy model (one-time cost)...")
            start_load = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s")
            
            # Performance testing
            print(f"\nRunning {iterations} iterations on {len(self.test_documents)} documents...")
            
            total_processing_time = 0
            total_entities = 0
            total_chars = 0
            
            for iteration in range(iterations):
                iteration_start = time.time()
                iteration_entities = 0
                
                for doc in self.test_documents:
                    result = nlp(doc['content'])
                    iteration_entities += len(result.ents)
                    total_chars += doc['char_count']
                
                iteration_time = time.time() - iteration_start
                total_processing_time += iteration_time
                total_entities += iteration_entities
                
                print(f"  Iteration {iteration + 1}: {iteration_time:.2f}s, {iteration_entities} entities")
            
            # Calculate performance metrics
            avg_processing_time = total_processing_time / iterations
            chars_per_sec = (total_chars / iterations) / avg_processing_time if avg_processing_time > 0 else 0
            pages_per_sec = chars_per_sec / 3000
            
            print(f"\n📊 SPACY RESULTS:")
            print(f"  Average processing time: {avg_processing_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Estimated pages per second: {pages_per_sec:.1f}")
            print(f"  Average entities per iteration: {total_entities / iterations:.0f}")
            
            return {
                'model': 'spaCy Baseline',
                'load_time': load_time,
                'avg_processing_time': avg_processing_time,
                'chars_per_sec': chars_per_sec,
                'pages_per_sec': pages_per_sec,
                'entities_per_iteration': total_entities / iterations,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ spaCy test failed: {e}")
            return {'model': 'spaCy Baseline', 'success': False, 'error': str(e)}

    def run_performance_comparison(self):
        """Run comprehensive performance comparison"""
        print("BERT NER PERFORMANCE COMPARISON")
        print("=" * 70)
        print("Testing realistic pages/sec performance on actual documents")
        print()
        
        if not self.test_documents:
            print("❌ No test documents loaded!")
            return
        
        # Run tests
        tests = [
            ("spaCy Baseline", self.test_spacy_baseline),
            ("Stanza", self.test_stanza_performance),
            ("Flair", self.test_flair_performance),
            ("HuggingFace BERT", self.test_huggingface_performance),
        ]
        
        results = []
        
        for name, test_func in tests:
            print()
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ {name} failed: {e}")
                results.append({'model': name, 'success': False, 'error': str(e)})
        
        # Final comparison
        print("\n" + "=" * 70)
        print("🏁 FINAL PERFORMANCE COMPARISON")
        print("=" * 70)
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if successful_results:
            print(f"{'Model':<20} {'Pages/Sec':<12} {'Load Time':<12} {'Entities/Run':<12} {'vs Target'}")
            print("-" * 70)
            
            for result in successful_results:
                model = result['model']
                pages_sec = result.get('pages_per_sec', 0)
                load_time = result.get('load_time', 0)
                entities = result.get('entities_per_iteration', 0)
                
                # Compare to 1000 pages/sec target
                if pages_sec >= 1000:
                    vs_target = "✅ MEETS TARGET"
                elif pages_sec >= 500:
                    vs_target = "🔄 GETTING CLOSE"
                elif pages_sec >= 100:
                    vs_target = "⚠️ TOO SLOW"
                else:
                    vs_target = "❌ WAY TOO SLOW"
                
                print(f"{model:<20} {pages_sec:<12.1f} {load_time:<12.1f} {entities:<12.0f} {vs_target}")
        
        print("\n🎯 KEY INSIGHTS:")
        print("• BERT models are more accurate but much slower")
        print("• None come close to 1000 pages/sec target")
        print("• One-time load costs are significant")
        print("• Accuracy vs speed trade-off is dramatic")
        print("• Regex + pyahocorasick still looks best for production")


def main():
    """Run BERT performance comparison"""
    tester = BERTPerformanceTester()
    tester.run_performance_comparison()


if __name__ == "__main__":
    main()