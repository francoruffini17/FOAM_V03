import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfig,
    create_graph_file,
    create_grid_file,
    create_gridhex_file,
    create_hexagonal_mesh_2,
)



cfg = MeshConfig(domain_size=1.0, n_holes_width=10, porosity=0.5)
mesh_path = f"C001_Mesh_files/A001.mesh.json"

generator, mesh = create_hexagonal_mesh_2(
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
    mesh_size_factor=1,
    periodic="both",
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)



create_graph_file(
    mesh_path,
    f"C001_Mesh_files/A010_J2000.graph.json",
    graph_characteristic_distance=0.01,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)

create_grid_file(
    mesh_path,
    f"C001_Mesh_files/A010_H2001.grid.json",
    grid_n=51,
    grid_m=51,
    grid_remove_edge_nodes=True,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)

create_gridhex_file(
    mesh_path,
    f"C001_Mesh_files/A010_I2002.gridhex.json",
    hexagon_size=1 / 151,
    grid_remove_edge_nodes=True,
    gridhex_pointy_top=False,
    delete_gridhex_isolated_bars=True,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)

create_gridhex_file(
    mesh_path,
    f"C001_Mesh_files/A010_K2002.gridhex.json",
    hexagon_size=1 / 151,
    grid_remove_edge_nodes=True,
    gridhex_pointy_top=False,
    delete_gridhex_isolated_bars=True,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)
