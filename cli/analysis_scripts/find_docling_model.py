#!/usr/bin/env python3
"""
Find the exact model that docling uses for 'smoldocling'
"""

import subprocess
import tempfile
from pathlib import Path

def find_docling_vlm_model():
    """Try to determine what model docling uses for smoldocling"""
    
    print("🔍 Investigating docling's VLM model...")
    
    # Create a simple test file
    test_content = "# Test Document\n\nThis is a test."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        test_file = Path(f.name)
    
    try:
        # Try running docling with VLM pipeline and verbose output
        cmd = [
            'docling',
            str(test_file),
            '--to', 'md',
            '--output', '/tmp/docling_test_output',
            '--pipeline', 'vlm',
            '--vlm-model', 'smoldocling',
            '--device', 'cpu',  # Use CPU to avoid GPU conflicts
            '-vv'  # Very verbose
        ]
        
        print(f"🧪 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"\\n📊 DOCLING VLM MODEL INVESTIGATION:")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"\\n📝 STDOUT:")
            print(result.stdout)
            
        if result.stderr:
            print(f"\\n⚠️ STDERR:")  
            print(result.stderr)
            
            # Look for model loading information
            stderr_lines = result.stderr.split('\\n')
            for line in stderr_lines:
                if 'model' in line.lower() or 'loading' in line.lower() or 'huggingface' in line.lower():
                    print(f"🔍 Model info: {line}")
        
        # Try different approaches to find model info
        print(f"\\n🔍 Checking for common VLM model patterns...")
        
        # Try smoldocling_vllm to see if it gives different model info
        cmd_vllm = [
            'docling',
            str(test_file),
            '--to', 'md', 
            '--output', '/tmp/docling_test_output2',
            '--pipeline', 'vlm',
            '--vlm-model', 'smoldocling_vllm',
            '--device', 'cpu',
            '-vv'
        ]
        
        print(f"\\n🧪 Testing smoldocling_vllm: {' '.join(cmd_vllm)}")
        result_vllm = subprocess.run(cmd_vllm, capture_output=True, text=True, timeout=120)
        
        if result_vllm.stderr:
            print(f"\\n⚠️ smoldocling_vllm STDERR:")
            print(result_vllm.stderr[:1000])
            
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
    
    print(f"\\n💡 RECOMMENDATIONS:")
    print(f"   1. Check docling source code for exact model mapping")
    print(f"   2. Try common VLM models: SmolVLM, Florence-2, Qwen2-VL")
    print(f"   3. Start with CPU mode to avoid GPU conflicts during testing")

if __name__ == "__main__":
    find_docling_vlm_model()