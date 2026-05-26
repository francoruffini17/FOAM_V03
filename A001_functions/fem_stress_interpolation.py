import numpy as np
import pickle
from typing import Tuple, Optional


def compute_integration_points(nodes_square):
    """
    Compute the physical positions of 2x2 Gauss integration points
    for a 4-node quadrilateral element.

    Parameters
    ----------
    nodes_square : list of [x, y]
        The 4 corner nodes of the element: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    Returns
    -------
    int_points : np.ndarray, shape (4, 2)
        Physical (x, y) coordinates of the 4 integration points.
    natural_coords : np.ndarray, shape (4, 2)
        Natural (xi, eta) coordinates of the 4 integration points.
    """
    # 2x2 Gauss points in natural coordinates
    g = 1.0 / np.sqrt(3.0)
    natural_coords = np.array([
        [-g, -g],
        [ g, -g],
        [ g,  g],
        [-g,  g],
    ])

    nodes = np.array(nodes_square)  # shape (4, 2)

    int_points = np.zeros((4, 2))
    for i, (xi, eta) in enumerate(natural_coords):
        # Bilinear shape functions for a 4-node quad
        N = np.array([
            (1 - xi) * (1 - eta) / 4.0,
            (1 + xi) * (1 - eta) / 4.0,
            (1 + xi) * (1 + eta) / 4.0,
            (1 - xi) * (1 + eta) / 4.0,
        ])
        int_points[i] = N @ nodes

    return int_points, natural_coords


def _shape_functions(xi: float, eta: float) -> np.ndarray:
    """Bilinear shape functions for a 4-node quad evaluated at (xi, eta)."""
    return np.array([
        (1 - xi) * (1 - eta) / 4.0,
        (1 + xi) * (1 - eta) / 4.0,
        (1 + xi) * (1 + eta) / 4.0,
        (1 - xi) * (1 + eta) / 4.0,
    ])


def _shape_functions_tri(xi: float, eta: float) -> np.ndarray:
    """Linear shape functions for a 3-node triangle at (xi, eta).

    Reference element: vertices at (0,0), (1,0), (0,1).
    """
    return np.array([1.0 - xi - eta, xi, eta])


def _map_physical_to_natural(
    x: float, y: float, nodes: np.ndarray,
    tol: float = 1e-12, max_iter: int = 50
) -> Tuple[float, float]:
    """
    Newton-Raphson iteration to find the natural coordinates (xi, eta)
    corresponding to a physical point (x, y) inside a 4-node quad element.

    Parameters
    ----------
    x, y : float
        Physical coordinates of the query point.
    nodes : np.ndarray, shape (4, 2)
        Corner nodes of the element.
    tol : float
        Convergence tolerance.
    max_iter : int
        Maximum number of iterations.

    Returns
    -------
    xi, eta : float
        Natural coordinates.
    """
    xi, eta = 0.0, 0.0  # initial guess (center of element)

    for _ in range(max_iter):
        N = _shape_functions(xi, eta)
        # Current mapped position
        x_map = N @ nodes[:, 0]
        y_map = N @ nodes[:, 1]

        # Residual
        R = np.array([x_map - x, y_map - y])

        if np.linalg.norm(R) < tol:
            break

        # Jacobian: d(x_map, y_map) / d(xi, eta)
        dN_dxi = np.array([
            -(1 - eta) / 4.0,
             (1 - eta) / 4.0,
             (1 + eta) / 4.0,
            -(1 + eta) / 4.0,
        ])
        dN_deta = np.array([
            -(1 - xi) / 4.0,
            -(1 + xi) / 4.0,
             (1 + xi) / 4.0,
             (1 - xi) / 4.0,
        ])

        J = np.array([
            [dN_dxi @ nodes[:, 0], dN_deta @ nodes[:, 0]],
            [dN_dxi @ nodes[:, 1], dN_deta @ nodes[:, 1]],
        ])

        delta = np.linalg.solve(J, -R)
        xi += delta[0]
        eta += delta[1]

    return xi, eta


