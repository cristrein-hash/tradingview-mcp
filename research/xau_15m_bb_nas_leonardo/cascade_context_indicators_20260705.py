#!/usr/bin/env python3
"""ESTRUTURA→INDICADORES — pré-registo (2026-07-05, GO do Cris: "após estrutura ser encontrada,
indicadores individualmente ou em combos de 2 e 3 podem ajudar muito").

CONTEXTO ESTRUTURAL (achado da gramática SMC, pré-fixado): cascade_down = nº de quebras
estruturais bear consecutivas (BOS-/CHoCH-) imediatamente antes do candidato (janela 48h).
  CTX-A: cascade>=4 (N~228, hit-3R 34,6% base do contexto)
  CTX-B: cascade>=5 (N~97)   [=5 sozinho N47: referência, não sub-fatiável]

LEDGER DE LENTES (12, DECLARADAS ANTES DE CORRER — indicadores + binárias anteriores):
  L01 oversold15    rsi_low <= 30
  L02 legbase       legpos60 <= 0.10
  L03 below_ema21   g_ema21_dist < 0
  L04 deep_pull     pullback_depth >= 0.90
  L05 swept         g_sweep_depth >= 1.0
  L06 reclaim_forte reclaim_atr >= 1.5
  L07 atr_spike     g_atr_spike >= 1.27
  L08 demanda       in_demand==1 OU dist_demand_atr<=0.5
  L09 oversold1h    h1_rsi <= 42
  L10 choch_up_rec  CHoCH+ nas últimas 8 barras (SMC)
  L11 eql_swept     EQL varrido na janela (SMC)
  L12 nao_bear      g_v5h != BEAR
COMBOS: singles (12) + todos os pares (66) + trios APENAS dos pares com hit>=45% & N>=25 no CTX-A
(regra de expansão declarada). Grupos com N<20 não avaliados (poder).

AVALIAÇÃO (alvo = LUCRO): hit-3R e NET3 dentro do contexto. NULL por bootstrap de subconjuntos
(2000×): para grupo de tamanho n no contexto, P = frac(subconjunto aleatório de n do contexto com
hit >= obs); FAMÍLIA: max-stat z-score sobre o ledger inteiro → P_fam. GATE: hit>=45% & N>=30 &
P_fam<=0,05 declarado como "candidato a confirmação" (o gate duro 0,002 fica para dados/rondas
virgens; este é o primeiro teste da conjunção pré-registada). Painel completo para finalistas."""
import json, glob, bisect, hashlib, random
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
    if key in seen:
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    tok = (e["text"] + ("+" if c > e["price"] else "-")) if e["text"] in ("BOS", "CHoCH") else e["text"]
    events.append({"t": e["t"], "tok": tok, "price": e["price"]})
ET = [e["t"] for e in events]

def smc_feats(cj):
    t0 = cj - 192 * 900
    hi = bisect.bisect_right(ET, cj)
    win = [events[i] for i in range(hi) if events[i]["t"] >= t0]
    dirs = [e["tok"] for e in win if e["tok"] not in ("EQH", "EQL")]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    chup = int(any(e["tok"] == "CHoCH+" and cj - e["t"] <= 8 * 900 for e in win))
    swept = 0
    for e in win:
        if e["tok"] != "EQL":
            continue
        i0 = bisect.bisect_right(TS, e["t"]); i1 = bisect.bisect_right(TS, cj)
        if any(S[k]["l"] < e["price"] for k in range(i0, i1)):
            swept = 1; break
    return n, chup, swept

for u in U:
    u["_casc"], u["_chup"], u["_eqls"] = smc_feats(u["cj_t"])

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
    "L11_eql_swept": lambda u: u["_eqls"] == 1,
    "L12_nao_bear": lambda u: u.get("g_v5h") != "BEAR",
}
WEEKS = len({u["g_week"] for u in U})

def outcome(rows):
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in rows if u["cj_t"] in R3]
    nets = [R3[u["cj_t"]]["net3"] for u in rows if u["cj_t"] in R3]
    return hs, nets

