#!/usr/bin/env python3
"""
Markdown Quality Comparison Test - THROWAWAY TEST
=================================================

GOAL: Compare current vs enhanced HTML-to-markdown conversion
REASON: Demonstrate improvement in semantic extraction quality  
PROBLEM: Current markdown has too much noise for good entity extraction

This script tests both converters against the CTGS URL and shows improvements.
"""

import sys
import os
import requests
import time
from pathlib import Path

# Add mvp-fusion to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import current converter
from utils.html_to_markdown_converter import convert_html_to_markdown

# Import enhanced converter
from throwaway_tests.enhanced_html_converter import convert_html_to_markdown_enhanced


def download_url_content(url: str, timeout: int = 15) -> tuple[str, str, int]:
    """Download URL content for testing."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        return response.text, content_type, response.status_code
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return "", "", 0


def analyze_markdown_quality(markdown: str, label: str) -> dict:
    """Analyze markdown quality metrics."""
    lines = markdown.split('\n')
    
    # Count different types of content
    total_lines = len(lines)
    empty_lines = sum(1 for line in lines if not line.strip())
    content_lines = total_lines - empty_lines
    
    # Count markdown elements
    headers = sum(1 for line in lines if line.strip().startswith('#'))
    links = markdown.count('[') + markdown.count('](')
    lists = sum(1 for line in lines if line.strip().startswith(('-', '*', '1.')))
    
    # Count potential noise indicators
    url_artifacts = len([line for line in lines if '%3' in line or 'elementor' in line or 'utm_' in line])
    nav_words = sum(1 for line in lines if any(word in line.lower() for word in ['skip to', 'menu', 'navigation', 'footer', 'header', 'cookie']))
    
    # Content quality score (higher is better)
    content_density = content_lines / total_lines if total_lines > 0 else 0
    noise_ratio = (url_artifacts + nav_words) / content_lines if content_lines > 0 else 1
    quality_score = content_density * (1 - min(noise_ratio, 1)) * 100
    
    return {
        'label': label,
        'total_lines': total_lines,
        'content_lines': content_lines,
        'empty_lines': empty_lines,
        'headers': headers,
        'links': links,
        'lists': lists,
        'url_artifacts': url_artifacts,
        'nav_words': nav_words,
        'content_density': content_density,
        'noise_ratio': noise_ratio,
        'quality_score': quality_score,
        'char_count': len(markdown)
    }


def print_comparison(current_stats: dict, enhanced_stats: dict):
    """Print side-by-side comparison of markdown quality."""
    print("\n" + "="*80)
    print("📊 MARKDOWN QUALITY COMPARISON")
    print("="*80)
    
    print(f"{'Metric':<25} {'Current':<15} {'Enhanced':<15} {'Improvement':<15}")
    print("-" * 75)
    
    # Content metrics
    print(f"{'Total Lines':<25} {current_stats['total_lines']:<15} {enhanced_stats['total_lines']:<15} {enhanced_stats['total_lines'] - current_stats['total_lines']:+d}")
    print(f"{'Content Lines':<25} {current_stats['content_lines']:<15} {enhanced_stats['content_lines']:<15} {enhanced_stats['content_lines'] - current_stats['content_lines']:+d}")
    print(f"{'Character Count':<25} {current_stats['char_count']:<15} {enhanced_stats['char_count']:<15} {enhanced_stats['char_count'] - current_stats['char_count']:+d}")
    
    print()
    # Structure metrics
    print(f"{'Headers':<25} {current_stats['headers']:<15} {enhanced_stats['headers']:<15} {enhanced_stats['headers'] - current_stats['headers']:+d}")
    print(f"{'Links':<25} {current_stats['links']:<15} {enhanced_stats['links']:<15} {enhanced_stats['links'] - current_stats['links']:+d}")
    print(f"{'Lists':<25} {current_stats['lists']:<15} {enhanced_stats['lists']:<15} {enhanced_stats['lists'] - current_stats['lists']:+d}")
    
    print()
    # Noise metrics (lower is better)
    print(f"{'URL Artifacts':<25} {current_stats['url_artifacts']:<15} {enhanced_stats['url_artifacts']:<15} {enhanced_stats['url_artifacts'] - current_stats['url_artifacts']:+d}")
    print(f"{'Navigation Words':<25} {current_stats['nav_words']:<15} {enhanced_stats['nav_words']:<15} {enhanced_stats['nav_words'] - current_stats['nav_words']:+d}")
    
    print()
    # Quality metrics
    print(f"{'Content Density %':<25} {current_stats['content_density']*100:.1f}%{'':<10} {enhanced_stats['content_density']*100:.1f}%{'':<10} {(enhanced_stats['content_density'] - current_stats['content_density'])*100:+.1f}%")
    print(f"{'Noise Ratio %':<25} {current_stats['noise_ratio']*100:.1f}%{'':<10} {enhanced_stats['noise_ratio']*100:.1f}%{'':<10} {(enhanced_stats['noise_ratio'] - current_stats['noise_ratio'])*100:+.1f}%")
    print(f"{'Quality Score':<25} {current_stats['quality_score']:.1f}{'':<11} {enhanced_stats['quality_score']:.1f}{'':<11} {enhanced_stats['quality_score'] - current_stats['quality_score']:+.1f}")
    
    print("\n" + "="*80)
    
    # Interpretation
    improvement_pct = ((enhanced_stats['quality_score'] - current_stats['quality_score']) / current_stats['quality_score'] * 100) if current_stats['quality_score'] > 0 else 0
    noise_reduction_pct = ((current_stats['noise_ratio'] - enhanced_stats['noise_ratio']) / current_stats['noise_ratio'] * 100) if current_stats['noise_ratio'] > 0 else 0
    
    print("🎯 KEY IMPROVEMENTS:")
    print(f"   Quality Score: {improvement_pct:+.1f}% improvement")
    print(f"   Noise Reduction: {noise_reduction_pct:.1f}% less noise")
    print(f"   URL Artifacts: {current_stats['url_artifacts'] - enhanced_stats['url_artifacts']} fewer artifacts")
    print(f"   Navigation Noise: {current_stats['nav_words'] - enhanced_stats['nav_words']} fewer nav elements")


def save_markdown_samples(current_md: str, enhanced_md: str, url: str):
    """Save markdown samples for manual inspection."""
    timestamp = int(time.time())
    
    # Save current markdown
    current_file = Path(f"throwaway_tests/current_markdown_{timestamp}.md")
    with open(current_file, 'w', encoding='utf-8') as f:
        f.write(f"# Current Converter Output\n")
        f.write(f"URL: {url}\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(current_md)
    
    # Save enhanced markdown
    enhanced_file = Path(f"throwaway_tests/enhanced_markdown_{timestamp}.md")
    with open(enhanced_file, 'w', encoding='utf-8') as f:
        f.write(f"# Enhanced Converter Output\n")
        f.write(f"URL: {url}\n") 
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(enhanced_md)
    
    print(f"\n📁 Markdown samples saved:")
    print(f"   Current: {current_file}")
    print(f"   Enhanced: {enhanced_file}")


def main():
    """Main comparison test."""
    print("🚀 MARKDOWN QUALITY COMPARISON TEST")
    print("Testing: Current vs Enhanced HTML-to-Markdown Conversion")
    
    # Test URL (CTGS)
    test_url = "https://www.ctgs.com/"
    
    print(f"\n📥 Downloading content from: {test_url}")
    html_content, content_type, status_code = download_url_content(test_url)
    
    if status_code != 200 or not html_content:
        print(f"❌ Failed to download content (HTTP {status_code})")
        return
    
    print(f"✅ Downloaded {len(html_content)} characters of HTML")
    
    # Convert with current converter
    print("\n🔄 Converting with CURRENT converter...")
    start_time = time.time()
    current_markdown = convert_html_to_markdown(html_content, test_url)
    current_time = time.time() - start_time
    
    # Convert with enhanced converter  
    print("🔄 Converting with ENHANCED converter...")
    start_time = time.time()
    enhanced_markdown = convert_html_to_markdown_enhanced(html_content, test_url)
    enhanced_time = time.time() - start_time
    
    print(f"⏱️  Conversion times: Current {current_time:.3f}s, Enhanced {enhanced_time:.3f}s")
    
    # Analyze quality
    print("\n📊 Analyzing markdown quality...")
    current_stats = analyze_markdown_quality(current_markdown, "Current")
    enhanced_stats = analyze_markdown_quality(enhanced_markdown, "Enhanced")
    
    # Print comparison
    print_comparison(current_stats, enhanced_stats)
    
    # Save samples for inspection
    save_markdown_samples(current_markdown, enhanced_markdown, test_url)
    
    # Show first few lines of each for immediate comparison
    print("\n" + "="*80)
    print("📝 SAMPLE OUTPUT COMPARISON (First 500 chars)")
    print("="*80)
    
    print("🔵 CURRENT CONVERTER:")
    print("-" * 40)
    print(current_markdown[:500] + "..." if len(current_markdown) > 500 else current_markdown)
    
    print("\n🟢 ENHANCED CONVERTER:")
    print("-" * 40)
    print(enhanced_markdown[:500] + "..." if len(enhanced_markdown) > 500 else enhanced_markdown)
    
    print("\n✅ Test completed! Check the saved markdown files for full comparison.")


if __name__ == "__main__":
    main()