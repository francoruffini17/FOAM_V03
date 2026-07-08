#!/bin/bash
# run_general.sh – flag-based pipeline for FOAM_V03, calls V20 scripts.
# Identical orchestration to run_all.sh; uses abq_scriptV20/Reduce_resultsV20/Video_executorV20
# instead of piping stdin to the legacy V5/V9 scripts.

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
    printf "Error: Failed to source conda initialization script.\n" >&2
    exit 1
}

if ! conda activate Fenv; then
    printf "Error: Failed to activate conda environment 'Fenv'.\n" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FUNCTIONS_DIR="$ROOT_DIR/A001_functions"

if [[ -d "$ROOT_DIR/E001_Simulations" ]]; then
    SIMS_DIR="$ROOT_DIR/E001_Simulations"
else
    SIMS_DIR="$ROOT_DIR"
fi

cd "$ROOT_DIR" || { printf "Error: Cannot cd to repo root %s\n" "$ROOT_DIR" >&2; exit 1; }
export PYTHONPATH="$FUNCTIONS_DIR:$ROOT_DIR:${PYTHONPATH:-}"

ABQ_CMD="${ABQ_CMD:-}"

resolve_abq_cmd() {
    local candidate resolved
    if [[ -n "$ABQ_CMD" ]]; then
        if [[ -x "$ABQ_CMD" ]]; then return 0; fi
        if resolved="$(command -v "$ABQ_CMD" 2>/dev/null)"; then ABQ_CMD="$resolved"; return 0; fi
        printf "Error: Abaqus command '%s' was not found or is not executable.\n" "$ABQ_CMD" >&2
        return 1
    fi
    for candidate in "abq" "/var/DassaultSystemes/SIMULIA/Commands/abq" "abaqus"; do
        if [[ -x "$candidate" ]]; then ABQ_CMD="$candidate"; return 0; fi
        if resolved="$(command -v "$candidate" 2>/dev/null)"; then ABQ_CMD="$resolved"; return 0; fi
    done
    printf "Error: Abaqus command not found. Try passing ABQ_CMD=/path/to/abq.\n" >&2
    return 1
}

# ---------------------------------------------------------------------------
usage() {
    cat >&2 <<EOF
Usage: $0 sim_num_ini sim_num_fin [OPTION=VALUE ...]
   or: $0 -list=<file>            [OPTION=VALUE ...]
   or: $0 <file.txt>              [OPTION=VALUE ...]

Step flags (default: n):
  RUN_SIMULATIONS=y|n   Run Abaqus FEM solver
  RUN_ABQ=y|n           Run ODB extraction  (abq python abq_scriptV20.py)
  RUN_EIGEN=y|n         Run stiffness-matrix min-eigenvalue extraction
                        (needed to produce DATA_PICK_*_EIG.json for PKL E;
                        only useful if the .inp has *Restart, write)
  RUN_REDUCE=y|n        Run Reduce_resultsV20
  RUN_VIDEO=y|n         Run Video_executorV20

  CONTINUE_ON_SOLVER_ERROR=y|n
                        If a solver/ABQ-extraction step fails (e.g. the
                        Abaqus solve did not fully converge but wrote output
                        for the last converged increment), keep running the
                        downstream steps for that simulation instead of
                        skipping them (default: n)

Parallelism (default: 1):
  -par_simulations=N    Max parallel solver jobs
  -par_abq=N            Max parallel ABQ extraction jobs
  -par_eigen=N          Max parallel eigenvalue-extraction jobs
  -par_red=N            Max parallel Reduce jobs
  -par_vid=N            Max parallel Video jobs

Abaqus solver:
  cpus=N                CPUs per solver job (default: 1)
  ABQ_CMD=<path>        Override Abaqus executable

ABQ extraction:
  DELETE_ODB=y|n        Delete ODB after extraction (default: n)

Reduce output options (defaults shown):
  A=y  A2=y  B=y  C=y  C2=y  D=y
  T1=n  T2=n  T1_ini=0  T1_fin=0
  J1=y  J2=y  J3=y  J_ini=0  J_fin=0  J_alg=1
  H1=y  H2=y  H3=y  H_ini=0  H_fin=0  H_alg=1
  I1=y  I2=y  I3=y  I_ini=0  I_fin=0  I_alg=1
  K1=y  K2=y  K3=y  K_ini=0  K_fin=0  K_alg=1
  Q1=n  Q2=n  Q_ini=0  Q_fin=0
  TP1=n  TP2=n  DEFC1=n  DEFC2=n
  E=n
  DELETE_CSV=n  N_WORKERS=0  MAX_MEMORY_GB=0
  (N_WORKERS=0 and MAX_MEMORY_GB=0 mean auto)

Video:
  VIDEOS_PROPERTIES_FILES=<name>  (default: Video_properties0001)

Other:
  MOVE_FOLDER=y|n       Move simulation folder after all steps (default: n)
  MOVE_DEST=<path>      Destination (default: /data/Franco/<repo>_completed)
  -delay=N              Seconds between launching consecutive sims (default: 120)
EOF
    exit 1
}

