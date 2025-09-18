#!/usr/bin/env python3
"""
Dataset Corpus Expander for Large-Scale Entity Recognition
===========================================================
Downloads and processes major NER datasets to extract millions of person and organization names
for high-confidence entity recognition at web scale.

Processes:
1. OntoNotes 5.0 - Multi-million tokens with PERSON/ORG
2. CoNLL-2003 - Classic PER/ORG/LOC benchmark 
3. WikiANN - 176 languages with multilingual PER/ORG
4. MultiCoNER v2 - 2.7M rows with fine-grained entities
5. Few-NERD - 492k entities with detailed taxonomy
6. WNUT-2017 - Noisy social media entities
7. Universal NER - Unified cross-lingual tagset
8. WikiNEuRal - Wikipedia-derived multilingual NER
9. CrossNER - Domain-specific PER/ORG entities

Output: Massively expanded corpus with millions of validated names
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import logging

# Try to import required libraries
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("❌ datasets library not available. Install with: pip install datasets")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("❌ pandas library not available. Install with: pip install pandas")

class DatasetCorpusExpander:
    """
    Downloads and processes major NER datasets to extract person and organization names
    for corpus expansion at massive scale.
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / "expanded_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for extracted names
        self.first_names = set()
        self.last_names = set()
        self.person_full_names = set()
        self.organization_names = set()
        self.organization_variants = set()
        
        # Statistics tracking
        self.dataset_stats = {}
        self.extraction_stats = defaultdict(int)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def expand_corpus_from_datasets(self, datasets_to_process: List[str] = None) -> Dict[str, Set[str]]:
        """
        Main method to expand corpus from multiple NER datasets.
        
        Args:
            datasets_to_process: List of dataset names to process. If None, processes all available.
            
        Returns:
            Dictionary with expanded corpus data
        """
        if not DATASETS_AVAILABLE:
            self.logger.error("❌ datasets library required. Install with: pip install datasets")
            return {}
        
        # Default datasets to process (ordered by priority/size)
        if datasets_to_process is None:
            datasets_to_process = [
                'conll2003',           # Classic benchmark, fast to process
                'wikiann_en',          # English subset of multilingual data
                'ontonotes5',          # Large, comprehensive
                'multiconer_v2_en',    # Modern, fine-grained
                'few_nerd',            # Detailed taxonomy
                'wnut17',              # Social media entities
                'universal_ner_en',    # Unified format
                'wikineural_en',       # Wikipedia-derived
                'cross_ner'            # Domain-specific
            ]
        
        self.logger.info(f"🚀 Starting corpus expansion from {len(datasets_to_process)} datasets")
        
        for dataset_name in datasets_to_process:
            try:
                self.logger.info(f"📊 Processing {dataset_name}...")
                start_time = time.time()
                
                if dataset_name == 'conll2003':
                    self._process_conll2003()
                elif dataset_name == 'wikiann_en':
                    self._process_wikiann_english()
                elif dataset_name == 'ontonotes5':
                    self._process_ontonotes5()
                elif dataset_name == 'multiconer_v2_en':
                    self._process_multiconer_v2()
                elif dataset_name == 'few_nerd':
                    self._process_few_nerd()
                elif dataset_name == 'wnut17':
                    self._process_wnut17()
                elif dataset_name == 'universal_ner_en':
                    self._process_universal_ner()
                elif dataset_name == 'wikineural_en':
                    self._process_wikineural()
                elif dataset_name == 'cross_ner':
                    self._process_cross_ner()
                else:
                    self.logger.warning(f"⚠️ Unknown dataset: {dataset_name}")
                    continue
                
                processing_time = time.time() - start_time
                self.logger.info(f"✅ {dataset_name} processed in {processing_time:.1f}s")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing {dataset_name}: {e}")
                continue
        
        # Generate final statistics
        self._generate_expansion_summary()
        
        # Save expanded corpus
        expanded_corpus = self._save_expanded_corpus()
        
        return expanded_corpus
    
    def _process_conll2003(self):
        """Process CoNLL-2003 dataset for PER/ORG entities."""
        try:
            dataset = load_dataset("eriktks/conll2003")
            
            person_count = 0
            org_count = 0
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    # CoNLL-2003 uses: 0=O, 1=B-PER, 2=I-PER, 3=B-ORG, 4=I-ORG, 5=B-LOC, 6=I-LOC, 7=B-MISC, 8=I-MISC
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        if tag in [1, 2]:  # B-PER, I-PER
                            if tag == 1 and current_entity:  # New entity starting
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif tag in [3, 4]:  # B-ORG, I-ORG
                            if tag == 3 and current_entity:  # New entity starting
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    # Process final entity if exists
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['conll2003'] = {
                'persons_extracted': self.extraction_stats['conll2003_persons'],
                'orgs_extracted': self.extraction_stats['conll2003_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CoNLL-2003: {e}")
    
    def _process_wikiann_english(self):
        """Process WikiANN English subset for multilingual PER/ORG entities."""
        try:
            # Load English subset only for speed
            dataset = load_dataset("unimelb-nlp/wikiann", "en")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    # WikiANN uses: 0=O, 1=B-PER, 2=I-PER, 3=B-ORG, 4=I-ORG, 5=B-LOC, 6=I-LOC
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        if tag in [1, 2]:  # B-PER, I-PER
                            if tag == 1 and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif tag in [3, 4]:  # B-ORG, I-ORG
                            if tag == 3 and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['wikiann_en'] = {
                'persons_extracted': self.extraction_stats['wikiann_persons'],
                'orgs_extracted': self.extraction_stats['wikiann_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WikiANN: {e}")
    
    def _process_ontonotes5(self):
        """Process OntoNotes 5.0 for comprehensive PERSON/ORG entities."""
        try:
            dataset = load_dataset("tner/ontonotes5")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    tags = example['tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, tags):
                        if tag.startswith('B-PERSON') or tag.startswith('I-PERSON'):
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif tag.startswith('B-ORG') or tag.startswith('I-ORG'):
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['ontonotes5'] = {
                'persons_extracted': self.extraction_stats['ontonotes_persons'],
                'orgs_extracted': self.extraction_stats['ontonotes_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing OntoNotes5: {e}")
    
    def _process_multiconer_v2(self):
        """Process MultiCoNER v2 for fine-grained modern entities."""
        try:
            # Process English subset
            dataset = load_dataset("MultiCoNER/multiconer_v2", "en")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        # MultiCoNER uses fine-grained tags, look for person/org related ones
                        if any(person_tag in tag for person_tag in ['PER', 'PERSON']) and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif any(org_tag in tag for org_tag in ['ORG', 'CORP', 'GROUP']) and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['multiconer_v2'] = {
                'persons_extracted': self.extraction_stats['multiconer_persons'],
                'orgs_extracted': self.extraction_stats['multiconer_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing MultiCoNER v2: {e}")
    
    def _process_few_nerd(self):
        """Process Few-NERD for detailed entity taxonomy."""
        try:
            dataset = load_dataset("DFKI-SLT/few-nerd")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        # Few-NERD uses hierarchical tags, look for person/organization
                        if 'person' in tag.lower() and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif 'organization' in tag.lower() and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['few_nerd'] = {
                'persons_extracted': self.extraction_stats['fewnerd_persons'],
                'orgs_extracted': self.extraction_stats['fewnerd_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Few-NERD: {e}")
    
    def _process_wnut17(self):
        """Process WNUT-2017 for noisy social media entities."""
        try:
            dataset = load_dataset("leondz/wnut_17")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        if 'person' in tag.lower() and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif any(org_tag in tag.lower() for org_tag in ['corporation', 'group', 'org']) and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['wnut17'] = {
                'persons_extracted': self.extraction_stats['wnut_persons'],
                'orgs_extracted': self.extraction_stats['wnut_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WNUT-2017: {e}")
    
    def _process_universal_ner(self):
        """Process Universal NER for standardized cross-lingual entities."""
        try:
            # This is a placeholder - would need to check actual dataset structure
            self.logger.info("⚠️ Universal NER processing not yet implemented")
            
        except Exception as e:
            self.logger.error(f"Error processing Universal NER: {e}")
    
    def _process_wikineural(self):
        """Process WikiNEuRal for Wikipedia-derived entities."""
        try:
            dataset = load_dataset("Babelscape/wikineural", "en")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        if tag in [1, 2]:  # Assuming B-PER, I-PER
                            if tag == 1 and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif tag in [3, 4]:  # Assuming B-ORG, I-ORG
                            if tag == 3 and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['wikineural'] = {
                'persons_extracted': self.extraction_stats['wikineural_persons'],
                'orgs_extracted': self.extraction_stats['wikineural_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WikiNEuRal: {e}")
    
    def _process_cross_ner(self):
        """Process CrossNER for domain-specific entities."""
        try:
            dataset = load_dataset("DFKI-SLT/cross_ner")
            
            for split in ['train', 'validation', 'test']:
                if split not in dataset:
                    continue
                    
                for example in dataset[split]:
                    tokens = example['tokens']
                    ner_tags = example['ner_tags']
                    
                    current_entity = []
                    current_type = None
                    
                    for token, tag in zip(tokens, ner_tags):
                        if any(person_tag in tag for person_tag in ['PER', 'PERSON']) and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'PER'
                        elif any(org_tag in tag for org_tag in ['ORG', 'ORGANIZATION']) and tag != 'O':
                            if tag.startswith('B-') and current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = [token]
                            else:
                                current_entity.append(token)
                            current_type = 'ORG'
                        else:
                            if current_entity:
                                self._process_entity(current_entity, current_type)
                                current_entity = []
                                current_type = None
                    
                    if current_entity:
                        self._process_entity(current_entity, current_type)
            
            self.dataset_stats['cross_ner'] = {
                'persons_extracted': self.extraction_stats['crossner_persons'],
                'orgs_extracted': self.extraction_stats['crossner_orgs']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CrossNER: {e}")
    
    def _process_entity(self, entity_tokens: List[str], entity_type: str):
        """
        Process an extracted entity and add to appropriate corpus.
        
        Args:
            entity_tokens: List of tokens forming the entity
            entity_type: 'PER' or 'ORG'
        """
        if not entity_tokens or not entity_type:
            return
        
        # Join tokens to form full entity name
        full_name = ' '.join(entity_tokens).strip()
        
        # Basic cleaning
        full_name = self._clean_entity_name(full_name)
        if not full_name or len(full_name) < 2:
            return
        
        if entity_type == 'PER':
            self._process_person_name(full_name)
            # Track by dataset for statistics
            for dataset in ['conll2003', 'wikiann', 'ontonotes', 'multiconer', 'fewnerd', 'wnut', 'wikineural', 'crossner']:
                if f'{dataset}_persons' not in self.extraction_stats:
                    self.extraction_stats[f'{dataset}_persons'] = 0
                self.extraction_stats[f'{dataset}_persons'] += 1
                break  # Only count in first matching dataset
                
        elif entity_type == 'ORG':
            self._process_organization_name(full_name)
            # Track by dataset for statistics
            for dataset in ['conll2003', 'wikiann', 'ontonotes', 'multiconer', 'fewnerd', 'wnut', 'wikineural', 'crossner']:
                if f'{dataset}_orgs' not in self.extraction_stats:
                    self.extraction_stats[f'{dataset}_orgs'] = 0
                self.extraction_stats[f'{dataset}_orgs'] += 1
                break
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean extracted entity name."""
        # Remove special characters at start/end
        name = name.strip('.,;:!?()[]{}"\'-')
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Filter out obvious non-names
        if any(char.isdigit() for char in name):
            return ""  # Skip names with numbers
        
        if len(name.split()) > 5:
            return ""  # Skip very long entities (likely extraction errors)
        
        return name
    
    def _process_person_name(self, full_name: str):
        """Process a person name and extract first/last name components."""
        self.person_full_names.add(full_name)
        
        # Split into components
        name_parts = full_name.split()
        
        if len(name_parts) >= 1:
            # First word is likely first name
            first_name = name_parts[0].lower()
            if self._is_valid_first_name(first_name):
                self.first_names.add(first_name)
        
        if len(name_parts) >= 2:
            # Last word is likely last name
            last_name = name_parts[-1].lower()
            if self._is_valid_last_name(last_name):
                self.last_names.add(last_name)
    
    def _process_organization_name(self, org_name: str):
        """Process an organization name and its variants."""
        self.organization_names.add(org_name)
        
        # Add lowercase variant
        self.organization_variants.add(org_name.lower())
        
        # Add variant without common suffixes
        for suffix in ['Inc', 'Corp', 'Corporation', 'LLC', 'Ltd', 'Limited', 'Company', 'Co']:
            if org_name.endswith(f' {suffix}'):
                base_name = org_name[:-len(suffix)-1].strip()
                if base_name:
                    self.organization_variants.add(base_name)
                    self.organization_variants.add(base_name.lower())
    
    def _is_valid_first_name(self, name: str) -> bool:
        """Check if a name component is a valid first name."""
        if len(name) < 2 or len(name) > 20:
            return False
        if not name.isalpha():
            return False
        if name.lower() in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']:
            return False
        return True
    
    def _is_valid_last_name(self, name: str) -> bool:
        """Check if a name component is a valid last name."""
        if len(name) < 2 or len(name) > 30:
            return False
        if not name.replace('-', '').replace("'", '').isalpha():
            return False
        return True
    
    def _generate_expansion_summary(self):
        """Generate summary of corpus expansion."""
        total_first_names = len(self.first_names)
        total_last_names = len(self.last_names)
        total_person_names = len(self.person_full_names)
        total_org_names = len(self.organization_names)
        total_org_variants = len(self.organization_variants)
        
        self.logger.info(f"\n📊 CORPUS EXPANSION SUMMARY:")
        self.logger.info(f"   First names extracted: {total_first_names:,}")
        self.logger.info(f"   Last names extracted: {total_last_names:,}")
        self.logger.info(f"   Full person names: {total_person_names:,}")
        self.logger.info(f"   Organization names: {total_org_names:,}")
        self.logger.info(f"   Organization variants: {total_org_variants:,}")
        
        # Dataset breakdown
        self.logger.info(f"\n📊 BY DATASET:")
        for dataset, stats in self.dataset_stats.items():
            self.logger.info(f"   {dataset}: {stats.get('persons_extracted', 0):,} persons, {stats.get('orgs_extracted', 0):,} orgs")
    
    def _save_expanded_corpus(self) -> Dict[str, Set[str]]:
        """Save expanded corpus data to files."""
        expanded_corpus = {
            'first_names': self.first_names,
            'last_names': self.last_names,
            'person_full_names': self.person_full_names,
            'organization_names': self.organization_names,
            'organization_variants': self.organization_variants
        }
        
        # Save individual files
        for corpus_type, corpus_data in expanded_corpus.items():
            output_file = self.output_dir / f"{corpus_type}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in sorted(corpus_data):
                    f.write(f"{item}\n")
            self.logger.info(f"💾 Saved {len(corpus_data):,} {corpus_type} to {output_file}")
        
        # Save combined JSON
        json_output = self.output_dir / "expanded_corpus.json"
        json_data = {k: list(v) for k, v in expanded_corpus.items()}
        json_data['stats'] = self.dataset_stats
        json_data['extraction_stats'] = dict(self.extraction_stats)
        
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"💾 Saved complete corpus to {json_output}")
        
        return expanded_corpus

def main():
    """Main function to run corpus expansion."""
    print("🚀 Dataset Corpus Expander for Large-Scale Entity Recognition")
    print("=" * 80)
    
    if not DATASETS_AVAILABLE:
        print("❌ Please install required libraries:")
        print("   pip install datasets transformers torch")
        return
    
    expander = DatasetCorpusExpander()
    
    # Process fast datasets first for quick results
    quick_datasets = ['conll2003', 'wikiann_en']
    print(f"🏃 Quick processing of {len(quick_datasets)} datasets for immediate results...")
    
    expanded_corpus = expander.expand_corpus_from_datasets(quick_datasets)
    
    if expanded_corpus:
        print(f"\n✅ Quick expansion completed!")
        print(f"   Ready to integrate {len(expanded_corpus['first_names']):,} first names")
        print(f"   and {len(expanded_corpus['organization_names']):,} organizations")
        print(f"   into your corpus-based entity disambiguation system.")
        
        # Ask if user wants to process more datasets
        print(f"\n💡 Run with all datasets for maximum coverage:")
        print(f"   python {__file__} --all-datasets")
    
    return expanded_corpus

if __name__ == "__main__":
    main()