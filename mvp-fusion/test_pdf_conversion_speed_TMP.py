#!/usr/bin/env python3
"""
GOAL: Test pure PDF-to-markdown conversion speed in isolation
REASON: Document processing dropped from 500+ pages/sec to 120 pages/sec
PROBLEM: Need to identify what's causing the PDF conversion slowdown
"""

import time
import fitz
from pathlib import Path

def test_pdf_conversion_speed():
    """Test PDF conversion performance in isolation"""
    data_dir = Path.home() / 'projects/docling/cli/data_complex/complex_pdfs'
    pdf_files = list(data_dir.glob('*.pdf'))
    
    print("🔍 ISOLATED PDF CONVERSION SPEED TEST")
    print("=" * 50)
    
    total_pages = 0
    total_time = 0
    
    for pdf_file in pdf_files:
        if not pdf_file.name.endswith('.pdf'):
            continue
            
        print(f"\n📄 Testing: {pdf_file.name}")
        
        # Test 1: Just opening and getting page count
        start_time = time.perf_counter()
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        open_time = time.perf_counter() - start_time
        
        # Test 2: Full text extraction (current method)
        start_time = time.perf_counter()
        markdown_content = [f"# {pdf_file.stem}\n"]
        
        for page_num in range(page_count):
            page = doc[page_num]
            
            # Use blocks method for fastest extraction
            blocks = page.get_text("blocks")
            if blocks:
                markdown_content.append(f"\n## Page {page_num + 1}\n")
                for block in blocks:
                    if block[4]:  # Check if block contains text
                        text = block[4].strip()
                        if text:
                            markdown_content.append(text + "\n")
        
        full_content = '\n'.join(markdown_content)
        extraction_time = time.perf_counter() - start_time
        doc.close()
        
        # Test 3: Alternative faster extraction methods
        start_time = time.perf_counter()
        doc = fitz.open(str(pdf_file))
        fast_content = []
        for page_num in range(page_count):
            page = doc[page_num]
            # Try get_text() without blocks (might be faster)
            text = page.get_text()
            if text.strip():
                fast_content.append(f"Page {page_num + 1}:\n{text}\n")
        fast_result = '\n'.join(fast_content)
        fast_time = time.perf_counter() - start_time
        doc.close()
        
        # Results
        file_size_mb = pdf_file.stat().st_size / (1024*1024)
        print(f"   📊 Pages: {page_count}, Size: {file_size_mb:.1f}MB")
        print(f"   ⏱️  Open time: {open_time*1000:.1f}ms")
        print(f"   ⏱️  Block extraction: {extraction_time*1000:.1f}ms ({page_count/extraction_time:.0f} pages/sec)")
        print(f"   ⏱️  Simple extraction: {fast_time*1000:.1f}ms ({page_count/fast_time:.0f} pages/sec)")
        print(f"   📏 Content size: Block={len(full_content)} chars, Simple={len(fast_result)} chars")
        
        total_pages += page_count
        total_time += extraction_time
    
    print(f"\n🚀 OVERALL RESULTS:")
    print(f"   Total pages: {total_pages}")
    print(f"   Total time: {total_time*1000:.1f}ms")
    print(f"   Speed: {total_pages/total_time:.0f} pages/sec")
    print(f"   Target: 500+ pages/sec")
    
    if total_pages/total_time < 400:
        print(f"🔴 PERFORMANCE ISSUE: {total_pages/total_time:.0f} pages/sec is well below target of 500+")
    else:
        print(f"🟢 PERFORMANCE OK: {total_pages/total_time:.0f} pages/sec meets target")

if __name__ == "__main__":
    test_pdf_conversion_speed()