# Design Test Plan (mecânico) — XAU_4H_BREAKOUT_D1A / v1

**Data:** 2026-06-16 · **Tipo:** plano de testes mecânicos read-only · **NOT_VALIDATION.**
**Este bloco NÃO executa nenhuma rodada** — só as desenha. Execução exige autorização explícita do Cris, RAW mapping resolvido (`raw_field_mapping.md §5`) e os hard stops do `gate_manifest.md §7` limpos.

**Princípios (project_authority/03 + memory):**
- Reproduzir, **não otimizar**. Nenhum threshold novo.
- Diferenças vs legacy/v1 devem ser **explicadas, não corrigidas à força** (`feedback_dont_conclude_from_broken_period`).
- `no_topN` / jackknife obrigatórios (edge é monumental-dependent: ~9 targets em n=115).
- SLIM só reconciliação; RAW é source-of-truth.
- DA full-time (`feedback_devils_advocate_fulltime`) antes de qualquer conclusão de cada rodada.

---

## Rodada Mecânica 1 — Rebuild baseline (reproduzir T1-T4 em RAW)

**Objetivo:** reconstruir o trigger puro (V0) de OHLCV RAW 4H e contar candidates.

- Confirmar conteúdo RAW 4H (arquivos, cobertura temporal, schema) — primeira ação real.
- Recomputar T1-T4 de RAW (resolver RSI_MA antes — hard stop).
- **Contar total de candidates** (sinais brutos, pré-regime, pré-overlap).
- Comparar com legacy/revalidação v1 **se possível** (v0 do sweep `A_baseline_no_regime` n=834/846; revalidação v1 com regime = 115). **Não** esperar match exato (slim vs RAW, close vs next-bar-open, períodos diferentes).
- **Diferenças esperadas devem ser explicadas, não corrigidas à força.** Documentar cada fonte de divergência (período, fonte, fill, RSI_MA, swing edge-case).

**Saída:** contagem de candidates V0 + log de reconciliação RAW-vs-slim-vs-legacy.

---

## Rodada Mecânica 2 — Regime matrix (R1-R5 incremental)

**Objetivo:** decompor a contribuição de cada gate de regime, reproduzindo o sweep **conceitual sem otimizar**.

- Aplicar V1-V5 (gates R1-R5 incrementais, ver `gate_manifest §6`).
- Reproduzir a decomposição conceitual (esperado direcional: trigger fraco → regime carrega; slope isolado = pior; EMA-stack+ADX = núcleo). **Confirmar ou refutar** com RAW, não assumir.
- **Métricas por variante** (project_authority/03 Passo 6):
  - `n`
  - `targets` / `stops` / `BE stops` / `time limits` (breakdown de exit_reason)
  - `sum R`, `avg R`
  - `PF`
  - `WR`
  - `max drawdown`
  - `losing streak`
  - `trades/year`
  - `year breakdown` + `regime breakdown`
  - `no_top1 / no_top3 / no_top5 / no_top10` (robustez)
  - `hit 1R/2R/3R/4R` (target capa em 4R)
- **Sem escolher vencedor por total_R.** R_full_trend_regime (V5) troca N por PF — registrar o trade-off, não promover.

**Saída:** tabela de decomposição V0→V5 com as métricas acima.

---

## Rodada Mecânica 3 — D1a (último daily fechado)

**Objetivo:** medir D1a isolado (V6) e combinado (V7), com causalidade provada.

