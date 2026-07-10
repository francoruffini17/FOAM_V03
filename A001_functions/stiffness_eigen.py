"""Extract the lowest eigenvalue of the tangent stiffness matrix at regular
points along a simulation's compression step (Step-1).

What this is (and is not)
-------------------------
The goal is the smallest eigenvalue of the tangent (Jacobian) stiffness
matrix K at each converged state: lambda_min crossing zero marks a loss of
stability (singular K). This is NOT a *Frequency analysis: a frequency step
solves the generalized problem (K - omega^2 M) phi = 0, so its eigenvalues
are mass-weighted (omega^2) and only the *sign*/zero-crossing coincides with
stiffness singularity. Here the actual eigenvalues of K itself are computed:
K is exported with *Matrix Generate, STIFFNESS (no mass involved) and the
smallest eigenvalue is found with shift-invert Lanczos in scipy.

Why a "replay" job instead of restart
-------------------------------------
The first implementation restarted the finished job at each saved increment
and ran a *Matrix Generate step on the restart data. On this model
(Abaqus 2022, surface-based *Fluid Cavity present) that combination crashes
ABAQUS/pre with an internal error (signal 6 in SMAPreMatrixOutput) for every
format (COORDINATE and MATRIX INPUT alike) - see the *_EIG_*.exception files
in E001_Simulations/SIM_10xx. The same *Matrix Generate step runs fine in a
fresh (non-restart) job on the identical model, so the workaround is:

  1. Build a standalone "replay" input file from the original .inp:
     - the model definition and Step-0 (gas pressurization) are copied
       verbatim (output requests stripped - the replay writes no field
       output, so no multi-GB odb is duplicated);
     - Step-1 is split into N equal segments with the *Boundary magnitudes
       ramped piecewise-linearly to the same totals (identical load path);
     - after Step-0 and after every segment a linear-perturbation step with
       *Matrix Generate, STIFFNESS / *Matrix Output, STIFFNESS is inserted.
       Perturbation steps do not alter the base state, so the static
       solution path is the same as the original single-step run.
  2. Run the replay job once (this re-solves the statics - the price of the
     restart bug - but is fully automatic and parallelizes across sims).
  3. Parse each JOB_STIF{n}.mtx into a sparse matrix, symmetrize, and
     compute the n_eigenvalues smallest eigenvalues with
     scipy.sparse.linalg.eigsh (sigma=0 shift-invert: one sparse LU
     factorization regardless of how many eigenvalues are requested, no
     dense eigendecomposition). The matrices are independent, so they are
     processed by a pool of worker processes (n_workers).
  4. Write I001_Results/DATA_PICK_{sim}_EIG.json; create_PKL_E() packages it
     into DATA_PICK_{sim}_E.pkl.

The matrix steps constrain the same DOFs as Step-1 (magnitude 0), so K is
reduced to the free DOFs of the compression step; the fluid-cavity pressure
DOFs (dof 8) are free in Step-1 and therefore present in K - the gas
coupling is included.

Requires an actual Abaqus install (the `abq` command) for step 2; the inp
building and mtx parsing/eigenvalue steps are plain Python and unit-testable
without Abaqus.

Salvage mode
------------
If the replay solver dies partway (e.g. the structure buckles and Abaqus
cannot converge past the instability - which is precisely the event being
detected), the JOB_STIF{n}.mtx files written before the failure are still
valid. `salvage()` / the --salvage CLI flag skips the solve entirely and
extracts eigenvalues from whatever .mtx files exist in the simulation
directory (or in an EIGBAK/ backup subdirectory), reading the segment
duration from the existing *_EIGJOB.inp.

Usage:
    python -m A001_functions.stiffness_eigen <SIM_NUMBER> [n_segments] [until] [cpus] [n_eigenvalues] [n_workers]
    python -m A001_functions.stiffness_eigen <SIM_NUMBER> --salvage [n_eigenvalues] [n_workers]

    n_segments    number of matrix-extraction points along Step-1 (default 100)
    until         fraction of Step-1 to replay, 0 < until <= 1 (default 1.0;
                  useful for quick validation runs)
    cpus          CPUs for the Abaqus replay solve (default 1)
    n_eigenvalues number of smallest eigenvalues to keep per extraction point
                  (default 20; the extra ones beyond the smallest are nearly
                  free, since eigsh reuses the same sparse LU factorization)
    n_workers     parallel worker processes for the parse+eigsh phase
                  (default min(8, cpu count))
"""
import glob
import json
import multiprocessing
import os
import pickle
import re
import shutil
import subprocess

