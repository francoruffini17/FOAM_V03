"""
Mesh_creator_random_R200
========================
RSA random foam mesh with right-skew hole-size distribution, porosity ≈ 0.60.
Same geometry as R103 (min=0.01, max=0.25, s=2.5, seed=42).

This script:
  1. Creates  C001_Mesh_files/R200.mesh.json
  2. Creates  C001_Mesh_files/R200_I3002.gridhex.json  (hex overlay for I-series reduction)

Abaqus input deck: see D001_Input_files_creator/SIM_700_inp_creator_random.py
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
    create_gridhex_file,
)


# -----------------------------------------------------------------------
# 1.  FE mesh
# -----------------------------------------------------------------------
cfg = MeshConfigRand(
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

mesh_path = "C001_Mesh_files/R200.mesh.json"

generator, mesh = create_random_mesh(
    config=cfg,
    filepath=mesh_path,
    export_mesh=True,
    export_vtk=False,
    show_plot=True,
    show_periodic_matching=True,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    mesh_size=0.004,
    periodic="both",
)

print(f"\nR200: {len(generator.hole_centers)} holes | "
      f"{mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")


# -----------------------------------------------------------------------
# 2.  Hole-distribution figure
# -----------------------------------------------------------------------
centers   = generator.hole_centers
radii     = generator.hole_radii
diameters = 2.0 * radii
L = cfg.domain_size

fig, (ax_foam, ax_hist) = plt.subplots(1, 2, figsize=(12, 5.5))

ax_foam.add_patch(Rectangle((0, 0), L, L,
                             linewidth=1.5, edgecolor='black', facecolor='#d9e6f2'))
for (cx, cy), r in zip(centers, radii):
    ax_foam.add_patch(Circle((cx, cy), r,
                              facecolor='white', edgecolor='#333333', linewidth=0.6))
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
    f'Hole size distribution  (right_skew  Beta(2,5),  s={cfg.hole_size_skew_strength})'
    f'\nskewness = {skew_d:.3f}'
)
ax_hist.legend()

fig.suptitle(
    f'R200 — RSA  |  right_skew s={cfg.hole_size_skew_strength}  |  '
    f'porosity = {achieved:.4f}  |  d = {cfg.min_distance_between_holes}',
    fontsize=12,
)
plt.tight_layout()

out_png = mesh_path.replace('.mesh.json', '_holes.png')
fig.savefig(out_png, dpi=120, bbox_inches='tight')
print(f"Hole distribution saved -> {out_png}")
plt.close(fig)


# -----------------------------------------------------------------------
# 3.  Gridhex overlay for I-series reduction (I3002)
# -----------------------------------------------------------------------
gridhex_path = "C001_Mesh_files/R200_I3002.gridhex.json"

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
