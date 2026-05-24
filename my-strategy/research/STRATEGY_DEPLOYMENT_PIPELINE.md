# Strategy Deployment Pipeline

Lifecycle formal para adicionar, promover, pausar e aposentar estratégias sem quebrar produção. Complementa `RESEARCH_POLICY.md` (ciclo D1-D5 de aprendizado pós-deploy) e `RESEARCH_RUNBOOK.md` (operação diária).

**Este documento é GUIA VIVO, não bíblia.** Esperado revisitar gates específicos depois que 2-3 estratégias passarem pelo fluxo real. Princípio: simplificar primeiro, complicar só com evidência de dor real. Mudanças no pipeline devem ser commit separado (`docs: adjust strategy pipeline gates`), não mistura com mudança de produção.

**Distinção HARD vs SOFT:**
- **HARD (infra/segurança):** regras na seção 9 marcadas 🔒 — não-negociáveis, sem exceção (originadas de incidentes reais).
- **SOFT (processo/gates):** sample gates, janelas temporais, número de exemplos — guidelines com espaço para exceção justificada por escrito no próprio Candidate Packet.

---

## 1. Princípio-base: duas máquinas, um sistema

- **Máquina de produção** (receiver + LaunchAgent + claude_recheck + Telegram): recebe alertas reais, valida, classifica, registra. Não pode ficar cega.
- **Máquina de pesquisa** (TradingView desktop + MCP + backtests + chart review): consome o chart e o MCP. Pode entrar em conflito com a produção se ambos quiserem o chart ao mesmo tempo.

Regra: **nunca desligar a produção pra fazer pesquisa.** Use o protocolo de Maintenance Window (seção 7).

---

## 1.5. Escopo: o que ESTE pipeline cobre (e o que NÃO cobre)

**Cobre — "Estratégia completa":** unidade decisional que gera trade real, com hipótese, critérios de entrada/saída, gestão, e expectativa de R/expectancy. Ex: `XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED`, `REVERSAL_CAPITULATION_LONG`.

**NÃO cobre — "Indicador de contexto" / detector:** sinal bruto que NÃO gera trade sozinho, mas alimenta classificação humana ou outras estratégias. Ex: `NAS_TopBottom_Detector`, `Custom_OB_Detector`, `Market_Bubbles`, `RSI` (cross/divergence).

**Por que separar:**
- Indicador de contexto não tem expectancy própria — não faz sentido aplicar gates "n≥30 trades, PF>1.2".
- Indicador é instrumental: vira input pro `claude_recheck`, pra `setup_research_log`, pra filtros macro. Falha/promoção segue critério diferente (cobertura de eventos, ruído/sinal).
- Aplicar pipeline completo a indicador é teatro burocrático.

**Fluxo simplificado pra indicadores de contexto:**
1. Pine criado, template JSON registra evento com `indicator_signal` + `signal_type`
2. Validação técnica via `DEPLOYMENT_CHECKLIST` (seções A, B, C, F1-F2 aplicam normais)
3. Sem ciclo SHADOW→SMALL→NORMAL; promoção é "loga e fica disponível pra outras estratégias usarem"
4. Aposentar quando 30 dias sem ser consumido por nenhuma estratégia ativa

Indicador que **VIRE** estratégia completa (ex: alguém propõe "comprar todo `Market_Bubbles_Large_Buy`") segue o pipeline completo a partir de RESEARCH.

---

## 2. Lifecycle — 7 estados oficiais

```
RESEARCH → CANDIDATE → SHADOW → PRODUCTION_SMALL_SIZE → PRODUCTION_NORMAL_SIZE
              ↓                            ↓                       ↓
            PAUSED ←──────────────────────────────────────────────┘
              ↓
           RETIRED
```

