# XAU 4H L2/BPT — Hypothesis & Promotion Policy

Escopo: **XAU_4H_L2_BPT_BOS_CHOCH** (Trade Qualification Engine). Não é engine global; sem promoção
cross-strategy. Esta política governa como uma hipótese nasce, é validada e — só então — pode pesar
em decisão. Existe para impedir que achado in-sample vire narrativa, regra informal ou overfit.

## Objetivo: LUCRO, não winrate/seletividade
O engine existe para **lucro em prop firm** = **expectancy × frequência** (R-multiple acumulado),
respeitando streak ≤5 e drawdown da FundedNext. **R:R alto justifica alguns losers a mais.** NÃO se
busca n baixo + ultra-winrate; over-filtrar mata frequência e lucro (por isso `ultra_filter_risk` é
risco). Métrica de lucro (expectancy/sumR/profit factor) é primária; winrate/hit_2R é diagnóstico ou
proxy quando realR está capado. **O gate rejeita o NÃO-VALIDADO/overfit, nunca "winrate moderado".**
Uma hipótese com WR médio + R:R alto + frequência decente é exatamente o que DEVE passar.

## Simplicidade (skeleton mínimo)
Governança = caminho mais curto e seguro. As etapas procedurais (readiness + DA + gate + sanity) vivem
num **único módulo** `hypothesis_gate.py`; o store/schema em `hypothesis_registry.py`; a biblioteca num
JSON. Sem lógica de cálculo prematura. Burocracia que desacelera pesquisa sem adicionar edge é o oposto
do objetivo — evitá-la.

## Thresholds — provisórios, versionados, revisáveis
Os thresholds do gate (`min_n_holdout`, DA aprovado, OOS validado, status promovível) foram definidos
com **n=1 exemplo** → são **provisórios** (`version: v0-provisional-2026-06-19`, `revisable: true`) e
serão **calibrados no bloco de validação**. O gate **bloqueia por OMISSÃO** — thresholds errados pecam
por bloquear demais, não por promover indevidamente.

## Forma da validação OOS — NÃO assumida
A forma do OOS (split temporal / sub-janelas anuais / walk-forward / purged k-fold) **não é hardcoded**.
O lab lista opções; a escolha acontece no bloco de validação, com métrica de lucro + base context-matched.

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

## Validação sub-janelas capit+rsi (2026-06-19, foco LUCRO)
`validate_capit_rsi_oos.py` (prereg `docs/XAU_4H_L2_BPT_CAPIT_RSI_OOS_PREREG.md`). Método: split temporal
in-sample (sem dado novo; Opção B não rodada → NÃO é OOS verdadeiro). Resultado da célula (n=17, 4 runners
capados): **exp_decap +2.055R** (drop-top2 +1.529 → robusta a outliers), **profit factor 8.94**, maxDD
−1.1R, streak 2, hit2R 65% Wilson [0.41,0.83]. **Bate todos os controles** (context-matched 0.608, capit-só
0.858, rsi-só 0.563, base 0.427, nas 1.178); **positiva em todas as janelas** (H1 +0.84 / H2 +2.56; thirds
+0.87/+2.19/+2.43); random-matched null P=0.3%. **Veredito: PASS in-sample profit-robusto + INCONCLUSIVE em
OOS verdadeiro** (mesmo conjunto da descoberta; janela 2020-2022 fina/fraca n3-5; freq ~2.8/ano = flag de
confluência, NÃO engine standalone). Status `PROMISING_IN_SAMPLE` → **`OOS_CANDIDATE`**, mantém REVIEW_ONLY.
Próximo: OOS real exige dado independente (Opção B / nova coleta). Gate continua `can_promote=NO`.

## Estado atual (2026-06-19)

- Registry: 1 hipótese — `L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1`, status `OOS_CANDIDATE`,
  `allowed_engine_use=REVIEW_ONLY`, `validation_required=True`, `oos_validated=False`.
- Validation lab: dry-run (ready=YES estrutural; **OOS não rodado**).
- DA audit: dry-run → OOS_CANDIDATE, manter REVIEW_ONLY, não promover sem OOS.
- Promotion gate: **can_promote=NO** (6 bloqueios). Nada promovido.
- Confluence library: **0 regras promovidas**; capit+rsi PROMISING_IN_SAMPLE/REVIEW_ONLY/oos=false.

## Módulos (skeleton mínimo)

- `pipeline/qualification/hypothesis_registry.py` — store + schema + status + `validate_hypothesis` + seed/validate.
- `pipeline/qualification/hypothesis_gate.py` — **único** módulo procedural: readiness de validação +
  DA checklist + promotion gate (default-deny) + `--sanity`. Dry-run; thresholds versionados; forma do OOS não-hardcoded.
  Outputs: `l2_bpt_hypothesis_gate_dry_run.csv`, `l2_bpt_hypothesis_infra_sanity.csv`.
- `pipeline/qualification/validated_confluence_library.json` — biblioteca (0 promovidas).
