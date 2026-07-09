#!/usr/bin/env python3
"""F1.5 CONTINGÊNCIA PRÉ-REGISTADA (manifest.contingency_preregistered): após falha do gate com
herdados congelados, abrir eff_thr {0.25,0.30,0.35} x slope_thr {0.15,0.20,0.25} sobre o sub-grid A1
(override OFF, 18 configs M x K_up x K_down). Todos os looks no ledger. Leitura dinâmica de trajetória
(caminhada de pernas), não snapshot. Sem eventos/entry/backtest. STOP e reporte ao Cris no fim."""
import json, csv, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import f1_structural_leg_machine as f1
from f1_structural_leg_machine import Data, walk
from f15_pltdm_gate import (gt_pltdm, stage1_metrics, plausible, dev_from_seed,
                            match, leg_candidates, PREHOLD_END, GRID, LEDGER)

def main():
    D = Data()
    PLT, DM = gt_pltdm()
    WIN = (min(t for t, _ in PLT)-2*86400, max(t for t, _ in DM)+2*86400)
    sub = [{"M": M, "K_up": ku, "K_down": kd, "D_flush": float("inf"), "mom": 24}
           for M in GRID["M"] for ku in GRID["K_up"] for kd in GRID["K_down"]]
    rows = []; looks = 0
    for eff in (0.25, 0.30, 0.35):
        for slp in (0.15, 0.20, 0.25):
            if eff == 0.30 and slp == 0.20:
                continue  # base já corrida no f15
            f1.EFF_THR = eff; f1.SLOPE_THR = slp
            D._rawleg_cache = {}
            surv = []
            for cfg in sub:
                looks += 1
                m = stage1_metrics(D, cfg, PREHOLD_END)
                if plausible(m):
                    surv.append(cfg)
            surv.sort(key=lambda c: (dev_from_seed(c), json.dumps(c, sort_keys=True)))
            for cfg in surv[:6]:   # top-6 por célula (limite declarado p/ conter looks)
                looks += 1
                _, legs, _ = walk(D, cfg)
                tops, bots = leg_candidates(legs, WIN)
                hp, _ = match(PLT, tops, D)
                hd, _ = match(DM, bots, D)
                rows.append({"eff": eff, "slope": slp, "cfg": cfg, "PLT": hp, "DM": hd,
                             "passes": hp >= 9 and hd >= 10})
    rows.sort(key=lambda r: -(r["PLT"]+r["DM"]))
    out = {"design": "contingência pré-registada eff x slope sobre sub-grid A1; top-6/célula",
           "n_looks": looks, "best": rows[:8], "any_pass": any(r["passes"] for r in rows)}
    (HERE/"results/f15_contingency_result.json").write_text(json.dumps(out, indent=2))
    with open(LEDGER, "a", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([f"S2_CONT", f"{looks}", "looks contingência eff/slope", "f15_contingency.py",
                    "results/f0_bars_cache.jsonl", "f15_contingency_result.json",
                    "RAW 9x .jsonl.gz via f0 (manifest)", "VERIFIED_DERIVED", "EXPLORATORY",
                    f"best={rows[0]['PLT']}/10+{rows[0]['DM']}/11" if rows else "sem sobreviventes"])
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
