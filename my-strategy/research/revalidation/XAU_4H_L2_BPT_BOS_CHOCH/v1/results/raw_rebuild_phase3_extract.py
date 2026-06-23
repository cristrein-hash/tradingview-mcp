#!/usr/bin/env python3
"""FASE 9 — extrator de outcome+path para o outcome audit RAW-clean (read-only, reprodutivel).
Materializa por episodio: outcome UNCAPPED (mfe_R/mae_R/max_run_R/runner/monster/realR/exit) que o Reader
NUNCA viu, + caminho de preco pos-entry (10/20/40 barras) do RAW frozen. NAO e gate/hit-rate; e diagnostico
de QUALIDADE de leitura por episodio (SANITY_PROBE declarada). Saida: raw_rebuild_phase3_audit_data.txt.
Verified at: 2026-06-23."""
import csv, json, os

V1 = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTCOMES = os.path.join(V1, "results", "l2_bpt_uncapped_or_proxy_outcomes_276.csv")
JSONL = os.path.join(V1, "repro_recovery", "raw_features_2020_2026.jsonl")
OUT = os.path.join(V1, "results", "raw_rebuild_phase3_audit_data.txt")

CL1 = [4918, 4926, 1661, 5701, 6887, 7426, 8878, 8923, 8940]
CL2 = [5826, 1623, 4401, 3825, 1522, 1873, 5627, 1775, 3949, 3929]
EPS = CL1 + CL2

OCOLS = ["datetime", "risk_atr", "capped_realR", "capped_exitype", "mfe_R", "mae_R", "mae_before_mfe",
         "max_run_R", "runner_bucket", "runner_flag", "monster_flag", "hit2", "hit3", "hit5", "hit8", "hit10",
         "time_to_2R", "time_to_max", "stop_before_2R", "realized_vstair_120"]


def main():
    tg = set(EPS)
    outc = {int(r["bar_idx"]): r for r in csv.DictReader(open(OUTCOMES)) if int(r["bar_idx"]) in tg}
    bars = [json.loads(l) for l in open(JSONL) if l.strip()]
    L = []
    a = L.append
    a("# FASE 9 — OUTCOME AUDIT DATA (RAW-clean rebuild). Outcome UNCAPPED + price path pos-entry.")
    a("# O Reader cego NUNCA viu nada disto. Use SO para auditar a leitura ja congelada.\n")
    for grp, name in ((CL1, "CLUSTER 1"), (CL2, "CLUSTER 2")):
        a(f"\n{'='*78}\n{name}\n{'='*78}")
        for bi in grp:
            o = outc.get(bi)
            a(f"\n--- EPISODIO {bi} ---")
            if o:
                a("  outcome: " + " ".join(f"{c}={o.get(c)}" for c in OCOLS))
            else:
                a("  outcome: NOT FOUND")
            if bi < len(bars):
                ec = bars[bi].get("close")
                a(f"  entry close={ec}")
                for N in (10, 20, 40):
                    seg = bars[bi + 1: bi + 1 + N]
                    if not seg:
                        continue
                    hh = max(b["high"] for b in seg); ll = min(b["low"] for b in seg); lc = seg[-1]["close"]
                    a(f"  next {N:>2}b: maxHigh={hh:.2f} minLow={ll:.2f} lastClose={lc:.2f} "
                      f"upMove={hh-ec:+.2f} dnMove={ll-ec:+.2f}")
    txt = "\n".join(L)
    open(OUT, "w").write(txt)
    print(f"OK -> {OUT} ({len(EPS)} episodios)")


if __name__ == "__main__":
    main()
