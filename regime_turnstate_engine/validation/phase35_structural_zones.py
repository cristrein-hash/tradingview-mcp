#!/usr/bin/env python3
"""Cris (2026-07-01, INSIGHT VISUAL): as zonas TOP/BOTTOM de cada regime tornam-se níveis que o PRÓXIMO regime RETESTA.
Causal (a zona forma-se ANTES do regime seguinte). Extrair os dados que os 10 boxes desenhados pelo Cris revelam:
para cada zona, (1) de que segmento-fonte deriva, (2) se o(s) regime(s) seguinte(s) RETESTARAM a zona (preço entrou),
(3) onde o alvo fez o extremo relevante vs a zona, (4) quantos TRADES entraram dentro da zona e o R deles.
Tese: bottom-do-regime-anterior prediz capitulação-do-bear / entry-no-range. Só análise."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def dds(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
# 10 boxes desenhados pelo Cris (lidos via draw_get_properties)
BOX=[
 ("atlF8P",1991.26,1926.71,1684980000,1719352800,"TOP regime BEAR/RANGE anteriores"),
 ("ROZB2X",2144.73,2058.70,1697551200,1720504800,"TOP regimes BULL/RANGE anteriores"),
 ("MoAPGk",2305.92,2229.45,1709521200,1721613600,"TOP regime anterior"),
 ("eKxgPH",2542.55,2429.92,1723456800,1738551600,"BOTTOM regime anterior"),
 ("AmKxn8",2798.81,2710.98,1730426400,1752069600,"TOP regime anterior"),
 ("rCNv4C",3168.74,3036.48,1738206000,1759485600,"TOP regime anterior"),
 ("B9wh1W",3510.73,3377.64,1745373600,1762513200,"TOP regime anterior"),
 ("klGwY0",4007.03,3819.12,1759284000,1770202800,"BOTTOM regime anterior"),
 ("Oid3MH",4389.71,4221.37,1760925600,1770015600,"TOP regime anterior"),
 ("NCWct7",4601.27,4494.00,1766977200,1772607600,"TOP regime anterior"),
]
segs=json.load(open("/tmp/causal_segments_v10.json"))
def seg_at(t):
    for s in segs:
        if s['start']<=t<=s['end']: return s
    return None
# trades
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
trades=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);trades.append({"bi":bi,"t":T[bi],"entry":float(r["entry"]),"R":round(float(r["letrun_struct"])-0.35,2)})
print("="*100)
print("ZONAS ESTRUTURAIS DO CRIS — cada zona projeta o TOP/BOTTOM de um regime para os regimes seguintes")
print("="*100)
for bid,hi,lo,t0,t1,lab in BOX:
    # segmento-fonte: o que termina imediatamente antes/em t0
    src=None
    for s in segs:
        if s['end']<=t0+4*3600: src=s
    src_str=f"{src['regime']}[{dds(src['start'])}->{dds(src['end'])}] hi{src['hi']:.0f}/lo{src['lo']:.0f}" if src else "?"
    # regime-alvo: segmentos que começam >= t0 (os que a zona projeta)
    tgts=[s for s in segs if t0<=s['start']<t1]
    # preço entrou na zona no intervalo [t0,t1]?
    i0=bisect.bisect_left(T,t0);i1=bisect.bisect_right(T,t1)
    touched=any(L[j]<=hi and H[j]>=lo for j in range(i0,i1))
    # extremo do alvo dentro do intervalo
    lowp=min(L[i0:i1]) if i1>i0 else None;highp=max(H[i0:i1]) if i1>i0 else None
    # trades dentro da zona (entry em [lo,hi]) e no intervalo
    intr=[x for x in trades if t0<=x["t"]<=t1 and lo<=x["entry"]<=hi]
    wr=100*sum(1 for x in intr if x["R"]>0)/len(intr) if intr else 0
    sr=sum(x["R"] for x in intr)
    print(f"\n[{bid}] {lab}  zona {lo:.0f}–{hi:.0f}  ({dds(t0)}->{dds(t1)})")
    print(f"   fonte(regime anterior) = {src_str}")
    print(f"   alvos seguintes = {[s['regime']+'['+dds(s['start'])+']' for s in tgts][:6]}")
    print(f"   preço RETESTOU a zona? {touched}  | low no período {lowp:.0f} / high {highp:.0f}")
    print(f"   TRADES com entry DENTRO da zona: {len(intr)} | WR {wr:.0f}% | sumR {sr:+.1f}")
# agregado: trades dentro de QUALQUER zona-bottom vs fora
def in_any(x,filt):
    for bid,hi,lo,t0,t1,lab in BOX:
        if filt in lab and t0<=x["t"]<=t1 and lo<=x["entry"]<=hi: return True
    return False
allt=[x for x in trades if dt.datetime.utcfromtimestamp(x["t"]).year>=2023]
for filt in ("BOTTOM","TOP"):
    inside=[x for x in allt if in_any(x,filt)]
    if inside:
        print(f"\n>>> trades dentro de zona '{filt} regime anterior': N={len(inside)} WR={100*sum(1 for x in inside if x['R']>0)/len(inside):.0f}% sumR={sum(x['R'] for x in inside):+.1f}")
