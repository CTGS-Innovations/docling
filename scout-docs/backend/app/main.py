import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.docling_service import DoclingProcessor, ProcessingResult
from app.logger import setup_logger, LogCapture
from app.websocket_manager import WebSocketManager

# Setup logging
logger = setup_logger(__name__)
app = FastAPI(title="Docling Demo API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
websocket_manager = WebSocketManager()
docling_processor = DoclingProcessor()
active_jobs: Dict[str, Dict] = {}

class ProcessingRequest(BaseModel):
    source: str  # URL or file reference
    pipeline: str = "standard"  # standard, vlm
    output_format: str = "markdown"  # markdown, html, json

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    logs: List[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    result: Optional[ProcessingResult] = None

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket_manager.connect(websocket, job_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        websocket_manager.disconnect(job_id)

@app.post("/api/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    pipeline: str = Form("standard"),
    output_format: str = Form("markdown")
):
    """Upload and process a file"""
    job_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    logger.info(f"🚀 Starting job {job_id}: {file.filename}")
    
    # Initialize job tracking
    active_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "start_time": timestamp,
        "end_time": None,
        "duration": None,
        "result": None,
        "filename": file.filename,
        "pipeline": pipeline,
        "output_format": output_format
    }
    
    # Save uploaded file
    storage_path = Path("storage") / job_id
    storage_path.mkdir(exist_ok=True)
    file_path = storage_path / file.filename
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            
        logger.info(f"📁 File saved: {file_path} ({len(content)} bytes)")
        
        # Start processing (in background)
        import asyncio
        asyncio.create_task(process_document_async(job_id, str(file_path), pipeline, output_format))
        
        return {"job_id": job_id, "status": "pending", "message": "File uploaded, processing started"}
        
    except Exception as e:
        logger.error(f"❌ Upload failed for job {job_id}: {e}")
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["logs"].append(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-url", response_model=dict)
async def process_url(request: ProcessingRequest):
    """Process a document from URL"""
    job_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    logger.info(f"🌐 Starting URL job {job_id}: {request.source}")
    
    # Initialize job tracking
    active_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "start_time": timestamp,
        "end_time": None,
        "duration": None,
        "result": None,
        "source": request.source,
        "pipeline": request.pipeline,
        "output_format": request.output_format
    }
    
    # Start processing (in background)
    import asyncio
    asyncio.create_task(process_document_async(job_id, request.source, request.pipeline, request.output_format))
    
    return {"job_id": job_id, "status": "pending", "message": "URL processing started"}

async def process_document_async(job_id: str, source: str, pipeline: str, output_format: str):
    """Async document processing with detailed logging and timing"""
    job = active_jobs[job_id]
    log_capture = LogCapture()
    
    try:
        # Update job status
        job["status"] = "processing"
        job["progress"] = 10
        await websocket_manager.send_update(job_id, job)
        
        # Start processing with timing
        start_time = time.perf_counter()
        logger.info(f"⚡ Processing started: {source}")
        log_capture.add_log(f"⚡ Processing started: {source}")
        
        # Phase 1: Document loading
        phase_start = time.perf_counter()
        job["progress"] = 20
        job["logs"] = log_capture.logs.copy()
        await websocket_manager.send_update(job_id, job)
        
        result = await docling_processor.process_document(
            source=source,
            pipeline=pipeline,
            output_format=output_format,
            log_capture=log_capture
        )
        
        # Calculate total processing time
        total_time = time.perf_counter() - start_time
        
        # Update final job status
        job["status"] = "completed"
        job["progress"] = 100
        job["end_time"] = datetime.now()
        job["duration"] = total_time
        job["result"] = result.dict()
        job["logs"] = log_capture.logs.copy()
        
        logger.info(f"✅ Job {job_id} completed in {total_time:.2f}s")
        log_capture.add_log(f"✅ Processing completed in {total_time:.2f}s")
        
        await websocket_manager.send_update(job_id, job)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Job {job_id} failed: {error_msg}")
        log_capture.add_log(f"❌ Error: {error_msg}")
        
        job["status"] = "failed"
        job["end_time"] = datetime.now()
        job["duration"] = time.perf_counter() - start_time if 'start_time' in locals() else 0
        job["logs"] = log_capture.logs.copy()
        
        await websocket_manager.send_update(job_id, job)

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status and logs"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**active_jobs[job_id])

@app.get("/api/jobs", response_model=List[JobStatus])
async def get_all_jobs():
    """Get all jobs"""
    return [JobStatus(**job) for job in active_jobs.values()]

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_jobs": len(active_jobs),
        "docling_available": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)