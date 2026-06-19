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

## 3. Papéis dos agentes especialistas (roster expandido — mesa de análise por família de evidência)
**Avaliação da proposta do Cris:** correta e mais forte que a v1 (8 papéis) — especialistas por indicador/família com mandato técnico estreito e evidência estruturada, agregador construindo TESE. Incorporada + ampliada com os edges validados do projeto (capitulação, sweep, bull-beta skeptic, Dead Hours, HTF) + o framework de valor-marginal (§3c) que impede "mais narradores".

### 3a. Roster (Stage A + 20 especialistas + DA + Aggregator)
| # | agente | lente ÚNICA e técnica (mandato estreito) | fatores-fonte obrigatórios |
|---|---|---|---|
| A | **Context Classifier** (cego à decisão) | classifica setup_type, SEM TAKE/SKIP | todos (resumo) |
| 1 | **Macro/Regime/Leg Reader** | regime bull/bear/chop, maturidade da perna | trend_30/90_atr, slope20, price_vs_sma50, dist_sma50 |
| 2 | **HTF/Daily-Context Reader** ⊕ | alinhamento 1D/semanal, gate diário (causal shift1) | rsi_1d, rsi_1d_sub_ma, has_d1_demand, dist_d1_demand_atr, has_d1_supply, dist_d1_supply_atr, macro_leg_* |
| 3 | **Auction Theory / Market-Structure Reader** | balanço vs imbalance, aceitação/rejeição, POC magnet | below_VAL, dist_POC_atr, dist_VAL_atr, va_width_atr |
| 4 | **Demand & Supply Quality Reader** | demanda defendida/colada, **supply-distance contínua**, espaço limpo até resistência | dist_4h_demand_low_atr, demand_width/age/touched, **dist_4h_supply_low_atr**, supply_blocks_2/3ATR, supply_rejected/broken_before |
| 5 | **Volume / Session VP / Absorption Reader** | volume real confirma capitulação? absorção vs distribuição | rel_volume, below_VAL, dist_POC/VAL_atr, va_width_atr |
| 6 | **NAS Specialist** | NAS LONG/BOTTOM/TOP relevante, first-appearance vs ruído, alinhado a fundo/topo/meio | nas_long_new_8b, nas_short_new_8b, nas_dist_ema_atr, nas_rsi, nas_1d_long_recent |
| 7 | **Market Order Bubbles Specialist** | absorção SELL pré-reversão, BUY-climax em topo, tier s/m/L, antes/depois da entrada | bub_sell_s/m/L, bub_buy_s/m/L, bub_buy_sell_ratio, bub_large_sell/buy_10b, bub_poc_recent |
| 8 | **RSI / Divergence / Momentum Reader** | oversold/neutro/overbought, divergência real, força vs blow-off | rsi, rsi_min8, rsi_max8, rsi_vs_ma, rsi_bear_div_20b, rsi_bull_div_20b, rsi_drop_6b |
| 9 | **SMC / BOS / CHoCH / Liquidity-Structure Reader** | BOS/CHoCH relevante vs ruído local, reclaim estrutural vs geométrico, polaridade defendida, LH-bear vs HL-reversão | smc_bos(text/bars_ago), smc_choch, reclaim_dist_from_supply/demand_atr |
| 10 | **Custom OB / Demand-Origin Reader** | OB de origem-de-perna, OB 1D, qualidade da zona | demand_origin_of_leg, demand_age_bars, has_d1_demand, dist_d1_demand_atr |
| 11 | **Capitulation / Climax-Wash Specialist** ⊕ | fundo: falling-knife, washout, climax (Tipo 1 silent / Tipo 2 climax F9) — distinto de exaustão de topo | drop20_atr, rsi_min8, sweet_spot_falling_knife, consec_down, below_VAL, range_exp, bub_large_sell_10b |
| 12 | **Liquidity Sweep / Stop-Run Specialist** ⊕ | varreu low estrutural e reclaimou? (BASE+SWEEP validado V1.4g) | low pivots (PL5), reclaim_body_atr, smc_choch, legpos60/90 |
| 13 | **Exhaustion / Top-Risk Specialist** | topo: blow-off, overbought, F_STRICT, distribuição, bear-div | legpos90, rise20_atr, rsi, rsi_bear_div_20b, F_STRICT_top_late, bub_large_buy_10b, nas_short_new_8b |
| 14 | **Entry Timing / Reclaim Quality Reader** | reclaim confirmado vs prematuro/tardio, corpo bullish, retest da demanda | reclaim_body_atr, demand_touched_on_retest, smc_choch bars_ago, consec_up |
| 15 | **Risk / SL / R-Geometry Reader** | SL demand-anchored quality, alcançabilidade do alvo 2R/6R vs supply, R/R | sl_atr, sl_type, dist_4h_supply_low_atr, supply_blocks_2/3ATR, dist_4h_demand_low_atr |
| 16 | **Session / Time-of-Day Specialist** ⊕ | Dead Hours (UTC 2/18/20), London/NY, dia | hour_utc, dead_hour |
| 17 | **Historical Analogues Specialist** | parecido com winners E1/E17/E27/E30/E40 ou losers E23/E24/E15/E34/E39? (por PERFIL de fatores, não outcome leak) | vetor dos eixos-chave; assinaturas na rubrica |
| 18 | **Bull-Beta / Drift Discriminator** ⊕ (modo de falha #1) | é edge ou só long-gold beta? um random long no mesmo regime faria isso? | trend_90_atr, regime, legpos, rel_volume; cruza com baseline-mental |
| 19 | **Volatility / ATR-Regime Reader** ⊕ | ATR percentil, spike de vol (entrada engole noise), regime de vol | atr_level, atr_pctile_proxy, range_exp |
| 20 | **Anti-Look-Ahead / Causality Auditor** ⊕ | todos os fatores são ≤ entrada? algum repinta (SMC/bubbles/OB)? | meta: flag de causalidade por fator |
| DA | **Devil's Advocate** (§9) | refutar a tese com evidência estruturada | conforme objeção |
| AGG | **Final Aggregator / Trade Qualification** (§10) | constrói a TESE + decide TAKE/REVIEW/SKIP | mapa de leituras + DA |

⊕ = adicionado por mim além dos 14 do Cris. Especialistas com fonte sobreposta (ex.: RSI #8 vs Exhaustion #13 vs Capitulation #11 todos tocam RSI) são **deliberadamente disjuntos no MANDATO** (#11 só fundo, #13 só topo, #8 só momentum puro) e validados por ablation (§3c) — quem não agrega valor marginal é cortado.

### 3b. O agregador constrói uma TESE (não soma votos)
O Aggregator NÃO conta votos. Ele formula a **tese principal** ("bottom reversal com capitulação + demanda defendida" / "bull pullback saudável" / "late top / no trade" / "bear bounce perigoso") a partir das leituras, e só então qualifica (§10). A tese é registrada e auditável.

### 3c. Valor marginal por especialista (a TRAVA anti-narrativa — o que faltou no engine atual)
Cada especialista SÓ permanece no roster se **provar contribuição marginal**, medido offline sobre os 276 (sem retune):
- **Ablation:** remover o especialista X piora o gradiente TAKE>SKIP / o lift vs baseline? Se não → REDUNDANTE → cortar ou fundir.
- **Separação win-vs-lose:** os fatores que o especialista X marca `decisive` realmente aparecem mais em winners que em losers? (o teste que HOJE falha). Se não separa → o especialista vira CONTEXTO, não decisive.
- **Redundância:** correlação das leituras entre especialistas; se #8 e #13 sempre concordam, fundir.
- **Não-circularidade:** Historical Analogues #17 e Bull-Beta #18 NÃO podem usar outcome; só perfil de fatores / regime.
Resultado: um roster ENXUTO comprovado, não 20 narradores. O número final de especialistas é EMPÍRICO (pode ser <20), definido pelo ablation, não pela vontade.

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
- **Custo/tokens:** ~20 especialistas + DA + AGG por trade × 276 = MUITO caro; mitigar com **tiering** (rodar especialistas baratos primeiro; DA + especialistas caros só em candidatos a TAKE/REVIEW) e com o **roster enxuto pós-ablation** (§3c — menos agentes comprovados).
- **Colusão/eco/redundância:** muitos especialistas tocam fatores sobrepostos (RSI aparece em #8/#11/#13) e veem o mesmo packet → podem convergir trivialmente ou inflar narrativa (o erro da auditoria). Mitigar com: mandatos REALMENTE disjuntos (§3a), **ablation + correlação de leituras (§3c)** que corta redundantes, e DA adversário. **Mais especialistas ≠ mais sinal até o ablation provar contribuição marginal.**
- **Calibração precisa de N grande:** confidence calibrada exige histórico; até lá, decorativa.
- **DA circular:** o DA pode "refutar bonito" sem dado → exigir factor_evidence estruturada nele também.
- **Overfit do aggregator:** a regra a-e não pode ser tunada aos 276 (in-sample) → pré-registrar antes de medir.

## 14. Plano de implementação futura (fases, NÃO agora)
1. **Fase 0:** schema de evidência + validador (factor_used∈84 ∧ value==packet) + packet tipado. (infra, sem decidir nada)
2. **Fase 1:** Stage A (Context Classifier) isolado + teste de não-circularidade (§7).
3. **Fase 2:** roster de especialistas (§3a) + DA, schema estruturado, num SUBSET pequeno; medir se os `decisive` factors de cada um separam win/lose.
3b. **Fase 2.5 — ABLATION (§3c):** medir contribuição marginal de CADA especialista sobre os 276; cortar/fundir redundantes e os que não separam win/lose. **O roster final é empírico (pode ser <20)**, não a lista cheia. Sem esta fase, o engine vira "20 narradores".
4. **Fase 3:** Aggregator constrói-tese + rubrica pré-registrada; rodar nos 276; comparar vs atual (§12), só com o roster enxuto que passou no ablation.
5. **Fase 4:** calibração posterior de confidence; só então confidence vira métrica.
6. **Fase 5 (só se §12 passar):** promover; aplicar a Opção B (2013-2017) como AI_REVIEW declarado.

## Phase 0 implemented: typed packet + evidence schema + validator (2026-06-19)
**SÓ infra de auditoria — nenhum agente, nenhuma decisão, engine atual intocado.**
- **Packet tipado:** `pipeline/qualification/multi_agent_schema.py` — 84 fatores, cada um com type/source/causal/nullable/unit/bucket/description/**allowed_families** (23 famílias do roster §3a). Mandatos disjuntos por família (demand_supply 18, risk_sl 22, exhaustion_top 20, rsi_momentum 6, nas 5, bubbles 12, capitulation 13…); wildcards (context_classifier/causality_audit/devils_advocate/aggregator) podem citar qualquer fator; 6 metas (ts/price/atr/bar_idx/datetime/episode_id) não-citáveis como evidência. Repaint-risk marcado (smc_bos/choch: direção/recência, não preço). Metadados embutidos (versionados; SEM dep runtime de /tmp).
- **Schema de evidência:** `specialist_id, episode_id, factor_used, value, packet_value, value_match, interpretation, impact{positive/negative/neutral/veto/review_flag}, strength{weak/medium/strong}, decisive_or_supporting, caveat, causal`.
- **Validador:** `pipeline/qualification/validate_agent_evidence.py` — REJEITA: factor fora dos 84; **value≠packet (anti-eco/artefato supply_distance)**; fator não-permitido p/ a família; sem source/impact/specialist_id; não-causal; **"uso" sem value explícito** (mata narrativa). Recomputa value_match do packet real (não confia na claim do agente).
- **Fixtures+teste:** `pipeline/qualification/phase0_test_validator.py` — 5 fixtures (1 TAKE-win/1 TAKE-lose/1 SKIP-win/1 SKIP-lose/1 REVIEW), 8 evidências cada (1 válida + 7 inválidas propositais). **Validador 40/40 PASS.** Relatório: `results/l2_bpt_multi_agent_phase0_schema_validation.csv`.
- **Não feito:** nenhum agente rodado, nenhuma decisão nova, nenhum outcome alterado, sem Opção B, sem retune.

## ESCOPO (trava do Cris 2026-06-19)
Este é o engine de qualificação de trade do **L2/BPT XAU 4H** — NÃO um "engine de trading global". Arquitetura reusável depois, mas **sem promoção cross-strategy agora**.

## Phase 1 implemented: Stage A Context Classifier (CEGO à decisão e ao outcome) — 2026-06-19
**Só classificação de contexto — NÃO decide trade, NÃO viu outcome/decisão/setup_type antigo.**
- **Mandato:** `pipeline/qualification/stage_a_context_classifier_prompt.md` (8 labels; sem linguagem de decisão/performance; ≥3 evidências estruturadas/episódio).
- **Runner:** `pipeline/qualification/run_stage_a_context_classifier.py` (--prep tira TODO vazamento: outcome/decision/confidence/setup_type/episode_id → 83 fatores; verificado 0 vazamento. --collect valida cada evidência pela Fase 0).
- **Execução:** 7 agentes LLM cegos classificaram 276 episódios → `results/l2_bpt_stage_a_context_labels.jsonl`. **Evidências 1231/1232 válidas** (validador anti-eco pegou 1 value≠packet; tolerância tight 0.011). 0 label fora das 8.
- **Distribuição:** bull_pullback_continuation 75, mid_range_noise 46, late_top_exhaustion 44, demand_reclaim 42, bear_bounce 25, bottom_reversal_capitulation 23, liquidity_sweep_reversal 20, unclear_conflict 1.
- **Não-circularidade (Tarefa 4, `..._noncircularity_audit.csv`): PASS.** Cego (estrutural, verificado). MI(label;outcome)=0.036 (NMI≈0.02 → sem vazamento de outcome). MI(label;old_decision)=0.366 (NMI 0.14/0.26/0.19). **DA af62d319:** MI(label;old_setup_type)=0.913 (NMI_min 0.38, 2.5× vs decisão) → **Stage A RE-DERIVA o setup_type antigo às cegas** ⇒ (a) prova que setup_type NÃO era relabel da decisão (é estrutura recuperável cega); (b) Stage A agrega AUDITABILIDADE, não um eixo de contexto NOVO.
- **Diagnóstico pós-hoc (Tarefa 5, `..._context_outcome_diagnostic.csv`, NÃO promoção):** demand_reclaim +0.896 (n42), bottom_reversal_capitulation +0.821 (n23) promissores; bear_bounce −0.230 (n25), late_top_exhaustion −0.141 (n44) perigosos; bull_pullback +0.278 (n75), liquidity_sweep +0.471 (n20), mid_range +0.206 (n46). Contraste promising-vs-dangerous: **Welch t=4.0, diff +1.04R** (grand mean +0.305, median −0.09) = sinal real, NÃO só bull-beta. Caveats DA: unclear n=1 (dropar), liquidity n20/bottom n23 subdimensionados; full-8 spread borderline (p~0.02-0.07).
- **Veredito Phase 1:** non-circular PASS; útil para Phase 2 = **CONDICIONAL/weak-PASS** — Stage A vale como **re-derivação reproduzível/auditável** do contexto estrutural (com evidência validada), NÃO como eixo novo. Próximo: Phase 2 (especialistas + ablation) tratando Stage A assim.

## Phase 2A implemented: specialist evidence generation + ablation prep — 2026-06-19
**Só geração de evidência por especialista. SEM aggregator, SEM decisão TAKE/REVIEW/SKIP, SEM outcome no input.**
- **10 especialistas** (subset controlado): demand_supply, capitulation, exhaustion_top, volume_vp, nas, bubbles, rsi_momentum, risk_sl, bull_beta, devils_advocate. Mandatos gerados do schema (`specialists/gen_specialist_prompts.py` → `specialists/prompts/*.md`): missão estreita + fatores PERMITIDOS exatos + perguntas obrigatórias + formato de evidência + travas (sem narrativa, sem TAKE/SKIP).
- **Amostra:** EXPANDIDA para os **276 episódios completos** (máxima precisão, pedido do Cris). Input = 83 fatores + context_label da Fase 1; outcome/decision/setup_type/episode_id STRIPPED (0 vazamento verificado).
- **Execução:** 10 agentes LLM, 1 lente cada × 276 episódios → `results/specialist_out/*.jsonl`. Runner `run_specialist_evidence.py` (--prep/--collect).
- **Validação (Tarefa 4, `..._evidence_validation_phase2a.csv`): 20137 evidências, 20137 VÁLIDAS (100%)** pelo validador da Fase 0. **0 fator proibido, 0 value-mismatch (anti-eco), 0 narrativa-sem-value.** A disciplina estruturada se sustentou em escala (20k evidências).
- **Não-eco/divergência de lentes:** net_read diverge por especialista (devils_advocate 205 hostile vs rsi_momentum 143 supportive vs capitulation 177 neutral) → lentes leem INDEPENDENTE, sem colusão.
- **Ablation prep (Tarefa 5, `..._ablation_ready_matrix.csv`):** 2760 linhas (276 episódios × 10 especialistas) com positive/negative/veto/review_flag counts + decisive_factors + unresolved_conflicts por (episódio,especialista). Pronto para a Fase 2B (ablation: contribuição marginal por especialista). Nenhuma performance final calculada.
- **DA:** 0 decisão TAKE/SKIP gerada; 0 outcome/decisão-antiga no input; 100% validado; 0 fator proibido; nenhum aggregator criado; engine/decisões 2020-2026 INTOCADOS (git); Opção B não rodada; produção intacta.
- **Veredito Phase 2A: PASS.** Evidência estruturada auditável gerada em escala; pronta para ablation (Fase 2B).

## 15. O que NÃO implementar agora
Nada de código. Nada de rodar agentes. Não tocar engine/rubrica/decisões 2020-2026. Não rodar Opção B. Não calibrar. Não criar os schemas em código. Este bloco entrega **só o design**; cada fase do §14 é um bloco futuro com gate próprio.

---
*Design. Sem código alterado, sem validação, sem produção/chart/plot/SLIM. Próximo passo (se Cris autorizar): Fase 0 (infra de schema/validação), isolada.*
