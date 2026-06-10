import numpy as np
import scipy.stats
import microstructpy as msp
import pickle
import subprocess

import re
import numpy as np
import matplotlib.tri as tri
import matplotlib.pyplot as plt


import numpy as np
from collections import defaultdict, deque

import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm


def plot_J1_graph_mesh(DATA_J1, ti, ax=None, show_node_labels=False,
                       bar_color='b', node_color='red', node_size=15,
                       linewidth=1.0, figsize=(10, 8), title=None,
                       show_undeformed=False, undeformed_color='0.75',
                       magnification=1.0,
                       color_by=None, cmap='coolwarm', vmin=None, vmax=None,
                       show_normals=False, normal_scale=0.02,
                       normal_color='green',
                       node_scale=1.0,
                       plot_ten_comp='both',
                       plot_ten_comp_color_bar=True):
    """
    Plot the graph mesh from a DATA_J1 dictionary at a given timestep.

    Parameters
    ----------
    ...
    node_scale : float
        Multiply every node coordinate by this factor.
    """
    if ti < 0 or ti >= len(DATA_J1['t']):
        raise ValueError(f"ti={ti} out of range [0, {len(DATA_J1['t']) - 1}]")

    n_nodes = len(DATA_J1['nodes'])
    bars_connectivity = DATA_J1['bars_connectivity']

    # Build node positions at the requested timestep
    nodes_at_ti = {}
    if magnification != 1.0:
        for nidx in range(n_nodes):
            x0, y0 = DATA_J1['nodes'][nidx][0]
            xd, yd = DATA_J1['nodes'][nidx][ti]
            x = x0 + magnification * (xd - x0)
            y = y0 + magnification * (yd - y0)
            nodes_at_ti[nidx] = (x * node_scale, y * node_scale)
    else:
        for nidx in range(n_nodes):
            x, y = DATA_J1['nodes'][nidx][ti]
            nodes_at_ti[nidx] = (x * node_scale, y * node_scale)

    # ------------------------------------------------------------------
    # Pre-compute per-segment scalar values if color_by is requested
    # ------------------------------------------------------------------
    seg_values = []  # flat list of one scalar per segment (across all bars)
    seg_coords = []  # matching list of ((x0,y0),(x1,y1))
    seg_normals = [] # matching list of (nx, ny)
    seg_axial_values = []  # always axial, used for tension/compression filtering

    if color_by is not None or show_normals or plot_ten_comp != 'both' or not plot_ten_comp_color_bar:
        for bar_id, segments in bars_connectivity.items():
            bar_ti = DATA_J1['bars'][bar_id][ti]
            normals = bar_ti['normals']
            SS = bar_ti['SS']  # list of (S11, S22, S12) per node
            for seg_idx, (sn, en) in enumerate(segments):
                p0 = nodes_at_ti[sn]
                p1 = nodes_at_ti[en]
                seg_coords.append((p0, p1))
                seg_normals.append(normals[seg_idx])

                s11_a, s22_a, s12_a = SS[seg_idx]
                s11_b, s22_b, s12_b = SS[seg_idx + 1]
                s11_m = (s11_a + s11_b) / 2.0
                s22_m = (s22_a + s22_b) / 2.0
                s12_m = (s12_a + s12_b) / 2.0
                nx_, ny_ = normals[seg_idx]
                n_vec = np.array([nx_, ny_])
                S_mat = np.array([[s11_m, s12_m],
                                  [s12_m, s22_m]])
                axial_val = float(n_vec @ S_mat @ n_vec)
                seg_axial_values.append(axial_val)

                if color_by is not None:
                    if color_by == 'S11':
                        seg_values.append(s11_m)
                    elif color_by == 'S22':
                        seg_values.append(s22_m)
                    elif color_by == 'S12':
                        seg_values.append(s12_m)
                    elif color_by == 'axial':
                        seg_values.append(axial_val)
                    else:
                        raise ValueError(
                            f"color_by='{color_by}' not recognised. "
                            f"Use 'S11', 'S22', 'S12', or 'axial'.")

    # ------------------------------------------------------------------
    # Set up color mapping with diverging colormap (blue-black-red)
    # ------------------------------------------------------------------
    scalar_map = None
    if color_by is not None and seg_values:
        arr = np.array(seg_values)
        
        # Create custom diverging colormap: blue -> black -> red
        from matplotlib.colors import LinearSegmentedColormap
        colors = ['blue', 'white', 'red']
        n_bins = 256
        cmap_diverging = LinearSegmentedColormap.from_list('blue_black_red', colors, N=n_bins)
        
        # Set vmin and vmax symmetrically around zero
        if vmin is None or vmax is None:
            abs_max = max(abs(arr.min()), abs(arr.max()))
            if abs_max == 0:
                abs_max = 1.0  # fallback when all values are zero
            _vmin = -abs_max if vmin is None else vmin
            _vmax = abs_max if vmax is None else vmax
        else:
            _vmin = vmin
            _vmax = vmax

        # Guard: TwoSlopeNorm requires vmin < vcenter < vmax
        if _vmin >= 0.0:
            _vmin = -1e-10
        if _vmax <= 0.0:
            _vmax = 1e-10

        norm = mcolors.TwoSlopeNorm(vmin=_vmin, vcenter=0.0, vmax=_vmax)
        scalar_map = cm.ScalarMappable(norm=norm, cmap=cmap_diverging)
        scalar_map.set_array(arr)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # --- optional undeformed overlay ---
    if show_undeformed:
        for bar_id, segments in bars_connectivity.items():
            for sn, en in segments:
                x0s, y0s = DATA_J1['nodes'][sn][0]
                x0e, y0e = DATA_J1['nodes'][en][0]
                ax.plot([x0s * node_scale, x0e * node_scale],
                        [y0s * node_scale, y0e * node_scale],
                        color=undeformed_color, linewidth=linewidth * 0.8,
                        zorder=1)

    # --- deformed bars ---
    if plot_ten_comp not in ('both', 't', 'c'):
        raise ValueError("plot_ten_comp must be one of: 'both', 't', 'c'")

    if plot_ten_comp == 't':
        # Plot only bars in tension with a fixed solid red color.
        for (p0, p1), axial_val in zip(seg_coords, seg_axial_values):
            if axial_val > 0:
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color='red',
                        linewidth=linewidth, zorder=2)
    elif plot_ten_comp == 'c':
        # Plot only bars in compression with a fixed solid blue color.
        for (p0, p1), axial_val in zip(seg_coords, seg_axial_values):
            if axial_val < 0:
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color='blue',
                        linewidth=linewidth, zorder=2)
    elif not plot_ten_comp_color_bar:
        # Plot both classes with solid sign colors and no colorbar,
        # regardless of the selected scalar field.
        for (p0, p1), axial_val in zip(seg_coords, seg_axial_values):
            if axial_val > 0:
                c = 'red'
            elif axial_val < 0:
                c = 'blue'
            else:
                c = bar_color
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=c,
                    linewidth=linewidth, zorder=2)
    elif color_by is not None and scalar_map is not None:
        for idx, ((p0, p1), val) in enumerate(zip(seg_coords, seg_values)):
            c = scalar_map.to_rgba(val)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=c,
                    linewidth=linewidth, zorder=2)
        fig.colorbar(scalar_map, ax=ax, label=color_by, shrink=0.8)
    else:
        for bar_id, segments in bars_connectivity.items():
            for sn, en in segments:
                xs, ys = nodes_at_ti[sn]
                xe, ye = nodes_at_ti[en]
                ax.plot([xs, xe], [ys, ye], color=bar_color,
                        linewidth=linewidth, zorder=2)

    # --- normals ---
    if show_normals:
        for (p0, p1), (nx_, ny_) in zip(seg_coords, seg_normals):
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            ax.annotate(
                "", xy=(mid[0] + nx_ * normal_scale,
                        mid[1] + ny_ * normal_scale),
                xytext=mid,
                arrowprops=dict(arrowstyle="->", color=normal_color, lw=0.8),
                zorder=4)

    # --- nodes ---
    xvals = [p[0] for p in nodes_at_ti.values()]
    yvals = [p[1] for p in nodes_at_ti.values()]
    ax.scatter(xvals, yvals, c=node_color, s=node_size, zorder=5)

    if show_node_labels:
        for nid, (x, y) in nodes_at_ti.items():
            ax.annotate(str(nid), (x, y), fontsize=6, ha='center',
                        va='bottom', textcoords='offset points', xytext=(0, 3))

    if title is None:
        mag_str = f", mag={magnification:.0f}x" if magnification != 1.0 else ""
        cb_str = f", color={color_by}" if color_by else ""
        sc_str = f", scale={node_scale:.2g}" if node_scale != 1.0 else ""
        title = f"J1 Graph Mesh — ti={ti}, t={DATA_J1['t'][ti]:.4g}{mag_str}{sc_str}{cb_str}"
    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)

    return ax


