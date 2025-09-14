#!/usr/bin/env python3
"""
Configuration loader for MVP Hyper-Core
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any


class Config:
    """Configuration manager for MVP Hyper-Core."""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        
        if not self.config_file.exists():
            print(f"Warning: Config file {self.config_file} not found, using defaults")
            return self._default_config()
            
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            # Expand home directory paths
            self._expand_paths(config)
            return config
            
        except Exception as e:
            print(f"Error loading config {self.config_file}: {e}")
            print("Using default configuration")
            return self._default_config()
    
    def _expand_paths(self, config: Dict[str, Any]):
        """Expand ~ in file paths."""
        
        if 'inputs' in config:
            if 'files' in config['inputs']:
                config['inputs']['files'] = [
                    os.path.expanduser(p) for p in config['inputs']['files']
                ]
            if 'directories' in config['inputs']:
                config['inputs']['directories'] = [
                    os.path.expanduser(p) for p in config['inputs']['directories']
                ]
        
        if 'output' in config and 'directory' in config['output']:
            config['output']['directory'] = os.path.expanduser(config['output']['directory'])
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file is missing."""
        
        return {
            'inputs': {
                'files': [],
                'directories': []
            },
            'processing': {
                'max_workers': 8,
                'skip_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                                  '.mp3', '.mp4', '.wav', '.avi', '.mov', '.wmv', '.flv',
                                  '.zip', '.tar', '.gz', '.bz2', '.rar', '.7z',
                                  '.exe', '.dll', '.so', '.dylib', '.bin', '.dat'],
                'max_file_size_mb': 100,
                'timeout_per_file': 10,
                'slow_file_threshold': 5.0
            },
            'pdf': {
                'skip_patterns': [],
                'fallback_strategies': ['direct_file_open', 'pdftotext_command', 'basic_text_only']
            },
            'output': {
                'directory': 'output',
                'save_performance_log': True,
                'save_error_log': True
            },
            'debug': {
                'progress_interval': 50,
                'timing_threshold': 1.0,
                'max_files_to_process': 0
            }
        }
    
    def get_input_files(self) -> List[Path]:
        """Get list of all input files from config."""
        
        all_files = []
        
        # Add individual files
        files_list = self.config.get('inputs', {}).get('files', [])
        for file_path in files_list:
            path = Path(file_path)
            if path.is_file():
                all_files.append(path)
            else:
                print(f"Warning: File not found: {file_path}")
        
        # Add files from directories
        directories_list = self.config.get('inputs', {}).get('directories', [])
        for dir_path in directories_list:
            path = Path(dir_path)
            if path.is_dir():
                print(f"Scanning directory: {path}")
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)
            else:
                print(f"Warning: Directory not found: {dir_path}")
        
        return self._filter_files(all_files)
    
    def _filter_files(self, files: List[Path]) -> List[Path]:
        """Filter files based on config settings."""
        
        filtered = []
        skip_extensions = set(self.config['processing']['skip_extensions'])
        max_size = self.config['processing']['max_file_size_mb'] * 1024 * 1024
        skip_patterns = self.config['pdf']['skip_patterns']
        max_files = self.config['debug']['max_files_to_process']
        
        for file_path in files:
            # Skip by extension
            if file_path.suffix.lower() in skip_extensions:
                continue
                
            # Skip by file size
            try:
                if file_path.stat().st_size > max_size:
                    print(f"Skipping large file: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
                    continue
            except:
                continue
                
            # Skip by filename patterns
            skip_file = False
            for pattern in skip_patterns:
                if pattern.lower() in file_path.name.lower():
                    print(f"Skipping file matching pattern '{pattern}': {file_path.name}")
                    skip_file = True
                    break
            
            if skip_file:
                continue
                
            filtered.append(file_path)
            
            # Limit for testing
            if max_files > 0 and len(filtered) >= max_files:
                break
        
        return filtered
    
    def should_skip_pdf(self, file_path: Path) -> bool:
        """Check if a PDF should be skipped based on patterns."""
        
        skip_patterns = self.config['pdf']['skip_patterns']
        for pattern in skip_patterns:
            if pattern.lower() in file_path.name.lower():
                return True
        return False
    
    def get(self, key_path: str, default=None):
        """Get config value using dot notation (e.g., 'processing.max_workers')."""
        
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value


# Example usage functions
def load_config(config_file: str = "config.yaml") -> Config:
    """Load configuration from file."""
    return Config(config_file)


def create_test_config():
    """Create a test config file for troubleshooting specific PDFs."""
    
    test_config = {
        'inputs': {
            'files': [
                # Add specific problematic PDFs here for testing
                "~/projects/docling/cli/data_osha/training-requirements-by-standard.pdf",
                "~/projects/docling/cli/data_osha/2254-training-requirements-in-osha-standards.pdf",
                "~/projects/docling/cli/data_osha/2268-shipyard-industry-standards.pdf"
            ],
            'directories': []
        },
        'processing': {
            'max_workers': 1,  # Single threaded for debugging
            'timeout_per_file': 30,
            'slow_file_threshold': 2.0
        },
        'pdf': {
            'skip_patterns': [],
            'fallback_strategies': ['direct_file_open', 'pdftotext_command']
        },
        'debug': {
            'max_files_to_process': 5,  # Only process 5 files
            'progress_interval': 1,     # Show progress every file
            'timing_threshold': 0.5
        },
        'output': {
            'directory': 'test_output'
        }
    }
    
    with open('test_config.yaml', 'w') as f:
        yaml.dump(test_config, f, default_flow_style=False)
    
    print("Created test_config.yaml for troubleshooting specific PDFs")


if __name__ == "__main__":
    # Create test config for troubleshooting
    create_test_config()