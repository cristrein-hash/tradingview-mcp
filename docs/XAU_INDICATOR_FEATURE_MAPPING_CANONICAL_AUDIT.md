# XAU — Canonical Indicator / Feature Mapping Audit

**Data:** 2026-06-16 · **Tipo:** auditoria de mapping de indicadores read-only · **NOT_VALIDATION.**
**Escopo:** indicadores usados ou potencialmente usados no XAUUSD_4H_BREAKOUT_CONTINUATION / D1a e camadas complementares.
**Propósito:** fixar a fonte-de-verdade canônica de cada indicador **antes** de qualquer RAW rebuild, impedindo backtest contaminado por mapping errado (Bubbles, NAS, SMC, Custom OB, RSI/ADX/ATR/EMA, D1, swing).
**Bloco:** read-only exceto docs/mapping. Nenhum backtest, rebuild, trade, plotagem, MCP/chart, Telegram, broker, RAW alterado.

> **Relação com docs irmãos:** complementa `docs/XAU_4H_BREAKOUT_D1A_FEATURE_MAPPING_AUDIT.md` (mesmo bloco, foco breakout). **Este** é o registro canônico **por-indicador** com a taxonomia de status formal. Onde divergirem, a CFEL (`scripts/extract_replay_features.py` + `docs/data/FEATURE_EXTRACTION_POLICY.md`) prevalece.

---

## Taxonomia de status (fixa)

| Status | Significado |
|---|---|
| **CANONICAL_CONFIRMED** | Fonte + mapping verificados na CFEL/Pine; confiança HIGH; usável |
| **USABLE_DERIVED_FROM_OHLCV** | Derivável de OHLCV com fórmula explícita e causal |
| **USABLE_FROM_RAW_INDICATOR_PAYLOAD** | Vem do payload RAW do indicador (study_values/pine_*) já mapeado |
| **USABLE_ONLY_AFTER_EXTRACTOR_AUDIT** | Existe mas precisa auditar extractor/cobertura antes de usar |
| **REFERENCE_ONLY** | Mapeado, mas não usado por V0/V1/D1a (consulta futura) |
| **DO_NOT_USE_UNTIL_RESOLVED** | Mapping insuficiente; proibido até resolver |
| **HARD_STOP_FOR_REBUILD** | Bloqueia o rebuild da variante que depende dele |

---

## 1. Matriz canônica de indicadores

