"""
PyTorch configuration for CPU-optimized performance.
Fixes pin_memory warnings and optimizes for CPU-only processing.
"""
import os
import warnings
import torch

def configure_torch_for_cpu():
    """Configure PyTorch for optimal CPU performance and suppress GPU-related warnings."""
    
    # Suppress pin_memory warnings when no GPU is available
    if not torch.cuda.is_available():
        # Set environment variable to disable pin_memory globally
        os.environ['PYTORCH_PIN_MEMORY'] = 'False'
        
        # Filter out the specific pin_memory warnings
        warnings.filterwarnings(
            "ignore", 
            message=".*pin_memory.*no accelerator is found.*",
            category=UserWarning,
            module="torch.utils.data.dataloader"
        )
    
    # Only configure threading if not already set
    if torch.get_num_threads() == 1:  # Default is 1, so we haven't configured yet
        # Optimize CPU threading for document processing
        cpu_count = os.cpu_count() or 4
        torch.set_num_threads(min(cpu_count, 8))  # Cap at 8 to avoid overhead
        torch.set_num_interop_threads(2)  # Low interop threads for single-threaded workload
    
    # Enable optimized CPU kernels
    torch.backends.mkl.enabled = True if hasattr(torch.backends, 'mkl') else False
    torch.backends.mkldnn.enabled = True if hasattr(torch.backends, 'mkldnn') else False
    
    print(f"🚀 PyTorch configured for CPU: {os.cpu_count()} cores, {torch.get_num_threads()} threads")

def configure_torch_for_gpu():
    """Configure PyTorch for optimal GPU performance."""
    
    if not torch.cuda.is_available():
        print("⚠️ Warning: GPU requested but CUDA is not available, falling back to CPU")
        configure_torch_for_cpu()
        return False
    
    # Configure for GPU usage
    device_count = torch.cuda.device_count()
    device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown GPU"
    
    # Enable GPU optimizations (these can be set multiple times safely)
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True  # Optimize for consistent input sizes
    
    # Enable pin_memory for faster GPU transfers
    os.environ['PYTORCH_PIN_MEMORY'] = 'True'
    
    print(f"🚀 PyTorch configured for GPU: {device_name} ({device_count} device{'s' if device_count != 1 else ''})")
    return True

def configure_torch_startup():
    """One-time PyTorch configuration at application startup."""
    # Do basic CPU configuration at startup
    configure_torch_for_cpu()
    
    # Check GPU availability and configure if present
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown GPU"
        print(f"🖥️  GPU Available: {device_name} ({device_count} device{'s' if device_count != 1 else ''})")
        # Set GPU backend optimizations (safe to call multiple times)
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = True
    else:
        print("🖥️  GPU: Not available")

def set_compute_mode_for_request(compute_mode: str):
    """Set compute mode for a specific request (without changing thread settings)."""
    if compute_mode.lower() == "gpu" and torch.cuda.is_available():
        # Use GPU - just set the device preference
        torch.cuda.set_device(0)
        return "gpu", torch.cuda.get_device_name(0)
    else:
        # Use CPU or fallback to CPU
        actual_mode = "cpu" if compute_mode.lower() == "cpu" else "cpu_fallback"
        return actual_mode, f"{os.cpu_count()} CPU cores"

def get_compute_info():
    """Get information about the compute environment (CPU vs GPU)."""
    cuda_available = torch.cuda.is_available()
    
    if cuda_available:
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown GPU"
        compute_type = "GPU"
        compute_details = f"{device_name} ({device_count} device{'s' if device_count != 1 else ''})"
    else:
        cpu_count = os.cpu_count() or 4
        compute_type = "CPU"
        compute_details = f"{cpu_count} cores, {torch.get_num_threads()} threads"
    
    return {
        "compute_type": compute_type,
        "compute_details": compute_details,
        "cuda_available": cuda_available,
        "device_count": device_count if cuda_available else 0
    }

# Configuration is now handled explicitly at startup