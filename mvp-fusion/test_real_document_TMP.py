#!/usr/bin/env python3
"""
Test Conservative Person Extraction on Real Content
==================================================
Test with content that should have clearly identifiable persons.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from utils.logging_config import setup_logging, get_fusion_logger
from test_person_extraction import process_url_for_persons, PersonEntityExtractor

def test_real_urls():
    """Test on real URLs with known persons"""
    
    setup_logging(verbosity=1)
    logger = get_fusion_logger(__name__)
    
    # Initialize extractor with sample names
    extractor = PersonEntityExtractor(min_confidence=0.7)
    
    # Add comprehensive sample names for testing
    extractor.first_names = {
        'john', 'jane', 'michael', 'sarah', 'tim', 'walt', 'steve',
        'bill', 'jeff', 'mark', 'elon', 'larry', 'sergey', 'susan',
        'mary', 'elizabeth', 'jennifer', 'lisa', 'karen', 'robert',
        'james', 'william', 'david', 'richard', 'thomas', 'charles',
        'daniel', 'matthew', 'anthony', 'christopher', 'satya', 'sundar'
    }
    
    extractor.last_names = {
        'smith', 'johnson', 'williams', 'jones', 'brown', 'davis',
        'miller', 'wilson', 'moore', 'taylor', 'anderson', 'thomas',
        'jackson', 'white', 'harris', 'martin', 'thompson', 'garcia',
        'martinez', 'robinson', 'cook', 'gates', 'jobs', 'musk',
        'bezos', 'zuckerberg', 'page', 'brin', 'dell', 'ellison',
        'nadella', 'pichai', 'dorsey', 'wojcicki', 'sandberg'
    }
    
    extractor.organizations = {
        'apple', 'google', 'microsoft', 'amazon', 'meta', 'tesla',
        'facebook', 'twitter', 'netflix', 'uber', 'airbnb', 'spotify',
        'ibm', 'oracle', 'salesforce', 'adobe', 'intel', 'nvidia',
        'ford', 'general motors', 'disney', 'walmart', 'jpmorgan'
    }
    
    # Test URLs with expected persons
    test_urls = [
        "https://en.wikipedia.org/wiki/Tim_Cook",
        "https://en.wikipedia.org/wiki/Elon_Musk",
        "https://en.wikipedia.org/wiki/Steve_Jobs"
    ]
    
    logger.stage("🌐 Testing Conservative Person Extraction on Real URLs")
    
    for i, url in enumerate(test_urls, 1):
        logger.stage(f"\n{i}. Testing: {url}")
        
        try:
            result = process_url_for_persons(url, extractor)
            
            if 'error' in result:
                logger.logger.error(f"❌ Error processing {url}: {result['error']}")
                continue
            
            persons = result.get('persons', [])
            logger.stage(f"   Found {len(persons)} persons:")
            
            for person in persons[:5]:  # Show top 5
                logger.stage(f"      {person['text']} (confidence: {person['confidence']:.3f})")
                evidence = person.get('evidence', [])
                if evidence:
                    logger.stage(f"         Evidence: {', '.join(evidence[:3])}")
            
            # Show confidence distribution
            dist = result.get('confidence_distribution', {})
            if dist:
                logger.stage(f"   Confidence: Very High={dist.get('very_high', 0)}, High={dist.get('high', 0)}, Medium={dist.get('medium', 0)}")
                logger.stage(f"   Average confidence: {dist.get('avg_confidence', 0):.3f}")
            
        except Exception as e:
            logger.logger.error(f"❌ Exception processing {url}: {e}")

def test_text_samples():
    """Test on sample text with clear and ambiguous persons"""
    
    logger = get_fusion_logger(__name__)
    logger.stage("\n📝 Testing on Sample Text Content")
    
    # Initialize extractor
    extractor = PersonEntityExtractor(min_confidence=0.7)
    
    # Add sample names
    extractor.first_names = {'tim', 'steve', 'bill', 'john', 'jane', 'walt', 'elon', 'mark'}
    extractor.last_names = {'cook', 'jobs', 'gates', 'doe', 'smith', 'disney', 'musk', 'zuckerberg'}
    extractor.organizations = {'apple', 'microsoft', 'disney', 'tesla', 'meta', 'facebook'}
    
    # Test cases with clear persons
    test_cases = [
        {
            'name': 'CEO Announcements',
            'text': '''
            Tim Cook, CEO of Apple Inc., announced new products yesterday.
            Microsoft's CEO Satya Nadella spoke about AI developments.
            Elon Musk, founder of Tesla and SpaceX, tweeted about Mars missions.
            Dr. Jane Smith, professor at Stanford University, published research findings.
            '''
        },
        {
            'name': 'Biographical Content',
            'text': '''
            Steve Jobs was born in 1955 and co-founded Apple Computer Company.
            Walt Disney founded Disney Studios in 1923 and created Mickey Mouse.
            Bill Gates, co-founder of Microsoft, is known for his philanthropic work.
            Mark Zuckerberg founded Facebook while studying at Harvard University.
            '''
        },
        {
            'name': 'Mixed Ambiguous',
            'text': '''
            Apple reported strong quarterly earnings. Ford announced new vehicle models.
            Disney+ streaming service gained millions of subscribers. Microsoft Azure
            cloud services experienced growth. Tesla stock price increased significantly.
            '''
        }
    ]
    
    for test_case in test_cases:
        logger.stage(f"\n📋 Test Case: {test_case['name']}")
        
        persons = extractor.extract_persons(test_case['text'])
        
        logger.stage(f"   Found {len(persons)} persons:")
        for person in persons:
            logger.stage(f"      ✓ {person['text']} (confidence: {person['confidence']:.3f})")
            evidence = person.get('evidence', [])
            if evidence:
                logger.stage(f"         Evidence: {', '.join(evidence[:2])}")
        
        if not persons:
            logger.stage(f"      (No persons found - conservative validation working)")

if __name__ == "__main__":
    print("="*60)
    print("REAL DOCUMENT PERSON EXTRACTION TEST")
    print("="*60)
    
    # Test with text samples first (faster)
    test_text_samples()
    
    # Test with real URLs (requires internet)
    test_real_urls()
    
    print("\n" + "="*60)
    print("✅ Real document testing completed!")
    print("="*60)