#!/usr/bin/env python3
"""A2 GT GATE — avaliação de REGIÕES, não trades (spec A2 §9, v1.1). Leitura dinâmica/trajetória.
PASSO 1 (dente automático): seleção r_cycle ∈ {4,6,8} vs PLT/DM (matcher verbatim F1.5: extremo da
região ↔ marca, |Δpx|≤0,7·ATR, |Δt|≤2d, greedy 1:1). Fasquia ≥9/10 PLT e ≥10/11 DM; empate → r=6.
3 looks, ledgered. SEM contingência (0/3 = BLOCKED, sem expansão).
PASSO 2: FREEZE do r escolhido.
PASSO 3 (REPORT-PARA-DECISÃO-DO-CRIS, sem dente automático — ordem explícita dele): leitura ÚNICA
dos 42 VELA DE FUNDO + 50 círculos + 4 INVALIDO. Cobertura CAUSAL no instante da marca por DOIS
canais separados: (a) região-FUNDO ativa; (b) região-TOPO convertida (converted_support) ativa.
Banda EXATA (primário) + near-miss ≤0,7·ATR além da borda (reportado à parte). Região da MESMA queda
(known_at > t_marca) = late/reconstrução, não conta. Marca em warmup = UNSCORABLE. Precision/FP/
traps/latency/retested→invalidated. GT usado SÓ aqui (avaliação)."""
import json, csv, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f0_raw_loader import load_cached
from f1_structural_leg_machine import Data, W_WARMUP
from a2_anchor_region_ledger import build_regions, summarize
from f15_pltdm_gate import gt_pltdm, match, GT_CATALOG, LEDGER

