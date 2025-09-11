#!/usr/bin/env python3
"""
Test script for extracting and processing images from PDFs using VLM.
This tests the visual element extraction and VLM processing pipeline.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

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


class ImageExtractionTest:
    """Test image extraction and VLM processing."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.output_dir = self.test_dir / "extracted_images"
        self.output_dir.mkdir(exist_ok=True)
        
        # Clean up previous test outputs
        for file in self.output_dir.glob("*.png"):
            file.unlink()
        for file in self.output_dir.glob("*.json"):
            file.unlink()
    
    def extract_images_from_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract all visual elements from a PDF."""
        print(f"\n📄 EXTRACTING IMAGES FROM: {pdf_path.name}")
        print("="*60)
        
        if not PYMUPDF_AVAILABLE:
            print("❌ PyMuPDF not available for image extraction")
            return []
        
        extracted_items = []
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(str(pdf_path))
            
            # First, use FastTextExtractor to detect visual elements
            extractor = FastTextExtractor()
            result = extractor.extract(pdf_path)
            
            if not result or not result.success:
                print("❌ Failed to analyze PDF structure")
                return []
            
            # Get visual placeholders from the extraction result
            visual_placeholders = result.visual_placeholders
            print(f"✅ Found {len(visual_placeholders)} visual elements identified")
            
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
                    
                    print(f"\n🖼️  Processing {placeholder_id}:")
                    print(f"   Type: {element_type}")
                    print(f"   Page: {page_num + 1}")
                    if bbox:
                        print(f"   Location: {bbox}")
                    
                    # Try to extract the visual content
                    image_path = None
                    
                    if element_type in ['formula', 'table', 'figure', 'chart', 'diagram', 'image']:
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
                            
                            # Save the extracted image
                            image_path = self.output_dir / f"{placeholder_id}_{element_type}_page{page_num + 1}.png"
                            pix.save(str(image_path))
                            print(f"   ✅ Extracted and saved: {image_path.name}")
                            
                            extracted_items.append({
                                'placeholder_id': placeholder_id,
                                'element_type': element_type,
                                'page_number': page_num + 1,
                                'image_path': str(image_path),
                                'bbox': bbox,
                                'context': placeholder.get('context', '')
                            })
                        else:
                            print(f"   ⚠️  No bounding box available for extraction")
                    
                    # Also try to extract embedded images if this is an image/figure
                    if element_type in ['figure', 'image', 'chart', 'diagram'] and image_list:
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
                                    img_path = self.output_dir / f"{placeholder_id}_embedded_{img_index}.png"
                                    pix.save(str(img_path))
                                    print(f"   ✅ Extracted embedded image: {img_path.name}")
                                    
                                    # Only add if we haven't already extracted this element
                                    if not image_path:
                                        extracted_items.append({
                                            'placeholder_id': f"{placeholder_id}_embedded_{img_index}",
                                            'element_type': element_type,
                                            'page_number': page_num + 1,
                                            'image_path': str(img_path),
                                            'bbox': None,
                                            'context': placeholder.get('context', '')
                                        })
                                
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
            json.dump({
                'source_pdf': str(pdf_path),
                'total_placeholders': len(visual_placeholders) if 'visual_placeholders' in locals() else 0,
                'extracted_items': extracted_items,
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   Total visual elements found: {len(visual_placeholders) if 'visual_placeholders' in locals() else 0}")
        print(f"   Successfully extracted: {len(extracted_items)}")
        print(f"   Output directory: {self.output_dir}")
        
        return extracted_items
    
    def process_extracted_images_vlm(self, extracted_items: List[Dict]) -> List[Dict]:
        """Process extracted images through VLM."""
        print(f"\n🤖 PROCESSING {len(extracted_items)} IMAGES WITH VLM")
        print("="*60)
        
        if not extracted_items:
            print("❌ No items to process")
            return []
        
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
        for i, item in enumerate(extracted_items, 1):
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
        
        return processed_items
    
    def _process_with_mock_vlm(self, extracted_items: List[Dict]) -> List[Dict]:
        """Mock VLM processing for testing without GPU."""
        print("\n🔄 MOCK VLM PROCESSING")
        processed = []
        
        for item in extracted_items:
            processed_item = item.copy()
            
            # Generate mock VLM content based on type
            if item['element_type'] == 'formula':
                processed_item['vlm_content'] = "$$\\text{[Mathematical Formula]}$$"
            elif item['element_type'] == 'table':
                processed_item['vlm_content'] = "| Column 1 | Column 2 |\n|----------|----------|\n| Data     | Data     |"
            elif item['element_type'] == 'chart':
                processed_item['vlm_content'] = "**Chart:** Data visualization showing trends"
            else:
                processed_item['vlm_content'] = f"**{item['element_type'].title()}:** Visual content"
            
            processed_item['vlm_metadata'] = {'mock': True}
            processed_item['processing_time'] = 0.1
            processed.append(processed_item)
            
            print(f"   ✅ Mock processed: {item['placeholder_id']}")
        
        return processed
    
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
        
        # Step 2: Process with VLM
        processed_items = self.process_extracted_images_vlm(extracted_items)
        
        # Step 3: Display results
        print("\n" + "="*60)
        print("📋 FINAL RESULTS")
        print("="*60)
        
        for item in processed_items[:5]:  # Show first 5 results
            print(f"\n📌 {item['placeholder_id']}:")
            print(f"   Type: {item['element_type']}")
            print(f"   Page: {item['page_number']}")
            if 'vlm_content' in item:
                content_preview = item['vlm_content'][:100] + "..." if len(item['vlm_content']) > 100 else item['vlm_content']
                print(f"   VLM Output: {content_preview}")
            if 'processing_time' in item and item['processing_time']:
                print(f"   Processing Time: {item['processing_time']:.2f}s")
        
        if len(processed_items) > 5:
            print(f"\n... and {len(processed_items) - 5} more items")
        
        print(f"\n✅ TEST COMPLETE")
        print(f"   Results saved to: {self.output_dir}")


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
    
    # Run the test
    tester = ImageExtractionTest()
    tester.run_test(test_pdf)


if __name__ == "__main__":
    main()