| Indicador | Feature | Fonte canônica | Arq:linha | Campo RAW | Campo slim | plot_id | Fórmula | Semântica visual | TF | SHIFT | Causal | Conf. | Status | Blocker V0/D1a? | Obs. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OHLCV | preço base | RAW `ohlcv` | extractor base | open/high/low/close | mesmos | — | — | candles | 4H/1D | — | sim | HIGH | CANONICAL_CONFIRMED | não | bar fechado |
| **RSI** | `rsi` | study_values TV "Relative Strength Index" | `extract:283` | `RSI` | `rsi` | — | TV RSI(14) Wilder (default) | linha RSI subpane | 4H | não | sim | HIGH | CANONICAL_CONFIRMED | não | lido, não recomputado |
| **RSI_MA** | `rsi_ma` | study_values "RSI-based MA" | `extract:284` | `RSI-based MA` | `rsi_ma` | — | TV "RSI-based MA" (default SMA 14) | linha MA no subpane | 4H | não | sim | HIGH | CANONICAL_CONFIRMED | não | **hard stop levantado** |
| RSI | `rsi_above_ma` (T4) | derivado | `extract:357` | — | `rsi_above_ma` | — | `rsi>rsi_ma` | — | 4H | não | sim | HIGH | CANONICAL_CONFIRMED | não | gate breakout |
| RSI divergence | bull/bear event | study_values "Regular Bullish/Bearish Label" | `extract:361-366` | `*_Label` | `rsi_div_*_event` | — | label discreto = evento | marcador RSI subpane | 4H | não | sim | MEDIUM | REFERENCE_ONLY | não | raw contínuo = diagnostic |
| OHLCV-deriv | `swing_high_10` (T1) | CFEL post_pass | `extract:419-423` | — | `close_above_swing_high_10` | — | `close[i]>max(high[i-10:i])` | rompe máx 10 prévias | 4H | i-10..i-1 | sim | HIGH | CANONICAL_CONFIRMED | não | exclui bar atual |
| OHLCV-deriv | `body_pct` (T3) | CFEL post_pass | `extract:426` | — | `body_pct` | — | `abs(C-O)/(H-L)` | corpo/range | 4H | não | sim | HIGH | CANONICAL_CONFIRMED | não | — |
| ATR | `atr14_wilder` (SL,R5) | CFEL post_pass | `extract:404-414` | — | `atr14_wilder` | — | Wilder(TR,14) | volatilidade | 4H | não | sim | HIGH | USABLE_DERIVED_FROM_OHLCV | não (declarar) | CFEL class=diagnostic; breakout usa este |
| ATR | `atr14_sma_tr` (CFEL oficial) | CFEL post_pass | `extract:413` | — | `atr14_sma_tr` | — | SMA(TR,14) | — | 4H | não | sim | HIGH | REFERENCE_ONLY | não | oficial CFEL, **não** usado pelo breakout |
| ATR | `ATR_MA20` (R5) | Python | `backtest_v1:229` | — | — | — | `SMA(atr14_wilder,20)` | — | 4H | não | sim | MEDIUM | USABLE_DERIVED_FROM_OHLCV | não | breakout-específico (≠ sma30_ratio) |
| ADX | `adx14` (R1) | Python | `backtest_v1:84-140` | — | — | — | Wilder DMI/DX/ADX(14) | força direcional | 4H | não | sim | MEDIUM | USABLE_DERIVED_FROM_OHLCV | não | não é campo slim/study |
| EMA | `ema50/ema200` (R2-R4) | Python | `backtest_v1:52,227-228` | — | — | — | EMA close `α=2/(p+1)` | médias | 4H | não | sim | HIGH | USABLE_DERIVED_FROM_OHLCV | não | — |
| EMA | `ema50_slope` (R4) | Python | `backtest_v1:258` | — | — | — | `ema50[i]>ema50[i-5]` | inclinação | 4H | não | sim | HIGH | USABLE_DERIVED_FROM_OHLCV | não | — |
| **EMA 1D** | `ema50_1D/ema200_1D` (D1a) | Python sobre 1D | **não implementado** | — | — | — | EMA close 1D | bias macro | 1D | latest-closed | sim | MEDIUM | **HARD_STOP_FOR_REBUILD** (V6/V7) | **SIM (D1a)** | RAW 1D existe; slim 1D não extraído |
| NAS | `nas_label_long/short` | pine_labels "NAS TOP BOTTOM DETECTOR" | `extract:49,298-302` | labels text | `nas_label_*` | — | text LONG/SHORT; recent `max_x−x≤5` | BOTTOM=LONG/TOP=SHORT | 4H | causal | sim | HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | não-central ao breakout |
| NAS | `nas_dist_ema_atr` | study_values | `extract:309` | `NAS_DISTANCE_FROM_EMA_ATR` | `nas_dist_ema_atr` | — | distância contínua | — | 4H | não | sim | HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | ≠ label; L1 usa SHIFT1≥1.31 |
| NAS | `NAS_*_SIGNAL` | study_values | CFEL §5 | numérico | (deprecated) | — | sinal numérico | — | 4H | — | — | LOW | DO_NOT_USE_UNTIL_RESOLVED | não | ~1 fire vs ~18 labels |
| Bubbles | BUY/SELL/POC | pine_shapes_bubbles.activations | `extract:259-280` | activations(time) | `bubble_*` | **BUY 0/2/4·SELL 6/8/10·POC 12** | size por ordem do plot | green-below=BUY/red-above=SELL | 4H | causal (time abs) | sim | dir HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | — |
| Bubbles | size tiers | mesmo | `extract:268-272` | — | `bubble_size_*` | small/med/large por plot | inferência de ordem | 3 tiers visuais | 4H | — | — | MED-HIGH | REFERENCE_ONLY | não | definitivo só via Pine Leviathan |
| Bubbles | price/y | — | — | — | — | — | — | — | — | — | — | — | **DO_NOT_USE_UNTIL_RESOLVED** | não | não capturado nas activations |
| SMC | structure event/dir/kind | pine_labels "LuxAlgo" | `extract:182-236` | labels | `smc_*` | — | dir=textColor; kind=size; event=id-diff | green=bull/blue=bear; tiny=internal | 4H | causal | sim | HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | vocab {CHoCH,BOS,EQH,EQL} |
| SMC | `has_recent_bos/choch` | derivado | CFEL §5 | — | (saturate) | — | — | — | 4H | — | — | LOW | DO_NOT_USE_UNTIL_RESOLVED | não | satura ~sempre-true → diagnostic |
| SMC | OB zones (bull/bear) | pine_boxes "LuxAlgo" | `extract:238-257` | boxes bgColor | `smc_nearest_*_ob_*` | — | bull r>b / bear b>r | cor da box | 4H | causal | sim | HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | — |
| Custom OB | zones DEMAND/SUPPLY | pine_boxes "OB Detector" (Pine v11) | `extract:142-181` + `11_custom_ob_detector_v11.pine` | boxes text+bgColor | `custom_ob_*`,`inside_*`,`nearest_*` | — | presence=active; state via bgColor alpha 77/51/25 | DEMAND green/SUPPLY orange | 4H | causal | sim | HIGH | CANONICAL_CONFIRMED · REFERENCE_ONLY | não (ref) | x2 NÃO usado p/ status |
| BigBeluga | supply/demand zones | legacy monitors/receiver (texto) | — | — | — | — | — | — | — | — | — | — | REFERENCE_ONLY | não | **não está na CFEL**; zona canônica = Custom OB v11 |

