# Arquitetura de Monitoração Realtime & Emissão de Sinais — Design Spec

**Data:** 2026-07-16 · **Estado:** DESIGN (aguarda revisão do Cris) · **Autor:** sessão Claude + Cris
**Regra-mãe:** este documento é design. **Nenhum código de produção, launchd, CDP ou religar de engine
sem autorização explícita por fase** (Pre-Change Discipline + `PRODUCTION_RUNBOOK_20260702`).

---

## 0. Origem e objetivo

### Porquê (os 2 erros de 2026-07-16 que motivaram isto)
1. **Omissão** — short XAUUSD perdido: o preço quebrou 4012 → 4000 num break-and-run, e a monitoração
   baseada em turnos do assistente teve um gap de ~19 min (a explicar contexto em vez de vigiar a fita).
   **Ninguém estava a olhar a fita no instante do gatilho.**
2. **Comissão** — SL de −1R no teste live (2026-07-15/16): entry apressada num vácuo de sessão, sem
   catalisador, contra-regime. Erro de precipitação/pouca contextualização.

> **Princípio central do design:** a arquitetura tem de matar os DOIS erros, que são opostos —
> **não perder** (omissão, resolvido por deteção determinística rápida) E **não entrar cedo/mal**
> (comissão, resolvido por um leitor de qualidade que *veta* antes de sinalizar).

### Restrições travadas com o Cris
- **CDP-only** (feed de preço via TradingView Desktop + MCP/CDP; sem broker/vendor externo).
- **24h contínuo** — o Mac nunca dorme; TV Desktop + MCP sempre operacionais (compromisso do Cris).
- **Claude fora do laço de polling** — determinístico faz o trabalho contínuo (0 tokens); Claude só é
  invocado num gatilho qualificado.
- **Orçamento = Claude Max 5x** — a Camada 2 tem de caber no plano (cooldown + dedup + cap).
- **Alerta-only, human-in-the-loop, ZERO auto-trade.** Execução automática (broker) = fase C, futura.

---

## 1. Arquitetura escolhida — Híbrida (③)

Uma **única peça nova** (o daemon de preço + scanner), que **reusa** os daemons EF/notícias já vivos como
contexto, e um **bridge fino** que corre o ensemble Claude só no gatilho.

```
                    ┌─────────────────────────────────────────────┐
   TradingView ─CDP─┤  DAEMON RÁPIDO (novo, launchd 24h, 0 tokens) │
   Desktop          │  · poll preço/OHLCV/estrutura via MCP/CDP    │
                    │  · Camada 1: avalia condições dos engines     │
                    │  · Camada 2 E0: monta market_context.json     │
                    │  · Camada 2 E1: deteta candidatos             │
                    └───────────────┬─────────────────────────────┘
   EF/News daemons ─(snapshots)────►│ (lê external_context.json,
   (já existentes)                  │  investinglive_news.json, etc.)
                                    │
                          gatilho qualificado
                                    ▼
                    ┌─────────────────────────────────────────────┐
                    │  BRIDGE DE JUÍZO (Claude ensemble — só aqui) │
                    │  · Camada 2 E2: leitor de qualidade + vetos  │
                    │  · Camada 1: qualify leve (opcional)         │
                    └───────────────┬─────────────────────────────┘
                                    ▼
                    ┌─────────────────────────────────────────────┐
                    │  TELEGRAM (reusa tg_trade_signal, alarme 3-5×)│
                    │  + log JSONL para revisão/forward            │
                    └─────────────────────────────────────────────┘
```

**Porquê ③** (vs ① monolito, vs ② multi-daemon+bus): superfície nova mínima (1 daemon), reusa o padrão
sancionado do projeto (Python determinístico + snapshots + launchd + Telegram), **divisão de trabalho (B)
por composição** (EF/news já são serviços separados) + **ensemble (C)** no gatilho, falha isolada, melhor
encaixe Max 5x, e entrega valor no Dia-1 (níveis A já teriam salvo o short de hoje).

