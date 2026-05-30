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
    create_random_mesh,
    export_delaunay_vtk_from_json,
    export_voronoi_vtk_from_json,
    preview_random_mesh,
)



cfg = MeshConfig(domain_size=1.0, n_holes_width=10, porosity=0.572)






# mesh_path = f"C001_Mesh_files/A001.mesh.json"

# generator, mesh = create_hexagonal_mesh_2(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=True,
#     show_plot=True,
#     show_periodic_matching=False,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     elements_around_hole=48,
#     mesh_size_factor=1.12,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )





# mesh_path = f"C001_Mesh_files/A002.mesh.json"

# generator, mesh = create_hexagonal_mesh_2(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=False,
#     show_plot=True,
#     show_periodic_matching=False,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     elements_around_hole=32,
#     mesh_size_factor=1.2,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )




# mesh_path = f"C001_Mesh_files/A003.mesh.json"

# generator, mesh = create_hexagonal_mesh_2(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=False,
#     show_plot=True,
#     show_periodic_matching=False,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     elements_around_hole=24,
#     mesh_size_factor=1.4,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )



# mesh_path = f"C001_Mesh_files/A004.mesh.json"

# generator, mesh = create_hexagonal_mesh_2(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=True,
#     show_plot=True,
#     show_periodic_matching=False,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     elements_around_hole=24,
#     mesh_size_factor=2,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )




mesh_path = f"C001_Mesh_files/A005.mesh.json"

generator, mesh = create_hexagonal_mesh_2(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    show_plot=False,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    elements_around_hole=80,
    mesh_size_factor=1.305,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)
