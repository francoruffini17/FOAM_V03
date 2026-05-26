---
name: foam-v02
description: "Working guide for the FOAM_V02 repository. Use when: navigating the foam simulation pipeline; editing mesh generation, Abaqus input creation, result extraction/reduction, or video/plot code; running or debugging any part of the hexagonal-mesh-to-video workflow; understanding the folder layout, import graph, or PKL data schemas."
---

# FOAM_V02 Repository Guide

## Repository Purpose

`FOAM_V02` is a research/simulation pipeline for 2D foam-like mesh studies. It creates hexagonal or random meshes, builds Abaqus input decks, extracts Abaqus results, reduces them into pickle/graph/interpolation datasets, and renders analysis plots and videos from notebooks and Python scripts.

---

## Folder Layout

| Folder | Role |
|--------|------|
| `A001_functions/` | Core Python library: mesh generation, Abaqus input writing, ODB extraction helpers, result reduction, stress interpolation, plotting, and video frame composition. |
| `A001_functions/Old/` | Legacy copies of older reducers, video helpers, and input creators. Some local-looking imports are now broken. |
| `A001_tests/` | pytest and script-style tests for mesh generation, stress interpolation, mapping, and reduced PKL outputs. |
| `B001_Mesh_creator/` | Mesh creation entry scripts, mostly calling `A001_functions.Hex_5`. |
| `C001_Mesh_files/` | **Generated** mesh artifacts: `.hex2`, `.grid`, `.gridhex`, `.graph`, `.per`, `.vtk`, metadata JSON. |
| `D001_Input_files_creator/` | Simulation-specific Abaqus input generator scripts; all import `A001_functions.abq_inp_file_creator`. |
| `E001_Simulations/` | **Generated** Abaqus simulation directories and solver outputs. |
| `F001_Video_properties_files/` | Video/plot config files that import `A001_functions.Video_functions`. |
| `H001_sh_files/` | Shell helpers for running, cleaning, locking, and terminating Abaqus jobs. |
| `I001_Results/` | **Generated** result pickles and processed result objects. |
| `I002_Videos/` | **Generated** video frame/output trees. |
| `J001_important_functions/` | Small plotting entry points, delegating to `A001_functions.plot_mesh_functions`. |
| `Presentation/` | Slides and generated presentation figures. |
| `Temp/`, `logs/` | Scratch and runtime output. |
| `my-app/` | Standalone React/Vite sandbox for a dynamic-system solver UI — **not** part of the Python/Abaqus pipeline. |
| Root notebooks | `SIM_*_analyzing*.ipynb`, `Check_*.ipynb`, `Presentation_Generator.ipynb` — analysis and plotting work. |

---

## Where to Look First (and What to Avoid)

**Prefer** source files under:
- `A001_functions/`
- `B001_Mesh_creator/`
- `D001_Input_files_creator/`
- `F001_Video_properties_files/`
- `A001_tests/`

**Avoid bulk-reading** (generated / heavy / binary):
- `C001_Mesh_files/`, `E001_Simulations/`, `I001_Results/`, `I002_Videos/`
- `Temp/`, `logs/`, `.pytest_cache/`, `__pycache__/`, `my-app/node_modules/`
- Root notebooks are large — inspect the Python modules behind them first.

---

## Main Workflow (End-to-End)

1. **Generate meshes** — `B001_Mesh_creator/*.py` or `A001_functions/Hex_5.py`; outputs land in `C001_Mesh_files/`.
2. **Create Abaqus input decks** — `D001_Input_files_creator/SIM_*_inp_creator.py` using `A001_functions/abq_inp_file_creator.py`.
3. **Run Abaqus** — shell scripts in `H001_sh_files/`; `How_to_run_scripts` lists commands such as `abq python A001_functions/abq_scriptV9.py`.
4. **Extract / reduce results** — `python -m A001_functions.Reduce_resultsV5`; root `reduce_inputs_*.txt` files parameterize reduction runs.
5. **Build plots / videos** — `python -m A001_functions.Video_executor` or `Video_executor_multiple`, using configs from `F001_Video_properties_files/`.
6. **Analyze outputs** — `SIM_*_analyzing*.ipynb`, `Check_*.ipynb`, `Presentation_Generator.ipynb`.

---

## Key Python Entry Points

