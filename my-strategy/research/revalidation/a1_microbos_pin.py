#!/usr/bin/env python3
"""PINAR a definição final do MICRO-BOS (ordem Cris 2026-07-14): resolver A1_01 (MB1 dispara tarde,
candle-de-low largo) e A1_03 (MB2 no-trig, candle-anterior largo). Causa comum: ancorar a UM candle
que pode ser largo. Testo definições e escolho a robusta:
  MB1 = fecho verde > high do candle do LOW (ancora fixa low-bar)
  MB2 = fecho verde > high da barra ANTERIOR ao low (ancora fixa prior-bar)
  MB3 = fecho verde > high da barra IMEDIATAMENTE anterior (break ROLANTE = 1o micro-thrust, robusto)
  MB4 = fecho verde > max(high low-bar, high prior-bar)
Mesma âncora de low robusta + SL=low−0.1ATR + 3R SL-first. RAW 15M direto do HD. Só medição."""
import gzip, json, bisect, datetime as dt, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
LOWBACK, LOWFWD, TRIG_WIN, HORIZON = 16, 8, 48, 480
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
bars = {}
for blk in BLOCKS:
    with gzip.open(RAW/blk, "rt") as fh:
        for l in fh:
            i = l.find('"ohlcv":')
            if i < 0: continue
            s = l.find('[', i); e = l.find(']', s)
            if s < 0 or e < 0: continue
            try: arr = json.loads(l[s:e+1])
            except Exception: continue
            for b in arr:
                t = b.get("time")
                if t is None: continue
                if t not in bars: bars[t] = [b["open"], b["high"], b["low"], b["close"]]
                else: bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
T = sorted(bars); O=[bars[t][0] for t in T]; H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]
N = len(T); EMA=[None]*N; ATR=[None]*N; ema=None; kE=2/22; trs=[]
for i in range(N):
    ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i]=ema
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
def outc(ei, sl, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if L[m] <= sl: return "LOSS", m-ei
        if H[m] >= tgt: return "WIN", m-ei
    return "OPEN", None
def fire(al, kind):
    for k in range(al+1, min(N, al+TRIG_WIN+1)):
        if not (C[k] > O[k]): continue
        ref = {"MB1": H[al], "MB2": H[al-1] if al > 0 else H[al], "MB3": H[k-1],
               "MB4": max(H[al], H[al-1] if al > 0 else H[al])}[kind]
        if C[k] > ref: return k
    return None
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A1 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A1_pullback_fundo"], key=lambda x: x["t"])
DEFS = ("MB1", "MB2", "MB3", "MB4")
res = {d: [] for d in DEFS}
print(f"{'#':<7}{'dt':16}{'ATR':>4}{'SL':>7}  " + "".join(f"{d:>15}" for d in DEFS))
for n, f in enumerate(A1, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    lo0, hi0 = max(0, j-LOWBACK), min(N, j+LOWFWD+1); al = min(range(lo0, hi0), key=lambda k: L[k])
    low = L[al]; atr = ATR[al] or 5.0; sl = round(low-0.1*atr, 2); cells = []
    for d in DEFS:
        ei = fire(al, d)
        if ei is None: res[d].append(None); cells.append("no-trig"); continue
        ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: res[d].append(("SKIP", None, r)); cells.append("tinyR"); continue
        o, b = outc(ei, sl, ent+3*r); res[d].append((o, ei-al, r)); cells.append(f"{o[:4]} R{r:.0f}+{ei-al}")
    print(f"A1_{n:02d}  {ds(t0):16}{atr:>4.0f}{sl:>7.0f}  " + "".join(f"{c:>15}" for c in cells))
print(f"\n{'DEF':<6}{'W':>3}{'L':>3}{'OPEN':>5}{'notrig':>7}{'medBars':>8}  01?      03?")
for d in DEFS:
    v = res[d]; w = sum(1 for x in v if x and x[0] == "WIN"); l = sum(1 for x in v if x and x[0] == "LOSS")
    op = sum(1 for x in v if x and x[0] == "OPEN"); nt = sum(1 for x in v if x is None)
    b2 = [x[1] for x in v if x and x[0] == "WIN" and x[1] is not None]
    r01 = v[0][0] if v[0] else "no-trig"; r03 = v[2][0] if v[2] else "no-trig"
    print(f"{d:<6}{w:>3}{l:>3}{op:>5}{nt:>7}{str(statistics.median(b2) if b2 else '-'):>8}  {r01:<8}{r03}")
