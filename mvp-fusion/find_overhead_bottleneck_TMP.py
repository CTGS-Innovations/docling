#!/usr/bin/env python3
"""
GOAL: Find the 325ms overhead between isolated (119ms) and pipeline (444ms) performance
REASON: Pipeline adds 325ms overhead to pure PDF processing  
PROBLEM: Need to identify what pipeline operations are adding this massive overhead
"""

import time
import fitz
from pathlib import Path
import sys
import os

# Add mvp-fusion to path
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_pipeline_overhead():
    """Test each pipeline component to find the 325ms overhead"""
    
    data_dir = Path.home() / 'projects/docling/cli/data_complex/complex_pdfs'
    pdf_files = [f for f in data_dir.glob('*.pdf')]
    
    print("🔍 PIPELINE OVERHEAD ANALYSIS")
    print("=" * 50)
    print(f"Target: Find where 325ms overhead comes from")
    print(f"Isolated: 119ms (442 pages/sec)")  
    print(f"Pipeline: 444ms (119 pages/sec)")
    print()
    
    total_pages = 0
    
    # Test 1: Pure PDF processing (baseline)
    start = time.perf_counter()
    for pdf_file in pdf_files:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        total_pages += page_count
        
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
        
        full_content = '\n'.join(markdown_content)
        doc.close()
    
    baseline_time = time.perf_counter() - start
    print(f"✅ Baseline (pure PDF): {baseline_time*1000:.1f}ms ({total_pages/baseline_time:.0f} pages/sec)")
    
    # Test 2: Add InMemoryDocument creation
    start = time.perf_counter()
    for pdf_file in pdf_files:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        
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
        
        full_content = '\n'.join(markdown_content)
        doc.close()
        
        # Add InMemoryDocument creation
        try:
            from pipeline.in_memory_document import InMemoryDocument
            memory_doc = InMemoryDocument(
                source_file_path=str(pdf_file),
                memory_limit_mb=100
            )
            memory_doc.markdown_content = full_content
        except Exception as e:
            print(f"InMemoryDocument error: {e}")
    
    inmemory_time = time.perf_counter() - start
    inmemory_overhead = inmemory_time - baseline_time
    print(f"📄 + InMemoryDocument: {inmemory_time*1000:.1f}ms (+{inmemory_overhead*1000:.1f}ms overhead)")
    
    # Test 3: Add content scanning
    start = time.perf_counter()
    for pdf_file in pdf_files:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        
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
        
        full_content = '\n'.join(markdown_content)
        doc.close()
        
        # Add InMemoryDocument creation
        try:
            from pipeline.in_memory_document import InMemoryDocument
            memory_doc = InMemoryDocument(
                source_file_path=str(pdf_file),
                memory_limit_mb=100
            )
            memory_doc.markdown_content = full_content
        except Exception as e:
            pass
        
        # Add content scanning (pipeline's _quick_content_scan)
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
    
    content_scan_time = time.perf_counter() - start
    content_scan_overhead = content_scan_time - inmemory_time
    print(f"🔍 + Content scanning: {content_scan_time*1000:.1f}ms (+{content_scan_overhead*1000:.1f}ms overhead)")
    
    # Test 4: Add YAML generation
    start = time.perf_counter()
    for pdf_file in pdf_files:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        
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
        
        full_content = '\n'.join(markdown_content)
        doc.close()
        
        # Add all previous steps
        try:
            from pipeline.in_memory_document import InMemoryDocument
            memory_doc = InMemoryDocument(
                source_file_path=str(pdf_file),
                memory_limit_mb=100
            )
            memory_doc.markdown_content = full_content
        except Exception as e:
            pass
        
        # Content scanning
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
        
        # Add YAML generation (pipeline's optimized template approach)
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
    
    yaml_time = time.perf_counter() - start
    yaml_overhead = yaml_time - content_scan_time
    print(f"📋 + YAML generation: {yaml_time*1000:.1f}ms (+{yaml_overhead*1000:.1f}ms overhead)")
    
    # Test 5: Add threading/queue simulation
    start = time.perf_counter()
    from queue import Queue
    from dataclasses import dataclass
    from typing import Any, Dict
    
    @dataclass
    class WorkItem:
        document: Any
        metadata: Dict[str, Any]
        ingestion_time: float
    
    work_queue = Queue(maxsize=100)
    
    for pdf_file in pdf_files:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        
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
        
        full_content = '\n'.join(markdown_content)
        doc.close()
        
        # All previous operations
        try:
            from pipeline.in_memory_document import InMemoryDocument
            memory_doc = InMemoryDocument(
                source_file_path=str(pdf_file),
                memory_limit_mb=100
            )
            memory_doc.markdown_content = full_content
        except Exception as e:
            memory_doc = {'content': full_content}  # Fallback
        
        # Content scanning and YAML (abbreviated)
        content_flags = {'has_tables': '|' in full_content}
        yaml_frontmatter = {'conversion': {'page_count': page_count}}
        
        # Add queue operations
        work_item = WorkItem(
            document=memory_doc,
            metadata={'conversion_time': 0.1},
            ingestion_time=time.perf_counter()
        )
        
        try:
            work_queue.put(work_item, timeout=5.0)
            # Simulate queue retrieval
            retrieved_item = work_queue.get(timeout=1.0)
        except:
            pass
    
    queue_time = time.perf_counter() - start
    queue_overhead = queue_time - yaml_time
    print(f"🔄 + Queue operations: {queue_time*1000:.1f}ms (+{queue_overhead*1000:.1f}ms overhead)")
    
    print(f"\n🚀 OVERHEAD BREAKDOWN:")
    total_overhead = queue_time - baseline_time
    print(f"   Baseline (PDF only): {baseline_time*1000:.1f}ms")
    print(f"   Total with pipeline: {queue_time*1000:.1f}ms")
    print(f"   TOTAL OVERHEAD: {total_overhead*1000:.1f}ms")
    print(f"   Target pipeline time: 444ms")
    print(f"   Unaccounted time: {(0.444 - queue_time)*1000:.1f}ms")

if __name__ == "__main__":
    test_pipeline_overhead()