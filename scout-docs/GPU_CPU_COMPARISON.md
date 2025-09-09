# GPU vs CPU Performance Comparison Feature

## Overview
The Docling Processing Center now includes automatic detection and tracking of compute resources (CPU vs GPU) used for document processing, enabling direct performance comparisons between different compute environments.

## Features Added

### 1. **Automatic Compute Detection**
- **Backend Detection**: Automatically detects available compute resources using PyTorch
- **Environment Logging**: Reports compute type (CPU/GPU) and details in processing logs
- **Metadata Tracking**: Stores compute information in job results for historical analysis

### 2. **Visual Compute Indicators**
- **Jobs Table Column**: New "Compute" column shows CPU 🖥️ or GPU 🚀 for each job
- **Color Coding**: 
  - GPU jobs: Green badge with rocket icon
  - CPU jobs: Blue badge with CPU chip icon
- **Tooltip Details**: Hover over compute badges to see detailed hardware information

### 3. **Performance Comparison Dashboard**
- **Executive Header**: Shows current compute mode (CPU/GPU)
- **Historical Tracking**: All jobs retain compute type information
- **Side-by-Side Comparison**: Easy visual comparison of processing times between GPU and CPU jobs

## Technical Implementation

### Backend Changes
1. **`torch_config.py`** - Added `get_compute_info()` function:
   ```python
   def get_compute_info():
       """Get information about the compute environment (CPU vs GPU)."""
       cuda_available = torch.cuda.is_available()
       
       if cuda_available:
           device_count = torch.cuda.device_count()
           device_name = torch.cuda.get_device_name(0)
           compute_type = "GPU"
           compute_details = f"{device_name} ({device_count} device(s))"
       else:
           cpu_count = os.cpu_count() or 4
           compute_type = "CPU"
           compute_details = f"{cpu_count} cores, {torch.get_num_threads()} threads"
   ```

2. **Enhanced ProcessingMetrics** - Added compute tracking:
   - `compute_type`: "CPU" or "GPU"
   - `compute_details`: Detailed hardware information

3. **Processing Logs** - Added compute environment logging:
   ```
   🖥️ Compute: CPU (8 cores, 8 threads)
   ```

### Frontend Changes
1. **CompactJobsTable.js** - Added compute column with visual indicators
2. **App.js** - Added current compute mode to executive dashboard
3. **Icons and Styling** - CPU chip and rocket launch icons for visual distinction

## Usage for Performance Comparison

### Comparing Results
When you have both GPU and CPU results, you can easily compare:

1. **Processing Speed**: Compare total processing times between GPU and CPU jobs
2. **Throughput**: Words per second and pages per second metrics
3. **Scalability**: How performance changes with document size/complexity
4. **Consistency**: Variance in processing times between compute types

### Example Comparison
```
Document: research_paper.pdf (57 pages)

CPU Processing:
- Compute: Intel i7-9700K (8 cores, 8 threads)
- Time: 100.3s
- Throughput: 2,279 words/sec
- Pages/sec: 0.57

GPU Processing (when available):
- Compute: NVIDIA RTX 3080 (1 device)
- Time: 45.2s
- Throughput: 5,065 words/sec  
- Pages/sec: 1.26

Performance Improvement: 2.2x faster with GPU
```

### Metrics to Compare
- **Total Processing Time**: Overall job completion time
- **Words per Second**: Text processing throughput
- **Pages per Second**: Document processing rate
- **Memory Usage**: Resource efficiency (when available)
- **Consistency**: Processing time variance across similar documents

## Benefits

### For Development
- **Optimization Guidance**: Identify which processing stages benefit most from GPU acceleration
- **Resource Planning**: Make informed decisions about compute infrastructure
- **Performance Regression**: Track performance changes between CPU and GPU implementations

### For Operations
- **Cost Analysis**: Compare processing costs between CPU and GPU instances
- **Capacity Planning**: Understand throughput differences for scaling decisions
- **SLA Management**: Set appropriate processing time expectations

### For Research
- **Performance Benchmarking**: Systematic comparison of document processing performance
- **Workload Analysis**: Understand which document types benefit most from GPU acceleration
- **Algorithm Evaluation**: Compare processing efficiency across different compute platforms

## Future Enhancements

### Potential Additions
1. **Mixed Mode Processing**: Hybrid CPU/GPU processing for optimal performance
2. **Real-time Resource Monitoring**: Live CPU/GPU utilization during processing
3. **Automatic Compute Selection**: AI-driven selection of optimal compute type per document
4. **Batch Processing Optimization**: Intelligent batching based on available compute resources
5. **Performance Prediction**: Estimate processing time based on document characteristics and compute type

### Integration Opportunities
1. **Cloud Auto-scaling**: Automatic GPU instance provisioning for large batch jobs
2. **Cost Optimization**: Dynamic compute selection based on cost/performance ratios
3. **Quality Metrics**: Correlate compute type with processing accuracy/quality scores

## Getting Started

### Current Setup (CPU Only)
The system is currently configured for CPU processing. All jobs will show:
- Compute Type: CPU
- Badge: Blue with CPU chip icon
- Details: Available CPU cores and thread count

### Adding GPU Support
To enable GPU processing:
1. Install CUDA-compatible PyTorch
2. Ensure GPU drivers are properly installed
3. The system will automatically detect and utilize GPU resources
4. Jobs will show GPU compute type with green badges and rocket icons

This feature provides the foundation for comprehensive performance analysis and optimization of document processing workflows across different compute environments.