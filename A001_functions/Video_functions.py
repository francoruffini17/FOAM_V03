#!/usr/bin/env python
# coding: utf-8
import os
import json
import pickle
import numpy as np
import matplotlib.pyplot as plt
import glob
import cv2
import subprocess
import tempfile
import shutil
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass, field
from typing import Any, List
import matplotlib.tri as tri
import copy
# from A001_functions.Hex_pack_funct import from_name, from_r_to_p
from typing import Callable, Optional
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import importlib
import A001_functions.mesh_functions as _mf
importlib.reload(_mf)
from A001_functions.mesh_functions import plot_foam_mesh
from A001_functions.mesh_functions import plot_J1_graph_mesh
from A001_functions.mesh_functions import plot_T1_triangulation_mesh
from A001_functions.fem_stress_interpolation import interpolate_stress

### ----------------------------- plot frame graph parameter -----------------------------##

@dataclass
class graph_property:
    ppty: str = None  # Property to plot (e.g., 'Density', 'Subgraphs_number', 'Subgraphs_number_no_indiv')
    t_x: int = None  # Index for special marker on plot
    legends: bool = False  # Whether to show legend
    xlabel: str = None  # X-axis label
    ylabel: str = None  # Y-axis label
    title: str = None  # Plot title
    save_path: str = None  # Path to save the figure
    dotted: bool = True  # Whether to use dotted lines for certain plot elements
    normalize: bool = True  # Whether to normalize values
    grid: bool = True  # Whether to show grid
    xlim: tuple = None  # X-axis limits
    ylim: tuple = None  # Y-axis limits
    tension_compression: str = 'both'  # Which curves to plot: 'tension', 'compression', or 'both'
    crit: str = 'crit_3'  # Criterion used (not used directly in plotting)
    dpi: int = 50  # DPI for saving figure
    show_fig: bool = False  # Whether to display the figure
    legend_loc: str = None  # Legend location
    figsize: list[float] = None  # Figure size
    file_ext: str = 'G2'  # File name (not used directly in plotting)
    xscale: str = 'linear'  # X-axis scale
    yscale: str = 'linear'  # Y-axis scale


def create_graph_property_frame(pkl_G2,T):
    
    if T.figsize is not None:
        plt.figure(figsize=T.figsize)
    else:
        plt.figure(figsize=(5,4))
    
    if T.tension_compression in ['both', 'tension']:
        if T.ppty == 'Density':
            sg_t = pkl_G2['density_t']
            if T.normalize is True:
                sg_t = np.array(sg_t)/np.array(pkl_G2['density_ref'])

        elif T.ppty == 'Subgraphs_number':
            sg_t = pkl_G2['num_sub_t']

        elif T.ppty == 'Subgraphs_number_no_indiv':
            sg_t = pkl_G2['num_sub_no_indv_t']

        elif T.ppty == 'G_eff':
            sg_t = pkl_G2['global_ef_t']

        if T.dotted == True:
            x = np.array(pkl_G2['t'][1:])
            y = np.array(sg_t[1:])
            
            # Create solid and dotted arrays filled with NaNs
            y_solid = np.full_like(y, np.nan, dtype=float)
            y_dotted = np.full_like(y, np.nan, dtype=float)

            # Populate them based on condition
            for i in range(len(y)):
                if y[i] == 1:
                    y_dotted[i] = y[i]
                else:
                    y_solid[i] = y[i]

            plt.plot(x,y_solid,'-r',label = 'Tension graph')
            plt.plot(x,y_dotted,':r',label ='Unit Tension graph')
        else:
            plt.plot(pkl_G2['t'][1:],sg_t[1:],'r',label = 'Tension graph')

        if T.t_x is not None:
            if T.t_x >0:
                plt.plot(pkl_G2['t'][T.t_x],sg_t[T.t_x],'kx')

        


    if T.tension_compression in ['both', 'compression']:

        if T.ppty == 'Density':
            sg_c = pkl_G2['density_c']
            if T.normalize is True:
                sg_c = np.array(sg_c)/np.array(pkl_G2['density_ref'])

        elif T.ppty == 'Subgraphs_number':
            sg_c = pkl_G2['num_sub_c']
        

        elif T.ppty == 'Subgraphs_number_no_indiv':
            sg_c = pkl_G2['num_sub_no_indv_c']

        elif T.ppty == 'G_eff':
            sg_c = pkl_G2['global_ef_c']

        plt.plot(pkl_G2['t'][1:],sg_c[1:],'b',label = 'Compression graph')

        
        if T.t_x is not None:
            if T.t_x > 0:
                plt.plot(pkl_G2['t'][T.t_x],sg_c[T.t_x],'kx')


    if T.tension_compression in ['comb']:

        if T.ppty == 'f':
            sg_c = np.array(pkl_G2['global_ef_c'])
            sg_t = np.array(pkl_G2['global_ef_t'])

        plt.plot(pkl_G2['t'][1:],sg_t[1:]/sg_c[1:],'g',label = 'Tension/Compression graph')

        if T.t_x is not None:
            if T.t_x > 0:
                plt.plot(pkl_G2['t'][T.t_x],sg_t[T.t_x]/sg_c[T.t_x],'kx')



    if T.grid is True:
        plt.grid()

    if T.title is not None:
        plt.title(T.title)

    if T.legends is True:
        plt.legend(loc=T.legend_loc)

    if T.xlabel is not None:
        plt.xlabel(T.xlabel)
        
    if T.ylabel is not None:
        plt.ylabel(T.ylabel)

    if T.xlim is not None:
        plt.xlim(T.xlim)

    if T.ylim is not None:
        plt.ylim(T.ylim)


    plt.xscale(T.xscale)
    plt.yscale(T.yscale)
    
    if T.save_path is not None:
        plt.savefig(T.save_path, dpi=T.dpi, bbox_inches = 'tight')
        print(f"Frame saved to {T.save_path}")
        
    if T.show_fig is True:
        plt.show()

    plt.close()



def create_graph_property_multiple_frames(sim_num, T, save_path=None, frames_format='png'):
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_{T.file_ext}.pkl', "rb") as f:
        Gs = pickle.load(f)

    os.makedirs(save_path, exist_ok=True)

    total_frames = len(Gs['t'])
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    for i in indices:
        save_path_ = os.path.join(save_path, f'frame_{i:08d}.{frames_format}')
        T_c = copy.deepcopy(T)
        T_c.save_path = save_path_
        T_c.t_x = i

        try:
            create_graph_property_frame(Gs, T_c)
        except Exception as e:
            print(f"Error in frame {i}: {e}")















### ---- PLOT ANIMATION  ---- ###
@dataclass
class frame_animation:
    dpi: int = 50
    title: str = None
    xlabel: str = None
    ylabel: str = None
    xlim: float = None
    ylim: float = None
    number_size: int = 10
    save_path = None
    background = False
    save_path: str = None
    figsize: list[float] = None
    num_frames: int = None
    plot_adjacency: bool = False
    plot_normals: bool = False
    node_size: float = 0.2
    mesh_line_size: float = 0.2
    show_element_numbers: bool = False
    elements_to_plot: list[int] = None
    normal_scale: float = 0.2
    color_element: str = None
    condition: Optional[Callable[[np.ndarray], bool]] = None


