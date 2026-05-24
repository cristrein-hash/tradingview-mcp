# Deployment Checklist — pré e pós deploy

Checklist operacional pra qualquer mudança que toque produção (estratégia nova, Pine atualizado, template alterado, receiver patch). **Copy-paste antes de cada deploy.** Cada item é hard requirement, não opcional.

Ver `STRATEGY_DEPLOYMENT_PIPELINE.md` pra contexto e gates de promoção.

---

## A. Pine Script checklist (estratégia nova ou alteração)

- [ ] Nome único do indicator (`indicator("...")`) — sem colidir com Pine existente (`pine_list_scripts` pra confirmar)
- [ ] `@version=5` ou superior
- [ ] `barstate.isconfirmed` ou `alert.freq_once_per_bar_close` (evita disparo em candle aberto)
- [ ] `ts_signal` via `str.format_time(time, "yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC")` no payload
- [ ] `alert_type` único no projeto (não colide com outros Pines/templates)
- [ ] `strategy_module` único e versionado (`<ASSET>_<TF>_<DIR>_<SHORT>_<VERSION>`)
- [ ] `symbol` via `syminfo.tickerid` (não hardcoded)
- [ ] `timeframe` via `timeframe.period`
- [ ] `price` ou `entry_price` presente (snapshot do momento do trigger)
- [ ] `r_sanity_pass` check: `r_points > 0 and r_points <= 5*atr14`
- [ ] `reason` descritivo (vai pro Telegram)
- [ ] `priority` definido (A/B/C)
- [ ] Compila sem erro: `pine_smart_compile` → 0 errors
- [ ] Save: `pine_save`
- [ ] Confirmar único slot no servidor TV (sem duplicate por substring de nome — bug session 2026-05-18)

---

## B. Template JSON checklist (alerta externo, não-Pine)

- [ ] JSON válido: `python3 -c "import json; json.load(open('template.json'))"` passa
- [ ] Campos obrigatórios presentes: `symbol`, `base_symbol`, `timeframe`, `alert_type`, `ts_signal`, `price`, `indicator_name`, `signal_type`
- [ ] Placeholders TV corretos: `{{ticker}}`, `{{interval}}`, `{{time}}`, `{{close}}`
- [ ] **Sem texto antes ou depois do JSON** (causou 3 alertas corrompidos session 2026-05-24)
- [ ] `ts_signal: "{{time}}"` literal (sem espaço extra, sem aspas extras)
- [ ] `indicator_version` bumped se houver mudança comportamental
- [ ] Path do template registrado no Candidate Packet

---

## C. Alerta TradingView checklist (criar/editar via UI)

- [ ] Symbol correto (broker prefix incluso: `PEPPERSTONE:XAUUSD`)
- [ ] Timeframe correto (15m, 30m, 1h, 4h, 1D)
- [ ] Condition: indicator + signal certos (não confundir com indicator de mesmo nome de outro Pine)
- [ ] **Frequency: Once per bar close** (não "once per bar")
- [ ] Webhook URL: `/webhook/<SECRET>` (NÃO `/webhook/local-test` — esse retorna 403 pós-cutover)
- [ ] Message: template colado SEM texto extra antes/depois (validar via clipboard `pbpaste | head -c 200`)
- [ ] Expiration ≥ 1 mês
- [ ] **Após salvar:** disparar teste manual (botão "Notify"); confirmar evento em `tradingview_alerts.jsonl` com `path: "/webhook/<SECRET_REDACTED>"`
- [ ] Validar via MCP `alert_list` que o alerta novo aparece e parsing OK (sem `payload_keys=[]` indicando JSON quebrado)

---

## D. Pre-deploy validations (antes de qualquer commit/restart)

