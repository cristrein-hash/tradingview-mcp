# XAU 4H BREAKOUT / D1a — Mechanical Rebuild Round 1 Results

**Data:** 2026-06-17 · **Tipo:** rodada mecânica de reconstrução · **NOT_VALIDATION — hypotheses-only.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT. Sem Caminho B, sem mudar conceito.
**Gross R (sem custos).** Read-only w.r.t. RAW/produção. Nenhuma plotagem, MCP/chart, Telegram, broker.

---

## 1. Executive summary

Primeira rodada mecânica controlada do BREAKOUT/D1a, reconstruída **RAW-first** (4H RAW 2016-2026, 15.434 barras, grid único 02/06/10/14/18/22 UTC; RSI/RSI_MA lidos do study TV capturado, 98,4% coverage; regime de OHLC; **D1a via regra CAUSAL `close_time≤bar_open`**). 8 variantes (V0-V7), predicados **congelados** do manifest, **zero otimização**.

**Resultado-chave de integridade:** o **trade-level SHIFT audit deu 0 leaks** em V6/V7 (same_day_selected=0, close_time_gt_bar_open=0, missing_daily=0) — o alinhamento causal do D1a está correto trade-a-trade. **V6/V7 não bloqueados.**

**Sinais (hipóteses, gross):** o trigger sozinho (V0) já é positivo (+90.96R, PF 1.55); o regime completo (V5) concentra qualidade (n=111, PF 1.79, avgR 0.358, DD -8); **D1a sobre o regime completo (V7)** poda ~23 trades e sobe PF 1.79→2.20 / avgR 0.358→0.51 / DD -8→-5.45 (n=88) — direção consistente com a prosa D1a.

**Mas — DA full-time aplicado (§13):** V7 PF 2.20 é **superestimado** (11 targets carregam tudo, ~33% de sumR em 2025, gross, escolhido entre 8 variantes, n pequeno). Nenhuma métrica é edge. **Tudo permanece hipótese.** O conceito segue **vivo e em investigação** — esta rodada reconstrói fielmente e separa as camadas; não valida nem invalida nada.

---

## 2. Mentalidade de research / limites de interpretação

Esta é uma **rodada de reconstrução e exploração disciplinada**, não um julgamento final.
- Resultado **ruim** numa variante **não** invalida o conceito, nem autoriza descartar D1a ou BREAKOUT — indica que a camada precisa ser reinterpretada/separada/melhor testada.
- Resultado **bom** numa variante **não** valida a estratégia, nem autoriza promoção/live — cria hipótese para a próxima camada.
- Nenhum número aqui é "validação". Gross R, in-sample, sem OOS, sem custos, sem visual review, sem correção de multiplicidade.

---

## 3. Fontes

`gate_manifest.md`, `raw_field_mapping.md`, `design_test_plan.md`, `docs/…MECHANICAL_REBUILD_PLAN.md`, `…D1_SHIFT_AUDIT.md`, `…EMA1D_SHIFT_AUDIT.md`, `…INDICATOR_FEATURE_MAPPING_CANONICAL_AUDIT.md`, `docs/CANONICAL_TRADE_PLOTTING.md`, `generated/xau_1d_ema_features.jsonl`, dataset_registry, RAW 4H (3 blocos contíguos 240m).

---

## 4. Sanity checks (pré-execução)

- git status limpo (só `alert-bridge/logs/` + arquivos deste bloco) ✓
- generated EMA1D existe, sha256 `31d3b255…`, 3584 barras ✓
- RAW 4H source = 3 blocos contíguos 240m (grid único 02/06/10/14/18/22) ✓
- D1a usa CAUSAL (`close_time≤bar_open`), nunca ORIG ✓ (provado trade-level §6)
- produção intacta (verificada read-only) ✓
- py_compile OK; determinístico ✓

---

## 5. Variantes executadas

V0 trigger_only · V1 +ADX · V2 +EMA stack · V3 +ATR exp · V4 +slope · V5 full regime R1-R5 · V6 +D1a · V7 full regime+D1a. (Predicados em `gate_manifest.md`.)

---

## 6. Trade-level SHIFT audit

| Var | d1a_eval | same_day_selected | close_time_gt_bar_open | missing_daily | verdict |
|---|--:|--:|--:|--:|---|
| V6 | 517 | **0** | **0** | 0 | PASS |
| V7 | 121 | **0** | **0** | 0 | PASS |

**0 forming-daily leaks.** O engine usa `latest_closed_daily` causal; o leak de 83,3% da regra de produção (provado em `EMA1D_SHIFT_AUDIT`) foi corretamente evitado. V6/V7 **válidos** como hipótese (não bloqueados).

