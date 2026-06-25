"""
Compute hole deformation characterization pickles DEFC1 and DEFC2.

DEFC1: per-hole, per-timestep area and aspect ratio (raw + normalized by t0).
DEFC2: cross-hole statistics and localization indices etaC_A and etaC_R.

t0 is the first timestep in the PKL data (start of Step-1, after internal
pressure has been applied).

Usage:
    python -m A001_functions.compute_DEFC <SIM_NUMBER>
"""

import sys
import json
import pickle
import numpy as np


def _shoelace_area(xs, ys):
    n = len(xs)
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(s) / 2.0


def create_PKL_DEFC1(sim_num: int, results_dir: str = "I001_Results",
                     output_path: str = None) -> dict:
    """
    Compute per-hole area and aspect ratio at every timestep for sim_num.

    Requires DATA_PICK_{sim_num}_TP1.pkl (for mesh source path) and
    DATA_PICK_{sim_num}_C.pkl (node coordinates).

    Returns the DEFC1 dict and saves it to disk.
    """
    tp1_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_TP1.pkl"
    with open(tp1_path, "rb") as f:
        tp1 = pickle.load(f)
    mesh_file = tp1["source_file"]

    with open(mesh_file) as f:
        mesh = json.load(f)

    hole_boundary_nodes = mesh["hole_boundary_nodes"]
    n_holes = len(hole_boundary_nodes)

    c_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_C.pkl"
    with open(c_path, "rb") as f:
        c = pickle.load(f)

    t = c["t"]
    n_t = len(t)
    COOR1 = c["COOR1"]
    COOR2 = c["COOR2"]

    # Load displacement (U2 of loading reference point) from A pkl
    a_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_A.pkl"
    with open(a_path, "rb") as f:
        a = pickle.load(f)
    displacement = list(a["U2"]["PERN-9999997"]["9999997"])

    # mesh node list index i (0-based) -> C pkl key str(i+1)
    areas = {}
    ratios = {}

    for h_idx, node_indices in enumerate(hole_boundary_nodes):
        keys = [str(ni + 1) for ni in node_indices]
        xs_t = np.array([[COOR1[k][ti] for k in keys] for ti in range(n_t)])
        ys_t = np.array([[COOR2[k][ti] for k in keys] for ti in range(n_t)])

        hole_areas = np.array([_shoelace_area(xs_t[ti], ys_t[ti]) for ti in range(n_t)])
        width_t  = xs_t.max(axis=1) - xs_t.min(axis=1)
        height_t = ys_t.max(axis=1) - ys_t.min(axis=1)
        hole_ratios = height_t / width_t

        areas[h_idx] = hole_areas
        ratios[h_idx] = hole_ratios

    areas_normalized  = {h: areas[h]  / areas[h][0]  for h in range(n_holes)}
    ratios_normalized = {h: ratios[h] / ratios[h][0] for h in range(n_holes)}

    DEFC1 = {
        "source_file": mesh_file,
        "t": t,
        "displacement": displacement,  # U2 of loading ref point (mm, negative = compression)
        "n_holes": n_holes,
        "areas": areas,
        "ratios": ratios,
        "areas_normalized": areas_normalized,
        "ratios_normalized": ratios_normalized,
    }

    if output_path is None:
        output_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_DEFC1.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(DEFC1, f)
    print(f"PKL_DEFC1 saved to '{output_path}'")

    return DEFC1


def create_PKL_DEFC2(DATA_DEFC1: dict, sim_num: int = None,
                     results_dir: str = "I001_Results",
                     output_path: str = None) -> dict:
    """
    Compute cross-hole statistics and localization indices from DEFC1.

    etaC_A = 1 - std(A_normalized) / stdM
    etaC_R = 1 - std(R_normalized) / stdM
    stdM   = 0.5 * sqrt(n_holes / (n_holes - 1))

    Returns the DEFC2 dict and saves it to disk.
    """
    t            = DATA_DEFC1["t"]
    displacement = DATA_DEFC1["displacement"]
    n_holes      = DATA_DEFC1["n_holes"]

    A_arr = np.array([DATA_DEFC1["areas_normalized"][h]  for h in range(n_holes)])
    R_arr = np.array([DATA_DEFC1["ratios_normalized"][h] for h in range(n_holes)])

    A_std  = A_arr.std(axis=0, ddof=1)
    A_mean = A_arr.mean(axis=0)
    A_min  = A_arr.min(axis=0)
    A_max  = A_arr.max(axis=0)

    R_std  = R_arr.std(axis=0, ddof=1)
    R_mean = R_arr.mean(axis=0)
    R_min  = R_arr.min(axis=0)
    R_max  = R_arr.max(axis=0)

    stdM   = 0.5 * np.sqrt(n_holes / (n_holes - 1))
    etaC_A = 1.0 - A_std / stdM
    etaC_R = 1.0 - R_std / stdM

    DEFC2 = {
        "source_file": DATA_DEFC1["source_file"],
        "t": t,
        "displacement": displacement,
        "n_holes": n_holes,
        "stdM": float(stdM),
        "A_std":  A_std,  "A_mean": A_mean, "A_min": A_min, "A_max": A_max,
        "R_std":  R_std,  "R_mean": R_mean, "R_min": R_min, "R_max": R_max,
        "etaC_A": etaC_A,
        "etaC_R": etaC_R,
    }

    if output_path is None:
        if sim_num is None:
            raise ValueError("Either output_path or sim_num must be provided")
        output_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_DEFC2.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(DEFC2, f)
    print(f"PKL_DEFC2 saved to '{output_path}'")

    return DEFC2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m A001_functions.compute_DEFC <SIM_NUMBER>")
        sys.exit(1)
    sim = int(sys.argv[1])
    data_defc1 = create_PKL_DEFC1(sim)
    create_PKL_DEFC2(data_defc1, sim_num=sim)
