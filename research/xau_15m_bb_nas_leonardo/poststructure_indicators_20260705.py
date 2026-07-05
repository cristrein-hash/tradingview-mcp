#!/usr/bin/env python3
"""FASE 2 — INDICADORES PÓS-ESTRUTURA (2026-07-05, diretriz Cris: indicadores em confluência DEPOIS da
estrutura dizem muito mais que soltos). Passo 1: POOL ESTRUTURAL = dip 15M profundo (fundo/abaixo-EMA/
sweep) + correção 4H (abaixo EMA21-4H, retração funda, sem HH recente) — o contexto do fundo genuíno.
Passo 2: DENTRO do pool, ranqueia confluências de indicadores (NAS, bubbles absorção/iniciativa, OB
demanda, SMC CHoCH, SVP POC/VAH/VAL, volume) por HIT-3R e por lift-MON+FORTE. Passo 3: convergência →
subset final (hit-3R + streak + freq). Alvo forward N=58 = CALIBRAÇÃO. Universo selado."""
import json, hashlib, collections, bisect, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
SB = 0.80
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
LEG = {x["cj_t"]: x for x in (json.loads(l) for l in open(HERE / "results" / "htf_leg_features_20260705.jsonl"))}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)
UC = {r["cj_t"]: r for r in U}
# SVP HTF (POC/VAH/VAL) asof 4H, p/ leitura de value-area
H4 = json.load(open(HERE / "htf_primitives" / "htf_4H.primitives.json"))["series"]
H4 = sorted(H4, key=lambda b: b["t"]); H4T = [b["t"] for b in H4]
def svp4h(cj_t):
    i = bisect.bisect_right(H4T, cj_t - 14400) - 1
    return H4[i] if i >= 0 else None

# ---- PASSO 1: POOL ESTRUTURAL (contexto do fundo genuíno; congelado das medianas) ----
def struct_pool(r):
    L = LEG.get(r["cj_t"], {})
    return (r["g_v5h"] != "BEAR" and r["g_knife"] == 0
        and fv(r, "g_box96", .5) <= 0.45              # dip 15M no fundo do range
        and fv(r, "g_ema21_dist", 9) <= 0.2           # não-esticado
        and fv(r, "legpos60", 1) <= 0.35              # base da perna 15M
        and fv(r, "g_sweep_depth", 0) >= 0.5          # varredura de liquidez
        and L.get("h4_ema21_dist", 9) <= 0.5          # correção 4H (abaixo/na EMA21-4H)
        and L.get("h4_retrace", 0) >= 0.3)            # retração 4H funda
POOL = [r for r in U if struct_pool(r)]
base_all = len(MF) / len(U)
mf_pool = sum(1 for r in POOL if r["cj_t"] in MF)
h3 = lambda rows: sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3) / len(rows) if rows else 0
print("=" * 100)
print("FASE 2 — INDICADORES PÓS-ESTRUTURA")
print("=" * 100)
print(f"POOL ESTRUTURAL (fundo genuíno): N={len(POOL)} ({len(POOL)/WEEKS:.2f}/sem) · hit3R {100*h3(POOL):.1f}% "
      f"· MON+FORTE dentro {mf_pool}/{len(MF)} · precisão-MF {100*mf_pool/len(POOL):.1f}% (base {100*base_all:.2f}%)")
base_pool = mf_pool / len(POOL) if POOL else 0

# ---- PASSO 2: indicadores DENTRO do pool ----
IND = {
 "NAS long 16": lambda r: fv(r, "nas_long_16", 0) >= 1,
 "h1n choch up": lambda r: fv(r, "h1n_choch_up_rec") == 1,
 "h4n choch up": lambda r: fv(r, "h4n_choch_up_rec") == 1,
 "absorção sell (sell_bub>=4)": lambda r: fv(r, "sell_bub_w", 0) >= 4,
 "iniciativa buy (buy_bub>=4)": lambda r: fv(r, "buy_bub_w", 0) >= 4,
 "in_demand": lambda r: fv(r, "in_demand") == 1,
 "htf_demand_confl": lambda r: fv(r, "htf_demand_confluence") == 1,
 "h1n_in_demand": lambda r: fv(r, "h1n_in_demand") == 1,
 "reclaim>=2": lambda r: fv(r, "reclaim_atr", 0) >= 2.0,
 "up_closes>=3": lambda r: fv(r, "up_closes_pc", 0) >= 3,
 "SVP: entry<=VAL (value buy)": lambda r: (lambda b: b is not None and b.get("val") is not None and r["g_entry"] <= b["val"])(svp4h(r["cj_t"])),
 "SVP: entry<=POC": lambda r: (lambda b: b is not None and b.get("poc") is not None and r["g_entry"] <= b["poc"])(svp4h(r["cj_t"])),
 "rsi_low>=35": lambda r: fv(r, "rsi_low", 50) >= 35,
 "micro_hl": lambda r: fv(r, "micro_hl") == 1,
}
print(f"\nINDICADORES DENTRO do pool (hit3R do pool {100*h3(POOL):.1f}%; ordenado por hit3R condicionado):")
rows = []
for nm, fn in IND.items():
    sub = [r for r in POOL if fn(r)]
    if len(sub) < 8: rows.append((nm, 0, len(sub), 0, 0)); continue
    hh = h3(sub); mfin = sum(1 for r in sub if r["cj_t"] in MF)
    rows.append((nm, hh, len(sub), mfin, mfin / len(sub)))
rows.sort(key=lambda x: -x[1])
for nm, hh, nn, mfin, prec in rows:
    fl = " <<<" if hh >= 0.45 and nn >= 15 else ""
    print(f"  hit3R {100*hh:>5.1f}%  N{nn:>3}  MF {mfin}  prec {100*prec:>4.1f}%  {nm}{fl}")

# ---- PASSO 3: convergência dos indicadores TOP dentro do pool ----
TOP = [nm for nm, hh, nn, mfin, prec in rows if hh >= h3(POOL) and nn >= 12][:6]
print(f"\nCONVERGÊNCIA indicadores pós-estrutura {TOP}:")
def iv(r): return sum(1 for nm in TOP if IND[nm](r))
def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    hh = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    mfin = sum(1 for r in rs if r["cj_t"] in MF)
    print(f"  {tag:<16} N{n:>3} hit3R {100*hh/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>6.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | MF {mfin}/{len(MF)} prec {100*mfin/n:.0f}% | {yr}")
    return {"n": n, "hit": hh / n, "stk": mL, "net": sum(nets), "mf": mfin}
res = {}
for k in range(1, len(TOP) + 1):
    keep = [r for r in POOL if iv(r) >= k]
    s = panel(keep, f"pool & >={k} ind")
    if s: res[k] = {**s, "members": [r["cj_t"] for r in keep]}
json.dump({"pool_n": len(POOL), "pool_hit": h3(POOL), "top_ind": TOP,
           "convergence": {k: {kk: v[kk] for kk in ("n", "hit", "stk", "net", "mf")} for k, v in res.items()}},
          open(HERE / "results" / "poststructure_indicators_20260705.json", "w"), indent=1)
print("OK → results/poststructure_indicators_20260705.json")
