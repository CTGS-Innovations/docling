# Distributed Benchmark System

Multi-container Docker benchmark system for ultra-high-performance document processing with coordinated warm-up and synchronized starts.

## 🎯 What This System Does

Creates multiple Docker containers that run in parallel, each pinned to its own CPU core, with coordinated warm-up and synchronized starts. Measures scaling efficiency as you add more containers.

## 📋 Setup Requirements

1. **Docker must be running** on your system
2. **Multi-core CPU** - each container gets its own core
3. **Data directories** must exist and be accessible
4. **Python 3.6+** for the orchestration script

## 🚀 Quick Start

### Basic Usage

#### Quick Test (2 containers)
```bash
cd /home/corey/projects/docling/mvp-hyper
python distributed-benchmark.py --containers 2
```

#### Full Benchmark (4 containers, 60 seconds)
```bash
python distributed-benchmark.py --containers 4 --duration 60
```

#### Scaling Analysis (test 1, 2, 4, 8 containers automatically)
```bash
python distributed-benchmark.py --scaling-test --max-containers 8
```

## 📊 Command Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--containers N` | Number of Docker containers to run | `--containers 4` |
| `--duration S` | How long each container runs (seconds) | `--duration 60` |
| `--data-dir PATH` | Data directory to mount | `--data-dir ~/data/pdfs` |
| `--scaling-test` | Automatically test 1, 2, 4, 8... containers | `--scaling-test` |
| `--max-containers N` | Maximum containers for scaling test | `--max-containers 8` |
| `--help` | Show all available options | `--help` |

### Advanced Options

| Command | Description | Default |
|---------|-------------|---------|
| `--config CONFIG` | Custom config file | `docker-config.yaml` |
| `--output-dir DIR` | Output directory for results | `benchmark_output` |
| `--warmup-time S` | Container warmup time | `10` |
| `--cleanup` | Clean up containers after test | `True` |

## 🔄 What You'll See

### Phase 1: Container Warm-up
```
🚀 DISTRIBUTED BENCHMARK: 4 containers, 60s each
📦 Building Docker containers (1/4)...
📦 Building Docker containers (2/4)...
📦 Building Docker containers (3/4)...
📦 Building Docker containers (4/4)...
⏳ Warming up containers...
✅ Container mvp-benchmark-1 ready on CPU 0
✅ Container mvp-benchmark-2 ready on CPU 1
✅ Container mvp-benchmark-3 ready on CPU 2
✅ Container mvp-benchmark-4 ready on CPU 3
```

### Phase 2: Coordinated Start
```
🏁 Starting coordinated benchmark in 3...2...1...GO!
📊 Monitoring containers...
```

### Phase 3: Real-time Progress
```
[15s] Container 1: 1,247 pages/sec | Container 2: 1,198 pages/sec | Container 3: 1,156 pages/sec | Container 4: 1,089 pages/sec
[30s] Container 1: 1,289 pages/sec | Container 2: 1,245 pages/sec | Container 3: 1,201 pages/sec | Container 4: 1,167 pages/sec
[45s] Container 1: 1,305 pages/sec | Container 2: 1,267 pages/sec | Container 3: 1,234 pages/sec | Container 4: 1,189 pages/sec
```

### Phase 4: Results Analysis
```
📋 BENCHMARK RESULTS:
====================================================
Container 1 (CPU 0): 1,305 pages/sec, 943 files processed
Container 2 (CPU 1): 1,267 pages/sec, 891 files processed
Container 3 (CPU 2): 1,234 pages/sec, 856 files processed
Container 4 (CPU 3): 1,189 pages/sec, 823 files processed

Total throughput: 4,995 pages/sec
Average per container: 1,249 pages/sec
Scaling efficiency: 89.2% (excellent)
====================================================
```

## 📈 Understanding Results

### Performance Metrics

| Metric | Description | Good Range |
|--------|-------------|------------|
| **Pages/sec per container** | Individual container throughput | 800-1,200 pages/sec |
| **Total throughput** | Combined performance of all containers | Scales linearly with containers |
| **Scaling efficiency** | How well performance scales with containers | 85-100% |
| **Average per container** | Mean performance across all containers | Should be consistent |

### Scaling Efficiency Guide

| Efficiency | Assessment | Likely Cause |
|------------|------------|--------------|
| **95-100%** | Perfect scaling | Optimal setup |
| **85-94%** | Excellent scaling | Minor overhead |
| **70-84%** | Good scaling | Some resource contention |
| **50-69%** | Poor scaling | CPU/Memory/I/O bottleneck |
| **<50%** | Failed scaling | System overloaded |

## 🎯 Expected Performance

Based on testing with various configurations:

### Single Container Performance
- **Optimal**: 1,000-1,200 pages/sec
- **Good**: 800-1,000 pages/sec  
- **Acceptable**: 500-800 pages/sec

