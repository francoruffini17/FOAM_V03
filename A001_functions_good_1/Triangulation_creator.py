import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.collections import LineCollection, PolyCollection


def triangulation_generator(n_nodes_per_edge: int, file_name: str) -> None:
    """
    Generate a triangular FEM mesh on the unit square [0,1]x[0,1].

    The mesh is built from a regular grid of (n_nodes_per_edge x n_nodes_per_edge)
    equispaced nodes (ID 1). Each grid cell is then split into 4 triangles by
    adding the cell-centre node (ID 2) and connecting it to the 4 cell corners.

    Node ordering convention
    ------------------------
    ID 1 nodes are laid out row-by-row (bottom → top, left → right):
        global index = row * n_nodes_per_edge + col
        (row=0 is y=0, col=0 is x=0)

    ID 2 nodes follow immediately after all ID 1 nodes, one per cell, laid out
    in the same row-major order over the (n-1)x(n-1) cells.

    Each cell (row r, col c) produces 4 CCW triangles:
        corners:  BL, BR, TR, TL  (ID 1 nodes)
        centre:   C               (ID 2 node)
        triangles:
            bottom  → BL, BR, C
            right   → BR, TR, C
            top     → TR, TL, C
            left    → TL, BL, C

    Parameters
    ----------
    n_nodes_per_edge : int
        Number of nodes along each edge of the unit square (≥ 2).
    file_name : str
        Path + filename where the mesh will be saved (plain text).
    """
    if n_nodes_per_edge < 2:
        raise ValueError("n_nodes_per_edge must be >= 2")

    n = n_nodes_per_edge
    n_cells = (n - 1) ** 2

    # ------------------------------------------------------------------
    # 1. Build ID-1 nodes  (n x n grid)
    # ------------------------------------------------------------------
    coords = []          # list of (x, y, id)
    node_id1 = {}        # (row, col) -> global index

    for row in range(n):
        for col in range(n):
            x = col / (n - 1)
            y = row / (n - 1)
            idx = len(coords)
            node_id1[(row, col)] = idx
            coords.append((x, y, 1))

    # ------------------------------------------------------------------
    # 2. Build ID-2 nodes  (one per cell, at cell centre)
    # ------------------------------------------------------------------
    node_id2 = {}        # (row, col) of cell -> global index

    for row in range(n - 1):       # row of the cell's bottom edge
        for col in range(n - 1):   # col of the cell's left edge
            x = (col + 0.5) / (n - 1)
            y = (row + 0.5) / (n - 1)
            idx = len(coords)
            node_id2[(row, col)] = idx
            coords.append((x, y, 2))

    # ------------------------------------------------------------------
    # 3. Build elements  (4 CCW triangles per cell)
    # ------------------------------------------------------------------
    elements = []

    for row in range(n - 1):
        for col in range(n - 1):
            BL = node_id1[(row,     col    )]
            BR = node_id1[(row,     col + 1)]
            TR = node_id1[(row + 1, col + 1)]
            TL = node_id1[(row + 1, col    )]
            C  = node_id2[(row,     col    )]

            # bottom  triangle: BL -> BR -> C  (CCW when y increases upward)
            elements.append((BL, BR, C))
            # right   triangle: BR -> TR -> C
            elements.append((BR, TR, C))
            # top     triangle: TR -> TL -> C
            elements.append((TR, TL, C))
            # left    triangle: TL -> BL -> C
            elements.append((TL, BL, C))

    # ------------------------------------------------------------------
    # 4. Write file
    # ------------------------------------------------------------------
    n_nodes = len(coords)
    n_elements = len(elements)

    with open(file_name, "w") as f:
        f.write(f"{n_nodes}\n")
        for x, y, nid in coords:
            f.write(f"{x:.10f}, {y:.10f}, {nid}\n")

        f.write(f"{n_elements}\n")
        for n1, n2, n3 in elements:
            f.write(f"{n1}, {n2}, {n3}\n")

    print(f"Mesh saved to '{file_name}'")
    print(f"  ID-1 nodes : {n * n}")
    print(f"  ID-2 nodes : {n_cells}")
    print(f"  Elements   : {4 * n_cells}")


# ---------------------------------------------------------------------------

