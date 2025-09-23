#!/usr/bin/env python3
"""
Test Integrated Sidecar Processor
=================================

GOAL: Test if OptimizedDocProcessor integrates properly with pipeline
REASON: Verify sidecar works with A/B testing framework
PROBLEM: Need working sidecar integration for production use

This tests the optimized processor through the factory system.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_optimized_processor_direct():
    """Test OptimizedDocProcessor directly."""
    print("🚀 Testing OptimizedDocProcessor Direct Import")
    print("=" * 50)
    
    try:
        # Direct import (bypassing factory issues)
        sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
        
        from optimized_doc_processor import OptimizedDocProcessor
        
        # Test instantiation
        config = {'test': True}
        processor = OptimizedDocProcessor(config)
        
        print(f"✅ OptimizedDocProcessor created: {processor.name}")
        
        # Test with files
        test_dir = Path('/home/corey/projects/docling/cli/data_complex/complex_pdfs')
        if test_dir.exists():
            files = list(test_dir.glob('*.pdf'))[:2]
            print(f"📁 Testing with {len(files)} files")
            
            result = processor.process(files, {'output_dir': '/tmp'})
            
            if result.success:
                print(f"🟢 **SUCCESS**: {result.timing_ms:.2f}ms")
                print(f"   • Processed {result.data['processed_files']} files")
                print(f"   • Speedup level: {result.data['optimization_level']}")
                print(f"   • Optimizations: {result.data['optimizations_applied']}")
                
                # Compare to target
                target_ms = 30
                if result.timing_ms < target_ms:
                    print(f"🟢 **UNDER TARGET**: {result.timing_ms:.2f}ms < {target_ms}ms")
                else:
                    print(f"🟡 **OVER TARGET**: {result.timing_ms:.2f}ms > {target_ms}ms")
                
                return True
            else:
                print(f"🔴 **FAILED**: {result.error}")
                return False
        else:
            print("❌ Test directory not found")
            return False
            
    except Exception as e:
        print(f"❌ OptimizedDocProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processor_factory_integration():
    """Test if processor can be created via factory."""
    print("\n🚀 Testing ProcessorFactory Integration")
    print("=" * 50)
    
    try:
        # Try to import and use the factory
        # This might fail due to Unicode issues, but worth testing
        
        from pipeline.processors import ProcessorFactory
        
        available = ProcessorFactory.get_available_processors()
        print(f"📋 Available processors: {available}")
        
        if 'optimized_doc_processor' in available:
            print("✅ OptimizedDocProcessor available in factory")
            
            # Try to create via factory
            config = {'max_workers': 2}
            processor = ProcessorFactory.create('optimized_doc_processor', config)
            print("✅ OptimizedDocProcessor created via factory")
            
            return True
        else:
            print("❌ OptimizedDocProcessor not in factory")
            return False
            
    except Exception as e:
        print(f"❌ ProcessorFactory integration failed: {e}")
        print("   (This is expected due to Unicode import issues)")
        return False

if __name__ == "__main__":
    print("🚀 Integrated Sidecar Processor Test")
    print("=" * 60)
    
    success1 = test_optimized_processor_direct()
    success2 = test_processor_factory_integration()
    
    if success1:
        print("\n🟢 **READY**: OptimizedDocProcessor works directly")
        if success2:
            print("🟢 **INTEGRATED**: Sidecar fully integrated with pipeline")
        else:
            print("🟡 **PARTIAL**: Sidecar works but factory has import issues")
    else:
        print("\n🔴 **BLOCKED**: OptimizedDocProcessor needs fixes")