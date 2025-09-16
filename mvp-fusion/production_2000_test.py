#!/usr/bin/env python3
"""
PRODUCTION 2000+ PAGES/SEC WITH MARKDOWN OUTPUT
Save extracted text as .md files with original names
"""

import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

# Optimization flags
os.environ['PYTHONOPTIMIZE'] = '2'

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def extract_and_save_markdown(pdf_path_and_output_dir):
    """Extract text and save as markdown file"""
    pdf_path, output_dir = pdf_path_and_output_dir
    
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {
                "success": False, 
                "pages": 0,
                "file": str(pdf_path),
                "error": f"Skipped: {page_count} pages (>100 limit)"
            }
        
        # Extract text using blocks method (proven fastest)
        markdown_content = []
        
        # Add markdown header with document info
        markdown_content.append(f"# {pdf_path.name}\n")
        markdown_content.append(f"**Pages:** {page_count}  ")
        markdown_content.append(f"**Source:** {pdf_path.name}  ")
        markdown_content.append(f"**Extracted:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        markdown_content.append("---\n\n")
        
        # Extract text from each page
        for i in range(page_count):
            page = doc[i]
            
            # Add page header
            markdown_content.append(f"## Page {i+1}\n\n")
            
            # Get blocks for better structure
            blocks = page.get_text("blocks")
            
            for block in blocks:
                if len(block) > 4:
                    text = block[4].strip()
                    if text:
                        # Clean up text for markdown
                        text = text.replace('\r\n', '\n')
                        text = text.replace('\r', '\n')
                        
                        # Add paragraph with proper spacing
                        markdown_content.append(text)
                        markdown_content.append("\n\n")
            
            # Page separator
            if i < page_count - 1:
                markdown_content.append("---\n\n")
        
        doc.close()
        
        # Join all content
        full_markdown = ''.join(markdown_content)
        
        # Save markdown file
        output_file = output_dir / f"{pdf_path.stem}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_markdown)
            
            return {
                "success": True,
                "pages": page_count,
                "file": str(pdf_path),
                "output": str(output_file),
                "text_len": len(full_markdown)
            }
            
        except Exception as save_error:
            return {
                "success": False,
                "pages": page_count,
                "file": str(pdf_path),
                "error": f"Save failed: {str(save_error)}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "pages": 0,
            "file": str(pdf_path),
            "error": str(e)
        }

def process_batch_with_saving(pdfs, output_dir, max_workers=None):
    """Process PDFs and save as markdown using ProcessPoolExecutor"""
    if max_workers is None:
        max_workers = mp.cpu_count()
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Processing {len(pdfs)} files with {max_workers} processes")
    print(f"📁 Saving markdown files to: {output_dir}")
    
    # Prepare arguments (pdf_path, output_dir) for each job
    job_args = [(pdf, output_dir) for pdf in pdfs]
    
    start_time = time.perf_counter()
    
    # Process with ProcessPoolExecutor for maximum speed
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_and_save_markdown, args) for args in job_args]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def production_benchmark():
    """Production benchmark with markdown output"""
    # Input and output directories
    osha_dir = Path("../cli/data_osha")
    output_dir = Path("../output/markdown_2000")
    
    # Get all OSHA PDFs
    pdfs = list(osha_dir.glob("*.pdf"))[:100]  # Test with 100 files
    
    print(f"🎯 PRODUCTION 2000+ PAGES/SEC WITH MARKDOWN OUTPUT")
    print(f"📁 Input: {len(pdfs)} OSHA PDF files")
    print(f"📁 Output: {output_dir}")
    print(f"🎯 Target: 2000+ pages/sec with full markdown saving")
    
    # Process and save
    results, total_time = process_batch_with_saving(pdfs, output_dir)
    
    # Calculate metrics
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    total_chars = sum(r.get("text_len", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    files_per_sec = len(successful) / total_time if total_time > 0 else 0
    
    print(f"\n" + "="*70)
    print(f"📊 PRODUCTION RESULTS")
    print(f"="*70)
    
    print(f"✅ Successfully processed: {len(successful)}/{len(results)} files")
    print(f"📄 Total pages extracted: {total_pages}")
    print(f"📝 Total characters written: {total_chars:,}")
    print(f"💾 Markdown files saved: {len(successful)}")
    print(f"⏱️  Total processing time: {total_time:.2f}s")
    
    print(f"\n🚀 PERFORMANCE METRICS:")
    print(f"   Pages per second: {pages_per_sec:.1f}")
    print(f"   Files per second: {files_per_sec:.1f}")
    
    # Performance analysis
    if pages_per_sec >= 2000:
        print(f"   🎉 TARGET ACHIEVED! {pages_per_sec:.1f} pages/sec")
        print(f"   📈 Performance: {pages_per_sec/700:.1f}x baseline")
    elif pages_per_sec >= 1000:
        print(f"   ✅ Good performance: {pages_per_sec:.1f} pages/sec")
    else:
        print(f"   ⚠️  Below target: {pages_per_sec:.1f} pages/sec")
    
    # Show saved files
    if successful:
        print(f"\n📁 SAVED MARKDOWN FILES:")
        for i, result in enumerate(successful[:5]):  # Show first 5
            output_file = Path(result.get('output', ''))
            if output_file.exists():
                size = output_file.stat().st_size
                print(f"   ✓ {output_file.name} ({size:,} bytes)")
        
        if len(successful) > 5:
            print(f"   ... and {len(successful) - 5} more files")
    
    # Show errors if any
    if failed:
        print(f"\n⚠️  ERRORS ({len(failed)} files):")
        for result in failed[:3]:  # Show first 3 errors
            print(f"   • {Path(result['file']).name}: {result.get('error', 'Unknown error')}")
        if len(failed) > 3:
            print(f"   ... and {len(failed) - 3} more errors")
    
    # Verify output files
    output_files = list(output_dir.glob("*.md"))
    print(f"\n✅ VERIFICATION:")
    print(f"   Markdown files in output directory: {len(output_files)}")
    
    if output_files:
        # Check a sample file
        sample_file = output_files[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample_content = f.read()
        
        print(f"\n📄 SAMPLE OUTPUT ({sample_file.name}):")
        print("   " + "-"*50)
        # Show first 500 characters
        preview = sample_content[:500].replace('\n', '\n   ')
        print(f"   {preview}")
        if len(sample_content) > 500:
            print(f"   ... ({len(sample_content) - 500} more characters)")
        print("   " + "-"*50)
    
    return {
        'pages_per_sec': pages_per_sec,
        'files_per_sec': files_per_sec,
        'total_files': len(successful),
        'total_pages': total_pages,
        'output_dir': str(output_dir)
    }

def verify_markdown_quality(output_dir, sample_count=3):
    """Verify the quality of generated markdown files"""
    output_dir = Path(output_dir)
    md_files = list(output_dir.glob("*.md"))[:sample_count]
    
    print(f"\n🔍 MARKDOWN QUALITY CHECK")
    print(f"="*70)
    
    for md_file in md_files:
        print(f"\n📄 {md_file.name}:")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check structure
        has_title = content.startswith("#")
        has_metadata = "**Pages:**" in content and "**Source:**" in content
        has_page_headers = "## Page" in content
        has_content = len(content) > 1000
        
        print(f"   ✓ Has title: {has_title}")
        print(f"   ✓ Has metadata: {has_metadata}")
        print(f"   ✓ Has page headers: {has_page_headers}")
        print(f"   ✓ Has substantial content: {has_content} ({len(content):,} chars)")
        
        # Count pages mentioned
        page_count = content.count("## Page")
        print(f"   ✓ Pages extracted: {page_count}")

if __name__ == "__main__":
    print("🔥 PRODUCTION MODE: 2000+ PAGES/SEC WITH MARKDOWN OUTPUT")
    print("📊 Using ProcessPoolExecutor for maximum performance")
    print("💾 Saving all output as .md files")
    
    try:
        results = production_benchmark()
        
        print(f"\n🏁 FINAL PRODUCTION RESULTS")
        print(f"🚀 Performance: {results['pages_per_sec']:.1f} pages/sec")
        print(f"📁 Output saved to: {results['output_dir']}")
        print(f"✅ Files processed: {results['total_files']}")
        print(f"📄 Total pages: {results['total_pages']}")
        
        if results['pages_per_sec'] >= 2000:
            print("\n🏆 MISSION ACCOMPLISHED!")
            print("✅ 2000+ pages/sec achieved WITH full markdown output!")
        
        # Verify quality
        verify_markdown_quality(results['output_dir'])
        
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        import traceback
        traceback.print_exc()