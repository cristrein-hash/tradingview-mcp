# XAU 4H BREAKOUT / D1a — Feature Mapping Audit

**Data:** 2026-06-16 · **Tipo:** auditoria de mapping de features read-only · **NOT_VALIDATION.**
**Escopo exclusivo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT.
**Propósito:** fixar a fonte canônica profunda de cada feature **antes** de qualquer rebuild/RAW, impedindo backtest contaminado por mapping errado.
**Bloco:** read-only exceto docs/mapping. Nenhum backtest, nenhuma plotagem, nada operacional, sem MCP/chart, sem RAW alterado.

---

## 1. Executive summary

Este bloco resgatou a **Canonical Feature Extraction Layer (CFEL)** — `scripts/extract_replay_features.py` (schema v2, promovido 2026-05-28) — e a **política canônica** `docs/data/FEATURE_EXTRACTION_POLICY.md`, e cruzou-as com o backtest **realmente implementado** do breakout (`scripts/backtest_xau_4h_breakout_continuation_v1.py`).

**Resultado principal: os 5 "hard stops" do bloco de plano anterior estão majoritariamente RESOLVIDOS** — não por inferência, mas porque a fonte canônica define cada feature:

- **RSI / RSI_MA — RESOLVIDO (hard stop levantado).** Não é recomputado de OHLCV; é **lido do study_values** da TV ("Relative Strength Index" → `RSI` e `RSI-based MA`). Classe CFEL = `official_for_backtest`, confiança **HIGH**.
- **swing10 — RESOLVIDO, inequívoco.** `close_above_swing_high_10 = close[i] > max(high[i-10..i-1])` — 10 barras **anteriores, excluindo o bar atual**.
- **ATR — RESOLVIDO com divergência declarada.** O breakout usa `atr14_wilder` (campo canônico, mas a CFEL o classifica como *diagnostic*; o ATR "oficial" da CFEL é SMA). Uso fiel à estratégia, **deve ser declarado**, não é blocker.
- **ADX — RESOLVIDO, definido.** ADX Wilder(14) computado em Python (`adx_wilder()` no backtest do breakout). Não é campo de slim nem study; derivável de OHLCV.
- **EMA50/200 (4H) — RESOLVIDO.** EMA Python `alpha=2/(period+1)` sobre close.

**Blocker remanescente (1):** **D1a não está mecanizado em lugar nenhum** — o backtest v1 é 4H-only e nunca implementou D1a (era prose-only research). Exige pipeline 1D (extrair slim canônico 1D do RAW 1D existente → EMA50_1D/EMA200_1D → alinhamento *latest-closed-daily* → **SHIFT1-audit**).

**Veredito de liberação:** **rebuild PARCIALMENTE liberado.** V0-V5 (trigger T1-T4 + regime 4H R1-R5) estão **desbloqueados** — todas as features são canonicamente definidas/disponíveis. **V6-V7 (D1a) BLOQUEADOS** até o pipeline 1D + SHIFT1-audit. **DA: PASS.**

> ⚠️ **RAW vs SLIM — distinção crítica esclarecida:** a proibição `feedback_never_use_slim_features` refere-se ao **slim v1** (semântica NAS/SMC/OB/Bubbles comprovadamente errada). A **CFEL v2** (`extract_replay_features.py`) é a camada canônica oficial; seus campos `official_for_backtest` são permitidos **com a confiança declarada**. RAW segue source-of-truth; o v2 é o intérprete oficial do RAW. Não confundir os dois slims.

---

## 2. Fontes lidas

| Camada | Fonte |
|---|---|
| Política RAW-first | `docs/project_authority/02_DATA_SOURCE_POLICY_RAW_FIRST.md`, `03_BACKTEST_VALIDATION_PROTOCOL.md`, `SKILL_02_RAW_BACKTEST_PROTOCOL.md`, `SKILL_03_VISUAL_REVIEW_AUCTION_THEORY.md` |
| **CFEL (canônica)** | `docs/data/FEATURE_EXTRACTION_POLICY.md` + `scripts/extract_replay_features.py` (schema v2) |
| Backtest implementado | `scripts/backtest_xau_4h_breakout_continuation_v1.py` |
| Sweep legacy | `my-strategy/research/backtests/xauusd_audit_20260512/regime_filter_test.py` |
| Registry RAW | `docs/data/dataset_registry.json` |
| Bloco anterior | `docs/XAU_4H_BREAKOUT_*_DEEP_DIVE.md`, `…EDGE_DECOMPOSITION…`, `…MECHANICAL_REBUILD_PLAN.md`, `…/v1/gate_manifest.md`, `raw_field_mapping.md`, `design_test_plan.md`, BOOTSTRAP pós-L1 |
| Pine fonte | `my-strategy/pine_alerts/11_custom_ob_detector_v11.pine` (semântica Custom OB) |
| Memória | mapping Bubbles 2026-06-07, NAS LONG/SHORT, plot_id validation |

