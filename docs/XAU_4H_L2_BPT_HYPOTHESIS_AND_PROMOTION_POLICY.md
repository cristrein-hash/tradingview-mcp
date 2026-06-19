# XAU 4H L2/BPT — Hypothesis & Promotion Policy

Escopo: **XAU_4H_L2_BPT_BOS_CHOCH** (Trade Qualification Engine). Não é engine global; sem promoção
cross-strategy. Esta política governa como uma hipótese nasce, é validada e — só então — pode pesar
em decisão. Existe para impedir que achado in-sample vire narrativa, regra informal ou overfit.

## Ciclo canônico

```
especialistas → aggregator/observador (PROPÕE) → hipótese → registry → validation lab → DA → promotion gate → validated confluence library
```

O aggregator **propõe**; ele **não** valida a própria hipótese, **não** promove e **não** decide com
base em hipótese não validada.

## Regras de leitura para o futuro aggregator

1. **O aggregator pode PROPOR hipótese** (registrá-la como UNTESTED no registry). Propor ≠ usar.
2. **O aggregator NÃO valida a própria hipótese.** Validação é externa (validation lab + DA + gate).
3. **Hipótese `UNTESTED` NÃO pode ser motivo decisivo.** `allowed_engine_use=NONE`. Ignorada na decisão.
4. **`PROMISING_IN_SAMPLE` pode pesar como REVIEW/CONTEXT, NUNCA como TAKE forte.** Máximo `REVIEW_ONLY`/`CONTEXT_ONLY`. É sinal de "olhar", não de "agir".
5. **`OOS_CANDIDATE`** = fila de validação; ainda `REVIEW_ONLY`. Não decide sozinha.
6. **`VALIDATED_FEATURE` pode pesar forte** (`DECISIVE_SUPPORT`/`VETO_SUPPORT`) — só após OOS + DA + gate.
7. **`AGGREGATOR_RULE_CANDIDATE` ainda precisa simulação/validação** antes de virar regra operacional (`RULE_CANDIDATE` → `PROMOTED`).
8. **`CONTEXT_ONLY`/`REVIEW_FLAG`/`VETO_ONLY`**: usos restritos ao próprio nome; nunca decisivo isolado.
9. **`REJECTED` deve ser IGNORADA** pelo aggregator. `RETIRED` = arquivada.
10. **Toda promoção exige registry + validation lab + DA + promotion gate** + autorização explícita do usuário. Sem exceção.

## Mapa de `status` → `allowed_engine_use` (default-deny)

| status | usos permitidos |
|---|---|
| UNTESTED | NONE |
| PROMISING_IN_SAMPLE | NONE, CONTEXT_ONLY, REVIEW_ONLY |
| OOS_CANDIDATE | NONE, CONTEXT_ONLY, REVIEW_ONLY |
| VALIDATED_FEATURE | + DECISIVE_SUPPORT, VETO_SUPPORT |
| AGGREGATOR_RULE_CANDIDATE | + RULE_CANDIDATE |
| CONTEXT_ONLY | NONE, CONTEXT_ONLY |
| REVIEW_FLAG | NONE, REVIEW_ONLY |
| VETO_ONLY | NONE, VETO_SUPPORT |
| REJECTED / RETIRED | NONE |

`PROMOTED` só é atribuído pelo `promotion_gate.py` (nunca por inserção no registry).

## Promotion gate — bloqueia se (default-deny)

sem prereg (discovery_commit/sample) · sem primary_metric · sem n mínimo · sem DA aprovado ·
sem OOS/sub-janelas suficientes · ultra-filter risk · outlier/cap-pinned dependence ·
status ainda UNTESTED/PROMISING_IN_SAMPLE · allowed_engine_use indevido para o status.

## Estado atual (2026-06-19)

- Registry: 1 hipótese — `L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1`, status `PROMISING_IN_SAMPLE`,
  `allowed_engine_use=REVIEW_ONLY`, `validation_required=True`.
- Validation lab: dry-run (ready=YES estrutural; **OOS não rodado**).
- DA audit: dry-run → OOS_CANDIDATE, manter REVIEW_ONLY, não promover sem OOS.
- Promotion gate: **can_promote=NO** (6 bloqueios). Nada promovido.
- Confluence library: **0 regras promovidas**; capit+rsi PROMISING_IN_SAMPLE/REVIEW_ONLY/oos=false.

## Módulos

- `pipeline/qualification/hypothesis_registry.py` — schema + status + `validate_hypothesis` + seed/validate.
- `pipeline/qualification/run_hypothesis_validation.py` — validation lab (dry-run; plano, não cálculo).
- `pipeline/qualification/hypothesis_da_audit.py` — DA checklist sobre metadados (dry-run).
- `pipeline/qualification/promotion_gate.py` — gate default-deny (dry-run).
- `pipeline/qualification/validated_confluence_library.json` — biblioteca (0 promovidas).
