"""
Test create_PKL_J1 on real simulation data (sim_num = 7500).

Loads DATA_B and DATA_C2 from pickle files, reads the graph mesh,
creates the J1 dictionary, saves it, and plots the bars with direction
vectors at several timesteps.
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

from A001_functions.Reduce_resultsV5 import create_PKL_J1
from A001_functions.Hex_5 import read_graph_mesh

SIM_NUM = 7010


def main():
    # --- paths ---------------------------------------------------------------
    pkl_b = f"I001_Results/DATA_PICK_{SIM_NUM}_B.pkl"
    pkl_c2 = f"I001_Results/DATA_PICK_{SIM_NUM}_C2.pkl"
    json_path = f"I001_Results/OBJ_files/SIM_{SIM_NUM}.json"

    for p in [pkl_b, pkl_c2, json_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    # --- load data -----------------------------------------------------------
    print(f"Loading DATA_B from {pkl_b} ...")
    with open(pkl_b, "rb") as f:
        DATA_B = pickle.load(f)

    print(f"Loading DATA_C2 from {pkl_c2} ...")
    with open(pkl_c2, "rb") as f:
        DATA_C2 = pickle.load(f)

    with open(json_path, "r") as f:
        sim_json = json.load(f)

    graph_path = sim_json["input_name"].replace(".mesh.json", "_graph.graph.json")
    print(f"Graph mesh: {graph_path}")

    # --- create J1 -----------------------------------------------------------
    output_pkl = f"I001_Results/DATA_PICK_{SIM_NUM}_J1.pkl"
    print("Creating DATA_J1 (this may take a while) ...")
    J1 = create_PKL_J1(
        DATA_B, DATA_C2, graph_path,
        output_path=output_pkl,
        sim_num=SIM_NUM,
    )
    print(f"J1 saved to {output_pkl}")
    print(f"  timesteps : {len(J1['t'])}")
    print(f"  nodes     : {len(J1['nodes'])}")
    print(f"  bars      : {len(J1['bars_connectivity'])}")

    # --- plot bars with direction vectors at several timesteps ----------------
    n_ti = len(J1["t"])
    timesteps = sorted(set([0, n_ti // 4, n_ti // 2, 3 * n_ti // 4, n_ti - 1]))

    n_plots = len(timesteps)
    fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 5))
    if n_plots == 1:
        axes = [axes]

    unique_bars = sorted(J1["bars_connectivity"].keys())
    cmap = plt.cm.get_cmap("tab20", max(len(unique_bars), 1))

    for ax_idx, ti in enumerate(timesteps):
        ax = axes[ax_idx]
        ax.set_title(f"ti={ti}  t={J1['t'][ti]:.4g}")

        for bar_id in unique_bars:
            color = cmap(bar_id % cmap.N)
            pairs = J1["bars_connectivity"][bar_id]
            normals = J1["bars"][bar_id][ti]["normals"]

            for seg_idx, (ni, nf) in enumerate(pairs):
                p0 = np.array(J1["nodes"][ni][ti])
                p1 = np.array(J1["nodes"][nf][ti])
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=color, linewidth=1.2)

                # Direction arrow at midpoint
                mid = (p0 + p1) / 2
                nx_, ny_ = normals[seg_idx]
                arrow_len = np.linalg.norm(p1 - p0) * 0.25
                ax.annotate(
                    "", xy=mid + np.array([nx_, ny_]) * arrow_len, xytext=mid,
                    arrowprops=dict(arrowstyle="->", color="red", lw=0.8),
                )

        # Draw all nodes
        xs = [J1["nodes"][nidx][ti][0] for nidx in range(len(J1["nodes"]))]
        ys = [J1["nodes"][nidx][ti][1] for nidx in range(len(J1["nodes"]))]
        ax.scatter(xs, ys, c="black", s=8, zorder=5)

        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    fig.suptitle(f"SIM {SIM_NUM} — bar directions at different timesteps", y=1.02)
    fig.tight_layout()

    out_png = f"test_J1_sim{SIM_NUM}_normals.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Plot saved to {out_png}")
    plt.show()


if __name__ == "__main__":
    main()
