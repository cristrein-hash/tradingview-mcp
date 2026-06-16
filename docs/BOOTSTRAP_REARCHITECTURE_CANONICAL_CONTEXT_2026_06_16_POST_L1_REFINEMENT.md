# BOOTSTRAP — CONTEXTO CANÔNICO PÓS-REFINAMENTO L1 (2026-06-16)

**Gerado:** 2026-06-16 · **Tipo:** snapshot canônico read-only pós-compactação · **NOT_VALIDATION.**
**Verificado contra:** repo (git log/status, código-fonte), `launchctl list`, receiver `/health`, public `/health`, processos vivos.
**Natureza:** estado canônico. Onde docs divergem do sistema real, **a verdade é sistema + git** (ver §10/§DIVERGÊNCIAS).
**Relação com o doc anterior:** complementa/supersede pontualmente `docs/BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md` (commit 400b30e), cujo §0 está **desatualizado** (ver Divergência D2). Não sobrescrevi o anterior por segurança.

---

## 1. Executive summary

O TRADING SYSTEM está numa nova arquitetura **human-in-the-loop**: TradingView/Pine = camada visual/indicadores; MCP = leitura controlada do chart; **Python = autoridade da estratégia**; Telegram = apenas *candidate notification*; **humano decide a entrada**; journal/outcome = auditoria; **broker e MCP trade-management INATIVOS**.

A única estratégia operacional é **XAU 4H LONG — CONTINUATION / L1 EMA21 CONTINUATION** (PEPPERSTONE:XAUUSD, 4H, LONG), com a **config refinada aprovada 2026-06-16** (stack anti-extensão + NAS SHIFT1≥1.31 + RSI exhaustion gate + SL estrutural + target +3R). Aprovada **sem OOS, risco assumido pelo Cris** → é *governance / user-approved working config*, **não** validação de edge.

Estado operacional **íntegro e confirmado** nesta sessão: receiver OK (PID 841), cloudflared vivo (PID 1033), public health 200, **pause flag presente**, `xau-l1-cycle` carregado, weekly-review decomissionado, broker inativo, enrich/D2R dormant.

O deep dive do **Caminho A L1 v1 F4+F5** (commit 5a3aae9) concluiu **`SUPERSEDED_BY_L1 / KEEP_REFERENCE`** — arquivar, não reabrir. Próxima frente provável: **L1 OOS** ou **Caminho B bottom-catcher (P0)**, conforme decisão do Cris.

**Divergências encontradas (todas não-bloqueantes):** ver §DIVERGÊNCIAS no fim. Nenhuma invalida a config ou a produção.

---

## 2. Estado operacional atual (confirmado 2026-06-16, read-only)

| Componente | Estado | Evidência |
|---|---|---|
| Arquitetura | TV/Pine → MCP (read) → **Python autoridade** → Telegram candidate → humano decide → journal/outcome | §3 docs L1 |
| Estratégia ativa | **L1 EMA21 CONTINUATION** (XAUUSD 4H LONG) | STRATEGY.md / scanner.py |
| XAU_240 | **ATIVO** (scheduler `xau-l1-cycle` com `--manage-chart`) | launchctl + run_l1_cycle.py |
| XAU_60 / XAU_15 | **reservados, INATIVOS, sem Telegram** | tv_read_adapter ALLOWED_TF |
| Receiver | **OK** PID 841, `claude_recheck:true`, `secret_configured:true` | `/health` |
| Pause flag | **PRESENTE** (`pause_flag_present: true`) | `/health` runtime |
| cloudflared | **VIVO** PID 1033 (`tunnel run tradingview-webhook`) | pgrep |
| Public ingress | **200** (`webhook.tdwclaudestrategy.org/health`) | curl |
| weekly-review | **DECOMISSIONADO** (commit e1fdaf1) | git log + launchctl (ausente) |
| `archive-weekly` | carregado, **distinto** do weekly-review (não é o decomissionado) | launchctl |
| Broker | **INATIVO** | arquitetura / sem agente |
| MCP trade-management | **INATIVO** | arquitetura |
| Event store | **vivo** (indicator_signals last_mod 2026-06-16, dedup index 16774) | `/health` logs |
| Enrich / D2R / OUTCOME EVALUATOR | **DORMANT** (0 processos) | pgrep |
| Telegram no bootstrap | **NÃO enviado** (este bloco é read-only) | — |

