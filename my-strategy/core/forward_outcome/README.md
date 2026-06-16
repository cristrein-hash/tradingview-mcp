# Forward Outcome Layer — `core/forward_outcome/`

Implementação **incremental** da Forward Outcome Layer (spec: [`docs/FORWARD_OUTCOME_LAYER_SPEC.md`](../../../docs/FORWARD_OUTCOME_LAYER_SPEC.md), roadmap: [`docs/FORWARD_OUTCOME_LAYER_ROADMAP.md`](../../../docs/FORWARD_OUTCOME_LAYER_ROADMAP.md)).

**Estado: MVP Fase 1 + Fase 2 (read-only).** Sem R, sem comparação backtest, sem Telegram, sem scheduler.

## O que faz
- **Fase 1 — qualidade:** *o `indicator_signals.jsonl` está limpo, completo, rastreável e útil como fonte forward?* Mede densidade, completude de payload, duplicatas, parse errors, subset XAU.
- **Fase 2 — matching:** *quando a L1 emite (ou emitiria) um candidato OPERACIONAL, achamos os live signals XAU 240 correspondentes na mesma janela?* Classifica matched_exact_bar / matched_within_window / unmatched_no_live_signal / live_signal_no_strategy_candidate / candidate_missing_fields / insufficient_forward_sample.

## Arquivos
- `ingest_live_signals.py` — biblioteca + CLI **read-only** que itera o event store, normaliza e é robusto a linhas inválidas. Sem side effects no import. Filtros: `--symbol`, `--since`, `--limit`, `--path`.
- `report_forward_quality.py` — Fase 1: 12 métricas → `reports/forward_quality_latest.md`(+`.json`).
- `match_candidates.py` — Fase 2: junta candidatos L1 (`.runtime_state/l1_cycle.log` + journal opcional) ↔ XAU 240 live signals → `reports/candidate_match_latest.md`(+`.json`).
- Saídas **apenas** em `reports/`.

## Uso
```bash
cd my-strategy/core/forward_outcome
python3 report_forward_quality.py --symbol XAUUSD      # Fase 1
python3 match_candidates.py --json                     # Fase 2 (match)
python3 match_candidates.py --no-write                 # só imprime
```

## Identidades (regra dura)
`signal_hash` (log L1 / runtime) = identidade **estratégica** do candidato. `ingestion_hash` (= `signal_hash` do event store) = identidade do **evento bruto**. **Nunca** comparados entre si; o match é por bar/símbolo/tf/janela temporal.

## Fonte e invariantes
- **Fonte:** `alert-bridge/logs/indicator_signals.jsonl` — **read-only, source-of-truth do comportamento live** dos alertas/indicadores. Schema v1.0 (`ts_signal, base_symbol, symbol, timeframe, indicator_name, signal_type, price, signal_hash, payload_full, …`).
- `signal_hash` do event store = **`ingestion_hash`** (id de evento/dedup do receiver), NÃO o signal_hash estratégico da L1.
- **Nunca** escreve/trunca/bloqueia o event store. Nunca toca receiver, RAW, journal, broker, scheduler, runtime L1.
- Único output permitido: `reports/`.

## Não faz (limites duros)
Não calcula R · não compara backtest · não envia Telegram · não cria scheduler · não muta event store · não valida edge. Densidade alta ≠ edge — é ruído a investigar.

## Próximas fases (roadmap)
Fase 2 match candidato↔sinal · Fase 3 forward R · Fase 4 comparação backtest×forward · Fase 5 hipóteses + digest de manutenção.
