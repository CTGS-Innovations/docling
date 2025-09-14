#!/usr/bin/env python3
"""
Enhanced PyMuPDF4LLM Quality Comparison with Advanced Options
Tests different PyMuPDF4LLM configurations to optimize markdown quality.
"""

import time
import fitz  # Standard PyMuPDF
from pathlib import Path
import sys
import json

def test_standard_pymupdf4llm(file_path: Path, output_dir: Path):
    """Test standard PyMuPDF4LLM with default settings."""
    print("🚀 Testing PyMuPDF4LLM (Standard)...")
    start_time = time.time()
    
    try:
        import pymupdf4llm
        
        # Standard conversion with defaults
        markdown_content = pymupdf4llm.to_markdown(str(file_path))
        
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_standard.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM Standard Settings -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM Standard",
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "config": "default settings"
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM Standard",
            "error": str(e),
            "time": time.time() - start_time
        }

def test_pymupdf4llm_enhanced_tables(file_path: Path, output_dir: Path):
    """Test PyMuPDF4LLM with enhanced table detection."""
    print("📊 Testing PyMuPDF4LLM (Enhanced Tables)...")
    start_time = time.time()
    
    try:
        import pymupdf4llm
        
        # Enhanced table detection with 'lines' strategy
        markdown_content = pymupdf4llm.to_markdown(
            str(file_path),
            table_strategy="lines",  # More aggressive table detection
            force_text=True,  # Extract text even when overlapping
            ignore_graphics=False,  # Keep graphics for table detection
            fontsize_limit=2  # Include smaller fonts
        )
        
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_enhanced_tables.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM Enhanced Tables -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- Config: table_strategy='lines', force_text=True -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM Enhanced Tables",
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "config": "table_strategy='lines', force_text=True"
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM Enhanced Tables",
            "error": str(e),
            "time": time.time() - start_time
        }

def test_pymupdf4llm_smart_headers(file_path: Path, output_dir: Path):
    """Test PyMuPDF4LLM with intelligent header detection."""
    print("📝 Testing PyMuPDF4LLM (Smart Headers)...")
    start_time = time.time()
    
    try:
        import pymupdf4llm
        import pymupdf
        
        # Open document for header analysis
        doc = pymupdf.open(str(file_path))
        
        # Use IdentifyHeaders for intelligent header detection
        headers = pymupdf4llm.IdentifyHeaders(doc, body_limit=10, max_levels=4)
        
        # Enhanced conversion with smart headers
        markdown_content = pymupdf4llm.to_markdown(
            doc,
            hdr_info=headers,  # Smart header detection
            table_strategy="lines_strict",  # Standard table detection
            force_text=True,  # Extract overlapping text
            ignore_code=False,  # Keep code formatting
            fontsize_limit=2,  # Include smaller fonts
            detect_bg_color=True  # Ignore background color text
        )
        
        doc.close()
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_smart_headers.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM Smart Headers -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- Config: IdentifyHeaders, force_text=True, detect_bg_color=True -->\n")
            f.write(f"<!-- Header mapping: {headers.header_id} -->\n")
            f.write(f"<!-- Body limit: {headers.body_limit} -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM Smart Headers",
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "config": "IdentifyHeaders + enhanced options",
            "header_mapping": headers.header_id,
            "body_limit": headers.body_limit
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM Smart Headers",
            "error": str(e),
            "time": time.time() - start_time
        }

def test_pymupdf4llm_toc_headers(file_path: Path, output_dir: Path):
    """Test PyMuPDF4LLM with Table of Contents based headers."""
    print("📚 Testing PyMuPDF4LLM (TOC Headers)...")
    start_time = time.time()
    
    try:
        import pymupdf4llm
        import pymupdf
        
        # Open document for TOC analysis
        doc = pymupdf.open(str(file_path))
        toc = doc.get_toc()
        
        if len(toc) > 0:
            print(f"   📖 Found {len(toc)} TOC entries")
            
            # Use TocHeaders for TOC-based header detection
            toc_headers = pymupdf4llm.TocHeaders(doc)
            
            # Enhanced conversion with TOC headers
            markdown_content = pymupdf4llm.to_markdown(
                doc,
                hdr_info=toc_headers,  # TOC-based header detection
                table_strategy="lines",  # Enhanced table detection
                force_text=True,  # Extract overlapping text
                ignore_code=False,  # Keep code formatting
                fontsize_limit=1,  # Include very small fonts
                detect_bg_color=True  # Ignore background color text
            )
            
            config_note = f"TocHeaders with {len(toc)} TOC entries"
        else:
            print("   ⚠️  No TOC found, using standard header detection")
            # Fallback to standard detection
            markdown_content = pymupdf4llm.to_markdown(
                doc,
                table_strategy="lines",
                force_text=True,
                fontsize_limit=1,
                detect_bg_color=True
            )
            config_note = "No TOC available, standard detection used"
        
        doc.close()
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_toc_headers.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM TOC Headers -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- Config: {config_note} -->\n")
            f.write(f"<!-- TOC entries: {len(toc)} -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM TOC Headers",
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "config": config_note,
            "toc_entries": len(toc)
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM TOC Headers",
            "error": str(e),
            "time": time.time() - start_time
        }

