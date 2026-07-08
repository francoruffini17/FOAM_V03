"""Extract the lowest eigenvalue of the tangent stiffness matrix at each
output frame of a simulation step.

Abaqus/Standard does not expose stiffness-matrix eigenvalues as a history
output during a general nonlinear *Static step - *Frequency is a separate
linear-perturbation procedure evaluated at one fixed state. To get the
lowest eigenvalue at every frame of an already-run step, this module:

  1. Reads the increment number of every frame of the step from the .odb
     (via abq_get_step_increments.py, run under `abq python`).
  2. For each increment, writes a small restart input file that reads the
     converged state at that increment and runs a *Matrix Generate,
     STIFFNESS / *Matrix Output, STIFFNESS, FORMAT=COORDINATE step, re-using
     the same *Boundary DOFs as the original step (pulled from the original
     .inp) so the output matrix is already reduced to the free DOFs.
  3. Submits each restart job through the `abq` CLI.
  4. Parses the resulting COORDINATE-format .mtx file into a sparse matrix
     and computes only the smallest eigenvalue with shift-invert Lanczos
     (scipy.sparse.linalg.eigsh, sigma=0) - this needs one sparse LU
     factorization, not a dense eigendecomposition, so it stays cheap even
     for a large matrix.

Requires an actual Abaqus install (the `abq` command) to run steps 1 and 3;
steps 2 and 4 are plain Python and can be unit-tested without Abaqus.
"""
import glob
import json
import os
import pickle
import re
import subprocess

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh


def extract_boundary_lines(inp_path, step_name):
    """Pull the *Boundary data lines (node/nset, dof range, value) used in
    `step_name` out of an already-written Abaqus .inp file, so the
    matrix-generation step constrains the same DOFs as the real analysis.
    """
    with open(inp_path) as f:
        lines = f.readlines()

    step_marker = '** STEP: {}'.format(step_name)
    start = next((i for i, l in enumerate(lines) if l.strip() == step_marker), None)
    if start is None:
        raise ValueError('Could not find step marker {!r} in {}'.format(step_marker, inp_path))

    boundary_start = next(
        (i for i in range(start, len(lines)) if lines[i].lstrip().startswith('*Boundary')),
        None,
    )
    if boundary_start is None:
        raise ValueError('No *Boundary block found for step {!r}'.format(step_name))

    data_lines = []
    for line in lines[boundary_start + 1:]:
        if line.lstrip().startswith('*'):
            break
        if line.strip():
            data_lines.append(line.rstrip('\n'))
    return data_lines


def write_matrix_generate_inp(step_number, inc_number, boundary_lines, out_path, job_label):
    """Write a restart input file that generates the stiffness matrix at the
    converged state after `inc_number` of step `step_number` of the original
    (old) job.
    """
    with open(out_path, 'w') as f:
        f.write('*Heading\n')
        f.write('** Stiffness matrix extraction at increment {}\n'.format(inc_number))
        f.write('*Restart, read, step={}, inc={}\n'.format(step_number, inc_number))
        f.write('*Step, name=EIG-{}, perturbation\n'.format(job_label))
        f.write('*Matrix Generate, stiffness\n')
        # FORMAT=MATRIX INPUT (Abaqus default) rather than FORMAT=COORDINATE:
        # COORDINATE hit an internal Abaqus preprocessor crash
        # (Assertion failed: !task.IsNull(), SMAPreMatrixOutput.cpp) on this
        # model (likely triggered by the *Fluid Cavity interaction). Both
        # formats write the same self-describing "node1, dof1, node2, dof2,
        # value" rows, so parse_coordinate_mtx() below needs no changes.
        f.write('*Matrix Output, stiffness, format=matrix input\n')
        f.write('*Boundary\n')
        for line in boundary_lines:
            f.write(line + '\n')
        f.write('*End Step\n')


def parse_coordinate_mtx(path):
    """Parse an Abaqus FORMAT=COORDINATE .mtx file (lines: node1, dof1,
    node2, dof2, value - lower triangle only) into a symmetric CSR matrix.
    Returns (matrix, dof_labels) where dof_labels[i] = (node, dof) for row i.
    """
    dof_index = {}
    rows, cols, vals = [], [], []

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
            v = float(val)
            rows.append(i)
            cols.append(j)
            vals.append(v)
            if i != j:
                rows.append(j)
                cols.append(i)
                vals.append(v)

    n = len(dof_index)
    K = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    dof_labels = [None] * n
    for key, idx in dof_index.items():
        dof_labels[idx] = key
    return K, dof_labels


