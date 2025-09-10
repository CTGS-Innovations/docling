#!/usr/bin/env python3
"""
Quick OCR Engine Test
Tests different OCR engines to find the most reliable one for the benchmark
"""

import subprocess
import time
from pathlib import Path
import json

def test_ocr_engine(engine_name, test_file):
    """Test a specific OCR engine with a single file"""
    
    output_dir = Path(f"/tmp/ocr_test_{engine_name}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        'docling',
        str(test_file),
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cuda',
        '--num-threads', '2',
        '--page-batch-size', '1',
        '--pipeline', 'standard',
        '--pdf-backend', 'dlparse_v4'
    ]
    
    # Add OCR engine if specified
    if engine_name != 'default':
        cmd.extend(['--ocr-engine', engine_name])
    
    print(f"Testing {engine_name}: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        error = result.stderr if not success else None
        
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        return {
            'engine': engine_name,
            'success': success,
            'duration': duration,
            'error': error[:200] if error else None,
            'stdout': result.stdout[:200] if result.stdout else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'engine': engine_name,
            'success': False,
            'duration': 60,
            'error': 'Timeout after 60 seconds'
        }
    except Exception as e:
        return {
            'engine': engine_name,
            'success': False,
            'duration': 0,
            'error': str(e)
        }

def main():
    """Test all available OCR engines"""
    
    # Find a test file
    data_dir = Path('/home/corey/projects/docling/cli/data')
    test_files = []
    
    # Look for a simple PDF first
    for ext in ['*.pdf', '*.png', '*.jpg', '*.tiff']:
        files = list(data_dir.glob(f"**/{ext}"))
        if files:
            test_files.extend(files[:2])  # Take first 2 of each type
    
    if not test_files:
        print("❌ No test files found in /data directory")
        return
    
    test_file = test_files[0]  # Use first available file
    print(f"🧪 Testing OCR engines with: {test_file.name}")
    
    # Test different OCR engines
    engines_to_test = [
        'default',      # No --ocr-engine argument
        'easyocr',      # Default according to help
        'tesseract',    # What we tried initially
        'rapidocr',     # Alternative option
        'tesserocr'     # Another alternative
    ]
    
    results = []
    
    for engine in engines_to_test:
        print(f"\n🔍 Testing {engine}...")
        result = test_ocr_engine(engine, test_file)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ SUCCESS: {result['duration']:.1f}s")
        else:
            print(f"   ❌ FAILED: {result['error']}")
    
    # Summary
    print(f"\n📊 OCR Engine Test Results for {test_file.name}:")
    print("=" * 60)
    
    successful_engines = []
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = f"{result['duration']:.1f}s" if result['success'] else "N/A"
        error = result['error'][:50] + "..." if result['error'] and len(result['error']) > 50 else (result['error'] or "")
        
        print(f"{result['engine']:12} | {status:8} | {duration:8} | {error}")
        
        if result['success']:
            successful_engines.append({
                'engine': result['engine'],
                'duration': result['duration']
            })
    
    # Recommendation
    print("\n🎯 RECOMMENDATION:")
    if successful_engines:
        # Sort by speed (fastest first)
        successful_engines.sort(key=lambda x: x['duration'])
        fastest = successful_engines[0]
        print(f"   Use: --ocr-engine {fastest['engine']} (fastest working option)")
        print(f"   Alternatives: {[e['engine'] for e in successful_engines[1:]]}")
        
        # Generate code snippet
        if fastest['engine'] == 'default':
            print(f"\n💻 CODE: Remove --ocr-engine argument entirely")
        else:
            print(f"\n💻 CODE: '--ocr-engine', '{fastest['engine']}'")
            
    else:
        print("   ❌ No OCR engines worked - there may be a deeper configuration issue")
        print("   💡 Try running docling manually to debug")
    
    # Save detailed results
    results_file = Path('/home/corey/projects/docling/cli/tests/ocr_test_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed results saved: {results_file}")

if __name__ == "__main__":
    main()