# AUDITORIA SEMÂNTICA DOS SINAIS TELEGRAM — 2026-08-19

Ordem Cris 19/08: auditar TODA a semântica dos sinais (estratégias, live reader, price-shock, advisories, infra)
vs as mensagens reais do Telegram; detetar erros/ambiguidades; propor parametrização única. Inventário completo
por leitura de código (read-only). Gatilho: sinais AMD e price-shock a sair no grupo rotulados "L1 EMA21 4H".

## A. DEFEITOS ENCONTRADOS (por gravidade)

### A1. Prefixo "📊 L1 EMA21 4H" herdado por 6 emissores (CRÍTICO — identidade errada no grupo)
`telegram_notify.py` da L1 prefixa TUDO com "📊 L1 EMA21 4H"; estes módulos importam-no:
1. CP run_cp_cycle.py — sai com DUPLO prefixo ("L1 EMA21 4H" + "CP CAPITULAÇÃO 15M")
2. AMD run_amd_cycle.py — "L1" + "🟡 AMD SETUP ARMADO"/"🟢 AMD 1H CANDIDATOS" (screenshot Cris 13/08)
3. finnhub_gld_ws.py — "L1" + "⚡ CHOQUE OURO (GLD tick)" + <b> cru
4. regime_engine_cycle.py — "L1" + "🔄 REGIME XAU: X→Y"
5. bar_store_cycle.py (alerta TAB SUMIU) — "L1" + <b> cru
6. level_alerts_watcher.py — "L1" + <b> cru
Já corrigido 19/08: price_shock_cycle.py (sender próprio "⚡ PRICE-SHOCK (advisory)", commit 51c4162).

### A2. `<b>` cru no grupo (formatação quebrada)
gld_ws, bar_store, level_watcher escrevem HTML mas o sender L1 envia sem parse_mode → tags aparecem literais.

### A3. Mute global `.telegram_muted` NÃO cobre o caminho E2._tg_send (CRÍTICO operacional)
Respeitam mute: L1, L2, price-shock, receiver, d2r/tg_trade_signal, weekly, monitor_legacy, e todos os que herdam TN.
IGNORAM mute: e2_quality._tg_send e todos os que o usam — reader E2, candle-reader, A1/A2, reclaim, vela,
validador, price-sentinel — e ainda o stack-watchdog (gate próprio WATCHDOG_TELEGRAM).
Consequência: "mutei os sinais" NÃO cala a maioria das linhas modernas.

### A4. Roteamento grupo/pessoal implícito e surpreendente
E2 reader: vai ao GRUPO se houver sinal de estratégia recente na mesma direção, senão vai ao pessoal — regra
invisível para quem lê. Reclaim: env RECLAIM_TG decide. Vela/validador/sentinela: sempre pessoal. Sem convenção declarada.

### A5. Vocabulário inconsistente entre linhas (ambiguidade de decisão)
- Tipos de chamada: "CANDIDATE — revise o chart" (L1) · "Candidato L2/BPT" (L2) · "ENTRY" (Cp) · "SETUP ARMADO"/
  "CANDIDATOS" (AMD) · "GO" (validador) · "SINAL CONFIRMADO" (candle) · "E2 LONG ... entry/SL/alvo" (reader) ·
  "SHORT FORTE (continuação)" (price-shock) · "ENTRADA SHORT REALTIME" (sentinela). 9 palavras ≠ 9 semânticas reais.
- Alvo: "TGT 3R" · "tgt(2R)" · "alvo (3R)" · "alvos ... RRs" · "TP 2R/ext 3R" — sem padrão.
- Rodapé humano: 4+ formulações de "a decisão é tua" / "alert-only" / "advisory" / "decides + marca #N".
- Cabeçalho "🤖 LIVE SYSTEM · E1/E2 READER 15M" — "LIVE SYSTEM" é rótulo reservado ao reader (decisão 05/08)
  mas colide visualmente com estratégias; e nada distingue à 1ª vista ENTRADA vs LEITURA vs AVISO.
