#!/usr/bin/env python3
"""
Simplified Distributed Docker Benchmark
========================================
Time-based burn-in test with real-time monitoring.
Each container processes the same files continuously for the specified duration.
"""

import subprocess
import threading
import time
import argparse
from pathlib import Path
from datetime import datetime


def run_container(container_id: int, duration: int, results: list):
    """Run a single container for the specified duration."""
    
    container_name = f"mvp-benchmark-{container_id}"
    cpu_core = str(container_id)
    
    print(f"🚀 Starting container {container_id} on CPU {cpu_core}")
    
    # Build command - just run mvp-hyper-core.py in a loop for duration
    cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "--cpus=1.0",
        "--memory=1g",
        f"--cpuset-cpus={cpu_core}",
        "-v", f"{Path.home()}/projects/docling/cli/data:/app/data:ro",
        "-v", f"{Path.home()}/projects/docling/cli/data_complex:/app/data_complex:ro", 
        "-v", f"{Path.home()}/projects/docling/cli/data_osha:/app/data_osha:ro",
        "-v", f"{Path.cwd()}/docker-config.yaml:/app/config.yaml:ro",
        "mvp-hyper:benchmark",
        "sh", "-c",
        f"end_time=$(($(date +%s) + {duration})); "
        f"cycles=0; "
        f"total_pages=0; "
        f"total_files=0; "
        f"while [ $(date +%s) -lt $end_time ]; do "
        f"  cycles=$((cycles + 1)); "
        f"  echo \"[Container {container_id}] Starting cycle $cycles at $(date +%H:%M:%S)\"; "
        f"  python mvp-hyper-core.py --config /app/config.yaml; "
        f"done; "
        f"echo \"[Container {container_id}] Completed $cycles cycles in {duration} seconds\""
    ]
    
    try:
        # Run and stream output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Track metrics
        pages_per_sec_values = []
        files_per_sec_values = []
        cycles = 0
        
        # Stream output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                # Capture metrics
                if 'Pages/second:' in line:
                    try:
                        pages_sec = float(line.split('Pages/second:')[1].strip())
                        pages_per_sec_values.append(pages_sec)
                    except:
                        pass
                elif 'Files/second:' in line:
                    try:
                        files_sec = float(line.split('Files/second:')[1].strip())
                        files_per_sec_values.append(files_sec)
                    except:
                        pass
                elif 'cycle' in line.lower() and 'starting' in line.lower():
                    cycles += 1
                
                # Show key metrics
                if any(keyword in line for keyword in ['Pages/second', 'Files/second', 'cycle', 'Completed']):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Container {container_id}: {line.strip()}")
        
        process.wait()
        
        # Calculate averages
        avg_pages_sec = sum(pages_per_sec_values) / len(pages_per_sec_values) if pages_per_sec_values else 0
        avg_files_sec = sum(files_per_sec_values) / len(files_per_sec_values) if files_per_sec_values else 0
        
        results.append({
            'container_id': container_id,
            'status': 'completed' if process.returncode == 0 else 'failed',
            'return_code': process.returncode,
            'cycles': cycles,
            'avg_pages_per_second': avg_pages_sec,
            'avg_files_per_second': avg_files_sec,
            'measurements': len(pages_per_sec_values)
        })
        
    except Exception as e:
        print(f"❌ Container {container_id} error: {e}")
        results.append({
            'container_id': container_id,
            'status': 'error',
            'error': str(e)
        })


def main():
    parser = argparse.ArgumentParser(description="Simplified distributed benchmark")
    parser.add_argument("--containers", type=int, default=2,
                       help="Number of containers (default: 2)")
    parser.add_argument("--duration", type=int, default=60,
                       help="Test duration in seconds (default: 60)")
    parser.add_argument("--stagger", type=float, default=0.5,
                       help="Stagger delay between container starts (default: 0.5s)")
    
    args = parser.parse_args()
    
    print(f"🔥 DISTRIBUTED BURN-IN TEST")
    print("=" * 60)
    print(f"📊 Configuration:")
    print(f"  • Containers: {args.containers}")
    print(f"  • Duration: {args.duration} seconds")  
    print(f"  • CPU cores: {args.containers} (1 per container)")
    print(f"  • RAM: {args.containers}GB total (1GB per container)")
    print(f"  • Stagger: {args.stagger}s between starts")
    print("=" * 60)
    
    # Build Docker image first
    print("🔨 Building Docker image...")
    build_result = subprocess.run(
        ["docker", "build", "-t", "mvp-hyper:benchmark", "."],
        capture_output=True,
        text=True
    )
    
    if build_result.returncode != 0:
        print(f"❌ Docker build failed: {build_result.stderr}")
        return
    
    print("✅ Docker image ready")
    print()
    
    # Start containers with stagger
    threads = []
    results = []
    
    for i in range(args.containers):
        if i > 0:
            time.sleep(args.stagger)
        
        thread = threading.Thread(
            target=run_container,
            args=(i, args.duration, results)
        )
        thread.start()
        threads.append(thread)
    
    print(f"\n⏱️  Running for {args.duration} seconds...")
    print("=" * 60)
    
    # Wait for all containers to complete
    for thread in threads:
        thread.join()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 BURN-IN TEST COMPLETE")
    print(f"✅ {len([r for r in results if r['status'] == 'completed'])} containers completed successfully")
    
    if any(r['status'] != 'completed' for r in results):
        print(f"❌ {len([r for r in results if r['status'] != 'completed'])} containers had issues")
    
    # Performance Summary
    print("\n📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    total_pages_per_sec = 0
    total_files_per_sec = 0
    
    for r in results:
        if r['status'] == 'completed' and 'avg_pages_per_second' in r:
            pages_sec = r['avg_pages_per_second']
            files_sec = r['avg_files_per_second']
            cycles = r.get('cycles', 0)
            
            print(f"Container {r['container_id']}: {pages_sec:7.1f} pages/sec, "
                  f"{files_sec:6.1f} files/sec ({cycles} cycles)")
            
            total_pages_per_sec += pages_sec
            total_files_per_sec += files_sec
    
    if total_pages_per_sec > 0:
        print("-" * 60)
        print(f"🎯 TOTAL THROUGHPUT: {total_pages_per_sec:7.1f} pages/sec")
        print(f"📁 TOTAL THROUGHPUT: {total_files_per_sec:7.1f} files/sec")
        
        if args.containers > 1:
            efficiency = (total_pages_per_sec / (total_pages_per_sec / args.containers * args.containers)) * 100
            print(f"⚡ Scaling Efficiency: {efficiency:.1f}%")
        
        if total_pages_per_sec >= 1000:
            print(f"\n✨ TARGET ACHIEVED! {total_pages_per_sec:.1f} pages/sec >= 1000!")
        else:
            print(f"\n📈 Current: {total_pages_per_sec:.1f} pages/sec (Target: 1000)")
            
    print("\n💡 Check Docker stats in another terminal with:")
    print("   docker stats --no-stream")


if __name__ == "__main__":
    main()