def lowest_eigenvalue(K, sigma=0.0, fallback_sigmas=(-1e-6, -1.0)):
    """Smallest eigenvalue of sparse symmetric K via shift-invert Lanczos.

    Only factorizes (K - sigma*I) once - no dense eigendecomposition -
    so this stays cheap even for a large sparse stiffness matrix.
    """
    sigmas_to_try = (sigma,) + fallback_sigmas
    last_err = None
    for s in sigmas_to_try:
        try:
            vals = eigsh(K, k=1, sigma=s, which='LM', return_eigenvectors=False)
            return float(vals[0])
        except Exception as e:  # singular shift, retry with an offset
            last_err = e
    raise RuntimeError('eigsh failed for all sigma values tried: {}'.format(last_err))


def run(sim_num, step_name='Step-1', step_number=2, keep_mtx=False):
    """Full pipeline for SIM_{sim_num}: discover frames, extract matrices,
    return a list of {'increment', 'time', 'lambda_min'} dicts (also written
    to I001_Results/DATA_PICK_{sim_num:03d}_EIG.json).
    """
    job_name = 'SIM_{:03d}'.format(sim_num)
    sim_dir = 'E001_Simulations/{}'.format(job_name)
    odb_path = '{}/{}.odb'.format(sim_dir, job_name)
    inp_path = '{}/{}.inp'.format(sim_dir, job_name)
    increments_json = '{}/{}_increments.json'.format(sim_dir, job_name)
    abq_cmd = os.environ.get('ABQ_CMD', 'abq')

    subprocess.run(
        [abq_cmd, 'python', 'A001_functions/abq_get_step_increments.py',
         odb_path, step_name, increments_json],
        check=True,
    )
    with open(increments_json) as f:
        frames = json.load(f)

    boundary_lines = extract_boundary_lines(inp_path, step_name)

    results = []
    for fr in frames:
        inc = fr['incrementNumber']
        mtx_job = '{}_EIG_{}'.format(job_name, inc)
        mtx_inp = '{}/{}.inp'.format(sim_dir, mtx_job)
        write_matrix_generate_inp(step_number, inc, boundary_lines, mtx_inp, job_label=inc)

        subprocess.run(
            [abq_cmd, 'job=' + mtx_job, 'oldjob=' + job_name, 'input=' + mtx_job + '.inp', 'interactive'],
            check=True, cwd=sim_dir,
        )

        mtx_matches = glob.glob('{}/{}_STIF*.mtx'.format(sim_dir, mtx_job))
        if not mtx_matches:
            raise FileNotFoundError('No .mtx output found for {}'.format(mtx_job))
        K, _ = parse_coordinate_mtx(mtx_matches[0])
        lam_min = lowest_eigenvalue(K)
        results.append({'increment': inc, 'time': fr['stepTime'], 'lambda_min': lam_min})

        if not keep_mtx:
            for ext in ('.inp', '.odb', '.dat', '.msg', '.sta', '.prt', '.res', '.stt', '.mdl'):
                p = '{}/{}{}'.format(sim_dir, mtx_job, ext)
                if os.path.exists(p):
                    os.remove(p)
            for p in mtx_matches:
                os.remove(p)

    out_path = 'I001_Results/DATA_PICK_{:03d}_EIG.json'.format(sim_num)
    os.makedirs('I001_Results', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print('Wrote {} eigenvalues to {}'.format(len(results), out_path))
    return results


def create_PKL_E(sim_num: int, results_dir: str = "I001_Results", output_path: str = None) -> dict:
    """
    Package the per-frame lowest stiffness-matrix eigenvalues of Step-1 into
    the standard DATA_PICK_{sim}_E.pkl format used by the other reduce
    outputs.

    Requires I001_Results/DATA_PICK_{sim_num:03d}_EIG.json, written by
    `run()` in this module (i.e. `python -m A001_functions.stiffness_eigen
    <SIM_NUMBER>`).
    """
    eig_json_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_EIG.json"
    with open(eig_json_path) as f:
        eig_data = json.load(f)

    eig_data = sorted(eig_data, key=lambda d: d['increment'])

    DATA_E = {
        'source_file': eig_json_path,
        't': [d['time'] for d in eig_data],
        'increment': [d['increment'] for d in eig_data],
        'lambda_min': [d['lambda_min'] for d in eig_data],
    }

    if output_path is None:
        output_path = f"{results_dir}/DATA_PICK_{sim_num:03d}_E.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(DATA_E, f)
    print(f"PKL_E saved to '{output_path}'")

    return DATA_E


if __name__ == '__main__':
    import sys
    run(int(sys.argv[1]))
