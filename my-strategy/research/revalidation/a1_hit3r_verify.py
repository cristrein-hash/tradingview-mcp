#!/usr/bin/env python3
"""VERIFICAÇÃO FUNDACIONAL (ordem Cris 2026-07-14): (1) resolver a ambiguidade do 'low' de fonte
(GT price vs low real do candle 15M) e (2) VERIFICAR hit-3R BARRA-A-BARRA no RAW (trocar 'plausível'
por verificado). Testa DUAS entradas de referência para verificar EMPIRICAMENTE o seletor de regime
do engine (V-agudo=colado ao low vs grind=reclaim EMA21). SL=low−0,1ATR, target=entry+3R, first-touch
forward (horizonte 480b=5d). RAW 15M direto do HD. Só medição, sem lookahead na decisão de entrada."""
import gzip, json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
WIN_LOW, RECLAIM_WIN, HORIZON = 4, 48, 480
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

# --- série 15M (ohlcv direto do RAW) + EMA21 + ATR14 ---
bars = {}
for blk in BLOCKS:
    with gzip.open(RAW / blk, "rt") as fh:
        for l in fh:
            i = l.find('"ohlcv":')
            if i < 0: continue
            s = l.find('[', i); e = l.find(']', s)
            if s < 0 or e < 0: continue
            try: arr = json.loads(l[s:e+1])
            except Exception: continue
            for b in arr:
                t = b.get("time")
                if t is not None and t not in bars:
                    bars[t] = (b.get("open"), b.get("high"), b.get("low"), b.get("close"))
T = sorted(bars); O = [bars[t][0] for t in T]; H = [bars[t][1] for t in T]; L = [bars[t][2] for t in T]; C = [bars[t][3] for t in T]
N = len(T); EMA = [None]*N; ATR = [None]*N; ema = None; kE = 2/22; trs = []
for i in range(N):
    ema = C[i] if ema is None else C[i]*kE + ema*(1-kE); EMA[i] = ema
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None

def verify(entry_i, sl, tgt):
    """first-touch forward barra-a-barra: WIN se HI>=tgt antes de LO<=SL; LOSS se SL antes; OPEN se nenhum."""
    for m in range(entry_i+1, min(N, entry_i+HORIZON+1)):
        if L[m] <= sl: return "LOSS", m
        if H[m] >= tgt: return "WIN", m
    return "OPEN", None

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A1 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A1_pullback_fundo"], key=lambda x: x["t"])
print(f"{'#':<3}{'data':16}{'GTprice':>8}{'lowReal':>8}{'Δlow':>5}{'ATR':>5}{'SL':>8} | "
      f"{'ENTRY-CEDO(colado)':^26} | {'ENTRY-RECLAIM(EMA21)':^28}")
we = wr = 0
for n, f in enumerate(A1, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    if j < 0: continue
    lo0, hi0 = max(0, j-WIN_LOW), min(N, j+WIN_LOW+1)
    k_low = min(range(lo0, hi0), key=lambda k: L[k]); low_real = L[k_low]   # low real perto do fundo
    atr = ATR[j] or 5.0; sl = round(low_real - 0.1*atr, 2)
    dlow = round(f["price"] - low_real, 1)
    # ENTRY-CEDO: close da barra do low real (colado)
    e1 = k_low; ent1 = C[e1]; r1 = ent1 - sl; tg1 = ent1 + 3*r1
    o1, m1 = verify(e1, sl, tg1) if r1 > 0.05*atr else ("SKIP", None)
    # ENTRY-RECLAIM: 1º close>EMA21 & close>close-1 após o low
    e2 = None
    for k in range(k_low+1, min(N, k_low+RECLAIM_WIN+1)):
        if EMA[k] is not None and C[k] > EMA[k] and C[k] > C[k-1]: e2 = k; break
    if e2 is not None:
        ent2 = C[e2]; r2 = ent2 - sl; tg2 = ent2 + 3*r2
        o2, m2 = verify(e2, sl, tg2) if r2 > 0.05*atr else ("SKIP", None)
    else: o2, ent2, r2, m2 = "NO-RECLAIM", None, None, None
    we += o1 == "WIN"; wr += o2 == "WIN"
    b2r1 = (m1-e1) if m1 else "-"; b2r2 = (m2-e2) if (m2 and e2) else "-"
    s1 = f"ent{ent1:.0f} R{r1:.1f} {o1}({b2r1})"
    s2 = f"ent{ent2:.0f} R{r2:.1f} {o2}({b2r2})" if ent2 else o2
    print(f"{n:<3}{ds(t0):16}{f['price']:>8.0f}{low_real:>8.0f}{dlow:>5}{atr:>5.0f}{sl:>8.0f} | {s1:^26} | {s2:^28}")
print(f"\nVERIFICADO barra-a-barra (N={len(A1)}): ENTRY-CEDO {we} WIN · ENTRY-RECLAIM {wr} WIN")
print("Δlow = GTprice − low_real do candle (ambiguidade de fonte resolvida usando low_real p/ SL)")
