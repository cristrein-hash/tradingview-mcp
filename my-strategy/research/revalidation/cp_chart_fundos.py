#!/usr/bin/env python3
"""Cp EXPANDIDO — os 5 fundos "FUNDO CAPITULAÇÃO" que o Cris marcou no chart (text_note, extraidos via
MCP 2026-07-15). Espalhados pela bear de 2026 (Fev-Jun), nao so o cluster de Marco do GT. Mapeia cada
nota ao PANIC LOW real no 15M RAW (menor low na janela da nota) e caracteriza pelos angulos de Cp
(flush/velocidade/climax/macro + MB3 causal). Auditoria de lookahead ja validada no modulo causal_entry."""
import json, bisect, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series, causal_entry
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
# notas extraidas do chart (id -> pontos [t,price]); janela = [min t, max t]
NOTES = [
    ("k9iUAG", 1770015600, 1770210000), ("g5h12H", 1770339600, 1771448400),
    ("qlbAZ1", 1774242000, 1774270800), ("ndsA5l", 1781128800, 1781128800),
    ("ulsS4e", 1782781200, 1782907200),
]
BLK = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
BUF = 12*3600

print(f"{'nota':7} {'janela':25} {'panic_low_dt':16} {'low':>7} {'macro':>5} {'dd%':>6} {'vel16%':>7} {'atrExp':>6} {'MB3':>12} {'lag':>4}")
out = []
for eid, t0, t1 in NOTES:
    lo_t, hi_t = min(t0, t1)-BUF, max(t0, t1)+BUF
    a = bisect.bisect_left(T, lo_t); b = bisect.bisect_right(T, hi_t)
    if a >= b: print(f"{eid:7} {ds(lo_t)}..{ds(hi_t)}  SEM-DADOS"); continue
    jlow = min(range(a, b), key=lambda k: L[k])            # panic low = menor low na janela da nota
    j = jlow; atr = ATR[j] or 5.0
    hi96 = max(H[max(0, j-96):j+1]); dd = 100*(hi96-L[j])/hi96
    vel16 = 100*(C[j]-C[j-16])/C[j-16]; atr_exp = atr/(ATR[j-20] or atr)
    e = causal_entry(S, j, "MB3")
    mb = f"{e['o']}({e['RATR']}A)" if e else "—"; lag = e["lag"] if e else None
    out.append({"id": eid, "fundo_dt": ds(T[j]), "t": T[j], "low": round(L[j], 1), "macro": macro_at(T[j]),
                "dd": round(dd, 1), "vel16": round(vel16, 1), "atr_exp": round(atr_exp, 1),
                "mb3": None if not e else {"o": e["o"], "R": e["R"], "RATR": e["RATR"], "lag": e["lag"]}})
    print(f"{eid:7} {ds(lo_t)}..{ds(hi_t)[5:]:10} {ds(T[j]):16} {L[j]:>7.0f} {str(macro_at(T[j])):>5} {dd:>5.1f}% {vel16:>+6.1f}% {atr_exp:>5.1f}x {mb:>12} {str(lag):>4}")
json.dump({"fundos": out}, open(HERE/"results"/"CP_CHART_FUNDOS.json", "w"), indent=1)
w = sum(1 for d in out if d["mb3"] and d["mb3"]["o"] == "WIN")
print(f"\n{len(out)} fundos capitulacao do Cris · MB3 3R {w}/{len(out)} · macros: {[d['macro'] for d in out]}")