#!/usr/bin/env python3
"""
Test docling enrichment flags for optimal image processing
"""

import subprocess
import time
from pathlib import Path

def test_enrichment_config(config_name, extra_flags, test_file):
    """Test docling with specific enrichment configuration"""
    
    output_dir = Path(f"/tmp/enrichment_test_{config_name}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        'docling',
        str(test_file),
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cuda',
        '--num-threads', '8',
        '--page-batch-size', '4',
        '--pipeline', 'standard',  # Use fast standard pipeline
        '--pdf-backend', 'dlparse_v4'
    ]
    
    # Add enrichment flags
    cmd.extend(extra_flags)
    
    print(f"🧪 Testing {config_name}:")
    print(f"   Flags: {' '.join(extra_flags)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        throughput = 1 / duration * 60 if success else 0
        
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        
        return {
            'config': config_name,
            'flags': extra_flags,
            'success': success,
            'duration': duration,
            'throughput': throughput,
            'error': result.stderr[:500] if result.stderr else None,
            'stdout': result.stdout[:300] if result.stdout else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'config': config_name,
            'flags': extra_flags,
            'success': False,
            'duration': 60,
            'throughput': 0,
            'error': 'Timeout'
        }

def main():
    """Test different enrichment configurations"""
    
    # Find a test file with images
    data_dir = Path('/home/corey/projects/docling/cli/data')
    test_file = None
    
    for ext in ['pdf', 'docx', 'pptx']:  # Formats likely to have images
        files = list(data_dir.glob(f'**/*.{ext}'))
        if files:
            test_file = files[0]
            break
    
    if not test_file:
        print("❌ No suitable test files found")
        return
    
    print(f"🔍 Testing enrichment options with: {test_file.name}")
    print("=" * 60)
    
    # Different enrichment configurations to test
    configs = [
        {
            'name': 'baseline',
            'flags': []  # Standard pipeline only
        },
        {
            'name': 'picture_description', 
            'flags': ['--enrich-picture-description']  # Add image descriptions
        },
        {
            'name': 'picture_classes',
            'flags': ['--enrich-picture-classes']  # Add image classification
        },
        {
            'name': 'both_pictures',
            'flags': ['--enrich-picture-description', '--enrich-picture-classes']  # Both
        },
        {
            'name': 'all_enrichments',
            'flags': ['--enrich-picture-description', '--enrich-picture-classes', 
                     '--enrich-code', '--enrich-formula']  # Everything
        }
    ]
    
    results = []
    
    for config in configs:
        result = test_enrichment_config(config['name'], config['flags'], test_file)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ {result['config']:20} {result['throughput']:6.1f} files/min ({result['duration']:4.1f}s)")
        else:
            print(f"   ❌ {result['config']:20} FAILED - {result['error']}")
    
    # Analysis
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        print(f"\\n📊 ENRICHMENT PERFORMANCE COMPARISON:")
        print("=" * 60)
        
        # Sort by throughput
        successful_results.sort(key=lambda x: x['throughput'], reverse=True)
        
        baseline = next((r for r in successful_results if r['config'] == 'baseline'), None)
        best = successful_results[0]
        
        print(f"🏆 FASTEST: {best['config']} ({best['throughput']:.1f} files/min)")
        
        if baseline:
            print(f"📏 BASELINE: {baseline['config']} ({baseline['throughput']:.1f} files/min)")
            
            for result in successful_results:
                if result['config'] != 'baseline':
                    overhead = ((result['duration'] - baseline['duration']) / baseline['duration']) * 100
                    print(f"   {result['config']:20} {result['throughput']:6.1f} files/min ({overhead:+5.1f}% overhead)")
        
        print(f"\\n💡 RECOMMENDATIONS:")
        
        # Find best enrichment with reasonable overhead
        good_options = [r for r in successful_results if r['throughput'] > 50]  # Reasonable performance
        
        if any('picture_description' in str(r['flags']) for r in good_options):
            print(f"   ✅ Picture description adds VLM capabilities with reasonable performance")
        else:
            print(f"   ⚠️  Picture enrichment adds significant overhead")
            
        print(f"   🎯 Recommended: {best['config']} for optimal balance")
        
        # Compare to previous benchmarks
        baseline_throughput = 337  # files/min from standard pipeline
        if best['throughput'] < baseline_throughput * 0.8:  # Less than 80% of baseline
            print(f"   ⚠️  Significant performance impact vs pure standard pipeline")
        else:
            print(f"   ✅ Reasonable performance impact for added VLM capabilities")

if __name__ == "__main__":
    main()