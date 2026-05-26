#!/bin/bash

source "/opt/anaconda3/etc/profile.d/conda.sh" || {
    printf "Error: Failed to source conda initialization script.\n" >&2
    exit 1
}

if ! conda activate Fenv; then
    printf "Error: Failed to activate conda environment 'Fenv'.\n" >&2
    exit 1
fi

# Make all paths relative to the repository root (parent of this script dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FUNCTIONS_DIR="$ROOT_DIR/A001_functions"

if [[ -d "$ROOT_DIR/E001_Simulations" ]]; then
    SIMS_DIR="$ROOT_DIR/E001_Simulations"
else
    SIMS_DIR="$ROOT_DIR"
fi

# Ensure we operate from the repo root regardless of where the script is invoked
cd "$ROOT_DIR" || { printf "Error: Cannot cd to repo root %s\n" "$ROOT_DIR" >&2; exit 1; }

# Help Python/Abaqus find modules inside A001_functions and the root
export PYTHONPATH="$FUNCTIONS_DIR:$ROOT_DIR:${PYTHONPATH:-}"

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    cat >&2 <<EOF
Usage: $0 sim_num_ini sim_num_fin [OPTION=VALUE ...]
   or: $0 -list=<file> [OPTION=VALUE ...]

Positional arguments:
  sim_num_ini           First simulation number (integer)
  sim_num_fin           Last  simulation number (integer, >= sim_num_ini)

List mode:
  -list=<file>          Read simulation numbers (one per line) from <file>.
                        Relative paths are resolved from the script directory.

Step flags (default: n):
  RUN_ABQ=y|n           Run ABQ ODB extraction  (abq python abq_scriptV9.py)
  RUN_REDUCE=y|n        Run Reduce_resultsV5
  RUN_VIDEO=y|n         Run video creation

Parallelism (default: 1):
  -par_abq=N            Max parallel ABQ extraction jobs
  -par_red=N            Max parallel Reduce jobs
  -par_vid=N            Max parallel Video jobs

ABQ extraction options:
  DELETE_ODB=y|n        Delete ODB after extraction (default: n)

Reduce results output options (defaults shown):
  A=y  A2=y  B=y  C=y  C2=y  D=y
  T1=n T2=n T1_ini=0 T1_fin=0
  J1=y J2=y J3=y J_ini=0 J_fin=0 J_alg=1
  H1=y H2=y H3=y H_ini=0 H_fin=0 H_alg=1
  I1=y I2=y I3=y I_ini=0 I_fin=0 I_alg=1
  K1=y K2=y K3=y K_ini=0 K_fin=0 K_alg=1
  DELETE_CSV=n  N_WORKERS=1  MAX_MEMORY_GB=10

Video options:
  VIDEOS_PROPERTIES_FILES=<name>   (default: Video_properties0001)

Other options:
  MOVE_FOLDER=y|n       Move simulation folder after processing (default: n)
EOF
    exit 1
}

# ---------------------------------------------------------------------------
# Parse positional arguments
# ---------------------------------------------------------------------------
if [[ "$#" -lt 1 ]]; then
    usage
fi

LIST_FILE=""
if [[ "$1" =~ ^-list=(.+)$ ]]; then
    LIST_FILE="${BASH_REMATCH[1]}"
    shift
else
    if [[ "$#" -lt 2 ]]; then
        usage
    fi
    START=$1
    END=$2
    shift 2
    if ! [[ "$START" =~ ^[0-9]+$ && "$END" =~ ^[0-9]+$ && "$START" -le "$END" ]]; then
        printf "Error: sim_num_ini and sim_num_fin must be valid positive integers, and sim_num_ini <= sim_num_fin.\n" >&2
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
RUN_ABQ="n"
RUN_REDUCE="n"
RUN_VIDEO="n"

PAR_ABQ=1
PAR_RED=1
PAR_VID=1

DELETE_ODB="n"
MOVE_FOLDER="n"
VIDEOS_PROPERTIES_FILES="Video_properties0001"

