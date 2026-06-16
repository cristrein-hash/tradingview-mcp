# XAU 4H BREAKOUT / D1a — D1 Pipeline + SHIFT1 Alignment Audit

**Data:** 2026-06-16 · **Tipo:** auditoria rigorosa de pipeline 1D + alinhamento SHIFT1 · **NOT_VALIDATION.**
**Escopo:** liberar ou manter bloqueado o D1a (V6/V7) do XAUUSD_4H_BREAKOUT_CONTINUATION.
**Princípio do bloco:** não aceitar "parece causal" — **provar**. Precedente: A1' SUPERTREND colapsou 88%→46% por lookahead daily não auditado.
**Bloco:** read-only exceto docs/mapping. Nenhum backtest, V6/V7, trade, plotagem, MCP/chart, Telegram, broker, produção, RAW alterado.

---

## 1. Executive summary

O pipeline 1D **existe** e foi localizado: `my-strategy/core/regime/build_daily_features.py` + `my-strategy/core/regime_l1/regime_l1_v4.py` + dados `xau_daily_l1v4.jsonl` (2597 barras, 2016-05-24→2026-06-15) + RAW 1D `XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz` (3602 barras).

**Achado central (provado empiricamente, §5-6):** a regra de alinhamento de **produção** `latest_state_before` (`t < bar_time_unix`, com `t = midnight(ts)`) **NÃO é causal para barras 4H intraday** — seleciona o **daily do mesmo dia calendário** (ainda em formação) para qualquer 4H em 04:00/08:00/12:00/16:00/20:00. **Só a barra das 00:00 (e barras sem daily same-day, ex. fim de semana) recebe D-1 limpo.** A L1 **live** escapa disso só porque o arquivo diário **exclui `today`** (a barra forming nunca está no arquivo); um **backtest** sobre o histórico completo **vazaria**.

**Dois mismatches adicionais:**
- **SMA, não EMA.** O pipeline diário canônico computa `ma_50 = SMA(close,50)` e `ma_200 = SMA(close,200)` — **não** os `EMA50_1D/EMA200_1D` que o D1a exige. D1a precisa de uma etapa de cálculo EMA nova.
- **Warmup.** EMA200_1D precisa ~200 barras diárias; o arquivo `xau_daily_l1v4.jsonl` começa em 2016-05-24 (warmup só ~2017-03), enquanto os trades do breakout começam 2016-07. → usar o **RAW 1D desde 2012** para warmup completo.

**Decisão:** **D1a permanece BLOQUEADO para V6/V7.** Mas o hard-stop de alinhamento é **rebaixado de "indefinido" para "regra definida e provada"** — a regra causal correta está especificada e demonstrada (§7). Falta **implementar** (EMA build + date-shift D-1 + SHIFT1-audit empírico ORIG-vs-SHIFT) antes de liberar. **V0-V5 seguem liberados** (não dependem de 1D). **DA: PASS.**

---

## 2. Fontes 1D localizadas (Tarefa 1)

| Fonte | Path | Papel |
|---|---|---|
| Builder de features diárias | `my-strategy/core/regime/build_daily_features.py` | computa ma_50/ma_200(SMA)/rsi_14/rsi_ma_14/slope_20_pct/atr_14 |
| Classificador regime | `my-strategy/core/regime_l1/regime_l1_v4.py` | `classify()` + **`latest_state_before()`** (alinhamento) |
| Refresh incremental | `my-strategy/core/regime_l1/refresh_regime_l1_v4.py` | append-only via MCP D; **exclui `ts >= today`** |
| Dados diários (gitignored) | `my-strategy/core/regime_l1/xau_daily_l1v4.jsonl` | 2597 barras, 2016-05-24→2026-06-15 |
| Manifest | `…/xau_daily_l1v4.manifest.json` | bars 2597, sha256_16 `67e07fc6…`, regime_last BEAR |
| Classifications | `…/regime_l1_v4_classifications.jsonl` | regime D-1 per bar |
| **RAW 1D** | `…/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz` | 3602 barras; integridade gzip_t+sha256 OK (registry) |
| (alt.) | `my-strategy/strategies/candidates/regime_classifier_v3/xau_daily_with_features.jsonl` | base regime v3 (referência) |

---

## 3. Cobertura 1D (Tarefa 2)

