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
# By convention simulations were moved into E001_Simulations. If that
# directory exists use it, otherwise fall back to repo root so older
# setups still work.
if [[ -d "$ROOT_DIR/E001_Simulations" ]]; then
    SIMS_DIR="$ROOT_DIR/E001_Simulations"
else
    SIMS_DIR="$ROOT_DIR"
fi

# Ensure we operate from the repo root regardless of where the script is invoked
cd "$ROOT_DIR" || { printf "Error: Cannot cd to repo root %s\n" "$ROOT_DIR" >&2; exit 1; }

# Help Python/Abaqus find modules inside A001_functions and the root
export PYTHONPATH="$FUNCTIONS_DIR:$ROOT_DIR:${PYTHONPATH:-}"

if [[ "$#" -lt 3 ]]; then
    printf "Usage: %s start end max_parallel_jobs [OPTION=VALUE ...]\n" "$0" >&2
    exit 1
fi

START=$1
END=$2
MAX_PARALLEL_JOBS=$3
shift 3

if ! [[ "$START" =~ ^[0-9]+$ && "$END" =~ ^[0-9]+$ && "$START" -le "$END" && "$MAX_PARALLEL_JOBS" =~ ^[0-9]+$ && "$MAX_PARALLEL_JOBS" -gt 0 ]]; then
    printf "Error: start, end, and max_parallel_jobs must be valid positive integers, and start must be less than or equal to end.\n" >&2
    exit 1
fi

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

CPUS=15
DELETE_ODB="n"
CREATE_VIDEO="n"
MOVE_FOLDER="n"
VIDEOS_PROPERTIES_FILES="Video_properties0001"

