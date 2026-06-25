"""
Hexagonal Mesh Generator for Square Domains with Circular Holes

This module generates finite element meshes for bilinear quadrilateral elements
on a square domain containing circular holes arranged in a hexagonal packing pattern.

The mesh CONFORMS to the circular hole boundaries - nodes are placed exactly on
the circle perimeters, providing accurate geometric representation.

Uses Gmsh for robust mesh generation with proper boundary conformity.

The hexagonal packing uses a triangular lattice where:
- Holes are arranged in rows
- Alternating rows are offset by half the horizontal spacing
- Vertical spacing is sqrt(3)/2 times the horizontal spacing

Key parameters:
- porosity: fraction of hole area to total area (defined for unit cell)
- n_holes_width: number of holes across the width of the domain
- domain_size: side length of the square domain
- elements_around_hole: controls mesh density around holes
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PolyCollection, LineCollection
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import warnings
import json as _json
import os
from scipy.spatial import Delaunay, Voronoi, cKDTree
import re 
from collections import defaultdict


try:
    import gmsh
    GMSH_AVAILABLE = True
except ImportError:
    GMSH_AVAILABLE = False
    warnings.warn("Gmsh not available. Install with: pip install gmsh")



def generate_hexagonal_gridhex_mesh(
    domain_size: float,
    hexagon_size: float,
    hole_centers=None,
    hole_radius: float = 0.0,
    pointy_top: bool = True,
    remove_edge_nodes: bool = True,
):
    """
    Build a hexagonal-grid graph object with the same storage layout
    as :class:`GraphMeshData`.
 
    An auxiliary hexagonal tiling covers ``[0, domain_size]²``.  For every
    hexagon that overlaps the domain:
 
    * A **centre node** (label = 1) is placed at the hexagon centre.
    * **12 peripheral nodes** (label = 2) are placed at the 6 *vertices*
      and the 6 *edge midpoints* of the hexagon.
    * **12 spoke bars** connect the centre to each peripheral node.
 
    Peripheral nodes at the same geometric position (shared by adjacent
    hexagons) are merged into a single node.  Nodes strictly inside a hole,
    or on the domain boundary (when ``remove_edge_nodes=True``), are removed
    together with all bars attached to them.
 
    Parameters
    ----------
    domain_size : float
        Side length of the square domain ``[0, L]²``.
    hexagon_size : float
        Vertex-to-vertex diameter of each auxiliary hexagon (2× circumradius).
    hole_centers : array-like, shape (N, 2), optional
        Centres of circular holes in the FE mesh.
    hole_radius : float
        Radius of every hole.
    pointy_top : bool
        ``True``  → pointy-top orientation (vertex at top/bottom).
        ``False`` → flat-top  orientation (flat edge at top/bottom).
    remove_edge_nodes : bool
        Remove nodes on the domain boundary (same as ``generate_cartesian_grid_mesh``).
 
    Returns
    -------
    GraphMeshData
    """
    R = hexagon_size / 2.0          # circumradius  (centre → vertex)
    r = R * np.sqrt(3.0) / 2.0     # inradius      (centre → edge midpoint)
    L = domain_size
 
    # ------------------------------------------------------------------
    # 1.  Generate auxiliary hexagon centres that cover [0, L]²
    # ------------------------------------------------------------------
    if pointy_top:
        # pointy-top:
        #   horizontal pitch between centres = sqrt(3) * R
        #   vertical   pitch between centres = 3/2 * R
        #   odd rows are offset by half the horizontal pitch
        sq3R      = np.sqrt(3.0) * R
        col_pitch = sq3R
        row_pitch = 1.5 * R
        row_offset = sq3R / 2.0
 
        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3
 
        hex_centres = []
        for row in range(-2, n_rows):
            cy = row * row_pitch
            for col in range(-2, n_cols):
                cx = col * col_pitch + (row % 2) * row_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))
 
        # pointy-top: vertices at 30°+k·60°, midpoints at 0°+k·60°
        vertex_angles   = np.deg2rad([30, 90, 150, 210, 270, 330])
        midpoint_angles = np.deg2rad([ 0, 60, 120, 180, 240, 300])
 
    else:
        # flat-top:
        #   horizontal pitch = 3/2 * R
        #   vertical   pitch = sqrt(3) * R
        #   odd columns are offset by half the vertical pitch
        sq3R       = np.sqrt(3.0) * R
        col_pitch  = 1.5 * R
        row_pitch  = sq3R
        col_offset = sq3R / 2.0
 
        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3
 
        hex_centres = []
        for col in range(-2, n_cols):
            cx = col * col_pitch
            for row in range(-2, n_rows):
                cy = row * row_pitch + (col % 2) * col_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))
 
        # flat-top: vertices at 0°+k·60°, midpoints at 30°+k·60°
        vertex_angles   = np.deg2rad([ 0, 60, 120, 180, 240, 300])
        midpoint_angles = np.deg2rad([30, 90, 150, 210, 270, 330])
 
    vertex_dirs   = np.stack([np.cos(vertex_angles),
                               np.sin(vertex_angles)], axis=1)   # (6,2)
    midpoint_dirs = np.stack([np.cos(midpoint_angles),
                               np.sin(midpoint_angles)], axis=1)  # (6,2)
 
    # ------------------------------------------------------------------
    # 2.  Collect unique node positions (merge shared peripheral nodes)
    # ------------------------------------------------------------------
    ROUND = 9   # decimal places used for deduplication key
 
    pos_to_idx: dict = {}
    node_xy:    list = []
    node_label: list = []
    raw_bars:   list = []
 
    def _add_node(x, y, label):
        k = (round(x, ROUND), round(y, ROUND))
        if k not in pos_to_idx:
            pos_to_idx[k] = len(node_xy)
            node_xy.append([x, y])
            node_label.append(label)
        return pos_to_idx[k]
 
    for (cx, cy) in hex_centres:
        ci = _add_node(cx, cy, 1)                           # centre (label 1)
 
        for d in vertex_dirs:                               # 6 vertices
            px, py = cx + R * d[0], cy + R * d[1]
            pi = _add_node(px, py, 2)                       # peripheral (label 2)
            raw_bars.append((ci, pi))
 
        for d in midpoint_dirs:                             # 6 edge midpoints
            px, py = cx + r * d[0], cy + r * d[1]
            pi = _add_node(px, py, 2)
            raw_bars.append((ci, pi))
 
    nodes_arr  = np.array(node_xy,    dtype=float)
    labels_arr = np.array(node_label, dtype=int)
 
    # ------------------------------------------------------------------
    # 3.  Build keep mask: domain interior
    # ------------------------------------------------------------------
    tol = L * 1e-9
 
    in_domain = (
        (nodes_arr[:, 0] >= -tol) & (nodes_arr[:, 0] <= L + tol) &
        (nodes_arr[:, 1] >= -tol) & (nodes_arr[:, 1] <= L + tol)
    )
    keep = in_domain.copy()
 
    if remove_edge_nodes:
        on_boundary = (
            (nodes_arr[:, 0] <= tol)     |
            (nodes_arr[:, 0] >= L - tol) |
            (nodes_arr[:, 1] <= tol)     |
            (nodes_arr[:, 1] >= L - tol)
        )
        keep &= ~on_boundary
 
    # ------------------------------------------------------------------
    # 4.  Keep mask: remove nodes strictly inside holes
    # ------------------------------------------------------------------
    if hole_centers is not None and len(hole_centers) > 0:
        centers_arr = np.asarray(hole_centers, dtype=float)
        active_r    = max(float(hole_radius) - L * 1e-12, 0.0)
        active_r_sq = active_r ** 2
 
        if active_r_sq > 0.0:
            # vectorised: compute min distance² for every node in one shot
            # shape: (n_nodes, n_holes)
            dx = nodes_arr[:, 0:1] - centers_arr[:, 0]   # (N,H)
            dy = nodes_arr[:, 1:2] - centers_arr[:, 1]   # (N,H)
            dist_sq = dx ** 2 + dy ** 2                   # (N,H)
            inside  = np.any(dist_sq < active_r_sq, axis=1)
            keep   &= ~inside
 
    # ------------------------------------------------------------------
    # 5.  Re-index surviving nodes
    # ------------------------------------------------------------------
    old_to_new            = np.full(len(nodes_arr), -1, dtype=int)
    old_to_new[keep]      = np.arange(keep.sum(), dtype=int)
 
    final_nodes  = nodes_arr[keep]
    final_labels = labels_arr[keep]
 
    # ------------------------------------------------------------------
    # 6.  Filter bars (both endpoints must survive) + deduplicate
    # ------------------------------------------------------------------
    final_bars:    list = []
    final_bar_num: list = []
    bar_counter         = 0
    seen_bars:     set  = set()
 
    for (a, b) in raw_bars:
        na, nb = old_to_new[a], old_to_new[b]
        if na < 0 or nb < 0:
            continue
        key = (min(na, nb), max(na, nb))
        if key in seen_bars:
            continue
        seen_bars.add(key)
        final_bars.append([na, nb])
        final_bar_num.append(bar_counter)
        bar_counter += 1
 
    bars_arr    = (np.array(final_bars,    dtype=int)
                   if final_bars else np.empty((0, 2), dtype=int))
    bar_num_arr = (np.array(final_bar_num, dtype=int)
                   if final_bar_num else np.empty((0,), dtype=int))
 
    return GraphMeshData(
        nodes      =final_nodes,
        node_ids   =final_labels,
        bars       =bars_arr,
        bar_numbers=bar_num_arr,
    )
 
 
def export_gridhex_mesh(grid: "GraphMeshData", filename: str) -> None:
    """Write hexagonal-grid data as ``*.gridhex.json``."""
    write_graph_json(
        grid,
        filename,
        graph_type="gridhex",
        created_by="export_gridhex_mesh",
        parameters={},
    )
 



def build_individual_surfaces_2(nodes, elements):
    """
    Build a dictionary mapping each hole surface to the element edges that form it.

    Nodes:
        nodes[i] = [x, y, ID]
        ID format: '1AB' (no hole) or '1ABX...' (hole number X..., possibly multi-digit)

    Elements:
        elements[e] = (n1, n2, n3)  # node indices into nodes list

    Returns:
        individual_surfaces: dict
            {
              'Surface-40': [[73, 'S1'], [102, 'S3'], ...],
              ...
            }

    Edge convention:
        S1: n1 -> n2
        S2: n2 -> n3
        S3: n3 -> n4
        S4: n4 -> n1
    """
    # Match '1AB' plus optional trailing digits
    pat = re.compile(r'^[0-9][0-9][0-9]([0-9]+)?$')

    def hole_num(node_id):
        """Return int hole number if present, else None."""
        node_id = str(node_id)
        m = pat.match(node_id)
        if not m:
            return None
        tail = m.group(1)
        return int(tail) if tail is not None else None

    # Precompute hole number per node index for speed
    node_hole = [None] * len(nodes)
    for i, node in enumerate(nodes):
        node_hole[i] = hole_num(node[2])

    individual_surfaces = defaultdict(list)

    for e_idx, elem in enumerate(elements):
        npe = len(elem)  # 3 for tri, 4 for quad

        # Check each edge: S1 (n0->n1), S2 (n1->n2), S3 (n2->n3), S4 (n3->n0)
        edge_names = ['S1', 'S2', 'S3', 'S4'][:npe]
        for edge_i in range(npe):
            na = elem[edge_i]
            nb = elem[(edge_i + 1) % npe]
            ha, hb = node_hole[na], node_hole[nb]
            if ha is not None and ha == hb:
                individual_surfaces[f"Surface-hole-{ha}"].append(
                    [e_idx + 1, edge_names[edge_i]]
                )
            
    individual_ele_sets = {}
    external_surfaces = {}

    nodes_new = [node[:2] for node in nodes]
    lst = [e[:] for e in elements]
    elements_new = [[x + 1 for x in sublist] for sublist in lst]
    
    return nodes_new, elements_new, dict(individual_surfaces), individual_ele_sets, external_surfaces


def scale_mesh(nodes, Ex, Ey, len=3):
    nodes_out = []
    if len == 3:
        for node in nodes:
            x, y, B = node
            x_scaled = x * Ex
            y_scaled = y * Ey
            nodes_out.append((x_scaled, y_scaled, B))
    elif len == 2:
        for node in nodes:
            x, y = node
            x_scaled = x * Ex
            y_scaled = y * Ey
            nodes_out.append((x_scaled, y_scaled))
    return nodes_out



@dataclass
class MeshData:
    """Container for mesh data."""
    nodes: np.ndarray  # (n_nodes, 2) array of node coordinates
    elements: np.ndarray  # (n_elements, 3 or 4) array of node indices (tri or quad)
    boundary_nodes: Dict[str, np.ndarray]  # 'bottom', 'right', 'top', 'left' edge nodes
    hole_boundary_nodes: List[np.ndarray]  # indices of nodes on each hole boundary
    node_labels: np.ndarray = None  # Label for each node (assigned after creation)
    hole_classifications: List[int] = None  # B-digit per hole (1=left-cut,2=bottom-cut,3=right-cut,4=top-cut,5=complete)
    element_types: np.ndarray = None  # (n_elements,) int array: 3=TRI, 4=QUAD. None means all QUAD.
    periodic_pairs_lr: np.ndarray = None  # (N, 2) int: [left_node_idx, right_node_idx]
    periodic_pairs_tb: np.ndarray = None  # (N, 2) int: [top_node_idx, bottom_node_idx]

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_elements(self) -> int:
        return len(self.elements)

    def get_all_boundary_nodes(self) -> np.ndarray:
        """Return all domain boundary nodes."""
        if not self.boundary_nodes:
            return np.array([])
        return np.unique(np.concatenate(list(self.boundary_nodes.values())))

    def compute_node_labels(self) -> np.ndarray:
        """
        Compute labels for all nodes using the format 1ABX..
        
        Format: 1ABX..
            1: Always present (prefix)
            A: Edge/corner position
                1 = left edge (not corner)
                2 = bottom edge (not corner)
                3 = right edge (not corner)
                4 = top edge (not corner)
                5 = bottom-left corner
                6 = top-right corner
                7 = top-left corner
                8 = bottom-right corner
                0 = interior (not on any edge or corner)
            B: Hole membership / completeness
                0 = does not belong to any hole
                1 = belongs to a hole cut by the left edge
                2 = belongs to a hole cut by the bottom edge
                3 = belongs to a hole cut by the right edge
                4 = belongs to a hole cut by the top edge
                5 = belongs to a complete hole (fully inside domain)
            X..: Hole number (1-indexed), only present if B != 0

        Returns:
            Array of string labels for each node
        """
        n_nodes = self.n_nodes
        labels = np.empty(n_nodes, dtype=object)
        
        # Create sets for faster lookup
        left_set = set(self.boundary_nodes.get('left', []))
        right_set = set(self.boundary_nodes.get('right', []))
        bottom_set = set(self.boundary_nodes.get('bottom', []))
        top_set = set(self.boundary_nodes.get('top', []))
        
        # Use hole_classifications if available, otherwise default all to 5
        if self.hole_classifications is not None:
            classifications = self.hole_classifications
        else:
            classifications = [5] * len(self.hole_boundary_nodes)
        
        # Create hole membership dict: node_idx -> (hole_number, B_digit)
        hole_membership = {}
        for hole_idx, hole_nodes in enumerate(self.hole_boundary_nodes):
            b_digit = classifications[hole_idx]
            for node_idx in hole_nodes:
                hole_membership[node_idx] = (hole_idx + 1, b_digit)  # 1-indexed
        
        for i in range(n_nodes):
            # Determine A (edge/corner position)
            on_left = i in left_set
            on_right = i in right_set
            on_bottom = i in bottom_set
            on_top = i in top_set
            
            # Check corners first (nodes on two edges)
            if on_bottom and on_left:
                A = '5'  # bottom-left corner
            elif on_top and on_right:
                A = '6'  # top-right corner
            elif on_top and on_left:
                A = '7'  # top-left corner
            elif on_bottom and on_right:
                A = '8'  # bottom-right corner
            # Then check edges (not corners)
            elif on_left:
                A = '1'  # left edge
            elif on_bottom:
                A = '2'  # bottom edge
            elif on_right:
                A = '3'  # right edge
            elif on_top:
                A = '4'  # top edge
            else:
                A = '0'  # interior
            
            # Determine B and X (hole membership)
            if i in hole_membership:
                hole_num, B_digit = hole_membership[i]
                B = str(B_digit)
                X = str(hole_num)
                labels[i] = f"1{A}{B}{X}"
            else:
                B = '0'
                labels[i] = f"1{A}{B}"
        
        self.node_labels = labels
        return labels

    def get_label_description(self, label: str) -> str:
        """
        Get human-readable description of a node label.
        
        Args:
            label: Node label in format 1ABX..
            
        Returns:
            Human-readable description
        """
        if len(label) < 3 or label[0] != '1':
            return "Invalid label"
        
        A = label[1]
        B = label[2]
        
        position_map = {
            '0': 'Interior',
            '1': 'Left edge',
            '2': 'Bottom edge',
            '3': 'Right edge',
            '4': 'Top edge',
            '5': 'Bottom-left corner',
            '6': 'Top-right corner',
            '7': 'Top-left corner',
            '8': 'Bottom-right corner'
        }
        
        position = position_map.get(A, 'Unknown position')
        
        hole_status_map = {
            '0': 'No hole',
            '1': 'Hole cut by left edge',
            '2': 'Hole cut by bottom edge',
            '3': 'Hole cut by right edge',
            '4': 'Hole cut by top edge',
            '5': 'Complete hole',
        }
        
        hole_status = hole_status_map.get(B, 'Unknown hole status')
        
        if B in ('1', '2', '3', '4', '5') and len(label) > 3:
            hole_num = label[3:]
            return f"{position}, {hole_status} #{hole_num}"
        elif B == '0':
            return f"{position}, {hole_status}"
        else:
            return f"{position}, {hole_status}"


@dataclass
class GraphMeshData:
    """
    Container for the subdivided Voronoi graph-mesh.

    Attributes:
        nodes: (N, 2) array of node coordinates.
        node_ids: (N,) int array – 1 for original Voronoi nodes,
            2 for nodes created by subdivision.
        bars: (M, 2) int array – each row ``[ni, nf]`` gives the start
            and end node indices of a sub-bar.
        bar_numbers: (M,) int array – the original bar number that each
            sub-bar belongs to.
    """
    nodes: np.ndarray
    node_ids: np.ndarray
    bars: np.ndarray
    bar_numbers: np.ndarray

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_bars(self) -> int:
        return len(self.bars)


MESH_FORMAT_VERSION = 1


def _json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return str(obj)


def _ensure_json_suffix(path: str, object_suffix: str) -> str:
    """Return a path ending in ``.<object_suffix>.json``."""
    suffix = f".{object_suffix}.json"
    path = str(path)
    if path.endswith(suffix):
        return path
    if path.endswith(".json"):
        stem = path[:-5]
    else:
        stem = path
    if stem.endswith(f".{object_suffix}"):
        return stem + ".json"
    return stem + suffix


def _mesh_base_path(mesh_path: str) -> str:
    mesh_path = str(mesh_path)
    if mesh_path.endswith(".mesh.json"):
        return mesh_path[:-10]
    if mesh_path.endswith(".json"):
        return mesh_path[:-5]
    return mesh_path


def _element_types_for_mesh(mesh: MeshData) -> np.ndarray:
    if mesh.element_types is not None and len(mesh.element_types) == mesh.n_elements:
        return np.asarray(mesh.element_types, dtype=int)
    if mesh.n_elements == 0:
        return np.array([], dtype=int)
    if isinstance(mesh.elements, np.ndarray) and mesh.elements.ndim == 2:
        return np.full(mesh.n_elements, mesh.elements.shape[1], dtype=int)
    return np.array([len(elem) for elem in mesh.elements], dtype=int)


def _mesh_elements_as_lists(mesh: MeshData) -> List[List[int]]:
    etypes = _element_types_for_mesh(mesh)
    out: List[List[int]] = []
    for elem, npe in zip(mesh.elements, etypes):
        out.append([int(elem[k]) for k in range(int(npe))])
    return out


def _mesh_boundary_as_json(boundary_nodes: Dict[str, np.ndarray]) -> Dict[str, List[int]]:
    return {
        name: [int(i) for i in np.asarray(indices, dtype=int).tolist()]
        for name, indices in (boundary_nodes or {}).items()
    }


def _periodic_pairs_as_json(pairs) -> List[List[int]]:
    if pairs is None:
        return []
    arr = np.asarray(pairs, dtype=int)
    if arr.size == 0:
        return []
    return [[int(a), int(b)] for a, b in arr.reshape(-1, 2)]


def _generator_geometry_payload(generator, mesh_kind: str) -> dict:
    centers = np.asarray(getattr(generator, "hole_centers", []), dtype=float)
    if centers.size == 0:
        centers = np.empty((0, 2), dtype=float)

    if hasattr(generator, "hole_radii"):
        radii = np.asarray(generator.hole_radii, dtype=float)
    else:
        radii = np.full(len(centers), float(generator.geometry.hole_radius))

    geometry = {
        "domain_size": float(generator.domain_size),
        "porosity": float(getattr(generator, "porosity", 0.0)),
        "hole_centers": centers.tolist(),
        "hole_radii": radii.tolist(),
        "horizontal_spacing": float(getattr(generator.geometry, "horizontal_spacing", 0.0)),
        "vertical_spacing": float(getattr(generator.geometry, "vertical_spacing", 0.0)),
        "hole_radius": float(getattr(generator.geometry, "hole_radius", 0.0)),
        "mesh_kind": mesh_kind,
    }
    if hasattr(generator, "n_holes_width"):
        geometry["n_holes_width"] = int(generator.n_holes_width)
    if len(radii) > 0:
        geometry["achieved_porosity"] = float(np.sum(np.pi * radii ** 2) / (generator.domain_size ** 2))
    return geometry


def write_mesh_json(
    mesh: MeshData,
    filename: str,
    *,
    mesh_kind: str,
    created_by: str,
    parameters: dict,
    generator,
) -> str:
    """Write the finite-element mesh and its creation metadata as JSON."""
    filename = _ensure_json_suffix(filename, "mesh")
    out_dir = os.path.dirname(filename)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    if mesh.node_labels is None:
        mesh.compute_node_labels()

    etypes = _element_types_for_mesh(mesh)
    geometry = _generator_geometry_payload(generator, mesh_kind)
    periodic_mode = str(parameters.get("periodic", "none")).lower()

    payload = {
        "format_version": MESH_FORMAT_VERSION,
        "type": "mesh",
        "mesh_kind": mesh_kind,
        "created_by": created_by,
        "parameters": parameters,
        "geometry": geometry,
        "nodes": [
            {"x": float(node[0]), "y": float(node[1]), "label": str(label)}
            for node, label in zip(mesh.nodes, mesh.node_labels)
        ],
        "elements": _mesh_elements_as_lists(mesh),
        "element_types": [int(x) for x in etypes.tolist()],
        "boundary_nodes": _mesh_boundary_as_json(mesh.boundary_nodes),
        "hole_boundary_nodes": [
            [int(i) for i in np.asarray(indices, dtype=int).tolist()]
            for indices in (mesh.hole_boundary_nodes or [])
        ],
        "hole_classifications": (
            [int(x) for x in mesh.hole_classifications]
            if mesh.hole_classifications is not None else []
        ),
        "periodic": {
            "mode": periodic_mode,
            "left_right_pairs": _periodic_pairs_as_json(mesh.periodic_pairs_lr),
            "top_bottom_pairs": _periodic_pairs_as_json(mesh.periodic_pairs_tb),
        },
        "summary": {
            "n_nodes": int(mesh.n_nodes),
            "n_elements": int(mesh.n_elements),
            "n_holes": int(len(geometry["hole_centers"])),
        },
    }

    with open(filename, "w") as f:
        _json.dump(payload, f, indent=4, default=_json_default)
    print(f"Mesh JSON exported to '{filename}'")
    return filename


def read_mesh_json_payload(filename: str) -> dict:
    """Read a ``*.mesh.json`` payload. Old text mesh files are not supported."""
    filename = str(filename)
    if not filename.endswith(".mesh.json"):
        raise ValueError(
            f"Unsupported mesh file '{filename}'. Mesh files must end with '.mesh.json'."
        )
    with open(filename, "r") as f:
        payload = _json.load(f)
    if payload.get("type") != "mesh":
        raise ValueError(f"File '{filename}' is not a mesh JSON file")
    return payload


def read_mesh_json(filename: str, include_metadata: bool = False):
    """Return ``nodes, elements`` from a ``*.mesh.json`` file."""
    payload = read_mesh_json_payload(filename)
    nodes = [
        (float(node["x"]), float(node["y"]), str(node.get("label", "")))
        for node in payload.get("nodes", [])
    ]
    elements = [[int(idx) for idx in elem] for elem in payload.get("elements", [])]
    if include_metadata:
        return nodes, elements, payload
    return nodes, elements


def mesh_data_from_json(filename: str) -> Tuple[MeshData, dict]:
    """Load a ``MeshData`` instance plus metadata from ``*.mesh.json``."""
    nodes_raw, elements_raw, payload = read_mesh_json(filename, include_metadata=True)
    nodes = np.array([(x, y) for x, y, _ in nodes_raw], dtype=float)
    labels = np.array([label for _, _, label in nodes_raw], dtype=object)
    etypes = np.array(payload.get("element_types") or [len(e) for e in elements_raw], dtype=int)
    max_npe = int(max(etypes)) if len(etypes) else 0
    if max_npe:
        elements = np.full((len(elements_raw), max_npe), -1, dtype=int)
        for i, elem in enumerate(elements_raw):
            elements[i, :len(elem)] = elem
    else:
        elements = np.empty((0, 0), dtype=int)

    periodic = payload.get("periodic", {})
    mesh = MeshData(
        nodes=nodes,
        elements=elements,
        boundary_nodes={
            name: np.asarray(indices, dtype=int)
            for name, indices in payload.get("boundary_nodes", {}).items()
        },
        hole_boundary_nodes=[
            np.asarray(indices, dtype=int)
            for indices in payload.get("hole_boundary_nodes", [])
        ],
        node_labels=labels,
        hole_classifications=[
            int(x) for x in payload.get("hole_classifications", [])
        ],
        element_types=etypes,
        periodic_pairs_lr=(
            np.asarray(periodic.get("left_right_pairs", []), dtype=int)
            if periodic.get("left_right_pairs") else None
        ),
        periodic_pairs_tb=(
            np.asarray(periodic.get("top_bottom_pairs", []), dtype=int)
            if periodic.get("top_bottom_pairs") else None
        ),
    )
    return mesh, payload


def _generator_from_mesh_payload(payload: dict):
    """Create a lightweight generator object from saved mesh geometry."""
    mesh_kind = payload.get("mesh_kind")
    geometry = payload.get("geometry", {})
    if mesh_kind == "random":
        gen = object.__new__(RandomMeshGenerator)
        gen.hole_radii = np.asarray(geometry.get("hole_radii", []), dtype=float)
        gen.min_hole_radius = float(np.min(gen.hole_radii)) if len(gen.hole_radii) else 0.0
        gen.max_hole_radius = float(np.max(gen.hole_radii)) if len(gen.hole_radii) else 0.0
        gen.min_distance = float(
            payload.get("parameters", {})
            .get("config", {})
            .get("min_distance_between_holes", 0.0)
        )
        gen.seed = payload.get("parameters", {}).get("config", {}).get("seed")
    else:
        gen = object.__new__(HexagonalMeshGenerator2)

    gen.domain_size = float(geometry.get("domain_size", 1.0))
    gen.porosity = float(geometry.get("porosity", 0.0))
    gen.center_domain = True
    gen.hole_centers = np.asarray(geometry.get("hole_centers", []), dtype=float)
    if gen.hole_centers.size == 0:
        gen.hole_centers = np.empty((0, 2), dtype=float)
    gen.n_holes_width = int(geometry.get("n_holes_width", max(int(np.sqrt(len(gen.hole_centers))), 1)))
    gen.horizontal_spacing = float(geometry.get("horizontal_spacing", gen.domain_size / max(gen.n_holes_width, 1)))
    gen.geometry = HexagonalPackingGeometry(
        horizontal_spacing=gen.horizontal_spacing,
        vertical_spacing=float(geometry.get("vertical_spacing", gen.horizontal_spacing * np.sqrt(3.0) / 2.0)),
        hole_radius=float(geometry.get("hole_radius", 0.0)),
        porosity=gen.porosity,
    )
    return gen


def _mesh_source_metadata(mesh_file: str) -> Tuple[dict, object]:
    payload = read_mesh_json_payload(mesh_file)
    return payload, _generator_from_mesh_payload(payload)


def _hole_radii_from_mesh_payload(payload: dict) -> np.ndarray:
    geometry = payload.get("geometry", {})
    radii = geometry.get("hole_radii")
    if radii:
        return np.asarray(radii, dtype=float)
    centers = geometry.get("hole_centers", [])
    return np.full(len(centers), float(geometry.get("hole_radius", 0.0)))


def _extended_centers_from_payload(
    payload: dict,
    generator,
    *,
    extra_rows_left: int = 0,
    extra_rows_right: int = 0,
    extra_rows_bottom: int = 0,
    extra_rows_top: int = 0,
    extend_random: bool = True,
) -> np.ndarray:
    if payload.get("mesh_kind") == "random":
        if extend_random and len(generator.hole_centers) > 0:
            return generator.compute_extended_hole_centers_random()
        return generator.hole_centers.copy()
    return generator.compute_extended_hole_centers(
        extra_left=extra_rows_left,
        extra_right=extra_rows_right,
        extra_bottom=extra_rows_bottom,
        extra_top=extra_rows_top,
    )


def write_graph_json(
    graph: GraphMeshData,
    filename: str,
    *,
    graph_type: str,
    created_by: str,
    parameters: dict,
    source_mesh_path: str = None,
    source_mesh_parameters: dict = None,
) -> str:
    """Write graph-like mesh data to JSON."""
    filename = _ensure_json_suffix(filename, graph_type)
    out_dir = os.path.dirname(filename)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    payload = {
        "format_version": MESH_FORMAT_VERSION,
        "type": graph_type,
        "created_by": created_by,
        "source_mesh_path": source_mesh_path,
        "source_mesh_parameters": source_mesh_parameters or {},
        "parameters": parameters,
        "nodes": [
            {"x": float(node[0]), "y": float(node[1]), "id": int(node_id)}
            for node, node_id in zip(graph.nodes, graph.node_ids)
        ],
        "bars": [
            {"start": int(pair[0]), "end": int(pair[1]), "bar_number": int(bar_number)}
            for pair, bar_number in zip(graph.bars, graph.bar_numbers)
        ],
        "summary": {
            "n_nodes": int(graph.n_nodes),
            "n_bars": int(graph.n_bars),
        },
    }
    with open(filename, "w") as f:
        _json.dump(payload, f, indent=4, default=_json_default)
    print(f"{graph_type} JSON exported to '{filename}'")
    return filename


def _plot_graph_json_from_source(
    mesh_file: str,
    graph_file: str,
    *,
    overlay_mesh: bool = True,
    boundary_only: bool = False,
    show_nodes_graph: bool = True,
) -> None:
    """Plot a graph/grid/gridhex JSON file after it is created."""
    from A001_functions.plot_mesh_functions import plot_graph_json_with_source

    plot_graph_json_with_source(
        graph_file,
        source_mesh_path=mesh_file,
        overlay_mesh=overlay_mesh,
        boundary_only=boundary_only,
        show_nodes_graph=show_nodes_graph,
        show=False,
    )
    plt.show()


def create_grid_json(
    mesh_file: str,
    output_path: str,
    *,
    grid_n: int,
    grid_m: int,
    grid_remove_edge_nodes: bool = True,
    show_plot: bool = False,
    overlay_mesh: bool = True,
    boundary_only: bool = False,
    show_nodes_graph: bool = True,
) -> GraphMeshData:
    """Create a Cartesian sampling grid from a ``*.mesh.json`` source file."""
    payload, _ = _mesh_source_metadata(mesh_file)
    geometry = payload["geometry"]
    grid = _generate_cartesian_grid_mesh_multi_radii(
        domain_size=float(geometry["domain_size"]),
        n_cols=grid_n,
        n_rows=grid_m,
        hole_centers=np.asarray(geometry.get("hole_centers", []), dtype=float),
        hole_radii=_hole_radii_from_mesh_payload(payload),
        remove_edge_nodes=grid_remove_edge_nodes,
    )
    graph_file = write_graph_json(
        grid,
        output_path,
        graph_type="grid",
        created_by="create_grid_json",
        source_mesh_path=mesh_file,
        source_mesh_parameters=payload.get("parameters", {}),
        parameters={
            "grid_n": grid_n,
            "grid_m": grid_m,
            "grid_remove_edge_nodes": grid_remove_edge_nodes,
        },
    )
    if show_plot:
        _plot_graph_json_from_source(
            mesh_file,
            graph_file,
            overlay_mesh=overlay_mesh,
            boundary_only=boundary_only,
            show_nodes_graph=show_nodes_graph,
        )
    return grid


def create_gridhex_json(
    mesh_file: str,
    output_path: str,
    *,
    hexagon_size: float,
    grid_remove_edge_nodes: bool = True,
    gridhex_pointy_top: bool = True,
    delete_gridhex_isolated_bars: bool = False,
    show_plot: bool = False,
    overlay_mesh: bool = True,
    boundary_only: bool = False,
    show_nodes_graph: bool = True,
) -> GraphMeshData:
    """Create a hexagonal sampling grid from a ``*.mesh.json`` source file."""
    payload, _ = _mesh_source_metadata(mesh_file)
    geometry = payload["geometry"]
    gridhex = _generate_hexagonal_gridhex_mesh_multi_radii(
        domain_size=float(geometry["domain_size"]),
        hexagon_size=hexagon_size,
        hole_centers=np.asarray(geometry.get("hole_centers", []), dtype=float),
        hole_radii=_hole_radii_from_mesh_payload(payload),
        pointy_top=gridhex_pointy_top,
        remove_edge_nodes=grid_remove_edge_nodes,
        delete_isolated_bars=delete_gridhex_isolated_bars,
    )
    graph_file = write_graph_json(
        gridhex,
        output_path,
        graph_type="gridhex",
        created_by="create_gridhex_json",
        source_mesh_path=mesh_file,
        source_mesh_parameters=payload.get("parameters", {}),
        parameters={
            "hexagon_size": hexagon_size,
            "grid_remove_edge_nodes": grid_remove_edge_nodes,
            "gridhex_pointy_top": gridhex_pointy_top,
            "delete_gridhex_isolated_bars": delete_gridhex_isolated_bars,
        },
    )
    if show_plot:
        _plot_graph_json_from_source(
            mesh_file,
            graph_file,
            overlay_mesh=overlay_mesh,
            boundary_only=boundary_only,
            show_nodes_graph=show_nodes_graph,
        )
    return gridhex


def create_graph_json(
    mesh_file: str,
    output_path: str,
    *,
    graph_characteristic_distance: float = 0.3,
    extra_rows_left: int = 0,
    extra_rows_right: int = 0,
    extra_rows_bottom: int = 0,
    extra_rows_top: int = 0,
    extend_random: bool = True,
    show_plot: bool = False,
    overlay_mesh: bool = True,
    boundary_only: bool = False,
    show_nodes_graph: bool = True,
) -> GraphMeshData:
    """Create a Voronoi graph JSON file from a ``*.mesh.json`` source file."""
    payload, generator = _mesh_source_metadata(mesh_file)
    centers = _extended_centers_from_payload(
        payload,
        generator,
        extra_rows_left=extra_rows_left,
        extra_rows_right=extra_rows_right,
        extra_rows_bottom=extra_rows_bottom,
        extra_rows_top=extra_rows_top,
        extend_random=extend_random,
    )
    graph = generator.generate_graph_mesh(graph_characteristic_distance, centers=centers)
    graph_file = write_graph_json(
        graph,
        output_path,
        graph_type="graph",
        created_by="create_graph_json",
        source_mesh_path=mesh_file,
        source_mesh_parameters=payload.get("parameters", {}),
        parameters={
            "graph_characteristic_distance": graph_characteristic_distance,
            "extra_rows_left": extra_rows_left,
            "extra_rows_right": extra_rows_right,
            "extra_rows_bottom": extra_rows_bottom,
            "extra_rows_top": extra_rows_top,
            "extend_random": extend_random,
        },
    )
    if show_plot:
        _plot_graph_json_from_source(
            mesh_file,
            graph_file,
            overlay_mesh=overlay_mesh,
            boundary_only=boundary_only,
            show_nodes_graph=show_nodes_graph,
        )
    return graph


def export_mesh_vtk_from_json(mesh_file: str, output_path: str = None) -> str:
    """Export the finite-element mesh JSON to legacy VTK for visualization."""
    mesh, payload = mesh_data_from_json(mesh_file)
    generator = _generator_from_mesh_payload(payload)
    vtk_path = output_path or (_mesh_base_path(mesh_file) + ".vtk")
    generator.export_mesh(mesh, vtk_path, format="vtk")
    print(f"Mesh VTK exported to '{vtk_path}'")
    return vtk_path


def export_voronoi_vtk_from_json(
    mesh_file: str,
    output_path: str = None,
    *,
    extra_rows_left: int = 0,
    extra_rows_right: int = 0,
    extra_rows_bottom: int = 0,
    extra_rows_top: int = 0,
    extend_random: bool = True,
) -> str:
    payload, generator = _mesh_source_metadata(mesh_file)
    centers = _extended_centers_from_payload(
        payload,
        generator,
        extra_rows_left=extra_rows_left,
        extra_rows_right=extra_rows_right,
        extra_rows_bottom=extra_rows_bottom,
        extra_rows_top=extra_rows_top,
        extend_random=extend_random,
    )
    vtk_path = output_path or (_mesh_base_path(mesh_file) + "_voronoi.vtk")
    generator.export_voronoi_vtk(vtk_path, centers=centers)
    print(f"Voronoi VTK exported to '{vtk_path}'")
    return vtk_path


def export_delaunay_vtk_from_json(
    mesh_file: str,
    output_path: str = None,
    *,
    extra_rows_left: int = 0,
    extra_rows_right: int = 0,
    extra_rows_bottom: int = 0,
    extra_rows_top: int = 0,
    extend_random: bool = True,
) -> str:
    payload, generator = _mesh_source_metadata(mesh_file)
    centers = _extended_centers_from_payload(
        payload,
        generator,
        extra_rows_left=extra_rows_left,
        extra_rows_right=extra_rows_right,
        extra_rows_bottom=extra_rows_bottom,
        extra_rows_top=extra_rows_top,
        extend_random=extend_random,
    )
    vtk_path = output_path or (_mesh_base_path(mesh_file) + "_delaunay.vtk")
    generator.export_delaunay_vtk(vtk_path, centers=centers)
    print(f"Delaunay VTK exported to '{vtk_path}'")
    return vtk_path


# Clearer aliases for callers that prefer "file" over "json".
create_grid_file = create_grid_json
create_gridhex_file = create_gridhex_json
create_graph_file = create_graph_json


def generate_cartesian_grid_mesh(
    domain_size: float,
    n_cols: int,
    n_rows: int,
    hole_centers: Optional[np.ndarray] = None,
    hole_radius: float = 0.0,
    remove_edge_nodes: bool = True,
) -> GraphMeshData:
    """
    Build a regular Cartesian grid using the same storage/layout as a graph.

    Nodes are ordered row-by-row starting from the top-left corner, moving
    left-to-right and then top-to-bottom. Each node is connected only to its
    immediate horizontal and vertical neighbours. Nodes strictly inside a hole
    are removed, together with any bars attached to them. Optionally, nodes on
    the domain boundary are also removed.
    """
    if n_cols is None or n_rows is None:
        raise ValueError("grid_n and grid_m must both be provided")
    if n_cols < 2 or n_rows < 2:
        raise ValueError("grid_n and grid_m must both be at least 2")

    x_coords = np.linspace(0.0, domain_size, n_cols)
    y_coords = np.linspace(domain_size, 0.0, n_rows)

    active_idx = -np.ones((n_rows, n_cols), dtype=int)
    nodes: List[List[float]] = []
    node_ids: List[int] = []

    centers = None
    if hole_centers is not None and len(hole_centers) > 0:
        centers = np.asarray(hole_centers, dtype=float)

    tol = max(domain_size, abs(hole_radius), 1.0) * 1e-12
    active_radius = max(float(hole_radius) - tol, 0.0)
    active_radius_sq = active_radius * active_radius

    for row, y in enumerate(y_coords):
        for col, x in enumerate(x_coords):
            if remove_edge_nodes and (
                row == 0 or row == n_rows - 1 or col == 0 or col == n_cols - 1
            ):
                continue

            if centers is not None and active_radius_sq > 0.0:
                dist_sq = np.sum((centers - np.array([x, y])) ** 2, axis=1)
                if np.any(dist_sq < active_radius_sq):
                    continue

            active_idx[row, col] = len(nodes)
            nodes.append([x, y])
            node_ids.append(0)

    bars: List[List[int]] = []
    bar_numbers: List[int] = []
    bar_number = 0

    for row in range(n_rows):
        for col in range(n_cols - 1):
            ni = active_idx[row, col]
            nf = active_idx[row, col + 1]
            if ni >= 0 and nf >= 0:
                bars.append([ni, nf])
                bar_numbers.append(bar_number)
                bar_number += 1

    for row in range(n_rows - 1):
        for col in range(n_cols):
            ni = active_idx[row, col]
            nf = active_idx[row + 1, col]
            if ni >= 0 and nf >= 0:
                bars.append([ni, nf])
                bar_numbers.append(bar_number)
                bar_number += 1

    return GraphMeshData(
        nodes=np.array(nodes, dtype=float) if nodes else np.empty((0, 2), dtype=float),
        node_ids=np.array(node_ids, dtype=int),
        bars=np.array(bars, dtype=int) if bars else np.empty((0, 2), dtype=int),
        bar_numbers=np.array(bar_numbers, dtype=int),
    )


@dataclass
class HexagonalPackingGeometry:
    """
    Geometry parameters for hexagonal packing of circular holes.

    In hexagonal packing, the unit cell is a rhombus containing one hole.

    The horizontal spacing a and vertical spacing b are related by:
    b = a * sqrt(3) / 2

    For a unit cell with one hole of radius r:
    Unit cell area = a * b = a^2 * sqrt(3) / 2
    Hole area = pi * r^2
    Porosity = pi * r^2 / (a^2 * sqrt(3) / 2) = 2 * pi * r^2 / (a^2 * sqrt(3))
    """
    horizontal_spacing: float  # a: distance between hole centers in a row
    vertical_spacing: float    # b: distance between rows
    hole_radius: float         # r: radius of circular holes
    porosity: float           # phi: area fraction of holes

    @classmethod
    def from_porosity_and_spacing(cls, porosity: float, horizontal_spacing: float) -> 'HexagonalPackingGeometry':
        """
        Create geometry from target porosity and horizontal spacing.

        Args:
            porosity: Target area fraction (0 < porosity < pi/(2*sqrt(3)) ≈ 0.9069)
            horizontal_spacing: Distance between hole centers in the same row

        Returns:
            HexagonalPackingGeometry instance
        """
        max_porosity = np.pi / (2 * np.sqrt(3))  # ~0.9069, when holes touch
        if porosity <= 0 or porosity >= max_porosity:
            raise ValueError(f"Porosity must be between 0 and {max_porosity:.4f} (got {porosity})")

        a = horizontal_spacing
        b = a * np.sqrt(3) / 2

        # From porosity = 2 * pi * r^2 / (a^2 * sqrt(3))
        r = a * np.sqrt(porosity * np.sqrt(3) / (2 * np.pi))

        return cls(
            horizontal_spacing=a,
            vertical_spacing=b,
            hole_radius=r,
            porosity=porosity
        )

    @classmethod
    def from_radius_and_spacing(cls, hole_radius: float, horizontal_spacing: float) -> 'HexagonalPackingGeometry':
        """Create geometry from hole radius and horizontal spacing."""
        a = horizontal_spacing
        b = a * np.sqrt(3) / 2
        r = hole_radius

        porosity = 2 * np.pi * r**2 / (a**2 * np.sqrt(3))

        max_porosity = np.pi / (2 * np.sqrt(3))
        if porosity >= max_porosity:
            raise ValueError(f"Hole radius too large: porosity {porosity:.4f} >= max {max_porosity:.4f}")

        return cls(
            horizontal_spacing=a,
            vertical_spacing=b,
            hole_radius=r,
            porosity=porosity
        )

    def get_minimum_ligament(self) -> float:
        """Return the minimum distance between hole edges."""
        return self.horizontal_spacing - 2 * self.hole_radius


class HexagonalMeshGenerator:
    """
    Generator for finite element meshes of square domains with hexagonally-packed holes.

    Creates boundary-conforming meshes suitable for bilinear quadrilateral (Q4) elements.
    The mesh nodes lie exactly on the circular hole boundaries.
    """

    def __init__(
        self,
        domain_size: float,
        n_holes_width: int,
        porosity: float,
        center_domain: bool = True
    ):
        """
        Initialize the mesh generator.

        Args:
            domain_size: Side length of the square domain
            n_holes_width: Number of holes across the width of the domain
            porosity: Target porosity (hole area / total area) for unit cell
            center_domain: If True, center the hole pattern in the domain
        """
        self.domain_size = domain_size
        self.n_holes_width = n_holes_width
        self.porosity = porosity
        self.center_domain = center_domain

        # Calculate horizontal spacing based on number of holes
        self.horizontal_spacing = domain_size / n_holes_width

        # Create geometry
        self.geometry = HexagonalPackingGeometry.from_porosity_and_spacing(
            porosity, self.horizontal_spacing
        )

        # Calculate hole centers (only fully interior holes)
        self.hole_centers = self._compute_hole_centers()

    def _compute_hole_centers(self) -> np.ndarray:
        """Compute the centers of all holes fully inside the domain."""
        a = self.geometry.horizontal_spacing
        b = self.geometry.vertical_spacing
        r = self.geometry.hole_radius
        L = self.domain_size

        n_rows = int(np.ceil(L / b)) + 2

        centers = []

        for row in range(-1, n_rows + 1):
            y = row * b
            x_offset = (a / 2) if (row % 2 == 1) else 0

            if self.center_domain:
                x_start = (L % a) / 2 + x_offset
            else:
                x_start = a / 2 + x_offset

            x = x_start
            while x < L + a:
                # Only include holes fully inside the domain
                if (x - r >= 0 and x + r <= L and y - r >= 0 and y + r <= L):
                    centers.append([x, y])
                x += a

        if len(centers) == 0:
            warnings.warn("No holes fit fully in the domain with current parameters")
            return np.array([]).reshape(0, 2)

        centers = np.array(centers)

        # Center vertically if requested
        if self.center_domain and len(centers) > 0:
            y_min = centers[:, 1].min()
            y_max = centers[:, 1].max()
            y_center_current = (y_max + y_min) / 2
            y_shift = L / 2 - y_center_current
            centers[:, 1] += y_shift

            # Re-filter after shifting
            mask = (
                (centers[:, 0] - r >= 0) & (centers[:, 0] + r <= L) &
                (centers[:, 1] - r >= 0) & (centers[:, 1] + r <= L)
            )
            centers = centers[mask]

        return centers

    def generate_mesh(
        self,
        elements_around_hole: int = 24,
        mesh_size_factor: float = 1.0,
        algorithm: str = 'auto'
    ) -> MeshData:
        """
        Generate a boundary-conforming quadrilateral mesh using Gmsh.

        Args:
            elements_around_hole: Approximate number of elements around each hole
            mesh_size_factor: Mesh density multiplier (smaller = finer mesh)
            algorithm: Meshing algorithm ('auto', 'delaunay', 'frontal')

        Returns:
            MeshData with conforming quad elements
        """
        if not GMSH_AVAILABLE:
            raise RuntimeError("Gmsh is required. Install with: pip install gmsh")

        # Calculate mesh size based on hole circumference
        circumference = 2 * np.pi * self.geometry.hole_radius
        mesh_size_hole = circumference / elements_around_hole * mesh_size_factor

        # Background mesh size (coarser away from holes)
        mesh_size_bg = min(
            self.geometry.get_minimum_ligament() / 3,
            self.horizontal_spacing / 4
        ) * mesh_size_factor

        # Initialize Gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)  # Suppress output
        gmsh.model.add("hexagonal_mesh")

        # Create domain boundary
        L = self.domain_size
        p1 = gmsh.model.geo.addPoint(0, 0, 0, mesh_size_bg)
        p2 = gmsh.model.geo.addPoint(L, 0, 0, mesh_size_bg)
        p3 = gmsh.model.geo.addPoint(L, L, 0, mesh_size_bg)
        p4 = gmsh.model.geo.addPoint(0, L, 0, mesh_size_bg)

        l_bottom = gmsh.model.geo.addLine(p1, p2)
        l_right = gmsh.model.geo.addLine(p2, p3)
        l_top = gmsh.model.geo.addLine(p3, p4)
        l_left = gmsh.model.geo.addLine(p4, p1)

        outer_loop = gmsh.model.geo.addCurveLoop([l_bottom, l_right, l_top, l_left])

        # Create holes
        hole_loops = []
        hole_curves = []

        for i, center in enumerate(self.hole_centers):
            cx, cy = center
            r = self.geometry.hole_radius

            # Create circle using 4 arcs for better mesh control
            pc = gmsh.model.geo.addPoint(cx, cy, 0, mesh_size_hole)
            pe = gmsh.model.geo.addPoint(cx + r, cy, 0, mesh_size_hole)
            pn = gmsh.model.geo.addPoint(cx, cy + r, 0, mesh_size_hole)
            pw = gmsh.model.geo.addPoint(cx - r, cy, 0, mesh_size_hole)
            ps = gmsh.model.geo.addPoint(cx, cy - r, 0, mesh_size_hole)

            arc1 = gmsh.model.geo.addCircleArc(pe, pc, pn)
            arc2 = gmsh.model.geo.addCircleArc(pn, pc, pw)
            arc3 = gmsh.model.geo.addCircleArc(pw, pc, ps)
            arc4 = gmsh.model.geo.addCircleArc(ps, pc, pe)

            hole_loop = gmsh.model.geo.addCurveLoop([arc1, arc2, arc3, arc4])
            hole_loops.append(hole_loop)
            hole_curves.append([arc1, arc2, arc3, arc4])

        # Create plane surface with holes
        surface = gmsh.model.geo.addPlaneSurface([outer_loop] + hole_loops)

        gmsh.model.geo.synchronize()

        # Add physical groups for boundary identification
        gmsh.model.addPhysicalGroup(1, [l_bottom], 1, "bottom")
        gmsh.model.addPhysicalGroup(1, [l_right], 2, "right")
        gmsh.model.addPhysicalGroup(1, [l_top], 3, "top")
        gmsh.model.addPhysicalGroup(1, [l_left], 4, "left")

        for i, curves in enumerate(hole_curves):
            gmsh.model.addPhysicalGroup(1, curves, 10 + i, f"hole_{i}")

        gmsh.model.addPhysicalGroup(2, [surface], 100, "domain")

        # Set meshing options for quads
        gmsh.option.setNumber("Mesh.RecombineAll", 1)
        gmsh.option.setNumber("Mesh.Algorithm", 8)  # Frontal-Delaunay for quads
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # Blossom
        gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 2)  # All-quads: split remaining tris
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)

        # Mesh size field for refinement near holes
        gmsh.model.mesh.field.add("Distance", 1)
        hole_curve_tags = [c for curves in hole_curves for c in curves]
        gmsh.model.mesh.field.setNumbers(1, "CurvesList", hole_curve_tags)
        gmsh.model.mesh.field.setNumber(1, "Sampling", 100)

        gmsh.model.mesh.field.add("Threshold", 2)
        gmsh.model.mesh.field.setNumber(2, "InField", 1)
        gmsh.model.mesh.field.setNumber(2, "SizeMin", mesh_size_hole)
        gmsh.model.mesh.field.setNumber(2, "SizeMax", mesh_size_bg)
        gmsh.model.mesh.field.setNumber(2, "DistMin", self.geometry.hole_radius * 0.5)
        gmsh.model.mesh.field.setNumber(2, "DistMax", self.geometry.get_minimum_ligament())

        gmsh.model.mesh.field.setAsBackgroundMesh(2)

        # Generate mesh
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.recombine()

        # Extract mesh data
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        nodes = np.array(node_coords).reshape(-1, 3)[:, :2]

        # Create tag to index mapping
        tag_to_idx = {tag: i for i, tag in enumerate(node_tags)}

        # Get quad elements (and verify no triangles remain)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(2)

        n_tri = 0
        elements = []
        for etype, etags, enodes in zip(elem_types, elem_tags, elem_node_tags):
            if etype == 2:  # 3-node triangle → degenerate quad (repeat last node)
                n_tri += len(etags)
                enodes = np.array(enodes).reshape(-1, 3)
                for tri_nodes in enodes:
                    elem = [tag_to_idx[t] for t in tri_nodes] + [tag_to_idx[tri_nodes[2]]]
                    elements.append(elem)
            elif etype == 3:  # 4-node quad
                enodes = np.array(enodes).reshape(-1, 4)
                for quad_nodes in enodes:
                    elem = [tag_to_idx[t] for t in quad_nodes]
                    elements.append(elem)
        if n_tri > 0:
            warnings.warn(
                f"Gmsh produced {n_tri} triangular element(s) that were "
                f"converted to degenerate quads (collapsed edge). Increase "
                f"elements_around_hole or decrease mesh_size_factor for a "
                f"fully-quad mesh."
            )

        elements = np.array(elements) if elements else np.array([]).reshape(0, 4)

        # Find nodes that are used in elements (remove isolated nodes like hole centers)
        if len(elements) > 0:
            used_node_indices = np.unique(elements.flatten())
        else:
            used_node_indices = np.array([], dtype=int)
        
        # Create mapping from old indices to new indices
        old_to_new = np.full(len(nodes), -1, dtype=int)
        old_to_new[used_node_indices] = np.arange(len(used_node_indices))
        
        # Filter nodes to only keep used ones
        nodes_filtered = nodes[used_node_indices]
        
        # Remap element connectivity
        elements_remapped = old_to_new[elements] if len(elements) > 0 else elements

        # Get boundary nodes by finding nodes on each edge geometrically (using filtered nodes)
        tol = L * 1e-6
        boundary_nodes = {
            'bottom': np.where(np.abs(nodes_filtered[:, 1]) < tol)[0],
            'right': np.where(np.abs(nodes_filtered[:, 0] - L) < tol)[0],
            'top': np.where(np.abs(nodes_filtered[:, 1] - L) < tol)[0],
            'left': np.where(np.abs(nodes_filtered[:, 0]) < tol)[0]
        }

        # Get hole boundary nodes by finding nodes on each circle (using filtered nodes)
        hole_boundary_nodes = []
        for center in self.hole_centers:
            distances = np.linalg.norm(nodes_filtered - center, axis=1)
            on_circle = np.where(np.abs(distances - self.geometry.hole_radius) < tol * 100)[0]
            hole_boundary_nodes.append(on_circle)

        gmsh.finalize()

        # All holes in the base generator are fully inside → B=5
        hole_classifications = [5] * len(self.hole_centers)

        return MeshData(
            nodes=nodes_filtered,
            elements=elements_remapped,
            boundary_nodes=boundary_nodes,
            hole_boundary_nodes=hole_boundary_nodes,
            hole_classifications=hole_classifications,
        )

    def generate_conforming_mesh(self, **kwargs) -> MeshData:
        """Alias for generate_mesh."""
        return self.generate_mesh(**kwargs)

    def plot_mesh(
        self,
        mesh: MeshData,
        show_nodes: bool = False,
        show_elements: bool = True,
        show_holes: bool = True,
        show_boundary: bool = True,
        highlight_hole_boundary: bool = True,
        figsize: Tuple[float, float] = (10, 10),
        title: str = None,
        element_color: str = 'lightblue',
        edge_color: str = 'blue'
    ) -> plt.Figure:
        """
        Visualize the generated mesh.
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Plot elements
        if show_elements and mesh.n_elements > 0:
            if mesh.element_types is not None:
                polygons = [
                    mesh.nodes[elem[:npe]]
                    for elem, npe in zip(mesh.elements, mesh.element_types)
                ]
            else:
                polygons = [mesh.nodes[elem] for elem in mesh.elements]
            collection = PolyCollection(
                polygons,
                facecolor=element_color,
                edgecolor=edge_color,
                linewidth=0.5,
                alpha=0.7
            )
            ax.add_collection(collection)

        # Plot nodes
        if show_nodes and mesh.n_nodes > 0:
            ax.scatter(mesh.nodes[:, 0], mesh.nodes[:, 1], s=3, c='black', zorder=5)

        # Highlight hole boundary nodes
        if highlight_hole_boundary:
            for indices in mesh.hole_boundary_nodes:
                if len(indices) > 0:
                    hole_pts = mesh.nodes[indices]
                    ax.scatter(hole_pts[:, 0], hole_pts[:, 1], s=8, c='red', zorder=6)

        # Plot reference circles
        if show_holes:
            for center in self.hole_centers:
                circle = Circle(center, self.geometry.hole_radius,
                              fill=True, facecolor='white',
                              edgecolor='darkred', linewidth=1.5, zorder=4)
                ax.add_patch(circle)

        # Plot domain boundary
        if show_boundary:
            rect = plt.Rectangle((0, 0), self.domain_size, self.domain_size,
                                fill=False, edgecolor='black', linewidth=2, zorder=3)
            ax.add_patch(rect)

        ax.set_xlim(-0.05 * self.domain_size, 1.05 * self.domain_size)
        ax.set_ylim(-0.05 * self.domain_size, 1.05 * self.domain_size)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')

        if title is None:
            title = (f'Conforming Mesh: {self.n_holes_width} holes/width, '
                    f'porosity={self.porosity:.3f}\n'
                    f'{mesh.n_nodes} nodes, {mesh.n_elements} quad elements')
        ax.set_title(title)

        plt.tight_layout()
        return fig

    def plot_node_labels(
        self,
        mesh: MeshData,
        show_elements: bool = True,
        show_holes: bool = True,
        figsize: Tuple[float, float] = (24, 10),
        title: str = None,
        node_size: int = 20,
        show_label: bool = True
    ) -> plt.Figure:
        """
        Visualize the mesh with nodes colored by their labels.

        Produces two side-by-side plots:
            Left  – nodes colored by the **A** digit (edge/corner position).
            Right – nodes colored by the **B** digit (hole classification).

        Label format: 1ABX..
            A: Position (0=interior, 1=left, 2=bottom, 3=right, 4=top, 5-8=corners)
            B: Hole classification
                0 = not part of any hole
                1 = hole cut by left edge
                2 = hole cut by bottom edge
                3 = hole cut by right edge
                4 = hole cut by top edge
                5 = complete hole
            X..: Hole number (if B != 0)

        Args:
            mesh: MeshData object with computed labels
            show_elements: Whether to show element edges
            show_holes: Whether to show hole circles
            figsize: Figure size (width applies to both subplots combined)
            title: Overall suptitle (auto-generated if None)
            node_size: Size of node markers
            show_label: Whether to show legends

        Returns:
            matplotlib Figure object
        """
        # Ensure labels are computed
        if mesh.node_labels is None:
            mesh.compute_node_labels()

        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=figsize)

        # ----- shared helpers -------------------------------------------------
        A_values = np.array([label[1] for label in mesh.node_labels])
        B_values = np.array([label[2] for label in mesh.node_labels])

        def _draw_elements(ax):
            if show_elements and mesh.n_elements > 0:
                if mesh.element_types is not None:
                    polygons = [
                        mesh.nodes[elem[:npe]]
                        for elem, npe in zip(mesh.elements, mesh.element_types)
                    ]
                else:
                    polygons = [mesh.nodes[elem] for elem in mesh.elements]
                collection = PolyCollection(
                    polygons,
                    facecolor='white',
                    edgecolor='lightgray',
                    linewidth=0.3,
                    alpha=0.5,
                )
                ax.add_collection(collection)

        def _draw_holes(ax):
            if show_holes:
                if hasattr(self, "hole_radii") and len(self.hole_radii) == len(self.hole_centers):
                    radii = self.hole_radii
                else:
                    radii = np.full(len(self.hole_centers), self.geometry.hole_radius)

                for center, radius in zip(self.hole_centers, radii):
                    circle = Circle(
                        center, radius,
                        fill=False, edgecolor='black', linewidth=1.0, zorder=4,
                    )
                    ax.add_patch(circle)

        def _draw_domain(ax):
            rect = plt.Rectangle(
                (0, 0), self.domain_size, self.domain_size,
                fill=False, edgecolor='black', linewidth=2, zorder=3,
            )
            ax.add_patch(rect)

        def _set_axes(ax, subtitle):
            ax.set_xlim(-0.05 * self.domain_size, 1.05 * self.domain_size)
            ax.set_ylim(-0.05 * self.domain_size, 1.05 * self.domain_size)
            ax.set_aspect('equal')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_title(subtitle)

        # =====================================================================
        # LEFT PLOT – colour by A (edge/corner position)
        # =====================================================================
        _draw_elements(ax_a)

        position_colors = {
            '0': 'gray',      # interior
            '1': 'blue',      # left edge
            '2': 'green',     # bottom edge
            '3': 'orange',    # right edge
            '4': 'red',       # top edge
            '5': 'purple',    # bottom-left corner
            '6': 'cyan',      # top-right corner
            '7': 'magenta',   # top-left corner
            '8': 'yellow',    # bottom-right corner
        }

        position_names = {
            '0': 'Interior (A=0)',
            '1': 'Left edge (A=1)',
            '2': 'Bottom edge (A=2)',
            '3': 'Right edge (A=3)',
            '4': 'Top edge (A=4)',
            '5': 'Bottom-left corner (A=5)',
            '6': 'Top-right corner (A=6)',
            '7': 'Top-left corner (A=7)',
            '8': 'Bottom-right corner (A=8)',
        }

        for A_val in ['0', '1', '2', '3', '4', '5', '6', '7', '8']:
            mask = A_values == A_val
            if not np.any(mask):
                continue
            pts = mesh.nodes[mask]
            color = position_colors[A_val]
            label_txt = position_names[A_val] if show_label else None
            ax_a.scatter(
                pts[:, 0], pts[:, 1],
                s=node_size, c=[color], marker='o',
                label=label_txt, zorder=5,
                edgecolors='black', linewidths=0.3,
            )

        _draw_holes(ax_a)
        _draw_domain(ax_a)
        _set_axes(ax_a, 'A digit – Edge / corner position')
        if show_label:
            ax_a.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)

        # =====================================================================
        # RIGHT PLOT – colour by B (hole classification)
        # =====================================================================
        _draw_elements(ax_b)

        hole_colors = {
            '0': 'gray',       # not part of any hole
            '1': 'blue',       # hole cut by left edge
            '2': 'green',      # hole cut by bottom edge
            '3': 'orange',     # hole cut by right edge
            '4': 'red',        # hole cut by top edge
            '5': 'purple',     # complete hole
        }

        hole_names = {
            '0': 'No hole (B=0)',
            '1': 'Hole cut left (B=1)',
            '2': 'Hole cut bottom (B=2)',
            '3': 'Hole cut right (B=3)',
            '4': 'Hole cut top (B=4)',
            '5': 'Complete hole (B=5)',
        }

        for B_val in ['0', '1', '2', '3', '4', '5']:
            mask = B_values == B_val
            if not np.any(mask):
                continue
            pts = mesh.nodes[mask]
            color = hole_colors[B_val]
            marker = 'o' if B_val == '0' else 's'
            label_txt = hole_names[B_val] if show_label else None
            ax_b.scatter(
                pts[:, 0], pts[:, 1],
                s=node_size if B_val == '0' else node_size * 1.5,
                c=[color], marker=marker,
                label=label_txt, zorder=5 if B_val == '0' else 6,
                edgecolors='black' if B_val == '0' else 'darkred',
                linewidths=0.3 if B_val == '0' else 0.8,
            )

        _draw_holes(ax_b)
        _draw_domain(ax_b)
        _set_axes(ax_b, 'B digit – Hole classification')
        if show_label:
            ax_b.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)

        # =====================================================================
        # Overall title
        # =====================================================================
        if title is None:
            title = (f'Node Labels (1ABX): {self.n_holes_width} holes/width, '
                     f'porosity={self.porosity:.3f} — '
                     f'{mesh.n_nodes} nodes, {len(self.hole_centers)} holes')
        fig.suptitle(title, fontsize=13, y=1.02)

        plt.tight_layout()
        return fig

    def compute_extended_hole_centers(
        self,
        extra_left: int = 0,
        extra_right: int = 0,
        extra_bottom: int = 0,
        extra_top: int = 0,
        hole_centers: np.ndarray = None,
        horizontal_spacing: float = None,
        vertical_spacing: float = None,
    ) -> np.ndarray:
        """
        Return *hole_centers* augmented with virtual rows / columns of
        holes outside the domain.

        The extra holes follow the same hexagonal packing pattern.
        They are used **only** for Voronoi / Delaunay construction so
        that the tessellation looks as though the pattern continues
        beyond the physical domain.

        Parameters
        ----------
        extra_left, extra_right : int
            Number of extra *columns* to add on each horizontal side.
        extra_bottom, extra_top : int
            Number of extra *rows* to add on each vertical side.
        hole_centers : np.ndarray or None
            The (already scaled) hole centres to extend.
            If *None*, ``self.hole_centers`` is used.
        horizontal_spacing, vertical_spacing : float or None
            Horizontal (``a``) and vertical (``b``) spacing to use for
            the extension grid.  If *None* the values from
            ``self.geometry`` are used.  Pass the **post-rescaling**
            spacings when edges have been added and the mesh rescaled.

        Returns
        -------
        np.ndarray, shape (N, 2)
            ``hole_centers`` followed by the virtual centres.
        """
        centers = hole_centers if hole_centers is not None else self.hole_centers
        if not (extra_left or extra_right or extra_bottom or extra_top):
            return centers.copy()

        a = horizontal_spacing if horizontal_spacing is not None else self.geometry.horizontal_spacing
        b = vertical_spacing if vertical_spacing is not None else self.geometry.vertical_spacing

        # ------------------------------------------------------------------
        # 1. Cluster the (already-rescaled) centres into horizontal rows
        # ------------------------------------------------------------------
        tol_y = b * 0.25
        sorted_idx = np.argsort(centers[:, 1])

        rows = []           # list of (mean_y, np.array of sorted x values)
        clust_ys: list = []
        clust_xs: list = []

        for idx in sorted_idx:
            cy, cx = centers[idx, 1], centers[idx, 0]
            if clust_ys and cy - np.mean(clust_ys) > tol_y:
                rows.append((float(np.mean(clust_ys)),
                             np.sort(np.array(clust_xs))))
                clust_ys, clust_xs = [], []
            clust_ys.append(cy)
            clust_xs.append(cx)
        if clust_ys:
            rows.append((float(np.mean(clust_ys)),
                         np.sort(np.array(clust_xs))))

        n_rows = len(rows)
        if n_rows == 0:
            return centers.copy()

        row_ys = np.array([r[0] for r in rows])

        # ------------------------------------------------------------------
        # 2. Classify rows into two alternating offset types (A / B) via
        #    the modular x-residue of the leftmost hole in each row.
        #    In a hexagonal packing the two types differ by ~a/2.
        # ------------------------------------------------------------------
        row_x_residues = np.array([float(r[1][0] % a) for r in rows])
        ref_res = row_x_residues[0]

        row_types = np.zeros(n_rows, dtype=int)
        for i in range(n_rows):
            diff = (row_x_residues[i] - ref_res) % a
            if diff > a / 2:
                diff -= a
            row_types[i] = 0 if abs(diff) < a / 4 else 1

        # Median x-residue for each type
        t0_mask = row_types == 0
        t1_mask = row_types == 1
        xb_0 = float(np.median(row_x_residues[t0_mask])) if t0_mask.any() else ref_res
        xb_1 = float(np.median(row_x_residues[t1_mask])) if t1_mask.any() else (ref_res + a / 2) % a

        x_base = {0: xb_0, 1: xb_1}

        # ------------------------------------------------------------------
        # 3. Build the list of virtual centres
        # ------------------------------------------------------------------
        virtual: list = []

        # 3a. Extend every existing row by extra_left / extra_right columns
        for _row_y, row_xs in rows:
            for j in range(1, extra_left + 1):
                virtual.append([row_xs[0] - j * a, _row_y])
            for j in range(1, extra_right + 1):
                virtual.append([row_xs[-1] + j * a, _row_y])

        # x-range for entirely new rows (bottom / top padding)
        x_min_existing = float(centers[:, 0].min())
        x_max_existing = float(centers[:, 0].max())
        x_left_bound  = x_min_existing - extra_left * a - a / 2
        x_right_bound = x_max_existing + extra_right * a + a / 2

        def _fill_row(xb_type: float, y_val: float) -> list:
            """Generate all x positions for a row of given type."""
            n_start = int(np.floor((x_left_bound - xb_type) / a))
            pts: list = []
            x = xb_type + n_start * a
            while x < x_right_bound:
                pts.append([x, y_val])
                x += a
            return pts

        # 3b. Extra rows below the bottom-most existing row
        bottom_type = row_types[0]
        for i in range(1, extra_bottom + 1):
            new_y = row_ys[0] - i * b
            new_type = bottom_type if (i % 2 == 0) else (1 - bottom_type)
            virtual.extend(_fill_row(x_base[new_type], new_y))

        # 3c. Extra rows above the top-most existing row
        top_type = row_types[-1]
        for i in range(1, extra_top + 1):
            new_y = row_ys[-1] + i * b
            new_type = top_type if (i % 2 == 0) else (1 - top_type)
            virtual.extend(_fill_row(x_base[new_type], new_y))

        if not virtual:
            return centers.copy()

        return np.vstack([centers, np.array(virtual)])

    def generate_voronoi_mesh(self, clip_to_domain: bool = True,
                              centers: np.ndarray = None) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Generate the Voronoi diagram (dual of Delaunay triangulation) of hole centers.

        The Voronoi diagram is the wireframe dual of the Delaunay triangulation.
        Each Voronoi cell contains exactly one hole center.

        Args:
            clip_to_domain: If True, clip Voronoi edges to domain boundary
            centers: Optional override for hole centers (e.g. extended set
                     from :meth:`compute_extended_hole_centers`).  If *None*,
                     ``self.hole_centers`` is used.

        Returns:
            Tuple of (vertices, edges) where:
                - vertices: (n_vertices, 2) array of Voronoi vertex coordinates
                - edges: list of (2,) arrays containing vertex indices for each edge
        """
        pts = centers if centers is not None else self.hole_centers
        if len(pts) < 3:
            raise ValueError("Need at least 3 hole centers for Voronoi diagram")

        # Compute Voronoi diagram
        vor = Voronoi(pts)

        vertices = vor.vertices
        edges = []

        L = self.domain_size

        # Extract finite edges
        for ridge_vertices in vor.ridge_vertices:
            if -1 not in ridge_vertices:
                # Finite edge
                v0, v1 = ridge_vertices
                p0, p1 = vertices[v0], vertices[v1]

                if clip_to_domain:
                    # Clip edge to domain
                    clipped = self._clip_line_to_domain(p0, p1, L)
                    if clipped is not None:
                        edges.append(clipped)
                else:
                    edges.append(np.array([p0, p1]))

        return vertices, edges

    def _clip_line_to_domain(
        self,
        p0: np.ndarray,
        p1: np.ndarray,
        L: float
    ) -> Optional[np.ndarray]:
        """
        Clip a line segment to the domain [0, L] x [0, L] using Cohen-Sutherland algorithm.

        Returns:
            Clipped line segment as (2, 2) array, or None if completely outside
        """
        def compute_outcode(x, y):
            code = 0
            if x < 0: code |= 1      # left
            elif x > L: code |= 2    # right
            if y < 0: code |= 4      # bottom
            elif y > L: code |= 8    # top
            return code

        x0, y0 = p0
        x1, y1 = p1

        outcode0 = compute_outcode(x0, y0)
        outcode1 = compute_outcode(x1, y1)

        while True:
            if not (outcode0 | outcode1):
                # Both points inside
                return np.array([[x0, y0], [x1, y1]])
            elif outcode0 & outcode1:
                # Both points in same outside region
                return None
            else:
                # Line crosses boundary
                outcode_out = outcode0 if outcode0 else outcode1

                if outcode_out & 8:      # top
                    x = x0 + (x1 - x0) * (L - y0) / (y1 - y0) if y1 != y0 else x0
                    y = L
                elif outcode_out & 4:    # bottom
                    x = x0 + (x1 - x0) * (0 - y0) / (y1 - y0) if y1 != y0 else x0
                    y = 0
                elif outcode_out & 2:    # right
                    y = y0 + (y1 - y0) * (L - x0) / (x1 - x0) if x1 != x0 else y0
                    x = L
                elif outcode_out & 1:    # left
                    y = y0 + (y1 - y0) * (0 - x0) / (x1 - x0) if x1 != x0 else y0
                    x = 0

                if outcode_out == outcode0:
                    x0, y0 = x, y
                    outcode0 = compute_outcode(x0, y0)
                else:
                    x1, y1 = x, y
                    outcode1 = compute_outcode(x1, y1)

    def plot_voronoi_dual(
        self,
        show_delaunay: bool = True,
        show_voronoi: bool = True,
        show_holes: bool = True,
        show_centers: bool = True,
        figsize: Tuple[float, float] = (10, 10),
        title: str = None,
        centers: np.ndarray = None,
    ) -> plt.Figure:
        """
        Plot the Delaunay triangulation and its dual Voronoi diagram.

        Args:
            show_delaunay: Show Delaunay triangulation edges
            show_voronoi: Show Voronoi diagram (the dual wireframe)
            show_holes: Show hole circles
            show_centers: Show hole center points
            figsize: Figure size
            title: Plot title
            centers: Optional override for hole centers (e.g. extended).
                     If *None*, ``self.hole_centers`` is used.

        Returns:
            matplotlib Figure object
        """
        pts = centers if centers is not None else self.hole_centers
        if len(pts) < 3:
            raise ValueError("Need at least 3 hole centers for triangulation")

        fig, ax = plt.subplots(figsize=figsize)
        L = self.domain_size

        # Compute Delaunay triangulation
        tri = Delaunay(pts)

        # Plot Delaunay triangulation
        if show_delaunay:
            for simplex in tri.simplices:
                tri_pts = pts[simplex]
                # Close the triangle
                tri_pts = np.vstack([tri_pts, tri_pts[0]])
                ax.plot(tri_pts[:, 0], tri_pts[:, 1], 'b-', linewidth=0.8, alpha=0.6)

        # Plot Voronoi diagram (dual)
        if show_voronoi:
            _, edges = self.generate_voronoi_mesh(clip_to_domain=True, centers=pts)
            for edge in edges:
                ax.plot(edge[:, 0], edge[:, 1], 'r-', linewidth=1.5)

        # Plot holes
        if show_holes:
            for center in self.hole_centers:
                circle = Circle(center, self.geometry.hole_radius,
                              fill=True, facecolor='lightgray',
                              edgecolor='black', linewidth=1.0, zorder=4)
                ax.add_patch(circle)

        # Plot hole centers
        if show_centers:
            ax.scatter(pts[:, 0], pts[:, 1],
                      s=30, c='black', zorder=5, label='Hole centers')

        # Plot domain boundary
        rect = plt.Rectangle((0, 0), L, L,
                            fill=False, edgecolor='black', linewidth=2, zorder=3)
        ax.add_patch(rect)

        ax.set_xlim(-0.05 * L, 1.05 * L)
        ax.set_ylim(-0.05 * L, 1.05 * L)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')

        if title is None:
            title = (f'Delaunay Triangulation & Voronoi Dual\n'
                    f'{len(pts)} hole centers')
        ax.set_title(title)

        # Add legend
        legend_elements = []
        if show_delaunay:
            legend_elements.append(plt.Line2D([0], [0], color='blue', linewidth=0.8, label='Delaunay'))
        if show_voronoi:
            legend_elements.append(plt.Line2D([0], [0], color='red', linewidth=1.5, label='Voronoi (dual)'))
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()
        return fig

    def export_mesh(
        self,
        mesh: MeshData,
        filename: str,
        format: str = 'vtk'
    ) -> None:
        """
        Export mesh to file.

        Args:
            mesh: MeshData to export
            filename: Output filename
            format: Output format ('vtk', 'inp', or 'txt')
        """
        if format == 'vtk':
            self._export_vtk(mesh, filename)
        elif format == 'inp':
            self._export_abaqus(mesh, filename)
        elif format == 'txt':
            self._export_txt(mesh, filename)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _export_vtk(self, mesh: MeshData, filename: str) -> None:
        """Export mesh in VTK legacy format with node labels as point data."""
        # Ensure labels are computed
        if mesh.node_labels is None:
            mesh.compute_node_labels()

        # Determine per-element node counts
        if mesh.element_types is not None:
            etypes = mesh.element_types
        else:
            etypes = np.full(mesh.n_elements, 4, dtype=int)

        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Hexagonal mesh with holes - boundary conforming\n")
            f.write("ASCII\n")
            f.write("DATASET UNSTRUCTURED_GRID\n")

            f.write(f"POINTS {mesh.n_nodes} float\n")
            for node in mesh.nodes:
                f.write(f"{node[0]} {node[1]} 0.0\n")

            # Each cell line has (npe + 1) entries: count followed by indices
            n_entries = int(np.sum(etypes + 1))
            f.write(f"CELLS {mesh.n_elements} {n_entries}\n")
            for elem, npe in zip(mesh.elements, etypes):
                idx_str = " ".join(str(elem[k]) for k in range(npe))
                f.write(f"{npe} {idx_str}\n")

            f.write(f"CELL_TYPES {mesh.n_elements}\n")
            for npe in etypes:
                # VTK_TRIANGLE = 5, VTK_QUAD = 9
                f.write(f"{5 if npe == 3 else 9}\n")

            # Add node labels as point data (as integers for VTK compatibility)
            f.write(f"\nPOINT_DATA {mesh.n_nodes}\n")
            f.write("SCALARS node_label int 1\n")
            f.write("LOOKUP_TABLE default\n")
            for label in mesh.node_labels:
                # Convert string label to integer for VTK
                f.write(f"{int(label)}\n")

    def _export_abaqus(self, mesh: MeshData, filename: str) -> None:
        """Export mesh in Abaqus INP format."""
        # Determine per-element node counts
        if mesh.element_types is not None:
            etypes = mesh.element_types
        else:
            etypes = np.full(mesh.n_elements, 4, dtype=int)

        has_tri = np.any(etypes == 3)
        has_quad = np.any(etypes == 4)

        with open(filename, 'w') as f:
            f.write("*HEADING\n")
            f.write("Hexagonal mesh with holes - boundary conforming\n")

            f.write("*NODE\n")
            for i, node in enumerate(mesh.nodes, start=1):
                f.write(f"{i}, {node[0]}, {node[1]}, 0.0\n")

            # Write quad elements
            if has_quad:
                quad_mask = etypes == 4
                f.write("*ELEMENT, TYPE=CPS4, ELSET=QUADS\n")
                for i, (elem, npe) in enumerate(
                    zip(mesh.elements, etypes), start=1
                ):
                    if npe == 4:
                        f.write(
                            f"{i}, {elem[0]+1}, {elem[1]+1}, "
                            f"{elem[2]+1}, {elem[3]+1}\n"
                        )

            # Write tri elements
            if has_tri:
                f.write("*ELEMENT, TYPE=CPS3, ELSET=TRIS\n")
                for i, (elem, npe) in enumerate(
                    zip(mesh.elements, etypes), start=1
                ):
                    if npe == 3:
                        f.write(
                            f"{i}, {elem[0]+1}, {elem[1]+1}, {elem[2]+1}\n"
                        )

            # Combined element set
            if has_tri and has_quad:
                f.write("*ELSET, ELSET=ALL\n")
                f.write("QUADS, TRIS\n")
            elif has_quad:
                f.write("*ELSET, ELSET=ALL\n")
                f.write("QUADS,\n")
            elif has_tri:
                f.write("*ELSET, ELSET=ALL\n")
                f.write("TRIS,\n")

            for name, indices in mesh.boundary_nodes.items():
                if len(indices) > 0:
                    f.write(f"*NSET, NSET={name.upper()}\n")
                    for j, idx in enumerate(indices):
                        if j > 0 and j % 10 == 0:
                            f.write("\n")
                        f.write(f"{idx+1}, ")
                    f.write("\n")

            for i, indices in enumerate(mesh.hole_boundary_nodes):
                if len(indices) > 0:
                    f.write(f"*NSET, NSET=HOLE{i+1}\n")
                    for j, idx in enumerate(indices):
                        if j > 0 and j % 10 == 0:
                            f.write("\n")
                        f.write(f"{idx+1}, ")
                    f.write("\n")

    def _export_txt(self, mesh: MeshData, filename: str) -> None:
        """Export mesh in simple text format."""
        # Determine per-element node counts
        if mesh.element_types is not None:
            etypes = mesh.element_types
        else:
            etypes = np.full(mesh.n_elements, 4, dtype=int)

        with open(filename, 'w') as f:
            f.write(f"# Hexagonal mesh with holes - boundary conforming\n")
            f.write(f"# Nodes: {mesh.n_nodes}\n")
            f.write(f"# Elements: {mesh.n_elements}\n")
            f.write(f"# Porosity: {self.porosity}\n")
            f.write(f"# Holes in width: {self.n_holes_width}\n")
            f.write(f"# Hole radius: {self.geometry.hole_radius}\n\n")

            f.write("# NODES (id, x, y)\n")
            for i, node in enumerate(mesh.nodes):
                f.write(f"{i} {node[0]} {node[1]}\n")

            f.write("\n# ELEMENTS (id, n1, n2, n3 [, n4])\n")
            for i, (elem, npe) in enumerate(zip(mesh.elements, etypes)):
                idx_str = " ".join(str(elem[k]) for k in range(npe))
                f.write(f"{i} {idx_str}\n")

    def export_voronoi_vtk(self, filename: str,
                           centers: np.ndarray = None) -> None:
        """
        Export the Voronoi dual mesh (wireframe) to VTK format for ParaView.

        The Voronoi diagram is exported as line segments (edges).

        Args:
            filename: Output VTK filename
            centers: Optional override for hole centers (e.g. extended).
        """
        _, edges = self.generate_voronoi_mesh(clip_to_domain=True, centers=centers)

        if len(edges) == 0:
            raise ValueError("No Voronoi edges to export")

        # Collect unique vertices and build edge connectivity
        vertices = []
        vertex_map = {}
        edge_connectivity = []

        for edge in edges:
            edge_indices = []
            for pt in edge:
                pt_tuple = (round(pt[0], 10), round(pt[1], 10))
                if pt_tuple not in vertex_map:
                    vertex_map[pt_tuple] = len(vertices)
                    vertices.append(pt)
                edge_indices.append(vertex_map[pt_tuple])
            edge_connectivity.append(edge_indices)

        vertices = np.array(vertices)
        n_vertices = len(vertices)
        n_edges = len(edge_connectivity)

        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Voronoi dual of Delaunay triangulation of hole centers\n")
            f.write("ASCII\n")
            f.write("DATASET UNSTRUCTURED_GRID\n")

            # Write vertices
            f.write(f"POINTS {n_vertices} float\n")
            for v in vertices:
                f.write(f"{v[0]} {v[1]} 0.0\n")

            # Write edges as VTK_LINE cells
            n_entries = n_edges * 3  # 2 vertices + count per edge
            f.write(f"CELLS {n_edges} {n_entries}\n")
            for e in edge_connectivity:
                f.write(f"2 {e[0]} {e[1]}\n")

            # Cell types: 3 = VTK_LINE
            f.write(f"CELL_TYPES {n_edges}\n")
            for _ in range(n_edges):
                f.write("3\n")

        print(f"Voronoi mesh exported: {n_vertices} vertices, {n_edges} edges")

    def generate_graph_mesh(
        self,
        characteristic_distance: float,
        centers: np.ndarray = None,
    ) -> 'GraphMeshData':
        """
        Build a subdivided graph from the clipped Voronoi dual.

        Each Voronoi edge is called a *bar* and each Voronoi vertex a *node*.
        Original nodes receive ``node_id = 1``.  Every bar is split into
        equal-length segments whose length is as close as possible to
        *characteristic_distance*.  Interior subdivision nodes receive
        ``node_id = 2``.  All sub-bars that come from the same original bar
        share the same ``bar_number``.

        Args:
            characteristic_distance: Target length for sub-bar segments.
            centers: Optional override for hole centers (e.g. extended).

        Returns:
            A :class:`GraphMeshData` instance.
        """
        _, raw_edges = self.generate_voronoi_mesh(clip_to_domain=True, centers=centers)
        if len(raw_edges) == 0:
            raise ValueError("No Voronoi edges to build graph from")

        # --- deduplicate original vertices -----------------------------------
        orig_coords: List[np.ndarray] = []
        vertex_map: Dict[Tuple[float, float], int] = {}
        edge_connectivity: List[List[int]] = []

        for edge in raw_edges:
            idx_pair: List[int] = []
            for pt in edge:
                key = (round(pt[0], 10), round(pt[1], 10))
                if key not in vertex_map:
                    vertex_map[key] = len(orig_coords)
                    orig_coords.append(pt)
                idx_pair.append(vertex_map[key])
            edge_connectivity.append(idx_pair)

        # --- initialise output lists with original nodes (id=1) --------------
        all_nodes = [np.array(c) for c in orig_coords]
        all_ids = [1] * len(all_nodes)

        all_bars: List[List[int]] = []
        all_bar_numbers: List[int] = []

        # --- subdivide each bar ----------------------------------------------
        for bar_number, (ni, nf) in enumerate(edge_connectivity):
            p0 = np.array(all_nodes[ni])
            p1 = np.array(all_nodes[nf])
            bar_len = np.linalg.norm(p1 - p0)

            n_segments = max(1, round(bar_len / characteristic_distance))

            if n_segments == 1:
                all_bars.append([ni, nf])
                all_bar_numbers.append(bar_number)
            else:
                prev_idx = ni
                for k in range(1, n_segments):
                    t = k / n_segments
                    new_pt = p0 + t * (p1 - p0)
                    new_idx = len(all_nodes)
                    all_nodes.append(new_pt)
                    all_ids.append(2)  # subdivision node
                    all_bars.append([prev_idx, new_idx])
                    all_bar_numbers.append(bar_number)
                    prev_idx = new_idx
                # last segment to the final original node
                all_bars.append([prev_idx, nf])
                all_bar_numbers.append(bar_number)

        return GraphMeshData(
            nodes=np.array(all_nodes),
            node_ids=np.array(all_ids, dtype=int),
            bars=np.array(all_bars, dtype=int),
            bar_numbers=np.array(all_bar_numbers, dtype=int),
        )

    def export_delaunay_vtk(self, filename: str,
                            centers: np.ndarray = None) -> None:
        """
        Export the Delaunay triangulation of hole centers to VTK format for ParaView.

        Args:
            filename: Output VTK filename
            centers: Optional override for hole centers (e.g. extended).
        """
        pts = centers if centers is not None else self.hole_centers
        if len(pts) < 3:
            raise ValueError("Need at least 3 hole centers for Delaunay triangulation")

        tri = Delaunay(pts)
        vertices = pts
        triangles = tri.simplices

        n_vertices = len(vertices)
        n_triangles = len(triangles)

        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Delaunay triangulation of hole centers\n")
            f.write("ASCII\n")
            f.write("DATASET UNSTRUCTURED_GRID\n")

            # Write vertices (hole centers)
            f.write(f"POINTS {n_vertices} float\n")
            for v in vertices:
                f.write(f"{v[0]} {v[1]} 0.0\n")

            # Write triangles
            n_entries = n_triangles * 4  # 3 vertices + count per triangle
            f.write(f"CELLS {n_triangles} {n_entries}\n")
            for t in triangles:
                f.write(f"3 {t[0]} {t[1]} {t[2]}\n")

            # Cell types: 5 = VTK_TRIANGLE
            f.write(f"CELL_TYPES {n_triangles}\n")
            for _ in range(n_triangles):
                f.write("5\n")

            # Add hole index as point data
            f.write(f"\nPOINT_DATA {n_vertices}\n")
            f.write("SCALARS hole_index int 1\n")
            f.write("LOOKUP_TABLE default\n")
            for i in range(n_vertices):
                f.write(f"{i}\n")

        print(f"Delaunay mesh exported: {n_vertices} vertices, {n_triangles} triangles")

    def get_mesh_quality_metrics(self, mesh: MeshData) -> dict:
        """
        Compute mesh quality metrics.

        Returns:
            Dictionary with quality metrics including aspect ratios and Jacobians.
        """
        if mesh.n_elements == 0:
            return {
                'aspect_ratio_min': 0,
                'aspect_ratio_max': 0,
                'aspect_ratio_mean': 0,
                'jacobian_min': 0,
                'jacobian_max': 0,
                'negative_jacobians': 0,
                'n_elements': 0,
                'n_nodes': mesh.n_nodes
            }

        aspect_ratios = []
        jacobians = []

        # Determine per-element node counts
        if mesh.element_types is not None:
            etypes = mesh.element_types
        else:
            etypes = np.full(mesh.n_elements, 4, dtype=int)

        for elem, npe in zip(mesh.elements, etypes):
            pts = mesh.nodes[elem[:npe]]

            if npe == 3:
                # Triangle: 3 edges
                edges = np.array([
                    pts[1] - pts[0],
                    pts[2] - pts[1],
                    pts[0] - pts[2],
                ])
            else:
                # Quad: 4 edges
                edges = np.array([
                    pts[1] - pts[0],
                    pts[2] - pts[1],
                    pts[3] - pts[2],
                    pts[0] - pts[3],
                ])
            edge_lengths = np.linalg.norm(edges, axis=1)

            if edge_lengths.min() > 1e-12:
                aspect_ratio = edge_lengths.max() / edge_lengths.min()
            else:
                aspect_ratio = np.inf
            aspect_ratios.append(aspect_ratio)

            if npe == 3:
                # Jacobian for triangle: cross product of two edges
                v1 = pts[1] - pts[0]
                v2 = pts[2] - pts[0]
                jac = v1[0] * v2[1] - v1[1] * v2[0]
            else:
                # Jacobian at quad element center
                dx_dxi = (pts[1] - pts[0] + pts[2] - pts[3]) / 2
                dx_deta = (pts[3] - pts[0] + pts[2] - pts[1]) / 2
                jac = dx_dxi[0] * dx_deta[1] - dx_dxi[1] * dx_deta[0]
            jacobians.append(jac)

        aspect_ratios = np.array(aspect_ratios)
        jacobians = np.array(jacobians)

        return {
            'aspect_ratio_min': float(aspect_ratios.min()),
            'aspect_ratio_max': float(aspect_ratios.max()),
            'aspect_ratio_mean': float(aspect_ratios.mean()),
            'jacobian_min': float(jacobians.min()),
            'jacobian_max': float(jacobians.max()),
            'negative_jacobians': int(np.sum(jacobians < 0)),
            'n_elements': mesh.n_elements,
            'n_nodes': mesh.n_nodes
        }


# ---------------------------------------------------------------------------
# Graph-mesh I/O and plotting (standalone functions)
# ---------------------------------------------------------------------------

def export_graph_mesh(graph: GraphMeshData, filename: str) -> None:
    """Write graph data as ``*.graph.json``."""
    write_graph_json(
        graph,
        filename,
        graph_type="graph",
        created_by="export_graph_mesh",
        parameters={},
    )


def export_grid_mesh(grid: GraphMeshData, filename: str) -> None:
    """Write Cartesian grid data as ``*.grid.json``."""
    write_graph_json(
        grid,
        filename,
        graph_type="grid",
        created_by="export_grid_mesh",
        parameters={},
    )


def read_graph_mesh(filename: str) -> GraphMeshData:
    """
    Read a graph-like JSON file.

    Args:
        filename: Path to a ``*.graph.json``, ``*.grid.json``, or
            ``*.gridhex.json`` file.

    Returns:
        A :class:`GraphMeshData` instance.
    """
    filename = str(filename)
    if not filename.endswith(".json"):
        raise ValueError(
            f"Unsupported graph file '{filename}'. Graph files must be JSON."
        )
    with open(filename, "r") as f:
        payload = _json.load(f)
    if payload.get("type") not in ("graph", "grid", "gridhex"):
        raise ValueError(f"File '{filename}' is not a graph/grid JSON file")

    node_records = payload.get("nodes", [])
    bar_records = payload.get("bars", [])
    nodes = np.array(
        [[float(node["x"]), float(node["y"])] for node in node_records],
        dtype=float,
    ) if node_records else np.empty((0, 2), dtype=float)
    node_ids = np.array(
        [int(node.get("id", 0)) for node in node_records],
        dtype=int,
    )
    bars = np.array(
        [[int(bar["start"]), int(bar["end"])] for bar in bar_records],
        dtype=int,
    ) if bar_records else np.empty((0, 2), dtype=int)
    bar_numbers = np.array(
        [int(bar.get("bar_number", i)) for i, bar in enumerate(bar_records)],
        dtype=int,
    )

    return GraphMeshData(
        nodes=nodes,
        node_ids=node_ids,
        bars=bars,
        bar_numbers=bar_numbers,
    )


def plot_graph_mesh(
    graph: GraphMeshData,
    figsize: Tuple[float, float] = (10, 10),
    title: str = None,
    show: bool = True,
) -> plt.Figure:
    """
    Plot a :class:`GraphMeshData`.

    * **Bars** are coloured by their ``bar_number`` (each original Voronoi
      edge gets a distinct colour).
    * **Nodes** with ``node_id == 1`` (original) are drawn in **black**;
      nodes with ``node_id == 2`` (subdivision) are drawn in **red**.

    Args:
        graph: The graph mesh to plot.
        figsize: Figure size.
        title: Optional title; a default is generated if *None*.
        show: If *True*, call ``plt.show()``.

    Returns:
        The matplotlib *Figure*.
    """
    fig, ax = plt.subplots(figsize=figsize)

    unique_bars = np.unique(graph.bar_numbers)
    cmap = plt.cm.get_cmap('tab20', len(unique_bars))
    bar_color_map = {bn: cmap(i) for i, bn in enumerate(unique_bars)}

    # Draw bars coloured by bar_number
    for (ni, nf), bn in zip(graph.bars, graph.bar_numbers):
        p0 = graph.nodes[ni]
        p1 = graph.nodes[nf]
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=bar_color_map[bn], linewidth=1.2, zorder=2)

    # Draw nodes
    orig_mask = graph.node_ids == 1
    sub_mask = graph.node_ids == 2

    if np.any(orig_mask):
        pts = graph.nodes[orig_mask]
        ax.scatter(pts[:, 0], pts[:, 1], s=30, c='black', zorder=5,
                   edgecolors='white', linewidths=0.4, label='Original (ID 1)')
    if np.any(sub_mask):
        pts = graph.nodes[sub_mask]
        ax.scatter(pts[:, 0], pts[:, 1], s=20, c='red', zorder=4,
                   edgecolors='white', linewidths=0.3, label='Subdivision (ID 2)')

    ax.set_aspect('equal')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    if title is None:
        title = (f'Graph mesh: {graph.n_nodes} nodes '
                 f'({int(orig_mask.sum())} orig + {int(sub_mask.sum())} sub), '
                 f'{graph.n_bars} sub-bars from '
                 f'{len(unique_bars)} original bars')
    ax.set_title(title)
    ax.legend(loc='upper right')
    plt.tight_layout()

    if show:
        plt.show()
    return fig


@dataclass
class MeshConfig:
    """
    Configuration object for hexagonal mesh generation.

    Attributes:
        domain_size: Side length of the square domain.
        n_holes_width: Number of holes across the width of the domain.
        porosity: Target porosity (hole area / total area) for the unit cell,
            relative to the active (inner) domain excluding solid edge strips.
        edge_left/right/bottom/top: Width of solid edge strips to add outside
            the porous zone.  Moved here from the meshing-function call so
            that porosity is always interpreted relative to the inner domain.
    """
    domain_size: float
    n_holes_width: int
    porosity: float
    edge_left: float = 0.0
    edge_right: float = 0.0
    edge_bottom: float = 0.0
    edge_top: float = 0.0


def create_hexagonal_mesh(
    config: MeshConfig,
    filepath: str,
    export_mesh: bool = True,
    export_vtk: bool = True,
    show_plot: bool = False,
    elements_around_hole: int = 24,
    mesh_size_factor: float = 1.0,
) -> Tuple[HexagonalMeshGenerator, MeshData]:
    """
    Create only the finite-element mesh for a hexagonal packing.

    Derived artifacts such as graph, grid, gridhex, and Voronoi/Delaunay VTK
    exports are created by separate functions that take the ``*.mesh.json``
    file as input.
    """

    # --- build generator & mesh ------------------------------------------------
    generator = HexagonalMeshGenerator(
        domain_size=config.domain_size,
        n_holes_width=config.n_holes_width,
        porosity=config.porosity,
    )

    mesh = generator.generate_mesh(
        elements_around_hole=elements_around_hole,
        mesh_size_factor=mesh_size_factor,
    )

    # Compute node labels (needed by VTK export and plotting)
    mesh.compute_node_labels()

    # --- ensure output directory exists ----------------------------------------
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    mesh_json = _ensure_json_suffix(filepath, "mesh")
    if export_mesh:
        write_mesh_json(
            mesh,
            mesh_json,
            mesh_kind="hexagonal_packing",
            created_by="create_hexagonal_mesh",
            generator=generator,
            parameters={
                "config": {
                    "domain_size": config.domain_size,
                    "n_holes_width": config.n_holes_width,
                    "porosity": config.porosity,
                },
                "elements_around_hole": elements_around_hole,
                "mesh_size_factor": mesh_size_factor,
                "periodic": "none",
            },
        )
        if export_vtk:
            export_mesh_vtk_from_json(mesh_json)

    # --- plotting --------------------------------------------------------------
    if show_plot:
        # Mesh with nodes colored by label IDs
        generator.plot_node_labels(mesh, show_label=True)
        plt.show()


    # --- summary ---------------------------------------------------------------
    print(
        f"Mesh created: {mesh.n_nodes} nodes, {mesh.n_elements} elements, "
        f"{len(generator.hole_centers)} holes"
    )

    return generator, mesh


# ---------------------------------------------------------------------------
# Variant 2 – hexagonal mesh with partial (cut) holes at the edges
# ---------------------------------------------------------------------------

class HexagonalMeshGenerator2(HexagonalMeshGenerator):
    """
    Like :class:`HexagonalMeshGenerator` but **allows holes that are only
    partially inside the domain**.

    Holes whose circles overlap the domain boundary are kept; the mesh
    is built with Gmsh's OpenCASCADE (OCC) kernel so that circles are
    automatically clipped against the rectangular domain.

    Per-edge flags (``allow_cut_*``) control which edges may have
    partially-cut holes.  Set a flag to *False* to exclude any hole
    that would intersect that edge.
    """

    def __init__(
        self,
        domain_size: float,
        n_holes_width: int,
        porosity: float,
        center_domain: bool = True,
        allow_cut_left: bool = True,
        allow_cut_right: bool = True,
        allow_cut_bottom: bool = True,
        allow_cut_top: bool = True,
    ):
        self.allow_cut_left = allow_cut_left
        self.allow_cut_right = allow_cut_right
        self.allow_cut_bottom = allow_cut_bottom
        self.allow_cut_top = allow_cut_top
        super().__init__(domain_size, n_holes_width, porosity, center_domain)

    # -----------------------------------------------------------------
    # Classify each hole by which edge (if any) cuts it
    # -----------------------------------------------------------------
    def _classify_holes(self) -> List[int]:
        """
        Classify each hole based on its position relative to the domain.

        Returns
        -------
        list[int]
            One entry per hole in ``self.hole_centers``:

            * 1 – hole is cut by the **left** edge
            * 2 – hole is cut by the **bottom** edge
            * 3 – hole is cut by the **right** edge
            * 4 – hole is cut by the **top** edge
            * 5 – hole is **complete** (fully inside the domain)

            When a hole is cut by more than one edge (corner region) the
            priority order is left → bottom → right → top.
        """
        L = self.domain_size
        r = self.geometry.hole_radius
        tol = L * 1e-8

        classifications: List[int] = []
        for cx, cy in self.hole_centers:
            cut_left   = (cx - r) < -tol
            cut_bottom = (cy - r) < -tol
            cut_right  = (cx + r) > L + tol
            cut_top    = (cy + r) > L + tol

            if cut_left:
                classifications.append(1)
            elif cut_bottom:
                classifications.append(2)
            elif cut_right:
                classifications.append(3)
            elif cut_top:
                classifications.append(4)
            else:
                classifications.append(5)

        return classifications

    # -----------------------------------------------------------------
    # Override: include partially-overlapping holes
    # -----------------------------------------------------------------
    def _compute_hole_centers(self) -> np.ndarray:
        """Compute hole centers including those that partially overlap the domain."""
        a = self.geometry.horizontal_spacing
        b = self.geometry.vertical_spacing
        r = self.geometry.hole_radius
        L = self.domain_size

        # Row range must cover y from -r to L+r so circles can
        # partially overlap the bottom and top edges.
        row_start = int(np.floor(-r / b)) - 1
        row_end = int(np.ceil((L + r) / b)) + 1

        centers = []

        for row in range(row_start, row_end + 1):
            y = row * b
            x_offset = (a / 2) if (row % 2 == 1) else 0

            if self.center_domain:
                x_base = (L % a) / 2 + x_offset
            else:
                x_base = a / 2 + x_offset

            # Walk x left until the circle cannot reach the domain
            x = x_base
            while x > -r:
                x -= a

            # Now sweep rightward, collecting any overlapping hole
            while x < L + r:
                if (x + r > 0 and x - r < L and y + r > 0 and y - r < L):
                    centers.append([x, y])
                x += a

        if len(centers) == 0:
            warnings.warn("No holes overlap the domain with current parameters")
            return np.array([]).reshape(0, 2)

        centers = np.array(centers)

        # Filter out holes that cut disallowed edges
        tol_edge = L * 1e-8
        keep = np.ones(len(centers), dtype=bool)
        for i, (cx, cy) in enumerate(centers):
            cuts_left   = (cx - r) < -tol_edge
            cuts_right  = (cx + r) > L + tol_edge
            cuts_bottom = (cy - r) < -tol_edge
            cuts_top    = (cy + r) > L + tol_edge

            if cuts_left and not self.allow_cut_left:
                keep[i] = False
            if cuts_right and not self.allow_cut_right:
                keep[i] = False
            if cuts_bottom and not self.allow_cut_bottom:
                keep[i] = False
            if cuts_top and not self.allow_cut_top:
                keep[i] = False
        centers = centers[keep]

        if len(centers) == 0:
            warnings.warn("All holes were removed by edge-cut filters")
            return np.array([]).reshape(0, 2)

        # Center vertically if requested
        if self.center_domain and len(centers) > 0:
            y_min = centers[:, 1].min()
            y_max = centers[:, 1].max()
            y_center_current = (y_max + y_min) / 2
            y_shift = L / 2 - y_center_current
            centers[:, 1] += y_shift

            # Re-filter: keep any hole that still overlaps the domain
            mask = (
                (centers[:, 0] + r > 0) & (centers[:, 0] - r < L) &
                (centers[:, 1] + r > 0) & (centers[:, 1] - r < L)
            )
            centers = centers[mask]

        return centers

    # -----------------------------------------------------------------
    # Override: use OCC kernel for boolean cut (handles partial holes)
    # -----------------------------------------------------------------
    def generate_mesh(
        self,
        elements_around_hole: int = 24,
        mesh_size_factor: float = 1.0,
        mesh_size: float = None,
        algorithm: str = 'auto',
        element_type: str = 'QUAD',
        edge_padding: Dict[str, float] = None,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
    ) -> MeshData:
        """
        Generate a boundary-conforming mesh using the OpenCASCADE kernel
        so that circles extending beyond the domain are automatically
        clipped.

        Parameters
        ----------
        elements_around_hole : int
            Approximate number of elements around each hole.
        mesh_size_factor : float
            Mesh density multiplier (smaller = finer).
        algorithm : str
            Gmsh meshing algorithm hint (``'auto'`` lets this method choose).
        element_type : str
            Element topology for the 2-D mesh.  One of:

            * ``'QUAD'`` – all-quad mesh (default, same as previous behaviour).
            * ``'TRI'``  – all-triangle mesh.
            * ``'BOTH'`` – mixed mesh; Gmsh recombines what it can into quads
              and leaves the rest as triangles.
        edge_padding : dict or None
            Optional padding to expand the domain rectangle before meshing.
            Keys: ``'left'``, ``'right'``, ``'bottom'``, ``'top'`` (floats,
            same units as ``domain_size``).  Holes remain at their original
            positions, so the padded regions become solid (hole-free) strips
            that are meshed naturally by Gmsh.
        periodic_lr : bool
            If True, enforce periodic meshing between left and right
            boundaries so that node positions match.  Requires a
            horizontally-periodic hole pattern.
        periodic_tb : bool
            If True, enforce periodic meshing between top and bottom
            boundaries so that node positions match.  Requires a
            vertically-periodic hole pattern.
        """
        element_type = element_type.upper()
        if element_type not in ('QUAD', 'TRI', 'BOTH'):
            raise ValueError(
                f"element_type must be 'QUAD', 'TRI' or 'BOTH' (got '{element_type}')"
            )

        if not GMSH_AVAILABLE:
            raise RuntimeError("Gmsh is required.  Install with: pip install gmsh")

        # Remember original periodicity request (local vars may be set to
        # False later if gmsh curve counts don't match)
        _want_periodic_lr = periodic_lr
        _want_periodic_tb = periodic_tb

        # --- mesh sizing -------------------------------------------------------
        if mesh_size is not None:
            mesh_size_hole = float(mesh_size)
            mesh_size_bg   = float(mesh_size)
        else:
            circumference = 2 * np.pi * self.geometry.hole_radius
            mesh_size_hole = circumference / elements_around_hole * mesh_size_factor
            mesh_size_bg = min(
                self.geometry.get_minimum_ligament() / 3,
                self.horizontal_spacing / 4,
            ) * mesh_size_factor

        L = self.domain_size
        r = self.geometry.hole_radius

        # Domain bounds (optionally expanded for solid edge strips)
        if edge_padding:
            _x0 = -edge_padding.get('left', 0.0)
            _x1 = L + edge_padding.get('right', 0.0)
            _y0 = -edge_padding.get('bottom', 0.0)
            _y1 = L + edge_padding.get('top', 0.0)
        else:
            _x0, _y0 = 0.0, 0.0
            _x1, _y1 = L, L

        # --- build geometry with OCC -------------------------------------------
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("hexagonal_mesh_2")

        # Rectangle (returns surface tag)
        rect_tag = gmsh.model.occ.addRectangle(_x0, _y0, 0, _x1 - _x0, _y1 - _y0)

        # Disks for every hole (including partial ones)
        disk_dimtags = []
        for cx, cy in self.hole_centers:
            dtag = gmsh.model.occ.addDisk(cx, cy, 0, r, r)
            disk_dimtags.append((2, dtag))

        # Boolean cut: rectangle − disks
        if disk_dimtags:
            out_dimtags, _ = gmsh.model.occ.cut(
                [(2, rect_tag)], disk_dimtags,
                removeObject=True, removeTool=True,
            )
        else:
            out_dimtags = [(2, rect_tag)]

        gmsh.model.occ.synchronize()

        # --- physical groups (surface) -----------------------------------------
        surface_tags = [dt[1] for dt in out_dimtags if dt[0] == 2]
        gmsh.model.addPhysicalGroup(2, surface_tags, 100, "domain")

        # Identify and tag boundary curves geometrically.
        # We use the curve ENDPOINTS to decide which domain edge a curve
        # belongs to.  This is essential when holes cut an edge: the
        # resulting arcs have midpoints that are not on x=0 / x=L, but
        # their endpoints *are* on the edge.  A curve can belong to both
        # an edge list (for periodicity) and hole_curve_tags (for size
        # field refinement).
        all_curves = gmsh.model.getEntities(1)
        bottom_curves, right_curves, top_curves, left_curves = [], [], [], []
        hole_curve_tags = []

        tol_class = L * 1e-4

        for dim, tag in all_curves:
            # --- endpoints ---------------------------------------------------
            param_range = gmsh.model.getParametrizationBounds(dim, tag)
            t_start, t_end = param_range[0][0], param_range[1][0]
            p_start = gmsh.model.getValue(dim, tag, [t_start])
            p_end   = gmsh.model.getValue(dim, tag, [t_end])
            sx, sy = p_start[0], p_start[1]
            ex, ey = p_end[0],   p_end[1]

            # --- midpoint (for hole check) -----------------------------------
            t_mid = 0.5 * (t_start + t_end)
            mid = gmsh.model.getValue(dim, tag, [t_mid])
            mx, my = mid[0], mid[1]

            # --- is this curve (part of) a hole arc? -------------------------
            is_hole = False
            for cx, cy in self.hole_centers:
                dist = np.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
                if abs(dist - r) < tol_class:
                    is_hole = True
                    break
            if is_hole:
                hole_curve_tags.append(tag)

            # --- classify by which edge BOTH endpoints lie on ----------------
            both_on_left   = abs(sx - _x0) < tol_class and abs(ex - _x0) < tol_class
            both_on_right  = abs(sx - _x1) < tol_class and abs(ex - _x1) < tol_class
            both_on_bottom = abs(sy - _y0) < tol_class and abs(ey - _y0) < tol_class
            both_on_top    = abs(sy - _y1) < tol_class and abs(ey - _y1) < tol_class

            if both_on_bottom:
                bottom_curves.append(tag)
            elif both_on_top:
                top_curves.append(tag)
            elif both_on_left:
                left_curves.append(tag)
            elif both_on_right:
                right_curves.append(tag)
            elif not is_hole:
                # Fallback: use midpoint for interior curves not on a hole
                pass

        if bottom_curves:
            gmsh.model.addPhysicalGroup(1, bottom_curves, 1, "bottom")
        if right_curves:
            gmsh.model.addPhysicalGroup(1, right_curves, 2, "right")
        if top_curves:
            gmsh.model.addPhysicalGroup(1, top_curves, 3, "top")
        if left_curves:
            gmsh.model.addPhysicalGroup(1, left_curves, 4, "left")
        if hole_curve_tags:
            gmsh.model.addPhysicalGroup(1, hole_curve_tags, 10, "holes")

        # --- meshing options (depend on element_type) --------------------------
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)

        if element_type == 'QUAD':
            gmsh.option.setNumber("Mesh.RecombineAll", 1)
            gmsh.option.setNumber("Mesh.Algorithm", 8)           # Frontal-Delaunay for quads
            gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # Blossom
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 2)   # All-quads
        elif element_type == 'TRI':
            gmsh.option.setNumber("Mesh.RecombineAll", 0)
            gmsh.option.setNumber("Mesh.Algorithm", 6)           # Frontal-Delaunay
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 0)
        else:  # BOTH
            gmsh.option.setNumber("Mesh.RecombineAll", 1)
            gmsh.option.setNumber("Mesh.Algorithm", 8)           # Frontal-Delaunay for quads
            gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # Blossom
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 0)   # Keep remaining tris

        # Size field for refinement near hole arcs
        if mesh_size is not None:
            # Uniform mesh: disable Gmsh geometric size hints and enforce
            # a constant global size so all elements are the same target size.
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
            gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
            gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_hole)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_bg)
        elif hole_curve_tags:
            gmsh.model.mesh.field.add("Distance", 1)
            gmsh.model.mesh.field.setNumbers(1, "CurvesList", hole_curve_tags)
            gmsh.model.mesh.field.setNumber(1, "Sampling", 100)

            gmsh.model.mesh.field.add("Threshold", 2)
            gmsh.model.mesh.field.setNumber(2, "InField", 1)
            gmsh.model.mesh.field.setNumber(2, "SizeMin", mesh_size_hole)
            gmsh.model.mesh.field.setNumber(2, "SizeMax", mesh_size_bg)
            gmsh.model.mesh.field.setNumber(2, "DistMin", r * 0.5)
            gmsh.model.mesh.field.setNumber(2, "DistMax",
                                            self.geometry.get_minimum_ligament())
            gmsh.model.mesh.field.setAsBackgroundMesh(2)
        else:
            # No holes → uniform background size
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_bg)

        # --- periodic meshing constraints ------------------------------------
        if periodic_lr:
            if len(left_curves) != len(right_curves):
                warnings.warn(
                    f"Cannot enforce LR periodicity: left has "
                    f"{len(left_curves)} curve(s) but right has "
                    f"{len(right_curves)}.  Ensure the hole pattern is "
                    f"horizontally periodic.  Skipping LR periodicity."
                )
                periodic_lr = False
            elif left_curves and right_curves:
                def _curve_y_mid(tag):
                    pr = gmsh.model.getParametrizationBounds(1, tag)
                    t = 0.5 * (pr[0][0] + pr[1][0])
                    return gmsh.model.getValue(1, tag, [t])[1]

                left_sorted = sorted(left_curves, key=_curve_y_mid)
                right_sorted = sorted(right_curves, key=_curve_y_mid)
                dx = _x1 - _x0
                affine_lr = [1, 0, 0, dx,
                             0, 1, 0, 0,
                             0, 0, 1, 0,
                             0, 0, 0, 1]
                gmsh.model.mesh.setPeriodic(
                    1, right_sorted, left_sorted, affine_lr)

        if periodic_tb:
            if len(bottom_curves) != len(top_curves):
                warnings.warn(
                    f"Cannot enforce TB periodicity: bottom has "
                    f"{len(bottom_curves)} curve(s) but top has "
                    f"{len(top_curves)}.  Ensure the hole pattern is "
                    f"vertically periodic.  Skipping TB periodicity."
                )
                periodic_tb = False
            elif bottom_curves and top_curves:
                def _curve_x_mid(tag):
                    pr = gmsh.model.getParametrizationBounds(1, tag)
                    t = 0.5 * (pr[0][0] + pr[1][0])
                    return gmsh.model.getValue(1, tag, [t])[0]

                bottom_sorted = sorted(bottom_curves, key=_curve_x_mid)
                top_sorted = sorted(top_curves, key=_curve_x_mid)
                dy = _y1 - _y0
                affine_tb = [1, 0, 0, 0,
                             0, 1, 0, dy,
                             0, 0, 1, 0,
                             0, 0, 0, 1]
                gmsh.model.mesh.setPeriodic(
                    1, top_sorted, bottom_sorted, affine_tb)

        # --- generate ----------------------------------------------------------
        gmsh.model.mesh.generate(2)
        if element_type in ('QUAD', 'BOTH'):
            gmsh.model.mesh.recombine()

        # --- extract mesh data -------------------------------------------------
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        nodes = np.array(node_coords).reshape(-1, 3)[:, :2]
        tag_to_idx = {tag: i for i, tag in enumerate(node_tags)}

        elem_types_gmsh, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(2)

        n_tri = 0
        n_quad = 0
        elements = []
        et_list: List[int] = []       # 3 or 4 per element

        for etype, etags, enodes in zip(elem_types_gmsh, elem_tags, elem_node_tags):
            if etype == 2:  # 3-node triangle
                n_tri += len(etags)
                enodes = np.array(enodes).reshape(-1, 3)
                for tri_nodes in enodes:
                    idx = [tag_to_idx[t] for t in tri_nodes]
                    if element_type == 'QUAD':
                        # Degenerate quad: repeat last node
                        elements.append(idx + [idx[2]])
                        et_list.append(4)
                    else:
                        elements.append(idx)
                        et_list.append(3)
            elif etype == 3:  # 4-node quad
                n_quad += len(etags)
                enodes = np.array(enodes).reshape(-1, 4)
                for quad_nodes in enodes:
                    elements.append([tag_to_idx[t] for t in quad_nodes])
                    et_list.append(4)

        # Warnings / info about element mix
        if element_type == 'QUAD' and n_tri > 0:
            warnings.warn(
                f"Gmsh produced {n_tri} triangular element(s) that were "
                f"converted to degenerate quads (collapsed edge). Increase "
                f"elements_around_hole or decrease mesh_size_factor for a "
                f"fully-quad mesh."
            )
        elif element_type == 'TRI' and n_quad > 0:
            warnings.warn(
                f"Gmsh produced {n_quad} quad element(s) in TRI mode. "
                f"This is unexpected; the mesh may need review."
            )

        # Build element_types array
        element_types_arr = np.array(et_list, dtype=int) if et_list else np.array([], dtype=int)

        # Pad TRI elements to width 4 when mixed with QUADs (BOTH mode)
        if element_type == 'BOTH' and n_tri > 0 and n_quad > 0:
            max_npe = 4
            padded = []
            for elem, npe in zip(elements, et_list):
                if npe < max_npe:
                    padded.append(elem + [-1] * (max_npe - npe))
                else:
                    padded.append(elem)
            elements_np = np.array(padded) if padded else np.array([]).reshape(0, 4)
        elif element_type == 'TRI' or (element_type == 'BOTH' and n_quad == 0):
            elements_np = np.array(elements) if elements else np.array([]).reshape(0, 3)
        else:
            elements_np = np.array(elements) if elements else np.array([]).reshape(0, 4)

        # Remove isolated nodes (e.g. hole centres kept by OCC)
        # When padding with -1, exclude -1 from the unique set
        if len(elements_np) > 0:
            flat = elements_np.flatten()
            used_node_indices = np.unique(flat[flat >= 0])
        else:
            used_node_indices = np.array([], dtype=int)

        old_to_new = np.full(len(nodes), -1, dtype=int)
        old_to_new[used_node_indices] = np.arange(len(used_node_indices))
        nodes_filtered = nodes[used_node_indices]

        if len(elements_np) > 0:
            # Remap node indices; keep -1 padding untouched
            mask_valid = elements_np >= 0
            elements_remapped = elements_np.copy()
            elements_remapped[mask_valid] = old_to_new[elements_np[mask_valid]]
        else:
            elements_remapped = elements_np

        # --- geometric boundary identification ---------------------------------
        tol = L * 1e-6
        boundary_nodes = {
            'bottom': np.where(np.abs(nodes_filtered[:, 1] - _y0) < tol)[0],
            'right':  np.where(np.abs(nodes_filtered[:, 0] - _x1) < tol)[0],
            'top':    np.where(np.abs(nodes_filtered[:, 1] - _y1) < tol)[0],
            'left':   np.where(np.abs(nodes_filtered[:, 0] - _x0) < tol)[0],
        }

        hole_boundary_nodes = []
        for center in self.hole_centers:
            distances = np.linalg.norm(nodes_filtered - center, axis=1)
            on_circle = np.where(
                np.abs(distances - r) < tol * 100
            )[0]
            hole_boundary_nodes.append(on_circle)

        # --- extract periodic node pairs from gmsh --------------------------
        _periodic_lr_gmsh: List[Tuple[int, int]] = []  # (left_tag, right_tag)
        _periodic_tb_gmsh: List[Tuple[int, int]] = []  # (top_tag, bottom_tag)

        if periodic_lr:
            for tag in right_curves:
                try:
                    _, slave_tags, master_tags, _ = (
                        gmsh.model.mesh.getPeriodicNodes(1, tag))
                    for st, mt in zip(slave_tags, master_tags):
                        _periodic_lr_gmsh.append(
                            (int(mt), int(st)))   # (left, right)
                except Exception:
                    pass

        if periodic_tb:
            for tag in top_curves:
                try:
                    _, slave_tags, master_tags, _ = (
                        gmsh.model.mesh.getPeriodicNodes(1, tag))
                    for st, mt in zip(slave_tags, master_tags):
                        _periodic_tb_gmsh.append(
                            (int(st), int(mt)))   # (top, bottom)
                except Exception:
                    pass

        gmsh.finalize()

        # --- remap periodic pairs through old_to_new ---------------------------
        periodic_pairs_lr = None
        periodic_pairs_tb = None

        if _periodic_lr_gmsh:
            pairs, seen = [], set()
            for left_tag, right_tag in _periodic_lr_gmsh:
                li = tag_to_idx.get(left_tag, -1)
                ri = tag_to_idx.get(right_tag, -1)
                if li >= 0 and ri >= 0:
                    li_new = int(old_to_new[li])
                    ri_new = int(old_to_new[ri])
                    if li_new >= 0 and ri_new >= 0 and (li_new, ri_new) not in seen:
                        pairs.append([li_new, ri_new])
                        seen.add((li_new, ri_new))
            if pairs:
                # Sort by y-coordinate of the left node for readability
                pairs.sort(key=lambda p: nodes_filtered[p[0], 1])
                periodic_pairs_lr = np.array(pairs, dtype=int)

        if _periodic_tb_gmsh:
            pairs, seen = [], set()
            for top_tag, bottom_tag in _periodic_tb_gmsh:
                ti_idx = tag_to_idx.get(top_tag, -1)
                bi = tag_to_idx.get(bottom_tag, -1)
                if ti_idx >= 0 and bi >= 0:
                    ti_new = int(old_to_new[ti_idx])
                    bi_new = int(old_to_new[bi])
                    if ti_new >= 0 and bi_new >= 0 and (ti_new, bi_new) not in seen:
                        pairs.append([ti_new, bi_new])
                        seen.add((ti_new, bi_new))
            if pairs:
                # Sort by x-coordinate of the top node for readability
                pairs.sort(key=lambda p: nodes_filtered[p[0], 0])
                periodic_pairs_tb = np.array(pairs, dtype=int)

        # --- geometric fallback for periodic pairs ----------------------------
        # When gmsh's setPeriodic could not be used (asymmetric OCC curves)
        # but periodicity was requested, build pairs by matching boundary
        # node coordinates.
        if _want_periodic_lr and periodic_pairs_lr is None:
            left_idx  = boundary_nodes['left']
            right_idx = boundary_nodes['right']
            if len(left_idx) > 0 and len(left_idx) == len(right_idx):
                # Sort both sets by y-coordinate and pair them
                left_sorted  = left_idx[np.argsort(nodes_filtered[left_idx, 1])]
                right_sorted = right_idx[np.argsort(nodes_filtered[right_idx, 1])]
                pairs = np.column_stack([left_sorted, right_sorted])
                periodic_pairs_lr = pairs
                print(f"  Periodic LR: {len(pairs)} pairs built by "
                      f"geometric matching (fallback)")
            elif len(left_idx) != len(right_idx):
                warnings.warn(
                    f"Cannot build LR periodic pairs: left has "
                    f"{len(left_idx)} node(s) but right has "
                    f"{len(right_idx)}.  Skipping."
                )

        if _want_periodic_tb and periodic_pairs_tb is None:
            bottom_idx = boundary_nodes['bottom']
            top_idx    = boundary_nodes['top']
            if len(bottom_idx) > 0 and len(bottom_idx) == len(top_idx):
                bottom_sorted = bottom_idx[np.argsort(nodes_filtered[bottom_idx, 0])]
                top_sorted    = top_idx[np.argsort(nodes_filtered[top_idx, 0])]
                pairs = np.column_stack([top_sorted, bottom_sorted])
                periodic_pairs_tb = pairs
                print(f"  Periodic TB: {len(pairs)} pairs built by "
                      f"geometric matching (fallback)")
            elif len(bottom_idx) != len(top_idx):
                warnings.warn(
                    f"Cannot build TB periodic pairs: bottom has "
                    f"{len(bottom_idx)} node(s) but top has "
                    f"{len(top_idx)}.  Skipping."
                )

        # Classify each hole (complete vs cut by which edge)
        hole_classifications = self._classify_holes()

        # Reorder holes so that numbering (X..) follows:
        #   B=5 (complete) → B=1 (left-cut) → B=2 (bottom-cut)
        #   → B=3 (right-cut) → B=4 (top-cut)
        b_priority = {5: 0, 1: 1, 2: 2, 3: 3, 4: 4}
        order = sorted(
            range(len(hole_classifications)),
            key=lambda i: b_priority.get(hole_classifications[i], 99),
        )
        hole_classifications = [hole_classifications[i] for i in order]
        hole_boundary_nodes = [hole_boundary_nodes[i] for i in order]
        self.hole_centers = self.hole_centers[order]

        return MeshData(
            nodes=nodes_filtered,
            elements=elements_remapped,
            boundary_nodes=boundary_nodes,
            hole_boundary_nodes=hole_boundary_nodes,
            hole_classifications=hole_classifications,
            element_types=element_types_arr,
            periodic_pairs_lr=periodic_pairs_lr,
            periodic_pairs_tb=periodic_pairs_tb,
        )


def export_periodic_file(filepath: str, mesh: MeshData) -> None:
    raise RuntimeError(
        "Periodic pair sidecar files have been removed. "
        "Periodic node matches are stored in the main *.mesh.json file."
    )


def _add_edge_strips(
    mesh: MeshData,
    edge_left: float = 0.0,
    edge_right: float = 0.0,
    edge_bottom: float = 0.0,
    edge_top: float = 0.0,
    n_strip_layers: int = 1,
) -> Tuple[MeshData, Dict[str, float]]:
    """
    Add solid quad-element strips along selected domain edges, then
    rescale the mesh so that the final bounding box is ``[0, L] x [0, L]``
    where *L* is the original domain size.

    For each requested edge a row of ``n_strip_layers`` quad elements is
    extruded outward from the existing boundary nodes.

    Parameters
    ----------
    mesh : MeshData
        Input mesh (nodes in ``[0, L]``).
    edge_left, edge_right, edge_bottom, edge_top : float
        Width of the solid strip on each edge, in the same units as the
        domain size.  Use ``0.0`` (or any falsy value) to skip an edge.
    n_strip_layers : int
        Number of element layers within each strip (default 1).
        The specified edge width is divided equally among the layers.

    Returns
    -------
    mesh_out : MeshData
        New mesh with added strips and coordinates rescaled to
        ``[0, Lx] x [0, Ly]``.
    scaling_info : dict
        Keys ``'w_left'``, ``'w_right'``, ``'w_bottom'``, ``'w_top'``,
        ``'Lx_orig'``, ``'Ly_orig'`` describing the transform applied,
        so the caller can rescale hole centres accordingly.
    """
    w_left = float(edge_left) if edge_left else 0.0
    w_right = float(edge_right) if edge_right else 0.0
    w_bottom = float(edge_bottom) if edge_bottom else 0.0
    w_top = float(edge_top) if edge_top else 0.0

    no_op_info = {'w_left': 0.0, 'w_right': 0.0, 'w_bottom': 0.0,
                  'w_top': 0.0, 'Lx_orig': 0.0, 'Ly_orig': 0.0}

    if not (w_left or w_right or w_bottom or w_top):
        return mesh, no_op_info  # nothing to do

    # Work with mutable copies
    nodes = mesh.nodes.copy().tolist()  # list of [x, y]
    elements = mesh.elements.copy().tolist()

    if mesh.element_types is not None:
        etypes = mesh.element_types.copy().tolist()
    else:
        etypes = [4] * len(elements)

    # Mutable boundary_nodes (dict of sets)
    bnd = {k: set(v.tolist()) for k, v in mesh.boundary_nodes.items()}

    # Deep copy hole_boundary_nodes (indices stay valid – we only add nodes)
    hole_bnd = [arr.copy() for arr in mesh.hole_boundary_nodes]
    hole_class = list(mesh.hole_classifications) if mesh.hole_classifications else []

    # Detect the current domain extent
    all_nodes = np.array(nodes)
    x_min, y_min = all_nodes.min(axis=0)
    x_max, y_max = all_nodes.max(axis=0)
    Lx_orig = x_max - x_min
    Ly_orig = y_max - y_min

    # ---- helper: extrude one edge -----------------------------------------
    def _extrude_edge(edge_name: str, coord_axis: int, at_max: bool,
                      total_width: float):
        """
        Extrude `n_strip_layers` of quad elements from boundary `edge_name`.

        coord_axis  : 0 for left/right (x), 1 for bottom/top (y)
        at_max      : True if the strip extends toward +axis (right / top)
        total_width : total strip thickness (divided among n_strip_layers)
        """
        nonlocal nodes, elements, etypes, bnd

        sort_axis = 1 if coord_axis == 0 else 0  # sort along the other axis
        bnd_indices = sorted(bnd[edge_name],
                             key=lambda i: nodes[i][sort_axis])

        if len(bnd_indices) < 2:
            return

        layer_width = total_width / n_strip_layers

        prev_layer = list(bnd_indices)  # node indices of the current edge

        # Track first/last (corner) node of every new layer so we can
        # register them all in the adjacent-edge boundary sets.
        all_first_corners = []   # adj_lo end (e.g. bottom for a left strip)
        all_last_corners = []    # adj_hi end (e.g. top   for a left strip)

        for layer in range(n_strip_layers):
            offset = layer_width * (layer + 1) * (1 if at_max else -1)
            new_layer = []
            for idx in bnd_indices:
                new_node = list(nodes[idx])
                new_node[coord_axis] += offset
                new_id = len(nodes)
                nodes.append(new_node)
                new_layer.append(new_id)

            all_first_corners.append(new_layer[0])
            all_last_corners.append(new_layer[-1])

            # Create quad elements between prev_layer and new_layer
            for j in range(len(prev_layer) - 1):
                if at_max:
                    if coord_axis == 0:  # right edge: extrude in +x
                        quad = [prev_layer[j], new_layer[j],
                                new_layer[j+1], prev_layer[j+1]]
                    else:  # top edge: extrude in +y
                        quad = [prev_layer[j], prev_layer[j+1],
                                new_layer[j+1], new_layer[j]]
                else:
                    if coord_axis == 0:  # left edge: extrude in -x
                        quad = [new_layer[j], prev_layer[j],
                                prev_layer[j+1], new_layer[j+1]]
                    else:  # bottom edge: extrude in -y
                        quad = [new_layer[j], new_layer[j+1],
                                prev_layer[j+1], prev_layer[j]]

                elements.append(quad)
                etypes.append(4)

            prev_layer = list(new_layer)

        # Update boundary: old boundary nodes are no longer on the edge,
        # the new outer layer becomes the boundary.
        bnd[edge_name] = set(prev_layer)

        # Determine which adjacent edges share the corner nodes.
        first_old = bnd_indices[0]
        last_old = bnd_indices[-1]

        if edge_name in ('left', 'right'):
            adj_lo, adj_hi = 'bottom', 'top'
        else:
            adj_lo, adj_hi = 'left', 'right'

        # Add ALL intermediate corner nodes to adjacent boundary sets.
        # Keep the original corner node too — it still lies on that edge.
        if first_old in bnd.get(adj_lo, set()):
            for nid in all_first_corners:
                bnd[adj_lo].add(nid)
        if last_old in bnd.get(adj_hi, set()):
            for nid in all_last_corners:
                bnd[adj_hi].add(nid)

    # ---- apply requested strips -------------------------------------------
    if w_left > 0:
        _extrude_edge('left', coord_axis=0, at_max=False, total_width=w_left)
    if w_right > 0:
        _extrude_edge('right', coord_axis=0, at_max=True, total_width=w_right)
    if w_bottom > 0:
        _extrude_edge('bottom', coord_axis=1, at_max=False, total_width=w_bottom)
    if w_top > 0:
        _extrude_edge('top', coord_axis=1, at_max=True, total_width=w_top)

    # ---- rescale to original domain [0, Lx] x [0, Ly] --------------------
    nodes_arr = np.array(nodes)
    new_xmin, new_ymin = nodes_arr.min(axis=0)
    new_xmax, new_ymax = nodes_arr.max(axis=0)

    # Shift so min is at 0, then scale to original L
    nodes_arr[:, 0] = (nodes_arr[:, 0] - new_xmin) / (new_xmax - new_xmin) * Lx_orig
    nodes_arr[:, 1] = (nodes_arr[:, 1] - new_ymin) / (new_ymax - new_ymin) * Ly_orig

    # ---- rebuild arrays ---------------------------------------------------
    max_npe = max(len(e) for e in elements) if elements else 4
    elements_padded = []
    for e in elements:
        if len(e) < max_npe:
            elements_padded.append(e + [-1] * (max_npe - len(e)))
        else:
            elements_padded.append(e)

    boundary_nodes_out = {k: np.array(sorted(v), dtype=int) for k, v in bnd.items()}

    scaling_info = {
        'w_left': w_left,
        'w_right': w_right,
        'w_bottom': w_bottom,
        'w_top': w_top,
        'Lx_orig': Lx_orig,
        'Ly_orig': Ly_orig,
    }

    mesh_out = MeshData(
        nodes=nodes_arr,
        elements=np.array(elements_padded, dtype=int),
        boundary_nodes=boundary_nodes_out,
        hole_boundary_nodes=hole_bnd,
        hole_classifications=hole_class if hole_class else None,
        element_types=np.array(etypes, dtype=int),
    )

    return mesh_out, scaling_info



def _remove_isolated_gridhex_nodes(nodes, labels, bars, bar_numbers):
    """
    Iteratively remove nodes connected to exactly one bar, together with
    that bar, until no such nodes remain.

    Parameters
    ----------
    nodes       : np.ndarray, shape (N, 2)
    labels      : np.ndarray, shape (N,)
    bars        : np.ndarray, shape (B, 2)
    bar_numbers : np.ndarray, shape (B,)

    Returns
    -------
    nodes, labels, bars, bar_numbers  – all re-indexed and renumbered.
    n_removed_nodes, n_removed_bars   – counts for logging.
    """
    n_removed_nodes = 0
    n_removed_bars  = 0

    # Work with plain Python lists for cheap mutation
    nodes_list  = list(nodes)
    labels_list = list(labels)
    bars_list   = [list(b) for b in bars]

    while True:
        n = len(nodes_list)
        if n == 0:
            break

        # Count how many bars each node is connected to
        degree = np.zeros(n, dtype=int)
        for (a, b) in bars_list:
            degree[a] += 1
            degree[b] += 1

        isolated = np.where(degree == 1)[0]
        if len(isolated) == 0:
            break   # converged

        isolated_set = set(isolated.tolist())

        # Drop bars that touch an isolated node
        new_bars = [b for b in bars_list
                    if b[0] not in isolated_set and b[1] not in isolated_set]
        n_removed_bars  += len(bars_list) - len(new_bars)
        n_removed_nodes += len(isolated_set)

        # Build keep mask and re-index
        keep       = np.ones(n, dtype=bool)
        keep[list(isolated_set)] = False
        old_to_new = np.full(n, -1, dtype=int)
        old_to_new[keep] = np.arange(keep.sum(), dtype=int)

        nodes_list  = [nodes_list[i]  for i in range(n) if keep[i]]
        labels_list = [labels_list[i] for i in range(n) if keep[i]]
        bars_list   = [[old_to_new[b[0]], old_to_new[b[1]]] for b in new_bars]

    # Pack back into arrays
    if nodes_list:
        out_nodes  = np.array(nodes_list,  dtype=float)
        out_labels = np.array(labels_list, dtype=int)
    else:
        out_nodes  = np.empty((0, 2), dtype=float)
        out_labels = np.empty((0,),   dtype=int)

    if bars_list:
        out_bars     = np.array(bars_list, dtype=int)
        out_bar_nums = np.arange(len(bars_list), dtype=int)
    else:
        out_bars     = np.empty((0, 2), dtype=int)
        out_bar_nums = np.empty((0,),   dtype=int)

    return out_nodes, out_labels, out_bars, out_bar_nums, n_removed_nodes, n_removed_bars


def generate_hexagonal_gridhex_mesh(
    domain_size: float,
    hexagon_size: float,
    hole_centers=None,
    hole_radius: float = 0.0,
    pointy_top: bool = True,
    remove_edge_nodes: bool = True,
    delete_isolated_bars: bool = False,
):
    """
    Build a hexagonal-grid graph object with the same storage layout
    as :class:`GraphMeshData`.

    An auxiliary hexagonal tiling covers ``[0, domain_size]²``.  For every
    hexagon that overlaps the domain:

    * A **centre node** (label = 1) is placed at the hexagon centre.
    * **12 peripheral nodes** (label = 2) are placed at the 6 *vertices*
      and the 6 *edge midpoints* of the hexagon.
    * **12 spoke bars** connect the centre to each peripheral node.

    Peripheral nodes at the same geometric position (shared by adjacent
    hexagons) are merged into a single node.  Nodes strictly inside a hole,
    or on the domain boundary (when ``remove_edge_nodes=True``), are removed
    together with all bars attached to them.

    Parameters
    ----------
    domain_size : float
        Side length of the square domain ``[0, L]²``.
    hexagon_size : float
        Vertex-to-vertex diameter of each auxiliary hexagon (2× circumradius).
    hole_centers : array-like, shape (N, 2), optional
        Centres of circular holes in the FE mesh.
    hole_radius : float
        Radius of every hole.
    pointy_top : bool
        ``True``  → pointy-top orientation (vertex at top/bottom).
        ``False`` → flat-top  orientation (flat edge at top/bottom).
    remove_edge_nodes : bool
        Remove nodes on the domain boundary (same as ``generate_cartesian_grid_mesh``).
    delete_isolated_bars : bool
        If ``True``, iteratively remove every node that is connected to
        exactly one bar (together with that bar) until no such nodes
        remain.  This cleans up dangling spokes that appear near holes
        or domain boundaries.

    Returns
    -------
    GraphMeshData
    """
    R = hexagon_size / 2.0          # circumradius  (centre → vertex)
    r = R * np.sqrt(3.0) / 2.0     # inradius      (centre → edge midpoint)
    L = domain_size

    # ------------------------------------------------------------------
    # 1.  Generate auxiliary hexagon centres that cover [0, L]²
    # ------------------------------------------------------------------
    if pointy_top:
        # pointy-top:
        #   horizontal pitch between centres = sqrt(3) * R
        #   vertical   pitch between centres = 3/2 * R
        #   odd rows are offset by half the horizontal pitch
        sq3R      = np.sqrt(3.0) * R
        col_pitch = sq3R
        row_pitch = 1.5 * R
        row_offset = sq3R / 2.0

        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3

        hex_centres = []
        for row in range(-2, n_rows):
            cy = row * row_pitch
            for col in range(-2, n_cols):
                cx = col * col_pitch + (row % 2) * row_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))

        # pointy-top: vertices at 30°+k·60°, midpoints at 0°+k·60°
        vertex_angles   = np.deg2rad([30, 90, 150, 210, 270, 330])
        midpoint_angles = np.deg2rad([ 0, 60, 120, 180, 240, 300])

    else:
        # flat-top:
        #   horizontal pitch = 3/2 * R
        #   vertical   pitch = sqrt(3) * R
        #   odd columns are offset by half the vertical pitch
        sq3R       = np.sqrt(3.0) * R
        col_pitch  = 1.5 * R
        row_pitch  = sq3R
        col_offset = sq3R / 2.0

        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3

        hex_centres = []
        for col in range(-2, n_cols):
            cx = col * col_pitch
            for row in range(-2, n_rows):
                cy = row * row_pitch + (col % 2) * col_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))

        # flat-top: vertices at 0°+k·60°, midpoints at 30°+k·60°
        vertex_angles   = np.deg2rad([ 0, 60, 120, 180, 240, 300])
        midpoint_angles = np.deg2rad([30, 90, 150, 210, 270, 330])

    vertex_dirs   = np.stack([np.cos(vertex_angles),
                               np.sin(vertex_angles)], axis=1)   # (6,2)
    midpoint_dirs = np.stack([np.cos(midpoint_angles),
                               np.sin(midpoint_angles)], axis=1)  # (6,2)

    # ------------------------------------------------------------------
    # 2.  Collect unique node positions (merge shared peripheral nodes)
    # ------------------------------------------------------------------
    ROUND = 9   # decimal places used for deduplication key

    pos_to_idx: dict = {}
    node_xy:    list = []
    node_label: list = []
    raw_bars:   list = []

    def _add_node(x, y, label):
        k = (round(x, ROUND), round(y, ROUND))
        if k not in pos_to_idx:
            pos_to_idx[k] = len(node_xy)
            node_xy.append([x, y])
            node_label.append(label)
        return pos_to_idx[k]

    for (cx, cy) in hex_centres:
        ci = _add_node(cx, cy, 1)                           # centre (label 1)

        for d in vertex_dirs:                               # 6 vertices
            px, py = cx + R * d[0], cy + R * d[1]
            pi = _add_node(px, py, 2)                       # peripheral (label 2)
            raw_bars.append((ci, pi))

        for d in midpoint_dirs:                             # 6 edge midpoints
            px, py = cx + r * d[0], cy + r * d[1]
            pi = _add_node(px, py, 2)
            raw_bars.append((ci, pi))

    nodes_arr  = np.array(node_xy,    dtype=float)
    labels_arr = np.array(node_label, dtype=int)

    # ------------------------------------------------------------------
    # 3.  Build keep mask: domain interior
    # ------------------------------------------------------------------
    tol = L * 1e-9

    in_domain = (
        (nodes_arr[:, 0] >= -tol) & (nodes_arr[:, 0] <= L + tol) &
        (nodes_arr[:, 1] >= -tol) & (nodes_arr[:, 1] <= L + tol)
    )
    keep = in_domain.copy()

    if remove_edge_nodes:
        on_boundary = (
            (nodes_arr[:, 0] <= tol)     |
            (nodes_arr[:, 0] >= L - tol) |
            (nodes_arr[:, 1] <= tol)     |
            (nodes_arr[:, 1] >= L - tol)
        )
        keep &= ~on_boundary

    # ------------------------------------------------------------------
    # 4.  Keep mask: remove nodes strictly inside holes
    # ------------------------------------------------------------------
    if hole_centers is not None and len(hole_centers) > 0:
        centers_arr = np.asarray(hole_centers, dtype=float)
        active_r    = max(float(hole_radius) - L * 1e-12, 0.0)
        active_r_sq = active_r ** 2

        if active_r_sq > 0.0:
            # vectorised: compute min distance² for every node in one shot
            # shape: (n_nodes, n_holes)
            dx = nodes_arr[:, 0:1] - centers_arr[:, 0]   # (N,H)
            dy = nodes_arr[:, 1:2] - centers_arr[:, 1]   # (N,H)
            dist_sq = dx ** 2 + dy ** 2                   # (N,H)
            inside  = np.any(dist_sq < active_r_sq, axis=1)
            keep   &= ~inside

    # ------------------------------------------------------------------
    # 5.  Re-index surviving nodes
    # ------------------------------------------------------------------
    old_to_new            = np.full(len(nodes_arr), -1, dtype=int)
    old_to_new[keep]      = np.arange(keep.sum(), dtype=int)

    final_nodes  = nodes_arr[keep]
    final_labels = labels_arr[keep]

    # ------------------------------------------------------------------
    # 6.  Filter bars (both endpoints must survive) + deduplicate
    # ------------------------------------------------------------------
    final_bars:    list = []
    final_bar_num: list = []
    bar_counter         = 0
    seen_bars:     set  = set()

    for (a, b) in raw_bars:
        na, nb = old_to_new[a], old_to_new[b]
        if na < 0 or nb < 0:
            continue
        key = (min(na, nb), max(na, nb))
        if key in seen_bars:
            continue
        seen_bars.add(key)
        final_bars.append([na, nb])
        final_bar_num.append(bar_counter)
        bar_counter += 1

    bars_arr    = (np.array(final_bars,    dtype=int)
                   if final_bars else np.empty((0, 2), dtype=int))
    bar_num_arr = (np.array(final_bar_num, dtype=int)
                   if final_bar_num else np.empty((0,), dtype=int))

    # ------------------------------------------------------------------
    # 7.  (Optional) iteratively remove isolated nodes
    # ------------------------------------------------------------------
    if delete_isolated_bars and len(bars_arr) > 0:
        (final_nodes, final_labels,
         bars_arr, bar_num_arr,
         n_rem_n, n_rem_b) = _remove_isolated_gridhex_nodes(
            final_nodes, final_labels, bars_arr, bar_num_arr)
        print(f"  Isolated-bar removal: {n_rem_n} nodes and "
              f"{n_rem_b} bars removed.")

    return GraphMeshData(
        nodes      =final_nodes,
        node_ids   =final_labels,
        bars       =bars_arr,
        bar_numbers=bar_num_arr,
    )


def export_gridhex_mesh(grid: "GraphMeshData", filename: str) -> None:
    """Write hexagonal-grid data as ``*.gridhex.json``."""
    write_graph_json(
        grid,
        filename,
        graph_type="gridhex",
        created_by="export_gridhex_mesh",
        parameters={},
    )


# ===========================================================================
# Updated create_hexagonal_mesh_2
# ===========================================================================

def create_hexagonal_mesh_2(
    config,
    filepath: str,
    export_mesh: bool = True,
    export_vtk: bool = True,
    show_plot: bool = False,
    show_periodic_matching: bool = False,
    elements_around_hole: int = 24,
    mesh_size_factor: float = 1.0,
    mesh_size: float = None,
    allow_cut_left: bool = True,
    allow_cut_right: bool = True,
    allow_cut_bottom: bool = True,
    allow_cut_top: bool = True,
    element_type: str = "QUAD",
    edge_left: float = None,
    edge_right: float = None,
    edge_bottom: float = None,
    edge_top: float = None,
    periodic: str = "none",
):
    """
    Create only the finite-element mesh for a hexagonal packing with optional
    partial holes and write it as ``*.mesh.json``.

    Graph, grid, gridhex, and Voronoi/Delaunay VTK files are created by the
    separate ``create_*_json`` and ``export_*_vtk_from_json`` functions that
    take the mesh JSON file as input.
    """

    # --- build generator & mesh -----------------------------------------------
    generator = HexagonalMeshGenerator2(
        domain_size=config.domain_size,
        n_holes_width=config.n_holes_width,
        porosity=config.porosity,
        allow_cut_left=allow_cut_left,
        allow_cut_right=allow_cut_right,
        allow_cut_bottom=allow_cut_bottom,
        allow_cut_top=allow_cut_top,
    )

    # --- compute edge padding -----------------------------------------------
    # Function-level arguments take precedence; fall back to config fields so
    # that edges can be co-located with the porosity specification.
    w_l = float(edge_left   if edge_left   is not None else getattr(config, 'edge_left',   0.0))
    w_r = float(edge_right  if edge_right  is not None else getattr(config, 'edge_right',  0.0))
    w_b = float(edge_bottom if edge_bottom is not None else getattr(config, 'edge_bottom', 0.0))
    w_t = float(edge_top    if edge_top    is not None else getattr(config, 'edge_top',    0.0))
    has_strips = bool(w_l or w_r or w_b or w_t)

    padding = ({"left": w_l, "right": w_r, "bottom": w_b, "top": w_t}
               if has_strips else None)

    # --- parse periodic flag --------------------------------------------------
    _periodic  = periodic.strip().lower()
    periodic_lr = _periodic in ("lr", "both")
    periodic_tb = _periodic in ("tb", "both")

    mesh = generator.generate_mesh(
        elements_around_hole=elements_around_hole,
        mesh_size_factor=mesh_size_factor,
        mesh_size=mesh_size,
        element_type=element_type,
        edge_padding=padding,
        periodic_lr=periodic_lr,
        periodic_tb=periodic_tb,
    )

    # --- rescale expanded domain back to [0, L] x [0, L] ---------------------
    if has_strips:
        L  = config.domain_size
        sx = L / (L + w_l + w_r)
        sy = L / (L + w_b + w_t)

        mesh.nodes[:, 0] = (mesh.nodes[:, 0] + w_l) * sx
        mesh.nodes[:, 1] = (mesh.nodes[:, 1] + w_b) * sy

        centres           = generator.hole_centers.copy()
        centres[:, 0]     = (centres[:, 0] + w_l) * sx
        centres[:, 1]     = (centres[:, 1] + w_b) * sy
        generator.hole_centers = centres

        generator.geometry.horizontal_spacing *= sx
        generator.geometry.vertical_spacing *= sy
        generator.geometry.hole_radius *= np.sqrt(sx * sy)

        print(f"  Edge strips added (L={edge_left}, R={edge_right}, "
              f"B={edge_bottom}, T={edge_top}), mesh rescaled to "
              f"[0, {config.domain_size}]")

    mesh.compute_node_labels()

    # --- ensure output directory exists ----------------------------------------
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    mesh_json = _ensure_json_suffix(filepath, "mesh")
    if export_mesh:
        write_mesh_json(
            mesh,
            mesh_json,
            mesh_kind="hexagonal_packing",
            created_by="create_hexagonal_mesh_2",
            generator=generator,
            parameters={
                "config": {
                    "domain_size": config.domain_size,
                    "n_holes_width": config.n_holes_width,
                    "porosity": config.porosity,
                },
                "elements_around_hole": elements_around_hole,
                "mesh_size_factor": mesh_size_factor,
                "allow_cut_left": allow_cut_left,
                "allow_cut_right": allow_cut_right,
                "allow_cut_bottom": allow_cut_bottom,
                "allow_cut_top": allow_cut_top,
                "element_type": element_type,
                "edge_left": edge_left,
                "edge_right": edge_right,
                "edge_bottom": edge_bottom,
                "edge_top": edge_top,
                "periodic": periodic,
            },
        )
        if export_vtk:
            export_mesh_vtk_from_json(mesh_json)

    # --- plotting --------------------------------------------------------------
    show_any_plot = False
    if show_plot:
        generator.plot_mesh(mesh, show_nodes=True, show_elements=True,
                            show_holes=True, highlight_hole_boundary=True)
        generator.plot_node_labels(mesh, show_label=True)
        show_any_plot = True

    if show_periodic_matching:
        if export_mesh:
            from A001_functions.plot_mesh_functions import plot_mesh_json_periodic

            plot_mesh_json_periodic(mesh_json, show=False)
            show_any_plot = True
        else:
            warnings.warn("show_periodic_matching requires export_mesh=True")

    if show_any_plot:
        plt.show()

    print(
        f"Mesh created: {mesh.n_nodes} nodes, {mesh.n_elements} elements, "
        f"{len(generator.hole_centers)} holes (incl. partial)"
    )

    return generator, mesh

# ---------------------------------------------------------------------------
# Undeformed → Deformed mapping
# ---------------------------------------------------------------------------

def _shape_functions_quad(xi: float, eta: float) -> np.ndarray:
    """Bilinear shape functions for a 4-node quad at (xi, eta)."""
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


def _map_physical_to_natural_quad(
    x: float, y: float, nodes: np.ndarray,
    tol: float = 1e-12, max_iter: int = 50,
) -> Tuple[float, float]:
    """
    Newton-Raphson inverse mapping from physical (x, y) to natural
    coordinates (xi, eta) for a 4-node quad whose corners are *nodes*.
    """
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = _shape_functions_quad(xi, eta)
        R = np.array([N @ nodes[:, 0] - x, N @ nodes[:, 1] - y])
        if np.linalg.norm(R) < tol:
            break
        dN_dxi = np.array([
            -(1 - eta) / 4, (1 - eta) / 4, (1 + eta) / 4, -(1 + eta) / 4,
        ])
        dN_deta = np.array([
            -(1 - xi) / 4, -(1 + xi) / 4, (1 + xi) / 4, (1 - xi) / 4,
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
    Mapping is affine so a single linear solve suffices.
    """
    x1, y1 = nodes[0]
    x2, y2 = nodes[1]
    x3, y3 = nodes[2]
    J = np.array([[x2 - x1, x3 - x1],
                   [y2 - y1, y3 - y1]])
    rhs = np.array([x - x1, y - y1])
    xi_eta = np.linalg.solve(J, rhs)
    return float(xi_eta[0]), float(xi_eta[1])


