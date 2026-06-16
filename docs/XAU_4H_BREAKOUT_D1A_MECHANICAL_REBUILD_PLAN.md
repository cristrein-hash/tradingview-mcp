# XAU 4H BREAKOUT / D1a — Mechanical Rebuild Plan

**Data:** 2026-06-16 · **Tipo:** plano de reconstrução mecânica read-only · **NOT_VALIDATION.**
**Escopo exclusivo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT. (Sem Caminho B, sem mudar conceito, sem encerrar prematuramente. L1 mantida separada.)
**Bloco:** preparar rebuild + design tests. **Nenhum backtest, nenhuma plotagem, nenhum threshold novo, nada operacional tocado.**

---

## 1. Executive summary

Este bloco **prepara** (não executa) a reconstrução mecânica do conceito **DECISIVE_BREAKOUT + D1a** para uma futura rodada de testes. Retoma após a queda 529 da sessão anterior — **verificado: nenhum arquivo parcial foi criado antes da queda** (slate limpo; o diretório alvo não existia).

O conceito é um **breakout decisivo pró-momentum** (rompe a máxima de 10 barras com corpo forte, em regime trending-bull com volatilidade expandindo) — **ortogonal à L1** (pullback anti-extensão). O **pacote legacy** está contaminado (rótulo `ACTIVE_CANDIDATE` enganoso, canal recheck:931 neutralizado, métricas só de SLIM), mas **não há prova de look-ahead** — os gates são estruturalmente causais. Logo: `RECONSTRUCTION_IN_PROGRESS`, não refutado.

O bloco produziu **4 artefatos** (3 no diretório de revalidação + este relatório) que isolam o núcleo limpo, mapeiam cada campo para RAW, e desenham as rodadas de teste — tudo desacoplado do canal recheck e do rótulo catalog.

**3 discrepâncias de fonte foram resolvidas canonicamente** (nome ≠ definição):
1. **Config-label mismatch:** `config_id: S_full_trend_htf` no v1, mas gates implementados = **`R_full_trend_regime`** (ADX+EMA-stack+slope+ATR). Rebuild adota R como R1-R5.
2. **D1a ≠ htf_1d:** legacy htf_1d = `close_1D>EMA50_1D`; D1a = `close_1D>EMA200_1D AND EMA50_1D>EMA200_1D` (stricter). A "redundância" do htf_1d no sweep **não** se aplica ao D1a.
3. **Entry:** spec legacy = close do sinal; rebuild adota **next-bar-open** (anti-lookahead).

---

## 2. Gate manifest criado

`my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/gate_manifest.md`

- Identidade: family `XAU_4H_BREAKOUT_D1A`, XAUUSD, 4H, LONG, archetype DECISIVE_BREAKOUT, ortogonal à L1 (futura L2 candidate), status RECONSTRUCTION_IN_PROGRESS / DESIGN_TEST_READY — not validated.
- Predicados T1-T4 (trigger), R1-R5 (regime = R_full_trend_regime), D1a (macro 1D causal), stop/target/exit legacy com fragilidades marcadas.
- Variantes V0-V9 para a matriz de decomposição.
- 5 hard stops do manifesto (RSI_MA indefinido, fórmula ADX, alinhamento 1D, swing10, config-label).

---

## 3. RAW mapping criado

`my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/raw_field_mapping.md`

- **RAW disponível** (verificado por `ls` read-only): `…/raw_replay/XAUUSD/4H/` e `…/1D/` presentes. Conteúdo interno **não inspecionado** (não tocar RAW) — confirmar na Rodada 1.
- Para cada campo (4H OHLCV + derivados; 1D para D1a; outcome): fonte RAW? derivado? fórmula? causalidade? SHIFT1? sanity check?
- SLIM = só reconciliação; RAW = source-of-truth.
- 6 hard stops do RAW mapping.

---

## 4. Predicados exatos

