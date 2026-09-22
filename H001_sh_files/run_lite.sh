#!/usr/bin/env bash
# Compact extraction/reduction pipeline for Video_3200.

set -euo pipefail

if [[ $# -ne 2 || ! "$1" =~ ^[0-9]+$ || ! "$2" =~ ^[0-9]+$ || "$1" -gt "$2" ]]; then
  echo "Usage: $0 SIM_START SIM_END" >&2
  echo "Optional environment: RUN_EIGEN=y CPUS=10 EXTRACT_WORKERS=1 EIGEN_SEGMENTS=400 EIGEN_WORKERS=8 REDUCE_WORKERS=1 MAX_MEMORY_GB=50 DELETE_ODB=n DELETE_CSV=n" >&2
  exit 2
fi

START="$1"
END="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

ABQ_CMD="${ABQ_CMD:-/usr/bin/abq}"
RUN_EIGEN="${RUN_EIGEN:-y}"
CPUS="${CPUS:-10}"
EXTRACT_WORKERS="${EXTRACT_WORKERS:-1}"
EIGEN_SEGMENTS="${EIGEN_SEGMENTS:-400}"
EIGEN_WORKERS="${EIGEN_WORKERS:-8}"
REDUCE_WORKERS="${REDUCE_WORKERS:-1}"
MAX_MEMORY_GB="${MAX_MEMORY_GB:-50}"
DELETE_ODB="${DELETE_ODB:-n}"
DELETE_CSV="${DELETE_CSV:-n}"

extract_args=(
  python A001_functions/abq_extract_lite.py "$START" "$END"
  --results-folder I001_Results --workers "$EXTRACT_WORKERS"
)
[[ "$DELETE_ODB" == y ]] && extract_args+=(--delete-odb)

echo "Extracting filtered compressed CSV data for SIM_${START}..SIM_${END}..."
"$ABQ_CMD" "${extract_args[@]}"

CONDA_SH=""
for candidate in \
  "${CONDA_EXE:+$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh}" \
  "$HOME/miniconda3/etc/profile.d/conda.sh" \
  "$HOME/anaconda3/etc/profile.d/conda.sh" \
  /opt/anaconda3/etc/profile.d/conda.sh
do
  if [[ -n "$candidate" && -f "$candidate" ]]; then
    CONDA_SH="$candidate"
    break
  fi
done
if [[ -n "$CONDA_SH" ]]; then
  # shellcheck source=/dev/null
  source "$CONDA_SH"
  conda activate Fenv
fi

reduce_args=(
  -m A001_functions.Reduce_results_lite "$START" "$END"
  --n-workers "$REDUCE_WORKERS" --max-memory-gb "$MAX_MEMORY_GB"
)
[[ "$DELETE_CSV" == y ]] && reduce_args+=(--delete-csv)

echo "Reducing to compact Video_3200 datasets..."
python "${reduce_args[@]}"

if [[ "$RUN_EIGEN" == y ]]; then
  echo "Generating compressed smallest-eigenmode datasets..."
  for sim in $(seq "$START" "$END"); do
    ABQ_CMD="$ABQ_CMD" python -m A001_functions.stiffness_eigen \
      "$sim" "$EIGEN_SEGMENTS" 1.0 "$CPUS" 1 "$EIGEN_WORKERS" 1 --lite
  done
fi

echo "Lite pipeline complete. Render with:"
echo "python -m A001_functions.Video_executorV20 --sim-num SIM --properties-file Video_properties_3200"
