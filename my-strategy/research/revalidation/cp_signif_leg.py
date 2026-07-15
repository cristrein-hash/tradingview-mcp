#!/usr/bin/env python3
"""Cp CORRIGIDO (Cris 2026-07-15) — capitulação = FUNDO de PERNA SIGNIFICATIVA (não flush de vela única).
Assinatura das 5 GT: legMag 18-32x ATR (perna inteira do último swing-high ao low) + posNaPerna 76-100%.
Candidato = swing-low que é o fundo de uma perna de baixa SIGNIFICATIVA (legMag>=thr) + is_leg_bottom.
Entrada = reclaim (close>high[-1] & close>open) que segura acima do low. SL=low-0.1ATR, 3R first-touch.
Varre thresholds de legMag e mede hit-3R + streak + GT capturados + candidate count. RAW-only 15M."""
import bisect, statistics, datetime as dt
import sys; from pathlib import Path; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
M_FRAC = 3; LEGWIN = 480; HMAX = 480
BLK = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN = [x+86400 for x in MM.T]
macro_at = lambda t: reg[bisect.bisect_right(KN, t)-1] if bisect.bisect_right(KN, t)-1 >= 0 else None
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600)
    GT.append(T[min(range(aa, bb), key=lambda k: L[k])])

def leg_mag(j):
    hb = max(range(max(0, j-LEGWIN), j+1), key=lambda k: H[k]); atr = ATR[j] or 5.0
    return (H[hb]-L[j])/atr

def reclaim_entry(j):
    atr = ATR[j] or 5.0; sl = round(L[j]-0.1*atr, 2)
    for k in range(j+M_FRAC, min(N, j+96)):
        if L[k] <= sl: return None                          # perdeu o low = faca
        if C[k] > H[k-1] and C[k] > O[k]:                   # reclaim
            ent = C[k]; r = ent-sl
            if r <= 0.05*atr: continue
            tgt = ent+3*r; o = "OPEN"
            for m in range(k+1, min(N, k+HMAX+1)):
                if L[m] <= sl: o = "LOSS"; break
                if H[m] >= tgt: o = "WIN"; break
            return {"ei": k, "j": j, "R": round(r, 2), "o": o}
    return None

def build(legmin, need_leg_bottom=True):
    rows = []; seen = set()
    for p in SLB:
        if not (t_lo <= T[p] <= t_hi): continue
        if leg_mag(p) < legmin: continue
        if need_leg_bottom and not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
        e = reclaim_entry(p)
        if not e or e["ei"] in seen: continue
        seen.add(e["ei"]); e["gt"] = any(abs(T[p]-g) < 6*3600 for g in GT); rows.append(e)
    return rows

def rep(name, rows):
    v = [r for r in rows if r["o"] in ("WIN", "LOSS")]; w = sum(1 for r in v if r["o"] == "WIN")
    hit = 100*w/len(v) if v else 0; net = sum((3 if r["o"] == "WIN" else -1) for r in v)
    eq = pk = dd = strk = mx = 0
    for r in v:
        x = 3 if r["o"] == "WIN" else -1; eq += x; pk = max(pk, eq); dd = min(dd, eq-pk); strk = strk+1 if x < 0 else 0; mx = min(mx, -strk)
    ng = sum(1 for r in rows if r["gt"])
    print(f"  {name:<34} cand={len(rows):>3} N={len(v):>3} hit3R {hit:>4.0f}% NET {net:>+5}R DD {dd:>+4} streak {mx:>3} GT {ng}/5")

print(f"RAW: {N} barras · swing-lows {len(SLB)} · 2026 bear")
print("\n=== Cp: FUNDO DE PERNA SIGNIFICATIVA (legMag threshold) + reclaim ===")
for thr in (0, 6, 10, 12, 15, 18, 22):
    rep(f"legMag>={thr}x ATR + is_leg_bottom", build(thr))