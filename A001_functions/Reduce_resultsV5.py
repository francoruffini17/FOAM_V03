import pickle
import multiprocessing
from .Read_resultsV5 import *
import numpy as np
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from types import SimpleNamespace
import igraph as ig
from A001_functions.mesh_functions import read_surfaces_from_inp, find_barycenters, add_id, filter_nodes, filter_elements_from_nodes, find_element_adjacency # find_triangle_adjacency
from A001_functions.Hex_5 import (read_graph_mesh, map_undeformed_to_deformed,
    _get_element_nodes_at, _map_physical_to_natural_quad,
    _map_physical_to_natural_tri, _point_in_tri, _dist_outside_tri,
    _shape_functions_tri, read_mesh_json)
from A001_functions.fem_stress_interpolation import interpolate_stress
from scipy.spatial import cKDTree
from scipy.linalg import fractional_matrix_power
from numba import jit


def _mesh_prefix_from_input_name(input_name: str) -> str:
    """
    Return the mesh artifact prefix used in C001_Mesh_files.

    New mesh JSON files are named like ``R010.mesh.json`` and derived files are
    named like ``R010_J2000.graph.json``.  Older inputs may still include extra
    underscore suffixes, so keep the old split fallback for those.
    """
    base = os.path.basename(input_name)
    if base.endswith(".mesh.json"):
        return base[:-len(".mesh.json")]
    return base.split("_")[0]


def _mesh_artifact_path(mesh_prefix: str, family: str, ext_id: int, suffix: str) -> str:
    """Build a C001_Mesh_files artifact path for J/H/I/K/T derived meshes."""
    return f"C001_Mesh_files/{mesh_prefix}_{family}{ext_id:03d}.{suffix}"


def _source_metadata(source_file):
    """Small provenance block stored in generated pickle dictionaries."""
    if source_file is None:
        return {'source_file': None, 'source_files': []}
    return {'source_file': source_file, 'source_files': [source_file]}


def _propagate_source_metadata(source_data):
    """Carry source-file provenance from an input pickle dictionary."""
    source_files = list(source_data.get('source_files', []))
    source_file = source_data.get('source_file')
    if source_file is not None and source_file not in source_files:
        source_files.insert(0, source_file)
    return {'source_file': source_file, 'source_files': source_files}


def _mesh_prefix_for_sim(sim_num: int) -> str:
    """Read the simulation JSON and derive the mesh artifact prefix."""
    json_path = f"I001_Results/OBJ_files/SIM_{sim_num:03d}.json"
    with open(json_path, "r") as f:
        sim_json = json.load(f)
    return _mesh_prefix_from_input_name(sim_json["input_name"])


def _load_pickle_or_skip(path: str, context: str):
    """Load a pickle dependency, returning None when this item should be skipped."""
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Skipping {context}; could not load '{path}': {e}")
        return None


def merge_data(data, dataa2):
    """
    Creates a new dictionary based on `data`, adding or updating 
    the 'cr' and 'd' keys from `dataa2` if they exist.
    
    Args:
        data (dict): The base dictionary.
        dataa2 (dict): The dictionary containing additional entries.
    
    Returns:
        dict: A new dictionary combining `data` with selected entries from `dataa2`.
    """
    new_dict = data.copy()  # Copy the original dictionary
    for key in ['t']:
        if key in dataa2:  # Only add if the key exists in dataa2
            new_dict[key] = dataa2[key]

    return new_dict



def create_graph_object(nodes_id, elements_id, adjacency_id, mean_dict_stress,  mode='tension', plot_g = True, title = None, condition= None):
    """
    Creates the graph object of a sim_num for a given instant of time, criteria and mode (tension or compression)
    """

    if condition is not None:
        nodes_filtered, nodes_removed = filter_nodes(nodes_id, condition)
        elements_filtered, elements_removed = filter_elements_from_nodes(elements_id, nodes_filtered)
        adjacency_filtered, adjacency_removed = filter_elements_from_nodes(adjacency_id, elements_filtered)
    else:
        nodes_filtered = nodes_id
        elements_filtered = elements_id
        adjacency_filtered = adjacency_id


    # I dentiffy tenssion or compression based on the tension ID:
    connections = [] #connections only in tension or compression
    connection_colors = []

    if mode == 'tension':
        for key in adjacency_filtered.keys():
            if mean_dict_stress[key] >=0:
                connections.append(adjacency_filtered[key][0:2])
                connection_colors.append('blue')

  
    elif mode == 'compression':
        for key in adjacency_filtered.keys():
            if mean_dict_stress[key] < 0:
                connections.append(adjacency_filtered[key][0:2])
                connection_colors.append('blue')
    else:
        raise ValueError("Invalid mode. Please specify 'tension' or 'compression'.")

    
    G = nx.Graph()
    G.add_nodes_from(list(map(int, nodes_filtered.keys())))
    G.add_edges_from(connections)
    # G.ids = ids


    D = SimpleNamespace(
    mode = mode,
    )
        
    for key, value in vars(D).items():
        setattr(G, key, value)

    if title is None:
        G.title = f'GRAPH'
    else:
        G.title = title


    # Assign color attributes to edges
    for i, edge in enumerate(connections):
        G.edges[edge]['color'] = connection_colors[i]

    if plot_g == True:
        plt.figure(figsize=(8, 6))  # Optional: set the figure size
        plt.title(G.title)
        nx.draw(G, with_labels=True, node_size=10, font_size=10, font_color='black', edge_color=connection_colors)
        plt.show()

    return G



def create_PKL_G(data_D, data_C2, condition= None):

    num_t_steps = len(data_C2['nodes_time'])
    nodes = data_C2['nodes_time'][0]
    adjacency = data_C2['adjacency']
    elements = data_C2['elements']

    # nodes_time[0] is already a dict with 1-based string keys
    nodes_id = nodes
    # elements and adjacency are already dicts with 1-based string keys
    elements_id = elements
    adjacency_id = adjacency

    modes = ['tension', 'compression']

    DATA_G = {}
    DATA_G['tension'] = []
    DATA_G['compression'] = []
    DATA_G['t'] = data_D['t']


    for mode in modes:
        for ti_0 in range(num_t_steps):
            ti_key = str(ti_0 + 1)
            stresses_vals = add_id(data_D['stresses'][ti_key])
            mean_dict_stress = {key: sum(value) / len(value) for key, value in stresses_vals.items()}
            G = create_graph_object(nodes_id, elements_id, adjacency_id, mean_dict_stress,  mode=mode, plot_g = False, title = None, condition= condition)
            DATA_G[mode].append(G)

    return DATA_G


def create_PKL_G2(DATA_G):
    """
    Optimized version that reduces memory usage and improves speed
    """
    
    @jit(nopython=True)
    def compute_efficiency_from_distances(dist_array):
        """JIT-compiled function to compute efficiency from distance matrix"""
        n = dist_array.shape[0]
        efficiency_sum = 0.0
        
        for i in range(n):
            for j in range(n):
                if i != j and dist_array[i, j] > 0 and np.isfinite(dist_array[i, j]):
                    efficiency_sum += 1.0 / dist_array[i, j]
        
        return efficiency_sum / (n * (n - 1))
    
    
    def compute_global_efficiency_fast(G_nx):
        """
        Memory-optimized global efficiency computation
        """
        # Handle empty or single-node graphs
        n = len(G_nx)
        print('sample size:', n)

        if n < 2:
            return 0.0
        
        # For very large graphs (>5000 nodes), use sampling
        if n > 2:
            return compute_global_efficiency_sampled(G_nx, sample_size=4000)
        
        # Convert to igraph for faster shortest paths
        try:
            G_ig = ig.Graph.from_networkx(G_nx)
            
            # Compute shortest paths in chunks to reduce memory
            chunk_size = min(500, n)  # Process nodes in chunks
            efficiency_sum = 0.0
            
            for start_idx in range(0, n, chunk_size):
                end_idx = min(start_idx + chunk_size, n)
                
                # Get distances only for this chunk of source nodes
                dist_chunk = G_ig.shortest_paths(source=range(start_idx, end_idx))
                dist_chunk = np.array(dist_chunk, dtype=np.float32)  # Use float32 to save memory
                
                # Compute efficiency for this chunk
                for i, row in enumerate(dist_chunk):
                    for j, d in enumerate(row):
                        if d > 0 and np.isfinite(d):
                            efficiency_sum += 1.0 / d
                
                # Free memory
                del dist_chunk
            
            return efficiency_sum / (n * (n - 1))
            
        except Exception as e:
            print(f"Warning: igraph conversion failed ({e}), falling back to NetworkX")
            return compute_global_efficiency_networkx(G_nx)
    
    
    def compute_global_efficiency_networkx(G_nx):
        """Fallback method using NetworkX with memory optimization"""
        n = len(G_nx)
        if n < 2:
            return 0.0
        
        efficiency_sum = 0.0
        # Process shortest paths one source at a time to minimize memory
        for source in G_nx.nodes():
            lengths = nx.single_source_shortest_path_length(G_nx, source)
            for target, length in lengths.items():
                if source != target and length > 0:
                    efficiency_sum += 1.0 / length
        
        return efficiency_sum / (n * (n - 1))
    
    
    def compute_global_efficiency_sampled(G_nx, sample_size=4000):
        """
        For very large graphs, estimate global efficiency using sampling
        """
        n = len(G_nx)
        if n < 2:
            return 0.0
        
        nodes = list(G_nx.nodes())
        sample_size = min(sample_size, n)
        sampled_nodes = np.random.choice(nodes, size=sample_size, replace=False)
        
        efficiency_sum = 0.0
        count = 0
        
        for source in sampled_nodes:
            lengths = nx.single_source_shortest_path_length(G_nx, source)
            for target in sampled_nodes:
                if source != target and target in lengths:
                    length = lengths[target]
                    if length > 0:
                        efficiency_sum += 1.0 / length
                        count += 1
        
        if count == 0:
            return 0.0
        
        return efficiency_sum / count

    
    # Initialize result lists
    global_ef_t = []
    global_ef_c = []
    
    total_steps = len(DATA_G['tension'])
    
    for i in range(total_steps):
        print(f'Processing time step {i+1} of {total_steps}')
        
        # Compute global efficiency for tension network
        try:
            eff_t = compute_global_efficiency_fast(DATA_G['tension'][i])
            global_ef_t.append(eff_t)
        except Exception as e:
            print(f"Error processing tension graph at step {i}: {e}")
            global_ef_t.append(np.nan)
        
        # Compute global efficiency for compression network
        try:
            eff_c = compute_global_efficiency_fast(DATA_G['compression'][i])
            global_ef_c.append(eff_c)
        except Exception as e:
            print(f"Error processing compression graph at step {i}: {e}")
            global_ef_c.append(np.nan)
    
    # Create output dictionary
    pkl_G2 = {
        't': DATA_G['t'],
        'global_ef_t': global_ef_t,
        'global_ef_c': global_ef_c,
        **_propagate_source_metadata(DATA_G),
    }
    
    return pkl_G2




# def create_PKL_G2_exact(DATA_G):


#     # Convert
#     def compute_global_efficiency_fast(G_nx):
#         G_ig = ig.Graph.from_networkx(G_nx)
#         dist = G_ig.shortest_paths()
#         dist = np.array(dist, dtype=float)

#         # Convert to efficiency: 1 / d, with infinite → 0
#         dist[dist == 0] = np.inf   # diagonal
#         eff_matrix = 1.0 / dist
#         eff_matrix[~np.isfinite(eff_matrix)] = 0.0
#         n = len(G_ig.vs)
#         global_eff = eff_matrix.sum() / (n*(n-1))
        
#         return global_eff


#     def global_efficiency_weighted(G, weight='weight'):
#         n = len(G)
#         if n < 2:
#             return 0  # no pairs of nodes

#         # Compute all-pairs shortest path lengths using the specified weight
#         length_dict = dict(nx.all_pairs_dijkstra_path_length(G, weight=weight))

#         # Accumulate the inverse of the shortest paths
#         efficiency_sum = 0
#         for u in G.nodes():
#             for v in G.nodes():
#                 if u != v:
#                     try:
#                         d = length_dict[u][v]
#                         efficiency_sum += 1 / d
#                     except KeyError:
#                         # No path between u and v
#                         continue

#         return efficiency_sum / (n * (n - 1))


#     sg_t=[]
#     sg_c=[]
#     gd_t=[]
#     gd_c=[]
#     sg_t2 = []
#     sg_c2 = []
#     c_t = []
#     c_c = []
#     g_t = []
#     g_c = []
#     trans_t = []
#     trans_c = []
#     local_ef_t = []
#     local_ef_c = []
#     global_ef_t = []
#     global_ef_c = []
#     global_ef_W_t = []
#     global_ef_W_c = []
#     s_metric_t = []
#     s_metric_c = []


#     for i in range(len(DATA_G['tension'])):

#         print(f'Processing time step {i+1} of {len(DATA_G["tension"])}')
#         # #Number of subgraph without disconnected nodes
#         # sg_t2.append(nx.number_connected_components(DATA_G['tension'][i]))
#         # sg_c2.append(nx.number_connected_components(DATA_G['compression'][i]))

#         # #number of graph
#         # sg_t.append(nx.number_connected_components(DATA_G['tension'][i]))
#         # sg_c.append(nx.number_connected_components(DATA_G['compression'][i]))

#         # #graph density
#         # gd_t.append(nx.density(DATA_G['tension'][i]))
#         # gd_c.append(nx.density(DATA_G['compression'][i]))

#         # # is the graph connected?
#         # c_t.append(nx.is_connected(DATA_G['tension'][i]))
#         # c_c.append(nx.is_connected(DATA_G['compression'][i]))

#         # # girth
#         # g_t.append(nx.girth(DATA_G['tension'][i]))
#         # g_c.append(nx.girth(DATA_G['compression'][i]))

#         # # graph transitivity
#         # trans_t.append(nx.transitivity(DATA_G['tension'][i]))
#         # trans_c.append(nx.transitivity(DATA_G['compression'][i]))

#         # # local efficiency
#         # local_ef_t.append(nx.local_efficiency(DATA_G['tension'][i]))
#         # local_ef_c.append(nx.local_efficiency(DATA_G['compression'][i]))

#         # # global efficiency
#         # global_ef_t.append(nx.global_efficiency(DATA_G['tension'][i]))
#         # global_ef_c.append(nx.global_efficiency(DATA_G['compression'][i]))

#         # global efficiency
#         global_ef_t.append(compute_global_efficiency_fast(DATA_G['tension'][i]))
#         global_ef_c.append(compute_global_efficiency_fast(DATA_G['compression'][i]))

#         # # # global efficiency wrighted
#         # global_ef_W_t.append(global_efficiency_weighted(DATA_G['tension'][i]))
#         # global_ef_W_c.append(global_efficiency_weighted(DATA_G['compression'][i]))

#         # # s-metric
#         # s_metric_t.append(nx.s_metric(DATA_G['tension'][i]))
#         # s_metric_c.append(nx.s_metric(DATA_G['compression'][i]))

        






#     pkl_G2 = {
#         't': DATA_G['t'],
#         # 'num_sub_t': sg_t,
#         # 'num_sub_c': sg_c,
#         # 'num_sub_no_indv_t': sg_t2,
#         # 'num_sub_no_indv_c': sg_c2,
#         # 'density_t': gd_t,
#         # 'density_c': gd_c,
#         # 'connected_t': c_t,
#         # 'connected_c': c_c,
#         # 'girth_t': g_t,
#         # 'girth_c': g_c,
#         # 'trans_t': trans_t,
#         # 'trans_c': trans_c,
#         # 'local_ef_t': local_ef_t,
#         # 'local_ef_c': local_ef_c,
#         'global_ef_t': global_ef_t,
#         'global_ef_c': global_ef_c,
#         # 's_metric_t': s_metric_t,
#         # 's_metric_c': s_metric_c,
#         # 'global_ef_W_t': global_ef_W_t,
#         # 'global_ef_W_c': global_ef_W_c
#     }


#     return pkl_G2
 


def _compute_global_efficiency_exact(G_nx, algorithm=None):
    """Module-level function for global efficiency (picklable for multiprocessing).

    Parameters
    ----------
    G_nx : networkx.Graph
        The graph.
    algorithm : str or None, optional
        ``None`` (default) uses igraph ``shortest_paths``;
        ``'bfs'`` uses Breadth-First Search (unweighted graphs).

    Returns
    -------
    (efficiency, pair_sum) : tuple of float
        ``efficiency`` is the standard global efficiency
        ``pair_sum / (n * (n - 1))`` with *n* the graph's node count;
        ``pair_sum`` is the raw sum of ``1/d(i, j)`` over all ordered
        pairs, so callers can re-normalise with a different node count.
    """
    n = len(G_nx)
    if n < 2:
        return 0.0, 0.0
    G_ig = ig.Graph.from_networkx(G_nx)

    if algorithm == 'bfs':
        # BFS-based all-pairs shortest paths (unweighted)
        # G_ig.bfs(source) returns (vertices, layer_starts, parents):
        #   vertices    – vertex IDs in BFS visit order (only the vertices
        #                 reachable from `source`; unreachable ones stay inf)
        #   layer_starts – indices into `vertices` where each new layer begins,
        #                 ending with a sentinel equal to len(vertices)
        #   parents     – parent of each vertex in the BFS tree
        dist = np.full((n, n), np.inf)
        for source in range(n):
            vertices, layer_starts, _ = G_ig.bfs(source)
            for layer_idx in range(len(layer_starts) - 1):
                start = layer_starts[layer_idx]
                end = layer_starts[layer_idx + 1]
                for pos in range(start, end):
                    dist[source, vertices[pos]] = layer_idx
        dist[dist == 0] = np.inf
    else:
        dist = G_ig.shortest_paths()
        dist = np.array(dist, dtype=float)
        dist[dist == 0] = np.inf

    eff_matrix = 1.0 / dist
    eff_matrix[~np.isfinite(eff_matrix)] = 0.0
    pair_sum = float(eff_matrix.sum())
    return pair_sum / (n * (n - 1)), pair_sum


