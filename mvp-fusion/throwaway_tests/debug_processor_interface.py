#!/usr/bin/env python3
"""
Debug Processor Interface Issue
==============================

GOAL: Understand what interface the pipeline expects vs what optimized processor returns
REASON: Getting 'str' object has no attribute 'success' error
PROBLEM: Interface mismatch between optimized processor and pipeline expectations

This debugs the processor interface to fix the compatibility issue.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def debug_service_processor():
    """Debug what ServiceProcessor actually returns."""
    print("🔍 Debugging ServiceProcessor Interface")
    print("=" * 50)
    
    try:
        # Test ServiceProcessor interface
        sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline' / 'legacy'))
        from service_processor import ServiceProcessor
        
        config = {'max_workers': 2}
        processor = ServiceProcessor(config, 2)
        
        # Find test files
        test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
        if test_dir.exists():
            files = list(test_dir.glob('*.pdf'))[:1]  # Just 1 file for testing
            output_dir = Path('/tmp')
            
            print(f"📁 Testing with: {files[0].name}")
            
            # Call process_files_service
            result = processor.process_files_service(files, output_dir)
            
            print(f"📊 ServiceProcessor returns:")
            print(f"   Type: {type(result)}")
            print(f"   Length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if isinstance(result, tuple):
                print(f"   Tuple[0] type: {type(result[0])}")
                print(f"   Tuple[1] type: {type(result[1])}")
                if hasattr(result[0], '__len__'):
                    print(f"   Tuple[0] length: {len(result[0])}")
                    if len(result[0]) > 0:
                        print(f"   First item type: {type(result[0][0])}")
                        if hasattr(result[0][0], 'success'):
                            print(f"   First item has .success: {result[0][0].success}")
                        else:
                            print(f"   First item attributes: {dir(result[0][0])[:5]}...")
                
            return result
        else:
            print("❌ Test directory not found")
            return None
            
    except Exception as e:
        print(f"❌ ServiceProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def debug_optimized_processor():
    """Debug what OptimizedProcessor returns."""
    print("\n🔍 Debugging OptimizedProcessor Interface")
    print("=" * 50)
    
    try:
        # Test OptimizedProcessor interface
        sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
        from optimized_doc_processor import OptimizedDocProcessorWrapper
        
        config = {'max_workers': 2}
        processor = OptimizedDocProcessorWrapper(config)
        
        # Find test files
        test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
        if test_dir.exists():
            files = list(test_dir.glob('*.pdf'))[:1]  # Just 1 file for testing
            output_dir = Path('/tmp')
            
            print(f"📁 Testing with: {files[0].name}")
            
            # Call process_files_service
            result = processor.process_files_service(files, output_dir)
            
            print(f"📊 OptimizedProcessor returns:")
            print(f"   Type: {type(result)}")
            print(f"   Length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if isinstance(result, tuple):
                print(f"   Tuple[0] type: {type(result[0])}")
                print(f"   Tuple[1] type: {type(result[1])}")
                if hasattr(result[0], '__len__'):
                    print(f"   Tuple[0] length: {len(result[0])}")
                    if len(result[0]) > 0:
                        print(f"   First item type: {type(result[0][0])}")
                        if hasattr(result[0][0], 'success'):
                            print(f"   First item has .success: {result[0][0].success}")
                        else:
                            print(f"   First item: {result[0][0]}")
                
            return result
        else:
            print("❌ Test directory not found")
            return None
            
    except Exception as e:
        print(f"❌ OptimizedProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Processor Interface Debug")
    print("=" * 60)
    
    service_result = debug_service_processor()
    optimized_result = debug_optimized_processor()
    
    print("\n🎯 COMPARISON SUMMARY")
    print("=" * 60)
    
    if service_result and optimized_result:
        print("✅ Both processors returned results")
        print(f"ServiceProcessor: {type(service_result)}")
        print(f"OptimizedProcessor: {type(optimized_result)}")
        
        if type(service_result) == type(optimized_result):
            print("✅ Return types match")
        else:
            print("❌ Return types differ - this is the interface problem!")
    else:
        print("❌ One or both processors failed")