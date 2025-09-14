#!/usr/bin/env python3
"""
Run the complete MVP Hyper Pipeline using EXISTING WORKING components
=====================================================================
This orchestrates the existing sidecars that already work at high performance.
"""

import os
import sys
import time
from pathlib import Path
import subprocess

def run_command(cmd, description):
    """Run a command and measure performance."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ Completed in {elapsed:.2f}s")
    else:
        print(f"❌ Failed with return code {result.returncode}")
    
    return result.returncode == 0, elapsed

def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python run-full-pipeline.py <input_dir> [output_base]")
        print("Example: python run-full-pipeline.py ~/projects/docling/cli/data output")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_base = sys.argv[2] if len(sys.argv) > 2 else "pipeline-output"
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║          MVP HYPER PIPELINE - FULL ORCHESTRATION             ║
╚═══════════════════════════════════════════════════════════════╝

📂 Input: {input_dir}
📂 Output: {output_base}/
    """)
    
    # Create output directories
    tier0_output = f"{output_base}/tier0-markdown"
    tier1_output = f"{output_base}/tier1-classified"
    tier2_output = f"{output_base}/tier2-tagged"
    tier3_output = f"{output_base}/tier3-semantic"
    
    for dir in [tier0_output, tier1_output, tier2_output, tier3_output]:
        Path(dir).mkdir(parents=True, exist_ok=True)
    
    total_start = time.time()
    
    # =====================================
    # TIER 0: Convert to Markdown (Baseline)
    # =====================================
    success, t0_time = run_command(
        f"python mvp-hyper-core.py {input_dir} --output {tier0_output} --config config.yaml",
        "TIER 0: Converting documents to markdown (target: 700+ pages/sec)"
    )
    
    if not success:
        print("❌ Tier 0 failed. Exiting.")
        return
    
    # Count files created
    md_files = list(Path(tier0_output).glob("*.md"))
    print(f"📊 Created {len(md_files)} markdown files")
    
    # =====================================
    # TIER 1: Document Classification
    # =====================================
    # For now, use the pipeline for classification only
    success, t1_time = run_command(
        f"python mvp-hyper-pipeline.py {tier0_output} --output {tier1_output} --tier1-only --config mvp-hyper-config.yaml",
        "TIER 1: Adding document classification (target: 2000+ pages/sec)"
    )
    
    if not success:
        print("⚠️  Tier 1 had issues, continuing anyway...")
    
    # =====================================
    # TIER 2: Enhanced Tagging
    # =====================================
    # Use the EXISTING mvp-hyper-core with tagging enabled
    success, t2_time = run_command(
        f"python mvp-hyper-core.py {tier1_output} --output {tier2_output} --enable-tagging --config config.yaml",
        "TIER 2: Adding domain-specific tags (target: 1500+ pages/sec)"
    )
    
    if not success:
        print("⚠️  Tier 2 had issues, continuing anyway...")
    
    # =====================================
    # TIER 3: Semantic Extraction
    # =====================================
    # Use the EXISTING mvp-hyper-semantic.py
    success, t3_time = run_command(
        f"python mvp-hyper-semantic.py {tier2_output}",
        "TIER 3: Extracting semantic facts to JSON (target: 300+ pages/sec)"
    )
    
    if not success:
        print("⚠️  Tier 3 had issues")
    
    # =====================================
    # FINAL SUMMARY
    # =====================================
    total_time = time.time() - total_start
    
    # Count final outputs
    final_md_files = list(Path(tier2_output).glob("*.md"))
    json_files = list(Path(tier2_output).glob("*.metadata.json"))
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                     PIPELINE COMPLETE                         ║
╚═══════════════════════════════════════════════════════════════╝

📊 RESULTS:
   Markdown files:     {len(final_md_files)}
   JSON fact files:    {len(json_files)}
   
⏱️  PERFORMANCE:
   Tier 0 (Convert):   {t0_time:.2f}s
   Tier 1 (Classify):  {t1_time:.2f}s  
   Tier 2 (Tag):       {t2_time:.2f}s
   Tier 3 (Extract):   {t3_time:.2f}s
   ─────────────────────────────
   TOTAL:              {total_time:.2f}s
   
   Average speed:      {len(md_files) / total_time:.1f} files/sec
   
📁 OUTPUT LOCATIONS:
   Tier 0: {tier0_output}/
   Tier 1: {tier1_output}/
   Tier 2: {tier2_output}/
   Tier 3: {tier2_output}/*.metadata.json
    """)
    
    # Show sample of a tagged file
    if final_md_files:
        sample_file = final_md_files[0]
        print(f"\n📄 SAMPLE OUTPUT ({sample_file.name}):")
        print("─" * 60)
        with open(sample_file, 'r') as f:
            lines = f.readlines()[:30]
            for line in lines:
                print(line.rstrip())
        print("─" * 60)
    
    # Show sample JSON if exists
    if json_files:
        sample_json = json_files[0]
        print(f"\n📊 SAMPLE JSON ({sample_json.name}):")
        print("─" * 60)
        with open(sample_json, 'r') as f:
            lines = f.readlines()[:20]
            for line in lines:
                print(line.rstrip())
        print("─" * 60)

if __name__ == "__main__":
    main()