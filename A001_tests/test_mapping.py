"""
Tests for map_undeformed_to_deformed (A001_functions.Hex_5).

Uses a synthetic 2×2 quad mesh so no pickle files are needed.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
import matplotlib.pyplot as plt

from A001_functions.Hex_5 import map_undeformed_to_deformed


# ---------------------------------------------------------------------------
# Helpers: build a small synthetic DATA_C2
# ---------------------------------------------------------------------------

def _make_grid_data_c2(
    nx: int = 2,
    ny: int = 2,
    dx: float = 1.0,
    dy: float = 1.0,
    n_times: int = 5,
    stretch_x: float = 0.1,
    stretch_y: float = 0.05,
) -> dict:
    """
    Build a DATA_C2 dict for a regular nx×ny quad grid.

    Undeformed nodes sit on [0, nx*dx] × [0, ny*dy].
    At time step ti the nodes are displaced by a uniform stretch:
        x_def = x * (1 + stretch_x * ti)
        y_def = y * (1 + stretch_y * ti)

    Elements are 1-based 4-node quads ordered CCW starting bottom-left.
    """
    # --- node grid -----------------------------------------------------------
    xs = np.linspace(0, nx * dx, nx + 1)
    ys = np.linspace(0, ny * dy, ny + 1)
    node_coords_undef = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            node_coords_undef.append([xs[i], ys[j]])
    node_coords_undef = np.array(node_coords_undef)  # (n_nodes, 2)

    # --- elements (1-based) --------------------------------------------------
    elements = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i          # bottom-left  (0-based)
            n1 = n0 + 1                     # bottom-right
            n2 = n1 + (nx + 1)              # top-right
            n3 = n0 + (nx + 1)              # top-left
            elements.append([n0 + 1, n1 + 1, n2 + 1, n3 + 1])  # 1-based

    # --- nodes_time for each ti ----------------------------------------------
    nodes_time_list = []
    t_list = list(range(n_times))
    for ti in t_list:
        sx = 1.0 + stretch_x * ti
        sy = 1.0 + stretch_y * ti
        deformed = node_coords_undef.copy()
        deformed[:, 0] *= sx
        deformed[:, 1] *= sy
        # Store as list of [x, y] lists to mimic real data
        nodes_time_list.append(deformed.tolist())

    return {
        'nodes_time': [
            {str(j + 1): tuple(coord) for j, coord in enumerate(nt)}
            for nt in nodes_time_list
        ],
        'elements': {str(i + 1): v for i, v in enumerate(elements)},
        't': t_list,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNodeMapping:
    """Map a mesh node — result must match exactly."""

    def setup_method(self):
        self.DATA_C2 = _make_grid_data_c2(nx=3, ny=3, n_times=6,
                                           stretch_x=0.2, stretch_y=0.1)

    def test_corner_node_exact(self):
        """Node 0 (bottom-left at origin) must map to (0, 0) at any ti."""
        for ti in range(1, 6):
            res = map_undeformed_to_deformed(0.0, 0.0, ti, self.DATA_C2)
            assert abs(res['x_def']) < 1e-12
            assert abs(res['y_def']) < 1e-12

    def test_interior_node_exact(self):
        """Node at (1, 1) must map to (1*(1+0.2*ti), 1*(1+0.1*ti))."""
        for ti in range(1, 6):
            res = map_undeformed_to_deformed(1.0, 1.0, ti, self.DATA_C2)
            expected_x = 1.0 * (1 + 0.2 * ti)
            expected_y = 1.0 * (1 + 0.1 * ti)
            assert abs(res['x_def'] - expected_x) < 1e-10
            assert abs(res['y_def'] - expected_y) < 1e-10

    def test_top_right_corner(self):
        """Node at (3, 3) maps to (3*(1+0.2*ti), 3*(1+0.1*ti))."""
        ti = 3
        res = map_undeformed_to_deformed(3.0, 3.0, ti, self.DATA_C2)
        assert abs(res['x_def'] - 3.0 * (1 + 0.2 * ti)) < 1e-10
        assert abs(res['y_def'] - 3.0 * (1 + 0.1 * ti)) < 1e-10


class TestInteriorPointMapping:
    """Map a point inside an element — bilinear interpolation."""

    def setup_method(self):
        self.DATA_C2 = _make_grid_data_c2(nx=2, ny=2, n_times=4,
                                           stretch_x=0.1, stretch_y=0.05)

    def test_element_center(self):
        """Center of bottom-left element (0.5, 0.5) under uniform stretch."""
        ti = 2
        res = map_undeformed_to_deformed(0.5, 0.5, ti, self.DATA_C2)
        expected_x = 0.5 * (1 + 0.1 * ti)
        expected_y = 0.5 * (1 + 0.05 * ti)
        assert abs(res['x_def'] - expected_x) < 1e-10
        assert abs(res['y_def'] - expected_y) < 1e-10

    def test_quarter_point(self):
        """Point (0.25, 0.75) under uniform stretch."""
        ti = 3
        res = map_undeformed_to_deformed(0.25, 0.75, ti, self.DATA_C2)
        expected_x = 0.25 * (1 + 0.1 * ti)
        expected_y = 0.75 * (1 + 0.05 * ti)
        assert abs(res['x_def'] - expected_x) < 1e-10
        assert abs(res['y_def'] - expected_y) < 1e-10

    def test_on_edge(self):
        """Point on an element edge (1.0, 0.5)."""
        ti = 1
        res = map_undeformed_to_deformed(1.0, 0.5, ti, self.DATA_C2)
        expected_x = 1.0 * (1 + 0.1 * ti)
        expected_y = 0.5 * (1 + 0.05 * ti)
        assert abs(res['x_def'] - expected_x) < 1e-10
        assert abs(res['y_def'] - expected_y) < 1e-10


class TestKnownElement:
    """Pass element_idx explicitly to skip the search."""

    def setup_method(self):
        self.DATA_C2 = _make_grid_data_c2(nx=2, ny=2, n_times=3,
                                           stretch_x=0.1, stretch_y=0.05)

    def test_explicit_element(self):
        """Passing element_idx gives the same result as auto-search."""
        ti = 2
        x, y = 0.7, 0.3
        auto = map_undeformed_to_deformed(x, y, ti, self.DATA_C2)
        expl = map_undeformed_to_deformed(x, y, ti, self.DATA_C2,
                                          element_idx=auto['element_idx'])
        assert abs(auto['x_def'] - expl['x_def']) < 1e-14
        assert abs(auto['y_def'] - expl['y_def']) < 1e-14


class TestUndeformedIdentity:
    """At ti=0 the mapping must be the identity."""

    def setup_method(self):
        self.DATA_C2 = _make_grid_data_c2(nx=3, ny=3, n_times=5)

    def test_identity(self):
        rng = np.random.default_rng(42)
        for _ in range(20):
            x = rng.uniform(0, 3)
            y = rng.uniform(0, 3)
            res = map_undeformed_to_deformed(x, y, 0, self.DATA_C2)
            assert abs(res['x_def'] - x) < 1e-10, f"x failed for ({x}, {y})"
            assert abs(res['y_def'] - y) < 1e-10, f"y failed for ({x}, {y})"


class TestOutsideDomain:
    """Point clearly outside the mesh should still return the closest match."""

    def setup_method(self):
        self.DATA_C2 = _make_grid_data_c2(nx=2, ny=2, n_times=2)

    def test_outside_raises_graceful(self):
        """Very far outside point — verify it doesn't crash."""
        # We don't require a specific error; the function uses the
        # nearest element as a fallback.  Just make sure it runs.
        res = map_undeformed_to_deformed(100.0, 100.0, 1, self.DATA_C2)
        assert 'x_def' in res