def evaluate_color_expression(expression, S11_val, S22_val, S12_val):
    """
    Evaluates a mathematical expression for coloring elements.
    
    Args:
        expression: String containing the mathematical expression
        S11_val, S22_val, S12_val: Values for the stress components
    
    Returns:
        The evaluated result
    """
    # Create a safe namespace with the stress values
    namespace = {
        'S11': S11_val,
        'S22': S22_val,
        'S12': S12_val,
        'S21': S12_val,  # S21 == S12 (symmetric stress tensor)
        'S1': S11_val,   # Alias for principal stress notation
        'S2': S22_val,
        'np': np,
        '__builtins__': {}
    }
    
    try:
        result = eval(expression, namespace)
        return result
    except Exception as e:
        print(f"Error evaluating expression '{expression}': {e}")
        return 0.0


def create_animation_frame(
        nodes, elements, barycenters=None, adjacency=None, normals=None,
        T=None, data_B=None, ti=None, data_C2=None):
    """
    Creates a 2D plot of the mesh with triangular and/or quad elements,
    optionally plotting barycenters, adjacency edges, and normal vectors.
    Can color elements based on stress values interpolated to the element
    barycenter using FEM shape functions.
    
    Args:
        nodes: Array of node coordinates
        elements: List of element connectivity (can be mixed 3-node triangles and 4-node quads)
        barycenters: Array of element barycenters
        adjacency: List of adjacent element pairs
        normals: Dictionary of normal vectors per element
        T: frame_animation settings object
        data_B: Dictionary containing stress data (S11, S22, S12/S21) if color_element is used
        ti: Time index for the current frame (0-based)
        data_C2: Dictionary with mesh/geometry data needed for stress interpolation
    """

    # -------------------------------
    # Extract settings from T
    # -------------------------------
    dpi = T.dpi
    save_path = T.save_path
    background = T.background
    xlabel = T.xlabel
    ylabel = T.ylabel
    title = T.title
    xlim = T.xlim
    ylim = T.ylim

    # -------------------------------
    # PRE-PROCESSING
    # -------------------------------
    nodes = np.array(nodes)
    
    # Handle elements - convert to list of arrays (can have different lengths)
    if isinstance(elements, np.ndarray) and elements.ndim == 2:
        # All elements have same number of nodes
        elements = [elem - 1 for elem in elements]  # to 0-based
    else:
        # Mixed element types or already a list
        elements = [np.array(elem) - 1 for elem in elements]  # to 0-based

    # Separate triangles and quads
    triangles = []
    quads = []
    tri_indices = []
    quad_indices = []
    
    for i, elem in enumerate(elements):
        if len(elem) == 3:
            triangles.append(elem)
            tri_indices.append(i)
        elif len(elem) == 4:
            quads.append(elem)
            quad_indices.append(i)
        else:
            print(f"Warning: Element {i+1} has {len(elem)} nodes, skipping.")

    # -------------------------------
    # APPLY CONDITION FILTER (if provided)
    # -------------------------------
    condition_filtered_element_ids = None
    if T.condition is not None:
        # Step 1: Identify nodes that satisfy the condition
        node_mask = np.array([T.condition(node) for node in nodes])
        valid_node_indices = np.where(node_mask)[0]
        valid_node_set = set(valid_node_indices)
        
        # Step 2: Identify elements where ALL nodes satisfy the condition
        element_mask = np.array([
            all(node_idx in valid_node_set for node_idx in elem)
            for elem in elements
        ])
        
        # Get the 1-based element IDs that passed the condition
        valid_element_indices = np.where(element_mask)[0]
        condition_filtered_element_ids = list(valid_element_indices + 1)  # Convert to 1-based
        
        print(f"Condition filter: {len(condition_filtered_element_ids)} elements satisfy the condition")

    # -------------------------------
    # COMBINE FILTERS
    # -------------------------------
    if condition_filtered_element_ids is not None and T.elements_to_plot is not None:
        final_elements_to_plot = sorted(set(condition_filtered_element_ids) & set(T.elements_to_plot))
    elif condition_filtered_element_ids is not None:
        final_elements_to_plot = sorted(condition_filtered_element_ids)
    elif T.elements_to_plot is not None:
        final_elements_to_plot = sorted(T.elements_to_plot)
    else:
        final_elements_to_plot = None

    # Store original element IDs (1-based) for color mapping
    if final_elements_to_plot is not None:
        original_element_ids = final_elements_to_plot
    else:
        original_element_ids = list(range(1, len(elements) + 1))

    # -------------------------------
    # FILTER ELEMENTS
    # -------------------------------
    if final_elements_to_plot is not None:
        elements_to_plot_set = set(final_elements_to_plot)
        
        # Filter elements
        filtered_elements = []
        filtered_indices = []
        for i, elem in enumerate(elements):
            if (i + 1) in elements_to_plot_set:
                filtered_elements.append(elem)
                filtered_indices.append(i)
        elements = filtered_elements
        
        # Re-separate triangles and quads after filtering
        triangles = []
        quads = []
        tri_original_ids = []
        quad_original_ids = []
        
        for idx, elem in zip(filtered_indices, elements):
            if len(elem) == 3:
                triangles.append(elem)
                tri_original_ids.append(idx + 1)  # 1-based
            elif len(elem) == 4:
                quads.append(elem)
                quad_original_ids.append(idx + 1)  # 1-based

        if barycenters is not None:
            barycenters = np.array(barycenters)
            mask = np.array([(i+1) in elements_to_plot_set for i in range(len(barycenters))])
            barycenters = barycenters[mask]

        if normals is not None and T.plot_normals is True:
            normals = {k: v for k, v in normals.items() if int(k) in elements_to_plot_set}

        if adjacency is not None and T.plot_adjacency is True:
            adjacency = [(i, j) for (i, j) in adjacency
                         if i in elements_to_plot_set and j in elements_to_plot_set]
    else:
        tri_original_ids = [i + 1 for i in tri_indices]
        quad_original_ids = [i + 1 for i in quad_indices]

    X = nodes[:, 0]
    Y = nodes[:, 1]

    # -------------------------------
    # CALCULATE COLOR VALUES
    # -------------------------------
    color_values_dict = {}
    if T.color_element is not None and data_B is not None and ti is not None:
        ti_key = str(ti + 1)  # interpolate_stress uses 1-based string keys

        for elem_id in original_element_ids:
            elem_str = str(elem_id)

            try:
                if data_C2 is not None:
                    # Use FEM interpolation to compute stress at element barycenter
                    bary_at_t = data_C2['baricenters'][ti_key]
                    bary_x = float(bary_at_t[elem_id - 1][0])
                    bary_y = float(bary_at_t[elem_id - 1][1])

                    result = interpolate_stress(
                        data_C2, data_B,
                        bary_x, bary_y,
                        ti_key,
                        element_idx=elem_str,
                    )
                    S11_val = result['S11']
                    S22_val = result['S22']
                    S12_val = result['S21']  # S12 == S21 (symmetric tensor)
                else:
                    # Fallback when data_C2 is not available:
                    # use first unique integration point (not interpolated)
                    S11_val = float(data_B['S11'][elem_str][0][ti]) if 'S11' in data_B else 0.0
                    S22_val = float(data_B['S22'][elem_str][0][ti]) if 'S22' in data_B else 0.0
                    s12_key = 'S12' if 'S12' in data_B else 'S21'
                    S12_val = float(data_B[s12_key][elem_str][0][ti]) if s12_key in data_B else 0.0

                color_val = evaluate_color_expression(T.color_element, S11_val, S22_val, S12_val)
                color_values_dict[elem_id] = float(color_val)

            except (KeyError, IndexError) as e:
                print(f"Warning: Could not get stress data for element {elem_id} at time {ti}: {e}")
                color_values_dict[elem_id] = 0.0

    # -------------------------------
    # CREATE FIGURE
    # -------------------------------
    fig, ax = plt.subplots(figsize=T.figsize, dpi=dpi)

    # -------------------------------
    # PLOT MESH WITH COLORS
    # -------------------------------
    all_color_values = list(color_values_dict.values()) if color_values_dict else []
    if all_color_values:
        vmin, vmax = min(all_color_values), max(all_color_values)
    else:
        vmin, vmax = 0, 1

    # Plot triangles
    if triangles:
        triangles_array = np.array(triangles)
        triang = tri.Triangulation(X, Y, triangles=triangles_array)
        
        if color_values_dict:
            tri_colors = np.array([color_values_dict.get(eid, 0.0) for eid in tri_original_ids])
            tcf = ax.tripcolor(triang, facecolors=tri_colors, 
                               cmap='viridis', edgecolors='black', 
                               linewidth=T.mesh_line_size, vmin=vmin, vmax=vmax)
        else:
            ax.triplot(triang, lw=T.mesh_line_size, color="black")

    # Plot quads
    if quads:
        quad_patches = []
        quad_colors = []
        
        for i, quad in enumerate(quads):
            quad_nodes = nodes[quad]
            polygon = Polygon(quad_nodes[:, :2], closed=True)
            quad_patches.append(polygon)
            
            if color_values_dict:
                quad_colors.append(color_values_dict.get(quad_original_ids[i], 0.0))
        
        if quad_patches:
            pc = PatchCollection(quad_patches, cmap='viridis', edgecolors='black', 
                                 linewidths=T.mesh_line_size)
            if color_values_dict:
                pc.set_array(np.array(quad_colors))
                pc.set_clim(vmin, vmax)
            else:
                pc.set_facecolor('none')
            ax.add_collection(pc)

    # Add colorbar if colors are used
    if color_values_dict:
        if triangles:
            cbar = fig.colorbar(tcf, ax=ax, shrink=0.5, aspect=10)
        elif quads:
            cbar = fig.colorbar(pc, ax=ax, shrink=0.5, aspect=10)
        cbar.set_label(T.color_element, rotation=270, labelpad=20)

    # Nodes
    ax.scatter(X, Y, s=T.node_size, color="red")

    # -------------------------------
    # ELEMENT NUMBERS
    # -------------------------------
    if T.show_element_numbers:
        if barycenters is None:
            # Calculate barycenters for all elements
            bary = []
            for elem in elements:
                elem_nodes = nodes[elem]
                bary.append(np.mean(elem_nodes, axis=0))
            bary = np.array(bary)
        else:
            bary = np.array(barycenters)

        elem_ids = original_element_ids

        for (cx, cy), eid in zip(bary[:, :2], elem_ids):
            ax.text(cx, cy, str(eid),
                    fontsize=6, ha='center', va='center', color='blue')

    # -------------------------------
    # ADJACENCY
    # -------------------------------
    if adjacency is not None and barycenters is not None and T.plot_adjacency is True:
        barycenters = np.array(barycenters)
        for t1, t2 in adjacency:
            x1, y1 = barycenters[t1-1][:2]
            x2, y2 = barycenters[t2-1][:2]
            ax.plot([x1, x2], [y1, y2], 'k-', lw=0.4)

    # -------------------------------
    # NORMAL VECTORS
    # -------------------------------
    if normals is not None and barycenters is not None and T.plot_normals is True:
        barycenters = np.array(barycenters)
        for elem_id_str, vec in normals.items():
            idx = int(elem_id_str) - 1
            px, py = barycenters[idx][:2]
            vx, vy = vec[:2]

            ax.arrow(px, py,
                     T.normal_scale * vx,
                     T.normal_scale * vy,
                     head_width=0.02,
                     head_length=0.03,
                     fc='green', ec='green')

    # -------------------------------
    # AXIS + STYLE
    # -------------------------------
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    if title: ax.set_title(title)

    ax.set_aspect("equal", "box")

    if xlim: ax.set_xlim(xlim)
    if ylim: ax.set_ylim(ylim)

    if not background:
        ax.set_axis_off()
        ax.grid(False)

    fig.tight_layout()

    # -------------------------------
    # SAVE OR SHOW
    # -------------------------------
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight', transparent=True)
        plt.close(fig)
        print(f"Frame saved to {save_path}")
    else:
        plt.show()

    return (ax.get_xlim(), ax.get_ylim())