| Estado | O que faz | Pode |
|---|---|---|
| **RESEARCH** | Hipótese em backtest/exploração. Pode mudar tudo. | Backtest, chart review, anotações. Nada operacional. |
| **CANDIDATE** | Backtest tem evidência mínima e a estratégia tem nome, ativo, TF, regras objetivas. Existe um `.md` no `strategies/candidates/`. | Criar Pine + template. Sem ativação no TV ainda. |
| **SHADOW** | Pine + template + alerta TV criados. Receiver loga, classifica, registra outcomes. **Não** envia Telegram operacional. **Não** entra em strategy_rules ativas. | Coletar dados reais. Refinar regras. |
| **PRODUCTION_SMALL_SIZE** | Estratégia gera SETUP_VALIDO real, com Telegram operacional e gestão real. Tamanho de posição **reduzido** (0.25-0.5x da regra normal). | Trade real, monitoramento intensivo, ajustes finos. |
| **PRODUCTION_NORMAL_SIZE** | Tamanho de posição normal (1x). | Operação plena. |
| **PAUSED** | Algo deu errado (regime change, bug, dúvida). Webhook continua chegando + logando, mas Telegram operacional silenciado e strategy_rules marca a regra como inativa. | Diagnosticar (seção 6). Decidir: re-promover ou aposentar. |
| **RETIRED** | Aposentada. Alerta TV desativado, template arquivado, regra removida de strategy_rules. Histórico preservado em `strategies/retired/`. | Nada. Pode ressurgir como nova RESEARCH se a tese mudar. |

**Paper trading (opcional, NÃO é gate):** pode ser usado em qualquer ponto após CANDIDATE pra validar execução, broker, slippage, sizing ou routing. **Não substitui** SHADOW (que valida edge) nem PRODUCTION_SMALL_SIZE (que valida sob condições reais). Não inserir paper como obrigação — só quando a dúvida for de execução, não de edge.

---

## 3. Promotion Gates (objetivos)

### Gate RESEARCH → CANDIDATE

- [ ] Strategy Candidate Packet preenchido (ver `STRATEGY_CANDIDATE_TEMPLATE.md`)
- [ ] Backtest com janela mínima de 6 meses (ou n≥30 trades, whichever first)
- [ ] Expectancy em R **positiva**
- [ ] Profit factor > 1.2 (ou justificativa por trade lifecycle longo)
- [ ] Critérios de entrada e invalidação **objetivos e codificáveis em Pine**
- [ ] Identificada janela de condições em que **não** operar

### Gate CANDIDATE → SHADOW

- [ ] Pine criado e compilado sem erro (`pine_smart_compile`)
- [ ] Template JSON validado (`json.loads()` passa, contém `ts_signal`)
- [ ] Alerta TV criado, validado via MCP `alert_list` (parsing OK, sem corrupção tipo Cris session 2026-05-24)
- [ ] Webhook URL correto (LaunchAgent `/webhook/<SECRET>`)
- [ ] `tradingview_alerts.jsonl` recebeu ao menos 1 disparo de teste com path sanitizado
- [ ] Entrada criada em `strategies/candidates/<id>.md` com status `SHADOW`

### Gate SHADOW → PRODUCTION_SMALL_SIZE

- [ ] **n ≥ 30 eventos shadow reais** registrados em `setup_research_log.jsonl` (sample gate directional da MEMORY)
- [ ] **Schema warnings < 5%** dos eventos da estratégia em `schema_warnings.jsonl`
- [ ] Sem `duplicate_hash` indevido (dedup rate normal pra TF)
- [ ] Outcome rate observado ≥ 80% do esperado pelo backtest (em R/expectancy)
- [ ] MFE/MAE coerentes com backtest (não desvio > 50%)
- [ ] Sem falsos positivos por template/Pine ruim
- [ ] Janela de observação ≥ 4 semanas (independente de n)
- [ ] Proposta formal em `proposals/` aprovada pelo Cris (segue D4-D5 do RESEARCH_POLICY)

### Gate PRODUCTION_SMALL_SIZE → PRODUCTION_NORMAL_SIZE

- [ ] **n ≥ 30 trades reais** em SMALL_SIZE (sample gate directional)
- [ ] Win rate / expectancy em R **dentro do intervalo esperado** pelo backtest (não fora de ±20%)
- [ ] Drawdown realizado ≤ drawdown projetado
- [ ] Slippage real ≤ assumido no backtest
- [ ] Sem incidente de execução grave (ordem perdida, dupla execução, etc.)
- [ ] Janela mínima ≥ 8 semanas em SMALL_SIZE
- [ ] Aprovação explícita do Cris

**Regra não-negociável:** nunca pular SMALL_SIZE. Mesmo estratégia com backtest excelente entra em SMALL_SIZE primeiro.

