import pickle, os, glob, collections
import numpy as np
SP = os.path.dirname(os.path.abspath(__file__))
rows=[]
for f in glob.glob(f'{SP}/pcache/*.pkl'):
    try:
        r=pickle.load(open(f,'rb'))
        if r and 'error' not in r: rows.append(r)
    except Exception: pass
try:
    for r in pickle.load(open(f'{SP}/cross_family_pstar_2010s.pkl','rb')).values():
        if 'error' not in r: rows.append(r)
except Exception: pass
rows.sort(key=lambda r:r['sim'])

# --- uniform recomputation from cached displ (robust to truncated runs) ---
for r in rows:
    u=np.asarray(r['displ'],float); i=r['i_star']; n=r['n_frames']
    r['eps_u']      = float((u[i]-u[0])/(20.0-u[0]))       # engineering strain at the minimum
    r['eps_end_u']  = float((u[-1]-u[0])/(20.0-u[0]))      # strain the run actually reached
    r['reach']      = r['eps_u']/r['eps_end_u'] if r['eps_end_u']>0 else np.nan
    r['pinned']     = bool(i >= 0.95*(n-1))                # minimum not interior -> limit not reached
    r['complete']   = bool(r['eps_end_u'] >= 0.20)         # run got near the intended 25%
    r['valid']      = bool((not r['pinned']) and r['eps_end_u'] > 0.05)

def cv(x):
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    return 100*x.std(ddof=1)/abs(x.mean()) if len(x)>1 else np.nan

print(f'{len(rows)} sims with results\n')
print('='*128)
print('TABLE 0 — RUN COMPLETENESS   (many jobs terminated before the intended 25% strain)')
print('='*128)
print(f"{'base':>5} {'mesh':>7} {'E':>3} {'mat':>11} {'n':>3} {'eps_end range':>16} {'#complete':>10} {'#valid p*':>10}")
fam=collections.defaultdict(list)
for r in rows: fam[r['base']].append(r)
for b in sorted(fam):
    rs=fam[b]; ee=np.array([r['eps_end_u'] for r in rs]); r0=rs[0]
    print(f"{b:>5} {r0['mesh']:>7} {r0['E']:>3.0f} {r0['material']:>11} {len(rs):>3} "
          f"{ee.min():>7.3f}-{ee.max():<8.3f} {sum(r['complete'] for r in rs):>10} {sum(r['valid'] for r in rs):>10}")

VALID=[r for r in rows if r['valid']]
print(f"\n{len(VALID)} of {len(rows)} runs give an interior compaction-limit minimum.")

print('\n'+'='*128)
print('TABLE 1 — p*/E PER MICROSTRUCTURE   (valid runs, linear elastic, E=20 only)')
print('='*128)
g=collections.defaultdict(list)
for r in VALID:
    if r['material']!='linear' or r['E']!=20.0: continue
    g[(r['mesh'],r['kind'],round(1-r['poro'],4))].append(r)
print(f"{'mesh':>7} {'packing':>17} {'rho':>6} {'n':>3} {'p*/E':>10} {'CV%':>6} {'eps* (strain) range':>22}")
X,Y=[],[]
for k in sorted(g,key=lambda k:k[2]):
    rs=g[k]; v=np.array([r['p_star_over_E'] for r in rs]); e=np.array([r['eps_u'] for r in rs])
    print(f"{k[0]:>7} {k[1]:>17} {k[2]:>6.3f} {len(v):>3} {v.mean():>10.5f} {cv(v):>6.1f} "
          f"{e.min():>9.4f}-{e.max():<11.4f}")
    if len(v)>=3: X.append(k[2]); Y.append(v.mean())
if len(X)>2:
    X,Y=np.array(X),np.array(Y); sl,ic=np.polyfit(np.log(X),np.log(Y),1)
    pr=np.exp(ic)*X**sl
    r2=1-((np.log(Y)-np.log(pr))**2).sum()/((np.log(Y)-np.log(Y).mean())**2).sum()
    print(f"\n  power law over {len(X)} microstructures: p*/E = {np.exp(ic):.4f} * rho^{sl:.2f}   (R2={r2:.3f})")
    print(f"  spread of p*/E across microstructures: CV {cv(Y):.1f}%   (a universal constant would give ~0)")
    print(f"  Gibson-Ashby elastic collapse: exponent ~2 (foam) / ~3 (honeycomb, t/l form)")

print('\n'+'='*128)
print('TABLE 2 — DOES p*/E DEPEND ON E?  mesh R1000, matched P/E   (probes the unscaled damping)')
print('='*128)
byPE=collections.defaultdict(dict)
for r in VALID:
    if r['mesh']!='R1000' or r['material']!='linear': continue
    byPE[round(r['P']/r['E'],5)][int(r['E'])]=r['p_star_over_E']
print(f"{'P/E':>8} {'E=20':>9} {'E=10':>9} {'E=5':>9} {'spread%':>9}")
for pe_ in sorted(byPE):
    d=byPE[pe_]; vals=[d.get(e) for e in (20,10,5)]; got=[v for v in vals if v is not None]
    sp=100*(max(got)-min(got))/np.mean(got) if len(got)>1 else float('nan')
    print(f"{pe_:>8.4f} "+' '.join(f"{v:>9.5f}" if v is not None else f"{'-':>9}" for v in vals)+f" {sp:>9.1f}")

print('\n'+'='*128)
print('TABLE 3 — eps* vs GAS PRESSURE, per family (valid runs)')
print('='*128)
print(f"{'base':>5} {'mesh':>7} {'E':>3} {'n':>3} {'a (intercept)':>14} {'b (slope)':>11} {'R2':>7}")
for b in sorted(fam):
    ok=[r for r in fam[b] if r['valid'] and r['material']=='linear']
    if len(ok)<3:
        print(f"{b:>5} {fam[b][0]['mesh']:>7} {fam[b][0]['E']:>3.0f} {len(ok):>3}   (too few valid runs)")
        continue
    x=np.array([r['P']/r['E'] for r in ok]); y=np.array([r['eps_u'] for r in ok])
    b_,a_=np.polyfit(x,y,1); r2=1-((y-(a_+b_*x))**2).sum()/((y-y.mean())**2).sum()
    print(f"{b:>5} {ok[0]['mesh']:>7} {ok[0]['E']:>3.0f} {len(ok):>3} {a_:>14.4f} {b_:>11.3f} {r2:>7.4f}")
pickle.dump({r['sim']:{k:v for k,v in r.items() if k not in ('mean_p','std_p','shear_mean','edi_mean','displ','f')}
             for r in rows}, open(f'{SP}/summary.pkl','wb'))
