# XAU 4H L2/BPT — SL Estrutural Trade-a-Trade

**Status:** `RESEARCH · NO_PRODUCTION · NO_SLIM · NO_PROMOTION · EXIT_FIXED_partial50` · **Data:** 2026-06-18
Constrói e mede políticas de SL estrutural causal para L2/BPT, exit FIXO **partial50@2R+6R**, sem mexer na entrada. 4 DAs (incl. um sobre este bloco). Look-ahead encontrado e corrigido por mim. NÃO promove estratégia.

---

## 1. Executive summary

Na base não-enviesada de **276 episódios**, **nenhum modelo de SL bate o baseline em R fora do ruído** (Δ avgR ~0.5 SE). O SL estrutural de swing-origin (**M5 = SL_STRUCTURE_LOW**, o SL que as anotações visuais do Cris apontam) **recupera mecanicamente os "bad_SL" curados 5→10/12**, melhora streak (12→9) e torna 2020-22 positivo (+5.3R vs baseline −0.9R) — **MAS** três ressalvas duras: (a) essa recuperação é **parcialmente circular** (os 12 bad_SL são *definidos* como "viram winner com SL estrutural"); (b) produz SL **operacionalmente inviável** (97/276 = 35% dos trades com SL >4ATR, **máx 15 ATR**); (c) **2 dos 9 winners (E13, E23) ainda stopam**, contradizendo a leitura visual → reconciliação pendente. Gap-aware fills testados (pedido do DA): **efeito desprezível** no ouro 4H. **Recomendação research-only:** o SL estrutural é correto em PRINCÍPIO mas precisa de **cap operacional (~4ATR)** para ser prop-firm-viável; o **M6 capped-hybrid** já mostra que uma versão limitada mantém quase todo o ganho (bad_SL 9/12, winners +17.6R, SL máx 4.72ATR) a sumR +69. **O SL NÃO é onde mora a edge** — entry-filtering e regime são alavancas maiores (DA). **Nada em produção.**

## 2. Why SL is the current focus

A reclamação visual nº1 do Cris (12 episódios `VALID_SETUP_BAD_SL`) é "winner morto por SL curto demais". O exit já foi aprovado (partial50@2R+6R) e fixado; BE rejeitado. O passo natural é medir se um SL estrutural real (não o low recente apertado) recupera esses winners sem inflar risco — trade-a-trade, recall-gate primeiro.

## 3. Inputs used (todos CURRENT/DIAGNOSTIC do inventário)

`pruned_base_v2.csv` (276 episódios) · `candidate_matrix.csv` (label + dist_pol_atr) · `full_res_visual_episode_review.csv` + `swing_anatomy.csv` + `visual_episode_labels.csv` (41 visuais) · `real_outcome.py` (SL baseline) · frozen 4H `/tmp/raw_features_2020_2026.jsonl` (com open/high/low/close) · `/tmp/XAU_1D_ohlc.jsonl`. Hard-stop de insumos: PASS (todos presentes/frescos).

## 4. Visual SL lessons from 41 episodes

- Em **TODOS** os valid_long o SL sugerido pelo Cris é **`SL_STRUCTURE_LOW`** (swing low de estrutura) — exceto **E40 = `SL_RETEST_LOW`** ("SL curto e eficiente"). Lição central: o SL correto é a **estrutura**, não o low recente apertado.
- `sl_origin_dist_atr` (swing anatomy): winners variam tight→moderado (E1 0.08, E40 0.19, E27 0.51, E30 0.75, E13 1.27, E5 1.62, E21 2.69, E17 0.74, **E23 4.73**); alguns SLFIX/REVIEW têm origem MUITO distante (**E14 6.66, E22 6.78, E24 5.22, E34 3.75**). Ou seja: o swing-origin às vezes é gigante — a raiz do risco operacional.
- 12 `bad_SL` = E2,E3,E4,E19,E20,E22,E28,E29,E31,E32,E38,E41. 9 winners GT = E1,E13,E17,E27,E30,E40,E21,E23,E5. should_not_long (macro-bear/trap) = E6-E11(parte),E15,E24,E34,E36,E37,E39.

## 5. SL model definitions (causais, não grid cego)

| Modelo | Definição | Stop |
|---|---|---|
| BASELINE | low recente 6-bar −0.1ATR, floor 0.3, SEM cap real (só flag) — `real_outcome.py` | intrabar |
| M1_RETEST_LOW | low recente 2-bar −0.1ATR, floor 0.3 | intrabar |
| **M2/M5_SWING_ORIGIN** | pivô Williams 5/5 mais recente abaixo da entrada −0.1ATR (= `SL_STRUCTURE_LOW`); **M5 só taggeia >4ATR/ideal2-4/tight** | intrabar |
| M3_DEMAND_BASE | menor pivô 5/5 nos últimos 30 bars abaixo da entrada −0.1ATR (proxy demanda; sem OB-zone offline) | intrabar |
| M4_POLARITY_CLOSE | nível de polaridade (entry − dist_pol_atr·ATR); sai no **CLOSE** abaixo −0.1ATR | close |
| M6_HYBRID | hierarquia demanda(≤4ATR)→swing(≤4ATR)→retest(LOW_CONF); limita SL operacionalmente | intrabar |