def create_animation_multiple_frames(sim_num, T, save_path=None, frames_format='png'):
    """
    Creates multiple animation frames from simulation data.
    Supports both triangular and quad elements.
    """
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_C2.pkl', "rb") as f:
        data_C2 = pickle.load(f)
    
    data_B = None
    if T.color_element is not None:
        try:
            with open(f'I001_Results/DATA_PICK_{sim_num:03d}_B.pkl', 'rb') as f:
                data_B = pickle.load(f)
            print(f"Loaded stress data for coloring with expression: {T.color_element}")
        except FileNotFoundError:
            print(f"Warning: Could not find DATA_PICK_{sim_num:03d}_B.pkl for color mapping")
            print("Continuing without element coloring...")
    
    os.makedirs(save_path, exist_ok=True)
    
    total_frames = len(data_C2['t'])
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    for ti in indices:
        ti_key = str(ti + 1)
        T.save_path = save_path + f'frame_{ti:08d}.{frames_format}'
        T.t_x = ti

        # adjacency is time-independent; convert dict values to list of pairs
        adj_pairs = list(data_C2['adjacency'].values()) if 'adjacency' in data_C2 else None

        # nodes_time[ti] is a dict {str(node_id): coords}; convert to sorted list
        nt = data_C2['nodes_time'][ti]
        nodes_list = [nt[k] for k in sorted(nt.keys(), key=int)]

        create_animation_frame(
            nodes_list, 
            list(data_C2['elements'].values()), 
            barycenters=data_C2['baricenters'][ti_key], 
            adjacency=adj_pairs, 
            normals=data_C2['normals'][ti],
            T=T,
            data_B=data_B,
            ti=ti,
            data_C2=data_C2,
        )








