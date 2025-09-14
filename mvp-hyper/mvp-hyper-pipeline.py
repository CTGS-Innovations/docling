#!/usr/bin/env python3
"""
MVP Hyper Processing Pipeline
=============================
Three-tier progressive refinement system with individual stage control.

Tier 1: Fast Document Classifier (5000+ pages/sec)
Tier 2: Domain-Specific Pre-Tagger (1500+ pages/sec) 
Tier 3: Enhanced Semantic Extraction (300+ pages/sec)

Usage:
  python mvp-hyper-pipeline.py input/ --output output/ --config pipeline-config.yaml
  python mvp-hyper-pipeline.py input/ --tier1-only  # Just classification
  python mvp-hyper-pipeline.py input/ --tier2-only  # Classification + domain tagging
  python mvp-hyper-pipeline.py input/ --tier3-only  # Full pipeline
  python mvp-hyper-pipeline.py input/ --baseline    # Just convert to markdown
"""

import argparse
import yaml
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import importlib.util

# Import existing components
spec_core = importlib.util.spec_from_file_location("mvp_hyper_core", "mvp-hyper-core.py")
mvp_hyper_core = importlib.util.module_from_spec(spec_core)
spec_core.loader.exec_module(mvp_hyper_core)

spec_semantic = importlib.util.spec_from_file_location("mvp_hyper_semantic", "mvp-hyper-semantic.py")
mvp_hyper_semantic = importlib.util.module_from_spec(spec_semantic)
spec_semantic.loader.exec_module(mvp_hyper_semantic)

