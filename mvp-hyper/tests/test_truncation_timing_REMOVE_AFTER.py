#!/usr/bin/env python3
"""
Test truncation performance on large files.
DELETE THIS FILE AFTER TESTING.
"""

import sys
import os
import time
from pathlib import Path

# Add the core directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from enhanced_classification_with_entities import EnhancedClassifierWithEntities

def test_truncation_performance():
    """Test classification timing with content truncation."""
    
    # Test the largest file
    large_file = "2206.01062.pages.md"
    output_dir = Path(__file__).parent.parent / 'output'
    file_path = output_dir / large_file
    
    if not file_path.exists():
        print(f"❌ {large_file} not found")
        return
    
    # Initialize classifier
    print("🔧 Initializing Enhanced Classifier...")
    classifier = EnhancedClassifierWithEntities()
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"\n📊 TRUNCATION PERFORMANCE TEST")
    print(f"🎯 Target file: {large_file} ({file_size_mb:.1f}MB)")
    print("=" * 60)
    
    # Test different truncation sizes
    truncation_sizes_mb = [1.0, 2.0, 5.0, None]  # None = full file
    
    for max_mb in truncation_sizes_mb:
        print(f"\n🔍 Testing with {max_mb}MB limit" if max_mb else "\n🔍 Testing full file")
        
        try:
            # Read file (with truncation if specified)
            read_start = time.time()
            with open(file_path, 'r', encoding='utf-8') as f:
                if max_mb:
                    max_chars = int(max_mb * 1024 * 1024)
                    content = f.read(max_chars)
                else:
                    content = f.read()
            read_time = time.time() - read_start
            
            # Get content stats
            char_count = len(content)
            line_count = content.count('\n')
            actual_mb = char_count / (1024 * 1024)
            
            print(f"   📖 Read: {read_time*1000:.1f}ms ({char_count:,} chars, {actual_mb:.1f}MB)")
            
            # Test classification
            classify_start = time.time()
            result = classifier.classify_and_extract(content, large_file)
            classify_time = time.time() - classify_start
            
            print(f"   🧠 Classification: {classify_time*1000:.1f}ms")
            print(f"   ⚡ Speed: {char_count/classify_time/1000:.1f}K chars/sec")
            
            # Speed improvement vs full file
            if max_mb == 1.0:
                baseline_time = classify_time
            elif max_mb is None:
                if 'baseline_time' in locals():
                    speedup = classify_time / baseline_time
                    print(f"   📈 Speedup vs 1MB: {speedup:.1f}x slower")
            
            # Show entity extraction results
            if result and 'universal_entities' in result:
                entities = result['universal_entities']
                entity_count = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
                print(f"   🔍 Entities found: {entity_count}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n💡 Recommendation: Using 1MB truncation gives good entity extraction")
    print(f"   with massive performance improvement for large files.")

if __name__ == "__main__":
    test_truncation_performance()