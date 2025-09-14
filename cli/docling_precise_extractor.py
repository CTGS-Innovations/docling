#!/usr/bin/env python3
"""
Docling-Powered Precise Visual Element Extractor
Extract formulas, tables, charts, and figures using Docling's advanced layout detection.
"""

import os
# Disable GPU usage before importing any ML libraries
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
from pathlib import Path
from typing import List, Dict, Optional
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


class DoclingPreciseExtractor:
    """Precise visual element extraction using Docling's professional layout detection."""
    
    def __init__(self, pdf_path: str, extract_types: List[str] = None):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # What to extract
        self.extract_types = set(extract_types or ["formulas", "tables", "charts", "figures"])
        
        # Output directory
        self.output_dir = Path("output") / self.pdf_path.stem
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear previous extractions
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        
        # Initialize Docling converter
        self.converter = self._setup_docling_converter()
        
        self.elements = []
        self.stats = {
            "formulas": 0,
            "tables": 0,
            "charts": 0,
            "figures": 0,
            "total": 0
        }
    
    def _setup_docling_converter(self) -> DocumentConverter:
        """Setup Docling converter with optimal configuration for visual extraction."""
        try:
            print("🤖 Configuring Docling with EGRET-LARGE model (CPU mode)...")
            
            pipeline_options = PdfPipelineOptions()
            
            # Use the most accurate layout model
            pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_EGRET_LARGE
            
            # Higher resolution for better detection
            pipeline_options.images_scale = 2.0
            
            # Enable formula enrichment
            pipeline_options.do_formula_enrichment = True
            
            # Generate page images
            pipeline_options.generate_page_images = True
            
            # Lower confidence threshold for better recall
            pipeline_options.layout_options.confidence_threshold = 0.3
            
            # Keep empty clusters
            pipeline_options.layout_options.keep_empty_clusters = True
            
            print("✅ Docling configured successfully (CPU mode)")
            
            converter = DocumentConverter(
                format_options={InputFormat.PDF: pipeline_options}
            )
            
            return converter
            
        except Exception as e:
            print(f"⚠️ Error configuring Docling: {e}")
            print("📌 Falling back to basic configuration...")
            return DocumentConverter()
    
    def extract(self):
        """Main extraction using Docling's layout detection."""
        print(f"\n{'='*60}")
        print(f"🎯 DOCLING PRECISE VISUAL EXTRACTION")
        print(f"📄 PDF: {self.pdf_path.name}")  
        print(f"📁 Output: {self.output_dir}")
        print(f"🔍 Extracting: {', '.join(sorted(self.extract_types))}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Use Docling to analyze the document
        print("📊 Running Docling layout analysis...")
        doc_result = self.converter.convert(self.pdf_path)
        
        # Open with PyMuPDF for image extraction
        pymupdf_doc = fitz.open(str(self.pdf_path))
        
        print(f"📖 Processing {len(pymupdf_doc)} pages...\n")
        
        # Extract elements from each page
        for page_num in range(len(pymupdf_doc)):
            page = pymupdf_doc[page_num]
            page_elements = self._extract_page_elements(doc_result, page, page_num + 1)
            
            if page_elements:
                print(f"📄 Page {page_num + 1}: Found {len(page_elements)} elements")
                self.elements.extend(page_elements)
        
        pymupdf_doc.close()
        
        # Save results
        self._save_metadata()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ EXTRACTION COMPLETE in {elapsed:.2f}s")
        print(f"📊 Elements extracted:")
        for elem_type, count in self.stats.items():
            if elem_type != "total" and count > 0:
                print(f"  - {elem_type}: {count}")
        print(f"  TOTAL: {self.stats['total']}")
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def _extract_page_elements(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract all visual elements from a page using Docling."""
        page_elements = []
        
        # Method 1: Extract from layout clusters
        layout_elements = self._extract_from_layout_clusters(doc_result, page, page_num)
        page_elements.extend(layout_elements)
        
        # Method 2: Extract enriched formulas
        if "formulas" in self.extract_types:
            enriched_elements = self._extract_from_enriched_elements(doc_result, page, page_num)
            page_elements.extend(enriched_elements)
        
        # Remove duplicates
        page_elements = self._deduplicate_elements(page_elements)
        
        self.stats["total"] += len(page_elements)
        return page_elements
    
    def _extract_from_layout_clusters(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract elements from Docling's layout clusters."""
        elements = []
        
        # Get layout clusters for this page
        page_layout = None
        if hasattr(doc_result, 'pages') and len(doc_result.pages) >= page_num:
            page_layout = doc_result.pages[page_num - 1]
        
        if not page_layout:
            return elements
        
        # Get clusters from layout prediction
        clusters = []
        if hasattr(page_layout, 'predictions') and hasattr(page_layout.predictions, 'layout'):
            clusters = page_layout.predictions.layout.clusters
        elif hasattr(page_layout, 'clusters'):
            clusters = page_layout.clusters
        
        if clusters:
            print(f"  🔍 Processing {len(clusters)} layout regions from Docling...")
        
        # Process each cluster
        for cluster in clusters:
            element_type = self._map_docling_label_to_type(cluster.label)
            
            # Skip if not requested
            if element_type == "unknown" or element_type not in self.extract_types:
                continue
            
            # Apply confidence threshold
            confidence = getattr(cluster, 'confidence', 1.0)
            if confidence < 0.3:
                continue
            
            # Extract the element
            element = self._extract_cluster_region(page, cluster, element_type, page_num)
            if element:
                elements.append(element)
                self.stats[element_type] += 1
        
        return elements
    
    def _extract_from_enriched_elements(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract enriched formulas from Docling's document structure."""
        elements = []
        
        # Check for enriched formulas in document texts
        if hasattr(doc_result, 'document') and hasattr(doc_result.document, 'texts'):
            for text_item in doc_result.document.texts:
                if (hasattr(text_item, 'label') and 
                    text_item.label == DocItemLabel.FORMULA and 
                    hasattr(text_item, 'prov') and text_item.prov):
                    
                    for prov in text_item.prov:
                        if hasattr(prov, 'page_no') and prov.page_no == page_num:
                            element = self._extract_enriched_formula(page, text_item, prov, page_num)
                            if element:
                                elements.append(element)
                                self.stats["formulas"] += 1
        
        return elements
    
    def _map_docling_label_to_type(self, docling_label) -> str:
        """Map Docling's DocItemLabel to our element types."""
        label_mapping = {
            DocItemLabel.FORMULA: "formulas",
            DocItemLabel.TABLE: "tables", 
            DocItemLabel.PICTURE: "figures",
            # Add more mappings as needed
        }
        
        mapped_type = label_mapping.get(docling_label, "unknown")
        
        # Heuristic: classify some pictures as charts
        if mapped_type == "figures" and "charts" in self.extract_types:
            # Could add more sophisticated logic here
            return "charts" if "charts" in self.extract_types else "figures"
        
        return mapped_type
    
    def _extract_cluster_region(self, page, cluster, element_type: str, page_num: int) -> Optional[Dict]:
        """Extract a region based on Docling's cluster detection."""
        try:
            bbox = cluster.bbox
            
            # Get page dimensions
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Handle different bbox formats
            if hasattr(bbox, 'l'):  # Normalized coordinates (0-100)
                # Debug: check the actual values
                if bbox.l > 100 or bbox.t > 100 or bbox.r > 100 or bbox.b > 100:
                    # These are likely pixel coordinates, not percentages
                    x0 = bbox.l
                    y0 = bbox.t  
                    x1 = bbox.r
                    y1 = bbox.b
                else:
                    # These are percentages
                    x0 = (bbox.l / 100.0) * page_width
                    y0 = (bbox.t / 100.0) * page_height
                    x1 = (bbox.r / 100.0) * page_width
                    y1 = (bbox.b / 100.0) * page_height
            elif hasattr(bbox, 'x'):  # Direct coordinates with x, y, w, h
                x0 = bbox.x
                y0 = bbox.y
                x1 = x0 + bbox.w
                y1 = y0 + bbox.h
            else:
                print(f"  ⚠️ Unknown bbox format for {element_type}")
                return None
            
            # Ensure coordinates are in correct order
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            
            # Clamp to page bounds before padding
            x0 = max(0, min(x0, page_width))
            y0 = max(0, min(y0, page_height))
            x1 = max(0, min(x1, page_width))
            y1 = max(0, min(y1, page_height))
            
            # Add reasonable padding based on element type
            if element_type == "formulas":
                padding_x, padding_y = 20, 15  # Much smaller padding
            elif element_type == "tables":
                padding_x, padding_y = 15, 10
            else:  # charts, figures
                padding_x, padding_y = 10, 8
            
            # Get page dimensions
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Apply padding while ensuring we stay within page bounds
            x0_final = max(0, x0 - padding_x)
            y0_final = max(0, y0 - padding_y)
            x1_final = min(page_width, x1 + padding_x)
            y1_final = min(page_height, y1 + padding_y)
            
            # Ensure valid rectangle
            if x0_final >= x1_final or y0_final >= y1_final:
                print(f"  ⚠️ Invalid bbox for {element_type}: ({x0_final}, {y0_final}, {x1_final}, {y1_final})")
                return None
            
            # Create element ID
            count = self.stats[element_type] + 1
            type_abbrev = {
                "formulas": "FML",
                "tables": "TBL", 
                "charts": "CHT",
                "figures": "FIG"
            }.get(element_type, "UNK")
            
            element_id = f"{type_abbrev}_P{page_num:03d}_N{count:03d}"
            
            # Extract high-resolution image
            rect = fitz.Rect(x0_final, y0_final, x1_final, y1_final)
            mat = fitz.Matrix(3.0, 3.0)  # High resolution
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image 
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            pix = None  # Free memory
            
            width = int(x1_final - x0_final)
            height = int(y1_final - y0_final)
            confidence = getattr(cluster, 'confidence', 1.0)
            
            print(f"  ✅ {element_id}: {element_type} ({width}x{height}px, confidence: {confidence:.2f})")
            
            return {
                "id": element_id,
                "type": element_type,
                "page": page_num,
                "bbox": [x0_final, y0_final, x1_final, y1_final],
                "width": width,
                "height": height,
                "confidence": confidence,
                "method": "docling_layout",
                "file": image_path.name
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract {element_type}: {e}")
            return None
    
    def _extract_enriched_formula(self, page, text_item, prov, page_num: int) -> Optional[Dict]:
        """Extract an enriched formula detected by Docling."""
        try:
            bbox = prov.bbox
            
            # Get page dimensions
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Handle coordinate format
            if bbox.l > 100 or bbox.t > 100 or bbox.r > 100 or bbox.b > 100:
                # These are likely pixel coordinates, not percentages
                x0 = bbox.l
                y0 = bbox.t
                x1 = bbox.r
                y1 = bbox.b
            else:
                # These are percentages (0-100 range)
                x0 = (bbox.l / 100.0) * page_width
                y0 = (bbox.t / 100.0) * page_height
                x1 = (bbox.r / 100.0) * page_width
                y1 = (bbox.b / 100.0) * page_height
            
            # Ensure coordinates are in correct order
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            
            # Clamp to page bounds
            x0 = max(0, min(x0, page_width))
            y0 = max(0, min(y0, page_height))
            x1 = max(0, min(x1, page_width))
            y1 = max(0, min(y1, page_height))
            
            # Reasonable padding for formulas  
            padding_x, padding_y = 20, 15
            
            x0_final = max(0, x0 - padding_x)
            y0_final = max(0, y0 - padding_y)
            x1_final = min(page_width, x1 + padding_x)
            y1_final = min(page_height, y1 + padding_y)
            
            # Ensure valid rectangle
            if x0_final >= x1_final or y0_final >= y1_final:
                print(f"  ⚠️ Invalid bbox for enriched formula: ({x0_final}, {y0_final}, {x1_final}, {y1_final})")
                return None
            
            # Create element ID
            count = self.stats["formulas"] + 1
            element_id = f"FML_P{page_num:03d}_N{count:03d}_enriched"
            
            # Extract high-resolution image
            rect = fitz.Rect(x0_final, y0_final, x1_final, y1_final)
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image 
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            pix = None  # Free memory
            
            width = int(x1_final - x0_final)
            height = int(y1_final - y0_final)
            
            # Get enriched text if available
            enriched_text = ""
            if hasattr(text_item, 'text'):
                enriched_text = text_item.text[:100]
            
            print(f"  ✅ {element_id}: enriched formula ({width}x{height}px)")
            
            return {
                "id": element_id,
                "type": "formulas",
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
    
    def _deduplicate_elements(self, elements: List[Dict]) -> List[Dict]:
        """Remove duplicate detections based on overlap."""
        if not elements:
            return elements
        
        # Sort by confidence
        elements_sorted = sorted(elements, key=lambda x: x.get("confidence", 0), reverse=True)
        
        deduplicated = []
        for current in elements_sorted:
            current_bbox = current["bbox"]
            is_duplicate = False
            
            for kept in deduplicated:
                kept_bbox = kept["bbox"]
                
                # Calculate overlap
                overlap_ratio = self._calculate_bbox_overlap(current_bbox, kept_bbox)
                
                # Be more aggressive about removing overlaps for formulas
                threshold = 0.5 if current.get("type") == "formulas" else 0.7
                if overlap_ratio > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(current)
        
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
        
        # Calculate areas
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        
        # Return intersection over minimum area
        min_area = min(area1, area2)
        return intersection_area / min_area if min_area > 0 else 0.0
    
    def _save_metadata(self):
        """Save extraction metadata and report."""
        # Save JSON metadata
        metadata = {
            "source": self.pdf_path.name,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "elements": self.elements,
            "extraction_method": "docling_precise"
        }
        
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Generate report
        report_path = self.output_dir / "extraction_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Docling Precise Extraction Report\n\n")
            f.write(f"**Source:** {self.pdf_path.name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Method:** Docling EGRET-LARGE Layout Detection\n\n")
            
            f.write("## Summary\n\n")
            for elem_type in ["formulas", "tables", "charts", "figures"]:
                if self.stats[elem_type] > 0:
                    f.write(f"- **{elem_type.capitalize()}:** {self.stats[elem_type]}\n")
            f.write(f"- **Total:** {self.stats['total']}\n\n")
            
            if self.elements:
                f.write("## Extracted Elements\n\n")
                current_page = 0
                for elem in self.elements:
                    if elem['page'] != current_page:
                        current_page = elem['page']
                        f.write(f"\n### Page {current_page}\n\n")
                    
                    f.write(f"- **{elem['id']}** ({elem['type']}): ")
                    f.write(f"{elem['width']}x{elem['height']}px - ")
                    f.write(f"Confidence: {elem['confidence']:.2f} - ")
                    f.write(f"Method: {elem['method']} - ")
                    f.write(f"[{elem['file']}]({elem['file']})\n")
        
        print(f"📄 Metadata saved: {metadata_path}")
        print(f"📄 Report saved: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Docling-Powered Precise Visual Element Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all element types (default)
  python docling_precise_extractor.py document.pdf
  
  # Extract only formulas
  python docling_precise_extractor.py document.pdf --formulas
  
  # Extract tables and charts
  python docling_precise_extractor.py document.pdf --tables --charts
        """
    )
    
    parser.add_argument("pdf_file", help="Path to the PDF file to process")
    parser.add_argument("--formulas", action="store_true", help="Extract mathematical formulas")
    parser.add_argument("--tables", action="store_true", help="Extract tables")
    parser.add_argument("--charts", action="store_true", help="Extract charts and graphs")
    parser.add_argument("--figures", action="store_true", help="Extract figures and images")
    
    args = parser.parse_args()
    
    # Determine what to extract
    extract_types = []
    if args.formulas:
        extract_types.append("formulas")
    if args.tables:
        extract_types.append("tables") 
    if args.charts:
        extract_types.append("charts")
    if args.figures:
        extract_types.append("figures")
    if not extract_types:
        extract_types = ["formulas", "tables", "charts", "figures"]
    
    try:
        extractor = DoclingPreciseExtractor(args.pdf_file, extract_types)
        extractor.extract()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()