# ---------------------------------------------------------------------------
[[ "$#" -lt 1 ]] && usage

LIST_FILE=""
if [[ "$1" =~ ^-list=(.+)$ ]]; then
    LIST_FILE="${BASH_REMATCH[1]}"; shift
elif [[ "$1" =~ ^[0-9]+$ ]]; then
    [[ "$#" -lt 2 ]] && usage
    START=$1; END=$2; shift 2
    [[ "$END" =~ ^[0-9]+$ && "$START" -le "$END" ]] \
        || { printf "Error: invalid sim range.\n" >&2; exit 1; }
else
    LIST_FILE="$1"; shift
fi

RUN_SIMULATIONS="n"; RUN_ABQ="n"; RUN_EIGEN="n"; RUN_REDUCE="n"; RUN_VIDEO="n"
CONTINUE_ON_SOLVER_ERROR="n"
PAR_SIMULATIONS=1; PAR_ABQ=1; PAR_EIGEN=1; PAR_RED=1; PAR_VID=1
START_DELAY=120
CPUS=1; DELETE_ODB="n"; MOVE_FOLDER="n"; MOVE_DEST=""
VIDEOS_PROPERTIES_FILES="Video_properties0001"

declare -A OUTPUT_OPTIONS=(
    [A]="y"    [A2]="y"   [B]="y"    [C]="y"    [C2]="y"   [D]="y"
    [T1]="n"   [T2]="n"   [T1_ini]="0" [T1_fin]="0"
    [J1]="y"   [J2]="y"   [J3]="y"   [J_ini]="0" [J_fin]="0" [J_alg]="1"
    [H1]="y"   [H2]="y"   [H3]="y"   [H_ini]="0" [H_fin]="0" [H_alg]="1"
    [I1]="y"   [I2]="y"   [I3]="y"   [I_ini]="0" [I_fin]="0" [I_alg]="1"
    [K1]="y"   [K2]="y"   [K3]="y"   [K_ini]="0" [K_fin]="0" [K_alg]="1"
    [Q1]="n"   [Q2]="n"   [Q_ini]="0" [Q_fin]="0"
    [TP1]="n"  [TP2]="n"  [DEFC1]="n" [DEFC2]="n"
    [E]="n"
    [DELETE_CSV]="n" [N_WORKERS]="0" [MAX_MEMORY_GB]="0"
)

