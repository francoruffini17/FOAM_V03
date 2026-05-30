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





# cfg = MeshConfigRand(
#     domain_size=1.0,
#     porosity=0.572,
#     min_hole_size=0.04,
#     max_hole_size=0.09,
#     min_distance_between_holes=0.01,
#     seed=42,
# )


# preview_random_mesh(
#     config=cfg,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )


mesh_path = f"C001_Mesh_files/R010.mesh.json"

# generator, mesh = create_random_mesh(
#     config=cfg,
#     filepath=mesh_path,
#     export_mesh=True,
#     show_plot=True,
#     show_periodic_matching=True,
#     allow_cut_left=False,
#     allow_cut_right=False,
#     allow_cut_bottom=False,
#     allow_cut_top=False,
#     element_type="BOTH",
#     elements_around_hole=48,
#     mesh_size_factor=3,
#     periodic="both",
#     edge_left=0.01,
#     edge_right=0.01,
#     edge_bottom=0.01,
#     edge_top=0.01,
# )

# # export_voronoi_vtk_from_json(mesh_path)
# # export_delaunay_vtk_from_json(mesh_path)

# create_graph_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_J2000.graph.json",
#     graph_characteristic_distance=0.01,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )

# create_grid_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_H2001.grid.json",
#     grid_n=51,
#     grid_m=51,
#     grid_remove_edge_nodes=True,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )

# create_gridhex_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_I2002.gridhex.json",
#     hexagon_size=1 / 151,
#     grid_remove_edge_nodes=True,
#     gridhex_pointy_top=False,
#     delete_gridhex_isolated_bars=True,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )

# create_gridhex_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_K2002.gridhex.json",
#     hexagon_size=1 / 151,
#     grid_remove_edge_nodes=True,
#     gridhex_pointy_top=False,
#     delete_gridhex_isolated_bars=True,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )




# triangulation_generator(
#     n_nodes_per_edge=51,
#     file_name="C001_Mesh_files/R010_T001.tri",
# )

# plot_triangulation(
#     "C001_Mesh_files/R010_T001.tri",
#     show_node_numbers=False,
#     show_element_numbers=False,
# )




# create_grid_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_H2000.grid.json",
#     grid_n=26,
#     grid_m=26,
#     grid_remove_edge_nodes=True,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )

# create_gridhex_file(
#     mesh_path,
#     f"C001_Mesh_files/R010_I2000.gridhex.json",
#     hexagon_size=1 / 51,
#     grid_remove_edge_nodes=True,
#     gridhex_pointy_top=False,
#     delete_gridhex_isolated_bars=True,
#     show_plot=True,
#     overlay_mesh=True,
#     boundary_only=True,
# )


# triangulation_path = "C001_Mesh_files/R010_T001.tri"

# triangulation_generator(
#     n_nodes_per_edge=9,
#     file_name=triangulation_path,
# )


# preview_triangulation_with_mesh(
#     mesh_file=mesh_path,
#     triangulation_file=triangulation_path,
#     snap_to_mesh_nodes=True,
#     show_original_triangulation=True,
#     show_mesh_nodes=True,
#     show_triangulation_nodes=True,
# )












cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.572,
    min_hole_size=0.04,
    max_hole_size=0.09,
    min_distance_between_holes=0.01,
    seed=42,
)



mesh_path = f"C001_Mesh_files/R001.mesh.json"

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
    elements_around_hole=48,
    mesh_size_factor=2,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)





mesh_path = f"C001_Mesh_files/R002.mesh.json"

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
    elements_around_hole=48/1.5,
    mesh_size_factor=2.7,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)




mesh_path = f"C001_Mesh_files/R003.mesh.json"

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
    elements_around_hole=int(48/2),
    mesh_size_factor=4,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)



mesh_path = f"C001_Mesh_files/R004.mesh.json"

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
    elements_around_hole=int(48/4),
    mesh_size_factor=2*4,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)