---

## 3. Feature mapping table

| Feature | Fonte canônica | Arquivo:linha | Campo / plot / raw key | Fórmula | TF | Causalidade | Confiança | Status |
|---|---|---|---|---|---|---|---|---|
| `close/open/high/low` | RAW `ohlcv` | extractor base | OHLCV | — | 4H/1D | causal (bar fechado) | HIGH | OK |
| `RSI` | TV study `study_values` | `extract_replay_features.py:283` | `sv["Relative Strength Index"]["RSI"]` → `rsi` | TV RSI(14) Wilder (default; confirmar settings) | 4H | causal (snapshot bar fechado) | **HIGH** (official) | **RESOLVIDO** |
| `RSI_MA` | TV study `study_values` | `:284` | `sv["Relative Strength Index"]["RSI-based MA"]` → `rsi_ma` | TV "RSI-based MA" (default SMA len 14; confirmar) | 4H | causal | **HIGH** (official) | **RESOLVIDO (hard stop levantado)** |
| `rsi_above_ma` (T4) | derivado | `:357` | `rsi > rsi_ma` | booleano | 4H | causal | HIGH | OK |
| `swing_high_10` (T1) | OHLCV-derived | `:419-423` | `close_above_swing_high_10 = C[i] > max(H[i-10:i])` | máx high das 10 barras **anteriores** (exclui atual) | 4H | causal (i-10..i-1) | **HIGH** (official) | **RESOLVIDO, inequívoco** |
| `body_pct` (T3) | OHLCV-derived | `:426` | `abs(C-O)/(H-L)` | — | 4H | causal | HIGH (official) | OK |
| `ATR14` (SL, R5) | OHLCV-derived | `:404-414` | **`atr14_wilder`** (usado pelo breakout) / `atr14_sma_tr` (CFEL oficial) | Wilder(TR,14) vs SMA(TR,14) | 4H | causal | HIGH (campo) · **CFEL class=diagnostic p/ wilder** | **RESOLVIDO c/ divergência declarada** |
| `ATR_MA20` (R5) | derivado | `backtest_v1:229` | `SMA(atr14_wilder, 20)` | breakout-específico (≠ `atr14_sma30_ratio`) | 4H | causal | MEDIUM | **RESOLVIDO c/ nota** |
| `ADX14` (R1) | Python (não-slim) | `backtest_v1:84-140,230` | `adx_wilder(h,l,c,14)` | Wilder DMI/DX/ADX | 4H | causal | MEDIUM (derivado, sem study/visual) | **RESOLVIDO, definido** |
| `EMA50/EMA200` (R2-R4) | Python (não-slim) | `backtest_v1:52,227-228` | `ema_series(close, p)` `alpha=2/(p+1)` | EMA close | 4H | causal | HIGH (definido) | OK |
| `EMA50_slope` (R4) | derivado | `backtest_v1:258` | `ema50[i] > ema50[i-5]` | slope 5 barras | 4H | causal | HIGH | OK |
| **`EMA50_1D/EMA200_1D` (D1a)** | Python sobre 1D | **não implementado** | precisa slim 1D canônico | EMA close 1D | 1D | causal (latest-closed) | MEDIUM | **BLOCKER (build 1D)** |
| `nas_label_long/short` | `pine_labels` | `extractor:49,298-302` | "NAS TOP BOTTOM DETECTOR" text LONG/SHORT; BOTTOM=LONG/TOP=SHORT | recent se `max_x−x≤5` | 4H | causal (label fechado) | HIGH | reference_only (breakout) |
| `nas_dist_ema_atr` | TV study | `extractor:309` | `NAS_DISTANCE_FROM_EMA_ATR` | study contínuo | 4H | causal | HIGH | reference_only |
| Bubbles | `pine_shapes_bubbles.activations` | `extractor` / policy §5 | BUY=0/2/4 SELL=6/8/10 POC=12 | size por ordem do plot | 4H | causal (time abs) | dir HIGH·size MED-HIGH·**price unavailable** | reference_only |
| Custom OB | `pine_boxes` | `11_custom_ob_detector_v11.pine` | text DEMAND/SUPPLY; presence=active; state via bgColor alpha (77/51/25) | Pine v11 audited | 4H | causal | HIGH | reference_only |

