#!/usr/bin/env python3
"""
Simple AsciiDoc Test - Test with basic AsciiDoc without image references
"""

import subprocess
import time
from pathlib import Path

def test_simple_asciidoc():
    """Test with a simple AsciiDoc file without image references"""
    
    # Create a simple AsciiDoc file without image references
    simple_content = """= Simple Test Document

This is a simple AsciiDoc document for testing.

== Section 1

Basic text content here.

* List item 1
* List item 2
* List item 3

== Section 2

More text content without any image references.

.Code Example
----
print("Hello World")
----

That's it - no images, no complex references.
"""
    
    test_file = Path('/tmp/simple_test.asciidoc')
    with open(test_file, 'w') as f:
        f.write(simple_content)
    
    output_dir = Path('/tmp/simple_asciidoc_output')
    output_dir.mkdir(exist_ok=True)
    
    cmd = [
        'docling',
        str(test_file),
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cpu',
        '--num-threads', '1',
        '--pipeline', 'standard'
    ]
    
    print("🧪 Testing simple AsciiDoc without image references...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        print(f"\n📊 SIMPLE ASCIIDOC RESULTS:")
        print(f"Success: {'✅ YES' if success else '❌ NO'}")
        print(f"Duration: {duration:.1f}s")
        
        if success:
            print("✅ Simple AsciiDoc works fine!")
            print("💡 The issue is likely the missing image references in your test files")
        else:
            print("❌ Even simple AsciiDoc fails:")
            print(f"Error: {result.stderr[:300]}")
        
        # Check output
        if success:
            output_files = list(output_dir.glob('*.md'))
            if output_files:
                print(f"📄 Generated: {output_files[0].name}")
                with open(output_files[0], 'r') as f:
                    content = f.read()[:200]
                print(f"Content preview: {content}...")
        
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def create_dummy_images():
    """Create dummy image files for the original AsciiDoc"""
    
    data_dir = Path('/home/corey/projects/docling/cli/data/asciidoc')
    
    # Create dummy PNG files
    dummy_images = [
        'rename-bookmark-menu.png',
        'rename-bookmark-text.png', 
        'renamed-bookmark.png'
    ]
    
    print("🖼️  Creating dummy image files...")
    
    # Create a minimal 1x1 pixel PNG (base64 encoded)
    png_data = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a4944415478da6300010000050001')
    
    created_files = []
    for img_name in dummy_images:
        img_path = data_dir / img_name
        if not img_path.exists():
            with open(img_path, 'wb') as f:
                f.write(png_data)
            created_files.append(img_path)
            print(f"   Created: {img_name}")
    
    return created_files

def test_original_with_dummy_images():
    """Test original AsciiDoc file after creating dummy images"""
    
    created_files = create_dummy_images()
    
    original_file = Path('/home/corey/projects/docling/cli/data/asciidoc/test_03.asciidoc')
    output_dir = Path('/tmp/asciidoc_with_images_output')
    output_dir.mkdir(exist_ok=True)
    
    cmd = [
        'docling',
        str(original_file),
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cpu',
        '--num-threads', '1',
        '--pipeline', 'standard'
    ]
    
    print(f"\n🧪 Testing original AsciiDoc with dummy images...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        success = result.returncode == 0
        
        print(f"Success with dummy images: {'✅ YES' if success else '❌ NO'}")
        
        if success:
            print("✅ FIXED! The issue was missing image files")
            print("💡 AsciiDoc files work when referenced images exist")
        else:
            print("❌ Still failing even with dummy images")
            print(f"Error: {result.stderr[:300]}")
            
        # Clean up dummy files
        for file_path in created_files:
            if file_path.exists():
                file_path.unlink()
                print(f"   Cleaned up: {file_path.name}")
                
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run comprehensive AsciiDoc diagnosis"""
    
    print("🔍 ASCIIDOC DIAGNOSIS - Testing hypothesis about missing images\n")
    
    # Test 1: Simple AsciiDoc without images
    simple_success = test_simple_asciidoc()
    
    # Test 2: Original AsciiDoc with dummy images
    if simple_success:
        original_success = test_original_with_dummy_images()
        
        print(f"\n🎯 DIAGNOSIS COMPLETE:")
        print(f"Simple AsciiDoc (no images): {'✅ WORKS' if simple_success else '❌ FAILS'}")  
        print(f"Original AsciiDoc (with dummy images): {'✅ WORKS' if original_success else '❌ FAILS'}")
        
        if simple_success and original_success:
            print(f"\n💡 ROOT CAUSE IDENTIFIED:")
            print(f"   AsciiDoc files with missing image references cause processing failures")
            print(f"   Solution: Either provide the missing images or handle missing references gracefully")
            
            print(f"\n🔧 BENCHMARK FIXES:")
            print(f"   Option 1: Skip AsciiDoc files with image references")
            print(f"   Option 2: Create dummy placeholder images")
            print(f"   Option 3: Use a different pipeline that ignores missing images")
            
        elif simple_success:
            print(f"\n💡 PARTIAL SUCCESS:")
            print(f"   Simple AsciiDoc works, but there's still an issue with the original file")
            print(f"   May need further investigation")
    else:
        print(f"\n❌ DEEPER ISSUE:")
        print(f"   Even simple AsciiDoc fails - there may be a broader AsciiDoc support issue")

if __name__ == "__main__":
    main()