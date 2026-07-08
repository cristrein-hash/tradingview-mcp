#!/usr/bin/env python3
"""N96 · DISCRIMINACAO EXAUSTIVA — TODOS indicadores x TODOS TFs, familia a familia (2026-07-08).
RAW-native via n96_mtf_kit (zero resample, zero Fractal-MTF, zero SLIM, causal born_t/known_at/close).
NAO produz veredito. Produz: (1) fire-check por indicador (nenhuma feature dispara 0 em silencio),
(2) tabela disc() completa por feature x familia (medianas WIN/C/D/R/MGMT + AUC vs WIN),
(3) ranking por poder de separacao, (4) oof_mining_null nas candidatas top por familia.
Arbitro final = DA (script nao conclui)."""
import json, sys, csv
import numpy as np, statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import (ENTRIES, FAM, famof, TF, BARSEC, bars_upto, smc_upto, nas_upto,
                         zones_upto, bubbles_upto, disc, oof_mining_null, HERE)
from agent_ctx_kit import ATR, HI, LO

TFS=["15M","30M","1H","4H","1D"]

def _f(x):
    try:
        v=float(x)
        return v if v==v else None   # NaN guard
    except Exception:
        return None

def tf_feats(tf, px, a, et):
    """features de UM tf, causal (barras fechadas, zonas born_t<et, eventos t<et)."""
    o={}
    bars=bars_upto(tf, et)
    if len(bars)>=8:
        last=bars[-1]
        rsi=_f(last.get("rsi")); ema=_f(last.get("ema21")); c=_f(last.get("c")); atr_tf=_f(last.get("atr"))
        o[f"{tf}_rsi"]=rsi
        # slope RSI sobre ~4 barras
        prev=[_f(b.get("rsi")) for b in bars[-5:-1] if _f(b.get("rsi")) is not None]
        o[f"{tf}_rsi_slope"]= (rsi-prev[0]) if (rsi is not None and prev) else None
        # trend EMA sobre ~6 barras, em ATR-15M
        ema6=_f(bars[-7].get("ema21")) if len(bars)>=7 else None
        o[f"{tf}_ema_trend"]= round((ema-ema6)/a,3) if (ema is not None and ema6 is not None) else None
        o[f"{tf}_px_vs_ema"]= round((px-ema)/a,3) if ema is not None else None
        o[f"{tf}_atr_rel"]= round(atr_tf/c,4) if (atr_tf and c) else None
    # zonas Custom OB (causal born_t<et): demanda mais proxima ABAIXO / supply ACIMA
    Z=zones_upto(tf, et); dem=99.0; sup=99.0
    for z in Z:
        mid=(z["high"]+z["low"])/2
        if z["text"].startswith("DEMAND") and z["low"]<=px+0.1*a:
            d=(px-mid)/a
            if 0<=d<dem: dem=d
        if z["text"].startswith("SUPPLY") and z["high"]>=px-0.1*a:
            s=(mid-px)/a
            if 0<=s<sup: sup=s
    o[f"{tf}_dem_below"]= round(dem,2) if dem<99 else None
    o[f"{tf}_sup_above"]= round(sup,2) if sup<99 else None
    # SMC recentes (~20 barras do tf)
    smc=smc_upto(tf, et, 20)
    for tag in ("BOS","CHoCH","EQH","EQL"):
        o[f"{tf}_smc_{tag}"]=sum(1 for e in smc if e.get("text","").upper().startswith(tag.upper()))
    # NAS recentes (~20 barras)
    nas=nas_upto(tf, et, 20)
    o[f"{tf}_nas_long"]=sum(1 for e in nas if str(e.get("dir","")).upper()=="LONG")
    o[f"{tf}_nas_short"]=sum(1 for e in nas if str(e.get("dir","")).upper()=="SHORT")
    return o

def bubble_feats(px, a, et, i):
    seg=bubbles_upto(et, 32)  # ~ultimas 32 barras 15M
    W={"S":1,"M":2,"L":3}
    seg=[b for b in seg if b.get("t",0)>=et-32*900]
    lo=LO[i]; rhi=max(HI[max(0,i-32):i+1])
    def ml(side): return sum(W.get(b.get("size","S"),1) for b in seg if b.get("side")==side and b.get("size") in ("M","L"))
    buy_ml=ml("BUY"); sell_ml=ml("SELL")
    sell_at_low=sum(1 for b in seg if b.get("side")=="SELL" and b.get("size") in ("M","L") and abs(_f(b.get("l") or px)-lo)<=0.6*a)
    buy_at_high=sum(1 for b in seg if b.get("side")=="BUY" and b.get("size") in ("M","L") and abs(_f(b.get("h") or px)-rhi)<=0.6*a)
    return {"bub_buy_ml":buy_ml,"bub_sell_ml":sell_ml,"bub_net":buy_ml-sell_ml,
            "bub_sell_absorbed_low":(1 if (sell_at_low>=1 and px>lo+0.3*a) else 0),
            "bub_buy_at_high":buy_at_high,"bub_count":len(seg)}

# ---- construir features de TODOS entries ----
ROWS={}
for e in ENTRIES:
    n=e["n"]; px=e["ent"]; et=e["t"]; i=e["i"]; a=ATR[e["j"]] or 5
    feat={}
    for tf in TFS: feat.update(tf_feats(tf, px, a, et))
    feat.update(bubble_feats(px, a, et, i))
    # MTF alignment agregados
    feat["mtf_bull_align"]=sum(1 for tf in TFS if (feat.get(f"{tf}_rsi") or 0)>50 and (feat.get(f"{tf}_px_vs_ema") or -9)>0)
    feat["mtf_dem_conf"]=sum(1 for tf in TFS if feat.get(f"{tf}_dem_below") is not None and feat[f"{tf}_dem_below"]<=1.2)
    feat["mtf_sup_conf"]=sum(1 for tf in TFS if feat.get(f"{tf}_sup_above") is not None and feat[f"{tf}_sup_above"]<=1.2)
    feat["mtf_net_conf"]=feat["mtf_dem_conf"]-feat["mtf_sup_conf"]
    ROWS[n]=feat