### ---- PLOT ANIMATION GRAPH  ---- ###

@dataclass
class PlotJ1GraphParams:
    show_node_labels: bool = False
    bar_color: str = 'b'
    node_color: str = 'red'
    node_size: int = 0
    linewidth: float = 1
    figsize: Any = (10, 8)
    title: Any | None = None
    show_undeformed: bool = False
    undeformed_color: str = '0.75'
    magnification: float = 1
    color_by: Any | None = 'axial'
    cmap: str = 'coolwarm'
    vmin: Any | None = None
    vmax: Any | None = None
    show_normals: bool = False
    normal_scale: float = 0.03
    normal_color: str = 'green'
    node_scale: float = 1.0
    plot_ten_comp: str = 'both'
    plot_ten_comp_color_bar: bool = True

@dataclass
class PlotMeshGraphParams:
    elements_to_plot: Any | None = None
    show_element_numbers: bool = False
    node_size: float = 0
    plot_barycenters: bool = True
    barycenter_size: int = 50
    boundary_only: bool = True
    boundary_lw: float = 0.5
    boundary_color: str = 'black'


@dataclass
class frame_animation_graph:
    dpi: int = 50
    title: str = ''
    xlabel: str = None
    ylabel: str = None
    xlim: float = None
    ylim: float = None
    number_size: int = 10
    save_path: str = None
    background: bool = False
    save_path: str = None
    figsize: list[float] = None
    num_frames: int = None
    plot_adjacency: bool = False
    plot_normals: bool = False
    node_size: float = 0.2
    mesh_line_size: float = 0.2
    show_element_numbers: bool = False
    elements_to_plot: list[int] = None
    normal_scale: float = 0.2
    color_element: str = None
    condition: Optional[Callable[[np.ndarray], bool]] = None
    plot_J1_params: PlotJ1GraphParams = field(default_factory=PlotJ1GraphParams)
    plot_Mesh_Graph_params: PlotMeshGraphParams = field(default_factory=PlotMeshGraphParams)
    J1_ext: float = '000'
    key_letter: str = 'J'
    plot_ten_comp: str = 'both'
    plot_ten_comp_color_bar: bool = True



def create_animation_graph_frame(c2, j1, T=None,  ti=None):

    # Backward compatibility: if the top-level frame object defines these
    # values, they override nested defaults in plot_J1_params.
    if hasattr(T, 'plot_ten_comp') and T.plot_ten_comp is not None:
        plot_ten_comp = T.plot_ten_comp
    else:
        plot_ten_comp = getattr(T.plot_J1_params, 'plot_ten_comp', 'both')

    if hasattr(T, 'plot_ten_comp_color_bar') and T.plot_ten_comp_color_bar is not None:
        plot_ten_comp_color_bar = T.plot_ten_comp_color_bar
    else:
        plot_ten_comp_color_bar = getattr(T.plot_J1_params, 'plot_ten_comp_color_bar', True)

    if plot_ten_comp not in ('both', 't', 'c'):
        raise ValueError("plot_ten_comp must be one of: 'both', 't', 'c'")
    
    ax = plot_J1_graph_mesh(j1, ti=ti, show_node_labels=T.plot_J1_params.show_node_labels,
    bar_color=T.plot_J1_params.bar_color,
    node_color=T.plot_J1_params.node_color,
    node_size=T.plot_J1_params.node_size,
    linewidth=T.plot_J1_params.linewidth,
    figsize=T.plot_J1_params.figsize,
    title= T.plot_J1_params.title,
    show_undeformed=T.plot_J1_params.show_undeformed,
    undeformed_color=T.plot_J1_params.undeformed_color,
    magnification=T.plot_J1_params.magnification,
    color_by=T.plot_J1_params.color_by,
    cmap=T.plot_J1_params.cmap,
    vmin=T.plot_J1_params.vmin,
    vmax=T.plot_J1_params.vmax,
    show_normals=T.plot_J1_params.show_normals,
    normal_scale=T.plot_J1_params.normal_scale,
    normal_color=T.plot_J1_params.normal_color,
    node_scale=T.plot_J1_params.node_scale,
    plot_ten_comp=plot_ten_comp,
    plot_ten_comp_color_bar=plot_ten_comp_color_bar)

    plot_foam_mesh(c2['nodes_time'][ti], elements=c2['elements'], ax=ax,   
    elements_to_plot = T.plot_Mesh_Graph_params.elements_to_plot,
    show_element_numbers = T.plot_Mesh_Graph_params.show_element_numbers,
    node_size = T.plot_Mesh_Graph_params.node_size,
    plot_barycenters = T.plot_Mesh_Graph_params.plot_barycenters,
    barycenter_size = T.plot_Mesh_Graph_params.barycenter_size,
    boundary_only = T.plot_Mesh_Graph_params.boundary_only,
    boundary_lw = T.plot_Mesh_Graph_params.boundary_lw,
    boundary_color = T.plot_Mesh_Graph_params.boundary_color)


    if T.xlim is not None:
        ax.set_xlim(T.xlim)
    if T.ylim is not None:
        ax.set_ylim(T.ylim)
    if T.xlabel is not None:
        ax.set_xlabel(T.xlabel)
    if T.ylabel is not None:
        ax.set_ylabel(T.ylabel)
    if T.title is not None:
        ax.set_title(T.title)
    if T.background == False:
        ax.set_axis_off()
        ax.grid(False)

    # -------------------------------
    # SAVE OR SHOW
    # -------------------------------
    fig = ax.get_figure()
    if T.save_path:
        fig.savefig(T.save_path, dpi=T.dpi, bbox_inches='tight', transparent=True)
        plt.close(fig)
        print(f"Frame saved to {T.save_path}")
    else:
        plt.show()


def create_animation_graph_multiple_frames(sim_num, T, save_path=None, frames_format='png'):
    """
    Creates multiple animation frames from simulation data.
    Supports both triangular and quad elements.
    """
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_C2.pkl', "rb") as f:
        data_C2 = pickle.load(f)
    
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_{T.key_letter}1_{T.J1_ext}.pkl', "rb") as f:
        data_J1 = pickle.load(f)

    os.makedirs(save_path, exist_ok=True)

    total_frames = len(data_C2['t'])
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    for ti in indices:
        T.save_path = save_path + f'frame_{ti:08d}.{frames_format}'
        T.t_x = ti
        
        create_animation_graph_frame(
            data_C2, 
            data_J1,
            T=T,
            ti=ti
        )



### ---- PLOT ANIMATION T1 TRIANGULATION ---- ###

@dataclass
class PlotT1Params:
    figsize: Any = (10, 8)
    title: Any | None = None
    show_edges: bool = True
    edge_color: str = 'k'
    linewidth: float = 0.5
    show_nodes: bool = False
    show_node_labels: bool = False
    node_color: str = 'red'
    node_size: int = 10
    color_by: str = 'area'  # 'area' = normalised A/A₀; any T2 key ('shear', 'q', …) = custom
    colorbar_label: str = None  # overrides default colorbar label; None → auto
    cmap: str = 'RdYlGn'
    vmin: Any | None = None
    vmax: Any | None = None
    color_limit: Any | None = None  # None=auto; number N → log scale [1/N, N], red<1, white=1, blue>1
    face_color: str = 'lightblue'
    face_alpha: float = 0.7
    show_undeformed: bool = False
    undeformed_edge_color: str = '0.75'
    magnification: float = 1.0
    node_scale: float = 1.0
    show_colorbar: bool = True


