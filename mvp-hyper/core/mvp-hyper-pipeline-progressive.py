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
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to .config directory within core
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, ".config", "mvp-hyper-pipeline-clean-config.yaml")
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
        print(f"\n🔸 {step_name.upper()}: {description}")
        
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
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, ".config", "config.yaml")
        core_path = os.path.join(current_dir, "mvp-hyper-core.py")
        command = f"python {core_path} {input_path} --output {output_path} --config {config_path} --quiet"
        success, elapsed, files = self.run_step(
            "conversion",
            command,
            "Converting documents to markdown (Target: 700+ pages/sec)"
        )
        return success
    
    def step_classification(self, input_path: str, output_path: str) -> bool:
        """Step 2: Add document classification and basic metadata (in-place enhancement)."""
        
        print(f"\n🔸 CLASSIFICATION: Adding document types")
        
        start_time = time.time()
        
        # Work with markdown directory - enhance files in place
        markdown_dir = Path(input_path)
        
        files_processed = 0
        for md_file in markdown_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Quick classification based on keyword counts
            content_lower = content.lower()
            
            doc_types = []
            confidence_scores = {}
            
            # Calculate domain scores
            safety_score = (content_lower.count('safety') + content_lower.count('hazard') + 
                          content_lower.count('osha') + content_lower.count('ppe'))
            tech_score = (content_lower.count('algorithm') + content_lower.count('function') + 
                         content_lower.count('code') + content_lower.count('api'))
            business_score = (content_lower.count('business') + content_lower.count('market') + 
                            content_lower.count('revenue') + content_lower.count('strategy'))
            research_score = (content_lower.count('research') + content_lower.count('study') + 
                            content_lower.count('analysis') + content_lower.count('hypothesis'))
            
            # Determine document types based on scores
            if safety_score > 10:
                doc_types.append('safety')
                confidence_scores['safety'] = min(safety_score / 50, 1.0)
            if tech_score > 10:
                doc_types.append('technical')
                confidence_scores['technical'] = min(tech_score / 50, 1.0)
            if business_score > 10:
                doc_types.append('business')
                confidence_scores['business'] = min(business_score / 50, 1.0)
            if research_score > 10:
                doc_types.append('research')
                confidence_scores['research'] = min(research_score / 50, 1.0)
            
            if not doc_types:
                doc_types = ['general']
                confidence_scores['general'] = 0.5
            
            # Calculate all domain scores for percentage breakdown
            all_domain_scores = {
                'safety': safety_score,
                'technical': tech_score, 
                'business': business_score,
                'research': research_score
            }
            
            # Convert to percentages
            total_score = sum(all_domain_scores.values()) or 1  # Avoid division by zero
            domain_percentages = {domain: (score / total_score) * 100 
                                for domain, score in all_domain_scores.items()}
            
            # Get top three domains by percentage
            top_three_domains = sorted(domain_percentages.items(), key=lambda x: x[1], reverse=True)[:3]
            top_three_formatted = {domain: f"{percentage:.1f}%" for domain, percentage in top_three_domains if percentage > 0}
            
            # Determine primary domain
            primary_domain = max(confidence_scores.items(), key=lambda x: x[1])[0] if confidence_scores else 'general'
            
            # Add classification to front matter (in-place)
            if content.startswith('---'):
                # Insert after existing front matter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]
                    
                    # Add classification metadata with domain breakdown
                    classification_data = f"\n# Classification (Step 2)\ndocument_types: {doc_types}\nprimary_domain: {primary_domain}\nclassification_confidence: {max(confidence_scores.values()) if confidence_scores else 0.5:.2f}\ndomain_percentages: {dict(top_three_formatted)}\n"
                    new_front_matter = front_matter.rstrip() + classification_data
                    content = f"---{new_front_matter}---{body}"
            else:
                # Add new front matter with domain breakdown
                classification_data = f"# Classification (Step 2)\ndocument_types: {doc_types}\nprimary_domain: {primary_domain}\nclassification_confidence: {max(confidence_scores.values()) if confidence_scores else 0.5:.2f}\ndomain_percentages: {dict(top_three_formatted)}\n"
                content = f"---\n{classification_data}---\n\n{content}"
            
            # Write enhanced file back to same location
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_processed += 1
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        
        self.performance_stats['classification'] = {
            'time': elapsed,
            'files': files_processed,
            'pages_per_sec': pages_per_sec
        }
        
        print(f"✅ Classification: {files_processed} files, {pages_per_sec:.1f} pages/sec (Target: 2000+)")
        
        return True
    
    def step_enrichment(self, input_path: str, output_path: str) -> bool:
        """Step 3: Add domain-specific enrichment (in-place enhancement)."""
        
        print(f"\n🔸 ENRICHMENT: Adding domain-specific tags")
        
        start_time = time.time()
        
        # Work with same markdown directory - enhance files in place
        markdown_dir = Path(input_path)
        
        files_processed = 0
        for md_file in markdown_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse existing front matter to get classification
            primary_domain = 'general'
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    # Extract primary domain if present
                    for line in front_matter.split('\n'):
                        if 'primary_domain:' in line:
                            primary_domain = line.split(':', 1)[1].strip()
                            break
            
            content_lower = content.lower()
            
            # Domain-specific entity extraction
            entities = {
                'organizations': [],
                'persons': [],
                'regulations': [],
                'technologies': []
            }
            
            # Extract organizations (simple pattern matching for speed)
            org_patterns = ['osha', 'niosh', 'epa', 'fda', 'cdc', 'who']
            for org in org_patterns:
                if org in content_lower:
                    entities['organizations'].append(org.upper())
            
            # Extract regulations (CFR patterns)
            import re
            cfr_pattern = r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?'
            cfr_matches = re.findall(cfr_pattern, content, re.IGNORECASE)
            entities['regulations'].extend(list(set(cfr_matches)))
            
            # Domain-specific tags based on primary domain
            domain_tags = {}
            
            if primary_domain == 'safety':
                # Safety-specific tags
                hazard_keywords = ['fall', 'electrical', 'chemical', 'fire', 'ergonomic']
                ppe_keywords = ['helmet', 'gloves', 'goggles', 'harness', 'respirator']
                
                hazards = [h for h in hazard_keywords if h in content_lower]
                ppe = [p for p in ppe_keywords if p in content_lower]
                
                if hazards:
                    domain_tags['hazard_types'] = hazards
                if ppe:
                    domain_tags['ppe_required'] = ppe
                    
            elif primary_domain == 'technical':
                # Technical-specific tags
                tech_keywords = ['api', 'database', 'algorithm', 'framework', 'protocol']
                lang_keywords = ['python', 'java', 'javascript', 'sql', 'rust']
                
                technologies = [t for t in tech_keywords if t in content_lower]
                languages = [l for l in lang_keywords if l in content_lower]
                
                if technologies:
                    domain_tags['technologies'] = technologies
                if languages:
                    domain_tags['programming_languages'] = languages
            
            elif primary_domain == 'business':
                # Business-specific tags
                business_keywords = ['revenue', 'profit', 'market', 'strategy', 'customer']
                metrics = [b for b in business_keywords if b in content_lower]
                
                if metrics:
                    domain_tags['business_metrics'] = metrics
            
            # Add enrichment to front matter (in-place)
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]
                    
                    # Add enrichment metadata
                    enrichment_data = f"\n# Enrichment (Step 3)\n"
                    if entities['organizations']:
                        enrichment_data += f"organizations: {entities['organizations']}\n"
                    if entities['regulations']:
                        enrichment_data += f"regulations: {entities['regulations']}\n"
                    if domain_tags:
                        enrichment_data += f"domain_tags:\n"
                        for tag_type, tags in domain_tags.items():
                            enrichment_data += f"  {tag_type}: {tags}\n"
                    
                    new_front_matter = front_matter.rstrip() + enrichment_data
                    content = f"---{new_front_matter}---{body}"
            
            # Write enhanced file back to same location
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_processed += 1
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        
        self.performance_stats['enrichment'] = {
            'time': elapsed,
            'files': files_processed,
            'pages_per_sec': pages_per_sec
        }
        
        print(f"✅ Enrichment: {files_processed} files, {pages_per_sec:.1f} pages/sec (Target: 1500+)")
        
        return True
    
    def step_extraction(self, input_path: str, output_path: str) -> bool:
        """Step 4: Extract semantic facts using enhanced context (creates .semantic.json files)."""
        
        print(f"\n🔸 EXTRACTION: Generating semantic facts")
        
        start_time = time.time()
        
        # Work in same directory - semantic files alongside markdown
        working_dir = Path(input_path)
        
        files_processed = 0
        total_facts = 0
        
        for md_file in working_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the enhanced front matter
            metadata = {}
            doc_body = content
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    doc_body = parts[2]
                    
                    # Parse metadata for context
                    for line in front_matter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            
            # Use classification and enrichment for better extraction
            primary_domain = metadata.get('primary_domain', 'general')
            doc_types = eval(metadata.get('document_types', "['general']"))
            
            # Extract facts based on domain context
            facts = []
            
            # Domain-specific fact extraction patterns
            import re
            
            if 'safety' in primary_domain or 'safety' in doc_types:
                # Safety-specific facts
                requirement_pattern = r'(?:shall|must|required to)\s+([^.]{20,100})'
                requirements = re.findall(requirement_pattern, doc_body, re.IGNORECASE)
                for req in requirements[:10]:  # Limit for performance
                    facts.append({
                        'type': 'safety_requirement',
                        'fact': req.strip(),
                        'confidence': 0.85,
                        'domain': 'safety'
                    })
            
            if 'technical' in primary_domain or 'technical' in doc_types:
                # Technical facts
                definition_pattern = r'([A-Z][\w\s]+)\s+(?:is|are|means|refers to)\s+([^.]{20,100})'
                definitions = re.findall(definition_pattern, doc_body)
                for term, definition in definitions[:10]:
                    facts.append({
                        'type': 'technical_definition',
                        'term': term.strip(),
                        'definition': definition.strip(),
                        'confidence': 0.80,
                        'domain': 'technical'
                    })
            
            # Generic fact patterns
            stat_pattern = r'(\d+(?:\.\d+)?%?)\s+(?:of|increase|decrease|growth)'
            stats = re.findall(stat_pattern, doc_body)
            for stat in stats[:5]:
                facts.append({
                    'type': 'statistic',
                    'value': stat,
                    'confidence': 0.75,
                    'domain': primary_domain
                })
            
            # Create semantic output
            semantic_output = {
                'source_file': md_file.name,
                'extraction_context': {
                    'classification': {
                        'primary_domain': primary_domain,
                        'document_types': doc_types,
                        'confidence': float(metadata.get('classification_confidence', 0.5))
                    },
                    'enrichment': {
                        'organizations': eval(metadata.get('organizations', '[]')),
                        'regulations': eval(metadata.get('regulations', '[]'))
                    }
                },
                'facts': facts,
                'fact_count': len(facts),
                'extraction_timestamp': time.time()
            }
            
            # Write semantic file in same directory as markdown
            semantic_file = working_dir / f"{md_file.stem}.semantic.json"
            import json
            with open(semantic_file, 'w', encoding='utf-8') as f:
                json.dump(semantic_output, f, indent=2)
            
            files_processed += 1
            total_facts += len(facts)
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        
        self.performance_stats['extraction'] = {
            'time': elapsed,
            'files': files_processed,
            'pages_per_sec': pages_per_sec,
            'total_facts': total_facts
        }
        
        print(f"✅ Extraction: {files_processed} files → {total_facts} facts, {pages_per_sec:.1f} pages/sec (Target: 300+)")
        
        return True
    
    def run_full_pipeline(self, input_path: str, output_base: str):
        """Run the complete progressive enhancement pipeline."""
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
        
        # Single unified output directory for all files
        output_dir = output_base
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        total_start = time.time()
        
        # Run each step in sequence (all in same directory)
        steps = [
            ('conversion', self.step_conversion, actual_input, output_dir),
            ('classification', self.step_classification, output_dir, output_dir),  # In-place
            ('enrichment', self.step_enrichment, output_dir, output_dir),  # In-place
            ('extraction', self.step_extraction, output_dir, output_dir)  # Same directory
        ]
        
        for step_info in steps:
            if len(step_info) == 4:
                step_name, step_func, input_arg, output_arg = step_info
                success = step_func(input_arg, output_arg)
            
            if not success:
                print(f"⚠️  {step_name} had issues, continuing...")
        
        total_time = time.time() - total_start
        
        # Print performance summary
        self.print_performance_summary(total_time)
        
        # Show final output location
        print(f"\n📁 All output files: {output_dir}")
        print(f"   • {len(list(Path(output_dir).glob('*.md')))} markdown files")
        print(f"   • {len(list(Path(output_dir).glob('*.semantic.json')))} semantic JSON files")
    
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
        description="MVP Hyper Pipeline - Progressive Enhancement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Progressive Enhancement Pipeline:
  Step 1: Conversion     - PDFs → Markdown files in 'markdown/' directory
  Step 2: Classification - Enhance markdown files in-place with document types
  Step 3: Enrichment     - Enhance markdown files in-place with domain tags
  Step 4: Extraction     - Generate semantic JSON files in 'semantic/' directory

