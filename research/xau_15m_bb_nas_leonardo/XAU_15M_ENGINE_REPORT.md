# XAU 15M — RELATÓRIO GERAL DA ENGINE MULTI-AGENTE (caminhos criados/executados)

**Data:** 2026-06-26 · **Modo:** autônomo, loop auto-reiniciante, gates inquebráveis (RAW-causal, source-guard, DA full-time, validação real recalibrada). · **Decisão final = Cris.**

## Meta (alvo)
1-3 trades/sem (mín 1/sem) · WR≥50% · streak≤3 · DD compatível FundedNext (~5%).

## Fundação (validada)
Fonte canônica RAW 15M exclusiva (8 blocos, ~47k barras, 2 anos). Primitivas causais (OHLC/RSI/ATR/EMA, NAS first-appearance, SMC BOS/CHoCH/EQ, zonas Custom OB v11 = proxy BigBeluga por linhagem Pine). Macro 4H causal (swing∧EMA50). Leitura visual dos 24 prints → gestalt (4 fases macro; assinatura vencedora = sweep+reclaim+retest a-favor; ruído = chop/contra-fase). Tudo source-guarded, sem dados secundários.

## Caminhos executados (4 teorias, 5 Devil's Advocates)
| # | Teoria (gatilho) | Melhor recorte | WR | streak | DD | freq | Veredito DA |
|---|---|---|---|---|---|---|---|
| 1 | NAS-em-zona + macro + let-run | with_macro n131 | 44% | 7 | −7R | 1.27/sem | CONCENTRATION_ARTIFACT (bug risco corrigido; leave-out −28) |
| 2 | Liquidez sweep+reclaim + confluência | +NAS&zona n17 | 47% | 4 | −4R | 0.18/sem | SMALL_N_ARTIFACT (2 trades=83%; leave-out −9) |
| 3 | Continuação a-favor (pullback) | +zona n33 | 27% | 6 | −3R | 0.34/sem | IMPL_STRAWMAN de família REFUTADA (leave-out −31) |
| 4 | **Exit+sizing (parcial@2R) s/ R1 BULL-long** | partial2R n88 | 39% | 8 | **−4R** | 0.92/sem | **STILL_ARTIFACT mas funded a ≤0.5%; leave-out +4.6R** |

## Diagnóstico estrutural (o achado central — não derrota, conhecimento)
As 4 teorias (3 famílias de entrada ortogonais + a alavanca de saída) batem na **MESMA parede**: entrada-seleção no XAU 15M produz um **substrato right-tail** — mediana de trade = stop, WR 27-49%, expectância vive em ~5% dos trades, e **todo recorte com qualidade-de-meta é raro + dirigido por poucos trades/1 janela + não robusto (leave-one-out)**. É o **canon L2/BPT 4H reproduzindo no 15M** (entrada não tem alpha de magnitude; losers auction-irredutíveis; edge mora em exit/regime/risk-shaping). 3 gatilhos diferentes na mesma parede = diagnóstico, não coincidência. A alavanca de saída (parcial@2R) confirmou pelo outro lado: torna a base thin *funded-survivable a ≤0.5%* mas não levanta WR nem conserta streak.

## ⛔ Teto honesto
**WR≥50 + streak≤3 + 1-3/sem + FN-DD são mutuamente exclusivos por entrada-seleção neste substrato.** Não há recorte que satisfaça os 4 simultaneamente.

## Melhor-achievable (marginal, relaxa a meta)
**partial2R sobre R1 with_macro BULL-long:** ~0.9 trade/sem, WR 39%, parcial 50%@2R + trail no resto, SL estrutural (piso 0.5ATR), **funded-survivable a 0.5% sizing** (FN +8% sem bust, DD −4R), leave-one-out marginal +4.6R (robusto-ish, não robusto). Atinge o constraint DURO (funded) mas falha os SOFT (WR, streak, piso 1/sem). BEAR-short não funciona (negativo). Concentrado em Ago-Nov/2024.

## Opções honestas (Cris decide)
1. **Aceitar o marginal** partial2R BULL-long a 0.5% como SHADOW/small (não-OFICIAL), ciente de que relaxa a meta (WR39/streak8/~0.9sem) e é concentrado. Pendências: dedup same-bar do detector (n real 86), forward-test.
2. **Relaxar a meta** (ex.: WR≥40 + expectância+sobrevivência em vez de WR≥50) — aí o melhor-achievable passa a ser deployável.
3. **Mudar o problema** (outro ativo/timeframe, ou setup não-baseado-em-entrada-seleção) — o substrato 15M-XAU com estes indicadores tem teto estrutural.
4. **Encerrar** XAU 15M como inviável para a meta exata e documentar (este relatório).

Artefatos: `research/xau_15m_bb_nas_leonardo/` (primitivas, FEATURE_MAP, VISUAL_READING_PRINTS, build_*/detect_*/eval_engine/survival_sim/theory4 + _DA_* probes reprodutíveis). Aprendizados em memória `project_xau_15m_engine_learnings`.
