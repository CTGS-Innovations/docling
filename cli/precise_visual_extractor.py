#!/usr/bin/env python3
"""
Precise Visual Element Extractor - Focus on accurate bounding boxes for VLM processing.
Based on the insight that Docling VLM works best with focused, precisely cropped elements.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
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


class PreciseVisualExtractor:
    """Precise detection and extraction with tight bounding boxes."""
    
    def __init__(self, pdf_path: str, extract_types: List[str] = None):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Filter what to extract
        self.extract_types = set(extract_types or ["formulas", "tables", "charts", "figures"])
        
        # Output directory
        self.output_dir = Path("output") / self.pdf_path.stem
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear previous extractions
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        
        # Initialize Docling converter with enhanced layout detection
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
        """Setup Docling converter with optimal layout detection for visual elements."""
        try:
            # Use basic Docling configuration for now
            print("🤖 Setting up Docling converter with default configuration...")
            
            # Create converter with basic options
            converter = DocumentConverter()
            
            print("✅ Docling converter ready")
            return converter
            
        except Exception as e:
            print(f"❌ Error setting up Docling converter: {e}")
            raise
    
    def extract(self):
        """Main extraction using Docling's professional layout detection."""
        print(f"\n{'='*60}")
        print(f"🎯 DOCLING-POWERED VISUAL ELEMENT EXTRACTION")
        print(f"📄 PDF: {self.pdf_path.name}")  
        print(f"📁 Output: {self.output_dir}")
        print(f"🔍 Extracting: {', '.join(sorted(self.extract_types))}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Use Docling to analyze the document layout
        print("📊 Running Docling layout analysis...")
        doc_result = self.converter.convert(self.pdf_path)
        
        # Also open with PyMuPDF for image extraction
        pymupdf_doc = fitz.open(str(self.pdf_path))
        
        print(f"📖 Processing {len(pymupdf_doc)} pages with Docling layout data...\n")
        
        # Extract elements based on Docling's layout detection
        for page_num in range(len(pymupdf_doc)):
            page = pymupdf_doc[page_num]
            page_elements = self._extract_using_docling_layout(doc_result, page, page_num + 1)
            
            if page_elements:
                print(f"📄 Page {page_num + 1}: Found {len(page_elements)} layout elements")
                self.elements.extend(page_elements)
        
        pymupdf_doc.close()
        
        # Save results
        self._save_metadata()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ DOCLING EXTRACTION COMPLETE in {elapsed:.2f}s")
        print(f"{'='*60}")
        print(f"📊 Elements extracted:")
        for elem_type, count in self.stats.items():
            if elem_type != "total" and count > 0:
                print(f"  - {elem_type}: {count}")
        print(f"  TOTAL: {self.stats['total']}")
        print(f"📁 Output: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def _extract_using_docling_layout(self, doc_result, page, page_num: int) -> List[Dict]:
        """Extract elements using Docling's professional layout detection."""
        page_elements = []
        
        # Get layout clusters from Docling for this page
        page_layout = None
        if hasattr(doc_result, 'pages') and len(doc_result.pages) >= page_num:
            page_layout = doc_result.pages[page_num - 1]  # 0-indexed
        
        if not page_layout:
            print(f"  ⚠️ No layout data found for page {page_num}")
            return page_elements
        
        print(f"  🔍 Processing {len(getattr(page_layout, 'clusters', []))} layout regions from Docling...")
        
        # Process each layout cluster detected by Docling
        for cluster in getattr(page_layout, 'clusters', []):
            element_type = self._map_docling_label_to_type(cluster.label)
            
            # Skip if this element type is not requested
            if element_type not in self.extract_types:
                continue
            
            # Apply confidence threshold
            confidence = getattr(cluster, 'confidence', 1.0)
            if confidence < 0.4:  # Lower threshold since Docling is more accurate
                continue
            
            # Extract the region using Docling's precise bounding box
            element = self._extract_docling_region(page, cluster, element_type, page_num)
            if element:
                page_elements.append(element)
                self.stats[element_type + "s"] += 1
                
                print(f"  ✅ {element['id']}: {element_type} "
                      f"({element['width']}x{element['height']}px, "
                      f"confidence: {confidence:.2f})")
        
        self.stats["total"] += len(page_elements)
        return page_elements
    
    def _map_docling_label_to_type(self, docling_label) -> str:
        """Map Docling's DocItemLabel to our element types."""
        label_mapping = {
            DocItemLabel.FORMULA: "formula",
            DocItemLabel.TABLE: "table", 
            DocItemLabel.PICTURE: "figure",
            # DocItemLabel.CHART: "chart",  # If available
            # Add more mappings as needed
        }
        
        mapped_type = label_mapping.get(docling_label, "unknown")
        
        # For pictures, try to classify as chart vs figure based on content
        if mapped_type == "figure" and "charts" in self.extract_types:
            # Simple heuristic: larger rectangles more likely to be charts
            return "chart"  # Could be made smarter
        
        return mapped_type
    
    def _extract_docling_region(self, page, cluster, element_type: str, page_num: int) -> Dict:
        """Extract region using Docling's precise bounding box with full-width approach."""
        try:
            # Get Docling's detected bounding box
            bbox = cluster.bbox
            docling_x0, docling_y0 = bbox.x, bbox.y
            docling_x1, docling_y1 = docling_x0 + bbox.w, docling_y0 + bbox.h
            
            # FULL-WIDTH ENHANCEMENT: Expand Docling's precise detection
            # Use Docling's detection as the base, but expand for better context
            
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Smart expansion based on element type and content
            if element_type == "formula":
                # For formulas, use generous full-width approach
                expansion_x = 80  # Good margin for formulas
                expansion_y = 25  # Extra space for super/subscripts
            elif element_type == "table":
                # For tables, expand to capture full table structure
                expansion_x = 40
                expansion_y = 20
            else:  # charts, figures
                # For images, minimal expansion (they're usually well-defined)
                expansion_x = 20
                expansion_y = 15
            
            # Apply full-width expansion
            x0 = max(0, docling_x0 - expansion_x)
            y0 = max(0, docling_y0 - expansion_y)
            x1 = min(page_width, docling_x1 + expansion_x)
            y1 = min(page_height, docling_y1 + expansion_y)
            
            # Create element ID
            count = self.stats.get(element_type + "s", 0) + 1
            type_abbrev = {
                "formula": "FML",
                "table": "TBL", 
                "chart": "CHT",
                "figure": "FIG"
            }.get(element_type, "UNK")
            
            element_id = f"{type_abbrev}_P{page_num:03d}_N{count:03d}"
            
            # Extract at high resolution
            rect = fitz.Rect(x0, y0, x1, y1)
            mat = fitz.Matrix(3.0, 3.0)  # High resolution for VLM
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            width = int(x1 - x0)
            height = int(y1 - y0)
            confidence = getattr(cluster, 'confidence', 1.0)
            
            return {
                "id": element_id,
                "type": element_type,
                "page": page_num,
                "bbox": [x0, y0, x1, y1],
                "docling_bbox": [docling_x0, docling_y0, docling_x1, docling_y1],
                "width": width,
                "height": height,
                "confidence": confidence,
                "method": "docling_layout_detection",
                "file": image_path.name,
                "text_preview": str(getattr(cluster, 'text', ''))[:100] if hasattr(cluster, 'text') else ""
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract {element_type}: {e}")
            return None
    
    def _extract_enriched_formula(self, page, text_item, prov, page_num: int) -> Dict:
        """Extract a formula image from enriched document element."""
        try:
            bbox = prov.bbox
            
            # Convert normalized coordinates to page coordinates
            page_width = page.rect.width
            page_height = page.rect.height
            
            x0 = bbox.l * page_width / 100.0
            y0 = bbox.t * page_height / 100.0
            x1 = bbox.r * page_width / 100.0
            y1 = bbox.b * page_height / 100.0
            
            # Add generous padding for formulas
            padding_x = 80
            padding_y = 30
            
            x0_final = max(0, x0 - padding_x)
            y0_final = max(0, y0 - padding_y)
            x1_final = min(page_width, x1 + padding_x)
            y1_final = min(page_height, y1 + padding_y)
            
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
                "docling_bbox": [x0, y0, x1, y1],
                "width": width,
                "height": height,
                "confidence": 0.9,
                "method": "docling_enriched",
                "file": image_path.name,
                "enriched_text": enriched_text[:100] if enriched_text else ""
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract enriched formula: {e}")
            return None
    
    def _deduplicate_elements(self, elements: List[Dict]) -> List[Dict]:
        """Remove duplicate element detections."""
        if not elements:
            return elements
        
        # Sort by confidence descending
        elements_sorted = sorted(elements, key=lambda x: x.get("confidence", 0), reverse=True)
        
        deduplicated = []
        for current in elements_sorted:
            current_bbox = current["bbox"]
            is_duplicate = False
            
            # Check against already kept elements
            for kept in deduplicated:
                kept_bbox = kept["bbox"]
                
                # Calculate overlap
                overlap_ratio = self._calculate_bbox_overlap(current_bbox, kept_bbox)
                
                # If significant overlap, consider duplicate
                if overlap_ratio > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(current)
        
        return deduplicated
    
    def _detect_visual_tables(self, page, page_num: int) -> List[Dict]:
        """Detect tables drawn with actual lines/borders."""
        tables = []
        drawings = page.get_drawings()
        
        if not drawings:
            return tables
        
        # Group line drawings into table structures
        line_groups = self._group_lines_into_tables(drawings)
        
        for group in line_groups:
            if len(group['lines']) >= 4:  # Need at least 4 lines for a table
                # Calculate tight bounding box around the lines
                x_coords = []
                y_coords = []
                
                for line in group['lines']:
                    if 'rect' in line:
                        rect = line['rect']
                        x_coords.extend([rect.x0, rect.x1])
                        y_coords.extend([rect.y0, rect.y1])
                
                if x_coords and y_coords:
                    bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    
                    # Must be substantial size
                    if width > 100 and height > 60:
                        tables.append({
                            "bbox": bbox,
                            "confidence": 0.9,
                            "method": "visual_lines",
                            "line_count": len(group['lines'])
                        })
        
        return tables
    
    def _group_lines_into_tables(self, drawings) -> List[Dict]:
        """Group line drawings that could form table borders."""
        horizontal_lines = []
        vertical_lines = []
        
        # Separate horizontal and vertical lines
        for drawing in drawings:
            if 'rect' in drawing:
                rect = drawing['rect']
                width = rect.x1 - rect.x0
                height = rect.y1 - rect.y0
                
                # Classify as horizontal or vertical line
                if height < 5 and width > 20:  # Horizontal line
                    horizontal_lines.append(drawing)
                elif width < 5 and height > 20:  # Vertical line
                    vertical_lines.append(drawing)
        
        # Group intersecting lines
        groups = []
        if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
            # Simple grouping - find lines that are close to each other
            for h_line in horizontal_lines:
                h_rect = h_line['rect']
                group_lines = [h_line]
                
                # Find related vertical lines
                for v_line in vertical_lines:
                    v_rect = v_line['rect']
                    # Check if vertical line intersects or is near horizontal line
                    if (v_rect.x0 >= h_rect.x0 - 10 and v_rect.x0 <= h_rect.x1 + 10 and
                        v_rect.y0 <= h_rect.y0 + 10 and v_rect.y1 >= h_rect.y0 - 10):
                        group_lines.append(v_line)
                
                if len(group_lines) >= 3:  # At least 1 horizontal + 2 vertical
                    groups.append({"lines": group_lines})
        
        return groups
    
    def _detect_text_tables(self, page, page_num: int) -> List[Dict]:
        """Detect tables formed by aligned text - capture full table regions with more context."""
        tables = []
        text_dict = page.get_text("dict")
        
        # Strategy 1: Look for blocks with consistent column alignment (original approach, but extended)
        for block in text_dict.get("blocks", []):
            if "lines" not in block or len(block["lines"]) < 3:
                continue
            
            lines = block["lines"]
            
            # Analyze column structure
            line_data = []
            
            for line in lines:
                spans = line.get("spans", [])
                if len(spans) < 2:  # Need multiple columns
                    continue
                
                line_positions = []
                line_text = ""
                
                for span in spans:
                    x_pos = span["bbox"][0]
                    line_positions.append(x_pos)
                    line_text += span.get("text", "") + " "
                
                line_data.append({
                    "positions": line_positions,
                    "text": line_text.strip(),
                    "bbox": line["bbox"]
                })
            
            # Check if we have consistent column structure
            if len(line_data) >= 3:
                # Find common x-positions across lines
                all_positions = []
                for line in line_data:
                    all_positions.extend(line["positions"])
                
                # Group similar positions (within 8 pixels for more flexibility)
                column_x = []
                for pos in sorted(set(all_positions)):
                    if not column_x or pos - column_x[-1] > 8:
                        column_x.append(pos)
                
                # If we have 2+ consistent columns, it's likely a table
                if len(column_x) >= 2:
                    # Calculate expanded bounding box with padding
                    all_bboxes = [line["bbox"] for line in line_data]
                    x0 = min(bbox[0] for bbox in all_bboxes) - 20  # More left padding
                    y0 = min(bbox[1] for bbox in all_bboxes) - 15  # Top padding
                    x1 = max(bbox[2] for bbox in all_bboxes) + 20  # More right padding
                    y1 = max(bbox[3] for bbox in all_bboxes) + 15  # Bottom padding
                    
                    width = x1 - x0
                    height = y1 - y0
                    
                    if width > 120 and height > 40:  # More lenient size requirements
                        confidence = 0.7 + (min(len(column_x), 5) * 0.05)  # Higher confidence for more columns
                        tables.append({
                            "bbox": [x0, y0, x1, y1],
                            "confidence": confidence,
                            "method": "aligned_text_extended",
                            "columns": len(column_x),
                            "rows": len(line_data),
                            "text_preview": " | ".join([line["text"][:30] for line in line_data[:2]])
                        })
                        print(f"  🔍 TEXT TABLE ({len(line_data)} rows, {len(column_x)} cols): {width}x{height}px")
        
        # Strategy 2: Look for tabular patterns across multiple blocks (tables that span blocks)
        blocks = text_dict.get("blocks", [])
        for i in range(len(blocks) - 1):
            current_block = blocks[i]
            next_block = blocks[i + 1]
            
            if ("lines" not in current_block or "lines" not in next_block or
                len(current_block["lines"]) < 2 or len(next_block["lines"]) < 2):
                continue
            
            # Check if blocks are close vertically (likely part of same table)
            current_bottom = max(line["bbox"][3] for line in current_block["lines"])
            next_top = min(line["bbox"][1] for line in next_block["lines"])
            vertical_gap = next_top - current_bottom
            
            if vertical_gap < 30:  # Blocks are close
                # Combine lines from both blocks
                all_lines = current_block["lines"] + next_block["lines"]
                
                # Check for consistent alignment across the combined blocks
                line_data = []
                for line in all_lines:
                    spans = line.get("spans", [])
                    line_text = "".join(span.get("text", "") for span in spans).strip()
                    
                    # Look for tabular indicators in the text
                    has_numbers = any(c.isdigit() for c in line_text)
                    has_separators = any(sep in line_text for sep in ["\t", "  ", " | "])  # Multiple spaces or separators
                    reasonable_length = 10 < len(line_text) < 200
                    
                    if has_numbers and reasonable_length and (has_separators or len(spans) >= 2):
                        line_data.append({
                            "text": line_text,
                            "bbox": line["bbox"]
                        })
                
                if len(line_data) >= 4:  # Need at least 4 tabular-looking lines
                    # Calculate bounding box for the multi-block table
                    all_bboxes = [line["bbox"] for line in line_data]
                    x0 = min(bbox[0] for bbox in all_bboxes) - 25
                    y0 = min(bbox[1] for bbox in all_bboxes) - 20
                    x1 = max(bbox[2] for bbox in all_bboxes) + 25
                    y1 = max(bbox[3] for bbox in all_bboxes) + 20
                    
                    width = x1 - x0
                    height = y1 - y0
                    
                    if width > 150 and height > 80:
                        tables.append({
                            "bbox": [x0, y0, x1, y1],
                            "confidence": 0.75,
                            "method": "multi_block_table",
                            "rows": len(line_data),
                            "blocks_spanned": 2,
                            "text_preview": " | ".join([line["text"][:25] for line in line_data[:3]])
                        })
                        print(f"  🔍 MULTI-BLOCK TABLE ({len(line_data)} rows): {width}x{height}px")
        
        return tables
    
    def _detect_precise_formulas(self, page, page_num: int) -> List[Dict]:
        """Detect mathematical expressions as complete lines/blocks - no fragments."""
        formulas = []
        text_dict = page.get_text("dict")
        
        # Enhanced mathematical indicators
        greek_letters = ["α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "ι", "κ", "λ", "μ", "ν", "ξ", "ο", "π", "ρ", "σ", "τ", "υ", "φ", "χ", "ψ", "ω",
                        "Α", "Β", "Γ", "Δ", "Ε", "Ζ", "Η", "Θ", "Ι", "Κ", "Λ", "Μ", "Ν", "Ξ", "Ο", "Π", "Ρ", "Σ", "Τ", "Υ", "Φ", "Χ", "Ψ", "Ω"]
        
        math_operators = ["∑", "∫", "∂", "√", "∞", "≤", "≥", "≠", "±", "×", "÷", "∇", "∆", "∈", "∉", "⊂", "⊆", "∪", "∩", "→", "←", "↔", "⇒", "⇔"]
        
        # Superscript/subscript indicators
        superscript_chars = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹", "⁺", "⁻", "⁼", "⁽", "⁾", "ⁿ", "ⁱ"]
        subscript_chars = ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉", "₊", "₋", "₌", "₍", "₎", "ₙ", "ᵢ"]
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            # Strategy 1: Analyze each LINE as a whole unit
            for line in block["lines"]:
                spans = line.get("spans", [])
                line_bbox = line["bbox"]
                
                # Get the complete text of the entire line
                line_text = "".join(span.get("text", "") for span in spans).strip()
                
                if not line_text or len(line_text) < 3:
                    continue
                
                # Analyze the ENTIRE LINE for mathematical content
                has_greek = any(char in line_text for char in greek_letters)
                has_math_ops = any(op in line_text for op in math_operators)
                has_superscript = any(char in line_text for char in superscript_chars)
                has_subscript = any(char in line_text for char in subscript_chars)
                
                # Check if any span has math fonts
                has_math_font = any(
                    any(font_hint in span.get("font", "").lower() for font_hint in 
                        ["math", "symbol", "times", "cmr", "tex", "stix", "cambria"])
                    for span in spans
                )
                
                # Pattern indicators for the entire line
                has_equation = ("=" in line_text and 
                               any(c.isalnum() for c in line_text) and 
                               any(c.isdigit() or c in "xyzabcfghijklmnopqrstuvw" for c in line_text))
                
                has_complex_fraction = ("/" in line_text and 
                                      any(c.isdigit() for c in line_text.replace("/", "")) and
                                      len(line_text.replace(" ", "")) > 5)
                
                has_parentheses_with_vars = ("(" in line_text and ")" in line_text and 
                                           any(c in "xyzabcfghijklmnopqrstuvw" for c in line_text.lower()))
                
                # LaTeX patterns
                has_latex = any(pattern in line_text for pattern in ["\\frac", "\\sum", "\\int", "\\begin", "\\end"])
                
                # Check if line is mostly mathematical (less regular text)
                words = line_text.split()
                math_word_count = 0
                for word in words:
                    if (any(char in word for char in greek_letters + math_operators + superscript_chars + subscript_chars) or
                        any(char in "=()+-*/^" for char in word) or
                        word.lower() in ["where", "let", "given", "if", "then", "such", "that"]):
                        math_word_count += 1
                
                is_mostly_math = len(words) > 0 and (math_word_count / len(words)) > 0.3
                
                # Determine if this is a standalone formula line (centered, isolated, etc.)
                is_standalone_line = (
                    len(line_text) < 100 and  # Not too long like a paragraph
                    (has_equation or has_math_ops or has_greek) and
                    not line_text.lower().startswith(("the", "this", "it", "we", "in", "for", "with", "as", "by"))
                )
                
                # Score the mathematical likelihood for the ENTIRE LINE
                math_score = 0
                if has_greek: math_score += 4
                if has_math_ops: math_score += 5
                if has_superscript or has_subscript: math_score += 3
                if has_math_font: math_score += 3
                if has_equation: math_score += 4
                if has_complex_fraction: math_score += 3
                if has_parentheses_with_vars: math_score += 2
                if has_latex: math_score += 5
                if is_mostly_math: math_score += 3
                if is_standalone_line: math_score += 2
                
                # Lower threshold since we're looking at complete lines
                threshold = 4
                
                if math_score >= threshold:
                    # FULL-WIDTH EXTRACTION APPROACH
                    # Instead of tight bounds, capture the full paragraph/section width
                    
                    # Find the actual text boundaries first
                    all_span_bboxes = []
                    for span in spans:
                        span_bbox = span["bbox"]
                        span_text = span.get("text", "").strip()
                        if span_text:
                            all_span_bboxes.append(span_bbox)
                    
                    if all_span_bboxes:
                        # Get the text boundaries
                        leftmost_x = min(bbox[0] for bbox in all_span_bboxes)
                        rightmost_x = max(bbox[2] for bbox in all_span_bboxes)
                        topmost_y = min(bbox[1] for bbox in all_span_bboxes)
                        bottommost_y = max(bbox[3] for bbox in all_span_bboxes)
                        
                        # FULL-WIDTH APPROACH: Extend horizontally to capture full context
                        # Look at the page margins/typical text width to determine full width
                        
                        # Strategy 1: Use a generous percentage of page width
                        page_width = page.rect.width
                        page_height = page.rect.height
                        
                        # For full-width extraction, extend significantly beyond text bounds
                        margin_left = leftmost_x * 0.8  # Go back toward typical left margin
                        margin_right = page_width - (page_width - rightmost_x) * 0.8  # Go forward toward typical right margin
                        
                        # Alternative strategy: Use fixed margins that work well for most documents
                        document_left_margin = min(50, leftmost_x)  # Don't go more than 50px left of text
                        document_right_margin = max(page_width - 50, rightmost_x + 50)  # Don't go more than 50px from right edge
                        
                        # Choose the more conservative approach
                        full_width_left = max(0, leftmost_x - 80)  # Generous left extension
                        full_width_right = min(page_width, rightmost_x + 80)  # Generous right extension
                        
                        # Smart vertical padding based on mathematical content
                        base_padding_y = 15  # More generous base padding
                        extra_padding_y = 0
                        
                        if has_subscript or any(char in line_text for char in subscript_chars):
                            extra_padding_y += 20
                        if has_superscript or any(char in line_text for char in superscript_chars):
                            extra_padding_y += 20
                        if has_complex_fraction or "/" in line_text:
                            extra_padding_y += 18
                        if any(op in line_text for op in ["∑", "∫", "∏", "√"]):
                            extra_padding_y += 25
                        
                        full_padding_y = base_padding_y + extra_padding_y
                        
                        # Final full-width bounding box
                        x0 = full_width_left
                        y0 = max(0, topmost_y - full_padding_y)
                        x1 = full_width_right
                        y1 = min(page_height, bottommost_y + full_padding_y)
                        
                    else:
                        # Fallback - use a very wide extraction around the line
                        line_center_x = (line_bbox[0] + line_bbox[2]) / 2
                        full_width = 400  # Default full width
                        
                        x0 = max(0, line_center_x - full_width/2)
                        x1 = min(page.rect.width, line_center_x + full_width/2)
                        y0 = max(0, line_bbox[1] - 25)
                        y1 = min(page.rect.height, line_bbox[3] + 25)
                    
                    width = x1 - x0
                    height = y1 - y0
                    
                    if width > 50 and height > 10:  # Reasonable line size
                        confidence = min(math_score / 10.0, 1.0)
                        formulas.append({
                            "bbox": [x0, y0, x1, y1],
                            "confidence": confidence,
                            "method": "full_line_analysis",
                            "text_preview": line_text[:100],
                            "math_score": math_score,
                            "is_standalone": is_standalone_line,
                            "word_count": len(words),
                            "math_density": math_word_count / len(words) if words else 0
                        })
                        print(f"  🔍 FULL LINE Formula: '{line_text[:60]}...' (score: {math_score}, standalone: {is_standalone_line})")
            
            # Strategy 2: Look for ENTIRE BLOCKS that are mathematical (like equation blocks)
            if len(block.get("lines", [])) >= 2:
                # Combine all lines in the block
                all_lines_text = []
                all_line_bboxes = []
                
                for line in block["lines"]:
                    line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                    if line_text:
                        all_lines_text.append(line_text)
                        all_line_bboxes.append(line["bbox"])
                
                if len(all_lines_text) >= 2:
                    block_text = " ".join(all_lines_text)
                    
                    # Check if the entire block is mathematical
                    block_has_math = (
                        any(op in block_text for op in math_operators) and
                        (any(char in block_text for char in greek_letters) or
                         block_text.count("=") >= 2 or  # Multiple equations
                         any(char in block_text for char in superscript_chars + subscript_chars))
                    )
                    
                    # Check if it's a coherent math block (not just random math scattered)
                    lines_with_math = sum(1 for line_text in all_lines_text 
                                        if any(op in line_text for op in math_operators + ["="]))
                    
                    is_coherent_math_block = (
                        block_has_math and 
                        lines_with_math >= 2 and
                        len(all_lines_text) <= 10 and  # Not too big like a whole paragraph
                        lines_with_math / len(all_lines_text) >= 0.5  # Most lines have math
                    )
                    
                    if is_coherent_math_block:
                        # FULL-WIDTH BLOCK EXTRACTION
                        all_span_bboxes_block = []
                        for line in block["lines"]:
                            for span in line.get("spans", []):
                                span_text = span.get("text", "").strip()
                                if span_text:
                                    all_span_bboxes_block.append(span["bbox"])
                        
                        if all_span_bboxes_block:
                            # Get text boundaries for the entire block
                            leftmost_x = min(bbox[0] for bbox in all_span_bboxes_block)
                            rightmost_x = max(bbox[2] for bbox in all_span_bboxes_block)
                            topmost_y = min(bbox[1] for bbox in all_span_bboxes_block)
                            bottommost_y = max(bbox[3] for bbox in all_span_bboxes_block)
                            
                            # FULL-WIDTH BLOCK: Much more generous horizontal expansion
                            page_width = page.rect.width
                            page_height = page.rect.height
                            
                            # For math blocks, use even more generous width
                            full_width_left = max(0, leftmost_x - 100)  # Very generous left extension
                            full_width_right = min(page_width, rightmost_x + 100)  # Very generous right extension
                            
                            # Smart vertical padding for math blocks
                            base_block_padding_y = 20  # More generous base for blocks
                            block_extra_padding_y = 0
                            
                            if any(char in block_text for char in subscript_chars + superscript_chars):
                                block_extra_padding_y += 25
                            if any(op in block_text for op in ["∑", "∫", "∏", "√", "/"]):
                                block_extra_padding_y += 30
                            if block_text.count("=") >= 2:
                                block_extra_padding_y += 20
                            
                            full_block_padding_y = base_block_padding_y + block_extra_padding_y
                            
                            x0 = full_width_left
                            y0 = max(0, topmost_y - full_block_padding_y)
                            x1 = full_width_right
                            y1 = min(page_height, bottommost_y + full_block_padding_y)
                        else:
                            # Fallback with full-width approach
                            x0 = max(0, min(bbox[0] for bbox in all_line_bboxes) - 100)
                            y0 = max(0, min(bbox[1] for bbox in all_line_bboxes) - 25)
                            x1 = min(page.rect.width, max(bbox[2] for bbox in all_line_bboxes) + 100)
                            y1 = min(page.rect.height, max(bbox[3] for bbox in all_line_bboxes) + 25)
                        
                        width = x1 - x0
                        height = y1 - y0
                        
                        if width > 100 and height > 30:
                            formulas.append({
                                "bbox": [x0, y0, x1, y1],
                                "confidence": 0.9,
                                "method": "coherent_math_block", 
                                "text_preview": block_text[:100],
                                "line_count": len(all_lines_text),
                                "math_line_ratio": lines_with_math / len(all_lines_text)
                            })
                            print(f"  🔍 MATH BLOCK ({len(all_lines_text)} lines): '{block_text[:60]}...'")
        
        # DEDUPLICATION: Remove overlapping/duplicate formula detections
        return self._deduplicate_formulas(formulas)
    
    def _deduplicate_formulas(self, formulas: List[Dict]) -> List[Dict]:
        """Remove duplicate/overlapping formula detections, keeping the best one."""
        if not formulas:
            return formulas
        
        # Sort by confidence descending, so we keep higher confidence detections
        formulas_sorted = sorted(formulas, key=lambda x: x.get("confidence", 0), reverse=True)
        
        deduplicated = []
        
        for current_formula in formulas_sorted:
            current_bbox = current_formula["bbox"]
            is_duplicate = False
            
            # Check against all formulas we've already kept
            for kept_formula in deduplicated:
                kept_bbox = kept_formula["bbox"]
                
                # Calculate overlap percentage
                overlap_ratio = self._calculate_bbox_overlap(current_bbox, kept_bbox)
                
                # If there's significant overlap (>70%), consider it a duplicate
                if overlap_ratio > 0.7:
                    is_duplicate = True
                    print(f"  🚫 DUPLICATE removed: '{current_formula.get('text_preview', '')[:40]}...' "
                          f"(overlap: {overlap_ratio:.2f} with kept formula)")
                    break
                
                # Also check for text similarity (same mathematical content)
                current_text = current_formula.get("text_preview", "")
                kept_text = kept_formula.get("text_preview", "")
                
                if len(current_text) > 10 and len(kept_text) > 10:
                    # Simple text similarity check
                    similarity = self._calculate_text_similarity(current_text, kept_text)
                    if similarity > 0.8:
                        is_duplicate = True
                        print(f"  🚫 DUPLICATE removed: '{current_text[:40]}...' "
                              f"(text similarity: {similarity:.2f})")
                        break
            
            if not is_duplicate:
                deduplicated.append(current_formula)
            
        print(f"  📊 Deduplication: {len(formulas)} → {len(deduplicated)} formulas")
        return deduplicated
    
    def _calculate_bbox_overlap(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate the overlap ratio between two bounding boxes."""
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
        
        # Return intersection over minimum area (more conservative)
        min_area = min(area1, area2)
        return intersection_area / min_area if min_area > 0 else 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity between two strings."""
        # Remove whitespace and convert to lowercase for comparison
        clean_text1 = ''.join(text1.split()).lower()
        clean_text2 = ''.join(text2.split()).lower()
        
        if not clean_text1 or not clean_text2:
            return 0.0
        
        # Simple approach: check how much of the shorter text appears in the longer one
        shorter = clean_text1 if len(clean_text1) <= len(clean_text2) else clean_text2
        longer = clean_text2 if len(clean_text1) <= len(clean_text2) else clean_text1
        
        if shorter in longer:
            return len(shorter) / len(longer)
        
        # Count common characters
        common_chars = sum(1 for c in shorter if c in longer)
        return common_chars / max(len(shorter), len(longer))
    
    def _detect_charts_and_figures(self, page, page_num: int) -> List[Dict]:
        """Detect charts and figures from embedded images."""
        charts_figures = []
        images = page.get_images()
        
        for img_index, img in enumerate(images):
            xref = img[0]
            
            try:
                # Get precise image bounds
                img_rects = page.get_image_rects(xref)
                
                if img_rects:
                    bbox = img_rects[0]
                    width = bbox.x1 - bbox.x0
                    height = bbox.y1 - bbox.y0
                    
                    # Filter by size - must be substantial
                    if width > 100 and height > 80:
                        aspect_ratio = width / height
                        
                        # Classify as chart or figure
                        is_chart = False
                        
                        # Charts tend to be more rectangular and larger
                        if width > 200 and height > 150:
                            if 0.8 < aspect_ratio < 2.0:  # Reasonable chart proportions
                                is_chart = True
                        
                        charts_figures.append({
                            "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                            "confidence": 0.9,
                            "method": "embedded_image",
                            "is_chart": is_chart,
                            "width": width,
                            "height": height
                        })
                        
            except Exception:
                continue
        
        return charts_figures
    
    def _extract_precise_region(self, page, region: Dict, element_type: str, page_num: int) -> Dict:
        """Extract region with precise cropping and padding."""
        try:
            bbox = region["bbox"]
            
            # Add small padding for better VLM processing
            padding = 5
            x0 = max(0, bbox[0] - padding)
            y0 = max(0, bbox[1] - padding)
            x1 = min(page.rect.width, bbox[2] + padding)
            y1 = min(page.rect.height, bbox[3] + padding)
            
            # Create element ID
            count = self.stats.get(element_type + "s", 0) + 1
            type_abbrev = {
                "formula": "FML",
                "table": "TBL", 
                "chart": "CHT",
                "figure": "FIG"
            }.get(element_type, "UNK")
            
            element_id = f"{type_abbrev}_P{page_num:03d}_N{count:03d}"
            
            # Extract at high resolution for VLM
            rect = fitz.Rect(x0, y0, x1, y1)
            mat = fitz.Matrix(3.0, 3.0)  # High resolution
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = self.output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            width = int(bbox[2] - bbox[0])
            height = int(bbox[3] - bbox[1])
            confidence = region.get("confidence", 0.5)
            method = region.get("method", "unknown")
            
            print(f"  ✅ {element_id}: {width}x{height}px (confidence: {confidence:.2f}, method: {method})")
            
            return {
                "id": element_id,
                "type": element_type,
                "page": page_num,
                "bbox": bbox,
                "width": width,
                "height": height,
                "confidence": confidence,
                "method": method,
                "file": image_path.name
            }
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract {element_type}: {e}")
            return None
    
    def _save_metadata(self):
        """Save extraction metadata with confidence scores."""
        metadata = {
            "source": self.pdf_path.name,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "elements": self.elements,
            "extraction_method": "precise_detection"
        }
        
        metadata_path = self.output_dir / "precise_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Generate detailed report
        report_path = self.output_dir / "precise_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Precise Visual Element Extraction Report\n\n")
            f.write(f"**Source:** {self.pdf_path.name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Method:** Precise detection with tight bounding boxes\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Formulas:** {self.stats['formulas']}\n")
            f.write(f"- **Tables:** {self.stats['tables']}\n") 
            f.write(f"- **Charts:** {self.stats['charts']}\n")
            f.write(f"- **Figures:** {self.stats['figures']}\n")
            f.write(f"- **Total:** {self.stats['total']}\n\n")
            
            if self.elements:
                f.write("## Extracted Elements (with Confidence Scores)\n\n")
                current_page = 0
                for elem in self.elements:
                    if elem['page'] != current_page:
                        current_page = elem['page']
                        f.write(f"\n### Page {current_page}\n\n")
                    
                    confidence = elem.get('confidence', 0.0)
                    method = elem.get('method', 'unknown')
                    f.write(f"- **{elem['id']}** ({elem['type']}): ")
                    f.write(f"{elem['width']}x{elem['height']}px - ")
                    f.write(f"Confidence: {confidence:.2f} ({method}) - ")
                    f.write(f"[{elem['file']}]({elem['file']})\n")


def main():
    parser = argparse.ArgumentParser(
        description="Precise Visual Element Extractor - Extract formulas, tables, charts, and figures with tight bounding boxes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all element types (default)
  python precise_visual_extractor.py document.pdf
  
  # Extract only formulas
  python precise_visual_extractor.py document.pdf --formulas
  
  # Extract only tables and charts
  python precise_visual_extractor.py document.pdf --tables --charts
  
  # Extract formulas and figures only
  python precise_visual_extractor.py document.pdf --formulas --figures
        """
    )
    
    parser.add_argument("pdf_file", help="Path to the PDF file to process")
    parser.add_argument("--formulas", action="store_true", help="Extract mathematical formulas and expressions")
    parser.add_argument("--tables", action="store_true", help="Extract tables (both visual and text-based)")
    parser.add_argument("--charts", action="store_true", help="Extract charts and graphs")
    parser.add_argument("--figures", action="store_true", help="Extract figures and images")
    parser.add_argument("--all", action="store_true", help="Extract all element types (default if no specific types selected)")
    
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
    if args.all or not extract_types:
        extract_types = ["formulas", "tables", "charts", "figures"]
    
    try:
        extractor = PreciseVisualExtractor(args.pdf_file, extract_types)
        extractor.extract()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()