#!/usr/bin/env python3
"""
Markdown Conversion Performance Benchmark - THROWAWAY TEST
==========================================================

GOAL: Compare performance of multiple HTML-to-Markdown converters
REASON: Find the fastest method that maintains quality
PROBLEM: Need data-driven decision on conversion approach

Testing: BeautifulSoup vs html2text vs markdownify
"""

import time
import requests
from pathlib import Path
import sys

# Add mvp-fusion to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our converters
from utils.html_to_markdown_converter import HTMLToMarkdownConverter
from throwaway_tests.enhanced_html_converter import EnhancedHTMLToMarkdownConverter

# Import third-party converters
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    print("⚠️  html2text not installed. Run: pip install html2text")

try:
    from markdownify import markdownify
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False
    print("⚠️  markdownify not installed. Run: pip install markdownify")


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


def test_current_converter(html_content: str, url: str) -> tuple[str, float]:
    """Test our current BeautifulSoup converter."""
    converter = HTMLToMarkdownConverter()
    
    # Warm up
    _ = converter.convert(html_content[:100], url)
    
    # Measure (average of 5 runs)
    times = []
    for _ in range(5):
        start_time = time.perf_counter()
        markdown = converter.convert(html_content, url)
        times.append(time.perf_counter() - start_time)
    
    avg_time = sum(times) / len(times)
    return markdown, avg_time


def test_enhanced_converter(html_content: str, url: str) -> tuple[str, float]:
    """Test our enhanced BeautifulSoup converter."""
    converter = EnhancedHTMLToMarkdownConverter()
    
    # Warm up
    _ = converter.convert(html_content[:100], url)
    
    # Measure (average of 5 runs)
    times = []
    for _ in range(5):
        start_time = time.perf_counter()
        markdown = converter.convert(html_content, url)
        times.append(time.perf_counter() - start_time)
    
    avg_time = sum(times) / len(times)
    return markdown, avg_time


def test_html2text(html_content: str, url: str) -> tuple[str, float]:
    """Test html2text converter."""
    if not HAS_HTML2TEXT:
        return "", 0
    
    h = html2text.HTML2Text()
    h.base_url = url
    h.body_width = 0  # Don't wrap text
    h.ignore_emphasis = False
    h.ignore_links = False
    h.ignore_images = True  # Ignore for cleaner text
    
    # Warm up
    _ = h.handle(html_content[:100])
    
    # Measure (average of 5 runs)
    times = []
    for _ in range(5):
        start_time = time.perf_counter()
        markdown = h.handle(html_content)
        times.append(time.perf_counter() - start_time)
    
    avg_time = sum(times) / len(times)
    return markdown, avg_time


def test_markdownify(html_content: str, url: str) -> tuple[str, float]:
    """Test markdownify converter."""
    if not HAS_MARKDOWNIFY:
        return "", 0
    
    # Warm up
    _ = markdownify(html_content[:100])
    
    # Measure (average of 5 runs)
    times = []
    for _ in range(5):
        start_time = time.perf_counter()
        markdown = markdownify(html_content, 
                              heading_style='ATX',  # Use # style headings
                              bullets='*',  # Use * for lists
                              escape_asterisks=True,
                              escape_underscores=True)
        times.append(time.perf_counter() - start_time)
    
    avg_time = sum(times) / len(times)
    return markdown, avg_time


def analyze_quality(markdown: str) -> dict:
    """Analyze markdown quality metrics."""
    return {
        'size': len(markdown),
        'lines': len(markdown.splitlines()),
        'urls': markdown.count('http'),
        'encoded_params': markdown.count('%3'),
        'elementor': markdown.count('elementor'),
        'cookie_refs': markdown.count('cookie') + markdown.count('Cookie'),
        'gtag_refs': markdown.count('gtag'),
        'empty_lines': sum(1 for line in markdown.splitlines() if not line.strip())
    }


