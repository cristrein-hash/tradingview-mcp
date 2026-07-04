#!/usr/bin/env python3
"""DA MTF SIGNATURE GATE — ATAQUE 1: MECANISMO DO COLAPSO (60% -> 3/35).
Hipótese: a separação do discovery era função do PREÇO-ÂNCORA retroativo (~0,83R
abaixo do mercado). Recompute a assinatura nos 35 sob variantes controladas:
  A: t=t_dele, price=entry_dele (fiction)      -> deve reproduzir 21/35 (60%)
  B: t=t_dele, price=close15M@t_dele (real)    -> isola o PREÇO (mesmo tempo)
  C: t=cj do candidato matched, price=close@cj -> deve reproduzir 3/35 (gate test)
  D: t=cj do candidato, price=entry_dele       -> isola o TEMPO (mesmo preço fictício)
Decomposição por perna (supply_far_3atr_15M / demand_near_1atr_1H) em cada variante.
Referência de controles: pass-rate do universo no cj = 358/4499 (8,0%).
Read-only; nada de chart/RAW/produção; sem commit (mandato DA)."""
import json, bisect, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = sorted([json.loads(l) for l in open(CANON)], key=lambda r: r["cj_t"])
Ut = [r["cj_t"] for r in U]

def load_zones_series(paths):
    zones = []; series = {}
    for p in paths:
        d = json.load(open(p))
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
        for b in d["series"]: series.setdefault(b["t"], b)
    S = sorted(series.values(), key=lambda b: b["t"])
    return zones, S, [b["t"] for b in S]

Z15, S15, T15 = load_zones_series(sorted((HERE / "primitives").glob("*.primitives.json")))
Z60, S60, T60 = load_zones_series(sorted(SBX.glob("prim60/*.primitives.json")))
DEM60 = sorted([z for z in Z60 if "DEMAND" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
SUP15 = sorted([z for z in Z15 if "SUPPLY" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])

def atr_asof(S, T, t0):
    j = bisect.bisect_right(T, t0) - 1
    return (S[j].get("atr") or 1.0) if j >= 0 else 1.0

def supply_far(t0, price):
    a = atr_asof(S15, T15, t0)
    for z in SUP15:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]) and z["low"] >= price and (z["low"] - price) / a < 3.0:
            return False
    return True

def demand_near(t0, price):
    a = atr_asof(S60, T60, t0)
    for z in DEM60:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]):
            if z["low"] <= price <= z["high"]: return True
            if z["high"] <= price and (price - z["high"]) / a <= 1.0: return True
    return False

def close15(t0):
    j = bisect.bisect_right(T15, t0) - 1
    return S15[j]["c"]

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
rows = []
for r in sorted(AN, key=lambda x: x["t"]):
    t_his, px_his = r["t"], r["entry"]
    i = bisect.bisect_right(Ut, t_his) - 1
    cand = U[i] if i >= 0 and t_his - U[i]["cj_t"] <= 24 * 900 else None
    a15 = atr_asof(S15, T15, t_his)
    mkt = close15(t_his)
    row = {"n": r["n"], "utc": r["utc"], "gap_atr": round((mkt - px_his) / a15, 2),
           "gap_R": round((mkt - px_his) / r["risk"], 2) if r.get("risk") else None,
           "cand_dt_bars": (t_his - cand["cj_t"]) // 900 if cand else None}
    for tag, (t0, px) in {
        "A_hisT_hisPx": (t_his, px_his),
        "B_hisT_mktPx": (t_his, mkt),
        "C_cjT_cjPx": (cand["cj_t"], cand["g_entry"]) if cand else (None, None),
        "D_cjT_hisPx": (cand["cj_t"], px_his) if cand else (None, None),
    }.items():
        if t0 is None:
            row[tag] = None; continue
        s, d = supply_far(t0, px), demand_near(t0, px)
        row[tag] = {"sup": int(s), "dem": int(d), "gate": int(s and d)}
    rows.append(row)

print("=" * 100)
print("MECANISMO — 35 alvos sob 4 variantes (perna sup / perna dem / gate)")
print("=" * 100)
print(f"{'n':>3} {'utc':<17} {'gapATR':>6} {'gapR':>5} {'dtb':>4} | " +
      " | ".join(f"{k:<14}" for k in ("A his/his", "B his/mkt", "C cj/cj", "D cj/his")))
for row in rows:
    cells = []
    for tag in ("A_hisT_hisPx", "B_hisT_mktPx", "C_cjT_cjPx", "D_cjT_hisPx"):
        v = row[tag]
        cells.append("   --  " if v is None else f"s{v['sup']} d{v['dem']} g{v['gate']}")
    print(f"{row['n']:>3} {row['utc']:<17} {row['gap_atr']:>6} {str(row['gap_R']):>5} {str(row['cand_dt_bars']):>4} | " +
          " | ".join(f"{c:<14}" for c in cells))

print("\nAGREGADO (pass / N avaliável):")
for tag in ("A_hisT_hisPx", "B_hisT_mktPx", "C_cjT_cjPx", "D_cjT_hisPx"):
    ok = [row[tag] for row in rows if row[tag] is not None]
    n = len(ok)
    print(f"  {tag:<14} gate {sum(v['gate'] for v in ok):>2}/{n}  ({100*sum(v['gate'] for v in ok)/n:.0f}%)"
          f"  | sup_far {sum(v['sup'] for v in ok):>2}/{n} ({100*sum(v['sup'] for v in ok)/n:.0f}%)"
          f"  | dem_near {sum(v['dem'] for v in ok):>2}/{n} ({100*sum(v['dem'] for v in ok)/n:.0f}%)")

gaps = sorted(row["gap_atr"] for row in rows)
gapsR = sorted(row["gap_R"] for row in rows if row["gap_R"] is not None)
print(f"\nGAP preço (close15M@t_dele − entry_dele): mediana {gaps[len(gaps)//2]:.2f} ATR15 · {gapsR[len(gapsR)//2]:.2f} R")
n_pass_cj = sum(1 for r in U if r["cj_t"] <= T60[-1] and supply_far(r["cj_t"], r["g_entry"]) and demand_near(r["cj_t"], r["g_entry"]))
n_cov = sum(1 for r in U if r["cj_t"] <= T60[-1])
print(f"Referência controles (universo no cj, recomputado): {n_pass_cj}/{n_cov} = {100*n_pass_cj/n_cov:.1f}%")

# transições por perna A->B (mesmo tempo, preço real): quem morre e por quê
kill_sup = sum(1 for row in rows if row["A_hisT_hisPx"]["sup"] and not row["B_hisT_mktPx"]["sup"])
kill_dem = sum(1 for row in rows if row["A_hisT_hisPx"]["dem"] and not row["B_hisT_mktPx"]["dem"])
gA = sum(1 for row in rows if row["A_hisT_hisPx"]["gate"])
gB = sum(1 for row in rows if row["B_hisT_mktPx"]["gate"])
gAB = sum(1 for row in rows if row["A_hisT_hisPx"]["gate"] and row["B_hisT_mktPx"]["gate"])
print(f"\nA→B (só troca preço fictício→real, tempo fixo): gate {gA}→{gB} (sobrevivem {gAB});"
      f" perna sup morre em {kill_sup} · perna dem morre em {kill_dem}")
