"""Is eps* visible on the macroscopic load-displacement curve?"""
import os, pickle
import numpy as np
RES = {'main': '/data/Franco/FOAM_V03_Results/I001_Results', 'local': '/Disk_F/FOAM_V03/I001_Results'}
BASES = [1010,1020,1030,1040,1050,1060,1070,1080,1100,1170,1180,2010]
def fam(s):
    for b in sorted(BASES, reverse=True):
        if b <= s < b+10: return b
out = {}
for tag, d in RES.items():
    for f in sorted(os.listdir(d)):
        if not (f.startswith('DATA_PICK_') and f.endswith('_A2.pkl')): continue
        s = f.split('_')[2]
        if not s.isdigit(): continue
        s = int(s)
        if fam(s) is None or s in out: continue
        try:
            a2 = pickle.load(open(f'{d}/{f}','rb'))
            tp2l = pickle.load(open(f'{d}/DATA_PICK_{s}_TP2_L.pkl','rb'))
        except Exception:
            continue
        U = -np.array(a2['U2']['PERN-9999997'], float)
        RF = np.array(a2['RF2']['PERN-9999997'], float)
        shear = np.array(tp2l['shear_mean'], float)
        n = len(shear)
        i_star = int(np.argmin(shear))
        u = U - U[0]
        k = np.gradient(np.abs(RF), u)          # tangent stiffness
        k = k[3:]                                # drop first-increment transient
        i_kmax = int(np.argmax(k)) + 3
        d2 = np.gradient(np.gradient(np.abs(RF), u), u)
        out[s] = dict(sim=s, base=fam(s), n=n, i_star=i_star,
                      i_kmax=i_kmax, frac_star=i_star/(n-1), frac_kmax=i_kmax/(n-1),
                      rf_at_star=float(np.abs(RF)[i_star]), rf_max=float(np.abs(RF).max()),
                      k_at_star=float(np.gradient(np.abs(RF), u)[i_star]),
                      k_max=float(k.max()), monotone_RF=bool(np.all(np.diff(np.abs(RF)) > -1e-12)))
pickle.dump(out, open('/tmp/claude-1001/-Disk-F-FOAM-V03/8aaf4c00-8615-4cc7-9023-45c0d7fc48ab/scratchpad/macro.pkl','wb'))
print(f'{len(out)} sims')
print(f"{'base':>5} {'n':>3} {'frac_star mean':>15} {'frac_kmax mean':>15} {'RF*/RFmax':>12} {'k*/kmax':>10}")
import collections
g = collections.defaultdict(list)
for r in out.values(): g[r['base']].append(r)
for b in sorted(g):
    rs = [r for r in g[b] if r['i_star'] < r['n']-1]
    if not rs: rs = g[b]
    fs = np.array([r['frac_star'] for r in rs]); fk = np.array([r['frac_kmax'] for r in rs])
    rr = np.array([r['rf_at_star']/r['rf_max'] for r in rs]); kk = np.array([r['k_at_star']/r['k_max'] for r in rs])
    print(f"{b:>5} {len(rs):>3} {fs.mean():>7.3f}+-{fs.std():<6.3f} {fk.mean():>7.3f}+-{fk.std():<6.3f} "
          f"{rr.mean():>6.3f}+-{rr.std():<5.3f} {kk.mean():>5.3f}+-{kk.std():<4.3f}")
