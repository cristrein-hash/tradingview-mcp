#!/usr/bin/env python3
"""L2/BPT — HYPOTHESIS GATE (skeleton mínimo, default-deny, DRY-RUN). Escopo: XAU_4H_L2_BPT_BOS_CHOCH.

Um único módulo que cobre as etapas procedurais da governança — readiness de validação, checklist DA
sobre metadados, e decisão de promoção — em UMA passada. NÃO calcula outcome, NÃO roda OOS, NÃO cria
aggregator, NÃO toca engine/produção. O store/schema fica no `hypothesis_registry.py`; a biblioteca em
`validated_confluence_library.json`. (Substitui run_hypothesis_validation.py + hypothesis_da_audit.py +
promotion_gate.py + hypothesis_infra_sanity.py — simplificação 2026-06-19, caminho mais curto.)

OBJETIVO DO ENGINE = LUCRO (expectancy × frequência), não winrate/seletividade. O gate rejeita o
NÃO-VALIDADO/overfit, nunca "winrate moderado". 'ultra_filter_risk' é risco porque over-filtrar mata
frequência e lucro. (ver memory feedback_engine_objetivo_lucro_nao_winrate)

THRESHOLDS são PROVISÓRIOS, versionados e revisáveis (definidos com n=1 exemplo). O gate bloqueia por
OMISSÃO; refinar no bloco de validação. A FORMA da validação OOS NÃO é assumida aqui (opções abaixo).

CLI: (default) dry-run -> l2_bpt_hypothesis_gate_dry_run.csv ; --sanity -> l2_bpt_hypothesis_infra_sanity.csv
"""
import os, sys, csv, json, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hypothesis_registry as reg

QD = os.path.dirname(os.path.abspath(__file__))
D = reg.D

# ---- THRESHOLDS versionados / revisáveis (ponto 4) ----
GATE_THRESHOLDS = {
    "version": "v0-provisional-2026-06-19",
    "revisable": True,
    "note": "Provisórios (definidos com n=1 exemplo). Gate bloqueia por omissão. Calibrar no bloco de validação OOS.",
    "min_n_holdout": 30,
    "require_da_approved": True,        # campo da_approved=True no registry
    "require_oos_validated": True,      # campo oos_validated=True no registry
    "promotable_status": ["VALIDATED_FEATURE", "AGGREGATOR_RULE_CANDIDATE"],
    "profit_metrics_preferidas": ["expectancy_R", "sumR", "profit_factor"],
    "winrate_apenas_diagnostico_ou_quando_realR_capado": True,
}

# ---- FORMA da validação OOS NÃO assumida (ponto 3): opções, nenhuma hardcoded ----
LAB_PLAN_OPTIONS = [
    "split temporal in-sample/holdout (corte a definir)",
    "sub-janelas anuais",
    "walk-forward (janela móvel)",
    "purged k-fold (anti-leak temporal)",
]
LAB_PLAN_NOTE = "FORMA a escolher no bloco de validação; NENHUMA assumida. Métrica de LUCRO (expectancy/sumR) + cap-independente (hit-rate só se realR capado); base CONTEXT-MATCHED; dedup serial; shuffle/context-null reaplicados."
VALIDATABLE = {"PROMISING_IN_SAMPLE", "OOS_CANDIDATE", "AGGREGATOR_RULE_CANDIDATE"}


def assess(h):
    notes = (h.get("notes", "") + " " + " ".join(h.get("expected_failure_modes", []))).lower()
    # --- readiness (estrutural; não calcula) ---
    v = reg.validate_hypothesis(h)
    missing = [f"campo:{m}" for m in v["missing"]] + v["errors"]
    ready = (not missing) and (h.get("status") in VALIDATABLE)
    # --- DA flags sobre metadados (dry-run; MANUAL = exige cálculo futuro) ---
    da = {
        "same_set": "YES" if "in_sample" in (h.get("discovery_sample", "") or "").lower() else "UNKNOWN",
        "n_small": "YES" if ("n=1" in notes or "n_pequeno" in notes) else "UNKNOWN",
        "outlier_cap_dep": "YES" if ("cap" in notes or "inflad" in notes or "+3.9" in notes) else "UNKNOWN",
        "context_relabel": "FLAGGED" if ("relabel" in notes or "re-selec" in notes) else "UNKNOWN",
        "bull_beta": "YES" if ("beta" in notes or "long_gold" in notes) else "UNKNOWN",
        "kills_skipwin_or_cuts_takeloser": "MANUAL",   # exige cruzar com outcomes (bloco futuro)
        "null_available": "YES" if ("context-matched" in notes or "shuffle-null" in notes) else "UNKNOWN",
        "oos_required": "YES" if h.get("validation_required") else "UNKNOWN",
    }
    # --- promotion gate (DEFAULT-DENY) ---
    blocks = []
    if not h.get("discovery_commit") or not h.get("discovery_sample"):
        blocks.append("sem_prereg")
    if not h.get("primary_metric"):
        blocks.append("sem_primary_metric")
    if not isinstance(h.get("minimum_n_required"), int) or h.get("minimum_n_required", 0) <= 0:
        blocks.append("sem_n_minimo")
    if GATE_THRESHOLDS["require_da_approved"] and h.get("da_approved") is not True:
        blocks.append("sem_DA_aprovado")
    if GATE_THRESHOLDS["require_oos_validated"] and h.get("oos_validated") is not True:
        blocks.append("sem_OOS_validado")
    if da["n_small"] == "YES":
        blocks.append("ultra_filter_risk(mata_frequencia/lucro)")
    if da["outlier_cap_dep"] == "YES":
        blocks.append("outlier/cap_pinned_dependence")
    if h.get("status") in ("UNTESTED", "PROMISING_IN_SAMPLE"):
        blocks.append(f"status_{h.get('status')}_nao_promovivel")
    if h.get("status") not in GATE_THRESHOLDS["promotable_status"]:
        blocks.append(f"status_fora_de_PROMOTABLE")
    st, au = h.get("status"), h.get("allowed_engine_use")
    if st in reg.STATUS_USE_OK and au not in reg.STATUS_USE_OK.get(st, set()):
        blocks.append(f"allowed_use_{au}_indevido")
    return dict(
        hypothesis_id=h.get("hypothesis_id"),
        status=st,
        allowed_engine_use=au,
        primary_metric=h.get("primary_metric"),
        validation_ready="YES" if ready else "NO",
        missing_fields="|".join(missing) if missing else "(nenhum)",
        lab_plan_options=" | ".join(LAB_PLAN_OPTIONS),
        lab_plan_note=LAB_PLAN_NOTE,
        da_flags=";".join(f"{k}={x}" for k, x in da.items()),
        suggested_status=("OOS_CANDIDATE (manter REVIEW_ONLY; não promover sem OOS)"
                          if da["oos_required"] == "YES" and st in ("PROMISING_IN_SAMPLE", "OOS_CANDIDATE")
                          else "MANTER (revisar manual)"),
        can_promote="YES" if not blocks else "NO",
        blocked_reasons="|".join(blocks) if blocks else "(nenhum)",
        thresholds_version=GATE_THRESHOLDS["version"],
    )


