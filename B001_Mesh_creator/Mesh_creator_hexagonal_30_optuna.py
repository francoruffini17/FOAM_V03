import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import optuna
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Optuna is not installed. Install it first, then rerun:\n"
        "  python3 -m pip install optuna\n"
        "  python3 B001_Mesh_creator/Mesh_creator_hexagonal_30_optuna.py"
    ) from exc

from A001_functions.Hex_5 import MeshConfig, create_hexagonal_mesh_2


# TARGET_NODES = [5_000, 10_000, 20_000, 40_000, 80_000]
# TARGET_REL_TOL = 0.01
# N_TRIALS_PER_BATCH = 40
# MAX_TRIALS_PER_TARGET = 100
# INITIAL_REFERENCE_MESH_SIZES = [0.012, 0.008, 0.0055, 0.00385, 0.0026]
# INITIAL_REFERENCE_NODE_COUNTS = [5680, 10846, 20982, 41312, 86874]
# MIN_MESH_SIZES = [ 0.01, 0.007, 0.0053, 0.0037, 0.0025]
# MAX_MESH_SIZES = [ 0.015, 0.0085, 0.006, 0.004, 0.0028]
# OUTPUT_TEMPLATE = "C001_Mesh_files/A030_{target_k:03d}k.mesh.json"


TARGET_NODES = [160_000]
TARGET_REL_TOL = 0.01
N_TRIALS_PER_BATCH = 40
MAX_TRIALS_PER_TARGET = 100
INITIAL_REFERENCE_MESH_SIZES = [0.0019]
INITIAL_REFERENCE_NODE_COUNTS = [159109]
MIN_MESH_SIZES = [0.0018]
MAX_MESH_SIZES = [0.002]
OUTPUT_TEMPLATE = "C001_Mesh_files/A030_{target_k:03d}k.mesh.json"


cfg = MeshConfig(
    domain_size=1.0,
    n_holes_width=10,
    porosity=0.572,
    edge_left=0.01,
    edge_right=0.01,
    edge_bottom=0.01,
    edge_top=0.01,
)


mesh_cache = {}


def build_mesh(mesh_size, filepath=None, export_mesh=False):
    _, mesh = create_hexagonal_mesh_2(
        config=cfg,
        filepath=filepath or "Temp/optuna_A030/not_exported.mesh.json",
        export_mesh=export_mesh,
        export_vtk=export_mesh,
        show_plot=False,
        show_periodic_matching=False,
        allow_cut_left=False,
        allow_cut_right=False,
        allow_cut_bottom=False,
        allow_cut_top=False,
        element_type="BOTH",
        mesh_size=mesh_size,
        periodic="both",
    )
    return mesh


def evaluate_mesh_size(mesh_size):
    key = round(float(mesh_size), 10)
    if key in mesh_cache:
        return mesh_cache[key]

    mesh = build_mesh(mesh_size, export_mesh=False)
    n_nodes = mesh.n_nodes
    result = {
        "mesh_size": float(mesh_size),
        "n_nodes": int(n_nodes),
        "n_elements": int(mesh.n_elements),
    }
    mesh_cache[key] = result
    return result


def initial_mesh_size_guess(
    target_nodes,
    initial_reference_mesh_size,
    initial_reference_nodes,
):
    return initial_reference_mesh_size * (
        initial_reference_nodes / target_nodes
    ) ** 0.5


def find_mesh_size_bounds(
    target_nodes,
    min_mesh_size,
    max_mesh_size,
    initial_reference_mesh_size,
    initial_reference_nodes,
):
    guess = max(
        min_mesh_size,
        min(
            max_mesh_size,
            initial_mesh_size_guess(
                target_nodes,
                initial_reference_mesh_size,
                initial_reference_nodes,
            ),
        ),
    )
    low = max(min_mesh_size, guess / 1.5)
    high = min(max_mesh_size, guess * 1.5)

    low_eval = evaluate_mesh_size(low)
    high_eval = evaluate_mesh_size(high)

    # Smaller mesh_size should produce more nodes. Expand until target is
    # bracketed, or until the hard mesh-size limits are reached.
    for _ in range(12):
        has_upper_node_count = low_eval["n_nodes"] >= target_nodes
        has_lower_node_count = high_eval["n_nodes"] <= target_nodes
        if has_upper_node_count and has_lower_node_count:
            return low, high

        if not has_upper_node_count:
            if low <= min_mesh_size:
                return low, high
            high = low
            high_eval = low_eval
            low = max(min_mesh_size, low / 1.5)
            low_eval = evaluate_mesh_size(low)
            continue

        if not has_lower_node_count:
            if high >= max_mesh_size:
                return low, high
            low = high
            low_eval = high_eval
            high = min(max_mesh_size, high * 1.5)
            high_eval = evaluate_mesh_size(high)

    return low, high


class StopWhenWithinTolerance:
    def __init__(self, target_nodes):
        self.target_nodes = target_nodes

    def __call__(self, study, trial):
        best_nodes = study.best_trial.user_attrs.get("n_nodes")
        if best_nodes is None:
            return
        rel_error = abs(best_nodes - self.target_nodes) / self.target_nodes
        if rel_error <= TARGET_REL_TOL:
            study.stop()


