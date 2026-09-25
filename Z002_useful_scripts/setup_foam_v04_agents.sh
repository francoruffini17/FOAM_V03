#!/usr/bin/env bash
# Install project-local guidance for AI agents launched from FOAM_V04.
set -euo pipefail

target_dir="/Disk_F/FOAM_V04"
[[ -d "$target_dir" ]] || { echo "Missing $target_dir" >&2; exit 1; }
mkdir -p "$target_dir/.agents" "$target_dir/.codex" \
    "$target_dir/.github/skills/foam-v04"

cat > "$target_dir/AGENTS.md" <<'EOF'
# FOAM_V04 Agent Notes

Read [docs/CODEMAP.md](docs/CODEMAP.md) first, then
[docs/SIM_6000_6040_LITE_REFINED.md](docs/SIM_6000_6040_LITE_REFINED.md)
for the current simulations and commands.

- This workspace contains SIM_6000–6049 only: five ten-case neo-Hookean
  pressure sweeps. Geometry is the sole family-level variable. All cases use
  the same physical settings and the same eigen schedule (1105 snapshots;
  3× finer late sampling than SIM_5150).
- Prefer Python source in `A001_functions/`, `B001_Mesh_creator/`, and
  `D001_Input_files_creator/` before reading large generated files.
- The main workflow is `H001_sh_files/run_6000_6040_lite_refined.sh`:
  Abaqus solve, lite extraction, lite reduction, then eigen replay.
- `I001_Results/LITE/SIM_NNN/curves.npz` supplies reaction force, shear mean,
  and the tension/compression efficiencies used for `f`.
  `geometry.npz`, `metadata.json`, `mode0.npz`, and `spectrum.npz` support
  analysis and Video 3200.
- Render with `Video_properties_3200`; analyze all five families with
  `Z001_Results_Analizer/SIM_6000s_eigenvalue_vs_strain.ipynb`.
- Avoid bulk-reading generated mesh, simulation, result, video, cache, and
  log folders. Abaqus extraction requires Abaqus Python (`odbAccess`).
- `A001_functions/__initi__.py` is a typo retained from the source project;
  imports rely on namespace-package behavior. Use Python AST when changing
  local import relationships.
EOF

cat > "$target_dir/CLAUDE.md" <<'EOF'
# Claude Code guidance for FOAM_V04

Read `AGENTS.md` and `docs/CODEMAP.md` first. This is the independent
SIM_6000–6049 neo-Hookean workspace. Do not use paths or commands from
FOAM_V03 unless explicitly comparing against that project.

## Commands

From `/Disk_F/FOAM_V04`:

```bash
bash H001_sh_files/run_6000_6040_lite_refined.sh
python3 -m A001_functions.Video_executorV20 \
  --sim-num 6000 --properties-file Video_properties_3200
python3 -m pytest A001_tests/
```

The runner creates lite reaction-force and efficiency curves, geometry,
metadata, and refined near-zero eigenvalue spectra. Use
`Z001_Results_Analizer/SIM_6000s_eigenvalue_vs_strain.ipynb` for the
crossing and `f` analysis. Abaqus ODB extraction must run under Abaqus Python.
Read source code before large generated data.
EOF

cat > "$target_dir/.github/skills/foam-v04/SKILL.md" <<'EOF'
---
name: foam-v04
description: "Project guide for the FOAM_V04 SIM_6000–6049 neo-Hookean lite simulation, eigenvalue, analysis, and Video 3200 workflow."
---

# FOAM_V04 workflow

Read `AGENTS.md`, `docs/CODEMAP.md`, and
`docs/SIM_6000_6040_LITE_REFINED.md` before changing this project.

The five ten-case families differ only by mesh. All have the same pressure
sweep and loading. Each eigen replay uses 400 base intervals and 12 late
subdivisions after `t=0.84`, yielding 1105 samples and four near-zero modes.

Run the complete pipeline with
`bash H001_sh_files/run_6000_6040_lite_refined.sh`. The lite reducer creates
`curves.npz` for reaction force and `f`, plus `geometry.npz` and
`metadata.json`; the eigen replay creates `mode0.npz` and `spectrum.npz`.
Render with `Video_properties_3200` and analyze with
`Z001_Results_Analizer/SIM_6000s_eigenvalue_vs_strain.ipynb`.

Inspect Python source before generated outputs. Abaqus-only modules must run
under Abaqus Python. Preserve the namespace-style import convention.
EOF

echo 'FOAM_V04 agent guidance and local skill are ready.'