# ---------------------------------------------------------------------------
# Plotting demo (runs when the file is executed directly)
# ---------------------------------------------------------------------------

def plot_mapping_demo():
    """Create a figure illustrating the undeformed → deformed mapping."""
    DATA_C2 = _make_grid_data_c2(
        nx=4, ny=4, dx=1.0, dy=1.0,
        n_times=6, stretch_x=0.15, stretch_y=0.1,
    )
    ti = 4  # time step to illustrate

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- left panel: undeformed mesh + query points -------------------------
    ax = axes[0]
    ax.set_title("Undeformed configuration (t = 0)")
    # Draw elements
    for elem in DATA_C2['elements'].values():
        n1, n2, n3, n4 = elem  # 1-based node IDs
        pts = np.array([
            DATA_C2['nodes_time'][0][str(n1)],
            DATA_C2['nodes_time'][0][str(n2)],
            DATA_C2['nodes_time'][0][str(n3)],
            DATA_C2['nodes_time'][0][str(n4)],
            DATA_C2['nodes_time'][0][str(n1)],
        ])
        ax.plot(pts[:, 0], pts[:, 1], 'b-', linewidth=0.6)
    # Draw nodes
    nt0 = DATA_C2['nodes_time'][0]
    undef_nodes = np.array([nt0[k] for k in sorted(nt0.keys(), key=int)])
    ax.scatter(undef_nodes[:, 0], undef_nodes[:, 1], c='blue', s=20, zorder=5)

    # Query points: a grid of interior points
    rng = np.random.default_rng(7)
    qx = rng.uniform(0.1, 3.9, 25)
    qy = rng.uniform(0.1, 3.9, 25)
    ax.scatter(qx, qy, c='red', s=40, marker='x', zorder=6, label='Query pts')
    ax.set_aspect('equal')
    ax.legend()

    # --- right panel: deformed mesh + mapped points -------------------------
    ax = axes[1]
    ax.set_title(f"Deformed configuration (ti = {ti})")
    for elem in DATA_C2['elements'].values():
        n1, n2, n3, n4 = elem  # 1-based node IDs
        pts = np.array([
            DATA_C2['nodes_time'][ti][str(n1)],
            DATA_C2['nodes_time'][ti][str(n2)],
            DATA_C2['nodes_time'][ti][str(n3)],
            DATA_C2['nodes_time'][ti][str(n4)],
            DATA_C2['nodes_time'][ti][str(n1)],
        ])
        ax.plot(pts[:, 0], pts[:, 1], 'b-', linewidth=0.6)
    nt_ti = DATA_C2['nodes_time'][ti]
    def_nodes = np.array([nt_ti[k] for k in sorted(nt_ti.keys(), key=int)])
    ax.scatter(def_nodes[:, 0], def_nodes[:, 1], c='blue', s=20, zorder=5)

    mapped_x, mapped_y = [], []
    for xi, yi in zip(qx, qy):
        res = map_undeformed_to_deformed(xi, yi, ti, DATA_C2)
        mapped_x.append(res['x_def'])
        mapped_y.append(res['y_def'])
    ax.scatter(mapped_x, mapped_y, c='red', s=40, marker='x', zorder=6,
               label='Mapped pts')
    ax.set_aspect('equal')
    ax.legend()

    # --- arrows connecting undeformed → deformed across panels ---------------
    fig.tight_layout()
    fig.suptitle("Undeformed → Deformed mapping", fontsize=14, y=1.02)
    plt.savefig("mapping_demo.png", dpi=150, bbox_inches='tight')
    plt.show()
    print("Demo plot saved to 'mapping_demo.png'")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
    # Show demo plot
    plot_mapping_demo()