---

## 4. RSI / RSI_MA

**RESOLVIDO — hard stop do bloco anterior levantado.**

- **Fonte:** TradingView study **"Relative Strength Index"** capturado em `study_values` no RAW replay. Lido pela CFEL (`extract_replay_features.py:282-284`): `rsi = sv["Relative Strength Index"]["RSI"]`, `rsi_ma = sv["Relative Strength Index"]["RSI-based MA"]`.
- **NÃO recomputado de OHLCV.** A correção em relação ao `raw_field_mapping.md` v1 (que dizia "recompute RSI from RAW OHLCV") é: a fonte canônica é o **study_value capturado**, não um recompute. Isso elimina a ambiguidade de fórmula.
- **Gate breakout (T4):** `rsi_above_ma = rsi > rsi_ma` (`extractor:357`; lido pelo backtest em `backtest_v1:224`).
- **Fórmula subjacente:** RSI = TV RSI(14) Wilder (default); "RSI-based MA" = MA da RSI, **default TV = SMA length 14**. Como o valor é capturado do estudo, o backtest não depende de reproduzir a fórmula — só de ler o campo.
- **Classe CFEL:** `official_for_backtest`, confiança **HIGH** (FEATURE_EXTRACTION_POLICY §4).
- **Residual (não-blocker):** se algum dia se quiser recomputar puramente de OHLCV (sem study_values), aí sim seriam necessários os settings exatos do indicador TV (RSI length, MA type/length). Para o rebuild canônico **não é necessário** — usa-se o campo capturado.
- **Hard stop?** **NÃO.** RSI/RSI_MA estão definidos e disponíveis canonicamente.

---

## 5. ADX

**RESOLVIDO — definido, derivável.**

- **Fonte:** **não é campo de slim nem de study_values.** ADX é computado em Python a partir de OHLCV.
- **Implementação autoritativa (a que gerou os trades revalidados):** `adx_wilder(highs, lows, closes, period=14)` em `backtest_xau_4h_breakout_continuation_v1.py:84-140`. Wilder DMI → DI± → DX → Wilder-smooth(DX). `adx14[i] < 20` ⇒ FAIL (`:252`).
- **Segunda implementação (sweep legacy):** `regime_filter_test.py:20-39` usa `ewm(alpha=1/14)` sobre TR/DM. Conceitualmente Wilder, mas **implementação diferente** (ewm vs loop seed). → **reconciliar qual é canônica para o rebuild**; recomendado adotar `adx_wilder` (atrelado ao trades.jsonl v1). Declarar.
- **Causalidade:** usa barras fechadas; sem lookahead.
- **Confiança:** MEDIUM (derivado de OHLCV, sem estudo TV nem validação visual). Reproduzível exatamente se a implementação for fixada.
- **Hard stop?** **NÃO** (fórmula definida). **Ação:** fixar `adx_wilder` como implementação canônica do rebuild e declarar.

---

## 6. ATR

**RESOLVIDO com divergência a declarar (não-blocker).**

- **Três convenções coexistem** — esta é a principal armadilha que o bloco evita:
  1. **CFEL oficial:** `atr14_sma_tr = SMA(TR,14)`; `ATR_MA30 = SMA(atr14,30)` → `atr14_sma30_ratio`. (`extractor:402,413-418`; FEATURE_EXTRACTION_POLICY §5 — "ATR legacy", casa com `monitor_xau_4h_strategies.py`.)
  2. **`atr14_wilder`** = Wilder(TR,14) (`extractor:404-414`). CFEL o marca **comparison/diagnostic**.
  3. **Sweep legacy** (`regime_filter_test.py`): `atr14` base + `rolling(20).mean()`.
