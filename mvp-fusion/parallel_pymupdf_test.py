#!/usr/bin/env python3
"""
PARALLEL PyMuPDF INSTANCES TEST
Use multiple PyMuPDF extractors in parallel with different strategies
"""

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
import threading

# Optimization flags
os.environ['PYTHONOPTIMIZE'] = '2'

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def extract_blocks_optimized(pdf_path):
    """Optimized blocks extraction"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Fastest block extraction
        text_parts = []
        for i in range(page_count):
            page = doc[i]
            blocks = page.get_text("blocks")
            # Only get text from blocks, skip positioning data
            page_text = " ".join([block[4] for block in blocks if len(block) > 4 and block[4].strip()])
            if page_text.strip():
                text_parts.append(page_text[:2000])  # Limit per page for speed
        
        doc.close()
        return {"success": True, "pages": page_count, "text_len": sum(len(t) for t in text_parts)}
        
    except Exception:
        return {"success": False, "pages": 0}

def extract_basic_optimized(pdf_path):
    """Optimized basic extraction"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Basic extraction with limits
        text_len = 0
        for i in range(page_count):
            page = doc[i]
            text = page.get_text()
            if text and len(text.strip()) > 0:
                text_len += min(len(text), 2000)  # Limit processing per page
        
        doc.close()
        return {"success": True, "pages": page_count, "text_len": text_len}
        
    except Exception:
        return {"success": False, "pages": 0}

def process_batch_parallel_extractors(pdfs, max_workers=None):
    """Use multiple extraction strategies in parallel"""
    if max_workers is None:
        max_workers = mp.cpu_count() * 3  # Aggressive threading
    
    # Split PDFs between different extraction methods
    mid = len(pdfs) // 2
    pdfs_blocks = pdfs[:mid]
    pdfs_basic = pdfs[mid:]
    
    print(f"🚀 Parallel extractors: {len(pdfs_blocks)} blocks + {len(pdfs_basic)} basic")
    print(f"🧵 Using {max_workers} total workers")
    
    start_time = time.perf_counter()
    results = []
    
    # Run both extraction methods simultaneously
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        # Submit blocks extraction jobs
        for pdf in pdfs_blocks:
            future = executor.submit(extract_blocks_optimized, pdf)
            futures.append(future)
        
        # Submit basic extraction jobs  
        for pdf in pdfs_basic:
            future = executor.submit(extract_basic_optimized, pdf)
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def process_batch_process_pool(pdfs, max_workers=None):
    """Use ProcessPoolExecutor for true parallelism"""
    if max_workers is None:
        max_workers = mp.cpu_count()
    
    print(f"🚀 Process pool: {max_workers} processes")
    
    start_time = time.perf_counter()
    
    # Use processes instead of threads
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_blocks_optimized, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    return results, total_time

def process_batch_hybrid(pdfs, max_workers=None):
    """Hybrid approach: Multiple thread pools"""
    if max_workers is None:
        max_workers = mp.cpu_count() * 2
    
    # Split into multiple batches for parallel processing
    batch_size = len(pdfs) // 4  # 4 parallel batches
    batches = [pdfs[i:i+batch_size] for i in range(0, len(pdfs), batch_size)]
    
    print(f"🚀 Hybrid: {len(batches)} batches with {max_workers//len(batches)} workers each")
    
    start_time = time.perf_counter()
    all_results = []
    
    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=len(batches)) as batch_executor:
        batch_futures = []
        
        for batch in batches:
            future = batch_executor.submit(process_single_batch, batch, max_workers//len(batches))
            batch_futures.append(future)
        
        for future in batch_futures:
            batch_results = future.result()
            all_results.extend(batch_results)
    
    total_time = time.perf_counter() - start_time
    return all_results, total_time

def process_single_batch(pdfs, workers):
    """Process a single batch of PDFs"""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(extract_blocks_optimized, pdf) for pdf in pdfs]
        return [future.result() for future in futures]