def test_pymupdf4llm_pro_optimized(file_path: Path, output_dir: Path, license_key: str = None):
    """Test PyMuPDF4LLM Pro with optimized settings for complex documents."""
    print("💎🚀 Testing PyMuPDF4LLM Pro (Optimized)...")
    start_time = time.time()
    
    try:
        # Setup Pro first
        try:
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
                print("   🔓 Pro license activated")
            else:
                print("   ⚠️  No license key - using trial version")
        except ImportError:
            print("   📦 Installing PyMuPDF Pro...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdfpro'])
            import pymupdf.pro
            if license_key:
                pymupdf.pro.unlock(license_key)
        
        import pymupdf4llm
        import pymupdf
        
        # Open document for analysis
        doc = pymupdf.open(str(file_path))
        
        # Try to use smart headers with Pro
        try:
            headers = pymupdf4llm.IdentifyHeaders(doc, body_limit=8, max_levels=5)
            header_info = headers
            header_note = f"IdentifyHeaders: {headers.header_id}, body_limit: {headers.body_limit}"
        except:
            header_info = None
            header_note = "Default header detection"
        
        # Pro optimized conversion
        markdown_content = pymupdf4llm.to_markdown(
            doc,
            hdr_info=header_info,  # Smart or default headers
            table_strategy="lines",  # Enhanced table detection
            force_text=True,  # Extract overlapping text
            ignore_code=False,  # Keep code formatting
            ignore_graphics=False,  # Keep graphics for better detection
            ignore_images=False,  # Keep images
            fontsize_limit=1,  # Include very small fonts
            detect_bg_color=True,  # Ignore background color text
            ignore_alpha=False,  # Include semi-transparent text
            dpi=200,  # Higher DPI for better image quality
            image_size_limit=0.03  # Include smaller images (3% vs 5% default)
        )
        
        doc.close()
        extraction_time = time.time() - start_time
        
        # Save markdown file
        output_file = output_dir / f"{file_path.stem}_pymupdf4llm_pro_optimized.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated with PyMuPDF4LLM Pro Optimized -->\n")
            f.write(f"<!-- License: {'Licensed' if license_key else 'Trial'} -->\n")
            f.write(f"<!-- Extraction time: {extraction_time:.3f} seconds -->\n")
            f.write(f"<!-- Config: {header_note}, enhanced detection -->\n")
            f.write(f"<!-- Settings: dpi=200, force_text=True, image_size_limit=0.03 -->\n")
            f.write(f"<!-- File: {file_path.name} -->\n\n")
            f.write(markdown_content)
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM Pro Optimized",
            "time": extraction_time,
            "output_file": output_file,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n')),
            "config": "Pro with optimized settings",
            "licensed": bool(license_key),
            "header_detection": header_note
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM Pro Optimized",
            "error": str(e),
            "time": time.time() - start_time
        }

