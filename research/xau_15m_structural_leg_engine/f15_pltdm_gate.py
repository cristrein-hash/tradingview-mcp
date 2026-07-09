#!/usr/bin/env python3
"""F1.5 — PLT/DM GATE (spec v1.2 §8; manifest stage1_preregistered + mining_null_f15).
Leitura DINÂMICA de trajetória (caminhada de pernas multi-fatorial), não snapshot de eixo único.

ESTÁGIO 1 (GT-free, janela pré-holdout 2024-05-25→2025-12-31): grid pré-registado 162 configs
{M×K_up×K_down×D_flush×mom}; bounds congelados: pernas/mês ∈[2,20] · duração mediana ∈[8h,120h] ·
% tempo por leg_dir ∈[5%,85%] · LEG_FLAT ≤70%. Sobreviventes ordenados por nº de desvios do seed,
desempate lexicográfico. AMENDMENT A1 (declarado, ledgered): se 0 sobreviventes E o diagnóstico
override-OFF for plausível => sub-grid {M×K_up×K_down} com override DESLIGADO segue ao estágio 2;
o redesenho do D_flush (defeito de transposição de escala, previsto pelo DA ataque B) vai ao Cris.

ESTÁGIO 2: top≤20 → matcher PLT/DM (±0.7 ATR, ±2d, greedy 1:1 — verbatim leg_walk_reproduce):
candidatos = topos (leg_top) e fundos (leg_bottom) de pernas FECHADAS na janela do Cris.
Gate: ≥9/10 PLT e ≥10/11 DM. Config final = 1º que passa na ordem determinística.
Mining-null (gate P≤0.05): 200 trials, offset comum ±3-10d (cluster-aware), recall do config final.
Sensibilidade: matcher apertado ±0.5d. FP/dia + precision na janela. Pós-freeze REPORT-ONLY:
proximidade aos VELA DE FUNDO pré-2026 (calibração) + estado nos 4 INVALIDO. HOLDOUT 2026 NÃO tocado.
Todos os looks → claims_ledger.csv. Sem eventos, sem entry, sem backtest."""
import json, csv, sys, random, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f1_structural_leg_machine import Data, walk, SEED_CFG, W_WARMUP

RES = HERE/"results"; REP = HERE/"reports"; REP.mkdir(exist_ok=True)
LEDGER = HERE/"claims_ledger.csv"
GT_SHAPES = HERE.parents[0]/"xau_15m_bb_nas_leonardo/results/manual_shapes_pltdm_20260707.json"
GT_CATALOG = HERE.parents[0]/"xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
PREHOLD_END = int(dt.datetime(2026, 1, 1).timestamp())
GRID = {"M": [12, 15, 24], "K_up": [4, 5, 6], "K_down": [3, 5],
        "D_flush": [1.5, 2.0, 2.5], "mom": [16, 24, 32]}
BOUNDS = {"legs_per_month": (2, 20), "dur_med_h": (8, 120), "dir_pct": (5, 85), "flat_max": 70}

