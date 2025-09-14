
## Directory Cleanup & Organization

### Current State Assessment
The `mvp-hyper/` directory has accumulated various files during development that need organization for maintainability and focus. Currently contains:

- **Core pipeline files**: 6 main components
- **Configuration files**: 8 different config files  
- **Test/debug scripts**: 9 testing and debugging utilities
- **Docker/deployment files**: 3 containerization files
- **Benchmark/analysis tools**: 5 performance measurement scripts
- **Documentation files**: 4 markdown documents
- **Utility scripts**: 6 setup and execution helpers

### Proposed Directory Structure

```
mvp-hyper/
├── core/                           # Main pipeline components
│   ├── mvp-hyper-core.py
│   ├── mvp-hyper-classification-enhanced.py   # New enhanced classifier
│   ├── mvp-hyper-tagger.py
│   ├── mvp-hyper-semantic.py
│   ├── mvp-hyper-pipeline-clean.py
│   └── mvp_semantic_domains.py
│
├── config/                         # Configuration files
│   ├── config.yaml                 # Main config (production)
│   ├── mvp-hyper-config.yaml      # Legacy config
│   ├── mvp-hyper-pipeline-clean-config.yaml
│   ├── pipeline-config.yaml
│   ├── docker-config.yaml
│   └── test_config.yaml           # Test configurations
│
├── tests/                          # Testing and debugging
│   ├── test_enhanced_tagger.py
│   ├── test_enhanced_semantic.py
│   ├── test_pipeline.py
│   ├── test_bi_extraction.py
│   ├── test-enhanced-classification.py  # New test for enhanced classifier
│   ├── debug_tagger.py
│   └── debug_regex.py
│
├── benchmarks/                     # Performance measurement
│   ├── benchmark.py
│   ├── distributed-benchmark.py
│   ├── distributed-benchmark-simple.py
│   ├── compare-semantic-extraction.py
│   └── continuous_processor.py
│
├── docker/                         # Containerization
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── run-docker-test.sh
│   └── docker-config.yaml (symlink)
│
├── scripts/                        # Utility and execution scripts
│   ├── setup.sh
│   ├── clean.sh
│   ├── run-pipeline.sh
│   ├── run-full-pipeline.py
│   └── diagnose_pdfs.py
│
├── utils/                          # Supporting utilities
│   ├── config_loader.py
│   └── __pycache__/               # Python cache (can be deleted)
│
├── docs/                           # Documentation
│   ├── FutureState.md             # This architecture document
│   ├── README.md
│   ├── NEW_FEATURE.md
│   └── DISTRIBUTED_BENCHMARK.md
│
├── output/                         # Output directories (created as needed)
│   ├── 1-markdown/               # Markdown conversion outputs
│   ├── 2-classified/             # Classification outputs  
│   ├── 3-enriched/               # Enrichment outputs
│   └── 4-semantic/               # Semantic extraction outputs
│
└── temp/                          # Temporary files (gitignored)
    ├── cache/
    ├── logs/
    └── working/
```

### Cleanup Implementation Plan

#### Phase 1: Create Directory Structure
```bash
# Create new directory structure
mkdir -p mvp-hyper/{core,config,tests,benchmarks,docker,scripts,utils,docs,output,temp}
mkdir -p mvp-hyper/output/{1-markdown,2-classified,3-enriched,4-semantic}
mkdir -p mvp-hyper/temp/{cache,logs,working}
```

#### Phase 2: Move Core Pipeline Files
```bash
# Move main pipeline components to core/
mv mvp-hyper-core.py core/
mv mvp-hyper-tagger.py core/
mv mvp-hyper-semantic.py core/  
mv mvp-hyper-pipeline-clean.py core/
mv mvp_semantic_domains.py core/
# mvp-hyper-classification-enhanced.py will be created in core/
```

#### Phase 3: Organize Configuration Files
```bash
# Move all config files to config/
mv *.yaml config/
mv config.yaml config/  # Ensure main config is included
```