- Recomputar EMA50_1D / EMA200_1D de close 1D RAW.
- Aplicar D1a com **último 1D fechado** (`merge_asof backward` por close-time do 1D).
- **SHIFT1-audit obrigatório**: rodar ORIG vs SHIFT1 do alinhamento 1D; esperado **sem delta** (já causal) — se houver delta, há look-ahead (precedente A1' SUPERTREND). Não concluir "limpo" sem este teste.
- Separar **kept vs rejected**; produzir **trade IDs estáveis** (cronológicos, ver plot spec).
- **Reconstruir os rejects por RAW** — **não** confiar na prosa antiga dos "25 rejects" do `summary.md` (prose-only, não reconstruível do trades.jsonl v1).
- Medir a **tensão htf_1d vs D1a** (sweep dizia htf_1d redundante; v1 dizia D1a aditivo) — agora com a definição correta (D1a stricter ≠ htf_1d).

**Saída:** V6/V7 com métricas Rodada 2 + lista completa kept/rejected (IDs estáveis) + resultado SHIFT1-audit.

---

## Rodada Mecânica 4 — Fragilidade de gestão (medir, NÃO mudar)

**Objetivo:** caracterizar a gestão sem alterar a estratégia.

- Medir distribuição de **MFE/MAE** (R) por variante e por regime.
- Medir **stop distance em ATR** (o SL é sempre 0.5ATR + low buffer ⇒ risk em ATR varia com o low).
- Identificar **blow-off / extensão extrema** (ex.: distância close_1D−EMA200_1D em ATR_1D; distância entry−swing_high em ATR_4H) — só **medir**, candidato a sub-filtro futuro (HYPOTHESIS_ONLY).
- Medir **distribuição do time_limit** (quantos % saem por tempo; v1: 29/115 ≈ 25%).
- **Gerar hipóteses** para SL/exit (bloco de gestão futuro) — sem testar, sem quantificar (quantificar agora = overfit in-sample garantido).

**Saída:** caracterização de gestão + lista de hipóteses marcadas `HYPOTHESIS_ONLY` / `DO_NOT_TEST_YET`.

---

## Rodada Mecânica 5 — Plot readiness (gerar dados, NÃO plotar)

**Objetivo:** emitir CSV/JSONL de trades pronto para a futura plotagem canônica.

- Para cada variante (ou ao menos V5 e V7), emitir `trades.jsonl` + CSV com os campos do `plot_ready_output_spec` (abaixo).
- IDs cronológicos estáveis preservados entre janelas/replots.
- **NÃO plotar.** Nenhum MCP/chart. Apenas gerar os arquivos.

**Saída:** `trades_V5.jsonl`, `trades_V7.jsonl` (+ CSV) prontos para plot futuro autorizado.

---

## plot_ready_output_spec

Campos obrigatórios por trade (alinhados a `docs/CANONICAL_TRADE_PLOTTING.md` + schema do `trades.jsonl` v1):

| Campo | Tipo | Descrição |
|---|---|---|
| `chronological_id` | int | índice estável no conjunto (`#1` = mais antigo); preservado entre replots |
| `variant_id` | str | V0…V9 (qual variante gerou o trade) |
| `entry_ts` | unix int | tempo de entrada (open da barra seguinte ao sinal) |
| `entry_price` | float | `open[signal_bar+1]` |
| `stop_price` | float | `low[signal_bar] − 0.5·ATR14` |
| `target_price` | float | `entry + 4·risk` |
| `exit_ts` | unix int | tempo de saída |
| `exit_price` | float | preço de saída |
| `close_R` | float | R realizado |
| `result_class` | str | winner (`close_R>0`) / loser (`close_R≤0`) |
| `exit_reason` | str | target / stop / stop_be / time_limit |
| `d1a_pass` | bool | passou no filtro D1a? |
| `regime_flags` | obj | {adx, close>ema200, ema50>ema200, slope, atr_exp, year_regime} |
| `notes` | str | livre (ex.: right_censored, be_moved, blow-off flag) |

**Regras de plotagem (do canonical — para o bloco futuro, NÃO agora):**
- **Labels:** texto `#<chronological_id>`; cor **verde `#1a8917`** se `close_R > 0`, **vermelho `#cc0000`** se `close_R ≤ 0`; bold, fontsize 12; posição `entry + 0.5·R_dollars`.
- **`long_position`:** `stopLevel`/`profitLevel` em **TICKS** (`mintick XAU = 0.01`): `round((entry−stop)/0.01)` e `round((target−entry)/0.01)` — **nunca preço absoluto** (bug canônico). `point2` no **target**.
- **NÃO** usar `vertical_line`. **NÃO** usar screenshot como validação (Cris vê o TV direto). Verificar por `success` + `draw_list`.
- Helper canônico: `alert-bridge/draw_xau_4h_trades.py`.

---

## Sanity checks obrigatórios (antes de QUALQUER backtest)

### Dados
- [ ] timestamps ordenados (4H e 1D)
- [ ] sem duplicatas
- [ ] sem buracos relevantes (gaps de barra documentados)
- [ ] timezone claro (UTC)
- [ ] 4H bars **fechados** (nenhum bar em formação)
- [ ] 1D **latest closed** corretamente alinhado ao bar 4H (não o D do dia em formação)

### Predicados
- [ ] breakout usa `swing10[i-1]` — nunca a swing atual/futura
- [ ] RSI usa candle **fechado**
- [ ] ADX / ATR / EMA não usam futuro (todas barras fechadas)
- [ ] D1a usa D1 **fechado** (SHIFT1-audit: ORIG vs SHIFT1 sem delta)
- [ ] entry no **next bar open** (regra definida explicitamente) — no same-bar impossible fill
- [ ] sanity stop: `0 < risk ≤ 5·ATR14` (senão skip)

### Outcome
- [ ] stop/target path logic definido (**stop-first** intrabar)
- [ ] se stop e target no mesmo bar ⇒ regra **conservadora** = stop
- [ ] BE@1R causal (aplica em `j+1`, sem lookahead no bar do cruzamento)
- [ ] time stop 24 bars causal (`right_censored` marcado)
- [ ] custos/slippage **definidos ou explicitamente zero/gross** (legacy sweep usou net @0.05R; revalidação v1 = gross — declarar e não comparar diretamente)
- [ ] MFE/MAE calculados sem lookahead para a entrada (janela `[entry_bar..exit_bar]`)

### Comparison
- [ ] legacy / recheck = **só referência**
- [ ] SLIM = **só reconciliação**
- [ ] RAW = **source-of-truth**
- [ ] diferenças RAW vs slim/legacy **não escondidas** — documentadas

---

## Sequência e gates entre rodadas

1. Rodada 1 só roda com hard stops do manifest limpos. Se candidates V0 divergirem inexplicavelmente do esperado → parar e investigar (não forçar match).
2. Rodada 2 só após V0 reconciliado.
3. Rodada 3 só após SHIFT1-audit do D1a passar.
4. Rodadas 4-5 são caracterização/emissão (não decidem promoção).
5. **Nenhuma rodada promove a estratégia.** Promoção exige (depois, separado): visual review 100%, walk-forward/OOS pós-2026-06, custos, correção de viés de seleção (sweep 22 configs), autorização explícita do Cris.

---

*Read-only. Nenhuma rodada executada. Nenhum threshold novo. Nenhuma plotagem. Nenhum MCP/chart/RAW tocado.*
