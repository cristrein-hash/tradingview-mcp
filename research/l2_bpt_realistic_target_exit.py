#!/usr/bin/env python3
"""L2/BPT — cenario REALISTA e CAUSAL de exit por ALVO estrutural do Cris (lido via MCP), com SL atual.
Corrige o teto-hindsight (+87.6R que tratava losers como winners = exagero, Cris 2026). Regra: forward no RAW,
primeiro-toque SL vs ALVO. SL-1º = loser (-1.35). ALVO-1º = R_cris. Testa tambem BE (mover SL p/ entry apos +Xr).
Realista = NÃO transforma stop em win; só deixa correr os nao-stopados ate ao alvo estrutural."""
import sys, csv, json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
bars=[json.loads(l) for l in open(REPO/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl") if l.strip()]
def g(b,*k):
    for kk in k:
        if kk in b:return b[kk]
O=[float(g(b,'o','open')) for b in bars];H=[float(g(b,'h','high')) for b in bars];L=[float(g(b,'l','low')) for b in bars];C=[float(g(b,'c','close')) for b in bars];N=len(bars)
MY={int(r['num']):r for r in csv.DictReader(open(REPO/"research/results/l2_bpt_17_trades.csv"))}
CT={int(r['num']):r for r in csv.DictReader(open(REPO/"research/results/l2_bpt_cris_targets.csv"))}
COST=0.35
def firsttouch(bi,entry,sl,tgt,be_trig=None):
    """forward: primeiro-toque. Se be_trig (em R) atingido, SL->entry. Devolve (R_net, motivo)."""
    cur_sl=sl; armed=False
    for j in range(bi+1,N):
        hi=H[j]; lo=L[j]
        # arma BE se high alcançou +be_trig R (antes de checar stop desta barra p/ ser conservador: checa stop 1º)
        if lo<=cur_sl:  # stop
            r=(cur_sl-entry)/(entry-sl)-COST
            return round(r,2), ("BE" if armed and abs(cur_sl-entry)<1e-6 else "STOP")
        if tgt and hi>=tgt:
            return round((tgt-entry)/(entry-sl)-COST,2),"ALVO"
        if be_trig is not None and not armed and hi>=entry+be_trig*(entry-sl):
            cur_sl=entry; armed=True
        if j-bi>500: break
    return round((C[min(bi+500,N-1)]-entry)/(entry-sl)-COST,2),"HORIZ"
def run(be_trig,label):
    rows=[]; s=0
    for n in sorted(MY):
        m=MY[n];entry=float(m['entry']);sl=float(m['sl']);bi=int(m['bar_idx'])
        tgt=CT[n]['alvo_cris']; tgt=float(tgt) if tgt not in ('','None') else None
        r,mot=firsttouch(bi,entry,sl,tgt,be_trig); s+=r
        rows.append((n,m['regime'],r,mot))
    los=sum(1 for _,_,r,_ in rows if r<=0); win=sum(1 for _,_,r,_ in rows if r>0)
    print(f"\n### {label}: sumR={s:+.1f}  WR={100*win/len(rows):.0f}%  losers={los}/{len(rows)}")
    print("   " + "  ".join(f"#{n}:{r:+.2f}({mot[:4]})" for n,_,r,mot in rows))
    return s,rows
print("="*100);print("EXIT REALISTA por ALVO ESTRUTURAL (SL atual, first-touch causal) — NÃO transforma stop em win");print("="*100)
print("Referência let-run oficial: +36.2R (8 losers).  Teto-hindsight (irrealista): +87.6R (0 losers).")
sA,_=run(None,"A) hold-to-ALVO, SL atual (stop-first) — losers reais mantidos")
sB,_=run(1.0,"B) + BE após +1.0R (move SL p/ entry) — losers que correram viram ~0")
sC,_=run(1.5,"C) + BE após +1.5R")
print("\nNota: 'ALVO' = chegou ao alvo estrutural do Cris antes do SL. 'STOP' = loser real. 'BE' = breakeven pós-gestão.")
print("Realista >> let-run se vier dos NÃO-stopados a correr até estrutura; losers reais continuam losers.")
