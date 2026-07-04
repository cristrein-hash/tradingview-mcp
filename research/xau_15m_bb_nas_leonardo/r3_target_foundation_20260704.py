#!/usr/bin/env python3
"""FUNDAÇÃO DO PROGRAMA 3R (2026-07-04, ordem Cris: exit FIXO 3R; otimizar entradas + cortes).
Computa o ALVO R3 (first-touch +3R antes do SL; same-bar ambíguo=−1; HMAX480) para TODOS os 4739
candidatos do universo selado (SL estrutural do candidato flush−0,1ATR) e produz as primeiras
leituras honestas: taxa-base de hit-3R por regime · base435@3R (reconcilia com exit lab) ·
SistemaA@3R · **LANE BEAR-PULLBACK** (mandato: em BEAR intenso, pullbacks bull podem render) —
recon das lentes causais candidatas em TODO o histórico BEAR (1146 candidatos incl. extensão).
STATUS: EXPLORATORY primeira-leitura (ledger: lentes BEAR pré-declaradas abaixo, 8; zero grid).
Output: results/r3_target_universe_20260704.jsonl (candidato+R3) + sumário impresso."""
import json, glob, bisect, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]

def r3(i, entry, sl):
    risk = entry - sl; tgt = entry + 3 * risk; end = min(i + 480, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= sl: return -1.0
        if H[k] >= tgt: return 3.0
    return max(-1.0, min(3.0, (C[end] - entry) / risk))
def asof(t): return bisect.bisect_right(TS, t) - 1

rows = []
for r in U:
    i = asof(r["cj_t"])
    R = r3(i, r["g_entry"], r["g_sl"])
    rows.append({**{k: r.get(k) for k in ("cj_t", "yr", "g_v5h", "g_entry", "g_sl", "g_risk", "g_atr",
                                          "g_in_base435", "block")},
                 "R3": round(R, 3), "net3": round(R - SB / r["g_risk"], 3),
                 "src": r})
with open(HERE / "results" / "r3_target_universe_20260704.jsonl", "w") as fh:
    for x in rows:
        fh.write(json.dumps({k: v for k, v in x.items() if k != "src"}) + "\n")

def panel(sub, tag):
    n = len(sub)
    if not n: print(f"  {tag:<34} vazio"); return None
    ns = [x["net3"] for x in sorted(sub, key=lambda x: x["cj_t"])]
    w = sum(1 for x in ns if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in ns:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    hit = sum(1 for x in sub if x["R3"] >= 3)
    print(f"  {tag:<34} N{n:>4} hit3R {100*hit/n:>5.1f}% WRliq {100*w/n:>5.1f}% NET {sum(ns):>8.1f} "
          f"avg {sum(ns)/n:>6.3f} DD {dd:>7.1f} stk-{mL}")
    return {"N": n, "hit": hit / n, "net": sum(ns)}

print("=" * 108)
print("PROGRAMA 3R — alvo congelado (first-touch 3R vs SL estrutural) · universo 4739 · CALIBRAÇÃO 1ª leitura")
print("=" * 108)
print("TAXAS-BASE por regime (breakeven bruto do 3R = 25% hit):")
for rg in ("BULL", "RANGE", "BEAR"):
    panel([x for x in rows if x["g_v5h"] == rg], f"universo {rg}")
panel(rows, "universo TOTAL")
print("\nSISTEMAS EXISTENTES sob 3R (reconciliação):")
b435 = [x for x in rows if x["g_in_base435"] == 1 and x["g_v5h"] != "BEAR"]
st = panel(b435, "BASE435 @3R")
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
panel([x for x in rows if sysA(x["src"])], "SISTEMA_A @3R")

print("\nLANE BEAR-PULLBACK (mandato Cris) — recon em TODOS os candidatos BEAR (hist+extensão):")
BEAR = [x for x in rows if x["g_v5h"] == "BEAR"]
LENSES = {  # 8 lentes pré-declaradas (ledger), inspiradas no g_bear_pullback_ok + sobreviventes reprecificados
    "bp_ok_congelada": lambda s: s.get("g_bear_pullback_ok") == 1,
    "choch1h_up": lambda s: fv(s, "h1n_choch_up_rec") == 1,
    "h1_trend_up": lambda s: fv(s, "h1n_trend") == 1,
    "reclaim_ge1": lambda s: fv(s, "reclaim_atr") >= 1.0,
    "rsi_div": lambda s: s.get("g_rsi_div") == 1,
    "swept": lambda s: fv(s, "swept_prior_low") == 1,
    "sem_faca": lambda s: s.get("g_knife") == 0,
    "capitulacao_sellL": lambda s: fv(s, "sell_bub_w") >= 4,
}
for nm, fn in LENSES.items():
    panel([x for x in BEAR if fn(x["src"])], f"BEAR & {nm}")
print("\nCONVERGÊNCIAS (pares pré-declarados das 3 com melhor hit — impressos TODOS, sem seleção):")
import itertools
hits = {}
for nm, fn in LENSES.items():
    sub = [x for x in BEAR if fn(x["src"])]
    if len(sub) >= 25: hits[nm] = sum(1 for x in sub if x["R3"] >= 3) / len(sub)
top3 = sorted(hits, key=lambda k: -hits[k])[:3]
for a, b in itertools.combinations(top3, 2):
    panel([x for x in BEAR if LENSES[a](x["src"]) and LENSES[b](x["src"])], f"BEAR & {a} & {b}")
print(f"\n(extensão mai→jul-26: {sum(1 for x in BEAR if x['cj_t'] > 1779667200)} candidatos BEAR novos incluídos)")
print("OK → results/r3_target_universe_20260704.jsonl")
