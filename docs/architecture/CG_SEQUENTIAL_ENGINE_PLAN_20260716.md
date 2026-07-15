# PLANO SEQUENCIAL — Engine Cg (fundo-profundo lento) + método anti-erro (2026-07-16)

Baseado na avaliação da sessão 2026-07-15/16 (que chegou ao Cp aprovado). **Regra-mãe: UMA camada de
engine por passo, completa e verificada ANTES do próximo. Nunca múltiplas requisições no mesmo passo.**

---

## A. AVALIAÇÃO DA SESSÃO (o que evitar / o que reproduzir)

### ERROS a EVITAR (custaram horas)
1. **Snapshot / eixo-único** em vez de multi-fatorial+trajetória (o hook de miopia disparou 3×).
2. **Ignorar estrutura-primeiro** (regime detector + leg) — fui direto a flushes/indicadores. Cris corrigiu 2×.
3. **Extração de indicadores partida** — só BUY-bubbles num sell-off (buy_abs=0), NAS seed-skip perdeu o cluster, cascade de label SMC repintante.
4. **Escala errada** — flush-de-vela (1,8×ATR) em vez de MAGNITUDE-DA-PERNA (18-32×ATR).
5. **Reinventar mal em vez de RESGATAR** os engines anteriores (perdi tempo a re-implementar com bugs).
6. **Bugs de dados** — truncamento de blocos (posições B falsas 17-39% vs 48-62%); contagem-vs-soma (4 vs 21 trades).
7. **Conclusões prematuras** — declarei "não mecanizável" antes do trabalho de confluência/DA completo.
8. **Muitas coisas num só passo** → muitos erros (o ponto do Cris).

### ACERTOS a REPRODUZIR
1. **Ordem ESTRUTURA → CONTEXTO → CONFLUÊNCIA** (quando aplicada, funcionou).
2. **Auditoria de lookahead ANTES de confiar** (apanhou engine7-lookahead; verificou event_stage2 e cp_refined causais) — feita via Agent tool real (subagent DA restrito a lookahead).
3. **Resgatar a lógica anterior** ([[BOTTOM_ENGINE_LOGIC_REFERENCE]]) — select-event-first, cascade/reclaim/hl.
4. **Leitura auction-theory / trajetória** (order-flow cumulativo na perna, não snapshot).
5. **Null-first** (bater a faca 22%).
6. **Plot canónico + validação VISUAL do Cris** ("melhor entry por construção").
7. **Pedir ao Cris para NOMEAR o que vê** quando encravei (assinatura de perna, auction) → destravou.
8. **Baseline vs refinamentos** — manter o que funciona, honesto (refinos que não melhoram = descartar).

### A SEQUÊNCIA VENCEDORA (filosofia que levou ao Cp)
GT(marcas Cris via MCP) → **estrutura-primeiro** → **null** → **resgatar prior** → **confluência**
(extração correta, multi-fatorial) → **auction/trajetória** → entry+SL+3R → **auditoria lookahead** →
**plot+validação Cris** → baseline-vs-refino → prereg+forward.

---

## B. PLANO Cg — engines sequenciais (fundo-profundo LENTO; oposto do flush violento do Cp)

> Natureza de Cg: declínio **lento, profundo, prolongado** que faz fundo **gradualmente** (rounding
> bottom / desaceleração), não clímax. Reversão estrutural lenta. Cada passo = 1 engine, na íntegra.
> Só avanço ao próximo quando o atual estiver verificado.

### PASSO 1 — GT + NATUREZA (case study)
- **Objetivo:** ter o ground-truth de Cg (fundos-profundos marcados pelo Cris) + entender a natureza (lento/rounding), distinta do Cp.
- **Como (íntegra):** Cris marca no chart os fundos-profundos (text_note); extraio via MCP → base-low 15M. Caracterizo APENAS a natureza (magnitude/duração da perna, desaceleração), sem indicadores ainda.
- **Evita erro:** #4 (escala) — medir a PERNA, não vela. Confirmar N.
- **Feito quando:** GT extraído + natureza descrita + Cris confirma.

