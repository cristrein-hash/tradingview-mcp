# XAU 4H L2/BPT — TAKE Engine: pipeline reprodutível (canônico)

**Status:** `CANONICAL · PARTIALLY REPRODUCIBLE · 2 BUILDERS MISSING (HARD-STOP) · OPTION B BLOCKED` · **Data:** 2026-06-18
Canoniza o pipeline do TAKE engine após o incidente de reprodutibilidade. Foundation: [[INCIDENT_L2_BPT_ENGINE_REPRODUCIBILITY_TMP_PIPELINE]] · [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]].

## 1. Por que o incidente aconteceu
Pesquisa rápida com builders escritos direto em `/tmp` (não versionados); só scripts downstream foram promovidos ao repo. `/tmp` volátil → builders de entrada perdidos. Detalhe no incidente.

## 2. Pipeline completo (15 etapas)
`RAW 4H gz → [1D bars] → [frozen raw_features] → detector v2.2 → candidate_matrix → pruned_base_v2 → demand/supply → macro → d1_sig → svp → 84-factor extractor → qualification matrix → TAKE rubric (LLM) → outcome evaluator → matched-random baselines`. Mapa completo (input/output/builder/status/determinismo): `results/l2_bpt_engine_pipeline_canonical_map.csv`.

## 3. Builders VERSIONADOS (OK)
detector (promovido `pipeline/detectors/L2_detector_v2_2.py`), GT (promovido), candidate_matrix (`l2_layer23_diag.py`), pruned_base, demand_supply_quality, macro_context_enrich, extract_1d_v3 (promovido `pipeline/features/`), extract_svp, qualification_extract, validate_qualification, build_1d_ohlc. Rubrica `QUALIFICATION_RUBRIC.md`.

## 4. Builders RECONSTRUÍDOS (2026-06-18, bloco de desbloqueio)
- **`pipeline/builders/reconstruct_raw_features.py`** (frozen) — RECONSTRUÍDO. Regras deduzidas empiricamente do ref: OHLC+vol do bar fechado do buffer; RSI do snapshot forming (mais-formado); bubbles_recent = acúmulo de `pine_shapes_bubbles[].activations` (plots 0/2/4/6/8/10, janela bars_ago 0..60, índice global); nas/smc_recent = labels x≤30. **Gate: OHLC/vol/bubbles=100% field-equivalent; rsi 97.3%/nas 97.7% residual (§5).**
- **`pipeline/builders/build_xau_1d_bars.py`** (1D bars) — RECONSTRUÍDO (projeção {time,close} de XAU_1D_ohlc). **Gate: 100% field-equivalent PASS.**

## 5. Fidelity gates (atualizado — resíduo resolvido p/ 99.6%, decision-invariant)
- **raw_features:** `results/l2_bpt_repro_fidelity_gate_raw_features{,_v2}.csv` — **ESTRUTURAL 100% byte-equivalent** (OHLC/volume/bubbles_recent). Descoberta da regra **carry-to-next** (replay estala → 2o snapshot do mesmo cur-time forma o PRÓXIMO bar; causal, verificado via replay_current_date) elevou **rsi 97.26→99.62%, nas 97.66→99.74%**. Resíduo restante (38 rsi diffs) = **dup_ts replay-stall artifacts** cujo handling exato do builder original é irreproduzível. **PROVA de não-criticidade:** ZERO dos 38 diffs cruzam o limiar rsi<30 → nenhum flag oversold dos 4 episódios tocados vira → **decisão INALTERADA**. Strict-gate=FAIL, mas **decision-invariant**. DA a72c93cb aprovou ship + unblock condicional.
- **daily_bars:** `results/l2_bpt_repro_fidelity_gate_daily_bars.csv` — **PASS** (100% field-equivalent).
- Sweep das 12 regras: `results/l2_bpt_repro_snapshot_selection_sweep.csv`; composta vencedora: `..._composite.csv`; casos: `..._rsi_nas_residue_cases.csv`.
- **Sentinela `pipeline/.fidelity_pass`:** ainda AUSENTE — Opção B usa OHLC/vol/bubbles (100%) + categórico rsi<30 (invariante), NÃO o rsi contínuo. Unblock JUSTIFICADO para o engine categórico-30 (decisão do Cris criar a sentinela). Caveat: feature futura usando rsi CONTÍNUO re-expõe 4 diffs sub-7pt.

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

## 11. O que ainda bloqueia a Opção B (estado pós-desbloqueio)
1. **frozen gate não-PASS-completo (rsi/nas residual 2.6%)** → estrutural reproduzível, mas RSI (crítico p/ 84 fatores) field-equivalente só 97.3%. Decisão do Cris: aceitar resíduo OU resolver a regra de seleção de snapshot em dup-capture. **1D-bars: PASS.** [parcialmente resolvido]
2. **Parametrização de paths `/tmp` NÃO feita** (HARD-STOP do gate impediu prosseguir). `L2_detector_v2_2.py`, `l2_layer23_diag.py`, `qualification_extract.py`, `demand_supply_quality`, `macro_context_enrich`, `validate_qualification`, `extract_svp`, `extract_1d_v3` ainda lêem/escrevem `/tmp` hardcoded → ~8 scripts a parametrizar (proposta: `os.environ.get('X', '/tmp/...')`, default preserva comportamento). [PENDENTE]
3. **reasoning LLM não-determinístico** → "mesmo engine sem retune" exige re-rodar subagentes (decisões novas) OU score determinístico (Opção C). [PENDENTE — decisão]
**Opção B BLOQUEADA** até (1) Cris decidir o resíduo rsi, (2) parametrizar paths, (3) decidir determinismo.

## 12. DA appendix
Ver relatório do bloco. Checklist: builders mapeados ✓ · recuperáveis promovidos ✓ (detector/GT/d1_sig) · faltantes reconstruídos só sob gate ✓ (não reconstruídos = hard-stop) · ainda missing: 2 builders ✓ documentado · dependência /tmp: regra permanente criada (§7) · reasoning marcado não-determinístico ✓ · dry-run funciona ✓ · reproduzir 2020-2026: HARD-STOP ✓ · nenhuma validação Opção B rodada ✓ · produção intacta ✓ · sem SLIM/chart/MCP/plot ✓.

---
*Canônico. Pipeline parcialmente reprodutível; 2 builders faltam (hard-stop); reasoning não-determinístico. Opção B bloqueada. Produção intacta.*
