#!/usr/bin/env python3
"""
vLLM Server Manager
Manages persistent vLLM server for optimal docling performance
"""

import subprocess
import time
import requests
import json
from pathlib import Path
import psutil
import signal
import os

class VLLMServerManager:
    def __init__(self, port=8000, model='ds4sd/SmolDocling-256M-preview'):  # Docling's actual smoldocling model
        self.port = port
        self.model = model
        self.server_process = None
        self.base_url = f"http://localhost:{port}"
        
    def start_server(self):
        """Start persistent vLLM server"""
        print(f"🚀 Starting vLLM server on port {self.port}...")
        print(f"📦 Model: {self.model}")
        
        # vLLM server command - match docling's default configuration
        cmd = [
            'vllm', 'serve',
            self.model,
            '--port', str(self.port),
            '--gpu-memory-utilization', '0.8',  # Use 80% of GPU memory
            '--max-model-len', '1024',  # Match model's actual max length
            '--tensor-parallel-size', '1',  # Single GPU
            '--disable-log-stats',
            '--host', '0.0.0.0'
        ]
        
        # Set environment variable to allow model configuration
        env = os.environ.copy()
        env['VLLM_ALLOW_LONG_MAX_MODEL_LEN'] = '1'
        
        print(f"💻 Command: {' '.join(cmd)}")
        
        try:
            # Start vLLM server in background
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            print(f"🔄 Server starting (PID: {self.server_process.pid})...")
            
            # Wait for server to be ready
            return self._wait_for_server()
            
        except Exception as e:
            print(f"❌ Failed to start vLLM server: {e}")
            return False
    
    def _wait_for_server(self, timeout=180):
        """Wait for vLLM server to be ready"""
        print("🔄 Waiting for vLLM server to initialize...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if process is still running
                if self.server_process and self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    print(f"❌ vLLM server process died:")
                    print(f"STDOUT: {stdout[-500:]}")
                    print(f"STDERR: {stderr[-500:]}")
                    return False
                
                # Try to connect to server
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ vLLM server ready in {time.time() - start_time:.1f}s")
                    print(f"🔗 Server URL: {self.base_url}")
                    return True
                    
            except requests.exceptions.RequestException:
                pass  # Server not ready yet
            
            print(".", end="", flush=True)
            time.sleep(2)
        
        print(f"\\n❌ vLLM server failed to start within {timeout}s")
        return False
    
    def check_server_status(self):
        """Check if vLLM server is running and healthy"""
        try:
            if not self.server_process or self.server_process.poll() is not None:
                return False
                
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_server_stats(self):
        """Get vLLM server performance statistics"""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def stop_server(self):
        """Gracefully stop vLLM server"""
        print("🛑 Stopping vLLM server...")
        
        if self.server_process:
            try:
                # Try graceful shutdown first
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=10)
                    print("✅ vLLM server stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠️  Force killing vLLM server...")
                    self.server_process.kill()
                    self.server_process.wait()
                    print("✅ vLLM server force stopped")
                    
            except Exception as e:
                print(f"⚠️  Error stopping server: {e}")
            
            self.server_process = None
    
    def get_gpu_memory_usage(self):
        """Get current GPU memory usage"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                used, total = result.stdout.strip().split(', ')
                return {'used': int(used), 'total': int(total), 'percent': int(used)/int(total)*100}
        except:
            pass
        return None
    
    def __enter__(self):
        """Context manager entry"""
        if self.start_server():
            return self
        else:
            raise RuntimeError("Failed to start vLLM server")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_server()

def main():
    """Test vLLM server management"""
    print("🧪 Testing vLLM Server Manager")
    
    # Use docling's actual smoldocling model
    candidate_models = [
        'ds4sd/SmolDocling-256M-preview',     # Docling's actual smoldocling model 
    ]
    
    print(f"📋 Testing candidate models for docling compatibility:")
    for model in candidate_models:
        print(f"   - {model}")
    
    model_to_use = candidate_models[0]  # Start with SmolVLM
    
    try:
        with VLLMServerManager(port=8000, model=model_to_use) as server:
            print("✅ vLLM server context manager working!")
            
            # Test server health
            if server.check_server_status():
                print("✅ Server health check passed")
                
                # Show GPU usage
                gpu_info = server.get_gpu_memory_usage()
                if gpu_info:
                    print(f"🔥 GPU Memory: {gpu_info['used']}MB / {gpu_info['total']}MB ({gpu_info['percent']:.1f}%)")
                
                # Test API endpoint
                try:
                    response = requests.get(f"{server.base_url}/v1/models", timeout=10)
                    if response.status_code == 200:
                        models = response.json()
                        print(f"📦 Server models: {[m['id'] for m in models['data']]}")
                except Exception as e:
                    print(f"⚠️  API test failed: {e}")
                
                print("⏳ Server running... (press Ctrl+C to stop)")
                time.sleep(5)  # Keep running for 5 seconds
                
            else:
                print("❌ Server health check failed")
                
    except KeyboardInterrupt:
        print("\\n🛑 User interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()