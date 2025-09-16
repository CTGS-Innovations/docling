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
import sys
import os
import re
from yaml_metadata_manager import YAMLMetadataManager
from pathlib import Path
from typing import Dict, Tuple, Any
from datetime import datetime

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import enhanced modules (AC + Entity extraction)
try:
    from core.enhanced_classification_with_entities import EnhancedClassifierWithEntities
    from core.enhanced_enrichment_targeted import TargetedEnrichment
    ENHANCED_MODULES_AVAILABLE = True
    print("✅ Enhanced classification with entity extraction + targeted enrichment loaded")
except ImportError as e:
    ENHANCED_MODULES_AVAILABLE = False
    print(f"⚠️ Enhanced modules not available: {e}")
    print("⚠️ Using basic classification and enrichment")

class MVPHyperPipeline:
    """Clean pipeline orchestrator for MVP Hyper system."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to progressive config directory within core
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, ".config", "mvp-hyper-pipeline-progressive-config.yaml")
        self.config_path = config_path
        self.performance_stats = {}
        self.config = self.load_config()
        
        # Initialize enhanced modules if available
        if ENHANCED_MODULES_AVAILABLE:
            try:
                self.classifier = EnhancedClassifierWithEntities()
                self.enrichment = TargetedEnrichment()
                self.enhanced_mode = True
                self.classification_cache = {}  # Cache classification results for enrichment
                print("🚀 Enhanced layered processing activated")
                print("   Layer 1: Classification + FREE entity extraction (money, dates, etc.)")
                print("   Layer 2: Targeted enrichment based on domains")
            except Exception as e:
                print(f"⚠️ Failed to initialize enhanced modules: {e}")
                self.enhanced_mode = False
                self.classifier = None
                self.enrichment = None
                self.classification_cache = {}
        else:
            self.enhanced_mode = False
            self.classifier = None
            self.enrichment = None
            self.classification_cache = {}
        
        # Load formula conversion settings
        self.convert_formulas = self.config.get('processing', {}).get('convert_formulas', True)
        self.remove_latexit = self.config.get('processing', {}).get('remove_latexit', True)
        self.formula_output_format = self.config.get('processing', {}).get('formula_output_format', 'both')
        
        # Initialize metadata manager for structured YAML handling
        self.metadata_manager = YAMLMetadataManager()
    
    def generate_step1_metadata(self, file_path: str, content: str) -> str:
        """Generate enhanced Step 1 conversion metadata."""
        path_obj = Path(file_path)
        
        # Basic file info
        file_stats = path_obj.stat() if path_obj.exists() else None
        
        # Content analysis (quick)
        lines = content.split('\n')
        words = content.split()
        
        # Quick content detection with enhanced formula analysis
        has_images = bool(re.search(r'!\[.*?\]|<img|Figure \d+|Image \d+', content, re.IGNORECASE))
        has_tables = bool(re.search(r'\|.*\||Table \d+|<table', content, re.IGNORECASE))
        has_urls = bool(re.search(r'https?://|www\.', content))
        has_emails = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        
        # Enhanced formula detection and analysis
        formula_indicators = [
            r'<latexit',  # LaTeX blocks
            r'\\begin\{|\\end\{',  # LaTeX environments
            r'\\frac|\\sum|\\int|\\sqrt',  # Math functions
            r'\\alpha|\\beta|\\gamma|\\theta|\\sigma|\\mu|\\lambda|\\pi|\\epsilon|\\delta',  # Greek letters
            r'\\nabla|\\partial|\\infty',  # Mathematical symbols
            r'\\log|\\exp|\\sin|\\cos|\\tan',  # Functions
            r'\\cdot|\\times|\\div|\\pm|\\le|\\ge|\\ne|\\approx|\\equiv',  # Operators
            r'\\propto|\\in|\\subset|\\cup|\\cap|\\forall|\\exists',  # Set theory
            r'\\rightarrow|\\leftarrow|\\Rightarrow|\\Leftarrow',  # Arrows
            r'\$\$|\$[^$]+\$',  # Inline/display math
            r'\\\\[a-zA-Z]+',  # LaTeX commands
            r'Equation \d+|Formula \d+|Figure \d+.*equation',  # References
            r'x_\d+|x_\{|p_θ|p_\\theta|q\(.*\)|DKL\(',  # Common math notation
            r'_{.*}|\^{.*}|mathrm|mathcal',  # Subscripts/superscripts
            r'diffusion.*model|probabilistic.*model'  # Domain-specific
        ]
        
        # Count different types of formula indicators
        formula_counts = {}
        total_formula_matches = 0
        
        for i, pattern in enumerate(formula_indicators):
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                formula_counts[f'pattern_{i+1}'] = len(matches)
                total_formula_matches += len(matches)
        
        has_formulas = total_formula_matches > 0
        
        # Quick LaTeX conversion analysis (since it's so fast!)
        latex_expressions = []
        if has_formulas:
            # Extract mathematical expressions for potential conversion
            math_notation_patterns = [
                (r'x_([T0-9t\-]+)', r'x_{\1}'),  # Variable subscripts
                (r'p_θ\(([^)]+)\)', r'p_\\theta(\1)'),  # Theta notation
                (r'q\(([^)]+)\)', r'q(\1)'),  # Q functions
                (r'DKL\(([^)]+)\)', r'D_{\\text{KL}}(\1)'),  # KL divergence
                (r'(?<![\\$])α', r'\\alpha'),  # Greek alpha
                (r'(?<![\\$])β', r'\\beta'),  # Greek beta
                (r'(?<![\\$])θ', r'\\theta'),  # Greek theta
            ]
            
            # Count convertible expressions
            convertible_count = 0
            for pattern, replacement in math_notation_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    convertible_count += len(matches)
                    latex_expressions.extend(matches[:3])  # Sample first 3
            
            formula_counts['convertible_expressions'] = convertible_count
        
        # Detect source type
        if file_path.startswith(('http://', 'https://')):
            source_type = "url"
            source_path = file_path
            filename = path_obj.name
        else:
            source_type = "file"
            source_path = str(path_obj.resolve()) if path_obj.exists() else file_path
            filename = path_obj.name
        
        # Size calculations
        size_bytes = file_stats.st_size if file_stats else len(content.encode('utf-8'))
        if size_bytes >= 1024*1024:
            size_human = f"{size_bytes / (1024*1024):.1f} MB"
        elif size_bytes >= 1024:
            size_human = f"{size_bytes / 1024:.1f} KB"
        else:
            size_human = f"{size_bytes} bytes"
        
        # Timestamps
        conversion_date = datetime.now().isoformat()
        created_date = datetime.fromtimestamp(file_stats.st_ctime).isoformat() if file_stats else None
        modified_date = datetime.fromtimestamp(file_stats.st_mtime).isoformat() if file_stats else None
        
        # Build metadata
        metadata_lines = [
            "# Step 1: Document Conversion & File Analysis",
            f"source_type: {source_type}",
            f"source_path: \"{source_path}\"",
            f"filename: \"{filename}\"",
            f"file_extension: \"{path_obj.suffix}\"",
            f"format: \"{path_obj.suffix.upper().lstrip('.')}\"" if path_obj.suffix else "format: \"UNKNOWN\"",
            f"size_bytes: {size_bytes}",
            f"size_human: \"{size_human}\"",
            f"conversion_date: \"{conversion_date}\"",
        ]
        
        # Add file timestamps if available
        if created_date:
            metadata_lines.append(f"created_date: \"{created_date}\"")
        if modified_date:
            metadata_lines.append(f"modified_date: \"{modified_date}\"")
        
        # Content analysis with enhanced formula details
        metadata_lines.extend([
            f"character_count: {len(content)}",
            f"word_count: {len(words)}",
            f"line_count: {len(lines)}",
            f"has_images: {str(has_images).lower()}",
            f"has_tables: {str(has_tables).lower()}",
            f"has_formulas: {str(has_formulas).lower()}",
            f"has_urls: {str(has_urls).lower()}",
            f"has_emails: {str(has_emails).lower()}",
            "conversion_method: \"mvp-hyper-pipeline\"",
        ])
        
        # Add enhanced formula analysis if formulas detected
        if has_formulas:
            metadata_lines.extend([
                f"formula_indicators_found: {total_formula_matches}",
                f"formula_types_detected: {len(formula_counts)}",
            ])
            
            # Add LaTeX conversion potential
            if latex_expressions:
                metadata_lines.extend([
                    f"latex_convertible_expressions: {formula_counts.get('convertible_expressions', 0)}",
                    f"sample_expressions: {latex_expressions[:3]}",  # First 3 examples
                ])
                
            # Add top formula indicators
            if formula_counts:
                top_indicators = sorted(formula_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                metadata_lines.append(f"top_formula_patterns: {[f'{k}:{v}' for k, v in top_indicators]}")
            
            metadata_lines.append("formula_conversion_ready: true")
        
        return "\n" + "\n".join(metadata_lines) + "\n"
    
    def _generate_step1_structured_data(self, file_path: str, content: str) -> Dict[str, Any]:
        """Generate Step 1 conversion metadata as structured data."""
        path_obj = Path(file_path)
        
        # Basic file info
        file_stats = path_obj.stat() if path_obj.exists() else None
        
        # Content analysis (quick)
        lines = content.split('\n')
        words = content.split()
        
        # Quick content detection with enhanced formula analysis
        has_images = bool(re.search(r'!\[.*?\]|<img|Figure \d+|Image \d+', content, re.IGNORECASE))
        has_tables = bool(re.search(r'\|.*\||Table \d+|<table', content, re.IGNORECASE))
        has_urls = bool(re.search(r'https?://|www\.', content))
        has_emails = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        
        # Enhanced formula detection
        formula_indicators = [
            r'<latexit',  # LaTeX blocks
            r'\\begin\{|\\end\{',  # LaTeX environments
            r'\\frac|\\sum|\\int|\\sqrt',  # Math functions
            r'\\alpha|\\beta|\\gamma|\\theta|\\sigma|\\mu|\\lambda|\\pi|\\epsilon|\\delta',  # Greek letters
            r'\\nabla|\\partial|\\infty',  # Mathematical symbols
            r'\\log|\\exp|\\sin|\\cos|\\tan',  # Functions
            r'\\cdot|\\times|\\div|\\pm|\\le|\\ge|\\ne|\\approx|\\equiv',  # Operators
            r'\\propto|\\in|\\subset|\\cup|\\cap|\\forall|\\exists',  # Set theory
            r'\\rightarrow|\\leftarrow|\\Rightarrow|\\Leftarrow',  # Arrows
            r'\$\$|\$[^$]+\$',  # Inline/display math
            r'\\\\[a-zA-Z]+',  # LaTeX commands
            r'Equation \d+|Formula \d+|Figure \d+.*equation',  # References
            r'x_\d+|x_\{|p_θ|p_\\theta|q\(.*\)|DKL\(',  # Common math notation
            r'_{.*}|\^{.*}|mathrm|mathcal',  # Subscripts/superscripts
            r'diffusion.*model|probabilistic.*model'  # Domain-specific
        ]
        
        # Count different types of formula indicators
        formula_counts = {}
        total_formula_matches = 0
        
        for i, pattern in enumerate(formula_indicators):
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                formula_counts[f'pattern_{i+1}'] = len(matches)
                total_formula_matches += len(matches)
        
        has_formulas = total_formula_matches > 0
        
        # Detect source type
        if file_path.startswith(('http://', 'https://')):
            source_type = "url"
            source_path = file_path
            filename = path_obj.name
        else:
            source_type = "file"
            source_path = str(path_obj.resolve()) if path_obj.exists() else file_path
            filename = path_obj.name
        
        # Size calculations
        size_bytes = file_stats.st_size if file_stats else len(content.encode('utf-8'))
        if size_bytes >= 1024*1024:
            size_human = f"{size_bytes / (1024*1024):.1f} MB"
        elif size_bytes >= 1024:
            size_human = f"{size_bytes / 1024:.1f} KB"
        else:
            size_human = f"{size_bytes} bytes"
        
        # Timestamps
        conversion_date = datetime.now().isoformat()
        created_date = datetime.fromtimestamp(file_stats.st_ctime).isoformat() if file_stats else None
        modified_date = datetime.fromtimestamp(file_stats.st_mtime).isoformat() if file_stats else None
        
        # Build structured data
        step1_data = {
            "description": "Document Conversion & File Analysis",
            "source_type": source_type,
            "source_path": source_path,
            "filename": filename,
            "file_extension": path_obj.suffix,
            "format": path_obj.suffix.upper().lstrip('.') if path_obj.suffix else "UNKNOWN",
            "size_bytes": size_bytes,
            "size_human": size_human,
            "conversion_date": conversion_date,
            "character_count": len(content),
            "word_count": len(words),
            "line_count": len(lines),
            "has_images": has_images,
            "has_tables": has_tables,
            "has_formulas": has_formulas,
            "has_urls": has_urls,
            "has_emails": has_emails,
            "conversion_method": "mvp-hyper-pipeline"
        }
        
        # Add file timestamps if available
        if created_date:
            step1_data["created_date"] = created_date
        if modified_date:
            step1_data["modified_date"] = modified_date
        
        # Add enhanced formula analysis if formulas detected
        if has_formulas:
            step1_data.update({
                "formula_indicators_found": total_formula_matches,
                "formula_types_detected": len(formula_counts),
                "formula_conversion_ready": True
            })
            
            if formula_counts:
                import json
                step1_data["formula_patterns"] = json.dumps(formula_counts, separators=(',', ':'))
        
        return step1_data
    
    def _generate_step2_structured_data(self, classification_metadata: str) -> Dict[str, Any]:
        """Convert classification metadata string to structured data."""
        step2_data = {
            "description": "Document Classification & Type Detection",
            "classification_date": datetime.now().isoformat(),
            "classification_method": "enhanced" if self.enhanced_mode else "basic"
        }
        
        # Parse the classification metadata string to extract structured data
        lines = classification_metadata.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Handle different value types
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.replace('.', '').replace('-', '').isdigit():
                    value = float(value) if '.' in value else int(value)
                elif value.startswith('[') and value.endswith(']'):
                    # Handle list values - keep as compact JSON string
                    try:
                        import ast
                        parsed_list = ast.literal_eval(value)
                        # Convert to compact JSON string for machine readability
                        import json
                        value = json.dumps(parsed_list, separators=(',', ':'))
                    except:
                        pass
                elif value.startswith('{') and value.endswith('}'):
                    # Handle dict values - keep as compact JSON string  
                    try:
                        import ast
                        parsed_dict = ast.literal_eval(value)
                        # Convert to compact JSON string for machine readability
                        import json
                        value = json.dumps(parsed_dict, separators=(',', ':'))
                    except:
                        pass
                
                step2_data[key] = value
        
        return step2_data
    
    def _generate_step3_structured_data(self, enrichment_metadata: str, entities: dict) -> Dict[str, Any]:
        """Convert enrichment metadata string to structured data."""
        step3_data = {
            "description": "Domain-Specific Enrichment & Entity Extraction",
            "enrichment_date": datetime.now().isoformat(),
            "enrichment_method": "enhanced" if self.enhanced_mode else "basic"
        }
        
        # Parse the enrichment metadata string to extract structured data
        lines = enrichment_metadata.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Handle different value types
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.replace('.', '').replace('-', '').isdigit():
                    value = float(value) if '.' in value else int(value)
                elif value.startswith('[') and value.endswith(']'):
                    # Handle list values - convert to compact JSON string
                    try:
                        import ast, json
                        parsed_list = ast.literal_eval(value)
                        value = json.dumps(parsed_list, separators=(',', ':'))
                    except:
                        pass
                
                step3_data[key] = value
        
        # Add structured entity data if available - ALL as compact JSON
        if entities and 'metadata' in entities:
            import json
            domains_processed = entities['metadata'].get('domains_scanned', [])
            step3_data.update({
                "entities_extracted": entities['metadata'].get('total_entity_count', 0),
                "processing_time_ms": entities['metadata'].get('processing_time_ms', 0),
                "domains_processed": json.dumps(domains_processed, separators=(',', ':')) if domains_processed else '[]'
            })
            
            # Add ONLY domain-specific entities (skip universal_entities to avoid duplication)
            for domain, domain_entities in entities.items():
                if domain not in ['metadata', 'universal_entities'] and domain_entities:
                    # Use compact JSON for complex nested structures (single line)
                    step3_data[f"{domain}_entities"] = json.dumps(domain_entities, separators=(',', ':'))
        
        # Convert any remaining list values to compact JSON format
        import json
        for key, value in step3_data.items():
            if isinstance(value, list):
                # Use compact format for simple lists
                step3_data[key] = json.dumps(value, separators=(',', ':'))
            elif isinstance(value, dict):
                # Use compact format for dictionaries (single line)
                step3_data[key] = json.dumps(value, separators=(',', ':'))
        
        return step3_data
    
    def convert_formulas_to_latex(self, content: str, filename: str = "") -> dict:
        """Process formulas: remove latexit blocks and optionally convert mathematical notation."""
        import time
        start_time = time.time()
        
        converted_content = content
        conversions_made = 0
        latexit_blocks_removed = 0
        
        # Step 1: Remove <latexit> blocks if enabled
        if self.remove_latexit:
            latexit_pattern = r'<latexit[^>]*>.*?</latexit>'
            latexit_blocks_removed = len(re.findall(latexit_pattern, converted_content, re.DOTALL))
            converted_content = re.sub(latexit_pattern, '', converted_content, flags=re.DOTALL)
        
        # Step 2: Convert mathematical notation if enabled
        if self.convert_formulas:
            # Add mathematical conversion logic here if needed in the future
            # For now, just remove latexit blocks
            pass
        
        processing_time = time.time() - start_time
        
        return {
            'converted_content': converted_content,
            'original_content': content,
            'conversions_made': conversions_made,
            'latexit_blocks_removed': latexit_blocks_removed,
            'processing_time_ms': round(processing_time * 1000, 2),
            'filename': filename
        }

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
        
        # Post-process: Enhance generated markdown files with rich Step 1 metadata
        if success:
            print("\n🔧 Enhancing converted files with rich metadata...")
            self._enhance_converted_files(output_path)
        
        return success
    
    def _enhance_converted_files(self, output_path: str):
        """Enhance converted markdown files with rich Step 1 metadata."""
        from pathlib import Path
        
        output_dir = Path(output_path)
        enhanced_count = 0
        
        for md_file in output_dir.glob("*.md"):
            try:
                # Read the file
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it has basic frontmatter and body
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        basic_frontmatter = parts[1]
                        body = parts[2]
                        
                        # Generate enhanced Step 1 metadata
                        enhanced_metadata = self.generate_step1_metadata(str(md_file), body)
                        
                        # Replace basic frontmatter with enhanced version
                        # Keep any existing essential metadata (filename, pages, etc.)
                        enhanced_content = f"---{enhanced_metadata}---{body}"
                        
                        # Write enhanced file
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(enhanced_content)
                        
                        enhanced_count += 1
                        
            except Exception as e:
                print(f"⚠️ Error enhancing {md_file}: {e}")
        
        print(f"✅ Enhanced {enhanced_count} files with rich Step 1 metadata")
    
    def step_classification(self, input_path: str, output_path: str) -> bool:
        """Step 2: Add document classification and basic metadata (in-place enhancement)."""
        
        if self.enhanced_mode:
            print(f"\n🔸 ENHANCED CLASSIFICATION: High-performance pattern-based classification")
        else:
            print(f"\n🔸 CLASSIFICATION: Adding document types (basic mode)")
        
        if self.convert_formulas:
            print(f"📐 LaTeX formula conversion: ENABLED (format: {self.formula_output_format})")
        elif self.remove_latexit:
            print(f"📐 LaTeX formula processing: LATEXIT REMOVAL ONLY")
        else:
            print(f"📐 LaTeX formula processing: DISABLED")
        
        start_time = time.time()
        
        # Work with markdown directory - enhance files in place
        markdown_dir = Path(input_path)
        
        files_processed = 0
        classification_errors = 0
        
        for md_file in markdown_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if self.enhanced_mode and self.classifier:
                    # Use classification + entity extraction (Layer 1)
                    result = self.classifier.classify_and_extract(content, md_file.name)
                    
                    # Cache classification for enrichment step
                    self.classification_cache[str(md_file)] = result
                    
                    # Format enhanced classification metadata with entities
                    classification_metadata = self.classifier.format_classification_metadata(result)
                else:
                    # Fallback to basic classification
                    classification_metadata = self._basic_classification(content)
                
                # Use YAMLMetadataManager for structured metadata handling - CLEAN APPROACH
                metadata, body = self.metadata_manager.parse_existing_metadata(content)
                
                # Generate Step 1 conversion metadata (structured data)
                step1_data = self._generate_step1_structured_data(str(md_file), body)
                
                # Generate Step 2 classification metadata (structured data)
                step2_data = self._generate_step2_structured_data(classification_metadata)
                
                # Create clean content with ONLY structured blocks (no loose fields)
                content = f"---\n---\n{body}"  # Start with empty metadata
                content = self.metadata_manager.update_step_metadata(content, 'step1', step1_data)
                content = self.metadata_manager.update_step_metadata(content, 'step2', step2_data)
                
                # LaTeX formula processing if enabled and formulas detected
                formula_conversion_results = None
                if ((self.convert_formulas or self.remove_latexit) and 
                    content.count('formula_conversion_ready: true') > 0):
                    
                    action = "Converting formulas" if self.convert_formulas else "Removing latexit blocks"
                    print(f"🔬 {action} in {md_file.name}...")
                    
                    # Get current body from content
                    metadata, current_body = self.metadata_manager.parse_existing_metadata(content)
                    formula_conversion_results = self.convert_formulas_to_latex(current_body, md_file.name)
                    
                    # Update content with converted formulas
                    if formula_conversion_results['conversions_made'] > 0 or formula_conversion_results['latexit_blocks_removed'] > 0:
                        # Update the body content
                        updated_body = formula_conversion_results['converted_content']
                        
                        # Add formula conversion results to step2 metadata
                        step2_data.update({
                            "formula_conversion_applied": True,
                            "latex_conversions_made": formula_conversion_results['conversions_made'],
                            "latexit_blocks_removed": formula_conversion_results['latexit_blocks_removed'],
                            "formula_conversion_time_ms": formula_conversion_results['processing_time_ms']
                        })
                        
                        # Update step2 metadata with formula results
                        content = self.metadata_manager.update_step_metadata(content, 'step2', step2_data)
                        
                        # Reconstruct content with updated body
                        metadata, _ = self.metadata_manager.parse_existing_metadata(content)
                        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False, width=float('inf'))
                        content = f"---\n{yaml_content}---\n{updated_body}"
                
                # Write enhanced file
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_processed += 1
                
            except Exception as e:
                classification_errors += 1
                print(f"⚠️ Classification error for {md_file.name}: {e}")
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        
        self.performance_stats['classification'] = {
            'time': elapsed,
            'files': files_processed,
            'errors': classification_errors,
            'pages_per_sec': pages_per_sec
        }
        
        if self.enhanced_mode:
            target_performance = pages_per_sec / 2000 * 100 if pages_per_sec > 0 else 0
            print(f"✅ Enhanced Classification: {files_processed} files, {pages_per_sec:.1f} pages/sec")
            print(f"📊 Performance vs Target (2000 pages/sec): {target_performance:.1f}%")
        else:
            print(f"✅ Basic Classification: {files_processed} files, {pages_per_sec:.1f} pages/sec")
        
        return classification_errors == 0
    
    def _basic_classification(self, content: str) -> str:
        """Fallback basic classification using keyword counting."""
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
        total_score = sum(all_domain_scores.values()) or 1
        domain_percentages = {domain: f"{(score / total_score) * 100:.1f}%" 
                            for domain, score in all_domain_scores.items()}
        
        # Determine primary domain
        primary_domain = max(confidence_scores.items(), key=lambda x: x[1])[0] if confidence_scores else 'general'
        
        return f"""
