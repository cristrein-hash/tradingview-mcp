# SUPABASE MEMORY — WAVE 2FINAL PRE-REVIEW (fecho da migração, 2026-07-02)

**Ficheiro:** `supabase/seeds/memory_cards_wave2final_seed.sql` · **Tag:** `seed:memory_cards_wave2final` · **Estado: CRIADO, NÃO APLICADO.**
**Gerador versionado:** `scripts/memory/generate_wave2final_seed.py` — com **reconciliação total embutida**: varre o diretório de memória, extrai os filenames migrados dos 4 geradores anteriores e **aborta** se este seed não fechar exatamente o remanescente. Impossível gerar o fecho com card faltando ou duplicado.

## 1. Reconciliação de contagem — 230/230 ✅ (correção do 229)

`disco=230 · migrados(2A/2B/2C/2C-b)=200 · restantes=30 · neste seed=30 → 200+30 = 230/230`

- **Por que 230 e não 229:** o inventário original (M1) contou 229 cards; durante o próprio bloco foi criado `project_supabase_memory_full_migration.md` (card do bloco ativo) → total real 230. Esse card já migrou na 2A.
- **A reconciliação embutida recuperou 2 cards esquecidos** das waves anteriores (1ª execução abortou, como desenhado): `project_external_factors_audit_roadmap` e `project_l2_bpt_sl_structural` — ambos classificados e incluídos (Grupo A2).

## 2. Lista completa dos 30 cards, classificação card-a-card

### Grupo A — project operacionais/config (12)
| Card | Status | Motivo |
|---|---|---|
| custom_ob_detector_v10 | **active** | ferramenta em uso (backbone L2 = RAW Custom OB) |
| receiver_broker_prefix_normalization | **active** | receiver VIVO comprovado pelo PRODUCTION_LOGIC_REAUDIT |
| telegram_silencer_observacao | **active** | config vigente do Telegram (vivo per Re-Audit) |
| tv_layouts_architecture | **active** | layouts aprovados em uso |
| watchlist_focus_5_plus_usousd | **active** | config vigente |
| replay_historical_base_multitf | **active** | base multi-TF existe e é usada |
| monitor_targets_leak | **dormant** | backlog #14 aberto sem trabalho ativo |
| pipeline_fase3 | **dormant** | crons fora do runtime vivo (Re-Audit: runtime estreito) |
| roadmap_post_xau_1h_v1 | **archived** | superseded pela ordem vigente |
| smc_eur_audit_v3 | **archived** | EUR fora do foco XAU-only |
| smc_xau_audit_v3 | **archived** | audit concluída/absorvida |
| tf_15m_long_liberated | **archived** | regra histórica do contexto D2R |

Nota: nenhum card marcado `active` de runtime sem comprovação no Re-Audit; nenhum marcado archived "só para fechar lote".

### Grupo A2 — históricos recuperados pela reconciliação (2)
| Card | Status | Motivo |
|---|---|---|
| external_factors_audit_roadmap | **superseded** | EF v1.2 substituído pelo EF v2 (card 2A ativo) |
| l2_bpt_sl_structural | **superseded** | substituído pelo SL_CONTEXT oficial (l2_bpt_sl_exit_approved, 2A) |

### Grupo B — legacy/formato antigo (16, revisão card a card)
| Card | Status | Motivo |
|---|---|---|
| feedback_cadence | **active** | regra comportamental operante (trabalho em camadas; sintetizada no PRINCIPAL_1) |
| feedback_memory_methodology | **active** (product) | protocolo de memória por sessão operante |
| feedback_partnership | **active** | parceria colaborativa ≠ automação — segue vigente |
| feedback_session_persistence | **active** (product) | persistência fim-de-sessão operante |
| feedback_statistical_patience | **active** (product) | canon estatístico vigente |
| feedback_trades_in_chat | **active** | preferência vigente do Cris (listas no chat) |
| project_execution_context | **active** | ainda verdadeiro: conta simulada, zero trades reais |
| project_d2r_state | **archived** | D2R substituído (Forward Outcome Layer) |
| project_operational_decisions | **archived** | snapshot 2026-05-13, superseded pelo status master |
| project_pending_work | **archived** | backlog datado maio/2026 |
| project_xau_losing_patterns | **archived** | finding n=7 histórico |
| reference_d2r_mechanics | **archived** | mecânica do legado D2R |
| project_external_factors | **superseded** | EF v1 → EF v2 |
| project_oracle_score | **deprecated** | DEACTIVATED 2026-05-21 |
| project_naming_proposal | **unknown_review** | proposta sem evidência de adoção — revisar com Cris |
| reference_files | **unknown_review** | mapa de navegação possivelmente stale pós-cleanups — revisar |

**Achado da revisão legacy:** os 16 cards "no-metadata" têm na verdade um campo `type:` parseável no formato antigo (gerador reportou 0 tipos inferidos por prefixo) — a distinção era de formato, não ausência; nenhum body precisou do fallback mínimo, todos têm description utilizável. Justificativas de `active` explícitas na tabela (regra especial cumprida).

## 3. Distribuição do seed

- **Rows:** 30, só `memory_items` · **Scope:** 27 private / 3 product (memory_methodology, session_persistence, statistical_patience — método genérico).
- **Status:** 13 active · 9 archived · 3 superseded · 2 dormant · 2 unknown_review · 1 deprecated.
- **Type:** 7 feedback · 21 project · 2 reference.

## 4. Verificações executadas (pré-apply)

- **Reconciliação 230/230** → OK (hard-abort embutido no gerador).
- Grep secrets → **0 hits** · Parse Postgres (sqlglot) → **OK** · 30/30 ids determinísticos + ON CONFLICT · rollback comentado por tag.
- Safety report → **BLOCKER=0 · WARNING=1 (só Caminho B TRUE_RISK) · INFO=50**.
- **Nada aplicado. Zero conexão de escrita.** Header do seed inclui a verificação pós-Run obrigatória (esperado 30).

## 5. Validação pós-apply (quando autorizada)

Esperado: memory_items total **240** (210 + 30) · tag wave2final = **30** · tags anteriores intactas (50×4) · scope: private 179 / product 61 · status: active 135 / archived 62 / dormant 24 / deprecated 12 / superseded 4 / paused 1 / unknown_review 2. **Migração de cards = 230/230 COMPLETA** após validação.

## 6. Critério de aceitação (pré-apply)

- [x] Seed criado (30 rows = remanescente real) · [x] Gerador versionado c/ reconciliação · [x] Review com classificação card-a-card e grupos A/A2/B separados · [x] Contagem reconciliada 230/230 (229 corrigido e explicado) · [x] Zero escrita Supabase · [x] Safety BLOCKER=0/WARNING=1 (Caminho B) · [x] Commit local, sem push sem autorização.
