#!/usr/bin/env python3
"""LAYER 2 — IMPULSO-VIVO v3: correções de cálculo prescritas pelo DA (2026-07-05).
(i) reclaim gated a closes <= cj (range fi..fi+3; v2 vazava 5 barras);
(ii) CONTEXTO PRÉ-PERNA: tokens medidos na janela que termina no HIGH de origem do dip
    (argmax high [i-96..i]) — a perna do dip imprime tokens bear e contaminava n_bull no cj
    (matriz DA: 66% dos fundos BULL do Cris reprovavam por isso);
(iii) recall estrito; painel completo; decomposição contexto/gatilho causal.
BULL-VIVO v3: n_bull_preleg>=5/8 & cd_preleg<=1 & sweep&reclaim-união CAUSAL & demanda & reclaim>=1."""
import json, bisect, hashlib, glob, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISS_BULL = [(r["ft"], r["flo"]) for r in gap["missed_rows"] if r["reg"] == "BULL"]

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

def sweep_causal(u):
    """níveis união; reclaim por close APENAS até cj (fi..fi+3)."""
    ft = u["t"]; flo = u["g_sl"] + 0.1 * u["g_atr"]
    i = bisect.bisect_right(TS, ft) - 1
    lv = {"EQL": last_tok_price(ft, "EQL", 48), "BOS+": last_tok_price(ft, "BOS+", 96),
          "CHoCH+": last_tok_price(ft, "CHoCH+", 96)}
    j = bisect.bisect_left(UTT, ft) - 1
    lv["FRACLOW"] = (USORT[j]["g_sl"] + 0.1 * USORT[j]["g_atr"]) if j >= 0 and ft - USORT[j]["t"] <= 96 * 3600 else None
    lv["SWING24"] = min(S[k]["l"] for k in range(i - 96, i - 24)) if i >= 96 else None
    for k, l in lv.items():
        if l is None or not (flo < l):
            continue
        if any(S[m]["c"] > l for m in range(i, min(len(S), i + 4))):
            return k
    return None

def preleg_ctx(u):
    """tokens na janela [hi_k−96h .. hi_k] onde hi_k = high de origem do dip (argmax [i-96..i])."""
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    if i < 96:
        return None
    hi_k = max(range(i - 96, i + 1), key=lambda k: S[k]["h"])
    t_hi = S[hi_k]["t"]
    t0 = t_hi - 384 * 900
    hi = bisect.bisect_right(ET2, t_hi)
    dirs = [EV2[m] for m in range(hi) if EV2[m]["t"] >= t0 and EV2[m]["tok"][-1] in "+-"]
    last8 = dirs[-8:]
    n_bull = sum(1 for e in last8 if e["tok"].endswith("+"))
    cd = 0
    for e in reversed(dirs):
        if e["tok"] in ("BOS-", "CHoCH-"):
            cd += 1
        else:
            break
    return {"n_bull": n_bull, "n8": len(last8), "cd": cd}

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

def dem_ok(u):
    return fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5

ELIG = []
for u in U:
    if u["cj_t"] not in R3 or is_cascex_member(u):
        continue
    pc = preleg_ctx(u)
    if pc is None:
        continue
    u["_pc"] = pc
    ELIG.append(u)
WEEKS = len({u["g_week"] for u in U})
uni_hit = sum(1 for u in ELIG if R3[u["cj_t"]]["R3"] >= 3) / len(ELIG)

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
        print(f"  {tag:<40} vazio"); return None
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(nets); eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"  {tag:<40} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | recallESTRITO {strict_recall(rows, gtlist)}/{len(gtlist)} | {yr}")
    return {"n": n, "hit": round(h / n, 3), "sum": round(s, 1), "dd": round(dd, 1), "stk": mL,
            "recall": strict_recall(rows, gtlist)}

print(f"elegíveis: N{len(ELIG)} · hit universo {100*uni_hit:.1f}%")
CTX = [u for u in ELIG if u["_pc"]["n8"] >= 6 and u["_pc"]["n_bull"] >= 5 and u["_pc"]["cd"] <= 1]
CONF = [u for u in CTX if dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0]
for u in CONF:
    u["_swt"] = sweep_causal(u)
FULL = [u for u in CONF if u["_swt"]]
print("\nDECOMPOSIÇÃO v3 (tudo causal):")
full_panel(CTX, "contexto pré-perna só", MISS_BULL)
full_panel(CONF, "contexto + confluência (dem+recl)", MISS_BULL)
p = full_panel(FULL, "BULL-VIVO v3 completo (+sweep causal)", MISS_BULL)
json.dump({"v3": p}, open(HERE / "results" / "layer2_impulso_vivo_v3_20260705.json", "w"), indent=1, default=str)
print("OK → results/layer2_impulso_vivo_v3_20260705.json")
