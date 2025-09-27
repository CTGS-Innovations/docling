#!/usr/bin/env python3
"""
URL to Markdown Performance Test - THROWAWAY TEST
=================================================

GOAL: Measure performance of URL → Markdown conversion
REASON: Determine if BeautifulSoup improvements justify performance cost
PROBLEM: Need data-driven decision on conversion approach

Simple test: Download URL, convert to markdown, measure time.
"""

import time
import requests
from pathlib import Path
import sys

# Add mvp-fusion to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import current converter
from utils.html_to_markdown_converter import HTMLToMarkdownConverter

# Import enhanced converter from our test
from throwaway_tests.enhanced_html_converter import EnhancedHTMLToMarkdownConverter


def download_url(url: str) -> tuple[str, float]:
    """Download URL and return HTML content with timing."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    start_time = time.perf_counter()
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    download_time = time.perf_counter() - start_time
    
    return response.text, download_time


def measure_conversion(html_content: str, url: str, converter_class, name: str) -> tuple[str, float]:
    """Measure conversion time and return markdown."""
    converter = converter_class()
    
    # Warm up (first run can be slower)
    _ = converter.convert(html_content[:100], url)
    
    # Actual measurement (average of 3 runs)
    times = []
    markdown = None
    
    for _ in range(3):
        start_time = time.perf_counter()
        markdown = converter.convert(html_content, url)
        conversion_time = time.perf_counter() - start_time
        times.append(conversion_time)
    
    avg_time = sum(times) / len(times)
    return markdown, avg_time


def main():
    """Main performance test."""
    test_url = "https://www.ctgs.com/"
    
    print("=" * 80)
    print("⚡ URL TO MARKDOWN PERFORMANCE TEST")
    print("=" * 80)
    print(f"Test URL: {test_url}")
    print()
    
    # Step 1: Download URL
    print("📥 Downloading URL...")
    html_content, download_time = download_url(test_url)
    print(f"   Downloaded: {len(html_content)} bytes in {download_time:.3f}s")
    print()
    
    # Step 2: Test CURRENT converter
    print("🔵 CURRENT CONVERTER (Simple/Fast)")
    print("-" * 40)
    current_markdown, current_time = measure_conversion(
        html_content, test_url, HTMLToMarkdownConverter, "Current"
    )
    print(f"   Conversion time: {current_time:.3f}s (avg of 3 runs)")
    print(f"   Output size: {len(current_markdown)} chars")
    print(f"   Lines: {len(current_markdown.splitlines())}")
    
    # Count some quality metrics
    current_urls = current_markdown.count('http')
    current_encoded = current_markdown.count('%3')
    current_elementor = current_markdown.count('elementor')
    print(f"   URLs: {current_urls}, Encoded params: {current_encoded}, Elementor refs: {current_elementor}")
    print()
    
    # Step 3: Test ENHANCED converter
    print("🟢 ENHANCED CONVERTER (BeautifulSoup/Thorough)")
    print("-" * 40)
    enhanced_markdown, enhanced_time = measure_conversion(
        html_content, test_url, EnhancedHTMLToMarkdownConverter, "Enhanced"
    )
    print(f"   Conversion time: {enhanced_time:.3f}s (avg of 3 runs)")
    print(f"   Output size: {len(enhanced_markdown)} chars")
    print(f"   Lines: {len(enhanced_markdown.splitlines())}")
    
    # Count quality metrics
    enhanced_urls = enhanced_markdown.count('http')
    enhanced_encoded = enhanced_markdown.count('%3')
    enhanced_elementor = enhanced_markdown.count('elementor')
    print(f"   URLs: {enhanced_urls}, Encoded params: {enhanced_encoded}, Elementor refs: {enhanced_elementor}")
    print()
    
    # Step 4: Performance Comparison
    print("=" * 80)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 80)
    
    slowdown = enhanced_time / current_time
    print(f"⏱️  Conversion Speed:")
    print(f"   Current:  {current_time:.3f}s")
    print(f"   Enhanced: {enhanced_time:.3f}s")
    print(f"   Slowdown: {slowdown:.1f}x slower")
    print()
    
    print(f"📈 Output Quality:")
    print(f"   Size reduction: {len(current_markdown) - len(enhanced_markdown)} chars removed")
    print(f"   Line reduction: {len(current_markdown.splitlines()) - len(enhanced_markdown.splitlines())} lines removed")
    print(f"   URL artifacts removed: {current_encoded - enhanced_encoded}")
    print(f"   Tracking params removed: {current_elementor - enhanced_elementor}")
    print()
    
    # Step 5: Show sample output
    print("📝 SAMPLE OUTPUT (First 500 chars)")
    print("=" * 80)
    
    print("CURRENT:")
    print("-" * 40)
    print(current_markdown[:500])
    print()
    
    print("ENHANCED:")
    print("-" * 40)
    print(enhanced_markdown[:500])
    print()
    
    # Step 6: Save full outputs for inspection
    timestamp = int(time.time())
    
    current_file = Path(f"throwaway_tests/perf_current_{timestamp}.md")
    with open(current_file, 'w') as f:
        f.write(f"# Performance Test - Current Converter\n")
        f.write(f"# Conversion time: {current_time:.3f}s\n\n")
        f.write(current_markdown)
    
    enhanced_file = Path(f"throwaway_tests/perf_enhanced_{timestamp}.md")
    with open(enhanced_file, 'w') as f:
        f.write(f"# Performance Test - Enhanced Converter\n")
        f.write(f"# Conversion time: {enhanced_time:.3f}s\n\n")
        f.write(enhanced_markdown)
    
    print("💾 Full markdown saved:")
    print(f"   Current:  {current_file}")
    print(f"   Enhanced: {enhanced_file}")
    print()
    
    # Final verdict
    print("=" * 80)
    print("🎯 VERDICT")
    print("=" * 80)
    
    if slowdown > 5:
        print(f"❌ Enhanced converter is {slowdown:.1f}x slower - performance cost too high")
    elif slowdown > 2:
        print(f"⚠️  Enhanced converter is {slowdown:.1f}x slower - moderate performance impact")
    else:
        print(f"✅ Enhanced converter is only {slowdown:.1f}x slower - acceptable performance")
    
    if current_encoded - enhanced_encoded > 0:
        print(f"✅ Quality improvement: {current_encoded - enhanced_encoded} URL artifacts removed")
    else:
        print(f"❌ No quality improvement in URL artifact removal")


if __name__ == "__main__":
    main()