def dsu(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")

def timeline(regions, events):
    """por região: converted_at / invalidated_at (known_at dos eventos)."""
    tl = {x["region_id"]: {"converted_at": None, "invalidated_at": None} for x in regions}
    for e in events:
        if e["event"] == "converted_support": tl[e["region_id"]]["converted_at"] = e["known_at"]
        elif e["event"] == "invalidated": tl[e["region_id"]]["invalidated_at"] = e["known_at"]
    return tl

def coverage(marks, regions, tl, D, warm_end):
    """cobertura causal por canal no instante da marca; devolve (rows, agg)."""
    rows = []
    bt = [x for x in regions if x["kind"] == "BOTTOM"]
    tp = [x for x in regions if x["kind"] == "TOP"]
    for m in marks:
        mt, mp = m["t"], m["price"]
        if mt <= warm_end:
            rows.append({"date": m.get("date", dsu(mt)), "verdict": "UNSCORABLE_WARMUP"}); continue
        a = D.ATR[bisect.bisect_right(D.TS, mt)-1] or 5
        best = None
        for x in bt:
            inv = tl[x["region_id"]]["invalidated_at"]
            if x["known_at"] < mt and (inv is None or inv > mt):
                if x["price_low"] <= mp <= x["price_high"]:
                    cand = ("bottom_active", x, 0.0)
                else:
                    gap = max(x["price_low"]-mp, mp-x["price_high"])/a
                    cand = ("bottom_near", x, gap) if gap <= 0.7 else None
                if cand and (best is None or cand[2] < best[2] or
                             (cand[0] == "bottom_active" and best[0] != "bottom_active")):
                    if cand[0] == "bottom_active" or best is None or best[0].endswith("near"):
                        best = cand
        conv_hit = None
        for x in tp:
            ca = tl[x["region_id"]]["converted_at"]; inv = tl[x["region_id"]]["invalidated_at"]
            if ca is not None and ca < mt and (inv is None or inv > mt):
                if x["price_low"] <= mp <= x["price_high"]:
                    conv_hit = conv_hit or ("converted_support", x, 0.0)
                elif conv_hit is None:
                    gap = max(x["price_low"]-mp, mp-x["price_high"])/a
                    if gap <= 0.7: conv_hit = ("converted_near", x, gap)
        # late/reconstrução: região-fundo da MESMA queda (known_at > mt, extremo perto da marca)
        late = any(x["known_at"] > mt and abs(x["extreme_t"]-mt) <= 8*3600 and
                   abs(x["extreme_px"]-mp) <= 1.0*a for x in bt)
        v = {"date": m.get("date", dsu(mt)), "px": round(mp, 1),
             "bottom": best[0] if best else None,
             "bottom_region": best[1]["region_id"] if best else None,
             "bottom_age_h": round((mt-best[1]["known_at"])/3600, 1) if best else None,
             "converted": conv_hit[0] if conv_hit else None,
             "converted_region": conv_hit[1]["region_id"] if conv_hit else None,
             "late_reconstruction": late,
             "verdict": ("COVERED_BOTTOM" if best and best[0] == "bottom_active" else
                         "COVERED_CONVERTED" if conv_hit and conv_hit[0] == "converted_support" else
                         "NEAR_MISS" if (best or conv_hit) else
                         "LATE_ONLY" if late else "MISS")}
        rows.append(v)
    n_sc = [r for r in rows if r["verdict"] != "UNSCORABLE_WARMUP"]
    agg = {"n": len(rows), "scorable": len(n_sc),
           "covered_bottom": sum(1 for r in n_sc if r["verdict"] == "COVERED_BOTTOM"),
           "covered_converted": sum(1 for r in n_sc if r["verdict"] == "COVERED_CONVERTED"),
           "covered_any": sum(1 for r in n_sc if r["verdict"].startswith("COVERED")),
           "near_miss": sum(1 for r in n_sc if r["verdict"] == "NEAR_MISS"),
           "late_only": sum(1 for r in n_sc if r["verdict"] == "LATE_ONLY"),
           "miss": sum(1 for r in n_sc if r["verdict"] == "MISS")}
    return rows, agg

def main():
    bars, ts = load_cached()
    D = Data(bars, ts)
    PLT, DM = gt_pltdm()
    WIN = (min(t for t, _ in PLT)-2*86400, max(t for t, _ in DM)+2*86400)
    warm_end = D.TS[W_WARMUP]
    led = []
    # -------- PASSO 1: seleção r vs PLT/DM (3 looks) --------
    built = {}; sel = []
    for r in (4, 6, 8):
        regions, events = build_regions(D, r)
        built[r] = (regions, events)
        tops = [(x["extreme_t"], x["extreme_px"]) for x in regions
                if x["kind"] == "TOP" and WIN[0] <= x["extreme_t"] <= WIN[1]]
        bots = [(x["extreme_t"], x["extreme_px"]) for x in regions
                if x["kind"] == "BOTTOM" and WIN[0] <= x["extreme_t"] <= WIN[1]]
        hp, dp = match(PLT, tops, D)
        hd, dd_ = match(DM, bots, D)
        sel.append({"r": r, "PLT": hp, "DM": hd, "passes": hp >= 9 and hd >= 10,
                    "n_top_win": len(tops), "n_bot_win": len(bots),
                    "miss_plt": [m["mark"] for m in dp if not m["hit"]],
                    "miss_dm": [m["mark"] for m in dd_ if not m["hit"]]})
        led.append(["A2_S1_r%d" % r, f"{hp}/10+{hd}/11", "PLT/DM recall A2 (extremos de região)",
                    "a2_anchor_gt_gate.py", "results/f0_bars_cache.jsonl",
                    "a2_anchor_gt_gate_result.json", "RAW 9x .jsonl.gz via f0 (manifest)",
                    "VERIFIED_DERIVED", "EXPLORATORY", "look passo-1"])
    passers = [s for s in sel if s["passes"]]
    if passers:
        chosen = 6 if any(s["r"] == 6 for s in passers) else min(passers, key=lambda s: abs(s["r"]-6))["r"]
        gate1 = "PASS"
    else:
        chosen = max(sel, key=lambda s: s["PLT"]+s["DM"])["r"]   # só para reporte de falhas
        gate1 = "BLOCKED_A2_GT_GATE"
    out = {"step1": sel, "step1_gate": gate1, "r_frozen": chosen if gate1 == "PASS" else None,
           "baseline_f15": "PLT 6/10 · DM 4/11"}
    # -------- PASSO 3: leitura única (mesmo se BLOCKED, reporte de falhas usa o melhor r, declarado) --------
    regions, events = built[chosen]
    tl = timeline(regions, events)
    cat = json.load(open(GT_CATALOG))
    fundos = cat["notes"]["FUNDO"]; circ = cat["circles"]; inval = cat["notes"]["INVALIDO"]
    rows_f, agg_f = coverage(fundos, regions, tl, D, warm_end)
    rows_c, agg_c = coverage([{"t": c["t"], "price": c["price"], "date": c["date"]} for c in circ],
                             regions, tl, D, warm_end)
    rows_i, agg_i = coverage(inval, regions, tl, D, warm_end)
    # famílias (contexto da região que cobriu; para misses, macro na marca)
    fam = {}
    for r0 in rows_f:
        if r0["verdict"].startswith("COVERED") and r0.get("bottom_region"):
            ctx = next(x["context"] for x in regions if x["region_id"] == r0["bottom_region"])
        else:
            ctx = "MACRO_" + D.macro_at([f for f in fundos if f.get("date") == r0["date"]][0]["t"]) \
                  if r0["verdict"] != "UNSCORABLE_WARMUP" else "WARMUP"
        fam.setdefault(ctx, {"covered": 0, "total": 0})
        fam[ctx]["total"] += 1
        if r0["verdict"].startswith("COVERED"): fam[ctx]["covered"] += 1
    # precision / FP (r escolhido, vida da região, GT = 42∪50)
    allgt = [(f["t"], f["price"]) for f in fundos] + [(c["t"], c["price"]) for c in circ]
    bt = [x for x in regions if x["kind"] == "BOTTOM"]
    touched = 0
    for x in bt:
        inv_t = tl[x["region_id"]]["invalidated_at"] or D.TS[-1]+900
        if any(x["known_at"] <= gt_t <= inv_t and x["price_low"] <= gp <= x["price_high"]
               for gt_t, gp in allgt):
            touched += 1
    weeks = (D.TS[-1]-warm_end)/(7*86400); days = (D.TS[-1]-warm_end)/86400
    summ = summarize(regions, events, D, chosen)
    out.update({
        "step3_note": "REPORT-PARA-DECISÃO-DO-CRIS (sem dente automático); leitura ÚNICA por ordem explícita; consome os 13 BULL-2026 antes reservados (região-nível)",
        "fundos_42": {"agg": agg_f, "per_family": fam, "rows": rows_f},
        "circles_50": {"agg": agg_c},
        "invalido_4": {"agg": agg_i, "rows": rows_i,
                       "rejected": sum(1 for r0 in rows_i if r0["verdict"] in ("MISS", "LATE_ONLY"))},
        "precision_fp": {"n_bottom_regions": len(bt), "gt_touched": touched,
                         "precision_gt": round(touched/len(bt), 3) if bt else None,
                         "bottoms_per_week": round(len(bt)/weeks, 2),
                         "fp_regions_per_day": round((len(bt)-touched)/days, 2),
                         "top_buy_traps_pos96": summ["top_buy_traps_pos96"],
                         "retested_then_invalidated_by_context": summ["retested_then_invalidated_by_context"]},
        "latency": {"p50_p90_bars": summ["latency_bars_p50_p90"]},
    })
    led.append(["A2_S3_F42", f"{agg_f['covered_any']}/{agg_f['scorable']}", "cobertura causal 42 FUNDO (leitura única)",
                "a2_anchor_gt_gate.py", "results/f0_bars_cache.jsonl", "a2_anchor_gt_gate_result.json",
                "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "REVIEW_LAYER",
                f"bottom {agg_f['covered_bottom']} + converted {agg_f['covered_converted']}"])
    led.append(["A2_S3_C50", f"{agg_c['covered_any']}/{agg_c['scorable']}", "cobertura causal 50 círculos",
                "a2_anchor_gt_gate.py", "results/f0_bars_cache.jsonl", "a2_anchor_gt_gate_result.json",
                "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "REVIEW_LAYER", ""])
    led.append(["A2_S3_INV", f"{out['invalido_4']['rejected']}/4", "INVALIDO rejeitados (sem região ativa)",
                "a2_anchor_gt_gate.py", "results/f0_bars_cache.jsonl", "a2_anchor_gt_gate_result.json",
                "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "REVIEW_LAYER", ""])
    (HERE/"results/a2_anchor_gt_gate_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with open(LEDGER, "a", newline="") as fh:
        w = csv.writer(fh)
        for row in led: w.writerow(row)
    slim_out = {k: v for k, v in out.items() if k not in ("fundos_42",)}
    slim_out["fundos_42_agg"] = agg_f; slim_out["fundos_42_per_family"] = fam
    print(json.dumps(slim_out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