def _point_in_tri(xi: float, eta: float, tol: float = 1e-8) -> bool:
    """Check if natural coordinates are inside the reference triangle."""
    return xi >= -tol and eta >= -tol and (xi + eta) <= 1.0 + tol


def _dist_outside_tri(xi: float, eta: float) -> float:
    """Distance metric for a point outside the reference triangle.

    Returns 0.0 when (xi, eta) is inside, positive otherwise.
    """
    return max(0.0, -xi) + max(0.0, -eta) + max(0.0, xi + eta - 1.0)


def _get_element_nodes_at(DATA_C2: dict, element_key: str, ti_key: str) -> np.ndarray:
    """Return (n, 2) node coordinates of element *element_key* at time *ti_key*.

    Works for both triangular (3-node) and quadrilateral (4-node) elements.

    Parameters
    ----------
    element_key : str
        1-based string key into ``DATA_C2['elements']``, e.g. ``'1'``.
    ti_key : str
        1-based string key; converted to 0-based index for
        ``DATA_C2['nodes_time']`` (a list of dicts), e.g. ``'1'`` → index 0.
    """
    elem = DATA_C2['elements'][element_key]
    nt = DATA_C2['nodes_time'][int(ti_key) - 1]
    return np.array([nt[str(n)] for n in elem], dtype=float)


