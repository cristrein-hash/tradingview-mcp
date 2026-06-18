# XAU 4H L2/BPT — TAKE Engine: política de determinismo

**Status:** `POLICY · ENGINE MARKED NON-DETERMINISTIC (reasoning layer)` · **Data:** 2026-06-18
Define o que é determinístico no pipeline e como tratar o reasoning LLM. Foundation: [[INCIDENT_L2_BPT_ENGINE_REPRODUCIBILITY_TMP_PIPELINE]].

## 1. O que existe
O pipeline tem duas naturezas:
- **Etapas 1-12, 14-15 = DETERMINÍSTICAS** (Python puro: detector, extrator 84 fatores, outcomes, baselines). Reproduzíveis byte/field se os builders forem versionados (ver incidente).
- **Etapa 13 = reasoning TAKE/REVIEW/SKIP = NÃO-DETERMINÍSTICA.** 14 subagentes LLM (modelo claude-opus desta sessão, temperatura default) leram a rubrica `QUALIFICATION_RUBRIC.md` + os packets de 84 fatores e decidiram. **Re-rodar dá decisões diferentes.**

## 2. Prompts/inputs preservados
- **Rubrica:** `QUALIFICATION_RUBRIC.md` (versionada).
- **Template de prompt dos 14 subagentes:** `pipeline/qualification/REASONING_AGENT_PROMPT_TEMPLATE.md` (salvo neste bloco; os 14 prompts diferiam só no número do lote `qual_batch_NN.jsonl`).
- **Inputs (packets):** `repro_recovery/qual_packets.jsonl` + `qual_batch_*.jsonl` (84 fatores, cegos ao resultado).
- **Decisões produzidas:** `repro_recovery/qual_dec_*.jsonl` + `results/l2_bpt_trade_qualification_decisions_merged.csv` (commitado).
- **Modelo/temperatura:** claude-opus (sessão 2026-06-18); temperatura não fixada (default). **Não há seed.**

## 3. Decisão de arquitetura (este bloco)
**Adotado: Opção A (congelar) + Opção B (marcar não-determinístico).**
- **Opção A — congelar decisões:** `decisions_merged.csv` (2020-2026) é o **artefato canônico imutável** das decisões TAKE do engine. Qualquer análise 2020-2026 referencia esse arquivo, não re-roda o reasoning.
- **Opção B — rotular:** o engine é **AI_REVIEW não-determinístico**, NÃO um classificador determinístico. Para um dataset novo (ex. 2013-2017), o reasoning teria que ser re-executado (decisões diferentes) OU substituído por um scoring determinístico.
- **Opção C — scoring determinístico derivado da rubrica:** **NÃO neste bloco** (bloco separado futuro).

## 3b. DECLARAÇÃO FORMAL FINAL (2026-06-18, bloco de parametrização)
**O TAKE engine atual É:**
- **Etapas 1-12,14,15 = DETERMINISTIC** (Python; builders versionados em `pipeline/`; frozen reconstruído byte-equiv estrutural + rsi/nas 99.6% decision-invariant; /tmp parametrizado via env).
- **Etapa 13 (TAKE/REVIEW/SKIP) = AI_REVIEW_NONDETERMINISTIC** + **FROZEN-DECISION ARTIFACT para 2020-2026**.
  - Prompts: salvos em `pipeline/qualification/REASONING_AGENT_PROMPT_TEMPLATE.md` (template dos 14 subagentes) + rubrica `QUALIFICATION_RUBRIC.md`. Model=claude-opus, temp=default, sem seed.
  - Decisões 2020-2026: **CONGELADAS** em `results/l2_bpt_trade_qualification_decisions_merged.csv` (artefato canônico imutável).
- **Para um dataset novo (ex. 2013-2017):** o reasoning teria que ser RE-EXECUTADO → decisões diferentes → declarar AI_REVIEW, NÃO backtest determinístico. **OU** converter a rubrica em scoring determinístico (Opção C, bloco separado) ANTES de qualquer claim de "mesmo engine determinístico".

## 4. Implicação para validação Opção B
Mesmo com todos os builders determinísticos reconstruídos+gated, a etapa 13 (reasoning) não é reproduzível byte-a-byte. Logo "rodar o MESMO engine sem retune" em 2013-2017 significa **re-rodar os subagentes** (decisões novas, mesma rubrica) — aceitável como AI_REVIEW, mas deve ser declarado, não vendido como determinístico. Alternativa rigorosa = Opção C (converter rubrica em score determinístico) antes de validar.

---
*Engine classificado: pipeline determinístico + camada de decisão AI_REVIEW não-determinística. Decisões 2020-2026 congeladas como canônicas.*
