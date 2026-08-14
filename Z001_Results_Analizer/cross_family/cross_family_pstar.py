"""Cross-family p* / eps* / f* extraction.

Follows SIM_1010s_shear_localization.ipynb exactly:
  - eps* : argmin of TP2_L['shear_mean'], eps = 5*(i/(n-1))/20   (doc convention)
  - p    : element average of -(S11+S22)/2 using integration points 0::2 of 8
  - f    : I3_BFS global_ef_t / global_ef_c
"""
import os, sys, pickle, json
import numpy as np
from multiprocessing import Pool

RES = '/data/Franco/FOAM_V03_Results/I001_Results'
OUT = os.path.dirname(os.path.abspath(__file__)) + '/cross_family_pstar.pkl'

Ps = [0.0] + [0.04 * (np.sqrt(2) ** i) for i in range(9)]

# base sim -> (mesh, E, material)
FAMILIES = {
    1010: ('R1000', 20.0, 'linear'),
    1020: ('R1000', 10.0, 'linear'),
    1030: ('R1000',  5.0, 'linear'),
    1040: ('R1040', 20.0, 'linear'),
    1050: ('R1050', 20.0, 'linear'),
    1060: ('R1060', 20.0, 'linear'),
    1070: ('S1000', 20.0, 'linear'),
    1080: ('RH1000', 20.0, 'linear'),
    1100: ('A1000', 20.0, 'linear'),
    1170: ('S1001', 20.0, 'linear'),
    1180: ('RH1001', 20.0, 'linear'),
    2010: ('R1000', 20.0, 'neohookean'),
}
MESHINFO = {}
for m in set(v[0] for v in FAMILIES.values()):
    p = f'/Disk_F/FOAM_V03/C001_Mesh_files/{m}.mesh.json'
    d = json.load(open(p))
    MESHINFO[m] = dict(kind=d['geometry']['mesh_kind'],
                       poro=d['geometry']['achieved_porosity'],
                       n_holes=d['summary']['n_holes'])

def sims_present():
    out = []
    for f in os.listdir(RES):
        if f.startswith('DATA_PICK_') and f.endswith('_B.pkl'):
            s = f.split('_')[2]
            if s.isdigit():
                out.append(int(s))
    return sorted(set(out))

def family_of(sim):
    for base in sorted(FAMILIES, reverse=True):
        if base <= sim < base + 10:
            return base
    return None

CACHE = os.path.dirname(os.path.abspath(__file__)) + '/pcache'

def one(sim):
    cp = f'{CACHE}/{sim}.pkl'
    if os.path.exists(cp):
        try:
            return pickle.load(open(cp, 'rb'))
        except Exception:
            pass
    r = _one(sim)
    try:
        pickle.dump(r, open(cp, 'wb'))
    except Exception:
        pass
    return r

