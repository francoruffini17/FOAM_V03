"""
Mesh_creator_random_R1000
=========================
RSA random foam meshes, porosity ≈ 0.60, ~80 k nodes each.
All share the same geometry recipe as R200 (min=0.01, max=0.25, s=2.5)
but vary by seed or hole-size distribution:

  R1000 — right_skew, seed=42   (baseline, matches R200 geometry at higher density)
  R1040 — right_skew, seed=123  (different hole realisation)
  R1050 — right_skew, seed=7    (different hole realisation)
  R1060 — uniform distribution,  seed=42

Each mesh gets:
  - C001_Mesh_files/<NAME>.mesh.json
  - C001_Mesh_files/<NAME>_holes.png   (foam + size-distribution figure)
  - C001_Mesh_files/<NAME>_I3002.gridhex.json  (hexagon_size=1/60)

mesh_size = 0.0028 targets ~80 000 nodes (R200 used 0.004 → ~39 k nodes).
Adjust if the actual count differs.
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
# Shared geometry recipe
# -----------------------------------------------------------------------
BASE_CFG = dict(
    domain_size=1.0,
    porosity=0.60,
    min_hole_size=0.01,
    max_hole_size=0.25,
    min_distance_between_holes=0.01,
    edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
    hole_size_skew_strength=2.5,
    placement_algorithm='rsa',
)

COMMON_MESH_KWARGS = dict(
    export_mesh=True,
    export_vtk=False,
    show_plot=True,
    show_periodic_matching=True,
    allow_cut_left=False,
    allow_cut_right=False,
    allow_cut_bottom=False,
    allow_cut_top=False,
    element_type="BOTH",
    periodic="both",
    mesh_size=0.0028,
)

# -----------------------------------------------------------------------
# Mesh specifications  (name, seed, hole_size_distribution)
# -----------------------------------------------------------------------
MESHES = [
    dict(name="R1000", seed=42,  hole_size_distribution='right_skew'),
    dict(name="R1040", seed=123, hole_size_distribution='right_skew'),
    dict(name="R1050", seed=7,   hole_size_distribution='right_skew'),
    dict(name="R1060", seed=42,  hole_size_distribution='uniform'),
]


# -----------------------------------------------------------------------
# Generate
# -----------------------------------------------------------------------
for spec in MESHES:
    name      = spec["name"]
    mesh_path = f"C001_Mesh_files/{name}.mesh.json"

    print(f"\n{'='*60}")
    print(f"Generating {name}  "
          f"(seed={spec['seed']}, dist={spec['hole_size_distribution']})")
    print(f"{'='*60}")

    cfg = MeshConfigRand(
        **BASE_CFG,
        seed=spec["seed"],
        hole_size_distribution=spec["hole_size_distribution"],
    )

    generator, mesh = create_random_mesh(
        config=cfg,
        filepath=mesh_path,
        **COMMON_MESH_KWARGS,
    )

    print(f"{name}: {len(generator.hole_centers)} holes | "
          f"{mesh.n_nodes} nodes | {mesh.n_elements} elements -> {mesh_path}")

    # -- hole-distribution figure -----------------------------------------
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
    dist_label = (f'right_skew  Beta(2,5),  s={cfg.hole_size_skew_strength}'
                  if spec["hole_size_distribution"] == 'right_skew'
                  else spec["hole_size_distribution"])
    ax_hist.set_title(
        f'Hole size distribution  ({dist_label})\nskewness = {skew_d:.3f}'
    )
    ax_hist.legend()

    fig.suptitle(
        f'{name} — RSA  |  {spec["hole_size_distribution"]}  |  seed={cfg.seed}  |  '
        f'porosity = {achieved:.4f}  |  d = {cfg.min_distance_between_holes}',
        fontsize=12,
    )
    plt.tight_layout()

    out_png = mesh_path.replace('.mesh.json', '_holes.png')
    fig.savefig(out_png, dpi=120, bbox_inches='tight')
    print(f"Hole distribution saved -> {out_png}")
    plt.close(fig)

    # -- gridhex overlay --------------------------------------------------
    gridhex_path = f"C001_Mesh_files/{name}_I3002.gridhex.json"
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

print("\nDone — R1000, R1040, R1050, R1060 created.")