def map_undeformed_to_deformed(
    x: float,
    y: float,
    ti: int,
    DATA_C2: dict,
    element_idx: Optional[int] = None,
) -> dict:
    """
    Map a point ``(x, y)`` from the **undeformed** configuration (t = 0)
    to the **deformed** configuration at time-step *ti*.

    Strategy
    --------
    1. Find the quad element that contains ``(x, y)`` in the undeformed
       mesh (``nodes_time[0]``).
    2. Compute the natural coordinates ``(xi, eta)`` inside that element.
    3. Evaluate the same shape functions at ``(xi, eta)`` using the
       **deformed** node positions (``nodes_time[ti]``) to obtain the
       deformed coordinates ``(x_def, y_def)``.

    If ``(x, y)`` coincides exactly with a mesh node the function returns
    that node's deformed position (no interpolation error).

    Parameters
    ----------
    x, y : float
        Physical coordinates in the undeformed configuration.
    ti : int
        Target time-step index (0-based into ``DATA_C2['t']``).
    DATA_C2 : dict
        Must contain ``'nodes_time'``, ``'elements'``, and ``'t'``.
    element_idx : int, optional
        If you already know which element contains ``(x, y)`` pass it
        here to skip the search.

    Returns
    -------
    dict
        ``{'x_def': float, 'y_def': float, 'element_idx': int,
          'xi': float, 'eta': float}``

    Raises
    ------
    ValueError
        If the point cannot be located in any element.
    """
    # --- locate the element in the UNDEFORMED configuration (ti='1') --------
    if element_idx is not None:
        candidates = [str(element_idx + 1)] if isinstance(element_idx, int) else [element_idx]
    else:
        candidates = sorted(DATA_C2['elements'].keys(), key=int)

    best_elem = None
    best_xi, best_eta = None, None
    best_dist = np.inf

    for ek in candidates:
        nodes_undef = _get_element_nodes_at(DATA_C2, ek, '1')
        n_nodes = len(DATA_C2['elements'][ek])

        if n_nodes == 3:
            xi, eta = _map_physical_to_natural_tri(x, y, nodes_undef)
            if _point_in_tri(xi, eta, tol=1e-8):
                best_elem = ek
                best_xi, best_eta = xi, eta
                break
            dist = _dist_outside_tri(xi, eta)
        else:
            xi, eta = _map_physical_to_natural_quad(x, y, nodes_undef)
            if abs(xi) <= 1.0 + 1e-8 and abs(eta) <= 1.0 + 1e-8:
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
            f"Could not locate point ({x}, {y}) in any undeformed element."
        )

    # --- evaluate position in the DEFORMED configuration --------------------
    ti_key = str(ti + 1)
    nodes_def = _get_element_nodes_at(DATA_C2, best_elem, ti_key)
    n_best = len(DATA_C2['elements'][best_elem])
    if n_best == 3:
        N = _shape_functions_tri(best_xi, best_eta)
    else:
        N = _shape_functions_quad(best_xi, best_eta)
    x_def = float(N @ nodes_def[:, 0])
    y_def = float(N @ nodes_def[:, 1])

    return {
        'x_def': x_def,
        'y_def': y_def,
        'element_idx': best_elem,
        'xi': best_xi,
        'eta': best_eta,
    }


