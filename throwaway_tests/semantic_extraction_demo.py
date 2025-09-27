#!/usr/bin/env python3
"""
Semantic Extraction Improvement Demo - THROWAWAY TEST
=====================================================

GOAL: Demonstrate how cleaned markdown improves entity extraction
REASON: Show reduction in false positives and better semantic fact quality
PROBLEM: Website noise creates false entities and poor knowledge extraction

This script analyzes entity extraction quality on both markdown versions.
"""

import sys
import re
from pathlib import Path

# Add mvp-fusion to path  
sys.path.insert(0, str(Path(__file__).parent.parent))


def extract_simple_entities(text: str) -> dict:
    """Simple entity extraction for demonstration (no FLPC for this throwaway test)."""
    entities = {
        'organizations': [],
        'people': [],
        'money': [],
        'dates': [],
        'measurements': [],
        'urls': [],
        'noise_indicators': []
    }
    
    # Simple patterns for demo (would use FLPC in production)
    org_patterns = [
        r'\b(?:CTGS|Staples|Freddie Mac|Shell Oil|Motiva|State Farm|General Electric|CVS|HireAction|Sun Microsystems|Amway)\b',
        r'\b[A-Z][a-z]+ (?:Inc|LLC|Corp|Corporation|Company|Group|Partners|Solutions)\b'
    ]
    
    people_patterns = [
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b(?=.*(?:CEO|CTO|founder|partner|director))'
    ]
    
    money_patterns = [
        r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
        r'\b\d+\s*(?:million|billion|thousand)\s*dollars?\b'
    ]
    
    date_patterns = [
        r'\b(?:20\d{2}|19\d{2})\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
    ]
    
    measurement_patterns = [
        r'\b\d+\s*(?:years?|months?|days?|hours?|minutes?)\b',
        r'\b\d+%\b'
    ]
    
    url_patterns = [
        r'https?://[^\s\)]+',
        r'www\.[^\s\)]+',
        r'%[0-9A-F]{2}',  # URL encoding artifacts
        r'elementor-action',
        r'utm_\w+'
    ]
    
    noise_patterns = [
        r'Skip to content',
        r'Google tag \(gtag\.js\)',
        r'Cookie[s]?',
        r'Privacy Policy',
        r'Terms of Service',
        r'Accept All',
        r'Manage choices',
        r'Newsletter',
        r'Subscribe'
    ]
    
    # Extract entities
    all_patterns = [
        ('organizations', org_patterns),
        ('people', people_patterns), 
        ('money', money_patterns),
        ('dates', date_patterns),
        ('measurements', measurement_patterns),
        ('urls', url_patterns),
        ('noise_indicators', noise_patterns)
    ]
    
    for category, patterns in all_patterns:
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities[category].extend(matches)
    
    # Remove duplicates while preserving order
    for category in entities:
        entities[category] = list(dict.fromkeys(entities[category]))
    
    return entities


def analyze_semantic_quality(entities: dict, text: str) -> dict:
    """Analyze semantic extraction quality."""
    total_entities = sum(len(entities[cat]) for cat in entities if cat != 'noise_indicators')
    noise_entities = len(entities['noise_indicators']) + len(entities['urls'])
    
    # Calculate signal-to-noise ratio
    signal_entities = total_entities - noise_entities
    noise_ratio = noise_entities / total_entities if total_entities > 0 else 0
    signal_ratio = signal_entities / total_entities if total_entities > 0 else 0
    
    # Entity density (entities per 100 words)
    word_count = len(text.split())
    entity_density = (total_entities / word_count * 100) if word_count > 0 else 0
    
    # Quality score (higher is better)
    quality_score = signal_ratio * (1 - noise_ratio) * min(entity_density / 5, 1) * 100
    
    return {
        'total_entities': total_entities,
        'signal_entities': signal_entities,
        'noise_entities': noise_entities,
        'signal_ratio': signal_ratio,
        'noise_ratio': noise_ratio,
        'entity_density': entity_density,
        'quality_score': quality_score,
        'word_count': word_count
    }


def print_entity_comparison(current_entities: dict, enhanced_entities: dict):
    """Print detailed entity extraction comparison."""
    print("\n" + "="*80)
    print("🧠 ENTITY EXTRACTION COMPARISON")
    print("="*80)
    
    categories = ['organizations', 'people', 'money', 'dates', 'measurements', 'urls', 'noise_indicators']
    
    for category in categories:
        current_count = len(current_entities[category])
        enhanced_count = len(enhanced_entities[category])
        change = enhanced_count - current_count
        
        print(f"\n📊 {category.upper()}:")
        print(f"   Current: {current_count} | Enhanced: {enhanced_count} | Change: {change:+d}")
        
        if category in ['urls', 'noise_indicators']:
            # For noise categories, show what was removed
            if current_count > enhanced_count:
                removed = set(current_entities[category]) - set(enhanced_entities[category])
                if removed:
                    print(f"   Removed noise: {list(removed)[:3]}{'...' if len(removed) > 3 else ''}")
        else:
            # For content categories, show new entities found
            if enhanced_count > current_count:
                new_entities = set(enhanced_entities[category]) - set(current_entities[category])
                if new_entities:
                    print(f"   New entities: {list(new_entities)[:3]}{'...' if len(new_entities) > 3 else ''}")
        
        # Show top entities for each
        if current_entities[category]:
            print(f"   Current top 3: {current_entities[category][:3]}")
        if enhanced_entities[category]:
            print(f"   Enhanced top 3: {enhanced_entities[category][:3]}")


