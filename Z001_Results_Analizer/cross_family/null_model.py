"""Random-bond null model f_random(q) on EACH mesh's own overlay lattice.

Same method as SIM_1010s_shear_localization.ipynb cell 47 part 3 (K=400 sampled sources),
extended from R1000 to all nine overlays. This is the control that separates
'f(q) is a microstructure fingerprint' from 'f(q) reflects the overlay lattice'.
"""
import json, pickle, os
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from multiprocessing import Pool

MESHES = ['R1000','R1040','R1050','R1060','S1000','S1001','A1000','RH1000','RH1001']
OUT = '/tmp/claude-1001/-Disk-F-FOAM-V03/8aaf4c00-8615-4cc7-9023-45c0d7fc48ab/scratchpad/null_model.pkl'
QS = np.round(np.arange(0.34, 0.821, 0.02), 3)
TR = 3

def run(mesh):
    g = json.load(open(f'/Disk_F/FOAM_V03/C001_Mesh_files/{mesh}_I3002.gridhex.json'))
    Eb = np.array([[b['start'], b['end']] for b in g['bars']])
    Nn = len(g['nodes'])
    rng = np.random.default_rng(23)
    K = min(400, Nn)
    src = rng.choice(Nn, K, replace=False)

    def A(e):
        M = csr_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(Nn, Nn))
        return M + M.T

    def eff(M):
        D = shortest_path(M, method='D', unweighted=True, indices=src)
        with np.errstate(divide='ignore'):
            inv = np.where(np.isfinite(D) & (D > 0), 1.0 / D, 0.0)
        return inv.sum() / (K * (Nn - 1))

    def clus(M):
        nc, lab = connected_components(M, directed=False)
        s = np.sort(np.bincount(lab))[::-1]; rest = s[1:]
        return s[0] / Nn, (s[1] / Nn if len(s) > 1 else 0.0), (rest**2).sum() / max(rest.sum(), 1)

    F = np.zeros((len(QS), TR)); L = np.zeros_like(F); L2 = np.zeros_like(F); X = np.zeros_like(F)
    for i, q in enumerate(QS):
        for t in range(TR):
            m = rng.random(len(Eb)) < q
            F[i, t] = eff(A(Eb[m])) / eff(A(Eb[~m]))
            L[i, t], L2[i, t], X[i, t] = clus(A(Eb[m]))
    print(f'{mesh}: done (N={Nn}, bars={len(Eb)})', flush=True)
    return mesh, dict(q=QS, f=F.mean(1), f_sd=F.std(1), lcc=L.mean(1),
                      lcc2=L2.mean(1), chi=X.mean(1), N=Nn, n_bars=len(Eb))

if __name__ == '__main__':
    with Pool(9) as p:
        res = dict(p.map(run, MESHES))
    pickle.dump(res, open(OUT, 'wb'))
    print('WROTE', OUT, flush=True)
