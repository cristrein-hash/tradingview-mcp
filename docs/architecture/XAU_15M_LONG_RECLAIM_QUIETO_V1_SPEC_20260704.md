# RECLAIM-QUIETO v1.0 — ENTRY INDEPENDENTE XAU 15M LONG · SPEC CONGELADA (2026-07-04)

> 🔴 **OUTCOME ONE-SHOT LIDO (GO Cris, mesmo dia): SISTEMA MORTO PELOS PRÓPRIOS KILL-CRITERIA.** N157 · NET +6,0 (avg 0,038) · WR_liq 35% · DD −16,5 · **streak −11 (hard ≤5 FAIL)** · indistinguível dos 3 nulls (pct 51-57%) · sem top-5 = −31 · nenhum ano sobrevive sem top-2 · 1 mês = 165% do sum · **ablação: remover QUALQUER lente melhora ou iguala (sem CHoCH: +21,1)** — as lentes reconhecem o ARQUÉTIPO do operador mas não carregam edge de outcome nesta frequência. One-shot respeitado: zero remendo, zero re-tuning. Ver `reclaim_quieto_v1_outcome_oneshot_20260704.py` + results. Lição: estilo ≠ edge; o reconhecimento do arquétipo (2,7× no perfil) não transfere para outcomes com exit let-run.

**Status: DESIGN OUTCOME-BLIND SELADO** — nenhuma leitura de outcome feita (g_R/letrun nunca abertos em nenhuma fase; verificado no código). Leitura de outcome = **ONE-SHOT, requer autorização explícita do Cris**. Origem: mandato Cris (re-mapeamento reprecificado + entry independente, SEM comparação com bases/entries anteriores).

## 1. Re-mapeamento REPRECIFICADO (fundamento)
As 35 operações manuais re-avaliadas com **preço = close real** (lição do gate test) vs 1.107 controles simétricos (`remap_cris_repriced_20260704.py` → `results/cris_repriced_map_20260704.json`). **Morrem no preço real:** todas as lentes de zona (demand_near/supply_far/inside_demand — artefato de fill-fiction confirmado). **Sobrevivem:** higher_low 15M 71%/45% (1,6×) · choch_rec24 15M 86%/54% (1,6×) · quiet4≤1 30M (1,33×) · rsi_40_60 1H (1,3×) · no_initiative_buyML 1H (1,29×) · absorb_sellML 1H (3,3×; cob 26%) · dipleg_sell_dom (1,7-2,1×) · nas_LONG_rec24 30M (2,2×; cob 29%). **Par honesto campeão: higher_low & choch_rec24 15M = 60%/22% = 2,67×.** Medianas: pullback_age 66 vs 36 (paciência) · ema21_dist +0,61 vs +0,25 (compra o RECLAIM, não a faca) · retrace96 0,41.

## 2. Sistema (fusão de 2 designers + DA-pré + síntese; workflow `wf_d3535e07-c1e`; config ÚNICA, zero grid)
**Tese:** pullback envelhecido (≥24 barras do high-96; mediana disparada 70), higher-low estrutural em dip quieto (compressão 30M causal), retração média (0,25-0,75 da caixa-96 — nem faca nem teto), CHoCH 15M **visível** (known_at reconstruído — correção do leak t_anchor do DA-pré), gatilho = **primeira barra de reclaim confirmado da EMA21** (borda close≥ema21+0,15ATR vinda de baixo; no-chase ≤1,2 ATR; esteve abaixo da EMA em ≤24 barras).
**SL estrutural com rejeição (nunca ajuste):** fractal-low recente −0,25 ATR; dist fora de [1,2, 4,0] ATR ou >$40 → SEM SINAL. Medido: mediana 1,93 ATR / $8,6, máx $31,5.
**Dedup:** cooldown 48 barras + 1 tiro por pullback (mesmo high-96 não rearma).
**Frequência (1 look autorizado, RAW 2024-05→2026-07, 111 semanas): N=157 = 1,41/sem** · por ano 55/72/30 (estável) · semanas: máx 4, zero bursts >4 (streak≤5 FN por construção). Pseudo-código integral no artefato do workflow e em `_sm_fuse_reclaim_quieto_v1_20260704.py`.

## 3. Cobertura dos 35 (honesta)
3/35 a ±6 barras (lift ~2,2× vs escala do null; N minúsculo, não-significativo). Queda 6→3 = preço das correções de honestidade (CHoCH known_at −636 candidatos; paciência ≥24 −764; caps de SL). **O sistema captura o ARQUÉTIPO modal do operador (age/retrace/ema_dist batem), não os timings individuais** — o árbitro real da tese de captura = alinhamento PROSPECTIVO (próximos ~15 trades manuais vs null ~7-8%).

## 4. Selagem
`results/reclaim_quieto_v1_signals_20260704.json` (157 sinais congelados) sha256 `21ede9c6c5a5755227982ac34dc9094aec8b18ef09cef846ca8a24d9709a52b3` · script `_sm_fuse_reclaim_quieto_v1_20260704.py` sha256 `7d976e0e...` · selos em `results/reclaim_quieto_v1_seal.sha256`. Qualquer mudança pós-outcome = sistema novo + re-null integral.

## 5. Protocolo da fase OUTCOME (pré-registrado; aguarda GO do Cris)
Entrada no close do sinal · exit let-run aprovado · painel duplo bruto+SB · **null a** mesma-frequência por-ano (500) · **null b** time-matched weekday×hora (500) · **null c** circular-shift semanal · jackknife mês/ano + ablação leave-one-lens (6 leituras declaradas) · runners (sem top-5 >0; nenhum ano negativo sem top-2) · FN-proxy (streak≤5 hard; throttle simulado dentro) · alinhamento prospectivo como kill-criterion.

## 6. Kill-criteria (congelados)
Causalidade violada → kill imediato · frequência rolling 12sem fora [1,4]/sem → suspender · alinhamento prospectivo ≤ null → tese refutada · geometria degenerada (rejeições SL >40%/mês) → kill · mudança de versão do indicador SMC → re-selar · fase outcome: não superar controle estrutura-pura nos nulls / streak>5 / ano líquido ≤0 → kill do sistema, não remendo.

## 7. Ledger
D1 34 looks · D2 ~58 (subcontagem reconhecida) · DA-pré 3 inspeções read-only · fusão 1 look (caracterização freq/cobertura da config exata) · **outcome: 0 leituras**. Multiplicidade declarada; status EXPLORATORY até a fase outcome + prospectivo.
