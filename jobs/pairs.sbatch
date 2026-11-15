#!/bin/bash
#SBATCH --job-name=mozar-pairs
#SBATCH --partition=cpuqs
#SBATCH --cpus-per-task=3
#SBATCH --mem=16G
#SBATCH --time=2-00:00:00
#SBATCH --output=logs/%x_%j.out
# Pair finding and pixel comparison on a CPU node, repeated while images are still arriving.
# Each pass only handles new images and new pairs. Stops after the pass that follows logs/downloads_done.
cd ~/mozar
while :; do
  last=$([ -f logs/downloads_done ] && echo 1)
  .venv/bin/python -u collect.py pairs diff review
  [ -n "$last" ] && break
  sleep 300
done
touch logs/pairs_done
