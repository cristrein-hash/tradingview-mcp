#!/usr/bin/env python3
"""CAMADA A — REGIME MACRO 4H causal, derivado do RAW 15M (resample), fonte primitives/*.json (extração RAW exclusiva).
Resample contínuo 15M→4H (bucket UTC = floor(t/14400)) sobre os 8 blocos; estrutura de swing 4H (HH/HL=BULL,
LH/LL=BEAR via fractal k=2) ∧ posição vs EMA50(4H). macro ∈ {BULL,BEAR,NEUTRAL}. Causal: regime de cada barra 4H
usa só barras 4H fechadas até ela; a barra 15M consome o último 4H FECHADO (sem look-ahead). Saída macro_regime_4h.json.
Bull/Bear do pane NÃO está no RAW → derivado de preço. Verified 2026-06-26."""
import json
from pathlib import Path
HERE = Path(__file__).parent
PRIM = sorted((HERE / "primitives").glob("*.primitives.json"))
BUCKET = 14400  # 4H em segundos
K = 2           # fractal swing

# ---- série 15M contínua (RAW-derivada) ----
# dedup nos seams dos blocos (overlap ~2 dias): last-writer-wins INTENCIONAL — verificado imaterial (0/3189 labels
# mudam vs first-writer; conflitos são ruído sub-barra que nunca vira bucket 4H; DA 2026-06-26 _DA_dedup_impact.py).
bars = {}
for p in PRIM:
    for b in json.loads(p.read_text())["series"]:
        bars[b["t"]] = b
ts = sorted(bars)
# ---- resample → 4H ----
buck = {}
for t in ts:
    b = bars[t]; k = t // BUCKET
    if k not in buck: buck[k] = {"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "t_start": k * BUCKET}
    else:
        z = buck[k]; z["h"] = max(z["h"], b["h"]); z["l"] = min(z["l"], b["l"]); z["c"] = b["c"]
    buck[k]["t_end"] = (k + 1) * BUCKET
H4 = [buck[k] for k in sorted(buck)]
# ---- EMA50(4H) + swing structure + macro (causal por barra 4H) ----
ema = None; kE = 2 / 51
Hh = [x["h"] for x in H4]; Ll = [x["l"] for x in H4]
for i, x in enumerate(H4):
    ema = x["c"] if ema is None else x["c"] * kE + ema * (1 - kE); x["ema50"] = ema
    # swings confirmados até i (pivô j precisa j+K<=i)
    sh, sl = [], []
    for j in range(K, i - K + 1):
        if Hh[j] == max(Hh[j - K:j + K + 1]): sh.append(Hh[j])
        if Ll[j] == min(Ll[j - K:j + K + 1]): sl.append(Ll[j])
    sd = 0
    if len(sh) >= 2 and len(sl) >= 2:
        if sh[-1] > sh[-2] and sl[-1] > sl[-2]: sd = 1
        elif sh[-1] < sh[-2] and sl[-1] < sl[-2]: sd = -1
    ep = 1 if x["c"] >= ema else -1
    x["swing_dir"] = sd; x["ema_pos"] = ep
    x["macro"] = "BULL" if (sd > 0 and ep > 0) else ("BEAR" if (sd < 0 and ep < 0) else "NEUTRAL")
out = {"n_bars_15m": len(ts), "n_bars_4h": len(H4), "t_start": ts[0], "t_end": ts[-1],
       "bars_4h": [{"t_start": x["t_start"], "t_end": x["t_end"], "c": round(x["c"], 2), "ema50": round(x["ema50"], 2),
                     "swing_dir": x["swing_dir"], "ema_pos": x["ema_pos"], "macro": x["macro"]} for x in H4]}
(HERE / "macro_regime_4h.json").write_text(json.dumps(out, default=str))
# ---- sumário ----
from collections import Counter
import datetime as dt
c = Counter(x["macro"] for x in H4)
# % de barras 15M sob cada macro (último 4H fechado)
endt = [x["t_end"] for x in H4]
import bisect
m15 = Counter()
for t in ts:
    k = bisect.bisect_right(endt, t) - 1
    m15[H4[k]["macro"] if k >= 0 else "WARMUP"] += 1
print(f"4H bars={len(H4)} | 15M bars={len(ts)} | {dt.datetime.utcfromtimestamp(ts[0]):%Y-%m-%d}→{dt.datetime.utcfromtimestamp(ts[-1]):%Y-%m-%d}")
print(f"macro por barra 4H: {dict(c)}")
print(f"macro por barra 15M (último 4H fechado): {{'BULL':{m15['BULL']}, 'BEAR':{m15['BEAR']}, 'NEUTRAL':{m15['NEUTRAL']}, 'WARMUP':{m15['WARMUP']}}}")
pct = lambda k: 100 * m15[k] / len(ts)
print(f"  → BULL {pct('BULL'):.0f}% | BEAR {pct('BEAR'):.0f}% | NEUTRAL {pct('NEUTRAL'):.0f}%")
# spot-check período dos prints (Dez/2025–Jan/2026 = BULL forte esperado)
def macro_at(iso):
    t = int(dt.datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    k = bisect.bisect_right(endt, t) - 1; return H4[k]["macro"] if k >= 0 else "WARMUP"
print("spot-check:", {d: macro_at(d) for d in ["2025-12-15", "2026-01-12", "2025-09-15", "2025-10-20"]})
