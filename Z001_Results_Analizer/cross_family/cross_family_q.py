"""Tension bond fraction q(t) per sim, from the I2 overlay graphs, for every family."""
import os, pickle
import numpy as np
from multiprocessing import Pool

RES = '/data/Franco/FOAM_V03_Results/I001_Results'
OUT = os.path.dirname(os.path.abspath(__file__)) + '/cross_family_q.pkl'
BASES = [1010,1020,1030,1040,1050,1060,1070,1080,1100,1170,1180]

def fam(sim):
    for b in sorted(BASES, reverse=True):
        if b <= sim < b + 10:
            return b
    return None

def one(sim):
    try:
        d = pickle.load(open(f'{RES}/DATA_PICK_{sim}_I2_3002.pkl', 'rb'))
        T, C = d['tension'], d['compression']
        ks = sorted(T, key=lambda k: int(k))
        nt = np.array([T[k].number_of_edges() for k in ks], float)
        nc = np.array([C[k].number_of_edges() for k in ks], float)
        del d, T, C
        q = nt / (nt + nc)
        i3 = pickle.load(open(f'{RES}/DATA_PICK_{sim}_I3_BFS_3002.pkl', 'rb'))
        eft = np.array(i3['global_ef_t'], float); efc = np.array(i3['global_ef_c'], float)
        with np.errstate(divide='ignore', invalid='ignore'):
            f = np.where(efc != 0, eft / efc, np.nan)
        return dict(sim=sim, base=fam(sim), q=q, f=f, n_bars=float(nt[0] + nc[0]),
                    ef_t=eft, ef_c=efc)
    except Exception as e:
        return dict(sim=sim, error=str(e))

if __name__ == '__main__':
    sims = sorted({int(f.split('_')[2]) for f in os.listdir(RES)
                   if f.startswith('DATA_PICK_') and f.endswith('_I2_3002.pkl')
                   and f.split('_')[2].isdigit() and fam(int(f.split('_')[2]))})
    print(len(sims), 'sims', flush=True)
    with Pool(5) as p:
        res = []
        for i, r in enumerate(p.imap_unordered(one, sims)):
            res.append(r)
            print(f"[{i+1}/{len(sims)}] {r['sim']}: " +
                  (r['error'] if 'error' in r else f"q0={r['q'][0]:.4f} qend={r['q'][-1]:.4f} bars={r['n_bars']:.0f}"),
                  flush=True)
    pickle.dump({r['sim']: r for r in res}, open(OUT, 'wb'))
    print('WROTE', OUT, flush=True)
