"""
Mesh_creator_rhombic_S1000
==========================
Rhombic-packed foam mesh with the same target properties as SIM_1000
(R1000): porosity 0.60, ~80 k nodes, periodic on both axes. Holes sit on
a general oblique lattice (two equal-length lattice vectors at
lattice_angle_deg=75, between the hexagonal 60-degree and square
90-degree special cases) instead of SIM_1000's random placement — this
is the "new ordering" requested alongside the existing hexagonal packing.

This script:
  1. Creates  C001_Mesh_files/RH1000.mesh.json
  2. Creates  C001_Mesh_files/RH1000_I3002.gridhex.json  (hex overlay, hexagon_size=1/60)

Configuration mirrors SIM 1000 / A1000:
  - porosity  = 0.60
  - n_holes_width = 9
  - edge padding  = 0.01 on all sides
  - periodic      = both
  - element_type  = BOTH
  - lattice_angle_deg = 75  (60 -> hexagonal, 90 -> square)

mesh_size = 0.0028 targets ~80 000 nodes, same recipe as A1000/R1000.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfigRhombic,
    create_rhombic_mesh,
    create_gridhex_file,
)


# -----------------------------------------------------------------------
# 1.  FE mesh
# -----------------------------------------------------------------------
cfg = MeshConfigRhombic(
    domain_size=1.0,
    n_holes_width=9,
    porosity=0.60,
    lattice_angle_deg=75.0,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)

mesh_path = "C001_Mesh_files/RH1000.mesh.json"

generator, mesh = create_rhombic_mesh(
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

print(f"\nRH1000: {mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")


# -----------------------------------------------------------------------
# 2.  Gridhex overlay for I-series reduction (I3002)
# -----------------------------------------------------------------------
gridhex_path = "C001_Mesh_files/RH1000_I3002.gridhex.json"

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
