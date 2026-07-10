#!/usr/bin/env python
"""Move simulation data (E001_Simulations folders + I001_Results files) to another disk.

Usage:
    python move_simulations.py 1000 1001 1002      # exactly these 3 sims
    python move_simulations.py 0 999                # every sim from 0 to 999 inclusive
    python move_simulations.py 1000 --dest-sim /mnt/other_disk/Results --dry-run

Note: passing exactly TWO sim numbers is interpreted as an inclusive range
(start end), not as "these two sims". Pass 1 or 3+ numbers for an explicit list.

By default, moves:
  - E001_Simulations/SIM_{n}                -> /data/Franco/FOAM_V03_Results/SIM_{n}
  - I001_Results/** matching SIM {n}        -> /data/Franco/FOAM_V03_I001_Results/**
    (DATA_PICK_{n}_*.pkl, RES_SIM_{n}.csv, OBJ_files/SIM_{n}.json,
     finished_simulations/SIM_{n}.inp, etc. - relative subfolder structure is preserved)

Matching is done on the LEADING digit-run of the filename/dirname (optionally
zero-padded), which is always the sim number per the naming conventions above
(e.g. DATA_PICK_{n}_T2_001.pkl - the "001" suffix is a type/step id, not a sim
number, and is correctly ignored). So sim 10 matches "SIM_010" /
"DATA_PICK_0010_T2_001.pkl" but not "SIM_100", "SIM_1000", or
"DATA_PICK_0001_T2_010.pkl".

Pass --reverse to move files back from the destination to the original
location (source/dest directories are swapped).

Pass --csv-only to move only *.csv files (e.g. RES_SIM_{n}.csv) from
I001_Results, skipping E001_Simulations dirs and all non-csv result files.
"""
import argparse
import os
import re
import shutil
from pathlib import Path

DEFAULT_DEST_SIM = "/data/Franco/FOAM_V03_Results"
DEFAULT_DEST_RESULTS = "/data/Franco/FOAM_V03_I001_Results"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SIM_DIR = REPO_ROOT / "E001_Simulations"
DEFAULT_RESULTS_DIR = REPO_ROOT / "I001_Results"


LEADING_NUMBER_RE = re.compile(r'\d+')


def leading_number(name):
    """Return the integer value of the first digit-run in name, or None."""
    m = LEADING_NUMBER_RE.search(name)
    return int(m.group()) if m else None


def matches_sim(name, sim):
    return leading_number(name) == sim


def move_path(src, dest, dry_run):
    if dest.exists():
        print(f"  SKIP (already exists at destination): {dest}")
        return
    print(f"  {src} -> {dest}")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))


def move_simulation_dirs(sim, sim_dir, dest_sim_dir, dry_run):
    moved = 0
    if not sim_dir.is_dir():
        return moved
    for entry in sorted(sim_dir.iterdir()):
        if entry.is_dir() and entry.name.startswith("SIM_") and matches_sim(entry.name, sim):
            move_path(entry, dest_sim_dir / entry.name, dry_run)
            moved += 1
    return moved


def move_results_files(sim, results_dir, dest_results_dir, dry_run, csv_only=False):
    moved = 0
    if not results_dir.is_dir():
        return moved
    for root, _dirs, files in os.walk(results_dir):
        root_path = Path(root)
        rel_root = root_path.relative_to(results_dir)
        for fname in sorted(files):
            if csv_only and not fname.endswith(".csv"):
                continue
            if matches_sim(fname, sim):
                src = root_path / fname
                dest = dest_results_dir / rel_root / fname
                move_path(src, dest, dry_run)
                moved += 1
    return moved


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sims", nargs="+", type=int,
                         help="Simulation numbers to move (e.g. 1000 1001 1002). "
                              "Exactly two numbers is treated as an inclusive range (start end).")
    parser.add_argument("--sim-dir", type=Path, default=DEFAULT_SIM_DIR,
                         help=f"Source E001_Simulations dir (default: {DEFAULT_SIM_DIR})")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR,
                         help=f"Source I001_Results dir (default: {DEFAULT_RESULTS_DIR})")
    parser.add_argument("--dest-sim", type=Path, default=Path(DEFAULT_DEST_SIM),
                         help=f"Destination for simulation folders (default: {DEFAULT_DEST_SIM})")
    parser.add_argument("--dest-results", type=Path, default=Path(DEFAULT_DEST_RESULTS),
                         help=f"Destination for I001_Results files (default: {DEFAULT_DEST_RESULTS})")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be moved without moving anything")
    parser.add_argument("--reverse", action="store_true",
                         help="Move files back from the destination to the original source location "
                              "(swaps --sim-dir/--dest-sim and --results-dir/--dest-results)")
    parser.add_argument("--csv-only", action="store_true",
                         help="Only move *.csv result files (skips E001_Simulations dirs and non-csv results)")
    args = parser.parse_args()

    if len(args.sims) == 2:
        start, end = sorted(args.sims)
        sims = list(range(start, end + 1))
        print(f"Interpreting '{args.sims[0]} {args.sims[1]}' as inclusive range {start}..{end} "
              f"({len(sims)} sims).\n")
    else:
        sims = args.sims

    if args.reverse:
        src_sim, dst_sim = args.dest_sim, args.sim_dir
        src_results, dst_results = args.dest_results, args.results_dir
        print(f"Reverse mode: moving sims from {src_sim} back to {dst_sim}, "
              f"and results from {src_results} back to {dst_results}\n")
    else:
        src_sim, dst_sim = args.sim_dir, args.dest_sim
        src_results, dst_results = args.results_dir, args.dest_results

    if args.csv_only:
        print("CSV-only mode: skipping E001_Simulations dirs, moving only *.csv result files.\n")

    for sim in sims:
        print(f"=== SIM {sim} ===")
        n1 = 0 if args.csv_only else move_simulation_dirs(sim, src_sim, dst_sim, args.dry_run)
        n2 = move_results_files(sim, src_results, dst_results, args.dry_run, csv_only=args.csv_only)
        if n1 == 0 and n2 == 0:
            print(f"  Nothing found for SIM {sim}")

    if args.dry_run:
        print("\nDry run - nothing was actually moved.")


if __name__ == "__main__":
    main()
