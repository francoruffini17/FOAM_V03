"""python -m A001_functions.Reduce_resultsV20 <sim_start> <sim_end> [flags]

Flag-based interface to Reduce_resultsV5.process_simulation. No stdin required.
"""

import argparse
import multiprocessing
import sys

from .Reduce_resultsV5 import process_simulation


def _yn(s):
    if s.lower() in ('y', 'n'):
        return s.lower()
    raise argparse.ArgumentTypeError("Expected y or n, got {!r}".format(s))


def main():
    p = argparse.ArgumentParser(
        description='Reduce Abaqus CSV results to PKL files (FOAM_V03).',
        allow_abbrev=False)
    p.add_argument('sim_start', type=int, help='First simulation number.')
    p.add_argument('sim_end',   type=int, help='Last simulation number (inclusive).')

    def yn(flag, default, help_text=''):
        p.add_argument('--' + flag, default=default, type=_yn, metavar='y|n',
                       help='{} (default: {})'.format(help_text, default))

    yn('A',     'y', 'PKL A – reaction forces / displacements')
    yn('A2',    'y', 'PKL A2 – aggregated A')
    yn('B',     'y', 'PKL B – stress field')
    yn('C',     'y', 'PKL C – coordinates')
    yn('C2',    'y', 'PKL C2 – mesh / adjacency')
    yn('D',     'y', 'PKL D – stress at adjacency')
    yn('T1',    'n', 'PKL T1 – triangulation areas')
    yn('T2',    'n', 'PKL T2 – triangulation stats')
    p.add_argument('--T1-ini', type=int, default=0, metavar='N',
                   help='First triangulation index for T1/T2 (default: 0)')
    p.add_argument('--T1-fin', type=int, default=0, metavar='N',
                   help='Last triangulation index for T1/T2 (default: 0)')
    yn('J1',    'y', 'PKL J1 – tension/compression graphs')
    yn('J2',    'y', 'PKL J2 – graph efficiency sampled')
    yn('J3',    'y', 'PKL J3 – graph efficiency exact')
    p.add_argument('--J-ini', type=int, default=0, metavar='N')
    p.add_argument('--J-fin', type=int, default=0, metavar='N')
    p.add_argument('--J-alg', default='1', choices=['1', '2'],
                   help='J3 algorithm: 1=igraph default, 2=BFS (default: 1)')
    yn('H1',    'y', 'PKL H1')
    yn('H2',    'y', 'PKL H2')
    yn('H3',    'y', 'PKL H3')
    p.add_argument('--H-ini', type=int, default=0, metavar='N')
    p.add_argument('--H-fin', type=int, default=0, metavar='N')
    p.add_argument('--H-alg', default='1', choices=['1', '2'])
    yn('I1',    'y', 'PKL I1')
    yn('I2',    'y', 'PKL I2')
    yn('I3',    'y', 'PKL I3')
    p.add_argument('--I-ini', type=int, default=0, metavar='N')
    p.add_argument('--I-fin', type=int, default=0, metavar='N')
    p.add_argument('--I-alg', default='1', choices=['1', '2'])
    yn('K1',    'y', 'PKL K1')
    yn('K2',    'y', 'PKL K2')
    yn('K3',    'y', 'PKL K3')
    p.add_argument('--K-ini', type=int, default=0, metavar='N')
    p.add_argument('--K-fin', type=int, default=0, metavar='N')
    p.add_argument('--K-alg', default='1', choices=['1', '2'])
    yn('Q1',    'n', 'PKL Q1 – quadrangulation areas')
    yn('Q2',    'n', 'PKL Q2 – quadrangulation stats')
    p.add_argument('--Q-ini', type=int, default=0, metavar='N')
    p.add_argument('--Q-fin', type=int, default=0, metavar='N')
    yn('TP1',   'n', 'PKL TP1')
    yn('TP2',   'n', 'PKL TP2')
    yn('DEFC1', 'n', 'PKL DEFC1')
    yn('DEFC2', 'n', 'PKL DEFC2')
    yn('E',     'n', 'PKL E - lowest stiffness-matrix eigenvalue per frame')

    p.add_argument('--delete-csv', default='n', type=_yn, metavar='y|n',
                   help='Delete CSV after reduction (default: n)')
    p.add_argument('--n-workers', type=int, default=0, metavar='N',
                   help='Parallel workers for G2_exact; 0=auto (default: 0)')
    p.add_argument('--max-memory-gb', type=float, default=0.0, metavar='GB',
                   help='RAM budget for G2_exact in GB; 0=auto (default: 0)')

    args = p.parse_args()

    J_alg = None if args.J_alg == '1' else 'bfs'
    H_alg = None if args.H_alg == '1' else 'bfs'
    I_alg = None if args.I_alg == '1' else 'bfs'
    K_alg = None if args.K_alg == '1' else 'bfs'

    args_list = [
        (
            i,
            args.A, args.A2, args.B, args.C, args.C2, args.D,
            args.T1, args.T2, args.T1_ini, args.T1_fin,
            args.J1, args.J2, args.J3, args.J_ini, args.J_fin, J_alg,
            args.H1, args.H2, args.H3, args.H_ini, args.H_fin, H_alg,
            args.I1, args.I2, args.I3, args.I_ini, args.I_fin, I_alg,
            args.K1, args.K2, args.K3, args.K_ini, args.K_fin, K_alg,
            args.Q1, args.Q2, args.Q_ini, args.Q_fin,
            args.TP1, args.TP2,
            args.DEFC1, args.DEFC2, args.E,
            args.delete_csv,
            args.n_workers or None,      # 0 → None (auto)
            args.max_memory_gb or None,  # 0.0 → None (auto)
        )
        for i in range(args.sim_start, args.sim_end + 1)
    ]

    with multiprocessing.Pool() as pool:
        pool.map(process_simulation, args_list)


if __name__ == '__main__':
    main()
