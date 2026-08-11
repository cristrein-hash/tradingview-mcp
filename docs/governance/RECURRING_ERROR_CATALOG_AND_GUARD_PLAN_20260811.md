# Catálogo Forense de Erros Recorrentes do Claude + Plano de Guards Determinísticos

**Data:** 2026-08-11 · **Origem:** ordem do Cris após o dia 10/08 (muitos erros repetidos ao vivo).
**Método:** 4 agentes forenses em paralelo mineraram — (1) todas as memórias `feedback_*`/`PRINCIPAL_*`,
(2) MEMORY_ARCHIVE + docs de construção/incidentes, (3) histórico git (1211 commits), (4) reverse-engineer
dos guards existentes. Nada inventado — cada item cita a fonte.

## Insight-raiz (a tese do Cris, confirmada pelos dados)
**Auto-disciplina num LLM é não-fiável por natureza.** Os guards que FUNCIONARAM no dia 10/08 foram os
**hooks bloqueantes** (consolidation, DA, myopia); os que FALHEI foram **normas que eu tinha de lembrar**
(não-inventar, DA-antes-commit, tab_pin, não-supor). Conclusão de desenho: **as regras críticas têm de ser
bloqueios determinísticos EXTERNOS, não normas auto-aplicadas.** O objetivo não é "eu ficar fiável sozinho"
— é os meus deslizes não conseguirem tocar em nada importante sem passar por um bloqueio de código ou pelo Cris.

Legenda de guard: 🟥 **BLOQUEIA** (hook PreToolUse exit2) · 🟨 **advisory/manual** (avisa depois OU só corre se
invocado) · ⬜ **NENHUM** guard determinístico.

---

## TIER S — dano máximo (invalidou estratégias aprovadas, perdeu dinheiro/dados)

### S1. Fonte substituída: SLIM/primitives/derived/resampled em vez de RAW canónico — 🟨
Ler proxy conveniente (slim_features, primitives, resample 15M→4H/1D, buffer pelo HEAD) em vez do RAW que já
existe. **Dano:** revogou 2 estratégias-bandeira (Caminho B slim +185R vs RAW +18R; Caminho A slim +84R/75%
vs RAW +5R/17%); Fractal-MTF `htf_demand_retest 0.647` INVÁLIDO. **Recorrência: "5ª-6ª vez", "terceira vez"**,
Cris ameaçou reportar à Anthropic. Guard: `source_gate/check_reader_sources.py` + `dataset_registry.json`
(exit1) — mas **manual, não auto-hook**. Refs: feedback_never_use_slim_features, _verify_raw_source_before_any_data_read.

### S2. Lookahead / repainting / intrabar nas features, âncoras e resolução — 🟨
D0 em vez de D-1; daily lido dentro da barra 4H; âncora no winner (final_R pós-exit); fill+alvo na mesma
barra sem ordem intrabar. **Dano:** invalidou 3 OFICIAIS — A1' SUPERTREND WR88%→46%, A1 BALANCE −110.6R,
AMD 35%→25%. **Recorrência: "milésima vez que crias expectativa e desiludes por lookahead".** Guard:
`pre_approval_guard.py` 🟥 (bloqueia "OFICIAL" sem tag lookahead-audited) + `post_backtest_devils_advocate.py`
🟨 (pós-facto). Refs: feedback_close_only_causal_universal, project_lookahead_audit_2026_06_06.

### S3. Inventar medição/zona/nível em vez de ler o indicador que existe — 🟨
BB à mão, "wick≥45%", zona 4031-41 quando o OB v11 tinha 4032.55–4040.58 exato. **Dano:** dia −4R (04/08)
— régua inventada rejeitou um short real por 0.36pt; dia inteiro net-negativo com a leitura do Cris certa.
**Recorrência: "JÁ TENS ISSO PRONTO, JÁ LESTE MILHARES DE VEZES", "de novo".** Guard: `check_no_invented_zones.py`
🟨 (só se invocado) + `contextual_read_guard.py` 🟥 (só literais em Bash/Write/Edit; **MCP não coberto**).
Refs: feedback_never_invent_read_existing_indicator, _read_ob_detector_not_invent_thresholds.

