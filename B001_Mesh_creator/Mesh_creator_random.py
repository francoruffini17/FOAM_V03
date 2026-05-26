import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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


RUN_CREATION = False


for i in range(1, 2):
    cfg = MeshConfigRand(
        domain_size=1.0,
        porosity=0.572,
        min_hole_size=0.01,
        max_hole_size=0.09,
        min_distance_between_holes=0.01,
        seed=42 + i,
    )

    preview_random_mesh(
        config=cfg,
        allow_cut_left=False,
        allow_cut_right=False,
        allow_cut_bottom=False,
        allow_cut_top=False,
        periodic="both",
        edge_left=0.01,
        edge_right=0.01,
        edge_bottom=0.01,
        edge_top=0.01,
    )

    if not RUN_CREATION:
        continue

    mesh_path = f"C001_Mesh_files/R601{i}_random_mesh.mesh.json"

    generator, mesh = create_random_mesh(
        config=cfg,
        filepath=mesh_path,
        export_mesh=True,
        show_plot=False,
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

    export_voronoi_vtk_from_json(mesh_path)
    export_delaunay_vtk_from_json(mesh_path)
    create_graph_file(
        mesh_path,
        f"C001_Mesh_files/R601{i}_G2000.graph.json",
        graph_characteristic_distance=0.01,
    )
    create_grid_file(
        mesh_path,
        f"C001_Mesh_files/R601{i}_H2001.grid.json",
        grid_n=301,
        grid_m=301,
        grid_remove_edge_nodes=True,
    )
    create_gridhex_file(
        mesh_path,
        f"C001_Mesh_files/R601{i}_I2002.gridhex.json",
        hexagon_size=1 / 101,
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
    )
    create_gridhex_file(
        mesh_path,
        f"C001_Mesh_files/R601{i}_K2002.gridhex.json",
        hexagon_size=1 / 101,
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
    )
