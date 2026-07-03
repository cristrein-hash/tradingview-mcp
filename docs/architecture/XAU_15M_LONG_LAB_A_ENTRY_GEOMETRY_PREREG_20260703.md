# LAB A — ENTRY REDESIGN · PRÉ-REGISTRO RODADA 2 (2026-07-03, ANTES de qualquer cálculo)

> **RODADA 2** — substitui o prereg da rodada 1 (execução pós-sinal, FAILS; íntegra no git history, commit c95d711). Hipóteses desta rodada = derivadas do discovery multi-agente (`XAU_15M_LONG_LAB_A_ENTRY_DISCOVERY_BRIEF_20260703.md`; síntese integral em `research/xau_15m_bb_nas_leonardo/results/lab_a2_discovery_synthesis.json`). Lab B (cuts de losers) DOBRADO para dentro por ordem do Cris.

## 1. Scope
XAU 15M LONG only · swept-runner base #4 (OFICIAL_FN, NOT production) · N435 · detector v5 hour-causal retido · **SB $0,80 líquido obrigatório em toda avaliação** · sem SHORT · sem produção/Telegram/chart/plot/RAW-write · commit só do orquestrador, subagents nunca.

## 2. Source/data mapping
Idêntico à rodada 1: 435 sinais do engine real via exec (`engine_substrate4_v5_hourcausal.py`, `cand[v5h≠BEAR]`); séries por bloco (`PRIMK[block]["series"]`); **universo pré-gate `entry_candidates_htf.jsonl` (4502 candidatos, ~60 features causais)** — novidade da rodada: usado para phantom scan (P1), quantis de lentes (P3/P4) e histogramas universo-vs-435. Lineage RAW-only, zero SLIM. Episódio: cadeia gap ≤96 barras com stop anterior não-resolvido (P5; congelada).

## 3. Baseline reproduction (fail-loud, JOIN — nunca re-derivação silenciosa)
N435 · WR47,6% · **+291,5R bruto** · **+233,6R líquido-SB** · DD−14,2/r-DD16,4 (SB) · streak−8 · anos 39,7/213,6/38,3. Não bater → PARAR.

## 4. Hipóteses pré-registradas (6, definições congeladas — fonte: síntese do discovery, verbatim no JSON)

### P1 — TRIG_DISP_EARLY (trigger_redesign)
Antecipação p+1/p+2 se **3 lentes TODAS**: close>high[p] · corpo≥0,5·ATR da barra · close>ema21. **Piso de risco:** se risk_usd<$6,40 (=8×RT) OU risco<0,35·ATR → NÃO antecipa. Senão fallback = base exata (close@cj). SL=flush−0,1ATR nos 2 ramos. UMA geometria, zero grid. Gates recomputados na barra de decisão **onde os dados permitem** (regime v5, rsi, pos20, swept-invariante, ema); KNIFEKILL/h1_pos/HTF do snapshot cj = **residual declarado** (brief §6), bounded por phantom scan no universo (entradas fantasma contadas e custeadas via letrun → painel tradeable-lower-bound). Pareado por episódio. **Null:** antecipação aleatória da mesma fração (500 reps) + jackknife-episódio + decomposição população-vs-timing. **Kill:** pareado mostrando que fundos que deslocam cedo teriam sido melhores entrando em cj → fecha.

### P2 — EXEC_STOP_CONT (execution_redesign)
No close de cj: buy-stop em **max(high[p..cj])+0,05·ATR_cj**, validade W=8, cancela se low tocar SL antes do fill; fill THROUGH (high≥stop+$0,40; gap→open). SL=flush−0,1ATR; risco=fill−sl (maior). Âncora única, zero grid. Same-bar stop+fill → −1 (conservador, declarado). **Null:** cancelamento aleatório mesma fração (500 reps). **Kill inegociável:** base-avgR dos misses deve ser ≤0; misses winners (como no limit) → DISCARD imediato sem iteração.

### P3 — SKIP_CEILING (labB_fold_skip)
4 lentes booleanas no cj (quantis no universo 4502): L1 n_supply_overhead≥q0,80 · L2 legpos90≥0,75 · L3 h1n_clean_sky_atr≤0,35 (99=céu limpo=FALSE) · L4 sell_bub_w≥1. **SKIP se ≥3/4.** Pesos uniformes, k=3 congelado, UMA config. **Pré-check:** corr par-a-par das lentes; par>0,8 → substituir por h1_rsi esticado (pré-declarada). **Null triplo:** cortes aleatórios mesmo N (500) · score permutado (500) · leave-episódio (atenção clusters ago/2025+jan/2026). Nenhum episódio >15% do delta. **Kill duro:** runner-kill (corte de trade R≥+4) = 1 → DISCARD.

