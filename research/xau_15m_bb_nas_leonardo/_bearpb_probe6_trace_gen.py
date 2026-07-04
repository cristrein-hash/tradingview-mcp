#!/usr/bin/env python3
"""BEAR-PULLBACK · PROBE 6 — trace do gerador V3 (bug-hunt, outcome-blind):
replica probe4 e imprime o caminho de decisão barra a barra em 2025-10-30 04:00→11:00."""
import json, glob, bisect, io, contextlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
regime_h = ns["regime_hourcausal"]
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
U.sort(key=lambda r: r["cj_t"])
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def asof(t): return bisect.bisect_right(TS, t) - 1
ANCH = [{"cj_i": asof(r["cj_t"]), "cj_t": r["cj_t"], "g_sl": r["g_sl"]}
        for r in U if fv(r, "swept_prior_low") == 1 and fv(r, "rsi_low", 99) <= 37
        and fv(r, "g_sweep_depth", -9) >= 0.8 and fv(r, "in_demand") == 1]
ANCH.sort(key=lambda a: a["cj_i"]); AI = [a["cj_i"] for a in ANCH]
W0 = int(dt.datetime(2025, 10, 30, 4, 0, tzinfo=dt.timezone.utc).timestamp())
W1 = int(dt.datetime(2025, 10, 30, 11, 0, tzinfo=dt.timezone.utc).timestamp())
REG = {}
def reg(i):
    if i not in REG: REG[i] = regime_h(TS[i])
    return REG[i]
signals = []; consumed = set(); cooldown_until = -1; last_swing = None
def tr(i, msg):
    if W0 <= TS[i] <= W1:
        print(f"{dt.datetime.utcfromtimestamp(TS[i]).strftime('%m-%d %H:%M')}  {msg}")
for i in range(100, N):
    b = S[i]; ema = b.get("ema21"); atr = b.get("atr"); rsi = b.get("rsi")
    if not ema or not atr or rsi is None: tr(i, "sem ema/atr/rsi"); continue
    k = bisect.bisect_right(AI, i - 2) - 1
    if k < 0: continue
    a = ANCH[k]; age = i - a["cj_i"]
    if age > 32: tr(i, f"âncora {dt.datetime.utcfromtimestamp(a['cj_t']).strftime('%d %H:%M')} idade {age}>32"); continue
    if k in consumed: tr(i, f"âncora {dt.datetime.utcfromtimestamp(a['cj_t']).strftime('%d %H:%M')} JÁ CONSUMIDA"); continue
    flush_low_min = min(L[a["cj_i"] + 1:i + 1])
    if flush_low_min <= a["g_sl"]: tr(i, f"low quebrado ({flush_low_min:.2f}<= {a['g_sl']:.2f})"); continue
    if last_swing is not None and i <= cooldown_until and a["g_sl"] < last_swing and a["cj_i"] > cooldown_until - 48:
        cooldown_until = -1
    low96 = min(L[i - 95:i + 1])
    if (C[i] - low96) < 2.5 * atr: tr(i, f"M fail {(C[i]-low96)/atr:.2f}"); continue
    if not (C[i] > ema and (C[i] - ema) <= 0.6 * atr): tr(i, f"Pd fail dist {(C[i]-ema)/atr:.3f}"); continue
    if not (min(L[i - 2:i + 1]) > min(L[i - 10:i - 2])): tr(i, "HL fail"); continue
    lo20 = min(L[i - 19:i + 1]); hi20 = max(H[i - 19:i + 1])
    pos20 = (C[i] - lo20) / ((hi20 - lo20) or atr)
    if not (40 <= rsi <= 60 and pos20 <= 0.85): tr(i, f"Fw fail rsi {rsi:.1f} pos {pos20:.2f}"); continue
    if reg(i) != "BEAR": tr(i, f"regime {reg(i)}"); continue
    consumed.add(k)
    if i <= cooldown_until: tr(i, f"COOLDOWN até {dt.datetime.utcfromtimestamp(TS[min(cooldown_until,N-1)]).strftime('%d %H:%M')} (consumida)"); continue
    swing = min(L[i - 11:i + 1])
    if swing <= a["g_sl"]: tr(i, "swing<=g_sl"); continue
    sl = swing - 0.1 * atr; risk = C[i] - sl
    if not (1.2 * atr <= risk <= 4.0 * atr): tr(i, f"BANDA fail {risk/atr:.2f}"); continue
    cooldown_until = i + 48; last_swing = swing
    signals.append(i); tr(i, f"SINAL entry {C[i]:.2f} sl {sl:.2f}")
print(f"\ntotal sinais {len(signals)} (esperado 73)")