# The parse+eigsh phase runs one worker process per matrix; without this,
# every worker's BLAS (OpenBLAS/MKL) spawns one thread per core and the
# workers spend almost all their time spinlocking against each other
# (observed: 10 workers on 128 cores -> sys time 4x user time, 32 min for
# what takes 3 min single-threaded-per-worker). ARPACK/SuperLU are mostly
# sequential anyway, so 1 BLAS thread per worker loses nothing. Must be set
# before numpy first initializes its BLAS; setdefault keeps any explicit
# user override.
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS'):
    os.environ.setdefault(_v, '1')

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh


def _remove_path(p):
    """os.remove that also handles directories (e.g. the *_EIGJOB.simdir
    directory Abaqus leaves behind), which os.remove alone crashes on."""
    if os.path.isdir(p) and not os.path.islink(p):
        shutil.rmtree(p, ignore_errors=True)
    else:
        os.remove(p)


def _step_marker_index(lines, step_name):
    marker = '** STEP: {}'.format(step_name)
    idx = next((i for i, l in enumerate(lines) if l.strip() == marker), None)
    if idx is None:
        raise ValueError('Could not find step marker {!r}'.format(marker))
    return idx


def extract_boundary_lines(inp_path, step_name):
    """Pull the *Boundary data lines (node/nset, dof range, value) used in
    `step_name` out of an already-written Abaqus .inp file, so the
    matrix-generation steps constrain the same DOFs as the real analysis.
    """
    with open(inp_path) as f:
        lines = f.readlines()

    start = _step_marker_index(lines, step_name)
    boundary_start = next(
        (i for i in range(start, len(lines)) if lines[i].lstrip().startswith('*Boundary')),
        None,
    )
    if boundary_start is None:
        raise ValueError('No *Boundary block found for step {!r}'.format(step_name))

    data_lines = []
    for line in lines[boundary_start + 1:]:
        stripped = line.lstrip()
        if stripped.startswith('*'):
            break
        if line.strip() and not stripped.startswith('**'):
            data_lines.append(line.rstrip('\n'))
    return data_lines


# Output-request keywords stripped from the copied Step-0 block (the replay
# job needs no field/history output and must not write restart data).
_STRIP_KEYWORDS = (
    '*output', '*restart', '*node output', '*element output',
    '*energy output', '*contact output', '*monitor', '*node print',
    '*el print', '*print',
)


def _strip_output_requests(step_lines):
    kept, dropping = [], False
    for line in step_lines:
        stripped = line.lstrip()
        if stripped.startswith('**'):
            continue  # comments are not needed in the replay step
        if stripped.startswith('*'):
            kw = stripped.lower()
            dropping = any(kw.startswith(k) for k in _STRIP_KEYWORDS)
            if not dropping:
                kept.append(line)
        elif not dropping and line.strip():
            kept.append(line)
    return kept


def _scaled_boundary_line(line, factor):
    """Scale the prescribed value (4th field) of a *Boundary data line."""
    parts = [p.strip() for p in line.split(',')]
    if len(parts) >= 4 and parts[3]:
        try:
            val = float(parts[3])
        except ValueError:
            return line
        parts[3] = repr(val * factor)
        return ', '.join(parts)
    return line


def _matrix_step_lines(label, boundary_lines):
    out = ['*Step, name=EIGMTX-{}, perturbation'.format(label),
           '*Matrix Generate, stiffness',
           '*Matrix Output, stiffness, format=matrix input',
           '*Boundary']
    out.extend(_scaled_boundary_line(l, 0.0) for l in boundary_lines)
    out.append('*End Step')
    return out


