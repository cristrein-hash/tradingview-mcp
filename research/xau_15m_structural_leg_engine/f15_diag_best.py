#!/usr/bin/env python3
"""F1.5 DIAGNÓSTICO INFORMATIVO no melhor config EXPLORATÓRIO (gate BLOCKED => nada congelado).
REPORT-ONLY para decisão do Cris: proximidade dos VELA DE FUNDO pré-2026 (matcher v2) + estado da
máquina nos 4 INVALIDO + latência dos flips. Holdout 2026 FUNDO/circles NÃO tocado. Ledgered."""
import json, csv, sys, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f1_structural_leg_machine import Data, walk
from f15_pltdm_gate import GT_CATALOG, LEDGER

BEST = {"M": 15, "K_up": 5, "K_down": 5, "D_flush": float("inf"), "mom": 24}

def main():
    D = Data()
    states, legs, anchors = walk(D, BEST)
    cat = json.load(open(GT_CATALOG))
    bots = [(l["bot_t"], l["bot_px"]) for l in legs]
    fundos25 = [x for x in cat["notes"]["FUNDO"] if x["date"] < "2026-01-01"]
    hits = 0; miss = []
    for x in fundos25:
        mt, mp = x["t"], x["price"]
        a = D.ATR[bisect.bisect_right(D.TS, mt)-1] or 5
        ok = any(abs(ct-mt) <= 8*3600 and -3*a <= (cp-mp) <= 1*a for ct, cp in bots)
        hits += ok
        if not ok: miss.append(x["date"])
    inval = []
    for x in cat["notes"]["INVALIDO"]:
        i = bisect.bisect_right(D.TS, x["t"])-1
        s = states[i]
        inval.append({"date": x["date"], "leg_dir": s["leg_dir"], "leg_phase": s["leg_phase"],
                      "macro": s["macro"],
                      "is_reject_state": s["leg_dir"] == "LEG_DOWN" and s["leg_phase"] in ("ACTIVE", "SHALLOW_BOUNCE")})
    out = {"config_exploratorio": {k: (None if v == float('inf') else v) for k, v in BEST.items()},
           "fundos_pre2026_proximity": f"{hits}/{len(fundos25)}", "misses": miss,
           "invalido_states": inval,
           "nota": "REPORT-ONLY exploratório (gate BLOCKED, nada congelado); fundos = leg bottoms de pernas macro fechadas vs matcher v2; holdout 2026 intocado"}
    (HERE/"results/f15_diag_best_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with open(LEDGER, "a", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DIAG_F25", f"{hits}/{len(fundos25)}", "proximidade fundos pre-2026 (informativo)",
                    "f15_diag_best.py", "results/f0_bars_cache.jsonl", "f15_diag_best_result.json",
                    "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "REVIEW_LAYER",
                    "config exploratorio nao congelado"])
        w.writerow(["DIAG_INV", f"{sum(1 for r in inval if r['is_reject_state'])}/4", "INVALIDO em estado de rejeicao",
                    "f15_diag_best.py", "results/f0_bars_cache.jsonl", "f15_diag_best_result.json",
                    "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "REVIEW_LAYER", ""])
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
