#!/usr/bin/env python3
"""
Test different VLM models with docling to find the fastest one
"""

import subprocess
import time
import tempfile
from pathlib import Path

def test_vlm_model(model_name, test_file):
    """Test a specific VLM model with docling"""
    
    output_dir = Path(f"/tmp/vlm_test_{model_name.replace('/', '_').replace('-', '_')}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        'docling',
        str(test_file),
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cuda',
        '--num-threads', '4',
        '--page-batch-size', '2',
        '--pipeline', 'vlm',
        '--vlm-model', model_name
    ]
    
    print(f"🧪 Testing {model_name}: {' '.join(cmd[-3:])}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        
        return {
            'model': model_name,
            'success': success,
            'duration': duration,
            'throughput': 1 / duration * 60 if success else 0,  # files per minute
            'error': result.stderr[:300] if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'model': model_name,
            'success': False,
            'duration': 120,
            'throughput': 0,
            'error': 'Timeout after 120 seconds'
        }
    except Exception as e:
        return {
            'model': model_name,
            'success': False,
            'duration': 0,
            'throughput': 0,
            'error': str(e)
        }

def main():
    """Test all available VLM models"""
    
    # Create a simple test PDF or use existing file
    data_dir = Path('/home/corey/projects/docling/cli/data')
    
    # Find a test file
    test_file = None
    for ext in ['pdf', 'png', 'jpg', 'docx']:
        files = list(data_dir.glob(f'**/*.{ext}'))
        if files:
            test_file = files[0]
            break
    
    if not test_file:
        print("❌ No suitable test files found")
        return
    
    print(f"🔍 Testing VLM models with: {test_file.name}")
    
    # Models to test based on docling documentation
    models_to_test = [
        'smoldocling',              # Default - should use Transformers
        'smoldocling_vllm',         # vLLM accelerated version (if it exists)
        'granite_vision',           # Alternative model
        'granite_vision_vllm',      # vLLM version (if it exists)
        'got_ocr_2'                 # OCR-focused model
    ]
    
    print(f"🚀 Testing {len(models_to_test)} VLM models:")
    print("=" * 60)
    
    results = []
    
    for model in models_to_test:
        result = test_vlm_model(model, test_file)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ {model:20} {result['throughput']:6.1f} files/min ({result['duration']:4.1f}s)")
        else:
            print(f"   ❌ {model:20} FAILED - {result['error'][:50]}...")
    
    # Analysis
    successful_results = [r for r in results if r['success']]
    
    print(f"\\n📊 VLM MODEL PERFORMANCE COMPARISON:")
    print("=" * 60)
    
    if successful_results:
        # Sort by throughput
        successful_results.sort(key=lambda x: x['throughput'], reverse=True)
        
        print(f"🏆 FASTEST MODEL: {successful_results[0]['model']}")
        print(f"   Throughput: {successful_results[0]['throughput']:.1f} files/minute")
        print(f"   Duration: {successful_results[0]['duration']:.1f} seconds")
        
        print(f"\\n📈 PERFORMANCE RANKING:")
        for i, result in enumerate(successful_results, 1):
            print(f"   {i}. {result['model']:20} {result['throughput']:6.1f} files/min")
        
        print(f"\\n💡 RECOMMENDATIONS:")
        fastest = successful_results[0]
        if '_vllm' in fastest['model']:
            print(f"   ✅ vLLM acceleration working: Use --vlm-model {fastest['model']}")
        else:
            print(f"   ⚠️  Standard model fastest: vLLM may not provide benefit")
            
        print(f"   🎯 Use {fastest['model']} for maximum throughput")
        
        # Compare to previous benchmark
        baseline_throughput = 81.5  # files/min from previous benchmark
        if fastest['throughput'] > baseline_throughput:
            improvement = (fastest['throughput'] / baseline_throughput - 1) * 100
            print(f"   🚀 {improvement:+.1f}% faster than baseline ({baseline_throughput} files/min)")
        else:
            decrease = (1 - fastest['throughput'] / baseline_throughput) * 100
            print(f"   ⚠️  {decrease:.1f}% slower than baseline ({baseline_throughput} files/min)")
            
    else:
        print("❌ No VLM models worked - check installation and GPU availability")

if __name__ == "__main__":
    main()