"""
Mesh_creator_random_104
=======================
RSA random foam mesh with right-skew hole-size distribution, porosity ≈ 0.60.
Variant of R103 with more, smaller holes.

Constraints (fixed, same as R101/R102/R103):
  min_distance_between_holes = 0.01
  edge_left/right/bottom/top = 0.01
  hole_size_distribution     = 'right_skew'

Parameter sweep results (d=0.01, seed=42, target=0.60):

  Winning configuration:
    min=0.01  max=0.20  s=2.0  →  achieved=0.6000  (100 holes)  skew=+0.35  ← PRIMARY
                                   Beta(2,4): mode≈0.055, mean≈0.073  (placed mean≈0.082)

  Explored but not used:
    min=0.01  max=0.20  s=2.5  →  achieved=0.5587  (139 holes)  skew=+0.48  ← doesn't reach 60 %
    min=0.02  max=0.25  s=3.0  seed=88  →  achieved=0.5606  (104 holes)  skew=+0.83  ← doesn't reach 60 %
    min=0.02  max=0.25  s=3.0  seed=777 →  achieved=0.5948  ( 94 holes)  skew=+0.45  ← close but <60 %

  Tradeoff vs R103:
    R103: min=0.01, max=0.25, s=2.5  →  81 holes, mean_d=0.092, skew=+0.47, por=0.60
    R104: min=0.01, max=0.20, s=2.0  → 100 holes, mean_d=0.082, skew=+0.35, por=0.60
    More holes and smaller mean diameter at the cost of slightly reduced skew.

Progression:
  R101: min=0.04, max=0.15, s=2.5  →  porosity≈0.50  (104 holes)  [uniform-ish]
  R102: min=0.04, max=0.25, s=2.5  →  porosity≈0.60  ( 56 holes)  [large holes]
  R103: min=0.01, max=0.25, s=2.5  →  porosity≈0.60  ( 81 holes)  [right-skewed]
  R104: min=0.01, max=0.20, s=2.0  →  porosity≈0.60  (100 holes)  [more, smaller, right-skewed]

Output: C001_Mesh_files/R104.mesh.json
        C001_Mesh_files/R104_holes.png
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from scipy.stats import skew as _skew

from A001_functions.Hex_5 import (
    MeshConfigRand,
    create_random_mesh,
)

# ---------------------------------------------------------------------------
# PRIMARY — min=0.01, max=0.20, s=2.0  →  achieved=0.60  (100 holes, skew +0.35)
# ---------------------------------------------------------------------------
cfg = MeshConfigRand(
    domain_size=1.0,
    porosity=0.60,
    min_hole_size=0.01,                    # same as R103
    max_hole_size=0.20,                    # narrower than R103 (was 0.25) → more holes
    min_distance_between_holes=0.01,       # FIXED — do not change
    seed=42,
    edge_left=0.01,                        # FIXED
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
    hole_size_distribution='right_skew',   # FIXED — Beta(2, 2*skew_strength)
    hole_size_skew_strength=2.0,           # Beta(2,4) — right-skewed, ~100 holes
    placement_algorithm='rsa',
)

# ---------------------------------------------------------------------------
# Build the FE mesh
# ---------------------------------------------------------------------------
mesh_path = "C001_Mesh_files/R104.mesh.json"

generator, mesh = create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    export_vtk=False,
    show_plot=False,
    show_periodic_matching=False,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.004,
    periodic="both",
)

print(f"\nR104: {len(generator.hole_centers)} holes | "
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
skew_d = float(_skew(diameters))
ax_hist.hist(diameters, bins='auto', edgecolor='black', color='#7bafd4')
ax_hist.axvline(mean_d, color='red', linestyle='--', linewidth=1.5,
                label=f'mean = {mean_d:.4f}')
ax_hist.axvline(mean_d - std_d, color='orange', linestyle=':', linewidth=1.2,
                label=f'±std = {std_d:.4f}')
ax_hist.axvline(mean_d + std_d, color='orange', linestyle=':', linewidth=1.2)
ax_hist.set_xlabel('Hole diameter')
ax_hist.set_ylabel('Count')
ax_hist.set_title(
    f'Hole size distribution  (right_skew  Beta(2,4),  s={cfg.hole_size_skew_strength})'
    f'\nskewness = {skew_d:.3f}'
)
ax_hist.legend()

fig.suptitle(
    f'R104 — RSA  |  right_skew s={cfg.hole_size_skew_strength}  |  '
    f'porosity = {achieved:.4f}  |  d = {cfg.min_distance_between_holes}',
    fontsize=12,
)
plt.tight_layout()

out_png = mesh_path.replace('.mesh.json', '_holes.png')
fig.savefig(out_png, dpi=120, bbox_inches='tight')
print(f"Hole distribution saved -> {out_png}")
plt.close(fig)
