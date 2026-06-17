"""
Examples: random foam meshes with the three hole-placement algorithms
=====================================================================

Demonstrates **mesh creation** and **visualization** for the placement
algorithms selectable through ``MeshConfigRand.placement_algorithm``:

    'rsa'  – Random Sequential Addition (default, fully random).
    'vgp'  – Void-Guided Placement (spatially uniform).
    'ls'   – Jittered triangular-lattice packing (densest / quasi-ordered).

All three now:
  * place strictly non-overlapping holes that respect ``min_distance``,
  * wrap correctly across periodic boundaries (true RVE — holes that leave one
    side re-enter on the opposite side), and
  * print, at placement time, the
        target / achieved / max_theoretical
    porosity, where the target is ``final void area / L^2`` (the final square,
    counting any added edge strips) and ``max_theoretical`` is the densest
    hexagonal packing of equal disks at the maximum radius with a
    ``min_distance`` gap, scaled by the fraction of the square the voids may
    occupy (so it drops with solid edges and rises again when voids may cut
    them).

Run from the repository root so the relative paths resolve, e.g.:

    source /home/franco/miniconda3/etc/profile.d/conda.sh && conda activate Fenv
    python B001_Mesh_creator/Mesh_creator_random_algorithms_demo.py

Outputs (written next to this script / under C001_Mesh_files):
    demo_random_algorithms.png      – side-by-side packing comparison
    R_demo_<algo>.mesh.json (+vtk)  – an actual FE mesh per algorithm
"""

import sys
import os
import io
import contextlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SHOW = True  # True -> also pop the project's interactive preview windows
              #         (foam plot + diameter histogram) via preview_random_mesh

import matplotlib
if not (SHOW and os.environ.get("DISPLAY")):
    matplotlib.use("Agg")          # headless-safe: figures are saved to PNG
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from A001_functions.Hex_5 import (
    MeshConfigRand,
    RandomMeshGenerator,
    create_random_mesh,
    preview_random_mesh,
)

ALGORITHMS = ("rsa", "vgp", "ls")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MESH_DIR = "C001_Mesh_files"


# ---------------------------------------------------------------------------
# A shared base configuration (larger holes -> easy to see by eye)
# ---------------------------------------------------------------------------
def base_config(algorithm: str, **overrides) -> MeshConfigRand:
    params = dict(
        domain_size=1.0,
        porosity=0.55,                 # target = final void area / L^2
        min_hole_size=0.05,            # hole DIAMETERS
        max_hole_size=0.10,
        min_distance_between_holes=0.01,
        seed=42,
        edge_left=0.01, edge_right=0.01, edge_bottom=0.01, edge_top=0.01,
        placement_algorithm=algorithm,
    )
    params.update(overrides)
    return MeshConfigRand(**params)


