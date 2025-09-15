#!/usr/bin/env python3
"""
Simple spaCy PERSON Entity Extractor
Shows exactly what spaCy finds in our documents for PERSON entities

This script will:
1. Load a few test documents
2. Run spaCy on them to extract PERSON entities
3. Show the results clearly with context
4. Then expand to show other entity types
"""

import spacy
import glob
import os
import time
from typing import List, Dict, Tuple


class SpacyPersonExtractor:
    """Simple spaCy person entity extractor"""
    
    def __init__(self, docs_dir: str = "../output/pipeline/3-enriched"):
        self.docs_dir = docs_dir
        
        # Load spaCy model
        print("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model loaded")

    def extract_persons_from_text(self, text: str, filename: str = "test") -> List[Dict]:
        """Extract PERSON entities from text using spaCy"""
        
        # Limit text size for processing
        if len(text) > 50000:
            text = text[:50000]
            print(f"  (Text truncated to 50,000 characters for processing)")
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract PERSON entities
        persons = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Get surrounding context
                start_char = max(0, ent.start_char - 50)
                end_char = min(len(text), ent.end_char + 50)
                context = text[start_char:end_char].replace('\n', ' ').strip()
                
                persons.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'context': context,
                    'file': filename
                })
        
        return persons

    def extract_all_entities_from_text(self, text: str, filename: str = "test") -> Dict[str, List]:
        """Extract ALL entity types from text using spaCy"""
        
        # Limit text size for processing
        if len(text) > 50000:
            text = text[:50000]
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Group entities by type
        entities_by_type = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities_by_type:
                entities_by_type[ent.label_] = []
            
            # Get surrounding context
            start_char = max(0, ent.start_char - 30)
            end_char = min(len(text), ent.end_char + 30)
            context = text[start_char:end_char].replace('\n', ' ').strip()
            
            entities_by_type[ent.label_].append({
                'text': ent.text,
                'context': context,
                'file': filename
            })
        
        return entities_by_type

    def test_person_extraction(self, num_docs: int = None):
        """Test PERSON extraction on sample documents"""
        print(f"\n🔍 TESTING PERSON EXTRACTION")
        print("=" * 60)
        
        # Get ALL documents
        doc_pattern = os.path.join(self.docs_dir, "*.md")
        all_doc_files = sorted(glob.glob(doc_pattern))
        
        if num_docs is None:
            doc_files = all_doc_files
            print(f"Processing ALL {len(doc_files)} documents")
        else:
            doc_files = all_doc_files[:num_docs]
            print(f"Processing {len(doc_files)} of {len(all_doc_files)} documents")
        
        if not doc_files:
            print("❌ No documents found!")
            return
        
        print()
        
        all_persons = []
        total_processing_time = 0
        
        for i, file_path in enumerate(doc_files, 1):
            filename = os.path.basename(file_path)
            print(f"📄 Document {i}: {filename}")
            print("-" * 50)
            
            try:
                # Read document
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"  Document size: {len(content):,} characters")
                
                # Extract persons with timing
                start_time = time.time()
                persons = self.extract_persons_from_text(content, filename)
                processing_time = time.time() - start_time
                total_processing_time += processing_time
                
                print(f"  Processing time: {processing_time:.3f}s")
                print(f"  PERSONS found: {len(persons)}")
                
                if persons:
                    # Extract just the entity text, clean and deduplicate
                    person_names = list(set(person['text'].strip() for person in persons))
                    person_names.sort()  # Sort alphabetically
                    
                    # Show as clean quoted, comma-separated list with type
                    quoted_names = [f'"{name}"' for name in person_names]
                    print(f"  📋 PERSON ENTITIES: {', '.join(quoted_names)}")
                    
                    all_persons.extend(persons)
                else:
                    print("  📋 PERSON ENTITIES: (none found)")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Error processing {filename}: {e}")
                print()
        
        # Summary
        print("=" * 60)
        print("PERSON EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Total documents processed: {len(doc_files)}")
        print(f"Total processing time: {total_processing_time:.3f}s")
        print(f"Total PERSON entities found: {len(all_persons)}")
        
        if all_persons:
            # Show unique persons
            unique_persons = list(set(person['text'] for person in all_persons))
            print(f"Unique persons: {len(unique_persons)}")
            
            print(f"\nTop 10 unique persons found:")
            for i, person in enumerate(unique_persons[:10], 1):
                print(f"  {i}. {person}")
            
            if len(unique_persons) > 10:
                print(f"  ... and {len(unique_persons) - 10} more")
        
        return all_persons

    def test_all_entities(self, num_docs: int = None):
        """Test extraction of ALL entity types"""
        print(f"\n🌟 TESTING ALL ENTITY TYPES")
        print("=" * 60)
        
        # Get ALL documents
        doc_pattern = os.path.join(self.docs_dir, "*.md")
        all_doc_files = sorted(glob.glob(doc_pattern))
        
        if num_docs is None:
            doc_files = all_doc_files
            print(f"Processing ALL {len(doc_files)} documents for complete entity analysis")
        else:
            doc_files = all_doc_files[:num_docs]
            print(f"Processing {len(doc_files)} of {len(all_doc_files)} documents")
        
        if not doc_files:
            print("❌ No documents found!")
            return
        
        all_entities = {}
        
        for i, file_path in enumerate(doc_files, 1):
            filename = os.path.basename(file_path)
            print(f"\n📄 Document {i}: {filename}")
            print("-" * 50)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract all entities
                start_time = time.time()
                entities = self.extract_all_entities_from_text(content, filename)
                processing_time = time.time() - start_time
                
                print(f"Processing time: {processing_time:.3f}s")
                print(f"Entity types found: {len(entities)}")
                
                # Show results for this document
                for entity_type, entity_list in entities.items():
                    print(f"\n  🏷️ {entity_type} ({len(entity_list)} found):")
                    
                    # Extract unique entities and show as quoted list
                    unique_entities = list(set(entity['text'].strip() for entity in entity_list))
                    unique_entities.sort()
                    
                    # Split into chunks if too many
                    if len(unique_entities) <= 10:
                        quoted_entities = [f'"{entity}"' for entity in unique_entities]
                        print(f"     {', '.join(quoted_entities)}")
                    else:
                        # Show first 10, then count remaining
                        quoted_entities = [f'"{entity}"' for entity in unique_entities[:10]]
                        print(f"     {', '.join(quoted_entities)}")
                        print(f"     ... and {len(unique_entities) - 10} more unique entities")
                    
                    # Aggregate for summary
                    if entity_type not in all_entities:
                        all_entities[entity_type] = []
                    all_entities[entity_type].extend(entity_list)
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
        
        # Overall summary
        print("\n" + "=" * 60)
        print("ALL ENTITIES SUMMARY")
        print("=" * 60)
        
        for entity_type, entity_list in sorted(all_entities.items()):
            unique_entities = list(set(entity['text'] for entity in entity_list))
            print(f"{entity_type:>15}: {len(entity_list):3d} total, {len(unique_entities):3d} unique")
        
        return all_entities


def main():
    """Run spaCy entity extraction tests"""
    extractor = SpacyPersonExtractor()
    
    print("SPACY ENTITY EXTRACTION TEST")
    print("=" * 60)
    print("Testing spaCy's accuracy on our OSHA documents")
    
    # First test: PERSON extraction only - process ALL documents
    persons = extractor.test_person_extraction()
    
    # Second test: ALL entity types on ALL documents (this is what you really want to see)
    print("\n" + "="*80)
    print("NOW SHOWING ALL ENTITY TYPES FOR ALL DOCUMENTS:")
    print("="*80)
    all_entities = extractor.test_all_entities(num_docs=None)  # Process ALL documents
    
    print("\n" + "=" * 60)
    print("🎯 KEY INSIGHTS:")
    print("• spaCy is slow but finds entities we'd miss with regex")
    print("• PERSON entities show names we can add to dictionaries")
    print("• Other entity types reveal additional extraction opportunities")
    print("• This data can train our pyahocorasick dictionaries")


if __name__ == "__main__":
    main()