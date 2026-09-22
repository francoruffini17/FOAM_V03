#!/usr/bin/env bash
set -euo pipefail

/Disk_F/SIM_tools/simctl \
  --project /Disk_F/FOAM_V03 \
  pipeline 5001 \
  --profile lite \
  --steps solve,extract,eigen,reduce,video \
  --continue-on-solver-error \
  --parallel-simulations 2 \
  --parallel-extract 2 \
  --parallel-eigen 2 \
  --parallel-reduce 2 \
  --parallel-video 2 \
  --delay 120 \
  --cpus 10 \
  --abq-cmd /usr/bin/abq \
  --eigen-segments 400 \
  --eigenvectors \
  --properties Video_properties_3200 \
  --delete-odb \
  --move-dest /data/Franco/FOAM_V03_Results \
  --reduce-options '--n-workers 40 --max-memory-gb 50 --delete-csv'
