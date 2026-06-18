# XAU 4H L2/BPT — Design do engine multiagente especialista por trade

**Status:** `DESIGN ONLY · NOT IMPLEMENTED · NO CODE CHANGED · NO OPTION B` · **Data:** 2026-06-19
Desenho de uma arquitetura para potencializar o TAKE engine: de **fan-out genérico por lote** para **análise multiagente especializada por trade**, observável/calibrável/auditável. **Nada implementado.** Foundation: [[XAU_4H_L2_BPT_AGENT_RUBRIC_AUDIT]] · [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]].

> **Trava:** este bloco é só design. NÃO alterar engine/rubrica/decisões congeladas. A implementação é um bloco futuro separado, fase a fase, cada fase comparada contra o engine atual antes de promover.

---

## 1. Problemas do fan-out atual (da auditoria, commit 99a349c)
- **Fan-out por lote, não ensemble:** cada trade decidido por **1 agente**; 0 trades com >1 decisão; **sem voto/consenso/debate/DA-por-trade/agregador**.
- **Confidence não calibra** (Spearman conf×realR = −0.02) → opinião subjetiva inútil como peso.
- **setup_type circular** (~colinear com a decisão: late_top=77/77 SKIP; bottom_reversal=0 SKIP) → rótulo = decisão relabelada.
- **Fatores citados não separam TAKE-winner de TAKE-loser** (n17/15, citações ~idênticas) → narrativa plausível, não causal.
- **supply_distance "usado 83%" era artefato** de regex (mediu o input do packet, não a cognição; flag⊂distance).
- **Sinal real existe na DECISÃO** (TAKE +0.91R/53% vs SKIP +0.06R/21% = gradiente monotônico) → o **gestalt funciona**; o que falha é a *prova* escrita.

**Implicação de design (crucial):** o objetivo NÃO é matar o gestalt (ele é o que funciona) — é torná-lo **observável e auditável** SEM transformá-lo num checklist mecânico que destrói a leitura holística. Os especialistas geram **evidência estruturada**; o aggregator preserva a **integração contextual**.

## 2. Nova arquitetura (por trade, em camadas)
```
1 trade (packet de 84 fatores causais, cego ao outcome)
  → STAGE A: Context Classifier (setup_type, CEGO à decisão final)
  → STAGE B: 6 especialistas analisam o MESMO trade (evidência estruturada)
  → STAGE C: Devil's Advocate ataca a tese
  → STAGE D: Aggregator decide TAKE/REVIEW/SKIP (rubrica verificável)
  → registro auditável (evidência + conflito + decisão) → outcome medido depois
```
Diferença vs atual: o MESMO trade passa por papéis distintos (cruzamento real), não "1 agente decide sozinho".

## 3. Papéis dos agentes especialistas
| # | agente | missão (lente única) | NÃO faz |
|---|---|---|---|
| A | **Context Classifier** | classifica setup_type (bottom_reversal/demand_reclaim/bull_pullback/late_top/bear_bounce/unclear) | NÃO decide TAKE/SKIP (separação anti-circular) |
| 1 | **Macro/Regime Reader** | trend_30/90, rsi_1d vs MA, price_vs_sma50, regime bull/bear/chop | ignora microestrutura |
| 2 | **Demand/Supply Reader** | demand-distance/width/touched, **supply-distance contínua**, blocks_target, D1 zones | ignora momentum |
| 3 | **Exhaustion/Top Risk Reader** | legpos90, rise20, rsi overbought, bear-div (A7), F_STRICT, blow-off, climax bubbles | ignora fundo |
| 4 | **Capitulation/Reversal Reader** | drop20, rsi_min8, sweet-spot falling-knife, below-VAL, SELL-bubble absorção, NAS LONG | ignora topo |
| 5 | **Entry Quality Reader** | reclaim body, CHoCH/BOS recência+direção, demand-retest timing, premature vs late | ignora risco |
| 6 | **Risk/SL Reader** | sl_atr, sl_type (V_REVERSAL/NORMAL/LATE_WIDE), demand-anchored quality, target reachability vs supply | ignora tese |
| DA | **Devil's Advocate** (§9) | atacar a tese: bull-beta? topo? supply perto? SL estrutura-fraca? loser parecido? | não decide |
| AGG | **Final Aggregator** (§10) | integra evidências + veredito DA → TAKE/REVIEW/SKIP + registro | não inventa fatores |

