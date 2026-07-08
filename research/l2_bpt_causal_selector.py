#!/usr/bin/env python3
"""L2/BPT — SELECTOR CAUSAL STANDALONE dos 17 (formalizacao). Implementa a regra de selecao INDEPENDENTEMENTE
(nao chama phase48.keep) e reproduz os 17 byte-a-byte (fail-loud). Fontes canonicas: config.paths (causal_segments
regime + ruler L2/BPT), phase10 (RAW 4H T/H/L). Zero SLIM/proxy, zero look-ahead, zero producao.

REGRA (causal, ex-ante) sobre o sinal-base L2/BPT:
  regime em t (detector causal) + range do regime ANTERIOR (fechado) + posicao no range atual (barras<=entry).
  KEEP se:  BULL -> entry in [prev.hi - amp/BAND, prev.hi]  (terco superior do range anterior)
            RANGE-> pos < POS_THR                            (terco inferior do range atual)
            BEAR -> entry in [lo_min, lo_min + amp/BAND]     (terco inf. da base de acumulacao ~WIN dias, seg>=MIN barras)
Params calibrados in-sample (BAND=3, POS_THR=0.34, MIN=15, WIN=180d) -> sensibilidade abaixo."""
import json, csv, io, contextlib, sys, bisect
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO))
from config import paths as CP
sys.path.insert(0, str(CP.repo("regime_turnstate_engine","validation")))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
T=P.T; H=P.H; L=P.L; N=len(T)
segs=sorted(json.load(open(CP.causal_segments())),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
REGUA=list(csv.DictReader(open(CP.ruler("XAU_4H_L2_BPT_BOS_CHOCH","v1","results")/"l2_bpt_regua_structural.csv")))
# ground-truth dos 17 (committed)
CANON17=sorted(int(r["bar_idx"]) for r in csv.DictReader(open(REPO/"research/results/l2_bpt_17_trades.csv")))
assert len(CANON17)==17
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def bear_deep(idx, MIN, WIN, BAND):
    bear_start=segs[idx]['start']; win=WIN*86400
    cand=[segs[j] for j in range(idx) if segs[j]['bars']>=MIN and segs[j]['start']>=bear_start-win]
    if not cand: cand=[segs[j] for j in range(idx) if segs[j]['bars']>=MIN]
    if not cand: return None
    lo_min=min(s['lo'] for s in cand); amp=max(s['hi']-s['lo'] for s in cand)
    return (lo_min, lo_min+amp/BAND)
def select(BAND=3.0, POS_THR=0.34, MIN=15, WIN=180, detail=False):
    sel=[]; rows=[]
    for r in REGUA:
        bi=int(r["bar_idx"]); t=T[bi]; idx=seg_idx(t)
        if idx is None or idx==0: continue
        s=segs[idx]; prev=segs[idx-1]; entry=float(r["entry"]); amp=prev['hi']-prev['lo']; reg=s['regime']
        ztop=(prev['hi']-amp/BAND, prev['hi']); zdeep=bear_deep(idx,MIN,WIN,BAND)
        i0=bisect.bisect_left(T,s['start']); rmin=min(L[i0:bi+1]); rmax=max(H[i0:bi+1]); pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
        keep=((reg=='BULL' and ztop[0]<=entry<=ztop[1]) or (reg=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (reg=='RANGE' and pos<POS_THR))
        if keep:
            sel.append(bi)
            if detail: rows.append(dict(bar_idx=bi,entry=round(entry,2),regime=reg,pos=round(pos,3),
                                        zone={'BULL':f"top[{ztop[0]:.1f},{ztop[1]:.1f}]",'BEAR':f"deep{zdeep}",'RANGE':f"pos<{POS_THR}"}[reg],
                                        R=round(float(r['letrun_struct'])-0.35,2)))
    return (sorted(sel), rows) if detail else sorted(sel)

# ---- BASELINE: reproduzir os 17 byte-a-byte (fail-loud) ----
base, rows = select(detail=True)
assert base==CANON17, f"FAIL-LOUD: selector nao reproduz os 17.\n selecionado={base}\n canonico={CANON17}\n diff+={sorted(set(base)-set(CANON17))} diff-={sorted(set(CANON17)-set(base))}"
print(f"BASELINE OK · selector reproduz os 17 byte-a-byte (BAND=3, POS_THR=0.34, MIN=15, WIN=180)")
print(f"  base signals L2/BPT (regua): {len(REGUA)} -> selecionados: {len(base)} ({100*len(base)/len(REGUA):.0f}%)")
print(f"  por regime: "+", ".join(f"{rg}={sum(1 for r in rows if r['regime']==rg)}" for rg in ('BULL','RANGE','BEAR')))

# ---- SENSIBILIDADE (frágil vs estruturalmente estável; NAO procura melhor resultado) ----
print("\n"+"="*90); print("SENSIBILIDADE DOS PARAMETROS (overlap com os 17 canonicos)"); print("="*90)
def cmp(sel):
    keep=len(set(sel)&set(CANON17)); return f"N={len(sel):2} ∩17={keep:2} (+{len(set(sel)-set(CANON17))} / -{len(set(CANON17)-set(sel))})"
sens=[]
print(f"{'variacao':<34}{'resultado':<30}")
GRID=[
  ("BASELINE (3,0.34,15,180)", dict()),
  ("BAND amp/2 (banda mais larga)", dict(BAND=2.0)),
  ("BAND amp/4 (banda mais estreita)", dict(BAND=4.0)),
  ("POS_THR 0.30", dict(POS_THR=0.30)), ("POS_THR 0.40", dict(POS_THR=0.40)),
  ("MIN 10 barras", dict(MIN=10)), ("MIN 20 barras", dict(MIN=20)),
  ("WIN 120 dias", dict(WIN=120)), ("WIN 240 dias", dict(WIN=240)),
]
for name,kw in GRID:
    sel=select(**kw); r=cmp(sel); sens.append(dict(variation=name,params=kw,N=len(sel),overlap17=len(set(sel)&set(CANON17)),
                                                    added=sorted(set(sel)-set(CANON17)),dropped=sorted(set(CANON17)-set(sel))))
    print(f"  {name:<34}{r}")
# outputs
out=REPO/"research/results"; out.mkdir(exist_ok=True)
with open(out/"l2_bpt_causal_selector_selected17.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump({"reproduces_17":base==CANON17,"base_signals":len(REGUA),"selected":base,
           "by_regime":{rg:sum(1 for r in rows if r['regime']==rg) for rg in ('BULL','RANGE','BEAR')},
           "params_baseline":{"BAND":3,"POS_THR":0.34,"MIN_BARS":15,"WIN_DAYS":180},"sensitivity":sens,
           "source":{"regime":"config.paths.causal_segments (phase10 causal)","raw":"phase10 T/H/L","signals":"l2_bpt_regua_structural.csv","note":"zero SLIM/proxy, zero lookahead"}},
          open(out/"l2_bpt_causal_selector_summary.json","w"),indent=1,default=str)
print("\nsaved results/l2_bpt_causal_selector_{selected17.csv,summary.json} · SEM veredito — DA arbitra robustez")
