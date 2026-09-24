"""Plot and summarize the four near-zero stiffness branches for SIM 5150--5159."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'I001_Results' / 'LITE'
OUTPUT = Path(__file__).resolve().parent


def tracked_branches(values, overlaps):
    """Match nearby eigenmodes between snapshots by eigenvector overlap."""
    n_times, n_modes = values.shape
    indices = np.empty((n_times, n_modes), dtype=np.int16)
    confidence = np.ones((n_times, n_modes), dtype=np.float32)
    indices[0] = np.arange(n_modes)
    for i, overlap in enumerate(overlaps, start=1):
        rows, columns = linear_sum_assignment(-overlap)
        assignment = np.empty(n_modes, dtype=np.int16)
        assignment[rows] = columns
        indices[i] = assignment[indices[i - 1]]
        confidence[i] = overlap[indices[i - 1], indices[i]]
    return values[np.arange(n_times)[:, None], indices], confidence


def main():
    fig, axes = plt.subplots(5, 2, figsize=(15, 18), sharex=True,
                             constrained_layout=True)
    rows = []
    for sim, ax in zip(range(5150, 5160), axes.flat):
        path = RESULTS / f'SIM_{sim}' / 'spectrum.npz'
        ax.set_title(f'SIM {sim}')
        ax.axhline(0, color='black', linewidth=0.7)
        if not path.exists():
            ax.text(0.5, 0.5, 'No spectrum yet', ha='center', va='center',
                    transform=ax.transAxes)
            continue
        with np.load(path, allow_pickle=False) as spectrum:
            time = spectrum['t'].copy()
            values = spectrum['eigenvalues'].copy()
            overlaps = spectrum['mode_overlap'].copy()
        tracked, confidence = tracked_branches(values, overlaps)
        for branch in range(tracked.shape[1]):
            eigenvalue = tracked[:, branch]
            ax.plot(25 * time, eigenvalue, linewidth=0.9,
                    label=f'Initial mode {branch + 1}')
            crossings = np.flatnonzero((eigenvalue[:-1] > 0) &
                                       (eigenvalue[1:] <= 0))
            for i in crossings:
                fraction = eigenvalue[i] / (eigenvalue[i] - eigenvalue[i + 1])
                crossing_time = time[i] + fraction * (time[i + 1] - time[i])
                certainty = float(confidence[i + 1, branch])
                ax.plot(25 * crossing_time, 0, 'o', markersize=4)
                rows.append((sim, branch + 1, crossing_time,
                             0.25 * crossing_time, certainty))
        ax.set_xlim(0, 25)
        ax.grid(alpha=0.2)
        ax.set_ylabel('Eigenvalue near zero')
    for ax in axes[-1]:
        ax.set_xlabel('Nominal compressive strain (%)')
    axes[0, 0].legend(fontsize=7)
    figure_path = OUTPUT / 'SIM_5150s_refined_eigenvalues_vs_strain.png'
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    summary_path = OUTPUT / 'SIM_5150s_refined_crossings.csv'
    with summary_path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('simulation', 'initial_mode', 'crossing_t',
                         'nominal_strain', 'mode_overlap'))
        writer.writerows(rows)
    print(f'Wrote {figure_path} and {summary_path}; {len(rows)} observed crossings')


if __name__ == '__main__':
    main()
