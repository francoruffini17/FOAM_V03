#!/usr/bin/env bash
# Solve, extract, reduce, and run common refined near-zero eigen replays.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

abq_cmd="${ABQ_CMD:-/usr/bin/abq}"
cpus="${CPUS:-10}"
eigen_workers="${EIGEN_WORKERS:-8}"
reduce_workers="${REDUCE_WORKERS:-8}"
max_memory_gb="${MAX_MEMORY_GB:-50}"

# SIM_5150 uses 4 subdivisions in each base interval after t=0.84.
# 12 subdivisions give every family 3x finer late sampling than SIM_5150.
families=(6000 6010 6020 6030 6040)
late_refine=12

for first in "${families[@]}"; do
    last=$((first + 9))
    for sim in $(seq "$first" "$last"); do
        result_dir="I001_Results/LITE/SIM_${sim}"
        odb_path="E001_Simulations/SIM_${sim}/SIM_${sim}.odb"
        csv_path="I001_Results/RES_SIM_${sim}_LITE.csv.gz"

        if [[ ! -s "$result_dir/curves.npz" || ! -s "$result_dir/geometry.npz" || ! -s "$result_dir/metadata.json" ]]; then
            if [[ ! -s "$csv_path" ]]; then
                if [[ ! -s "$odb_path" ]]; then
                    echo "SIM_${sim}: solving main physical run"
                    (cd "E001_Simulations/SIM_${sim}" && "$abq_cmd" \
                        "job=SIM_${sim}" "cpus=${cpus}" double interactive)
                fi
                echo "SIM_${sim}: extracting lite histories"
                "$abq_cmd" python A001_functions/abq_extract_lite.py \
                    "$sim" "$sim" --results-folder I001_Results --workers 1
            fi
            echo "SIM_${sim}: reducing reaction force, f, and geometry"
            python3 -m A001_functions.Reduce_results_lite \
                "$sim" "$sim" --n-workers "$reduce_workers" \
                --max-memory-gb "$max_memory_gb"
        fi

        if [[ -s "$result_dir/mode0.npz" && -s "$result_dir/spectrum.npz" ]]; then
            echo "SIM_${sim}: refined eigen outputs already exist; skipping replay"
            continue
        fi
        echo "SIM_${sim}: eigen replay, 3x finer late sampling than SIM_5150"
        ABQ_CMD="$abq_cmd" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
            MPLCONFIGDIR="/tmp/foam_6000_matplotlib" \
            python3 -u -m A001_functions.stiffness_eigen \
            "$sim" 400 1.0 "$cpus" 4 "$eigen_workers" 1 \
            --lite --late-start 0.84 --late-refine "$late_refine"
    done
done

echo 'SIM 6000--6049 lite curves, geometry, metadata, and eigen spectra complete.'
