#!/usr/bin/env python3
"""
Test Regex + spaCy Hybrid Approach
1. Use fast regex to extract candidate entities
2. Use spaCy to normalize and classify the candidates

This should combine speed (regex pre-filtering) with intelligence (spaCy normalization)
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


class RegexSpacyHybrid:
    """Hybrid entity extraction using regex pre-filtering + spaCy normalization"""
    
    def __init__(self, test_docs_dir: str = "../output/pipeline/1-markdown"):
        self.test_docs_dir = test_docs_dir
        
        # Fast regex patterns to extract candidates
        self.extraction_patterns = {
            'MONEY_CANDIDATES': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|k|M|B))?',
                r'(?:USD|dollars?)\s*[\d,]+(?:\.\d{2})?',
                r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD)',
                r'cost(?:s|ing)?\s*(?:of\s*)?[\$\d,]+',
                r'budget(?:ed)?\s*(?:of\s*)?[\$\d,]+'
            ],
            'DATE_CANDIDATES': [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', 
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
            ],
            'PERSON_CANDIDATES': [
                r'\b(?:Dr|Mr|Ms|Mrs|Prof|Professor|Director|Manager|Inspector|Chief|Captain|Officer)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Jr|Sr|III|II|PhD|MD|PE)\.?)*\b',
                r'(?:contacted?|reach|email|call)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',
                r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:said|reported|stated|found|noted)'
            ],
            'ORG_CANDIDATES': [
                r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b',  # All caps orgs like EPA, OSHA
                r'\b(?:Department|Bureau|Agency|Administration|Institute|Center|Office|Division)\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Department|Bureau|Agency|Administration|Institute|Center|Office|Division)\b',
                r'\b(?:Inc|LLC|Corp|Corporation|Company|Ltd)\.?\b',
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Corporation|Company|Ltd)\.?\b'
            ],
            'QUANTITY_CANDIDATES': [
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:percent|%|percentage)\b',
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:feet|ft|inches|in|yards|yd|miles|mi)\b',
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:pounds|lbs|tons|ounces|oz|grams|kg)\b',
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:hours|hrs|minutes|mins|seconds|secs|days|weeks|months|years)\b',
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:workers|employees|people|individuals|cases|violations)\b'
            ],
            'LOCATION_CANDIDATES': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # City, State
                r'\bin\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?\b',
                r'\b(?:United States|USA|US|America)\b',
                r'\b[A-Z][a-z]+\s+(?:County|Parish|District)\b'
            ]
        }
        
        # Load spaCy model for normalization
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                # Keep only NER for speed
                self.nlp.disable_pipes(["tagger", "parser", "lemmatizer", "attribute_ruler"])
                self.spacy_ready = True
            except:
                self.spacy_ready = False
        else:
            self.spacy_ready = False

    def extract_candidates_with_regex(self, text: str) -> Dict[str, List[Dict]]:
        """Extract candidate entities using fast regex patterns"""
        candidates = defaultdict(list)
        
        for category, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    candidates[category].append({
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': pattern
                    })
        
        return dict(candidates)

    def normalize_with_spacy(self, candidates: Dict[str, List[Dict]], original_text: str) -> Dict[str, List[Dict]]:
        """Use spaCy to normalize and validate regex-extracted candidates"""
        if not self.spacy_ready:
            return {"error": "spaCy not available for normalization"}
        
        normalized = defaultdict(list)
        
        # Process each candidate through spaCy
        for category, candidate_list in candidates.items():
            for candidate in candidate_list:
                candidate_text = candidate['text']
                
                # Get spaCy's analysis of this candidate
                doc = self.nlp(candidate_text)
                
                spacy_entities = []
                for ent in doc.ents:
                    spacy_entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'confidence': getattr(ent, 'confidence', 0.0)
                    })
                
                # Enhanced candidate with spaCy normalization
                enhanced_candidate = {
                    'original_text': candidate_text,
                    'regex_category': category,
                    'start': candidate['start'],
                    'end': candidate['end'],
                    'spacy_entities': spacy_entities,
                    'spacy_normalized': len(spacy_entities) > 0
                }
                
                # Categorize based on spaCy's analysis if available
                if spacy_entities:
                    primary_entity = spacy_entities[0]
                    normalized[f"SPACY_{primary_entity['label']}"].append(enhanced_candidate)
                else:
                    # Keep regex category if spaCy doesn't recognize it
                    normalized[category].append(enhanced_candidate)
        
        return dict(normalized)

    def test_on_sample_documents(self, limit: int = 3) -> Dict[str, Any]:
        """Test hybrid approach on sample documents"""
        doc_pattern = os.path.join(self.test_docs_dir, "*.md")
        test_files = sorted(glob.glob(doc_pattern))[:limit]
        
        if not test_files:
            return {"error": "No test documents found"}
        
        results = {
            'files_processed': [],
            'total_candidates': 0,
            'total_normalized': 0,
            'performance': {},
            'samples': {}
        }
        
        total_regex_time = 0
        total_spacy_time = 0
        total_chars = 0
        
        for file_path in test_files:
            filename = os.path.basename(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            total_chars += len(content)
            
            # Step 1: Fast regex extraction
            start_time = time.time()
            candidates = self.extract_candidates_with_regex(content)
            regex_time = time.time() - start_time
            total_regex_time += regex_time
            
            candidate_count = sum(len(v) for v in candidates.values())
            
            # Step 2: spaCy normalization (only on candidates)
            start_time = time.time()
            normalized = self.normalize_with_spacy(candidates, content)
            spacy_time = time.time() - start_time
            total_spacy_time += spacy_time
            
            normalized_count = sum(len(v) for v in normalized.values())
            
            results['files_processed'].append({
                'filename': filename,
                'char_count': len(content),
                'candidates_found': candidate_count,
                'normalized_entities': normalized_count,
                'regex_time': regex_time,
                'spacy_time': spacy_time
            })
            
            results['total_candidates'] += candidate_count
            results['total_normalized'] += normalized_count
            
            # Save samples from first file
            if len(results['samples']) == 0:
                results['samples'] = {
                    'candidates': candidates,
                    'normalized': normalized
                }
        
        # Calculate performance metrics
        total_time = total_regex_time + total_spacy_time
        results['performance'] = {
            'total_chars': total_chars,
            'total_time': total_time,
            'regex_time': total_regex_time,
            'spacy_time': total_spacy_time,
            'chars_per_sec': total_chars / total_time if total_time > 0 else 0,
            'regex_percentage': (total_regex_time / total_time * 100) if total_time > 0 else 0,
            'spacy_percentage': (total_spacy_time / total_time * 100) if total_time > 0 else 0
        }
        
        return results

    def show_sample_results(self, results: Dict[str, Any]):
        """Display sample extraction and normalization results"""
        print("\n📋 SAMPLE CANDIDATE EXTRACTION (Regex)")
        print("-" * 50)
        
        candidates = results['samples'].get('candidates', {})
        for category, candidate_list in candidates.items():
            if candidate_list:
                print(f"\n🏷️ {category} ({len(candidate_list)} found):")
                for i, candidate in enumerate(candidate_list[:3]):
                    print(f"  {i+1}. \"{candidate['text']}\"")
                if len(candidate_list) > 3:
                    print(f"     ... and {len(candidate_list) - 3} more")
        
        print("\n🧠 SPACY NORMALIZATION RESULTS")
        print("-" * 50)
        
        normalized = results['samples'].get('normalized', {})
        for category, entity_list in normalized.items():
            if entity_list:
                print(f"\n🎯 {category} ({len(entity_list)} normalized):")
                for i, entity in enumerate(entity_list[:3]):
                    original = entity['original_text']
                    spacy_ents = entity['spacy_entities']
                    if spacy_ents:
                        spacy_text = spacy_ents[0]['text']
                        spacy_label = spacy_ents[0]['label']
                        print(f"  {i+1}. \"{original}\" → \"{spacy_text}\" ({spacy_label})")
                    else:
                        print(f"  {i+1}. \"{original}\" (regex only)")
                if len(entity_list) > 3:
                    print(f"     ... and {len(entity_list) - 3} more")

    def run_hybrid_test(self):
        """Run complete hybrid extraction test"""
        print("REGEX + SPACY HYBRID ENTITY EXTRACTION TEST")
        print("=" * 60)
        print("Strategy: Fast regex pre-filtering → spaCy normalization")
        print()
        
        if not self.spacy_ready:
            print("❌ spaCy not available - running regex-only test")
        
        # Test on sample documents
        results = self.test_on_sample_documents(3)
        
        if "error" in results:
            print(f"❌ {results['error']}")
            return
        
        # Show performance results
        perf = results['performance']
        print(f"📊 PERFORMANCE RESULTS:")
        print(f"  Documents processed: {len(results['files_processed'])}")
        print(f"  Total characters: {perf['total_chars']:,}")
        print(f"  Total candidates found: {results['total_candidates']}")
        print(f"  Total normalized entities: {results['total_normalized']}")
        print()
        
        print(f"⏱️ TIMING BREAKDOWN:")
        print(f"  Regex extraction: {perf['regex_time']:.4f}s ({perf['regex_percentage']:.1f}%)")
        print(f"  spaCy normalization: {perf['spacy_time']:.4f}s ({perf['spacy_percentage']:.1f}%)")
        print(f"  Total time: {perf['total_time']:.4f}s")
        print(f"  Processing speed: {perf['chars_per_sec']:,.0f} chars/sec")
        print()
        
        # Convert to pages/sec (assuming 3KB average page)
        pages_per_sec = (perf['chars_per_sec'] / 3000) if perf['chars_per_sec'] > 0 else 0
        print(f"🎯 ESTIMATED PERFORMANCE: {pages_per_sec:.0f} pages/sec")
        
        target_status = "✅ TARGET MET" if pages_per_sec >= 1000 else "🔄 IMPROVING" if pages_per_sec >= 500 else "❌ INSUFFICIENT"
        print(f"   Status vs 1000 pages/sec target: {target_status}")
        print()
        
        # Show sample results
        self.show_sample_results(results)
        
        print("\n" + "=" * 60)
        print("HYBRID APPROACH ANALYSIS:")
        print("✅ Pros:")
        print("  • Fast regex pre-filtering reduces spaCy workload")
        print("  • spaCy normalization improves entity quality")  
        print("  • Can focus spaCy on promising candidates only")
        print("❌ Cons:")
        print("  • Still limited by spaCy processing time")
        print("  • Regex patterns may miss edge cases")
        print("💡 Optimization potential:")
        print("  • Batch spaCy processing for better efficiency")
        print("  • Cache spaCy results for repeated entities")
        print("  • Use smaller spaCy models for speed")


def main():
    """Run regex + spaCy hybrid test"""
    hybrid = RegexSpacyHybrid()
    hybrid.run_hybrid_test()


if __name__ == "__main__":
    main()