def full_panel(rows, tag):
    rs = sorted([u for u in rows if u["cj_t"] in R3], key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rs]
    n = len(rs); w = sum(1 for x in nets if x > 0); h = sum(1 for u in rs if R3[u["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rs) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    s = sum(nets)
    print(f"  PAINEL {tag}: N{n} hit3R {100*h/n:.1f}% WR {100*w/n:.1f}% sumR {s:+.1f} avgR {s/n:+.3f} "
          f"DD {dd:.1f} r/DD {s/abs(dd) if dd else 0:.1f} stk-{mL} | {n/WEEKS:.2f}/sem | {yr}")

for CTXNAME, CMIN in (("CTX-A cascade>=4", 4), ("CTX-B cascade>=5", 5)):
    CTX = [u for u in U if u["_casc"] >= CMIN and u["cj_t"] in R3]
    hs0, nets0 = outcome(CTX)
    base = sum(hs0) / len(hs0)
    print("=" * 110)
    print(f"{CTXNAME}: N{len(CTX)} · hit-3R {100*base:.1f}% · NET3 {sum(nets0):+.1f}")
    ledger = []
    for nm, fn in LENSES.items():
        ledger.append((nm, [u for u in CTX if fn(u)]))
    keys = list(LENSES)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            g = [u for u in CTX if LENSES[keys[i]](u) and LENSES[keys[j]](u)]
            ledger.append((f"{keys[i]}&{keys[j]}", g))
    ledger = [(nm, g) for nm, g in ledger if len(g) >= 20]
    # expansão a trios: pares com hit>=45% & N>=25
    strong_pairs = []
    for nm, g in ledger:
        if "&" in nm:
            hs, _ = outcome(g)
            if len(hs) >= 25 and sum(hs) / len(hs) >= 0.45:
                strong_pairs.append(nm)
    for pair in strong_pairs:
        a, b = pair.split("&")
        for c in keys:
            if c in (a, b):
                continue
            g = [u for u in CTX if LENSES[a](u) and LENSES[b](u) and LENSES[c](u)]
            if len(g) >= 20:
                ledger.append((f"{pair}&{c}", g))
    # dedup nomes
    seen_nm = set(); L2 = []
    for nm, g in ledger:
        if nm not in seen_nm:
            seen_nm.add(nm); L2.append((nm, g))
    ledger = L2
    # null bootstrap: max z-score da família
    random.seed(9)
    HS = hs0
    obs = []
    for nm, g in ledger:
        hs, nets = outcome(g)
        obs.append((nm, len(hs), sum(hs) / len(hs), sum(nets)))
    maxz = []
    for _ in range(2000):
        m = -9
        for nm, n_, h_, _ in obs:
            samp = random.sample(HS, n_)
            r = sum(samp) / n_
            m = max(m, (r - base) / max(0.001, (base * (1 - base) / n_) ** 0.5))
        maxz.append(m)
    maxz.sort()
    def pfam(hit, n_):
        z = (hit - base) / max(0.001, (base * (1 - base) / n_) ** 0.5)
        return sum(1 for m in maxz if m >= z) / len(maxz)
    obs.sort(key=lambda x: -(x[2]))
    print(f"  ledger {len(ledger)} grupos · null max-z q95 {maxz[int(0.95*2000)]:.2f}")
    print(f"  {'grupo':<44} {'N':>4} {'hit3R%':>7} {'NET3':>8} {'P_fam':>6}")
    finalists = []
    for nm, n_, h_, net in obs[:14]:
        p = pfam(h_, n_)
        gate = h_ >= 0.45 and n_ >= 30 and p <= 0.05
        if gate:
            finalists.append(nm)
        print(f"  {nm:<44} {n_:>4} {100*h_:>6.1f}% {net:>+8.1f} {p:>6.3f}{'  <<< GATE' if gate else ''}")
    for nm in finalists:
        g = dict(ledger)[nm]
        full_panel(g, nm)
    json.dump({"ctx": CTXNAME, "n_ctx": len(CTX), "base_hit": round(base, 3),
               "top": [{"g": nm, "n": n_, "hit": round(h_, 3), "net3": round(float(net), 1),
                        "p_fam": pfam(h_, n_)} for nm, n_, h_, net in obs[:20]],
               "finalists": finalists},
              open(HERE / "results" / f"cascade_context_indicators_{CMIN}_20260705.json", "w"), indent=1)
print("OK → results/cascade_context_indicators_{4,5}_20260705.json")
