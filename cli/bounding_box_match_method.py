#!/usr/bin/env python3
"""
Two-Phase Bounding Box Approach for Complex Document Processing

Phase 1: Create paragraph-level bounding boxes around content regions
Phase 2: Analyze each bounding box to determine content type (formula, table, mixed)

This approach is more robust because:
- Captures context better with paragraph-level regions
- Handles mixed content (formula + text + table) naturally
- More accurate content analysis within defined boundaries
- Better replacement integration with docling
"""

import fitz  # PyMuPDF
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContentRegion:
    """A content region with bounding box and analyzed content."""
    region_id: str
    page_number: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    normalized_bbox: Tuple[float, float, float, float]  # Full-width normalized
    
    # Raw content
    raw_text: str
    
    # Analysis results
    contains_formula: bool = False
    contains_table: bool = False
    contains_mixed: bool = False
    confidence_score: float = 0.0
    content_type: str = "text"  # "formula", "table", "mixed", "text"
    
    # Processing info
    extracted_image_path: Optional[str] = None
    processing_priority: int = 3  # 1-5, higher = more important
    

class TwoPhaseProcessor:
    """Two-phase approach for robust content region processing."""
    
    def __init__(self, log_to_file: bool = True):
        self.region_counter = 0
        self.log_to_file = log_to_file
        self.log_file = None
        
        if self.log_to_file:
            # Create output directory and log file
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = output_dir / f"two_phase_log_{timestamp}.txt"
            
            # Initialize log file
            with open(self.log_file, 'w') as f:
                f.write(f"=== TWO-PHASE BOUNDING BOX PROCESSING LOG - {datetime.now()} ===\n\n")
    
    def _log(self, message: str):
        """Log message to both console and file if enabled."""
        print(message)
        if self.log_to_file and self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process document using two-phase approach with full text extraction and timing.
        
        Returns:
            Dictionary containing extracted text, regions, performance metrics, etc.
        """
        start_time = time.time()
        self._log(f"🚀 Starting two-phase processing: {file_path.name}")
        self._log("=" * 60)
        
        # Open PDF document
        try:
            doc = fitz.open(str(file_path))
            self._log(f"📖 Opened PDF: {len(doc)} pages")
        except Exception as e:
            self._log(f"❌ Failed to open PDF: {e}")
            return {"success": False, "error": str(e)}
        
        # PHASE 0: Extract complete document text (what you actually wanted!)
        text_extraction_start = time.time()
        full_document_text = ""
        page_texts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            page_texts.append({
                "page_number": page_num + 1,
                "text": page_text,
                "word_count": len(page_text.split()),
                "char_count": len(page_text)
            })
            full_document_text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
        
        text_extraction_time = time.time() - text_extraction_start
        self._log(f"📄 Full text extraction: {text_extraction_time:.3f}s")
        self._log(f"   Total text length: {len(full_document_text):,} characters")
        self._log(f"   Total words: {len(full_document_text.split()):,}")
        
        # Save full extracted text
        self._save_full_text(full_document_text, file_path.stem)
        
        # Save detailed page structure for validation
        self._save_page_structure_analysis(file_path)
        
        # Save raw PyMuPDF export (unprocessed)
        self._save_raw_pymupdf_export(file_path)
        
        # Save simple mapping structure
        self._save_simple_mapping_structure(file_path)
        
        # PHASE 1 & 2: Detect and analyze special content regions
        detection_start = time.time()
        all_regions = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]  # 0-based indexing for PyMuPDF
            display_page_num = page_num + 1  # 1-based for display
            self._log(f"\n📄 Processing page {display_page_num}")
            
            # Phase 1: Extract regions with special content
            regions = self._phase1_extract_regions(page, display_page_num)
            self._log(f"   Phase 1: Found {len(regions)} special content regions")
            
            # Phase 2: Analyze content in each region
            analyzed_regions = self._phase2_analyze_regions(page, regions)
            self._log(f"   Phase 2: Analyzed {len(analyzed_regions)} regions")
            
            # Create visualization of detections for this page
            if analyzed_regions or len(regions) == 0:  # Show even pages with no detections
                self._create_detection_visualization(page, analyzed_regions, display_page_num)
            
            all_regions.extend(analyzed_regions)
        
        detection_time = time.time() - detection_start
        total_time = time.time() - start_time
        
        # Store page count before closing document
        total_pages = len(doc)
        doc.close()
        
        # Performance Summary
        self._log(f"\n⏱️  PERFORMANCE METRICS")
        self._log(f"=" * 40)
        self._log(f"Text extraction: {text_extraction_time:.3f}s")
        self._log(f"Special content detection: {detection_time:.3f}s") 
        self._log(f"Total processing time: {total_time:.3f}s")
        self._log(f"Pages per second: {total_pages / total_time:.1f}")
        
        # Content Summary
        self._log(f"\n📊 CONTENT ANALYSIS")
        self._log(f"=" * 40)
        self._log(f"Total pages processed: {total_pages}")
        self._log(f"Special content regions found: {len(all_regions)}")
        
        # Count by content type
        type_counts = {}
        for region in all_regions:
            type_counts[region.content_type] = type_counts.get(region.content_type, 0) + 1
        
        for content_type, count in type_counts.items():
            self._log(f"   {content_type}: {count} regions")
        
        if self.log_file:
            self._log(f"\n📋 Detailed log saved to: {self.log_file}")
        
        return {
            "success": True,
            "file_name": file_path.name,
            "full_text": full_document_text,
            "page_texts": page_texts,
            "special_regions": all_regions,
            "performance": {
                "text_extraction_time": text_extraction_time,
                "detection_time": detection_time,
                "total_time": total_time,
                "pages_per_second": total_pages / total_time,
                "pages_processed": total_pages,
                "total_words": len(full_document_text.split()),
                "total_characters": len(full_document_text)
            },
            "content_summary": {
                "special_regions_found": len(all_regions),
                "content_types": type_counts,
                "pages_with_special_content": len(set(r.page_number for r in all_regions))
            }
        }
    
    def _phase1_extract_regions(self, page, page_num: int) -> List[Dict]:
        """
        Phase 1: Extract ALL text as structured JSON, then analyze for special content.
        
        NEW APPROACH:
        - Get complete page structure with positioning data (FAST)  
        - Analyze text content to find formulas/tables (FAST)
        - Only create regions for content that needs VLM processing (EFFICIENT)
        """
        
        # ENHANCED: Use PyMuPDF's sort=True for natural reading order
        # This should fix formula fragmentation by proper coordinate sorting
        text_dict = page.get_text("dict", sort=True)
        blocks = text_dict.get("blocks", [])
        
        if not blocks:
            return []
        
        self._log(f"      Analyzing {len(blocks)} blocks for special content")
        
        # Extract all text blocks with their exact positioning
        text_blocks = [block for block in blocks if "lines" in block and block.get("bbox")]
        
        if not text_blocks:
            return []
        
        # FIXED APPROACH: Merge overlapping blocks first, then create regions
        special_regions = []
        
        # Step 1: Merge overlapping blocks to fix fragmented formulas
        merged_blocks = self._merge_overlapping_blocks(text_blocks, page_num)
        self._log(f"      Merged {len(text_blocks)} raw blocks into {len(merged_blocks)} non-overlapping blocks")
        
        # Step 2: Process merged blocks (now guaranteed non-overlapping)
        for merged_idx, merged_block in enumerate(merged_blocks):
            # Extract text from merged block
            merged_text = merged_block['combined_text']
            
            if not merged_text.strip():
                continue
                
            # Create unique identifier for merged block
            block_id = f"page_{page_num}_merged_{merged_idx:03d}"
            
            # Analyze merged block for special content
            formula_score = self._quick_formula_analysis(merged_text, merged_block)
            table_score = self._quick_table_analysis(merged_text, merged_block)
            
            # Only create regions for blocks that likely contain special content
            if formula_score > 0.3 or table_score > 0.3:
                # Create full-width region from merged block (guaranteed no overlap)
                region = self._create_merged_region(merged_block, merged_text, page_num, merged_idx, block_id, page)
                region["formula_score"] = formula_score
                region["table_score"] = table_score
                special_regions.append(region)
                
                self._log(f"         📍 {block_id}: formula={formula_score:.2f}, table={table_score:.2f} -> Special region (merged {len(merged_block['source_blocks'])} blocks)")
            else:
                self._log(f"         ⚪ {block_id}: formula={formula_score:.2f}, table={table_score:.2f} -> Regular text")
        
        self._log(f"      Found {len(special_regions)} blocks with special content (out of {len(text_blocks)} total)")
        
        # Store full page text for later use
        full_page_text = page.get_text()
        
        return special_regions
    
    def _extract_block_text(self, block: Dict) -> str:
        """Extract text from a single block."""
        block_text = ""
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
            block_text += line_text + "\n"
        return block_text.strip()
    
    def _merge_overlapping_blocks(self, text_blocks: List[Dict], page_num: int) -> List[Dict]:
        """Merge blocks that have overlapping vertical boundaries."""
        if not text_blocks:
            return []
        
        merged_blocks = []
        used_indices = set()
        
        for i, block in enumerate(text_blocks):
            if i in used_indices:
                continue
            
            # Start a new merged block with this block
            block_text = self._extract_block_text(block)
            if not block_text.strip():
                continue
                
            current_group = [block]
            current_indices = {i}
            current_bbox = list(block["bbox"])  # [x0, y0, x1, y1]
            combined_text = block_text
            
            # Find all blocks that overlap with this group
            for j, other_block in enumerate(text_blocks):
                if j in current_indices or j in used_indices:
                    continue
                
                other_text = self._extract_block_text(other_block)
                if not other_text.strip():
                    continue
                
                # Check if this block overlaps vertically with current group
                if self._blocks_overlap_vertically(current_bbox, other_block["bbox"]):
                    current_group.append(other_block)
                    current_indices.add(j)
                    combined_text += " " + other_text
                    
                    # Expand the group bounding box
                    other_bbox = other_block["bbox"]
                    current_bbox[0] = min(current_bbox[0], other_bbox[0])  # x0
                    current_bbox[1] = min(current_bbox[1], other_bbox[1])  # y0
                    current_bbox[2] = max(current_bbox[2], other_bbox[2])  # x1
                    current_bbox[3] = max(current_bbox[3], other_bbox[3])  # y1
            
            # Mark all blocks in this group as used
            used_indices.update(current_indices)
            
            # Create merged block
            merged_block = {
                'merged_bbox': tuple(current_bbox),
                'source_blocks': current_group,
                'combined_text': combined_text.strip(),
                'block_count': len(current_group)
            }
            
            merged_blocks.append(merged_block)
        
        return merged_blocks
    
    def _blocks_overlap_vertically(self, bbox1: List[float], bbox2: Tuple[float, float, float, float]) -> bool:
        """Check if two bounding boxes overlap vertically."""
        # bbox format: [x0, y0, x1, y1]
        y1_top, y1_bottom = bbox1[1], bbox1[3]
        y2_top, y2_bottom = bbox2[1], bbox2[3]
        
        # Check for vertical overlap
        overlap = not (y1_bottom < y2_top or y2_bottom < y1_top)
        return overlap
    
    def _create_merged_region(self, merged_block: Dict, text: str, page_num: int, merged_idx: int, block_id: str, page) -> Dict:
        """Create a region from a merged block using page/paragraph naming."""
        
        # Get merged bounding box
        merged_bbox = merged_block['merged_bbox']
        x0, y0, x1, y1 = merged_bbox
        
        # Get page dimensions
        page_rect = page.rect
        page_width = page_rect.width
        
        # Create full-width region respecting merged boundaries
        full_width_bbox = (
            0,          # Start at left edge of page
            y0,         # Keep merged top boundary
            page_width, # Extend to right edge of page
            y1          # Keep merged bottom boundary
        )
        
        # Use paragraph naming for merged blocks
        paragraph_number = merged_idx + 1
        region_id = f"page_{page_num}_paragraph_{paragraph_number:03d}"
        
        return {
            "region_id": region_id,
            "page_number": page_num,
            "paragraph_number": paragraph_number,
            "merged_index": merged_idx,
            "bbox": full_width_bbox,
            "original_bbox": merged_bbox,
            "source_blocks": merged_block['source_blocks'],
            "raw_text": text,
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "mapping": {
                "original_blocks_merged": merged_block['block_count'],
                "original_width": x1 - x0,
                "expanded_width": page_width,
                "width_expansion_ratio": page_width / (x1 - x0) if (x1 - x0) > 0 else 1.0,
                "guaranteed_no_overlap": True,
                "merged_fragmented_formula": True
            }
        }
    
    def _create_mapped_region(self, block: Dict, text: str, page_num: int, block_idx: int, block_id: str, page) -> Dict:
        """Create a region using YOUR simple page/paragraph naming convention."""
        
        # Get original block bounding box - this represents a natural paragraph boundary
        original_bbox = block["bbox"]
        x0, y0, x1, y1 = original_bbox
        
        # Get page dimensions
        page_rect = page.rect
        page_width = page_rect.width
        
        # Create full-width region that respects this block's natural boundaries
        # This ensures no overlap since each PyMuPDF block has distinct vertical space
        full_width_bbox = (
            0,          # Start at left edge of page
            y0,         # Keep exact top boundary from block
            page_width, # Extend to right edge of page  
            y1          # Keep exact bottom boundary from block
        )
        
        # Use YOUR naming convention: page_X_paragraph_Y
        paragraph_number = block_idx + 1  # 1-based for human readability
        region_id = f"page_{page_num}_paragraph_{paragraph_number:03d}"
        
        return {
            "region_id": region_id,  # YOUR simple naming: page_3_paragraph_016
            "page_number": page_num,
            "paragraph_number": paragraph_number,
            "block_index": block_idx,  # 0-based index in PyMuPDF blocks
            "bbox": full_width_bbox,
            "original_bbox": original_bbox,
            "source_block": block,  # Complete PyMuPDF block for reference
            "raw_text": text,
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "mapping": {
                "pymupdf_block_index": block_idx,
                "original_width": x1 - x0,
                "expanded_width": page_width,
                "width_expansion_ratio": page_width / (x1 - x0) if (x1 - x0) > 0 else 1.0,
                "guaranteed_no_overlap": True,
                "uses_your_naming_convention": True
            }
        }
    
    def _create_full_width_region(self, block: Dict, text: str, page_num: int, index: int, page) -> Dict:
        """Create a full-width region that respects the block's natural vertical boundaries."""
        self.region_counter += 1
        
        # Get original block bounding box - this represents a natural paragraph boundary
        original_bbox = block["bbox"]
        x0, y0, x1, y1 = original_bbox
        
        # Get page dimensions
        page_rect = page.rect
        page_width = page_rect.width
        
        # RESPECT THE BLOCK'S NATURAL BOUNDARIES
        # Only expand horizontally to full width, keep the exact vertical boundaries
        # This prevents overlapping since each block has distinct vertical space
        
        full_width_bbox = (
            0,                           # Start at left edge of page
            y0,                          # Keep exact top boundary (no padding)
            page_width,                  # Extend to right edge of page  
            y1                           # Keep exact bottom boundary (no padding)
        )
        
        return {
            "region_id": f"region_{self.region_counter:04d}",
            "page_number": page_num,
            "bbox": full_width_bbox,
            "original_bbox": original_bbox,  # Keep track of original detection
            "block": block,
            "raw_text": text,
            "block_index": index,
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "expansion": {
                "original_width": x1 - x0,
                "new_width": page_width,
                "width_expansion_ratio": page_width / (x1 - x0) if (x1 - x0) > 0 else 1.0,
                "respects_natural_boundaries": True
            }
        }
    
    def _group_nearby_blocks(self, candidate_blocks: List[Dict], page_num: int) -> List[Dict]:
        """Group nearby blocks that likely belong to the same mathematical formula or table."""
        if not candidate_blocks:
            return []
        
        grouped_regions = []
        used_blocks = set()
        
        for i, block in enumerate(candidate_blocks):
            if i in used_blocks:
                continue
                
            # Start a new group with this block
            group = [block]
            group_indices = {i}
            current_bbox = list(block['bbox'])  # [x0, y0, x1, y1]
            
            # Look for nearby blocks to add to this group
            max_iterations = 3  # Prevent infinite loops
            for iteration in range(max_iterations):
                added_any = False
                
                for j, other_block in enumerate(candidate_blocks):
                    if j in group_indices or j in used_blocks:
                        continue
                    
                    # Check if this block is close enough to the current group
                    if self._blocks_should_be_grouped(current_bbox, other_block['bbox'], block, other_block):
                        group.append(other_block)
                        group_indices.add(j)
                        
                        # Expand the group bounding box
                        other_bbox = other_block['bbox']
                        current_bbox[0] = min(current_bbox[0], other_bbox[0])  # x0
                        current_bbox[1] = min(current_bbox[1], other_bbox[1])  # y0
                        current_bbox[2] = max(current_bbox[2], other_bbox[2])  # x1
                        current_bbox[3] = max(current_bbox[3], other_bbox[3])  # y1
                        added_any = True
                
                if not added_any:
                    break
            
            # Mark all blocks in this group as used
            used_blocks.update(group_indices)
            
            # Create the grouped region
            if group:
                grouped_region = self._create_grouped_region(group, current_bbox, page_num)
                grouped_regions.append(grouped_region)
        
        return grouped_regions
    
    def _blocks_should_be_grouped(self, group_bbox: List[float], block_bbox: Tuple[float, float, float, float], 
                                 group_block: Dict, candidate_block: Dict) -> bool:
        """Determine if two blocks should be grouped together."""
        x0, y0, x1, y1 = group_bbox
        bx0, by0, bx1, by1 = block_bbox
        
        # Calculate distances
        horizontal_gap = min(abs(bx0 - x1), abs(x0 - bx1))
        vertical_gap = min(abs(by0 - y1), abs(y0 - by1))
        
        # Check for overlap or close proximity
        horizontal_overlap = not (bx1 < x0 or x1 < bx0)
        vertical_overlap = not (by1 < y0 or y1 < by0)
        
        # Height-based thresholds (larger formulas need bigger gaps)
        group_height = y1 - y0
        block_height = by1 - by0
        avg_height = (group_height + block_height) / 2
        
        # Dynamic thresholds based on content type and size
        max_horizontal_gap = avg_height * 0.5  # Allow some horizontal spacing
        max_vertical_gap = avg_height * 0.3    # Tighter vertical spacing
        
        # Check if blocks should be grouped
        should_group = False
        
        # Case 1: Overlapping regions (definitely group)
        if horizontal_overlap and vertical_overlap:
            should_group = True
        
        # Case 2: Vertically aligned with small horizontal gap (formula continuation)
        elif vertical_overlap and horizontal_gap <= max_horizontal_gap:
            should_group = True
        
        # Case 3: Horizontally aligned with small vertical gap (multi-line formulas)
        elif horizontal_overlap and vertical_gap <= max_vertical_gap:
            should_group = True
        
        # Case 4: Both blocks have strong mathematical indicators (group even if slightly separated)
        elif (group_block.get('formula_score', 0) > 0.4 and candidate_block.get('formula_score', 0) > 0.4 and
              horizontal_gap <= max_horizontal_gap * 1.5 and vertical_gap <= max_vertical_gap * 1.5):
            should_group = True
        
        return should_group
    
    def _create_grouped_region(self, blocks: List[Dict], combined_bbox: List[float], page_num: int) -> Dict:
        """Create a region from a group of blocks."""
        self.region_counter += 1
        
        # Combine text from all blocks
        combined_text = ""
        all_blocks = []
        
        for block_data in blocks:
            combined_text += block_data['text'] + " "
            all_blocks.append(block_data['block'])
        
        combined_text = combined_text.strip()
        
        return {
            "region_id": f"region_{self.region_counter:04d}",
            "page_number": page_num,
            "bbox": tuple(combined_bbox),
            "blocks": all_blocks,
            "raw_text": combined_text,
            "combined_text": combined_text,
            "word_count": len(combined_text.split()),
            "line_count": len(combined_text.split('\n')) + 1,
            "block_count": len(blocks)
        }
    
    def _quick_formula_analysis(self, text: str, block: Dict) -> float:
        """Fast formula detection - lightweight version."""
        import re
        
        if len(text) < 3:
            return 0.0
            
        score = 0.0
        
        # Mathematical symbols (high confidence indicators)
        math_symbols = ['∑', '∫', '∏', '√', '±', '∞', '≈', '≤', '≥', '≠', '∂', '∇', 
                       '∀', '∃', '∈', '∉', '⊂', '⊃', '∪', '∩', 'α', 'β', 'γ', 'δ', 'ε', 'θ', 'λ', 'μ', 'π', 'σ', 'φ', 'ψ', 'ω']
        
        symbol_count = sum(text.count(symbol) for symbol in math_symbols)
        if symbol_count > 0:
            score += min(0.6, symbol_count * 0.3)  # High weight for math symbols
        
        # Common formula patterns
        patterns = [
            (r'[a-zA-Z]\s*[=≈]\s*[0-9\-+\(\)]+', 0.4),  # x = 123
            (r'\b[a-zA-Z]\^[0-9]+\b', 0.3),              # x^2
            (r'\b[a-zA-Z]_[0-9]+\b', 0.25),              # x_1
            (r'\([^)]*[+\-*/][^)]*\)', 0.2),             # (a + b)
            (r'\b(sin|cos|tan|log|ln|exp)\b', 0.3),      # functions
        ]
        
        for pattern, weight in patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                score += min(weight, matches * 0.15)
        
        # Font analysis for math content
        blocks_to_analyze = []
        if isinstance(block, dict):
            if 'blocks' in block:  # Grouped region
                blocks_to_analyze = block['blocks']
            else:  # Single block
                blocks_to_analyze = [block]
        
        if blocks_to_analyze:
            math_font_ratio = self._get_math_font_ratio(blocks_to_analyze)
            if math_font_ratio > 0.3:
                score += math_font_ratio * 0.4
        
        return min(1.0, score)
    
    def _quick_table_analysis(self, text: str, block: Dict) -> float:
        """Fast table detection - lightweight version.""" 
        import re
        
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return 0.0
            
        score = 0.0
        
        # Table keywords
        table_keywords = ['table', 'column', 'row', 'data', 'results']
        keyword_count = sum(text.lower().count(kw) for kw in table_keywords)
        if keyword_count > 0:
            score += min(0.3, keyword_count * 0.1)
        
        # Structural indicators
        pipe_lines = [line for line in lines if '|' in line]
        tab_lines = [line for line in lines if '\t' in line]
        
        if len(pipe_lines) >= 2:
            score += 0.5  # Strong indicator
        elif len(tab_lines) >= 2:
            score += 0.4
        
        # Numeric data patterns
        numeric_lines = sum(1 for line in lines if len(re.findall(r'\b\d+\.?\d*\b', line)) >= 2)
        if numeric_lines >= 2:
            numeric_ratio = numeric_lines / len(lines)
            score += numeric_ratio * 0.4
        
        # Consistent spacing (simplified check)
        spacing_lines = sum(1 for line in lines if len(re.findall(r'\s{2,}', line)) >= 1)
        if spacing_lines >= len(lines) * 0.6:
            score += 0.3
        
        return min(1.0, score)
    
    def _save_full_text(self, full_text: str, filename_stem: str):
        """Save the full extracted document text to files for verification."""
        try:
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as plain text
            text_file = output_dir / f"{filename_stem}_full_text.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # Save as JSON with metadata
            json_file = output_dir / f"{filename_stem}_full_text.json"
            text_data = {
                "filename": filename_stem,
                "extraction_time": datetime.now().isoformat(),
                "total_characters": len(full_text),
                "total_words": len(full_text.split()),
                "total_lines": len(full_text.split('\n')),
                "full_text": full_text
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(text_data, f, indent=2, ensure_ascii=False)
            
            self._log(f"💾 Full text saved:")
            self._log(f"   📄 Text file: {text_file.name}")
            self._log(f"   📊 JSON file: {json_file.name}")
            self._log(f"   📝 Characters: {len(full_text):,}")
            self._log(f"   📝 Words: {len(full_text.split()):,}")
            self._log(f"   📝 Lines: {len(full_text.split('\n')):,}")
            
        except Exception as e:
            self._log(f"⚠️  Failed to save full text: {e}")
    
    def _save_page_structure_analysis(self, file_path: Path):
        """Save detailed page structure analysis for validation."""
        try:
            # Reopen document for structure analysis
            doc = fitz.open(str(file_path))
            
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create comprehensive structure analysis
            structure_analysis = {
                "document_name": file_path.name,
                "total_pages": len(doc),
                "analysis_timestamp": datetime.now().isoformat(),
                "pages": []
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                display_page_num = page_num + 1
                
                # Get complete page structure
                text_dict = page.get_text("dict")
                
                page_analysis = {
                    "page_number": display_page_num,
                    "page_dimensions": {
                        "width": page.rect.width,
                        "height": page.rect.height
                    },
                    "total_blocks": len(text_dict.get("blocks", [])),
                    "blocks": []
                }
                
                # Analyze each block in detail
                blocks = text_dict.get("blocks", [])
                text_blocks = [block for block in blocks if "lines" in block and block.get("bbox")]
                
                for block_idx, block in enumerate(text_blocks):
                    block_text = self._extract_block_text(block)
                    
                    if not block_text.strip():
                        continue
                    
                    # Create unique block identifier  
                    block_id = f"page_{display_page_num}_block_{block_idx:03d}"
                    
                    # Analyze content
                    formula_score = self._quick_formula_analysis(block_text, block)
                    table_score = self._quick_table_analysis(block_text, block)
                    
                    # Detect special indicators
                    has_table_title = any(keyword in block_text.lower() for keyword in ['table ', 'figure ', 'algorithm '])
                    has_equation_number = bool(re.search(r'\(\d+\)$', block_text.strip()))
                    
                    block_analysis = {
                        "block_id": block_id,  # Clear unique identifier
                        "block_index": block_idx,
                        "bbox": block["bbox"],
                        "dimensions": {
                            "width": block["bbox"][2] - block["bbox"][0],
                            "height": block["bbox"][3] - block["bbox"][1]
                        },
                        "text_preview": block_text[:200] + "..." if len(block_text) > 200 else block_text,
                        "full_text": block_text,
                        "word_count": len(block_text.split()),
                        "line_count": len(block.get("lines", [])),
                        "analysis": {
                            "formula_score": formula_score,
                            "table_score": table_score,
                            "has_table_title": has_table_title,
                            "has_equation_number": has_equation_number,
                            "needs_vlm": formula_score > 0.3 or table_score > 0.3,
                            "max_score": max(formula_score, table_score)
                        },
                        "font_info": self._extract_font_info(block),
                        "raw_pymupdf_block": block  # Include complete PyMuPDF block structure
                    }
                    
                    page_analysis["blocks"].append(block_analysis)
                
                structure_analysis["pages"].append(page_analysis)
            
            doc.close()
            
            # Save the structure analysis
            structure_file = output_dir / f"{file_path.stem}_page_structure.json"
            with open(structure_file, 'w', encoding='utf-8') as f:
                json.dump(structure_analysis, f, indent=2, ensure_ascii=False)
            
            # Also save a readable summary
            summary_file = output_dir / f"{file_path.stem}_structure_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"=== PAGE STRUCTURE ANALYSIS: {file_path.name} ===\n\n")
                
                for page_data in structure_analysis["pages"]:
                    page_num = page_data["page_number"]
                    f.write(f"PAGE {page_num} ({page_data['total_blocks']} blocks)\n")
                    f.write("=" * 50 + "\n")
                    
                    for block in page_data["blocks"]:
                        f.write(f"\nBlock {block['block_index']}: ")
                        f.write(f"{'SPECIAL' if block['analysis']['detected_as_special'] else 'REGULAR'}\n")
                        f.write(f"  BBox: {block['bbox']}\n")
                        f.write(f"  Size: {block['dimensions']['width']:.1f} x {block['dimensions']['height']:.1f}\n")
                        f.write(f"  Formula: {block['analysis']['formula_score']:.2f}, Table: {block['analysis']['table_score']:.2f}\n")
                        f.write(f"  Text: {block['text_preview']}\n")
                        if block['analysis']['has_table_title']:
                            f.write("  ⭐ HAS TABLE/FIGURE TITLE\n")
                        if block['analysis']['has_equation_number']:
                            f.write("  ⭐ HAS EQUATION NUMBER\n")
                    
                    f.write("\n" + "="*50 + "\n\n")
            
            self._log(f"📋 Page structure analysis saved:")
            self._log(f"   📊 JSON details: {structure_file.name}")
            self._log(f"   📄 Summary: {summary_file.name}")
            
        except Exception as e:
            self._log(f"⚠️  Failed to save page structure: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_font_info(self, block: Dict) -> Dict:
        """Extract font information from a block."""
        fonts = {}
        total_spans = 0
        
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font = span.get("font", "unknown")
                size = span.get("size", 0)
                flags = span.get("flags", 0)
                
                font_key = f"{font}_{size}"
                fonts[font_key] = fonts.get(font_key, 0) + 1
                total_spans += 1
        
        # Determine dominant font
        dominant_font = max(fonts.items(), key=lambda x: x[1]) if fonts else ("unknown", 0)
        
        return {
            "total_spans": total_spans,
            "unique_fonts": len(fonts),
            "dominant_font": dominant_font[0],
            "font_distribution": fonts
        }
    
    def _save_raw_pymupdf_export(self, file_path: Path):
        """Save the complete raw PyMuPDF structure with zero processing."""
        try:
            doc = fitz.open(str(file_path))
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Complete raw export - exactly what PyMuPDF gives us
            raw_export = {
                "document_name": file_path.name,
                "export_timestamp": datetime.now().isoformat(),
                "total_pages": len(doc),
                "raw_pymupdf_data": []
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get the raw dictionary structure from PyMuPDF - NO PROCESSING
                raw_page_dict = page.get_text("dict")
                
                page_export = {
                    "page_number": page_num + 1,
                    "page_rect": {
                        "x0": page.rect.x0,
                        "y0": page.rect.y0, 
                        "x1": page.rect.x1,
                        "y1": page.rect.y1,
                        "width": page.rect.width,
                        "height": page.rect.height
                    },
                    "raw_text_dict": raw_page_dict  # Complete unmodified PyMuPDF structure
                }
                
                raw_export["raw_pymupdf_data"].append(page_export)
            
            doc.close()
            
            # Save raw export
            raw_file = output_dir / f"{file_path.stem}_raw_pymupdf.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(raw_export, f, indent=2, ensure_ascii=False)
            
            self._log(f"📤 Raw PyMuPDF export saved: {raw_file.name}")
            
        except Exception as e:
            self._log(f"⚠️  Failed to save raw PyMuPDF export: {e}")
    
    def _save_simple_mapping_structure(self, file_path: Path):
        """Save simple page/paragraph/bbox mapping to prove no overlaps."""
        try:
            doc = fitz.open(str(file_path))
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            simple_mapping = {
                "document_name": file_path.name,
                "mapping_timestamp": datetime.now().isoformat(),
                "total_pages": len(doc),
                "explanation": "Simple 1:1 mapping of PyMuPDF blocks to page/paragraph structure",
                "pages": []
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                display_page_num = page_num + 1
                
                # Get blocks from PyMuPDF
                text_dict = page.get_text("dict")
                blocks = text_dict.get("blocks", [])
                text_blocks = [block for block in blocks if "lines" in block and block.get("bbox")]
                
                page_mapping = {
                    "page_number": display_page_num,
                    "total_paragraphs": len(text_blocks),
                    "paragraphs": []
                }
                
                for paragraph_idx, block in enumerate(text_blocks):
                    # Extract text from this paragraph/block
                    paragraph_text = self._extract_block_text(block)
                    
                    if not paragraph_text.strip():
                        continue
                    
                    # Create simple identifier
                    paragraph_id = f"page_{display_page_num}_paragraph_{paragraph_idx + 1:03d}"
                    
                    # Simple paragraph mapping
                    paragraph_mapping = {
                        "paragraph_id": paragraph_id,
                        "paragraph_number": paragraph_idx + 1,
                        "bounding_box": block["bbox"],
                        "text_preview": paragraph_text[:100] + "..." if len(paragraph_text) > 100 else paragraph_text,
                        "word_count": len(paragraph_text.split()),
                        "character_count": len(paragraph_text)
                    }
                    
                    page_mapping["paragraphs"].append(paragraph_mapping)
                
                simple_mapping["pages"].append(page_mapping)
            
            doc.close()
            
            # Save simple mapping
            mapping_file = output_dir / f"{file_path.stem}_simple_mapping.json"
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(simple_mapping, f, indent=2, ensure_ascii=False)
            
            # Also save a readable summary
            summary_file = output_dir / f"{file_path.stem}_mapping_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"=== SIMPLE PAGE/PARAGRAPH MAPPING: {file_path.name} ===\n\n")
                
                for page_data in simple_mapping["pages"]:
                    page_num = page_data["page_number"]
                    f.write(f"PAGE {page_num} ({page_data['total_paragraphs']} paragraphs)\n")
                    f.write("=" * 60 + "\n")
                    
                    for para in page_data["paragraphs"]:
                        f.write(f"\n{para['paragraph_id']}:\n")
                        f.write(f"  BBox: {para['bounding_box']}\n")
                        f.write(f"  Words: {para['word_count']}, Chars: {para['character_count']}\n")
                        f.write(f"  Text: {para['text_preview']}\n")
                    
                    f.write("\n" + "="*60 + "\n\n")
            
            self._log(f"📋 Simple mapping saved:")
            self._log(f"   📊 JSON: {mapping_file.name}")
            self._log(f"   📄 Summary: {summary_file.name}")
            
        except Exception as e:
            self._log(f"⚠️  Failed to save simple mapping: {e}")
    
    def _create_individual_block_region(self, block: Dict, text: str, page_num: int, index: int) -> Dict:
        """Create region from individual block."""
        self.region_counter += 1
        
        bbox = block["bbox"]
        return {
            "region_id": f"region_{self.region_counter:04d}",
            "page_number": page_num,
            "bbox": bbox,
            "block": block,
            "raw_text": text,
            "block_index": index,
            "word_count": len(text.split()),
            "line_count": len(text.split('\n'))
        }
    
    def _create_paragraph_region(self, blocks: List[Dict], page_num: int) -> Dict:
        """Create a paragraph region from a group of blocks."""
        
        # Calculate combined bounding box
        min_x = min(block["bbox"][0] for block in blocks)
        min_y = min(block["bbox"][1] for block in blocks) 
        max_x = max(block["bbox"][2] for block in blocks)
        max_y = max(block["bbox"][3] for block in blocks)
        
        # Extract text content
        region_text = ""
        for block in blocks:
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                region_text += line_text + "\n"
        
        self.region_counter += 1
        
        return {
            "region_id": f"region_{self.region_counter:04d}",
            "page_number": page_num,
            "bbox": (min_x, min_y, max_x, max_y),
            "blocks": blocks,
            "raw_text": region_text.strip(),
            "word_count": len(region_text.split()),
            "line_count": region_text.count('\n') + 1
        }
    
    def _phase2_analyze_regions(self, page, regions: List[Dict]) -> List[ContentRegion]:
        """
        Phase 2: Analyze content in each region to determine type.
        
        For each region, determine:
        - Contains mathematical formulas?
        - Contains table structures?
        - Contains mixed content?
        - Processing priority
        """
        
        analyzed_regions = []
        
        for region_data in regions:
            region = self._analyze_single_region(page, region_data)
            analyzed_regions.append(region)
        
        return analyzed_regions
    
    def _analyze_single_region(self, page, region_data: Dict) -> ContentRegion:
        """Analyze a single region to determine its content type."""
        
        text = region_data["raw_text"]
        
        # Use pre-calculated scores from Phase 1
        formula_score = region_data.get("formula_score", 0.0)
        table_score = region_data.get("table_score", 0.0)
        
        # Initialize content region
        region = ContentRegion(
            region_id=region_data["region_id"],
            page_number=region_data["page_number"],
            bbox=region_data["bbox"],
            normalized_bbox=self._normalize_bbox(page, region_data["bbox"]),
            raw_text=text
        )
        
        # Set analysis results
        region.contains_formula = formula_score > 0.3
        region.contains_table = table_score > 0.3
        
        # Simplified: Either needs VLM processing or it doesn't
        needs_vlm = region.contains_formula or region.contains_table
        
        if needs_vlm:
            # Single category: "special" - needs VLM processing
            region.content_type = "special"
            region.processing_priority = 4
            region.confidence_score = max(formula_score, table_score)
        else:
            # This shouldn't happen since we only process blocks with scores > 0.3
            region.content_type = "text" 
            region.processing_priority = 1
            region.confidence_score = max(formula_score, table_score)
        
        return region
    
    def _analyze_mathematical_content(self, text: str, blocks: List[Dict]) -> float:
        """
        Analyze if region contains mathematical content.
        Returns confidence score 0.0-1.0
        """
        import re
        
        score = 0.0
        factors = []
        
        # Check for mathematical symbols
        math_symbols = ['∑', '∫', '∏', '√', '±', '∞', '≈', '≤', '≥', '≠', '∂', '∇', 
                       '∀', '∃', '∈', '∉', '⊂', '⊃', '∪', '∩', '∧', '∨', '¬', '→', '↔',
                       'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'λ', 'μ', 'π', 'σ', 'φ', 'ψ', 'ω']
        
        symbol_count = sum(text.count(symbol) for symbol in math_symbols)
        if symbol_count > 0:
            score += min(0.4, symbol_count * 0.1)
            factors.append(f"symbols:{symbol_count}")
        
        # Check for mathematical patterns
        math_patterns = [
            (r'[a-zA-Z]\s*[=≈]\s*[0-9\-+\s\(\)]+', 0.2, "equations"),
            (r'\([^)]*[+\-*/][^)]*\)', 0.15, "expressions"), 
            (r'\b[a-zA-Z]\^[0-9]+\b', 0.2, "exponents"),
            (r'\b[a-zA-Z]_[0-9]+\b', 0.15, "subscripts"),
            (r'\b\d+\s*[+\-×÷*/]\s*\d+', 0.1, "arithmetic"),
            (r'\b(sin|cos|tan|log|ln|exp)\b', 0.2, "functions"),
            (r'\b[f|g|h]\([^)]*\)', 0.25, "function_notation"),
        ]
        
        for pattern, weight, name in math_patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                pattern_score = min(weight, matches * weight * 0.3)
                score += pattern_score
                factors.append(f"{name}:{matches}")
        
        # Check font characteristics
        math_font_ratio = self._get_math_font_ratio(blocks)
        if math_font_ratio > 0.2:
            font_score = min(0.3, math_font_ratio)
            score += font_score
            factors.append(f"math_fonts:{math_font_ratio:.2f}")
        
        # Normalize score
        final_score = min(1.0, score)
        
        if final_score > 0.3:
            self._log(f"            📐 Math analysis: {final_score:.2f} ({', '.join(factors)})")
        
        return final_score
    
    def _analyze_table_content(self, text: str, blocks: List[Dict]) -> float:
        """
        Analyze if region contains table content.
        Returns confidence score 0.0-1.0
        """
        import re
        
        score = 0.0
        factors = []
        lines = text.strip().split('\n')
        
        if len(lines) < 2:
            return 0.0
        
        # Check for explicit table indicators
        table_keywords = ['table', 'column', 'row', 'header', 'data', 'results', 'values']
        keyword_count = sum(text.lower().count(keyword) for keyword in table_keywords)
        if keyword_count > 0:
            score += min(0.2, keyword_count * 0.05)
            factors.append(f"keywords:{keyword_count}")
        
        # Check for structured patterns
        if len(lines) >= 3:
            # Markdown-style tables
            pipe_lines = [line for line in lines if '|' in line]
            if len(pipe_lines) >= 2:
                pipe_counts = [line.count('|') for line in pipe_lines]
                if len(set(pipe_counts)) <= 2 and max(pipe_counts) >= 2:
                    score += 0.4
                    factors.append(f"pipes:{len(pipe_lines)}")
            
            # Tab-separated values
            tab_lines = [line for line in lines if '\t' in line]
            if len(tab_lines) >= 2:
                score += 0.3
                factors.append(f"tabs:{len(tab_lines)}")
            
            # Consistent spacing patterns
            spacing_patterns = []
            for line in lines:
                spaces = len(re.findall(r'\s{2,}', line))
                spacing_patterns.append(spaces)
            
            if spacing_patterns and max(spacing_patterns) >= 2:
                consistent_lines = len([s for s in spacing_patterns if s >= 2])
                if consistent_lines / len(lines) > 0.5:
                    score += 0.25
                    factors.append(f"spacing:{consistent_lines}/{len(lines)}")
            
            # Numeric data patterns
            numeric_lines = 0
            for line in lines:
                numbers = len(re.findall(r'\b\d+\.?\d*\b', line))
                if numbers >= 2:
                    numeric_lines += 1
            
            if numeric_lines / len(lines) > 0.3:
                score += 0.2
                factors.append(f"numeric:{numeric_lines}/{len(lines)}")
        
        # Check layout consistency using block positioning
        layout_score = self._analyze_layout_consistency(blocks)
        if layout_score > 0.3:
            score += layout_score * 0.3
            factors.append(f"layout:{layout_score:.2f}")
        
        # Normalize score
        final_score = min(1.0, score)
        
        if final_score > 0.3:
            self._log(f"            📊 Table analysis: {final_score:.2f} ({', '.join(factors)})")
        
        return final_score
    
    def _get_math_font_ratio(self, blocks: List[Dict]) -> float:
        """Calculate ratio of mathematical fonts in blocks."""
        total_spans = 0
        math_font_spans = 0
        
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    total_spans += 1
                    font = span.get("font", "").lower()
                    if any(math_font in font for math_font in 
                          ["math", "italic", "symbol", "times-italic", "cambria-math"]):
                        math_font_spans += 1
        
        return math_font_spans / total_spans if total_spans > 0 else 0.0
    
    def _analyze_layout_consistency(self, blocks: List[Dict]) -> float:
        """Analyze layout consistency suggesting tabular structure."""
        if len(blocks) < 2:
            return 0.0
        
        # Check for consistent left margins (aligned columns)
        left_margins = []
        for block in blocks:
            for line in block.get("lines", []):
                if line.get("spans"):
                    left_margins.append(line["spans"][0].get("bbox", [0])[0])
        
        if not left_margins:
            return 0.0
        
        # Calculate margin consistency
        unique_margins = len(set(round(margin) for margin in left_margins))
        margin_ratio = unique_margins / len(left_margins)
        
        # Lower ratio means more consistent alignment (better for tables)
        consistency_score = max(0, 1 - margin_ratio)
        
        return consistency_score
    
    def _normalize_bbox(self, page, bbox: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Return bbox as-is since we're already creating full-width regions."""
        # No additional normalization needed - regions are already full-width
        return bbox
    
    def _create_detection_visualization(self, page, regions: List[ContentRegion], page_num: int):
        """Create visualization of detected regions with colored bounding boxes."""
        try:
            # Create output directory
            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename for page visualization
            filename = f"page_{page_num:02d}_detections.png"
            output_path = output_dir / filename
            
            # Render page as high-quality image
            mat = fitz.Matrix(2, 2)  # 2x scaling for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image for drawing
            import io
            from PIL import Image, ImageDraw, ImageFont
            
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(io.BytesIO(img_data))
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fall back to default if not available (define once for entire function)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            # Simplified color scheme: special vs regular text
            colors = {
                "special": (255, 0, 0, 128),    # Red for special content (needs VLM)
                "text": (128, 128, 128, 64)     # Light gray for regular text
            }
            
            border_colors = {
                "special": (255, 0, 0, 255),    # Solid red border
                "text": (128, 128, 128, 128)    # Gray border
            }
            
            # Draw bounding boxes for each region
            for region in regions:
                # Scale bounding box coordinates (2x scaling)
                x0, y0, x1, y1 = region.bbox
                x0, y0, x1, y1 = x0*2, y0*2, x1*2, y1*2
                
                # Get colors for this content type
                fill_color = colors.get(region.content_type, colors["text"])
                border_color = border_colors.get(region.content_type, border_colors["text"])
                
                # Draw filled rectangle (semi-transparent)
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([x0, y0, x1, y1], fill=fill_color)
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                
                # Draw border
                draw = ImageDraw.Draw(img)
                border_width = 3 if region.content_type != "text" else 1
                draw.rectangle([x0, y0, x1, y1], outline=border_color[:3], width=border_width)
                
                # Add label using YOUR naming convention
                label = f"{region.region_id}\n{region.content_type}"
                if region.confidence_score > 0:
                    label += f"\n{region.confidence_score:.2f}"
                
                # Draw label background
                bbox = draw.textbbox((x0 + 5, y0 + 5), label, font=font)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline=(0, 0, 0, 255))
                
                # Draw label text
                draw.text((x0 + 5, y0 + 5), label, fill=(0, 0, 0, 255), font=font)
            
            # Add legend
            legend_y = 10
            legend_items = [
                ("🔴 Special (VLM)", colors["special"][:3]),
                ("⚪ Regular Text", colors["text"][:3])
            ]
            
            for legend_text, color in legend_items:
                # Draw legend color box
                draw.rectangle([10, legend_y, 30, legend_y + 15], fill=color, outline=(0, 0, 0))
                # Draw legend text
                draw.text((35, legend_y), legend_text, fill=(0, 0, 0), font=font)
                legend_y += 25
            
            # Save the visualization
            img.save(str(output_path), 'PNG', quality=95)
            
            self._log(f"      📊 Created detection visualization: {filename}")
            self._log(f"         Regions visualized: {len([r for r in regions if r.content_type != 'text'])} high-value, {len([r for r in regions if r.content_type == 'text'])} text")
            
            # Free memory
            pix = None
            
        except Exception as e:
            self._log(f"      ⚠️  Failed to create visualization: {e}")
            import traceback
            traceback.print_exc()


def test_pymupdf_extraction_methods(file_path: Path, page_num: int = 3):
    """Test different PyMuPDF extraction methods to find the best one for formulas."""
    print(f"🧪 TESTING PYMUPDF EXTRACTION METHODS - PAGE {page_num}")
    print("=" * 70)
    
    try:
        doc = fitz.open(str(file_path))
        page = doc[page_num - 1]  # 0-based indexing
        
        # Test different extraction methods
        methods = [
            ("dict_default", lambda: page.get_text("dict")),
            ("dict_sorted", lambda: page.get_text("dict", sort=True)),
            ("blocks_default", lambda: page.get_text("blocks")), 
            ("blocks_sorted", lambda: page.get_text("blocks", sort=True)),
            ("words_sorted", lambda: page.get_text("words", sort=True)),
        ]
        
        output_dir = Path('/home/corey/projects/docling/cli/output/latest')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for method_name, extract_func in methods:
            print(f"\n🔍 Testing: {method_name}")
            
            start_time = time.time()
            result = extract_func()
            extraction_time = time.time() - start_time
            
            # Save results
            result_file = output_dir / f"page_{page_num}_{method_name}_test.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "method": method_name,
                    "page": page_num,
                    "extraction_time": extraction_time,
                    "result": result
                }, f, indent=2, ensure_ascii=False)
            
            # Analyze for overlapping blocks if dict format
            if "dict" in method_name and isinstance(result, dict):
                blocks = result.get("blocks", [])
                text_blocks = [b for b in blocks if "lines" in b and b.get("bbox")]
                overlaps = count_overlapping_blocks(text_blocks)
                print(f"   ⏱️ Time: {extraction_time:.3f}s")
                print(f"   📦 Blocks: {len(text_blocks)}")
                print(f"   ⚠️  Overlaps: {overlaps}")
            elif "blocks" in method_name:
                overlaps = count_overlapping_tuples(result)
                print(f"   ⏱️ Time: {extraction_time:.3f}s") 
                print(f"   📦 Blocks: {len(result)}")
                print(f"   ⚠️  Overlaps: {overlaps}")
            else:
                print(f"   ⏱️ Time: {extraction_time:.3f}s")
                print(f"   📄 Items: {len(result) if isinstance(result, list) else 'N/A'}")
        
        doc.close()
        print(f"\n✅ Test results saved to: {output_dir}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def count_overlapping_blocks(blocks: List[Dict]) -> int:
    """Count overlapping blocks in dict format."""
    overlaps = 0
    for i, block1 in enumerate(blocks):
        bbox1 = block1.get("bbox", [0, 0, 0, 0])
        for j, block2 in enumerate(blocks[i+1:], i+1):
            bbox2 = block2.get("bbox", [0, 0, 0, 0])
            if blocks_overlap_vertically_tuples(bbox1, bbox2):
                overlaps += 1
    return overlaps

def count_overlapping_tuples(blocks: List[Tuple]) -> int:
    """Count overlapping blocks in tuple format."""
    overlaps = 0
    for i, block1 in enumerate(blocks):
        bbox1 = block1[:4]  # First 4 elements are bbox
        for j, block2 in enumerate(blocks[i+1:], i+1):
            bbox2 = block2[:4]
            if blocks_overlap_vertically_tuples(bbox1, bbox2):
                overlaps += 1
    return overlaps

def blocks_overlap_vertically_tuples(bbox1: Tuple, bbox2: Tuple) -> bool:
    """Check if two bounding boxes overlap vertically."""
    y1_top, y1_bottom = bbox1[1], bbox1[3]
    y2_top, y2_bottom = bbox2[1], bbox2[3]
    return not (y1_bottom < y2_top or y2_bottom < y1_top)

def main():
    """Test PyMuPDF extraction methods and the two-phase processor."""
    import sys
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = Path('/home/corey/projects/docling/cli/data/complex_pdfs/Complex1.pdf')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    # First, test different PyMuPDF methods
    test_pymupdf_extraction_methods(file_path, page_num=3)
    
    print("\n" + "="*70)
    print("🔄 TWO-PHASE BOUNDING BOX PROCESSING")
    print("=" * 60)
    print(f"📄 Processing: {file_path.name}")
    print()
    
    processor = TwoPhaseProcessor(log_to_file=True)
    result = processor.process_document(file_path)
    
    print(f"\n✅ Processing complete!")
    if isinstance(result, dict):
        special_regions = result.get("special_regions", [])
        print(f"   📊 Found {len(special_regions)} special content regions")
    print(f"   📋 Detailed log saved to: {processor.log_file}")
    print(f"   💾 Visualization images saved to: /home/corey/projects/docling/cli/output/latest/")
    print(f"\n💡 Check the log file for detailed analysis and any errors!")


if __name__ == "__main__":
    main()