**Trigger (T1-T4), candle 4H fechado, todos obrigatórios:**
- T1 `close[i] > highest(high,10)[i-1]`
- T2 `close[i] > open[i]`
- T3 `body_pct[i] ≥ 0.5` (`body_pct = |close-open|/(high-low)`)
- T4 `RSI(14)[i] > RSI_MA[i]` ⚠️ (RSI_MA sem definição formalizada — hard stop)

**Regime (R1-R5 = R_full_trend_regime), candle de sinal, todos obrigatórios:**
- R1 `ADX(14)[i] ≥ 20` (Wilder DMI)
- R2 `close[i] > EMA(200)[i]`
- R3 `EMA(50)[i] > EMA(200)[i]`
- R4 `EMA(50)[i] > EMA(50)[i-5]` (slope)
- R5 `ATR(14)[i] > SMA(ATR14,20)[i]`

**D1a (macro 1D, on top):**
- `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` no **último 1D fechado** antes do bar 4H. Macro-context filter, não trigger. NEEDS_SHIFT1_AUDIT.

**Stop/Target/Exit (baseline legacy):** SL `low − 0.5·ATR14` (sanity `0<risk≤5·ATR`); target `+4R`; BE@+1R (em `j+1`); time-stop 24 barras; intrabar **stop-first**; fill **next-bar-open**; no-overlap.

---

## 5. Variantes mecânicas planejadas

| V | Composição |
|---|---|
| V0 | trigger only |
| V1 | trigger + ADX |
| V2 | trigger + EMA stack |
| V3 | trigger + ATR expanding |
| V4 | trigger + slope |
| V5 | trigger + regime_full (R1-R5) |
| V6 | trigger + D1a |
| V7 | trigger + regime_full + D1a |
| V8 | legacy adopted config (espelho da revalidação v1) |
| V9 | minimal candidate (só se o sweep justificar — sem threshold novo) |

Desenhadas em 5 rodadas (`design_test_plan.md`): (1) rebuild baseline, (2) regime matrix, (3) D1a + SHIFT1-audit, (4) fragilidade de gestão (medir, não mudar), (5) plot readiness (gerar, não plotar). Métricas completas por variante: n, exit breakdown, sumR, avgR, PF, WR, maxDD, streak, trades/year, year/regime breakdown, no_topN, hit-R.

---

## 6. Output plot-ready

Especificado em `design_test_plan.md → plot_ready_output_spec`. Campos: `chronological_id, variant_id, entry_ts, entry_price, stop_price, target_price, exit_ts, exit_price, close_R, result_class, exit_reason, d1a_pass, regime_flags, notes`.

Regras (para bloco futuro, **não agora**): labels `#<id>` verde `#1a8917`/vermelho `#cc0000`; `long_position` com `stopLevel`/`profitLevel` em **TICKS** (mintick 0.01); sem `vertical_line`; sem screenshot como validação; helper `alert-bridge/draw_xau_4h_trades.py`. Conforme `docs/CANONICAL_TRADE_PLOTTING.md`.

---

## 7. Sanity checks

Listados em `design_test_plan.md` (Data / Predicados / Outcome / Comparison) — devem passar **antes de qualquer backtest**. Destaques: 4H bars fechados; 1D latest-closed alinhado; swing10 usa `[i-1]`; D1a SHIFT1-audit ORIG-vs-SHIFT1 sem delta; entry next-bar-open; stop-first; BE@1R causal; custos declarados; RAW vs slim não escondido.

---

## 8. Hard stops (consolidados)

Parar (não rodar rebuild) se:
- RAW 4H ou 1D ausente / cobertura insuficiente.
- Daily alignment do D1a não provável (SHIFT1-audit falha/ambíguo).
- swing10 ambíguo.
- **RSI_MA sem definição** (período/tipo).
- Fórmula ADX/ATR não fechada.
- Outcome engine não garante causalidade (same-bar fill, BE/stop/target ambíguos).
- Mismatch scanner/runtime/backtest/manifest (invalida números até rederivação).

---

## 9. Próximos passos dentro de BREAKOUT/D1a

