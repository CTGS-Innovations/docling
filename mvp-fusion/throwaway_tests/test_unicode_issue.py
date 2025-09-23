#!/usr/bin/env python3
"""
Unicode Issue Investigation
===========================

GOAL: Find exact source of 0xa0 byte causing Unicode decode error
REASON: FastDocProcessor import failing with Unicode issue
PROBLEM: Need to isolate and fix Unicode problem

This systematically tests imports to find the Unicode issue.
"""

import sys
from pathlib import Path

def test_file_encoding():
    """Check for Unicode issues in fast_doc_processor.py."""
    print("🔍 Checking fast_doc_processor.py encoding...")
    
    file_path = Path(__file__).parent.parent / 'pipeline' / 'fast_doc_processor.py'
    
    try:
        # Check for 0xa0 bytes
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Find 0xa0 bytes
        a0_positions = []
        for i, byte in enumerate(content):
            if byte == 0xa0:
                a0_positions.append(i)
        
        if a0_positions:
            print(f"❌ Found {len(a0_positions)} 0xa0 bytes at positions: {a0_positions[:5]}...")
            
            # Show context around first 0xa0
            pos = a0_positions[0]
            start = max(0, pos - 20)
            end = min(len(content), pos + 20)
            context = content[start:end]
            print(f"Context around first 0xa0: {context}")
            
            # Calculate line number
            line_num = content[:pos].count(b'\n') + 1
            print(f"0xa0 byte is on line {line_num}")
            
        else:
            print("✅ No 0xa0 bytes found in fast_doc_processor.py")
            
        # Try UTF-8 decode
        try:
            text_content = content.decode('utf-8')
            print("✅ File decodes as UTF-8 successfully")
        except UnicodeDecodeError as e:
            print(f"❌ UTF-8 decode failed: {e}")
            
    except Exception as e:
        print(f"❌ File check failed: {e}")

def test_minimal_import():
    """Test minimal import without any dependencies."""
    print("\n🔍 Testing minimal import...")
    
    try:
        # Add pipeline to path
        pipeline_path = Path(__file__).parent.parent / 'pipeline'
        sys.path.insert(0, str(pipeline_path))
        
        # Try importing just the time module (should work)
        import time
        print("✅ time module import OK")
        
        # Try importing pathlib 
        from pathlib import Path
        print("✅ pathlib import OK")
        
        # Try importing the actual file
        print("Attempting fast_doc_processor import...")
        import fast_doc_processor
        print("✅ fast_doc_processor import OK")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    print("🚀 Unicode Issue Investigation")
    print("=" * 50)
    
    test_file_encoding()
    test_minimal_import()