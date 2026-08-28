#!/usr/bin/env python3
"""EDGE REAL POR RULE DO E1 (ordem Cris 28/08): cada candidato E1 resolvido SL-first 3R contra bars_15m.
Diz, por rule E por direção, N/WR/sumR/avgR — qual gera sinal positivo e qual é ruído. Materializado.
NOTA: candidato E1 = pré-reader (antes do gate/juízo). Mede a matéria-prima, não o que foi enviado.
py3 stdlib."""
import json
import datetime as dt
from collections import defaultdict
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp"); LX = dt.timezone(dt.timedelta(hours=1))


def jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except Exception:
        return []


def ts(x):
    if isinstance(x, (int, float)):
        return x
    try:
        return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


bars = jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl")
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]


def resolve(t0, e, sl, tgt, lng):
    if not (t0 and e and sl):
        return None
    i0 = next((i for i, t in enumerate(T) if t > t0), None)
    if i0 is None:
        return None
    risk = (e - sl) if lng else (sl - e)
    if risk <= 0:
        return None
    tgt = tgt or (e + 3 * risk if lng else e - 3 * risk)
    for i in range(i0, len(T)):
        if lng:
            if L[i] <= sl: return -1.0
            if H[i] >= tgt: return 3.0
        else:
            if H[i] >= sl: return -1.0
            if L[i] <= tgt: return 3.0
    return 0.0


cands = jl(REPO / "alert-bridge/logs/e1_candidates.jsonl")
# dedup: mesmo (rule,dir,bar_time) conta 1× (E1 repete o mesmo candidato em ciclos consecutivos)
seen = set(); agg = defaultdict(list)
t0min = T[0] if T else 0
for c in cands:
    t = ts(c.get("t") or c.get("ts") or c.get("bar_time"))
    if t is None or t < t0min:               # só o que a janela do store 15m cobre
        continue
    rule = c.get("rule"); dirn = (c.get("direction") or "").upper()
    key = (rule, dirn, int(t // 900))
    if key in seen:
        continue
    seen.add(key)
    R = resolve(t, c.get("entry"), c.get("sl"), c.get("target"), dirn == "LONG")
    if R is not None:
        agg[(rule, dirn)].append(R)

print(f"EDGE POR RULE DO E1 (candidatos dedup na janela store ~{len(T)} barras 15m; SL-first 3R)")
print(f"{'rule':<18}{'dir':<6}{'N':>5}{'WR':>5}{'sumR':>8}{'avgR':>7}")
rows = []
for (rule, dirn), rs in sorted(agg.items(), key=lambda x: -sum(x[1])):
    n = len(rs); w = sum(1 for r in rs if r > 0); s = sum(rs)
    rows.append(dict(rule=rule, dir=dirn, N=n, WR=round(100 * w / n) if n else None,
                     sumR=round(s, 1), avgR=round(s / n, 2) if n else None))
    print(f"{rule:<18}{dirn:<6}{n:>5}{(round(100*w/n) if n else 0):>5}{s:>8.1f}{(s/n if n else 0):>7.2f}")
# só LONG (o que fica live)
print("\n— só LONG (direção viva) —")
for r in [x for x in rows if x["dir"] == "LONG"]:
    print(f"  {r['rule']:<18} N{r['N']:>4} WR{r['WR']} avgR{r['avgR']:+.2f} sumR{r['sumR']:+.1f}")
json.dump(rows, open(REPO / "my-strategy/research/revalidation/e1_rule_edge_20260828.json", "w"), indent=1)
