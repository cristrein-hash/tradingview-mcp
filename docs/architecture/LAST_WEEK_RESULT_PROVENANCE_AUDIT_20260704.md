# LAST WEEK — RESULT PROVENANCE AUDIT

**Incident audit** iniciado por Cris 2026-07-07 (suspeita: resultados sem leitura RAW / sem prova de origem). Modo: read-only, no new research, no push sem autorização. Ledger companion: `LAST_WEEK_NUMERIC_CLAIMS_LEDGER_20260704.md`.

## 1. Executive verdict
**PARTIAL_CONTAMINATION** — com **RAW_FIRST_VIOLATION_CONFIRMED localizado ao bloco Fractal-MTF (2026-07-07)**.
- O grosso da semana (trabalho 15M) tem **linhagem RAW→primitives provada e forçada por source guard (PASS)** e reproduz → VERIFIED_DERIVED.
- **UM bloco viola RAW-first**: o leitor Fractal-MTF resampleou 15M→4H/1D à mão e reinventou demandas, ignorando `htf_primitives/` (RAW 4H/1D nativos, já existentes) → source guard FAIL → **INVALID**.
- 3 BLOCKERs de safety (naming "catalog") = falsos-positivos de padrão, não contaminação de dados (ver §5).

## 2. Scope
- Datas: 2026-06-30 → 2026-07-07 (últimos 7 dias).
- Commits: **198**, todos autor `Cristiano Trein` (+Co-Authored Claude), **0 commits de subagente**, todos pushed (HEAD==origin 7fa2b35).
- Artefatos: 764 ficheiros tocados (456 .py, 154 .json, 96 .md, 29 .sql). 342 no dir de pesquisa 15M, 170 em results/.

## 3. Trust matrix by block

| block | key results | source | reprodutibilidade | STATUS | action |
|---|---|---|---|---|---|
| **RAW 15M extension** | +2714 barras, 9º bloco, kill-check N=0, guard 7/7 | **RAW gz 15M direto** + manifest/SHA/roundtrip | manifest validado | **VERIFIED_RAW** | usável |
| **Lab E (slippage)** | SB +233,6R r/DD16,4 | primitives (RAW-15M lineage) | não re-rodado | **VERIFIED_DERIVED** | usável; rerun opcional |
| **Lab A (entry geometry)** | P1 +19R p=0,726; resto FAILS | primitives + r3_universe | não re-rodado | **VERIFIED_DERIVED** | usável |
| **Lab F (risk/streak)** | NO_STREAK_DD_WR_SOLUTION; F4 sizing | primitives | não | **VERIFIED_DERIVED** | usável |
| **Lab G (Sistema A)** | N53 WR60,4 NET+25,9; 21/53 fora-base | primitives → lab_g_candidates (sancionado) | não | **VERIFIED_DERIVED** | usável (já era POSITIVO_FRÁGIL) |
| **PLT/DM assimilação** | escada r=3 9/10; confluência N101 | primitives + shapes MCP | reproduz | **VERIFIED_DERIVED** | usável |
| **Entry engine 3R** | MARKUP 54,2% N96; reclaim-R 61,4% | primitives | **reproduz byte** | **VERIFIED_DERIVED** | usável |
| **Filter/phase studies** | ER OOF 63,5% (partial); FaseD∩FSM4 = mining artifact | primitives | reproduz; DA mata FaseD∩FSM4 | **PARTIAL / INVALID** | ER=NOT_FOR_DECISION; FaseD∩FSM4=descartado |
| **Fractal MTF (HTF demand retest)** | OOF 0,647 mining_null 0,01 | **15M RESAMPLEADO (não RAW 4H/1D)** | reproduz nº, fonte inválida | **INVALID (RAW-FIRST VIOLATION)** | **CONGELAR + rerun sobre htf_primitives RAW** |
| **Supabase deltas (9 seeds)** | 273→281 rows | seeds committed + read-back | read-back OK | **VERIFIED** | usável (só descrevem, não decidem) |

## 4. Claims ledger summary
- Total claims-chave: 15. **VERIFIED_RAW: 1** (C07) · **VERIFIED_DERIVED: 9** · **PARTIAL: 1** (C12 ER) · **SUSPECT/INVALID: 2** (C13 mining-artifact, C14 fractal-MTF violation) · auto-refutadas contadas em derived (C08/C11/C15).

