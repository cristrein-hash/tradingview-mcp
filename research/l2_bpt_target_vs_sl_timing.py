#!/usr/bin/env python3
"""Para cada trade L2/BPT: no RAW 4H forward, o preco toca o SL ANTES ou DEPOIS de alcancar o ALVO do Cris?
Decide o design do exit-layer: (a) alvo reached antes de SL = so falta regra de TARGET; (b) SL tocado antes =
precisa GESTAO de SL (sobreviver ao wick). Tambem: quantas barras ate ao alvo (horizonte necessario). Causal-diag."""
import sys, io, contextlib, csv, json, bisect
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0,str(REPO/"regime_turnstate_engine/validation")); sys.path.insert(0,str(REPO))
RAW=REPO/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
bars=[json.loads(l) for l in open(RAW) if l.strip()]
def gg(b,*k):
    for kk in k:
        if kk in b:return b[kk]
H=[float(gg(b,"h","high")) for b in bars];L=[float(gg(b,"l","low")) for b in bars]
C=[float(gg(b,"c","close")) for b in bars];T=[int(gg(b,"t","time","ts")) for b in bars];N=len(bars)
MY={int(r["num"]):r for r in csv.DictReader(open(REPO/"research/results/l2_bpt_17_trades.csv"))}
CT={int(r["num"]):r for r in csv.DictReader(open(REPO/"research/results/l2_bpt_cris_targets.csv"))}
print("="*104);print("TIMING SL-vs-ALVO (RAW 4H forward) — o que falta para chegar aos alvos do Cris");print("="*104)
print(f"{'#':>2} {'reg':<6}{'entry':>9}{'sl':>9}{'alvo':>9}{'t_sl(bar)':>10}{'t_alvo':>9}{'ordem':>12}{'bars→alvo':>10}{'wick_only?':>11}")
need_mgmt=[];need_target=[];both=0
for n in sorted(MY):
    m=MY[n];entry=float(m["entry"]);sl=float(m["sl"]);bi=int(m["bar_idx"]);tgt=float(CT[n]["alvo_cris"]) if CT[n]["alvo_cris"] not in ("","None") else None
    risk=abs(entry-sl)
    t_sl=t_tgt=None
    for j in range(bi+1,N):
        if t_sl is None and L[j]<=sl:t_sl=j
        if tgt and t_tgt is None and H[j]>=tgt:t_tgt=j
        if (t_sl or 1e9) and t_tgt:break
        if j-bi>400:break
    order = "—"
    if t_tgt and (t_sl is None or t_tgt< t_sl): order="ALVO 1º"
    elif t_sl and (t_tgt is None or t_sl<=t_tgt): order="SL 1º"
    bars_to=t_tgt-bi if t_tgt else None
    # wick-only stop? a barra do SL fecha ACIMA do SL (so pavio tocou)?
    wick = (C[t_sl]>sl) if t_sl else None
    if order=="SL 1º" and t_tgt: need_mgmt.append(n)
    if order=="ALVO 1º": need_target.append(n)
    print(f"#{n:>2} {m['regime']:<6}{entry:>9}{sl:>9}{str(tgt):>9}{str(t_sl-bi if t_sl else None):>10}{str(bars_to):>9}{order:>12}{str(bars_to):>10}{str(wick):>11}")
print("-"*104)
print(f"ALVO alcancado ANTES do SL (so precisa regra de TARGET): {sorted(need_target)}  ({len(need_target)})")
print(f"SL tocado ANTES do alvo mas alvo depois alcancado (precisa GESTAO de SL/wick): {sorted(need_mgmt)}  ({len(need_mgmt)})")
never=[n for n in sorted(MY) if n not in need_target and n not in need_mgmt]
print(f"alvo NUNCA alcancado no forward (target inatingivel): {never}  ({len(never)})")
print("\nLeitura p/ design: TARGET-only = held-to-structural-target basta. GESTAO = precisa SL que sobreviva ao wick")
print("(SL estrutural mais fundo / não-stop-first no pavio da mesma barra / re-entry).")
