#!/usr/bin/env python3
"""DISCRIMINADOR Cp (Cris 2026-07-15) — a skill do Cris (80% vs null 22%) esta nos READS mecanicos ou no
olho? Dos 260 flushes-capitulacao na bear 2026, compara os reads WIN vs LOSS e testa se algum read (ou
limiar) da uma subpopulacao com hit-3R >> 22%. Marca onde caem os 5 GT. Se nenhum read separa => Cp NAO
e mecanizavel (discricionario/forward). RAW 15M, causal_entry auditado."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp())
t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
GT_T = [1770015600+23400, 1770339600, 1774242000+26100, 1781128800, 1782781200]  # aprox (marca GT)

def reads(k):
    atr = ATR[k] or 5.0
    ck = max(range(max(0, k-6), k+1), key=lambda z: H[z]-L[z]); crng = max(1e-9, H[ck]-L[ck])
    cap_range = (H[ck]-L[ck])/atr; cap_wick = (min(O[ck], C[ck])-L[ck])/crng; cap_cpos = (C[ck]-L[ck])/crng
    hi96 = max(H[max(0, k-96):k+1]); dd = 100*(hi96-L[k])/hi96
    vel16 = 100*(C[k]-C[k-16])/C[k-16]; atr_exp = atr/(ATR[k-20] or atr)
    lows = [L[p] for p in range(max(M_FRAC, k-LOWBACK), k-M_FRAC) if _is_swinglow(L, p, M_FRAC)]
    sweep = (lows[-1]-L[k])/atr if lows and L[k] < lows[-1] else 0.0
    return dict(cap_range=cap_range, cap_wick=cap_wick, cap_cpos=cap_cpos, dd=dd, vel16=vel16, atr_exp=atr_exp, sweep=sweep)

seen = set(); rows = []
for k in range(120, N):
    if not (t_lo <= T[k] <= t_hi): continue
    atr = ATR[k] or 5.0
    if (H[k]-L[k]) < 1.8*atr or C[k] >= O[k]: continue
    e = causal_entry(S, k, "MB3")
    if not e or e["ei"] in seen or e["o"] == "OPEN": continue
    seen.add(e["ei"])
    r = reads(k); r["o"] = e["o"]; r["t"] = T[k]
    r["is_gt"] = any(abs(T[k]-g) < 6*3600 for g in GT_T)
    rows.append(r)

W = [r for r in rows if r["o"] == "WIN"]; Lo = [r for r in rows if r["o"] == "LOSS"]
print(f"Flushes resolvidos: {len(rows)} · WIN {len(W)} ({100*len(W)/len(rows):.0f}%) · LOSS {len(Lo)}")
print(f"\n{'read':10} {'WIN med':>9} {'LOSS med':>9} {'separa?':>8}")
for key in ("cap_range", "cap_wick", "cap_cpos", "dd", "vel16", "atr_exp", "sweep"):
    wm = statistics.median([r[key] for r in W]); lm = statistics.median([r[key] for r in Lo])
    sep = "sugestivo" if abs(wm-lm)/(abs(lm)+1e-9) > 0.3 else "nao"
    print(f"{key:10} {wm:>9.2f} {lm:>9.2f} {sep:>8}")
# melhor limiar univariado (marginal hit>=45% & N>=15)?
print(f"\nBusca de subpopulacao (limiar univariado, marginal hit-3R & N):")
best = None
for key in ("cap_range", "cap_wick", "cap_cpos", "dd", "sweep", "atr_exp"):
    vals = sorted(set(round(r[key], 1) for r in rows))
    for thr in vals:
        for sign in (">=", "<="):
            sub = [r for r in rows if (r[key] >= thr if sign == ">=" else r[key] <= thr)]
            if len(sub) < 15: continue
            hr = 100*sum(1 for r in sub if r["o"] == "WIN")/len(sub)
            if best is None or hr > best[0]: best = (hr, key, sign, thr, len(sub))
print(f"  melhor: {best[1]} {best[2]} {best[3]} -> hit-3R {best[0]:.0f}% (N={best[4]})  [null base 22%]")
# onde caem os 5 GT
gtr = [r for r in rows if r["is_gt"]]
print(f"\n5 GT no conjunto: {len(gtr)} encontrados · reads: " + ", ".join(f"{r['o']}(cr{r['cap_range']:.1f},dd{r['dd']:.0f},sw{r['sweep']:.1f})" for r in gtr))