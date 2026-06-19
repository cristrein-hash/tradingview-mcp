#!/usr/bin/env python3
"""L2/BPT — VALIDATION LAB (skeleton). Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
DRY-RUN APENAS NESTA FASE. NÃO calcula resultado real, NÃO roda OOS, NÃO toca engine/produção.

Carrega o registry, seleciona hipóteses por status, checa se cada hipótese está COMPLETA e
EXECUTÁVEL (fatores ∈ 84-schema, especialistas ∈ famílias, primary_metric definida), monta um
plano de validação textual e emite dry-run report. O cálculo real fica para um bloco futuro
explicitamente autorizado.
"""
import os, sys, csv, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multi_agent_schema import is_factor, SPECIALIST_FAMILIES
import hypothesis_registry as reg

D = reg.D
OUT = os.path.join(D, "l2_bpt_hypothesis_validation_dry_run.csv")
# status que entram no lab (UNTESTED ainda não tem nada para validar; REJECTED/RETIRED saem)
VALIDATABLE = {"PROMISING_IN_SAMPLE", "OOS_CANDIDATE", "AGGREGATOR_RULE_CANDIDATE"}


def plan_for(h):
    """Plano de validação textual (não executa)."""
    n = h.get("minimum_n_required", "?")
    pm = h.get("primary_metric", "?")
    return ("; ".join([
        f"split temporal in-sample(2020-2023)/holdout(2024-2026) + sub-janelas anuais",
        f"métrica primária={pm} vs base CONTEXT-MATCHED (não incondicional)",
        f"exigir n>={n} no holdout; Wilson-lo separado da base",
        "shuffle-null + context-matched-null + drop-top2 reaplicados no holdout",
        "cap-independente: usar hit-rate, NÃO avgR (realR capado +3.9R)",
        "dedup serial por episódio (anti múltiplos do mesmo evento)",
    ]))


def assess(h):
    missing = []
    v = reg.validate_hypothesis(h)
    missing += [f"campo:{m}" for m in v["missing"]]
    missing += v["errors"]
    for fx in h.get("factors_used", []):
        if not is_factor(fx):
            missing.append(f"fator_inexistente:{fx}")
    for sp in h.get("specialist_ids", []):
        if sp not in SPECIALIST_FAMILIES:
            missing.append(f"especialista_inexistente:{sp}")
    if not h.get("primary_metric"):
        missing.append("primary_metric_ausente")
    status = h.get("status")
    blocked = ""
    if status not in VALIDATABLE:
        blocked = f"status={status} fora do lab (UNTESTED/REJECTED/RETIRED/CONTEXT/VETO não validáveis aqui)"
    ready = (not missing) and (not blocked)
    req_inputs = "qual_packets.jsonl + specialist evidence (state matrix) + outcomes(exitype/realR) + Stage A labels"
    return dict(
        hypothesis_id=h.get("hypothesis_id"),
        status=status,
        ready_for_validation="YES" if ready else "NO",
        missing_fields="|".join(missing) if missing else "(nenhum)",
        required_inputs=req_inputs,
        validation_plan=plan_for(h),
        blocked_reason=blocked or ("" if ready else "definição incompleta"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.parse_args()
    rows = [assess(h) for h in reg.load_registry()]
    os.makedirs(D, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        cols = ["hypothesis_id", "status", "ready_for_validation", "missing_fields",
                "required_inputs", "validation_plan", "blocked_reason"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"validation DRY-RUN: {len(rows)} hipótese(s) -> {OUT}")
    for r in rows:
        print(f"  {r['hypothesis_id']}: ready={r['ready_for_validation']} ({r['blocked_reason'] or 'definição OK; validação real NÃO executada nesta fase'})")
    print("NOTA: nenhum resultado real calculado. OOS não rodado.")


if __name__ == "__main__":
    main()