@dataclass
class frame_animation_T1:
    dpi: int = 50
    title: str = None
    xlabel: str = None
    ylabel: str = None
    xlim: float = None
    ylim: float = None
    save_path: str = None
    background: bool = False
    figsize: list[float] = None
    num_frames: int = None
    T1_ext: str = ''
    T2_ext: str = None  # set to load T2 data when color_by != 'area'
    plot_T1_params: PlotT1Params = field(default_factory=PlotT1Params)
    plot_Mesh_Graph_params: PlotMeshGraphParams = field(default_factory=PlotMeshGraphParams)


def create_animation_T1_frame(c2, t1, T=None, ti=None, t2=None):
    """
    Create a single animation frame with the T1 triangulation mesh overlaid
    on the foam FEM mesh (plot_foam_mesh).

    Parameters
    ----------
    c2 : dict
        DATA_C2 dictionary (nodes_time, elements, baricenters, …).
    t1 : dict
        DATA_T1 dictionary (nodes, elements, elements_area_normalized, t, …).
    T : frame_animation_T1
        Frame configuration object.
    ti : int
        Timestep index (0-based).
    t2 : dict, optional
        DATA_T2 dictionary.  Required when ``T.plot_T1_params.color_by``
        is set to a T2 key (e.g. ``'shear'``, ``'q'``).
    """
    # ------------------------------------------------------------------
    # Resolve per-element colour values
    # ------------------------------------------------------------------
    _color_by  = T.plot_T1_params.color_by   # 'area' | 'none' | str T2 key | ('w', (K,G,m,n))
    _color_by_area = (_color_by != 'none')
    _custom_values = None
    _cb_label = T.plot_T1_params.colorbar_label

    if _color_by not in ('area', 'none'):
        elem_ids = sorted(t1['elements'].keys())
        # Support nested-key access: color_by = ('w', (K, G, m, n))
        # maps to t2['w'][(K, G, m, n)][eid][ti]
        if isinstance(_color_by, tuple) and len(_color_by) == 2:
            _top_key, _sub_key = _color_by
            if t2 is not None and _top_key in t2 and _sub_key in t2[_top_key]:
                try:
                    _custom_values = np.array(
                        [t2[_top_key][_sub_key][eid][ti] for eid in elem_ids], dtype=float
                    )
                    if _cb_label is None:
                        _cb_label = f"{_top_key}{list(_sub_key)}"
                except (KeyError, TypeError, IndexError) as _e:
                    print(f"Warning: could not read T2['{_top_key}'][{_sub_key}] at ti={ti}: {_e}")
            else:
                print(f"Warning: color_by={_color_by!r} requested but T2 data not available; "
                      "falling back to area colouring.")
        # Plain string key: existing behaviour unchanged
        elif t2 is not None and _color_by in t2:
            try:
                _custom_values = np.array(
                    [t2[_color_by][eid][ti] for eid in elem_ids], dtype=float
                )
                if _cb_label is None:
                    _cb_label = _color_by
            except (KeyError, TypeError, IndexError) as _e:
                print(f"Warning: could not read T2['{_color_by}'] at ti={ti}: {_e}")
        else:
            print(f"Warning: color_by='{_color_by}' requested but T2 data not available; "
                  "falling back to area colouring.")

    ax = plot_T1_triangulation_mesh(
        t1, ti,
        figsize=T.plot_T1_params.figsize,
        title=T.plot_T1_params.title,
        show_edges=T.plot_T1_params.show_edges,
        edge_color=T.plot_T1_params.edge_color,
        linewidth=T.plot_T1_params.linewidth,
        show_nodes=T.plot_T1_params.show_nodes,
        show_node_labels=T.plot_T1_params.show_node_labels,
        node_color=T.plot_T1_params.node_color,
        node_size=T.plot_T1_params.node_size,
        color_by_area=_color_by_area,
        custom_values=_custom_values,
        colorbar_label=_cb_label,
        cmap=T.plot_T1_params.cmap,
        vmin=T.plot_T1_params.vmin,
        vmax=T.plot_T1_params.vmax,
        color_limit=T.plot_T1_params.color_limit,
        face_color=T.plot_T1_params.face_color,
        face_alpha=T.plot_T1_params.face_alpha,
        show_undeformed=T.plot_T1_params.show_undeformed,
        undeformed_edge_color=T.plot_T1_params.undeformed_edge_color,
        magnification=T.plot_T1_params.magnification,
        node_scale=T.plot_T1_params.node_scale,
        show_colorbar=T.plot_T1_params.show_colorbar,
    )

    plot_foam_mesh(
        c2['nodes_time'][ti], elements=c2['elements'], ax=ax,
        elements_to_plot=T.plot_Mesh_Graph_params.elements_to_plot,
        show_element_numbers=T.plot_Mesh_Graph_params.show_element_numbers,
        node_size=T.plot_Mesh_Graph_params.node_size,
        plot_barycenters=T.plot_Mesh_Graph_params.plot_barycenters,
        barycenter_size=T.plot_Mesh_Graph_params.barycenter_size,
        boundary_only=T.plot_Mesh_Graph_params.boundary_only,
        boundary_lw=T.plot_Mesh_Graph_params.boundary_lw,
        boundary_color=T.plot_Mesh_Graph_params.boundary_color,
    )

    if T.xlim is not None:
        ax.set_xlim(T.xlim)
    if T.ylim is not None:
        ax.set_ylim(T.ylim)
    if T.xlabel is not None:
        ax.set_xlabel(T.xlabel)
    if T.ylabel is not None:
        ax.set_ylabel(T.ylabel)
    if T.title is not None:
        ax.set_title(T.title)
    if T.background == False:
        ax.set_axis_off()
        ax.grid(False)

    fig = ax.get_figure()
    if T.save_path:
        fig.savefig(T.save_path, dpi=T.dpi, bbox_inches='tight', transparent=True)
        plt.close(fig)
        print(f"Frame saved to {T.save_path}")
    else:
        plt.show()