- Vozes contraditórias na mesma msg (ex.: "SHORT FORTE ... regime BULL(ctx) ... macro✓") sem hierarquia declarada.

### A6. Legados com template vivo
- realtime_monitor.py mantém template "NÍVEL ARMADO CRUZADO" (conceito CANCELADO 11/08) — plist não carregado,
  mas o código emissor existe; risco de religamento acidental.
- monitor_xau_4h_strategies.py ("#SETUP_XAU_4H") — legado sem daemon; manter desligado ou arquivar.

### A7. Erros de leitura na auditoria anterior (meta, para registo)
- "AMD 0 sinais/30d" errado: o ledger AMD usa h4_bar_t (epoch) — o probe procurou etime/t/ts e não achou.
- "L1 enviou os sinais X" errado: eram price-shock com prefixo herdado. Ambos derivam de A1.

## B. PARAMETRIZAÇÃO PROPOSTA (taxonomia única)

### B1. Quatro CANAIS com emoji fixo de 1º carácter (identidade à primeira vista)
- 🎯 ENTRADA — engine com entry/SL/alvo pré-registado: Cp, A1/A2, Reclaim, L1, L2, AMD-ping2
- 🧠 LEITURA — reader (E2, candle-reader): interpretação com níveis, não engine
- ⚡ AVISO — advisory sem obrigação de trade: price-shock, GLD tick, AMD-ping1 (setup armado), validador GO/INVALIDOU,
  vela-no-nível, sentinela, regime-flip
- 🩺 INFRA — saúde/feed: watchdog, tab-sumiu, weekly, d2r

### B2. Formato único de mensagem (todas as linhas)
linha1: {emoji-canal} {CANAL} · {NOME-ÚNICO} · {TF}        ex.: "🎯 ENTRADA · CP CAPITULAÇÃO · 15M"
linha2: {🟢 LONG|🔴 SHORT} {símbolo} — {tipo-de-evento}     tipos permitidos: ENTRY · CANDIDATO · SETUP · GO · INVALIDOU · LEITURA · CHOQUE · FLIP
linha3 (se há níveis): entry {x} · SL {y} · alvo {z} ({n}R)   — SEMPRE "alvo … (nR)", nunca TGT/tgt/TP
linha4: contexto mínimo (1 linha, SEM vozes contraditórias: se contexto contradiz a direção, escrever "CONTRA {voz}: {valor}")
linha5 (rodapé único): "decisão humana · marca #N"           — uma só formulação em todo o sistema
Formato: texto plano SEMPRE (sem parse_mode HTML, sem <b>) — copiável, robusto; hora sempre Lisboa.

### B3. Sender ÚNICO partilhado
Novo módulo alert-bridge/notify.py: send(label, text, audience="group"|"personal", respeita SEMPRE .telegram_muted,
sem parse_mode. Todos os emissores migram para ele; telegram_notify da L1 fica EXCLUSIVO da L1 (ou também migra).
Mata A1/A2/A3 de uma vez e dá um único sítio para auditar.

### B4. Roteamento explícito
grupo = 🎯 ENTRADA das linhas aprovadas em foco + 🩺 crítico; pessoal = resto (🧠, ⚡, reclaim até N=20).
Regra escrita aqui, não implícita no código. (Alinha com proposta de foco 19/08: grupo = Cp + A1/A2.)

## C. PLANO DE APLICAÇÃO (aguarda OK por passo)
P1. notify.py único + migrar os 6 herdeiros do prefixo L1 (mata A1+A2) — mecânico, sem mudar lógica de gate
P2. mute global no caminho E2._tg_send + watchdog (mata A3)
P3. Normalizar headers/vocabulário B1/B2 em todos os emissores (mata A5) + neutralizar templates legados (A6)
P4. Roteamento B4 conforme decisão de foco do Cris
Validação: 1 mensagem de teste por emissor no chat pessoal antes de qualquer envio ao grupo.
