#!/usr/bin/env python3
"""LAYER 2 — IMPULSO-VIVO v2: sweep&reclaim de QUALQUER nível estrutural (2026-07-05).
Diagnóstico selou: união dos 5 níveis (FRACLOW/BOS+/CHoCH+/SWING24/EQL) cobre 52/56 fundos GT;
nenhum tipo domina. v2 = contexto estrutural (o discriminador) + gatilho de união:
  BULL-VIVO: >=5/8 tokens bull & cascade_down<=1 & sweep&reclaim(união) & demanda & reclaim>=1,0
  RANGE-FUNDO: cd<=2 & cu<=2 & box480<=0,35 & sweep&reclaim(união) & demanda & reclaim>=1,0
Ex-CASCEX. Recall ESTRITO. Painel completo. Lentes declaradas (FDR): casc_up>=2 · rsi1h<=55 ·
bolha_buy · nível=FRACLOW · nível=BOS+."""
import json, bisect, hashlib, glob, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED = gap["missed_rows"]
MISS_BULL = [(r["ft"], r["flo"]) for r in MISSED if r["reg"] == "BULL"]
MISS_RANGE = [(r["ft"], r["flo"]) for r in MISSED if r["reg"] not in ("BULL", "BEAR")]

EV2 = []
seen2 = set()
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for e in json.load(open(p))["smc_events"]:
        key = (e["t"], e["text"], round(e["price"], 2))
        if key in seen2:
            continue
        seen2.add(key)
        c = close_at(e["t"])
        if c is None:
            continue
        tok = e["text"] + (("+" if c > e["price"] else "-") if e["text"] in ("BOS", "CHoCH") else "")
        EV2.append({"t": e["t"], "tok": tok, "price": e["price"]})
EV2.sort(key=lambda x: x["t"]); ET2 = [e["t"] for e in EV2]
USORT = sorted(U, key=lambda u: u["t"]); UTT = [u["t"] for u in USORT]

def last_tok_price(ft, tok, hours):
    hi = bisect.bisect_right(ET2, ft)
    for i in range(hi - 1, -1, -1):
        if EV2[i]["t"] < ft - hours * 3600:
            break
        if EV2[i]["tok"] == tok:
            return EV2[i]["price"]
    return None

def levels_of(u):
    ft = u["t"]
    out = {"EQL": last_tok_price(ft, "EQL", 48), "BOS+": last_tok_price(ft, "BOS+", 96),
           "CHoCH+": last_tok_price(ft, "CHoCH+", 96)}
    j = bisect.bisect_left(UTT, ft) - 1
    out["FRACLOW"] = (USORT[j]["g_sl"] + 0.1 * USORT[j]["g_atr"]) if j >= 0 and ft - USORT[j]["t"] <= 96 * 3600 else None
    i = bisect.bisect_right(TS, ft) - 1
    out["SWING24"] = min(S[k]["l"] for k in range(i - 96, i - 24)) if i >= 96 else None
    return out

def sweep_types(u):
    flo = u["g_sl"] + 0.1 * u["g_atr"]
    i = bisect.bisect_right(TS, u["t"]) - 1
    types = []
    for k, lvl in levels_of(u).items():
        if lvl is None or not (flo < lvl):
            continue
        if any(S[m]["c"] > lvl for m in range(i, min(len(S), i + 9))):
            types.append(k)
    return types

def struct_ctx(cj):
    t0 = cj - 384 * 900
    hi = bisect.bisect_right(ET2, cj)
    dirs = [EV2[i] for i in range(hi) if EV2[i]["t"] >= t0 and EV2[i]["tok"][-1] in "+-"]
    last8 = dirs[-8:]
    n_bull = sum(1 for e in last8 if e["tok"].endswith("+"))
    cd = cu = 0
    for e in reversed(dirs):
        if e["tok"] in ("BOS-", "CHoCH-"):
            cd += 1
        else:
            break
    for e in reversed(dirs):
        if e["tok"] in ("BOS+", "CHoCH+"):
            cu += 1
        else:
            break
    return {"n_bull": n_bull, "n8": len(last8), "cd": cd, "cu": cu}

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

