"""
Tests for create_PKL_J1 (A001_functions.Reduce_resultsV5).

Uses fully synthetic DATA_B, DATA_C2 and a tiny graph-mesh file so that
no real simulation data or pickle files are needed.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
import tempfile
import shutil

import matplotlib
matplotlib.use("Agg")          # non-interactive backend for CI
import matplotlib.pyplot as plt

from A001_functions.Hex_5 import (
    export_graph_mesh,
    read_graph_mesh,
    GraphMeshData,
    map_undeformed_to_deformed,
)
from A001_functions.fem_stress_interpolation import interpolate_stress


# ── We import create_PKL_J1 without triggering the relative-import
#    inside Reduce_resultsV5.  We monkey-patch the module first.  ──
import importlib, types

# Build a thin shim so the `from .Read_resultsV5 import *` inside
# Reduce_resultsV5 does not blow up when run outside the package.
_fake_pkg = types.ModuleType("A001_functions")
_fake_pkg.__path__ = [os.path.join(os.path.dirname(__file__), "..", "A001_functions")]
sys.modules.setdefault("A001_functions", _fake_pkg)

# Provide a stub Read_resultsV5 so the star-import succeeds
_fake_read = types.ModuleType("A001_functions.Read_resultsV5")
sys.modules.setdefault("A001_functions.Read_resultsV5", _fake_read)

from A001_functions.Reduce_resultsV5 import create_PKL_J1, _order_sub_bar_chain


# ---------------------------------------------------------------------------
# Helpers: synthetic data
# ---------------------------------------------------------------------------

def _make_grid_data_c2(
    nx=3, ny=3, dx=1.0, dy=1.0, n_times=4,
    stretch_x=0.05, stretch_y=0.02,
):
    """Regular nx×ny quad mesh with uniform stretch deformation."""
    xs = np.linspace(0, nx * dx, nx + 1)
    ys = np.linspace(0, ny * dy, ny + 1)
    node_coords = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            node_coords.append([xs[i], ys[j]])
    node_coords = np.array(node_coords)

    elements = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            elements.append([n0 + 1, n0 + 2, n0 + 2 + (nx + 1), n0 + 1 + (nx + 1)])

    nodes_time_list = []
    t_list = list(range(n_times))
    for ti in t_list:
        d = node_coords.copy()
        d[:, 0] *= 1 + stretch_x * ti
        d[:, 1] *= 1 + stretch_y * ti
        nodes_time_list.append(d.tolist())

    return {
        "nodes_time": [
            {str(j + 1): tuple(coord) for j, coord in enumerate(nt)}
            for nt in nodes_time_list
        ],
        "elements": {str(i + 1): v for i, v in enumerate(elements)},
        "t": t_list,
    }


def _make_data_b(DATA_C2, s11_val=100.0, s22_val=50.0, s12_val=10.0):
    """
    Create a DATA_B with uniform stress at all integration points.

    DATA_B['S11'][str(elem+1)][ip*2][ti]  (ip in 0..3, element 1-based key)
    """
    n_elems = len(DATA_C2["elements"])
    n_times = len(DATA_C2["t"])
    DATA_B = {"S11": {}, "S22": {}, "S21": {}, "t": DATA_C2["t"]}

    for eidx in range(n_elems):
        key = str(eidx + 1)
        # 8 integration-point slots (ip*2: 0,2,4,6)
        DATA_B["S11"][key] = {ip * 2: [s11_val] * n_times for ip in range(4)}
        DATA_B["S22"][key] = {ip * 2: [s22_val] * n_times for ip in range(4)}
        DATA_B["S21"][key] = {ip * 2: [s12_val] * n_times for ip in range(4)}

    return DATA_B


def _make_simple_graph(tmp_dir):
    """
    Create a tiny graph-mesh with 5 original nodes and 3 bars,
    each bar subdivided into 2 sub-bars (i.e. 5 + 3 = 8 nodes total,
    6 sub-bars).

    Layout (inside unit square):

        0 ──bar0── 5 ──bar0── 1
        |                      |
       bar2                   bar1
        |                      |
        7                      6
        |                      |
       bar2                   bar1
        |                      |
        3 ────────────────────  2

    Coordinates chosen well inside the 3×3 mesh.
    """
    nodes = np.array([
        [0.5, 2.5],   # 0 - original
        [2.5, 2.5],   # 1 - original
        [2.5, 0.5],   # 2 - original
        [0.5, 0.5],   # 3 - original
        [1.5, 1.5],   # 4 - original (center, used as a junction)
        [1.5, 2.5],   # 5 - subdivision on bar 0
        [2.5, 1.5],   # 6 - subdivision on bar 1
        [0.5, 1.5],   # 7 - subdivision on bar 2
    ])
    node_ids = np.array([1, 1, 1, 1, 1, 2, 2, 2])
    bars = np.array([
        [0, 5], [5, 1],       # bar 0
        [1, 6], [6, 2],       # bar 1
        [0, 7], [7, 3],       # bar 2
    ])
    bar_numbers = np.array([0, 0, 1, 1, 2, 2])

    graph = GraphMeshData(nodes=nodes, node_ids=node_ids,
                          bars=bars, bar_numbers=bar_numbers)
    path = os.path.join(tmp_dir, "test_graph.graph.json")
    export_graph_mesh(graph, path)
    return path, graph


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOrderSubBarChain:
    """Unit tests for the chain-ordering helper."""

    def test_already_ordered(self):
        chain = _order_sub_bar_chain([[0, 1], [1, 2], [2, 3]])
        assert chain == [(0, 1), (1, 2), (2, 3)]

    def test_reversed(self):
        chain = _order_sub_bar_chain([[2, 3], [0, 1], [1, 2]])
        # Either direction is valid; verify it's a continuous chain
        forward = [(0, 1), (1, 2), (2, 3)]
        backward = [(3, 2), (2, 1), (1, 0)]
        assert chain == forward or chain == backward

    def test_single_segment(self):
        chain = _order_sub_bar_chain([[5, 6]])
        assert chain == [(5, 6)]


class TestCreatePKLJ1:
    """Integration test on synthetic data."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.DATA_C2 = _make_grid_data_c2(nx=3, ny=3, n_times=4)
        self.DATA_B = _make_data_b(self.DATA_C2,
                                   s11_val=100.0, s22_val=50.0, s12_val=10.0)
        self.graph_path, self.graph = _make_simple_graph(self.tmp_dir)
        yield
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_returns_dict_with_expected_keys(self):
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        assert set(J1.keys()) == {"t", "nodes", "bars", "bars_connectivity"}

    def test_timesteps_match(self):
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        assert J1["t"] == self.DATA_C2["t"]

    def test_node_count_and_structure(self):
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        assert len(J1["nodes"]) == self.graph.n_nodes
        # Each node dict has one entry per timestep
        for nidx in range(self.graph.n_nodes):
            assert len(J1["nodes"][nidx]) == len(self.DATA_C2["t"])
            for ti in range(len(self.DATA_C2["t"])):
                pos = J1["nodes"][nidx][ti]
                assert len(pos) == 2  # (x, y)

    def test_identity_at_ti0(self):
        """At ti=0 the deformed positions equal the undeformed ones."""
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        for nidx in range(self.graph.n_nodes):
            x0, y0 = self.graph.nodes[nidx]
            xd, yd = J1["nodes"][nidx][0]
            assert abs(xd - x0) < 1e-8, f"node {nidx}: x mismatch"
            assert abs(yd - y0) < 1e-8, f"node {nidx}: y mismatch"

    def test_bars_connectivity(self):
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        # Three original bars (0, 1, 2), each with 2 sub-bars
        assert set(J1["bars_connectivity"].keys()) == {0, 1, 2}
        for bar_id in [0, 1, 2]:
            pairs = J1["bars_connectivity"][bar_id]
            assert len(pairs) == 2
            # Chain continuity: end of pair k == start of pair k+1
            for k in range(len(pairs) - 1):
                assert pairs[k][1] == pairs[k + 1][0]

    def test_bars_normals_are_unit(self):
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        for bar_id in J1["bars"]:
            for ti in J1["bars"][bar_id]:
                for nx_, ny_ in J1["bars"][bar_id][ti]["normals"]:
                    length = np.sqrt(nx_ ** 2 + ny_ ** 2)
                    assert abs(length - 1.0) < 1e-8 or length == 0.0

    def test_bars_stress_count(self):
        """Each bar should have n_sub_bars + 1 stress tuples (one per node)."""
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        for bar_id in J1["bars"]:
            n_sub = len(J1["bars_connectivity"][bar_id])
            for ti in J1["bars"][bar_id]:
                ss = J1["bars"][bar_id][ti]["SS"]
                assert len(ss) == n_sub + 1
                for tup in ss:
                    assert len(tup) == 3  # (S11, S22, S12)

    def test_uniform_stress_values(self):
        """With uniform stress field, all S11 should be ~100."""
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path)
        for bar_id in J1["bars"]:
            for ti in J1["bars"][bar_id]:
                for s11, s22, s12 in J1["bars"][bar_id][ti]["SS"]:
                    assert abs(s11 - 100.0) < 5.0   # allow small interp error
                    assert abs(s22 - 50.0) < 5.0
                    assert abs(s12 - 10.0) < 5.0

    def test_pickle_round_trip(self):
        pkl_path = os.path.join(self.tmp_dir, "test_J1.pkl")
        J1 = create_PKL_J1(self.DATA_B, self.DATA_C2, self.graph_path,
                            output_path=pkl_path)
        assert os.path.isfile(pkl_path)
        import pickle
        with open(pkl_path, "rb") as f:
            J1_loaded = pickle.load(f)
        assert J1_loaded["t"] == J1["t"]
        assert len(J1_loaded["nodes"]) == len(J1["nodes"])


