#!/bin/bash
#SBATCH --job-name=mozar-judge
#SBATCH --partition=nsfq
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=3
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --output=logs/%x_%j.out
# Labeling model on one H100. Reads the model from models/ (compute nodes have no internet).
# Optional: WAIT_FOR=<log file> makes the job wait until that run has written its review page.
cd ~/mozar
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
if [ -n "$WAIT_FOR" ]; then
  until grep -q "review page" "$WAIT_FOR"; do sleep 60; done
fi
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# Stop labeling before the 6-hour limit so the decisions below are always written; the next job continues.
timeout 340m .venv/bin/python -u collect.py judge
.venv/bin/python -u collect.py decide index review