---

## 2. Bubbles mapping (obrigatório)

**Status: CANONICAL_CONFIRMED (direção) · REFERENCE_ONLY (breakout) · DO_NOT_USE (price/y).**

- **Fonte:** `pine_shapes_bubbles.activations` (tempo absoluto), lida em `extract_replay_features.py:259-280`.
- **Mapping canônico (hard-coded no extractor `:267-269`, casa com memória 2026-06-07 + FEATURE_EXTRACTION_POLICY §5):**
  - **BUY** = `plot_0` (small) / `plot_2` (medium) / `plot_4` (large)
  - **SELL** = `plot_6` (small) / `plot_8` (medium) / `plot_10` (large)
  - **POC** = `plot_12`
- **Direção visual:** green-below-price = BUY · red-above-price = SELL. Confiança **HIGH** (stat bull% 60-78 + visual).
- **Size tiers:** small/medium/large por ordem do plot dentro da direção. Confiança **MEDIUM-HIGH** (3 tiers visuais; ordem exata plot→size é inferência — definitiva só via Pine Leviathan, protegido/3rd-party).
- **Bubble y/price:** **unavailable in RAW** (não capturado nas activations) → **DO_NOT_USE_UNTIL_RESOLVED** (continua verdade).
- **Anti-erro:** mapping antigo/invertido (`BUY=2/6/10, SELL=0/4/8`) é **DO_NOT_USE / SUPERSEDED** — confirmado que **não reapareceu** (o extractor usa 0/2/4 buy, 6/8/10 sell, 12 POC).
- **Uso no breakout:** **REFERENCE_ONLY** (H5 bubbles foi bloqueado; não em V0/V1/D1a). Se uma variante futura usar Bubbles, o mapping acima é a fonte; size→plot exato fica MEDIUM-HIGH (não promover a HIGH sem o Pine source).

---

## 3. NAS mapping (obrigatório)

**Status: CANONICAL_CONFIRMED · REFERENCE_ONLY (breakout).**

