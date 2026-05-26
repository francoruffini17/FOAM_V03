#!/usr/bin/env bash

START="$1"
END="$2"

run_simulation_in_folder() {
    local folder="$1"
    if [[ ! -d "$folder" ]]; then
        printf "Skipping %s: Directory does not exist\n" "$folder" >&2
        return
    fi

    cd "$folder" || {
        printf "Failed to enter directory %s\n" "$folder" >&2
        return
    }

    if ! abq job="$folder" terminate; then
        printf "Simulation failed in %s\n" "$folder" >&2
    fi

    cd .. || {
        printf "Failed to return from directory %s\n" "$folder" >&2
        return
    }
}

validate_inputs() {
    if [[ ! "$START" =~ ^[0-9]+$ ]] || [[ ! "$END" =~ ^[0-9]+$ ]]; then
        printf "Error: Start and end must be numeric.\n" >&2
        return 1
    fi

    if (( START > END )); then
        printf "Error: Start value must be less than or equal to end value.\n" >&2
        return 1
    fi
}

main() {
    if ! validate_inputs; then
        return 1
    fi

    cd E001_Simulations || {
        printf "Error: Cannot access H001_sh_files directory.\n" >&2
        return 1
    }

    local i sim;
    for i in $(seq -f "%03g" "$START" "$END"); do
        sim="SIM_$i"
        printf "Running simulation in %s...\n" "$sim"
        run_simulation_in_folder "$sim"
    done

    printf "All simulations completed.\n"
}

main
