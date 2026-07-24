# CRUZAMENTO PROFUNDO — Ground-truth motor (Cris 2026-07-24)

Reconstruído 100% de fontes live/locais (bars_5m/15m, bubbles_15m, nas_15m, latest.json). Multi-fatorial +
trajetória + duplo-objetivo (WR **e** MFE). **DIAGNÓSTICO in-sample** (N=68, 1 semana, mesmo regime macro; verd dos
61 = proxy-MFE sem SL/TP fixo, 7 winners = reais) — **NÃO é validação de edge** (locks OOS/calibração). Scripts:
`research/deep_cross_20260724.py`, `research/master_trades_cross_20260724.py`.

## Amostra
61 sinais do motor ANTIGO (voto-MTF) + 7 winners do Cris (extraídos do MCP: entry/SL/TP/data-hora). Backdrop macro
**constante** na semana (real_yield 2.39 · DXY 120.5 · VIX ~17-19 · oil +13.8%/20d) → external factors NÃO
diferenciam winner/loser DENTRO da semana; a separação é **estrutural**.

## O que SEPARA (por ordem de força)
1. **★ ALINHAMENTO PERNA 1H = o eixo central.** COM-perna 56% WR / MFE 15.3 · CONTRA-perna 27% / MFE 8.6.
   Nos 61 sinais antigos sozinhos: COM 48% vs CONTRA 23%. Monótono e forte. **Confirma o motor novo.**
   - Os 7 winners: 5 COM-perna + 2 CONTRA (estes 2 = reversões no HTF, ambos WIN) → "CONTRA-perna só no HTF OB" sustenta-se.
2. **EMA-pos (px vs EMA21 15M):** abaixo 59% / acima 25%. Forte MAS **confounded** com o viés short da amostra
   (49/68 short; abaixo-EMA+short = continuação) → é a perna/continuação restated, não fator independente.
3. **Fluxo bubbles alinhado:** 52% vs 35% (MFE 15.8 vs 9.3). Confirmador secundário real.
4. **modo antigo:** reversão 43% > continuação 31% — a "continuação" do motor antigo (direção por voto-MTF) FADAVA a
   perna → "continuava" para o lado errado. Prova que a direção antiga estava ao contrário.

## O que NÃO separa (dropar do gate)
- **RSI side alinhado: 41% vs 41% = ZERO separação.** Não usar RSI como filtro de direção/qualidade.
- **DMI (+DI/-DI) alinhado: 43% vs 37%** = separador fraco.
- **NAS alinhado: INVERTIDO/ruído** (NAS-contra 52% > NAS-com 25%, N=8 minúsculo) — não confiar.
- **Convergência-COUNT (nº de 5 fatores) NÃO é escada limpa:** 4/5=55% mas 3/5=33% < 1/5=46%. Confirma
  [[feedback_contextual_convergence_not_determinism]]: score/kill-count não é separador. Só o TOPO (4/5) e a
  perna-alignment se destacam.

## Q antigo era quase inútil
FORTE 42% vs FRACO 33% (mal separava). MASTER (Cris) 100%. O rótulo FORTE/FRACO antigo não identificava winner.

## Sessão / direção (secundário, confounded)
NY 29% (pior — flushes overnight/NY) · London 50% · asia 43% · late 50%. LONG 52% vs SHORT 36% (motor antigo
**sobre-shortou**: 49 short / 19 long numa semana em recuperação/range).

## VEREDICTO — keep / avoid / improve / skip
- **MANTER:** direção = perna 1H (o #1 separador, já live) · fluxo-bubbles como confirmador secundário · reversão só no HTF OB.
- **EVITAR:** CONTRA-perna sem OB 4H/1D (27% WR = os losers; o motor novo já dá SKIP) · sobre-shortar · gate por RSI/DMI/NAS · gate por convergência-count.
- **MELHORAR:** substituir o eixo de qualidade FORTE/FRACO (inútil) por **perna-alignment + fluxo-alignment** (os 2 que separam) · rebalancear long/short via perna.
- **SKIPAR melhor:** contra-perna 15M sem HTF OB = pullback-marker SKIP (já implementado) — é exatamente a classe de 27% WR.

## Caveats (auditados)
N=68 in-sample, 1 semana, mesmo regime; verd dos 61 = proxy-MFE (mistura com 7 reais = direcional). Perna
reconstruída (resample 1H, não byte-idêntica ao E0). Resultado CONFIRMA a direção do motor novo e identifica
features inúteis a dropar — **não** promove edge. Árbitro real = forward dos próximos trades.
