# INCIDENT — Last Week Result Provenance Audit (EXPANDED)

**Consolidação Git + Supabase + memória/status.** Cris 2026-07-07. Read-only, sem push/SQL-write/revert/delete/novo-lab.

## VEREDITO: PARTIAL_CONTAMINATION + RAW_FIRST_VIOLATION_CONFIRMED
Contaminação **localizada** ao bloco **Fractal-MTF (2026-07-07)**. O resto da semana tem linhagem provada + source guard PASS. Supabase/memória carregam os caveats corretos; status master limpo.

## 1. Resultado do audit parcial (c5581d6)
15M work = VERIFIED_DERIVED (RAW→primitives→source guard PASS); RAW 15M extension = VERIFIED_RAW; Fractal-MTF = INVALID (resample 15M em vez de RAW 4H/1D; `htf_primitives/` nativos ignorados; guard FAIL). Ledger: `LAST_WEEK_NUMERIC_CLAIMS_LEDGER_20260704.md`.

## 2. Git/push inventory (`INCIDENT_LAST_WEEK_GIT_PUSH_INVENTORY_20260704.md`)
198 commits, todos meus, **0 diretos por processo paralelo**, todos pushed exceto `c5581d6`. 49 tocam seeds; status master NÃO tocado nesta sessão.

## 3. Supabase audit (`INCIDENT_SUPABASE_LAST_WEEK_ROWS_AUDIT_20260704.md`)
MCP read-only confirmado (supabase_read_only_user, txn_read_only=on). 281 memory_items (230 migração + deltas). 9 rows desta sessão — todas com caveat correto, **nenhuma promove suspeito como validado**. 8 decisions = CORE arquiteturais. source_registry = RAW root source_of_truth.

## 4. Supabase trust matrix (`INCIDENT_SUPABASE_TRUST_MATRIX_20260704.md`)
KEEP_VERIFIED: PLT/DM, entry-engine, regra, decisions, source_registry. **SHOULD_NOT_GUIDE_DECISION**: `334948c4` (ER), `39cd6480` (FaseD artifact), `654d71bc` (fractal — +MARK_SUSPECT+NEEDS_RERUN em delta futuro).

## 5. Status/memory contamination (`INCIDENT_STATUS_MEMORY_CONTAMINATION_AUDIT_20260704.md`)
Status master 04/05 = **LIMPO** (0 menções aos suspeitos). MEMORY.md hot = corrigido (bloco INCIDENT AUDIT congela os 3). Pendente: rebaixar fractal no doc TOTAL_STRUCTURAL_READING + delta Supabase corretivo.

## 6. Claims ledger summary
15 claims-chave: **VERIFIED_RAW 1 · VERIFIED_DERIVED 9 · PARTIAL 1 (ER) · SUSPECT/INVALID 2 (FaseD, Fractal-MTF)**.

## 7. Decisões CONGELADAS (NOT_FOR_DECISION)
1. **Fractal-MTF htf_demand_retest 0,647** — INVALID por fonte (RAW-first). Congelado até rerun sobre `htf_primitives/`.
2. **FaseD∩FSM4 68,2%** — mining artifact.
3. **Kaufman-ER OOF 63,5%** — promissor-não-validado (multiplicidade).

## 8. Decisões ainda USÁVEIS
RAW 15M extension (VERIFIED_RAW) · Labs E/A/F/G, PLT/DM, Entry engine 3R (54,2% N96 reproduz byte / reclaim-R 61,4%), negativos honestos (filtro=muro, phase-LOO confound) = VERIFIED_DERIVED. Supabase 281 = índice. Nenhum destes foi contaminado.

## 9. Reruns obrigatórios
- **HTF demand retest CORRETO** sobre `htf_primitives/htf_{4H,1D}.primitives.json` (RAW nativo + OB detector), passando source guard 15M-estendido, com OOF + mining-null composto + causal-0. **Acceptance:** guard PASS + reprodução + mining-null composto < 0,1 corrigido.

## 10. Delta / correção futura recomendada (NÃO executar agora — read-only)
- **Supabase:** 1 INSERT idempotente flag para `654d71bc` (SHOULD_NOT_GUIDE_DECISION + motivo RAW-first). NÃO delete/update.
- **Doc:** editar `XAU15M_TOTAL_STRUCTURAL_READING` (fractal → INVALID).
- **Source guard:** estender a HTF (permitir RAW 4H/1D + `htf_primitives/`; PROIBIR resample de 15M).
- **Process fix:** verificar `dataset_registry.json` antes de qualquer leitura multi-TF ([[feedback_verify_raw_source_before_any_data_read]]); manifest local em `primitives/` e `htf_primitives/`.

## 11. Safety
BLOCKER=3 (naming `catalog_*` = falso-positivo, scripts de pesquisa escrevem em results/, não tocam produção; documentado, scanner não alterado), WARNING=1, INFO=50. Report-only.

## Hashes
- `c5581d6` (audit parcial, local) · commit expansão (este bloco) = novo commit local. `origin/main`=`7fa2b35`. **Push pendente de autorização.**