for arg in "$@"; do
    if   [[ "$arg" =~ ^-par_simulations=([0-9]+)$ ]]; then PAR_SIMULATIONS="${BASH_REMATCH[1]}"
    elif [[ "$arg" =~ ^-par_abq=([0-9]+)$ ]];         then PAR_ABQ="${BASH_REMATCH[1]}"
    elif [[ "$arg" =~ ^-par_eigen=([0-9]+)$ ]];       then PAR_EIGEN="${BASH_REMATCH[1]}"
    elif [[ "$arg" =~ ^-par_red=([0-9]+)$ ]];         then PAR_RED="${BASH_REMATCH[1]}"
    elif [[ "$arg" =~ ^-par_vid=([0-9]+)$ ]];         then PAR_VID="${BASH_REMATCH[1]}"
    elif [[ "$arg" =~ ^-delay=([0-9]+)$ ]];           then START_DELAY="${BASH_REMATCH[1]}"
    else
        key="${arg%%=*}"; value="${arg#*=}"
        case "$key" in
            RUN_SIMULATIONS) [[ "$value" == y || "$value" == n ]] && RUN_SIMULATIONS="$value" ;;
            RUN_ABQ)         [[ "$value" == y || "$value" == n ]] && RUN_ABQ="$value" ;;
            RUN_EIGEN)       [[ "$value" == y || "$value" == n ]] && RUN_EIGEN="$value" ;;
            CONTINUE_ON_SOLVER_ERROR) [[ "$value" == y || "$value" == n ]] && CONTINUE_ON_SOLVER_ERROR="$value" ;;
            RUN_REDUCE)      [[ "$value" == y || "$value" == n ]] && RUN_REDUCE="$value" ;;
            RUN_VIDEO)       [[ "$value" == y || "$value" == n ]] && RUN_VIDEO="$value" ;;
            cpus)            [[ "$value" =~ ^[0-9]+$ && "$value" -gt 0 ]] && CPUS="$value" ;;
            DELETE_ODB)      [[ "$value" == y || "$value" == n ]] && DELETE_ODB="$value" ;;
            MOVE_FOLDER)     [[ "$value" == y || "$value" == n ]] && MOVE_FOLDER="$value" ;;
            MOVE_DEST)       MOVE_DEST="$value" ;;
            VIDEOS_PROPERTIES_FILES) VIDEOS_PROPERTIES_FILES="$value" ;;
            ABQ_CMD)         ABQ_CMD="$value" ;;
            *) [[ -n "${OUTPUT_OPTIONS[$key]+_}" ]] && OUTPUT_OPTIONS[$key]="$value" \
                   || printf "Warning: Ignoring unknown option %s\n" "$arg" >&2 ;;
        esac
    fi
done

if [[ "$RUN_SIMULATIONS" == n && "$RUN_ABQ" == n && "$RUN_EIGEN" == n && "$RUN_REDUCE" == n && "$RUN_VIDEO" == n ]]; then
    printf "Error: No steps enabled. Set at least one of RUN_SIMULATIONS/RUN_ABQ/RUN_EIGEN/RUN_REDUCE/RUN_VIDEO=y.\n" >&2
    exit 1
fi

if [[ "$RUN_SIMULATIONS" == y || "$RUN_ABQ" == y || "$RUN_EIGEN" == y ]]; then
    resolve_abq_cmd || exit 1
    printf "Using Abaqus command: %s\n" "$ABQ_CMD"
fi
export ABQ_CMD

# ---------------------------------------------------------------------------
create_semaphore() {
    local name="$1" capacity="$2"
    local fifo="/tmp/.sem_${name}_$$"
    mkfifo "$fifo"
    eval "exec {${name}_fd}<>\"$fifo\""
    rm -f "$fifo"
    local i; for ((i=0; i<capacity; i++)); do eval "printf '\\n' >&\${${name}_fd}"; done
}
acquire_semaphore() { local name="$1"; eval "read -u \${${name}_fd}"; }
release_semaphore() { local name="$1"; eval "printf '\\n' >&\${${name}_fd}"; }

# ---------------------------------------------------------------------------
run_simulation() {
    local sim="$1" sim_path="$SIMS_DIR/$1"
    [[ -d "$sim_path" ]] || { printf "Warning: %s not found. Skipping.\n" "$sim_path" >&2; return 1; }
    printf "Simulation: Starting %s (cpus=%s) ...\n" "$sim" "$CPUS"
    local sim_log="$sim_path/${sim}.log"
    (cd "$sim_path" && "$ABQ_CMD" job="$sim" cpus="$CPUS" double interactive > "$sim_log" 2>&1)
    local status=$?
    if [[ $status -ne 0 ]]; then
        printf "Error: Simulation %s failed. See %s\n" "$sim" "$sim_log" >&2
    else
        printf "Simulation: %s completed.\n" "$sim"
        cp "$sim_path/${sim}.inp" "I001_Results/finished_simulations/${sim}.inp" 2>/dev/null || true
    fi
    return "$status"
}

