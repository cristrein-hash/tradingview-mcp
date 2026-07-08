#!/usr/bin/env python3
"""N96 · HARDENING do filtro intra-BEAR (2026-07-08). Aplica as licoes do DA ao achado intra-BEAR:
(1) FEATURE-SEARCH null: paga a busca de ~50 features (nao so o threshold). Em cada permutacao dos outcomes
    do bear, procura o MELHOR corte-por-feature (todas features, ambas direcoes, mesmo tamanho) e regista dR.
    Se o obs real bate o q95 do melhor-por-permutacao, sobrevive a multiplicidade de features.
(2) STALENESS: HTF primitives terminam ~2026-05-24/25 (gap RAW). Verifica se os trades CORTADOS caem na cauda
    stale (HTF congelado) — se sim, o corte apoia-se em input degenerado.
(3) PROFIT-robustness ja mostrado (todos thresholds +R). SEM veredito — DA arbitra."""
import csv, sys, json, datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE
from agent_ctx_kit import ENTRIES
REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
OUT={int(r["n"]):int(r["out"]) for r in rows}
TBYN={e["n"]:e["t"] for e in ENTRIES}
def g(r,k):
    try: return float(r.get(k))
    except: return None
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]
BEAR=sorted(n for n in BYN if REG[n]=="BEAR")
outs=np.array([OUT[n] for n in BEAR])
def dR_cut(cut_ns):
    cw=sum(OUT[n] for n in cut_ns); cl=len(cut_ns)-cw; return -(cw*3-cl)  # dR de cortar = -(R do cortado)

# corte real de referencia (1D_px_vs_ema>=0)
real_cut=[n for n in BEAR if (g(BYN[n],"1D_px_vs_ema") or -99)>=0]
obs=dR_cut(real_cut)
print(f"BEAR N={len(BEAR)} ({int(outs.sum())}W/{len(BEAR)-int(outs.sum())}L)  corte real 1D_px_vs_ema>=0: cut={len(real_cut)} obs_dR={obs:+d}")

# ---- (1) FEATURE-SEARCH null ----
# para um vetor de outcomes y sobre o bear: melhor dR cortando por 1 feature (ambas direcoes), varrendo cortes
# de tamanho k~len(real_cut)+-3, quantis de threshold. Devolve o max dR alcancavel por busca.
Ksz=range(max(3,len(real_cut)-3), len(real_cut)+4)
FMAT={k:np.array([ (g(BYN[n],k) if g(BYN[n],k) is not None else np.nan) for n in BEAR]) for k in FEATS}
def best_search_dR(y):
    best=-999
    for k,col in FMAT.items():
        if np.isnan(col).all(): continue
        c=col.copy(); c[np.isnan(c)]=np.nanmedian(c)
        order_hi=np.argsort(-c)  # cortar os MAIORES (repique raso = px alto vs ema)
        order_lo=np.argsort(c)
        for order in (order_hi,order_lo):
            for ksz in Ksz:
                idx=order[:ksz]; cw=y[idx].sum(); cl=ksz-cw; d=-(cw*3-cl)
                if d>best: best=d
    return best
obs_search=best_search_dR(outs)  # melhor busca no outcome REAL (>= obs do 1D_px_vs_ema)
rng=np.random.default_rng(31); nulls=[]
for _ in range(1000):
    yp=rng.permutation(outs); nulls.append(best_search_dR(yp))
nulls=np.array(nulls); p_search=float((nulls>=obs_search).mean())
print("\n(1) FEATURE-SEARCH null (paga busca de ~%d features x 2 direcoes x %d tamanhos):"%(len(FEATS),len(list(Ksz))))
print(f"    melhor dR busca-real={obs_search:+d}  |  null(melhor-busca em outcomes permutados): media={nulls.mean():+.1f} q95={np.quantile(nulls,0.95):+.1f} max={nulls.max():+d}")
print(f"    P(null_best >= obs_best) = {p_search:.3f}  -> {'SOBREVIVE a busca de features' if p_search<0.1 else 'NAO sobrevive (multiplicidade de features explica)'}")

# ---- (2) STALENESS ----
STALE_1D=dt.datetime(2026,5,24).timestamp()
def yr(n): return dt.datetime.utcfromtimestamp(TBYN[n]).year
print("\n(2) STALENESS (HTF 1D congela ~2026-05-24):")
cut_stale=[n for n in real_cut if TBYN[n]>=STALE_1D]; cut_fresh=[n for n in real_cut if TBYN[n]<STALE_1D]
print(f"    trades CORTADOS: {len(real_cut)} | em cauda stale (>=05-24): {len(cut_stale)} {cut_stale} | frescos: {len(cut_fresh)}")
print(f"    dR do corte SO com frescos: {dR_cut(cut_fresh):+d} (obs total {obs:+d})")
# datas do corte
print("    datas dos cortados:", ", ".join(f"#{n}={dt.datetime.utcfromtimestamp(TBYN[n]).strftime('%Y-%m-%d')}({'W' if OUT[n] else 'L'})" for n in sorted(real_cut)))

# ---- (3) por ano do corte ----
print("\n(3) por ano (o bear e' essencialmente 2026, mas #24/25 sao 2025 counter-pullback):")
for y in (2025,2026):
    cc=[n for n in real_cut if yr(n)==y]
    if cc: print(f"    {y}: cortados={len(cc)} win={sum(OUT[n] for n in cc)} los={sum(1-OUT[n] for n in cc)} dR={dR_cut(cc):+d}")
print("\nSEM veredito. Dados de hardening p/ DA dedicado ao intra-BEAR.")
