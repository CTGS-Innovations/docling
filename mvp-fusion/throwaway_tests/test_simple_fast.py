#!/usr/bin/env python3
"""
Test Simple Fast Processor - Verify A/B Integration
===================================================

GOAL: Test SimpleFastProcessor for A/B comparison with ServiceProcessor
REASON: Need working processor for pipeline sidecar testing
PROBLEM: Complex processors have import issues, need simple version

This tests the simple processor directly and via processor factory.
"""

import sys
from pathlib import Path

# Add pipeline path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_simple_processor():
    """Test SimpleFastProcessor directly."""
    print("🚀 Testing SimpleFastProcessor")
    print("=" * 50)
    
    try:
        from pipeline.simple_fast_processor import SimpleFastProcessor
        
        # Configuration
        config = {'pipeline': {'document_processing': {'target_time_ms': 30}}}
        processor = SimpleFastProcessor(config)
        
        # Find test files
        test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
        if test_dir.exists():
            files = list(test_dir.glob('*.pdf'))[:2]
            print(f"📁 Testing with {len(files)} files")
            
            # Run the test
            result = processor.process(files, {'output_dir': Path('/tmp')})
            
            if result.success:
                print(f"🟢 **SUCCESS**: {result.timing_ms:.2f}ms")
                print(f"   • Processed {result.data['processed_files']} files")
                print(f"   • Total size: {result.data['total_size_bytes'] / 1024:.1f} KB")
                print(f"   • Avg size: {result.data['avg_size_kb']:.1f} KB per file")
                
                target_ms = config['pipeline']['document_processing']['target_time_ms']
                if result.timing_ms < target_ms:
                    print(f"🟢 **UNDER TARGET**: {result.timing_ms:.2f}ms < {target_ms}ms")
                else:
                    print(f"🟡 **OVER TARGET**: {result.timing_ms:.2f}ms > {target_ms}ms")
                
                return True
            else:
                print(f"🔴 **FAILED**: {result.error}")
                return False
        else:
            print(f"❌ Test directory not found: {test_dir}")
            return False
            
    except Exception as e:
        print(f"❌ SimpleFastProcessor test failed: {e}")
        return False

def test_processor_factory():
    """Test SimpleFastProcessor via ProcessorFactory."""
    print("\n🚀 Testing ProcessorFactory Integration")
    print("=" * 50)
    
    try:
        from pipeline.processors import ProcessorFactory
        
        # Check available processors
        available = ProcessorFactory.get_available_processors()
        print(f"📋 Available processors: {available}")
        
        if 'simple_fast_processor' in available:
            print("✅ SimpleFastProcessor available in factory")
            
            # Create processor via factory
            config = {'max_workers': 2}
            processor = ProcessorFactory.create('simple_fast_processor', config)
            print("✅ SimpleFastProcessor created via factory")
            
            return True
        else:
            print("❌ SimpleFastProcessor not in factory")
            return False
            
    except Exception as e:
        print(f"❌ ProcessorFactory test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Fast Processor Integration Test")
    print("=" * 60)
    
    success1 = test_simple_processor()
    success2 = test_processor_factory()
    
    if success1 and success2:
        print("\n🟢 **READY**: SimpleFastProcessor ready for A/B sidecar testing")
    else:
        print("\n🔴 **BLOCKED**: SimpleFastProcessor needs fixes")