Examples:
  # Full pipeline
  python mvp-hyper-pipeline-progressive.py input/ --output output/
  
  # Individual steps (working with markdown directory)
  python mvp-hyper-pipeline-progressive.py input/ --output output/ --step conversion
  python mvp-hyper-pipeline-progressive.py output/markdown --step classification
  python mvp-hyper-pipeline-progressive.py output/markdown --step enrichment
  python mvp-hyper-pipeline-progressive.py output/markdown --output output/ --step extraction
        """
    )
    
    parser.add_argument("input", nargs='?', help="Input directory (PDFs for conversion, markdown for other steps)")
    parser.add_argument("--output", default="output", help="Output base directory")
    parser.add_argument("--config", default="mvp-hyper-pipeline-progressive-config.yaml", help="Configuration file")
    
    # Step selection
    parser.add_argument("--step", choices=['conversion', 'classification', 'enrichment', 'extraction'],
                       help="Run a specific step only")
    parser.add_argument("--full", action="store_true", help="Run full progressive pipeline (all steps)")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MVPHyperPipeline(args.config)
    
    # Handle default input directory for operations
    if args.input is None:
        if args.step in ['classification', 'enrichment', 'extraction']:
            # For in-place operations, work on output directory
            args.input = args.output
        elif args.step == 'conversion' or args.full or (not args.step):
            # For conversion or full pipeline, use directories from config
            if pipeline.config and 'inputs' in pipeline.config and 'directories' in pipeline.config['inputs']:
                input_dirs = pipeline.config['inputs']['directories']
                if input_dirs:
                    # Join multiple directories for command line
                    expanded_dirs = [str(Path(d).expanduser()) for d in input_dirs]
                    args.input = ' '.join(expanded_dirs)
                    print(f"Using input directories from config: {', '.join(input_dirs)}")
                else:
                    print("Error: No input directories found in configuration file")
                    return
            else:
                print("Error: No input directories configuration found")
                return
    
    # Run requested operations
    if args.full or (not args.step):
        # Run full progressive pipeline
        pipeline.run_full_pipeline(args.input, args.output)
    elif args.step == 'conversion':
        # Convert PDFs to unified output directory
        pipeline.step_conversion(args.input, args.output)
    elif args.step == 'classification':
        # Enhance markdown files in-place
        pipeline.step_classification(args.input, args.input)  # Same dir for in-place
    elif args.step == 'enrichment':
        # Enhance markdown files in-place
        pipeline.step_enrichment(args.input, args.input)  # Same dir for in-place
    elif args.step == 'extraction':
        # Extract to same directory as markdown files
        pipeline.step_extraction(args.input, args.input)

if __name__ == "__main__":
    main()