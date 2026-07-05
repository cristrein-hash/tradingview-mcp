#!/usr/bin/env python3
"""PAINEL COMPLETO — CASCATA SMC >=5 standalone (2026-07-05).
Achado: estrutura sozinha (>=5 quebras bear consecutivas antes do fundo local confirmado) carrega;
indicadores por cima não acrescentam (pré-registo: P_fam≈1,0 em 165 grupos). Causalidade dos labels
SMC auditada (2878/2888 quebras visíveis por close em/antes do label t; 0,2% exceções).
Painel canónico + null vs universo (subconjuntos aleatórios N-iguais, 2000×) + por-ano + streak
distribucional simples (bootstrap iid 2000× da sequência de outcomes)."""
import json, glob, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}; EV = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    EV += d["smc_events"]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def close_at(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i]["c"] if i >= 0 else None

seen = set(); events = []
for e in sorted(EV, key=lambda x: x["t"]):
    key = (e["t"], e["text"], round(e["price"], 2))
    if key in seen or e["text"] not in ("BOS", "CHoCH"):
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    events.append({"t": e["t"], "tok": e["text"] + ("+" if c > e["price"] else "-")})
ET = [e["t"] for e in events]

def cascade(cj):
    t0 = cj - 192 * 900
    hi = bisect.bisect_right(ET, cj)
    dirs = [events[i]["tok"] for i in range(hi) if events[i]["t"] >= t0]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    return n

POCKET = [u for u in U if u["cj_t"] in R3 and cascade(u["cj_t"]) >= 5]
POCKET.sort(key=lambda u: u["cj_t"])
nets = [R3[u["cj_t"]]["net3"] for u in POCKET]
hits = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in POCKET]
WEEKS = len({u["g_week"] for u in U})
n = len(POCKET); h = sum(hits); s = sum(nets); w = sum(1 for x in nets if x > 0)
eq = pk = dd = 0.0; mL = cl = 0
for x in nets:
    eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    if x <= 0: cl += 1; mL = max(mL, cl)
    else: cl = 0
yr = {y: {"n": sum(1 for u in POCKET if u["yr"] == y),
          "net": round(sum(nets[i] for i, u in enumerate(POCKET) if u["yr"] == y), 1),
          "hit": round(100 * sum(hits[i] for i, u in enumerate(POCKET) if u["yr"] == y) /
                       max(1, sum(1 for u in POCKET if u["yr"] == y)), 1)} for y in (2024, 2025, 2026)}
print(f"CASCATA>=5 STANDALONE: N{n} · hit-3R {100*h/n:.1f}% · WR {100*w/n:.1f}% · sumR {s:+.1f} · "
      f"avgR {s/n:+.3f} · DD {dd:.1f} · r/DD {s/abs(dd):.1f} · streak-{mL} · {n/WEEKS:.2f}/sem")
print(f"  por ano: {yr}")
reg = {}
for i, u in enumerate(POCKET):
    reg.setdefault(u.get("g_v5h"), []).append(i)
print("  por regime:", {k: f"N{len(v)} hit {100*sum(hits[i] for i in v)/len(v):.0f}% net {sum(nets[i] for i in v):+.1f}"
                        for k, v in reg.items()})
# null vs universo
random.seed(13)
ALLH = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in U if u["cj_t"] in R3]
ALLN = [R3[u["cj_t"]]["net3"] for u in U if u["cj_t"] in R3]
geh = gen = 0
for _ in range(2000):
    idx = random.sample(range(len(ALLH)), n)
    if sum(ALLH[i] for i in idx) >= h: geh += 1
    if sum(ALLN[i] for i in idx) >= s: gen += 1
print(f"  null vs universo (N-igual, 2000×): P(hit) {geh/2000:.4f} · P(NET) {gen/2000:.4f}")
# streak distribucional iid
random.seed(14); q = []
for _ in range(2000):
    sq = random.choices(nets, k=n); c2 = m2 = 0
    for x in sq:
        c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
    q.append(m2)
q.sort()
print(f"  streak distribucional (iid, WR {100*w/n:.0f}%): obs {mL} · q50 {q[1000]} · q95 {q[int(0.95*2000)]}")
json.dump({"n": n, "hit3r": round(h / n, 3), "sumR": round(s, 1), "dd": round(dd, 1), "streak_obs": mL,
           "streak_q95": q[int(0.95 * 2000)], "per_year": yr,
           "p_hit_vs_universe": geh / 2000, "p_net_vs_universe": gen / 2000,
           "cj_ts": [u["cj_t"] for u in POCKET]},
          open(HERE / "results" / "cascade5_standalone_panel_20260705.json", "w"), indent=1)
print("OK → results/cascade5_standalone_panel_20260705.json")