| Item | Valor | Evidência |
|---|---|---|
| Range (arquivo daily L1) | 2016-05-24 → 2026-06-15 | head/tail `xau_daily_l1v4.jsonl` |
| Barras (arquivo daily) | 2597 | manifest |
| Range (RAW 1D) | 2012-06-19 → 2026-05-25 | registry `replay_range_real` |
| Barras (RAW 1D) | 3602 | registry |
| **Timestamp convention** | **`ts` = data de ABERTURA do candle diário** (TradingView `bar.time`=open; `refresh:69` `datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")`) | código + dados |
| Timezone | UTC | `utcfromtimestamp` / registry `…UTC` |
| Gaps | fins de semana ausentes (ex.: 2016-05-28 Sáb, 05-29 Dom ausentes; Sex 05-27 → Seg 05-30) | dados |
| Duplicatas | nenhuma (refresh valida monotonicidade + `len(set)`) | `refresh:93-95` |
| **Forming bar atual** | **NUNCA no arquivo** — refresh mantém só `ts < today` (`refresh:78`) | código |
| Cobre o período do rebuild? | **Sim** (4H breakout 2016-2026 ⊂ RAW 1D 2012-2026); RAW 1D dá warmup EMA200 | registry |

**Convenção provada:** cada linha diária dada por `ts` = data de open; o candle datado `D` cobre `[D 00:00, D+1 00:00)` (UTC) e seu **close só é conhecido em D+1 00:00**. (Confirmar a hora exata de close/abertura da sessão do candle XAU do chart fonte é refinamento; a regra causal §7 é robusta a essa hora — ver §7.)

---

## 4. Features D1 — reprodutíveis? (Tarefa 3)

| Feature D1a | Existe no pipeline? | Fórmula no pipeline | Status p/ D1a |
|---|---|---|---|
| `close_1D` | ✅ | OHLCV diário | OK |
| `EMA50_1D` | ❌ **não** | pipeline computa `ma_50 = SMA(close,50)` (`build_daily_features:78`) | **FALTA — precisa EMA** |
| `EMA200_1D` | ❌ **não** | pipeline computa `ma_200 = SMA(close,200)` | **FALTA — precisa EMA** |
| (aux) rsi_14/atr_14/slope | ✅ | RSI Wilder, ATR Wilder, linreg slope | não usados por D1a |

**Mismatch SMA vs EMA:** o D1a especificado (gate_manifest §4: `close_1D>EMA200_1D AND EMA50_1D>EMA200_1D`) exige **EMA**; o pipeline canônico só tem **SMA** (`ma_50/ma_200`). O `htf_1d` legacy do sweep usava EMA (`ewm span=50`), mas `htf_1d ≠ D1a` (já documentado). → Para mecanizar D1a fielmente:
- computar `EMA50_1D`, `EMA200_1D` sobre `close` diário, `α = 2/(period+1)`;
- **bar fechado**, sem futuro;
- **warmup ≥ 200 barras diárias** → construir do **RAW 1D 2012** (não do arquivo que começa 2016) para o breakout 2016 ter EMA200 já estabilizada.

(Não decidir aqui SMA-vs-EMA por conveniência: o spec diz EMA; manter EMA, declarar.)

---

## 5. Regra de alinhamento 4H→1D — duas candidatas (Tarefa 4)

| Regra | Definição | Implementação |
|---|---|---|
| **PROD (produção L1)** | `latest_state_before`: último daily com `midnight(ts) < bar_time_unix` | `regime_l1_v4.py:53-66` |
| **CAUSAL (proposta D1a)** | `latest_closed_daily`: último daily com **`date(ts) < date(eval_bar_4h_UTC)`** (date-shift D-1) | a implementar |

**Por que a PROD não serve para backtest:** `t = midnight(ts)` = 00:00 do dia de open. Para um 4H em `D HH:00` com `HH>0`, o daily `D` tem `t = D 00:00 < D HH:00` → **selecionado**, mas o candle `D` só fecha em `D+1 00:00` → **lookahead** (usa close de fim-de-dia que não existe ainda). A PROD só dá D-1 limpo quando `HH=00` ou quando não há daily same-day (fim de semana).

**Por que a CAUSAL é segura:** exige `date(daily) < date(eval)`. Para qualquer 4H no dia `X`, o último daily elegível é dado `≤ X-1`, cujo candle fechou em `X 00:00 ≤` qualquer 4H de `X`. → **sempre fechado, nunca lookahead.** No pior caso é conservadora (levemente stale por algumas horas se a sessão diária fechar antes de 00:00), **jamais** antecipa informação.

---

## 6. Testes de borda — PROVA empírica (Tarefa 5 + 6)

Computado read-only sobre `xau_daily_l1v4.jsonl` real (datas ao redor do gap Sex 2016-05-27 → Seg 2016-05-30; Sáb 28/Dom 29 ausentes). **Não é backtest** — é demonstração lógica do seletor.

