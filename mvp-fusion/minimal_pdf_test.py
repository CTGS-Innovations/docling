#!/usr/bin/env python3
"""
Minimal PDF test to isolate performance bottlenecks.
"""

import time
import sys
from pathlib import Path

try:
    import fitz
    print("✅ PyMuPDF available")
except ImportError:
    print("❌ PyMuPDF not available")
    sys.exit(1)

def test_minimal_extraction():
    """Test raw PDF extraction without any framework overhead."""
    
    # Get one test file
    test_dirs = [Path("../cli/data"), Path("../cli/data_complex"), Path("../cli/data_osha")]
    
    test_file = None
    for test_dir in test_dirs:
        if test_dir.exists():
            pdfs = list(test_dir.glob("*.pdf"))
            if pdfs:
                test_file = pdfs[0]
                break
    
    if not test_file:
        print("❌ No PDF files found")
        return
    
    print(f"🧪 Testing: {test_file.name}")
    
    # Test 1: Raw PyMuPDF extraction (MVP-Hyper style)
    print("\n⚡ RAW PYMUPDF EXTRACTION")
    
    for run in range(3):
        start_time = time.perf_counter()
        
        doc = fitz.open(str(test_file))
        page_count = len(doc)
        
        texts = []
        for page in doc:  # Iterator pattern
            text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            texts.append(text or "")
        
        content = '\n'.join(texts)
        doc.close()
        
        extraction_time = time.perf_counter() - start_time
        pages_per_sec = page_count / extraction_time if extraction_time > 0 else 0
        
        print(f"  Run {run+1}: {pages_per_sec:.1f} pages/sec ({extraction_time:.3f}s, {page_count} pages)")
        print(f"    Content length: {len(content)} chars")
    
    # Test 2: Alternative extraction methods
    print("\n🔄 ALTERNATIVE METHODS")
    
    # Method A: No flags
    start_time = time.perf_counter()
    doc = fitz.open(str(test_file))
    texts = []
    for page in doc:
        text = page.get_text()  # No flags
        texts.append(text or "")
    content_no_flags = '\n'.join(texts)
    doc.close()
    extraction_time = time.perf_counter() - start_time
    pages_per_sec = page_count / extraction_time
    print(f"  No flags: {pages_per_sec:.1f} pages/sec")
    
    # Method B: Dict mode
    start_time = time.perf_counter()
    doc = fitz.open(str(test_file))
    texts = []
    for page in doc:
        text = page.get_text("text")  # Simple text mode
        texts.append(text or "")
    content_text = '\n'.join(texts)
    doc.close()
    extraction_time = time.perf_counter() - start_time
    pages_per_sec = page_count / extraction_time
    print(f"  Text mode: {pages_per_sec:.1f} pages/sec")
    
    print(f"\n📊 Results:")
    print(f"   File: {test_file.name}")
    print(f"   Pages: {page_count}")
    print(f"   Content lengths: {len(content)}, {len(content_no_flags)}, {len(content_text)}")

if __name__ == "__main__":
    test_minimal_extraction()