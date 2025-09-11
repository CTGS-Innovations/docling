#!/usr/bin/env python3
"""
PDF Complexity Analyzer
========================

Rapidly analyzes PDF documents to determine optimal processing strategy:
- Text-heavy PDFs → Fast text extraction path (100+ pages/sec)
- Visual-heavy PDFs → Full VLM pipeline path
- Mixed content → Hybrid processing with queued visuals

This classifier runs in <100ms to make routing decisions.
"""

import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

try:
    import pymupdf as fitz  # PyMuPDF for fast PDF analysis
except ImportError:
    try:
        import fitz  # Alternative import name
    except ImportError:
        fitz = None

try:
    from pypdfium2 import PdfDocument
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False


class ProcessingStrategy(Enum):
    """Processing strategy based on PDF complexity analysis."""
    FAST_TEXT = "fast_text"          # Text-heavy: fast extraction
    FULL_VLM = "full_vlm"            # Visual-heavy: full VLM pipeline  
    HYBRID = "hybrid"                # Mixed: fast text + queued visuals


@dataclass
class ComplexityMetrics:
    """Metrics for PDF complexity analysis."""
    total_pages: int
    text_density: float              # 0-1: ratio of text area to page area
    image_count: int
    image_density: float             # 0-1: ratio of image area to page area
    table_indicators: int            # Heuristic count of potential tables
    formula_indicators: int          # Heuristic count of potential formulas
    scanned_page_ratio: float        # 0-1: ratio of likely scanned pages
    text_extractable: bool           # Whether text can be extracted directly
    processing_strategy: ProcessingStrategy
    confidence: float                # 0-1: confidence in strategy choice
    analysis_time: float             # Time taken for analysis (seconds)


@dataclass
class VisualElement:
    """Represents a visual element requiring enhanced processing."""
    page_num: int
    element_type: str                # "image", "table", "formula", "complex_layout"
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    priority: int                    # 1-5: processing priority
    estimated_processing_time: float # Estimated GPU processing time


