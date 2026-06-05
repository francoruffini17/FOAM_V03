

from numpy import floor
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





vals = [5, 10, 20, 40, 80, 160]
for val in vals:
    mesh_path = f"C001_Mesh_files/A030_{val:03d}k.mesh.json"
    for i in range(5):
        create_grid_file(
            mesh_path,
            f"C001_Mesh_files/A030_{val:03d}k_H300{i+1}.grid.json",
            grid_n=int(floor(40*(1.5**i))),
            grid_m=int(floor(40*(1.5**i))),
            grid_remove_edge_nodes=True,
            show_plot=False,
            overlay_mesh=True,
            boundary_only=True,
        )


        create_gridhex_file(
            mesh_path,
            f"C001_Mesh_files/A030_{val:03d}k_I300{i+1}.gridhex.json",
            hexagon_size=1 / int(floor(40*(1.5**i))),
            grid_remove_edge_nodes=True,
            gridhex_pointy_top=False,
            delete_gridhex_isolated_bars=True,
            show_plot=False,
            overlay_mesh=True,
            boundary_only=True,
        )

        triangulation_generator(
            n_nodes_per_edge=int(floor(10*(1.5**i))),
            file_name=f"C001_Mesh_files/A030_{val:03d}k_T00{i+1}.tri",
        )

        # plot_triangulation(
        #     f"C001_Mesh_files/A030_{val:03d}k_T00{i+1}.tri",
        #     show_node_numbers=False,
        #     show_element_numbers=False,
        # )
