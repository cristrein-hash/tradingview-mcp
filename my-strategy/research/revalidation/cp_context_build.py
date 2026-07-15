#!/usr/bin/env python3
"""SUBSTRATO Cp — CAPITULAÇÃO AGUDA (engine distinto, Cris 2026-07-15) — dossiês RAW CAUSAIS dos 5
fundos C_PANIC_aguda pelos ângulos de capitulação, para a leitura contextual antes de desenhar:
 ① FLUSH: queda do topo recente ao low (dd) + VELOCIDADE (ret 8/16 barras para dentro do low)
 ② CLÍMAX: expansão de ATR/range (ATR[j] vs ATR[j-20]); vela de capitulação (range/mecha)
 ③ CONTEXTO MACRO: regime no fundo + crash disparou? (a tensão: reversão vs início de markdown)
 ④ RECLAIM (o V): MB3 causal após o low — lag, R, desfecho 3R (SL low-real=panic low, LARGO)
Problema central declarado: distinguir CAPITULAÇÃO-que-reverte de MARKDOWN-começa (faca a cair), causal.
RAW 15M direto do HD. Nada é feature ainda. Grava results/CP_CONTEXT.json + painel."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series, causal_entry, LOWBACK
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
CP = sorted([f for f in GT["fundos"] if f.get("subclasse") == "C_PANIC_aguda"], key=lambda x: x["t"])

# blocos que cobrem as datas dos 5 Cp
def blocks_for(dates):
    ep = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    out = set()
    for p in sorted(RAW.glob("XAUUSD_15m_replay_*.jsonl.gz")):
        try:
            a, b = p.name.replace("XAUUSD_15m_replay_", "").split(".jsonl")[0].split("_to_"); b = b.split("_")[0]
            ta, tb = ep(a), ep(b)+86400*95
        except Exception: continue
        for d in dates:
            if ta-30*86400 <= d <= tb: out.add(str(p))
    return sorted(out)

BLK = blocks_for([int(f["t"]) for f in CP])
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
def macro_at(t0):
    i = bisect.bisect_right(KN1, t0)-1
    return reg[i] if i >= 0 else None

print(f"C_PANIC_aguda N={len(CP)}")
print(f"{'#':>2} {'data':16} {'macro':>5} {'crash':>5} {'dd%':>6} {'vel8%':>6} {'vel16%':>6} {'atrExp':>6} {'MB3':>12} {'lag':>4} {'R→3R bars':>9}")
doss = []
for n, f in enumerate(CP, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    if j < 40: continue
    atr = ATR[j] or 5.0
    hi96 = max(H[max(0, j-96):j+1]); dd = 100*(hi96-L[j])/hi96
    vel8 = 100*(C[j]-C[j-8])/C[j-8]; vel16 = 100*(C[j]-C[j-16])/C[j-16]
    atr_exp = atr/(ATR[j-20] or atr)
    crash = any((C[k]/C[k-2]-1)*100 <= -6.0 for k in range(max(2, j-16), j+1))  # crash 15M-scale? (proxy)
    e = causal_entry(S, j, "MB3")
    mb = f"{e['o']}({e['RATR']}A)" if e else "—"
    lag = e["lag"] if e else None; bars = e["bars"] if (e and e["o"] == "WIN") else None
    doss.append({"n": n, "date": ds(t0), "macro": macro_at(t0), "crash": crash, "dd": round(dd, 1),
                 "vel8": round(vel8, 1), "vel16": round(vel16, 1), "atr_exp": round(atr_exp, 1),
                 "mb3": None if not e else {"o": e["o"], "R": e["R"], "RATR": e["RATR"], "lag": e["lag"], "bars": e["bars"]}})
    print(f"{n:>2} {ds(t0):16} {str(macro_at(t0)):>5} {str(crash):>5} {dd:>5.1f}% {vel8:>+5.1f}% {vel16:>+5.1f}% {atr_exp:>5.1f}x {mb:>12} {str(lag):>4} {str(bars):>9}")

json.dump({"fundos": doss}, open(HERE/"results"/"CP_CONTEXT.json", "w"), indent=1)
w = sum(1 for d in doss if d["mb3"] and d["mb3"]["o"] == "WIN")
print(f"\nAGREGADO: MB3 3R {w}/{len(doss)} · dd med {statistics.median([d['dd'] for d in doss]):.1f}% · "
      f"vel16 med {statistics.median([d['vel16'] for d in doss]):.1f}% · macro: {[d['macro'] for d in doss]}")