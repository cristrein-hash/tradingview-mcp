# INCIDENTE — L2/BPT Census v1 = NOT_VALIDATION (recall failure)

**Data:** 2026-06-17 · **Severidade:** metodológica (resultado nulo, sem dano a produção). · **Status:** RESOLVIDO via recuperação do Detector v2.2.

---

## 1. O que aconteceu

Rodei o **census L2/BPT BOS-CHoCH 2019-2026** (`run_l2_bpt_census_v1.py`, 53 entries, net **−9.7R**) **SEM** antes validar o recall do detector contra o Ground Truth dos winners desejados (17 GT BOM_HIGH). Depois descobri (via pergunta do Cris) que o detector v1 recaptura **0/17** dos GT BOM_HIGH dentro de ±2 barras (estimativa prévia ≤2/17 — ambas nulas), e que os pouquíssimos que chegavam perto viravam losers.

## 2. Por que o resultado é NULO

O census v1 mediu um detector que **descarta os próprios winners que a estratégia quer capturar**. Um resultado net-negativo de um detector com recall ~0 **não testa o conceito L2/BPT** — testa um detector mal-especificado. O conceito **NÃO foi refutado**; o detector é que falhou.

## 3. Causa raiz (GT-by-GT, ver `results/gt_recall_diagnostic.csv`)

- **13/17** winners: census v1 **nem formou um CHoCH perto** (`no_CHoCH_episode_near`). A fonte de polaridade Williams 5/5 SHIFT5 → protected_LH é estruturalmente mais restritiva que as 6 fontes permissivas do Detector v2.2 (esp. `fractal_3_3`, que ancora 16/17 dos BOM).
- **2/17** (GT09, GT21): CHoCH formou-se mas o SL estrutural >1.5ATR disparou `R_ceiling_abort`.
- **1/17** (GT10): `timeout_no_retest` (retest ≤0.15ATR em 24b estrito demais).
- **1/17** (GT23): `timeout_no_reclaim` (reclaim verde body≥0.5 estrito demais).

## 4. Erro de processo

Tratei a implementação fiel da spec do manifesto como o objetivo e **pulei a sanity-check primária** (recall-gate). A ordem correta é: (1) construir detector → (2) **recall-gate contra Ground Truth** → (3) só então censo/métricas. Pior: o **Detector v2.2 antigo já tinha recall alto** (17/17 confirmado agora) e existia justamente para ser o anchor — e eu o ignorei.

## 5. Resolução

- Census v1 marcado **NOT_VALIDATION / NULO** em `XAU_4H_L2_BPT_BOS_CHOCH_CENSUS_2019_2026.md`.
- **Detector v2.2 recuperado e auditado** (recall 17/17 LIVE) — ver `XAU_4H_L2_BPT_DETECTOR_V2_2_RECALL_AUDIT.md`. Passa a ser a base de recall-alignment; census v1 NÃO é base.
- **Recall HARD-GATE** adicionado ao `gate_manifest.md`: nenhum censo/backtest pode ser interpretado antes do detector capturar ≥15/17 BOM_HIGH.

## 6. Mecanismos contra repetição

- Memória permanente `feedback_recall_gate_before_backtest` (Cris, 2026-06-17).
- Hard-gate no gate manifest (recall ≥15/17 antes de qualquer métrica).
- Hook `post_backtest_devils_advocate.py` (DA forçado após backtest).

---

*Sem impacto em produção (receiver/cloudflared/xau-l1-cycle/broker intactos). Incidente metodológico; aprendizado preservado.*