ALLF=sorted({k for f in ROWS.values() for k in f})

# ---- FIRE-CHECK: nenhuma feature dispara 0/None em silencio ----
print("="*78); print("FIRE-CHECK (nao-nulo / nao-zero por feature, N=96)"); print("="*78)
dead=[]
for k in ALLF:
    vals=[ROWS[n].get(k) for n in ROWS]
    nn=sum(1 for v in vals if v is not None)
    nz=sum(1 for v in vals if v is not None and v!=0)
    tag="" if nz>=5 else "  <-- MORTA/RARA (revisar extractor, NAO 'sem sinal')"
    if nz<5: dead.append(k)
    print(f"  {k:<22} nonnull={nn:>3}/96  nonzero={nz:>3}{tag}")
print(f"\nfeatures vivas: {len(ALLF)-len(dead)}/{len(ALLF)}  |  mortas/raras: {dead}")

# ---- DISC completo por feature ----
print("\n"+"="*78); print("DISCRIMINACAO disc() — medianas WIN/C/D/R/MGMT + AUC(WIN vs familia)"); print("="*78)
print(f"{'feature':<22}{'WIN':>7}{'C':>7}{'D':>7}{'R':>7}{'MGMT':>7} | {'aucC':>6}{'aucD':>6}{'aucR':>6}{'aucM':>6}  sep")
disc_rows=[]
for k in ALLF:
    if k in dead: continue
    d=disc({n:ROWS[n].get(k) for n in ROWS})
    m=d["med"]; au=d["auc_vs_win"]
    sep=max(abs(au[f]-0.5) for f in ("C","D","R"))  # poder separando WIN de loser-real (nao MGMT)
    disc_rows.append((sep,k,d))
    def s(x): return f"{x:>7.2f}" if isinstance(x,(int,float)) else f"{'-':>7}"
    print(f"{k:<22}{s(m['WIN'])}{s(m['C'])}{s(m['D'])}{s(m['R'])}{s(m['MGMT'])} | "
          f"{au['C']:>6.2f}{au['D']:>6.2f}{au['R']:>6.2f}{au['MGMT']:>6.2f}  {sep:.2f}")

# ---- RANKING por poder de separacao (loser real) ----
disc_rows.sort(reverse=True)
print("\n"+"="*78); print("TOP-20 features por separacao WIN-vs-loser-real (|AUC-0.5| max em C/D/R)"); print("="*78)
for sep,k,d in disc_rows[:20]:
    au=d["auc_vs_win"]
    print(f"  {k:<22} sep={sep:.2f}  aucC={au['C']:.2f} aucD={au['D']:.2f} aucR={au['R']:.2f}")

# ---- OOF honesto: top features multivariadas (arbitro real; in-sample nao conta) ----
print("\n"+"="*78); print("OOF + mining-null (LOO logistic + 200 perms) — candidatas top (in-sample NAO conta)"); print("="*78)
def build_X(feats):
    ns=[e["n"] for e in ENTRIES]
    X=[]
    for n in ns:
        row=[]
        for k in feats:
            v=ROWS[n].get(k)
            row.append(99.0 if v is None else float(v))
        X.append(row)
    return np.array(X,dtype=float)

topfeats=[k for _,k,_ in disc_rows[:8]]
oof_results={}
# (a) top-8 multivariado global
oof_results["top8_global"]={"feats":topfeats,"oof":oof_mining_null(build_X(topfeats))}
# (b) por familia: top-4 features que mais separam AQUELA familia
for fam in ("C","D","R"):
    ranked=sorted(ALLF, key=lambda k: (0 if k in dead else abs(disc({n:ROWS[n].get(k) for n in ROWS})["auc_vs_win"][fam]-0.5)), reverse=True)
    ff=[k for k in ranked if k not in dead][:4]
    oof_results[f"{fam}_top4"]={"feats":ff,"oof":oof_mining_null(build_X(ff))}
for tag,r in oof_results.items():
    o=r["oof"]
    print(f"  {tag:<14} feats={r['feats']}")
    print(f"                 oof_hit={o.get('oof_hit')} base={o.get('base')} N_keep={o.get('N_keep')} "
          f"poison={o.get('poison')} p={o.get('mining_null_p')} verdict={o.get('verdict')}")

# ---- persist ----
out={"features":ALLF,"dead":dead,
     "disc":{k:disc({n:ROWS[n].get(k) for n in ROWS}) for k in ALLF if k not in dead},
     "ranking":[(k,round(sep,3)) for sep,k,_ in disc_rows],
     "oof":{t:{"feats":r["feats"],"oof":r["oof"]} for t,r in oof_results.items()}}
import os; os.makedirs(HERE+"/results",exist_ok=True)
json.dump(out, open(HERE+"/results/n96_exhaustive_mtf_discrimination.json","w"), indent=1, default=str)
with open(HERE+"/results/n96_exhaustive_mtf_features.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["n","out","fam"]+ALLF)
    for e in ENTRIES:
        n=e["n"]; w.writerow([n,e["out"],famof(n)]+[ROWS[n].get(k) for k in ALLF])
print("\nsaved results/n96_exhaustive_mtf_discrimination.json + n96_exhaustive_mtf_features.csv")
print("NOTA: sem veredito. Arbitro = DA sobre oof + ranking.")