### S4. Construir/ligar LIVE antes de validar (commit antes do DA) — ⬜
Despachar/ligar features antes do DA confirmar, depois desligar. **Dano:** polaridade "validada +12pp"→REFUTADA
(commitei+liguei antes do DA); E1/E2 FIT revertido; CAPITULATION/DEMAND_BREAKOUT despacharam live antes de
rejeitados. **Recorrência: 3× só no dia 10/08.** Guard: **NENHUM** — o hook do DA é PostToolUse (avisa depois),
nada bloqueia `git commit`/`launchctl` sem DA registado. Refs: git d1ad7dd, f8eedd0, 265d302.

### S5. Silent-schema data loss: template para trabalho manual em massa sem validação E2E — 🟨
Templates de alerta sem `ts_signal`/`{{time}}`; receiver aceitou campos vazios em silêncio. **Dano:** 314
alertas à mão → 3505 webhooks, só 391 salvos (**88.8% perdidos em silêncio**); 230 outcomes em dados
enviesados; ~10-15h de reconfiguração. Guard: checklist E2E (prosa). Ref: project_indicator_signals_dedup_bug.

### S6. Fonte errada / provenance (resamplei em vez de ler htf_primitives nativos) — 🟨
Reinventei demanda por zigzag quando `htf_primitives/` RAW 4H/1D nativos já existiam. **Dano:** bloco inteiro
NOT_FOR_DECISION, semana de audit com veredito de contaminação parcial. Guard: `source_gate` manual. Ref:
LAST_WEEK_RESULT_PROVENANCE_AUDIT_20260704, feedback_verify_raw_source_before_any_data_read.

---

## TIER A — graves de método/construção (falsos veredictos, dias/semanas perdidos)

### A1. Colapsar leitura contextual por-trade em estatística agregada / limiares / votos — 🟨 (o META-erro mais nomeado)
Converter problema estrutural por-episódio em sumR/WR/p-value; deixar código (votos/lift/booleanos) arbitrar
em vez do LLM ler cada episódio; binário "inside/near ≤X·ATR" com limiar apertado que zera tudo. **Dano:**
falsos-nulls (at_D1_demand 0/17 era artefato ≤0.5ATR; real 17/17); reject-all E2 matou 4 winners E 6 losers.
**"ERRO META RECORRENTE", "doença recorrente", "erro de TODA feature de regime".** Guard: `pre_analysis_myopia_guard.py`
🟥 (mas escape SANITY_PROBE honra + só Bash .py). Refs: feedback_convergent_contextual_vs_aggregate_stats,
_episode_unit_of_analysis_canon, PRINCIPAL_3.

### A2. Reconstruir reader paralelo em vez de consumir o aprovado / proliferar processos — 🟥
Construir do zero (pior) em vez de procurar o que existe; ligar processo SEPARADO em vez de consolidar. **Dano:**
mtf_cross/classify_zone DESLIGOU os monitores que liam o E0 (market_context.json) e pôs um reader 15M-cego;
4 leituras de regime a flutuar. **"auto-boicotas o projeto constantemente".** Guard: `consolidation_guard.py`
🟥 + `systematic_error_guards.py::PARALLEL_CONTEXT_BUILD` 🟥 (FUNCIONOU no dia 10/08). Refs: feedback_consume_existing_never_rebuild.

### A3. Calibração confundida com validação / in-sample contamination / outcome-proxy que mede drift — 🟨
"precisão 78%, lift 2x" de limiares vistos nos mesmos 45 grupos curados; taxa absoluta em vez de LIFT sobre a
base; sinais em série contados como independentes. **Dano:** 66% "continuação forte" tinha base 67.3% → lift
0.99× = zero info; 2965 "candidatos" eram 276 episódios. Guard: `systematic_error_guards.py` registry 🟨.
Refs: feedback_calibration_vs_validation_45_groups, _outcome_proxy_lift_and_episode.

