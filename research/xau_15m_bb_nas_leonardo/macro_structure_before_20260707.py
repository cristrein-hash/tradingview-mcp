#!/usr/bin/env python3
"""ESTRUTURA MACRO ANTERIOR (6-9 meses) por VELA DE FUNDO (2026-07-07, nova meta Cris).
Ordem que funciona: ESTRUTURA primeiro. Para cada vela de fundo marcada, computar a estrutura macro
dos ~6-9 meses anteriores (causal, só barras <= t_fundo) e testar a regra do Cris:
"FUNDO NÃO VÁLIDO SE PERNA BEAR CLARA ANTECEDE". Validar contra os 3 inválidos marcados + 1 pequena-
acumulação. Sem look-ahead. Features macro (dias):
  - regime dominante 6-9m (fração de dias BULL vs BEAR via EMA50/EMA100 slope)
  - perna BEAR clara antes: maior queda pico->vale em ATR-dia nos últimos 6m que TERMINA perto do fundo
  - posição do fundo na estrutura macro (retração da última perna de alta macro)
  - distância a topo/fundo macro anterior
SANITY_PROBE: catálogo de tags (não teste de métrica); features macro causais dia; validar regra
de invalidação declarada pelo Cris contra as marcações dele."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
# séries 15M
series = {}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
# agregação diária
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"],"o":b.get("o",b["c"]),"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(vals,n):
    k=2/(n+1); e=vals[0]
    out=[e]
    for v in vals[1:]: e=v*k+e*(1-k); out.append(e)
    return out
E50=ema(DC,50); E100=ema(DC,100)
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]

cat = json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
fundos = sorted([n for n in cat["notes"]["FUNDO"] if n["t"]], key=lambda x:int(x["t"]))
inval = sorted([n for n in cat["notes"].get("INVALIDO",[]) if n["t"]], key=lambda x:int(x["t"]))

def macro_before(t_fundo, months=8):
    di = bisect.bisect_right(DT, t_fundo)-1
    if di < 60: return None
    w0 = max(0, di - months*21)  # ~21 dias úteis/mês
    seg = range(w0, di+1)
    # regime dominante: fração de dias com EMA50>EMA100 (BULL) vs EMA50<EMA100 (BEAR)
    bull = sum(1 for i in seg if E50[i] > E100[i]); bear = sum(1 for i in seg if E50[i] < E100[i])
    nseg = len(list(seg))
    # perna BEAR clara ANTES do fundo: maior queda pico->vale (ATR-dia) nos últimos ~2m que termina <=15 dias do fundo
    recent = range(max(0, di-42), di+1)
    peak_i = max(recent, key=lambda i: DH[i]);
    # vale após o pico até o fundo
    after_peak = range(peak_i, di+1)
    vale_i = min(after_peak, key=lambda i: DL[i]) if len(list(after_peak))>1 else di
    drop_atr = (DH[peak_i]-DL[vale_i])/max(0.01, ATRd[di])
    bars_since_vale = di - vale_i
    # perna de alta macro (para retração): último swing low macro nos 6m
    seg6 = range(max(0,di-126), di+1)
    lo_i = min(seg6, key=lambda i: DL[i]); hi_after = max(range(lo_i,di+1), key=lambda i: DH[i]) if lo_i<di else di
    up_leg = DH[hi_after]-DL[lo_i]
    ci = bisect.bisect_right(TS, t_fundo)-1
    flo = LO[ci]
    retr_up = (DH[hi_after]-flo)/max(0.01, up_leg) if up_leg>0 else None
    return {"di":di,"bull_frac":round(bull/nseg,2),"bear_frac":round(bear/nseg,2),
            "regime":"BULL" if bull>bear*1.3 else ("BEAR" if bear>bull*1.3 else "RANGE"),
            "drop_before_atr":round(drop_atr,1),"bars_since_vale":bars_since_vale,
            "retr_up_macro":round(retr_up,2) if retr_up else None,
            "ema50_gt_100": int(E50[di]>E100[di])}

print("=== ESTRUTURA MACRO ANTERIOR (6-9m) por VELA DE FUNDO ===")
print(f"{'data':<12} {'regime':<6} {'bull%':>5} {'bear%':>5} {'drop_ant_ATR':>12} {'d_vale':>7} {'retr_up':>8} {'e50>100':>7}")
recs=[]
for f in fundos:
    m = macro_before(int(f["t"]))
    if not m: continue
    recs.append({"date":ds(f["t"]),"t":int(f["t"]),**m})
    print(f"{ds(f['t']):<12} {m['regime']:<6} {100*m['bull_frac']:>4.0f}% {100*m['bear_frac']:>4.0f}% "
          f"{m['drop_before_atr']:>12.1f} {m['bars_since_vale']:>7} {str(m['retr_up_macro']):>8} {m['ema50_gt_100']:>7}")
print("\n=== INVÁLIDOS marcados pelo Cris (regra: perna BEAR clara antecede / pequena acumulação) ===")
for iv in inval:
    m = macro_before(int(iv["t"]))
    tag = iv["text"].strip().replace(chr(10)," ")
    if m:
        print(f"{ds(iv['t'])}  regime {m['regime']} bear%{100*m['bear_frac']:.0f} drop_ant {m['drop_before_atr']:.1f}ATR e50>100={m['ema50_gt_100']} :: {tag}")
json.dump(recs, open(HERE/"results"/"macro_structure_before_20260707.json","w"), indent=1)
print("\nOK -> results/macro_structure_before_20260707.json")
