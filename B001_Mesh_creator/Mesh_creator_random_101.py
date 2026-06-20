"""
Mesh_creator_random_101
=======================
RSA random foam mesh with right-skew hole-size distribution, ~0.70 porosity.

Empirical sweep (right_skew, seed=42) — best confirmed results:

  min=0.010  d=0.001  s=1.5  → achieved=0.7001  (379 holes)  PRIMARY
  min=0.010  d=0.0005 s=1.5  → achieved=0.7000  (340 holes)  ALT-A
  min=0.015  d=0.0005 s=1.5  → achieved=0.7141  (371 holes)  ALT-B (target=0.72)

Why these parameters work:
  hole_size_skew_strength=1.5  — Beta(2,3).  Visually right-skewed AND keeps
    the RSA pre-sample pool large enough; stronger skew (e.g. s=4 from R100)
    starves the pool and achieves < 0.45 porosity regardless of other settings.
  min_hole_size=0.010 (diameter)  — small holes fill jammed gaps left by large
    ones, letting RSA pack 10 % more area than with min_hole=0.04.
  min_distance_between_holes=0.001  — dominant lever; raises the packing ceiling
    from ~0.71 to ~0.85.  Smaller d (e.g. 0.0005) gives marginal extra porosity
    but needs mesh_size ≤ 0.0005, producing very large meshes.

Output: C001_Mesh_files/R101.mesh.json
        C001_Mesh_files/R101_holes.png
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_random_mesh,
)

# ---------------------------------------------------------------------------
# PRIMARY — d=0.001, min_hole=0.010
# Empirically confirmed: achieved porosity = 0.7001 (379 holes, seed=42)
# ---------------------------------------------------------------------------
cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.70,
    min_hole_size=0.010,                  # diameter; smaller → fills RSA gaps
    max_hole_size=0.09,
    min_distance_between_holes=0.001,     # key porosity lever (was 0.01 in R100)
    seed=42,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
    hole_size_distribution='right_skew',  # Beta(2, 2*skew_strength) = Beta(2,3)
    hole_size_skew_strength=1.5,          # visually right-skewed, pool-safe
    placement_algorithm='rsa',
)

# ---------------------------------------------------------------------------
# ALT-A — d=0.0005 (fewer holes, finer mesh required: mesh_size ≤ 0.0005)
# ---------------------------------------------------------------------------
# cfg = MeshConfigRand(
#     domain_size=1.0,
#     porosity=0.70,
#     min_hole_size=0.010,
#     max_hole_size=0.09,
#     min_distance_between_holes=0.0005,
#     seed=42,
#     edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
#     hole_size_distribution='right_skew',
#     hole_size_skew_strength=1.5,
#     placement_algorithm='rsa',
# )

# ---------------------------------------------------------------------------
# ALT-B — min_hole=0.015 (larger min → easier mesh), target=0.72 overshoots
# slightly so RSA jams at ~0.714; use mesh_size ≤ 0.0005
# ---------------------------------------------------------------------------
# cfg = MeshConfigRand(
#     domain_size=1.0,
#     porosity=0.72,
#     min_hole_size=0.015,
#     max_hole_size=0.09,
#     min_distance_between_holes=0.0005,
#     seed=42,
#     edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
#     hole_size_distribution='right_skew',
#     hole_size_skew_strength=1.5,
#     placement_algorithm='rsa',
# )

# ---------------------------------------------------------------------------
# Build the FE mesh
# mesh_size=0.001: ~1 element across the d=0.001 gap; Gmsh refines locally
# near the smallest holes (r≈0.005) so actual smallest elements will be finer.
# ---------------------------------------------------------------------------
mesh_path = "C001_Mesh_files/R101.mesh.json"

generator, mesh = create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    export_vtk=False,
    show_plot=True,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.001,
    periodic="both",
)

print(f"\nR101: {len(generator.hole_centers)} holes | "
      f"{mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")

# ---------------------------------------------------------------------------
# Hole distribution figure — saved next to the mesh file.
# generator.hole_centers / hole_radii are already rescaled to [0, L].
# ---------------------------------------------------------------------------
centers   = generator.hole_centers
radii     = generator.hole_radii
diameters = 2.0 * radii
L = cfg.domain_size

fig, (ax_foam, ax_hist) = plt.subplots(1, 2, figsize=(12, 5.5))

# Left panel: hole layout
ax_foam.add_patch(Rectangle(
    (0, 0), L, L,
    linewidth=1.5, edgecolor='black', facecolor='#d9e6f2',
))
for (cx, cy), r in zip(centers, radii):
    ax_foam.add_patch(Circle(
        (cx, cy), r,
        facecolor='white', edgecolor='#333333', linewidth=0.6,
    ))
margin = L * 0.04
ax_foam.set_xlim(-margin, L + margin)
ax_foam.set_ylim(-margin, L + margin)
ax_foam.set_aspect('equal')
ax_foam.set_xlabel('x')
ax_foam.set_ylabel('y')
achieved = float(np.sum(np.pi * radii ** 2) / (L * L))
ax_foam.set_title(
    f"{len(centers)} holes  |  porosity = {achieved:.4f}  (target {cfg.porosity})\n"
    f"min_d = {cfg.min_distance_between_holes}  |  "
    f"diameter ∈ [{cfg.min_hole_size}, {cfg.max_hole_size}]  |  seed = {cfg.seed}"
)

# Right panel: hole diameter histogram
mean_d = float(diameters.mean())
std_d  = float(diameters.std())
ax_hist.hist(diameters, bins='auto', edgecolor='black', color='#7bafd4')
ax_hist.axvline(mean_d, color='red', linestyle='--', linewidth=1.5,
                label=f'mean = {mean_d:.4f}')
ax_hist.axvline(mean_d - std_d, color='orange', linestyle=':', linewidth=1.2,
                label=f'±std = {std_d:.4f}')
ax_hist.axvline(mean_d + std_d, color='orange', linestyle=':', linewidth=1.2)
ax_hist.set_xlabel('Hole diameter')
ax_hist.set_ylabel('Count')
ax_hist.set_title('Hole size distribution  (right_skew  Beta(2,3),  s=1.5)')
ax_hist.legend()

fig.suptitle(
    f'R101 — RSA placement  |  right_skew s=1.5  |  '
    f'porosity={achieved:.4f}  |  d={cfg.min_distance_between_holes}',
    fontsize=12,
)
plt.tight_layout()

out_png = mesh_path.replace('.mesh.json', '_holes.png')
fig.savefig(out_png, dpi=120, bbox_inches='tight')
print(f"Hole distribution saved -> {out_png}")
plt.show()
