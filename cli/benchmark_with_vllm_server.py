#!/usr/bin/env python3
"""
Docling Performance Benchmark with Persistent vLLM Server
Uses external vLLM server for optimal GPU utilization and performance
"""

import os
import sys
from pathlib import Path
import subprocess
import time
import json

# Add the current directory to Python path to import existing benchmark
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from performance_benchmark import DoclingPerformanceBenchmark
from vllm_server_manager import VLLMServerManager

class VLLMServerBenchmark(DoclingPerformanceBenchmark):
    """Enhanced benchmark that uses persistent vLLM server"""
    
    def __init__(self, data_dir, output_dir=None, vllm_port=8000):
        # Set default output_dir if None
        if output_dir is None:
            output_dir = Path(__file__).parent / 'output'
        
        super().__init__(data_dir, output_dir)
        self.vllm_port = vllm_port
        self.vllm_manager = None
        self.server_stats = []
        
    def _prewarm_gpu(self):
        """Override: GPU warming handled by persistent vLLM server startup"""
        self.logger.info("🔥 GPU warming handled by persistent vLLM server startup")
        
    def setup_vllm_server(self):
        """Start persistent vLLM server for the entire benchmark"""
        self.logger.info("🚀 Setting up persistent vLLM server...")
        
        # Use docling's actual smoldocling model for exact compatibility
        vision_model = 'ds4sd/SmolDocling-256M-preview'  # Exact same model as docling's smoldocling
        
        self.vllm_manager = VLLMServerManager(port=self.vllm_port, model=vision_model)
        
        if self.vllm_manager.start_server():
            self.logger.info("✅ vLLM server ready - models loaded and persistent!")
            
            # Log GPU memory usage after model loading
            gpu_info = self.vllm_manager.get_gpu_memory_usage()
            if gpu_info:
                self.logger.info(f"🔥 GPU Memory: {gpu_info['used']}MB/{gpu_info['total']}MB ({gpu_info['percent']:.1f}%)")
                self.logger.info("🎯 Target: 80% utilization maintained throughout benchmark")
            
            return True
        else:
            self.logger.error("❌ Failed to start vLLM server")
            return False
    
    def shutdown_vllm_server(self):
        """Shutdown persistent vLLM server"""
        if self.vllm_manager:
            self.logger.info("🛑 Shutting down vLLM server...")
            self.vllm_manager.stop_server()
            self.vllm_manager = None
    
    def optimize_for_80_percent_utilization(self, doc_classification, total_files):
        """Override: Enhanced config for vLLM server usage"""
        config = super().optimize_for_80_percent_utilization(doc_classification, total_files)
        
        # Update VLM configuration to use external server
        config.update({
            'vlm_server_url': f'http://localhost:{self.vllm_port}',
            'use_external_vlm': True,
            'vlm_model': 'server',  # Indicate using external server
            'page_batch_size': 10,  # Larger batches with persistent server
        })
        
        self.logger.info("🔗 Configured to use persistent vLLM server")
        return config
    
    def _run_gpu_hot_processing(self, files, pipeline_name, config, formats):
        """Override: Enhanced monitoring with persistent vLLM server"""
        
        self.logger.info(f"🔥 GPU-Hot Processing with persistent vLLM: {len(files)} files")
        self.logger.info(f"   Server URL: http://localhost:{self.vllm_port}")
        
        # Monitor server health before processing
        if self.vllm_manager and not self.vllm_manager.check_server_status():
            self.logger.warning("⚠️  vLLM server not healthy, attempting restart...")
            if not self.setup_vllm_server():
                self.logger.error("❌ Failed to restart vLLM server, falling back to standard pipeline")
                config['pipeline'] = 'standard'
        
        # Set environment variables for docling to use external vLLM server
        env = os.environ.copy()
        if config.get('use_external_vlm'):
            env['DOCLING_VLM_SERVER_URL'] = config['vlm_server_url']
            env['DOCLING_USE_EXTERNAL_VLM'] = '1'
        
        # Track server stats during processing
        start_gpu_info = self.vllm_manager.get_gpu_memory_usage() if self.vllm_manager else None
        start_time = time.time()
        
        # Call parent implementation with enhanced environment
        result = self._run_chunk_processing_with_env(files, pipeline_name, config, formats, env)
        
        # Log server performance during processing
        end_time = time.time()
        end_gpu_info = self.vllm_manager.get_gpu_memory_usage() if self.vllm_manager else None
        
        if start_gpu_info and end_gpu_info:
            memory_stable = abs(start_gpu_info['used'] - end_gpu_info['used']) < 100  # Less than 100MB change
            self.logger.info(f"🔥 GPU Memory: {end_gpu_info['used']}MB ({end_gpu_info['percent']:.1f}%) - {'Stable' if memory_stable else 'Variable'}")
            
            if memory_stable:
                self.logger.info("✅ GPU-hot processing achieved - models stayed loaded!")
            else:
                self.logger.warning("⚠️  GPU memory changed - models may have reloaded")
        
        return result
    
    def _run_chunk_processing_with_env(self, files, pipeline_name, config, formats, env):
        """Run chunk processing with custom environment variables"""
        # This is a modified version of the parent's _run_gpu_hot_processing logic
        # but with custom environment variables for vLLM server usage
        
        pipeline_output_dir = self.output_dir / f"{pipeline_name}_persistent_vllm"
        pipeline_output_dir.mkdir(parents=True, exist_ok=True)
        
        successful_files = []
        failed_files = []
        total_processing_time = 0
        
        # Process in chunks
        chunk_size = config.get('page_batch_size', 20)
        
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i+chunk_size]
            chunk_start = time.time()
            
            self.logger.info(f"   🔥 Processing chunk {i//chunk_size + 1}/{(len(files)-1)//chunk_size + 1}: {len(chunk)} files")
            
            # Build command for this chunk  
            cmd = [
                'docling',
                '--to', 'md',
                '--output', str(pipeline_output_dir),
                '--device', config['device'],
                '--num-threads', str(config['num_threads']),
                '--page-batch-size', str(config['page_batch_size']),
                '--pipeline', config['pipeline'],
                '--pdf-backend', config['pdf_backend'],
                # No need to specify VLM model - using server
            ]
            
            # Add pipeline-specific options
            if config['pipeline'] == 'vlm' and config.get('use_external_vlm'):
                # Let docling discover the external vLLM server via env vars
                pass  
            elif config['pipeline'] == 'vlm':
                cmd.extend(['--vlm-model', config['vlm_model']])
            elif config['pipeline'] == 'asr':
                cmd.extend(['--asr-model', config['asr_model']])
            
            # Add chunk files
            cmd.extend([str(f) for f in chunk])
            
            # Execute chunk with enhanced environment
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=env)
                chunk_time = time.time() - chunk_start
                total_processing_time += chunk_time
                
                if result.returncode == 0:
                    successful_files.extend(chunk)
                    throughput = len(chunk) / chunk_time * 60
                    
                    self.logger.info(f"      ✅ Chunk completed: {len(chunk)} files in {chunk_time:.1f}s ({throughput:.1f} files/min)")
                    
                    # Monitor vLLM server during processing
                    if self.vllm_manager:
                        gpu_info = self.vllm_manager.get_gpu_memory_usage()
                        if gpu_info:
                            self.logger.info(f"      🔥 vLLM Server GPU: {gpu_info['used']}MB ({gpu_info['percent']:.1f}%) - Persistent")
                else:
                    failed_files.extend(chunk)
                    self.logger.warning(f"      ❌ Chunk failed: {result.stderr[:200] if result.stderr else 'Unknown error'}")
                    
                    # Individual retry for failed chunks
                    if len(chunk) > 1:
                        self.logger.info(f"      🔄 Retrying chunk files individually...")
                        for file_path in chunk:
                            individual_result = self._process_single_file_with_env(file_path, pipeline_output_dir, config, env)
                            if individual_result['success']:
                                if file_path in failed_files:
                                    failed_files.remove(file_path)
                                if file_path not in successful_files:
                                    successful_files.append(file_path)
                                    
            except subprocess.TimeoutExpired:
                failed_files.extend(chunk)
                self.logger.error(f"      ❌ Chunk timeout after 30 minutes")
                
        # Calculate results
        success_rate = len(successful_files) / len(files) * 100 if files else 0
        throughput = len(successful_files) / total_processing_time * 60 if total_processing_time > 0 else 0
        
        return {
            'successful_files': successful_files,
            'failed_files': failed_files, 
            'total_time': total_processing_time,
            'throughput_files_per_minute': throughput,
            'success_rate': success_rate,
            'pipeline_name': pipeline_name,
            'server_persistent': True
        }
    
    def _process_single_file_with_env(self, file_path, output_dir, config, env):
        """Process single file with custom environment"""
        cmd = [
            'docling', str(file_path),
            '--to', 'md',
            '--output', str(output_dir),
            '--device', config['device'],
            '--num-threads', '1',
            '--page-batch-size', '1',
            '--pipeline', config['pipeline'],
            '--pdf-backend', config['pdf_backend']
        ]
        
        if config['pipeline'] == 'vlm' and not config.get('use_external_vlm'):
            cmd.extend(['--vlm-model', config['vlm_model']])
        elif config['pipeline'] == 'asr':
            cmd.extend(['--asr-model', config['asr_model']])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'timeout'}
    
    def run_comprehensive_benchmark(self):
        """Override: Run benchmark with persistent vLLM server"""
        
        self.logger.info("🚀 Starting Performance Benchmark with Persistent vLLM Server")
        
        # Start vLLM server first
        if not self.setup_vllm_server():
            self.logger.error("❌ Failed to setup vLLM server, falling back to standard benchmark")
            return super().run_comprehensive_benchmark()
        
        try:
            # Run the standard benchmark logic with vLLM server active
            results = super().run_comprehensive_benchmark()
            
            # Add vLLM server statistics to results
            if self.vllm_manager:
                gpu_info = self.vllm_manager.get_gpu_memory_usage()
                if gpu_info:
                    results['vllm_server_stats'] = {
                        'gpu_memory_used': gpu_info['used'],
                        'gpu_memory_total': gpu_info['total'],
                        'gpu_utilization_percent': gpu_info['percent'],
                        'server_persistent': True
                    }
            
            return results
            
        finally:
            # Always shutdown vLLM server
            self.shutdown_vllm_server()

def main():
    """Run benchmark with persistent vLLM server"""
    
    cli_dir = Path(__file__).parent
    data_dir = cli_dir / 'data'
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        sys.exit(1)
    
    print("🚀 DOCLING PERFORMANCE BENCHMARK WITH PERSISTENT vLLM SERVER")
    print("=" * 70)
    
    try:
        benchmark = VLLMServerBenchmark(data_dir)
        results = benchmark.run_comprehensive_benchmark()
        
        print("\\n✅ Benchmark Complete!")
        print(f"📄 Results: {benchmark.output_dir}")
        
        if 'vllm_server_stats' in results:
            stats = results['vllm_server_stats']
            print(f"🔥 vLLM Server GPU: {stats['gpu_memory_used']}MB ({stats['gpu_utilization_percent']:.1f}%)")
        
    except KeyboardInterrupt:
        print("\\n🛑 Benchmark interrupted by user")
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()