#!/usr/bin/env python3
"""N96 · ESTRUTURAL-PRIMEIRO CAUSAL (2026-07-08). Refaz o bucketing com o DETECTOR v5 CANONICO CAUSAL
(engine_substrate4_v5_hourcausal.py: override 1H no ultimo bar fechado <= t + estavel do dia D-1, ZERO look-ahead).
Carrega o codigo VERBATIM (exec das linhas 1..73 = maquina + regime_hourcausal), sem reinventar nem correr a
analise do substrato #4. Mapeia os 96 entries ao regime CAUSAL, bucketiza, R por balde, recruza indicadores
intra-regime, e compara com a regua hindsight (concordancia). SEM veredito."""
import csv, sys, statistics as st
from collections import defaultdict
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, famof
from agent_ctx_kit import ENTRIES
# ---- carregar detector v5 causal VERBATIM (linhas 1..73) ----
SRC=HERE+"/engine_substrate4_v5_hourcausal.py"
core="\n".join(open(SRC).read().splitlines()[:73])
ns={"__file__":SRC}
exec(core, ns)
regime_hourcausal=ns["regime_hourcausal"]

rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
def g(r,k):
    try: return float(r.get(k))
    except: return None
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]
TBYN={e["n"]:e["t"] for e in ENTRIES}

# ---- regime CAUSAL por entry ----
REG={n:regime_hourcausal(TBYN[n]) for n in sorted(BYN)}

# comparar com regua hindsight (se existir mapa)
try:
    import json; HS=json.load(open(HERE+"/results/n96_structural_buckets.json")); HSREG={int(k):v["regime"] for k,v in HS.items()}
except Exception:
    HSREG={}

print("="*84); print("REGIME CAUSAL v5 (hour-causal) por entry — composicao dos 96"); print("="*84)
buckets=defaultdict(list)
for n in sorted(BYN): buckets[REG[n]].append(n)
def Rof(ns):
    w=sum(1 for n in ns if BYN[n]["out"]=="1"); l=len(ns)-w; return w,l,w*3-l
for reg in sorted(buckets, key=lambda k:-len(buckets[k])):
    ns=buckets[reg]; w,l,R=Rof(ns)
    fams=defaultdict(int)
    for n in ns: fams[famof(n)]+=1
    print(f"  {reg:<7} N={len(ns):>2} win={w:>2} los={l:>2} hit={w/len(ns):.2f} R={R:+d} | fam {dict(fams)}")
    print(f"       trades: {ns}")

# concordancia causal vs hindsight
if HSREG:
    agree=sum(1 for n in sorted(BYN) if REG[n]==HSREG.get(n));
    print(f"\nconcordancia CAUSAL vs regua-hindsight: {agree}/96 = {agree/96:.2f}")
    disc=[(n,REG[n],HSREG.get(n)) for n in sorted(BYN) if REG[n]!=HSREG.get(n)]
    print(f"  divergencias ({len(disc)}): "+", ".join(f"#{n}:{c}vs{h}" for n,c,h in disc[:30]))

# ---- CORTE CAUSAL: e' profit-positivo cortar BEAR-causal? ----
print("\n"+"="*84); print("CORTE CAUSAL ='SKIP regime BEAR' — impacto operacional (causal, sem look-ahead)"); print("="*84)
base_ns=[n for n in sorted(BYN)]; bw,bl,bR=Rof(base_ns)
keep=[n for n in base_ns if REG[n]!="BEAR"]; cut=[n for n in base_ns if REG[n]=="BEAR"]
kw,kl,kR=Rof(keep); cw,cl,cR=Rof(cut)
print(f"  BASE   N={len(base_ns)} hit={bw/len(base_ns):.3f} R={bR:+d}")
print(f"  KEEP(!=BEAR) N={len(keep)} hit={(kw/len(keep) if keep else 0):.3f} R={kR:+d}")
print(f"  CUT (BEAR)   N={len(cut)} hit={(cw/len(cut) if cut else 0):.3f} R={cR:+d}  (win cortados={cw} los cortados={cl})")
print(f"  --> cortar BEAR-causal: dR={kR-bR:+d} (positivo=lucrativo), corta {len(cut)} trades")
print(f"  winners sacrificados: {sorted(n for n in cut if BYN[n]['out']=='1')}")
print(f"  losers cortados:      {sorted(n for n in cut if BYN[n]['out']=='0')}")

# ---- RE-CRUZAMENTO intra-regime CAUSAL ----
def auc(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+=1 if x>y else (0.5 if x==y else 0)
    return c/t
print("\n"+"="*84); print("RE-CRUZAMENTO INTRA-REGIME CAUSAL — top separadores WIN-vs-LOSER"); print("="*84)
for reg in ("RANGE","BULL","BEAR"):
    ns=buckets.get(reg,[]); Win=[n for n in ns if BYN[n]["out"]=="1"]; Los=[n for n in ns if BYN[n]["out"]=="0"]
    print(f"\n### {reg} CAUSAL: N={len(ns)} win={len(Win)} los={len(Los)}")
    if len(Win)<5 or len(Los)<5:
        print("   (win/los <5 — sem discriminacao estavel; reportado)"); continue
    ranked=[]
    for k in FEATS:
        wv=[g(BYN[n],k) for n in Win if g(BYN[n],k) is not None]; lv=[g(BYN[n],k) for n in Los if g(BYN[n],k) is not None]
        if len(wv)<4 or len(lv)<4: continue
        a=auc(wv,lv); ranked.append((abs(a-0.5),k,round(st.median(wv),3),round(st.median(lv),3),round(a,3)))
    ranked.sort(reverse=True)
    print(f"   {'feature':<20}{'WIN':>9}{'LOS':>9}{'AUC':>7}  sep")
    for sep,k,wm,lm,a in ranked[:10]: print(f"   {k:<20}{wm:>9}{lm:>9}{a:>7}  {sep:.2f}")
import json; json.dump({str(n):REG[n] for n in REG}, open(HERE+"/results/n96_causal_regime.json","w"), indent=1)
print("\nsaved results/n96_causal_regime.json · SEM veredito — dado causal p/ DA.")
