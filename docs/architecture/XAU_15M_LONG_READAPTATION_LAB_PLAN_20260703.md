# XAU 15M LONG — READAPTATION LAB PLAN (2026-07-03)

## 1. Executive verdict

**READAPTATION_READY_FOR_PREREG_LABS** — base sólida + leitura de maturação DA-auditada concluída; levers identificados com formato conhecido; nenhum lab executado neste bloco (plano-apenas).

## 2. Current base

`XAU 15M LONG · swept-runner base #4 FINAL hour-causal` (USER_APPROVED_NOT_PRODUCTION, **LONG-only** por decisão de split): **N435 · WR47,6% · +291,5R · avgR0,670 · DD−11,0 · r/DD26,58 · streak−8/+6 · anos 39,7/213,6/38,3**. Regime **v5 MTF hour-causal** (canônico, intacto). RAW 15M: 2024-05-25→**2026-05-25** (8 blocos, manifests). Pendência única OFICIAL_FN: slippage/custos.

## 3. Maturation findings (leitura 2026-07-03, DA-auditada)

- **ROBUST:** (i) confirmação do gatilho é FIXA — cj−p=3 barras em 435/435; custo de confirmação = altura do bounce (mediana ~2,1 ATR) → compressão de R estrutural; (ii) **SL widening por pad NÃO paga** (−35/−43R nos pads 0,15/0,30 ATR, robusto nos 2 framings de sizing); (iii) painel base reproduzível em toda execução.
- **EXPLORATORY SIGNALS (calibração):** room_above monotônico em WR/avgR + convergência com família supply-overhead do L2 (MAS sumR anti-monotônico → só lente); padrão visual fundo-ganha / sob-supply-perde / multi-stop-em-episódio.
- **REFUTED:** SL pad como ajuste; lateness-em-preço como teste (identidade com risk_atr).
- **DA-DOWNGRADED:** recuperação pós-stop 61% (sem null, circular, double-counting) → só hipótese de re-entry; hora UTC (melhor-de-6); 2ª-entrada-de-cluster (n=37, fail-then-retry); slice BEAR-Cris N18 (anedota; só bloqueia veto).

## 4. Forbidden paths (não re-testar sem ordem explícita)

SL widening como pad · filtro ingênuo de lateness-em-preço · veto macro-BEAR duro · short mirror · direção-por-regime · seleção-de-entrada além do stack sem null novo (parede 0/27 confirmada) · limpezas subtrativas cegas · **room_above como FILTRO** (corta o bucket mais lucrativo — ENGINE=LUCRO).

## 5. Candidate labs (pré-registro obrigatório antes de rodar — §7)

### Lab A — Trigger geometry — ✅ EXECUTADO 2026-07-03: **TRIGGER_GEOMETRY_FAILS (escopo: execução pós-sinal)**
17 execuções testadas (grid limit + 4 propostas de engine multi-agentes + nulls + through): **NENHUMA bate market@cj em líquido-SB** (base 233,6 vs melhor 207,6); mecanismo = seleção adversa medida (missed base-avgR 1,4-2,7 vs filled 0,23-0,55; runners não retestam); p null=0,506. **PRESERVE market@cj como execução canônica · DISCARD família limit/retest pós-sinal (forbidden path novo)** · gatilho NO NÍVEL DO SINAL (A1/A3/A4) segue BLOCKED/aberto p/ rodada com builder re-scan. Docs: `XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_{PREREG,DA,REPORT}_20260703.md`. Próximo: **Lab B**.

### Lab A — STATUS FINAL (Cris 2026-07-03): **COMPLETE · VERDICT = NO_STRUCTURAL_SOLUTION_FOR_WR_STREAK**
P1 = timing improvement / not enough for WR-streak · **LAB_A_DOES_NOT_SOLVE_FUNDEDNEXT_WR_STREAK**. Resumo aprovado: P1 melhora NET-SB mas p(null)=0,726 (não é informação estrutural forte) · P2 reduz DD mas destrói lucro/runners · P3 vacuidade · P4 mata runners · P5 reduz DD mas corta lucro a ~49% · WR/streak seguem não-resolvidos · STREAK_ANATOMY: 97% da dor é cluster/episódio/calendário. **Próximo alvo: Lab F — Episode Risk / Streak / DD / WR** (camada de gestão de exposição, não filtro de feature). Adendo Cris: próxima etapa avalia variantes em DUAS baselines (BASE e BASE+P1).

