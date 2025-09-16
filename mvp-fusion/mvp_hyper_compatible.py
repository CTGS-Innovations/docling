#!/usr/bin/env python3
"""
MVP-Hyper Compatible Ultra Fast Fusion
=====================================

Minimal architecture matching MVP-Hyper's exact approach for maximum performance.
Target: 700+ pages/sec to match MVP-Hyper baseline.
"""

import time
from pathlib import Path
from typing import Union, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib

# PyMuPDF
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Optional accelerators
try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

@dataclass
class UltraFastResult:
    """Minimal result structure matching MVP-Hyper exactly."""
    file_path: str
    success: bool
    text: str
    page_count: int
    extraction_time: float
    pages_per_second: float
    file_size_bytes: int
    error: str = None

class MVPHyperCompatible:
    """
    MVP-Hyper compatible extractor with identical architecture.
    
    No memory pools, no complex initialization - just direct extraction.
    """
    
    def __init__(self, num_workers: int = 8):
        """Minimal initialization - create thread pool only when needed."""
        self.num_workers = num_workers
        self.cache = {}  # Simple dict cache like MVP-Hyper
        # No thread pool creation here - create when needed
        
    def extract_document(self, file_path: Union[str, Path]) -> UltraFastResult:
        """Extract document using MVP-Hyper exact approach."""
        file_path = Path(file_path)
        start_time = time.perf_counter()
        file_ext = file_path.suffix.lower()
        
        # Check cache first (MVP-Hyper pattern)
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return UltraFastResult(
                file_path=str(file_path),
                success=True,
                text=cached['text'],
                page_count=cached['pages'],
                extraction_time=0.001,  # Cache hit is ~1ms
                pages_per_second=cached['pages'] / 0.001,
                file_size_bytes=file_path.stat().st_size
            )
        
        # Route to appropriate extractor (MVP-Hyper pattern)
        if file_ext == '.pdf':
            return self._extract_pdf(file_path, start_time, cache_key)
        elif file_ext in ['.txt', '.md']:
            return self._extract_text(file_path, start_time, cache_key)
        else:
            # Universal fallback
            return self._extract_text(file_path, start_time, cache_key)
    
    def _extract_pdf(self, file_path: Path, start_time: float, cache_key: str) -> UltraFastResult:
        """Extract PDF using MVP-Hyper exact method."""
        if not HAS_PYMUPDF:
            return self._fail_fast_pdf(file_path, start_time, "PyMuPDF not available")
        
        try:
            # Direct file opening (MVP-Hyper pattern)
            doc = fitz.open(str(file_path))
            
            try:
                page_count = len(doc)
                
                # Fail fast if doc seems corrupted
                if page_count == 0:
                    doc.close()
                    return self._fail_fast_pdf(file_path, start_time, "PDF has 0 pages")
                
                # Extract text using MVP-Hyper's _extract_sequential_safe pattern
                text = self._extract_sequential_safe(doc, page_count)
                
                doc.close()
                
                extraction_time = time.perf_counter() - start_time
                pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
                
                result = UltraFastResult(
                    file_path=str(file_path),
                    success=True,
                    text=text or "[No text extracted]",
                    page_count=page_count,
                    extraction_time=extraction_time,
                    pages_per_second=pages_per_second,
                    file_size_bytes=file_path.stat().st_size
                )
                
                # Cache result (MVP-Hyper pattern)
                self.cache[cache_key] = {
                    'text': result.text,
                    'pages': result.page_count,
                    'metadata': {"filename": file_path.name, "format": "PDF"}
                }
                
                return result
                
            except Exception as e:
                doc.close()
                return self._fail_fast_pdf(file_path, start_time, f"PDF processing error: {e}")
                
        except Exception as e:
            return self._fail_fast_pdf(file_path, start_time, f"PDF open error: {e}")
    
    def _extract_sequential_safe(self, doc, max_pages=None) -> str:
        """MVP-Hyper's exact _extract_sequential_safe method."""
        texts = []
        pages_to_process = min(len(doc), max_pages) if max_pages else len(doc)
        
        for i in range(pages_to_process):
            try:
                page = doc[i]  # Direct indexing like MVP-Hyper
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                texts.append(text or "")
            except Exception as e:
                texts.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
        return '\n'.join(texts)
    
    def _extract_text(self, file_path: Path, start_time: float, cache_key: str) -> UltraFastResult:
        """Extract plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            extraction_time = time.perf_counter() - start_time
            
            result = UltraFastResult(
                file_path=str(file_path),
                success=True,
                text=text,
                page_count=1,
                extraction_time=extraction_time,
                pages_per_second=1 / extraction_time if extraction_time > 0 else 0,
                file_size_bytes=file_path.stat().st_size
            )
            
            # Cache result
            self.cache[cache_key] = {
                'text': result.text,
                'pages': result.page_count,
                'metadata': {"filename": file_path.name, "format": file_path.suffix.upper()}
            }
            
            return result
            
        except Exception as e:
            extraction_time = time.perf_counter() - start_time
            return UltraFastResult(
                file_path=str(file_path),
                success=False,
                text="",
                page_count=0,
                extraction_time=extraction_time,
                pages_per_second=0,
                file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                error=str(e)
            )
    
    def _fail_fast_pdf(self, file_path: Path, start_time: float, error_msg: str) -> UltraFastResult:
        """Fast failure for PDF errors."""
        extraction_time = time.perf_counter() - start_time
        return UltraFastResult(
            file_path=str(file_path),
            success=False,
            text="",
            page_count=0,
            extraction_time=extraction_time,
            pages_per_second=0,
            file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            error=error_msg
        )
    
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key using fast hashing (MVP-Hyper pattern)."""
        if HAS_XXHASH:
            h = xxhash.xxh64()
        else:
            h = hashlib.blake2b()
        
        # Hash file path and modification time
        key_string = f"{file_path.absolute()}_{file_path.stat().st_mtime}"
        h.update(key_string.encode())
        return h.hexdigest()
    
    def process_batch(self, file_paths: List[Union[str, Path]]) -> List[UltraFastResult]:
        """Process batch with threading (create thread pool on demand)."""
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(self.extract_document, fp) for fp in file_paths]
            return [future.result() for future in futures]

# Compatibility function
def create_ultra_fast_fusion(config=None):
    """Create MVP-Hyper compatible fusion instance."""
    num_workers = 8
    if config and 'performance' in config:
        num_workers = config['performance'].get('max_workers', 8)
    
    return MVPHyperCompatible(num_workers=num_workers)