1. (autorizado) **Rodada 1** — confirmar conteúdo RAW 4H/1D + resolver RSI_MA/ADX; reconstruir V0; reconciliar contagem.
2. **Rodada 2** — regime matrix V0-V5 (decomposição, sem otimizar).
3. **Rodada 3** — D1a V6/V7 + SHIFT1-audit + reconstrução RAW dos rejects (não a prosa antiga).
4. **Rodada 4** — caracterização de gestão (MFE/MAE, stop em ATR, blow-off, time_limit) → hipóteses HYPOTHESIS_ONLY.
5. **Rodada 5** — emitir trades.jsonl/CSV plot-ready.
6. (separado, futuro) visual review 100%, walk-forward/OOS pós-2026-06, custos, correção de viés de seleção, autorização explícita → só então decisão de promoção.

L1 permanece operacional e **separada**. Prioridade de projeto (Caminho B = P0) inalterada — BREAKOUT/D1a é P2/futura L2; este bloco só **prepara**, não fura fila.

---

## 10. Estado de produção (verificado read-only neste bloco)

| Componente | Estado |
|---|---|
| Receiver | **OK** (PID 841, port 8787, `claude_recheck:true`, `secret_configured:true`) |
| Pause flag | **PRESENTE** (`runtime.pause_flag_present: true`) |
| cloudflared | **VIVO** (PID 1033) |
| Public ingress | **200** (`webhook.tdwclaudestrategy.org/health` → `ok:true`) |
| `xau-l1-cycle` | **carregado** (launchd) |
| Broker / enrich / OUTCOME evaluator | **dormant (0 processos)** |

Nada tocado. Nenhum Telegram. Nenhum MCP/chart. Nenhum RAW modificado.

---

## 11. Devil's Advocate (embutido)

| Pergunta DA | Resposta |
|---|---|
| Nenhum backtest rodado? | ✅ Correto — só leitura + escrita de docs/manifest. |
| Nenhum threshold novo inventado? | ✅ Todos os valores (10, 0.5, 20, 200/50, 5, 4R, 24, 0.5ATR) vêm das fontes legacy. V9 marcado "sem inventar threshold". |
| D1a definido com D1 fechado? | ✅ "último 1D fechado"; NEEDS_SHIFT1_AUDIT explícito (precedente A1' SUPERTREND). |
| RAW mapping completo? | ✅ 4H + 1D + outcome; cada campo com fonte/derivação/causalidade/SHIFT1/sanity; RAW disponibilidade verificada. |
| SLIM tratado só como referência? | ✅ "SLIM = só reconciliação" em todos os arquivos. |
| Plotagem não executada? | ✅ Spec gerada; nenhum `draw_shape`/MCP. |
| Canonical plotting spec referenciada? | ✅ ticks/cores/labels/helper conforme `CANONICAL_TRADE_PLOTTING.md`. |
| L1 mantida separada? | ✅ ortogonal, módulo próprio, não fundir. |
| Nenhum Caminho B recomendado? | ✅ Não recomendado em nenhum ponto. |
| Nada operacional tocado? | ✅ Produção verificada íntegra; read-only. |
| Config-label mismatch tratado (nome≠definição)? | ✅ Resolvido canonicamente (R_full_trend_regime), não propagado. |

**DA verdict: PASS.**

---

## 12. Recuperação pós-queda (529)

- `git status --short` antes: só `alert-bridge/logs/` untracked (produção, não relacionado).
- Diretório alvo `XAU_4H_BREAKOUT_D1A/` **não existia** → **nenhum arquivo parcial criado antes da queda**. Nada a completar/remover/recuperar. Slate limpo.

---

## 13. Arquivos criados neste bloco

1. `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/gate_manifest.md`
2. `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/raw_field_mapping.md`
3. `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/design_test_plan.md`
4. `docs/XAU_4H_BREAKOUT_D1A_MECHANICAL_REBUILD_PLAN.md` (este relatório)

---

*Read-only exceto docs/manifest. Nenhum backtest. Nenhuma plotagem. Nenhum threshold novo. Nenhum MCP/chart/Telegram/broker/RAW/catalog/strategy_rules/L1 tocado. Métricas legacy citadas são in-sample/SLIM/agregado — histórico, não validação.*
