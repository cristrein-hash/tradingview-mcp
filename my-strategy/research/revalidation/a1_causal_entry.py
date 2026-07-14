#!/usr/bin/env python3
"""ENTRY CAUSAL CANÓNICO (fix lookahead, Cris 2026-07-15) — módulo único usado pela verificação E pelo
coletor forward. Corrige o +8-forward da âncora do SL: a âncora é agora um SWING-LOW FRACTAL CONFIRMADO
(m=3 barras de cada lado, tudo <= barra de decisão) → ZERO lookahead. MB3 dispara após a confirmação.
SL=swing_low−0.1ATR, alvo=entry+3R, outcome SL-first. RAW 15M direto do HD.
__main__ = re-verifica A1/A2 e compara com research (que tinha o +8)."""
import gzip, json, bisect, datetime as dt, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
M_FRAC, TRIG_WIN, LOWBACK, HORIZON = 3, 48, 16, 480

def load_series(blocks):
    bars = {}
    for blk in blocks:
        p = RAW/blk if not str(blk).startswith("/") else Path(blk)
        with gzip.open(p, "rt") as fh:
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
    return dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)

def _is_swinglow(L, p, m):
    if p-m < 0 or p+m >= len(L): return False
    return L[p] == min(L[p-m:p+m+1]) and L[p] < min(L[p-m:p])

def causal_entry(S, j, kind="MB3"):
    """CAUSAL: âncora = swing-low fractal confirmado (confirma em p+m, <= barra k). MB3/reclaim dispara
    após confirmação. Devolve dict(ei, ent, sl, R, anchor_bar, o, bars) ou None. Sem lookahead."""
    L, O, H, C, EMA, ATR, N = S["L"], S["O"], S["H"], S["C"], S["EMA"], S["ATR"], S["N"]
    anchor_low = float("inf"); anchor_bar = None
    for p in range(max(M_FRAC, j-LOWBACK), j-M_FRAC+1):        # swing-lows já confirmados por j
        if _is_swinglow(L, p, M_FRAC) and L[p] < anchor_low: anchor_low, anchor_bar = L[p], p
    for k in range(j, min(N, j+TRIG_WIN)):
        p = k-M_FRAC                                            # swing-low confirma em k (fractal <= k)
        if p >= max(M_FRAC, j-LOWBACK) and _is_swinglow(L, p, M_FRAC) and L[p] < anchor_low:
            anchor_low, anchor_bar = L[p], p
        if anchor_bar is None or k <= anchor_bar: continue
        trig = (C[k] > O[k] and C[k] > H[k-1]) if kind == "MB3" else (EMA[k] is not None and C[k] > EMA[k] and C[k] > C[k-1])
        if not trig: continue
        atr = ATR[anchor_bar] or 5.0; sl = round(anchor_low-0.1*atr, 2); ent = C[k]; r = ent-sl
        if r <= 0.05*atr: continue
        tgt = ent+3*r; o, bb = "OPEN", None
        for mrk in range(k+1, min(N, k+HORIZON+1)):
            if L[mrk] <= sl: o, bb = "LOSS", mrk-k; break
            if H[mrk] >= tgt: o, bb = "WIN", mrk-k; break
        return dict(ei=k, ent=round(ent, 2), sl=sl, R=round(r, 2), RATR=round(r/atr, 2),
                    anchor_bar=anchor_bar, lag=k-anchor_bar, o=o, bars=bb, tgt=round(tgt, 2))
    return None

if __name__ == "__main__":
    ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
    BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
           "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
    S = load_series(BLK); T = S["T"]
    GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
    for layer in ("A1_pullback_fundo", "A2_pullback_raso"):
        F = sorted([f for f in GT["fundos"] if f.get("subclasse") == layer], key=lambda x: x["t"])
        print(f"\n{'='*72}\n{layer} (N={len(F)}) — ENTRY CAUSAL (swing-low fractal, SEM +8 lookahead)\n{'='*72}")
        wm = wr = tight = 0; b2 = []
        for n, f in enumerate(F, 1):
            j = bisect.bisect_right(T, int(f["t"]))-1
            mb = causal_entry(S, j, "MB3"); rc = causal_entry(S, j, "RCL")
            if mb: wm += mb["o"] == "WIN"; tight += mb["RATR"] < 1.65
            if mb and mb["o"] == "WIN" and mb["bars"]: b2.append(mb["bars"])
            if rc: wr += rc["o"] == "WIN"
            sm = f"MB3 {mb['o']} R{mb['R']}({mb['RATR']}A)+{mb['lag']}" if mb else "MB3 —"
            sr = f"RCL {rc['o']}" if rc else "RCL —"
            print(f"  {n:2d} {ds(int(f['t'])):16} {sm:<28} {sr}")
        print(f"  PAINEL CAUSAL: MB3 {wm}/{len(F)} WIN · RCL {wr}/{len(F)} WIN · tight-R {tight}/{len(F)} · med barras {statistics.median(b2) if b2 else '-'}")
