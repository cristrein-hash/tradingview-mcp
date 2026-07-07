# INCIDENT — Containment Check (curto)

**Cris 2026-07-07 (de-escalação):** talvez não tão grave; fechar contenção mínima. Read-only, sem revert/delete/SQL/novo-lab. Status aceite: `PARTIAL_CONTAMINATION_LOCALIZED_PENDING_CONTAINMENT`.

## 1. Audit parcial (recap)
- 15M work = **VERIFIED_DERIVED** (RAW→primitives→source guard PASS). RAW 15M extension = **VERIFIED_RAW**.
- Fractal-MTF = **INVALID** (resample 15M em vez de RAW 4H/1D; `htf_primitives/` nativos ignorados; guard FAIL). Docs: `LAST_WEEK_*_20260704.md` + `INCIDENT_*_EXPANDED_20260704.md`.

## 2. Blocos verificados / usáveis
RAW 15M extension (VERIFIED_RAW) · Labs E/A/F/G, PLT/DM, Entry engine 3R (54,2% N96 reproduz byte / reclaim-R 61,4%), negativos honestos (filtro=muro, phase-LOO confound) = VERIFIED_DERIVED. RWS-15M (PROMISSOR-NÃO-VALIDADO, pré-sessão) intacto.

## 3. Blocos congelados (NOT_FOR_DECISION)
Fractal-MTF htf_demand_retest 0,647 (INVALID RAW-first) · FaseD∩FSM4 68,2% (mining artifact) · Kaufman-ER OOF 63,5% (promissor, multiplicidade).

## 4. Supabase rows encontradas (MCP read-only: supabase_read_only_user, txn_read_only=on)
Busca por Fractal-MTF/htf_demand_retest/FaseD/FSM4/Kaufman/OOF/impulse:
| id8 | table | title | tags | apresenta como | ação |
|---|---|---|---|---|---|
| 334948c4 | memory_items | Router MURO + Kaufman ER | promissor-nao-validado | **suspeito/não-validado** (caveat no body) | SHOULD_NOT_GUIDE_DECISION |
| 39cd6480 | memory_items | Classificador FASE = artifact | mining-null, devils-advocate-matou | **inválido/artefato** (caveat no body) | SHOULD_NOT_GUIDE_DECISION |
| 654d71bc | memory_items | Fractal MTF htf_demand_retest | fractal-mtf, promissor-nao-validado | **promissor-não-validado** (mas SEM flag RAW-first) | MARK_SUSPECT + NEEDS_RERUN (delta futuro) |
| decisions / artifacts / source_registry | — | — | — | **0 hits** | — |

**Todas as 3 rows carregam caveat no body; NENHUMA se apresenta como conclusão confiável/aprovada. Zero em decisions/artifacts/source_registry.**

## 5. Memória / status contaminados?
- **MEMORY.md hot: NÃO** — termos críticos aparecem apenas no bloco "INCIDENT AUDIT" como CONGELADO/INVÁLIDO/artifact. Não há promoção como confiável.
- **Status master 04 / 05: NÃO** — 0 menções (grep=0).
- **Docs da semana:** aparecem em contexto de audit/estudo com caveats; o `XAU15M_TOTAL_STRUCTURAL_READING` descreve o fractal como "promissor-não-validado" (recomendado rebaixar a INVALID, não-urgente).

## 6. Correção necessária?
- **Nenhuma correção urgente/destrutiva.** A contenção está feita: memória hot + status limpos; Supabase só descritivo com caveat.
- **Recomendações (futuras, não-executadas):**
  1. Delta Supabase idempotente: 1 INSERT flag para `654d71bc` (SHOULD_NOT_GUIDE_DECISION + motivo RAW-first). NÃO delete/update.
  2. Editar `XAU15M_TOTAL_STRUCTURAL_READING`: fractal → INVALID(RAW-first).
  3. Rerun HTF demand retest sobre `htf_primitives/htf_{4H,1D}.primitives.json` (RAW nativo + OB detector), guard-PASS, antes de qualquer confiança.

## DECISÃO FINAL
**LOCALIZED_CONTAMINATION_CONTAINED** — contaminação localizada ao bloco Fractal-MTF, contida; Supabase/memória/status sem promoção de resultado suspeito como confiável. **Não precisa de audit expandido adicional.** Podemos voltar ao fluxo normal (com os 3 blocos congelados e o rerun HTF pendente).

Safety no fecho: BLOCKER=3 (naming `catalog_*` falso-positivo), WARNING=1, INFO=50 (report-only).