| 4H eval bar (UTC) | PROD `t<bt` | CAUSAL `date<` | same-day leak? |
|---|---|---|---|
| Seg 2016-05-30 **00:00** | 2016-05-27 | 2016-05-27 | **no** (ok) |
| Seg 2016-05-30 **04:00** | **2016-05-30** | 2016-05-27 | **YES LOOKAHEAD** |
| Seg 2016-05-30 **20:00** | **2016-05-30** | 2016-05-27 | **YES LOOKAHEAD** |
| Sex 2016-05-27 **00:00** | 2016-05-26 | 2016-05-26 | no (ok) |
| Sex 2016-05-27 **12:00** | **2016-05-27** | 2016-05-26 | **YES LOOKAHEAD** |
| Dom 2016-05-29 **20:00** (weekend) | 2016-05-27 | 2016-05-27 | no (ok) |
| Qui 2016-05-26 **08:00** (normal) | **2016-05-26** | 2016-05-25 | **YES LOOKAHEAD** |

**Conclusões provadas:**
- **PROD vaza** em todas as barras 4H intraday (04:00/08:00/12:00/16:00/20:00) — pega o daily same-day forming. Só 00:00 e barras de fim de semana (sem daily same-day) são limpas.
- **CAUSAL nunca vaza** — sempre o último dia de pregão anterior. No gap de fim de semana pega corretamente Sex 05-27 para todas as barras de Segunda.
- **Daily forming atual:** o arquivo exclui `ts ≥ today` (`refresh:78`), então em **live** a PROD não acha o daily de hoje (causal por construção live). Em **backtest** essa proteção não existe → **obrigatório** usar a CAUSAL.

**SHIFT1-audit (Tarefa 6) — itens provados:**
- [x] D1a deve usar o **daily fechado anterior** ao eval_bar → regra CAUSAL `date(daily)<date(eval)`.
- [x] **NÃO** usar daily do mesmo dia em formação → PROD falha nisso intraday; CAUSAL garante.
- [x] **NÃO** usar close diário conhecido só no fim do dia → o close de `D` é conhecido em `D+1 00:00`; CAUSAL só usa `≤ D-1`.
- [x] Convenção open/close: `ts`=open; candle fecha em `D+1`; CAUSAL robusta à hora de close.
- [x] **Não** repete o bug A1'/L5 (que consultava classificação daily do mesmo dia) — desde que a CAUSAL seja adotada e um audit ORIG-vs-SHIFT empírico seja rodado na implementação.

---

## 7. Regra canônica `latest_closed_daily` (especificação)

```
latest_closed_daily(eval_bar_time_utc, daily_rows_sorted_by_date):
    d_eval = date(eval_bar_time_utc)                  # data UTC do bar 4H
    return last row r with date(r.ts) < d_eval        # estritamente anterior
    # se nenhum: None (warmup / início da série) -> trade SEM D1a (ou bloqueado, decisão da Rodada 3)
```

- **Comparação:** `date(daily) < date(eval)` (date-shift D-1). **Não** `midnight(ts) < bar_time` (PROD, vaza).
- **EMA do daily selecionado:** `close_1D`, `EMA50_1D`, `EMA200_1D` (α=2/(p+1), warmup≥200 do RAW 1D 2012).
- **Predicado D1a:** `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` no daily retornado.
- **SHIFT1-audit obrigatório na implementação:** rodar ORIG (CAUSAL) vs SHIFT (mais um dia atrás) e confirmar que a CAUSAL não tem delta de lookahead (esperado: CAUSAL = limpo; PROD-style mostraria inflação). Sem isso, não liberar V6/V7.

---

## 8. Comparação com fonte antiga (Tarefa 7)

- **D1a prose (`summary.md`):** "último 1D fechado, no-lookahead" — **intenção correta**, mas nunca foi mecanizada nem auditada empiricamente (era prose). Esta auditoria fornece a regra exata que faltava.
- **htf_1d legacy (sweep):** `close_1D > EMA50_1D` via `merge_asof(direction='backward')` sobre `time` (open). `merge_asof backward` em `time`=open tem a **mesma fragilidade** da PROD (pode casar o daily same-day se o 4H for depois do open diário). E `htf_1d ≠ D1a` (EMA50-only vs close+EMA50+EMA200). → legacy **não é autoridade**; divergência explicada, não forçada.
- **regime_l1_v4 (produção):** causal em **live** (arquivo exclui today), mas a função `latest_state_before` por si **não** é causal em backtest. A L1 não é refutada por isso (live ok); mas o **D1a backtest não pode reusar `latest_state_before`** — deve usar a CAUSAL.

> ⚠️ **Observação (não-ação neste bloco):** a fragilidade `t<bar_time` da `latest_state_before` em contexto de *backtest* vale registrar para qualquer rederivação histórica do regime L1 (não tocar L1 aqui; só anotar). Em **produção live** a L1 permanece causal pelo guard `ts<today`.

