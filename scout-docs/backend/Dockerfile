FROM python:3.11-slim

# Install system dependencies including potential CUDA support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libblas-dev \
    liblapack-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment variables for both GPU and CPU modes
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMP_NUM_THREADS=8
ENV MKL_NUM_THREADS=8

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch with CUDA support (falls back to CPU)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 || \
    pip install --no-cache-dir torch torchvision torchaudio

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage && chmod 755 /app/storage

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import torch; print('✅ PyTorch available, GPU:', torch.cuda.is_available()); exit(0)"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]