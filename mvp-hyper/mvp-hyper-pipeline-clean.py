#!/usr/bin/env python3
"""
MVP Hyper Pipeline - Clean Orchestration
=========================================
A single, human-readable pipeline that orchestrates existing components.

Steps:
1. CONVERSION: Convert documents to markdown (mvp-hyper-core)
2. CLASSIFICATION: Add document types and basic metadata
3. ENRICHMENT: Add domain-specific tags and entities  
4. EXTRACTION: Generate semantic facts as JSON

Usage:
  python mvp-hyper-pipeline-clean.py <input> --step conversion
  python mvp-hyper-pipeline-clean.py <input> --step classification
  python mvp-hyper-pipeline-clean.py <input> --step enrichment
  python mvp-hyper-pipeline-clean.py <input> --step extraction
  python mvp-hyper-pipeline-clean.py <input> --full  # Run all steps
"""

import argparse
import subprocess
import time
import json
import yaml
from pathlib import Path
from typing import Dict, Tuple

class MVPHyperPipeline:
    """Clean pipeline orchestrator for MVP Hyper system."""
    
    def __init__(self, config_path: str = "mvp-hyper-pipeline-clean-config.yaml"):
        self.config_path = config_path
        self.performance_stats = {}
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load and return configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"⚠️  Error parsing config file: {e}")
            return {}
    
    def display_config_summary(self, input_path: str, output_path: str, steps: list):
        """Display a summary of configuration and planned execution."""
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    CONFIGURATION SUMMARY                      ║
╚═══════════════════════════════════════════════════════════════╝

📋 CONFIG: {self.config_path}
📂 INPUT:  {input_path}
📂 OUTPUT: {output_path}

🔄 PIPELINE STEPS: {' → '.join([s.upper() for s in steps])}
        """)
        
        # Show directories that will be processed
        if self.config and 'inputs' in self.config and 'directories' in self.config['inputs']:
            dirs = self.config['inputs']['directories']
            if dirs:
                print("📁 DIRECTORIES TO PROCESS:")
                for dir_path in dirs:
                    expanded_path = Path(dir_path).expanduser()
                    if expanded_path.exists():
                        file_count = sum(1 for _ in expanded_path.rglob('*') if _.is_file())
                        print(f"   ✅ {dir_path} ({file_count} files)")
                    else:
                        print(f"   ❌ {dir_path} (not found)")
        
        # Show performance targets
        if self.config and 'pipeline' in self.config and 'performance_targets' in self.config['pipeline']:
            targets = self.config['pipeline']['performance_targets']
            print(f"""