# ---------------------------------------------------------------------------
# Plot: bars with normals at different time steps
# ---------------------------------------------------------------------------

def plot_bars_with_normals(J1: dict, timesteps=None, figsize=(14, 5)):
    """
    Plot the graph-mesh bars in deformed configuration with normal
    arrows at several time-steps.

    Parameters
    ----------
    J1 : dict
        DATA_J1 as produced by create_PKL_J1.
    timesteps : list[int], optional
        Which time indices to plot (default: first, middle, last).
    figsize : tuple
        Figure size.
    """
    all_ti = list(range(len(J1["t"])))
    if timesteps is None:
        timesteps = [all_ti[0], all_ti[len(all_ti) // 2], all_ti[-1]]

    n_plots = len(timesteps)
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)
    if n_plots == 1:
        axes = [axes]

    unique_bars = sorted(J1["bars_connectivity"].keys())
    cmap = plt.cm.get_cmap("tab20", max(len(unique_bars), 1))

    for ax_idx, ti in enumerate(timesteps):
        ax = axes[ax_idx]
        ax.set_title(f"ti = {ti}  (t = {J1['t'][ti]})")

        for bar_id in unique_bars:
            color = cmap(bar_id % cmap.N)
            pairs = J1["bars_connectivity"][bar_id]
            normals = J1["bars"][bar_id][ti]["normals"]

            for seg_idx, (ni, nf) in enumerate(pairs):
                p0 = np.array(J1["nodes"][ni][ti])
                p1 = np.array(J1["nodes"][nf][ti])
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=color, linewidth=1.5)

                # Draw direction arrow at midpoint
                mid = (p0 + p1) / 2
                nx_, ny_ = normals[seg_idx]
                arrow_len = np.linalg.norm(p1 - p0) * 0.25
                ax.annotate(
                    "", xy=mid + np.array([nx_, ny_]) * arrow_len, xytext=mid,
                    arrowprops=dict(arrowstyle="->", color="red", lw=1.0),
                )

        # Draw nodes
        all_nodes_ti = {
            nidx: J1["nodes"][nidx][ti]
            for nidx in range(len(J1["nodes"]))
        }
        xs = [v[0] for v in all_nodes_ti.values()]
        ys = [v[1] for v in all_nodes_ti.values()]
        ax.scatter(xs, ys, c="black", s=15, zorder=5)

        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Stand-alone execution: run tests then show demo plot
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Run pytest first
    exit_code = pytest.main([__file__, "-v"])

    # Build synthetic data for the demo plot
    tmp = tempfile.mkdtemp()
    try:
        DC2 = _make_grid_data_c2(nx=3, ny=3, n_times=6,
                                  stretch_x=0.08, stretch_y=0.04)
        DB = _make_data_b(DC2)
        gpath, _ = _make_simple_graph(tmp)
        J1 = create_PKL_J1(DB, DC2, gpath)

        matplotlib.use("TkAgg")   # switch to interactive for display
        fig = plot_bars_with_normals(J1)
        plt.savefig("test_J1_normals.png", dpi=150, bbox_inches="tight")
        print("Plot saved to test_J1_normals.png")
        plt.show()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
