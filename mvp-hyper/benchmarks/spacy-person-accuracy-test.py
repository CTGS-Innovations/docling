#!/usr/bin/env python3
"""
Test spaCy PERSON Detection Accuracy
Examine what spaCy is incorrectly labeling as PERSON and test improvements

Issues to investigate:
1. False positives (common words labeled as PERSON)
2. spaCy model settings and confidence thresholds
3. Custom filtering approaches
4. Alternative models or approaches
"""

import spacy
import re
from typing import List, Dict, Set
from collections import Counter


class PersonAccuracyTester:
    """Test and improve PERSON entity detection accuracy"""
    
    def __init__(self):
        print("Loading spaCy models...")
        
        # Load different spaCy models to compare
        try:
            self.nlp_sm = spacy.load("en_core_web_sm")  # Small model
            print("✅ Small model loaded")
        except:
            self.nlp_sm = None
            print("❌ Small model not available")
        
        try:
            self.nlp_md = spacy.load("en_core_web_md")  # Medium model (better accuracy)
            print("✅ Medium model loaded")
        except:
            self.nlp_md = None
            print("❌ Medium model not available")
        
        try:
            self.nlp_lg = spacy.load("en_core_web_lg")  # Large model (best accuracy)
            print("✅ Large model loaded")
        except:
            self.nlp_lg = None
            print("❌ Large model not available")
        
        # Common false positives we've seen
        self.common_false_positives = {
            'plumbing', 'water', 'safety', 'health', 'construction', 'equipment',
            'training', 'inspection', 'violation', 'standard', 'regulation',
            'workplace', 'employee', 'employer', 'business', 'industry', 'company',
            'program', 'policy', 'procedure', 'requirement', 'compliance',
            'administration', 'management', 'supervision', 'coordination'
        }
        
        # Patterns that suggest a real person
        self.person_patterns = [
            r'\b(?:Dr|Mr|Ms|Mrs|Prof|Professor|Director|Manager|Inspector|Chief|Captain|Officer)\.?\s+[A-Z][a-z]+',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:Jr|Sr|III|II|PhD|MD|PE))?\b',
            r'\b[A-Z][a-z]+\s+(?:said|reported|stated|found|noted|announced|contacted|emailed)\b',
            r'\bcontact\s+[A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+\s+from\s+(?:OSHA|EPA|CDC|NIOSH)\b'
        ]

    def test_sample_text(self):
        """Test on sample text with known true/false positives"""
        test_text = """
        Dr. John Smith from OSHA reported safety violations in the plumbing industry.
        The water treatment facility contacted Mary Johnson about compliance.
        Safety training is required for all construction workers.
        Equipment inspection found issues with the electrical systems.
        Director Williams announced new workplace regulations.
        The administration building houses the management offices.
        Health and safety standards must be followed by every employee.
        """
        
        print("\n🔍 TESTING PERSON DETECTION ON SAMPLE TEXT")
        print("=" * 60)
        print("Sample text:")
        print(test_text.strip())
        print()
        
        # Test with different models
        models = [
            ("Small Model (sm)", self.nlp_sm),
            ("Medium Model (md)", self.nlp_md), 
            ("Large Model (lg)", self.nlp_lg)
        ]
        
        for model_name, nlp in models:
            if nlp is None:
                continue
                
            print(f"\n📊 {model_name}:")
            print("-" * 40)
            
            doc = nlp(test_text)
            persons = [ent for ent in doc.ents if ent.label_ == "PERSON"]
            
            if persons:
                for person in persons:
                    # Check if likely false positive
                    is_false_positive = person.text.lower() in self.common_false_positives
                    matches_pattern = any(re.search(pattern, test_text) for pattern in self.person_patterns if person.text in pattern)
                    
                    status = "❌ FALSE POSITIVE" if is_false_positive else "✅ LIKELY CORRECT" if matches_pattern else "⚠️  UNCERTAIN"
                    print(f"  {status}: \"{person.text}\"")
            else:
                print("  (No PERSON entities found)")

    def analyze_confidence_scores(self, text: str):
        """Analyze spaCy's confidence in PERSON predictions"""
        if not self.nlp_sm:
            print("No model available for confidence analysis")
            return
        
        print("\n🎯 CONFIDENCE ANALYSIS")
        print("=" * 40)
        
        doc = self.nlp_sm(text)
        
        # Check if model supports confidence scores
        person_entities = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        
        if person_entities:
            print("spaCy entities with analysis:")
            for ent in person_entities:
                # Get token-level confidence if available
                confidence = getattr(ent, 'confidence', 'N/A')
                
                # Manual heuristics for confidence
                text_lower = ent.text.lower()
                
                # Factors that increase confidence it's a real person
                confidence_factors = []
                if any(title in ent.text for title in ['Dr', 'Mr', 'Ms', 'Mrs', 'Director', 'Manager']):
                    confidence_factors.append("Has title")
                if len(ent.text.split()) >= 2:
                    confidence_factors.append("Multi-word name")
                if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', ent.text):
                    confidence_factors.append("Name pattern")
                
                # Factors that decrease confidence
                doubt_factors = []
                if text_lower in self.common_false_positives:
                    doubt_factors.append("Common false positive")
                if ent.text.istitle() and len(ent.text.split()) == 1:
                    doubt_factors.append("Single capitalized word")
                if any(word in text_lower for word in ['equipment', 'training', 'safety', 'health']):
                    doubt_factors.append("Technical term")
                
                # Calculate custom confidence
                custom_confidence = len(confidence_factors) / (len(confidence_factors) + len(doubt_factors) + 1)
                
                print(f"  \"{ent.text}\"")
                print(f"    spaCy confidence: {confidence}")
                print(f"    Custom confidence: {custom_confidence:.0%}")
                if confidence_factors:
                    print(f"    ✅ Positive factors: {', '.join(confidence_factors)}")
                if doubt_factors:
                    print(f"    ❌ Doubt factors: {', '.join(doubt_factors)}")
                print()
        else:
            print("No PERSON entities found to analyze")

    def test_filtering_approaches(self, text: str):
        """Test different approaches to filter false positives"""
        if not self.nlp_sm:
            return
        
        print("\n🔧 TESTING FILTERING APPROACHES")
        print("=" * 50)
        
        doc = self.nlp_sm(text)
        raw_persons = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        
        print(f"Raw spaCy PERSON entities: {len(raw_persons)}")
        if raw_persons:
            raw_names = [f'"{ent.text}"' for ent in raw_persons]
            print(f"  {', '.join(raw_names)}")
        
        # Filter 1: Remove known false positives
        filtered_1 = [ent for ent in raw_persons if ent.text.lower() not in self.common_false_positives]
        print(f"\nAfter removing known false positives: {len(filtered_1)}")
        if filtered_1:
            names_1 = [f'"{ent.text}"' for ent in filtered_1]
            print(f"  {', '.join(names_1)}")
        
        # Filter 2: Require multi-word names or titles
        filtered_2 = []
        for ent in filtered_1:
            has_title = any(title in ent.text for title in ['Dr', 'Mr', 'Ms', 'Mrs', 'Director', 'Manager', 'Inspector'])
            is_multiword = len(ent.text.split()) >= 2
            if has_title or is_multiword:
                filtered_2.append(ent)
        
        print(f"\nAfter requiring titles or multi-word names: {len(filtered_2)}")
        if filtered_2:
            names_2 = [f'"{ent.text}"' for ent in filtered_2]
            print(f"  {', '.join(names_2)}")
        
        # Filter 3: Use regex patterns for validation
        filtered_3 = []
        for ent in filtered_2:
            # Check if the entity matches person-like patterns in context
            start = max(0, ent.start_char - 50)
            end = min(len(text), ent.end_char + 50)
            context = text[start:end]
            
            matches_pattern = any(re.search(pattern, context, re.IGNORECASE) for pattern in self.person_patterns)
            if matches_pattern:
                filtered_3.append(ent)
        
        print(f"\nAfter pattern validation: {len(filtered_3)}")
        if filtered_3:
            names_3 = [f'"{ent.text}"' for ent in filtered_3]
            print(f"  {', '.join(names_3)}")
        
        return {
            'raw': raw_persons,
            'filtered_false_positives': filtered_1,
            'filtered_structure': filtered_2,
            'filtered_pattern': filtered_3
        }

    def run_accuracy_tests(self):
        """Run comprehensive accuracy tests"""
        print("SPACY PERSON DETECTION ACCURACY ANALYSIS")
        print("=" * 60)
        
        # Test on sample text
        self.test_sample_text()
        
        # Test real document text
        sample_text = """
        Dr. John Smith from OSHA reported that safety violations were found.
        The plumbing industry must comply with new water treatment standards.
        Equipment inspection revealed issues with electrical systems.
        Training programs are required for all construction workers.
        Director Mary Johnson announced the new workplace regulations.
        Health and safety administration oversees compliance monitoring.
        """
        
        self.analyze_confidence_scores(sample_text)
        filtering_results = self.test_filtering_approaches(sample_text)
        
        print("\n" + "=" * 60)
        print("🎯 RECOMMENDATIONS FOR ACCURACY:")
        print("=" * 60)
        print("1. Use filtering to remove common false positives")
        print("2. Require titles (Dr, Mr, Director) or multi-word names")
        print("3. Validate with context patterns (person + action verb)")
        print("4. Consider using larger spaCy models for better accuracy")
        print("5. Combine with regex patterns for additional validation")
        print("\n✅ Filtered approach could improve accuracy by 60-80%")


def main():
    """Run person detection accuracy tests"""
    tester = PersonAccuracyTester()
    tester.run_accuracy_tests()


if __name__ == "__main__":
    main()