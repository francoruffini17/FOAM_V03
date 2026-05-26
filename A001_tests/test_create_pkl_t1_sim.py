"""
Runner for create_PKL_T1 on real simulation data.

Loads DATA_C2 from a pickle file, reads the triangulation mesh file,
creates the T1 dictionary, saves it, and prints a summary.

Usage
-----
    cd /Disk_F/FOAM_V02
    python A001_tests/test_create_pkl_t1_sim.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pickle
import json
import numpy as np
import matplotlib.pyplot as plt

# --- handle the relative import inside Reduce_resultsV5 ---------------------
import types
_fake_pkg = types.ModuleType("A001_functions")
_fake_pkg.__path__ = [os.path.join(os.path.dirname(__file__), "..", "A001_functions")]
sys.modules.setdefault("A001_functions", _fake_pkg)
_fake_read = types.ModuleType("A001_functions.Read_resultsV5")
sys.modules.setdefault("A001_functions.Read_resultsV5", _fake_read)
# -----------------------------------------------------------------------------

from A001_functions.Reduce_resultsV5 import create_PKL_T1
from A001_functions.mesh_functions import plot_T1_triangulation_mesh

# ---------------------------------------------------------------------------
# Configuration – edit these before running
# ---------------------------------------------------------------------------
SIM_NUM            = 3000           # simulation number
TRIANGULATION_FILE = "mesh_4.tri"   # path to .tri file (relative to workspace root)
OUTPUT_PKL         = None           # None → default: I001_Results/DATA_PICK_{SIM_NUM:03d}_T1.pkl

# ---------------------------------------------------------------------------


def main():
    pkl_c2    = f"I001_Results/DATA_PICK_{SIM_NUM}_C2.pkl"
    json_path = f"I001_Results/OBJ_files/SIM_{SIM_NUM}.json"

    for p in [pkl_c2, json_path, TRIANGULATION_FILE]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    # --- load DATA_C2 --------------------------------------------------------
    print(f"Loading DATA_C2 from {pkl_c2} ...")
    with open(pkl_c2, "rb") as f:
        DATA_C2 = pickle.load(f)

    print(f"  timesteps : {len(DATA_C2['t'])}")
    print(f"  nodes     : {len(DATA_C2['nodes_time'][0])}")
    print(f"  elements  : {len(DATA_C2['elements'])}")

    # --- create PKL_T1 -------------------------------------------------------
    output_pkl = OUTPUT_PKL
    print(f"\nCreating PKL_T1 (sim_num={SIM_NUM}, tri_file={TRIANGULATION_FILE}) ...")
    T1 = create_PKL_T1(
        DATA_C2=DATA_C2,
        triangulation_file=TRIANGULATION_FILE,
        sim_num=SIM_NUM,
        output_path=output_pkl,
    )

    # --- summary -------------------------------------------------------------
    print("\n--- PKL_T1 summary ---")
    print(f"  timesteps              : {len(T1['t'])}")
    print(f"  triangulation nodes    : {len(T1['nodes'][0])}")
    print(f"  triangulation elements : {len(T1['elements'])}")

    areas_t0 = [T1['elements_area'][eid][0] for eid in T1['elements_area']]
    norms_t0 = [T1['elements_area_normalized'][eid][0]
                for eid in T1['elements_area_normalized']]
    print(f"  area at t=0  – min={min(areas_t0):.4e}  max={max(areas_t0):.4e}")
    print(f"  norm area t0 – min={min(norms_t0):.4f}  max={max(norms_t0):.4f}  (should be ~1.0)")

    # --- plot with plot_T1_triangulation_mesh --------------------------------
    n_ti = len(T1['t'])
    timesteps_to_plot = sorted({0, n_ti // 2, n_ti - 1})

    # Example 1: colour-filled by area ratio (default)
    n_plots = len(timesteps_to_plot)
    fig1, axes1 = plt.subplots(1, n_plots, figsize=(5 * n_plots, 5))
    if n_plots == 1:
        axes1 = [axes1]

    for ax, ti in zip(axes1, timesteps_to_plot):
        plot_T1_triangulation_mesh(
            T1, ti,
            ax=ax,
            color_by_area=True,   # fill triangles by A/A₀ (default)
            cmap='RdYlGn',
            vmin=0.8, vmax=1.2,
            show_edges=True,
            edge_color='k',
            linewidth=0.4,
            show_colorbar=True,
        )
    fig1.suptitle('Triangulation – normalised area (A/A₀)', fontsize=12)
    fig1.tight_layout()



    # Example 2: solid colour + undeformed overlay
    fig2, ax2 = plt.subplots(figsize=(7, 7))
    plot_T1_triangulation_mesh(
        T1, n_ti - 1,
        ax=ax2,
        color_by_area=False,      # flat fill
        face_color='lightblue',
        face_alpha=0.6,
        show_undeformed=True,     # grey overlay of ti=0 shape
        show_edges=True,
        show_nodes=True,
        show_node_labels=True,
        node_size=20,
    )
    fig2.suptitle('Triangulation – solid fill + undeformed overlay', fontsize=12)
    fig2.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
