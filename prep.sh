#!/bin/sh

echo "[INFO] Running Experiment Preparation"
echo "[INFO]"
echo "[INFO] Build Cloud Provider Benchamrk Query $1"

cd ../dependencies/flink-benchmarks/ && python3 build.py $1





