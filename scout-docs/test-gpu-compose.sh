#!/bin/bash

echo "🐳 Testing GPU Access with Docker Compose..."
echo "============================================="
echo ""

# Check if docker-compose/docker compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Neither docker-compose nor 'docker compose' command found"
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

echo "Test 1: Build and Check Backend Container GPU Access"
echo "---------------------------------------------------"

# Build the backend service if not already built
echo "Building backend container..."
$COMPOSE_CMD build backend

if [ $? -eq 0 ]; then
    echo "✅ Backend container built successfully"
else
    echo "❌ Backend container build failed"
    exit 1
fi

echo ""
echo "Test 2: Run GPU Detection Test in Backend Container"
echo "---------------------------------------------------"

# Run a one-off container to test GPU detection
$COMPOSE_CMD run --rm backend python -c "
import torch
print('🔍 GPU Detection Test Results:')
print(f'   PyTorch version: {torch.__version__}')
print(f'   CUDA available: {torch.cuda.is_available()}')
print(f'   CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')

if torch.cuda.is_available():
    print(f'   GPU count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'   GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'   GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB')
else:
    print('   No GPU detected in container')
"

if [ $? -eq 0 ]; then
    echo "✅ GPU detection test completed"
else
    echo "❌ GPU detection test failed"
fi

echo ""
echo "Test 3: Test VLM Model Configuration"
echo "------------------------------------"

$COMPOSE_CMD run --rm backend python -c "
try:
    from docling.datamodel import vlm_model_specs
    from docling.datamodel.accelerator_options import AcceleratorDevice
    
    print('🤖 VLM Model Configuration Test:')
    model = vlm_model_specs.SMOLDOCLING_TRANSFORMERS
    print(f'   Model ID: {model.repo_id}')
    print(f'   Framework: {model.inference_framework}')
    print(f'   Supported devices: {model.supported_devices}')
    print(f'   CUDA supported: {AcceleratorDevice.CUDA in model.supported_devices}')
    print('✅ VLM model configuration is correct')
except Exception as e:
    print(f'❌ VLM model test failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ VLM model configuration test passed"
else
    echo "❌ VLM model configuration test failed"
fi

echo ""
echo "Test 4: Test Docker Compose GPU Service"
echo "---------------------------------------"

# Check if the backend service can start with GPU access
echo "Starting backend service..."
$COMPOSE_CMD up -d backend redis

# Wait a moment for service to start
sleep 10

# Check if service is running
if $COMPOSE_CMD ps backend | grep -q "Up"; then
    echo "✅ Backend service started successfully"
    
    # Test the health check endpoint
    echo "Testing health endpoint..."
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend API is responding"
        
        # Test system info endpoint for GPU info
        echo "Checking system info..."
        curl -s http://localhost:8000/api/system-info | python -m json.tool
        
    else
        echo "⚠️ Backend API not responding yet (may still be starting up)"
    fi
    
    echo ""
    echo "Checking service logs..."
    $COMPOSE_CMD logs --tail=20 backend
    
else
    echo "❌ Backend service failed to start"
    echo "Service logs:"
    $COMPOSE_CMD logs --tail=50 backend
fi

echo ""
echo "Test 5: Docker Compose GPU Configuration Check"
echo "----------------------------------------------"

echo "Checking docker-compose.yml GPU configuration..."
if grep -q "driver: nvidia" docker-compose.yml; then
    echo "✅ NVIDIA driver configuration found"
fi

if grep -q "capabilities: \[gpu\]" docker-compose.yml; then
    echo "✅ GPU capabilities configuration found"
fi

if grep -q "NVIDIA_VISIBLE_DEVICES" docker-compose.yml; then
    echo "✅ NVIDIA_VISIBLE_DEVICES environment variable found"
fi

echo ""
echo "🎯 Docker Compose GPU Test Complete!"
echo "======================================"

echo ""
echo "💡 Next Steps:"
echo "1. If all tests pass, your GPU setup is working correctly"
echo "2. You can now test VLM processing with: compute_mode='gpu' and pipeline='vlm'"
echo "3. Stop the test services: $COMPOSE_CMD down"
echo ""
echo "🚀 To test the full application:"
echo "   $COMPOSE_CMD up -d"
echo "   Open http://localhost:3000 and try processing a PDF with GPU+VLM"