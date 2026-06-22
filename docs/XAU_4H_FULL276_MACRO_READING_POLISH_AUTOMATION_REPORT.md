# FULL 276 — MACRO READING POLISH / AUTOMATION-PATH

**2026-06-22.** Bloco fechado sob canon efaf48a. Diagnóstico na população 276. NÃO produção, NÃO promoção.
outcome só na avaliação (capado +3.9R = hit-rate, não expectancy). **Validação mora DENTRO dos 276** —
não há OOS nem cross-asset (Cris travou em definitivo; ver `feedback_no_oos_no_crossasset_validation`).

## 0. Correção de rumo (Cris)
HUMAN_VISUAL_REQUIRED **não é endpoint**. O objetivo segue sendo **AUTOMAÇÃO**; a leitura visual é
calibração/ground-truth para CONSTRUIR a representação automatável, não o fim. Este bloco busca o **maior
alavancador de automação** na população completa e classifica cada caminho como automatável-agora /
precisa-feature / precisa-dado / overfit-rejeitado.

## 1. Mapa de erro (onde está a alavanca)
`results/l2_bpt_full276_macro_error_map.csv` (276 episódios). Maior alavanca isolada = **fase-macro causal**:
`AUTO_TAKE_BAD_CONTEXT` (45) + `REVIEW_SHOULD_BE_TAKE` (23) = **68 episódios** cuja raiz é regime/fase-macro
mal-medido (`results/l2_bpt_full276_macro_polish_leverage.csv`). Não é a confluência (já exaurida) nem o exit
(13 `AUTO_TAKE_BAD_EXIT`, eixo próprio) — é a **medição de contexto macro**.

## 2. Feature causal construída
`results/l2_bpt_full276_macro_phase_causal_candidate.csv`. Daily file contíguo (`regime_classifier_v3/
xau_daily_with_features.jsonl`), **shift D-1**. macro_phase:
- `MACRO_BULL_RUN` se `dist_from_126d_high <= 0.04 AND close >= SMA200`
- `MACRO_BULL_PULLBACK` se pullback raso em bull (acima SMA200, sma50 subindo)
- `MACRO_BEAR_MARKDOWN` se `close < SMA200 AND dist > 0.10`
- `MACRO_RANGE_TRANSITION` caso contrário

Distribuição: BULL_RUN 126 · RANGE_TRANSITION 94 · BULL_PULLBACK 33 · BEAR_MARKDOWN 23.

## 3. Candidato A (TAKE = MACRO_BULL_RUN) — resultado
`results/l2_bpt_full276_macro_polish_candidate_results.csv`:

| sistema | n | WR | PF | sumR(cap) | maxDD | Lstreak | runners/16 | big/65 |
|---|---|---|---|---|---|---|---|---|
| **Candidato A (BULL_RUN)** | 126 | **50.0%** | **1.74** | +49.2 | 16.9 | **15** | **9** | **32** |
| visual_anchored TAKE | 82 | 42.7% | 1.49 | +24.5 | 15.7 | 6 | 5 | 24 |

**Candidato A melhora a leitura anterior em TODAS as métricas** com uma feature CAUSAL simples — WR +7.3pp,
PF +0.25, runners 5→9, big 24→32.

### Split temporal (a ressalva honesta)
| período | n | WR | PF | sumR | Lstreak | runners |
|---|---|---|---|---|---|---|
| P1 2020-22 | 46 | 43.5% | 1.20 | +5.6 | **15** | 3 |
| P2 2023-26 | 80 | 53.8% | 2.12 | +43.6 | 5 | 6 |

~89% da edge capada vive em 2023-26. O Lstreak 15 é um **drought de 18 meses (2020-08 → 2022-01)** — o
classificador disparando BULL_RUN em chop pós-COVID. E no **próprio bull 2020** (Mar-Ago, monster rally)
BULL_RUN rende WR 43.5% — ou seja, nem é cleanly bull-beta: subperformou no 1º bull, só o 2º (2023-26) pagou.

## 4. Diagnóstico por especialista
`results/l2_bpt_full276_macro_polish_agent_diagnostics.csv` (4 eixos):
- **Macro Phase Boundary** — fronteira boa 2023-26, ruim 2020-22; feature é *lagging* (marca BULL_RUN no topo).
  Falta geometria de rollover/topo (sequência de LH). NEEDS_FEATURE.
- **Auction Acceptance** — supply-lens já corrigida (markup em bull); mas não separa markup-saudável de
  late-distribution no mesmo BULL_RUN = fonte dos 45 AUTO_TAKE_BAD_CONTEXT. NEEDS_DATA (SVP nativo).
- **Convexity Preservation** — 9/16 runners é ganho real mas ~mecânico; ainda perde 7/16 (bottom-turns/reclaims
  fora de BULL_RUN). Compor com bottom_turn/capitulation.
