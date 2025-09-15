#!/usr/bin/env python3
"""
Optimized Regex + spaCy Hybrid Approach
Testing different strategies for combining regex pre-filtering with spaCy normalization

Strategies to test:
1. Pure regex extraction (baseline speed)
2. Regex + spaCy on individual candidates (current approach)
3. Regex + spaCy batch processing (optimized)
4. Regex + spaCy on context windows (focused processing)
"""

import re
import time
import glob
import os
from typing import List, Dict, Any, Tuple
from collections import defaultdict

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class OptimizedHybridExtractor:
    """Optimized hybrid entity extraction with multiple strategies"""
    
    def __init__(self, test_docs_dir: str = "../output/pipeline/1-markdown"):
        self.test_docs_dir = test_docs_dir
        
        # Optimized regex patterns for better precision
        self.patterns = {
            'MONEY': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD)',
                r'cost(?:ing)?\s*[\$\d,]+(?:\.\d{2})?'
            ],
            'DATE': [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'
            ],
            'PERSON': [
                r'\b(?:Dr|Mr|Ms|Mrs|Prof|Director|Manager|Inspector)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:Jr|Sr|PhD|MD))?\b(?=\s+(?:said|reported|stated|found|works|at|from))'
            ],
            'ORGANIZATION': [
                r'\b(?:OSHA|EPA|CDC|NIOSH|DOL|Department of Labor|Occupational Safety and Health Administration)\b',
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Department|Bureau|Agency|Administration|Institute)\b'
            ],
            'PHONE': [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\d{3}-\d{3}-\d{4}\b'
            ],
            'EMAIL': [
                r'\b[\w.-]+@[\w.-]+\.\w+\b'
            ]
        }
        
        # Load spaCy model
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
                self.spacy_ready = True
            except:
                self.spacy_ready = False
        else:
            self.spacy_ready = False

    def get_test_documents(self, limit: int = 10) -> List[Tuple[str, str]]:
        """Get test documents for benchmarking"""
        docs = []
        doc_pattern = os.path.join(self.test_docs_dir, "*.md")
        
        for file_path in sorted(glob.glob(doc_pattern))[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    docs.append((filename, content))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return docs

    def strategy_1_pure_regex(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Strategy 1: Pure regex extraction (baseline)"""
        start_time = time.time()
        
        total_entities = 0
        all_extractions = defaultdict(list)
        
        for filename, content in documents:
            for entity_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        total_entities += 1
                        all_extractions[entity_type].append({
                            'text': match.group(),
                            'file': filename,
                            'start': match.start(),
                            'end': match.end()
                        })
        
        processing_time = time.time() - start_time
        total_chars = sum(len(content) for _, content in documents)
        
        return {
            'strategy': 'Pure Regex',
            'entities_found': total_entities,
            'processing_time': processing_time,
            'chars_per_sec': total_chars / processing_time if processing_time > 0 else 0,
            'pages_per_sec': (total_chars / 3000) / processing_time if processing_time > 0 else 0,
            'extractions': dict(all_extractions)
        }

    def strategy_2_individual_spacy(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Strategy 2: Regex + spaCy on individual candidates"""
        if not self.spacy_ready:
            return {"error": "spaCy not available"}
        
        start_time = time.time()
        
        total_entities = 0
        validated_entities = 0
        all_extractions = defaultdict(list)
        
        for filename, content in documents:
            # Extract candidates with regex
            for entity_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        total_entities += 1
                        candidate_text = match.group()
                        
                        # Validate with spaCy
                        doc = self.nlp(candidate_text)
                        spacy_entities = [ent for ent in doc.ents]
                        
                        if spacy_entities or entity_type in ['PHONE', 'EMAIL']:  # Always accept phone/email
                            validated_entities += 1
                            all_extractions[entity_type].append({
                                'text': candidate_text,
                                'file': filename,
                                'start': match.start(),
                                'end': match.end(),
                                'spacy_validated': len(spacy_entities) > 0,
                                'spacy_labels': [ent.label_ for ent in spacy_entities]
                            })
        
        processing_time = time.time() - start_time
        total_chars = sum(len(content) for _, content in documents)
        
        return {
            'strategy': 'Regex + Individual spaCy',
            'candidates_found': total_entities,
            'entities_found': validated_entities,
            'processing_time': processing_time,
            'chars_per_sec': total_chars / processing_time if processing_time > 0 else 0,
            'pages_per_sec': (total_chars / 3000) / processing_time if processing_time > 0 else 0,
            'extractions': dict(all_extractions)
        }

    def strategy_3_batch_spacy(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Strategy 3: Regex + spaCy batch processing"""
        if not self.spacy_ready:
            return {"error": "spaCy not available"}
        
        start_time = time.time()
        
        # First pass: collect all candidates
        all_candidates = []
        candidate_map = {}
        
        for filename, content in documents:
            for entity_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        candidate_text = match.group()
                        candidate_id = len(all_candidates)
                        all_candidates.append(candidate_text)
                        candidate_map[candidate_id] = {
                            'type': entity_type,
                            'text': candidate_text,
                            'file': filename,
                            'start': match.start(),
                            'end': match.end()
                        }
        
        # Second pass: batch process with spaCy
        validated_entities = 0
        all_extractions = defaultdict(list)
        
        # Process in batches for efficiency
        batch_size = 100
        for i in range(0, len(all_candidates), batch_size):
            batch = all_candidates[i:i+batch_size]
            
            # Create combined text for batch processing
            combined_text = " ||| ".join(batch)  # Use delimiter to separate
            doc = self.nlp(combined_text)
            
            # Map back to individual candidates
            text_parts = combined_text.split(" ||| ")
            for j, part in enumerate(text_parts):
                candidate_id = i + j
                if candidate_id in candidate_map:
                    candidate = candidate_map[candidate_id]
                    
                    # Check if this part has spaCy entities
                    part_start = combined_text.find(part)
                    part_end = part_start + len(part)
                    
                    spacy_entities = [ent for ent in doc.ents 
                                   if ent.start_char >= part_start and ent.end_char <= part_end]
                    
                    if spacy_entities or candidate['type'] in ['PHONE', 'EMAIL']:
                        validated_entities += 1
                        all_extractions[candidate['type']].append({
                            'text': candidate['text'],
                            'file': candidate['file'],
                            'start': candidate['start'],
                            'end': candidate['end'],
                            'spacy_validated': len(spacy_entities) > 0,
                            'spacy_labels': [ent.label_ for ent in spacy_entities]
                        })
        
        processing_time = time.time() - start_time
        total_chars = sum(len(content) for _, content in documents)
        
        return {
            'strategy': 'Regex + Batch spaCy',
            'candidates_found': len(all_candidates),
            'entities_found': validated_entities,
            'processing_time': processing_time,
            'chars_per_sec': total_chars / processing_time if processing_time > 0 else 0,
            'pages_per_sec': (total_chars / 3000) / processing_time if processing_time > 0 else 0,
            'extractions': dict(all_extractions)
        }

    def strategy_4_context_windows(self, documents: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Strategy 4: Regex + spaCy on context windows"""
        if not self.spacy_ready:
            return {"error": "spaCy not available"}
        
        start_time = time.time()
        
        total_entities = 0
        all_extractions = defaultdict(list)
        processed_windows = set()  # Avoid duplicate processing
        
        for filename, content in documents:
            for entity_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        total_entities += 1
                        
                        # Extract context window around match
                        window_start = max(0, match.start() - 100)
                        window_end = min(len(content), match.end() + 100)
                        context_window = content[window_start:window_end]
                        
                        # Avoid processing same window multiple times
                        window_hash = hash(context_window)
                        if window_hash in processed_windows:
                            continue
                        processed_windows.add(window_hash)
                        
                        # Process context window with spaCy
                        doc = self.nlp(context_window)
                        
                        # Find entities in the context window
                        for ent in doc.ents:
                            # Check if entity overlaps with our regex match
                            ent_start_global = window_start + ent.start_char
                            ent_end_global = window_start + ent.end_char
                            
                            overlap = (ent_start_global < match.end() and ent_end_global > match.start())
                            
                            if overlap or ent.label_ in ['PERSON', 'ORG', 'GPE', 'MONEY', 'DATE']:
                                all_extractions[f"SPACY_{ent.label_}"].append({
                                    'text': ent.text,
                                    'file': filename,
                                    'start': ent_start_global,
                                    'end': ent_end_global,
                                    'confidence': getattr(ent, 'confidence', 0.0),
                                    'from_context': True
                                })
        
        processing_time = time.time() - start_time
        total_chars = sum(len(content) for _, content in documents)
        
        return {
            'strategy': 'Regex + Context Window spaCy',
            'regex_matches': total_entities,
            'entities_found': sum(len(v) for v in all_extractions.values()),
            'processing_time': processing_time,
            'chars_per_sec': total_chars / processing_time if processing_time > 0 else 0,
            'pages_per_sec': (total_chars / 3000) / processing_time if processing_time > 0 else 0,
            'extractions': dict(all_extractions)
        }

    def run_strategy_comparison(self):
        """Compare all hybrid strategies"""
        print("OPTIMIZED REGEX + SPACY HYBRID COMPARISON")
        print("=" * 60)
        
        # Load test documents
        documents = self.get_test_documents(10)
        if not documents:
            print("❌ No test documents found")
            return
        
        total_chars = sum(len(content) for _, content in documents)
        print(f"📊 Testing on {len(documents)} documents ({total_chars:,} characters)")
        print()
        
        # Test all strategies
        strategies = [
            ("1. Pure Regex (Baseline)", self.strategy_1_pure_regex),
            ("2. Regex + Individual spaCy", self.strategy_2_individual_spacy),
            ("3. Regex + Batch spaCy", self.strategy_3_batch_spacy),
            ("4. Regex + Context Windows", self.strategy_4_context_windows)
        ]
        
        results = []
        
        for name, strategy_func in strategies:
            print(f"🔍 Testing {name}...")
            result = strategy_func(documents)
            
            if "error" in result:
                print(f"  ❌ {result['error']}")
                continue
            
            results.append((name, result))
            
            pages_sec = result.get('pages_per_sec', 0)
            entities = result.get('entities_found', result.get('regex_matches', 0))
            
            target_status = "✅" if pages_sec >= 1000 else "🔄" if pages_sec >= 500 else "❌"
            
            print(f"  {target_status} {pages_sec:.0f} pages/sec, {entities} entities")
            print()
        
        # Summary comparison
        print("📈 STRATEGY COMPARISON SUMMARY")
        print("-" * 60)
        print(f"{'Strategy':<30} {'Pages/Sec':<12} {'Entities':<10} {'Status'}")
        print("-" * 60)
        
        for name, result in results:
            pages_sec = result.get('pages_per_sec', 0)
            entities = result.get('entities_found', result.get('regex_matches', 0))
            
            if pages_sec >= 1000:
                status = "✅ TARGET MET"
            elif pages_sec >= 500:
                status = "🔄 IMPROVING"  
            else:
                status = "❌ INSUFFICIENT"
            
            short_name = name.split('.')[1].strip() if '.' in name else name
            print(f"{short_name:<30} {pages_sec:<12.0f} {entities:<10} {status}")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        
        # Find best performing strategy
        best_strategy = max(results, key=lambda x: x[1].get('pages_per_sec', 0))
        print(f"🏆 Best Performance: {best_strategy[0]}")
        print(f"   {best_strategy[1]['pages_per_sec']:.0f} pages/sec")
        
        # Show sample extractions from best strategy
        print(f"\n📋 Sample extractions from best strategy:")
        extractions = best_strategy[1].get('extractions', {})
        for entity_type, entities in extractions.items():
            if entities:
                print(f"  {entity_type}: {len(entities)} found")
                for i, entity in enumerate(entities[:2]):
                    print(f"    • \"{entity['text']}\" ({entity['file']})")
                if len(entities) > 2:
                    print(f"    ... and {len(entities) - 2} more")


def main():
    """Run optimized hybrid strategy comparison"""
    extractor = OptimizedHybridExtractor()
    extractor.run_strategy_comparison()


if __name__ == "__main__":
    main()