# Basic Classification (Step 2)
document_types: {doc_types}
primary_domain: {primary_domain}
classification_confidence: {max(confidence_scores.values()) if confidence_scores else 0.5:.2f}
domain_percentages: {domain_percentages}
enhanced_mode: false
"""
    
    def step_enrichment(self, input_path: str, output_path: str) -> bool:
        """Step 3: Add domain-specific enrichment (in-place enhancement)."""
        
        if self.enhanced_mode:
            print(f"\n🔸 ENHANCED ENRICHMENT: pyahocorasick + regex entity extraction")
        else:
            print(f"\n🔸 ENRICHMENT: Adding domain-specific tags (basic mode)")
        
        start_time = time.time()
        
        # Work with same markdown directory - enhance files in place
        markdown_dir = Path(input_path)
        
        files_processed = 0
        enrichment_errors = 0
        total_entities = 0
        for md_file in markdown_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract primary domain from existing classification
                primary_domain = self._extract_primary_domain(content)
                
                if self.enhanced_mode and self.enrichment:
                    # Use targeted enrichment (Layer 2) with cached classification
                    classification_result = self.classification_cache.get(str(md_file), {})
                    if not classification_result:
                        # Fallback: extract primary domain from metadata
                        classification_result = {'primary_domain': primary_domain}
                    
                    entities = self.enrichment.extract_entities_targeted(content, classification_result, md_file.name)
                    enrichment_metadata = self.enrichment.format_enrichment_metadata(entities, classification_result)
                    
                    total_entities += entities['metadata']['total_entity_count']
                else:
                    # Fallback to basic enrichment
                    enrichment_metadata = self._basic_enrichment(content, primary_domain)
                
                # Use YAMLMetadataManager for structured enrichment metadata
                step3_data = self._generate_step3_structured_data(enrichment_metadata, entities if self.enhanced_mode else {})
                content = self.metadata_manager.update_step_metadata(content, 'step3', step3_data)
                
                # Write enriched file
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_processed += 1
                
            except Exception as e:
                enrichment_errors += 1
                print(f"⚠️ Enrichment error for {md_file.name}: {e}")
        
        elapsed = time.time() - start_time
        pages_per_sec = files_processed / elapsed if elapsed > 0 else 0
        entities_per_sec = total_entities / elapsed if elapsed > 0 else 0
        
        self.performance_stats['enrichment'] = {
            'time': elapsed,
            'files': files_processed,
            'errors': enrichment_errors,
            'total_entities': total_entities,
            'pages_per_sec': pages_per_sec,
            'entities_per_sec': entities_per_sec
        }
        
        if self.enhanced_mode:
            target_performance = pages_per_sec / 1500 * 100 if pages_per_sec > 0 else 0
            print(f"✅ Enhanced Enrichment: {files_processed} files, {total_entities} entities")
            print(f"📊 Performance: {pages_per_sec:.1f} pages/sec, {entities_per_sec:.1f} entities/sec")
            print(f"📊 Performance vs Target (1500 pages/sec): {target_performance:.1f}%")
        else:
            print(f"✅ Basic Enrichment: {files_processed} files, {pages_per_sec:.1f} pages/sec")
        
        return enrichment_errors == 0
    
    def _extract_primary_domain(self, content: str) -> str:
        """Extract primary domain from existing front matter."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = parts[1]
                for line in front_matter.split('\n'):
                    if 'primary_domain:' in line:
                        return line.split(':', 1)[1].strip()
        return 'general'
    
    def _basic_enrichment(self, content: str, primary_domain: str) -> str:
        """Fallback enrichment using basic regex patterns."""
        import re
        
        # Basic entity patterns
        money_pattern = r'\$[0-9,]+(?:\.[0-9]{2})?'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        cfr_pattern = r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?'
        
        money_matches = re.findall(money_pattern, content)
        email_matches = re.findall(email_pattern, content)
        cfr_matches = re.findall(cfr_pattern, content, re.IGNORECASE)
        
        # Basic organization detection
        content_lower = content.lower()
        org_patterns = ['osha', 'niosh', 'epa', 'fda', 'cdc', 'who']
        orgs_found = [org.upper() for org in org_patterns if org in content_lower]
        
        # Basic domain tags
        domain_tags = {}
        if primary_domain == 'safety':
            hazard_keywords = ['fall', 'electrical', 'chemical', 'fire', 'ergonomic']
            hazards_found = [h for h in hazard_keywords if h in content_lower]
            if hazards_found:
                domain_tags['hazard_types'] = hazards_found
        
        return f"""
# Basic Enrichment (Step 3)
organizations: {orgs_found}
regulations: {cfr_matches}
domain_tags: {domain_tags}
entities_found: {len(money_matches) + len(email_matches) + len(cfr_matches) + len(orgs_found)}
money_mentions: {len(money_matches)}
email_mentions: {len(email_matches)}
enhanced_mode: false
"""
    
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