run_abq_extraction() {
    local sim="$1"
    local sim_number; sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local sim_path="$SIMS_DIR/$sim"
    [[ -d "$sim_path" ]] || { printf "Warning: %s not found. Skipping ABQ.\n" "$sim_path" >&2; return 1; }
    printf "ABQ: Starting extraction for %s ...\n" "$sim"

    local abq_args=("$sim_number" "$sim_number" --results-folder I001_Results)
    [[ "$DELETE_ODB" == y ]] && abq_args+=(--delete-odb)

    "$ABQ_CMD" python "$FUNCTIONS_DIR/abq_scriptV20.py" "${abq_args[@]}" \
        > "logs/SIM_${sim_number}.log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: ABQ extraction for %s failed. See logs/SIM_%s.log\n" "$sim" "$sim_number" >&2
    elif [[ ! -f "I001_Results/RES_SIM_${sim_number}.csv" ]]; then
        printf "Error: Expected RES_SIM_%s.csv not created.\n" "$sim_number" >&2; status=1
    else
        printf "ABQ: %s completed.\n" "$sim"
    fi
    return "$status"
}

run_eigen() {
    local sim="$1"
    local sim_number; sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    local sim_path="$SIMS_DIR/$sim"
    [[ -d "$sim_path" ]] || { printf "Warning: %s not found. Skipping eigenvalue extraction.\n" "$sim_path" >&2; return 1; }
    printf "Eigen: Starting stiffness-matrix eigenvalue extraction for %s ...\n" "$sim"

    python -m A001_functions.stiffness_eigen "$sim_number" \
        > "logs/SIM_${sim_number}_eigen.log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: Eigenvalue extraction for %s failed. See logs/SIM_%s_eigen.log\n" "$sim" "$sim_number" >&2
    else
        printf "Eigen: %s completed.\n" "$sim"
    fi
    return "$status"
}

run_reduce() {
    local sim="$1"
    local sim_number; sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    printf "Reduce: Starting for %s ...\n" "$sim"

    python -m A001_functions.Reduce_resultsV20 "$sim_number" "$sim_number" \
        --A  "${OUTPUT_OPTIONS[A]}"     --A2 "${OUTPUT_OPTIONS[A2]}" \
        --B  "${OUTPUT_OPTIONS[B]}"     --C  "${OUTPUT_OPTIONS[C]}" \
        --C2 "${OUTPUT_OPTIONS[C2]}"    --D  "${OUTPUT_OPTIONS[D]}" \
        --T1 "${OUTPUT_OPTIONS[T1]}"    --T2 "${OUTPUT_OPTIONS[T2]}" \
        --T1-ini "${OUTPUT_OPTIONS[T1_ini]}"  --T1-fin "${OUTPUT_OPTIONS[T1_fin]}" \
        --J1 "${OUTPUT_OPTIONS[J1]}"    --J2 "${OUTPUT_OPTIONS[J2]}"  --J3 "${OUTPUT_OPTIONS[J3]}" \
        --J-ini "${OUTPUT_OPTIONS[J_ini]}"    --J-fin "${OUTPUT_OPTIONS[J_fin]}" \
        --J-alg "${OUTPUT_OPTIONS[J_alg]}" \
        --H1 "${OUTPUT_OPTIONS[H1]}"    --H2 "${OUTPUT_OPTIONS[H2]}"  --H3 "${OUTPUT_OPTIONS[H3]}" \
        --H-ini "${OUTPUT_OPTIONS[H_ini]}"    --H-fin "${OUTPUT_OPTIONS[H_fin]}" \
        --H-alg "${OUTPUT_OPTIONS[H_alg]}" \
        --I1 "${OUTPUT_OPTIONS[I1]}"    --I2 "${OUTPUT_OPTIONS[I2]}"  --I3 "${OUTPUT_OPTIONS[I3]}" \
        --I-ini "${OUTPUT_OPTIONS[I_ini]}"    --I-fin "${OUTPUT_OPTIONS[I_fin]}" \
        --I-alg "${OUTPUT_OPTIONS[I_alg]}" \
        --K1 "${OUTPUT_OPTIONS[K1]}"    --K2 "${OUTPUT_OPTIONS[K2]}"  --K3 "${OUTPUT_OPTIONS[K3]}" \
        --K-ini "${OUTPUT_OPTIONS[K_ini]}"    --K-fin "${OUTPUT_OPTIONS[K_fin]}" \
        --K-alg "${OUTPUT_OPTIONS[K_alg]}" \
        --Q1 "${OUTPUT_OPTIONS[Q1]}"    --Q2 "${OUTPUT_OPTIONS[Q2]}" \
        --Q-ini "${OUTPUT_OPTIONS[Q_ini]}"    --Q-fin "${OUTPUT_OPTIONS[Q_fin]}" \
        --TP1 "${OUTPUT_OPTIONS[TP1]}"  --TP2 "${OUTPUT_OPTIONS[TP2]}" \
        --DEFC1 "${OUTPUT_OPTIONS[DEFC1]}"  --DEFC2 "${OUTPUT_OPTIONS[DEFC2]}" \
        --E "${OUTPUT_OPTIONS[E]}" \
        --delete-csv "${OUTPUT_OPTIONS[DELETE_CSV]}" \
        --n-workers "${OUTPUT_OPTIONS[N_WORKERS]}" \
        --max-memory-gb "${OUTPUT_OPTIONS[MAX_MEMORY_GB]}" \
        > "logs/SIM_${sim_number}_reduce.log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: Reduce for %s failed. See logs/SIM_%s_reduce.log\n" "$sim" "$sim_number" >&2
    else
        printf "Reduce: %s completed.\n" "$sim"
    fi
    return "$status"
}

