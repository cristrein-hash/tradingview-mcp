# XAU 4H BREAKOUT/D1a × L2/BPT — Measurement Audit

**Data:** 2026-06-17 · **Tipo:** auditoria de integridade da medição (antes de confiar nos números) · **NOT_VALIDATION.**
**Bloco:** auditoria — nenhuma estratégia/filtro/otimização nova; nenhuma plotagem/MCP/Telegram/produção/SLIM. Re-rodado o MESMO script com os mesmos params só para expandir o dump auditável (registrado).

---

## 1. Executive summary

Auditei a medição BREAKOUT/D1a × L2/BPT de ponta a ponta (código + dump + recálculo + DA independente). **Auditoria PASSOU (integridade limpa):** os 11 invariantes passam, os números **reproduzem exatamente** (re-run determinístico: immediate R4 +82.4R / retest R4 +74.6R idênticos), **sem look-ahead, sem SLIM, fills causais, R correto, pareamento correto, no-overlap outcome-blind**. Uma otimização **menor** de fill (entrada bookada em P mesmo quando o preço só alcançou P+0.15·ATR → até 0.15·ATR otimista).

**Conclusão de confiança:** os números são **confiáveis como MEDIÇÃO** (o que foi medido está correto e auditável). Mas **NÃO são evidência de edge promovível** — a afirmação defensável é estreita e condicional (§10). Correção de enquadramento: **não justapor +82.4R (176 eventos) vs +74.6R (141 eventos) como universos iguais**; a comparação honesta é o **pareado** (+15.6R imediata vs +74.6R retest nos MESMOS 141) **mais** o custo de oportunidade (31 runaways que o retest não embarca). **DA: PASS (integridade); edge não-promovível.**

---

## 2. Artefatos auditados

- **Script:** `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/run_l2bpt_breakout_test.py` (RAW-only via `build_entry_anatomy.extract_raw_rows()` → extractor auditado `scripts/extract_replay_features.py` in-memory; **zero slim**).
- **Métricas:** `compute_l2_bpt_metrics.py` (read-only do dump).
- **Inputs RAW:** 3 blocos contíguos `raw_replay/XAUUSD/4H/*.gz` + `generated/xau_1d_ema_features.jsonl` (EMA1D de RAW 1D).
- **Outputs:** `results/l2_bpt_breakout_test_summary.json` (tracked), `l2_bpt_metrics_only_{summary.json,tables.csv}` (tracked), `l2_bpt_audit_sample.csv` (novo, tracked), `l2_bpt_events_full.jsonl` (**dump per-evento, 577 linhas, gitignored**, regenerável).
- **Commit base:** `3494726` (métricas); este bloco expande o dump + audita.

---

## 3. Definições operacionais (do código, com linha)

**Universo:** barras `i∈[200, n-1]` com evento **T8** = `close_above_swing_high_10` (trigger T1) ∧ `close>open` ∧ `body_pct≥0.5` ∧ `rsi_above_ma` ∧ **EMA stack** (`ema50>ema200 ∧ close>ema200`) ∧ **D1a** (`d1a_at(Tc[i]-14400).d1a_pass`). `run_l2bpt:84-91`. 577 eventos; 176 no-overlap.

**A — Imediata T8:** entry = `open[i+1]` (`:104`); stop = `low[i]−0.5·ATR` (`:104`); target = `entry+{2,3,4}·risk`; time-stop 24 barras; **sem BE** (limpo); stop-first intrabar (`sim_from :48-51`).

