# XAU 4H L2/BPT — Multi-Agent Engine — CHECKPOINT 2026-06-19

Checkpoint documental do estado do **engine multiagente de qualificação de trades** ANTES de iniciar a
infraestrutura de Hypothesis Registry / Validation Lab / Promotion Gate. Snapshot apenas — não altera
engine, não roda teste, não toca produção.

---

## 1. Escopo exato

- **Estratégia:** XAU 4H **L2/BPT** (BOS-CHoCH) Trade Qualification Engine.
- **NÃO** é engine global de trading.
- **NÃO** promover para outras estratégias / ativos / timeframes.
- Arquitetura reutilizável no futuro, mas sem promoção cross-strategy agora.
- Toda a análise é **diagnóstico**, outcome cruzado apenas pós-hoc; especialistas cegos a decisão/outcome.

---

## 2. Commits por fase

| Fase | Commit | Título |
|------|--------|--------|
| Phase 0   | `ffb06ba` | typed packet schema + evidence schema + validator (infra only) |
| Phase 1   | `5e7cf34` | Stage A Context Classifier cego (non-circular PASS; re-deriva setup_type) |
| Phase 2A  | `2a70da7` | 10 specialist evidence generation + ablation prep (100% validated) |
| Phase 2B  | `3a67707` | ablation / contribuição marginal (diagnóstico; aggregator NÃO ainda) |
| Phase 2B.5| `2a59b4f` | confluência / interação (1 confluência genuína: capit+rsi) |

---

## 3. O que foi criado em cada fase

### Phase 0 — `ffb06ba` (infra)
- `multi_agent_schema.py`: dicionário dos 84 fatores (FACTORS), SPECIALIST_FAMILIES, FAMILY_FACTORS, `allowed_for`.
- `validate_agent_evidence.py`: `validate_evidence(ev, packet)`. Rejeita: fator ∉ 84, value ≠ packet (anti-eco),
  fator-proibido-para-família, impact/specialist_id ausente, não-causal, "uso sem value" (anti-narrativa).
- `REASONING_AGENT_PROMPT_TEMPLATE.md` (template de especialista).
- Schema de evidência: `{specialist_id, episode_id, factor_used, value, packet_value, value_match,
  interpretation, impact(positive/negative/neutral/veto/review_flag), strength, decisive_or_supporting, caveat, causal}`.

### Phase 1 — `5e7cf34` (Stage A Context Classifier, cego)
- `run_stage_a_context_classifier.py` + `stage_a_context_classifier_prompt.md`.
- Saídas: `l2_bpt_stage_a_context_labels.jsonl` (276), `_noncircularity_audit.csv`, `_context_outcome_diagnostic.csv`.
- Classifica contexto cego a decisão/outcome; re-deriva `setup_type` (non-circular PASS).

### Phase 2A — `2a70da7` (geração de evidência, 10 especialistas, 276 episódios)
- `run_specialist_evidence.py` (`--prep` stripa campos LEAK e usa os 276; `--collect` valida tudo na Fase 0).
- `gen_specialist_prompts.py` + `prompts/*.md` (10): demand_supply, capitulation, exhaustion_top, volume_vp,
  nas, bubbles, rsi_momentum, risk_sl, bull_beta, devils_advocate.
- Saídas: `specialist_out/*.jsonl` (net_read + array de evidência por episódio), evidência validada 100%,
  `l2_bpt_specialist_ablation_ready_matrix.csv`.

### Phase 2B — `3a67707` (ablation / contribuição marginal — diagnóstico)
- `analyze_specialist_ablation.py`. Saídas: `marginal_contribution`, `redundancy_matrix`, `leave_one_out`,
  `classification`, `error_pattern_analysis`.
- DA `af791016` corrigiu over-claims (capitulation NÃO decisive isolado; volume_vp ruído; demand↔risk_sl
  condicionalmente independentes; cap +3.9R infla magnitudes).

### Phase 2B.5 — `2a59b4f` (confluência / interação — diagnóstico)
- `analyze_specialist_confluence.py`. Saídas: `state_matrix`, `pairwise_confluence`, `three_way_confluence`,
  `confluence_by_context`, `confluence_hit_rate_metrics`, `classification_after_confluence`.
- DA `ac573cc2` (shuffle-null 2000 + context-matched 10k + drop-top2): **1 única confluência genuína = capit+rsi**.