- **O que o breakout REALMENTE usa:** **`atr14_wilder`** — confirmado em `backtest_v1:215-216` (`atrs = b["atr14_wilder"]`), usado no SL (`:275-276` `stop = low - 0.5*atr14_wilder`) e no R5 (`atr_ma20 = SMA(atr14_wilder, 20)`, `:229,260`).
- **TR:** `max(h−l, |h−prev_close|, |l−prev_close|)` (`extractor:395`), bar fechado.
- **Divergência:** o breakout usa o ATR que a CFEL classifica como *diagnostic*, não o *official* (SMA). Como `atr14_wilder` **é** computado canonicamente, o uso é fiel à estratégia — **mas deve ser declarado** no manifest/rebuild (não trocar para o SMA "oficial" sem teste, pois mudaria SL e R5). O `ATR_MA20` (SMA de wilder sobre 20) é breakout-específico, **não** o `atr14_sma30_ratio` canônico.
- **ATR expanding (R5):** `atr14_wilder[i] > SMA(atr14_wilder, 20)[i]`. Período da MA = **20** (não 30). Declarado.
- **Hard stop?** **NÃO.** **Ação:** declarar explicitamente "breakout usa `atr14_wilder` + ATR_MA20(SMA,20)", divergente do ATR oficial CFEL.

---

## 7. EMA / D1 alignment

**EMA 4H — RESOLVIDO. D1a 1D — BLOCKER (não mecanizado).**

