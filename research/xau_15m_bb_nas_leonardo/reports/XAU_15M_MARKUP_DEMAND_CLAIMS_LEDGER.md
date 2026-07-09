# XAU 15M MARKUP-DEMAND — CLAIMS LEDGER (corrigido)
**2026-07-09.** Todo número → script/output/source. Sem claim fora deste ledger.

| # | claim | status | evidence | allowed? |
|---|---|---|---|---|
| 1 | "N96/N83 original tem +125R" | **HISTORICAL_CONTAMINATED_RESULT** | `xau_15m_n83_confirmation_leak_check_result.json` (94/96 pré-conf; 0/94 lower-low) | **NÃO como validação** |
| 2 | "Base original é inválida p/ produção" | **VALIDATED** | event-selection lookahead (DA + verificação indep. 2×) | sim |
| 3 | "Filtro Intra-Bear Capitulation é causal" | **VALIDATED** | predicado (BEAR-v5-causal + 1D bar fechado); source guard; recovery DA | sim |
| 4 | "Filtro corta losers sem cortar winners na base causal" | **VALIDATED_IN_REPAIRED_BASE** | 22/22 losers; P=0,0016 exato / 0,0047 episódico; 14/14 novos (`xau_15m_live_fireable_n83_filter_result.json`) | sim |
| 5 | "SL V1 é bom" | **TRANSFER_CANDIDATE** | `xau_15m_n83_sl_review_result.json` (domina 4 alternativas) | sim, condicional |
| 6 | "3R é o exit mais robusto" | **TRANSFER_CANDIDATE** | exit review + trailing (RLAD ~90% exposição; delay inverte) | sim, condicional |
| 7 | "Opção B é produção" | **FALSE** | +40R marginal (p 0,036-0,061); DD−15; streak 15 | — |
| 8 | "BULL bucket pode ser promissor" | **STRUCTURAL_LEAD** | 44,4%/PF 2,4/n45 (`..._n83_filter_result.json` per_regime) | precisa lab próprio |
| 9 | "Opção A pode salvar" | **UNKNOWN_PREREG_ONLY** | `..._OPTION_A_PREREG.md` | não testado |
| 10 | "15M está pronta p/ produção" | **FALSE** | tudo acima | — |
