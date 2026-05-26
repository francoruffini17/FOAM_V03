#!/usr/bin/env bash

set -euo pipefail

LOCK_EXT=".lck"
LOCK_PATHS=()

collect_lock_paths() {
    local lock_files;
    if ! lock_files=$(find . -type f -name "*${LOCK_EXT}"); then
        printf "Error: Failed to find lock files\n" >&2
        return 1
    fi

    while IFS= read -r line; do
        [[ -n "${line// /}" ]] && LOCK_PATHS+=("$line")
    done <<< "$lock_files"

    if [[ ${#LOCK_PATHS[@]} -eq 0 ]]; then
        printf "No lock files found.\n" >&2
        return 1
    fi
}

extract_job_name() {
    local lock_file="$1"
    local filename; filename=$(basename "$lock_file")

    if [[ "$filename" != *.lck ]]; then
        printf "Error: Invalid lock file: %s\n" "$lock_file" >&2
        return 1
    fi

    local job_name="${filename%.lck}"
    if [[ -z "$job_name" || "$job_name" =~ [^a-zA-Z0-9_-] ]]; then
        printf "Error: Invalid job name extracted: %s\n" "$job_name" >&2
        return 1
    fi

    printf "%s\n" "$job_name"
}

terminate_abq_job() {
    local job_name="$1"

    if [[ ! -d "$job_name" ]]; then
        printf "Warning: Directory does not exist: %s\n" "$job_name" >&2
        return 0
    fi

    if ! cd "$job_name"; then
        printf "Error: Failed to enter directory: %s\n" "$job_name" >&2
        return 1
    fi

    if ! abq job="$job_name" terminate; then
        printf "Error: Failed to terminate job '%s'\n" "$job_name" >&2
        cd - >/dev/null || return 1
        return 1
    fi

    cd - >/dev/null || return 1
}

main() {
    if ! collect_lock_paths; then
        return 1
    fi

    cd E001_Simulations || {
        printf "Error: Cannot access H001_sh_files directory.\n" >&2
        return 1
    }

    local lock; local job
    for lock in "${LOCK_PATHS[@]}"; do
        if ! job=$(extract_job_name "$lock"); then
            continue
        fi
        if ! terminate_abq_job "$job"; then
            printf "Failed to process job: %s\n" "$job" >&2
        fi
    done
}

main "$@"
