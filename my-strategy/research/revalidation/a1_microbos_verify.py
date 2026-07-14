#!/usr/bin/env python3
"""VERIFICAÇÃO PRÓPRIA do gatilho MICRO-BOS vs RECLAIM-EMA21 (A1, ordem Cris 2026-07-14).
Corrige o que o engine apanhou: (1) ÂNCORA DE LOW PRINCIPIADA — o ±4 barras era apertado e apanhava
low local errado (fundo_10: ±4 dava 4202, real ~4186); aqui o low = MENOR low do pullback numa janela
robusta em torno da marca. (2) MICRO-BOS PINADO — testo 2 defs p/ resolver o candle-de-low largo
(que disparava a +98b): MB1 = fecho > high do candle do low; MB2 = fecho > high da barra ANTERIOR ao
low (mais cedo/robusto a candle largo). (3) SL-FIRST honesto barra-a-barra (perde se a mecha toca o
SL antes do alvo) + painel completo + R/ATR (flag R-apertado otimista) + NULL de timing (entrada
aleatória na reação). SL=low−0.1ATR, alvo=entry+3R. RAW 15M direto do HD. Só medição; sem lookahead."""
import gzip, json, bisect, random, datetime as dt, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
LOWBACK, LOWFWD, TRIG_WIN, HORIZON = 16, 8, 48, 480
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
random.seed(20260714)

# --- série 15M (ohlcv RAW) + EMA21 + ATR14 ---
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
                else:  # FUNDIR capturas da mesma barra: max high, min low, último close (barra completa)
                    bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
T = sorted(bars); O=[bars[t][0] for t in T]; H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]
N = len(T); EMA=[None]*N; ATR=[None]*N; ema=None; kE=2/22; trs=[]
for i in range(N):
    ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i]=ema
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None

def outcome(ei, sl, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if L[m] <= sl: return "LOSS", m-ei
        if H[m] >= tgt: return "WIN", m-ei
    return "OPEN", None

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A1 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A1_pullback_fundo"], key=lambda x: x["t"])

def trig_microbos(al, ref_high):
    """1º bar verde (c>o) após o low com close > ref_high."""
    for k in range(al+1, min(N, al+TRIG_WIN+1)):
        if C[k] > O[k] and C[k] > ref_high: return k
    return None
def trig_reclaim(al):
    for k in range(al+1, min(N, al+TRIG_WIN+1)):
        if EMA[k] is not None and C[k] > EMA[k] and C[k] > C[k-1]: return k
    return None

rows = []
for n, f in enumerate(A1, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    if j < 0: continue
    lo0, hi0 = max(0, j-LOWBACK), min(N, j+LOWFWD+1)
    al = min(range(lo0, hi0), key=lambda k: L[k])           # âncora = MENOR low do pullback (robusta)
    low = L[al]; atr = ATR[al] or 5.0; sl = round(low-0.1*atr, 2)
    row = {"id": f"A1_{n:02d}", "dt": ds(t0), "gt": f["price"], "low": low, "d_gt": round(f["price"]-low, 1),
           "atr": round(atr, 1), "sl": sl, "yr": ds(t0)[:4]}
    # gatilhos
    for tag, ei in (("MB1", trig_microbos(al, H[al])),
                    ("MB2", trig_microbos(al, H[al-1] if al > 0 else H[al])),
                    ("RCL", trig_reclaim(al))):
        if ei is None: row[tag] = {"o": "NO-TRIG"}; continue
        ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: row[tag] = {"o": "SKIP-tinyR"}; continue
        o, b = outcome(ei, sl, ent+3*r)
        row[tag] = {"ent": round(ent, 1), "lag": ei-al, "R": round(r, 1), "RATR": round(r/atr, 2), "o": o, "b2r": b}
    # NULL: entrada aleatória na reação [al+1, al+TRIG_WIN]
    wins = 0
    for _ in range(500):
        ei = random.randint(al+1, min(N-2, al+TRIG_WIN)); ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: continue
        if outcome(ei, sl, ent+3*r)[0] == "WIN": wins += 1
    row["null_win%"] = round(100*wins/500)
    rows.append(row)

def panel(tag):
    v = [r[tag] for r in rows if isinstance(r[tag], dict) and "o" in r[tag] and r[tag]["o"] in ("WIN", "LOSS", "OPEN")]
    w = sum(1 for x in v if x["o"] == "WIN"); l = sum(1 for x in v if x["o"] == "LOSS"); op = sum(1 for x in v if x["o"] == "OPEN")
    b2r = [x["b2r"] for x in v if x["o"] == "WIN" and x["b2r"]]
    ratr = [x["RATR"] for x in v]
    tight = sum(1 for x in ratr if x < 1.65)
    return w, l, op, len(v), (statistics.median(b2r) if b2r else None), tight

print(f"{'#':<7}{'dt':16}{'gt':>7}{'lowReal':>8}{'Δgt':>5}{'ATR':>5}{'SL':>8}  {'MB1':>16}{'MB2':>16}{'RCL':>16}{'null%':>6}")
for r in rows:
    def cell(t):
        x = r[t]
        return f"{x['o'][:4]} R{x.get('R','-')} +{x.get('lag','-')}" if "o" in x and "ent" in x else x.get("o", "?")
    print(f"{r['id']:<7}{r['dt']:16}{r['gt']:>7.0f}{r['low']:>8.0f}{r['d_gt']:>5}{r['atr']:>5.0f}{r['sl']:>8.0f}  "
          f"{cell('MB1'):>16}{cell('MB2'):>16}{cell('RCL'):>16}{r['null_win%']:>5}%")
print(f"\n{'PAINEL':<8}{'W':>3}{'L':>3}{'OPEN':>5}{'N':>3}  med_bars_to_3R  tight_R(<1.65ATR)")
for tag in ("MB1", "MB2", "RCL"):
    w, l, op, nn, med, tight = panel(tag)
    print(f"  {tag:<6}{w:>3}{l:>3}{op:>5}{nn:>3}       {str(med):>6}          {tight}/{nn}")
nm = statistics.mean([r["null_win%"] for r in rows]); nq = sorted([r["null_win%"] for r in rows])[int(0.95*len(rows))]
print(f"\nNULL (entrada aleatória na reação): win% médio {nm:.0f} · q95 {nq}")
print("Δgt = gt_price − low_real (fonte); SL usa low_real robusto. b2r=barras até 3R. tight_R = wins otimistas (colam ao SL, 15M não resolve intrabar).")