declare -A OUTPUT_OPTIONS=(
    ["A"]="y"
    ["A2"]="y"
    ["B"]="y"
    ["C"]="y"
    ["C2"]="y"
    ["D"]="y"
    ["T1"]="n"
    ["T2"]="n"
    ["T1_ini"]="0"
    ["T1_fin"]="0"
    ["J1"]="y"
    ["J2"]="y"
    ["J3"]="y"
    ["J_ini"]="0"
    ["J_fin"]="0"
    ["J_alg"]="1"
    ["H1"]="y"
    ["H2"]="y"
    ["H3"]="y"
    ["H_ini"]="0"
    ["H_fin"]="0"
    ["H_alg"]="1"
    ["I1"]="y"
    ["I2"]="y"
    ["I3"]="y"
    ["I_ini"]="0"
    ["I_fin"]="0"
    ["I_alg"]="1"
    ["K1"]="y"
    ["K2"]="y"
    ["K3"]="y"
    ["K_ini"]="0"
    ["K_fin"]="0"
    ["K_alg"]="1"
    ["DELETE_CSV"]="n"
    ["N_WORKERS"]="1"
    ["MAX_MEMORY_GB"]="10"
)

# ---------------------------------------------------------------------------
# Parse optional KEY=VALUE and -flag=VALUE arguments
# ---------------------------------------------------------------------------
for arg in "$@"; do
    # Handle -par_* flags (with leading dash)
    if [[ "$arg" =~ ^-par_abq=([0-9]+)$ ]]; then
        PAR_ABQ="${BASH_REMATCH[1]}"
        [[ "$PAR_ABQ" -gt 0 ]] || { printf "Error: -par_abq must be > 0\n" >&2; exit 1; }
        continue
    elif [[ "$arg" =~ ^-par_red=([0-9]+)$ ]]; then
        PAR_RED="${BASH_REMATCH[1]}"
        [[ "$PAR_RED" -gt 0 ]] || { printf "Error: -par_red must be > 0\n" >&2; exit 1; }
        continue
    elif [[ "$arg" =~ ^-par_vid=([0-9]+)$ ]]; then
        PAR_VID="${BASH_REMATCH[1]}"
        [[ "$PAR_VID" -gt 0 ]] || { printf "Error: -par_vid must be > 0\n" >&2; exit 1; }
        continue
    fi

    key="${arg%%=*}"
    value="${arg#*=}"

    case "$key" in
        RUN_ABQ)
            [[ "$value" == "y" || "$value" == "n" ]] && RUN_ABQ="$value" || printf "Warning: Ignoring invalid RUN_ABQ=%s\n" "$value" >&2
            ;;
        RUN_REDUCE)
            [[ "$value" == "y" || "$value" == "n" ]] && RUN_REDUCE="$value" || printf "Warning: Ignoring invalid RUN_REDUCE=%s\n" "$value" >&2
            ;;
        RUN_VIDEO)
            [[ "$value" == "y" || "$value" == "n" ]] && RUN_VIDEO="$value" || printf "Warning: Ignoring invalid RUN_VIDEO=%s\n" "$value" >&2
            ;;
        DELETE_ODB)
            [[ "$value" == "y" || "$value" == "n" ]] && DELETE_ODB="$value" || printf "Warning: Ignoring invalid DELETE_ODB=%s\n" "$value" >&2
            ;;
        MOVE_FOLDER)
            [[ "$value" == "y" || "$value" == "n" ]] && MOVE_FOLDER="$value" || printf "Warning: Ignoring invalid MOVE_FOLDER=%s\n" "$value" >&2
            ;;
        VIDEOS_PROPERTIES_FILES)
            VIDEOS_PROPERTIES_FILES="$value"
            ;;
        N_WORKERS)
            [[ "$value" =~ ^[0-9]+$ ]] && OUTPUT_OPTIONS[N_WORKERS]="$value" || printf "Warning: Ignoring invalid N_WORKERS=%s\n" "$value" >&2
            ;;
        MAX_MEMORY_GB)
            [[ "$value" =~ ^[0-9]+(\.[0-9]+)?$ ]] && OUTPUT_OPTIONS[MAX_MEMORY_GB]="$value" || printf "Warning: Ignoring invalid MAX_MEMORY_GB=%s\n" "$value" >&2
            ;;
        *)
            if [[ -n "${OUTPUT_OPTIONS[$key]+_}" ]]; then
                OUTPUT_OPTIONS[$key]="$value"
            else
                printf "Warning: Ignoring unknown or invalid option %s\n" "$arg" >&2
            fi
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Sanity check: at least one step must be enabled
# ---------------------------------------------------------------------------
if [[ "$RUN_ABQ" == "n" && "$RUN_REDUCE" == "n" && "$RUN_VIDEO" == "n" ]]; then
    printf "Error: No processing steps enabled. Set at least one of RUN_ABQ=y, RUN_REDUCE=y, or RUN_VIDEO=y.\n" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Semaphore helpers – use named pipes (FIFOs) as counting semaphores