def optimize_target(
    target_nodes,
    min_mesh_size,
    max_mesh_size,
    initial_reference_mesh_size,
    initial_reference_nodes,
):
    mesh_size_low, mesh_size_high = find_mesh_size_bounds(
        target_nodes,
        min_mesh_size,
        max_mesh_size,
        initial_reference_mesh_size,
        initial_reference_nodes,
    )
    sampler = optuna.samplers.TPESampler(seed=42 + target_nodes)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    guess = max(
        mesh_size_low,
        min(
            mesh_size_high,
            initial_mesh_size_guess(
                target_nodes,
                initial_reference_mesh_size,
                initial_reference_nodes,
            ),
        ),
    )
    for mesh_size in (mesh_size_low, guess, mesh_size_high):
        study.enqueue_trial({"mesh_size": mesh_size})

    def objective(trial):
        mesh_size = trial.suggest_float("mesh_size", mesh_size_low, mesh_size_high)
        result = evaluate_mesh_size(mesh_size)
        n_nodes = result["n_nodes"]
        n_elements = result["n_elements"]
        rel_error = abs(n_nodes - target_nodes) / target_nodes

        trial.set_user_attr("n_nodes", n_nodes)
        trial.set_user_attr("n_elements", n_elements)
        trial.set_user_attr("rel_error", rel_error)
        print(
            f"target={target_nodes:6d} trial={trial.number:03d} "
            f"mesh_size={mesh_size:.8f} nodes={n_nodes:6d} "
            f"rel_error={rel_error:.4%}"
        )
        return rel_error

    print(
        f"\nOptimizing target={target_nodes} nodes "
        f"with mesh_size bounds [{mesh_size_low:.8f}, {mesh_size_high:.8f}]"
    )
    while len(study.trials) < MAX_TRIALS_PER_TARGET:
        remaining = MAX_TRIALS_PER_TARGET - len(study.trials)
        study.optimize(
            objective,
            n_trials=min(N_TRIALS_PER_BATCH, remaining),
            callbacks=[StopWhenWithinTolerance(target_nodes)],
        )

        best_rel_error = study.best_trial.user_attrs["rel_error"]
        if best_rel_error <= TARGET_REL_TOL:
            break

        print(
            f"Continuing target={target_nodes}: best rel_error is "
            f"{best_rel_error:.4%}, tolerance is {TARGET_REL_TOL:.2%}"
        )

    best = study.best_trial
    best_mesh_size = best.params["mesh_size"]
    best_nodes = best.user_attrs["n_nodes"]
    best_rel_error = best.user_attrs["rel_error"]

    output_path = OUTPUT_TEMPLATE.format(target_k=target_nodes // 1000)
    final_mesh = build_mesh(best_mesh_size, filepath=output_path, export_mesh=True)

    # The exported mesh should match the trial, but report the final count in
    # case downstream export options ever change.
    final_rel_error = abs(final_mesh.n_nodes - target_nodes) / target_nodes
    result = {
        "target_nodes": target_nodes,
        "mesh_size": best_mesh_size,
        "trial_nodes": best_nodes,
        "final_nodes": final_mesh.n_nodes,
        "final_elements": final_mesh.n_elements,
        "trial_rel_error": best_rel_error,
        "final_rel_error": final_rel_error,
        "output_path": output_path,
    }

    print(
        f"Best for target={target_nodes}: mesh_size={best_mesh_size:.9f}, "
        f"nodes={final_mesh.n_nodes}, rel_error={final_rel_error:.4%}, "
        f"output={output_path}"
    )
    return result


def main():
    list_lengths = {
        len(TARGET_NODES),
        len(MIN_MESH_SIZES),
        len(MAX_MESH_SIZES),
        len(INITIAL_REFERENCE_MESH_SIZES),
        len(INITIAL_REFERENCE_NODE_COUNTS),
    }
    if len(list_lengths) != 1:
        raise SystemExit(
            "TARGET_NODES, MIN_MESH_SIZES, MAX_MESH_SIZES, "
            "INITIAL_REFERENCE_MESH_SIZES, and INITIAL_REFERENCE_NODE_COUNTS "
            "must have the same length."
        )

    results = []
    for (
        target_nodes,
        min_mesh_size,
        max_mesh_size,
        initial_reference_mesh_size,
        initial_reference_nodes,
    ) in zip(
        TARGET_NODES,
        MIN_MESH_SIZES,
        MAX_MESH_SIZES,
        INITIAL_REFERENCE_MESH_SIZES,
        INITIAL_REFERENCE_NODE_COUNTS,
    ):
        results.append(
            optimize_target(
                target_nodes,
                min_mesh_size,
                max_mesh_size,
                initial_reference_mesh_size,
                initial_reference_nodes,
            )
        )

    print("\nSummary")
    failed = []
    for result in results:
        status = "OK" if result["final_rel_error"] <= TARGET_REL_TOL else "CHECK"
        if status != "OK":
            failed.append(result)
        print(
            f"{status} target={result['target_nodes']:6d} "
            f"mesh_size={result['mesh_size']:.9f} "
            f"nodes={result['final_nodes']:6d} "
            f"rel_error={result['final_rel_error']:.4%} "
            f"file={result['output_path']}"
        )

    if failed:
        failed_targets = ", ".join(str(item["target_nodes"]) for item in failed)
        raise SystemExit(
            f"Targets outside {TARGET_REL_TOL:.2%} tolerance after "
            f"{MAX_TRIALS_PER_TARGET} trials: {failed_targets}"
        )


if __name__ == "__main__":
    main()