### Componentes
| Componente | Novo? | Função | Custo Claude |
|---|---|---|---|
| Daemon rápido (`realtime_monitor.py`) | **novo** | poll CDP + Camada 1 + Camada 2 E0/E1 | 0 |
| Context Engine (E0, dentro do daemon) | **novo** | monta o dossiê `market_context.json` | 0 |
| Candidate Detector (E1, dentro do daemon) | **novo** | deteta formações/eventos → candidatos | 0 |
| Quality Reader (E2, bridge) | **novo** | ensemble LLM: convergência + vetos | **só no gatilho** |
| EF/News daemons | existe | contexto macro/notícias (snapshots) | 0 |
| Telegram bridge | existe | emitir sinal (reusa `tg_trade_signal.py`) | 0 |
| Watchdog/heartbeat | **novo** | saúde do daemon + CDP → alerta se morto | 0 |

---

## 2. Camada 1 — Alerta de Entrys dos Engines

Engines aprovados a vigiar ao vivo. Cada engine = um **avaliador de condição determinístico** no laço
rápido; no gatilho → (qualify leve opcional via Claude) → Telegram.

### Escopo — ✅ CAMADA 1 APROVADA (Cris 2026-07-16)
Todos abaixo + L1/L2 4H LONG. Painel de métricas verificado pós-DA em
`my-strategy/research/revalidation/consolidate_entry_metrics_20260716.py`. Todas IN-SAMPLE (forward=árbitro).
| TF | Engine | Ativar | Nota (painel in-sample / ressalva) |
|---|---|---|---|
| 15M | A1 / A2 (MB3 + SL low-real) | ✅ | A1 13/14 · A2 16/18; N minúsculo (sem poder), fill 3R-idealizado |
| 15M | B v1.1 (MB3 + SPRING) | ✅ | RANGE_ORDERLY banda baixa ≤40% (não no painel de hoje; aprovado in-sample) |
| 15M | Cp capitulação (1º-reclaim, SL flush−0,1ATR, 3R) | ✅ | N21 WR43 avgR+0,60 strk−4; SÓ bear-2026 (regime único) |
| 15M | 5ATR-A2 STACK (N181) | ✅ | WR65,2 +75,6R DD−3 strk−3 (mais robusto por N+DD+streak) |
| 15M | CASCEX v0.1 | ✅ | N34 WR55,9 +39,6R; ⚠️ NET confinado à janela vista (fora=neutro) |
| 15M | N96 intra-BEAR | ❌ | filtro, não gatilho de entry |
| 15M | swept-runner / substrato#4 | ❌ | baseline de research |
| 4H | L1 EMA21 Continuation LONG | ✅ | SL V1 (zona_OB_low−0,1ATR) |
| 4H | L2/BPT LONG | ✅ | regime-level engine |
| 15M/4H | Short 15M · Short 4H | 🔜 futuro | entram quando os shorts forem construídos |

### Progressão A → B → C (aprovada)
- **A — Níveis estáticos** (Dia-1): armar níveis sob demanda; daemon compara `last` vs nível → Telegram.
  Resolve já o "nunca mais perder um 4012". Substitui o alerta do TV (que falhou por dom_fallback).
- **B — Condições computadas**: o daemon lê OHLCV + calcula (EMA/RSI/DMI/estrutura) e dispara em
  quebra/reclaim/rejeição.
- **C — Regras de engine**: as condições causais exatas de cada engine (Cp reclaim, A1/A2 MB3, L1/L2)
  a disparar ao vivo. Reusa a lógica já validada em `my-strategy/research/revalidation/*`.

**Governança:** alerta-only. O sinal diz "engine X armou — avalia e executa TU". Nenhuma ordem ao broker.

---

## 3. Camada 2 — Detector de Oportunidades Convergentes (o difícil)

Detector 24h de oportunidades **LONG ou SHORT** discricionárias (formações estruturais 15M/30M/1H +
oportunidades de notícia/evento realtime), com um leitor de qualidade que só emite sinal **convergente**.

### 3.1 Estágio 0 — Context Engine (determinístico, contínuo, 0 tokens)
Mantém um **dossiê de mercado** vivo (`market_context.json`), atualizado a cada ciclo, fundindo:

- **MTF estrutura (4H / 1H / 30M / 15M):** tendência por TF, leg atual (mag ×ATR, posição-na-perna),
  CHoCH/BOS recentes, swing highs/lows, zonas OB / demanda / supply (via CDP: pine_boxes, SMC, OB Detector).