### Lab A — RODADA 2 (entry redesign discovery-first + Lab B dobrado) — ✅ EXECUTADO 2026-07-03
Discovery multi-agente (wf_fe1ae2d6-cfe, 5 perspectivas+síntese) → 6 hipóteses pré-registradas → execução → DA (1 bug material no null do P1, corrigido). Resultados: **P1 disp-early PROMISING_NEEDS_VISUAL** (~+19R tradeable, DD/runners melhores, MAS p=0,726 vs null timing-com-piso = ganho é timing, não informação; residual declarado) · **P2 stop-continuação FAILS** (kill-PASS: misses são losers — física invertida vs limit, mas −71R) · **P3 skip-ceiling FAILS por vacuidade** (gates da base já excluem teto: corta 1/435) · **P4 skip-capx KILL** (runner-kill 14) · **P5 budget episódico PROMISING como contabilidade** (DD q95 −57%, pior mês −5,0→−1,8, NET −51%) · **P6≡P1**. STREAK_ANATOMY: 97% da dor de streak é cluster episódio/calendário. **Nenhuma hipótese move WR_liq/streak** (falhas FN pré-existentes da base). Docs: BRIEF/PREREG/DA/REPORT `..._20260703.md`. Continuidade = decisão Cris.

### Lab A (spec original) — Trigger geometry (confirmação mais barata) — lever nº 1
- **Objetivo:** reduzir o custo estrutural de confirmação (~2,1 ATR mediano) sem perder a causalidade do fundo confirmado.
- **Hipótese:** existe geometria de confirmação (reclaim de nível · altura fixa tipo 5ATR A2 · CHoCH-15M/HTF · close acima de barra-chave) que entra mais perto do flush low, preservando os 53 runners e o WR da base.
- **Dados:** primitives atuais (RAW-only); reusar substrato de candidatos pré-gate.
- **Null/validação:** comparação pareada por EPISÓDIO (mesmos fundos, gatilhos diferentes) + null de geometrias aleatórias de altura equivalente + jackknife-por-episódio; runners preservados = critério de 1ª classe.
- **Sanity:** 3 exemplos visuais pass/fail/borderline reconciliados com prints; zero look-ahead (confirmação só com barras fechadas).
- **Forbidden interpretations:** WR maior por SL mecanicamente mais perto ≠ edge (lição L1); não comparar por WR isolado — painel completo sempre.

### Lab F — Episode Risk / Streak / DD / WR — ✅ EXECUTADO 2026-07-03: **NO_STREAK_DD_WR_SOLUTION**
Camada de gestão de exposição (autorização Cris; discovery 7 agentes + 13 configs congeladas × 2 baselines BASE/BASE+P1, máquina de estados causal exit-realizado). **Nenhuma das 26 variantes bate nulls** (p 0,13-0,98); única que atinge WR/streak FN (F2_max1c: WR 50 · stk −5) = FAIL por amputação (34% retention, 70% dos runners mortos). **Sub-achado: F4 sizing 1,0/0,5/0,25 por chain_pos causal = RISK_CONTROL_FOUND_NOT_EDGE** (93-94% retention, DD −12/−18%, zero runner-kill — candidato a camada de conta prop, decisão Cris). F8 continuation-abort PIORA WR e streak. Mecanismo unificador: **loss-clusters e runner-bursts são os mesmos clusters (fail-then-fire)** — regras chaveadas em losses recentes taxam os trades que pagam o sistema. DA: 1 bug (F3 pausa) + 2 desvios prereg (F5) corrigidos. **Eixo WR/streak segue NÃO-RESOLVIDO após Labs A+F** (estrutural do perfil swept-runner). Docs: `XAU_15M_LONG_LAB_F_EPISODE_RISK_STREAK_DD_WR_{PREREG,DA,REPORT}_20260703.md`.