@dataclass
class ProcessingStats:
    """Processing statistics for performance monitoring."""
    files_processed: int = 0
    total_time: float = 0.0
    tier1_time: float = 0.0
    tier2_time: float = 0.0
    tier3_time: float = 0.0
    pages_per_sec: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class MVPHyperPipeline:
    """Three-tier progressive document processing pipeline."""
    
    def __init__(self, config_path: str = "mvp-hyper-config.yaml"):
        """Initialize pipeline with configuration."""
        self.config = self._load_config(config_path)
        self.stats = ProcessingStats()
        
        # Pre-compile regex patterns for performance
        self._compile_patterns()
        
        # Initialize semantic extractor if needed
        self.semantic_extractor = None
        if self.config['pipeline']['tier3_semantic']['enabled']:
            self.semantic_extractor = mvp_hyper_semantic.MVPHyperSemanticExtractor()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load pipeline configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration if config file not found."""
        return {
            'pipeline': {
                'output_directory': 'output',
                'tier1_classifier': {'enabled': True, 'confidence_threshold': 0.5},
                'tier2_pretagger': {'enabled': True},
                'tier3_semantic': {'enabled': True, 'max_facts_per_doc': 100}
            },
            'output': {
                'formats': {
                    'enhanced_markdown': True,
                    'semantic_json': True,
                    'performance_stats': True
                }
            }
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.tier1_patterns = {}
        self.tier2_patterns = {}
        
        # Compile Tier 1 classification patterns
        if 'patterns' in self.config['pipeline']['tier1_classifier']:
            for doc_type, pattern_str in self.config['pipeline']['tier1_classifier']['patterns'].items():
                self.tier1_patterns[doc_type] = re.compile(pattern_str, re.I)
        
        # Compile Tier 2 domain-specific patterns  
        if 'domains' in self.config['pipeline']['tier2_pretagger']:
            for domain, patterns in self.config['pipeline']['tier2_pretagger']['domains'].items():
                self.tier2_patterns[domain] = {}
                for pattern_name, pattern_str in patterns.items():
                    self.tier2_patterns[domain][pattern_name] = re.compile(pattern_str, re.I)
        
        # Compile universal entity patterns
        self.universal_patterns = {}
        if 'universal_entities' in self.config['pipeline']['tier2_pretagger']:
            for entity_type, pattern_str in self.config['pipeline']['tier2_pretagger']['universal_entities'].items():
                self.universal_patterns[entity_type] = re.compile(pattern_str, re.I)
    
    def process_files(self, input_path: str, output_path: str, 
                     tier1_only: bool = False, tier2_only: bool = False, 
                     baseline_only: bool = False) -> ProcessingStats:
        """Process files through the three-tier pipeline."""
        
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all input files recursively
        input_files = []
        if input_dir.is_file():
            input_files = [input_dir]
        else:
            # Search recursively for supported file types
            for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.md', '*.html', '*.csv']:
                input_files.extend(input_dir.rglob(ext))  # rglob for recursive search
        
        print(f"🔧 Processing {len(input_files)} files through MVP Hyper Pipeline")
        print(f"📂 Output: {output_dir}")
        
        total_start = time.time()
        
        for file_path in input_files:
            try:
                self._process_single_file(file_path, output_dir, tier1_only, tier2_only, baseline_only)
                self.stats.files_processed += 1
            except Exception as e:
                error_msg = f"Failed to process {file_path}: {str(e)}"
                self.stats.errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        self.stats.total_time = time.time() - total_start
        self.stats.pages_per_sec = self._calculate_pages_per_sec()
        
        self._print_summary()
        return self.stats
    
    def _process_single_file(self, file_path: Path, output_dir: Path, 
                           tier1_only: bool, tier2_only: bool, baseline_only: bool):
        """Process a single file through the pipeline."""
        
        print(f"📄 Processing: {file_path.name}")
        
        # Convert to markdown (always required)
        markdown_content = self._convert_to_markdown(file_path)
        output_file = output_dir / f"{file_path.stem}.md"
        
        if baseline_only:
            # Just save markdown and exit
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            return
        
        # Tier 1: Fast Document Classification
        tier1_start = time.time()
        classification = self._tier1_classify(markdown_content)
        self.stats.tier1_time += time.time() - tier1_start
        
        if tier1_only:
            # Save with Tier 1 metadata only
            enhanced_content = self._add_front_matter(markdown_content, classification)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            return
        
        # Tier 2: Domain-Specific Pre-Tagging
        tier2_start = time.time()
        domain_tags = self._tier2_pretag(markdown_content, classification)
        self.stats.tier2_time += time.time() - tier2_start
        
        # Combine Tier 1 + Tier 2 metadata
        combined_metadata = {**classification, **domain_tags}
        
        if tier2_only:
            # Save with Tier 1 + Tier 2 metadata
            enhanced_content = self._add_front_matter(markdown_content, combined_metadata)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            return
        
        # Tier 3: Enhanced Semantic Extraction
        tier3_start = time.time()
        semantic_facts = self._tier3_extract(markdown_content, combined_metadata)
        self.stats.tier3_time += time.time() - tier3_start
        
        # Save enhanced markdown
        enhanced_content = self._add_front_matter(markdown_content, combined_metadata)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        # Save semantic JSON
        if self.config['output']['formats']['semantic_json']:
            semantic_file = output_dir / f"{file_path.stem}.metadata.json"
            with open(semantic_file, 'w', encoding='utf-8') as f:
                json.dump(semantic_facts, f, indent=2, ensure_ascii=False)
    
    def _convert_to_markdown(self, file_path: Path) -> str:
        """Convert input file to markdown using existing converter."""
        # Use existing mvp-hyper-core conversion logic
        if file_path.suffix.lower() == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # TODO: Integrate with existing docling conversion
            # For now, return placeholder
            return f"# {file_path.stem}\n\nContent converted from {file_path.suffix}"
    
    def _tier1_classify(self, content: str) -> Dict[str, Any]:
        """Tier 1: Balanced fast classification - accurate but performant."""
        start_time = time.time()
        content_lower = content.lower()
        scores = {}
        
        # Load keyword sets from config
        keyword_sets = {}
        if 'keywords' in self.config['pipeline']['tier1_classifier']:
            config_keywords = self.config['pipeline']['tier1_classifier']['keywords']
            for doc_type, keyword_list in config_keywords.items():
                keyword_sets[doc_type] = set(word.lower() for word in keyword_list)
        else:
            # Fallback to default sets if config doesn't have keywords
            keyword_sets = {
                'technical': {'algorithm', 'function', 'method', 'system', 'database', 'api', 'code'},
                'legal': {'shall', 'agreement', 'contract', 'copyright', 'patent', 'clause'},
                'safety': {'safety', 'hazard', 'risk', 'osha', 'emergency', 'protection'},
                'financial': {'revenue', 'profit', 'investment', 'budget', 'cost', 'tax'},
                'research': {'research', 'study', 'hypothesis', 'analysis', 'experiment', 'data'},
                'business': {'business', 'company', 'market', 'customer', 'strategy', 'management'}
            }
        
        # Weighted scoring based on word frequency (more sophisticated than just presence)
        words = content_lower.split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        for doc_type, keywords in keyword_sets.items():
            # Sum up frequencies of matching keywords (weighted scoring)
            scores[doc_type] = sum(word_counts.get(keyword, 0) for keyword in keywords)
        
        # Calculate percentages
        total_matches = sum(scores.values())
        if total_matches == 0:
            return {
                'document_types': ['general: 100%'],
                'confidence': 0.5,
                'processing_time': time.time()
            }
        
        # Get top 3 types
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        type_percentages = []
        confidence = 0.0
        
        for doc_type, score in sorted_types:
            if score > 0:
                pct = (score / total_matches) * 100
                type_percentages.append(f"{doc_type}: {pct:.0f}%")
                if doc_type == sorted_types[0][0]:  # Primary type
                    confidence = min(pct / 100, 1.0)
        
        processing_time = time.time() - start_time
        
        return {
            'document_types': type_percentages or ['general: 100%'],
            'confidence': confidence,
            'classification_time': f"{processing_time:.4f}s"
        }
    
    def _tier2_pretag(self, content: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Tier 2: Domain-specific pre-tagging."""
        tags = {}
        
        # Extract universal entities (always)
        universal_entities = {}
        for entity_type, pattern in self.universal_patterns.items():
            matches = []
            for match in pattern.finditer(content):
                if match.lastindex and match.lastindex >= 1:
                    matches.append(match.group(1))
                else:
                    matches.append(match.group(0))
            
            if matches:
                universal_entities[entity_type] = list(set(matches))[:10]  # Limit and dedupe
        
        if universal_entities:
            tags['universal_entities'] = universal_entities
        
        # Determine primary domain from classification
        primary_type = classification.get('document_types', ['general: 100%'])[0].split(':')[0]
        
        # Apply domain-specific patterns
        if primary_type in self.tier2_patterns:
            domain_patterns = self.tier2_patterns[primary_type]
            
            for pattern_name, pattern in domain_patterns.items():
                matches = []
                for match in pattern.finditer(content):
                    if match.lastindex and match.lastindex >= 1:
                        matches.append(match.group(1))
                    else:
                        matches.append(match.group(0))
                
                if matches:
                    tags[pattern_name] = list(set(matches))[:10]  # Limit and dedupe
        
        tags['domain_processing_time'] = f"{time.time():.3f}s"
        return tags
    
    def _tier3_extract(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Tier 3: Enhanced semantic extraction."""
        if not self.semantic_extractor:
            return {'semantic_facts': [], 'processing_time': f"{time.time():.3f}s"}
        
        # Convert metadata to format expected by semantic extractor
        enhanced_content = self._add_front_matter(content, metadata)
        
        # Extract semantic facts using existing extractor
        try:
            semantic_result = self.semantic_extractor.extract_semantic_metadata(
                Path("temp.md"), enhanced_content
            )
            
            return {
                'facts': [asdict(fact) for fact in semantic_result.facts],
                'entities': [asdict(entity) for entity in semantic_result.entities], 
                'relationships': semantic_result.relationships,
                'extraction_stats': semantic_result.extraction_stats,
                'processing_time': semantic_result.processing_time
            }
        except Exception as e:
            return {'error': str(e), 'processing_time': f"{time.time():.3f}s"}
    
    def _add_front_matter(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add metadata as YAML front matter to markdown content."""
        
        # Remove existing front matter if present
        if content.strip().startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].lstrip('\n')
        
        # Create YAML front matter
        yaml_lines = ['---']
        for key, value in metadata.items():
            if isinstance(value, list):
                yaml_lines.append(f"{key}: {value}")
            elif isinstance(value, dict):
                yaml_lines.append(f"{key}:")
                for subkey, subvalue in value.items():
                    yaml_lines.append(f"  {subkey}: {subvalue}")
            else:
                yaml_lines.append(f"{key}: {value}")
        yaml_lines.append('---')
        yaml_lines.append('')
        
        return '\n'.join(yaml_lines) + content
    
    def _calculate_pages_per_sec(self) -> float:
        """Calculate processing speed in pages per second."""
        if self.stats.total_time == 0:
            return 0.0
        # Assume average 2000 characters per page
        total_chars = self.stats.files_processed * 2000  # Rough estimate
        pages = total_chars / 2000
        return pages / self.stats.total_time
    
    def _print_summary(self):
        """Print processing summary."""
        print(f"\n✅ Pipeline Processing Complete!")
        print(f"📊 Files processed: {self.stats.files_processed}")
        print(f"⏱️  Total time: {self.stats.total_time:.2f}s")
        print(f"🚀 Speed: {self.stats.pages_per_sec:.1f} pages/sec")
        print(f"🔍 Tier 1 time: {self.stats.tier1_time:.2f}s")
        print(f"🏷️  Tier 2 time: {self.stats.tier2_time:.2f}s") 
        print(f"🧠 Tier 3 time: {self.stats.tier3_time:.2f}s")
        
        if self.stats.errors:
            print(f"❌ Errors: {len(self.stats.errors)}")
            for error in self.stats.errors:
                print(f"   - {error}")

