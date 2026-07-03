# LAB A (RODADA 2) — ENTRY DISCOVERY BRIEF (2026-07-03)

**Discovery-first (correção de escopo Cris):** exploração ampla ANTES do prereg. Engine multi-agente real: **5 perspectivas + síntese** (workflow `wf_fe1ae2d6-cfe`, 6 agentes, 337k tokens; artefato integral versionado em `research/xau_15m_bb_nas_leonardo/results/lab_a2_discovery_synthesis.json`). Nenhum subagent commitou (git log verificado). Objetivo declarado: **WR ≥50% e streak ≤5-6 (FundedNext) sem destruir runners/sumR líquido-SB**; Lab B dobrado para dentro (entry + cuts).

## 1. Linhagem resgatada (fontes lidas pelos agentes)
Maturação base #4 · Lab E (COST_ROBUST; custo em R sobe quando risk_$ cai) · Lab A rodada 1 (execução pós-sinal FAILS; seleção adversa 1:1) · lab plan (B/C/D specs + forbidden) · 5ATR/8ATR · bottom-power · swept-runner · CHoCH N84 · L2/BPT zona-pura (formato eliminação convergente + posição-na-estrutura) · regime v5 · leituras visuais documentadas (clusters de losers sob supply #295-304/#313-315/#403-408; pop-then-die MFE 0,38R) · refutações (short-mirror, direction-by-regime, macro-bottom, Engine2/7, subtrativas, 0/27 micro).

## 2. Perspectivas e hipóteses geradas (16 no total)
- **Entry Geometry:** antecipação-com-fallback (deslocamento p+1/p+2) · stop-entry de continuação (física OPOSTA ao limit refutado: miss vira loser) · SKIP de teto dobrado na entrada · ladder 2 tranches.
- **Auction/Structure:** score de capitulação-exaustão (fundo legítimo = capitulação violenta E completa; lifts publicados no scan exploratório do agente) · TRAP-BUY (comprador preso) · confirmação por deslocamento-completo · qualificação da 1ª entrada do episódio.
- **Regime Context:** mapa de validade por posição no box v5 (análogo phase34 L2) · banda de supply do regime ANTERIOR como veto condicional · legpos60/90 como trajetória de perna · confirmação especializada por regime (nível do sinal).
- **Cost/Prop Risk:** COST_FLOOR (skip de trades cost-dominados) · STREAK_ANATOMY + orçamento de stops por episódio · confirmação barata COM piso de risco (anti-armadilha Lab E) · skip de teto pesado nos clusters.
- **DA-pré:** EPISODE_RISK_BUDGET (contabilidade 1R/episódio) · GRADED_SIZE_NO_SKIP (tamanho graduado em vez de corte) + **14 exigências de protocolo** (ledger de variantes, JOIN fail-loud, anti-look-ahead automatizado, decomposição população-vs-timing, streak SÓ distribucional/bootstrap, agregações congeladas, nulls por família, runner-kill duro, painel FundedNext comum, kill-criteria inegociáveis).

## 3. Taxonomia (categorias do mandato)
1. **Trigger redesign:** antecipação por deslocamento convergente (P1) · confirmação especializada por regime (DEFER: builder) · deslocamento-completo (fundido em P1).
2. **Execution redesign:** stop-entry continuação (P2) · ladder (DEFER: pós-P2, Lab C-adjacente) · limit/retest = REJECT (forbidden rodada 1).
3. **Context-conditioned entry:** posição-no-box v5 e banda do regime anterior (DEFER → Lab B rodada estrutural; exigem box hi/lo por segmento).
4. **Risk-shape:** COST_FLOOR (embutido como piso em P1) · graded-size (DEFER: variante de P5).
5. **Episode-level:** STREAK_ANATOMY + budget (P5) · EP-FIRST e re-entry qualificada (DEFER → Lab D).
6. **Reject/forbidden:** limit/retest pós-sinal · delay puro · room_above como filtro · antecipação k2 pura sem gate · filtro de hora/killzone · SL pad · short-mirror · direção-por-regime.

## 4. Selecionadas para prereg (6 — ver PREREG para definições integrais)
**P1** TRIG_DISP_EARLY (antecipação c/ fallback + piso de risco) · **P2** EXEC_STOP_CONT (buy-stop continuação, kill-criterion nos misses) · **P3** SKIP_CEILING (veto convergente ≥3/4 lentes de teto, formato L2) · **P4** SKIP_CAPX (cap_score ≤1 = fundo sem capitulação legítima) · **P5** EPISODE_RISK_BUDGET (+STREAK_ANATOMY passo 0) · **P6** COMBO (composição congelada trigger+skips).

## 5. Rejeitadas antes do teste (com motivo) e diferidas
Ver §3.6 acima + lista integral no JSON (defer: SL_CONTEXT→Lab C, ladder→pós-P2, re-entry→Lab D, box-pos estrutural→Lab B r2, confirmação-por-regime→builder futuro, TRAP-BUY→leitura secundária de P4 [dupla contagem declarada], COST_FLOOR standalone→addendum). **Ledger de multiplicidade:** 1º score de absorção (priors de varejo) do Auction agent FALHOU no scan exploratório e **conta como tentativa** da rodada.

## 6. Limitações de dados DECLARADAS (antes de rodar)
- P1 "gates recomputados na barra de decisão": recomputáveis por barra = regime v5, rsi, pos_recent20, ema/deslocamento, piso, swept (janela ≤ p, invariante). **NÃO-recomputáveis sem builder: KNIFEKILL (bubbles janeladas), h1_pos, HTF trends** → usados do snapshot cj (2 barras à frente) = **look-ahead residual declarado**, BOUNDED por: (a) fração antecipada reportada; (b) **phantom scan no universo 4502** (candidatos onde o deslocamento dispara e os gates recomputáveis passam mas o stack cj falha = entradas fantasma do live) — contados e custeados (letrun) num painel tradeable-lower-bound.
- P3 quantil q0,80 de n_supply_overhead: global no universo 4502 (não rolling) — declarado.
- P5 pertença ao episódio: cadeia com gap ≤96 barras + trade anterior stopado (partição congelada; 3 exemplos no eval).