### Lab B — Context elimination (posição-no-regime + supply overhead) — lever nº 2
- **Lentes:** room_above (24h) · posição fundo/meio/topo no box do regime v5 (análogo phase34 L2) · banda de supply do regime anterior.
- **Formato:** convergência ASSIMÉTRICA de eliminação (estilo L2: SKIP quando ≥k lentes convergem) — **objetivo: cortar losers SEM cortar runners** (runner-kill ≈ 0 = critério duro).
- **Null:** cortes aleatórios de mesmo N (500 reps) + leave-episódio; sumR/DD/streak no painel completo.

### Lab C — SL_CONTEXT (estrutural, não pad)
- SL no **nível estrutural de contexto** (low do box/zona de regime), não pad sobre o flush.
- **Risco prop-firm em 1ª classe:** medir distribuição de risco/trade em ATR (L2 mostrou 35% >4ATR = inviável sem cap); sanity contra sumR E risco máximo; viabilidade operacional/streak como árbitro.

### Lab D — Re-entry de EPISÓDIO (pós-stop)
- Unidade = EPISÓDIO, nunca trade isolado; trigger de re-entry pré-definido (sem jardim de bifurcações).
- **Null anti-circularidade obrigatório:** baseline de bounce ambiente ≥ X ATR pós-low em 96b (o furo apontado pelo DA) + desconto do R já monetizado por entradas subsequentes existentes.

### Lab E — Slippage/cost (pendência OFICIAL_FN) — ✅ EXECUTADO 2026-07-03: **COST_ROBUST**
SB realista ($0,80 RT): +233,6R (80% do bruto), r/DD 16,4, todos anos+, runners 53→51. Caveat: 2024/risco-$-baixo frágil (modelo conservador). Condição de custo do OFICIAL_FN **PASSED** (marcação do status = decisão Cris). **Regra nova transversal: labs futuros reportam painel bruto E líquido-SB.** Docs: PREREG/DA/REPORT `XAU_15M_LONG_LAB_E_SLIPPAGE_COST_*_20260703.md`.
- Cenários: spread/slippage por sessão (Ásia pior) · custo fixo por trade em R (risco mediano ~2,1 ATR → custo relativo) · sensibilidade do painel a 0,05/0,10/0,20R de custo.
- Campos: entry/SL/exit reais da base; **manifesto próprio antes da execução** (fonte, período, predicados, exemplos).

## 6. Lab ordering recommendation

**E → A → B → C/D.** Justificativa para E primeiro (alternativa à ordem sugerida A→B→E): E é a **única pendência do OFICIAL_FN da base já aprovada**, é barato (sem novo desenho, só custo sobre trades existentes) e **re-rankeia os demais labs** — se o custo comer o edge dos trades de risco alto, Lab A (que reduz risco/trade) ganha ainda mais prioridade e Lab C (que tende a aumentar risco/trade) perde. A e B seguem em paralelo conceitual (A mexe no gatilho, B na eliminação); C/D só depois, informados por E. Ordem final = decisão do Cris.

## 7. Required manifests (nenhum lab sério sem)

Gate manifest (predicados exatos em linguagem natural E código) · RAW/source-field mapping · null desenhado ANTES de rodar · sanity checks (pass/fail/borderline com timestamps) · output spec · **DA adversarial antes de reportar** · painel completo sempre · unidade = episódio.

## 8. Plotting requirement

Qualquer visual futuro passa pelo **skill plotting-canon** (preflight completo, NO_CLEAR default, sem screenshot, report contract). Nenhum chart/clear/screenshot sem autorização explícita por execução.

## 9. RAW extension relation

Base atual cobre até **2026-05-25**; o gap mai→jul-2026 **não bloqueia** Labs A/B/E preliminares (rodam sobre a cobertura existente). Extensão RAW = bloco separado já planejado (`RAW_15M_EXTENSION_PLAN_MAR_JUN_2026.md`), com 5 aprovações próprias. Labs re-rodam sobre a base estendida quando existir (BEAR tardio mar-mai/26 entra aí).

## 10. Acceptance criteria

- [x] Plano criado · [x] **zero execução de lab/backtest** · [x] zero mudança em estratégia/gates/detector · [x] zero RAW/coleta/plot/chart/produção · [x] proibições listadas · [x] manifests obrigatórios definidos · [x] commit local sem push sem autorização.
