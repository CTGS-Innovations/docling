#!/usr/bin/env python3
"""
Use Docling's native detection to extract visual elements as images.
Simple and focused: detect elements, save as PNG files.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# Image processing
try:
    import fitz  # PyMuPDF for image extraction
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Error: PyMuPDF required. Install with: pip install PyMuPDF")
    sys.exit(1)


def extract_elements_as_images(pdf_path: str):
    """
    Use Docling to detect elements and extract them as images.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Set up output directory
    output_dir = Path("output") / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear previous extractions
    for file in output_dir.glob("*.png"):
        file.unlink()
    
    print(f"\n{'='*60}")
    print(f"📄 DOCLING ELEMENT EXTRACTION")
    print(f"📄 PDF: {pdf_path.name}")
    print(f"📁 Output: {output_dir}")
    print(f"{'='*60}\n")
    
    # Configure Docling pipeline for comprehensive detection
    print("🔧 Configuring Docling pipeline...")
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True           # Enable table detection
    pipeline_options.do_ocr = False                      # Skip OCR for speed
    pipeline_options.generate_page_images = False        # We'll extract ourselves
    pipeline_options.generate_picture_images = True      # Let Docling generate images
    
    # Additional options if available
    try:
        pipeline_options.do_code_enrichment = True       # Enable code detection
        pipeline_options.do_formula_enrichment = True    # Enable formula detection
    except AttributeError:
        pass  # Older version might not have these
    
    # Create converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    # Convert document
    print("🔍 Detecting elements with Docling...")
    result = converter.convert(str(pdf_path))
    
    if not result or not hasattr(result, 'document'):
        print("❌ Docling conversion failed")
        return
    
    doc = result.document
    
    # Open PDF with PyMuPDF for image extraction
    pdf_doc = fitz.open(str(pdf_path))
    
    # Track what we find
    elements_found = []
    element_counts = {}
    
    # Process all elements found by Docling
    print("\n📊 Processing detected elements...")
    
    for item in doc.iterate_items():
        # Check if item has position information
        if not hasattr(item, 'bbox') or not item.bbox:
            continue
        
        # Get element type
        element_type = item.__class__.__name__
        
        # Get page number (Docling uses 1-based indexing)
        page_num = getattr(item, 'page_idx', 0) + 1
        if page_num < 1 or page_num > len(pdf_doc):
            page_num = 1  # Default to first page
        
        # Get bounding box
        bbox = item.bbox
        x0, y0, x1, y1 = bbox.l, bbox.t, bbox.r, bbox.b
        
        # Filter out tiny elements
        width = x1 - x0
        height = y1 - y0
        if width < 30 or height < 20:
            continue
        
        # Count element types
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
        count = element_counts[element_type]
        
        # Generate element ID
        type_abbrev = {
            'Table': 'TBL',
            'TableCell': 'CEL',
            'Formula': 'FML',
            'Equation': 'EQN',
            'Figure': 'FIG',
            'Picture': 'PIC',
            'Code': 'COD',
            'CodeBlock': 'BLK',
            'Paragraph': 'PAR',
            'List': 'LST',
            'ListItem': 'ITM',
        }.get(element_type, element_type[:3].upper())
        
        element_id = f"{type_abbrev}_P{page_num:03d}_N{count:03d}"
        
        # Extract the image
        try:
            page = pdf_doc[page_num - 1]
            
            # Create rectangle for extraction
            rect = fitz.Rect(x0, y0, x1, y1)
            
            # Extract at high resolution
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for quality
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Save image
            image_path = output_dir / f"{element_id}.png"
            pix.save(str(image_path))
            
            print(f"  ✅ {element_id}: {element_type} ({int(width)}x{int(height)}px)")
            
            # Record element info
            elements_found.append({
                'id': element_id,
                'type': element_type,
                'page': page_num,
                'bbox': [x0, y0, x1, y1],
                'width': int(width),
                'height': int(height),
                'file': image_path.name
            })
            
        except Exception as e:
            print(f"  ⚠️  Failed to extract {element_id}: {e}")
    
    pdf_doc.close()
    
    # Save metadata
    metadata = {
        'source': pdf_path.name,
        'timestamp': datetime.now().isoformat(),
        'total_elements': len(elements_found),
        'element_types': dict(sorted(element_counts.items())),
        'elements': elements_found
    }
    
    metadata_path = output_dir / "elements.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Generate summary report
    print(f"\n{'='*60}")
    print(f"📊 EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total elements extracted: {len(elements_found)}")
    print(f"\nElements by type:")
    for elem_type, count in sorted(element_counts.items()):
        print(f"  - {elem_type}: {count}")
    print(f"\n📁 Output saved to: {output_dir}")
    print(f"📋 Metadata: {metadata_path}")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python docling_extract_images.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    extract_elements_as_images(pdf_path)


if __name__ == "__main__":
    main()