# DEEP ENGINE — DIFERENCIAÇÃO DO GRUPO-ALVO {T2,T3,T4,T16,T17,T23,T24}

**2026-06-22.** Bloco fechado. Diagnóstico nos 62 (ensino). Sem 276/OOS, sem chart/MCP, sem produção.
Rótulo = classe VISUAL do Cris (cega ao outcome — mistura winners T2/T24 e losers → contraste NÃO-circular).
Join seguro plot_id→datetime→84-stream + categoricais dos evidence packs = **matriz mestra 97 features**.
Scripts: `microstructure_deep_assemble.py` + análises inline. Evidência: `results/l2_bpt_deep_target7_findings.csv`,
`results/l2_bpt_deep_master_matrix_62.csv`.

## Resultado: **PARTIAL_SIGNAL (real, era-level) + os 7 NÃO são feature-separáveis dos outros B-preservados**

### O que encontrei de REAL e quantificável (auction-sólido, confirmado 2 formas)
**Eixo "clean-sky vs rompeu-supply-testada"** — descoberto por discriminação univariada (era-controlada) E
confirmado por **agente cego independente** (partição em 2 arquétipos, IDs opacos):
- Os winners do era choppy 2020-2022 entraram **SOB uma supply próxima já testada e ROMPERAM-na** (demanda
  vencendo resistência conhecida = follow-through). Assinatura "no_near_unbroken_supply": **30%**.
- O grupo-alvo entrou em **CLEAN-SKY / vácuo — sem nível testado acima para romper** (sem demonstração de força):
  **86%**. Agente cego: 5/7 do alvo no grupo "clean-sky" vs 8/10 winners no grupo "rompeu-supply".
- Insight de Auction Theory genuíno e novo: **num regime de range, comprar espaço-vazio (clean-sky) ≠ comprar o
  rompimento de uma resistência defendida.** O segundo demonstra demanda; o primeiro é fé.

### Auto-avaliação — 3 erros de caminho que refutei antes de reportar (disciplina pedida pelo Cris)
1. **legpos90/trend_30** (1ª pista): artefato de média — per-trade espalhado (T16 lp90=97, T17=23). DESCARTADO.
2. **macro/weekly/distribution** (2ª pista): spec_regime 6/7 MACRO_BULL = igual ao resto; F_STRICT_top_late tudo
   False; NAS/bubbles-sell 0% no alvo. DESCARTADO.
3. **clean-sky como o eixo do Cris** (3ª pista): **FALHA VALIDAÇÃO** — os 4 B-preservados que o Cris EXCLUIU
   (T18,T20,T30,T40) são 4/4=100% clean-sky, MAIS que o alvo. Logo clean-sky separa B-trades de A-winners, mas
   **NÃO isola os 7 específicos do Cris**.

### Prova decisiva do negativo (não-mascarada)
- **Cluster tightness (z-space, 65 features): ratio intra/inter = 1.03** — os 7 NÃO formam cluster (pior que
  grupos aleatórios 0.78-0.89).
- **ZERO features separam target-7 dos 4 excluídos** (T18/T20/T30/T40) — com 65 numéricas e 7-vs-4 o acaso geraria
  várias; há zero. Qualquer regra "7/7" é hull min/max = ID-fit (proibido).
- ⇒ **A distinção visual do Cris NÃO está presente no agregado de 97 features causais.**

### Hipótese para o "porquê" (re-confirma o arco macro engine)
Os 7 agrupam-se em **3 topos macro locais** (2020-03 COVID, 2021-11, 2022-03 guerra) que **precederam quedas**.
A comunalidade provável = **entrada perto de um topo macro que depois reverteu** — que é forward-looking à entrada
e **auction-irredutível** (o trap é feito idêntico à continuação). Isto re-confirma a conclusão central de toda a
frente: late-top/near-macro-top é visível em hindsight no gráfico, mas disfarçado nas features causais à entrada.
A peça que faltaria = **geometria de preço contígua** (a forma do topo macro) que não temos em série 2020-2026.

## Honestidade ao Cris
Fui fundo (4 famílias, era-control, 2 agentes cegos, validação cruzada, scan 7-vs-4) e **não consegui reproduzir
a tua distinção visual exata por features causais** — não por falta de profundidade, mas porque ela não está
codificada nos dados disponíveis. O que ENTREGO de real: o eixo **clean-sky-vácuo vs rompeu-supply-testada**
(novo, auction-sólido, separa B-trades de A-winners no era choppy a 86% vs 30%) — mas atinge 40% dos grandes
winners 2024-25, logo **NÃO é filtro promovível**, é **ingrediente de confluência / flag de contexto**.

## Rodada 2 — CONFLUÊNCIA EXAUSTIVA das features excluídas (pedido do Cris: "fraqueza isolada ≠ inútil")
Repeti à exaustão incluindo TODAS as 97+ features (mais as REFERENCE_ONLY/mortas `macro_leg_direction/phase`),
busca AND **1/2/3-way** sobre 177 literais (`deep_confluence_exhaustive.py`), com **TESTE DE PERMUTAÇÃO** como
guarda anti-ID-fit. Evidência: `results/l2_bpt_deep_confluence_permutation.json`.
- **Melhor confluência do alvo:** `spec_fuel==high_fuel AND d1_n_SH>=11 AND supply_blocks_2ATR==0` → captura
  **6/7** do alvo, **3/36** falsos, score 0.774.
- **TESTE DE PERMUTAÇÃO (decisivo):** 120 subsets-7 ALEATÓRIOS dos preservados; **20/120 atingem score ≥ alvo
  (p=0.167)**; null mediana 0.663, p90=0.774 (= o próprio score do alvo). ⇒ **a "melhor confluência" do alvo é
  estatisticamente indistinguível de hull sobre 7 trades quaisquer = ID-FIT, SEM sinal real.**
- **Conclusão da exaustão:** ir além de 3-way só aumenta o overfit (mais literais = mais hulls), não o sinal.
  A confluência das features excluídas **não revela** um diferenciador real dos 7 — confirma o negativo da rodada 1.

## Próxima recomendação
Se queres que eu chegue exatamente aos 7, o ingrediente que falta é a **geometria do topo macro** (sequência de
swings / forma do rollover) — só derivável de série OHLC contígua 2020-2022 (que não temos). Alternativa: tu
apontares QUAL traço visual vês nesses 7 (ex.: "todos compram o 2º teste de uma máxima", "todos sem pullback a
demanda recente"), e eu testo esse traço específico causalmente. Sem isso, a evidência diz: **não-separável /
near-macro-top auction-irredutível**, com o eixo clean-sky como único diferencial parcial real.
