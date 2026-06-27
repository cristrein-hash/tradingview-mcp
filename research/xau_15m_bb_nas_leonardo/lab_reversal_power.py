#!/usr/bin/env python3
"""LAB POTÊNCIA DAS REVERSÕES (Cris 2026-06-27): medir a EXTENSÃO da perna lançada por cada um dos 414 fundos/topos
verdadeiros (true_reversals_M8.csv) e classificar do mais PODEROSO ao mais FRACO.
CARACTERIZAÇÃO (gabarito) — usa dado FORWARD por design (mede a perna que de fato ocorreu); NÃO é feature causal de
entrada. Série CONTÍNUA juntando os 8 blocos (dedup por t) p/ pernas que duram dias/semanas/meses.
Definição da perna:
  BOT: do fundo, anda pra frente enquanto NÃO faz mínima < fundo (fundo segurou). Fim = 1ª violação (ou fim da série).
       MFE = maior high no trecho. ext_atr=(MFE-P)/ATR · ext_pct · ext_usd · dur (até o pico) · consistência.
  TOP: espelho (anda enquanto NÃO faz máxima > topo; MFE pra baixo).
Consistência: path_eff = move_líquido / soma|Δclose| no trecho até o pico (1.0=reta perfeita) + max_giveback_atr (maior
recuo do pico, em ATR, antes do pico final). Cross-check com out_atr do zigzag M8 (perna até o próximo pivô).
Saída: reversal_power.csv (ranqueado) + tabela por camadas. RAW. Sem estratégia/WR. """
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent

# --- série global contínua (8 blocos, dedup por t) ---
bars={}
for p in sorted((HERE/"primitives").glob("*.primitives.json")):
    for b in json.loads(p.read_text())["series"]:
        bars.setdefault(b["t"], b)        # 1ª ocorrência vence (boundaries duplicados)
S=[bars[t] for t in sorted(bars)]
T2I={b["t"]:i for i,b in enumerate(S)}
print(f"série global contínua: {len(S)} barras 15M ({S[0]['t']}→{S[-1]['t']})")

rev=sorted((r for r in csv.DictReader(open(HERE/"true_reversals_M8.csv"))), key=lambda r:int(r["t"]))
def f(x): return float(x) if x not in (None,"","None") else None
_same=sum(1 for k in range(len(rev)-1) if rev[k]["kind"]==rev[k+1]["kind"])
print(f"adjacencias mesmo-tipo no gabarito (emendas de bloco): {_same} — perna termina no PICO (FIX P1, nao corrompe path_eff/giveback)")

def durability(i,P,kind):
    """(B) até o fundo/topo ser violado: dias e MFE_atr. Mede significância secular (não força local)."""
    if kind=="BOT":
        mfe=P
        for k in range(i+1,len(S)):
            if S[k]["l"]<P: return k-i, mfe-P
            mfe=max(mfe,S[k]["h"])
    else:
        mfe=P
        for k in range(i+1,len(S)):
            if S[k]["h"]>P: return k-i, P-mfe
            mfe=min(mfe,S[k]["l"])
    return len(S)-1-i, abs(mfe-P)  # truncado (nunca violado na janela)

rows=[]
for n,r in enumerate(rev):
    t=int(r["t"]); kind=r["kind"]; P=f(r["price"]); A=f(r["atr"]); i=T2I.get(t)
    if i is None or not A: continue
    # (A) PERNA LOCAL = deste pivô ao PRÓXIMO pivô confirmado (zigzag alterna BOT/TOP)
    nxt=rev[n+1] if n+1<len(rev) else None
    trunc=nxt is None
    j=T2I.get(int(nxt["t"])) if nxt else len(S)-1
    seg=S[i:j+1]
    # FIX P1 (DA): perna termina no PICO (MFE), nao no proximo pivo (corrige emendas TOP->TOP/BOT->BOT
    # e mede consistencia so na subida ate o pico, nao na ida-e-volta).
    if kind=="BOT":
        peak_k=i+max(range(len(seg)),key=lambda x:seg[x]["h"]); ext=S[peak_k]["h"]-P
    else:
        peak_k=i+min(range(len(seg)),key=lambda x:seg[x]["l"]); ext=P-S[peak_k]["l"]
    legseg=S[i:peak_k+1]
    gpeak=P; gmax=0.0
    for b in legseg[1:]:
        if kind=="BOT": gpeak=max(gpeak,b["h"]); gmax=max(gmax,gpeak-b["l"])
        else:           gpeak=min(gpeak,b["l"]); gmax=max(gmax,b["h"]-gpeak)
    trav=sum(abs(legseg[x]["c"]-legseg[x-1]["c"]) for x in range(1,len(legseg)))
    dur_bars=peak_k-i; leg_atr=ext/A
    pe=ext/trav if trav>0 else None
    db_bars,db_ext=durability(i,P,kind)
    rows.append({"date":r["date"],"t":t,"kind":kind,"price":round(P,2),"atr":round(A,2),
                 "leg_atr":round(leg_atr,2),"leg_pct":round(100*ext/P,2),"leg_usd":round(ext,1),
                 "leg_days":round(dur_bars*15/60/24,2),
                 "path_eff":round(pe,2) if pe is not None else None,"giveback_atr":round(gmax/A,2),
                 "power_score":round(leg_atr*pe,1) if pe is not None else None,
                 "durab_days":round(db_bars*15/60/24,1),"durab_atr":round(db_ext/A,1),
                 "zigzag_out_atr":f(r["out_atr"]),"truncated":int(trunc),"yr":r["yr"]})

