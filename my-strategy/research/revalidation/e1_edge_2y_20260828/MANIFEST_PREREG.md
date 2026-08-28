# EDGE POR RULE DO E1 — RAW 2 ANOS (prereg selado 28/08; ordem Cris, pós-DA que reprovou o 1-mês)
Objetivo: edge REAL por rule/direção do E1 sobre 2 anos, com os 3 fixes do DA. Base para decidir (Cris)
que rules manter/cortar — NÃO decido eu.

## Método (fiel, harness canónico — NÃO rebuild paralelo)
- Replay barra-a-barra do `e1_detector.detect(d, p)` REAL. O dossiê `d` é RECONSTRUÍDO por barra a partir
  do RAW canónico via `context_structure.structure()` (swings/choch/leg/trend por TF 15/60/240/1D,
  resample do RAW 15M) + zonas do pine RAW as-of (OB v11/SMC) + RSI as-of. Consome os módulos aprovados.
- FIX1 dedup: unidade = bar_time do sinal (não ts de emissão).
- FIX2 causal: resolve SL-first 3R a partir da BARRA do sinal (bar_time), não da emissão.
- FIX3 TF: separar métrica por (rule, dir, tf) — não fundir TFs.
- Normalizar também por sl_atr (reportar risk_atr mediano por rule — o −229 era SL 0.16 ATR).
- Coorte: reportar BRUTO (todos os detect) E a fração que o reader teria de julgar (survivor do gate).

## Saída (selada)
Por (rule, dir, tf): N (bar_times distintos), WR, sumR, avgR, risk_atr mediano, por-semestre, jackknife.
Painel completo. Gate de leitura = referência; veredito de corte = Cris. DA obrigatório.
Limitação declarada: zonas/RSI históricos dependem de o RAW ter o pine capturado nessa barra; onde não
tiver, o rule que depende de zona fica com cobertura menor (declarar %, não inventar).