### PASSO 2 — ENGINE DE ESTRUTURA (structure-first, ZERO indicadores)
- **Objetivo:** detetar a região estrutural de Cg (fundo de perna de baixa PROFUNDA e LENTA) via regime detector + leg.
- **Como:** por GT, ler leg 4H + macro 1D; achar assinatura comum (legMag grande + duração longa + desaceleração dos lower-lows + is_leg_bottom). Output = detetor de candidato estrutural.
- **Evita erro:** #2 (estrutura-primeiro) e #1 (desaceleração = trajetória, não snapshot).
- **Feito quando:** detetor capta os GT (recall) + densidade reportada.

### PASSO 3 — NULL (a faca)
- **Objetivo:** o baseline a bater (buy-any-reclaim na região estrutural).
- **Como:** enumerar candidatos na região, entry base + 3R, medir hit-3R = null.
- **Evita erro:** #7 (não concluir antes de ter o null).
- **Feito quando:** null quantificado.

### PASSO 4 — RESGATE (referência, não reinvenção)
- **Objetivo:** aplicar os padrões vencedores anteriores ao Cg antes de construir.
- **Como:** ler [[BOTTOM_ENGINE_LOGIC_REFERENCE]]; mapear o que transfere (select-event-first, entry-por-construção).
- **Evita erro:** #5 (não reinventar).
- **Feito quando:** padrões aplicáveis listados.

### PASSO 5 — CONFLUÊNCIA DE INDICADORES (multi-fatorial, extração CORRETA)
- **Objetivo:** a confluência que separa os fundos-Cg reais dos falsos da região.
- **Como:** extração RAW correta (NAS cluster por first-appearance, BUY **e** SELL bubbles com known_at, RSI+MA+divergência-do-indicador); convergência de ≥2-3 juntos (NÃO eixo-único); testar quais separam os GT + acham extras.
- **Evita erro:** #1 (multi-fatorial) e #3 (extração completa/correta).
- **Feito quando:** confluência testada vs null + WIN/LOSS + GT.

### PASSO 6 — LEITURA AUCTION/TRAJETÓRIA (específica de Cg)
- **Objetivo:** a leitura dinâmica de Cg — para grind lento: **absorção acumulada na BASE** + desaceleração + divergência (esforço-vs-resultado ao longo do grind).
- **Como:** order-flow cumulativo/desaceleração sobre a perna-grind (trajetória, não ponto).
- **Evita erro:** #1 (trajetória).
- **Feito quando:** a leitura auction bate o null / capta os GT.

### PASSO 7 — ENTRY + SL + EXIT
- **Objetivo:** a mecânica (gatilho + SL + exit), comparando baseline vs refinamentos.
- **Como:** 1º-reclaim (ou gatilho grind-específico) + SL + 3R-fixo vs trailing (comparar, manter o melhor).
- **Evita erro:** #8 (um objetivo por vez).
- **Feito quando:** painel comparativo (WR·avgR·NET·streak·DD·GT).

### PASSO 8 — AUDITORIA DE LOOKAHEAD
- **Objetivo:** provar causalidade (sem lookahead).
- **Como:** subagente DA restrito a lookahead (via Agent tool real) sobre entrada/exit/extração/known_at.
- **Feito quando:** veredito causal + resíduos declarados.

### PASSO 9 — PLOT CANÓNICO + VALIDAÇÃO VISUAL DO CRIS
- **Objetivo:** Cris avalia as trades no gráfico.
- **Como:** pausa + long_position+label (sem screenshot); Cris julga região/qualidade.
- **Feito quando:** Cris valida ou aponta correções.

### PASSO 10 — BASELINE vs REFINO + PREREG + FORWARD
- **Objetivo:** selar o melhor variante + prereg + coletor.
- **Como:** comparar honesto, selar, prereg (regras congeladas + PASS/FAIL), coletor forward.
- **Feito quando:** prereg selado + memória + commit.

---

## C. DISCIPLINA DE EXECUÇÃO
- **1 passo por interação.** Cada passo = 1 objetivo. Verificar antes de avançar.
- **Antes de correr qualquer análise:** confirmar multi-fatorial + trajetória + estrutura-primeiro + extração-correta (checklist do hook de miopia).
- **Antes de reportar backtest:** auditoria de lookahead (subagente real).
- **Se encravar:** pedir ao Cris para NOMEAR o que vê, não adivinhar.