⚠️ **Atenção operacional (não-bloqueante):** há **1 processo `src/server.js` (PID 7043)** vivo — possível MCP órfão (enrich/coleta estão dormant; não deveria haver server.js residual). **Não matei** (read-only / minimum-safe / sem autorização). Recomendo `incident-response` num bloco futuro se persistir. Não afeta receiver/cloudflared/pause/L1.

---

## 3. Config L1 refinada atual (APROVADA 2026-06-16 — verificada contra `scanner.py`)

Base rule (close-only-causal, SHIFT1 onde repinta): regime **BULL D-1 via `regime_l1_v4`** + `close>EMA21>SMA50` + slopes EMA21/SMA50 positivos + **BOS causal** + toque zona **Custom OB v11** + `body_pct≥0.35` + **F5 `vol_ratio_med50≤1.0`**.

Camadas refinadas (**constantes confirmadas em `scanner.py`**):

| Filtro | Threshold | Constante (scanner.py) |
|---|---|---|
| Anti-extensão ret5 | `ret5 ≤ 1.42%` | `RET5_MAX = 0.0142` ✓ |
| Extensão da EMA | `ext_ema ≤ 2.95·ATR` | `EXT_EMA_ATR_MAX = 2.95` ✓ |
| Largura da zona | `zone_w ≥ 0.6·ATR` | `ZONE_W_ATR_MIN = 0.6` ✓ |
| Distância à zona | `dist_zone ≤ 1.81·ATR` | `DIST_ZONE_ATR_MAX = 1.81` ✓ |
| NAS (SHIFT1) | `NAS_DISTANCE(i-1) ≥ 1.31` | `NAS_DIST_SHIFT1_MIN = 1.31` ✓ |
| RSI exhaustion **gate** | `round(rsi_vs_ma,2) ≤ −9.35` → `blocked_exhaustion` | `RSI_VS_MA_THR = -9.35` ✓ |
| SL estrutural | `max(zone_OB_low, swing6_low) − 0.1·ATR` | `SWING_N=6`, `SL_ATR_BUFFER=0.1` ✓ |
| Target | `+3R` | `TARGET_R = 3.0` ✓ |

**Proibições confirmadas:** `vol_entry_z` **removido/proibido** (morto sob F5 + derivado de matriz bugada); `regime_B_v3` **proibido como autoridade live** (REMOVIDO do caminho L1 — confirmado no header e import do `scanner.py`).

**Resultado aprovado (governance, in-sample, risco assumido, NÃO OOS):** estudo cenário C = 34 trades, WR 53%, +41.0R, PF 3.74, 5/5 monumentais preservados. Realização fiel no full-scan do scanner: **31 operacionais / 17 TARGET / 13 STOP / 1 TIME / +40.0R / PF 4.08 / 5/5 monumentais** (difere por 3 RSI-exhaustion-blocked que o gate corretamente exclui). **Isto é working config user-approved, não prova de edge** (`NOT_VALIDATED_OOS`).

---

## 4. Runtime / MCP / study-values (confirmado)

- **scanner = runtime quanto aos gates:** `runtime_xau.py` faz `import scanner` e chama **`scanner.evaluate`** (autoridade única). Constantes/SL/filtros não são duplicados.
- **Regime unificado:** ambos importam `latest_state_before` de `regime_l1_v4` (mesma função). `regime_B_v3` fora do caminho L1.
- **`data_get_study_values_at_bar`** existe (`src/tools/data.js` + `src/core/data.js`, commit fdfab30) — lê `study.data().valueAt(barIndex)` (slot 0 = time, slots 1+ = plots). **Alinhamento por TIMESTAMP, não índice** (`align_study_values(eval_t, prev_t, …)` no runtime).
- **Bar fechado:** runtime seleciona o **último bar fechado** (`now ≥ bar_time + TF_SEC`); **forming bar rejeitado** → `blocked_bar_not_closed`. NAS eval e NAS SHIFT1 vêm de bars fechados; RSI eval do eval_bar fechado.
- **Estados de bloqueio:** `blocked_bar_not_closed`, `blocked_missing_closed_bar_study_values`, `blocked_missing_nas_shift1`, `blocked_missing_base_rule_live_fields`, `blocked_exhaustion`, `no_candidate`, `operational_candidate`. Se alinhamento falhar → bloqueia com estado claro **e sem Telegram**.
- **Scheduler (`run_l1_cycle.py`):** `--manage-chart` (captura chart → troca p/ PEPPERSTONE:XAUUSD/240 via `_MCP`/`src/server.js` → roda → **restaura** o chart anterior; `--leave-chart-240` deixa em 240). `--send-telegram` só envia em `operational_candidate`. Default = DRY-RUN sem Telegram.
- **Status live honesto:** runtime ainda **PARCIAL** — base-rule estrutural live não totalmente confirmada e timing do snapshot pode trazer bar em formação; o **scanner é o gate autoritativo** até a base-rule live fechar (bloco futuro). Nenhum Telegram silencioso.

