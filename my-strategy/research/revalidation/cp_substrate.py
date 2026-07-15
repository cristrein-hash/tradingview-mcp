#!/usr/bin/env python3
"""SUBSTRATO Cp (GT = 5 velas de capitulacao do Cris, confirmado 2026-07-15) — dossies RAW CAUSAIS pelos
angulos de CAPITULACAO EM BEAR, para desenhar o entry. Reads (todos <= barra do fundo = causal):
 ① VELA DE CAPITULACAO: no [j-6,j], a barra de maior range -> range/ATR (expansao), mecha inferior
    (rejeicao), posicao do close (absorcao), direcao (down-flush).
 ② FLUSH: dd do topo 96b, velocidade (vel8/vel16), climax (ATR[j]/ATR[j-20]).
 ③ CONTEXTO: macro (BEAR/RANGE) — faca a cair; distancia a uma demanda/low anterior varrido (sweep).
 ④ RECLAIM (o V): MB3 causal apos o low (lag, R, desfecho 3R). SL=low_real-0.1ATR (LARGO no flush).
Problema central: separar capitulacao-que-segura de flush-que-continua (faca), causal, em BEAR.
RAW 15M direto do HD. causal_entry ja auditado sem lookahead. Grava CP_GT.json + CP_SUBSTRATE.json."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
# Cp GT = 5 velas de capitulacao do Cris (chart text_note -> panic low 15M)
CP_GT = [("k9iUAG", 1770015600, 1770210000), ("g5h12H", 1770339600, 1771448400),
         ("qlbAZ1", 1774242000, 1774270800), ("ndsA5l", 1781128800, 1781128800),
         ("ulsS4e", 1782781200, 1782907200)]
BLK = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
BUF = 12*3600

def panic_low(t0, t1):
    a = bisect.bisect_left(T, min(t0, t1)-BUF); b = bisect.bisect_right(T, max(t0, t1)+BUF)
    return min(range(a, b), key=lambda k: L[k]) if a < b else None

gt = []; doss = []
print(f"{'#':>2} {'fundo_dt':16} {'low':>6} {'macro':>5} {'capRng':>6} {'capWick':>7} {'capCpos':>7} {'dd%':>6} {'vel16':>6} {'atrExp':>6} {'sweep':>6} {'MB3':>11} {'lag':>4}")
for n, (eid, t0, t1) in enumerate(CP_GT, 1):
    j = panic_low(t0, t1)
    if j is None: continue
    atr = ATR[j] or 5.0
    # ① vela de capitulacao = maior range em [j-6, j]
    ck = max(range(max(0, j-6), j+1), key=lambda k: H[k]-L[k]); crng = max(1e-9, H[ck]-L[ck])
    cap_range = (H[ck]-L[ck])/atr; cap_wick = (min(O[ck], C[ck])-L[ck])/crng; cap_cpos = (C[ck]-L[ck])/crng
    # ② flush
    hi96 = max(H[max(0, j-96):j+1]); dd = 100*(hi96-L[j])/hi96
    vel16 = 100*(C[j]-C[j-16])/C[j-16]; atr_exp = atr/(ATR[j-20] or atr)
    # ③ sweep: varreu abaixo do swing-low anterior? (liquidez)
    lows = [L[p] for p in range(max(M_FRAC, j-LOWBACK), j-M_FRAC) if _is_swinglow(L, p, M_FRAC)]
    sweep = (lows[-1]-L[j])/atr if lows and L[j] < lows[-1] else 0.0
    # ④ reclaim
    e = causal_entry(S, j, "MB3"); mb = f"{e['o']}({e['RATR']}A)" if e else "—"; lag = e["lag"] if e else None
    gt.append({"id": eid, "t": T[j], "dt": ds(T[j]), "low": round(L[j], 1), "macro": macro_at(T[j])})
    doss.append({"id": eid, "dt": ds(T[j]), "low": round(L[j], 1), "macro": macro_at(T[j]),
                 "cap_range_atr": round(cap_range, 1), "cap_wick": round(cap_wick, 2), "cap_cpos": round(cap_cpos, 2),
                 "dd": round(dd, 1), "vel16": round(vel16, 1), "atr_exp": round(atr_exp, 1), "sweep_atr": round(sweep, 2),
                 "mb3": None if not e else {"o": e["o"], "R": e["R"], "RATR": e["RATR"], "lag": e["lag"], "bars": e["bars"]}})
    print(f"{n:>2} {ds(T[j]):16} {L[j]:>6.0f} {str(macro_at(T[j])):>5} {cap_range:>5.1f}x {cap_wick:>6.2f} {cap_cpos:>6.2f} {dd:>5.1f}% {vel16:>+5.1f}% {atr_exp:>5.1f}x {sweep:>5.2f} {mb:>11} {str(lag):>4}")

json.dump({"fundos": gt}, open(HERE/"results"/"CP_GT.json", "w"), indent=1)
json.dump({"fundos": doss}, open(HERE/"results"/"CP_SUBSTRATE.json", "w"), indent=1)
w = sum(1 for d in doss if d["mb3"] and d["mb3"]["o"] == "WIN")
print(f"\nAGREGADO: MB3 3R {w}/{len(doss)} · capRange med {statistics.median([d['cap_range_atr'] for d in doss]):.1f}x · "
      f"dd med {statistics.median([d['dd'] for d in doss]):.1f}% · sweep>0: {sum(1 for d in doss if d['sweep_atr']>0)}/{len(doss)} · macros {[d['macro'] for d in doss]}")