# Deep Dive — XAUUSD_4H_BREAKOUT_CONTINUATION / D1a (resgate arqueológico)

**Data:** 2026-06-16 · **Tipo:** reconstrução histórica/técnica read-only · **NOT_VALIDATION.**
**Mindset:** investigador, não executor. **Resgatar e preservar o máximo de informação útil antes de qualquer julgamento final.** A conclusão principal pode ser: *"ainda não sabemos, mas agora sabemos exatamente o que precisa ser testado."*
**Não fez:** backtest, scanner, alteração de código/catalog/strategy_rules/runtime/scheduler, Telegram, broker, MCP/chart, RAW, mover/deletar. Só este relatório foi criado.
**Regra deste bloco:** não decidir descarte final salvo prova objetiva de look-ahead/contaminação irreparável. Não confundir "não validado" com "sem valor". Não reduzir a família a uma métrica antiga.

---

## 1. Executive summary

XAUUSD_4H_BREAKOUT_CONTINUATION é um **breakout decisivo** (rompimento da máxima de 10 barras com corpo forte, em regime trending-bull com volatilidade expandindo) — **conceito distinto da L1** (pullback-and-go calmo). O **pacote legacy** (entrada catalog `ACTIVE_CANDIDATE`, Pine #01, canal recheck) está **contaminado** — rótulo enganoso, canal recheck `:931` **neutralizado 2026-06-15**, e **todas as métricas vêm de SLIM** (proibido como validação). Mas o **conceito** (decisive breakout + filtro de regime macro, especialmente o **D1a**) **não está refutado** — está em **reconstrução**, com várias camadas ainda por separar.

O que já sabemos com clareza:
- Os **gates são estruturalmente causais** (catalog marca `lookahead_free:true`; D1a usa o último 1D **fechado**, explicitamente no-lookahead). **Não há look-ahead provado** — diferente de A1 BALANCE / A1' SUPERTREND.
- O edge vem do **filtro de regime** ("quando NÃO operar"), não do trigger. O trigger sozinho (baseline) é fraco (+13R no_top5 negativo no sweep).
- **D1a** (direção macro 1D, causal) é a sub-ideia mais limpa e reaproveitável: melhora R + estabilidade + simplicidade, preservando targets, distribuído em janelas (não concentrado num regime).

O que ainda **não** sabemos (e agora sabemos que precisamos testar): comportamento em **RAW** (não slim), **OOS** real pós-2026-06, correção do **viés de seleção** (vencedor de sweep de 22 configs), **visual review 100%** (só 25 D1a-rejects revisados), e a **separação limpa** do conceito vs o pacote legacy contaminado.

**Achado de reconciliação (novo, §6/§12):** o `config.json` da revalidação v1 rotula o config como **`S_full_trend_htf`**, mas os **gates implementados** (ADX≥20 + close>EMA200 + EMA50>EMA200 + EMA50 slope + ATR expanding) e o número citado (n=234/+64.57R/PF1.64) correspondem a **`R_full_trend_regime`** no sweep CSV. `S_full_trend_htf` é uma config **diferente** (com `htf_1d_bullish`, sem slope/atr, n=427/PF1.37). **Nome ≠ definição** — rastreabilidade a corrigir, não invalidação.

**Veredito (reformulado, §15):** pacote = `CONTAMINATED_LEGACY_PACKAGE`; conceito DECISIVE_BREAKOUT/D1a = `RECONSTRUCTION_IN_PROGRESS` + `LAYER_CANDIDATE` (possível L2 breakout) + `NEEDS_CONCEPT_SEPARATION` + `NEEDS_GATE_MANIFEST` + `NEEDS_RAW_MAPPING` + `NEEDS_VISUAL_REVIEW`. **Sem decisão final.** **DA: PASS** (§17).

---

## 2. Fontes lidas (read-only)

| Camada | Fonte |
|---|---|
| Catalog | `my-strategy/strategies/catalog.json` → entrada `XAUUSD_4H_BREAKOUT_CONTINUATION` (96-114) |
| Packet | `my-strategy/research/experimental/xauusd_4h_long_breakout_continuation_regime_filtered.md` |
| Pine | `my-strategy/pine_alerts/01_xauusd_4h_breakout_continuation.pine` |
| Revalidação v1 | `research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/` (summary.md, config.json, report.json, methodology.md, trades.jsonl 115) |
| Sweep legacy (origem) | `my-strategy/research/backtests/xauusd_audit_20260512/XAUUSD_4H_breakout_regime_filter_sweep.csv` (22 configs) + `regime_filter_test.py`, `XAUUSD_deep_strategy_audit_report.md` |
| Canal legacy | `alert-bridge/claude_recheck.py` (recheck:931 NEUTRALIZADO 2026-06-15; module_aware :51,526,649,731) |
| Contexto | BOOTSTRAP pós-L1, MASTER_INVENTORY, PRE_BOTTOM_CATCHER deep dive, IDEA_REVIEW, REEVALUATION_PLAN, LEGACY_KNOWLEDGE_INDEX, project_authority/ |

**Não usado como validação:** SLIM e métricas in-sample (citadas só como histórico, marcadas como tal).

---

## 3. Identidade real e status

- **Nome oficial:** `XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED` (id catalog `XAUUSD_4H_BREAKOUT_CONTINUATION`). Arquétipo **`DECISIVE_BREAKOUT_CONTINUATION`**. `family_origin: B`.
- **Nome enganoso:** "CONTINUATION" no nome **+** `validation_status: ACTIVE_CANDIDATE` no catalog. "Continuation" sugere a mesma família da L1 (pullback-continuation) — **não é**. É **breakout decisivo** (entra no rompimento, não no respiro).
- **Por que "continuation" confunde:** ambos são "long em tendência de alta", mas a L1 entra em **pullback calmo que retoma** (anti-extensão, volume baixo); este entra na **quebra da máxima com corpo forte e volatilidade expandindo** (pró-momentum/displacement). São arquétipos **ortogonais**.
- **Pullback ou breakout decisivo?** **Decisive breakout**, inequivocamente (gate `close>swing_high(10)`).
- **TF/Direção/Universo:** 4H · LONG · universo = barras que rompem a máxima de 10 barras com corpo ≥0.5 e RSI>MA, dentro do filtro de regime.
- **Status atual correto:** **pacote legacy contaminado, conceito em reconstrução.** Não deployado. `current_deployment_status: LIVE_DORMANT`.
- **Onde está no catalog:** entrada `XAUUSD_4H_BREAKOUT_CONTINUATION`, `validation_status=ACTIVE_CANDIDATE`, `recommended/current_deployment=LIVE_DORMANT`, `candidate_packet` aponta para o experimental md, `supersedes: [XAUUSD_4H_LONG_REJECTION_SWING]`.
- **Catalog enganoso? Como?** Sim. `ACTIVE_CANDIDATE` lê como "candidato ativo/vivo" mas: (a) **não está deployado**; (b) o canal de emissão (recheck) foi **neutralizado** (`recheck:931`, 2026-06-15) — proibido emitir `SETUP_VALIDO`/`PROMOTE_TO_SETUP_VALIDO`; (c) indicator signals **bypassam** o recheck desde 2026-05-17. O próprio catalog observa "PURELY DESCRIPTIVE: no consumer reads this yet". O rótulo não reflete o estado real (dormant/neutralizado).

---

## 4. Hipótese / conceito

- **"Breakout decisivo" aqui:** fechamento 4H **acima da máxima dos últimos 10 candles** (`close>swing_high(10)`), com **candle bullish** (`close>open`) e **corpo ≥50% do range** (`body_pct≥0.5`) e **RSI>RSI-MA** (momentum alinhado). É rompimento com **corpo forte** (displacement), não rompimento marginal.
- **Comportamento de mercado:** "XAU paga bem em **continuação de momentum 4H** quando o regime é **trending bull com volatilidade expandindo**." O setup tenta pegar o **impulso pós-rompimento** em tendência viva.
- **Entrada:** no spec original = **close do candle de sinal**; na revalidação v1 = **next-bar-open** (realismo anti-lookahead). É no candle de rompimento/confirmação, **não** após pullback.
- **De onde vem o edge (decomposição pelo sweep):**
  - **corpo forte / trigger sozinho** → fraco (baseline `A_baseline_no_regime`: +32.8R mas no_top10 **−6.66R**, streak 31).
  - **regime** → é a alavanca real. O filtro "trending bull + ADX + ATR expanding" (`R_full_trend_regime`) sobe para +64.57R net / PF1.64 / no_top10 +25.07R / streak 16. **O edge é "quando NÃO operar".**
  - **ausência de exaustão** → não é gate mecânico (H1/H2/H5 ficaram como diagnostic visual; ver §7).
  - **D1 / D1a** → camada macro 1D adicionada depois (§7), melhora ainda mais.
- **Como difere da L1:** L1 = pullback-and-go calmo (anti-extensão, volume baixo, zona OB, NAS SHIFT1, RSI exhaustion gate). Este = breakout pró-momentum (corpo forte, ATR expandindo, sem anti-extensão — ao contrário, quer expansão). **Opostos no eixo "respiro vs rompimento".**

---

## 5. Cronologia de construção

1. **Pré-2026-05-12:** módulo `XAUUSD_4H_LONG_REJECTION_SWING` (expectancy negativo, disparava em chop).
2. **2026-05-12:** **audit sweep** (`xauusd_audit_20260512`, `regime_filter_test.py`) — testou **22 configs** de filtro de regime sobre o mesmo trigger de breakout. Vencedor por total_R: `S_full_trend_htf` (n=427); vencedor por PF/qualidade: **`R_full_trend_regime`** (n=234, +64.57R net, PF1.64). O módulo adotou os **5 filtros do R_full_trend_regime**. BREAKOUT_CONTINUATION_REGIME_FILTERED substitui REJECTION_SWING.
3. **2026-05-15:** Pine `#01` criado (replica os 9 critérios; comentário "234 trades / 7.4y / +64.57R / PF 1.64").
4. **(catalog):** entrada criada `ACTIVE_CANDIDATE` / `LIVE_DORMANT`; module_aware no `claude_recheck.py` (shadow removido 2026-05-12).
5. **2026-05-17:** migração — indicator signals passam a **bypassar** o recheck. Canal legacy começa a esvaziar.
6. **2026-05-24:** última rodada recheck. Canal efetivamente dormant.
7. **2026-05-29:** **revalidação canônica v1** (`replay_real_rt_canonical_slim`) sobre **slim 4H** → trade-level `trades.jsonl` (115 trades) para review visual. **Não para promoção.**
8. **2026-06-01:** pesquisa **D1a** (filtro macro 1D) + walk-forward por janela + **visual review de 25 D1a-rejects** + testes H1c/H2b/H5 (rejeitados como filtro mecânico). Conclusão: D1a é o candidato research-stage; **sem promoção**.
9. **2026-06-15:** **recheck:931 — módulo NEUTRALIZADO** (legacy, pré-Production v2). Proibido emitir SETUP_VALIDO sob este nome.
10. **2026-06-16:** deep dive pré-Bottom-Catcher classifica o pacote `CONTAMINATED_LEGACY / KEEP_REFERENCE` e o D1a como revalidation candidate. **Este bloco** aprofunda.

**O que foi descartado:** trigger sem regime (fraco); H1c/H2b (NAS/RSI-div) como filtro mecânico (degradam W2 ou cosméticos); H5 bubbles (extractor zera POC); exceções para D1a-rejects (event-driven/não-replicáveis); D1a_ext extension-cap (arquivado, risco de degradar bull_recent).
**O que melhorou:** regime filter (trigger→+64.57R); D1a (115→90, +25.3→+32.2R, PF→1.86).
**O que ficou incompleto:** RAW (só slim), OOS real, viés de seleção do sweep, visual review 100%, gate manifest, separação conceito-vs-pacote.
**Por que não foi validado seriamente:** por **design** — a v1 era explicitamente "produzir trades.jsonl plotável para review visual, **não promover**". A validação séria foi conscientemente deixada para depois (preconditions listadas no próprio summary).

---

## 6. Gates reais

Extraídos de `methodology.md` §3 + `config.json` + Pine #01 (não do nome).

| # | Gate | Condição exata | Campo | TF | Causalidade | SHIFT1? | Lookahead | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | breakout | `close[i] > highest(high,10)[i-1]` | `close_above_swing_high_10` | 4H | causal (usa [i-1]) | n/a | nenhum | KEEP |
| T2 | bullish | `close[i] > open[i]` | OHLC | 4H | causal | n/a | nenhum | KEEP |
| T3 | corpo decisivo | `body_pct[i] ≥ 0.5` | `body_pct` | 4H | causal | n/a | nenhum | KEEP |
| T4 | momentum RSI | `rsi(14)[i] > rsi_ma[i]` | `rsi_above_ma` | 4H | causal | n/a | nenhum | KEEP / NEEDS_RAW_MAPPING |
| R1 | força | `ADX(14)[i] ≥ 20` | ADX (calc Python) | 4H | causal | n/a | nenhum | KEEP / NEEDS_RAW_MAPPING |
| R2 | bias macro | `close[i] > EMA(200)[i]` | EMA (calc) | 4H | causal | n/a | nenhum | KEEP |
| R3 | golden cross | `EMA(50)[i] > EMA(200)[i]` | EMA (calc) | 4H | causal | n/a | nenhum | KEEP |
| R4 | slope vivo | `EMA(50)[i] > EMA(50)[i-5]` | EMA (calc) | 4H | causal | n/a | nenhum | KEEP |
| R5 | vol expandindo | `ATR14[i] > SMA(ATR14,20)[i]` | `atr14_wilder` | 4H | causal | n/a | nenhum | KEEP |
| D1a | direção macro 1D | `close_1D>EMA200_1D AND EMA50_1D>EMA200_1D` no **último 1D fechado** | EMA 1D (calc do close 1D) | 1D→4H | **causal (1D fechado, explicit no-lookahead)** | **SHIFT correto ✓** | nenhum | REUSABLE / NEEDS_RAW_MAPPING |
| SL | stop estrutural | `low[i] − 0.5·ATR14`; abort se `risk>5·ATR` | OHLC+ATR | 4H | causal | n/a | nenhum | KEEP (mas pequeno em blow-off, §10) |
| EX | exit | target +4R; BE@+1R (aplica em j+1); time 24 | — | 4H | causal (BE sem intrabar lookahead) | n/a | nenhum | KEEP |
| TG | trade-gen | next-bar-open fill; no-overlap; 1 trade/sinal | — | 4H | causal | n/a | nenhum | KEEP |

**Leitura:** o conjunto é **estruturalmente causal e lookahead-free** — distinto de A1 BALANCE (look-ahead em outcome) e A1' SUPERTREND (look-ahead em regime daily). Os únicos `NEEDS_RAW_MAPPING` são porque os campos vêm do **slim** (RSI/RSI-MA, ATR, body via extractor) e precisam ser remapeados/recomputados de RAW para uma validação séria. **Nenhum gate precisa de SHIFT1 4H** (todos usam barras fechadas); D1a já usa o 1D fechado corretamente.

---

## 7. D1a em detalhe (foco)

- **O que é:** D1a = **filtro de contexto de direção macro 1D** aplicado **on top** dos gates 4H. **NÃO** é entrada, **NÃO** é regime-model completo, **NÃO** é submodelo — é um **gate booleano de direção**.
- **Condição exata:** manter o long só se, no `signal_iso`, o **1D mais recente já fechado** satisfaz `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D`. EMAs computadas da série de close 1D (slim não pré-publica).
- **Por que pareceu ter valor:** remove 25 trades que somam **−6.93R** líquido, cortando **só 1 target** (8 de 9 preservados). Sobe avg_R +0.220→+0.358, total_R +25.28→+32.20, PF 1.479→1.862, WR 30.4→33.3%.
- **Que problema resolve:** corta breakouts 4H que ocorrem **contra/sem** a direção macro 1D (tops/exaustão/contexto inadequado). É a versão **causal e no-lookahead** da ideia `htf_1d_bullish` que já tinha aparecido no sweep (config `S_full_trend_htf`).
- **Trades mantidos/cortados:** 115→**90** (corta 25). Walk-forward por janela: W1 2016-2020 +9.55→**+13.15** (+3.60); W2 2020-2023 −2.52→**+0.81** (+3.33, PF cruza 1.0); W3 2023-2026 +18.24→+18.24 (**no-op**, não degrada a janela mais recente/forte). Ganho **distribuído**, não concentrado num regime.
- **Métricas (D1a):** n=90, WR 33.3%, avg_R +0.358, total_R +32.20, PF 1.862, 8 targets.
- **Causal?** **Sim** — usa o último 1D **fechado** (explicit no-lookahead na methodology). É o oposto do bug A1' SUPERTREND (que usava o D do mesmo dia).
- **SHIFT1 correto?** Sim — "most recent **completed** 1D bar (no lookahead)". É o padrão correto que o audit 2026-06-06 exige.
- **Usa dado de futuro?** Não.
- **RAW ou SLIM/proxy?** **SLIM** (1D EMAs computadas de close 1D do slim). Precisa RAW mapping para validação séria.
- **OOS?** **Não.** Walk-forward interno (mesmo set), não OOS verdadeiro. O set que derivou D1a não o valida.
- **Visual review?** **Parcial** — operador revisou os **25 D1a-rejects** (~20/25 rejeições corretas: topo/exaustão/contexto; ~5 falsos-positivos +8.48R, mas event-driven/não-replicáveis → decisão de não criar exceção). Os 90 **mantidos** não tiveram review 100%.
- **Revalidável sem reescrever a hipótese?** **Sim** — D1a é uma regra fechada, simples, causal. Pode ir direto para gate manifest + RAW + OOS sem mudar a tese.

---

## 8. Indicadores / features

| Indicador | Papel | Entrada/Filtro/Saída/Contexto | RAW existe? | Precisa extractor? | Live? | SHIFT1? |
|---|---|---|---|---|---|---|
| OHLCV 4H | base | todos | sim (RAW 4H) | não | sim | — |
| close/open/high/low | trigger T1-T3, SL | entrada/saída | sim | não | sim | usa [i-1] no swing |
| ATR14 (Wilder) | R5, SL, sanity | filtro/saída | derivável | sim (recompute) | sim | não |
| body_pct | T3 | filtro | derivável | sim | sim | não |
| swing_high(10) | T1 | entrada | derivável | não | sim | [i-1] ✓ |
| RSI / RSI-MA | T4 | filtro | derivável | sim | sim | não |
| EMA50/EMA200 4H | R2/R3/R4 | filtro regime | derivável | sim | sim | não |
| ADX(14) Wilder | R1 | filtro força | derivável | sim | sim | não |
| EMA50/EMA200 **1D** | **D1a** | contexto macro | derivável de close 1D | sim | sim | **1D fechado ✓** |
| OB / Custom OB | — | (não usado) | sim | — | — | — |
| NAS | H1c (diagnostic) | só visual | sim | sim | — | repinta |
| Bubbles | H5 (bloqueado) | — | sim | **extractor zera POC** | bloqueado | repinta |
| regime daily classifier | — | (não usado; ≠ A1') | — | — | — | — |
| V_stair | — | (não usado neste pacote) | — | — | — | — |
| volume | — | (não usado) | sim | — | — | — |

**Observação:** o pacote **não** usa OB, NAS, Bubbles, V_stair nem regime classifier como gate — é puramente **price/EMA/ADX/ATR/RSI + D1a**. Isso o torna **conceitualmente simples e RAW-mapeável** (boa propriedade para reconstrução). NAS/RSI-div/Bubbles foram testados como filtros e ficaram como **diagnostic visual**, não mecânico.

---

## 9. Estudos / backtests / métricas

| Estudo | Range | Dataset | Tipo | n | WR | R | PF | streak | OOS? | Visual? | Validade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sweep legacy (22 configs) | ~2019-2026 (7.4y) | CSV agregado (sem trades) | param sweep | — | — | — | — | — | não | não | **viés de seleção** (22 configs) |
| ↳ `R_full_trend_regime` (adotado) | 7.4y | agregado | net @0.05R | 234 | 28.6% | +64.57R | 1.64 | 16 | não | não | in-sample/agregado |
| ↳ `S_full_trend_htf` (rótulo no config) | 7.4y | agregado | net | 427 | 25.8% | +68.8R | 1.37 | 22 | não | não | config **diferente** (§12) |
| ↳ `A_baseline_no_regime` (trigger só) | 7.4y | agregado | net | 834 | 23.1% | +32.84R (no_top10 **−6.66R**) | 1.09 | 31 | não | não | mostra: trigger fraco sozinho |
| Revalidação v1 | 2016-2026 | **canonical SLIM 4H** | gross R, real stop/target/time | 115 | 30.4% | +25.28R | 1.479 | — | não | parcial | in-sample/slim |
| ↳ + D1a | 2016-2026 | slim + 1D causal | gross R | 90 | 33.3% | +32.20R | 1.862 | — | WF interno | 25 rejects | in-sample/slim |

Exit reasons v1: **9 target / 52 stop / 25 stop_be / 29 time_limit** (29 right-censored). Por regime (v1): bull_recent +16.42R (n=40, melhor), bull_pre_covid +7.46R, covid_rally +3.63R, chop_macro +1.82R, pre_covid +2.09R; **negativos:** chop_inflation_bear −5.15R (2022 blow-off), chop_post_covid −1.0R.

**NÃO é validação** (por todos os critérios do bloco): usou SLIM; sem RAW mapping; sem OOS; vencedor de sweep com viés de seleção; canal recheck legacy; rótulo catalog enganoso; reconciliação impossível (legacy só agregado). Custos: legacy usou net @0.05R; revalidação v1 é **gross** (sem custo) — não comparável diretamente.

---

## 10. Trades / casos relevantes

- **9 targets (+4R) na v1:** 2017-08-09 (pre_covid), 2019-06-03/06-19 (bull_pre_covid), 2020-02-18/07-21 (covid_rally, MFE 4.9/4.5), 2021-11-07 (chop_post_covid, **MFE 6.0** — maior excursão) + 3 em bull_recent. **Importam** porque D1a preserva 8/9 (só perde 1) — evidência de que o filtro corta losers sem matar winners.
- **Losers (−1R, stop):** concentrados em **pre_covid** (2016-11-09, 2017-01-12/01-23/03-27) e **chop**. Motivaram a tese "regime filter = quando não operar".
- **Caso que motivou D1a / fragilidade:** **chop_inflation_bear 2022** (Rússia/Ucrânia + inflação parabólica): 7 D1a-keep trades, 0 targets, entries com close_1D ~**+3.18 daily-ATR acima da EMA200** (blow-off) e a +9.5 ATR_4H da swing_high — **chasing breakout esticado**. Stop 0.5ATR **pequeno demais** para a expansão pós-entrada. Aceito como custo residual raro.
- **5 D1a-rejects "falsos-positivos" (+8.48R deixados na mesa):** #3 +0.76, #8 +2.08, #10 +0.96, #20 +4.00, #21 +0.67 — mas event-driven (Fed pivot Nov-2021, CPI surprise Nov-2022) ou drifts não-replicáveis. Só #10 seria candidato replicável. Decisão: **não criar exceção** (custo do delay 12h apaga o ganho).
- Todos exigiriam **visual review futura** (100%) para promoção — hoje só os 25 rejects foram vistos.

---

## 11. Comparação com a L1 EMA21 CONTINUATION refinada

| Eixo | BREAKOUT / D1a | L1 refinada |
|---|---|---|
| Mercado capturado | rompimento de momentum (displacement) | pullback calmo que retoma |
| Entrada | breakout candle (next-bar-open) | toque em zona OB + reclaim |
| Ritmo | pró-expansão (ATR expandindo) | anti-extensão (ret5/ext_ema/zone_w/dist_zone) |
| Risco/SL | `low−0.5ATR` (pequeno; frágil em blow-off) | `max(zona_OB_low, swing6_low)−0.1ATR` (estrutural) |
| Target | +4R, BE@+1R, time 24 | +3R fixo |
| Regime | EMA200/golden-cross/ADX/ATR + **D1a (1D causal)** | regime_l1_v4 BULL D-1 (SHIFT1) |
| NAS | não (diagnostic só) | NAS SHIFT1≥1.31 (gate) |
| RSI | RSI>MA (momentum, pró) | `rsi_vs_ma≤−9.35` (exhaustion, **anti**) |
| OB/zona | não usa | Custom OB v11 + zone quality |
| Anti-extensão | **não** (quer expansão) | **sim** (stack v1) |
| Causalidade | causal/lookahead-free | causal ✓ |
| Live-readiness | pesquisa (slim, recheck neutralizado) | operacional (parcial), scanner=runtime |
| Validação | in-sample/slim, sem OOS | in-sample, sem OOS |

**Respostas obrigatórias:**
- **D1a compete com L1?** **Não** — captura mercado oposto (rompimento vs respiro). Frequência e timing distintos.
- **Complementa L1?** **Sim** — cobre o regime de **breakout/momentum** que a L1 (anti-extensão) **deliberadamente evita**. Ortogonal.
- **Futura L2 breakout?** **Sim, candidata** — é o encaixe natural como camada breakout separada.
- **Separada do motor L1?** **Sim** — deve ficar em módulo próprio. Misturar breakout (pró-expansão) dentro do gate L1 (anti-extensão) **contaminaria** ambos.
- **Pode compartilhar componentes?** Sim, com cuidado: **SL estrutural** (a L1 tem um melhor que o `low−0.5ATR`) e a **infra scanner=runtime / study-values por timestamp / chart-management**. O **RSI gate** NÃO deve ser compartilhado como está (a L1 usa RSI como *anti-exhaustion*; o breakout usa RSI como *pró-momentum* — semânticas opostas).
- **Onde NÃO misturar:** anti-extensão ↔ pró-expansão; RSI exhaustion ↔ RSI momentum; regime_l1_v4 (pullback) ↔ regime de breakout. Manter **conceitos separados**.

---

## 12. Contaminações / riscos

| Risco | Onde | Severidade | Reparável? |
|---|---|---|---|
| Rótulo catalog `ACTIVE_CANDIDATE` enganoso | catalog | 🟡 cosmético/operacional | sim (corrigir rótulo, bloco futuro) |
| Canal **recheck:931 legacy** | claude_recheck.py | 🟡 neutralizado mas existe | sim (desligar de qualquer revival) |
| **SLIM** = fonte de TODA métrica | revalidação v1 + sweep | 🟠 invalida números até RAW | sim (RAW mapping) |
| **Viés de seleção** (vencedor de 22 configs) | sweep 2026-05-12 | 🟠 sem Bonferroni/OOS | sim (OOS + pré-registro) |
| **Config-label mismatch** (`S_full_trend_htf` rotula gates de `R_full_trend_regime`) | config.json v1 | 🟡 rastreabilidade (nome≠definição) | sim (corrigir label) |
| Legacy CSV **agregado** (sem trade-level) | sweep | 🟡 reconciliação impossível | parcial (re-derivar de RAW) |
| **Sem OOS** | tudo | 🟠 não prova edge | sim (OOS pós-2026-06) |
| Bubbles bloqueadas (extractor zera POC) | H5 | 🟡 feature indisponível | sim (corrigir extractor) |
| Custos não aplicados (gross R) na v1 | revalidação v1 | 🟡 R otimista | sim (cost overlay) |
| Stop 0.5ATR pequeno em blow-off | SL | 🟠 risco em regime parabólico | sim (re-desenhar SL) |

**Nenhuma contaminação é look-ahead irreparável.** Diferente de A1 BALANCE / A1' SUPERTREND, **não há prova de look-ahead** aqui — os gates são causais. As contaminações são de **fonte (slim), seleção (sweep), rótulo (catalog/config), canal (recheck) e ausência de OOS** — todas **reparáveis** por reconstrução. **Não há base objetiva para descarte final.**

---

## 13. O que faltou para validação séria

1. **Gate manifest** — predicados exatos sobre RAW (campos, fórmulas ADX/EMA/ATR, swing, D1a 1D), mapping de qualquer indicador, close-only-causal documentado.
2. **RAW / source-field mapping** — sair do SLIM; recomputar ATR/RSI/EMA/ADX/body de OHLCV RAW; confirmar fidelidade do extractor.
3. **Correção do viés de seleção** — o config adotado venceu um sweep de 22; precisa pré-registro + correção de multiplicidade.
4. **SHIFT1/HTF** — D1a já é causal; documentar formalmente e confirmar EMA 1D do D-1.
5. **Outcome engine causal + stop/target real + custos/slippage** — a v1 é gross R; aplicar custos; modelar fill.
6. **Train/val/test ou OOS real** — pós-2026-06, cobrindo ao menos uma mudança de regime direcional.
7. **Visual review 100%** — só 25 D1a-rejects vistos; falta revisar os 90 mantidos.
8. **Audit no-lookahead formal** — ORIG vs SHIFT1 (esperado: sem delta, pois já causal — confirmar).
9. **scanner/runtime parity** — se virar L2, precisa do mesmo padrão da L1 (gate único reusado).
10. **Sanity checks / reconciliação** — legacy só agregado; re-derivar trade-level de RAW para reconciliar.

**Resumo:** *ainda não sabemos se tem edge — mas agora sabemos exatamente o que precisa ser testado* (1-10 acima).

---

## 14. Melhor conceito recuperável

- **NÃO é o pacote inteiro** (catalog + recheck + slim = contaminado).
- **É o conceito DECISIVE_BREAKOUT + filtro de regime macro, com o D1a como peça mais limpa.** Especificamente:
  - **Núcleo recuperável:** trigger de breakout decisivo (T1-T4) + 5 gates de regime causais (R1-R5) + **D1a (direção macro 1D, causal/no-lookahead)** + SL estrutural (re-desenhado) + exit +4R/BE/time.
  - **A sub-ideia de maior valor isolado:** **D1a** — simples, causal, melhora R+estabilidade+simplicidade, distribuída em janelas, revalidável sem reescrever a tese.
  - **Aprendizado transversal:** "o edge do breakout vem do **regime** (quando NÃO operar), não do trigger"; "SL 0.5ATR é pequeno em blow-off"; "H1/H2/H5 são diagnostic visual, não filtro mecânico".
- **O que deve morrer / não reabrir como está:** a **emissão via canal recheck legacy** (:931) e o **rótulo catalog `ACTIVE_CANDIDATE`**. A **dependência de slim** como fonte de verdade.
- **O que preservar:** o conceito, os gates causais, o D1a, os trades.jsonl (para review visual futura), o sweep CSV (para entender a decomposição do edge), este deep dive.

---

## 15. Veredito (reformulado — sem decisão final)

| Alvo | Veredito |
|---|---|
| **Pacote legacy** (catalog `ACTIVE_CANDIDATE` + Pine #01 + canal recheck:931) | **`CONTAMINATED_LEGACY_PACKAGE`** |
| **Conceito DECISIVE_BREAKOUT / D1a** | **`RECONSTRUCTION_IN_PROGRESS`** + **`LAYER_CANDIDATE`** (futura L2 breakout, separada da L1) |
| **Ações necessárias antes de qualquer julgamento** | **`NEEDS_CONCEPT_SEPARATION`** (separar conceito limpo do pacote) · **`NEEDS_GATE_MANIFEST`** · **`NEEDS_RAW_MAPPING`** · **`NEEDS_VISUAL_REVIEW`** (100%) |
| **Artefatos** | **`KEEP_REFERENCE`** (trades.jsonl, sweep CSV, packet, este doc) |

**Não há decisão final de descarte nem de promoção.** Não há prova de look-ahead → **não invalidar**. "Não validado" ≠ "sem valor". Conclusão principal: **ainda não sabemos se há edge, mas agora sabemos exatamente o que testar (§13) e qual é o núcleo recuperável (§14).**

---

## 16. Próximo bloco recomendado (sem executar nada agora)

Coerente com a prioridade do projeto (**Caminho B bottom-catcher = P0**), o BREAKOUT/D1a é **P2 / futura L2 breakout** — não deve passar à frente do Caminho B. Quando chegar a vez:

1. **Bloco de separação de conceito** (read-only): destacar o núcleo limpo (T1-T4 + R1-R5 + D1a + SL re-desenhado) num **gate manifest** próprio, explicitamente desacoplado do canal recheck e do rótulo catalog.
2. **Bloco RAW mapping** (read-only): mapear cada campo slim → RAW; especificar recomputação de ADX/EMA/ATR/RSI/swing/D1a de OHLCV RAW; confirmar fidelidade do extractor.
3. **Só então** (com autorização): pré-registro + RAW backtest + OOS pós-2026-06 + visual review 100% + custos.
4. **Em paralelo, bloco futuro autorizado:** corrigir o rótulo `ACTIVE_CANDIDATE` no catalog e o config-label mismatch (rastreabilidade).

**Recomendação imediata:** seguir para o **gate manifest do Caminho B (P0)**; manter BREAKOUT/D1a em `RECONSTRUCTION_IN_PROGRESS` como LAYER_CANDIDATE documentado.

---

## 17. Apêndice — Devil's Advocate

| Pergunta DA | Resposta | PASS? |
|---|---|---|
| Confundiu breakout decisivo com pullback continuation? | Não — separados explicitamente (§3/§4/§11); arquétipo DECISIVE_BREAKOUT, oposto à L1 no eixo respiro/rompimento. | ✅ |
| Classificou pelo nome? | Não — gates extraídos de methodology/config/Pine/sweep (§6). | ✅ |
| D1a foi extraído por gates reais? | Sim — condição exata, campos, causalidade, métricas, walk-forward (§7). | ✅ |
| Algum número slim/proxy chamado de validação? | Não — todos marcados in-sample/SLIM; "NÃO é validação" explícito (§9). | ✅ |
| D1/HTF tem SHIFT1 ou caveat? | Sim — D1a usa o **1D fechado** (no-lookahead), documentado; ainda assim slim → NEEDS_RAW_MAPPING. | ✅ |
| recheck:931 tratado como legacy risk? | Sim — NEUTRALIZADO 2026-06-15, contaminação reparável (§5/§12). | ✅ |
| Catalog label checado? | Sim — `ACTIVE_CANDIDATE` declarado enganoso; + achado config-label mismatch S_full_trend_htf vs R_full_trend_regime (§12). | ✅ |
| L1 descrita com config refinada correta? | Sim (§11, verificada vs scanner.py em blocos anteriores). | ✅ |
| Misturou D1a dentro da L1 sem evidência? | Não — recomendou módulo separado; listou onde NÃO misturar (§11). | ✅ |
| Transformou "não validado" em "invalidado"? | Não — veredito reformulado, sem descarte final, sem prova de look-ahead (§15). | ✅ |
| Nenhum backtest rodado? | Correto — read-only. | ✅ |
| Nada operacional tocado? | Correto — só este relatório. | ✅ |

**DA verdict: PASS.**

---

*Documento read-only. Nenhum backtest rodado, nenhum scanner executado, nenhum código/catalog/strategy_rules/runtime/scheduler/RAW/event-store/broker tocado, nenhum Telegram, nenhum MCP/chart. Métricas citadas são in-sample/SLIM/agregado conforme as fontes do §2. Nenhuma decisão final de descarte ou promoção tomada.*
