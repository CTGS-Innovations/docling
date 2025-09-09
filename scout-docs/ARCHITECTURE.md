# Docling Integration Architecture

## Overview
This demo showcases Docling as a **backend processing service** in a clean multi-tier architecture designed for **performance analysis** and **knowledge pipeline development**.

## Architecture Layers

### 1. Frontend (React) - Port 3000
**Purpose**: Clean UI for uploading files and monitoring processing
**Components**:
- `FileUpload.js` - Drag & drop file interface
- `URLInput.js` - Process documents from URLs  
- `ProcessingLog.js` - Real-time processing logs with timing
- `ResultsViewer.js` - Formatted output with performance metrics
- `JobsList.js` - Processing history and job tracking

**Key Features**:
- Real-time WebSocket updates during processing
- Performance metrics visualization (words/sec, timing breakdown)
- Export processed content for knowledge pipelines

### 2. Backend API (FastAPI) - Port 8000  
**Purpose**: Business logic, job management, and Docling orchestration
**Components**:
- `main.py` - API endpoints and WebSocket management
- `docling_service.py` - **Core Docling integration with timing**
- `logger.py` - Structured logging with performance tracking
- `websocket_manager.py` - Real-time updates to frontend

**Key Features**:
- Async document processing with detailed timing
- Phase-by-phase processing logs (Loading → Conversion → Output)
- Multiple pipeline support (Standard vs VLM)
- Performance metrics collection

### 3. Docling Processing Engine
**Integration**: Installed in backend container via pip
**Configuration**:
```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PipelineOptions

class DoclingProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
    
    async def process_document(self, source, pipeline, output_format):
        # Timed processing with detailed logging
        start_time = time.perf_counter()
        
        # Phase 1: Document Loading (timed)
        # Phase 2: Docling Conversion (timed) 
        # Phase 3: Output Generation (timed)
        
        result = self.converter.convert(source)
        
        return ProcessingResult(
            output_content=result.document.export_to_markdown(),
            metrics=timing_data,
            success=True
        )
```

## Processing Flow

### 1. Document Input
```
User uploads file/URL → Frontend → POST /api/upload → Backend
```

### 2. Docling Processing (Backend)
```python
# Detailed timing and logging for each phase:

⚡ Processing started: document.pdf
📖 Phase 1: Loading document... (0.234s)
🔄 Phase 2: Docling conversion... (2.156s) 
📤 Phase 3: Generating output... (0.089s)
📊 Document stats: 15 pages, ~3,247 words
🚀 Speed: 1,507 words/second
✅ Processing completed in 2.479s
```

### 3. Real-time Updates (WebSocket)
```javascript
// Frontend receives live updates:
{
  "job_id": "abc123",
  "progress": 75,
  "logs": ["🔄 Phase 2: Docling conversion..."],
  "metrics": {
    "conversion_time": 2.156,
    "words_processed": 3247
  }
}
```

### 4. Results Display
- **Performance Metrics**: Conversion time, throughput, processing breakdown
- **Output Content**: Markdown/HTML/JSON with copy/download options
- **Processing History**: All jobs with timing comparisons

## Performance Focus

### Timing Analysis
- **Loading Time**: Document download/file reading
- **Conversion Time**: Core Docling ML processing
- **Output Generation**: Format conversion (MD/HTML/JSON)
- **Total Throughput**: Words per second processing speed

### Use Cases
- **Knowledge Pipeline**: Convert docs to clean Markdown for LLM training
- **Dataset Creation**: Batch process documents for fine-tuning datasets
- **Performance Benchmarking**: Compare processing speeds across document types
- **Pipeline Comparison**: Standard vs VLM processing performance

## Production Benefits

### Clean Architecture
- **Frontend**: No heavy dependencies, pure UI/UX
- **Backend**: Stateless API, easy to scale horizontally
- **Docling**: Isolated processing, can be containerized separately

### Observable Processing
- **Real-time Logs**: Watch processing phases in action
- **Performance Metrics**: Detailed timing for optimization
- **Job History**: Track processing patterns and bottlenecks

### Scalable Design
- **Horizontal Scaling**: Add more backend containers
- **Load Balancing**: Nginx can distribute processing load
- **Queue Management**: Redis for job queuing and caching

This architecture gives you a **professional sandbox** to explore Docling's capabilities while building toward production knowledge pipelines.