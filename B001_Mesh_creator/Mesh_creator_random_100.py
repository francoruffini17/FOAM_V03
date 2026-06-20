"""
Mesh_creator_random_100
=======================
Random foam mesh with right-skew hole-size distribution and high porosity (0.65).

All three placement algorithms are run with identical parameters so the best
result can be chosen by inspection:

  rsa  – Random Sequential Addition  -> C001_Mesh_files/R100_rsa.mesh.json
  vgp  – Void-Guided Placement       -> C001_Mesh_files/R100_vgp.mesh.json
  ls   – Jittered triangular lattice -> C001_Mesh_files/R100_ls.mesh.json

Comment out the two you don't need before wiring this mesh to a simulation.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_random_mesh,
    preview_random_mesh,
)

# ---------------------------------------------------------------------------
# Shared configuration
# ---------------------------------------------------------------------------
# right_skew + high skew_strength -> many small holes -> more holes fit at the
# same porosity target, and small holes are easier for RSA/VGP/LS to pack
# tightly without jamming.
BASE_PARAMS = dict(
    domain_size=1.0,
    porosity=0.9,
    min_hole_size=0.04,
    max_hole_size=0.09,
    min_distance_between_holes=0.01,
    seed=42,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
    hole_size_distribution='right_skew',
    hole_size_skew_strength=4.0,
)

MESH_COMMON = dict(
    export_mesh=True,
    export_vtk=False,
    show_plot=True,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.005,
    periodic="both",
)

# ---------------------------------------------------------------------------
# RSA – Random Sequential Addition
# ---------------------------------------------------------------------------
cfg_rsa = MeshConfigRand(**BASE_PARAMS, placement_algorithm='rsa')

generator_rsa, mesh_rsa = create_random_mesh(
    config=cfg_rsa,
    filepath="C001_Mesh_files/R100_rsa.mesh.json",
    **MESH_COMMON,
)

# ---------------------------------------------------------------------------
# VGP – Void-Guided Placement
# ---------------------------------------------------------------------------
cfg_vgp = MeshConfigRand(**BASE_PARAMS, placement_algorithm='vgp')

generator_vgp, mesh_vgp = create_random_mesh(
    config=cfg_vgp,
    filepath="C001_Mesh_files/R100_vgp.mesh.json",
    **MESH_COMMON,
)

# ---------------------------------------------------------------------------
# LS – Jittered triangular-lattice packing
# ---------------------------------------------------------------------------
cfg_ls = MeshConfigRand(**BASE_PARAMS, placement_algorithm='ls')

generator_ls, mesh_ls = create_random_mesh(
    config=cfg_ls,
    filepath="C001_Mesh_files/R100_ls.mesh.json",
    **MESH_COMMON,
)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n=== Mesh_creator_random_100 summary ===")
for algo, gen, mesh in (
    ("rsa", generator_rsa, mesh_rsa),
    ("vgp", generator_vgp, mesh_vgp),
    ("ls",  generator_ls,  mesh_ls),
):
    print(f"  {algo:3s}: {len(gen.hole_centers):3d} holes  |  "
          f"{mesh.n_nodes:6d} nodes  {mesh.n_elements:6d} elements  "
          f"-> C001_Mesh_files/R100_{algo}.mesh.json")
