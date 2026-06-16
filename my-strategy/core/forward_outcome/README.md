# Forward Outcome Layer — `core/forward_outcome/`

Implementação **incremental** da Forward Outcome Layer (spec: [`docs/FORWARD_OUTCOME_LAYER_SPEC.md`](../../../docs/FORWARD_OUTCOME_LAYER_SPEC.md), roadmap: [`docs/FORWARD_OUTCOME_LAYER_ROADMAP.md`](../../../docs/FORWARD_OUTCOME_LAYER_ROADMAP.md)).

**Estado: MVP Fase 1 — Live Signal Quality (read-only).** Sem R, sem comparação backtest, sem Telegram, sem scheduler.

## O que faz
Responde: *o `indicator_signals.jsonl` está limpo, completo, rastreável e útil como fonte forward de comportamento live?* Mede densidade, completude de payload, duplicatas, parse errors e o subset XAU.

## Arquivos
- `ingest_live_signals.py` — biblioteca + CLI **read-only** que itera o event store, normaliza e é robusto a linhas inválidas. Sem side effects no import. Filtros: `--symbol`, `--since`, `--limit`, `--path`.
- `report_forward_quality.py` — calcula as 12 métricas e escreve o relatório. Escreve **apenas** em `reports/`.
- `reports/forward_quality_latest.md` (+ opcional `.json`) — saída.

## Uso
```bash
cd my-strategy/core/forward_outcome
python3 report_forward_quality.py                      # todos os ativos
python3 report_forward_quality.py --symbol XAUUSD      # subset XAU
python3 report_forward_quality.py --no-write           # só imprime, não escreve
python3 report_forward_quality.py --json               # também grava .json
```

## Fonte e invariantes
- **Fonte:** `alert-bridge/logs/indicator_signals.jsonl` — **read-only, source-of-truth do comportamento live** dos alertas/indicadores. Schema v1.0 (`ts_signal, base_symbol, symbol, timeframe, indicator_name, signal_type, price, signal_hash, payload_full, …`).
- `signal_hash` do event store = **`ingestion_hash`** (id de evento/dedup do receiver), NÃO o signal_hash estratégico da L1.
- **Nunca** escreve/trunca/bloqueia o event store. Nunca toca receiver, RAW, journal, broker, scheduler, runtime L1.
- Único output permitido: `reports/`.

## Não faz (limites duros)
Não calcula R · não compara backtest · não envia Telegram · não cria scheduler · não muta event store · não valida edge. Densidade alta ≠ edge — é ruído a investigar.

## Próximas fases (roadmap)
Fase 2 match candidato↔sinal · Fase 3 forward R · Fase 4 comparação backtest×forward · Fase 5 hipóteses + digest de manutenção.
