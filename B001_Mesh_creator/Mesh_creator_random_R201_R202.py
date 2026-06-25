"""
Mesh_creator_random_R201_R202
=============================
RSA random foam meshes sharing the same geometry as R200 (same holes,
porosity ≈ 0.60, right-skew distribution, seed=42) but at different
FE mesh densities:

  R201  — coarser mesh,  mesh_size = 0.0054  → target ≈ 15 000 elements
  R202  — finer   mesh,  mesh_size = 0.0027  → target ≈ 60 000 elements

Only the triangulation/quadrangulation density changes; the foam geometry
(hole centres, radii, domain, periodicity) is identical to R200.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_random_mesh,
    create_gridhex_file,
)

# -----------------------------------------------------------------------
# Shared foam geometry  (identical to R200)
# -----------------------------------------------------------------------
BASE_CFG = dict(
    domain_size=1.0,
    porosity=0.60,
    min_hole_size=0.01,
    max_hole_size=0.25,
    min_distance_between_holes=0.01,
    seed=42,
    edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
    hole_size_distribution='right_skew',
    hole_size_skew_strength=2.5,
    placement_algorithm='rsa',
)

COMMON_MESH_KWARGS = dict(
    export_mesh=True,
    export_vtk=False,
    show_plot=False,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    periodic="both",
)

# -----------------------------------------------------------------------
# Meshes to generate
# -----------------------------------------------------------------------
MESHES = [
    dict(name="R201", mesh_size=0.0054, gridhex_size=1/60),  # ~15 000 elements
    dict(name="R202", mesh_size=0.0027, gridhex_size=1/60),  # ~60 000 elements
]

# -----------------------------------------------------------------------
# Generate
# -----------------------------------------------------------------------
for spec in MESHES:
    name      = spec["name"]
    mesh_path = f"C001_Mesh_files/{name}.mesh.json"

    print(f"\n{'='*60}")
    print(f"Generating {name}  (mesh_size={spec['mesh_size']})")
    print(f"{'='*60}")

    cfg = MeshConfigRand(**BASE_CFG)

    generator, mesh = create_random_mesh(
        config=cfg,
        filepath=mesh_path,
        mesh_size=spec["mesh_size"],
        **COMMON_MESH_KWARGS,
    )

    print(f"{name}: {len(generator.hole_centers)} holes | "
          f"{mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")

    gridhex_path = f"C001_Mesh_files/{name}_I3002.gridhex.json"
    create_gridhex_file(
        mesh_path,
        gridhex_path,
        hexagon_size=spec["gridhex_size"],
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
        show_plot=False,
        overlay_mesh=False,
        boundary_only=True,
    )
    print(f"Gridhex overlay saved -> {gridhex_path}")

print("\nDone — R201 and R202 created.")