def read_triangulation_file(file_name: str):
    """
    Read a triangulation file produced by ``triangulation_generator``.

    Returns
    -------
    nodes : list[tuple[float, float, int]]
        Triangulation nodes as ``(x, y, ID)``.
    elements : list[tuple[int, int, int]]
        Triangle connectivity with 0-based node indices.
    """
    nodes = []
    elements = []

    with open(file_name, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    n_nodes_total = int(lines[i])
    i += 1
    for _ in range(n_nodes_total):
        parts = lines[i].replace(",", " ").split()
        i += 1
        nodes.append((float(parts[0]), float(parts[1]), int(parts[2])))

    n_elements_total = int(lines[i])
    i += 1
    for _ in range(n_elements_total):
        parts = lines[i].replace(",", " ").split()
        i += 1
        elements.append((int(parts[0]), int(parts[1]), int(parts[2])))

    return nodes, elements


def _element_segments(coords, elements):
    """Return line segments for drawing polygon/triangle element edges."""
    segments = []
    for elem in elements:
        n = len(elem)
        for i in range(n):
            segments.append([coords[elem[i]], coords[elem[(i + 1) % n]]])
    return segments


def _boundary_segments(coords, elements):
    """Return only edges used by one element."""
    edge_count = {}
    for elem in elements:
        n = len(elem)
        for i in range(n):
            edge = tuple(sorted((elem[i], elem[(i + 1) % n])))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    return [
        [coords[n1], coords[n2]]
        for (n1, n2), count in edge_count.items()
        if count == 1
    ]


def preview_triangulation_with_mesh(
    mesh_file: str,
    triangulation_file: str,
    *,
    snap_to_mesh_nodes: bool = True,
    show_original_triangulation: bool = True,
    show_mesh_nodes: bool = True,
    show_triangulation_nodes: bool = False,
    show_node_numbers: bool = False,
    show_element_numbers: bool = False,
    mesh_boundary_only: bool = False,
    figsize: tuple = (8, 8),
    ax=None,
    show: bool = True,
) -> plt.Figure:
    """
    Preview a triangulation mesh over a finite-element ``*.mesh.json`` file.

    When ``snap_to_mesh_nodes=True`` the triangulation vertices are moved to
    their nearest FEM mesh nodes before plotting.  This previews the same node
    matching used by ``create_PKL_T1``.
    """
    from scipy.spatial import cKDTree
    from A001_functions.Hex_5 import read_mesh_json

    mesh_nodes_raw, mesh_elements = read_mesh_json(mesh_file)
    mesh_coords = np.array([(x, y) for x, y, _ in mesh_nodes_raw], dtype=float)

    tri_nodes, tri_elements = read_triangulation_file(triangulation_file)
    tri_coords_original = np.array([(x, y) for x, y, _ in tri_nodes], dtype=float)
    if snap_to_mesh_nodes:
        _, matched_indices = cKDTree(mesh_coords).query(tri_coords_original, k=1)
        matched_indices = np.asarray(matched_indices, dtype=int)
        tri_coords = mesh_coords[matched_indices]
    else:
        tri_coords = tri_coords_original

    tri_ids = np.array([node_id for _, _, node_id in tri_nodes], dtype=int)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    if mesh_elements:
        if mesh_boundary_only:
            boundary = _boundary_segments(mesh_coords, mesh_elements)
            if boundary:
                ax.add_collection(LineCollection(
                    boundary,
                    colors="0.35",
                    linewidths=1.0,
                    zorder=1,
                ))
        else:
            ax.add_collection(PolyCollection(
                [mesh_coords[element] for element in mesh_elements],
                facecolors="#d7e8f7",
                edgecolors="#6f7f8f",
                linewidths=0.45,
                alpha=0.35,
                zorder=1,
            ))

    if show_mesh_nodes:
        ax.scatter(
            mesh_coords[:, 0],
            mesh_coords[:, 1],
            s=6,
            c="black",
            alpha=0.65,
            linewidths=0,
            zorder=4,
            label="FEM nodes",
        )

    if snap_to_mesh_nodes and show_original_triangulation:
        original_segments = _element_segments(tri_coords_original, tri_elements)
        ax.add_collection(LineCollection(
            original_segments,
            colors="#9aa5b1",
            linewidths=0.45,
            linestyles="dotted",
            alpha=0.7,
            zorder=2,
        ))

    tri_segments = _element_segments(tri_coords, tri_elements)
    ax.add_collection(LineCollection(
        tri_segments,
        colors="#d62728",
        linewidths=0.9,
        alpha=0.95,
        zorder=3,
    ))

    if show_triangulation_nodes:
        colors = {1: "#1a1a2e", 2: "#2ecc71"}
        sizes = {1: 18, 2: 22}
        for node_id in sorted(set(tri_ids)):
            mask = tri_ids == node_id
            ax.scatter(
                tri_coords[mask, 0],
                tri_coords[mask, 1],
                c=colors.get(node_id, "#7f8c8d"),
                s=sizes.get(node_id, 18),
                edgecolors="white",
                linewidths=0.25,
                zorder=5,
            )

    if show_node_numbers:
        for idx, (x, y) in enumerate(tri_coords):
            ax.annotate(
                str(idx),
                xy=(x, y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
                color="#c0392b",
                zorder=6,
            )

    if show_element_numbers:
        for elem_idx, (n1, n2, n3) in enumerate(tri_elements):
            centroid = (tri_coords[n1] + tri_coords[n2] + tri_coords[n3]) / 3.0
            ax.text(
                centroid[0],
                centroid[1],
                str(elem_idx),
                ha="center",
                va="center",
                fontsize=5,
                color="#8e44ad",
                zorder=6,
            )

    all_coords = [mesh_coords, tri_coords]
    if snap_to_mesh_nodes and show_original_triangulation:
        all_coords.append(tri_coords_original)
    all_coords = np.vstack(all_coords)
    x_min, y_min = all_coords.min(axis=0)
    x_max, y_max = all_coords.max(axis=0)
    span = max(x_max - x_min, y_max - y_min)
    pad = 0.05 * span if span > 0 else 0.05

    ax.set_xlim(x_min - pad, x_max + pad)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    mode = "snapped to FEM nodes" if snap_to_mesh_nodes else "original"
    ax.set_title(
        f"Triangulation preview ({mode})\n"
        f"{len(mesh_coords)} FEM nodes, {len(mesh_elements)} FEM elements, "
        f"{len(tri_nodes)} tri nodes, {len(tri_elements)} triangles"
    )

    legend_handles = [
        mpatches.Patch(
            facecolor="#d7e8f7",
            edgecolor="#6f7f8f",
            alpha=0.35,
            label="FEM mesh",
        ),
        mlines.Line2D([], [], color="#d62728", linewidth=0.9,
                      label="Triangulation"),
    ]
    if snap_to_mesh_nodes and show_original_triangulation:
        legend_handles.append(mlines.Line2D(
            [], [], color="#9aa5b1", linewidth=0.45,
            linestyle="dotted", label="Original triangulation"
        ))
    ax.legend(handles=legend_handles, loc="upper right", fontsize=8)

    fig.tight_layout()
    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------

def plot_triangulation(
    file_name: str,
    show_node_numbers: bool = False,
    show_element_numbers: bool = False,
    ax=None,
) -> plt.Figure:
    """
    Read a mesh file produced by triangulation_generator and plot it.

    Parameters
    ----------
    file_name : str
        Path to the mesh file.
    show_node_numbers : bool
        If True, annotate each node with its global index.
    show_element_numbers : bool
        If True, annotate each element with its index (at its centroid).
    ax : matplotlib Axes, optional
        Axes to draw on.  A new figure is created when None.

    Returns
    -------
    fig : matplotlib Figure
    """
    # ------------------------------------------------------------------
    # Parse file
    # ------------------------------------------------------------------
    nodes, elements = read_triangulation_file(file_name)

    xs   = np.array([n[0] for n in nodes])
    ys   = np.array([n[1] for n in nodes])
    ids  = np.array([n[2] for n in nodes])
    tris = np.array(elements, dtype=int)

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 7))
    else:
        fig = ax.get_figure()

    ax.set_aspect("equal")
    ax.set_title("FEM Triangulation", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Draw triangle edges
    tri_obj = mtri.Triangulation(xs, ys, tris)
    ax.triplot(tri_obj, color="#4a90d9", linewidth=0.8, alpha=0.85)

    # Colour scheme
    colors = {1: "#1a1a2e", 2: "#2ecc71"}   # dark navy for ID1, green for ID2
    labels = {1: "ID 1 (grid nodes)", 2: "ID 2 (cell-centre nodes)"}
    sizes  = {1: 30, 2: 40}

    for nid in (1, 2):
        mask = ids == nid
        ax.scatter(
            xs[mask], ys[mask],
            c=colors[nid], s=sizes[nid], zorder=5,
            label=labels[nid], edgecolors="white", linewidths=0.4,
        )

    # Optional: node labels
    if show_node_numbers:
        for i, (x, y, nid) in enumerate(nodes):
            ax.annotate(
                str(i),
                xy=(x, y), xytext=(3, 3), textcoords="offset points",
                fontsize=6, color=colors[nid], zorder=6,
            )

    # Optional: element labels
    if show_element_numbers:
        for e_idx, (n1, n2, n3) in enumerate(elements):
            cx = (xs[n1] + xs[n2] + xs[n3]) / 3
            cy = (ys[n1] + ys[n2] + ys[n3]) / 3
            ax.text(
                cx, cy, str(e_idx),
                ha="center", va="center",
                fontsize=5, color="#c0392b", zorder=6,
            )

    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    
    plt.show()

    # fig.show()
    return fig




# ---------------------------------------------------------------------------
# Quick demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mesh_file = "./C001_Mesh_files/T001.tri"

    triangulation_generator(n_nodes_per_edge=15, file_name=mesh_file)

    plot_triangulation(
        mesh_file,
        show_node_numbers=True,
        show_element_numbers=True,
    )
    
