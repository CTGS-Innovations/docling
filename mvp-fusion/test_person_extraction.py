#!/usr/bin/env python3
"""
Test Person Entity Extraction on Documents and URLs
===================================================
Test the conservative person entity extractor with real documents and URLs.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict
import json
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from utils.person_entity_extractor import PersonEntityExtractor, ConfidenceLevel
from utils.logging_config import setup_logging, get_fusion_logger
from fusion_cli import process_single_file, process_single_url, download_url_content

def extract_persons_from_text(text: str, extractor: PersonEntityExtractor) -> List[Dict]:
    """Extract person entities from text"""
    persons = extractor.extract_persons(text)
    return persons

def process_document_for_persons(file_path: Path, extractor: PersonEntityExtractor) -> Dict:
    """Process a document and extract person entities"""
    logger = get_fusion_logger(__name__)
    
    logger.stage(f"📄 Processing document: {file_path.name}")
    
    # Read the document content
    if file_path.suffix.lower() == '.md':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # For other formats, we might need to use the fusion pipeline
        # For now, let's handle text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return {'error': str(e)}
    
    # Extract persons
    persons = extract_persons_from_text(content, extractor)
    
    # Analyze results
    result = {
        'file': str(file_path),
        'total_persons': len(persons),
        'persons': persons,
        'confidence_distribution': analyze_confidence_distribution(persons)
    }
    
    return result

def process_url_for_persons(url: str, extractor: PersonEntityExtractor) -> Dict:
    """Process a URL and extract person entities"""
    logger = get_fusion_logger(__name__)
    
    logger.stage(f"🌐 Processing URL: {url}")
    
    try:
        # Download URL content
        content, content_type, file_ext, status_code, headers = download_url_content(url)
        
        if status_code != 200:
            return {'error': f'HTTP {status_code}', 'url': url}
        
        # Convert content to text
        if file_ext in ['.html', '.htm']:
            # Simple HTML text extraction (you might want to use BeautifulSoup for better results)
            import re
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', content.decode('utf-8', errors='ignore'))
            # Clean up whitespace
            text = ' '.join(text.split())
        else:
            text = content.decode('utf-8', errors='ignore')
        
        # Extract persons
        persons = extract_persons_from_text(text, extractor)
        
        # Analyze results
        result = {
            'url': url,
            'content_type': content_type,
            'total_persons': len(persons),
            'persons': persons,
            'confidence_distribution': analyze_confidence_distribution(persons)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        return {'error': str(e), 'url': url}

def analyze_confidence_distribution(persons: List[Dict]) -> Dict:
    """Analyze the confidence distribution of extracted persons"""
    if not persons:
        return {}
    
    distribution = {
        'very_high': 0,  # >= 0.9
        'high': 0,       # >= 0.8
        'medium': 0,     # >= 0.7
        'total': len(persons)
    }
    
    for person in persons:
        confidence = person['confidence']
        if confidence >= 0.9:
            distribution['very_high'] += 1
        elif confidence >= 0.8:
            distribution['high'] += 1
        else:
            distribution['medium'] += 1
    
    # Calculate percentages
    total = distribution['total']
    distribution['very_high_pct'] = (distribution['very_high'] / total * 100) if total > 0 else 0
    distribution['high_pct'] = (distribution['high'] / total * 100) if total > 0 else 0
    distribution['medium_pct'] = (distribution['medium'] / total * 100) if total > 0 else 0
    
    # Calculate average confidence
    if persons:
        distribution['avg_confidence'] = sum(p['confidence'] for p in persons) / len(persons)
    else:
        distribution['avg_confidence'] = 0
    
    return distribution

def print_results(results: Dict, verbose: bool = False):
    """Print extraction results"""
    logger = get_fusion_logger(__name__)
    
    print("\n" + "="*60)
    print("PERSON ENTITY EXTRACTION RESULTS")
    print("="*60)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Source: {results.get('file') or results.get('url')}")
    print(f"   Total persons found: {results['total_persons']}")
    
    # Confidence distribution
    dist = results.get('confidence_distribution', {})
    if dist:
        print(f"\n📈 Confidence Distribution:")
        print(f"   Very High (≥0.9): {dist.get('very_high', 0)} ({dist.get('very_high_pct', 0):.1f}%)")
        print(f"   High (≥0.8):      {dist.get('high', 0)} ({dist.get('high_pct', 0):.1f}%)")
        print(f"   Medium (≥0.7):    {dist.get('medium', 0)} ({dist.get('medium_pct', 0):.1f}%)")
        print(f"   Average:          {dist.get('avg_confidence', 0):.3f}")
    
    # Detailed person list
    if results['persons']:
        print(f"\n👥 Persons Found:")
        
        # Sort by confidence
        persons = sorted(results['persons'], key=lambda x: x['confidence'], reverse=True)
        
        # Show top persons (or all if verbose)
        limit = len(persons) if verbose else min(10, len(persons))
        
        for i, person in enumerate(persons[:limit], 1):
            print(f"\n   {i}. {person['text']}")
            print(f"      Confidence: {person['confidence']:.3f}")
            
            if verbose and person.get('evidence'):
                print(f"      Evidence: {', '.join(person['evidence'][:5])}")
            
            if verbose and person.get('context'):
                # Show truncated context
                context = person['context'].replace('\n', ' ')[:100]
                print(f"      Context: ...{context}...")
        
        if not verbose and len(persons) > limit:
            print(f"\n   ... and {len(persons) - limit} more (use --verbose to see all)")

def run_batch_test(test_urls: List[str], test_docs: List[Path], 
                   extractor: PersonEntityExtractor, output_file: Path = None):
    """Run batch testing on multiple URLs and documents"""
    logger = get_fusion_logger(__name__)
    
    logger.stage("🚀 Running Batch Test")
    
    all_results = []
    
    # Process documents
    for doc_path in test_docs:
        if doc_path.exists():
            result = process_document_for_persons(doc_path, extractor)
            all_results.append(result)
            print_results(result)
    
    # Process URLs
    for url in test_urls:
        result = process_url_for_persons(url, extractor)
        all_results.append(result)
        print_results(result)
    
    # Generate summary report
    print("\n" + "="*60)
    print("BATCH TEST SUMMARY")
    print("="*60)
    
    total_sources = len(all_results)
    total_persons = sum(r.get('total_persons', 0) for r in all_results if 'error' not in r)
    successful = sum(1 for r in all_results if 'error' not in r)
    failed = total_sources - successful
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Sources processed: {total_sources}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total persons found: {total_persons}")
    
    if successful > 0:
        avg_persons = total_persons / successful
        print(f"   Average persons per source: {avg_persons:.1f}")
    
    # Save results if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(
        description="Test person entity extraction on documents and URLs"
    )
    
    # Input options
    parser.add_argument('--url', type=str, help='Single URL to process')
    parser.add_argument('--file', type=str, help='Single file to process')
    parser.add_argument('--batch-urls', nargs='+', help='Multiple URLs to process')
    parser.add_argument('--batch-files', nargs='+', help='Multiple files to process')
    
    # Corpus options
    parser.add_argument('--first-names', type=str, 
                       help='Path to first names corpus')
    parser.add_argument('--last-names', type=str,
                       help='Path to last names corpus')
    parser.add_argument('--organizations', type=str,
                       help='Path to organizations corpus')
    
    # Configuration options
    parser.add_argument('--min-confidence', type=float, default=0.7,
                       help='Minimum confidence threshold (default: 0.7)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--output', '-o', type=str,
                       help='Save results to JSON file')
    
    # Test suite option
    parser.add_argument('--test-suite', action='store_true',
                       help='Run built-in test suite')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbosity=2 if args.verbose else 1)
    logger = get_fusion_logger(__name__)
    
    # Initialize extractor
    extractor = PersonEntityExtractor(
        first_names_path=Path(args.first_names) if args.first_names else None,
        last_names_path=Path(args.last_names) if args.last_names else None,
        organizations_path=Path(args.organizations) if args.organizations else None,
        min_confidence=args.min_confidence
    )
    
    # Add sample names if no corpus provided (for testing)
    if not args.first_names:
        extractor.first_names = {
            'john', 'jane', 'michael', 'sarah', 'tim', 'walt', 'henry',
            'steve', 'bill', 'jeff', 'mark', 'elon', 'larry', 'sergey',
            'susan', 'mary', 'elizabeth', 'jennifer', 'lisa', 'karen'
        }
    
    if not args.last_names:
        extractor.last_names = {
            'smith', 'johnson', 'williams', 'jones', 'brown', 'davis',
            'miller', 'wilson', 'moore', 'taylor', 'anderson', 'thomas',
            'jackson', 'white', 'harris', 'martin', 'thompson', 'garcia',
            'martinez', 'robinson', 'cook', 'gates', 'jobs', 'musk',
            'bezos', 'zuckerberg', 'page', 'brin', 'dell', 'ellison'
        }
    
    if not args.organizations:
        extractor.organizations = {
            'apple', 'google', 'microsoft', 'amazon', 'meta', 'tesla',
            'facebook', 'twitter', 'netflix', 'uber', 'airbnb', 'spotify',
            'ibm', 'oracle', 'salesforce', 'adobe', 'intel', 'nvidia'
        }
    
    logger.stage(f"🔧 Person Entity Extractor Initialized")
    logger.stage(f"   Min confidence: {args.min_confidence}")
    logger.stage(f"   First names loaded: {len(extractor.first_names)}")
    logger.stage(f"   Last names loaded: {len(extractor.last_names)}")
    logger.stage(f"   Organizations loaded: {len(extractor.organizations)}")
    
    # Run test suite
    if args.test_suite:
        from utils.person_entity_extractor import run_tests
        run_tests()
        return
    
    # Process single URL
    if args.url:
        result = process_url_for_persons(args.url, extractor)
        print_results(result, verbose=args.verbose)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
    
    # Process single file
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
        
        result = process_document_for_persons(file_path, extractor)
        print_results(result, verbose=args.verbose)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
    
    # Batch processing
    elif args.batch_urls or args.batch_files:
        urls = args.batch_urls or []
        files = [Path(f) for f in (args.batch_files or [])]
        output_path = Path(args.output) if args.output else None
        
        run_batch_test(urls, files, extractor, output_path)
    
    else:
        # Default test with sample data
        logger.stage("Running default test with sample data...")
        
        # Sample test URLs
        test_urls = [
            "https://en.wikipedia.org/wiki/Steve_Jobs",
            "https://www.apple.com/leadership/",
        ]
        
        # Sample test documents (if they exist)
        test_docs = []
        sample_doc = Path("sample_document.txt")
        if sample_doc.exists():
            test_docs.append(sample_doc)
        
        if test_urls or test_docs:
            output_path = Path(args.output) if args.output else None
            run_batch_test(test_urls, test_docs, extractor, output_path)
        else:
            print("No test data available. Use --url, --file, or --test-suite")

if __name__ == "__main__":
    main()