def plot_T1_triangulation_mesh(
    DATA_T1, ti,
    ax=None,
    figsize=(10, 8),
    title=None,
    # --- mesh geometry ---
    show_edges=True,
    edge_color='k',
    linewidth=0.5,
    # --- node display ---
    show_nodes=False,
    show_node_labels=False,
    node_color='red',
    node_size=10,
    # --- face colouring ---
    color_by_area=True,
    custom_values=None,
    colorbar_label=None,
    cmap='RdYlGn',
    vmin=None,
    vmax=None,
    color_limit=None,
    face_color='lightblue',
    face_alpha=0.7,
    # --- undeformed overlay ---
    show_undeformed=False,
    undeformed_edge_color='0.75',
    # --- deformation magnification ---
    magnification=1.0,
    # --- coordinate scaling ---
    node_scale=1.0,
    # --- colorbar ---
    show_colorbar=True,
):
    """
    Plot the triangulation mesh from a DATA_T1 dictionary at a given timestep.

    Parameters
    ----------
    DATA_T1 : dict
        Dictionary produced by ``create_PKL_T1``.  Must have keys
        ``'t'``, ``'nodes'``, ``'elements'``,
        ``'elements_area'``, ``'elements_area_normalized'``.
    ti : int
        Timestep index (0-based).
    ax : matplotlib Axes, optional
        Axes to draw on.  A new figure+axes is created when *None*.
    figsize : tuple
        Figure size passed to ``plt.subplots`` (used only when *ax* is None).
    title : str, optional
        Axes title.  Auto-generated when *None*.
    show_edges : bool
        Draw triangle edges.
    edge_color : str
        Colour of triangle edges.
    linewidth : float
        Line width of triangle edges.
    show_nodes : bool
        Scatter-plot the triangulation nodes.
    show_node_labels : bool
        Annotate each node with its 1-based id.
    node_color : str
        Node scatter colour.
    node_size : float
        Node scatter marker size.
    color_by_area : bool
        Fill each triangle with a colour proportional to
        ``area(ti) / area(undeformed)``.  When *False* all triangles
        are filled with *face_color*.  Automatically set to *True* when
        *custom_values* is provided.
    custom_values : array-like, optional
        Per-element scalar values to use for colouring instead of the
        normalised area.  Must have the same length as the number of
        elements in *DATA_T1*, ordered by ``sorted(elements.keys())``.
        When provided, *color_by_area* is treated as *True*.
    colorbar_label : str, optional
        Label for the colorbar.  Defaults to ``'A / A₀'`` when colouring
        by area, or an empty string when *custom_values* are used.
    cmap : str
        Colormap name used when *color_by_area* is *True*.
        Defaults to ``'RdYlGn'`` (green ≈ 1, red = large deviation).
    vmin, vmax : float, optional
        Colour scale limits for the normalised area.  Defaults to the
        data range when *None*.
    face_color : str
        Solid fill colour used when *color_by_area* is *False*.
    face_alpha : float
        Alpha of triangle faces (0 = transparent, 1 = opaque).
    show_undeformed : bool
        Overlay the undeformed (ti=0) mesh as faint grey edges.
    undeformed_edge_color : str
        Edge colour for the undeformed overlay.
    magnification : float
        Exaggerate the displacement from the reference (ti=0) state.
        1.0 = true deformed shape.
    node_scale : float
        Multiply every coordinate by this factor (useful for unit
        conversion).
    show_colorbar : bool
        Add a colourbar when *color_by_area* is *True*.

    Returns
    -------
    ax : matplotlib Axes
    """
    n_ti = len(DATA_T1['t'])
    if ti < 0 or ti >= n_ti:
        raise ValueError(f"ti={ti} out of range [0, {n_ti - 1}]")

    # ------------------------------------------------------------------
    # Build node coordinate arrays
    # ------------------------------------------------------------------
    node_ids = sorted(DATA_T1['nodes'][0].keys())   # 1-based ints
    n_nodes  = len(node_ids)

    def _deformed_xy(time_index):
        """Return (xs, ys) arrays at *time_index* with magnification."""
        xs = np.empty(n_nodes)
        ys = np.empty(n_nodes)
        for arr_idx, nid in enumerate(node_ids):
            if magnification != 1.0:
                x0, y0, _ = DATA_T1['nodes'][0][nid]
                xd, yd, _ = DATA_T1['nodes'][time_index][nid]
                xs[arr_idx] = (x0 + magnification * (xd - x0)) * node_scale
                ys[arr_idx] = (y0 + magnification * (yd - y0)) * node_scale
            else:
                xd, yd, _ = DATA_T1['nodes'][time_index][nid]
                xs[arr_idx] = xd * node_scale
                ys[arr_idx] = yd * node_scale
        return xs, ys

    # nid -> 0-based array index
    nid_to_idx = {nid: i for i, nid in enumerate(node_ids)}

    # ------------------------------------------------------------------
    # Build triangle connectivity (0-based into node_ids list)
    # Elements store raw 0-based indices from the .tri file.
    # ------------------------------------------------------------------
    elem_ids    = sorted(DATA_T1['elements'].keys())
    n_elems     = len(elem_ids)
    triangles   = np.array([DATA_T1['elements'][eid] for eid in elem_ids], dtype=int)   # (n_elems, 3) – 0-based

    # ------------------------------------------------------------------
    # Per-element scalar: normalised area (always computed as fallback)
    # ------------------------------------------------------------------
    norm_areas = np.array(
        [DATA_T1['elements_area_normalized'][eid][ti] for eid in elem_ids],
        dtype=float,
    )

    # Resolve which values to use for colouring
    _custom = np.asarray(custom_values, dtype=float) if custom_values is not None else None
    _do_color = color_by_area or (_custom is not None)
    _values   = _custom if _custom is not None else norm_areas
    _cb_label = colorbar_label if colorbar_label is not None else (
        'A / A₀' if _custom is None else ''
    )

    # ------------------------------------------------------------------
    # Colour mapping
    # ------------------------------------------------------------------
    if _do_color:
        if color_limit is not None:
            # Log-scale diverging map: [1/color_limit, color_limit]
            # red < 1, white = 1, blue > 1
            import matplotlib.colors as _mcolors
            _lim = float(color_limit)
            _vmin_log = 1.0 / _lim
            _vmax_log = _lim
            # Build red-white-blue diverging colormap centred at 1.0
            _rwb = _mcolors.LinearSegmentedColormap.from_list(
                'rwb_log', ['red', 'white', 'blue']
            )
            norm_obj = _mcolors.LogNorm(vmin=_vmin_log, vmax=_vmax_log)
            cmap_obj = _rwb
        else:
            _vmin = vmin if vmin is not None else _values.min()
            _vmax = vmax if vmax is not None else _values.max()
            norm_obj = mcolors.Normalize(vmin=_vmin, vmax=_vmax)
            # Built-in custom colormap aliases (two-colour linear gradients)
            _CUSTOM_CMAPS = {
                'red_white'  : ['red',   'white'],
                'white_red'  : ['white', 'red'],
                'blue_white' : ['blue',  'white'],
                'white_blue' : ['white', 'blue'],
            }
            if cmap in _CUSTOM_CMAPS:
                cmap_obj = mcolors.LinearSegmentedColormap.from_list(
                    cmap, _CUSTOM_CMAPS[cmap]
                )
            else:
                cmap_obj = cm.get_cmap(cmap)
        scalar_map = cm.ScalarMappable(norm=norm_obj, cmap=cmap_obj)
        scalar_map.set_array(_values)
        face_colors = [scalar_map.to_rgba(v, alpha=face_alpha) for v in _values]
    else:
        face_colors = [face_color] * n_elems

    # ------------------------------------------------------------------
    # Create axes
    # ------------------------------------------------------------------
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    xs, ys = _deformed_xy(ti)

    # ------------------------------------------------------------------
    # Optional undeformed overlay
    # ------------------------------------------------------------------
    if show_undeformed and ti != 0:
        xs0, ys0 = _deformed_xy(0)
        tri_obj0 = tri.Triangulation(xs0, ys0, triangles)
        ax.triplot(tri_obj0, color=undeformed_edge_color,
                   linewidth=linewidth * 0.7, zorder=1)

    # ------------------------------------------------------------------
    # Filled triangles
    # ------------------------------------------------------------------
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection

    patches = []
    for tri_idx, (n0, n1, n2) in enumerate(triangles):
        verts = np.array([
            [xs[n0], ys[n0]],
            [xs[n1], ys[n1]],
            [xs[n2], ys[n2]],
        ])
        patches.append(Polygon(verts, closed=True))

    col = PatchCollection(patches, facecolors=face_colors,
                          edgecolors=edge_color if show_edges else 'none',
                          linewidths=linewidth, zorder=2)
    ax.add_collection(col)

    # ------------------------------------------------------------------
    # Optional edge overlay (drawn on top for clarity)
    # ------------------------------------------------------------------
    if show_edges:
        tri_obj = tri.Triangulation(xs, ys, triangles)
        ax.triplot(tri_obj, color=edge_color, linewidth=linewidth, zorder=3)

    # ------------------------------------------------------------------
    # Optional nodes
    # ------------------------------------------------------------------
    if show_nodes:
        ax.scatter(xs, ys, c=node_color, s=node_size, zorder=5)

    if show_node_labels:
        for arr_idx, nid in enumerate(node_ids):
            ax.annotate(str(nid), (xs[arr_idx], ys[arr_idx]),
                        fontsize=6, ha='center', va='bottom',
                        textcoords='offset points', xytext=(0, 3))

    # ------------------------------------------------------------------
    # Colourbar
    # ------------------------------------------------------------------
    if _do_color and show_colorbar:
        fig.colorbar(scalar_map, ax=ax, label=_cb_label, shrink=0.8)

    # ------------------------------------------------------------------
    # Axis decoration
    # ------------------------------------------------------------------
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.grid(True, linestyle='--', alpha=0.4)

    if title is None:
        mag_str = f', mag={magnification:.0f}x' if magnification != 1.0 else ''
        sc_str  = f', scale={node_scale:.2g}'   if node_scale  != 1.0 else ''
        cb_str  = ', A/A₀'                       if color_by_area      else ''
        title   = (f'T1 Triangulation — ti={ti}, '
                   f't={DATA_T1["t"][ti]:.4g}{mag_str}{sc_str}{cb_str}')
    ax.set_title(title)

    return ax


