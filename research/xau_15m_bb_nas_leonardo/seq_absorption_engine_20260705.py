#!/usr/bin/env python3
"""ENGINE SEQUENCIAL ENRIQUECIDO (2026-07-05, frente 2 Cris): aprofundar o CARREGADOR (acumulação/
absorção/velocidade da virada NO TEMPO) para EXPANDIR N além dos 54 do RWS, mantendo streak<=4.
Mapa exaustivo mostrou que grupos estruturais/HTF não ajudam; a expansão mora no read sequencial.
Novos reads multi-barra:
  ACUM: buy bubbles acumulando (janelas 0-4/0-8/0-12, peso decrescente) = pressão compradora crescente
  ABSORÇÃO: sell M/L que NÃO derrubam (preço fecha acima do nível do sell) = vendedor absorvido
  VELOCIDADE: reclaim rápido pós-low ((close-low)/barras/atr) + reclaim_atr forte
  QUALIDADE: burst genuíno (recente>=antigo mas não spike-late-fake) + rsi_above_ma + anti-beardiv
SCORE contínuo → varre limiar → curva N × hit-3R × streak (achar máx N com streak<=4 e hit>>25%).
Walk-forward por ano em cada ponto. Universo selado."""
import json, glob, bisect, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
RSI = [b.get("rsi") for b in S]; RSIMA = [None] * Np
for i in range(Np):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
BUB = sorted([json.loads(l) for p in glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)],
             key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]
wgt = {"S": 1, "M": 2, "L": 3}
def bub(t0, wlo, whi):
    hi = bisect.bisect_right(BUBK, t0)
    return [BUB[i] for i in range(hi) if t0 - whi * 900 <= BUB[i]["t"] <= t0 - wlo * 900]
def score(r):
    cj_t = r["cj_t"]; i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return None
    atr = S[i].get("atr") or 1.0; close = S[i]["c"]
    w4 = bub(cj_t, 0, 4); w8 = bub(cj_t, 0, 8); w12 = bub(cj_t, 0, 12); old = bub(cj_t, 5, 10)
    # ACUM: pressão compradora crescente (recente pesa mais)
    buy4 = sum(wgt[x["size"]] for x in w4 if x["side"] == "BUY")
    buy8 = sum(wgt[x["size"]] for x in w8 if x["side"] == "BUY")
    acum = buy4 * 1.0 + (buy8 - buy4) * 0.5
    # ABSORÇÃO: sell M/L cujo close-do-sell < close-atual (vendedor não derrubou)
    absorb = sum(1 for x in w8 if x["side"] == "SELL" and x["size"] in ("M", "L") and x.get("c") is not None and close > x["c"])
    # VELOCIDADE: reclaim rápido pós-low local
    lo_i = min(range(max(0, i - 12), i + 1), key=lambda k: S[k]["l"])
    vel = (close - S[lo_i]["l"]) / atr / max(1, i - lo_i)
    # QUALIDADE
    burst = buy4 - sum(wgt[x["size"]] for x in old if x["side"] == "BUY")
    large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in w8))
    rsi_above = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):
            pv = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0, j - 2):j + 3])]
            if pv and RSI[k] is not None and RSI[pv[-1]] is not None and S[k]["h"] > S[pv[-1]]["h"] and RSI[k] < RSI[pv[-1]]: bd += 1
    j = bisect.bisect_right(NAST, cj_t) - 1
    nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj_t - nas[j]["t"]) // 900 <= 4)
    # SCORE contínuo (só componentes causais/positivos; anti-filtros duros)
    if bd >= 2: return {"score": -99, "acum": acum}                       # A7 duro
    if burst >= 3 and large8 == 0 and nas_short == 0: return {"score": -99, "acum": acum}  # A6 duro
    reclaim = fv(r, "reclaim_atr", 0)
    sc = (min(acum, 6) / 6 * 2.0            # acumulação (0-2)
          + min(absorb, 3) / 3 * 1.5        # absorção (0-1.5)
          + min(vel, 1.5) / 1.5 * 1.0       # velocidade (0-1)
          + min(reclaim, 3) / 3 * 1.0       # força reclaim (0-1)
          + rsi_above * 0.5                 # momentum
          + large8 * 0.5)                   # confirmação institucional
    return {"score": round(sc, 3), "acum": acum, "absorb": absorb, "vel": round(vel, 2), "buy4": buy4}
SC = {r["cj_t"]: score(r) for r in U}
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0 and SC.get(r["cj_t"]) is not None]
def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<18} vazio")
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[k] for k, r in enumerate(rs) if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    if show:
        allpos = all(v > 0 for v in yr.values())
        print(f"  {tag:<18} N{n:>4} hit3R {100*h/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} stk-{mL:>2} "
              f"| {n/WEEKS:.2f}/sem | {yr} {'✓anos+' if allpos else ''}")
    return {"n": n, "hit": h / n, "stk": mL, "net": sum(nets), "yr": yr}
print("=" * 104)
print("ENGINE SEQUENCIAL ENRIQUECIDO — curva N × hit-3R × streak (varre limiar do score)")
print("=" * 104)
print("RWS-original (referência): N54 hit 44,4%% streak 4")
print("\nSCORE >= limiar (achar máx N com streak<=4 e hit alto):")
best = None
for thr in [4.0, 3.5, 3.25, 3.0, 2.75, 2.5, 2.25, 2.0, 1.75]:
    keep = [r for r in NB if SC[r["cj_t"]]["score"] >= thr]
    s = panel(keep, f"score>={thr}")
    if s and s["stk"] <= 4 and s["hit"] >= 0.38 and (best is None or s["n"] > best[1]["n"]):
        best = (thr, s, keep)
if best:
    thr, s, keep = best
    print(f"\n>>> MELHOR (streak<=4, hit>=38%, máx N): score>={thr} · N{s['n']} hit {100*s['hit']:.1f}% streak {s['stk']} {s['n']/WEEKS:.2f}/sem")
    json.dump({"threshold": thr, **{k: s[k] for k in ("n", "hit", "stk", "net", "yr")},
               "per_week": s["n"] / WEEKS, "members_cjt": [r["cj_t"] for r in keep]},
              open(HERE / "results" / "seq_absorption_engine_20260705.json", "w"), indent=1)
print("OK → results/seq_absorption_engine_20260705.json")