## 5. Critical findings
1. **RAW-first violation (grave):** bloco Fractal-MTF (`mtf_kit.py`, `mtf_feat_*.py`, 2026-07-07) **resampleou 15M→4H/1D** e reinventou demanda por zigzag, **quando `htf_primitives/htf_{4H,1D}.primitives.json` (do RAW 4H/1D via `build_htf_primitives.py`, 2026-06-28) já existiam** com OB detector nativo. Source guard **FAIL** em `mtf_feat_htf_demand_retest.py`. → resultado 0,647 **INVALID por fonte**.
2. **Resultados apresentados sem leitura RAW direta:** confirmado estruturalmente — **267 scripts leem `primitives/` (derived)**, quase nenhum lê RAW gz direto. MAS os primitives têm linhagem RAW provada + source guard, logo é o padrão SANCIONADO (não contaminação) — **exceto o bloco MTF**.
3. **3 safety BLOCKERs:** `catalog_manual_tags/pairing/structural_catalog_*.py` disparam `forbidden_paths` por conterem "catalog" no nome. São scripts de pesquisa que escrevem em `results/`, **não** tocam o catalog de produção. Falso-positivo de naming; recomenda-se renomear ou whitelistar.
4. **Sem manifest ao lado de `primitives/`:** a linhagem existe (docs RAW_15M_EXTENSION + source guard) mas não há um `primitives/MANIFEST.md` local — recomendado adicionar.
5. **Subagentes:** 0 commits diretos (COMPLIANT). Workflows retornam resultados; o commit foi sempre meu.

## 6. Immediate corrections
- **C14 (Fractal-MTF 0,647):** reclassificado **INVALID / NOT_FOR_DECISION**. Congelado. Exige **rerun sobre `htf_primitives/` (RAW 4H/1D nativo + OB detector)** antes de qualquer confiança.
- **C13 (FaseD∩FSM4 68,2%):** já descartado pelo próprio DA (mining artifact) — permanece NOT_FOR_DECISION.
- **C12 (ER OOF 63,5%):** mantém-se PROMISSOR-NÃO-VALIDADO (multiplicidade declarada) — NOT_FOR_DECISION até forward.

## 7. What remains usable (VERIFIED)
- RAW 15M extension (VERIFIED_RAW). · Labs E/A/F/G, PLT/DM, Entry engine 3R (54,2%/reclaim-R 61,4%), negativos honestos (filtro=muro, phase-LOO confound) — todos VERIFIED_DERIVED com linhagem + source guard PASS + reprodução onde testada. · Supabase 281 rows (índice, não decisão).

## 8. What must be frozen (NOT_FOR_DECISION)
- **Fractal-MTF htf_demand_retest 0,647** (RAW-first violation — congelado até rerun sobre htf_primitives).
- **FaseD∩FSM4 68,2%** (mining artifact).
- **ER OOF 63,5%** (promissor, multiplicidade não-corrigida).
- Nenhum destes pode orientar decisão estratégica, gate, ou status master.

## 9. Required reruns
| rerun | inputs | RAW mapping | script | acceptance |
|---|---|---|---|---|
| **HTF demand retest CORRETO** | `htf_primitives/htf_4H.primitives.json` + `htf_1D.primitives.json` (RAW 4H/1D nativos) + OB detector zones nativas | RAW 4H/1D via build_htf_primitives (já feito) | reescrever mtf_feat_htf_demand_retest p/ ler htf_primitives (não resample); passar source guard | source guard PASS + OOF + mining-null composto + causal 0 violações |
| (opcional) byte-rerun Labs E/A/F/G | primitives | RAW 15M | scripts dos labs | outputs byte-idênticos aos committed |

## 10. Process fixes (adicionar ao canon)
1. **Nenhum report numérico HTF/multi-TF sem passar `_source_guard.py`** (estender o guard a HTF: fonte permitida = RAW 4H/1D gz + `htf_primitives/`; PROIBIR resample de 15M).
2. **Verificar `dataset_registry.json` + DATA_STORAGE_POLICY ANTES de qualquer leitura multi-TF** — nunca resamplear nem reinventar deteção que o RAW já traz ([[feedback_verify_raw_source_before_any_data_read]]).
3. **Nenhum número sem script+output+source_ref** committados; **provenance appendix** obrigatório por lab.
4. Adicionar `primitives/MANIFEST.md` + `htf_primitives/MANIFEST.md` com SHA + RAW source.
5. Subagentes não reportam métrica sem artifact salvo (já cumprido: 0 commits subagente).

## Assinatura da auditoria
- HEAD 7fa2b35 == origin. Safety: BLOCKER=3 (naming catalog, falso-positivo), WARNING=1, INFO=50 (report-only).
- Verificado: linhagem 15M provada + source guard PASS; **1 violação RAW-first (MTF) confirmada e congelada**.