**B — Retest à polaridade (l2_touch_fix1):** **polaridade P = `swing_high_10[i]`** = `max(high[i-10:i])` = o nível rompido (Pattern #1; `extract:421`). Retest = primeiro `k∈[i+1,i+24]` com `low[k] ≤ P+0.15·ATR[i]` (`:113`). Fill = limit em **P** (`:172`). SL = **`P − 1.0·ATR[i]`** (buffer fixo causal; `:168`). target = `P+{2,3,4}·risk` (risk=1·ATR). time-stop 24 da barra de fill; stop-first. (Variante `l2_touch` estrutural usa `swing_low_10[i]−0.1ATR` → aborta ~tudo por R>1.5ATR; **não** é a carregada.)

**C — Reclaim (l2_reclaim_fix1):** após touch, primeiro `m` com `close>open ∧ body≥0.5 ∧ close>P+0.1·ATR`; entry=`close[m]`; SL=`P−1·ATR`; R-ceiling 1.5ATR. Causal (close de bar fechado). n=24.

**D — Runaways:** `retested=False` = nenhum `k∈[i+1,i+24]` com `low≤P+0.15ATR`. 35/176; 31 com imm_R4>0 (runaway perdido), 4 com imm_R4≤0 (toploss evitado).

**E/F/G/H — Pareado:** MESMO evento `i` (mesma validação T8, mesmo ts), B filled, compara `imm_R4` vs `l2f_R4` (`compute_l2:88-93`). E=imm≤0&ret>0 (6); F=imm>0&ret≤0 (6); G=ambos>0 (43); H=ambos≤0 (86).

**No-overlap:** `no_overlap = i>last_end`; `last_end=i+24` quando mantido (`:93-95`) — **por índice de barra, antes de qualquer outcome** (outcome-blind).

---

## 4. Tabela de amostra auditável

`results/l2_bpt_audit_sample.csv` — **45 linhas** em 7 categorias (10 imm winners · 10 imm losers · 5 retest winners · 5 retest losers · 5 runaways · 6 retest-improves (imm lose/retest win) · 6 retest-worsens (imm win/retest lose); E/F só têm 6 cada no universo). Campos: event_id, timestamp, T8_pass, polarity_level, polarity_source, retest_filled, retest_fill_time, immediate_entry/stop/target/R/exit, retest_entry/stop/target/R/exit, no_overlap, notes. (Categorias-fonte: imm_w 80, imm_l 96, ret_w 49, ret_l 92, runaways 35, improves 6, worsens 6.)

---

## 5. Invariantes (DA independente — leitura de código + spot-check)

| # | Invariante | Verdict |
|---|---|---|
| 1 | T8 D1a CAUSAL (`close_time≤bar_open`, `Tc[i]-14400`), não ORIG | **PASS** |
| 2 | Sem SLIM (RAW via extractor auditado in-memory) | **PASS** |
| 3 | Polaridade `swing_high_10[i]` conhecida no bar i (não-futuro) | **PASS** |
| 4 | Retest fill causal (`low[k]≤P+0.15ATR[i]`, ATR do bar i) | **PASS** |
| 5 | L2 SL (fix1) = `P−1ATR` fixo, NÃO usa low da barra de toque | **PASS** |
| 6 | R = `(exit−entry)/risk`, risco correto (retest=1ATR) | **PASS** |
| 7 | Imediata vs retest no MESMO evento | **PASS** |
| 8 | No-overlap outcome-blind (por índice, pré-outcome) | **PASS** |
| 9 | Runaway = sem retest em 24 barras; 31:4 confere | **PASS** |
| 10 | Intrabar stop-first (conservador) | **PASS** |
| 11 | Same-bar fill/stop tratado; entry-em-P | **PASS (otimismo ≤0.15ATR)** |

Spot-check de linhas do dump: 0 inconsistências (l2f_R4=4.0↔target; filled=false↔R null; retested↔fill_time). Re-run determinístico: métricas idênticas.

---

## 6. Métricas recalculadas (transparente, do dump auditado)

| Grupo | n | filled | WR | sumR | avgR | medR | PF | maxDD | streak | tgt/stop/time |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| Immediate T8 (R4) | 176 | 176 | 45.5% | +82.4 | 0.468 | −0.25 | 1.97 | −9.1 | 7 | 26/82/68 |
| Retest l2_touch_fix1 (R4) | 141 | 141 | 34.8% | +74.6 | 0.529 | −1.0 | 1.82 | −7.0 | 7 | 36/90/15 |
| Reclaim (R3) | 24 | 24 | 33.3% | +4.6 | 0.191 | −1.0 | 1.32 | −9.0 | 9 | 5/14/5 |
| **Paired (141, R4)** | 141 | — | — | **imm +15.6 / retest +74.6** | — | — | — | — | — | E6·F6·G43·H86 |
| Runaways (no retest) | 35 | 0 | — | — | — | — | — | — | — | 31 lost : 4 avoided |

(stop_be=0: BE desligado neste teste — declarado.) Confere com `l2_bpt_metrics_only_summary.json`.

---

## 7. Diferenças vs relatório anterior

- **Números: NENHUMA diferença** — reproduzidos exatamente (determinístico).
- **Enquadramento (sharpening):** o lado-a-lado "+82.4R (176) vs +74.6R (141)" mistura universos; a leitura honesta é o **pareado** (+15.6 vs +74.6 nos 141) **+** custo de runaways (31). O relatório anterior já trazia o pareado e o caveat; a auditoria reforça não tratar os totais como universo igual.
- **Achado de higiene (DA):** `R_FLOOR` aparece em `canonical_reused` mas **não é usado** no caminho fix1 (param morto) — cosmético, sem efeito nos números.

---

## 8. Riscos restantes (mesmo com invariantes OK)

1. **Enquadramento de denominador** (totais de universos diferentes) — usar pareado.
2. **Custo de oportunidade**: retest não embarca os ~31 runaways (só vale condicional a haver retest, ~80%).
3. **Amostra discriminante fina**: só ~12 eventos (6+6) separam A de B; perto de ruído.
4. **Seleção/multiplicidade**: 21 células medidas, sem Bonferroni; B@R4 é escolha post-hoc da "variante viável".
5. **Gross R**: sem custos/spread/slippage + otimismo de fill ≤0.15ATR — comprimiriam a vantagem por trade.
6. **Poder do holdout**: n~73-90, CIs largas; sumR com target R4 é concentration-prone (verificar contribuição top-5 antes de qualquer claim de edge).

---

## 9. O que PODE ser confiado

- A **integridade da medição**: sem look-ahead, sem SLIM, fills causais, R correto, pareamento correto, no-overlap outcome-blind, determinístico.
- Os **fatos estruturais**: retest ocorre ~80%; 31:4 runaway:toploss; SL P−1ATR é R-viável; reclaim corta N (141→24).
- A afirmação **condicional**: *dado que há retest (~80% dos breakouts D1a), entrar no retest da polaridade com stop fixo 1ATR supera materialmente perseguir o candle de rompimento nos mesmos eventos* (+74.6 vs +15.6).

## 10. O que NÃO pode ser confiado

- Que o retest seja **superior em full-universe** (não é — abre mão de 31 runaways; totais ~empatam).
- Qualquer **claim de edge promovível** (gross, sem custos, sem OOS, B@R4 post-hoc, amostra discriminante ~12, holdout fino).
- O lado-a-lado de totais como se fossem o mesmo universo.

---

## 11. Devil's Advocate

DA independente spawnado (leu código + dump). Veredito: **integridade limpa (11/11 invariantes PASS, 1 otimismo de fill menor); números reais e reproduzíveis; NÃO promovível como edge.**
- ✅ Medição auditável. ✅ O que foi medido está claro (§3). ✅ Retest/polaridade sem ambiguidade. ✅ Sem look-ahead. ✅ Sem SLIM. ✅ Fill otimista só ≤0.15ATR (registrado). ✅ Pareamento correto. ✅ Nenhuma métrica anterior mudou. ✅ Riscos residuais listados. ✅ Nenhuma plotagem/MCP/Telegram/broker. ✅ L1 intacta. ✅ Caminho B não recomendado. ✅ SHORT não aberto.

**Auditoria: PASS (parcial no sentido edge — integridade OK, edge não-promovível).**

---

*Read-only. RAW-only (zero slim). Re-run determinístico (mesmos params, dump expandido). Outputs auditáveis: `l2_bpt_audit_sample.csv` + `l2_bpt_metrics_only_*` (tracked); dump gitignored. Nenhuma plotagem.*