- **Fonte primária (direção):** `pine_labels` "NAS TOP BOTTOM DETECTOR" (`extract:49,98-141,298-302`). Text **LONG/SHORT**; recent se `max_x − x ≤ 5` (`NAS_RECENT_N=5`). **BOTTOM=LONG, TOP=SHORT** (CFEL §5; memória `feedback_nas_long_short_never_top_bottom`).
- **NAS_DISTANCE (contínuo):** campo `nas_dist_ema_atr` = study `NAS_DISTANCE_FROM_EMA_ATR` (`extract:309`). É o valor contínuo per-bar. (L1 usa NAS_DISTANCE SHIFT1≥1.31 — é **este** campo, não os labels.)
- **Diferença entre representações (não confundir):**
  - **Pine shapes/labels** (`pine_labels`) = eventos discretos visíveis (direção). Per-bar via extractor histórico.
  - **study_values contínuos** (`nas_dist_ema_atr`, `nas_rsi`) = série per-bar; live via `data_get_study_values_at_bar` por **timestamp**.
  - **`NAS_*_SIGNAL` numérico** = **deprecated/diagnostic** (~1 fire/bloco vs ~18 labels) → **DO_NOT_USE**.
  - **event store** (indicator_signals) = esparso, **não** série per-bar → não usar como proxy de distância.
- **Regras duras:** "tem NAS" (label recente) **não** substitui `NAS_DISTANCE`; shapes **não** substituem o plot contínuo se o gate exigir valor/distância; event store esparso **não** é série per-bar.
- **Histórico:** extractor/replay (`nas_label_*`, `nas_dist_ema_atr` por bar). **Live:** `data_get_study_values_at_bar` por timestamp (alinhamento por timestamp, não índice — BOOTSTRAP §4).
- **Uso no breakout:** **REFERENCE_ONLY** (H1c diagnostic, rejeitado como filtro mecânico). Mapping provado → não é HARD STOP, mas só entra como confluência se uma variante futura o exigir.

---

## 4. LuxAlgo SMC / structure mapping (obrigatório)

**Status: CANONICAL_CONFIRMED (mapping visual-validado) · REFERENCE_ONLY (breakout).**

- **Fonte:** `pine_labels` + `pine_boxes` cujo `name` contém **"LuxAlgo"** (`SMC_NAME`, `extract:42,182-257`). Vocab estrutural = **{CHoCH, BOS, EQH, EQL}** (`SMC_STRUCT_VOCAB`).
- **Mapping visual validado (CFEL §5, confirmado 2026-05-27):**
  - **Direção = textColor:** `green (g>b) = bull`, `blue (b>g) = bear` (`smc_dir`, `:211-216`), ancorado por EQH=bear-color / EQL=bull-color.
  - **Internal vs swing = size:** `size=="tiny" → internal`; senão **swing** (`smc_kind`, `:217-218`).
  - **Evento discriminativo = id-diff:** `smc_struct_new = this_ids − prev_ids` (`:190,219-220`) → `smc_structure_event_new/type/direction/kind/price`.
  - **BOS/CHoCH swing direction:** última label não-tiny por tipo (`last_swing_dir`, `:226-230`).
  - **Strong High/Low price:** `:232-236`.
  - **OB boxes (bull/bear) por bgColor:** `bull r>b`, `bear b>r` (`box_dir`, `:238-257`).
- **Separação obrigatória:**
  - **SMC visual labels** (o que se vê) ≠ **RAW fields** (`textColor`/`size`/`id`/`price`) ≠ **interpretação do extractor** (`smc_*`). Documentados acima por origem.
- **Diagnostic (não usar como gate):** `smc_has_recent_bos/choch` **saturam (~sempre true)** → `diagnostic_only`. Usar `smc_structure_event_new` / `last_structure` / swing-dir.
- **Anti-erro:** **não inferir structure por nome.** Direção vem de **cor**, kind de **size**, evento de **id-diff** — nunca do texto isolado.
- **Uso no breakout:** **REFERENCE_ONLY** — o breakout não usa SMC. Qualquer gate SMC-derived numa variante futura é **CANONICAL_CONFIRMED** se usar os campos oficiais acima; caso contrário **DO_NOT_USE_UNTIL_RESOLVED**.

---

## 5. Custom OB / BigBeluga mapping (obrigatório)

**Status: Custom OB = CANONICAL_CONFIRMED (Pine v11) · REFERENCE_ONLY (breakout). BigBeluga = REFERENCE_ONLY (fora da CFEL).**