# ---------------------------------------------------------------------------
create_semaphore() {
    local name="$1" capacity="$2"
    local fifo="/tmp/.sem_${name}_$$"
    mkfifo "$fifo"
    eval "exec {${name}_fd}<>\"$fifo\""
    rm -f "$fifo"   # unlink; the fd keeps it alive

    local i
    for ((i = 0; i < capacity; i++)); do
        eval "printf '\\n' >&\${${name}_fd}"
    done
}

acquire_semaphore() {
    local name="$1"
    eval "read -u \${${name}_fd}"
}

release_semaphore() {
    local name="$1"
    eval "printf '\\n' >&\${${name}_fd}"
}

# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------
run_abq_extraction() {
    local sim="$1"
    local sim_number
    sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local sim_path="$SIMS_DIR/$sim"
    local log_folder="logs"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist. Skipping ABQ extraction.\n" "$sim_path" >&2
        return 1
    fi

    printf "ABQ extraction: Starting for %s ...\n" "$sim"

    printf "%s\n%s\nI001_Results\n%s\n" "$sim_number" "$sim_number" "$DELETE_ODB" \
        | abq python "$FUNCTIONS_DIR/abq_scriptV9.py" > "$log_folder/SIM_${sim_number}.log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: ABQ extraction for %s failed. See logs/SIM_%s.log\n" "$sim" "$sim_number" >&2
    elif [[ ! -f "I001_Results/RES_SIM_${sim_number}.csv" ]]; then
        printf "Error: Expected results file RES_SIM_%s.csv was not created.\n" "$sim_number" >&2
    else
        printf "ABQ extraction: %s completed successfully.\n" "$sim"
    fi
    return "$status"
}

run_reduce() {
    local sim="$1"
    local sim_number
    sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local log_folder="logs"

    printf "Reduce: Starting for %s ...\n" "$sim"

    local reduce_input_file="reduce_inputs_${sim_number}.txt"
    {
        printf "%s\n%s\n" "$sim_number" "$sim_number"

        for key in A A2 B C C2 D T1 T2 T1_ini T1_fin J1 J2 J3 J_ini J_fin J_alg H1 H2 H3 H_ini H_fin H_alg I1 I2 I3 I_ini I_fin I_alg K1 K2 K3 K_ini K_fin K_alg DELETE_CSV N_WORKERS MAX_MEMORY_GB; do
            printf "%s\n" "${OUTPUT_OPTIONS[$key]}"
        done
    } > "$reduce_input_file"

    python -m A001_functions.Reduce_resultsV5 < "$reduce_input_file" > "$log_folder/SIM_${sim_number}_reduce.log" 2>&1
    local status=$?

    rm -f "$reduce_input_file"

    if [[ $status -ne 0 ]]; then
        printf "Error: Reduce for %s failed. See logs/SIM_%s_reduce.log\n" "$sim" "$sim_number" >&2
    else
        printf "Reduce: %s completed successfully.\n" "$sim"
    fi
    return "$status"
}


run_video() {
    local sim="$1"
    local sim_number
    sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local video_log="SIM_${sim_number}_video.log"

    printf "Video: Starting for %s ...\n" "$sim"

    printf "%s\n%s\n" "$sim_number" "$VIDEOS_PROPERTIES_FILES" \
        | python -m A001_functions.Video_executor > "logs/$video_log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: Video creation for %s failed. See logs/%s\n" "$sim" "$video_log" >&2
    else
        printf "Video: %s completed successfully.\n" "$sim"
    fi
    return "$status"
}

move_folder() {
    local sim="$1"
    local sim_path="$SIMS_DIR/$sim"
    local sim_number
    sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist. Skipping move.\n" "$sim_path" >&2
        return 1
    fi

    local realpath_sim
    if ! realpath_sim=$(realpath "$sim_path"); then
        printf "Error: Unable to resolve real path for %s\n" "$sim_path" >&2
        return 1
    fi

    local target_dir="/data/Franco/$(basename "$(dirname "$realpath_sim")")_completed"
    local dest_dir="$target_dir/SIM_${sim_number}"

    mkdir -p "$target_dir"

    if [[ -d "$dest_dir" ]]; then
        rm -rf "$dest_dir"
        printf "Warning: Existing directory %s was removed.\n" "$dest_dir" >&2
    fi

    mv "$sim_path" "$dest_dir"
    printf "Moved %s to %s\n" "$sim_path" "$dest_dir"
}

