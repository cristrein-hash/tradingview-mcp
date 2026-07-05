#!/usr/bin/env python3
"""PAINEL COMPLETO do universo flush-reclaim causal (2026-07-05) — antes de qualquer claim.
Lê rows do round-1 (capitulation_discriminator_20260705.json). Painel canônico: N·WR·sumR·avgR·
DD·return/DD·streak·por-ano, bruto e NET-SB (custo $0,80 por lado → em R via risco em $).
Corte único PRÉ-DECLARADO do round-1: reclaim_atr ≤ 0,98 (Q1 — entrada colada ao fundo).
Reconciliação com DA-36,5%: variante SEM flush-death (reclaim admitido mesmo após low quebrado)
e SEM dedup-16 para expor de onde vem a diferença."""
import json, glob, bisect, statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
D = json.load(open(HERE / "results" / "capitulation_discriminator_20260705.json"))
rows = D["rows"]

def panel(rs, tag):
    if not rs:
        print(f"  {tag:<34} vazio"); return
    rs = sorted(rs, key=lambda r: r["t"])
    # custo SB: $0,80 round-trip; risco em $ = risk_price. r_net = r - 0.8/risk$
    nets = []
    for r in rs:
        nets.append(r["r"] - 0.8 / r["risk_usd"] if r.get("risk_usd") else r["r"])
    n = len(rs); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets):
        y = dt.datetime.utcfromtimestamp(r["t"]).year
        yr[y] = round(yr.get(y, 0) + x, 1)
    s = sum(nets)
    print(f"  {tag:<34} N{n:>4} WR {100*w/n:>5.1f}% sumR {s:>+8.1f} avgR {s/n:>+.3f} "
          f"DD {dd:>6.1f} r/DD {(s/abs(dd) if dd else 0):>5.1f} stk-{mL} | {yr}")

# risco em $ por trade (para custo): risk = entry - sl em pontos = $ por 1 unidade...
# convenção do projeto: risco em $ = pontos de risco (XAU 1pt=$1/oz); custo 0,80/risk_pts em R
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
for r in rows:
    i = bisect.bisect_right(TS, r["entry_t"]) - 1
    atrf = S[bisect.bisect_right(TS, r["t"]) - 1].get("atr") or 5.0
    e = S[i]["c"]; sl = r["flush_low"] - 0.3 * atrf
    r["risk_usd"] = max(0.01, e - sl)

print("=" * 118)
print("PAINEL — universo flush-reclaim causal (novo low 96b → reclaim +0,3ATR ≤16b sem low novo → SL 0,3ATR abaixo → 3R)")
print("=" * 118)
panel(rows, "BASE N335 (bruto→NET-SB)")
pocket = [r for r in rows if r["reclaim_atr"] <= 0.98]
panel(pocket, "POCKET reclaim_atr≤0,98 (Q1)")
cris = [r for r in rows if r["is_cris"]]
panel(cris, "dentro do rótulo Cris (25)")
print()
# risco mediano em $ (contexto de custo)
print(f"  risco mediano: base {st.median(r['risk_usd'] for r in rows):.1f}$ · pocket "
      f"{st.median(r['risk_usd'] for r in pocket):.1f}$  (custo 0,80$ ⇒ "
      f"{0.8/st.median(r['risk_usd'] for r in pocket):.2f}R no pocket)")
print()
# ---- reconciliação com DA 36,5%: sem flush-death, sem dedup ----
flushes_all = [i for i in range(96, len(S)) if S[i]["l"] < min(S[j]["l"] for j in range(i - 96, i))]
res_da = []
for fi in flushes_all:
    fb = S[fi]; atr = fb.get("atr") or 5.0; flo = fb["l"]
    ei = None
    for k in range(fi + 1, min(len(S), fi + 17)):
        if S[k]["c"] >= flo + 0.3 * atr:
            ei = k; break            # SEM flush-death: aceita reclaim mesmo com low novo antes
    if ei is None: continue
    e = S[ei]["c"]; sl = flo - 0.3 * atr; risk = e - sl
    if risk <= 0: continue
    tgt = e + 3 * risk; rr = None
    for k in range(ei + 1, min(len(S), ei + 193)):
        if S[k]["l"] <= sl: rr = -1.0; break
        if S[k]["h"] >= tgt: rr = 3.0; break
    if rr is None:
        k = min(len(S) - 1, ei + 192); rr = (S[k]["c"] - e) / risk
    res_da.append(rr)
h = sum(1 for x in res_da if x >= 3)
print(f"RECONCILIAÇÃO variante-DA (todo novo-low, sem death/dedup): N{len(res_da)} "
      f"hit-3R {100*h/len(res_da):.1f}% NET {sum(res_da):+.1f}R")
print("  → a diferença vs 50,1% vem das regras flush-death (low quebrado mata o setup) + dedup episódico")