# def plot_J1_graph_mesh(DATA_J1, ti, ax=None, show_node_labels=False,
#                        bar_color='b', node_color='red', node_size=15,
#                        linewidth=1.0, figsize=(10, 8), title=None,
#                        show_undeformed=False, undeformed_color='0.75',
#                        magnification=1.0,
#                        color_by=None, cmap='coolwarm', vmin=None, vmax=None,
#                        show_normals=False, normal_scale=0.02,
#                        normal_color='green',
#                        node_scale=1.0):
#     """
#     Plot the graph mesh from a DATA_J1 dictionary at a given timestep.

#     Parameters
#     ----------
#     ...
#     node_scale : float
#         Multiply every node coordinate by this factor.
#     """
#     if ti < 0 or ti >= len(DATA_J1['t']):
#         raise ValueError(f"ti={ti} out of range [0, {len(DATA_J1['t']) - 1}]")

#     n_nodes = len(DATA_J1['nodes'])
#     bars_connectivity = DATA_J1['bars_connectivity']

#     # Build node positions at the requested timestep
#     nodes_at_ti = {}
#     if magnification != 1.0:
#         for nidx in range(n_nodes):
#             x0, y0 = DATA_J1['nodes'][nidx][0]
#             xd, yd = DATA_J1['nodes'][nidx][ti]
#             x = x0 + magnification * (xd - x0)
#             y = y0 + magnification * (yd - y0)
#             nodes_at_ti[nidx] = (x * node_scale, y * node_scale)
#     else:
#         for nidx in range(n_nodes):
#             x, y = DATA_J1['nodes'][nidx][ti]
#             nodes_at_ti[nidx] = (x * node_scale, y * node_scale)

#     # ------------------------------------------------------------------
#     # Pre-compute per-segment scalar values if color_by is requested
#     # ------------------------------------------------------------------
#     seg_values = []  # flat list of one scalar per segment (across all bars)
#     seg_coords = []  # matching list of ((x0,y0),(x1,y1))
#     seg_normals = [] # matching list of (nx, ny)

#     if color_by is not None or show_normals:
#         for bar_id, segments in bars_connectivity.items():
#             bar_ti = DATA_J1['bars'][bar_id][ti]
#             normals = bar_ti['normals']
#             SS = bar_ti['SS']  # list of (S11, S22, S12) per node
#             for seg_idx, (sn, en) in enumerate(segments):
#                 p0 = nodes_at_ti[sn]
#                 p1 = nodes_at_ti[en]
#                 seg_coords.append((p0, p1))
#                 seg_normals.append(normals[seg_idx])

#                 if color_by is not None:
#                     s11_a, s22_a, s12_a = SS[seg_idx]
#                     s11_b, s22_b, s12_b = SS[seg_idx + 1]
#                     s11_m = (s11_a + s11_b) / 2.0
#                     s22_m = (s22_a + s22_b) / 2.0
#                     s12_m = (s12_a + s12_b) / 2.0

#                     if color_by == 'S11':
#                         seg_values.append(s11_m)
#                     elif color_by == 'S22':
#                         seg_values.append(s22_m)
#                     elif color_by == 'S12':
#                         seg_values.append(s12_m)
#                     elif color_by == 'axial':
#                         nx_, ny_ = normals[seg_idx]
#                         n_vec = np.array([nx_, ny_])
#                         S_mat = np.array([[s11_m, s12_m],
#                                           [s12_m, s22_m]])
#                         seg_values.append(float(n_vec @ S_mat @ n_vec))
#                     else:
#                         raise ValueError(
#                             f"color_by='{color_by}' not recognised. "
#                             f"Use 'S11', 'S22', 'S12', or 'axial'.")

#     # ------------------------------------------------------------------
#     # Set up color mapping
#     # ------------------------------------------------------------------
#     scalar_map = None
#     if color_by is not None and seg_values:
#         arr = np.array(seg_values)
#         _vmin = vmin if vmin is not None else arr.min()
#         _vmax = vmax if vmax is not None else arr.max()
#         norm = mcolors.Normalize(vmin=_vmin, vmax=_vmax)
#         scalar_map = cm.ScalarMappable(norm=norm, cmap=cmap)
#         scalar_map.set_array(arr)

#     if ax is None:
#         fig, ax = plt.subplots(figsize=figsize)
#     else:
#         fig = ax.figure

