"""Create the ST1000 chevron-pair foam used by the SIM_5140 family.

The four existing 1000-series geometries change the packing of circular
cavities, but they do not deliberately introduce a single soft deformation
mechanism.  ST1000 does: successive row pairs are moved toward one another and
shifted in opposite horizontal directions.  This produces a periodic set of
thin diagonal ligaments.  Under vertical compression those ligaments can
rotate and buckle as a collective chevron mode, providing a candidate
snap-through/collapse point.

The design retains the comparison settings used by A1000/R1000/S1000/RH1000:
nominal porosity 0.60, solid edge strips of width 0.01, mixed CPS3/CPS4 mesh,
and periodic node matching on both axes.  The 8 x 8 motif has exactly 64 equal
cavities.  ``mesh_size=0.0028`` resolves the weakest undeformed ligament with
approximately three elements.

Outputs
-------
* C001_Mesh_files/ST1000.mesh.json
* C001_Mesh_files/ST1000.vtk
* C001_Mesh_files/ST1000_I3002.gridhex.json
* C001_Mesh_files/ST1000_preview.png
"""

import os
import sys
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Hex_5 import (
    HexagonalPackingGeometry,
    RandomMeshGenerator,
    create_gridhex_file,
    export_mesh_vtk_from_json,
    write_mesh_json,
)


@dataclass(frozen=True)
class SnapThroughConfig:
    domain_size: float = 1.0
    n_columns: int = 8
    n_rows: int = 8
    porosity: float = 0.60
    pair_closing: float = 0.004
    chevron_shift: float = 0.007
    edge_left: float = 0.01
    edge_right: float = 0.01
    edge_bottom: float = 0.01
    edge_top: float = 0.01


class SnapThroughMeshGenerator(RandomMeshGenerator):
    """Structured equal-radius cavity array using the multi-radius mesher."""

    def __init__(self, config: SnapThroughConfig):
        L = float(config.domain_size)
        nx = int(config.n_columns)
        ny = int(config.n_rows)
        if nx < 2 or ny < 2 or ny % 4:
            raise ValueError("n_columns must be >= 2 and n_rows must be a multiple of 4")
        if not 0.0 < config.porosity < np.pi / 4.0:
            raise ValueError("porosity must be between 0 and pi/4")

        pitch_x = L / nx
        pitch_y = L / ny
        radius = np.sqrt(config.porosity * L * L / (nx * ny * np.pi))

        centers = []
        for row in range(ny):
            pair = row // 2
            member = row % 2
            # Bring the two rows of each pair closer together.  Alternate the
            # diagonal direction every pair to form a balanced /\/\ motif.
            y_sign = 1.0 if member == 0 else -1.0
            pair_direction = 1.0 if pair % 2 == 0 else -1.0
            x_sign = pair_direction * (-1.0 if member == 0 else 1.0)
            y = (row + 0.5) * pitch_y + y_sign * config.pair_closing
            x_shift = x_sign * config.chevron_shift
            for col in range(nx):
                centers.append([(col + 0.5) * pitch_x + x_shift, y])

        self.domain_size = L
        self.porosity = float(config.porosity)
        self.min_hole_radius = radius
        self.max_hole_radius = radius
        self.min_distance = 0.0
        self.seed = None
        self.center_domain = True
        self.allow_cut_left = False
        self.allow_cut_right = False
        self.allow_cut_bottom = False
        self.allow_cut_top = False
        self.edge_left = float(config.edge_left)
        self.edge_right = float(config.edge_right)
        self.edge_bottom = float(config.edge_bottom)
        self.edge_top = float(config.edge_top)
        self.hole_size_distribution = "equal"
        self.hole_size_skew_strength = 0.0
        self.placement_algorithm = "chevron_pair"
        self.hole_centers = np.asarray(centers, dtype=float)
        self.hole_radii = np.full(len(centers), radius, dtype=float)
        self.n_holes_width = nx
        self.horizontal_spacing = pitch_x
        self.geometry = HexagonalPackingGeometry(
            horizontal_spacing=pitch_x,
            vertical_spacing=pitch_y,
            hole_radius=radius,
            porosity=float(config.porosity),
        )