- **Micro 15M:** preço vs EMAs, RSI + RSI-MA, DMI (ADX/+DI/−DI), CHOP, volume de sessão (up/down).
- **Confluência de indicadores:** NAS (bottom/top/dist-EMA/RSI), Market Order Bubbles, SMC.
- **Notícias / eventos:** dos snapshots EF já produzidos — real-yield 10Y, USD broad, VIX, COT net,
  fed path, calendário (eventos iminentes ≤96h), news gate InvestingLive (high_impact/urgency/session).

**Como computo do CDP:** reuso das MCP tools já existentes (`quote_get`, `data_get_ohlcv`,
`data_get_study_values`, `data_get_pine_boxes/lines/labels`). O daemon chama o MCP server (mesmo caminho
CDP) e/ou fala direto com CDP :9222. Cadência-alvo do dossiê: **~2-5 s** para preço/estrutura leve,
recomputo de estrutura MTF mais pesada a cada **~30-60 s** (multi-TF não muda tick-a-tick).

**Saída:** `external_factors_v2/snapshots/market_context.json` (padrão do projeto: snapshot JSON versionado
+ `latest`), com `_meta.cycle_ts` e `source_health` por eixo (fresh/stale/partial).

### 3.2 Estágio 1 — Detector de Candidatos (determinístico)
Dispara um **candidato** (com direção LONG/SHORT proposta) quando:

- **(a) Formação estrutural** (15M/30M/1H): sweep+reclaim, quebra+retest com inversão de polaridade,
  CHoCH, rejeição numa zona MTF (OB/demanda/supply), reclaim de EMA em fundo de perna, etc.
- **(b) Evento macro de alto impacto** no ouro: `news_gate.high_impact` OU janela de evento
  (`event_window`) com reação de preço confirmada.

Cada candidato carrega o **dossiê do instante** + metadados (que regra disparou, direção, níveis
propostos entry/SL/alvo derivados da estrutura).

**Anti-spam (determinístico, antes de gastar Claude):** cooldown por tipo de formação, dedup por
zona/nível, e um "gate de materialidade" mínimo (ex.: candidato tem de tocar uma zona MTF real, não ruído).

### 3.3 Estágio 2 — Leitor de Qualidade (REDESENHADO 2026-07-16 — resolve o risco de veto)
> **Problema:** o E2 puxa em direções opostas — não perder o bom (recall) E não sinalizar o mau (precisão).
> Veto rígido + voto-de-maioria de LLMs falha nos DOIS sentidos. Cinco princípios (aprovados pelo Cris):

**(0) VETOS DETERMINÍSTICOS (antes do LLM — auditáveis, tunáveis).** Os vetos importantes são computáveis
do dossiê; saem do LLM para **gates numéricos** (cada veto loga QUAL disparou + o número):
- **vácuo de sessão** = relógio UTC + ATR (ver `reference_session_volatility_windows`)
- **sem catalisador** = news_gate / EF
- **R:R ruim** = distância à próxima zona MTF (número)
- **perseguição** = distância preço↔nível de entrada (×ATR)
- **dossiê stale** = `source_health`
- **contra-regime SEM exaustão** = contra-regime **condicional à AUSÊNCIA de assinatura de reversão/
  capitulação** (NÃO à direção — os melhores negócios, Cp e o short de hoje, SÃO contra-regime; é a lição do Cp).
> O erro de ontem (vácuo+sem-catalisador+contra-regime) era 100% deterministicamente apanhável — não
> depende do LLM. Isto mata o "não veta quando precisa" E (via contra-regime-condicional) o "veta demais".

**(1) Convergência multi-eixo** (score, se passar os gates): MTF alinha com a direção? · estrutura 15M
confirma? · catalisador macro coerente? · confluência de indicadores? · timing/sessão favorável? · R:R até
à próxima zona?

**(2) Ensemble ADVERSARIAL (não vota — REFUTA).** LLMs com o mesmo prompt concordam (erros correlacionados).
Em vez de N juízes agreeable: **3 refutadores, 3 lentes distintas (estrutura / macro / execução-timing)**,
cada um a tentar **matar o candidato com uma razão CONCRETA do dossiê** (não "vibes"). Emite só se **nenhum**
refutador achar razão de morte **E** os gates determinísticos (0) passam. Refutar > julgar para precisão.