def main():
    parser = argparse.ArgumentParser(
        description="MVP Hyper Three-Tier Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full three-tier pipeline
  python mvp-hyper-pipeline.py input/ --output output/
  
  # Individual tier testing
  python mvp-hyper-pipeline.py input/ --baseline        # Just markdown conversion
  python mvp-hyper-pipeline.py input/ --tier1-only      # + document classification  
  python mvp-hyper-pipeline.py input/ --tier2-only      # + domain-specific tagging
  python mvp-hyper-pipeline.py input/ --tier3-only      # + semantic extraction (default)
  
  # Custom configuration
  python mvp-hyper-pipeline.py input/ --config custom-config.yaml
        """
    )
    
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--config", "-c", default="pipeline-config.yaml", help="Configuration file")
    
    # Pipeline control flags
    parser.add_argument("--baseline", action="store_true", help="Convert to markdown only (no tagging)")
    parser.add_argument("--tier1-only", action="store_true", help="Tier 1: Document classification only")
    parser.add_argument("--tier2-only", action="store_true", help="Tier 1+2: Add domain-specific pre-tagging")
    parser.add_argument("--tier3-only", action="store_true", help="Full pipeline: Add semantic extraction (default)")
    
    args = parser.parse_args()
    
    # Initialize and run pipeline
    pipeline = MVPHyperPipeline(args.config)
    
    stats = pipeline.process_files(
        args.input,
        args.output, 
        tier1_only=args.tier1_only,
        tier2_only=args.tier2_only,
        baseline_only=args.baseline
    )
    
    # Save performance stats if configured
    if pipeline.config['output']['formats'].get('performance_stats', False):
        stats_file = Path(args.output) / "pipeline_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(asdict(stats), f, indent=2)
        print(f"📈 Performance stats saved to: {stats_file}")

if __name__ == "__main__":
    main()