def main():
    """Main benchmark."""
    test_url = "https://www.ctgs.com/"
    
    print("=" * 80)
    print("⚡ MARKDOWN CONVERSION PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"Test URL: {test_url}")
    print(f"Testing: BeautifulSoup (current & enhanced) vs html2text vs markdownify")
    print()
    
    # Download URL
    print("📥 Downloading URL...")
    html_content, download_time = download_url(test_url)
    print(f"   Downloaded: {len(html_content)} bytes in {download_time:.3f}s")
    print()
    
    # Test all converters
    results = []
    
    # 1. Current (BeautifulSoup)
    print("🔵 Testing Current Converter (BeautifulSoup)...")
    current_md, current_time = test_current_converter(html_content, test_url)
    current_quality = analyze_quality(current_md)
    results.append(('Current (BS4)', current_time, current_quality, current_md))
    
    # 2. Enhanced (BeautifulSoup with cleaning)
    print("🟢 Testing Enhanced Converter (BeautifulSoup + Cleaning)...")
    enhanced_md, enhanced_time = test_enhanced_converter(html_content, test_url)
    enhanced_quality = analyze_quality(enhanced_md)
    results.append(('Enhanced (BS4+)', enhanced_time, enhanced_quality, enhanced_md))
    
    # 3. html2text
    if HAS_HTML2TEXT:
        print("🟡 Testing html2text...")
        html2text_md, html2text_time = test_html2text(html_content, test_url)
        html2text_quality = analyze_quality(html2text_md)
        results.append(('html2text', html2text_time, html2text_quality, html2text_md))
    
    # 4. markdownify
    if HAS_MARKDOWNIFY:
        print("🟣 Testing markdownify...")
        markdownify_md, markdownify_time = test_markdownify(html_content, test_url)
        markdownify_quality = analyze_quality(markdownify_md)
        results.append(('markdownify', markdownify_time, markdownify_quality, markdownify_md))
    
    print()
    print("=" * 80)
    print("📊 PERFORMANCE RESULTS (sorted by speed)")
    print("=" * 80)
    
    # Sort by speed
    results.sort(key=lambda x: x[1])
    
    # Use fastest as baseline
    baseline_time = results[0][1]
    
    print(f"{'Converter':<20} {'Time (ms)':<12} {'Slowdown':<10} {'Size':<8} {'Lines':<8} {'Noise':<8}")
    print("-" * 80)
    
    for name, conv_time, quality, _ in results:
        slowdown = conv_time / baseline_time if baseline_time > 0 else 1
        noise = quality['encoded_params'] + quality['elementor'] + quality['cookie_refs'] + quality['gtag_refs']
        print(f"{name:<20} {conv_time*1000:>8.1f}ms  {slowdown:>6.1f}x     "
              f"{quality['size']:>6}  {quality['lines']:>6}  {noise:>6}")
    
    print()
    print("=" * 80)
    print("📈 QUALITY METRICS")
    print("=" * 80)
    
    print(f"{'Converter':<20} {'URLs':<8} {'Encoded':<10} {'Elementor':<10} {'Cookies':<10}")
    print("-" * 80)
    
    for name, _, quality, _ in results:
        print(f"{name:<20} {quality['urls']:>6}  {quality['encoded_params']:>8}  "
              f"{quality['elementor']:>9}  {quality['cookie_refs']:>9}")
    
    # Save samples
    print()
    print("💾 Saving markdown samples...")
    timestamp = int(time.time())
    
    for name, _, _, markdown in results:
        safe_name = name.replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus')
        filename = Path(f"throwaway_tests/benchmark_{safe_name}_{timestamp}.md")
        with open(filename, 'w') as f:
            f.write(f"# Benchmark: {name}\n")
            f.write(f"# Timestamp: {timestamp}\n\n")
            f.write(markdown)
        print(f"   {name}: {filename}")
    
    # Final recommendation
    print()
    print("=" * 80)
    print("🎯 RECOMMENDATION")
    print("=" * 80)
    
    # Find best balance of speed and quality
    best_speed = min(results, key=lambda x: x[1])
    best_quality = min(results, key=lambda x: x[2]['encoded_params'] + x[2]['elementor'])
    
    print(f"⚡ Fastest: {best_speed[0]} at {best_speed[1]*1000:.1f}ms")
    print(f"✨ Cleanest: {best_quality[0]} with {best_quality[2]['encoded_params']} encoded params")
    
    # Calculate quality/speed ratio
    for name, conv_time, quality, _ in results:
        noise = quality['encoded_params'] + quality['elementor'] + quality['cookie_refs']
        if noise == 0:
            noise = 0.1  # Avoid division by zero
        quality_score = 100 / (noise * conv_time * 1000)  # Higher is better
        print(f"📊 {name}: Quality/Speed Score = {quality_score:.2f}")


if __name__ == "__main__":
    main()