import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from A001_functions.fem_stress_interpolation import (
    compute_integration_points,
    interpolate_stress,
    _map_physical_to_natural,
    _interpolate_at_natural_coords,
    _shape_functions,
)


# ---------------------------------------------------------------------------
# Helper: build synthetic DATA_C2 and DATA_B for a single rectangular element
# ---------------------------------------------------------------------------
def _make_synthetic_data(
    x0=0.0, y0=0.0, dx=2.0, dy=2.0,
    s11_values=None, s22_values=None, s21_values=None,
    n_times=20,
):
    """
    Create fake DATA_C2 and DATA_B dictionaries for a single
    rectangular quad element with corners at:
        (x0, y0), (x0+dx, y0), (x0+dx, y0+dy), (x0, y0+dy)

    Stress values at the 4 Gauss points can be prescribed.
    """
    if s11_values is None:
        s11_values = [100.0, 200.0, 300.0, 400.0]
    if s22_values is None:
        s22_values = [10.0, 20.0, 30.0, 40.0]
    if s21_values is None:
        s21_values = [1.0, 2.0, 3.0, 4.0]

    # Node numbering starts at 1
    _node_coords = [
        [x0, y0],
        [x0 + dx, y0],
        [x0 + dx, y0 + dy],
        [x0, y0 + dy],
    ]
    DATA_C2 = {
        'elements': {'1': [1, 2, 3, 4]},  # single element, 1-based key
        'nodes_time': [
            {str(j + 1): _node_coords[j] for j in range(4)}
            for ti in range(n_times)
        ],
    }

    # DATA_B: stress[key][ip*2][ti]
    # key = str(element_idx + 1) = '1'
    def _make_stress_array(vals):
        # vals: list of 4 values, one per integration point
        # Structure: stress['1'][ip*2][ti] -> value
        # ip*2 gives indices 0, 2, 4, 6
        arr = {}
        arr['1'] = {}
        for ip in range(4):
            arr['1'][ip * 2] = {ti: vals[ip] for ti in range(n_times)}
        return arr

    DATA_B = {
        'S11': _make_stress_array(s11_values)['1'],
        'S22': _make_stress_array(s22_values)['1'],
        'S21': _make_stress_array(s21_values)['1'],
    }
    # Wrap so that DATA_B['S11']['1'][ip*2][ti] works
    DATA_B = {
        'S11': {'1': DATA_B['S11']},
        'S22': {'1': DATA_B['S22']},
        'S21': {'1': DATA_B['S21']},
    }

    return DATA_C2, DATA_B


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNaturalCoordinateMapping:
    """Test that physical ↔ natural coordinate mapping is consistent."""

    def test_center_of_unit_square(self):
        """Center of a [0,2]×[0,2] square should map to (0,0) in natural coords."""
        nodes = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=float)
        xi, eta = _map_physical_to_natural(1.0, 1.0, nodes)
        assert abs(xi) < 1e-10
        assert abs(eta) < 1e-10

    def test_corner_mapping(self):
        """Corners should map to (±1, ±1)."""
        nodes = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=float)

        corners_phys = [(0, 0), (2, 0), (2, 2), (0, 2)]
        corners_nat = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

        for (px, py), (exi, eeta) in zip(corners_phys, corners_nat):
            xi, eta = _map_physical_to_natural(px, py, nodes)
            assert abs(xi - exi) < 1e-10, f"Failed at corner ({px},{py})"
            assert abs(eta - eeta) < 1e-10, f"Failed at corner ({px},{py})"

    def test_round_trip(self):
        """Map physical → natural → physical and verify consistency."""
        nodes = np.array([[1, 1], [4, 0.5], [5, 3], [0.5, 3.5]], dtype=float)
        # Pick an interior point via known natural coords
        xi0, eta0 = 0.3, -0.2
        N = _shape_functions(xi0, eta0)
        x0 = N @ nodes[:, 0]
        y0 = N @ nodes[:, 1]

        xi_rec, eta_rec = _map_physical_to_natural(x0, y0, nodes)
        assert abs(xi_rec - xi0) < 1e-10
        assert abs(eta_rec - eta0) < 1e-10


