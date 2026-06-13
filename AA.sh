cd /Disk_F/FOAM_V03

source /opt/anaconda3/etc/profile.d/conda.sh && conda activate Fenv

# Delete stale G_eff frames
for SIM in 504 604; do
  rm -rf I002_Videos/Video_1001/SIM_${SIM}/frames_FH30 \
         I002_Videos/Video_1001/SIM_${SIM}/frames_FI300{1..5}
done

# Re-create video 1001
python -m A001_functions.Video_executor 504 1001
python -m A001_functions.Video_executor 604 1001

mkdir -p logs

# Function to run Reduce_resultsV5
reduce_branch () {  # $1 = sim number, $2 = H or I
  local sim=$1 fam=$2
  local H2=n H3=n I2=n I3=n

  if [ "$fam" = "H" ]; then
    H2=y
    H3=y
  else
    I2=y
    I3=y
  fi

  printf '%s\n' "$sim" "$sim" \
      n n n n n n \
      n n 0 0 \
      n n n 0 0 1 \
      n "$H2" "$H3" 3001 3005 2 \
      n "$I2" "$I3" 3001 3005 2 \
      n n n 0 0 1 \
      n 50 50 \
    | python -m A001_functions.Reduce_resultsV5 > "logs/SIM_${sim}_reduce_${fam}.log" 2>&1

  echo "DONE: SIM $sim branch $fam (exit $?)"
}

# Run four reduce jobs in parallel
reduce_branch 504 H &
reduce_branch 504 I &
reduce_branch 604 H &
reduce_branch 604 I &

wait