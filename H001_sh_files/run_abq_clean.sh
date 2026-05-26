#!/bin/bash

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <start_sim> <end_sim>"
    exit 1
fi

# Read input arguments
start_sim=$1
end_sim=$2

# Make paths relative to repo root (parent of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$ROOT_DIR/E001_Simulations" ]]; then
    SIMS_DIR="$ROOT_DIR/E001_Simulations"
else
    SIMS_DIR="$ROOT_DIR"
fi

cd "$SIMS_DIR" || { echo "Cannot access simulations directory: $SIMS_DIR"; exit 1; }

# Validate that start and end are integers and start <= end
re='^[0-9]+$'
if ! [[ $start_sim =~ $re && $end_sim =~ $re ]]; then
    echo "Error: start_sim and end_sim must be integers. Received: $start_sim $end_sim"
    exit 1
fi
if [ "$start_sim" -gt "$end_sim" ]; then
    echo "Error: start_sim must be <= end_sim"
    exit 1
fi

# Enable nullglob so globs that match nothing disappear (avoid literal patterns)
shopt -s nullglob

# Loop through the specified simulation numbers using zero-padded 3-digit names
for sim_padded in $(seq -f "%03g" "$start_sim" "$end_sim"); do
    sim_folder="SIM_$sim_padded"

    if [ -d "$sim_folder" ]; then
        echo "Processing $sim_folder..."
        cd "$sim_folder" || { echo "Failed to enter $sim_folder"; continue; }

        # Remove files named SIM_###.* except the .inp file
        for file in SIM_${sim_padded}.*; do
            # Skip the .inp file
            if [[ "$(basename "$file")" == "SIM_${sim_padded}.inp" ]]; then
                continue
            fi
            # echo "  removing: $file"
            rm -rf -- "$file"
        done

        # Optionally remove common auxiliary directories (odb, results, frames)
        for d in odb results frames; do
            if [ -d "$d" ]; then
                echo "  removing directory: $d"
                rm -rf -- "$d"
            fi
        done

        cd ..
    else
        echo "Folder $sim_folder does not exist, skipping..."
    fi
done

shopt -u nullglob

echo "Cleanup complete."
