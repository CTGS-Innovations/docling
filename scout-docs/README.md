# Docling Demo Application

A containerized web application showcasing Docling's document processing capabilities with real-time logging, performance metrics, and a clean, professional UI.

## 🚀 Features

- **Clean UI**: Modern React interface with drag-and-drop file uploads
- **Real-time Processing**: WebSocket-powered live updates and logging
- **Performance Metrics**: Detailed timing analysis and processing stats
- **Multiple Formats**: Support for PDF, DOCX, HTML, images, audio files
- **Pipeline Options**: Standard and VLM (Vision Language Model) processing
- **Export Options**: Markdown, HTML, and JSON output formats
- **Processing History**: Track and review all processing jobs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Docling       │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Processing    │
│   Port: 3000    │    │   Port: 8000    │    │   Core          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Redis         │
│   Port: 80      │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ available RAM
- Internet connection (for downloading Docling models)

### Launch the Application

1. **Clone and navigate to the project**:
   ```bash
   cd /home/corey/projects/docling/scout-docs
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - **Web UI**: http://localhost (via nginx)
   - **Direct Frontend**: http://localhost:3000 (development)
   - **API**: http://localhost:8000 (FastAPI docs at /docs)

### First Run Notes
- Initial startup may take 2-3 minutes while Docling downloads ML models
- Watch the backend logs for model download progress
- The UI will show "connecting" until the backend is fully ready

## 📊 Performance Focus

This demo is specifically designed to showcase **Docling's processing speed and capabilities**:

### Key Metrics Displayed
- **Loading Time**: Document download/reading
- **Conversion Time**: Core Docling processing
- **Output Generation**: Format conversion (MD/HTML/JSON)
- **Words per Second**: Processing throughput
- **Memory Usage**: Resource consumption

### Real-time Logging
- Phase-by-phase processing breakdown
- Detailed timing for each step
- Error handling and diagnostics
- Performance summaries

## 🎯 Use Cases

### Knowledge Pipeline for LLMs
- Convert documents to clean Markdown for training data
- Process large document collections with batch operations
- Extract structured content for fine-tuning datasets
- Quality control with visual inspection of results

### Document Processing Research
- Compare processing speeds across different document types
- Benchmark Standard vs VLM pipeline performance
- Analyze processing patterns and bottlenecks
- Export metrics for further analysis

## 🔧 Configuration Options

### Pipeline Selection
- **Standard**: Fast, CPU-based processing
- **VLM**: Vision Language Model (slower, more accurate for complex layouts)

### Output Formats
- **Markdown**: Clean, structured text (ideal for LLM training)
- **HTML**: Formatted web content
- **JSON**: Structured data with metadata

### Processing Sources
- **File Upload**: Drag-and-drop interface (max 100MB)
- **URL Processing**: Direct web document processing

## 📁 Project Structure

```
scout-docs/
├── docker-compose.yml      # Multi-container orchestration
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── main.py           # API endpoints
│   │   ├── docling_service.py # Core processing logic
│   │   ├── logger.py         # Logging utilities
│   │   └── websocket_manager.py # Real-time updates
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React application
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── App.js          # Main application
│   │   └── index.js        # Entry point
│   ├── package.json
│   └── Dockerfile
├── nginx/               # Reverse proxy
│   └── nginx.conf
└── storage/            # Local file storage
```

## 🔍 Monitoring and Logs

### Backend Logs
```bash
docker-compose logs backend -f
```

### Frontend Logs
```bash
docker-compose logs frontend -f
```

### All Services
```bash
docker-compose logs -f
```

## 🛠️ Development

### Local Development Mode
```bash
# Backend only (with auto-reload)
cd backend && python -m app.main

# Frontend only (with hot reload)
cd frontend && npm start
```

### Adding New Features
1. Backend changes: Edit files in `backend/app/`
2. Frontend changes: Edit files in `frontend/src/`
3. Changes auto-reload in development mode

## 🚧 Future Enhancements

- **Cloud Storage**: Cloudflare R2 and Google Cloud Storage integration
- **Batch Processing**: Multiple file upload and processing
- **Export Pipeline**: Direct integration with knowledge bases
- **Performance Analytics**: Historical metrics and trends
- **API Keys**: Authentication for production deployment

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting**: Check Docker logs for model download issues
2. **WebSocket connection failed**: Ensure all containers are running
3. **File upload fails**: Check file size (100MB limit) and format support
4. **Processing stuck**: Check backend logs for Docling errors

### Reset Everything
```bash
docker-compose down -v  # Remove containers and volumes
docker-compose up --build --force-recreate
```

## 📝 API Endpoints

- `POST /api/upload` - Upload and process file
- `POST /api/process-url` - Process document from URL  
- `GET /api/jobs/{job_id}` - Get job status and logs
- `GET /api/jobs` - List all jobs
- `GET /api/health` - Health check
- `WS /ws/{job_id}` - Real-time job updates

## 🎯 Performance Testing

Use the sample URLs in the interface to test with known documents:
- **Docling Paper**: https://arxiv.org/pdf/2408.09869
- **Research Paper**: https://arxiv.org/pdf/2206.01062

Monitor processing times and throughput to understand Docling's capabilities for your specific use cases.