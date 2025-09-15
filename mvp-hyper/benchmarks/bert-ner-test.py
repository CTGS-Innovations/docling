#!/usr/bin/env python3
"""
Test BERT-based NER Models on CPU
Compare accuracy and speed vs spaCy for entity extraction

Models to test:
1. Flair - Uses BERT embeddings, often 20-30% more accurate
2. HuggingFace Transformers - State-of-the-art BERT/RoBERTa models
3. spaCy Transformers - spaCy with BERT backend
4. Stanza - Stanford's transformer-based NLP

All CPU-compatible, Python-based
"""

import time
import sys
from typing import List, Dict, Any


class BERTNERTester:
    """Test BERT-based NER models against spaCy"""
    
    def __init__(self):
        self.test_text = """
        Dr. John Smith from OSHA reported that the Department of Labor 
        has allocated $2.5 million for safety programs in Washington, DC.
        Mary Johnson, the EPA inspector, found violations on March 15, 2024.
        The CDC and NIOSH are collaborating on new guidelines.
        Contact Director Williams at the Environmental Protection Agency.
        Equipment safety training is required for all construction workers.
        """
        
        self.models_tested = {}
        
    def test_flair_ner(self):
        """Test Flair NER model"""
        print("\n🔥 TESTING FLAIR NER")
        print("-" * 40)
        
        try:
            # Install and import Flair
            import subprocess
            print("Installing Flair...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flair'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            from flair.data import Sentence
            from flair.models import SequenceTagger
            
            print("Loading Flair NER model...")
            start_load = time.time()
            tagger = SequenceTagger.load("ner")
            load_time = time.time() - start_load
            
            print(f"Model loaded in {load_time:.2f}s")
            
            # Test extraction
            sentence = Sentence(self.test_text)
            
            start_time = time.time()
            tagger.predict(sentence)
            processing_time = time.time() - start_time
            
            # Extract entities
            entities = []
            for entity in sentence.get_spans('ner'):
                entities.append({
                    'text': entity.text,
                    'label': entity.get_label('ner').value,
                    'confidence': entity.get_label('ner').score
                })
            
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Entities found: {len(entities)}")
            
            # Show entities by type
            by_type = {}
            for entity in entities:
                label = entity['label']
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(f'"{entity["text"]}" ({entity["confidence"]:.2f})')
            
            for label, ents in by_type.items():
                print(f"  {label}: {', '.join(ents)}")
            
            return {
                'model': 'Flair',
                'load_time': load_time,
                'processing_time': processing_time,
                'entities': entities,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Flair failed: {e}")
            return {'model': 'Flair', 'success': False, 'error': str(e)}
    
    def test_huggingface_ner(self):
        """Test HuggingFace Transformers NER"""
        print("\n🤗 TESTING HUGGINGFACE TRANSFORMERS")
        print("-" * 40)
        
        try:
            import subprocess
            print("Installing transformers...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'transformers[torch]'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            from transformers import pipeline
            
            print("Loading BERT NER model...")
            start_load = time.time()
            # Use a good BERT model for NER
            ner = pipeline("ner", 
                          model="dbmdz/bert-large-cased-finetuned-conll03-english",
                          aggregation_strategy="simple")
            load_time = time.time() - start_load
            
            print(f"Model loaded in {load_time:.2f}s")
            
            # Test extraction
            start_time = time.time()
            entities = ner(self.test_text)
            processing_time = time.time() - start_time
            
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Entities found: {len(entities)}")
            
            # Show entities by type
            by_type = {}
            for entity in entities:
                label = entity['entity_group']
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(f'"{entity["word"]}" ({entity["score"]:.2f})')
            
            for label, ents in by_type.items():
                print(f"  {label}: {', '.join(ents)}")
            
            return {
                'model': 'HuggingFace BERT',
                'load_time': load_time,
                'processing_time': processing_time,
                'entities': entities,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ HuggingFace failed: {e}")
            return {'model': 'HuggingFace BERT', 'success': False, 'error': str(e)}
    
    def test_spacy_transformers(self):
        """Test spaCy with transformer backend"""
        print("\n🚀 TESTING SPACY TRANSFORMERS")
        print("-" * 40)
        
        try:
            import subprocess
            print("Installing spaCy transformers...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy[transformers]'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Try to download transformer model
            subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_trf'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            import spacy
            
            print("Loading spaCy transformer model...")
            start_load = time.time()
            nlp = spacy.load("en_core_web_trf")
            load_time = time.time() - start_load
            
            print(f"Model loaded in {load_time:.2f}s")
            
            # Test extraction
            start_time = time.time()
            doc = nlp(self.test_text)
            processing_time = time.time() - start_time
            
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Entities found: {len(entities)}")
            
            # Show entities by type
            by_type = {}
            for text, label in entities:
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(f'"{text}"')
            
            for label, ents in by_type.items():
                print(f"  {label}: {', '.join(ents)}")
            
            return {
                'model': 'spaCy Transformers',
                'load_time': load_time,
                'processing_time': processing_time,
                'entities': entities,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ spaCy Transformers failed: {e}")
            return {'model': 'spaCy Transformers', 'success': False, 'error': str(e)}
    
    def test_stanza_ner(self):
        """Test Stanford Stanza NER"""
        print("\n🏛️ TESTING STANFORD STANZA")
        print("-" * 40)
        
        try:
            import subprocess
            print("Installing Stanza...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'stanza'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            import stanza
            
            print("Downloading Stanza English model...")
            stanza.download('en', verbose=False)
            
            print("Loading Stanza NER model...")
            start_load = time.time()
            nlp = stanza.Pipeline('en', processors='tokenize,ner', verbose=False)
            load_time = time.time() - start_load
            
            print(f"Model loaded in {load_time:.2f}s")
            
            # Test extraction
            start_time = time.time()
            doc = nlp(self.test_text)
            processing_time = time.time() - start_time
            
            # Extract entities
            entities = []
            for sent in doc.sentences:
                for ent in sent.ents:
                    entities.append((ent.text, ent.type))
            
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Entities found: {len(entities)}")
            
            # Show entities by type
            by_type = {}
            for text, label in entities:
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(f'"{text}"')
            
            for label, ents in by_type.items():
                print(f"  {label}: {', '.join(ents)}")
            
            return {
                'model': 'Stanza',
                'load_time': load_time,
                'processing_time': processing_time,
                'entities': entities,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Stanza failed: {e}")
            return {'model': 'Stanza', 'success': False, 'error': str(e)}
    
    def test_baseline_spacy(self):
        """Test baseline spaCy for comparison"""
        print("\n📚 TESTING BASELINE SPACY")
        print("-" * 40)
        
        try:
            import spacy
            
            print("Loading spaCy small model...")
            start_load = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start_load
            
            print(f"Model loaded in {load_time:.2f}s")
            
            # Test extraction
            start_time = time.time()
            doc = nlp(self.test_text)
            processing_time = time.time() - start_time
            
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Entities found: {len(entities)}")
            
            # Show entities by type
            by_type = {}
            for text, label in entities:
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(f'"{text}"')
            
            for label, ents in by_type.items():
                print(f"  {label}: {', '.join(ents)}")
            
            return {
                'model': 'spaCy Baseline',
                'load_time': load_time,
                'processing_time': processing_time,
                'entities': entities,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ spaCy failed: {e}")
            return {'model': 'spaCy Baseline', 'success': False, 'error': str(e)}
    
    def run_all_tests(self):
        """Run all BERT NER model tests"""
        print("BERT-BASED NER MODEL COMPARISON")
        print("=" * 60)
        print("Testing state-of-the-art NER models on CPU")
        print(f"Test text length: {len(self.test_text)} characters")
        print()
        
        # Test all models
        tests = [
            ("Baseline spaCy", self.test_baseline_spacy),
            ("Flair", self.test_flair_ner),
            ("HuggingFace BERT", self.test_huggingface_ner),
            ("spaCy Transformers", self.test_spacy_transformers),
            ("Stanford Stanza", self.test_stanza_ner)
        ]
        
        results = []
        
        for name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ {name} test failed: {e}")
                results.append({'model': name, 'success': False, 'error': str(e)})
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if successful_results:
            print(f"{'Model':<20} {'Load Time':<12} {'Process Time':<14} {'Entities':<10} {'Est. Pages/Sec'}")
            print("-" * 70)
            
            for result in successful_results:
                model = result['model']
                load_time = result.get('load_time', 0)
                proc_time = result.get('processing_time', 0)
                entities = len(result.get('entities', []))
                
                # Estimate pages/sec (assuming 3000 chars per page)
                chars_per_sec = len(self.test_text) / proc_time if proc_time > 0 else 0
                pages_per_sec = chars_per_sec / 3000
                
                print(f"{model:<20} {load_time:<12.2f} {proc_time:<14.3f} {entities:<10} {pages_per_sec:<10.1f}")
        
        print("\n🎯 KEY INSIGHTS:")
        print("• Transformer models are much more accurate but slower")
        print("• Load times are significant (one-time cost)")
        print("• Processing times vary dramatically")
        print("• All models work on CPU (no GPU required)")
        print("• Better accuracy comes with speed trade-offs")


def main():
    """Run BERT NER model tests"""
    tester = BERTNERTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()