#!/usr/bin/env python3
"""
Direct test of MVP-Hyper extraction code in our environment
Copy MVP-Hyper's exact extraction logic to eliminate environment variables
"""

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib
from typing import Dict, Any, Optional

try:
    import fitz
    HAS_PYMUPDF = True
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    HAS_PYMUPDF = False
    print("❌ No PyMuPDF")
    exit(1)

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

class MVPHyperDirectTest:
    """MVP-Hyper's exact extraction code running in our environment"""
    
    def __init__(self, num_workers=16):
        self.num_workers = num_workers
        self.cache = {}
        self.cache_size = 512 * 1024 * 1024  # 512MB
        self.current_cache_size = 0
    
    def _get_cache_key(self, file_path: Path) -> str:
        """MVP-Hyper's exact cache key generation"""
        if HAS_XXHASH:
            h = xxhash.xxh64()
        else:
            h = hashlib.blake2b()
        
        key_string = f"{file_path}:{file_path.stat().st_mtime}:{file_path.stat().st_size}"
        h.update(key_string.encode())
        return h.hexdigest()
    
    def _extract_sequential_safe(self, doc, max_pages=None) -> str:
        """MVP-Hyper's exact sequential extraction method"""
        texts = []
        pages_to_process = min(len(doc), max_pages) if max_pages else len(doc)
        
        for i in range(pages_to_process):
            try:
                page = doc[i]
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                texts.append(text or "")
            except Exception as e:
                texts.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
        return '\n'.join(texts)
    
    def _extract_basic_text(self, doc) -> str:
        """MVP-Hyper's exact basic text extraction fallback"""
        texts = []
        for i in range(min(len(doc), 100)):  # Limit to first 100 pages for speed
            try:
                page = doc[i]
                text = page.get_text()  # Simplest method
                texts.append(text or "")
            except:
                texts.append(f"[Page {i+1} failed]")
        return '\n'.join(texts)
    
    def _extract_pdf(self, file_path: Path, start_time: float, cache_key: str):
        """MVP-Hyper's exact PDF extraction method"""
        if not HAS_PYMUPDF:
            return self._fail_fast_pdf(file_path, start_time, "PyMuPDF not available")
        
        try:
            doc = fitz.open(str(file_path))
            
            try:
                page_count = len(doc)
                
                if page_count == 0:
                    doc.close()
                    return self._fail_fast_pdf(file_path, start_time, "PDF has 0 pages")
                
                # MVP-Hyper's page limits
                max_pages_config = 999999
                skip_if_over = 100  # MVP-Hyper's 100-page limit
                
                if page_count > skip_if_over:
                    doc.close()
                    return self._fail_fast_pdf(file_path, start_time, f"PDF has {page_count} pages (limit: {skip_if_over})")
                
                pages_to_extract = min(page_count, max_pages_config)
                
                try:
                    text = self._extract_sequential_safe(doc, pages_to_extract)
                    
                    if pages_to_extract < page_count:
                        text += f"\n\n[Note: Only extracted first {pages_to_extract} of {page_count} pages for speed]"
                except Exception as text_error:
                    try:
                        text = self._extract_basic_text(doc)
                    except:
                        doc.close()
                        return self._fail_fast_pdf(file_path, start_time, f"Text extraction failed: {str(text_error)}")
                
                try:
                    metadata = {
                        "filename": file_path.name,
                        "pages": page_count,
                        "size_bytes": file_path.stat().st_size,
                        "format": "PDF",
                    }
                except Exception:
                    metadata = {
                        "filename": file_path.name,
                        "format": "PDF",
                        "pages": page_count,
                        "size_bytes": file_path.stat().st_size
                    }
                
                doc.close()
                
                extraction_time = time.perf_counter() - start_time
                pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
                
                result = {
                    "file_path": str(file_path),
                    "success": True,
                    "text": text or "[No text extracted]",
                    "page_count": page_count,
                    "extraction_time": extraction_time,
                    "pages_per_second": pages_per_second,
                    "metadata": metadata
                }
                
                if len(text or "") < 10_000_000:
                    self._cache_result(cache_key, result)
                
                return result
                
            except Exception as process_error:
                try:
                    doc.close()
                except:
                    pass
                return self._fail_fast_pdf(file_path, start_time, f"PDF processing error: {str(process_error)}")
                
        except Exception as open_error:
            return self._fail_fast_pdf(file_path, start_time, f"PDF open error: {str(open_error)}")
    
    def _fail_fast_pdf(self, file_path: Path, start_time: float, error_msg: str):
        """MVP-Hyper's exact fail fast method"""
        extraction_time = time.perf_counter() - start_time
        return {
            "file_path": str(file_path),
            "success": False,
            "text": "",
            "page_count": 0,
            "extraction_time": extraction_time,
            "pages_per_second": 0,
            "metadata": {"filename": file_path.name, "format": "PDF", "error": "fail_fast"},
            "error": error_msg
        }
    
    def _cache_result(self, cache_key: str, result):
        """MVP-Hyper's exact caching method"""
        cache_data = {
            'text': result["text"],
            'pages': result["page_count"],
            'metadata': result["metadata"]
        }
        
        data_size = len(result["text"])
        if self.current_cache_size + data_size > self.cache_size:
            to_remove = list(self.cache.keys())[:len(self.cache)//4]
            for key in to_remove:
                del self.cache[key]
            self.current_cache_size *= 0.75
        
        self.cache[cache_key] = cache_data
        self.current_cache_size += data_size
    
    def extract_document_ultrafast(self, file_path: Path):
        """MVP-Hyper's exact document extraction method"""
        start_time = time.perf_counter()
        file_ext = file_path.suffix.lower()
        
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return {
                "file_path": str(file_path),
                "success": True,
                "text": cached['text'],
                "page_count": cached['pages'],
                "extraction_time": 0.001,
                "pages_per_second": cached['pages'] / 0.001,
                "metadata": cached['metadata']
            }
        
        if file_ext == '.pdf':
            return self._extract_pdf(file_path, start_time, cache_key)
        else:
            return self._fail_fast_pdf(file_path, start_time, f"Unsupported file type: {file_ext}")
    
    def process_batch(self, file_paths):
        """MVP-Hyper's exact batch processing method"""
        print(f"Thread processing {len(file_paths)} files with {self.num_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for file_path in file_paths:
                future = executor.submit(self.extract_document_ultrafast, file_path)
                futures.append(future)
            
            results = []
            for future in futures:
                results.append(future.result())
        
        return results

def find_osha_pdfs(limit=100):
    """Find OSHA PDF files"""
    osha_dir = Path("../cli/data_osha")
    
    if not osha_dir.exists():
        print(f"❌ OSHA directory not found: {osha_dir}")
        return []
    
    pdfs = []
    for pdf in osha_dir.glob("*.pdf"):
        pdfs.append(pdf)
        if len(pdfs) >= limit:
            break
    
    return sorted(pdfs)

def test_mvp_hyper_direct():
    """Test MVP-Hyper's exact code in our environment"""
    
    pdfs = find_osha_pdfs(100)
    if not pdfs:
        print("❌ No OSHA PDFs found")
        return
    
    print(f"🚀 MVP-HYPER DIRECT TEST (Our Environment)")
    print(f"📁 Found {len(pdfs)} OSHA PDF files")
    
    # Test with different worker counts like MVP-Hyper
    for workers in [1, 16]:
        print(f"\n⚡ TESTING WITH {workers} WORKERS")
        
        extractor = MVPHyperDirectTest(num_workers=workers)
        
        start_time = time.perf_counter()
        results = extractor.process_batch(pdfs)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        successful = [r for r in results if r.get("success")]
        total_pages = sum(r.get("page_count", 0) for r in successful)
        
        pages_per_sec = total_pages / total_time if total_time > 0 else 0
        
        print(f"✅ {workers} Workers Results:")
        print(f"   Files: {len(successful)}/{len(results)}")
        print(f"   Pages: {total_pages}")
        print(f"   Time: {total_time:.2f}s")
        print(f"   📊 Current: {pages_per_sec:.1f} pages/sec")
        
        # Compare to MVP-Hyper baseline
        mvp_hyper_baseline = 708  # Average from user's tests
        if abs(pages_per_sec - mvp_hyper_baseline) < 50:
            print(f"   ✅ MATCHES MVP-Hyper performance!")
        else:
            gap = mvp_hyper_baseline - pages_per_sec
            print(f"   Gap: {gap:+.1f} pages/sec vs MVP-Hyper")

if __name__ == "__main__":
    test_mvp_hyper_direct()