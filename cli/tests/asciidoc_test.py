#!/usr/bin/env python3
"""
AsciiDoc Processing Test
Tests different approaches to process AsciiDoc files with docling
"""

import subprocess
import time
from pathlib import Path
import json

def test_asciidoc_processing(file_path, test_config):
    """Test AsciiDoc processing with specific configuration"""
    
    output_dir = Path(f"/tmp/asciidoc_test_{test_config['name']}_{int(time.time())}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        'docling',
        str(file_path),
        '--to', 'md',
        '--output', str(output_dir),
    ]
    
    # Add configuration options
    for key, value in test_config['args'].items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        else:
            cmd.extend([f"--{key}", str(value)])
    
    print(f"🧪 Testing {test_config['name']}: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        
        return {
            'config_name': test_config['name'],
            'success': success,
            'duration': duration,
            'error': result.stderr[:500] if result.stderr else None,
            'stdout': result.stdout[:300] if result.stdout else None
        }
        
    except subprocess.TimeoutExpired:
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        return {
            'config_name': test_config['name'],
            'success': False,
            'duration': 60,
            'error': 'Timeout after 60 seconds'
        }
    except Exception as e:
        return {
            'config_name': test_config['name'],
            'success': False,
            'duration': 0,
            'error': str(e)
        }

def main():
    """Test AsciiDoc files with different docling configurations"""
    
    data_dir = Path('/home/corey/projects/docling/cli/data')
    asciidoc_files = list(data_dir.glob("**/*.asciidoc"))
    
    if not asciidoc_files:
        print("❌ No AsciiDoc files found in data directory")
        return
    
    test_file = asciidoc_files[0]  # Test with first AsciiDoc file
    print(f"🔍 Testing AsciiDoc processing with: {test_file.name}")
    print(f"📏 File size: {test_file.stat().st_size / 1024:.1f} KB\\n")
    
    # Different configurations to test
    test_configs = [
        {
            'name': 'minimal',
            'args': {
                'device': 'cpu',
                'num-threads': '1',
                'pipeline': 'standard'
            }
        },
        {
            'name': 'explicit_format',
            'args': {
                'from': 'asciidoc',  # Explicitly specify input format
                'device': 'cpu',
                'num-threads': '1',
                'pipeline': 'standard'
            }
        },
        {
            'name': 'no_ocr',
            'args': {
                'device': 'cpu',
                'num-threads': '1',
                'pipeline': 'standard',
                'no-ocr': True  # Disable OCR for text files
            }
        },
        {
            'name': 'text_pipeline',
            'args': {
                'to': 'text',  # Try text output instead of markdown
                'device': 'cpu',
                'num-threads': '1',
                'pipeline': 'standard'
            }
        },
        {
            'name': 'gpu_standard',
            'args': {
                'device': 'cuda',
                'num-threads': '4',
                'pipeline': 'standard',
                'page-batch-size': '1'
            }
        },
        {
            'name': 'current_benchmark_config',
            'args': {
                'device': 'cuda',
                'num-threads': '12',
                'page-batch-size': '1',
                'pipeline': 'standard',
                'pdf-backend': 'dlparse_v4'
            }
        }
    ]
    
    results = []
    
    print("🚀 Testing different AsciiDoc processing configurations:\\n")
    
    for config in test_configs:
        result = test_asciidoc_processing(test_file, config)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ {config['name']:20} SUCCESS ({result['duration']:.1f}s)")
        else:
            print(f"   ❌ {config['name']:20} FAILED")
            if result['error']:
                print(f"      Error: {result['error'][:100]}...")
    
    # Analysis
    successful_configs = [r for r in results if r['success']]
    
    print(f"\\n📊 ASCIIDOC PROCESSING ANALYSIS:")
    print("=" * 60)
    print(f"File tested: {test_file.name}")
    print(f"Successful configs: {len(successful_configs)}/{len(results)}")
    
    if successful_configs:
        fastest = min(successful_configs, key=lambda x: x['duration'])
        print(f"\\n🏆 RECOMMENDED CONFIG: {fastest['config_name']}")
        print(f"   Duration: {fastest['duration']:.1f}s")
        print(f"   This configuration works reliably for AsciiDoc files")
        
        print(f"\\n✅ WORKING CONFIGURATIONS:")
        for result in successful_configs:
            print(f"   - {result['config_name']:20} ({result['duration']:.1f}s)")
    else:
        print("\\n❌ NO CONFIGURATIONS WORKED")
        print("   This suggests a deeper issue with AsciiDoc support")
    
    # Specific recommendations
    print(f"\\n🎯 RECOMMENDATIONS FOR BENCHMARK:")
    if successful_configs:
        if any(r['config_name'] == 'explicit_format' for r in successful_configs):
            print("   💡 Use --from asciidoc to explicitly specify input format")
        if any(r['config_name'] == 'no_ocr' for r in successful_configs):
            print("   💡 Use --no-ocr flag for AsciiDoc files (they're text, not images)")
        if any(r['config_name'] == 'minimal' for r in successful_configs):
            print("   💡 Use CPU processing for AsciiDoc files (simpler than GPU)")
        
        print(f"\\n💻 BENCHMARK UPDATE:")
        print(f"   Add special handling for AsciiDoc files:")
        print(f"   - Use working configuration from test")
        print(f"   - Process AsciiDoc files separately from other formats")
        print(f"   - Consider disabling OCR for text-based formats")
    else:
        print("   🔍 Investigate AsciiDoc file content - may have formatting issues")
        print("   📝 Consider converting AsciiDoc to Markdown first")
    
    # Save detailed results
    results_file = Path('/home/corey/projects/docling/cli/tests/asciidoc_analysis.json')
    with open(results_file, 'w') as f:
        json.dump({
            'test_file': str(test_file),
            'file_size_kb': test_file.stat().st_size / 1024,
            'successful_configs': len(successful_configs),
            'total_configs': len(results),
            'results': results
        }, f, indent=2)
    
    print(f"\\n💾 Detailed analysis saved: {results_file}")

if __name__ == "__main__":
    main()