### Multi-Container Scaling
| Containers | Expected Throughput | Scaling Efficiency |
|------------|--------------------|--------------------|
| 1 | ~1,000 pages/sec | 100% (baseline) |
| 2 | ~1,900 pages/sec | 95% |
| 4 | ~3,600 pages/sec | 90% |
| 8 | ~6,800 pages/sec | 85% |

**Note**: Performance degrades beyond your CPU core count.

## 🔧 Usage Examples

### Development Testing
```bash
# Quick 30-second test with 2 containers
python distributed-benchmark.py --containers 2 --duration 30

# Test specific data directory
python distributed-benchmark.py --containers 2 --data-dir ~/test-data
```

### Production Benchmarking
```bash
# Full 5-minute benchmark with 4 containers
python distributed-benchmark.py --containers 4 --duration 300

# Comprehensive scaling analysis
python distributed-benchmark.py --scaling-test --max-containers $(nproc) --duration 120
```

### Resource-Constrained Testing
```bash
# Test with limited containers (edge device simulation)
python distributed-benchmark.py --containers 1 --duration 60 --config docker-config.yaml

# Memory-constrained scaling test
python distributed-benchmark.py --scaling-test --max-containers 2 --config docker-config.yaml
```

## 🛠️ Troubleshooting

### Common Issues

#### Low Performance (<500 pages/sec per container)
```bash
# Check Docker resources
docker system info | grep -E "(CPUs|Memory)"

# Monitor resource usage during test
htop  # Check CPU usage
docker stats  # Check container resource usage
```

#### Poor Scaling Efficiency (<80%)
```bash
# Check if hitting CPU limits
lscpu  # Check available CPU cores
cat /proc/cpuinfo | grep "^processor" | wc -l  # Count cores

# Check I/O bottlenecks
iotop  # Monitor disk I/O during test
```

#### Container Failures
```bash
# Check container logs
docker logs mvp-benchmark-1
docker logs mvp-benchmark-2

# Check Docker daemon
sudo systemctl status docker
```

### Performance Optimization

#### For Maximum Speed
```bash
# Use all CPU cores
python distributed-benchmark.py --containers $(nproc) --duration 120

# Ensure Docker has sufficient resources
docker system prune  # Clean up unused containers/images
```

#### For Resource Constraints
```bash
# Limit containers to available cores
python distributed-benchmark.py --containers 2 --config docker-config.yaml

# Shorter duration for quick tests
python distributed-benchmark.py --containers 1 --duration 15
```

## 📁 File Structure

```
mvp-hyper/
├── distributed-benchmark.py    # Main orchestration script
├── docker-config.yaml         # Resource-constrained config
├── config.yaml                # Default production config
├── mvp-hyper-core.py          # Processing engine (runs in containers)
├── Dockerfile                 # Container definition
└── DISTRIBUTED_BENCHMARK.md   # This documentation
```

## 🔄 Integration with Main System

### Use with existing configs
```bash
# Use production settings
python distributed-benchmark.py --containers 4 --config config.yaml

# Use Docker-optimized settings
python distributed-benchmark.py --containers 2 --config docker-config.yaml
```

### Generate custom test data
```bash
# Create test configuration first
python mvp-hyper-core.py --test-config

# Use test config in distributed benchmark
python distributed-benchmark.py --containers 2 --config test_config.yaml
```

## 🚀 Advanced Usage

### Custom CPU Pinning
The system automatically pins each container to a specific CPU core:
- Container 1 → CPU 0
- Container 2 → CPU 1  
- Container 3 → CPU 2
- etc.

### Monitoring Integration
```bash
# Run with external monitoring
python distributed-benchmark.py --containers 4 &
BENCHMARK_PID=$!

# Monitor in separate terminal
watch -n 1 'docker stats --no-stream'

# Wait for completion
wait $BENCHMARK_PID
```

### Batch Testing
```bash
#!/bin/bash
# Test multiple configurations
for containers in 1 2 4 8; do
    echo "Testing $containers containers..."
    python distributed-benchmark.py --containers $containers --duration 60
    sleep 10  # Cool down between tests
done
```

## 📊 Output Files

The system generates detailed logs and results:

- `benchmark_output/results_TIMESTAMP.json` - Detailed performance data
- `benchmark_output/containers/` - Individual container logs
- `benchmark_output/scaling_analysis.csv` - Scaling efficiency data

## 🎯 Next Steps

After running benchmarks:

1. **Analyze Results**: Look for scaling efficiency patterns
2. **Optimize Configuration**: Adjust based on bottlenecks found  
3. **Deploy Production**: Use optimal container count for your hardware
4. **Monitor Performance**: Set up continuous benchmarking