#!/bin/bash
# Queued behind the January-October 2026 run (login node; needs internet). Starts once that run has finished
# finding pairs, then collects:
#   1. July-December 2025 for the original 15 communities
#   2. July 2025 to November 2026 for the four added communities (config.MORE_SUBREDDITS)
# with downloads, pair finding and hourly labeling running alongside, as in the first run.
cd ~/mozar
until [ -f logs/pairs_done ]; do sleep 300; done
rm -f logs/downloads_done logs/pairs_done
echo "next run started $(date)" >> logs/next_run.log
(
  MOZAR_AFTER=2025-07-01 MOZAR_BEFORE=2026-01-01 .venv/bin/python -u collect.py posts
  MOZAR_SUBREDDITS=mildlyinteresting,HistoryPorn,isthisAI,RealOrAI MOZAR_AFTER=2025-07-01 MOZAR_BEFORE=2026-11-08 \
    .venv/bin/python -u collect.py posts
) >> logs/next_run.log 2>&1 &
POSTS=$!
sbatch jobs/pairs.sbatch
jobs/long_run.sh "$POSTS"
echo "next run finished $(date)" >> logs/next_run.log