# ===========================================================================
# Random Mesh with Varying Hole Sizes
# ===========================================================================

@dataclass
class MeshConfigRand:
    """
    Configuration for random mesh generation with varying hole sizes.

    Attributes:
        domain_size: Side length of the square domain.
        porosity: Target porosity (hole area / inner area), where inner area
            excludes the solid edge strips.
        min_hole_size: Minimum hole **diameter**.
        max_hole_size: Maximum hole **diameter**.
        min_distance_between_holes: Minimum edge-to-edge distance between
            holes.  ``0`` means overlap is allowed.
        seed: Random seed for reproducible results.
        edge_left/right/bottom/top: Width of solid edge strips to add outside
            the porous zone.  Moved here from the meshing-function call so
            that porosity is always interpreted relative to the inner domain.
    """
    domain_size: float
    porosity: float
    min_hole_size: float        # diameter
    max_hole_size: float        # diameter
    min_distance_between_holes: float
    seed: int
    edge_left: float = 0.0
    edge_right: float = 0.0
    edge_bottom: float = 0.0
    edge_top: float = 0.0
    hole_size_distribution: str = 'normal'
    """Sampling distribution for hole diameters.
    Accepted values:
      ``'normal'``      – truncated normal centred at mid-range (default).
      ``'uniform'``     – flat probability across [min, max].
      ``'right_skew'``  – skewed toward small holes (Beta(2, 2*skew_strength)).
      ``'left_skew'``   – skewed toward large holes (Beta(2*skew_strength, 2)).
    """
    hole_size_skew_strength: float = 2.5
    """Controls the degree of skewness when ``hole_size_distribution`` is
    ``'right_skew'`` or ``'left_skew'``.

    The Beta distribution parameters are derived as:
      - ``right_skew``: Beta(2, 2 * skew_strength)  – higher → more small holes.
      - ``left_skew``:  Beta(2 * skew_strength, 2)  – higher → more large holes.

    Default ``2.5`` gives Beta(2, 5) / Beta(5, 2) (mild-to-moderate skew).
    Values around ``1.0`` approach uniform; values above ``5`` give strong skew.
    Has no effect for ``'normal'`` or ``'uniform'`` distributions.
    """
    placement_algorithm: str = 'rsa'
    """Hole-placement algorithm.  All three guarantee a non-overlapping packing
    that respects ``min_distance_between_holes`` and wrap correctly across
    periodic boundaries.

    ``'rsa'`` – Random Sequential Addition (default).  Fast, fully random;
    jams near ~55 % porosity.

    ``'ls'``  – Jittered triangular-lattice packing with Gauss–Seidel radius
    fitting.  The densest, most uniform option (quasi-ordered); approaches the
    hexagonal-packing limit as the internal jitter is reduced.

    ``'vgp'`` – Void-Guided Placement.  At each step the grid point with the
    largest clearance from existing hole edges and walls is chosen as the next
    hole centre.  Produces spatially uniform distributions.  No extra
    parameters required.
    """
    ls_max_steps: int = 3000
    """Deprecated/unused: retained for backward compatibility with older
    configs.  The current ``'ls'`` algorithm is lattice-based and does not use
    growth-iteration tuning."""
    ls_resolve_iters: int = 80
    """Deprecated/unused (see :attr:`ls_max_steps`)."""
    ls_growth_rate: float = 0.02
    """Deprecated/unused (see :attr:`ls_max_steps`)."""


