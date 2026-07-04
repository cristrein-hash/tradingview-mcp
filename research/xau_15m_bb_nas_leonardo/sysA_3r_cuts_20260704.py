#!/usr/bin/env python3
"""FRENTE 1 (2026-07-04): SISTEMA A sob exit congelado 3R — cortes de losers pré-declarados.
Semente: N53, hit3R 49,1%, +47,1 NET, stk −4 (r3_target_foundation). Objetivo Cris: ≥55% hit
mantendo ~1/sem e streak ≤4. LEDGER = 5 lentes (sobreviventes do perfil reprecificado a close real,
medidas na barra do cj do candidato) + convergência ≥1-de-k das aprovadas — TODAS impressas, zero
seleção escondida. N pequeno (53) = CALIBRAÇÃO declarada; nulls random-cut mesmo-N (500) por lente.
Contexto por barra reusa as funções do remap (choch/quiet/fluxo) na timeline global."""
import json, glob, bisect, random, hashlib, statistics as stt
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
SB = 0.80
random.seed(42)

R3U = {}
for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl"):
    d = json.loads(l); R3U[d["cj_t"]] = d
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
A = sorted([r for r in U if sysA(r)], key=lambda r: r["cj_t"])
assert len(A) == 53

# contexto de barra (choch/quiet/fluxo) — mesmas construções do remap reprecificado
series = {}; smcs = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    smcs += [e for e in d["smc_events"] if "CHOCH" in str(e.get("text", "")).upper()]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
smcs.sort(key=lambda e: e["t"]); SMCT = [e["t"] for e in smcs]
b30 = {}
for b in S:
    key = b["t"] // 1800
    r = b30.setdefault(key, {"h": b["h"], "l": b["l"], "t_close": b["t"]})
    r["h"] = max(r["h"], b["h"]); r["l"] = min(r["l"], b["l"]); r["t_close"] = max(r["t_close"], b["t"])
B30 = sorted(b30.values(), key=lambda r: r["t_close"])
B30C = [r["t_close"] for r in B30]; TR30 = [r["h"] - r["l"] for r in B30]
ATR30 = []; a = None
for tr in TR30: a = tr if a is None else (a * 13 + tr) / 14.0; ATR30.append(a)
BUB60 = []
for p in sorted(SBX.glob("bub60/*.bubbles.jsonl")):
    BUB60 += [json.loads(l) for l in open(p)]
BUB60.sort(key=lambda x: x["t"])
def ctx(t0):
    j = bisect.bisect_right(SMCT, t0) - 1
    choch24 = j >= 0 and (t0 - SMCT[j]) // 900 <= 24
    q = None
    jj = bisect.bisect_right(B30C, t0) - 1
    if jj >= 20: q = sum(TR30[jj - 3:jj + 1]) / 4.0 / max(1e-9, ATR30[jj])
    w6 = t0 - 6 * 3600; w24 = t0 - 24 * 3600
    bb = [x for x in BUB60 if (x.get("known_at") or x["t"]) <= t0 and x["t"] > w24]
    no_init = sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L") and x["t"] > w6) == 0
    selldom = (sum(1 for x in bb if x["side"] == "SELL" and x["size"] in ("M", "L")) >
               sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L")))
    return {"choch24": choch24, "quiet_ok": q is not None and q <= 1.0, "no_init": no_init, "selldom": selldom}

LENSES = {
    "L1_choch24_15m": lambda r, c: c["choch24"],
    "L2_quiet30": lambda r, c: c["quiet_ok"],
    "L3_noinit_1h": lambda r, c: c["no_init"],
    "L4_selldom_1h": lambda r, c: c["selldom"],
    "L5_rsi_40_60": lambda r, c: 40 <= (r.get("src", r).get("rsi_low") or 50) <= 60 if False else True,
}
# L5 rotulada indisponível de forma limpa no cj (rsi 1H exigiria asof 1H) — DECLARADA e removida do ledger executável.
del LENSES["L5_rsi_40_60"]

CTX = {r["cj_t"]: ctx(r["cj_t"]) for r in A}
def panel(sub, tag):
    n = len(sub)
    if not n: print(f"  {tag:<26} vazio"); return None
    ns = sorted(sub, key=lambda r: r["cj_t"])
    nets = [R3U[r["cj_t"]]["net3"] for r in ns]
    hit = sum(1 for r in ns if R3U[r["cj_t"]]["R3"] >= 3)
    w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(ns, nets):
        yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    print(f"  {tag:<26} N{n:>3} hit3R {100*hit/n:>5.1f}% NET {sum(nets):>6.1f} DD {dd:>6.1f} stk-{mL} | anos {yr}")
    return {"n": n, "hit": hit / n, "net": sum(nets), "stk": mL}

print("=" * 100)
print("FRENTE 1 — SISTEMA A sob 3R: cortes pré-declarados (CALIBRAÇÃO N53; ledger integral)")
print("=" * 100)
base = panel(A, "A @3R (semente)")
res = {}
for nm, fn in LENSES.items():
    keep = [r for r in A if fn(r, CTX[r["cj_t"]])]
    st = panel(keep, f"A & {nm}")
    if st and 0 < len(keep) < 53:
        cut = 53 - len(keep)
        nd = []
        for _ in range(500):
            pick = random.sample(A, len(keep))
            nd.append(sum(R3U[r["cj_t"]]["net3"] for r in pick))
        pct = 100 * sum(1 for x in nd if x < st["net"]) / len(nd)
        print(f"      corta {cut} · null random-keep mesmo-N: pct {pct:.0f}%")
        res[nm] = {"keep": len(keep), "hit": st["hit"], "net": st["net"], "pct": pct}
print("\nCONVERGÊNCIAS (todas impressas):")
for k in (2, 3):
    keep = [r for r in A if sum(1 for fn in LENSES.values() if fn(r, CTX[r["cj_t"]])) >= k]
    panel(keep, f"A & >= {k} de 4 lentes")
json.dump(res, open(HERE / "results" / "sysA_3r_cuts_20260704.json", "w"), indent=1)
print("OK → results/sysA_3r_cuts_20260704.json")
