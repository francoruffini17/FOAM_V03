import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Triangulation_creator import (
    plot_triangulation,
    preview_triangulation_with_mesh,
    triangulation_generator,
)
from A001_functions.Hex_5 import (
    MeshConfig,
    create_graph_file,
    create_grid_file,
    create_gridhex_file,
    create_hexagonal_mesh_2,
    export_delaunay_vtk_from_json,
    export_voronoi_vtk_from_json,
    preview_random_mesh,
)





cfg = MeshConfig(
    domain_size=1.0,
    n_holes_width=10,
    porosity=0.572,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)

mesh_path = f"C001_Mesh_files/A03X.mesh.json"

generator, mesh = create_hexagonal_mesh_2(
    config=cfg,
    filepath=mesh_path,
    export_mesh=False,
    show_plot=False,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.00185,
    periodic="both",
)