def create_animation_T1_multiple_frames(sim_num, T, save_path=None, frames_format='png'):
    """
    Create multiple T1 animation frames for a simulation.

    Loads DATA_C2 and DATA_T1 pickles, then renders one frame per
    timestep (or a subset if T.num_frames is set).
    """
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_C2.pkl', 'rb') as f:
        data_C2 = pickle.load(f)

    t1_suffix = f'_T1_{T.T1_ext}' if T.T1_ext else '_T1'
    t1_path = f'I001_Results/DATA_PICK_{sim_num:03d}{t1_suffix}.pkl'
    with open(t1_path, 'rb') as f:
        data_T1 = pickle.load(f)

    # Load T2 data when a non-area colouring is requested
    data_T2 = None
    if T.plot_T1_params.color_by not in ('area', 'none'):
        if T.T2_ext is not None:
            t2_suffix = f'_T2_{T.T2_ext}' if T.T2_ext else '_T2'
            t2_path   = f'I001_Results/DATA_PICK_{sim_num:03d}{t2_suffix}.pkl'
            try:
                with open(t2_path, 'rb') as f:
                    data_T2 = pickle.load(f)
                print(f"Loaded T2 data from {t2_path}")
            except FileNotFoundError:
                print(f"Warning: T2 data not found at {t2_path}; "
                      "defaulting to area colouring.")
        else:
            print(f"Warning: color_by='{T.plot_T1_params.color_by}' requires "
                  "T2_ext to be set on frame_animation_T1.")

    os.makedirs(save_path, exist_ok=True)

    total_frames = len(data_C2['t'])
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    for ti in indices:
        T.save_path = save_path + f'frame_{ti:08d}.{frames_format}'
        T.t_x = ti
        create_animation_T1_frame(data_C2, data_T1, T=T, ti=ti, t2=data_T2)



# # GRAPHS



### ----------------------------- plot frame variable  -----------------------------##

@dataclass
class frame_variable:
    x_key_path = None
    y_key_paths: list[str] = None
    t_x = None
    legends = None
    invert_y = False
    derivative = False
    xlabel = None
    ylabel = None
    title = None
    save_path = None
    normalized_by = None
    f = None # additional factor to nomrlaize force than A or V
    xlim = None
    ylim = None
    dpi=50
    save_path: str = None
    figsize: list[float] = None
    num_frames: int = None
    experiment_plot: str = None
    experiment_normalize_load: float = None
    experiment_normalize_travel: float = None
    experiment_label: str = None
    plot_from_0: bool = False
    normalize_x: float = None
    file_key_y: str = 'A2'
    file_key_x: str = 'A2'
    yscale: str = 'linear'
    ratio_key_pairs: list = None



def create_variable_frame(pkl_A2_obj, T, pkl_y_obj=None):
    def der(y, x, n=1):
        for _ in range(n):
            y = np.gradient(y, x, edge_order=2)
        return y

    # Normalize derivative: False->0, True->1, int->int
    deriv_order = T.derivative
    if deriv_order is True:
        deriv_order = 1
    elif deriv_order is False:
        deriv_order = 0
    else:
        deriv_order = int(deriv_order)

    x_key_path =T.x_key_path
    y_key_paths = T.y_key_paths or []
    ratio_key_pairs = getattr(T, 'ratio_key_pairs', None) or []
    t_x = T.t_x
    legends = T.legends
    invert_y = T.invert_y
    xlabel = T.xlabel
    ylabel = T.ylabel
    title = T.title
    save_path = T.save_path
    normalized_by = T.normalized_by
    xlim = T.xlim
    ylim = T.ylim
    dpi=T.dpi
    
    
    # Create the plot
    if T.figsize is None:
        plt.figure(figsize=(8, 6))
    else:
        plt.figure(figsize=T.figsize)
        
    plt.grid(True)

    plot_legends = True

    # Ensure legends match the number of curves (y_key_paths + ratio_key_pairs)
    total_curves = len(y_key_paths) + len(ratio_key_pairs)
    if legends is None:
        legends = [f"Curve {i+1}" for i in range(total_curves)]
        plot_legends = False
    elif len(legends) != total_curves:
        raise ValueError("The number of legends must match the total number of curves (y_key_paths + ratio_key_pairs).")


    data_x = pkl_A2_obj
    data_y = pkl_y_obj if pkl_y_obj is not None else pkl_A2_obj

    data = data_x

    D = np.array(eval(f"data_x{x_key_path}"))

    if T.normalize_x is None:
        T.normalize_x = 1

    D = np.array(D)*T.normalize_x

    if normalized_by is not None:
        if normalized_by == 'A':
            normalized_factor = data_y['Lx']*data_y['Ly']
        elif normalized_by == "V":
            normalized_factor = data_y['Lx']*data_y['Ly']*data_y['Lz']
        elif normalized_by == 'fA':
            normalized_factor = data_y['Lx']*data_y['Ly']*T.f
        elif normalized_by == 'fV':
            normalized_factor = data_y['Lx']*data_y['Ly']*data_y['Lz']*T.f
        elif isinstance(normalized_by, (int, float)):
            normalized_factor = normalized_by
    else:
        normalized_factor = 1

    # Plot each curve
    for i, y_key_path in enumerate(y_key_paths):
        try:
            RF3 = np.array(eval(f"data_y{y_key_path}"))
            if invert_y == True:
                RF3 = -RF3
            Y = der(RF3, D, deriv_order) / normalized_factor if deriv_order > 0 else RF3 / normalized_factor

            plt.plot(D, Y, '-', label=legends[i])

            if T.plot_from_0 is True:
                plt.plot(D - D[0], Y, '-', label=legends[i])



            if t_x is not None:
                if T.experiment_plot is None:
                    plt.scatter(D[t_x], Y[t_x], color='red')

                    if T.plot_from_0 is True:
                        plt.scatter(D[t_x] - D[0], Y[t_x], color='red')
                else:
                    plt.axvline(D[t_x], color='red', linestyle=':', linewidth=2)
                    
        except:
            print(y_key_path)
            print('Warning variable do not exist')

    # Plot ratio curves
    for i, (num_path, den_path) in enumerate(ratio_key_pairs):
        try:
            num_vals = np.array(eval(f"data_y{num_path}"))
            den_vals = np.array(eval(f"data_y{den_path}"))
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = np.where(den_vals != 0, num_vals / den_vals, np.nan)
            label = legends[len(y_key_paths) + i]
            plt.plot(D, ratio, '-', label=label)
            if t_x is not None:
                plt.scatter(D[t_x], ratio[t_x], color='red')
        except Exception:
            print(f"Warning: ratio {num_path}/{den_path} could not be computed")

        
    if xlabel is not None:
        plt.xlabel(xlabel)

    if ylabel is not None:
        plt.ylabel(ylabel)

    if title is not None:
        plt.title(title)

    if plot_legends is True:
        plt.legend(loc='upper left')
        
    if xlim is not None:
        plt.xlim(xlim)
    
    if ylim is not None:
        plt.ylim(ylim)

    plt.yscale(getattr(T, 'yscale', 'linear'))

    # Save or display the plot
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
        plt.close()
    else:
        plt.show()


def create_variable_multiple_frames(sim_num, T , save_path = None, frames_format='png'):
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_{T.file_key_x}.pkl', "rb") as f:
        pkl_x_obj = pickle.load(f)

    if T.file_key_y != T.file_key_x:
        with open(f'I001_Results/DATA_PICK_{sim_num:03d}_{T.file_key_y}.pkl', "rb") as f:
            pkl_y_obj = pickle.load(f)
    else:
        pkl_y_obj = pkl_x_obj

    os.makedirs(save_path, exist_ok=True)

    total_frames = len(pkl_x_obj['t'])
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    if T.experiment_plot is not None:
        T.experiment_plot = T.experiment_plot + f'{sim_num:03d}.log'

    for ti in indices:
        T.save_path = save_path + f'frame_{ti:08d}.{frames_format}'
        T.t_x = ti
        create_variable_frame(pkl_x_obj, T, pkl_y_obj=pkl_y_obj)