#     # --- optional undeformed overlay ---
#     if show_undeformed:
#         for bar_id, segments in bars_connectivity.items():
#             for sn, en in segments:
#                 x0s, y0s = DATA_J1['nodes'][sn][0]
#                 x0e, y0e = DATA_J1['nodes'][en][0]
#                 ax.plot([x0s * node_scale, x0e * node_scale],
#                         [y0s * node_scale, y0e * node_scale],
#                         color=undeformed_color, linewidth=linewidth * 0.8,
#                         zorder=1)

#     # --- deformed bars ---
#     if color_by is not None and scalar_map is not None:
#         for idx, ((p0, p1), val) in enumerate(zip(seg_coords, seg_values)):
#             c = scalar_map.to_rgba(val)
#             ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=c,
#                     linewidth=linewidth, zorder=2)
#         fig.colorbar(scalar_map, ax=ax, label=color_by, shrink=0.8)
#     else:
#         for bar_id, segments in bars_connectivity.items():
#             for sn, en in segments:
#                 xs, ys = nodes_at_ti[sn]
#                 xe, ye = nodes_at_ti[en]
#                 ax.plot([xs, xe], [ys, ye], color=bar_color,
#                         linewidth=linewidth, zorder=2)

#     # --- normals ---
#     if show_normals:
#         for (p0, p1), (nx_, ny_) in zip(seg_coords, seg_normals):
#             mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
#             ax.annotate(
#                 "", xy=(mid[0] + nx_ * normal_scale,
#                         mid[1] + ny_ * normal_scale),
#                 xytext=mid,
#                 arrowprops=dict(arrowstyle="->", color=normal_color, lw=0.8),
#                 zorder=4)

#     # --- nodes ---
#     xvals = [p[0] for p in nodes_at_ti.values()]
#     yvals = [p[1] for p in nodes_at_ti.values()]
#     ax.scatter(xvals, yvals, c=node_color, s=node_size, zorder=5)

#     if show_node_labels:
#         for nid, (x, y) in nodes_at_ti.items():
#             ax.annotate(str(nid), (x, y), fontsize=6, ha='center',
#                         va='bottom', textcoords='offset points', xytext=(0, 3))

#     if title is None:
#         mag_str = f", mag={magnification:.0f}x" if magnification != 1.0 else ""
#         cb_str = f", color={color_by}" if color_by else ""
#         sc_str = f", scale={node_scale:.2g}" if node_scale != 1.0 else ""
#         title = f"J1 Graph Mesh — ti={ti}, t={DATA_J1['t'][ti]:.4g}{mag_str}{sc_str}{cb_str}"
#     ax.set_title(title)
#     ax.set_xlabel('X')
#     ax.set_ylabel('Y')
#     ax.set_aspect('equal')
#     ax.grid(True, linestyle='--', alpha=0.5)

#     return ax




def add_id(nodes):
    """
    Creates a dictionary mapping node IDs to node coordinates.

    Args:
        nodes (list of tuple): A list of nodes where each node is represented by a tuple (x, y).

    Returns:
        dict: Dictionary where keys are node IDs (strings starting from '1') 
              and values are the coordinate tuples (x, y).
    """
    nodes_dict = {
        str(i + 1): node 
        for i, node in enumerate(nodes)
    }
    
    return nodes_dict

def filter_nodes(nodes, condition):
    """
    Filter nodes based on a condition.
    
    Parameters:
    -----------
    nodes : dict
        Dictionary where keys are node numbers (as strings) and values are (x, y) tuples
    condition : callable
        A function that takes a node coordinate tuple (x, y) and returns True/False
        
    Returns:
    --------
    tuple of dict
        (filtered_nodes, removed_nodes) - Two dictionaries:
        - filtered_nodes: containing only nodes that satisfy the condition
        - removed_nodes: containing nodes that were filtered out
        
    Examples:
    ---------
    # Filter nodes where x < 1
    filtered, removed = filter_nodes(nodes, lambda node: node[0] < 1)
    
    # Filter nodes where y > 0.5
    filtered, removed = filter_nodes(nodes, lambda node: node[1] > 0.5)
    
    # Filter nodes in a circular region
    filtered, removed = filter_nodes(nodes, lambda node: node[0]**2 + node[1]**2 < 1)
    """
    filtered_nodes = {key: value for key, value in nodes.items() if condition(value)}
    removed_nodes = {key: value for key, value in nodes.items() if not condition(value)}
    return filtered_nodes, removed_nodes


def filter_elements_from_nodes(elements, nodes):
    """
    Filter elements to keep only those whose nodes all exist in the nodes dictionary.
    
    Parameters:
    -----------
    elements : dict
        Dictionary where keys are element numbers (as strings) and values are lists 
        of node numbers that form each element
    nodes : dict
        Dictionary where keys are node numbers (as strings) and values are (x, y) tuples
        
    Returns:
    --------
    tuple of dict
        (filtered_elements, removed_elements) - Two dictionaries:
        - filtered_elements: containing only elements where all constituent nodes exist
        - removed_elements: containing elements that were filtered out
        
    Examples:
    ---------
    elements = {
        '1': [34, 35, 46],
        '2': [34, 46, 45],
        '3': [35, 36, 47]
    }
    
    nodes = {
        '34': (0.5, 0.3),
        '35': (1.5, 0.8),
        '46': (0.2, 1.2)
    }
    
    # Only element '1' will be kept since nodes 45, 36, 47 don't exist
    filtered, removed = filter_elements_from_nodes(elements, nodes)
    # Result: filtered = {'1': [34, 35, 46]}
    #         removed = {'2': [34, 46, 45], '3': [35, 36, 47]}
    """
    filtered_elements = {}
    removed_elements = {}
    
    for elem_key, node_list in elements.items():
        # Check if all nodes in this element exist in the nodes dictionary
        if all(str(node_num) in nodes for node_num in node_list):
            filtered_elements[elem_key] = node_list
        else:
            removed_elements[elem_key] = node_list
    
    return filtered_elements, removed_elements


def filter_barycenters(barycenters, elements):
    """
    Filter barycenters to keep only those whose corresponding elements exist.
    
    Parameters:
    -----------
    barycenters : dict
        Dictionary where keys are element numbers (as strings) and values are (x, y) tuples
        representing the barycenter coordinates
    elements : dict
        Dictionary where keys are element numbers (as strings) and values are lists 
        of node numbers that form each element
        
    Returns:
    --------
    tuple of dict
        (filtered_barycenters, removed_barycenters) - Two dictionaries:
        - filtered_barycenters: containing only barycenters for elements that exist
        - removed_barycenters: containing barycenters that were filtered out
        
    Examples:
    ---------
    barycenters = {
        '1': (0.5, 0.4),
        '2': (1.2, 0.8),
        '3': (0.8, 1.0),
        '4': (1.5, 1.2)
    }
    
    elements = {
        '1': [34, 35, 46],
        '4': [50, 51, 52],
        '5': [60, 61, 62]
    }
    
    filtered, removed = filter_barycenters(barycenters, elements)
    # Result: filtered = {'1': (0.5, 0.4), '4': (1.5, 1.2)}
    #         removed = {'2': (1.2, 0.8), '3': (0.8, 1.0)}
    # Barycenter '2' excluded because element '2' doesn't exist
    # Barycenter '3' excluded because element '3' doesn't exist
    """
    filtered_barycenters = {key: value for key, value in barycenters.items() if key in elements}
    removed_barycenters = {key: value for key, value in barycenters.items() if key not in elements}
    return filtered_barycenters, removed_barycenters


# def filter_nodes(nodes, condition):
#     """
#     Filter nodes based on a condition.
    
#     Parameters:
#     -----------
#     nodes : dict
#         Dictionary where keys are node numbers (as strings) and values are (x, y) tuples
#     condition : callable
#         A function that takes a node coordinate tuple (x, y) and returns True/False
        
