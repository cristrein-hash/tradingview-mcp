# XAU Strategy Reevaluation Plan — pós re-arquitetura (2026-06-16, read-only)

## 1. Executive summary
A re-arquitetura está estável (L1 EMA21 Continuation operacional, scheduler ativo, regime_L1_v4, Forward Outcome Layer F1/F2, event store vivo, RAW source-of-truth, legacy perigoso neutralizado). Este plano **inventaria e prioriza** as estratégias XAU a revisitar **sob a nova arquitetura**, sem backtest e sem tocar produção. **Recomendação P0: revalidar o Caminho B (bottom-catcher 4H LONG) em RAW sob gate manifest novo** — é o candidato de maior valor, ortogonal à L1, com gates claros, packet já versionado e validável em RAW. Próximo bloco = **preparar o gate manifest do Caminho B** (não rodar backtest ainda). Regra-mãe: *live signals geram hipótese; edge só valida em RAW; nome de variante não é prova — verificar gates reais.*

> **Nota de status (verificada no catalog, não no nome):** nenhuma estratégia XAU está `LIVE`. `XAUUSD_4H_BREAKOUT_CONTINUATION` aparece como `validation_status=ACTIVE_CANDIDATE` mas **não está deployada** e corresponde ao breakout legacy **neutralizado** (recheck:931 sem SETUP_VALIDO). A única XAU operacional é a **nova L1** (`XAU_4H_LONG_CONTINUATION / L1_EMA21_CONTINUATION`), que **não está no catalog.json** (é módulo da nova arquitetura).

## 2–10. Famílias / estratégias (status real · conhecimento · hipótese · razão · contaminação · dados · gates · gaps)

### F1 — XAU 4H LONG Continuation (ANTIGA)
- **Veredito Caminho A L1 v1 F4+F5 (registrado 2026-06-16, deep dive `docs/XAU_4H_CAMINHO_A_L1_F4_F5_DEEP_DIVE.md`, commit 5a3aae9):** **`SUPERSEDED_BY_L1 / KEEP_REFERENCE`**. **NÃO reabrir como estratégia operável independente** salvo hipótese nova explícita; manter como lição histórica. Por quê (gates/processo/métricas, não por nome): **F4 inerte** (`sell≤7` nunca cortou nada); hipótese real = **EMA21_A + F5 (volume calmo)**; **reconciliação 11/16/38 nunca fechou** (config original perdida/auto-inconsistente); **R_CEIL 1.5ATR abortava 35/38** candidatos — removê-lo foi o conserto real do rebuild_v3; **KEEP-19 +32.6R = artefato in-sample / hindsight humano** (não é prova de edge). A **L1 refinada é superset estrita** (stack anti-extensão/zona + NAS SHIFT1 causal + RSI gate + SL estrutural + target +3R, scanner=runtime) — **nada operável em F4+F5 que a L1 não cubra**. ROI = validar/observar a L1 + reanalisar outras famílias, **não** reabrir F4+F5.
- **Status:** superseded pela **nova L1** (operacional). · **Conhecimento:** a L1 É a reconstrução fiel da continuation (regime BULL D-1 + EMA21>SMA50 + slopes + BOS + Custom OB v11 zone + body≥0.35 + F5 vol≤1.0; exit V_stair_A; RSI gate ≤−9.35). · **Hipótese reaproveitável:** já viva na L1. · **Razão:** config antiga era auto-inconsistente; reconstruída com stop/trigger humano. · **Contaminação:** baixa (substituída). · **Dados:** RAW XAU 4H. · **Gates:** os da L1. · **Gap:** a L1 live ainda marca `needs_base_confirmation` (confirmação estrutural completa é autoridade do scanner, ainda não no snapshot live). → **Não é reevaluation; é completar a L1** (trabalho de runtime, fora deste bloco).

### F2 — Caminho B (BOTTOM CATCHER 4H LONG) ⭐ P0
- **Status:** OFICIAL em memory (v1.5/v1.6), **KEEP_FOR_REVALIDATION**, **não migrado** à nova arquitetura. Packet versionado em `candidates/xau_4h_caminho_b_long/`. · **Conhecimento:** convergência 4 agents + anti_demand + rsi≤30 + circuit breakers + Dead Hours + Sweet Spot; exit V_stair (+ V_stair V6 climax conditional); filtro composto v1.6 (OB 1D demand / bubble LARGE / NAS_top5). · **Hipótese:** reversão/bottom-catch em capitulação — **ortogonal à L1 continuation** (atende o OBJETIVO PERMANENTE de múltiplas lógicas ortogonais). · **Razão de aprovação prévia:** robustness ±20% OK, walk-forward 3/3, jackknife estável (em memory). · **Contaminação:** **média-baixa** — foi validado em slim e depois re-checado; o lookahead audit (2026-06-06) atingiu o Caminho A, **B v1.5 confirmado clean (SHIFT1)**. · **Dados:** RAW XAU 4H (existe). · **Gates conhecidos:** documentados e específicos. · **Gaps antes de backtest:** (a) **gate manifest novo** (predicados exatos sobre RAW, mapping bubble plot_id, close-only-causal/SHIFT1); (b) re-rodar sob checklist 15 problemas (≥12/15); (c) walk-forward externo pendente (EUR/USOUSD como teste de especificidade, NÃO como refutação).

