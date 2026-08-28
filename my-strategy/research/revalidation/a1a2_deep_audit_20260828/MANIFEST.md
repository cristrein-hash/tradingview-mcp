# A1/A2 DEEP AUDIT — melhora + buy-limit (ordem Cris 28/08)
NATUREZA: EXPLORATÓRIA (geração de hipóteses sobre o censo 863). Nenhum split daqui vira regra sem
prereg+forward próprio. Painel completo por corte; block-null só nos cortes candidatos; DA obrigatório.
BASE: censo detetor REAL (harness validado); features CAUSAIS na barra do gatilho:
  estruturais: layer, depth_atr, bounce%, lag, risk_atr, ema_dist, hora Lisboa, weekday, Layer1 1D, distrib V1H
  indicadores LIDOS do RAW as-of (nunca re-derivados): RSI, OB-v11 zona abaixo <=1ATR / dentro, volume da barra
BUY-LIMIT: variante limite = topo do retest_zone que a mensagem publica; janela fill 16b; fill-bar SL conta;
  tgt 3R do preço-limite; contabiliza NO-FILL e winners perdidos. Comparação market vs limit no MESMO episódio.
