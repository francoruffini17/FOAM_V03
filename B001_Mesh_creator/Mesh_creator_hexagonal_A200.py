"""
Mesh_creator_hexagonal_A200
===========================
Hexagonal foam mesh with porosity ≈ 0.60 — paired with R200 for comparison.

This script:
  1. Creates  C001_Mesh_files/A200.mesh.json
  2. Creates  C001_Mesh_files/A200_I3002.gridhex.json  (hex overlay for I-series reduction)

Mesh: hexagonal periodic packing, n_holes_width=9, porosity=0.60.
This gives ~77 uniform circular holes with diameter ≈ 0.092, closely matching
the mean hole size and porosity of R200 (random, right-skewed, 81 holes).

Abaqus input deck: see D001_Input_files_creator/SIM_710_inp_creator_hexagonal.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfig,
    create_hexagonal_mesh_2,
    create_gridhex_file,
)


# -----------------------------------------------------------------------
# 1.  FE mesh
# -----------------------------------------------------------------------
cfg = MeshConfig(
    domain_size=1.0,
    n_holes_width=9,
    porosity=0.60,
    edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
)

mesh_path = "C001_Mesh_files/A200.mesh.json"

generator, mesh = create_hexagonal_mesh_2(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    show_plot=True,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.004,
    periodic="both",
)

print(f"\nA200: {mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")


# -----------------------------------------------------------------------
# 2.  Gridhex overlay for I-series reduction (I3002)
# -----------------------------------------------------------------------
gridhex_path = "C001_Mesh_files/A200_I3002.gridhex.json"

create_gridhex_file(
    mesh_path,
    gridhex_path,
    hexagon_size=1 / 60,
    grid_remove_edge_nodes=True,
    gridhex_pointy_top=False,
    delete_gridhex_isolated_bars=True,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)

print(f"Gridhex overlay saved -> {gridhex_path}")
