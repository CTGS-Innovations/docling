#!/bin/bash

echo "Workers,Performance(pages/sec)" > perf_results.csv

for w in $(seq 1 16); do
  echo "Running with $w workers..."
  perf=$(python fusion_cli.py \
    --config config/fusion_config.yaml \
    --convert-only \
    --extractor highspeed_markdown_general \
    --workers $w | grep "PERFORMANCE" | awk '{print $2 $3}')
  
  echo "$w,$perf" | tee -a perf_results.csv
done

