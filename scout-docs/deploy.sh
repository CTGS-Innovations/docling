#!/bin/bash

echo "🚀 Deploying Docling Processing Center..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for GPU support
GPU_AVAILABLE=false
if command -v nvidia-smi >/dev/null 2>&1; then
    if nvidia-smi > /dev/null 2>&1; then
        GPU_AVAILABLE=true
        echo "🖥️  GPU detected:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1
    fi
fi

if [ "$GPU_AVAILABLE" = true ]; then
    echo "✅ GPU support enabled - both CPU and GPU processing available"
else  
    echo "ℹ️  No GPU detected - CPU processing only"
    echo "💡 To enable GPU: Install NVIDIA drivers and NVIDIA Container Toolkit"
fi

echo ""
echo "🔨 Building and starting containers..."

# Build and start services
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🔍 Checking service status..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend may not be ready yet"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"  
else
    echo "⚠️  Frontend may not be ready yet"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📱 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000" 
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "🖥️  Processing modes available:"
if [ "$GPU_AVAILABLE" = true ]; then
    echo "   CPU Processing:  Fast, reliable, works everywhere"
    echo "   GPU Processing:  Faster for complex documents (if available)"
else
    echo "   CPU Processing:  Fast, reliable processing"
fi
echo ""
echo "📊 Check system capabilities: http://localhost:8000/api/system-info"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"