# ---------------------------------------------------------------------------
# Per-simulation pipeline (runs in a sub-shell)
# ---------------------------------------------------------------------------
process_simulation() {
    local sim="$1"

    # --- ABQ extraction (needs simulation directory) ---
    if [[ "$RUN_ABQ" == "y" ]]; then
        acquire_semaphore sem_abq
        run_abq_extraction "$sim"
        release_semaphore sem_abq
    fi

    # --- Reduce results (works from simulation number, no directory needed) ---
    if [[ "$RUN_REDUCE" == "y" ]]; then
        acquire_semaphore sem_red
        run_reduce "$sim"
        release_semaphore sem_red
    fi

    # --- Video creation (works from simulation number, no directory needed) ---
    if [[ "$RUN_VIDEO" == "y" ]]; then
        acquire_semaphore sem_vid
        run_video "$sim"
        release_semaphore sem_vid
    fi

    # --- Move folder (needs simulation directory) ---
    if [[ "$MOVE_FOLDER" == "y" ]]; then
        move_folder "$sim"
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    mkdir -p I001_Results logs

    # Create semaphores with the requested capacities
    create_semaphore sem_abq "$PAR_ABQ"
    create_semaphore sem_red "$PAR_RED"
    create_semaphore sem_vid "$PAR_VID"

    # Total max concurrency = max of the three parallelisms (each pipeline
    # is self-throttled by the semaphores, so we can launch all at once).
    local MAX_CONCURRENT=$(( PAR_ABQ > PAR_RED ? PAR_ABQ : PAR_RED ))
    MAX_CONCURRENT=$(( MAX_CONCURRENT > PAR_VID ? MAX_CONCURRENT : PAR_VID ))

    local -a PIDS=()
    local -a SIM_LIST=()
    local i sim sim_path

    # Build the list of zero-padded simulation numbers
    if [[ -n "$LIST_FILE" ]]; then
        local list_path
        if [[ "$LIST_FILE" = /* ]]; then
            list_path="$LIST_FILE"
        else
            list_path="$SCRIPT_DIR/$LIST_FILE"
        fi
        if [[ ! -f "$list_path" ]]; then
            printf "Error: List file '%s' not found.\n" "$list_path" >&2
            exit 1
        fi
        while IFS= read -r line || [[ -n "$line" ]]; do
            line="${line//[[:space:]]/}"
            [[ -z "$line" || "$line" == \#* ]] && continue
            if ! [[ "$line" =~ ^[0-9]+$ ]]; then
                printf "Warning: Skipping invalid entry '%s' in list file.\n" "$line" >&2
                continue
            fi
            SIM_LIST+=("$(printf "%03d" "$line")")
        done < "$list_path"
        if [[ "${#SIM_LIST[@]}" -eq 0 ]]; then
            printf "Error: No valid simulation numbers found in '%s'.\n" "$list_path" >&2
            exit 1
        fi
    else
        for i in $(seq -f "%03g" "$START" "$END"); do
            SIM_LIST+=("$i")
        done
    fi

    for i in "${SIM_LIST[@]}"; do
        sim="SIM_$i"

        # Only check for simulation directory if ABQ extraction is enabled
        if [[ "$RUN_ABQ" == "y" ]]; then
            sim_path="$SIMS_DIR/$sim"
            if [[ ! -d "$sim_path" ]]; then
                printf "Warning: Simulation directory %s does not exist. Skipping.\n" "$sim_path" >&2
                continue
            fi
        fi

        # Throttle total concurrent sub-shells so we don't spawn hundreds
        while [[ "$(jobs -rp | wc -l)" -ge "$MAX_CONCURRENT" ]]; do
            sleep 1
        done

        process_simulation "$sim" &
        PIDS+=("$!")
    done

    # Wait for everything to finish
    local pid
    for pid in "${PIDS[@]}"; do
        if ! wait "$pid"; then
            printf "Process %s finished with errors.\n" "$pid" >&2
        fi
    done

    printf "All processing completed.\n"
}

trap 'printf "Termination signal received. Exiting...\n" >&2; exit 1' SIGINT SIGTERM

set -o pipefail
main