# Repository Codemap

## Purpose

`FOAM_V02` is a research/simulation pipeline for 2D foam-like mesh studies. It creates hexagonal/random meshes, builds Abaqus input decks, extracts Abaqus results, reduces them into pickle/graph/interpolation datasets, and renders analysis plots/videos from notebooks and Python scripts.

## Top-Level Folders

- `A001_functions/`: core Python library for mesh generation, Abaqus input writing, ODB extraction helpers, result reduction, stress interpolation, plotting, and video frame composition.
- `A001_functions/Old/`: legacy copies of older reducers, video helpers, and input creators. Some local-looking imports are now missing.
- `A001_tests/`: pytest and script-style tests for mesh generation, stress interpolation, mapping, and reduced PKL outputs.
- `B001_Mesh_creator/`: mesh creation entry scripts, mostly calling `A001_functions.Hex_5`.
- `C001_Mesh_files/`: generated mesh artifacts such as `.mesh.json`, `.graph.json`, `.grid.json`, `.gridhex.json`, and `.vtk`.
- `D001_Input_files_creator/`: simulation-specific Abaqus input generator scripts. These all import `A001_functions.abq_inp_file_creator`.
- `E001_Simulations/`: generated Abaqus simulation directories and solver outputs.
- `F001_Video_properties_files/`: video/plot configuration files that import `A001_functions.Video_functions`.
- `H001_sh_files/`: shell helpers for running, cleaning, locking, and terminating Abaqus jobs.
- `I001_Results/`: generated result pickles and processed result objects. `Files_structure` documents the PKL schemas.
- `I002_Videos/`: generated video frame/output trees.
- `J001_important_functions/`: small plotting entry points, currently delegating to `A001_functions.plot_mesh_functions`.
- `Presentation/`: slides and generated presentation figures.
- `Temp/`, `logs/`: scratch and runtime output.
- `my-app/`: React/Vite sandbox for a dynamic-system solver UI; separate from the Python/Abaqus pipeline.
- Root notebooks: analysis notebooks for SIM ranges and plotting/presentation work.

## Main Workflows

1. Generate meshes with `B001_Mesh_creator/*.py` or directly from `A001_functions/Hex_5.py`; outputs usually land in `C001_Mesh_files/`.
2. Create Abaqus input decks with `D001_Input_files_creator/SIM_*_inp_creator.py`, which use `A001_functions/abq_inp_file_creator.py`.
3. Run Abaqus through scripts in `H001_sh_files/`; `How_to_run_scripts` lists commands such as `abq python A001_functions/abq_scriptV9.py`.
4. Extract/reduce simulation outputs with `python -m A001_functions.Reduce_resultsV5`; root `reduce_inputs_*.txt` files appear to parameterize reduction runs.
5. Build plots/videos with `python -m A001_functions.Video_executor` or `Video_executor_multiple`, using configs from `F001_Video_properties_files/`.
6. Analyze outputs in `SIM_*_analyzing*.ipynb`, `Check_*.ipynb`, and `Presentation_Generator.ipynb`.

## Important Python Entry Points

- `A001_functions/Hex_5.py`: central mesh module. Important classes include `MeshData`, `GraphMeshData`, `HexagonalPackingGeometry`, `HexagonalMeshGenerator`, `MeshConfig`, `HexagonalMeshGenerator2`, `MeshConfigRand`, and `RandomMeshGenerator`. Important functions include `create_hexagonal_mesh`, `create_hexagonal_mesh_2`, `create_random_mesh`, `create_graph_file`, `create_grid_file`, `create_gridhex_file`, `read_mesh_json`, `read_graph_mesh`, `map_undeformed_to_deformed`, and preview/export helpers.
- `A001_functions/mesh_functions.py`: mesh parsing, surface/boundary utilities, adjacency/barycenter helpers, plotting, and node/element IO.
- `A001_functions/abq_inp_file_creator.py`: Abaqus input writer with `StepData`, `data`, `write_step_block`, `get_node_limits`, and `S6`.
- `A001_functions/abq_scriptV9.py` and `abq_script_to_plot.py`: Abaqus ODB extraction scripts. They require Abaqus Python.
- `A001_functions/Read_resultsV5.py`: raw reduced-data reader helpers.
- `A001_functions/Reduce_resultsV5.py`: main reduction module. Important functions include `create_PKL_G`, `create_PKL_G2`, `create_PKL_G2_exact`, `create_PKL_T1`, `create_PKL_T2`, `create_PKL_J1`, `create_PKL_J2`, `create_PKL_K1`, `create_PKL_K2`, `create_PKL_H2`, and `process_simulation`.
- `A001_functions/fem_stress_interpolation.py`: integration-point stress interpolation with `compute_integration_points` and `interpolate_stress`.
- `A001_functions/Video_functions.py`: frame/video composition classes and helpers including `graph_property`, `frame_animation`, `frame_animation_graph`, `frame_animation_T1`, `frame_variable`, `frames_combination`, `SimulationConfig`, and `create_vid_from_frames_for_sim`.
- `run_and_time.py`: generic timing wrapper for simulation commands.
- `Extract_videos.py`: copies/extracts generated video assets.

## Generated Data And Heavy Outputs

Avoid opening these broadly unless the task specifically requires their contents: `C001_Mesh_files/`, `E001_Simulations/`, `I001_Results/`, `I002_Videos/`, `Temp/`, `logs/`, `.pytest_cache/`, `__pycache__/`, and `my-app/node_modules/`. Many root notebooks are large; inspect Python modules first when possible.

`Files_structure` is useful when working with `I001_Results/` pickle files. It documents naming such as `DATA_PICK_{SIM}_{TYPE}.pkl`, time-series length conventions, and indexing differences between Abaqus IDs, mesh IDs, interpolation nodes, and force-chain bars.

## Compatibility And Legacy Notes

- `A001_functions/__initi__.py` is misspelled and does not behave as a normal package initializer. Imports currently rely on namespace-package behavior and scripts that modify `sys.path`.
- Abaqus extraction modules import external Abaqus-only names (`abaqusConstants`, `odbAccess`) and should be run with Abaqus Python, not system Python.
- Legacy files under `A001_functions/Old/` reference missing local files such as `A001_functions/Hex_pack_funct.py` and `A001_functions/Old/Read_resultsV5.py`; these are dashed in the import graphs.
- `my-app/` is a standalone React/Vite project and is not part of the Python import graph.

## Import Graphs

The local Python import graph was generated with Python AST over source-ish `.py` files, excluding caches, `node_modules`, and generated output trees (`E001_Simulations/`, `I001_Results/`, `I002_Videos/`, `Temp/`). Solid arrows indicate local imports whose files exist; dashed arrows indicate local-looking imports whose target file is missing.

- [Mermaid import graph](repository_import_graph.mmd)
- [Graphviz DOT import graph](repository_import_graph.dot)
