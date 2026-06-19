#!/usr/bin/env python3
"""L2/BPT — HYPOTHESIS REGISTRY (governança). Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
INFRA DE CONTROLE APENAS. Não roda OOS, não decide, não cria aggregator, não toca o engine atual.
Registra hipóteses com schema obrigatório + status + allowed_engine_use, e VALIDA estrutura
(campos completos, fatores ∈ 84-schema, especialistas ∈ famílias, métrica definida).

Regra-mãe: hipótese nova começa UNTESTED + allowed_engine_use=NONE. Só hipótese já documentada
in-sample pode entrar PROMISING_IN_SAMPLE + REVIEW_ONLY (nunca DECISIVE) e ainda assim com
validation_required=True. Promoção exige registry + lab + DA + gate (ver promotion_gate.py).

CLI: --seed (cria/sobrescreve o registry com a hipótese capit+rsi) ; --validate (audita o registry).
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multi_agent_schema import FACTORS, SPECIALIST_FAMILIES, is_factor

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results")
D = os.path.normpath(D)
REGISTRY = os.path.join(D, "l2_bpt_hypothesis_registry.jsonl")
STRATEGY_SCOPE = "XAU_4H_L2_BPT_BOS_CHOCH"

STATUSES = ["UNTESTED", "PROMISING_IN_SAMPLE", "OOS_CANDIDATE", "VALIDATED_FEATURE",
            "AGGREGATOR_RULE_CANDIDATE", "CONTEXT_ONLY", "REVIEW_FLAG", "VETO_ONLY",
            "REJECTED", "RETIRED"]
ALLOWED_USES = ["NONE", "CONTEXT_ONLY", "REVIEW_ONLY", "DECISIVE_SUPPORT",
                "VETO_SUPPORT", "RULE_CANDIDATE", "PROMOTED"]

# status -> conjunto de allowed_engine_use que NÃO violam a governança (default-deny além disso)
STATUS_USE_OK = {
    "UNTESTED": {"NONE"},
    "PROMISING_IN_SAMPLE": {"NONE", "CONTEXT_ONLY", "REVIEW_ONLY"},
    "OOS_CANDIDATE": {"NONE", "CONTEXT_ONLY", "REVIEW_ONLY"},
    "VALIDATED_FEATURE": {"NONE", "CONTEXT_ONLY", "REVIEW_ONLY", "DECISIVE_SUPPORT", "VETO_SUPPORT"},
    "AGGREGATOR_RULE_CANDIDATE": {"NONE", "CONTEXT_ONLY", "REVIEW_ONLY", "DECISIVE_SUPPORT", "RULE_CANDIDATE"},
    "CONTEXT_ONLY": {"NONE", "CONTEXT_ONLY"},
    "REVIEW_FLAG": {"NONE", "REVIEW_ONLY"},
    "VETO_ONLY": {"NONE", "VETO_SUPPORT"},
    "REJECTED": {"NONE"},
    "RETIRED": {"NONE"},
}

REQUIRED_FIELDS = ["hypothesis_id", "strategy_scope", "proposed_by", "proposed_at", "source_phase",
    "hypothesis_name", "description", "exact_rule_candidate", "factors_used", "specialist_ids",
    "context_labels_allowed", "primary_metric", "secondary_metrics", "target_direction",
    "minimum_n_required", "expected_failure_modes", "examples_seen", "discovery_sample",
    "discovery_commit", "status", "allowed_engine_use", "validation_required", "notes"]


def validate_hypothesis(h):
    """Valida estrutura (não outcome). Retorna {valid, missing[], errors[]}."""
    missing = [f for f in REQUIRED_FIELDS if f not in h]
    errors = []
    if h.get("strategy_scope") != STRATEGY_SCOPE:
        errors.append(f"strategy_scope!={STRATEGY_SCOPE}")
    if h.get("status") not in STATUSES:
        errors.append(f"status_invalido:{h.get('status')}")
    if h.get("allowed_engine_use") not in ALLOWED_USES:
        errors.append(f"allowed_use_invalido:{h.get('allowed_engine_use')}")
    st, au = h.get("status"), h.get("allowed_engine_use")
    if st in STATUS_USE_OK and au not in STATUS_USE_OK[st]:
        errors.append(f"use_{au}_proibido_para_status_{st}")
    for fx in h.get("factors_used", []):
        if not is_factor(fx):
            errors.append(f"fator_inexistente:{fx}")
    for sp in h.get("specialist_ids", []):
        if sp not in SPECIALIST_FAMILIES:
            errors.append(f"especialista_inexistente:{sp}")
    if not h.get("primary_metric"):
        errors.append("primary_metric_ausente")
    # default-deny: nada nasce PROMOTED/VALIDATED por inserção
    if st in ("VALIDATED_FEATURE", "AGGREGATOR_RULE_CANDIDATE") and h.get("validation_required") is not False:
        pass  # ok: validado externamente; flag controlada pelo gate, não aqui
    if au == "PROMOTED":
        errors.append("PROMOTED_so_via_promotion_gate")
    return {"valid": not missing and not errors, "missing": missing, "errors": errors}


def load_registry(path=REGISTRY):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def save_registry(rows, path=REGISTRY):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---- SEED: hipótese atual capit+rsi (Fase 2B.5) ----
SEED = [{
    "hypothesis_id": "L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1",
    "strategy_scope": STRATEGY_SCOPE,
    "proposed_by": "phase_2b5_confluence_audit",
    "proposed_at": "2026-06-19",
    "source_phase": "2B.5",
    "hypothesis_name": "Confluência capitulation + rsi_momentum",
    "description": ("Quando o especialista capitulation E o rsi_momentum estão ambos em postura "
        "supportive no mesmo episódio, a taxa de acerto a 2R aproximadamente dobra vs base "
        "context-matched. Dois especialistas fracos isolados que viram informativos JUNTOS."),
    "exact_rule_candidate": ("state(capitulation)==supportive AND state(rsi_momentum)==supportive "
        "-> review_flag positivo (NAO decisivo). Definicao de state conforme analyze_specialist_confluence.py."),
    "factors_used": ["drop20_atr", "rsi_min8", "rsi_drop_6b", "rsi", "rsi_vs_ma"],
    "specialist_ids": ["capitulation", "rsi_momentum"],
    "context_labels_allowed": ["bottom_reversal_capitulation", "bear_bounce", "mid_range"],
    "primary_metric": "hit_2R",  # hit_2R só porque realR está CAPADO +3.9R; objetivo do engine = LUCRO
    "secondary_metrics": ["expectancy_R", "sumR", "profit_factor", "stop_rate", "scratch_rate", "runner_rate"],
    "target_direction": ("LUCRO: expectancy/sumR positivos e estáveis vs base context-matched; hit_2R "
        "(Wilson-lo separado da base) como proxy enquanto realR está capado. R:R alto justifica + losers."),
    "minimum_n_required": 30,
    "expected_failure_modes": ["in_sample_multiplicity", "cap_pinned_inflation_+3.9R", "n_pequeno_17",
        "context_relabel (so re-seleciona bottom_reversal)", "nao_estacionario/beta_long_gold"],
    "examples_seen": ["ver results/l2_bpt_specialist_confluence_hit_rate_metrics.csv (celula capit+rsi, n=17)"],
    "discovery_sample": "full_276_episodes_in_sample_2020_2026",
    "discovery_commit": "2a59b4f",
    "status": "OOS_CANDIDATE",
    "allowed_engine_use": "REVIEW_ONLY",
    "validation_required": True,
    "oos_validated": False,
    "subwindow_validation": "PASS_in_sample_profit_robust",
    "notes": ("DA ac573cc2: family-wise p=0.014 (shuffle-null), context-matched p=0.0098, drop-top2 +1.25; "
        "hit_2R 65% vs base 32% (lift 2.0x, Wilson-lo 41%). VALIDACAO sub-janelas 2026-06-19 "
        "(validate_capit_rsi_oos.py): exp_decap +2.055R (drop2 +1.529), pf 8.94, maxDD -1.1R, streak 2; "
        "bate TODOS controles (context-matched 0.608, capit-so 0.858, rsi-so 0.563, nas 1.178); "
        "positiva em TODAS janelas (H1 +0.84/H2 +2.56; thirds +0.87/+2.19/+2.43); random-matched null P=0.3%. "
        "PASS in-sample profit-robusto -> OOS_CANDIDATE. CAVEATS: NAO e OOS verdadeiro (mesmo conjunto da "
        "descoberta); janela 2020-2022 fina/fraca (n3-5, hit2R 33-40%); 4 runners capados; freq ~2.8/ano "
        "(flag de confluencia, NAO engine standalone). REVIEW_ONLY, NUNCA DECISIVE ate OOS real pelo gate."),
}]


def cmd_seed():
    rows = SEED[:]
    bad = [(h["hypothesis_id"], validate_hypothesis(h)) for h in rows]
    bad = [(hid, r) for hid, r in bad if not r["valid"]]
    if bad:
        for hid, r in bad:
            print(f"INVALIDO {hid}: missing={r['missing']} errors={r['errors']}")
        sys.exit(1)
    save_registry(rows)
    print(f"seed: {len(rows)} hipótese(s) -> {REGISTRY}")
    for h in rows:
        print(f"  {h['hypothesis_id']}: status={h['status']} use={h['allowed_engine_use']} validation_required={h['validation_required']}")


def cmd_validate():
    rows = load_registry()
    allok = True
    for h in rows:
        r = validate_hypothesis(h)
        flag = "OK" if r["valid"] else "FALHA"
        if not r["valid"]:
            allok = False
        print(f"[{flag}] {h.get('hypothesis_id')}: status={h.get('status')} use={h.get('allowed_engine_use')}"
              + ("" if r["valid"] else f" missing={r['missing']} errors={r['errors']}"))
    print(f"registry: {len(rows)} hipótese(s) | schema {'PASS' if allok else 'FAIL'}")
    return allok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.seed:
        cmd_seed()
    elif a.validate:
        cmd_validate()
    else:
        print("--seed ou --validate")
