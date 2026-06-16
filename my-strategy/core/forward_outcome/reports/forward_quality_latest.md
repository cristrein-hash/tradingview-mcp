# Forward Signal Quality — MVP Fase 1 (read-only)

> Mede QUALIDADE/OPERAÇÃO do event store live, **não** edge. Sem R, sem comparação backtest, sem Telegram. Fonte: `alert-bridge/logs/indicator_signals.jsonl` (read-only).

## 1–2. Volume e range temporal
- **Sinais lidos (após filtros):** 16454  ·  linhas totais no arquivo: 16454  ·  filtrados fora: 0
- **Filtros:** symbol=`None` · since=`None` · limit=`None`
- **Range:** 2026-05-17T21:00:00.572031+00:00 → 2026-06-16T08:00:00+00:00  ·  span 30 dias  ·  **~548.5 sinais/dia**

## 3. Dias de maior densidade (top 5)
| dia | sinais |
|---|---|
| 2026-06-05 | 1090 |
| 2026-06-10 | 1030 |
| 2026-06-15 | 992 |
| 2026-05-28 | 934 |
| 2026-06-02 | 928 |

## 4. Sinais por símbolo
| base_symbol | sinais |
|---|---|
| ETHUSD | 4488 |
| XAUUSD | 3307 |
| XAGUSD | 2997 |
| EURUSD | 2865 |
| US500 | 2794 |
| (vazio) | 3 |

## 5. Provider / indicador
**Provider:**
| provider | sinais |
|---|---|
| PEPPERSTONE | 12892 |
| (nenhum) | 3562 |

**Indicador (top 10):**
| indicador | sinais |
|---|---|
| Custom_OB_Detector | 9195 |
| Market_Bubbles | 3863 |
| RSI | 2415 |
| NAS_TopBottom_Detector | 976 |
| (vazio) | 2 |
| TEST | 2 |
| TEST_PROVIDER_NORMALIZATION | 1 |

**Timeframe:**
| timeframe | sinais |
|---|---|
| 15 | 8722 |
| 30 | 4603 |
| 60 | 2333 |
| 240 | 660 |
| D | 135 |
| 4H | 1 |

## 6. Completude de payload
| campo | presentes | % |
|---|---|---|
| has_timestamp | 16454 | 100.0% |
| has_symbol | 16454 | 100.0% |
| has_timeframe | 16454 | 100.0% |
| has_source | 16452 | 99.99% |
| has_signal_type | 16452 | 99.99% |
| has_payload | 16454 | 100.0% |
| has_ingestion_hash | 16454 | 100.0% |

## 7. Duplicatas
- por `ingestion_hash`: **0**  ·  por tupla (sem hash): 0  ·  registros sem hash: 0
- **total duplicatas: 0  ·  taxa: 0.0%**

## 8–9. Integridade
- **Parse errors (JSON inválido):** 0
- **Quarantine vivo:** `indicator_signals_quarantined.jsonl` (0 bytes na auditoria 2026-06-16 — vazio).

## 10. Subset XAU (PEPPERSTONE:XAUUSD / XAUUSD)
- **Sinais XAU:** 3310
- **Por timeframe:**
| tf | sinais |
|---|---|
| 15 | 1747 |
| 30 | 922 |
| 60 | 470 |
| 240 | 140 |
| D | 30 |
| 4H | 1 |
- **Por indicador:**
| indicador | sinais |
|---|---|
| Custom_OB_Detector | 1644 |
| Market_Bubbles | 1031 |
| RSI | 402 |
| NAS_TopBottom_Detector | 228 |
| (vazio) | 2 |
| TEST | 2 |
| TEST_PROVIDER_NORMALIZATION | 1 |
- **Por dia (últimos 7 dias com XAU):**
| dia | sinais |
|---|---|
| 2026-06-09 | 191 |
| 2026-06-10 | 269 |
| 2026-06-11 | 211 |
| 2026-06-12 | 131 |
| 2026-06-14 | 23 |
| 2026-06-15 | 229 |
| 2026-06-16 | 60 |
- **Últimos 8 sinais XAU:**
| ts_signal | symbol | tf | indicador | signal_type |
|---|---|---|---|---|
| 2026-06-16T07:00:00Z | PEPPERSTONE:XAUUSD | 60 | Custom_OB_Detector | ob_bearish_violated |
| 2026-06-16T07:15:00Z | PEPPERSTONE:XAUUSD | 15 | Market_Bubbles | Small_Buy |
| 2026-06-16T07:30:00Z | PEPPERSTONE:XAUUSD | 30 | Custom_OB_Detector | ob_bearish_violated |
| 2026-06-16T07:30:00Z | PEPPERSTONE:XAUUSD | 30 | Market_Bubbles | Small_Buy |
| 2026-06-16T07:30:00Z | PEPPERSTONE:XAUUSD | 30 | Custom_OB_Detector | new_ob_bullish |
| 2026-06-16T07:45:00Z | PEPPERSTONE:XAUUSD | 15 | Custom_OB_Detector | ob_bearish_violated |
| 2026-06-16T07:45:00Z | PEPPERSTONE:XAUUSD | 15 | Market_Bubbles | Medium_Buy |
| 2026-06-16T08:00:00Z | PEPPERSTONE:XAUUSD | 15 | Market_Bubbles | Medium_Buy |

## 11. Clusters por hora (UTC) — densidade/ruído
| hora_utc | sinais |
|---|---|
| 0 | 588 |
| 1 | 767 |
| 2 | 750 |
| 3 | 631 |
| 4 | 671 |
| 5 | 668 |
| 6 | 709 |
| 7 | 680 |
| 8 | 630 |
| 9 | 646 |
| 10 | 687 |
| 11 | 640 |
| 12 | 834 |
| 13 | 946 |
| 14 | 883 |
| 15 | 732 |
| 16 | 656 |
| 17 | 688 |
| 18 | 610 |
| 19 | 597 |
| 20 | 556 |
| 21 | 401 |
| 22 | 855 |
| 23 | 627 |

## 12. Limitações (não esquecer)
- **Missing negatives:** o event store loga o que disparou, não o que *deveria* ter disparado. Não mede recall.
- **Payload drift / indicator version drift:** `indicator_version` muda no tempo; mesma `signal_type` pode ter semântica diferente entre versões.
- **Sem outcome/R ainda:** este MVP mede só qualidade/operação. R e comparação backtest são fases futuras.
- **Não valida edge.** Densidade alta ≠ edge; é sinal de ruído a investigar.

_Gerado por `report_forward_quality.py` (read-only). Não altera o event store._
