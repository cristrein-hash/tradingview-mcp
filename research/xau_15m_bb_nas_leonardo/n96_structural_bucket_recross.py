#!/usr/bin/env python3
"""N96 · ESTRUTURAL-PRIMEIRO + RE-CRUZAMENTO POR BALDE (2026-07-08). Cris (repetido desde o inicio do 15M LONG):
indicadores so discriminam DEPOIS de ler onde o trade esta no REGIME MACRO + PERNA especifica.
Usa a REGUA canonica (ground-truth desenhado pelo Cris): regime_turnstate_engine/ground_truth/cris_regime_boxes.csv
(MACRO BULL/BEAR/RANGE + PULLBACK contra-tendencia). Mapeia cada um dos 96 trades ao seu balde estrutural,
e SO ENTAO recruza TODOS os indicadores x TODOS os TFs (WIN vs LOSER) DENTRO de cada balde.
Regua = hindsight p/ SEGMENTAR (nao e feature causal). SEM veredito — clareza de discriminacao por contexto."""
import csv, sys
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, famof
from agent_ctx_kit import ENTRIES
BOXCSV="/Users/cristrein/tradingview-mcp/regime_turnstate_engine/ground_truth/cris_regime_boxes.csv"
boxes=[b for b in csv.DictReader(open(BOXCSV))]
MACRO=[b for b in boxes if b["role"]=="MACRO"]
PULL=[b for b in boxes if b["role"]=="PULLBACK"]
def macro_of(t):
    hit=[b for b in MACRO if float(b["start"])<=t<=float(b["end"])]
    return hit[-1] if hit else None   # o mais recente que contem t
def pull_of(t):
    hit=[b for b in PULL if float(b["start"])<=t<=float(b["end"])]
    return hit[-1] if hit else None
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
def g(r,k):
    try: return float(r.get(k))
    except: return None
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]
TBYN={e["n"]:e["t"] for e in ENTRIES}

# ---- mapear cada trade ao balde estrutural ----
STR={}
for n in sorted(BYN):
    t=TBYN[n]; mb=macro_of(t); pb=pull_of(t)
    reg=mb["family"] if mb else "NONE"
    days_into=(t-float(mb["start"]))/86400 if mb else None
    dur=float(mb["dur_days"]) if mb else None
    frac=round(days_into/dur,2) if (days_into is not None and dur) else None  # posicao na perna (0=inicio,1=fim)
    STR[n]={"regime":reg,"in_pullback":(pb["family"]+"-in-"+pb["parent_fam"]) if pb else "",
            "frac_leg":frac,"out":BYN[n]["out"],"fam":famof(n)}

# ---- composicao dos baldes ----
print("="*84); print("BALDES ESTRUTURAIS (regime macro + pullback) — composicao dos 96"); print("="*84)
from collections import defaultdict
buckets=defaultdict(list)
for n in sorted(BYN):
    key=STR[n]["regime"]+("|"+STR[n]["in_pullback"] if STR[n]["in_pullback"] else "")
    buckets[key].append(n)
for key in sorted(buckets, key=lambda k:-len(buckets[k])):
    ns=buckets[key]; w=sum(1 for n in ns if BYN[n]["out"]=="1")
    fams=defaultdict(int)
    for n in ns: fams[STR[n]["fam"]]+=1
    print(f"  {key:<26} N={len(ns):>2} win={w:>2} hit={w/len(ns):.2f} | fam {dict(fams)}")
    print(f"       trades: {ns}")

# ---- RE-CRUZAMENTO: todos indicadores x TFs DENTRO de cada regime macro ----
def auc(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+=1 if x>y else (0.5 if x==y else 0)
    return c/t
print("\n"+"="*84); print("RE-CRUZAMENTO INTRA-REGIME — top separadores WIN-vs-LOSER dentro de cada regime"); print("="*84)
for reg in ("RANGE","BULL","BEAR"):
    ns=[n for n in sorted(BYN) if STR[n]["regime"]==reg]
    Win=[n for n in ns if BYN[n]["out"]=="1"]; Los=[n for n in ns if BYN[n]["out"]=="0"]
    print(f"\n### REGIME {reg}: N={len(ns)} win={len(Win)} los={len(Los)}"+(" (amostra pequena)" if len(ns)<12 else ""))
    if len(Win)<5 or len(Los)<5:
        print("   (win/los <5 dentro do regime — sem discriminacao estavel; reportado, nao induzido)"); continue
    ranked=[]
    for k in FEATS:
        wv=[g(BYN[n],k) for n in Win if g(BYN[n],k) is not None]
        lv=[g(BYN[n],k) for n in Los if g(BYN[n],k) is not None]
        if len(wv)<4 or len(lv)<4: continue
        a=auc(wv,lv); ranked.append((abs(a-0.5),k,round(st.median(wv),3),round(st.median(lv),3),round(a,3)))
    ranked.sort(reverse=True)
    print(f"   {'feature':<20}{'WIN':>9}{'LOS':>9}{'AUC':>7}  sep")
    for sep,k,wm,lm,a in ranked[:10]:
        print(f"   {k:<20}{wm:>9}{lm:>9}{a:>7}  {sep:.2f}")

# ---- posicao na perna (frac_leg): winners vs losers por regime ----
print("\n"+"="*84); print("POSICAO NA PERNA (frac_leg 0=inicio→1=fim do macro) — win vs los por regime"); print("="*84)
for reg in ("RANGE","BULL","BEAR"):
    ns=[n for n in sorted(BYN) if STR[n]["regime"]==reg and STR[n]["frac_leg"] is not None]
    if not ns: continue
    wl=[STR[n]["frac_leg"] for n in ns if BYN[n]["out"]=="1"]; ll=[STR[n]["frac_leg"] for n in ns if BYN[n]["out"]=="0"]
    print(f"  {reg:<6} win_frac_med={st.median(wl) if wl else None}  los_frac_med={st.median(ll) if ll else None}  (n_win={len(wl)} n_los={len(ll)})")

# ---- persist mapa estrutural ----
import json
json.dump({str(n):STR[n] for n in STR}, open(HERE+"/results/n96_structural_buckets.json","w"), indent=1)
print("\nsaved results/n96_structural_buckets.json · SEM veredito — recruzamento intra-regime entregue como dado.")