## 4. Input obrigatório por agente (Q1, Q2)
- **Q1 — transformar 84 fatores em input estruturado:** o packet vira um **dicionário tipado** `{factor: {value, unit, source, causal:true, null:bool}}`. Cada agente recebe o packet COMPLETO (para contexto) MAS tem um **subconjunto OBRIGATÓRIO** que deve avaliar e citar (abaixo). Assim a leitura holística é preservada, mas a cobertura é forçada.
- **Q2 — fatores obrigatórios por agente:**
  - Macro: trend_30_atr, trend_90_atr, rsi_1d, rsi_1d_sub_ma, price_vs_sma50, dist_sma50_atr.
  - Demand/Supply: dist_4h_demand_low_atr, demand_touched_on_retest, demand_width_atr, **dist_4h_supply_low_atr**, supply_blocks_2ATR, supply_rejected_before, has_d1_demand, has_d1_supply.
  - Exhaustion: legpos90, rise20_atr, rsi, rsi_bear_div_20b, F_STRICT_top_late, bub_large_buy_10b.
  - Capitulation: drop20_atr, rsi_min8, sweet_spot_falling_knife, below_VAL, bub_sell_total, nas_long_new_8b.
  - Entry: reclaim_body_atr, smc_choch (bars_ago+dir), smc_bos, reclaim_dist_from_demand_atr.
  - Risk/SL: sl_atr, sl_type, dist_4h_demand_low_atr, supply_blocks_2/3ATR, dist_POC_atr.
- Cada agente deve emitir verdict para CADA fator obrigatório (mesmo que "neutral/unavailable") → cobertura auditável.

## 5. Output estruturado obrigatório (Q3, Q4)
Cada agente devolve uma **tabela de evidência** (não narrativa). Por fator avaliado:
```json
{"factor_used":"dist_4h_supply_low_atr","value":1.42,"interpretation":"supply close but not immediate (1.4 ATR)",
 "impact":"negative","confidence_local":"medium","role":"decisive|supporting","caveat":"binário blocks_2ATR=1 confirma"}
```
E um resumo por agente: `{lens, top_evidence:[...], net_read:"supportive|neutral|hostile", missing_data:[...]}`.
- **Q3 — impedir repetir texto do packet:** validação programática — `factor_used` deve estar nos 84 fatores E `value` deve **bater com o packet** (tolerância). Se citar fator inexistente ou valor divergente → **rejeitar a evidência** (não conta). Assim "citou" = "leu o campo certo com o valor certo", não eco do texto.
- **Q4 — exigir campo+valor+interpretação:** schema acima é obrigatório; `interpretation` deve referenciar o `value`; `impact` ∈ {positive,negative,neutral}. Sem os 3, a evidência é descartada.

## 6. Como evitar narrativa post-hoc (Q10)
- **Toda explicação vira tabela `factor → value → interpretation → impact`** (não prosa).
- **Validação cruzada com dados:** após N trades, medir por fator: aparece mais em TAKE-winner ou TAKE-loser? (o teste que a auditoria fez e que hoje mostra "indistinguível"). Um fator citado como "decisive" que não separa win/lose vira **suspeito de narrativa** e é despromovido.
- **decisive vs supporting:** só fatores marcados `decisive` entram no gate do aggregator; o resto é contexto. Isso força o agente a comprometer-se com poucos fatores reais.

## 7. Separar contexto/setup da decisão (Q5)
- **Stage A (Context Classifier)** roda PRIMEIRO e CEGO à decisão final: só classifica setup_type a partir dos fatores. Não vê TAKE/SKIP, não os produz.
- **Stage D (Aggregator)** decide TAKE/REVIEW/SKIP DEPOIS, recebendo o setup_type como UM input entre vários.
- **Teste de não-circularidade:** medir se setup_type prediz outcome **controlando pela decisão** (dentro de cada decisão, bottom_reversal vs late_top separam R?). Se setup_type só prediz porque = decisão, ele é circular e deve ser despromovido a contexto puro.

## 8. Calibração empírica de confidence (Q6)
- **O LLM NÃO inventa confidence livre.** Cada agente dá `confidence_local` categórica (low/medium/high) só como evidência.
- **Confidence final = função empírica posterior:** depois de um conjunto de trades com outcome, ajustar um mapa `(features do aggregator) → P(win)` calibrado (ex.: isotonic/Platt sobre um score composto auditável). Até existir esse histórico calibrado, **confidence é texto decorativo, não métrica** (como hoje, ρ≈0).
- **Nunca** usar a confidence subjetiva do LLM como peso de decisão.

## 9. Devil's Advocate por trade (Q7)
Para cada candidato a TAKE, um agente DA dedicado **tenta refutar**, respondendo objetivamente:
- É só **bull-beta** (dip num uptrend secular que sobe de qualquer jeito)?
- Está comprando **topo/blow-off**?
- **Supply** perto demais (target 2R inalcançável)?
- SL depende de **estrutura fraca**?
- Há **exemplo parecido que perdeu** (loser conhecido)?
Saída: `{objection: text, severity: low/medium/high/fatal, factor_evidence:[...]}`. **DA com objeção `high`/`fatal` → TAKE cai para REVIEW** (ou SKIP se fatal). DA é obrigatório e estruturado (mesmo schema de evidência), não opinião solta.

