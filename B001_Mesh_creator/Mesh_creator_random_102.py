"""
Mesh_creator_random_102
=======================
RSA random foam mesh with right-skew hole-size distribution, porosity ≈ 0.60.

Constraints (fixed, same as R101):
  min_distance_between_holes = 0.01
  edge_left/right/bottom/top = 0.01
  hole_size_distribution     = 'right_skew'

Empirical sweep findings (d=0.01, seed=42, target=0.60):

  Wider max_hole is the lever — at d=0.01, the max determines how much area
  large holes can contribute before RSA jams.  The same skew strength (s=2.5)
  used in R101 reaches 0.60 when max_hole is raised from 0.15 → 0.25.

  Winning configuration (min=0.04 kept consistent with R101):
    max=0.25  s=2.5  →  achieved=0.6012  (56 holes)    ← PRIMARY
    max=0.25  s=2.0  →  achieved=0.6025  (38 holes)    ← ALT (fewer holes)
    max=0.25  s=3.0  →  achieved=0.5840  (68 holes)    ← just short of 0.60

  Beta(2,5) (s=2.5) on diameter range [0.04, 0.25]:
    mode ≈ 0.082,  mean ≈ 0.100 — clear right tail to 0.25.

Progression vs R101:
  R101: min=0.04, max=0.15, s=2.5  →  porosity≈0.50  (104 holes)
  R102: min=0.04, max=0.25, s=2.5  →  porosity≈0.60  ( 56 holes)

Output: C001_Mesh_files/R102.mesh.json
        C001_Mesh_files/R102_holes.png
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
# PRIMARY — min=0.04, max=0.25, s=2.5  →  achieved ≈ 0.60  (56 holes)
# ---------------------------------------------------------------------------
cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.60,
    min_hole_size=0.04,                   # diameter — same as R101
    max_hole_size=0.25,                   # wider range to reach 0.60 at d=0.01
    min_distance_between_holes=0.01,      # FIXED — do not change
    seed=42,
    edge_left=0.01,                       # FIXED
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
    hole_size_distribution='right_skew',  # FIXED — Beta(2, 2*skew_strength)
    hole_size_skew_strength=2.5,          # Beta(2,5) — same as R101, clear right skew
    placement_algorithm='rsa',
)

# ---------------------------------------------------------------------------
# ALT — s=2.0 gives 38 holes (fewer, larger); s=3.0 falls short of 0.60
# ---------------------------------------------------------------------------
# cfg = MeshConfigRand(
#     domain_size=1.0, porosity=0.60,
#     min_hole_size=0.04, max_hole_size=0.25,
#     min_distance_between_holes=0.01, seed=42,
#     edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
#     hole_size_distribution='right_skew',
#     hole_size_skew_strength=2.0,
#     placement_algorithm='rsa',
# )

# ---------------------------------------------------------------------------
# Build the FE mesh
# ---------------------------------------------------------------------------
mesh_path = "C001_Mesh_files/R102.mesh.json"

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
    mesh_size=0.004,
    periodic="both",
)

print(f"\nR102: {len(generator.hole_centers)} holes | "
      f"{mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")

# ---------------------------------------------------------------------------
# Hole distribution figure — saved next to the mesh file.
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
ax_hist.set_title(
    f'Hole size distribution  (right_skew  Beta(2,5),  s={cfg.hole_size_skew_strength})'
)
ax_hist.legend()

fig.suptitle(
    f'R102 — RSA  |  right_skew s={cfg.hole_size_skew_strength}  |  '
    f'porosity = {achieved:.4f}  |  d = {cfg.min_distance_between_holes}',
    fontsize=12,
)
plt.tight_layout()

out_png = mesh_path.replace('.mesh.json', '_holes.png')
fig.savefig(out_png, dpi=120, bbox_inches='tight')
print(f"Hole distribution saved -> {out_png}")
plt.show()