---

## 9. Hard stops (Tarefa 9) — status

| Hard stop | Estado |
|---|---|
| timestamp 1D ambíguo | ✅ **resolvido** — `ts`=open, UTC, candle fecha D+1 (provado) |
| daily atual/forming pode entrar | ✅ **resolvido** — CAUSAL `date<date(eval)` exclui same-day; live exclui today |
| cobertura 1D insuficiente | ✅ **resolvido** — RAW 1D 2012-2026 cobre + warmup |
| EMA50/EMA200 não reproduzíveis | ⚠️ **PENDENTE** — pipeline tem SMA, não EMA; precisa build EMA (α=2/(p+1)) |
| warmup não definido | ✅ **definido** — ≥200 daily, usar RAW 1D 2012 |
| 4H→1D alignment diverge sem explicação | ✅ **resolvido** — PROD vs CAUSAL explicado e provado (§5-6) |
| qualquer teste de borda falha | ✅ todos os 7 testes demonstrados; CAUSAL 0 leaks |
| **SHIFT1-audit empírico ORIG-vs-SHIFT** | ⚠️ **PENDENTE** — exige a implementação (backtest), fora do escopo deste bloco |

---

## 10. Decisão final

| Pergunta | Resposta |
|---|---|
| **D1 pipeline encontrado?** | **SIM** — `build_daily_features.py` + `regime_l1_v4.py` + `xau_daily_l1v4.jsonl` + RAW 1D. |
| **Convenção timestamp resolvida?** | **SIM** — `ts`=open UTC; candle fecha D+1. |
| **`latest_closed_daily` provada?** | **SIM** — regra CAUSAL `date(daily)<date(eval)` definida e demonstrada (0 leaks). |
| **D1a liberado?** | **NÃO** — falta (a) build EMA50_1D/EMA200_1D (pipeline só tem SMA), (b) implementar a CAUSAL, (c) SHIFT1-audit empírico. |
| **V6/V7 liberados?** | **NÃO** — bloqueados até os 3 itens acima. |
| **V0-V5 liberados?** | **SIM** — não dependem de 1D. |
| **Blockers restantes** | (1) EMA1D build; (2) implementar `latest_closed_daily` CAUSAL; (3) SHIFT1-audit ORIG-vs-SHIFT na implementação. |
| **Hard-stop de alinhamento** | **rebaixado** de "indefinido" → "definido e provado, implementação pendente". |
| **Menor próximo passo** | Quando autorizado: construir `EMA50_1D/EMA200_1D` do RAW 1D 2012 + implementar a CAUSAL + rodar SHIFT1-audit; **só então** habilitar V6/V7. |

---

## 11. Devil's Advocate (Tarefa DA)

| Pergunta DA | Resposta |
|---|---|
| D1 usa só candle fechado? | ✅ Regra CAUSAL `date(daily)<date(eval)` garante; PROD não (provado vazar intraday). |
| Timestamp open/close resolvido? | ✅ `ts`=open UTC; candle fecha D+1 (`refresh:69` + dados). |
| `latest_closed_daily` provado? | ✅ Especificado + 7 testes de borda (0 leaks na CAUSAL). |
| 00:00 / 04:00 / 20:00 testados? | ✅ Todos — 04:00/20:00 vazam na PROD, limpos na CAUSAL. |
| Weekend/gap considerado? | ✅ Sex 05-27→Seg 05-30 (Sáb/Dom ausentes); CAUSAL pega Sex p/ toda a Segunda. |
| EMA50/EMA200 causal? | ⚠️ **A construir** — pipeline tem SMA; D1a exige EMA (warmup RAW 1D 2012). Marcado pendente, não mascarado. |
| Nenhum D1 forming usado? | ✅ CAUSAL exclui same-day; live exclui today. |
| Nenhum backtest rodado? | ✅ Só demonstração lógica do seletor sobre datas reais; nenhuma simulação de trade. |
| V6/V7 não executados? | ✅ Não executados; permanecem bloqueados. |
| Nada operacional tocado? | ✅ Produção verificada íntegra (read-only); L1 não tocada (só anotada). |
| Caminho B não recomendado? | ✅ Não. |

**DA verdict: PASS.**

---

*Read-only exceto docs/mapping. Demonstração do seletor computada sobre `xau_daily_l1v4.jsonl` real (leitura, sem alteração). RAW 1D `.gz` não modificado (1 registro lido para schema). Nenhum backtest/trade/plotagem/MCP/chart/Telegram/broker. L1 não alterada. Pipeline 1D rastreado a `build_daily_features.py` / `regime_l1_v4.py` / `refresh_regime_l1_v4.py`.*