---

## 5. Legacies e arquivos proibidos (hard)

- **`regime_B_v3` como autoridade live:** PROIBIDO. Histórico estático recuperável só p/ backtest; **não forward-computável** (gerador v1 perdido), bias ~10.68% sem SHIFT1. `DO_NOT_REOPEN (live)`.
- **`vol_entry_z`:** PROIBIDO reintroduzir (morto + matriz bugada).
- **SLIM features como validação:** PROIBIDO (`feedback_never_use_slim_features`). Sempre RAW.
- **Catalog enganoso:** `XAUUSD_4H_BREAKOUT_CONTINUATION` marcado ACTIVE_CANDIDATE no catalog é **rótulo legacy enganoso** (não deployado; recheck:931 neutralizado) — `CONTAMINATED_LEGACY / KEEP_REFERENCE`.
- **Recheck/Telegram legacy** dos pacotes antigos: não reativar.
- **RAW / event store / source-of-truth / `indicator_signals.jsonl`:** não tocar/mover/deletar.
- **Generated state gitignored:** `regime_l1_v4_classifications.jsonl` (561KB) e `xau_daily_l1v4.jsonl` confirmados **git-ignored** (GENERATED_LIVE_STATE). Não versionar.

---

## 6. Estratégias XAU 4H resgatadas (inventário mestre)

Fonte: `docs/XAU_4H_STRATEGY_RESCUE_MASTER_INVENTORY.md`. Resumo de status:

- **L1 EMA21 CONTINUATION** → `ACTIVE_OPERATIONAL_CURRENT` (in-sample, NEEDS_RAW_BACKTEST OOS).
- **Continuation rebuild_v1/v2/v3 (EMA21_A+F5)** → `SUPERSEDED_BY_L1 / KEEP_REFERENCE`.
- **Caminho A L1 v1 F4+F5** → `SUPERSEDED_BY_L1 / KEEP_REFERENCE` (§7).
- **XAUUSD_4H_BREAKOUT_CONTINUATION** → `CONTAMINATED_LEGACY / KEEP_REFERENCE` (rótulo a corrigir; possível L2 breakout futura).
- **Caminho A A1 BALANCE / A1' SUPERTREND** → `KEEP_REFERENCE` (família com look-ahead conhecido).
- **XAU_4H_REVERSAL (capitulation / discretionary / v1_4g_rws_a6/a7)** → candidatos/KEEP_REFERENCE.
- **regime_B_v3** → `KEEP_REFERENCE (histórico) / DO_NOT_REOPEN (live)`.
- **1H packets** → `KEEP_REFERENCE (não-4H)`.

Prioridades: **Caminho B bottom-catcher = P0** para próxima reanálise estrutural; demais P1/P2. F4+F5 saiu da fila (absorvido).

---

## 7. Status Caminho A L1 v1 F4+F5

Deep dive concluído em **`docs/XAU_4H_CAMINHO_A_L1_F4_F5_DEEP_DIVE.md` (commit 5a3aae9)**:

- **F4 era INERTE:** `sell ≤ 7` nunca cortou nenhum trade (max=0 sob mapping correto). Hipótese real = **EMA21_A + F5 (volume calmo)**.
- **Reconciliação 11/16/38 NUNCA fechou** — config original perdida/auto-inconsistente.
- **`R_CEIL 1.5ATR` abortava 35/38 candidatos** (risco mediano 2.28 ATR); removê-lo foi o **conserto real** no rebuild_v3 (não era o cooldown — refutado empiricamente).
- **KEEP-19 +32.6R = artefato in-sample / hindsight humano** (`NOT_VALIDATION`, `mechanizable_now=false`).
- **L1 refinada é superset estrita:** nada operável em F4+F5 que a L1 não cubra.
- **Decisão:** arquivar / keep reference, **NÃO reabrir como estratégia**. Memória atualizada.

---

## 8. XAU 15M BB+NAS Leonardo — PAUSADO

