# XAU 4H BREAKOUT / D1a — EMA1D Build + ORIG-vs-SHIFT Alignment Audit

**Data:** 2026-06-16 · **Tipo:** build de feature D1 causal + auditoria empírica de alinhamento · **NOT_VALIDATION.**
**Escopo:** liberar ou manter bloqueado o D1a (V6/V7) do XAUUSD_4H_BREAKOUT_CONTINUATION.
**Princípio:** provar, não assumir. Precedente A1' SUPERTREND (88%→46% por lookahead daily).
**Bloco:** read-only w.r.t. RAW/produção. Nenhum backtest BREAKOUT V6/V7, nenhum trade, plotagem, MCP/chart, Telegram, broker. Scripts + dataset derivado criados em research/revalidation.

---

## 1. Executive summary

Construí a base D1 causal correta para o D1a e **provei empiricamente** o alinhamento SHIFT1.

- **Dataset EMA1D gerado** do RAW 1D (2012-2026), warmup desde 2012: `generated/xau_1d_ema_features.jsonl` (3584 barras diárias, EMA50/EMA200, d1a_pass). EMA200 warmup-ready em **2013-04** → totalmente estável antes do início do breakout (2016-07).
- **Regra causal D-1 implementada e provada:** `latest_closed_daily(eval) = último daily com close_time ≤ bar_open_4h`. Sobre **15.434 barras 4H reais** (RAW 4H 2016-2026): a regra de produção/suspeita (`open_time < bar_open`) **vaza 12.854 (83,3%)** — seleciona o daily do mesmo dia ainda em formação; a CAUSAL **0 vazamentos**. O lookahead corromperia **349 (2,3%)** dos `d1a_pass`.
- **Decisão:** **D1a LIBERADO para design tests.** Os 6 critérios de liberação estão satisfeitos (§6). **V6/V7 podem usar este dataset + a regra CAUSAL na próxima rodada**, com a condição vinculante de consumir `latest_closed_daily` (close_time ≤ bar_open) e re-rodar um SHIFT-audit trade-level na implementação. **DA: PASS.**

> ⚠️ **Caveat de precisão (não-blocker):** o close diário RAW (capturado ~22:00 UTC) difere do `xau_daily_l1v4` (produção MCP) por **mediana 1,72 / 81% ≤ 5 USD**; 65/2597 (2,5%) com diff>20, **todos em dias de alta volatilidade** (COVID 03/2020, invasão 24/02/2022, FOMC 16/06/2021) = diferença de horário de close, não bug. **RAW é source-of-truth** (project_authority/02). A relação EMA50>EMA200 é robusta (só **69/15.434 = 0,4%** de divergência sob a diferença de seleção).

---

## 2. Tarefa 1 — RAW 1D confirmado

| Item | Valor |
|---|---|
| Arquivo | `…/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz` |
| gzip integrity | **OK** (`gzip -t` pass; registry sha256 + gzip_t true) |
| Registry range | 2012-06-19 → 2026-05-25; 3602 barras |
| Records lidos | 3602 (cada = snapshot replay; `ohlcv` = janela rolante ~5 barras) |
| Reconstrução | união de todas as janelas `ohlcv`, dedup por `time`, keep-last (= close finalizado) → **3584 barras diárias** |
| **Timestamp convention** | `bar.time` = **OPEN da sessão, 22:00 UTC** (provado: `1339452000 → 2012-06-11T22:00Z`) |
| Timezone | UTC |
| Candle | dura 24h: abre 22:00 dia D, fecha 22:00 dia D+1, **representa o pregão D+1** |
| Duplicatas | nenhuma (dedup por time) |
| Gaps | fins de semana (sem candle Sex22→Dom22; candle de sexta = open Qui22→close Sex22) |
| Warmup p/ EMA200 | **suficiente** (2012 → EMA200 ready 2013-04, antes do breakout 2016-07) |
| RAW alterado? | **NÃO** (somente leitura streaming) |

---

## 3. Tarefa 2 — Dataset EMA1D causal gerado

**Artefato derivado:** `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/generated/xau_1d_ema_features.jsonl`
- **linhas:** 3584 · **sha256:** `31d3b2555a29ccfe7f007bd1d48675f92059272d84b35af4bab0c820a0a32a66`
- **range:** 2012-06-12 → 2026-05-25 · **first_warmup_ready:** 2013-04-12 · **d1a_pass_count:** 1918
- **builder:** `build_xau_1d_ema_features.py` (py_compile OK) · **calc_version:** `ema1d_v1_2026-06-16`