def cmd_dry_run():
    rows = [assess(h) for h in reg.load_registry()]
    os.makedirs(D, exist_ok=True)
    OUT = os.path.join(D, "l2_bpt_hypothesis_gate_dry_run.csv")
    cols = ["hypothesis_id", "status", "allowed_engine_use", "primary_metric", "validation_ready",
            "missing_fields", "lab_plan_options", "lab_plan_note", "da_flags", "suggested_status",
            "can_promote", "blocked_reasons", "thresholds_version"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"GATE dry-run (default-deny, thresholds {GATE_THRESHOLDS['version']}): {len(rows)} hipótese(s) -> {OUT}")
    for r in rows:
        print(f"  {r['hypothesis_id']}: ready={r['validation_ready']} can_promote={r['can_promote']} blocks=[{r['blocked_reasons']}]")
    print("NOTA: forma do OOS NÃO assumida; thresholds provisórios/revisáveis; nada calculado/promovido.")
    return rows


def cmd_sanity():
    rows = reg.load_registry()
    checks = []
    def add(n, ok, d): checks.append({"check": n, "result": "PASS" if ok else "FAIL", "detail": d})
    add("registry_schema_valid", bool(rows) and all(reg.validate_hypothesis(h)["valid"] for h in rows), f"{len(rows)} hipótese(s)")
    capr = next((h for h in rows if h["hypothesis_id"] == "L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1"), None)
    add("capit_rsi_registered", bool(capr) and capr["status"] == "PROMISING_IN_SAMPLE" and capr["allowed_engine_use"] == "REVIEW_ONLY", f"status={capr and capr['status']} use={capr and capr['allowed_engine_use']}")
    gate_rows = cmd_dry_run()
    cr = next((r for r in gate_rows if r["hypothesis_id"] == (capr or {}).get("hypothesis_id")), {})
    add("validation_dry_run_pass", cr.get("validation_ready") == "YES", "ready=YES; OOS não rodado")
    add("da_dry_run_pass", "oos_required=YES" in cr.get("da_flags", ""), "oos_required=YES; manter REVIEW_ONLY")
    add("gate_blocks_capit_rsi", cr.get("can_promote") == "NO" and cr.get("blocked_reasons") not in ("", "(nenhum)"), cr.get("blocked_reasons", "")[:80])
    lib = json.load(open(os.path.join(QD, "validated_confluence_library.json")))
    add("library_no_promoted", lib.get("promoted_rules") == [] and all(it.get("oos_status") is False for it in lib.get("items", [])), f"promoted={lib.get('promoted_rules')}")
    add("no_aggregator_created", len(glob.glob(os.path.join(QD, "*aggregator*"))) == 0, "0 aggregator")
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=QD).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=root).stdout
    touched = [l for l in dirty.splitlines() if any(k in l for k in ("decisions_merged", "qualification_extract", "QUALIFICATION_RUBRIC", "strategy_rules", "monitor_xau", "receiver"))]
    add("no_engine_or_decisions_changed", len(touched) == 0, f"engine/decisões tocados={len(touched)}")
    OUT = os.path.join(D, "l2_bpt_hypothesis_infra_sanity.csv")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "result", "detail"]); w.writeheader(); w.writerows(checks)
    npass = sum(1 for c in checks if c["result"] == "PASS")
    print(f"\nSANITY: {npass}/{len(checks)} PASS -> {OUT}")
    for c in checks:
        print(f"  [{c['result']}] {c['check']}: {c['detail']}")
    return npass == len(checks)


if __name__ == "__main__":
    if "--sanity" in sys.argv:
        ok = cmd_sanity()
        sys.exit(0 if ok else 1)
    else:
        cmd_dry_run()
