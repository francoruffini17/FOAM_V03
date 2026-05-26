"""
Tests for create_hexagonal_mesh_2 — hexagonal mesh with partial (cut) holes.
"""
import sys
import os
import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for CI
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Hex_5 import (
    MeshConfig,
    HexagonalMeshGenerator2,
    create_hexagonal_mesh_2,
    create_graph_file,
    export_delaunay_vtk_from_json,
    export_voronoi_vtk_from_json,
)


# ── helpers ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'Temp', 'test_hex2')


@pytest.fixture(autouse=True)
def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── tests ────────────────────────────────────────────────────────────────────

class TestHexagonalMeshGenerator2:
    """Basic sanity checks for the partial-hole generator."""

    def test_more_holes_than_generator1(self):
        """Generator2 should include more hole centres than Generator1."""
        from A001_functions.Hex_5 import HexagonalMeshGenerator

        cfg = dict(domain_size=1.0, n_holes_width=5, porosity=0.3)
        gen1 = HexagonalMeshGenerator(**cfg)
        gen2 = HexagonalMeshGenerator2(**cfg)

        assert len(gen2.hole_centers) >= len(gen1.hole_centers), (
            f"Generator2 ({len(gen2.hole_centers)}) should have ≥ holes "
            f"than Generator1 ({len(gen1.hole_centers)})"
        )

    def test_partial_hole_centers_extend_beyond_domain(self):
        """At least some hole-centre circles should cross the domain boundary."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        gen = HexagonalMeshGenerator2(
            domain_size=cfg.domain_size,
            n_holes_width=cfg.n_holes_width,
            porosity=cfg.porosity,
        )
        r = gen.geometry.hole_radius
        L = gen.domain_size

        has_partial = False
        for cx, cy in gen.hole_centers:
            # Circle extends beyond at least one edge
            if cx - r < 0 or cx + r > L or cy - r < 0 or cy + r > L:
                has_partial = True
                break

        assert has_partial, "Expected at least one partial (edge-cut) hole"


class TestCreateHexagonalMesh2:
    """Integration tests for the full create_hexagonal_mesh_2 pipeline."""

    def test_basic_mesh_creation(self):
        """Mesh is generated and has nodes + elements."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_basic')

        gen, mesh = create_hexagonal_mesh_2(
            config=cfg,
            filepath=filepath,
            export_mesh=True,
            show_plot=False,
        )

        assert mesh.n_nodes > 0, "Mesh should have nodes"
        assert mesh.n_elements > 0, "Mesh should have elements"
        assert os.path.isfile(filepath + ".vtk"), "VTK file should exist"
        assert os.path.isfile(filepath + ".mesh.json"), "mesh JSON file should exist"

    def test_all_nodes_inside_domain(self):
        """Every mesh node must lie inside (or on boundary of) the domain."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_bounds')

        _, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        L = cfg.domain_size
        tol = L * 1e-4
        assert np.all(mesh.nodes[:, 0] >= -tol), "Nodes should not be left of x=0"
        assert np.all(mesh.nodes[:, 0] <= L + tol), "Nodes should not be right of x=L"
        assert np.all(mesh.nodes[:, 1] >= -tol), "Nodes should not be below y=0"
        assert np.all(mesh.nodes[:, 1] <= L + tol), "Nodes should not be above y=L"

    def test_quad_elements_have_four_nodes(self):
        """Each element should reference exactly 4 nodes."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_quads')

        _, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        assert mesh.elements.shape[1] == 4

    def test_boundary_nodes_populated(self):
        """Boundary node sets should be non-empty for all 4 edges."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_bnd')

        _, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        for edge in ('bottom', 'right', 'top', 'left'):
            assert len(mesh.boundary_nodes[edge]) > 0, (
                f"Boundary '{edge}' should have nodes"
            )

    def test_node_labels_computed(self):
        """Node labels should be computed and have the expected format."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_labels')

        _, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        assert mesh.node_labels is not None
        assert len(mesh.node_labels) == mesh.n_nodes
        # Labels should start with '1'
        for lbl in mesh.node_labels:
            assert lbl.startswith('1'), f"Label '{lbl}' does not start with '1'"

    def test_export_all_formats(self):
        """All export options should produce files without errors."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_all')

        gen, mesh = create_hexagonal_mesh_2(
            config=cfg,
            filepath=filepath,
            export_mesh=True,
            show_plot=False,
        )
        mesh_path = filepath + ".mesh.json"
        export_voronoi_vtk_from_json(mesh_path)
        export_delaunay_vtk_from_json(mesh_path)
        create_graph_file(
            mesh_path,
            filepath + "_graph.graph.json",
            graph_characteristic_distance=0.05,
        )

        assert os.path.isfile(filepath + ".vtk")
        assert os.path.isfile(mesh_path)
        assert os.path.isfile(filepath + "_voronoi.vtk")
        assert os.path.isfile(filepath + "_delaunay.vtk")
        assert os.path.isfile(filepath + "_graph.graph.json")

    def test_plot_mesh(self):
        """Plotting should not raise and should produce a figure."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_plot')

        gen, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        fig = gen.plot_mesh(mesh)
        assert fig is not None
        fig.savefig(os.path.join(OUTPUT_DIR, 'mesh_plot.png'), dpi=100)
        plt.close(fig)

        fig2 = gen.plot_node_labels(mesh)
        assert fig2 is not None
        fig2.savefig(os.path.join(OUTPUT_DIR, 'mesh_labels.png'), dpi=100)
        plt.close(fig2)

    def test_positive_jacobians(self):
        """All element Jacobians should be positive (no inverted elements)."""
        cfg = MeshConfig(domain_size=1.0, n_holes_width=5, porosity=0.3)
        filepath = os.path.join(OUTPUT_DIR, 'mesh_jac')

        gen, mesh = create_hexagonal_mesh_2(
            config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
        )

        metrics = gen.get_mesh_quality_metrics(mesh)
        assert metrics['negative_jacobians'] == 0, (
            f"Found {metrics['negative_jacobians']} elements with negative Jacobians"
        )

    def test_different_configs(self):
        """Mesh generation should succeed for different n_holes / porosity combos."""
        configs = [
            MeshConfig(domain_size=1.0, n_holes_width=3, porosity=0.2),
            MeshConfig(domain_size=1.0, n_holes_width=8, porosity=0.4),
            MeshConfig(domain_size=2.0, n_holes_width=6, porosity=0.5),
        ]
        for i, cfg in enumerate(configs):
            filepath = os.path.join(OUTPUT_DIR, f'mesh_cfg_{i}')
            gen, mesh = create_hexagonal_mesh_2(
                config=cfg, filepath=filepath, export_mesh=False, show_plot=False,
            )
            assert mesh.n_nodes > 0
            assert mesh.n_elements > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
