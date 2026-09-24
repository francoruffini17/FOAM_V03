#!/usr/bin/env bash
# Recompute SIM 5150--5159 with four nearby stiffness modes and finer late samples.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
mkdir -p logs

for sim in {5150..5159}; do
    result_dir="I001_Results/LITE/SIM_${sim}"
    if [[ -s "$result_dir/mode0.npz" && -s "$result_dir/spectrum.npz" ]]; then
        echo "SIM_${sim}: existing eigen outputs found; skipping"
        continue
    fi
    echo "SIM_${sim}: starting refined eigen replay"
    ABQ_CMD=/usr/bin/abq OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
        MPLCONFIGDIR=/tmp/foam_5150_matplotlib \
        python3 -u -m A001_functions.stiffness_eigen \
        "$sim" 400 1.0 10 4 8 1 --lite --late-start 0.84 --late-refine 4 \
        > "logs/SIM_${sim}_eigen_refined.log" 2>&1
    echo "SIM_${sim}: wrote $result_dir/mode0.npz and spectrum.npz"
done

MPLCONFIGDIR=/tmp/foam_5150_matplotlib \
    python3 Z001_Results_Analizer/analyze_refined_5150.py
echo 'SIM 5150--5159 refined eigen family finished.'