for arg in "$@"; do
    key="${arg%%=*}"
    value="${arg#*=}"

    if [[ -n "${OUTPUT_OPTIONS[$key]}" ]]; then
        OUTPUT_OPTIONS[$key]="$value"
    elif [[ "$key" == "cpus" && "$value" =~ ^[0-9]+$ && "$value" -gt 0 ]]; then
        CPUS="$value"
    elif [[ "$key" == "DELETE_ODB" && ("$value" == "y" || "$value" == "n") ]]; then
        DELETE_ODB="$value"
    elif [[ "$key" == "CREATE_VIDEO" && ("$value" == "y" || "$value" == "n") ]]; then
        CREATE_VIDEO="$value"
    elif [[ "$key" == "MOVE_FOLDER" && ("$value" == "y" || "$value" == "n") ]]; then
        MOVE_FOLDER="$value"
    elif [[ "$key" == "VIDEOS_PROPERTIES_FILES" ]]; then
        VIDEOS_PROPERTIES_FILES="$value"
    elif [[ "$key" == "N_WORKERS" && "$value" =~ ^[0-9]+$ ]]; then
        OUTPUT_OPTIONS[N_WORKERS]="$value"
    elif [[ "$key" == "MAX_MEMORY_GB" && "$value" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        OUTPUT_OPTIONS[MAX_MEMORY_GB]="$value"
    else
        printf "Warning: Ignoring unknown or invalid option %s\n" "$arg" >&2
    fi
done

create_video() {
    local sim_number="$1"
    local video_log="SIM_${sim_number}_video.log"

    printf "%s\n%s\n" "$sim_number" "$VIDEOS_PROPERTIES_FILES" | python -m A001_functions.Video_executor > "logs/$video_log" 2>&1

    if [[ $? -eq 0 ]]; then
        printf "Video creation for simulation %s completed successfully.\n" "$sim_number"
    else
        printf "Error: Video creation for simulation %s failed. See %s\n" "$sim_number" "$video_log" >&2
    fi
}

run_simulation() {
    local sim="$1"

    local sim_path="$SIMS_DIR/$sim"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist. Skipping simulation run.\n" "$sim_path" >&2
        return 1
    fi

    printf "Starting simulation in %s...\n" "$sim_path"
    cd "$sim_path" || { printf "Error: Cannot access directory %s\n" "$sim_path" >&2; return 1; }

    local sim_log="${sim}.log"
    abq job="$sim" cpus="$CPUS" double interactive > "$sim_log" 2>&1
    local status=$?

    cd - > /dev/null

    if [[ "$status" -eq 0 ]]; then
        printf "Simulation %s completed successfully.\n" "$sim"
        # cp "$sim_path"/SIM_info.json I001_Results/finished_simulations/"$sim".json
        cp "$sim_path"/"$sim".inp I001_Results/finished_simulations/"$sim".inp
    else
        printf "Simulation %s failed.\n" "$sim" >&2
        # cp "$sim_path"/SIM_info.json I001_Results/finished_simulations/"$sim".json
        cp "$sim_path"/"$sim".inp I001_Results/finished_simulations/"$sim".inp
    fi
    return "$status"
}

process_results() {
    local sim="$1"

    local sim_path="$SIMS_DIR/$sim"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist for processing. Skipping.\n" "$sim_path" >&2
        return 1
    fi

    local sim_number
    sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local log_folder="logs"
    mkdir -p "$log_folder"

    printf "Processing results for simulation %s...\n" "$sim_path"

    local reduce_input_file="reduce_inputs_${sim_number}.txt"

    # Run the Abaqus python script from the repo root but operate on the
    # simulation-specific files under $sim_path. The abq script is expected
    # to use the provided simulation number or locate files using absolute
    # paths. We keep the working directory at the repo root as required.
    printf "%s\n%s\nI001_Results\n%s\n" "$sim_number" "$sim_number" "$DELETE_ODB" | abq python "$FUNCTIONS_DIR/abq_scriptV9.py" > "$log_folder/SIM_${sim_number}.log" 2>&1

    if [[ ! -f "I001_Results/RES_SIM_${sim_number}.csv" ]]; then
        printf "Error: Expected results file RES_SIM_%s.csv was not created.\n" "$sim_number" >&2
    fi

    {
        printf "%s\n%s\n" "$sim_number" "$sim_number"

        for key in A A2 B C C2 D T1 T2 T1_ini T1_fin J1 J2 J3 J_ini J_fin J_alg H1 H2 H3 H_ini H_fin H_alg I1 I2 I3 I_ini I_fin I_alg K1 K2 K3 K_ini K_fin K_alg DELETE_CSV N_WORKERS MAX_MEMORY_GB; do
            printf "%s\n" "${OUTPUT_OPTIONS[$key]}"
        done
    } > "$reduce_input_file"

    # python "$FUNCTIONS_DIR/Reduce_resultsV5.py" < "$reduce_input_file" > "$log_folder/SIM_${sim_number}.log" 2>&1

    python -m A001_functions.Reduce_resultsV5 < "$reduce_input_file" > "$log_folder/SIM_${sim_number}_reduce.log" 2>&1

    rm -f "$reduce_input_file"

    printf "Results processing for simulation %s completed.\n" "$sim"

    if [[ "$MOVE_FOLDER" == "y" ]]; then
        local realpath_sim;
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
    fi

    if [[ "$CREATE_VIDEO" == "y" ]]; then
        create_video "$sim_number"
    fi
}

wait_for_sim_slot() {
    while :; do
        local active_pids=()
        local pid
        for pid in "${RUNNING_SIM_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                active_pids+=("$pid")
            fi
        done
        RUNNING_SIM_PIDS=("${active_pids[@]}")

        if [[ "${#RUNNING_SIM_PIDS[@]}" -lt "$MAX_PARALLEL_JOBS" ]]; then
            break
        fi
        sleep 1
    done
}

start_simulation() {
    local sim="$1"

    local sim_path="$SIMS_DIR/$sim"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist. Skipping simulation start.\n" "$sim_path" >&2
        return
    fi

    (
        run_simulation "$sim"; queue_processing "$sim"
    ) &
    RUNNING_SIM_PIDS+=("$!")
}

queue_processing() {
    local sim="$1"

    local sim_path="$SIMS_DIR/$sim"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist for processing. Skipping queue.\n" "$sim_path" >&2
        return
    fi

    (
        process_results "$sim"
    ) &
    PROCESS_PIDS+=("$!")
}

main() {
    local i sim pid
    mkdir -p I001_Results/finished_simulations I001_Results/finished_simulations logs

    for i in $(seq -f "%03g" "$START" "$END"); do
        sim="SIM_$i"
        sim_path="$SIMS_DIR/$sim"

        if [[ ! -d "$sim_path" ]]; then
            printf "Warning: Simulation directory %s does not exist. Skipping.\n" "$sim_path" >&2
            continue
        fi

        wait_for_sim_slot
        start_simulation "$sim"
    done

    for pid in "${RUNNING_SIM_PIDS[@]}"; do
        if ! wait "$pid"; then
            printf "Simulation process %s failed\n" "$pid" >&2
        fi
    done

    for pid in "${PROCESS_PIDS[@]}"; do
        if ! wait "$pid"; then
            printf "Processing process %s failed\n" "$pid" >&2
        fi
    done

    printf "All simulations and processing completed.\n"
}

declare -a RUNNING_SIM_PIDS=()
declare -a PROCESS_PIDS=()

trap 'printf "Termination signal received. Exiting...\n" >&2; exit 1' SIGINT SIGTERM

set -o pipefail
main