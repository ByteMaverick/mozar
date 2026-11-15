#!/bin/bash
# Login-node side of a long run (needs internet). Three things run side by side:
#   collect.py posts   fetches posts from the archive            (already running; its pid is $1)
#   this script        downloads images for the posts fetched so far, and queues the H100 labeling job hourly
#   jobs/pairs.sbatch  finds pairs and compares pixels on a CPU node (submit it separately)
# Usage: jobs/long_run.sh <pid of the running "collect.py posts">
cd ~/mozar
get() { .venv/bin/python -u -c "import collect; collect.image_posts(); collect.fetch_images()" >> logs/images.log 2>&1; }

( until [ -f logs/pairs_done ]; do
    sleep 3600
    squeue -u "$USER" -h -n mozar-judge | grep -q . || sbatch jobs/judge.sbatch
  done
  sbatch jobs/judge.sbatch ) &

while pgrep -f "collect.fetch_images" > /dev/null; do sleep 20; done   # let a download pass already running finish
while kill -0 "$1" 2>/dev/null; do get; sleep 60; done
get
touch logs/downloads_done