# ---------------------------------------------------------------------------
# Multi-radii helper: Cartesian grid
# ---------------------------------------------------------------------------

def _generate_cartesian_grid_mesh_multi_radii(
    domain_size: float,
    n_cols: int,
    n_rows: int,
    hole_centers: Optional[np.ndarray] = None,
    hole_radii: Optional[np.ndarray] = None,
    remove_edge_nodes: bool = True,
) -> "GraphMeshData":
    """
    ``generate_cartesian_grid_mesh`` variant that accepts per-hole radii.
    """
    if n_cols is None or n_rows is None:
        raise ValueError("grid_n and grid_m must both be provided")
    if n_cols < 2 or n_rows < 2:
        raise ValueError("grid_n and grid_m must both be at least 2")

    x_coords = np.linspace(0.0, domain_size, n_cols)
    y_coords = np.linspace(domain_size, 0.0, n_rows)

    active_idx = -np.ones((n_rows, n_cols), dtype=int)
    nodes: List[List[float]] = []
    node_ids: List[int] = []

    centers = None
    radii_sq = None
    if hole_centers is not None and len(hole_centers) > 0:
        centers = np.asarray(hole_centers, dtype=float)
        if hole_radii is not None and len(hole_radii) > 0:
            tol = max(domain_size, 1.0) * 1e-12
            radii_sq = (np.asarray(hole_radii, dtype=float) - tol) ** 2
            radii_sq = np.maximum(radii_sq, 0.0)

    for row, y in enumerate(y_coords):
        for col, x in enumerate(x_coords):
            if remove_edge_nodes and (
                row == 0 or row == n_rows - 1 or col == 0 or col == n_cols - 1
            ):
                continue

            if centers is not None and radii_sq is not None:
                dist_sq = np.sum((centers - np.array([x, y])) ** 2, axis=1)
                if np.any(dist_sq < radii_sq):
                    continue

            active_idx[row, col] = len(nodes)
            nodes.append([x, y])
            node_ids.append(0)

    bars: List[List[int]] = []
    bar_numbers: List[int] = []
    bar_number = 0

    for row in range(n_rows):
        for col in range(n_cols - 1):
            ni = active_idx[row, col]
            nf = active_idx[row, col + 1]
            if ni >= 0 and nf >= 0:
                bars.append([ni, nf])
                bar_numbers.append(bar_number)
                bar_number += 1

    for row in range(n_rows - 1):
        for col in range(n_cols):
            ni = active_idx[row, col]
            nf = active_idx[row + 1, col]
            if ni >= 0 and nf >= 0:
                bars.append([ni, nf])
                bar_numbers.append(bar_number)
                bar_number += 1

    return GraphMeshData(
        nodes=np.array(nodes, dtype=float) if nodes else np.empty((0, 2), dtype=float),
        node_ids=np.array(node_ids, dtype=int),
        bars=np.array(bars, dtype=int) if bars else np.empty((0, 2), dtype=int),
        bar_numbers=np.array(bar_numbers, dtype=int),
    )


