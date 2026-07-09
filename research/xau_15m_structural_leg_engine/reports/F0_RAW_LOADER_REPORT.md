# F0 — RAW LOADER REPORT (2026-07-09) — STATUS: PASS (VERIFIED_RAW)

Script: `f0_raw_loader.py` · Result: `results/f0_raw_loader_result.json` · Manifest: `docs/architecture/XAU_15M_STRUCTURAL_LEG_ENGINE_GATE_MANIFEST.md` (RAW_LINEAGE_PASS strict).

## Fontes
- 9 blocos RAW `.jsonl.gz` do HD externo (sha256 de cada um em `raw_sha256` do result). ZERO
  primitives / raw_features / superseded / proxy. HD desmontado = assert BLOCKED.

## Números
- **49.804 barras 15M FECHADAS**, 2024-05-24 19:45 → 2026-07-03 16:15 UTC, monotónicas, dedup OK.
- **0 conflitos CLOSED-vs-CLOSED** entre blocos (tolerância 1e-6 O/H/L/C, fail-loud armado).
- 1 barra never-closed excluída (2026-07-03 16:30, fim do stream).
- Gaps: 108 weekend · 418 session-break diários · **20 "other" = todos feriados de calendário**
  (Natal/Ano Novo/Páscoa/Thanksgiving/MLK/etc. — lista no result). Zero buracos de dados reais.

## Descobertas materiais (corrigem premissas da spec)
1. **`tail[-1]` do ohlcv é a barra CORRENTE possivelmente EM FORMAÇÃO** (evolui entre snapshots).
   A v1 do loader assumia "tail = 5 barras fechadas" e o fail-loud disparou (o=h=l=c no 1º snapshot
   do bar). Semântica corrigida e CAUSAL: bar é CLOSED só quando visto em profundidade ≥1 do fim do
   tail; assert de igualdade só CLOSED-vs-CLOSED; provisional excluído da série. **Implicação para
   F1/F2: qualquer consumo por barra deve usar apenas barras CLOSED (o loader já entrega só essas).**
2. **Os 8 limites de bloco são CONTÍGUOS na camada de preço** (t_min do bloco k+1 = t_max do bloco
   k + 900s, verificado nos 8). O "warmup-hole ~24h" documentado no lab anterior pertence aos streams
   de LABELS/indicadores, não ao preço. Para F0→F1.5 (price-only) não há descontinuidade a costurar;
   o carry de estado entre blocos é trivialmente contínuo. O tratamento de warmup de labels fica para
   a Fase 2/3 (quando labels entrarem como anotação).

## Cache derivado declarado
`results/f0_bars_cache.jsonl` — sha256 no result e a declarar no manifest; source_ref = derivação 1:1
dos 9 RAW (tails ohlcv, dedup, assert). Uso interno F1/F1.5; NUNCA substitui o RAW como autoridade.

## Confirmação negativa
Sem eventos · sem entry · sem indicadores · sem backtest · sem produção/Telegram/broker · sem chart.