- **EMA50/EMA200 4H:** Python `ema_series(close, period)`, `alpha=2/(period+1)` (`backtest_v1:52-53,227-228`). Não são campos de slim. Bar fechado. R2 `close>EMA200`, R3 `EMA50>EMA200`, R4 `EMA50[i]>EMA50[i-5]`. Definido, HIGH.
- **D1a (1D):** exige `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` no **último 1D fechado** antes do bar 4H.
  - **Estado real:** o backtest v1 é **4H-only** e **nunca implementou D1a** (D1a foi research prose-only em `summary.md`). Não há código que faça o join 1D→4H para esta família.
  - **RAW 1D disponível:** registry confirma `XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz` (3602 barras, active).
  - **Pipeline necessário:** extrair slim canônico 1D (CFEL suporta via registry) → computar EMA50_1D/EMA200_1D de close 1D → alinhar.
  - **Regra de alinhamento canônica (a fixar e provar):** para o bar 4H em `t`, usar o 1D com **close-time ≤ t** mais recente; **nunca** o D em formação. Implementar via `merge_asof(direction='backward')` sobre o **close-time** do candle diário. Confirmar timezone (UTC) e convenção open/close dos timestamps no RAW 1D (Rodada 1).
  - **SHIFT1-audit obrigatório:** ORIG vs SHIFT1 sem delta (precedente A1' SUPERTREND: "causal-by-construction" colapsou 88%→46%). Não aceitar sem prova empírica.
- **Hard stop?** Para **D1a (V6/V7): SIM** — bloqueado até pipeline 1D + alinhamento provado + SHIFT1-audit. Para **EMA 4H (V2-V5): NÃO.**

---

## 8. swing10

**RESOLVIDO — inequívoco.**

- **Fonte:** OHLCV-derived na CFEL, `extract_replay_features.py:419-423`:
  ```
  if i >= 10 and all(H[j] for j in range(i-10, i)):
      sh = max(H[i-10:i])           # 10 barras ANTERIORES, EXCLUI o bar atual
      close_above_swing_high_10 = (C[i] > sh)
  ```
- **Semântica:** `close[i] > max(high[i-10 .. i-1])` — rompe a máxima das **10 barras estritamente anteriores**. Equivalente ao `highest(high,10)[i-1]` do manifest. **Não** é swing fractal; é rolling-high das 10 prévias. O nível é **conhecido antes** do candle de rompimento (causal). Usado pelo backtest em `:223` (`close_above_swing[i]`).
- **Hard stop?** **NÃO.** Regra inequívoca.

---

## 9. NAS mapping

**RESOLVIDO (reference_only para breakout).**

- **Fonte:** `pine_labels` "NAS TOP BOTTOM DETECTOR" (`extractor:49,98-141`). Direção via **text LONG/SHORT**; `recent` se `max_x − x ≤ 5`.
- **Regra canônica fixa (CFEL §5):** **BOTTOM = LONG, TOP = SHORT** (não há campos top/bottom separados). Os `study_values` `NAS_*_SIGNAL` são **deprecated/diagnostic** (~1 fire/bloco vs ~18 labels visíveis). Coerente com a memória `feedback_nas_long_short_never_top_bottom`.
- **Campos:** `nas_label_long/short_recent`, `nas_label_recent_long/short_bars`, `nas_label_long/short_event`, `nas_label_event_type/price/id` (eventos via id-diff + price-match) (`:298-302`).
- **NAS_DISTANCE:** campo contínuo `nas_dist_ema_atr` (= study `NAS_DISTANCE_FROM_EMA_ATR`, `:309`) — distinto dos labels. (L1 usa NAS_DISTANCE SHIFT1≥1.31; é este campo contínuo, não o label.)
- **Não confundir:** label (pine_labels) ≠ event store ≠ study_value contínuo. Para histórico, extractor/replay; para live, `data_get_study_values_at_bar` por timestamp.
- **Uso no breakout:** **NÃO central.** Apareceu só como H1c diagnostic (rejeitado como filtro mecânico). `reference_only` — resgatado para eventuais variantes futuras, não para V0/V1/D1a.

---

## 10. Bubbles mapping

**RESOLVIDO (reference_only para breakout) — mapping correto confirmado, invertido NÃO reapareceu.**

- **Fonte:** `pine_shapes_bubbles.activations` (tempo absoluto) (`extractor` / FEATURE_EXTRACTION_POLICY §4-5).
- **Mapping canônico (CFEL §5, casa com memória 2026-06-07):**
  - **BUY = plot_0/2/4**, **SELL = plot_6/8/10**, **POC = plot_12**.
  - Size por ordem do plot dentro da direção (small/medium/large).
  - Direção visual: green-below-price = BUY, red-above-price = SELL.
- **Confiança:** direção **HIGH** (stat bull% 60-78 + visual); size **MEDIUM-HIGH** (3 tiers visuais; ordem exata plot→size é inferência — definitiva só via Pine Leviathan, protegido); **price/y = unavailable** (não capturado nas activations → `do_not_use` para y).
- **Anti-erro:** o mapping antigo/invertido (BUY=2/6/10, SELL=0/4/8) é **SUPERSEDED** (memória `feedback_validate_plot_id_mapping`). Confirmado que **não** reapareceu aqui — usado o correto (0/2/4 buy, 6/8/10 sell, 12 POC).
- **Uso no breakout:** `reference_only` (H5 bubbles ficou bloqueado; extractor zerava POC no contexto antigo). Não para V0/V1/D1a.

---

## 11. Custom OB mapping

**RESOLVIDO (reference_only para breakout).**

- **Fonte semântica:** **Pine v11** `my-strategy/pine_alerts/11_custom_ob_detector_v11.pine` (presente; v10 e **v12 também existem** — flag: confirmar qual é a live atual se virar relevante). Extraído de `pine_boxes` "Custom OB Detector v11" (`extractor:142-181`).
- **Regra canônica (CFEL §5):**
  - **Presence of box = active zone** (v11 com `obshowbb=false` deleta violadas/aged/overlapping; FIFO 40/dir; auto-delete após 800 bars).
  - DEMAND = bull/green, SUPPLY = bear/orange (por `text`).
  - **State via bgColor alpha:** 77 = fresh, 51 = touched, 25 = mitigated.
  - `x2` = coord de criação (boxes usam `extend.right`) → **NÃO** usar para status ativo.
- **Campos oficiais:** `custom_ob_demand/supply_active`, `inside_demand/supply_zone`, `nearest_demand/supply_*`, `custom_ob_nearest_demand/supply_state`, counts. `demand/supply_zone_active` (x2-based) = **deprecated**.
- **Anti-erro:** **não interpretar genericamente por x2** nem por "acho que essa box é zona". Fonte = Pine v11 audited.
- **Uso no breakout:** **não usa OB/zonas** (família price/EMA/ADX/ATR/RSI + D1a). `reference_only`.

---

## 12. RAW vs SLIM

- **Hierarquia (project_authority/02):** TV visual > **RAW replay** > extractor fiel auditado (CFEL v2) > derivadas simples verificáveis > slim/proxy interpretativo (não-validatório).
- **CFEL v2 é o intérprete oficial do RAW.** Campos `official_for_backtest` (HIGH) são permitidos **com confiança declarada**. **Não** é o "slim proibido" — o proibido é o **slim v1** (`extract_replay_features_v1.py`, semântica NAS/SMC/OB/Bubbles errada, DELETE_CANDIDATE).
- **RAW XAU disponível (registry confirma conteúdo, não só existência):**
  - **4H:** 3 blocos contíguos (`2016-05-25→2020`, `2020→2023`, `2023→2026-05-25`; 5557+4636+5242 barras) + bloco combinado `XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW` (10074 barras). Todos `status: active`.
  - **1D:** `2012-06-19→2026-05-25` (3602 barras), `active`.
- **Upgrade vs bloco anterior:** o `raw_field_mapping.md` v1 dizia "existence checked, conteúdo não inspecionado". Agora o **registry confirma janelas e contagem de barras** (cobertura completa 2016-2026 em 4H, 2012-2026 em 1D). Resta confirmar na Rodada 1: (a) qual bloco 4H carrega o study RSI (a CFEL já extraiu `rsi_above_ma` com sucesso → existe); (b) cobertura do slim canônico v2 (re-extração full §8 step 6 pendente de autorização).
- **Regra:** RAW = source-of-truth para backtest sério; slim v2 canônico = reconciliação + features oficiais com confiança; **SLIM nunca = validação final.**

---

## 13. Feature availability matrix

| Feature | Needed V0/V1/D1a? | Available in RAW? | Derivable from OHLCV? | Requires indicator RAW payload? | Requires extractor? | Requires TV study values? | Confidence | Blocker? |
|---|---|---|---|---|---|---|---|---|
| OHLCV 4H | V0 | ✅ | — | não | não | não | HIGH | não |
| swing10 / body_pct / range | V0 (T1,T3) | ✅ (derivado) | ✅ | não | ✅ (post_pass) | não | HIGH | não |
| RSI / RSI_MA / rsi_above_ma | V0 (T4) | ✅ (study_values) | ❌ (é study TV) | sim (study) | ✅ (lê) | **sim** | HIGH | **não (RESOLVIDO)** |
| ATR14 (`atr14_wilder`) / ATR_MA20 | V3,V5 (R5)+SL | ✅ (derivado) | ✅ | não | ✅ (wilder) | não | HIGH (class=diag) | não (declarar) |
| ADX14 | V1,V5 (R1) | ✅ (Python) | ✅ | não | não (Python) | não | MEDIUM | não |
| EMA50/200 4H | V2,V5 (R2-R4) | ✅ (Python) | ✅ | não | não | não | HIGH | não |
| EMA50/200 **1D** (D1a) | **D1a (V6,V7)** | ✅ RAW 1D existe; **slim não extraído** | ✅ (de 1D) | não | **✅ (extrair 1D)** | não | MEDIUM | **SIM (build 1D + SHIFT1-audit)** |
| NAS (labels / dist) | não (ref) | ✅ | ❌ | sim | ✅ | parcial | HIGH | não (não-needed V0) |
| Bubbles | não (ref) | ✅ | ❌ | sim | ✅ | não | dir HIGH | não (não-needed V0) |
| Custom OB | não (ref) | ✅ | ❌ | sim | ✅ (Pine v11) | não | HIGH | não (não-needed V0) |

---

## 14. Blockers before rebuild

1. **D1a 1D pipeline — BLOCKER (V6/V7 apenas; V0-V5 livres).** Extrair slim canônico 1D (RAW 1D existe) → EMA50_1D/EMA200_1D → alinhamento *latest-closed-daily* (provar timezone/convenção open-close) → **SHIFT1-audit** ORIG-vs-SHIFT1 sem delta. Até lá, D1a não roda.
2. **ATR — declaração obrigatória (não-blocker).** Fixar: breakout usa `atr14_wilder` + `ATR_MA20 = SMA(atr14_wilder,20)`, divergente do ATR "oficial" CFEL (SMA/MA30). Não trocar sem teste desenhado.
3. **ADX — reconciliar implementação (não-blocker).** Adotar `adx_wilder` (backtest v1) como canônico do rebuild; declarar a diferença vs a versão ewm do sweep.
4. **Cobertura slim canônico v2 (não-blocker).** Confirmar na Rodada 1 que o slim v2 4H cobre 2016-2026 com RSI study presente em todos os blocos (re-extração full §8 pendente de autorização).
5. **Custos/gross (carryover, não-blocker).** Declarar: legacy sweep usou net @0.05R; revalidação v1 = gross. Não comparar diretamente.

**Não-blockers confirmados (features definidas/disponíveis):** RSI/RSI_MA, swing10, body_pct, ATR (wilder), ADX (Python), EMA 4H.

---

## 15. Updates made to raw_field_mapping

**SIM — atualizado** `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/raw_field_mapping.md` (apenas clarificação de mapping, sem inventar campo nem mudar estratégia):

- **RSI/RSI_MA:** corrigido de "recompute from OHLCV" → **"ler de study_values (TV 'Relative Strength Index' → RSI / RSI-based MA)"**; hard stop **levantado** (campo canônico official, HIGH).
- **ATR:** marcado que o breakout usa **`atr14_wilder`** (campo canônico, CFEL-class diagnostic) + ATR_MA20(SMA,20); divergência do ATR oficial CFEL declarada.
- **swing10:** fixada a fórmula canônica `close[i] > max(high[i-10:i])` (exclui atual), referência `extractor:419-423`.
- **ADX:** marcado Python `adx_wilder` (backtest v1) como implementação canônica; não é campo de slim.
- **D1a:** marcado **BLOCKER** — slim 1D não extraído; pipeline + SHIFT1-audit pendentes.
- **RAW availability:** atualizado de "existence checked" → registry confirma janelas/barras (4H 2016-2026, 1D 2012-2026).

(Hard stops §5 do arquivo reordenados: RSI_MA/ADX/ATR/swing **resolvidos**; D1a 1D alignment permanece o único blocker estrutural.)

---

## 16. Devil's Advocate

| Pergunta DA | Resposta |
|---|---|
| Nenhuma feature inferida por nome? | ✅ Cada feature rastreada a `extractor`/`backtest_v1`/CFEL com arquivo:linha. |
| RSI_MA definido ou HARD STOP? | ✅ **Definido** — study_values "RSI-based MA" (CFEL official HIGH). Hard stop levantado, não mascarado. |
| ADX definido ou HARD STOP? | ✅ **Definido** — `adx_wilder` Python (`backtest_v1:84`). Reconciliação ewm vs loop declarada. |
| ATR expanding definido ou HARD STOP? | ✅ **Definido** — `atr14_wilder > SMA(atr14_wilder,20)`; divergência CFEL declarada (não escondida). |
| D1 alignment definido ou HARD STOP? | ✅ Regra definida (latest-closed-daily) **mas marcado BLOCKER** (não mecanizado + SHIFT1-audit pendente). Honesto. |
| swing10 definido ou HARD STOP? | ✅ **Definido inequívoco** — `max(high[i-10:i])`, exclui atual (`extractor:419-423`). |
| NAS confundido com shapes/event store? | ✅ Não — label (pine_labels) ≠ study_value contínuo (`nas_dist_ema_atr`) ≠ event store, separados explicitamente. |
| Bubbles antigo/invertido reapareceu? | ✅ Não — usado o correto (BUY 0/2/4, SELL 6/8/10, POC 12); invertido marcado SUPERSEDED. |
| Custom OB interpretado genericamente? | ✅ Não — fonte = Pine v11 audited; x2 explicitamente NÃO usado para status. |
| RAW substituído por SLIM? | ✅ Não — RAW source-of-truth; v2 canônico = intérprete oficial com confiança; v1 slim = proibido, distinguido. |
| Nenhum backtest rodado? | ✅ Só leitura + docs. |
| Nenhuma plotagem? | ✅ Nenhum draw/MCP. |
| Nada operacional tocado? | ✅ Produção verificada íntegra (read-only). |
| Caminho B não recomendado? | ✅ Não recomendado. |

**DA verdict: PASS.**

---

*Read-only exceto docs/mapping. Nenhum backtest. Nenhuma plotagem. Nenhum MCP/chart/Telegram/broker. Nenhum RAW alterado (registry/extractor lidos; RAW `.gz` não aberto). Features rastreadas à CFEL canônica (`extract_replay_features.py` schema v2) + backtest implementado. Métricas legacy não reabertas aqui.*
