#!/usr/bin/env bash
# Finish the incomplete lite pipeline products for SIM 5140--5144.
#
# Current recovery plan:
#   - SIM 5144: reduce its already complete RES_SIM_5144_LITE.csv.gz.
#   - SIM 5140--5143: remove stale main Abaqus job outputs (preserving .inp),
#     then run solve -> lite extract -> lite reduce.
#   - Do not rerun eigen extraction: mode0.npz is already complete for all ten
#     members of the SIM 5140 family.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SIMCTL="/Disk_F/SIM_tools/simctl"

if [[ ! -x "$SIMCTL" ]]; then
  echo "ERROR: simctl is not executable at $SIMCTL" >&2
  exit 1
fi

for sim in 5140 5141 5142 5143; do
  input_file="$PROJECT_DIR/E001_Simulations/SIM_${sim}/SIM_${sim}.inp"
  if [[ ! -f "$input_file" ]]; then
    echo "ERROR: required input file is missing: $input_file" >&2
    exit 1
  fi
done

sim5144_csv="$PROJECT_DIR/I001_Results/RES_SIM_5144_LITE.csv.gz"
if [[ ! -f "$sim5144_csv" ]]; then
  echo "ERROR: SIM 5144 lite CSV is missing: $sim5144_csv" >&2
  exit 1
fi

cd "$PROJECT_DIR"

echo "[1/3] Reducing the existing complete SIM 5144 lite extraction..."
"$SIMCTL" \
  --project "$PROJECT_DIR" \
  pipeline 5144 \
  --profile lite \
  --steps reduce \
  --parallel-reduce 1 \
  --reduce-options '--n-workers 40 --max-memory-gb 50 --delete-csv'

echo "[2/3] Removing stale main-job outputs for SIM 5140--5143..."
echo "      Input decks and existing lite eigenvalue files are preserved."
"$SIMCTL" \
  --project "$PROJECT_DIR" \
  clean 5140 5143 --yes

echo "[3/3] Running solve, lite extraction, and lite reduction for SIM 5140--5143..."
"$SIMCTL" \
  --project "$PROJECT_DIR" \
  pipeline \
  --sim 5140 --sim 5141 --sim 5142 --sim 5143 \
  --profile lite \
  --steps solve,extract,reduce \
  --cpus 10 \
  --abq-cmd /usr/bin/abq \
  --parallel-simulations 2 \
  --parallel-extract 2 \
  --parallel-reduce 1 \
  --delay 120 \
  --delete-odb \
  --reduce-options '--n-workers 40 --max-memory-gb 50 --delete-csv'

echo "SIM 5140--5144 recovery completed successfully."