def benchmark_parallel_strategies():
    """Test different parallel processing strategies"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"🎯 PARALLEL PyMuPDF STRATEGIES BENCHMARK")
    print(f"📁 Testing {len(pdfs)} OSHA PDF files")
    print(f"🎯 Target: 2000 pages/sec (beat 700 baseline)")
    
    strategies = [
        ("Standard Threading", lambda pdfs: process_batch_parallel_extractors(pdfs, mp.cpu_count() * 2)),
        ("Aggressive Threading", lambda pdfs: process_batch_parallel_extractors(pdfs, mp.cpu_count() * 4)),
        ("Extreme Threading", lambda pdfs: process_batch_parallel_extractors(pdfs, mp.cpu_count() * 6)),
        ("Process Pool", process_batch_process_pool),
        ("Hybrid Batching", process_batch_hybrid),
    ]
    
    results = []
    
    for strategy_name, strategy_func in strategies:
        print(f"\n⚡ STRATEGY: {strategy_name}")
        
        try:
            strategy_results, total_time = strategy_func(pdfs)
            
            successful = [r for r in strategy_results if r.get("success")]
            total_pages = sum(r.get("pages", 0) for r in successful)
            total_chars = sum(r.get("text_len", 0) for r in successful)
            
            pages_per_sec = total_pages / total_time if total_time > 0 else 0
            
            print(f"✅ Results:")
            print(f"   Files: {len(successful)}/{len(strategy_results)}")
            print(f"   Pages: {total_pages}")
            print(f"   Characters: {total_chars:,}")
            print(f"   Time: {total_time:.3f}s")
            print(f"   📊 Speed: {pages_per_sec:.1f} pages/sec")
            
            # Performance analysis
            if pages_per_sec >= 2000:
                print(f"   🎉 EXTREME TARGET HIT!")
            elif pages_per_sec >= 700:
                print(f"   ✅ BASELINE BEATEN! ({pages_per_sec/700:.1f}x)")
                improvement = ((pages_per_sec - 700) / 700) * 100
                print(f"   📈 Improvement: +{improvement:.1f}%")
            else:
                print(f"   📊 Below baseline ({pages_per_sec/700:.1f}x of 700)")
            
            results.append({
                'strategy': strategy_name,
                'speed': pages_per_sec,
                'files': len(successful),
                'time': total_time,
                'chars': total_chars
            })
            
        except Exception as e:
            print(f"   ❌ {strategy_name} failed: {e}")
            results.append({
                'strategy': strategy_name,
                'speed': 0,
                'error': str(e)
            })
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"🏆 PARALLEL STRATEGIES RESULTS")
    print(f"=" * 70)
    
    successful_results = [r for r in results if r['speed'] > 0]
    successful_results.sort(key=lambda x: x['speed'], reverse=True)
    
    for i, result in enumerate(successful_results):
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1:2d}."
        strategy = result['strategy']
        speed = result['speed']
        vs_baseline = speed / 700 if speed > 0 else 0
        
        print(f"{rank} {strategy:20s}: {speed:8.1f} pages/sec ({vs_baseline:.1f}x baseline)")
    
    if successful_results:
        best = successful_results[0]
        print(f"\n🏆 CHAMPION: {best['strategy']}")
        print(f"🚀 Performance: {best['speed']:.1f} pages/sec")
        print(f"📊 vs 700 baseline: {best['speed']/700:.1f}x")
        print(f"📊 vs 2000 target: {best['speed']/2000:.1f}x")
        
        if best['speed'] >= 2000:
            print("🎉 EXTREME TARGET ACHIEVED!")
        elif best['speed'] >= 700:
            print("✅ BASELINE CRUSHED!")
            improvement = ((best['speed'] - 700) / 700) * 100
            print(f"📈 Total improvement: +{improvement:.1f}%")
        else:
            print("⚙️  Need more parallel optimization")
    
    return successful_results

if __name__ == "__main__":
    print("🔥 PARALLEL PyMuPDF PERFORMANCE TEST")
    print("⚡ Testing multiple parallel extraction strategies")
    
    try:
        results = benchmark_parallel_strategies()
        
        if results:
            champion = results[0]
            print(f"\n🏁 FINAL RECOMMENDATION: {champion['strategy']}")
            print(f"🚀 Peak Performance: {champion['speed']:.1f} pages/sec")
            
            if champion['speed'] >= 2000:
                print("🏆 MISSION ACCOMPLISHED - 2000+ pages/sec achieved!")
            elif champion['speed'] >= 700:
                print("🎯 BASELINE DEFEATED!")
            
    except Exception as e:
        print(f"❌ Parallel test failed: {e}")
        import traceback
        traceback.print_exc()