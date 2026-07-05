#!/usr/bin/env python3
"""ESTRUTURA→INDICADORES v2 — correção pós-desafio do Cris (2026-07-05).
v1 tinha 3 defeitos que esmagavam as lentes: (1) trios duplicados por permutação de nome inflavam
o ledger e o null max-z familiar; (2) max-stat dominado por grupos N20-30 ruidosos → barra q95
z=2,75 (N63 precisava hit≥62,6% p/ contar) = zero poder para incrementos reais de +10-15pp;
(3) pergunta errada: dentro de N97 não há headroom — a hipótese operacional do Cris é SUBSTITUIÇÃO
(estrutura mais fraca + indicador ≈ qualidade do ≥5 com N maior).

v2:
  CONTEXTOS: cascade>=3 e cascade>=4 (headroom real) + >=5 (referência).
  LEDGER: mesmas 12 lentes declaradas; singles + pares + trios (expansão: pares com hit>=base+8pp
  & N>=40), DEDUP por frozenset, grupos N>=40 apenas.
  INFERÊNCIA: P por grupo via bootstrap de subconjuntos do contexto (5000×) + Benjamini-Hochberg
  FDR q=0,10 no ledger dedupado (controlo de multiplicidade COM poder, sem max-stat).
  PODER: coluna com hit mínimo detectável a z=2 por N do grupo (transparência).
  VEREDITO-CHAVE: alguma combinação em >=3/>=4 atinge hit>=45% com N>97? (substituição confirmada
  = indicadores expandem frequência mantendo qualidade do degrau estrutural)."""
import json, glob, bisect, random, math
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

def choch_up_recent(cj):
    hi = bisect.bisect_right(ET, cj)
    return int(any(events[i]["tok"] == "CHoCH+" and cj - events[i]["t"] <= 8 * 900 for i in range(hi)
                   if events[i]["t"] >= cj - 192 * 900))

for u in U:
    u["_casc"] = cascade(u["cj_t"]); u["_chup"] = choch_up_recent(u["cj_t"])

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

LENSES = {
    "L01_oversold15": lambda u: fv(u, "rsi_low", 99) <= 30,
    "L02_legbase": lambda u: fv(u, "legpos60", 9) <= 0.10,
    "L03_below_ema21": lambda u: fv(u, "g_ema21_dist", 9) < 0,
    "L04_deep_pull": lambda u: fv(u, "pullback_depth", 0) >= 0.90,
    "L05_swept": lambda u: fv(u, "g_sweep_depth", 0) >= 1.0,
    "L06_reclaim_forte": lambda u: fv(u, "reclaim_atr", 0) >= 1.5,
    "L07_atr_spike": lambda u: fv(u, "g_atr_spike", 0) >= 1.27,
    "L08_demanda": lambda u: fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5,
    "L09_oversold1h": lambda u: fv(u, "h1_rsi", 99) <= 42,
    "L10_choch_up_rec": lambda u: u["_chup"] == 1,
    "L11_eql_swept": lambda u: True,  # substituída: era ~50% do universo, sem valor discriminante em v1
    "L12_nao_bear": lambda u: u.get("g_v5h") != "BEAR",
}
del LENSES["L11_eql_swept"]
KEYS = list(LENSES)
WEEKS = len({u["g_week"] for u in U})

def hit_net(rows):
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in rows]
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    return sum(hs), sum(nets)

random.seed(21)
RESULTS = {}
for CMIN in (3, 4, 5):
    CTX = [u for u in U if u["cj_t"] in R3 and u["_casc"] >= CMIN]
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in CTX]
    base = sum(H0) / len(H0)
    print("=" * 112)
    print(f"CTX cascade>={CMIN}: N{len(CTX)} · hit base {100*base:.1f}%")
    groups = {}
    for nm in KEYS:
        groups[frozenset([nm])] = [u for u in CTX if LENSES[nm](u)]
    for i in range(len(KEYS)):
        for j in range(i + 1, len(KEYS)):
            fs = frozenset([KEYS[i], KEYS[j]])
            groups[fs] = [u for u in CTX if LENSES[KEYS[i]](u) and LENSES[KEYS[j]](u)]
    groups = {fs: g for fs, g in groups.items() if len(g) >= 40}
    # expansão a trios: pares hit>=base+8pp & N>=40
    for fs in [fs for fs in list(groups) if len(fs) == 2]:
        h, _ = hit_net(groups[fs])
        if h / len(groups[fs]) >= base + 0.08:
            for c in KEYS:
                if c in fs:
                    continue
                fs3 = fs | {c}
                if fs3 in groups:
                    continue
                g3 = [u for u in CTX if all(LENSES[k](u) for k in fs3)]
                if len(g3) >= 40:
                    groups[fs3] = g3
    # P por grupo via bootstrap + FDR
    stats = []
    for fs, g in groups.items():
        h, net = hit_net(g)
        n = len(g); obs = h / n
        ge = 0
        for _ in range(5000):
            if sum(random.sample(H0, n)) / n >= obs:
                ge += 1
        stats.append((fs, n, obs, net, ge / 5000))
    m = len(stats)
    stats.sort(key=lambda x: x[4])
    fdr_sig = set()
    for rank, (fs, n, obs, net, p) in enumerate(stats, 1):
        if p <= 0.10 * rank / m:
            fdr_sig.add(fs)
    print(f"  ledger dedupado: {m} grupos · FDR q=0,10 → {len(fdr_sig)} significativos")
    print(f"  {'grupo':<46} {'N':>4} {'hit%':>6} {'Δpp':>5} {'NET3':>8} {'P':>7} {'min-det@z2':>10}")
    for fs, n, obs, net, p in stats[:12]:
        mind = base + 2 * math.sqrt(base * (1 - base) / n)
        tag = "&".join(sorted(fs))
        mark = "  <<< FDR" if fs in fdr_sig else ""
        print(f"  {tag:<46} {n:>4} {100*obs:>5.1f}% {100*(obs-base):>+5.1f} {net:>+8.1f} {p:>7.4f} {100*mind:>9.1f}%{mark}")
    RESULTS[CMIN] = {"n_ctx": len(CTX), "base": round(base, 3), "ledger": m,
                     "fdr_sig": ["&".join(sorted(fs)) for fs in fdr_sig],
                     "top": [{"g": "&".join(sorted(fs)), "n": n, "hit": round(o, 3),
                              "net3": round(float(net), 1), "p": p} for fs, n, o, net, p in stats[:15]]}
    # veredito substituição
    subs = [(fs, n, o, net) for fs, n, o, net, p in stats if o >= 0.45 and n > 97 and fs in fdr_sig]
    if subs:
        print(f"  >>> SUBSTITUIÇÃO CONFIRMADA (hit>=45% & N>97 & FDR): "
              f"{[('&'.join(sorted(f)), n, round(100*o,1)) for f, n, o, _ in subs]}")
json.dump(RESULTS, open(HERE / "results" / "cascade_context_indicators_v2_20260705.json", "w"), indent=1)
print("OK → results/cascade_context_indicators_v2_20260705.json")
