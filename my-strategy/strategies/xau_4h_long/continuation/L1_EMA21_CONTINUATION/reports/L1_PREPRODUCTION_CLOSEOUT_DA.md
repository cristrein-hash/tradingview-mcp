# L1 PRE-PRODUCTION CLOSEOUT — Devil's Advocate

**2026-07-09.** DA real (Agent tool, general-purpose) + correção aplicada em resposta. Verdict: **PASS_READY_FOR_PRODUCTION_DECISION** (produção continua NÃO autorizada).

## 1. Repo/safety — OK
HEAD `5c9e96a`; diff tracked = só `plist` + `runtime_xau.py` (+import os, `_production_authorized`, gate). `scanner.py` diff vazio; threshold `NAS_DIST_SHIFT1_MIN=1.31`, SL, exit, entry, filters, monitor, broker, strategy_rules **intactos**.

## 2. Telegram hard-lock — OK (após correção do DA)
- **Env-gate de código airtight** para o caminho daemon/cycle: `notify()` bloqueia (`PRODUCTION_NOT_AUTHORIZED`) **antes** do `subprocess.run(telegram_notify.py)` se `L1_PRODUCTION_AUTHORIZED!=1`. Propagação `run_l1_cycle → runtime → notify(send=True)` traçada; env **não está setado em lado nenhum** (repo/zshrc/zprofile/env). Tripwire: `send=True`+no-env → subprocess NÃO chamado.
- **🚨 FLAW do DA (corrigido nesta sessão):** a neutralização inicial tocou só a **cópia do repo**; o launchd lê `~/Library/LaunchAgents/...` e essa cópia deployada **ainda tinha `--send-telegram`**. → **Corrigido:** sincronizei a versão neutralizada por cima da deployada (backup `.pre_hardlock_bak`). Audit agora confirma `repo_plist_active_send_flag=false` **E** `deployed_plist_active_send_flag=false`. **Agora são 2 locks reais** (flag removida de ambas as cópias + env-gate).
- **Escape hatch manual conhecido (por design):** `telegram_notify.py --send` com um candidato JSON envia direto (não passa por `notify()`). É uma ferramenta manual humana, não um caminho de daemon acidental; documentado como decisão futura (env-gate no próprio sender, se desejado).

## 3. Plist/cycle/daemon/cron — OK
Não carregada (`launchctl list` vazio); sem cron; `RunAtLoad=false`; XML válido (`plutil -lint OK`) em ambas as cópias. Editar não a tornou perigosa. Backup `.pre_hardlock_bak` da versão antiga existe (não lido pelo launchd; requer ação deliberada para restaurar).

## 4. NAS visibility — CONCERN (frágil, mas fail-safe)
`visible=true`, `n_bars=8`, distância + timestamps 4H. **Durabilidade é escopo-de-layout, não durável:** reload de layout pode largar o estudo. Se reverter → série vazia → SHIFT1 sem i-1 → `blocked_missing_nas_shift1_ledger` (fail-closed). **Revert NÃO causa disparo falso**, só torna o caminho live silencioso. Go-live blocker: tornar durável.

## 5. SHIFT1 causal + fail-closed — OK
Guards 5/5 (2017 write+read, dup conflitante, símbolo errado, valid, missing→None). Dry-run final `blocked_missing_nas_shift1_ledger` (operational=false, forming excluído, bar fechado) = estado correto + fail-closed. Tripwire Telegram zero. Sem look-ahead; leitura i-1-only = causal.

## 6. Capacity/risk — OK (rotulado honestamente)
`FROZEN_PROPOSAL_NOT_WIRED`. `journal.py` mantém camadas de execução como futuras (default NONE); broker "camada futura". Sem enforcement wired. Nit cosmético: doc diz `--execution-layer`, flag real é `--execution-mode` (substância correta).

## 7. Production readiness — PASS para DECISÃO, não go-live
Disparo acidental impossível no estado atual (plists sem flag + env unset + gate antes do subprocess + SHIFT1 fail-closed). **Blockers restantes para go-live real:**
1. NAS SHIFT1 durável (independente da visibilidade do layout).
2. Decidir se `telegram_notify.py --send` deve ser env-gated (fechar o escape manual).
3. Broker/capacity enforcement = não construído (correto) — exige camada de execução/risco + autorização separada.
4. (feito nesta sessão) reconciliar a cópia deployada do plist — ✅.

## 8. Scope — OK
Nenhum parâmetro protegido mudou. Só mudanças aditivas (env-gate + import + comentário/flag no plist). **Net = mais DURO** (novo interlock que não existia; nada tornado carregável/perigoso).

## Veredito final
**PASS_READY_FOR_PRODUCTION_DECISION.** Nenhum caminho de Telegram/broker/produção dispara de uma ação acidental; nenhum parâmetro protegido mudou. O gap do DA (cópia deployada do plist) foi **corrigido em sessão** → 2 locks reais + fail-closed.
**PRODUCTION STILL NOT AUTHORIZED — REQUIRES EXPLICIT CRIS GO-LIVE APPROVAL.** `L1_PRODUCTION_AUTHORIZED` unset everywhere; daemon não carregado; todo caminho live avaliado = não-operacional/fail-closed.
