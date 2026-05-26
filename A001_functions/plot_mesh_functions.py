"""
Standalone plotting utilities for mesh and graph JSON files.

Usage
-----
    from J001_important_functions.plot_mesh import plot_mesh_json, plot_graph_mesh

    plot_mesh_json("C001_Mesh_files/A004_hexagonal_mesh.mesh.json")
    plot_graph_mesh("C001_Mesh_files/A004_G000.graph.json")
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle

from A001_functions.Hex_5 import read_mesh_json, read_graph_mesh


# ---------------------------------------------------------------------------
# 1.  plot_mesh_json  –  reads a mesh JSON file, produces two figures
#     Figure 1: FE mesh (elements + nodes + hole circles + domain boundary)
#     Figure 2: Node-label colouring (A digit and B digit, side by side)
# ---------------------------------------------------------------------------

def plot_mesh_json(
    mesh_path: str,
    *,
    show_nodes: bool = True,
    show_elements: bool = True,
    show_labels: bool = True,
    element_color: str = "lightblue",
    edge_color: str = "blue",
    node_size: float = 3,
    label_node_size: float = 20,
    figsize_mesh: tuple = (10, 10),
    figsize_labels: tuple = (24, 10),
    show: bool = True,
):
    """
    Read a ``*.mesh.json`` file and produce one or two matplotlib figures.

    **Figure 1** – the finite-element mesh with elements, nodes, hole
    circles and the domain boundary.

    **Figure 2** (only when *show_labels=True*) – two side-by-side
    scatter plots of nodes coloured by the **A** digit (edge/corner
    position) and the **B** digit (hole classification) of the node
    label ``1ABX…``.

    Parameters
    ----------
    mesh_path : str
        Path to the ``*.mesh.json`` file.
    show_nodes / show_elements : bool
        Toggle individual layers of Figure 1.
    show_labels : bool
        If *True* a second figure with node-label colouring is produced.
    element_color, edge_color : str
        Colours for Figure 1 element faces / edges.
    node_size : float
        Marker size for nodes in Figure 1.
    label_node_size : float
        Marker size for the label-coloured nodes in Figure 2.
    figsize_mesh, figsize_labels : tuple
        Figure sizes.
    show : bool
        Call ``plt.show()`` at the end.

    Returns
    -------
    figs : list[plt.Figure]
        One or two figures depending on *show_labels*.
    """
    # ------------------------------------------------------------------
    # Read the mesh JSON file
    # ------------------------------------------------------------------
    nodes_raw, elements_raw = read_mesh_json(mesh_path)

    coords = np.array([(x, y) for x, y, _ in nodes_raw])      # (N, 2)
    labels = np.array([str(lbl) for _, _, lbl in nodes_raw])    # (N,)

    # Elements are stored 0-based
    elements_0 = elements_raw

    # Domain size (assume square starting at 0)
    L = coords.max()

    figs = []

    # ==================================================================
    # FIGURE 1 – finite-element mesh
    # ==================================================================
    fig1, ax = plt.subplots(figsize=figsize_mesh)

    if show_elements:
        polygons = [coords[e] for e in elements_0]
        ax.add_collection(PolyCollection(
            polygons,
            facecolor=element_color,
            edgecolor=edge_color,
            linewidth=0.5,
            alpha=0.7,
        ))

    if show_nodes:
        ax.scatter(coords[:, 0], coords[:, 1], s=node_size,
                   c="black", zorder=5)

    ax.set_xlim(-0.05 * L, 1.05 * L)
    ax.set_ylim(-0.05 * L, 1.05 * L)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        f"Mesh JSON: {len(coords)} nodes, {len(elements_0)} elements"
    )
    fig1.tight_layout()
    figs.append(fig1)

    # ==================================================================
    # FIGURE 2 – node-label colouring  (A digit | B digit)
    # ==================================================================
    if show_labels:
        A_vals = np.array([lbl[1] for lbl in labels])
        B_vals = np.array([lbl[2] for lbl in labels])

        fig2, (ax_a, ax_b) = plt.subplots(1, 2, figsize=figsize_labels)

        def _draw_bg(ax):
            """Draw semi-transparent element edges + domain rectangle."""
            if show_elements:
                polygons = [coords[e] for e in elements_0]
                ax.add_collection(PolyCollection(
                    polygons,
                    facecolor="white",
                    edgecolor="lightgray",
                    linewidth=0.3,
                    alpha=0.5,
                ))
            ax.add_patch(plt.Rectangle(
                (0, 0), L, L,
                fill=False, edgecolor="black", linewidth=2, zorder=3,
            ))
            ax.set_xlim(-0.05 * L, 1.05 * L)
            ax.set_ylim(-0.05 * L, 1.05 * L)
            ax.set_aspect("equal")
            ax.set_xlabel("x")
            ax.set_ylabel("y")

        # ---- Left subplot: colour by A (edge/corner position) ----
        _draw_bg(ax_a)

        position_colors = {
            "0": "gray",     "1": "blue",     "2": "green",
            "3": "orange",   "4": "red",      "5": "purple",
            "6": "cyan",     "7": "magenta",  "8": "yellow",
        }
        position_names = {
            "0": "Interior",       "1": "Left edge",
            "2": "Bottom edge",    "3": "Right edge",
            "4": "Top edge",       "5": "Bottom-left corner",
            "6": "Top-right corner", "7": "Top-left corner",
            "8": "Bottom-right corner",
        }
        for val in sorted(set(A_vals)):
            mask = A_vals == val
            ax_a.scatter(
                coords[mask, 0], coords[mask, 1],
                s=label_node_size,
                c=position_colors.get(val, "black"),
                label=f"A={val} – {position_names.get(val, '?')}",
                zorder=5,
            )
        ax_a.set_title("Node position (A digit)")
        ax_a.legend(loc="upper right", fontsize=7, markerscale=0.8)

        # ---- Right subplot: colour by B (hole classification) ----
        _draw_bg(ax_b)

        hole_colors = {
            "0": "gray",     "1": "blue",   "2": "green",
            "3": "orange",   "4": "red",    "5": "purple",
        }
        hole_names = {
            "0": "No hole",
            "1": "Hole cut by left",
            "2": "Hole cut by bottom",
            "3": "Hole cut by right",
            "4": "Hole cut by top",
            "5": "Complete hole",
        }
        for val in sorted(set(B_vals)):
            mask = B_vals == val
            ax_b.scatter(
                coords[mask, 0], coords[mask, 1],
                s=label_node_size,
                c=hole_colors.get(val, "black"),
                label=f"B={val} – {hole_names.get(val, '?')}",
                zorder=5,
            )
        ax_b.set_title("Hole classification (B digit)")
        ax_b.legend(loc="upper right", fontsize=7, markerscale=0.8)

        fig2.suptitle(
            f"Node labels – {len(coords)} nodes",
            fontsize=13, y=1.01,
        )
        fig2.tight_layout()
        figs.append(fig2)

    if show:
        plt.show()

    return figs


# ---------------------------------------------------------------------------
# 2.  plot_graph_mesh  –  reads graph/grid/gridhex JSON files
# ---------------------------------------------------------------------------

def plot_graph_mesh(
    graph_path: str,
    *,
    figsize: tuple = (10, 10),
    title: str = None,
    show: bool = True,
) -> plt.Figure:
    """
    Read a graph/grid/gridhex JSON file and plot it.

    Bars are coloured by their original bar number.  Nodes are
    distinguished by their ``node_id``: **1** = original Voronoi
    vertex (black), **2** = subdivision node (red).

    Parameters
    ----------
    graph_path : str
        Path to the graph/grid/gridhex JSON file.
    figsize : tuple
        Figure size.
    title : str or None
        Custom title; auto-generated when *None*.
    show : bool
        Call ``plt.show()`` at the end.

    Returns
    -------
    fig : plt.Figure
    """
    graph = read_graph_mesh(graph_path)

    fig, ax = plt.subplots(figsize=figsize)

    # Colour bars by bar_number
    unique_bars = np.unique(graph.bar_numbers)
    cmap = plt.cm.get_cmap("tab20", len(unique_bars))
    bar_cmap = {bn: cmap(i) for i, bn in enumerate(unique_bars)}

    for (ni, nf), bn in zip(graph.bars, graph.bar_numbers):
        p0, p1 = graph.nodes[ni], graph.nodes[nf]
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=bar_cmap[bn], linewidth=1.2, zorder=2)

    # Nodes
    orig_mask = graph.node_ids == 1
    sub_mask  = graph.node_ids == 2

    if np.any(orig_mask):
        pts = graph.nodes[orig_mask]
        ax.scatter(pts[:, 0], pts[:, 1], s=30, c="black", zorder=5,
                   edgecolors="white", linewidths=0.4,
                   label="Original (ID 1)")
    if np.any(sub_mask):
        pts = graph.nodes[sub_mask]
        ax.scatter(pts[:, 0], pts[:, 1], s=20, c="red", zorder=4,
                   edgecolors="white", linewidths=0.3,
                   label="Subdivision (ID 2)")

    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title is None:
        title = (
            f"Graph mesh: {graph.n_nodes} nodes "
            f"({int(orig_mask.sum())} orig + {int(sub_mask.sum())} sub), "
            f"{graph.n_bars} sub-bars from "
            f"{len(unique_bars)} original bars"
        )
    ax.set_title(title)
    ax.legend(loc="upper right")
    fig.tight_layout()

    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# 3.  plot_mesh_json_and_graph  –  overlay FE mesh + graph mesh on one figure
# ---------------------------------------------------------------------------

def plot_mesh_json_and_graph(
    mesh_path: str,
    graph_path: str,
    *,
    boundary_only: bool = False,
    show_nodes_hex: bool = False,
    show_nodes_graph: bool = True,
    element_color: str = "lightblue",
    edge_color: str = "blue",
    boundary_color: str = "black",
    boundary_lw: float = 1.0,
    graph_lw: float = 1.2,
    node_size_hex: float = 3,
    figsize: tuple = (10, 10),
    title: str = None,
    show: bool = True,
) -> plt.Figure:
    """
    Overlay the FE mesh (``*.mesh.json``) and graph JSON mesh
    on a single figure.

    Parameters
    ----------
    mesh_path : str
        Path to the ``*.mesh.json`` file.
    graph_path : str
        Path to the graph/grid/gridhex JSON file.
    boundary_only : bool
        If *True*, only the outer boundary edges of the FE mesh are
        drawn (edges belonging to a single element).  If *False*,
        all element edges are drawn.
    show_nodes_hex : bool
        Show FE mesh nodes.
    show_nodes_graph : bool
        Show graph mesh nodes (original in black, subdivision in red).
    element_color : str
        Face colour for FE elements (ignored when *boundary_only=True*).
    edge_color : str
        Edge colour for FE element edges (ignored when *boundary_only*).
    boundary_color : str
        Colour for boundary edges when *boundary_only=True*.
    boundary_lw : float
        Line width for boundary edges.
    graph_lw : float
        Line width for graph bars.
    node_size_hex : float
        Marker size for FE nodes.
    figsize : tuple
        Figure size.
    title : str or None
        Custom title; auto-generated when *None*.
    show : bool
        Call ``plt.show()`` at the end.

    Returns
    -------
    fig : plt.Figure
    """
    from matplotlib.collections import LineCollection

    # ---- read mesh JSON ----
    nodes_raw, elements_raw = read_mesh_json(mesh_path)
    coords = np.array([(x, y) for x, y, _ in nodes_raw])
    elements_0 = elements_raw  # already 0-based

    # ---- read graph ----
    graph = read_graph_mesh(graph_path)

    L = coords.max()
    fig, ax = plt.subplots(figsize=figsize)

    # ---- FE mesh layer ----
    if boundary_only:
        # Collect edges and count how many elements share each edge
        edge_count = {}
        for elem in elements_0:
            n = len(elem)
            for k in range(n):
                e = tuple(sorted((elem[k], elem[(k + 1) % n])))
                edge_count[e] = edge_count.get(e, 0) + 1
        boundary_segs = []
        for (n1, n2), cnt in edge_count.items():
            if cnt == 1:
                boundary_segs.append([coords[n1], coords[n2]])
        if boundary_segs:
            lc = LineCollection(boundary_segs, colors=boundary_color,
                                linewidths=boundary_lw, zorder=2)
            ax.add_collection(lc)
    else:
        polygons = [coords[e] for e in elements_0]
        ax.add_collection(PolyCollection(
            polygons,
            facecolor=element_color,
            edgecolor=edge_color,
            linewidth=0.5,
            alpha=0.7,
            zorder=1,
        ))

    if show_nodes_hex:
        ax.scatter(coords[:, 0], coords[:, 1], s=node_size_hex,
                   c="black", zorder=3)

    # ---- graph mesh layer ----
    unique_bars = np.unique(graph.bar_numbers)
    cmap = plt.cm.get_cmap("tab20", len(unique_bars))
    bar_cmap = {bn: cmap(i) for i, bn in enumerate(unique_bars)}

    for (ni, nf), bn in zip(graph.bars, graph.bar_numbers):
        p0, p1 = graph.nodes[ni], graph.nodes[nf]
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=bar_cmap[bn], linewidth=graph_lw, zorder=4)

    if show_nodes_graph:
        orig_mask = graph.node_ids == 1
        sub_mask = graph.node_ids == 2
        if np.any(orig_mask):
            pts = graph.nodes[orig_mask]
            ax.scatter(pts[:, 0], pts[:, 1], s=30, c="black", zorder=6,
                       edgecolors="white", linewidths=0.4,
                       label="Graph original")
        if np.any(sub_mask):
            pts = graph.nodes[sub_mask]
            ax.scatter(pts[:, 0], pts[:, 1], s=20, c="red", zorder=5,
                       edgecolors="white", linewidths=0.3,
                       label="Graph subdivision")

    ax.set_xlim(-0.05 * L, 1.05 * L)
    ax.set_ylim(-0.05 * L, 1.05 * L)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title is None:
        mode = "boundary only" if boundary_only else "all elements"
        title = (
            f"Mesh JSON ({mode}) + Graph mesh\n"
            f"FE: {len(coords)} nodes, {len(elements_0)} elems  |  "
            f"Graph: {graph.n_nodes} nodes, {graph.n_bars} bars"
        )
    ax.set_title(title)
    ax.legend(loc="upper right")
    fig.tight_layout()

    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# 4.  plot_mesh_json_periodic  –  mesh + periodic node pairs
# ---------------------------------------------------------------------------


# Distinct colours that are easy to tell apart (no colorscale).
_PAIR_COLORS = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
    "#dcbeff", "#9A6324", "#800000", "#aaffc3", "#808000",
    "#000075", "#a9a9a9", "#e6beff", "#ffe119", "#ffd8b1",
]


def plot_mesh_json_periodic(
    mesh_path: str,
    *,
    element_color: str = "lightblue",
    edge_color: str = "blue",
    node_size: float = 3,
    pair_node_size: float = 50,
    label_fontsize: float = 7,
    figsize: tuple = (12, 12),
    show: bool = True,
):
    """Plot a mesh JSON file together with its stored periodic node pairs.

    Parameters
    ----------
    mesh_path : str
        Path to the ``*.mesh.json`` mesh file.
    element_color, edge_color : str
        Mesh fill / edge colours.
    node_size : float
        Marker size for ordinary mesh nodes.
    pair_node_size : float
        Marker size for periodic-pair nodes.
    label_fontsize : float
        Font size for the ``LR1``, ``UL3``, … labels.
    figsize : tuple
        Figure size.
    show : bool
        Call ``plt.show()`` at the end.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    # --- read mesh ---------------------------------------------------------
    nodes_raw, elements_raw, payload = read_mesh_json(mesh_path, include_metadata=True)
    coords = np.array([(x, y) for x, y, _ in nodes_raw])
    elements_0 = elements_raw
    L = coords.max()

    # --- read periodic pairs -----------------------------------------------
    periodic = payload.get("periodic", {})
    lr_pairs = [tuple(pair) for pair in periodic.get("left_right_pairs", [])]
    tb_pairs = [tuple(pair) for pair in periodic.get("top_bottom_pairs", [])]

    # --- figure ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=figsize)

    # Elements
    polygons = [coords[e] for e in elements_0]
    ax.add_collection(PolyCollection(
        polygons,
        facecolor=element_color,
        edgecolor=edge_color,
        linewidth=0.5,
        alpha=0.7,
    ))

    # All nodes (small, grey)
    ax.scatter(coords[:, 0], coords[:, 1], s=node_size,
               c="black", zorder=4)

    # --- helper to plot a pair list ----------------------------------------
    def _plot_pairs(pairs, prefix, offset_vec):
        for k, (i, j) in enumerate(pairs):
            colour = _PAIR_COLORS[k % len(_PAIR_COLORS)]
            tag = f"{prefix}{k + 1}"
            for idx in (i, j):
                ax.scatter(coords[idx, 0], coords[idx, 1],
                           s=pair_node_size, c=colour, edgecolors="black",
                           linewidths=0.5, zorder=6)
                ax.annotate(
                    tag,
                    xy=(coords[idx, 0], coords[idx, 1]),
                    xytext=offset_vec,
                    textcoords="offset points",
                    fontsize=label_fontsize,
                    fontweight="bold",
                    color=colour,
                    ha="center", va="center",
                    zorder=7,
                )

    _plot_pairs(lr_pairs, "LR", (0, 8))
    _plot_pairs(tb_pairs, "TB", (8, 0))

    ax.set_xlim(-0.05 * L, 1.05 * L)
    ax.set_ylim(-0.05 * L, 1.05 * L)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    n_lr = len(lr_pairs)
    n_tb = len(tb_pairs)
    ax.set_title(
        f"Mesh JSON + periodic pairs  "
        f"({len(coords)} nodes, {len(elements_0)} elems, "
        f"{n_lr} LR pairs, {n_tb} TB pairs)"
    )
    fig.tight_layout()

    if show:
        plt.show()
    return fig