def _one(sim):
    base = family_of(sim)
    if base is None:
        return None
    mesh, E, mat = FAMILIES[base]
    try:
        a2 = pickle.load(open(f'{RES}/DATA_PICK_{sim}_A2.pkl', 'rb'))
        tp2l = pickle.load(open(f'{RES}/DATA_PICK_{sim}_TP2_L.pkl', 'rb'))
    except Exception as e:
        return dict(sim=sim, error=f'A2/TP2_L: {e}')
    displ = -np.array(a2['U2']['PERN-9999997'], dtype=float)
    shear = np.array(tp2l['shear_mean'], dtype=float)
    edi = np.array(tp2l.get('edi_mean', []), dtype=float)
    tarr = np.array(tp2l['t'], dtype=float)
    n = len(shear)
    i_star = int(np.argmin(shear))
    # Many runs terminated early (n_frames 20..201, t_end 0.095..1.0), so
    # i_star/(n-1) is NOT the load fraction. Use the recorded time and the real
    # displacement instead.
    pinned = bool(i_star >= 0.95 * (n - 1))
    eps_star = 5.0 * tarr[i_star] / 20.0                    # doc convention, eps = 5t/20
    eps_star_u = float((displ[i_star] - displ[0]) / (20.0 - displ[0]))   # engineering strain
    eps_end_u = float((displ[-1] - displ[0]) / (20.0 - displ[0]))
    t_star = float(tarr[i_star]); t_end = float(tarr[-1])

    # f from I3
    f = None
    try:
        i3 = pickle.load(open(f'{RES}/DATA_PICK_{sim}_I3_BFS_3002.pkl', 'rb'))
        eft = np.array(i3['global_ef_t'], float); efc = np.array(i3['global_ef_c'], float)
        with np.errstate(divide='ignore', invalid='ignore'):
            f = np.where(efc != 0, eft / efc, np.nan)
    except Exception:
        pass

    # p from B (element average, IPs 0::2)
    try:
        b = pickle.load(open(f'{RES}/DATA_PICK_{sim}_B.pkl', 'rb'))
    except Exception as e:
        return dict(sim=sim, error=f'B: {e}')
    eids = list(b['S11'].keys())
    # Meshes with mixed element types store different integration-point counts per
    # element (e.g. S1001: 53,685 elements with 8 slots, 38 with 2). Group by count
    # so the 0::2 selection is applied consistently without ragged stacking.
    bynip = {}
    for e in eids:
        bynip.setdefault(len(b['S11'][e]), []).append(e)
    tot = None; tot2 = None; nel = 0
    for nip, es in bynip.items():
        a11 = np.array([b['S11'][e] for e in es], dtype=np.float32)   # (m, nip, nframes)
        a22 = np.array([b['S22'][e] for e in es], dtype=np.float32)
        pe = (-(a11[:, 0::2, :] + a22[:, 0::2, :]) / 2.0).mean(axis=1)   # (m, nframes)
        del a11, a22
        tot = pe.sum(axis=0) if tot is None else tot + pe.sum(axis=0)
        tot2 = (pe**2).sum(axis=0) if tot2 is None else tot2 + (pe**2).sum(axis=0)
        nel += pe.shape[0]
        del pe
    del b
    mean_p = (tot / nel).astype(float)
    std_p = np.sqrt(np.maximum(tot2 / nel - (tot / nel)**2, 0)).astype(float)
    nip_counts = {int(k): len(v) for k, v in bynip.items()}

    # frame where mean p crosses zero (linear interp on frame index)
    frame_p0 = np.nan
    sgn = np.sign(mean_p)
    idx = np.where((sgn[:-1] < 0) & (sgn[1:] >= 0))[0]
    if len(idx):
        i0 = int(idx[0])
        frame_p0 = i0 + mean_p[i0] / (mean_p[i0] - mean_p[i0 + 1])

    # frame where f crosses 1 (first downward crossing after frame 0)
    frame_f1 = np.nan; q_note = None
    if f is not None:
        g = f - 1.0
        good = np.isfinite(g)
        idx = np.where(good[:-1] & good[1:] & (g[:-1] >= 0) & (g[1:] < 0))[0]
        if len(idx):
            i0 = int(idx[0])
            frame_f1 = i0 + g[i0] / (g[i0] - g[i0 + 1])

    P = Ps[sim - base] if (sim - base) < len(Ps) else np.nan
    mi = MESHINFO[mesh]
    return dict(sim=sim, base=base, mesh=mesh, kind=mi['kind'], poro=mi['poro'],
                n_holes=mi['n_holes'], E=E, material=mat, P=P, n_frames=n,
                i_star=i_star, pinned=pinned, eps_star=eps_star,
                eps_star_u=eps_star_u, eps_end_u=eps_end_u, t_star=t_star, t_end=t_end,
                nip_counts=nip_counts,
                p0=float(mean_p[0]), p_star=float(mean_p[i_star]),
                p_final=float(mean_p[-1]),
                p_star_over_E=float(mean_p[i_star] / E),
                p0_over_P=float(mean_p[0] / P) if P else np.nan,
                std_p_star=float(std_p[i_star]),
                frame_p0=float(frame_p0), frame_f1=float(frame_f1),
                f_star=float(f[i_star]) if f is not None and np.isfinite(f[i_star]) else np.nan,
                f0=float(f[0]) if f is not None else np.nan,
                mean_p=mean_p, std_p=std_p, shear_mean=shear, edi_mean=edi,
                displ=displ, f=f)

if __name__ == '__main__':
    sims = [s for s in sims_present() if family_of(s) is not None]
    print(f'{len(sims)} sims: {sims}', flush=True)
    with Pool(10) as pool:
        res = []
        for i, r in enumerate(pool.imap_unordered(one, sims)):
            if r is not None:
                res.append(r)
                tag = r['error'] if 'error' in r else f"eps*={r['eps_star']:.4f} p*/E={r['p_star_over_E']:.5f}" 
                print(f"[{i+1}/{len(sims)}] {r['sim']}: {tag}", flush=True)
    with open(OUT, 'wb') as fh:
        pickle.dump({r['sim']: r for r in res}, fh)
    print('WROTE', OUT, flush=True)
