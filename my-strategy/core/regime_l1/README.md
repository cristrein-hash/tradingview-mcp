# regime_L1_v4 — fonte de regime D-1 da L1 (Production v2)

Fonte de regime **explícita, limpa e rastreável** da estratégia XAU 4H LONG — CONTINUATION (L1 EMA21).
**Substitui** o regime legacy v1 B / `regime_B_v3`, declarado **IRRECUPERÁVEL** (ver `../regime/README.md`).
Não reproduz o classificador morto; não usa `combined_score`/breaks legacy.

## Predicates (validadas historicamente)
Sobre as features diárias canônicas (`../regime/build_daily_features.py`):
```
BULL        : close > ma_200 AND (ma_50 >= ma_200 OR slope_20_pct > 0)
                          AND (rsi_14 >= rsi_ma_14 OR rsi_14 >= 50)
BEAR        : close < ma_200 AND slope_20_pct < 0
TRANSITION  : caso contrário
```
3 estados {BULL, TRANSITION, BEAR}. A L1 usa **regime D-1 == BULL** como gate-base de contexto (não é ordem de entrada).

## Arquivos
- `xau_daily_l1v4.jsonl` — OHLCV diário (histórico + barras frescas), append-only.
- `xau_daily_l1v4.manifest.json` — fonte/símbolo/TF/range/sha.
- `regime_l1_v4.py` — classificador + `latest_state_before()` (usado pelo runtime).
- `regime_l1_v4_classifications.jsonl` — saída (ts + features + `regime_l1_v4`).

## Fonte de dados (2026-06-16)
- Histórico OHLCV: extraído de `regime_classifier_v3/xau_daily_with_features.jsonl` (até 2026-05-25).
- Barras novas (2026-05-26 → 2026-06-14): **MCP D live read-only** (chart já em PEPPERSTONE:XAUUSD 1D; sem trocar símbolo; barra corrente incompleta de hoje excluída). Chart restaurado para 240 após a leitura.
- **Nenhum 1D RAW re-coletado.** Sem broker, sem scheduler.

## Validação
- Preservação obrigatória: #36/#38/#11/#1 → regime D-1 = **BULL** (PASS).
- Diagnóstico vs `regime_B_v3` (legacy, não-autoridade): ~51.6% concordância — **não se exige match** (regime novo e explícito).
- Runtime `--once`: deixa de retornar `regime_feed_stale`; consome `regime_l1_v4`; se feed não cobrir D-1 recente → `regime_l1_v4_stale`.

## Atualizar (frescor) — `refresh_regime_l1_v4.py` (sob demanda)
Refresh incremental SOB DEMANDA via MCP D (read-only, restaura o chart). Default = dry-run.
```bash
python3 refresh_regime_l1_v4.py            # dry-run: current_last_date / target_d1 / missing_count
python3 refresh_regime_l1_v4.py --write    # escreve só se houver barra fechada faltante; senão already_fresh
```
- Nunca usa barra diária incompleta (`date < today` + volume ≥ 0.3× mediana; senão hard stop).
- Append-only + revalida monotonicidade/duplicata/OHLCV + reclassifica + grava manifest.
- Não muda símbolo; restaura TF original ao final. Não envia Telegram. **Sem scheduler/daemon.**
- `already_fresh` quando o dataset já cobre o último daily close confirmado.

**Bloco futuro (com autorização):** agendamento contínuo do refresh + runtime no fechamento de cada 4H.
