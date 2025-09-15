#!/usr/bin/env python3
"""
Real spaCy Performance Test
Process ALL files in the enriched pipeline folder and measure actual speed

This will give us the true pages/sec performance of spaCy on real documents
"""

import spacy
import time
import os
import glob
from typing import List, Dict


class SpacyRealPerformanceTest:
    """Test spaCy on all enriched documents for real performance metrics"""
    
    def __init__(self, docs_dir: str = "/home/corey/projects/docling/mvp-hyper/output/pipeline/3-enriched"):
        self.docs_dir = docs_dir
        self.nlp = None
        
    def load_spacy_model(self):
        """Load spaCy model once"""
        print("🔄 Loading spaCy model...")
        start_time = time.time()
        self.nlp = spacy.load("en_core_web_sm")
        load_time = time.time() - start_time
        print(f"✅ spaCy model loaded in {load_time:.2f}s")
        return load_time
    
    def get_all_documents(self):
        """Load ALL documents from the enriched folder"""
        doc_pattern = os.path.join(self.docs_dir, "*.md")
        doc_files = sorted(glob.glob(doc_pattern))
        
        documents = []
        total_chars = 0
        
        print(f"📁 Loading documents from: {self.docs_dir}")
        print(f"🔍 Found {len(doc_files)} markdown files")
        print()
        
        for i, file_path in enumerate(doc_files, 1):
            filename = os.path.basename(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                char_count = len(content)
                word_count = len(content.split())
                total_chars += char_count
                
                documents.append({
                    'filename': filename,
                    'content': content,
                    'char_count': char_count,
                    'word_count': word_count
                })
                
                print(f"  {i:2d}. {filename[:60]:<60} {char_count:>8,} chars, {word_count:>6,} words")
                
            except Exception as e:
                print(f"  {i:2d}. ❌ ERROR reading {filename}: {e}")
        
        print(f"\n📊 TOTAL: {len(documents)} documents, {total_chars:,} characters")
        print(f"📊 AVERAGE: {total_chars / len(documents):,.0f} chars per document")
        
        # Calculate estimated pages (assuming 3000 chars per page)
        total_pages = total_chars / 3000
        print(f"📊 ESTIMATED PAGES: {total_pages:.1f} pages")
        print()
        
        return documents
    
    def process_documents(self, documents: List[Dict]) -> Dict:
        """Process all documents with spaCy and measure performance"""
        if not self.nlp:
            print("❌ spaCy model not loaded!")
            return {}
        
        print("🚀 PROCESSING ALL DOCUMENTS WITH SPACY")
        print("=" * 70)
        
        total_chars = 0
        total_entities = 0
        processing_times = []
        
        overall_start = time.time()
        
        for i, doc in enumerate(documents, 1):
            filename = doc['filename']
            content = doc['content']
            char_count = doc['char_count']
            
            print(f"Processing {i:2d}/{len(documents)}: {filename[:50]:<50}", end=" ")
            
            # Process document
            start_time = time.time()
            spacy_doc = self.nlp(content)
            processing_time = time.time() - start_time
            
            # Count entities
            entities = list(spacy_doc.ents)
            entity_count = len(entities)
            
            # Track totals
            total_chars += char_count
            total_entities += entity_count
            processing_times.append(processing_time)
            
            # Calculate speed for this document
            chars_per_sec = char_count / processing_time if processing_time > 0 else 0
            pages_per_sec = chars_per_sec / 3000
            
            print(f"{processing_time:6.3f}s, {entity_count:3d} entities, {pages_per_sec:5.1f} p/s")
        
        overall_time = time.time() - overall_start
        
        # Calculate overall performance
        avg_processing_time = sum(processing_times) / len(processing_times)
        total_pages = total_chars / 3000
        
        overall_chars_per_sec = total_chars / overall_time
        overall_pages_per_sec = overall_chars_per_sec / 3000
        
        print("\n" + "=" * 70)
        print("📊 PERFORMANCE RESULTS")
        print("=" * 70)
        
        print(f"Documents processed: {len(documents)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Total estimated pages: {total_pages:.1f}")
        print(f"Total entities found: {total_entities:,}")
        print(f"Total processing time: {overall_time:.2f}s")
        print(f"Average time per document: {avg_processing_time:.3f}s")
        print()
        
        print("🎯 SPEED METRICS:")
        print(f"  Characters per second: {overall_chars_per_sec:,.0f}")
        print(f"  Pages per second: {overall_pages_per_sec:.1f}")
        print(f"  Documents per second: {len(documents) / overall_time:.1f}")
        print(f"  Entities per second: {total_entities / overall_time:.0f}")
        print()
        
        # Compare to target
        if overall_pages_per_sec >= 1000:
            status = "✅ MEETS TARGET!"
        elif overall_pages_per_sec >= 500:
            status = "🔄 GETTING CLOSE"
        elif overall_pages_per_sec >= 100:
            status = "⚠️ TOO SLOW"
        else:
            status = "❌ WAY TOO SLOW"
        
        print(f"🎯 TARGET COMPARISON: {status}")
        print(f"   Target: 1000+ pages/sec")
        print(f"   Actual: {overall_pages_per_sec:.1f} pages/sec")
        print(f"   Gap: {1000 / overall_pages_per_sec:.1f}x too slow")
        
        # Show entity breakdown
        print("\n🏷️ ENTITY BREAKDOWN:")
        entity_types = {}
        for doc in documents:
            spacy_doc = self.nlp(doc['content'])
            for ent in spacy_doc.ents:
                if ent.label_ not in entity_types:
                    entity_types[ent.label_] = 0
                entity_types[ent.label_] += 1
        
        for entity_type in sorted(entity_types.keys()):
            count = entity_types[entity_type]
            percentage = (count / total_entities * 100) if total_entities > 0 else 0
            print(f"  {entity_type:>12}: {count:4d} ({percentage:4.1f}%)")
        
        return {
            'documents_processed': len(documents),
            'total_chars': total_chars,
            'total_pages': total_pages,
            'total_entities': total_entities,
            'total_time': overall_time,
            'chars_per_sec': overall_chars_per_sec,
            'pages_per_sec': overall_pages_per_sec,
            'avg_time_per_doc': avg_processing_time,
            'entity_types': entity_types
        }
    
    def run_full_test(self):
        """Run complete performance test"""
        print("SPACY REAL-WORLD PERFORMANCE TEST")
        print("=" * 70)
        print("Testing spaCy on ALL enriched pipeline documents")
        print()
        
        # Load model
        load_time = self.load_spacy_model()
        
        # Load documents
        documents = self.get_all_documents()
        
        if not documents:
            print("❌ No documents found!")
            return
        
        # Process documents
        results = self.process_documents(documents)
        
        if results:
            print("\n" + "=" * 70)
            print("🏁 FINAL ASSESSMENT")
            print("=" * 70)
            print("For production use at 1000+ pages/sec:")
            
            if results['pages_per_sec'] >= 1000:
                print("✅ spaCy meets the performance target!")
            else:
                gap = 1000 / results['pages_per_sec']
                print(f"❌ spaCy is {gap:.1f}x too slow for production target")
                print(f"   Would need {gap:.1f}x speedup or {gap:.0f}x more CPU cores")
        
        return results


def main():
    """Run the real spaCy performance test"""
    tester = SpacyRealPerformanceTest()
    results = tester.run_full_test()


if __name__ == "__main__":
    main()