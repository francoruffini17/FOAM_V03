"""
Tests for create_PKL_J2.

Builds a synthetic DATA_J1, calls create_PKL_J2, and verifies the
tension / compression classification logic with NetworkX graphs.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pickle
import tempfile
import numpy as np
import networkx as nx

# --- handle the relative import inside Reduce_resultsV5 ---------------------
import types
_fake_pkg = types.ModuleType("A001_functions")
_fake_pkg.__path__ = [os.path.join(os.path.dirname(__file__), "..", "A001_functions")]
sys.modules.setdefault("A001_functions", _fake_pkg)
_fake_read = types.ModuleType("A001_functions.Read_resultsV5")
sys.modules.setdefault("A001_functions.Read_resultsV5", _fake_read)
# -----------------------------------------------------------------------------

from A001_functions.Reduce_resultsV5 import create_PKL_J2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_bar_ids_from_graph(G):
    """Return set of bar_ids present as edges in the graph."""
    return {d['bar_id'] for _, _, d in G.edges(data=True)}


def _get_axial_force(G, bar_id):
    """Return the axial_force stored on the edge with the given bar_id."""
    for _, _, d in G.edges(data=True):
        if d['bar_id'] == bar_id:
            return d['axial_force']
    raise KeyError(f"bar_id {bar_id} not found in graph")


def _make_j1(
    n_timesteps: int = 3,
    stress_values: dict = None,
):
    """
    Create a tiny DATA_J1 with 2 bars.

    Bar 0 — 3 segments (nodes 0-1-2-3), direction along +x → n = (1, 0)
        Original nodes: 0 and 3
    Bar 1 — 2 segments (nodes 4-5-6),   direction along +y → n = (0, 1)
        Original nodes: 4 and 6

    Defaults give:
        bar 0 → S11=10, S22=2, S12=0  →  axial along x = S11 = 10  (tension)
        bar 1 → S11=1, S22=-5, S12=0  →  axial along y = S22 = -5  (compression)
    """
    if stress_values is None:
        stress_values = {
            0: (10.0, 2.0, 0.0),
            1: (1.0, -5.0, 0.0),
        }

    t = list(range(n_timesteps))

    base_nodes_bar0 = [(i * 0.1, 0.0) for i in range(4)]
    base_nodes_bar1 = [(0.5, i * 0.1) for i in range(3)]
    base_nodes = base_nodes_bar0 + base_nodes_bar1  # 7 nodes

    nodes = []
    for pos in base_nodes:
        node_dict = {}
        for ti in range(n_timesteps):
            node_dict[ti] = (pos[0] + ti * 0.001, pos[1] + ti * 0.001)
        nodes.append(node_dict)

    bars_connectivity = {
        0: [(0, 1), (1, 2), (2, 3)],   # 3 segments, original nodes: 0, 3
        1: [(4, 5), (5, 6)],            # 2 segments, original nodes: 4, 6
    }

    bars = {0: {}, 1: {}}
    for ti in range(n_timesteps):
        bars[0][ti] = {
            'normals': [(1.0, 0.0)] * 3,
            'SS': [stress_values[0]] * 4,
        }
        bars[1][ti] = {
            'normals': [(0.0, 1.0)] * 2,
            'SS': [stress_values[1]] * 3,
        }

    return {
        't': t,
        'nodes': nodes,
        'bars': bars,
        'bars_connectivity': bars_connectivity,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreatePKLJ2:

    def test_returns_dict_with_expected_keys(self):
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        assert isinstance(J2, dict)
        for key in ('t', 'tension', 'compression'):
            assert key in J2, f"Missing key '{key}'"

    def test_timesteps_match(self):
        J1 = _make_j1(n_timesteps=5)
        J2 = create_PKL_J2(J1)
        assert J2['t'] == J1['t']

    def test_graphs_are_networkx(self):
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        for ti in range(len(J1['t'])):
            assert isinstance(J2['tension'][ti], nx.Graph)
            assert isinstance(J2['compression'][ti], nx.Graph)

    def test_original_nodes_in_both_graphs(self):
        """Both graphs must contain all original nodes (0, 3, 4, 6)."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        expected_nodes = {0, 3, 4, 6}
        for ti in range(len(J1['t'])):
            assert set(J2['tension'][ti].nodes) == expected_nodes
            assert set(J2['compression'][ti].nodes) == expected_nodes

    def test_node_pos_attribute(self):
        """Each node must have a 'pos' attribute matching the deformed position."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        for ti in range(len(J1['t'])):
            G = J2['tension'][ti]
            for nidx in G.nodes:
                assert G.nodes[nidx]['pos'] == J1['nodes'][nidx][ti]

    def test_tension_compression_classification(self):
        """Bar 0 → tension edge, Bar 1 → compression edge."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        for ti in range(len(J1['t'])):
            t_bars = _get_bar_ids_from_graph(J2['tension'][ti])
            c_bars = _get_bar_ids_from_graph(J2['compression'][ti])
            assert 0 in t_bars, f"Bar 0 should be in tension at ti={ti}"
            assert 1 in c_bars, f"Bar 1 should be in compression at ti={ti}"
            assert 0 not in c_bars
            assert 1 not in t_bars

    def test_edges_connect_original_nodes(self):
        """Bar 0 edge: (0,3). Bar 1 edge: (4,6)."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        for ti in range(len(J1['t'])):
            G_t = J2['tension'][ti]
            G_c = J2['compression'][ti]
            assert G_t.has_edge(0, 3)
            assert G_c.has_edge(4, 6)

    def test_axial_force_on_edges(self):
        """Check the axial_force attribute stored on each edge."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        for ti in range(len(J1['t'])):
            af_bar0 = _get_axial_force(J2['tension'][ti], 0)
            af_bar1 = _get_axial_force(J2['compression'][ti], 1)
            assert abs(af_bar0 - 10.0) < 1e-12
            assert abs(af_bar1 - (-5.0)) < 1e-12

    def test_shear_contribution(self):
        """Non-zero S12 with diagonal direction."""
        n_ti = 2
        angle = np.pi / 4
        nvx, nvy = np.cos(angle), np.sin(angle)
        n_vec = np.array([nvx, nvy])

        s11, s22, s12 = 4.0, 2.0, 3.0
        S = np.array([[s11, s12], [s12, s22]])
        expected_af = float(n_vec @ S @ n_vec)

        J1 = {
            't': list(range(n_ti)),
            'nodes': [
                {ti: (0.0, 0.0) for ti in range(n_ti)},
                {ti: (1.0, 1.0) for ti in range(n_ti)},
            ],
            'bars_connectivity': {0: [(0, 1)]},
            'bars': {
                0: {
                    ti: {
                        'normals': [(nvx, nvy)],
                        'SS': [(s11, s22, s12), (s11, s22, s12)],
                    }
                    for ti in range(n_ti)
                }
            },
        }
        J2 = create_PKL_J2(J1)
        for ti in range(n_ti):
            af = _get_axial_force(J2['tension'][ti], 0)
            assert abs(af - expected_af) < 1e-12

    def test_middle_segment_odd(self):
        """Bar with 3 segments: middle is segment index 1."""
        J1 = {
            't': [0],
            'nodes': [{0: (i * 0.1, 0.0)} for i in range(4)],
            'bars_connectivity': {0: [(0, 1), (1, 2), (2, 3)]},
            'bars': {
                0: {
                    0: {
                        'normals': [(1.0, 0.0)] * 3,
                        'SS': [
                            (0.0, 0.0, 0.0),
                            (100.0, 0.0, 0.0),
                            (100.0, 0.0, 0.0),
                            (0.0, 0.0, 0.0),
                        ],
                    }
                }
            },
        }
        J2 = create_PKL_J2(J1)
        af = _get_axial_force(J2['tension'][0], 0)
        assert abs(af - 100.0) < 1e-12

    def test_middle_segments_even(self):
        """Bar with 2 segments: average of segments 0 and 1."""
        J1 = {
            't': [0],
            'nodes': [{0: (i * 0.1, 0.0)} for i in range(3)],
            'bars_connectivity': {0: [(0, 1), (1, 2)]},
            'bars': {
                0: {
                    0: {
                        'normals': [(1.0, 0.0)] * 2,
                        'SS': [
                            (10.0, 0.0, 0.0),
                            (20.0, 0.0, 0.0),
                            (30.0, 0.0, 0.0),
                        ],
                    }
                }
            },
        }
        J2 = create_PKL_J2(J1)
        af = _get_axial_force(J2['tension'][0], 0)
        # Seg 0 mid-S11 = 15, Seg 1 mid-S11 = 25, avg = 20
        assert abs(af - 20.0) < 1e-12

    def test_zero_axial_goes_to_compression(self):
        """When axial force == 0, the bar goes to compression."""
        J1 = {
            't': [0],
            'nodes': [{0: (i * 0.1, 0.0)} for i in range(2)],
            'bars_connectivity': {0: [(0, 1)]},
            'bars': {
                0: {
                    0: {
                        'normals': [(1.0, 0.0)],
                        'SS': [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
                    }
                }
            },
        }
        J2 = create_PKL_J2(J1)
        assert 0 in _get_bar_ids_from_graph(J2['compression'][0])
        assert 0 not in _get_bar_ids_from_graph(J2['tension'][0])

    def test_every_bar_classified(self):
        """Every bar appears as an edge in exactly one graph per ti."""
        J1 = _make_j1(n_timesteps=4)
        J2 = create_PKL_J2(J1)
        all_bars = set(J1['bars_connectivity'].keys())
        for ti in range(len(J1['t'])):
            t_bars = _get_bar_ids_from_graph(J2['tension'][ti])
            c_bars = _get_bar_ids_from_graph(J2['compression'][ti])
            assert t_bars | c_bars == all_bars
            assert t_bars & c_bars == set()

    def test_no_subdivision_nodes(self):
        """Only original nodes (endpoints) appear — no subdivision nodes."""
        J1 = _make_j1()
        J2 = create_PKL_J2(J1)
        # Subdivision nodes are 1, 2, 5
        for ti in range(len(J1['t'])):
            for G in (J2['tension'][ti], J2['compression'][ti]):
                assert 1 not in G.nodes
                assert 2 not in G.nodes
                assert 5 not in G.nodes

    def test_pickle_round_trip(self):
        J1 = _make_j1()
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "J2.pkl")
            J2 = create_PKL_J2(J1, output_path=out)
            assert os.path.isfile(out)
            with open(out, "rb") as f:
                loaded = pickle.load(f)
            assert loaded['t'] == J2['t']
            for ti in range(len(J2['t'])):
                assert set(loaded['tension'][ti].nodes) == set(J2['tension'][ti].nodes)
                assert set(loaded['tension'][ti].edges) == set(J2['tension'][ti].edges)
                assert set(loaded['compression'][ti].nodes) == set(J2['compression'][ti].nodes)
                assert set(loaded['compression'][ti].edges) == set(J2['compression'][ti].edges)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