---

## 7. Métricas por variante (gross)

| Var | n | tgt | stop | be | time | sumR | avgR | PF | WR | maxDD | streak |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| V0 | 393 | 32 | 162 | 100 | 99 | +90.96 | 0.232 | 1.55 | 30% | -10.93 | 15 |
| V1 | 301 | 23 | 134 | 68 | 76 | +56.82 | 0.189 | 1.42 | 30% | -15.75 | 11 |
| V2 | 246 | 25 | 98 | 62 | 61 | +82.03 | 0.334 | 1.82 | 32% | -12.35 | 16 |
| V3 | 242 | 18 | 87 | 54 | 83 | +69.42 | 0.287 | 1.75 | 34% | -8.04 | 9 |
| V5 | 111 | 11 | 48 | 22 | 30 | +39.74 | 0.358 | 1.79 | 33% | -8.00 | 9 |
| V4 | 317 | 28 | 125 | 87 | 77 | +84.36 | 0.266 | 1.65 | 29% | -12.17 | 16 |
| V6 | 283 | 25 | 110 | 78 | 70 | +80.51 | 0.285 | 1.72 | 30% | -12.67 | 15 |
| **V7** | 88 | 11 | 35 | 18 | 24 | +44.65 | 0.507 | 2.20 | 35% | -5.45 | 9 |

**Pré/pós-2020 (sumR):** V0 12.6/78.3 · V5 9.3/30.5 · V7 11.4/33.2 (pós-2020 carrega).
**D1a kept/rejected (V5→V7):** V5 n=111 → V7 n=88 (~23 trades a menos sob D1a). ⚠️ não é subconjunto limpo: o `no-overlap` reordena elegibilidade ao remover trades, então "23 cortados" é o efeito líquido, não 23 D1a-fails isolados.

---

## 8. Reconciliação com legacy (não forçar match — RAW é source-of-truth)

| Referência | n | R | PF |
|---|--:|--:|--:|
| Revalidação v1 (slim, gross) | 115 | +25.3 | 1.48 |
| D1a prose (slim) | 90 | +32.2 | 1.86 |
| Sweep R_full_trend_regime (agregado, **net**) | 234 | +64.57 | 1.64 |
| **Este RAW V5 (full regime, gross)** | 111 | +39.74 | 1.79 |
| **Este RAW V7 (regime+D1a, gross)** | 88 | +44.65 | 2.20 |

**n direcionalmente alinhado** (V5 111 ≈ revalidação 115; V7 88 ≈ D1a prose 90). **sumR gross maior** que o slim — esperado. Divergências explicadas:
- **entry close→next-bar-open** (este usa next-open; spec original close).
- **grid 4H** (02/06/.../22 aqui vs outras fontes) muda qual barra é o breakout.
- **D1 CAUSAL vs ORIG/htf_1d** (este corta same-day forming que o legacy possivelmente vazava).
- **RSI lido do study TV** (não recomputado) vs **ADX/ATR/EMA Python**.
- **SLIM vs RAW** (legacy slim; este RAW source-of-truth).
- Sweep era **net @0.05R** e n=234 (grid/entry diferentes) — não comparável diretamente.

---

## 9. O que aprendemos (hipóteses)

1. **O alinhamento D1a causal funciona trade-level** (0 leaks) — a infraestrutura do D1a está correta e reutilizável.
2. **O edge do breakout não é monumental-dependente** aqui: target capado +4R, maxR=4.0 por construção. É **target-count-dependente e ano-dependente** (2019/2025 carregam) — fragilidade diferente, igualmente real.
3. **D1a sobre o regime completo poda losers e reduz DD** (V5→V7: PF↑, DD↓), mas o lift de sumR é pequeno e dentro de ruído (n=88).
4. **Cada camada de regime tem efeito distinto** (V1 ADX solo não ajudou nesta rodada; V2/V3/V4 sobem PF vs V0; V5 concentra qualidade). Decomposição preservada para estudo.
5. **Geometria +4R/BE@1R é um regime de exit diferente** da suite OFICIAL XAU 4H (+20R, monumental-dependent) — é uma ideia fresca, não comparável à suite.

---

## 10. O que ainda NÃO sabemos

- Se sobrevive a **custos/slippage** (gross; com 11 targets, V7 pode cruzar PF 1.0-1.3) — **maior ameaça** (DA top-1).
- Se sobrevive **OOS / walk-forward** e à **correção de multiplicidade** (8 variantes; V7 cherry-picked).
- Se o edge é **2 anos bons** (2019+2025) ou estrutural — stripar 2019/2025 e re-checar.
- **Sensibilidade do D1a ao vintage daily 1,72** perto de cruzamentos EMA (pode mudar trades borderline V6/V7).
- Reconciliação **visual** (nada plotado/revisado); ADX/ATR/EMA recomputados vs TV não reconciliados nesta rodada.
- Robustez do n (V5 111 / V7 88, ~11 targets) a **jackknife/no-topN/block-bootstrap**.

