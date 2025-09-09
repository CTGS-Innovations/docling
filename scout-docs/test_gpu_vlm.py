#!/usr/bin/env python3
"""
Test GPU VLM configuration for Docling
Based on official examples from docling_github/docs/examples/
"""

import os
import sys
import time
import torch
from pathlib import Path

# Add the backend app to path so we can import the service
sys.path.append(str(Path(__file__).parent / "backend" / "app"))

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.datamodel import vlm_model_specs
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

def test_gpu_availability():
    """Test if GPU is available and configured correctly"""
    print("🔍 Testing GPU availability...")
    
    cuda_available = torch.cuda.is_available()
    print(f"   CUDA Available: {cuda_available}")
    
    if cuda_available:
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
        print(f"   GPU Device: {device_name}")
        print(f"   Device Count: {device_count}")
        
        # Test memory
        try:
            memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
            print(f"   GPU Memory - Reserved: {memory_reserved:.2f} GB, Allocated: {memory_allocated:.2f} GB")
        except Exception as e:
            print(f"   ⚠️ GPU memory check failed: {e}")
        
        return True
    else:
        print("   ❌ No GPU available")
        return False

def test_vlm_model_config():
    """Test VLM model configuration"""
    print("\n🤖 Testing VLM Model Configuration...")
    
    # Test SmolDocling Transformers (supports CUDA)
    model_spec = vlm_model_specs.SMOLDOCLING_TRANSFORMERS
    print(f"   Model: {model_spec.repo_id}")
    print(f"   Framework: {model_spec.inference_framework}")
    print(f"   Supported Devices: {model_spec.supported_devices}")
    print(f"   Response Format: {model_spec.response_format}")
    
    # Check if CUDA is in supported devices
    cuda_supported = AcceleratorDevice.CUDA in model_spec.supported_devices
    print(f"   CUDA Supported by Model: {cuda_supported}")
    
    return cuda_supported

def test_pipeline_configuration():
    """Test the VLM pipeline configuration"""
    print("\n⚙️ Testing VLM Pipeline Configuration...")
    
    try:
        # Configure for GPU
        accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CUDA,
            num_threads=4,
            cuda_use_flash_attention2=True
        )
        print(f"   Accelerator Device: {accelerator_options.device}")
        print(f"   Flash Attention 2: {accelerator_options.cuda_use_flash_attention2}")
        
        # Configure VLM options
        vlm_options = vlm_model_specs.SMOLDOCLING_TRANSFORMERS
        
        # Create pipeline options
        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_options
        )
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.generate_page_images = True
        
        print(f"   Pipeline configured successfully")
        
        # Create converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )
        
        print(f"   ✅ Document converter created successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline configuration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 GPU VLM Configuration Test")
    print("=" * 50)
    
    # Test 1: GPU Availability
    gpu_available = test_gpu_availability()
    
    # Test 2: Model Configuration
    model_supports_cuda = test_vlm_model_config()
    
    # Test 3: Pipeline Configuration
    pipeline_ok = test_pipeline_configuration()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   GPU Available: {'✅' if gpu_available else '❌'}")
    print(f"   Model Supports CUDA: {'✅' if model_supports_cuda else '❌'}")
    print(f"   Pipeline Configuration: {'✅' if pipeline_ok else '❌'}")
    
    if gpu_available and model_supports_cuda and pipeline_ok:
        print("\n🎉 All tests passed! GPU VLM should work correctly.")
        print("\n💡 Next steps:")
        print("   1. Make sure your Docker container has GPU access (--gpus all)")
        print("   2. Ensure CUDA drivers are installed in the container")
        print("   3. Try processing a document with pipeline='vlm' and compute_mode='gpu'")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
        
        if not gpu_available:
            print("   - No GPU detected. Make sure Docker has GPU access.")
        if not model_supports_cuda:
            print("   - Model doesn't support CUDA. Check model specifications.")
        if not pipeline_ok:
            print("   - Pipeline configuration failed. Check error messages above.")

if __name__ == "__main__":
    main()