**(3) Saída GRADUADA (não binária).** Três níveis — o tier Watch resolve o "veta demais" (borderline vira
aviso, não kill silencioso; o Cris decide):
- **🟢 Sinal forte** (convergência alta + zero veto) → alarme Telegram completo (3-5×).
- **⚠️ Watch** (borderline) → heads-up "a formar-se, vigia" (NÃO é trade call).
- **⚫ Descarta** (veto ou baixa convergência) → só log.

**(4) Calibração EMPÍRICA (nunca a priori).** O shadow-run loga TODO candidato + dossiê + decisão E2 + **o
que o mercado fez**. Afinam-se os limiares contra outcomes reais (falsos-negativos = bons vetados;
falsos-positivos = maus emitidos), ancorado nos 2 testes de aceitação (short-de-hoje **passa**; SL-de-ontem
**é vetado**).

**Saída (sinal forte):** `direção · entry · SL · alvo(3R) · razão · grau de convergência (ex.: 4/6) · flag
"discricionário (Camada 2), não engine validado"`.

### 3.4 Estágio 3 — Sinal & Feedback
- **Telegram:** reusa `tg_trade_signal.send_trade_signal` (formato scannable + alarme 3-5×). Camada 2
  usa cabeçalho distinto ("⚡ OPORTUNIDADE — Camada 2 / discricionário").
- **Log:** JSONL de todos os candidatos (emitidos e reprovados) com o dossiê, para: (i) auditoria de
  qualidade, (ii) construir o forward/estatística da Camada 2, (iii) afinar limiares.

### Como isto mata os 4 erros
| Erro | Estágio |
|---|---|
| Pouca contextualização | E0 — dossiê rico pré-montado (MTF + micro + indicadores + macro) |
| Perda de timing | E1 — deteção determinística instantânea, 24h |
| Pouca confluência | E2 — exige convergência ≥ limiar multi-eixo |
| Precipitação | E2 — vetos de disciplina + ensemble devil's-advocate |

---

## 4. Orçamento Max-5x (calculado)

- **E0 + E1 + Camada 1 (polling):** **0 tokens Claude** (100% determinístico). O custo é electricidade +
  CDP; nunca toca o plano.
- **E2 (leitor de qualidade):** único consumidor. Governado por:
  - **Frequência de candidatos:** os engines são 0,5–2,6 sinais/semana cada; a Camada 2 discricionária
    é mais frequente mas ainda **poucos candidatos MATERIAIS/dia** (o gate de materialidade + cooldown +
    dedup cortam ruído antes do Claude).
  - **Estimativa:** ~**5–20 avaliações E2/dia** no total (Camada 1 gatilhos + Camada 2 candidatos).
  - **Por avaliação:** 1 chamada orquestrada que faz o ensemble internamente (subagentes numa só sessão),
    contexto **bounded** (dossiê compacto, não histórico bruto). Evita N sessões top-level separadas.
  - **Salvaguardas de custo:** cooldown por engine/formação · dedup por zona · **cap global/hora**
    (ex.: ≤6/h) · modo "degradado" que baixa o ensemble a 1 leitura se o cap se aproximar.
- **Conclusão:** cabe no Max 5x com folga, desde que o polling nunca invoque Claude e o cap/dedup segurem
  mercado choppy. **A calcular com números reais na fase de implementação** (medir candidatos/dia num
  shadow-run antes de ligar o Telegram).

---

## 5. Tratamento de Falhas / Watchdog (o "sem falhas" possível com CDP-only)

Com CDP-only, "sem falhas" = **detetar e ALERTAR a falha rápido**, não silêncio. Mecanismos:

- **launchd `KeepAlive`** no daemon rápido (reinício automático se morrer).
- **Health-check CDP** a cada ciclo: se `tv_health_check` falhar / preço não atualiza há > N s →
  tenta reconnect; se persistir → **alerta Telegram "MONITOR CEGO"** (nunca falha em silêncio, que foi
  o modo de falha de hoje).
- **Heartbeat**: o daemon emite um "estou vivo + preço atual" (log sempre; Telegram só em transição de
  estado ok↔degradado, para não spammar).
- **Keep-awake**: `caffeinate` sob o daemon (o Mac não dorme; se o compromisso mudar, o watchdog avisa).
- **Degradação graciosa**: se um eixo do dossiê ficar stale (ex.: news feed morto), o daemon **continua**
  com estrutura+preço e **marca o dossiê como parcial** (E2 sabe que falta o eixo macro → mais conservador).
