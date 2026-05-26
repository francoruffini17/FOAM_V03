# Agent Notes

Read [docs/CODEMAP.md](docs/CODEMAP.md) first. It is the quick map of this repository, the main workflows, generated-data areas, and the import graph links.

Guidelines for future LLM agents:

- Prefer source files under `A001_functions/`, `B001_Mesh_creator/`, `D001_Input_files_creator/`, `F001_Video_properties_files/`, and `A001_tests/` before opening large notebooks or generated outputs.
- Avoid bulk-reading generated data and binary-heavy folders: `C001_Mesh_files/`, `E001_Simulations/`, `I001_Results/`, `I002_Videos/`, `Temp/`, `logs/`, cache directories, and `node_modules/`.
- Use Python AST when updating local Python import relationships. Solid graph arrows mean the local target file exists; dashed arrows mean the import looks local but the target file was not found.
- Abaqus-specific scripts require Abaqus Python modules such as `abaqusConstants` and `odbAccess`; do not expect them to run in a normal Python environment.
- The codebase uses namespace-style imports and `sys.path` adjustments in scripts. There is a typo file `A001_functions/__initi__.py`, not a normal `__init__.py`.

