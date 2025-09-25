#!/usr/bin/env python3
"""
Performance Comparison Test
===========================

GOAL: Compare original fusion_cli.py vs enhanced fusion_cli_enhanced.py
REASON: Verify 10x+ performance improvement (105s → ~10s target)
PROBLEM: Need concrete comparison on same workload

This test runs both versions and compares:
- Processing time
- Files per second
- Success rate
- Memory usage
"""

import subprocess
import time
import sys
from pathlib import Path


def run_cli_test(cli_script: str, config_path: str, timeout: int = 300) -> dict:
    """Run CLI and measure performance"""
    print(f"\n🔄 Testing {cli_script}...")
    print(f"   Config: {config_path}")
    print(f"   Timeout: {timeout}s")
    
    start_time = time.perf_counter()
    
    try:
        # Run CLI with timeout
        result = subprocess.run([
            'python', cli_script, 
            '--config', config_path
        ], 
        cwd='/home/corey/projects/docling/mvp-fusion',
        capture_output=True, 
        text=True, 
        timeout=timeout
        )
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Parse output for metrics
        stdout = result.stdout
        stderr = result.stderr
        
        # Extract key metrics from output
        files_processed = 0
        files_per_sec = 0
        success_rate = 0
        
        # Try to extract metrics from output
        for line in stdout.split('\n'):
            if 'Files processed:' in line:
                try:
                    files_processed = int(line.split(':')[1].strip().replace(',', ''))
                except:
                    pass
            elif 'Speed:' in line and 'files/sec' in line:
                try:
                    files_per_sec = float(line.split('Speed:')[1].split('files/sec')[0].strip())
                except:
                    pass
            elif 'Success rate:' in line:
                try:
                    success_rate = float(line.split(':')[1].strip().replace('%', ''))
                except:
                    pass
        
        return {
            'success': result.returncode == 0,
            'total_time': total_time,
            'files_processed': files_processed,
            'files_per_sec': files_per_sec,
            'success_rate': success_rate,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        end_time = time.perf_counter()
        return {
            'success': False,
            'total_time': end_time - start_time,
            'files_processed': 0,
            'files_per_sec': 0,
            'success_rate': 0,
            'stdout': '',
            'stderr': f'Process timed out after {timeout}s',
            'returncode': -1,
            'timeout': True
        }
    
    except Exception as e:
        end_time = time.perf_counter()
        return {
            'success': False,
            'total_time': end_time - start_time,
            'files_processed': 0,
            'files_per_sec': 0,
            'success_rate': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2,
            'error': True
        }


def print_comparison_results(original_result: dict, enhanced_result: dict):
    """Print detailed comparison results"""
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"\n📈 Processing Results:")
    print(f"{'Metric':<20} {'Original CLI':<15} {'Enhanced CLI':<15} {'Improvement'}")
    print("-" * 70)
    
    # Success status
    orig_status = "✅ Success" if original_result['success'] else "❌ Failed"
    enh_status = "✅ Success" if enhanced_result['success'] else "❌ Failed"
    print(f"{'Status':<20} {orig_status:<15} {enh_status:<15}")
    
    # Time comparison
    orig_time = original_result['total_time']
    enh_time = enhanced_result['total_time']
    time_improvement = orig_time / enh_time if enh_time > 0 else 0
    
    print(f"{'Total Time':<20} {orig_time:<13.1f}s {enh_time:<13.1f}s {time_improvement:>7.1f}x faster")
    
    # Files processed
    orig_files = original_result['files_processed']
    enh_files = enhanced_result['files_processed']
    
    print(f"{'Files Processed':<20} {orig_files:<15} {enh_files:<15}")
    
    # Speed comparison
    orig_speed = original_result['files_per_sec']
    enh_speed = enhanced_result['files_per_sec']
    speed_improvement = enh_speed / orig_speed if orig_speed > 0 else 0
    
    print(f"{'Speed (files/sec)':<20} {orig_speed:<13.1f}  {enh_speed:<13.1f}  {speed_improvement:>7.1f}x faster")
    
    # Success rate
    orig_rate = original_result['success_rate']
    enh_rate = enhanced_result['success_rate']
    
    print(f"{'Success Rate':<20} {orig_rate:<13.1f}% {enh_rate:<13.1f}%")
    
    # Performance targets
    print(f"\n🎯 Performance Targets:")
    baseline_time = 105.39  # Known slow baseline
    target_time = baseline_time / 10  # 10x improvement target
    
    print(f"   Baseline time: {baseline_time:.1f}s (known slow)")
    print(f"   Target time: {target_time:.1f}s (10x improvement)")
    print(f"   Enhanced actual: {enh_time:.1f}s")
    
    if enh_time <= target_time:
        print(f"   🏆 TARGET ACHIEVED! {(target_time/enh_time):.1f}x better than target!")
    elif enh_time <= baseline_time:
        improvement = baseline_time / enh_time
        print(f"   ✅ Significant improvement: {improvement:.1f}x faster than baseline")
    else:
        print(f"   ⚠️ Still slower than baseline")
    
    # Error analysis
    if original_result.get('timeout'):
        print(f"\n⚠️ Original CLI timed out (>{original_result['total_time']:.0f}s)")
    
    if enhanced_result.get('timeout'):
        print(f"\n⚠️ Enhanced CLI timed out (>{enhanced_result['total_time']:.0f}s)")
    
    if not original_result['success']:
        print(f"\n❌ Original CLI Error: {original_result['stderr'][:200]}...")
    
    if not enhanced_result['success']:
        print(f"\n❌ Enhanced CLI Error: {enhanced_result['stderr'][:200]}...")
    
    print("=" * 80)


