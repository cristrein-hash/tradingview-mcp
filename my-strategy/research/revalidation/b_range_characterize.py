#!/usr/bin/env python3
"""CARACTERIZAÇÃO RAW dos 15 fundos B_range (estudo de caso, Cris 2026-07-15) — para fundamentar
EMPIRICAMENTE a pergunta accum-vs-distribuição. Para cada B: geometria do range (high/low em lookback),
posição do fundo na banda, tendência que ENTRA no range, e o DESFECHO (hindsight, só p/ ENTENDER a
natureza — NÃO é feature do engine): rompeu o topo (markup=acum) ou o fundo (markdown=distrib)?
RAW 15M direto do HD. Sem lookahead-claim: o desfecho é explicitamente retrospetivo p/ rotular natureza."""
import gzip, json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLK = ["XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz", "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz", "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz"]
WB, WL, HF = 480, 1440, 480   # lookback curto(5d), contexto longo(15d), forward(5d)
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
bars = {}
for blk in BLK:
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
T = sorted(bars); H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]; N = len(T)
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])

print(f"{'#':>3} {'data':10} {'preço':>8} {'range[lo-hi]':>17} {'pos%':>5} {'entra(15d%)':>11} {'leg':>13} "
      f"{'fwd:1ºbreak':>11} {'net5d%':>7} {'natureza(hindsight)':>20}")
rows = []
for n, f in enumerate(B, 1):
    j = bisect.bisect_right(T, int(f["t"]))-1
    lo0 = max(0, j-WB); rlo, rhi = min(L[lo0:j+1]), max(H[lo0:j+1])
    pos = 100*(C[j]-rlo)/max(1e-9, rhi-rlo)
    l15 = max(0, j-WL); trend15 = 100*(C[j]-C[l15])/C[l15]
    # forward hindsight: 1º rompimento do topo(rhi) ou do fundo(rlo) do range prévio
    hi_thr, lo_thr = rhi*1.003, rlo*0.997; first = "—"; netp = None
    for m in range(j+1, min(N, j+HF+1)):
        if H[m] >= hi_thr: first = "UP(topo)"; break
        if L[m] <= lo_thr: first = "DOWN(fundo)"; break
    end = min(N-1, j+HF); netp = 100*(C[end]-C[j])/C[j]
    nat = "ACUM(markup)" if first.startswith("UP") else ("DISTRIB(markdown)" if first.startswith("DOWN") else "indef/contido")
    rows.append((n, first, netp, trend15))
    print(f"{n:>3} {ds(f['t']):10} {f['price']:>8.1f} {rlo:>7.0f}-{rhi:<7.0f} {pos:>4.0f}% {trend15:>+10.1f}% "
          f"{str(f.get('leg')):>13} {first:>11} {netp:>+6.1f}% {nat:>20}")

up = sum(1 for r in rows if r[1].startswith("UP")); dn = sum(1 for r in rows if r[1].startswith("DOWN"))
print(f"\nRESUMO: 1º-break UP(acum) {up}/15 · DOWN(distrib) {dn}/15 · net5d>0: {sum(1 for r in rows if r[2]>0)}/15")
print(f"  cluster 2025 (B#1-12): 1º-break UP {sum(1 for r in rows[:12] if r[1].startswith('UP'))}/12 · net5d>0 {sum(1 for r in rows[:12] if r[2]>0)}/12")
print(f"  cluster 2026-02 (B#13-15): 1º-break UP {sum(1 for r in rows[12:] if r[1].startswith('UP'))}/3 · net5d>0 {sum(1 for r in rows[12:] if r[2]>0)}/3")