def _process_timestep_exact(args):
    """Worker function for a single timestep (picklable for multiprocessing)."""
    i, G_tension, G_compression, algorithm, n_total = args
    eff_t, sum_t = _compute_global_efficiency_exact(G_tension, algorithm)
    eff_c, sum_c = _compute_global_efficiency_exact(G_compression, algorithm)
    if n_total is not None and n_total >= 2:
        norm_all = n_total * (n_total - 1)
        eff_t_all = sum_t / norm_all
        eff_c_all = sum_c / norm_all
    else:
        # Total node count unknown (e.g. H2/I2 pickle created before
        # 'n_nodes_total' was added) - store NaN rather than a misleading value.
        eff_t_all = float('nan')
        eff_c_all = float('nan')
    return i, eff_t, eff_c, eff_t_all, eff_c_all


def create_PKL_G2_exact(DATA_G, n_workers=None, max_memory_gb=None, algorithm=None):
    """
    Compute global efficiency for tension/compression graphs at each timestep.

    Parameters
    ----------
    DATA_G : dict
        Dictionary with keys ``'tension'``, ``'compression'``, ``'t'``.
    n_workers : int, optional
        Number of parallel worker processes.  Defaults to
        ``min(cpu_count, total_steps)``.  Set to 1 to disable
        parallelism.
    max_memory_gb : float, optional
        Approximate RAM budget in GB.  When provided the number of
        workers is capped so that total estimated usage stays below
        this limit (rough heuristic: each worker may hold a full
        dense distance matrix of the largest graph).
    algorithm : str or None, optional
        ``None`` (default) uses igraph ``shortest_paths``;
        ``'bfs'`` uses Breadth-First Search (unweighted graphs).
    """
    from concurrent.futures import ProcessPoolExecutor

    total_steps = len(DATA_G['tension'])

    # ---- Determine worker count ----------------------------------------
    if n_workers is None:
        n_workers = min(multiprocessing.cpu_count(), total_steps)

    if max_memory_gb is not None and total_steps > 0:
        # Estimate peak memory per worker from largest graph
        max_nodes = max(
            max(len(DATA_G['tension'][i]), len(DATA_G['compression'][i]))
            for i in range(total_steps)
        )
        # float64 distance matrix: n*n*8 bytes, x2 for intermediate arrays
        mem_per_worker_gb = (max_nodes ** 2 * 8 * 2) / (1024 ** 3)
        if mem_per_worker_gb > 0:
            n_workers = min(n_workers, max(1, int(max_memory_gb / mem_per_worker_gb)))

    n_workers = max(1, n_workers)
    print(f"create_PKL_G2_exact: {total_steps} timesteps, {n_workers} workers, algorithm={algorithm}")

    # ---- Build task list -----------------------------------------------
    # n_nodes_total: total overlay-graph node count (including isolated
    # nodes that never enter the tension/compression graphs).  Stored by
    # create_PKL_H2; None for pickles created before the key existed.
    n_nodes_total = DATA_G.get('n_nodes_total')

    tasks = [
        (i, DATA_G['tension'][i], DATA_G['compression'][i], algorithm, n_nodes_total)
        for i in range(total_steps)
    ]

    # ---- Execute -------------------------------------------------------
    global_ef_t = [None] * total_steps
    global_ef_c = [None] * total_steps
    global_ef_t_allnodes = [None] * total_steps
    global_ef_c_allnodes = [None] * total_steps

    # Cannot spawn child processes from a daemon process (e.g. inside Pool workers)
    if multiprocessing.current_process().daemon:
        n_workers = 1

    if n_workers == 1:
        for task in tasks:
            idx, eff_t, eff_c, eff_t_all, eff_c_all = _process_timestep_exact(task)
            global_ef_t[idx] = eff_t
            global_ef_c[idx] = eff_c
            global_ef_t_allnodes[idx] = eff_t_all
            global_ef_c_allnodes[idx] = eff_c_all
            print(f'  Timestep {idx + 1}/{total_steps} done')
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            for idx, eff_t, eff_c, eff_t_all, eff_c_all in executor.map(
                _process_timestep_exact, tasks, chunksize=max(1, total_steps // (n_workers * 4))
            ):
                global_ef_t[idx] = eff_t
                global_ef_c[idx] = eff_c
                global_ef_t_allnodes[idx] = eff_t_all
                global_ef_c_allnodes[idx] = eff_c_all
                print(f'  Timestep {idx + 1}/{total_steps} done')

    pkl_G2 = {
        't': DATA_G['t'],
        'global_ef_t': global_ef_t,
        'global_ef_c': global_ef_c,
        # Same pairwise sums, but normalised by n_nodes_total*(n_nodes_total-1)
        # (all overlay nodes, isolated ones included).  NaN when the input
        # pickle predates the 'n_nodes_total' key.
        'global_ef_t_allnodes': global_ef_t_allnodes,
        'global_ef_c_allnodes': global_ef_c_allnodes,
        'n_nodes_total': n_nodes_total,
        **_propagate_source_metadata(DATA_G),
    }

    return pkl_G2


def dataD_generator(data_B, data_C2, normal_computation = 'per_timestep'):
    """
    Docstring for dataD_generator
    
    :param data_B
    :param data_C2
    :param normal_computation: It can be computed at timestep 0 ('initial') or per timestep ('per_timestep')
    """
    from A001_functions.fem_stress_interpolation import (
        _get_stress_at_integration_points,
        _interpolate_at_natural_coords,
    )

    s12_key = 'S12' if 'S12' in data_B else 'S21'

    TENS_DICT = {}
    DATA_D = {}
    n_timesteps = len(data_C2['nodes_time'])
    n_adjacency = len(data_C2['adjacency'])
    for ti_0 in range(n_timesteps):
        ti_key = str(ti_0 + 1)
        TENS = []
        for num_ad in range(1, n_adjacency + 1):

            n1, n2 = data_C2['adjacency'][str(num_ad)]

            # The normals are computed at each timestep
            if normal_computation == 'per_timestep':
                normal = data_C2['normals'][ti_0][str(num_ad)]
            elif normal_computation == 'initial':
                normal = data_C2['normals'][0][str(num_ad)]

            # Interpolate stress at each element's barycenter using
            # FEM shape functions.  For a quad the barycenter maps to
            # (xi=0, eta=0) in natural coordinates, which gives the
            # equal-weight average of the 4 Gauss-point values.
            # For a triangle the stress is constant (single IP).
            def _stress_at_barycenter(elem_key):
                n_en = len(data_C2['elements'][elem_key])
                s11_ip, s22_ip, s12_ip = _get_stress_at_integration_points(
                    data_B, elem_key, ti_key, n_element_nodes=n_en
                )
                if n_en == 3:
                    return float(s11_ip[0]), float(s22_ip[0]), float(s12_ip[0])
                else:
                    # Quad barycenter ↦ (xi=0, eta=0) in natural coords
                    return (
                        _interpolate_at_natural_coords(0.0, 0.0, s11_ip),
                        _interpolate_at_natural_coords(0.0, 0.0, s22_ip),
                        _interpolate_at_natural_coords(0.0, 0.0, s12_ip),
                    )

            s11_1, s22_1, s12_1 = _stress_at_barycenter(str(n1))
            s11_2, s22_2, s12_2 = _stress_at_barycenter(str(n2))

            SE1 = np.array([
                [s11_1, s12_1],
                [s12_1, s22_1]
            ])

            SE2 = np.array([
                [s11_2, s12_2],
                [s12_2, s22_2]
            ])


            result_1 = (SE1.dot(normal)).dot(normal)
            result_2 = (SE2.dot(normal)).dot(normal)



            TENS.append((result_1, result_2))

        TENS_DICT[ti_key] = TENS
    DATA_D['stresses'] = TENS_DICT
    DATA_D['t'] = data_B['t']
    return DATA_D



def dataA2_generator(DATA):
    DATA_OUT = {}
    for C1 in ['RF1', 'RF2', 'RF3', 'RM1', 'RM2', 'RM3']:
        if C1 in DATA:
            DATA_OUT[C1] = {}
            for C2 in DATA[C1].keys():
                DATA_OUT[C1][C2] = []
                for C3 in DATA[C1][C2].keys():
                    if isinstance(DATA[C1][C2][C3], list):
                        if len(DATA_OUT[C1][C2]) == 0:
                            DATA_OUT[C1][C2] = DATA[C1][C2][C3]
                        else:
                            DATA_OUT[C1][C2] = [sum(x) for x in zip(DATA_OUT[C1][C2], DATA[C1][C2][C3])]


    for C1 in ['U1', 'U2', 'U3', 'UR1', 'UR2', 'UR3']:
        if C1 in DATA:
            DATA_OUT[C1] = {}
            for C2 in DATA[C1].keys():
                DATA_OUT[C1][C2] = []
                for C3 in DATA[C1][C2].keys():
                    if isinstance(DATA[C1][C2][C3], list):
                        if len(DATA_OUT[C1][C2]) == 0:
                            DATA_OUT[C1][C2] = DATA[C1][C2][C3]
                        else:
                            DATA_OUT[C1][C2] = [np.mean(x) for x in zip(DATA_OUT[C1][C2], DATA[C1][C2][C3])]

    # Invert sign for specific keys if they exist and are lists
    for key1, key2 in [
        ('U2', 'Y-POSITIVE'),
        ('U2', 'Y-NEGATIVE'),
        ('RF2', 'Y-POSITIVE'),
        ('RF2', 'Y-NEGATIVE')
    ]:
        if key1 in DATA_OUT and key2 in DATA_OUT[key1]:
            if isinstance(DATA_OUT[key1][key2], list):
                DATA_OUT[key1][key2] = [-x for x in DATA_OUT[key1][key2]]


    DATA_OUT['t'] = DATA['t']
    return DATA_OUT



def dataC2_generator(DATA_C, sim_num=None):
    with open(f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json', 'r') as json_file:
        json_file = json.load(json_file)
    path = json_file['input_name']

    mesh_file = path

    if not mesh_file.endswith('.mesh.json'):
        raise ValueError("Unsupported mesh file format. Supported format is .mesh.json")
    _, elements = read_mesh_json(mesh_file)
    elements = [[x + 1 for x in element] for element in elements]  # Convert to 1-based indexing

    nodes_time = []
    for ti in range(len(DATA_C['COOR1']['1'])):
        nodes_ti = []
        for idx in range(len(DATA_C['COOR1'])):
            if 'COOR3' in DATA_C:
                nodes_ti.append((DATA_C['COOR1'][str(idx+1)][ti], DATA_C['COOR2'][str(idx+1)][ti], DATA_C['COOR3'][str(idx+1)][ti]))
            else:
                nodes_ti.append((DATA_C['COOR1'][str(idx+1)][ti], DATA_C['COOR2'][str(idx+1)][ti]))
        nodes_time.append(nodes_ti)

    dataC2 = {}

    adjacency = find_element_adjacency(elements)

    baricenters = []
    for i in range(len(nodes_time)):
        bary = find_barycenters(nodes_time[i], elements)
        baricenters.append(bary)

    # nodes_time: list (0-indexed by ti), each element is a dict {str(node_id): coords}
    dataC2['nodes_time'] = [
        {str(j + 1): coord for j, coord in enumerate(nt)}
        for nt in nodes_time
    ]
    # elements, adjacency, baricenters: dicts with 1-based string keys
    dataC2['elements'] = {str(i + 1): v for i, v in enumerate(elements)}
    dataC2['adjacency'] = {str(i + 1): v for i, v in enumerate(adjacency)}
    dataC2['baricenters'] = {str(i + 1): v for i, v in enumerate(baricenters)}
    # Truncate t to match the actual number of computed timesteps
    # (DATA_C['t'] may list more target times than the solver produced).
    dataC2['t'] = DATA_C['t'][:len(nodes_time)]

    # -------------------
    # COMPUTE NORMALS
    # -------------------
    # normals: list (0-indexed by ti), each element is a dict {str(adj_id): unit_vec}
    normals = []
    n_timesteps = len(dataC2['baricenters'])

    for ti_0 in range(n_timesteps):
        ti_key = str(ti_0 + 1)
        bary = np.asarray(dataC2['baricenters'][ti_key])
        dim = bary.shape[1]
        normals_ti = {}

        idx = 0
        for adj_key in sorted(dataC2['adjacency'].keys(), key=int):
            a, b = dataC2['adjacency'][adj_key]
            a0 = a - 1
            b0 = b - 1

            pa = bary[a0]
            pb = bary[b0]

            v = pb - pa
            norm = np.linalg.norm(v)
            if norm == 0:
                unit = np.zeros(dim)
            else:
                unit = v / norm

            normals_ti[str(idx+1)] = unit
            idx += 1

        normals.append(normals_ti)

    dataC2['normals'] = normals

    return dataC2




def create_PKL_T1(
    DATA_C2: dict,
    triangulation_file: str,
    sim_num: int,
    output_path: str = None,
) -> dict:
    """
    Create the PKL_T1 dictionary for triangulation mesh data.

    Parameters
    ----------
    DATA_C2 : dict
        Mesh data with keys 'nodes_time', 'elements', 't'.
        - nodes_time[ti][str(node_id)] -> (x, y)  (0-based ti, 1-based string node_id)
        - elements[str(elem_id)] -> list of 1-based node ids (string key)
        - t -> list of timestep floats
    triangulation_file : str
        Path to triangulation file (as produced by A001_functions/Triangulation_creator.py).
        Format (values may be comma- or space-separated):
            N_nodes
            x  y  ID      (one row per node)
            ...
            N_elements
            n1  n2  n3    (one row per triangle, 0-based node indices)
            ...
    sim_num : int
        Simulation number. Used to load scale factors from JSON and build
        the default output path.
    output_path : str, optional
        If given, the resulting dict is pickled here.
        Defaults to 'I001_Results/DATA_PICK_{sim_num:03d}_T1.pkl'.

    Returns
    -------
    dict  PKL_T1
        PKL_T1['t']                              -> list of timesteps
        PKL_T1['nodes'][ti][nid]                 -> (x_def, y_def, ID)
        PKL_T1['elements'][element_id]           -> [n1, n2, n3]  (0-based)
        PKL_T1['elements_area'][element_id][ti]  -> area at timestep ti
        PKL_T1['elements_area_normalized'][element_id][ti]
                                                 -> area(ti) / area(undeformed)
        PKL_T1['node_matches'][nid]              -> FEM mesh node id used by
                                                     triangulation node nid
    """

    # ------------------------------------------------------------------
    # 0.  Load scale factors from JSON
    # ------------------------------------------------------------------
    json_path = f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json'
    with open(json_path, 'r') as fj:
        sim_json = json.load(fj)

    scale_x      = sim_json['scale_x']
    scale_y      = sim_json['scale_y']
    mesh_file_path = sim_json['input_name']

    print(f"  Scale factors: scale_x={scale_x}, scale_y={scale_y}")
    print(f"  Mesh file: {mesh_file_path}")

    # ------------------------------------------------------------------
    # 1.  Read triangulation file
    # ------------------------------------------------------------------
    tri_nodes_raw = []     # list of (x, y, ID) - unscaled
    tri_elements_raw = []  # list of [n1, n2, n3] - 0-based

    with open(triangulation_file, 'r') as ft:
        n_tri_nodes = int(ft.readline().strip())
        for _ in range(n_tri_nodes):
            parts = ft.readline().strip().replace(',', ' ').split()
            tri_nodes_raw.append((float(parts[0]), float(parts[1]), int(parts[2])))
        n_tri_elems = int(ft.readline().strip())
        for _ in range(n_tri_elems):
            parts = ft.readline().strip().replace(',', ' ').split()
            tri_elements_raw.append([int(parts[0]), int(parts[1]), int(parts[2])])

    tri_nodes_scaled = [(x * scale_x, y * scale_y, ID)
                        for x, y, ID in tri_nodes_raw]
    tri_node_ids = [ID for _, _, ID in tri_nodes_scaled]

    print(f"  Triangulation: {n_tri_nodes} nodes, {n_tri_elems} elements")

    # ------------------------------------------------------------------
    # 2.  Build the undeformed FEM node list and snap triangulation nodes
    # ------------------------------------------------------------------
    mesh_nodes_raw, _ = read_mesh_json(mesh_file_path)
    n_fe_nodes = len(DATA_C2['nodes_time'][0])
    nodes_undeformed = [(float(x) * scale_x, float(y) * scale_y)
                        for x, y, _ in mesh_nodes_raw]
    if len(nodes_undeformed) != n_fe_nodes:
        raise ValueError(
            f"Mesh file has {len(nodes_undeformed)} nodes but DATA_C2 has "
            f"{n_fe_nodes}"
        )

    nodes_undef_arr = np.array(nodes_undeformed, dtype=float)
    tri_xy_scaled = np.array([(x, y) for x, y, _ in tri_nodes_scaled], dtype=float)
    snap_distances, matched_indices = cKDTree(nodes_undef_arr).query(
        tri_xy_scaled, k=1
    )
    if np.isscalar(matched_indices):
        matched_indices = np.array([matched_indices])
        snap_distances = np.array([snap_distances])

    matched_mesh_node_ids = [int(idx) + 1 for idx in matched_indices]
    node_matches = {
        tri_node_id: mesh_node_id
        for tri_node_id, mesh_node_id in enumerate(matched_mesh_node_ids, start=1)
    }

    mean_snap = float(np.mean(snap_distances)) if n_tri_nodes else 0.0
    max_snap = float(np.max(snap_distances)) if n_tri_nodes else 0.0
    unique_matches = len(set(matched_mesh_node_ids))
    print(f"  Node snapping: {n_tri_nodes} triangulation nodes matched to "
          f"{unique_matches} FEM nodes")
    print(f"  Snap distance: mean={mean_snap:.6g}, max={max_snap:.6g}")

    # ------------------------------------------------------------------
    # 3.  Area helper
    # ------------------------------------------------------------------
    def _tri_area(p1, p2, p3) -> float:
        return 0.5 * abs(
            (p2[0] - p1[0]) * (p3[1] - p1[1]) -
            (p3[0] - p1[0]) * (p2[1] - p1[1])
        )

    # original_areas are computed from ti=0 deformed positions (see loop below)
    original_areas = {}

    # ------------------------------------------------------------------
    # 4.  Main time-loop: copy matched FEM node coordinates, then compute
    #     triangulation element areas.
    # ------------------------------------------------------------------
    n_timesteps = len(DATA_C2['nodes_time'])

    # Initialise output containers
    nodes_out              = [{} for _ in range(n_timesteps)]
    elements_area          = {eid + 1: {} for eid in range(n_tri_elems)}
    elements_area_norm     = {eid + 1: {} for eid in range(n_tri_elems)}

    for ti in range(n_timesteps):
        # --- 4a. snapped triangulation node positions ---
        ti_nodes = DATA_C2['nodes_time'][ti]
        deformed_tri = np.empty((n_tri_nodes, 2), dtype=float)

        for nidx in range(n_tri_nodes):
            node_ID = tri_node_ids[nidx]
            mesh_node_id = matched_mesh_node_ids[nidx]
            mesh_node_key = str(mesh_node_id)
            if mesh_node_key not in ti_nodes:
                raise KeyError(
                    f"DATA_C2['nodes_time'][{ti}] has no coordinates for "
                    f"snapped FEM node {mesh_node_key}"
                )
            x_def, y_def = ti_nodes[mesh_node_key]

            deformed_tri[nidx] = (x_def, y_def)
            # 1-based node id in output
            nodes_out[ti][nidx + 1] = (float(x_def), float(y_def), node_ID)

        # --- 4b. element areas ---
        for elem_id_0, (n1, n2, n3) in enumerate(tri_elements_raw):
            eid = elem_id_0 + 1
            area = _tri_area(
                deformed_tri[n1],
                deformed_tri[n2],
                deformed_tri[n3],
            )
            elements_area[eid][ti] = area
            if ti == 0:
                original_areas[eid] = area
            orig = original_areas.get(eid, area)
            elements_area_norm[eid][ti] = area / orig if orig > 1e-30 else 0.0

        print(f"  Timestep {ti + 1}/{n_timesteps} done")

    # ------------------------------------------------------------------
    # 5.  Assemble PKL_T1
    # ------------------------------------------------------------------
    # elements dict: 1-based element_id -> [n1, n2, n3] using 0-based node indices
    elements_out = {eid + 1: tri_elements_raw[eid]
                    for eid in range(n_tri_elems)}

    PKL_T1 = {
        **_source_metadata(triangulation_file),
        't'                        : DATA_C2['t'],
        'nodes'                    : nodes_out,
        'elements'                 : elements_out,
        'elements_area'            : elements_area,
        'elements_area_normalized' : elements_area_norm,
        'node_matches'             : node_matches,
    }

    # ------------------------------------------------------------------
    # 6.  Save to pickle
    # ------------------------------------------------------------------
    if output_path is None:
        output_path = f'I001_Results/DATA_PICK_{sim_num:03d}_T1.pkl'

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'wb') as fp:
        pickle.dump(PKL_T1, fp)
    print(f"PKL_T1 saved to '{output_path}'")

    return PKL_T1


# ---------------------------------------------------------------------------
# T2 pickle: statistical summary of T1 triangulation mesh areas
# ---------------------------------------------------------------------------

def create_PKL_T2(DATA_T1: dict, output_path: str = None, sim_num: int = None,
                  w_param_sets: list = None) -> dict:
    """
    Compute statistical summary of element areas from a PKL_T1 dictionary.

    Parameters
    ----------
    DATA_T1 : dict
        PKL_T1 dictionary with keys:
          't'                        -> list[float]  len=N_t
          'nodes'                    -> list[dict]  nodes[ti][nid] = (x, y, ID)
          'elements'                 -> dict { elem_id (int, 1-based) -> [n1, n2, n3] }
          'elements_area'            -> dict { elem_id (int, 1-based) ->
                                              dict { ti (int, 0-based) -> float } }
          'elements_area_normalized' -> same structure, normalized values
    output_path : str, optional
        If given, the result is pickled here.
    sim_num : int, optional
        Used to build a default output_path when output_path is None.
    w_param_sets : list of tuple, optional
        List of (K, G, m, n) parameter tuples for the strain energy w.
        Defaults to [(1, 1, 1, 1)].

    Returns
    -------
    dict  PKL_T2
        't'              -> list[float]
        'time_variant'   -> area/normalized_areas statistics per timestep
        'time_invariant' -> area/normalized_areas statistics per element
        'general_information' -> global scalars
        'eta'            -> list[float]  mesh regularity index per timestep
        'edge_sizes'     -> dict { elem_id -> { ti -> [l1, l2, l3] } }
                           Lengths of edges n1-n2, n2-n3, n3-n1.
        'q'              -> dict { elem_id -> { ti -> float } }
                           Mesh quality: 4*sqrt(3)*A / (l1^2+l2^2+l3^2).
        'epsilon'        -> dict { elem_id -> { ti -> [eps1, eps2, eps3] } }
                           Edge strains: epsi(ti) = (li(ti) - li(0)) / li(0).
        'F'              -> dict { elem_id -> { ti -> [[F11,F12],[F21,F22]] } }
                           2x2 deformation gradient dx/dX.
        'shear'          -> dict { elem_id -> { ti -> float } }
                           1/2 * trace(F^T F).
        'gle'            -> dict { elem_id -> { ti -> float } }
                           Green-Lagrange strain energy: trace(E),
                           where E = 1/2 * (F^T F - I).
        'shear_mean'     -> list[float]  len=N_t
                           Mean of shear across all elements at each timestep.
        'gle_mean'       -> list[float]  len=N_t
                           Mean of GLE across all elements at each timestep.
        'edi'            -> dict { elem_id -> { ti -> float } }
                           Edge deformation index:
                           1/3 * (|l1t/l10| + |l2t/l20| + |l3t/l30|).
        'edi_mean'       -> list[float]  len=N_t
                           Mean of EDI across all elements at each timestep.
        'J'              -> dict { elem_id -> { ti -> float } }
                           Jacobian determinant J = det(F).
        'C'              -> dict { elem_id -> { ti -> [[...],[...]] } }
                           Isochoric RIGHT Cauchy-Green tensor
                           C = J^(-2/3) * F^T @ F  (2x2 matrix).
        'w'              -> dict { (K, G, m, n) -> { elem_id -> { ti -> float } } }
                           Neo-Hookean-like strain energy density.
                           w = K/4*(1/m^2*(J^m-1)^2 + 1/m^2*(J^(-m)-1)^2)
                             + G/4*(1/n^2*||C^n-I||_F^2 + 1/n^2*||C^(-n)-I||_F^2)
                           Keyed by parameter tuple (K, G, m, n).
                           Defaults to (K=1, G=1, m=1, n=1).
        'w_mean'         -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Mean of w across all elements at each timestep,
                           for each parameter set.
        'w_std'          -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Standard deviation of w across all elements at each
                           timestep.
        'w_cv'           -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Coefficient of variation of w:
                           w_std / (abs(w_mean) + eps).
        'w_std_area_weighted'
                         -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Reference-area-weighted standard deviation of w,
                           using A_e(t=0) as weights.
        'w_cv_area_weighted'
                         -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Reference-area-weighted coefficient of variation:
                           w_std_area_weighted / (abs(W/sum_e A_e(t=0)) + eps).
        'W'              -> dict { (K, G, m, n) -> list[float]  len=N_t }
                           Area-weighted sum: W(ti) = sum_e( w[e,ti] * A_e(t=0) ),
                           for each parameter set.
    """
    t = DATA_T1['t']
    n_t = len(t)
    elem_ids = sorted(DATA_T1['elements'].keys())   # list of int (1-based)
    n_elems  = len(elem_ids)

    # ------------------------------------------------------------------
    # 1.  Build flat arrays for easier vectorised operations
    #     areas_mat[ei, ti]  and  norm_mat[ei, ti]
    # ------------------------------------------------------------------
    areas_mat = np.zeros((n_elems, n_t), dtype=float)
    norm_mat  = np.zeros((n_elems, n_t), dtype=float)

    for ei, eid in enumerate(elem_ids):
        ea   = DATA_T1['elements_area'][eid]
        ean  = DATA_T1['elements_area_normalized'][eid]
        for ti in range(n_t):
            areas_mat[ei, ti] = ea[ti]
            norm_mat[ei, ti]  = ean[ti]

    # ------------------------------------------------------------------
    # 2.  time_variant statistics  (one scalar per timestep)
    # ------------------------------------------------------------------
    tv_areas = {
        'min' : areas_mat.min(axis=0).tolist(),
        'max' : areas_mat.max(axis=0).tolist(),
        'mean': areas_mat.mean(axis=0).tolist(),
        'std' : areas_mat.std(axis=0).tolist(),
    }

    tv_norm = {
        'min' : norm_mat.min(axis=0).tolist(),
        'max' : norm_mat.max(axis=0).tolist(),
        'mean': norm_mat.mean(axis=0).tolist(),
        'std' : norm_mat.std(axis=0).tolist(),
    }

    # ------------------------------------------------------------------
    # 3.  time_invariant statistics  (one dict entry per element,
    #     aggregated across ALL timesteps)
    # ------------------------------------------------------------------
    ti_areas = {}
    ti_norm  = {}
    for ei, eid in enumerate(elem_ids):
        row      = areas_mat[ei]
        row_norm = norm_mat[ei]
        ti_areas[eid] = {
            'min' : float(row.min()),
            'max' : float(row.max()),
            'mean': float(row.mean()),
            'std' : float(row.std()),
        }
        ti_norm[eid] = {
            'min' : float(row_norm.min()),
            'max' : float(row_norm.max()),
            'mean': float(row_norm.mean()),
            'std' : float(row_norm.std()),
        }

    # ------------------------------------------------------------------
    # 4.  general_information
    # ------------------------------------------------------------------
    general_information = {
        'n_elements'        : n_elems,
        'area_global_min'   : float(areas_mat.min()),
        'area_global_max'   : float(areas_mat.max()),
        'norm_area_global_min': float(norm_mat.min()),
        'norm_area_global_max': float(norm_mat.max()),
    }

    # ------------------------------------------------------------------
    # 5.  eta at each timestep
    #     eta(ti) = 1 - std(normalised_area at ti) / std_i
    #     std_i   = (r/2) * sqrt(it / (it - 1))
    #     where r=1 and it = n_elems
    # ------------------------------------------------------------------
    r  = 1.0
    it = n_elems
    std_i = (r / 2.0) * np.sqrt(it / (it - 1))

    eta = [1.0 - (tv_norm['std'][ti] / std_i) for ti in range(n_t)]

    # ------------------------------------------------------------------
    # 6.  edge_sizes, q, epsilon, F (deformation gradient), SHEAR, GLE, EDI
    # ------------------------------------------------------------------
    edge_sizes = {}
    q          = {}
    epsilon    = {}
    F_grad     = {}
    shear      = {}
    gle        = {}
    edi        = {}
    J_det      = {}
    C_iso      = {}

    # Parameter sets for the strain energy w: (K, G, m, n)
    if w_param_sets is None:
        w_param_sets = [(1, 1, 1, 1), (1, 1, 2, 2)]
    _w_param_sets = w_param_sets
    w  = {params: {} for params in _w_param_sets}
    I2 = np.eye(2)  # 2x2 identity used in w computation

    for ei, eid in enumerate(elem_ids):
        n1, n2, n3 = DATA_T1['elements'][eid]   # 0-based node indices

        # Reference positions (t=0)
        p1_0 = np.array(DATA_T1['nodes'][0][n1 + 1][:2], dtype=float)
        p2_0 = np.array(DATA_T1['nodes'][0][n2 + 1][:2], dtype=float)
        p3_0 = np.array(DATA_T1['nodes'][0][n3 + 1][:2], dtype=float)

        l1_0 = float(np.linalg.norm(p2_0 - p1_0))
        l2_0 = float(np.linalg.norm(p3_0 - p2_0))
        l3_0 = float(np.linalg.norm(p1_0 - p3_0))

        # Reference edge vectors from node 1 (columns of the reference deformation basis)
        DX_mat = np.column_stack([p2_0 - p1_0, p3_0 - p1_0])  # (2, 2)
        try:
            DX_inv = np.linalg.inv(DX_mat)
        except np.linalg.LinAlgError:
            DX_inv = np.linalg.pinv(DX_mat)

        edge_sizes[eid] = {}
        q[eid]          = {}
        epsilon[eid]    = {}
        F_grad[eid]     = {}
        shear[eid]      = {}
        gle[eid]        = {}
        edi[eid]        = {}
        J_det[eid]      = {}
        C_iso[eid]      = {}
        for params in _w_param_sets:
            w[params][eid] = {}

        for ti in range(n_t):
            p1 = np.array(DATA_T1['nodes'][ti][n1 + 1][:2], dtype=float)
            p2 = np.array(DATA_T1['nodes'][ti][n2 + 1][:2], dtype=float)
            p3 = np.array(DATA_T1['nodes'][ti][n3 + 1][:2], dtype=float)

            l1 = float(np.linalg.norm(p2 - p1))
            l2 = float(np.linalg.norm(p3 - p2))
            l3 = float(np.linalg.norm(p1 - p3))

            edge_sizes[eid][ti] = [l1, l2, l3]

            sum_l2 = l1**2 + l2**2 + l3**2
            area   = areas_mat[ei, ti]
            q[eid][ti] = (4.0 * np.sqrt(3.0) * area / sum_l2) if sum_l2 > 1e-30 else 0.0

            epsilon[eid][ti] = [
                (l1 - l1_0) / l1_0 if l1_0 > 1e-30 else 0.0,
                (l2 - l2_0) / l2_0 if l2_0 > 1e-30 else 0.0,
                (l3 - l3_0) / l3_0 if l3_0 > 1e-30 else 0.0,
            ]

            # Deformation gradient: F = [x2-x1 | x3-x1] @ [X2-X1 | X3-X1]^{-1}
            dx_mat = np.column_stack([p2 - p1, p3 - p1])  # (2, 2)
            F_mat  = dx_mat @ DX_inv
            F_grad[eid][ti] = F_mat.tolist()

            # SHEAR = 1/2 * trace(F^T F)  (half-trace of the right Cauchy-Green tensor)
            shear[eid][ti] = 0.5 * float(np.trace(F_mat.T @ F_mat))

            # GLE = trace(E), E = 1/2 * (F^T F - I)  (Green-Lagrange strain energy)
            E_mat = 0.5 * (F_mat.T @ F_mat - np.eye(2))
            gle[eid][ti] = float(np.trace(E_mat))

            # EDI = 1/3 * (|l1t/l10| + |l2t/l20| + |l3t/l30|)
            edi[eid][ti] = (1.0 / 3.0) * (
                (abs(l1 / l1_0) if l1_0 > 1e-30 else 0.0) +
                (abs(l2 / l2_0) if l2_0 > 1e-30 else 0.0) +
                (abs(l3 / l3_0) if l3_0 > 1e-30 else 0.0)
            )

            # J = det(F)  (signed: negative means element inversion)
            J = float(np.linalg.det(F_mat))
            J_det[eid][ti] = J

            # For C and w we need J > 0 (physical requirement).
            # Use abs(J) so that inverted elements don't produce complex results;
            # the signed value in J_det is still available for inversion detection.
            J_pos = abs(J)
            if J_pos < 1e-30:
                J_pos = 1e-30  # guard against division by zero

            # C = J^(-2/3) * F^T @ F  (isochoric right Cauchy-Green tensor)
            C_mat = (J_pos ** (-2.0 / 3.0)) * (F_mat.T @ F_mat)
            C_iso[eid][ti] = C_mat.tolist()

            # Strain energy w for each parameter set (K, G, m, n)
            for (K, G, m, n) in _w_param_sets:
                # Volumetric part  (uses J_pos = |J| to stay real-valued)
                vol = (K / 4.0) * (
                    (1.0 / m**2) * (J_pos**m - 1.0)**2
                    + (1.0 / m**2) * (J_pos**(-m) - 1.0)**2
                )
                # Isochoric part: matrix powers of C
                C_n  = fractional_matrix_power(C_mat, n)
                C_ni = fractional_matrix_power(C_mat, -n)
                iso = (G / 4.0) * (
                    (1.0 / n**2) * np.linalg.norm(C_n  - I2, 'fro')**2
                    + (1.0 / n**2) * np.linalg.norm(C_ni - I2, 'fro')**2
                )
                w[(K, G, m, n)][eid][ti] = float(vol + iso)

    # ------------------------------------------------------------------
    # 7.  Assemble output dictionary
    # ------------------------------------------------------------------
    # Pre-compute per-timestep means of shear and GLE (shape: n_t)
    shear_mean = [
        float(np.mean([shear[eid][ti] for eid in elem_ids]))
        for ti in range(n_t)
    ]
    gle_mean = [
        float(np.mean([gle[eid][ti] for eid in elem_ids]))
        for ti in range(n_t)
    ]
    edi_mean = [
        float(np.mean([edi[eid][ti] for eid in elem_ids]))
        for ti in range(n_t)
    ]

    w_mean = {
        params: [
            float(np.mean([w[params][eid][ti] for eid in elem_ids]))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    w_std = {
        params: [
            float(np.std([w[params][eid][ti] for eid in elem_ids]))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    _cv_eps = 1e-30
    w_cv = {
        params: [
            float(w_std[params][ti] / (abs(w_mean[params][ti]) + _cv_eps))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }

    # W = sum_e( w[e, ti] * area_e(t=0) )  for each timestep
    _area0 = {eid: float(DATA_T1['elements_area'][eid][0]) for eid in elem_ids}
    _area0_sum = float(sum(_area0.values()))
    if _area0_sum <= 1e-30:
        _area0_sum = 1e-30
    W = {
        params: [
            float(sum(w[params][eid][ti] * _area0[eid] for eid in elem_ids))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    _w_area_mean = {
        params: [
            float(W[params][ti] / _area0_sum)
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    w_std_area_weighted = {
        params: [
            float(np.sqrt(
                sum(
                    _area0[eid] * (w[params][eid][ti] - _w_area_mean[params][ti])**2
                    for eid in elem_ids
                ) / _area0_sum
            ))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    w_cv_area_weighted = {
        params: [
            float(
                w_std_area_weighted[params][ti]
                / (abs(_w_area_mean[params][ti]) + _cv_eps)
            )
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }

    PKL_T2 = {
        **_propagate_source_metadata(DATA_T1),
        't': t,
        'time_variant': {
            'areas'           : tv_areas,
            'normalized_areas': tv_norm,
        },
        'time_invariant': {
            'areas'           : ti_areas,
            'normalized_areas': ti_norm,
        },
        'general_information': general_information,
        'eta'        : eta,
        'edge_sizes' : edge_sizes,
        'q'          : q,
        'epsilon'    : epsilon,
        'F'          : F_grad,
        'shear'      : shear,
        'gle'        : gle,
        'shear_mean' : shear_mean,
        'gle_mean'   : gle_mean,
        'edi'        : edi,
        'edi_mean'   : edi_mean,
        'J'          : J_det,
        'C'          : C_iso,
        'w'          : w,
        'w_mean'     : w_mean,
        'w_std'      : w_std,
        'w_cv'       : w_cv,
        'w_std_area_weighted': w_std_area_weighted,
        'w_cv_area_weighted' : w_cv_area_weighted,
        'W'          : W,
    }

    # ------------------------------------------------------------------
    # 8.  Save to pickle
    # ------------------------------------------------------------------
    if output_path is None and sim_num is not None:
        output_path = f'I001_Results/DATA_PICK_{sim_num:03d}_T2.pkl'

    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as fp:
            pickle.dump(PKL_T2, fp)
        print(f"PKL_T2 saved to '{output_path}'")

    return PKL_T2


# ---------------------------------------------------------------------------
# Q1 pickle: quad mesh data (analogous to T1 but for 4-node quad elements)
# ---------------------------------------------------------------------------

def create_PKL_Q1(
    DATA_C2: dict,
    quadrangulation_file: str,
    sim_num: int,
    output_path: str = None,
) -> dict:
    """
    Create the PKL_Q1 dictionary for quadrangulation mesh data.

    Analogous to create_PKL_T1 but reads 4-node quad elements from a .quad file.

    Parameters
    ----------
    DATA_C2 : dict
        Mesh data with keys 'nodes_time', 'elements', 't'.
    quadrangulation_file : str
        Path to .quad file produced by quadrangulation_generator.
        Format: N_nodes / (x y ID per line) / N_elements / (n1 n2 n3 n4 per line).
    sim_num : int
        Simulation number.
    output_path : str, optional
        Defaults to 'I001_Results/DATA_PICK_{sim_num:03d}_Q1.pkl'.

    Returns
    -------
    dict  PKL_Q1
        Same key structure as PKL_T1, but elements have 4 node indices.
    """
    json_path = f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json'
    with open(json_path, 'r') as fj:
        sim_json = json.load(fj)

    scale_x        = sim_json['scale_x']
    scale_y        = sim_json['scale_y']
    mesh_file_path = sim_json['input_name']

    print(f"  Scale factors: scale_x={scale_x}, scale_y={scale_y}")
    print(f"  Mesh file: {mesh_file_path}")

    # 1. Read quadrangulation file
    quad_nodes_raw    = []   # (x, y, ID)
    quad_elements_raw = []   # [n1, n2, n3, n4] 0-based

    with open(quadrangulation_file, 'r') as fq:
        n_quad_nodes = int(fq.readline().strip())
        for _ in range(n_quad_nodes):
            parts = fq.readline().strip().replace(',', ' ').split()
            quad_nodes_raw.append((float(parts[0]), float(parts[1]), int(parts[2])))
        n_quad_elems = int(fq.readline().strip())
        for _ in range(n_quad_elems):
            parts = fq.readline().strip().replace(',', ' ').split()
            quad_elements_raw.append([int(parts[0]), int(parts[1]),
                                      int(parts[2]), int(parts[3])])

    quad_nodes_scaled = [(x * scale_x, y * scale_y, ID)
                         for x, y, ID in quad_nodes_raw]
    quad_node_ids = [ID for _, _, ID in quad_nodes_scaled]

    print(f"  Quadrangulation: {n_quad_nodes} nodes, {n_quad_elems} elements")

    # 2. Snap quad nodes to FEM mesh nodes
    mesh_nodes_raw, _ = read_mesh_json(mesh_file_path)
    n_fe_nodes = len(DATA_C2['nodes_time'][0])
    nodes_undeformed = [(float(x) * scale_x, float(y) * scale_y)
                        for x, y, _ in mesh_nodes_raw]
    if len(nodes_undeformed) != n_fe_nodes:
        raise ValueError(
            f"Mesh file has {len(nodes_undeformed)} nodes but DATA_C2 has {n_fe_nodes}"
        )

    nodes_undef_arr = np.array(nodes_undeformed, dtype=float)
    quad_xy_scaled  = np.array([(x, y) for x, y, _ in quad_nodes_scaled], dtype=float)
    snap_distances, matched_indices = cKDTree(nodes_undef_arr).query(quad_xy_scaled, k=1)
    if np.isscalar(matched_indices):
        matched_indices = np.array([matched_indices])
        snap_distances  = np.array([snap_distances])

    matched_mesh_node_ids = [int(idx) + 1 for idx in matched_indices]
    node_matches = {
        quad_node_id: mesh_node_id
        for quad_node_id, mesh_node_id in enumerate(matched_mesh_node_ids, start=1)
    }

    mean_snap    = float(np.mean(snap_distances)) if n_quad_nodes else 0.0
    max_snap     = float(np.max(snap_distances)) if n_quad_nodes else 0.0
    unique_match = len(set(matched_mesh_node_ids))
    print(f"  Node snapping: {n_quad_nodes} quad nodes matched to {unique_match} FEM nodes")
    print(f"  Snap distance: mean={mean_snap:.6g}, max={max_snap:.6g}")

    # 3. Area helpers (split quad into 2 triangles)
    def _tri_area(p1, p2, p3) -> float:
        return 0.5 * abs(
            (p2[0] - p1[0]) * (p3[1] - p1[1]) -
            (p3[0] - p1[0]) * (p2[1] - p1[1])
        )

    def _quad_area(p1, p2, p3, p4) -> float:
        return _tri_area(p1, p2, p3) + _tri_area(p1, p3, p4)

    original_areas = {}

    # 4. Main time-loop
    n_timesteps = len(DATA_C2['nodes_time'])

    nodes_out          = [{} for _ in range(n_timesteps)]
    elements_area      = {eid + 1: {} for eid in range(n_quad_elems)}
    elements_area_norm = {eid + 1: {} for eid in range(n_quad_elems)}

    for ti in range(n_timesteps):
        ti_nodes = DATA_C2['nodes_time'][ti]
        deformed_quad = np.empty((n_quad_nodes, 2), dtype=float)

        for nidx in range(n_quad_nodes):
            node_ID      = quad_node_ids[nidx]
            mesh_node_id = matched_mesh_node_ids[nidx]
            mesh_key     = str(mesh_node_id)
            if mesh_key not in ti_nodes:
                raise KeyError(
                    f"DATA_C2['nodes_time'][{ti}] missing FEM node {mesh_key}"
                )
            x_def, y_def = ti_nodes[mesh_key]
            deformed_quad[nidx] = (x_def, y_def)
            nodes_out[ti][nidx + 1] = (float(x_def), float(y_def), node_ID)

        for elem_id_0, (n1, n2, n3, n4) in enumerate(quad_elements_raw):
            eid  = elem_id_0 + 1
            area = _quad_area(
                deformed_quad[n1], deformed_quad[n2],
                deformed_quad[n3], deformed_quad[n4],
            )
            elements_area[eid][ti] = area
            if ti == 0:
                original_areas[eid] = area
            orig = original_areas.get(eid, area)
            elements_area_norm[eid][ti] = area / orig if orig > 1e-30 else 0.0

        print(f"  Timestep {ti + 1}/{n_timesteps} done")

    # 5. Assemble PKL_Q1
    elements_out = {eid + 1: quad_elements_raw[eid] for eid in range(n_quad_elems)}

    PKL_Q1 = {
        **_source_metadata(quadrangulation_file),
        't'                        : DATA_C2['t'],
        'nodes'                    : nodes_out,
        'elements'                 : elements_out,
        'elements_area'            : elements_area,
        'elements_area_normalized' : elements_area_norm,
        'node_matches'             : node_matches,
    }

    # 6. Save
    if output_path is None:
        output_path = f'I001_Results/DATA_PICK_{sim_num:03d}_Q1.pkl'

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'wb') as fp:
        pickle.dump(PKL_Q1, fp)
    print(f"PKL_Q1 saved to '{output_path}'")

    return PKL_Q1


# ---------------------------------------------------------------------------
# Q2 pickle: statistical summary of Q1 quad mesh (analogous to T2)
# ---------------------------------------------------------------------------

def create_PKL_Q2(DATA_Q1: dict, output_path: str = None, sim_num: int = None,
                  w_param_sets: list = None) -> dict:
    """
    Compute statistical summary of element data from a PKL_Q1 dictionary.

    Analogous to create_PKL_T2 for 4-node quad elements.
    Deformation gradient F is computed via bilinear shape functions at the
    element centroid (ξ=0, η=0).

    Parameters
    ----------
    DATA_Q1 : dict
        PKL_Q1 dictionary (same structure as PKL_T1 but 4-node elements).
    output_path : str, optional
        Defaults to 'I001_Results/DATA_PICK_{sim_num:03d}_Q2.pkl'.
    sim_num : int, optional
        Used to build a default output_path when output_path is None.
    w_param_sets : list of tuple, optional
        List of (K, G, m, n) parameter tuples for the strain energy w.
        Defaults to [(1, 1, 1, 1)].

    Returns
    -------
    dict  PKL_Q2
        Same key structure as PKL_T2. 'edge_sizes' has 4 edges per element,
        'epsilon' has 4 edge strains, 'q' = 4*A/(l1^2+l2^2+l3^2+l4^2),
        'edi' = 1/4*(|l1/l10|+...).
    """
    t        = DATA_Q1['t']
    n_t      = len(t)
    elem_ids = sorted(DATA_Q1['elements'].keys())
    n_elems  = len(elem_ids)

    # 1. Flat area matrices
    areas_mat = np.zeros((n_elems, n_t), dtype=float)
    norm_mat  = np.zeros((n_elems, n_t), dtype=float)

    for ei, eid in enumerate(elem_ids):
        ea  = DATA_Q1['elements_area'][eid]
        ean = DATA_Q1['elements_area_normalized'][eid]
        for ti in range(n_t):
            areas_mat[ei, ti] = ea[ti]
            norm_mat[ei, ti]  = ean[ti]

    # 2. time_variant statistics
    tv_areas = {
        'min' : areas_mat.min(axis=0).tolist(),
        'max' : areas_mat.max(axis=0).tolist(),
        'mean': areas_mat.mean(axis=0).tolist(),
        'std' : areas_mat.std(axis=0).tolist(),
    }
    tv_norm = {
        'min' : norm_mat.min(axis=0).tolist(),
        'max' : norm_mat.max(axis=0).tolist(),
        'mean': norm_mat.mean(axis=0).tolist(),
        'std' : norm_mat.std(axis=0).tolist(),
    }

    # 3. time_invariant statistics
    ti_areas = {}
    ti_norm  = {}
    for ei, eid in enumerate(elem_ids):
        row      = areas_mat[ei]
        row_norm = norm_mat[ei]
        ti_areas[eid] = {
            'min' : float(row.min()),  'max' : float(row.max()),
            'mean': float(row.mean()), 'std' : float(row.std()),
        }
        ti_norm[eid] = {
            'min' : float(row_norm.min()),  'max' : float(row_norm.max()),
            'mean': float(row_norm.mean()), 'std' : float(row_norm.std()),
        }

    # 4. general_information
    general_information = {
        'n_elements'            : n_elems,
        'area_global_min'       : float(areas_mat.min()),
        'area_global_max'       : float(areas_mat.max()),
        'norm_area_global_min'  : float(norm_mat.min()),
        'norm_area_global_max'  : float(norm_mat.max()),
    }

    # 5. eta
    r  = 1.0
    it = n_elems
    std_i = (r / 2.0) * np.sqrt(it / (it - 1))
    eta = [1.0 - (tv_norm['std'][ti] / std_i) for ti in range(n_t)]

    # 6. Per-element mechanics
    # Bilinear shape function derivatives at centroid (ξ=0, η=0)
    # Node order: BL(0), BR(1), TR(2), TL(3)
    # dN/dξ row: [-1/4, 1/4, 1/4, -1/4]
    # dN/dη row: [-1/4, -1/4, 1/4, 1/4]
    B = np.array([[-0.25,  0.25, 0.25, -0.25],
                  [-0.25, -0.25, 0.25,  0.25]], dtype=float)

    edge_sizes = {}
    q          = {}
    epsilon    = {}
    F_grad     = {}
    shear      = {}
    gle        = {}
    edi        = {}
    J_det      = {}
    C_iso      = {}

    if w_param_sets is None:
        w_param_sets = [(1, 1, 1, 1), (1, 1, 2, 2)]
    _w_param_sets = w_param_sets
    w  = {params: {} for params in _w_param_sets}
    I2 = np.eye(2)

    for ei, eid in enumerate(elem_ids):
        n1, n2, n3, n4 = DATA_Q1['elements'][eid]   # 0-based node indices

        # Reference positions (t=0); nodes dict uses 1-based keys
        p1_0 = np.array(DATA_Q1['nodes'][0][n1 + 1][:2], dtype=float)
        p2_0 = np.array(DATA_Q1['nodes'][0][n2 + 1][:2], dtype=float)
        p3_0 = np.array(DATA_Q1['nodes'][0][n3 + 1][:2], dtype=float)
        p4_0 = np.array(DATA_Q1['nodes'][0][n4 + 1][:2], dtype=float)

        l1_0 = float(np.linalg.norm(p2_0 - p1_0))   # BL-BR
        l2_0 = float(np.linalg.norm(p3_0 - p2_0))   # BR-TR
        l3_0 = float(np.linalg.norm(p4_0 - p3_0))   # TR-TL
        l4_0 = float(np.linalg.norm(p1_0 - p4_0))   # TL-BL

        # Reference Jacobian via bilinear shape functions
        P_ref_0 = np.array([p1_0, p2_0, p3_0, p4_0], dtype=float)  # (4,2)
        J_ref_0 = B @ P_ref_0                                         # (2,2)
        try:
            J_ref_0_inv_T = np.linalg.inv(J_ref_0.T)
        except np.linalg.LinAlgError:
            J_ref_0_inv_T = np.linalg.pinv(J_ref_0.T)

        edge_sizes[eid] = {}
        q[eid]          = {}
        epsilon[eid]    = {}
        F_grad[eid]     = {}
        shear[eid]      = {}
        gle[eid]        = {}
        edi[eid]        = {}
        J_det[eid]      = {}
        C_iso[eid]      = {}
        for params in _w_param_sets:
            w[params][eid] = {}

        for ti in range(n_t):
            p1 = np.array(DATA_Q1['nodes'][ti][n1 + 1][:2], dtype=float)
            p2 = np.array(DATA_Q1['nodes'][ti][n2 + 1][:2], dtype=float)
            p3 = np.array(DATA_Q1['nodes'][ti][n3 + 1][:2], dtype=float)
            p4 = np.array(DATA_Q1['nodes'][ti][n4 + 1][:2], dtype=float)

            l1 = float(np.linalg.norm(p2 - p1))
            l2 = float(np.linalg.norm(p3 - p2))
            l3 = float(np.linalg.norm(p4 - p3))
            l4 = float(np.linalg.norm(p1 - p4))

            edge_sizes[eid][ti] = [l1, l2, l3, l4]

            sum_l2 = l1**2 + l2**2 + l3**2 + l4**2
            area   = areas_mat[ei, ti]
            q[eid][ti] = (4.0 * area / sum_l2) if sum_l2 > 1e-30 else 0.0

            epsilon[eid][ti] = [
                (l1 - l1_0) / l1_0 if l1_0 > 1e-30 else 0.0,
                (l2 - l2_0) / l2_0 if l2_0 > 1e-30 else 0.0,
                (l3 - l3_0) / l3_0 if l3_0 > 1e-30 else 0.0,
                (l4 - l4_0) / l4_0 if l4_0 > 1e-30 else 0.0,
            ]

            # Deformation gradient via bilinear shape functions
            P_def = np.array([p1, p2, p3, p4], dtype=float)  # (4,2)
            J_def = B @ P_def                                  # (2,2)
            F_mat = J_def.T @ J_ref_0_inv_T
            F_grad[eid][ti] = F_mat.tolist()

            shear[eid][ti] = 0.5 * float(np.trace(F_mat.T @ F_mat))

            E_mat = 0.5 * (F_mat.T @ F_mat - np.eye(2))
            gle[eid][ti] = float(np.trace(E_mat))

            edi[eid][ti] = (1.0 / 4.0) * (
                (abs(l1 / l1_0) if l1_0 > 1e-30 else 0.0) +
                (abs(l2 / l2_0) if l2_0 > 1e-30 else 0.0) +
                (abs(l3 / l3_0) if l3_0 > 1e-30 else 0.0) +
                (abs(l4 / l4_0) if l4_0 > 1e-30 else 0.0)
            )

            J = float(np.linalg.det(F_mat))
            J_det[eid][ti] = J

            J_pos = max(abs(J), 1e-30)
            C_mat = (J_pos ** (-2.0 / 3.0)) * (F_mat.T @ F_mat)
            C_iso[eid][ti] = C_mat.tolist()

            for (K, G, m, n) in _w_param_sets:
                vol = (K / 4.0) * (
                    (1.0 / m**2) * (J_pos**m - 1.0)**2
                    + (1.0 / m**2) * (J_pos**(-m) - 1.0)**2
                )
                C_n  = fractional_matrix_power(C_mat,  n)
                C_ni = fractional_matrix_power(C_mat, -n)
                iso = (G / 4.0) * (
                    (1.0 / n**2) * np.linalg.norm(C_n  - I2, 'fro')**2
                    + (1.0 / n**2) * np.linalg.norm(C_ni - I2, 'fro')**2
                )
                w[(K, G, m, n)][eid][ti] = float(vol + iso)

    # 7. Assemble per-timestep aggregates
    shear_mean = [float(np.mean([shear[eid][ti] for eid in elem_ids])) for ti in range(n_t)]
    gle_mean   = [float(np.mean([gle[eid][ti]   for eid in elem_ids])) for ti in range(n_t)]
    edi_mean   = [float(np.mean([edi[eid][ti]   for eid in elem_ids])) for ti in range(n_t)]

    w_mean = {
        params: [float(np.mean([w[params][eid][ti] for eid in elem_ids])) for ti in range(n_t)]
        for params in _w_param_sets
    }
    w_std = {
        params: [float(np.std([w[params][eid][ti] for eid in elem_ids])) for ti in range(n_t)]
        for params in _w_param_sets
    }
    _cv_eps = 1e-30
    w_cv = {
        params: [float(w_std[params][ti] / (abs(w_mean[params][ti]) + _cv_eps)) for ti in range(n_t)]
        for params in _w_param_sets
    }

    _area0     = {eid: float(DATA_Q1['elements_area'][eid][0]) for eid in elem_ids}
    _area0_sum = max(float(sum(_area0.values())), 1e-30)
    W = {
        params: [float(sum(w[params][eid][ti] * _area0[eid] for eid in elem_ids)) for ti in range(n_t)]
        for params in _w_param_sets
    }
    _w_area_mean = {
        params: [float(W[params][ti] / _area0_sum) for ti in range(n_t)]
        for params in _w_param_sets
    }
    w_std_area_weighted = {
        params: [
            float(np.sqrt(
                sum(_area0[eid] * (w[params][eid][ti] - _w_area_mean[params][ti])**2
                    for eid in elem_ids) / _area0_sum
            ))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }
    w_cv_area_weighted = {
        params: [
            float(w_std_area_weighted[params][ti] / (abs(_w_area_mean[params][ti]) + _cv_eps))
            for ti in range(n_t)
        ]
        for params in _w_param_sets
    }

    PKL_Q2 = {
        **_propagate_source_metadata(DATA_Q1),
        't': t,
        'time_variant'        : {'areas': tv_areas, 'normalized_areas': tv_norm},
        'time_invariant'      : {'areas': ti_areas, 'normalized_areas': ti_norm},
        'general_information' : general_information,
        'eta'        : eta,
        'edge_sizes' : edge_sizes,
        'q'          : q,
        'epsilon'    : epsilon,
        'F'          : F_grad,
        'shear'      : shear,
        'gle'        : gle,
        'shear_mean' : shear_mean,
        'gle_mean'   : gle_mean,
        'edi'        : edi,
        'edi_mean'   : edi_mean,
        'J'          : J_det,
        'C'          : C_iso,
        'w'          : w,
        'w_mean'     : w_mean,
        'w_std'      : w_std,
        'w_cv'       : w_cv,
        'w_std_area_weighted': w_std_area_weighted,
        'w_cv_area_weighted' : w_cv_area_weighted,
        'W'          : W,
    }

    # 8. Save
    if output_path is None and sim_num is not None:
        output_path = f'I001_Results/DATA_PICK_{sim_num:03d}_Q2.pkl'

    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as fp:
            pickle.dump(PKL_Q2, fp)
        print(f"PKL_Q2 saved to '{output_path}'")

    return PKL_Q2


# ---------------------------------------------------------------------------
# J1 pickle: dual-mesh nodes mapped to deformed config + bar stresses
# ---------------------------------------------------------------------------

def create_PKL_J1(
    DATA_B: dict,
    DATA_C2: dict,
    graph_file_path: str,
    output_path: str = None,
    sim_num: int = None,
) -> dict:
    """
    Create the DATA_J1 dictionary (and optionally save it as a pickle).

    Parameters
    ----------
    DATA_B : dict
        Stress data with keys ``'S11'``, ``'S22'``, ``'S21'`` (or ``'S12'``),
        and ``'t'``.
    DATA_C2 : dict
        Mesh data with keys ``'nodes_time'``, ``'elements'``, ``'t'``.
    graph_file_path : str
        Path to the ``.graph.json`` file produced from the mesh JSON.
    output_path : str, optional
        If given, the resulting dictionary is pickled to this file.
        When *None* and *sim_num* is provided the default path
        ``I001_Results/DATA_PICK_{sim_num:03d}_J1.pkl`` is used.
    sim_num : int, optional
        Simulation number (used for the default output path and to
        load the simulation JSON for scale factors / mesh file).

    Returns
    -------
    dict
        DATA_J1 with keys ``'t'``, ``'nodes'``, ``'bars'``,
        ``'bars_connectivity'``.

    Structure
    ---------
    DATA_J1['t']
        List of timesteps (same as DATA_C2['t']).
    DATA_J1['nodes'][node_idx][ti]
        ``(x, y)`` deformed coordinates of graph-mesh node *node_idx*
        at time-step *ti*.
    DATA_J1['bars'][bar_id][ti]['normals']
        List of unit-normal vectors (one per sub-bar segment) for
        original bar *bar_id* at time-step *ti*.  The normal of each
        segment points from its first node to its second node.
    DATA_J1['bars'][bar_id][ti]['SS']
        List of ``(S11, S22, S12)`` stress tuples — one per node that
        belongs to the bar (len = n_sub_bars + 1).
    DATA_J1['bars_connectivity'][bar_id]
        List of ``(ni, nf)`` tuples giving the global node indices
        for each sub-bar segment (time-independent).
    """
    from A001_functions.Hex_5 import _shape_functions_quad, _shape_functions_tri
    from A001_functions.fem_stress_interpolation import (
        _get_stress_at_integration_points,
        _interpolate_at_natural_coords,
    )

    graph = read_graph_mesh(graph_file_path)
    n_timesteps = len(DATA_C2['nodes_time'])

    # ------------------------------------------------------------------
    # 0.  Load scale factors and build the TRUE undeformed node list
    #     from the mesh file (the mesh file is in [0,1]^2; we scale it).
    #     nodes_time[0] is NOT the undeformed configuration.
    # ------------------------------------------------------------------
    if sim_num is None:
        raise ValueError("sim_num is required to load scale factors from JSON")

    json_path = f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json'
    with open(json_path, 'r') as f:
        sim_json = json.load(f)

    scale_x = sim_json['scale_x']
    scale_y = sim_json['scale_y']
    mesh_file_path = sim_json['input_name']

    print(f"  Scale factors: scale_x={scale_x}, scale_y={scale_y}")
    print(f"  Mesh file: {mesh_file_path}")

    # Read mesh file nodes (each is (x, y, id) in [0,1]^2)
    mesh_nodes_raw, _ = read_mesh_json(mesh_file_path)

    # Build undeformed node list matching nodes_time ordering (0-based)
    # Scaled to physical dimensions.
    n_fe_nodes = len(DATA_C2['nodes_time'][0])
    nodes_undeformed = [(float(x) * scale_x, float(y) * scale_y)
                        for x, y, _ in mesh_nodes_raw]
    assert len(nodes_undeformed) == n_fe_nodes, (
        f"Mesh file has {len(nodes_undeformed)} nodes but DATA_C2 has {n_fe_nodes}")

    # Scale graph node coordinates
    graph_nodes_scaled = np.empty_like(graph.nodes)
    graph_nodes_scaled[:, 0] = graph.nodes[:, 0] * scale_x
    graph_nodes_scaled[:, 1] = graph.nodes[:, 1] * scale_y
    print(f"  Graph nodes scaled: x=[{graph_nodes_scaled[:,0].min():.4f}, "
          f"{graph_nodes_scaled[:,0].max():.4f}], "
          f"y=[{graph_nodes_scaled[:,1].min():.4f}, "
          f"{graph_nodes_scaled[:,1].max():.4f}]")

    # Helper: get element node coords from undeformed config
    def _get_element_nodes_undef(elem_key):
        """elem_key is a 1-based string key into DATA_C2['elements']."""
        elem = DATA_C2['elements'][elem_key]
        return np.array([nodes_undeformed[n - 1] for n in elem], dtype=float)

    # ------------------------------------------------------------------
    # 1.  Pre-compute the containing element for each graph node
    #     (in the TRUE UNDEFORMED mesh from the mesh file).
    # ------------------------------------------------------------------
    n_elements = len(DATA_C2['elements'])
    elem_keys = sorted(DATA_C2['elements'].keys(), key=int)
    centroids = np.empty((n_elements, 2))
    for i, ek in enumerate(elem_keys):
        centroids[i] = _get_element_nodes_undef(ek).mean(axis=0)
    tree = cKDTree(centroids)

    K_NEIGHBOURS = min(30, n_elements)

    node_elem_cache = [None] * graph.n_nodes       # 1-based string key
    node_natural_cache = [None] * graph.n_nodes     # (xi, eta) in undeformed

    for nidx in range(graph.n_nodes):
        x0, y0 = graph_nodes_scaled[nidx]
        _, near_idxs = tree.query([x0, y0], k=K_NEIGHBOURS)
        if K_NEIGHBOURS == 1:
            near_idxs = [near_idxs]

        found = False
        best_elem, best_dist = None, np.inf
        best_xi, best_eta = None, None
        for cidx in near_idxs:
            ek = elem_keys[int(cidx)]
            nodes_undef = _get_element_nodes_undef(ek)
            n_en = len(DATA_C2['elements'][ek])

            if n_en == 3:
                xi, eta = _map_physical_to_natural_tri(
                    float(x0), float(y0), nodes_undef)
                if _point_in_tri(xi, eta, tol=1e-8):
                    node_elem_cache[nidx] = ek
                    node_natural_cache[nidx] = (xi, eta)
                    found = True
                    break
                dist = _dist_outside_tri(xi, eta)
            else:
                xi, eta = _map_physical_to_natural_quad(
                    float(x0), float(y0), nodes_undef)
                if abs(xi) <= 1.0 + 1e-8 and abs(eta) <= 1.0 + 1e-8:
                    node_elem_cache[nidx] = ek
                    node_natural_cache[nidx] = (xi, eta)
                    found = True
                    break
                dist = max(abs(xi), abs(eta))

            if dist < best_dist:
                best_dist = dist
                best_elem = ek
                best_xi, best_eta = xi, eta

        if not found:
            node_elem_cache[nidx] = best_elem
            node_natural_cache[nidx] = (best_xi, best_eta)

        if (nidx + 1) % 200 == 0 or nidx == graph.n_nodes - 1:
            print(f"  Element search: {nidx + 1}/{graph.n_nodes} nodes done")

    # ------------------------------------------------------------------
    # 2.  Build bars_connectivity  (time-independent)
    # ------------------------------------------------------------------
    unique_bar_ids = sorted(set(graph.bar_numbers.tolist()))
    bars_connectivity = {}
    bar_sub_indices = {}

    for bar_id in unique_bar_ids:
        mask = graph.bar_numbers == bar_id
        sub_rows = np.where(mask)[0]
        sub_bars = graph.bars[sub_rows].tolist()
        ordered_pairs = _order_sub_bar_chain(sub_bars)
        bars_connectivity[bar_id] = [(ni, nf) for ni, nf in ordered_pairs]
        bar_sub_indices[bar_id] = ordered_pairs

    # ------------------------------------------------------------------
    # 3.  For each time-step, map graph nodes to deformed config using
    #     the natural coordinates found in the UNDEFORMED reference,
    #     then compute normals and interpolate stresses.
    # ------------------------------------------------------------------
    nodes_data = [dict() for _ in range(graph.n_nodes)]
    bars_data = {bid: dict() for bid in unique_bar_ids}
    zero_stress_fallbacks = 0

    for ti in range(n_timesteps):
        ti_key = str(ti + 1)
        # --- 3a. deformed positions via shape-function evaluation --------
        deformed_pos = np.empty((graph.n_nodes, 2))
        for nidx in range(graph.n_nodes):
            ek = node_elem_cache[nidx]
            xi, eta = node_natural_cache[nidx]
            nodes_def = _get_element_nodes_at(DATA_C2, ek, ti_key)
            n_en = len(DATA_C2['elements'][ek])
            if n_en == 3:
                N = _shape_functions_tri(xi, eta)
            else:
                N = _shape_functions_quad(xi, eta)
            x_def = float(N @ nodes_def[:, 0])
            y_def = float(N @ nodes_def[:, 1])
            deformed_pos[nidx] = (x_def, y_def)
            nodes_data[nidx][ti] = (x_def, y_def)

        # --- 3b. per-bar normals and stresses ----------------------------
        for bar_id in unique_bar_ids:
            pairs = bar_sub_indices[bar_id]
            normals = []
            for ni, nf in pairs:
                p0 = deformed_pos[ni]
                p1 = deformed_pos[nf]
                d = p1 - p0
                length = np.linalg.norm(d)
                if length > 0:
                    normals.append((d[0] / length, d[1] / length))
                else:
                    normals.append((0.0, 0.0))

            bar_nodes = [pairs[0][0]] + [nf for _, nf in pairs]

            stresses = []
            for nidx in bar_nodes:
                try:
                    ek = node_elem_cache[nidx]
                    xi, eta = node_natural_cache[nidx]
                    n_en = len(DATA_C2['elements'][ek])

                    # Get stress at integration points for this element
                    s11_ip, s22_ip, s12_ip = _get_stress_at_integration_points(
                        DATA_B, ek, ti_key, n_element_nodes=n_en
                    )

                    if n_en == 3:
                        # Triangle: single integration point → constant stress
                        stresses.append((float(s11_ip[0]),
                                         float(s22_ip[0]),
                                         float(s12_ip[0])))
                    else:
                        # Quad: interpolate from 4 Gauss points using
                        # the natural coordinates found in the UNDEFORMED
                        # reference (isoparametric ⇒ same in deformed).
                        stresses.append((
                            _interpolate_at_natural_coords(xi, eta, s11_ip),
                            _interpolate_at_natural_coords(xi, eta, s22_ip),
                            _interpolate_at_natural_coords(xi, eta, s12_ip),
                        ))
                except Exception:
                    stresses.append((0.0, 0.0, 0.0))
                    zero_stress_fallbacks += 1

            bars_data[bar_id][ti] = {
                'normals': normals,
                'SS': stresses,
            }

        print(f"  Timestep {ti + 1}/{n_timesteps} done")

    if zero_stress_fallbacks > 0:
        print(f"  WARNING: {zero_stress_fallbacks} stress lookups failed and were "
              f"replaced with (0, 0, 0); affected bars will be classified as "
              f"compression downstream (axial force 0).")

    # ------------------------------------------------------------------
    # 4.  Assemble DATA_J1
    # ------------------------------------------------------------------
    DATA_J1 = {
        **_source_metadata(graph_file_path),
        't': DATA_C2['t'][:n_timesteps],
        'nodes': nodes_data,
        'bars': bars_data,
        'bars_connectivity': bars_connectivity,
    }

    # ------------------------------------------------------------------
    # 5.  Optionally save to pickle
    # ------------------------------------------------------------------
    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(DATA_J1, f)
        print(f"DATA_J1 saved to '{output_path}'")

    return DATA_J1


# ---------------------------------------------------------------------------
# K1 pickle: similar to J1 but with node IDs, per-node stresses, and
#            an alternative bar stress metric (bars_meth2).
#            Works with .gridhex.json files (no sub-bars, bars always ID1→ID2).
# ---------------------------------------------------------------------------

def create_PKL_K1(
    DATA_B: dict,
    DATA_C2: dict,
    gridhex_file_path: str,
    output_path: str = None,
    sim_num: int = None,
    create_bars_2: bool = False,
) -> dict:
    """
    Create the DATA_K1 dictionary (and optionally save it as a pickle).

    Similar to :func:`create_PKL_J1` but uses ``.gridhex.json`` files (same
    JSON graph object as ``.graph.json`` but bars have no sub-elements and always run
    from an ID=1 node to an ID=2 node).  Adds per-node IDs, per-node
    stress tensors, and an optional alternative bar stress metric.

    Parameters
    ----------
    DATA_B : dict
        Stress data with keys ``'S11'``, ``'S22'``, ``'S21'`` (or ``'S12'``),
        and ``'t'``.
    DATA_C2 : dict
        Mesh data with keys ``'nodes_time'``, ``'elements'``, ``'t'``.
    gridhex_file_path : str
        Path to the ``.gridhex.json`` file (same JSON graph object but
        without sub-bars).
    output_path : str, optional
        If given, the resulting dictionary is pickled to this file.
    sim_num : int, optional
        Simulation number (used for the default output path and to
        load the simulation JSON for scale factors / mesh file).
    create_bars_2 : bool, optional
        If True, compute ``bars_meth2`` — a scalar axial stress for
        each bar evaluated at the ID=1 endpoint only.

    Returns
    -------
    dict
        DATA_K1 with keys ``'t'``, ``'nodes'``, ``'nodes_id'``,
        ``'nodes_stress'``, ``'bars'``, ``'bars_connectivity'``,
        and optionally ``'bars_meth2'``.

    Structure
    ---------
    DATA_K1['t']
        List of timesteps.
    DATA_K1['nodes'][node_idx][ti]
        ``(x, y)`` deformed coordinates of graph-mesh node *node_idx*
        at time-step *ti*.
    DATA_K1['nodes_id'][node_idx]
        Integer ID of node *node_idx* (read from the ``.gridhex.json`` file).
    DATA_K1['nodes_stress'][ti][node_idx]
        ``[S11, S22, S12]`` interpolated stress tensor components at
        node *node_idx* for time-step *ti*.
    DATA_K1['bars'][bar_id][ti]['normals']
        List of unit-direction vectors (one per segment) for bar
        *bar_id* at time-step *ti*.
    DATA_K1['bars'][bar_id][ti]['SS']
        List of ``(S11, S22, S12)`` stress tuples — one per node that
        belongs to the bar.
    DATA_K1['bars_connectivity'][bar_id]
        List of ``(ni, nf)`` tuples giving the global node indices
        for each bar segment (time-independent).
    DATA_K1['bars_meth2'][bar_id][ti]
        (Only if *create_bars_2* is True.)  Scalar axial stress
        ``n^T S n`` evaluated at the ID=1 endpoint of the bar, where
        ``n`` is the unit direction from the ID=1 node to the ID=2
        node in the deformed configuration.
    """
    from A001_functions.Hex_5 import _shape_functions_quad, _shape_functions_tri
    from A001_functions.fem_stress_interpolation import (
        _get_stress_at_integration_points,
        _interpolate_at_natural_coords,
    )

    graph = read_graph_mesh(gridhex_file_path)
    n_timesteps = len(DATA_C2['nodes_time'])

    # ------------------------------------------------------------------
    # 0.  Load scale factors and build the TRUE undeformed node list
    # ------------------------------------------------------------------
    if sim_num is None:
        raise ValueError("sim_num is required to load scale factors from JSON")

    json_path = f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json'
    with open(json_path, 'r') as f:
        sim_json = json.load(f)

    scale_x = sim_json['scale_x']
    scale_y = sim_json['scale_y']
    mesh_file_path = sim_json['input_name']

    print(f"  Scale factors: scale_x={scale_x}, scale_y={scale_y}")
    print(f"  Mesh file: {mesh_file_path}")

    mesh_nodes_raw, _ = read_mesh_json(mesh_file_path)

    n_fe_nodes = len(DATA_C2['nodes_time'][0])
    nodes_undeformed = [(float(x) * scale_x, float(y) * scale_y)
                        for x, y, _ in mesh_nodes_raw]
    assert len(nodes_undeformed) == n_fe_nodes, (
        f"Mesh file has {len(nodes_undeformed)} nodes but DATA_C2 has {n_fe_nodes}")

    # Scale graph node coordinates
    graph_nodes_scaled = np.empty_like(graph.nodes)
    graph_nodes_scaled[:, 0] = graph.nodes[:, 0] * scale_x
    graph_nodes_scaled[:, 1] = graph.nodes[:, 1] * scale_y
    print(f"  Graph nodes scaled: x=[{graph_nodes_scaled[:,0].min():.4f}, "
          f"{graph_nodes_scaled[:,0].max():.4f}], "
          f"y=[{graph_nodes_scaled[:,1].min():.4f}, "
          f"{graph_nodes_scaled[:,1].max():.4f}]")

    # ------------------------------------------------------------------
    # 0b. Read node IDs from the gridhex file
    # ------------------------------------------------------------------
    nodes_id = graph.node_ids.tolist()   # list[int], indexed by node_idx

    def _get_element_nodes_undef(elem_key):
        elem = DATA_C2['elements'][elem_key]
        return np.array([nodes_undeformed[n - 1] for n in elem], dtype=float)

    # ------------------------------------------------------------------
    # 1.  Pre-compute the containing element for each graph node
    # ------------------------------------------------------------------
    n_elements = len(DATA_C2['elements'])
    elem_keys = sorted(DATA_C2['elements'].keys(), key=int)
    centroids = np.empty((n_elements, 2))
    for i, ek in enumerate(elem_keys):
        centroids[i] = _get_element_nodes_undef(ek).mean(axis=0)
    tree = cKDTree(centroids)

    K_NEIGHBOURS = min(30, n_elements)

    node_elem_cache = [None] * graph.n_nodes
    node_natural_cache = [None] * graph.n_nodes

    for nidx in range(graph.n_nodes):
        x0, y0 = graph_nodes_scaled[nidx]
        _, near_idxs = tree.query([x0, y0], k=K_NEIGHBOURS)
        if K_NEIGHBOURS == 1:
            near_idxs = [near_idxs]

        found = False
        best_elem, best_dist = None, np.inf
        best_xi, best_eta = None, None
        for cidx in near_idxs:
            ek = elem_keys[int(cidx)]
            nodes_undef = _get_element_nodes_undef(ek)
            n_en = len(DATA_C2['elements'][ek])

            if n_en == 3:
                xi, eta = _map_physical_to_natural_tri(
                    float(x0), float(y0), nodes_undef)
                if _point_in_tri(xi, eta, tol=1e-8):
                    node_elem_cache[nidx] = ek
                    node_natural_cache[nidx] = (xi, eta)
                    found = True
                    break
                dist = _dist_outside_tri(xi, eta)
            else:
                xi, eta = _map_physical_to_natural_quad(
                    float(x0), float(y0), nodes_undef)
                if abs(xi) <= 1.0 + 1e-8 and abs(eta) <= 1.0 + 1e-8:
                    node_elem_cache[nidx] = ek
                    node_natural_cache[nidx] = (xi, eta)
                    found = True
                    break
                dist = max(abs(xi), abs(eta))

            if dist < best_dist:
                best_dist = dist
                best_elem = ek
                best_xi, best_eta = xi, eta

        if not found:
            node_elem_cache[nidx] = best_elem
            node_natural_cache[nidx] = (best_xi, best_eta)

        if (nidx + 1) % 200 == 0 or nidx == graph.n_nodes - 1:
            print(f"  Element search: {nidx + 1}/{graph.n_nodes} nodes done")

    # ------------------------------------------------------------------
    # 2.  Build bars_connectivity  (time-independent)
    # ------------------------------------------------------------------
    unique_bar_ids = sorted(set(graph.bar_numbers.tolist()))
    bars_connectivity = {}
    bar_sub_indices = {}

    for bar_id in unique_bar_ids:
        mask = graph.bar_numbers == bar_id
        sub_rows = np.where(mask)[0]
        sub_bars = graph.bars[sub_rows].tolist()
        ordered_pairs = _order_sub_bar_chain(sub_bars)
        bars_connectivity[bar_id] = [(ni, nf) for ni, nf in ordered_pairs]
        bar_sub_indices[bar_id] = ordered_pairs

    # ------------------------------------------------------------------
    # 2b. For bars_meth2: identify the ID=1 endpoint of each bar
    # ------------------------------------------------------------------
    if create_bars_2:
        bar_id1_node = {}   # bar_id -> node index with ID=1
        bar_id2_node = {}   # bar_id -> node index with ID=2
        for bar_id in unique_bar_ids:
            pairs = bar_sub_indices[bar_id]
            start_node = pairs[0][0]
            end_node = pairs[-1][1]
            if nodes_id[start_node] == 1:
                bar_id1_node[bar_id] = start_node
                bar_id2_node[bar_id] = end_node
            elif nodes_id[end_node] == 1:
                bar_id1_node[bar_id] = end_node
                bar_id2_node[bar_id] = start_node
            else:
                raise ValueError(
                    f"Bar {bar_id}: neither endpoint (nodes "
                    f"{start_node}, {end_node}) has ID=1. "
                    f"IDs are {nodes_id[start_node]}, {nodes_id[end_node]}")

    # ------------------------------------------------------------------
    # 3.  For each time-step: deformed positions, normals, stresses,
    #     per-node stresses, and optionally bars_meth2.
    # ------------------------------------------------------------------
    nodes_data = [dict() for _ in range(graph.n_nodes)]
    bars_data = {bid: dict() for bid in unique_bar_ids}
    nodes_stress_data = [None] * n_timesteps
    if create_bars_2:
        bars_meth2_data = {bid: dict() for bid in unique_bar_ids}

    def _interpolate_stress_at_node(nidx, ti_key):
        """Return (S11, S22, S12) interpolated at graph node nidx."""
        ek = node_elem_cache[nidx]
        xi, eta = node_natural_cache[nidx]
        n_en = len(DATA_C2['elements'][ek])

        s11_ip, s22_ip, s12_ip = _get_stress_at_integration_points(
            DATA_B, ek, ti_key, n_element_nodes=n_en
        )

        if n_en == 3:
            return (float(s11_ip[0]), float(s22_ip[0]), float(s12_ip[0]))
        else:
            return (
                _interpolate_at_natural_coords(xi, eta, s11_ip),
                _interpolate_at_natural_coords(xi, eta, s22_ip),
                _interpolate_at_natural_coords(xi, eta, s12_ip),
            )

    for ti in range(n_timesteps):
        ti_key = str(ti + 1)
        # --- 3a. deformed positions via shape-function evaluation --------
        deformed_pos = np.empty((graph.n_nodes, 2))
        for nidx in range(graph.n_nodes):
            ek = node_elem_cache[nidx]
            xi, eta = node_natural_cache[nidx]
            nodes_def = _get_element_nodes_at(DATA_C2, ek, ti_key)
            n_en = len(DATA_C2['elements'][ek])
            if n_en == 3:
                N = _shape_functions_tri(xi, eta)
            else:
                N = _shape_functions_quad(xi, eta)
            x_def = float(N @ nodes_def[:, 0])
            y_def = float(N @ nodes_def[:, 1])
            deformed_pos[nidx] = (x_def, y_def)
            nodes_data[nidx][ti] = (x_def, y_def)

        # --- 3b. per-node stress tensor ----------------------------------
        stress_ti = {}
        for nidx in range(graph.n_nodes):
            try:
                s11, s22, s12 = _interpolate_stress_at_node(nidx, ti_key)
                stress_ti[nidx] = [s11, s22, s12]
            except Exception:
                stress_ti[nidx] = [0.0, 0.0, 0.0]
        nodes_stress_data[ti] = stress_ti

        # --- 3c. per-bar normals and stresses (same as J1) ---------------
        for bar_id in unique_bar_ids:
            pairs = bar_sub_indices[bar_id]
            normals = []
            for ni, nf in pairs:
                p0 = deformed_pos[ni]
                p1 = deformed_pos[nf]
                d = p1 - p0
                length = np.linalg.norm(d)
                if length > 0:
                    normals.append((d[0] / length, d[1] / length))
                else:
                    normals.append((0.0, 0.0))

            bar_nodes = [pairs[0][0]] + [nf for _, nf in pairs]

            stresses = []
            for nidx in bar_nodes:
                try:
                    s11, s22, s12 = _interpolate_stress_at_node(nidx, ti_key)
                    stresses.append((s11, s22, s12))
                except Exception:
                    stresses.append((0.0, 0.0, 0.0))

            bars_data[bar_id][ti] = {
                'normals': normals,
                'SS': stresses,
            }

        # --- 3d. bars_meth2: n^T S n at the ID=1 endpoint ---------------
        if create_bars_2:
            for bar_id in unique_bar_ids:
                n1_idx = bar_id1_node[bar_id]
                n2_idx = bar_id2_node[bar_id]

                # Direction from ID=1 to ID=2 in deformed config
                p1 = deformed_pos[n1_idx]
                p2 = deformed_pos[n2_idx]
                d = p2 - p1
                length = np.linalg.norm(d)
                if length > 0:
                    n_vec = d / length
                else:
                    n_vec = np.array([0.0, 0.0])

                # Stress tensor at ID=1 node
                s11, s22, s12 = stress_ti[n1_idx]
                S = np.array([[s11, s12],
                              [s12, s22]])

                # Scalar axial stress: n^T S n
                axial_stress = float(n_vec @ S @ n_vec)
                bars_meth2_data[bar_id][ti] = axial_stress

        print(f"  Timestep {ti + 1}/{n_timesteps} done")

    # ------------------------------------------------------------------
    # 4.  Assemble DATA_K1
    # ------------------------------------------------------------------
    DATA_K1 = {
        **_source_metadata(gridhex_file_path),
        't': DATA_C2['t'][:n_timesteps],
        'nodes': nodes_data,
        'nodes_id': nodes_id,
        'nodes_stress': nodes_stress_data,
        'bars': bars_data,
        'bars_connectivity': bars_connectivity,
    }

    if create_bars_2:
        DATA_K1['bars_meth2'] = bars_meth2_data

    # ------------------------------------------------------------------
    # 5.  Optionally save to pickle
    # ------------------------------------------------------------------
    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(DATA_K1, f)
        print(f"DATA_K1 saved to '{output_path}'")

    return DATA_K1


def create_PKL_J2(
    DATA_J1: dict,
    output_path: str = None,
    sim_num: int = None,
) -> dict:
    """
    Create the DATA_J2 dictionary (and optionally save it as a pickle).

    For every time-step the original bars are classified as *tension* or
    *compression* and placed into two separate **NetworkX** graphs.

    Classification
    --------------
    The axial force of a bar is evaluated at the middle sub-bar segment
    (or averaged over the two middle segments when the count is even)::

        axial_force = n^T · S · n

    where ``S = [[S11, S12], [S12, S22]]`` is the Cauchy stress tensor
    at the segment mid-point (average of the two endpoint stress values)
    and ``n`` is the unit direction vector of the segment (node_i → node_f).

    A positive axial force → **tension**; zero or negative → **compression**.

    Graph construction
    ------------------
    * **Nodes** — all *original* nodes (i.e. the first and last node of
      each bar chain, *not* the subdivision nodes).  Each node stores
      a ``pos`` attribute with its ``(x, y)`` deformed position at that
      time-step.
    * **Edges** — one edge per original bar (not per sub-bar).  Each
      edge connects the two original endpoint nodes and stores
      ``bar_id`` and ``axial_force`` attributes.

    Parameters
    ----------
    DATA_J1 : dict
        Output of :func:`create_PKL_J1`.
    output_path : str, optional
        If given, the resulting dictionary is pickled to this file.
        When *None* and *sim_num* is provided the default path
        ``I001_Results/DATA_PICK_{sim_num:03d}_J2.pkl`` is used.
    sim_num : int, optional
        Simulation number (used for the default output path).

    Returns
    -------
    dict
        DATA_J2 with keys ``'t'``, ``'tension'``, ``'compression'``.

    Structure
    ---------
    DATA_J2['t']
        List of timesteps (same as DATA_J1['t']).
    DATA_J2['tension'][ti]
        ``networkx.Graph`` containing the bars in tension at *ti*.
    DATA_J2['compression'][ti]
        ``networkx.Graph`` containing the bars in compression at *ti*.
    """
    t = DATA_J1['t']
    n_timesteps = len(t)
    bar_ids = sorted(DATA_J1['bars_connectivity'].keys())

    # ------------------------------------------------------------------
    # Identify original nodes (bar-chain endpoints) and bar endpoints
    # ------------------------------------------------------------------
    original_nodes = set()
    bar_endpoints = {}          # bar_id -> (start_node, end_node)

    for bar_id in bar_ids:
        pairs = DATA_J1['bars_connectivity'][bar_id]
        n_start = pairs[0][0]
        n_end   = pairs[-1][1]
        original_nodes.add(n_start)
        original_nodes.add(n_end)
        bar_endpoints[bar_id] = (n_start, n_end)

    original_nodes = sorted(original_nodes)

    # ------------------------------------------------------------------
    # Pre-compute middle-segment indices for each bar
    # ------------------------------------------------------------------
    bar_mid_indices = {}
    for bar_id in bar_ids:
        n_segments = len(DATA_J1['bars_connectivity'][bar_id])
        if n_segments % 2 == 1:
            bar_mid_indices[bar_id] = [n_segments // 2]
        else:
            bar_mid_indices[bar_id] = [n_segments // 2 - 1,
                                       n_segments // 2]

    # ------------------------------------------------------------------
    # Build tension / compression graphs for each time-step
    # ------------------------------------------------------------------
    tension = {}
    compression = {}

    for ti in range(n_timesteps):
        G_tension     = nx.Graph()
        G_compression = nx.Graph()

        # Add all original nodes to both graphs (with deformed position)
        for nidx in original_nodes:
            pos = DATA_J1['nodes'][nidx][ti]
            G_tension.add_node(nidx, pos=pos)
            G_compression.add_node(nidx, pos=pos)

        # Classify each bar and add the edge to the appropriate graph
        for bar_id in bar_ids:
            bar_ti  = DATA_J1['bars'][bar_id][ti]
            normals = bar_ti['normals']
            SS      = bar_ti['SS']

            af_sum = 0.0
            for mid_idx in bar_mid_indices[bar_id]:
                # Direction vector of this sub-bar segment
                nvx, nvy = normals[mid_idx]
                n_vec = np.array([nvx, nvy])

                # Mid-point stress (average of endpoint node values)
                s11_a, s22_a, s12_a = SS[mid_idx]
                s11_b, s22_b, s12_b = SS[mid_idx + 1]
                S_mat = np.array([
                    [(s11_a + s11_b) / 2.0, (s12_a + s12_b) / 2.0],
                    [(s12_a + s12_b) / 2.0, (s22_a + s22_b) / 2.0],
                ])

                af_sum += float(n_vec @ S_mat @ n_vec)

            af_avg = af_sum / len(bar_mid_indices[bar_id])

            n_start, n_end = bar_endpoints[bar_id]
            if af_avg > 0:
                G_tension.add_edge(n_start, n_end,
                                   bar_id=bar_id, axial_force=af_avg)
            else:
                G_compression.add_edge(n_start, n_end,
                                       bar_id=bar_id, axial_force=af_avg)

        tension[ti]     = G_tension
        compression[ti] = G_compression

    # ------------------------------------------------------------------
    # Assemble DATA_J2
    # ------------------------------------------------------------------
    DATA_J2 = {
        **_propagate_source_metadata(DATA_J1),
        't': t,
        'tension': tension,
        'compression': compression,
    }

    # ------------------------------------------------------------------
    # Optionally save to pickle
    # ------------------------------------------------------------------
    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(DATA_J2, f)
        print(f"DATA_J2 saved to '{output_path}'")

    return DATA_J2


# ---------------------------------------------------------------------------
# K2 pickle: tension/compression graphs from K1, filtering bars per
#            ID=1 node to keep only the 2 largest + 2 smallest values.
# ---------------------------------------------------------------------------

def create_PKL_K2(
    DATA_K1: dict,
    output_path: str = None,
    sim_num: int = None,
) -> dict:
    """
    Create the DATA_K2 dictionary (and optionally save it as a pickle).

    For every time-step the bars are classified as *tension* or
    *compression* and placed into two separate **NetworkX** graphs,
    after filtering: for each ID=1 node, only the 2 bars with the
    largest ``bars_meth2`` values and the 2 bars with the smallest
    values are kept.  If an ID=1 node has fewer than 4 connections,
    all its bars are kept.

    Parameters
    ----------
    DATA_K1 : dict
        Output of :func:`create_PKL_K1` (must have been created with
        ``create_bars_2=True`` so that ``bars_meth2`` is present).
    output_path : str, optional
        If given, the resulting dictionary is pickled to this file.
    sim_num : int, optional
        Simulation number (used for the default output path).

    Returns
    -------
    dict
        DATA_K2 with keys ``'t'``, ``'tension'``, ``'compression'``.

    Structure
    ---------
    DATA_K2['t']
        List of timesteps (same as DATA_K1['t']).
    DATA_K2['tension'][ti]
        ``networkx.Graph`` containing the kept bars with positive
        ``bars_meth2`` value at *ti*.  Nodes store ``pos`` and
        ``node_id`` attributes.
    DATA_K2['compression'][ti]
        ``networkx.Graph`` containing the kept bars with zero or
        negative ``bars_meth2`` value at *ti*.  Nodes store ``pos``
        and ``node_id`` attributes.
    """
    if 'bars_meth2' not in DATA_K1:
        raise ValueError(
            "DATA_K1 must contain 'bars_meth2'. "
            "Re-run create_PKL_K1 with create_bars_2=True.")

    t = DATA_K1['t']
    n_timesteps = len(t)
    nodes_id = DATA_K1['nodes_id']
    bar_ids = sorted(DATA_K1['bars_connectivity'].keys())

    # ------------------------------------------------------------------
    # Identify bar endpoints (ID=1 node and ID=2 node) for each bar
    # ------------------------------------------------------------------
    bar_endpoints = {}          # bar_id -> (id1_node, id2_node)
    for bar_id in bar_ids:
        pairs = DATA_K1['bars_connectivity'][bar_id]
        start_node = pairs[0][0]
        end_node = pairs[-1][1]
        if nodes_id[start_node] == 1:
            bar_endpoints[bar_id] = (start_node, end_node)
        elif nodes_id[end_node] == 1:
            bar_endpoints[bar_id] = (end_node, start_node)
        else:
            raise ValueError(
                f"Bar {bar_id}: neither endpoint (nodes "
                f"{start_node}, {end_node}) has ID=1.")

    # ------------------------------------------------------------------
    # Build mapping: ID=1 node -> list of bar_ids connected to it
    # ------------------------------------------------------------------
    from collections import defaultdict
    id1_to_bars = defaultdict(list)
    for bar_id in bar_ids:
        id1_node = bar_endpoints[bar_id][0]
        id1_to_bars[id1_node].append(bar_id)

    # Collect all node indices for graph construction
    all_nodes = set()
    for bar_id in bar_ids:
        n1, n2 = bar_endpoints[bar_id]
        all_nodes.add(n1)
        all_nodes.add(n2)
    all_nodes = sorted(all_nodes)

    # ------------------------------------------------------------------
    # Build tension / compression graphs for each time-step
    # ------------------------------------------------------------------
    tension = {}
    compression = {}

    for ti in range(n_timesteps):
        # --- Determine which bars to keep at this timestep ---------------
        kept_bars = set()
        for id1_node, connected_bars in id1_to_bars.items():
            if len(connected_bars) <= 4:
                # Keep all bars for this node
                kept_bars.update(connected_bars)
            else:
                # Sort by absolute value of bars_meth2, keep 4 largest
                bar_values = [
                    (bar_id, DATA_K1['bars_meth2'][bar_id][ti])
                    for bar_id in connected_bars
                ]
                bar_values.sort(key=lambda x: abs(x[1]), reverse=True)
                # Keep 4 largest in absolute value
                keep = bar_values[:4]
                kept_bars.update(bid for bid, _ in keep)

        # --- Build graphs ------------------------------------------------
        G_tension = nx.Graph()
        G_compression = nx.Graph()

        # Add ALL nodes to both graphs
        for nidx in all_nodes:
            pos = DATA_K1['nodes'][nidx][ti]
            node_id = nodes_id[nidx]
            G_tension.add_node(nidx, pos=pos, node_id=node_id)
            G_compression.add_node(nidx, pos=pos, node_id=node_id)

        # Add kept bars to appropriate graph
        for bar_id in kept_bars:
            id1_node, id2_node = bar_endpoints[bar_id]
            axial_stress = DATA_K1['bars_meth2'][bar_id][ti]
            if axial_stress > 0:
                G_tension.add_edge(id1_node, id2_node,
                                   bar_id=bar_id, axial_force=axial_stress)
            else:
                G_compression.add_edge(id1_node, id2_node,
                                       bar_id=bar_id, axial_force=axial_stress)

        tension[ti] = G_tension
        compression[ti] = G_compression

    # ------------------------------------------------------------------
    # Assemble DATA_K2
    # ------------------------------------------------------------------
    DATA_K2 = {
        **_propagate_source_metadata(DATA_K1),
        't': t,
        'tension': tension,
        'compression': compression,
    }

    # ------------------------------------------------------------------
    # Optionally save to pickle
    # ------------------------------------------------------------------
    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(DATA_K2, f)
        print(f"DATA_K2 saved to '{output_path}'")

    return DATA_K2


def create_PKL_H2(
    DATA_J1: dict,
    output_path: str = None,
    sim_num: int = None,
) -> dict:
    """
    Create the DATA_H2 tension/compression graph dictionary (and optionally
    save it as a pickle).  Used for the H2 and I2 stages, whose grid /
    gridhex overlay bars always have exactly one segment.

    For every time-step the original bars are classified as *tension* or
    *compression* and placed into two separate **NetworkX** graphs.

    Classification
    --------------
    The axial force of a bar is evaluated at its (single) segment::

        axial_force = n^T · S · n

    where ``S = [[S11, S12], [S12, S22]]`` is the Cauchy stress tensor
    at the segment mid-point (average of the two endpoint stress values)
    and ``n`` is the unit direction vector of the segment (node_i → node_f).

    A positive axial force → **tension**; zero or negative → **compression**.

    Graph construction
    ------------------
    * **Nodes** — all *original* nodes (bar endpoints).  Each node stores
      a ``pos`` attribute with its ``(x, y)`` deformed position at that
      time-step.
    * **Edges** — one edge per bar, connecting its two endpoint nodes and
      storing ``bar_id`` and ``axial_force`` attributes.

    Parameters
    ----------
    DATA_J1 : dict
        Output of :func:`create_PKL_J1` (H1 / I1 data).
    output_path : str, optional
        If given, the resulting dictionary is pickled to this file.
        When *None* nothing is saved (the dispatch loop in
        :func:`process_simulation` handles saving).
    sim_num : int, optional
        Simulation number (informational only).

    Returns
    -------
    dict
        DATA_H2 with keys ``'t'``, ``'tension'``, ``'compression'`` and
        ``'n_nodes_total'`` (total overlay node count, isolated nodes
        included, for the all-nodes efficiency normalisation).

    Structure
    ---------
    DATA_H2['t']
        List of timesteps (same as DATA_J1['t']).
    DATA_H2['tension'][ti]
        ``networkx.Graph`` containing the bars in tension at *ti*.
    DATA_H2['compression'][ti]
        ``networkx.Graph`` containing the bars in compression at *ti*.
    """
    t = DATA_J1['t']
    n_timesteps = len(t)
    bar_ids = sorted(DATA_J1['bars_connectivity'].keys())

    # ------------------------------------------------------------------
    # Identify original nodes (bar-chain endpoints) and bar endpoints
    # ------------------------------------------------------------------
    original_nodes = set()
    bar_endpoints = {}          # bar_id -> (start_node, end_node)

    for bar_id in bar_ids:
        pairs = DATA_J1['bars_connectivity'][bar_id]
        n_start = pairs[0][0]
        n_end   = pairs[-1][1]
        original_nodes.add(n_start)
        original_nodes.add(n_end)
        bar_endpoints[bar_id] = (n_start, n_end)

    original_nodes = sorted(original_nodes)

    # ------------------------------------------------------------------
    # Pre-compute middle-segment indices for each bar
    # ------------------------------------------------------------------
    bar_mid_indices = {}
    for bar_id in bar_ids:
        n_segments = len(DATA_J1['bars_connectivity'][bar_id])
        if n_segments != 1:
            print(f"Warning: bar_id {bar_id} has {n_segments} segments; "
                  f"expected 1. Check bars_connectivity.")
        else:
            bar_mid_indices[bar_id] = [0]


    # ------------------------------------------------------------------
    # Build tension / compression graphs for each time-step
    # ------------------------------------------------------------------
    tension = {}
    compression = {}

    for ti in range(n_timesteps):
        G_tension     = nx.Graph()
        G_compression = nx.Graph()

        # Add all original nodes to both graphs (with deformed position)
        for nidx in original_nodes:
            pos = DATA_J1['nodes'][nidx][ti]
            G_tension.add_node(nidx, pos=pos)
            G_compression.add_node(nidx, pos=pos)

        # Classify each bar and add the edge to the appropriate graph
        for bar_id in bar_ids:
            bar_ti  = DATA_J1['bars'][bar_id][ti]
            normals = bar_ti['normals']
            SS      = bar_ti['SS']

            af_sum = 0.0
            for mid_idx in bar_mid_indices[bar_id]:
                # Direction vector of this sub-bar segment
                nvx, nvy = normals[mid_idx]
                n_vec = np.array([nvx, nvy])

                # Mid-point stress (average of endpoint node values)
                s11_a, s22_a, s12_a = SS[mid_idx]
                s11_b, s22_b, s12_b = SS[mid_idx + 1]
                S_mat = np.array([
                    [(s11_a + s11_b) / 2.0, (s12_a + s12_b) / 2.0],
                    [(s12_a + s12_b) / 2.0, (s22_a + s22_b) / 2.0],
                ])

                af_sum += float(n_vec @ S_mat @ n_vec)

            af_avg = af_sum / len(bar_mid_indices[bar_id])

            n_start, n_end = bar_endpoints[bar_id]
            if af_avg > 0:
                G_tension.add_edge(n_start, n_end,
                                   bar_id=bar_id, axial_force=af_avg)
            else:
                G_compression.add_edge(n_start, n_end,
                                       bar_id=bar_id, axial_force=af_avg)

        tension[ti]     = G_tension
        compression[ti] = G_compression

    # ------------------------------------------------------------------
    # Assemble DATA_H2
    # ------------------------------------------------------------------
    DATA_H2 = {
        **_propagate_source_metadata(DATA_J1),
        't': t,
        'tension': tension,
        'compression': compression,
        # Total overlay-graph node count, including isolated nodes that do
        # not appear in the tension/compression graphs.  Used by
        # create_PKL_G2_exact for the 'global_ef_*_allnodes' normalisation.
        'n_nodes_total': len(DATA_J1['nodes']),
    }

    # ------------------------------------------------------------------
    # Optionally save to pickle
    # ------------------------------------------------------------------
    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(DATA_H2, f)
        print(f"DATA_H2 saved to '{output_path}'")

    return DATA_H2

def _order_sub_bar_chain(
    sub_bars: list,
) -> list:
    """
    Given an unordered list of ``[ni, nf]`` pairs that form a single
    chain, return them re-ordered head-to-tail.

    E.g. ``[[5, 201], [202, 6], [201, 202]]`` → ``[[5, 201], [201, 202], [202, 6]]``
    """
    if len(sub_bars) <= 1:
        return [tuple(sb) for sb in sub_bars]

    # Build adjacency: node -> list of (other_node, pair_index)
    from collections import defaultdict
    adj = defaultdict(list)
    for idx, (a, b) in enumerate(sub_bars):
        adj[a].append((b, idx))
        adj[b].append((a, idx))

    # Find an endpoint (node appearing in only one pair)
    endpoints = [n for n, nbrs in adj.items() if len(nbrs) == 1]
    if len(endpoints) >= 2:
        start = endpoints[0]
    else:
        # Cycle – just start anywhere
        start = sub_bars[0][0]

    ordered = []
    visited = set()
    current = start
    while len(ordered) < len(sub_bars):
        for other, idx in adj[current]:
            if idx not in visited:
                visited.add(idx)
                # Preserve direction: current → other
                ordered.append((current, other))
                current = other
                break
        else:
            break  # no more unvisited edges

    return ordered




def process_simulation(args):
    """Processes a single simulation based on input arguments."""

    try:
        i, in_A, in_A2, in_B, in_C, in_C2, in_D, in_T1, in_T2, T1_ini, T1_fin, in_J1, in_J2, in_J3, J_ini, J_fin, J_alg, in_H1, in_H2, in_H3, H_ini, H_fin, H_alg, in_I1, in_I2, in_I3, I_ini, I_fin, I_alg, in_K1, in_K2, in_K3, K_ini, K_fin, K_alg, in_Q1, in_Q2, Q_ini, Q_fin, delete_csv, n_workers, max_memory_gb = args
        
        csv_file = f'I001_Results/RES_SIM_{i:03}.csv'

        # try:
        if in_A in ('y', 'Y'):

            # if not os.path.exists(json_path):
            #     print(f"Error in creating A, file {json_path} missing")
            if not os.path.exists(csv_file):
                print(f"Error in creating A, file {csv_file} missing")

            # CONDITIONS = [['Model'], ['BARS','BARS'], ['CABLES','CABLES'], ['RP'],['Layers'],['ADD'],['PHISIC_NODES']]
            data_varA = READ_DATA_RED_GRL(csv_file, type = 'A')
            # data_varA = append_json(data_varA, f'I001_Results/finished_simulations/SIM_{i:03}.json')

            pickle_file = f'I001_Results/DATA_PICK_{i:03}_A.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varA, f)
            del data_varA




        if in_A2 in ('y', 'Y'):
            data_varA = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_A.pkl', f"A2 for simulation {i:03d}")
            if data_varA is None:
                return
            data_varA2 = dataA2_generator(data_varA)
            pickle_file = f'I001_Results/DATA_PICK_{i:03}_A2.pkl'

            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varA2, f)

            del data_varA2
            
    

        if in_B in ('y', 'Y'):

            if not os.path.exists(csv_file):
                print(f"Error in creating B, file {csv_file} missing")

            # CONDITIONS = [['Model'], ['BARS','BARS'], ['CABLES','CABLES'], ['RP'],['Layers'],['ADD'],['PHISIC_NODES']]
            data_varB = READ_DATA_RED_GRL(csv_file, type = 'B')
            # data_varA = append_json(data_varA, f'I001_Results/finished_simulations/SIM_{i:03}.json')

            pickle_file = f'I001_Results/DATA_PICK_{i:03}_B.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varB, f)
            del data_varB


        if in_C in ('y', 'Y'):

            if not os.path.exists(csv_file):
                print(f"Error in creating B, file {csv_file} missing")

            # CONDITIONS = [['Model'], ['BARS','BARS'], ['CABLES','CABLES'], ['RP'],['Layers'],['ADD'],['PHISIC_NODES']]
            data_varC = READ_DATA_RED_GRL(csv_file, type = 'C')
            # data_varA = append_json(data_varA, f'I001_Results/finished_simulations/SIM_{i:03}.json')

            pickle_file = f'I001_Results/DATA_PICK_{i:03}_C.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varC, f)
            del data_varC


        if in_C2 in ('y', 'Y'):
            data_varC = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C.pkl', f"C2 for simulation {i:03d}")
            if data_varC is None:
                return
            data_varC2 = dataC2_generator(data_varC, sim_num=i)
            pickle_file = f'I001_Results/DATA_PICK_{i:03}_C2.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varC2, f)

            del data_varC2


        if in_D in ('y', 'Y'):
            data_varB = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_B.pkl', f"D for simulation {i:03d}")
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"D for simulation {i:03d}")
            if data_varB is None or data_varC2 is None:
                return

            data_varD = dataD_generator(data_varB, data_varC2)
            pickle_file = f'I001_Results/DATA_PICK_{i:03}_D.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varD, f)

            del data_varD


        if in_A2 in ('y', 'Y'):
            data_varA = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_A.pkl', f"A2 for simulation {i:03d}")
            if data_varA is None:
                return
            data_varA2 = dataA2_generator(data_varA)
            pickle_file = f'I001_Results/DATA_PICK_{i:03}_A2.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_varA2, f)

            del data_varA2


        if in_T1 in ('y', 'Y'):
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"T1 for simulation {i:03d}")
            if data_varC2 is None:
                return
            mesh_prefix = _mesh_prefix_for_sim(i)

            for ext_T1s in range(T1_ini, T1_fin + 1):
                try:
                    tri_file = _mesh_artifact_path(mesh_prefix, "T", ext_T1s, "tri")

                    data_T1 = create_PKL_T1(
                        data_varC2, tri_file,
                        sim_num=i,
                        output_path=f'I001_Results/DATA_PICK_{i:03}_T1_{ext_T1s:03d}.pkl',
                    )

                    if in_T2 in ('y', 'Y'):
                        try:
                            data_T2 = create_PKL_T2(
                                data_T1,
                                sim_num=i,
                                output_path=f'I001_Results/DATA_PICK_{i:03d}_T2_{ext_T1s:03d}.pkl',
                                w_param_sets= [(1,1,1,1), (1, 1, 2, 2)]
                            )
                            del data_T2
                        except Exception as e:
                            print(f"Error processing T2 for simulation {i:03d}, T1={ext_T1s:03d}: {e}")

                    del data_T1
                except Exception as e:
                    print(f"Error processing T1 for simulation {i:03d}, T1={ext_T1s:03d}: {e}")

            del data_varC2

        elif in_T2 in ('y', 'Y'):
            # T1 already exists on disk, load it and compute T2
            for ext_T1s in range(T1_ini, T1_fin + 1):
                try:
                    t1_path = f'I001_Results/DATA_PICK_{i:03}_T1_{ext_T1s:03d}.pkl'
                    data_T1 = _load_pickle_or_skip(t1_path, f"T2 for simulation {i:03d}, T1={ext_T1s:03d}")
                    if data_T1 is None:
                        continue
                    data_T2 = create_PKL_T2(
                        data_T1,
                        sim_num=i,
                        output_path=f'I001_Results/DATA_PICK_{i:03d}_T2_{ext_T1s:03d}.pkl',
                        w_param_sets= [(1,1,1,1),(1, 1, 2, 2)]
                    )
                    del data_T1, data_T2
                except Exception as e:
                    print(f"Error processing T2 for simulation {i:03d}, T1={ext_T1s:03d}: {e}")


        if in_J1 in ('y', 'Y'):
            data_varB = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_B.pkl', f"J1 for simulation {i:03d}")
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"J1 for simulation {i:03d}")
            if data_varB is None or data_varC2 is None:
                print(f"Skipping J1 stage for simulation {i:03d}: missing B/C2 inputs; continuing with remaining stages")
            else:
                # Resolve graph file path from the simulation JSON
                mesh_prefix = _mesh_prefix_for_sim(i)


                for ext_Js in range(J_ini, J_fin + 1):

                    try:
                        graph_path = _mesh_artifact_path(mesh_prefix, "J", ext_Js, "graph.json")

                        data_J1 = create_PKL_J1(
                            data_varB, data_varC2, graph_path,
                            sim_num=i,
                        )

                        pickle_file = f'I001_Results/DATA_PICK_{i:03}_J1_{ext_Js:03d}.pkl'
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(data_J1, f)

                        if in_J2 in ('y', 'Y'):
                            data_J2 = create_PKL_J2(data_J1, sim_num=i)

                            pickle_file = f'I001_Results/DATA_PICK_{i:03}_J2_{ext_Js:03d}.pkl'
                            with open(pickle_file, 'wb') as f:
                                pickle.dump(data_J2, f)

                            del data_J2

                        del data_J1
                    except Exception as e:
                        print(f"Error processing J1 for simulation {i:03d}, J={ext_Js:03d}: {e}")

                del data_varB, data_varC2

        elif in_J2 in ('y', 'Y'):
            # J1 already exists on disk, load it
            for ext_Js in range(J_ini, J_fin + 1):

                try:

                    j1_path = f'I001_Results/DATA_PICK_{i:03}_J1_{ext_Js:03d}.pkl'
                    data_J1 = _load_pickle_or_skip(j1_path, f"J2 for simulation {i:03d}, J={ext_Js:03d}")
                    if data_J1 is None:
                        continue
                    data_J2 = create_PKL_J2(data_J1, sim_num=i)
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_J2_{ext_Js:03d}.pkl'
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(data_J2, f)

                    del data_J1, data_J2
                except Exception as e:
                    print(f"Error processing J2 for simulation {i:03d}, J={ext_Js:03d}: {e}")


        if in_J3 in ('y', 'Y'):
            for ext_Js in range(J_ini, J_fin + 1):

                try:
                    j2_path = f"I001_Results/DATA_PICK_{i:03}_J2_{ext_Js:03d}.pkl"
                    data_J2 = _load_pickle_or_skip(j2_path, f"J3 for simulation {i:03d}, J={ext_Js:03d}")
                    if data_J2 is None:
                        continue

                    pkl_J3 = create_PKL_G2_exact(data_J2, n_workers=n_workers, max_memory_gb=max_memory_gb, algorithm=J_alg)

                    alg_suffix = '_BFS' if J_alg == 'bfs' else ''
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_J3{alg_suffix}_{ext_Js:03d}.pkl'

                    with open(pickle_file, 'wb') as f:
                        pickle.dump(pkl_J3, f)
                    del pkl_J3

                except Exception as e:
                    print(f"Error processing J3 for simulation {i:03d}, J={ext_Js:03d}: {e}")





        if in_H1 in ('y', 'Y'):
            data_varB = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_B.pkl', f"H1 for simulation {i:03d}")
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"H1 for simulation {i:03d}")
            if data_varB is None or data_varC2 is None:
                print(f"Skipping H1 stage for simulation {i:03d}: missing B/C2 inputs; continuing with remaining stages")
            else:
                # Resolve graph file path from the simulation JSON
                mesh_prefix = _mesh_prefix_for_sim(i)


                for ext_Hs in range(H_ini, H_fin + 1):

                    try:
                        graph_path = _mesh_artifact_path(mesh_prefix, "H", ext_Hs, "grid.json")

                        data_H1 = create_PKL_J1(
                            data_varB, data_varC2, graph_path,
                            sim_num=i,
                        )

                        pickle_file = f'I001_Results/DATA_PICK_{i:03}_H1_{ext_Hs:03d}.pkl'
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(data_H1, f)

                        if in_H2 in ('y', 'Y'):
                            data_H2 = create_PKL_H2(data_H1, sim_num=i)

                            pickle_file = f'I001_Results/DATA_PICK_{i:03}_H2_{ext_Hs:03d}.pkl'
                            with open(pickle_file, 'wb') as f:
                                pickle.dump(data_H2, f)

                            del data_H2

                        del data_H1

                    except Exception as e:
                        print(f"Error processing H1 for simulation {i:03d}, H={ext_Hs:03d}: {e}")

                del data_varB, data_varC2

        elif in_H2 in ('y', 'Y'):
            # J1 already exists on disk, load it
            for ext_Hs in range(H_ini, H_fin + 1):

                try:

                    h1_path = f'I001_Results/DATA_PICK_{i:03}_H1_{ext_Hs:03d}.pkl'
                    data_H1 = _load_pickle_or_skip(h1_path, f"H2 for simulation {i:03d}, H={ext_Hs:03d}")
                    if data_H1 is None:
                        continue
                    data_H2 = create_PKL_H2(data_H1, sim_num=i)
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_H2_{ext_Hs:03d}.pkl'
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(data_H2, f)

                    del data_H1, data_H2
                except Exception as e:
                    print(f"Error processing H2 for simulation {i:03d}, H={ext_Hs:03d}: {e}")


        if in_H3 in ('y', 'Y'):
            for ext_Hs in range(H_ini, H_fin + 1):

                try:
                    h2_path = f"I001_Results/DATA_PICK_{i:03}_H2_{ext_Hs:03d}.pkl"
                    data_H2 = _load_pickle_or_skip(h2_path, f"H3 for simulation {i:03d}, H={ext_Hs:03d}")
                    if data_H2 is None:
                        continue

                    pkl_H3 = create_PKL_G2_exact(data_H2, n_workers=n_workers, max_memory_gb=max_memory_gb, algorithm=H_alg)

                    alg_suffix = '_BFS' if H_alg == 'bfs' else ''
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_H3{alg_suffix}_{ext_Hs:03d}.pkl'

                    with open(pickle_file, 'wb') as f:
                        pickle.dump(pkl_H3, f)
                    del pkl_H3

                except Exception as e:
                    print(f"Error processing H3 for simulation {i:03d}, H={ext_Hs:03d}: {e}")




        if in_I1 in ('y', 'Y'):
            data_varB = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_B.pkl', f"I1 for simulation {i:03d}")
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"I1 for simulation {i:03d}")
            if data_varB is None or data_varC2 is None:
                print(f"Skipping I1 stage for simulation {i:03d}: missing B/C2 inputs; continuing with remaining stages")
            else:
                # Resolve graph file path from the simulation JSON
                mesh_prefix = _mesh_prefix_for_sim(i)


                for ext_Is in range(I_ini, I_fin + 1):

                    try:
                        graph_path = _mesh_artifact_path(mesh_prefix, "I", ext_Is, "gridhex.json")

                        data_I1 = create_PKL_J1(
                            data_varB, data_varC2, graph_path,
                            sim_num=i,
                        )

                        pickle_file = f'I001_Results/DATA_PICK_{i:03}_I1_{ext_Is:03d}.pkl'
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(data_I1, f)

                        if in_I2 in ('y', 'Y'):
                            data_I2 = create_PKL_H2(data_I1, sim_num=i)

                            pickle_file = f'I001_Results/DATA_PICK_{i:03}_I2_{ext_Is:03d}.pkl'
                            with open(pickle_file, 'wb') as f:
                                pickle.dump(data_I2, f)

                            del data_I2

                        del data_I1

                    except Exception as e:
                        print(f"Error processing I1 for simulation {i:03d}, I={ext_Is:03d}: {e}")

                del data_varB, data_varC2

        elif in_I2 in ('y', 'Y'):
            # J1 already exists on disk, load it
            for ext_Is in range(I_ini, I_fin + 1):

                try:

                    i1_path = f'I001_Results/DATA_PICK_{i:03}_I1_{ext_Is:03d}.pkl'
                    data_I1 = _load_pickle_or_skip(i1_path, f"I2 for simulation {i:03d}, I={ext_Is:03d}")
                    if data_I1 is None:
                        continue
                    data_I2 = create_PKL_H2(data_I1, sim_num=i)
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_I2_{ext_Is:03d}.pkl'
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(data_I2, f)

                    del data_I1, data_I2
                except Exception as e:
                    print(f"Error processing I2 for simulation {i:03d}, I={ext_Is:03d}: {e}")


        if in_I3 in ('y', 'Y'):
            for ext_Is in range(I_ini, I_fin + 1):

                try:
                    i2_path = f"I001_Results/DATA_PICK_{i:03}_I2_{ext_Is:03d}.pkl"
                    data_I2 = _load_pickle_or_skip(i2_path, f"I3 for simulation {i:03d}, I={ext_Is:03d}")
                    if data_I2 is None:
                        continue

                    pkl_I3 = create_PKL_G2_exact(data_I2, n_workers=n_workers, max_memory_gb=max_memory_gb, algorithm=I_alg)

                    alg_suffix = '_BFS' if I_alg == 'bfs' else ''
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_I3{alg_suffix}_{ext_Is:03d}.pkl'

                    with open(pickle_file, 'wb') as f:
                        pickle.dump(pkl_I3, f)
                    del pkl_I3

                except Exception as e:
                    print(f"Error processing I3 for simulation {i:03d}, I={ext_Is:03d}: {e}")




        if in_K1 in ('y', 'Y'):
            data_varB = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_B.pkl', f"K1 for simulation {i:03d}")
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"K1 for simulation {i:03d}")
            if data_varB is None or data_varC2 is None:
                print(f"Skipping K1 stage for simulation {i:03d}: missing B/C2 inputs; continuing with remaining stages")
            else:
                # Resolve mesh prefix from the simulation JSON
                mesh_prefix = _mesh_prefix_for_sim(i)

                for ext_Ks in range(K_ini, K_fin + 1):

                    try:
                        gridhex_path = _mesh_artifact_path(mesh_prefix, "K", ext_Ks, "gridhex.json")

                        data_K1 = create_PKL_K1(
                            data_varB, data_varC2, gridhex_path,
                            sim_num=i,
                            create_bars_2=True,
                        )

                        pickle_file = f'I001_Results/DATA_PICK_{i:03}_K1_{ext_Ks:03d}.pkl'
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(data_K1, f)

                        if in_K2 in ('y', 'Y'):
                            data_K2 = create_PKL_K2(data_K1, sim_num=i)

                            pickle_file = f'I001_Results/DATA_PICK_{i:03}_K2_{ext_Ks:03d}.pkl'
                            with open(pickle_file, 'wb') as f:
                                pickle.dump(data_K2, f)

                            del data_K2

                        del data_K1

                    except Exception as e:
                        print(f"Error processing K1 for simulation {i:03d}, K={ext_Ks:03d}: {e}")

                del data_varB, data_varC2

        elif in_K2 in ('y', 'Y'):
            # K1 already exists on disk, load it
            for ext_Ks in range(K_ini, K_fin + 1):

                try:

                    k1_path = f'I001_Results/DATA_PICK_{i:03}_K1_{ext_Ks:03d}.pkl'
                    data_K1 = _load_pickle_or_skip(k1_path, f"K2 for simulation {i:03d}, K={ext_Ks:03d}")
                    if data_K1 is None:
                        continue
                    data_K2 = create_PKL_K2(data_K1, sim_num=i)
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_K2_{ext_Ks:03d}.pkl'
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(data_K2, f)

                    del data_K1, data_K2
                except Exception as e:
                    print(f"Error processing K2 for simulation {i:03d}, K={ext_Ks:03d}: {e}")


        if in_K3 in ('y', 'Y'):
            for ext_Ks in range(K_ini, K_fin + 1):

                try:
                    k2_path = f"I001_Results/DATA_PICK_{i:03}_K2_{ext_Ks:03d}.pkl"
                    data_K2 = _load_pickle_or_skip(k2_path, f"K3 for simulation {i:03d}, K={ext_Ks:03d}")
                    if data_K2 is None:
                        continue

                    pkl_K3 = create_PKL_G2_exact(data_K2, n_workers=n_workers, max_memory_gb=max_memory_gb, algorithm=K_alg)

                    alg_suffix = '_BFS' if K_alg == 'bfs' else ''
                    pickle_file = f'I001_Results/DATA_PICK_{i:03}_K3{alg_suffix}_{ext_Ks:03d}.pkl'

                    with open(pickle_file, 'wb') as f:
                        pickle.dump(pkl_K3, f)
                    del pkl_K3

                except Exception as e:
                    print(f"Error processing K3 for simulation {i:03d}, K={ext_Ks:03d}: {e}")




        if in_Q1 in ('y', 'Y'):
            data_varC2 = _load_pickle_or_skip(f'I001_Results/DATA_PICK_{i:03}_C2.pkl', f"Q1 for simulation {i:03d}")
            if data_varC2 is None:
                print(f"Skipping Q1 stage for simulation {i:03d}: missing C2 input; continuing with remaining stages")
            else:
                mesh_prefix = _mesh_prefix_for_sim(i)

                for ext_Qs in range(Q_ini, Q_fin + 1):
                    try:
                        quad_file = _mesh_artifact_path(mesh_prefix, "Q", ext_Qs, "quad")

                        data_Q1 = create_PKL_Q1(
                            data_varC2, quad_file,
                            sim_num=i,
                            output_path=f'I001_Results/DATA_PICK_{i:03}_Q1_{ext_Qs:03d}.pkl',
                        )

                        if in_Q2 in ('y', 'Y'):
                            try:
                                data_Q2 = create_PKL_Q2(
                                    data_Q1,
                                    sim_num=i,
                                    output_path=f'I001_Results/DATA_PICK_{i:03d}_Q2_{ext_Qs:03d}.pkl',
                                    w_param_sets=[(1, 1, 1, 1), (1, 1, 2, 2)],
                                )
                                del data_Q2
                            except Exception as e:
                                print(f"Error processing Q2 for simulation {i:03d}, Q={ext_Qs:03d}: {e}")

                        del data_Q1
                    except Exception as e:
                        print(f"Error processing Q1 for simulation {i:03d}, Q={ext_Qs:03d}: {e}")

                del data_varC2

        elif in_Q2 in ('y', 'Y'):
            # Q1 already exists on disk, load it and compute Q2
            for ext_Qs in range(Q_ini, Q_fin + 1):
                try:
                    q1_path = f'I001_Results/DATA_PICK_{i:03}_Q1_{ext_Qs:03d}.pkl'
                    data_Q1 = _load_pickle_or_skip(q1_path, f"Q2 for simulation {i:03d}, Q={ext_Qs:03d}")
                    if data_Q1 is None:
                        continue
                    data_Q2 = create_PKL_Q2(
                        data_Q1,
                        sim_num=i,
                        output_path=f'I001_Results/DATA_PICK_{i:03d}_Q2_{ext_Qs:03d}.pkl',
                        w_param_sets=[(1, 1, 1, 1), (1, 1, 2, 2)],
                    )
                    del data_Q1, data_Q2
                except Exception as e:
                    print(f"Error processing Q2 for simulation {i:03d}, Q={ext_Qs:03d}: {e}")


        if delete_csv in ('y','Y'):
            if os.path.exists(csv_file):
                os.remove(csv_file)
                print(f"{csv_file} has been deleted.")
            else:
                print(f"{csv_file} not found.")
    except Exception as e:
        print(f"An error occurred while processing simulation {i:03d}: {e}")


if __name__ == "__main__":
    A = int(input('First simulation to reduce: '))
    B = int(input('Last simulation to reduce: '))

    in_A = input('Output file A? (y/n): ') or 'y'
    in_A2 = input('Output file A2? (y/n): ') or 'y'
    in_B = input('Output file B? (y/n): ') or 'y'
    in_C = input('Output file C? (y/n): ') or 'y'
    in_C2 = input('Output file C2? (y/n): ') or 'y'
    in_D = input('Output file D? (y/n): ') or 'y'
    in_T1 = input('Output file T1? (y/n): ') or 'n'
    in_T2 = input('Output file T2? (y/n): ') or 'n'
    T1_ini = int(input('Initial T1 index: ') or '0')
    T1_fin = int(input('Final T1 index: ') or '0')
    in_J1 = input('Output file J1? (y/n): ') or 'y'
    in_J2 = input('Output file J2? (y/n): ') or 'y'
    in_J3 = input('Output file J3? (y/n): ') or 'y'
    J_ini = input('Initial J? (y/n): ') or '0'
    J_fin = input('Final J? (y/n): ') or '0'
    J_alg = input('Algorithm for J3? (1=default, 2=BFS, default=1): ') or '1'
    in_H1 = input('Output file H1? (y/n): ') or 'y'
    in_H2 = input('Output file H2? (y/n): ') or 'y'
    in_H3 = input('Output file H3? (y/n): ') or 'y'
    H_ini = input('Initial H? (y/n): ') or '0'
    H_fin = input('Final H? (y/n): ') or '0'
    H_alg = input('Algorithm for H3? (1=default, 2=BFS, default=1): ') or '1'
    in_I1 = input('Output file I1? (y/n): ') or 'y'
    in_I2 = input('Output file I2? (y/n): ') or 'y'
    in_I3 = input('Output file I3? (y/n): ') or 'y'
    I_ini = input('Initial I? (y/n): ') or '0'
    I_fin = input('Final I? (y/n): ') or '0'
    I_alg = input('Algorithm for I3? (1=default, 2=BFS, default=1): ') or '1'
    in_K1 = input('Output file K1? (y/n): ') or 'y'
    in_K2 = input('Output file K2? (y/n): ') or 'y'
    in_K3 = input('Output file K3? (y/n): ') or 'y'
    K_ini = input('Initial K? (y/n): ') or '0'
    K_fin = input('Final K? (y/n): ') or '0'
    K_alg = input('Algorithm for K3? (1=default, 2=BFS, default=1): ') or '1'
    in_Q1 = input('Output file Q1? (y/n): ') or 'n'
    in_Q2 = input('Output file Q2? (y/n): ') or 'n'
    Q_ini = input('Initial Q index: ') or '0'
    Q_fin = input('Final Q index: ') or '0'
    delete_csv = input('Delete csv? (y/n): ') or 'n'
    n_workers_str = input('Number of parallel workers for G2_exact (default=auto): ') or '0'
    max_memory_gb_str = input('Max memory in GB for G2_exact (default=auto): ') or '0'

    n_workers = int(n_workers_str) if int(n_workers_str) > 0 else None
    max_memory_gb = float(max_memory_gb_str) if float(max_memory_gb_str) > 0 else None

    J_ini = int(J_ini)
    J_fin = int(J_fin)
    H_ini = int(H_ini)
    H_fin = int(H_fin)
    I_ini = int(I_ini)
    I_fin = int(I_fin)
    K_ini = int(K_ini)
    K_fin = int(K_fin)
    Q_ini = int(Q_ini)
    Q_fin = int(Q_fin)

    J_alg = None if J_alg == '1' else 'bfs'
    H_alg = None if H_alg == '1' else 'bfs'
    I_alg = None if I_alg == '1' else 'bfs'
    K_alg = None if K_alg == '1' else 'bfs'

    # Prepare arguments for multiprocessing
    args_list = [(i, in_A, in_A2, in_B, in_C, in_C2, in_D, in_T1, in_T2, T1_ini, T1_fin, in_J1, in_J2, in_J3, J_ini, J_fin, J_alg, in_H1, in_H2, in_H3, H_ini, H_fin, H_alg, in_I1, in_I2, in_I3, I_ini, I_fin, I_alg, in_K1, in_K2, in_K3, K_ini, K_fin, K_alg, in_Q1, in_Q2, Q_ini, Q_fin, delete_csv, n_workers, max_memory_gb) for i in range(A, B + 1)]

    # Use multiprocessing to process simulations in parallel
    with multiprocessing.Pool() as pool:
        pool.map(process_simulation, args_list)
