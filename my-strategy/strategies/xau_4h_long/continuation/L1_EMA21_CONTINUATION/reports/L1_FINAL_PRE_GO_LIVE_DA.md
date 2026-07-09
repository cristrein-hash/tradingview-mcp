# L1 FINAL PRE-GO-LIVE — Devil's Advocate

**2026-07-09.** DA real (Agent tool) + leituras read-only + testes de fronteira. Verdict: **PASS_READY_FOR_EXPLICIT_GO_LIVE_DECISION.**

## Por secção
1. **Repo/safety — OK.** Diff tracked = só `runtime_xau.py` (+guard NAS) + `telegram_notify.py` (+env-gate); `capacity_journal.py` novo. `scanner.py` diff **vazio**. Baseline BLOCKER=3/W=1/INFO=50.
2. **Telegram hard-lock + escape — OK.** Todos os caminhos de envio passam por `send_telegram()` (único caller: `telegram_notify.py`). Gates env **antes** do send em: (a) runtime `notify()`; (b) `telegram_notify.py --send`; (c) `--test --send`. `L1_PRODUCTION_AUTHORIZED` não setado em repo/zshrc/zprofile/bash/env. Nenhum caminho chega a `urlopen` sem env=1. **Escape manual fechado.**
3. **Plist/cycle/cron — OK.** Cópias repo+deployada byte-idênticas, flag removida, `RunAtLoad=false`, não carregado, sem cron.
4. **NAS durability/startup — OK (caveat).** Guard `blocked_missing_nas_live_series` dispara com `nas_series` vazio, **antes** do alinhamento, só lê o snapshot (não toca chart). Caveat: a leitura live de durabilidade do DA apanhou o chart noutro símbolo/TF; o mecanismo está provado mas um dry-run live-XAU limpo com NAS presente não foi obtido nesta corrida (MCP hiccup → fail-closed).
5. **NAS SHIFT1 causal — OK.** Guard é early-exit puro; não mexe no `ledger_frozen`/cross-check/fail-closed.
6. **Ledger — OK.** `.runtime_state` sem modificação git; sem regressão 2017.
7. **Risk/capacity/journal — CONCERN → RESOLVIDO.** Código `capacity_journal.py` sound + fail-closed (11/11 PASS), honestamente NOT_WIRED (só o dry-run report o importa). **DA apanhou:** (i) `L1_RISK_CAPACITY_JOURNAL_RULES.md` não existia; (ii) o doc antigo (3 slots/1.0R) contradizia o código (2/€200/€100). **Corrigido nesta sessão:** escrito `L1_RISK_CAPACITY_JOURNAL_RULES.md` canónico (€-based, espelha o código) + antigo marcado **SUPERSEDED**. Ambiguidade eliminada.
8. **Broker safety — OK.** Única chamada de rede = `urlopen` do Telegram (duplo-gated). Sem caminho broker/order/execute. `journal.py` broker fields default None.
9. **Dry-run final — OK (caveat).** Tripwire notify+subprocess.run = zero. Nada enviado. Live XAU eval pulado por MCP hiccup → fail-closed. `would_send` payloads construídos (slot 1/2 e 2/2, €100/€200, `manual_approval_required`, `telegram_status=NOT_SENT_DRYRUN`) nunca transmitidos.
10. **Params protegidos — OK.** `scanner.py` diff vazio: 1.31/3.0/0.1, SL V1, +3R, entry, filtros intactos.

**Direção:** estritamente **mais DURO** (escape manual fechado + startup guard). Nada aproxima de disparo.

## Veredito final
**PASS_READY_FOR_EXPLICIT_GO_LIVE_DECISION.** Nenhum caminho de envio/broker/produção dispara sem **`L1_PRODUCTION_AUTHORIZED=1` E** ação humana deliberada (carregar plist / `--send-telegram`). Nenhum parâmetro protegido mudou. Sistema net-hardened. O CONCERN de documentação (rules doc divergente/em falta) foi **resolvido em sessão**.
**PRODUCTION STILL NOT AUTHORIZED — REQUIRES EXPLICIT CRIS GO-LIVE APPROVAL.**

## Passos exatos restantes para go-live (cada um = autorização explícita separada)
1. (feito) reconciliar rules doc ↔ `capacity_journal.py` ✅.
2. Obter um dry-run live-XAU/240 operacional limpo (NAS presente, sem MCP hiccup) — prova end-to-end read-only.
3. Cris seta `L1_PRODUCTION_AUTHORIZED=1`.
4. Re-adicionar `--send-telegram` ao plist (ou invocar com ele) + `launchctl load`.
5. Ligar o cycle. (Wiring da camada capacity/broker ao runtime = autorização futura separada; hoje NOT_WIRED.)