CANDS = []
for u in U:
    if u["cj_t"] not in R3 or is_cascex_member(u):
        continue
    u["_sw"] = sweep_types(u)
    if not u["_sw"]:
        continue
    u["_sc"] = struct_ctx(u["cj_t"])
    CANDS.append(u)
WEEKS = len({u["g_week"] for u in U})

def dem_ok(u):
    return fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5

def strict_recall(rows, gtlist):
    got = 0
    ts = sorted((u["cj_t"], u["g_sl"] + 0.1 * u["g_atr"], u.get("g_atr") or 5.0) for u in rows)
    T = [x[0] for x in ts]
    for ft, flo in gtlist:
        j = bisect.bisect_left(T, ft - 8 * 3600); ok = False
        while j < len(T) and T[j] <= ft + 8 * 3600:
            if abs(ts[j][1] - flo) <= ts[j][2]:
                ok = True; break
            j += 1
        got += ok
    return got

def full_panel(rows, tag, gtlist):
    if not rows:
        print(f"  {tag:<36} vazio"); return None
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(nets); eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"  {tag:<36} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | recallESTRITO {strict_recall(rows, gtlist)}/{len(gtlist)} | {yr}")
    return {"n": n, "hit": round(h / n, 3), "sum": round(s, 1), "stk": mL,
            "recall": strict_recall(rows, gtlist)}

print(f"candidatos com sweep&reclaim(união), ex-CASCEX: N{len(CANDS)} · "
      f"hit {100*sum(1 for u in CANDS if R3[u['cj_t']]['R3']>=3)/len(CANDS):.1f}%")
BULLV = [u for u in CANDS if u["_sc"]["n8"] >= 6 and u["_sc"]["n_bull"] >= 5 and u["_sc"]["cd"] <= 1
         and dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0]
RANGEV = [u for u in CANDS if u["_sc"]["cd"] <= 2 and u["_sc"]["cu"] <= 2
          and fv(u, "g_box480", 9) <= 0.35 and dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0]
print("\nBASES v2 (união de níveis):")
pb = full_panel(BULLV, "BULL-VIVO v2", MISS_BULL)
pr = full_panel(RANGEV, "RANGE-FUNDO v2", MISS_RANGE)
LENS = {
    "casc_up>=2": lambda u: u["_sc"]["cu"] >= 2,
    "rsi1h<=55": lambda u: fv(u, "h1_rsi", 99) <= 55,
    "bolha_buy": lambda u: fv(u, "buy_bub_w", 0) >= 1,
    "nivel_FRACLOW": lambda u: "FRACLOW" in u["_sw"],
    "nivel_BOS+": lambda u: "BOS+" in u["_sw"],
}
for basename, BASEX, gl in (("BULL-VIVO v2", BULLV, MISS_BULL), ("RANGE-FUNDO v2", RANGEV, MISS_RANGE)):
    if len(BASEX) < 50:
        continue
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASEX]
    random.seed(37)
    print(f"\n  lentes sobre {basename}:")
    for nm, fn in LENS.items():
        g = [u for u in BASEX if fn(u)]
        if len(g) < 25:
            continue
        hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
        obs = sum(hs) / len(hs)
        ge = sum(1 for _ in range(2000) if sum(random.sample(H0, len(g))) / len(g) >= obs)
        nets = sum(R3[u["cj_t"]]["net3"] for u in g)
        print(f"    {nm:<16} N{len(g):>4} hit {100*obs:>5.1f}% NET {nets:>+7.1f} "
              f"recall {strict_recall(g, gl)}/{len(gl)} P {ge/2000:.4f}")
json.dump({"bull": pb, "range": pr}, open(HERE / "results" / "layer2_impulso_vivo_v2_20260705.json", "w"),
          indent=1, default=str)
print("OK → results/layer2_impulso_vivo_v2_20260705.json")
