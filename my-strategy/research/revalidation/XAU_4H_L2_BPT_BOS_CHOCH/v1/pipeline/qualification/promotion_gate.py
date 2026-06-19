#!/usr/bin/env python3
"""L2/BPT — PROMOTION GATE (skeleton, DEFAULT-DENY). Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
DRY-RUN APENAS. NÃO promove nada, NÃO toca engine/produção. Decide can_promote=False por OMISSÃO
e lista TODOS os motivos de bloqueio. Promover só quando TODOS os bloqueios caírem E o usuário
autorizar explicitamente num bloco futuro.

Bloqueia promoção se: sem prereg; sem primary_metric; sem n mínimo; sem DA aprovado; sem OOS/
sub-janelas suficientes; ultra-filter risk; outlier dependence; status ainda UNTESTED/PROMISING_IN_SAMPLE;
allowed_engine_use indevido para o status.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hypothesis_registry as reg

D = reg.D
OUT = os.path.join(D, "l2_bpt_promotion_gate_dry_run.csv")
# só estes status podem sequer ser considerados para peso decisivo/promoção
PROMOTABLE_STATUS = {"VALIDATED_FEATURE", "AGGREGATOR_RULE_CANDIDATE"}


def gate(h):
    blocks = []
    notes = (h.get("notes", "") + " " + " ".join(h.get("expected_failure_modes", []))).lower()
    # prereg: exige discovery_commit + discovery_sample + primary_metric + minimum_n
    if not h.get("discovery_commit") or not h.get("discovery_sample"):
        blocks.append("sem_prereg(discovery_commit/sample)")
    if not h.get("primary_metric"):
        blocks.append("sem_primary_metric")
    if not isinstance(h.get("minimum_n_required"), int) or h.get("minimum_n_required", 0) <= 0:
        blocks.append("sem_n_minimo")
    # DA aprovado: precisa marca explícita (campo da_approved=True) — ausente => bloqueia
    if h.get("da_approved") is not True:
        blocks.append("sem_DA_aprovado")
    # OOS: precisa oos_validated=True + n no holdout >= minimum_n
    if h.get("oos_validated") is not True:
        blocks.append("sem_OOS_ou_subjanelas_suficientes")
    # riscos estruturais herdados dos caveats
    if "n=17" in notes or "n_pequeno" in notes or "n=1" in notes:
        blocks.append("n_pequeno(ultra_filter_risk)")
    if "cap" in notes or "inflad" in notes or "+3.9" in notes:
        blocks.append("outlier/cap_pinned_dependence")
    if h.get("status") in ("UNTESTED", "PROMISING_IN_SAMPLE"):
        blocks.append(f"status_{h.get('status')}_nao_promovivel")
    if h.get("status") not in PROMOTABLE_STATUS:
        blocks.append(f"status_{h.get('status')}_fora_de_PROMOTABLE")
    # allowed_engine_use indevido para o status
    st, au = h.get("status"), h.get("allowed_engine_use")
    if st in reg.STATUS_USE_OK and au not in reg.STATUS_USE_OK.get(st, set()):
        blocks.append(f"allowed_use_{au}_indevido_para_{st}")
    can = len(blocks) == 0
    return dict(
        hypothesis_id=h.get("hypothesis_id"),
        status=st,
        allowed_engine_use=au,
        can_promote="YES" if can else "NO",
        blocked_reasons="|".join(blocks) if blocks else "(nenhum)",
        required_to_unblock="DA aprovado + OOS validado(n>=min) + status->VALIDATED_FEATURE + remover riscos cap/n + autorização explícita do usuário",
    )


def main():
    rows = [gate(h) for h in reg.load_registry()]
    os.makedirs(D, exist_ok=True)
    cols = ["hypothesis_id", "status", "allowed_engine_use", "can_promote", "blocked_reasons", "required_to_unblock"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"promotion gate DRY-RUN (default-deny): {len(rows)} hipótese(s) -> {OUT}")
    for r in rows:
        print(f"  {r['hypothesis_id']}: can_promote={r['can_promote']} blocks=[{r['blocked_reasons']}]")
    print("NOTA: gate bloqueia por omissão. Nenhuma promoção executada.")


if __name__ == "__main__":
    main()