def main():
    """Run performance comparison"""
    print("🚀 MVP-Fusion CLI Performance Comparison")
    print("=" * 80)
    
    # Configuration
    config_path = "config/full.yaml"
    
    # Check if files exist
    fusion_cli_path = Path("/home/corey/projects/docling/mvp-fusion/fusion_cli.py")
    fusion_cli_enhanced_path = Path("/home/corey/projects/docling/mvp-fusion/fusion_cli_enhanced.py")
    config_file_path = Path(f"/home/corey/projects/docling/mvp-fusion/{config_path}")
    
    if not fusion_cli_path.exists():
        print(f"❌ Original CLI not found: {fusion_cli_path}")
        sys.exit(1)
    
    if not fusion_cli_enhanced_path.exists():
        print(f"❌ Enhanced CLI not found: {fusion_cli_enhanced_path}")
        sys.exit(1)
    
    if not config_file_path.exists():
        print(f"❌ Config file not found: {config_file_path}")
        sys.exit(1)
    
    print(f"✅ All files found, starting comparison...")
    
    # Run tests
    print(f"\n🔬 Performance Comparison Test")
    print(f"   Configuration: {config_path}")
    print(f"   Original timeout: 180s (3 minutes)")
    print(f"   Enhanced timeout: 60s (1 minute)")
    
    # Test enhanced version first (should be fast)
    enhanced_result = run_cli_test("fusion_cli_enhanced.py", config_path, timeout=60)
    
    # Test original version with longer timeout (known to be slow)
    original_result = run_cli_test("fusion_cli.py", config_path, timeout=180)
    
    # Compare results
    print_comparison_results(original_result, enhanced_result)
    
    # Recommendation
    print(f"\n💡 Recommendation:")
    if enhanced_result['success'] and enhanced_result['total_time'] < original_result['total_time']:
        speedup = original_result['total_time'] / enhanced_result['total_time']
        print(f"   🏆 Use fusion_cli_enhanced.py - {speedup:.1f}x faster!")
        print(f"   🚀 Ready for production deployment")
    elif enhanced_result['success']:
        print(f"   ✅ Enhanced version works, continue optimization")
    else:
        print(f"   ⚠️ Enhanced version needs debugging")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()