class TestInterpolationAtGaussPoints:
    """Verify that interpolation exactly recovers stress at Gauss points."""

    def test_recover_gauss_point_values(self):
        """
        When we query exactly at a Gauss point, the interpolated stress
        should match the prescribed value.
        """
        s11_vals = [100.0, 200.0, 300.0, 400.0]
        DATA_C2, DATA_B = _make_synthetic_data(
            x0=0, y0=0, dx=4, dy=4, s11_values=s11_vals
        )
        ti = 5

        nodes = np.array([[0, 0], [4, 0], [4, 4], [0, 4]], dtype=float)
        int_points, _ = compute_integration_points(nodes.tolist())

        for ip in range(4):
            result = interpolate_stress(
                DATA_C2, DATA_B,
                int_points[ip, 0], int_points[ip, 1],
                ti_key=str(ti + 1), element_idx='1',
            )
            assert abs(result['S11'] - s11_vals[ip]) < 1e-10, (
                f"Gauss point {ip}: expected S11={s11_vals[ip]}, got {result['S11']}"
            )


class TestUniformStressField:
    """If all Gauss points have the same stress, any point should return that stress."""

    def test_uniform_field(self):
        uniform = 42.0
        DATA_C2, DATA_B = _make_synthetic_data(
            s11_values=[uniform] * 4,
            s22_values=[uniform] * 4,
            s21_values=[uniform] * 4,
        )
        ti = 3

        # Query at several random interior points
        rng = np.random.default_rng(seed=123)
        for _ in range(20):
            x = rng.uniform(0.1, 1.9)
            y = rng.uniform(0.1, 1.9)
            result = interpolate_stress(DATA_C2, DATA_B, x, y, ti_key=str(ti + 1))
            assert abs(result['S11'] - uniform) < 1e-10
            assert abs(result['S22'] - uniform) < 1e-10
            assert abs(result['S21'] - uniform) < 1e-10


class TestLinearField:
    """
    If the stress varies bilinearly over the Gauss sub-grid, the
    interpolation should reproduce it exactly at the element center.
    """

    def test_center_is_average(self):
        """
        For a bilinear field on a rectangular element, the value at the
        center (xi=0, eta=0) equals the average of the 4 Gauss-point values.
        """
        s11_vals = [10.0, 20.0, 40.0, 30.0]
        DATA_C2, DATA_B = _make_synthetic_data(
            x0=0, y0=0, dx=2, dy=2, s11_values=s11_vals
        )
        ti = 0
        result = interpolate_stress(DATA_C2, DATA_B, 1.0, 1.0, ti_key=str(ti + 1))
        expected = np.mean(s11_vals)
        assert abs(result['S11'] - expected) < 1e-10


class TestElementSearch:
    """Verify that the correct element is found when element_idx is not given."""

    def test_auto_find_element(self):
        """Build a 2-element mesh and check that each query lands in the right element."""
        # Element 0: [0,2]×[0,2],  Element 1: [2,4]×[0,2]
        DATA_C2 = {
            'elements': {
                '1': [1, 2, 3, 4],
                '2': [2, 5, 6, 3],
            },
            'nodes_time': [
                {
                    '1': [0, 0],
                    '2': [2, 0],
                    '3': [2, 2],
                    '4': [0, 2],
                    '5': [4, 0],
                    '6': [4, 2],
                }
            ],
        }

        # Distinct stress values per element
        DATA_B = {
            'S11': {}, 'S22': {}, 'S21': {},
        }
        for comp in ['S11', 'S22', 'S21']:
            DATA_B[comp]['1'] = {ip * 2: {0: 100.0} for ip in range(4)}
            DATA_B[comp]['2'] = {ip * 2: {0: 999.0} for ip in range(4)}

        # Point inside element 0
        r0 = interpolate_stress(DATA_C2, DATA_B, 1.0, 1.0, ti_key='1')
        assert r0['element_idx'] == '1'
        assert abs(r0['S11'] - 100.0) < 1e-10

        # Point inside element 1
        r1 = interpolate_stress(DATA_C2, DATA_B, 3.0, 1.0, ti_key='1')
        assert r1['element_idx'] == '2'
        assert abs(r1['S11'] - 999.0) < 1e-10


class TestReturnedKeys:
    """Make sure the returned dict contains all expected keys."""

    def test_keys_present(self):
        DATA_C2, DATA_B = _make_synthetic_data()
        result = interpolate_stress(DATA_C2, DATA_B, 1.0, 1.0, ti_key='1')
        for key in ['S11', 'S22', 'S21', 'element_idx', 'xi', 'eta']:
            assert key in result, f"Missing key: {key}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])