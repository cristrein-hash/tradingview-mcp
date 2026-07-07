# INCIDENT — Supabase Rows Audit (last week)

**Via MCP READ-ONLY** (confirmado: `current_user=supabase_read_only_user`, `transaction_read_only=on`, `default_read_only=on`). **Zero INSERT/UPDATE/DELETE.** Projeto DEV `vgfofofozptrtjvtuyzy`.

## Contagem por tabela (todas as rows são "recentes" porque a migração total foi 2026-07-02, <10 dias)
| tabela | total | notas |
|---|---|---|
| memory_items | **281** | 230 da migração (2026-07-02) + deltas W1/2026-07-04/2026-07-07 |
| decisions | 8 | todas CORE arquiteturais, aprovadas Cris |
| artifacts | 12 | migração |
| source_registry | 7 | RAW root = source_of_truth |
| agent_runs | 6 | migração |
| safety_reports | 1 | migração |
| retrieval_queries | 0 | — |

## memory_items desta sessão (2026-07-07) — as que poderiam promover resultado suspeito
| id8 | title (curto) | categoria | status | tem nº | claim estratégica | provisório |
|---|---|---|---|---|---|---|
| 7a81fec7 | Assimilação PLT/DM escada markup | project | active | sim | não (achado metodológico) | **VERIFIED_DERIVED** |
| 423fef5e | PLT/DM = caminhada sequencial (refutação) | project | active | sim | não (refutação) | **VERIFIED_DERIVED** |
| 3ef136c3 | Engine entry 3R MASTER = melhor entry 15M | project | active | sim | sim (54,2%/reclaim-R 61,4%) | **VERIFIED_DERIVED** (número reproduz; "melhor" = descritivo, não aprovação) |
| 21dff298 | Leitura visual 96 entries validada | project | active | sim | contexto (não número de estratégia) | **VERIFIED_DERIVED / INDEX** |
| 5fcdc7b6 | Vencer-muro = LOOKAHEAD apanhado | project | active | sim | não (lição; auto-refutação) | **VERIFIED / INDEX** |
| 48644c04 | REGRA DURA causalidade pré-condição | feedback | active | sim | não (regra de comportamento) | **VERIFIED / INDEX** |
| 334948c4 | Motor multi-agente: router MURO + Kaufman ER | project | active | sim | **sim (ER OOF 63,5%)** | **PROMISING_NOT_VALIDATED / SHOULD_NOT_GUIDE_DECISION** |
| 39cd6480 | Classificador FASE = MATO pelo DA (artifact) | project | active | sim | **sim (FaseD∩FSM4 68,2%)** — mas descrito como ARTEFATO | **SHOULD_NOT_GUIDE_DECISION** (já marcado artifact na própria row) |
| 654d71bc | **Fractal MTF htf_demand_retest (vindica Cris)** | project | active | sim | **sim (OOF 0,647)** — descrito "promissor-não-validado" | **SUSPECT → SHOULD_NOT_GUIDE_DECISION** (audit rebaixa a INVALID por violação RAW-first; row não tem esse flag ainda) |

## Achado central Supabase
- **Nenhuma row PROMOVE um resultado suspeito como validado/aprovado.** Todas carregam o caveat correto (mining artifact / lookahead apanhado / promissor-não-validado / muro). São INDEX/descritivas, não decisões.
- **Nenhuma row em `decisions` aprova estratégia/resultado suspeito** — as 8 são CORE arquiteturais (memória, boundary, no-auto-trading, EF v2, safety, migração), aprovadas por Cris pré-sessão.
- **1 row precisa correção futura:** `654d71bc` (fractal) diz "vindica Cris / promissor-não-validado" — o audit adiciona que é **INVALID por fonte (RAW-first violation)**. Como não se escreve Supabase agora, isto vai para **delta corretivo futuro** (não delete; INSERT de flag SHOULD_NOT_GUIDE + motivo).