- **Custom OB — fonte semântica real:** **Pine v11** `my-strategy/pine_alerts/11_custom_ob_detector_v11.pine` (presente; **v10 e v12 também existem** — flag: confirmar a live atual se virar relevante). Extraído de `pine_boxes` cujo `name` contém **"OB Detector"** (`COB_NAME`, `extract:43,142-181`).
- **Regra canônica (CFEL §5 — Pine v11 audited):**
  - **Presence of box = active zone** (v11 `obshowbb=false` deleta violadas/aged/overlapping; FIFO 40/dir; auto-delete após 800 bars).
  - **DEMAND = bull/green, SUPPLY = bear/orange** (por `text`).
  - **State via bgColor alpha:** `77=fresh`, `51=touched`, `25=mitigated`.
  - **`x2` = coord de criação** (boxes usam `extend.right`) → **NÃO** usar para status ativo. `demand/supply_zone_active` (x2-based) = **deprecated**.
- **Campos (zone high/low/direction/touch/age/width):**
  - `nearest_demand_high/low`, `nearest_supply_high/low` (zone high/low) · `inside_demand/supply_zone` (touch) · `custom_ob_nearest_demand/supply_state` (fresh/touched/mitigated — proxy de age/touch) · `nearest_demand/supply_dist` (distância) · counts `custom_ob_n_demand/supply_zones`. Width não é campo direto (derivável de high−low).
- **Features L1 que usam zonas (referência, não tocar L1):** a L1 refinada usa `zone_w ≥ 0.6·ATR` (largura), `dist_zone ≤ 1.81·ATR` (distância à zona), e SL estrutural = `max(zone_OB_low, swing6_low) − 0.1·ATR` (zone low). Validação visual: Custom OB v11 audited (BOOTSTRAP §3). **Fora do escopo deste bloco** — citado só para mostrar que o mapping de zona já é canônico onde a L1 o usa.
- **BigBeluga:** aparece em monitores legacy / `claude_recheck.py` / receiver / policy como conceito de supply/demand, mas **NÃO está na CFEL nem no extractor**. A fonte canônica de zona é o **Custom OB v11**. → **REFERENCE_ONLY**; não inventar mapping BigBeluga.
- **Anti-erro:** não aceitar interpretação genérica por `x2`; fonte = Pine v11 audited.
- **Uso no breakout:** **REFERENCE_ONLY** (o breakout não usa zonas). Se uma variante usar, exige o mapping Pine v11 acima.

---

## 6. RSI / RSI_MA

**Status: CANONICAL_CONFIRMED — hard stop levantado.**

- **RSI:** `study_values["Relative Strength Index"]["RSI"]` (`extract:283`). **Não recomputado de OHLCV** — lido do estudo TV capturado no RAW. Fórmula subjacente = TV RSI(14) Wilder (default).
- **RSI_MA:** `study_values["Relative Strength Index"]["RSI-based MA"]` (`extract:284`). Fórmula subjacente = TV "RSI-based MA" (**default SMA length 14**). Como é valor capturado, o backtest **não** depende de reproduzir a fórmula — lê o campo.
- **Gate (T4):** `rsi_above_ma = rsi > rsi_ma` (`extract:357`; usado em `backtest_v1:224,249`).
- **Classe CFEL:** `official_for_backtest`, **HIGH**.
- **Residual (não-blocker):** recompute puro de OHLCV (sem study) exigiria confirmar settings TV (RSI length, MA type/length). Não necessário no caminho canônico.
- **Hard stop?** **NÃO.**

---

## 7. ADX / ATR / EMA

**Status: USABLE_DERIVED_FROM_OHLCV — todos definidos.**

