#!/usr/bin/env python3
"""
PDF Diagnostic Tool
==================
Analyze why certain PDFs are slow to process.
"""

import fitz
import time
from pathlib import Path
import os

def diagnose_pdf(pdf_path):
    """Analyze a PDF to understand why it might be slow."""
    
    print(f"\n🔍 DIAGNOSING: {pdf_path.name}")
    print("-" * 50)
    
    # Basic file info
    file_size = pdf_path.stat().st_size
    print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    
    try:
        # Time the PDF opening
        start_time = time.perf_counter()
        doc = fitz.open(str(pdf_path))
        open_time = time.perf_counter() - start_time
        
        print(f"Open time: {open_time:.3f}s")
        print(f"Page count: {len(doc)} pages")
        print(f"File size per page: {file_size / len(doc) / 1024:.1f} KB/page")
        
        # Check first few pages for complexity
        complex_pages = 0
        image_count = 0
        text_length = 0
        
        sample_pages = min(5, len(doc))  # Check first 5 pages
        
        for i in range(sample_pages):
            page = doc[i]
            
            # Count images
            images = page.get_images()
            image_count += len(images)
            
            # Get text length
            text = page.get_text()
            text_length += len(text)
            
            # Check for complexity (drawings, forms, etc.)
            drawings = page.get_drawings()
            if len(drawings) > 10 or len(images) > 3:
                complex_pages += 1
        
        print(f"Images in first {sample_pages} pages: {image_count}")
        print(f"Text length in first {sample_pages} pages: {text_length:,} chars")
        print(f"Complex pages (many drawings/images): {complex_pages}/{sample_pages}")
        
        # Test extraction speed on first page
        if len(doc) > 0:
            page = doc[0]
            
            # Test different extraction methods
            methods = [
                ("get_text()", lambda p: p.get_text()),
                ("get_text('text')", lambda p: p.get_text("text")),
                ("get_text('blocks')", lambda p: p.get_text("blocks")),
            ]
            
            print(f"\nExtraction method speeds (page 1):")
            for method_name, method_func in methods:
                try:
                    start = time.perf_counter()
                    result = method_func(page)
                    duration = time.perf_counter() - start
                    result_len = len(str(result))
                    print(f"  {method_name}: {duration:.3f}s ({result_len:,} chars)")
                except Exception as e:
                    print(f"  {method_name}: FAILED ({str(e)[:50]})")
        
        # Estimate total processing time
        if sample_pages > 0:
            avg_time_per_page = open_time / sample_pages
            estimated_total = avg_time_per_page * len(doc)
            print(f"\nEstimated total processing time: {estimated_total:.2f}s")
            
            if estimated_total > 5.0:
                print(f"❌ SLOW FILE CONFIRMED - Likely causes:")
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    print(f"  • Large file size ({file_size / 1024 / 1024:.1f}MB)")
                if len(doc) > 50:
                    print(f"  • Many pages ({len(doc)} pages)")
                if image_count / sample_pages > 2:
                    print(f"  • Many images ({image_count / sample_pages:.1f} per page)")
                if complex_pages / sample_pages > 0.5:
                    print(f"  • Complex layouts ({complex_pages}/{sample_pages} complex pages)")
                if text_length / sample_pages > 10000:
                    print(f"  • Very text-heavy ({text_length / sample_pages:,.0f} chars per page)")
            else:
                print(f"✅ Should be reasonably fast")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def main():
    """Diagnose the slow PDFs."""
    
    # Known slow PDFs from your output
    slow_pdfs = [
        "~/projects/docling/cli/data_osha/training-requirements-by-standard.pdf",
        "~/projects/docling/cli/data_osha/2254-training-requirements-in-osha-standards.pdf", 
        "~/projects/docling/cli/data_osha/2268-shipyard-industry-standards.pdf",
        "~/projects/docling/cli/data_osha/3902-silica-small-entity-compliance-guide-for-the-respirable-crystalline-silica-standard-in-construction-english.pdf"
    ]
    
    print("PDF DIAGNOSTIC TOOL")
    print("==================")
    
    for pdf_path_str in slow_pdfs:
        pdf_path = Path(os.path.expanduser(pdf_path_str))
        if pdf_path.exists():
            diagnose_pdf(pdf_path)
        else:
            print(f"\n❌ File not found: {pdf_path}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"  • Files >50 pages: Consider page-limit or skip")
    print(f"  • Files >10MB: Consider size-limit or skip") 
    print(f"  • Files with many images: Use simpler text extraction")
    print(f"  • Files with complex layouts: Skip or use fallback extraction")


if __name__ == "__main__":
    main()