def build_replay_inp(inp_path, out_path, step0_name='Step-0', step1_name='Step-1',
                     n_segments=100, until=1.0):
    """Build the standalone replay input deck described in the module
    docstring. Returns the list of Step-1 step times at which a stiffness
    matrix is generated (first entry 0.0 = end of Step-0). Abaqus names the
    .mtx files JOB_STIF{job step number}.mtx; the matrix step for segment k
    is job step 2 + 2k (job step 1 is Step-0, then matrix/segment steps
    alternate), so t = ((index - 2) / 2) * (period / n_segments).
    """
    with open(inp_path) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    s0 = _step_marker_index(lines, step0_name)
    s1 = _step_marker_index(lines, step1_name)

    def end_step_index(start):
        return next(i for i in range(start, len(lines))
                    if lines[i].strip().lower() == '*end step')

    model_lines = lines[:s0]
    step0_lines = _strip_output_requests(lines[s0:end_step_index(s0) + 1])

    # Step-1 header: the *Step keyword line, the *Static keyword line and its
    # data line (initial dt, period, min dt, max dt).
    step_kw = next(i for i in range(s1, len(lines))
                   if lines[i].lstrip().lower().startswith('*step'))
    static_kw = next(i for i in range(step_kw, len(lines))
                     if lines[i].lstrip().lower().startswith('*static'))
    static_data = next(i for i in range(static_kw + 1, len(lines))
                       if lines[i].strip() and not lines[i].lstrip().startswith('*'))

    step_line = lines[step_kw].strip()
    static_line = lines[static_kw].strip()
    dt_init, period, dt_min, dt_max = [float(p) for p in lines[static_data].split(',')]

    boundary_lines = extract_boundary_lines(inp_path, step1_name)

    n_run = int(round(n_segments * until))
    if not 1 <= n_run <= n_segments:
        raise ValueError('until={} gives no segments to run'.format(until))
    dt = period / n_segments

    out = list(model_lines)
    out.append('** ---- replay job written by A001_functions/stiffness_eigen.py ----')
    out.extend(step0_lines)

    schedule = [0.0]                # first matrix = state at end of Step-0
    out.extend(_matrix_step_lines(0, boundary_lines))

    for k in range(1, n_run + 1):
        name = 'EIGSEG-{}'.format(k)
        seg_step = re.sub(r'name=[^,]+', 'name=' + name, step_line)
        # constant-factor stabilization (no allsdtol) forbids continue=YES,
        # so each segment recomputes its damping factor exactly like the
        # original continue=NO step does
        out.append(seg_step)
        out.append(static_line)
        out.append('{:g}, {:g}, {:g}, {:g}'.format(min(dt, dt_max), dt, dt_min, dt_max))
        out.append('*Boundary, op=NEW')
        factor = float(k) / n_segments
        out.extend(_scaled_boundary_line(l, factor) for l in boundary_lines)
        out.append('*End Step')

        out.extend(_matrix_step_lines(k, boundary_lines))
        schedule.append(k * dt)

    with open(out_path, 'w') as f:
        f.write('\n'.join(out) + '\n')
    return schedule


def _parse_coordinate_mtx_slow(path):
    """Original line-by-line parser, kept as a fallback for .mtx files that
    are not plain comma-separated (e.g. exotic whitespace layouts)."""
    dof_index = {}
    entries = {}

    def index_of(node, dof):
        key = (node, dof)
        if key not in dof_index:
            dof_index[key] = len(dof_index)
        return dof_index[key]

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p for p in re.split(r'[,\s]+', line) if p]
            if len(parts) < 5:
                continue
            n1, d1, n2, d2, val = parts[0], parts[1], parts[2], parts[3], parts[4]
            i = index_of(int(n1), int(d1))
            j = index_of(int(n2), int(d2))
            entries[(i, j)] = float(val)

    rows, cols, vals = [], [], []
    for (i, j), v in entries.items():
        rows.append(i)
        cols.append(j)
        vals.append(v)
        if i != j and (j, i) not in entries:
            rows.append(j)
            cols.append(i)
            vals.append(v)

    n = len(dof_index)
    K = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    dof_labels = [None] * n
    for key, idx in dof_index.items():
        dof_labels[idx] = key
    return K, dof_labels


