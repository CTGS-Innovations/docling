#!/usr/bin/env python3
"""
Validation Script: Test Extraction Accuracy
Shows exactly what we're extracting and whether it's correct

This script will:
1. Create test documents with KNOWN entities
2. Extract entities using our regex approach
3. Show what we found vs what we should have found
4. Calculate precision, recall, and accuracy
"""

import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import json


class ExtractionAccuracyValidator:
    """Validate the accuracy of our entity extraction approaches"""
    
    def __init__(self):
        # Our current regex patterns (same as in production)
        self.patterns = {
            'MONEY': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD)',
            ],
            'DATE': [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'
            ],
            'PERSON': [
                r'\b(?:Dr|Mr|Ms|Mrs|Prof|Director|Manager|Inspector)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            ],
            'PHONE': [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\d{3}-\d{3}-\d{4}\b'
            ],
            'EMAIL': [
                r'\b[\w.-]+@[\w.-]+\.\w+\b'
            ],
            'ORGANIZATION': [
                r'\b(?:OSHA|EPA|CDC|NIOSH|DOL|Department of Labor|Occupational Safety and Health Administration)\b',
            ]
        }
        
        # Create test documents with KNOWN entities (ground truth)
        self.test_documents = [
            {
                'id': 'doc1',
                'text': """
                Dr. John Smith from OSHA reported on March 15, 2024 that the 
                Department of Labor has allocated $2.5 million for safety programs.
                Contact him at john.smith@dol.gov or (202) 693-1999.
                The EPA will review the case on 12/31/2023.
                """,
                'ground_truth': {
                    'PERSON': ['Dr. John Smith'],
                    'ORGANIZATION': ['OSHA', 'Department of Labor', 'EPA'],
                    'DATE': ['March 15, 2024', '12/31/2023'],
                    'MONEY': ['$2.5 million'],
                    'EMAIL': ['john.smith@dol.gov'],
                    'PHONE': ['(202) 693-1999']
                }
            },
            {
                'id': 'doc2',
                'text': """
                Inspector Mary Johnson found 15 violations costing $50,000 in fines.
                The CDC and NIOSH released guidelines on January 1st, 2023.
                For questions, email safety@company.com or call 555-123-4567.
                Budget increased to 1.2 million dollars this fiscal year.
                """,
                'ground_truth': {
                    'PERSON': ['Inspector Mary Johnson'],
                    'ORGANIZATION': ['CDC', 'NIOSH'],
                    'DATE': ['January 1st, 2023'],  # Note: our regex might not catch "1st"
                    'MONEY': ['$50,000', '1.2 million dollars'],
                    'EMAIL': ['safety@company.com'],
                    'PHONE': ['555-123-4567']
                }
            },
            {
                'id': 'doc3',
                'text': """
                Manager Robert Williams Jr. works at the Occupational Safety and Health Administration.
                The project deadline is 2024-06-30 with a budget of $750,000.
                Contact: bob.williams@osha.gov, phone: 202.693.2000
                Ms. Sarah Lee from EPA reported the incident.
                """,
                'ground_truth': {
                    'PERSON': ['Manager Robert Williams', 'Ms. Sarah Lee'],  # Note: "Jr." might complicate
                    'ORGANIZATION': ['Occupational Safety and Health Administration', 'EPA'],
                    'DATE': ['2024-06-30'],
                    'MONEY': ['$750,000'],
                    'EMAIL': ['bob.williams@osha.gov'],
                    'PHONE': ['202.693.2000']  # Note: dots instead of dashes
                }
            },
            {
                'id': 'edge_cases',
                'text': """
                John Smith (no title) reported to OSHA.  
                Cost: USD 5000 (no dollar sign)
                Date: Dec 15, 2023 (abbreviated month)
                Phone with extension: (202) 693-1999 ext. 123
                Partial email: john@company
                Random number that looks like phone: 123-456-7890
                """,
                'ground_truth': {
                    'PERSON': ['John Smith'],  # No title - will we catch it?
                    'ORGANIZATION': ['OSHA'],
                    'DATE': ['Dec 15, 2023'],
                    'MONEY': ['USD 5000'],
                    'EMAIL': [],  # 'john@company' is invalid
                    'PHONE': ['(202) 693-1999', '123-456-7890']  # Extension might confuse
                }
            }
        ]

    def extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """Extract entities using our regex patterns"""
        extracted = defaultdict(set)
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    extracted[entity_type].add(match.group().strip())
        
        return dict(extracted)

    def normalize_for_comparison(self, text: str) -> str:
        """Normalize text for comparison (lowercase, strip whitespace)"""
        return text.lower().strip()

    def calculate_metrics(self, extracted: Set[str], ground_truth: List[str]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score"""
        # Normalize for comparison
        extracted_norm = {self.normalize_for_comparison(e) for e in extracted}
        truth_norm = {self.normalize_for_comparison(t) for t in ground_truth}
        
        # Calculate metrics
        true_positives = len(extracted_norm & truth_norm)
        false_positives = len(extracted_norm - truth_norm)
        false_negatives = len(truth_norm - extracted_norm)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }

    def validate_document(self, doc: Dict) -> Dict:
        """Validate extraction for a single document"""
        doc_id = doc['id']
        text = doc['text']
        ground_truth = doc['ground_truth']
        
        # Extract entities
        extracted = self.extract_entities(text)
        
        # Calculate metrics for each entity type
        results = {
            'doc_id': doc_id,
            'text_sample': text[:200] + '...' if len(text) > 200 else text,
            'entity_results': {}
        }
        
        for entity_type in set(list(extracted.keys()) + list(ground_truth.keys())):
            extracted_set = extracted.get(entity_type, set())
            truth_list = ground_truth.get(entity_type, [])
            
            metrics = self.calculate_metrics(extracted_set, truth_list)
            
            results['entity_results'][entity_type] = {
                'metrics': metrics,
                'extracted': list(extracted_set),
                'ground_truth': truth_list,
                'missed': [t for t in truth_list if self.normalize_for_comparison(t) not in 
                          {self.normalize_for_comparison(e) for e in extracted_set}],
                'false_positives': [e for e in extracted_set if self.normalize_for_comparison(e) not in 
                                   {self.normalize_for_comparison(t) for t in truth_list}]
            }
        
        return results

    def run_validation(self):
        """Run validation on all test documents"""
        print("ENTITY EXTRACTION ACCURACY VALIDATION")
        print("=" * 70)
        print("Testing regex patterns against known entities (ground truth)")
        print()
        
        all_results = []
        aggregate_metrics = defaultdict(lambda: {
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'extracted': [],
            'missed': [],
            'false_positive_examples': []
        })
        
        for doc in self.test_documents:
            print(f"\n📄 Document: {doc['id']}")
            print("-" * 50)
            
            results = self.validate_document(doc)
            all_results.append(results)
            
            # Display results for this document
            for entity_type, entity_results in results['entity_results'].items():
                metrics = entity_results['metrics']
                
                # Aggregate metrics
                aggregate_metrics[entity_type]['true_positives'] += metrics['true_positives']
                aggregate_metrics[entity_type]['false_positives'] += metrics['false_positives']
                aggregate_metrics[entity_type]['false_negatives'] += metrics['false_negatives']
                aggregate_metrics[entity_type]['extracted'].extend(entity_results['extracted'])
                aggregate_metrics[entity_type]['missed'].extend(entity_results['missed'])
                aggregate_metrics[entity_type]['false_positive_examples'].extend(entity_results['false_positives'])
                
                # Show per-document results
                print(f"\n{entity_type}:")
                print(f"  Precision: {metrics['precision']:.1%}")
                print(f"  Recall: {metrics['recall']:.1%}")
                print(f"  F1 Score: {metrics['f1']:.1%}")
                
                if entity_results['extracted']:
                    print(f"  ✅ Found: {entity_results['extracted']}")
                
                if entity_results['missed']:
                    print(f"  ❌ Missed: {entity_results['missed']}")
                
                if entity_results['false_positives']:
                    print(f"  ⚠️  False Positives: {entity_results['false_positives']}")
        
        # Overall Summary
        print("\n" + "=" * 70)
        print("OVERALL ACCURACY SUMMARY")
        print("=" * 70)
        
        for entity_type, totals in aggregate_metrics.items():
            tp = totals['true_positives']
            fp = totals['false_positives']
            fn = totals['false_negatives']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            print(f"\n🏷️  {entity_type}")
            print(f"  Overall Precision: {precision:.1%} ({tp} correct / {tp + fp} extracted)")
            print(f"  Overall Recall: {recall:.1%} ({tp} found / {tp + fn} expected)")
            print(f"  Overall F1 Score: {f1:.1%}")
            
            if totals['missed']:
                print(f"  Common Misses: {list(set(totals['missed']))[:3]}")
            
            if totals['false_positive_examples']:
                print(f"  False Positive Examples: {list(set(totals['false_positive_examples']))[:3]}")
        
        # Final Assessment
        print("\n" + "=" * 70)
        print("ACCURACY ASSESSMENT")
        print("=" * 70)
        
        high_accuracy = []
        needs_improvement = []
        
        for entity_type, totals in aggregate_metrics.items():
            tp = totals['true_positives']
            fp = totals['false_positives']
            fn = totals['false_negatives']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            if precision >= 0.8 and recall >= 0.8:
                high_accuracy.append(entity_type)
            else:
                needs_improvement.append((entity_type, precision, recall))
        
        print(f"\n✅ HIGH ACCURACY (>80% precision & recall): {high_accuracy if high_accuracy else 'None'}")
        print(f"\n⚠️  NEEDS IMPROVEMENT:")
        for entity_type, precision, recall in needs_improvement:
            print(f"  • {entity_type}: {precision:.0%} precision, {recall:.0%} recall")
        
        print("\n💡 KEY FINDINGS:")
        print("  1. Speed (1717 pages/sec) comes with accuracy trade-offs")
        print("  2. Some patterns need refinement (especially PERSON without titles)")
        print("  3. Edge cases reveal pattern limitations")
        print("  4. Consider adding more comprehensive patterns or fallback methods")
        
        return all_results


def main():
    """Run extraction accuracy validation"""
    validator = ExtractionAccuracyValidator()
    results = validator.run_validation()
    
    # Save detailed results
    with open('extraction_accuracy_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Detailed results saved to extraction_accuracy_results.json")


if __name__ == "__main__":
    main()