#!/usr/bin/env python3
"""
Simple Markdown Comparison: Standard PyMuPDF vs PyMuPDF4LLM vs Pro Versions
Pass a file, get multiple markdown files, compare timing and quality.
"""

import time
import fitz  # Standard PyMuPDF
from pathlib import Path
import sys

def convert_with_standard_pymupdf(file_path: Path, output_dir: Path):
    """Convert PDF to markdown using standard PyMuPDF."""
    print("🔄 Converting with Standard PyMuPDF...")
    start_time = time.time()
    
    try:
        # Open document
        doc = fitz.open(str(file_path))
        
        # Extract text from all pages
        markdown_lines = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text", sort=True)
            
            # Simple markdown formatting
            markdown_lines.append(f"# Page {page_num + 1}\n\n{page_text}\n\n---\n\n")
        
        # Combine all text
        markdown_content = "".join(markdown_lines)
        
        # Store page count before closing
        total_pages = len(doc)
        doc.close()
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_standard_pymupdf.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with Standard PyMuPDF -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "time": extraction_time,
            "output_file": output_file,
            "pages": total_pages,
            "characters": len(markdown_content),
            "words": len(markdown_content.split())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }

def convert_with_pymupdf4llm(file_path: Path, output_dir: Path):
    """Convert PDF to markdown using PyMuPDF4LLM."""
    print("🚀 Converting with PyMuPDF4LLM...")
    start_time = time.time()
    
    try:
        # Try to import, install if needed
        try:
            import pymupdf4llm
        except ImportError:
            print("   📦 Installing PyMuPDF4LLM...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdf4llm'])
            import pymupdf4llm
        
        # Convert to markdown
        markdown_content = pymupdf4llm.to_markdown(str(file_path))
        
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n'))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }

def convert_with_pymupdf_pro(file_path: Path, output_dir: Path, license_key: str = None):
    """Convert PDF to markdown using PyMuPDF Pro."""
    print("💎 Converting with PyMuPDF Pro...")
    start_time = time.time()
    
    try:
        # Try to import and setup PyMuPDF Pro
        try:
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
                print("   🔓 Pro license activated")
            else:
                print("   ⚠️  No license key - using trial version (first 3 pages only)")
        except ImportError:
            print("   📦 Installing PyMuPDF Pro...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdfpro'])
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
        
        # Open document with Pro features
        doc = fitz.open(str(file_path))
        
        # Extract text from all pages
        markdown_lines = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text", sort=True)
            
            # Simple markdown formatting
            markdown_lines.append(f"# Page {page_num + 1}\n\n{page_text}\n\n---\n\n")
        
        # Combine all text
        markdown_content = "".join(markdown_lines)
        
        # Store page count before closing
        total_pages = len(doc)
        doc.close()
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf_pro.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF Pro -->\n")
            f.write(f"<!-- License: {'Licensed' if license_key else 'Trial (3 pages max)'} -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "time": extraction_time,
            "output_file": output_file,
            "pages": total_pages,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "licensed": bool(license_key)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }

def convert_with_pymupdf4llm_pro(file_path: Path, output_dir: Path, license_key: str = None):
    """Convert PDF to markdown using PyMuPDF4LLM with Pro features."""
    print("🚀💎 Converting with PyMuPDF4LLM Pro...")
    start_time = time.time()
    
    try:
        # Setup Pro first
        try:
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
                print("   🔓 Pro license activated for 4LLM")
            else:
                print("   ⚠️  No license key - using trial version")
        except ImportError:
            print("   📦 Installing PyMuPDF Pro for 4LLM...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdfpro'])
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
        
        # Import and use PyMuPDF4LLM
        try:
            import pymupdf4llm
        except ImportError:
            print("   📦 Installing PyMuPDF4LLM...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdf4llm'])
            import pymupdf4llm
        
        # Convert to markdown with Pro features
        markdown_content = pymupdf4llm.to_markdown(str(file_path))
        
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_pro.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM Pro -->\n")
            f.write(f"<!-- License: {'Licensed' if license_key else 'Trial (3 pages max)'} -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "licensed": bool(license_key)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }

def main():
    """Convert PDF to markdown using all four methods and compare."""
    # Your Pro license key
    PRO_LICENSE_KEY = "FxmPuMWHPlLUpCUpSUq+Xttu"
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default file
        file_path = Path('/home/corey/projects/docling/cli/data/complex_pdfs/Complex1.pdf')
        print("💡 Usage: python test_simple_markdown_comparison.py <path_to_pdf>")
        print(f"   Using default file: {file_path.name}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    # Setup output directory
    output_dir = Path('/home/corey/projects/docling/cli/output/latest')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📄 Converting: {file_path.name}")
    print(f"📐 File size: {file_path.stat().st_size / 1024:.1f} KB")
    print("🔑 Using Pro license key")
    print("=" * 60)
    
    # Convert with all four methods
    result1 = convert_with_standard_pymupdf(file_path, output_dir)
    result2 = convert_with_pymupdf4llm(file_path, output_dir)
    result3 = convert_with_pymupdf_pro(file_path, output_dir, PRO_LICENSE_KEY)
    result4 = convert_with_pymupdf4llm_pro(file_path, output_dir, PRO_LICENSE_KEY)
    
    results = [result1, result2, result3, result4]
    
    print("\n📊 RESULTS")
    print("=" * 40)
    
    method_names = ["Standard PyMuPDF", "PyMuPDF4LLM", "PyMuPDF Pro", "PyMuPDF4LLM Pro"]
    
    # Display results for each method
    for i, (result, name) in enumerate(zip(results, method_names)):
        if result["success"]:
            print(f"✅ {name}:")
            print(f"   ⏱️  Time: {result['time']:.3f} seconds")
            if 'pages' in result:
                print(f"   📄 Pages: {result['pages']}")
            print(f"   📝 Words: {result['words']:,}")
            if 'licensed' in result:
                license_status = "🔓 Licensed" if result['licensed'] else "🔓 Trial"
                print(f"   {license_status}")
            print(f"   📁 File: {result['output_file'].name}")
        else:
            print(f"❌ {name} failed: {result['error']}")
        print()  # Empty line between results
    
    # Speed comparison
    successful_results = [r for r in results if r["success"]]
    if len(successful_results) >= 2:
        print(f"⚡ SPEED COMPARISON")
        print("-" * 30)
        
        # Find fastest method
        times = [r["time"] for r in successful_results]
        fastest_time = min(times)
        fastest_index = times.index(fastest_time)
        fastest_method = method_names[[results.index(r) for r in successful_results][fastest_index]]
        
        print(f"🏆 Fastest: {fastest_method} ({fastest_time:.3f}s)")
        
        # Show speedup comparisons
        for i, result in enumerate(successful_results):
            if result["time"] != fastest_time:
                original_index = results.index(result)
                method_name = method_names[original_index]
                speedup = result["time"] / fastest_time
                print(f"   └─ {speedup:.1f}x faster than {method_name}")
        
        print()
        
        # Word count comparison
        word_counts = [r["words"] for r in successful_results if "words" in r]
        if word_counts:
            max_words = max(word_counts)
            min_words = min(word_counts)
            print(f"📝 Content extraction range: {min_words:,} - {max_words:,} words")
            if max_words != min_words:
                word_diff = max_words - min_words
                print(f"   📊 Difference: {word_diff:,} words ({word_diff/min_words*100:.1f}% more content)")
    
    print(f"\n💾 OUTPUT FILES")
    print("-" * 20)
    
    # List all generated files
    for i, (result, name) in enumerate(zip(results, method_names)):
        if result["success"]:
            print(f"📄 {result['output_file'].name}")
            print(f"   └─ {name} extraction")
    
    print(f"\n📁 All files saved to: {output_dir}")
    print(f"\n💡 Compare the markdown files manually to see quality differences!")
    print(f"🔍 Pro versions should handle Office docs better and have enhanced extraction")

if __name__ == "__main__":
    main()