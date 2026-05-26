# Mesh File Extensions

Mesh geometry and derived sampling meshes are now JSON objects. The legacy
plain-text mesh, graph, grid, gridhex, and periodic-pair sidecar formats have
been removed from the code paths.

## Quick Reference

| Extension | Main purpose | Typical creator |
| --- | --- | --- |
| `.mesh.json` | Primary finite-element mesh object. | `create_hexagonal_mesh_2(...)`, `create_random_mesh(...)` |
| `.graph.json` | Subdivided Voronoi graph of the holes. | `create_graph_file(mesh_file=...)` |
| `.grid.json` | Regular Cartesian sampling grid. | `create_grid_file(mesh_file=...)` |
| `.gridhex.json` | Hexagonal sampling grid. | `create_gridhex_file(mesh_file=...)` |
| `.vtk` | Visualization/export format for ParaView and other VTK readers. | `export_mesh_vtk_from_json(...)`, `export_voronoi_vtk_from_json(...)`, `export_delaunay_vtk_from_json(...)` |
| `.tri` | Standalone triangular sampling mesh created by `Triangulation_creator.py`. | `triangulation_generator(...)` |
| `.inp` | Abaqus input deck, created after mesh generation. | `D001_Input_files_creator/*.py` |

## `.mesh.json`

The `.mesh.json` file is the source of truth for the finite-element mesh. It
stores mesh geometry, connectivity, labels, boundary sets, hole data, periodic
node matches, and the parameters used to create the mesh.

Top-level structure:

```json
{
  "format_version": 1,
  "type": "mesh",
  "mesh_kind": "random",
  "created_by": "create_random_mesh",
  "parameters": {},
  "geometry": {},
  "nodes": [],
  "elements": [],
  "element_types": [],
  "boundary_nodes": {},
  "hole_boundary_nodes": [],
  "hole_classifications": [],
  "periodic": {},
  "summary": {}
}
```

Notes:

- `mesh_kind` is either `random` or `hexagonal_packing`.
- `parameters` contains the generator inputs such as porosity, hole counts,
  random seed, cut-edge flags, mesh sizing, edge strips, element type, and
  periodic mode.
- `geometry` includes the generated hole centers and radii, so derived files
  can be created from the saved mesh object without recomputing from element
  connectivity.
- `nodes` store `x`, `y`, and `label`.
- `elements` store 0-based triangular or quadrilateral connectivity.
- `periodic.left_right_pairs` and `periodic.top_bottom_pairs` store the
  periodic node matching directly in the mesh object. There is no separate
  periodic-pair sidecar file.

Example:

```text
C001_Mesh_files/R6011_random_mesh.mesh.json
```

## `.graph.json`

The `.graph.json` file stores a subdivided Voronoi graph mesh. It references
the source mesh file and stores only the graph object plus graph-creation
parameters.

Top-level structure:

```json
{
  "format_version": 1,
  "type": "graph",
  "created_by": "create_graph_json",
  "source_mesh_path": "C001_Mesh_files/R6011_random_mesh.mesh.json",
  "source_mesh_parameters": {},
  "parameters": {},
  "nodes": [],
  "bars": [],
  "summary": {}
}
```

Notes:

- `nodes` store `x`, `y`, and integer `id`.
- `id=1` means an original Voronoi node.
- `id=2` means a subdivision node inserted along a Voronoi bar.
- `bars` store `start`, `end`, and `bar_number`.

Example:

```text
C001_Mesh_files/R6011_G2000.graph.json
```

## `.grid.json`

The `.grid.json` file stores a regular Cartesian sampling grid using the same
JSON graph object layout as `.graph.json`.

Notes:

- `type` is `grid`.
- Current Cartesian grid nodes use `id=0`.
- Bars connect immediate horizontal and vertical neighbors.
- Nodes inside holes and optional edge nodes are removed using the hole data
  saved in the source `.mesh.json` file.

Example:

```text
C001_Mesh_files/R6011_H2001.grid.json
```

## `.gridhex.json`

The `.gridhex.json` file stores a hexagonal sampling grid using the same JSON
graph object layout as `.graph.json`.

Notes:

- `type` is `gridhex`.
- Each auxiliary hexagon has a center node with `id=1`.
- Peripheral nodes, placed at vertices and edge midpoints, use `id=2`.
- Nodes inside holes and optional edge nodes are removed using the hole data
  saved in the source `.mesh.json` file.

Example:

```text
C001_Mesh_files/R6011_I2002.gridhex.json
```

## `.vtk`

VTK exports remain plain VTK files for visualization. They are created from
the mesh JSON object:

```python
export_mesh_vtk_from_json("C001_Mesh_files/R6011_random_mesh.mesh.json")
export_voronoi_vtk_from_json("C001_Mesh_files/R6011_random_mesh.mesh.json")
export_delaunay_vtk_from_json("C001_Mesh_files/R6011_random_mesh.mesh.json")
```

## Typical Workflow

```python
from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_random_mesh,
    create_graph_file,
    create_grid_file,
    create_gridhex_file,
)

cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.572,
    min_hole_size=0.04,
    max_hole_size=0.09,
    min_distance_between_holes=0.01,
    seed=42,
)

mesh_path = "C001_Mesh_files/R6011_random_mesh.mesh.json"

create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    periodic="both",
)

create_graph_file(
    mesh_path,
    "C001_Mesh_files/R6011_G2000.graph.json",
    graph_characteristic_distance=0.01,
)

create_grid_file(
    mesh_path,
    "C001_Mesh_files/R6011_H2001.grid.json",
    grid_n=301,
    grid_m=301,
)

create_gridhex_file(
    mesh_path,
    "C001_Mesh_files/R6011_I2002.gridhex.json",
    hexagon_size=1 / 101,
)
```