run_video() {
    local sim="$1"
    local sim_number; sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    printf "Video: Starting for %s ...\n" "$sim"

    python -m A001_functions.Video_executorV20 \
        --sim-num "$sim_number" \
        --properties-file "$VIDEOS_PROPERTIES_FILES" \
        > "logs/SIM_${sim_number}_video.log" 2>&1
    local status=$?

    if [[ $status -ne 0 ]]; then
        printf "Error: Video for %s failed. See logs/SIM_%s_video.log\n" "$sim" "$sim_number" >&2
    else
        printf "Video: %s completed.\n" "$sim"
    fi
    return "$status"
}

move_folder() {
    local sim="$1" sim_path="$SIMS_DIR/$1"
    local sim_number; sim_number=$(printf "%s" "$sim" | grep -oE '[0-9]+$')
    [[ -d "$sim_path" ]] || { printf "Warning: %s not found. Skipping move.\n" "$sim_path" >&2; return 1; }
    local realpath_sim; realpath_sim=$(realpath "$sim_path")
    local target_dir="${MOVE_DEST:-/data/Franco/$(basename "$(dirname "$realpath_sim")")_completed}"
    local dest_dir="$target_dir/SIM_${sim_number}"
    mkdir -p "$target_dir"
    [[ -d "$dest_dir" ]] && { rm -rf "$dest_dir"; printf "Warning: Removed existing %s\n" "$dest_dir" >&2; }
    mv "$sim_path" "$dest_dir"
    printf "Moved %s to %s\n" "$sim_path" "$dest_dir"
}