def _map_physical_to_natural_tri(
    x: float, y: float, nodes: np.ndarray,
) -> Tuple[float, float]:
    """
    Direct (exact) inverse mapping from physical (x, y) to natural
    coordinates (xi, eta) for a 3-node triangle.

    Reference element: vertices at (0,0), (1,0), (0,1).
    """
    x1, y1 = nodes[0]
    x2, y2 = nodes[1]
    x3, y3 = nodes[2]
    J = np.array([[x2 - x1, x3 - x1],
                   [y2 - y1, y3 - y1]])
    rhs = np.array([x - x1, y - y1])
    xi_eta = np.linalg.solve(J, rhs)
    return float(xi_eta[0]), float(xi_eta[1])


def _point_in_quad(xi: float, eta: float, tol: float = 1.05) -> bool:
    """Check if the natural coordinates are within the reference element [-1, 1]^2."""
    return abs(xi) <= tol and abs(eta) <= tol


def _point_in_tri(xi: float, eta: float, tol: float = 1e-8) -> bool:
    """Check if natural coordinates are inside the reference triangle."""
    return xi >= -tol and eta >= -tol and (xi + eta) <= 1.0 + tol


def _dist_outside_tri(xi: float, eta: float) -> float:
    """Distance metric for a point outside the reference triangle."""
    return max(0.0, -xi) + max(0.0, -eta) + max(0.0, xi + eta - 1.0)


def _get_element_nodes(DATA_C2: dict, element_key: str, ti_key: str) -> np.ndarray:
    """
    Get the physical coordinates of the nodes of an element at a time step.

    Works for both triangular (3-node) and quadrilateral (4-node) elements.

    Parameters
    ----------
    element_key : str
        1-based string key into ``DATA_C2['elements']``, e.g. ``'1'``.
    ti_key : str
        1-based string key; converted to 0-based index for
        ``DATA_C2['nodes_time']`` (a list of dicts), e.g. ``'1'`` → index 0.

    Returns
    -------
    nodes : np.ndarray, shape (n, 2)  where n is 3 or 4
    """
    elem = DATA_C2['elements'][element_key]
    ti = int(ti_key) - 1
    nodes = np.array([DATA_C2['nodes_time'][ti][str(n)] for n in elem])
    return nodes