---

## 11. Subideias preservadas para próximas camadas

- **D1a como filtro de regime macro** (poda losers, reduz DD) — preservar, testar net + OOS + sensibilidade vintage.
- **EMA-stack + ATR-expanding (V2/V3)** como núcleo de qualidade com mais n que o regime completo — candidato a "V9 minimal" (sem inventar threshold).
- **Decomposição por camada** (cada gate tem efeito próprio) — base para pré-registro de qual subconjunto testar.
- **Geometria de exit alternativa** (+4R cap vs +20R) — estudo SL/exit dedicado (bloco futuro).
- Todas marcadas **HYPOTHESIS_ONLY** — nenhuma quantificada como edge.

---

## 12. Próximos blocos dentro BREAKOUT/D1a (permitidos)

- Plotagem canônica de subconjuntos escolhidos (V7 ou D1a-rejects) — `CANONICAL_TRADE_PLOTTING.md`.
- Estudo SL/exit (gross→net, +4R vs alternativas, time-stop).
- Relação fina BREAKOUT × L1 (sobreposição temporal).
- Refinamento de predicados **com pré-registro** + OOS/walk-forward + correção de multiplicidade.
- Investigação dos subfiltros preservados (§11).
- **Custos/slippage net** (prioridade DA).

(Cris decide qual/quando. Caminho B não recomendado.)

---

## 13. Devil's Advocate (subagente, incorporado)

DA executado via subagente ANTES da conclusão (hook `post_backtest_devils_advocate`). **Veredito: sem bug fatal; engine causalmente sólido; SHIFT audit legítimo. Tratar tudo como hipótese; V7 PF 2.20 superestimado.**

| Pergunta DA | Risco | Síntese |
|---|---|---|
| Look-ahead | **LOW** | D1a 0 leaks; EMA/ADX/ATR/swing em barra i fechada, entry i+1; swing exclui atual; RSI do close de i é causal. |
| In-sample | **MEDIUM** | predicados congelados, mas herdados de rodadas XAU 4H sobre os mesmos dados — não é OOS limpo. |
| Selection bias | **HIGH** | 8 variantes, V7 escolhido = cherry-pick; sem Bonferroni; PF 2.20 = CI larga. |
| Statistical power | **HIGH** | V7 n=88, 11 targets; ~33% sumR em 2025; flip de 2-3 targets derruba PF<1.5. |
| Execution risk | **MED/HIGH** | gross; 11 targets margem fina vs custos; entry next-open em breakout pode gapar; grid ≠ SVP_LUX. |
| Visual/cross-check | **MEDIUM** | nada plotado; ADX/ATR/EMA não reconciliados vs TV; D1a sensível ao vintage 1,72 perto de cruzamentos. |

**Top 3 que mudariam a conclusão:** (1) custos+slippage net; (2) OOS/walk-forward + multiplicidade + stripar 2019/2025; (3) sensibilidade D1a ao vintage daily.
**Correções aplicadas:** V7 reportado como point estimate gross/ano-concentrado, não edge; "ADX hurts" rebaixado a ruído de 1 rodada; D1a lift descrito como pequeno/dentro de ruído; conceito preservado como investigação.

### Checklist DA do bloco
- ✅ Nenhum threshold novo · ✅ D1a usou CAUSAL · ✅ SHIFT audit 0 leaks · ✅ V6/V7 não bloqueados (sem leak) · ✅ RAW não alterado · ✅ SLIM não usado como source-of-truth · ✅ Métricas NÃO chamadas de validação · ✅ Métricas ruins NÃO chamadas de invalidação final · ✅ Métricas boas NÃO chamadas de validação · ✅ Conceito preservado como investigação · ✅ Plot-ready gerado, NÃO plotado · ✅ Nenhum MCP/chart · ✅ Nenhum Telegram/broker · ✅ L1 intacta · ✅ Caminho B não recomendado.

**DA verdict: PASS (hypotheses-only).**

---

*Read-only w.r.t. RAW e produção. RAW 4H/1D lidos por streaming (não modificados). Gross R, in-sample, sem OOS/custos/visual/multiplicidade. Outputs em `results/` (bulk trades.jsonl + plot_ready.csv gitignored, regeneráveis; summary.json + shift_audit.json tracked). Nenhuma plotagem executada.*