---

## 4. Sample gates (calibrados ao histórico do projeto)

Mesmos gates da MEMORY:

| Tier | n | Decisão permitida |
|---|---|---|
| Anedótico | < 30 | Apenas hipótese; nada operacional |
| Directional | ≥ 30 | Indica direção; pode entrar em SHADOW |
| Preliminary | ≥ 50 | Suficiente pra promover SHADOW→SMALL_SIZE com proposta |
| Solid | ≥ 100 | Confiança alta; pode promover SMALL_SIZE→NORMAL_SIZE |

Se a estratégia opera 4H ou 1D, n=30 pode levar meses. **Não force** redução de janela pra atingir n — espere ou aumente cobertura (mais ativos, mais TFs aplicáveis).

---

## 5. Canary deploy (regra de escalonamento)

Quando promover de SHADOW → SMALL_SIZE:

- **1 ativo, 1 TF, 1 alerta** primeiro (mesmo que a estratégia funcione em N ativos no backtest)
- Mínimo **30 dias OU n=30 trades**, whichever first
- Se OK → expandir pra 2º ativo/TF
- Sempre adicionar 1 dimensão por vez (nunca 2 ativos novos no mesmo deploy)

---

## 6. DIAGNOSIS protocol (quando estratégia falha)

Estratégia em PRODUCTION que perde em sequência (drawdown > 1.5× projetado, ou 3 trades perdedores consecutivos fora do esperado) entra em **PAUSED**, não direto em RETIRED.

Em PAUSED, classificar a falha em uma de 3 categorias:

| Categoria | Sinais | Ação |
|---|---|---|
| **Regime change** | Volatilidade mudou, correlação quebrou, contexto macro virou. Padrão de price action diferente do backtest. | Não retirar. Re-treinar regras pra novo regime (volta a RESEARCH) ou esperar regime anterior voltar. |
| **Flaw real** | Bug no Pine, template, schema, dedup. Backtest tinha viés (lookahead, survivorship). Critério ambíguo. | Corrigir bug ou reformular tese. Volta a RESEARCH ou RETIRED. |
| **Random variance** | Drawdown dentro da faixa de drawdown esperado pelo backtest. Sem mudança de regime detectável. | Manter PAUSED por mais 2 semanas observando. Re-promover se voltar à média. |

**Não retirar estratégia sob impulso emocional após perda.** Diagnosticar primeiro.

---

## 7. Maintenance Window (pesquisa sem cegar produção)

Pesquisa no TradingView (chart review, backtests com MCP, replay mode) **pode conflitar** com:
- `monitor_xau_4h_strategies.py` (precisa do chart pra ler indicadores)
- `claude_recheck.py` (faz screenshots via MCP)
- `mcp__tradingview__chart_set_*` (concorre com manipulação manual do chart)

### Protocolo de entrada na janela

1. Confirmar receiver saudável: `curl http://127.0.0.1:8787/health` → `ok:true`
2. Confirmar LaunchAgent: `launchctl print gui/$(id -u)/com.cristrein.tv-webhook-receiver` → state=running
3. Pausar processos que usam MCP/chart:
   - `claude_recheck`: `touch /tmp/claude_recheck.paused` (flag já existe)
   - Monitor MCP: parar via `launchctl bootout` ou stop_script equivalente (NÃO inventar nova flag agora — usar mecanismo já existente do processo)
4. Registrar início: append em `logs/research_window.jsonl` com `{"started_at":"<iso>","reason":"<txt>"}`
5. Rodar pesquisa

### Protocolo de saída

1. Remover flags / restartar processos pausados via launchd/wrapper
2. Smoke test:
   - `/health` OK
   - `tail tradingview_alerts.jsonl` mostra eventos recentes
   - `tail launchd_tv_receiver_stderr.log` = 0 bytes ou sem traceback
3. Registrar fim: append em `logs/research_window.jsonl` com `{"ended_at":"<iso>","health_ok":true}`
4. **Receiver continua ON o tempo inteiro.** Só processos MCP-dependentes ficam pausados.

---

## 8. Git rules

### Branches

