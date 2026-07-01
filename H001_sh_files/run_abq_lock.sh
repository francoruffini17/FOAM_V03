#!/bin/bash

# run_abq_lock.sh
# Monitors running Abaqus simulations and terminates any that appear locked.
#
# Usage:
#   run_abq_lock.sh sim_ini=<N> sim_fin=<N> time=<minutes> [lock_iters=<N>]
#
# Arguments:
#   sim_ini     First simulation number to monitor (inclusive)
#   sim_fin     Last simulation number to monitor (inclusive)
#   time        Wait time in minutes between monitoring cycles
#   lock_iters  Consecutive increments sharing the same STEP before the
#               simulation is considered locked (default: 10)
#
# Example:
#   run_abq_lock.sh sim_ini=0 sim_fin=10 time=5

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
SIM_INI=""
SIM_FIN=""
WAIT_MINUTES=""
LOCK_ITERS=10

for arg in "$@"; do
    key="${arg%%=*}"
    value="${arg#*=}"
    case "$key" in
        sim_ini)    SIM_INI="$value" ;;
        sim_fin)    SIM_FIN="$value" ;;
        time)       WAIT_MINUTES="$value" ;;
        lock_iters) LOCK_ITERS="$value" ;;
        *)
            printf "Warning: Unknown argument '%s' -- ignoring.\n" "$arg" >&2
            ;;
    esac
done

# Validate
if [[ -z "$SIM_INI" || -z "$SIM_FIN" || -z "$WAIT_MINUTES" ]]; then
    printf "Usage: %s sim_ini=<N> sim_fin=<N> time=<minutes> [lock_iters=<N>]\n" "$0" >&2
    exit 1
fi

for var_name in SIM_INI SIM_FIN LOCK_ITERS; do
    val="${!var_name}"
    if ! [[ "$val" =~ ^[0-9]+$ ]]; then
        printf "Error: '%s' must be a non-negative integer (got '%s').\n" "$var_name" "$val" >&2
        exit 1
    fi
done

if ! [[ "$WAIT_MINUTES" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    printf "Error: 'time' must be a positive number (got '%s').\n" "$WAIT_MINUTES" >&2
    exit 1
fi

WAIT_SECONDS=$(echo "$WAIT_MINUTES * 60" | bc | xargs printf "%.0f")

# ---------------------------------------------------------------------------
# Resolve simulation root directory (same logic as the main runner)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -d "$ROOT_DIR/E001_Simulations" ]]; then
    SIMS_DIR="$ROOT_DIR/E001_Simulations"
else
    SIMS_DIR="$ROOT_DIR"
fi

# ---------------------------------------------------------------------------
# is_locked <sta_file>
#
# Checks column 8 (INC OF TIME/LPF) of the last LOCK_ITERS data rows.
# If the value has not changed at all, the simulation is stuck.
# ---------------------------------------------------------------------------
is_locked() {
    local sta_file="$1"

    if [[ ! -f "$sta_file" ]]; then
        return 1
    fi

    local inc_values total_lines last_incs unique_count
    inc_values=$(awk '$1 ~ /^[0-9]+$/ {print $8}' "$sta_file")
    total_lines=$(printf "%s\n" "$inc_values" | grep -c .)

    if [[ "$total_lines" -lt "$LOCK_ITERS" ]]; then
        return 1
    fi

    last_incs=$(printf "%s\n" "$inc_values" | tail -n "$LOCK_ITERS")
    unique_count=$(printf "%s\n" "$last_incs" | sort -u | grep -c .)

    [[ "$unique_count" -eq 1 ]]
}

# ---------------------------------------------------------------------------
# terminate_simulation <sim_name> <sim_path>
# ---------------------------------------------------------------------------
terminate_simulation() {
    local sim_name="$1"
    local sim_path="$2"

    printf "[%s] Terminating locked simulation %s ...\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name"

    (
        cd "$sim_path" || { printf "Error: Cannot cd to %s\n" "$sim_path" >&2; exit 1; }
        abq job="$sim_name" terminate
    )

    printf "[%s] Terminate command sent for %s.\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name"
}

# ---------------------------------------------------------------------------
# Main monitoring loop
# ---------------------------------------------------------------------------
printf "[%s] Lock monitor started: SIM_%03d to SIM_%03d | interval = %s min | lock threshold = %d identical STEP rows\n" \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$SIM_INI" "$SIM_FIN" "$WAIT_MINUTES" "$LOCK_ITERS"

while true; do

    running_count=0
    pending_count=0

    for (( i = SIM_INI; i <= SIM_FIN; i++ )); do

        sim_name="SIM_$(printf "%03d" "$i")"
        sim_path="$SIMS_DIR/$sim_name"
        simdir="$sim_path/${sim_name}.simdir"
        sta_file="$sim_path/${sim_name}.sta"

        # Skip if the simulation folder doesn't exist at all
        [[ ! -d "$sim_path" ]] && continue

        # Not running if .simdir is absent
        if [[ ! -d "$simdir" ]]; then
            # If only .inp file(s) are present, job hasn't started yet — keep waiting
            non_inp_files=$(find "$sim_path" -maxdepth 1 -type f ! -name "*.inp" | wc -l)
            if [[ "$non_inp_files" -eq 0 ]]; then
                (( pending_count++ ))
                printf "[%s] %s not yet started (only .inp present) -- will recheck later.\n" \
                    "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name"
            fi
            continue
        fi

        (( running_count++ ))

        printf "[%s] %s is running -- checking for lock ...\n" \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name"

        if is_locked "$sta_file"; then
            printf "[%s] %s LOCKED (last %d increments share the same STEP value).\n" \
                "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name" "$LOCK_ITERS"
            terminate_simulation "$sim_name" "$sim_path"
        else
            printf "[%s] %s is progressing normally.\n" \
                "$(date '+%Y-%m-%d %H:%M:%S')" "$sim_name"
        fi

    done

    # Stop only when nothing is running or pending
    if [[ "$running_count" -eq 0 && "$pending_count" -eq 0 ]]; then
        printf "[%s] All simulations in range SIM_%03d to SIM_%03d are done. Exiting.\n" \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$SIM_INI" "$SIM_FIN"
        exit 0
    fi

    printf "[%s] %d running, %d pending. Next check in %s minute(s)...\n\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$running_count" "$pending_count" "$WAIT_MINUTES"

    sleep "$WAIT_SECONDS"

done