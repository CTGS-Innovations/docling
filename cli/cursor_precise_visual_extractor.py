#!/usr/bin/env python3
"""
Simple Visual Element Extractor - Extract accurate image files only.
Focus: Clean, precise image extraction for VLM processing.
"""

import sys
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
import time
import argparse

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF required. Install with: pip install PyMuPDF")
    sys.exit(1)

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_EGRET_LARGE
    from docling.datamodel.base_models import DocItemLabel
except ImportError:
    print("Error: Docling required. Install with: pip install docling")
    sys.exit(1)


class SimpleVisualExtractor:
    """Simple image extraction focused on accuracy."""
    
    def __init__(self, pdf_path: str, extract_types: List[str] = None):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Focus on formulas for now
        self.extract_types = set(extract_types or ["formulas"])
        
        # Output directory
        self.output_dir = Path("output") / self.pdf_path.stem
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear previous extractions
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        
        # Initialize Docling converter
        self.converter = self._setup_docling_converter()
        
        self.elements = []
        self.stats = {"formulas": 0, "total": 0}
    
    def _setup_docling_converter(self) -> DocumentConverter:
        """Setup Docling converter focused on formula detection."""
        try:
            pipeline_options = PdfPipelineOptions()
            
            # Use accurate layout model
                    pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_EGRET_LARGE
            
            # Higher resolution for better detection
                pipeline_options.images_scale = 2.0
            
            # Enable formula enrichment
                pipeline_options.do_formula_enrichment = True
            
            # Generate page images
            pipeline_options.generate_page_images = True
            
            # Lower confidence threshold for better formula detection
            pipeline_options.layout_options.confidence_threshold = 0.3
            
            # Keep empty clusters (important for formulas)
            pipeline_options.layout_options.keep_empty_clusters = True
            
            print("✅ Docling configured for formula extraction")
            
            converter = DocumentConverter(
                format_options={InputFormat.PDF: pipeline_options}
            )
            
            return converter
            
        except Exception as e:
            print(f"❌ Error setting up Docling: {e}")
            return DocumentConverter()
    
    def extract(self):
        """Extract formula images using Docling."""
        print(f"\n{'='*50}")
        print(f"🎯 FORMULA IMAGE EXTRACTION")
        print(f"📄 PDF: {self.pdf_path.name}")  
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*50}\n")
        
        start_time = time.time()
        
        # Use Docling to analyze the document
        print("📊 Running Docling analysis...")
        doc_result = self.converter.convert(self.pdf_path)
        
        # Open with PyMuPDF for image extraction
        pymupdf_doc = fitz.open(str(self.pdf_path))
        
        print(f"📖 Processing {len(pymupdf_doc)} pages...\n")
        
        # Extract formulas from each page
        for page_num in range(len(pymupdf_doc)):
            page = pymupdf_doc[page_num]
            page_elements = self._extract_formulas_from_page(doc_result, page, page_num + 1)
            
            if page_elements:
                print(f"📄 Page {page_num + 1}: Found {len(page_elements)} formulas")
                self.elements.extend(page_elements)
        
        pymupdf_doc.close()
        
        # Save results
        self._save_metadata()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*50}")
        print(f"✅ EXTRACTION COMPLETE in {elapsed:.2f}s")
        print(f"📊 Formulas extracted: {self.stats['formulas']}")
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*50}\n")
    
    def _extract_formulas_from_page(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract formulas from a single page using Docling."""
        formulas = []
        
        # Method 1: Extract from layout clusters
        layout_formulas = self._extract_from_layout_clusters(doc_result, page, page_num)
        formulas.extend(layout_formulas)
        
        # Method 2: Extract from enriched document elements
        enriched_formulas = self._extract_from_enriched_elements(doc_result, page, page_num)
        formulas.extend(enriched_formulas)
        
        # Remove duplicates
        formulas = self._deduplicate_formulas(formulas)
        
        self.stats["formulas"] += len(formulas)
        return formulas
    
    def _extract_from_layout_clusters(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract formulas from Docling's layout clusters."""
        formulas = []
        
        # Get layout clusters for this page
        page_layout = None
        if hasattr(doc_result, 'pages') and len(doc_result.pages) >= page_num:
            page_layout = doc_result.pages[page_num - 1]
        
        if not page_layout:
            return formulas
        
        # Get clusters from layout prediction
        clusters = []
        if hasattr(page_layout, 'predictions') and hasattr(page_layout.predictions, 'layout'):
            clusters = page_layout.predictions.layout.clusters
        elif hasattr(page_layout, 'clusters'):
            clusters = page_layout.clusters
        
        # Process formula clusters
        for cluster in clusters:
            if cluster.label == DocItemLabel.FORMULA:
            confidence = getattr(cluster, 'confidence', 1.0)
                if confidence >= 0.3:  # Lower threshold for better detection
                    formula = self._extract_formula_image(page, cluster, page_num, "layout")
                    if formula:
                        formulas.append(formula)
        
        return formulas
    
    def _extract_from_enriched_elements(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract formulas from Docling's enriched document elements."""
        formulas = []
        
        # Check document texts for enriched formulas
        if hasattr(doc_result, 'document') and hasattr(doc_result.document, 'texts'):
            for text_item in doc_result.document.texts:
                if (hasattr(text_item, 'label') and 
                    text_item.label == DocItemLabel.FORMULA and 
                    hasattr(text_item, 'prov') and text_item.prov):
                    
                    prov = text_item.prov[0]
                    if hasattr(prov, 'page_no') and prov.page_no == page_num:
                        formula = self._extract_enriched_formula_image(page, text_item, prov, page_num)
                        if formula:
                            formulas.append(formula)
        
        return formulas
    
    def _extract_formula_image(self, page, cluster, page_num: int, method: str) -> Dict:
        """Extract a formula image from a layout cluster."""
        try:
            bbox = cluster.bbox
            
            # Convert coordinates
            if hasattr(bbox, 'l'):  # Normalized coordinates
            page_width = page.rect.width
            page_height = page.rect.height
                x0 = bbox.l * page_width / 100.0
                y0 = bbox.t * page_height / 100.0
                x1 = bbox.r * page_width / 100.0
                y1 = bbox.b * page_height / 100.0
            else:  # Direct coordinates
                x0, y0 = bbox.x, bbox.y
                x1, y1 = x0 + bbox.w, y0 + bbox.h
            
            # Add generous padding for complete formula capture
            padding_x = 80
            padding_y = 30
            
            x0_final = max(0, x0 - padding_x)
            y0_final = max(0, y0 - padding_y)
            x1_final = min(page.rect.width, x1 + padding_x)
            y1_final = min(page.rect.height, y1 + padding_y)
            
            # Create element ID
            count = self.stats["formulas"] + 1
            element_id = f"FML_P{page_num:03d}_N{count:03d}"
            
            # Extract high-resolution image
            rect = fitz.Rect(x0_final, y0_final, x1_final, y1_final)
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            width = int(x1_final - x0_final)
            height = int(y1_final - y0_final)
            confidence = getattr(cluster, 'confidence', 1.0)
            
            print(f"  ✅ {element_id}: {width}x{height}px (confidence: {confidence:.2f})")
            
            return {
                "id": element_id,
                "type": "formula",
                "page": page_num,
                "bbox": [x0_final, y0_final, x1_final, y1_final],
                "width": width,
                "height": height,
                "confidence": confidence,
                "method": f"docling_{method}",
                "file": image_path.name
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract formula: {e}")
            return None
    
    def _extract_enriched_formula_image(self, page, text_item, prov, page_num: int) -> Dict:
        """Extract a formula image from enriched document element."""
        try:
            bbox = prov.bbox
            x0, y0 = bbox.l, bbox.t
            x1, y1 = bbox.r, bbox.b
            
            # Convert to page coordinates
            page_width = page.rect.width
            page_height = page.rect.height
            
            x0_scaled = x0 * page_width / 100.0
            y0_scaled = y0 * page_height / 100.0
            x1_scaled = x1 * page_width / 100.0
            y1_scaled = y1 * page_height / 100.0
            
            # Add generous padding
            padding_x = 80
            padding_y = 30
            
            x0_final = max(0, x0_scaled - padding_x)
            y0_final = max(0, y0_scaled - padding_y)
            x1_final = min(page_width, x1_scaled + padding_x)
            y1_final = min(page_height, y1_scaled + padding_y)
            
            # Create element ID
            count = self.stats["formulas"] + 1
            element_id = f"FML_P{page_num:03d}_N{count:03d}"
            
            # Extract high-resolution image
            rect = fitz.Rect(x0_final, y0_final, x1_final, y1_final)
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            width = int(x1_final - x0_final)
            height = int(y1_final - y0_final)
            
            # Get enriched text if available
            enriched_text = ""
            if hasattr(text_item, 'text'):
                enriched_text = text_item.text
            
            print(f"  ✅ {element_id}: enriched formula {width}x{height}px")
            
            return {
                "id": element_id,
                "type": "formula",
                "page": page_num,
                "bbox": [x0_final, y0_final, x1_final, y1_final],
                "width": width,
                "height": height,
                                "confidence": 0.9,
                "method": "docling_enriched",
                "file": image_path.name,
                "enriched_text": enriched_text
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract enriched formula: {e}")
            return None
    
    def _deduplicate_formulas(self, formulas: List[Dict]) -> List[Dict]:
        """Remove duplicate formula detections."""
        if not formulas:
            return formulas
        
        # Sort by confidence descending
        formulas_sorted = sorted(formulas, key=lambda x: x.get("confidence", 0), reverse=True)
        
        deduplicated = []
        for current_formula in formulas_sorted:
            current_bbox = current_formula["bbox"]
            is_duplicate = False
            
            # Check against already kept formulas
            for kept_formula in deduplicated:
                kept_bbox = kept_formula["bbox"]
                
                # Calculate overlap
                overlap_ratio = self._calculate_bbox_overlap(current_bbox, kept_bbox)
                
                # If significant overlap, consider duplicate
                if overlap_ratio > 0.7:
                    is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(current_formula)
            
        return deduplicated
    
    def _calculate_bbox_overlap(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate overlap ratio between two bounding boxes."""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Calculate intersection
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        if x_overlap == 0 or y_overlap == 0:
            return 0.0
        
        intersection_area = x_overlap * y_overlap
        
        # Calculate area of each bbox
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        
        # Return intersection over minimum area
        min_area = min(area1, area2)
        return intersection_area / min_area if min_area > 0 else 0.0
    
    def _save_metadata(self):
        """Save extraction metadata."""
        metadata = {
            "source": self.pdf_path.name,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "elements": self.elements,
            "extraction_method": "simple_formula_extraction"
        }
        
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📄 Metadata saved: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple Visual Element Extractor - Extract formula images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract formulas (default)
  python cursor_precise_visual_extractor.py document.pdf
  
  # Extract formulas only
  python cursor_precise_visual_extractor.py document.pdf --formulas
        """
    )
    
    parser.add_argument("pdf_file", help="Path to the PDF file to process")
    parser.add_argument("--formulas", action="store_true", help="Extract mathematical formulas")
    
    args = parser.parse_args()
    
    # Determine what to extract
    extract_types = []
    if args.formulas:
        extract_types.append("formulas")
    if not extract_types:
        extract_types = ["formulas"]  # Default to formulas
    
    try:
        extractor = SimpleVisualExtractor(args.pdf_file, extract_types)
        extractor.extract()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()