class PDFComplexityAnalyzer:
    """Fast PDF complexity analyzer for processing strategy decisions."""
    
    def __init__(self):
        self.text_density_threshold = 0.7    # >70% text → fast path
        self.image_density_threshold = 0.3   # >30% images → VLM path
        self.scanned_threshold = 0.5         # >50% scanned → VLM path
        
    def analyze(self, pdf_path: Path) -> ComplexityMetrics:
        """
        Analyze PDF complexity and determine optimal processing strategy.
        
        Target: Complete analysis in <100ms for routing decisions.
        """
        start_time = time.time()
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            # Use pypdfium2 first for consistency with text extractor
            if PYPDFIUM2_AVAILABLE:
                metrics = self._analyze_with_pypdfium2(pdf_path)
            elif fitz is not None:
                metrics = self._analyze_with_pymupdf(pdf_path)
            else:
                # Fallback to basic file analysis
                metrics = self._analyze_basic(pdf_path)
                
        except Exception as e:
            print(f"Warning: PDF analysis failed for {pdf_path}: {e}")
            # Default to safe VLM processing
            metrics = ComplexityMetrics(
                total_pages=1,
                text_density=0.0,
                image_count=0,
                image_density=0.0,
                table_indicators=0,
                formula_indicators=0,
                scanned_page_ratio=1.0,
                text_extractable=False,
                processing_strategy=ProcessingStrategy.FULL_VLM,
                confidence=0.5,
                analysis_time=0.0
            )
        
        analysis_time = time.time() - start_time
        metrics.analysis_time = analysis_time
        
        # Determine processing strategy
        metrics.processing_strategy, metrics.confidence = self._determine_strategy(metrics)
        
        return metrics
    
    def _analyze_with_pymupdf(self, pdf_path: Path) -> ComplexityMetrics:
        """Fast analysis using PyMuPDF (recommended)."""
        doc = fitz.open(str(pdf_path))
        
        total_pages = len(doc)
        total_text_area = 0
        total_image_area = 0  
        total_page_area = 0
        image_count = 0
        table_indicators = 0
        formula_indicators = 0
        scanned_pages = 0
        text_extractable = True
        
        # Analyze up to first 10 pages for speed (sample-based analysis)
        sample_pages = min(10, total_pages)
        
        for page_num in range(sample_pages):
            page = doc[page_num]
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height
            total_page_area += page_area
            
            # Text analysis
            text = page.get_text()
            text_blocks = page.get_text("dict")["blocks"]
            
            # Calculate text coverage
            text_area = 0
            for block in text_blocks:
                if "lines" in block:  # Text block
                    bbox = block["bbox"]
                    block_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    text_area += block_area
            
            total_text_area += text_area
            
            # Image analysis - detect both images and drawings/graphics
            images = page.get_images()
            image_count += len(images)
            
            # Also check for drawings/graphics (charts, maps, etc.)
            drawings = page.get_drawings()
            if drawings:
                image_count += len(drawings)  # Count drawings as visual elements
            
            # Estimate image area
            for img in images:
                try:
                    bbox = page.get_image_bbox(img)
                    img_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    total_image_area += img_area
                except:
                    # Fallback estimate
                    total_image_area += page_area * 0.1
            
            # Estimate drawing area (for charts, graphics)
            for drawing in drawings:
                # Drawings don't have easy bbox access, estimate based on complexity
                total_image_area += page_area * 0.15  # Assume 15% of page per drawing
            
            # Heuristic indicators
            if len(text) < 100:  # Very little text
                scanned_pages += 1
                
            # Table indicators (simple heuristics)
            if "|" in text or "┌" in text or "├" in text:
                table_indicators += 1
                
            # Formula indicators
            if any(char in text for char in ["∑", "∫", "√", "≤", "≥", "α", "β", "γ"]):
                formula_indicators += 1
            
            # Visual content indicators (charts, maps, figures)
            if any(pattern in text.lower() for pattern in ["figure", "chart", "graph", "map", "diagram"]):
                # Treat as visual content that needs processing
                image_count += 1
                
            # Check if text is actually extractable
            if len(text.strip()) == 0 and len(images) > 0:
                text_extractable = False
        
        doc.close()
        
        # Calculate ratios (extrapolate from sample)
        if total_page_area > 0:
            text_density = total_text_area / total_page_area
            image_density = total_image_area / total_page_area
        else:
            text_density = 0.0
            image_density = 0.0
            
        scanned_page_ratio = scanned_pages / sample_pages if sample_pages > 0 else 0.0
        
        # Scale counts to full document
        if sample_pages < total_pages:
            scale_factor = total_pages / sample_pages
            image_count = int(image_count * scale_factor)
            table_indicators = int(table_indicators * scale_factor)
            formula_indicators = int(formula_indicators * scale_factor)
        
        return ComplexityMetrics(
            total_pages=total_pages,
            text_density=text_density,
            image_count=image_count,
            image_density=image_density,
            table_indicators=table_indicators,
            formula_indicators=formula_indicators,
            scanned_page_ratio=scanned_page_ratio,
            text_extractable=text_extractable,
            processing_strategy=ProcessingStrategy.FAST_TEXT,  # Will be determined later
            confidence=0.0,  # Will be calculated later
            analysis_time=0.0
        )
    
    def _analyze_with_pypdfium2(self, pdf_path: Path) -> ComplexityMetrics:
        """Enhanced analysis using pypdfium2 (same as text extractor)."""
        doc = PdfDocument(str(pdf_path))
        total_pages = len(doc)
        
        # Enhanced analysis - check for visual indicators
        sample_pages = min(10, total_pages)
        total_text_length = 0
        image_count = 0
        table_indicators = 0
        formula_indicators = 0
        
        for i in range(sample_pages):
            page = doc[i]
            text = page.get_textpage().get_text_range()
            total_text_length += len(text.strip())
            
            # Check for visual content indicators
            text_lower = text.lower()
            if any(pattern in text_lower for pattern in ["figure", "chart", "graph", "map", "diagram"]):
                image_count += 1
            
            # Table indicators
            if "|" in text or "┌" in text or "├" in text:
                table_indicators += 1
                
            # Formula indicators
            if any(char in text for char in ["∑", "∫", "√", "≤", "≥", "α", "β", "γ"]):
                formula_indicators += 1
        
        # Scale counts to full document if we sampled
        if sample_pages < total_pages:
            scale_factor = total_pages / sample_pages
            image_count = int(image_count * scale_factor)
            table_indicators = int(table_indicators * scale_factor)
            formula_indicators = int(formula_indicators * scale_factor)
        
        # Basic heuristics
        text_extractable = total_text_length > 50
        text_density = min(1.0, total_text_length / (sample_pages * 1000))  # Rough estimate
        image_density = 0.1 if image_count > 0 else 0.0  # Estimate if we found visual indicators
        
        return ComplexityMetrics(
            total_pages=total_pages,
            text_density=text_density,
            image_count=image_count,
            image_density=image_density,
            table_indicators=table_indicators,
            formula_indicators=formula_indicators,
            scanned_page_ratio=0.0 if text_extractable else 1.0,
            text_extractable=text_extractable,
            processing_strategy=ProcessingStrategy.FAST_TEXT,  # Will be determined later
            confidence=0.8,  # Higher confidence with better analysis
            analysis_time=0.0
        )
    
    def _analyze_basic(self, pdf_path: Path) -> ComplexityMetrics:
        """Basic file-based analysis when no PDF libraries available."""
        file_size = pdf_path.stat().st_size
        
        # Very rough heuristics based on file size
        estimated_pages = max(1, file_size // (50 * 1024))  # ~50KB per page estimate
        
        # Conservative defaults - assume might need VLM
        return ComplexityMetrics(
            total_pages=estimated_pages,
            text_density=0.5,  # Unknown, assume mixed
            image_count=0,
            image_density=0.3,  # Assume some images
            table_indicators=0,
            formula_indicators=0,
            scanned_page_ratio=0.3,  # Assume some scanned content
            text_extractable=True,
            processing_strategy=ProcessingStrategy.HYBRID,
            confidence=0.3,  # Low confidence
            analysis_time=0.0
        )
    
    def _determine_strategy(self, metrics: ComplexityMetrics) -> Tuple[ProcessingStrategy, float]:
        """
        Determine optimal processing strategy based on metrics.
        
        Returns (strategy, confidence_score)
        """
        
        # Force HYBRID if any visual elements detected (charts, maps, figures)
        # This ensures we get visual descriptions even in text-heavy documents
        if (metrics.image_count > 0 or 
            metrics.table_indicators > 0 or 
            metrics.formula_indicators > 0):
            return ProcessingStrategy.HYBRID, 0.85
        
        # High confidence VLM path for visually complex documents  
        if (metrics.scanned_page_ratio > self.scanned_threshold or
            metrics.image_density > self.image_density_threshold or
            not metrics.text_extractable):
            return ProcessingStrategy.FULL_VLM, 0.85
        
        # Fast text path only for pure text documents with no visual elements
        if (metrics.text_density > self.text_density_threshold and 
            metrics.image_density < 0.05 and 
            metrics.scanned_page_ratio < 0.1 and
            metrics.text_extractable and
            metrics.image_count == 0 and
            metrics.table_indicators == 0):
            return ProcessingStrategy.FAST_TEXT, 0.9
        
        # Default to hybrid for safety
        return ProcessingStrategy.HYBRID, 0.7
    
    def identify_visual_elements(self, pdf_path: Path, metrics: ComplexityMetrics) -> List[VisualElement]:
        """
        Identify specific visual elements that need enhanced processing.
        
        Used for HYBRID strategy to queue specific elements.
        """
        visual_elements = []
        
        if not fitz:
            return visual_elements
        
        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(min(doc.page_count, 20)):  # Limit for performance
                page = doc[page_num]
                
                # Find images
                images = page.get_images()
                for img in images:
                    try:
                        bbox = page.get_image_bbox(img)
                        visual_elements.append(VisualElement(
                            page_num=page_num,
                            element_type="image",
                            bbox=bbox,
                            priority=3,
                            estimated_processing_time=2.0
                        ))
                    except:
                        continue
                
                # Heuristic table detection
                text = page.get_text()
                if "|" in text or "┌" in text:
                    # Rough table area (would need better detection in practice)
                    page_rect = page.rect
                    visual_elements.append(VisualElement(
                        page_num=page_num,
                        element_type="table",
                        bbox=(0, 0, page_rect.width, page_rect.height),
                        priority=4,
                        estimated_processing_time=5.0
                    ))
            
            doc.close()
            
        except Exception as e:
            print(f"Warning: Visual element detection failed: {e}")
        
        return visual_elements
    
    def save_analysis(self, pdf_path: Path, metrics: ComplexityMetrics, output_path: Optional[Path] = None):
        """Save analysis results for debugging and optimization."""
        if output_path is None:
            output_path = pdf_path.parent / f"{pdf_path.stem}_complexity_analysis.json"
        
        analysis_data = {
            "pdf_path": str(pdf_path),
            "analysis_timestamp": time.time(),
            "metrics": {
                "total_pages": metrics.total_pages,
                "text_density": metrics.text_density,
                "image_count": metrics.image_count,
                "image_density": metrics.image_density,
                "table_indicators": metrics.table_indicators,
                "formula_indicators": metrics.formula_indicators,
                "scanned_page_ratio": metrics.scanned_page_ratio,
                "text_extractable": metrics.text_extractable,
                "processing_strategy": metrics.processing_strategy.value,
                "confidence": metrics.confidence,
                "analysis_time": metrics.analysis_time
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)


def main():
    """Test the PDF complexity analyzer."""
    analyzer = PDFComplexityAnalyzer()
    
    # Find test PDFs
    data_dir = Path('/home/corey/projects/docling/cli/data')
    pdf_files = list(data_dir.glob('**/*.pdf'))
    
    if not pdf_files:
        print("No PDF files found in data directory")
        return
    
    print("🔍 PDF COMPLEXITY ANALYSIS")
    print("=" * 50)
    
    for pdf_file in pdf_files[:5]:  # Test first 5 PDFs
        print(f"\n📄 Analyzing: {pdf_file.name}")
        
        try:
            metrics = analyzer.analyze(pdf_file)
            
            print(f"   📊 Pages: {metrics.total_pages}")
            print(f"   📝 Text density: {metrics.text_density:.2f}")
            print(f"   🖼️  Images: {metrics.image_count} (density: {metrics.image_density:.2f})")
            print(f"   📋 Tables: {metrics.table_indicators}")
            print(f"   🔢 Formulas: {metrics.formula_indicators}")
            print(f"   📸 Scanned ratio: {metrics.scanned_page_ratio:.2f}")
            print(f"   ⚡ Strategy: {metrics.processing_strategy.value}")
            print(f"   🎯 Confidence: {metrics.confidence:.2f}")
            print(f"   ⏱️  Analysis time: {metrics.analysis_time:.3f}s")
            
            # Always try to identify visual elements for debugging
            visual_elements = analyzer.identify_visual_elements(pdf_file, metrics)
            print(f"   🎨 Visual elements: {len(visual_elements)}")
            
            if metrics.processing_strategy == ProcessingStrategy.HYBRID and visual_elements:
                for i, element in enumerate(visual_elements[:3]):  # Show first 3
                    print(f"      {i+1}. {element.element_type.value} on page {element.page_num + 1}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Analysis complete")


if __name__ == "__main__":
    main()