"""
Mesh_creator_hexagonal_A1000
============================
Hexagonal foam mesh with porosity 0.60 — scaled-up version of A200 (~80 k nodes).

This script:
  1. Creates  C001_Mesh_files/A1000.mesh.json
  2. Creates  C001_Mesh_files/A1000_I3002.gridhex.json  (hex overlay, hexagon_size=1/60)

Configuration mirrors SIM 700 (A200):
  - porosity  = 0.60
  - n_holes_width = 9
  - edge padding  = 0.01 on all sides
  - periodic      = both
  - element_type  = BOTH

mesh_size = 0.0028 targets ~80 000 nodes (A200 used 0.004 → 39 103 nodes;
scaling as 1/sqrt(2) gives the estimate).  Adjust if the actual count differs.

Abaqus input deck: see D001_Input_files_creator/SIM_A1000_inp_creator_hexagonal.py
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
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)

mesh_path = "C001_Mesh_files/A1000.mesh.json"

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
    mesh_size=0.0028,
    periodic="both",
)

print(f"\nA1000: {mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")


# -----------------------------------------------------------------------
# 2.  Gridhex overlay for I-series reduction (I3002)
# -----------------------------------------------------------------------
gridhex_path = "C001_Mesh_files/A1000_I3002.gridhex.json"

create_gridhex_file(
    mesh_path,
    gridhex_path,
    hexagon_size=1 / 60,          # 0.016666...
    grid_remove_edge_nodes=True,
    gridhex_pointy_top=False,
    delete_gridhex_isolated_bars=True,
    show_plot=True,
    overlay_mesh=True,
    boundary_only=True,
)

print(f"Gridhex overlay saved -> {gridhex_path}")