process_simulation() {
    local sim="$1"

    if [[ "$RUN_SIMULATIONS" == y ]]; then
        acquire_semaphore sem_sim; run_simulation "$sim"; local s=$?; release_semaphore sem_sim
        if [[ $s -ne 0 ]]; then
            if [[ "$CONTINUE_ON_SOLVER_ERROR" == y ]]; then
                printf "Warning: %s solver failed but CONTINUE_ON_SOLVER_ERROR=y - proceeding with partial results.\n" "$sim" >&2
            else
                printf "Skipping remaining steps for %s.\n" "$sim" >&2
                return $s
            fi
        fi
    fi

    if [[ "$RUN_ABQ" == y ]]; then
        acquire_semaphore sem_abq; run_abq_extraction "$sim"; local s=$?; release_semaphore sem_abq
        if [[ $s -ne 0 ]]; then
            if [[ "$CONTINUE_ON_SOLVER_ERROR" == y ]]; then
                printf "Warning: %s ABQ extraction failed but CONTINUE_ON_SOLVER_ERROR=y - proceeding.\n" "$sim" >&2
            else
                printf "Skipping reduce/video for %s.\n" "$sim" >&2
                return $s
            fi
        fi
    fi

    local all_ok=0

    if [[ "$RUN_EIGEN" == y ]]; then
        acquire_semaphore sem_eigen; run_eigen "$sim"; local s=$?; release_semaphore sem_eigen
        [[ $s -ne 0 ]] && all_ok=1
    fi

    if [[ "$RUN_REDUCE" == y ]]; then
        acquire_semaphore sem_red; run_reduce "$sim"; local s=$?; release_semaphore sem_red
        [[ $s -ne 0 ]] && all_ok=1
    fi

    if [[ "$RUN_VIDEO" == y ]]; then
        acquire_semaphore sem_vid; run_video "$sim"; local s=$?; release_semaphore sem_vid
        [[ $s -ne 0 ]] && all_ok=1
    fi

    if [[ "$MOVE_FOLDER" == y ]]; then
        if [[ $all_ok -eq 0 ]]; then move_folder "$sim"
        else printf "Warning: Skipping move for %s due to errors.\n" "$sim" >&2; fi
    fi
}

main() {
    mkdir -p I001_Results/finished_simulations logs

    create_semaphore sem_sim "$PAR_SIMULATIONS"
    create_semaphore sem_abq "$PAR_ABQ"
    create_semaphore sem_eigen "$PAR_EIGEN"
    create_semaphore sem_red "$PAR_RED"
    create_semaphore sem_vid "$PAR_VID"

    local MAX_CONCURRENT
    MAX_CONCURRENT=$(( PAR_SIMULATIONS > PAR_ABQ   ? PAR_SIMULATIONS : PAR_ABQ ))
    MAX_CONCURRENT=$(( MAX_CONCURRENT  > PAR_EIGEN ? MAX_CONCURRENT  : PAR_EIGEN ))
    MAX_CONCURRENT=$(( MAX_CONCURRENT  > PAR_RED   ? MAX_CONCURRENT  : PAR_RED ))
    MAX_CONCURRENT=$(( MAX_CONCURRENT  > PAR_VID   ? MAX_CONCURRENT  : PAR_VID ))

    local -a PIDS=() SIM_LIST=()
    local i first_sim=1

    if [[ -n "$LIST_FILE" ]]; then
        local list_path
        [[ "$LIST_FILE" = /* ]] && list_path="$LIST_FILE" || list_path="$SCRIPT_DIR/$LIST_FILE"
        [[ -f "$list_path" ]] || { printf "Error: List file '%s' not found.\n" "$list_path" >&2; exit 1; }
        while IFS= read -r line || [[ -n "$line" ]]; do
            line="${line//[[:space:]]/}"
            [[ -z "$line" || "$line" == \#* ]] && continue
            [[ "$line" =~ ^[0-9]+$ ]] && SIM_LIST+=("$(printf "%03d" "$line")") \
                || printf "Warning: Skipping invalid entry '%s'.\n" "$line" >&2
        done < "$list_path"
        [[ "${#SIM_LIST[@]}" -gt 0 ]] || { printf "Error: No valid entries in '%s'.\n" "$list_path" >&2; exit 1; }
    else
        for i in $(seq -f "%03g" "$START" "$END"); do SIM_LIST+=("$i"); done
    fi

    for i in "${SIM_LIST[@]}"; do
        local sim="SIM_$i"
        if [[ "$first_sim" -eq 0 && "$START_DELAY" -gt 0 ]]; then
            printf "Waiting %ss before starting %s...\n" "$START_DELAY" "$sim"
            sleep "$START_DELAY"
        fi
        first_sim=0
        while [[ "$(jobs -rp | wc -l)" -ge "$MAX_CONCURRENT" ]]; do sleep 1; done
        process_simulation "$sim" &
        PIDS+=("$!")
    done

    local pid
    for pid in "${PIDS[@]}"; do
        wait "$pid" || printf "Process %s finished with errors.\n" "$pid" >&2
    done
    printf "All processing completed.\n"
}

trap 'printf "Termination signal received. Exiting...\n" >&2; exit 1' SIGINT SIGTERM
set -o pipefail
main