def main():
    """Main semantic extraction demo."""
    print("🧠 SEMANTIC EXTRACTION QUALITY DEMO")
    print("Comparing entity extraction on Current vs Enhanced markdown")
    
    # Load the markdown files generated by previous test
    markdown_files = list(Path("throwaway_tests/").glob("*_markdown_*.md"))
    
    if len(markdown_files) < 2:
        print("❌ Markdown files not found. Run test_markdown_quality.py first.")
        return
    
    # Find current and enhanced markdown files
    current_file = next((f for f in markdown_files if 'current' in f.name), None)
    enhanced_file = next((f for f in markdown_files if 'enhanced' in f.name), None)
    
    if not current_file or not enhanced_file:
        print("❌ Could not find both current and enhanced markdown files.")
        return
    
    # Load markdown content
    with open(current_file, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    with open(enhanced_file, 'r', encoding='utf-8') as f:
        enhanced_content = f.read()
    
    # Extract just the markdown content (skip the header)
    current_markdown = '\n'.join(current_content.split('\n')[4:])  # Skip header
    enhanced_markdown = '\n'.join(enhanced_content.split('\n')[4:])  # Skip header
    
    print(f"\n📄 Analyzing content:")
    print(f"   Current markdown: {len(current_markdown)} characters")
    print(f"   Enhanced markdown: {len(enhanced_markdown)} characters")
    
    # Extract entities
    print("\n🔍 Extracting entities...")
    current_entities = extract_simple_entities(current_markdown)
    enhanced_entities = extract_simple_entities(enhanced_markdown)
    
    # Analyze quality
    current_quality = analyze_semantic_quality(current_entities, current_markdown)
    enhanced_quality = analyze_semantic_quality(enhanced_entities, enhanced_markdown)
    
    # Print entity comparison
    print_entity_comparison(current_entities, enhanced_entities)
    
    # Print quality metrics
    print("\n" + "="*80)
    print("📈 SEMANTIC QUALITY METRICS")
    print("="*80)
    
    metrics = [
        ('Total Entities', 'total_entities'),
        ('Signal Entities', 'signal_entities'),
        ('Noise Entities', 'noise_entities'),
        ('Word Count', 'word_count'),
        ('Entity Density', 'entity_density'),
        ('Signal Ratio %', 'signal_ratio'),
        ('Noise Ratio %', 'noise_ratio'),
        ('Quality Score', 'quality_score')
    ]
    
    print(f"{'Metric':<20} {'Current':<15} {'Enhanced':<15} {'Change':<15}")
    print("-" * 70)
    
    for metric_name, metric_key in metrics:
        current_val = current_quality[metric_key]
        enhanced_val = enhanced_quality[metric_key]
        change = enhanced_val - current_val
        
        if 'ratio' in metric_key:
            print(f"{metric_name:<20} {current_val*100:.1f}%{'':<10} {enhanced_val*100:.1f}%{'':<10} {change*100:+.1f}%")
        elif metric_key in ['entity_density', 'quality_score']:
            print(f"{metric_name:<20} {current_val:.1f}{'':<12} {enhanced_val:.1f}{'':<12} {change:+.1f}")
        else:
            print(f"{metric_name:<20} {current_val:<15} {enhanced_val:<15} {change:+d}")
    
    # Summary
    improvement_pct = ((enhanced_quality['quality_score'] - current_quality['quality_score']) / current_quality['quality_score'] * 100) if current_quality['quality_score'] > 0 else 0
    noise_reduction_pct = ((current_quality['noise_ratio'] - enhanced_quality['noise_ratio']) / current_quality['noise_ratio'] * 100) if current_quality['noise_ratio'] > 0 else 0
    
    print("\n" + "="*80)
    print("🎯 SEMANTIC EXTRACTION IMPROVEMENTS:")
    print(f"   Quality Score: {improvement_pct:+.1f}% improvement")
    print(f"   Noise Reduction: {noise_reduction_pct:.1f}% less noise entities")
    print(f"   Signal Enhancement: {enhanced_quality['signal_entities'] - current_quality['signal_entities']:+d} more meaningful entities")
    print(f"   Cleaner Knowledge: {current_quality['noise_entities'] - enhanced_quality['noise_entities']} fewer noise artifacts")
    
    print("\n✅ Semantic extraction demo completed!")
    print("📊 Enhanced converter produces cleaner input for better knowledge extraction.")


if __name__ == "__main__":
    main()