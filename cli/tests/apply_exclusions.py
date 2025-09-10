#!/usr/bin/env python3
"""
Apply file exclusions to benchmark script based on problematic files analysis
"""

from pathlib import Path

def update_benchmark_with_exclusions():
    """Add exclusion logic to performance benchmark"""
    
    exclusion_file = Path('/home/corey/projects/docling/cli/tests/files_to_exclude.txt')
    benchmark_file = Path('/home/corey/projects/docling/cli/performance_benchmark.py')
    
    if not exclusion_file.exists():
        print("❌ No exclusion file found - run problematic_files_finder.py first")
        return
        
    if not benchmark_file.exists():
        print("❌ Benchmark file not found")
        return
    
    # Read exclusion list
    with open(exclusion_file, 'r') as f:
        excluded_files = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Found {len(excluded_files)} files to exclude:")
    for filename in excluded_files:
        print(f"   - {filename}")
    
    # Read benchmark script
    with open(benchmark_file, 'r') as f:
        content = f.read()
    
    # Add exclusion logic to get_document_inventory method
    exclusion_code = f'''
        # Exclude problematic files identified by testing
        excluded_filenames = {set(excluded_files)}
        
        def should_exclude_file(file_path):
            \"\"\"Check if file should be excluded from benchmarking\"\"\"
            return file_path.name in excluded_filenames or file_path.suffix.lower() == '.asciidoc'
    '''
    
    # Find the get_document_inventory method and add exclusion logic
    if "should_exclude_file" not in content:
        # Add exclusion function after imports
        import_end = content.find('class DoclingPerformanceBenchmark:')
        if import_end != -1:
            updated_content = content[:import_end] + exclusion_code + "\\n\\n" + content[import_end:]
            
            # Update file filtering in get_document_inventory
            original_filter = "files = list(self.data_dir.glob(f\"**/*.{ext}\"))"
            updated_filter = """files = [f for f in self.data_dir.glob(f"**/*.{ext}") if not should_exclude_file(f)]"""
            
            updated_content = updated_content.replace(original_filter, updated_filter)
            
            # Write updated benchmark
            with open(benchmark_file, 'w') as f:
                f.write(updated_content)
                
            print(f"✅ Updated benchmark script with exclusions")
            print(f"🎯 Excluded files will be skipped during benchmarking")
            print(f"📊 This should eliminate chunk failures from problematic files")
        else:
            print("❌ Could not locate insertion point in benchmark script")
    else:
        print("✅ Benchmark script already has exclusion logic")

if __name__ == "__main__":
    update_benchmark_with_exclusions()