### D1. Git hygiene
- [ ] `git status --short` — sem arquivo inesperado staged
- [ ] `git diff --check` — sem whitespace error
- [ ] Secret scan: `grep -rF "$SECRET" <staged_files>` → 0 ocorrências
- [ ] Nada de `.env`, `.bak`, `.log`, `.jsonl`, `logs/` staged
- [ ] Commit message no formato `<verb-imperativo> <escopo>`
- [ ] Co-author: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`

### D2. Receiver health (se for restartar)
- [ ] `/health` retorna `ok:true`, `claude_recheck:true`, `secret_configured:true`, `legacy_endpoint_enabled:false`
- [ ] `launchctl print gui/$(id -u)/com.cristrein.tv-webhook-receiver` → state=running, last exit = never
- [ ] `wc -c logs/launchd_tv_receiver_stderr.log` → 0 bytes (ou sem traceback recente)
- [ ] `schema_warnings_recent_count_24h` no health não está em spike (>50 = alerta)

### D3. Pre-Change Discipline (CLAUDE.md raiz)
Antes de mudança em receiver/template/Pine/prompt operacional:
1. [ ] Que INPUT a mudança opera? (alert_type específico, canal, etc.)
2. [ ] Esse input está vivo nos últimos 7 dias? (validar com grep/wc no log)
3. [ ] Quantos eventos/dia chegam pelo canal? (últ 24-48h)
4. [ ] Se <5 events/dia OU canal dormente: **STOP**. Pode estar mexendo em dead infrastructure.

### D4. Mudanças arquiteturais
Se a mudança toca **prompt operacional, schema de logs, routing webhook, dedup, ou pipeline lógica**:
- [ ] Invocar `Plan agent` (`subagent_type=Plan`) ANTES de escrever código
- [ ] NÃO fast-fix mode

---

## E. Restart checklist

**Opção 1 — via wrapper (manual, dev local):**
```bash
cd ~/tradingview-mcp/alert-bridge
./start_receiver.sh
```
Espera:
- `OK: TV_WEBHOOK_SECRET set (length=43)` ou similar
- `Archived: ...` (logs rotacionados se houver)
- `Receiver started: PID=<n>`
- `Health: {"ok": true, ...}`
- `stderr size: 0 bytes`

**Opção 2 — via LaunchAgent (produção):**
```bash
launchctl kickstart -k gui/$(id -u)/com.cristrein.tv-webhook-receiver
sleep 3
```

**NUNCA fazer:**
```bash
python3 tv_webhook_receiver.py             # ❌ SECRET cai pro default
nohup python3 -u tv_webhook_receiver.py &  # ❌ idem
```

---

## F. Post-deploy validation

### F1. Smoke test (10 minutos pós-restart)
- [ ] `curl http://127.0.0.1:8787/health` → `ok:true`
- [ ] Endpoint novo retorna 200: teste com payload mínimo via script Python local (sem expor secret no shell)
- [ ] `/webhook/local-test` retorna 403
- [ ] Endpoint inválido retorna 403
- [ ] `tail logs/tradingview_alerts.jsonl` mostra evento de teste com path sanitizado
- [ ] `wc -c logs/launchd_tv_receiver_stderr.log` → 0 bytes

### F2. Secret scan pós-deploy
```bash
SECRET=$(grep '^TV_WEBHOOK_SECRET=' .env | cut -d= -f2 | tr -d '"'"'")
grep -rF "$SECRET" logs/ | wc -l
```
- [ ] Retorna 0

### F3. Validação via MCP (estratégia nova)
- [ ] `mcp__tradingview__alert_list` → alert novo aparece, `message` parseia como JSON, `signal_type` esperado
- [ ] Disparar 1 alerta de teste real (botão "Notify" no TV) e confirmar:
  - Evento em `tradingview_alerts.jsonl` com path sanitizado
  - Evento em `indicator_signals.jsonl` ou `setup_research_log.jsonl` conforme o tipo
  - Telegram recebido (se a estratégia já estiver em SMALL_SIZE ou NORMAL_SIZE; em SHADOW não envia)

### F4. Schema warnings (Fase 1 SHADOW ativa)
- [ ] `tail logs/schema_warnings.jsonl` — se houver warning novo da estratégia recém-deployada, **investigar** (template pode ter campo faltando)

### F5. 24-48h watch
- [ ] No próximo `weekly_review.py --mode once`: seção "Template / Schema / Dedup Health" continua **OK** ou **WARN explicável**
- [ ] `legacy_endpoint_used` = 0 nos logs ativos
- [ ] Nenhum spike de `schema_warnings_24h`

---

## G. Rollback procedure

### Quando rollback
- F1 falhou em qualquer item
- F3 mostra payload corrompido ou JSON inválido
- F4 mostra schema warning não esperado
- F5 detecta degradação 24h pós-deploy

### Como rollback
**Código:**
```bash
git revert <commit_sha>           # cria commit revertendo
# OU (se commit não foi pushed)
git reset --hard HEAD~1           # só se NÃO empurrado pro remote
```

**Receiver:**
```bash
launchctl kickstart -k gui/$(id -u)/com.cristrein.tv-webhook-receiver
```

**Alerta TV:**
- Desativar alerta novo via UI (não deletar — só desativar; permite re-ativar rápido)
- Manter logs históricos pra diagnosis

**Estratégia:**
- Mover entrada do `strategies/active/<id>.md` pra `strategies/paused/<id>.md`
- Anotar motivo do rollback no arquivo
- Seguir DIAGNOSIS protocol (seção 6 do PIPELINE)

---

## H. Regras não-negociáveis (resumo executivo)

- **Nunca** rodar receiver com `python3` direto — sempre `./start_receiver.sh` ou LaunchAgent
- **Nunca** ativar estratégia direto em PRODUCTION_NORMAL_SIZE — sempre SHADOW → SMALL_SIZE → NORMAL_SIZE
- **Nunca** misturar mudança de infra (receiver/secret/webhook) com Pine/estratégia no mesmo commit
- **Nunca** ignorar `schema_warnings.jsonl` — se subir, parar promoção
- **Nunca** propor mudança com n<30 — declarar "Amostra insuficiente"
- **Nunca** pular Pre-Change Discipline (4 perguntas) em mudanças que tocam canais de dados
- **Sempre** secret scan antes de commit
- **Sempre** `git diff --check` antes de commit
- **Sempre** smoke test pós-deploy (F1)
- **Sempre** 24-48h watch (F5)

---

## I. Quando este checklist NÃO se aplica

- Mudanças puramente em `my-strategy/research/`, `docs/`, `MEMORY.md`: pular C, D2, D4, E, F (não toca produção)
- Backtests sem alterar Pine/template: pular tudo de C em diante (não vai pra produção)
- Documentação: apenas D1 (git hygiene) é obrigatório
