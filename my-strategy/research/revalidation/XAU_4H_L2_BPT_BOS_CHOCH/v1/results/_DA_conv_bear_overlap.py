#!/usr/bin/env python3
"""OVERLAP & CONTRIBUICAO INCREMENTAL — conv<=1 vs regime BEAR (v3) vs bear-leg refined (aprovado). Responde: conv<=1
e REDUNDANTE com um filtro BEAR ja conhecido, ou corta um subconjunto mais inteligente (preservando runner que BEAR
cortaria)? Conjuntos A-F + decisivos conv<=1\\BEAR e BEAR\\conv<=1. Tabela por-trade salva. Calibracao 276 (canon),
NAO regra/gate. Read-only. Verified 2026-06-25."""
import json, csv, datetime as dt, bisect
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
DSPA = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
SW = {r["b"]: r for r in json.load(open(V1 / "results/l2_bpt_elimination_sweep.json"))}
# bear-leg refined (aprovado): bear_leg_refined=="BLOCK" no cross_master_matrix (dentro de MACRO_BEAR_LEG; 12 BLOCK)
BLR = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_dspa_cross_master_matrix_276.csv")):
    try: BLR[int(float(r["bar_idx"]))] = r
    except Exception: pass
# regime v3 asof (p/ derivar voice regime e why_conv_low)
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_ep"] = toep(r["ts"])
rb.sort(key=lambda r: r["_ep"]); rbt = [r["_ep"] for r in rb]
def v3_asof(et):
    k = bisect.bisect_right(rbt, et) - 1
    return rb[k].get("raw_state") if k >= 0 else None

rows = []
for b in sorted(OUT):
    o = OUT[b]; d = DSPA.get(b, {}); sw = SW.get(b, {})
    v3 = v3_asof(int(F[b]["ts_epoch"]))
    sst = d.get("f6_svp_state"); dpoc = d.get("f6_dist_poc_atr")
    vreg = 1 if (v3 and v3 != "BEAR") else 0
    vsnap = 1 if (sst == "ACCEPTING_ABOVE_VALUE" or (dpoc not in (None, "") and float(dpoc) > 0)) else 0
    vsweep = 1 if str(d.get("f1_swept_low_reclaim")).lower() in ("1", "true", "yes") else 0
    conv = int(sw.get("conv", vreg + vsnap + vsweep))  # conv guardado (inclui buy-bubble)
    vbub = conv - vreg - vsnap - vsweep
    off = [n for n, v in (("regime", vreg), ("snap", vsnap), ("sweep", vsweep), ("bubble", vbub)) if v == 0]
    realR = float(o["capped_realR"]) if o.get("capped_realR") not in (None, "") else 0.0; mfe = float(o["mfe_R"])
    blr = BLR.get(b, {})
    rows.append({"b": b, "dt": o["datetime"][:10], "conv": conv,
                 "rm_conv": 1 if conv <= 1 else 0, "rm_bear": 1 if v3 == "BEAR" else 0,
                 "rm_blr": 1 if str(blr.get("bear_leg_refined")).upper() == "BLOCK" else 0,
                 "mfe": mfe, "realR": realR, "winner": 1 if realR > 0 else 0, "runner": 1 if mfe >= 10 else 0,
                 "regime": v3, "macro_leg": blr.get("macro_reader_leg", "") if blr else "", "why_low": "|".join(off)})

def summ(sub, name):
    n = len(sub); rcut = sum(s["runner"] for s in sub); wcut = sum(s["winner"] for s in sub)
    sr = sum(s["realR"] for s in sub)
    print(f"  {name:>22} | n={n:>3} | runners_cut={rcut} | winners_cut={wcut} | sumR_removed={sr:+6.1f}")
    return n, rcut, wcut, sr

CONV = [r for r in rows if r["rm_conv"]]; BEAR = [r for r in rows if r["rm_bear"]]; BLR_ = [r for r in rows if r["rm_blr"]]
print(f"corpus 276 | conv<=1={len(CONV)} BEAR(v3)={len(BEAR)} bear_leg_refined={len(BLR_)}\n")
print("=== CONJUNTOS (o que cada um REMOVE) ===")
summ(CONV, "A) conv<=1")
summ(BEAR, "B) BEAR(v3)")
summ(BLR_, "C) bear_leg_refined")
summ([r for r in rows if r["rm_conv"] and r["rm_bear"]], "D) conv<=1 ∩ BEAR")
EmB = [r for r in rows if r["rm_conv"] and not r["rm_bear"]]
BmE = [r for r in rows if r["rm_bear"] and not r["rm_conv"]]
summ(EmB, "E) conv<=1 \\ BEAR")
summ(BmE, "F) BEAR \\ conv<=1")
# overlap conv vs bear-leg refined
print(f"\noverlap conv<=1 ∩ bear_leg_refined = {len([r for r in rows if r['rm_conv'] and r['rm_blr']])} / {len(BLR_)} do BLR")
print("\n=== DECISIVO E) conv<=1 \\ BEAR (trades extras que so a baixa-convergencia corta) ===")
for r in sorted(EmB, key=lambda x: x["dt"]):
    print(f"  #{r['b']:>4} {r['dt']} {'WIN ' if r['winner'] else 'LOSS'} realR={r['realR']:+.1f} mfe={r['mfe']:.1f} runner={r['runner']} regime={r['regime']} why_low={r['why_low']}")
print("\n=== DECISIVO F) BEAR \\ conv<=1 (trades que BEAR corta mas conv preserva — o runner mora aqui?) ===")
for r in sorted(BmF if (BmF:=BmE) else [], key=lambda x: (-x["runner"], x["dt"])):
    print(f"  #{r['b']:>4} {r['dt']} {'WIN ' if r['winner'] else 'LOSS'} realR={r['realR']:+.1f} mfe={r['mfe']:.1f} RUNNER={r['runner']} regime={r['regime']} conv={r['conv']} why_low={r['why_low']}")
# tabela completa salva
import csv as _csv
with open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv", "w", newline="") as fh:
    w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"\ntabela completa -> results/l2_bpt_conv_bear_overlap_table.csv ({len(rows)} trades). Calibracao 276, nao gate.")
