#!/bin/bash
# Second reduce pass for the 3010s: produces the files the automatic
# post-processing in run_abq_V18_list.sh leaves out (it defaults to B=n and
# I*/TP*/DEFC* off, writing only A/A2/C/C2/D).
#
# Produces per sim: B, C, C2, I1_3002, I2_3002, I3_BFS_3002,
#                   TP1, TP2, TP2_L, DEFC1, DEFC2
# These are what SIM_3010s_shear_localization.ipynb plots.
#
# Usage:  bash H001_sh_files/reduce_3010s.sh "<sim list>" [parallel]
#   e.g.  bash H001_sh_files/reduce_3010s.sh "3010 3011 3013 3014" 4
set -u
PY=/home/fruffini/.conda/envs/Fenv/bin/python
SIMS=${1:?usage: reduce_3010s.sh "<sims>" [parallel]}
PAR=${2:-1}
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
mkdir -p logs Temp/reduce_inputs

gen() {                       # 48 answers, in the order Reduce_resultsV5 prompts
  printf "%s\n%s\n" "$1" "$1"
  printf "n\nn\ny\ny\ny\nn\n"            # A A2 B C C2 D
  printf "n\nn\n0\n0\n"                  # T1 T2 T1_ini T1_fin
  printf "n\nn\nn\n0\n0\n1\n"            # J1 J2 J3 J_ini J_fin J_alg
  printf "n\nn\nn\n0\n0\n1\n"            # H1 H2 H3 H_ini H_fin H_alg
  printf "y\ny\ny\n3002\n3002\n2\n"      # I1 I2 I3 I_ini I_fin I_alg(2=BFS)
  printf "n\nn\nn\n0\n0\n1\n"            # K1 K2 K3 K_ini K_fin K_alg
  printf "n\nn\n0\n0\n"                  # Q1 Q2 Q_ini Q_fin
  printf "y\ny\ny\ny\nn\nn\n1\n10\n"     # TP1 TP2 DEFC1 DEFC2 E DELETE_CSV N_WORKERS MAX_MEM
}

run_one() {
  local s=$1 f=Temp/reduce_inputs/reduce_inputs_${1}.txt
  if [[ ! -f I001_Results/RES_SIM_${s}.csv ]]; then
    printf "SIM %s: no RES_SIM_%s.csv -- solve/extract it first, skipping\n" "$s" "$s" >&2; return 1
  fi
  gen "$s" > "$f"
  printf "SIM %s: reducing -> logs/SIM_%s_reduce_full.log\n" "$s" "$s"
  $PY -m A001_functions.Reduce_resultsV5 < "$f" > "logs/SIM_${s}_reduce_full.log" 2>&1
  printf "SIM %s: done (exit %s)\n" "$s" "$?"
}

n=0
for s in $SIMS; do
  run_one "$s" &
  n=$((n+1))
  if (( n % PAR == 0 )); then wait; fi
done
wait
printf "All requested reductions finished.\n"