# ---------------------------------------------------------------------------
# Multi-radii helper: hexagonal gridhex
# ---------------------------------------------------------------------------

def _generate_hexagonal_gridhex_mesh_multi_radii(
    domain_size: float,
    hexagon_size: float,
    hole_centers=None,
    hole_radii=None,
    pointy_top: bool = True,
    remove_edge_nodes: bool = True,
    delete_isolated_bars: bool = False,
) -> "GraphMeshData":
    """
    ``generate_hexagonal_gridhex_mesh`` variant that accepts per-hole radii.
    """
    R = hexagon_size / 2.0
    r_hex = R * np.sqrt(3.0) / 2.0
    L = domain_size

    # 1. Generate hex centres covering [0, L]²
    if pointy_top:
        sq3R      = np.sqrt(3.0) * R
        col_pitch = sq3R
        row_pitch = 1.5 * R
        row_offset = sq3R / 2.0
        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3
        hex_centres = []
        for row in range(-2, n_rows):
            cy = row * row_pitch
            for col in range(-2, n_cols):
                cx = col * col_pitch + (row % 2) * row_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))
        vertex_angles   = np.deg2rad([30, 90, 150, 210, 270, 330])
        midpoint_angles = np.deg2rad([ 0, 60, 120, 180, 240, 300])
    else:
        sq3R       = np.sqrt(3.0) * R
        col_pitch  = 1.5 * R
        row_pitch  = sq3R
        col_offset = sq3R / 2.0
        n_cols = int(np.ceil(L / col_pitch)) + 3
        n_rows = int(np.ceil(L / row_pitch)) + 3
        hex_centres = []
        for col in range(-2, n_cols):
            cx = col * col_pitch
            for row in range(-2, n_rows):
                cy = row * row_pitch + (col % 2) * col_offset
                if cx > L + R or cx < -R or cy > L + R or cy < -R:
                    continue
                hex_centres.append((cx, cy))
        vertex_angles   = np.deg2rad([ 0, 60, 120, 180, 240, 300])
        midpoint_angles = np.deg2rad([30, 90, 150, 210, 270, 330])

    vertex_dirs   = np.stack([np.cos(vertex_angles),
                               np.sin(vertex_angles)], axis=1)
    midpoint_dirs = np.stack([np.cos(midpoint_angles),
                               np.sin(midpoint_angles)], axis=1)

    # 2. Collect unique nodes
    ROUND = 9
    pos_to_idx: dict = {}
    node_xy:    list = []
    node_label: list = []
    raw_bars:   list = []

    def _add_node(x, y, label):
        k = (round(x, ROUND), round(y, ROUND))
        if k not in pos_to_idx:
            pos_to_idx[k] = len(node_xy)
            node_xy.append([x, y])
            node_label.append(label)
        return pos_to_idx[k]

    for (cx, cy) in hex_centres:
        ci = _add_node(cx, cy, 1)
        for d in vertex_dirs:
            px, py = cx + R * d[0], cy + R * d[1]
            pi = _add_node(px, py, 2)
            raw_bars.append((ci, pi))
        for d in midpoint_dirs:
            px, py = cx + r_hex * d[0], cy + r_hex * d[1]
            pi = _add_node(px, py, 2)
            raw_bars.append((ci, pi))

    nodes_arr  = np.array(node_xy,    dtype=float)
    labels_arr = np.array(node_label, dtype=int)

    # 3. Keep mask: domain interior
    tol = L * 1e-9
    in_domain = (
        (nodes_arr[:, 0] >= -tol) & (nodes_arr[:, 0] <= L + tol) &
        (nodes_arr[:, 1] >= -tol) & (nodes_arr[:, 1] <= L + tol)
    )
    keep = in_domain.copy()

    if remove_edge_nodes:
        on_boundary = (
            (nodes_arr[:, 0] <= tol) | (nodes_arr[:, 0] >= L - tol) |
            (nodes_arr[:, 1] <= tol) | (nodes_arr[:, 1] >= L - tol)
        )
        keep &= ~on_boundary

    # 4. Remove nodes inside holes (per-hole radii)
    if hole_centers is not None and len(hole_centers) > 0:
        centers_arr = np.asarray(hole_centers, dtype=float)
        if hole_radii is not None and len(hole_radii) > 0:
            radii_arr = np.asarray(hole_radii, dtype=float)
            tol_r = L * 1e-12
            radii_sq = (radii_arr - tol_r) ** 2
            radii_sq = np.maximum(radii_sq, 0.0)
            dx = nodes_arr[:, 0:1] - centers_arr[:, 0]
            dy = nodes_arr[:, 1:2] - centers_arr[:, 1]
            dist_sq = dx ** 2 + dy ** 2
            inside = np.any(dist_sq < radii_sq[np.newaxis, :], axis=1)
            keep &= ~inside

    # 5. Re-index
    old_to_new           = np.full(len(nodes_arr), -1, dtype=int)
    old_to_new[keep]     = np.arange(keep.sum(), dtype=int)
    final_nodes  = nodes_arr[keep]
    final_labels = labels_arr[keep]

    # 6. Filter bars
    final_bars:    list = []
    final_bar_num: list = []
    bar_counter         = 0
    seen_bars:     set  = set()
    for (a, b) in raw_bars:
        na, nb = old_to_new[a], old_to_new[b]
        if na < 0 or nb < 0:
            continue
        key = (min(na, nb), max(na, nb))
        if key in seen_bars:
            continue
        seen_bars.add(key)
        final_bars.append([na, nb])
        final_bar_num.append(bar_counter)
        bar_counter += 1

    bars_arr    = (np.array(final_bars, dtype=int)
                   if final_bars else np.empty((0, 2), dtype=int))
    bar_num_arr = (np.array(final_bar_num, dtype=int)
                   if final_bar_num else np.empty((0,), dtype=int))

    # 7. Remove isolated bars/nodes
    if delete_isolated_bars and len(bars_arr) > 0:
        (final_nodes, final_labels,
         bars_arr, bar_num_arr,
         n_rem_n, n_rem_b) = _remove_isolated_gridhex_nodes(
            final_nodes, final_labels, bars_arr, bar_num_arr)
        print(f"  Isolated-bar removal: {n_rem_n} nodes and "
              f"{n_rem_b} bars removed.")

    return GraphMeshData(
        nodes=final_nodes,
        node_ids=final_labels,
        bars=bars_arr,
        bar_numbers=bar_num_arr,
    )


# ---------------------------------------------------------------------------
# Geometry helper: exact area of a disk clipped to an axis-aligned rectangle
# ---------------------------------------------------------------------------

def _disk_rect_area(
    cx: float, cy: float, r: float,
    x0: float, x1: float, y0: float, y1: float,
) -> float:
    """Area of the disk (centre ``(cx, cy)``, radius ``r``) intersected with the
    axis-aligned rectangle ``[x0, x1] x [y0, y1]``.

    Any bound may be ``+/- np.inf`` to express "no clipping" on that side (used
    for periodic directions, where a hole that leaves the cell re-enters on the
    opposite side and its full area still belongs to the unit cell).

    Holes are non-overlapping by construction, so summing this over all holes
    gives the exact total void area with no double counting.
    """
    if r <= 0.0:
        return 0.0
    # Fully inside the rectangle -> full disk.
    if (cx - r >= x0 and cx + r <= x1 and cy - r >= y0 and cy + r <= y1):
        return float(np.pi * r * r)
    # Fully outside the rectangle -> nothing.
    if (cx + r <= x0 or cx - r >= x1 or cy + r <= y0 or cy - r >= y1):
        return 0.0
    # Partial overlap: integrate the clipped vertical extent over x.
    a = max(x0, cx - r)
    b = min(x1, cx + r)
    if b <= a:
        return 0.0
    n = 2000
    xs = np.linspace(a, b, n + 1)
    h = np.sqrt(np.maximum(r * r - (xs - cx) ** 2, 0.0))
    upper = np.minimum(y1, cy + h)
    lower = np.maximum(y0, cy - h)
    height = np.maximum(0.0, upper - lower)
    return float(np.trapz(height, xs))


# ---------------------------------------------------------------------------
# RandomMeshGenerator
# ---------------------------------------------------------------------------