## ------------- FUNCTIONS TO COMBINE AND MAKE VIDEO -----------------------## 
@dataclass
class frames_combination:
    figures_path = None
    sizes: List[str] = None
    title = None
    subtitles = None
    save_path = False
    title_size = 40
    output_path = None
    title_font = None
    subtitle_size = 30
    subtitle_font = None
    subtitle_offset = 5
    title_color = "black"
    subtitle_color = "black"
    dpi = (300, 300)
    frames_to_create: List[str] = None
    objects: List[object] = None
    delete_frames: bool = False
    canvas_size = (800, 600)
    canvas_color = "white"
    title_position = (0, 0)
    size = (300, 300)
    elements: List[dict] = None
    delete_after_concat: bool = False
    max_parallel: int = 50
    frames_format: str = 'png'
    num_frames: int = None
    vid_folder: str = "Video_001"

@dataclass
class SimulationConfig:
    delete_concat_frames_after_video: bool = False
    frames_format: str = 'png'
    max_parallel: int = 50
    individual_frames_path: List[str] = None
    frame_rate: int = 30
    codec: str = "mp4v"
    frames_pattern: str = None
    video_output_name: str = None
    vid_folder: str = "Video_001"


def create_placeholder_image(size, color_name):
    color_map = {
        'white': (255, 255, 255),
        'gray': (128, 128, 128),
        'black': (0, 0, 0)
    }
    color = color_map.get(color_name.lower(), (255, 255, 255))
    return Image.new("RGB", size, color)

def safe_load_image(path, size):
    if path.lower() in ["white", "gray", "black"]:
        # Use default size if size is None
        return create_placeholder_image(size if size else (100, 100), path)
    if not os.path.isfile(path):
        return create_placeholder_image(size if size else (100, 100), "white")
    try:
        img = Image.open(path).convert("RGB")
        if size is not None:
            return img.resize(size)
        else:
            return img  # Return original size if size is None
    except Exception:
        return create_placeholder_image(size if size else (100, 100), "white")



def flexible_image_compositor_updated(T):
    canvas_size = T.canvas_size
    elements = T.elements
    title = T.title
    title_position = T.title_position
    output_path = T.save_path
    title_font = T.title_font
    title_size = T.title_size
    title_color = T.title_color
    dpi = T.dpi

    try:
        # Load title font
        font = ImageFont.truetype(title_font, title_size) if title_font else ImageFont.load_default()

        # Create canvas
        canvas = Image.new("RGB", canvas_size, T.canvas_color)
        draw = ImageDraw.Draw(canvas)

        # Draw title
        draw.text(title_position, title, fill=title_color, font=font)

        # Draw each image element
        for el in elements:
            pos = el["position"]
            size = el["size"]
            path = el["path"]
            subtitle = el.get("subtitle", "")
            subtitle_font_path = el.get("subtitle_font", title_font)
            subtitle_font_size = el.get("subtitle_size", T.subtitle_size)
            subtitle_offset = el.get("subtitle_offset", 5)

            subtitle_font = ImageFont.truetype(subtitle_font_path, subtitle_font_size) if subtitle_font_path else ImageFont.load_default()
            img = safe_load_image(path, size)
            # If size is None, use the image's original size for pasting
            if size is None:
                canvas.paste(img, pos)
                img_width, img_height = img.size
                actual_size = (img_width, img_height)
            else:
                canvas.paste(img, pos)
                actual_size = size

            # Draw subtitle if present
            if subtitle:
                subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_x = pos[0] + (actual_size[0] - subtitle_width) // 2
                subtitle_y = pos[1] + actual_size[1] + subtitle_offset
                draw.text((subtitle_x, subtitle_y), subtitle, fill=T.subtitle_color, font=subtitle_font)

        # Save or display result
        if output_path:
            canvas.save(output_path, dpi=dpi)
            print(f"Image saved at {output_path}")
        else:
            canvas.show()

        # Delete source files if requested
        if getattr(T, 'delete_after_concat', False):
            for el in elements:
                path = el["path"]
                try:
                    os.remove(path)
                    print(f"Deleted: {path}")
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

    except Exception as e:
        print(f"Error in flexible_image_compositor_updated: {e}")


def _create_single_frame_object(args):
    """Module-level helper for parallel frame-object creation (one process per object)."""
    frame_type, obj, sim_num, save_path, replace_frames, frames_format = args

    frame_functions = {
        'V':   create_variable_multiple_frames,
        'A':   create_animation_multiple_frames,
        'GP':  create_graph_property_multiple_frames,
        'GA':  create_animation_graph_multiple_frames,
        'T1A': create_animation_T1_multiple_frames,
    }

    if frame_type not in frame_functions or obj is None:
        return

    print(replace_frames is True)
    print(save_path)

    if not replace_frames and os.path.exists(save_path) and len(os.listdir(save_path)) > 0:
        print(f"Skipping frame creation for {save_path} (replace_frames=False and folder exists)")
        return

    if replace_frames is True or not os.path.exists(save_path):
        print(f"Overwriting frame creation for {save_path}")
        try:
            if frame_type in ['EFS', 'EM', 'EB', 'EA']:
                frame_functions[frame_type](sim_num, obj, num_workers=1, save_path=save_path, frames_format=frames_format)
            else:
                frame_functions[frame_type](sim_num, obj, save_path=save_path, frames_format=frames_format)
        except Exception as e:
            print(f"Skipping {save_path}: {e}")
    else:
        print('SOMETHING NOT WORKING in create_frames_for_sim')


def create_frames_for_sim(sim_num, T_C, max_parallel=1, frames_format='png'):
    delete_frames = T_C.delete_frames
    frames_type_to_create = []
    objects = []
    paths_to_delete = []
    for ele in T_C.elements:
        if ele['create_frames'] is True:
            frames_type_to_create.append(ele['type'])
            OBJ = ele['object']
            OBJ.save_path = ele['path']
            objects.append(OBJ)
            paths_to_delete.append(ele['path'])
            

    
    
    # Mapping frame types to corresponding functions
    frame_functions = {
        'V': create_variable_multiple_frames,
        'A': create_animation_multiple_frames,
        'GP': create_graph_property_multiple_frames,
        'GA': create_animation_graph_multiple_frames,
        'T1A': create_animation_T1_multiple_frames,
    }

    tasks = []
    for frame_type, obj in zip(frames_type_to_create, objects):
        if frame_type in frame_functions and obj is not None:
            save_path = f'I002_Videos/{T_C.vid_folder}/SIM_{sim_num:03d}/' + obj.save_path

            replace_frames = True
            for ele in T_C.elements:
                if ele.get('path', None) == obj.save_path:
                    replace_frames = ele.get('replace_frames', True)
                    break

            tasks.append((frame_type, obj, sim_num, save_path, replace_frames, frames_format))

    if max_parallel > 1:
        with ProcessPoolExecutor(max_workers=max_parallel) as executor:
            list(executor.map(_create_single_frame_object, tasks))
    else:
        for task in tasks:
            _create_single_frame_object(task)