def _get_stress_at_integration_points(
    DATA_B: dict, element_key: str, ti_key: str, n_element_nodes: int = 4
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract stress values at the integration points of an element.

    For a 4-node quad (CPS4): 4 integration points (2x2 Gauss).
    For a 3-node triangle (CPS3): 1 integration point (centroid).

    Parameters
    ----------
    element_key : str
        1-based string key, e.g. ``'1'``.  Used directly as DATA_B key.
    ti_key : str
        1-based string key for the time step, e.g. ``'1'``.
        Converted to 0-based int internally for DATA_B time indexing.

    Returns
    -------
    s11, s22, s21 : np.ndarray, each of shape (n_ips,)
    """
    ti = int(ti_key) - 1  # DATA_B uses 0-based time indices
    s21_key = 'S21' if 'S21' in DATA_B else 'S12'

    if n_element_nodes == 3:
        # Triangle (CPS3): 1 integration point
        s11 = np.array([DATA_B['S11'][element_key][0][ti]])
        s22 = np.array([DATA_B['S22'][element_key][0][ti]])
        s21 = np.array([DATA_B[s21_key][element_key][0][ti]])
    else:
        # Quad (CPS4): 4 integration points
        # Stride of 2 accounts for section-point entries in the data layout.
        s11 = np.array([DATA_B['S11'][element_key][ip * 2][ti] for ip in range(4)])
        s22 = np.array([DATA_B['S22'][element_key][ip * 2][ti] for ip in range(4)])
        s21 = np.array([DATA_B[s21_key][element_key][ip * 2][ti] for ip in range(4)])

    return s11, s22, s21


def _interpolate_at_natural_coords(
    xi: float, eta: float, values_at_gauss: np.ndarray
) -> float:
    """
    Interpolate a field known at 2x2 Gauss points to an arbitrary
    point (xi, eta) in the natural coordinate system, using bilinear
    interpolation over the Gauss-point sub-grid.

    The 4 Gauss points sit at (±1/√3, ±1/√3). We treat them as
    corners of a sub-quad and use shape functions scaled to that
    sub-quad.

    Parameters
    ----------
    xi, eta : float
        Natural coordinates in [-1, 1].
    values_at_gauss : np.ndarray, shape (4,)
        Field values at the 4 Gauss points (ordered as
        (-g,-g), (+g,-g), (+g,+g), (-g,+g)).

    Returns
    -------
    float
        Interpolated value.
    """
    g = 1.0 / np.sqrt(3.0)

    # Map (xi, eta) from [-1,1] to the Gauss sub-quad [-g, g]
    # Shape functions for the sub-quad: corners at (±g, ±g)
    N = np.array([
        (g - xi) * (g - eta),
        (g + xi) * (g - eta),
        (g + xi) * (g + eta),
        (g - xi) * (g + eta),
    ]) / (4.0 * g * g)

    return float(N @ values_at_gauss)


def interpolate_stress(
    DATA_C2: dict,
    DATA_B: dict,
    x: float,
    y: float,
    ti_key: str,
    element_idx: Optional[str] = None,
) -> dict:
    """
    Interpolate stress (S11, S22, S21) at an arbitrary point (x, y)
    from the finite element mesh data.

    Supports both triangular (3-node) and quadrilateral (4-node) elements,
    including mixed meshes.

    Strategy:
      1. If element_idx is not given, loop over all elements and find the
         one whose natural-coordinate mapping places (x, y) inside.
      2. Map (x, y) → (xi, eta) in natural coordinates.
      3. Interpolate stresses from integration points:
         - Quad: bilinear interpolation over 4 Gauss points.
         - Triangle: constant stress (single integration point).

    Parameters
    ----------
    DATA_C2 : dict
        Mesh data with 1-based string keys (elements, nodes_time, …).
    DATA_B : dict
        Stress data (S11, S22, S21).
    x, y : float
        Physical coordinates of the query point.
    ti_key : str
        1-based string key for the time step, e.g. ``'1'``.
    element_idx : str, optional
        1-based string key of the element that contains (x, y).
        If given, the element search is skipped.

    Returns
    -------
    dict
        {'S11': float, 'S22': float, 'S21': float, 'element_idx': str,
         'xi': float, 'eta': float}
    """
    if element_idx is not None:
        candidates = [element_idx]
    else:
        candidates = sorted(DATA_C2['elements'].keys(), key=int)

    best_elem = None
    best_xi, best_eta = None, None
    best_dist = np.inf  # distance in natural coords from (0,0), used as tie-breaker

    for ek in candidates:
        nodes = _get_element_nodes(DATA_C2, ek, ti_key)
        n_nodes = len(DATA_C2['elements'][ek])

        if n_nodes == 3:
            xi, eta = _map_physical_to_natural_tri(x, y, nodes)
            if _point_in_tri(xi, eta, tol=1e-8):
                best_elem = ek
                best_xi, best_eta = xi, eta
                break
            dist = _dist_outside_tri(xi, eta)
        else:
            xi, eta = _map_physical_to_natural(x, y, nodes)
            if _point_in_quad(xi, eta, tol=1.0 + 1e-8):
                best_elem = ek
                best_xi, best_eta = xi, eta
                break
            dist = max(abs(xi), abs(eta))

        if dist < best_dist:
            best_dist = dist
            best_elem = ek
            best_xi, best_eta = xi, eta

    if best_elem is None:
        raise ValueError(
            f"Could not locate point ({x}, {y}) in any element at time step {ti_key}."
        )

    # Determine element type
    n_elem_nodes = len(DATA_C2['elements'][best_elem])

    # Get stress values at integration points
    s11, s22, s21 = _get_stress_at_integration_points(
        DATA_B, best_elem, ti_key, n_element_nodes=n_elem_nodes
    )

    if n_elem_nodes == 3:
        # Triangle: single integration point → constant stress
        S11_val = float(s11[0])
        S22_val = float(s22[0])
        S21_val = float(s21[0])
    else:
        # Quad: interpolate from 4 Gauss points
        S11_val = _interpolate_at_natural_coords(best_xi, best_eta, s11)
        S22_val = _interpolate_at_natural_coords(best_xi, best_eta, s22)
        S21_val = _interpolate_at_natural_coords(best_xi, best_eta, s21)

    return {
        'S11': S11_val,
        'S22': S22_val,
        'S21': S21_val,
        'element_idx': best_elem,
        'xi': best_xi,
        'eta': best_eta,
    }