#     Returns:
#     --------
#     dict
#         Filtered dictionary containing only nodes that satisfy the condition
        
#     Examples:
#     ---------
#     # Filter nodes where x < 1
#     filtered = filter_nodes(nodes, lambda node: node[0] < 1)
    
#     # Filter nodes where y > 0.5
#     filtered = filter_nodes(nodes, lambda node: node[1] > 0.5)
    
#     # Filter nodes in a circular region
#     filtered = filter_nodes(nodes, lambda node: node[0]**2 + node[1]**2 < 1)
#     """
#     return {key: value for key, value in nodes.items() if condition(value)}



# def filter_elements_from_nodes(elements, nodes):
#     """
#     Filter elements to keep only those whose nodes all exist in the nodes dictionary.
    
#     Parameters:
#     -----------
#     elements : dict
#         Dictionary where keys are element numbers (as strings) and values are lists 
#         of node numbers that form each element
#     nodes : dict
#         Dictionary where keys are node numbers (as strings) and values are (x, y) tuples
        
#     Returns:
#     --------
#     dict
#         Filtered dictionary containing only elements where all constituent nodes exist
        
#     Examples:
#     ---------
#     elements = {
#         '1': [34, 35, 46],
#         '2': [34, 46, 45],
#         '3': [35, 36, 47]
#     }
    
#     nodes = {
#         '34': (0.5, 0.3),
#         '35': (1.5, 0.8),
#         '46': (0.2, 1.2)
#     }
    
#     # Only element '1' will be kept since nodes 45, 36, 47 don't exist
#     filtered = filter_elements_from_nodes(elements, nodes)
#     # Result: {'1': [34, 35, 46]}
#     """
#     filtered_elements = {}
    
#     for elem_key, node_list in elements.items():
#         # Check if all nodes in this element exist in the nodes dictionary
#         if all(str(node_num) in nodes for node_num in node_list):
#             filtered_elements[elem_key] = node_list
    
#     return filtered_elements
    

# def filter_barycenters(barycenters, elements):
#     """
#     Filter barycenters to keep only those whose corresponding elements exist.
    
#     Parameters:
#     -----------
#     barycenters : dict
#         Dictionary where keys are element numbers (as strings) and values are (x, y) tuples
#         representing the barycenter coordinates
#     elements : dict
#         Dictionary where keys are element numbers (as strings) and values are lists 
#         of node numbers that form each element
        
#     Returns:
#     --------
#     dict
#         Filtered dictionary containing only barycenters for elements that exist
        
#     Examples:
#     ---------
#     barycenters = {
#         '1': (0.5, 0.4),
#         '2': (1.2, 0.8),
#         '3': (0.8, 1.0),
#         '4': (1.5, 1.2)
#     }
    
#     elements = {
#         '1': [34, 35, 46],
#         '4': [50, 51, 52],
#         '5': [60, 61, 62]
#     }
    
#     filtered = filter_barycenters(barycenters, elements)
#     # Result: {'1': (0.5, 0.4), '4': (1.5, 1.2)}
#     # Barycenter '2' excluded because element '2' doesn't exist
#     # Barycenter '3' excluded because element '3' doesn't exist
#     # Barycenter '5' excluded because it doesn't exist in barycenters
#     """
#     return {key: value for key, value in barycenters.items() if key in elements}



