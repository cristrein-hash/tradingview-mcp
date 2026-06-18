# XAU 4H L2/BPT — TAKE Engine: pipeline reprodutível (canônico)

**Status:** `CANONICAL · PARTIALLY REPRODUCIBLE · 2 BUILDERS MISSING (HARD-STOP) · OPTION B BLOCKED` · **Data:** 2026-06-18
Canoniza o pipeline do TAKE engine após o incidente de reprodutibilidade. Foundation: [[INCIDENT_L2_BPT_ENGINE_REPRODUCIBILITY_TMP_PIPELINE]] · [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]].

## 1. Por que o incidente aconteceu
Pesquisa rápida com builders escritos direto em `/tmp` (não versionados); só scripts downstream foram promovidos ao repo. `/tmp` volátil → builders de entrada perdidos. Detalhe no incidente.

## 2. Pipeline completo (15 etapas)
`RAW 4H gz → [1D bars] → [frozen raw_features] → detector v2.2 → candidate_matrix → pruned_base_v2 → demand/supply → macro → d1_sig → svp → 84-factor extractor → qualification matrix → TAKE rubric (LLM) → outcome evaluator → matched-random baselines`. Mapa completo (input/output/builder/status/determinismo): `results/l2_bpt_engine_pipeline_canonical_map.csv`.

## 3. Builders VERSIONADOS (OK)
detector (promovido `pipeline/detectors/L2_detector_v2_2.py`), GT (promovido), candidate_matrix (`l2_layer23_diag.py`), pruned_base, demand_supply_quality, macro_context_enrich, extract_1d_v3 (promovido `pipeline/features/`), extract_svp, qualification_extract, validate_qualification, build_1d_ohlc. Rubrica `QUALIFICATION_RUBRIC.md`.

## 4. Builders RECONSTRUÍDOS
**Nenhum.** Os 2 faltantes (frozen `extract_raw_features.py`; `XAU_1D_bars.jsonl` builder) **NÃO foram reconstruídos** — mecanismo mapeado mas field-equivalence não validada → HARD-STOP (§5). Reconstrução adiada para bloco dedicado com autorização.

## 5. Fidelity gates
- **raw_features:** `results/l2_bpt_repro_fidelity_gate_raw_features.csv` — mecanismo 100% mapeado (OHLC do bar fechado, RSI do snapshot forming, bubbles_recent = acúmulo de `pine_shapes_bubbles[].activations`), mas pareamento exato não reproduzível com confiança sem o original → **HARD_STOP**.
- **daily_bars:** `results/l2_bpt_repro_fidelity_gate_daily_bars.csv` — **DEFERRED** (low-risk).
- **Gate obrigatório:** reproduzir `raw_features_2020_2026.jsonl` **byte/field-equivalent** (ref SHA `9fac96b9`) ANTES de aplicar em 2013-2017. Sentinela `pipeline/.fidelity_pass` (ausente).

## 6. Artefatos de referência (preservados, íntegros)
`repro_recovery/` (51 arquivos; ver `results/l2_bpt_repro_preserved_tmp_artifacts.csv`). Frozen `raw_features_2020_2026.jsonl` SHA `9fac96b9` idêntico em SHA256SUMS+safety pack+/tmp+repro_recovery. Decisões LLM 2020-2026 congeladas (`decisions_merged.csv` + `qual_dec_*`).

## 7. Política /tmp (REGRA PERMANENTE)
> **Nada que gere `raw_features`, `candidate_matrix`, `pruned_base`, feature matrix, decision matrix, outcome, baselines ou bootstrap pode existir apenas em `/tmp`.** `/tmp` é só scratch. Se o output for usado em decisão, o builder DEVE ser versionado ANTES do próximo bloco. (Ideal: check de CI que falha se um script do pipeline lê/importa de `/tmp`.)

## 8. Política de determinismo LLM
Etapas 1-12,14,15 = determinísticas. Etapa 13 (reasoning TAKE) = **LLM NÃO-determinístico** (AI_REVIEW). Decisões 2020-2026 congeladas como canônicas. Ver [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]].

## 9. Como rodar dry-run
`python3 pipeline/run_l2_bpt_engine_pipeline.py --dry-run` → lista as 15 etapas, marca builders faltantes, sinaliza não-determinismo, conclui REPRODUZÍVEL=NÃO.

## 10. Como reproduzir 2020-2026
`--reproduce-2020-2026` → roda o fidelity gate. **Atualmente HARD-STOP** (frozen + 1D builders faltam). Após reconstrução autorizada, comparar output vs SHA `9fac96b9` e, se PASS, criar `pipeline/.fidelity_pass`.

## 11. O que ainda bloqueia a Opção B
1. **frozen builder** + **1D-bars builder** faltam → pipeline não re-executável (HARD-STOP).
2. **TODO script do pipeline lê/escreve `/tmp` HARDCODED** (achado DA): `L2_detector_v2_2.py` lê `/tmp/raw_features` + `/tmp/XAU_1D_bars`; `l2_layer23_diag.py` importa o detector (PYTHONPATH) + lê `/tmp/L2_ground_truth_v1.json`; `qualification_extract.py` lê `/tmp/{raw_features,svp_bars,d1_sig_v3}`; `demand_supply_quality`/`macro_context_enrich`/`validate_qualification` lêem `/tmp/raw_features`. Mesmo com os 2 builders reconstruídos, o pipeline **não roda em dataset novo sem uma passada de PARAMETRIZAÇÃO DE PATHS** (substituir `/tmp/*` por args do runner). Não feito aqui (mexeria em ~8 scripts — bloco autorizado separado).
3. **reasoning é LLM não-determinístico** → "mesmo engine sem retune" exige re-rodar subagentes (decisões novas) OU converter rubrica em score determinístico (Opção C, bloco futuro).
Até (1) reconstruir+gate, (2) parametrizar paths, e (3) decidir o determinismo, **a validação Opção B permanece BLOQUEADA**.

## 12. DA appendix
Ver relatório do bloco. Checklist: builders mapeados ✓ · recuperáveis promovidos ✓ (detector/GT/d1_sig) · faltantes reconstruídos só sob gate ✓ (não reconstruídos = hard-stop) · ainda missing: 2 builders ✓ documentado · dependência /tmp: regra permanente criada (§7) · reasoning marcado não-determinístico ✓ · dry-run funciona ✓ · reproduzir 2020-2026: HARD-STOP ✓ · nenhuma validação Opção B rodada ✓ · produção intacta ✓ · sem SLIM/chart/MCP/plot ✓.

---
*Canônico. Pipeline parcialmente reprodutível; 2 builders faltam (hard-stop); reasoning não-determinístico. Opção B bloqueada. Produção intacta.*