---

## 4. O que NÃO foi criado ainda

- **Aggregator** (nenhum vote/soma/decisão combinada entre especialistas).
- **TAKE/SKIP novo** (0 decisão nova; decisões 2020-2026 congeladas).
- **Opção B** (regime não-bull / bear histórico) — não coletado, não rodado.
- **OOS** (nenhuma validação out-of-sample / split temporal rodada).
- **Promotion gate** (nenhum critério formal de promoção implementado).
- **Validated confluence library** (nenhuma biblioteca de confluências validadas).

---

## 5. Achados principais

| Especialista / componente | Veredito |
|---|---|
| **Stage A** | Auditável, re-deriva contexto sem circularidade. **NÃO é edge novo** — é organização/observabilidade. |
| **nas** | **DECISIVE individual.** |
| **exhaustion_top** | Útil **com caveat** (winner-selection + cap +3.9R infla magnitude). |
| **demand_supply + risk_sl** | **SUPPORTING** (condicionalmente independentes, manter ambos). |
| **volume_vp** | **NOISY** (nenhuma confluência/contexto defensável; células n=1-3). |
| **bubbles** | **CONTEXT_ONLY** (solo lift 1.01× = ruído; só carrega sinal dentro da célula capit+rsi). |
| **devils_advocate** | **VETO_ONLY** — precisa **rewrite**; veto ainda NÃO validado além do contexto (DAveto+demand-hostile p=0.11). |
| **Confluência genuína** | **`capitulation + rsi_momentum`** — única que sobrevive a todos os gates. |

Detalhe do par genuíno: family-wise p=0.014 (shuffle-null), context-matched p=0.0098 (sinal independente do
contexto), drop-top2 +1.25. **Métrica honesta = hit-2R 65% vs base 32% (lift 2.0×, Wilson-lo 41%)**.
`rsi_momentum` standalone NÃO é decisive (lift 1.10×); só importa no par.

---

## 6. Status de `capitulation + rsi_momentum`

- **PROMISING_IN_SAMPLE** — sobrevive shuffle-null + context-matched + drop-top2 (in-sample).
- **OOS_CANDIDATE** — candidato a validação out-of-sample como **hit-rate target** (não como avgR).
- **NÃO promoted.**
- **NÃO aggregator rule.**
- **NÃO TAKE rule.**
- Caveat: n=17, 4 episódios no cap +3.9R → avgR +1.56 é ~40% cap-inflado (floor-2R → +1.11).
  **In-sample, não validado OOS.** A única afirmação defensável é hit-rate, não expectancy em R.

---

## 7. Próximo bloco planejado

**Hypothesis Registry + Validation Lab + DA Audit + Promotion Gate.**

Objetivo: dar à hipótese `capit+rsi` (e às futuras) um trilho formal de validação OOS antes de qualquer
aggregator. Registry = catálogo de hipóteses com status/pré-registro; Validation Lab = execução OOS
controlada (split temporal / sub-janelas XAU); DA Audit = adversário obrigatório por hipótese;
Promotion Gate = critério explícito para sair de IN_SAMPLE → VALIDATED.

> Nota: este checkpoint **não** inicia essa infra. Aguarda autorização explícita por bloco.

---

## 8. Riscos atuais

- **Overfit** — única confluência sobre n=17; combinatória in-sample (31 combos testadas).
- **Ultra-filtragem** — empilhar especialistas reduz n e fabrica falso-edge.
- **Confluência in-sample** — capit+rsi clear a multiplicidade a p=0.014 (fino), não validada OOS.
- **n pequeno** — células de 13-17 episódios; instabilidade alta.
- **Cap-inflated expectancy** — realR capado em +3.9R distorce avgR; usar hit-rate.
- **Aggregator prematuro** — construir aggregator sobre 1 célula de 17 = overfit garantido.

---

## 9. Produção

- **Intacta.**
- **Sem chart / MCP / plot / SLIM.**
- **`decisions_merged` intocado** (decisões 2020-2026 congeladas; 0 TAKE/SKIP novo).
- Engine de qualificação atual não foi alterado por nenhuma das fases de análise.

---

## 10. Token GitHub

- **Pendente renovação.**
- Tratar **apenas quando o usuário autorizar**. Nenhum push remoto neste bloco.