def dsu(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")

def gt_pltdm():
    rows = json.load(open(GT_SHAPES))
    def gp(r):
        pts = r.get("points") or []
        return (int(pts[0]["time"]), pts[0]["price"]) if pts and pts[0].get("time") else None
    PLT = sorted([gp(r) for r in rows if r["name"] == "text_note" and r["text"].strip().upper() == "PLT" and gp(r)])
    DM = sorted([gp(r) for r in rows if r["name"] == "text_note" and r["text"].strip().upper() == "DM" and gp(r)])
    return PLT, DM

def stage1_metrics(D, cfg, t_end):
    i_end = bisect.bisect_right(D.TS, t_end)
    states, legs, _ = walk(D, cfg, i_end=i_end)
    states = [s for s in states if not s["warmup"]]
    n = len(states)
    months = (D.TS[i_end-1]-D.TS[W_WARMUP])/(30*86400)
    occ = {}
    for s in states: occ[s["leg_dir"]] = occ.get(s["leg_dir"], 0)+1
    pct = {k: 100*v/n for k, v in occ.items()}
    durs = sorted(l["dur_bars"] for l in legs)
    return {"legs_per_month": len(legs)/months if months > 0 else 0,
            "dur_med_h": durs[len(durs)//2]*0.25 if durs else 0,
            "pct_up": pct.get("LEG_UP", 0), "pct_down": pct.get("LEG_DOWN", 0),
            "pct_flat": pct.get("LEG_FLAT", 0), "n_legs": len(legs)}

def plausible(m):
    lo, hi = BOUNDS["legs_per_month"]
    if not (lo <= m["legs_per_month"] <= hi): return False
    lo, hi = BOUNDS["dur_med_h"]
    if not (lo <= m["dur_med_h"] <= hi): return False
    lo, hi = BOUNDS["dir_pct"]
    for k in ("pct_up", "pct_down", "pct_flat"):
        if not (lo <= m[k] <= hi if k != "pct_flat" else m[k] <= BOUNDS["flat_max"]): return False
    return True

def dev_from_seed(cfg):
    return sum(1 for k in SEED_CFG if cfg.get(k) != SEED_CFG[k])

def match(marks, cands, D, t_tol=2*86400):
    """matcher verbatim: ±0.7 ATR15, ±t_tol, greedy 1:1 por proximidade temporal."""
    hits = 0; used = set(); detail = []
    for mt, mp in marks:
        a = D.ATR[bisect.bisect_right(D.TS, mt)-1] or 5
        cand = [(abs(ct-mt), k) for k, (ct, cp) in enumerate(cands)
                if abs(cp-mp) <= 0.7*a and abs(ct-mt) <= t_tol and k not in used]
        if cand:
            cand.sort(); used.add(cand[0][1]); hits += 1
            detail.append({"mark": dsu(mt), "px": round(mp, 1), "hit": True, "dt_h": round(cand[0][0]/3600, 1)})
        else:
            detail.append({"mark": dsu(mt), "px": round(mp, 1), "hit": False})
    return hits, detail

def leg_candidates(legs, win):
    tops = [(l["top_t"], l["top_px"]) for l in legs if win[0] <= l["top_t"] <= win[1]]
    bots = [(l["bot_t"], l["bot_px"]) for l in legs if win[0] <= l["bot_t"] <= win[1]]
    return tops, bots

def main():
    D = Data()
    PLT, DM = gt_pltdm()
    WIN = (min(t for t, _ in PLT)-2*86400, max(t for t, _ in DM)+2*86400)
    ledger = []
    def led(claim, number, metric, out, status, note=""):
        ledger.append({"claim_id": claim, "number": number, "metric": metric,
                       "script": "f15_pltdm_gate.py", "input_file": "results/f0_bars_cache.jsonl",
                       "output_file": out, "source_ref": "RAW 9x .jsonl.gz via f0 (manifest)",
                       "raw_or_derived": "VERIFIED_DERIVED", "status": status, "note": note})
    # -------- ESTÁGIO 1: grid pré-registado --------
    combos = [{"M": M, "K_up": ku, "K_down": kd, "D_flush": df, "mom": mo}
              for M in GRID["M"] for ku in GRID["K_up"] for kd in GRID["K_down"]
              for df in GRID["D_flush"] for mo in GRID["mom"]]
    s1 = []
    for cfg in combos:
        m = stage1_metrics(D, cfg, PREHOLD_END)
        ok = plausible(m)
        s1.append({"cfg": cfg, "metrics": {k: round(v, 2) for k, v in m.items()}, "plausible": ok})
    surv = [r for r in s1 if r["plausible"]]
    led("S1_GRID", len(combos), "configs estágio-1 (pré-registado)", "f15_pltdm_gate_result.json", "EXPLORATORY",
        f"sobreviventes={len(surv)}")
    amendment = None
    if not surv:
        # -------- AMENDMENT A1 (declarado): defeito de transposição do D_flush --------
        # diagnóstico GT-free: sub-grid M×K_up×K_down com override OFF (D_flush=None)
        sub = [{"M": M, "K_up": ku, "K_down": kd, "D_flush": float("inf"), "mom": 24}
               for M in GRID["M"] for ku in GRID["K_up"] for kd in GRID["K_down"]]
        s1b = []
        for cfg in sub:
            m = stage1_metrics(D, cfg, PREHOLD_END)
            s1b.append({"cfg": cfg, "metrics": {k: round(v, 2) for k, v in m.items()}, "plausible": plausible(m)})
        surv = [r for r in s1b if r["plausible"]]
        amendment = {"id": "A1", "reason": "grid pré-registado 162/162 IMPLAUSÍVEL: D_flush em ATR15 sobre running-peak "
                     "dispara em pullback normal (2 ATR15 ≈ 0.25%% vs 6%% do v5) e satura LEG_DOWN — defeito da CLASSE "
                     "apontada pelo critical review R1 / DA-da-auditoria ataque 6 (thresholds não transferem entre escalas; "
                     "o defeito exato ATR15-vs-%% não tinha sido previsto por ninguém). Sub-grid com override OFF segue ao "
                     "estágio 2; redesenho do flush override = DECISÃO DO CRIS (F2).",
                     "subgrid": len(sub), "survivors": len(surv), "stage1b": s1b}
        led("S1_A1", len(sub), "configs A1 override-OFF", "f15_pltdm_gate_result.json", "EXPLORATORY",
            f"sobreviventes={len(surv)}")
    surv.sort(key=lambda r: (dev_from_seed(r["cfg"]), json.dumps(r["cfg"], sort_keys=True)))
    top = surv[:20]
    # -------- ESTÁGIO 2: PLT/DM gate --------
    results2 = []; final = None
    for r in top:
        cfg = r["cfg"]
        _, legs, _ = walk(D, cfg)
        tops, bots = leg_candidates(legs, WIN)
        hp, dp = match(PLT, tops, D)
        hd, dd_ = match(DM, bots, D)
        days = (WIN[1]-WIN[0])/86400
        n_cand = len(tops)+len(bots)
        fp = n_cand - hp - hd
        row = {"cfg": cfg, "PLT": f"{hp}/10", "DM": f"{hd}/11",
               "n_cand_window": n_cand, "fp_per_day": round(fp/days, 2),
               "precision": round((hp+hd)/n_cand, 3) if n_cand else 0.0,
               "passes": hp >= 9 and hd >= 10, "detail_plt": dp, "detail_dm": dd_}
        results2.append(row)
        led(f"S2_{len(results2)}", f"{hp}/10+{hd}/11", "PLT/DM recall", "f15_pltdm_gate_result.json",
            "EXPLORATORY", json.dumps(cfg))
        if row["passes"] and final is None:
            final = row
    out = {"window": [dsu(WIN[0]), dsu(WIN[1])], "n_PLT": len(PLT), "n_DM": len(DM),
           "stage1": {"n_grid": len(combos), "n_survivors_pregrid": len([r for r in s1 if r['plausible']]),
                      "sample_degenerate": s1[0]},
           "amendment": ({k: v for k, v in amendment.items() if k != "stage1b"} if amendment else None),
           "stage1b_survivors": ([{"cfg": r["cfg"], "metrics": r["metrics"]} for r in surv] if amendment else None),
           "stage2": [{k: v for k, v in r.items() if not k.startswith("detail")} for r in results2],
           "final": None}
    if final:
        cfg = final["cfg"]
        # mining-null (gate P<=0.05): offset comum cluster-aware ±3-10d, 200 trials
        _, legs, _ = walk(D, cfg)
        tops, bots = leg_candidates(legs, (WIN[0]-15*86400, WIN[1]+15*86400))
        rng = random.Random(20260709)
        obs = int(final["PLT"].split("/")[0]) + int(final["DM"].split("/")[0])
        cnt = 0; TRI = 200
        for _ in range(TRI):
            off = rng.choice([-1, 1]) * rng.randint(3*86400, 10*86400)
            hp, _ = match([(t+off, p) for t, p in PLT], tops, D)
            hd, _ = match([(t+off, p) for t, p in DM], bots, D)
            if hp+hd >= obs: cnt += 1
        pnull = cnt/TRI
        # sensibilidade matcher apertado ±0.5d
        tops_w, bots_w = leg_candidates(legs, WIN)
        hp5, _ = match(PLT, tops_w, D, t_tol=int(0.5*86400))
        hd5, _ = match(DM, bots_w, D, t_tol=int(0.5*86400))
        out["final"] = {**{k: v for k, v in final.items() if not k.startswith("detail")},
                        "mining_null_P": pnull, "mining_null_pass": pnull <= 0.05,
                        "tight_matcher_0.5d": f"PLT {hp5}/10 · DM {hd5}/11",
                        "misses_PLT": [m for m in final["detail_plt"] if not m["hit"]],
                        "misses_DM": [m for m in final["detail_dm"] if not m["hit"]]}
        led("NULL_F15", pnull, "mining-null P (gate<=0.05)", "f15_pltdm_gate_result.json",
            "VERIFIED_DERIVED", json.dumps(cfg))
        # -------- pós-freeze REPORT-ONLY (sem iteração; holdout 2026 NÃO tocado) --------
        cat = json.load(open(GT_CATALOG))
        fundos25 = [x for x in cat["notes"]["FUNDO"] if x["date"] < "2026-01-01"]
        states, legs_all, _ = walk(D, cfg)
        bots_all = [(l["bot_t"], l["bot_px"]) for l in legs_all]
        # proximidade matcher v2 assimétrico: |dt|<=8h e -3ATR <= (bot - low_GT) <= +1ATR
        hits25 = 0; miss25 = []
        for x in fundos25:
            mt, mp = x["t"], x["price"]
            a = D.ATR[bisect.bisect_right(D.TS, mt)-1] or 5
            ok = any(abs(ct-mt) <= 8*3600 and -3*a <= (cp-mp) <= 1*a for ct, cp in bots_all)
            hits25 += ok
            if not ok: miss25.append(x["date"])
        tmap = {t: i for i, t in enumerate(D.TS)}
        inval = []
        for x in cat["notes"]["INVALIDO"]:
            i = bisect.bisect_right(D.TS, x["t"])-1
            s = states[i]
            inval.append({"date": x["date"], "leg_dir": s["leg_dir"], "leg_phase": s["leg_phase"],
                          "macro": s["macro"], "is_reject_state": s["leg_dir"] == "LEG_DOWN" and s["leg_phase"] in ("ACTIVE", "SHALLOW_BOUNCE")})
        out["post_freeze_report_only"] = {
            "fundos_pre2026_proximity": f"{hits25}/{len(fundos25)}", "misses": miss25,
            "note_fundos": "REPORT-ONLY informativo (leg bottoms fechados vs matcher v2); avaliação de EVENTOS = F2/F3; holdout 2026 NÃO tocado",
            "invalido_states": inval,
            "note_invalido": "REPORT-ONLY pós-freeze (marcas 2026, firewall C7 respeitado: zero iteração)"}
        led("RPT_F25", f"{hits25}/{len(fundos25)}", "proximidade fundos pré-2026 (informativo)",
            "f15_pltdm_gate_result.json", "REVIEW_LAYER")
        out["gate"] = "PASS" if (final["passes"] and pnull <= 0.05) else "BLOCKED_F15_GATE"
    else:
        out["gate"] = "BLOCKED_F15_GATE"
    (RES/"f15_pltdm_gate_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    # append-safe (DA F0-F1.5 correção 7): re-run NUNCA apaga histórico do ledger
    new_file = not LEDGER.exists()
    with open(LEDGER, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["claim_id", "number", "metric", "script", "input_file",
                                           "output_file", "source_ref", "raw_or_derived", "status", "note"])
        if new_file: w.writeheader()
        for r in ledger: w.writerow(r)
    print(json.dumps({k: v for k, v in out.items() if k not in ("stage2", "stage1b_survivors")}, indent=2, ensure_ascii=False))
    print("stage2 rows:", len(results2), "| gate:", out["gate"])

if __name__ == "__main__":
    main()
