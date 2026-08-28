#!/usr/bin/env python3
"""GT HUMANO — verificação dos 5 ranges rotulados pelo Cris (28/08) contra o RAW 4H/diário.
Para cada período: largura, drift líquido, % de barras dentro da banda, comportamento nas bordas
(sweeps além da banda que voltam). Materializado (regra output-órfão). py3.9 stdlib. SANITY_PROBE n/a:
verificação de GT humano prereg'd."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent

PERIODS = [
    ("R1_range_claro",  "2026-06-20", "2026-08-05"),
    ("R2_range_agosto", "2026-08-07", "2026-08-19"),
    ("R3_distribuicao", "2026-05-06", "2026-05-14"),
    ("R4_acumulacao",   "2025-04-11", "2025-08-29"),
    ("R5_range_24_25",  "2024-09-16", "2025-01-10"),
]

rows = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl") if l.strip()]
rows.sort(key=lambda x: x["t"])
T = [b["t"] for b in rows]; H = [b["h"] for b in rows]; L = [b["l"] for b in rows]; C = [b["c"] for b in rows]
trs = [0] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, len(T))]

# ATR diário REAL: resample 4H→1D (dia UTC), TR diário, média 14 (auditoria: 6×TR4h sobrestima ~2.6×)
days = {}
for i in range(len(T)):
    d = T[i] - (T[i] % 86400)
    if d not in days:
        days[d] = [H[i], L[i], C[i]]
    else:
        days[d][0] = max(days[d][0], H[i]); days[d][1] = min(days[d][1], L[i]); days[d][2] = C[i]
DK = sorted(days)
DTR = [0.0]
for k in range(1, len(DK)):
    h, l, c = days[DK[k]]; pc = days[DK[k - 1]][2]
    DTR.append(max(h - l, abs(h - pc), abs(l - pc)))


def atr_d_real(t):
    import bisect
    k = bisect.bisect_left(DK, t - (t % 86400))
    seg = DTR[max(1, k - 14):k]
    return sum(seg) / len(seg) if seg else 1.0


def ep(s):
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())


out = []
print(f"{'periodo':<18}{'barras':>7}{'dias':>6}{'lo':>8}{'hi':>8}{'larg%':>7}{'largATRd':>9}{'net%larg':>9}{'%dentro':>8}{'sweeps':>7}")
for name, a, b in PERIODS:
    ta, tb = ep(a), ep(b) + 86400
    idx = [i for i, t in enumerate(T) if ta <= t < tb]
    if not idx:
        print(f"{name:<18} SEM BARRAS"); continue
    i0, i1 = idx[0], idx[-1]
    lo, hi = min(L[i0:i1 + 1]), max(H[i0:i1 + 1])
    w = hi - lo
    atr_d = atr_d_real(T[i0])
    net = abs(C[i1] - C[i0])
    # banda "core" = percentis 5-95 dos fechos; % de fechos dentro; sweeps = barras cujo extremo fura
    cs = sorted(C[i0:i1 + 1]); n = len(cs)
    p5, p95 = cs[int(.05 * n)], cs[int(.95 * n)]
    inside = sum(1 for i in idx if p5 <= C[i] <= p95) / n
    sweeps = sum(1 for i in idx if (H[i] > p95 and C[i] < p95) or (L[i] < p5 and C[i] > p5))
    days = (T[i1] - T[i0]) / 86400
    rec = dict(name=name, ini=a, fim=b, barras=n, dias=round(days), lo=round(lo, 1), hi=round(hi, 1),
               larg_pct=round(100 * w / lo, 1), larg_atrd=round(w / atr_d, 1),
               net_frac_larg=round(net / w, 2), fechos_dentro_p5p95=round(inside, 2), sweeps_borda=sweeps)
    out.append(rec)
    print(f"{name:<18}{n:>7}{rec['dias']:>6}{rec['lo']:>8}{rec['hi']:>8}{rec['larg_pct']:>7}{rec['larg_atrd']:>9}{rec['net_frac_larg']:>9}{rec['fechos_dentro_p5p95']:>8}{sweeps:>7}")

(HERE / "gt_human.json").write_text(json.dumps(dict(
    autor="Cris", data="2026-08-28", nota="rotulagem humana; GT canonico para medir detetores de range",
    periodos=out), indent=1))
print("\ngravado gt_human.json (GT canónico humano)")
