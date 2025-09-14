#!/usr/bin/env python3
"""
Distributed Docker Benchmark
============================
Multi-container performance benchmark with warm-up and coordinated start.
Each container gets 1 CPU core and 1GB RAM for realistic scaling test.
"""

import time
import subprocess
import json
import threading
from pathlib import Path
from typing import Dict, List
import argparse
import sys
import yaml
from datetime import datetime


class DistributedBenchmark:
    """Orchestrates multiple Docker containers for distributed processing."""
    
    def __init__(self, num_containers: int = 4, ram_per_container: str = "1g", duration: int = 30):
        self.num_containers = num_containers
        self.ram_per_container = ram_per_container
        self.duration = duration
        self.results = []
        self.containers = []
        
    def prepare_containers(self) -> bool:
        """Build Docker image and prepare containers."""
        
        print(f"🔨 BUILDING DOCKER IMAGE")
        print("=" * 50)
        
        # Build the image
        build_cmd = ["docker", "build", "-t", "mvp-hyper:benchmark", "."]
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
        
        print("✅ Docker image built successfully")
        return True
    
    def warm_up_containers(self) -> bool:
        """Pre-warm all containers to avoid startup overhead."""
        
        print(f"\n🔥 WARMING UP {self.num_containers} CONTAINERS")
        print("=" * 50)
        
        # Create warm-up config (process just 1 file for speed)
        warmup_config = self._create_warmup_config()
        
        warmup_threads = []
        warmup_results = []
        
        for i in range(self.num_containers):
            container_name = f"mvp-hyper-benchmark-{i}"
            cpu_core = str(i)  # Pin to specific CPU core
            
            print(f"🚀 Warming up container {i+1}/{self.num_containers} (CPU {cpu_core})")
            
            thread = threading.Thread(
                target=self._warm_up_single_container,
                args=(container_name, cpu_core, warmup_config, warmup_results, i)
            )
            warmup_threads.append(thread)
            thread.start()
        
        # Wait for all warm-ups to complete
        for thread in warmup_threads:
            thread.join()
        
        # Check if all containers warmed up successfully
        if len(warmup_results) == self.num_containers:
            print(f"✅ All {self.num_containers} containers warmed up successfully!")
            print(f"⏱️  Average warm-up time: {sum(warmup_results)/len(warmup_results):.2f}s")
            return True
        else:
            print(f"❌ Only {len(warmup_results)}/{self.num_containers} containers warmed up")
            return False
    
    def _warm_up_single_container(self, container_name: str, cpu_core: str, 
                                  config: Dict, results: List, container_id: int):
        """Warm up a single container."""
        
        start_time = time.perf_counter()
        
        try:
            # Save warm-up config
            config_file = f"warmup_config_{container_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f)
            
            # Run warm-up
            cmd = [
                "docker", "run", "--rm",
                "--cpus=1.0",
                f"--memory={self.ram_per_container}",
                f"--cpuset-cpus={cpu_core}",  # Pin to specific CPU core
                "-v", f"{Path.cwd()}/{config_file}:/app/config.yaml",
                "-v", f"{Path.home()}/projects/docling/cli/data:/app/data:ro",
                "-v", f"{Path.home()}/projects/docling/cli/data_complex:/app/data_complex:ro",
                "-v", f"{Path.home()}/projects/docling/cli/data_osha:/app/data_osha:ro",
                "mvp-hyper:benchmark",
                "python", "mvp-hyper-core.py", "--config", "/app/config.yaml"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                warmup_time = time.perf_counter() - start_time
                results.append(warmup_time)
                print(f"  ✅ Container {container_id} warmed up in {warmup_time:.2f}s")
            else:
                print(f"  ❌ Container {container_id} warm-up failed")
                print(f"  🔍 STDERR: {result.stderr[:200]}")
                print(f"  🔍 STDOUT: {result.stdout[:200]}")
                
        except Exception as e:
            print(f"  ❌ Container {container_id} warm-up error: {str(e)[:50]}")
        finally:
            # Cleanup config file
            try:
                Path(f"warmup_config_{container_id}.yaml").unlink()
            except:
                pass
    
    def run_distributed_benchmark(self) -> Dict:
        """Run the coordinated distributed benchmark."""
        
        print(f"\n🏁 DISTRIBUTED BENCHMARK START!")
        print("=" * 50)
        print(f"📊 Configuration:")
        print(f"  • Containers: {self.num_containers}")
        print(f"  • CPU per container: 1 core (pinned)")
        print(f"  • RAM per container: {self.ram_per_container}")
        print(f"  • Total resources: {self.num_containers} cores, {self.num_containers}GB RAM")
        print("")
        
        # Create benchmark configs
        benchmark_configs = self._create_benchmark_configs()
        
        # Start all containers simultaneously
        print("🚀 Starting all containers...")
        
        benchmark_threads = []
        benchmark_results = []
        
        # Coordinated start
        start_signal = time.time() + 2  # Give 2 seconds for all threads to be ready
        
        for i in range(self.num_containers):
            container_name = f"mvp-hyper-benchmark-{i}"
            cpu_core = str(i)
            config = benchmark_configs[i]
            
            thread = threading.Thread(
                target=self._run_single_benchmark,
                args=(container_name, cpu_core, config, benchmark_results, i, start_signal)
            )
            benchmark_threads.append(thread)
            thread.start()
        
        print(f"⏰ Coordinated start in 2 seconds...")
        print(f"🎯 GO! All containers processing...")
        
        # Wait for all benchmarks to complete
        for thread in benchmark_threads:
            thread.join()
        
        # Analyze results
        return self._analyze_distributed_results(benchmark_results)
    
    def _run_single_benchmark(self, container_name: str, cpu_core: str, 
                             config: Dict, results: List, container_id: int, start_signal: float):
        """Run benchmark on a single container."""
        
        # Wait for coordinated start
        while time.time() < start_signal:
            time.sleep(0.01)
        
        benchmark_start = time.perf_counter()
        
        try:
            # Save benchmark config
            config_file = f"benchmark_config_{container_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f)
            
            # Run benchmark - use continuous processor if duration is set
            cmd = [
                "docker", "run", "--rm",
                "--cpus=1.0",
                f"--memory={self.ram_per_container}",
                f"--cpuset-cpus={cpu_core}",  # Pin to specific CPU core
                f"--name={container_name}",
                "-v", f"{Path.cwd()}/{config_file}:/app/config.yaml",
                "-v", f"{Path.cwd()}/benchmark_output_{container_id}:/app/output",
                "-v", f"{Path.home()}/projects/docling/cli/data:/app/data:ro",
                "-v", f"{Path.home()}/projects/docling/cli/data_complex:/app/data_complex:ro",
                "-v", f"{Path.home()}/projects/docling/cli/data_osha:/app/data_osha:ro",
                "-v", f"{Path.cwd()}/continuous_processor.py:/app/continuous_processor.py:ro",
                "mvp-hyper:benchmark",
                "python", "continuous_processor.py", str(self.duration)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.duration + 30)
            benchmark_time = time.perf_counter() - benchmark_start
            
            if result.returncode == 0:
                # Parse output for performance metrics
                performance = self._parse_container_output(result.stdout, container_id, benchmark_time)
                results.append(performance)
                print(f"  ✅ Container {container_id}: {performance['pages_per_second']:.1f} pages/sec")
            else:
                print(f"  ❌ Container {container_id} failed: {result.stderr[:100]}")
                
        except Exception as e:
            print(f"  ❌ Container {container_id} error: {str(e)[:50]}")
        finally:
            # Cleanup
            try:
                Path(f"benchmark_config_{container_id}.yaml").unlink()
            except:
                pass
    
    def _create_warmup_config(self) -> Dict:
        """Create config for quick warm-up (1 file only)."""
        
        return {
            'inputs': {
                'files': [],
                'directories': ['/app/data', '/app/data_complex', '/app/data_osha']
            },
            'processing': {
                'max_workers': 1,
                'max_file_size_mb': 5,
                'timeout_per_file': 5,
                'skip_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                                  '.mp3', '.mp4', '.wav', '.avi', '.mov', '.wmv', '.flv',
                                  '.zip', '.tar', '.gz', '.bz2', '.rar', '.7z',
                                  '.exe', '.dll', '.so', '.dylib', '.bin', '.dat']
            },
            'pdf': {
                'max_pages_to_extract': 1,
                'skip_if_pages_over': 10,
                'skip_patterns': []
            },
            'debug': {
                'max_files_to_process': 1,  # Only 1 file for warm-up
                'progress_interval': 1,
                'timing_threshold': 1.0
            },
            'output': {
                'directory': '/app/output'
            }
        }
    
    def _create_benchmark_configs(self) -> List[Dict]:
        """Create benchmark configs for each container."""
        
        configs = []
        
        # All containers process the same data for fair performance comparison
        directories = ['/app/data', '/app/data_complex', '/app/data_osha']
        
        for i in range(self.num_containers):
            # Each container processes ALL directories (same workload)
            assigned_dirs = directories
            
            config = {
                'inputs': {
                    'files': [],
                    'directories': assigned_dirs
                },
                'processing': {
                    'max_workers': 1,  # Single core per container
                    'max_file_size_mb': 25,
                    'timeout_per_file': 10,
                    'slow_file_threshold': 3.0,
                    'skip_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                                      '.mp3', '.mp4', '.wav', '.avi', '.mov', '.wmv', '.flv',
                                      '.zip', '.tar', '.gz', '.bz2', '.rar', '.7z',
                                      '.exe', '.dll', '.so', '.dylib', '.bin', '.dat']
                },
                'pdf': {
                    'max_pages_to_extract': 15,
                    'skip_if_pages_over': 75,
                    'skip_patterns': []
                },
                'debug': {
                    'max_files_to_process': 0,  # Process all assigned files
                    'progress_interval': 100,
                    'timing_threshold': 1.0
                },
                'output': {
                    'directory': '/app/output',
                    'save_performance_log': True,
                    'save_error_log': True
                }
            }
            configs.append(config)
        
        return configs
    
    def _parse_container_output(self, output: str, container_id: int, total_time: float) -> Dict:
        """Parse container output for performance metrics."""
        
        # Default values
        performance = {
            'container_id': container_id,
            'total_time': total_time,
            'files_processed': 0,
            'pages_processed': 0,
            'files_per_second': 0,
            'pages_per_second': 0,
            'cpu_core': container_id
        }
        
        try:
            # Look for JSON results from continuous processor
            if 'RESULTS_JSON_START' in output and 'RESULTS_JSON_END' in output:
                json_start = output.index('RESULTS_JSON_START') + len('RESULTS_JSON_START')
                json_end = output.index('RESULTS_JSON_END')
                json_str = output[json_start:json_end].strip()
                results = json.loads(json_str)
                
                performance['files_processed'] = results['total_files']
                performance['pages_processed'] = results['total_pages']
                performance['files_per_second'] = results['files_per_second']
                performance['pages_per_second'] = results['pages_per_second']
                performance['total_time'] = results['duration']
            else:
                # Fallback to old parsing method
                lines = output.split('\n')
                for line in lines:
                    if 'Total files:' in line:
                        performance['files_processed'] = int(line.split(':')[1].strip())
                    elif 'Total pages:' in line:
                        performance['pages_processed'] = int(line.split(':')[1].strip())
                    elif 'Files/second:' in line:
                        performance['files_per_second'] = float(line.split(':')[1].strip())
                    elif 'Pages/second:' in line:
                        performance['pages_per_second'] = float(line.split(':')[1].strip())
        
        except Exception as e:
            print(f"  ⚠️  Error parsing container {container_id} output: {str(e)[:50]}")
            # If parsing fails, calculate from totals
            if total_time > 0:
                performance['files_per_second'] = performance['files_processed'] / total_time
                performance['pages_per_second'] = performance['pages_processed'] / total_time
        
        return performance
    
    def _analyze_distributed_results(self, results: List[Dict]) -> Dict:
        """Analyze the distributed benchmark results."""
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Calculate totals and averages
        total_files = sum(r['files_processed'] for r in results)
        total_pages = sum(r['pages_processed'] for r in results)
        total_time = max(r['total_time'] for r in results)  # Longest running container
        
        # Calculate distributed throughput
        distributed_files_per_sec = total_files / total_time if total_time > 0 else 0
        distributed_pages_per_sec = total_pages / total_time if total_time > 0 else 0
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'containers': self.num_containers,
                'cpu_cores_total': self.num_containers,
                'ram_total_gb': self.num_containers,
                'ram_per_container': self.ram_per_container
            },
            'results': {
                'total_files_processed': total_files,
                'total_pages_processed': total_pages,
                'total_processing_time': total_time,
                'distributed_files_per_second': distributed_files_per_sec,
                'distributed_pages_per_second': distributed_pages_per_sec,
                'containers_completed': len(results)
            },
            'container_details': results,
            'scaling_analysis': self._calculate_scaling_metrics(results)
        }
        
        return analysis
    
    def _calculate_scaling_metrics(self, results: List[Dict]) -> Dict:
        """Calculate scaling efficiency metrics."""
        
        if not results:
            return {}
        
        # Single container baseline (hypothetical)
        single_container_estimate = sum(r['pages_per_second'] for r in results) / len(results)
        
        # Actual distributed performance
        total_pages = sum(r['pages_processed'] for r in results)
        max_time = max(r['total_time'] for r in results)
        actual_distributed = total_pages / max_time if max_time > 0 else 0
        
        # Theoretical maximum (perfect scaling)
        theoretical_max = single_container_estimate * self.num_containers
        
        # Scaling efficiency
        scaling_efficiency = (actual_distributed / theoretical_max * 100) if theoretical_max > 0 else 0
        
        return {
            'single_container_avg_pages_per_sec': single_container_estimate,
            'theoretical_max_pages_per_sec': theoretical_max,
            'actual_distributed_pages_per_sec': actual_distributed,
            'scaling_efficiency_percent': scaling_efficiency,
            'linear_scaling_achieved': scaling_efficiency > 80
        }
    
    def print_results(self, analysis: Dict):
        """Print beautiful benchmark results."""
        
        print(f"\n🏆 DISTRIBUTED BENCHMARK RESULTS")
        print("=" * 60)
        print(f"📅 Timestamp: {analysis['timestamp']}")
        print(f"🐳 Configuration:")
        print(f"  • Containers: {analysis['configuration']['containers']}")
        print(f"  • CPU Cores: {analysis['configuration']['cpu_cores_total']} (1 per container)")
        print(f"  • Total RAM: {analysis['configuration']['ram_total_gb']}GB")
        
        results = analysis['results']
        print(f"\n📊 Performance Results:")
        print(f"  • Files Processed: {results['total_files_processed']:,}")
        print(f"  • Pages Processed: {results['total_pages_processed']:,}")
        print(f"  • Processing Time: {results['total_processing_time']:.2f}s")
        print(f"  • Files/Second: {results['distributed_files_per_second']:.1f}")
        print(f"  • Pages/Second: {results['distributed_pages_per_second']:.1f}")
        
        scaling = analysis['scaling_analysis']
        print(f"\n🚀 Scaling Analysis:")
        print(f"  • Single Container Avg: {scaling['single_container_avg_pages_per_sec']:.1f} pages/sec")
        print(f"  • Theoretical Maximum: {scaling['theoretical_max_pages_per_sec']:.1f} pages/sec")
        print(f"  • Actual Distributed: {scaling['actual_distributed_pages_per_sec']:.1f} pages/sec")
        print(f"  • Scaling Efficiency: {scaling['scaling_efficiency_percent']:.1f}%")
        
        if scaling['linear_scaling_achieved']:
            print(f"  ✅ Excellent scaling achieved!")
        else:
            print(f"  ⚠️  Scaling could be improved")
        
        # Individual container performance
        print(f"\n📋 Individual Container Performance:")
        for result in analysis['container_details']:
            print(f"  Container {result['container_id']:2d} (CPU {result['cpu_core']}): "
                  f"{result['pages_per_second']:6.1f} pages/sec, "
                  f"{result['files_processed']:3d} files, "
                  f"{result['total_time']:5.2f}s")
        
        # Achievement check
        if results['distributed_pages_per_second'] >= 1000:
            print(f"\n🎉 TARGET ACHIEVED: {results['distributed_pages_per_second']:.1f} pages/sec >= 1000!")
        else:
            print(f"\n📈 Current: {results['distributed_pages_per_second']:.1f} pages/sec (Target: 1000)")
            needed_containers = 1000 / scaling['single_container_avg_pages_per_sec']
            print(f"💡 Estimated containers needed for 1000 pages/sec: {needed_containers:.1f}")
        
        # Save results
        self._save_results(analysis)
    
    def _save_results(self, analysis: Dict):
        """Save benchmark results to file."""
        
        output_file = f"distributed_benchmark_{analysis['configuration']['containers']}containers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def cleanup(self):
        """Cleanup any remaining containers and files."""
        
        print("\n🧹 Cleaning up...")
        
        # Stop any running containers
        for i in range(self.num_containers):
            container_name = f"mvp-hyper-benchmark-{i}"
            subprocess.run(["docker", "stop", container_name], 
                         capture_output=True, text=True)
            subprocess.run(["docker", "rm", container_name], 
                         capture_output=True, text=True)
        
        # Clean up config files
        for i in range(self.num_containers):
            try:
                Path(f"warmup_config_{i}.yaml").unlink()
                Path(f"benchmark_config_{i}.yaml").unlink()
            except:
                pass


def main():
    """Main benchmark runner."""
    
    parser = argparse.ArgumentParser(description="Distributed Docker benchmark")
    parser.add_argument("--containers", type=int, default=4,
                       help="Number of containers (default: 4)")
    parser.add_argument("--ram", default="1g",
                       help="RAM per container (default: 1g)")
    parser.add_argument("--duration", type=int, default=30,
                       help="Test duration in seconds (default: 30)")
    parser.add_argument("--no-warmup", action="store_true",
                       help="Skip warm-up phase")
    
    args = parser.parse_args()
    
    if args.containers > 8:
        print(f"⚠️  Warning: {args.containers} containers may exceed available CPU cores")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    benchmark = DistributedBenchmark(args.containers, args.ram, args.duration)
    
    try:
        # Prepare containers
        if not benchmark.prepare_containers():
            sys.exit(1)
        
        # Warm-up phase
        if not args.no_warmup:
            if not benchmark.warm_up_containers():
                print("❌ Warm-up failed, aborting benchmark")
                sys.exit(1)
        
        # Run benchmark
        results = benchmark.run_distributed_benchmark()
        
        # Display results
        benchmark.print_results(results)
        
    except KeyboardInterrupt:
        print("\n🛑 Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    main()