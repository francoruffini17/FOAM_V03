import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.patches as mpatches


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
    nodes    = []    # list of (x, y, id)
    elements = []    # list of (n1, n2, n3)

    with open(file_name, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    i = 0
    n_nodes_total = int(lines[i]); i += 1
    for _ in range(n_nodes_total):
        parts = [p.strip() for p in lines[i].split(",")]; i += 1
        nodes.append((float(parts[0]), float(parts[1]), int(parts[2])))

    n_elements_total = int(lines[i]); i += 1
    for _ in range(n_elements_total):
        parts = [p.strip() for p in lines[i].split(",")]; i += 1
        elements.append((int(parts[0]), int(parts[1]), int(parts[2])))

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
    