#!/usr/bin/env python3
"""
Comprehensive Visual Element Extractor for PDFs
Aggressively extracts ALL elements that Docling/VLM can process:
- Mathematical formulas (inline and display)
- Tables (structured data)
- Charts (bar, line, pie, scatter, etc.)
- Plots (scientific plots, graphs)
- Algorithms (pseudocode, algorithmic descriptions)
- Code blocks (source code snippets)
- Diagrams (technical diagrams, flowcharts)
- Equations (numbered and unnumbered)
- Matrices and mathematical structures
- Chemical formulas and structures
- Circuit diagrams
- Network diagrams
- UML diagrams
- And more...
"""

import sys
import os
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import json
import time
from datetime import datetime
import re

# Image processing
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available - install with: pip install Pillow")

# PDF processing with PyMuPDF
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available - install with: pip install PyMuPDF")

# Docling for advanced detection
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Warning: Docling not available")


# Comprehensive element types that VLMs can process
class VLMElementType:
    """All element types that can be processed by Vision Language Models."""
    
    # Mathematical elements
    FORMULA_INLINE = "formula_inline"      # Inline math: $...$
    FORMULA_DISPLAY = "formula_display"    # Display math: $$...$$
    EQUATION = "equation"                   # Numbered equations
    MATRIX = "matrix"                       # Mathematical matrices
    PROOF = "proof"                         # Mathematical proofs
    
    # Data structures
    TABLE = "table"                         # Data tables
    TABLE_COMPLEX = "table_complex"        # Multi-level headers, merged cells
    SPREADSHEET = "spreadsheet"            # Spreadsheet-like data
    
    # Visualizations
    CHART_BAR = "chart_bar"                # Bar charts
    CHART_LINE = "chart_line"              # Line charts
    CHART_PIE = "chart_pie"                # Pie charts
    CHART_SCATTER = "chart_scatter"        # Scatter plots
    CHART_HEATMAP = "chart_heatmap"        # Heatmaps
    PLOT_SCIENTIFIC = "plot_scientific"    # Scientific plots
    GRAPH = "graph"                         # Network graphs
    HISTOGRAM = "histogram"                 # Statistical histograms
    
    # Code and algorithms
    CODE_BLOCK = "code_block"              # Source code
    ALGORITHM = "algorithm"                 # Pseudocode algorithms
    TERMINAL = "terminal"                   # Terminal/console output
    
    # Diagrams
    DIAGRAM_FLOW = "diagram_flow"          # Flowcharts
    DIAGRAM_UML = "diagram_uml"            # UML diagrams
    DIAGRAM_CIRCUIT = "diagram_circuit"    # Circuit diagrams
    DIAGRAM_NETWORK = "diagram_network"    # Network topology
    DIAGRAM_ARCH = "diagram_arch"          # Architecture diagrams
    DIAGRAM_SEQUENCE = "diagram_sequence"  # Sequence diagrams
    DIAGRAM_BLOCK = "diagram_block"        # Block diagrams
    DIAGRAM_VENN = "diagram_venn"          # Venn diagrams
    DIAGRAM_TREE = "diagram_tree"          # Tree structures
    
    # Scientific
    CHEMICAL_STRUCTURE = "chemical_struct" # Chemical structures
    CHEMICAL_EQUATION = "chemical_eq"      # Chemical equations
    BIOLOGICAL_DIAGRAM = "bio_diagram"     # Biological diagrams
    PHYSICS_DIAGRAM = "physics_diagram"    # Physics diagrams
    
    # Other processable elements
    TIMELINE = "timeline"                   # Timelines
    MINDMAP = "mindmap"                     # Mind maps
    GANTT_CHART = "gantt"                  # Gantt charts
    
    @classmethod
    def all_types(cls) -> List[str]:
        """Get all element types."""
        return [v for k, v in cls.__dict__.items() if not k.startswith('_') and isinstance(v, str)]


@dataclass
class VisualElement:
    """Represents an extracted visual element."""
    element_id: str                        # Unique identifier
    element_type: str                      # Type from VLMElementType
    page_num: int                          # Page number (1-indexed)
    bbox: Tuple[float, float, float, float]  # Bounding box (x0, y0, x1, y1)
    confidence: float                      # Detection confidence
    image: Optional[Image.Image] = None   # PIL Image object
    text_content: str = ""                 # Any text associated with element
    context: str = ""                      # Surrounding context
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_method: str = ""           # How it was detected
    