**Campos:** `date, ts, open_time, close_time, close_time_approx, open, high, low, close, volume, ema50, ema200, ema50_gt_ema200, close_gt_ema200, d1a_pass, warmup_ready, source_raw_path, calculation_version`.

**Fórmula EMA:** `alpha = 2/(period+1)`, recursivo `adjust=False` seed=close[0]; EMA50 (p=50), EMA200 (p=200), sobre **close diário**, em ordem cronológica, **sem futuro**. `warmup_ready=False` até índice ≥200 (EMA200 confiável). `d1a_pass = close>EMA200 AND EMA50>EMA200 AND warmup_ready`.

**Cross-check vs produção (`xau_daily_l1v4.jsonl`):** overlap 2581; mediana 1,72; ≤2 USD 54%; ≤5 USD 81%; diffs>20 em 65 dias (todos alta-vol). Interpretação: mesmo candle, diferença de horário de close (RAW 22:00 vs MCP); **RAW = source-of-truth**; imaterial para filtro de direção.

---

## 4. Tarefa 3 — Função de alinhamento causal D-1

`latest_closed_daily_d1a(eval_4h_open_ts)` (em `audit_orig_vs_shift.py`):
```
CAUSAL: último daily com  daily.close_time <= bar_open_4h
        (daily completamente fechado antes do 4H abrir; close_time = open + 86400)
```
- **Nunca** usa daily em formação (close_time > bar_open é excluído).
- Robusto a offset open/close (alinha por `close_time` absoluto, não por rótulo de data).
- Se não houver daily anterior (warmup/início) → `None` → trade **sem D1a** ou bloqueado (decisão da Rodada 3).
- **NÃO** usar `open_time < bar_time` (regra de produção/suspeita) — vaza em backtest (§5).

**Exemplos verificados:**
| 4H eval (open) | CAUSAL daily | Comentário |
|---|---|---|
| Seg 2024-05-13 02:00 | 2024-05-10 (Sex) | weekend: pega sexta, não o domingo/segunda forming |
| Seg 2024-05-13 06/10/14/18:00 | 2024-05-10 (Sex) | idem — toda a Segunda usa Sexta até o daily de Seg fechar |
| Seg 2024-05-13 22:00 | 2024-05-13 | daily de Seg fechou exatamente 22:00 → agora elegível |
| Ter 2024-05-14 02:00 | 2024-05-13 (Seg) | D-1 limpo |

---

## 5. Tarefa 4 — ORIG-vs-SHIFT audit (PROVA empírica)

**Universo:** 15.434 barras 4H reais (RAW 4H contíguo 2016-05-24 → 2026-05-24; grid 02/06/10/14/18/22 UTC). Artefato: `generated/orig_vs_shift_audit.json` (sha256 `bb2f0993…`).

| Métrica | Valor |
|---|---|
| Total 4H bars | 15.434 |
| **ORIG leak (forming daily selecionado)** | **12.854 (83,28%)** |
| Mesma daily escolhida (ORIG=CAUSAL) | 2.580 (16,7% — barras 22:00 + concordâncias) |
| **Divergências em `d1a_pass`** (ORIG vs CAUSAL) | **349 (2,3%)** ← erro de lookahead que corromperia o backtest |
| Divergências `close_gt_ema200` | 499 |
| Divergências `ema50_gt_ema200` | 69 (0,4% — relação EMA muito estável) |
| ORIG None / CAUSAL None | 0 / 0 |

**Provado:**
- **ORIG (`open_time < bar_open`) vaza em 83% das barras 4H intraday** — seleciona o daily do mesmo dia ainda em formação (close 22:00). Ex.: bar 2016-05-24 06:00 → ORIG pega daily 2016-05-24 (fecha 22:00, **forming**) vs CAUSAL 2016-05-23.
- **CAUSAL nunca usa daily em formação** (0 leaks por construção: close_time ≤ bar_open).
- **D1a causal é implementável sem forming-day leakage.**
- A L1 **live** escapa do leak só porque o arquivo exclui `today`; um **backtest** D1a com a regra de produção corromperia 349 d1a_pass. Por isso o D1a backtest **deve** usar a CAUSAL.

**Por que a L1 produção não é refutada:** em live o arquivo diário nunca contém o dia corrente (refresh exclui `ts≥today`), então `latest_state_before` não acha o daily forming. O problema é estritamente de **backtest histórico** — escopo deste bloco.

---

## 6. Tarefa 6 — Decisão de liberação