- **ADX(14):** Wilder DMI → DI± → DX → Wilder-smooth(DX). Implementação canônica = `adx_wilder()` (`backtest_v1:84-140`), `adx14<20 ⇒ FAIL`. Existe 2ª impl (sweep `regime_filter_test.py`, ewm) — **reconciliar** (adotar `adx_wilder` do v1, atrelado ao trades.jsonl). Não é campo slim/study. MEDIUM.
- **ATR(14):** o breakout usa **`atr14_wilder`** (Wilder, `extract:404-414`), confirmado em `backtest_v1:215-216,275-276`. CFEL classifica `atr14_wilder` como *diagnostic* e `atr14_sma_tr` (SMA) como *official* — **divergência declarada**: o breakout usa o Wilder (fiel à spec), não trocar sem teste.
- **ATR expanding (R5):** `atr14_wilder[i] > SMA(atr14_wilder, 20)[i]` — período da MA = **20** (não o 30 do `atr14_sma30_ratio`). Definido.
- **EMA50/EMA200:** EMA close padrão `α=2/(period+1)` (`backtest_v1:52`). **Slope (R4):** `ema50[i] > ema50[i-5]` (5 barras). Todos usam **bar fechado**.
- **Hard stop?** **NÃO** — fórmulas todas definidas. **Ação:** declarar (a) `adx_wilder` canônico, (b) ATR=`atr14_wilder`+ATR_MA20(SMA,20) divergente do ATR oficial CFEL.

---

## 8. D1 alignment

**Status: HARD_STOP_FOR_REBUILD (V6/V7) — regra definida, mecanização + prova pendentes.**

