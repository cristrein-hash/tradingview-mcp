# XAU 15M LONG · N96 · D (Bear-Active) Filter Round

**Cris 2026-07-08.** Research-only · RAW-first · LONG-only · NO production/Telegram/runtime/chart/plot/RAW-write/Supabase-write. Ciclo N96 continua aberto.

## 1. Executive verdict (DA fechada — `..._D_BEAR_ACTIVE_FILTER_DA_20260708.md`)
**O filtro intra-BEAR já é a melhor camada limpa. NÃO há gate adicional para a família D que sobreviva a multiplicidade honesta.** Veredito DA = `NO_ADDITIONAL_GATE_INTRABEAR_SUFFICES` (ganho, mas corrigiu 2 pontos meus):
- **Correção #1 (raciocínio):** existem SIM cortes profit-positivos **in-sample** (ex.: `rangewidth≤6,62`→+4R/0W; par `demand_room & 1D_ema_trend`→+6R/0W). O motivo de não valerem **não é o sinal — é MULTIPLICIDADE:** mining-null (baralha outcomes + repete a busca single+pair) dá ≥+6R em **39,7%** das vezes (P=0,40) → winner's-curse. Cheguei à resposta certa pelo motivo errado (o meu teste grosseiro mascarou os cortes positivos).
- **Correção #2 (confound stale, o caveat central):** htf_1D congela **2026-05-24**, htf_4H **2026-06-09**. **4 dos 8 deep-losers (#89,92,93,94) são Jun/2026** e a profundidade extrema (px_vs_ema −20 a −54) está **amplificada por uma EMA 1D de um mês atrás durante uma queda** — o cluster-faca é dominado por um episódio sobre referências HTF congeladas. Reforça "sem gate" mas eu devia tê-lo destacado.
- **Assinatura fraca real** (rangewidth P=0,028 · demand_room P=0,030 · rotational P=0,046 sobrevivem univariado; mas `bub_sell_ml` FALHA P=0,103, e sob ~15 features é Bonferroni-borderline) → no máximo **review-layer fraco** (flag, nunca gate). Nota: **#77 é MGMT, não D** (7/8 deep-losers são D).

## 2. Família D (14 losers) e cobertura pelo intra-BEAR
`results/n96_d_bear_active_filter_results.csv`. D = #27,49,50,66,67,68,69,80,86,87,89,92,93,94.
- **Já cortados pelo intra-BEAR (repique raso, 1D_px_vs_ema≥0):** #66,#67.
- **Permanecem (12):** #27,49,50,68,69,80,86,87,89,92,93,94.
- **Winners no regime BEAR a PRESERVAR (16):** #26,70,71,72,73,74,75,76,78,81,82,88,90,91,95,96.

## 3. Subfamílias (heurística estrutural, causal)
- **D2 repique raso** [#66,67] — já cortado pelo intra-BEAR.
- **D3 lower-high bounce** [#27,68] — repique meio-profundo em RANGE de transição.
- **Falling knives / capitulações falhadas** [#80,86,87,89,92,93,94] — DEEP (1D_px_vs_ema −6 a −54, 1D a cair −4 a −7,4), apanhou dips cada vez mais fundos que continuaram a cair. 1D_rsi ~45 (não extremo).
- **#49,50** = BULL-regime (Jan/26 pré-bear), px_vs_ema +16/+23 = distribuição-topo (não bear ativo causal).

## 4. Pool DEEP-BEAR — capitulação (winner) vs faca (loser)
N=24 · winners 16 · losers 8 [#77,80,86,87,89,92,93,94]. Discriminação intra-pool (top, AUC):
| feature | WIN (capitulação) | LOSER (faca) | AUC |
|---|---|---|---|
| `rangewidth_atr_15m` | 11,6 | 8,5 | 0,78 |
| `demand_room_4h` / `4H_dem_below` | 1,84 | 0,45 | 0,78 |
| `rotational_smc` | 1,0 | 0,0 | 0,75 |
| `bub_sell_ml` (climax de venda absorvido) | 4,0 | 0,0 | 0,70 |
| `1D_ema_trend` | −8,8 | −5,5 | 0,22 |

**Leitura de auction:** a capitulação VÁLIDA é **violenta** (range 15M largo, climax de venda `sell_ml` absorvido, longe da demanda anterior = novo excess-low, com rotação/CHoCH). A **faca** é **quieta** (range estreito, colada a demanda já mitigada, sem climax de absorção). Sinal real mas **fraco** (AUC 0,75-0,78, N=8 losers).

## 5. Candidatos de corte — o que morre é MULTIPLICIDADE, não sinal (corrigido pela DA)
- Cortes grosseiros (q0,4-0,6 nas top-4 features) = profit-negativos (dR −6…−14), cortam winners.
- MAS busca exaustiva single+pair ACHA cortes **in-sample +R/0W**: `rangewidth≤6,62`→{77,86,87,92}=+4R; par `demand_room≤0,568 & 1D_ema_trend≥−7,47`→{80,86,87,89,93,94}=+6R.
- **Mining-null (baralha DEEP outcomes + repete a busca): melhor ganho ≥+6R em 39,7% das vezes → P=0,40.** Os cortes limpos são winner's-curse. **Nenhum gate D sobrevive a multiplicidade honesta.**
- Corte largo = catastrófico: `rangewidth≤q0,6` destrói 7 winners de capitulação (−21R).

## 6. Gate vs Review vs Management
- **Gate adicional:** NÃO (todo corte profit-negativo; a faca é inseparável da capitulação sem sacrificar mais R em winners).
- **intra-BEAR já basta:** SIM, para o objetivo-lucro, é a melhor camada limpa.
- **Review-layer fraco (opcional):** "dip fundo QUIETO (range estreito + sem climax de venda absorvido + colado a demanda já tocada) = risco de faca" — precisão fraca, não gate.
- **Management:** não testável (só `out` binário, sem MAE/MFE).

## 7. Próxima rodada / caveats
Falhas de capitulação-falhada (#89,92,93,94) são near-idênticas ex-ante às capitulações vencedoras → **provável limite estrutural com features atuais** (a diferença real pode estar na micro-sequência do turn ou em inter-mercado, não no snapshot). N=8 losers no pool. Daily stale pós-2026-05-24. Não produção, não SHORT.

## 8. Artefactos
`n96_d_bear_active_filter_analysis.py` · `results/n96_d_bear_active_filter_{results.csv,summary.json}`. Regime causal, exhaustive + auction features. **PENDENTE DA.**