def _save_preview(generator, path):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="#263746", edgecolor="black"))
    for (cx, cy), radius in zip(generator.hole_centers, generator.hole_radii):
        ax.add_patch(plt.Circle((cx, cy), radius, facecolor="white", edgecolor="#9fd3ff", linewidth=0.6))
    # Mark one repeated weak diagonal ligament per row pair.
    for pair in range(4):
        y0 = generator.hole_centers[2 * pair * 8, 1]
        y1 = generator.hole_centers[(2 * pair + 1) * 8, 1]
        x0 = generator.hole_centers[2 * pair * 8 + 3, 0]
        x1 = generator.hole_centers[(2 * pair + 1) * 8 + 3, 0]
        ax.plot([x0, x1], [y0, y1], color="#ff5c5c", linewidth=1.2)
    ax.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xlabel="x", ylabel="y",
           title="ST1000 chevron-pair cavities (red: representative weak ligaments)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def create_st1000(config=SnapThroughConfig(), mesh_size=0.0028):
    generator = SnapThroughMeshGenerator(config)
    padding = {
        "left": config.edge_left,
        "right": config.edge_right,
        "bottom": config.edge_bottom,
        "top": config.edge_top,
    }
    mesh = generator.generate_mesh(
        mesh_size=mesh_size,
        element_type="BOTH",
        edge_padding=padding,
        periodic_lr=True,
        periodic_tb=True,
    )

    # Match the established 1000-series convention: add strips outside the
    # porous unit square and rescale the expanded domain back to [0, 1]^2.
    sx = config.domain_size / (config.domain_size + config.edge_left + config.edge_right)
    sy = config.domain_size / (config.domain_size + config.edge_bottom + config.edge_top)
    mesh.nodes[:, 0] = (mesh.nodes[:, 0] + config.edge_left) * sx
    mesh.nodes[:, 1] = (mesh.nodes[:, 1] + config.edge_bottom) * sy
    generator.hole_centers[:, 0] = (generator.hole_centers[:, 0] + config.edge_left) * sx
    generator.hole_centers[:, 1] = (generator.hole_centers[:, 1] + config.edge_bottom) * sy
    generator.hole_radii *= np.sqrt(sx * sy)
    generator.geometry.horizontal_spacing *= sx
    generator.geometry.vertical_spacing *= sy
    generator.geometry.hole_radius *= np.sqrt(sx * sy)
    mesh.compute_node_labels()

    mesh_path = "C001_Mesh_files/ST1000.mesh.json"
    parameters = {
        "config": {
            "domain_size": config.domain_size,
            "n_columns": config.n_columns,
            "n_rows": config.n_rows,
            "porosity": config.porosity,
            "pair_closing": config.pair_closing,
            "chevron_shift": config.chevron_shift,
            "min_distance_between_holes": 0.0,
            "seed": None,
        },
        "design_intent": "collective chevron-ligament rotation and snap-through",
        "element_type": "BOTH",
        "mesh_size": mesh_size,
        "edge_left": config.edge_left,
        "edge_right": config.edge_right,
        "edge_bottom": config.edge_bottom,
        "edge_top": config.edge_top,
        "periodic": "both",
    }
    write_mesh_json(
        mesh,
        mesh_path,
        mesh_kind="snap_through",
        created_by="Mesh_creator_snap_through_ST1000.create_st1000",
        generator=generator,
        parameters=parameters,
    )
    export_mesh_vtk_from_json(mesh_path)
    create_gridhex_file(
        mesh_path,
        "C001_Mesh_files/ST1000_I3002.gridhex.json",
        hexagon_size=1 / 60,
        grid_remove_edge_nodes=True,
        gridhex_pointy_top=False,
        delete_gridhex_isolated_bars=True,
        show_plot=False,
        overlay_mesh=True,
        boundary_only=True,
    )
    _save_preview(generator, "C001_Mesh_files/ST1000_preview.png")

    minimum_ligament = generator.get_minimum_ligament()
    print(
        f"ST1000: {mesh.n_nodes} nodes | {mesh.n_elements} elements | "
        f"{len(generator.hole_centers)} holes | minimum ligament "
        f"{minimum_ligament:.6f} ({minimum_ligament / mesh_size:.2f} mesh sizes)"
    )
    return generator, mesh


if __name__ == "__main__":
    create_st1000()
