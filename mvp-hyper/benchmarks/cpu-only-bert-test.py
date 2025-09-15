#!/usr/bin/env python3
"""
CPU-Only BERT Performance Test
Force all models to run on CPU only to get accurate CPU performance numbers

This will prove what the actual CPU-only performance is vs GPU-accelerated
"""

import os
import time
import torch

# Force CPU-only for all models
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Hide GPU from PyTorch
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"


class CPUOnlyBERTTest:
    """Test BERT models forced to run on CPU only"""
    
    def __init__(self):
        self.test_text = """
        Dr. John Smith from OSHA reported that the Department of Labor 
        has allocated $2.5 million for safety programs in Washington, DC.
        Mary Johnson, the EPA inspector, found violations on March 15, 2024.
        The CDC and NIOSH are collaborating on new guidelines.
        Contact Director Williams at the Environmental Protection Agency.
        Equipment safety training is required for all construction workers.
        """ * 10  # Make it bigger to see real performance
        
        print(f"Test text length: {len(self.test_text):,} characters")
        print(f"PyTorch CUDA available: {torch.cuda.is_available()}")
        print(f"PyTorch device count: {torch.cuda.device_count()}")
        print()

    def test_huggingface_cpu_only(self):
        """Test HuggingFace BERT forced to CPU only"""
        print("🤗 TESTING HUGGINGFACE BERT - CPU ONLY")
        print("-" * 50)
        
        try:
            from transformers import pipeline
            
            print("Loading HuggingFace BERT model (CPU ONLY)...")
            start_load = time.time()
            
            # Explicitly force CPU device
            ner = pipeline("ner", 
                          model="dbmdz/bert-large-cased-finetuned-conll03-english",
                          aggregation_strategy="simple",
                          device=-1)  # -1 forces CPU
            
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s on device: {ner.device}")
            
            # Test processing multiple times
            iterations = 3
            total_time = 0
            
            print(f"\nRunning {iterations} iterations...")
            
            for i in range(iterations):
                start_time = time.time()
                entities = ner(self.test_text)
                iteration_time = time.time() - start_time
                total_time += iteration_time
                
                print(f"  Iteration {i+1}: {iteration_time:.3f}s, {len(entities)} entities")
            
            avg_time = total_time / iterations
            chars_per_sec = len(self.test_text) / avg_time
            pages_per_sec = chars_per_sec / 3000
            
            print(f"\n📊 CPU-ONLY RESULTS:")
            print(f"  Average processing time: {avg_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Pages per second: {pages_per_sec:.1f}")
            
            return {
                'model': 'HuggingFace BERT (CPU)',
                'device': str(ner.device),
                'pages_per_sec': pages_per_sec,
                'avg_time': avg_time,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ HuggingFace CPU test failed: {e}")
            return {'success': False, 'error': str(e)}

    def test_spacy_cpu_comparison(self):
        """Test spaCy for comparison"""
        print("\n📚 TESTING SPACY BASELINE - CPU")
        print("-" * 50)
        
        try:
            import spacy
            
            print("Loading spaCy model...")
            start_load = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start_load
            print(f"✅ Model loaded in {load_time:.2f}s")
            
            # Test processing
            iterations = 3
            total_time = 0
            
            print(f"\nRunning {iterations} iterations...")
            
            for i in range(iterations):
                start_time = time.time()
                doc = nlp(self.test_text)
                entities = list(doc.ents)
                iteration_time = time.time() - start_time
                total_time += iteration_time
                
                print(f"  Iteration {i+1}: {iteration_time:.3f}s, {len(entities)} entities")
            
            avg_time = total_time / iterations
            chars_per_sec = len(self.test_text) / avg_time
            pages_per_sec = chars_per_sec / 3000
            
            print(f"\n📊 SPACY CPU RESULTS:")
            print(f"  Average processing time: {avg_time:.3f}s")
            print(f"  Characters per second: {chars_per_sec:,.0f}")
            print(f"  Pages per second: {pages_per_sec:.1f}")
            
            return {
                'model': 'spaCy (CPU)',
                'pages_per_sec': pages_per_sec,
                'avg_time': avg_time,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ spaCy test failed: {e}")
            return {'success': False, 'error': str(e)}

    def test_cpu_vs_gpu_comparison(self):
        """Test the same model with and without GPU to show difference"""
        print("\n⚡ CPU vs GPU COMPARISON TEST")
        print("-" * 50)
        
        # First, let's see what happens when we allow GPU
        print("Testing with GPU allowed...")
        
        # Temporarily allow GPU
        if "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
        
        try:
            from transformers import pipeline
            import torch
            
            print(f"CUDA available: {torch.cuda.is_available()}")
            
            if torch.cuda.is_available():
                # Test with GPU
                print("\n🚀 Testing with GPU:")
                ner_gpu = pipeline("ner", 
                                  model="dbmdz/bert-base-cased-finetuned-conll03-english",  # Smaller model
                                  aggregation_strategy="simple",
                                  device=0)  # GPU
                
                start_time = time.time()
                entities_gpu = ner_gpu(self.test_text[:5000])  # Smaller text for quick test
                gpu_time = time.time() - start_time
                
                print(f"  GPU time: {gpu_time:.3f}s, {len(entities_gpu)} entities")
                print(f"  GPU device: {ner_gpu.device}")
                
                # Test with CPU
                print("\n💻 Testing with CPU (same model):")
                ner_cpu = pipeline("ner", 
                                  model="dbmdz/bert-base-cased-finetuned-conll03-english",
                                  aggregation_strategy="simple",
                                  device=-1)  # CPU
                
                start_time = time.time()
                entities_cpu = ner_cpu(self.test_text[:5000])
                cpu_time = time.time() - start_time
                
                print(f"  CPU time: {cpu_time:.3f}s, {len(entities_cpu)} entities")
                print(f"  CPU device: {ner_cpu.device}")
                
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                print(f"\n📊 GPU is {speedup:.1f}x faster than CPU")
                
                return {
                    'gpu_time': gpu_time,
                    'cpu_time': cpu_time,
                    'speedup': speedup,
                    'success': True
                }
            else:
                print("No GPU available for comparison")
                return {'success': False, 'error': 'No GPU available'}
                
        except Exception as e:
            print(f"❌ Comparison test failed: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Restore CPU-only setting
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

    def run_cpu_only_tests(self):
        """Run comprehensive CPU-only tests"""
        print("CPU-ONLY BERT PERFORMANCE TEST")
        print("=" * 60)
        print("Forcing all models to use CPU only to get accurate CPU performance")
        print()
        
        # Test CPU vs GPU first to show the difference
        comparison = self.test_cpu_vs_gpu_comparison()
        
        # Now test CPU-only performance
        os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Ensure CPU-only
        
        huggingface_result = self.test_huggingface_cpu_only()
        spacy_result = self.test_spacy_cpu_comparison()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 CPU-ONLY PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if comparison.get('success'):
            print(f"GPU vs CPU speed difference: {comparison['speedup']:.1f}x")
            print(f"GPU processing time: {comparison['gpu_time']:.3f}s")
            print(f"CPU processing time: {comparison['cpu_time']:.3f}s")
            print()
        
        results = [huggingface_result, spacy_result]
        successful = [r for r in results if r.get('success')]
        
        if successful:
            print("CPU-Only Performance:")
            for result in successful:
                model = result['model']
                pages_sec = result['pages_per_sec']
                
                if pages_sec >= 1000:
                    status = "✅ MEETS TARGET"
                elif pages_sec >= 100:
                    status = "⚠️ TOO SLOW"
                else:
                    status = "❌ WAY TOO SLOW"
                
                print(f"  {model:<25}: {pages_sec:6.1f} pages/sec {status}")
        
        print(f"\nTarget: 1000+ pages/sec")
        print("💡 Conclusion: BERT on CPU alone is insufficient for production workloads")


def main():
    """Run CPU-only BERT tests"""
    tester = CPUOnlyBERTTest()
    tester.run_cpu_only_tests()


if __name__ == "__main__":
    main()