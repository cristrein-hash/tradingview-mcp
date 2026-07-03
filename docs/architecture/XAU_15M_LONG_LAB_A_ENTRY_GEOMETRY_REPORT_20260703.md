# LAB A RODADA 2 — ENTRY REDESIGN · RELATÓRIO (2026-07-03)

> Rodada 1 (execução pós-sinal, FAILS) no git history (c95d711). Esta rodada = redesenho amplo discovery-first (mandato Cris), Lab B dobrado para dentro. **Este relatório traz DADOS; não propõe finalização de processo** — continuidade é decisão do Cris. Fluxo: brief (`..._ENTRY_DISCOVERY_BRIEF_20260703.md`) → prereg (6 hipóteses congeladas) → execução → DA independente (1 bug material corrigido, re-executado) → este doc.

## 1. Baseline (fail-loud, reproduzida em toda execução)
N435 · WR_liq 46,0% · bruto +291,5 / **NET +233,6** · DD −14,2 · r/DD 16,4 · streak −8/+6 · anos 13,6/183,4/36,6 · 73% meses+ · pior mês −5,0 · runners 53. **FN-gate 4/6 — a própria base falha WR_liq≥50 e streak≤6** (referência para tudo abaixo).

## 2. STREAK_ANATOMY (diagnóstico comum, passo 0)
36 loss-runs ≥3: **15 intra-episódio · 20 dentro de ≤2 semanas · só 1 espalhada → 97% concentradas**. A dor de streak NÃO é espalhada — é cluster de calendário/episódio (padrão phase31/L2 confirmado no 15M).

## 3. Painéis (bruto | NET-SB $0,80; nulls pós-correção DA)

| Hipótese | N | WR_liq | NET | DD | r/DD | stk | runners | p(null) | kill |
|---|---|---|---|---|---|---|---|---|---|
| **BASE market@cj** | 435 | 46,0 | **233,6** | −14,2 | 16,4 | −8 | 53 | — | — |
| **P1 disp-early** (127 antecip.) | 435 | 46,7 | **257,1** | −13,5 | 19,0 | −8 | 56 | 0,726 | não |
| P2 stop-continuação (miss=0) | 435 | 38,2 | 162,8 | −8,8 | 18,5 | −13 | 38 | 0,650 | não (kill-PASS) |
| P3 skip-ceiling | 434 | 45,9 | 232,5 | −14,2 | 16,3 | −8 | 53 | 0,69-0,71 | não |
| P4 skip-capx | 287 | 45,3 | 142,0 | −16,7 | 8,5 | −7 | 35 | 0,70-0,72 | **SIM** |
| P5 budget (R ponderado) | 435 | 46,0 | 113,8* | −5,9 | 19,2 | −8 | 16* | — | não |
| P6 COMBO (≡P1) | 435 | 46,7 | 257,1 | −13,5 | 19,0 | −8 | 56 | 0,700 | — |

\*P5 em unidades ponderadas (0,5/0,3/0,2R por posição na cadeia) — não comparável 1:1; leitura honesta em §4.5.