Causalidade: pivô Williams 5/5 em `j` só é confirmado em `j+5` → busca restrita a `j≤i−5` (**look-ahead corrigido**, 2 bars). Buffer 0.1ATR, floor 0.3ATR. **SEM teto 1.5ATR** (erro conhecido). Exit FIXO partial50@2R+6R. Fills **gap-aware** (preenche no open se o bar abre através do stop). Custo 0.10R.

## 6. Trade-by-trade SL classification (`results/l2_bpt_sl_structural_trade_review.csv`)

9 winners sob M5: salvam 7/9. **E13 (−1.1R stop, SL 2.87ATR) e E23 (−1.1R stop, SL 4.83ATR) STOPAM** apesar de anotados winner — **contradição visual, reconciliação pendente**. Mesmo os salvos E1/E17 saem mutados (+0.64R/+0.91R, SL 5.3/8.36ATR — o SL gigante encolhe o R-múltiplo e partial50 corta metade). 14 dos 41 visuais têm SL>4ATR (E1,E3,E9,E14,E15,E16,E17,E22,E23,E24,E33,E34,E36,E38).

## 7. Performance by SL model (full 276, partial50, gap-aware, cost 0.10R)

| Modelo | WR | avgR | sumR | medR | PF | maxDD | streak | SL ATR med/p90/máx | >4ATR |
|---|---|---|---|---|---|---|---|---|---|
| BASELINE | 42.8 | +0.286 | **+78.8** | −1.1 | 1.46 | 30.4 | 12 | 1.97/3.29/5.3 | 9 |
| M1_RETEST_LOW | 41.3 | +0.218 | +60.1 | −1.1 | 1.34 | **22.6** | 11 | 1.31/2.43/4.72 | 4 |
| **M2/M5_SWING_ORIGIN** | **48.2** | +0.226 | +62.5 | −0.11 | 1.44 | 24.3 | **9** | 3.06/6.38/**15.04** | **97** |
| M3_DEMAND_BASE | 48.6 | +0.207 | +57.2 | −0.07 | 1.43 | 25.8 | 11 | 3.82/6.92/15.04 | 132 |
| M4_POLARITY_CLOSE | 54.0 | +0.184 | +50.7 | +0.9 | 1.18 | **44.3** | **6** | 0.6/1.0/2.53 | 0 |
| **M6_HYBRID** | 44.2 | +0.25 | +69.0 | −1.1 | 1.42 | 25.7 | 12 | 2.14/3.59/**4.72** | **3** (97 LOW_CONF) |

Leitura: **BASELINE tight maximiza sumR (+78.8) mas falha os bad_SL (5/12) e é o mais choppy** (DD 30, streak 12). **M2/M5 estrutural: melhor WR/streak/medR, recupera bad_SL — mas 35% dos trades >4ATR (máx 15ATR)**. **M4 close-based: melhor streak(6)/WR(54) porém pior maxDD (44) e pior nos traps — REJEITADO** (risco de gap/stop apertado). **M6 hybrid: limita SL a 4.72ATR mantendo sumR +69 e winners, mas perde o ganho de streak (12) e vira "estrutural só no nome" em 97 LOW_CONF**.

## 8. Impact on monumentals / subsets

| Subset | BASELINE | M2/M5 | M6 | M4 |
|---|---|---|---|---|
| 9 winners (saved, sumR) | 7/9 +13.6R | 7/9 +13.7R | 7/9 **+17.6R** | 7/9 +11.2R |
| 12 bad_SL (saved) | **5/12** +0.2R | **10/12** +11.8R | 9/12 +10.3R | 7/12 +4.4R |
| 12 should_not_long (saved) | 0/12 −12.3R | 3/12 −6.2R | 2/12 −8.0R | 3/12 −23.4R |

- **bad_SL é a confirmação mecânica da tese do Cris** (tight 5/12 → estrutural 10/12) — porém **circular** (labels = "structural SL fixes these").
- **should_not_long:** o SL largo "resgata" 3/12 traps macro-bear (direção ERRADA — inflam WR; serão tratados pelo entry-filter humano futuro). Net ainda negativo (−6.2R), bom.
- **2 winners (E13,E23) nunca salvam** por nenhum modelo → problema é **upstream (entrada/estrutura)**, não SL.

## 9. Temporal split (sanity check, NÃO OOS limpo — regra usa 41 visuais de 2020-22)

| Modelo | 2020-2022 | 2023-2026 | único ano negativo |
|---|---|---|---|
| BASELINE | −0.9R streak11 DD30 | +79.7R streak12 DD16 | 2021 −19R |
| M2/M5 | **+5.3R** streak9 DD24 | +57.2R streak6 **DD9.2** | 2021 −12R |
| M6 | +16.3R streak11 | +52.8R streak12 | 2021 −14R |

Edge **não-estacionária** em todos (2020-22 pequeno, 2023-26 carrega). M2/M5 melhora o lado fraco (2020-22 positivo) e o holdout (streak 6, DD 9.2 vs 12/16). 2021 (bear) é o único ano negativo em todos.

## 10. Operational risk

**O risco decisivo (DA: FATAL para prop-firm):** R-normalização **esconde o risco em dólar**. M2/M5 tem 97/276 stops >4ATR, máx **15 ATR** — com sizing fracionário fixo, cada −1R num stop de 15ATR é **15× a perda em $** de um −1R baseline. "Menos −1R losses" é ilusão contábil; maxDD-em-R subestima o drawdown-$ real e estoura limites de daily-loss/sizing. **Por isso o SL estrutural puro (M5, sem cap) NÃO é operável como está.** M4 (close-based) tem risco de gap. Gap-aware fills testados: impacto <0.3R (ouro 4H quase não dá gap através do stop) — não muda o quadro.

## 11. Recommended SL policy (research-only)

**Princípio validado:** o SL deve ser a **estrutura** (swing-origin / `SL_STRUCTURE_LOW`), não o low apertado — recupera os bad_SL, melhora streak e o lado fraco 2020-22, e bate a leitura visual do Cris. **Mas exige cap operacional.**

- **Recomendado para o objetivo prop-firm:** **SL estrutural CAPADO em ~4ATR** (próxima iteração — neste bloco o Cris pediu só taggear >4ATR, não capar). O **M6_HYBRID** é o proxy capado disponível: bad_SL 9/12, winners +17.6R (o melhor!), SL máx 4.72ATR, sumR +69 — ao custo de streak 12 e 97 LOW_CONF.
- **M5 (swing-origin sem cap)** = referência estrutural; **não operável** pelos 97 trades >4ATR.
- **BASELINE tight** maximiza R total mas **falha o motivo do bloco** (bad_SL 5/12) e é choppy.
- **NÃO** reintroduzir teto 1.5ATR (mata monumentais). **NÃO** alterar o exit aprovado.

## 12. What remains unresolved

1. **E13/E23 stopam sob SL estrutural** mas são winners visuais → reconciliar (entrada mapeada ≠ entrada do Cris? swing-origin ≠ low estrutural que ele desenhou? partial50?). **UNTRUSTED até reconciliar.**
2. **Cap de 4ATR não testado** (Cris pediu só tag nesta rodada) — é a iteração natural que torna M5 operável.
3. **Circularidade** dos 12 bad_SL — recuperação esperada por construção; a base 276 (onde M5 não bate baseline em R) é o teste honesto.
4. **2 winners não-salváveis + 3 traps resgatados** apontam para **entry-filtering** como próxima alavanca (DA), não SL.
5. **Edge não-estacionária** (2020-22 fraco) persiste — fora do escopo do SL.
6. Diferenças entre modelos **dentro do ruído** (~0.5 SE) na base 276 — não promover nenhum por sumR isolado.

## 13. DA appendix

4 DAs nesta frente (regime/exit anteriores + 1 dedicado a este SL). Checklist deste bloco:
- **SLIM?** Não. **Futuro p/ escolher SL?** Não — look-ahead do pivô Williams (j≤i−5) **encontrado e corrigido por mim** antes de concluir; gap-aware fills implementados a pedido do DA. dist_pol_atr (M4) é feature de barra de entrada (estrutura passada reclaimed) — assumido causal; M4 rejeitado de qualquer forma.
- **SL depende só de info na entrada?** Sim (pivôs confirmados, low recente, polaridade passada).
- **Preserva monumentais?** 7/9 (E13/E23 reconciliação pendente); winners mutados por SL gigante + partial50.
- **Aumenta R artificialmente?** NÃO — M5 sumR (+62.5) < baseline (+78.8); melhora WR/streak/DD, não R.
- **Risco SL>4ATR reportado?** Sim — 97/276, máx 15ATR, FATAL prop-firm sem cap (§10).
- **Robusto por janela?** Não-estacionário; M2/M5 melhora ambas janelas mas edge concentrada 2023-26.
- **Teto 1.5ATR reintroduzido?** NÃO. **Exit alterado?** NÃO (partial50 fixo). **Produção?** Intacta. **Estratégia promovida?** NÃO.

**DA verdict (síntese):** SL não é onde mora a edge; na base não-enviesada os modelos estão dentro do ruído; a vantagem aparente do estrutural é (parcialmente) manufaturada pelos subsets curados + R-normalização escondendo risco-$ de 15ATR. Conclusão honesta: **adotar SL estrutural CAPADO em ~4ATR (princípio do M5, limite do M6) e redirecionar esforço para o ENTRY-FILTER** — onde vivem os 2 winners não-salváveis e os traps should_not_long. Research-only, nada promovido.

---

*Outputs: `results/l2_bpt_sl_structural_{trade_review,models,performance,temporal_split}.csv`. Script: `sl_structural.py`. Sem produção, sem SLIM, sem chart.*