def compare_enhanced_methods(file_path: Path):
    """Compare all enhanced PyMuPDF4LLM methods."""
    PRO_LICENSE_KEY = "FxmPuMWHPlLUpCUpSUq+Xttu"
    
    print(f"🧪 ENHANCED PYMUPDF4LLM QUALITY COMPARISON")
    print("=" * 70)
    print(f"📄 File: {file_path.name}")
    print(f"📐 Size: {file_path.stat().st_size / 1024:.1f} KB")
    print(f"🔑 Using Pro license for optimized test")
    print()
    
    # Setup output directory
    output_dir = Path('/home/corey/projects/docling/cli/output/latest')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run all enhanced tests
    results = []
    
    # Test 1: Standard PyMuPDF4LLM
    result1 = test_standard_pymupdf4llm(file_path, output_dir)
    results.append(result1)
    if result1["success"]:
        print(f"   ✅ {result1['time']:.3f}s - {result1['words']:,} words, {result1['lines']:,} lines")
    else:
        print(f"   ❌ Failed: {result1['error']}")
    
    # Test 2: Enhanced Tables
    result2 = test_pymupdf4llm_enhanced_tables(file_path, output_dir)
    results.append(result2)
    if result2["success"]:
        print(f"   ✅ {result2['time']:.3f}s - {result2['words']:,} words, {result2['lines']:,} lines")
    else:
        print(f"   ❌ Failed: {result2['error']}")
    
    # Test 3: Smart Headers
    result3 = test_pymupdf4llm_smart_headers(file_path, output_dir)
    results.append(result3)
    if result3["success"]:
        print(f"   ✅ {result3['time']:.3f}s - {result3['words']:,} words, {result3['lines']:,} lines")
        if 'header_mapping' in result3:
            print(f"     📝 Headers detected: {result3['header_mapping']}")
    else:
        print(f"   ❌ Failed: {result3['error']}")
    
    # Test 4: TOC Headers
    result4 = test_pymupdf4llm_toc_headers(file_path, output_dir)
    results.append(result4)
    if result4["success"]:
        print(f"   ✅ {result4['time']:.3f}s - {result4['words']:,} words, {result4['lines']:,} lines")
        if 'toc_entries' in result4:
            print(f"     📚 TOC entries: {result4['toc_entries']}")
    else:
        print(f"   ❌ Failed: {result4['error']}")
    
    # Test 5: Pro Optimized
    result5 = test_pymupdf4llm_pro_optimized(file_path, output_dir, PRO_LICENSE_KEY)
    results.append(result5)
    if result5["success"]:
        print(f"   ✅ {result5['time']:.3f}s - {result5['words']:,} words, {result5['lines']:,} lines")
        if 'licensed' in result5:
            license_status = "🔓 Licensed" if result5['licensed'] else "🔓 Trial"
            print(f"     {license_status}")
    else:
        print(f"   ❌ Failed: {result5['error']}")
    
    # Analysis
    print(f"\\n📈 QUALITY & PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    successful_results = [r for r in results if r["success"]]
    if len(successful_results) >= 2:
        # Performance comparison
        times = [r["time"] for r in successful_results]
        fastest_time = min(times)
        fastest_method = next(r["method"] for r in successful_results if r["time"] == fastest_time)
        
        print(f"🏆 Fastest: {fastest_method} ({fastest_time:.3f}s)")
        
        # Content comparison
        word_counts = [r["words"] for r in successful_results if "words" in r]
        line_counts = [r["lines"] for r in successful_results if "lines" in r]
        
        if word_counts:
            max_words = max(word_counts)
            min_words = min(word_counts)
            max_word_method = next(r["method"] for r in successful_results if r.get("words") == max_words)
            
            print(f"📝 Most content: {max_word_method} ({max_words:,} words)")
            print(f"📊 Content range: {min_words:,} - {max_words:,} words")
            
            if max_words != min_words:
                word_diff = max_words - min_words
                print(f"   📈 Best extraction has {word_diff:,} more words ({word_diff/min_words*100:.1f}% more)")
        
        if line_counts:
            max_lines = max(line_counts)
            min_lines = min(line_counts)
            print(f"📄 Line range: {min_lines:,} - {max_lines:,} lines")
    
    # Save detailed results
    comparison_file = output_dir / f"{file_path.stem}_enhanced_comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump({
            "file": str(file_path),
            "file_size_kb": file_path.stat().st_size / 1024,
            "test_timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "test_type": "Enhanced PyMuPDF4LLM Quality Comparison",
            "results": results
        }, f, indent=2, default=str)
    
    print(f"\\n💾 OUTPUT FILES")
    print("-" * 30)
    
    # List all generated files
    for result in results:
        if result["success"]:
            print(f"📄 {result['output_file'].name}")
            print(f"   └─ {result['method']}: {result['config']}")
    
    print(f"\\n📁 All files saved to: {output_dir}")
    print(f"💾 Detailed results: {comparison_file.name}")
    print(f"\\n💡 RECOMMENDATIONS:")
    print(f"   📝 Compare markdown files manually for formula/table quality")
    print(f"   🔍 Check header detection accuracy in complex documents")  
    print(f"   📊 Look for better table formatting and mathematical content preservation")
    print(f"   ⚡ Consider speed vs quality tradeoffs for your use case")
    
    return results

def main():
    """Main enhanced comparison test."""
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default to Complex1.pdf
        file_path = Path('/home/corey/projects/docling/cli/data/complex_pdfs/Complex1.pdf')
        print("💡 Usage: python test_enhanced_markdown_comparison.py <path_to_pdf>")
        print(f"   Using default file: {file_path.name}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print(f"💡 Usage: python test_enhanced_markdown_comparison.py <path_to_pdf>")
        return
    
    results = compare_enhanced_methods(file_path)
    
    # Summary recommendations
    print(f"\\n🎯 FINAL SUMMARY")
    print("=" * 40)
    
    successful_results = [r for r in results if r["success"]]
    if len(successful_results) >= 2:
        # Find best performing methods
        word_counts = [(r["words"], r["method"]) for r in successful_results if "words" in r]
        if word_counts:
            best_content = max(word_counts)
            print(f"🏆 Best content extraction: {best_content[1]} ({best_content[0]:,} words)")
        
        times = [(r["time"], r["method"]) for r in successful_results]
        fastest = min(times)
        print(f"⚡ Fastest method: {fastest[1]} ({fastest[0]:.3f}s)")
        
        print(f"\\n🔧 For complex documents with formulas/tables:")
        print(f"   • Use Enhanced Tables or Pro Optimized for best quality")
        print(f"   • Use Smart Headers for documents with clear font hierarchies")
        print(f"   • Use TOC Headers for well-structured documents with bookmarks")
        print(f"   • Standard version for simple documents where speed matters")

if __name__ == "__main__":
    main()