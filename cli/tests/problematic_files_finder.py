#!/usr/bin/env python3
"""
Fast Problematic Files Finder
Uses binary search approach to quickly identify problematic files
"""

import subprocess
import time
from pathlib import Path
import json
from collections import defaultdict
import random

def test_file_batch(files, batch_name="test"):
    """Test a batch of files quickly to see if any cause issues"""
    
    if not files:
        return {'success': True, 'problematic_files': []}
    
    output_dir = Path(f"/tmp/batch_test_{batch_name}_{int(time.time())}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        'docling',
        '--to', 'md', 
        '--output', str(output_dir),
        '--device', 'cuda',
        '--num-threads', '12',
        '--page-batch-size', '1',  # Process individually to isolate issues
        '--pipeline', 'standard',
        '--pdf-backend', 'dlparse_v4'
    ]
    
    # Add files to command
    cmd.extend([str(f) for f in files])
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)  # Fast timeout
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        # Quick cleanup
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        
        # Identify problematic files if batch failed
        problematic = []
        if not success and result.stderr:
            # Look for specific file mentions in error
            error_text = result.stderr.lower()
            for file_path in files:
                if file_path.name.lower() in error_text or str(file_path).lower() in error_text:
                    problematic.append(file_path)
        
        return {
            'success': success,
            'duration': duration,
            'file_count': len(files),
            'problematic_files': problematic,
            'error_snippet': result.stderr[:200] if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
        return {
            'success': False,
            'duration': 60,
            'file_count': len(files),
            'problematic_files': files,  # Assume all files are problematic if timeout
            'error_snippet': 'Batch timeout - likely contains slow/problematic files'
        }
    except Exception as e:
        return {
            'success': False,
            'duration': 0,
            'file_count': len(files),
            'problematic_files': files,
            'error_snippet': str(e)
        }

def binary_search_problematic_files(files):
    """Use binary search to quickly find problematic files in a batch"""
    
    if len(files) <= 1:
        if files:
            # Test single file
            result = test_file_batch(files, "single")
            return files if not result['success'] else []
        return []
    
    # Split files in half
    mid = len(files) // 2
    left_half = files[:mid]
    right_half = files[mid:]
    
    print(f"   Testing {len(left_half)} files... ", end="", flush=True)
    left_result = test_file_batch(left_half, "left")
    
    print(f"Testing {len(right_half)} files... ", end="", flush=True)
    right_result = test_file_batch(right_half, "right")
    
    problematic = []
    
    # Recursively search problematic halves
    if not left_result['success']:
        print(f"❌ Left half has issues, drilling down...")
        problematic.extend(binary_search_problematic_files(left_half))
    else:
        print(f"✅ Left half OK")
    
    if not right_result['success']:
        print(f"❌ Right half has issues, drilling down...")  
        problematic.extend(binary_search_problematic_files(right_half))
    else:
        print(f"✅ Right half OK")
    
    return problematic

def main():
    """Fast binary search to find problematic files"""
    
    data_dir = Path('/home/corey/projects/docling/cli/data')
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Find all files quickly
    all_files = []
    supported_extensions = {'.pdf', '.docx', '.pptx', '.html', '.md', '.csv', '.xlsx', 
                          '.png', '.jpg', '.jpeg', '.tiff', '.webp', '.asciidoc'}
    
    for ext in supported_extensions:
        files = list(data_dir.glob(f"**/*{ext}"))
        all_files.extend(files)
    
    print(f"🚀 FAST PROBLEMATIC FILE FINDER")
    print(f"🔍 Found {len(all_files)} files - using binary search approach")
    print(f"⏱️  This should take ~2-5 minutes instead of hours\n")
    
    # Quick initial test with all files
    print(f"🧪 Step 1: Testing all {len(all_files)} files together...")
    initial_result = test_file_batch(all_files, "all")
    
    if initial_result['success']:
        print("✅ All files process successfully!")
        print("💡 The chunk failures might be due to batch size or timing issues")
        print("🎯 Try reducing batch size in your benchmark script")
        return
    
    print(f"❌ Found issues! Starting binary search to isolate problematic files...")
    print(f"🔍 Error preview: {initial_result['error_snippet'][:100]}...\n")
    
    # Binary search to find problematic files
    print(f"🔎 Step 2: Binary search through files...")
    start_time = time.time()
    problematic_files = binary_search_problematic_files(all_files)
    search_time = time.time() - start_time
    
    print(f"\n📊 FAST ANALYSIS COMPLETE ({search_time:.1f}s):")
    print("=" * 60)
    print(f"Total files scanned: {len(all_files)}")
    print(f"Problematic files found: {len(problematic_files)}")
    print(f"Success rate: {((len(all_files) - len(problematic_files)) / len(all_files) * 100):.1f}%")
    
    if problematic_files:
        print(f"\n❌ PROBLEMATIC FILES ({len(problematic_files)}):")
        print("-" * 60)
        
        # Group by extension and size
        by_extension = defaultdict(list)
        large_files = []
        
        for file_path in problematic_files:
            ext = file_path.suffix.lower()
            size_mb = file_path.stat().st_size / (1024*1024) if file_path.exists() else 0
            
            by_extension[ext].append(file_path.name)
            if size_mb > 10:  # Files larger than 10MB
                large_files.append((file_path.name, size_mb))
        
        # Show breakdown by file type
        for ext, filenames in by_extension.items():
            print(f"\n🔸 {ext.upper()} files: {len(filenames)}")
            for filename in filenames[:3]:  # Show first 3
                print(f"   - {filename}")
            if len(filenames) > 3:
                print(f"   ... and {len(filenames) - 3} more")
        
        # Show large files
        if large_files:
            print(f"\n📏 LARGE FILES (>10MB):")
            large_files.sort(key=lambda x: x[1], reverse=True)
            for filename, size in large_files[:5]:
                print(f"   - {filename} ({size:.1f} MB)")
    
    # Quick recommendations
    print(f"\n🎯 QUICK RECOMMENDATIONS:")
    if len(problematic_files) < len(all_files) * 0.1:  # Less than 10% problematic
        print(f"   ✅ Only {len(problematic_files)} problematic files ({len(problematic_files)/len(all_files)*100:.1f}%)")
        print("   🔧 Exclude these files from benchmarking for clean results")
        print("   💡 Or add specific error handling for these files")
    else:
        print(f"   ⚠️  High failure rate ({len(problematic_files)/len(all_files)*100:.1f}%)")
        print("   🔧 Consider using smaller batch sizes")
        print("   💡 Or investigate common file characteristics")
    
    # Save results (much faster format)
    results = {
        'analysis_time_seconds': search_time,
        'total_files': len(all_files),
        'problematic_count': len(problematic_files),
        'success_rate': ((len(all_files) - len(problematic_files)) / len(all_files)) * 100,
        'problematic_files': [str(f) for f in problematic_files],
        'by_extension': {k: len(v) for k, v in by_extension.items()},
        'initial_error': initial_result['error_snippet']
    }
    
    results_file = Path('/home/corey/projects/docling/cli/tests/fast_problematic_files_analysis.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Fast analysis saved: {results_file}")
    
    # Generate exclusion list 
    if problematic_files:
        exclusion_list = [f.name for f in problematic_files]
        exclusion_file = Path('/home/corey/projects/docling/cli/tests/files_to_exclude.txt')
        with open(exclusion_file, 'w') as f:
            f.write('\n'.join(exclusion_list))
        print(f"📝 Exclusion list saved: {exclusion_file}")
        
        print(f"\n💻 BENCHMARK UPDATE:")
        print(f"   Add file exclusion logic to skip {len(problematic_files)} problematic files")
        print(f"   Or use smaller batch sizes to handle mixed file complexity")

if __name__ == "__main__":
    main()