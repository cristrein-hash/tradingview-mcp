# L1 PRODUCTION-GATE DRY-RUN — Devil's Advocate

**2026-07-09.** DA real (Agent tool, general-purpose) com leitura de código/plist/ledger + recomputação independente de bar-close e verificação do ledger. Verdict: **PASS** (com 2 correções de honestidade obrigatórias, incorporadas no relatório).

## §1 Telegram hard-lock — OK (+ 1 correção)
- `telegram_notify.py` envia só via `urllib` dentro de `send_telegram()`/`main()` gated por `--send`; **sem side-effect de import**. Alcançável do runtime **só** via `notify()` → `subprocess.run([python, telegram_notify.py])` (runtime_xau.py:311-313). Dry-run chama `evaluate()` direto; nunca `main()`/`notify()`.
- `runtime_xau.py` sem `os.system`/`requests`/`urllib`/`Popen`; único subprocess = o `.run` em `notify()`, tripwired. `scanner.py` sem superfície de envio.
- plist **NÃO carregado** (`launchctl list` vazio), `RunAtLoad=false`, log parou 23-jun. Nenhum `launchctl load` hoje.
- **CORREÇÃO #1:** o tripwire cobre `subprocess.run`, não `subprocess.Popen`. Um `Popen` correu = `server.js`/CDP (canal de LEITURA do `tv_read_adapter`), não Telegram. Reformular "subprocess surface zero" → "a via `subprocess.run` do Telegram ficou tripwired e nunca foi chamada".

## §2 NAS i-1 causality — OK
- Seed = valor da barra FECHADA `1783533600` (i-1), congelado/não-repaint = o que um ciclo anterior persistiria. Legítimo.
- Happy-path usa `ledger_frozen` (autoritário), não a série viva (runtime_xau.py:274). Correto.
- **Nota:** seed vindo da série viva faz o cross-check casar trivialmente → o demo não exercita `blocked_nas_shift1_ledger_mismatch` (já provado no wiring dry-run T5). Não mascara problema: o run primário (ledger real) fail-closed corretamente.

## §3 Bar-close — OK (recomputado independentemente)
- eval `1783548000` (22:00) fecha 02:00 → fechada (now≥close). forming `1783562400` (02:00) fecha 06:00 → não-fechada, excluída. prev `1783533600` (18:00) = i-1. Lógica `now>=t+14400` correta; nenhuma barra aberta entrou no gate.

## §4 Runtime safety — OK (+ 1 correção)
- **CORREÇÃO #2:** houve **1 append real** ao ledger (`.runtime_state/l1_feature_history.jsonl`, `1783548000`, `persisted_at 2026-07-09`, schema novo, guarded, **gitignored**). "Read-only" não é literal → "nenhuma produção tocada **além do append de captura autorizado**". Append-only, guard rejeita corrupção/conflito, não git-tracked.
- Temp-ledger restaurado (`finally` → real_fh); warm.jsonl não vazou. Sem strategy_rules/monitor/broker/production-log/dedup tocados.

## §5 Result interpretation — OK
- `blocked_missing_nas_shift1_ledger` = fail-close correto (i-1 confirmado ausente do ledger, gap desde Junho), não bug. `no_candidate/regime_d1_not_BULL` = estado plausível. `dry_run_pass=true` justificado no seu escopo (telegram-locked + fail-closed + happy-path wiring), **não** implica produção.

## §6 Closer-to-firing — OK
- Ledger 1 barra mais quente (`1783548000` = i-1 do próximo bar). Disparar ainda exige BULL (false) + gate + `main()`→`notify()` com `--send-telegram` (plist descarregado). **Nenhum caminho autónomo criado; gate humano intacto.**

## Veredito final
**PASS** com as 2 correções de honestidade acima. Sem via de Telegram/emissão (provado estrutural + tripwire), sem quebra de causalidade (i-1 congelado + fail-close correto no cold), bar-close correto, sem write de produção além do append de ledger autorizado. **Produção continua NOT_AUTHORIZED**; sistema 1 barra-de-warmup mais quente mas sem caminho autónomo de disparo.
