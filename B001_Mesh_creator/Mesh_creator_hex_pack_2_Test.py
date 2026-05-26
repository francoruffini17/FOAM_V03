import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfig,
    create_hexagonal_mesh_2,
    create_graph_file,
    create_grid_file,
    export_delaunay_vtk_from_json,
    export_voronoi_vtk_from_json,
)

cfg = MeshConfig(domain_size=1.0, n_holes_width=2, porosity=0.7)

mesh_path = "C001_Mesh_files/A9998_hexagonal_mesh.mesh.json"

generator, mesh = create_hexagonal_mesh_2(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    show_plot=True,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type='BOTH',
    elements_around_hole=10,
    mesh_size_factor=1,
    periodic='both',
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)

export_voronoi_vtk_from_json(
    mesh_path,
    extra_rows_left=1,
    extra_rows_right=1,
    extra_rows_bottom=1,
    extra_rows_top=1,
)
export_delaunay_vtk_from_json(
    mesh_path,
    extra_rows_left=1,
    extra_rows_right=1,
    extra_rows_bottom=1,
    extra_rows_top=1,
)
create_graph_file(
    mesh_path,
    "C001_Mesh_files/G9998.graph.json",
    graph_characteristic_distance=0.01,
    extra_rows_left=1,
    extra_rows_right=1,
    extra_rows_bottom=1,
    extra_rows_top=1,
)
create_grid_file(
    mesh_path,
    "C001_Mesh_files/H9998.grid.json",
    grid_n=10,
    grid_m=10,
    grid_remove_edge_nodes=True,
)