- **Regra canônica:** para cada 4H eval_bar em `t`, usar o **último 1D fechado** com `close_time ≤ t`. **Nunca** o D em formação.
- **Predicado D1a:** `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` no daily fechado.
- **Estado real:** **não mecanizado** — o backtest v1 é 4H-only; D1a foi research prose-only. Não existe join 1D→4H para esta família.
- **RAW 1D disponível:** registry confirma `XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz` (3602 barras, active).
- **A provar (Rodada 1):** timezone (UTC), convenção do timestamp 1D (open vs close), implementação `merge_asof(direction='backward')` sobre **close-time** do 1D.
- **SHIFT1-audit obrigatório:** ORIG vs SHIFT1 sem delta (precedente A1' SUPERTREND: 88%→46% sob audit). **Não** aceitar "causal-by-construction".
- **Hard stop?** **SIM para D1a (V6/V7).** V0-V5 não dependem de D1.

---

## 9. swing10

**Status: CANONICAL_CONFIRMED — inequívoco.**

- **Fórmula (CFEL `extract:419-423`):** `swing_high_10 = max(high[i-10:i])` (10 barras **anteriores**, **exclui** o bar atual); `close_above_swing_high_10 = close[i] > swing_high_10`.
- **É rolling high das 10 prévias** — **não** fractal, **não** swing estrutural. Nível conhecido **antes** do candle de rompimento (causal, usa i-10..i-1). Equivalente a `highest(high,10)[i-1]`.
- **Hard stop?** **NÃO.**

---

## 10. RAW vs SLIM

- **Hierarquia (project_authority/02):** TV visual > **RAW replay** > **CFEL v2** (intérprete oficial) > derivadas simples > slim/proxy (não-validatório).
- **CFEL v2** (`extract_replay_features.py`) campos `official_for_backtest` (HIGH) = permitidos **com confiança declarada**. **≠ slim v1 proibido** (`feedback_never_use_slim_features` refere-se ao v1 com semântica errada, DELETE_CANDIDATE).
- **RAW XAU disponível (registry confirma conteúdo, não só existência):** 4H 2016-2026 (3 blocos: 5557+4636+5242 barras + bloco SVP_LUX_RAW 10074); 1D 2012-2026 (3602 barras); todos `active`.
- **Conteúdo `.gz` não aberto neste bloco** (não tocar RAW) → confirmar na Rodada 1: qual bloco carrega o study RSI (a CFEL já extraiu `rsi_above_ma` → existe) + cobertura do slim v2 (re-extração full §8 pendente).
- **Regra:** nenhum campo slim é "validado" sem mapping para RAW; RAW = source-of-truth para backtest sério.

---

## 11. Atualização do mapping BREAKOUT/D1a

**SIM** — `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/raw_field_mapping.md` atualizado (v1.1, só clarificação; sem inventar campo, sem mudar estratégia): RSI/RSI_MA de study_values (não OHLCV recompute); ATR=`atr14_wilder`+ATR_MA20(20) com divergência CFEL; ADX=`adx_wilder` Python; swing fórmula fixada; hard stops reordenados (RSI_MA/ADX/ATR/swing resolvidos; **D1a 1D = único blocker estrutural**).

---

## 12. Decisão final do bloco

| Pergunta | Resposta |
|---|---|
| **Rebuild V0 liberado?** | **SIM** — trigger T1-T4 (OHLCV + RSI study + swing + body) todas CANONICAL_CONFIRMED. |
| **Rebuild V1-V5 (regime 4H) liberado?** | **SIM** — ADX/EMA/ATR USABLE_DERIVED_FROM_OHLCV, fórmulas fixadas (com 2 declarações: ATR-wilder, ADX-wilder). |
| **Rebuild V6/V7 (D1a) liberado?** | **NÃO** — HARD_STOP: pipeline 1D não mecanizado + SHIFT1-audit pendente. |
| **Blockers restantes** | (1) D1a 1D (BLOCKER); (2) declarar ATR-wilder; (3) reconciliar ADX impl; (4) confirmar cobertura slim v2 4H; (5) custos/gross. |
| **Features seguras** | OHLCV, RSI/RSI_MA, swing10, body_pct, ATR-wilder, ATR_MA20, ADX, EMA50/200/slope (4H). |
| **Indicadores NÃO usáveis ainda** | EMA 1D/D1a (HARD_STOP); Bubble price/y (DO_NOT_USE); NAS_*_SIGNAL numérico (DO_NOT_USE); SMC has_recent_* (diagnostic). NAS/Bubbles/SMC/Custom OB/BigBeluga = REFERENCE_ONLY (não-needed em V0-V5). |
| **Menor próximo passo** | Iniciar **Rodada 1** (autorizada): confirmar conteúdo RAW 4H + cobertura slim v2; reconstruir V0; reconciliar contagem. (D1a fica para depois do pipeline 1D.) |

**Veredito: rebuild PARCIAL liberado — V0-V5 desbloqueados; V6-V7 (D1a) bloqueados.**

---

## 13. Devil's Advocate

| Pergunta DA | Resposta |
|---|---|
| Nenhuma feature inferida por nome? | ✅ Cada uma rastreada a `extract`/`backtest_v1`/Pine com arq:linha. |
| Bubbles antigo/invertido reapareceu? | ✅ Não — `0/2/4 buy, 6/8/10 sell, 12 POC` (extractor `:267-269`); invertido = DO_NOT_USE. |
| NAS shape/event store usado como NAS_DISTANCE? | ✅ Não — `nas_dist_ema_atr` (study contínuo) separado de labels e event store explicitamente. |
| SMC interpretado genericamente? | ✅ Não — dir=textColor, kind=size, evento=id-diff; texto isolado não basta. |
| Custom OB sem Pine/source? | ✅ Não — Pine v11 audited; x2 NÃO usado p/ status; BigBeluga marcado fora-da-CFEL. |
| RSI_MA definido ou HARD STOP? | ✅ **Definido** (study "RSI-based MA", HIGH). |
| ADX/ATR/EMA definidos ou HARD STOP? | ✅ **Definidos** (adx_wilder; atr14_wilder+MA20; EMA α=2/(p+1)). Divergências declaradas. |
| D1 alignment definido ou HARD STOP? | ✅ Regra definida **mas HARD_STOP** (não mecanizado + SHIFT1 pendente). |
| swing10 definido ou HARD STOP? | ✅ **Definido** `max(high[i-10:i])` exclui atual. |
| RAW substituído por SLIM? | ✅ Não — RAW source-of-truth; v2 = intérprete oficial; v1 proibido distinguido. |
| Nenhum backtest rodado? | ✅ Só leitura + docs. |
| Nenhuma plotagem? | ✅ Nenhum draw/MCP. |
| Nada operacional tocado? | ✅ Produção íntegra (read-only). |
| Caminho B não recomendado? | ✅ Não. |

**DA verdict: PASS.**

---

*Read-only exceto docs/mapping. Nenhum backtest, rebuild, trade, plotagem, MCP/chart, Telegram, broker. Nenhum RAW alterado (registry/extractor/Pine lidos; `.gz` não aberto). Mapping rastreado à CFEL canônica (`extract_replay_features.py` schema v2) + Pine v11 + backtest implementado.*
