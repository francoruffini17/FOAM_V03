import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfig,
    create_grid_file,
    create_gridhex_file,
    create_hexagonal_mesh_2,
)


CASES = [
    ("A3000", 0.7),
    ("A3100", 0.6),
    ("A3200", 0.5),
]


for prefix, porosity in CASES:
    cfg = MeshConfig(domain_size=1.0, n_holes_width=10, porosity=porosity)
    mesh_path = f"C001_Mesh_files/{prefix}_hexagonal_mesh.mesh.json"

    generator, mesh = create_hexagonal_mesh_2(
        config=cfg,
        filepath=mesh_path,
        export_mesh=True,
        show_plot=True,
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

    create_grid_file(
        mesh_path,
        f"C001_Mesh_files/{prefix}_H2002.grid.json",
        grid_n=601,
        grid_m=601,
        grid_remove_edge_nodes=True,
    )

    create_gridhex_file(
        mesh_path,
        f"C001_Mesh_files/{prefix}_I2003.gridhex.json",
        hexagon_size=1 / 201,
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
    )

    create_gridhex_file(
        mesh_path,
        f"C001_Mesh_files/{prefix}_K2002.gridhex.json",
        hexagon_size=1 / 201,
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
    )
