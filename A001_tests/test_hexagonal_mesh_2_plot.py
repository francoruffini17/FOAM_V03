"""
Visual test – generates and saves plots of hexagonal_mesh_2 with partial holes.

Run directly:  python A001_tests/test_hexagonal_mesh_2_plot.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from A001_functions.Hex_5 import (
    MeshConfig,
    HexagonalMeshGenerator,
    HexagonalMeshGenerator2,
    create_hexagonal_mesh_2,
)

OUT = os.path.join(os.path.dirname(__file__), '..', 'Temp', 'hex2_plots')
os.makedirs(OUT, exist_ok=True)


def plot_comparison():
    """Side-by-side: Generator1 (fully interior) vs Generator2 (partial holes)."""
    cfg = dict(domain_size=1.0, n_holes_width=5, porosity=0.3)

    gen1 = HexagonalMeshGenerator(**cfg)
    mesh1 = gen1.generate_mesh(elements_around_hole=24)
    mesh1.compute_node_labels()

    gen2 = HexagonalMeshGenerator2(**cfg)
    mesh2 = gen2.generate_mesh(elements_around_hole=24)
    mesh2.compute_node_labels()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # --- left: original ---
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle

    polys1 = [mesh1.nodes[e] for e in mesh1.elements]
    ax1.add_collection(PolyCollection(polys1, facecolor='lightblue',
                                       edgecolor='blue', linewidth=0.4, alpha=0.7))
    for c in gen1.hole_centers:
        ax1.add_patch(Circle(c, gen1.geometry.hole_radius, fill=True,
                             facecolor='white', edgecolor='darkred', lw=1.2, zorder=4))
    ax1.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec='black', lw=2, zorder=3))
    ax1.set_xlim(-0.05, 1.05); ax1.set_ylim(-0.05, 1.05); ax1.set_aspect('equal')
    ax1.set_title(f'create_hexagonal_mesh (original)\n'
                  f'{mesh1.n_nodes} nodes, {mesh1.n_elements} elems, '
                  f'{len(gen1.hole_centers)} holes')

    # --- right: partial holes ---
    polys2 = [mesh2.nodes[e] for e in mesh2.elements]
    ax2.add_collection(PolyCollection(polys2, facecolor='lightyellow',
                                       edgecolor='green', linewidth=0.4, alpha=0.7))
    for c in gen2.hole_centers:
        ax2.add_patch(Circle(c, gen2.geometry.hole_radius, fill=True,
                             facecolor='white', edgecolor='darkred', lw=1.2, zorder=4))
    ax2.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec='black', lw=2, zorder=3))
    ax2.set_xlim(-0.05, 1.05); ax2.set_ylim(-0.05, 1.05); ax2.set_aspect('equal')
    ax2.set_title(f'create_hexagonal_mesh_2 (partial holes)\n'
                  f'{mesh2.n_nodes} nodes, {mesh2.n_elements} elems, '
                  f'{len(gen2.hole_centers)} holes')

    fig.suptitle('Hexagonal mesh comparison', fontsize=14, y=1.01)
    fig.tight_layout()
    path = os.path.join(OUT, 'comparison.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {path}')


def plot_node_labels():
    """Node labels coloured by boundary category."""
    cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
    gen, mesh = create_hexagonal_mesh_2(
        config=cfg,
        filepath=os.path.join(OUT, 'labels_mesh'),
        export_mesh=False, show_plot=False,
    )
    fig = gen.plot_node_labels(mesh, show_label=True)
    path = os.path.join(OUT, 'node_labels.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {path}')


def plot_multiple_configs():
    """Grid of meshes with different n_holes_width / porosity combinations."""
    configs = [
        MeshConfig(domain_size=1.0, n_holes_width=3, porosity=0.2),
        MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3),
        MeshConfig(domain_size=1.0, n_holes_width=8, porosity=0.4),
        MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.5),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle

    for ax, cfg in zip(axes.flat, configs):
        gen, mesh = create_hexagonal_mesh_2(
            config=cfg,
            filepath=os.path.join(OUT, f'grid_{cfg.n_holes_width}_{int(cfg.porosity*100)}'),
            export_mesh=False, show_plot=False,
        )
        polys = [mesh.nodes[e] for e in mesh.elements]
        ax.add_collection(PolyCollection(polys, facecolor='lightblue',
                                          edgecolor='steelblue', linewidth=0.3, alpha=0.7))
        for c in gen.hole_centers:
            ax.add_patch(Circle(c, gen.geometry.hole_radius, fill=True,
                                facecolor='white', edgecolor='darkred', lw=0.8, zorder=4))
        ax.add_patch(plt.Rectangle((0, 0), cfg.domain_size, cfg.domain_size,
                                    fill=False, ec='black', lw=2, zorder=3))
        ax.set_xlim(-0.05, cfg.domain_size * 1.05)
        ax.set_ylim(-0.05, cfg.domain_size * 1.05)
        ax.set_aspect('equal')
        ax.set_title(f'n_holes={cfg.n_holes_width}, porosity={cfg.porosity}\n'
                     f'{mesh.n_nodes} nodes, {mesh.n_elements} elems, '
                     f'{len(gen.hole_centers)} holes', fontsize=10)

    fig.suptitle('create_hexagonal_mesh_2 – different configurations', fontsize=13)
    fig.tight_layout()
    path = os.path.join(OUT, 'multiple_configs.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {path}')


if __name__ == '__main__':
    plot_comparison()
    plot_node_labels()
    plot_multiple_configs()
    print(f'\nAll plots saved to {os.path.abspath(OUT)}')
