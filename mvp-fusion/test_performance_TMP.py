#!/usr/bin/env python3
"""
Performance Test Script - Isolate Classification Bottleneck
Creates controlled test files to measure where the 12-second delay occurs
"""

import time
import tempfile
import os
from pathlib import Path

def create_test_files():
    """Create test files of varying complexity"""
    test_dir = Path("test_files_TMP")
    test_dir.mkdir(exist_ok=True)
    
    # Test 1: Minimal content
    with open(test_dir / "minimal.txt", "w") as f:
        f.write("Simple test document with minimal content.")
    
    # Test 2: Government entities only
    with open(test_dir / "government.txt", "w") as f:
        f.write("""
        Government Document Test
        GAO report shows NASA budget increases.
        EPA regulations updated by Department of Defense.
        Library of Congress archives FDA documents.
        """)
    
    # Test 3: Complex entities
    with open(test_dir / "complex.txt", "w") as f:
        f.write("""
        Business Document Test
        SpaceX received $100M from Sequoia Capital.
        Microsoft Corp acquired GitHub for $7.5B.
        Apple Inc reported 25% growth in California.
        Tesla stock increased by 15% in Texas markets.
        """)
    
    # Test 4: Large content (same entities repeated)
    large_content = "GAO NASA EPA FDA. " * 1000  # Repeat simple content
    with open(test_dir / "large_simple.txt", "w") as f:
        f.write(f"Large Document Test\n{large_content}")
    
    # Test 5: Complex large content
    complex_large = """
    SpaceX received $100M from Sequoia Capital in California.
    Microsoft Corp acquired GitHub for $7.5B with 25% growth.
    Apple Inc reported strong performance in Texas markets.
    Tesla stock increased by 15% according to NASA reports.
    """ * 500  # Repeat complex content
    with open(test_dir / "large_complex.txt", "w") as f:
        f.write(f"Complex Large Document Test\n{complex_large}")
    
    return test_dir

def run_performance_test():
    """Run performance test with timing"""
    print("🧪 PERFORMANCE BOTTLENECK TEST")
    print("=" * 50)
    
    # Create test files
    test_dir = create_test_files()
    print(f"📁 Created test files in: {test_dir}")
    
    # Test each file individually
    for test_file in sorted(test_dir.glob("*.txt")):
        print(f"\n🔍 Testing: {test_file.name}")
        
        # Time just the classification stage
        start_time = time.perf_counter()
        
        # Run MVP-Fusion classification only
        cmd = f'source .venv-clean/bin/activate && python fusion_cli.py --file "{test_file}" --classify-only -q'
        print(f"  Command: {cmd}")
        
        # Run the classification test
        print(f"  🔄 Running classification test...")
        result = os.system(cmd)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Get file size for analysis
        file_size = test_file.stat().st_size
        
        print(f"  ⏱️  Time: {duration:.3f}s")
        print(f"  📄 Size: {file_size:,} bytes")
        print(f"  🚀 Rate: {file_size/duration/1024:.1f} KB/s")

if __name__ == "__main__":
    run_performance_test()