| File | Key Symbols |
|------|-------------|
| `A001_functions/Hex_5.py` | `MeshData`, `GraphMeshData`, `HexagonalPackingGeometry`, `HexagonalMeshGenerator`, `MeshConfig`, `HexagonalMeshGenerator2`, `MeshConfigRand`, `RandomMeshGenerator`, `create_hexagonal_mesh`, `create_hexagonal_mesh_2`, `create_random_mesh`, `map_undeformed_to_deformed` |
| `A001_functions/mesh_functions.py` | Mesh parsing, surface/boundary utilities, adjacency/barycenter helpers, plotting, node/element IO |
| `A001_functions/abq_inp_file_creator.py` | `StepData`, `data`, `write_step_block`, `get_node_limits`, `S6` |
| `A001_functions/abq_scriptV9.py`, `abq_script_to_plot.py` | Abaqus ODB extraction — **Abaqus Python only** |
| `A001_functions/Read_resultsV5.py` | Raw reduced-data reader helpers |
| `A001_functions/Reduce_resultsV5.py` | `create_PKL_G`, `create_PKL_G2`, `create_PKL_G2_exact`, `create_PKL_T1`, `create_PKL_T2`, `create_PKL_J1`, `create_PKL_J2`, `create_PKL_K1`, `create_PKL_K2`, `create_PKL_H2`, `process_simulation` |
| `A001_functions/fem_stress_interpolation.py` | `compute_integration_points`, `interpolate_stress` |
| `A001_functions/Video_functions.py` | `graph_property`, `frame_animation`, `frame_animation_graph`, `frame_animation_T1`, `frame_variable`, `frames_combination`, `SimulationConfig`, `create_vid_from_frames_for_sim` |
| `run_and_time.py` | Generic timing wrapper for simulation commands |
| `Extract_videos.py` | Copies/extracts generated video assets |

---

## Compatibility and Legacy Notes

- **`A001_functions/__initi__.py`** is intentionally misspelled (not `__init__.py`). Imports rely on namespace-package behavior and `sys.path` manipulation in scripts. Do not rename this file.
- **Abaqus scripts** (`abq_scriptV9.py`, `abq_script_to_plot.py`) import `abaqusConstants` and `odbAccess`. They must be run with Abaqus Python, not system Python, and will fail if executed otherwise.
- **`A001_functions/Old/`** contains legacy files that reference missing local files (`Hex_pack_funct.py`, `Old/Read_resultsV5.py`). These broken imports are shown as dashed arrows in the import graphs.
- **`my-app/`** is a standalone React/Vite project. It is not part of the Python import graph and has its own `node_modules/`.

---

## Import Graph

The import graph was generated with Python AST over `.py` source files. Solid arrows = local import whose target exists. Dashed arrows = local-looking import whose target file is missing.

- [`repository_import_graph.mmd`](../../docs/repository_import_graph.mmd) — Mermaid
- [`repository_import_graph.dot`](../../docs/repository_import_graph.dot) — Graphviz DOT

When editing import relationships, use Python AST analysis rather than text search.

---

## PKL Result File Conventions

See `Files_structure` at the repository root for full schemas. Key naming pattern: `DATA_PICK_{SIM}_{TYPE}.pkl`. Time-series length conventions, and indexing differences between Abaqus IDs, mesh IDs, interpolation nodes, and force-chain bars are documented there.

---

## Long-Term Memory: Save What You Learn

Whenever you discover something important about the repository that is not already captured in this skill — structural conventions, undocumented behaviors, gotchas, verified commands, schema details, naming patterns, or anything that would save future agents time — **save it to repository memory immediately**.

### When to Save

Save a memory entry when you learn any of the following:

- A folder, file, or symbol whose purpose was unclear and is now confirmed
- An undocumented CLI command, argument, or flag that works
- A PKL schema field or indexing convention not in `Files_structure`
- A mesh or simulation parameter convention discovered by reading source
- A bug, workaround, or known limitation in the pipeline
- A `sys.path` trick or import pattern required to run a script
- Any Abaqus version constraint, environment variable, or job setting
- A notebook cell order dependency or state requirement
- Anything that contradicts or extends what is written in CODEMAP.md or AGENTS.md

### How to Save

Use the `memory` tool with `command: create` and path under `/memories/repo/`. Choose a short, descriptive filename. Use bullet points, not prose. Keep entries concise.

Example categories and paths:

| What you learned | Save to |
|-----------------|---------|
| PKL schema detail | `/memories/repo/pkl-schemas.md` |
| Mesh/simulation convention | `/memories/repo/mesh-conventions.md` |
| Abaqus job/environment note | `/memories/repo/abaqus-notes.md` |
| Import / `sys.path` trick | `/memories/repo/import-notes.md` |
| Verified CLI commands | `/memories/repo/cli-commands.md` |
| Folder/file purpose clarified | `/memories/repo/folder-notes.md` |
| Bug or known limitation | `/memories/repo/known-issues.md` |

If the target file already exists, use `command: str_replace` to append to it rather than creating a duplicate.

### What Not to Save

- Information already in this SKILL.md, CODEMAP.md, or AGENTS.md
- Generated output content (PKL values, mesh coordinates, simulation numbers)
- Temporary debugging notes or one-off observations with no reuse value
