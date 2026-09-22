#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

REDUCE_OPTIONS=(
  A=y A2=y B=y C=y C2=y D=n
  T1=n T2=n T1_ini=0 T1_fin=0
  J1=n J2=n J3=n J_ini=0 J_fin=0 J_alg=1
  H1=n H2=n H3=n H_ini=0 H_fin=0 H_alg=1
  I1=y I2=y I3=y I_ini=3002 I_fin=3002 I_alg=2
  K1=n K2=n K3=n K_ini=0 K_fin=0 K_alg=1
  Q1=n Q2=n Q_ini=0 Q_fin=0
  E=n TP1=y TP2=y DEFC1=y DEFC2=y
  DELETE_CSV=y N_WORKERS=40 MAX_MEMORY_GB=50
  RESUME=y
)

echo "Reducing SIM_5120 and SIM_5126 from their existing CSV files..."
for sim in 5120 5126; do
  "$SCRIPT_DIR/run_general.sh" "$sim" "$sim" \
    RUN_REDUCE=y \
    -par_red=1 \
    "${REDUCE_OPTIONS[@]}"
done

echo "Rerunning, extracting, and reducing SIM_5125..."
"$SCRIPT_DIR/run_general.sh" 5125 5125 \
  RUN_SIMULATIONS=y \
  RUN_ABQ=y \
  RUN_REDUCE=y \
  CONTINUE_ON_SOLVER_ERROR=n \
  cpus=10 \
  ABQ_CMD=/usr/bin/abq \
  DELETE_ODB=n \
  MOVE_FOLDER=n \
  "${REDUCE_OPTIONS[@]}"

LOCAL_SIM_5123="$ROOT_DIR/E001_Simulations/SIM_5123"
MOVED_SIM_5123="/data/Franco/FOAM_V03_Results/SIM_5123"
FINISHED_INP_5123="$ROOT_DIR/I001_Results/finished_simulations/SIM_5123.inp"

echo "Preparing SIM_5123 for EIG/EIGV generation..."
if [[ ! -d "$LOCAL_SIM_5123" ]]; then
  if [[ ! -d "$MOVED_SIM_5123" ]]; then
    echo "Error: SIM_5123 was not found locally or at $MOVED_SIM_5123" >&2
    exit 1
  fi
  mv "$MOVED_SIM_5123" "$LOCAL_SIM_5123"
fi

if [[ ! -f "$LOCAL_SIM_5123/SIM_5123.inp" ]]; then
  if [[ ! -f "$FINISHED_INP_5123" ]]; then
    echo "Error: Missing input file $FINISHED_INP_5123" >&2
    exit 1
  fi
  cp "$FINISHED_INP_5123" "$LOCAL_SIM_5123/SIM_5123.inp"
fi

echo "Generating the missing EIG and EIGV files for SIM_5123..."
"$SCRIPT_DIR/run_general.sh" 5123 5123 \
  RUN_EIGEN=y \
  cpus=10 \
  ABQ_CMD=/usr/bin/abq \
  EIGEN_SEGMENTS=400 \
  N_EIGENVALUES=20 \
  EIGEN_WORKERS=8 \
  EIGENVECTORS=y

if [[ -d "$MOVED_SIM_5123" ]]; then
  echo "Error: Cannot move SIM_5123 back because $MOVED_SIM_5123 already exists." >&2
  exit 1
fi
mv "$LOCAL_SIM_5123" "$MOVED_SIM_5123"

echo "Verifying reduction outputs..."
missing=0
for sim in 5120 5125 5126; do
  for suffix in \
    A A2 B C C2 DEFC1 DEFC2 TP1 TP2 TP2_L \
    I1_3002 I2_3002 I3_BFS_3002
  do
    output="I001_Results/DATA_PICK_${sim}_${suffix}.pkl"
    if [[ ! -s "$output" ]]; then
      echo "MISSING: $output" >&2
      missing=1
    fi
  done
done

for output in \
  I001_Results/DATA_PICK_5123_EIG.json \
  I001_Results/DATA_PICK_5123_EIGV.pkl
do
  if [[ ! -s "$output" ]]; then
    echo "MISSING: $output" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "One or more expected outputs are still missing." >&2
  exit 1
fi

eig_records="$(rg -c '"matrix_index"' I001_Results/DATA_PICK_5123_EIG.json)"
if [[ "$eig_records" -ne 401 ]]; then
  echo "Error: SIM_5123 EIG contains $eig_records records; expected 401." >&2
  exit 1
fi

echo "All missing reduction and EIG/EIGV outputs are complete."
