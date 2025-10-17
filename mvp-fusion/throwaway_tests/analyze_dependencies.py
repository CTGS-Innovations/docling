#!/usr/bin/env python3
"""
Analyze actual dependency usage in MVP-Fusion project.
Maps import statements to PyPI package names.
"""

import re
import ast
from pathlib import Path
from typing import Set

# Map of common import names to PyPI package names
IMPORT_TO_PACKAGE = {
    'bs4': 'beautifulsoup4',
    'yaml': 'PyYAML',
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'sklearn': 'scikit-learn',
    'ahocorasick': 'pyahocorasick',
}

def extract_imports_from_file(filepath: Path) -> Set[str]:
    """Extract all top-level imports from a Python file."""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse imports using AST for accuracy
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except SyntaxError:
            # Fallback to regex if AST fails
            for match in re.finditer(r'^(?:from\s+(\S+)|import\s+(\S+))', content, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module:
                    imports.add(module.split('.')[0].split(',')[0].strip())
    except Exception:
        pass

    return imports

# Find all source Python files (excluding venv)
source_files = []
for filepath in Path('/home/corey/projects/docling/mvp-fusion').rglob('*.py'):
    # Skip virtual environments and site-packages
    if any(part in filepath.parts for part in ['lib', 'lib64', '.venv-clean', 'site-packages', '__pycache__']):
        continue
    source_files.append(filepath)

# Collect all imports
all_imports = set()
for filepath in source_files:
    all_imports.update(extract_imports_from_file(filepath))

# Filter to third-party only (exclude stdlib and local modules)
stdlib_modules = {
    'os', 'sys', 're', 'json', 'pathlib', 'typing', 'datetime', 'time',
    'collections', 'itertools', 'functools', 'logging', 'argparse', 'csv',
    'io', 'copy', 'dataclasses', 'enum', 'abc', 'asyncio', 'concurrent',
    'multiprocessing', 'threading', 'subprocess', 'tempfile', 'shutil',
    'glob', 'fnmatch', 'hashlib', 'pickle', 'warnings', 'traceback',
    'urllib', 'html', 'math', 'contextlib', 'signal', 'gc', 'gzip',
    'zipfile', 'queue', 'cProfile', 'pstats', 'tracemalloc', 'ctypes'
}

local_modules = {
    'fusion', 'utils', 'extraction', 'knowledge', 'metadata',
    'normalization', 'pipeline', 'performance', 'tests'
}

third_party = sorted([
    m for m in all_imports
    if m not in stdlib_modules and m not in local_modules
])

print('=' * 60)
print('THIRD-PARTY PACKAGES ACTUALLY USED:')
print('=' * 60)
for pkg in third_party:
    # Map to PyPI package name if known
    pypi_name = IMPORT_TO_PACKAGE.get(pkg, pkg)
    if pypi_name != pkg:
        print(f'  {pkg:20} -> {pypi_name}')
    else:
        print(f'  {pkg}')