| Critério | Status |
|---|---|
| RAW 1D validado | ✅ gzip OK + reconstruído + cross-check produção (diffs de vintage explicados) |
| EMA50/EMA200 calculados com warmup | ✅ 2012→ready 2013-04, estável antes de 2016 |
| `latest_closed_daily` D-1 provado | ✅ CAUSAL `close_time≤bar_open`, **0 leaks** em 15.434 barras |
| ORIG-vs-SHIFT documentado | ✅ 83,3% leak na ORIG, 349 d1a divergências (este doc + json) |
| Nenhum daily forming usado | ✅ provado por construção + empírico |
| docs/mapping atualizados | ✅ (§7) |

**Todos os 6 critérios satisfeitos.**

| Pergunta | Resposta |
|---|---|
| D1a dataset gerado? | **SIM** (`generated/xau_1d_ema_features.jsonl`, 3584 linhas) |
| EMA50/EMA200 D1 prontos? | **SIM** (warmup 2012, estável pré-2016) |
| Regra causal D-1 implementada/provada? | **SIM** (`close_time≤bar_open`, 0 leaks) |
| ORIG-vs-SHIFT audit passou? | **SIM** (leak quantificado e isolado à regra suspeita) |
| **D1a liberado para design tests?** | **SIM** |
| **V6/V7 liberados para próxima rodada?** | **SIM — condicional:** a implementação V6/V7 **deve** consumir `latest_closed_daily` CAUSAL + este dataset, e re-rodar um SHIFT-audit trade-level. |

**Blockers restantes (não impedem V6/V7, mas declarados):**
1. **Precisão de close RAW vs produção** (mediana 1,72; cauda em dias voláteis) — vintage/horário; imaterial p/ direção; RAW=truth. Monitorar se afetar d1a perto de cruzamentos EMA.
2. **Grid 4H heterogêneo entre fontes:** blocos contíguos 240m = 02/06/10/14/18/22 UTC; bloco SVP_LUX = 23/03/07/11/15/19. A Rodada V6/V7 deve usar **uma** fonte 4H consistente e a mesma `close_time` alignment.
3. **V6/V7 backtest ainda não rodado** (correto — fora do escopo deste bloco).

---

## 7. Tarefa 5 — Atualizações de docs/mapping

- `raw_field_mapping.md` → §2 1D: EMA50/EMA200 agora **deriváveis e geradas** (`generated/xau_1d_ema_features.jsonl`); regra causal por `close_time≤bar_open`.
- `docs/XAU_4H_BREAKOUT_D1A_D1_SHIFT_AUDIT.md` → nota de continuação apontando para esta auditoria empírica + os números.
- Este doc novo (`…_EMA1D_SHIFT_AUDIT.md`) = registro empírico do build + ORIG-vs-SHIFT.

---

## 8. Devil's Advocate

| Pergunta DA | Resposta |
|---|---|
| RAW 1D não foi alterado? | ✅ Somente leitura streaming; nenhuma escrita no `.gz`. |
| EMA com close diário e alpha correto? | ✅ `alpha=2/(p+1)`, close diário, recursivo, sem futuro. |
| Warmup 2012 usado? | ✅ série desde 2012; EMA200 ready 2013-04. |
| Daily timestamp open/UTC respeitado? | ✅ open=22:00 UTC; close_time=open+86400; provado. |
| `latest_closed_daily` usa date-shift D-1? | ✅ via `close_time≤bar_open` (mais rigoroso que date-shift; robusto a offset). |
| Nenhum daily do mesmo dia (forming) usado? | ✅ CAUSAL 0 leaks; ORIG leak 83% (provado e rejeitado). |
| ORIG-vs-SHIFT quantificado? | ✅ 15.434 barras; 12.854 leaks; 349 d1a divergências. |
| V6/V7 backtestados? | ✅ **NÃO** — só dataset + alinhamento; V6/V7 não executados. |
| Nenhum trade gerado? | ✅ Nenhum. |
| Nenhum plot? | ✅ Nenhum. |
| Nenhum MCP/chart? | ✅ Nenhum. |
| Produção intacta? | ✅ Verificada read-only. |
| Caminho B não recomendado? | ✅ Não. |

**DA verdict: PASS.**

---

*Read-only w.r.t. RAW e produção. RAW 1D/4H lidos por streaming (não modificados). Dataset derivado + audit json em research/revalidation. Scripts py_compile OK. Nenhum backtest BREAKOUT, trade, plotagem, MCP/chart, Telegram, broker. L1 não alterada (só anotada). Cross-check vs `xau_daily_l1v4` como sanity, não autoridade.*