class ComprehensiveVisualExtractor:
    """Intelligently extracts meaningful visual elements from PDFs."""
    
    def __init__(self, pdf_path: str, output_dir: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Set up output directory
        pdf_name = self.pdf_path.stem
        self.output_dir = Path(output_dir or "output") / pdf_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear previous extractions
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        
        self.elements: List[VisualElement] = []
        self.stats = {
            "total_pages": 0,
            "elements_by_type": {},
            "extraction_methods": {},
            "filtered_out": 0
        }
        
        # Extraction parameters
        self.min_width = 50    # Minimum width in pixels
        self.min_height = 30   # Minimum height in pixels
        self.min_area = 2000   # Minimum area in square pixels
        self.merge_distance = 20  # Distance for merging nearby elements
        
    def extract_all(self, aggressive: bool = False) -> List[VisualElement]:
        """
        Extract meaningful visual elements from the PDF.
        
        Args:
            aggressive: If True, lower thresholds and extract more aggressively
        """
        print(f"\n{'='*60}")
        print(f"📄 EXTRACTING VISUAL ELEMENTS FROM: {self.pdf_path.name}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⚙️  Mode: {'Aggressive' if aggressive else 'Smart'}")
        print(f"📏 Min size: {self.min_width}x{self.min_height} pixels")
        print(f"{'='*60}\n")
        
        if not PYMUPDF_AVAILABLE:
            print("❌ PyMuPDF is required for extraction")
            return []
        
        # Adjust thresholds for aggressive mode
        if aggressive:
            self.min_width = 30
            self.min_height = 20
            self.min_area = 1000
        
        # Open PDF
        doc = fitz.open(str(self.pdf_path))
        self.stats["total_pages"] = len(doc)
        
        # Method 1: Smart visual region detection (primary method)
        print("🔍 Method 1: Smart visual region detection...")
        self._extract_meaningful_regions(doc)
        
        # Method 2: Docling detection (if available)
        if DOCLING_AVAILABLE:
            print("🔍 Method 2: Docling AI detection...")
            self._extract_with_docling_smart(doc)
        
        # Method 3: Pattern-based detection for formulas and code
        print("🔍 Method 3: Formula and code detection...")
        self._extract_formulas_and_code(doc)
        
        # Method 4: Table structure detection
        print("🔍 Method 4: Table detection...")
        self._extract_tables(doc)
        
        doc.close()
        
        # Post-processing
        self._merge_nearby_elements()
        self._deduplicate_elements()
        self._save_elements()
        self._generate_report()
        
        return self.elements
    
    def _extract_formulas_and_code(self, doc):
        """Extract formulas and code blocks by detecting patterns."""
        for page_num, page in enumerate(doc, 1):
            # Get text blocks with positions for better extraction
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    block_text = ""
                    block_bbox = block["bbox"]
                    
                    # Combine all text in block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            block_text += span.get("text", "")
                    
                    # Check for formula patterns
                    if any(pattern in block_text for pattern in ['$', '\\frac', '\\sum', '\\int', 'equation']):
                        width = block_bbox[2] - block_bbox[0]
                        height = block_bbox[3] - block_bbox[1]
                        
                        if width >= self.min_width and height >= self.min_height:
                            self._extract_region(
                                page, page_num, block_bbox,
                                VLMElementType.FORMULA_DISPLAY,
                                confidence=0.8,
                                method="formula_detection"
                            )
                    
                    # Check for code patterns
                    elif any(pattern in block_text for pattern in ['def ', 'function ', 'class ', 'import ', '{', '}']):
                        # Look for code block characteristics
                        lines = block_text.split('\n')
                        if len(lines) > 3:  # Multi-line code
                            width = block_bbox[2] - block_bbox[0]
                            height = block_bbox[3] - block_bbox[1]
                            
                            if width >= self.min_width and height >= self.min_height:
                                self._extract_region(
                                    page, page_num, block_bbox,
                                    VLMElementType.CODE_BLOCK,
                                    confidence=0.7,
                                    method="code_detection"
                                )
    
    def _extract_meaningful_regions(self, doc):
        """Extract meaningful visual regions, avoiding tiny fragments."""
        for page_num, page in enumerate(doc, 1):
            # Collect all potential regions first
            regions = []
            
            # Get all images on the page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    rects = page.get_image_rects(img[0])
                    if rects:
                        rect = rects[0]
                        width = rect.x1 - rect.x0
                        height = rect.y1 - rect.y0
                        
                        # Filter out tiny images
                        if width >= self.min_width and height >= self.min_height:
                            regions.append({
                                'bbox': (rect.x0, rect.y0, rect.x1, rect.y1),
                                'type': 'image',
                                'confidence': 0.7
                            })
                except Exception:
                    continue
            
            # Get vector graphics and group them
            drawings = page.get_drawings()
            if drawings:
                # Group nearby vector elements
                vector_groups = self._group_vector_elements(drawings)
                for group in vector_groups:
                    width = group['bbox'][2] - group['bbox'][0]
                    height = group['bbox'][3] - group['bbox'][1]
                    
                    # Only add if meaningful size
                    if width >= self.min_width and height >= self.min_height:
                        regions.append({
                            'bbox': group['bbox'],
                            'type': 'vector_group',
                            'confidence': 0.6,
                            'element_count': group['count']
                        })
            
            # Now extract the meaningful regions
            for region in regions:
                element_type = self._classify_region(region)
                if element_type:
                    self._extract_region(
                        page, page_num, region['bbox'],
                        element_type,
                        confidence=region['confidence'],
                        method='smart_visual'
                    )
    
    def _group_vector_elements(self, drawings):
        """Group nearby vector elements into meaningful units."""
        if not drawings:
            return []
        
        groups = []
        used = set()
        
        for i, drawing in enumerate(drawings):
            if i in used or 'rect' not in drawing:
                continue
            
            # Start a new group
            group_bbox = [drawing['rect'].x0, drawing['rect'].y0, 
                         drawing['rect'].x1, drawing['rect'].y1]
            group_items = [i]
            used.add(i)
            
            # Find nearby elements to group
            for j, other in enumerate(drawings):
                if j in used or j == i or 'rect' not in other:
                    continue
                
                # Check if close enough to group
                if self._are_nearby(drawing['rect'], other['rect'], self.merge_distance):
                    group_bbox[0] = min(group_bbox[0], other['rect'].x0)
                    group_bbox[1] = min(group_bbox[1], other['rect'].y0)
                    group_bbox[2] = max(group_bbox[2], other['rect'].x1)
                    group_bbox[3] = max(group_bbox[3], other['rect'].y1)
                    group_items.append(j)
                    used.add(j)
            
            groups.append({
                'bbox': tuple(group_bbox),
                'count': len(group_items)
            })
        
        return groups
    
    def _are_nearby(self, rect1, rect2, threshold):
        """Check if two rectangles are within threshold distance."""
        # Check horizontal distance
        h_dist = min(abs(rect1.x1 - rect2.x0), abs(rect2.x1 - rect1.x0))
        # Check vertical distance
        v_dist = min(abs(rect1.y1 - rect2.y0), abs(rect2.y1 - rect1.y0))
        
        return h_dist <= threshold or v_dist <= threshold
    
    def _classify_region(self, region):
        """Classify a region based on its characteristics."""
        bbox = region['bbox']
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        area = width * height
        aspect = width / height if height > 0 else 1
        
        # Skip if too small
        if area < self.min_area:
            self.stats['filtered_out'] += 1
            return None
        
        # Classification based on shape and size
        if aspect > 3 and height < 100:  # Wide and short
            return VLMElementType.FORMULA_DISPLAY
        elif aspect > 2 and height > 100:  # Wide table
            return VLMElementType.TABLE
        elif 0.8 < aspect < 1.2 and width > 200:  # Large square
            return VLMElementType.DIAGRAM_BLOCK
        elif height > width * 1.5:  # Tall
            return VLMElementType.DIAGRAM_FLOW
        elif region.get('element_count', 0) > 10:  # Many vector elements
            return VLMElementType.CHART_LINE
        else:
            return VLMElementType.CHART_BAR
    
    def _extract_with_docling_smart(self, doc):
        """Use Docling for advanced element detection with smart filtering."""
        try:
            pipeline_options = PdfPipelineOptions(
                do_ocr=False,
                do_table_structure=True,
                table_structure_options={"mode": TableFormerMode.ACCURATE},
                generate_picture_images=True
            )
            
            converter = DocumentConverter(pipeline_options=pipeline_options)
            result = converter.convert(str(self.pdf_path))
            
            if hasattr(result, 'document'):
                docling_doc = result.document
                
                # Process items found by Docling
                for item in docling_doc.iterate_items():
                    if hasattr(item, 'bbox') and item.bbox:
                        bbox = (item.bbox.l, item.bbox.t, item.bbox.r, item.bbox.b)
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        
                        # Skip tiny elements
                        if width < self.min_width or height < self.min_height:
                            self.stats['filtered_out'] += 1
                            continue
                        
                        page_num = getattr(item, 'page_num', 1)
                        
                        # Classify based on Docling's detection
                        class_name = item.__class__.__name__.lower()
                        
                        if 'table' in class_name:
                            element_type = VLMElementType.TABLE
                            confidence = 0.95
                        elif 'formula' in class_name or 'equation' in class_name:
                            element_type = VLMElementType.EQUATION
                            confidence = 0.9
                        elif 'code' in class_name:
                            element_type = VLMElementType.CODE_BLOCK
                            confidence = 0.85
                        elif 'figure' in class_name:
                            # Only extract meaningful figures
                            if width > 100 and height > 100:
                                element_type = VLMElementType.DIAGRAM_BLOCK
                                confidence = 0.7
                            else:
                                continue
                        else:
                            continue  # Skip unknown types
                        
                        # Extract using PyMuPDF
                        page = doc[page_num - 1]
                        self._extract_region(
                            page, page_num, bbox,
                            element_type,
                            confidence=confidence,
                            method="docling"
                        )
                        
        except Exception as e:
            print(f"⚠️ Docling detection error: {e}")
    
    def _extract_tables(self, doc):
        """Extract complete tables by analyzing structure."""
        for page_num, page in enumerate(doc, 1):
            # Get text blocks
            blocks = page.get_text("dict")
            
            # Find potential table regions
            table_regions = []
            
            for i, block in enumerate(blocks.get("blocks", [])):
                if block.get("type") == 0:  # Text block
                    lines = block.get("lines", [])
                    
                    if len(lines) < 2:
                        continue
                    
                    # Analyze for table characteristics
                    has_alignment = False
                    x_positions = set()
                    
                    for line in lines:
                        line_x_positions = []
                        for span in line.get("spans", []):
                            line_x_positions.append(span["bbox"][0])
                        
                        if len(line_x_positions) > 1:
                            x_positions.update(line_x_positions)
                    
                    # Multiple aligned columns suggest a table
                    if len(x_positions) >= 3:
                        has_alignment = True
                    
                    # Check for separators
                    block_text = "".join([span.get("text", "") 
                                         for line in lines 
                                         for span in line.get("spans", [])])
                    
                    has_separators = '|' in block_text or '\t' in block_text
                    
                    if has_alignment or has_separators:
                        table_regions.append(block["bbox"])
            
            # Merge nearby table regions
            merged_tables = self._merge_table_regions(table_regions)
            
            # Extract each table
            for table_bbox in merged_tables:
                width = table_bbox[2] - table_bbox[0]
                height = table_bbox[3] - table_bbox[1]
                
                if width >= self.min_width * 2 and height >= self.min_height * 2:
                    self._extract_region(
                        page, page_num, table_bbox,
                        VLMElementType.TABLE,
                        confidence=0.75,
                        method="table_detection"
                    )
    
    def _merge_table_regions(self, regions):
        """Merge nearby table regions into complete tables."""
        if not regions:
            return []
        
        merged = []
        used = set()
        
        for i, region in enumerate(regions):
            if i in used:
                continue
            
            # Start with this region
            merged_bbox = list(region)
            used.add(i)
            
            # Try to merge with nearby regions
            for j, other in enumerate(regions):
                if j in used or j == i:
                    continue
                
                # Check vertical proximity (for multi-part tables)
                v_dist = abs(other[1] - merged_bbox[3])
                if v_dist < 30:  # Within 30 pixels vertically
                    # Merge
                    merged_bbox[0] = min(merged_bbox[0], other[0])
                    merged_bbox[1] = min(merged_bbox[1], other[1])
                    merged_bbox[2] = max(merged_bbox[2], other[2])
                    merged_bbox[3] = max(merged_bbox[3], other[3])
                    used.add(j)
            
            merged.append(tuple(merged_bbox))
        
        return merged
    
    def _merge_nearby_elements(self):
        """Merge elements that are likely parts of the same visual unit."""
        if len(self.elements) < 2:
            return
        
        print(f"\n🔄 Merging nearby elements...")
        merged_count = 0
        
        # Group by page
        pages = {}
        for elem in self.elements:
            if elem.page_num not in pages:
                pages[elem.page_num] = []
            pages[elem.page_num].append(elem)
        
        # Process each page
        new_elements = []
        for page_num, page_elements in pages.items():
            # Sort by vertical position
            page_elements.sort(key=lambda x: (x.bbox[1], x.bbox[0]))
            
            merged = []
            used = set()
            
            for i, elem in enumerate(page_elements):
                if i in used:
                    continue
                
                # Check if this element should be merged with others
                merge_candidates = []
                for j, other in enumerate(page_elements):
                    if j <= i or j in used:
                        continue
                    
                    # Check if same type and nearby
                    if elem.element_type == other.element_type:
                        v_dist = abs(other.bbox[1] - elem.bbox[3])
                        h_overlap = min(elem.bbox[2], other.bbox[2]) - max(elem.bbox[0], other.bbox[0])
                        
                        # Merge if vertically close and horizontally aligned
                        if v_dist < 30 and h_overlap > 0:
                            merge_candidates.append(j)
                
                if merge_candidates:
                    # Create merged element
                    all_indices = [i] + merge_candidates
                    merged_bbox = list(elem.bbox)
                    
                    for idx in merge_candidates:
                        other = page_elements[idx]
                        merged_bbox[0] = min(merged_bbox[0], other.bbox[0])
                        merged_bbox[1] = min(merged_bbox[1], other.bbox[1])
                        merged_bbox[2] = max(merged_bbox[2], other.bbox[2])
                        merged_bbox[3] = max(merged_bbox[3], other.bbox[3])
                        used.add(idx)
                    
                    elem.bbox = tuple(merged_bbox)
                    merged_count += len(merge_candidates)
                
                new_elements.append(elem)
                used.add(i)
        
        if merged_count > 0:
            print(f"  Merged {merged_count} elements")
            self.elements = new_elements
    
    def _extract_region(self, page, page_num: int, bbox: Tuple[float, float, float, float], 
                        element_type: str, confidence: float = 0.5, method: str = "unknown"):
        """Extract a specific region from the page."""
        try:
            # Create element ID with descriptive naming
            type_abbrev = {
                VLMElementType.FORMULA_INLINE: "FML_INL",
                VLMElementType.FORMULA_DISPLAY: "FML_DSP",
                VLMElementType.EQUATION: "EQN",
                VLMElementType.TABLE: "TBL",
                VLMElementType.CODE_BLOCK: "CODE",
                VLMElementType.CHART_BAR: "CHT_BAR",
                VLMElementType.DIAGRAM_FLOW: "DGM_FLW",
                VLMElementType.ALGORITHM: "ALG",
            }.get(element_type, element_type[:3].upper())
            
            element_id = f"{type_abbrev}_P{page_num:03d}_N{len(self.elements):04d}"
            
            # Extract the image
            rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Increase resolution for better quality
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Save the image
            image_path = self.output_dir / f"{element_id}.png"
            pil_image.save(image_path, "PNG", optimize=True)
            
            # Create element record
            element = VisualElement(
                element_id=element_id,
                element_type=element_type,
                page_num=page_num,
                bbox=bbox,
                confidence=confidence,
                image=pil_image,
                extraction_method=method,
                metadata={
                    "width": int(bbox[2] - bbox[0]),
                    "height": int(bbox[3] - bbox[1]),
                    "file_path": str(image_path)
                }
            )
            
            self.elements.append(element)
            
            # Update stats
            self.stats["elements_by_type"][element_type] = \
                self.stats["elements_by_type"].get(element_type, 0) + 1
            self.stats["extraction_methods"][method] = \
                self.stats["extraction_methods"].get(method, 0) + 1
            
            print(f"  ✅ Extracted: {element_id} ({element_type}) - {method} method")
            
        except Exception as e:
            print(f"  ⚠️ Failed to extract region: {e}")
    
    def _deduplicate_elements(self):
        """Remove duplicate elements based on overlap."""
        if not self.elements:
            return
        
        print(f"\n🔄 Deduplicating {len(self.elements)} elements...")
        
        # Sort by page and confidence
        self.elements.sort(key=lambda x: (x.page_num, -x.confidence))
        
        # Check for overlaps
        unique_elements = []
        for elem in self.elements:
            is_duplicate = False
            
            for unique in unique_elements:
                if unique.page_num == elem.page_num:
                    # Check bbox overlap
                    overlap = self._calculate_overlap(unique.bbox, elem.bbox)
                    if overlap > 0.7:  # 70% overlap threshold
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_elements.append(elem)
        
        removed = len(self.elements) - len(unique_elements)
        if removed > 0:
            print(f"  Removed {removed} duplicate elements")
        
        self.elements = unique_elements
    
    def _calculate_overlap(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """Calculate overlap ratio between two bboxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        return intersection / min(area1, area2)
    
    def _save_elements(self):
        """Save element metadata to JSON."""
        metadata = {
            "source_pdf": str(self.pdf_path),
            "extraction_time": datetime.now().isoformat(),
            "total_elements": len(self.elements),
            "stats": self.stats,
            "elements": []
        }
        
        for elem in self.elements:
            metadata["elements"].append({
                "id": elem.element_id,
                "type": elem.element_type,
                "page": elem.page_num,
                "bbox": elem.bbox,
                "confidence": elem.confidence,
                "method": elem.extraction_method,
                "metadata": elem.metadata
            })
        
        json_path = self.output_dir / "extraction_metadata.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Saved metadata to: {json_path}")
    
    def _generate_report(self):
        """Generate a markdown report of the extraction."""
        report_path = self.output_dir / "extraction_report.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Visual Element Extraction Report\n\n")
            f.write(f"**Source:** `{self.pdf_path.name}`\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Pages:** {self.stats['total_pages']}\n")
            f.write(f"**Total Elements:** {len(self.elements)}\n\n")
            
            f.write("## Summary by Element Type\n\n")
            f.write("| Element Type | Count |\n")
            f.write("|-------------|-------|\n")
            for elem_type, count in sorted(self.stats["elements_by_type"].items()):
                f.write(f"| {elem_type} | {count} |\n")
            
            f.write("\n## Extraction Methods Used\n\n")
            f.write("| Method | Elements Found |\n")
            f.write("|--------|---------------|\n")
            for method, count in sorted(self.stats["extraction_methods"].items()):
                f.write(f"| {method} | {count} |\n")
            
            f.write("\n## Extracted Elements\n\n")
            
            current_page = 0
            for elem in sorted(self.elements, key=lambda x: (x.page_num, x.bbox[1])):
                if elem.page_num != current_page:
                    current_page = elem.page_num
                    f.write(f"\n### Page {current_page}\n\n")
                
                f.write(f"#### {elem.element_id}\n")
                f.write(f"- **Type:** {elem.element_type}\n")
                f.write(f"- **Confidence:** {elem.confidence:.2f}\n")
                f.write(f"- **Method:** {elem.extraction_method}\n")
                f.write(f"- **Dimensions:** {elem.metadata.get('width', 0)}x{elem.metadata.get('height', 0)}\n")
                f.write(f"- **Image:** [{elem.element_id}.png]({elem.element_id}.png)\n\n")
        
        print(f"📝 Generated report: {report_path}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python extract_all_visual_elements.py <pdf_file> [--aggressive]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    aggressive = "--aggressive" in sys.argv
    
    # Extract all visual elements
    extractor = ComprehensiveVisualExtractor(pdf_path)
    elements = extractor.extract_all(aggressive=aggressive)
    
    print(f"\n{'='*60}")
    print(f"✅ EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Total elements extracted: {len(elements)}")
    print(f"📁 Output directory: {extractor.output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()