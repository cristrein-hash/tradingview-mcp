#!/usr/bin/env python3
"""ENGINE AMPLO DE LEITURA DE FUNDOS 15M (2026-07-05, Cris: mapear fundos à EXAUSTÃO, contextualizado —
não uma lógica pronta solta). Combina 4 GRUPOS de lentes já validados/promissores nesta jornada:
  SEQ  (sequencial, porte V1.4g-RWS): buy_recent · burst · large8 · rsi_above_ma · anti_beardiv · anti_burst
  STR  (fundo estrutural): box96 baixo · legpos60 baixo · sweep_depth · ema21_dist não-esticado · pullback
  HTF  (perna 4H/1D): correção 4H (below ema21, retrace fundo) · d1 contexto
  IND  (indicadores pós-estrutura): in_demand · htf_demand · choch_up · reclaim · nas_long · absorção
Passos: (1) medir hit-3R/streak/N de CADA grupo sozinho; (2) RWS-base REFINADO por cada grupo (contexto
melhora?); (3) arquétipos disjuntos (SEQ-pop vs STR-pop, overlap); (4) score amplo = soma de grupos,
mapa hit-3R por nº de grupos ativos. STATUS: MAPA/CALIBRAÇÃO (promoção exige prereg+DA+walk-forward).
Reusa FT sequencial do rws engine (recomputa). Universo selado."""
import json, glob, bisect, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
LEG = {x["cj_t"]: x for x in (json.loads(l) for l in open(HERE / "results" / "htf_leg_features_20260705.jsonl"))}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)

# --- reconstruir features sequenciais (RWS) ---
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
RSI = [b.get("rsi") for b in S]
RSIMA = [None] * Np
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
def seqf(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return {}
    recent = bub(cj_t, 0, 4); older = bub(cj_t, 5, 10); win8 = bub(cj_t, 0, 8)
    br = sum(wgt[x["size"]] for x in recent if x["side"] == "BUY")
    o = {"buy_recent": br, "burst": br - sum(wgt[x["size"]] for x in older if x["side"] == "BUY"),
         "large8": int(any(x["side"] == "BUY" and x["size"] == "L" for x in win8)),
         "sell_ml8": sum(1 for x in win8 if x["side"] == "SELL" and x["size"] in ("M", "L")),
         "rsi_above": int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])}
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):
            pv = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0, j - 2):j + 3])]
            if pv and RSI[k] is not None and RSI[pv[-1]] is not None and S[k]["h"] > S[pv[-1]]["h"] and RSI[k] < RSI[pv[-1]]: bd += 1
    o["beardiv"] = bd
    j = bisect.bisect_right(NAST, cj_t) - 1
    o["nas_short"] = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj_t - nas[j]["t"]) // 900 <= 4)
    o["nas_long"] = int(j >= 0 and nas[j]["dir"] == "LONG" and (cj_t - nas[j]["t"]) // 900 <= 24)
    return o
SF = {r["cj_t"]: seqf(r["cj_t"]) for r in U}

# --- os 4 grupos como booleanos causais ---
def gSEQ(r):
    f = SF.get(r["cj_t"], {})
    if not f: return False
    if f.get("buy_recent", 0) < 2: return False
    if f.get("rsi_above") == 0 and fv(r, "n_supply_overhead", 99) <= 20: return False
    if f.get("burst", 0) >= 3 and f.get("large8") == 0 and f.get("nas_short") == 0: return False
    if f.get("beardiv", 0) >= 2: return False
    return True
def gSTR(r):
    return (fv(r, "g_box96", .5) <= 0.5 and fv(r, "legpos60", 1) <= 0.4 and fv(r, "g_sweep_depth", 0) >= 0.5
            and fv(r, "g_ema21_dist", 9) <= 0.5)
def gHTF(r):
    L = LEG.get(r["cj_t"], {})
    return L.get("h4_ema21_dist", 9) <= 0.6 and L.get("h4_retrace", 0) >= 0.3
def gIND(r):
    return ((fv(r, "in_demand") == 1 or fv(r, "htf_demand_confluence") == 1)
            and (fv(r, "reclaim_atr", 0) >= 1.5 or fv(r, "h1n_choch_up_rec") == 1 or SF.get(r["cj_t"], {}).get("nas_long") == 1))
GRP = {"SEQ": gSEQ, "STR": gSTR, "HTF": gHTF, "IND": gIND}

def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<26} vazio")
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, r in enumerate(rs) if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    if show:
        print(f"  {tag:<26} N{n:>4} hit3R {100*h/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} stk-{mL} "
              f"| {n/WEEKS:.2f}/sem | {yr}")
    return {"n": n, "hit": h / n, "stk": mL, "net": sum(nets)}

NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
print("=" * 100)
print("ENGINE AMPLO DE FUNDOS 15M — mapa exaustivo (não-BEAR N=%d, %.1f/sem)" % (len(NB), len(NB) / WEEKS))
print("=" * 100)
print("(1) CADA GRUPO SOZINHO:")
for g, fn in GRP.items(): panel([r for r in NB if fn(r)], f"grupo {g}")
print("\n(2) RWS(SEQ)-base REFINADO por cada contexto (contexto MELHORA/expande?):")
seqpop = [r for r in NB if gSEQ(r)]
panel(seqpop, "SEQ base")
for g in ("STR", "HTF", "IND"):
    panel([r for r in seqpop if GRP[g](r)], f"SEQ & {g}")
print("\n(3) ARQUÉTIPOS DISJUNTOS (overlap dos grupos):")
sets = {g: set(r["cj_t"] for r in NB if fn(r)) for g, fn in GRP.items()}
for a in GRP:
    for b in GRP:
        if a < b:
            ov = len(sets[a] & sets[b]); print(f"  {a}∩{b} = {ov}  ({a}={len(sets[a])} {b}={len(sets[b])})")
print("\n(4) SCORE AMPLO = nº de grupos ativos (mapa exaustivo):")
res = {}
for k in (1, 2, 3, 4):
    keep = [r for r in NB if sum(1 for fn in GRP.values() if fn(r)) >= k]
    s = panel(keep, f">={k}/4 grupos")
    if s: res[k] = s
# união dos arquétipos fortes: SEQ (proven) OU (STR&HTF&IND) — bottoms profundos contextualizados
alt = [r for r in NB if gSEQ(r) or (gSTR(r) and gHTF(r) and gIND(r))]
print("\n(5) UNIÃO ARQUÉTIPOS: SEQ ∪ (STR&HTF&IND):")
panel(alt, "SEQ ∪ fundo-context")
json.dump({"groups_alone": {g: panel([r for r in NB if fn(r)], g, show=False) for g, fn in GRP.items()},
           "score_map": res, "seq_n": len(seqpop)},
          open(HERE / "results" / "broad_bottom_engine_20260705.json", "w"), indent=1)
print("OK → results/broad_bottom_engine_20260705.json")
