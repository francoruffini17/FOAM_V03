#!/bin/bash

CONDA_SH=""

if [[ -n "${CONDA_EXE:-}" ]]; then
    CONDA_ROOT="$(dirname "$(dirname "$CONDA_EXE")")"
    if [[ -f "$CONDA_ROOT/etc/profile.d/conda.sh" ]]; then
        CONDA_SH="$CONDA_ROOT/etc/profile.d/conda.sh"
    fi
fi

if [[ -z "$CONDA_SH" ]]; then
    for candidate in \
        "$HOME/miniconda3/etc/profile.d/conda.sh" \
        "$HOME/anaconda3/etc/profile.d/conda.sh" \
        "/opt/anaconda3/etc/profile.d/conda.sh"
    do
        if [[ -f "$candidate" ]]; then
            CONDA_SH="$candidate"
            break
        fi
    done
fi

if [[ -z "$CONDA_SH" ]]; then
    printf "Error: Could not find conda initialization script.\n" >&2
    exit 1
fi

source "$CONDA_SH" || {
    printf "Error: Failed to source conda initialization script: %s\n" "$CONDA_SH" >&2
    exit 1
}

if ! conda activate Fenv; then
    printf "Error: Failed to activate conda environment 'Fenv'.\n" >&2
    exit 1
fi

if [[ "$#" -lt 2 ]]; then
    printf "Usage: %s simlist.txt max_parallel_jobs [OPTION=VALUE ...]\n  Options: cpus=N DELETE_ODB=y|n RUN_VIDEO=y|n MOVE_FOLDER=y|n MOVE_DEST=<path> VIDEOS_PROPERTIES_FILES=<name> ABQ_CMD=<path> + all reduce output flags\n" "$0" >&2
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

SIMLIST_FILE="H001_sh_files/$1"
MAX_PARALLEL_JOBS="$2"
shift 2

if [[ ! -f "$SIMLIST_FILE" ]]; then
    printf "Error: Simulation list file '%s' does not exist.\n" "$SIMLIST_FILE" >&2
    exit 1
fi

if ! [[ "$MAX_PARALLEL_JOBS" =~ ^[0-9]+$ && "$MAX_PARALLEL_JOBS" -gt 0 ]]; then
    printf "Error: max_parallel_jobs must be a positive integer.\n" >&2
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
    ["Q1"]="n"
    ["Q2"]="n"
    ["Q_ini"]="0"
    ["Q_fin"]="0"
    ["TP1"]="n"
    ["TP2"]="n"
    ["DEFC1"]="n"
    ["DEFC2"]="n"
    ["DELETE_CSV"]="n"
    ["N_WORKERS"]="1"
    ["MAX_MEMORY_GB"]="10"
)

CPUS=15
ABQ_CMD="${ABQ_CMD:-}"
DELETE_ODB="n"
RUN_VIDEO="n"
MOVE_FOLDER="n"
MOVE_DEST=""
VIDEOS_PROPERTIES_FILES="Video_properties0001"

for arg in "$@"; do
    key="${arg%%=*}"
    value="${arg#*=}"

    if [[ -n "${OUTPUT_OPTIONS[$key]+_}" ]]; then
        OUTPUT_OPTIONS[$key]="$value"
    elif [[ "$key" == "cpus" && "$value" =~ ^[0-9]+$ && "$value" -gt 0 ]]; then
        CPUS="$value"
    elif [[ "$key" == "ABQ_CMD" ]]; then
        ABQ_CMD="$value"
    elif [[ "$key" == "DELETE_ODB" && ("$value" == "y" || "$value" == "n") ]]; then
        DELETE_ODB="$value"
    elif [[ "$key" == "RUN_VIDEO" && ("$value" == "y" || "$value" == "n") ]]; then
        RUN_VIDEO="$value"
    elif [[ "$key" == "MOVE_FOLDER" && ("$value" == "y" || "$value" == "n") ]]; then
        MOVE_FOLDER="$value"
    elif [[ "$key" == "MOVE_DEST" ]]; then
        MOVE_DEST="$value"
    elif [[ "$key" == "VIDEOS_PROPERTIES_FILES" ]]; then
        VIDEOS_PROPERTIES_FILES="$value"
    else
        printf "Warning: Ignoring unknown or invalid option %s\n" "$arg" >&2
    fi
done

resolve_abq_cmd() {
    local candidate resolved

    if [[ -n "$ABQ_CMD" ]]; then
        if [[ -x "$ABQ_CMD" ]]; then
            return 0
        fi
        if resolved="$(command -v "$ABQ_CMD" 2>/dev/null)"; then
            ABQ_CMD="$resolved"
            return 0
        fi
        printf "Error: Abaqus command '%s' was not found or is not executable.\n" "$ABQ_CMD" >&2
        return 1
    fi

    for candidate in \
        "abq" \
        "/var/DassaultSystemes/SIMULIA/Commands/abq" \
        "abaqus"
    do
        if [[ -x "$candidate" ]]; then
            ABQ_CMD="$candidate"
            return 0
        fi
        if resolved="$(command -v "$candidate" 2>/dev/null)"; then
            ABQ_CMD="$resolved"
            return 0
        fi
    done

    printf "Error: Abaqus command not found. Try passing ABQ_CMD=/path/to/abq.\n" >&2
    return 1
}

