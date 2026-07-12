# SESSÃO 2026-07-12 — VERIFICAÇÃO E TENTATIVA DE AFINAÇÃO DO REGIME DETECTOR 4H

> Registro canónico do dia. Detector de produção/pesquisa INTOCADO. P&L fora do loop em tudo.
> GT = `REGIME_GT_CRIS_4H_20260712.json` (19 janelas, sha be4a9d6f…, bordas ±3d fora).

## 1. Fix causal + prova
- Vazamento real em `ovr_at` (barra em formação) corrigido (`67bb7ef`); gates L1/L2 byte-idênticos;
  DA 6/6 CAUSAL_OK. Repaint refutado (rótulos nunca reescritos; caixas do plot = cosmética).

## 2. Medições de base
- Churn: RANGE21-22 1,07 vs TREND24-25 0,95/100b (defeito = rótulo errado, não frequência).
- "15M" = diário reamostrado (16 vs 14 flips) — zero conteúdo nativo 15M.
- Exposição janela range: L1 2/24 (nada) · L2 56/276 (material).
- Overlays do Cris (22 lidos via MCP): híbrido hindsight = L1 zero · **L2 +54R** (teto do prémio).
- Baseline vs GT: acc 66,5 · bal 64,1 · piores janelas: V-turn 6,9% · nov/24 0% · range21-22 35,8%.

## 3. Seis mecanismos de melhoria — TODOS REPROVADOS (causais, DA-limpos)
| Mecanismo | Resultado |
|---|---|
| Contenção ER-120 (grelha congelada) | −16 a −43pp em TODOS os combos → ARQUIVADA (triagem barata) |
| Dial dd×K_in×K_out (30 combos) | soma-zero; nada bate bal 64,1; split: IS-winner 69,2 < baseline 73,4 cego |
| Pivots fractais micro (r1, 32 combos) | escala ERRADA (129 pivots na janela de ~8 swings) — invalidado; melhor cego 51,0 |
| Pivots macro zigzag/fractal (r2, 80 combos) | melhor cego 56,2; IS-tops desabam (61,8→40,1) |
| 4 famílias ortogonais multi-agente + combos | leg 57,5/cong 54,6/cad 48,2/mtf 58,1 in; melhor combo cego 66,3 < 73,4 |
| Hierárquico (base decide RANGE; mtf dá direção) | critério congelado 1/3 PASS → NÃO ADOTADO |

## 4. K-fold purged/embargoed (split cronológico do chat estava partido — ambiguidade toda no treino)
r2 (purge por janela GT inteira + embargo 15d):
- baseline: folds 47,3/52,9/78,3/75,7/75,6 · média 66,0±13,1 · **OOF 64,1** (B/Be/R 68,6/70,7/53,1)
- C_V voto: média 67,5±8,7 (ganha 3/5 folds; V-turn 6,9→69) · OOF 60,9 (RANGE 31,1) — melhor na direção, pior no RANGE
- HIER: OOF 62,6 · nov/24 0% (estrutural: base-RANGE cala o mtf) → reprovado pelo critério do Cris
- leg_geometry sozinho: 40,0 → morto (RANGE 73,9 era artefacto da era 2020-22)

## 5. Sonda-antes-de-rodar (novo padrão obrigatório)
Override de precisão (mtf fura RANGE quando "grita"): sonda de separação EMA10-30/ATR matou antes
da corrida — nov/24 (n=6!) med |sep| 0,50 vs RANGE p75 0,54 (sobrepostos; 20,6% dos RANGE abaixo
da mediana de nov/24; sinal troca DENTRO da janela). `probe_ema_sep_nov24_vs_range.py`.

## 6. Diagnóstico honesto
(a) árbitro sem poder estatístico (19 janelas; alvo n=6 barras); (b) perseguimos episódios n=1 com
mecanismos globais — imposto em 6.700 barras para ganhar em 60; (c) baseline = ótimo local real
(~200 variantes, nada o bate no cego 73,4); (d) o que falta é o que o olho usa: EXÓGENAS
(DXY/yields), relação ENTRE escalas, volume/SVP.

## 7. PLANO APROVADO PELO CRIS (próxima fase) — caso a caso + contexto exógeno
- FASE 0: fichas dos 7 casos (janelas <60%: V-turn 6,9 · nov/24 0 · range21-22 35,8 · bull-abr-jun21
  39,1 · bull-fev-abr22 53,8 · bear-gigante-bordas 59,7 · bear-jun-ago21 58,6). Estruturais viram
  ferramenta de DIAGNÓSTICO por caso + confirmação estreita (mtf acertou nov/24 100%).
- FASE 1: coletar DXY+US10Y diário (ideal 2012→; via MCP paginação no chart, aguarda autorização
  de janela) + SONDA de separação por caso ANTES de qualquer regra.
- FASE 2: regras de caso pré-registadas, uma a uma; aceitação congelada: resolve >50% do caso E
  dano ≤0 nas outras 18 janelas E racional causal físico; entram como EXCEÇÃO/REVIEW-LAYER com
  watch forward. DA por regra. Honestidade: n=1 por caso — validação real só com forward/GT longo.
- FASE 3: baseline manda + exceções estreitas; tabela 19 janelas antes/depois + k-fold r2 como
  não-regressão; plot canónico para visual do Cris.
- Alavanca opcional: Cris marcar GT 2012-2019 no diário (triplica episódios; 1D nativo já extraído).