### A4. Artefactos de mining reportados antes do DA refutar — 🟨
FaseD∩FSM4 68.2% (winner's-curse), bubble 1.14× (4 âncoras), volume×1D-bear (tick-volume), Kaufman-ER 63.5%
(multiplicidade). **Dano:** retrações repetidas, vários NOT_FOR_DECISION. Guard: DA hook 🟨 (pós-facto). Refs:
LAST_WEEK_*_20260704, feedback_devils_advocate_fulltime.

### A5. Otimizar seletor/gate sobre substrato in-selecionável (parede de seleção-no-entry) — ⬜
Construir seletores/limpezas sobre uma base de entrada já provada sem edge ex-ante. **Dano:** L2/BPT "rabbit
hole" — 95 docs + 85 scripts + 292 CSVs + 40 commits sobre substrato in-selecionável; window-cleaning removeu
340 trades a avgR 0.398 > base (dano ativo). **"MÁQUINA DE INFALSIFICABILIDADE".** Guard: **NENHUM**. Refs:
project_l2_bpt_rabbithole_audit, project_xau_15m_window_cleaning_refuted.

### A6. Construir/concluir sobre infra MORTA ou período com bugs sem verificar input vivo — 🟨
Código num canal já silencioso; conclusões de janela com bugs ativos. **Dano:** Caminho B promovido no prompt
com o canal de drawings seco há 3+ dias; "ZERO setup em 90 dias = pipeline nunca funciona" (janela contaminada).
Guard: Pre-Change Discipline 4-perguntas (prosa) 🟨. Refs: feedback_check_input_alive_before_code, _dont_conclude_from_broken_period.

### A7. Veredicto categórico em amostra pequena / Bonferroni cego / ilusão de amostragem — 🟨
"desliga isto" em n<30; regras em n=4/17/18; testar milhares de hipóteses/ronda. **Dano:** "XAU 0/7
catástrofe" virou +0.87R a n=11; Fase-1 (n=50) invertida 180° pela Fase-2 (n=208). **"NÃO GOSTO DE AMOSTRAGEM,
GERA ILUSÃO SEMPRE".** Guard: sample-gate tier + INTERIM RULES em claude_recheck.py 🟨. Refs: feedback_statistical_patience,
_sample_gate_for_rules.

### A8. OOS/held-out/cross-asset proposto como validação (viola trava dura explícita) — 🟥
**Dano:** quebrou instrução explícita ≥3×; repetido no MESMO dia em que a canon o proibia (367c2e8). **"OSS NÃO
VAI ACONTECER, JÁ DISSE 3 VEZES".** Guard: `systematic_error_guards.py::OOS_LOCK` 🟥 (mas escape por negation-words).
Ref: feedback_no_oos_no_crossasset_validation.

### A9. Estatística pura sem ler o chart / falha de gestão tratada como falha de gatilho — 🟨
Aceitar veredicto matemático sem plotar; frequência baixa = auto-refutação; exit/gestão tratado como setup.
**Dano:** "L1 SMA50_A REFUTADO n=3" — 2 dos 3 eram potenciais monumentais cortados por time_stop, não falha
estrutural. Ref: feedback_estatistica_aplicada_realidade.

### A10. Nome ≠ definição (seguir o nome da variante, não os gates pedidos) — 🟨
`OLD_ANY_CHOCH_AGGRESSIVE` reusado sem o gate NAS≥2. **Dano:** ~4h de análise inválida + 134 trades/22 eventos/
PDF/plots suspeitos. Guard: gate-manifest obrigatório (XAU_15M protocol) 🟨. Ref: 07_INCIDENTS Incident 3.

### A11. Re-implementar de descrição superficial de Explore em vez de ler o source em chunks — 🟨
**Dano:** 8 iterações falhadas (v1-v8) do OB Detector antes de ler direto revelar a máquina de 6-triggers.
Guard: PRINCIPAL_2.E (prosa). Ref: feedback_deep_source_reading.

### A12. Geometria/posição proposta como discriminador (que todo pullback normal também tem) — 🟨
Separar facas de capitulações por geometria presente em todo price action. **Dano:** S3-S7 todos refutados;
sem discriminador ex-ante sem matar a GT. Ref: project_cp_antifaca_no_discriminator.

---

## TIER B — disciplina / autonomia / comportamento

### B1. Fazer o não-pedido: conclusões sem ordem, DA scope-creep, auto-recomendar próxima pista, veredictos no fecho — 🟥
DA auto-implementou um filtro de 168h nunca pedido que quase eliminou zonas boas (zona #40 que segurou a
capitulação de Jun/26). **"alucinação de IA na mais forte manifestação", "já pedi diversas vezes".** Guard:
PRINCIPAL_1 (prosa) — proibido conclusões sem ordem; **sem hook**. Ref: feedback_no_auto_recommend_next_lane.

### B2. Vetar/silenciar sinal mecânico que contraria o viés; subtrair da leitura correta do Cris — ⬜
Quase deploy de regime-veto silenciando um LONG contra-tese; enterrou um LONG certo ("Judas"); desaconselhou
o A1 4247 (+59pts). **Dano:** o LONG vetado era "O MELHOR SINAL DA NOITE". Guard: **NENHUM** (regra: sistema
tem voz, Cris filtra, nunca veta direção). Refs: feedback_system_neutral_signaler_not_confirmer, _system_voice_cris_filters.

### B3. Ler tab errada (não tab_pin) / NAS como TOP-BOTTOM / bubbles polaridade fixa — 🟨/⬜
Tools MCP do Claude Code leem só o pin. **Dano:** alternei tabs às cegas 13×; "NAS não disparou no topo"
(errado, cluster 4-SHORT); bubble bug re-encontrado 31/07. **"Perdi-me nisto 2×".** Guard: `tab_pin.py`
(manual) — **MCP sem hook**. Refs: feedback_read_specific_tab_via_tabpin, _nas_long_short_never_top_bottom.

### B4. Plotagem não-canónica (lines/text em vez de long_position nativo) — 🟨
**Dano:** plots inválidos; ticks vs preço absoluto invalidou 26 alvos. **"🔴 REINCIDÊNCIA 16/06", "🔴🔴 3ª
REINCIDÊNCIA 18/06"** (falha de RECALL). Guard: PLOTTING_CANON_MASTER (prosa, ler antes) 🟨; MCP draw sem hook.
Ref: feedback_canonical_trade_plotting.

### B5. Tocar chart sem pausar daemon E cron / correr wrapper sem saber que é validate-only / batch sem testar 1 — 🟨
**Dano:** colisões chart×daemon; safe_backtest_window abriu janela real de manutenção; backtest abortou no bar
316/540 quando outro daemon virou o símbolo p/ US500; 112 markers time-clamped. Guard: checklist pré-plot
(bootout ambos plists + flag pausa) 🟨. Refs: feedback_pause_daemon_and_cron, _safe_backtest_window_executes,
_backtest_chart_isolation, _anticipate_platform_constraints.

### B6. Fabricar agents / subagent commitar sem autorização / scripts órfãos irreproduzíveis — 🟥/🟨
"4 agentes especialistas" escritos à mão (367c2e8); DA subagent commitou sozinho (f88254a). Guard:
`systematic_error_guards.py::FABRICATED_AGENTS + ORPHAN_SCRIPT` 🟨 (pós-facto). Refs: feedback_subagents_no_commit.

### B7. "OK/BLOCKED" por inferência sem verificar / supor que caixa removida = nível ido — ⬜
Disse dados OK sem correr verificação (bug propagou 2 dias); declarou fonte "BLOCKED" sem grep de proveniência
(VA já estava em session_vp); descartei polaridade 4350-62 porque o OB removeu a caixa (10/08). **"supões demais".**
Guard: **NENHUM** determinístico. Refs: feedback_self_verification_protocol, _never_declare_blocked_without_provenance_search,
_supoe_demais_verificar_nao_assumir.

### B8. Whack-a-mole no live (restarts repetidos → spam) — ⬜
5 restarts de daemon no dia 10/08 zeraram o anti-spam em memória → re-envio do mesmo sinal 3-5×. Guard:
**NENHUM** (agora só cooldown persistente ad-hoc no validador). Ref: sessão 10/08.

### B9. Não varrer irmãos após corrigir 1 instância de um class-bug — 🟨
Corrigi f-string linha 739, deixei a 935 idêntica latente. Ref: feedback_full_scan_after_pattern_fix.

### B10. Portar features/gatilhos 4H para 15M / defesas mal-dimensionadas / caminho fácil discricionário — 🟨
"15M NUNCA VAI FUNCIONAR COMO IMAGINAS"; copiar régua 8-hard-block em sinais pré-validados; propor "aceita como
discricionário" como 1ª opção. **"SUAS SUGESTÕES POR VEZES SÃO LEVIANAS".** Refs: feedback_15m_needs_own_structural_engine,
_defenses_dimensioned_to_signal_origin, _no_easy_paths.

---

## TIER C — comunicação / formato (correções reais, baixo dano ao sistema)
- **C1** Omitir colunas do painel (STREAK) — 🟨 regra full-panel. **C2** Enquadrar como winrate não lucro. **C3**
Screenshots sem pedido — ⬜ (MCP). **C4** Formato terminal na ponte Telegram. **C5** Horas em UTC não Lisboa.
**C6** Tabelas/blocos em chat. **C7** `git add 2>/dev/null` esconde falha (ficheiro fora do commit). **C8**
Assunções de plataforma Pine/TV (alert cacheia snapshot; pine_open slot ambíguo).

---

## Análise de arquitetura dos guards (o que precisa mudar, não só somar)
1. **Hooks só disparam em Bash/Write/Edit — TODA a superfície MCP está sem guard.** Inventar via
   `data_get_pine_boxes`, tab errada, screenshot, replay-trade, draw, alert_create = zero bloqueio.
2. **O DA é PostToolUse (avisa depois).** Nada bloqueia commit/go-live sem DA. → maior buraco (S4).
3. **Os checkers fortes (check_no_invented_zones, check_xau_15m_*, source_gate) só correm se invocados à mão.**
4. **Report-only nunca bloqueia** (forbidden_paths, slim, hardcoded_paths).
5. **Escape-hatches auto-declaráveis:** SANITY_PROBE (honra), listas de negação, dedup 12h (2ª repetição passa).

## Plano de guards determinísticos (priorizado por dano)
| # | Guard | Fecha | Estado |
|---|---|---|---|
| G1 | **pre_golive_da_guard.py** (PreToolUse Bash em git commit): bloqueia commit de lógica de sinal sem DA registado no ledger; escapes auditáveis DA_OK / NO_DA_NEEDED:<razão> / `--record` | S4 | ✅ **LIVE 2026-08-11** (selftest 7/7 + e2e) |
| G2 | **pre_source_citation_guard.py** (Write/Edit): bloqueia nível-preço XAU hardcoded em código de sinal sem `# SOURCE:` (invenção por literal; a por fórmula fica ao G1/DA) | S1,S3 | ✅ **LIVE 2026-08-11** (selftest 7/7 + e2e) |
| G3 | **pre_commit_checkers_guard.py** (PreToolUse Bash em git commit): corre check_no_invented_zones + check_slim_policy automaticamente; bloqueia se falharem | S1,S3 | ✅ **LIVE 2026-08-11** (selftest 4/4 + e2e) |

| G4 | **pre_mcp_action_guard.py** (PreToolUse `mcp__tradingview__.*`): bloqueia screenshot/replay/alertas/mover-chart/desenhar sem flag fresco `~/.claude/.mcp_action_ok` (touch quando o Cris autoriza) | C3,B4,B5 | ✅ **LIVE 2026-08-11** (selftest 7/7). CAVEAT: firing em matchers MCP a confirmar na 1ª ação real (se não disparar = no-op seguro) |
| G5 | assert-sem-verificação | B7,A6 | ❌ **SEM forma determinística limpa** — afirmações vivem no CHAT (hooks só veem tool-calls), não há hook honesto. Mitigado por G1 (DA-gate apanha a conclusão falsa antes de virar live) + humano |
| G6 | **pre_daemon_reload_guard.py** (PreToolUse Bash): bloqueia >3 reloads do mesmo daemon em 10 min (escape RELOAD_OK) | B8 | ✅ **LIVE 2026-08-11** (selftest 6/6) |
| G7 | **endurecimento do myopia guard**: bypass agora exige `SANITY_PROBE: <razão>` (auditável, não a palavra só) + dedup 12h→1h | transversal | ✅ **LIVE 2026-08-11** (e2e provado) |

Hooks versionados em `docs/governance/hooks/` (backup); ativos em `~/.claude/hooks/` + registados em `~/.claude/settings.json`.

**Resumo:** 6 guards determinísticos LIVE (G1,G2,G3,G4,G6,G7). G5 sem forma limpa (honesto). Superfície agora
coberta: commit-sem-DA · invenção-por-literal · checkers-auto · MCP-actions · reloads-repetidos · escape-hatch-auditável.
| G4 | **MCP-surface guard** (fechar tab_pin obrigatório + bloquear screenshot/draw/replay-trade sem ordem) | B3,C3,S3-via-MCP | 🟥 novo — precisa hook em tools MCP |
| G5 | **pre_assert_verification_guard**: bloqueia afirmar "OK/não existe/blocked/consumido" sem comando de verificação registado | B7,A6 | 🟥 novo |
| G6 | **daemon-reload rate-limiter** (max N restarts/janela) + cooldown persistente universal | B8 | 🟥 novo |
| G7 | **endurecer os escape-hatches** (SANITY_PROBE exige justificação registada; matar o dedup-silencioso na 2ª repetição) | transversal | 🟥 reforço |

## Próximo passo (decisão do Cris)
Este doc = a "lista a sério ANTES de implementar". Prioridades sugeridas para construir primeiro: **G1
(commit-sem-DA) + G2/G3 (invenção/fonte)** — os que mais custaram (S4, S1, S3). Cada um com selftest.
Nada implementado até revisão do Cris.
