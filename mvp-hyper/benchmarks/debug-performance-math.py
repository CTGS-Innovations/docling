#!/usr/bin/env python3
"""
Debug Performance Math
Check if our pages/sec calculations are correct

Let me trace through the math step by step to see what's wrong
"""

import glob
import os


def debug_performance_calculations():
    """Debug the performance math from our test results"""
    
    print("🔍 DEBUGGING PERFORMANCE CALCULATIONS")
    print("=" * 60)
    
    # Let's check our test documents first
    docs_dir = "../output/pipeline/3-enriched"
    doc_pattern = os.path.join(docs_dir, "*.md")
    doc_files = sorted(glob.glob(doc_pattern))[:7]  # Same as our test
    
    total_chars = 0
    print("📄 TEST DOCUMENTS:")
    for i, file_path in enumerate(doc_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Our test limits to 20,000 chars per document
                if len(content) > 20000:
                    content = content[:20000]
                
                char_count = len(content)
                total_chars += char_count
                
                filename = os.path.basename(file_path)
                print(f"  {i}. {filename[:50]}... : {char_count:,} chars")
        except Exception as e:
            print(f"  {i}. Error: {e}")
    
    print(f"\nTotal characters across all documents: {total_chars:,}")
    print(f"Average characters per document: {total_chars / len(doc_files):,.0f}")
    print()
    
    # Now let's check the math from our test results
    print("🧮 CHECKING SPACY BASELINE MATH:")
    print("-" * 40)
    
    # From the test output:
    spacy_avg_time = 1.972  # seconds
    spacy_chars_per_sec = 71009
    spacy_pages_per_sec = 23.7
    
    # The test runs 3 iterations, so total chars processed is:
    total_chars_processed = total_chars * 3
    
    print(f"Test setup:")
    print(f"  Documents: {len(doc_files)}")
    print(f"  Iterations: 3")
    print(f"  Total chars per iteration: {total_chars:,}")
    print(f"  Total chars processed (3 iterations): {total_chars_processed:,}")
    print(f"  Average processing time: {spacy_avg_time}s")
    print()
    
    # Let's recalculate
    print("Manual calculations:")
    
    # Chars per second should be: total_chars_per_iteration / avg_time
    manual_chars_per_sec = total_chars / spacy_avg_time
    print(f"  Manual chars/sec: {total_chars:,} ÷ {spacy_avg_time} = {manual_chars_per_sec:,.0f}")
    
    # Pages per second (assuming 3000 chars per page)
    manual_pages_per_sec = manual_chars_per_sec / 3000
    print(f"  Manual pages/sec: {manual_chars_per_sec:,.0f} ÷ 3000 = {manual_pages_per_sec:.1f}")
    
    print()
    print("Test reported:")
    print(f"  Chars/sec: {spacy_chars_per_sec:,}")
    print(f"  Pages/sec: {spacy_pages_per_sec}")
    
    print()
    print("❗ ISSUE FOUND:")
    if abs(manual_chars_per_sec - spacy_chars_per_sec) > 1000:
        print(f"  The test is calculating chars/sec incorrectly!")
        print(f"  Difference: {abs(manual_chars_per_sec - spacy_chars_per_sec):,.0f} chars/sec")
    
    # Check other models
    print("\n🧮 CHECKING OTHER MODELS:")
    print("-" * 40)
    
    models = [
        ("Stanza", 3.372, 41518, 13.8),
        ("Flair", 3.677, 38071, 12.7),
        ("HuggingFace", 0.906, 154521, 51.5)
    ]
    
    for model_name, avg_time, reported_chars_sec, reported_pages_sec in models:
        manual_chars_sec = total_chars / avg_time
        manual_pages_sec = manual_chars_sec / 3000
        
        print(f"\n{model_name}:")
        print(f"  Manual calculation: {manual_chars_sec:,.0f} chars/sec, {manual_pages_sec:.1f} pages/sec")
        print(f"  Test reported: {reported_chars_sec:,} chars/sec, {reported_pages_sec} pages/sec")
        
        if abs(manual_chars_sec - reported_chars_sec) > 1000:
            print(f"  ❌ ERROR: Difference of {abs(manual_chars_sec - reported_chars_sec):,.0f} chars/sec")
        else:
            print(f"  ✅ Math checks out")
    
    print("\n" + "=" * 60)
    print("🎯 CORRECTED PERFORMANCE ESTIMATES:")
    print("=" * 60)
    
    print("Realistic pages/sec (based on corrected math):")
    for model_name, avg_time, _, _ in [("spaCy", spacy_avg_time)] + [(m[0], m[1], 0, 0) for m in models]:
        correct_chars_sec = total_chars / avg_time
        correct_pages_sec = correct_chars_sec / 3000
        
        if correct_pages_sec >= 1000:
            status = "✅ MEETS TARGET"
        elif correct_pages_sec >= 100:
            status = "⚠️ TOO SLOW"
        else:
            status = "❌ WAY TOO SLOW"
        
        print(f"  {model_name:<15}: {correct_pages_sec:6.1f} pages/sec {status}")
    
    print(f"\nTarget: 1000+ pages/sec")
    print(f"Best performer: HuggingFace BERT at ~{total_chars / 0.906 / 3000:.1f} pages/sec")
    print(f"Still {1000 / (total_chars / 0.906 / 3000):.0f}x too slow for our target!")


if __name__ == "__main__":
    debug_performance_calculations()