resolve_abq_cmd || exit 1
printf "Using Abaqus command: %s\n" "$ABQ_CMD"

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
    "$ABQ_CMD" job="$sim" cpus="$CPUS" double interactive > "$sim_log" 2>&1
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

    printf "%s\n%s\nI001_Results\n%s\n" "$sim_number" "$sim_number" "$DELETE_ODB" | "$ABQ_CMD" python "$FUNCTIONS_DIR/abq_scriptV9.py" > "$log_folder/SIM_${sim_number}.log" 2>&1
    local abq_status=$?

    if [[ $abq_status -ne 0 ]] || [[ ! -f "I001_Results/RES_SIM_${sim_number}.csv" ]]; then
        printf "Error: ABQ extraction for %s failed (status=%d). Skipping reduce.\n" "$sim_number" "$abq_status" >&2
        return 1
    fi

    {
        printf "%s\n%s\n" "$sim_number" "$sim_number"
        for key in A A2 B C C2 D T1 T2 T1_ini T1_fin J1 J2 J3 J_ini J_fin J_alg H1 H2 H3 H_ini H_fin H_alg I1 I2 I3 I_ini I_fin I_alg K1 K2 K3 K_ini K_fin K_alg Q1 Q2 Q_ini Q_fin TP1 TP2 DEFC1 DEFC2 DELETE_CSV N_WORKERS MAX_MEMORY_GB; do
            printf "%s\n" "${OUTPUT_OPTIONS[$key]}"
        done
    } > "$reduce_input_file"

    python -m A001_functions.Reduce_resultsV5 < "$reduce_input_file" > "$log_folder/SIM_${sim_number}_reduce.log" 2>&1
    local reduce_status=$?
    rm -f "$reduce_input_file"

    if [[ $reduce_status -ne 0 ]]; then
        printf "Error: Reduce for %s failed. See logs/SIM_%s_reduce.log\n" "$sim" "$sim_number" >&2
    else
        printf "Results processing for simulation %s completed.\n" "$sim"
    fi

    if [[ "$MOVE_FOLDER" == "y" ]]; then
        if [[ $reduce_status -ne 0 ]]; then
            printf "Warning: Skipping move for %s due to processing errors.\n" "$sim" >&2
        else
            local realpath_sim
            if ! realpath_sim=$(realpath "$sim_path"); then
                printf "Error: Unable to resolve real path for %s\n" "$sim_path" >&2
                return 1
            fi

            local target_dir
            if [[ -n "$MOVE_DEST" ]]; then
                target_dir="$MOVE_DEST"
            else
                target_dir="/data/Franco/$(basename "$(dirname "$realpath_sim")")_completed"
            fi
            local dest_dir="$target_dir/SIM_${sim_number}"

            mkdir -p "$target_dir"

            if [[ -d "$dest_dir" ]]; then
                rm -rf "$dest_dir"
                printf "Warning: Existing directory %s was removed.\n" "$dest_dir" >&2
            fi

            mv "$sim_path" "$dest_dir"
            printf "Moved %s to %s\n" "$sim_path" "$dest_dir"
        fi
    fi

    if [[ "$RUN_VIDEO" == "y" ]]; then
        create_video "$sim_number"
    fi
}

start_simulation() {
    local sim="$1"
    local sim_path="$SIMS_DIR/$sim"

    if [[ ! -d "$sim_path" ]]; then
        printf "Warning: Simulation directory %s does not exist. Skipping.\n" "$sim_path" >&2
        return
    fi

    (
        if run_simulation "$sim"; then
            process_results "$sim"
        else
            printf "Skipping result processing for %s because the simulation failed.\n" "$sim" >&2
        fi
    ) &
    RUNNING_SIM_PIDS+=("$!")
    SIMS_RUN+=("$sim")
}

get_next_sim_to_run() {
    local sim_list;
    if ! sim_list=$(< "$SIMLIST_FILE"); then
        return 1
    fi

    local sim_number sim_name
    local index=0
    while read -r sim_number; do
        ((index++))
        if [[ ! "$sim_number" =~ ^[0-9]+$ ]]; then
            continue
        fi
        sim_name="SIM_$(printf "%03d" "$sim_number")"
        if [[ " ${SIMS_RUN[*]} " == *" $sim_name "* ]]; then
            continue
        fi
        if [[ ! " ${SIMS_QUEUED[*]} " == *" $index "* ]]; then
            SIMS_QUEUED+=("$index")
            NEXT_SIM_NAME="$sim_name"
            return 0
        fi
    done <<< "$sim_list"

    return 1
}

main() {
    mkdir -p I001_Results/finished_simulations I001_Results/finished_simulations logs

    while :; do
        local active_count="${#RUNNING_SIM_PIDS[@]}"
        local available_slots=$((MAX_PARALLEL_JOBS - active_count))

        while [[ "$available_slots" -gt 0 ]]; do
            local NEXT_SIM_NAME=""
            if get_next_sim_to_run; then
                start_simulation "$NEXT_SIM_NAME"
                ((available_slots--))
            else
                break
            fi
        done

        local new_running=()
        for pid in "${RUNNING_SIM_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                new_running+=("$pid")
            fi
        done
        RUNNING_SIM_PIDS=("${new_running[@]}")

        if [[ "${#RUNNING_SIM_PIDS[@]}" -eq 0 ]]; then
            local check_more=""
            if ! check_more=$(grep -E '^[0-9]+$' "$SIMLIST_FILE"); then
                break
            fi
            local count
            count=$(printf "%s\n" "$check_more" | wc -l)
            [[ "${#SIMS_QUEUED[@]}" -ge "$count" ]] && break
        fi

        sleep 2
    done

    printf "All simulations and processing completed.\n"
}

declare -a RUNNING_SIM_PIDS=()
declare -a SIMS_RUN=()
declare -a SIMS_QUEUED=()
declare NEXT_SIM_NAME=""

trap 'printf "Termination signal received. Exiting...\n" >&2; exit 1' SIGINT SIGTERM

set -o pipefail
main