- **Risk/Exit Separation** — Lstreak 15 é de ENTRADA (fase mal-medida), NÃO de exit; não se resolve por gestão.

## 5. Devil's Advocate (obrigatório) — PASS
`results/l2_bpt_full276_macro_polish_da.csv` (8 pontos). Números reproduzem exatamente. Verdict:
**`PROMISING_BUT_NEEDS_VALIDATION`, explicitamente NÃO `AUTOMATION_READY`.**
- Look-ahead = **PASS-by-construction** (pendente revisão do script gerador do daily file).
- **Falha central = IN-SAMPLE SELECTION** (não a não-estacionariedade): os 4 thresholds foram escolhidos contra
  os mesmos 276 com outcomes visíveis; PF 1.74 = teto otimista. A correção é **remover a seleção**
  (substituir o threshold fitado por convergência causal), não buscar outro dataset.
- Não-estacionariedade CONFIRMADA e pior que o enquadrado (falhou no bull 2020).
- Convexidade 9 vs 5 = ~mecânica.
- realR capado não resgata (assimetria 3.5:1 frágil a decay de WR em sub-janela temporal).
- Outcome-as-predicate = CLEAN (causalidade per-trade limpa; contaminação só na seleção-de-threshold).
- Orientação automação = PASS (não derivou pra human-in-the-loop endpoint).

## 6. Seleção de caminhos
`results/l2_bpt_full276_macro_polish_path_selection.csv`:
1. **macro_phase causal como FEATURE de contexto** — `PROMISING_BUT_NEEDS_VALIDATION`. **Guardar a feature**
   (lever causal ortogonal legítimo); **rejeitar a policy TAKE=BULL_RUN** até substituir o threshold fitado
   por convergência causal validada dentro dos 276.
2. **BULL_RUN OR bottom_turn OR capitulation-reclaim** — `PROMISING_BUT_NEEDS_FEATURE` (recupera 7/16 runners,
   sem hard-block bear; precisa control/null antes de número).
3. **Volume-acceptance REAL (Session VP) dentro de BULL_RUN** — `PROMISING_BUT_NEEDS_DATA` (separa markup de
   late-distribution; ataca os 45 AUTO_TAKE_BAD_CONTEXT).
4. **Reconciliar drought 2020-22** — `PROMISING_BUT_NEEDS_FEATURE` (geometria de topo; o Lstreak 15 é o gargalo
   prop-firm).
- TAKE=BULL_RUN como policy promovida = `OVERFIT_REJECTED`.
- Hard-block bear-leg = `CONVEXITY_KILLER_REJECTED` (legbear RETRATADO na base 276).

## 7. Resposta às perguntas do bloco
- **WR > 50%?** Candidato A = 50.0% (no fio). **WR > 60%?** Não.
- **PF/DD/streak sustentam?** PF 1.74 e DD 16.9 OK; **streak NÃO** (Lstreak 15 = streak-fatal FundedNext ≤5).
- **Runners/big winners preservados?** Melhorou (9/16, 32/65) vs leitura anterior, mas in-sample.
- **Automatável agora?** **NÃO.** A FEATURE é automatável e causal; a POLICY não é promovível enquanto for
  threshold-fit in-sample.
- **Falta feature/dado?** Sim, tudo DENTRO dos 276: (a) substituir o threshold fitado por convergência estrutural
  causal (remove a seleção) + null/permutation + jackknife + robustez ±20% + sub-janelas temporais, (b) revisar
  script daily p/ fechar look-ahead, (c) geometria de topo p/ o drought 2020-22, (d) Session VP real p/ precisão.
  **NÃO há OOS nem cross-asset.**

## 8. Conclusão
O bloco encontrou a **maior alavanca de automação** (fase-macro causal) e produziu uma feature que melhora a
leitura anterior de forma mensurável e causal — **mas a regra TAKE=BULL_RUN não está pronta**: é um ajuste de
threshold in-sample com edge não-estacionária e Lstreak streak-fatal. **Decisão: guardar a feature macro_phase
como lever ortogonal; não promover a policy.** O caminho de automação não termina em humano nem em OOS —
termina em substituir o threshold fitado por convergência causal (validada por null/jackknife/robustez/sub-janelas
DENTRO dos 276) + as 3 features faltantes (geometria de topo, SVP real, composição com bottom-turn).
Diagnóstico apenas; nada promovido; nada em produção. Aguardo direção.

DA = PASS. Outputs: `results/l2_bpt_full276_macro_error_map.csv`, `..._macro_polish_leverage.csv`,
`..._macro_phase_causal_candidate.csv`, `..._macro_polish_candidates.csv`, `..._macro_polish_candidate_results.csv`,
`..._macro_polish_agent_diagnostics.csv`, `..._macro_polish_path_selection.csv`, `..._macro_polish_da.csv`.
