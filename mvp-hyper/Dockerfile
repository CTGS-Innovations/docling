FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    pymupdf \
    pyyaml \
    psutil \
    openpyxl \
    python-docx \
    python-pptx \
    beautifulsoup4

# Copy application files
COPY mvp-hyper-core.py .
COPY config_loader.py .
COPY config.yaml .
COPY clean.sh .

# Make scripts executable
RUN chmod +x mvp-hyper-core.py clean.sh

# Create output directory
RUN mkdir -p /app/output

# Set resource limits in environment
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Default command
CMD ["python", "mvp-hyper-core.py"]