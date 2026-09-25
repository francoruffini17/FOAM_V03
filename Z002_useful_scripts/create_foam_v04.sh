#!/usr/bin/env bash
# Make an independent, clean FOAM_V04 workspace for the SIM_6000--6049 study.
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_dir="/Disk_F/FOAM_V04"

if [[ -e "$target_dir" ]]; then
    echo "Target already exists; refusing to merge into it: $target_dir" >&2
    exit 1
fi

mkdir -p "$target_dir"/{A001_functions,A001_tests,B001_Mesh_creator,C001_Mesh_files,D001_Input_files_creator,E001_Simulations,F001_Video_properties_files,H001_sh_files,I001_Results/OBJ_files,I001_Results/LITE,I001_Results/finished_simulations,I002_Videos/Video_3200,Temp,logs,docs}

# Source modules and tests, without generated caches or old simulation data.
for folder in A001_functions A001_tests B001_Mesh_creator; do
    rsync -a --prune-empty-dirs --include='*/' --include='*.py' --exclude='*' \
        "$source_dir/$folder/" "$target_dir/$folder/"
done

cp "$source_dir/D001_Input_files_creator/SIM_4000_family_common.py" "$target_dir/D001_Input_files_creator/"
cp "$source_dir/D001_Input_files_creator/SIM_6000_6040_lite_inp_creator.py" "$target_dir/D001_Input_files_creator/"
cp "$source_dir/F001_Video_properties_files/Video_properties_3200.py" "$target_dir/F001_Video_properties_files/"
cp "$source_dir/H001_sh_files/run_6000_6040_lite_refined.sh" "$target_dir/H001_sh_files/"
cp "$source_dir/docs/SIM_6000_6040_LITE_REFINED.md" "$target_dir/docs/"
cp "$source_dir/.gitignore" "$source_dir/AGENTS.md" "$target_dir/"

for mesh in A1000 R1000 S1000 RH1000 ST1000; do
    cp "$source_dir/C001_Mesh_files/${mesh}.mesh.json" "$target_dir/C001_Mesh_files/"
    cp "$source_dir/C001_Mesh_files/${mesh}_I3002.gridhex.json" "$target_dir/C001_Mesh_files/"
done

for sim in $(seq 6000 6049); do
    sim_name="SIM_${sim}"
    mkdir -p "$target_dir/E001_Simulations/$sim_name" \
        "$target_dir/I001_Results/LITE/$sim_name" \
        "$target_dir/I002_Videos/Video_3200/$sim_name"
    cp "$source_dir/E001_Simulations/$sim_name/$sim_name.inp" \
        "$target_dir/E001_Simulations/$sim_name/"
    cp "$source_dir/I001_Results/OBJ_files/$sim_name.json" \
        "$target_dir/I001_Results/OBJ_files/"
done

cat > "$target_dir/docs/CODEMAP.md" <<'EOF'
# FOAM_V04 codemap

This workspace contains only the SIM_6000--6049 neo-Hookean study.

- `A001_functions/`: mesh, Abaqus input, lite extraction/reduction, eigen replay, and video code.
- `B001_Mesh_creator/`: Python mesh generation source; the five required meshes are already in `C001_Mesh_files/`.
- `D001_Input_files_creator/`: common pressure-sweep builder and the 6000--6049 generator.
- `E001_Simulations/`: 50 input decks; each simulation directory otherwise starts empty.
- `I001_Results/OBJ_files/`: 50 simulation parameter JSON files.
- `I001_Results/LITE/`: empty per-simulation result directories to receive curves, geometry, metadata, and eigen spectra.
- `F001_Video_properties_files/Video_properties_3200.py`: five-panel diagnostic video configuration.
- `H001_sh_files/run_6000_6040_lite_refined.sh`: solve, extract, reduce, and refined eigen runner.
- `I002_Videos/Video_3200/`, `logs/`, `Temp/`: empty output areas.

See `docs/SIM_6000_6040_LITE_REFINED.md` for the parameters and commands.
EOF

echo "Created $target_dir with 50 input decks and empty result, log, and video areas."
