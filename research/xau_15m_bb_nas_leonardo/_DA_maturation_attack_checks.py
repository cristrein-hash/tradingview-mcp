#!/usr/bin/env python3
"""DA ADVERSARIAL — checks numéricos p/ atacar analysis_base4_maturation_read.py (2026-07-03).
Read-only sobre base4_maturation_features.json. Calcula: colinearidade lateness~risk_atr,
confound room_above~pos20/lateness, N/z por bucket, sensibilidade a cauda (ex-top3),
poder binomial do slice Cris-BEAR, estrutura real dos episódios multi-entrada.
"""
import json, math, statistics as st
import datetime as dt
from pathlib import Path
from math import comb

HERE = Path(__file__).resolve().parent
T = json.load(open(HERE / "base4_maturation_features.json"))
BASE_WR = 0.476

def corr(a, b):
    xs = [(t[a], t[b]) for t in T if t[a] is not None and t[b] is not None]
    ma = st.mean(x for x, _ in xs); mb = st.mean(y for _, y in xs)
    num = sum((x - ma) * (y - mb) for x, y in xs)
    return num / math.sqrt(sum((x - ma) ** 2 for x, _ in xs) * sum((y - mb) ** 2 for _, y in xs))

print("corr lateness~risk_atr:", round(corr("lateness", "risk_atr"), 4), "(identidade: risk_atr = lateness + 0.1)")
print("corr room_above~pos20:", round(corr("room_above", "pos20"), 3),
      " room~lateness:", round(corr("room_above", "lateness"), 3),
      " room~ext_ema:", round(corr("room_above", "ext_ema"), 3))

for name, key, edges in [("lateness", "lateness", [(0, .8), (.8, 1.2), (1.2, 1.8), (1.8, 99)]),
                         ("room", "room_above", [(0, .5), (.5, 1.5), (1.5, 3), (3, 99)])]:
    for lo, hi in edges:
        b = [t for t in T if lo <= t[key] < hi]
        w = sum(t["win"] for t in b); n = len(b)
        se = math.sqrt(BASE_WR * (1 - BASE_WR) / n)
        yrs = {y: sum(1 for t in b if t["yr"] == y) for y in (2024, 2025, 2026)}
        print(f"{name}[{lo},{hi}): N{n} WR{100*w/n:.1f}% z={(w/n-BASE_WR)/se:+.2f} yrs{yrs} "
              f"sumR{sum(t['R'] for t in b):+.1f} top2R{[round(x,1) for x in sorted((t['R'] for t in b), reverse=True)[:2]]}")

for lo, hi in [(0, .5), (.5, 1.5), (1.5, 3), (3, 99)]:
    b = [t for t in T if lo <= t["room_above"] < hi]
    print(f"room[{lo},{hi}): med pos20={st.median(t['pos20'] for t in b):.2f} "
          f"med lateness={st.median(t['lateness'] for t in b):.2f} med rsi={st.median(t['rsi'] for t in b):.1f}")

buck = {}
for t in T: buck.setdefault(t["hour"] // 4, []).append(t)
for h in sorted(buck):
    b = buck[h]; n = len(b); w = sum(t["win"] for t in b)
    se = math.sqrt(BASE_WR * (1 - BASE_WR) / n)
    R = sorted((t["R"] for t in b), reverse=True)
    yrs = {y: sum(1 for t in b if t["yr"] == y) for y in (2024, 2025, 2026)}
    print(f"h{h*4:02d}-{h*4+3:02d}: N{n} WR{100*w/n:.1f}% z={(w/n-BASE_WR)/se:+.2f} avgR{sum(R)/n:+.3f} "
          f"avgR_ex-top3{(sum(R)-sum(R[:3]))/(n-3):+.3f} yrs{yrs}")

cut = int(dt.datetime(2026, 1, 29, tzinfo=dt.timezone.utc).timestamp())
S = [t for t in T if t["t"] >= cut]
R = sorted((t["R"] for t in S), reverse=True)
w = sum(t["win"] for t in S); n = len(S)
pv = sum(comb(n, k) * BASE_WR ** k * (1 - BASE_WR) ** (n - k) for k in range(w, n + 1))
print(f"CRIS slice N{n} wins{w} sumR{sum(R):+.1f} top3{[round(x,1) for x in R[:3]]} "
      f"sumR ex-top3{sum(R[3:]):+.1f} | binomial one-sided P(W>={w}|p={BASE_WR})={pv:.3f}")

T2 = sorted(T, key=lambda t: t["t"])
eps = []; cur = [T2[0]]
for a, b in zip(T2, T2[1:]):
    if b["t"] - a["t"] <= 8 * 900: cur.append(b)
    else: eps.append(cur); cur = [b]
eps.append(cur)
multi = [e for e in eps if len(e) > 1]
sec = [t for e in multi for t in e[1:]]
print(f"episodes{len(eps)} multi{len(multi)} 2nd+ N{len(sec)} WR2nd {100*sum(t['win'] for t in sec)/len(sec):.1f}% "
      f"| WR da 1ª entrada DOS multi: {100*sum(1 for e in multi if e[0]['win'])/len(multi):.1f}%  <-- estrutura fail-then-retry")

print("med risk_atr W", round(st.median(t["risk_atr"] for t in T if t["win"]), 2),
      "L", round(st.median(t["risk_atr"] for t in T if not t["win"]), 2))
L = [t for t in T if not t["win"]]; stp = [t for t in L if t["stopped"]]
print("losers", len(L), "stopped", len(stp), "rec1", sum(1 for t in stp if t["rec1"]),
      "rec2", sum(1 for t in stp if t["rec2"]), "(SEM null baseline de bounce ambiente — ver relatório DA)")
