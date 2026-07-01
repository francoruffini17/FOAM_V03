# abq python A001_functions/abq_scriptV20.py <sim_start> <sim_end> [flags]
#
# Flag-based ODB extraction for FOAM_V03. Runs under Abaqus Python 2.7.
# All extraction logic stays in abq_scriptV9.py; this file adds a CLI front-end.

from multiprocessing import Pool, cpu_count
import argparse
import os
import sys

# abq_scriptV9 lives in the same directory; safe to import under abq python.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from abq_scriptV9 import process_simulation


def main():
    parser = argparse.ArgumentParser(
        description='Extract Abaqus ODB history to CSV (FOAM_V03). Runs under abq python.',
        allow_abbrev=False)
    parser.add_argument('sim_start', type=int,
                        help='First simulation number.')
    parser.add_argument('sim_end', type=int,
                        help='Last simulation number (inclusive).')
    parser.add_argument('--results-folder', '-r', default='I001_Results',
                        metavar='PATH',
                        help='Output folder for CSV files (default: I001_Results).')
    parser.add_argument('--delete-odb', action='store_true', default=False,
                        help='Delete ODB file after extraction.')
    parser.add_argument('--workers', type=int, default=None, metavar='N',
                        help='Number of parallel workers (default: auto = cpu_count).')

    # abq python prepends the script path as argv[0].
    args = parser.parse_args(sys.argv[1:])

    simulations = list(range(args.sim_start, args.sim_end + 1))
    if not simulations:
        print("No simulations in range {}-{}.".format(args.sim_start, args.sim_end))
        return

    result_folder = args.results_folder
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    output_draw = False  # FOAM_V03 never writes draw CSV
    delete_odb = args.delete_odb

    sim_args_list = [(sim, result_folder, output_draw, delete_odb) for sim in simulations]

    n_workers = args.workers if args.workers is not None else min(cpu_count(), len(simulations))
    print("Using {} workers.".format(n_workers))

    pool = Pool(processes=n_workers)
    try:
        pool.map(process_simulation, sim_args_list)
    finally:
        pool.close()
        pool.join()


if __name__ == '__main__':
    main()
