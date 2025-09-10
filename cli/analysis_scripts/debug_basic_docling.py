#!/usr/bin/env python3
"""
Debug basic docling command to see what's failing
"""

import subprocess
from pathlib import Path

def test_basic_docling():
    """Test the most basic docling command"""
    
    # Find a test file
    data_dir = Path('/home/corey/projects/docling/cli/data')
    test_file = list(data_dir.glob('**/*.pdf'))[0]
    
    output_dir = Path('/tmp/basic_docling_test')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Very basic command
    cmd = [
        'docling',
        str(test_file),
        '--to', 'md',
        '--output', str(output_dir)
    ]
    
    print(f"🧪 Testing basic docling command:")
    print(f"   File: {test_file.name}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"\\n📊 RESULTS:")
        print(f"Return code: {result.returncode}")
        print(f"Success: {'✅' if result.returncode == 0 else '❌'}")
        
        if result.stdout:
            print(f"\\n📝 STDOUT:")
            print(result.stdout)
            
        if result.stderr:
            print(f"\\n⚠️ STDERR:")
            print(result.stderr)
            
        # Check output files
        output_files = list(output_dir.glob('*.md'))
        if output_files:
            print(f"\\n✅ Generated {len(output_files)} output files:")
            for f in output_files:
                print(f"   - {f.name}")
        else:
            print(f"\\n❌ No output files generated")
            
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DEBUGGING BASIC DOCLING FUNCTIONALITY")
    print("=" * 50)
    
    success = test_basic_docling()
    
    if success:
        print("\\n✅ Basic docling works - issue is with specific flags")
    else:
        print("\\n❌ Basic docling failing - fundamental issue")
        print("💡 Check:")
        print("   - docling installation")
        print("   - Python environment")
        print("   - GPU drivers")
        print("   - Required dependencies")