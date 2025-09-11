#!/usr/bin/env python3
"""
Test script for extracting Docling-specific visual elements from PDFs.
Focuses on formulas, tables, charts, algorithms, and diagrams that Docling
can convert to markdown using VLM.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time
import math
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fast_text_extractor import FastTextExtractor
from visual_queue_manager import VisualQueueManager, ElementType, Priority

# Import PyMuPDF for direct image extraction
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available")

# Import Docling for advanced extraction
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import BoundingBox
    from docling.datamodel.document import DoclingDocument
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Warning: Docling not available")


@dataclass
class ExtractedElement:
    """Represents an extracted visual element from a PDF."""
    image: Optional[Image.Image]
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int
    element_type: str  # 'formula', 'table', 'chart', 'algorithm', 'diagram'
    placeholder_id: str
    context: str = ""
    vlm_content: Optional[str] = None
    image_path: Optional[Path] = None
    confidence: float = 0.0  # Confidence that this is a Docling-convertible element


class ImageExtractionTest:
    """Test image extraction and VLM processing with collage creation."""
    
    def __init__(self, pdf_name: str = None):
        # Use 'output' directory for final results
        self.output_dir = Path("output")
        if pdf_name:
            self.output_dir = self.output_dir / pdf_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use temp directory for preprocessing
        self.temp_dir = Path("temp") / "image_extraction"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up previous test outputs in output dir
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        for file in self.output_dir.glob("*.json"):
            file.unlink()
        for file in self.output_dir.glob("*.md"):
            file.unlink()
        
        # Clean up temp dir
        for file in self.temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
        
        self.extracted_elements: List[ExtractedElement] = []
    
    def detect_docling_elements(self, pdf_path: Path) -> List[Dict]:
        """Use Docling to detect convertible visual elements (formulas, tables, charts, algorithms)."""
        if not DOCLING_AVAILABLE:
            return []
        
        elements = []
        try:
            # Configure Docling for optimal visual element detection
            pipeline_options = PdfPipelineOptions(
                do_ocr=False,
                do_table_structure=True,
                table_structure_options={
                    "mode": TableFormerMode.ACCURATE
                },
                generate_picture_images=True
            )
            
            converter = DocumentConverter(
                pipeline_options=pipeline_options
            )
            result = converter.convert(str(pdf_path))
            
            if hasattr(result, 'document'):
                doc = result.document
                
                # Track what we find
                element_count = {'formula': 0, 'table': 0, 'chart': 0, 'algorithm': 0, 'diagram': 0}
                
                # Iterate through all elements
                for item in doc.iterate_items():
                    element_type = None
                    confidence = 0.0
                    
                    if hasattr(item, '__class__'):
                        class_name = item.__class__.__name__.lower()
                        item_text = str(item) if hasattr(item, '__str__') else ''
                        
                        # Detect formulas/equations
                        if any(x in class_name for x in ['formula', 'equation', 'math']):
                            element_type = ElementCategory.FORMULA
                            confidence = 0.9
                        elif any(x in item_text.lower() for x in ['\\frac', '\\sum', '\\int', '$$', '\\begin{equation']):
                            element_type = ElementCategory.FORMULA
                            confidence = 0.8
                        
                        # Detect tables
                        elif 'table' in class_name:
                            element_type = ElementCategory.TABLE
                            confidence = 0.95
                        
                        # Detect charts/graphs/plots
                        elif 'chart' in class_name:
                            element_type = ElementCategory.CHART
                            confidence = 0.85
                        elif 'graph' in class_name:
                            element_type = ElementCategory.GRAPH
                            confidence = 0.85
                        elif 'plot' in class_name:
                            element_type = ElementCategory.PLOT
                            confidence = 0.85
                        
                        # Detect algorithms/code
                        elif any(x in class_name for x in ['code', 'listing']):
                            element_type = ElementCategory.CODE
                            confidence = 0.8
                        elif 'algorithm' in class_name:
                            element_type = ElementCategory.ALGORITHM
                            confidence = 0.8
                        
                        # Detect diagrams/flowcharts/schematics
                        elif 'diagram' in class_name:
                            element_type = ElementCategory.DIAGRAM
                            confidence = 0.75
                        elif 'flow' in class_name:
                            element_type = ElementCategory.FLOWCHART
                            confidence = 0.75
                        elif 'schema' in class_name or 'schematic' in class_name:
                            element_type = ElementCategory.SCHEMATIC
                            confidence = 0.7
                        
                        # Skip generic figures/images unless they look technical
                        elif 'figure' in class_name or 'image' in class_name:
                            # Check if it might be a technical diagram
                            if hasattr(item, 'caption'):
                                caption = str(item.caption).lower()
                                if any(x in caption for x in ['algorithm', 'flow', 'diagram', 'chart', 'graph', 'equation']):
                                    element_type = 'diagram'
                                    confidence = 0.7
                    
                    if element_type and hasattr(item, 'bbox') and item.bbox:
                        bbox = item.bbox
                        page_num = getattr(item, 'page_num', 1)
                        element_count[element_type] += 1
                        
                        elements.append({
                            'type': element_type,
                            'bbox': (bbox.l, bbox.t, bbox.r, bbox.b),
                            'page': page_num,
                            'width': int(bbox.r - bbox.l),
                            'height': int(bbox.b - bbox.t),
                            'confidence': confidence,
                            'placeholder_id': f'{element_type}_{page_num:02d}_{element_count[element_type]:04d}'
                        })
                
                # Print summary of what was found
                if elements:
                    print("📊 Docling detected:")
                    for elem_type, count in element_count.items():
                        if count > 0:
                            print(f"   - {count} {elem_type}(s)")
        except Exception as e:
            print(f"⚠️ Docling detection failed: {e}")
        
        return elements
    
    def extract_images_from_pdf(self, pdf_path: Path) -> List[ExtractedElement]:
        """Extract all visual elements from a PDF."""
        print(f"\n📄 EXTRACTING IMAGES FROM: {pdf_path.name}")
        print("="*60)
        
        self.extracted_elements = []
        
        if not PYMUPDF_AVAILABLE:
            print("❌ PyMuPDF not available for image extraction")
            return []
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(str(pdf_path))
            
            # First, use FastTextExtractor to detect visual elements
            visual_placeholders = []
            try:
                extractor = FastTextExtractor()
                result = extractor.extract(pdf_path)
                
                if result and hasattr(result, 'visual_placeholders'):
                    visual_placeholders = result.visual_placeholders
                    print(f"✅ FastTextExtractor found {len(visual_placeholders)} visual elements")
            except Exception as e:
                print(f"⚠️ FastTextExtractor failed: {e}")
            
            # Use Docling detection for better element identification
            docling_elements = self.detect_docling_elements(pdf_path)
            
            # If we have Docling elements, prioritize those
            if docling_elements:
                print(f"✅ Using Docling detection: {len(docling_elements)} elements")
                # Filter to only high-confidence Docling elements
                visual_placeholders = [e for e in docling_elements if e.get('confidence', 0) > 0.6]
                print(f"✅ Filtered to {len(visual_placeholders)} high-confidence elements")
            elif not visual_placeholders:
                print("📍 Using heuristic detection...")
                # Try to detect based on visual patterns in the PDF
                visual_placeholders = self.detect_by_visual_patterns(doc, pdf_path)
            
            print(f"✅ Total {len(visual_placeholders)} Docling-compatible elements identified")
            
            # Now extract actual images from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_placeholders = [p for p in visual_placeholders if p.get('page', 1) == page_num + 1]
                
                if not page_placeholders:
                    continue
                    
                print(f"\n📄 Page {page_num + 1}: {len(page_placeholders)} visual elements")
                
                # Extract all images from this page
                image_list = page.get_images()
                
                for i, placeholder in enumerate(page_placeholders):
                    element_type = placeholder.get('type', 'unknown')
                    placeholder_id = placeholder.get('placeholder_id', f'visual_{page_num:02d}_{i:04d}')
                    bbox = placeholder.get('bbox')
                    
                    # Only process Docling-compatible elements
                    if element_type not in ['formula', 'table', 'chart', 'algorithm', 'diagram']:
                        # Skip general images/figures
                        continue
                    
                    # Format bbox display
                    if bbox and len(bbox) == 4:
                        width = int(bbox[2] - bbox[0])
                        height = int(bbox[3] - bbox[1])
                        icon = self._get_element_icon(element_type)
                        confidence = placeholder.get('confidence', 0.0)
                        print(f"{icon} Detected {element_type}: {width}x{height} at Rect({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}) on page {page_num + 1} (confidence: {confidence:.2f})")
                    else:
                        continue  # Skip if no bbox
                    
                    # Try to extract the visual content
                    image_path = None
                    
                    if element_type in ['formula', 'table', 'chart', 'algorithm', 'diagram']:
                        # For any visual element, try to extract it as an image
                        if bbox:
                            # Convert bbox to fitz.Rect if it's a tuple/list
                            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                                rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                            else:
                                # Fallback to full page if bbox is invalid
                                rect = page.rect
                            
                            # Extract the region as an image
                            # Increase resolution for better quality
                            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for higher quality
                            pix = page.get_pixmap(matrix=mat, clip=rect)
                            
                            # Convert PyMuPDF pixmap to PIL Image
                            img_data = pix.tobytes("png")
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                            # Save the extracted image to temp directory first
                            temp_image_path = self.temp_dir / f"{placeholder_id}_{element_type}_page{page_num + 1}.png"
                            pix.save(str(temp_image_path))
                            
                            # Also save to output directory for final results
                            image_path = self.output_dir / f"{placeholder_id}_{element_type}_page{page_num + 1}.png"
                            pil_image.save(str(image_path))
                            print(f"   ✅ Extracted and saved: {image_path.name}")
                            
                            # Create ExtractedElement
                            element = ExtractedElement(
                                image=pil_image,
                                bbox=bbox if bbox else (0, 0, pil_image.width, pil_image.height),
                                page_num=page_num + 1,
                                element_type=element_type,
                                placeholder_id=placeholder_id,
                                context=placeholder.get('context', ''),
                                image_path=image_path
                            )
                            self.extracted_elements.append(element)
                        else:
                            print(f"   ⚠️  No bounding box available for extraction")
                    
                    # Skip embedded image extraction for non-Docling elements
                    # We only want formulas, tables, charts, algorithms, diagrams
                    if element_type in ['chart', 'diagram'] and image_list:
                        # Try to match and extract actual embedded images
                        for img_index, img in enumerate(image_list):
                            try:
                                xref = img[0]
                                # Get the image
                                pix = fitz.Pixmap(doc, xref)
                                
                                # Convert CMYK to RGB if necessary
                                if pix.n - pix.alpha > 3:
                                    pix = fitz.Pixmap(fitz.csRGB, pix)
                                
                                # Save if it's substantial
                                if pix.width > 50 and pix.height > 50:
                                    # Save to both temp and output directories
                                    temp_path = self.temp_dir / f"{placeholder_id}_embedded_{img_index}.png"
                                    img_path = self.output_dir / f"{placeholder_id}_embedded_{img_index}.png"
                                    pix.save(str(temp_path))
                                    
                                    # Convert to PIL and save to output
                                    img_data = pix.tobytes("png")
                                    pil_image_embedded = Image.open(io.BytesIO(img_data))
                                    pil_image_embedded.save(str(img_path))
                                    print(f"   ✅ Extracted embedded image: {img_path.name}")
                                    
                                    # Only add if we haven't already extracted this element
                                    if not image_path:
                                        # Create ExtractedElement for embedded image
                                        element = ExtractedElement(
                                            image=pil_image_embedded,
                                            bbox=(0, 0, pix.width, pix.height),
                                            page_num=page_num + 1,
                                            element_type=element_type,
                                            placeholder_id=f"{placeholder_id}_embedded_{img_index}",
                                            context=placeholder.get('context', ''),
                                            image_path=img_path
                                        )
                                        self.extracted_elements.append(element)
                                
                                pix = None  # Free memory
                            except Exception as e:
                                print(f"   ⚠️  Could not extract embedded image {img_index}: {e}")
            
            doc.close()
            
        except Exception as e:
            print(f"❌ Error extracting images: {e}")
            import traceback
            traceback.print_exc()
        
        # Save extraction metadata
        metadata_file = self.output_dir / "extraction_metadata.json"
        with open(metadata_file, 'w') as f:
            # Convert ExtractedElement objects to dictionaries for JSON serialization
            extracted_items_dict = [{
                'placeholder_id': element.placeholder_id,
                'element_type': element.element_type,
                'page_number': element.page_num,
                'image_path': str(element.image_path) if element.image_path else None,
                'bbox': element.bbox,
                'context': element.context
            } for element in self.extracted_elements]
            
            json.dump({
                'source_pdf': str(pdf_path),
                'total_placeholders': len(visual_placeholders) if 'visual_placeholders' in locals() else 0,
                'extracted_items': extracted_items_dict,
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   Total visual elements found: {len(visual_placeholders) if 'visual_placeholders' in locals() else 0}")
        print(f"   Successfully extracted: {len(self.extracted_elements)}")
        print(f"   Output directory: {self.output_dir}")
        
        return self.extracted_elements
    
    def _get_element_icon(self, element_type: str) -> str:
        """Get icon for element type."""
        icons = {
            'formula': '∑',  # Mathematical formula
            'table': '⊞',   # Table/grid
            'chart': '📊',   # Chart/graph
            'algorithm': '⟨⟩', # Algorithm/code
            'diagram': '⬡'   # Technical diagram
        }
        return icons.get(element_type, '•')
    
    def detect_by_visual_patterns(self, doc, pdf_path: Path) -> List[Dict]:
        """Detect visual elements by analyzing patterns in the PDF."""
        elements = []
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Look for text patterns that indicate formulas, tables, etc.
                text = page.get_text()
                lines = text.split('\n')
                
                # Detect potential formulas by LaTeX patterns
                for i, line in enumerate(lines):
                    if any(pattern in line for pattern in ['$$', '\\begin{', '\\frac', '\\sum', '\\int', 'Equation']):
                        # Try to get approximate bbox for this line
                        text_instances = page.search_for(line[:20] if len(line) > 20 else line)
                        if text_instances:
                            rect = text_instances[0]
                            elements.append({
                                'type': 'formula',
                                'bbox': (rect.x0, rect.y0, rect.x1, rect.y1),
                                'page': page_num + 1,
                                'confidence': 0.7,
                                'placeholder_id': f'formula_{page_num:02d}_{i:04d}'
                            })
                
                # Look for table-like structures (multiple | characters)
                for i, line in enumerate(lines):
                    if line.count('|') >= 3:  # Likely a table row
                        text_instances = page.search_for(line[:20] if len(line) > 20 else line)
                        if text_instances:
                            rect = text_instances[0]
                            elements.append({
                                'type': 'table',
                                'bbox': (rect.x0, rect.y0, rect.x1, rect.y1),
                                'page': page_num + 1,
                                'confidence': 0.6,
                                'placeholder_id': f'table_{page_num:02d}_{i:04d}'
                            })
                            break  # One table per detection
        except Exception as e:
            print(f"⚠️ Pattern detection failed: {e}")
        
        return elements
    
    def create_image_collage(self, elements: List[ExtractedElement], output_name: str = "collage.png") -> Path:
        """Create a compact collage of all extracted images."""
        if not elements:
            print("❌ No images to create collage")
            return None
        
        print(f"\n🎨 CREATING IMAGE COLLAGE")
        print("="*60)
        
        # Filter elements with valid images
        valid_elements = [e for e in elements if e.image is not None]
        if not valid_elements:
            print("❌ No valid images for collage")
            return None
        
        # Calculate grid dimensions
        num_images = len(valid_elements)
        cols = math.ceil(math.sqrt(num_images))
        rows = math.ceil(num_images / cols)
        
        # Cell dimensions
        cell_width = 350
        cell_height = 350
        padding = 15
        label_height = 30
        
        # Create collage canvas
        collage_width = cols * (cell_width + padding) + padding
        collage_height = rows * (cell_height + padding) + padding
        
        collage = Image.new('RGB', (collage_width, collage_height), color='#f0f0f0')
        draw = ImageDraw.Draw(collage)
        
        # Try to load a better font
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # Place images in grid
        for idx, element in enumerate(valid_elements):
            row = idx // cols
            col = idx % cols
            
            x = col * (cell_width + padding) + padding
            y = row * (cell_height + padding) + padding
            
            # Create cell background
            draw.rectangle([x, y, x + cell_width, y + cell_height], fill='white', outline='#cccccc', width=1)
            
            # Resize image to fit cell (leaving room for label)
            img = element.image.copy()
            img.thumbnail((cell_width - 20, cell_height - label_height - 10), Image.Resampling.LANCZOS)
            
            # Center image in cell
            img_x = x + (cell_width - img.width) // 2
            img_y = y + label_height + (cell_height - label_height - img.height) // 2
            
            # Paste image
            collage.paste(img, (img_x, img_y))
            
            # Add header bar
            draw.rectangle([x, y, x + cell_width, y + label_height], fill='#4a90e2', outline='#4a90e2')
            
            # Add label
            label = f"{element.element_type.upper()} - Page {element.page_num}"
            bbox = draw.textbbox((0, 0), label, font=title_font)
            text_width = bbox[2] - bbox[0]
            draw.text((x + (cell_width - text_width) // 2, y + 8), label, fill='white', font=title_font)
            
            # Add dimensions info
            if element.bbox:
                width = int(element.bbox[2] - element.bbox[0])
                height = int(element.bbox[3] - element.bbox[1])
                dim_text = f"{width}x{height}"
                draw.text((x + 5, y + cell_height - 20), dim_text, fill='#666666', font=label_font)
        
        # Save collage
        collage_path = self.output_dir / output_name
        collage.save(collage_path, quality=95, optimize=True)
        
        print(f"✅ Collage saved to: {collage_path}")
        print(f"   Dimensions: {collage_width}x{collage_height}")
        print(f"   Grid: {cols}x{rows} ({num_images} images)")
        
        return collage_path
    
    def process_extracted_images_vlm(self, extracted_items: List[ExtractedElement]) -> List[ExtractedElement]:
        """Process extracted images through VLM."""
        print(f"\n🤖 PROCESSING {len(extracted_items)} IMAGES WITH VLM")
        print("="*60)
        
        if not extracted_items:
            print("❌ No items to process")
            return []
        
        # Convert ExtractedElement objects to dicts for compatibility
        items_dict = []
        for elem in extracted_items:
            if isinstance(elem, ExtractedElement):
                items_dict.append({
                    'placeholder_id': elem.placeholder_id,
                    'element_type': elem.element_type,
                    'page_number': elem.page_num,
                    'image_path': str(elem.image_path) if elem.image_path else '',
                    'bbox': elem.bbox,
                    'context': elem.context
                })
            else:
                items_dict.append(elem)
        
        # Initialize VLM queue manager
        try:
            vlm_queue = VisualQueueManager(max_workers=1, batch_timeout=30.0)
            print("   ✅ VLM Queue Manager initialized with GPU support")
            
        except Exception as e:
            print(f"   ❌ Failed to initialize VLM components: {e}")
            print("   🔄 Falling back to mock processing...")
            return self._process_with_mock_vlm(extracted_items)
        
        processed_items = []
        queued_jobs = {}
        
        # Step 1: Queue all items for VLM processing
        for i, item in enumerate(items_dict, 1):
            print(f"🔄 Queuing {i}/{len(extracted_items)}: {item['placeholder_id']} ({item['element_type']})")
            
            image_path = Path(item['image_path'])
            if not image_path.exists():
                print(f"   ❌ Image file not found: {image_path}")
                continue
                
            try:
                # Map element types to VLM element types
                element_type_map = {
                    'formula': ElementType.FORMULA,
                    'table': ElementType.TABLE, 
                    'image': ElementType.IMAGE,
                    'figure': ElementType.IMAGE,
                    'chart': ElementType.CHART,
                    'diagram': ElementType.DIAGRAM
                }
                
                vlm_element_type = element_type_map.get(item['element_type'], ElementType.IMAGE)
                priority = Priority.HIGH if item['element_type'] == 'formula' else Priority.NORMAL
                
                # Queue the job for VLM processing
                job_id = vlm_queue.add_job(
                    document_path=image_path,  # Use the extracted image path
                    element_type=vlm_element_type,
                    page_number=item['page_number'],
                    priority=priority,
                    estimated_time=5.0,
                    placeholder_id=item['placeholder_id']
                )
                
                queued_jobs[job_id] = item
                print(f"   ✅ Queued job: {job_id[:8]}...")
                
            except Exception as e:
                print(f"   ❌ Failed to queue: {e}")
                continue
        
        if not queued_jobs:
            print("   ❌ No jobs queued successfully")
            vlm_queue.shutdown()
            return []
        
        # Step 2: Wait for VLM processing to complete
        print(f"\n⏳ WAITING FOR {len(queued_jobs)} VLM JOBS TO COMPLETE...")
        print("   This may take several minutes depending on GPU availability...")
        
        try:
            # Give the batch processor time to create batches
            time.sleep(1.0)
            
            # Group jobs by document (since we're using individual image files as documents)
            jobs_by_document = {}
            for job_id, item in queued_jobs.items():
                doc_path = Path(item['image_path'])
                if doc_path not in jobs_by_document:
                    jobs_by_document[doc_path] = []
                jobs_by_document[doc_path].append((job_id, item))
            
            # Wait for each document's jobs to complete
            for doc_path, doc_jobs in jobs_by_document.items():
                print(f"   📄 Waiting for {len(doc_jobs)} jobs from {doc_path.name}...")
                
                # Wait for this document's jobs (timeout: 5 minutes per document)
                completed_jobs = vlm_queue.wait_for_document(doc_path, timeout=300.0)
                
                if completed_jobs:
                    print(f"   ✅ Received {len(completed_jobs)} completed jobs from {doc_path.name}")
                    
                    # Process completed jobs
                    for job in completed_jobs:
                        # Find the corresponding item
                        for job_id, item in doc_jobs:
                            if job.job_id == job_id:
                                processed_item = item.copy()
                                processed_item['vlm_content'] = job.enhanced_content
                                processed_item['vlm_metadata'] = job.metadata
                                processed_item['processing_time'] = (
                                    (job.completed_time - job.started_time).total_seconds()
                                    if job.completed_time and job.started_time else None
                                )
                                # Update the original ExtractedElement if we have it
                                for elem in extracted_items:
                                    if isinstance(elem, ExtractedElement) and elem.placeholder_id == item['placeholder_id']:
                                        elem.vlm_content = job.enhanced_content
                                        break
                                
                                processed_items.append(processed_item)
                                print(f"      ✅ Processed: {item['placeholder_id']}")
                                break
                else:
                    print(f"   ⚠️  No results received for {doc_path.name}")
            
            # Check for any failed jobs
            for job_id in queued_jobs:
                job_status = vlm_queue.get_job_status(job_id)
                if job_status and job_status.status.value == 'FAILED':
                    print(f"   ❌ Job failed: {job_id[:8]} - {job_status.error_message}")
            
        except Exception as e:
            print(f"❌ Error during VLM processing: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Shutdown VLM queue
            vlm_queue.shutdown()
            print("   🛑 VLM Queue Manager shutdown")
        
        # Save processing results
        results_file = self.output_dir / "vlm_processing_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'total_processed': len(processed_items),
                'items': processed_items,
                'processing_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        print(f"\n📊 VLM PROCESSING SUMMARY:")
        print(f"   Total items queued: {len(queued_jobs)}")
        print(f"   Successfully processed: {len(processed_items)}")
        print(f"   Failed/Timeout: {len(queued_jobs) - len(processed_items)}")
        
        # Return ExtractedElement objects if that's what we received
        if extracted_items and isinstance(extracted_items[0], ExtractedElement):
            return extracted_items
        return processed_items
    
    def _process_with_mock_vlm(self, extracted_items: List[ExtractedElement]) -> List[ExtractedElement]:
        """Mock VLM processing for testing without GPU."""
        print("\n🔄 MOCK VLM PROCESSING")
        
        for item in extracted_items:
            if isinstance(item, ExtractedElement):
                element_type = item.element_type
                placeholder_id = item.placeholder_id
            else:
                element_type = item.get('element_type', 'unknown')
                placeholder_id = item.get('placeholder_id', 'unknown')
            
            # Generate mock VLM content based on type
            if element_type == 'formula':
                vlm_content = "$$\\text{[Mathematical Formula]}$$"
            elif element_type == 'table':
                vlm_content = "| Column 1 | Column 2 |\n|----------|----------|\n| Data     | Data     |"
            elif element_type == 'chart':
                vlm_content = "**Chart:** Data visualization showing trends"
            else:
                vlm_content = f"**{element_type.title()}:** Visual content"
            
            if isinstance(item, ExtractedElement):
                item.vlm_content = vlm_content
            else:
                item['vlm_content'] = vlm_content
                item['vlm_metadata'] = {'mock': True}
                item['processing_time'] = 0.1
            
            print(f"   ✅ Mock processed: {placeholder_id}")
        
        return extracted_items
    
    def run_test(self, pdf_path: Path):
        """Run the complete test pipeline."""
        print("\n" + "="*60)
        print("🚀 STARTING IMAGE EXTRACTION AND VLM PROCESSING TEST")
        print("="*60)
        
        # Step 1: Extract images from PDF
        extracted_items = self.extract_images_from_pdf(pdf_path)
        
        if not extracted_items:
            print("\n❌ No images extracted. Test cannot continue.")
            return
        
        # Step 2: Create collage of extracted images
        collage_path = self.create_image_collage(extracted_items, f"{pdf_path.stem}_collage.png")
        
        # Step 3: Process with VLM
        processed_items = self.process_extracted_images_vlm(extracted_items)
        
        # Step 4: Generate markdown report
        self.generate_markdown_report(processed_items, collage_path, pdf_path)
        
        # Step 5: Display results
        print("\n" + "="*60)
        print("📋 FINAL RESULTS")
        print("="*60)
        
        for i, item in enumerate(processed_items[:5], 1):  # Show first 5 results
            if isinstance(item, ExtractedElement):
                print(f"\n📌 [{i}] {item.placeholder_id}:")
                print(f"   Type: {item.element_type}")
                print(f"   Page: {item.page_num}")
                if item.vlm_content:
                    content_preview = item.vlm_content[:100] + "..." if len(item.vlm_content) > 100 else item.vlm_content
                    print(f"   VLM Output: {content_preview}")
            else:
                print(f"\n📌 [{i}] {item.get('placeholder_id', 'unknown')}:")
                print(f"   Type: {item.get('element_type', 'unknown')}")
                print(f"   Page: {item.get('page_number', 'unknown')}")
                if 'vlm_content' in item:
                    content_preview = item['vlm_content'][:100] + "..." if len(item['vlm_content']) > 100 else item['vlm_content']
                    print(f"   VLM Output: {content_preview}")
        
        if len(processed_items) > 5:
            print(f"\n... and {len(processed_items) - 5} more items")
        
        print(f"\n✅ TEST COMPLETE")
        print(f"   📁 Output directory: {self.output_dir}")
        if collage_path:
            print(f"   🖼️  Collage: {collage_path}")
        print(f"   📝 Report: {self.output_dir / 'extraction_report.md'}")
    
    def generate_markdown_report(self, items: List[ExtractedElement], collage_path: Path, pdf_path: Path):
        """Generate a markdown report of the extraction results."""
        report_path = self.output_dir / "extraction_report.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Image Extraction Report\n\n")
            f.write(f"**Source PDF**: `{pdf_path.name}`\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Elements Extracted**: {len(items)}\n")
            
            # Count by type
            type_counts = {}
            for item in items:
                if isinstance(item, ExtractedElement):
                    elem_type = item.element_type
                else:
                    elem_type = item.get('element_type', 'unknown')
                type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
            
            for elem_type, count in sorted(type_counts.items()):
                f.write(f"- **{elem_type.capitalize()}s**: {count}\n")
            
            if collage_path and collage_path.exists():
                f.write(f"\n## Visual Collage\n\n")
                f.write(f"![Extracted Elements Collage]({collage_path.name})\n\n")
            
            f.write(f"## Extracted Elements\n\n")
            
            for i, item in enumerate(items, 1):
                if isinstance(item, ExtractedElement):
                    f.write(f"### {i}. {item.element_type.capitalize()} - Page {item.page_num}\n\n")
                    f.write(f"- **ID**: `{item.placeholder_id}`\n")
                    if item.bbox:
                        width = int(item.bbox[2] - item.bbox[0])
                        height = int(item.bbox[3] - item.bbox[1])
                        f.write(f"- **Dimensions**: {width}x{height}\n")
                        f.write(f"- **Position**: ({item.bbox[0]:.1f}, {item.bbox[1]:.1f})\n")
                    if item.vlm_content:
                        f.write(f"\n**VLM Output**:\n\n```\n{item.vlm_content}\n```\n\n")
                else:
                    f.write(f"### {i}. {item.get('element_type', 'unknown').capitalize()} - Page {item.get('page_number', 'unknown')}\n\n")
                    if 'vlm_content' in item:
                        f.write(f"**VLM Output**:\n\n```\n{item['vlm_content']}\n```\n\n")
        
        print(f"✅ Report generated: {report_path}")


def main():
    """Main test entry point."""
    # Determine test PDF
    test_pdf = Path("data/test_documents/test.pdf")
    
    # Check for command line argument
    if len(sys.argv) > 1:
        test_pdf = Path(sys.argv[1])
    
    # Validate PDF exists
    if not test_pdf.exists():
        print(f"❌ Error: PDF not found: {test_pdf}")
        print("\nUsage: python test_image_extraction.py [path_to_pdf]")
        print(f"Default: {test_pdf}")
        sys.exit(1)
    
    # Run the test with PDF name for output directory
    pdf_name = test_pdf.stem  # Get filename without extension
    tester = ImageExtractionTest(pdf_name=pdf_name)
    tester.run_test(test_pdf)


if __name__ == "__main__":
    main()