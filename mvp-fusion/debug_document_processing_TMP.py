#!/usr/bin/env python3
"""
GOAL: Debug what's taking time in document processing phase
REASON: Should be 500+ pages/sec but seeing 118 pages/sec (450ms total)
PROBLEM: Need to isolate each step to find the bottleneck
"""

import time
import fitz
from pathlib import Path

def debug_document_processing():
    """Break down each step in document processing to find bottleneck"""
    
    # Use same files as pipeline
    data_dir = Path.home() / 'projects/docling/cli/data_complex/complex_pdfs'
    pdf_files = [f for f in data_dir.glob('*.pdf')]
    
    print("🔍 DOCUMENT PROCESSING STEP-BY-STEP ANALYSIS")
    print("=" * 55)
    
    total_pages = 0
    step_times = {
        'pdf_open': 0,
        'text_extraction': 0,
        'content_creation': 0,
        'content_scanning': 0,
        'yaml_creation': 0,
        'object_creation': 0
    }
    
    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file.name}")
        
        # Step 1: PDF Opening
        start = time.perf_counter()
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        step_times['pdf_open'] += time.perf_counter() - start
        
        # Step 2: Text Extraction (blocks method like pipeline)
        start = time.perf_counter()
        markdown_content = [f"# {pdf_file.stem}\n"]
        for page_num in range(page_count):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            if blocks:
                markdown_content.append(f"\n## Page {page_num + 1}\n")
                for block in blocks:
                    if block[4]:
                        text = block[4].strip()
                        if text:
                            markdown_content.append(text + "\n")
        step_times['text_extraction'] += time.perf_counter() - start
        doc.close()
        
        # Step 3: Content String Creation
        start = time.perf_counter()
        full_content = '\n'.join(markdown_content)
        step_times['content_creation'] += time.perf_counter() - start
        
        # Step 4: Content Scanning (pipeline's _quick_content_scan equivalent)
        start = time.perf_counter()
        content_lower = full_content.lower()
        lines = full_content.split('\n') if '\n' in full_content else []
        
        has_lists = False
        has_headers = False
        for line in lines:
            stripped = line.strip()
            if not has_lists and stripped and (stripped.startswith(('-', '*', '+', '•')) or 
                                              (stripped[0].isdigit() and '.' in stripped[:10])):
                has_lists = True
            if not has_headers and stripped.startswith('#'):
                has_headers = True
            if has_lists and has_headers:
                break
        
        content_flags = {
            'has_tables': '|' in full_content and full_content.count('|') >= 3,
            'has_images': '![' in full_content or 'image' in content_lower,
            'has_formulas': '$' in full_content or '`' in full_content,
            'has_code': '```' in full_content or 'import ' in full_content,
            'has_links': 'http' in content_lower,
            'has_lists': has_lists,
            'has_headers': has_headers,
            'has_footnotes': '[' in full_content and ']' in full_content,
            'has_citations': 'et al' in content_lower or '(202' in full_content,
            'has_structured_data': 'json' in content_lower or 'xml' in content_lower
        }
        step_times['content_scanning'] += time.perf_counter() - start
        
        # Step 5: YAML Creation (like pipeline's optimized version)
        start = time.perf_counter()
        yaml_template = {
            'conversion': {
                'engine': 'mvp-fusion-highspeed',
                'page_count': 0,
                'conversion_time_ms': 0,
                'source_file': '',
                'format': ''
            },
            'content_detection': {},
            'processing': {
                'stage': 'converted',
                'content_length': 0
            }
        }
        
        yaml_frontmatter = yaml_template.copy()
        yaml_frontmatter['conversion'] = yaml_template['conversion'].copy()
        yaml_frontmatter['processing'] = yaml_template['processing'].copy()
        
        yaml_frontmatter['conversion']['page_count'] = page_count
        yaml_frontmatter['conversion']['conversion_time_ms'] = 100.0
        yaml_frontmatter['conversion']['source_file'] = pdf_file.name
        yaml_frontmatter['conversion']['format'] = 'PDF'
        yaml_frontmatter['content_detection'] = content_flags
        yaml_frontmatter['processing']['content_length'] = len(full_content)
        step_times['yaml_creation'] += time.perf_counter() - start
        
        # Step 6: Mock Object Creation (simulate InMemoryDocument)
        start = time.perf_counter()
        mock_doc = {
            'source_file_path': str(pdf_file),
            'markdown_content': full_content,
            'yaml_frontmatter': yaml_frontmatter,
            'memory_limit_mb': 100
        }
        step_times['object_creation'] += time.perf_counter() - start
        
        total_pages += page_count
        file_size_mb = pdf_file.stat().st_size / (1024*1024)
        print(f"   📊 Pages: {page_count}, Size: {file_size_mb:.1f}MB, Content: {len(full_content)} chars")
    
    print(f"\n🚀 STEP-BY-STEP TIMING ANALYSIS:")
    print(f"   Total pages: {total_pages}")
    
    total_time = sum(step_times.values())
    for step, timing in step_times.items():
        percentage = (timing / total_time * 100) if total_time > 0 else 0
        pages_per_sec = total_pages / timing if timing > 0 else 0
        print(f"   {step:15}: {timing*1000:6.1f}ms ({percentage:4.1f}%) - {pages_per_sec:5.0f} pages/sec")
    
    print(f"   {'TOTAL':15}: {total_time*1000:6.1f}ms (100.0%) - {total_pages/total_time:5.0f} pages/sec")
    print(f"\n🎯 Target: 500+ pages/sec")
    
    if total_pages/total_time < 400:
        print(f"🔴 ISSUE: {total_pages/total_time:.0f} pages/sec is below target")
        # Find the slowest step
        slowest_step = max(step_times.keys(), key=lambda k: step_times[k])
        slowest_time = step_times[slowest_step]
        print(f"🔍 Bottleneck: '{slowest_step}' takes {slowest_time*1000:.1f}ms ({slowest_time/total_time*100:.1f}% of total time)")
    else:
        print(f"🟢 OK: {total_pages/total_time:.0f} pages/sec meets target")

if __name__ == "__main__":
    debug_document_processing()