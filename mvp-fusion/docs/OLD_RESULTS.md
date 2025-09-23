python fusion_cli.py
📋 Config: config/config.yaml
🚀 Deployment Profile: Local Development/CLI
MVP-Fusion Engine: HighSpeed_Markdown_General
Performance: High-speed document extraction (2000+ pages/sec) with markdown output
Workers: 2 | Formats: 38
Profile: Local Development/CLI | Memory: 6553MB
Output directory: ../output/fusion
Processing 1 directories from config (default):
   - ~/projects/docling/cli/data_complex
📊 PROCESSING SUMMARY:
   Total files: 5
   File types: {'.pdf': 3, '.txt': 1, '.md': 1}
   Total URLs: 0
   Workers: 2
Starting file batch processing with clean pipeline architecture...
🏗️ Initializing Clean Pipeline Architecture

======================================================================
📈 CORE-8 INITIALIZATION SUMMARY
----------------------------------------------------------------------
Entity          Patterns        Engine                   
----------------------------------------------------------------------
PERSON                 498,064 Aho-Corasick ✅           
ORG                    142,293 Aho-Corasick ✅           
GPE                      3,247 Aho-Corasick ✅           
LOC                      1,167 Aho-Corasick ✅           
DATE             FLPC Compiled FLPC Engine ✅            
TIME             FLPC Compiled FLPC Engine ✅            
MONEY            FLPC Compiled FLPC Engine ✅            
MEASUREMENT      FLPC Compiled FLPC Engine ✅            
----------------------------------------------------------------------
TOTAL                  644,771 848.2ms                  
======================================================================
Service Processor initialized: 1 I/O + 8 CPU workers
🔄 Starting phase: document_processing
Starting I/O + CPU service...
Service started: 1 I/O worker + 8 CPU workers
Processing 5 files with I/O + CPU service
I/O worker starting ingestion of 5 files
I/O worker completed ingestion of 5 files
I/O ingestion completed
Service processing complete: 5 results in 0.96s
✅ Phase 'document_processing' completed in 2944.94ms

📊 PHASE PERFORMANCE:
   🔄 PDF Conversion: 6083 pages/sec, 304 MB/sec (108 pages, 17.7531ms)
   📄 Document Processing: 248 pages/sec, 12 MB/sec (108 pages, 435.6253ms)
   🏷️  Classification: 129609 pages/sec, 6 GB/sec (108 pages, 0.8333ms)
   🔍 Entity Extraction: 21570706 pages/sec, 1 TB/sec (108 pages, 0.0050ms)
   🔄 Normalization: 15394 pages/sec, 770 MB/sec (108 pages, 7.0157ms)
   🧠 Semantic Analysis: 2885254 pages/sec, 144 GB/sec (108 pages, 0.0374ms)
   💾 File Writing: 8559 pages/sec, 428 MB/sec (108 pages, 12.6183ms)

🚀 PROCESSING PERFORMANCE:
   🚀 PAGES/SEC: 0 (overall pipeline)
   ⚡ THROUGHPUT: 5.6 MB/sec raw document processing

🔧 CLEAN PIPELINE PERFORMANCE:
   🏗️  Pipeline Architecture: Clean Phase Separation
   🔧 Primary Processor: service_processor
   ⚡ Total Pipeline Time: 2945.01ms
   • ✅ document_processing: 2944.94ms (100.0%) - 0 pages/sec
   📊 INPUT: 17 MB across 5 files (0 pages)
   📊 OUTPUT: 2.0 MB in 5 markdown files
   🗜️  COMPRESSION: 87.8% smaller (eliminated formatting, images, bloat)
   📁 RESULTS: 5 successful
   ⚡ PROCESSING TIME: 2.95s
   🔧 INITIALIZATION TIME: 2.25s
   ⏱️  TOTAL TIME: 5.19s

💻 PROCESSING FOOTPRINT:

🧪 SIDECAR A/B TESTING STATUS:
   ⚪ No sidecars configured