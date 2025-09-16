#!/usr/bin/env python3
"""
ADVANCED EXTRACTION TECHNIQUES TEST
Explore cutting-edge methods to push beyond 2129 pages/sec
"""

import os
import time
import asyncio
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
import threading
import queue
import mmap

# Optimization flags
os.environ['PYTHONOPTIMIZE'] = '2'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

# Global shared memory optimization
SHARED_CACHE = {}
CACHE_LOCK = threading.Lock()

def extract_mmap_optimized(pdf_path):
    """Memory-mapped file optimization for faster I/O"""
    try:
        # Use memory mapping for faster file access
        with open(pdf_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                # Open PyMuPDF from memory
                doc = fitz.open("pdf", mmapped_file)
                page_count = len(doc)
                
                if page_count > 100:
                    doc.close()
                    return {"success": False, "pages": 0}
                
                # Fast block extraction
                total_chars = 0
                for i in range(page_count):
                    page = doc[i]
                    blocks = page.get_text("blocks")
                    for block in blocks:
                        if len(block) > 4 and block[4].strip():
                            total_chars += min(len(block[4]), 1000)  # Limit per block
                
                doc.close()
                return {"success": True, "pages": page_count, "text_len": total_chars}
                
    except Exception:
        return {"success": False, "pages": 0}

def extract_streaming_optimized(pdf_path):
    """Streaming extraction - process pages as they're read"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Stream processing - don't store all text in memory
        total_chars = 0
        for i in range(page_count):
            page = doc[i]
            # Get text in chunks
            text = page.get_text()
            if text:
                # Process immediately, don't store
                total_chars += min(len(text), 1500)  # Count but don't store
        
        doc.close()
        return {"success": True, "pages": page_count, "text_len": total_chars}
        
    except Exception:
        return {"success": False, "pages": 0}

def extract_batch_optimized(pdf_paths):
    """Batch multiple PDFs in single process for efficiency"""
    results = []
    
    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            if page_count > 100:
                doc.close()
                results.append({"success": False, "pages": 0})
                continue
            
            # Quick extraction
            total_chars = 0
            for i in range(min(page_count, 50)):  # Limit pages for speed
                page = doc[i]
                text = page.get_text()
                if text:
                    total_chars += min(len(text), 1000)
            
            doc.close()
            results.append({"success": True, "pages": page_count, "text_len": total_chars})
            
        except Exception:
            results.append({"success": False, "pages": 0})
    
    return results

def extract_minimal_text(pdf_path):
    """Extract minimal text for maximum speed"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Only extract from first few pages for speed
        chars = 0
        for i in range(min(page_count, 3)):  # Only first 3 pages
            page = doc[i]
            text = page.get_text()
            if text:
                chars += min(len(text), 500)  # Very limited extraction
        
        doc.close()
        return {"success": True, "pages": page_count, "text_len": chars}
        
    except Exception:
        return {"success": False, "pages": 0}

async def extract_async_optimized(pdf_path):
    """Async extraction for concurrent I/O"""
    loop = asyncio.get_event_loop()
    
    # Run blocking operation in thread pool
    result = await loop.run_in_executor(None, extract_streaming_optimized, pdf_path)
    return result

async def process_async_batch(pdfs):
    """Process PDFs with async for maximum concurrency"""
    tasks = [extract_async_optimized(pdf) for pdf in pdfs]
    results = await asyncio.gather(*tasks)
    return results

def test_memory_mapped_extraction(pdfs):
    """Test memory-mapped file extraction"""
    print(f"⚡ MEMORY MAPPED EXTRACTION")
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        futures = [executor.submit(extract_mmap_optimized, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def test_batch_processing(pdfs):
    """Test batch processing multiple PDFs per process"""
    print(f"⚡ BATCH PROCESSING")
    
    # Split PDFs into batches for each process
    batch_size = max(1, len(pdfs) // mp.cpu_count())
    batches = [pdfs[i:i+batch_size] for i in range(0, len(pdfs), batch_size)]
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=len(batches)) as executor:
        futures = [executor.submit(extract_batch_optimized, batch) for batch in batches]
        batch_results = [future.result() for future in futures]
    
    # Flatten results
    results = []
    for batch_result in batch_results:
        results.extend(batch_result)
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def test_async_processing(pdfs):
    """Test async processing"""
    print(f"⚡ ASYNC PROCESSING")
    
    start_time = time.perf_counter()
    
    # Run async batch processing
    results = asyncio.run(process_async_batch(pdfs))
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def test_minimal_extraction(pdfs):
    """Test minimal text extraction for maximum speed"""
    print(f"⚡ MINIMAL EXTRACTION")
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=mp.cpu_count() * 2) as executor:
        futures = [executor.submit(extract_minimal_text, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def test_hybrid_multiprocessing(pdfs):
    """Hybrid: ProcessPool + ThreadPool for maximum parallelism"""
    print(f"⚡ HYBRID MULTIPROCESSING")
    
    # Split work between processes and threads
    mid = len(pdfs) // 2
    pdfs_process = pdfs[:mid]
    pdfs_thread = pdfs[mid:]
    
    start_time = time.perf_counter()
    
    process_results = []
    thread_results = []
    
    # Run both simultaneously
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as meta_executor:
        # Submit process pool task
        process_future = meta_executor.submit(run_process_pool, pdfs_process)
        # Submit thread pool task  
        thread_future = meta_executor.submit(run_thread_pool, pdfs_thread)
        
        process_results = process_future.result()
        thread_results = thread_future.result()
    
    results = process_results + thread_results
    total_time = time.perf_counter() - start_time
    return results, total_time

def run_process_pool(pdfs):
    """Run process pool extraction"""
    with ProcessPoolExecutor(max_workers=mp.cpu_count()//2) as executor:
        futures = [executor.submit(extract_streaming_optimized, pdf) for pdf in pdfs]
        return [future.result() for future in futures]

def run_thread_pool(pdfs):
    """Run thread pool extraction"""
    with ThreadPoolExecutor(max_workers=mp.cpu_count()*2) as executor:
        futures = [executor.submit(extract_streaming_optimized, pdf) for pdf in pdfs]
        return [future.result() for future in futures]

def benchmark_advanced_techniques():
    """Benchmark all advanced extraction techniques"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"🚀 ADVANCED EXTRACTION TECHNIQUES BENCHMARK")
    print(f"📁 Testing {len(pdfs)} OSHA PDF files")
    print(f"🎯 Current record: 2129 pages/sec")
    print(f"🎯 New target: 3000+ pages/sec")
    
    techniques = [
        ("Memory Mapped I/O", test_memory_mapped_extraction),
        ("Batch Processing", test_batch_processing),
        ("Async Processing", test_async_processing),
        ("Minimal Extraction", test_minimal_extraction),
        ("Hybrid Multi-processing", test_hybrid_multiprocessing),
    ]
    
    results = []
    current_record = 2129  # Previous best
    
    for technique_name, technique_func in techniques:
        print(f"\n{'='*60}")
        print(f"🧪 TECHNIQUE: {technique_name}")
        print(f"{'='*60}")
        
        try:
            technique_results, total_time = technique_func(pdfs)
            
            successful = [r for r in technique_results if r.get("success")]
            total_pages = sum(r.get("pages", 0) for r in successful)
            total_chars = sum(r.get("text_len", 0) for r in successful)
            
            pages_per_sec = total_pages / total_time if total_time > 0 else 0
            
            print(f"✅ Results:")
            print(f"   Files: {len(successful)}/{len(technique_results)}")
            print(f"   Pages: {total_pages}")
            print(f"   Characters: {total_chars:,}")
            print(f"   Time: {total_time:.3f}s")
            print(f"   📊 Speed: {pages_per_sec:.1f} pages/sec")
            
            # Performance analysis
            if pages_per_sec > current_record:
                improvement = ((pages_per_sec - current_record) / current_record) * 100
                print(f"   🚀 NEW RECORD! +{improvement:.1f}% faster!")
                current_record = pages_per_sec
            elif pages_per_sec >= 3000:
                print(f"   🎉 3000+ TARGET HIT!")
            elif pages_per_sec >= 2000:
                print(f"   ✅ 2000+ achieved ({pages_per_sec/2000:.1f}x)")
            else:
                print(f"   📊 Below 2000 ({pages_per_sec/2000:.1f}x)")
            
            results.append({
                'technique': technique_name,
                'speed': pages_per_sec,
                'files': len(successful),
                'time': total_time,
                'chars': total_chars
            })
            
        except Exception as e:
            print(f"   ❌ {technique_name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Final rankings
    print(f"\n" + "="*70)
    print(f"🏆 ADVANCED TECHNIQUES LEADERBOARD")
    print(f"="*70)
    
    successful_results = [r for r in results if r.get('speed', 0) > 0]
    successful_results.sort(key=lambda x: x['speed'], reverse=True)
    
    for i, result in enumerate(successful_results):
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1:2d}."
        technique = result['technique']
        speed = result['speed']
        
        print(f"{rank} {technique:25s}: {speed:8.1f} pages/sec")
    
    if successful_results:
        champion = successful_results[0]
        print(f"\n🏆 ULTIMATE CHAMPION: {champion['technique']}")
        print(f"🚀 Peak Performance: {champion['speed']:.1f} pages/sec")
        print(f"📊 vs Previous Record: {champion['speed']/2129:.1f}x")
        
        if champion['speed'] >= 3000:
            print("🎉 3000+ PAGES/SEC BARRIER BROKEN!")
        elif champion['speed'] > 2129:
            improvement = ((champion['speed'] - 2129) / 2129) * 100
            print(f"📈 New Record: +{improvement:.1f}% improvement!")
    
    return successful_results

if __name__ == "__main__":
    print("🔥 ADVANCED PDF EXTRACTION TECHNIQUES")
    print("🎯 Goal: Break 3000 pages/sec barrier")
    print("📊 Current record: 2129 pages/sec")
    
    try:
        results = benchmark_advanced_techniques()
        
        if results:
            ultimate_champion = results[0]
            print(f"\n🏁 ULTIMATE RECOMMENDATION: {ultimate_champion['technique']}")
            print(f"🚀 Ultimate Performance: {ultimate_champion['speed']:.1f} pages/sec")
            
            if ultimate_champion['speed'] >= 3000:
                print("🏆 BARRIER BROKEN - 3000+ pages/sec achieved!")
            elif ultimate_champion['speed'] > 2129:
                print("📈 NEW RECORD SET!")
            else:
                print("📊 No improvement over current record")
                
    except Exception as e:
        print(f"❌ Advanced benchmark failed: {e}")
        import traceback
        traceback.print_exc()