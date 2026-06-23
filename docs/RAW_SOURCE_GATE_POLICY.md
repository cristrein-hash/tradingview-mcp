# RAW SOURCE GATE POLICY (Reader Vivo) — 2026-06-23

## Regra canônica
**Nenhum** indicador, feature visual, camada causal, label, shape, study_value, box, line, SVP, Custom OB, NAS, SMC,
bubbles, RSI/divergência, supply/demand ou campo usado pelo **Reader Vivo** pode depender de **derivado** como
fonte-de-verdade. O **RAW original / source-of-truth é obrigatório** para todos.

Derivados (`repro_recovery`, `raw_features_2020_2026.jsonl`, packets, slim, cached summaries, frozen features,
CSV/JSONL gerados) são **apenas conveniência**. Só podem ser usados se carregarem mapeamento explícito ao RAW:
`RAW_ORIGINAL_FIELD` · `RAW_SOURCE_FILE_OR_REGISTRY` · `TRANSFORM_METHOD` · `CAUSAL_TIMING_MODEL` ·
`NO_FUTURE_GUARD` · `FIDELITY_CHECK` · `DERIVED_FROM_RAW_SHA_OR_MANIFEST`. Sem isso, o campo fica **BLOQUEADO**.

## Classes de status (manifest)
| status | significado | allowed_in_blind_packet |
|---|---|---|
| `RAW_ORIGINAL_OK` | lido direto do RAW replay original | YES |
| `DERIVED_FROM_RAW_WITH_MAPPING` | derivado mas com mapeamento completo + fidelity | YES |
| `VISUAL_AUX_ONLY` | só apoio visual (chart/print), nunca fonte | NO |
| `HEURISTIC_ONLY_FLAGGED` | heurística marcada, separada do RAW | NO (só com flag) |
| `UNKNOWN_BLOCKED` | RAW existe mas ainda não mapeado/extraído | NO |
| `UNMAPPED_DERIVED_DISALLOWED` | derivado sem mapeamento RAW | NO |
| `DERIVED_ARTIFACT_BUG` | derivado comprovadamente errado (ex.: head-of-buffer) | NO |

**`allowed_as_decision` = NO para TODOS** — indicador/feature é evidência de leitura, nunca gate/score/veto/TAKE-SKIP.

## Fonte RAW canônica
`/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_*.jsonl.gz` (+ `..._SVP_LUX_RAW.jsonl.gz` p/ SVP).
Captura **as-of-bar** (causal). Campos: `study_values`, `pine_labels`, `pine_shapes_bubbles`, `pine_boxes`, `pine_lines`,
`ohlcv`, `session_vp` (bloco SVP). Manifest oficial: `…/v1/source_gate/reader_raw_source_manifest.yaml`.

## Gate executável (fail-fast)
`…/v1/source_gate/check_reader_sources.py` sai com **exit 1** se:
1. qualquer indicador usa derivado sem RAW mapping;
2. qualquer campo usa `repro_recovery`/`raw_features_2020_2026.jsonl` como fonte-de-verdade;
3. qualquer campo usa packet/slim/cache sem `DERIVED_FROM_RAW_WITH_MAPPING`;
4. qualquer indicador não tem `no_future_guard`;
5. qualquer pacote cego contém outcome/R/MFE/winner/loser/runner/trap;
6. qualquer indicador aparece como gate/score/veto;
7. qualquer `UNKNOWN_BLOCKED`/`UNMAPPED_DERIVED_DISALLOWED` está `allowed_in_blind_packet=YES`.

## Protocolo
Todo pacote cego do Reader Vivo declara `source_mapping_status`. Campos `UNMAPPED_DERIVED_DISALLOWED`/`UNKNOWN_BLOCKED`
ficam **fora** do pacote até serem mapeados ao RAW. Se RAW e derivado divergem → **RAW vence**, derivado = incidente.
Se RAW e chart divergem → abrir **source-mapping incident**. Nenhum derivado entra porque "parece funcionar".
Incidente fundador: `docs/architecture/NAS_SMC_SOURCE_INCIDENT.md`. Ver `feedback_indicators_raw_first` (memória).
