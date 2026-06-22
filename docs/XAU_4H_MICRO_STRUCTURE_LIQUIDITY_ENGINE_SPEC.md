# MICRO-STRUCTURE LIQUIDITY ENGINE — SPEC (diagnóstico)

**2026-06-22.** Diagnóstico/calibração nos 62 (ensino). NÃO produção, NÃO 276/OOS, NÃO promover, NÃO chart/MCP.

## Tese
A distinção T17/T20 (micro-top bad entry em range-bull) vs T21/T22/S12 (micro-bottom/reclaim/breakout bom)
talvez NÃO seja macro-regime, nem entry-quality simples, nem legpos, nem dist_supply isolado. Pode ser
**microestrutura de liquidez**: entrada após reclaim de micro-fundo / spring / acceptance (boa) vs entrada após
varredura de micro-topo / failed continuation / trap sob supply (ruim).

## Pergunta central
Existe sinal CAUSAL, conhecível na entrada, que distinga micro-top bad entry de micro-bottom/breakout good entry?

## Estados de microestrutura (rótulos)
MICRO_BOTTOM_RECLAIM · MICRO_TOP_TRAP · BREAKOUT_ACCEPTANCE · FAILED_BREAKOUT · RANGE_CHOP ·
LIQUIDITY_SWEEP_REVERSAL · UNKNOWN_INSUFFICIENT_EDGE.

## Método
1. JOIN SEGURO: 62 plot_id → datetime preciso → stream causal de 84 features (proveniência verificada,
   commit 1937d82). visual_matrix usado SÓ para o mapa; NUNCA outcome/realR/exit_type como predicado.
2. Features causais de microestrutura: dist_4h_demand/supply_atr, net_micro_location, has_overhead,
   demand_touched, reclaim_body_atr + reclaim_dist_from_demand/supply, va_state/POC/VAL (SVP), legpos30/90,
   drop20/rise20, smc, bubbles order-flow, sup_cat/pol_cat/demand_cat (camadas anteriores como evidência condicional).
3. 3 agentes independentes, CEGOS a outcome/set/cris, IDs OPACOS (X01..X18), leitura de conjunto.
4. Decodificar consenso e comparar com o papel verdadeiro (Cris) — sem usar o papel como input dos agentes.

## Risco metodológico (declarado a priori)
- O sinal pode ser **parcialmente irredutível** (breakout-bom e micro-topo-ruim idênticos à entrada — disfarce
  de liquidez para capturar liquidez, Auction Theory).
- **Limitação de dados**: não há série OHLC CONTÍGUA 2020-2026 local → micro_range_position bruto, sweep
  intrabar (high/low prior), bars_since_swing = `FEATURE_UNAVAILABLE_NO_CONTIGUOUS_SERIES`. range-position
  bruto já falhou antes. Usamos os proxies causais que a extração já computou da série.
- Se não houver sinal causal: registrar **FEATURE_MISSING / MICROSTRUCTURE_NOT_CAPTURED** — NÃO forçar regra,
  NÃO transformar micro-top/microestrutura aberta em filtro promovido.