# --- classificação por camada (quantis de ext_atr, separado BOT/TOP) ---
def tier_labels(vals):
    qs=st.quantiles(vals,n=10) if len(vals)>=10 else [max(vals)]*9
    # camadas: MONSTRO>=p90, FORTE>=p70, MÉDIO>=p40, FRACO<p40
    def lab(v):
        if v>=qs[8]: return "MONSTRO"
        if v>=qs[6]: return "FORTE"
        if v>=qs[3]: return "MEDIO"
        return "FRACO"
    return lab, qs
for kind in ("BOT","TOP"):
    g=[r for r in rows if r["kind"]==kind]
    lab,_=tier_labels([r["leg_atr"] for r in g])
    labp,_=tier_labels([r["power_score"] for r in g if r["power_score"] is not None])
    for r in g:
        r["tier"]=lab(r["leg_atr"])                                  # por TAMANHO
        r["tier_clean"]=labp(r["power_score"]) if r["power_score"] is not None else "?"  # tamanho x consistencia

rows.sort(key=lambda r:(-r["leg_atr"]))
with open(HERE/"reversal_power.csv","w",newline="") as fo:
    w=csv.DictWriter(fo,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# --- relatório ---
def summ(g,name):
    e=[r["leg_atr"] for r in g]; d=[r["leg_days"] for r in g]; pe=[r["path_eff"] for r in g if r["path_eff"] is not None]
    print(f"\n{name} (n={len(g)}): leg_atr med {st.median(e):.1f} (min {min(e):.1f}/max {max(e):.1f}) | "
          f"leg_dur med {st.median(d):.1f}d (max {max(d):.0f}d) | path_eff med {st.median(pe):.2f}")
    from collections import Counter; print("   camadas (por leg_atr):",dict(Counter(r['tier'] for r in g)))
bots=[r for r in rows if r["kind"]=="BOT"]; tops=[r for r in rows if r["kind"]=="TOP"]
summ(bots,"FUNDOS (BOT, perna LONG)"); summ(tops,"TOPOS (TOP, perna SHORT)")

def tbl(g,title):
    print(f"\n{title}")
    print(f"{'data':<17}{'legATR':>7}{'eff':>5}{'pwr':>6}{'dias':>6}{'gb':>5}{'durDias':>8}{'tier':>8}{'tierClean':>10}")
    for r in g:
        print(f"{r['date']:<17}{r['leg_atr']:>7}{str(r['path_eff']):>5}{str(r['power_score']):>6}{r['leg_days']:>6}{r['giveback_atr']:>5}{r['durab_days']:>8}{r['tier']:>8}{r['tier_clean']:>10}")
tbl([x for x in rows if x['kind']=='BOT'][:12], "=== TOP 12 FUNDOS por TAMANHO da perna (legATR) ===")
print("\n=== TOP 12 FUNDOS por POTÊNCIA (tamanho x consistência = power_score) ===")
tbl(sorted([x for x in rows if x['kind']=='BOT'],key=lambda r:-(r['power_score'] or 0))[:12], "")
tbl([x for x in rows if x['kind']=='BOT'][-5:], "=== 5 FUNDOS mais FRACOS (legATR) ===")
print("\n-> reversal_power.csv (414; rank por leg_atr; cols power_score, tier, tier_clean, durab_*)")