def compute_hole_volume(nodes, elements, holes_surfaces, hole_key):
    """
    Compute the area (volume in 2D) of a hole defined by boundary segments.

    Parameters  
    ----------
    nodes : np.ndarray
        Array of shape (N_nodes, 2) with coordinates. **Node IDs start at 1.**
    elements : list of tuples
        Element connectivity. **Element IDs start at 1.**
    holes_surfaces : dict
        Dictionary where each key is a hole name and each value is a list of
        (element_id, face_label), e.g. ('S1', 'S2', 'S3').
    hole_key : str
        The key of the hole to compute, e.g. 'Surface-hole-246'

    Returns
    -------
    float
        Area of the hole (in 2D → this is the "volume")
    """

    # ---- 1) Extract list like [(elem_id, "S1"), ...] ----
    boundary_list = holes_surfaces[hole_key]

    # ---- 2) Map surface labels to node pairs for triangle elements ----
    face_map = {
        "S1": (0, 1),   # For tri: S1 = nodes [n1, n2]
        "S2": (1, 2),   #        S2 = nodes [n2, n3]
        "S3": (0, 2)    #        S3 = nodes [n1, n3]
    }

    boundary_edges = []

    for elem_id, surf in boundary_list:
        elem_nodes = elements[elem_id - 1]     # element IDs start at 1
        i, j = face_map[surf]                  # get correct two nodes of the face
        n1 = elem_nodes[i]
        n2 = elem_nodes[j]

        boundary_edges.append((n1, n2))

    # ---- 3) Build adjacency map to order nodes around the loop ----
    adjacency = {}
    for a, b in boundary_edges:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    # pick a start node
    start = next(iter(adjacency))
    ordered_nodes = [start]

    prev = None
    curr = start

    # follow the loop
    while True:
        neighbors = adjacency[curr]

        # choose the next neighbor that is not the previous node
        nxt = neighbors[0] if neighbors[0] != prev else neighbors[1]
        ordered_nodes.append(nxt)

        if nxt == start:
            break  # completed loop

        prev, curr = curr, nxt

    # ---- 4) Convert node IDs → coordinates ----
    coords = np.array([nodes[nid - 1] for nid in ordered_nodes])

    # ---- 5) Compute polygon area (shoelace formula) ----
    x = coords[:, 0]
    y = coords[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    return area



def compute_hole_barycenters(holes_surfaces, elements, nodes):
    """
    holes_surfaces : dict from group_surfaces_into_holes_by_nodes
    elements : (Ne, 3) array with triangle connectivity (1-based)
    nodes : (Nn, 2) array with node coordinates

    Returns:
        barycenters = {
            'Surface-hole-1': (x, y),
            'Surface-hole-2': (x, y),
            ...
        }
    """

    elements = np.asarray(elements, dtype=int)
    nodes = np.asarray(nodes, dtype=float)

    barycenters = {}

    for hole_name, elem_list in holes_surfaces.items():

        # ---- gather all unique nodes belonging to the hole ----
        hole_nodes = set()

        for elem_id, _orient in elem_list:
            n1, n2, n3 = elements[elem_id - 1]  # convert elem_id to index
            hole_nodes.update([n1, n2, n3])

        # convert to sorted list
        hole_nodes = sorted(hole_nodes)

        # ---- get node coordinates (remember nodes are 1-based!) ----
        coords = nodes[np.array(hole_nodes) - 1, :]   # shape (n, 2)

        # ---- compute barycenter ----
        cx = coords[:, 0].mean()
        cy = coords[:, 1].mean()

        barycenters[hole_name] = (cx, cy)

    return barycenters

def compute_hole_barycenters_2(holes_surfaces, elements, nodes):
    """
    holes_surfaces : dict from group_surfaces_into_holes_by_nodes
    elements : list of elements with 3 or 4 node connectivity (1-based)
    nodes : (Nn, 2) array with node coordinates

    Returns:
        barycenters = {
            'Surface-hole-1': (x, y),
            'Surface-hole-2': (x, y),
            ...
        }
    """

    nodes = np.asarray(nodes, dtype=float)

    barycenters = {}

    for hole_name, elem_list in holes_surfaces.items():

        # ---- gather all unique nodes belonging to the hole ----
        hole_nodes = set()

        for elem_id, _orient in elem_list:
            elem = elements[elem_id - 1]  # convert elem_id to index
            hole_nodes.update(elem)

        # convert to sorted list
        hole_nodes = sorted(hole_nodes)

        # ---- get node coordinates (remember nodes are 1-based!) ----
        coords = nodes[np.array(hole_nodes) - 1, :]   # shape (n, 2)

        # ---- compute barycenter ----
        cx = coords[:, 0].mean()
        cy = coords[:, 1].mean()

        barycenters[hole_name] = (cx, cy)

    return barycenters


def edge_nodes_from_side(conn, side):
    n1, n2, n3 = conn
    if side == 'S1':
        return (n1, n2)
    if side == 'S2':
        return (n2, n3)
    if side == 'S3':
        return (n3, n1)
    raise ValueError("Invalid side label")


def build_hole_surfaces(elements, individual_surfaces):
    """
    elements: list of (elemID, n1, n2, n3)
              OR a pure connectivity array but with global IDs stored elsewhere.
              YOU MUST PROVIDE global element IDs.

    individual_surfaces:
           dict: surface_name -> list( (elemID, 'S2') )
    """

    # ------------------------------------------
    # 1) Build mapping elemID -> connectivity
    # ------------------------------------------
    # CASE 1 (recommended): elements = [(id,n1,n2,n3), ...]
    # CASE 2: elements = [(n1,n2,n3), ...] AND you separately have global IDs
    #         --> user must adjust accordingly.

    elem_id_to_conn = {}

    # If first entry has length > 3 we assume format (id,n1,n2,n3)
    if len(elements[0]) == 4:
        for (eid, n1, n2, n3) in elements:
            elem_id_to_conn[eid] = (n1, n2, n3)
    else:
        # Otherwise we assume elements is ONLY (n1,n2,n3)
        # AND element IDs are 1..Ne
        for i, (n1, n2, n3) in enumerate(elements, start=1):
            elem_id_to_conn[i] = (n1, n2, n3)

    # ------------------------------------------
    # 2) Build boundary *edges* (elemID, side)
    # ------------------------------------------
    edge_records = []
    node_to_edges = defaultdict(list)

    for surf_name, entries in individual_surfaces.items():
        for elem_id, side in entries:

            if elem_id not in elem_id_to_conn:
                # This is the problem that caused empty output
                raise ValueError(
                    f"Element ID {elem_id} not in the mesh. "
                    f"Check your element numbering!"
                )

            conn = elem_id_to_conn[elem_id]
            ni, nj = edge_nodes_from_side(conn, side)

            k = len(edge_records)
            edge_records.append({
                'elem': elem_id,
                'side': side,
                'nodes': (ni, nj),
            })

            node_to_edges[ni].append(k)
            node_to_edges[nj].append(k)

    # ------------------------------------------
    # 3) Build adjacency between edges (shared node → same hole)
    # ------------------------------------------
    adj = defaultdict(set)

    for node, e_list in node_to_edges.items():
        if len(e_list) <= 1:
            continue
        base = e_list[0]
        for e in e_list[1:]:
            adj[base].add(e)
            adj[e].add(base)

    # ------------------------------------------
    # 4) Connected components of edges = holes
    # ------------------------------------------
    visited = set()
    components = []

    for k in range(len(edge_records)):
        if k in visited:
            continue
        comp = []
        queue = deque([k])
        visited.add(k)

        while queue:
            u = queue.popleft()
            comp.append(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    queue.append(v)

        components.append(comp)

    # ------------------------------------------
    # 5) Build output dictionary
    # ------------------------------------------
    holes = {}
    for i, comp in enumerate(components, start=1):
        name = f"Surface-hole-{i}"
        entries = []
        for k in comp:
            rec = edge_records[k]
            entries.append((rec['elem'], rec['side']))

        # optional sorting
        entries.sort(key=lambda x: x[0])
        holes[name] = entries

    return holes



def find_element_adjacency(elements):
    """
    elements: list of elements (triangles with 3 nodes or quads with 4 nodes)
    returns: list of [elem_i, elem_j] adjacency pairs (1-based)
    """
    elements = [np.asarray(e, dtype=int) for e in elements]
    Ne = len(elements)

    # Edge -> list of elements sharing it
    edge_map = {}

    for t in range(Ne):
        nodes = elements[t]
        n = len(nodes)
        
        # Build edges for polygon (works for triangles and quads)
        edges = []
        for i in range(n):
            edge = tuple(sorted((nodes[i], nodes[(i + 1) % n])))
            edges.append(edge)

        for e in edges:
            if e not in edge_map:
                edge_map[e] = []
            edge_map[e].append(t)

    # Now build adjacency: edges shared by exactly 2 elements
    adjacency = []
    for e, elems in edge_map.items():
        if len(elems) == 2:
            adjacency.append([elems[0] + 1, elems[1] + 1])

    return adjacency


def find_barycenters(nodes, elements):
    """
    Given nodes and elements of a mesh (triangles or quads),
    compute the barycenters of each element.

    Parameters:
    nodes : ndarray
        Array of shape (Nn, 2) or (Nn, 3) with coordinates of nodes.
    elements : list
        List of elements, each element is a list of node indices (1-based).

    Returns:
    barycenters : ndarray
        Array of shape (Ne, dim) with coordinates of element barycenters.
    """
    nodes = np.asarray(nodes, dtype=float)
    
    barycenters = []
    for elem in elements:
        # Convert to 0-based indexing
        indices = np.asarray(elem, dtype=int) - 1
        # Take the coordinates of the vertices
        elem_coords = nodes[indices]
        # Barycenter = mean of the vertices
        bary = elem_coords.mean(axis=0)
        barycenters.append(bary)
    
    return np.array(barycenters)


# def find_triangle_adjacency(elements):
#     """
#     elements: ndarray shape (Ne, 3) with 1-based node indices
#     returns: list of [tri_i, tri_j] adjacency pairs
#     """
#     elements = np.asarray(elements, dtype=int)
#     Ne = elements.shape[0]

#     # Edge -> list of triangles sharing it
#     edge_map = {}

#     for t in range(Ne):
#         n1, n2, n3 = elements[t]

#         edges = [
#             tuple(sorted((n1, n2))),
#             tuple(sorted((n2, n3))),
#             tuple(sorted((n3, n1)))
#         ]

#         for e in edges:
#             if e not in edge_map:
#                 edge_map[e] = []
#             edge_map[e].append(t)

#     # Now build adjacency: edges shared by exactly 2 triangles
#     adjacency = []
#     for e, tris in edge_map.items():
#         if len(tris) == 2:
#             adjacency.append([tris[0]+1, tris[1]+1])

#     return adjacency


# def find_barycenters(nodes, elements):
#     """
#     Given nodes and elements of a triangular mesh,
#     compute the barycenters of each triangle.

#     Parameters:
#     nodes : ndarray
#         Array of shape (Nn, 2) with coordinates of nodes.
#     elements : ndarray
#         Array of shape (Ne, 3) with indices of triangle vertices.

#     Returns:
#     barycenters : ndarray
#         Array of shape (Ne, 2) with coordinates of triangle barycenters.
#     """
#     nodes = np.asarray(nodes, dtype=float)
#     elements = np.asarray(np.array(elements)-1, dtype=int)

#     # If elements are still 1-based, uncomment this:
#     # if elements.min() == 1:
#     #     elements = elements - 1

#     # Take the coordinates of the 3 vertices for each triangle
#     tri_coords = nodes[elements]      # shape (Ne, 3, 2)

#     # Barycenters = mean of the 3 vertices (axis=1)
#     barycenters = tri_coords.mean(axis=1)   # shape (Ne, 2)

#     return barycenters




def plot_foam_mesh(nodes, elements=None, barycenters=None, adjacency=None, normals=None,
                   normal_scale=0.2, elements_to_plot=None, show_element_numbers=False,
                   node_size=0.2, plot_barycenters=True, barycenter_size=50, ax=None,
                   boundary_only=False, boundary_lw=0.5, boundary_color='black'):
    """
    Plots triangular mesh and (optional) barycenters, adjacency edges, and normal vectors.

    When inputs are dictionaries:
      - Element IDs are preserved exactly (starting from 1).
      - No reindexing of elements, barycenters, adjacency, or normals occurs.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        If provided, draw onto this axes instead of creating a new figure.
    boundary_only : bool
        If True, draw only the outer boundary edges of the mesh (edges
        belonging to a single element) instead of every element edge.
    boundary_lw : float
        Line width for boundary edges (used when *boundary_only* is True).
    boundary_color : str
        Color for boundary edges (used when *boundary_only* is True).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 9))
    else:
        fig = ax.figure

    # ------------------------------------------------------------
    # HANDLE NODES
    # ------------------------------------------------------------
    if isinstance(nodes, dict):
        max_node_id = max(int(k) for k in nodes.keys())
        nodes_array = np.full((max_node_id, 2), np.nan)
        for node_id_str, coords in nodes.items():
            idx = int(node_id_str) - 1  # Only nodes are converted to 0-based for NumPy
            nodes_array[idx] = coords
        nodes = nodes_array
    else:
        nodes = np.array(nodes)

    # ------------------------------------------------------------
    # HANDLE ELEMENTS
    # ------------------------------------------------------------
    is_elements_dict = isinstance(elements, dict) if elements is not None else False

    if elements is not None:
        if is_elements_dict:
            # Keep a list of (element_id, node_indices) preserving IDs
            element_items = sorted(elements.items(), key=lambda x: int(x[0]))
            element_ids = [int(k) for k, _ in element_items]
            # Keep as list-of-lists to support mixed tri/quad meshes
            elements_list = [[int(n) - 1 for n in elem_nodes] for _, elem_nodes in element_items]
        else:
            # Convert to list-of-lists, handling both uniform and mixed
            elements_list = [[int(n) - 1 for n in elem] for elem in elements]
            element_ids = list(range(1, len(elements_list) + 1))
            
    else:
        elements_list = None
        element_ids = None

    # ------------------------------------------------------------
    # HANDLE BARYCENTERS
    # ------------------------------------------------------------

    if barycenters is not None:
        if isinstance(barycenters, dict):
            # Keep as dict: element_id -> (x, y)
            barycenters_dict = {int(k): np.array(v) for k, v in barycenters.items()}
        else:
            barycenters_array = np.array(barycenters)
            barycenters_dict = {eid: barycenters_array[i]
                                for i, eid in enumerate(element_ids)}
            
        if plot_barycenters is True:      # Plot the barycenters
            barycenter_coords = np.array(list(barycenters_dict.values()))
            ax.scatter(barycenter_coords[:, 0], barycenter_coords[:, 1], 
                    c='red', s=barycenter_size, marker='x', zorder=5, 
                    label='Barycenters')
        
    else:
        barycenters_dict = None

    

    # ------------------------------------------------------------
    # FILTER ELEMENTS IF REQUESTED
    # ------------------------------------------------------------
    if elements_to_plot is not None:
        elements_to_plot = set(elements_to_plot)

        # Filter elements
        keep = [eid in elements_to_plot for eid in element_ids]
        elements_list = [e for e, k in zip(elements_list, keep) if k]
        element_ids = [eid for eid in element_ids if eid in elements_to_plot]

        if barycenters_dict is not None:
            barycenters_dict = {eid: barycenters_dict[eid]
                                for eid in element_ids if eid in barycenters_dict}

        # Filter adjacency (handle both dict and list formats)
        if adjacency is not None:
            if isinstance(adjacency, dict):
                adjacency = {k: v for k, v in adjacency.items()
                             if int(k) in elements_to_plot}
            else:
                adjacency = [(i, j) for (i, j) in adjacency
                             if i in elements_to_plot and j in elements_to_plot]

        if normals is not None:
            normals = {k: v for k, v in normals.items()
                       if int(k) in elements_to_plot}

    # ------------------------------------------------------------
    # SPLIT COORDS & PLOT NODES
    # ------------------------------------------------------------
    X = nodes[:, 0]
    Y = nodes[:, 1]
    valid_mask = ~np.isnan(X)
    ax.scatter(X[valid_mask], Y[valid_mask], s=node_size, color="red")

    # ------------------------------------------------------------
    # TRIANGULATION & MESH PLOT
    # ------------------------------------------------------------
    if elements_list is not None:
        if boundary_only:
            # Draw only edges that belong to exactly one element
            from matplotlib.collections import LineCollection
            edge_count = {}
            for elem in elements_list:
                n = len(elem)
                for k in range(n):
                    e = tuple(sorted((elem[k], elem[(k + 1) % n])))
                    edge_count[e] = edge_count.get(e, 0) + 1
            boundary_segs = []
            for (n1, n2), cnt in edge_count.items():
                if cnt == 1:
                    p1, p2 = nodes[n1], nodes[n2]
                    if not (np.isnan(p1).any() or np.isnan(p2).any()):
                        boundary_segs.append([p1, p2])
            if boundary_segs:
                lc = LineCollection(boundary_segs, colors=boundary_color,
                                    linewidths=boundary_lw)
                ax.add_collection(lc)
        else:
            # Group elements by vertex count to handle mixed tri/quad meshes
            from collections import defaultdict
            from matplotlib.collections import PolyCollection
            groups = defaultdict(list)
            for elem in elements_list:
                groups[len(elem)].append(elem)

            for n_verts, group_elems in groups.items():
                group_array = np.array(group_elems)
                if n_verts == 3:
                    # Triangles — use triplot
                    triang = tri.Triangulation(X, Y, triangles=group_array)
                    ax.triplot(triang, lw=0.2, color="black")
                else:
                    # Quads (or general polygons) — draw as PolyCollection
                    verts = nodes[group_array]  # shape (n_elems, n_nodes, 2)
                    # Filter out elements with any NaN vertex
                    valid = ~np.isnan(verts).any(axis=(1, 2))
                    poly = PolyCollection(verts[valid], edgecolors="black",
                                          facecolors="none", linewidths=0.2)
                    ax.add_collection(poly)

    # ------------------------------------------------------------
    # ELEMENT NUMBERS
    # ------------------------------------------------------------
    if show_element_numbers and elements_list is not None:
        if barycenters_dict is not None:
            for eid in element_ids:
                if eid not in barycenters_dict:
                    continue
                cx, cy = barycenters_dict[eid][:2]
                if np.isnan(cx) or np.isnan(cy):
                    continue
                ax.text(cx, cy, str(eid), fontsize=6,
                         ha='center', va='center', color='blue')
        else:
            # Compute barycenters on the fly from list-of-lists
            for i, elem in enumerate(elements_list):
                elem_coords = nodes[elem]
                cx, cy = np.mean(elem_coords, axis=0)[:2]
                if np.isnan(cx) or np.isnan(cy):
                    continue
                ax.text(cx, cy, str(element_ids[i]), fontsize=6,
                         ha='center', va='center', color='blue')

    # ------------------------------------------------------------
    # ADJACENCY PLOT
    # ------------------------------------------------------------
    if isinstance(adjacency, dict):

        # Dictionary adjacency (keys are strings, values are [e1, e2])
        for key, elements in adjacency.items():
            if len(elements) < 2:
                continue
            e1, e2 = elements[0], elements[1]
            if e1 not in barycenters_dict or e2 not in barycenters_dict:
                continue
            x1, y1 = barycenters_dict[e1][:2]
            x2, y2 = barycenters_dict[e2][:2]
            if np.isnan(x1) or np.isnan(y1) or np.isnan(x2) or np.isnan(y2):
                continue
            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=0.4)
   
    else:
        # List adjacency (1-based)
        if adjacency is not None:
            for t1, t2 in adjacency:
                if t1 not in barycenters_dict or t2 not in barycenters_dict:
                    continue
                x1, y1 = barycenters_dict[t1][:2]
                x2, y2 = barycenters_dict[t2][:2]
                if np.isnan(x1) or np.isnan(y1) or np.isnan(x2) or np.isnan(y2):
                    continue
                ax.plot([x1, x2], [y1, y2], 'b-', linewidth=0.4)

    # ------------------------------------------------------------
    # NORMAL VECTORS
    # ------------------------------------------------------------
    if normals is not None and barycenters_dict is not None:
        for elem_id_str, vec in normals.items():
            eid = int(elem_id_str)
            if eid not in barycenters_dict:
                continue

            px, py = barycenters_dict[eid][:2]
            if np.isnan(px) or np.isnan(py):
                continue

            vx, vy = vec[:2]
            ax.arrow(px, py, normal_scale * vx, normal_scale * vy,
                      head_width=0.02, head_length=0.03,
                      fc='green', ec='green')

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Triangular Mesh")
    ax.set_aspect("equal", "box")
    fig.tight_layout()
    # plt.show()
    return ax








def read_surfaces_from_inp(filename):
    """
    Reads:
        - Nodes
        - Elements (the first one is element = 1)
        - Individual surfaces (type=element)
        - External union surfaces (combine=union)
    
    Returns:
        nodes: np.ndarray (N, 2 or 3)
        elements: list[tuple]
        individual_surfaces: dict[surf_name → list of (element_id, face)]
        external_surfaces: dict[ext_name → list of surface_names]
    """

    individual_surfaces = {}
    external_surfaces = {}
    individual_ele_sets = {}

    nodes = []
    elements = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # ------------------------------------------
        # READ NODES
        # ------------------------------------------
        if line.startswith("*Node"):
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                data = lines[i].strip()
                if data:
                    parts = data.split(",")
                    # Node number = parts[0], we ignore it
                    coords = [float(x) for x in parts[1:]]
                    nodes.append(coords)
                i += 1
            continue

        # ------------------------------------------
        # READ ELEMENTS
        # ------------------------------------------
        if line.startswith("*Element"):
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                data = lines[i].strip()
                if data:
                    parts = data.split(",")
                    # parts[0] = element id
                    conn = tuple(int(x) for x in parts[1:])
                    elements.append(conn)
                i += 1
            continue

        # ------------------------------------------
        # ELEMENT SETS
        # ------------------------------------------
        if line.startswith("*Elset") and "elset=Set-E-Seed" in line:
            m = re.search(r"elset=([^\s,]+)", line)
            if not m:
                i += 1
                continue

            elset_name = m.group(1).strip()
            individual_ele_sets[elset_name] = []

            i += 1  # move to the first data line
            while i < len(lines):
                data = lines[i].strip()

                # stop when reaching the next keyword
                if data.startswith("*"):
                    break

                if data:
                    # split by comma, clean, convert to int
                    ids = [int(x.strip()) for x in data.split(",") if x.strip()]
                    individual_ele_sets[elset_name].extend(ids)

                i += 1

            # don't increment i here, we want the outer loop
            # to see the line starting with "*"
            continue


        # ------------------------------------------
        # INDIVIDUAL SURFACES
        # ------------------------------------------
        if line.startswith("*Surface") and "type=element" in line:
            m = re.search(r"name=([^,]+)", line)
            if not m:
                i += 1
                continue

            surf_name = m.group(1).strip()
            individual_surfaces[surf_name] = []

            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                data = lines[i].strip()
                if data:
                    elem_id, face = data.split(",")
                    individual_surfaces[surf_name].append(
                        (int(elem_id.strip()), face.strip())
                    )
                i += 1
            continue

        # ------------------------------------------
        # EXTERNAL SURFACES (combine=union)
        # ------------------------------------------
        if line.startswith("*Surface") and "combine=union" in line:
            m = re.search(r"name=([^,]+)", line)
            if not m:
                i += 1
                continue

            ext_name = m.group(1).strip()
            external_surfaces[ext_name] = []

            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                data = lines[i].strip()
                if data:
                    external_surfaces[ext_name].append(data)
                i += 1
            continue

        i += 1

    # ---------------------------------------------------------
    # FILTER EXTERNAL SURFACES (ONLY KEEP EXISTING SURFACES)
    # ---------------------------------------------------------
    indiv_keys = set(individual_surfaces.keys())

    for ext_name, surf_list in external_surfaces.items():
        cleaned_list = [s for s in surf_list if s in indiv_keys]
        external_surfaces[ext_name] = cleaned_list

    # ---------------------------------------------------------
    # Convert nodes to numpy array
    # ---------------------------------------------------------
    nodes = np.array(nodes)

    return nodes, elements, individual_surfaces, individual_ele_sets, external_surfaces




def write_nodes_elements(nodes, elements, file):

    IDS = []

    for node in nodes:
        ID = '9'
        for coord in range(len(node)):
            if abs(node[coord] - (-0.5)) < 1e-8:
                ID += '1'
            elif abs(node[coord] - (0.5)) < 1e-8:
                ID += '2'
            else:
                ID += '0'

        IDS.append(ID)


    with open(file, 'w') as f:
        f.write(f"{len(nodes)} {len(nodes[0])}\n")
        for i, node in enumerate(nodes):
            f.write(" ".join(str(x) for x in node) + " " + IDS[i] + "\n")

        f.write(f"{len(elements)} {len(elements[0])}\n")
        for element in elements:
            f.write(" ".join([str(n) for n in element]) + "\n")




def read_mesh_file(filename):
    # Read data from the file
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_nodes, dim_nodes = lines[0].split()
    num_nodes = int(num_nodes)
    dim_nodes = int(dim_nodes)

    nodes = []
    for line in lines[1:num_nodes+1]:
        coords = [float(line.split()[i]) for i in range(dim_nodes)]
        id = line.split()[dim_nodes] if len(line.split()) > dim_nodes else None
        node = [*coords, id]
        nodes.append(node)

    # Parse element data
    element_start_index = num_nodes + 1
    num_elements, dim_elements = lines[element_start_index].split()
    num_elements = int(num_elements)
    dim_elements = int(dim_elements)

    elements = []
    for line in lines[element_start_index + 1: element_start_index + num_elements + 1]:
        element_data = [int(line.split()[i]) for i in range(dim_elements )]
        elements.append(element_data)

    return nodes, elements, dim_nodes, dim_elements


def read_nodes_elements(file):
    with open(file, 'r') as f:
        lines = f.readlines()

    header_nodes = lines[0].strip().split()
    num_nodes = int(header_nodes[0])
    dim = int(header_nodes[1])

    nodes = []
    for i in range(1, num_nodes + 1):
        parts = lines[i].strip().split()
        coord = [float(x) for x in parts[:dim]]
        nodes.append(coord)

    header_elements = lines[num_nodes + 1].strip().split()
    num_elements = int(header_elements[0])
    element_size = int(header_elements[1])

    elements = []
    for i in range(num_nodes + 2, num_nodes + 2 + num_elements):
        parts = lines[i].strip().split()
        element = [int(x) - 1 for x in parts]
        elements.append(element)

    return np.array(nodes), np.array(elements)




def pick_edge(void_tess):
    f_neighs = void_tess.facet_neighbors
    i = -1
    neighs = [-1, -1]
    while any([n < 0 for n in neighs]):
        i = np.random.randint(len(f_neighs))
        neighs = f_neighs[i]
    facet = void_tess.facets[i]
    j = np.random.randint(len(facet))
    kp1 = facet[j]
    kp2 = facet[j - 1]
    return kp1, kp2


def trial_position(void_tess):
    kp1, kp2 = pick_edge(void_tess)
    pt1 = void_tess.points[kp1]
    pt2 = void_tess.points[kp2]

    f = np.random.rand()
    return [f * x1 + (1 - f) * x2 for x1, x2 in zip(pt1, pt2)]


def check_pt(point, r, breakdowns):
    pts = breakdowns[:, :-1]
    rads = breakdowns[:, -1]

    rel_pos = pts - point
    dist = np.sqrt(np.sum(rel_pos * rel_pos, axis=1))
    min_dist = rads + r - 0.3 * np.minimum(rads, r)
    return np.all(dist > min_dist)


