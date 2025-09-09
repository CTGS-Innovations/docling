# Docling Docker Demo Application

## Project Overview
A containerized web application to explore and demonstrate Docling's document processing capabilities with a clean, professional UI and multiple storage backend options.

## Architecture Design

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend UI   │◄──►│  Backend API    │◄──►│  Storage Layer  │
│   (React/Vue)   │    │  (FastAPI)      │    │  (Multi-backend)│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Web Server    │    │  Docling Core   │    │  - Local FS     │
│   (Nginx)       │    │  Processing     │    │  - Cloudflare R2│
│                 │    │                 │    │  - Google Cloud │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Architecture
1. **Frontend Container**: React/Vue.js with professional UI components
2. **Backend API Container**: FastAPI with Docling integration
3. **Storage Proxy Container**: Handles multiple storage backends
4. **Redis Container**: Caching and session management
5. **Database Container**: PostgreSQL for metadata and job tracking

## Features Specification

### Core Functionality
- **Document Upload**: Support file uploads and URL processing
- **Format Support**: PDF, DOCX, HTML, images, audio files
- **Processing Options**: 
  - Standard pipeline vs VLM pipeline
  - OCR options (EasyOCR, Tesseract, RapidOCR)
  - Output formats (Markdown, HTML, JSON)
- **Real-time Processing**: WebSocket updates for long-running jobs
- **Storage Management**: Configurable storage backends

### UI Components
- **Upload Interface**: Drag-and-drop with URL input
- **Processing Dashboard**: Job queue, progress tracking
- **Results Viewer**: Rendered output with download options
- **Configuration Panel**: Pipeline settings and storage options
- **History Browser**: Previous processing jobs and results

### Storage Integration
- **Local Storage**: File system for development/testing
- **Cloudflare R2**: S3-compatible object storage
- **Google Cloud Storage**: Enterprise cloud storage
- **Metadata Database**: PostgreSQL for searchable document metadata

## Technical Stack

### Frontend
- **Framework**: React with TypeScript
- **UI Library**: Tailwind CSS + Headless UI
- **State Management**: Zustand or Redux Toolkit
- **File Handling**: React Dropzone
- **WebSocket**: Socket.io-client

### Backend
- **API Framework**: FastAPI with Python 3.11
- **Document Processing**: Docling SDK
- **Task Queue**: Celery with Redis
- **Database ORM**: SQLAlchemy
- **Storage SDK**: boto3 (S3-compatible), google-cloud-storage

### Infrastructure
- **Containerization**: Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Monitoring**: Prometheus + Grafana (optional)

## Development Phases

### Phase 1: Core Setup
- Docker Compose configuration
- Basic FastAPI backend with Docling integration
- Simple React frontend
- Local file storage

### Phase 2: Advanced Processing
- Multiple pipeline options
- WebSocket real-time updates
- Job queue with Celery
- Processing history and metadata

### Phase 3: Cloud Integration
- Cloudflare R2 storage backend
- Google Cloud Storage backend
- Environment-based configuration
- Production deployment setup

### Phase 4: UI Polish & Features
- Professional UI design
- Advanced filtering and search
- Batch processing capabilities
- Export and sharing features

## Environment Configuration

### Development
```yaml
STORAGE_BACKEND=local
DOCLING_PIPELINE=standard
DEBUG=true
```

### Production
```yaml
STORAGE_BACKEND=cloudflare_r2  # or google_cloud
CLOUDFLARE_R2_ACCOUNT_ID=xxx
CLOUDFLARE_R2_ACCESS_KEY_ID=xxx
CLOUDFLARE_R2_SECRET_ACCESS_KEY=xxx
CLOUDFLARE_R2_BUCKET=docling-demo
```

## File Structure
```
scout-docs/
├── docker-compose.yml
├── .env.example
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── docling_service.py
│   │   └── storage/
├── nginx/
│   └── nginx.conf
├── database/
│   └── init.sql
└── docs/
    ├── API.md
    └── DEPLOYMENT.md
```

## Success Metrics
- Successfully process various document formats
- Demonstrate storage flexibility (local → cloud)
- Clean, responsive UI that showcases Docling capabilities
- Scalable architecture suitable for production deployment
- Clear documentation for setup and usage