def _build_generator(cfg, *, allow_cut, periodic_lr, periodic_tb):
    """Build a RandomMeshGenerator from a config, capturing the porosity line
    it prints at construction so we can reuse it as a plot title."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        gen = RandomMeshGenerator(
            domain_size=cfg.domain_size,
            porosity=cfg.porosity,
            min_hole_diameter=cfg.min_hole_size,
            max_hole_diameter=cfg.max_hole_size,
            min_distance=cfg.min_distance_between_holes,
            seed=cfg.seed,
            allow_cut_left=allow_cut, allow_cut_right=allow_cut,
            allow_cut_bottom=allow_cut, allow_cut_top=allow_cut,
            periodic_lr=periodic_lr, periodic_tb=periodic_tb,
            edge_left=cfg.edge_left, edge_right=cfg.edge_right,
            edge_bottom=cfg.edge_bottom, edge_top=cfg.edge_top,
            placement_algorithm=cfg.placement_algorithm,
        )
    report = buf.getvalue().strip().splitlines()
    report = report[-1].strip() if report else ""
    return gen, report


# ---------------------------------------------------------------------------
# Example 1 — side-by-side packing comparison (saved to PNG)
# ---------------------------------------------------------------------------
def example_comparison_png(periodic="both", allow_cut=False):
    """Compare the three algorithms on one figure.

    Reads ``generator.hole_centers`` / ``generator.hole_radii`` directly (these
    already include the periodic mirror disks when holes wrap).

    ``allow_cut`` controls whether holes may cross the domain edges:
      * ``allow_cut=False`` – holes stay fully inside the cell (no edge
        cutting), even when periodic.  No wrapping, so no mirror disks.
      * ``allow_cut=True``  – holes may cross; on a periodic side they wrap to
        the opposite side (a true dense RVE).  Mirror disks are drawn in grey.
    """
    periodic_lr = periodic in ("lr", "both")
    periodic_tb = periodic in ("tb", "both")
    L = 1.0

    fig, axes = plt.subplots(1, len(ALGORITHMS), figsize=(5.0 * len(ALGORITHMS), 5.4))
    print(f"\n=== Example 1: packing comparison (porosity target 0.55, "
          f"periodic={periodic}, allow_cut={allow_cut}) ===")
    for ax, algo in zip(axes, ALGORITHMS):
        cfg = base_config(algo)
        gen, report = _build_generator(
            cfg, allow_cut=allow_cut, periodic_lr=periodic_lr, periodic_tb=periodic_tb)
        print(f"  {report}")

        ax.add_patch(Rectangle((0, 0), L, L, fill=False, ec="black", lw=1.5))
        for (cx, cy), r in zip(gen.hole_centers, gen.hole_radii):
            inside = (0.0 <= cx <= L) and (0.0 <= cy <= L)
            ax.add_patch(Circle(
                (cx, cy), r,
                facecolor="#4a90d9" if inside else "#cfd8e3",   # mirrors = grey
                edgecolor="black", lw=0.5, alpha=0.75))
        ax.set_xlim(-0.12, L + 0.12)
        ax.set_ylim(-0.12, L + 0.12)
        ax.set_aspect("equal")
        ax.axis("off")
        # report looks like "ALGO porosity: target=.. achieved=.. max_theoretical=.."
        ax.set_title(report.replace("porosity:", "\n").strip(), fontsize=9)

    cut_note = ("allow_cut=True — holes wrap across periodic edges (grey = mirrors)"
                if allow_cut else
                "allow_cut=False — holes stay inside the cell (no edge cutting)")
    fig.suptitle(f"Random foam — placement algorithms\n{cut_note}", fontsize=12)
    fig.tight_layout()
    tag = "cut" if allow_cut else "nocut"
    out = os.path.join(SCRIPT_DIR, f"demo_random_algorithms_{periodic}_{tag}.png")
    fig.savefig(out, dpi=90)
    plt.close(fig)
    print(f"  -> saved {out}")


# ---------------------------------------------------------------------------
# Example 2 — how edges and the cut flag change the theoretical maximum
# ---------------------------------------------------------------------------
def example_edges_and_cut():
    """Solid edge strips lower the maximum achievable porosity unless the voids
    are allowed to cut into them.  The construction print shows max_theoretical
    moving accordingly."""
    print("\n=== Example 2: edges + allow_cut effect on max_theoretical ===")
    edge = 0.06
    for label, allow_cut in (("voids may NOT cut edges", False),
                             ("voids MAY cut edges    ", True)):
        cfg = base_config("rsa",
                          edge_left=edge, edge_right=edge,
                          edge_bottom=edge, edge_top=edge)
        _, report = _build_generator(
            cfg, allow_cut=allow_cut, periodic_lr=False, periodic_tb=False)
        print(f"  edge={edge}  {label}:  {report}")


# ---------------------------------------------------------------------------
# Example 3 — build actual FE meshes (one per algorithm)
# ---------------------------------------------------------------------------
def example_build_meshes(periodic="both"):
    """Full pipeline: place holes -> Gmsh boolean cut -> conforming FE mesh,
    written as C001_Mesh_files/R_demo_<algo>.mesh.json."""
    print(f"\n=== Example 3: build FE meshes (periodic={periodic}) ===")
    os.makedirs(MESH_DIR, exist_ok=True)
    for algo in ALGORITHMS:
        cfg = base_config(algo)
        mesh_path = os.path.join(MESH_DIR, f"R_demo_{algo}.mesh.json")
        gen, mesh = create_random_mesh(
            config=cfg,
            filepath=mesh_path,
            export_mesh=True,
            export_vtk=False,
            show_plot=False,
            allow_cut_left=False, allow_cut_right=False,
            allow_cut_bottom=False, allow_cut_top=False,
            element_type="QUAD",
            mesh_size=0.015,
            periodic=periodic,
        )
        print(f"  {algo}: {mesh.n_nodes} nodes, {mesh.n_elements} elements "
              f"-> {mesh_path}")


# ---------------------------------------------------------------------------
# Example 4 — the project's own interactive preview (optional, needs a display)
# ---------------------------------------------------------------------------
def example_interactive_preview(periodic="both"):
    """``preview_random_mesh`` shows the foam plot + a hole-diameter histogram
    and prints the porosity report — no meshing required.  Pops windows, so it
    only runs when SHOW is True and a display is available."""
    print(f"\n=== Example 4: interactive preview (periodic={periodic}) ===")
    for algo in ALGORITHMS:
        preview_random_mesh(
            base_config(algo),
            allow_cut_left=False, allow_cut_right=False,
            allow_cut_bottom=False, allow_cut_top=False,
            periodic=periodic,
            title=f"Random foam preview — {algo.upper()}",
        )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # allow_cut=False: holes confined inside the cell (no edge cutting).
    example_comparison_png(periodic="both", allow_cut=False)
    # allow_cut=True: holes wrap across the periodic seam (true dense RVE).
    example_comparison_png(periodic="both", allow_cut=True)
    example_edges_and_cut()
    example_build_meshes(periodic="both")
    if SHOW and os.environ.get("DISPLAY"):
        example_interactive_preview(periodic="both")
    else:
        print("\n(Set SHOW = True at the top — with a display — to also pop the "
              "interactive preview windows.)")