### P4 — SKIP_CAPX (labB_fold_skip)
cap_score 0-5 (barras ≤cj, direto do ROWS): +1 sell_bub_w>0 · +1 downleg_eff≥0,45 · +1 downleg_decel==0 · +1 pullback_depth≥0,6 · +1 low_wick<0,5. **SKIP se cap_score≤1** (fundo sem capitulação legítima). Thresholds CONGELADOS (scan exploratório do discovery; 1º score [absorption] falhou lá e conta como tentativa no ledger). TRAP-BUY = leitura secundária (dupla contagem declarada). **Null:** permutado + cortes aleatórios (500) + leave-episódio. **Kill:** monotonicidade não transfere para R dos 435 → DISCARD sem re-fitting. Runner-kill duro idem P3.

### P5 — EPISODE_RISK_BUDGET (episode_level, contabilidade não seleção)
**Passo 0 obrigatório (diagnóstico comum): STREAK_ANATOMY** — loss-runs ≥3/≥5 decompostas por episódio-id e semana; se streak espalhada → NÃO RODAR o budget (negativo registrado). Regra: 1ª entrada do episódio 0,5R · 2ª 0,3R · 3ª+ 0,2R (partição única congelada; pertença: stop anterior não-resolvido, região de flush compartilhada, ≤96 barras). **Null:** bootstrap de sequência por blocos de episódio (≥1000 reps) vs baseline 1R/trade + jackknife.

### P6 — COMBO (trigger×skip, composição congelada ANTES dos resultados componentes)
COMBO = (P1 se passar gate individual, senão cj) + (união dos SKIPs P3/P4 sobreviventes). Skip decidido no cj-candidato antes do ramo de antecipação. Zero re-tuning; 1 variante no ledger. **Null COMBINADO** (antecipação aleatória × cortes aleatórios, 500 reps) — combo tem de bater o null combinado; reconciliação contábil componentes+interação fail-loud; nenhum episódio >15%.

## 5. Protocolo de avaliação (comum, pré-registrado — 14 exigências do DA-pré, integral no JSON)
1. **LEDGER único de variantes** (incluindo descartadas: absorption score) — Bonferroni informal.
2. Reprodução fail-loud por JOIN (§3) antes de qualquer variante.
3. **Anti-look-ahead automatizado:** assert de que triggers pré-cj não usam snapshot cj nos campos recomputáveis; residual declarado (brief §6) reportado com bound.
4. Decomposição população-vs-timing quando barra de decisão ≠ cj.
5. **Streak SÓ distribucional:** bootstrap por blocos de episódio ≥1000 reps + distribuição de loss-runs ≥3/≥5. STREAK_ANATOMY roda ANTES de qualquer claim.
6. Agregações congeladas (zero varredura; null permutado obrigatório para scores).
7. Nulls por família: skips = cortes aleatórios N + permutado + leave-episódio; triggers = antecipação/cancelamento aleatório; combo = null combinado.
8. **Runner-kill duro:** nenhum trade R≥+4 cortado (1 = DISCARD); runners ≥48/51 no painel final.
9. Painel bruto E líquido-SB $0,80 sempre, completo (N·WR·sumR·avgR·DD·r/DD·streak·por-ano) + % meses positivos + pior mês.
10. **GATE FUNDEDNEXT comum (congelado):** WR_liq≥50% · max-streak≤6 (distribucional) · runners≥48/51 · sumR_liq≥200R · 3 anos positivos líquidos com 2024≥+10 · cost_R mediano ≤0,15.
11. Kill-criteria por hipótese (§4) inegociáveis.
12. Sanity 3 exemplos pass/fail/borderline por hipótese com timestamps.
13. Governança: zero commit por subagents; zero push; zero RAW/chart/produção; forbidden paths da rodada 1 vigentes.
14. **Sem conclusões/finalização:** relatório traz DADOS + vereditos por hipótese (opções: ENTRY_REDESIGN_CANDIDATE_FOUND · PROMISING_NEEDS_VISUAL · FAILS · BLOCKED_BY_DATA · DISCOVERY_ONLY_NO_EXECUTION_SAFE); continuidade decidida pelo Cris.

## 6. Outputs
Script: `research/xau_15m_bb_nas_leonardo/lab_a_entry_geometry_analysis.py` (reescrito, rodada 2) · Report: `XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_REPORT_20260703.md` (reescrito) · DA: `..._DA_20260703.md` (reescrito) · síntese discovery já versionada. Commit único: `"Run XAU 15M long entry redesign lab"` — **sem push sem autorização**.
