# XAU 15M Research Execution Protocol V1 — Rollout

**Cris 2026-07-08.** O que foi criado, como usar, e como teria impedido os erros recentes. **Este rollout é doc + guards executáveis — NÃO spawnou subagentes (Agent tool); nenhuma métrica foi gerada aqui.**

## O que foi criado
- **Protocolo (autoridade):** `docs/project_authority/XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.md` — 10 stages, baldes canónicos, regras de fonte, regras de subagente, status language.
- **Templates:** `docs/templates/XAU_15M_LAB_GATE_MANIFEST_TEMPLATE.md` (manifest com bloco `json` machine-readable) · `docs/templates/XAU_15M_CLAIMS_LEDGER_TEMPLATE.csv`.
- **Blockers executáveis (fail-loud, stdlib):**
  - `scripts/safety/check_xau_15m_raw_lineage.py` → `RAW_LINEAGE_PASS`/FAIL.
  - `scripts/safety/check_xau_15m_structural_first.py` → `STRUCTURAL_FIRST_PASS`/FAIL.
  - `scripts/safety/check_xau_15m_claims_ledger.py` → `CLAIMS_LEDGER_PASS`/FAIL.
  - `scripts/safety/run_xau_15m_lab_gate.py` → runner único → `XAU_15M_LAB_GATE_PASS`/FAIL.

## Como usar (todo lab 15M futuro)
1. Copiar o manifest template → `docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md`, preencher o bloco `json`.
2. Stage 3: gerar tabela estrutural (regime+leg+family) ANTES de indicadores; outputs carregam colunas de regime+familia.
3. Preencher o claims ledger (todo número → script/input/output/source_ref).
4. Correr o gate:
   ```
   python scripts/safety/run_xau_15m_lab_gate.py --manifest docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md \
     --report docs/architecture/XAU_15M_<LAB>_ROUND_20260708.md \
     --ledger research/xau_15m_bb_nas_leonardo/results/XAU_15M_<LAB>_claims.csv \
     --results research/xau_15m_bb_nas_leonardo/results/<lab>_results.csv
   ```
5. Sem `XAU_15M_LAB_GATE_PASS`, o lab **não** está completo e **não** vai a commit/aprovação.

## Verificação (2026-07-08, testado no scratchpad)
- lineage BAD manifest → **FAIL** (raw inexistente, derived sem source_ref/checksum, `slim`, `resample`+allow=false, HTF stale não declarado).
- lineage GOOD → **PASS** (HD externo ausente = WARN, não bloqueia offline).
- structural CSV com `regime`+`subfam` → **PASS**; CSV sem regime/família → **FAIL** ("indicador sem contexto = PROIBIDO").
- claims: ledger template/vazio → **FAIL**; ledger real cobrindo os números → **PASS**.
- runner integrado (manifest+report+ledger válidos) → **XAU_15M_LAB_GATE_PASS**.

## Como isto teria impedido os erros recentes
- **Fractal-MTF (resample 15M→4H como fonte):** `allow_resample=false` + banned-source → lineage FAIL antes de gerar 0,647.
- **Análise global descontextualizada (RSI global estéril):** structural-first exige colunas de regime+família no output → global scan sem bucket = FAIL.
- **"apareceu 61%" sem artefato:** claims-ledger exige script/input/output/source por número → sem ledger, report bloqueado.
- **Veredito prematuro NO_CLEAN_FILTER:** Stage 7 exige DA adversarial (Agent tool real) + status language sem "validated" nu.
- **Derived sem lineage / HTF stale escondido:** lineage exige source_ref+checksum e `htf_stale_declared`.

## Grandfathering
Labs anteriores a 2026-07-08 (swept-runner, intra-BEAR, RANGE, D-bear) ficam **grandfathered** — não re-validados retroativamente. **Todo lab 15M novo — em especial XAU 15M SHORT — tem de passar o gate.**

## Estado
`NO_NEW_STRATEGY_WORK` · `NO_XAU_15M_SHORT` · `NO_NEW_LAB` até este protocolo estar commitado e em uso. Doc+guards apenas; nada de produção/Telegram/runtime/chart/RAW/Supabase.