| Branch | Quando usar |
|---|---|
| `main` | Produção validada. Sem código não testado E2E. |
| `feature/<nome>` | Nova estratégia (Pine + template + entrada no registry) |
| `research/<hipotese>` | Backtest puro, sem código que entre em produção |
| `fix/<problema>` | Correção isolada (template ruim, bug no receiver, etc.) |
| `infra/<area>` | Mudanças no receiver/wrapper/launchd/health/schema |

Branches `research/*` e `feature/*` podem viver semanas. `fix/*` e `infra/*` devem ser pequenos e mergeados rápido.

### Commits

- **Um commit, um propósito.** Nunca misturar Pine novo + receiver patch + template fix no mesmo commit.
- Commit message no formato: `<verb-imperativo> <escopo>`. Ex: `Add ETH 15M reversal candidate Pine`, `Fix XAU template missing ts_signal`.
- Sempre `git diff --check` antes (whitespace).
- Sempre secret scan antes (grep do SECRET nos staged files).

### Co-author

Toda mudança feita junto com Claude usa:
```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## 9. Regras 🔒 HARD (não-negociáveis, originadas de incidentes reais)

Estas regras são absolutas. Quebrar uma delas custou dias de retrabalho — não há exceção justificável.

### 9.1 🔒 Receiver
- **Nunca** rodar com `python3 tv_webhook_receiver.py` ou `nohup python3 -u tv_webhook_receiver.py` direto. Sempre via `./start_receiver.sh` ou LaunchAgent (`launchctl kickstart -k`).
- **Motivo do hard:** sem `source .env`, `SECRET` cai pro default `local-test` e todos os 359 alertas TV dão 403 silenciosamente (incidente 2026-05-24).

### 9.2 🔒 Separação de mudanças
- **Nunca** mexer em receiver/secret/webhook **no mesmo commit** que adiciona Pine ou template novo.
- **Nunca** editar alertas TV em massa sem checklist por lote (ver `DEPLOYMENT_CHECKLIST.md`).
- **Motivo:** mistura cria zona de ambiguidade pra rollback. Cada bug custa horas a mais pra diagnosticar.

### 9.3 🔒 Pre-Change Discipline (CLAUDE.md raiz)
Antes de propor mudança em receiver/template/Pine/prompt operacional, responder as 4 perguntas:
1. Que INPUT a mudança opera?
2. Esse input está vivo nos últimos 7 dias?
3. Quantos eventos/dia chegam pelo canal?
4. Se < 5 events/dia OU canal dormente: STOP e revisar arquitetura.
- **Motivo do hard:** em 2026-05-18 propusemos fix em arquitetura morta (Caminho B silencioso há 3 dias).

---

## 9-SOFT. Regras de processo (guidelines com espaço pra exceção justificada)

Estas são gates de qualidade. Se a estratégia exige exceção, **registrar a justificativa no Candidate Packet** (campo "exception_to_pipeline") — não pular silenciosamente.

### 9.4 SOFT — Promoção de estratégia
- Ativar estratégia direto em PRODUCTION_NORMAL_SIZE: **não recomendado**, mas se houver justificativa (ex: estratégia já validada em conta externa por meses), documentar no Candidate Packet.
- Pular SHADOW: **não recomendado**. Backtest forte ainda merece dados reais. Exceção: estratégia migrada de sistema externo com track record auditado ≥ 6 meses.

### 9.5 SOFT — Sample gates
- Mudança de regra com n<30: tendência é declarar "amostra insuficiente". Exceção: change drift detectado em monitoramento (ex: regime macro virou e gates antigos não fazem mais sentido) — documentar.
- Schema warnings > 5%: pausar promoção é default. Exceção: warnings são falsos positivos comprovados — documentar e seguir.

---

## 10. Próximos upgrades (NÃO criar agora — backlog)

- `my-strategy/strategies/registry.json` quando >10 estratégias ativas
- Wrapper `enter_maintenance.sh` / `exit_maintenance.sh` quando research window virar rotina semanal
- Auto-promotion script que lê sample gates e sugere próximo estado (após 3+ estratégias passarem manualmente pelo pipeline)
- Dashboard de strategy performance no `weekly_review.py` (já tem Template/Schema/Dedup Health; falta Strategy Health por estratégia)

Nenhum desses deve ser criado antes de o pipeline atual rodar 3+ vezes na mão. **Simplest first.**