- Estudo BB+NAS feito; PDF winners/losers analisado; CSV manual estruturado criado (`docs/XAU_15M_BB_NAS_LEONARDO_WORKFLOW_PROPOSAL.md` + `_QUESTIONS.md`, commits 34a29a8/b46f24f).
- **Aguardando respostas do Leonardo.** **NÃO avançar 15M** até as respostas, salvo autorização explícita do Cris.

---

## 9. Forward Outcome Layer

- **Fase 1 `report_forward_quality`** implementada (commit 1150f3a).
- **Fase 2 `match_candidates`** implementada (commit 6d5c651); candidate_timestamp persistido (fb4671d).
- **Event store** limpo, útil como forward data. **Live signals validam comportamento OPERACIONAL, não edge.**
- Forward Outcome Layer **não envia Telegram nem toca broker**.

---

## 10. Hard stops (invioláveis neste e nos próximos blocos)

1. Read-only por padrão; só o doc de bootstrap é escrito neste bloco.
2. Não alterar código / runtime / scheduler / catalog / registry.
3. Não enviar Telegram. Não tocar broker. Não tocar RAW / event store / source-of-truth.
4. Não reativar `regime_B_v3` live; não reintroduzir `vol_entry_z`; não usar SLIM como validação.
5. Não reabrir F4+F5 como estratégia.
6. MCP/chart só health/read estritamente necessário — nunca dirigir trade nem trocar símbolo fora do `--manage-chart` autorizado do scheduler.
7. Não remover pause flag. Não matar processos sem autorização (inclui o server.js órfão observado).
8. Qualquer mismatch scanner/runtime/backtest/manifest **invalida os números até rederivação**.
9. Config L1 = **user-approved working config (não OOS)**; nunca apresentar como edge validado.
10. Mensagem de candidate **nunca** é ordem, entrada aprovada, trade validado ou recomendação direta.

---

## 11. Verificações pós-compactação (executadas nesta sessão)

- [x] receiver `/health` OK (PID 841, recheck/secret true, **pause presente**)
- [x] cloudflared vivo (PID 1033) + public `/health` 200
- [x] `xau-l1-cycle` carregado; weekly-review ausente (decomissionado e1fdaf1)
- [x] enrich / D2R / OUTCOME EVALUATOR dormant (0 processos)
- [x] broker inativo; MCP trade-management inativo
- [x] event store vivo (indicator_signals 2026-06-16)
- [x] git limpo (exceto `alert-bridge/logs/` untracked)
- [x] scanner.py constantes == config refinada declarada (8/8 ✓)
- [x] scanner usa `regime_l1_v4`; `regime_B_v3` removido do caminho L1
- [x] runtime reusa `scanner.evaluate`; alinhamento por timestamp; forming bar rejeitado
- [x] `data_get_study_values_at_bar` presente (valueAt)
- [x] generated jsonl de regime git-ignored
- [x] todos os 41 arquivos obrigatórios presentes
- [⚠] server.js PID 7043 vivo — possível órfão (reportado, não tocado)

---

## DIVERGÊNCIAS encontradas (todas não-bloqueantes)

- **D1 — paths do prompt:** `research/revalidation/` e `candidates/` (top-level) **não existem**; os paths canônicos são `my-strategy/research/revalidation/` e `my-strategy/strategies/candidates/`. Cosmético.
- **D2 — bootstrap anterior §0 desatualizado:** `BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md` (commit 400b30e) diz que os docs de autoridade (`00_*`…`10_*`, `SKILL_*`) vivem **fora do repo** (`~/Desktop/...`). **Realidade atual:** estão **versionados no repo** em `docs/project_authority/` (commit dd69839 "Version project authority docs and skills"). Este doc supersede essa afirmação. (Recomendo, em bloco futuro autorizado, atualizar o §0 do doc antigo.)
- **D3 — docstring stale:** `run_l1_cycle.py` linha 13 referencia `tv_read_adapter.MCPClient`; a classe real é **`_MCP`** (linhas 70-71 usam `_MCP` corretamente). Apenas comentário desatualizado, **sem impacto funcional**.
- **D4 — server.js órfão:** PID 7043 vivo sem coleta/enrich ativos. Não tocado (read-only). Candidato a limpeza via `incident-response` se persistir.

Nenhuma divergência altera a config L1, o estado de produção, ou os status de estratégia.

---

*Documento read-only. Nenhum código/runtime/scheduler/catalog/RAW/event-store/broker tocado; nenhum Telegram enviado; MCP não dirigido (apenas health/read via curl/launchctl/pgrep e leitura estática de arquivos).*
