# L1 EMA21 4H LONG Continuation — FINAL PRE-GO-LIVE · RELATÓRIO

**Data:** 2026-07-09 · **Verdict:** **PASS_READY_FOR_EXPLICIT_GO_LIVE_DECISION** (DA PASS) · **Produção:** `NOT_AUTHORIZED`

Fecho dos controlos finais pré-go-live da L1, sem ativar produção.

## Estado estratégico
- XAU 4H LONG — L1 EMA21 Continuation · SL oficial **V1** (`zone_OB_low − 0.1ATR`) · Exit **+3R fixo** · NAS SHIFT1 `≥ 1.31` (**intactos**).
- NAS-live = RESOLVED-FOR-DRYRUN · Dry-run read-only = PASS · Pre-production closeout = PASS · **Final pre-go-live = PASS_READY_FOR_DECISION**.
- Commits: `4b58ac9` SL+exit · `d328b25` NAS remediation · `5c9e96a` dry-run · `4df7431` pre-production closeout · **(este bloco)** final pre-go-live.

## O que está fechado ✅
1. **Telegram triplo-hardening:** flag `--send-telegram` removida do plist (repo + deployado) **+** `runtime_xau.notify()` env-gate **+** `telegram_notify.py --send` env-gate (escape manual fechado). Envio real exige `L1_PRODUCTION_AUTHORIZED=1` (default OFF, unset em todo lado) **E** ação humana.
2. **NAS durability + startup fail-closed:** novo estado `blocked_missing_nas_live_series` se a série NAS live sumir (sem tocar chart, sem envio). Estudo NAS visível/computado (n_bars>0, distância + timestamps 4H).
3. **SHIFT1 causal + ledger:** i-1 = ledger congelado (`ledger_frozen`), cross-check live, fail-closed; guards 5/5 (2017/dup/símbolo/valid/missing).
4. **Risco/capacidade/journal:** `capacity_journal.py` (puro, fail-closed, **NÃO wired**) + doc canónico `L1_RISK_CAPACITY_JOURNAL_RULES.md` (antigo 3-slot SUPERSEDED). Audit 11/11 PASS.
5. **Dry-run final:** tripwire Telegram zero; `would_send` payload demonstrado (slot/risk/manual-approval) **nunca enviado**.

## O que segue PROIBIDO 🚫
Produção · Telegram operacional · broker · carregar plist/cycle/daemon/cron · enviar sinal · setar `L1_PRODUCTION_AUTHORIZED=1` · alterar estratégia/SL/exit/filtros/threshold.

## Regra de risco/capacidade (canónica, €-based)
max **2** posições · max **2** mesmo-símbolo · agregado **€200** · **€100**/posição · `fixed_equal` · duplicate-same-bar **BLOCK** · LONG-only sem hedge · broker **MANUAL_APPROVAL_ONLY** · auto-broker **NOT_AUTHORIZED_YET**.

## Como será o go-live futuro (SE o Cris autorizar) — checklist exato
1. Confirmar **safety** baseline limpo.
2. Confirmar **NAS visível/computado** no chart XAU 4H (n_bars>0, distância).
3. Confirmar **ledger com i-1** (barra anterior fechada presente; senão fail-closed até aquecer).
4. Confirmar **risk slots** (≤2 abertas, agregado ≤€200) via `capacity_journal`.
5. **Cris seta `L1_PRODUCTION_AUTHORIZED=1`** (autorização explícita).
6. **Carregar plist** (`launchctl load`) — re-adicionar `--send-telegram` se desejar envio.
7. **Ligar cycle**.
8. **Primeiro alerta Telegram = apenas human-review** (não é ordem; entrada 100% humana).
9. **Broker = manual** (aprovação humana; sem automação).

## Confirmação negativa
Telegram **não emitido** · broker **não tocado** · cycle/daemon/cron **não ligado** · strategy_rules/monitor **não alterados** · **nenhum sinal operacional emitido** · scanner intacto (1.31/3.0/0.1) · chart não plotado/desenhado/screenshot.

**PRODUCTION STILL NOT AUTHORIZED — REQUIRES EXPLICIT CRIS GO-LIVE APPROVAL.**