# node/dof pairs are packed into a single int key for fast vectorized
# uniquing; Abaqus structural/fluid dofs are < _DOF_PACK.
_DOF_PACK = 100


def parse_coordinate_mtx(path):
    """Parse an Abaqus *Matrix Output stiffness .mtx file (lines: node1,
    dof1, node2, dof2, value; both FORMAT=COORDINATE and FORMAT=MATRIX INPUT
    write these self-describing rows) into a CSR matrix. Entries whose
    transpose is absent from the file (lower-triangle-only storage) are
    mirrored; if the file already contains both triangles (unsymmetric
    parent step) it is taken as-is. Returns (matrix, dof_labels) where
    dof_labels[i] = (node, dof) for row i.

    Vectorized with pandas/numpy (the files are a few million comma-separated
    rows, ~100 MB each); falls back to the original line-by-line parser if
    the file does not read cleanly as 5 comma-separated columns.
    """
    try:
        import pandas as pd
        df = pd.read_csv(path, header=None, sep=',', skipinitialspace=True,
                         dtype={0: np.int64, 1: np.int64, 2: np.int64, 3: np.int64, 4: np.float64})
        if df.shape[1] != 5:
            raise ValueError('expected 5 columns, got {}'.format(df.shape[1]))
    except Exception:
        return _parse_coordinate_mtx_slow(path)

    n1 = df[0].to_numpy()
    d1 = df[1].to_numpy()
    n2 = df[2].to_numpy()
    d2 = df[3].to_numpy()
    v = df[4].to_numpy()
    if len(v) and (d1.max() >= _DOF_PACK or d2.max() >= _DOF_PACK):
        return _parse_coordinate_mtx_slow(path)

    key1 = n1 * _DOF_PACK + d1
    key2 = n2 * _DOF_PACK + d2
    uniq, inv = np.unique(np.concatenate([key1, key2]), return_inverse=True)
    i = inv[:len(key1)]
    j = inv[len(key1):]
    n = len(uniq)

    ck = i * np.int64(n) + j
    if len(np.unique(ck)) != len(ck):
        # duplicate (i, j) rows: keep the last occurrence, matching the
        # dict-overwrite semantics of the original parser
        _, first_of_reversed = np.unique(ck[::-1], return_index=True)
        keep = np.sort(len(ck) - 1 - first_of_reversed)
        i, j, v = i[keep], j[keep], v[keep]
        ck = i * np.int64(n) + j
    tk = j * np.int64(n) + i

    mirror = (i != j) & ~np.isin(tk, ck)
    rows = np.concatenate([i, j[mirror]])
    cols = np.concatenate([j, i[mirror]])
    vals = np.concatenate([v, v[mirror]])

    K = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    dof_labels = [(int(k // _DOF_PACK), int(k % _DOF_PACK)) for k in uniq]
    return K, dof_labels


def smallest_eigenvalues(K, k=20, sigma=0.0, fallback_sigmas=(-1e-6, -1.0)):
    """The k smallest eigenvalues (ascending) of the symmetric part of sparse
    K via shift-invert Lanczos. The steps use the unsymmetric solver (fluid
    cavity + stabilization), so K may be slightly unsymmetric; stability of
    the equilibrium is governed by the symmetric part, and eigsh requires it.

    Only factorizes (K - sigma*I) once, regardless of k - no dense
    eigendecomposition - so this stays cheap even for a large sparse
    stiffness matrix. k is capped at K.shape[0] - 2 (eigsh's limit for a
    sparse matrix).
    """
    Ks = (K + K.T) * 0.5
    k = min(k, Ks.shape[0] - 2)
    sigmas_to_try = (sigma,) + fallback_sigmas
    last_err = None
    for s in sigmas_to_try:
        try:
            vals = eigsh(Ks, k=k, sigma=s, which='LM', return_eigenvectors=False)
            return np.sort(vals)
        except Exception as e:  # singular shift, retry with an offset
            last_err = e
    raise RuntimeError('eigsh failed for all sigma values tried: {}'.format(last_err))


def _mtx_index(path):
    return int(re.search(r'_STIF(\d+)\.mtx$', path).group(1))


def _mtx_index_to_time(idx, dt):
    """Job step 1 is Step-0; matrix step for segment k is job step 2 + 2k,
    so STIF{idx} corresponds to t = ((idx - 2) / 2) * dt (t = 0.0 is the
    state at the end of Step-0)."""
    if idx < 2 or idx % 2:
        return None
    return ((idx - 2) // 2) * dt


def _eigen_worker(args):
    """Parse one .mtx and return (index, eigenvalues list). Module-level so
    multiprocessing can pickle it."""
    mtx, n_eigenvalues = args
    K, _ = parse_coordinate_mtx(mtx)
    eigvals = smallest_eigenvalues(K, k=n_eigenvalues)
    return _mtx_index(mtx), eigvals.tolist()


def _extract_eigenvalues(mtx_files, dt, n_eigenvalues=20, n_workers=None,
                         delete_after=False):
    """Run parse + eigsh over the given .mtx files with a process pool and
    return the results list sorted by time. Each file is deleted right after
    its eigenvalues are extracted when delete_after=True (the files are
    ~100 MB each and there can be hundreds)."""
    if n_workers is None:
        n_workers = min(8, os.cpu_count() or 1)
    n_workers = max(1, min(int(n_workers), len(mtx_files) or 1))

    results = []
    jobs = [(m, n_eigenvalues) for m in mtx_files]

    def _collect(idx, eigvals):
        t = _mtx_index_to_time(idx, dt)
        if t is None:
            print('WARNING: unexpected matrix step number {} - skipping'.format(idx))
            return
        results.append({'matrix_index': idx, 'time': t, 'eigenvalues': eigvals})
        print('t = {:.4f}  lambda_min = {:.6e}  ({} eigenvalues)'.format(
            t, eigvals[0], len(eigvals)), flush=True)

    by_index = {_mtx_index(m): m for m in mtx_files}
    if n_workers == 1:
        for job in jobs:
            idx, eigvals = _eigen_worker(job)
            _collect(idx, eigvals)
            if delete_after:
                os.remove(by_index[idx])
    else:
        with multiprocessing.Pool(n_workers) as pool:
            for idx, eigvals in pool.imap_unordered(_eigen_worker, jobs):
                _collect(idx, eigvals)
                if delete_after:
                    os.remove(by_index[idx])

    results.sort(key=lambda d: d['time'])
    return results


def _write_eig_json(sim_num, results):
    out_path = 'I001_Results/DATA_PICK_{:03d}_EIG.json'.format(sim_num)
    os.makedirs('I001_Results', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print('Wrote {} eigenvalues to {}'.format(len(results), out_path))
    return out_path


def run(sim_num, n_segments=100, until=1.0, keep_files=False, cpus=1,
        n_eigenvalues=20, n_workers=None):
    """Full pipeline for SIM_{sim_num}: build the replay job, run it, parse
    every stiffness matrix, and write
    I001_Results/DATA_PICK_{sim_num}_EIG.json with
    {'matrix_index', 'time', 'eigenvalues'} per extraction point ('time' is
    Step-1 step time; time 0.0 is the state at the end of Step-0;
    'eigenvalues' is the n_eigenvalues smallest eigenvalues, ascending).
    """
    job_name = 'SIM_{:03d}'.format(sim_num)
    sim_dir = 'E001_Simulations/{}'.format(job_name)
    inp_path = '{}/{}.inp'.format(sim_dir, job_name)
    eig_job = '{}_EIGJOB'.format(job_name)
    eig_inp = '{}/{}.inp'.format(sim_dir, eig_job)
    abq_cmd = os.environ.get('ABQ_CMD', 'abq')

    schedule = build_replay_inp(inp_path, eig_inp, n_segments=n_segments, until=until)
    dt = schedule[1] if len(schedule) > 1 else 0.0

    # remove stale outputs of a previous attempt so old .mtx files are not
    # mistaken for results of this run
    for p in glob.glob('{}/{}*'.format(sim_dir, eig_job)):
        if not p.endswith('.inp'):
            _remove_path(p)

    cmd = [abq_cmd, 'job=' + eig_job, 'input=' + eig_job + '.inp',
           'cpus={}'.format(int(cpus)), 'interactive']
    proc = subprocess.run(cmd, cwd=sim_dir)
    if proc.returncode != 0:
        print('WARNING: {} exited with status {} - parsing whatever matrices '
              'were written before the failure.'.format(eig_job, proc.returncode))

    mtx_files = sorted(
        glob.glob('{}/{}_STIF*.mtx'.format(sim_dir, eig_job)), key=_mtx_index)
    if len(mtx_files) < len(schedule):
        print('WARNING: only {} of {} stiffness matrices were written - the '
              'job probably stopped early.'.format(len(mtx_files), len(schedule)))

    results = _extract_eigenvalues(mtx_files, dt, n_eigenvalues=n_eigenvalues,
                                   n_workers=n_workers,
                                   delete_after=not keep_files)

    if not keep_files:
        for p in glob.glob('{}/{}*'.format(sim_dir, eig_job)):
            if not p.endswith(('.inp', '.dat', '.sta')):
                _remove_path(p)

    if not results:
        raise RuntimeError('No stiffness matrices were produced by {} - see '
                           '{}/{}.dat'.format(eig_job, sim_dir, eig_job))

    _write_eig_json(sim_num, results)
    return results


def _segment_dt_from_replay_inp(eig_inp):
    """Read the segment duration back out of an existing replay .inp: the
    *Static data line of step EIGSEG-1 has the segment period as its second
    field."""
    with open(eig_inp) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]
    seg = next(i for i, l in enumerate(lines)
               if l.lstrip().lower().startswith('*step') and 'name=EIGSEG-1,' in l.replace(' ', '') + ',')
    static_kw = next(i for i in range(seg, len(lines))
                     if lines[i].lstrip().lower().startswith('*static'))
    data = next(lines[i] for i in range(static_kw + 1, len(lines))
                if lines[i].strip() and not lines[i].lstrip().startswith('*'))
    return float(data.split(',')[1])


def salvage(sim_num, n_eigenvalues=20, n_workers=None, keep_files=True):
    """Extract eigenvalues from the .mtx files an earlier (possibly failed or
    crashed) replay run left in E001_Simulations/SIM_{sim_num}/ - or in its
    EIGBAK/ backup subdirectory - without re-running Abaqus. Writes the same
    DATA_PICK_{sim}_EIG.json as run(). By default the .mtx files are kept
    (keep_files=True), since salvage exists precisely because re-creating
    them is expensive."""
    job_name = 'SIM_{:03d}'.format(sim_num)
    sim_dir = 'E001_Simulations/{}'.format(job_name)
    eig_job = '{}_EIGJOB'.format(job_name)
    eig_inp = '{}/{}.inp'.format(sim_dir, eig_job)

    mtx_files = sorted(
        glob.glob('{}/{}_STIF*.mtx'.format(sim_dir, eig_job)), key=_mtx_index)
    if not mtx_files:
        mtx_files = sorted(
            glob.glob('{}/EIGBAK/{}_STIF*.mtx'.format(sim_dir, eig_job)), key=_mtx_index)
    if not mtx_files:
        raise RuntimeError('No {}_STIF*.mtx files found in {} (or EIGBAK/) - '
                           'nothing to salvage.'.format(eig_job, sim_dir))

    dt = _segment_dt_from_replay_inp(eig_inp)
    print('Salvaging {} stiffness matrices from {} (segment dt = {:g})'.format(
        len(mtx_files), sim_dir, dt))

    results = _extract_eigenvalues(mtx_files, dt, n_eigenvalues=n_eigenvalues,
                                   n_workers=n_workers,
                                   delete_after=not keep_files)
    if not results:
        raise RuntimeError('No eigenvalues could be extracted from the '
                           'salvaged matrices.')
    _write_eig_json(sim_num, results)
    return results


def create_PKL_E(sim_num: int, results_dir: str = "I001_Results", output_path: str = None,
                  delete_mtx: bool = True) -> dict:
    """
    Package the per-frame smallest stiffness-matrix eigenvalues of Step-1
    into the standard DATA_PICK_{sim}_E.pkl format used by the other reduce
    outputs. 't' is Step-1 step time (0.0 = end of Step-0 pressurization).
    'eigenvalues' holds all n_eigenvalues smallest eigenvalues (ascending)
    per frame; 'lambda_min' is kept as the first column (the single smallest
    eigenvalue) for backward compatibility with code/notebooks that only
    plot the lowest one.

    Requires I001_Results/DATA_PICK_{sim_num:03d}_EIG.json, written by
    `run()` in this module (i.e. `python -m A001_functions.stiffness_eigen
    <SIM_NUMBER>`). EIG.json files written before the switch to storing
    multiple eigenvalues (which have a scalar 'lambda_min' instead of an
    'eigenvalues' list per entry) need to be regenerated by re-running the
    eigenvalue extraction.

    `run()` already deletes each .mtx right after it is parsed, but if it was
    called with keep_files=True, or a previous attempt was interrupted before
    its own cleanup ran, leftover EIGJOB files (.mtx/.odb/.dat/...) can still
    be sitting in E001_Simulations/SIM_{sim_num:03d}/. Since the eigenvalues
    are already safely packaged in the .pkl at this point, none of those
    files are needed any more - delete_mtx (default True) sweeps them up
    (including any EIGBAK/ salvage backup).
    """
    eig_json_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_EIG.json"
    with open(eig_json_path) as f:
        eig_data = json.load(f)
    if not eig_data:
        raise ValueError(f"{eig_json_path} is empty - run the eigenvalue "
                         "extraction first (python -m A001_functions.stiffness_eigen "
                         f"{sim_num})")

    eig_data = sorted(eig_data, key=lambda d: d['time'])

    DATA_E = {
        'source_file': eig_json_path,
        't': [d['time'] for d in eig_data],
        'matrix_index': [d['matrix_index'] for d in eig_data],
        'eigenvalues': [d['eigenvalues'] for d in eig_data],
        'lambda_min': [d['eigenvalues'][0] for d in eig_data],
    }

    if output_path is None:
        output_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_E.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(DATA_E, f)
    print(f"PKL_E saved to '{output_path}'")

    if delete_mtx:
        job_name = 'SIM_{:03d}'.format(sim_num)
        eig_job = '{}_EIGJOB'.format(job_name)
        sim_dir = 'E001_Simulations/{}'.format(job_name)
        leftovers = glob.glob('{}/{}*'.format(sim_dir, eig_job))
        bak_dir = '{}/EIGBAK'.format(sim_dir)
        if os.path.isdir(bak_dir):
            leftovers.append(bak_dir)
        for p in leftovers:
            _remove_path(p)
        if leftovers:
            print(f"Deleted {len(leftovers)} leftover {eig_job} file(s) from {sim_dir}")

    return DATA_E


if __name__ == '__main__':
    import sys
    args = [a for a in sys.argv[1:] if a != '--salvage']
    do_salvage = '--salvage' in sys.argv[1:]
    sim = int(args[0])
    if do_salvage:
        n_eig = int(args[1]) if len(args) > 1 else 20
        workers = int(args[2]) if len(args) > 2 else None
        salvage(sim, n_eigenvalues=n_eig, n_workers=workers)
    else:
        n_seg = int(args[1]) if len(args) > 1 else 100
        until_frac = float(args[2]) if len(args) > 2 else 1.0
        n_cpus = int(args[3]) if len(args) > 3 else 1
        n_eig = int(args[4]) if len(args) > 4 else 20
        workers = int(args[5]) if len(args) > 5 else None
        run(sim, n_segments=n_seg, until=until_frac, cpus=n_cpus,
            n_eigenvalues=n_eig, n_workers=workers)
