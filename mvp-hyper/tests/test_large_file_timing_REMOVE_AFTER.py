#!/usr/bin/env python3
"""
Timing analysis for large files to understand classification bottlenecks.
DELETE THIS FILE AFTER TESTING.
"""

import sys
import os
import time
from pathlib import Path

# Add the core directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from enhanced_classification_with_entities import EnhancedClassifierWithEntities

def test_large_file_timing():
    """Test classification timing on specific large files."""
    
    # Target large files to test
    large_files = [
        "2206.01062.pages.md",      # 11M
        "multi_page.pages.md",      # 771K  
        "right_to_left_02.pages.md", # 576K
        "ipg07997973.md",           # 467K
        "elife-56337.nxml.md",      # 334K
        "2206.01062.md"             # 372K
    ]
    
    output_dir = Path(__file__).parent.parent / 'output'
    
    # Initialize classifier
    print("🔧 Initializing Enhanced Classifier...")
    classifier = EnhancedClassifierWithEntities()
    
    print("\n📊 LARGE FILE CLASSIFICATION TIMING ANALYSIS")
    print("=" * 60)
    
    results = []
    
    for filename in large_files:
        file_path = output_dir / filename
        
        if not file_path.exists():
            print(f"❌ {filename} - File not found")
            continue
            
        # Get file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        print(f"\n🔍 Testing: {filename} ({file_size_mb:.1f}MB)")
        
        try:
            # Read file
            read_start = time.time()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            read_time = time.time() - read_start
            
            # Get content stats
            char_count = len(content)
            line_count = content.count('\n')
            
            print(f"   📖 Read: {read_time*1000:.1f}ms ({char_count:,} chars, {line_count:,} lines)")
            
            # Test classification
            classify_start = time.time()
            result = classifier.classify_and_extract(content, filename)
            classify_time = time.time() - classify_start
            
            print(f"   🧠 Classification: {classify_time*1000:.1f}ms")
            print(f"   ⚡ Speed: {char_count/classify_time/1000:.1f}K chars/sec")
            
            # Check if content looks like dense XML/HTML
            xml_tags = content.count('<') + content.count('>')
            xml_density = xml_tags / len(content) if content else 0
            print(f"   📄 XML tag density: {xml_density:.3f} (tags/char)")
            
            results.append({
                'filename': filename,
                'size_mb': file_size_mb,
                'char_count': char_count,
                'line_count': line_count,
                'read_time_ms': read_time * 1000,
                'classify_time_ms': classify_time * 1000,
                'chars_per_sec': char_count / classify_time,
                'xml_density': xml_density
            })
            
            # Show entity extraction results
            if result and 'universal_entities' in result:
                entities = result['universal_entities']
                entity_count = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
                print(f"   🔍 Entities found: {entity_count}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if results:
        # Sort by processing time
        results.sort(key=lambda x: x['classify_time_ms'], reverse=True)
        
        print(f"{'File':<30} {'Size(MB)':<8} {'Time(ms)':<8} {'Speed(K/s)':<10} {'XML':<6}")
        print("-" * 68)
        
        for r in results:
            print(f"{r['filename']:<30} {r['size_mb']:<8.1f} {r['classify_time_ms']:<8.0f} "
                  f"{r['chars_per_sec']/1000:<10.0f} {r['xml_density']:<6.3f}")
        
        # Find correlation patterns
        avg_xml_density = sum(r['xml_density'] for r in results) / len(results)
        print(f"\n🔍 Average XML density: {avg_xml_density:.3f}")
        
        slowest = results[0]
        fastest = results[-1]
        print(f"🐌 Slowest: {slowest['filename']} ({slowest['classify_time_ms']:.0f}ms)")
        print(f"⚡ Fastest: {fastest['filename']} ({fastest['classify_time_ms']:.0f}ms)")
        
        # Check if XML density correlates with slow processing
        high_xml_files = [r for r in results if r['xml_density'] > avg_xml_density]
        if high_xml_files:
            avg_time_high_xml = sum(r['classify_time_ms'] for r in high_xml_files) / len(high_xml_files)
            low_xml_files = [r for r in results if r['xml_density'] <= avg_xml_density]
            if low_xml_files:
                avg_time_low_xml = sum(r['classify_time_ms'] for r in low_xml_files) / len(low_xml_files)
                print(f"📊 High XML density files avg time: {avg_time_high_xml:.0f}ms")
                print(f"📊 Low XML density files avg time: {avg_time_low_xml:.0f}ms")

if __name__ == "__main__":
    test_large_file_timing()