### F3 — XAU 1H LONG (DEMAND_RECLAIM_REENTRY) — P1
- **Status:** PAUSADO (hipótese oficial v1.1), KEEP_FOR_REVALIDATION; **revisar depois, NÃO ativar agora** (regra do bloco). · **Conhecimento:** L4 (cluster+CHoCH+maturity+lowest_risk+BE2R) + Secondary v2 + filtro drop_20_atr≤4.64; 51 trades, +62R fix. · **Hipótese:** reentrada demand reclaim intraday. · **Contaminação:** média (intraday, mais sensível a repaint/timing). · **Dados:** RAW XAU 1H (~11.800 bars, 3 blocos no HD externo). · **Gates:** documentados. · **Gaps:** revisão visual manual em curso (memory); gate manifest 1H; cuidado com look-ahead de features daily em barra 1H (mesmo bug do audit 2026-06-06).

### F4 — XAU 15M/30M potenciais — P2
- **Status:** POTENCIAL (só stubs `candidates/xauusd_{15m,30m}_long_pending.md` + datasets replay prontos). · **Hipótese:** intraday agressivo contextualizado por 1H/4H. · **Contaminação:** N/A (sem edge declarada). · **Dados:** datasets multi-TF coletados (externo). · **Gaps:** **não há hipótese formal** — precisa nascer de auction logic antes de qualquer backtest. · **Compat XAU-only:** sim, mas baixa prioridade vs 4H.

### F5 — DEMAND_BREAKOUT — DO_NOT_REOPEN (salvo hipótese nova)
- **Status:** REJECTED (catalog + visual review: comprava em zonas que agiam como venda). · **Razão:** data-only insuficiente; hipótese deve nascer de auction logic. · **Contaminação:** alta. · **Reabrir só com** hipótese auction-theory nova e clara. KEEP_REFERENCE.

### F6 — REVERSAL_CAPITULATION — DO_NOT_REOPEN (salvo hipótese nova)
- **Status:** REJECTED (PF 0.47 na revalidação canônica RAW; slim inflava). · **Contaminação:** alta (caso de slim enganoso). KEEP_REFERENCE.

### F7 — SWEEP / REVERSAL_DISCRETIONARY — P2 / KEEP_REFERENCE
- **Status:** RESEARCH, discricionária, n pequeno. · **Hipótese reaproveitável:** sweep+reentry é gatilho objetivo válido (mecanizável). · **Gap:** mecanizar critério discricionário + n suficiente. · **Contaminação:** média.

### F8 — BB Confluence (INTRADAY 15M) — P2
- **Status:** RESEARCH, forward test parado ~2026-04-30, NOT_DEPLOYED. · **Gap:** revalidar em RAW 15M; sem deployment. KEEP_FOR_REVALIDATION.

### F9 — L2 / BPT / Reason Atlas — P2 / KEEP_REFERENCE
- **Status:** RESEARCH_CORE (safety pack `~/Desktop/.../L2_REBOOT_SAFETY_PACK_2026-06-09`). · **Conhecimento:** o que separa good/bad é gestão/exit, não filtro de entrada; zona REVIEW irredutível no miolo BULL_EXPANSION. · **Gap:** eixos ortogonais + coleta; pesado. Não fit para XAU-only-3mo imediato.

### F10 — regime_B v1/v2/v3 — DO_NOT_REOPEN
- **Status:** MORTO, arquivado (`dead_regime_B_v3/`), substituído por `regime_L1_v4`. Não reabrir como autoridade operacional. KEEP_REFERENCE (caso-escola).

## 11. Prioridade
| Prioridade | Família | Racional |
|---|---|---|
| **P0 (próxima)** | **F2 Caminho B (bottom-catcher 4H)** | maior valor, ortogonal à L1, gates claros, packet versionado, RAW-validatable, XAU-4H, baixa dependência de legacy, clean no lookahead audit |
| **P0-infra (paralelo, runtime)** | **Completar confirmação base-rule live da L1** | desbloqueia candidatos operacionais reais (hoje `needs_base_confirmation`); habilita Forward Outcome F3 com amostra. **É runtime, não reevaluation** — exige Pre-Change Discipline |
| **P1** | F3 XAU 1H LONG (DEMAND_RECLAIM) | hipótese madura, RAW existe; revisar (não ativar); cuidado look-ahead daily→1H |
| **P2** | F4 15M/30M · F7 SWEEP · F8 BB · F9 L2/BPT | precisam de hipótese formal / mecanização / coleta antes de backtest |
| **KEEP_REFERENCE** | F1 continuation antiga (superseded) · F7 discricionário · F9 L2 · F10 regime_B | conhecimento preservado, sem reabertura ativa |
| **DO_NOT_REOPEN** | F5 DEMAND_BREAKOUT · F6 REVERSAL_CAPITULATION · F10 regime_B autoridade | rejeitadas com razão forte; só com hipótese nova clara |

## 12. Próximo bloco recomendado
**Preparar o GATE MANIFEST do Caminho B (F2)** — documento de pré-registro (predicados exatos sobre RAW, mapping bubble plot_id confirmado, convenção close-only-causal/SHIFT1, exit policy, janela TRAIN/VAL/TEST, critérios do checklist de 15 problemas ≥12/15, Wilson lower ≥45%, Bonferroni da rodada). **Sem rodar backtest** — só o manifest. Backtest sério só no bloco seguinte, após o manifest aprovado por você.

**Riscos principais a vigiar:** (1) look-ahead via features daily consultadas em barra 4H (bug sistêmico de 2026-06-06 — exigir SHIFT1); (2) confiar em números slim/in-sample — validar só em RAW; (3) calibração vs validação (45 grupos = calibração, não prova de edge); (4) contaminação de produção — nada disto toca a L1 operacional, scheduler, Telegram ou broker.

---
_Plano read-only. Nenhum backtest rodado, nenhuma estratégia implementada, produção não tocada. Fontes: catalog.json, XAU_LEGACY_KNOWLEDGE_INDEX, BOOTSTRAP canônico, Forward Outcome SPEC/ROADMAP, UNTRACKED_ARTIFACTS_INVENTORY, candidates/, memory protocols._