class RandomMeshGenerator(HexagonalMeshGenerator):
    """
    Mesh generator that places circular holes **randomly** within a square
    domain, with per-hole radii drawn from a uniform distribution.

    Inherits visualisation, Voronoi, Delaunay, graph-mesh and export
    methods from :class:`HexagonalMeshGenerator`.  Overrides hole
    placement, mesh generation and plotting to handle varying radii.
    """

    # ---- construction ---------------------------------------------------

    def __init__(
        self,
        domain_size: float,
        porosity: float,
        min_hole_diameter: float,
        max_hole_diameter: float,
        min_distance: float,
        seed: int,
        allow_cut_left: bool = True,
        allow_cut_right: bool = True,
        allow_cut_bottom: bool = True,
        allow_cut_top: bool = True,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
        edge_left: float = 0.0,
        edge_right: float = 0.0,
        edge_bottom: float = 0.0,
        edge_top: float = 0.0,
        hole_size_distribution: str = 'normal',
        hole_size_skew_strength: float = 2.5,
        placement_algorithm: str = 'rsa',
        ls_max_steps: int = 3000,
        ls_resolve_iters: int = 80,
        ls_growth_rate: float = 0.02,
    ):
        # Store parameters (do NOT call super().__init__ because that
        # computes hexagonal geometry).
        self.domain_size = domain_size
        self.porosity = porosity
        self.min_hole_radius = min_hole_diameter / 2.0
        self.max_hole_radius = max_hole_diameter / 2.0
        self.min_distance = min_distance
        self.seed = seed
        self.center_domain = True
        self.allow_cut_left = allow_cut_left
        self.allow_cut_right = allow_cut_right
        self.allow_cut_bottom = allow_cut_bottom
        self.allow_cut_top = allow_cut_top
        self.edge_left   = float(edge_left)
        self.edge_right  = float(edge_right)
        self.edge_bottom = float(edge_bottom)
        self.edge_top    = float(edge_top)
        self.hole_size_distribution = hole_size_distribution
        self.hole_size_skew_strength = float(hole_size_skew_strength)
        self.placement_algorithm = placement_algorithm
        self.ls_max_steps    = int(ls_max_steps)
        self.ls_resolve_iters = int(ls_resolve_iters)
        self.ls_growth_rate  = float(ls_growth_rate)

        # Place holes
        self.hole_centers, self.hole_radii = self._place_random_holes(
            periodic_lr=periodic_lr, periodic_tb=periodic_tb,
        )

        # Build a representative HexagonalPackingGeometry so inherited
        # methods that rely on self.geometry keep working.
        n_holes = len(self.hole_centers)
        if n_holes > 0:
            avg_r = float(np.mean(self.hole_radii))
            approx_spacing = domain_size / max(int(np.sqrt(n_holes)), 1)
        else:
            avg_r = (self.min_hole_radius + self.max_hole_radius) / 2.0
            approx_spacing = domain_size / 10.0

        self.geometry = HexagonalPackingGeometry(
            horizontal_spacing=approx_spacing,
            vertical_spacing=approx_spacing * np.sqrt(3.0) / 2.0,
            hole_radius=avg_r,
            porosity=porosity,
        )
        self.n_holes_width = max(int(np.sqrt(n_holes)), 1)
        self.horizontal_spacing = approx_spacing

    # ---- shared placement / porosity helpers -----------------------------

    def _edge_widths(self) -> Tuple[float, float, float, float]:
        """Solid edge-strip widths ``(left, right, bottom, top)``."""
        return (float(self.edge_left), float(self.edge_right),
                float(self.edge_bottom), float(self.edge_top))

    def _total_domain_area(self) -> float:
        """Area of the final square measured in the porous (pre-rescale) frame.

        Edge strips are added *outside* ``[0, L]^2`` and the whole geometry is
        then rescaled back to ``[0, L]^2``.  In the porous frame that final
        square is the expanded rectangle ``(L+wl+wr) x (L+wb+wt)``; the rescale
        maps it to area ``L^2``.  Because both void and total area scale by the
        same factor, ``void/total`` is invariant under the rescale, so a
        porosity computed here equals ``final_void_area / L^2``.
        """
        L = self.domain_size
        wl, wr, wb, wt = self._edge_widths()
        return (L + wl + wr) * (L + wb + wt)

    def _target_void_area(self) -> float:
        """Void area (porous frame) such that, after the edge rescale,
        ``final_void_area / L^2 == porosity``."""
        return self.porosity * self._total_domain_area()

    @staticmethod
    def _min_image(d, L, periodic):
        """Minimum-image displacement along one axis (no-op when not periodic).
        Works element-wise on NumPy arrays as well as scalars."""
        if periodic:
            return d - L * np.round(d / L)
        return d

    def _periodic_mirrors(self, cx, cy, r, periodic_lr, periodic_tb):
        """Mirror centres of a primary hole that straddles a periodic boundary.

        A primary hole lives in ``[0, L)``; if it pokes past a periodic edge it
        re-enters on the opposite side, so a duplicate (mirror) disk is needed
        for the periodic FE mesh.  Returns the list of extra ``(x, y)`` centres
        (the primary itself is not included)."""
        L = self.domain_size
        xs = [cx]
        ys = [cy]
        if periodic_lr:
            if cx - r < 0.0:
                xs.append(cx + L)
            if cx + r > L:
                xs.append(cx - L)
        if periodic_tb:
            if cy - r < 0.0:
                ys.append(cy + L)
            if cy + r > L:
                ys.append(cy - L)
        mirrors = []
        for i, mx in enumerate(xs):
            for j, my in enumerate(ys):
                if i == 0 and j == 0:
                    continue
                mirrors.append((mx, my))
        return mirrors

    def _max_theoretical_porosity(self, periodic_lr: bool,
                                  periodic_tb: bool) -> float:
        """Maximum porosity attainable with these constraints, from the
        densest hexagonal packing of equal disks.

        The disks have the largest allowed radius ``r_max`` and an edge-to-edge
        gap equal to ``min_distance`` (the binding lower bound on spacing), so
        the triangular-lattice packing fraction is

            phi_hex = 2*pi*r_max^2 / (sqrt(3) * (2*r_max + min_distance)^2).

        This is then scaled by the fraction of the final square the voids may
        occupy.  On a side that carries a solid edge strip and is *not* allowed
        to be cut, the voids are confined to the porous zone; otherwise they may
        reach the outer boundary.  Hence the result decreases when edges are
        present and the voids may not cut them, and rises back to ``phi_hex``
        when cutting is allowed."""
        r_max = self.max_hole_radius
        d = self.min_distance
        phi_hex = 2.0 * np.pi * r_max ** 2 / (np.sqrt(3.0) * (2.0 * r_max + d) ** 2)

        L = self.domain_size
        wl, wr, wb, wt = self._edge_widths()
        left   = 0.0 if (wl > 0 and not self.allow_cut_left)   else -wl
        right  = L   if (wr > 0 and not self.allow_cut_right)  else L + wr
        bottom = 0.0 if (wb > 0 and not self.allow_cut_bottom) else -wb
        top    = L   if (wt > 0 and not self.allow_cut_top)    else L + wt
        avail = max(right - left, 0.0) * max(top - bottom, 0.0)
        total = self._total_domain_area()
        return float(phi_hex * avail / total) if total > 0 else 0.0

    def _report_porosity(self, centers, radii, periodic_lr, periodic_tb,
                         label: str = "") -> Tuple[float, float]:
        """Print and return ``(achieved, max_theoretical)`` porosity.

        ``centers``/``radii`` must be the **primary** holes only (no periodic
        mirrors).  Achieved porosity is the true clipped void area divided by
        the final square area, i.e. ``final_void_area / L^2``."""
        L = self.domain_size
        wl, wr, wb, wt = self._edge_widths()
        total = self._total_domain_area()
        # No clipping across periodic seams (wrapped area stays in the cell);
        # clip to the outer boundary on non-periodic sides.
        x0 = -np.inf if periodic_lr else -wl
        x1 =  np.inf if periodic_lr else L + wr
        y0 = -np.inf if periodic_tb else -wb
        y1 =  np.inf if periodic_tb else L + wt
        void = 0.0
        for (cx, cy), r in zip(centers, radii):
            void += _disk_rect_area(cx, cy, r, x0, x1, y0, y1)
        achieved = void / total if total > 0 else 0.0
        max_phi = self._max_theoretical_porosity(periodic_lr, periodic_tb)
        tag = f"{label} " if label else ""
        print(f"  {tag}porosity:  target={self.porosity:.4f}   "
              f"achieved={achieved:.4f}   max_theoretical={max_phi:.4f}   "
              f"(holes={len(centers)})")
        if self.porosity > max_phi + 1e-9:
            warnings.warn(
                f"Requested porosity {self.porosity:.4f} exceeds the maximum "
                f"theoretical porosity {max_phi:.4f} for these constraints "
                f"(max hole diameter {2 * self.max_hole_radius:.4g}, "
                f"min distance {self.min_distance:.4g}); achieved porosity will "
                f"fall short of the target."
            )
        return achieved, max_phi

    # ---- random placement ------------------------------------------------

    def _place_random_holes(
        self,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Place holes randomly until the target porosity is approximately
        reached.  Respects minimum edge-to-edge distance between holes
        and ``allow_cut_*`` flags.

        Strategy
        --------
        1. **Truncated-normal radii** – all hole radii are pre-sampled
           from a truncated normal distribution centred at
           ``(min_r + max_r) / 2``, clipped to ``[min_r, max_r]``.
           This keeps the diameter histogram approximately Gaussian.
        2. **Large-to-small placement order** – the pre-sampled radii
           are sorted in descending order so that the biggest holes are
           placed first, filling the domain efficiently before smaller
           holes pack the remaining gaps.
        3. **KD-tree acceleration** – a ``cKDTree`` is used for
           collision checks (``O(log n)`` instead of ``O(n)``).

        When *periodic_lr* / *periodic_tb* is ``True``, any hole that
        extends past a periodic boundary is automatically mirrored to
        the opposite side.
        """
        # Dispatch to the configured placement algorithm
        algo = getattr(self, 'placement_algorithm', 'rsa').strip().lower()
        if algo == 'ls':
            return self._place_holes_ls(periodic_lr=periodic_lr,
                                        periodic_tb=periodic_tb)
        if algo == 'vgp':
            return self._place_holes_vgp(periodic_lr=periodic_lr,
                                         periodic_tb=periodic_tb)

        # --- RSA (Random Sequential Addition) ---
        rng = np.random.default_rng(self.seed)
        L = self.domain_size
        # Target void area is set so that, after the outside-edge rescale, the
        # final void area divided by the final square area (L^2, including the
        # rescaled edge strips) equals the requested porosity.
        target_area = self._target_void_area()

        min_r = self.min_hole_radius
        max_r = self.max_hole_radius
        min_dist = self.min_distance

        # Clip bounds for void-area bookkeeping (no clip across periodic seams).
        wl, wr, wb, wt = self._edge_widths()
        cx0 = -np.inf if periodic_lr else -wl
        cx1 =  np.inf if periodic_lr else L + wr
        cy0 = -np.inf if periodic_tb else -wb
        cy1 =  np.inf if periodic_tb else L + wt

        # Primary holes only (periodic duplicates are appended at the very end).
        centers: List[List[float]] = []
        radii:   List[float]       = []
        current_area = 0.0

        margin = max_r  # allowed overshoot past a wall when cutting is enabled

        # --- pre-sample radii from the requested distribution --------------
        mean_r = (min_r + max_r) / 2.0
        mean_area = np.pi * mean_r ** 2
        n_estimate = int(np.ceil(target_area / mean_area * 1.5)) + 50
        all_radii = np.sort(self._sample_radii(n_estimate, rng))[::-1]

        # --- KD-tree bookkeeping (rebuilt after every acceptance) ----------
        tree: Optional[cKDTree] = None
        arr: Optional[np.ndarray] = None

        def _rebuild_tree():
            nonlocal tree, arr
            if centers:
                arr = np.asarray(centers, dtype=float)
                tree = cKDTree(arr)
            else:
                arr = None
                tree = None

        def _check_no_overlap(x: float, y: float, r_new: float) -> bool:
            """True if a hole (x, y, r_new) keeps the minimum gap to every
            existing primary hole, honouring periodic wrap via the
            minimum-image convention."""
            if tree is None:
                return True
            search_r = r_new + max_r + min_dist
            # Query the point and its periodic seam images so the Euclidean
            # KD-tree also reaches wrap-around neighbours.
            qpts = [(x, y)]
            if periodic_lr:
                qpts += [(x + L, y), (x - L, y)]
            if periodic_tb:
                qpts += [(x, y + L), (x, y - L)]
            if periodic_lr and periodic_tb:
                qpts += [(x + L, y + L), (x + L, y - L),
                         (x - L, y + L), (x - L, y - L)]
            idxs: set = set()
            for q in qpts:
                idxs.update(tree.query_ball_point(q, search_r))
            if not idxs:
                return True
            idx = list(idxs)
            sub = arr[idx]
            dx = self._min_image(x - sub[:, 0], L, periodic_lr)
            dy = self._min_image(y - sub[:, 1], L, periodic_tb)
            rr = np.asarray(radii)[idx]
            return not np.any(dx * dx + dy * dy < (r_new + rr + min_dist) ** 2)

        # --- placement loop ------------------------------------------------
        max_position_attempts = 5_000   # attempts per candidate radius
        ri = 0

        while current_area < target_area and ri < len(all_radii):
            r = float(all_radii[ri])
            ri += 1

            remaining = target_area - current_area
            if np.pi * r ** 2 > remaining * 3.0:
                continue

            for _ in range(max_position_attempts):
                # --- sample a primary centre --------------------------------
                # Periodic axis: canonical position in [0, L).  Otherwise the
                # centre may overshoot a wall only where cutting is allowed.
                if periodic_lr:
                    x = rng.uniform(0.0, L)
                else:
                    x_lo = -margin if self.allow_cut_left  else 0.0
                    x_hi = L + margin if self.allow_cut_right else L
                    x = rng.uniform(x_lo, x_hi)
                if periodic_tb:
                    y = rng.uniform(0.0, L)
                else:
                    y_lo = -margin if self.allow_cut_bottom else 0.0
                    y_hi = L + margin if self.allow_cut_top    else L
                    y = rng.uniform(y_lo, y_hi)

                # --- cut / wall constraints --------------------------------
                # A hole may cross a side only where that side allows cutting —
                # periodic or not.  (Periodicity decides whether a crossing hole
                # *wraps*; it does not by itself license edge cutting.)
                if not self.allow_cut_left   and x - r < 0:  continue
                if not self.allow_cut_right  and x + r > L:  continue
                if not self.allow_cut_bottom and y - r < 0:  continue
                if not self.allow_cut_top    and y + r > L:  continue
                if not periodic_lr and not (x + r > 0 and x - r < L): continue
                if not periodic_tb and not (y + r > 0 and y - r < L): continue

                # --- minimum-distance check (minimum-image) -----------------
                if not _check_no_overlap(x, y, r):
                    continue

                # --- accept -------------------------------------------------
                centers.append([x, y])
                radii.append(r)
                current_area += _disk_rect_area(x, y, r, cx0, cx1, cy0, cy1)
                _rebuild_tree()
                break

        if not centers:
            warnings.warn("No holes were placed")
            return np.array([]).reshape(0, 2), np.array([])

        # --- report porosity on the primary holes --------------------------
        self._report_porosity(centers, radii, periodic_lr, periodic_tb,
                              label="RSA")

        # --- append periodic mirror duplicates for the FE mesh -------------
        out_centers = [list(c) for c in centers]
        out_radii   = list(radii)
        for (cx, cy), r in zip(centers, radii):
            for mx, my in self._periodic_mirrors(cx, cy, r,
                                                 periodic_lr, periodic_tb):
                if mx + r > 0 and mx - r < L and my + r > 0 and my - r < L:
                    out_centers.append([mx, my])
                    out_radii.append(r)

        return np.array(out_centers), np.array(out_radii)

    # ---- shared radius sampler -------------------------------------------

    def _sample_radii(self, N: int, rng: 'np.random.Generator') -> np.ndarray:
        """Sample *N* target hole radii from the configured distribution."""
        from scipy.stats import truncnorm, beta as beta_dist

        min_r = self.min_hole_radius
        max_r = self.max_hole_radius
        mean_r = (min_r + max_r) / 2.0
        distribution = getattr(self, 'hole_size_distribution', 'normal')
        skew_s = max(float(getattr(self, 'hole_size_skew_strength', 2.5)), 1e-3)

        _dist = distribution.strip().lower()
        if _dist == 'uniform':
            return rng.uniform(min_r, max_r, size=N).astype(float)
        elif _dist == 'right_skew':
            return np.asarray(beta_dist.rvs(
                2, 2 * skew_s, loc=min_r, scale=(max_r - min_r),
                size=N, random_state=rng), dtype=float)
        elif _dist == 'left_skew':
            return np.asarray(beta_dist.rvs(
                2 * skew_s, 2, loc=min_r, scale=(max_r - min_r),
                size=N, random_state=rng), dtype=float)
        else:  # 'normal'
            std_r = max((max_r - min_r) / 4.0, 1e-15)
            a_clip = (min_r - mean_r) / std_r
            b_clip = (max_r - mean_r) / std_r
            return np.asarray(truncnorm.rvs(
                a_clip, b_clip, loc=mean_r, scale=std_r,
                size=N, random_state=rng), dtype=float)

    # ---- 'ls': jittered-lattice dense packing ----------------------------

    def _place_holes_ls(
        self,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Dense packing via a jittered triangular lattice (high-porosity option).

        Seeds are placed on a triangular (hexagonal close-packed) lattice whose
        spacing is derived from the target porosity, perturbed by a small random
        jitter, and then each disk radius is fitted — with a Gauss–Seidel sweep
        processed largest-target-first — to the largest value that keeps the
        minimum edge-to-edge gap to every neighbour and to every hard wall.

        Because radii are only ever reduced from their targets, the result is
        guaranteed overlap-free, while the near-optimal lattice arrangement lets
        it reach a higher packing fraction than random sequential addition.
        Periodic directions use the minimum-image convention and a lattice that
        tiles the cell exactly, so the packing is seamlessly periodic.  Lower
        ``jitter`` trades randomness for density.

        The ``ls_*`` :class:`MeshConfigRand` fields are accepted for backward
        compatibility but are no longer used.
        """
        rng = np.random.default_rng(self.seed)
        L = self.domain_size
        min_r = self.min_hole_radius
        max_r = self.max_hole_radius
        min_dist = self.min_distance
        mean_r = (min_r + max_r) / 2.0

        wl, wr, wb, wt = self._edge_widths()
        total = self._total_domain_area()

        # --- triangular lattice spacing from the target porosity -----------
        # phi_local is the void fraction the lattice must reach inside the region
        # the holes may occupy (the porous square, or the whole expanded domain
        # when edge cutting is allowed) to deliver the requested final porosity.
        any_cut = (self.allow_cut_left or self.allow_cut_right or
                   self.allow_cut_bottom or self.allow_cut_top)
        region_area = total if any_cut else (L * L)
        target_area = self._target_void_area()
        phi_local = min(max(target_area / region_area, 1e-3), 0.9)
        a = mean_r * np.sqrt(2.0 * np.pi / (np.sqrt(3.0) * phi_local))
        a = max(a, 2.0 * mean_r + min_dist)       # cannot pack tighter than this
        row_pitch = a * np.sqrt(3.0) / 2.0

        # Lay out the lattice.  Along a periodic axis the lattice must tile the
        # cell exactly (spacing snapped so an integer number of cells fits, and
        # exactly that many points generated — padding there would create
        # coincident points after wrapping).  Along a non-periodic axis the grid
        # is padded and later clipped to the domain.
        if periodic_lr:
            n_cols = max(int(round(L / a)), 1)
            ax = L / n_cols
        else:
            ax = a
            n_cols = int(np.ceil(L / ax)) + 2
        if periodic_tb:
            nrow = max(int(round(L / row_pitch)), 1)
            if nrow % 2:                # even row count -> the offset pattern wraps
                nrow += 1
            ay = L / nrow
            n_rows = nrow
        else:
            ay = row_pitch
            n_rows = int(np.ceil(L / ay)) + 2

        # --- generate jittered lattice points covering [0, L]^2 ------------
        jitter = 0.06 * a
        pts = []
        for row in range(n_rows):
            y = row * ay
            xoff = (ax * 0.5) if (row % 2) else 0.0
            for col in range(n_cols):
                pts.append((col * ax + xoff, y))
        pos = np.asarray(pts, dtype=float)
        pos += rng.uniform(-jitter, jitter, pos.shape)

        if periodic_lr:
            pos[:, 0] %= L
        if periodic_tb:
            pos[:, 1] %= L
        keep = np.ones(len(pos), dtype=bool)
        if not periodic_lr:
            keep &= (pos[:, 0] >= 0.0) & (pos[:, 0] <= L)
        if not periodic_tb:
            keep &= (pos[:, 1] >= 0.0) & (pos[:, 1] <= L)
        pos = pos[keep]
        if len(pos) == 0:
            warnings.warn("LS placement: no holes were placed.")
            return np.array([]).reshape(0, 2), np.array([])

        N = len(pos)
        target_radii = self._sample_radii(N, rng)

        # --- Gauss-Seidel radius fitting (positions fixed) -----------------
        # Each disk takes the largest radius that still keeps the minimum gap to
        # every neighbour (minimum-image) and to every hard wall.  Sequential
        # in-place updates — processed largest-target first — avoid the mutual
        # over-shrinking a simultaneous (Jacobi) update would cause and converge
        # to a dense, strictly valid assignment.
        dx = self._min_image(pos[:, 0][:, None] - pos[:, 0][None, :], L, periodic_lr)
        dy = self._min_image(pos[:, 1][:, None] - pos[:, 1][None, :], L, periodic_tb)
        D = np.sqrt(dx * dx + dy * dy)
        np.fill_diagonal(D, np.inf)
        radii = target_radii.copy()
        order = np.argsort(-target_radii)
        for _ in range(80):
            changed = 0.0
            for i in order:
                cap = float(np.min(D[i] - min_dist - radii))
                # Confine to any side that disallows cutting (periodic or not):
                # the disk may not poke past it.
                if not self.allow_cut_left:   cap = min(cap, pos[i, 0])
                if not self.allow_cut_right:  cap = min(cap, L - pos[i, 0])
                if not self.allow_cut_bottom: cap = min(cap, pos[i, 1])
                if not self.allow_cut_top:    cap = min(cap, L - pos[i, 1])
                new_r = min(float(target_radii[i]), max(cap, 0.0))
                changed = max(changed, abs(new_r - radii[i]))
                radii[i] = new_r
            if changed <= 1e-12:
                break

        # Drop disks that had to shrink to ~nothing or fell outside the domain.
        keep = radii > max(min_r * 0.25, 1e-6)
        keep &= (pos[:, 0] + radii > 1e-9) & (pos[:, 0] - radii < L - 1e-9)
        keep &= (pos[:, 1] + radii > 1e-9) & (pos[:, 1] - radii < L - 1e-9)
        pos, radii = pos[keep], radii[keep]

        if len(pos) == 0:
            warnings.warn("LS placement: no holes were placed.")
            return np.array([]).reshape(0, 2), np.array([])

        centers = pos.tolist()
        radii_l = radii.tolist()

        # --- report porosity on the primary holes --------------------------
        self._report_porosity(centers, radii_l, periodic_lr, periodic_tb,
                              label="LS")

        # --- append periodic mirror duplicates for the FE mesh -------------
        out_centers = [list(c) for c in centers]
        out_radii   = list(radii_l)
        for (cx, cy), r in zip(centers, radii_l):
            for mx, my in self._periodic_mirrors(cx, cy, r,
                                                 periodic_lr, periodic_tb):
                if mx + r > 0 and mx - r < L and my + r > 0 and my - r < L:
                    out_centers.append([mx, my])
                    out_radii.append(r)

        return np.array(out_centers), np.array(out_radii)

    # ---- Void-Guided Placement algorithm ---------------------------------

    def _place_holes_vgp(
        self,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Void-Guided Placement (VGP) algorithm.

        A uniform grid of candidate positions is maintained over the domain.
        At each step the grid point with the largest *effective clearance*
        – distance to the nearest existing hole edge, clamped by any active
        wall constraints – is selected as the centre for the next hole.
        This deterministically fills the largest voids first, yielding more
        spatially uniform distributions and higher packing efficiency than
        pure RSA.

        Randomness enters only through hole-size sampling (same
        ``_sample_radii`` helper as RSA/LS) and a small sub-cell jitter
        applied after the best grid point is selected.

        Accepts the same parameters as RSA/LS: ``domain_size``,
        ``porosity``, ``min/max_hole_size``, ``min_distance_between_holes``,
        ``edge_left/right/bottom/top``, ``hole_size_distribution``, and
        ``hole_size_skew_strength``.  No additional fields are needed.
        """
        rng = np.random.default_rng(self.seed)
        L = self.domain_size
        target_area = self._target_void_area()

        min_r = self.min_hole_radius
        max_r = self.max_hole_radius
        min_dist = self.min_distance

        wl, wr, wb, wt = self._edge_widths()
        cx0 = -np.inf if periodic_lr else -wl
        cx1 =  np.inf if periodic_lr else L + wr
        cy0 = -np.inf if periodic_tb else -wb
        cy1 =  np.inf if periodic_tb else L + wt

        # Grid of candidate centres over the whole porous square [0, L]^2.
        # (Edge strips are added *outside* this square and the mesh is rescaled
        #  afterwards, so the placement region is the full square, not a shrunk
        #  inner zone.)
        cell_size = max(min_r * 0.5, L / 800.0)
        grid_n = max(int(np.ceil(L / cell_size)), 40)
        cell_size = L / grid_n
        half = cell_size * 0.5
        xs = np.arange(grid_n) * cell_size + half
        ys = np.arange(grid_n) * cell_size + half
        gx, gy = np.meshgrid(xs, ys)
        cand = np.column_stack([gx.ravel(), gy.ravel()])  # (M, 2)

        # Static wall-clearance field.  A side constrains placement wherever it
        # disallows cutting (periodic or not): the hole may not poke past it.
        # Cut-allowed sides impose no clearance (holes may cross / wrap).
        wall_clr = np.full(len(cand), np.inf)
        if not self.allow_cut_left:
            wall_clr = np.minimum(wall_clr, cand[:, 0])
        if not self.allow_cut_right:
            wall_clr = np.minimum(wall_clr, L - cand[:, 0])
        if not self.allow_cut_bottom:
            wall_clr = np.minimum(wall_clr, cand[:, 1])
        if not self.allow_cut_top:
            wall_clr = np.minimum(wall_clr, L - cand[:, 1])

        # Pre-sample radii sorted largest-first.
        mean_r = (min_r + max_r) / 2.0
        n_est  = int(np.ceil(target_area / (np.pi * mean_r ** 2) * 1.5)) + 50
        all_radii = np.sort(self._sample_radii(n_est, rng))[::-1]

        centers: List[List[float]] = []   # primary holes only
        radii:   List[float]       = []
        current_area = 0.0

        # Dynamic hole-clearance field: distance from each grid point to the
        # nearest existing hole *edge*, using the minimum-image distance so the
        # field wraps correctly across periodic seams.
        hole_clr = np.full(len(cand), np.inf)

        def _grid_clearance(px, py):
            dx = self._min_image(cand[:, 0] - px, L, periodic_lr)
            dy = self._min_image(cand[:, 1] - py, L, periodic_tb)
            return np.sqrt(dx * dx + dy * dy)

        def _overlaps(px, py, r_new):
            if not centers:
                return False
            arr = np.asarray(centers)
            rad = np.asarray(radii)
            dx = self._min_image(px - arr[:, 0], L, periodic_lr)
            dy = self._min_image(py - arr[:, 1], L, periodic_tb)
            return bool(np.any(dx * dx + dy * dy < (rad + r_new + min_dist) ** 2))

        jitter_scale = min(half * 0.9, max_r * 0.10)

        ri = 0
        while current_area < target_area and ri < len(all_radii):
            r = float(all_radii[ri])
            ri += 1

            remaining = target_area - current_area
            if np.pi * r ** 2 > remaining * 3.0:
                continue

            # Effective clearance = min(hole clearance, wall clearance) - gap
            eff = np.minimum(hole_clr, wall_clr) - min_dist
            valid_idxs = np.where(eff >= r)[0]
            if valid_idxs.size == 0:
                continue

            best_idx = valid_idxs[np.argmax(eff[valid_idxs])]
            bx, by   = float(cand[best_idx, 0]), float(cand[best_idx, 1])

            # Sub-cell jitter for variety
            cx = bx + rng.uniform(-jitter_scale, jitter_scale)
            cy = by + rng.uniform(-jitter_scale, jitter_scale)
            cx = float(np.clip(cx, 0.0, L))
            cy = float(np.clip(cy, 0.0, L))

            # Re-impose no-cut constraints after the jitter (every side that
            # disallows cutting, periodic or not).
            if not self.allow_cut_left   and cx - r < 0: cx = bx
            if not self.allow_cut_right  and cx + r > L: cx = bx
            if not self.allow_cut_bottom and cy - r < 0: cy = by
            if not self.allow_cut_top    and cy + r > L: cy = by

            # Overlap guard (jitter may push into a neighbour); fall back to the
            # un-jittered grid point, else skip.
            if _overlaps(cx, cy, r):
                cx, cy = bx, by
                if _overlaps(cx, cy, r):
                    continue

            # --- accept (primary) ---
            centers.append([cx, cy])
            radii.append(r)
            current_area += _disk_rect_area(cx, cy, r, cx0, cx1, cy0, cy1)
            hole_clr = np.minimum(hole_clr, _grid_clearance(cx, cy) - r)

        if not centers:
            warnings.warn("VGP: no holes were placed.")
            return np.array([]).reshape(0, 2), np.array([])

        # --- report porosity on the primary holes --------------------------
        self._report_porosity(centers, radii, periodic_lr, periodic_tb,
                              label="VGP")

        # --- append periodic mirror duplicates for the FE mesh -------------
        out_centers = [list(c) for c in centers]
        out_radii   = list(radii)
        for (cx, cy), r in zip(centers, radii):
            for mx, my in self._periodic_mirrors(cx, cy, r,
                                                 periodic_lr, periodic_tb):
                if mx + r > 0 and mx - r < L and my + r > 0 and my - r < L:
                    out_centers.append([mx, my])
                    out_radii.append(r)

        return np.array(out_centers), np.array(out_radii)

    # ---- not used, kept for interface consistency -------------------------

    def _compute_hole_centers(self) -> np.ndarray:
        """Not used; holes are placed by ``_place_random_holes``."""
        return self.hole_centers

    # ---- classify each hole (per-hole radius) ----------------------------

    def _classify_holes(self) -> List[int]:
        """
        Classify each hole based on its individual radius.

        Returns same codes as
        :meth:`HexagonalMeshGenerator2._classify_holes`.
        """
        L = self.domain_size
        tol = L * 1e-8
        classifications: List[int] = []
        for (cx, cy), r in zip(self.hole_centers, self.hole_radii):
            cut_left   = (cx - r) < -tol
            cut_bottom = (cy - r) < -tol
            cut_right  = (cx + r) > L + tol
            cut_top    = (cy + r) > L + tol
            if cut_left:
                classifications.append(1)
            elif cut_bottom:
                classifications.append(2)
            elif cut_right:
                classifications.append(3)
            elif cut_top:
                classifications.append(4)
            else:
                classifications.append(5)
        return classifications

    # ---- minimum ligament (edge-to-edge gap) -----------------------------

    def get_minimum_ligament(self) -> float:
        """Return the minimum edge-to-edge gap among all hole pairs."""
        n = len(self.hole_centers)
        if n < 2:
            return self.domain_size / 10.0
        min_lig = float("inf")
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(self.hole_centers[i] - self.hole_centers[j])
                gap = d - self.hole_radii[i] - self.hole_radii[j]
                if gap < min_lig:
                    min_lig = gap
        return max(min_lig, self.domain_size * 1e-6)

    # ---- extended hole centres (mirror/reflect) --------------------------

    def compute_extended_hole_centers_random(self) -> np.ndarray:
        """
        Augment hole centres by reflecting all holes across each domain
        boundary and the four corners.
        """
        if len(self.hole_centers) == 0:
            return self.hole_centers.copy()

        L = self.domain_size
        shifts = [(-L, 0), (L, 0), (0, -L), (0, L),
                  (-L, -L), (L, -L), (-L, L), (L, L)]
        mirrors = []
        for dx, dy in shifts:
            mirrors.append(self.hole_centers + np.array([[dx, dy]]))
        return np.vstack([self.hole_centers] + mirrors)

    def compute_extended_hole_radii_random(self) -> np.ndarray:
        """Return ``hole_radii`` repeated for each reflected copy."""
        if len(self.hole_radii) == 0:
            return self.hole_radii.copy()
        return np.tile(self.hole_radii, 9)  # 1 original + 8 mirrors

    # ---- plot override (varying radii) -----------------------------------

    def plot_mesh(
        self,
        mesh: "MeshData",
        show_nodes: bool = False,
        show_elements: bool = True,
        show_holes: bool = True,
        show_boundary: bool = True,
        highlight_hole_boundary: bool = True,
        figsize: Tuple[float, float] = (10, 10),
        title: str = None,
        element_color: str = 'lightblue',
        edge_color: str = 'blue',
    ) -> plt.Figure:
        """Visualise the mesh, drawing each hole with its own radius."""
        fig, ax = plt.subplots(figsize=figsize)

        if show_elements and mesh.n_elements > 0:
            if mesh.element_types is not None:
                polygons = [
                    mesh.nodes[elem[:npe]]
                    for elem, npe in zip(mesh.elements, mesh.element_types)
                ]
            else:
                polygons = [mesh.nodes[elem] for elem in mesh.elements]
            collection = PolyCollection(
                polygons, facecolor=element_color, edgecolor=edge_color,
                linewidth=0.5, alpha=0.7,
            )
            ax.add_collection(collection)

        if show_nodes and mesh.n_nodes > 0:
            ax.scatter(mesh.nodes[:, 0], mesh.nodes[:, 1], s=3, c='black', zorder=5)

        if highlight_hole_boundary:
            for indices in mesh.hole_boundary_nodes:
                if len(indices) > 0:
                    ax.scatter(mesh.nodes[indices, 0], mesh.nodes[indices, 1],
                               s=8, c='red', zorder=6)

        if show_holes:
            for center, r_h in zip(self.hole_centers, self.hole_radii):
                circle = Circle(center, r_h, fill=True, facecolor='white',
                                edgecolor='darkred', linewidth=1.5, zorder=4)
                ax.add_patch(circle)

        if show_boundary:
            rect = plt.Rectangle(
                (0, 0), self.domain_size, self.domain_size,
                fill=False, edgecolor='black', linewidth=2, zorder=3,
            )
            ax.add_patch(rect)

        ax.set_xlim(-0.05 * self.domain_size, 1.05 * self.domain_size)
        ax.set_ylim(-0.05 * self.domain_size, 1.05 * self.domain_size)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')

        if title is None:
            title = (
                f'Random Mesh: {len(self.hole_centers)} holes, '
                f'porosity≈{self.porosity:.3f}\n'
                f'{mesh.n_nodes} nodes, {mesh.n_elements} elements'
            )
        ax.set_title(title)
        plt.tight_layout()
        return fig

    # ---- Voronoi plot override (varying radii) ---------------------------

    def plot_voronoi_dual(
        self,
        show_delaunay: bool = True,
        show_voronoi: bool = True,
        show_holes: bool = True,
        show_centers: bool = True,
        figsize: Tuple[float, float] = (10, 10),
        title: str = None,
        centers: np.ndarray = None,
    ) -> plt.Figure:
        """Plot Voronoi / Delaunay with per-hole radii circles."""
        pts = centers if centers is not None else self.hole_centers
        if len(pts) < 3:
            raise ValueError("Need at least 3 hole centers for triangulation")

        fig, ax = plt.subplots(figsize=figsize)
        L = self.domain_size
        tri = Delaunay(pts)

        if show_delaunay:
            for simplex in tri.simplices:
                tri_pts = pts[simplex]
                tri_pts = np.vstack([tri_pts, tri_pts[0]])
                ax.plot(tri_pts[:, 0], tri_pts[:, 1], 'b-', linewidth=0.8, alpha=0.6)

        if show_voronoi:
            _, edges = self.generate_voronoi_mesh(clip_to_domain=True, centers=pts)
            for edge in edges:
                ax.plot(edge[:, 0], edge[:, 1], 'r-', linewidth=1.5)

        if show_holes:
            for center, r_h in zip(self.hole_centers, self.hole_radii):
                circle = Circle(center, r_h, fill=True, facecolor='lightgray',
                                edgecolor='black', linewidth=1.0, zorder=4)
                ax.add_patch(circle)

        if show_centers:
            ax.scatter(pts[:, 0], pts[:, 1], s=30, c='black', zorder=5,
                       label='Hole centers')

        rect = plt.Rectangle((0, 0), L, L, fill=False, edgecolor='black',
                              linewidth=2, zorder=3)
        ax.add_patch(rect)
        ax.set_xlim(-0.05 * L, 1.05 * L)
        ax.set_ylim(-0.05 * L, 1.05 * L)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')

        if title is None:
            title = (f'Delaunay Triangulation & Voronoi Dual\n'
                     f'{len(pts)} hole centers')
        ax.set_title(title)

        legend_elements = []
        if show_delaunay:
            legend_elements.append(
                plt.Line2D([0], [0], color='blue', linewidth=0.8, label='Delaunay'))
        if show_voronoi:
            legend_elements.append(
                plt.Line2D([0], [0], color='red', linewidth=1.5, label='Voronoi (dual)'))
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()
        return fig

    # ==================================================================
    # generate_mesh  – OCC-based mesh with per-hole radii
    # ==================================================================

    def generate_mesh(
        self,
        elements_around_hole: int = 24,
        mesh_size_factor: float = 1.0,
        mesh_size: float = None,
        algorithm: str = 'auto',
        element_type: str = 'QUAD',
        edge_padding: Dict[str, float] = None,
        periodic_lr: bool = False,
        periodic_tb: bool = False,
    ) -> "MeshData":
        """
        Generate a boundary-conforming mesh using the OCC kernel.

        Identical to
        :meth:`HexagonalMeshGenerator2.generate_mesh` except that every
        hole can have its own radius (``self.hole_radii``).
        """
        element_type = element_type.upper()
        if element_type not in ('QUAD', 'TRI', 'BOTH'):
            raise ValueError(
                f"element_type must be 'QUAD', 'TRI' or 'BOTH' "
                f"(got '{element_type}')"
            )
        if not GMSH_AVAILABLE:
            raise RuntimeError("Gmsh is required.  Install with: pip install gmsh")

        _want_periodic_lr = periodic_lr
        _want_periodic_tb = periodic_tb

        # --- mesh sizing ---------------------------------------------------
        if mesh_size is not None:
            mesh_size_hole = float(mesh_size)
            mesh_size_bg   = float(mesh_size)
            min_lig = self.get_minimum_ligament()
            min_r   = float(np.min(self.hole_radii)) if len(self.hole_radii) else 0.01
        else:
            min_r = float(np.min(self.hole_radii)) if len(self.hole_radii) else 0.01
            circumference = 2 * np.pi * min_r
            mesh_size_hole = circumference / elements_around_hole * mesh_size_factor
            min_lig = self.get_minimum_ligament()
            mesh_size_bg = min(
                min_lig / 3.0,
                self.domain_size / 20.0,
            ) * mesh_size_factor

        L = self.domain_size

        # Domain bounds
        if edge_padding:
            _x0 = -edge_padding.get('left', 0.0)
            _x1 = L + edge_padding.get('right', 0.0)
            _y0 = -edge_padding.get('bottom', 0.0)
            _y1 = L + edge_padding.get('top', 0.0)
        else:
            _x0, _y0 = 0.0, 0.0
            _x1, _y1 = L, L

        # --- OCC geometry --------------------------------------------------
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("random_mesh")

        rect_tag = gmsh.model.occ.addRectangle(_x0, _y0, 0, _x1 - _x0, _y1 - _y0)

        disk_dimtags = []
        for (cx, cy), r_h in zip(self.hole_centers, self.hole_radii):
            dtag = gmsh.model.occ.addDisk(cx, cy, 0, r_h, r_h)
            disk_dimtags.append((2, dtag))

        if disk_dimtags:
            out_dimtags, _ = gmsh.model.occ.cut(
                [(2, rect_tag)], disk_dimtags,
                removeObject=True, removeTool=True,
            )
        else:
            out_dimtags = [(2, rect_tag)]

        gmsh.model.occ.synchronize()

        # --- physical groups -----------------------------------------------
        surface_tags = [dt[1] for dt in out_dimtags if dt[0] == 2]
        gmsh.model.addPhysicalGroup(2, surface_tags, 100, "domain")

        all_curves = gmsh.model.getEntities(1)
        bottom_curves, right_curves, top_curves, left_curves = [], [], [], []
        hole_curve_tags = []

        tol_class = L * 1e-4

        for dim, tag in all_curves:
            param_range = gmsh.model.getParametrizationBounds(dim, tag)
            t_start, t_end = param_range[0][0], param_range[1][0]
            p_start = gmsh.model.getValue(dim, tag, [t_start])
            p_end   = gmsh.model.getValue(dim, tag, [t_end])
            sx, sy = p_start[0], p_start[1]
            ex, ey = p_end[0],   p_end[1]

            t_mid = 0.5 * (t_start + t_end)
            mid = gmsh.model.getValue(dim, tag, [t_mid])
            mx, my = mid[0], mid[1]

            # Is this curve part of a hole arc? (per-hole radius)
            is_hole = False
            for (cx, cy), r_h in zip(self.hole_centers, self.hole_radii):
                dist = np.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
                if abs(dist - r_h) < tol_class:
                    is_hole = True
                    break
            if is_hole:
                hole_curve_tags.append(tag)

            both_on_left   = abs(sx - _x0) < tol_class and abs(ex - _x0) < tol_class
            both_on_right  = abs(sx - _x1) < tol_class and abs(ex - _x1) < tol_class
            both_on_bottom = abs(sy - _y0) < tol_class and abs(ey - _y0) < tol_class
            both_on_top    = abs(sy - _y1) < tol_class and abs(ey - _y1) < tol_class

            if both_on_bottom:
                bottom_curves.append(tag)
            elif both_on_top:
                top_curves.append(tag)
            elif both_on_left:
                left_curves.append(tag)
            elif both_on_right:
                right_curves.append(tag)

        if bottom_curves:
            gmsh.model.addPhysicalGroup(1, bottom_curves, 1, "bottom")
        if right_curves:
            gmsh.model.addPhysicalGroup(1, right_curves, 2, "right")
        if top_curves:
            gmsh.model.addPhysicalGroup(1, top_curves, 3, "top")
        if left_curves:
            gmsh.model.addPhysicalGroup(1, left_curves, 4, "left")
        if hole_curve_tags:
            gmsh.model.addPhysicalGroup(1, hole_curve_tags, 10, "holes")

        # --- meshing options -----------------------------------------------
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)

        if element_type == 'QUAD':
            gmsh.option.setNumber("Mesh.RecombineAll", 1)
            gmsh.option.setNumber("Mesh.Algorithm", 8)
            gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 2)
        elif element_type == 'TRI':
            gmsh.option.setNumber("Mesh.RecombineAll", 0)
            gmsh.option.setNumber("Mesh.Algorithm", 6)
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 0)
        else:  # BOTH
            gmsh.option.setNumber("Mesh.RecombineAll", 1)
            gmsh.option.setNumber("Mesh.Algorithm", 8)
            gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
            gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 0)

        # Size field
        if mesh_size is not None:
            # Uniform mesh: disable Gmsh geometric size hints and enforce
            # a constant global size so all elements are the same target size.
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
            gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
            gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_hole)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_bg)
        elif hole_curve_tags:
            gmsh.model.mesh.field.add("Distance", 1)
            gmsh.model.mesh.field.setNumbers(1, "CurvesList", hole_curve_tags)
            gmsh.model.mesh.field.setNumber(1, "Sampling", 100)

            gmsh.model.mesh.field.add("Threshold", 2)
            gmsh.model.mesh.field.setNumber(2, "InField", 1)
            gmsh.model.mesh.field.setNumber(2, "SizeMin", mesh_size_hole)
            gmsh.model.mesh.field.setNumber(2, "SizeMax", mesh_size_bg)
            gmsh.model.mesh.field.setNumber(2, "DistMin", min_r * 0.5)
            gmsh.model.mesh.field.setNumber(2, "DistMax", min_lig)
            gmsh.model.mesh.field.setAsBackgroundMesh(2)
        else:
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_bg)

        # --- periodic constraints ------------------------------------------
        if periodic_lr:
            if len(left_curves) != len(right_curves):
                warnings.warn(
                    f"Cannot enforce LR periodicity: left has "
                    f"{len(left_curves)} curve(s) but right has "
                    f"{len(right_curves)}.  Skipping."
                )
                periodic_lr = False
            elif left_curves and right_curves:
                def _curve_y_mid(tag):
                    pr = gmsh.model.getParametrizationBounds(1, tag)
                    t = 0.5 * (pr[0][0] + pr[1][0])
                    return gmsh.model.getValue(1, tag, [t])[1]
                left_sorted  = sorted(left_curves,  key=_curve_y_mid)
                right_sorted = sorted(right_curves, key=_curve_y_mid)
                dx = _x1 - _x0
                affine_lr = [1, 0, 0, dx,
                             0, 1, 0, 0,
                             0, 0, 1, 0,
                             0, 0, 0, 1]
                gmsh.model.mesh.setPeriodic(1, right_sorted, left_sorted, affine_lr)

        if periodic_tb:
            if len(bottom_curves) != len(top_curves):
                warnings.warn(
                    f"Cannot enforce TB periodicity: bottom has "
                    f"{len(bottom_curves)} curve(s) but top has "
                    f"{len(top_curves)}.  Skipping."
                )
                periodic_tb = False
            elif bottom_curves and top_curves:
                def _curve_x_mid(tag):
                    pr = gmsh.model.getParametrizationBounds(1, tag)
                    t = 0.5 * (pr[0][0] + pr[1][0])
                    return gmsh.model.getValue(1, tag, [t])[0]
                bottom_sorted = sorted(bottom_curves, key=_curve_x_mid)
                top_sorted    = sorted(top_curves,    key=_curve_x_mid)
                dy = _y1 - _y0
                affine_tb = [1, 0, 0, 0,
                             0, 1, 0, dy,
                             0, 0, 1, 0,
                             0, 0, 0, 1]
                gmsh.model.mesh.setPeriodic(1, top_sorted, bottom_sorted, affine_tb)

        # --- generate mesh -------------------------------------------------
        gmsh.model.mesh.generate(2)
        if element_type in ('QUAD', 'BOTH'):
            gmsh.model.mesh.recombine()

        # --- extract mesh data ---------------------------------------------
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        nodes = np.array(node_coords).reshape(-1, 3)[:, :2]
        tag_to_idx = {tag: i for i, tag in enumerate(node_tags)}

        elem_types_gmsh, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(2)

        n_tri = 0
        n_quad = 0
        elements = []
        et_list: List[int] = []

        for etype, etags, enodes in zip(elem_types_gmsh, elem_tags, elem_node_tags):
            if etype == 2:  # triangle
                n_tri += len(etags)
                enodes = np.array(enodes).reshape(-1, 3)
                for tri_nodes in enodes:
                    idx = [tag_to_idx[t] for t in tri_nodes]
                    if element_type == 'QUAD':
                        elements.append(idx + [idx[2]])
                        et_list.append(4)
                    else:
                        elements.append(idx)
                        et_list.append(3)
            elif etype == 3:  # quad
                n_quad += len(etags)
                enodes = np.array(enodes).reshape(-1, 4)
                for quad_nodes in enodes:
                    elements.append([tag_to_idx[t] for t in quad_nodes])
                    et_list.append(4)

        if element_type == 'QUAD' and n_tri > 0:
            warnings.warn(
                f"Gmsh produced {n_tri} triangular element(s) converted "
                f"to degenerate quads."
            )
        elif element_type == 'TRI' and n_quad > 0:
            warnings.warn(
                f"Gmsh produced {n_quad} quad element(s) in TRI mode."
            )

        element_types_arr = np.array(et_list, dtype=int) if et_list else np.array([], dtype=int)

        if element_type == 'BOTH' and n_tri > 0 and n_quad > 0:
            max_npe = 4
            padded = []
            for elem, npe in zip(elements, et_list):
                if npe < max_npe:
                    padded.append(elem + [-1] * (max_npe - npe))
                else:
                    padded.append(elem)
            elements_np = np.array(padded) if padded else np.array([]).reshape(0, 4)
        elif element_type == 'TRI' or (element_type == 'BOTH' and n_quad == 0):
            elements_np = np.array(elements) if elements else np.array([]).reshape(0, 3)
        else:
            elements_np = np.array(elements) if elements else np.array([]).reshape(0, 4)

        # Remove isolated nodes
        if len(elements_np) > 0:
            flat = elements_np.flatten()
            used_node_indices = np.unique(flat[flat >= 0])
        else:
            used_node_indices = np.array([], dtype=int)

        old_to_new = np.full(len(nodes), -1, dtype=int)
        old_to_new[used_node_indices] = np.arange(len(used_node_indices))
        nodes_filtered = nodes[used_node_indices]

        if len(elements_np) > 0:
            mask_valid = elements_np >= 0
            elements_remapped = elements_np.copy()
            elements_remapped[mask_valid] = old_to_new[elements_np[mask_valid]]
        else:
            elements_remapped = elements_np

        # --- boundary identification ---------------------------------------
        tol = L * 1e-6
        boundary_nodes = {
            'bottom': np.where(np.abs(nodes_filtered[:, 1] - _y0) < tol)[0],
            'right':  np.where(np.abs(nodes_filtered[:, 0] - _x1) < tol)[0],
            'top':    np.where(np.abs(nodes_filtered[:, 1] - _y1) < tol)[0],
            'left':   np.where(np.abs(nodes_filtered[:, 0] - _x0) < tol)[0],
        }

        hole_boundary_nodes = []
        for (cx, cy), r_h in zip(self.hole_centers, self.hole_radii):
            distances = np.linalg.norm(nodes_filtered - np.array([cx, cy]), axis=1)
            on_circle = np.where(np.abs(distances - r_h) < tol * 100)[0]
            hole_boundary_nodes.append(on_circle)

        # --- periodic pairs ------------------------------------------------
        _periodic_lr_gmsh: List[Tuple[int, int]] = []
        _periodic_tb_gmsh: List[Tuple[int, int]] = []

        if periodic_lr:
            for tag in right_curves:
                try:
                    _, slave_tags, master_tags, _ = (
                        gmsh.model.mesh.getPeriodicNodes(1, tag))
                    for st, mt in zip(slave_tags, master_tags):
                        _periodic_lr_gmsh.append((int(mt), int(st)))
                except Exception:
                    pass

        if periodic_tb:
            for tag in top_curves:
                try:
                    _, slave_tags, master_tags, _ = (
                        gmsh.model.mesh.getPeriodicNodes(1, tag))
                    for st, mt in zip(slave_tags, master_tags):
                        _periodic_tb_gmsh.append((int(st), int(mt)))
                except Exception:
                    pass

        gmsh.finalize()

        # --- remap periodic pairs ------------------------------------------
        periodic_pairs_lr = None
        periodic_pairs_tb = None

        if _periodic_lr_gmsh:
            pairs, seen = [], set()
            for left_tag, right_tag in _periodic_lr_gmsh:
                li = tag_to_idx.get(left_tag, -1)
                ri = tag_to_idx.get(right_tag, -1)
                if li >= 0 and ri >= 0:
                    li_new = int(old_to_new[li])
                    ri_new = int(old_to_new[ri])
                    if li_new >= 0 and ri_new >= 0 and (li_new, ri_new) not in seen:
                        pairs.append([li_new, ri_new])
                        seen.add((li_new, ri_new))
            if pairs:
                pairs.sort(key=lambda p: nodes_filtered[p[0], 1])
                periodic_pairs_lr = np.array(pairs, dtype=int)

        if _periodic_tb_gmsh:
            pairs, seen = [], set()
            for top_tag, bottom_tag in _periodic_tb_gmsh:
                ti_idx = tag_to_idx.get(top_tag, -1)
                bi = tag_to_idx.get(bottom_tag, -1)
                if ti_idx >= 0 and bi >= 0:
                    ti_new = int(old_to_new[ti_idx])
                    bi_new = int(old_to_new[bi])
                    if ti_new >= 0 and bi_new >= 0 and (ti_new, bi_new) not in seen:
                        pairs.append([ti_new, bi_new])
                        seen.add((ti_new, bi_new))
            if pairs:
                pairs.sort(key=lambda p: nodes_filtered[p[0], 0])
                periodic_pairs_tb = np.array(pairs, dtype=int)

        # --- geometric fallback for periodic pairs -------------------------
        if _want_periodic_lr and periodic_pairs_lr is None:
            left_idx  = boundary_nodes['left']
            right_idx = boundary_nodes['right']
            if len(left_idx) > 0 and len(left_idx) == len(right_idx):
                left_sorted  = left_idx[np.argsort(nodes_filtered[left_idx, 1])]
                right_sorted = right_idx[np.argsort(nodes_filtered[right_idx, 1])]
                periodic_pairs_lr = np.column_stack([left_sorted, right_sorted])
                print(f"  Periodic LR: {len(periodic_pairs_lr)} pairs (geometric fallback)")
            elif len(left_idx) != len(right_idx):
                warnings.warn(
                    f"Cannot build LR periodic pairs: left has "
                    f"{len(left_idx)} node(s) but right has "
                    f"{len(right_idx)}.  Skipping."
                )

        if _want_periodic_tb and periodic_pairs_tb is None:
            bottom_idx = boundary_nodes['bottom']
            top_idx    = boundary_nodes['top']
            if len(bottom_idx) > 0 and len(bottom_idx) == len(top_idx):
                bottom_sorted = bottom_idx[np.argsort(nodes_filtered[bottom_idx, 0])]
                top_sorted    = top_idx[np.argsort(nodes_filtered[top_idx, 0])]
                periodic_pairs_tb = np.column_stack([top_sorted, bottom_sorted])
                print(f"  Periodic TB: {len(periodic_pairs_tb)} pairs (geometric fallback)")
            elif len(bottom_idx) != len(top_idx):
                warnings.warn(
                    f"Cannot build TB periodic pairs: bottom has "
                    f"{len(bottom_idx)} node(s) but top has "
                    f"{len(top_idx)}.  Skipping."
                )

        # --- classify & reorder holes --------------------------------------
        hole_classifications = self._classify_holes()

        b_priority = {5: 0, 1: 1, 2: 2, 3: 3, 4: 4}
        order = sorted(
            range(len(hole_classifications)),
            key=lambda i: b_priority.get(hole_classifications[i], 99),
        )
        hole_classifications = [hole_classifications[i] for i in order]
        hole_boundary_nodes  = [hole_boundary_nodes[i]  for i in order]
        self.hole_centers    = self.hole_centers[order]
        self.hole_radii      = self.hole_radii[order]

        return MeshData(
            nodes=nodes_filtered,
            elements=elements_remapped,
            boundary_nodes=boundary_nodes,
            hole_boundary_nodes=hole_boundary_nodes,
            hole_classifications=hole_classifications,
            element_types=element_types_arr,
            periodic_pairs_lr=periodic_pairs_lr,
            periodic_pairs_tb=periodic_pairs_tb,
        )


# ---------------------------------------------------------------------------
# preview_random_mesh  – lightweight domain + holes visualisation
# ---------------------------------------------------------------------------

def preview_random_mesh(
    config: "MeshConfigRand",
    allow_cut_left: bool = True,
    allow_cut_right: bool = True,
    allow_cut_bottom: bool = True,
    allow_cut_top: bool = True,
    periodic: str = "none",
    edge_left: float = None,
    edge_right: float = None,
    edge_bottom: float = None,
    edge_top: float = None,
    figsize: Tuple[float, float] = (8, 8),
    title: str = None,
):
    """
    Plot the square domain with randomly placed holes **without meshing**.

    This gives a quick visual preview of what the foam will look like.
    The hole placement logic is identical to :func:`create_random_mesh`.

    Parameters
    ----------
    config : MeshConfigRand
        Random-mesh configuration.
    allow_cut_left/right/bottom/top : bool
        Whether holes may extend past each boundary.
    periodic : str
        ``"none"``, ``"lr"``, ``"tb"`` or ``"both"``.
    edge_left/right/bottom/top : float
        Extra edge strips (same as in ``create_random_mesh``).
    figsize : tuple
        Figure size.
    title : str or None
        Plot title.  ``None`` generates a default title.

    Returns
    -------
    fig : matplotlib.figure.Figure
    ax  : matplotlib.axes.Axes
    """
    _periodic = periodic.strip().lower()
    periodic_lr = _periodic in ("lr", "both")
    periodic_tb = _periodic in ("tb", "both")

    w_l = float(edge_left   if edge_left   is not None else getattr(config, 'edge_left',   0.0))
    w_r = float(edge_right  if edge_right  is not None else getattr(config, 'edge_right',  0.0))
    w_b = float(edge_bottom if edge_bottom is not None else getattr(config, 'edge_bottom', 0.0))
    w_t = float(edge_top    if edge_top    is not None else getattr(config, 'edge_top',    0.0))

    generator = RandomMeshGenerator(
        domain_size=config.domain_size,
        porosity=config.porosity,
        min_hole_diameter=config.min_hole_size,
        max_hole_diameter=config.max_hole_size,
        min_distance=config.min_distance_between_holes,
        seed=config.seed,
        allow_cut_left=allow_cut_left,
        allow_cut_right=allow_cut_right,
        allow_cut_bottom=allow_cut_bottom,
        allow_cut_top=allow_cut_top,
        periodic_lr=periodic_lr,
        periodic_tb=periodic_tb,
        edge_left=w_l,
        edge_right=w_r,
        edge_bottom=w_b,
        edge_top=w_t,
        hole_size_distribution=getattr(config, 'hole_size_distribution', 'normal'),
        hole_size_skew_strength=getattr(config, 'hole_size_skew_strength', 2.5),
        placement_algorithm=getattr(config, 'placement_algorithm', 'rsa'),
        ls_max_steps=getattr(config, 'ls_max_steps', 3000),
        ls_resolve_iters=getattr(config, 'ls_resolve_iters', 80),
        ls_growth_rate=getattr(config, 'ls_growth_rate', 0.02),
    )

    # --- rescale if edge strips are used -----------------------------------
    has_strips = bool(w_l or w_r or w_b or w_t)

    L = config.domain_size
    centers = generator.hole_centers.copy()
    radii = generator.hole_radii.copy()

    if has_strips:
        sx = L / (L + w_l + w_r)
        sy = L / (L + w_b + w_t)
        centers[:, 0] = (centers[:, 0] + w_l) * sx
        centers[:, 1] = (centers[:, 1] + w_b) * sy
        radii *= np.sqrt(sx * sy)

    # --- plot --------------------------------------------------------------
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Domain rectangle
    domain_rect = plt.Rectangle(
        (0, 0), L, L,
        linewidth=1.5, edgecolor='black', facecolor='#d9e6f2',
    )
    ax.add_patch(domain_rect)

    # Holes
    for (cx, cy), r in zip(centers, radii):
        circle = plt.Circle(
            (cx, cy), r,
            facecolor='white', edgecolor='black', linewidth=0.8,
        )
        ax.add_patch(circle)

    margin = L * 0.05
    ax.set_xlim(-margin, L + margin)
    ax.set_ylim(-margin, L + margin)
    ax.set_aspect('equal')
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    if title is None:
        achieved_porosity = np.sum(np.pi * radii ** 2) / (L * L)
        title = (
            f"Random foam preview – {len(centers)} holes, "
            f"porosity ≈ {achieved_porosity:.3f} (target {config.porosity:.3f}), "
            f"seed={config.seed}"
        )
    ax.set_title(title)

    plt.tight_layout()

    # --- histogram of hole diameters ---------------------------------------
    diameters = 2.0 * radii
    mean_d = np.mean(diameters)
    std_d  = np.std(diameters)

    fig_hist, ax_hist = plt.subplots(1, 1, figsize=(8, 4))
    ax_hist.hist(diameters, bins='auto', edgecolor='black', color='#7bafd4')
    ax_hist.axvline(mean_d, color='red', linestyle='--', linewidth=1.5,
                    label=f'mean = {mean_d:.4f}')
    ax_hist.axvline(mean_d - std_d, color='orange', linestyle=':', linewidth=1.2,
                    label=f'std = {std_d:.4f}')
    ax_hist.axvline(mean_d + std_d, color='orange', linestyle=':', linewidth=1.2)
    ax_hist.set_xlabel('Hole diameter')
    ax_hist.set_ylabel('Count')
    ax_hist.set_title(f'Hole diameter distribution  (n={len(diameters)})')
    ax_hist.legend()
    plt.tight_layout()

    plt.show()
    return fig, ax


# ---------------------------------------------------------------------------
# create_random_mesh
# ---------------------------------------------------------------------------

def create_random_mesh(
    config: "MeshConfigRand",
    filepath: str,
    export_mesh: bool = True,
    export_vtk: bool = True,
    show_plot: bool = False,
    show_periodic_matching: bool = False,
    elements_around_hole: int = 24,
    mesh_size_factor: float = 1.0,
    mesh_size: float = None,
    allow_cut_left: bool = True,
    allow_cut_right: bool = True,
    allow_cut_bottom: bool = True,
    allow_cut_top: bool = True,
    element_type: str = "QUAD",
    edge_left: float = None,
    edge_right: float = None,
    edge_bottom: float = None,
    edge_top: float = None,
    periodic: str = "none",
):
    """
    Create only the finite-element mesh for a random packing and write it as
    ``*.mesh.json``.

    Derived graph, grid, gridhex, and Voronoi/Delaunay VTK files are created
    by separate functions that take this mesh JSON file as input.
    """

    # --- parse periodic flag -----------------------------------------------
    _periodic = periodic.strip().lower()
    periodic_lr = _periodic in ("lr", "both")
    periodic_tb = _periodic in ("tb", "both")

    # --- edge padding (read from config if not provided as arguments) ------
    # Function-level arguments take precedence; fall back to config fields so
    # that edges are co-located with the porosity specification.
    w_l = float(edge_left   if edge_left   is not None else getattr(config, 'edge_left',   0.0))
    w_r = float(edge_right  if edge_right  is not None else getattr(config, 'edge_right',  0.0))
    w_b = float(edge_bottom if edge_bottom is not None else getattr(config, 'edge_bottom', 0.0))
    w_t = float(edge_top    if edge_top    is not None else getattr(config, 'edge_top',    0.0))
    has_strips = bool(w_l or w_r or w_b or w_t)
    padding = ({"left": w_l, "right": w_r, "bottom": w_b, "top": w_t}
               if has_strips else None)

    # --- build generator & place holes -------------------------------------
    generator = RandomMeshGenerator(
        domain_size=config.domain_size,
        porosity=config.porosity,
        min_hole_diameter=config.min_hole_size,
        max_hole_diameter=config.max_hole_size,
        min_distance=config.min_distance_between_holes,
        seed=config.seed,
        allow_cut_left=allow_cut_left,
        allow_cut_right=allow_cut_right,
        allow_cut_bottom=allow_cut_bottom,
        allow_cut_top=allow_cut_top,
        periodic_lr=periodic_lr,
        periodic_tb=periodic_tb,
        edge_left=w_l,
        edge_right=w_r,
        edge_bottom=w_b,
        edge_top=w_t,
        hole_size_distribution=getattr(config, 'hole_size_distribution', 'normal'),
        hole_size_skew_strength=getattr(config, 'hole_size_skew_strength', 2.5),
        placement_algorithm=getattr(config, 'placement_algorithm', 'rsa'),
        ls_max_steps=getattr(config, 'ls_max_steps', 3000),
        ls_resolve_iters=getattr(config, 'ls_resolve_iters', 80),
        ls_growth_rate=getattr(config, 'ls_growth_rate', 0.02),
    )

    print(f"Random holes placed: {len(generator.hole_centers)} holes "
          f"(seed={config.seed})")

    # --- generate FE mesh --------------------------------------------------
    mesh = generator.generate_mesh(
        elements_around_hole=elements_around_hole,
        mesh_size_factor=mesh_size_factor,
        mesh_size=mesh_size,
        element_type=element_type,
        edge_padding=padding,
        periodic_lr=periodic_lr,
        periodic_tb=periodic_tb,
    )

    # --- rescale expanded domain back to [0, L] x [0, L] ------------------
    if has_strips:
        L  = config.domain_size
        sx = L / (L + w_l + w_r)
        sy = L / (L + w_b + w_t)

        mesh.nodes[:, 0] = (mesh.nodes[:, 0] + w_l) * sx
        mesh.nodes[:, 1] = (mesh.nodes[:, 1] + w_b) * sy

        centres = generator.hole_centers.copy()
        centres[:, 0] = (centres[:, 0] + w_l) * sx
        centres[:, 1] = (centres[:, 1] + w_b) * sy
        generator.hole_centers = centres

        generator.hole_radii *= np.sqrt(sx * sy)
        generator.geometry.horizontal_spacing *= sx
        generator.geometry.vertical_spacing *= sy
        generator.geometry.hole_radius *= np.sqrt(sx * sy)

        print(f"  Edge strips added (L={edge_left}, R={edge_right}, "
              f"B={edge_bottom}, T={edge_top}), mesh rescaled to "
              f"[0, {config.domain_size}]")

    mesh.compute_node_labels()

    # --- ensure output directory -------------------------------------------
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    mesh_json = _ensure_json_suffix(filepath, "mesh")
    if export_mesh:
        write_mesh_json(
            mesh,
            mesh_json,
            mesh_kind="random",
            created_by="create_random_mesh",
            generator=generator,
            parameters={
                "config": {
                    "domain_size": config.domain_size,
                    "porosity": config.porosity,
                    "min_hole_size": config.min_hole_size,
                    "max_hole_size": config.max_hole_size,
                    "min_distance_between_holes": config.min_distance_between_holes,
                    "seed": config.seed,
                },
                "elements_around_hole": elements_around_hole,
                "mesh_size_factor": mesh_size_factor,
                "allow_cut_left": allow_cut_left,
                "allow_cut_right": allow_cut_right,
                "allow_cut_bottom": allow_cut_bottom,
                "allow_cut_top": allow_cut_top,
                "element_type": element_type,
                "edge_left": edge_left,
                "edge_right": edge_right,
                "edge_bottom": edge_bottom,
                "edge_top": edge_top,
                "periodic": periodic,
            },
        )
        if export_vtk:
            export_mesh_vtk_from_json(mesh_json)

    # --- plotting ----------------------------------------------------------
    show_any_plot = False
    if show_plot:
        generator.plot_mesh(mesh, show_nodes=True, show_elements=True,
                            show_holes=True, highlight_hole_boundary=True)
        generator.plot_node_labels(mesh, show_label=True)
        show_any_plot = True

    if show_periodic_matching:
        if export_mesh:
            from A001_functions.plot_mesh_functions import plot_mesh_json_periodic

            plot_mesh_json_periodic(mesh_json, show=False)
            show_any_plot = True
        else:
            warnings.warn("show_periodic_matching requires export_mesh=True")

    if show_any_plot:
        plt.show()

    print(
        f"Mesh created: {mesh.n_nodes} nodes, {mesh.n_elements} elements, "
        f"{len(generator.hole_centers)} holes"
    )

    return generator, mesh


# ---------------------------------------------------------------------------
# Stand-alone execution example
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = MeshConfig(domain_size=1.0, n_holes_width=10, porosity=0.6)

    generator, mesh = create_hexagonal_mesh(
        config=cfg,
        filepath="C001_Mesh_files/hexagonal_mesh",
        export_mesh=True,
        show_plot=True,
    )
