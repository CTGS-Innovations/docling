#!/usr/bin/env python3
"""
Optimize visual format (PDF, TIFF, WebP) processing throughput
Target: Increase from 5.3 files/min to 16.7 files/min baseline
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any

class VisualFormatOptimizer:
    """Test different configurations to optimize visual format processing"""
    
    def __init__(self):
        self.data_dir = Path('/home/corey/projects/docling/cli/data')
        self.output_base = Path('/tmp/visual_optimization')
        self.visual_formats = ['pdf', 'tiff', 'webp', 'png', 'jpg', 'jpeg']
        
    def find_visual_files(self) -> Dict[str, List[Path]]:
        """Find visual format files for testing"""
        visual_files = {}
        
        for fmt in self.visual_formats:
            files = list(self.data_dir.glob(f'**/*.{fmt}'))
            if files:
                visual_files[fmt] = files[:3]  # Limit to 3 files per format for speed
                
        return visual_files
    
    def test_configuration(self, config_name: str, files: List[Path], 
                         pipeline: str, extra_flags: List[str] = None) -> Dict[str, Any]:
        """Test a specific docling configuration"""
        
        if extra_flags is None:
            extra_flags = []
            
        output_dir = self.output_base / f"test_{config_name}_{int(time.time())}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Base command with performance optimizations
        cmd = [
            'docling',
            *[str(f) for f in files],
            '--to', 'md',
            '--output', str(output_dir),
            '--device', 'cuda',
            '--pipeline', pipeline
        ]
        
        # Add extra flags
        cmd.extend(extra_flags)
        
        print(f"🧪 Testing {config_name}: {pipeline} pipeline")
        print(f"   Files: {len(files)} files")
        print(f"   Flags: {' '.join(extra_flags) if extra_flags else 'none'}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            duration = time.time() - start_time
            
            success = result.returncode == 0
            throughput = len(files) / duration * 60 if success and duration > 0 else 0
            
            # Count output files
            output_files = list(output_dir.glob('*.md'))
            
            # Clean up
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir, ignore_errors=True)
                
            return {
                'config': config_name,
                'pipeline': pipeline,
                'files_processed': len(files),
                'success': success,
                'duration': duration,
                'throughput': throughput,
                'output_files': len(output_files),
                'flags': extra_flags,
                'error': result.stderr[-500:] if result.stderr else None,
                'stdout': result.stdout[-300:] if result.stdout else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'config': config_name,
                'pipeline': pipeline,
                'files_processed': len(files),
                'success': False,
                'duration': 180,
                'throughput': 0,
                'output_files': 0,
                'flags': extra_flags,
                'error': 'Timeout after 180 seconds'
            }
        except Exception as e:
            return {
                'config': config_name,
                'pipeline': pipeline,
                'files_processed': len(files),
                'success': False,
                'duration': 0,
                'throughput': 0,
                'output_files': 0,
                'flags': extra_flags,
                'error': str(e)
            }
    
    def run_optimization_tests(self):
        """Run comprehensive visual format optimization tests"""
        
        print("🎯 VISUAL FORMAT OPTIMIZATION TEST")
        print("Target: Increase throughput from 5.3 to 16.7 files/min")
        print("=" * 60)
        
        # Find visual files
        visual_files = self.find_visual_files()
        
        if not visual_files:
            print("❌ No visual format files found")
            return
            
        # Select test files (mix of formats)
        test_files = []
        for fmt, files in visual_files.items():
            test_files.extend(files)
            print(f"   Found {len(files)} {fmt.upper()} files")
        
        print(f"\n🔍 Testing with {len(test_files)} visual files")
        print("=" * 60)
        
        # Test configurations focused on visual processing
        configurations = [
            {
                'name': 'standard_baseline',
                'pipeline': 'standard',
                'flags': []
            },
            {
                'name': 'standard_optimized',
                'pipeline': 'standard', 
                'flags': [
                    '--num-threads', '8',
                    '--page-batch-size', '8',
                    '--pdf-backend', 'dlparse_v4'
                ]
            },
            {
                'name': 'standard_max_batch',
                'pipeline': 'standard',
                'flags': [
                    '--num-threads', '12', 
                    '--page-batch-size', '16',
                    '--pdf-backend', 'dlparse_v4'
                ]
            },
            {
                'name': 'vlm_minimal',
                'pipeline': 'vlm',
                'flags': [
                    '--num-threads', '4',
                    '--page-batch-size', '2',
                    '--vlm-model', 'smoldocling'
                ]
            },
            {
                'name': 'vlm_optimized',
                'pipeline': 'vlm',
                'flags': [
                    '--num-threads', '6',
                    '--page-batch-size', '4', 
                    '--vlm-model', 'smoldocling'
                ]
            },
            {
                'name': 'standard_fast_ocr',
                'pipeline': 'standard',
                'flags': [
                    '--num-threads', '8',
                    '--page-batch-size', '8',
                    '--force-ocr',
                    '--pdf-backend', 'dlparse_v4'
                ]
            },
            {
                'name': 'standard_no_ocr',
                'pipeline': 'standard', 
                'flags': [
                    '--num-threads', '10',
                    '--page-batch-size', '12',
                    '--no-ocr',
                    '--pdf-backend', 'dlparse_v4'
                ]
            }
        ]
        
        results = []
        
        # Run each test configuration
        for config in configurations:
            result = self.test_configuration(
                config['name'],
                test_files,
                config['pipeline'], 
                config['flags']
            )
            results.append(result)
            
            if result['success']:
                print(f"   ✅ {result['config']:20} {result['throughput']:6.1f} files/min ({result['duration']:4.1f}s)")
            else:
                error_msg = result['error'][:80] if result['error'] else 'Unknown error'
                print(f"   ❌ {result['config']:20} FAILED - {error_msg}")
        
        # Analysis and recommendations
        self.analyze_results(results, test_files)
    
    def analyze_results(self, results: List[Dict], test_files: List[Path]):
        """Analyze test results and provide optimization recommendations"""
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            print("\n❌ No configurations worked - check GPU and docling installation")
            return
            
        print(f"\n📊 VISUAL FORMAT OPTIMIZATION ANALYSIS")
        print("=" * 60)
        
        # Sort by throughput
        successful_results.sort(key=lambda x: x['throughput'], reverse=True)
        
        best_result = successful_results[0]
        target_throughput = 16.7  # files/min target
        current_baseline = 5.3    # files/min current VLM performance
        
        print(f"🎯 TARGET: {target_throughput} files/min (previous standard pipeline)")
        print(f"📏 CURRENT: {current_baseline} files/min (VLM pipeline)")
        print(f"🏆 BEST ACHIEVED: {best_result['throughput']:.1f} files/min ({best_result['config']})")
        
        # Performance comparison
        if best_result['throughput'] >= target_throughput:
            improvement = (best_result['throughput'] / target_throughput - 1) * 100
            print(f"🚀 SUCCESS: {improvement:+.1f}% above target!")
        else:
            gap = (1 - best_result['throughput'] / target_throughput) * 100
            print(f"⚠️  GAP: {gap:.1f}% below target")
        
        print(f"\n📈 PERFORMANCE RANKING:")
        for i, result in enumerate(successful_results[:5], 1):
            pipeline_icon = "🔥" if result['pipeline'] == 'standard' else "🧠"
            vs_target = result['throughput'] / target_throughput * 100
            print(f"   {i}. {pipeline_icon} {result['config']:20} {result['throughput']:6.1f} files/min ({vs_target:5.1f}% of target)")
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        # Find best standard vs VLM
        best_standard = next((r for r in successful_results if r['pipeline'] == 'standard'), None)
        best_vlm = next((r for r in successful_results if r['pipeline'] == 'vlm'), None)
        
        if best_standard and best_vlm:
            standard_advantage = (best_standard['throughput'] / best_vlm['throughput'] - 1) * 100
            print(f"   📊 Standard pipeline is {standard_advantage:.1f}% faster than VLM")
            
            if best_standard['throughput'] >= target_throughput * 0.9:  # Within 10% of target
                print(f"   ✅ RECOMMENDED: Use standard pipeline for visual formats")
                print(f"      Configuration: {best_standard['config']}")
                print(f"      Flags: {' '.join(best_standard['flags']) if best_standard['flags'] else 'default'}")
            else:
                print(f"   ⚠️  Standard pipeline still below target - investigate further")
        
        # Batch size analysis
        batch_results = {}
        for result in successful_results:
            flags = result['flags']
            batch_size = None
            if '--page-batch-size' in flags:
                idx = flags.index('--page-batch-size')
                if idx + 1 < len(flags):
                    batch_size = int(flags[idx + 1])
            if batch_size:
                batch_results[batch_size] = result['throughput']
                
        if batch_results:
            best_batch = max(batch_results.items(), key=lambda x: x[1])
            print(f"   🎯 Optimal batch size: {best_batch[0]} pages ({best_batch[1]:.1f} files/min)")
        
        # Thread analysis  
        thread_results = {}
        for result in successful_results:
            flags = result['flags']
            num_threads = None
            if '--num-threads' in flags:
                idx = flags.index('--num-threads')
                if idx + 1 < len(flags):
                    num_threads = int(flags[idx + 1])
            if num_threads:
                thread_results[num_threads] = result['throughput']
                
        if thread_results:
            best_threads = max(thread_results.items(), key=lambda x: x[1])
            print(f"   🔧 Optimal thread count: {best_threads[0]} threads ({best_threads[1]:.1f} files/min)")
        
        # Final recommendation
        if best_result['throughput'] >= target_throughput:
            print(f"\n🎉 SOLUTION FOUND:")
            print(f"   Use: docling [files] --pipeline {best_result['pipeline']} {' '.join(best_result['flags']) if best_result['flags'] else ''}")
            print(f"   Expected throughput: {best_result['throughput']:.1f} files/min")
        else:
            print(f"\n🔍 NEXT STEPS TO REACH TARGET:")
            print(f"   1. Try higher batch sizes (16, 32)")
            print(f"   2. Test different PDF backends")
            print(f"   3. Consider hybrid approach (standard for text, VLM only for images)")
            print(f"   4. Profile GPU memory usage during processing")
            
        # Save detailed results
        results_file = Path('/home/corey/projects/docling/cli/visual_optimization_results.json')
        with open(results_file, 'w') as f:
            json.dump({
                'test_files': [str(f) for f in test_files],
                'target_throughput': target_throughput,
                'results': results,
                'best_config': best_result,
                'summary': {
                    'best_throughput': best_result['throughput'],
                    'target_achieved': best_result['throughput'] >= target_throughput,
                    'recommended_pipeline': best_result['pipeline'],
                    'recommended_flags': best_result['flags']
                }
            }, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    optimizer = VisualFormatOptimizer()
    optimizer.run_optimization_tests()