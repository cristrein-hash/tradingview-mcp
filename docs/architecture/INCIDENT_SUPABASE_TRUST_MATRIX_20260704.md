# INCIDENT — Supabase Trust Matrix

**Read-only audit.** Não deletar nem atualizar nada agora. Ações = recomendações para delta corretivo futuro.

| row (id8) / table | title | tags | source_ref aponta p/ arquivo/commit existente? | claim type | provenance status | AÇÃO |
|---|---|---|---|---|---|---|
| 7a81fec7 / memory_items | Assimilação PLT/DM | pltdm, escada-markup | sim (doc+scripts+commit b287bab) | achado metodológico (derived) | VERIFIED_DERIVED | KEEP_VERIFIED |
| 423fef5e / memory_items | PLT/DM caminhada sequencial | pltdm, processo-não-feature | sim (commit 603198a) | refutação (derived) | VERIFIED_DERIVED | KEEP_VERIFIED |
| 3ef136c3 / memory_items | Engine entry 3R MASTER | entry-3r, reclaim-speed | sim (commits 2baf2e2/28db774) | número reproduzível | VERIFIED_DERIVED | KEEP_VERIFIED |
| 21dff298 / memory_items | Leitura visual 96 entries | leitura-visual-validada | sim (commit aab6f62) | contexto | VERIFIED_DERIVED | KEEP_AS_INDEX_ONLY |
| 5fcdc7b6 / memory_items | Vencer-muro = lookahead | lookahead-escala-zigzag | sim (commit ca21524) | lição | VERIFIED | KEEP_AS_INDEX_ONLY |
| 48644c04 / memory_items | Regra dura causalidade | lookahead-gate, comportamento | sim (feedback card) | regra | VERIFIED | KEEP_VERIFIED |
| 334948c4 / memory_items | Router MURO + Kaufman ER | promissor-nao-validado | sim (commit dff3805) | **ER OOF 63,5%** | PROMISING_NOT_VALIDATED | **SHOULD_NOT_GUIDE_DECISION** |
| 39cd6480 / memory_items | Classificador FASE = artifact | mining-null, devils-advocate-matou | sim (commit 4fe7412) | **FaseD∩FSM4 = artefato** | INVALID(artifact) | **SHOULD_NOT_GUIDE_DECISION** (já reflete) |
| 654d71bc / memory_items | **Fractal MTF htf_demand_retest** | fractal-mtf, promissor-nao-validado | sim (commit 8747daf) MAS **fonte resampleada inválida** | **OOF 0,647** | **SUSPECT (INVALID por RAW-first)** | **MARK_SUSPECT_IN_FUTURE_DELTA + SHOULD_NOT_GUIDE_DECISION + NEEDS_RERUN** |
| decisions ×8 | CORE arquiteturais | — | sim | arquiteturais (não estratégia) | VERIFIED (aprovadas Cris) | KEEP_VERIFIED |
| source_registry ×7 | RAW root source_of_truth | — | `/Volumes/GUTS_ LACIE/TradingData/` | linhagem RAW | VERIFIED | KEEP_VERIFIED |
| artifacts ×12 / agent_runs ×6 / safety_reports ×1 | migração 2026-07-02 | — | sim (índice) | índice | INDEX_ONLY | KEEP_AS_INDEX_ONLY |

## Cross-check obrigatório (§4 do escopo)
- **Fractal-MTF/htf_demand_retest no Supabase (654d71bc):** ✅ presente → **SHOULD_NOT_GUIDE_DECISION** (+ rebaixar a INVALID em delta futuro; hoje row diz "promissor").
- **FaseD∩FSM4 (39cd6480):** ✅ presente e já descrito ARTEFATO → **SHOULD_NOT_GUIDE_DECISION**.
- **Kaufman-ER OOF (334948c4):** ✅ presente como promissor-não-validado → **SHOULD_NOT_GUIDE_DECISION**.
- **Lab E/A/F/G:** presentes em cards da migração/semana → **VERIFIED_DERIVED** (linhagem primitives+source guard).
- **RAW extension:** presente → **VERIFIED_RAW**.
- **Sistema A:** card existente = **POSITIVE_FRAGILE / NOT_VALIDATED / kill-check N0 inconclusivo** — confirmado NÃO aprovado.

**Nenhum delete/update agora.** Delta corretivo futuro = 1 INSERT flag para `654d71bc` (SHOULD_NOT_GUIDE + RAW-first violation).