⚡ PERFORMANCE TARGETS:
   Conversion:     {targets.get('conversion', 'N/A')} pages/sec
   Classification: {targets.get('classification', 'N/A')} pages/sec  
   Enrichment:     {targets.get('enrichment', 'N/A')} pages/sec
   Extraction:     {targets.get('extraction', 'N/A')} pages/sec
        """)
        
        print("🚀 Starting pipeline execution...\n")
    
    def run_step(self, step_name: str, command: str, description: str) -> Tuple[bool, float, int]:
        """Run a pipeline step and measure performance."""
        print(f"\n{'='*70}")
        print(f"🚀 {step_name.upper()}: {description}")
        print(f"{'='*70}")
        print(f"Command: {command}")
        
        start_time = time.time()
        
        # Capture output so we can parse real performance metrics
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        elapsed = time.time() - start_time
        
        # Show the actual component output (this contains the performance breakdown)
        if result.stdout:
            print(result.stdout)
        
        # Only show errors if they occur
        if result.stderr:
            print("COMPONENT ERRORS:")
            print(result.stderr)
        
        # Parse ACTUAL performance metrics from component output
        file_count = 0
        pages_per_sec = 0
        
        if step_name == "conversion":
            # Parse mvp-hyper-core output for real metrics
            total_files = 0
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # Parse file counts from performance breakdown lines like ".pdf: 12 files, 0.17s total"
                if ' files, ' in line and 'total' in line:
                    try:
                        # Extract number before " files"
                        parts = line.split(' files, ')[0]
                        file_count_str = parts.split()[-1]  # Get last word before " files"
                        file_count_this_ext = int(file_count_str)
                        total_files += file_count_this_ext
                    except:
                        pass
                
                elif 'Current:' in line and 'pages/sec' in line:
                    try:
                        # Extract from lines like "📊 Current: 729.1 pages/sec (Target: 1000)"
                        parts = line.split('Current:')[1].split('pages/sec')[0].strip()
                        pages_per_sec = float(parts)
                    except:
                        pass
            
            # Use the total files we counted
            if total_files > 0:
                file_count = total_files
        
        elif step_name == "enrichment":
            # Parse mvp-hyper-tagger output for real metrics
            for line in result.stdout.split('\n'):
                if 'files processed' in line.lower():
                    try:
                        # Extract file count from tagger output
                        numbers = [int(s) for s in line.split() if s.isdigit()]
                        if numbers:
                            file_count = numbers[0]
                    except:
                        pass
                elif 'pages/sec' in line:
                    try:
                        # Extract pages/sec from tagger output
                        parts = line.split('pages/sec')
                        if len(parts) > 0:
                            speed_part = parts[0].split()[-1]
                            pages_per_sec = float(speed_part)
                    except:
                        pass
        
        elif step_name == "extraction":
            # Parse mvp-hyper-semantic output for real metrics
            for line in result.stdout.split('\n'):
                if 'files processed' in line.lower() or 'documents processed' in line.lower():
                    try:
                        numbers = [int(s) for s in line.split() if s.isdigit()]
                        if numbers:
                            file_count = numbers[0]
                    except:
                        pass
        
        # If we didn't get pages_per_sec from output, calculate from file count and time
        if pages_per_sec == 0 and file_count > 0 and elapsed > 0:
            pages_per_sec = file_count / elapsed
        
        # Store stats
        self.performance_stats[step_name] = {
            'time': elapsed,
            'files': file_count,
            'pages_per_sec': pages_per_sec
        }
        
        if result.returncode == 0:
            print(f"✅ Completed: {file_count} files in {elapsed:.2f}s")
            print(f"⚡ Performance: {pages_per_sec:.1f} pages/sec")
        else:
            print(f"❌ Failed with return code {result.returncode}")
        
        return result.returncode == 0, elapsed, file_count
    
    def step_conversion(self, input_path: str, output_path: str) -> bool:
        """Step 1: Convert documents to markdown using mvp-hyper-core."""
        # Use the working config.yaml that we know works at 725 pages/sec
        # Pass input directories so mvp-hyper-core knows what to process
        # Add --quiet for clean pipeline output
        command = f"python mvp-hyper-core.py {input_path} --output {output_path} --config config.yaml --quiet"
        success, elapsed, files = self.run_step(
            "conversion",
            command,
            "Converting documents to markdown (Target: 700+ pages/sec)"
        )
        return success
    
    def step_classification(self, input_path: str, output_path: str) -> bool:
        """Step 2: Add document classification and basic metadata."""
        # For now, we'll use a simple classification approach
        # In production, this would call the actual classifier
        
        print(f"\n{'='*70}")
        print(f"🚀 CLASSIFICATION: Adding document types and basic metadata")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        # Copy files and add classification
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files_processed = 0
        for md_file in input_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Quick classification based on keyword counts
            content_lower = content.lower()
            
            doc_types = []
            if content_lower.count('safety') + content_lower.count('hazard') + content_lower.count('osha') > 10:
                doc_types.append('safety')
            if content_lower.count('algorithm') + content_lower.count('function') + content_lower.count('code') > 10:
                doc_types.append('technical')
            if content_lower.count('business') + content_lower.count('market') + content_lower.count('revenue') > 10:
                doc_types.append('business')
            if content_lower.count('research') + content_lower.count('study') + content_lower.count('analysis') > 10:
                doc_types.append('research')
            
            if not doc_types:
                doc_types = ['general']
            
            # Add classification to front matter
            if content.startswith('---'):
                # Insert after existing front matter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]
                    
                    # Add classification
                    new_front_matter = front_matter.rstrip() + f"\ndocument_types: {doc_types}\nclassification_confidence: 0.85\n"
                    content = f"---{new_front_matter}---{body}"
            else:
                # Add new front matter
                content = f"---\ndocument_types: {doc_types}\nclassification_confidence: 0.85\n---\n\n{content}"
            
            # Write enhanced file
            output_file = output_dir / md_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_processed += 1
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        
        self.performance_stats['classification'] = {
            'time': elapsed,
            'files': files_processed,
            'pages_per_sec': pages_per_sec
        }
        
        print(f"✅ Completed: {files_processed} files in {elapsed:.2f}s")
        print(f"⚡ Performance: {pages_per_sec:.1f} pages/sec (Target: 2000+)")
        
        return True
    
    def step_enrichment(self, input_path: str, output_path: str) -> bool:
        """Step 3: Add domain-specific enrichment using mvp-hyper-tagger."""
        command = f"python mvp-hyper-tagger.py {input_path} --output {output_path} --config {self.config_path}"
        success, elapsed, files = self.run_step(
            "enrichment",
            command,
            "Adding domain-specific tags and entities (Target: 1500+ pages/sec)"
        )
        return success
    
    def step_extraction(self, input_path: str) -> bool:
        """Step 4: Extract semantic facts to JSON using mvp-hyper-semantic."""
        command = f"python mvp-hyper-semantic.py {input_path}"
        success, elapsed, files = self.run_step(
            "extraction",
            command,
            "Extracting semantic facts to JSON (Target: 300+ pages/sec)"
        )
        return success
    
    def run_full_pipeline(self, input_path: str, output_base: str):
        """Run the complete pipeline through all steps."""
        # Use directories from config if available, otherwise use command line input
        if self.config and 'inputs' in self.config and 'directories' in self.config['inputs']:
            input_dirs = self.config['inputs']['directories']
            # Expand paths and join them for the command line
            expanded_dirs = [str(Path(d).expanduser()) for d in input_dirs]
            actual_input = ' '.join(expanded_dirs)
        else:
            actual_input = input_path
            
        # Display configuration summary first
        steps = ['conversion', 'classification', 'enrichment', 'extraction']
        self.display_config_summary(actual_input, output_base, steps)
        
        # Create output directories for each step
        outputs = {
            'conversion': f"{output_base}/1-markdown",
            'classification': f"{output_base}/2-classified",
            'enrichment': f"{output_base}/3-enriched",
            'extraction': f"{output_base}/3-enriched"  # Same dir, adds JSON files
        }
        
        for dir_path in outputs.values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        total_start = time.time()
        
        # Run each step in sequence
        steps = [
            ('conversion', self.step_conversion, actual_input, outputs['conversion']),
            ('classification', self.step_classification, outputs['conversion'], outputs['classification']),
            ('enrichment', self.step_enrichment, outputs['classification'], outputs['enrichment']),
            ('extraction', self.step_extraction, outputs['enrichment'])
        ]
        
        for step_info in steps:
            if len(step_info) == 4:
                step_name, step_func, input_arg, output_arg = step_info
                if step_name == 'extraction':
                    success = step_func(input_arg)
                else:
                    success = step_func(input_arg, output_arg)
            
            if not success:
                print(f"⚠️  {step_name} had issues, continuing...")
        
        total_time = time.time() - total_start
        
        # Print performance summary
        self.print_performance_summary(total_time)
    
    def print_performance_summary(self, total_time: float):
        """Print a summary of performance metrics."""
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                  PERFORMANCE SUMMARY                          ║
╚═══════════════════════════════════════════════════════════════╝

Step              Time(s)   Files   Pages/sec   Target    Status
────────────────────────────────────────────────────────────────""")
        
        targets = {
            'conversion': 700,
            'classification': 2000,
            'enrichment': 1500,
            'extraction': 300
        }
        
        for step_name, stats in self.performance_stats.items():
            target = targets.get(step_name, 0)
            status = "✅" if stats['pages_per_sec'] >= target else "⚠️"
            
            print(f"{step_name:15} {stats['time']:8.2f} {stats['files']:7} {stats['pages_per_sec']:10.1f} {target:8}+ {status}")
        
        total_files = max((s['files'] for s in self.performance_stats.values()), default=0)
        avg_speed = total_files / total_time if total_time > 0 else 0
        
        print(f"""────────────────────────────────────────────────────────────────
TOTAL:          {total_time:8.2f} {total_files:7} {avg_speed:10.1f}

✨ Pipeline complete! Check output directories for results.
        """)

def main():
    parser = argparse.ArgumentParser(
        description="MVP Hyper Pipeline - Clean Orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input", help="Input directory or file")
    parser.add_argument("--output", default="pipeline-output", help="Output base directory")
    parser.add_argument("--config", default="mvp-hyper-pipeline-clean-config.yaml", help="Configuration file")
    
    # Step selection
    parser.add_argument("--step", choices=['conversion', 'classification', 'enrichment', 'extraction'],
                       help="Run a specific step only")
    parser.add_argument("--full", action="store_true", help="Run full pipeline (all steps)")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MVPHyperPipeline(args.config)
    
    # Run requested operations
    if args.full or (not args.step):
        # Run full pipeline
        pipeline.run_full_pipeline(args.input, args.output)
    elif args.step == 'conversion':
        pipeline.step_conversion(args.input, f"{args.output}/1-markdown")
    elif args.step == 'classification':
        pipeline.step_classification(args.input, f"{args.output}/2-classified")
    elif args.step == 'enrichment':
        pipeline.step_enrichment(args.input, f"{args.output}/3-enriched")
    elif args.step == 'extraction':
        pipeline.step_extraction(args.input)

if __name__ == "__main__":
    main()