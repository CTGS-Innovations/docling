#!/usr/bin/env python3
"""
Fast detection and extraction of visual elements from PDFs.
Uses the same detection approach as high_performance_pdf_processor.py
to quickly identify and extract tables, formulas, charts, and other visual elements.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
import json
from datetime import datetime
import time

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF required. Install with: pip install PyMuPDF")
    sys.exit(1)


class FastVisualElementExtractor:
    """Fast detection and extraction of visual elements using PyMuPDF."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Output directory
        self.output_dir = Path("output") / self.pdf_path.stem
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear previous extractions
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        
        self.elements = []
        self.stats = {
            "formulas": 0,
            "tables": 0,
            "charts": 0,
            "figures": 0,
            "total": 0
        }
    
    def extract(self):
        """Main extraction method."""
        print(f"\n{'='*60}")
        print(f"⚡ FAST VISUAL ELEMENT EXTRACTION")
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Open PDF
        doc = fitz.open(str(self.pdf_path))
        total_pages = len(doc)
        
        print(f"📖 Processing {total_pages} pages...\n")
        
        # Process each page
        for page_num in range(total_pages):
            page = doc[page_num]
            page_elements = self._detect_and_extract_page(page, page_num + 1)
            
            if page_elements:
                print(f"📄 Page {page_num + 1}: Found {len(page_elements)} elements")
                self.elements.extend(page_elements)
        
        doc.close()
        
        # Save metadata and generate report
        self._save_metadata()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ EXTRACTION COMPLETE in {elapsed:.2f}s")
        print(f"{'='*60}")
        print(f"📊 Elements extracted:")
        for elem_type, count in self.stats.items():
            if elem_type != "total" and count > 0:
                print(f"  - {elem_type}: {count}")
        print(f"  TOTAL: {self.stats['total']}")
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def _detect_and_extract_page(self, page, page_num: int) -> List[Dict]:
        """Detect and extract visual elements from a page."""
        page_elements = []
        
        # 1. Detect mathematical regions
        math_regions = self._detect_math_regions(page, page_num)
        for region in math_regions:
            element = self._extract_region(page, region, "formula", page_num)
            if element:
                page_elements.append(element)
                self.stats["formulas"] += 1
        
        # 2. Detect table regions
        table_regions = self._detect_table_regions(page, page_num)
        for region in table_regions:
            element = self._extract_region(page, region, "table", page_num)
            if element:
                page_elements.append(element)
                self.stats["tables"] += 1
        
        # 3. Detect embedded images/charts
        image_regions = self._detect_image_regions(page, page_num)
        for region in image_regions:
            # Classify as chart or figure based on context
            element_type = self._classify_image(region)
            element = self._extract_region(page, region, element_type, page_num)
            if element:
                page_elements.append(element)
                if element_type == "chart":
                    self.stats["charts"] += 1
                else:
                    self.stats["figures"] += 1
        
        self.stats["total"] += len(page_elements)
        return page_elements
    
    def _detect_math_regions(self, page, page_num: int) -> List[Dict]:
        """Detect mathematical expressions and formulas."""
        regions = []
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            block_text = ""
            has_math = False
            
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    block_text += text
                    
                    # Check for mathematical indicators
                    if any(sym in text for sym in ["∑", "∫", "∂", "√", "∞", "α", "β", "γ", "Δ", "π", "θ", "λ", "μ", "σ"]):
                        has_math = True
                    # Check for LaTeX patterns
                    if any(pat in text for pat in ["\\frac", "\\sum", "\\int", "\\begin{", "$$"]):
                        has_math = True
                    # Check for equation patterns
                    if "=" in text and any(c.isdigit() or c in "xyz" for c in text):
                        # Likely an equation
                        has_math = True
            
            if has_math and len(block_text.strip()) > 5:
                bbox = block["bbox"]
                # Filter out tiny regions
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                if width > 30 and height > 15:
                    regions.append({
                        "bbox": bbox,
                        "text": block_text[:100],
                        "type": "formula"
                    })
        
        return regions
    
    def _detect_table_regions(self, page, page_num: int) -> List[Dict]:
        """Detect table structures - look for visual table layouts."""
        regions = []
        
        # Method 1: Look for actual drawn tables (lines/borders)
        drawings = page.get_drawings()
        if drawings:
            # Group drawings into potential table structures
            table_candidates = self._group_table_drawings(drawings)
            for candidate in table_candidates:
                if candidate['confidence'] > 0.7:
                    regions.append({
                        "bbox": candidate['bbox'],
                        "type": "table",
                        "confidence": candidate['confidence'],
                        "method": "visual_lines"
                    })
        
        # Method 2: Look for text arranged in tabular format
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            lines = block["lines"]
            if len(lines) < 2:  # Need at least 2 rows
                continue
            
            # Analyze the block more carefully
            pipe_counts = []
            tab_counts = []
            x_positions_per_line = []
            
            block_text = ""
            for line in lines:
                line_text = ""
                line_x_positions = []
                
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    line_text += text
                    line_x_positions.append(span["bbox"][0])
                
                block_text += line_text + "\n"
                
                # Count separators per line
                pipe_counts.append(line_text.count("|"))
                tab_counts.append(line_text.count("\t"))
                x_positions_per_line.append(line_x_positions)
            
            # Strong table indicators:
            # 1. Consistent pipe separators across lines
            is_pipe_table = False
            if pipe_counts and min(pipe_counts) >= 2:  # At least 2 pipes per line
                # Check if pipe counts are consistent
                if max(pipe_counts) - min(pipe_counts) <= 2:  # Allow small variation
                    is_pipe_table = True
            
            # 2. Look for table header separators (---, ===)
            has_header_separator = False
            for line in block_text.split("\n"):
                if "---" in line or "===" in line or "___" in line:
                    if line.count("-") >= 5 or line.count("=") >= 5:
                        has_header_separator = True
                        break
            
            # 3. Check for grid alignment (columns)
            has_column_alignment = False
            if len(x_positions_per_line) >= 3:
                # Check if x positions repeat across lines (indicating columns)
                common_x_positions = set(x_positions_per_line[0])
                for line_positions in x_positions_per_line[1:]:
                    common_x_positions &= set(line_positions)
                
                if len(common_x_positions) >= 2:  # At least 2 consistent column positions
                    has_column_alignment = True
            
            # 4. Check for tab-separated values
            is_tsv = False
            if tab_counts and min(tab_counts) >= 1:
                # Consistent tabs across lines
                if max(tab_counts) - min(tab_counts) <= 1:
                    is_tsv = True
            
            # Decide if it's really a table
            confidence_score = 0
            if is_pipe_table:
                confidence_score += 3
            if has_header_separator:
                confidence_score += 2
            if has_column_alignment:
                confidence_score += 1
            if is_tsv:
                confidence_score += 2
            
            # Need a minimum confidence score to be considered a table
            if confidence_score >= 2:
                bbox = block["bbox"]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                # Tables should be reasonably sized
                if width > 100 and height > 40:
                    # Debug: print what we're detecting as a table
                    if confidence_score >= 3:  # High confidence
                        regions.append({
                            "bbox": bbox,
                            "text": block_text[:100],
                            "type": "table",
                            "confidence": confidence_score
                        })
                    elif confidence_score == 2:
                        # Medium confidence - might be a list or structured text
                        # Check if it's really a table by looking for data patterns
                        lines_split = block_text.split("\n")
                        if len(lines_split) >= 4:  # Enough rows for a table
                            regions.append({
                                "bbox": bbox,
                                "text": block_text[:100],
                                "type": "table",
                                "confidence": confidence_score
                            })
        
        return regions
    
    def _detect_image_regions(self, page, page_num: int) -> List[Dict]:
        """Detect embedded images and charts."""
        regions = []
        images = page.get_images()
        
        for img_index, img in enumerate(images):
            xref = img[0]
            
            try:
                # Get image rectangle
                img_rects = page.get_image_rects(xref)
                
                if img_rects:
                    bbox = img_rects[0]
                    width = bbox.x1 - bbox.x0
                    height = bbox.y1 - bbox.y0
                    
                    # Filter out tiny images (likely decorative)
                    if width > 50 and height > 50:
                        regions.append({
                            "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                            "xref": xref,
                            "width": width,
                            "height": height,
                            "type": "image"
                        })
            except Exception:
                continue
        
        return regions
    
    def _classify_image(self, region: Dict) -> str:
        """Classify an image as chart or figure based on characteristics."""
        # Simple heuristics - can be enhanced
        width = region.get("width", 0)
        height = region.get("height", 0)
        
        # Charts tend to be more square or landscape
        aspect_ratio = width / height if height > 0 else 1
        
        if 0.7 < aspect_ratio < 1.5:
            return "chart"  # Likely a chart/graph
        else:
            return "figure"  # General figure
    
    def _extract_region(self, page, region: Dict, element_type: str, page_num: int) -> Dict:
        """Extract a region as an image."""
        try:
            bbox = region["bbox"]
            
            # Create element ID
            count = self.stats.get(element_type + "s", 0) + 1
            type_abbrev = {
                "formula": "FML",
                "table": "TBL",
                "chart": "CHT",
                "figure": "FIG"
            }.get(element_type, "UNK")
            
            element_id = f"{type_abbrev}_P{page_num:03d}_N{count:03d}"
            
            # Extract image at high resolution
            rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            width = int(bbox[2] - bbox[0])
            height = int(bbox[3] - bbox[1])
            
            print(f"  ✅ {element_id}: {width}x{height}px")
            
            return {
                "id": element_id,
                "type": element_type,
                "page": page_num,
                "bbox": bbox,
                "width": width,
                "height": height,
                "file": image_path.name
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract {element_type}: {e}")
            return None
    
    def _save_metadata(self):
        """Save extraction metadata."""
        metadata = {
            "source": self.pdf_path.name,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "elements": self.elements
        }
        
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Generate markdown report
        report_path = self.output_dir / "extraction_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Visual Element Extraction Report\n\n")
            f.write(f"**Source:** {self.pdf_path.name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Formulas:** {self.stats['formulas']}\n")
            f.write(f"- **Tables:** {self.stats['tables']}\n")
            f.write(f"- **Charts:** {self.stats['charts']}\n")
            f.write(f"- **Figures:** {self.stats['figures']}\n")
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
                    f.write(f"[{elem['file']}]({elem['file']})\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_detect_extract_images.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    extractor = FastVisualElementExtractor(pdf_path)
    extractor.extract()


if __name__ == "__main__":
    main()