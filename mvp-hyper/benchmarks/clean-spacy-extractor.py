#!/usr/bin/env python3
"""
Clean spaCy Entity Extractor
Shows all entity types for all documents in a clean, readable format
"""

import spacy
import glob
import os
import time
from typing import Dict, List
from collections import defaultdict, Counter


class CleanSpacyExtractor:
    """Clean, comprehensive entity extraction with spaCy"""
    
    def __init__(self, docs_dir: str = "../output/pipeline/3-enriched"):
        self.docs_dir = docs_dir
        
        print("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model loaded\n")

    def extract_all_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract all entities grouped by type"""
        # Limit text for processing
        if len(text) > 100000:
            text = text[:100000]
        
        doc = self.nlp(text)
        
        entities_by_type = defaultdict(list)
        for ent in doc.ents:
            entities_by_type[ent.label_].append(ent.text.strip())
        
        # Deduplicate and sort within each type
        for entity_type in entities_by_type:
            entities_by_type[entity_type] = sorted(list(set(entities_by_type[entity_type])))
        
        return dict(entities_by_type)

    def process_all_documents(self):
        """Process all documents and show comprehensive results"""
        print("🔍 COMPREHENSIVE ENTITY EXTRACTION")
        print("=" * 80)
        
        # Get all documents
        doc_pattern = os.path.join(self.docs_dir, "*.md")
        doc_files = sorted(glob.glob(doc_pattern))
        
        if not doc_files:
            print("❌ No documents found!")
            return
        
        print(f"Processing {len(doc_files)} documents from enriched pipeline\n")
        
        # Track totals across all documents
        all_entities = defaultdict(list)
        entity_counts = Counter()
        doc_results = []
        
        total_start_time = time.time()
        
        for i, file_path in enumerate(doc_files, 1):
            filename = os.path.basename(file_path)
            
            # Clean filename for display
            display_name = filename.replace('.md', '').replace('-', ' ').title()
            if len(display_name) > 60:
                display_name = display_name[:57] + "..."
            
            print(f"📄 {i:2d}. {display_name}")
            print("-" * 70)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract entities
                start_time = time.time()
                entities = self.extract_all_entities(content)
                processing_time = time.time() - start_time
                
                # Count entities for this document
                doc_entity_count = sum(len(entities_list) for entities_list in entities.values())
                
                print(f"   📊 {doc_entity_count} entities in {processing_time:.2f}s")
                
                if entities:
                    # Show entities by type
                    for entity_type in sorted(entities.keys()):
                        entity_list = entities[entity_type]
                        count = len(entity_list)
                        
                        # Track totals
                        entity_counts[entity_type] += count
                        all_entities[entity_type].extend(entity_list)
                        
                        # Format entity list for display
                        if count <= 8:
                            # Show all if 8 or fewer
                            quoted_entities = [f'"{entity}"' for entity in entity_list]
                            entities_display = ', '.join(quoted_entities)
                        else:
                            # Show first 6, then indicate more
                            quoted_entities = [f'"{entity}"' for entity in entity_list[:6]]
                            entities_display = ', '.join(quoted_entities) + f', ... +{count-6} more'
                        
                        print(f"   🏷️  {entity_type:12} ({count:2d}): {entities_display}")
                
                else:
                    print("   (No entities found)")
                
                doc_results.append({
                    'filename': filename,
                    'entities': entities,
                    'count': doc_entity_count,
                    'time': processing_time
                })
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()
        
        total_time = time.time() - total_start_time
        
        # SUMMARY SECTION
        print("=" * 80)
        print("📊 COMPREHENSIVE SUMMARY")
        print("=" * 80)
        
        # Overall stats
        total_entities = sum(entity_counts.values())
        avg_time = total_time / len(doc_files)
        
        print(f"Documents processed: {len(doc_files)}")
        print(f"Total processing time: {total_time:.1f}s")
        print(f"Average time per document: {avg_time:.2f}s")
        print(f"Total entities found: {total_entities:,}")
        print(f"Unique entity types: {len(entity_counts)}")
        print()
        
        # Entity type breakdown with totals
        print("🏷️  ENTITY TYPE BREAKDOWN:")
        print("-" * 50)
        
        for entity_type in sorted(entity_counts.keys()):
            count = entity_counts[entity_type]
            unique_count = len(set(all_entities[entity_type]))
            percentage = (count / total_entities * 100) if total_entities > 0 else 0
            
            print(f"{entity_type:>15}: {count:4d} total, {unique_count:4d} unique ({percentage:4.1f}%)")
        
        print()
        
        # Show samples of each entity type
        print("📋 SAMPLE ENTITIES BY TYPE:")
        print("-" * 50)
        
        for entity_type in sorted(all_entities.keys()):
            unique_entities = sorted(list(set(all_entities[entity_type])))
            
            if len(unique_entities) <= 10:
                # Show all if 10 or fewer
                samples = unique_entities
                more_text = ""
            else:
                # Show first 10
                samples = unique_entities[:10]
                more_text = f" ... +{len(unique_entities)-10} more"
            
            quoted_samples = [f'"{entity}"' for entity in samples]
            print(f"{entity_type:>15}: {', '.join(quoted_samples)}{more_text}")
        
        print()
        
        # Performance estimate
        chars_per_sec = sum(len(open(f, 'r').read()) for f in doc_files) / total_time if total_time > 0 else 0
        pages_per_sec = chars_per_sec / 3000
        
        print("⚡ PERFORMANCE ESTIMATE:")
        print(f"   Characters/sec: {chars_per_sec:,.0f}")
        print(f"   Pages/sec: {pages_per_sec:.1f}")
        
        print("\n" + "=" * 80)
        print("✅ EXTRACTION COMPLETE")
        print("=" * 80)


def main():
    """Run comprehensive entity extraction"""
    extractor = CleanSpacyExtractor()
    extractor.process_all_documents()


if __name__ == "__main__":
    main()