## 4. Leitura por hipótese (dados + escopo obrigatório do DA)
1. **P1 TRIG_DISP_EARLY** — +23,5R pareado, DD/r-DD/runners/pior-mês melhoram, todos anos melhoram. **MAS**: (a) null justo timing-com-piso (med +28,8) → **p=0,726 = zero evidência de informação no deslocamento**; o ganho é mecânica de timing (entrar mais cedo/mais baixo com piso); o valor causal do disp lens é **controle de fantasmas** (147 entradas live-only custam só −2,3R); (b) classe fantasma não-coberta (fractais que falham confirmação — fora do dataset) estimada pelo DA em −2,2 a −3R → **tradeable honesto ≈ +252 NET (~+19R vs base)**; (c) residual dos gates cj (knife/h1_pos/HTF em p+1/p+2) declarado e NÃO bounded; (d) WR e streak NÃO mudam (falhas FN pré-existentes da base). Rótulo: **PROMISING_NEEDS_VISUAL** (com as 4 ressalvas acima carregadas).
2. **P2 EXEC_STOP_CONT** — **FAILS** no painel (−71R vs base; compressão de R por entry mais alto), robusto à física same-bar (±4,3R). **Achado valioso: kill-criterion PASSOU** — os 116 misses têm base-avgR −0,56 (são losers): o buy-stop de continuação tem a física de seleção INVERTIDA vs limit (rodada 1) como teorizado; ele filtra losers de verdade, só que paga caro demais nos winners. DD −8,8 e pior streak −13.
3. **P3 SKIP_CEILING** — **FAILS por vacuidade honesta**: corta 1/435. As lentes de teto (válidas no L2 4H) quase não disparam na base 15M porque **h1_pos/pos20/HTF-up já excluem contexto de teto** (lente supply: 20,1% do universo, 0,9% dos 435). Não há losers-sob-teto sobrando para cortar NA BASE FILTRADA.
4. **P4 SKIP_CAPX** — **KILL**: runner-kill 14 (critério duro), transferência de monotonicidade FAIL (s1 +0,92 > s2 +0,83; s0 +0,45 ainda positivo), −91,6R NET cortados. Descartado sem re-fitting (prereg).
5. **P5 EPISODE_RISK_BUDGET** — risco-normalizado: **R/unidade-alocada 0,537→0,572 (+7%) · DD obs −14,2→−5,9 · DD q95 bootstrap 22,7→9,8 · pior mês −5,0→−1,8** · NET absoluto cai a 49% (113,8). Streak em contagem invariante POR CONSTRUÇÃO (nota DA — não é achado). É contabilidade de risco, não seleção: reduz exposição aos clusters multi-stop que a ANATOMY mostrou serem 97% da dor.
6. **P6 COMBO** — só P1 sobreviveu ao gate individual → COMBO≡P1 (reconciliação exata).

## 5. Ledger de multiplicidade
7 tentativas (P1-P6 + absorption score pré-descartado no discovery). **Nada com p<0,05 sob nulls corretos.** Zero varredura/grid; agregações congeladas; runner-kill e kill-criteria aplicados como pré-registrados.

## 6. FundedNext gate (objetivo da rodada: WR≥50, streak≤5-6)
**Nenhuma hipótese move WR_liq ou streak** — P1 melhora lucro/DD/runners mas WR 46,7 e streak −8 seguem os da base; P5 reduz a PROFUNDIDADE da dor (DD/pior mês) sem mudar contagem. As alavancas testadas movem sumR/DD, não WR/streak. Dado para a continuidade (decisão Cris): o eixo WR/streak permanece não-resolvido pelas famílias trigger/execução/skip-convergente/budget desta rodada; a ANATOMY (97% cluster) aponta a natureza episódica/calendário da dor.

## 7. DA verdict (independente; não commitou — verificado)
1 bug material (null P1 sem piso → manchetes falsas; corrigido, re-executado, números deste doc = pós-correção, batem com verificação independente) + 1 bug de reporte (P5 streak trivial). P1/P5 = POSITIVO_COM_RESSALVA_GRAVE · P2/P3/P4 = CONFIRMA_NEGATIVO · P6≡P1. Doc: `XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_DA_20260703.md`.

## 8. Vereditos da rodada (por hipótese, sem finalização de processo)
- **P1: PROMISING_NEEDS_VISUAL** (~+19R tradeable, DD/runners melhores; sem info-edge sobre timing; residual declarado; exige builder re-scan p/ gates exatos em p+1/p+2 e reconciliação visual do Cris antes de qualquer status).
- **P2: FAILS** (painel) com kill-PASS registrado como conhecimento de física de fill.
- **P3: FAILS** (vacuidade na base — lentes de teto já cobertas pelos gates).
- **P4: FAILS** (KILL runner-kill+transferência).
- **P5: PROMISING_NEEDS_VISUAL** como camada de CONTABILIDADE (risk-shape), condicionada a decisão do Cris sobre trade-off lucro-absoluto × dor.
- **P6: ≡P1.**
Diferidas/registradas para rodadas futuras (do discovery, sem execução aqui): SL_CONTEXT (Lab C) · ladder pós-P2 · re-entry qualificada (Lab D) · box-pos estrutural do regime (Lab B r2) · confirmação especializada por regime (builder) · re-run integral sobre RAW estendido mar-jun/2026.
