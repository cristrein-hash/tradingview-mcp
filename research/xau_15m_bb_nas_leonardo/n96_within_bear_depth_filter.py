#!/usr/bin/env python3
"""N96 · FILTRO INTRA-REGIME (2026-07-08). Corte-por-regime bruto e' beta-overlay (-27R). A tese: dentro de
cada regime causal ha discriminador. No BEAR causal: winner=capitulacao funda (1D bem abaixo EMA), loser=repique
raso (perto/acima EMA 1D). Testa manter-fundo/cortar-repique-raso via profundidade 1D, com R e null honesto.
Regras PRE-declaradas (multiplas thresholds reportadas, sem cherry-pick). CAUSAL: regime v5 hour-causal +
features 1D causais. SEM veredito."""
import csv, sys, json
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, famof
from agent_ctx_kit import ENTRIES
REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
def g(r,k):
    try: return float(r.get(k))
    except: return None
OUT={int(r["n"]):int(r["out"]) for r in rows}
def Rof(ns):
    w=sum(OUT[n] for n in ns); return w,len(ns)-w,w*3-(len(ns)-w)
ALL=sorted(BYN); BEAR=[n for n in ALL if REG[n]=="BEAR"]
bw,bl,bR=Rof(ALL)
print(f"BASE 96: win={bw} los={bl} R={bR:+d}")
print(f"BEAR causal: N={len(BEAR)} "+str(Rof(BEAR))+"\n")

# ---- filtro intra-BEAR: manter so 'fundo' (1D abaixo EMA), cortar 'repique raso' ----
# regra: dentro do BEAR, SKIP se 1D_px_vs_ema >= X (repique raso perto/acima da EMA 1D). fora do BEAR: keep tudo.
print("="*78); print("FILTRO 'manter fundo BEAR' — SKIP intra-BEAR se 1D_px_vs_ema >= X"); print("="*78)
print(f"{'X':>6} | {'N_keep':>6}{'R_keep':>7}{'dR':>6} | {'N_cut':>5}{'cut_win':>8}{'cut_los':>8}{'R_cut':>7}")
for X in (0.0,-1.0,-3.0,-5.0,-8.0,-12.0):
    cut=[n for n in BEAR if (g(BYN[n],"1D_px_vs_ema") or -99)>=X]
    keep=[n for n in ALL if n not in cut]
    kw,kl,kR=Rof(keep); cw,cl,cR=Rof(cut)
    print(f"{X:>6} | {len(keep):>6}{kR:>7d}{kR-bR:>+6d} | {len(cut):>5}{cw:>8}{cl:>8}{cR:>+7d}")

# ---- combinado com 1D_ema_trend (fundo = 1D a cair) ----
print("\n"+"="*78); print("FILTRO combinado intra-BEAR: SKIP se 1D_px_vs_ema>=Xp E 1D_ema_trend>=Xt (repique raso + 1D a virar)"); print("="*78)
best=None
for Xp in (0.0,-1.0,-3.0,-5.0):
    for Xt in (0.0,-1.0,-2.0):
        cut=[n for n in BEAR if (g(BYN[n],"1D_px_vs_ema") or -99)>=Xp and (g(BYN[n],"1D_ema_trend") or -99)>=Xt]
        if not cut: continue
        keep=[n for n in ALL if n not in cut]; kw,kl,kR=Rof(keep); cw,cl,cR=Rof(cut)
        print(f"  Xp>={Xp:>5} Xt>={Xt:>5} | cut {len(cut):>2} (win {cw} los {cl} R {cR:+d}) | KEEP R={kR:+d} dR={kR-bR:+d}")

# ---- honest null: dentro do BEAR, o corte-por-profundidade bate permutacao? ----
print("\n"+"="*78); print("NULL HONESTO intra-BEAR (permuta outcomes DENTRO do bear; corte fixo 1D_px_vs_ema>=-3)"); print("="*78)
Xp=-3.0
cut=[n for n in BEAR if (g(BYN[n],"1D_px_vs_ema") or -99)>=Xp]
keep_bear=[n for n in BEAR if n not in cut]
obs_dR=Rof([n for n in ALL if n not in cut])[2]-bR
# permuta: sorteia o MESMO numero de 'cut' dentro do bear, mede dR
outs=np.array([OUT[n] for n in BEAR]); ncut=len(cut); rng=np.random.default_rng(21); vals=[]
for _ in range(2000):
    idx=rng.choice(len(BEAR),ncut,replace=False); cw=outs[idx].sum(); cl=ncut-cw
    vals.append(-(cw*3-cl))  # dR de cortar esse conjunto aleatorio = -(R do conjunto cortado)
vals=np.array(vals); p=float((vals>=obs_dR).mean())
print(f"  corte real (1D_px_vs_ema>=-3): cut={ncut}  obs_dR={obs_dR:+d}")
print(f"  null (cortes aleatorios de mesmo tamanho no bear): media_dR={vals.mean():+.1f} q95={np.quantile(vals,0.95):+.1f} P(null>=obs)={p:.3f}")
print(f"  keep-bear que fica (fundos): {sorted(keep_bear)}  R={Rof(keep_bear)}")
print(f"  cut (repiques rasos): {sorted(cut)}  win_cortados={sum(OUT[n] for n in cut)} los_cortados={sum(1-OUT[n] for n in cut)}")
print("\nSEM veredito — filtro intra-regime entregue como dado. DA arbitra multiplicidade + forward.")