#### Phase 4: Organize Testing & Debugging
```bash
# Move test files to tests/
mv test_*.py tests/
mv debug_*.py tests/
# test-enhanced-classification.py will be created in tests/
```

#### Phase 5: Organize Benchmarking
```bash
# Move benchmark files to benchmarks/
mv benchmark.py benchmarks/
mv distributed-benchmark*.py benchmarks/
mv compare-semantic-extraction.py benchmarks/
mv continuous_processor.py benchmarks/
```

#### Phase 6: Organize Docker & Scripts
```bash
# Move Docker files
mv Dockerfile docker/
mv docker-compose.yml docker/
mv run-docker-test.sh docker/

# Move utility scripts
mv setup.sh scripts/
mv clean.sh scripts/
mv run-*.py scripts/
mv run-*.sh scripts/
mv diagnose_pdfs.py scripts/

# Move utilities
mv config_loader.py utils/
```

#### Phase 7: Organize Documentation
```bash
# Move documentation to docs/
mv *.md docs/
```

#### Phase 8: Update Import Paths
Update all import statements in files to reflect new directory structure:

```python
# Old imports
from mvp_semantic_domains import DOMAIN_REGISTRY
import mvp_hyper_core

# New imports  
from core.mvp_semantic_domains import DOMAIN_REGISTRY
import core.mvp_hyper_core as mvp_hyper_core
```

### Updated File References

#### Pipeline Execution
```bash
# Old way
python mvp-hyper-pipeline-clean.py input/ --output output/

# New way  
python core/mvp-hyper-pipeline-clean.py input/ --output output/
```

#### Configuration Management
```bash
# Standard config location
--config config/config.yaml

# Pipeline-specific config
--config config/mvp-hyper-pipeline-clean-config.yaml
```

### Benefits of Organization

#### Development Benefits
- **Clear separation of concerns**: Core logic separate from tests and utilities
- **Easier navigation**: Related files grouped together
- **Reduced clutter**: Main directory contains only organized subdirectories
- **Better version control**: Logical grouping for git operations

#### Maintenance Benefits
- **Simplified debugging**: Test files in dedicated location
- **Configuration management**: All configs in one place with clear naming
- **Documentation accessibility**: All docs centralized and discoverable
- **Deployment preparation**: Docker files organized for containerization

#### Performance Benefits
- **Faster file access**: Organized structure reduces search time
- **Cleaner output management**: Dedicated output directories by phase
- **Temporary file management**: Designated temp space for cache/logs

### Cleanup Validation Checklist

- ✅ **Core pipeline files**: All main components in `core/` directory
- ✅ **Configuration centralized**: All YAML configs in `config/` directory  
- ✅ **Tests organized**: All test/debug files in `tests/` directory
- ✅ **Benchmarks grouped**: Performance tools in `benchmarks/` directory
- ✅ **Docker containerized**: All deployment files in `docker/` directory
- ✅ **Scripts consolidated**: Utility scripts in `scripts/` directory
- ✅ **Documentation accessible**: All markdown files in `docs/` directory
- ✅ **Output structured**: Phase-based output directories created
- ✅ **Import paths updated**: All file references corrected
- ✅ **Execution verified**: Pipeline runs correctly from new structure

---

## Future Considerations

### Phase 2 Enhancements (Post-Implementation)
- **Multi-language support**: Extend spaCy models for non-English documents
- **Custom entity training**: Train domain-specific entity models
- **Advanced structural parsing**: Table extraction, complex document layouts
- **Performance scaling**: Distributed processing, GPU acceleration

### Integration Opportunities
- **Real-time processing**: Stream processing capabilities
- **API integration**: RESTful API for external system integration  
- **Cloud deployment**: Scalable cloud-based processing pipeline
- **Analytics integration**: Performance monitoring and optimization dashboards

---

*Document Version: 1.0*  
*Last Updated: 2025-09-14*  
*Status: Architecture Planning Complete - Ready for Implementation*