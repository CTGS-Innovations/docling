#!/usr/bin/env python3
"""
Test FastDocProcessor Standalone - Verify Optimized Performance
===============================================================

GOAL: Test if FastDocProcessor shows performance improvements
REASON: Need to verify optimization before integrating with sidecar
PROBLEM: Want to compare fast vs slow text processing

This tests the optimized processor directly.
"""

import sys
from pathlib import Path

# Add pipeline path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_fast_processor():
    """Test FastDocProcessor performance."""
    print("🚀 Testing FastDocProcessor Performance")
    print("=" * 50)
    
    try:
        from pipeline.fast_doc_processor import FastDocProcessor
        
        # Configuration
        config = {'pipeline': {'document_processing': {'target_time_ms': 30}}}
        processor = FastDocProcessor(config)
        
        # Find test files
        test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
        if test_dir.exists():
            files = list(test_dir.glob('*.pdf'))[:2]  # First 2 PDFs only
            print(f"📁 Testing with {len(files)} files")
            for f in files:
                print(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
            
            # Run the test
            result = processor.process(files, {'output_dir': Path('/tmp')})
            
            # Display results
            print("\n" + "=" * 50)
            print("🎯 FAST PROCESSOR RESULTS")
            print("=" * 50)
            
            if result.success:
                analysis = result.data['bottleneck_analysis']
                print(f"🟢 **SUCCESS**: Test completed in {result.timing_ms:.2f}ms")
                print(f"🔴 **BOTTLENECK**: {analysis['slowest_operation']} ({analysis['slowest_time_ms']:.2f}ms)")
                
                # Show timing breakdown
                timing = result.data['timing_breakdown']
                for operation, time_ms in timing.items():
                    print(f"   • {operation}: {time_ms:.2f}ms")
                
                # Compare to target
                target_ms = config['pipeline']['document_processing']['target_time_ms']
                comparison = result.timing_ms / target_ms
                print(f"\n⏱️  **PERFORMANCE**: {comparison:.1f}x compared to {target_ms}ms target")
                
                if result.timing_ms < target_ms:
                    print("🟢 **UNDER TARGET** - Fast processor is working!")
                else:
                    print("🟡 **OVER TARGET** - Still needs optimization")
                
                return True
                
            else:
                print(f"🔴 **BLOCKED**: {result.error}")
                return False
                
        else:
            print(f"❌ Test directory not found: {test_dir}")
            return False
            
    except Exception as e:
        print(f"❌ FastDocProcessor test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fast_processor()
    if success:
        print("\n🟢 **READY**: FastDocProcessor working - can integrate with sidecar")
    else:
        print("\n🔴 **BLOCKED**: FastDocProcessor needs fixes before sidecar integration")