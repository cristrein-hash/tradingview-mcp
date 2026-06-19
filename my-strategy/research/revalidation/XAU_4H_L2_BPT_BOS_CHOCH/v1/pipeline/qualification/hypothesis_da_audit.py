#!/usr/bin/env python3
"""L2/BPT — DA AUDIT de hipóteses (skeleton/dry-run). Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
NÃO roda teste novo, NÃO calcula outcome, NÃO toca engine/produção. Aplica o checklist
adversário do Devil's Advocate sobre os METADADOS do registry (discovery_sample, n, caveats,
status) e emite respostas YES/NO/UNKNOWN(MANUAL) + status sugerido. O DA real, com cálculo,
fica para o bloco de validação OOS.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hypothesis_registry as reg

D = reg.D
OUT = os.path.join(D, "l2_bpt_hypothesis_da_audit_dry_run.csv")

CHECKS = [
    "discovered_and_tested_same_set",  # descoberta e teste no mesmo conjunto?
    "n_small",                         # n pequeno?
    "outlier_dependence",
    "cap_pinned_dependence",
    "context_relabel",                 # só re-rotula contexto?
    "subset_of_other_hypothesis",
    "bull_beta_risk",
    "ultra_filter_risk",
    "kills_good_skip_winners",
    "cuts_take_losers",
    "random_context_matched_available",
    "oos_required",
]


def audit(h):
    caT = " ".join(h.get("expected_failure_modes", []) + [h.get("notes", "")]).lower()
    n_req = h.get("minimum_n_required", 0)
    examples = h.get("examples_seen", [])
    disc = (h.get("discovery_sample", "") or "").lower()
    ans = {}
    ans["discovered_and_tested_same_set"] = "YES" if "in_sample" in disc else "UNKNOWN"
    # n da descoberta vem dos caveats/notes (ex.: "n=17")
    ans["n_small"] = "YES" if ("n=1" in caT or "n_pequeno" in caT or "n=17" in caT) else "UNKNOWN"
    ans["outlier_dependence"] = "YES" if ("cap" in caT or "inflad" in caT or "outlier" in caT) else "UNKNOWN"
    ans["cap_pinned_dependence"] = "YES" if "cap" in caT and "pin" in caT or "cap-pinned" in caT or "cap_pinned" in caT else ("YES" if "+3.9" in caT else "UNKNOWN")
    ans["context_relabel"] = "FLAGGED" if "relabel" in caT or "re-selec" in caT or "re-rotul" in caT else "UNKNOWN"
    ans["subset_of_other_hypothesis"] = "UNKNOWN"  # exige comparação entre hipóteses (manual/futuro)
    ans["bull_beta_risk"] = "YES" if "beta" in caT or "bull_gold" in caT or "long_gold" in caT else "UNKNOWN"
    ans["ultra_filter_risk"] = "YES" if (isinstance(n_req, int) and n_req < 40) else "UNKNOWN"
    ans["kills_good_skip_winners"] = "MANUAL"   # exige cruzar com SKIP-winners (cálculo futuro)
    ans["cuts_take_losers"] = "MANUAL"          # exige cruzar com TAKE-losers (cálculo futuro)
    ans["random_context_matched_available"] = "YES" if "context-matched" in caT or "context_matched" in caT or "shuffle-null" in caT else "UNKNOWN"
    ans["oos_required"] = "YES" if h.get("validation_required") else ("YES" if "nao_oos" in caT or "não oos" in caT or "nao oos" in caT else "UNKNOWN")
    # status sugerido pelo DA (default conservador)
    if h.get("status") in ("REJECTED", "RETIRED"):
        suggested = h["status"]
    elif ans["oos_required"] == "YES" and h.get("status") in ("PROMISING_IN_SAMPLE", "OOS_CANDIDATE"):
        suggested = "OOS_CANDIDATE (manter REVIEW_ONLY; NÃO promover sem OOS)"
    else:
        suggested = "MANTER (revisar manualmente)"
    return h.get("hypothesis_id"), ans, suggested


def main():
    rows = []
    for h in reg.load_registry():
        hid, ans, sug = audit(h)
        row = {"hypothesis_id": hid}
        row.update(ans)
        row["suggested_status"] = sug
        rows.append(row)
    os.makedirs(D, exist_ok=True)
    cols = ["hypothesis_id"] + CHECKS + ["suggested_status"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"DA audit DRY-RUN: {len(rows)} hipótese(s) -> {OUT}")
    for r in rows:
        print(f"  {r['hypothesis_id']}: oos_required={r['oos_required']} n_small={r['n_small']} outlier_dep={r['outlier_dependence']} -> {r['suggested_status']}")
    print("NOTA: respostas MANUAL/UNKNOWN exigem cálculo real (bloco OOS futuro). Nada calculado aqui.")


if __name__ == "__main__":
    main()
