import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Triangulation_creator import (
    plot_triangulation,
    preview_triangulation_with_mesh,
    triangulation_generator,
)
from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_graph_file,
    create_grid_file,
    create_gridhex_file,
    create_random_mesh,
    export_delaunay_vtk_from_json,
    export_voronoi_vtk_from_json,
    preview_random_mesh,
)





cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.572,
    min_hole_size=0.04,
    max_hole_size=0.09,
    min_distance_between_holes=0.01,
    seed=42,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)


# preview_random_mesh(
#     config=cfg,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     periodic="both",
# )






# mesh_path = f"C001_Mesh_files/R020.mesh.json"

# generator, mesh = create_random_mesh(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=True,
#     show_plot=False,
#     show_periodic_matching=True,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     mesh_size=0.0028,
#     periodic="both",
# )





# mesh_path = f"C001_Mesh_files/R021.mesh.json"

# generator, mesh = create_random_mesh(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=True,
#     show_plot=False,
#     show_periodic_matching=True,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     mesh_size=0.004,
#     periodic="both",
# )




mesh_path = f"C001_Mesh_files/R022.mesh.json"

generator, mesh = create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    show_plot=True,
    show_periodic_matching=True,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.0057,
    periodic="both",
)



mesh_path = f"C001_Mesh_files/R023.mesh.json"

generator, mesh = create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    show_plot=True,
    show_periodic_matching=True,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.0087,
    periodic="both",
)




mesh_path = f"C001_Mesh_files/R024.mesh.json"

generator, mesh = create_random_mesh(
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
    mesh_size=0.013,
    periodic="both",
)