def concatenate_multiple_images_for_sim(sim_num,T, num_workers=30, frames_format='png'):
    # from A001_functions.Hex_pack_funct import from_name, from_r_to_p

    # print(f'evvvvv: {from_r_to_p(3)}')

    title_gen = T.title  # Store the original title
    
    # Check if title contains placeholders to evaluate
    contains_evaluation = "{" in title_gen and "}" in title_gen if title_gen else False
    
    # if contains_evaluation:
    with open(f'I001_Results/DATA_PICK_{sim_num:03d}_A2.pkl', "rb") as f:
        DATA = pickle.load(f)

    with open(f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json', 'r') as file:
        DATA_J = json.load(file)

    # --- load porosity from mesh JSON ---
    _mesh_file = DATA_J.get('input_name', '')
    porosity = None
    if _mesh_file.endswith('.mesh.json') and os.path.exists(_mesh_file):
        with open(_mesh_file, 'r') as _f:
            _mesh_info = json.load(_f)
        porosity = _mesh_info.get('geometry', {}).get('porosity')


    original_save_path = T.save_path 
    original_element_paths = [ele['path'] for ele in T.elements]

    total_frames = len(DATA['t'])
    
    if getattr(T, 'num_frames', None) is not None and T.num_frames is not None and T.num_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, T.num_frames, dtype=int)
    else:
        indices = range(total_frames)

    # for ti in range(len(DATA['t'])):
    for ti in indices:
        try:
            T.ti = ti
            
            T.save_path = 'I002_Videos/' + T.vid_folder + f'/SIM_{sim_num:03d}/' + original_save_path + f'frame_{ti:08d}.{frames_format}'
        
            os.makedirs(os.path.dirname(T.save_path), exist_ok=True)    
        
            #update path
            for ele_idx in range(len(T.elements)):
                if T.elements[ele_idx]['path'] not in ['white', 'black', 'gray']:
                    if original_element_paths[ele_idx][0] == '!':
                        T.elements[ele_idx]['path'] =  original_element_paths[ele_idx][1:].replace('!SIM_NUM', f'SIM_{sim_num:03d}') + f'frame_{ti:08d}.{frames_format}'
                    else:
                        T.elements[ele_idx]['path'] = 'I002_Videos/' + T.vid_folder + f'/SIM_{sim_num:03d}/' + original_element_paths[ele_idx] + f'frame_{ti:08d}.{frames_format}'

            
            # if contains_evaluation:
            #     try:
            #         T.title = eval(f'f"""{title_gen}"""', {"DATA": DATA, "DATA_J": DATA_J, "ti": ti})
            #     except Exception as e:
            #         print(f"Error evaluating title for frame {ti}: {e}")
            if contains_evaluation:
                try:
                    T.title = eval(f'f"""{title_gen}"""', {
                        "DATA": DATA, 
                        "DATA_J": DATA_J, 
                        "ti": ti,
                        "porosity": porosity,
                        # "from_name": from_name,
                        # "from_r_to_p": from_r_to_p
                    })
                except Exception as e:
                    print(f"Error evaluating title for frame {ti}: {e}")

            flexible_image_compositor_updated(T)


            
        except Exception as e:
            print(f"Error in concatenate_multiple_images ti {ti}: {e}")


    path_to_delete = [T.elements[ele_idx]['path'] for ele_idx in range(len(T.elements))]

    for file_path in path_to_delete:
        folder_path = os.path.dirname(file_path)
        
        if os.path.isdir(folder_path):
            all_items = os.listdir(folder_path)
            
            # Remove .ipynb_checkpoints if present
            checkpoints_path = os.path.join(folder_path, '.ipynb_checkpoints')
            if '.ipynb_checkpoints' in all_items:
                try:
                    if os.path.isdir(checkpoints_path):
                        os.rmdir(checkpoints_path)  # only works if it's empty
                except OSError:
                    pass  # leave it if not empty
        
            # Refresh the item list
            all_items = os.listdir(folder_path)
            if not all_items:
                os.rmdir(folder_path)
                print(f'remove {folder_path}')
                



def create_vid_from_frames(frame_pattern=None, output_path=None, frame_rate=50, codec="mp4v", delete_frames=False):

    # Get list of image frames and sort them numerically
    frame_files = sorted(glob.glob(frame_pattern))

    if not frame_files:
        print(f"No frames found in {frame_pattern}. Make sure the images are in the correct format (frame_XXXXXX.png).")
        return

    # Read first frame to get dimensions
    first_frame = cv2.imread(frame_files[0])
    if first_frame is None:
        print(f"Could not read the first frame: {frame_files[0]}")
        return
    height, width, _ = first_frame.shape

    # Create a temporary AVI file
    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp_avi:
        avi_path = tmp_avi.name

    # Write frames to AVI using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Use XVID for AVI
    video_writer = cv2.VideoWriter(avi_path, fourcc, frame_rate, (width, height))

    for frame_file in frame_files:
        frame = cv2.imread(frame_file)
        if frame is None:
            print(f"Warning: Could not read {frame_file}. Skipping.")
            continue
        video_writer.write(frame)

    video_writer.release()

    # Convert AVI to MP4 using FFmpeg
    if output_path is None:
        output_path = os.path.splitext(avi_path)[0] + ".mp4"

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file if exists
        "-i", avi_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Video saved as {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed: {e.stderr.decode()}")
        print(f"AVI video saved as {avi_path} (MP4 conversion failed)")
        return

    # Remove temporary AVI file
    try:
        os.remove(avi_path)
    except Exception as e:
        print(f"Error deleting temporary AVI file: {e}")

    # Optionally delete frames and their folder
    if delete_frames:
        frame_dir = os.path.dirname(frame_files[0])
        for frame_file in frame_files:
            try:
                os.remove(frame_file)
            except Exception as e:
                print(f"Error deleting {frame_file}: {e}")
        try:
            shutil.rmtree(frame_dir)
            print(f"Deleted folder: {frame_dir}")
        except Exception as e:
            print(f"Error deleting folder {frame_dir}: {e}")


    
def create_vid_from_frames_for_sim(sim_num, SCONF):
    frame_pattern = f'I002_Videos/{SCONF.vid_folder}/SIM_{sim_num:03d}/' + SCONF.frames_pattern
    output_path = f'I002_Videos/{SCONF.vid_folder}/SIM_{sim_num:03d}/' + SCONF.video_output_name

    #add sim_num
    base, ext = os.path.splitext(output_path)
    output_path = f"{base}_SIM_{sim_num:03d}{ext}"

    create_vid_from_frames(frame_pattern = frame_pattern, output_path = output_path, frame_rate = SCONF.frame_rate, codec = SCONF.codec, delete_frames = SCONF.delete_concat_frames_after_video)