## 10. Como o aggregator decide (Q8, Q9)
Rubrica **verificável** (não fórmula rígida, mas regra auditável):
```
TAKE  só se: (a) tese principal clara (Context + ≥1 lente decisive forte alinhada);
             (b) ≥3 confluências fortes INDEPENDENTES (de lentes distintas, marcadas decisive);
             (c) nenhum VETO crítico (F_STRICT severo / supply target-blocking / SL LATE_WIDE blow-off);
             (d) risco/SL aceitável (sl_type ∈ {V_REVERSAL, NORMAL});
             (e) DA não encontra objeção high/fatal.
REVIEW: tese parcial OU 2 confluências OU DA objeção medium OU risco ambíguo (human-in-loop).
SKIP:  sem tese / veto crítico / DA fatal / confluências insuficientes.
```
- **Q9 — registrar conflito:** o aggregator grava o **mapa de leituras** (Macro: supportive/neutral/hostile · Demand: strong/weak/absent · Supply: clean/capped/dangerous · Exhaustion: low/med/high · Entry: good/late/premature · Risk: good/poor · DA: pass/fail) + onde as lentes DISCORDAM (ex.: Capitulation=supportive vs Exhaustion=high → conflito → REVIEW). O conflito é um SINAL, não escondido.

## 11. Reasoning auditável registrado (Q12)
Por trade, persistir: packet usado (hash), setup_type (Stage A), tabela de evidências de cada lente, objeção do DA, mapa de leituras + conflitos, decisão do aggregator + regra acionada (qual cláusula a-e), e os `decisive` factors com value. **Tudo reproduzível dado o mesmo packet + mesmo model/prompt** (reasoning segue não-determinístico, mas o REGISTRO é completo e auditável → AI_REVIEW de verdade, não caixa-preta).

## 12. Comparar engine antigo vs novo (Q11)
- Rodar o NOVO sobre os **mesmos 276 episódios 2020-2026** (mesmos packets, mesmos outcomes; decisões antigas CONGELADAS como baseline, não tocadas).
- **Métricas de superioridade:** (1) TAKE>SKIP gradiente maior; (2) **os `decisive` factors agora SEPARAM win de loser** (o que hoje falha) — teste por fator win-vs-lose; (3) menos dos 27 missed-winners perdidos; (4) conflito-alto prediz outcome pior (utilidade do disagreement); (5) bate baselines (legpos-random, state-matched, SL-matched) como o atual; (6) bootstrap + held-out NON-GT.
- **Gate de promoção:** o novo só substitui o atual se bater o gestalt atual fora do ruído E os `decisive` factors forem causalmente separadores (não narrativa). Senão, mantém o atual (gestalt) + usa o novo só como camada de AUDITORIA/explicação.

## 13. Riscos
- **Destruir o gestalt:** forçar checklist estruturado pode reduzir a leitura holística que HOJE funciona → o gate §12 deve provar que o novo ≥ atual, senão não promove.
- **Custo/tokens:** 8 agentes/trade × 276 = muito mais caro; mitigar com tiering (DA só em candidatos a TAKE).
- **Colusão/eco entre agentes:** se os especialistas virem o mesmo packet, podem convergir trivialmente; mitigar com lentes realmente disjuntas + DA adversário.
- **Calibração precisa de N grande:** confidence calibrada exige histórico; até lá, decorativa.
- **DA circular:** o DA pode "refutar bonito" sem dado → exigir factor_evidence estruturada nele também.
- **Overfit do aggregator:** a regra a-e não pode ser tunada aos 276 (in-sample) → pré-registrar antes de medir.

## 14. Plano de implementação futura (fases, NÃO agora)
1. **Fase 0:** schema de evidência + validador (factor_used∈84 ∧ value==packet) + packet tipado. (infra, sem decidir nada)
2. **Fase 1:** Stage A (Context Classifier) isolado + teste de não-circularidade (§7).
3. **Fase 2:** 6 especialistas + DA, schema estruturado, num SUBSET pequeno; medir se `decisive` factors separam win/lose.
4. **Fase 3:** Aggregator com rubrica pré-registrada; rodar nos 276; comparar vs atual (§12).
5. **Fase 4:** calibração posterior de confidence; só então confidence vira métrica.
6. **Fase 5 (só se §12 passar):** promover; aplicar a Opção B (2013-2017) como AI_REVIEW declarado.

## 15. O que NÃO implementar agora
Nada de código. Nada de rodar agentes. Não tocar engine/rubrica/decisões 2020-2026. Não rodar Opção B. Não calibrar. Não criar os schemas em código. Este bloco entrega **só o design**; cada fase do §14 é um bloco futuro com gate próprio.

---
*Design. Sem código alterado, sem validação, sem produção/chart/plot/SLIM. Próximo passo (se Cris autorizar): Fase 0 (infra de schema/validação), isolada.*
