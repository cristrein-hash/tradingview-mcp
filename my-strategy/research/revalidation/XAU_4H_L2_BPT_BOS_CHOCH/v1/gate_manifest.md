# Gate Manifest — XAU 4H LONG L2/BPT BOS-CHoCH (census v1)

**Data:** 2026-06-17 · **Tipo:** definição congelada para censo/reconstrução mecânica · **NOT_VALIDATION (reconstruction census / mechanical baseline / hypotheses-only).**
**Validação final = regra congelada + OOS/forward DEPOIS.** 2019-2026 contém histórico onde a estratégia foi construída visualmente → é **censo**, não validação.

---

## 0. Universo
- Símbolo **XAUUSD** (PEPPERSTONE), TF **4H**, direção **LONG**, janela **2019-01-01 → 2026** (censo).
- Fonte: **RAW replay `.gz` ONLY** (extractor auditado in-memory; **zero slim** — `feedback_never_use_slim_features`).

## 1. Estrutura (gates, CLOSE-ONLY-CAUSAL)
1. **Pivot Williams 5/5 SHIFT5:** PH em `j` se `high[j] > max(high[j-5..j-1]) AND high[j] > max(high[j+1..j+5])`; **só confirmado/usável em bar `i ≥ j+5`**. PL análogo. No bar `i`, só pivots com `j ≤ i-5`.
2. **Contexto bearish** (pré-CHoCH): última sequência de pivots confirmados em LH/LL (≥1 lower-low OU lower-high recente).
3. **protected_LH (causal):** o **PH confirmado imediatamente anterior ao PL confirmado mais recente** da fase bearish (não `max`). É o LH estrutural que originou a última perna de baixa.
4. **CHoCH bullish:** `close[i] > protected_LH + 0.2·ATR[i]` em contexto bearish → fixa **polaridade = protected_LH.price** (não atualiza com BOS).
5. **BOS bullish (contado; tag):** pós-CHoCH, `close[i] > PH_anterior_em_sequência_HH-HL + 0.2·ATR[i]`.
6. **retest:** `low[k] ≤ polaridade + 0.15·ATR` (k após CHoCH, janela ≤ N_RETEST=24 bars).
7. **reclaim (aceitação):** bar verde `close>open`, `body_pct ≥ 0.5`, `close > polaridade + 0.1·ATR`.
8. **Entrada:** **close do reclaim** (close-only-causal; documentado; alternativa next-open registrada como variante futura, NÃO usada no census v1).
9. **SL estrutural:** `min(PL_confirmado_mais_recente_abaixo_da_entrada, low recente) − 0.1·ATR`; **R-bounded: floor 0.3·ATR, ceiling 1.5·ATR → ABORT** (`R_ceiling`).
10. **Target:** versões fixas **+2R / +3R / +4R** (comparação, **sem otimizar**). Intrabar **stop-first**. Time-stop = 24 bars (documentado).
11. **Invalidação (pré-entrada):** `close < polaridade` estrutural (ou < swing low estrutural) → CHoCH cancelado, sem entrada.
12. **Dedup:** **uma posição por episódio estrutural** (por CHoCH/polaridade); novo CHoCH exige nova polaridade.

## 2. Overlays contextuais (TAGS, não filtro duro)
Registrados por trade, **não** bloqueiam no census v1:
- `at_D1_demand` (BPT v2; **deferido** se exigir extração 1D pesada — marcado `tag_pending` no census v1) ·
- `inside_demand_zone` / `inside_supply_zone` / `nearest_supply_dist` (Custom OB v11, do extractor 4H) ·
- **NAS LONG/SHORT** (first-appearance de labels; nunca TOP/BOTTOM nem `*_SIGNAL`) ·
- Market Order Bubbles (buy/sell/large) · RSI / rsi_exhaustion (rsi_div) · supply_overhead · Reason Atlas block/category (macro-leg) — quando derivável causalmente.

## 3. Hard stops (parar o census se)
- Algum gate depender de feature não-causal · protected_LH não reconstruível · CHoCH/BOS usar futuro · retest/reclaim ambíguo · SL estrutural não R-viável · RAW mapping não fechar.

## 4. Status
- `RECONSTRUCTION_CENSUS / MECHANICAL_BASELINE / HYPOTHESES_ONLY`. Sem produção, sem promoção, sem OOS aqui. Detector census v1 = **aproximação causal do L2 v2 SMC** (fidelidade de detector = risco a auditar; refino em v2).