- **Dry-run / kill-switch**: flag de pausa (`monitor.pause`) e modo log-only (não emite Telegram) para
  manutenção segura, alinhado a `feedback_pause_daemon_and_cron`.

---

## 6. Testes / Validação

- **Replay dos casos conhecidos:** correr o Candidate Detector (E1) contra: (i) o short de hoje
  (quebra 4012 → deve gerar candidato SHORT a tempo), (ii) o SL de ontem (vácuo/contra-regime → E2 deve
  **vetar**). São os 2 testes de aceitação canónicos.
- **Shadow-run (log-only) antes do Telegram:** rodar N dias emitindo só para log; medir candidatos/dia,
  taxa de veto, custo Claude real → validar orçamento Max-5x e afinar limiares ANTES de confiar.
- **Dossiê vs realidade:** comparar `market_context.json` com o que o Cris vê no chart (amostragem).
- **Watchdog:** simular CDP morto → confirmar alerta "MONITOR CEGO" em < N s.
- **Nada é declarado pronto sem demonstrar** (PRINCIPAL_2.A): abrir o log, mostrar o sinal real,
  comparar antes/depois.

---

## 7. Ordem de construção (incremental — 1 fase por vez, autorização por fase)

| Fase | Entrega | Valor | Toca produção? |
|---|---|---|---|
| **P1** | Daemon rápido + Camada 1 **níveis (A)** + watchdog + heartbeat + Telegram | "nunca mais perder um 4012" | novo daemon (autorizar) |
| **P2** | Camada 1 **condições (B)** + regras de engine **(C)**: Cp, A1/A2, B, L1, L2 | engines aprovados ao vivo | religar engines (autorizar) |
| **P3** | Camada 2 **E0** — Context Engine (dossiê MTF+micro+indic+macro) | contexto rico pré-montado | novo snapshot (baixo risco) |
| **P4** | Camada 2 **E1** — Candidate Detector | deteção 24h de oportunidades | determinístico (baixo risco) |
| **P5** | Camada 2 **E2** — Quality Reader (ensemble) + shadow-run + orçamento real | sinais convergentes filtrados | Claude gasto (validar Max-5x) |
| **P6** | Ligar Telegram da Camada 2 após shadow-run aprovado | sinais discricionários ao vivo | emissão ao vivo (autorizar) |
| **🔜** | Short 15M + Short 4H → Camada 1 (quando os shorts existirem) | cobertura short | futuro |

Cada fase: Pre-Change Discipline + Plan agent para o que for arquitetural + verificação antes de "pronto".

---

## 8. Governança & Risco (não-negociável)

- **Alerta-only. ZERO auto-trade.** Nenhuma ordem a broker em nenhuma fase deste spec.
- **Camada 2 = discricionário** — sinais etiquetados "não engine validado, confiança menor". O Cris
  executa e é o árbitro.
- **Produção atual intocada** até cada fase ser autorizada; nada de religar engine/daemon sem sign-off
  (`PRODUCTION_RUNBOOK` §5 forbidden actions).
- **Secrets** (.env, tokens Telegram, webhook) nunca expostos; reuso do bridge existente.
- **Se a realidade divergir do plano, parar e re-planear** (não empurrar).

---

## 9. Questões abertas — RESOLVIDAS (Cris 2026-07-16)
1. ✅ **5ATR STACK + CASCEX** entram na Camada 1 (todos + L1/L2 4H LONG). Painel verificado pós-DA.
2. ✅ **Cadência do dossiê = event-driven + piso 60s** (recompute MTF pesado no fecho de barra 15M, OU
   move > X·ATR, OU candidato a formar-se; cache entre isso). Mais barato E mais fresco-quando-importa.
3. ✅ **Limiares E2 = calibrar no shadow-run** (começar permissivo/graduado: forte ≥4/6, watch 3/6). Não a priori.
4. ✅ **Ensemble = 3 refutadores adversariais, 3 lentes** (estrutura/macro/execução). Ver §3.3(2).
5. ✅ **Daemon ↔ CDP = MCP-first** (reusa a camada de tools provada — pine graphics parsing já resolvido;
   latência irrelevante à cadência de segundos). CDP :9222 direto só se a P3 medir o salto MCP lento demais.
