---
name: project_e0e1e2_forward_case_20260717
description: "Caso forward E0/E1/E2 2026-07-17: sistema recusou os 2 trades certos do Cris (LONG detetado pelo E1, morto pelo E2 contra-regime) e aprovou 2 SHORTs errados no topo da mesma perna — inversão da leitura; diagnóstico do que falta"
metadata:
  node_type: memory
  type: project
  originSessionId: d1341f00-be87-4e4d-a046-9208ee4563a5
---

# Caso forward E0/E1/E2 — 2026-07-17 (sexta) — INVERSÃO DA LEITURA E2

Primeiro dia de teste live full-time do pipeline. Funil: **224 candidatos E1 → 53 materiality PASS → 11
leituras E2 → 2 surfaced** (SHORTs zone_reject 17:39 @4012.27 e 18:32 @4015.10, conv 45/52, tese
"1D/4H DOWN + supply + up-leg esticada"). **Cris: qualidade RUIM, prevê ambos SL até seg-madrugada**
(forward call falsificável + 6 fatores em `alert-bridge/logs/e2_forward_notes.jsonl` e
[[feedback_e2_calibration_cris_reads]]).

## Os 2 trades CERTOS do dia (plotados pelo Cris; lidos via draw_get_properties)
1. **SHORT @3999.11 (09:00 UTC)** SL 4010.36 TGT 3966.12 → **TGT ATINGIDO** no flush 12:15-12:30 (low
   3959.25), ~2,9R cheio. Motivos (reconstruídos da fita): sequência de LOWER-HIGHS na manhã (4008.5→
   4007.2→4002.6) re-testando supply overnight + round 4000 SEM iniciativa compradora (1 só BUY sz1 na
   madrugada) = rally vazio → fade de CONTINUAÇÃO com o regime DOWN; alvo nos lows overnight.
2. **LONG @3985.24 (13:30 UTC)** SL 3968 TGT 4037 → correu a 4023.9 (+38pts), direção certa. Motivos:
   **clímax vendedor** (cascata SELL bubbles sz2→sz3 12:15-13:15) varre TODOS os lows do dia até 3959 e
   **V-reverte na mesma janela** (~3997) = vendas absorvidas; entrada no 1º pullback pós-reclaim; SL
   abaixo da zona do flush; ímanes acima NÃO testados (OB 15M + 3 SVPs) → alvo em cima. **= Cp-intraday
   de manual; o baseline Cp não dispara porque legMag do flush ~10-12×ATR < 15 (gate).**

## A INVERSÃO (o achado central)
**O E1 DETETOU o LONG certo duas vezes** — 12:37 zone_reject LONG @3981.91 (melhor preço que o do Cris)
e 13:40 @3996.84, ambos materiality PASS — **e o E2 recusou ambos** (conv 8 / 0.12, "contra-regime, 1D
manda BAIXA"). Horas depois **aprovou os 2 SHORTs errados no TOPO da perna que os LONGs recusados
geraram**. Mesmo prior nos dois erros: **peso dominante do regime HTF, zero leitura de clímax/absorção/
maturidade-da-perna/ímanes**. Recusou os certos, aprovou os errados.

## O que falta (diagnóstico; NÃO mexer sem ordem do Cris)
1. **Auction na tese E2:** clímax-então-absorção (cascata SELL + V-reclaim) tem de poder inverter o
   prior do regime; hoje "contra-regime" mata tudo mesmo pós-exaustão (e foi por isso que o null Cp 22%
   existe — MAS o pós-clímax é a exceção que o olho do Cris usa).
2. **Maturidade da perna + ímanes não-testados:** 1º pullback de perna de alta com OB+SVPs por cima
   ≠ local de short.
3. **Iniciativa das velas + bubbles POR LADO na janela do sinal:** os SHORTs aprovados tinham BUY
   bubbles 15:15-16:00 e ZERO sell-bubbles; a tese nem os viu (dossier pode não expor).
4. **Gaps mecânicos:** dedup matou a única zone_reject SHORT da manhã (07:06 mat-PASS); 11:23
   sweep_reclaim SHORT mat-PASS NUNCA chegou ao E2 (gap de acionamento); 4 leituras `claude is_error`
   14:02-15:07 (colisão subprocesso claude -p); sexta-tarde não está em DEAD_SESSIONS={dead_zone,asia,
   other} (wind-down de sexta classifica sessão viva).

Resolução do forward call (dom-noite/seg) = 1º ponto de GT do E2. Só depois calibrar a leitura.
Relaciona [[project_cp_capitulation]] (Cp-intraday abaixo do gate legMag), [[feedback_contextual_convergence_not_determinism]].
